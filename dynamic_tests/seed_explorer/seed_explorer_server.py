"""Compatibility entry for the former Seed Explorer server location.

The formal implementation lives in :mod:`airport_sim.server.app`.  Package
imports continue to expose its API, while direct script execution delegates to
the unified public CLI without adding the workspace to ``sys.path``.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any


if __name__ == "__main__" and not __package__:
    workspace_root = Path(__file__).resolve().parents[2]
    raise SystemExit(
        subprocess.call(
            [sys.executable, "-m", "airport_sim", "serve", *sys.argv[1:]],
            cwd=workspace_root,
        )
    )

from airport_sim.server import app as _app

main = _app.main


def __getattr__(name: str) -> Any:
    return getattr(_app, name)


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(dir(_app)))


if __name__ == "__main__":
    main()
