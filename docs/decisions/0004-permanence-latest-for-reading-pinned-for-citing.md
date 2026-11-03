# ADR 0004 — Permanence: latest for reading, pinned for citing

**Status:** Accepted — 2026-11-02

## Context

Two conventions conflict. Scholarship cites fixed editions: "GD², 1908" means the same words forever. The web convention is that a URL shows the current state of a living resource. Bron's texts are living — OCR corrections and reviewed translations keep landing — so a footnote that silently resolves to different words years later would violate the scholarly convention while honoring the web one.

Living corpora that have faced this (Wikipedia; DH projects releasing through Zenodo) resolve it by separating reading from citing.

## Decision

- A bare Bron URL shows the **latest** text. Reading defaults to current.
- Every passage offers a **"cite this"** action that yields a permalink **pinned to a version**. Citing defaults to pinned.
- Pinned form: the readable URL with a `?v=<release>` parameter (Wikipedia's `oldid` convention, readable). `@` is not used for versions because CTS already uses it for subreferences.
- Bron cuts **numbered releases** of the data (semantic-ish versioning: `1.0`, `1.1`, …) and registers each with **Zenodo for a DOI**, so a scholar can cite "Bron 1.2" the way they would cite an edition.
- Identifiers are **never renumbered or reused**. If a paragraph is split or merged after publication, the old identifier remains and redirects (with a note), never 404s.
- When a reader arrives at a passage via a pinned link and the latest text differs, the page says so and offers both.

## Consequences

- Git history plus release tags is the versioning mechanism; no separate versioning system is invented.
- Every public page must know which release it is showing and whether the text has changed since.
- Zenodo integration is a release-process task, not a code task.
