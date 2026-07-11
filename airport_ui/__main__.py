from __future__ import annotations

import sys

from airport_sim.cli import main as airport_sim_main


def main() -> None:
    """Compatibility wrapper for the unified Airport CLI."""
    raise SystemExit(airport_sim_main(["serve", *sys.argv[1:]]))


if __name__ == "__main__":
    main()
