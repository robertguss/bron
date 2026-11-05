import hashlib
import struct
from pathlib import Path

import pytest

from bron.ocr import OcrError, delpher
from bron.ocr.download import Downloader
from bron.ocr.manifest import Manifest
from bron.ocr.pagemap import Entry
from bron.ocr.pipeline import Volume, fetch_pages, load_judgments, mark_spans_checked

FIXTURES = Path(__file__).parent.parent / "fixtures" / "ocr" / "delpher"
ALTO = (FIXTURES / "alto-v2-p2.xml").read_bytes()  # its page is 1903x2848


def codestream(width: int, height: int) -> bytes:
    siz = struct.pack(">HHIIIIIIIIH", 41, 0, width, height, 0, 0, width, height, 0, 0, 1)
    return b"\x00\x00\x00\x0cjP  " + b"\xff\x4f\xff\x51" + siz


def setup(tmp_path: Path, image: bytes) -> tuple[Manifest, dict[int, Volume], Downloader]:
    scan = delpher.Scan(
        1,
        "MMUBVU05:000000817:00001",
        "https://resolver.kb.nl/resolve?urn=MMUBVU05:000000817:00001:image",
        hashlib.md5(image).hexdigest(),
        "https://resolver.kb.nl/resolve?urn=MMUBVU05:000000817:00001:alto",
        hashlib.md5(ALTO).hexdigest(),
    )
    volume = Volume(2, "MMUBVU05:000000817", (scan,), (), (Entry(1, 2, "read"),), tmp_path)
    answers = {scan.image_url: (200, image), scan.alto_url: (200, ALTO)}
    downloader = Downloader(
        tmp_path / "cache", {}, answers.__getitem__, lambda _: None, lambda: 0.0
    )
    manifest = Manifest({"pages": [{"id": "v2-p002", "volume": 2, "page": 2}]})
    return manifest, {2: volume}, downloader


def test_an_image_at_the_masters_own_size_is_refused_and_nothing_is_recorded(
    tmp_path: Path,
) -> None:
    manifest, volumes, downloader = setup(tmp_path, codestream(1903, 2848))
    with pytest.raises(OcrError, match="half the master's size"):
        fetch_pages(manifest, volumes, downloader, tmp_path / "cache")
    assert "print2" not in manifest.data["pages"][0]


def test_screening_judgments_are_read_as_booleans(tmp_path: Path) -> None:
    path = tmp_path / "screening.yaml"
    path.write_text("- {volume: 1, page: 326, greek: false, hebrew: true}\n", encoding="utf-8")
    judgments, rows = load_judgments(path)
    assert judgments[(1, 326)].hebrew and not judgments[(1, 326)].greek
    assert rows[0]["page"] == 326


def test_a_quoted_false_judgment_is_refused_not_read_as_true(tmp_path: Path) -> None:
    path = tmp_path / "screening.yaml"
    path.write_text('- {volume: 1, page: 2, greek: "false", hebrew: false}\n', encoding="utf-8")
    with pytest.raises(OcrError, match="unquoted"):
        load_judgments(path)


def spanned(covering: list[int] | None) -> Manifest:
    entry = {"id": "v1-p326", "volume": 1, "page": 326, "print4": {"covering_pages": covering}}
    return Manifest({"pages": [entry]})


def test_a_checked_span_is_recorded_with_who_checked_it() -> None:
    manifest = spanned([286])
    mark_spans_checked(manifest, ["v1-p326"], "Claude Opus 5.5")
    check = manifest.data["pages"][0]["print4"]["visual_check"]
    assert check["by"] == "Claude Opus 5.5" and check["on"]


@pytest.mark.parametrize(("ids", "covering"), [(["v9-p001"], [286]), (["v1-p326"], None)])
def test_an_unknown_page_or_an_unlocated_span_cannot_be_marked_checked(
    ids: list[str], covering: list[int] | None
) -> None:
    manifest = spanned(covering)
    with pytest.raises(OcrError):
        mark_spans_checked(manifest, ids, "Claude Opus 5.5")
    assert "visual_check" not in manifest.data["pages"][0]["print4"]
