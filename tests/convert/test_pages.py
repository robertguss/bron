import pytest

from bron.convert.gd1 import ConversionError
from tests.convert.conftest import text_of, wrap, xpath

XML_ID = "{http://www.w3.org/XML/1998/namespace}id"


def test_a_page_span_inside_a_section_heading_opens_the_section(converted) -> None:
    body = wrap(converted(2).body)
    [section] = xpath(body, "//tei:div[@type='section'][@n='28']")
    page_break = section[0]
    assert page_break.tag.endswith("pb")
    assert (page_break.get("n"), page_break.get(XML_ID)) == ("313", "v2-p313")
    assert page_break.get("facs") == (
        "https://www.dbnl.org/arch/bavi002gere02_01/pag/bavi002gere02_01.pdf#page=319"
    )
    assert page_break.get("resp") is None
    assert text_of(section[1]).startswith("§")


def test_an_unmarked_chapter_opening_page_is_inserted_before_the_chapter(converted) -> None:
    body = converted(2).body
    [index] = [i for i, d in enumerate(body) if d.get("type") == "chapter" and d.get("n") == "V"]
    page_break = body[index - 1]
    assert page_break.tag.endswith("pb")
    assert (page_break.get("n"), page_break.get("resp")) == ("386", "#bron-convert")
    assert page_break.get("facs").endswith("bavi002gere02_01.pdf#page=392")


def test_an_unmarked_front_matter_page_is_inserted_before_the_contents(converted) -> None:
    front = converted(1).front
    [contents] = [d for d in xpath(front, "tei:div") if text_of(d).startswith("INHOUD.")]
    page_break = contents.getprevious()
    assert (page_break.get("n"), page_break.get("resp")) == ("VI", "#bron-convert")
    assert page_break.get("facs").endswith("bavi002gere01_01.pdf#page=8")
    [in_cell] = xpath(front, ".//tei:cell/tei:pb")
    assert in_cell.get("n") == "VII"


def test_a_marker_whose_label_is_not_its_number_takes_the_number_from_the_map(
    converted,
) -> None:
    volume = converted(4)
    [page_break] = xpath(wrap(volume.body), "//tei:pb[@n='484']")
    assert page_break.get("facs").endswith("bavi002gere04_01.pdf#page=490")
    assert ("484", "]") in volume.pages.malformed
    assert "]" not in text_of(page_break.getparent())


def test_a_marker_split_from_its_label_breaks_before_the_marked_word(converted) -> None:
    body = wrap(converted(4).body)
    [page_break] = xpath(body, "//tei:pb[@n='18']")
    assert page_break.tail.lstrip().startswith("uitverkorenen")
    assert "[18]" not in text_of(body)
    [anchored] = xpath(body, "//tei:pb[@n='369']")
    assert anchored.tail.lstrip().startswith("zĳn dood")
    assert "[369]" not in text_of(body)


def test_every_page_in_the_map_must_appear_once(converted) -> None:
    with pytest.raises(ConversionError) as error:
        converted(1).pages.check_complete()
    message = str(error.value)
    assert "vol. 1" in message
    assert "2, 3, 4" in message
