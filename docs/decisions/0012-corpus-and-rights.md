# ADR 0012 — Corpus and rights registry

**Status:** Accepted — 2026-11-02

## Decision

- **Registry:** one record per work per source copy, in a plain data file in the data repo, naming the holding institution, its identifier (e.g. Delpher `MMUBVU05:000000743`, DBNL `bavi002gere01`, Gutenberg #51052), the edition and printing, and the rights statement.
- **Rights vocabulary:** rightsstatements.org statements for sources ("No Copyright - United States", "Public Domain Mark", "No Copyright - Other Known Legal Restrictions", "Copyright Undetermined" while a check is pending) and Creative Commons for Bron's outputs (ADR: licensing decision pending; intended CC BY 4.0 or CC0 for data).
- **Public-domain rule of thumb, recorded per work:** US — published 1930 or earlier (as of 2026); EU — author dead 70+ years. Both are recorded; the stricter applies to what Bron publishes.
- **Terms checks are registry records too:** the reuse terms of Delpher, DBNL and the NRI sources site are recorded with date checked and link, before bulk use of their scans.
- **Inventory source for Bavinck:** the NRI bibliography (917 items); the periphery is catalogued from it, each item with its source copy and rights record before transcription.
- **Copyrighted translations** (Bolt/Vriend, Giger/Dennison, Battles, New City Press, Lexham) are listed in the registry as judge-only material with a "never published" flag.

## Consequences
- Every text Bron shows can answer "where did this come from and why may we show it" from one record.
- Later authors (Schilder, Dooyeweerd) enter the registry with their rights status first; the registry, not enthusiasm, decides what gets transcribed.
