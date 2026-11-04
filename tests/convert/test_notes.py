from bron.convert.gd1.emit import assemble
from tests.convert.conftest import PAGE_MAP, registry, text_of, wrap, xpath


def test_a_footnote_is_encoded_once_at_its_callout(converted) -> None:
    body = wrap(converted(1).body)
    [note] = xpath(body, "//tei:note")
    assert (note.get("place"), note.get("n")) == ("bottom", "1")
    assert text_of(note).startswith("Kortheidshalve worden hier eenige werken genoemd")
    assert len(xpath(note, "tei:p")) == 2
    paragraph = note.getparent()
    assert text_of(paragraph).startswith("3. De aanvangen der theologie")
    assert text_of(paragraph).split("Zöckler Supplement S. 40 f.")[1].startswith("Kortheidshalve")


def test_the_footnote_text_appears_nowhere_else_in_the_file(converted) -> None:
    tei = assemble([converted(1)], registry(), PAGE_MAP, "0" * 40).decode("utf-8")
    assert tei.count("Kortheidshalve worden hier eenige werken") == 1


def test_a_footnote_in_the_contents_stays_in_the_front_matter(converted) -> None:
    front = converted(2).front
    [note] = xpath(front, ".//tei:note")
    assert note.get("n") == "*"
    assert text_of(note).startswith("Naar deze opgave gelieve men")
    assert note.getparent().tag.endswith("cell")
