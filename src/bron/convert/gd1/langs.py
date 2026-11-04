"""Language tags for GD¹, in three layers, each told apart from the others.

1. The transcribers' own language spans (vols. 2-4) are carried over by `html.Converter`
   as `foreign` with their code and no `resp`.
2. Every run of Greek or Hebrew script that is not already inside a span of its language is
   wrapped in `foreign` with `xml:lang` `grc` or `hbo`. The characters are those of the
   script rule `bron check` enforces, so the file passes that rule by construction.
3. Latin, German and French outside any language span are proposed by statistical language
   identification over clauses: the text between punctuation, quotation marks, parentheses
   and elements that are not plain text, and the text of each highlighted (mostly italic)
   phrase. A clause is tagged only when the identifier is confident it is one of those
   three languages, it is long enough to judge, and it holds no common Dutch word and no
   word with the Dutch ĳ ligature. Neighbouring clauses tagged with the same language form
   one span. So a Dutch clause with a Latin term in it stays untagged, as does a short
   phrase, at the cost of leaving some foreign text untagged.

Tags of the second and third layers carry `resp="#bron-langid"`. A span only ever wraps a
stretch of one element's own content, so it never crosses an element boundary; page breaks,
corrections, highlighting and abbreviations inside that stretch move into the span whole.
"""

import re
import unicodedata
from collections import Counter
from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field
from functools import cache

from lingua import Language, LanguageDetector, LanguageDetectorBuilder
from lxml import etree

from bron.checks.bron_rules import SCRIPTS
from bron.convert.gd1 import TAGGER
from bron.tei import XML_LANG, tei

SCRIPT_CODES = {"grc": SCRIPTS["Greek"][0], "hbo": SCRIPTS["Hebrew"][0]}

# The identifier chooses among these, so that the Dutch of the book and the English of its
# citations are recognized as such rather than forced into one of the tagged languages. Its
# language models ship inside the package, so the package version is the model version.
LIBRARY = "lingua-language-detector"
LANGUAGES = (Language.DUTCH, Language.ENGLISH, Language.LATIN, Language.GERMAN, Language.FRENCH)
TAGGED = {Language.LATIN: "la", Language.GERMAN: "de", Language.FRENCH: "fr"}
# The identified language's confidence must exceed this. The identifier's confidences differ
# in their last digits between processes, as Python seeds string hashing per process; a
# threshold above one half leaves no near tie for the top language that could flip.
THRESHOLD = 0.8
FLOOR = 20  # and the clause must have more letters than this
# Common Dutch words, which show that a clause is Dutch around a foreign term. A few are
# also words of a tagged language, and count only against the others.
# fmt: off
DUTCH_WORDS = frozenset({
    "aan", "alleen", "als", "dan", "daar", "dat", "den", "der", "deze", "dezen", "die", "dit",
    "door", "dus", "een", "eene", "en", "enz", "er", "geen", "had", "heeft", "hebben", "het",
    "hier", "hun", "is", "kan", "maar", "men", "met", "moet", "naar", "niet", "nog", "of", "om",
    "onder", "ook", "op", "over", "reeds", "ten", "ter", "tegen", "toch", "tot", "tusschen", "uit",
    "van", "voor", "waar", "want", "wat", "wel", "welke", "werd", "wordt", "worden", "zal", "zich",
    "zoo",
})
# fmt: on
ALSO = {
    "als": "de",
    "den": "de",
    "der": "de",
    "die": "de la",
    "en": "fr",
    "er": "de",
    "hier": "de fr",
}
WORD = re.compile(r"[^\W\d_]+")

DELIMITERS = frozenset(',;:.!?()[]„“”"«»—')
# Elements a span may hold whole: milestones, corrections, highlighting, abbreviations.
INLINE = frozenset(tei(name) for name in ("pb", "lb", "choice", "sic", "corr", "hi", "abbr"))
# Of those, the ones that are only ever read as part of the clause around them; italic and
# other highlighting is also a clause of its own.
PART_OF_A_CLAUSE = INLINE - {tei("hi")}
FOREIGN = tei("foreign")


@dataclass
class Tags:
    """The language tags of one volume, by layer and language."""

    carried: Counter[str] = field(default_factory=Counter)  # the transcribers' own
    script: Counter[str] = field(default_factory=Counter)
    statistical: Counter[str] = field(default_factory=Counter)


def tag(nodes: Sequence[etree._Element], language: str = "nl") -> Tags:
    """Add the script and statistical language tags to `nodes`, which are in `language`."""
    tags = Tags()
    for node in nodes:
        tags.carried.update(span.get(XML_LANG, "") for span in node.iter(FOREIGN))
    for node in nodes:
        _scripts(node, language, tags)
    for node in nodes:
        _statistical(node, language, tags)
    return tags


# Positions in an element's own content are (segment, offset): segment 0 is the element's
# text and segment k + 1 the tail of its child k, so child k sits between segments k and k + 1.
Position = tuple[int, int]


def _segments(element: etree._Element) -> list[str]:
    return [element.text or ""] + [child.tail or "" for child in element]


def _wrap(element: etree._Element, start: Position, end: Position, language: str) -> None:
    """Wrap the stretch of `element`'s content from `start` to `end` in a machine tag."""
    (first, offset), (last, end_offset) = start, end
    segments = _segments(element)
    span = etree.Element(FOREIGN)
    span.set(XML_LANG, language)
    span.set("resp", TAGGER)
    moved = list(element[first:last])
    if moved:
        span.text = segments[first][offset:] or None
        span.extend(moved)  # each child moves with its tail
        moved[-1].tail = segments[last][:end_offset] or None
    else:
        span.text = segments[first][offset:end_offset] or None
    span.tail = segments[last][end_offset:] or None
    before = segments[first][:offset] or None
    if first == 0:
        element.text = before
    else:
        element[first - 1].tail = before
    element.insert(first, span)


def _language(element: etree._Element, inherited: str) -> str:
    return element.get(XML_LANG) or inherited


def _is_neutral(character: str) -> bool:
    return character.isspace() or unicodedata.category(character).startswith("P")


def _scripts(element: etree._Element, inherited: str, tags: Tags) -> None:
    language = _language(element, inherited)
    for code, characters in SCRIPT_CODES.items():
        if language != code:
            for start, end in reversed(list(_script_runs(element, characters))):
                _wrap(element, start, end, code)
                tags.script[code] += 1
    for child in element:
        if isinstance(child.tag, str):
            _scripts(child, language, tags)


def _script_runs(
    element: etree._Element, characters: re.Pattern[str]
) -> Iterator[tuple[Position, Position]]:
    """Each stretch of the script in `element`'s own content, from its first character to its
    last. Spaces, punctuation and combining marks inside a stretch do not end it, nor do
    children holding nothing but the script, punctuation or no text at all."""
    start: Position | None = None
    end: Position = (0, 0)
    for index, text in enumerate(_segments(element)):
        for offset, character in enumerate(text):
            if characters.match(character) or (
                start is not None and unicodedata.category(character).startswith("M")
            ):
                start = start or (index, offset)
                end = (index, offset + 1)
            elif not _is_neutral(character):
                if start is not None:
                    yield start, end
                start = None
        if index == len(element):
            break
        child = element[index]
        kind = _script_kind(child, characters)
        if kind == "script":
            start = start or (index, len(text))
            end = (index + 1, 0)
        elif kind == "other" and start is not None:
            yield start, end
            start = None
    if start is not None:
        yield start, end


def _script_kind(child: etree._Element, characters: re.Pattern[str]) -> str:
    """Whether a child can sit inside a stretch of the script: "script" if it holds the
    script, "neutral" if it holds no letters, "other" otherwise."""
    if not _plain(child):
        return "other"
    text = "".join(child.itertext())
    if any(not characters.match(c) and not _is_neutral(c) for c in text):
        return "other"
    return "script" if any(characters.match(c) for c in text) else "neutral"


@dataclass
class Clause:
    start: Position
    end: Position
    text: str


def _statistical(element: etree._Element, inherited: str, tags: Tags) -> None:
    language = _language(element, inherited)
    if language != "nl" or element.tag in PART_OF_A_CLAUSE:
        return
    spans: list[tuple[Position, Position, str]] = []
    for clause in _clauses(element):
        code = _identify(clause.text)
        if code is None:
            spans.append((clause.start, clause.end, ""))
        elif spans and spans[-1][2] == code and _joined(element, spans[-1][1], clause.start):
            spans[-1] = (spans[-1][0], clause.end, code)
        else:
            spans.append((clause.start, clause.end, code))
    for start, end, code in reversed(spans):
        if code:
            _wrap(element, start, end, code)
            tags.statistical[code] += 1
    for child in element:
        if isinstance(child.tag, str):
            _statistical(child, language, tags)


def _clauses(element: etree._Element) -> Iterator[Clause]:
    """The clauses of `element`'s own content, each trimmed of surrounding spaces."""
    start: Position | None = None
    end: Position = (0, 0)
    text: list[str] = []
    for index, segment in enumerate(_segments(element)):
        for offset, character in enumerate(segment):
            if character in DELIMITERS:
                if start is not None:
                    yield Clause(start, end, "".join(text).strip())
                start, text = None, []
            elif character.isspace():
                text.append(" ")
            else:
                start = start or (index, offset)
                end = (index, offset + 1)
                text.append(character)
        if index == len(element):
            break
        child = element[index]
        if _plain(child):
            if child.tag in (tei("pb"), tei("lb")):
                text.append(" ")
            elif "".join(child.itertext()).strip():
                start = start or (index, len(segment))
                end = (index + 1, 0)
                text.append(_reading(child))
        else:
            if start is not None:
                yield Clause(start, end, "".join(text).strip())
            start, text = None, []
    if start is not None:
        yield Clause(start, end, "".join(text).strip())


def _plain(child: etree._Element) -> bool:
    """Whether a child is plain text a clause can run through, and a span can hold whole."""
    return (
        isinstance(child.tag, str)
        and child.tag in INLINE
        and all(node.tag in INLINE for node in child.iterdescendants())
    )


def _reading(element: etree._Element) -> str:
    """An element's text as read: a correction reads as corrected, not as printed."""
    parts = [element.text or ""]
    for child in element:
        if child.tag != tei("sic"):
            parts.append(_reading(child))
        parts.append(child.tail or "")
    return "".join(parts)


def _joined(element: etree._Element, end: Position, start: Position) -> bool:
    """Whether only punctuation, spaces and page or line breaks lie between two positions
    in `element`."""
    (first, offset), (last, start_offset) = end, start
    segments = _segments(element)
    if first == last:
        between = segments[first][offset:start_offset]
    else:
        between = segments[first][offset:] + "".join(segments[first + 1 : last])
        between += segments[last][:start_offset]
        if any(child.tag not in (tei("pb"), tei("lb")) for child in element[first:last]):
            return False
    return all(_is_neutral(character) for character in between)


@cache
def _detector() -> LanguageDetector:
    return LanguageDetectorBuilder.from_languages(*LANGUAGES).build()


def _identify(text: str) -> str | None:
    """The code of the language `text` is in, if it is one tagged and the identifier is
    sure enough of it; None otherwise."""
    if sum(character.isalpha() for character in text) <= FLOOR:
        return None
    words = WORD.findall(text.lower())
    # Words that rule a clause out whatever the identifier says are checked before it runs.
    if any("ĳ" in word or (word in DUTCH_WORDS and word not in ALSO) for word in words):
        return None
    # The identifier's Dutch models spell ij as two letters, as the ligature is rarely used.
    best = _detector().compute_language_confidence_values(text.replace("ĳ", "ij"))[0]
    if best.language not in TAGGED or best.value <= THRESHOLD:
        return None
    code = TAGGED[best.language]
    if any(word in DUTCH_WORDS and code not in ALSO.get(word, "").split() for word in words):
        return None
    return code
