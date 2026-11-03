# Text model and citation scheme

**Status:** Designed 2026-11-02 (design session 1). Decisions are recorded as ADRs 0001–0005 in `decisions/`; this document consolidates them into one reference and lists what remains to verify.

## 1. Governing principle

Convention over invention (ADR 0001). Everything below is an adoption, not a design, except where marked **Bron-specific**.

## 2. Identity layers

| Layer | Form | Audience | Stability |
|---|---|---|---|
| Human citation | the work's own scholarly convention: `GD² §317`, `Inst. 1.1.1`, `CO 2:123` | footnotes, readers | permanent |
| Readable URL | `/bavinck/gd/ed2/317` | anyone pasting a link | permanent (ADR 0005) |
| CTS URN | `urn:cts:bron:bavinck.gd.ed2:317` | tools, DTS API, metadata | permanent (ADR 0003) |
| Internal segment ID | TEI `xml:id` on `<p>` and `<s>` | pipeline, alignment, provenance | internal; never a public contract |

The first three are mechanically equivalent: the URL's path segments are the URN's components, and the human citation is the URN's passage rendered in the work's convention.

## 3. Hierarchy per work

Declared per edition in the TEI `refsDecl`. Known so far:

| Work | Edition / version | Primary hierarchy | Secondary index | Notes |
|---|---|---|---|---|
| Bavinck, *Gereformeerde Dogmatiek* | `ed2` (1906–11) | § | volume:page | § numbering believed continuous across volumes — verify |
| Bavinck, *Gereformeerde Dogmatiek* | `ed1` (1895–1901) | **unknown** | volume:page | verify whether usable § numbering exists; if not, volume:page is primary |
| Calvin, *Institutio* (1559) | via *Calvini Opera* | book.chapter.section | CO volume:column | universal convention |
| *Calvini Opera* (other works) | CR edition | volume:column | — | page/column is the convention |
| Augustine | existing OGL editions | book.chapter.paragraph | PL column | reuse existing `latinLit` URNs |
| Translations (any) | `bron-eng` etc. | inherits source | — | no structure of their own |

## 4. Units

- **Paragraph** (the smallest conventional unit of the work: §, section, paragraph) is the smallest citable unit.
- **Sentence** is the unit of translation alignment and provenance state. Sentences have internal IDs only.
- **Sub-paragraph public pointing** uses CTS subreferences: `317@genade[2]`. Survives re-segmentation; breaks (gracefully, with a message) only if the cited word itself is corrected.

**Bron-specific, internal:** sentence IDs are stable random identifiers assigned at first ingest and never reassigned. A text correction keeps the ID and bumps a revision; policy decides whether a correction resets the sentence's provenance state (to be settled in the provenance session).

## 5. Logical vs physical

- Logical structure is the identity. Page, column, and line are anchors (TEI `<pb/>`, `<cb/>`, `<lb/>` with `facs` → IIIF canvas), carried as metadata.
- Exception: works whose convention is page- or column-based (ADR 0002). There the page *is* a logical level.

## 6. Scans

- IIIF Image and Presentation APIs.
- Prefer the holding library's IIIF (Delpher, Munich, e-rara) where it exists; host Bron's own IIIF for public-domain scans otherwise.
- Paragraph → region links as IIIF annotations, produced by the transcription pipeline.

## 7. Versioning and permanence (ADR 0004)

- Latest for reading; pinned for citing.
- Pinned form: `?v=<release>`.
- Numbered releases of the data repo, each with a Zenodo DOI.
- Identifiers never renumbered or reused; splits and merges leave redirects.
- Pages state when the text differs from the pinned version a reader arrived with.

## 8. URLs (ADR 0005)

```
/{textgroup}/{work}/{version}/{passage}            /bavinck/gd/ed2/317
/{textgroup}/{work}/{version}/{from}-{to}          /bavinck/gd/ed2/317-320
/{textgroup}/{work}/{version}/{passage}@{word}[n]  /bavinck/gd/ed2/317@genade[2]
/{textgroup}/{work}/{version}/page/{vol}.{page}    /bavinck/gd/ed2/page/2.350   → redirects to containing passage
...?v={release}                                    pinned
/urn:cts:bron:{textgroup}.{work}.{version}:{passage}  → 301 to readable
```

Views (parallel, translation, diff) are presentation and are decided in the reader session; they never change identity.

## 9. Related conventions adopted

- Scripture references: OSIS IDs (`Rom.8.28`), linked out.
- Authors and works: Wikidata and VIAF IDs in metadata.
- Provenance states (for the provenance session): XLIFF 2 segment-state vocabulary (initial → translated → reviewed → final) rather than an invented one.
- Resolution: DTS. Encoding: TEI P5 + CapiTainS.

## 10. Facts to verify before locking Bavinck

1. Does GD 1st edition carry usable § numbering? If not: volume:page primary.
2. Does GD 2nd edition § numbering run continuously across all four volumes, and does it match the bracketed numbers in the English edition?
3. Does Delpher (or whichever library holds the GD scans) serve IIIF for them?
4. Which Augustine works already have Open Greek and Latin / `latinLit` URNs, and which editions those URNs point to.
5. Current state of the DTS specification and reference implementations (the spec has had several drafts).

## 11. Out of scope here

Alignment method (edition diff), transcription tooling, translation and lexicon, provenance workflow, reader design, partners, infrastructure. Each has its own session (PRD §15).
