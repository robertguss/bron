"""The sample manifest: everything the test drew, fetched and derived, with its hashes.

It records the seed and how the pages were drawn, every screening judgment, each sampled
page with its sources in both printings, and two hash sets. `sources` holds what was
fetched into the cache (scans, ALTO, PDFs); `bron ocr verify` checks it against the cache.
`committed` holds the files committed to bron-data beside the manifest; scoring checks only
those, so it runs from a fresh clone with no cache and no network.
"""

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

from bron.ocr import OcrError
from bron.ocr.download import sha256

PROTOCOL = "bron M2 OCR sample test, protocol 1"


class Manifest:
    def __init__(self, data: Mapping[str, Any] | None = None) -> None:
        self.data: dict[str, Any] = dict(data or {})
        self.data.setdefault("protocol", PROTOCOL)
        self.data.setdefault("hashes", {"sources": {}, "committed": {}})

    @classmethod
    def load(cls, path: Path) -> Manifest:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or data.get("protocol") != PROTOCOL:
            raise OcrError(f"{path} is not a manifest of {PROTOCOL!r}")
        return cls(data)

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        text = yaml.safe_dump(self.data, sort_keys=False, allow_unicode=True, width=100)
        path.write_text(text, encoding="utf-8")

    def record_source(self, cache: Path, path: Path) -> str:
        """Record a cached file's SHA-256 under its path relative to the cache."""
        relative = path.relative_to(cache).as_posix()
        digest = sha256(path.read_bytes())
        self.data["hashes"]["sources"][relative] = digest
        return relative

    def verify_sources(self, cache: Path) -> list[str]:
        """Every recorded source missing from the cache or changed since it was recorded."""
        problems = []
        for relative, digest in self.data["hashes"]["sources"].items():
            path = cache / relative
            if not path.is_file():
                problems.append(f"{relative}: missing from the cache")
            elif sha256(path.read_bytes()) != digest:
                problems.append(f"{relative}: changed since it was recorded")
        return problems

    def verify_committed(self, root: Path) -> list[str]:
        """Every recorded committed file missing under `root` or changed since recorded."""
        problems = []
        for relative, digest in self.data["hashes"]["committed"].items():
            path = root / relative
            if not path.is_file():
                problems.append(f"{relative}: missing")
            elif sha256(path.read_bytes()) != digest:
                problems.append(f"{relative}: changed since it was recorded")
        return problems
