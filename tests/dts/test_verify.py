import json
from pathlib import Path

import pytest

from bron.cli import main
from bron.dts import app as resolver
from bron.dts import responses
from bron.dts.responses import Problem
from bron.dts.verify import verify
from tests.conftest import Edit
from tests.dts.conftest import RESOURCE
from tests.dts.test_redirects import without_3_2

RIGHT = (f"{RESOURCE}:3.2", "2. Maar de kerk met hare")


def test_the_fixture_repository_verifies(data_repo: Path) -> None:
    report = verify(data_repo)
    assert report.failures == []
    assert report.documents == 15  # every citable unit, each fetched as a Document
    assert report.navigations > 15


def test_a_repository_without_texts_verifies(metadata_only_repo: Path) -> None:
    assert verify(metadata_only_repo).failures == []


def test_a_passage_whose_document_fails_is_named(
    data_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    real = responses.tei_fragment

    def broken(units):
        if units[0].ref == "3.5":
            raise RuntimeError("extraction failed")
        return real(units)

    monkeypatch.setattr(responses, "tei_fragment", broken)
    failures = verify(data_repo).failures
    assert failures
    assert all("3.5" in failure for failure in failures)
    assert any("ref=3.5" in failure and "500" in failure for failure in failures)


def test_a_member_whose_parent_does_not_exist_fails(
    data_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    real = responses.citable_unit

    def orphaned(unit):
        found = real(unit)
        if unit.ref == "4.2":
            found["parent"] = "5"
        return found

    monkeypatch.setattr(responses, "citable_unit", orphaned)
    failures = verify(data_repo).failures
    assert any("4.2" in failure and "parent 5" in failure for failure in failures)


def test_expected_text_prefix(data_repo: Path) -> None:
    assert verify(data_repo, expectations=[RIGHT]).failures == []
    [failure] = verify(data_repo, expectations=[(f"{RESOURCE}:3.2", "3. Maar ook")]).failures
    assert "'3. Maar ook'" in failure
    assert "'2. Maar de kerk" in failure


def test_an_expected_urn_that_does_not_resolve_fails(data_repo: Path) -> None:
    [failure] = verify(data_repo, expectations=[(f"{RESOURCE}:9.9", "Iets")]).failures
    assert "9.9" in failure and "404" in failure


@pytest.mark.parametrize(
    ("record", "status"),
    [
        (f'status: redirected\n    replaced_by: ["{RESOURCE}:3.3"]', 301),
        (f'status: redirected\n    replaced_by: ["{RESOURCE}:3.3", "{RESOURCE}:3.4"]', 300),
        ("status: retired", 410),
    ],
)
def test_withdrawn_identifiers_answer_as_recorded(
    data_repo: Path, edit: Edit, record: str, status: int
) -> None:
    repo = without_3_2(
        data_repo,
        edit,
        f"""redirects:
  - urn: "{RESOURCE}:3.2"
    {record}
    reason: Test.
    date: 2026-11-03
""",
    )
    report = verify(repo)
    assert report.failures == []
    assert report.withdrawn == 1


def test_a_redirected_identifier_answering_404_fails(
    data_repo: Path, edit: Edit, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = without_3_2(
        data_repo,
        edit,
        f"""redirects:
  - urn: "{RESOURCE}:3.2"
    status: redirected
    replaced_by: ["{RESOURCE}:3.3"]
    reason: Test.
    date: 2026-11-03
""",
    )
    monkeypatch.setattr(resolver, "_gone", lambda *args: Problem(404, "Not Found", "gone"))
    failures = verify(repo).failures
    assert len(failures) == 2  # Navigation and Document
    assert all("3.2" in f and "404" in f and "301" in f for f in failures)


def write_schemas(folder: Path, entry_requires: list[str]) -> Path:
    folder.mkdir()
    anything = {"$schema": "https://json-schema.org/draft/2020-12/schema", "type": "object"}
    entry = {**anything, "required": entry_requires}
    for name, schema in (
        ("entry_response.schema.json", entry),
        ("collection_response.schema.json", anything),
        ("navigation_response.schema.json", anything),
    ):
        (folder / name).write_text(json.dumps(schema), encoding="utf-8")
    return folder


def test_responses_are_validated_against_the_given_schemas(data_repo: Path, tmp_path: Path) -> None:
    passing = write_schemas(tmp_path / "passing", ["dtsVersion"])
    assert verify(data_repo, schemas=passing).failures == []
    failing = write_schemas(tmp_path / "failing", ["dtsVersion", "nonexistent"])
    [failure] = verify(data_repo, schemas=failing).failures
    assert "nonexistent" in failure


def test_cli_prints_failures_and_exits_1(
    data_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["dts", "verify", str(data_repo), "--expect", "=".join(RIGHT)]) == 0
    assert main(["dts", "verify", str(data_repo), "--expect", f"{RESOURCE}:3.2=Niets"]) == 1
    out = capsys.readouterr().out
    assert ": dts-expect: " in out


def test_cli_rejects_a_malformed_expectation(
    data_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["dts", "verify", str(data_repo), "--expect", "no-equals-sign"]) == 2
    assert "URN=TEXT" in capsys.readouterr().err


def test_a_unit_navigation_leaves_out_is_reported_and_still_fetched(
    data_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    real = responses.navigation

    def dropping(index, resource, base, request_id, anchors, members):
        if members is not None:
            members = [unit for unit in members if unit.ref != "4.2"]
        return real(index, resource, base, request_id, anchors, members)

    monkeypatch.setattr(responses, "navigation", dropping)
    report = verify(data_repo)
    assert any("dts-member" in f and "omits 4.2" in f for f in report.failures)
    assert report.documents == 15


def test_a_fragment_with_the_wrong_text_fails(
    data_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    real = responses.tei_fragment

    def altered(units):
        body = real(units)
        if [unit.ref for unit in units] == ["3.2"]:
            return body.replace(b"Maar de kerk", b"Maar het volk")
        return body

    monkeypatch.setattr(responses, "tei_fragment", altered)
    [failure] = verify(data_repo).failures
    assert "ref=3.2" in failure and "dts-text" in failure


def test_members_out_of_document_order_fail(
    data_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    real = responses.navigation

    def reversed_members(index, resource, base, request_id, anchors, members):
        return real(index, resource, base, request_id, anchors, members and members[::-1])

    monkeypatch.setattr(responses, "navigation", reversed_members)
    failures = verify(data_repo).failures
    assert any("dts-order" in f for f in failures)
