# ADR 0016 — GD¹: PDF page anchors and an agent-read error estimate, as staged exceptions

**Status:** Accepted — 2026-11-03. Amends ADR 0003 (Scan linking) and ADR 0007 (published quality figures) for GD¹ only.

## Context

GD¹ arrives as proofread Gutenberg transcriptions, and its scans are on DBNL as one PDF per volume (`bavi002gere01`–`04`). Two accepted decisions do not fit that situation yet.

- **ADR 0003** says every `<pb>` points to a IIIF canvas, from a library's IIIF or from Bron's own. DBNL offers no IIIF service that research found, and Bron does not yet host IIIF. DBNL's title-specific terms (*gebruiksvoorwaarden*) permit reuse once a work's copyright has expired. Their database and bulk-download conditions are separate. So hosting IIIF derived from these scans may be allowed, but only after a check of the specific source copies.
- **ADR 0007** says every number Bron publishes about transcription quality is measured against a human-corrected sample. GD¹'s first error estimate comes before any reviewer is available, and its sample check is read by agents.

## Decision

- **Page anchors link the DBNL PDFs.** For GD¹, each `<pb>` carries `facs` pointing at its page of the DBNL PDF (`…/bavi002gere01_01.pdf#page=25`). Nothing from DBNL is copied or redistributed.
- **IIIF replaces the PDF links later.** That waits for a source-copy rights check of the DBNL scans and lands with Bron's IIIF work (M3 for GD² scans, M6 for the public reader). The registry's DBNL terms record states the terms as they read, keeping work copyright, site terms and bulk-download conditions apart.
- **GD¹'s sample check publishes an exploratory, agent-read estimate.** The 20-page check against the DBNL scans reports a residual-discrepancy figure, with its protocol and with its corroboration labeled as such, not as ground truth. It is not a gate.
- **Human-corrected measurement starts with GD².** ADR 0007's rule applies from the M2 OCR sample test onward.

## Consequences

- M1 can resolve a GD¹ citation to its printed page now, without image infrastructure.
- The M6 reader cannot embed DBNL images until the rights check is done. The NRI's own GD¹ scan is a candidate source to evaluate then.
- GD¹'s published quality figure is clearly weaker evidence than GD²'s will be, and says so.
