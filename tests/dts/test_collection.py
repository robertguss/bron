from pathlib import Path

from fastapi.testclient import TestClient

from tests.dts.conftest import BASE, RESOURCE, Client

ROOT = "urn:cts:bron"
TEXTGROUP = "urn:cts:bron:fixture"
WORK = "urn:cts:bron:fixture.gd"


def collection(client: TestClient, **params: str) -> dict:
    response = client.get("/api/dts/collection", params=params)
    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("application/ld+json")
    return response.json()


def test_root_collection_lists_the_textgroups(client: TestClient) -> None:
    root = collection(client)
    assert root["@id"] == ROOT
    assert root["@type"] == "Collection"
    assert root["dtsVersion"] == "1.0"
    assert root["totalParents"] == 0
    assert root["totalChildren"] == 1
    assert [m["@id"] for m in root["member"]] == [TEXTGROUP]
    assert root["member"][0]["title"] == "Herman Bavinck"


def test_work_lists_its_edition_as_a_resource(client: TestClient) -> None:
    work = collection(client, id=WORK)
    assert work["title"] == "Gereformeerde Dogmatiek"
    assert {"lang": "en", "value": "Reformed Dogmatics"} in work["dublinCore"]["title"]
    assert work["totalParents"] == 1
    assert work["totalChildren"] == 1
    (edition,) = work["member"]
    assert edition["@id"] == RESOURCE
    assert edition["@type"] == "Resource"
    assert edition["totalChildren"] == 0


def test_resource_carries_its_endpoint_templates_and_citation_tree(client: TestClient) -> None:
    resource = collection(client, id=RESOURCE)
    assert resource["@type"] == "Resource"
    assert resource["title"] == "Gereformeerde Dogmatiek, eerste druk (testexcerpt)"
    assert resource["description"] == "A trimmed excerpt of the first edition, for tests."
    assert resource["dublinCore"]["language"] == ["nl"]
    assert resource["mediaTypes"] == ["application/tei+xml"]
    assert resource["collection"] == f"{BASE}/collection?id={RESOURCE}{{&nav}}"
    assert resource["navigation"] == (
        f"{BASE}/navigation?resource={RESOURCE}{{&ref,start,end,down,tree,page}}"
    )
    assert resource["document"] == (
        f"{BASE}/document?resource={RESOURCE}{{&ref,start,end,tree,mediaType}}"
    )
    assert resource["citationTrees"][0]["citeStructure"][0]["citeType"] == "section"


def test_parents_lead_back_to_the_root(client: TestClient) -> None:
    chain = []
    current = RESOURCE
    while True:
        body = collection(client, id=current, nav="parents")
        if not body.get("member"):
            assert body["totalParents"] == 0
            break
        (parent,) = body["member"]
        chain.append(parent["@id"])
        current = parent["@id"]
    assert chain == [WORK, TEXTGROUP, ROOT]


def test_unknown_id_is_404_and_bad_nav_is_400(client: TestClient) -> None:
    response = client.get("/api/dts/collection", params={"id": "urn:cts:bron:nothing"})
    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/problem+json")
    assert client.get("/api/dts/collection", params={"nav": "siblings"}).status_code == 400


def test_a_repository_without_editions_serves_its_collections(
    serve: Client, metadata_only_repo: Path
) -> None:
    client = serve(metadata_only_repo)
    assert client.get("/api/dts/").status_code == 200
    work = collection(client, id=WORK)
    assert work["totalChildren"] == 0
    assert work.get("member", []) == []
