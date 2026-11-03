# ADR 0001 — Convention over invention

**Status:** Accepted — 2026-11-02

## Context

Bron is one person plus agents building a scholarly commons that must be trusted by scholars and must outlive its software. Every invented identifier, format, or workflow is something a scholar has to learn and something that can rot.

## Decision

Where an established convention exists — in scholarship, in digital humanities, in the web, in the translation industry — Bron adopts it rather than designing its own. Bron invents only where no convention exists, and documents why.

Rough order of authority when conventions compete: the scholarly convention for the specific work or tradition first; then the digital-humanities convention (TEI, CTS, DTS, IIIF, OSIS); then general web convention.

## Consequences

- Most design questions become lookups: "what does Perseus / CCEL / TEI / XLIFF do?"
- Bron's identifiers, formats and citations are legible to people who have never heard of Bron.
- Some conventions are ugly or dated (CTS URN syntax, TEI verbosity). Bron accepts that cost and hides it behind readable surfaces where web convention allows.
- When two conventions conflict (e.g. fixed scholarly editions vs. living web text), the conflict is resolved explicitly in an ADR, not silently.
