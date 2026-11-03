import shutil
from pathlib import Path

import pytest
from lxml import etree

from bron.checks import run_checks
from bron.checks.stability import stability_check
from bron.tei import NSMAP
from bron.tei.text import normalized_text
from tests.conftest import EDITION, FIXTURES, Edit

URN = "urn:cts:bron:fixture.gd.ed1"


@pytest.fixture
def base(tmp_path: Path) -> Path:
    repo = tmp_path / "base"
    shutil.copytree(FIXTURES / "data-repo", repo)
    return repo


@pytest.fixture
def head(tmp_path: Path) -> Path:
    repo = tmp_path / "head"
    shutil.copytree(FIXTURES / "data-repo", repo)
    return repo


def findings(head: Path, base: Path | None, require_base: bool = True) -> list[tuple[str, str]]:
    found = run_checks(head, [stability_check(base, require_base=require_base)])
    return [(f.check, f.message) for f in found]


def checks(head: Path, base: Path) -> list[str]:
    return [check for check, _ in findings(head, base)]


def subparagraph(tree: etree._ElementTree, section: str, number: str) -> etree._Element:
    [element] = tree.xpath(
        f"//tei:div[@type='section'][@n='{section}']/tei:div[@type='subparagraph'][@n='{number}']",
        namespaces=NSMAP,
    )
    return element


def remove_subparagraph(repo: Path, section: str, number: str) -> None:
    path = repo / EDITION
    tree = etree.parse(str(path))
    element = subparagraph(tree, section, number)
    parent = element.getparent()
    assert parent is not None
    parent.remove(element)
    tree.write(str(path), encoding="utf-8", xml_declaration=True)


def swap_subparagraph_texts(repo: Path, first: str, second: str) -> None:
    """Exchange the contents of two subparagraphs of section 3, keeping their labels."""
    path = repo / EDITION
    tree = etree.parse(str(path))
    a, b = subparagraph(tree, "3", first), subparagraph(tree, "3", second)
    a_children, b_children = list(a), list(b)
    for child in a_children:
        a.remove(child)
    for child in b_children:
        b.remove(child)
    a.extend(b_children)
    b.extend(a_children)
    tree.write(str(path), encoding="utf-8", xml_declaration=True)


def write(repo: Path, relative: str, text: str) -> None:
    path = repo / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


RETIRED_3_2 = f"""redirects:
  - urn: {URN}:3.2
    status: retired
    reason: merged into 3.1 by the editor
    date: 2026-11-03
"""


def test_identical_base_and_head_pass(head: Path, base: Path) -> None:
    assert findings(head, base) == []


def test_head_adding_a_subparagraph_passes(head: Path, base: Path, edit: Edit) -> None:
    closing = "</div>\n      </div>\n      </div>"
    added = (
        '</div>\n<div type="subparagraph" n="3"><p>3. Nieuw.</p></div>\n      </div>\n      </div>'
    )
    edit(head / EDITION, closing, added)
    assert findings(head, base) == []


def test_head_removing_a_subparagraph_fails_naming_its_urn(head: Path, base: Path) -> None:
    remove_subparagraph(head, "3", "2")
    [(check, message)] = findings(head, base)
    assert check == "stability-removed"
    assert f"{URN}:3.2" in message


def test_removal_recorded_as_retired_passes(head: Path, base: Path) -> None:
    remove_subparagraph(head, "3", "2")
    write(head, "identifiers/redirects.yaml", RETIRED_3_2)
    assert findings(head, base) == []


def test_removal_recorded_as_redirected_passes(head: Path, base: Path) -> None:
    remove_subparagraph(head, "3", "2")
    write(
        head,
        "identifiers/redirects.yaml",
        f"""redirects:
  - urn: {URN}:3.2
    status: redirected
    replaced_by: [{URN}:3.3]
    reason: renumbered
    date: 2026-11-03
""",
    )
    assert findings(head, base) == []


def test_retired_identifier_still_present_in_head_fails_as_reuse(head: Path, base: Path) -> None:
    write(head, "identifiers/redirects.yaml", RETIRED_3_2)
    assert checks(head, base) == ["stability-reuse"]


def test_deleting_a_retirement_record_and_reintroducing_the_id_fails(
    head: Path, base: Path
) -> None:
    remove_subparagraph(base, "3", "2")
    write(base, "identifiers/redirects.yaml", RETIRED_3_2)
    # head still has 3.2 (the copy is untouched) and no redirects file at all
    assert set(checks(head, base)) == {"stability-redirects"}


def test_altering_a_base_redirect_entry_fails(head: Path, base: Path) -> None:
    for repo in (base, head):
        remove_subparagraph(repo, "3", "2")
    write(base, "identifiers/redirects.yaml", RETIRED_3_2)
    write(head, "identifiers/redirects.yaml", RETIRED_3_2.replace("by the editor", "by accident"))
    assert checks(head, base) == ["stability-redirects"]


def test_redirect_to_an_identifier_that_does_not_exist_fails(head: Path, base: Path) -> None:
    remove_subparagraph(head, "3", "2")
    write(
        head,
        "identifiers/redirects.yaml",
        f"""redirects:
  - urn: {URN}:3.2
    status: redirected
    replaced_by: [{URN}:3.99]
    reason: renumbered
    date: 2026-11-03
""",
    )
    assert checks(head, base) == ["stability-redirects"]


def test_redirects_that_point_at_each_other_fail_as_a_cycle(head: Path, base: Path) -> None:
    for number in ("2", "3"):
        remove_subparagraph(head, "3", number)
    write(
        head,
        "identifiers/redirects.yaml",
        f"""redirects:
  - urn: {URN}:3.2
    status: redirected
    replaced_by: [{URN}:3.3]
    reason: renumbered
    date: 2026-11-03
  - urn: {URN}:3.3
    status: redirected
    replaced_by: [{URN}:3.2]
    reason: renumbered
    date: 2026-11-03
""",
    )
    messages = [message for check, message in findings(head, base)]
    assert any("cycle" in message for message in messages)


def test_swapping_two_subparagraphs_text_fails_naming_both(head: Path, base: Path) -> None:
    swap_subparagraph_texts(head, "2", "3")
    found = findings(head, base)
    assert {check for check, _ in found} == {"stability-text-changed"}
    named = " ".join(message for _, message in found)
    assert f"{URN}:3.2" in named
    assert f"{URN}:3.3" in named


def test_correcting_one_word_passes(head: Path, base: Path, edit: Edit) -> None:
    edit(head / EDITION, "kan toch het principium", "kan toch wel het principium")
    assert findings(head, base) == []


def rewrite_3_2(repo: Path) -> str:
    path = repo / EDITION
    tree = etree.parse(str(path))
    element = subparagraph(tree, "3", "2")
    for child in list(element):
        element.remove(child)
    paragraph = etree.SubElement(element, "{http://www.tei-c.org/ns/1.0}p")
    paragraph.text = "2. Een geheel nieuwe tekst die met de oude niets meer gemeen heeft."
    tree.write(str(path), encoding="utf-8", xml_declaration=True)
    import hashlib

    return hashlib.sha256(normalized_text(element).encode("utf-8")).hexdigest()


def test_declared_rewrite_with_the_matching_hash_passes(head: Path, base: Path) -> None:
    digest = rewrite_3_2(head)
    write(
        head,
        "identifiers/edits.yaml",
        f"""edits:
  - urn: {URN}:3.2
    reason: the printed text was misread in the first ingest
    date: 2026-11-03
    sha256: "{digest}"
""",
    )
    assert findings(head, base) == []


def test_declared_rewrite_with_a_stale_hash_fails(head: Path, base: Path) -> None:
    rewrite_3_2(head)
    write(
        head,
        "identifiers/edits.yaml",
        f"""edits:
  - urn: {URN}:3.2
    reason: the printed text was misread in the first ingest
    date: 2026-11-03
    sha256: "{"0" * 64}"
""",
    )
    assert checks(head, base) == ["stability-text-changed"]


def test_undeclared_rewrite_reports_the_hash_to_declare(head: Path, base: Path) -> None:
    digest = rewrite_3_2(head)
    [(check, message)] = findings(head, base)
    assert check == "stability-text-changed"
    assert digest in message


def test_deleting_a_whole_edition_fails_listing_its_identifiers(head: Path, base: Path) -> None:
    (head / EDITION).unlink()
    [(check, message)] = findings(head, base)
    assert check == "stability-removed"
    assert URN in message
    assert f"{URN}:3.11" in message


def test_first_text_landing_on_an_empty_base_passes(head: Path, base: Path) -> None:
    (base / EDITION).unlink()
    assert findings(head, base) == []


def test_missing_base_with_require_base_fails(head: Path, tmp_path: Path) -> None:
    assert [check for check, _ in findings(head, tmp_path / "nowhere")] == ["stability-base"]
    assert [check for check, _ in findings(head, None)] == ["stability-base"]


def test_no_base_without_require_base_is_skipped(head: Path) -> None:
    assert findings(head, None, require_base=False) == []


def test_malformed_redirects_file_fails(head: Path, base: Path) -> None:
    write(head, "identifiers/redirects.yaml", "redirects:\n  - urn: 3\n")
    assert set(checks(head, base)) == {"stability-redirects"}


def test_unreadable_base_redirects_fail_closed(head: Path, base: Path) -> None:
    remove_subparagraph(base, "3", "2")
    write(base, "identifiers/redirects.yaml", RETIRED_3_2 + "    note: not a schema field\n")
    # head deletes the retirement record and cites 3.2 again
    assert "stability-base" in checks(head, base)


def test_base_text_that_cannot_be_enumerated_fails_closed(
    head: Path, base: Path, edit: Edit
) -> None:
    # the section-level pattern loses its closing parenthesis, so it no longer parses
    edit(base / EDITION, "[@n='$1'])\"", "[@n='$1']\"")
    remove_subparagraph(head, "3", "2")
    assert "stability-base" in checks(head, base)


def test_base_without_a_data_directory_fails_closed(head: Path, tmp_path: Path) -> None:
    empty = tmp_path / "not-a-data-repo"
    empty.mkdir()
    assert [check for check, _ in findings(head, empty)] == ["stability-base"]


def test_malformed_edits_file_fails(head: Path, base: Path) -> None:
    write(head, "identifiers/edits.yaml", "edits:\n  - urn: 3\n")
    assert set(checks(head, base)) == {"stability-edits"}
