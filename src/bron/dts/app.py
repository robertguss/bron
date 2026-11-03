"""`bron serve`: a read-only DTS 1.0 resolver over a data repository.

Parameter combinations follow the tables of the DTS 1.0 specification; see README.md
beside this file for the endpoints, Bron's redirect and tombstone answers, and the problem
body every error carries.
"""

from pathlib import Path
from typing import Annotated
from urllib.parse import urlencode, urlsplit

from fastapi import FastAPI, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import RedirectResponse

from bron.dts import responses
from bron.dts.index import DEFAULT_TREE, Index, Resource, Unit, build_index
from bron.dts.responses import JsonLd, Problem

Param = Annotated[str | None, Query()]
Number = Annotated[int | None, Query()]


def create_app(repo: Path, *, base_url: str) -> FastAPI:
    """The resolver for `repo`, answering under `base_url`; raises DataError."""
    index = build_index(repo)
    base = base_url.rstrip("/")
    prefix = urlsplit(base).path
    app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None)

    @app.exception_handler(RequestValidationError)
    async def invalid_parameter(request: Request, error: RequestValidationError) -> Response:
        names = ", ".join(str(e["loc"][-1]) for e in error.errors())
        return Problem(400, "Bad Request", f"invalid value for {names}")

    def entry() -> Response:
        return JsonLd(responses.entry(base))

    app.get(f"{prefix}/")(entry)
    if prefix:
        app.get(prefix)(entry)

    @app.get(f"{prefix}/collection")
    def collection(id: Param = None, page: Number = None, nav: Param = None) -> Response:
        if nav not in (None, "children", "parents"):
            return Problem(400, "Bad Request", "nav must be children or parents")
        if problem := _single_page(page):
            return problem
        node = index.collections.get(id or index.root)
        if node is None:
            return Problem(404, "Not Found", f"no collection or resource {id}")
        return JsonLd(responses.collection(index, node, base, nav or "children"))

    @app.get(f"{prefix}/navigation")
    def navigation(
        request: Request,
        resource: Param = None,
        ref: Param = None,
        start: Param = None,
        end: Param = None,
        down: Number = None,
        tree: Param = None,
        page: Number = None,
    ) -> Response:
        found = _lookup(index, base, "navigation", request, resource, ref, start, end, tree)
        if isinstance(found, Response):
            return found
        text, anchors = found
        if down is not None and down < -1:
            return Problem(400, "Bad Request", "down must be -1, 0 or a positive depth")
        if down is None and not anchors:
            return Problem(400, "Bad Request", "give ref, start and end, or down")
        if down == 0 and "ref" not in anchors:
            return Problem(400, "Bad Request", "down=0 needs a ref")
        if problem := _single_page(page):
            return problem
        depth = None if down == -1 else down
        if "ref" in anchors:
            unit = anchors["ref"]
            if down is None:
                members = None
            elif down == 0:
                members = text.children(text.by_ref[unit.parent] if unit.parent else None)
            else:
                members = text.subtree(unit, depth)
        elif anchors:
            members = None if down is None else text.span(anchors["start"], anchors["end"], depth)
        else:
            members = [u for u in text.units if depth is None or u.level <= depth]
        request_id = f"{base}/navigation?{request.url.query}"
        return JsonLd(responses.navigation(index, text, base, request_id, anchors, members))

    @app.get(f"{prefix}/document")
    def document(
        request: Request,
        resource: Param = None,
        ref: Param = None,
        start: Param = None,
        end: Param = None,
        tree: Param = None,
        mediaType: Param = None,
    ) -> Response:
        found = _lookup(index, base, "document", request, resource, ref, start, end, tree)
        if isinstance(found, Response):
            return found
        text, anchors = found
        if mediaType not in (None, responses.TEI_MEDIA_TYPE):
            return Problem(404, "Not Found", f"{text.urn} is available only as TEI")
        headers = {"Link": f'<{responses.collection_url(base, text.urn)}>; rel="collection"'}
        if "ref" in anchors:
            units = [anchors["ref"]]
        elif anchors:
            units = text.covering(anchors["start"], anchors["end"])
        else:
            content = text.path.read_bytes()
            return Response(content, media_type=responses.TEI_MEDIA_TYPE, headers=headers)
        body = responses.tei_fragment(units)
        return Response(body, media_type=responses.TEI_MEDIA_TYPE, headers=headers)

    return app


def _single_page(page: int | None) -> Response | None:
    """Bron's responses are never paginated, so page 1 is the only page."""
    if page not in (None, 1):
        return Problem(404, "Not Found", f"there is no page {page}; responses have one page")
    return None


def _lookup(
    index: Index,
    base: str,
    endpoint: str,
    request: Request,
    resource: str | None,
    ref: str | None,
    start: str | None,
    end: str | None,
    tree: str | None,
) -> tuple[Resource, dict[str, Unit]] | Response:
    """The resource and the units a Navigation or Document request names, or the answer that
    stops it: an invalid combination, an unknown name, or a redirected or retired ref."""
    if not resource:
        return Problem(400, "Bad Request", "the resource parameter is required")
    if ref is not None and (start is not None or end is not None):
        return Problem(400, "Bad Request", "ref cannot be combined with start or end")
    if (start is None) != (end is None):
        return Problem(400, "Bad Request", "start and end must be given together")
    text = index.resource(resource)
    if text is None:
        return Problem(404, "Not Found", f"no resource {resource}")
    if tree is not None and tree != DEFAULT_TREE:
        return Problem(404, "Not Found", f"{resource} has no citation tree {tree!r}")

    anchors: dict[str, Unit] = {}
    for name, value in (("ref", ref), ("start", start), ("end", end)):
        if value is None:
            continue
        unit = text.by_ref.get(value)
        if unit is None:
            return _gone(index, base, endpoint, request, name, f"{resource}:{value}")
        anchors[name] = unit
    if "start" in anchors and anchors["start"].ordinal > anchors["end"].ordinal:
        return Problem(400, "Bad Request", "start comes after end in the text")
    return text, anchors


def _gone(
    index: Index, base: str, endpoint: str, request: Request, name: str, urn: str
) -> Response:
    """The answer for a ref that is not live: its replacement, its tombstone, or 404."""
    record = index.redirects.get(urn)
    if record is None:
        return Problem(404, "Not Found", f"{urn} is not a passage of this resource")
    if record["status"] == "retired":
        return Problem(
            410,
            "Gone",
            f"{urn} was retired: {record['reason']}",
            urn=urn,
            reason=record["reason"],
            date=record["date"],
        )

    def replaced(target: str) -> str:
        resource, ref = target.rsplit(":", 1)
        params = dict(request.query_params)
        params.update({"resource": resource, name: ref})
        return f"{base}/{endpoint}?{urlencode(params, safe=':,')}"

    targets = record["replaced_by"]
    if len(targets) == 1:
        return RedirectResponse(replaced(targets[0]), status_code=301)
    return Problem(
        300,
        "Multiple Choices",
        f"{urn} was split: {record['reason']}",
        urn=urn,
        reason=record["reason"],
        date=record["date"],
        replaced_by=[{"urn": target, "url": replaced(target)} for target in targets],
    )
