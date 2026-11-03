# ADR 0010 — Reader: static-first, embedded IIIF viewer, dictionaries linked not built, interleaved parallel text on phones

**Status:** Accepted — 2026-11-02

## Context

The reader is replaceable (principle 1: the data is the project), but it is where readers meet the principles of "original always visible" and "provenance visible" (ADR 0009). Per ADR 0001, existing viewers, dictionaries and citation styles are used rather than rebuilt.

## Decision

### Architecture
- **Static-first.** Every passage page is pre-rendered from the TEI at build time; the same build emits DTS 1.0 Level 0 endpoints (ADR 0003) and a static full-text index (Pagefind or equivalent). Client-side script enhances (badges, lookups, diff highlighting, reveal) but the page reads without it.
- **Scans:** an embedded IIIF viewer (Mirador or Universal Viewer); Bron does not build an image viewer. Any IIIF-served scan elsewhere can appear in the scan column.

### Views on a passage page
- **Desktop:** scan | original | English, three columns; the edition diff as a fourth mode replacing the scan column.
- **Phone, default: interleaved pairs.** Each English sentence followed by its source sentence in a lighter face. The reader may switch to "English only," which keeps the provenance badges and a per-sentence tap-to-reveal of the source; the choice to hide the original is always the reader's, never Bron's default.
- **Diff mode** follows the Versioning Machine and code-diff conventions: units side by side, inline word-level differences within a unit, moves rendered as links to the destination, the structural concordance as the map at the top.

### Lookups
- **Dutch:** tap a word → lemma and gloss; link to the WNT entry (INT, the historical dictionary of Dutch) and to Bron's lexicon entry when the word is a term.
- **Latin and Greek:** Alpheios-style morphology; links to Logeion (Lewis & Short, LSJ).
- Bron supplies lemmas, glosses and links; it does not publish a dictionary.

### Provenance display
A small badge per sentence showing state and origin kind; tap/hover shows reviewer, date, automatic score, and flags (`source-changed`, `translators-disagree`, etc.). Badges can be dimmed, not removed.

### Citation
"Cite this" emits: readable URL, pinned URL (`?v=`), CTS URN, and a formatted citation in **SBL style** including edition, passage, Bron release, and the state and reviewer at that version.

### Ask-an-agent
A passage tool: answers only from the visible passage, its lexicon entries and resolved cross-references; every answer cites passage identifiers; it declines questions beyond the text. Not a general chat.

### Other
- Semantic HTML; print stylesheet; keyboard navigation.
- UI in English initially; the texts carry their own languages.

## Consequences

- The reader can be rebuilt without touching data; its contract is the TEI, the stand-off files and the DTS endpoints.
- Phone pages are longer in the default view; that is the price of the principle, chosen knowingly.
- Dictionary quality is the dictionaries' problem; Bron's responsibility is correct lemmas and links.
