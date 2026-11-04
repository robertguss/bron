"""The GD¹ page map: the page of each DBNL scan PDF that every printed page of GD¹ is on.

Every page break in the GD¹ TEI links to that page of DBNL's PDF of its volume. The PDF
page is measured, never computed from an offset. Each PDF's OCR text layer prints the
page number as its first line, or as its last line on a chapter opening, so a page whose
number is readable there is matched. A match that none of the two nearest matches on each
side agrees with is a misreading and is set aside. A page between two matches that agree
takes its PDF page by interpolation. Any other page stays unresolved until someone looks at
the rendered scan and records a review. A review that contradicts the measurement is a
conflict, never silently preferred: the map is complete only with no conflicts and no
unresolved pages.

Run `bron convert gd1-page-map` to re-measure. It rewrites `data/page-map.yaml` and keeps
the file's hand-kept sections (reviews, numbering findings, printed headings) as they are.
"""

import itertools
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import yaml

from bron.convert.gd1 import source_record
from bron.convert.gd1.fetch import content_sha256

MAP = Path(__file__).parent / "data" / "page-map.yaml"

# Sections of the map file written by hand and carried over unchanged by a re-measure.
KEPT_SECTIONS = ("reviews", "numbering", "headings")


@dataclass(frozen=True)
class Volume:
    """A volume's printed page sequence: roman front-matter pages, then 1…last_page."""

    number: int
    roman: tuple[str, ...]
    last_page: int

    @property
    def sequences(self) -> tuple[tuple[str, ...], ...]:
        arabic = tuple(str(page) for page in range(1, self.last_page + 1))
        return (self.roman, arabic) if self.roman else (arabic,)

    @property
    def labels(self) -> tuple[str, ...]:
        return tuple(label for sequence in self.sequences for label in sequence)


# Vol. 1 numbers its Voorbericht and Inhoud in roman, III to VII (VIII is blank). Vols. 2
# to 4 have no numbered front matter. The last page of each volume is read from its scan.
VOLUMES = {
    1: Volume(1, ("III", "IV", "V", "VI", "VII"), 532),
    2: Volume(2, (), 571),
    3: Volume(3, (), 572),
    4: Volume(4, (), 590),
}


@dataclass(frozen=True)
class Review:
    """A page whose PDF page someone confirmed by looking at the rendered scan."""

    volume: int
    n: str
    pdf: int
    note: str


Method = Literal["ocr", "interpolated", "visually verified", "unresolved"]


@dataclass(frozen=True)
class Entry:
    n: str
    pdf: int | None
    method: Method
    evidence: str = ""
    note: str = ""


@dataclass
class Measurement:
    volumes: dict[int, list[Entry]] = field(default_factory=dict)
    # (volume, PDF page, the number read there) for each misreading set aside.
    outliers: list[tuple[int, int, str]] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    interpolated: list[tuple[int, str]] = field(default_factory=list)
    unresolved: list[tuple[int, str]] = field(default_factory=list)

    @property
    def complete(self) -> bool:
        return not self.conflicts and not self.unresolved


class HashMismatch(Exception):
    pass


_ARABIC = re.compile(r"\d{1,3}")
# A roman page number beside a running head in capitals: "IV VOORBERICHT.", "INHOUD.\tVII".
_ROMAN_HEAD = re.compile(r"([IVXLC]+)\s+[A-Z][A-Z. ]*|[A-Z][A-Z. ]*?\s+([IVXLC]+)")


def printed_number(lines: Sequence[str], *, roman: bool) -> tuple[str, str] | None:
    """The page number printed on a page and where it was read: header, else footer."""
    if not lines:
        return None
    header = lines[0].strip()
    if _ARABIC.fullmatch(header):
        return str(int(header)), "header"
    if roman and (match := _ROMAN_HEAD.fullmatch(header)):
        return match.group(1) or match.group(2), "header"
    footer = lines[-1].strip()
    if len(lines) > 1 and _ARABIC.fullmatch(footer):
        return str(int(footer)), "footer"
    return None


def measure(
    pdfs: Mapping[int, Sequence[Sequence[str]]],
    volumes: Mapping[int, Volume],
    reviews: Sequence[Review],
) -> Measurement:
    """Map every printed page of each volume from its PDF's OCR lines, page by page."""
    result = Measurement()
    for number, volume in volumes.items():
        entries = _measure_volume(volume, pdfs[number], result)
        _apply_reviews(volume, entries, [r for r in reviews if r.volume == number], result)
        result.volumes[number] = [entries[label] for label in volume.labels]
        result.interpolated += [
            (number, label) for label in volume.labels if entries[label].method == "interpolated"
        ]
        result.unresolved += [
            (number, label) for label in volume.labels if entries[label].method == "unresolved"
        ]
    return result


def _measure_volume(
    volume: Volume, pages: Sequence[Sequence[str]], result: Measurement
) -> dict[str, Entry]:
    entries: dict[str, Entry] = {}
    for sequence in volume.sequences:
        position = {label: index for index, label in enumerate(sequence)}
        matches = []  # (PDF page, label, where), in PDF order
        for index, lines in enumerate(pages, start=1):
            read = printed_number(lines, roman=bool(volume.roman))
            if read and read[0] in position:
                matches.append((index, *read))
        offsets = [pdf - position[label] for pdf, label, _ in matches]
        kept = []
        for k, (pdf, label, where) in enumerate(matches):
            neighbours = offsets[max(k - 2, 0) : k] + offsets[k + 1 : k + 3]
            if offsets[k] in neighbours:
                kept.append((pdf, label, where, offsets[k]))
            else:
                result.outliers.append((volume.number, pdf, label))
        for (pdf_a, label_a, _, off_a), (pdf_b, label_b, _, off_b) in itertools.pairwise(kept):
            if off_a != off_b:
                result.conflicts.append(
                    f"vol. {volume.number}: printed {label_a} is on PDF page {pdf_a} and printed "
                    f"{label_b} on PDF page {pdf_b}, which their numbering does not allow"
                )
        by_label = {label: (pdf, where) for pdf, label, where, _ in kept}
        for label, index in position.items():
            if label in by_label:
                pdf, where = by_label[label]
                entries[label] = Entry(label, pdf, "ocr", f"{where} '{label}'")
                continue
            before = [off for pdf, lab, _, off in kept if position[lab] < index][-1:]
            after = [off for pdf, lab, _, off in kept if position[lab] > index][:1]
            if before and after and before == after:
                entries[label] = Entry(label, index + before[0], "interpolated")
            else:
                entries[label] = Entry(label, None, "unresolved")
    return entries


def _apply_reviews(
    volume: Volume, entries: dict[str, Entry], reviews: Sequence[Review], result: Measurement
) -> None:
    for review in reviews:
        entry = entries.get(review.n)
        if entry is None:
            result.conflicts.append(
                f"vol. {volume.number}: review of page {review.n}: no such page"
            )
            continue
        if entry.pdf is not None and entry.pdf != review.pdf:
            result.conflicts.append(
                f"vol. {volume.number}: page {review.n} was reviewed on PDF page {review.pdf} "
                f"but measured ({entry.method}) on PDF page {entry.pdf}"
            )
            continue
        entries[review.n] = Entry(
            review.n, review.pdf, "visually verified", entry.evidence, review.note
        )


def verified_pdf(path: Path, sha256: str) -> Path:
    """The PDF, once its content hash is the one the registry records."""
    digest = content_sha256(path.read_bytes())
    if digest != sha256:
        raise HashMismatch(f"{path}: SHA-256 is {digest}, the registry records {sha256}")
    return path


def pdf_lines(path: Path) -> list[list[str]]:
    """The non-empty OCR text lines of every page of a PDF, in page order."""
    import pypdfium2

    document = pypdfium2.PdfDocument(path)
    try:
        pages = []
        for page in document:
            text = page.get_textpage().get_text_range()
            pages.append([line.strip() for line in text.splitlines() if line.strip()])
        return pages
    finally:
        document.close()


def load_map(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) if path.is_file() else {}


def reviews_of(page_map: Mapping[str, Any]) -> list[Review]:
    return [
        Review(int(item["volume"]), str(item["n"]), int(item["pdf"]), str(item["note"]))
        for item in page_map.get("reviews") or []
    ]


def render(
    result: Measurement, sources: Mapping[int, Mapping[str, Any]], kept: Mapping[str, Any]
) -> str:
    """The map file: generated page lists, then the hand-kept sections unchanged."""
    lines = [
        "# GD¹ page map: the DBNL scan PDF page each printed page is on.",
        "# Generated by `bron convert gd1-page-map` from the PDFs' OCR text layer; method is",
        "# ocr (number read in the page's header or footer line), interpolated (between two",
        "# agreeing OCR matches), or visually verified (an entry under `reviews`).",
        "# `reviews`, `numbering` and `headings` are kept by hand and carried over on re-runs.",
        "volumes:",
    ]
    for number, entries in result.volumes.items():
        source = sources[number]
        lines += [
            f"  - volume: {number}",
            f"    pdf: {source['url']}",
            f"    sha256: {source['sha256']}",
        ]
        outliers = [(pdf, label) for vol, pdf, label in result.outliers if vol == number]
        if outliers:
            lines.append("    outliers:")
            lines += [f"      - {{pdf: {pdf}, read: '{label}'}}" for pdf, label in outliers]
        else:
            lines.append("    outliers: []")
        lines.append("    pages:")
        for entry in entries:
            pdf = "null" if entry.pdf is None else str(entry.pdf)
            lines.append(f"      - {{n: '{entry.n}', pdf: {pdf}, method: {entry.method}}}")
    body = "\n".join(lines) + "\n"
    rest = {key: kept[key] for key in KEPT_SECTIONS if key in kept}
    if rest:
        body += yaml.safe_dump(rest, allow_unicode=True, sort_keys=False, width=100)
    return body


def remeasure(registry_path: Path, cache: Path, map_path: Path) -> Measurement:
    """Measure every volume from the cached PDFs and rewrite the map file."""
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    kept = load_map(map_path)
    sources = {number: source_record(registry, number, "dbnl") for number in VOLUMES}
    pdfs = {}
    for number, source in sources.items():
        path = cache / Path(source["url"]).name
        if not path.is_file():
            raise FileNotFoundError(f"{path}: not cached; download it from {source['url']}")
        pdfs[number] = pdf_lines(verified_pdf(path, source["sha256"]))
    result = measure(pdfs, VOLUMES, reviews_of(kept))
    map_path.write_text(render(result, sources, kept), encoding="utf-8")
    return result
