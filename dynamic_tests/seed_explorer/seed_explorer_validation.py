from __future__ import annotations

import math
from collections.abc import Collection
from typing import Any


def as_float(value: Any, default: float = 0.0) -> float:
    if value in (None, ""):
        return default
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if math.isnan(number) or math.isinf(number):
        return default
    return number


def as_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def clean_seed(value: Any) -> int:
    try:
        seed = int(str(value).strip())
    except (TypeError, ValueError):
        raise ValueError("seed must be an integer")
    if seed < 0:
        raise ValueError("seed must be non-negative")
    return seed


def clean_years(value: Any) -> int:
    try:
        years = int(str(value).strip())
    except (TypeError, ValueError):
        return 60
    return max(5, min(90, years))


def clean_operation_mode(value: Any, allowed_modes: Collection[str]) -> str:
    mode = str(value or "replay").strip()
    if mode not in allowed_modes:
        raise ValueError(f"unsupported operation mode: {mode}")
    return mode
