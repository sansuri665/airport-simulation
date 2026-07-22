from __future__ import annotations

import argparse
import math
from typing import Any


def clamp(value: float, low: float, high: float) -> float:
    """Return value constrained to the inclusive [low, high] interval."""
    return max(low, min(high, value))


def require_finite(name: str, value: float) -> None:
    """Reject non-finite configured values before they enter a simulation row."""
    if not math.isfinite(float(value)):
        raise ValueError(f"{name} must be finite")


def require_in_range(name: str, value: float, low: float, high: float) -> None:
    """Require a configured value to stay inside an inclusive model boundary."""
    require_finite(name, value)
    if value < low or value > high:
        raise ValueError(f"{name} must be in [{low}, {high}]")


def require_positive(name: str, value: float) -> None:
    """Require a finite value that is strictly greater than zero."""
    require_finite(name, value)
    if value <= 0.0:
        raise ValueError(f"{name} must be positive")


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
