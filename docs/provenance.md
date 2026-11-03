# Provenance and review

**Status:** Designed 2026-11-02 (design session 5). Decisions in ADR 0009.

## 1. What a sentence says about itself

| Axis | Values | Where |
|---|---|---|
| Origin | pipeline run · named human · public-domain published translation | `@resp` → `<respStmt>` (name, role, ORCID) |
| State | `translated` · `reviewed` · `final` (XLIFF 2) | `@ana` → vocabulary in header |
| Score | automatic MQM score at generation (ADR 0008) | stand-off, per sentence, with run id |
| Flags | `source-changed` · `lexicon-changed` · `translators-disagree` · `below-gate` | stand-off |
| Reviewer, date | from the merge that set the state | git |

## 2. Lifecycle

```
machine draft ──(gate ≥ threshold)──▶ public, state=translated, label+score
      │                                     │
      │  proposal (anyone, PR)              │  vetted reviewer: approve / edit / MQM mark / lexicon proposal
      ▼                                     ▼
   proposal queue ──(vetted approval)──▶ state=reviewed ──(second vetted reviewer)──▶ state=final
                                            ▲
      source sentence changed ──────────────┘ (drops to translated + flag; old text kept visible)
```

## 3. Roles

| Role | Who | May |
|---|---|---|
| Contributor | anyone with an account | open proposals (PRs) |
| Vetted reviewer | listed in `REVIEWERS.md` with language(s) and attestation; real name; ORCID if any | set `reviewed`; approve proposals; set `final` on others' `reviewed` |
| Maintainer | Robert | maintain the list; publish criteria; promote contributors by track record; set `final` on anchored public-domain translations after a check |

Promotion criteria (to be written into `REVIEWERS.md`): a sustained record of accepted proposals in a language, plus a vetted reviewer's endorsement.

## 4. The reviewer's screen (requirements for the reader session)

Per paragraph: source sentences with IDs | draft with state badges | approved lexicon entries present in the paragraph | places where the two translators disagreed | flags. Per sentence: approve · edit · mark MQM error (category, severity, note) · propose lexicon entry. Every action becomes a commit; a session's actions become one PR.

## 5. Files
- `REVIEWERS.md` — the vetted list, criteria, and how to ask.
- Data repo: `translations/…tei.xml` (canonical, with `@resp`/`@ana`), `provenance/…` (stand-off scores and flags), `lexicon/bron.tbx`, PR history.

## 6. Open items
- Exact `@ana` vocabulary declaration and where scores live (stand-off TEI vs. JSON sidecar).
- Whether `final` is needed in the first release or `reviewed` is enough until there are two reviewers per language.
- How the seminar workflow authenticates students (GitHub accounts under real names is the simplest honest option).
