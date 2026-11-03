# ADR 0002 — Citations follow each work's scholarly convention

**Status:** Accepted — 2026-11-02

## Context

A citation scheme is the one decision that cannot be changed after publication. Two options: a single uniform Bron scheme across all works, or each work's existing scholarly citation convention wrapped in a uniform syntax (the Perseus approach).

Scholars already cite Bavinck's *Gereformeerde Dogmatiek* (2nd ed.) by § number and by volume:page; Calvin's *Institutes* by book.chapter.section; the *Calvini Opera* by volume and column; Augustine by book.chapter.paragraph.

## Decision

The human-facing citation for each work is that work's existing scholarly convention. Bron supplies a uniform syntax and resolver around it, never a replacement numbering.

Specifically:

- The citation hierarchy for each edition is declared per edition (TEI `refsDecl`), following what scholars already use for that edition.
- Where a work's convention is page- or column-based (e.g. the *Calvini Opera*; possibly GD 1st ed.), the page or column is a first-class citation level, not merely a physical anchor.
- Where two conventions coexist for one work (GD 2nd ed.: § and volume:page), the primary hierarchy is the logical one (§) and the other is a resolvable secondary index.
- Translations have no citation structure of their own. The English is cited by the original's divisions (Loeb convention).
- Scripture references use OSIS identifiers (e.g. `Rom.8.28`) and link out.
- Where a work already has a CTS URN assigned by another project (Open Greek and Latin's `latinLit` URNs for Augustine and other Latin authors), Bron reuses that URN rather than minting its own. Bron mints URNs only for works nobody has identified.

## Consequences

- A Bron citation in a footnote means something to a reader who never visits Bron.
- Each new work requires a short "citation convention" note before ingestion.
- Bavinck's 1st edition needs a fact check: whether it has usable § numbering. If not, its convention is volume:page.
