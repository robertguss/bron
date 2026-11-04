"""Polite, verified downloads into a cache outside the repositories.

Every object fetched gets its own directory in the cache, created empty just before the
download, so nothing fetched can sit beside anything else. Requests to one host are spaced
apart, and a 429 or 503 answer backs off and retries. A file whose checksum disagrees with
the one its source publishes is refused, never kept.
"""

import hashlib
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

from bron.ocr import OcrError

# Fetches a URL: the HTTP status and the body.
Get = Callable[[str], tuple[int, bytes]]

RETRY_STATUSES = frozenset({429, 503})


def http_get(url: str) -> tuple[int, bytes]:
    import httpx2

    try:
        response = httpx2.get(
            url, follow_redirects=True, timeout=900, headers={"User-Agent": "bron-ocr"}
        )
    except httpx2.HTTPError as error:
        raise OcrError(f"{url}: {error}") from error
    return response.status_code, response.content


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def md5(data: bytes) -> str:
    return hashlib.md5(data, usedforsecurity=False).hexdigest()


@dataclass
class Downloader:
    """Fetches into `cache`, at least `spacing[host]` seconds apart per host."""

    cache: Path
    spacing: Mapping[str, float]
    get: Get = http_get
    sleep: Callable[[float], None] = time.sleep
    clock: Callable[[], float] = time.monotonic
    retries: int = 4
    last: dict[str, float] = field(default_factory=dict)

    def fetch(
        self,
        source: str,
        key: str,
        url: str,
        filename: str,
        *,
        md5sum: str | None = None,
        sha256sum: str | None = None,
    ) -> Path:
        """The cached file for `url`, downloaded first unless a verified copy is cached."""
        folder = self.cache / source / key
        path = folder / filename
        if path.is_file() and self._verified(path.read_bytes(), md5sum, sha256sum):
            return path
        if folder.exists() and any(folder.iterdir()):
            raise OcrError(f"{folder} holds something other than a verified {filename}")
        data = self._download(url)
        if not self._verified(data, md5sum, sha256sum):
            raise OcrError(f"{url}: the download's checksum disagrees with its source's")
        folder.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    @staticmethod
    def _verified(data: bytes, md5sum: str | None, sha256sum: str | None) -> bool:
        if md5sum is not None and md5(data) != md5sum.lower():
            return False
        return sha256sum is None or sha256(data) == sha256sum

    def _download(self, url: str) -> bytes:
        host = urlsplit(url).hostname or ""
        wait = self.spacing.get(host, 10.0)
        for attempt in range(self.retries + 1):
            if host in self.last:
                remaining = self.last[host] + wait - self.clock()
                if remaining > 0:
                    self.sleep(remaining)
            status, body = self.get(url)
            self.last[host] = self.clock()
            if status == 200:
                return body
            if status not in RETRY_STATUSES or attempt == self.retries:
                raise OcrError(f"{url}: HTTP {status}")
            self.sleep(wait * 2 ** (attempt + 1))
        raise AssertionError("unreachable")
