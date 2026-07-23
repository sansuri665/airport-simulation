"""Pure helpers for the city-airline long-run supply equilibrium.

The annual city layer owns the state machine, shocks and hard safety bounds.  This
module isolates only the deterministic equilibrium channels so they can be
proved independently from file IO, RNG and the phase machine.
"""

from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class AirlineSupplyEquilibriumChannels:
    """Named channels used before phase impulses and annual change limits."""

    long_run_equilibrium_index: float
    adjustment_reference_index: float
    equilibrium_gap_index: float
    captured_gap_index: float
    captured_target_index: float
    regional_planning_signal_index: float
    is_initial_state: bool


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def equilibrium_channels(
    *,
    potential_anchor_index: float,
    regional_trend_index: float,
    previous_supply_index: float | None,
    previous_regional_trend_index: float | None = None,
    demand_pull_capture: float,
    macro_adjustment_index: float,
    constraint_drag_index: float,
    downward_gap_limit_index: float = 28.0,
    upward_gap_limit_index: float = 155.0,
    regional_signal_limit_index: float = 30.0,
) -> AirlineSupplyEquilibriumChannels:
    """Separate equilibrium level, gap capture and regional planning signal.

    ``demand_pull_capture`` controls how much of the *current gap to the
    equilibrium* is represented in this year's planning target.  It therefore
    changes convergence speed, not the fixed point.  The initial row retains the
    historical regional-trend reference so a configured starting state is not
    rewritten by the G4 transition rule.
    """

    values = (
        potential_anchor_index,
        regional_trend_index,
        demand_pull_capture,
        macro_adjustment_index,
        constraint_drag_index,
        downward_gap_limit_index,
        upward_gap_limit_index,
        regional_signal_limit_index,
    )
    if previous_supply_index is not None:
        values += (previous_supply_index,)
    if previous_regional_trend_index is not None:
        values += (previous_regional_trend_index,)
    if any(not math.isfinite(value) for value in values):
        raise ValueError("airline supply equilibrium channels require finite inputs")
    if demand_pull_capture <= 0.0:
        raise ValueError("demand_pull_capture must be positive")
    if downward_gap_limit_index < 0.0 or upward_gap_limit_index < 0.0:
        raise ValueError("gap limits must be non-negative")

    long_run_equilibrium = (
        potential_anchor_index + macro_adjustment_index - constraint_drag_index
    )
    is_initial = previous_supply_index is None
    reference = regional_trend_index if is_initial else float(previous_supply_index)

    if is_initial:
        # Preserve the old initial-state decomposition exactly: the regional
        # trend is the configured starting reference, while macro and constraint
        # channels are applied outside demand-gap capture.
        raw_gap = potential_anchor_index - reference
        captured_gap = _clamp(
            raw_gap * demand_pull_capture,
            -downward_gap_limit_index,
            upward_gap_limit_index,
        )
        captured_target = (
            reference
            + captured_gap
            + macro_adjustment_index
            - constraint_drag_index
        )
        regional_signal = 0.0
    else:
        # From year 1 onward the gap is always measured against the explicit
        # long-run equilibrium.  Any capture below one slows convergence but no
        # longer creates a permanent fraction of the trend/potential gap.
        raw_gap = long_run_equilibrium - reference
        captured_gap = _clamp(
            raw_gap * demand_pull_capture,
            -downward_gap_limit_index,
            upward_gap_limit_index,
        )
        captured_target = reference + captured_gap
        # Regional capacity is a short-horizon planning input.  Consume its
        # year-on-year change rather than its level relative to city supply, so
        # it can affect phase timing without becoming a second fixed point.
        regional_signal = (
            0.0
            if previous_regional_trend_index is None
            else _clamp(
                regional_trend_index - previous_regional_trend_index,
                -regional_signal_limit_index,
                regional_signal_limit_index,
            )
        )

    return AirlineSupplyEquilibriumChannels(
        long_run_equilibrium_index=long_run_equilibrium,
        adjustment_reference_index=reference,
        equilibrium_gap_index=raw_gap,
        captured_gap_index=captured_gap,
        captured_target_index=captured_target,
        regional_planning_signal_index=regional_signal,
        is_initial_state=is_initial,
    )
