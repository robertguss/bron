# PRD — Bron

*Bron* (Dutch): source; also spring, well.

**Status:** Draft v0.1 — captures the 2026-11-02 brainstorm; nothing here is final
**Owner:** Robert (personal project; public, open source)
**Working model:** Robert designs; AI agents build; humans and tools verify

---

## 1. One-liner

An open commons that gives English readers access to the primary sources of the Reformed and neo-Calvinist tradition in their original languages (Dutch, Latin, French, German) without requiring them to know those languages — original and translation side by side, every claim traceable to a page, every translation carrying its provenance.

Short form: **Perseus for the Reformed tradition.**

## 2. Problem

- The tradition's primary sources are mostly public domain and increasingly digitized (NRI's Kuyper and Bavinck archives, Delpher, DBNL, PRDL, archive.org), but they exist as catalog entries and PDFs — a library, not an engine.
- Most of the corpus is untranslated. Human translation projects (Davenant, RHB, Lexham, Brill) are excellent, slow, expensive, and copyrighted.
- What is translated is locked: the Bolt/Vriend Bavinck, the Giger/Dennison Turretin, the Battles Calvin cannot be used in an open resource.
- English-only pastors, seminarians, and scholars therefore read the tradition through a narrow, curated window. Bavinck's first-edition *Dogmatiek* has never been in English. Most of Kuyper has never been in English.
- Machine translation is now good enough to draft, but theology punishes fluent error: a plausible rendering of *subsistentia* or *habitus* can be doctrinally wrong. Fluency without verification is worse than nothing.

## 3. Vision

Open the original on the left, the transcription in the middle, English on the right. Tap any word for its lemma and gloss. Every scripture reference, every citation of Augustine or Aquinas, resolves to a link. Every English sentence shows whether it is a machine draft, human-reviewed, or anchored to a published translation. Ask an agent about the passage. Cite the passage with an identifier that will resolve forever.

Reading this way, an English reader absorbs the Dutch or Latin by osmosis — Loeb-style, but alive and open.

## 4. Questions underneath the project

- What does scholarship look like when an agent can read an entire tradition in its own languages?
- How little expert-human time does a trustworthy translation pipeline actually need, and where exactly must it be spent?
- Can translation decisions be made explicit, consistent, and auditable across a whole corpus (a controlled lexicon) rather than hidden inside each translator's head?

## 5. Goals

1. Make the primary sources *readable* by English readers with the original always visible.
2. Make every translation *trustworthy* through explicit provenance and human review, not through fluency.
3. Make every passage *citable* with stable, permanent identifiers.
4. Make the whole thing *open*: data, pipeline, and code, so others can reuse, extend, and re-run it.
5. Make the data the durable asset; the reader app is replaceable.

## 6. Non-goals (for now)

- Not a replacement for critical scholarly editions or peer-reviewed translations; it is a draft-and-verify commons that links to them.
- Not Greek/Hebrew biblical tools (plenty exist); scripture references link out.
- Not a general-purpose OCR product; transcription serves this corpus.
- Not a commercial product. No paywall, ever.
- Not shipping any copyrighted translation, even partially.

## 7. Users

| User | Need | Notes |
|---|---|---|
| Robert | Read Bavinck's periphery and first edition; research for his own writing | First user; dogfood |
| English-only pastors and students | Read the tradition beyond what's been translated | Primary public audience |
| Scholars (NRI, Bavinck Institute, Junius Institute, seminary faculty) | Citable texts, edition comparison, searchable corpus | Credibility depends on them |
| Reviewers (Dutch/Latin readers, esp. Westminster faculty and PhD students) | Fast correction workflow that respects their time | The scarce resource |
| Researchers / builders | Bulk data, stable API, reproducible pipeline | Open data makes this possible |

## 8. Principles

0. **Convention over invention.** Where a scholarly, digital-humanities, web, or industry convention exists, Bron adopts it. Bron invents only where nothing exists, and documents why. (ADR 0001)
1. **The data is the project.** TEI texts, alignments, lexicon, translations live in git under an open license. UIs come and go (Perseus has outlived three).
2. **Original always visible.** No English is ever shown without its source beside it.
3. **Nothing is trusted by default.** Every translated unit carries a provenance state. Review is explicit, never assumed.
4. **Citations never break.** Stable identifiers from day one; texts are versioned; a cited passage resolves forever.
5. **Verification over fluency.** Outside judges (existing translations, human reviewers, consistency checks), never the model grading itself.
6. **Reproducible.** Anyone can re-run scan → text → translation with the published pipeline, prompts, and lexicon.
7. **Open, and separable.** Data and code in separate repos under separate licenses so the texts can outlive the software.
8. **Build over the existing library, link back.** The NRI, PRDL, Delpher, and DBNL did the acquisition. Be the engine, not a competitor.

## 9. Corpus plan

### Phase 1 — Bavinck (start here)
- **Why first:** died 1921 (public domain everywhere); modern roman type (OCR nearly solved); Dutch MT is strong; NRI has the bibliography (800+ sources) and PDFs; the periphery is largely untranslated.
- **Gereformeerde Dogmatiek, both editions:** 1st ed. 1895–1901; 2nd ed. 1906–1911 (revised throughout; Gootjes: "differs in all sorts of ways from the first, but there are only a few changes in contents"). The English (Bolt/Vriend) translates the 4th printing, which reproduces the 2nd. The 1st edition has never been in English by a human translator; Monergism published an unverified AI auto-translation in 2026 (see `docs/research/2026-11-02-fact-checks.md`), which sharpens rather than weakens the case for the engine.
- **Open transcriptions:** all four 1st-edition volumes are proofread on Project Gutenberg; no open transcription of the 2nd/4th edition exists, so that is real transcription work.
- **Periphery:** articles (*De Bazuin* and other periodicals), lectures and orations, reviews, pedagogical and psychological writings, letters.
- **Marginalia and archive:** Bavinck's archive via NRI; handwritten material is a later phase (needs HTR).

### Phase 2 — Kuyper
- Died 1920; public domain. Enormous output (daily journalism for decades). Even after Lexham's 12-volume *Collected Works in Public Theology*, most remains untranslated (e.g., *Dictaten Dogmatiek*, *E Voto Dordraceno*, the journalism — status to verify).
- NRI holds the complete digitized archive (with Princeton and the VU's HDC).

### Phase 3 — Calvin (the calibration set)
- Use the *Calvini Opera* (Corpus Reformatorum, 59 vols., 1863–1900): a clean, public-domain, 19th-century critical edition — trivially OCR-able. First editions become a comparison layer, not the source.
- Public-domain English exists for much of Calvin (Beveridge and Allen *Institutes*; Calvin Translation Society commentaries). This is the Latin→English parallel corpus for teaching and testing the translation layer before trusting it on untranslated material.
- Untranslated remainder: many French sermons (*Supplementa Calviniana*), much correspondence.

### Phase 3b — Augustine (the stress test)
- Latin already digital (Migne's *Patrologia Latina*, augustinus.it); nearly fully translated (New City Press, copyrighted; NPNF, public domain).
- Little access to unlock; value is (a) proving the lexicon generalizes to patristic rather than scholastic Latin, and (b) the citation graph — everyone cites Augustine.

### Phase 4 — Post-Reformation scholastics
- Via PRDL (Junius Institute). Early-modern print: long s, ligatures, printed abbreviations, two-column layouts, blackletter for Dutch/German. This is where the hard OCR problem lives. Candidates (to verify what remains untranslated): Voetius, Polanus, Keckermann, Maccovius, Zanchi, Cocceius.

### Phase 5 — Archives and handwriting
- Correspondence, lecture notes, marginalia from the NRI archives. Requires HTR (Transkribus, Kraken/eScriptorium).

### Legal line for later authors
- **US:** works published 1930 or earlier are public domain (as of 2026); later works are murky.
- **EU:** author died 70+ years ago. Kuyper and Bavinck free everywhere; Schilder (d. 1952) free in the EU since 2023, murky in the US for post-1930 works; Dooyeweerd (d. 1977) and Vollenhoven (d. 1978) locked.

## 10. System components

### 10.1 Corpus and rights registry
- Catalog of works, editions, scans, sources (NRI, Delpher, DBNL, archive.org, e-rara, PRDL), with rights status per work and per source.
- Check terms of use for each source (NRI sources site, Delpher, DBNL) before bulk use.

### 10.2 Transcription (scan → text)
- Modern print (Bavinck, Kuyper, Calvini Opera, Migne): OCR + vision-model correction.
- Early-modern print: Kraken/eScriptorium or Transkribus, with vision models expanding abbreviations.
- Handwriting: HTR (later phase).
- **Output:** TEI-XML with page and line anchors back to the scan. Never plain text as the canonical form.
- Expect the NRI PDFs' existing OCR layers to be mediocre; re-read everything.

### 10.3 Text model and citation scheme
- **Designed 2026-11-02.** See `docs/text-model.md` and ADRs 0002–0005.
- Citations follow each work's scholarly convention; TEI P5 (CapiTainS) encoding; CTS URNs under `bron`; DTS resolution; IIIF scan links; readable canonical URLs; latest for reading, pinned (with Zenodo-DOI'd releases) for citing.

### 10.4 Alignment
- Edition-to-edition alignment (Bavinck 1st vs 2nd) at paragraph and sentence level, with change classification (added / removed / revised / moved).
- Source-to-translation alignment (original ↔ English).

### 10.5 Translation layer
- Agentic translation using a **controlled lexicon** of technical terms where each rendering is an explicit, documented, corpus-wide decision.
- Calibration before trust: translate works that already have trusted translations (public-domain ones openly; copyrighted ones privately as a judge), measure drift, feed drift back into the lexicon and prompts.
- Reviewer corrections become examples for future runs.

### 10.6 Lexicon
- Machine-readable controlled vocabulary for scholastic and neo-Calvinist terms (Latin, Dutch) with chosen English renderings, alternatives considered, rationale, and references.
- Public-domain lexica as inputs: Lewis & Short, Du Cange; modern ones (e.g., Muller's *Dictionary*) consulted, never copied.

### 10.7 Linking
- Scripture references resolved to canonical references (link out).
- Cross-references and citations (Augustine, Aquinas, the Fathers, confessions) resolved within the corpus where present.
- Citation graph across works.

### 10.8 Provenance and review
- Every translated unit carries a state: `machine-draft` → `human-reviewed` → `anchored` (to a public-domain published translation). States are visible in the reader.
- Reviewer workflow: a Dutch/Latin reader sees original + draft, approves or corrects a paragraph in seconds; corrections flow to the lexicon and examples.
- Possible model: seminary doctoral seminars reading Bavinck use the draft as the assignment; review happens as a byproduct of reading that would occur anyway.

### 10.9 Reader
- Parallel view: scan | transcription | English. Tappable lemmas with glosses. Provenance badges. Edition diff view. Ask-an-agent about a passage. Permanent citation links.
- Static-first publishing from the data repo; the app is replaceable.

### 10.10 Community and partners
- NRI (Utrecht), Bavinck Institute (Calvin Seminary), Junius Institute / PRDL, CCEL as precedent and possible ally, Westminster faculty and students as contributors.
- Talk to NRI and the Bavinck Institute early: the project is the open engine over their library, linking back.

## 11. First milestone — "The Bavinck Diff"

**Definition:** Both editions of the *Gereformeerde Dogmatiek*, transcribed to TEI, aligned paragraph by paragraph, every change rendered in English, published as a reading environment with provenance states and stable citations.

**Why this one:** bounded (four volumes, two editions), fully public domain, novel (nobody has it), useful to scholars, and it forces every core component: OCR, TEI, identifiers, alignment, translation with lexicon, provenance, reader.

**Built-in outside judge:** for 2nd-edition text, score machine drafts privately against the Bolt/Vriend translation to measure drift before trusting the pipeline on the untranslated 1st edition.

**Thin slice first:** one chapter (likely vol. 1 prolegomena, where revisions are heaviest) end to end on a public URL before scaling.

**Success criteria (draft):**
- A scholar can cite any paragraph of either edition with a permanent link.
- Every English unit shows its provenance state; reviewed share is tracked and visible.
- Measured drift against the held-out translation is reported, not hidden.
- Pipeline re-runs reproducibly from the published repo.

## 12. Verification strategy (outside judges)

1. **Parallel corpora:** public-domain pairs (Calvin Latin ↔ Beveridge/CTS) openly; copyrighted pairs (Bavinck ↔ Bolt) privately, as judges only.
2. **Human reviewers:** Dutch/Latin readers via the review workflow; seminary seminars.
3. **Consistency checks:** lexicon-driven term consistency across the corpus; flagged deviations.
4. **Reproducibility:** published pipeline, prompts, lexicon, and evaluation numbers.
5. **Never** the model grading itself as the final word.

## 13. Legal and licensing

- **Sources:** public domain originals only (Kuyper, Bavinck, Calvin, Augustine, pre-1931 publications in the US; author-death+70 in the EU).
- **Never ship** copyrighted translations (Bolt/Vriend, Battles, Giger/Dennison, New City Press, Lexham). Use privately for evaluation only.
- **Data license:** CC BY 4.0 or CC0 for texts, alignments, lexicon, translations.
- **Code license:** Apache-2.0 or MIT.
- **Repos:** data and code separated so the texts can outlive the software.
- **Ownership:** Robert's personal project — personal GitHub org, personal infrastructure, personal time. Obtain a short written acknowledgement from Westminster that this is an outside project, since the subject sits inside the employer's domain. Contributors (including faculty/students) contribute under the open license like anyone else (DCO or light CLA).
- **Source terms:** verify reuse terms for NRI sources site, Delpher, DBNL, e-rara before bulk ingestion.

## 14. Risks

| Risk | Mitigation |
|---|---|
| Fluent, wrong theology published | Provenance states; original always visible; calibration against judges; human review before "reviewed" state |
| Platform with no content | The Bavinck Diff first; one chapter end-to-end before any generalization |
| Mediocre existing OCR | Re-transcribe everything to TEI with anchors |
| Human review bottleneck | Seminar-as-review model; make review a seconds-per-paragraph task; open contribution |
| Identifier breakage | Design the citation scheme first; version texts; never renumber |
| Institutional entanglement | Written IP acknowledgement; personal infra; open license from day one |
| Scope creep (Kuyper, scholastics, archives) | Phased corpus plan; each phase gated on the prior one's verification numbers |
| Rights surprises on scans | Rights registry; check source terms; prefer PD scans on archive.org/Delpher |
| Scholars ignore it | Partner early (NRI, Bavinck Institute); ship something they'd cite |

## 15. Open questions (research areas for design sessions)

Each is a session of its own; order is a proposal.

1. ~~**Text model and citation scheme**~~ — done 2026-11-02; see `docs/text-model.md`. Open facts to verify are listed there.
2. **Corpus and rights** — inventory of Bavinck sources via NRI bibliography; what's translated; source terms; rights registry design.
3. **Transcription** — tool choice for modern print now and early-modern print later; TEI output; quality measurement.
4. **Alignment** — edition diff method and change taxonomy.
5. **Translation and lexicon** — model, prompts, lexicon format, calibration protocol, drift metrics.
6. **Provenance and review** — state model, reviewer UI, how corrections feed back.
7. **Reader** — parallel view, lemma/gloss, diff view, agent-ask, static publishing.
8. **Partners and community** — outreach to NRI, Bavinck Institute, Junius; contribution model; governance.
9. **Infrastructure** — hosting (personal VPS), pipeline runtime, cost of inference at corpus scale.
10. ~~**Name**~~ — decided 2026-11-02: **Bron**. The first milestone is "the Bavinck Diff" underneath it.

## 16. Glossary (seed)

- **Bron** — the project and the commons: Dutch for "source," also "spring" or "well."
- **TEI** — Text Encoding Initiative XML; the scholarly standard for encoded texts.
- **CTS URN** — Canonical Text Services identifier; stable, hierarchical citation scheme used by Perseus and the Homer Multitext.
- **HTR** — Handwritten Text Recognition (Transkribus, Kraken/eScriptorium).
- **Lexicon** — the project's controlled vocabulary of technical terms with explicit English renderings.
- **Provenance state** — the per-unit label recording how an English rendering was produced and whether it has been reviewed.
- **Outside judge** — any verification source other than the model itself: parallel translations, human reviewers, consistency tools.
- **The Bavinck Diff** — the first milestone: both editions of the *Gereformeerde Dogmatiek* aligned and rendered.

## 17. References

- Felix Rieseberg, "How to be more ambitious: A tutorial for humans with models" — https://felixrieseberg.com/how-to-be-more-ambitious-a-tutorial-for-humans-with-models/
- Neo-Calvinism Research Institute — https://www.neocalvinism.org/ ; sources — https://sources.neocalvinism.org
- Bavinck Institute (Calvin Seminary) — https://bavinckinstitute.org
- Post-Reformation Digital Library (Junius Institute) — https://www.prdl.org
- Delpher (KB, Dutch digitized books and periodicals) — https://www.delpher.nl
- DBNL (Digital Library of Dutch Literature) — https://www.dbnl.org
- Calvini Opera (Corpus Reformatorum) — scans on archive.org
- Augustine, Latin corpus — https://www.augustinus.it
- Perseus Digital Library — https://www.perseus.tufts.edu
- CCEL — https://www.ccel.org
- TEI — https://tei-c.org
- Transkribus — https://www.transkribus.org ; eScriptorium/Kraken — https://escriptorium.readthedocs.io
