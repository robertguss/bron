import hashlib
from pathlib import Path

import pytest

from bron.ocr import OcrError
from bron.ocr.download import Downloader

URL = "https://resolver.kb.nl/resolve?urn=MMUBVU05:000000817:00013:image"
BODY = b"the scan's bytes"
MD5 = hashlib.md5(BODY).hexdigest()


class Network:
    """A fake network serving a queue of (status, body) answers per URL."""

    def __init__(self, answers: dict[str, list[tuple[int, bytes]]]) -> None:
        self.answers = answers
        self.asked: list[str] = []

    def __call__(self, url: str) -> tuple[int, bytes]:
        self.asked.append(url)
        return self.answers[url].pop(0)


class Clock:
    def __init__(self) -> None:
        self.now = 0.0
        self.slept: list[float] = []

    def time(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.slept.append(seconds)
        self.now += seconds


def downloader(tmp_path: Path, network: Network, clock: Clock) -> Downloader:
    return Downloader(tmp_path, {"resolver.kb.nl": 10.0}, network, clock.sleep, clock.time)


def test_a_download_lands_alone_in_its_own_directory(tmp_path: Path) -> None:
    network = Network({URL: [(200, BODY)]})
    path = downloader(tmp_path, network, Clock()).fetch(
        "delpher", "scan-image", URL, "image.jp2", md5sum=MD5
    )
    assert path == tmp_path / "delpher" / "scan-image" / "image.jp2"
    assert path.read_bytes() == BODY
    assert [p.name for p in path.parent.iterdir()] == ["image.jp2"]


def test_a_verified_cached_copy_is_used_without_a_request(tmp_path: Path) -> None:
    network = Network({URL: [(200, BODY)]})
    fetcher = downloader(tmp_path, network, Clock())
    fetcher.fetch("delpher", "scan-image", URL, "image.jp2", md5sum=MD5)
    fetcher.fetch("delpher", "scan-image", URL, "image.jp2", md5sum=MD5)
    assert network.asked == [URL]


def test_requests_to_one_host_wait_out_the_spacing(tmp_path: Path) -> None:
    other = URL.replace("00013", "00014")
    network = Network({URL: [(200, BODY)], other: [(200, BODY)]})
    clock = Clock()
    fetcher = downloader(tmp_path, network, clock)
    fetcher.fetch("delpher", "a", URL, "image.jp2")
    clock.now += 3
    fetcher.fetch("delpher", "b", other, "image.jp2")
    assert clock.slept == [7.0]


def test_a_429_backs_off_and_retries(tmp_path: Path) -> None:
    network = Network({URL: [(429, b""), (200, BODY)]})
    clock = Clock()
    path = downloader(tmp_path, network, clock).fetch("delpher", "a", URL, "image.jp2")
    assert path.read_bytes() == BODY
    assert clock.slept[0] == 20.0


def test_a_download_whose_checksum_disagrees_is_refused_and_not_kept(tmp_path: Path) -> None:
    network = Network({URL: [(200, b"something else")]})
    with pytest.raises(OcrError, match="checksum"):
        downloader(tmp_path, network, Clock()).fetch("delpher", "a", URL, "image.jp2", md5sum=MD5)
    assert not (tmp_path / "delpher" / "a").exists()


def test_a_directory_holding_anything_else_is_refused(tmp_path: Path) -> None:
    folder = tmp_path / "delpher" / "a"
    folder.mkdir(parents=True)
    (folder / "planted.py").write_text("print('hi')")
    network = Network({URL: [(200, BODY)]})
    with pytest.raises(OcrError, match="holds something other"):
        downloader(tmp_path, network, Clock()).fetch("delpher", "a", URL, "image.jp2")
    assert network.asked == []
