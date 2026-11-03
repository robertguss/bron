# ADR 0006 — Alignment: stand-off links, hierarchical levels, hybrid translation alignment

**Status:** Accepted — 2026-11-02

## Context

Bron aligns texts in two senses: edition to edition (the Bavinck Diff: GD¹ ↔ GD², same language, revised and restructured, many-to-many with moves) and source to translation (Dutch ↔ English, where Bron produces the English itself). Both must be represented, produced, and verified. Per ADR 0001, conventions are adopted where they exist.

## Decision

### Representation
- Alignments are **stand-off TEI** `<linkGrp>` files whose `<link>` targets are passage identifiers (CTS URNs down to the internal sentence `xml:id`s). Alignment markup is never embedded in the text files.
- Each `<link>` carries: a change type (`equal`, `replace`, `insert`, `delete`, `move`, `split`, `merge` — diff's opcodes plus the three structural ones), TEI `@cert` for confidence, and TEI `@resp` for who or what asserted it (pipeline run, model, or named human reviewer). `@resp` is the provenance hook; no separate vocabulary is invented.
- Links are many-to-many by design; `427a`/`427b` and 1:3 expansions are ordinary.

### Levels
Structure first (Par ↔ §), then unit (subparagraph ↔ ¶), then sentence, then word-level diff computed at display time and never stored. Each level constrains the next: sentence alignment happens only inside unit-aligned pairs.

### Segmentation
Sentence segmentation follows **SRX** rules, with a Bron SRX file tuned for Bavinck's citation-dense prose (abbreviations, inline references, Greek and Latin). Segmentation is part of the alignment pipeline and versioned with it.

### Edition-to-edition method and judge
Automated alignment (structural concordance from the tables of contents; then embedding similarity at unit and sentence level with model adjudication for low-confidence pairs), **scored against a human-aligned gold sample** of a few sections, reported as precision and recall at unit and sentence level. No alignment is published without the score.

### Source-to-translation: the hybrid
Translation is produced **per paragraph for fluency, with alignment required by construction**: the model receives source sentences with IDs and must return English sentences each tagged with the source sentence IDs they render. Reconciliation rules:
- Every source sentence ID appears exactly once across the output groups.
- Allowed cardinalities: 1:1, 1:n (one Dutch sentence rendered as several English), n:1 (several Dutch merged into one English). Nothing unaccounted for, nothing invented.
- An output that does not reconcile is rejected and retried with a stricter instruction; after a bounded number of retries the paragraph falls back to sentence-by-sentence translation and is flagged for review.
- English sentence identifiers are derived from their source groups, so the Dutch → English mapping is recoverable from the IDs alone.

## Consequences

- Provenance attaches at the sentence level with no reconstruction step: every English sentence names the Dutch it came from, at the moment it is produced.
- Reviewers see the translator's own account of what maps to what, which is also what they correct.
- The structural concordance GD¹ ↔ GD² is the first alignment artifact and can be built from the two tables of contents before any transcription exists.
- A gold sample needs a Dutch reader; this is the first concrete ask of the Westminster reviewer pool.
