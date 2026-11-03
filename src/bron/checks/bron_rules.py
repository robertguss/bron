"""Bron's own structural rules for TEI files, on top of the TEI schema."""

import re
from collections.abc import Iterator
from pathlib import Path

from lxml import etree

from bron.checks import Context
from bron.findings import Finding
from bron.tei import NSMAP, XML_LANG, tei, xml_ids

# Attributes whose values are pointers; a `#id` token among them must resolve in the file.
POINTER_ATTRIBUTES = (
    "ana",
    "corresp",
    "end",
    "hand",
    "next",
    "prev",
    "ref",
    "resp",
    "sameAs",
    "source",
    "start",
    "synch",
    "target",
    "who",
)

SCRIPTS = {
    "Greek": (re.compile(r"[Ͱ-Ͽἀ-῿]"), {"grc", "el", "gre", "ell"}),
    "Hebrew": (re.compile(r"[֐-׿יִ-ﭏ]"), {"hbo", "he", "heb", "arc"}),
}


def check_bron_rules(context: Context) -> Iterator[Finding]:
    for path in context.tei_files():
        tree = context.tree(path)
        if tree is None:
            continue
        yield from _availability(path, tree)
        yield from _page_break_facs(path, tree)
        yield from _pointers(path, tree)
        yield from _script_languages(path, tree)


def _availability(path: Path, tree: etree._ElementTree) -> Iterator[Finding]:
    """Each file names its license status in its header (ADR 0014)."""
    statements = tree.xpath(
        "/tei:TEI/tei:teiHeader/tei:fileDesc/tei:publicationStmt/tei:availability",
        namespaces=NSMAP,
    )
    licensed = [
        a
        for a in statements
        if a.get("status") and a.xpath("tei:licence[@target]", namespaces=NSMAP)
    ]
    if not licensed:
        line = statements[0].sourceline if statements else tree.getroot().sourceline
        yield Finding(
            path,
            line,
            "availability",
            "publicationStmt needs an <availability> with @status and a <licence target>",
        )


def _page_break_facs(path: Path, tree: etree._ElementTree) -> Iterator[Finding]:
    for page_break in tree.xpath("/tei:TEI/tei:text/tei:body//tei:pb", namespaces=NSMAP):
        if not page_break.get("facs"):
            yield Finding(
                path,
                page_break.sourceline,
                "pb-facs",
                f"page break n={page_break.get('n')!r} has no facs link to its scan",
            )


def _pointers(path: Path, tree: etree._ElementTree) -> Iterator[Finding]:
    ids = xml_ids(tree)
    for element in tree.iter():
        if not isinstance(element.tag, str):
            continue
        for attribute in POINTER_ATTRIBUTES:
            for token in element.get(attribute, "").split():
                if token.startswith("#") and token[1:] not in ids:
                    yield Finding(
                        path,
                        element.sourceline,
                        "id-ref",
                        f"@{attribute} points at {token}, which no xml:id in this file names",
                    )


def _primary_subtag(language: str | None) -> str | None:
    return language.split("-")[0].lower() if language else None


def _script_languages(path: Path, tree: etree._ElementTree) -> Iterator[Finding]:
    """Greek and Hebrew characters in the text sit inside a matching xml:lang span."""
    for text in tree.getroot().iterfind(tei("text")):
        yield from _scan(path, text, _primary_subtag(text.get(XML_LANG)))


def _scan(path: Path, element: etree._Element, inherited: str | None) -> Iterator[Finding]:
    language = _primary_subtag(element.get(XML_LANG)) or inherited
    yield from _check_run(path, element.sourceline, element.text, language)
    for child in element:
        if isinstance(child.tag, str):
            yield from _scan(path, child, language)
        # A child's tail is text of this element, in this element's language.
        yield from _check_run(path, child.sourceline, child.tail, language)


def _check_run(
    path: Path, line: int | None, text: str | None, language: str | None
) -> Iterator[Finding]:
    if not text or text.isascii():
        return
    for script, (characters, languages) in SCRIPTS.items():
        found = characters.search(text)
        if found and language not in languages:
            word = text[max(0, found.start() - 10) : found.end() + 10].strip()
            yield Finding(
                path,
                line,
                "script-lang",
                f"{script} text {word!r} is not inside an xml:lang span for {script}",
            )
