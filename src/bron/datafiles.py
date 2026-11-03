"""YAML data files in a Bron data repository, validated against Bron's JSON Schemas."""

import datetime
import json
from collections.abc import Iterator
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, ValidationError
from jsonschema.protocols import Validator

from bron.findings import Finding

SCHEMAS = Path(__file__).parent / "schemas"


@dataclass(frozen=True)
class YamlFile:
    """A loaded YAML file, with its node tree kept for line numbers."""

    path: Path
    data: Any
    node: yaml.Node | None

    def line(self, *keys: str | int) -> int | None:
        node = self.node
        for key in keys:
            if isinstance(node, yaml.MappingNode):
                node = next((value for name, value in node.value if name.value == key), None)
            elif isinstance(node, yaml.SequenceNode) and isinstance(key, int):
                node = node.value[key] if key < len(node.value) else None
            else:
                return None
        return node.start_mark.line + 1 if node is not None else None


def load_yaml(path: Path, check: str) -> YamlFile | Finding:
    """The parsed file, or a finding when it is not valid YAML."""
    text = path.read_text(encoding="utf-8")
    try:
        node = yaml.compose(text, Loader=yaml.SafeLoader)
        data = _iso_dates(yaml.safe_load(text))
    except yaml.MarkedYAMLError as error:
        mark = error.problem_mark or error.context_mark
        line = mark.line + 1 if mark else None
        return Finding(path, line, check, f"not valid YAML: {error.problem or error.context}")
    except (yaml.YAMLError, ValueError) as error:
        # PyYAML raises ValueError for an unquoted date that is not a calendar date.
        return Finding(path, None, check, f"not valid YAML: {error}")
    return YamlFile(path, data, node)


def schema_findings(file: YamlFile, schema: str, check: str, name_key: str) -> Iterator[Finding]:
    """One finding per schema error, located at and named after the record it falls in."""
    for error in _validator(schema).iter_errors(file.data):
        where = list(error.absolute_path)
        record, field = where[:2], ".".join(str(key) for key in where[2:])
        label = _label(file.data, record, name_key)
        detail = f"{field}: {_explain(error)}" if field else _explain(error)
        yield Finding(file.path, file.line(*record), check, f"{label}: {detail}")


@cache
def _validator(schema: str) -> Validator:
    loaded = json.loads((SCHEMAS / schema).read_text(encoding="utf-8"))
    return Draft202012Validator(loaded, format_checker=Draft202012Validator.FORMAT_CHECKER)


def _iso_dates(value: Any) -> Any:
    """YAML loads dates as `datetime.date`; the schema checks them as ISO strings."""
    if isinstance(value, dict):
        return {key: _iso_dates(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_iso_dates(item) for item in value]
    if isinstance(value, datetime.date):
        return value.isoformat()
    return value


def _label(data: Any, record: list[Any], name_key: str) -> str:
    if len(record) < 2 or not isinstance(record[1], int):
        return "file"
    item = data[record[0]][record[1]]
    name = item.get(name_key) if isinstance(item, dict) else None
    return f"record {name!r}" if name else f"record {record[1] + 1}"


def _explain(error: ValidationError) -> str:
    """A subschema's `description` is its plain-words rule; otherwise jsonschema's own message."""
    description = error.schema.get("description") if isinstance(error.schema, dict) else None
    if description is None:
        return error.message
    if isinstance(error.instance, str | int | float):
        return f"{error.instance!r} {description}"
    return description
