import pytest

from bron.cli import main


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
