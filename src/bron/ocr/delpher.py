"""Delpher's scans of the second printing: page list, page images, ALTO and page numbers.

A volume's DIDL record (KB's OAI service) lists every scan in order with the resolver URLs
of its image and ALTO, each with the MD5 the KB publishes. The public image is a JPEG 2000
at half the size of the master scan Delpher's own OCR read, so the ALTO's coordinates are
scaled by one half into the image Bron reads. Printed page numbers come from the volume
PDF's text layer, one download per volume.
"""

import re
import struct
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from lxml import etree

from bron.ocr import OcrError

if TYPE_CHECKING:
    from PIL import Image

OAI = "https://services.kb.nl/mdo/oai"
RESOLVER = "https://resolver.kb.nl/resolve?urn="

# How far a scaled ALTO page may differ from the image, in pixels, on each axis.
SIZE_TOLERANCE = 2

_DIDL = "urn:mpeg:mpeg21:2002:02-DIDL-NS"
_DC = "http://purl.org/dc/elements/1.1/"
_SCAN_ID = re.compile(r"^[A-Z0-9]+:\d+:(\d{5})$")


def didl_url(volume_id: str) -> str:
    collection = volume_id.split(":")[0]
    return f"{OAI}?verb=GetRecord&identifier=BOEKEN:{collection}:{volume_id}&metadataPrefix=didl"


def pdf_url(volume_id: str) -> str:
    return f"{RESOLVER}{volume_id}:pdf"


@dataclass(frozen=True)
class Scan:
    """One scan of a volume, with its resources and the KB's checksums for them."""

    seq: int
    identifier: str
    image_url: str
    image_md5: str
    alto_url: str
    alto_md5: str


def parse_didl(data: bytes) -> list[Scan]:
    """Every scan the DIDL record lists, in scan order."""
    root = etree.fromstring(data)
    scans = []
    for item in root.iter(f"{{{_DIDL}}}Item"):
        identifier = item.get(f"{{{_DC}}}identifier", "")
        if not (match := _SCAN_ID.match(identifier)):
            continue
        resources = dict(_resources(item, identifier))
        if "image" not in resources or "alto" not in resources:
            raise OcrError(f"{identifier}: the DIDL record lacks its image or ALTO")
        (image_url, image_md5), (alto_url, alto_md5) = resources["image"], resources["alto"]
        scans.append(
            Scan(int(match.group(1)), identifier, image_url, image_md5, alto_url, alto_md5)
        )
    scans.sort(key=lambda scan: scan.seq)
    if [scan.seq for scan in scans] != list(range(1, len(scans) + 1)):
        raise OcrError("the DIDL record's scans are not numbered 1, 2, 3 … without a gap")
    return scans


def pdf_md5(data: bytes) -> str:
    """The MD5 the DIDL record publishes for the volume's PDF."""
    root = etree.fromstring(data)
    for component in root.iter(f"{{{_DIDL}}}Component"):
        if component.get(f"{{{_DC}}}identifier", "").endswith(":pdf"):
            checksum = component.find(f".//{{{_DIDL}}}Statement[@{{{_DC}}}type='md5']")
            if checksum is not None and checksum.text:
                return checksum.text.strip().lower()
    raise OcrError("the DIDL record publishes no MD5 for the volume's PDF")


def _resources(item: etree._Element, identifier: str) -> Iterator[tuple[str, tuple[str, str]]]:
    for component in item.iter(f"{{{_DIDL}}}Component"):
        kind = component.get(f"{{{_DC}}}identifier", "").removeprefix(identifier + ":")
        if kind not in ("image", "alto"):
            continue
        resource = component.find(f"{{{_DIDL}}}Resource")
        checksum = component.find(f".//{{{_DIDL}}}Statement[@{{{_DC}}}type='md5']")
        if resource is None or checksum is None or not checksum.text:
            raise OcrError(f"{identifier}: its {kind} has no URL or no MD5")
        url = resource.get("ref", "").replace("http://", "https://", 1)
        yield kind, (url, checksum.text.strip().lower())


def jp2_size(data: bytes) -> tuple[int, int]:
    """Width and height of a JPEG 2000 image, read from its codestream header."""
    start = data.find(b"\xff\x4f\xff\x51")
    if start < 0 or len(data) < start + 24:
        raise OcrError("not a JPEG 2000 codestream")
    width, height, x0, y0 = struct.unpack(">IIII", data[start + 8 : start + 24])
    return width - x0, height - y0


def open_scan(path: Path) -> Image.Image:
    """A cached scan opened as JPEG 2000 only, so a download in another format is refused.

    Pillow otherwise picks a decoder from the bytes, whatever the file is called, and some of
    its decoders hand the file to outside programs such as Ghostscript.
    """
    from PIL import Image, UnidentifiedImageError

    try:
        return Image.open(path, formats=["JPEG2000"])
    except UnidentifiedImageError as error:
        raise OcrError(f"{path} is not a JPEG 2000 image") from error


def alto_page_size(data: bytes) -> tuple[int, int]:
    root = etree.fromstring(data)
    page = next(root.iter("{*}Page"), None)
    if page is None:
        raise OcrError("the ALTO has no Page")
    return int(page.get("WIDTH", "0")), int(page.get("HEIGHT", "0"))


def alto_scale(image: tuple[int, int], alto: tuple[int, int]) -> float:
    """The factor taking the ALTO's coordinates into the image: one half, or an error."""
    if all(abs(2 * i - a) <= SIZE_TOLERANCE for i, a in zip(image, alto, strict=True)):
        return 0.5
    raise OcrError(
        f"the image is {image[0]}x{image[1]} and its ALTO page {alto[0]}x{alto[1]}; "
        "Bron expects Delpher's public image at half the master's size"
    )


def pdf_page_texts(path: Path) -> list[list[str]]:
    """The text lines of every page of a PDF's text layer, in page order."""
    import pypdfium2 as pdfium

    pdf = pdfium.PdfDocument(path)
    try:
        return [_lines(pdf[i].get_textpage().get_text_range()) for i in range(len(pdf))]
    finally:
        pdf.close()


def _lines(text: str) -> list[str]:
    return [line.strip() for line in re.split(r"[\r\n]+", text) if line.strip()]


@dataclass(frozen=True)
class AltoLine:
    """A text line of an ALTO page: its text, box (x, y, width, height) and type size."""

    text: str
    box: tuple[int, int, int, int]
    size: float | None


def alto_lines(data: bytes) -> list[AltoLine]:
    """Every text line of an ALTO page in its reading order, with its block's type size."""
    root = etree.fromstring(data)
    sizes = {
        style.get("ID"): float(style.get("FONTSIZE", "0") or 0)
        for style in root.iter("{*}TextStyle")
    }
    lines = []
    for block in root.iter("{*}TextBlock"):
        refs = (block.get("STYLEREFS") or "").split()
        size = next((sizes[r] for r in refs if r in sizes), None)
        for line in block.iter("{*}TextLine"):
            words: list[str] = []
            for item in line.iter("{*}String", "{*}HYP"):
                content = item.get("CONTENT", "")
                if not content:
                    continue
                if etree.QName(item).localname == "HYP" and words:
                    words[-1] += content  # a line-end hyphen belongs to the word it breaks
                else:
                    words.append(content)
            x, y, w, h = (int(float(line.get(k, "0"))) for k in ("HPOS", "VPOS", "WIDTH", "HEIGHT"))
            lines.append(AltoLine(" ".join(words), (x, y, w, h), size))
    return lines
