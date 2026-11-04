import struct
from pathlib import Path

import pytest

from bron.ocr import OcrError
from bron.ocr.delpher import alto_lines, alto_page_size, alto_scale, jp2_size, parse_didl

FIXTURES = Path(__file__).parent.parent / "fixtures" / "ocr" / "delpher"


def test_the_didl_record_lists_each_scan_with_its_resources_and_checksums() -> None:
    scans = parse_didl((FIXTURES / "didl-3-scans.xml").read_bytes())
    assert [scan.seq for scan in scans] == [1, 2, 3]
    first = scans[0]
    assert first.identifier == "MMUBVU05:000000817:00001"
    assert first.image_url == "https://resolver.kb.nl/resolve?urn=MMUBVU05:000000817:00001:image"
    assert first.alto_url.endswith("MMUBVU05:000000817:00001:alto")
    assert len(first.image_md5) == 32 and first.image_md5 == first.image_md5.lower()


def test_a_didl_record_with_a_gap_in_its_scans_is_refused() -> None:
    data = (FIXTURES / "didl-3-scans.xml").read_text(encoding="utf-8")
    data = data.replace("MMUBVU05:000000817:00002", "MMUBVU05:000000817:00009")
    with pytest.raises(OcrError, match="without a gap"):
        parse_didl(data.encode())


def codestream(width: int, height: int) -> bytes:
    siz = struct.pack(">HHIIIIIIIIH", 41, 0, width, height, 0, 0, width, height, 0, 0, 1)
    return b"\x00\x00\x00\x0cjP  " + b"\xff\x4f\xff\x51" + siz


def test_the_jpeg2000_size_is_read_from_its_header() -> None:
    assert jp2_size(codestream(942, 1416)) == (942, 1416)


def test_the_alto_page_size_is_read_from_its_page() -> None:
    assert alto_page_size((FIXTURES / "alto-v2-p2.xml").read_bytes()) == (1903, 2848)


@pytest.mark.parametrize(
    ("image", "alto"), [((952, 1424), (1903, 2848)), ((942, 1416), (1883, 2831))]
)
def test_the_public_image_at_half_the_masters_size_takes_alto_coordinates_by_half(
    image: tuple[int, int], alto: tuple[int, int]
) -> None:
    assert alto_scale(image, alto) == 0.5


def test_an_image_at_the_masters_own_size_is_refused_with_both_sizes() -> None:
    with pytest.raises(OcrError, match=r"1884x2832.*1883x2831"):
        alto_scale((1884, 2832), (1883, 2831))


def test_a_line_end_hyphen_stays_on_the_word_it_breaks() -> None:
    lines = alto_lines((FIXTURES / "alto-v2-p2.xml").read_bytes())
    broken = next(line for line in lines if line.text.endswith("Alle leer-"))
    assert broken.text.endswith("dogma, de uitsluitende inhoud der gansche dogmatiek. Alle leer-")
    assert sum(line.text.endswith("-") for line in lines) == 5
