"""Chapters, sections and subparagraphs: the citable structure of GD¹.

The body of each volume opens with `<milestone unit="volume">` and that volume's first page
break. Each `h2` opens an uncited `<div type="chapter">`, and a part title printed before it
(Deel I, Deel II) becomes the chapter's `<head type="part">`. Each `h3` "§ N." opens
`<div type="section" n="N" xml:id="sec-N">`. Within a section, in source order:

- a paragraph whose text opens with "N. ", once page breaks and empty anchors are skipped
  and a correction is read as corrected, opens `<div type="subparagraph" n="N">`;
- a paragraph without a number continues the open subparagraph;
- a lettered `h4` ("A. Opkomst der dogmatiek") becomes the `head` of the subparagraph the
  next numbered paragraph opens. An `h4` not followed by a numbered paragraph stops the
  conversion.

A page break that falls between blocks goes where the next block goes: before a chapter,
at the start of a section, or into the subparagraph the next paragraph belongs to, so a
subparagraph that begins a page opens with that page's `pb`.

The number check then holds every § to the next number and every subparagraph to 1, 2, 3
and so on, allowing only the gaps the print itself has (the page map's `numbering`). The
front and back matter keep the transcription's headings as nested, uncited divisions.
"""

import re
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass, field
from typing import Any

from lxml import etree

from bron.convert.gd1 import ConversionError
from bron.convert.gd1.corrections import printed_number
from bron.convert.gd1.html import Converter, is_container, is_skipped, leading_breaks
from bron.tei import XML_ID, tei

NUMBERED = re.compile(r"(\d+)\.\s")
SECTION = re.compile(r"§\s*(\d+)\b")
CHAPTER = re.compile(r"HOOFDSTUK\s+([IVXLC]+)", re.IGNORECASE)
LEVELS = {"h1": 1, "h2": 1, "h3": 2, "h4": 3}


@dataclass(frozen=True)
class Subparagraph:
    n: int
    line: int | None


@dataclass
class Section:
    volume: int
    n: int
    line: int | None
    subparagraphs: list[Subparagraph] = field(default_factory=list)


def allowed_gaps(page_map: Mapping[str, Any]) -> set[tuple[int, int]]:
    """(§, subparagraph) pairs the print does not have, as read on the scans."""
    return {
        (int(item["section"]), int(item["missing"]))
        for item in page_map.get("numbering") or []
        if "missing" in item
    }


def printed_headings(page_map: Mapping[str, Any]) -> dict[int, int]:
    """The number each misnumbered § heading prints, by the § it is cited as."""
    return {int(item["section"]): int(item["printed"]) for item in page_map.get("headings") or []}


def body(
    source: Iterable[etree._Element],
    converter: Converter,
    volume: int,
    printed: Mapping[int, int],
) -> tuple[list[etree._Element], list[Section]]:
    """One volume's body as TEI, and the numbers of its sections and subparagraphs."""
    milestone = etree.Element(tei("milestone"))
    milestone.set("unit", "volume")
    milestone.set("n", str(volume))
    out: list[etree._Element] = [milestone]
    sections: list[Section] = []
    pending: list[etree._Element] = []  # page breaks waiting for the next block
    held: list[etree._Element] = []  # a lettered heading waiting for its subparagraph
    held_at: tuple[int | None, str] = (None, "")
    parts: list[etree._Element] = []  # part titles waiting for their chapter
    chapter = section = subparagraph = None

    def unheaded() -> ConversionError:
        line, text = held_at
        return ConversionError(
            f"vol. {volume}, line {line}: the heading {text!r} is not followed by a numbered "
            "paragraph"
        )

    for block in source:
        pending += converter.pages.before(block)
        if is_container(block) or is_skipped(block):
            continue
        tag = block.tag
        if held and tag != "p":
            raise unheaded()
        where = f"vol. {volume}, line {block.sourceline}"
        if tag == "div":
            head = converter.block(block)
            head.tag = tei("head")
            head.set("type", "part")
            parts.append(head)
        elif tag == "h2":
            head, early = _heading(converter, block)
            chapter = etree.Element(tei("div"))
            chapter.set("type", "chapter")
            if found := CHAPTER.search(_text(head)):
                chapter.set("n", found.group(1).upper())
            out += [*pending, *early, chapter]
            chapter.extend([*parts, head])
            pending, parts, section, subparagraph = [], [], None, None
        elif tag == "h3":
            head, early = _heading(converter, block)
            found = SECTION.match(_text(head))
            if chapter is None or found is None:
                raise ConversionError(
                    f"{where}: a § heading must open with its number in a chapter"
                )
            number = int(found.group(1))
            if number in printed:
                printed_number(head, number, printed[number])
            section = etree.SubElement(chapter, tei("div"))
            section.set("type", "section")
            section.set("n", str(number))
            section.set(XML_ID, f"sec-{number}")
            section.extend([*pending, *early, head])
            sections.append(Section(volume, number, block.sourceline))
            pending, subparagraph = [], None
        elif tag == "h4":
            if section is None:
                raise ConversionError(f"{where}: a lettered heading outside any §")
            head, early = _heading(converter, block)
            held, pending = [*pending, *early, head], []
            held_at = (block.sourceline, _text(head))
        elif tag == "p":
            paragraph = converter.block(block)
            early = leading_breaks(paragraph)
            found = NUMBERED.match(_opening(paragraph))
            if found is None:
                if held:
                    raise unheaded()
                if subparagraph is None:
                    raise ConversionError(f"{where}: a paragraph before the first subparagraph")
            else:
                if section is None:
                    raise ConversionError(f"{where}: a numbered paragraph outside any §")
                subparagraph = etree.SubElement(section, tei("div"))
                subparagraph.set("type", "subparagraph")
                subparagraph.set("n", found.group(1))
                sections[-1].subparagraphs.append(
                    Subparagraph(int(found.group(1)), block.sourceline)
                )
                subparagraph.extend(held)
                held = []
            subparagraph.extend([*pending, *early, paragraph])
            pending = []
        else:
            raise ConversionError(f"{where}: unexpected <{tag}> in the body")
    if held:
        raise unheaded()
    if pending:
        last = next((e for e in (subparagraph, section, chapter) if e is not None), None)
        if last is None:
            out += pending
        else:
            last.extend(pending)
    return out, sections


def matter(source: Iterable[etree._Element], converter: Converter) -> list[etree._Element]:
    """Front or back matter as uncited divisions, nested as the headings nest.

    Each heading opens a division at its level. Each of the transcribers' page-sized
    containers, and any text before the first heading, opens a new top-level division.
    """
    out: list[etree._Element] = []
    stack: list[tuple[int, etree._Element]] = []
    pending: list[etree._Element] = []

    def place(*nodes: etree._Element) -> None:
        (stack[-1][1] if stack else out).extend(nodes)

    for block in source:
        pending += converter.pages.before(block)
        if is_container(block):
            stack.clear()
            continue
        if is_skipped(block):
            continue
        if block.tag in LEVELS:
            level = LEVELS[str(block.tag)]
            head, early = _heading(converter, block)
            while stack and stack[-1][0] >= level:
                stack.pop()
            division = etree.Element(tei("div"))
            place(*pending, *early, division)
            division.append(head)
            stack.append((level, division))
        else:
            node = converter.block(block)
            if not stack:
                division = etree.Element(tei("div"))
                place(division)
                stack.append((1, division))
            place(*pending, node)
        pending = []
    place(*pending)
    return out


def check_numbers(
    sections: list[Section], allowed: set[tuple[int, int]], *, first: int | None = None
) -> list[tuple[int, int, int]]:
    """The (volume, §, subparagraph) gaps found, all of them allowed; raises otherwise.

    The §§ must follow each other without a gap, from `first` when given, and each §'s
    subparagraphs must run 1, 2, 3... with only the allowed numbers missing.
    """
    problems: list[str] = []
    gaps: list[tuple[int, int, int]] = []
    expected = first if first is not None else (sections[0].n if sections else None)
    for section in sections:
        if expected is not None and section.n != expected:
            problems.append(
                f"vol. {section.volume}, line {section.line}: "
                + _out_of_sequence("§", expected, section.n)
            )
        expected = section.n + 1
        number = 0
        for subparagraph in section.subparagraphs:
            number += 1
            while number < subparagraph.n and (section.n, number) in allowed:
                gaps.append((section.volume, section.n, number))
                number += 1
            if subparagraph.n != number:
                problems.append(
                    f"vol. {section.volume}, § {section.n}, line {subparagraph.line}: "
                    + _out_of_sequence("subparagraph", number, subparagraph.n)
                )
                number = subparagraph.n
    if problems:
        raise ConversionError("; ".join(problems))
    return gaps


def _out_of_sequence(unit: str, expected: int, found: int) -> str:
    if found > expected:
        return f"{unit} {expected} is missing ({found} follows {expected - 1})"
    return f"{unit} {found} comes again after {expected - 1}"


def _heading(converter: Converter, block: etree._Element) -> tuple[etree._Element, list]:
    """A heading as `head`, and the page breaks it opens with, which go before it."""
    head = converter.block(block)
    return head, leading_breaks(head)


def _text(element: etree._Element) -> str:
    return " ".join("".join(_readable(element)).split())


def _opening(element: etree._Element) -> str:
    return "".join(_readable(element)).lstrip()[:24]


def _readable(element: etree._Element) -> Iterator[str]:
    """The text of an element as it reads: corrections as corrected, notes left out."""
    if element.text:
        yield element.text
    for child in element:
        if child.tag not in (tei("sic"), tei("note")):
            yield from _readable(child)
        if child.tail:
            yield child.tail
