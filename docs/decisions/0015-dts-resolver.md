# ADR 0015 — DTS is served by a small read-only resolver

**Status:** Accepted — 2026-11-03. Amends ADR 0011 (Hosting, and its consequence about dynamic features).

## Context

ADR 0011 planned DTS 1.0 Level 0 as static files, with any dynamic feature coming "later behind a small service, if ever". Working that design out for GD¹ showed static files cannot meet Level 0. Level 0 exempts only Navigation `start`/`end`. Document range requests (`start`/`end`) and every valid `down` value are still required, and a finite set of pre-generated files cannot answer them. Calling a static build "Level 0 conformant" would have been false.

ADR 0004 also requires that a retired or split identifier "remains and redirects (with a note), never 404s". A static file tree has no way to answer a request for an identifier that no longer exists in the text.

## Decision

- **The reader stays static.** Reader pages, the search index and scans remain files served from a static host (ADR 0010, ADR 0011).
- **DTS is a small read-only Python service** (`bron serve`) over the canonical TEI in `bron-data`. It builds an in-memory index of collections and passages at startup. It has no database, no write path and no generated files, so its only input is the data repo.
- **It answers every DTS 1.0 Level 0 call**, including Document ranges and any `down` value. It also answers Navigation `start`/`end`, because the upstream DTS validator's range tests depend on it.
- **Retired and redirected identifiers resolve.** A redirected identifier answers with its replacement (HTTP 301, or 300 for a split). A retired identifier answers HTTP 410 with a tombstone naming the identifier, the reason and the date. The DTS spec is silent here, so Bron documents the behavior with the service.
- **Errors follow the spec's 400 and 404 conditions**, with RFC 9457 `application/problem+json` bodies, since the spec defines no error body.
- **Stack:** FastAPI on uvicorn, Python 3.15.
- **Hosting and supervision** of the service on the VPS are decided with the first public deployment (M6). Until then it runs locally and in CI.

## Consequences

- First-release operations are copying files plus running one stateless process. The process can be restarted or moved freely, because everything it serves comes from the data repo.
- CI starts the same service the public will use and runs the upstream validator against it with no tests excluded.
- Mirroring Bron's data stays trivial. Mirroring the DTS API means running the service, not copying a directory.
