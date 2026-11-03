# ADR 0014 — Licensing: Apache-2.0 for code; public domain / CC0 for transcriptions and metadata; CC BY 4.0 for authored content

**Status:** Accepted — 2026-11-02

## Context

Three kinds of material with different legal natures: software; transcriptions of public-domain works and the metadata about them; and original work by Bron and its contributors (translations, lexicon, alignment judgments, documentation).

## Decision

- **Code (`bron`): Apache-2.0.** Patent grant; contributions automatically under the same terms (section 5), so no contributor agreement is needed; comfortable for institutional contributors.
- **Transcriptions of public-domain works, metadata, registry (`bron-data`): no license claimed.** Marked with the Public Domain Mark where the underlying work is public domain; any residual rights Bron might hold are waived under CC0 1.0. Bron never claims rights in the sources it opens.
- **Content authored by Bron and contributors (`bron-data`): CC BY 4.0.** Attribution to "Bron contributors" and to named reviewers where recorded. Chosen over CC BY-SA for reach: the original stays open regardless, and compatibility with the organizations most able to carry the texts further (CCEL, Bible software, publishers) outweighs capturing their improvements.
- `CITATION.cff` in both repos; `LICENSE` and `LICENSE-CC0` at the root of `bron-data`; each data file names its own status in its header.

## Consequences

- Nobody can accuse Bron of enclosing public-domain sources.
- Reviewers' credit travels with any reuse of the translations.
- Contributions to code need no CLA; contributions to data are accepted under CC BY 4.0 by the act of opening a pull request, stated in the data repo's README.
