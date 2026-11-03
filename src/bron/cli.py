"""The `bron` command line.

Exit status is 0 when every check passes and 1 when any check fails. Findings are
printed one per line as `file:line: check-id: message` so CI logs stay greppable.
"""

import argparse
import re
import sys
from collections.abc import Sequence
from pathlib import Path


def _not_yet(name: str) -> int:
    print(f"bron {name}: not available yet", file=sys.stderr)
    return 2


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
    convert_commands.add_parser("gd1", help="Bavinck, Gereformeerde Dogmatiek, 1st edition")

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
        case "convert":
            return _not_yet("convert gd1")
    raise AssertionError(f"unhandled command {args.command!r}")


if __name__ == "__main__":
    sys.exit(main())
