import shutil
from collections.abc import Callable
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"
EDITION = Path("data/fixture/gd/fixture.gd.ed1.xml")
WORK_CTS = Path("data/fixture/gd/__cts__.xml")
TEXTGROUP_CTS = Path("data/fixture/__cts__.xml")


@pytest.fixture
def data_repo(tmp_path: Path) -> Path:
    """A private copy of the valid fixture repository, safe to break."""
    repo = tmp_path / "data-repo"
    shutil.copytree(FIXTURES / "data-repo", repo)
    return repo


@pytest.fixture
def metadata_only_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "metadata-only"
    shutil.copytree(FIXTURES / "metadata-only", repo)
    return repo


Edit = Callable[[Path, str, str], None]


@pytest.fixture
def edit() -> Edit:
    """Replace exactly one occurrence of `old` with `new` in `path`."""

    def replace(path: Path, old: str, new: str) -> None:
        text = path.read_text(encoding="utf-8")
        assert text.count(old) == 1, f"expected one {old!r} in {path.name}"
        path.write_text(text.replace(old, new), encoding="utf-8")

    return replace
