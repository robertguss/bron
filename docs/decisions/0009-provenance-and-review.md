# ADR 0009 — Provenance and review: origin and state on every sentence, XLIFF states, git as the ledger, vetted reviewers with promotion

**Status:** Accepted — 2026-11-02

## Context

Bron's promise is that every English sentence says what it is. That requires a precise claim per sentence, a rule about who may make it, a rule about what un-makes it, and a workflow in which the claims are produced as a byproduct of reading. Per ADR 0001, the XLIFF state vocabulary, TEI responsibility attributes, ORCID, and the open-source pull-request model are adopted rather than designed.

## Decision

### Two axes
- **Origin** — who or what produced the text: a pipeline run (`#run-YYYY-MM-DD-…`), a named human, or a public-domain published translation (e.g. Beveridge for Calvin). Carried on each sentence by TEI `@resp`, pointing to a `<respStmt>` in the header (name, role, ORCID where available).
- **State** — how far the text has been checked. XLIFF 2 values, unchanged:
  - `translated` — a draft exists (machine or human);
  - `reviewed` — a vetted reader checked it against the source;
  - `final` — approved for citation.
  Carried by `@ana` pointing to the vocabulary declared once in the TEI header. XLIFF files are generated for exchange with CAT tools; TEI remains canonical.

### Who may set what (vetted with promotion)
- Anyone may propose a correction (a pull request against the data repo).
- `reviewed` may be set only by a **vetted reviewer**: a person on a maintained list whose competence in the source language is attested (faculty, doctoral students, scholars who ask), identified by real name and, where they have one, ORCID.
- **Promotion:** a contributor whose proposals have been repeatedly accepted by vetted reviewers may be added to the list by the maintainer; the criteria are published.
- `final` is set by a vetted reviewer other than the one who set `reviewed`, or by the maintainer for anchored public-domain translations after a check.
- Anonymous or pseudonymous accounts may propose; their work never carries a state above `translated` until a vetted reviewer approves it.

### What changes state
- Source sentence changed (OCR correction, re-segmentation): its translation drops to `translated`, flagged "source changed since review"; the previously reviewed text stays visible beside the flag.
- Reviewer edit or approval: `reviewed`.
- Lexicon entry changed: affected sentences are flagged for re-check, not reset.
- Nothing is promoted or demoted silently; every change is a commit with a responsible party.

### Git is the ledger
- The data repo's commit and pull-request history is the provenance log. Reviews are PR reviews; approvals are merges by vetted reviewers.
- The reviewer UI (session: reader) writes commits and PRs; it does not keep state anywhere else.
- "Seminar as review" maps directly: students open PRs, the professor (vetted) approves.

### Review doubles as data
The reviewer screen shows, per paragraph: source | draft | lexicon hints | the two translators' disagreements | flags. Four actions per sentence:
1. approve;
2. edit (sets `reviewed`, records the edit as a future example);
3. mark an error by **MQM category and severity** (the human judge data of ADR 0008);
4. propose a lexicon change (a `proposed` TBX entry, ADR 0008).

### Credit
Reviewer name and date are visible on the sentence, listed in the TEI header, and included in "cite this" output at the cited version.

## Consequences

- A `reviewed` label means exactly one thing: a named, competent reader checked this sentence against the source.
- The review workflow produces the lexicon, the judge calibration data, and the training examples without a separate data-collection effort.
- Vetting is a maintainer responsibility; the list and criteria are public files in the repo.
- The reader must render origin, state, reviewer, date, score and "source changed" flags per sentence (reader session).
