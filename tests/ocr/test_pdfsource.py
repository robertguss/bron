import numpy as np
from PIL import Image

from bron.ocr.pdfsource import _to_display, gutter, split


class Page:
    """The two facts the coordinate mapping reads from a PDF page."""

    def __init__(self, rotation: int, cropbox: tuple[float, float, float, float]) -> None:
        self.rotation, self.cropbox = rotation, cropbox

    def get_rotation(self) -> int:
        return self.rotation

    def get_cropbox(self) -> tuple[float, float, float, float]:
        return self.cropbox


def test_a_spread_stored_rotated_maps_its_text_onto_the_displayed_spread() -> None:
    # The theologienet layout: stored portrait with a 270-degree rotation and a crop box
    # set apart from the media box. The left page's running head sits high in stored y.
    page = Page(270, (32.66, 0.0, 718.18, 902.37))
    left_head = _to_display(page, 669, 784)  # type: ignore[arg-type]
    right_head = _to_display(page, 583, 125)  # type: ignore[arg-type]
    assert left_head[0] < 451 < right_head[0]
    assert left_head[1] < 100 and right_head[1] < 200


def test_the_gutter_is_the_lightest_column_near_the_middle() -> None:
    pixels = np.full((100, 400), 255, dtype=np.uint8)
    pixels[:, 30:190] = 60  # left page's text block
    pixels[:, 215:380] = 60  # right page's text block
    pixels[:, 0:5] = 255
    image = Image.fromarray(pixels, mode="L")
    x = gutter(image)
    assert 190 <= x < 215
    left, right = split(image, x)
    assert left.width + right.width == 400
