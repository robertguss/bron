# Schemas

## `tei_all-4.12.0.rng`

The TEI P5 `tei_all` RelaxNG schema, version 4.12.0 (revision `113e933e2`, generated 2026-07-28), copied unchanged from the TEI Vault:

- Source: <https://tei-c.org/Vault/P5/4.12.0/xml/tei/custom/schema/relaxng/tei_all.rng>
- SHA-256: `b0f115095ead2ccc6933aa3365c6f4a82cba3b2ec7eee7f76bb616d7a63b7e48`
- License: the TEI Consortium releases TEI material under both CC BY and BSD-2 (see the notice in the file).

Bron validates with lxml's RelaxNG, which needs no Java. Upgrading TEI means replacing this file, updating the checksum here, and running the test suite.

## TEI Schematron rules

`tei_all` also embeds Schematron rules (98 rule contexts in 4.12.0). They need an XSLT 2 pipeline that neither lxml nor jing runs, so Bron enforces natively the rules that apply to the elements its files use (`src/bron/checks/tei_constraints.py`).

| TEI rule | Status | Check id |
|---|---|---|
| `link`: `@target` has at least two values | Enforced, with one deviation: `type="insert"` and `type="delete"` links must have exactly one target (ADR 0017) | `tei-link-targets` |
| outer `citeStructure/@match` starts with `/` | Enforced | `tei-citestructure-match` |
| nested `citeStructure/@match` does not start with `/` | Enforced | `tei-citestructure-match` |
| `@subtype` only with `@type` | Enforced | `tei-subtype` |
| no `p` inside `p` or `ab` (outside the allowed parents) | Enforced | `tei-abstract-model` |
| no `div` inside `p` or `ab` (outside `floatingText`) | Enforced | `tei-abstract-model` |
| `ref`/`ptr`: not both `@target` and `@cRef` | Enforced | `tei-pointer` |
| no `s` directly inside `s` | Enforced | `tei-s-nesting` |
| `join`: `@target` has at least two values | Not applicable: Bron does not use `join` | — |
| every other rule | Not applicable: they govern ODD specification elements (`elementSpec`, `constraintSpec`, `schemaSpec` and the like), manuscript description, facsimile zones, verse (`l`, `lg`), critical apparatus, spans (`addSpan`, `delSpan`, `damageSpan`, `span`), `subst`, `relation`, and dating attributes (`@when`, `@from`, `@to`), none of which Bron's files use | — |

Because of the deviation, Bron's files are described as valid against `tei_all` with one documented Schematron deviation, never as plain TEI-valid. A file that starts using one of the not-applicable elements needs its rule added here and in `tei_constraints.py`.
