# ADR 0017 — One-target alignment links, and the rights vocabulary

**Status:** Accepted — 2026-11-03. Amends ADR 0006 (Representation) and ADR 0012 (Rights vocabulary).

## Context

Two details of accepted decisions turned out not to match the standards they cite.

- **ADR 0006** represents an `insert` or `delete` alignment as a `<link>` with one target, the unit that exists on one side only. The structural concordance already does this (for example `<link type="insert" target="bavinck.gd.ed2.xml#par-9"/>`). TEI's own Schematron rule for `<link>` requires at least two targets. RelaxNG validation alone does not catch this, so Bron's files would pass the schema while breaking a TEI constraint.
- **ADR 0012** lists the "Public Domain Mark" among rightsstatements.org statements. It is a Creative Commons tool. rightsstatements.org's own documentation points to Creative Commons for it.

## Decision

- **One-target `insert` and `delete` links are a documented Bron deviation from TEI's `<link>` constraint.** Bron's validator enforces two or more targets on every `<link>` except `type="insert"` and `type="delete"`, which must have exactly one. Each alignment file states the deviation in its `encodingDesc`. Bron's alignment files are described as valid against `tei_all` with this one documented Schematron deviation, never as plain TEI-valid.
- **Source rights use standard URIs from two vocabularies:** rightsstatements.org statement URIs, and the Creative Commons Public Domain Mark and CC0 URIs. The registry's schema accepts both.
- **Three things are recorded separately:** a source's copyright status, a site's access and reuse terms, and the status of Bron's own outputs (ADR 0014).

## Consequences

- The concordance keeps its content and its simplest reading: an insertion points at what was inserted.
- A TEI tool running the full `tei_all` Schematron will report the one-target links. The deviation note in each file says why.
- A later Bron ODD customization could make the deviation formal, if one is ever written.
