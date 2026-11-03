# ADR 0003 — Text format and identifier stack: TEI (CapiTainS), CTS URNs, DTS, IIIF

**Status:** Accepted — 2026-11-02

## Context

Per ADR 0001, Bron adopts the digital-humanities conventions for encoding, identifying, resolving, and image-linking texts rather than inventing a format.

## Decision

- **Encoding:** TEI P5 XML, following the CapiTainS conventions used by Perseus: one file per edition or translation ("version"), with a `refsDecl` declaring the citation hierarchy, plus the CapiTainS metadata files. TEI is the canonical form; plain text, JSON, and HTML are derived.
- **Identifiers:** CTS URNs under a `bron` namespace: `urn:cts:bron:<textgroup>.<work>.<version>:<passage>`. Textgroups and works use readable slugs (e.g. `bavinck.gd`); editions and translations are versions (`ed1`, `ed2`, `bron-eng`). Wikidata and VIAF identifiers for authors and works are carried in metadata, since no numeric registry exists for modern authors the way TLG/PHI numbers exist for the classics.
- **Sub-paragraph pointing:** CTS subreferences (`...:317@genade[2]` = the second occurrence of *genade* in §317). Sentences carry internal TEI `xml:id`s for alignment and provenance but never appear in public citations.
- **Resolution API:** DTS (Distributed Text Services).
- **Scan linking:** IIIF. Each page break in the TEI (`<pb/>`) points to a IIIF canvas; paragraph-to-region links use IIIF annotations. Bron points at a library's IIIF where one exists (Delpher, etc.) and hosts its own IIIF for public-domain scans otherwise.
- **Physical vs logical:** the logical structure (§, chapter, paragraph) is the identity. Page and line are anchors carried as metadata, except for works whose scholarly convention is page-based (ADR 0002).

## Consequences

- Bron texts are usable by any CapiTainS/DTS-aware tool on day one.
- TEI is verbose and the tooling is academic; agents will do the encoding, and validation (schema + CapiTainS checks) is part of the pipeline.
- Internal sentence segmentation can change on correction without breaking any public citation.
