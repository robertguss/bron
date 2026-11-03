# Alignments

Stand-off alignment files per ADR 0006. These are data, not code; they live here only until the data repo exists, and will move there unchanged.

| File | Pair | Level | Status |
|---|---|---|---|
| `bavinck.gd.ed1--ed2.structure.md` | GD¹ ↔ GD² | structure (§ ↔ Par.) | drafted 2026-11-02 from the two tables of contents; human check pending |
| `bavinck.gd.ed1--ed2.structure.xml` | GD¹ ↔ GD² | structure | same, as a TEI `<linkGrp>` |

Section-level targets use the planned `xml:id`s of the edition files (`sec-NN` for GD¹ §§, `par-NN` for GD² Par., `par-13b` for the second Par. 13), because the structural level sits above the CTS passage hierarchy of GD² (whose citable unit is the subparagraph `#`). Unit- and sentence-level links will use CTS URNs.
