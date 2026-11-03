# ADR 0011 — Infrastructure: static output, static IIIF, Python pipeline, CI that guards citations

**Status:** Accepted — 2026-11-02

## Decision

- **Hosting:** the reader is static output served from Robert's own VPS or any static host. No server process is required for the first release; DTS 1.0 Level 0 endpoints and the search index are files.
- **Scans:** static IIIF, Image API level 0 (pre-generated tiles and `info.json` per page) and Presentation manifests as static JSON, served beside the HTML. No image server.
- **Pipeline language:** Python, because the digital-humanities toolchain is Python (lxml, MyCapytain, CapiTainS validators, Kraken, the DTS validator). The reader build may use a different stack; its contract is the TEI, the stand-off files and the DTS endpoints.
- **CI (GitHub Actions) on the data repo:** TEI schema validation, CapiTainS and DTS validation, alignment reconciliation checks, identifier stability checks (no renumbering, no reuse), and provenance consistency. A pull request that would break a citation cannot merge.
- **Releases:** git tags on the data repo; Zenodo DOI per release (ADR 0004).
- **Compute:** OCR locally on the Mac or on short-lived cloud instances; translation and judging through frontier-model APIs; order of magnitude a few hundred dollars per full pass of GD² with two translators and a judge.
- **Secrets and private judge material** (API keys, the Bolt digital text) never enter any repo; they live on Robert's machine and in CI secrets.

## Consequences
- First-release operations are copying files; the project can be mirrored or forked trivially, which is part of being a commons.
- Level 1 DTS (range queries) and any dynamic features come later behind a small service, if ever.
