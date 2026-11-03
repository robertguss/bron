# ADR 0008 — Translation and lexicon: TBX termbase defaulting to established usage, MQM as the judge, calibrated automatic judging, gated public drafts

**Status:** Accepted — 2026-11-02

## Context

Translation is the center of Bron's thesis and its largest risk: fluent, doctrinally wrong English. Unverified machine translation of public-domain Bavinck already exists (Monergism, 2026), so the contribution is verification, consistency and provenance, not translation as such. Per ADR 0001, conventions from the translation industry and from machine-translation evaluation are adopted.

## Decision

### Unit and workflow
Per ADR 0006: paragraph-level translation with mandatory sentence-ID reconciliation (the hybrid). Two independent models translate in the pilot; disagreement is a reviewer flag.

### Register and scope
- Contemporary, formal, **literal-leaning** English: fidelity over elegance, because the reader checks the English against the original beside it.
- **No modernization or paraphrase of the author's structure**; sentence restructuring only within the reconciliation rules.
- **Quotations in other languages** (Latin, Greek, German, French) are translated as their own units with `xml:lang` on the source; never silently folded into the surrounding prose.
- **Bibliographic references** are normalized and linked, not translated.

### Lexicon
- **Format: TBX** (ISO 30042, TBX-Basic profile). One concept per entry: source terms as they occur (Dutch, Latin, Greek), preferred English rendering, admitted and deprecated alternatives, a definition drawn from where the author defines or characteristically uses the term, the rationale, and references to passages.
- **Default: established usage.** The preferred rendering is the established English vocabulary of Reformed theology — as codified for Bavinck by the Bolt/Vriend edition, for scholastic Latin by Muller's *Dictionary*, and for confessional terms by the Standards' English. Terms are facts of usage; Bron borrows terms, never sentences or definitions from copyrighted works.
- **Departures are documented decisions:** a departure from established usage requires a rationale in the entry and is a reviewable change.
- **Entries have states:** `proposed` → `approved` (by a reviewer). Only approved entries are injected into translation; proposed entries only flag.
- **Seeding:** the GD² calibration run proposes entries from `#`-aligned comparison with established usage; reviewers approve.

### Enforcement
- **Glossary injection:** approved entries relevant to the passage are supplied to the translator.
- **Terminology QA:** a post-pass flags any output departing from a preferred rendering; a departure stands only with a stated reason attached to that sentence (recorded in provenance).

### Quality: what "drift" means
- **Cheap signals:** chrF and COMET against a reference where one exists (Bolt for GD², privately). Early warning only; two faithful translations differ.
- **The judge: MQM** (Multidimensional Quality Metrics) error typology — accuracy (mistranslation, omission, addition), terminology, fluency, style — with severity weights. Human MQM on samples is the ground truth.
- **Calibrated automatic judge:** a model acting as MQM reviewer is scored against human MQM on GD² (where Bolt also exists) before it is trusted anywhere. Its measured reliability is what licenses its use on GD¹ and the periphery, where no reference exists. Judge first, then text.
- **Terminology adherence** is measured automatically against the lexicon for every passage.

### Publication gate (public visibility before human review)
- A machine draft becomes publicly visible only when it clears a **measured threshold** from the calibrated automatic judge, and it still carries its provenance label (`initial`/machine draft) and score.
- Below threshold, the draft stays private to the pipeline and reviewers and is queued.
- Thresholds are set from the GD² calibration numbers and published with them; they can move, but changes are releases (ADR 0004).

### Calibration order
GD² first (reference available); the lexicon is built and corrected there; GD¹ and the periphery inherit the approved lexicon and the calibrated judge.

## Consequences

- Bron's English is predictable to readers of the Baker volumes and to users of Muller.
- Every number Bron publishes about translation quality traces to human MQM on a sample; the automatic judge is never the final word, and its own reliability is a published number.
- Readers never see an unlabeled or unscored draft, and never see a draft below the floor.
- The private judge material (Bolt's digital text) lives outside the repo; only scores are published.
