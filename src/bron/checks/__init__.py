"""`bron check`: every validation of a CapiTainS data repository."""

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from pathlib import Path

from lxml import etree

from bron.findings import Finding

_PARSER = etree.XMLParser(resolve_entities=False, no_network=True, huge_tree=True)


@dataclass
class Context:
    """One data repository under check, with each XML file parsed at most once."""

    root: Path
    _trees: dict[Path, etree._ElementTree | None] = field(default_factory=dict)
    parse_errors: dict[Path, Finding] = field(default_factory=dict)

    def tree(self, path: Path) -> etree._ElementTree | None:
        """The parsed file, or None when it is not well-formed (the schema check reports it)."""
        if path not in self._trees:
            try:
                self._trees[path] = etree.parse(str(path), _PARSER)
            except etree.XMLSyntaxError as error:
                self._trees[path] = None
                self.parse_errors[path] = Finding(path, error.lineno, "parse", error.msg)
        return self._trees[path]

    def text_files(self) -> list[Path]:
        """TEI texts under `data/`: every XML file except CapiTainS metadata."""
        data = self.root / "data"
        if not data.is_dir():
            return []
        return sorted(p for p in data.rglob("*.xml") if p.name != "__cts__.xml")

    def alignment_files(self) -> list[Path]:
        alignments = self.root / "alignments"
        return sorted(alignments.rglob("*.xml")) if alignments.is_dir() else []

    def tei_files(self) -> list[Path]:
        return self.text_files() + self.alignment_files()


Check = Callable[[Context], Iterable[Finding]]


def run_checks(root: Path, checks: Iterable[Check]) -> list[Finding]:
    context = Context(root=root.resolve())
    findings: list[Finding] = []
    for check in checks:
        findings.extend(check(context))
    return sorted(set(findings), key=lambda f: (str(f.path), f.line or 0, f.check, f.message))
