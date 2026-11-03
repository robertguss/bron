"""The resolver's in-memory index of a data repository: collections, resources, passages.

It is built once at startup from the CapiTainS metadata (`__cts__.xml`), each text's
citation declarations, and `identifiers/redirects.yaml`. Nothing is written anywhere.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from lxml import etree

from bron.checks.capitains import CTS, CTS_NS, VERSION_KINDS
from bron.checks.stability import REDIRECTS
from bron.datafiles import load_records
from bron.tei import NSMAP, XML_LANG
from bron.tei.passages import (
    PassageError,
    cite_structure_units,
    cref_passages,
    open_document,
)

# The name a request may give the one citation tree each text declares.
DEFAULT_TREE = "default"

_PARSER = etree.XMLParser(resolve_entities=False, no_network=True, huge_tree=True)


class DataError(Exception):
    """The repository cannot be served; `bron check` names the underlying problems."""


@dataclass(frozen=True)
class Unit:
    """One citable unit of a resource, at its place in document order."""

    ref: str
    level: int
    parent: str | None
    cite_type: str
    ordinal: int  # position in document order
    last: int  # ordinal of its last descendant, or its own when it has none
    element: etree._Element


@dataclass
class Resource:
    urn: str
    path: Path
    units: list[Unit]
    cite_structure: list[dict[str, Any]]
    language: str | None
    by_ref: dict[str, Unit] = field(init=False)

    def __post_init__(self) -> None:
        self.by_ref = {unit.ref: unit for unit in self.units}

    def children(self, unit: Unit | None) -> list[Unit]:
        parent = unit.ref if unit else None
        return [u for u in self.units if u.parent == parent]

    def subtree(self, unit: Unit, depth: int | None) -> list[Unit]:
        """`unit` and its descendants down to `depth` levels below it (all when None)."""
        found = self.units[unit.ordinal : unit.last + 1]
        if depth is None:
            return found
        return [u for u in found if u.level <= unit.level + depth]

    def span(self, start: Unit, end: Unit, depth: int | None) -> list[Unit]:
        """Units from `start` through the whole of `end`, at the cited levels and `depth` below."""
        shallowest = min(start.level, end.level)
        deepest = max(start.level, end.level)
        found = self.units[start.ordinal : end.last + 1]
        return [
            u
            for u in found
            if u.level >= shallowest and (depth is None or u.level <= deepest + depth)
        ]

    def covering(self, start: Unit, end: Unit) -> list[Unit]:
        """The fewest whole units, at the shallower cited level or below, that hold the text
        from `start` through `end`."""
        shallowest = min(start.level, end.level)
        chosen: list[Unit] = []
        covered_until = -1
        for unit in self.units[start.ordinal : end.last + 1]:
            if unit.ordinal <= covered_until or unit.last > end.last or unit.level < shallowest:
                continue
            chosen.append(unit)
            covered_until = unit.last
        return chosen


@dataclass
class Collection:
    """A node of the collection tree: the root, a textgroup, a work, or a resource."""

    urn: str
    titles: list[tuple[str, str]]  # (lang, text), in source order
    descriptions: list[tuple[str, str]] = field(default_factory=list)
    language: str | None = None
    parent: str | None = None
    children: list[str] = field(default_factory=list)
    resource: Resource | None = None

    @property
    def title(self) -> str:
        return self.titles[0][1] if self.titles else self.urn


@dataclass
class Index:
    root: str
    collections: dict[str, Collection]
    redirects: dict[str, dict[str, Any]]

    def resource(self, urn: str) -> Resource | None:
        node = self.collections.get(urn)
        return node.resource if node else None


def build_index(repo: Path) -> Index:
    """Index every collection, resource and passage of `repo`; raises DataError."""
    repo = repo.resolve()
    data = repo / "data"
    if not data.is_dir():
        raise DataError(f"{repo} has no data/ directory")
    collections: dict[str, Collection] = {}
    textgroups = []
    for folder in sorted(p for p in data.iterdir() if p.is_dir()):
        textgroups.append(_textgroup(folder, collections))
    namespaces = {urn.split(":")[2] for urn in textgroups}
    if len(namespaces) != 1:
        raise DataError(
            "the textgroups must share exactly one CTS namespace, found "
            + (", ".join(sorted(namespaces)) or "none")
        )
    root = f"urn:cts:{namespaces.pop()}"
    collections[root] = Collection(urn=root, titles=[], children=textgroups)
    for urn in textgroups:
        collections[urn].parent = root
    records, problems = load_records(
        repo, REDIRECTS, "redirects.schema.json", "redirects", "redirects", "urn"
    )
    if problems:
        raise DataError("; ".join(problem.render(repo) for problem in problems))
    return Index(root=root, collections=collections, redirects={r["urn"]: r for r in records})


def _metadata(path: Path, kind: str) -> etree._Element:
    try:
        root = etree.parse(str(path), _PARSER).getroot()
    except (OSError, etree.XMLSyntaxError) as error:
        raise DataError(f"{path} cannot be read: {error}") from error
    if root.tag != f"{{{CTS_NS}}}{kind}" or not root.get("urn"):
        raise DataError(f"{path} must be a <ti:{kind}> with a urn")
    return root


def _labelled(element: etree._Element, name: str) -> list[tuple[str, str]]:
    return [
        (child.get(XML_LANG, ""), " ".join((child.text or "").split()))
        for child in element.iterfind(f"ti:{name}", CTS)
    ]


def _textgroup(folder: Path, collections: dict[str, Collection]) -> str:
    textgroup = _metadata(folder / "__cts__.xml", "textgroup")
    urn = textgroup.get("urn", "")
    node = Collection(urn=urn, titles=_labelled(textgroup, "groupname"))
    collections[urn] = node
    for work_folder in sorted(p for p in folder.iterdir() if p.is_dir()):
        node.children.append(_work(work_folder, urn, collections))
    return urn


def _work(folder: Path, parent: str, collections: dict[str, Collection]) -> str:
    work = _metadata(folder / "__cts__.xml", "work")
    urn = work.get("urn", "")
    node = Collection(
        urn=urn,
        titles=_labelled(work, "title"),
        descriptions=_labelled(work, "description"),
        language=work.get(XML_LANG),
        parent=parent,
    )
    collections[urn] = node
    for kind in VERSION_KINDS:
        for version in work.iterfind(f"ti:{kind}", CTS):
            version_urn = version.get("urn", "")
            resource = _resource(folder / f"{version_urn.split(':')[-1]}.xml", version_urn)
            collections[version_urn] = Collection(
                urn=version_urn,
                titles=_labelled(version, "label"),
                descriptions=_labelled(version, "description"),
                language=resource.language,
                parent=urn,
                resource=resource,
            )
            node.children.append(version_urn)
    return urn


def _resource(path: Path, urn: str) -> Resource:
    if not path.is_file():
        raise DataError(f"{urn} is listed in its work's metadata but {path} does not exist")
    try:
        tree = etree.parse(str(path), _PARSER)
        units = cite_structure_units(open_document(path))
        passages = cref_passages(tree)
    except (etree.XMLSyntaxError, PassageError) as error:
        raise DataError(f"{path}: {error}") from error
    if [u.ref for u in units] != [p.ref for p in passages]:
        raise DataError(f"{path}: its two citation declarations name different passages")

    lasts = list(range(len(units)))
    open_ancestors: list[int] = []
    for ordinal, unit in enumerate(units):
        while open_ancestors and units[open_ancestors[-1]].ref != unit.parent:
            open_ancestors.pop()
        for ancestor in open_ancestors:
            lasts[ancestor] = ordinal
        open_ancestors.append(ordinal)

    return Resource(
        urn=urn,
        path=path,
        units=[
            Unit(
                ref=unit.ref,
                level=unit.depth,
                parent=unit.parent,
                cite_type=unit.cite_type,
                ordinal=ordinal,
                last=lasts[ordinal],
                element=passage.element,
            )
            for ordinal, (unit, passage) in enumerate(zip(units, passages, strict=True))
        ],
        cite_structure=_cite_structure(tree),
        language=_body_language(tree),
    )


def _body_language(tree: etree._ElementTree) -> str | None:
    body = tree.find("tei:text/tei:body", NSMAP)
    return body.get(XML_LANG) if body is not None else None


def _cite_structure(tree: etree._ElementTree) -> list[dict[str, Any]]:
    """The default `citeStructure` as DTS CiteStructure objects."""

    def describe(element: etree._Element) -> dict[str, Any]:
        found: dict[str, Any] = {"@type": "CiteStructure", "citeType": element.get("unit", "")}
        children = element.findall("tei:citeStructure", NSMAP)
        if children:
            found["citeStructure"] = [describe(child) for child in children]
        return found

    declarations = tree.xpath(
        "/tei:TEI/tei:teiHeader/tei:encodingDesc/tei:refsDecl[tei:citeStructure]",
        namespaces=NSMAP,
    )
    default = next((d for d in declarations if d.get("default") == "true"), None)
    chosen = default if default is not None else declarations[0]
    return [describe(element) for element in chosen.findall("tei:citeStructure", NSMAP)]
