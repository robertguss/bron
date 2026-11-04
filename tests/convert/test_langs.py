import os
import subprocess
import sys
from pathlib import Path

from lxml import etree

from bron.convert.gd1.html import Converter, parse
from bron.convert.gd1.langs import tag
from bron.convert.gd1.notes import Footnotes
from bron.convert.gd1.pages import for_volume
from bron.tei import XML_LANG, tei
from tests.convert.conftest import PAGE_MAP, xpath

# Real paragraphs of the transcriptions, trimmed, with their volume.
GRATIA = (
    "<p>Het genadeverbond is niet, gelĳk Coccejus leerde, de successieve\nafschaffing, het "
    "is veeleer de vervulling en herstelling van het\nwerkverbond. "
    '<span lang="la">Gratia reparat et perficit naturam</span>. God houdt zich\naan den eisch, '
    "dat alleen in den weg van gehoorzaamheid het\neeuwig leven te verkrĳgen is.</p>",
    3,
)
SCRIPTURE = (
    "<p>Niet de kerk maar de Schrift is αὐτοπιστος, judex controversiarum,\n"
    '<span class="pagenum" id="Page_25">[25]</span>\n'
    "sui ipsius interpres. Niets mag met haar op ééne lĳn\nworden gesteld.</p>",
    1,
)
# The transcribers' span around the second Greek phrase has been removed: vols. 3 and 4
# have no Greek outside their spans.
NATURES = (
    "<p>Daarom is de menschelĳke natuur in Christus niet door een\neigen persoonlĳkheid met "
    "den Logos gecoordineerd maar aan dezen\nondergeschikt. Beide naturen zĳn en blĳven wel "
    '<span lang="grc">ἀλλο και ἀλλο</span>,\nmaar niet ἀλλος και ἀλλος. Het is altĳd '
    "dezelfde persoon,\nhetzelfde subject, hetzelfde ik.</p>",
    3,
)
PROPHETS = (
    "<p>Met den droom is het visioen verwant Gen. 15:1, 11; 20:7;\nNum. 12:6. Reeds de namen "
    "רֹאֶה‎, ‏חֹזֶה‎, ‏נָבִיא en misschien ook\nצֹפֶה waarmede de profeet "
    "genoemd wordt, Kuenen, De Profeten I 58.</p>",
    1,
)
AGES = (
    "<p>Er komt een nieuwe hemel\nen een nieuwe aarde. Deze Jom Jhvh, deze עֹלָם הַבָּא,\n"
    "αἰων μελλων, in tegenstelling met den עֹלָם הַזֶּה, αἰων οὑτος,\nis naar de "
    "voorstelling der Schrift met het N. Test. aangebroken.</p>",
    1,
)
AUGUSTINE = (
    "<p>De leer van de\npraedestinatio en van de gratia is met dit begrip van kerk en\n"
    "sacrament niet overeen te brengen. Multi qui foris videntur intus\nsunt et multi qui "
    "intus videntur foris sunt. Er zĳn schapen\nbuiten en wolven binnen de kooi. Ook leerde "
    "Augustinus wel de\nperseverantia sanctorum, maar hĳ durfde de subjectieve "
    "verzekerdheid\ndaarvan niet aan.</p>",
    1,
)
HUMILITY = (
    "<p>Het werk van Christus bestaat dus niet\nzoozeer in humilitas, niet alleen in zĳn "
    "dood, maar in zĳne\ngansche, zoowel actieve als passieve gehoorzaamheid.</p>",
    3,
)
EXCERPTS = (GRATIA, SCRIPTURE, NATURES, PROPHETS, AGES, AUGUSTINE, HUMILITY)


def paragraph(excerpt: tuple[str, int]) -> etree._Element:
    """One excerpt converted to a TEI `p` and tagged."""
    html, volume = excerpt
    body = parse(f"<html><body>{html}</body></html>".encode()).body
    converter = Converter(for_volume(PAGE_MAP, volume), Footnotes(body))
    [source] = body.iter("p")
    target = etree.Element(tei("p"))
    converter.fill(source, target)
    tag([target])
    return target


def foreign(excerpt: tuple[str, int]) -> list[tuple[str | None, str | None, str]]:
    """Each language span of the tagged excerpt as (xml:lang, resp, text)."""
    return [
        (span.get(XML_LANG), span.get("resp"), "".join(span.itertext()))
        for span in xpath(paragraph(excerpt), ".//tei:foreign")
    ]


def test_a_transcribers_language_span_keeps_its_code_and_names_no_tagger() -> None:
    assert foreign(GRATIA) == [("la", None, "Gratia reparat et perficit naturam")]


def test_an_untagged_greek_word_in_vol_1_is_tagged_by_script() -> None:
    [span] = xpath(paragraph(SCRIPTURE), "tei:foreign[@xml:lang='grc']")
    assert (span.text, span.get("resp")) == ("αὐτοπιστος", "#bron-langid")
    assert span.tail.startswith(", judex")


def test_an_untagged_greek_phrase_in_vol_3_is_tagged_beside_the_transcribers_spans() -> None:
    assert foreign(NATURES) == [
        ("grc", None, "ἀλλο και ἀλλο"),
        ("grc", "#bron-langid", "ἀλλος και ἀλλος"),
    ]


def test_untagged_hebrew_becomes_hbo_without_bidirectional_marks() -> None:
    assert foreign(PROPHETS) == [
        ("hbo", "#bron-langid", "רֹאֶה, חֹזֶה, נָבִיא"),
        ("hbo", "#bron-langid", "צֹפֶה"),
    ]


def test_hebrew_and_greek_side_by_side_each_get_their_own_span() -> None:
    assert [(lang, text) for lang, _, text in foreign(AGES)] == [
        ("hbo", "עֹלָם הַבָּא"),
        ("grc", "αἰων μελλων"),
        ("hbo", "עֹלָם הַזֶּה"),
        ("grc", "αἰων οὑτος"),
    ]


def test_a_clear_latin_sentence_in_vol_1_is_tagged_by_the_identifier() -> None:
    assert foreign(AUGUSTINE) == [
        (
            "la",
            "#bron-langid",
            "Multi qui foris videntur intus sunt et multi qui intus videntur foris sunt",
        )
    ]


def test_a_dutch_sentence_around_a_latin_term_is_not_tagged() -> None:
    # The identifier rates "Ook leerde Augustinus wel de perseverantia sanctorum" Latin
    # (0.91), but "ook" and "wel" are Dutch.
    assert "perseverantia" not in "".join(text for *_, text in foreign(AUGUSTINE))
    assert foreign(HUMILITY) == []


def test_a_latin_phrase_below_the_floor_is_not_tagged() -> None:
    # The identifier is sure "judex controversiarum" and "sui ipsius interpres" are Latin
    # (0.93 and 0.92), but they have 20 and 18 letters.
    assert [lang for lang, *_ in foreign(SCRIPTURE)] == ["grc"]


def test_tagging_is_the_same_in_every_process() -> None:
    # Python seeds string hashing per process, which changes the order in which the
    # identifier sums its probabilities.
    program = (
        "from lxml import etree\n"
        "from tests.convert.test_langs import EXCERPTS, paragraph\n"
        "for excerpt in EXCERPTS:\n"
        "    print(etree.tostring(paragraph(excerpt), encoding='unicode'))\n"
    )
    runs = {
        subprocess.run(
            [sys.executable, "-c", program],
            capture_output=True,
            check=True,
            text=True,
            cwd=Path(__file__).parents[2],
            env={**os.environ, "PYTHONHASHSEED": seed},
        ).stdout
        for seed in ("1", "2")
    }
    here = "".join(
        etree.tostring(paragraph(excerpt), encoding="unicode") + "\n" for excerpt in EXCERPTS
    )
    assert runs == {here}
