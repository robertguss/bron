# ADR 0005 — Readable URLs are canonical; URNs are exposed, not pasted

**Status:** Accepted — 2026-11-02

## Context

Conventions disagree on what a text URL looks like. Scaife (Perseus) puts the full CTS URN in the path (`/reader/urn:cts:...`): precise, one identifier, ugly in a footnote. CCEL uses readable paths that mirror the citation: what people actually paste, at the cost of a second identifier to keep in sync.

## Decision

- The **canonical public URL is readable** and mirrors the scholarly citation:
  `/<textgroup>/<work>/<version>/<passage>` — e.g. `/bavinck/gd/ed2/317`.
- Ranges and subreferences mirror CTS syntax inside the passage segment: `/bavinck/gd/ed2/317-320`, `/bavinck/gd/ed2/317@genade[2]`.
- Pinned citations append `?v=<release>` (ADR 0004).
- Secondary indexes (e.g. volume:page for GD²) resolve under an explicit segment, e.g. `/bavinck/gd/ed2/page/2.350`, redirecting to the containing logical passage.
- The **CTS URN is exposed** in page metadata, in the "cite this" output, and through the DTS API. A URN-in-path form (`/urn:cts:bron:bavinck.gd.ed2:317`) is accepted and redirects (301) to the readable URL.
- How the parallel view, translation, and diff are selected on a passage page (query parameters vs. paths) is a reader-design question, deferred to that session. Identity is edition + passage; views are presentation.

## Consequences

- Footnotes citing Bron are readable without visiting Bron.
- The readable path and the URN must stay in lockstep; the mapping is mechanical (slugs are the URN components), so there is one source of truth.
- URL slugs are part of the permanent contract and are chosen with the same care as URNs: never renamed, only redirected.
