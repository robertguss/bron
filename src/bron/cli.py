"""The `bron` command line.

Exit status is 0 when every check passes and 1 when any check fails. Findings are
printed one per line as `file:line: check-id: message` so CI logs stay greppable.
`bron ocr sample` exits 3 when pages still need a Greek and Hebrew judgment before the draw
can finish, and any command exits 2 on a usage error or a missing optional extra.
"""

import argparse
import re
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path


def _literal(text: str) -> str:
    """Pull-request text as one line of Markdown that renders exactly as written."""
    return re.sub(r"([\\`*_{}\[\]()#+!|<>&~-])", r"\\\1", " ".join(text.split()))


def _summary(head: Path, base: Path) -> str:
    """Markdown listing the identifier records new since the base, for a CI job summary."""
    from bron.checks.stability import new_records

    lines = ["### Identifier records new since the base", ""]
    for relative, records in new_records(head, base).items():
        if not records:
            lines.append(f"- {relative}: none")
            continue
        lines.append(f"- {relative}:")
        for record in records:
            change = record.get("status", "edit")
            if replaced_by := record.get("replaced_by"):
                change += " to " + ", ".join(_literal(urn) for urn in replaced_by)
            lines.append(
                f"  - {_literal(record['urn'])} {change}: {_literal(record['reason'])} "
                f"({_literal(str(record['date']))})"
            )
    return "\n".join([*lines, ""])


def _check(data_repo: Path, base: Path | None, require_base: bool, summary: Path | None) -> int:
    from bron.checks.suite import check_repository

    if not data_repo.is_dir():
        print(f"bron check: {data_repo} is not a directory", file=sys.stderr)
        return 2
    if base is None and not require_base:
        print("bron check: no --base given, so identifier stability was skipped", file=sys.stderr)
    findings, notices = check_repository(data_repo, base, require_base=require_base)
    for notice in notices:
        print(f"bron check: {notice}", file=sys.stderr)
    root = data_repo.resolve()
    for finding in findings:
        print(finding.render(root))
    print(f"{len(findings)} finding{'s' if len(findings) != 1 else ''}", file=sys.stderr)
    if summary is not None and base is not None and base.is_dir():
        with summary.open("a", encoding="utf-8") as out:
            out.write(_summary(data_repo, base))
    return 1 if findings else 0


def _serve(data_repo: Path, host: str, port: int, base_url: str | None) -> int:
    import uvicorn

    from bron.dts.app import create_app
    from bron.dts.index import DataError

    try:
        app = create_app(data_repo, base_url=base_url or f"http://{host}:{port}")
    except DataError as error:
        print(f"bron serve: {error}", file=sys.stderr)
        return 1
    uvicorn.run(app, host=host, port=port)
    return 0


def _missing_extra(command: str, error: ModuleNotFoundError) -> int:
    print(
        f"bron {command}: needs {error.name}, from bron's convert extra "
        "(uv sync installs it; pip install 'bron[convert]' otherwise)",
        file=sys.stderr,
    )
    return 2


def _page_map(registry: Path, cache: Path, map_path: Path | None) -> int:
    from bron.convert.gd1 import ConversionError
    from bron.convert.gd1.pagemap import MAP, HashMismatch, remeasure

    target = map_path or MAP
    try:
        result = remeasure(registry, cache, target)
    except ModuleNotFoundError as error:
        return _missing_extra("convert gd1-page-map", error)
    except (ConversionError, HashMismatch, FileNotFoundError, KeyError) as error:
        print(f"bron convert gd1-page-map: {error}", file=sys.stderr)
        return 1
    for volume, pdf, read in result.outliers:
        print(f"vol. {volume}: PDF page {pdf} reads {read!r}, which its neighbours rule out")
    for volume, page in result.unresolved:
        print(f"vol. {volume}: page {page} is unresolved: review it on the scan")
    for conflict in result.conflicts:
        print(f"conflict: {conflict}")
    print(
        f"bron convert gd1-page-map: wrote {target}; {len(result.interpolated)} interpolated, "
        f"{len(result.unresolved)} unresolved, {len(result.conflicts)} conflicts",
        file=sys.stderr,
    )
    return 0 if result.complete else 1


def _convert_gd1(registry: Path, cache: Path, commit: str, out: Path) -> int:
    from bron.convert.gd1 import ConversionError
    from bron.convert.gd1.fetch import FetchError

    try:
        from bron.convert.gd1.emit import convert
    except ModuleNotFoundError as error:
        return _missing_extra("convert gd1", error)

    try:
        result = convert(registry, cache, commit)
    except (ConversionError, FetchError, FileNotFoundError, KeyError) as error:
        print(f"bron convert gd1: {error}", file=sys.stderr)
        return 1
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(result.tei)
    for volume in result.volumes:
        pages = volume.pages
        inserted = ", ".join(pages.inserted) or "none"
        relabelled = ", ".join(f"{page} (shows {shown!r})" for page, shown in pages.malformed)
        print(
            f"vol. {volume.number}: {len(volume.sections)} sections, {len(pages.found)} page "
            f"breaks (inserted: {inserted}; numbered from their anchor: {relabelled or 'none'}), "
            f"{volume.corrections} corrections"
        )
        tags = volume.languages
        print(
            f"vol. {volume.number}: language tags kept from the transcribers: "
            f"{_counts(tags.carried)}; added by script: {_counts(tags.script)}; "
            f"added by identification: {_counts(tags.statistical)}"
        )
    for number, section, missing in result.gaps:
        print(f"numbering gap allowed by the page map: vol. {number}, § {section}, no {missing}")
    sections = sum(len(volume.sections) for volume in result.volumes)
    print(f"bron convert gd1: wrote {out} with {sections} sections", file=sys.stderr)
    return 0


def _counts(counts: Mapping[str, int]) -> str:
    return ", ".join(f"{code} {n}" for code, n in sorted(counts.items())) or "none"


def _expectation(raw: str) -> tuple[str, str]:
    urn, separator, prefix = raw.partition("=")
    if not separator or not urn or not prefix:
        raise ValueError(raw)
    return urn, prefix


def _verify(data_repo: Path, expect: list[str], schemas: Path | None) -> int:
    from bron.dts.index import DataError
    from bron.dts.verify import verify

    try:
        expectations = [_expectation(raw) for raw in expect]
    except ValueError as error:
        print(f"bron dts verify: --expect {error} must be URN=TEXT", file=sys.stderr)
        return 2
    if schemas is None:
        print(
            "bron dts verify: no --schemas given, so JSON Schema validation was skipped",
            file=sys.stderr,
        )
    try:
        report = verify(data_repo, expectations=expectations, schemas=schemas)
    except DataError as error:
        print(f"bron dts verify: {error}", file=sys.stderr)
        return 1
    for failure in report.failures:
        print(failure)
    print(f"bron dts verify: {report.summary()}", file=sys.stderr)
    print(
        f"{len(report.failures)} failure{'s' if len(report.failures) != 1 else ''}", file=sys.stderr
    )
    return 1 if report.failures else 0


def _ocr_missing(command: str, error: ModuleNotFoundError) -> int:
    print(
        f"bron ocr {command}: needs {error.name}, from bron's ocr extra "
        "(uv sync installs it; pip install 'bron[ocr]' otherwise)",
        file=sys.stderr,
    )
    return 2


def _ocr(args: argparse.Namespace) -> int:
    from bron.ocr import OcrError

    try:
        return _ocr_command(args)
    except ModuleNotFoundError as error:
        return _ocr_missing(args.ocr_command, error)
    except (OcrError, FileNotFoundError, KeyError) as error:
        print(f"bron ocr {args.ocr_command}: {error}", file=sys.stderr)
        return 1


def _ocr_command(args: argparse.Namespace) -> int:
    from bron.ocr import pipeline, sources
    from bron.ocr.download import Downloader
    from bron.ocr.manifest import Manifest

    command = args.ocr_command
    if command == "span-check":
        manifest = Manifest.load(args.manifest)
        pipeline.mark_spans_checked(manifest, args.pages, args.by)
        manifest.write(args.manifest)
        print(f"bron ocr span-check: marked {len(args.pages)} spans checked", file=sys.stderr)
        return 0
    downloader = Downloader(args.cache, sources.SPACING)
    if command == "packet":
        from bron.ocr.packets import round1

        written = round1(Manifest.load(args.manifest), args.cache, args.rules, args.out)
        print(f"bron ocr packet: wrote {len(written)} files to {args.out}", file=sys.stderr)
        return 0
    if command == "verify":
        manifest = Manifest.load(args.manifest)
        problems = manifest.verify_sources(args.cache)
        if args.committed is not None:
            problems += manifest.verify_committed(args.committed)
        for problem in problems:
            print(problem)
        print(f"bron ocr verify: {len(problems)} problems", file=sys.stderr)
        return 1 if problems else 0
    registry = sources.load_registry(args.registry)
    if command == "sources":
        pipeline.fetch_sources(registry, downloader)
        print("bron ocr sources: every source is cached and verified", file=sys.stderr)
        return 0
    volumes = {n: pipeline.read_volume(registry, downloader, n) for n in sources.VOLUMES}
    if command == "sample":
        from bron.ocr.sample import NeedJudgments

        judgments, rows = pipeline.load_judgments(args.screening)
        result = pipeline.draw(volumes, args.seed_commit, judgments)
        if isinstance(result, NeedJudgments):
            listed = ", ".join(f"vol. {v} p. {p}" for v, p in result.pages)
            print(f"judge these pages for Greek and Hebrew, then rerun: {listed}")
            if args.sheets is not None:
                for sheet in pipeline.contact_sheets(volumes, result.pages, args.sheets):
                    print(f"contact sheet: {sheet}")
            return 3
        manifest = Manifest()
        pipeline.write_sample(manifest, volumes, args.seed_commit, result, rows)
        manifest.write(args.out)
        for page in manifest.data["pages"]:
            print(f"sampled: {page['id']}")
        print(f"bron ocr sample: wrote {args.out}", file=sys.stderr)
        return 0
    if command == "fetch":
        manifest = Manifest.load(args.manifest)
        pipeline.fetch_pages(manifest, volumes, downloader, args.cache)
        manifest.write(args.manifest)
        print(f"bron ocr fetch: updated {args.manifest}", file=sys.stderr)
        return 0
    if command == "spans":
        manifest = Manifest.load(args.manifest)
        problems = pipeline.locate_spans(
            manifest, registry, downloader, args.cache, volumes, args.renders
        )
        manifest.write(args.manifest)
        for problem in problems:
            print(problem)
        print(f"bron ocr spans: updated {args.manifest}", file=sys.stderr)
        return 1 if problems else 0
    raise AssertionError(f"unhandled ocr command {command!r}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bron",
        description="Validate a CapiTainS data repository, serve it over DTS, ingest texts.",
    )
    commands = parser.add_subparsers(dest="command", required=True, metavar="command")

    check = commands.add_parser("check", help="validate a data repository")
    check.add_argument("data_repo", type=Path, help="root of a CapiTainS data repository")
    check.add_argument(
        "--base",
        type=Path,
        help="a checkout of the same repository at the base commit, for identifier stability",
    )
    check.add_argument(
        "--require-base",
        action="store_true",
        help="fail when the base checkout is missing instead of skipping identifier stability",
    )
    check.add_argument(
        "--summary",
        type=Path,
        help="append, as Markdown, the redirect and edit records that are new since the base",
    )
    serve = commands.add_parser("serve", help="serve a data repository over DTS 1.0")
    serve.add_argument("data_repo", type=Path, help="root of a CapiTainS data repository")
    serve.add_argument("--host", default="127.0.0.1", help="interface to listen on")
    serve.add_argument("--port", type=int, default=8000, help="port to listen on")
    serve.add_argument(
        "--base-url",
        help="public URL the endpoints answer under (default: http://<host>:<port>)",
    )

    dts = commands.add_parser("dts", help="DTS conformance tools")
    dts_commands = dts.add_subparsers(dest="dts_command", required=True, metavar="command")
    verify = dts_commands.add_parser(
        "verify", help="verify the DTS responses for a data repository"
    )
    verify.add_argument("data_repo", type=Path, help="root of a CapiTainS data repository")
    verify.add_argument(
        "--expect",
        action="append",
        default=[],
        metavar="URN=TEXT",
        help="the passage URN must resolve to text beginning TEXT (repeatable)",
    )
    verify.add_argument(
        "--schemas",
        type=Path,
        help="directory of the DTS validator's JSON Schemas to check each response against",
    )

    convert = commands.add_parser("convert", help="convert a source text to TEI")
    convert_commands = convert.add_subparsers(dest="convert_command", required=True, metavar="text")
    gd1 = convert_commands.add_parser("gd1", help="Bavinck, Gereformeerde Dogmatiek, 1st edition")
    gd1.add_argument(
        "--registry", type=Path, required=True, help="bron-data's registry/sources.yaml"
    )
    gd1.add_argument(
        "--cache", type=Path, required=True, help="directory the source HTML is cached in"
    )
    gd1.add_argument(
        "--bron-commit", required=True, help="the bron commit converting, recorded in the header"
    )
    gd1.add_argument("--out", type=Path, required=True, help="the TEI file to write")
    page_map = convert_commands.add_parser(
        "gd1-page-map", help="re-measure the GD¹ page map from the cached DBNL scan PDFs"
    )
    page_map.add_argument(
        "--registry", type=Path, required=True, help="bron-data's registry/sources.yaml"
    )
    page_map.add_argument(
        "--cache", type=Path, required=True, help="directory holding the downloaded scan PDFs"
    )
    page_map.add_argument(
        "--map", type=Path, help="page map to rewrite (default: the one shipped with bron)"
    )

    ocr = commands.add_parser("ocr", help="the GD² OCR sample test")
    ocr_commands = ocr.add_subparsers(dest="ocr_command", required=True, metavar="step")

    def ocr_step(
        name: str, help_: str, *, registry: bool = True, cache: bool = True
    ) -> argparse.ArgumentParser:
        step = ocr_commands.add_parser(name, help=help_)
        if registry:
            step.add_argument(
                "--registry", type=Path, required=True, help="bron-data's registry/sources.yaml"
            )
        if cache:
            step.add_argument(
                "--cache", type=Path, required=True, help="cache directory, outside any repository"
            )
        return step

    ocr_step("sources", "fetch and verify both printings' sources into the cache")
    draw = ocr_step("sample", "draw the seeded sample of second-printing pages")
    draw.add_argument(
        "--seed-commit", required=True, help="the bron-data commit whose SHA seeds the draw"
    )
    draw.add_argument("--screening", type=Path, help="YAML of Greek and Hebrew judgments")
    draw.add_argument("--sheets", type=Path, help="directory for contact sheets to judge")
    draw.add_argument("--out", type=Path, required=True, help="the manifest to write")
    fetch = ocr_step("fetch", "fetch the sampled pages' scans and ALTO into the cache")
    fetch.add_argument("--manifest", type=Path, required=True, help="the sample manifest")
    spans = ocr_step("spans", "find each sampled page's words in the fourth printing")
    spans.add_argument("--manifest", type=Path, required=True, help="the sample manifest")
    spans.add_argument("--renders", type=Path, help="directory for scans to check spans on")
    checked = ocr_step(
        "span-check", "record that spans were checked on the scans", registry=False, cache=False
    )
    checked.add_argument("--manifest", type=Path, required=True, help="the sample manifest")
    checked.add_argument("--by", required=True, help="who checked the spans")
    checked.add_argument("pages", nargs="+", help="ids of the pages whose spans match the scans")
    packet = ocr_step("packet", "write the reader's round-1 packet", registry=False)
    packet.add_argument("--manifest", type=Path, required=True, help="the sample manifest")
    packet.add_argument("--rules", type=Path, required=True, help="the transcription rules")
    packet.add_argument("--out", type=Path, required=True, help="an empty packet directory")
    check = ocr_step("verify", "check the manifest's hashes", registry=False)
    check.add_argument("--manifest", type=Path, required=True, help="the sample manifest")
    check.add_argument(
        "--committed", type=Path, help="root the committed files are relative to, to check too"
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    match args.command:
        case "check":
            return _check(args.data_repo, args.base, args.require_base, args.summary)
        case "serve":
            return _serve(args.data_repo, args.host, args.port, args.base_url)
        case "dts":
            return _verify(args.data_repo, args.expect, args.schemas)
        case "convert" if args.convert_command == "gd1-page-map":
            return _page_map(args.registry, args.cache, args.map)
        case "convert":
            return _convert_gd1(args.registry, args.cache, args.bron_commit, args.out)
        case "ocr":
            return _ocr(args)
    raise AssertionError(f"unhandled command {args.command!r}")


if __name__ == "__main__":
    sys.exit(main())
