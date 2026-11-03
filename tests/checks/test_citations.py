from pathlib import Path

import pytest
from lxml import etree

from bron.checks import citations, run_checks
from bron.checks.citations import check_citations
from bron.tei.passages import cite_structure_units
from tests.conftest import EDITION, Edit


def findings(repo: Path) -> list[tuple[str, str]]:
    return [(f.check, f.message) for f in run_checks(repo, [check_citations])]


def test_valid_fixture_passes(data_repo: Path) -> None:
    assert findings(data_repo) == []


def test_fixture_enumerates_in_document_order(data_repo: Path) -> None:
    refs = [unit.ref for unit in cite_structure_units(data_repo / EDITION)]
    assert refs == ["3", *[f"3.{n}" for n in range(1, 12)], "4", "4.1", "4.2"]


def test_sibling_subparagraphs_with_the_same_number_fail(data_repo: Path, edit: Edit) -> None:
    edit(
        data_repo / EDITION, '<div type="subparagraph" n="11">', '<div type="subparagraph" n="10">'
    )
    checks = {check for check, _ in findings(data_repo)}
    assert "passage-duplicate" in checks


def test_empty_cited_subparagraph_fails(data_repo: Path) -> None:
    path = data_repo / EDITION
    tree = etree.parse(str(path))
    [subparagraph] = tree.xpath(
        "//tei:div[@n='3']/tei:div[@n='4']", namespaces={"tei": "http://www.tei-c.org/ns/1.0"}
    )
    for child in list(subparagraph):
        subparagraph.remove(child)
    subparagraph.text = None
    tree.write(str(path), encoding="utf-8", xml_declaration=True)
    assert ("passage-empty", "passage 3.4 has no text") in findings(data_repo)


def test_cref_pattern_matching_one_passage_fewer_fails_and_names_it(
    data_repo: Path, edit: Edit
) -> None:
    edit(
        data_repo / EDITION,
        "tei:div[@type='subparagraph'][@n='$2'])",
        "tei:div[@type='subparagraph'][@n='$2'][not(@n='11')])",
    )
    [(check, message)] = findings(data_repo)
    assert check == "citation-parity"
    assert "3.11" in message


def test_declarations_selecting_different_text_for_the_same_labels_fail(
    data_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Same label set, but citeStructure resolves 3.2 to other words (here, section 4's).
    real_extract = citations.extract_passage

    def extract(path: Path, ref: str) -> etree._Element:
        return real_extract(path, "4" if ref == "3.2" else ref)

    monkeypatch.setattr(citations, "extract_passage", extract)
    assert findings(data_repo) == [
        ("citation-parity", "passage 3.2 has different text under cRefPattern and citeStructure")
    ]


def test_label_with_a_forbidden_character_fails(data_repo: Path, edit: Edit) -> None:
    edit(
        data_repo / EDITION, '<div type="subparagraph" n="11">', '<div type="subparagraph" n="1 1">'
    )
    assert "passage-label" in {check for check, _ in findings(data_repo)}


def test_cite_structure_cannot_read_files_from_the_runner(
    data_repo: Path, tmp_path: Path, edit: Edit
) -> None:
    secret = tmp_path / "secret.txt"
    secret.write_text("TOPSECRET-CANARY", encoding="utf-8")
    edit(
        data_repo / EDITION,
        'use="@n" delim="."/>',
        f'use="concat(@n, unparsed-text(\'{secret.as_uri()}\'))" delim="."/>',
    )
    found = findings(data_repo)
    assert found
    assert all("TOPSECRET-CANARY" not in message for _, message in found)


def test_text_with_a_doctype_is_refused(data_repo: Path, edit: Edit) -> None:
    edit(
        data_repo / EDITION,
        '<?xml version="1.0" encoding="UTF-8"?>\n',
        '<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE TEI [<!ENTITY x "y">]>\n',
    )
    [(check, message)] = findings(data_repo)
    assert check == "citation-cite-structure"
    assert "DOCTYPE" in message
