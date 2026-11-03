"""TEI schema validation against the vendored tei_all RelaxNG (TEI P5 4.12.0)."""

from collections.abc import Iterator
from functools import cache
from pathlib import Path

from lxml import etree

from bron.checks import Context
from bron.findings import Finding

SCHEMA = Path(__file__).parent.parent / "schemas" / "tei_all-4.12.0.rng"


@cache
def _tei_all() -> etree.RelaxNG:
    # Compiling tei_all takes several seconds, so it happens once per process.
    return etree.RelaxNG(etree.parse(str(SCHEMA)))


def check_schema(context: Context) -> Iterator[Finding]:
    """Every TEI file under data/ and alignments/ is well-formed and valid against tei_all."""
    for path in context.tei_files():
        tree = context.tree(path)
        if tree is None:
            yield context.parse_errors[path]
            continue
        schema = _tei_all()
        if schema.validate(tree):
            continue
        for error in schema.error_log:
            yield Finding(path, error.line, "schema", error.message)
