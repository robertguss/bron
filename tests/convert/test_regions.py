import pytest

from bron.convert.gd1 import ConversionError
from bron.convert.gd1.emit import convert_volume
from tests.convert.conftest import PAGE_MAP, edited, text_of, wrap, xpath


def test_a_volumes_title_page_and_contents_land_in_its_front_division(converted) -> None:
    front = converted(2).front
    assert (front.get("type"), front.get("n")) == ("volume", "2")
    heads = [text_of(head) for head in xpath(front, ".//tei:head")]
    assert "GEREFORMEERDE DOGMATIEK." in heads
    assert "INHOUD." in heads
    assert "TWEEDE DEEL." in text_of(front)
    assert "Opmerkingen van de bewerker" not in text_of(front)


def test_the_body_opens_with_the_volume_milestone_then_its_first_page_break(converted) -> None:
    body = converted(2).body
    assert body[0].tag.endswith("milestone")
    assert (body[0].get("unit"), body[0].get("n")) == ("volume", "2")
    assert body[1].tag.endswith("pb")
    assert body[1].get("n") == "1"
    assert body[1].get("{http://www.w3.org/XML/1998/namespace}id") == "v2-p1"


def test_a_preface_without_a_heading_keeps_its_own_division(converted) -> None:
    front = converted(3).front
    divisions = xpath(front, "tei:div")
    openings = ["GEREFORMEERDE DOGMATIEK", "GEREFORMEERDE", "Onder de bewerking", "INHOUD."]
    assert len(divisions) == len(openings)
    for division, opening in zip(divisions, openings, strict=True):
        assert text_of(division).startswith(opening)


def test_back_matter_starts_at_its_anchor_and_is_never_part_of_a_subparagraph(converted) -> None:
    volume = converted(4)
    assert volume.back is not None
    assert text_of(xpath(volume.back, "tei:div/tei:head")[0]) == "BREEDERE INHOUDSOPGAVE."
    entries = [p for p in xpath(volume.back, ".//tei:p") if text_of(p).startswith("§ 1.")]
    assert len(entries) == 1
    body = wrap(volume.body)
    last = xpath(body, "//tei:div[@type='section'][@n='56']/tei:div[last()]")[0]
    assert last.get("n") == "11"
    assert text_of(xpath(last, "tei:p")[-1]).endswith("1895-1900.")
    assert "BREEDERE" not in text_of(body)
    assert "§ 1. Naam en begrip" not in text_of(body)


def test_a_volume_whose_named_boundary_is_missing_fails() -> None:
    html = edited(4, '<h2 id="_inhoud">', '<h2 id="_breedere">')
    with pytest.raises(ConversionError) as error:
        convert_volume(html, 4, PAGE_MAP)
    assert "vol. 4" in str(error.value)
    assert "_inhoud" in str(error.value)
