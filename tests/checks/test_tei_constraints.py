from pathlib import Path

from bron.checks import run_checks
from bron.checks.tei_constraints import check_tei_constraints
from tests.conftest import EDITION, Edit

LINK_FILE = """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader><fileDesc><titleStmt><title>t</title></titleStmt>
    <publicationStmt><p>x</p></publicationStmt><sourceDesc><p>x</p></sourceDesc></fileDesc>
  </teiHeader>
  <text><body><linkGrp type="edition">{links}</linkGrp></body></text>
</TEI>
"""


def alignment(repo: Path, links: str) -> list[str]:
    folder = repo / "alignments"
    folder.mkdir(exist_ok=True)
    (folder / "a.xml").write_text(LINK_FILE.format(links=links), encoding="utf-8")
    return [f.check for f in run_checks(repo, [check_tei_constraints])]


def test_valid_fixture_passes(data_repo: Path) -> None:
    assert run_checks(data_repo, [check_tei_constraints]) == []


def test_equal_link_with_one_target_fails(data_repo: Path) -> None:
    assert alignment(data_repo, '<link type="equal" target="a.xml#x"/>') == ["tei-link-targets"]


def test_insert_link_with_one_target_passes(data_repo: Path) -> None:
    assert alignment(data_repo, '<link type="insert" target="a.xml#x"/>') == []


def test_insert_link_with_two_targets_fails(data_repo: Path) -> None:
    links = '<link type="insert" target="a.xml#x b.xml#y"/>'
    assert alignment(data_repo, links) == ["tei-link-targets"]


def test_top_level_cite_structure_with_relative_match_fails(data_repo: Path, edit: Edit) -> None:
    edit(data_repo / EDITION, "match=\"/TEI/text/body//div[@type='section']\"", 'match="div"')
    [finding] = run_checks(data_repo, [check_tei_constraints])
    assert finding.check == "tei-citestructure-match"


def test_nested_cite_structure_with_absolute_match_fails(data_repo: Path, edit: Edit) -> None:
    edit(data_repo / EDITION, "match=\"div[@type='subparagraph']\"", 'match="/TEI"')
    [finding] = run_checks(data_repo, [check_tei_constraints])
    assert finding.check == "tei-citestructure-match"


def test_subtype_without_type_fails(data_repo: Path, edit: Edit) -> None:
    edit(data_repo / EDITION, '<div type="chapter" n="1">', '<div subtype="x" n="1">')
    [finding] = run_checks(data_repo, [check_tei_constraints])
    assert finding.check == "tei-subtype"
