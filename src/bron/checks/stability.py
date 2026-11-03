"""Identifier stability: a change may not remove, reuse, or silently repoint a citation.

The check compares the head data repository against a base checkout (a pull request's base
branch, or the commit before a push). Every passage identifier on the base must survive in
head or be recorded in `identifiers/redirects.yaml`, whose entries are append-only. A
recorded identifier may never be cited again. And where an identifier survives, the text it
points to may not change substantially unless `identifiers/edits.yaml` declares that exact
new text, so two passages trading labels cannot pass unnoticed.
"""

import datetime
import hashlib
import json
from collections.abc import Iterator
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from functools import cache
from pathlib import Path
from typing import Any

import jsonschema
import yaml
from jsonschema.protocols import Validator

from bron.checks import Check, Context
from bron.findings import Finding
from bron.tei import NSMAP
from bron.tei.passages import PassageError, cref_passages
from bron.tei.text import normalized_text

SCHEMAS = Path(__file__).parent.parent / "schemas"
REDIRECTS = Path("identifiers/redirects.yaml")
EDITS = Path("identifiers/edits.yaml")

# Word-level similarity below which a passage counts as rewritten rather than corrected.
# Measured on GD1 vol. 1, §§ 1-5: a one-word change scored at least 0.994, and the 64 pairs
# of neighbouring subparagraphs (what a label swap compares) scored at most 0.113.
SUBSTANTIAL_CHANGE_BELOW = 0.6


@dataclass
class Passage:
    urn: str
    path: Path
    line: int | None
    text: str
    is_leaf: bool


@dataclass
class Snapshot:
    """Every cited passage of one repository state, keyed by full passage URN."""

    passages: dict[str, Passage] = field(default_factory=dict)
    texts: dict[str, list[str]] = field(default_factory=dict)  # text URN -> passage URNs


def stability_check(base: Path | None, *, require_base: bool) -> Check:
    def check_stability(context: Context) -> Iterator[Finding]:
        if base is None or not base.is_dir():
            if require_base or base is not None:
                yield Finding(
                    context.root,
                    None,
                    "stability-base",
                    "identifier stability needs the base checkout, and none was found"
                    + (f" at {base}" if base is not None else ""),
                )
            return
        yield from _compare(context, Context(root=base.resolve()))

    return check_stability


def _snapshot(context: Context) -> Snapshot:
    snapshot = Snapshot()
    for path in context.text_files():
        tree = context.tree(path)
        if tree is None:
            continue
        body = tree.xpath("/tei:TEI/tei:text/tei:body", namespaces=NSMAP)
        text_urn = body[0].get("n") if body else None
        if not text_urn:
            continue
        try:
            passages = cref_passages(tree)
        except PassageError:
            continue  # the citation check reports undeclared or broken citation schemes
        parents = {p.parent for p in passages}
        urns = []
        for passage in passages:
            urn = f"{text_urn}:{passage.ref}"
            urns.append(urn)
            snapshot.passages[urn] = Passage(
                urn=urn,
                path=path,
                line=passage.element.sourceline,
                text=normalized_text(passage.element),
                is_leaf=passage.ref not in parents,
            )
        snapshot.texts[text_urn] = urns
    return snapshot


@cache
def _validator(name: str) -> Validator:
    schema = json.loads((SCHEMAS / f"{name}.schema.json").read_text(encoding="utf-8"))
    return jsonschema.Draft202012Validator(
        schema, format_checker=jsonschema.Draft202012Validator.FORMAT_CHECKER
    )


def _as_json(value: Any) -> Any:
    """YAML dates load as `datetime.date`; JSON Schema validates them as ISO strings."""
    if isinstance(value, dict):
        return {key: _as_json(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_as_json(item) for item in value]
    if isinstance(value, datetime.date):
        return value.isoformat()
    return value


def _load(
    root: Path, relative: Path, schema: str, key: str, check: str
) -> tuple[list[dict[str, Any]], list[Finding]]:
    path = root / relative
    if not path.is_file():
        return [], []
    try:
        document = _as_json(yaml.safe_load(path.read_text(encoding="utf-8")))
    except yaml.YAMLError as error:
        mark = getattr(error, "problem_mark", None)
        line = mark.line + 1 if mark is not None else None
        return [], [Finding(path, line, check, f"{relative} is not valid YAML: {error}")]
    errors = sorted(_validator(schema).iter_errors(document), key=lambda e: list(e.path))
    if errors:
        return [], [
            Finding(
                path,
                None,
                check,
                f"{relative}: {'/'.join(map(str, e.path)) or 'top level'}: {e.message}",
            )
            for e in errors
        ]
    return document[key], []


def _compare(head_context: Context, base_context: Context) -> Iterator[Finding]:
    root = head_context.root
    redirects, problems = _load(root, REDIRECTS, "redirects", "redirects", "stability-redirects")
    yield from problems
    edits, problems = _load(root, EDITS, "edits", "edits", "stability-edits")
    yield from problems
    base_redirects, _ = _load(
        base_context.root, REDIRECTS, "redirects", "redirects", "stability-redirects"
    )

    head = _snapshot(head_context)
    base = _snapshot(base_context)
    redirects_file = root / REDIRECTS

    for entry in base_redirects:
        if entry not in redirects:
            yield Finding(
                redirects_file,
                None,
                "stability-redirects",
                f"the base records {entry['urn']} as {entry['status']}; redirect entries are "
                "append-only and may not be deleted or altered",
            )

    recorded = {entry["urn"]: entry for entry in redirects}
    for urn in recorded:
        if urn in head.passages:
            passage = head.passages[urn]
            yield Finding(
                passage.path,
                passage.line,
                "stability-reuse",
                f"{urn} is recorded in {REDIRECTS} and may never be cited again",
            )
    for entry in redirects:
        if entry["status"] == "redirected":
            yield from _chain(entry, recorded, head, redirects_file)

    yield from _removals(base, head, recorded, root, base_context.root)
    yield from _text_changes(base, head, edits)


def _chain(
    entry: dict[str, Any], recorded: dict[str, dict[str, Any]], head: Snapshot, path: Path
) -> Iterator[Finding]:
    """A redirect must lead, possibly through other redirects, to identifiers head cites."""
    for target in entry["replaced_by"]:
        seen = [entry["urn"]]
        current = target
        while current not in head.passages:
            if current in seen:
                cycle = " -> ".join([*seen, current])
                yield Finding(path, None, "stability-redirects", f"redirect cycle: {cycle}")
                break
            step = recorded.get(current)
            if step is None:
                yield Finding(
                    path,
                    None,
                    "stability-redirects",
                    f"{entry['urn']} redirects to {current}, which no text cites "
                    "and no redirect records",
                )
                break
            if step["status"] == "retired":
                yield Finding(
                    path,
                    None,
                    "stability-redirects",
                    f"{entry['urn']} redirects to {current}, which is retired",
                )
                break
            seen.append(current)
            if len(step["replaced_by"]) != 1:
                break  # a split: each branch is checked from its own entry
            current = step["replaced_by"][0]


def _removals(
    base: Snapshot,
    head: Snapshot,
    recorded: dict[str, dict[str, Any]],
    head_root: Path,
    base_root: Path,
) -> Iterator[Finding]:
    for text_urn, urns in base.texts.items():
        lost = [u for u in urns if u not in head.passages and u not in recorded]
        if not lost:
            continue
        if text_urn not in head.texts:
            where = head_root / base.passages[urns[0]].path.relative_to(base_root)
            yield Finding(
                where,
                None,
                "stability-removed",
                f"text {text_urn} was removed, taking {len(lost)} cited identifiers with it: "
                f"{', '.join(lost)}; record each in {REDIRECTS} or restore the text",
            )
            continue
        for urn in lost:
            where = head_root / base.passages[urn].path.relative_to(base_root)
            yield Finding(
                where,
                None,
                "stability-removed",
                f"{urn} is cited on the base but missing here; record it in {REDIRECTS} "
                "as redirected or retired, or restore it",
            )


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _text_changes(base: Snapshot, head: Snapshot, edits: list[dict[str, Any]]) -> Iterator[Finding]:
    declared = {(edit["urn"], edit["sha256"]) for edit in edits}
    for urn, before in base.passages.items():
        after = head.passages.get(urn)
        if after is None or not after.is_leaf or before.text == after.text:
            continue
        similarity = SequenceMatcher(
            None, before.text.split(), after.text.split(), autojunk=False
        ).ratio()
        if similarity >= SUBSTANTIAL_CHANGE_BELOW:
            continue
        digest = _digest(after.text)
        if (urn, digest) in declared:
            continue
        yield Finding(
            after.path,
            after.line,
            "stability-text-changed",
            f"{urn} now points to substantially different text ({similarity:.0%} similar); "
            f'if this is a deliberate edit, declare it in {EDITS} with sha256: "{digest}"',
        )
