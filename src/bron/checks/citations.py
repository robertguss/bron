"""Citable passages: enumerable, labelled, non-empty, unique, and equal under both declarations.

A text's `cRefPattern`s and its `citeStructure` must name the same passages and select the
same text for each, or two kinds of tools would resolve one citation to different words.
"""

import re
from collections import Counter
from collections.abc import Iterator
from pathlib import Path

from bron.checks import Context
from bron.findings import Finding
from bron.tei import NSMAP
from bron.tei.passages import (
    PassageError,
    cite_structure_units,
    cref_passages,
    extract_passage,
)
from bron.tei.text import normalized_text

# Characters a passage label may not contain: CTS uses them for levels, subreferences,
# ranges and URN components.
FORBIDDEN_IN_LABEL = re.compile(r"[\s.:@#\-]")


def check_citations(context: Context) -> Iterator[Finding]:
    for path in context.text_files():
        tree = context.tree(path)
        if tree is None or not tree.xpath(
            "/tei:TEI/tei:teiHeader/tei:encodingDesc/tei:refsDecl[@n='CTS']", namespaces=NSMAP
        ):
            continue  # parse and CapiTainS checks report these
        yield from _text(path, tree)


def _text(path: Path, tree) -> Iterator[Finding]:
    try:
        crefs = cref_passages(tree)
    except PassageError as error:
        yield Finding(path, None, "citation-cref", str(error))
        return
    try:
        units = cite_structure_units(path)
    except PassageError as error:
        yield Finding(path, None, "citation-cite-structure", str(error))
        return

    for passage in crefs:
        label = passage.element.get("n", "")
        if not label or FORBIDDEN_IN_LABEL.search(label):
            yield Finding(
                path,
                passage.element.sourceline,
                "passage-label",
                f"cited element has label {label!r}; labels must be non-empty and contain "
                "no whitespace, '.', ':', '@', '#' or '-'",
            )
        if not normalized_text(passage.element):
            yield Finding(
                path,
                passage.element.sourceline,
                "passage-empty",
                f"passage {passage.ref} has no text",
            )

    counts = Counter(p.ref for p in crefs)
    for passage in crefs:
        if counts[passage.ref] > 1:
            yield Finding(
                path,
                passage.element.sourceline,
                "passage-duplicate",
                f"passage {passage.ref} is cited {counts[passage.ref]} times",
            )

    cref_refs = [p.ref for p in crefs]
    unit_refs = [u.ref for u in units]
    if cref_refs != unit_refs:
        missing_in_cref = [r for r in unit_refs if r not in set(cref_refs)]
        missing_in_structure = [r for r in cref_refs if r not in set(unit_refs)]
        details = []
        if missing_in_cref:
            details.append(f"only citeStructure has {', '.join(missing_in_cref)}")
        if missing_in_structure:
            details.append(f"only cRefPattern has {', '.join(missing_in_structure)}")
        if not details:
            details.append("both list the same passages in a different order")
        yield Finding(
            path,
            None,
            "citation-parity",
            "the two citation declarations disagree: " + "; ".join(details),
        )
        return

    for passage in crefs:
        if counts[passage.ref] > 1:
            continue
        try:
            extracted = extract_passage(path, passage.ref)
        except PassageError as error:
            yield Finding(path, passage.element.sourceline, "citation-parity", str(error))
            continue
        if normalized_text(extracted) != normalized_text(passage.element):
            yield Finding(
                path,
                passage.element.sourceline,
                "citation-parity",
                f"passage {passage.ref} has different text under cRefPattern and citeStructure",
            )
