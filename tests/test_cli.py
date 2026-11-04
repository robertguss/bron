import shutil
from pathlib import Path

import pytest

from bron.cli import main
from tests.conftest import EDITION


def test_help_lists_the_subcommands(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exit_info:
        main(["--help"])
    assert exit_info.value.code == 0
    out = capsys.readouterr().out
    for command in ("check", "serve", "dts", "convert", "ocr"):
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


def test_check_without_a_base_says_stability_was_skipped(
    data_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["check", str(data_repo)]) == 0
    assert "identifier stability was skipped" in capsys.readouterr().err


def test_check_with_require_base_and_no_base_fails(
    data_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["check", str(data_repo), "--require-base"]) == 1
    assert ": stability-base: " in capsys.readouterr().out


def test_check_against_an_identical_base_passes(data_repo: Path, tmp_path: Path) -> None:
    base = tmp_path / "base"
    shutil.copytree(data_repo, base)
    assert main(["check", str(data_repo), "--base", str(base), "--require-base"]) == 0


def test_check_against_a_base_reports_a_removed_citation(
    data_repo: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    base = tmp_path / "base"
    shutil.copytree(data_repo, base)
    edition = data_repo / EDITION
    text = edition.read_text(encoding="utf-8")
    start = text.index('<div type="subparagraph" n="2">')
    end = text.index("</div>", start) + len("</div>")
    edition.write_text(text[:start] + text[end:], encoding="utf-8")
    assert main(["check", str(data_repo), "--base", str(base), "--require-base"]) == 1
    assert ": stability-removed: " in capsys.readouterr().out


def test_serve_refuses_a_repository_it_cannot_index(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["serve", str(tmp_path)]) == 1
    assert "has no data/ directory" in capsys.readouterr().err


def test_check_summary_lists_the_records_new_since_the_base(
    data_repo: Path, tmp_path: Path
) -> None:
    base = tmp_path / "base"
    shutil.copytree(data_repo, base)
    identifiers = data_repo / "identifiers"
    identifiers.mkdir()
    urn = "urn:cts:bron:fixture.gd.ed1:3.12"
    (identifiers / "redirects.yaml").write_text(
        f'redirects:\n  - urn: "{urn}"\n    status: retired\n'
        "    reason: Never printed.\n    date: 2026-11-03\n",
        encoding="utf-8",
    )
    summary = tmp_path / "summary.md"
    main(["check", str(data_repo), "--base", str(base), "--summary", str(summary)])
    text = summary.read_text(encoding="utf-8")
    assert "identifiers/redirects.yaml" in text
    assert urn in text and "retired" in text and "Never printed." in text
    assert "identifiers/edits.yaml: none" in text


def test_check_summary_without_new_records(data_repo: Path, tmp_path: Path) -> None:
    base = tmp_path / "base"
    shutil.copytree(data_repo, base)
    summary = tmp_path / "summary.md"
    assert main(["check", str(data_repo), "--base", str(base), "--summary", str(summary)]) == 0
    assert "identifiers/redirects.yaml: none" in summary.read_text(encoding="utf-8")


def test_check_summary_shows_record_text_literally(data_repo: Path, tmp_path: Path) -> None:
    base = tmp_path / "base"
    shutil.copytree(data_repo, base)
    identifiers = data_repo / "identifiers"
    identifiers.mkdir()
    (identifiers / "redirects.yaml").write_text(
        'redirects:\n  - urn: "urn:cts:bron:fixture.gd.ed1:3.12"\n    status: retired\n'
        '    reason: "Hidden <!-- start\\n## Fake heading [link](https://x) `code`"\n'
        "    date: 2026-11-03\n",
        encoding="utf-8",
    )
    summary = tmp_path / "summary.md"
    main(["check", str(data_repo), "--base", str(base), "--summary", str(summary)])
    text = summary.read_text(encoding="utf-8")
    assert "<!--" not in text
    assert not any(line.startswith("## Fake") for line in text.splitlines())
    assert "](" not in text
    assert "Fake heading" in text
