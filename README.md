# Bron

*Bron* (Dutch): source; also spring, well.

An open commons giving English readers access to the primary sources of the Reformed and neo-Calvinist tradition in their original languages — Dutch, Latin, French, German — without requiring them to know those languages. Original and translation side by side, every claim traceable to a page, every translation carrying its provenance, every passage citable forever.

Short form: Perseus for the Reformed tradition.

## Status

Designed; not yet built. Start with [PRD.md](PRD.md), then [docs/roadmap.md](docs/roadmap.md). The design lives in [docs/](docs/) (text model, alignment, transcription, translation, provenance) and fourteen ADRs in [docs/decisions/](docs/decisions/). The first data artifact, the GD¹ ↔ GD² structural concordance, is in [bron-data](https://github.com/robertguss/bron-data).

**First milestone — the Bavinck Diff:** both editions of Herman Bavinck's *Gereformeerde Dogmatiek* (1895–1901 and 1906–1911) transcribed, aligned paragraph by paragraph, with every change rendered in English. The first edition has never been in English.

## Principles

1. The data is the project; the reader app is replaceable.
2. The original is always visible beside any translation.
3. Nothing is trusted by default; every translated unit carries its provenance state.
4. Citations never break.
5. Verification over fluency; outside judges, never the model grading itself.
6. Reproducible; anyone can re-run the pipeline.
7. Open, and separable: data and code in separate repos under separate licenses.
8. Built over the existing libraries (NRI, PRDL, Delpher, DBNL), linking back.

## Repos

- `bron` (this repo) — design docs and, later, code. Apache-2.0.
- [`bron-data`](https://github.com/robertguss/bron-data) — texts, alignments, lexicon, provenance, registry. Public domain / CC0 for transcriptions and metadata; CC BY 4.0 for authored content. The first data artifact, the GD¹ ↔ GD² structural concordance, lives there.

## Licensing

Code: Apache-2.0 (`LICENSE`). Data: see `bron-data`. Decision recorded in ADR 0014.

## Working model

Designed by Robert Guss. Built by AI agents. Verified by humans and tools.
