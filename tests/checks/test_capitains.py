from pathlib import Path

from bron.checks import run_checks
from bron.checks.capitains import check_capitains
from tests.conftest import EDITION, TEXTGROUP_CTS, WORK_CTS, Edit


def checks(repo: Path) -> list[str]:
    return [f.check for f in run_checks(repo, [check_capitains])]


def test_valid_fixture_passes(data_repo: Path) -> None:
    assert checks(data_repo) == []


def test_metadata_without_editions_passes(metadata_only_repo: Path) -> None:
    assert checks(metadata_only_repo) == []


def test_missing_language_on_body_fails(data_repo: Path, edit: Edit) -> None:
    edit(data_repo / EDITION, ' xml:lang="nl">', ">")
    assert checks(data_repo) == ["cts-body-lang"]


def test_body_urn_that_disagrees_with_its_filename_fails(data_repo: Path, edit: Edit) -> None:
    edit(data_repo / EDITION, 'n="urn:cts:bron:fixture.gd.ed1"', 'n="urn:cts:bron:fixture.gd.ed9"')
    assert checks(data_repo) == ["cts-body-urn"]


def test_edition_file_not_listed_in_work_metadata_fails(data_repo: Path) -> None:
    extra = data_repo / "data/fixture/gd/fixture.gd.ed2.xml"
    extra.write_text((data_repo / EDITION).read_text(encoding="utf-8"), encoding="utf-8")
    assert checks(data_repo) == ["cts-unlisted-file"]


def test_listed_edition_without_its_file_fails(data_repo: Path) -> None:
    (data_repo / EDITION).unlink()
    assert checks(data_repo) == ["cts-missing-file"]


def test_work_group_urn_that_does_not_match_its_textgroup_fails(
    data_repo: Path, edit: Edit
) -> None:
    edit(data_repo / WORK_CTS, 'groupUrn="urn:cts:bron:fixture"', 'groupUrn="urn:cts:bron:other"')
    assert checks(data_repo) == ["cts-work"]


def test_textgroup_urn_that_does_not_match_its_directory_fails(data_repo: Path, edit: Edit) -> None:
    edit(data_repo / TEXTGROUP_CTS, 'urn="urn:cts:bron:fixture"', 'urn="urn:cts:bron:fixtur"')
    assert "cts-textgroup" in checks(data_repo)


def test_textgroup_directory_without_metadata_fails(data_repo: Path) -> None:
    (data_repo / TEXTGROUP_CTS).unlink()
    assert checks(data_repo) == ["cts-textgroup"]


def test_text_without_cts_citation_declaration_fails(data_repo: Path, edit: Edit) -> None:
    edit(data_repo / EDITION, '<refsDecl n="CTS">', '<refsDecl n="other">')
    assert checks(data_repo) == ["cts-citation"]


def test_version_urn_without_a_namespace_is_a_finding_not_a_crash(
    data_repo: Path, edit: Edit
) -> None:
    for path in (data_repo / TEXTGROUP_CTS, data_repo / WORK_CTS):
        path.write_text(
            path.read_text(encoding="utf-8").replace("urn:cts:bron:", "urn:cts:"), encoding="utf-8"
        )
    assert "cts-edition" in checks(data_repo)
