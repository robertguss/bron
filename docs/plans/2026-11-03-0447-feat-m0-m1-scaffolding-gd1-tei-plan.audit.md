# Audit: M0 Scaffolding and M1 GD1 in TEI

- **audit_of:** `docs/plans/2026-11-03-0447-feat-m0-m1-scaffolding-gd1-tei-plan.md`
- **date:** 2026-11-03
- **auditor:** T3 Code / Codex harness, gpt-6-astra
- **mode:** interactive
- **capabilities:** subagents yes, web yes, file writes yes, shell yes
- **draft independence:** compromised: the parent read the mixed Goal Capsule, including means and execution details, before a fresh child produced its independent draft without reading the plan or ADRs.
- **target repo:** `/home/exedev/bron` at `535515d50ea473e8bf791b672679ea806896475c`, clean before audit
- **notes:** All 27 tracked files reviewed. No implementation exists. The external data repository and surviving original research evidence were also inspected. The user explicitly permits challenges to accepted decisions and a small API service if justified. This report does not change those decisions or authorize deployment.

## Verdict

**Rethink** (14 of 71 ledger entries unverifiable)

Keep the durable TEI data, scholarly citation scheme, separate repositories, pinned tooling and M0–M1 scope. Reconsider the static-only API mechanism: the proposed filename enumeration cannot fulfill its advertised request contract, and the underlying infrastructure ADR repeats that premise. The remaining issues principally require stronger citation lifecycle rules, accurate source evidence, and fuller conversion/validation acceptance criteria; they do not justify restarting the whole project.

### Top issues

1. **PA-1:** The static API omits valid DTS requests; deselecting tests cannot establish conformance.
2. **PA-2:** Retiring or reusing an identifier can pass CI while breaking the citation promise.
3. **PA-3–PA-4:** Existing alignment data conflicts with the proposed validation and reference rules.
4. **PA-5, PA-7:** Source-rights interpretation and conversion coverage need correction before ingestion.

## Findings

### PA-1. The static-only API cannot satisfy the advertised DTS contract

- **Severity:** High
- **Category:** `approach`
- **Evidence:** L26–L31; P:98,140–151; ADR0011:7,17. DTS Level 0 exempts Navigation ranges, not Document ranges, and valid beyond-depth navigation is not covered by the generated files.
- **Suggested fix:** Revise ADR0011 and KTD6–7 around a small read-only resolver over canonical TEI or generated indexes. Keep reader pages and bulk exports static. Require Document ranges, valid high down values, explicit headers, invalid-request behavior and resource/tree handling in integration tests; use upstream tests as supplementary evidence. Prototype the service on the same small fixture before committing to a framework. If static-only is retained, label it a partial export API and revise the claimed outcome instead.

This finding challenges the delivery mechanism, not TEI, CTS or the separation of code and data. The specification itself promotes static implementations, so this is an internal tension worth documenting rather than assuming away. With the current finite filename scheme, a valid down=99 request has no response file. User confirmation now permits evaluating a service; operating simplicity remains a tradeoff to test.

### PA-2. The citation guard permits disappearing citations and identifier reuse

- **Severity:** High
- **Category:** `missing-work`
- **Evidence:** L7–L10,L22; P:95,138,152,391–398; docs/decisions/0004-permanence-latest-for-reading-pinned-for-citing.md:17.
- **Suggested fix:** Make retirement history append-only against base; validate replacement existence, chains, cycles and split/merge destinations. Produce resolvable legacy responses or explicit durable tombstone pages retaining the old identity and explanation. Compare stable source-node identity as well as public labels, with reviewed exceptions for editorial corrections. Test record deletion plus reintroduction, same-set numbering swaps, and full edition removal. Check both citation declarations resolve each label to the same unit.

Concrete bypass: retire 3.2, then in a later PR delete that retirement record and add 3.2 back. The base has no 3.2 to lose and the current record no longer forbids it. Separately, the proposed retirement-without-replacement test passes while the DTS builder generates no old-identifier response. Do not use text hashes as immutable content: legitimate corrections must remain possible.

### PA-3. Passing RelaxNG will conceal applicable TEI violations

- **Severity:** High
- **Category:** `false-claim`
- **Evidence:** L20–L21,L56; P:97,131–138,499; official TEI 4.12 link and citeStructure constraints.
- **Suggested fix:** Either run relevant TEI Schematron or enumerate and enforce the applicable constraints in Bron. Resolve how insert/delete alignments with one target are encoded: a validated documented customization or a standard representation, rather than claiming uncustomized TEI validity. Test single-target links and invalid citeStructure match patterns.

The omitted rules affect existing alignment content and the planned citation declarations. Moving notes out of link fixes its empty content model but does not fix the rule requiring at least two targets. That is an upstream representation decision in ADR0006 as well as an implementation concern.

### PA-4. The existing concordance still fails the planned header and link contract

- **Severity:** High
- **Category:** `missing-work`
- **Evidence:** L57–L58; P:132,135,380,412,487–499; [actual concordance](https://raw.githubusercontent.com/robertguss/bron-data/main/alignments/bavinck.gd.ed1--ed2.structure.xml).
- **Suggested fix:** Include the concordance in U7’s authoritative files and allow an encoding-only header update with its actual CC BY4.0 status. Define local versus external reference validation. Correct relative paths or supply a standards-valid base/catalog mapping, and explicitly allow-list genuinely deferred GD2 resources. Preserve alignment judgments and provenance.

Its publication statement currently has no availability element. Also, a basename target in alignments resolves relative to alignments, whereas the edition will live under data/bavinck/gd. A custom checker that searches by basename could pass data other TEI tools cannot resolve. Neither change requires silently altering the scholarly concordance.

### PA-5. DBNL’s terms do not justify the plan’s blanket linking-only restriction

- **Severity:** High
- **Category:** `false-claim`
- **Evidence:** L40–L42; P:167,312,501; Source:168; [DBNL title-specific terms](https://www.dbnl.org/titels/gebruiksvoorwaarden.php?id=bavi002gere01), copyright conditions and expired-copyright reuse.
- **Suggested fix:** Record the conditions accurately, assess the exact source copy and contributors, and keep database/bulk-download terms separate from work copyright. Treat linking-only as an explicit temporary project choice if desired. Amend ADR0003 with a staged PDF-anchor exception or deliver canvas links; do not cite the conditional terms as proof that IIIF hosting is prohibited.

This audit does not establish blanket permission to republish every DBNL scan. It establishes that the cited evidence does not support the asserted prohibition. Revisit the underlying decision using the source-copy rights record, while retaining attribution and the independent bulk-use check.

### PA-6. The rights schema excludes the project’s chosen public-domain vocabulary

- **Severity:** Medium
- **Category:** `consistency`
- **Evidence:** L14; P:153,411,415; docs/decisions/0012-corpus-and-rights.md:8; [official vocabulary guidance](https://rightsstatements.org/en/documentation/).
- **Suggested fix:** Allow the selected RightsStatements URIs and Creative Commons PDM/CC0/license URIs where semantically appropriate. Separate source rights, access/use conditions and Bron’s output status. Test a real public-domain source record and correct ADR0012’s attribution of PDM.

A host-name-only validator would reject the Creative Commons Public Domain Mark or encourage inventing a nonexistent rightsstatements.org equivalent.

### PA-7. Conversion lacks rules for footnotes and the fourth volume’s back matter

- **Severity:** High
- **Category:** `missing-work`
- **Evidence:** L36,L65; P:162,522–526; docs/decisions/0007-transcription.md:29; vol4 Gutenberg source contents and footnotes.
- **Suggested fix:** Add explicit source-region boundaries and conversion rules for front matter, main text, footnotes, the extended contents and indexes. Specify back-matter retention and whether it is uncitable. Preserve note callouts and note text exactly once, without treating note numbers or index entries as new subparagraphs. Add real fixtures at body-to-back transition, a long note, and lettered heading transitions.

The rule that unnumbered text follows the current subparagraph is insufficient at these boundaries. A parser could attach indexes to the last theological passage or lose notes while still producing schema-valid XML. The stated following-paragraph versus heading-opens-next-subparagraph rules also need one consistent source-order example.

### PA-8. Page-map confidence is overstated and needs an explicit verification artifact

- **Severity:** Medium
- **Category:** `false-claim`
- **Evidence:** L37–L39,L45,L66; P:165,170,523–524; /tmp/gdscripts/off.py:1; Source:183,195,199,203.
- **Suggested fix:** Describe +10/+6 as OCR-supported offsets until every required mapping is accounted for. Preserve PDF hashes and a per-page map with provenance, unmatched-page list and reviewed exceptions. Verify volume starts, chapter starts, corrected headings, page 484’s malformed HTML label, and the unresolved section 5 numbering against scans before final conversion.

The offsets have substantial support; there is no evidence here that the offsets themselves are wrong. The problem is claiming exhaustive measurement from a script that tallies numeric first/last OCR lines. Page-count completeness alone cannot establish that every break lies at the correct word.

### PA-9. Language tagging promises exhaustive coverage but measures only precision

- **Severity:** Medium
- **Category:** `consistency`
- **Evidence:** L51–L52,L67; P:58,183,552–569,604; Source:41,118.
- **Suggested fix:** Choose either exhaustive tagging with an explicit review/completion step, or an honestly limited machine-assisted annotation requirement. Measure missed foreign spans as well as false tags on an independently annotated sample; include short quotations and spans outside typographic candidates. Pin the chosen library/model/configuration and preserve tag provenance.

Leaving short spans untagged is a defensible conservative policy, but it contradicts every span. Source tag counts also do not prove volumes 3–4 are complete. The provenance distinction already in the plan is useful and should remain.

### PA-10. Reproducibility depends on an unproven archival service outcome

- **Severity:** Medium
- **Category:** `assumption`
- **Evidence:** L49–L50,L67; P:178–181,500,520,541–543.
- **Suggested fix:** Before making byte-identical re-ingest an acceptance promise, secure and verify all four exact source byte streams in durable storage with recorded hashes. Treat Wayback as one possible copy, not the sole guaranteed retention mechanism. Record a fallback if capture fails; pin parser/model resources and distinguish initial-ingest reproduction from later canonical editorial history.

The live-source hash failure path is well designed. The missing premise is that a future raw archive capture will succeed and remain retrievable. Because that premise is unverifiable, this finding is Medium rather than High. Do not silently add archived source blobs to either repository against the declared scope.

### PA-11. The sample-error figure lacks a reproducible reading and counting protocol

- **Severity:** Medium
- **Category:** `missing-work`
- **Evidence:** L4,L54–L55; P:189–194,601–608; original user approval at Parent:129–132.
- **Suggested fix:** Keep the approved agent-produced, nongating report, but define sample population/strata/selection algorithm; diplomatic versus corrected reading; note inclusion; hyphenation, whitespace and Unicode normalization; denominator; and how insertions/deletions are counted. Report textual error separately from tag/page-encoding errors and preserve page-level comparisons plus confirmation provenance.

An OCR layer agreeing with an agent is useful corroboration, not automatically human ground truth or statistical independence. Label this an exploratory residual-discrepancy estimate unless a suitable ground-truth protocol is supplied. Do not retroactively impose a human-review gate that the user explicitly declined for this milestone.

### PA-12. CI needs a precise baseline and merge-state contract

- **Severity:** Medium
- **Category:** `risk`
- **Evidence:** L12,L60,L62–L63; P:152,435,462,497,502; [GitHub protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches).
- **Suggested fix:** Specify base/current-main/candidate-merge handling; require an up-to-date branch or a verified merge-queue equivalent; test concurrent PRs, first push and multi-commit push. Define nested fixture base paths and fail closed on missing baselines in CI. State document-order sorting explicitly. Review workflow/action-pin edits as guard changes.

GitHub can enforce admin restrictions as planned, but the precise configuration is not supplied. This is a conditional risk, not a claim that a live branch is currently misconfigured. Testing a post-merge push cannot retroactively prevent a bad merge.

### PA-13. Milestone boundaries obscure what is delivered and defer a dependency too late

- **Severity:** Medium
- **Category:** `consistency`
- **Evidence:** L5,L68–L69; P:80–90,631–632; docs/roadmap.md:14,29,35,41.
- **Suggested fix:** Say that M0–M1 proves local/CI resolution and M6 delivers public access. Distinguish ingest completion from M1 completion including U11. Move sentence segmentation/ID assignment to before or within M4, retaining edition sentence alignment in M5. Record the PDF/IIIF staging decision alongside these boundaries.

There is no need to add a public deployment to this audit’s approved scope. The wording should stop promising it. Likewise, the translation pilot already needs source sentence IDs even though edition alignment comes later.

## Pre-mortem

- A third-party client follows valid DTS parameters, receives 404, and cannot use Bron despite green CI. The finite generation scheme and excluded tests hid incomplete coverage (PA-1).
- A maintainer retires an identifier, later removes the record, and inadvertently reuses its number. Existing citations fail or point at different text while set-based checks pass (PA-2).
- The first real data PR cannot pass its own rules. Implementers either weaken checks or improvise an undocumented TEI dialect because the concordance was never validated against the whole intended contract (PA-3–PA-4).
- Conversion looks plausible on3.2 but mishandles notes and indexes. Schema validity and a few fixtures fail to establish content preservation across all four volumes (PA-7).
- A published low error figure combines editorial corrections, language tags and transcription errors under an unspecified denominator. Later reviewers cannot reproduce or interpret it (PA-8–PA-11).

## Open questions

The user has clarified the audit scope and located the original research. The remaining items below are evidence or implementation questions, not claims that nonexistent code should already work. Do not convert them into favorable assumptions or require the user to guess technical results.

- **L12 — Merge-base validation alone protects against intervening main changes:** Exact checkout/merge-result strategy and strict up-to-date requirement are unspecified; P:152,462,497,502.
- **L25 — No other reusable generator or mature Python option exists:** Research examined several alternatives; ecosystem-wide absence and maturity are not established by that search. They are selection judgments, not verified facts.
- **L29 — Uploading colon-bearing paths needs an archive workaround:** Plan cites upload-artifact behavior without a version/source. Archive packaging is sensible independently; actual selected action must be checked.
- **L31 — Exact upstream validator behavior is pinned and established:** P:150 leaves commit to implementation; historical research used main. :229 records 3 failed, 11 passed, 19 skipped, not a fully passing final prototype.
- **L33 — Pinned dependencies are proven on CI Python 3.12 and 3.13:** Framework:89 tested 3.14.7; upstream matrix through 3.12 at :261. Future CI matrix is an appropriate verification task, not an observed result.
- **L41 — No usable DBNL IIIF/per-page image service exists:** Unsuccessful discovery is not absence proof; Source:150 even records thumbnails. PDF fallback can be chosen without claiming universal absence.
- **L45 — Vol1 section 5 genuinely lacks 7 in print:** Source:246,264,268,272,276 never establish this visually. Plan correctly leaves it as a pre-conversion investigation.
- **L47 — Removing bidi controls preserves intended Hebrew rendering:** Controls are presentation data, but no captured TEI/client rendering comparison proves the downstream effect. Preserve script text and test direction handling.
- **L49 — All four hash-identical raw Wayback captures can be obtained:** No matching archive URLs/hashes supplied or successful capture demonstrated; P:500 requires a future external service action.
- **L55 — Page text comparison produces an interpretable residual-error figure:** P:191,603–604 do not define sic/corr reading, notes, hyphenation, combining marks or denominator. These must be specified before measurement.
- **L60 — Sorting response members necessarily preserves source order:** P:435 does not specify sort key; P:439 requires document order. Lexical sorting would put 3.10 before 3.2; specify source ordinal.
- **L62 — Base checkout works identically for nested fixtures and actual data repositories:** P:462 does not specify fixture subpath on base checkout, empty initial push before SHA, or merge-result handling. Acceptance scenarios must settle these.
- **L67 — Language identification is reproducible from the specified inputs:** Library, model/resource hash, confidence/floor and randomness settings remain unchosen at P:560; pin before reproducibility acceptance.
- **L71 — Replacing static-only API with a small service is within audit scope:** User-asserted preference in this audit: allowed if evidence justifies it; this authorizes recommendation, not proof of implementation reliability.

## Assumptions

- **User-stated:** accepted ADRs may be challenged on evidence; a small citation/API service may be recommended if justified. These are preferences, not empirical proof that a particular service is reliable (L71).
- **Prior user decision, transcript verified:** M0–M1 together; code/data separation and licenses fixed for that planning session; owner checkpoints do not block agent work; agent sample report is nongating. This audit does not silently add later translation, public deployment or human-review work.
- **Plan assumptions exposed:** retirement history persists; labels preserve identity; two citation declarations select the same text; CI validates the relevant merge state; generic hosting supplies suitable responses; source archives retain exact bytes; language models are deterministic; sampled page text has an agreed reading. Their individual status and evidence are recorded in the ledger.
- **Blind-draft assumptions:** “anyone can resolve” initially suggested public accessibility, but the actual approved milestone is better stated as a local/CI proof before M6. Printed-page anchors are essential; fine-grained IIIF regions need not be added to M1 merely because the independent draft considered them. Standards, rights and source availability needed external verification.
- **Audit judgment:** using a small resolver is a justified candidate for replacing finite API file enumeration, not a benchmarked framework selection. It must earn its operational cost in a short integration prototype.

## Run notes

**Evidence notation.** `P:<line>` means the audited plan named in the header. `ADR0003`, etc., refer to the correspondingly numbered files in `docs/decisions/`. Transcript references are JSONL line numbers, not rendered chat-message numbers:

- **Parent:** `/home/exedev/.claude/projects/-home-exedev-bron/0ad922bf-3dbc-4cba-a8cf-80ea0bc569be.jsonl`
- **Source:** `/home/exedev/.claude/projects/-home-exedev-bron/0ad922bf-3dbc-4cba-a8cf-80ea0bc569be/subagents/agent-ad6670de03a050037.jsonl`
- **Framework:** `/home/exedev/.claude/projects/-home-exedev-bron/0ad922bf-3dbc-4cba-a8cf-80ea0bc569be/subagents/agent-af0ef2b7081b4b27d.jsonl`

The user directed inspection of the Claude Code planning session. Its tool requests/results, source files and explicit user confirmations were treated as evidence; assistant summaries were not sufficient to confirm measurements. HTML, PDFs and OCR files survive under `/tmp/gd`, with scripts in `/tmp/gdscripts`. The `/tmp/dtsres` experiments and summarized research dossier were deleted by the original session. Historical command results are labeled as such; this audit did not rerun their installs or tests. Temporary source paths are evidence locators, not a durable archival strategy.

Read-only work included git status/HEAD/inventory/hash checks, numbered document reads, selective JSONL parsing, source HTML/OCR inspection and primary-source web retrieval. No repository tests existed; no dependencies were installed, services started, remote settings changed, messages sent, or PRs created. Three bounded native subagent tasks supplied the blind draft, standards evidence and transcript-source evidence. Earlier `*.audit*.md` files were not read. Some prior review prompts and edit descriptions surfaced while locating research in the parent transcript; they were not used as verification evidence. The draft remains labeled compromised regardless.

A progress message initially overstated the missing-page-marker issue. Inspection showed adjacent pagenum spans for most detached page anchors; PA-8/L66 retain only the supported malformed-label and mapping-verification concerns. An earlier progress count of 28 tracked files was corrected to 27. No source artifact or tracked file was changed. The only repository addition is this report. The original plan SHA-256 before/after is `6090a9e4c9979abf9c64f3e6d7f45efe556d0fa7ea144654299bbeef1327d101`.

**Coverage.** Read README, PRD, LICENSE, CITATION.cff, .gitignore; all six top-level design/roadmap documents; all fourteen ADRs; the fact-check document; and the entire plan. The complete initial tracked-file inventory was `git ls-files`. External standards were checked at the plan’s named versions where possible; moving GitHub main sources are identified as such. No external search can establish exhaustive ecosystem absence.

**Requirement-to-work check.** R1→U2/U3/U4/U5/U6/U7; R2→U3; R3→U1/U6/U7; R4→U2/U5/U6/U7; R5→U4/U7; R6→U4/U7; R7→U2/U8/U10; R8→U8/U10; R9→U8; R10→U9; R11→U4/U8/U10; R12→U5/U6/U10; R13→U8/U10; R14→U11. Every numbered requirement has planned work. Findings concern the adequacy or consistency of that work, not missing labels. Future test scenarios are intended acceptance checks, not current-runtime claims.

**Recommended revision sequence.** Resolve API architecture and citation lifecycle first; validate one fixture plus the existing concordance against the chosen rules; prove one real passage including a note/page boundary; complete the source archive and page map; then scale conversion and perform the sample report. This preserves the original scope while exposing foundational failures before six PRs depend on them.

## Claim ledger

| ID | Section | Kind | Claim | Verdict | Evidence or reason |
|---|---|---|---|---|---|
| L1 | Problem frame | codebase | bron contains design documents and licenses, no implementation | confirmed | git ls-files: 27 tracked files; README.md:11; no package/test/CI files in inventory. |
| L2 | Problem frame | codebase | bron-data already contains licenses, skeleton and concordance | confirmed | [Data repository](https://github.com/robertguss/bron-data); its README explicitly says only alignments has content. |
| L3 | Key decisions | consistency | M0–M1 scope and nonblocking owner tasks were approved | confirmed | Parent transcript:129 proposes revised scope; :132 user says Confirm. |
| L4 | Key decisions | consistency | Agent sample report without a publication threshold was approved | confirmed | Parent transcript:129 and :132; P:69. |
| L5 | Goal/scope | consistency | Anyone can resolve through the delivered service | refuted | P:18 versus P:80–81: no public deployment, only CI artifact. Local technical proof is an achievable narrower outcome. |
| L6 | R1/U6 | consistency | Every data CI run performs all three DTS validations | refuted | P:43,148–151 versus P:465: upstream validation explicitly skipped with no resources; specify this legitimate bootstrap exception. |
| L7 | R2/KTD8 | consistency | Deletion of an existing passage fails absent a redirect record | confirmed | P:152,390–401 explicitly implement and test this set comparison. |
| L8 | KTD8/U3 | assumption | Retirement records preserve old citation resolution | refuted | P:397 permits retirement without replacement; U5/U6 never consume redirects for resolution; ADR0004:17 requires old identifiers to resolve. |
| L9 | KTD8/U3 | assumption | A retired identifier cannot later be reused under the described algorithm | refuted | P:152,391,398 check current records, but do not preserve base retirement records. Removing an old record and adding that ID evades both checks. |
| L10 | Considered/not built | assumption | Realistic identifier shifts always change the set | refuted | P:95 admits same-set swaps; P:181 makes manual canonical edits normal. Swapping @n between existing units preserves the set and changes citation meaning. |
| L11 | KTD1/U6 | consistency | Code and data use one deliberately pinned action/tool version | confirmed | P:122,461,497 specify action SHA and installation from that same ref; implementation remains future work. |
| L12 | KTD8/U7 | assumption | Merge-base validation alone protects against intervening main changes | unverifiable | Exact checkout/merge-result strategy and strict up-to-date requirement are unspecified; P:152,462,497,502. |
| L13 | R5/DoD | consistency | Terms confirmation gates M0 completion | confirmed | P:50,153,630; confirmed original scope at Parent:129–132. |
| L14 | KTD16/U4 | consistency | rightsstatements.org-only validation covers the adopted Public Domain Mark | refuted | P:415 rejects other domains; ADR0012:8 includes PDM. [RightsStatements guidance](https://rightsstatements.org/en/documentation/) identifies PDM as a Creative Commons tool. |
| L15 | KTD2 | external | CapiTainS profile supports body URN/language, metadata and filename checks | confirmed | [Official guidelines](https://raw.githubusercontent.com/Capitains/website/master/pages/guidelines.md), directory structure and TEI requirements; valid profile, not proof of exhaustive equivalence to HookTest. |
| L16 | KTD2 | external | HookTest has old releases and a GPL MyCapytain dependency | confirmed | Framework:125,129 record HookTest 1.3.1 January 2020 and MyCapytain dependency/GPL metadata. Formal abandonment is judgment; repository was not archived. |
| L17 | KTD2 | runtime | setuptools compatibility problems were observed | confirmed | Framework:167 records pkg_resources warning and recommendation setuptools<81; historical environment, not a universal incompatibility result. |
| L18 | KTD3 | external | TEI P5 4.12.0 exists and supplies RelaxNG | confirmed | [TEI 4.12 link documentation](https://tei-c.org/release/doc/tei-p5-doc/en/html/ref-link.html); Framework:97 captures schema version. |
| L19 | KTD3 | runtime | Schema compilation took about six seconds in research | confirmed | Framework:101 output compile 5.9; :265 outputs 5.86 and 5.99. This is historical measurement, not a performance guarantee. |
| L20 | KTD3 | assumption | Native rules replace all relevant omitted Schematron constraints | refuted | [TEI link](https://tei-c.org/release/doc/tei-p5-doc/en/html/ref-link.html) requires >=2 targets; real insert links have 1. [Pinned citeStructure](https://raw.githubusercontent.com/TEIC/TEI/P5_Release_4.12.0/P5/Source/Specs/citeStructure.xml) constrains outer/inner match patterns. |
| L21 | KTD4 | external | Separate refsDecl siblings support CTS and citeStructure | confirmed | [Pinned refsDecl](https://raw.githubusercontent.com/TEIC/TEI/P5_Release_4.12.0/P5/Source/Specs/refsDecl.xml) alternatives; encodingDesc permits repeated components. Framework:174 records fixture passing HookTest. |
| L22 | KTD4 | assumption | Equal enumerated labels establish identical citation mapping | refuted | P:138 tests passage lists only; equal labels can select different XML nodes. Extraction or source-node parity is also necessary. |
| L23 | KTD5 | external | dapytains 1.0.0rc4 and saxonche 12.9.0 are valid pins | confirmed | [Versioned package metadata](https://pypi.org/pypi/dapytains/1.0.0rc4/json) names exact dependency; Framework:89 installed and imported on Python 3.14.7. |
| L24 | KTD5 | external | dapytains provides citeStructure enumeration and fragment extraction | confirmed | [Versioned README](https://raw.githubusercontent.com/distributed-text-services/MyDapytains/1.0.0rc4/README.md); Framework:182 shows two-level enumeration. Exact full-GD1 fidelity remains an implementation check. |
| L25 | KTD5/KTD6 | external | No other reusable generator or mature Python option exists | unverifiable | Research examined several alternatives; ecosystem-wide absence and maturity are not established by that search. They are selection judgments, not verified facts. |
| L26 | KTD6 | external | DTS 1.0 Level 0 exempts Navigation ranges only | confirmed | [DTS 1.0 Conformance](https://dtsapi.org/specifications/versions/v1.0/#conformance). |
| L27 | KTD6/U5 | consistency | The proposed static output is fully Level 0 conformant | refuted | P:145 omits Document ranges; P:144 generates finite down values, while DTS permits beyond-depth navigation requests. |
| L28 | KTD6 | assumption | Extensions yield the required response types on any host | refuted | P:141 universal claim is unsupported; Framework:229 logs missing application/ld+json. Host headers require explicit configuration/testing. |
| L29 | KTD6 | external | Uploading colon-bearing paths needs an archive workaround | unverifiable | Plan cites upload-artifact behavior without a version/source. Archive packaging is sensible independently; actual selected action must be checked. |
| L30 | KTD7 | runtime | Installed validator CLI rejected --entry-endpoint during research | confirmed | Framework:211 records the error; :215 identifies installed dts-validator 0.2.3 and pytest invocation from checkout. |
| L31 | KTD7 | external | Exact upstream validator behavior is pinned and established | unverifiable | P:150 leaves commit to implementation; historical research used main. :229 records 3 failed, 11 passed, 19 skipped, not a fully passing final prototype. |
| L32 | KTD7/U6 | external | Current upstream empty-resource path can dereference None | confirmed | [Client source](https://raw.githubusercontent.com/distributed-text-services/validator/main/dts_validator/client.py) get_one_resource and [conftest](https://raw.githubusercontent.com/distributed-text-services/validator/main/tests/conftest.py) resource.id; evidence applies to inspected main, not future pin. |
| L33 | KTD17 | external | Pinned dependencies are proven on CI Python 3.12 and 3.13 | unverifiable | Framework:89 tested 3.14.7; upstream matrix through 3.12 at :261. Future CI matrix is an appropriate verification task, not an observed result. |
| L34 | KTD9 | consistency | One file for all four GD1 volumes follows accepted version model | confirmed | ADR0003:11; P:158–161. Physical volumes need not be separate logical CTS resources. |
| L35 | KTD9/R7 | external | Four Gutenberg volumes have continuous section numbering 1–56 | confirmed | Four HTML sources and TOCs inspected; Source:41,71; section ranges match docs/research/2026-11-02-fact-checks.md. |
| L36 | KTD10/U8 | assumption | Trailing content can all be assigned to the last numbered unit | refuted | Vol4 HTML has back-matter contents/indexes beginning printed 530; P:522 defines section/paragraph parsing but no boundary for this material. |
| L37 | KTD11 | external | +10/+6 offsets were verified against every body page | refuted | Source:183,195,199,203 aggregate 491/560/552/565 OCR matches; /tmp/gdscripts/off.py:1 examines numeric first/last lines, not every page. |
| L38 | R12/U8 | external | GD1 3.2 begins Maar de kerk on printed 15 / PDF 25 | confirmed | Source:187 and /tmp/gd/dbnl/txt/p025.txt show heading/page and paragraph start in PDF OCR; visual full-page proof remains separate. |
| L39 | KTD11 | external | Vol2 chapter-opening page 386 lacks an HTML marker | confirmed | Source:110 HTML and :235 PDF 392 OCR; supported interpolation exception. |
| L40 | KTD11 | external | DBNL terms establish linking-only use for these scans | refuted | [Title-specific terms](https://www.dbnl.org/titels/gebruiksvoorwaarden.php?id=bavi002gere01) condition restrictions on copyright and allow reuse after expiry; source-copy assessment still required. |
| L41 | KTD11 | external | No usable DBNL IIIF/per-page image service exists | unverifiable | Unsuccessful discovery is not absence proof; Source:150 even records thumbnails. PDF fallback can be chosen without claiming universal absence. |
| L42 | KTD11/ADR0003 | consistency | PDF facs links honor the existing unconditional IIIF contract | refuted | ADR0003:15 requires canvas links; P:164–167 uses PDF fragments; record a staged exception or deliver IIIF. |
| L43 | KTD12 | external | Vol2 TOC directs correction of headings 27–33 | confirmed | Gutenberg67966 TOC; Source:203 PDF319 OCR shows §26 on printed 313 where corrected section is28. |
| L44 | KTD12 | external | Missing 29.11 is documented by the transcribers | confirmed | Source:71 reproduces DP testimony; distinguish source testimony from independent scan verification. |
| L45 | KTD12/U8 | external | Vol1 section 5 genuinely lacks 7 in print | unverifiable | Source:246,264,268,272,276 never establish this visually. Plan correctly leaves it as a pre-conversion investigation. |
| L46 | KTD13 | external | Source attribution to Gutenberg is permitted | confirmed | [Gutenberg permission guidance](https://www.gutenberg.org/policy/permission.html), Crediting; stripping boilerplate and crediting source are compatible with this guidance. |
| L47 | KTD13 | assumption | Removing bidi controls preserves intended Hebrew rendering | unverifiable | Controls are presentation data, but no captured TEI/client rendering comparison proves the downstream effect. Preserve script text and test direction handling. |
| L48 | KTD14 | external | Captured Gutenberg metadata records October 2024 updates | confirmed | Source:128: volume 1 October 22, volumes 2/3 October 18, volume 4 October 19; hashes are still needed for exact bytes. |
| L49 | KTD14/U7 | assumption | All four hash-identical raw Wayback captures can be obtained | unverifiable | No matching archive URLs/hashes supplied or successful capture demonstrated; P:500 requires a future external service action. |
| L50 | KTD14 | consistency | Initial deterministic ingest and subsequent canonical TEI edits are distinguished | confirmed | P:179–181 explicitly makes TEI canonical after ingest. Reproducing the initial ingest does not reproduce later editorial revisions. |
| L51 | KTD15 | external | Foreign language tags are complete in volumes 3–4 | refuted | Source:41 inventories tags, not completeness; :118 finds 161 Greek characters outside language spans in volume 3. |
| L52 | R10/U9 | consistency | Every foreign span is tagged by the described algorithm | refuted | P:552 promises every span; P:567 intentionally leaves short spans untagged. Candidate heuristics cannot establish exhaustive recall. |
| L53 | KTD18 | external | DBNL rate limiting was observed | confirmed | Source:187,199 HTTP 429; :203 succeeds after 150-second cooldown. Fixed two-minute safety is not established. |
| L54 | KTD18/U11 | assumption | A seed alone specifies the stratified sample | refuted | P:189 leaves eligible pages, forced-page replacement and Greek/Hebrew-heavy classification undefined; seed+algorithm+population are needed. |
| L55 | KTD18/U11 | assumption | Page text comparison produces an interpretable residual-error figure | unverifiable | P:191,603–604 do not define sic/corr reading, notes, hyphenation, combining marks or denominator. These must be specified before measurement. |
| L56 | U2/U7 | external | Existing nested link notes must move for RelaxNG validity | confirmed | [TEI link](https://tei-c.org/release/doc/tei-p5-doc/en/html/ref-link.html) is empty; actual concordance has note children. P:499 fixes that part. |
| L57 | U2/U7 | consistency | The permitted concordance edit makes it pass all planned checks | refuted | Real publicationStmt has no availability/license status, but P:132,380 require it; U7 permits only moving notes, and omits concordance from authoritative file list. |
| L58 | U4 | assumption | Existing basename-fragment targets are ordinary resolvable relative links | refuted | alignments/bavinck.gd.ed1--ed2.structure.xml targets bavinck.gd.ed1.xml in its own directory; actual edition path is data/bavinck/gd/. Custom basename lookup is not standard URI resolution. |
| L59 | U4 | consistency | Missing GD2 targets can be deferred until the edition arrives | confirmed | P:412,419 explicitly skips missing files and checks present files. Needs declared deferred resources so misspellings are not silently excused. |
| L60 | U5 | assumption | Sorting response members necessarily preserves source order | unverifiable | P:435 does not specify sort key; P:439 requires document order. Lexical sorting would put 3.10 before 3.2; specify source ordinal. |
| L61 | U5 | consistency | Mid-page fragments explicitly carry a governing pb without duplicate ID | confirmed | P:146,442–444 specify copy, removed xml:id and source corresp; good targeted protection. |
| L62 | U6/U7 | assumption | Base checkout works identically for nested fixtures and actual data repositories | unverifiable | P:462 does not specify fixture subpath on base checkout, empty initial push before SHA, or merge-result handling. Acceptance scenarios must settle these. |
| L63 | U7 | external | GitHub can enforce checks for administrators | confirmed | [Protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches), bypass setting. Existence of the future configured rule is not claimed here. |
| L64 | U8 | external | ins title supplies original/corrected text, with documented exception | confirmed | Source:63,65 show geplitst/gesplitst and inserted worden note plus nested Hebrew correction. Universal coverage still needs count reconciliation. |
| L65 | U8 | consistency | Editorial footnote policy has an implementation step | refuted | ADR0007:29 requires note place=bottom; U8 has no footnote extraction, callout, placement or test despite real footnotes in sources. |
| L66 | U8 | assumption | pagenum text always yields its printed number directly | refuted | /tmp/gd/v4/pg69005-images.html:19725 has Page_484 with visible label only ]. Most separate anchors do have adjacent pagenum spans; do not infer missing pages from anchor classes alone. |
| L67 | U9 | assumption | Language identification is reproducible from the specified inputs | unverifiable | Library, model/resource hash, confidence/floor and randomness settings remain unchosen at P:560; pin before reproducibility acceptance. |
| L68 | Deferrals | consistency | Sentence segmentation can wait until M5 | refuted | P:88 versus docs/roadmap.md:29 and docs/alignment.md hybrid workflow: M4 translation already consumes source sentence IDs. |
| L69 | DoD | consistency | M1 completion includes all its planned work | refuted | P:631 declares M1 at U10; sample U11 separately at632 despite roadmap:14. Clarify technical ingest versus complete milestone. |
| L70 | U10 | consistency | A deletion canary is required as an actual integration proof | confirmed | P:589 explicitly requires draft PR failing stability; this is future work, not a claim that it has already run. |
| L71 | Cross-cutting | assumption | Replacing static-only API with a small service is within audit scope | unverifiable | User-asserted preference in this audit: allowed if evidence justifies it; this authorizes recommendation, not proof of implementation reliability. |

## Blind draft

**Excerpt used:** Anyone should resolve a citation to Bavinck’s first-edition Gereformeerde Dogmatiek to the correct Dutch passage and printed scan page; changes must preserve citations. The project is designed but unbuilt, with initial scope M0 infrastructure and M1 first-edition TEI. The parent saw mixed goal/solution material while extracting this excerpt, so independence is compromised even though the fresh child excluded plans and ADRs.

**Approach:** Start with a reproducible code scaffold and separately versioned data, then make one real passage traverse acquisition, TEI conversion, citation resolution and scan linking before scaling to all four volumes. Record exact copies, hashes, reuse evidence and tool versions. Model first-edition identity as section and numbered subparagraph, preserving editorial distinctions, notes, languages, page boundaries and numbering irregularities. Generate metadata and API output from the same canonical TEI. Preserve published identities through checked history and resolvable split/merge mappings, rather than presence of strings alone. Validate every page/citation mapping mechanically and publish a documented 20-page comparison.

**Must-cover:**

- Code/data separation, licenses, reproducible setup, CI and commands: U1/U6/U7; retain.
- Verified TEI/CapiTainS/CTS/DTS contract: U2/U5/U6; PA-1, PA-3.
- Source/reuse evidence and maintainer confirmation: U4/U7; PA-5, PA-6.
- Four Gutenberg sources matched to DBNL copies: U7/U8; PA-8, PA-10.
- Sections 1–56, corrected 27–33 and original numbering gaps: U8; sound intent, unresolved section 5 scan check recorded in L45.
- Printed labels versus PDF ordinals, front matter and spanning passages: U8/U5; PA-8; governing-pb fragment handling is a strength.
- Corrections, editorial header, notes and languages: U8/U9; PA-7, PA-9.
- Named 3.2 resolution plus boundary cases: U5/U6/U10; PA-2, PA-7, PA-8.
- Public URLs, releases and invalid citations: public release work reasonably belongs to M6; PA-13 corrects current wording, PA-1/PA-2 address API validity and old IDs.
- Removal, reuse, renumbering, splits/merges and changed text: U3; PA-2, PA-12.
- All four volumes and 20-page sample with error method: U10/U11; PA-7, PA-11, PA-13.
- Independence from later OCR/translation/reader work: scope preserved; PA-13 fixes the later segmentation dependency without expanding M1.

**Draft assumptions:**

- The goal was extracted from a mixed section and is therefore qualified above.
- An accessible public resolution surface was initially assumed; the plan’s explicit CI-only boundary makes this a wording clarification, not a mandate to deploy early.
- Page-level anchors suffice for the first proof; precise regions can follow an explicitly staged IIIF policy.
- No implementation, external standard or source-rights conclusion was presumed verified by the blind draft.
- Blind child opened README.md, PRD.md, docs/text-model.md, docs/provenance.md, docs/transcription.md, docs/roadmap.md, docs/research/2026-11-02-fact-checks.md, CITATION.cff, .gitignore and LICENSE. Parent additionally reviewed the remaining permitted design context before proceeding to the plan and ADRs.
