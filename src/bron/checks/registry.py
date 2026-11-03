"""The rights registry: where each source copy came from, and each site's terms of use."""

from collections.abc import Iterator

from bron.checks import Context
from bron.datafiles import YamlFile, load_yaml, schema_findings
from bron.findings import Finding

# Each registry file, its schema, and the field that names one of its records.
REGISTRY = (
    ("sources.yaml", "registry-sources.schema.json", "id"),
    ("terms.yaml", "registry-terms.schema.json", "site"),
)


def check_registry(context: Context) -> Iterator[Finding]:
    for name, schema, name_key in REGISTRY:
        path = context.root / "registry" / name
        if not path.is_file():
            continue
        file = load_yaml(path, "registry")
        if isinstance(file, Finding):
            yield file
            continue
        findings = list(schema_findings(file, schema, "registry", name_key))
        yield from findings
        if name == "sources.yaml" and not findings:
            yield from _duplicate_ids(file)


def _duplicate_ids(file: YamlFile) -> Iterator[Finding]:
    seen: set[str] = set()
    for index, source in enumerate(file.data["sources"]):
        if source["id"] in seen:
            yield Finding(
                file.path,
                file.line("sources", index),
                "registry",
                f"record {source['id']!r}: id is already used by an earlier record",
            )
        seen.add(source["id"])


def _duplicate_ids(file: YamlFile) -> Iterator[Finding]:
    seen: set[str] = set()
    for index, source in enumerate(file.data["sources"]):
        if source["id"] in seen:
            yield Finding(
                file.path,
                file.line("sources", index),
                "registry",
                f"record {source['id']!r}: id is already used by an earlier record",
            )
        seen.add(source["id"])
