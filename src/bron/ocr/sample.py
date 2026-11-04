"""The seeded draw of the ten second-printing pages.

The seed is the bron-data commit that recorded the sources, read as a number, so nobody
chose it. Four pages come from Par. 23 to 25 of vol. 2, the thin slice: from the page where
the Par. 23 heading is printed to the page before the one where Par. 26 begins. Two come
from each of vols. 1, 3 and 4, the first two of each volume's seeded order. Among those
six, one page must carry at least three lines of Greek and one at least three of Hebrew,
as judged on the scan by a person or an agent. Where the six lack a script, the earliest
volume with a qualifying page gives up its second pick (or its first) to the first page in
its order that qualifies, never removing the only page that carries the other script. The
draw needs a judgment of each page it looks at, and asks for the next ones it needs.
"""

import random
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from bron.ocr import OcrError

SLICE_VOLUME = 2
SLICE_SIZE = 4
OTHER_VOLUMES = (1, 3, 4)
PICKS_PER_VOLUME = 2
SCRIPTS = ("greek", "hebrew")
# How many unjudged candidates to ask for at once while looking for a script.
ASK_AHEAD = 10

ALGORITHM = (
    "rng = random.Random(seed); slice = sorted(rng.sample(sorted(slice_pages), 4)); "
    "then for volume in (1, 3, 4): order[volume] = rng.sample(sorted(population[volume]), "
    "len(population[volume])); picks are the first two of each order, with the script "
    "replacement rule in bron.ocr.sample"
)

_HEADING = re.compile(r"^[§$S]\s*(\d{1,2})\s*\.")

Page = tuple[int, int]  # (volume, printed page)


@dataclass(frozen=True)
class Judgment:
    greek: bool
    hebrew: bool

    def has(self, script: str) -> bool:
        return getattr(self, script)


def seed_from_commit(commit: str) -> int:
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise OcrError(f"{commit!r} is not a full 40-character commit SHA")
    return int(commit, 16)


def heading_scan(texts: Sequence[Sequence[str]], number: int, after: int = 0) -> int:
    """The first scan after `after` with a line opening the paragraph `number`."""
    for scan, lines in enumerate(texts, 1):
        if scan <= after:
            continue
        if any((m := _HEADING.match(line)) and int(m.group(1)) == number for line in lines):
            return scan
    raise OcrError(f"no scan prints the heading of Par. {number}")


def slice_pages(texts: Sequence[Sequence[str]], scan_to_page: Mapping[int, int]) -> list[int]:
    """Vol. 2's printed pages from Par. 23's heading to the page before Par. 26 begins."""
    first = heading_scan(texts, 23)
    stop = heading_scan(texts, 26, after=first)
    pages = [scan_to_page[scan] for scan in range(first, stop) if scan in scan_to_page]
    if len(pages) != stop - first:
        raise OcrError("a scan inside Par. 23 to 25 has no known printed page")
    return pages


@dataclass
class Draw:
    seed: int
    slice: list[int]
    orders: dict[int, list[int]]
    picks: dict[int, list[int]] = field(default_factory=dict)
    replacements: list[dict] = field(default_factory=list)
    missing_scripts: list[str] = field(default_factory=list)

    def pages(self) -> list[Page]:
        chosen = [(SLICE_VOLUME, page) for page in self.slice]
        chosen += [(volume, page) for volume in OTHER_VOLUMES for page in self.picks[volume]]
        return sorted(chosen)


@dataclass(frozen=True)
class NeedJudgments:
    """The draw cannot finish until these pages are judged on the scan."""

    pages: tuple[Page, ...]


def orders(seed: int, population: Mapping[int, Sequence[int]], slice_: Sequence[int]) -> Draw:
    rng = random.Random(seed)
    chosen = sorted(rng.sample(sorted(slice_), SLICE_SIZE))
    ordered = {v: rng.sample(sorted(population[v]), len(population[v])) for v in OTHER_VOLUMES}
    return Draw(seed, chosen, ordered)


def select(draw: Draw, judgments: Mapping[Page, Judgment]) -> Draw | NeedJudgments:
    """Apply the picks and the script rule, or say which pages still need judging."""
    picks = {v: list(draw.orders[v][:PICKS_PER_VOLUME]) for v in OTHER_VOLUMES}
    first = [(v, p) for v in OTHER_VOLUMES for p in picks[v] if (v, p) not in judgments]
    if first:
        return NeedJudgments(tuple(first))
    replaced: set[tuple[int, int]] = set()
    replacements: list[dict] = []
    missing: list[str] = []

    def carriers(script: str) -> list[Page]:
        return [(v, p) for v in OTHER_VOLUMES for p in picks[v] if judgments[(v, p)].has(script)]

    for script in SCRIPTS:
        if carriers(script):
            continue
        other = next(s for s in SCRIPTS if s != script)
        done = False
        for volume in OTHER_VOLUMES:
            found = _first_qualifying(draw.orders[volume], volume, script, judgments)
            if isinstance(found, NeedJudgments):
                return found
            if found is None:
                continue
            for slot in (1, 0):
                current = (volume, picks[volume][slot])
                if (volume, slot) in replaced:
                    continue
                if judgments[current].has(other) and carriers(other) == [current]:
                    continue
                replacements.append(
                    {
                        "script": script,
                        "volume": volume,
                        "replaced": current[1],
                        "by": found,
                        "pick": slot + 1,
                    }
                )
                picks[volume][slot] = found
                replaced.add((volume, slot))
                done = True
                break
            if done:
                break
        if not done:
            missing.append(script)
    return Draw(draw.seed, draw.slice, draw.orders, picks, replacements, missing)


def _first_qualifying(
    order: Sequence[int], volume: int, script: str, judgments: Mapping[Page, Judgment]
) -> int | NeedJudgments | None:
    for i, page in enumerate(order):
        judgment = judgments.get((volume, page))
        if judgment is None:
            ahead = [(volume, p) for p in order[i:] if (volume, p) not in judgments]
            return NeedJudgments(tuple(ahead[:ASK_AHEAD]))
        if judgment.has(script):
            return page
    return None
