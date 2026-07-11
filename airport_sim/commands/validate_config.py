from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path
from typing import Any

from airport_sim.paths import CONFIG_ROOT


class DuplicateJsonKeyError(ValueError):
    """Raised when a JSON object contains an ambiguous duplicate key."""


def _object_without_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateJsonKeyError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def validate_config_tree(config_root: Path = CONFIG_ROOT) -> dict[str, Any]:
    """Validate JSON syntax and duplicate keys for every configuration file."""

    root = config_root.expanduser().resolve()
    errors: list[dict[str, str]] = []
    if not root.is_dir():
        errors.append({"path": str(root), "error": "configuration directory does not exist"})
        paths: list[Path] = []
    else:
        paths = sorted(path for path in root.rglob("*.json") if path.is_file())

    for path in paths:
        try:
            with path.open("r", encoding="utf-8") as handle:
                json.load(handle, object_pairs_hook=_object_without_duplicate_keys)
        except (OSError, UnicodeError, json.JSONDecodeError, DuplicateJsonKeyError) as exc:
            try:
                label = path.relative_to(root).as_posix()
            except ValueError:
                label = str(path)
            errors.append({"path": label, "error": str(exc)})

    return {
        "schemaVersion": "airport-config-validation-v1",
        "configRoot": str(root),
        "fileCount": len(paths),
        "validCount": max(0, len(paths) - len(errors)),
        "invalidCount": len(errors),
        "checks": ["json_syntax", "duplicate_object_keys"],
        "errors": errors,
    }


def validate_config_command(args: Namespace) -> int:
    report = validate_config_tree(Path(args.config_root))
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif report["invalidCount"]:
        print(
            f"Configuration validation failed: {report['invalidCount']} problem(s) "
            f"in {report['configRoot']}."
        )
        for error in report["errors"]:
            print(f"- {error['path']}: {error['error']}")
    else:
        print(
            f"Configuration validation passed: {report['fileCount']} JSON file(s) "
            f"under {report['configRoot']}."
        )
    return 1 if report["invalidCount"] else 0
