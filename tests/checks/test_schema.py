from pathlib import Path

from bron.checks import run_checks
from bron.checks.schema import check_schema
from tests.conftest import EDITION, Edit


def findings(repo: Path) -> list[tuple[str, str]]:
    return [(f.check, f.message) for f in run_checks(repo, [check_schema])]


def test_valid_fixture_passes(data_repo: Path) -> None:
    assert findings(data_repo) == []


def test_element_not_in_tei_all_fails_with_file_and_line(data_repo: Path, edit: Edit) -> None:
    edit(data_repo / EDITION, "<head>Inleiding.</head>", "<head>Inleiding.</head><bogus/>")
    found = run_checks(data_repo, [check_schema])
    assert {f.check for f in found} == {"schema"}
    assert all(f.path == (data_repo / EDITION).resolve() and f.line for f in found)
    assert any("bogus" in f.message for f in found)


def test_duplicate_xml_id_is_a_parse_error(data_repo: Path, edit: Edit) -> None:
    edit(data_repo / EDITION, 'xml:id="sec-4"', 'xml:id="sec-3"')
    [(check, message)] = findings(data_repo)
    assert check == "parse"
    assert "sec-3" in message


def test_alignment_files_are_validated(data_repo: Path) -> None:
    alignments = data_repo / "alignments"
    alignments.mkdir()
    (alignments / "broken.xml").write_text('<TEI xmlns="http://www.tei-c.org/ns/1.0"/>')
    assert [check for check, _ in findings(data_repo)] == ["schema"]
