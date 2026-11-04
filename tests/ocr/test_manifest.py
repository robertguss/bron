from pathlib import Path

import pytest

from bron.ocr import OcrError
from bron.ocr.manifest import Manifest


def test_recorded_sources_verify_until_one_changes_or_goes_missing(tmp_path: Path) -> None:
    cache = tmp_path / "cache"
    (cache / "delpher" / "a").mkdir(parents=True)
    scan = cache / "delpher" / "a" / "image.jp2"
    scan.write_bytes(b"scan")
    manifest = Manifest()
    assert manifest.record_source(cache, scan) == "delpher/a/image.jp2"
    assert manifest.verify_sources(cache) == []
    scan.write_bytes(b"changed")
    assert manifest.verify_sources(cache) == ["delpher/a/image.jp2: changed since it was recorded"]
    scan.unlink()
    assert manifest.verify_sources(cache) == ["delpher/a/image.jp2: missing from the cache"]


def test_committed_files_verify_without_any_cache(tmp_path: Path) -> None:
    (tmp_path / "gt.txt").write_text("regel")
    manifest = Manifest({"hashes": {"sources": {"delpher/a/image.jp2": "0" * 64}, "committed": {}}})
    manifest.data["hashes"]["committed"]["gt.txt"] = (
        "e9b14bbd8bf35d1f4b2d4f36a5d0cfa27e5c7de9a9b9b6e7d6ef8c8b2ab4f0b5"
    )
    problems = manifest.verify_committed(tmp_path)
    assert problems == ["gt.txt: changed since it was recorded"]


def test_a_manifest_round_trips_and_a_foreign_file_is_refused(tmp_path: Path) -> None:
    path = tmp_path / "manifest.yaml"
    Manifest({"pages": [{"id": "v2-p001"}]}).write(path)
    assert Manifest.load(path).data["pages"] == [{"id": "v2-p001"}]
    path.write_text("protocol: something else\n")
    with pytest.raises(OcrError, match="not a manifest"):
        Manifest.load(path)
