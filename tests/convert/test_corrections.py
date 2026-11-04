import lxml.html
from lxml import etree

from bron.convert.gd1.html import Converter, parse
from bron.convert.gd1.notes import Footnotes
from bron.convert.gd1.pages import for_volume
from bron.tei import tei
from tests.convert.conftest import PAGE_MAP, excerpt, text_of, wrap, xpath


def paragraph(html: str, volume: int = 1) -> etree._Element:
    """One real HTML paragraph, converted to a TEI `p`."""
    body = parse(f"<html><body>{html}</body></html>".encode()).body
    converter = Converter(for_volume(PAGE_MAP, volume), Footnotes(body))
    [source] = body.iter("p")
    target = etree.Element(tei("p"))
    converter.inline(source, target)
    return target


def test_a_correction_shows_the_printed_reading_and_the_correction() -> None:
    p = paragraph(
        '<p>en in allerlei bĳzondere dogmata zich vertakt en <ins title="geplitst" '
        'id="cor_3">gesplitst</ins> heeft.</p>'
    )
    [choice] = xpath(p, "tei:choice")
    assert [(child.tag, child.text) for child in choice] == [
        (tei("sic"), "geplitst"),
        (tei("corr"), "gesplitst"),
    ]
    assert choice.tail == " heeft."


def test_an_inserted_word_has_an_empty_reading_and_the_transcribers_note() -> None:
    p = paragraph(
        '<p>Er moet daarom onderscheiden <ins title="\u2019worden\u2019 ingevoegd" '
        'id="cor_1">worden</ins> tusschen</p>'
    )
    [choice] = xpath(p, "tei:choice")
    assert choice[0].tag == tei("sic") and len(choice[0]) == 0 and not choice[0].text
    assert text_of(choice[1]) == "worden"
    note = choice.getnext()
    assert (note.tag, note.get("type"), note.text) == (
        tei("note"),
        "transcriber",
        "\u2019worden\u2019 ingevoegd",
    )


def test_a_correction_inside_a_hebrew_span_stays_inside_it(converted) -> None:
    [source] = lxml.html.document_fromstring(excerpt(2)).xpath("//span[@lang='hbo']/ins")
    printed, corrected = source.get("title", ""), source.text or ""
    body = wrap(converted(2).body)
    [choice] = xpath(body, "//tei:foreign/tei:choice")
    unmarked = str.maketrans("", "", "\u200e\u200f")
    assert text_of(choice[0]) == printed.translate(unmarked)
    assert text_of(choice[1]) == corrected.translate(unmarked)


def test_bidirectional_marks_are_removed_and_the_hebrew_kept_in_order() -> None:
    hebrew = "שְׂעִירִם"
    p = paragraph(f'<p>de <span lang="hbo">\u200e\u200f{hebrew}\u200f\u200e</span>, Lev. 17:7</p>')
    [span] = xpath(p, "tei:foreign")
    assert span.text == hebrew
    assert "\u200e" not in text_of(p) and "\u200f" not in text_of(p)


def test_a_printed_section_number_is_kept_beside_its_correction(converted) -> None:
    body = wrap(converted(2).body)
    [head] = xpath(body, "//tei:div[@n='28']/tei:head")
    [choice] = xpath(head, "tei:choice")
    assert choice.get("resp") == "#bron-convert"
    assert [text_of(choice[0]), text_of(choice[1])] == ["26", "28"]
    assert text_of(head).endswith(". De Raad Gods.")


def test_every_correction_in_a_volume_is_converted(converted) -> None:
    for number in (1, 2, 4):
        source = lxml.html.document_fromstring(excerpt(number))
        assert converted(number).corrections == len(list(source.iter("ins")))
