"""Alignment link targets resolve to an xml:id in an edition file, or to a deferred file."""

from collections.abc import Iterator
from pathlib import Path
from urllib.parse import urljoin, urlsplit
from urllib.request import url2pathname

from lxml import etree

from bron.checks import Context
from bron.datafiles import load_yaml, schema_findings
from bron.findings import Finding
from bron.tei import XML_BASE, XML_ID, tei

DEFERRED = Path("alignments/deferred.yaml")
SKIPPED = "skipped"


def check_alignment(context: Context) -> Iterator[Finding]:
    yield from alignment_report(context)[0]


def alignment_report(context: Context) -> tuple[list[Finding], int]:
    """The findings, and how many targets were skipped because their file is deferred."""
    deferred, findings = _deferred(context)
    ids: dict[Path, set[str] | None] = {}
    skipped = 0
    for path in context.alignment_files():
        tree = context.tree(path)
        if tree is None:
            continue
        document = path.resolve().as_uri()
        for link in tree.iter(tei("link")):
            base = _base(document, link)
            for token in link.get("target", "").split():
                problem = _resolve(context, urljoin(base, token), deferred, ids)
                if problem == SKIPPED:
                    skipped += 1
                elif problem:
                    message = f"link on line {link.sourceline}: target {token!r} {problem}"
                    findings.append(Finding(path, link.sourceline, "alignment-target", message))
    return findings, skipped


def _resolve(
    context: Context, uri: str, deferred: set[str], ids: dict[Path, set[str] | None]
) -> str | None:
    """What is wrong with one resolved target, SKIPPED when its file is deferred, else None."""
    parts = urlsplit(uri)
    if parts.scheme != "file":
        return None  # URNs and web URLs are not file references.
    target = Path(url2pathname(parts.path))
    root = context.root.resolve()
    if not target.is_relative_to(root):
        return None
    relative = target.relative_to(root).as_posix()
    if not target.is_file():
        if relative in deferred:
            return SKIPPED
        return f"resolves to {relative}, which does not exist and is not listed in {DEFERRED}"
    if target not in ids:
        tree = context.tree(target)
        # A target file that does not parse is the schema check's finding, not this one's.
        ids[target] = {i for e in tree.iter() if (i := e.get(XML_ID))} if tree is not None else None
    known = ids[target]
    if parts.fragment and known is not None and parts.fragment not in known:
        return f"resolves to {relative}, which has no xml:id {parts.fragment!r}"
    return None


def _base(document: str, link: etree._Element) -> str:
    """The link's base URI: every xml:base on its ancestors-or-self, applied outermost first."""
    base = document
    for element in [*reversed(list(link.iterancestors())), link]:
        value = element.get(XML_BASE)
        if value is not None:
            base = urljoin(base, value)
    return base


def _deferred(context: Context) -> tuple[set[str], list[Finding]]:
    """Repo-relative paths of target files a later milestone adds, from alignments/deferred.yaml."""
    path = context.root / DEFERRED
    if not path.is_file():
        return set(), []
    file = load_yaml(path, "alignment-deferred")
    if isinstance(file, Finding):
        return set(), [file]
    findings = list(schema_findings(file, "deferred.schema.json", "alignment-deferred", "path"))
    if findings:
        return set(), findings
    return {entry["path"] for entry in file.data["deferred"]}, []
