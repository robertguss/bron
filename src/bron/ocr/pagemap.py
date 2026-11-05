"""Printed page numbers read from a scan sequence's text, and the map they give.

A running head carries the page number first (even pages) or last (odd pages); a chapter
opening carries it alone on the last line. A reading that neither of its two nearest
readings on either side agrees with, in the offset between scan and printed number, is a
misreading and is set aside. A scan between two kept readings that agree takes its number
by interpolation. A scan before the first reading takes its number from the first two
readings when they agree and the number is at least 1: a volume's first page often prints
none. Any other scan stays unresolved and is left out of the page population.
"""

import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

Method = Literal["read", "interpolated", "extrapolated", "unresolved"]

_LEADING = re.compile(r"^(\d{1,4})\s+\S")
_TRAILING = re.compile(r"\S\s+(\d{1,4})$")
_ALONE = re.compile(r"^(\d{1,4})$")


def printed_number(lines: Sequence[str]) -> int | None:
    """The page number a page's text prints in its running head or its foot, if any."""
    lines = [line.strip() for line in lines if line.strip()]
    if not lines:
        return None
    head = lines[0]
    if match := _ALONE.match(head):
        return int(match.group(1))
    letters = [c for c in head if c.isalpha()]
    capitals = bool(letters) and sum(c.isupper() for c in letters) / len(letters) >= 0.6
    if len(head) <= 90 and capitals and (match := _LEADING.match(head) or _TRAILING.search(head)):
        return int(match.group(1))
    if match := _ALONE.match(lines[-1]):
        return int(match.group(1))
    return None


@dataclass(frozen=True)
class Entry:
    """One scan of a sequence: the printed page it carries, and how that was found."""

    scan: int
    page: int | None
    method: Method


def page_map(texts: Sequence[Sequence[str]]) -> list[Entry]:
    """Each scan's printed page, from the text of every scan in order (scan numbers from 1)."""
    readings = {scan: n for scan, lines in enumerate(texts, 1) if (n := printed_number(lines))}
    order = sorted(readings)
    kept: dict[int, int] = {}
    for i, scan in enumerate(order):
        offset = scan - readings[scan]
        neighbours = order[max(0, i - 2) : i] + order[i + 1 : i + 3]
        if any(other - readings[other] == offset for other in neighbours):
            kept[scan] = readings[scan]
    entries = []
    kept_order = sorted(kept)
    for scan in range(1, len(texts) + 1):
        if scan in kept:
            entries.append(Entry(scan, kept[scan], "read"))
            continue
        before = [s for s in kept_order if s < scan]
        after = [s for s in kept_order if s > scan]
        if before and after:
            offset = before[-1] - kept[before[-1]]
            if after[0] - kept[after[0]] == offset and scan - offset >= 1:
                entries.append(Entry(scan, scan - offset, "interpolated"))
                continue
        if not before and len(after) >= 2:
            offset = after[0] - kept[after[0]]
            if after[1] - kept[after[1]] == offset and scan - offset >= 1:
                entries.append(Entry(scan, scan - offset, "extrapolated"))
                continue
        entries.append(Entry(scan, None, "unresolved"))
    return _drop_duplicates(entries)


def _drop_duplicates(entries: list[Entry]) -> list[Entry]:
    seen: dict[int, int] = {}
    for entry in entries:
        if entry.page is not None:
            seen[entry.page] = seen.get(entry.page, 0) + 1
    return [
        Entry(e.scan, None, "unresolved") if e.page is not None and seen[e.page] > 1 else e
        for e in entries
    ]


def by_page(entries: Sequence[Entry]) -> dict[int, int]:
    """Printed page to scan, for every scan whose page is known."""
    return {e.page: e.scan for e in entries if e.page is not None}
