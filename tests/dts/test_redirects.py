from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from tests.conftest import EDITION, Edit
from tests.dts.conftest import BASE, RESOURCE, Client

SUBPARAGRAPH_2 = (
    '<div type="subparagraph" n="2">\n'
    '          <pb n="15" xml:id="v1-p15" facs="https://www.dbnl.org/arch/bavi002gere01_01/pag/'
    'bavi002gere01_01.pdf#page=25"/>\n'
    "          <p>2. Maar de kerk"
)


def without_3_2(repo: Path, edit: Edit, redirects: str) -> Path:
    """The fixture with subparagraph 3.2 relabelled 3.2a, and the given redirect records."""
    edit(repo / EDITION, SUBPARAGRAPH_2, SUBPARAGRAPH_2.replace('n="2"', 'n="2a"', 1))
    (repo / "identifiers").mkdir()
    (repo / "identifiers" / "redirects.yaml").write_text(redirects, encoding="utf-8")
    return repo


@pytest.fixture
def redirected(serve: Client, data_repo: Path, edit: Edit) -> TestClient:
    return serve(
        without_3_2(
            data_repo,
            edit,
            f"""redirects:
  - urn: "{RESOURCE}:3.2"
    status: redirected
    replaced_by: ["{RESOURCE}:3.3"]
    reason: Merged into the next subparagraph.
    date: 2026-11-03
""",
        )
    )


@pytest.mark.parametrize("endpoint", ["navigation", "document"])
def test_redirected_ref_answers_301_to_the_replacement(
    redirected: TestClient, endpoint: str
) -> None:
    response = redirected.get(f"/api/dts/{endpoint}", params={"resource": RESOURCE, "ref": "3.2"})
    assert response.status_code == 301
    assert response.headers["location"] == f"{BASE}/{endpoint}?resource={RESOURCE}&ref=3.3"


def test_redirect_keeps_the_other_parameters(redirected: TestClient) -> None:
    response = redirected.get(
        "/api/dts/navigation",
        params={"resource": RESOURCE, "start": "3.2", "end": "3.4", "down": 1},
    )
    assert response.status_code == 301
    assert response.headers["location"] == (
        f"{BASE}/navigation?resource={RESOURCE}&start=3.3&end=3.4&down=1"
    )


def test_split_answers_300_listing_every_replacement(
    serve: Client, data_repo: Path, edit: Edit
) -> None:
    client = serve(
        without_3_2(
            data_repo,
            edit,
            f"""redirects:
  - urn: "{RESOURCE}:3.2"
    status: redirected
    replaced_by: ["{RESOURCE}:3.3", "{RESOURCE}:3.4"]
    reason: Split in two.
    date: 2026-11-03
""",
        )
    )
    response = client.get("/api/dts/document", params={"resource": RESOURCE, "ref": "3.2"})
    assert response.status_code == 300
    assert response.headers["content-type"].startswith("application/problem+json")
    body = response.json()
    assert body["urn"] == f"{RESOURCE}:3.2"
    assert [r["urn"] for r in body["replaced_by"]] == [f"{RESOURCE}:3.3", f"{RESOURCE}:3.4"]
    assert body["replaced_by"][0]["url"] == f"{BASE}/document?resource={RESOURCE}&ref=3.3"


def test_retired_ref_answers_410_with_a_tombstone(
    serve: Client, data_repo: Path, edit: Edit
) -> None:
    client = serve(
        without_3_2(
            data_repo,
            edit,
            f"""redirects:
  - urn: "{RESOURCE}:3.2"
    status: retired
    reason: Not part of the printed text.
    date: 2026-11-03
""",
        )
    )
    for endpoint in ("navigation", "document"):
        response = client.get(f"/api/dts/{endpoint}", params={"resource": RESOURCE, "ref": "3.2"})
        assert response.status_code == 410
        assert response.headers["content-type"].startswith("application/problem+json")
        body = response.json()
        assert body["urn"] == f"{RESOURCE}:3.2"
        assert body["reason"] == "Not part of the printed text."
        assert body["date"] == "2026-11-03"
