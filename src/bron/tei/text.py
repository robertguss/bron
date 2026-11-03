"""Plain-text views of TEI elements, normalized so two readings compare equal."""

import unicodedata

from lxml import etree


def normalized_text(element: etree._Element) -> str:
    """All text under `element`, notes included, NFC-normalized with whitespace collapsed."""
    raw = "".join(element.itertext())
    return " ".join(unicodedata.normalize("NFC", raw).split())
