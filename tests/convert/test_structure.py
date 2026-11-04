import pytest

from bron.convert.gd1 import ConversionError
from bron.convert.gd1.emit import convert_volume
from bron.convert.gd1.structure import allowed_gaps, check_numbers
from tests.convert.conftest import PAGE_MAP, edited, text_of, wrap, xpath

SECTION = "//tei:div[@type='section'][@n='{}']"
SUB = SECTION + "/tei:div[@type='subparagraph'][@n='{}']"


def test_section_3_subparagraph_2_opens_with_its_page_break_and_number(converted) -> None:
    body = wrap(converted(1).body)
    [sub] = xpath(body, SUB.format(3, 2))
    first = sub[0]
    assert first.tag.endswith("pb")
    assert first.get("n") == "15"
    assert first.get("facs").endswith("bavi002gere01_01.pdf#page=25")
    [p] = xpath(sub, "tei:p")
    assert text_of(p).startswith("2. Maar de kerk")


def test_an_unnumbered_paragraph_continues_the_open_subparagraph(converted) -> None:
    body = wrap(converted(1).body)
    paragraphs = xpath(body, SUB.format(5, 2) + "/tei:p")
    assert len(paragraphs) == 2
    assert text_of(paragraphs[0]).startswith("2. Bĳ deze eenvoudige")
    assert text_of(paragraphs[1]).startswith("Tegenover deze verschillende aanvallen")
    assert xpath(body, "//tei:div[@type='subparagraph'][not(@n)]") == []


def test_lettered_headings_head_the_subparagraph_their_numbered_paragraph_opens(
    converted,
) -> None:
    body = wrap(converted(1).body)
    [head_a] = xpath(body, SUB.format(5, 1) + "/tei:head")
    assert text_of(head_a).startswith("A. Opkomst der dogmatiek")
    [head_b] = xpath(body, SUB.format(5, 5) + "/tei:head")
    assert text_of(head_b).startswith("B. De dogmatiek in de Oostersche Kerk")
    assert xpath(body, SUB.format(5, 4) + "/tei:head") == []
    last = xpath(body, SUB.format(5, 4) + "/tei:p")[-1]
    assert text_of(last).startswith("4. In den aanvang der derde eeuw")


def test_a_lettered_heading_followed_by_an_unnumbered_paragraph_fails_with_its_location() -> None:
    html = edited(1, "<p>5. De periode", "<p>De periode")
    with pytest.raises(ConversionError) as error:
        convert_volume(html, 1, PAGE_MAP)
    message = str(error.value)
    assert "vol. 1" in message
    assert "line " in message
    assert "B. De dogmatiek in de Oostersche Kerk" in message


def test_a_numbered_paragraph_opening_with_an_empty_anchor_opens_its_subparagraph(
    converted,
) -> None:
    body = wrap(converted(4).body)
    [p] = xpath(body, SUB.format(53, 3) + "/tei:p")
    assert text_of(p).startswith("3. Dit avondmaal")


def test_a_corrected_subparagraph_number_is_cited_by_its_correction(converted) -> None:
    body = wrap(converted(4).body)
    numbers = [sub.get("n") for sub in xpath(body, SECTION.format(51) + "/tei:div")]
    assert numbers == ["1", "2", "3", "4", "5", "6", "7"]
    [choice] = xpath(body, SUB.format(51, 7) + "/tei:p/tei:choice")
    assert [text_of(choice[0]), text_of(choice[1])] == ["6.", "7."]
    assert [child.tag.split("}")[1] for child in choice] == ["sic", "corr"]


def test_the_allowed_gap_in_section_29_passes_the_number_check(converted) -> None:
    volume = converted(2)
    numbers = [s.n for s in volume.sections[0].subparagraphs]
    assert [s.n for s in volume.sections] == [28, 29]
    assert 11 not in [s.n for s in volume.sections[1].subparagraphs]
    assert numbers == [1, 2]
    gaps = check_numbers(volume.sections, allowed_gaps(PAGE_MAP))
    assert gaps == [(2, 29, 11)]


def test_a_jump_not_on_the_allow_list_fails_naming_volume_section_and_number() -> None:
    html = edited(2, '<p class="sep2">10. De Schrift', '<p class="sep2">De Schrift')
    volume = convert_volume(html, 2, PAGE_MAP)
    with pytest.raises(ConversionError) as error:
        check_numbers(volume.sections, allowed_gaps(PAGE_MAP))
    message = str(error.value)
    assert "vol. 2" in message
    assert "§ 29" in message
    assert "subparagraph 10" in message


def test_sections_must_follow_each_other_without_a_gap(converted) -> None:
    with pytest.raises(ConversionError) as error:
        check_numbers([*converted(1).sections, *converted(2).sections], allowed_gaps(PAGE_MAP))
    assert "§ 6" in str(error.value)
