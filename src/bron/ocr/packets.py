"""The reader's packets: what the Dutch reader receives, as plain files.

Round 1 holds, for each sampled page, the scan as a PNG at its own size and a text file
pre-filled with Delpher's OCR, one printed line per text line, in reading order. The page's
running head is tagged `@head` for the reader to confirm; footnote lines are left for the
reader to tag `@note`. Each text file opens with a `#` line naming its page, so a renamed
file is still matched. The packet also holds the transcription rules, a minutes file and a
manifest of every file's SHA-256, so what comes back can be matched to what went out.
"""

from collections.abc import Sequence
from pathlib import Path

import yaml

from bron.ocr import OcrError
from bron.ocr.delpher import AltoLine, alto_lines, open_scan
from bron.ocr.download import sha256
from bron.ocr.manifest import Manifest
from bron.ocr.spans import parts

HEAD = "@head"
NOTE = "@note"


def prefill(page_id: str, label: str, page: int, lines: Sequence[AltoLine]) -> str:
    """A page's text file: its `#` header, the running head tagged, then every line."""
    split = parts(lines, page)
    out = [f"# {page_id}: {label}"]
    if split.head:
        row = sorted(split.head, key=lambda line: line.box[0])
        out.append(f"{HEAD} " + " ".join(line.text for line in row))
    out.extend(line.text for line in lines if line not in split.head)
    return "\n".join(out) + "\n"


def round1(manifest: Manifest, cache: Path, rules: Path, out: Path) -> list[Path]:
    """Write the round-1 packet into `out`, which must not exist yet or be empty.

    Every sampled page's scan and ALTO are looked for before anything is written, so a packet
    asked for too early leaves `out` as it was and can simply be asked for again.
    """
    if out.exists() and any(out.iterdir()):
        raise OcrError(f"{out} is not empty")
    for entry in manifest.data["pages"]:
        print2 = entry.get("print2")
        if print2 is None:
            raise OcrError(f"{entry['id']}: fetch the sampled pages first")
        for kind in ("alto", "image"):
            if not (cache / print2[kind]["file"]).is_file():
                raise OcrError(f"{entry['id']}: its {kind} is not in the cache; fetch it first")
    pages = out / "pages"
    pages.mkdir(parents=True, exist_ok=True)
    written = []
    minutes = []
    for entry in manifest.data["pages"]:
        print2 = entry["print2"]
        label = f"vol. {entry['volume']}, p. {entry['page']} (Delpher {print2['identifier']})"
        lines = alto_lines((cache / print2["alto"]["file"]).read_bytes())
        text = pages / f"{entry['id']}.gt.txt"
        text.write_text(prefill(entry["id"], label, entry["page"], lines), encoding="utf-8")
        image = pages / f"{entry['id']}.png"
        with open_scan(cache / print2["image"]["file"]) as scan:
            scan.save(image)
        written += [text, image]
        minutes.append(f"{entry['id']}: ")
    copied = out / "RULES.md"
    copied.write_text(rules.read_text(encoding="utf-8"), encoding="utf-8")
    times = out / "minutes.txt"
    times.write_text(
        "Minutes spent on each page, rounded to five, after the colon.\n"
        + "\n".join(minutes)
        + "\n",
        encoding="utf-8",
    )
    written += [copied, times]
    hashes = {path.relative_to(out).as_posix(): sha256(path.read_bytes()) for path in written}
    listing = out / "packet-manifest.yaml"
    listing.write_text(
        yaml.safe_dump({"round": 1, "files": hashes}, sort_keys=True), encoding="utf-8"
    )
    return [*written, listing]
