"""The same words in the fourth printing: where each sampled page's text was reprinted.

A sampled page's body (its lines in the body type, below the running head) gives an
opening and a closing run of words, and each of its footnotes gives its own opening words.
Each run is looked for, by fuzzy match, in the theologienet text layer of the same volume,
within a window around the page the proportion of the two printings predicts. A run found
twice about equally well is ambiguous and reported, never guessed. The pages the runs land
on are the span's covering pages; an agent then checks each span on the rendered scans.
"""

import re
import unicodedata
from bisect import bisect_right
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass

from bron.ocr import OcrError
from bron.ocr.delpher import AltoLine
from bron.ocr.pagemap import printed_number
from bron.ocr.pdfsource import Spreads

RUN = 6  # words in an opening or closing run
MIN_SCORE = 80.0  # rapidfuzz partial-ratio a match must reach
AMBIGUITY = 3.0  # a second match within this many points makes the first ambiguous
WINDOW = 60  # printed pages either side of the predicted page searched
MAX_COVER = 3  # fourth-printing pages one second-printing page can plausibly span


@dataclass(frozen=True)
class Parts:
    head: tuple[AltoLine, ...]
    body: tuple[AltoLine, ...]
    notes: tuple[AltoLine, ...]


def parts(lines: Sequence[AltoLine], page: int | None = None) -> Parts:
    """A page's running head, its body (the most used type size) and its notes (smaller
    type, below the body). The head is the top row, when a page number can be read from it
    or it carries `page`, the page's own number, among its digits (OCR often adds a stray
    mark to the number, as in `■556`)."""
    if not lines:
        raise OcrError("the ALTO page has no text")
    top = min(lines, key=lambda line: line.box[1])
    row = [line for line in lines if abs(line.box[1] - top.box[1]) <= top.box[3]]
    row_text = " ".join(line.text for line in sorted(row, key=lambda line: line.box[0]))
    numbered = printed_number([row_text]) is not None
    carries_page = page is not None and str(page) in re.findall(r"\d+", row_text)
    head = row if numbered or carries_page else []
    rest = [line for line in lines if line not in head]
    weights = Counter()
    for line in rest:
        weights[line.size] += len(line.text)
    body_size = weights.most_common(1)[0][0] if weights else None
    body = [line for line in rest if line.size == body_size]
    bottom = max((line.box[1] for line in body), default=0)
    notes = [line for line in rest if line not in body and line.box[1] > bottom - 5]
    body = [line for line in rest if line not in notes]
    return Parts(tuple(head), tuple(body), tuple(notes))


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFC", text).lower()
    text = re.sub(r"[-­]\s*\n\s*", "", text)
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def words(lines: Sequence[AltoLine]) -> list[str]:
    return normalize("\n".join(line.text for line in lines)).split()


@dataclass(frozen=True)
class Hit:
    page: int
    score: float
    ambiguous: bool


@dataclass(frozen=True)
class Haystack:
    """A theologienet volume's text, half by half, with each half's printed page."""

    text: str
    starts: tuple[int, ...]
    pages: tuple[int | None, ...]

    @classmethod
    def build(cls, spreads: Spreads) -> Haystack:
        entries = spreads.page_map()
        chunks, starts, pages, offset = [], [], [], 0
        for half, entry in zip(spreads.halves, entries, strict=True):
            chunk = normalize("\n".join(half.lines)) + " "
            starts.append(offset)
            pages.append(entry.page)
            chunks.append(chunk)
            offset += len(chunk)
        return cls("".join(chunks), tuple(starts), tuple(pages))

    def page_at(self, index: int) -> int | None:
        return self.pages[bisect_right(self.starts, index) - 1]

    def window(self, predicted: float, reach: float = WINDOW) -> tuple[int, int]:
        inside = [
            i for i, p in enumerate(self.pages) if p is not None and abs(p - predicted) <= reach
        ]
        if not inside:
            raise OcrError(f"no fourth-printing page is near p. {predicted}")
        last = inside[-1] + 1
        end = self.starts[last] if last < len(self.starts) else len(self.text)
        return self.starts[inside[0]], end

    def find(self, run: Sequence[str], predicted: float, reach: float = WINDOW) -> Hit | None:
        from rapidfuzz import fuzz

        needle = " ".join(run)
        start, end = self.window(predicted, reach)
        hay = self.text[start:end]
        best = fuzz.partial_ratio_alignment(needle, hay, score_cutoff=MIN_SCORE)
        if best is None:
            return None
        masked = (
            hay[: best.dest_start] + " " * (best.dest_end - best.dest_start) + hay[best.dest_end :]
        )
        second = fuzz.partial_ratio_alignment(needle, masked, score_cutoff=MIN_SCORE)
        ambiguous = second is not None and best.score - second.score < AMBIGUITY
        page = self.page_at(start + best.dest_start)
        if page is None:
            return None
        return Hit(page, round(best.score, 1), ambiguous)


def locate(lines: Sequence[AltoLine], page: int, ratio: float, haystack: Haystack) -> dict:
    """Where a sampled page's body and footnotes are printed in the fourth printing."""
    split = parts(lines, page)
    body = words(split.body)
    if len(body) < 2 * RUN:
        raise OcrError(f"p. {page}: too little body text to locate")
    predicted = round(page * ratio)
    opening, closing = body[:RUN], body[-RUN:]
    first, last = haystack.find(opening, predicted), haystack.find(closing, predicted)
    found = {
        "predicted_page": predicted,
        "opening": {"words": " ".join(opening), **_hit(first)},
        "closing": {"words": " ".join(closing), **_hit(last)},
        "notes": [],
    }
    pages = [h.page for h in (first, last) if h is not None]
    spread = pages[1] - pages[0] + 1 if len(pages) == 2 else 0
    covering = list(range(pages[0], pages[1] + 1)) if 1 <= spread <= MAX_COVER else None
    found["covering_pages"] = covering
    for note in _notes(split.notes):
        hit = None
        if covering:
            # A note is reprinted with its body: on the covering pages or the page after.
            centre = (covering[0] + covering[-1] + 1) / 2
            hit = haystack.find(note[:RUN], centre, centre - covering[0])
        if hit is None:
            hit = haystack.find(note[:RUN], predicted)
        found["notes"].append({"words": " ".join(note[:RUN]), **_hit(hit)})
    return found


def _hit(hit: Hit | None) -> dict:
    if hit is None:
        return {"page": None, "score": None, "ambiguous": None}
    return {"page": hit.page, "score": hit.score, "ambiguous": hit.ambiguous}


# A footnote's number and bracket. OCR reads a superscript number as the digits or as any
# one mark (Delpher's ALTO has ') !) *) J) and others for 1) and 2)).
_CALLOUT = re.compile(r"^\s*(?:\d{1,2}|\S)\s*\)\s")


def _notes(lines: Sequence[AltoLine]) -> list[list[str]]:
    """Each footnote's words: a new note starts at a line opening with its number and ')'."""
    notes: list[list[str]] = []
    for line in lines:
        if _CALLOUT.match(line.text) or not notes:
            notes.append([])
        notes[-1].extend(normalize(line.text).split())
    return [note for note in notes if len(note) >= 3]
