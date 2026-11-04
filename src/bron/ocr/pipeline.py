"""The steps `bron ocr` runs: fetch the sources, draw the sample, fetch the sampled pages.

Each step reads only what the earlier ones cached or recorded, so a step can be rerun on
its own. Nothing here writes to a repository; the manifest is written where it is told.
"""

import datetime
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from bron.ocr import OcrError, delpher, sample, sources
from bron.ocr.download import Downloader
from bron.ocr.manifest import Manifest
from bron.ocr.pagemap import Entry, by_page, page_map


@dataclass(frozen=True)
class Volume:
    """One volume of the second printing, read from its cached DIDL and PDF."""

    number: int
    identifier: str
    scans: tuple[delpher.Scan, ...]
    texts: tuple[tuple[str, ...], ...]
    entries: tuple[Entry, ...]
    pdf: Path

    @property
    def pages(self) -> dict[int, int]:
        return by_page(self.entries)


def fetch_sources(registry: Mapping[str, Mapping[str, Any]], downloader: Downloader) -> None:
    """Cache every volume's DIDL and PDF from Delpher, and every theologienet PDF."""
    for number in sources.VOLUMES:
        identifier = str(sources.record(registry, number, "delpher")["holder_id"])
        sources.didl(downloader, identifier)
        sources.volume_pdf(downloader, identifier)
    for number in sources.VOLUMES:
        sources.theologienet_pdf(downloader, sources.record(registry, number, "theologienet"))


def read_volume(
    registry: Mapping[str, Mapping[str, Any]], downloader: Downloader, number: int
) -> Volume:
    identifier = str(sources.record(registry, number, "delpher")["holder_id"])
    scans = delpher.parse_didl(sources.didl(downloader, identifier).read_bytes())
    pdf = sources.volume_pdf(downloader, identifier)
    texts = delpher.pdf_page_texts(pdf)
    if len(texts) != len(scans):
        raise OcrError(f"vol. {number}: the PDF has {len(texts)} pages, the DIDL {len(scans)}")
    entries = page_map(texts)
    return Volume(
        number, identifier, tuple(scans), tuple(tuple(t) for t in texts), tuple(entries), pdf
    )


def load_judgments(path: Path | None) -> tuple[dict[sample.Page, sample.Judgment], list[dict]]:
    if path is None or not path.is_file():
        return {}, []
    rows = yaml.safe_load(path.read_text(encoding="utf-8")) or []
    judgments = {
        (int(row["volume"]), int(row["page"])): sample.Judgment(
            bool(row["greek"]), bool(row["hebrew"])
        )
        for row in rows
    }
    return judgments, rows


def draw(
    volumes: Mapping[int, Volume], commit: str, judgments: Mapping[sample.Page, sample.Judgment]
) -> sample.Draw | sample.NeedJudgments:
    population = {n: sorted(v.pages) for n, v in volumes.items()}
    return sample.select(
        sample.orders(sample.seed_from_commit(commit), population, slice_population(volumes)),
        judgments,
    )


def slice_population(volumes: Mapping[int, Volume]) -> list[int]:
    """The printed pages of vol. 2 the slice is drawn from."""
    v = volumes[sample.SLICE_VOLUME]
    scan_to_page = {scan: page for page, scan in v.pages.items()}
    return sample.slice_pages(v.texts, scan_to_page)


def contact_sheets(
    volumes: Mapping[int, Volume], pages: Sequence[sample.Page], out: Path
) -> list[Path]:
    """Render each page from its volume PDF, two to a sheet, labelled, for judging scripts."""
    import pypdfium2 as pdfium
    from PIL import Image, ImageDraw

    out.mkdir(parents=True, exist_ok=True)
    renders = []
    for volume, page in pages:
        v = volumes[volume]
        pdf = pdfium.PdfDocument(v.pdf)
        try:
            p = pdf[v.pages[page] - 1]
            renders.append((f"vol. {volume} p. {page}", p.render(scale=2.1).to_pil()))
        finally:
            pdf.close()
    sheets = []
    for i in range(0, len(renders), 2):
        pair = renders[i : i + 2]
        width = sum(img.width for _, img in pair) + 20 * len(pair)
        height = max(img.height for _, img in pair) + 40
        sheet = Image.new("RGB", (width, height), "white")
        draw_ = ImageDraw.Draw(sheet)
        x = 0
        for label, img in pair:
            sheet.paste(img, (x, 40))
            draw_.text((x + 10, 10), label, fill="red")
            x += img.width + 20
        path = out / f"sheet-{i // 2 + 1:02d}.png"
        sheet.save(path)
        sheets.append(path)
    return sheets


def write_sample(
    manifest: Manifest,
    volumes: Mapping[int, Volume],
    commit: str,
    result: sample.Draw,
    judgment_rows: Sequence[dict],
) -> None:
    slice_ = sorted(slice_population(volumes))
    population = {}
    for n, v in sorted(volumes.items()):
        pages = sorted(v.pages)
        population[n] = {
            "delpher": v.identifier,
            "scans": len(v.scans),
            "pages": len(pages),
            "first_page": pages[0],
            "last_page": pages[-1],
            "unresolved_scans": [e.scan for e in v.entries if e.page is None],
        }
    used = {}
    for n in sample.OTHER_VOLUMES:
        judged = [p for (vol, p) in ((r["volume"], r["page"]) for r in judgment_rows) if vol == n]
        deepest = max(
            [
                result.orders[n].index(p)
                for p in [*judged, *result.picks[n]]
                if p in result.orders[n]
            ],
            default=1,
        )
        used[n] = result.orders[n][: deepest + 1]
    manifest.data.update(
        {
            "drawn_on": datetime.date.today().isoformat(),
            "seed": {
                "bron_data_commit": commit,
                "value": str(result.seed),
                "algorithm": sample.ALGORITHM,
            },
            "population": population,
            "slice": {
                "volume": sample.SLICE_VOLUME,
                "drawn_from": "the page with Par. 23's heading to the page before Par. 26 begins",
                "first_page": slice_[0],
                "last_page": slice_[-1],
                "pages": result.slice,
            },
            "orders": {
                n: {"first": used[n], "note": "the rest of each order follows from the seed"}
                for n in sample.OTHER_VOLUMES
            },
            "screening": list(judgment_rows),
            "replacements": result.replacements,
            "missing_scripts": result.missing_scripts,
            "pages": [{"id": page_id(v, p), "volume": v, "page": p} for v, p in result.pages()],
        }
    )


def page_id(volume: int, page: int) -> str:
    return f"v{volume}-p{page:03d}"


def fetch_pages(
    manifest: Manifest, volumes: Mapping[int, Volume], downloader: Downloader, cache: Path
) -> None:
    """Fetch each sampled page's image and ALTO, check their sizes, record them."""
    for entry in manifest.data["pages"]:
        v = volumes[entry["volume"]]
        scan = v.scans[v.pages[entry["page"]] - 1]
        image = sources.scan_image(downloader, scan)
        alto = sources.scan_alto(downloader, scan)
        size = delpher.jp2_size(image.read_bytes())
        alto_size = delpher.alto_page_size(alto.read_bytes())
        entry["print2"] = {
            "scan": scan.seq,
            "identifier": scan.identifier,
            "image": {
                "url": scan.image_url,
                "file": manifest.record_source(cache, image),
                "size": list(size),
            },
            "alto": {
                "url": scan.alto_url,
                "file": manifest.record_source(cache, alto),
                "page_size": list(alto_size),
            },
            "alto_scale": delpher.alto_scale(size, alto_size),
        }
    for v in volumes.values():
        manifest.record_source(cache, v.pdf)
        didl = cache / "delpher" / f"{sources.key(v.identifier)}-didl" / "didl.xml"
        manifest.record_source(cache, didl)


def locate_spans(
    manifest: Manifest,
    registry: Mapping[str, Mapping[str, Any]],
    downloader: Downloader,
    cache: Path,
    volumes: Mapping[int, Volume],
    renders: Path | None,
) -> list[str]:
    """Find each sampled page's words in the fourth printing; return what needs a look."""
    from bron.ocr import pdfsource, spans
    from bron.ocr.delpher import alto_lines

    problems = []
    haystacks = {}
    for number in sorted({entry["volume"] for entry in manifest.data["pages"]}):
        pdf = sources.theologienet_pdf(downloader, sources.record(registry, number, "theologienet"))
        read = pdfsource.read_volume(pdf)
        haystack = spans.Haystack.build(read)
        last4 = max(p for p in haystack.pages if p is not None)
        ratio = last4 / max(volumes[number].pages)
        haystacks[number] = (pdf, read, haystack, ratio)
    for entry in manifest.data["pages"]:
        pdf, read, haystack, ratio = haystacks[entry["volume"]]
        lines = alto_lines((cache / entry["print2"]["alto"]["file"]).read_bytes())
        found = spans.locate(lines, entry["page"], ratio, haystack)
        halves = []
        for page in found["covering_pages"] or []:
            index = haystack.pages.index(page)
            half = read.halves[index]
            halves.append(
                {
                    "page": page,
                    "spread": half.spread,
                    "side": half.side,
                    "gutter": read.gutters[half.spread],
                }
            )
        entry["print4"] = {"pdf": manifest.record_source(cache, pdf), **found, "halves": halves}
        for which in ("opening", "closing"):
            hit = found[which]
            if hit["page"] is None or hit["ambiguous"]:
                problems.append(f"{entry['id']}: the {which} words were not found unambiguously")
        if found["covering_pages"] is None:
            problems.append(f"{entry['id']}: no covering pages; locate this span by hand")
        if renders is not None:
            _render_span(entry, cache, pdf, halves, renders)
    return problems


def _render_span(entry: dict, cache: Path, pdf: Path, halves: list[dict], out: Path) -> None:
    from PIL import Image

    from bron.ocr import pdfsource

    out.mkdir(parents=True, exist_ok=True)
    with Image.open(cache / entry["print2"]["image"]["file"]) as scan:
        scan.convert("L").save(out / f"{entry['id']}-print2.png")
    for half in halves:
        image = pdfsource.render_half(pdf, half["spread"], half["side"], half["gutter"])
        image.save(out / f"{entry['id']}-print4-p{half['page']}.png")
