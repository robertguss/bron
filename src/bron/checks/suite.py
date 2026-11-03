"""The full set of checks `bron check` runs, in reporting order."""

from pathlib import Path

from bron.checks import Check, Context, run_in
from bron.checks.alignment import check_alignment
from bron.checks.bron_rules import check_bron_rules
from bron.checks.capitains import check_capitains
from bron.checks.citations import check_citations
from bron.checks.registry import check_registry
from bron.checks.schema import check_schema
from bron.checks.stability import stability_check
from bron.checks.tei_constraints import check_tei_constraints
from bron.findings import Finding

ALL_CHECKS: list[Check] = [
    check_schema,
    check_tei_constraints,
    check_bron_rules,
    check_capitains,
    check_citations,
    check_registry,
    check_alignment,
]


def check_repository(
    root: Path, base: Path | None = None, *, require_base: bool = False
) -> tuple[list[Finding], list[str]]:
    """Run every check; identifier stability also compares against `base` when given.

    Returns the findings and the notices: facts worth printing that are not failures.
    """
    context = Context(root=root.resolve())
    findings = run_in(context, [*ALL_CHECKS, stability_check(base, require_base=require_base)])
    return findings, context.notices
