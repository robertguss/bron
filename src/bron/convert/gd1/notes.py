"""Footnotes, encoded once at their callouts.

The transcription collects a footnote's paragraphs in a `div.footnotes` block after the
paragraph that calls it. Each footnote becomes `<note place="bottom">` at its callout
(`a.fnanchor`), numbered with the label the book prints ("1", "*", "A"), and the block
itself is dropped from the text, so the note's words appear exactly once.
"""

from collections.abc import Callable

from lxml import etree

from bron.convert.gd1 import ConversionError
from bron.tei import tei

Fill = Callable[[etree._Element, etree._Element], None]


class Footnotes:
    """The footnotes of one volume, by the id of their label."""

    def __init__(self, body: etree._Element) -> None:
        self.paragraphs: dict[str, list[etree._Element]] = {}
        self.placed: list[str] = []
        for block in body.iter("div"):
            if "footnotes" not in (block.get("class") or "").split():
                continue
            current = None
            for paragraph in block.iter("p"):
                for anchor in paragraph.iter("a"):
                    if (name := anchor.get("id") or "").startswith("Footnote_"):
                        current = name
                        self.paragraphs[current] = []
                if current is None:
                    raise ConversionError(
                        f"line {paragraph.sourceline}: a footnote paragraph with no footnote label"
                    )
                self.paragraphs[current].append(paragraph)

    def note(self, callout: etree._Element, fill: Fill) -> etree._Element:
        """The footnote a callout calls, as a `note` to put in the callout's place."""
        target = (callout.get("href") or "").removeprefix("#")
        if target not in self.paragraphs:
            raise ConversionError(f"line {callout.sourceline}: callout to a missing {target}")
        if target in self.placed:
            raise ConversionError(f"line {callout.sourceline}: {target} is called twice")
        self.placed.append(target)
        note = etree.Element(tei("note"))
        note.set("place", "bottom")
        note.set("n", "".join(callout.itertext()).strip().strip("[]"))
        paragraphs = self.paragraphs[target]
        if len(paragraphs) == 1:
            fill(paragraphs[0], note)
        else:
            for paragraph in paragraphs:
                fill(paragraph, etree.SubElement(note, tei("p")))
        return note

    def check_placed(self) -> None:
        """Every footnote was placed at a callout."""
        if unplaced := [name for name in self.paragraphs if name not in self.placed]:
            raise ConversionError(f"footnotes never called: {', '.join(unplaced)}")
