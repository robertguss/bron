"""`bron check`: every validation of a CapiTainS data repository."""

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from pathlib import Path

from lxml import etree

from bron.findings import Finding
from bron.tei.passages import CrefPassage, PassageError, cref_passages

_PARSER = etree.XMLParser(resolve_entities=False, no_network=True, huge_tree=True)


@dataclass
class Context:
    """One data repository under check, with each XML file parsed at most once."""

    root: Path
    _trees: dict[Path, etree._ElementTree | None] = field(default_factory=dict)
    parse_errors: dict[Path, Finding] = field(default_factory=dict)
    _crefs: dict[Path, list[CrefPassage] | PassageError] = field(default_factory=dict)
    notices: list[str] = field(default_factory=list)  # facts worth printing that are not findings

    def tree(self, path: Path) -> etree._ElementTree | None:
        """The parsed file, or None when it is not well-formed (the schema check reports it)."""
        if path not in self._trees:
            try:
                self._trees[path] = etree.parse(str(path), _PARSER)
            except etree.XMLSyntaxError as error:
                self._trees[path] = None
                self.parse_errors[path] = Finding(path, error.lineno, "parse", error.msg)
        return self._trees[path]

    def cref_passages(self, path: Path) -> list[CrefPassage]:
        """The passages a parsed text's cRefPatterns cite, computed once; raises PassageError."""
        if path not in self._crefs:
            tree = self.tree(path)
            if tree is None:
                raise PassageError(f"{path.name} is not well-formed")
            try:
                self._crefs[path] = cref_passages(tree)
            except PassageError as error:
                self._crefs[path] = error
        result = self._crefs[path]
        if isinstance(result, PassageError):
            raise result
        return result

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
    return run_in(Context(root=root.resolve()), checks)


def run_in(context: Context, checks: Iterable[Check]) -> list[Finding]:
    findings: list[Finding] = []
    for check in checks:
        findings.extend(check(context))
    return sorted(set(findings), key=lambda f: (str(f.path), f.line or 0, f.check, f.message))
