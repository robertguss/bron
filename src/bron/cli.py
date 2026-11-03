"""The `bron` command line.

Exit status is 0 when every check passes and 1 when any check fails. Findings are
printed one per line as `file:line: check-id: message` so CI logs stay greppable.
"""

import argparse
import sys
from collections.abc import Sequence


def _not_yet(name: str) -> int:
    print(f"bron {name}: not available yet", file=sys.stderr)
    return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bron",
        description="Validate a CapiTainS data repository, serve it over DTS, ingest texts.",
    )
    commands = parser.add_subparsers(dest="command", required=True, metavar="command")

    commands.add_parser("check", help="validate a data repository")
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
            return _not_yet("check")
        case "serve":
            return _not_yet("serve")
        case "dts":
            return _not_yet("dts verify")
        case "convert":
            return _not_yet("convert gd1")
    raise AssertionError(f"unhandled command {args.command!r}")


if __name__ == "__main__":
    sys.exit(main())
