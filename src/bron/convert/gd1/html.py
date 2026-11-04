"""A Distributed Proofreaders volume: read from its Gutenberg HTML, and mapped to TEI.

Reading keeps only the book. It drops the Project Gutenberg header and footer, HTML
comments, and the paragraphs the transcribers set in sans-serif, which are their own
navigation links and headings, not print. It strips the bidirectional marks U+200E and
U+200F that the HTML puts around Hebrew for display; Hebrew is stored in logical order, so
removing them changes no character and no order.

`Converter` maps the transcription's markup to TEI. Page markers become `pb`, footnote
callouts become notes, and corrections become `choice` (see `pages`, `notes` and
`corrections`). Italic, bold, superscript, small capitals and letterspacing become `hi`.
The transcribers' language spans become `foreign`. Hyperlinks, abbreviation expansions,
images and rules are dropped, keeping the text they carry. An element with no mapping
stops the conversion, so no text is lost unnoticed.
"""

import re
from collections.abc import Iterator
from dataclasses import dataclass, field

import lxml.html
from lxml import etree

from bron.convert.gd1 import ConversionError
from bron.convert.gd1.corrections import choice
from bron.convert.gd1.notes import Footnotes
from bron.convert.gd1.pages import PageBreaks
from bron.tei import tei

BIDI_MARKS = str.maketrans("", "", "\u200e\u200f")
SANS_SERIF = frozenset({"sansrf", "ssrf"})
BLOCK_TAGS = frozenset({"p", "h1", "h2", "h3", "h4", "div", "table", "ul", "hr"})
HEADINGS = frozenset({"h1", "h2", "h3", "h4"})
WHITESPACE = re.compile(r"[ \t\r\n]+")
CREDITS = re.compile(
    r"Credits:\s*(?:Produced by\s+)?(.+?),?\s+and\s+the Online Distributed Proofreading Team"
)

# Inline elements that become `hi`, and the classes whose rendering `hi` records.
HI_TAGS = {"i": "italic", "b": "bold", "strong": "bold", "sup": "superscript"}
HI_CLASSES = {"smcap": "small-caps", "esp": "letterspaced"}
# Classes whose element is not text: the page label, the duplicate link text the
# transcribers added for handheld readers, and a footnote's own label.
NOT_TEXT = frozenset({"pagenum", "handheld", "label"})
DROPPED_TAGS = frozenset({"img", "hr"})


@dataclass
class Source:
    """One volume's transcription with everything but the book removed."""

    body: etree._Element
    title: str  # the ebook's title, from its header
    transcribers: list[str]  # the people its header credits, before the DP team
    corrections: int  # the `ins` elements in the book's text


def parse(data: bytes) -> Source:
    parser = lxml.html.HTMLParser(encoding="utf-8", remove_comments=True)
    root = lxml.html.document_fromstring(data, parser=parser)
    title, transcribers = "", []
    for header in root.iterfind(".//header[@id='pg-header']"):
        for line in header.iter("p"):
            text = " ".join(line.text_content().split())
            if text.startswith("Title:"):
                title = text.removeprefix("Title:").strip()
            elif match := CREDITS.match(text):
                transcribers = [name.strip() for name in match.group(1).split(",")]
    for boilerplate in root.xpath(".//header[@id='pg-header'] | .//footer[@id='pg-footer']"):
        boilerplate.drop_tree()
    for paragraph in list(root.iter("p")):
        if SANS_SERIF & _classes(paragraph):
            paragraph.drop_tree()
    for element in root.iter():
        element.text = element.text and element.text.translate(BIDI_MARKS)
        element.tail = element.tail and element.tail.translate(BIDI_MARKS)
        if title_attribute := element.get("title"):
            element.set("title", title_attribute.translate(BIDI_MARKS))
    body = root.find("body")
    if body is None:
        raise ConversionError("the HTML has no <body>")
    return Source(body, title, transcribers, sum(1 for _ in body.iter("ins")))


def blocks(element: etree._Element) -> Iterator[etree._Element]:
    """Every block-level element in document order, a container before its contents."""
    for child in element:
        if not isinstance(child.tag, str):
            continue
        yield child
        if is_container(child):
            yield from blocks(child)


def is_container(element: etree._Element) -> bool:
    """A `div` that only groups blocks, such as the transcribers' page-sized divisions."""
    return (
        element.tag == "div"
        and "footnotes" not in _classes(element)
        and any(child.tag in BLOCK_TAGS for child in element)
    )


def is_skipped(element: etree._Element) -> bool:
    """A block that carries no text of its own: a rule, a footnote block, a figure or a
    page marker, whose page break `PageBreaks.before` has already taken."""
    classes = _classes(element)
    return (
        element.tag == "hr"
        or bool(classes & {"footnotes", "pagenum"})
        or (element.tag == "div" and not "".join(element.itertext()).strip())
    )


def leading_breaks(element: etree._Element) -> list[etree._Element]:
    """Remove and return the page breaks an element opens with, before any of its text."""
    found = []
    while not (element.text or "").strip() and len(element) and element[0].tag == tei("pb"):
        page_break = element[0]
        element.text = (element.text or "") + (page_break.tail or "")
        page_break.tail = None
        element.remove(page_break)
        found.append(page_break)
    trim(element)
    return found


def trim(element: etree._Element) -> None:
    """Strip the whitespace an element opens and closes with."""
    element.text = (element.text or "").lstrip() or None
    if len(element):
        last = element[-1]
        last.tail = (last.tail or "").rstrip() or None
    elif element.text:
        element.text = element.text.rstrip() or None


def _classes(element: etree._Element) -> set[str]:
    return set((element.get("class") or "").split())


def _append(target: etree._Element, text: str | None) -> None:
    """Add text at the end of `target`, with runs of whitespace collapsed to one space."""
    if not text:
        return
    text = WHITESPACE.sub(" ", text)
    current = (target[-1].tail if len(target) else target.text) or ""
    if current.endswith(" ") and text.startswith(" "):
        text = text[1:]
    if len(target):
        target[-1].tail = current + text
    else:
        target.text = current + text


@dataclass
class Converter:
    """Maps one volume's HTML to TEI, counting the corrections it converts."""

    pages: PageBreaks
    notes: Footnotes
    corrections: int = field(default=0)

    def block(self, source: etree._Element) -> etree._Element:
        """A paragraph, heading, table or list as TEI."""
        if source.tag in ("p", "div"):
            target = etree.Element(tei("p"))
            self.fill(source, target)
        elif source.tag in HEADINGS:
            target = etree.Element(tei("head"))
            self.fill(source, target)
        elif source.tag == "table":
            target = etree.Element(tei("table"))
            for source_row in source.iter("tr"):
                row = etree.SubElement(target, tei("row"))
                for source_cell in source_row.iterfind("td"):
                    cell = etree.SubElement(row, tei("cell"))
                    if columns := source_cell.get("colspan"):
                        cell.set("cols", columns)
                    self.fill(source_cell, cell)
        elif source.tag == "ul":
            target = etree.Element(tei("list"))
            for source_item in source.iterfind("li"):
                self.fill(source_item, etree.SubElement(target, tei("item")))
        else:
            raise ConversionError(f"line {source.sourceline}: no TEI mapping for <{source.tag}>")
        return target

    def fill(self, source: etree._Element, target: etree._Element) -> None:
        """Convert the content of `source` into `target`, trimmed."""
        self.inline(source, target)
        trim(target)

    def inline(self, source: etree._Element, target: etree._Element) -> None:
        """Append the text and inline elements of `source` to `target`."""
        _append(target, source.text)
        for child in source:
            if isinstance(child.tag, str):
                self._element(child, target)
            _append(target, child.tail)

    def _element(self, source: etree._Element, target: etree._Element) -> None:
        classes = _classes(source)
        if (page_break := self.pages.marker(source)) is not None:
            target.append(page_break)
        tag = str(source.tag)
        if classes & NOT_TEXT or tag in DROPPED_TAGS:
            return
        if tag == "a" and "fnanchor" in classes and source.get("id"):
            target.append(self.notes.note(source, self.fill))
            return
        if tag == "ins":
            self.corrections += 1
            target.extend(choice(source, self.fill))
            return
        if tag == "br":
            etree.SubElement(target, tei("lb"))
            _append(target, " ")
            return
        if source.get("lang"):
            target = etree.SubElement(target, tei("foreign"))
        if tag in HI_TAGS:
            rend = HI_TAGS[tag]
        elif tag == "span":
            rend = " ".join(rend for name, rend in HI_CLASSES.items() if name in classes)
        elif tag in ("a", "abbr"):
            rend = ""
            if tag == "abbr":
                target = etree.SubElement(target, tei("abbr"))
        else:
            raise ConversionError(f"line {source.sourceline}: no TEI mapping for <{tag}>")
        if rend:
            target = etree.SubElement(target, tei("hi"), rend=rend)
        self.inline(source, target)
