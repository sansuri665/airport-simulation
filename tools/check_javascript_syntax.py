from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
JAVASCRIPT_ROOTS = (ROOT_DIR / "web", ROOT_DIR / "map_research")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check browser JavaScript syntax with Node.js.")
    parser.add_argument(
        "--node",
        default=os.environ.get("NODE_BINARY") or shutil.which("node"),
        help="Path to the Node.js executable. Defaults to NODE_BINARY or node on PATH.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.node:
        print("Node.js was not found; install it or pass --node PATH.", file=sys.stderr)
        return 2
    files = sorted(
        path
        for root in JAVASCRIPT_ROOTS
        if root.is_dir()
        for path in root.rglob("*.js")
        if path.is_file()
    )
    failures: list[tuple[Path, str]] = []
    for path in files:
        result = subprocess.run(
            [str(args.node), "--check", str(path)],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode:
            failures.append((path, (result.stderr or result.stdout).strip()))
    if failures:
        print(f"Found JavaScript syntax errors in {len(failures)} file(s):", file=sys.stderr)
        for path, detail in failures:
            print(f"- {path.relative_to(ROOT_DIR).as_posix()}", file=sys.stderr)
            if detail:
                print(detail, file=sys.stderr)
        return 1
    print(f"Checked JavaScript syntax in {len(files)} browser file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
