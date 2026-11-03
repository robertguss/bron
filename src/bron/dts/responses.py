"""DTS response bodies: JSON-LD objects in a fixed key order, problem bodies, TEI fragments."""

from copy import deepcopy
from typing import Any

from fastapi.responses import JSONResponse
from lxml import etree

from bron.dts.index import Collection, Index, Resource, Unit
from bron.tei import TEI_NS, XML_ID, tei

CONTEXT = "https://dtsapi.org/context/v1.0.json"
DTS_VERSION = "1.0"
DTS_NS = "https://w3id.org/api/dts#"
TEI_MEDIA_TYPE = "application/tei+xml"


class JsonLd(JSONResponse):
    media_type = "application/ld+json"


class Problem(JSONResponse):
    """An RFC 9457 problem body; DTS defines no error body of its own."""

    media_type = "application/problem+json"

    def __init__(self, status: int, title: str, detail: str, **extra: Any) -> None:
        body = {"type": "about:blank", "title": title, "status": status, "detail": detail}
        super().__init__({**body, **extra}, status_code=status)


def entry(base: str) -> dict[str, Any]:
    return {
        "@context": CONTEXT,
        "dtsVersion": DTS_VERSION,
        "@id": f"{base}/",
        "@type": "EntryPoint",
        "collection": f"{base}/collection{{?id,page,nav}}",
        "navigation": f"{base}/navigation{{?resource,ref,start,end,down,tree,page}}",
        "document": f"{base}/document{{?resource,ref,start,end,tree,mediaType}}",
    }


def collection_url(base: str, urn: str) -> str:
    return f"{base}/collection?id={urn}"


def _dublin_core(node: Collection) -> dict[str, Any]:
    found: dict[str, Any] = {}
    if node.titles:
        found["title"] = [{"lang": lang, "value": value} for lang, value in node.titles]
    if node.descriptions:
        found["description"] = [{"lang": lang, "value": value} for lang, value in node.descriptions]
    if node.language:
        found["language"] = [node.language]
    return found


def collection_member(index: Index, node: Collection, base: str) -> dict[str, Any]:
    """A Collection or Resource object, as it appears in a `member` array."""
    resource = node.resource
    found: dict[str, Any] = {
        "@id": node.urn,
        "@type": "Resource" if resource else "Collection",
        "title": node.title,
    }
    if node.descriptions:
        found["description"] = node.descriptions[0][1]
    found["totalParents"] = 0 if node.parent is None else 1
    found["totalChildren"] = len(node.children)
    if dublin_core := _dublin_core(node):
        found["dublinCore"] = dublin_core
    if resource is None:
        found["collection"] = f"{collection_url(base, node.urn)}{{&page,nav}}"
        return found
    found["collection"] = f"{collection_url(base, node.urn)}{{&nav}}"
    found.update(_resource_links(resource, base))
    found["mediaTypes"] = [TEI_MEDIA_TYPE]
    return found


def _resource_links(resource: Resource, base: str) -> dict[str, Any]:
    urn = resource.urn
    return {
        "navigation": f"{base}/navigation?resource={urn}{{&ref,start,end,down,tree,page}}",
        "document": f"{base}/document?resource={urn}{{&ref,start,end,tree,mediaType}}",
        "citationTrees": [{"@type": "CitationTree", "citeStructure": resource.cite_structure}],
    }


def collection(index: Index, node: Collection, base: str, nav: str) -> dict[str, Any]:
    found = {"@context": CONTEXT, "dtsVersion": DTS_VERSION}
    found.update(collection_member(index, node, base))
    if nav == "parents":
        related = [node.parent] if node.parent else []
    elif node.resource is None:
        related = node.children
    else:
        return found
    found["member"] = [collection_member(index, index.collections[urn], base) for urn in related]
    return found


def citable_unit(unit: Unit) -> dict[str, Any]:
    return {
        "identifier": unit.ref,
        "@type": "CitableUnit",
        "level": unit.level,
        "parent": unit.parent,
        "citeType": unit.cite_type,
    }


def navigation(
    index: Index,
    resource: Resource,
    base: str,
    request_id: str,
    anchors: dict[str, Unit],
    members: list[Unit] | None,
) -> dict[str, Any]:
    found: dict[str, Any] = {
        "@context": CONTEXT,
        "dtsVersion": DTS_VERSION,
        "@type": "Navigation",
        "@id": request_id,
        "resource": collection_member(index, index.collections[resource.urn], base),
    }
    for name, unit in anchors.items():
        found[name] = citable_unit(unit)
    if members is not None:
        found["member"] = [citable_unit(unit) for unit in members]
    return found


def tei_fragment(units: list[Unit]) -> bytes:
    """A TEI document whose `dts:wrapper` holds the units, opened by their governing page break.

    The governing page break is the last `pb` at or before the start of the first unit. When
    the unit itself opens with a `pb`, that one already serves. Otherwise a copy is added
    without its `xml:id`, pointing back at the original with `corresp`, so the fragment never
    holds an identifier twice.
    """
    root = etree.Element(tei("TEI"), nsmap={None: TEI_NS})
    root.text = "\n"
    wrapper = etree.SubElement(root, f"{{{DTS_NS}}}wrapper", nsmap={"dts": DTS_NS})
    wrapper.text = "\n"
    wrapper.tail = "\n"
    first = units[0].element
    if _opens_with(first) is not True:
        governing = first.xpath("preceding::tei:pb[1]", namespaces={"tei": TEI_NS})
        if governing:
            wrapper.append(_anchor_copy(governing[0]))
    for unit in units:
        copy = deepcopy(unit.element)
        copy.tail = "\n"
        wrapper.append(copy)
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8")


def _anchor_copy(page_break: etree._Element) -> etree._Element:
    copy = etree.Element(tei("pb"))
    for name, value in page_break.attrib.items():
        if name != XML_ID:
            copy.set(name, value)
    if original := page_break.get(XML_ID):
        copy.set("corresp", f"#{original}")
    copy.tail = "\n"
    return copy


def _opens_with(element: etree._Element) -> bool | None:
    """True when a `pb` comes before any text inside `element`, False when text does,
    None when it holds neither."""
    if element.text and element.text.strip():
        return False
    for child in element:
        if child.tag == tei("pb"):
            return True
        if isinstance(child.tag, str) and (found := _opens_with(child)) is not None:
            return found
        if child.tail and child.tail.strip():
            return False
    return None
