from pathlib import Path

from bron.checks import run_checks
from bron.checks.bron_rules import check_bron_rules
from tests.conftest import EDITION, Edit


def checks(repo: Path) -> list[str]:
    return [f.check for f in run_checks(repo, [check_bron_rules])]


def test_valid_fixture_passes(data_repo: Path) -> None:
    assert checks(data_repo) == []


def test_page_break_in_body_without_facs_fails(data_repo: Path, edit: Edit) -> None:
    page_31 = '<pb n="31" xml:id="v1-p31" facs="https://www.dbnl.org/arch/bavi002gere01_01/pag/bavi002gere01_01.pdf#page=41"/>'
    edit(data_repo / EDITION, page_31, '<pb n="31" xml:id="v1-p31"/>')
    assert checks(data_repo) == ["pb-facs"]


def test_availability_without_licence_status_fails(data_repo: Path, edit: Edit) -> None:
    edit(data_repo / EDITION, '<availability status="free">', "<availability>")
    assert checks(data_repo) == ["availability"]


def test_alignment_file_without_availability_fails(data_repo: Path) -> None:
    folder = data_repo / "alignments"
    folder.mkdir()
    (folder / "a.xml").write_text(
        '<TEI xmlns="http://www.tei-c.org/ns/1.0"><teiHeader><fileDesc>'
        "<titleStmt><title>t</title></titleStmt><publicationStmt><p>x</p></publicationStmt>"
        "<sourceDesc><p>x</p></sourceDesc></fileDesc></teiHeader><text><body><p>x</p></body>"
        "</text></TEI>"
    )
    assert checks(data_repo) == ["availability"]


def test_pointer_to_missing_id_fails(data_repo: Path, edit: Edit) -> None:
    edit(data_repo / EDITION, "<head>A. Methode.</head>", '<head corresp="#nowhere">A.</head>')
    assert checks(data_repo) == ["id-ref"]


def test_greek_outside_any_language_span_fails(data_repo: Path, edit: Edit) -> None:
    edit(data_repo / EDITION, '<foreign xml:lang="grc">αὐτοπιστος</foreign>', "αὐτοπιστος")
    [finding] = run_checks(data_repo, [check_bron_rules])
    assert finding.check == "script-lang"
    assert finding.line is not None
    assert "Greek" in finding.message


def test_greek_inside_a_greek_span_passes(data_repo: Path) -> None:
    text = (data_repo / EDITION).read_text(encoding="utf-8")
    assert '<foreign xml:lang="grc">αὐτοπιστος</foreign>' in text
    assert checks(data_repo) == []


def test_hebrew_outside_any_language_span_fails(data_repo: Path, edit: Edit) -> None:
    edit(data_repo / EDITION, "judex controversiarum.", "judex controversiarum. תּוֹרָה")
    assert checks(data_repo) == ["script-lang"]


def test_hebrew_inside_a_hebrew_span_passes(data_repo: Path, edit: Edit) -> None:
    new = 'judex controversiarum. <foreign xml:lang="hbo">תּוֹרָה</foreign>'
    edit(data_repo / EDITION, "judex controversiarum.", new)
    assert checks(data_repo) == []
