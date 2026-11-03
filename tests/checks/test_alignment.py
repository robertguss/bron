from pathlib import Path

from bron.checks import Context, run_checks
from bron.checks.alignment import alignment_report, check_alignment
from bron.findings import Finding

ALIGNMENT = Path("alignments/fixture.gd.ed1--ed2.structure.xml")


def write_alignment(repo: Path, targets: list[str], base: str | None) -> Path:
    links = "\n".join(f'      <link type="equal" target="{t}"/>' for t in targets)
    base_attribute = f' xml:base="{base}"' if base else ""
    path = repo / ALIGNMENT
    path.parent.mkdir(exist_ok=True)
    path.write_text(
        f"""<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader>
    <fileDesc>
      <titleStmt><title>Structural concordance (test fixture)</title></titleStmt>
      <publicationStmt>
        <availability status="free">
          <licence target="https://creativecommons.org/publicdomain/zero/1.0/">CC0</licence>
        </availability>
      </publicationStmt>
      <sourceDesc><p>Test fixture.</p></sourceDesc>
    </fileDesc>
  </teiHeader>
  <text><body>
    <linkGrp type="edition"{base_attribute}>
{links}
    </linkGrp>
  </body></text>
</TEI>
""",
        encoding="utf-8",
    )
    return path


def write_deferred(repo: Path, text: str) -> Path:
    path = repo / "alignments" / "deferred.yaml"
    path.parent.mkdir(exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def findings(repo: Path) -> list[Finding]:
    return run_checks(repo, [check_alignment])


def test_target_under_xml_base_that_exists_passes(data_repo: Path) -> None:
    write_alignment(
        data_repo, ["fixture.gd.ed1.xml#sec-3 fixture.gd.ed1.xml#sec-4"], "../data/fixture/gd/"
    )
    assert findings(data_repo) == []


def test_same_target_without_xml_base_fails(data_repo: Path) -> None:
    path = write_alignment(data_repo, ["fixture.gd.ed1.xml#sec-3"], None)
    [finding] = findings(data_repo)
    assert (finding.path, finding.line, finding.check) == (path, 16, "alignment-target")
    assert "alignments/fixture.gd.ed1.xml" in finding.message


def test_fragment_with_no_such_id_fails_naming_the_link(data_repo: Path) -> None:
    path = write_alignment(
        data_repo, ["fixture.gd.ed1.xml#sec-3 fixture.gd.ed1.xml#sec-99"], "../data/fixture/gd/"
    )
    [finding] = findings(data_repo)
    assert (finding.path, finding.line, finding.check) == (path, 16, "alignment-target")
    assert "line 16" in finding.message
    assert "fixture.gd.ed1.xml#sec-99" in finding.message
    assert "data/fixture/gd/fixture.gd.ed1.xml" in finding.message


def test_targets_into_a_deferred_missing_file_are_skipped_and_counted(data_repo: Path) -> None:
    write_alignment(
        data_repo,
        ["fixture.gd.ed1.xml#sec-3 fixture.gd.ed2.xml#par-3", "fixture.gd.ed2.xml#par-4"],
        "../data/fixture/gd/",
    )
    write_deferred(
        data_repo,
        "deferred:\n  - path: data/fixture/gd/fixture.gd.ed2.xml\n    milestone: second edition\n",
    )
    assert alignment_report(Context(root=data_repo)) == ([], 2)


def test_targets_into_a_missing_file_not_deferred_fail(data_repo: Path) -> None:
    write_alignment(
        data_repo, ["fixture.gd.ed1.xml#sec-3 fixture.gd.ed2.xml#par-3"], "../data/fixture/gd/"
    )
    [finding] = findings(data_repo)
    assert finding.check == "alignment-target"
    assert "data/fixture/gd/fixture.gd.ed2.xml" in finding.message


def test_malformed_deferred_list_fails(data_repo: Path) -> None:
    write_alignment(
        data_repo, ["fixture.gd.ed1.xml#sec-3 fixture.gd.ed1.xml#sec-4"], "../data/fixture/gd/"
    )
    path = write_deferred(data_repo, "deferred:\n  - path: data/fixture/gd/fixture.gd.ed2.xml\n")
    [finding] = findings(data_repo)
    assert (finding.path, finding.check) == (path, "alignment-deferred")
