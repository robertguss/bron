# Fact checks for the text model (2026-11-02)

Five facts flagged in `docs/text-model.md` §10, checked against primary sources where possible. Confidence is stated per item. Items 1–2 were checked against the texts themselves (Project Gutenberg transcriptions and the NRI tables of contents), not against prose about them.

## 1. Does GD 1st edition have usable § numbering? — YES, two levels

**Finding.** The first edition (Kampen: Bos, 1895–1901) has a two-level logical structure of its own:

- **§ 1–56**, numbered continuously across all four volumes: §1–19 in vol. 1, §20–34 in vol. 2, §35–46 in vol. 3, §47–56 in vol. 4. Above the §§ sit four *Delen* and eleven *Hoofdstukken*.
- **Numbered subparagraphs within each §, restarting at 1 in every §.** E.g. §1 runs 1–5, then §2 begins again at 1. (Verified in the Gutenberg transcription of vol. 1: §1 ¶1–5, §2 ¶1–3, §3 ¶1–4 …)
- Erratum in vol. 2: the printed text misnumbers §§27–33; the table of contents is authoritative ("Naar deze opgave gelieve men de foutieve nummering van de paragrafen 27-33 in den tekst te herstellen").

**Consequence for the citation scheme.** GD¹ is cited by `§.¶` (e.g. `GD¹ 3.2` = §3, subparagraph 2), with volume:page as the secondary index (which is how Bremmer, Veenhof and Gootjes cite it in the secondary literature). Page is not needed as the primary level.

**Bonus.** All four volumes of the first edition exist as proofread Distributed Proofreaders transcriptions on Project Gutenberg: vol. 1 [#51052](https://www.gutenberg.org/ebooks/51052), vol. 2 [#67966](https://www.gutenberg.org/ebooks/67966), vol. 3 [#68527](https://www.gutenberg.org/ebooks/68527), vol. 4 [#69005](https://gutenberg.org/ebooks/69005). Page breaks are marked inline (`[IV]`, `[2]`, …). This removes most of the OCR work for GD¹; what remains is conversion to TEI with anchors and verification against the DBNL scans.

**Confidence.** High. Sources: Gutenberg vol. 1 text; NRI "1e druk" TOC; NRI PDF of vol. 4 (1901); DBNL catalog.

## 2. Does GD 2nd edition numbering run continuously, and match the English? — YES

**Finding.**

- The second edition (1906–1911) has **Par. 1–62** (in fact 63, because Par. 13 is used twice: "Openbaring en Heilige Schrift" and "De Theopneustie van de Schrift"), and **subparagraphs 1–580 numbered continuously across all four volumes**, with at least one split: **427a / 427b**. Vol. 1 ends at #160, vol. 2 at #306, vol. 3 at #432, vol. 4 at #580.
- The Baker *Reformed Dogmatics* (Bolt/Vriend, 2003–2008) **retains the subparagraph numbers in square brackets** ("##161–306 in square brackets in the text, used in the second and subsequent Dutch editions") and **drops the Par. numbers and the four major divisions**. Cross-references in the English cite by `#`. The one-volume abridgement also keeps the bracketed numbers.
- The 3rd (1918) and 4th (1928–30) editions reproduce the 2nd edition's text; the 4th has different pagination.
- Gootjes (1990) notes the 2nd edition "differs in all sorts of ways from the first, but there are only a few changes in contents," citing Bremmer (1961, 151ff., 367) for a comparison. Expectation for the Bavinck Diff: many structural and stylistic changes, fewer doctrinal ones. That is still valuable (nobody has published the diff), but it tempers the "discovery" framing.

**Consequence for the citation scheme.** GD² is cited by **subparagraph #** (e.g. `GD² #317`), which is what the English edition's readers already use; Par. and volume:page are secondary indexes. Non-integer identifiers (`427a`) exist in the convention, so the scheme must allow them. GD¹ `§.¶` and GD² `#` are different schemes; the Diff needs an explicit alignment table, not a shared key.

**Confidence.** High. Sources: NRI "2e druk" TOC with subparagraph numbers (sources.neocalvinism.org/49); Baker RD vol. 2 editor's preface; Gootjes, "The Structure of Bavinck's Reformed Dogmatics" (Radix 1990, tr. Pol).

## 3. Does Delpher serve IIIF for the GD scans? — NOT YET, as far as can be found

**Finding.** The KB joined the IIIF Consortium in February 2025 and states it intends to publish its images via IIIF. A 2019 KB Lab post describes an internal wrapper supporting IIIF Image API 2.1 (level 1) that they "hope to expose in the near future." No public IIIF manifest or Image API endpoint for Delpher *books* was found. The GD¹ scans are on **DBNL** (KB-run) as downloadable PDFs (~29–32 MB per volume); DBNL labels the title "mogelijk auteursrechtelijk beschermd," which appears to be a cautious default (Bavinck d. 1921), not an assertion.

**Consequence.** Plan on Bron hosting its own IIIF (Image + Presentation) for the public-domain scans it uses, and revisit if the KB publishes endpoints. Delpher's separate image bank (geheugen.delpher.nl) is being shut down in October 2026, unrelated but worth knowing.

**Confidence.** Medium (absence of evidence). Sources: netwerkdigitaalerfgoed.nl (Feb 2025); lab.kb.nl OpenJPEG post; kb.nl news; DBNL title pages.

## 4. Which Augustine works already have CTS URNs? — Most of them, at work level

**Finding.** Augustine is textgroup **`urn:cts:latinLit:stoa0040`** in the Perseus Catalog. Work-level URNs exist for the large majority of the corpus, e.g. Confessiones `stoa0040.stoa001`, De civitate dei `stoa0040.stoa003`, De fide et symbolo `stoa0040.stoa006`, Epistulae `stoa0040.stoa011`, Contra Faustum `stoa0040.stoa024`, De Genesi ad litteram `stoa0040.stoa042a`, De Trinitate (to confirm its number). Edition-level texts are uneven: Scaife/ATLAS lists one text for Confessiones, De civitate dei, De fide et symbolo and some others; many works have a work URN but no CTS-compliant edition yet (the canonical-latinLit wiki notes files ending in "1" are often not yet compliant).

**Consequence.** Bron reuses `stoa0040.<work>` URNs for Augustine and adds its own edition version where OGL has none, following the CapiTainS convention for version identifiers (`bron-lat1`), e.g. `urn:cts:latinLit:stoa0040.stoa003.bron-lat1` for a PL-based De civitate dei. Per-work edition availability is a lookup at ingestion time.

**Confidence.** High for the textgroup and the listed work URNs; medium for edition coverage. Sources: catalog.perseus.org; atlas.perseus.tufts.edu; scaife.perseus.org; PerseusDL/canonical-latinLit wiki; capitains.org guidelines.

## 5. Is DTS stable? — YES, 1.0 since February 2026

**Finding.** Distributed Text Services **1.0 was published 13 February 2026** (dtsapi.org; GitHub tag v1.0, 16 Feb 2026; Zenodo record 18661951). Four endpoints: Entry, Collection, Navigation, Document. Reference implementations: MyDapytains (Python/Flask), DoTS (BaseX, Biblissima+/ENC), SCDH dts-transformations (XSLT); a validator suite exists. The spec defines **Level 0 "static-site conformance"** (everything except `start`/`end` range queries), explicitly so that fully compliant implementations can be generated statically.

**Consequence.** Bron can be a DTS 1.0 Level 0 server from static files, which matches the static-first publishing principle exactly; Level 1 ranges can come later behind a small service.

**Confidence.** High. Sources: dtsapi.org/specifications; GitHub release v1.0; Zenodo; Balisage 2026 paper (Scott et al.).

## Landscape note: machine translations of Bavinck already exist

Monergism Books released in 2026 free PDF "auto-translated" editions of (a) the **first edition**, taken from the Gutenberg transcriptions and run through an OpenAI model, and (b) the **fourth edition**, transcribed from facsimiles and translated with a Claude model, with AI-generated explanatory footnotes. Monergism claims copyright ("all rights reserved") on these, notes they are not at the level of the professional translation, and warns of errors. No provenance per sentence, no alignment, no citations beyond page markers.

Implications for Bron:
- Unverified AI translation of public-domain Bavinck is no longer novel. The contribution is the engine: alignment, provenance, review, citations, lexicon. This confirms the thesis in PRD §2.
- Bron produces its own transcription of the 2nd/4th edition Dutch; there is no open proofread transcription of it (Gutenberg has only the 1st edition). Monergism's transcription is not reusable.
- The NRI's "2e druk" pages list every subparagraph number; registered users may have access to text. Contact: Dmytro (Dima) Bintsarovskyi, TU Kampen/Utrecht, named on the page as the maintainer.
