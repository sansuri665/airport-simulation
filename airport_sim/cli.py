from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from airport_sim.commands.cache import cache_command, configure_cache_parser
from airport_sim.commands.run import run_command
from airport_sim.commands.serve import serve_command
from airport_sim.commands.validate_config import validate_config_command
from airport_sim.paths import CONFIG_ROOT


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="airport-sim",
        description="Unified command entry for the Airport simulation workspace.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    run_parser = commands.add_parser(
        "run",
        add_help=False,
        help="Run the existing full-chain model (use 'run --help' for model options).",
    )
    run_parser.set_defaults(passthrough_handler=run_command)

    serve_parser = commands.add_parser(
        "serve",
        add_help=False,
        help="Start the local UI (use 'serve --help' for server options).",
    )
    serve_parser.set_defaults(passthrough_handler=serve_command)

    validate_parser = commands.add_parser(
        "validate-config",
        help="Validate configuration syntax, family schemas, ranges, references, weights, and curves.",
    )
    validate_parser.add_argument(
        "--config-root",
        type=str,
        default=str(CONFIG_ROOT),
        help="Configuration root; defaults to the workspace config directory.",
    )
    validate_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output.")
    validate_parser.set_defaults(command_handler=validate_config_command)

    cache_parser = commands.add_parser("cache", help="Inspect and safely manage generated caches.")
    configure_cache_parser(cache_parser)
    cache_parser.set_defaults(command_handler=cache_command)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    args, remaining = parser.parse_known_args(arguments)

    passthrough_handler = getattr(args, "passthrough_handler", None)
    if passthrough_handler is not None:
        return int(passthrough_handler(remaining))
    if remaining:
        parser.error(f"unrecognized arguments: {' '.join(remaining)}")

    command_handler = getattr(args, "command_handler", None)
    if command_handler is None:  # pragma: no cover - required subparsers prevent this.
        parser.error("a command is required")
    return int(command_handler(args))
