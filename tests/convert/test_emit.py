from pathlib import Path

from lxml import etree

from bron.checks.suite import check_repository
from bron.convert.gd1.emit import assemble, convert_volume
from tests.convert.conftest import PAGE_MAP, excerpt, registry, xpath

COMMIT = "0123456789abcdef0123456789abcdef01234567"

WORK = """<?xml version="1.0" encoding="UTF-8"?>
<ti:work xmlns:ti="http://chs.harvard.edu/xmlns/cts" groupUrn="urn:cts:bron:bavinck" \
urn="urn:cts:bron:bavinck.gd" xml:lang="nl">
  <ti:title xml:lang="nl">Gereformeerde Dogmatiek</ti:title>
  <ti:edition workUrn="urn:cts:bron:bavinck.gd" urn="urn:cts:bron:bavinck.gd.ed1">
    <ti:label xml:lang="nl">Gereformeerde Dogmatiek, eerste druk</ti:label>
  </ti:edition>
</ti:work>
"""
TEXTGROUP = """<?xml version="1.0" encoding="UTF-8"?>
<ti:textgroup xmlns:ti="http://chs.harvard.edu/xmlns/cts" urn="urn:cts:bron:bavinck">
  <ti:groupname xml:lang="nl">Herman Bavinck</ti:groupname>
</ti:textgroup>
"""


def emitted(*volumes: int) -> bytes:
    converted = [convert_volume(excerpt(n), n, PAGE_MAP) for n in volumes]
    return assemble(converted, registry(), PAGE_MAP, COMMIT)


def test_the_ebook_boilerplate_is_named_only_in_the_source_description() -> None:
    tei = etree.fromstring(emitted(1, 2, 3, 4))
    for source in xpath(tei, "//tei:sourceDesc"):
        source.getparent().remove(source)
    assert b"Project Gutenberg" not in etree.tostring(tei, encoding="utf-8")
    assert "Project Gutenberg" in emitted(1).decode("utf-8")


def test_no_bidirectional_marks_survive_and_the_ij_ligature_does() -> None:
    tei = emitted(1, 2, 3, 4).decode("utf-8")
    assert "\u200e" not in tei
    assert "\u200f" not in tei
    assert "belĳdenis" in tei
    assert "belijdenis" not in tei


def test_two_conversions_of_the_same_sources_are_byte_identical() -> None:
    assert emitted(1, 2, 3, 4) == emitted(1, 2, 3, 4)


def test_the_bron_commit_is_recorded_as_the_converter_responsible() -> None:
    tei = etree.fromstring(emitted(1))
    [name] = xpath(tei, "//tei:titleStmt/tei:respStmt/tei:name[@xml:id='bron-convert']")
    assert COMMIT in "".join(name.getparent().itertext())


def test_the_header_records_how_the_machine_language_tags_were_made() -> None:
    tei = etree.fromstring(emitted(1))
    [languages] = xpath(tei, "//tei:editorialDecl/tei:p[starts-with(., 'Languages.')]")
    for setting in ("lingua-language-detector 1.4.2", "above 0.8", "more than 20 letters"):
        assert setting in languages.text


def test_the_emitted_file_passes_bron_check(tmp_path: Path) -> None:
    repo = tmp_path / "data-repo"
    work = repo / "data" / "bavinck" / "gd"
    work.mkdir(parents=True)
    (repo / "data" / "bavinck" / "__cts__.xml").write_text(TEXTGROUP, encoding="utf-8")
    (work / "__cts__.xml").write_text(WORK, encoding="utf-8")
    (work / "bavinck.gd.ed1.xml").write_bytes(emitted(1))
    findings, _ = check_repository(repo)
    assert [f.render(repo) for f in findings] == []
