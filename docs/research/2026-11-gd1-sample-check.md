# GD¹ 20-page sample check

**Date:** 2026-11-04. **Text checked:** `bron-data:data/bavinck/gd/bavinck.gd.ed1.xml` at `bron-data` commit `d112b55`, SHA-256 `225fef26c3ee02e57529ffed31d741b53b97bcc2cd18bfdcfaefb55e44c3e952`, converted at `bron` commit `c911e8f`. **Scans:** the four DBNL PDFs, each matching its SHA-256 in `bron-data:registry/sources.yaml`.

This report compares 20 pages of the GD¹ TEI with the DBNL scans of the printed volumes. It estimates how often the TEI's text departs from the print.

**The figures are an exploratory estimate.** They come from 20 pages, one reader per page plus a second reading of each discrepancy, and no human proofreading. They are not a measured error rate and set no threshold.

## Result

On the 20 pages (47,858 characters), the TEI departs from the print in 13 places, 17 characters in all: **0.36 per 1,000 characters**. The OCR layer confirms 4 of these places (8 characters, 0.17 per 1,000), and a second agent reading supports the other 9 (9 characters, 0.19 per 1,000). No discrepancy is left unconfirmed.

The 17 randomly drawn pages give **0.12 per 1,000** (5 characters in 40,869). The three forced pages, chosen for p. 15 and for their Greek and Hebrew, hold 8 of the 13 discrepancies. One Greek-heavy page (vol. 4 p. 323) holds 6 of them.

On these pages there are no encoding errors in page breaks or structure. The language tags have one machine-tagged span that runs 3 letters too far (0.06 per 1,000).

All 13 textual discrepancies are already in the Distributed Proofreaders transcription. In each case the Gutenberg source has the TEI's reading, so the conversion copied the transcription faithfully. They fall into two groups:

- **The TEI introduces a wrong reading** (9): a misspelled name (*Zeiler* for *Zeller*), a lost accent (*alleén*, *zèer*), a lost Greek breathing (ἀνομια), title case added to an English title, a wrong Greek letter in two words (τον for του, εἰωχια for εὐωχια), and a wrong Hebrew letter in two words (הָרוֹן for חָרוֹן, עֶבְרָם for עֶבְרָה).
- **The TEI corrects a printer's error without recording it** (4): *gemeensehap*, *uud* (a turned *n*), and the Greek εἰχαριστια and εἰλογια, which are printed with an iota where the upsilon belongs.

The second group contradicts two statements in the TEI header (see [Findings](#findings-for-the-tei-header)).

## Protocol

### Population and sample

**Population.** Every body page with an arabic printed number: each `pb` inside `text/body` whose `n` is all digits. That is 2,204 pages: 532 in vol. 1, 571 in vol. 2, 572 in vol. 3 and 529 in vol. 4. Each volume's pages run from 1 to its last number without a gap. Front matter (vol. 1 pp. III–VII) and vol. 4's back matter (pp. 530–590) are excluded.

**Page text.** A page's text is everything in the body after its `pb` and before the next `pb`, in document order:

- the printed reading where there is a `choice` (`sic`, not `corr`);
- `note`s of type `transcriber` left out, because they are not printed;
- footnotes moved to the end of the page.

None of the sampled pages has a footnote.

**Script counts.** Greek-script characters are U+0370–03FF and U+1F00–1FFF. Hebrew-script characters are U+0590–05FF and U+FB1D–FB4F.

**Strata.** Five pages per volume. Three pages are forced:

- vol. 1 p. 15;
- one Greek-heavy page;
- one Hebrew-heavy page.

Each forced page takes one of its volume's five places. "Heavy" means the top decile of the pages that contain the script: rank those pages by that script's character count, highest first, with ties broken by (volume, page), and take the first ⌈n/10⌉. 764 pages contain Greek, so the Greek decile is 77 pages, each with 98 or more Greek characters. 144 pages contain Hebrew, so the Hebrew decile is 15 pages, each with 44 or more Hebrew characters. The decile is taken over pages that contain the script rather than over all 2,204 pages because Hebrew appears on only 144 pages, so a decile of all pages would include pages with no Hebrew.

**Seed and algorithm.** The seed is the TEI file's SHA-256 read as an integer, so nobody chose it. The draw was run once, with Python 3.15.2:

```python
seed = int("225fef26c3ee02e57529ffed31d741b53b97bcc2cd18bfdcfaefb55e44c3e952", 16)
rng = random.Random(seed)
forced = [(1, 15)]
forced.append(rng.choice([p for p in greek_decile if p not in forced]))  # sorted (vol, page) list
forced.append(rng.choice([p for p in hebrew_decile if p not in forced]))  # sorted (vol, page) list
sample = list(forced)
for vol in (1, 2, 3, 4):
    pool = [n for n in range(1, last_page[vol] + 1) if (vol, n) not in forced]
    sample += [(vol, n) for n in rng.sample(pool, 5 - sum(f[0] == vol for f in forced))]
```

**The sample:**

| Vol. | Pages | Forced |
|---|---|---|
| 1 | 11, 15, 146, 171, 356 | 15 |
| 2 | 122, 158, 188, 196, 294 | 196 (Hebrew-heavy, 49 Hebrew characters) |
| 3 | 30, 46, 59, 164, 182 | none |
| 4 | 180, 253, 323, 435, 461 | 323 (Greek-heavy, 217 Greek characters) |

### Reading the scans

Each sampled page was rendered from its PDF at 2,400 pixels wide. The rendered page was cut into four bands, always between two text lines, so each printed line appears in exactly one band.

Five agents (Claude Opus 5.5, four pages each) transcribed the bands. They worked from the images alone: they had no access to the TEI, the Gutenberg files, the PDFs or their OCR layer, and were told not to search the web for the text. The brief asked for:

- one output line per printed line;
- line-end hyphens kept as printed;
- running heads and page numbers marked so that they could be dropped;
- paragraph breaks and headings marked;
- superscripts marked;
- Greek and Hebrew transcribed with their diacritics as printed;
- every Latin, German and French word or phrase marked, including single terms inside Dutch sentences and abbreviated book titles. Ordinary Dutch loanwords, names and bare citation abbreviations (*cf.*, *S.*, *f.*) were not marked.

### Comparison

Both texts were normalized before comparison:

- NFC normalization;
- whitespace collapsed;
- ĳ written as *ij*;
- curly and straight quotation marks treated as equal, and the Greek letter variants ϑ and ϰ treated as θ and κ;
- line-end hyphens in the transcription rejoined. A hyphen was kept only where the TEI writes that word with one, which is a real compound split at its hyphen.

The texts were then aligned word by word. Each run of differing words is one hunk, and a hunk counts its character-level edits: the characters it inserts, deletes or substitutes.

The transcribers' documented silent normalizations were applied before any hunk was counted as a discrepancy:

- a hunk that differs only in spacing counts as a spacing normalization;
- a hunk that differs only in punctuation counts as a punctuation normalization;
- a Hebrew hunk in vols. 2–4 that differs only in vowel points would have counted as a Hebrew normalization. There were none.

The header also lists æ/œ printed as *ae*/*oe* and German noun capitals in vol. 1. Neither occurred on the sampled pages. Normalizations are counted separately below and are neither errors nor candidates for fixes.

**Denominator:** the character count of the normalized TEI page text.

### Confirmation

Each remaining hunk was checked in this order:

1. **OCR-confirmed:** the PDF's own OCR text layer has the transcription's reading at that place.
2. Otherwise, a second agent was given only a high-resolution crop of those lines, with no candidate readings, and asked what one named word is printed there:
   - it read the transcription's reading: **agent-corroborated**;
   - it read the TEI's reading: **refuted**, a misreading in the first transcription that is not counted against the TEI;
   - it read neither: **unconfirmed**.

The OCR layer cannot read Greek or Hebrew, and on these pages it also drops some accents (*alleen*) and garbles some words (*Bene* for *ééne*). This is why every discrepancy it does not support goes to the second reading. Both kinds of confirmation are corroboration, not ground truth: two readings can share a misreading.

The second reading was run on all 17 remaining hunks, including those the OCR confirmed. It matched three of the four OCR-confirmed readings exactly. On the fourth (*zèer*), it saw an accent on the same letter but could not make out its form.

### Encoding checks

On each page, three encoding checks were made against the scan:

- **page breaks:** the TEI page starts and ends at the same words as the scan;
- **structure:** each paragraph break and heading in the TEI matches one in the scan, and each numbered subparagraph opens where its number is printed;
- **page link:** the `pb`'s `facs` opens the PDF page that carries the printed number.

## Figures

### Textual discrepancies

Characters per 1,000, with the number of hunks in brackets.

| Vol. | Characters | OCR-confirmed | Agent-corroborated | Unconfirmed | All |
|---|---|---|---|---|---|
| 1 | 11,833 | 0.00 (0) | 0.08 (1) | 0 | 0.08 |
| 2 | 12,074 | 0.00 (0) | 0.17 (2) | 0 | 0.17 |
| 3 | 11,855 | 0.25 (3) | 0.08 (1) | 0 | 0.34 |
| 4 | 12,096 | 0.41 (1) | 0.41 (5) | 0 | 0.83 |
| **All 20 pages** | **47,858** | **0.17 (4)** | **0.19 (9)** | **0** | **0.36** |
| 17 random pages | 40,869 | 0.07 (3) | 0.05 (2) | 0 | 0.12 |

Vol. 4's higher figure comes from p. 323, the forced Greek-heavy page, which holds 1 OCR-confirmed hunk and all 5 of vol. 4's agent-corroborated hunks. Discrepancies cluster on pages like this one, so the per-volume figures rest on very few events. A confidence interval from a count model would overstate what 20 pages can show, so none is given.

The second reading refuted 4 further hunks as misreadings in the first transcription. One reader normalized the misprinted German *Beschaffenheid* to *Beschaffenheit*, and three times a reader wrote *éene* where the print, the OCR and the TEI all have *ééne*.

### Encoding errors

Characters per 1,000, with the number of errors in brackets. The character counts are those of the textual table.

| Class | Vol. 1 | Vol. 2 | Vol. 3 | Vol. 4 | All 20 pages |
|---|---|---|---|---|---|
| Page break | 0.00 (0) | 0.00 (0) | 0.00 (0) | 0.00 (0) | 0.00 (0) |
| Structure (paragraphs, headings, subparagraph numbers) | 0.00 (0) | 0.00 (0) | 0.00 (0) | 0.00 (0) | 0.00 (0) |
| Language tag | 0.25 (1 span, 3 letters) | 0.00 (0) | 0.00 (0) | 0.00 (0) | 0.06 (1 span, 3 letters) |

All 20 page links open the right PDF page. The OCR layer's first line gives the printed number on 18 pages. On vol. 1 p. 356 and vol. 3 p. 59 that line is garbled, and the transcribers read the numbers from the scan. Separately, all 2,270 `pb`s in the file were checked against the page map: each `facs` names the right volume's PDF and the page the map gives, and no page index lies outside its PDF.

The language-tag error is in vol. 1 p. 146, § 7.1. The machine tag on Leibniz's title *Nouveaux essais sur l'entendement humain* also takes in the citation that follows it, *I ch.* This is counted from the independent marking and checked against the TEI text. It is not a reading of the scan, so OCR confirmation does not apply to it.

### Normalizations (not errors)

| Vol. | Spacing hunks (characters) | Punctuation hunks (characters) |
|---|---|---|
| 1 | 73 (78) | 0 (0) |
| 2 | 95 (240) | 6 (18) |
| 3 | 34 (85) | 3 (5) |
| 4 | 33 (73) | 11 (30) |
| All | 235 (476) | 20 (53) |

Most spacing hunks are the print's spaced colons in Bible references (*Rom. 2 : 8*, written *2:8* in the TEI) and its spaces before commas and semicolons. Of the punctuation hunks, 16 are only the dash in a range of numbers (*5—7*): both readers saw a long dash where the TEI and the OCR have a hyphen. The other 4 change a punctuation mark: *Syst,* (vol. 2 p. 122), *enz ,* (vol. 4 p. 180), *lust,.* (vol. 3 p. 164) and *behaald.* (vol. 4 p. 461). In each case the transcription has a different mark.

### Language tags

The tags were compared letter by letter on the words where the TEI and the transcription agree. The transcribers' Latin, German and French marking is the reference.

**Machine tags for Latin, German and French** (`resp="#bron-langid"`):

| | Letters | Precision | Recall |
|---|---|---|---|
| Latin | 562 tagged; 1,526 to find | 100% | 37% |
| German | 104 tagged; 594 to find | 100% | 18% |
| French | 79 tagged; 156 to find | 96% | 49% |
| **All** | **745 tagged; 2,276 to find** | **99.6%** | **33%** |

Recall counts only letters outside the transcribers' own language spans, because the machine layer never tags inside them. All 13 machine-tagged spans on the sampled pages are in the right language. The one imprecise span is the *I ch.* overreach above.

As the TEI header says, the machine tags favour precision over recall. The independent marking includes many single Latin terms within Dutch sentences and many abbreviated titles (*Inst.*, *S. c. Gent.*). Both fall under the machine layer's 20-letter floor or its Dutch-word filter by design. Recall by volume: 32% (vol. 1), 46% (vol. 2), 12% (vol. 3) and 0% (vol. 4). In vols. 3 and 4 the transcribers' own spans already cover much of the foreign text, and what is left is mostly short.

**The transcribers' spans** on the sampled pages (372 letters, all in vols. 3 and 4) agree with the independent marking on every letter. Together with the machine tags, 42% of the marked Latin, German and French letters on these pages are inside a span of the right language.

**Machine tags for Greek and Hebrew:** 51 letters on the sampled pages, all in the tagged script. No Greek or Hebrew letter on the sampled pages is outside a language span. Here both precision and the absence of untagged letters hold by construction, and CI checks them on the whole file.

## Corrections

Only the four OCR-confirmed discrepancies are corrected, in a follow-up `bron-data` pull request: **not yet opened, waiting on Robert's OK.** Each correction is an ordinary edit to the TEI. The agent-corroborated discrepancies are listed below and not edited.

| Place | TEI now | Print (OCR and both readings) | Proposed correction |
|---|---|---|---|
| Vol. 3 p. 46, § 36.4 | *Zeiler, Philos. d. Gr.* | *Zeller, Philos. d. Gr.* | *Zeller* |
| Vol. 3 p. 164, § 39.3 | *gemeenschap met God* | *gemeensehap met God* | `<choice><sic>gemeensehap</sic><corr>gemeenschap</corr></choice>`, the encoding the TEI already uses for the transcribers' corrections |
| Vol. 3 p. 182, § 39.7 | *eene zeer groote macht* | *eene zèer groote macht* | *zèer*. The accent is worn. The OCR and the first reading have a grave, and the second reading saw a near-vertical mark of unclear form. Check the scan before merging. |
| Vol. 4 p. 323, § 53.4 | *The Doctrine Of The Holy Eucharist* | *The doctrine of the holy eucharist* | lower case as printed |

**Agent-corroborated, not edited:**

| Place | TEI | Print (both readings) |
|---|---|---|
| Vol. 1 p. 146, § 7.1 | *alleen uit het denken* | *alleén* (the OCR drops the accent) |
| Vol. 2 p. 196, § 26.14 | הָרוֹן | חָרוֹן |
| Vol. 2 p. 196, § 26.14 | עֶבְרָם | עֶבְרָה |
| Vol. 3 p. 59, § 36.7 | ανομια | ἀνομια |
| Vol. 4 p. 323, § 53.4 | *Spiritualismus und Realismus* | *uud* (a turned *n*) |
| Vol. 4 p. 323, § 53.5 | ποτηριον τον κυριου | ποτηριον του κυριου |
| Vol. 4 p. 323, § 53.5 | εὐχαριστια | εἰχαριστια |
| Vol. 4 p. 323, § 53.5 | εὐλογια | εἰλογια |
| Vol. 4 p. 323, § 53.5 | εἰωχια | εὐωχια |

**Outside the sample:** the TEI spells the name *Zeiler* twice more, at § 35.1 and § 36.2 (vol. 3), against 42 instances of *Zeller*. These were not checked against the scans and are not counted or corrected here.

## Findings for the TEI header

The sample contradicts two of the header's statements about the transcribers' silent normalizations. Neither statement is changed by this report.

- **Greek misprints.** The header says misprints in Greek are left as printed in vols. 2–4. On vol. 4 p. 323 the TEI has εὐχαριστια and εὐλογια where the print has εἰχαριστια and εἰλογια, so it corrects at least these two. On the same page it has εἰωχια where the print has the correct εὐωχια, and τον where the print has του. Whether to restore the printed Greek, or to encode it as `sic` and `corr`, is an editorial decision for a later pass.
- **Undocumented corrections.** The header says every correction the transcribers made is encoded as `choice`, and it lists their silent normalizations. The transcription also corrects Dutch and German misprints silently (*gemeensehap*, *uud*). Those corrections are on neither list, and because the transcription does not mark them, the converter could not encode them.

Both Hebrew discrepancies on vol. 2 p. 196 go the other way from the documented Hebrew corrections. The print has the expected word for the gloss beside it (חָרוֹן, burning anger; עֶבְרָה, wrath), and the TEI does not.

## Numbering findings, restated

The page-map review (`docs/research/2026-11-gd1-page-map.md`) settled three numbering questions on the scans:

- **Vol. 1 § 5 has no subparagraph 7.** Subparagraph 6 opens on p. 64 and 8 on p. 69. The three paragraphs between them are unnumbered in the print.
- **Vol. 2 § 29 has no subparagraph 11.** Subparagraph 10 runs from p. 417 into p. 419, where 12 opens.
- **Vol. 4 § 51 prints "6." twice** (pp. 239 and 246). The transcribers corrected the second to 7, and the TEI cites it as 7.

No number is invented, so §§ 5 and 29 have no identifier for the missing subparagraph. None of these pages fell in the sample.

## Repeating the check

1. Draw the sample with the code above from the TEI file with the SHA-256 given at the top. A file with a different hash gives a different seed and a different sample.
2. Render each page from its `pb`'s `facs` and cut it into line-safe bands. Have each page transcribed from the images alone, to the brief summarized under *Reading the scans*.
3. Extract each page's TEI text as defined under *Population and sample*, normalize both texts, align them word by word, and classify each hunk as described.
4. Check each remaining hunk against the PDF's OCR text layer, then give a second reader a crop of its lines with no candidate readings.

A repeat with different readers will differ in detail, because the readings are the measurement.

## Appendix: page-level comparison

Hunks (characters) per page. *Refuted* hunks are misreadings in the first transcription and are not counted. Page breaks, paragraph breaks and headings matched the scan on every page.

| Page | PDF page | Characters | Spacing | Punctuation | OCR-confirmed | Agent-corroborated | Refuted |
|---|---|---|---|---|---|---|---|
| 1 p. 11 | 21 | 2,508 | 15 (16) | 0 (0) | 0 (0) | 0 (0) | 0 |
| 1 p. 15 | 25 | 2,301 | 17 (17) | 0 (0) | 0 (0) | 0 (0) | 1 |
| 1 p. 146 | 156 | 2,350 | 7 (7) | 0 (0) | 0 (0) | 1 (1) | 0 |
| 1 p. 171 | 181 | 2,207 | 33 (37) | 0 (0) | 0 (0) | 0 (0) | 0 |
| 1 p. 356 | 366 | 2,467 | 1 (1) | 0 (0) | 0 (0) | 0 (0) | 0 |
| 2 p. 122 | 128 | 2,447 | 0 (0) | 3 (4) | 0 (0) | 0 (0) | 1 |
| 2 p. 158 | 164 | 2,427 | 0 (0) | 0 (0) | 0 (0) | 0 (0) | 0 |
| 2 p. 188 | 194 | 2,385 | 19 (66) | 0 (0) | 0 (0) | 0 (0) | 0 |
| 2 p. 196 | 202 | 2,387 | 67 (159) | 3 (14) | 0 (0) | 2 (2) | 0 |
| 2 p. 294 | 300 | 2,428 | 9 (15) | 0 (0) | 0 (0) | 0 (0) | 0 |
| 3 p. 30 | 36 | 2,349 | 28 (73) | 2 (4) | 0 (0) | 0 (0) | 0 |
| 3 p. 46 | 52 | 2,353 | 0 (0) | 0 (0) | 1 (1) | 0 (0) | 0 |
| 3 p. 59 | 65 | 2,447 | 0 (0) | 0 (0) | 0 (0) | 1 (1) | 0 |
| 3 p. 164 | 170 | 2,324 | 1 (2) | 1 (1) | 1 (1) | 0 (0) | 0 |
| 3 p. 182 | 188 | 2,382 | 5 (10) | 0 (0) | 1 (1) | 0 (0) | 0 |
| 4 p. 180 | 186 | 2,425 | 14 (32) | 2 (4) | 0 (0) | 0 (0) | 0 |
| 4 p. 253 | 259 | 2,458 | 12 (25) | 0 (0) | 0 (0) | 0 (0) | 1 |
| 4 p. 323 | 329 | 2,301 | 5 (12) | 1 (1) | 1 (5) | 5 (5) | 0 |
| 4 p. 435 | 441 | 2,476 | 0 (0) | 0 (0) | 0 (0) | 0 (0) | 1 |
| 4 p. 461 | 467 | 2,436 | 2 (4) | 8 (25) | 0 (0) | 0 (0) | 0 |

Each discrepancy and refuted hunk, as TEI → first reading, with the OCR layer and the second reading:

| Page | TEI | First reading | OCR layer | Second reading | Class |
|---|---|---|---|---|---|
| 1 p. 15 | Beschaffenheid | Beschaffenheit | Beschaffenheid | Beschaffenheid | refuted |
| 1 p. 146 | alleen | alleén | alleen | alleén | agent-corroborated |
| 2 p. 122 | ééne | éene | ééne | ééne | refuted |
| 2 p. 196 | הָרוֹן | חָרוֹן | unreadable | חָרוֹן | agent-corroborated |
| 2 p. 196 | עֶבְרָם | עֶבְרָה | unreadable | עֶבְרָה | agent-corroborated |
| 3 p. 46 | Zeiler | Zeller | Zeller | Zeller | OCR-confirmed |
| 3 p. 59 | ανομια | ἀνομια | unreadable (*ávoua*) | ἀνομια | agent-corroborated |
| 3 p. 164 | gemeenschap | gemeensehap | gemeensehap | gemeensehap | OCR-confirmed |
| 3 p. 182 | zeer | zèer | zèer | zėer (unclear) | OCR-confirmed |
| 4 p. 253 | ééne | éene | ééne | ééne | refuted |
| 4 p. 323 | und | uud | and | uud | agent-corroborated |
| 4 p. 323 | Doctrine Of The Holy Eucharist | doctrine of the holy eucharist | doctrine of the holy eucharist | doctrine of the holy eucharist | OCR-confirmed |
| 4 p. 323 | τον | του | unreadable | του | agent-corroborated |
| 4 p. 323 | εὐχαριστια | εἰχαριστια | unreadable | εἰχαριστια | agent-corroborated |
| 4 p. 323 | εὐλογια | εἰλογια | unreadable | εἰλογια | agent-corroborated |
| 4 p. 323 | εἰωχια | εὐωχια | unreadable | εὐωχια | agent-corroborated |
| 4 p. 435 | ééne | éene | Bene | ééne | refuted |
