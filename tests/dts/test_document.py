from pathlib import Path

from fastapi.testclient import TestClient
from lxml import etree

from bron.tei import TEI_NS, XML_ID, tei
from bron.tei.text import normalized_text
from tests.conftest import EDITION, Edit
from tests.dts.conftest import BASE, RESOURCE

DTS_NS = "https://w3id.org/api/dts#"


def document(client: TestClient, **params: str):
    return client.get("/api/dts/document", params={"resource": RESOURCE, **params})


def wrapper(response) -> etree._Element:
    assert response.status_code == 200, response.text
    root = etree.fromstring(response.content)
    assert root.tag == tei("TEI")
    found = root.find(f"{{{DTS_NS}}}wrapper")
    assert found is not None
    return found


def subparagraphs(fragment: etree._Element) -> list[str]:
    return [div.get("n", "") for div in fragment.iterfind(tei("div"))]


def first_page_break(fragment: etree._Element) -> etree._Element:
    found = fragment.find(f".//{tei('pb')}")
    assert found is not None
    return found


def source_text(repo: Path, section: str, subparagraph: str) -> str:
    tree = etree.parse(str(repo / EDITION))
    found = tree.xpath(
        f"//tei:div[@type='section'][@n='{section}']/tei:div[@n='{subparagraph}']",
        namespaces={"tei": TEI_NS},
    )
    return normalized_text(found[0])


def test_a_passage_that_opens_with_a_page_break_carries_it_once(
    client: TestClient, data_repo: Path
) -> None:
    response = document(client, ref="3.2")
    assert response.headers["content-type"].startswith("application/tei+xml")
    assert response.headers["link"] == (f'<{BASE}/collection?id={RESOURCE}>; rel="collection"')
    fragment = wrapper(response)
    assert subparagraphs(fragment) == ["2"]
    page_breaks = fragment.findall(f".//{tei('pb')}")
    assert len(page_breaks) == 1
    assert page_breaks[0].get("n") == "15"
    assert page_breaks[0].get(XML_ID) == "v1-p15"  # the original, inside the passage
    assert normalized_text(fragment) == source_text(data_repo, "3", "2")
    assert normalized_text(fragment).startswith("2. Maar de kerk")


def test_a_passage_starting_mid_page_carries_the_earlier_page_break(client: TestClient) -> None:
    fragment = wrapper(document(client, ref="3.5"))
    anchor = fragment[0]
    assert anchor.tag == tei("pb")
    assert anchor.get("n") == "15"  # not 18, which falls inside the passage
    assert anchor.get(XML_ID) is None
    assert anchor.get("corresp") == "#v1-p15"
    assert anchor.get("facs", "").endswith("bavi002gere01_01.pdf#page=25")
    ids = [element.get(XML_ID) for element in fragment.iter() if element.get(XML_ID)]
    assert ids == ["v1-p18"]


def test_the_first_passage_takes_the_volume_opening_page_break(client: TestClient) -> None:
    anchor = wrapper(document(client, ref="3.1"))[0]
    assert anchor.get("corresp") == "#v1-p14"


def test_a_section_is_returned_whole(client: TestClient, data_repo: Path) -> None:
    fragment = wrapper(document(client, ref="4"))
    assert fragment[0].get("corresp") == "#v1-p22"
    section = fragment[1]
    assert section.get("n") == "4"
    assert subparagraphs(section) == ["1", "2"]


def test_a_range_within_a_section(client: TestClient, data_repo: Path) -> None:
    fragment = wrapper(document(client, start="3.2", end="3.3"))
    assert subparagraphs(fragment) == ["2", "3"]
    assert first_page_break(fragment).get(XML_ID) == "v1-p15"  # 3.2 opens with its own
    assert normalized_text(fragment) == " ".join(
        [source_text(data_repo, "3", "2"), source_text(data_repo, "3", "3")]
    )


def test_a_range_across_a_section_boundary_keeps_every_subparagraph(
    client: TestClient, data_repo: Path
) -> None:
    fragment = wrapper(document(client, start="3.2", end="4.1"))
    assert subparagraphs(fragment) == [*(str(n) for n in range(2, 12)), "1"]
    expected = [source_text(data_repo, "3", str(n)) for n in range(2, 12)]
    assert normalized_text(fragment) == " ".join([*expected, source_text(data_repo, "4", "1")])
    assert first_page_break(fragment).get("n") == "15"


def test_every_fragment_parses_and_holds_no_duplicate_ids(client: TestClient) -> None:
    for params in ({"ref": "4.1"}, {"start": "3.1", "end": "4.2"}, {"ref": "3"}):
        fragment = wrapper(document(client, **params))
        ids = [element.get(XML_ID) for element in fragment.iter() if element.get(XML_ID)]
        assert len(ids) == len(set(ids)), params


def test_no_page_break_before_the_passage_adds_none(
    client: TestClient, data_repo: Path, edit: Edit, serve
) -> None:
    edit(
        data_repo / EDITION,
        '<pb n="14" xml:id="v1-p14" facs="https://www.dbnl.org/arch/bavi002gere01_01/pag/'
        'bavi002gere01_01.pdf#page=24"/>',
        "",
    )
    fragment = wrapper(document(serve(data_repo), ref="3.1"))
    assert fragment.find(tei("pb")) is None


def test_the_whole_resource_is_the_tei_file(client: TestClient, data_repo: Path) -> None:
    response = client.get("/api/dts/document", params={"resource": RESOURCE})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/tei+xml")
    assert response.content == (data_repo / EDITION).read_bytes()


def test_tei_media_type_is_accepted_and_others_are_404(client: TestClient) -> None:
    assert document(client, ref="3.2", mediaType="application/tei+xml").status_code == 200
    response = document(client, ref="3.2", mediaType="text/html")
    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/problem+json")


def test_invalid_combinations_and_unknown_refs(client: TestClient) -> None:
    assert client.get("/api/dts/document", params={"ref": "3.2"}).status_code == 400
    assert document(client, ref="3.2", start="3.1", end="3.3").status_code == 400
    assert document(client, start="3.1").status_code == 400
    assert document(client, ref="3.12").status_code == 404
    assert document(client, ref="3.2", tree="pages").status_code == 404
    assert document(client, ref="3.2", tree="default").status_code == 200


def test_a_range_of_subparagraphs_never_returns_a_whole_section(client: TestClient) -> None:
    fragment = wrapper(document(client, start="3.1", end="4.2"))
    assert subparagraphs(fragment) == [*(str(n) for n in range(1, 12)), "1", "2"]
    assert "§ 4." not in normalized_text(fragment)


def test_a_range_of_sections_returns_them_whole(client: TestClient) -> None:
    fragment = wrapper(document(client, start="3", end="4"))
    assert subparagraphs(fragment) == ["3", "4"]
