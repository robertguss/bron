# Roadmap

**Status:** Written 2026-11-02 at the end of the design phase. Order of work, not a schedule; no dates on purpose. Each milestone names what "done" means and who does it: **R** = Robert (decides, approves, maintains), **A** = agents (build everything), **V** = vetted reviewer (a Dutch reader; the first external ask).

The thread through all of it: one chapter of Bavinck, both editions, end to end, before anything scales. GD² Par. 23–25 (`#161–177`, the knowability of God) and its GD¹ counterpart §20–22 are the chosen slice, because the same seventeen subparagraphs serve the OCR ground truth, the translation judge, and the alignment gold sample, so a single reviewer ask covers all three.

## M0 — Scaffolding
- **A:** `bron` repo layout for code; `bron-data` layout per CapiTainS (created 2026-11-02; licenses in place, ADR 0014); CI with TEI schema, CapiTainS, DTS validators and the identifier-stability check (ADR 0011).
- **R:** obtain the written outside-project acknowledgement from Westminster (PRD §13); confirm Delpher, DBNL and NRI reuse terms (A drafts the registry records, R confirms).
- **Done when:** an empty but valid CapiTainS data repo passes CI, and the three terms checks are recorded (ADR 0012).

## M1 — GD¹ in TEI
- **A:** convert the four Gutenberg transcriptions to TEI per ADR 0007: `§.¶` citation hierarchy in the `refsDecl`, `<pb n facs>` restored to the DBNL scans, DP's correction lists as `<choice><sic/><corr/></choice>`, DP normalizations documented in the header, languages tagged; CapiTainS-valid; DTS Level 0 build produces the four volumes.
- **A:** sample check of 20 pages against the DBNL scans; report residual error.
- **Done when:** `urn:cts:bron:bavinck.gd.ed1:3.2` resolves through DTS to the right Dutch, with its page image anchor.

## M2 — GD² OCR sample test
- **A:** ten pages from the Delpher second printing and the same ten pages from the fourth-printing PDFs, through two engines and Delpher's layer; ALTO out; reconciled TEI out.
- **V:** hand-correct the ten second-printing pages (ground truth).
- **A:** CER and WER per engine and reconciled, per printing; recommendation.
- **R:** confirm or flip the base text (ADR 0007).
- **Done when:** the numbers are in `docs/research/` and the base text is confirmed.

## M3 — GD² Par. 23–25 transcribed
- **A:** full pipeline on `#161–177` (second printing): ALTO → TEI with part/chapter/par/subsection/subparagraph structure, footnotes, languages; fourth-printing `<pb ed="ed4">` layered by alignment; static IIIF tiles for those pages; CapiTainS-valid; DTS resolves `…ed2:170`.
- **V:** ground-truth pages within the range (reuse M2 pages where they overlap).
- **Done when:** CER for the range is published and `urn:cts:bron:bavinck.gd.ed2:170` resolves with its scan.

## M4 — Translation pilot (ADR 0008 §2)
- **A:** two translators, hybrid reconciliation, lexicon empty on pass one; propose TBX entries from observed pairs; re-run with injection; chrF/COMET against Bolt locally (R keeps the Bolt text on his machine; only scores leave it); automatic MQM.
- **V:** human MQM on a fixed subset; approve or reject proposed lexicon entries.
- **A:** judge calibration figure; gate threshold from the distribution.
- **Done when:** the first approved TBX entries exist, the judge's agreement with the human is a published number, the threshold is set, and the seventeen subparagraphs carry `translated` state with scores.

## M5 — Alignment pilot (ADR 0006)
- **A:** unit and sentence alignment GD¹ §20–22 ↔ GD² Par. 23–25 within the structural concordance; stand-off link file with `@cert`/`@resp`.
- **V:** gold alignment of the three sections at unit and sentence level.
- **A:** precision and recall; publication threshold proposed.
- **Done when:** the link file and its score are committed and the diff renders.

## M6 — Thin slice public
- **A:** reader pages for the slice per ADR 0010: desktop three columns and diff mode, phone interleaved default, IIIF viewer embedded, lookups linked to WNT and Logeion, provenance badges, SBL "cite this" with URL, pinned URL and URN; DTS Level 0 and search index from the same build; deployed static on the VPS.
- **R:** first release tag; Zenodo DOI; `REVIEWERS.md` with the first vetted reviewer and the promotion criteria (ADR 0009).
- **Done when:** a stranger can open `/bavinck/gd/ed2/170`, see the Dutch, the English with its badge, the scan, the GD¹ counterpart in diff mode, and cite it with a permalink that pins to release 0.1.

## M7 — Outreach (ADR 0013)
- **R:** emails in the agreed order, each with the URL: Dmytro Bintsarovskyi (NRI), the Bavinck Institute, Westminster faculty (reviewer list), CCEL.
- **Done when:** asks are out and recorded; nothing in M8 waits on replies.

## M8 — Scale Bavinck
- GD² transcription volume by volume (vol. 1 first; revisions heaviest there), each volume with its CER before publication.
- Full GD¹ ↔ GD² diff, scored.
- Full translation of GD² (gated drafts), then GD¹, then the periphery from the NRI inventory as rights records are confirmed.
- Reviewer program: seminar-as-review at Westminster; promotions by track record.
- Releases with DOIs at each volume.

## Later phases (PRD §9)
Kuyper; Calvin as the Latin calibration set (*Calvini Opera* with public-domain English pairs); Augustine on existing `stoa0040` URNs; the post-Reformation scholastics via PRDL, which reopens transcription for early-modern print; archives and handwriting.

## What must not slip
- No volume published without its CER; no draft public below the gate; no `reviewed` without a named vetted reviewer.
- Identifiers never renumbered. Bolt's text never in a repo.

## Deliberately absent
Dates, team size, and hours. The order is the plan; the pace is Robert's.
