"""Citable passages of a TEI text, read from both of its citation declarations.

A Bron text declares its citation scheme twice: `<refsDecl n="CTS">` with `cRefPattern`s,
the CapiTainS convention, and `<refsDecl default="true">` with `citeStructure`, the form
DTS-era tools read. This module is the only one that imports `dapytains`, which reads
`citeStructure`; `cRefPattern`s are evaluated here directly with XPath 1.
"""

import re
from dataclasses import dataclass
from pathlib import Path

from dapytains.tei.document import Document
from lxml import etree

from bron.tei import CTS_REFSDECL, NSMAP


class PassageError(Exception):
    """A text's citation declaration is missing or cannot be evaluated."""


@dataclass(frozen=True)
class CitableUnit:
    ref: str
    depth: int
    parent: str | None
    cite_type: str


@dataclass(frozen=True)
class CrefPassage:
    ref: str
    depth: int
    parent: str | None
    element: etree._Element


# Saxon evaluates a text's citeStructure @match and @use as full XPath 3.1, whose
# unparsed-text() and doc() can read files and fetch URLs. Data comes from untrusted pull
# requests, so a text may carry no DTD (no entities to expand) and, once Saxon has parsed
# it, may reach no URI at all.
_SAFE_PARSER = etree.XMLParser(resolve_entities=False, no_network=True, load_dtd=False)
_ALLOWED_PROTOCOLS = "http://saxon.sf.net/feature/allowedProtocols"


def open_document(path: Path) -> Document:
    """The text as `dapytains` reads it; open it once and reuse it for every passage."""
    try:
        docinfo = etree.parse(str(path), _SAFE_PARSER).docinfo
    except etree.XMLSyntaxError as error:
        raise PassageError(f"the text is not well-formed: {error}") from error
    if docinfo.doctype or docinfo.internalDTD is not None:
        raise PassageError("a text may not carry a DOCTYPE declaration")
    try:
        document = Document(str(path))
    except Exception as error:  # dapytains raises bare exceptions on bad declarations
        raise PassageError(f"citeStructure cannot be read: {error}") from error
    document.xml_processor.set_configuration_property(_ALLOWED_PROTOCOLS, "")
    return document


def _document(source: Path | Document) -> Document:
    return open_document(source) if isinstance(source, Path) else source


def cite_structure_units(source: Path | Document) -> list[CitableUnit]:
    """Every citable unit the default `citeStructure` declares, in document order."""
    document = _document(source)
    if not document.citeStructure:
        raise PassageError("no citeStructure declaration")
    tree = document.citeStructure.get("default") or next(iter(document.citeStructure.values()))
    units: list[CitableUnit] = []

    def walk(found: list, depth: int, parent: str | None) -> None:
        for unit in found:
            units.append(
                CitableUnit(ref=unit.ref, depth=depth, parent=parent, cite_type=unit.citeType)
            )
            walk(unit.children, depth + 1, unit.ref)

    try:
        walk(tree.find_refs(root=document.xml, structure=tree.structure), 1, None)
    except Exception as error:
        raise PassageError(f"citeStructure cannot be enumerated: {error}") from error
    return units


def extract_passage(source: Path | Document, ref: str) -> etree._Element:
    """The TEI fragment for one citable unit, as `dapytains` extracts it."""
    document = _document(source)
    try:
        return document.get_passage(ref)
    except Exception as error:
        raise PassageError(f"passage {ref} cannot be extracted: {error}") from error


_LEVEL_VALUE = re.compile(r"""@n\s*=\s*(['"])\$(\d+)\1""")
_XPATH_WRAPPER = re.compile(r"^#xpath\((.*)\)$", re.DOTALL)


def _cref_xpaths(tree: etree._ElementTree) -> list[str]:
    """The `cRefPattern` XPaths, shallowest level first."""
    patterns = tree.xpath(f"{CTS_REFSDECL}/tei:cRefPattern", namespaces=NSMAP)
    if not patterns:
        raise PassageError('no <refsDecl n="CTS"> with cRefPattern')
    xpaths = []
    for pattern in reversed(patterns):  # CapiTainS orders them deepest first
        match = _XPATH_WRAPPER.match(pattern.get("replacementPattern", "").strip())
        if not match:
            raise PassageError("cRefPattern replacementPattern is not #xpath(...)")
        xpaths.append(match.group(1))
    return xpaths


def _bind(xpath: str, values: list[str]) -> str:
    """Substitute known level values; leave the next level as a wildcard on `@n`."""

    def substitute(match: re.Match[str]) -> str:
        level = int(match.group(2))
        if level <= len(values):
            return f"@n='{values[level - 1]}'"
        return "@n"

    return _LEVEL_VALUE.sub(substitute, xpath)


def cref_passages(tree: etree._ElementTree) -> list[CrefPassage]:
    """Every passage the `cRefPattern`s select, depth-first in document order."""
    xpaths = _cref_xpaths(tree)
    passages: list[CrefPassage] = []

    def walk(values: list[str], parent: str | None) -> None:
        depth = len(values) + 1
        if depth > len(xpaths):
            return
        try:
            elements = tree.xpath(_bind(xpaths[depth - 1], values), namespaces=NSMAP)
        except etree.XPathError as error:
            raise PassageError(f"cRefPattern XPath cannot be evaluated: {error}") from error
        for element in elements:
            label = element.get("n", "")
            ref = ".".join([*values, label])
            passages.append(CrefPassage(ref=ref, depth=depth, parent=parent, element=element))
            if label:
                walk([*values, label], ref)

    walk([], None)
    return passages
