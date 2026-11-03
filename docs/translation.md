# Translation and lexicon

**Status:** Designed 2026-11-02 (design session 4). Decisions in ADR 0008. This consolidates them and lays out the pilot.

## 1. Pipeline per paragraph

```
source sentences (IDs) + approved lexicon entries + section context
      │
      ├─▶ model A ─┐
      └─▶ model B ─┤  each: paragraph translation with sentence-ID groups
                   ▼
            reconcile (ADR 0006 rules) ─▶ reject/retry/fallback
                   ▼
            terminology QA (lexicon) ─▶ flags, reasons for departures
                   ▼
            automatic MQM judge (calibrated) ─▶ score
                   ▼
            gate: score ≥ threshold ─▶ public as `initial` with label + score
                   └─ else ─▶ private queue for review
```

## 2. The pilot (first thing to build after the TEI exists)

**Material:** GD² Par. 23–25 (`#161–177`, the knowability of God), 17 subparagraphs, roughly a chapter of Bolt vol. 2.

**Steps**
1. Translate with two models under the pipeline above, lexicon empty on the first pass.
2. Propose lexicon entries from the term pairs observed; a reviewer approves; re-run with injection.
3. Score: chrF/COMET against Bolt (private); automatic MQM; **human MQM** on a fixed subset by a Dutch reader.
4. Calibrate: compare automatic MQM to human MQM; record agreement. This number is the license for the automatic judge elsewhere.
5. Set the publication threshold from the distribution; publish the numbers with the first release.

**Outputs:** the first approved lexicon entries (TBX), the judge calibration figure, the gate threshold, and 17 subparagraphs of gated English.

## 3. Lexicon entry (TBX-Basic, sketched)

```xml
<termEntry id="c-0042">
  <descrip type="subjectField">theology proper</descrip>
  <descrip type="definition">… drawn from GD² #178–180 …</descrip>
  <descrip type="rationale">established usage (Bolt vol. 2; Muller s.v. nomen Dei)</descrip>
  <admin type="status">approved</admin>
  <langSet xml:lang="nl"><tig><term>benoemingsnamen Gods</term></tig></langSet>
  <langSet xml:lang="en">
    <tig><term>the names of God (proper names)</term><termNote type="administrativeStatus">preferredTerm-admn-sts</termNote></tig>
  </langSet>
  <ref type="crossReference" target="urn:cts:bron:bavinck.gd.ed2:188"/>
</termEntry>
```

## 4. What is never done
- No copyrighted translation text is stored in the repo or shown anywhere; Bolt is read locally for scoring only.
- No draft is public without a label and a score, and none below the gate.
- No lexicon rendering departs from established usage without a written rationale.

## 5. Open items
- Model choice for the two translators and for the judge (the judge should not be one of the translators).
- Prompt texts; how much surrounding context (the whole Par.) to supply.
- COMET model variant for Dutch→English; whether chrF alone suffices as the cheap signal.
- Threshold value: set from pilot data, not in advance.
- Legal comfort note on term borrowing to be confirmed with someone who can give it; the design does not depend on it beyond what ordinary translators do.
