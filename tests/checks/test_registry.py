from pathlib import Path

import pytest

from bron.checks import run_checks
from bron.checks.registry import check_registry
from bron.findings import Finding

SOURCES = """\
sources:
  - id: pg-51052
    work: urn:cts:bron:bavinck.gd
    holder: Project Gutenberg
    holder_id: "51052"
    edition: 1ste druk
    printing: Kampen, J.H. Bos, 1895
    rights: http://rightsstatements.org/vocab/NoC-US/1.0/
    url: https://www.gutenberg.org/ebooks/51052
    sha256: 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
    mirrors:
      - url: https://web.archive.org/web/2026/https://www.gutenberg.org/ebooks/51052
        kind: wayback
        status: ok
  - id: dbnl-gd1
    work: urn:cts:bron:bavinck.gd
    holder: DBNL
    holder_id: bavi002gere01
    edition: 1ste druk
    rights: https://creativecommons.org/publicdomain/mark/1.0/
    url: https://www.dbnl.org/tekst/bavi002gere01_01/
"""

TERMS = """\
terms:
  - site: DBNL
    terms_url: https://www.dbnl.org/overdbnl/gebruiksvoorwaarden.php
    checked_on: 2026-11-02
    summary: Public-domain texts may be reused.
    status: confirmed
    confirmed_by: Robert Guss
    confirmed_on: 2026-11-03
  - site: Project Gutenberg
    terms_url: https://www.gutenberg.org/policy/license.html
    checked_on: 2026-11-02
    summary: Strip the Project Gutenberg licence header before reuse.
    status: pending
"""


def write(repo: Path, name: str, text: str) -> Path:
    folder = repo / "registry"
    folder.mkdir(exist_ok=True)
    path = folder / name
    path.write_text(text, encoding="utf-8")
    return path


def findings(repo: Path) -> list[Finding]:
    return run_checks(repo, [check_registry])


def test_no_registry_files_pass(data_repo: Path) -> None:
    assert findings(data_repo) == []


def test_valid_sources_and_terms_pass(data_repo: Path) -> None:
    write(data_repo, "sources.yaml", SOURCES)
    write(data_repo, "terms.yaml", TERMS)
    assert findings(data_repo) == []


def test_unquoted_numeric_holder_id_passes(data_repo: Path) -> None:
    write(data_repo, "sources.yaml", SOURCES.replace('holder_id: "51052"', "holder_id: 51052", 1))
    assert findings(data_repo) == []


def test_public_domain_mark_rights_pass(data_repo: Path) -> None:
    assert "rights: https://creativecommons.org/publicdomain/mark/1.0/" in SOURCES
    write(data_repo, "sources.yaml", SOURCES)
    assert findings(data_repo) == []


def test_rightsstatements_rights_pass(data_repo: Path) -> None:
    assert "rights: http://rightsstatements.org/vocab/NoC-US/1.0/" in SOURCES
    write(data_repo, "sources.yaml", SOURCES)
    assert findings(data_repo) == []


def test_arbitrary_rights_url_fails(data_repo: Path) -> None:
    text = SOURCES.replace(
        "https://creativecommons.org/publicdomain/mark/1.0/", "https://example.org/free"
    )
    path = write(data_repo, "sources.yaml", text)
    [finding] = findings(data_repo)
    assert (finding.path, finding.line, finding.check) == (path, 15, "registry")
    assert "dbnl-gd1" in finding.message
    assert "rights" in finding.message


def test_confirmed_terms_without_confirmed_on_fail(data_repo: Path) -> None:
    write(data_repo, "terms.yaml", TERMS.replace("    confirmed_on: 2026-11-03\n", ""))
    [finding] = findings(data_repo)
    assert finding.check == "registry"
    assert "DBNL" in finding.message
    assert "confirmed_on" in finding.message


def test_pending_terms_with_confirmed_by_fail(data_repo: Path) -> None:
    write(data_repo, "terms.yaml", TERMS + "    confirmed_by: Robert Guss\n")
    [finding] = findings(data_repo)
    assert finding.check == "registry"
    assert finding.line == 9
    assert "Project Gutenberg" in finding.message
    assert "pending" in finding.message


@pytest.mark.parametrize("date", ['"2026-13-40"', "2026-13-40"])
def test_malformed_checked_on_date_fails(data_repo: Path, date: str) -> None:
    write(
        data_repo, "terms.yaml", TERMS.replace("checked_on: 2026-11-02", f"checked_on: {date}", 1)
    )
    [finding] = findings(data_repo)
    assert finding.check == "registry"


def test_duplicate_source_ids_fail(data_repo: Path) -> None:
    write(data_repo, "sources.yaml", SOURCES.replace("id: dbnl-gd1", "id: pg-51052"))
    [finding] = findings(data_repo)
    assert (finding.line, finding.check) == (15, "registry")
    assert "pg-51052" in finding.message


def test_yaml_syntax_error_is_a_finding(data_repo: Path) -> None:
    path = write(data_repo, "sources.yaml", "sources:\n  - id: [unclosed\n")
    [finding] = findings(data_repo)
    assert (finding.path, finding.check) == (path, "registry")
