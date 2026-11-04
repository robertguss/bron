"""Page breaks: every printed page of a volume as a `pb` linked to its page of the scan.

Each `pb` carries the printed page number, an `xml:id` unique across the four volumes, and
a `facs` link to that page of DBNL's PDF of the volume, read from the measured page map
(`pagemap.py`), never computed. The transcription marks a page with an element whose id is
`Page_N`: usually a `span.pagenum` showing "[N]", sometimes a heading, a `div` or an empty
anchor. The number is always taken from the id. A marker whose visible label is not its
number (vol. 4 p. 484 shows "]") is listed in `malformed` for the conversion report.

Two pages carry no marker at all: vol. 1 p. VI, where the Inhoud opens, and vol. 2 p. 386,
where Hoofdstuk V opens. Their page breaks are inserted before the element that opens the
page and carry `resp="#bron-convert"`, so a derived break is never mistaken for a
transcribed one. Every page in the map must appear exactly once per volume.
"""

import re
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from lxml import etree

from bron.convert.gd1 import CONVERTER, ConversionError
from bron.tei import XML_ID, tei

PAGE_ID = re.compile(r"Page_([0-9]+|[IVXLC]+)")

# Unmarked pages, by volume: the id of the element that opens the page, and its number.
INSERTED = {1: {"toc": "VI"}, 2: {"para_29": "386"}}


@dataclass
class PageBreaks:
    """One volume's page breaks, made as its markers are met."""

    volume: int
    pdf: str
    pdf_pages: dict[str, int]  # printed page -> page of the PDF, in printed order
    found: list[str] = field(default_factory=list)
    inserted: list[str] = field(default_factory=list)
    malformed: list[tuple[str, str]] = field(default_factory=list)  # (page, label shown)

    def make(self, page: str, *, inserted: bool = False) -> etree._Element:
        if page not in self.pdf_pages:
            raise ConversionError(f"vol. {self.volume}: page {page} is not in the page map")
        page_break = etree.Element(tei("pb"))
        page_break.set("n", page)
        page_break.set(XML_ID, f"v{self.volume}-p{page}")
        page_break.set("facs", f"{self.pdf}#page={self.pdf_pages[page]}")
        if inserted:
            page_break.set("resp", CONVERTER)
            self.inserted.append(page)
        self.found.append(page)
        return page_break

    def marker(self, source: etree._Element) -> etree._Element | None:
        """The page break an HTML element marks, if its id names a page."""
        match = PAGE_ID.fullmatch(source.get("id") or "")
        if match is None:
            return None
        page = match.group(1)
        if "pagenum" in (source.get("class") or "").split():
            shown = "".join(source.itertext()).strip()
            if shown.strip("[]") != page:
                self.malformed.append((page, shown))
        return self.make(page)

    def before(self, source: etree._Element) -> list[etree._Element]:
        """The page breaks that come before a block: an unmarked page that opens there,
        then the page the block itself marks."""
        found = []
        if page := INSERTED.get(self.volume, {}).get(source.get("id") or ""):
            found.append(self.make(page, inserted=True))
        if (page_break := self.marker(source)) is not None:
            found.append(page_break)
        return found

    def check_complete(self) -> None:
        """Every page of the map appears exactly once."""
        counts = Counter(self.found)
        missing = [page for page in self.pdf_pages if counts[page] == 0]
        repeated = [page for page in self.pdf_pages if counts[page] > 1]
        problems = []
        if missing:
            problems.append(f"no page break for pages {', '.join(missing)}")
        if repeated:
            problems.append(f"more than one page break for pages {', '.join(repeated)}")
        if problems:
            raise ConversionError(f"vol. {self.volume}: {'; '.join(problems)}")


def for_volume(page_map: Mapping[str, Any], volume: int) -> PageBreaks:
    """The page breaks of one volume of the page map."""
    for entry in page_map["volumes"]:
        if entry["volume"] == volume:
            pages = {str(page["n"]): int(page["pdf"]) for page in entry["pages"]}
            return PageBreaks(volume, entry["pdf"], pages)
    raise ConversionError(f"the page map has no vol. {volume}")
