import pytest
from fastapi.testclient import TestClient

from tests.dts.conftest import BASE, RESOURCE

SECTION_3 = ["3", *(f"3.{n}" for n in range(1, 12))]
SECTION_4 = ["4", "4.1", "4.2"]


def navigate(client: TestClient, **params: str | int):
    return client.get("/api/dts/navigation", params={"resource": RESOURCE, **params})


def identifiers(body: dict) -> list[str]:
    return [unit["identifier"] for unit in body["member"]]


def test_entry_lists_three_templates_that_expand_to_working_calls(client: TestClient) -> None:
    from uritemplate import URITemplate

    response = client.get("/api/dts/")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/ld+json")
    entry = response.json()
    assert entry["dtsVersion"] == "1.0"
    assert entry["@type"] == "EntryPoint"
    calls: dict[str, dict[str, str | int | None]] = {
        "collection": {"id": RESOURCE},
        "navigation": {"resource": RESOURCE, "ref": "3", "down": 1},
        "document": {"resource": RESOURCE, "ref": "3.2"},
    }
    for endpoint, values in calls.items():
        url = URITemplate(entry[endpoint]).expand(dict(values))
        assert url.startswith(BASE)
        assert client.get(url.removeprefix("http://testserver")).status_code == 200, url


def test_children_of_a_section_are_in_document_order(client: TestClient) -> None:
    response = navigate(client, ref="3", down=1)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/ld+json")
    body = response.json()
    assert identifiers(body) == SECTION_3  # 3.10 after 3.9, not after 3.1
    assert body["ref"] == {
        "identifier": "3",
        "@type": "CitableUnit",
        "level": 1,
        "parent": None,
        "citeType": "section",
    }
    assert {unit["parent"] for unit in body["member"][1:]} == {"3"}
    assert {unit["citeType"] for unit in body["member"][1:]} == {"subparagraph"}


def test_ref_without_down_describes_the_unit_alone(client: TestClient) -> None:
    body = navigate(client, ref="3.2").json()
    assert body["ref"]["identifier"] == "3.2"
    assert body["ref"]["parent"] == "3"
    assert "member" not in body


def test_down_zero_lists_the_unit_with_its_siblings(client: TestClient) -> None:
    assert identifiers(navigate(client, ref="4.1", down=0).json()) == ["4.1", "4.2"]
    assert identifiers(navigate(client, ref="3", down=0).json()) == ["3", "4"]


def test_whole_tree(client: TestClient) -> None:
    assert identifiers(navigate(client, down=-1).json()) == SECTION_3 + SECTION_4


def test_top_level_only(client: TestClient) -> None:
    body = navigate(client, down=1).json()
    assert identifiers(body) == ["3", "4"]
    assert "ref" not in body


def test_down_deeper_than_the_tree_returns_what_exists(client: TestClient) -> None:
    assert identifiers(navigate(client, ref="3", down=99).json()) == SECTION_3
    assert identifiers(navigate(client, ref="3.2", down=1).json()) == ["3.2"]


def test_range(client: TestClient) -> None:
    body = navigate(client, start="3.2", end="3.4").json()
    assert body["start"]["identifier"] == "3.2"
    assert body["end"]["identifier"] == "3.4"
    assert "member" not in body
    with_down = navigate(client, start="3.2", end="3.4", down=1).json()
    assert identifiers(with_down) == ["3.2", "3.3", "3.4"]


def test_range_of_sections_with_their_children(client: TestClient) -> None:
    assert identifiers(navigate(client, start="3", end="4", down=1).json()) == (
        SECTION_3 + SECTION_4
    )


def test_range_across_a_section_boundary_keeps_to_the_cited_level(client: TestClient) -> None:
    body = navigate(client, start="3.10", end="4.1", down=1).json()
    assert identifiers(body) == ["3.10", "3.11", "4.1"]


@pytest.mark.parametrize(
    "params",
    [
        {"ref": "3", "start": "3.1", "end": "3.2"},
        {"ref": "3", "start": "3.1"},
        {"start": "3.1"},
        {"end": "3.1"},
        {},
        {"down": 0},
        {"start": "3.1", "end": "3.2", "down": 0},
        {"ref": "3", "down": -2},
        {"ref": "3", "down": "deep"},
        {"start": "3.4", "end": "3.2"},
    ],
)
def test_invalid_parameter_combinations_are_400(client: TestClient, params: dict) -> None:
    response = navigate(client, **params)
    assert response.status_code == 400
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["status"] == 400


def test_missing_resource_is_400(client: TestClient) -> None:
    assert client.get("/api/dts/navigation", params={"ref": "3"}).status_code == 400


@pytest.mark.parametrize(
    "params",
    [
        {"ref": "9"},
        {"ref": "3.12", "down": 1},
        {"start": "3.1", "end": "9.9"},
        {"ref": "3", "tree": "pages"},
    ],
)
def test_unknown_ref_or_tree_is_404(client: TestClient, params: dict) -> None:
    response = navigate(client, **params)
    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["detail"]


def test_unknown_resource_is_404(client: TestClient) -> None:
    response = client.get(
        "/api/dts/navigation", params={"resource": "urn:cts:bron:nothing", "down": 1}
    )
    assert response.status_code == 404


def test_naming_the_default_tree_is_the_same_as_omitting_it(client: TestClient) -> None:
    named = navigate(client, ref="3", down=1, tree="default").json()
    assert identifiers(named) == identifiers(navigate(client, ref="3", down=1).json())


def test_navigation_describes_its_resource(client: TestClient) -> None:
    body = navigate(client, ref="3", down=1).json()
    assert body["@type"] == "Navigation"
    assert body["dtsVersion"] == "1.0"
    assert body["@id"].startswith(f"{BASE}/navigation?")
    resource = body["resource"]
    assert resource["@id"] == RESOURCE
    assert resource["@type"] == "Resource"
    assert resource["citationTrees"] == [
        {
            "@type": "CitationTree",
            "citeStructure": [
                {
                    "@type": "CiteStructure",
                    "citeType": "section",
                    "citeStructure": [{"@type": "CiteStructure", "citeType": "subparagraph"}],
                }
            ],
        }
    ]


def test_unknown_paths_and_methods_answer_with_problem_bodies(client: TestClient) -> None:
    for response, status in (
        (client.get("/api/dts/nowhere"), 404),
        (client.post("/api/dts/navigation"), 405),
    ):
        assert response.status_code == status
        assert response.headers["content-type"].startswith("application/problem+json")
        assert response.json()["status"] == status


def test_a_failure_inside_the_resolver_answers_500_with_a_problem_body(
    data_repo, monkeypatch
) -> None:
    from bron.dts import responses
    from bron.dts.app import create_app
    from tests.dts.conftest import BASE

    def broken(units):
        raise RuntimeError("extraction failed")

    monkeypatch.setattr(responses, "tei_fragment", broken)
    client = TestClient(create_app(data_repo, base_url=BASE), raise_server_exceptions=False)
    response = client.get("/api/dts/document", params={"resource": RESOURCE, "ref": "3.2"})
    assert response.status_code == 500
    assert response.headers["content-type"].startswith("application/problem+json")
