# Alignment

**Status:** Designed 2026-11-02 (design session 2). Decisions in ADR 0006. This document consolidates them and lists what remains.

## 1. Two problems

| | Edition ↔ edition | Source ↔ translation |
|---|---|---|
| Example | GD¹ ↔ GD² (the Bavinck Diff) | GD² Dutch ↔ Bron English |
| Nature | same language, revised and restructured; many-to-many with moves | different languages; Bron produces the target |
| How produced | automated + adjudicated, scored against gold | by construction during translation (hybrid) |
| Judge | human-aligned gold sample; precision/recall | reconciliation rules at generation time; reviewer corrections |

## 2. Representation

Stand-off TEI link files in `bron-data/alignments/`, one per pair of versions, e.g. `bavinck.gd.ed1--ed2.structure.xml`, `alignments/bavinck.gd.ed2--bavinck.gd.ed2.bron-eng.xml`.

```xml
<linkGrp type="edition" corresp="urn:cts:bron:bavinck.gd.ed1 urn:cts:bron:bavinck.gd.ed2">
  <link type="move"    cert="high"   resp="#run-2026-11-20"
        target="urn:cts:bron:bavinck.gd.ed1:35 urn:cts:bron:bavinck.gd.ed2:301-306"/>
  <link type="replace" cert="medium" resp="#run-2026-11-20"
        target="urn:cts:bron:bavinck.gd.ed1:3.2 urn:cts:bron:bavinck.gd.ed2:19"/>
  <link type="insert"  cert="high"   resp="#jdoe"
        target="urn:cts:bron:bavinck.gd.ed2:12"/>
</linkGrp>
```

- `type`: `equal | replace | insert | delete | move | split | merge`.
- `cert`: TEI certainty (`high | medium | low`).
- `resp`: pointer to a pipeline run or a named human in the file's header. This is the provenance hook for alignments; it is the same attribute reviewers' corrections carry.

Word-level diffs are computed at display time from the aligned sentences and never stored.

## 3. Levels

1. **Structure:** Par ↔ § (GD²'s 62 Par. against GD¹'s 56 §§). Built first, largely from the tables of contents; moves and insertions show up here (e.g. Providence: GD¹ §35 → GD² Par. 39; GD² Par. 9, 12, 13, 18 as additions).
2. **Unit:** subparagraph (`#`) ↔ subparagraph (`§.¶`), inside structurally aligned sections.
3. **Sentence:** inside unit-aligned pairs.
4. **Word:** display only.

## 4. Segmentation

SRX rules, with `segmentation/bron-nl.srx` for Dutch of Bavinck's period (abbreviations like `bl.`, `v.`, `Hd.`, inline citations, Greek and Latin spans) and `segmentation/bron-la.srx` later for Latin. Segmentation output is what sentence IDs attach to, so the SRX file is versioned with the pipeline and changes to it are treated like text changes (ADR 0004).

## 5. Edition-to-edition method

1. Structural concordance from the TOCs (agent-drafted, human-checked; it's 62 × 56).
2. Unit alignment: multilingual sentence-embedding similarity (works monolingually), constrained to the structurally aligned sections; model adjudication of low-confidence pairs; explicit move detection across sections.
3. Sentence alignment inside unit pairs by the same method.
4. Score against a **gold sample**: three sections aligned by a Dutch reader at unit and sentence level; report precision and recall; set a publication threshold before the first release.

## 6. Source-to-translation: the hybrid

Per paragraph: the translator receives the Dutch sentences with IDs and returns English sentences each tagged with the source IDs it renders.

Reconciliation (hard rules, enforced by the pipeline, not the model):
- every source ID used exactly once across groups;
- allowed cardinalities 1:1, 1:n, n:1; nothing unaccounted, nothing invented;
- non-reconciling output is rejected and retried with a stricter instruction; after N retries the paragraph is translated sentence-by-sentence and flagged for review.

English sentence identifiers derive from their source groups (e.g. Dutch `s12` → English `s12`, or `s12a`/`s12b` for a 1:2 split, or `s12-13` for a 2:1 merge), so the alignment is recoverable from the IDs and the link file is redundant but published for tooling.

Provenance state (XLIFF vocabulary; detailed in the provenance session) attaches to each English sentence at generation.

## 7. Open items (not design decisions)
- Choice of embedding model for unit and sentence alignment; evaluate on the gold sample.
- N for retries; the stricter-instruction wording.
- Who aligns the gold sample (first ask of the Westminster reviewer pool).
- Whether the NRI's segmented GD² pages expose text that could seed the structural concordance (contact: Dmytro Bintsarovskyi).
