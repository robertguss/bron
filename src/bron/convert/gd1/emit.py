"""The GD¹ TEI file: each volume converted, checked, assembled and written deterministically.

`convert` fetches the four volumes, converts each, checks that every page of the page map
appears exactly once and that the § and subparagraph numbers run without unexplained gaps,
and assembles one TEI file. The output is a pure function of its inputs (the four
transcriptions, the page map, the registry and the bron commit): attributes are written in
a fixed order, indentation is fixed, and nothing records the time of the run.
"""

from collections.abc import Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from lxml import etree

from bron.convert.gd1 import ConversionError
from bron.convert.gd1.fetch import Download, fetch, http_get
from bron.convert.gd1.header import Provenance, header
from bron.convert.gd1.html import Converter, parse
from bron.convert.gd1.notes import Footnotes
from bron.convert.gd1.pagemap import MAP, load_map
from bron.convert.gd1.pages import PageBreaks, for_volume
from bron.convert.gd1.regions import split
from bron.convert.gd1.structure import (
    Section,
    allowed_gaps,
    body,
    check_numbers,
    matter,
    printed_headings,
)
from bron.tei import TEI_NS, XML_LANG, tei

URN = "urn:cts:bron:bavinck.gd.ed1"
VOLUMES = (1, 2, 3, 4)
XML_MODEL = (
    'href="https://tei-c.org/Vault/P5/4.12.0/xml/tei/custom/schema/relaxng/tei_all.rng" '
    'type="application/xml" schematypens="http://relaxng.org/ns/structure/1.0"'
)
INDENT = "  "
# Elements that hold only other elements, which are written one per line.
STRUCTURAL = frozenset(
    tei(name)
    for name in (
        "TEI",
        "teiHeader",
        "fileDesc",
        "titleStmt",
        "respStmt",
        "publicationStmt",
        "availability",
        "sourceDesc",
        "listBibl",
        "bibl",
        "encodingDesc",
        "editorialDecl",
        "refsDecl",
        "citeStructure",
        "text",
        "front",
        "body",
        "back",
        "div",
        "table",
        "row",
        "list",
        "note",
    )
)


@dataclass
class Volume:
    """One volume converted: its three regions, its numbering, and what the header needs."""

    number: int
    title: str
    transcribers: list[str]
    front: etree._Element
    body: list[etree._Element]
    back: etree._Element | None
    notes: list[etree._Element]  # the transcribers' notes
    sections: list[Section]
    pages: PageBreaks
    corrections: int


@dataclass
class Conversion:
    tei: bytes
    volumes: list[Volume]
    gaps: list[tuple[int, int, int]]  # (volume, §, subparagraph) the print does not have


def convert_volume(data: bytes, number: int, page_map: Mapping[str, Any]) -> Volume:
    """One volume's transcription as TEI regions; raises ConversionError with a location."""
    source = parse(data)
    if not source.transcribers:
        raise ConversionError(f"vol. {number}: the ebook's header credits no transcribers")
    regions = split(source.body, number)
    footnotes = Footnotes(source.body)
    converter = Converter(for_volume(page_map, number), footnotes)
    front = _division(number, matter(regions.front, converter))
    nodes, sections = body(regions.body, converter, number, printed_headings(page_map))
    back = _division(number, matter(regions.back, converter)) if regions.back else None
    notes = [converter.block(block) for block in regions.notes if block.tag in ("p", "ul")]
    footnotes.check_placed()
    if converter.corrections != source.corrections:
        raise ConversionError(
            f"vol. {number}: {source.corrections} corrections in the source, "
            f"{converter.corrections} converted"
        )
    return Volume(
        number,
        source.title,
        source.transcribers,
        front,
        nodes,
        back,
        notes,
        sections,
        converter.pages,
        converter.corrections,
    )


def convert(
    registry_path: Path, cache: Path, commit: str, download: Download = http_get
) -> Conversion:
    """All four volumes as one TEI file, from the sources the registry pins."""
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    paths = [fetch(_record(registry, n, "gutenberg"), cache, download) for n in VOLUMES]
    page_map = load_map(MAP)
    volumes = []
    for number, path in zip(VOLUMES, paths, strict=True):
        volume = convert_volume(path.read_bytes(), number, page_map)
        volume.pages.check_complete()
        volumes.append(volume)
    sections = [section for volume in volumes for section in volume.sections]
    gaps = check_numbers(sections, allowed_gaps(page_map), first=1)
    return Conversion(assemble(volumes, registry, page_map, commit), volumes, gaps)


def assemble(
    volumes: Sequence[Volume],
    registry: Mapping[str, Any],
    page_map: Mapping[str, Any],
    commit: str,
) -> bytes:
    """The TEI file holding the given volumes, serialized."""
    root = etree.Element(tei("TEI"), nsmap={None: TEI_NS})
    provenance = [
        Provenance(
            volume.number,
            _record(registry, volume.number, "gutenberg"),
            _record(registry, volume.number, "dbnl"),
            volume.title,
            volume.transcribers,
            [deepcopy(note) for note in volume.notes],
            volume.pages.inserted,
            volume.pages.malformed,
        )
        for volume in volumes
    ]
    root.append(header(provenance, page_map, commit))
    text = etree.SubElement(root, tei("text"))
    text.set(XML_LANG, "nl")
    etree.SubElement(text, tei("front")).extend(deepcopy(v.front) for v in volumes)
    main = etree.SubElement(text, tei("body"))
    main.set("n", URN)
    main.set(XML_LANG, "nl")
    main.extend(deepcopy(node) for volume in volumes for node in volume.body)
    if backs := [v.back for v in volumes if v.back is not None]:
        etree.SubElement(text, tei("back")).extend(deepcopy(back) for back in backs)
    _indent(root, 0)
    return (
        b'<?xml version="1.0" encoding="UTF-8"?>\n'
        + f"<?xml-model {XML_MODEL}?>\n".encode()
        + etree.tostring(root, encoding="UTF-8", xml_declaration=False)
        + b"\n"
    )


def _division(number: int, nodes: list[etree._Element]) -> etree._Element:
    division = etree.Element(tei("div"))
    division.set("type", "volume")
    division.set("n", str(number))
    division.extend(nodes)
    return division


def _record(registry: Mapping[str, Any], volume: int, kind: str) -> Mapping[str, Any]:
    wanted = f"gd1-vol{volume}-{kind}"
    for record in registry["sources"]:
        if record["id"] == wanted:
            return record
    raise ConversionError(f"the registry has no source {wanted!r}")


def _indent(element: etree._Element, level: int) -> None:
    """Put each child of an element-only element on its own line, indented by depth.

    Mixed content keeps its whitespace as converted, except that a footnote of several
    paragraphs inside it is indented too, so its paragraphs never run together.
    """
    if not _element_only(element):
        for child in element:
            _indent(child, level + 1)
        return
    inner = "\n" + INDENT * (level + 1)
    element.text = inner
    for child in element:
        child.tail = inner
        _indent(child, level + 1)
    element[-1].tail = "\n" + INDENT * level


def _element_only(element: etree._Element) -> bool:
    if element.tag not in STRUCTURAL or not len(element):
        return False
    if (element.text or "").strip() or any((child.tail or "").strip() for child in element):
        return False
    return element.tag != tei("note") or all(c.tag in (tei("p"), tei("list")) for c in element)
