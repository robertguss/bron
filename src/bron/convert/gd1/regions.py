"""A volume's regions: front matter, body and back matter, split at named anchors.

Each volume runs from its title page through the body to the transcribers' notes. The
boundaries are named here per volume by the id of the HTML element that opens each region,
and conversion fails if one is missing, so a change in the source cannot shift text from
one region to another unnoticed. The front matter (title page, Voorbericht, Inhoud) and vol.
4's back matter (the Breedere inhoudsopgave and the registers, from p. 530) are encoded but
not citable. The transcribers' notes become provenance in the TEI header.
"""

from dataclasses import dataclass, field

from lxml import etree

from bron.convert.gd1 import ConversionError
from bron.convert.gd1.html import blocks


@dataclass(frozen=True)
class Boundaries:
    body: str  # the element that opens the body: the marker of p. 1
    back: str | None  # the element that opens the back matter, in a volume that has one
    notes: str  # the transcribers' notes, which follow the book's last page


REGIONS = {
    1: Boundaries(body="Page_1", back=None, notes="noot"),
    2: Boundaries(body="Page_1", back=None, notes="noot"),
    3: Boundaries(body="Page_1", back=None, notes="noot"),
    4: Boundaries(body="Page_1", back="_inhoud", notes="noot"),
}


@dataclass
class Regions:
    front: list[etree._Element] = field(default_factory=list)
    body: list[etree._Element] = field(default_factory=list)
    back: list[etree._Element] = field(default_factory=list)
    notes: list[etree._Element] = field(default_factory=list)


def split(body: etree._Element, volume: int) -> Regions:
    """The volume's blocks, region by region, in document order."""
    bounds = REGIONS[volume]
    starts = [("body", bounds.body), ("back", bounds.back), ("notes", bounds.notes)]
    starts = [(name, anchor) for name, anchor in starts if anchor is not None]
    regions = Regions()
    current = regions.front
    for block in blocks(body):
        if starts and block.get("id") == starts[0][1]:
            current = getattr(regions, starts.pop(0)[0])
        current.append(block)
    if starts:
        name, anchor = starts[0]
        raise ConversionError(f"vol. {volume}: the {name} boundary #{anchor} is missing")
    return regions
