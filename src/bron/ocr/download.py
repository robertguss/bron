"""Polite, verified downloads into a cache outside the repositories.

Every object fetched gets its own directory in the cache, created empty just before the
download, so nothing fetched can sit beside anything else, and a name that would leave that
directory is refused. A download is written under a partial name and renamed when whole, so
an interrupted run never leaves a truncated file to be taken for a good one. Requests to one
host are spaced apart, and a 429 or 503 answer backs off and retries. A download whose
checksum disagrees with the one its source publishes is refused, never kept; a source that
publishes no checksum is checked for its shape instead. A cached copy that fails its check is
fetched again once, and refused if the new download fails too.
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

# Whether a fetched body is what its source should serve, for a source with no checksum.
Check = Callable[[bytes], bool]

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
        check: Check | None = None,
    ) -> Path:
        """The cached file for `url`, downloaded first unless a verified copy is cached."""
        for name in (source, key, filename):
            if name in ("", ".", "..") or Path(name).name != name:
                raise OcrError(f"{name!r} is not a plain name for a directory or file in the cache")
        folder = self.cache / source / key
        path = folder / filename
        partial = folder / f".{filename}.partial"
        if path.is_file() and self._verified(path.read_bytes(), md5sum, sha256sum, check):
            return path
        if folder.exists():
            # A copy that fails its check, or a write that was cut off, is fetched again
            # once; anything else in the directory is not ours to remove.
            if any(entry not in (path, partial) for entry in folder.iterdir()):
                raise OcrError(f"{folder} holds something other than a verified {filename}")
            path.unlink(missing_ok=True)
            partial.unlink(missing_ok=True)
        data = self._download(url)
        if not self._verified(data, md5sum, sha256sum, None):
            raise OcrError(f"{url}: the download's checksum disagrees with its source's")
        if check is not None and not check(data):
            raise OcrError(f"{url}: the download is not a usable {filename}")
        folder.mkdir(parents=True, exist_ok=True)
        partial.write_bytes(data)
        partial.replace(path)
        return path

    @staticmethod
    def _verified(
        data: bytes, md5sum: str | None, sha256sum: str | None, check: Check | None
    ) -> bool:
        if md5sum is not None and md5(data) != md5sum.lower():
            return False
        if sha256sum is not None and sha256(data) != sha256sum:
            return False
        return check is None or check(data)

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
