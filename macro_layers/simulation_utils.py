from __future__ import annotations

import argparse
from typing import Any


def clamp(value: float, low: float, high: float) -> float:
    """Return value constrained to the inclusive [low, high] interval."""
    return max(low, min(high, value))


def resolve_seeds(args: argparse.Namespace) -> list[int]:
    if args.seed is not None:
        return [args.seed]
    if args.seeds:
        return list(dict.fromkeys(args.seeds))
    return list(range(args.seed_start, args.seed_start + args.seed_count))


def round_record(record: dict[str, Any]) -> dict[str, Any]:
    result = dict(record)
    for key, value in list(result.items()):
        if isinstance(value, float):
            result[key] = round(value, 4)
    return result


def as_float_convert_lookup_default(
    row: dict[str, Any],
    key: str,
    default: float = 0.0,
) -> float:
    value = row.get(key, default)
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def as_float_return_missing_default(
    row: dict[str, Any],
    key: str,
    default: float = 0.0,
) -> float:
    value = row.get(key)
    if value in (None, ""):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    if abs(denominator) <= 1e-9:
        return default
    return numerator / denominator
