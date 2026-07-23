"""Pure city passenger-demand mapping primitives for G3.

This module deliberately performs no file I/O and consumes no random numbers.
It separates the city total path from the five-component structural path:

* the regional total index enters city total exactly once;
* component indices enter only as ratios to that regional total;
* city configuration controls bounded long-run and Seed-relative factors;
* component shares are normalized before passenger volumes are allocated.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping


COMPONENTS = ("business", "leisure", "vfr", "long_haul", "transfer")

CITY_INDEX_BOUNDARIES: dict[str, tuple[float, float]] = {
    "business": (65.0, 245.0),
    "leisure": (55.0, 230.0),
    "vfr": (65.0, 225.0),
    "long_haul": (55.0, 210.0),
    "transfer": (45.0, 185.0),
}

# The regional common path is authoritative for city total demand.  It is
# linear through the ordinary 100 -> 150 range, then blends a saturating mature-
# market response with a small linear tail.  The tail keeps the mapping
# unbounded, so stronger regions and Seeds never converge on a fixed plateau.
REGIONAL_TOTAL_FACTOR_FLOOR = 0.0
REGIONAL_TOTAL_NUMERIC_SAFETY_CAP = 1.0e6
REGIONAL_TOTAL_LINEAR_CEILING = 1.5
REGIONAL_TOTAL_SOFT_SPAN = 1.5
REGIONAL_TOTAL_LINEAR_TAIL_WEIGHT = 0.10
CITY_LONG_TERM_BIAS_ELASTICITY = 0.40
_RELATIVE_SIGNAL_FLOOR = 1.0e-6
_RELATIVE_SIGNAL_CAP = 1.0e6


@dataclass(frozen=True)
class ComponentBoundaryDiagnostic:
    raw_index: float
    final_index: float
    boundary_state: str
    floor_applied: int
    cap_applied: int


def _finite(value: float, fallback: float) -> float:
    number = float(value)
    return number if math.isfinite(number) else fallback


def _clamp(value: float, lower: float, upper: float) -> float:
    return min(upper, max(lower, value))


def regional_total_factor(regional_total_index: float) -> float:
    """Convert the dimensionless regional index to the sole common total factor."""

    index = _finite(regional_total_index, 100.0)
    raw_factor = min(
        REGIONAL_TOTAL_NUMERIC_SAFETY_CAP,
        max(REGIONAL_TOTAL_FACTOR_FLOOR, index / 100.0),
    )
    if raw_factor <= REGIONAL_TOTAL_LINEAR_CEILING:
        return raw_factor

    excess_ratio = (
        raw_factor - REGIONAL_TOTAL_LINEAR_CEILING
    ) / REGIONAL_TOTAL_SOFT_SPAN
    return REGIONAL_TOTAL_LINEAR_CEILING + REGIONAL_TOTAL_SOFT_SPAN * (
        (1.0 - REGIONAL_TOTAL_LINEAR_TAIL_WEIGHT) * math.tanh(excess_ratio)
        + REGIONAL_TOTAL_LINEAR_TAIL_WEIGHT * excess_ratio
    )


def bounded_long_term_factor(
    year_index: float,
    annual_bias_pct: float,
    max_bias_pct: float,
) -> float:
    """Return a bounded city-relative long-run factor.

    ``max_bias_pct`` is interpreted as a symmetric absolute safety magnitude so
    the helper remains well-defined for counterfactual negative city biases.
    Existing city configurations use positive annual biases.
    """

    years = max(0.0, _finite(year_index, 0.0))
    annual = _finite(annual_bias_pct, 0.0)
    limit = abs(_finite(max_bias_pct, 0.0))
    effective_bias = _clamp(years * annual, -limit, limit)
    raw_factor = max(0.05, 1.0 + effective_bias / 100.0)
    # The configured bias was calibrated while the old component indices also
    # carried aggregate growth.  Preserve its direction and ordering as a
    # city-relative modifier, but apply an explicit common elasticity instead
    # of silently using the old full multiplier in the separated total path.
    return raw_factor ** CITY_LONG_TERM_BIAS_ELASTICITY


def city_total_potential(
    *,
    baseline_million: float,
    regional_total_index: float,
    long_term_factor: float,
    seed_relative_factor: float,
) -> float:
    """Calculate city total potential with one and only one regional factor."""

    baseline = max(0.0, _finite(baseline_million, 0.0))
    regional = regional_total_factor(regional_total_index)
    structural = _clamp(_finite(long_term_factor, 1.0), 0.05, 5.0)
    seed = _clamp(_finite(seed_relative_factor, 1.0), 0.05, 5.0)
    result = baseline * regional * structural * seed
    if not math.isfinite(result):
        # All factors are bounded, so only a pathological baseline can reach
        # this branch.  Fail safely rather than exporting NaN/Infinity.
        return 0.0
    return max(0.0, result)


def component_boundary_diagnostic(
    component: str,
    raw_index: float,
) -> ComponentBoundaryDiagnostic:
    """Apply the component's real final safety boundary and expose its state."""

    lower, upper = CITY_INDEX_BOUNDARIES[component]
    raw = _finite(raw_index, 100.0)
    if raw < lower:
        return ComponentBoundaryDiagnostic(raw, lower, "floor", 1, 0)
    if raw > upper:
        return ComponentBoundaryDiagnostic(raw, upper, "cap", 0, 1)
    return ComponentBoundaryDiagnostic(raw, raw, "none", 0, 0)


def component_relative_diagnostics(
    *,
    regional_total_index: float,
    regional_component_indices: Mapping[str, float],
    city_response_elasticities: Mapping[str, float],
) -> dict[str, ComponentBoundaryDiagnostic]:
    """Map regional *relative* component signals into bounded city scores.

    Dividing each component index by the same regional total removes common
    scaling.  The city share-bias parameters act as response elasticities: at a
    neutral relative signal (1.0), every score remains exactly 100 regardless of
    the elasticity, so configured base shares stay the city structural anchor.
    """

    total = max(_RELATIVE_SIGNAL_FLOOR, _finite(regional_total_index, 100.0))
    diagnostics: dict[str, ComponentBoundaryDiagnostic] = {}
    for component in COMPONENTS:
        component_index = max(
            _RELATIVE_SIGNAL_FLOOR,
            _finite(regional_component_indices.get(component, total), total),
        )
        relative = _clamp(
            component_index / total,
            _RELATIVE_SIGNAL_FLOOR,
            _RELATIVE_SIGNAL_CAP,
        )
        elasticity = _clamp(
            _finite(city_response_elasticities.get(component, 1.0), 1.0),
            0.25,
            2.0,
        )
        # Log-space calculation is stable for extreme positive counterfactuals.
        raw_index = 100.0 * math.exp(elasticity * math.log(relative))
        diagnostics[component] = component_boundary_diagnostic(component, raw_index)
    return diagnostics


def normalized_component_shares(
    *,
    base_shares_pct: Mapping[str, float],
    diagnostics: Mapping[str, ComponentBoundaryDiagnostic],
) -> dict[str, float]:
    """Normalize five positive relative scores into shares summing to 100%."""

    weighted = {
        component: max(0.0, _finite(base_shares_pct.get(component, 0.0), 0.0))
        * max(0.0, diagnostics[component].final_index)
        for component in COMPONENTS
    }
    denominator = sum(weighted.values())
    if denominator <= 0.0 or not math.isfinite(denominator):
        fallback = {
            component: max(0.0, _finite(base_shares_pct.get(component, 0.0), 0.0))
            for component in COMPONENTS
        }
        denominator = sum(fallback.values())
        if denominator <= 0.0:
            return {component: 100.0 / len(COMPONENTS) for component in COMPONENTS}
        return {
            component: fallback[component] / denominator * 100.0
            for component in COMPONENTS
        }
    return {
        component: weighted[component] / denominator * 100.0
        for component in COMPONENTS
    }


def component_passenger_volumes(
    city_total_million: float,
    shares_pct: Mapping[str, float],
) -> dict[str, float]:
    """Allocate the city total exactly across the normalized component shares."""

    total = max(0.0, _finite(city_total_million, 0.0))
    passengers = {
        component: total * max(0.0, _finite(shares_pct.get(component, 0.0), 0.0)) / 100.0
        for component in COMPONENTS
    }
    # Give the final component the tiny floating residual so the unrounded layer
    # identity is exact without changing any economically meaningful share.
    residual = total - sum(passengers.values())
    passengers[COMPONENTS[-1]] += residual
    return passengers


def advance_boundary_streak(
    previous_streak: int,
    boundary_state: str,
) -> int:
    """Advance a per-city/Seed/component consecutive boundary counter."""

    return max(0, int(previous_streak)) + 1 if boundary_state in {"floor", "cap"} else 0
