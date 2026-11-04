"""The theologienet PDFs of the fourth printing: two book pages to every PDF page.

Each PDF page is a spread, stored rotated, with its scan as one image or as two stacked
image layers. A spread is rendered at the scale of its largest embedded image, so its pixels
are the scan's own, and cut at the gutter: the lightest column near the middle. The text
layer's characters are placed on the displayed spread and divided the same way, left page
then right. Left pages are even and right pages odd, and each half's running head gives
its printed number.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from bron.ocr import OcrError
from bron.ocr.pagemap import Entry, page_map

if TYPE_CHECKING:
    import pypdfium2 as pdfium
    from PIL import Image

# The gutter is looked for within this fraction of the spread's width either side of centre.
GUTTER_WINDOW = 0.12
# Spreads are rendered small to find the gutter, which is then scaled to the scan.
PREVIEW_SCALE = 0.4


@dataclass(frozen=True)
class Half:
    """One book page of a spread: which spread, which side, and its text lines."""

    spread: int
    side: int  # 0 left, 1 right
    lines: tuple[str, ...]


def native_scale(page: pdfium.PdfPage) -> float:
    """Pixels per point at which the spread renders at its largest image's own resolution."""
    import pypdfium2 as pdfium

    width, height = page.get_size()
    long_side = max(width, height)
    pixels = [
        max(obj.get_px_size())
        for obj in page.get_objects()
        if obj.type == pdfium.raw.FPDF_PAGEOBJ_IMAGE
    ]
    if not pixels:
        raise OcrError("the PDF page holds no scanned image")
    return max(pixels) / long_side


def render(page: pdfium.PdfPage) -> Image.Image:
    """The displayed spread at its scan's own resolution, in greyscale."""
    return page.render(scale=native_scale(page), grayscale=True).to_pil().convert("L")


def gutter(image: Image.Image) -> int:
    """The x of the lightest column within the window around the spread's centre."""
    import numpy as np

    columns = np.asarray(image, dtype=float).mean(axis=0)
    centre, reach = image.width // 2, int(image.width * GUTTER_WINDOW)
    window = columns[centre - reach : centre + reach]
    return centre - reach + int(window.argmax())


def split(image: Image.Image, x: int) -> tuple[Image.Image, Image.Image]:
    return image.crop((0, 0, x, image.height)), image.crop((x, 0, image.width, image.height))


class Placed(Protocol):
    """What placing a point on the displayed page needs from a PDF page."""

    def get_rotation(self) -> int: ...

    def get_cropbox(self) -> tuple[float, float, float, float]: ...


def _to_display(page: Placed, x: float, y: float) -> tuple[float, float]:
    """A point in unrotated page space, in displayed coordinates with the origin top left.

    The display is the crop box, which these PDFs set apart from the media box.
    """
    left, bottom, right, top = page.get_cropbox()
    width, height = right - left, top - bottom
    x, y = x - left, y - bottom
    match page.get_rotation():
        case 0:
            return x, height - y
        case 90:
            return y, x
        case 180:
            return width - x, y
        case 270:
            return height - y, width - x
    raise OcrError(f"unexpected page rotation {page.get_rotation()}")


def halves(page: pdfium.PdfPage, spread: int, gutter_px: int, scale: float) -> list[Half]:
    """The spread's text layer divided at the gutter: left page, then right page."""
    textpage = page.get_textpage()
    text = textpage.get_text_range()
    cut = gutter_px / scale
    sides: list[list[str]] = [[], []]
    current = 0
    for i, char in enumerate(text):
        if char in "\r\n":
            sides[current].append("\n")
            continue
        box = textpage.get_charbox(i)
        if box != (0, 0, 0, 0):
            x, _ = _to_display(page, (box[0] + box[2]) / 2, (box[1] + box[3]) / 2)
            current = 0 if x < cut else 1
        sides[current].append(char)
    return [
        Half(
            spread, side, tuple(line.strip() for line in "".join(chars).split("\n") if line.strip())
        )
        for side, chars in enumerate(sides)
    ]


@dataclass(frozen=True)
class Spreads:
    """A theologienet volume read spread by spread."""

    halves: tuple[Half, ...]
    gutters: tuple[int, ...]
    scales: tuple[float, ...]

    def page_map(self) -> list[Entry]:
        """Printed page of each half, the halves numbered 1, 2, 3 … in reading order."""
        return page_map([half.lines for half in self.halves])


def read_volume(path: Path) -> Spreads:
    """Every spread of a volume: its halves' text, gutter and render scale."""
    import pypdfium2 as pdfium

    pdf = pdfium.PdfDocument(path)
    try:
        found: list[Half] = []
        gutters, scales = [], []
        for index in range(len(pdf)):
            page = pdf[index]
            scale = native_scale(page)
            preview = page.render(scale=PREVIEW_SCALE, grayscale=True).to_pil().convert("L")
            x = round(gutter(preview) * scale / PREVIEW_SCALE)
            found.extend(halves(page, index, x, scale))
            gutters.append(x)
            scales.append(scale)
        return Spreads(tuple(found), tuple(gutters), tuple(scales))
    finally:
        pdf.close()


def render_half(path: Path, spread: int, side: int, gutter_px: int) -> Image.Image:
    """One book page of a spread, at the scan's own resolution."""
    import pypdfium2 as pdfium

    pdf = pdfium.PdfDocument(path)
    try:
        return split(render(pdf[spread]), gutter_px)[side]
    finally:
        pdf.close()


def page_text(spreads: Spreads, half_number: int) -> Sequence[str]:
    """The text lines of a half, numbered from 1 in reading order."""
    return spreads.halves[half_number - 1].lines
