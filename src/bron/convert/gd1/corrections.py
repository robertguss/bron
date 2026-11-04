"""The transcribers' corrections, kept visible beside the printed reading.

Distributed Proofreaders mark each correction as `<ins title="PRINTED">CORRECTED</ins>`. It
becomes `<choice><sic>PRINTED</sic><corr>CORRECTED</corr></choice>`, so the print's reading
is never lost. Where the title is a note that a missing word was inserted ("ingevoegd")
rather than a reading, the `sic` is empty and the note follows as `<note type="transcriber">`.
A title writes superscript in braces ("3{9}"), which is restored as superscript. One
correction in vol. 4 is malformed in the transcription, its title spilled into its text as
`title="elkandar">elkander`, and is read the same way.

The printed headings of vol. 2 §§ 27-33 carry wrong numbers, which the book's own Inhoud
corrects and the transcribers corrected silently. The converter restores each printed
number beside the corrected one, as a `choice` with `resp="#bron-convert"`.
"""

import re
from collections.abc import Callable

from lxml import etree

from bron.convert.gd1 import ConversionError
from bron.tei import tei

Fill = Callable[[etree._Element, etree._Element], None]

CONVERTER = "#bron-convert"
INSERTION = "ingevoegd"
SPILLED_TITLE = re.compile(r'title="([^"]*)">(.*)', re.DOTALL)
SUPERSCRIPT = re.compile(r"\{([^}]*)\}")


def choice(ins: etree._Element, fill: Fill) -> list[etree._Element]:
    """A correction as `choice`, followed by the transcribers' note when it has one."""
    encoded = etree.Element(tei("choice"))
    sic = etree.SubElement(encoded, tei("sic"))
    corr = etree.SubElement(encoded, tei("corr"))
    fill(ins, corr)
    title = ins.get("title")
    if title is None:
        spilled = SPILLED_TITLE.fullmatch(corr.text or "") if not len(corr) else None
        if spilled is None:
            raise ConversionError(f"line {ins.sourceline}: a correction with no printed reading")
        title, corr.text = spilled.group(1), spilled.group(2)
    if INSERTION in title:
        note = etree.Element(tei("note"))
        note.set("type", "transcriber")
        note.text = title
        return [encoded, note]
    parts = SUPERSCRIPT.split(title)
    sic.text = parts[0] or None
    for index in range(1, len(parts), 2):
        superscript = etree.SubElement(sic, tei("hi"), rend="superscript")
        superscript.text = parts[index]
        superscript.tail = parts[index + 1] or None
    return [encoded]


def printed_number(head: etree._Element, section: int, printed: int) -> None:
    """Put the number a § heading prints beside the number it is cited by."""
    pattern = re.compile(rf"(§\s*){section}\b")
    slots: list[tuple[etree._Element, bool]] = [(head, True), *((c, False) for c in head)]
    for holder, is_text in slots:
        value = (holder.text if is_text else holder.tail) or ""
        found = pattern.search(value)
        if found is None:
            continue
        encoded = etree.Element(tei("choice"))
        encoded.set("resp", CONVERTER)
        etree.SubElement(encoded, tei("sic")).text = str(printed)
        etree.SubElement(encoded, tei("corr")).text = str(section)
        encoded.tail = value[found.end() :]
        if is_text:
            holder.text = value[: found.end(1)]
            holder.insert(0, encoded)
        else:
            holder.tail = value[: found.end(1)]
            holder.addnext(encoded)
        return
    raise ConversionError(f"line {head.sourceline}: § {section} not found in its heading")
