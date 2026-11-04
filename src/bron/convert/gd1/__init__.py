"""Conversion of the first edition of Bavinck's Gereformeerde Dogmatiek (GD¹) to TEI.

`bron convert gd1` turns the four Distributed Proofreaders transcriptions on Project
Gutenberg into one TEI file, once. The modules follow the steps: `fetch` gets each volume
as registered, `html` reads it and maps its inline markup, `regions` splits it into front
matter, body and back matter, `structure` builds chapters, sections and subparagraphs,
`pages`, `notes` and `corrections` encode page breaks, footnotes and the transcribers'
corrections, `header` writes the TEI header, and `emit` assembles and serializes the file.
"""

from collections.abc import Callable, Mapping
from typing import Any

from lxml import etree

# The `resp` pointers of what the converter derives and what language tagging adds; the
# header declares both under these ids.
CONVERTER = "#bron-convert"
TAGGER = "#bron-langid"

# Fills a new TEI element with the converted content of a source element.
Fill = Callable[[etree._Element, etree._Element], None]


class ConversionError(Exception):
    """The source cannot be converted as it stands; the message says where."""


def source_record(registry: Mapping[str, Any], volume: int, kind: str) -> Mapping[str, Any]:
    """A volume's registry record: `kind` is `gutenberg` (the text) or `dbnl` (the scan)."""
    wanted = f"gd1-vol{volume}-{kind}"
    for record in registry["sources"]:
        if record["id"] == wanted:
            return record
    raise ConversionError(f"the registry has no source {wanted!r}")
