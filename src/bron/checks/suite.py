"""The full set of checks `bron check` runs, in reporting order."""

from pathlib import Path

from bron.checks import Check, run_checks
from bron.checks.bron_rules import check_bron_rules
from bron.checks.capitains import check_capitains
from bron.checks.citations import check_citations
from bron.checks.schema import check_schema
from bron.checks.tei_constraints import check_tei_constraints
from bron.findings import Finding

ALL_CHECKS: list[Check] = [
    check_schema,
    check_tei_constraints,
    check_bron_rules,
    check_capitains,
    check_citations,
]


def check_repository(root: Path) -> list[Finding]:
    return run_checks(root, ALL_CHECKS)
