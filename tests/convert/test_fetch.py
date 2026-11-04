import gzip
import hashlib
from pathlib import Path

import pytest
import yaml

from bron.convert.gd1.emit import convert
from bron.convert.gd1.fetch import FetchError, fetch

LIVE = "https://www.gutenberg.org/cache/epub/51052/pg51052-images.html"
RELEASE = (
    "https://github.com/robertguss/bron-data/releases/download/sources-gd1/pg51052-images.html"
)
WAYBACK = "https://web.archive.org/web/20261104104729id_/" + LIVE

GOOD = b"<html><body>the registered volume</body></html>"


def record(content: bytes = GOOD) -> dict:
    return {
        "id": "gd1-vol1-gutenberg",
        "url": LIVE,
        "sha256": hashlib.sha256(content).hexdigest(),
        "mirrors": [
            {"url": RELEASE, "kind": "release-asset", "status": "ok"},
            {"url": WAYBACK, "kind": "wayback", "status": "ok"},
        ],
    }


class Downloads:
    """A fake network: each URL serves the given bytes, or nothing."""

    def __init__(self, served: dict[str, bytes]) -> None:
        self.served = served
        self.asked: list[str] = []

    def __call__(self, url: str) -> bytes | None:
        self.asked.append(url)
        return self.served.get(url)


def test_a_revised_live_file_is_replaced_by_the_release_asset(tmp_path: Path) -> None:
    downloads = Downloads({LIVE: b"revised in place", RELEASE: GOOD, WAYBACK: GOOD})
    path = fetch(record(), tmp_path, downloads)
    assert path == tmp_path / "pg51052-images.html"
    assert path.read_bytes() == GOOD
    assert downloads.asked == [LIVE, RELEASE]


def test_the_wayback_copy_serves_when_only_it_matches(tmp_path: Path) -> None:
    downloads = Downloads({LIVE: b"revised in place", RELEASE: b"missing asset", WAYBACK: GOOD})
    assert fetch(record(), tmp_path, downloads).read_bytes() == GOOD
    assert downloads.asked == [LIVE, RELEASE, WAYBACK]


def test_a_wayback_copy_stored_gzip_compressed_matches_once_decompressed(tmp_path: Path) -> None:
    downloads = Downloads({WAYBACK: gzip.compress(GOOD, mtime=0)})
    assert fetch(record(), tmp_path, downloads).read_bytes() == GOOD


def test_a_damaged_compressed_mirror_is_skipped_for_the_next_one(tmp_path: Path) -> None:
    # A valid gzip header followed by a deflate block of an invalid type.
    damaged = b"\x1f\x8b\x08\x00\x00\x00\x00\x00\x00\xff" + b"\xff" * 8
    downloads = Downloads({RELEASE: damaged, WAYBACK: GOOD})
    assert fetch(record(), tmp_path, downloads).read_bytes() == GOOD
    assert downloads.asked == [LIVE, RELEASE, WAYBACK]


def test_a_cached_copy_with_the_registered_hash_is_used_without_downloading(
    tmp_path: Path,
) -> None:
    (tmp_path / "pg51052-images.html").write_bytes(GOOD)
    downloads = Downloads({})
    assert fetch(record(), tmp_path, downloads).read_bytes() == GOOD
    assert downloads.asked == []


def test_a_volume_no_copy_of_which_matches_fails_before_any_parsing(tmp_path: Path) -> None:
    records = []
    for volume, ebook in enumerate((51052, 67966, 68527, 69005), start=1):
        records.append(
            {
                "id": f"gd1-vol{volume}-gutenberg",
                "url": f"https://www.gutenberg.org/cache/epub/{ebook}/pg{ebook}-images.html",
                "sha256": "0" * 64,
                "mirrors": [],
            }
        )
    registry = tmp_path / "sources.yaml"
    registry.write_text(yaml.safe_dump({"sources": records}), encoding="utf-8")
    cache = tmp_path / "cache"
    downloads = Downloads(
        {str(r["url"]): b"<html><body><p>not it</p></body></html>" for r in records}
    )
    with pytest.raises(FetchError) as error:
        convert(registry, cache, "0" * 40, downloads)
    assert "gd1-vol1-gutenberg" in str(error.value)
    assert not (cache / "pg51052-images.html").exists()
