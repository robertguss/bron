"""`bron dts verify`: drive the resolver in-process and check every answer it gives.

Every Collection call, every Navigation call (each citable unit with `down` absent, 0
through one past the tree's depth, and -1), every citable unit and a range from each to
the next one at its level as a Document, and every withdrawn identifier. Each JSON body is
checked against the upstream DTS validator's JSON Schemas when their directory is given.
Each Document must be TEI with a `dts:wrapper` whose text equals the passages it names:
the upstream validator only checks that Document returns something, so passage content
rests on this check. Navigation members must name parents that exist and come in document
order, and named citations must resolve to the expected text.
"""

import json
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from itertools import pairwise
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from fastapi.testclient import TestClient
from httpx2 import Response
from jsonschema import Draft202012Validator
from jsonschema.protocols import Validator
from lxml import etree
from referencing import Registry, Resource
from uritemplate import URITemplate

from bron.dts.app import create_app
from bron.dts.index import Index, Unit, build_index
from bron.dts.index import Resource as Text
from bron.dts.responses import DTS_NS
from bron.tei import tei
from bron.tei.text import normalized_text

BASE = "http://testserver/dts"
SCHEMA_FILES = {
    "entry": "entry_response.schema.json",
    "collection": "collection_response.schema.json",
    "navigation": "navigation_response.schema.json",
}


@dataclass
class Report:
    failures: list[str] = field(default_factory=list)
    collections: int = 0
    navigations: int = 0
    documents: int = 0
    ranges: int = 0
    withdrawn: int = 0

    def summary(self) -> str:
        return (
            f"{self.collections} collection, {self.navigations} navigation, "
            f"{self.documents} document and {self.ranges} range requests, "
            f"{self.withdrawn} withdrawn identifiers"
        )


def verify(
    repo: Path,
    *,
    expectations: Iterable[tuple[str, str]] = (),
    schemas: Path | None = None,
) -> Report:
    """Check every answer the resolver gives for `repo`; raises DataError if it cannot start."""
    index = build_index(repo)
    client = TestClient(
        create_app(repo, base_url=BASE), raise_server_exceptions=False, follow_redirects=False
    )
    run = _Run(index, client, _validators(schemas) if schemas else {})
    run.entry()
    run.collections()
    for node in index.collections.values():
        if node.resource is not None:
            run.text(node.resource)
    run.withdrawn()
    for urn, prefix in expectations:
        run.expect(urn, prefix)
    return run.report


def _validators(folder: Path) -> dict[str, Validator]:
    registry: Registry = Registry()
    for path in sorted(folder.glob("*.json")):
        contents = json.loads(path.read_text(encoding="utf-8"))
        registry = registry.with_resource(path.name, Resource.from_contents(contents))
    return {
        kind: Draft202012Validator(registry.contents(name), registry=registry)
        for kind, name in SCHEMA_FILES.items()
    }


@dataclass
class _Run:
    index: Index
    client: TestClient
    validators: dict[str, Validator]
    report: Report = field(default_factory=Report)
    templates: dict[str, URITemplate] = field(default_factory=dict)

    def fail(self, where: str, check: str, message: str) -> None:
        self.report.failures.append(f"{where}: {check}: {message}")

    def get(self, endpoint: str, **values: Any) -> tuple[str, Response]:
        url = self.templates[endpoint].expand(values)
        return url, self.client.get(url)

    def json(self, kind: str, url: str, response: Response, status: int = 200) -> Any:
        """The JSON body of a successful response, checked against its schema."""
        if response.status_code != status:
            self.fail(url, "dts-status", f"answered {response.status_code}, expected {status}")
            return None
        if not response.headers.get("content-type", "").startswith("application/ld+json"):
            self.fail(url, "dts-media-type", "JSON responses must be application/ld+json")
        body = response.json()
        if validator := self.validators.get(kind):
            for error in validator.iter_errors(body):
                path = "/".join(str(part) for part in error.absolute_path) or "the body"
                self.fail(url, "dts-schema", f"{path}: {error.message}")
        return body

    def entry(self) -> None:
        url = f"{BASE}/"
        body = self.json("entry", url, self.client.get(url))
        self.templates = {
            endpoint: URITemplate(body[endpoint])
            for endpoint in ("collection", "navigation", "document")
        }

    def collections(self) -> None:
        for urn in self.index.collections:
            for nav in ("children", "parents"):
                self.report.collections += 1
                url, response = self.get("collection", id=urn, nav=nav)
                self.json("collection", url, response)

    def text(self, text: Text) -> None:
        root = text.units[0].element.getroottree() if text.units else None
        position = {id(element): n for n, element in enumerate(root.iter())} if root else {}
        known = self.navigation_tree(text)
        depth = max((unit.level for unit in text.units), default=0)
        for unit in text.units:
            for down in (None, *range(depth + 2), -1):
                self.navigate(text, position, known, ref=unit.ref, down=down)
        for down in (*range(1, depth + 2), -1):
            self.navigate(text, position, known, down=down)
        for identifier in known:
            unit = text.by_ref.get(identifier)
            if unit is None:
                self.fail(text.urn, "dts-member", f"Navigation lists {identifier}, not a unit")
            else:
                self.document(text, [unit], ref=identifier)
        by_level: dict[int, list[Unit]] = {}
        for unit in text.units:
            by_level.setdefault(unit.level, []).append(unit)
        for same_level in by_level.values():
            for start, end in pairwise(same_level):
                self.document(text, [start, end], start=start.ref, end=end.ref)
            if len(same_level) > 2:
                first, last = same_level[0], same_level[-1]
                self.document(text, same_level, start=first.ref, end=last.ref)

    def navigation_tree(self, text: Text) -> dict[str, dict]:
        """Every unit the whole-tree Navigation lists, by identifier."""
        url, response = self.get("navigation", resource=text.urn, down=-1)
        body = self.json("navigation", url, response)
        members = body.get("member", []) if body else []
        return {member["identifier"]: member for member in members}

    def navigate(
        self, text: Text, position: dict[int, int], known: dict[str, dict], **values: Any
    ) -> None:
        self.report.navigations += 1
        if values.get("down") is not None:
            values["down"] = str(values["down"])  # uritemplate expands the integer 0 as empty
        url, response = self.get("navigation", resource=text.urn, **values)
        body = self.json("navigation", url, response)
        if body is None:
            return
        members = body.get("member") or []
        for member in members:
            parent = member.get("parent")
            if parent is None:
                continue
            if parent not in known:
                self.fail(
                    url,
                    "dts-parent",
                    f"{member['identifier']} names parent {parent}, which is not a unit",
                )
            elif known[parent]["level"] != member["level"] - 1:
                self.fail(
                    url, "dts-parent", f"{member['identifier']} is not a level below {parent}"
                )
        places = []
        for member in members:
            unit = text.by_ref.get(member["identifier"])
            if unit is None:
                self.fail(url, "dts-member", f"{member['identifier']} is not a unit of the text")
                return
            places.append(position[id(unit.element)])
        if places != sorted(places):
            self.fail(url, "dts-order", "members are not in document order")

    def document(self, text: Text, units: list[Unit], **values: Any) -> None:
        if "ref" in values:
            self.report.documents += 1
        else:
            self.report.ranges += 1
        url, response = self.get("document", resource=text.urn, **values)
        fragment = self.fragment(url, response)
        if fragment is None:
            return
        expected = " ".join(normalized_text(unit.element) for unit in units)
        if normalized_text(fragment) != expected:
            self.fail(url, "dts-text", "the fragment's text differs from the passages it names")

    def fragment(self, url: str, response: Response) -> etree._Element | None:
        """The `dts:wrapper` of a Document response, or None after reporting why not."""
        if response.status_code != 200:
            self.fail(url, "dts-status", f"answered {response.status_code}, expected 200")
            return None
        if not response.headers.get("content-type", "").startswith("application/tei+xml"):
            self.fail(url, "dts-media-type", "Document must answer application/tei+xml")
        try:
            root = etree.fromstring(response.content)
        except etree.XMLSyntaxError as error:
            self.fail(url, "dts-document", f"not well-formed XML: {error}")
            return None
        wrapper = root.find(f"{{{DTS_NS}}}wrapper")
        if root.tag != tei("TEI") or wrapper is None:
            self.fail(url, "dts-document", "a fragment must be <TEI> holding a <dts:wrapper>")
            return None
        return wrapper

    def withdrawn(self) -> None:
        for urn, record in self.index.redirects.items():
            self.report.withdrawn += 1
            resource, ref = urn.rsplit(":", 1)
            for endpoint in ("navigation", "document"):
                url, response = self.get(endpoint, resource=resource, ref=ref)
                for problem in _withdrawn_problems(endpoint, record, response):
                    self.fail(url, "dts-withdrawn", f"{urn}: {problem}")

    def expect(self, urn: str, prefix: str) -> None:
        resource, ref = urn.rsplit(":", 1)
        url, response = self.get("document", resource=resource, ref=ref)
        if response.status_code != 200:
            self.fail(url, "dts-expect", f"{urn} answered {response.status_code}")
            return
        fragment = self.fragment(url, response)
        if fragment is None:
            return
        text = normalized_text(fragment)
        wanted = " ".join(prefix.split())
        if not text.startswith(wanted):
            self.fail(
                url,
                "dts-expect",
                f"{urn} should begin {wanted!r} but begins {text[: len(wanted) + 20]!r}",
            )


def _withdrawn_problems(endpoint: str, record: dict, response: Response) -> Iterator[str]:
    status = response.status_code
    if record["status"] == "retired":
        expected = 410
    else:
        expected = 301 if len(record["replaced_by"]) == 1 else 300
    if status != expected:
        yield f"answered {status}, expected {expected}"
        return
    if expected == 301:
        resource, ref = record["replaced_by"][0].rsplit(":", 1)
        location = f"{BASE}/{endpoint}?{urlencode({'resource': resource, 'ref': ref}, safe=':')}"
        if response.headers.get("location") != location:
            yield f"redirects to {response.headers.get('location')}, expected {location}"
        return
    body = response.json()
    if body.get("urn") != record["urn"]:
        yield f"the problem body names {body.get('urn')!r}"
    if expected == 410 and (body.get("reason"), body.get("date")) != (
        record["reason"],
        record["date"],
    ):
        yield "the tombstone does not carry the recorded reason and date"
    if expected == 300 and [r.get("urn") for r in body.get("replaced_by", [])] != list(
        record["replaced_by"]
    ):
        yield "the body does not list the recorded replacements"
