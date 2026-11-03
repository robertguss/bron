"""The `bron` command line.

Exit status is 0 when every check passes and 1 when any check fails. Findings are
printed one per line as `file:line: check-id: message` so CI logs stay greppable.
"""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path


def _not_yet(name: str) -> int:
    print(f"bron {name}: not available yet", file=sys.stderr)
    return 2


def _check(data_repo: Path, base: Path | None, require_base: bool) -> int:
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
    return 1 if findings else 0


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
    commands.add_parser("serve", help="serve a data repository over DTS 1.0")

    dts = commands.add_parser("dts", help="DTS conformance tools")
    dts_commands = dts.add_subparsers(dest="dts_command", required=True, metavar="command")
    dts_commands.add_parser("verify", help="verify the DTS responses for a data repository")

    convert = commands.add_parser("convert", help="convert a source text to TEI")
    convert_commands = convert.add_subparsers(dest="convert_command", required=True, metavar="text")
    convert_commands.add_parser("gd1", help="Bavinck, Gereformeerde Dogmatiek, 1st edition")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    match args.command:
        case "check":
            return _check(args.data_repo, args.base, args.require_base)
        case "serve":
            return _not_yet("serve")
        case "dts":
            return _not_yet("dts verify")
        case "convert":
            return _not_yet("convert gd1")
    raise AssertionError(f"unhandled command {args.command!r}")


if __name__ == "__main__":
    sys.exit(main())
