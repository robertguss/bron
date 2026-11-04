"""The four Gutenberg volumes, fetched into a local cache and checked against the registry.

Gutenberg revises its files in place, so the registry records the SHA-256 of each volume as
converted, and two durable copies of it: a release asset on bron-data and a Wayback Machine
raw capture. A volume comes from the cache when its hash matches. Otherwise the live file,
the release asset and the Wayback copy are tried in that order, and the first whose hash
matches is cached. The Wayback capture keeps the bytes as Gutenberg sent them,
gzip-compressed, so a compressed copy is checked once decompressed. A volume no copy of
which matches stops the conversion before anything is parsed.
"""

import gzip
import hashlib
import zlib
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

# Fetches a URL; None when it cannot be fetched.
Download = Callable[[str], bytes | None]

MIRROR_ORDER = ("release-asset", "wayback")


class FetchError(Exception):
    pass


def http_get(url: str) -> bytes | None:
    import httpx2

    try:
        response = httpx2.get(url, follow_redirects=True, timeout=60)
    except httpx2.HTTPError:
        return None
    return response.content if response.status_code == 200 else None


def fetch(record: Mapping[str, Any], cache: Path, download: Download = http_get) -> Path:
    """The cached file of a registry record, fetched first if the cache lacks a matching copy."""
    path = cache / Path(record["url"]).name
    expected = record["sha256"]
    if path.is_file() and content_sha256(path.read_bytes()) == expected:
        return path
    mirrors = sorted(record.get("mirrors") or [], key=lambda m: MIRROR_ORDER.index(m["kind"]))
    urls = [record["url"], *(mirror["url"] for mirror in mirrors)]
    for url in urls:
        data = download(url)
        if data is not None and (verified := _verified(data, expected)) is not None:
            cache.mkdir(parents=True, exist_ok=True)
            path.write_bytes(verified)
            return path
    raise FetchError(
        f"{record['id']}: no copy has the registered SHA-256 {expected}; tried {', '.join(urls)}"
    )


def _verified(data: bytes, expected: str) -> bytes | None:
    if content_sha256(data) == expected:
        return data
    if data[:2] == b"\x1f\x8b":
        try:
            unpacked = gzip.decompress(data)
        except OSError, EOFError, zlib.error:
            return None
        if content_sha256(unpacked) == expected:
            return unpacked
    return None


def content_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
