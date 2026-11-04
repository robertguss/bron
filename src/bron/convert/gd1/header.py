"""The TEI header of GD¹: sources, credits, licence, editorial decisions and citation scheme.

The header names each source copy with its content hash: the four transcriptions with
their durable copies, and the four DBNL scans the page breaks link to. It credits the
transcribers each ebook names and keeps their own notes and correction lists as provenance.
It declares `#bron-convert`, the converter at the given bron commit, and `#bron-langid`,
for machine language tags. `editorialDecl` states every decision the conversion makes,
including how the machine language tags were made, so a reader can tell the print, the
transcribers' work and Bron's encoding apart.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from importlib.metadata import version
from typing import Any

from lxml import etree

from bron.convert.gd1 import CONVERTER, TAGGER, langs
from bron.tei import XML_ID, XML_LANG, tei

PUBLIC_DOMAIN_MARK = "https://creativecommons.org/publicdomain/mark/1.0/"
CC0 = "https://creativecommons.org/publicdomain/zero/1.0/"
DP_TEAM = "Online Distributed Proofreading Team"

# The footnote to vol. 2's Inhoud, which asks readers to correct §§ 27-33.
RENUMBERING_NOTE = (
    "Naar deze opgave gelieve men de foutieve nummering van de paragrafen 27-33 in den "
    "tekst te herstellen."
)

CTS_PATTERNS = (
    (
        "subparagraph",
        r"(\w+)\.(\w+)",
        "#xpath(/tei:TEI/tei:text/tei:body//tei:div[@type='section'][@n='$1']"
        "/tei:div[@type='subparagraph'][@n='$2'])",
    ),
    (
        "section",
        r"(\w+)",
        "#xpath(/tei:TEI/tei:text/tei:body//tei:div[@type='section'][@n='$1'])",
    ),
)


@dataclass
class Provenance:
    """What the header records about one volume."""

    volume: int
    ebook: Mapping[str, Any]  # the registry record of the transcription
    scan: Mapping[str, Any]  # the registry record of the DBNL scan
    title: str
    transcribers: list[str]
    notes: list[etree._Element]  # the transcribers' notes, as TEI
    inserted: list[str]  # pages whose page break the converter inserted
    malformed: list[tuple[str, str]]  # (page, label shown) for mislabelled markers


def header(
    volumes: Sequence[Provenance], page_map: Mapping[str, Any], commit: str
) -> etree._Element:
    root = etree.Element(tei("teiHeader"))
    root.set(XML_LANG, "en")
    file_desc = etree.SubElement(root, tei("fileDesc"))
    _title_statement(etree.SubElement(file_desc, tei("titleStmt")), volumes, commit)
    publication = etree.SubElement(file_desc, tei("publicationStmt"))
    _add(publication, "publisher", "Bron")
    availability = etree.SubElement(publication, tei("availability"), status="free")
    _add(
        availability,
        "licence",
        "Public Domain Mark 1.0: the work and this transcription are in the public domain.",
        target=PUBLIC_DOMAIN_MARK,
    )
    _add(
        availability,
        "licence",
        "CC0 1.0: any rights Bron might hold in this encoding are waived.",
        target=CC0,
    )
    sources = etree.SubElement(etree.SubElement(file_desc, tei("sourceDesc")), tei("listBibl"))
    for volume in volumes:
        sources.append(_ebook(volume))
        sources.append(_scan(volume))
    encoding = etree.SubElement(root, tei("encodingDesc"))
    decisions = etree.SubElement(encoding, tei("editorialDecl"))
    for paragraph in _decisions(volumes, page_map, commit):
        _add(decisions, "p", paragraph)
    cts = etree.SubElement(encoding, tei("refsDecl"), n="CTS")
    for name, match, replacement in CTS_PATTERNS:
        etree.SubElement(
            cts,
            tei("cRefPattern"),
            n=name,
            matchPattern=match,
            replacementPattern=replacement,
        )
    default = etree.SubElement(encoding, tei("refsDecl"), default="true")
    sections = etree.SubElement(
        default,
        tei("citeStructure"),
        unit="section",
        match="/TEI/text/body//div[@type='section']",
        use="@n",
    )
    etree.SubElement(
        sections,
        tei("citeStructure"),
        unit="subparagraph",
        match="div[@type='subparagraph']",
        use="@n",
        delim=".",
    )
    return root


def _title_statement(statement: etree._Element, volumes: Sequence[Provenance], commit: str) -> None:
    _add(statement, "title", "Gereformeerde Dogmatiek")
    _add(statement, "title", "Eerste druk, Kampen: J. H. Bos, 1895-1901", type="sub")
    _add(statement, "author", "Herman Bavinck")
    for volume in volumes:
        credit = etree.SubElement(statement, tei("respStmt"))
        _add(credit, "resp", f"transcription and proofreading of deel {volume.volume}")
        for person in volume.transcribers:
            _add(credit, "persName", person)
        _add(credit, "orgName", DP_TEAM)
    converter = etree.SubElement(statement, tei("respStmt"))
    _add(converter, "resp", f"conversion to TEI at bron commit {commit}")
    _add(converter, "name", "bron convert gd1").set(XML_ID, CONVERTER.removeprefix("#"))
    tagger = etree.SubElement(statement, tei("respStmt"))
    _add(tagger, "resp", "machine language tagging")
    _add(tagger, "name", "bron language identification").set(XML_ID, TAGGER.removeprefix("#"))


def _ebook(volume: Provenance) -> etree._Element:
    record = volume.ebook
    bibl = etree.Element(tei("bibl"))
    bibl.set(XML_ID, record["id"])
    _add(bibl, "title", volume.title)
    _add(bibl, "author", "Herman Bavinck")
    _add(bibl, "edition", f"{record['edition']}; {record['printing']}")
    _add(bibl, "publisher", record["holder"])
    _add(bibl, "idno", str(record["holder_id"]), type="ebook")
    _add(bibl, "ref", record["url"], target=record["url"])
    _add(bibl, "idno", record["sha256"], type="sha256")
    for mirror in record.get("mirrors") or []:
        _add(bibl, "ref", mirror["url"], target=mirror["url"], type=mirror["kind"])
    notes = etree.SubElement(bibl, tei("note"), type="transcription")
    notes.set(XML_LANG, "nl")
    notes.extend(volume.notes)
    return bibl


def _scan(volume: Provenance) -> etree._Element:
    record = volume.scan
    bibl = etree.Element(tei("bibl"))
    bibl.set(XML_ID, record["id"])
    _add(bibl, "title", "Gereformeerde Dogmatiek")
    _add(bibl, "author", "Herman Bavinck")
    _add(bibl, "edition", f"{record['edition']}; {record['printing']}")
    _add(bibl, "publisher", record["holder"])
    _add(bibl, "idno", str(record["holder_id"]), type="dbnl")
    _add(bibl, "ref", record["url"], target=record["url"])
    _add(bibl, "idno", record["sha256"], type="sha256")
    _add(bibl, "note", "The scan whose pages the page breaks of this volume link to.")
    return bibl


def _decisions(
    volumes: Sequence[Provenance], page_map: Mapping[str, Any], commit: str
) -> list[str]:
    inserted = [f"vol. {v.volume} p. {page}" for v in volumes for page in v.inserted]
    malformed = [
        f"vol. {v.volume} p. {page} (shows {shown!r})"
        for v in volumes
        for page, shown in v.malformed
    ]
    headings = [
        f"§ {item['section']} is printed '§ {item['printed']}' (p. {item['page']})"
        for item in page_map.get("headings") or []
    ]
    numbering = page_map.get("numbering") or []
    gaps = [
        f"§ {item['section']} has no subparagraph {item['missing']} "
        f"(vol. {item['volume']}, pp. {item['pages']})"
        for item in numbering
        if "missing" in item
    ]
    twice = [
        f"vol. {item['volume']} § {item['section']} prints '{item['printed_twice']}.' twice "
        f"(pp. {item['pages']}); the transcribers corrected the second, which is cited as "
        f"{int(item['printed_twice']) + 1}"
        for item in numbering
        if "printed_twice" in item
    ]
    return [
        "Conversion. This file was converted once, by bron convert gd1 at bron commit "
        f"{commit}, from the Distributed Proofreaders transcriptions in the source "
        "description, each checked against its SHA-256. From then on the TEI is the "
        "canonical text: corrections are edits to it, not new conversions.",
        "Regions. Each volume's title page, preface and contents are in front, in a div of "
        "type volume per volume. The Breedere inhoudsopgave and registers that close vol. 4 "
        "(pp. 530-590) are in back. Neither is citable. The body holds the §§, cited by "
        "number, and their subparagraphs, cited as §.¶. Chapters are uncited, and each "
        "volume opens with a milestone of unit volume.",
        "Page breaks. Every pb carries its printed page number and a facs link to that page "
        "of DBNL's scan PDF of the volume, from Bron's measured page map. Pages the "
        "transcription leaves unmarked have page breaks inserted by the converter "
        f"(resp #bron-convert): {_listing(inserted)}. Page markers whose visible label is "
        f"not their number take the number from their anchor: {_listing(malformed)}.",
        "Corrections. Every correction the transcribers made in the text is encoded as "
        "choice: sic holds the printed reading they recorded, corr their correction. Where "
        "they inserted a missing word, sic is empty and their remark follows as a note of "
        "type transcriber. One correction in vol. 4 (elkandar, p. 187) is malformed in the "
        "transcription, its printed reading spilled into the text, and is encoded from that "
        "text.",
        "Renumbered headings. The printed headings of vol. 2 carry wrong § numbers: "
        f"{_listing(headings)}. The volume's Inhoud corrects them in a footnote: "
        f"'{RENUMBERING_NOTE}' The transcribers applied the correction silently. Bron cites "
        "the corrected numbers and keeps each printed number as sic in a choice with resp "
        "#bron-convert.",
        "Corrected subparagraph numbers are cited by the correction, the printed number kept "
        f"as sic: {_listing(twice)}.",
        f"Numbering gaps, checked on the scans: {_listing(gaps)}. No number is invented, so "
        "these subparagraphs have no identifier.",
        "Characters. Spelling is as printed, and the Dutch ĳ ligature (U+0133) is kept as "
        "transcribed. The bidirectional marks U+200E and U+200F that the transcription puts "
        "around Hebrew for display are removed; the Hebrew is stored in logical order, which "
        "removing them does not change. The transcribers' own silent normalizations are "
        "stated in their notes, kept with each volume in the source description: æ and œ, "
        "printed as ae and oe, stay so; spacing and punctuation are corrected here and "
        "there; German nouns are capitalized where needed (vol. 1); run-together expressions "
        "such as afteleiden are split (vols. 2-4); misprints in Hebrew are corrected and its "
        "diacritics corrected or completed, while misprints in Greek are left as printed "
        "(vols. 2-4).",
        "Footnotes are encoded once each, as notes placed at the bottom, at their callouts, "
        "with the label the book prints.",
        "Not encoded: the ebook's header, footer and licence; the transcribers' navigation "
        "links and their own headings; images (rules, ornaments, and the signature "
        "facsimile under vol. 1's Voorbericht); the expansions the transcribers attached to "
        "abbreviations such as LXX, O. T. and N. T. (vols. 3-4); the duplicate link text vol. "
        "2 adds for handheld readers; and hyperlinks, including those from vols. 2-4 to the "
        "ebooks of the other volumes, whose text is kept.",
        _languages(),
    ]


def _languages() -> str:
    names = ", ".join(language.name.title() for language in langs.LANGUAGES)
    words = ", ".join(sorted(langs.DUTCH_WORDS))
    also = "; ".join(f"{word} ({languages})" for word, languages in sorted(langs.ALSO.items()))
    return (
        "Languages. The tags come in three layers. The language spans the transcribers marked "
        "(vols. 2-4) are kept as foreign with their code and no resp. Every run of Greek or "
        "Hebrew script outside a span of its language is tagged as foreign with xml:lang grc "
        "or hbo and resp #bron-langid, so every Greek and Hebrew character is inside a "
        "language span. Latin, German and French outside any language span are tagged as "
        "foreign with xml:lang la, de or fr and resp #bron-langid by statistical language "
        f"identification with {langs.LIBRARY} {version(langs.LIBRARY)}, whose language "
        "models ship in the package, so its version is the model version. The candidates "
        "are clauses: the text between punctuation marks, quotation marks, parentheses, notes "
        "and other language spans, and the text of each highlighted phrase. The identifier "
        f"chooses among {names}. A clause is tagged when it is identified as Latin, German "
        f"or French with a confidence above {langs.THRESHOLD}, has more than {langs.FLOOR} "
        "letters, and has no word with the ĳ ligature and none of these common Dutch words: "
        f"{words}. Of these, a few are also words of a tagged language and do not count "
        f"against it: {also}. Neighbouring tagged clauses of one language, with only "
        "punctuation or a page break between them, form one span. The machine tags favour "
        "precision over recall: much Latin, German and French is left untagged, notably "
        "short phrases and terms within Dutch clauses."
    )


def _listing(items: list[str]) -> str:
    return "; ".join(items) if items else "none"


def _add(parent: etree._Element, name: str, text: str, **attributes: str) -> etree._Element:
    child = etree.SubElement(parent, tei(name), attrib=attributes)
    child.text = text
    return child
