# Transcription

**Status:** Designed 2026-11-02 (design session 3). Decisions in ADR 0007. This consolidates them and lists sources and open items.

## 1. Sources per edition

| Edition | Text source | Scans | Notes |
|---|---|---|---|
| GD¹ (1895–1901) | Project Gutenberg DP transcriptions: vol. 1 #51052, vol. 2 #67966, vol. 3 #68527, vol. 4 #69005 | DBNL (KB), PDF per volume, ~29–32 MB | DP texts are corrected, with correction lists; §27–33 erratum applied in vol. 2; vol. 2 §29 lacks a subparagraph 11 in the original |
| GD² (1906–1911) base | OCR by Bron | Delpher, VU Amsterdam copy, permanent URL per page, OCR layer (`MMUBVU05:…`) | "Auteursrecht onbekend" is Delpher's default label; confirm reuse terms |
| GD² fourth-printing pagination (1928–30) | theologienet.nl PDFs (OCR layer) | same | used only to derive `<pb ed="ed4">`; anonymous provenance, so never the base |

## 2. Pipelines

```
GD¹:  Gutenberg HTML ──convert──▶ TEI (+pb facs→DBNL, choice/sic/corr from DP list) ──sample check vs scans──▶ ed1
GD²:  Delpher page images ──engine A, engine B, Delpher OCR──▶ ALTO per page ──reconcile──▶ TEI ──align──▶ +pb ed4 ──▶ ed2
                                                      └── CER vs ground-truth pages (per volume) ──▶ published number
```

## 3. Judge

- Ground truth: a fixed set of pages per volume, hand-corrected by a reviewer against the scan.
- Metrics: character error rate and word error rate against ground truth, per engine and for the reconciled text; reported per volume.
- Policy: no volume published without its number; threshold to be set once the first volume's numbers exist.

## 4. Editorial policy (summary)
Spelling as printed; corrections only for typesetting errors, as `<sic>`/`<corr>`; DP's normalizations documented in the header; footnotes as `<note place="bottom">`; languages tagged.

## 5. Open items
1. Sample test: 10 pages each from the Delpher second printing and the theologienet fourth printing through both engines; compare CER. Decides base-text confirmation.
2. Engine choice and models (Kraken vs. Tesseract for the classical voice; which vision model; whether to train on ground truth).
3. Confirm Delpher/KB reuse terms for public-domain book scans; note the VU as source copy in the TEI header.
4. Whether the DBNL PDFs are the same scans as Delpher's for GD¹ (both are KB), so one IIIF set serves both.
5. Hebrew in GD²: whether engines handle it or those spans get flagged for human entry.
