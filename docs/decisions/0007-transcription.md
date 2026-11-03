# ADR 0007 — Transcription: two pipelines, ALTO → TEI, ensemble OCR with a measured judge, second edition as base text

**Status:** Accepted — 2026-11-02

## Context

The two Bavinck editions arrive in different states. GD¹ (1895–1901) exists as proofread, *corrected* Distributed Proofreaders transcriptions on Project Gutenberg (all four volumes) with scans on DBNL. GD² (1906–1911) has no open transcription; the second printing is scanned on Delpher (VU Amsterdam copy, permanent URL per page, OCR layer) and the fourth printing (1928–30, retypeset, same words, different pagination) exists as PDFs with an OCR layer on theologienet.nl. The fourth printing's pagination is the one scholars cite, because the fifth through seventh printings reproduce it.

## Decision

### Two pipelines
- **GD¹: conversion.** Gutenberg HTML → TEI. Page anchors (DP's inline `[n]` markers) become `<pb n facs>` pointing at the DBNL scans. DP's end-of-book correction list is encoded as `<choice><sic/><corr/></choice>` so every reading that is not the print's is visible. DP's silent normalizations (Hebrew diacritics; `æ`→`ae` kept as printed) are documented in the TEI header. A sample of pages is checked against the scans to estimate residual error.
- **GD²: OCR.** Scan → ALTO → TEI, as below.

### Base text for `ed2`
The **second printing** (Delpher scans) is the base text: it is the last edition Bavinck prepared and its scans have library provenance and permanent page URLs. The **fourth printing's page breaks are layered on** as a second series (`<pb ed="ed4" n="…"/>`), derived by aligning text against the theologienet PDFs' OCR layer, so `GD² vol:page` resolves in either pagination. Derived page breaks carry `resp` marking them as aligned, not read. Before committing whole volumes, sample pages from both printings are run through the pipeline and compared by character error rate; if the second printing reads materially worse, the roles flip (fourth as base, second's pages layered) with no other design change.

### Physical and logical layers
- OCR output is **ALTO** XML, one file per page, with coordinates. ALTO is the physical layer and is kept.
- **TEI** is derived from ALTO and is the logical, canonical text. Every `<pb>` carries `facs`; paragraph-to-region links are emitted as IIIF annotations from the ALTO coordinates.

### Ensemble OCR with a measured judge
- At least two independent engines per page (a trainable classical engine such as Kraken, with Dutch, Greek and Hebrew models; and a vision model), with Delpher's own OCR layer as a third voice where available. Agreement → high confidence; disagreement → adjudicated and flagged with `cert`.
- A set of **hand-corrected ground-truth pages** per volume is the judge. Quality is reported as **character error rate** (and word error rate) against it, per volume, before publication. The ground truth is a reviewer task.

### Editorial policy
- **No modernization.** Spelling as printed. The NRI's modernized section titles are a finding aid, not text.
- Corrections only for typesetting errors, always as `<sic>`/`<corr>`; nothing silently changed.
- Footnotes as `<note place="bottom">`; Greek, Hebrew, Latin, German, French spans with `xml:lang`.

### Structure encoding for GD²
`<div type="part">` (Deel) → `<div type="chapter">` (Hoofdstuk) → `<div type="par">` (Par., with `par-13` and `par-13b`) → `<div type="subsection" n="A">` where present (e.g. Par. 5 A–F, Par. 30 A–E) → subparagraph `#` as the citable unit (the `refsDecl` level), with the original continuous numbering including `427a`/`427b`.

## Consequences

- GD¹ can be in TEI quickly; GD² is the long pole and needs the sample test and ground-truth pages first.
- Every number Bron publishes about transcription quality is against a human-corrected sample, never the engines' self-reported confidence.
- The Bolt/Vriend translation, which keeps the `#` numbers, aligns to the GD² TEI almost for free by `#` and serves privately as the translation judge (never published, never committed; it lives outside the repo).
