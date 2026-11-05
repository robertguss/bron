from pathlib import Path

import pytest
import yaml
from PIL import Image

from bron.ocr import OcrError
from bron.ocr.delpher import alto_lines
from bron.ocr.download import sha256
from bron.ocr.manifest import Manifest
from bron.ocr.packets import prefill, round1

FIXTURES = Path(__file__).parent.parent / "fixtures" / "ocr" / "delpher"


def test_the_prefill_tags_the_running_head_and_keeps_body_then_notes_in_order() -> None:
    lines = alto_lines((FIXTURES / "alto-v2-p2.xml").read_bytes())
    text = prefill("v2-p002", "vol. 2, p. 2", 2, lines).splitlines()
    assert text[0] == "# v2-p002: vol. 2, p. 2"
    assert text[1] == "@head 2 DE ONBEGRIJPELIJKHEID GODS."
    assert text[2].startswith("liet begin van haar arbeid")
    assert len(text) == len(lines) - 1 + 1  # the head row's two ALTO lines become one


def packet_inputs(tmp_path: Path) -> tuple[Manifest, Path, Path]:
    cache = tmp_path / "cache"
    (cache / "delpher" / "s-image").mkdir(parents=True)
    (cache / "delpher" / "s-alto").mkdir(parents=True)
    Image.new("L", (40, 60), 200).save(cache / "delpher" / "s-image" / "image.jp2", "JPEG2000")
    (cache / "delpher" / "s-alto" / "alto.xml").write_bytes(
        (FIXTURES / "alto-v2-p2.xml").read_bytes()
    )
    manifest = Manifest(
        {
            "pages": [
                {
                    "id": "v2-p002",
                    "volume": 2,
                    "page": 2,
                    "print2": {
                        "identifier": "MMUBVU05:000000817:00014",
                        "image": {"file": "delpher/s-image/image.jp2"},
                        "alto": {"file": "delpher/s-alto/alto.xml"},
                    },
                }
            ]
        }
    )
    rules = tmp_path / "README.md"
    rules.write_text("# Rules\n")
    return manifest, cache, rules


def test_the_round1_packet_holds_scan_text_rules_minutes_and_their_hashes(tmp_path: Path) -> None:
    manifest, cache, rules = packet_inputs(tmp_path)
    out = tmp_path / "packet"
    round1(manifest, cache, rules, out)
    listing = yaml.safe_load((out / "packet-manifest.yaml").read_text())
    assert sorted(listing["files"]) == [
        "RULES.md",
        "minutes.txt",
        "pages/v2-p002.gt.txt",
        "pages/v2-p002.png",
    ]
    for name, digest in listing["files"].items():
        assert sha256((out / name).read_bytes()) == digest
    with Image.open(out / "pages" / "v2-p002.png") as png:
        assert png.size == (40, 60)
    assert "v2-p002: " in (out / "minutes.txt").read_text()


def test_a_packet_is_never_written_over_anything(tmp_path: Path) -> None:
    manifest, cache, rules = packet_inputs(tmp_path)
    out = tmp_path / "packet"
    out.mkdir()
    (out / "left-over.txt").write_text("x")
    with pytest.raises(OcrError, match="not empty"):
        round1(manifest, cache, rules, out)


def test_a_packet_asked_for_before_the_fetch_writes_nothing_and_can_be_asked_for_again(
    tmp_path: Path,
) -> None:
    manifest, cache, rules = packet_inputs(tmp_path)
    fetched = manifest.data["pages"][0].pop("print2")
    out = tmp_path / "packet"
    with pytest.raises(OcrError, match="fetch the sampled pages first"):
        round1(manifest, cache, rules, out)
    assert not out.exists()
    manifest.data["pages"][0]["print2"] = fetched
    assert len(round1(manifest, cache, rules, out)) == 5


def test_a_page_whose_scan_is_missing_from_the_cache_writes_nothing(tmp_path: Path) -> None:
    manifest, cache, rules = packet_inputs(tmp_path)
    (cache / "delpher" / "s-image" / "image.jp2").unlink()
    out = tmp_path / "packet"
    with pytest.raises(OcrError, match="image is not in the cache"):
        round1(manifest, cache, rules, out)
    assert not out.exists()


def test_a_scan_that_is_not_jpeg2000_is_refused(tmp_path: Path) -> None:
    manifest, cache, rules = packet_inputs(tmp_path)
    Image.new("L", (40, 60), 200).save(cache / "delpher" / "s-image" / "image.jp2", "PNG")
    with pytest.raises(OcrError, match="not a JPEG 2000 image"):
        round1(manifest, cache, rules, tmp_path / "packet")
