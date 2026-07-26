from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT_DIR = Path(__file__).resolve().parents[1]
EXCLUDED_DIRECTORIES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "node_modules",
    "output",
    "saves",
}
EXCLUDED_RELATIVE_PREFIXES = {
    ("handoff", "inbox"),
    ("handoff", "outbox"),
    ("handoff", "work"),
}
INLINE_LINK = re.compile(r"!?\[[^\]]*\]\((?P<destination>[^)]+)\)")
EXTERNAL_SCHEMES = {"data", "http", "https", "javascript", "mailto"}


def markdown_files() -> list[Path]:
    return sorted(
        path
        for path in ROOT_DIR.rglob("*.md")
        if not is_excluded_markdown_path(path)
    )


def is_excluded_markdown_path(path: Path) -> bool:
    parts = path.relative_to(ROOT_DIR).parts
    if EXCLUDED_DIRECTORIES.intersection(parts):
        return True
    return any(parts[: len(prefix)] == prefix for prefix in EXCLUDED_RELATIVE_PREFIXES)


def link_target(raw_destination: str) -> str:
    destination = raw_destination.strip()
    if destination.startswith("<"):
        closing = destination.find(">")
        return destination[1:closing] if closing >= 0 else destination[1:]
    return destination.split(maxsplit=1)[0]


def local_path(source: Path, raw_target: str) -> Path | None:
    target = unquote(raw_target.strip())
    if not target or target.startswith(("#", "//")):
        return None
    parsed = urlsplit(target)
    if parsed.scheme.lower() in EXTERNAL_SCHEMES:
        return None
    path_text = parsed.path
    if not path_text:
        return None
    if path_text.startswith("/"):
        return (ROOT_DIR / path_text.lstrip("/")).resolve()
    return (source.parent / path_text).resolve()


def main() -> int:
    files = markdown_files()
    checked = 0
    missing: list[tuple[Path, int, str]] = []
    for source in files:
        content = source.read_text(encoding="utf-8")
        for match in INLINE_LINK.finditer(content):
            target = link_target(match.group("destination"))
            resolved = local_path(source, target)
            if resolved is None:
                continue
            checked += 1
            if not resolved.exists():
                line = content.count("\n", 0, match.start()) + 1
                missing.append((source, line, target))

    if missing:
        print(f"Found {len(missing)} missing local Markdown link(s):", file=sys.stderr)
        for source, line, target in missing:
            print(f"- {source.relative_to(ROOT_DIR).as_posix()}:{line}: {target}", file=sys.stderr)
        return 1
    print(f"Checked {checked} local Markdown link(s) across {len(files)} file(s); none are missing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
