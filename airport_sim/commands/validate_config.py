from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

from airport_sim.config_validation import (
    CONFIG_FAMILY_SPECS,
    DuplicateJsonKeyError,
    _object_without_duplicate_keys,
    validate_config_tree,
)


def validate_config_command(args: Namespace) -> int:
    report = validate_config_tree(Path(args.config_root))
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif report["invalidCount"]:
        print(
            f"Configuration validation failed: {report['invalidCount']} invalid file(s), "
            f"{report['issueCount']} problem(s) in {report['configRoot']}."
        )
        for error in report["errors"]:
            print(
                f"- {error['path']} {error['location']} "
                f"[{error['code']}]: {error['message']}"
            )
    else:
        print(
            f"Configuration validation passed: {report['fileCount']} JSON file(s) "
            f"across {report['familyCount']} families under {report['configRoot']}."
        )
    return 1 if report["invalidCount"] else 0


__all__ = [
    "CONFIG_FAMILY_SPECS",
    "DuplicateJsonKeyError",
    "_object_without_duplicate_keys",
    "validate_config_command",
    "validate_config_tree",
]
