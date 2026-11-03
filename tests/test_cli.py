from pathlib import Path

import pytest

from bron.cli import main
from tests.conftest import EDITION


def test_help_lists_the_four_subcommands(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exit_info:
        main(["--help"])
    assert exit_info.value.code == 0
    out = capsys.readouterr().out
    for command in ("check", "serve", "dts", "convert"):
        assert command in out


def test_unknown_subcommand_exits_non_zero_with_usage(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exit_info:
        main(["frobnicate"])
    assert exit_info.value.code != 0
    assert "usage:" in capsys.readouterr().err


def test_check_passes_the_valid_fixture(
    data_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["check", str(data_repo)]) == 0
    assert capsys.readouterr().out == ""


def test_check_reports_findings_as_file_line_check_message(
    data_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    edition = data_repo / EDITION
    edition.write_text(
        edition.read_text(encoding="utf-8").replace(' xml:lang="nl">', ">"), encoding="utf-8"
    )
    assert main(["check", str(data_repo)]) == 1
    [line] = capsys.readouterr().out.splitlines()
    assert line.startswith("data/fixture/gd/fixture.gd.ed1.xml:")
    assert ": cts-body-lang: " in line
