# GD¹ page map

**Date:** 2026-11-04. **Artifact:** `src/bron/convert/gd1/data/page-map.yaml`, produced by `bron convert gd1-page-map`.

Every page break in the GD¹ TEI links to a page of DBNL's scan PDF of its volume (ADR 0016). This report covers how that link was measured, the evidence for each page, and the numbering questions settled on the scans.

## Inputs

The four DBNL PDFs, each checked against its SHA-256 in `bron-data:registry/sources.yaml` before use:

| Vol. | PDF | Pages | SHA-256 |
|---|---|---|---|
| 1 | `bavi002gere01_01.pdf` | 544 | `1da332b5…` |
| 2 | `bavi002gere02_01.pdf` | 580 | `745feb1d…` |
| 3 | `bavi002gere03_01.pdf` | 580 | `b9a64cdd…` |
| 4 | `bavi002gere04_01.pdf` | 598 | `5afb55f3…` |

## Method

1. **Read.** For each PDF page, the tool reads the PDF's own OCR text layer (pypdfium2 5.14.0). The page number is the page's first line. On chapter openings, where the number is printed at the foot, it is the last line. In vol. 1's front matter, a roman numeral is read beside the running head ("IV VOORBERICHT.", "INHOUD. VII").
2. **Set aside misreadings.** Each match gives an offset (PDF page minus position in the volume's page sequence). A match is kept when its offset agrees with at least one of the two nearest matches on each side. Otherwise it is a misreading and is set aside.
3. **Report conflicts.** Two kept matches next to each other with different offsets are a conflict, and the tool reports it rather than choosing between them. There were none.
4. **Interpolate.** A page with no kept match, lying between two kept matches that agree, takes their offset.
5. **Review.** Every other page, and every checkpoint below, was rendered from the PDF and read. Each such page is recorded under `reviews` in the map with a note, and its method becomes `visually verified`. A review that contradicted the measurement would be a conflict. There were none.

The map lists every printed page of each volume once: vol. 1's roman pages III–VII, then pages 1 to the last page of each volume.

## Results

| Vol. | Pages mapped | OCR | Interpolated | Visually verified | Offset (arabic) | Misreadings set aside |
|---|---|---|---|---|---|---|
| 1 | 537 (III–VII, 1–532) | 485 | 35 | 17 | +10 | 4 |
| 2 | 571 | 546 | 10 | 15 | +6 | 2 |
| 3 | 572 | 550 | 18 | 4 | +6 | 3 |
| 4 | 590 | 558 | 20 | 12 | +6 | 6 |

The offsets of +10 (vol. 1) and +6 (vols. 2–4) that research predicted hold for every page of every volume. No volume has an inserted plate or a skipped page. Vol. 1's roman pages sit at PDF 5–9 (III = PDF 5).

**Misreadings set aside**, as PDF page and the number read there:
- vol. 1: 137 ('197'), 163 ('53'), 218 ('203'), 379 ('24');
- vol. 2: 210 ('201'), 367 ('36');
- vol. 3: 131 ('120'), 211 ('5'), 348 ('343');
- vol. 4: 39 ('32'), 199 ('13'), 358 ('312'), 359 ('23'), 450 ('244'), 581 ('55').

Some of these are printer's sheet signatures, not page numbers. A sheet of 16 pages is signed at the foot of its first page (vol. 4 p. 193 carries '13', and p. 353 carries '23'). On vols. 3 and 4, p. 1's signature '1' is also its page number. Both of those pages were reviewed.

**Interpolated pages** (no readable number; between agreeing matches):
- vol. 1: 5, 9, 20, 21, 25, 38, 111, 127, 132, 153, 208, 211, 216, 227, 249, 262, 266, 285, 303, 307, 308, 310, 315, 318, 324, 335, 346, 351, 356, 365, 369, 370, 387, 460, 466;
- vol. 2: 8, 26, 121, 204, 266, 351, 361, 375, 485, 521;
- vol. 3: 6, 59, 62, 64, 73, 75, 83, 92, 96, 113, 125, 205, 229, 253, 255, 342, 360, 452;
- vol. 4: 7, 11, 33, 39, 55, 80, 116, 120, 132, 233, 326, 346, 352, 360, 419, 444, 557, 562, 567, 575.

None borders a conflict, so none needed a visual check of its own.

## Checkpoints read on the scans

Every checkpoint agreed with the measurement.

- **First and last body pages:** vol. 1 pp. 1 and 532, vol. 2 pp. 1 and 571, vol. 3 pp. 1 and 572, vol. 4 pp. 1 and 529. The PDF pages after each volume's last page are blank. Vol. 4's back matter runs from p. 530 (*Breedere inhoudsopgave*) to p. 590 (end of the *Register van zaken*), both read.
- **Chapter openings** (none prints its page number, except where the sheet signature coincides with it):
  - vol. 1: pp. 1 (*Inleiding*), 140 (*Deel I*, *Hoofdstuk I* and § 6, all on one page), 215 and 416;
  - vol. 2: pp. 1 and 386;
  - vol. 3: pp. 1, 187 and 425;
  - vol. 4: pp. 1, 193 and 353.
- **Front matter:** vol. 1 pp. III (*Voorbericht*, unnumbered), VI (*Inhoud*, unnumbered) and VII. PDF 10 (VIII) is blank.
- **Vol. 4 p. 484:** the scan prints "484". The transcription's marker for this page shows the label "]", so the converter takes the number from the map.
- **Vol. 2 p. 386:** the scan prints no number, and the transcription has no marker for this page. *Hoofdstuk V* and § 29 open here, so the converter inserts this page break before the chapter heading.

## The §§ 27–33 headings as printed

The vol. 2 headings carry wrong numbers, which the book's own *Inhoud* footnote asks readers to correct. The transcription applied that correction silently. The scans read:

| § (corrected) | Page | Printed |
|---|---|---|
| 27 | 227 | § 25 |
| 28 | 313 | § 26 |
| 29 | 386 | § 27 |
| 30 | 424 | § 28 |
| 31 | 456 | § 29 |
| 32 | 490 | § 36 |
| 33 | 508 | § 31 |
| 34 | 545 | § 34 (correct) |

§ 32's heading prints "36", not "30". It was read at 5× by two separate readings. The *Inhoud* gives p. 455 for § 31, but the heading is on p. 456; p. 455 carries § 30's last page.

## Numbering findings

- **Vol. 1 § 5 has no subparagraph 7.** Subparagraph 6 opens on p. 64 and 8 on p. 69, after the heading "C." Pages 64–69 were each read. The three paragraphs that begin between them are unnumbered. The gap is in the print, not a transcription loss.
- **Vol. 2 § 29 has no subparagraph 11.** Subparagraph 10 opens on p. 417 and runs through p. 418 into p. 419, where 12 opens. The transcribers' note says the same.
- **Vol. 4 § 51 prints "6." twice:** on p. 239 ("6. Alnaarmate het verband…") and on p. 246 ("6. Het getal der sacramenten…"). No other numbered subparagraph opens between 5 (p. 234) and the second 6. The transcribers corrected the second to 7.

The converter's numbering check allows exactly the two gaps (§ 5 without 7, § 29 without 11) and the §51 correction. These findings are recorded under `numbering` and `headings` in the map.

## Repeating the measurement

```sh
uv run bron convert gd1-page-map --registry ../bron-data/registry/sources.yaml --cache ~/.cache/bron/sources
```

The command fails when a cached PDF's hash differs from the registry. It rewrites the page lists and keeps `reviews`, `numbering` and `headings` unchanged. It exits non-zero while any page is unresolved or any conflict is reported.
