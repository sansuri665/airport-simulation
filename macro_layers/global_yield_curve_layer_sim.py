from __future__ import annotations

from importlib import import_module

_SIBLING_PREFIX = f"{__package__}." if __package__ else ""
simulation_io = import_module(f"{_SIBLING_PREFIX}simulation_io")
simulation_utils = import_module(f"{_SIBLING_PREFIX}simulation_utils")

write_csv = simulation_io.write_csv
write_json = simulation_io.write_json
clamp = simulation_utils.clamp
resolve_seeds = simulation_utils.resolve_seeds
round_record = simulation_utils.round_record

import argparse
import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean
from typing import Any

global_gdp_layer = import_module(f"{_SIBLING_PREFIX}global_gdp_annual_sim")
inflation_layer = import_module(f"{_SIBLING_PREFIX}global_inflation_annual_sim")
policy_rate_layer = import_module(f"{_SIBLING_PREFIX}global_policy_rate_layer_sim")

GDPParams = global_gdp_layer.GDPParams
simulate_global_gdp = global_gdp_layer.simulate_global_gdp
INFLATION_PARAM_VERSION = inflation_layer.INFLATION_PARAM_VERSION
InflationParams = inflation_layer.InflationParams
as_float = inflation_layer.as_float
simulate_inflation_for_gdp_path = inflation_layer.simulate_inflation_for_gdp_path
COMBINED_POLICY_FIELDS = policy_rate_layer.COMBINED_POLICY_FIELDS
POLICY_PARAM_VERSION = policy_rate_layer.POLICY_PARAM_VERSION
PolicyRateParams = policy_rate_layer.PolicyRateParams
simulate_policy_for_macro_path = policy_rate_layer.simulate_policy_for_macro_path


YIELD_CURVE_PARAM_VERSION = "global-yield-curve-layer-v0.3"
YIELD_CURVE_INTERFACE_VERSION = "yield-curve-feedback-interface-v0.2"
YIELD_CURVE_BOUNDARY_VERSION = "yield-curve-boundaries-v1"


YIELD_CURVE_FIELDS = [
    "yield_curve_param_version",
    "yield_curve_interface_version",
    "yield_curve_boundary_version",
    "global_short_rate_pct",
    "global_2y_yield_pct",
    "global_10y_yield_pct",
    "global_real_10y_yield_pct",
    "term_spread_10y_2y_pct",
    "term_premium_pct",
    "expected_short_rate_10y_pct",
    "expected_shadow_short_rate_10y_pct",
    "unclamped_short_rate_target_pct",
    "unclamped_expected_short_rate_10y_target_pct",
    "unclamped_expected_shadow_short_rate_10y_target_pct",
    "unclamped_2y_yield_target_pct",
    "unclamped_10y_yield_target_pct",
    "unclamped_term_premium_target_pct",
    "short_rate_floor_applied",
    "short_rate_cap_applied",
    "expected_short_rate_floor_applied",
    "expected_short_rate_cap_applied",
    "shadow_short_rate_floor_applied",
    "shadow_short_rate_cap_applied",
    "yield_2y_floor_applied",
    "yield_2y_cap_applied",
    "yield_10y_floor_applied",
    "yield_10y_cap_applied",
    "term_premium_floor_applied",
    "term_premium_cap_applied",
    "short_rate_consecutive_boundary_years",
    "expected_short_rate_consecutive_boundary_years",
    "shadow_short_rate_consecutive_boundary_years",
    "yield_2y_consecutive_boundary_years",
    "yield_10y_consecutive_boundary_years",
    "term_premium_consecutive_boundary_years",
    "bond_price_index",
    "bond_total_return_pct",
    "duration_pressure_index",
    "curve_inversion_pressure",
    "yield_curve_regime",
    "yield_curve_to_dollar_impulse",
    "yield_curve_to_equity_valuation_impulse",
    "yield_curve_to_credit_impulse",
    "yield_curve_to_gdp_drag_placeholder",
]


COMBINED_YIELD_CURVE_FIELDS = COMBINED_POLICY_FIELDS + YIELD_CURVE_FIELDS


@dataclass(frozen=True)
class YieldCurveParams:
    initial_short_rate_pct: float = 3.25
    initial_2y_yield_pct: float = 3.40
    initial_10y_yield_pct: float = 4.05
    initial_term_premium_pct: float = 0.65
    initial_expected_short_rate_10y_pct: float = 3.35
    initial_expected_shadow_short_rate_10y_pct: float = 3.35
    short_rate_policy_speed: float = 0.78
    expected_short_rate_speed: float = 0.24
    two_year_speed: float = 0.56
    ten_year_speed: float = 0.34
    term_premium_speed: float = 0.30
    base_term_premium_pct: float = 0.58
    inflation_term_premium_beta: float = 0.17
    inflation_vol_term_premium_beta: float = 0.10
    stress_term_premium_beta: float = 0.018
    qe_term_premium_beta: float = 0.014
    balance_sheet_term_premium_beta: float = 0.012
    policy_stance_term_premium_beta: float = 0.08
    inflation_expectation_long_rate_beta: float = 0.22
    inflation_long_rate_impulse_beta: float = 0.35
    potential_growth_long_rate_beta: float = 0.08
    crisis_flight_to_quality_beta: float = 0.42
    market_noise_scale: float = 0.10
    two_year_noise_scale: float = 0.07
    ten_year_noise_scale: float = 0.09
    bond_duration_years: float = 7.4
    min_yield_pct: float = -0.35
    max_yield_pct: float = 10.50
    min_observable_expected_short_rate_pct: float = 0.05
    max_observable_expected_short_rate_pct: float = 10.50
    min_shadow_expected_short_rate_pct: float = -0.75
    max_shadow_expected_short_rate_pct: float = 10.50
    min_term_premium_pct: float = -0.45
    max_term_premium_pct: float = 2.80
    shadow_expected_short_rate_speed: float = 0.30
    shadow_qe_beta: float = 0.014
    shadow_balance_sheet_beta: float = 0.004
    two_year_shadow_weight: float = 0.18
    ten_year_shadow_weight: float = 0.32
    dollar_curve_inversion_beta: float = 0.30
    dollar_curve_term_premium_change_beta: float = 0.18
    dollar_curve_ten_year_change_beta: float = 0.10
    yield_seed_offset: int = 7_200_071


@dataclass
class YieldCurveState:
    short_rate_pct: float = 3.25
    two_year_yield_pct: float = 3.40
    ten_year_yield_pct: float = 4.05
    term_premium_pct: float = 0.65
    expected_short_rate_10y_pct: float = 3.35
    expected_shadow_short_rate_10y_pct: float = 3.35
    bond_price_index: float = 100.0
    previous_ten_year_yield_pct: float = 4.05
    previous_term_spread_pct: float = 0.65


@dataclass
class YieldCurveRecord:
    yield_curve_param_version: str
    yield_curve_interface_version: str
    yield_curve_boundary_version: str
    global_short_rate_pct: float
    global_2y_yield_pct: float
    global_10y_yield_pct: float
    global_real_10y_yield_pct: float
    term_spread_10y_2y_pct: float
    term_premium_pct: float
    expected_short_rate_10y_pct: float
    expected_shadow_short_rate_10y_pct: float
    unclamped_short_rate_target_pct: float
    unclamped_expected_short_rate_10y_target_pct: float
    unclamped_expected_shadow_short_rate_10y_target_pct: float
    unclamped_2y_yield_target_pct: float
    unclamped_10y_yield_target_pct: float
    unclamped_term_premium_target_pct: float
    short_rate_floor_applied: bool
    short_rate_cap_applied: bool
    expected_short_rate_floor_applied: bool
    expected_short_rate_cap_applied: bool
    shadow_short_rate_floor_applied: bool
    shadow_short_rate_cap_applied: bool
    yield_2y_floor_applied: bool
    yield_2y_cap_applied: bool
    yield_10y_floor_applied: bool
    yield_10y_cap_applied: bool
    term_premium_floor_applied: bool
    term_premium_cap_applied: bool
    short_rate_consecutive_boundary_years: int
    expected_short_rate_consecutive_boundary_years: int
    shadow_short_rate_consecutive_boundary_years: int
    yield_2y_consecutive_boundary_years: int
    yield_10y_consecutive_boundary_years: int
    term_premium_consecutive_boundary_years: int
    bond_price_index: float
    bond_total_return_pct: float
    duration_pressure_index: float
    curve_inversion_pressure: float
    yield_curve_regime: str
    yield_curve_to_dollar_impulse: float
    yield_curve_to_equity_valuation_impulse: float
    yield_curve_to_credit_impulse: float
    yield_curve_to_gdp_drag_placeholder: float



def smooth(old: float, target: float, speed: float) -> float:
    return old * (1.0 - speed) + target * speed


def boundary_flags(value: float, floor: float, cap: float) -> tuple[bool, bool]:
    return value < floor, value > cap


def advance_boundary_run(previous: int, floor_applied: bool, cap_applied: bool) -> int:
    return previous + 1 if floor_applied or cap_applied else 0


def compound_index_with_soft_drag(
    previous: float,
    total_return_pct: float,
    *,
    floor: float,
    soft_start: float,
    softness: float = 0.65,
) -> float:
    adjusted_return = total_return_pct
    if total_return_pct > 0.0 and previous > soft_start:
        adjusted_return *= (soft_start / previous) ** softness
    return max(floor, previous * (1.0 + adjusted_return / 100.0))


def classify_yield_curve_regime(
    *,
    year_index: int,
    term_spread: float,
    previous_term_spread: float,
    ten_year_change: float,
    term_premium_change: float,
    policy_change: float,
    policy_stance: float,
    qe_liquidity_index: float,
    crisis_intensity: float,
    stress: float,
    headline_inflation: float,
) -> str:
    spread_change = term_spread - previous_term_spread
    if year_index == 0:
        return "initial"
    if term_spread < -0.35 and policy_stance > 0.25:
        return "inverted_tightening"
    if crisis_intensity >= 0.60 and ten_year_change < -0.20:
        return "recession_bull_flattening"
    if qe_liquidity_index >= 45.0 and term_spread >= -0.20 and ten_year_change <= 0.15:
        return "qe_suppressed_curve"
    if ten_year_change > 0.35 and term_premium_change > 0.10 and headline_inflation >= 3.2:
        return "bear_steepening"
    if spread_change > 0.35 and policy_change <= 0.05 and ten_year_change <= 0.20:
        return "bull_steepening"
    if ten_year_change > 0.30 and term_spread < previous_term_spread - 0.15:
        return "bear_flattening"
    if abs(term_spread) <= 0.25:
        return "flat_curve"
    if term_spread < 0.0:
        return "mild_inversion"
    if stress >= 55.0 and ten_year_change > 0.15:
        return "risk_premium_steepening"
    return "normal_upward_curve"


def simulate_yield_curve_for_policy_path(
    records: list[dict[str, Any]],
    params: YieldCurveParams,
) -> list[dict[str, Any]]:
    if not records:
        return []

    seed = int(records[0].get("seed", 0))
    rng = random.Random(seed + params.yield_seed_offset)
    state = YieldCurveState(
        short_rate_pct=params.initial_short_rate_pct,
        two_year_yield_pct=params.initial_2y_yield_pct,
        ten_year_yield_pct=params.initial_10y_yield_pct,
        previous_ten_year_yield_pct=params.initial_10y_yield_pct,
        term_premium_pct=params.initial_term_premium_pct,
        expected_short_rate_10y_pct=params.initial_expected_short_rate_10y_pct,
        expected_shadow_short_rate_10y_pct=params.initial_expected_shadow_short_rate_10y_pct,
        previous_term_spread_pct=params.initial_10y_yield_pct - params.initial_2y_yield_pct,
    )
    boundary_runs = {
        "short_rate": 0,
        "expected_short_rate": 0,
        "shadow_short_rate": 0,
        "yield_2y": 0,
        "yield_10y": 0,
        "term_premium": 0,
    }
    combined: list[dict[str, Any]] = []

    for row in records:
        year_index = int(row["year_index"])
        policy_rate = as_float(row, "global_policy_rate_pct", 3.25)
        policy_change = as_float(row, "policy_rate_change_pct")
        neutral_policy = as_float(row, "neutral_policy_rate_pct", 3.25)
        real_policy = as_float(row, "real_policy_rate_pct")
        policy_stance = as_float(row, "policy_stance_index")
        headline = as_float(row, "headline_inflation_pct", 2.35)
        expectation = as_float(row, "inflation_expectation_pct", 2.25)
        output_gap = as_float(row, "output_gap_pct")
        potential_growth = as_float(row, "potential_growth_pct", 2.0)
        stress = as_float(row, "financial_stress_index")
        crisis_intensity = as_float(row, "crisis_intensity")
        qe = as_float(row, "qe_liquidity_index")
        balance_sheet_impulse = as_float(row, "balance_sheet_impulse")
        hike_pressure = as_float(row, "rate_hike_pressure")
        cut_pressure = as_float(row, "rate_cut_pressure")
        inflation_long_impulse = as_float(row, "inflation_to_long_rate_impulse")

        short_rate_target = policy_rate + rng.gauss(0.0, params.market_noise_scale * 0.20)
        unclamped_short_rate_next = smooth(
            state.short_rate_pct, short_rate_target, params.short_rate_policy_speed
        )
        short_rate_floor_applied, short_rate_cap_applied = boundary_flags(
            unclamped_short_rate_next, params.min_yield_pct, params.max_yield_pct
        )
        short_rate = clamp(
            unclamped_short_rate_next, params.min_yield_pct, params.max_yield_pct
        )

        expected_short_target = (
            0.50 * neutral_policy
            + 0.35 * policy_rate
            + 0.15 * state.expected_short_rate_10y_pct
            + 0.012 * (hike_pressure - cut_pressure)
            + 0.15 * output_gap
            - 0.40 * crisis_intensity
        )
        expected_short_rate_floor_applied, expected_short_rate_cap_applied = boundary_flags(
            expected_short_target,
            params.min_observable_expected_short_rate_pct,
            params.max_observable_expected_short_rate_pct,
        )
        bounded_expected_short_target = clamp(
            expected_short_target,
            params.min_observable_expected_short_rate_pct,
            params.max_observable_expected_short_rate_pct,
        )
        expected_short_rate_10y = smooth(
            state.expected_short_rate_10y_pct,
            bounded_expected_short_target,
            params.expected_short_rate_speed,
        )

        expected_shadow_short_target = (
            expected_short_rate_10y
            - params.shadow_qe_beta * qe
            - params.shadow_balance_sheet_beta * max(0.0, balance_sheet_impulse)
        )
        shadow_short_rate_floor_applied, shadow_short_rate_cap_applied = boundary_flags(
            expected_shadow_short_target,
            params.min_shadow_expected_short_rate_pct,
            params.max_shadow_expected_short_rate_pct,
        )
        bounded_shadow_short_target = clamp(
            expected_shadow_short_target,
            params.min_shadow_expected_short_rate_pct,
            params.max_shadow_expected_short_rate_pct,
        )
        expected_shadow_short_rate_10y = smooth(
            state.expected_shadow_short_rate_10y_pct,
            bounded_shadow_short_target,
            params.shadow_expected_short_rate_speed,
        )

        term_premium_target = (
            params.base_term_premium_pct
            + params.inflation_term_premium_beta * max(0.0, headline - 2.65)
            + params.inflation_vol_term_premium_beta * abs(inflation_long_impulse)
            + params.stress_term_premium_beta * max(0.0, stress - 32.0)
            + params.balance_sheet_term_premium_beta * max(0.0, -balance_sheet_impulse)
            + params.policy_stance_term_premium_beta * max(0.0, policy_stance)
            - params.qe_term_premium_beta * qe
            - 0.010 * max(0.0, balance_sheet_impulse)
            + rng.gauss(0.0, params.market_noise_scale)
        )
        term_premium_floor_applied, term_premium_cap_applied = boundary_flags(
            term_premium_target, params.min_term_premium_pct, params.max_term_premium_pct
        )
        bounded_term_premium_target = clamp(
            term_premium_target, params.min_term_premium_pct, params.max_term_premium_pct
        )
        term_premium = smooth(
            state.term_premium_pct, bounded_term_premium_target, params.term_premium_speed
        )

        two_year_target = (
            0.62 * short_rate
            + 0.30 * policy_rate
            + 0.08 * expected_short_rate_10y
            + 0.20 * term_premium
            + 0.18 * policy_change
            + 0.006 * (hike_pressure - cut_pressure)
            + params.two_year_shadow_weight
            * (expected_shadow_short_rate_10y - expected_short_rate_10y)
            + rng.gauss(0.0, params.two_year_noise_scale)
        )
        unclamped_two_year_next = smooth(
            state.two_year_yield_pct, two_year_target, params.two_year_speed
        )
        yield_2y_floor_applied, yield_2y_cap_applied = boundary_flags(
            unclamped_two_year_next, params.min_yield_pct, params.max_yield_pct
        )
        two_year_yield = clamp(
            unclamped_two_year_next, params.min_yield_pct, params.max_yield_pct
        )

        ten_year_target = (
            expected_short_rate_10y
            + term_premium
            + params.inflation_expectation_long_rate_beta * (expectation - 2.25)
            + params.inflation_long_rate_impulse_beta * inflation_long_impulse
            + params.potential_growth_long_rate_beta * (potential_growth - 2.0)
            - params.crisis_flight_to_quality_beta * crisis_intensity
            + params.ten_year_shadow_weight
            * (expected_shadow_short_rate_10y - expected_short_rate_10y)
            + rng.gauss(0.0, params.ten_year_noise_scale)
        )
        unclamped_ten_year_next = smooth(
            state.ten_year_yield_pct, ten_year_target, params.ten_year_speed
        )
        yield_10y_floor_applied, yield_10y_cap_applied = boundary_flags(
            unclamped_ten_year_next, params.min_yield_pct, params.max_yield_pct
        )
        ten_year_yield = clamp(
            unclamped_ten_year_next, params.min_yield_pct, params.max_yield_pct
        )

        boundary_runs["short_rate"] = advance_boundary_run(
            boundary_runs["short_rate"], short_rate_floor_applied, short_rate_cap_applied
        )
        boundary_runs["expected_short_rate"] = advance_boundary_run(
            boundary_runs["expected_short_rate"],
            expected_short_rate_floor_applied,
            expected_short_rate_cap_applied,
        )
        boundary_runs["shadow_short_rate"] = advance_boundary_run(
            boundary_runs["shadow_short_rate"],
            shadow_short_rate_floor_applied,
            shadow_short_rate_cap_applied,
        )
        boundary_runs["yield_2y"] = advance_boundary_run(
            boundary_runs["yield_2y"], yield_2y_floor_applied, yield_2y_cap_applied
        )
        boundary_runs["yield_10y"] = advance_boundary_run(
            boundary_runs["yield_10y"], yield_10y_floor_applied, yield_10y_cap_applied
        )
        boundary_runs["term_premium"] = advance_boundary_run(
            boundary_runs["term_premium"],
            term_premium_floor_applied,
            term_premium_cap_applied,
        )

        ten_year_change = ten_year_yield - state.ten_year_yield_pct
        term_spread = ten_year_yield - two_year_yield
        term_premium_change = term_premium - state.term_premium_pct
        real_10y = ten_year_yield - expectation
        duration_pressure = clamp(params.bond_duration_years * ten_year_change, -15.0, 15.0)

        if year_index == 0:
            bond_total_return = 0.0
        else:
            bond_total_return = clamp(
                state.previous_ten_year_yield_pct - params.bond_duration_years * ten_year_change,
                -28.0,
                24.0,
            )
        bond_price_index = compound_index_with_soft_drag(
            state.bond_price_index,
            bond_total_return,
            floor=25.0,
            soft_start=240.0,
        )

        inversion_pressure = clamp(
            32.0 * max(0.0, -term_spread)
            + 9.0 * max(0.0, policy_stance)
            + 6.0 * max(0.0, real_policy - 1.0)
            + 9.0 * crisis_intensity,
            0.0,
            100.0,
        )
        regime = classify_yield_curve_regime(
            year_index=year_index,
            term_spread=term_spread,
            previous_term_spread=state.previous_term_spread_pct,
            ten_year_change=ten_year_change,
            term_premium_change=term_premium_change,
            policy_change=policy_change,
            policy_stance=policy_stance,
            qe_liquidity_index=qe,
            crisis_intensity=crisis_intensity,
            stress=stress,
            headline_inflation=headline,
        )

        # Curve-only signal: real rates and policy stance are consumed directly by
        # the dollar layer, so repeating them here would double count the same stance.
        dollar_impulse = clamp(
            params.dollar_curve_inversion_beta * max(0.0, -term_spread)
            + params.dollar_curve_term_premium_change_beta * term_premium_change
            + params.dollar_curve_ten_year_change_beta * ten_year_change,
            -2.0,
            2.0,
        )
        equity_valuation_impulse = clamp(
            -0.30 * real_10y
            - 0.70 * max(0.0, ten_year_change)
            - 0.18 * max(0.0, -term_spread)
            + 0.014 * qe,
            -2.0,
            2.0,
        )
        credit_impulse = clamp(
            0.35 * max(0.0, -term_spread)
            + 0.48 * max(0.0, ten_year_change)
            + 0.20 * max(0.0, term_premium - 0.75)
            + 0.12 * max(0.0, policy_stance)
            - 0.012 * qe,
            -2.0,
            2.0,
        )
        gdp_drag = clamp(
            -0.16 * max(0.0, real_10y - 1.0)
            - 0.12 * max(0.0, -term_spread)
            - 0.12 * max(0.0, credit_impulse)
            + 0.006 * qe,
            -1.5,
            0.45,
        )

        record = YieldCurveRecord(
            yield_curve_param_version=YIELD_CURVE_PARAM_VERSION,
            yield_curve_interface_version=YIELD_CURVE_INTERFACE_VERSION,
            yield_curve_boundary_version=YIELD_CURVE_BOUNDARY_VERSION,
            global_short_rate_pct=short_rate,
            global_2y_yield_pct=two_year_yield,
            global_10y_yield_pct=ten_year_yield,
            global_real_10y_yield_pct=real_10y,
            term_spread_10y_2y_pct=term_spread,
            term_premium_pct=term_premium,
            expected_short_rate_10y_pct=expected_short_rate_10y,
            expected_shadow_short_rate_10y_pct=expected_shadow_short_rate_10y,
            unclamped_short_rate_target_pct=short_rate_target,
            unclamped_expected_short_rate_10y_target_pct=expected_short_target,
            unclamped_expected_shadow_short_rate_10y_target_pct=expected_shadow_short_target,
            unclamped_2y_yield_target_pct=two_year_target,
            unclamped_10y_yield_target_pct=ten_year_target,
            unclamped_term_premium_target_pct=term_premium_target,
            short_rate_floor_applied=short_rate_floor_applied,
            short_rate_cap_applied=short_rate_cap_applied,
            expected_short_rate_floor_applied=expected_short_rate_floor_applied,
            expected_short_rate_cap_applied=expected_short_rate_cap_applied,
            shadow_short_rate_floor_applied=shadow_short_rate_floor_applied,
            shadow_short_rate_cap_applied=shadow_short_rate_cap_applied,
            yield_2y_floor_applied=yield_2y_floor_applied,
            yield_2y_cap_applied=yield_2y_cap_applied,
            yield_10y_floor_applied=yield_10y_floor_applied,
            yield_10y_cap_applied=yield_10y_cap_applied,
            term_premium_floor_applied=term_premium_floor_applied,
            term_premium_cap_applied=term_premium_cap_applied,
            short_rate_consecutive_boundary_years=boundary_runs["short_rate"],
            expected_short_rate_consecutive_boundary_years=boundary_runs["expected_short_rate"],
            shadow_short_rate_consecutive_boundary_years=boundary_runs["shadow_short_rate"],
            yield_2y_consecutive_boundary_years=boundary_runs["yield_2y"],
            yield_10y_consecutive_boundary_years=boundary_runs["yield_10y"],
            term_premium_consecutive_boundary_years=boundary_runs["term_premium"],
            bond_price_index=bond_price_index,
            bond_total_return_pct=bond_total_return,
            duration_pressure_index=duration_pressure,
            curve_inversion_pressure=inversion_pressure,
            yield_curve_regime=regime,
            yield_curve_to_dollar_impulse=dollar_impulse,
            yield_curve_to_equity_valuation_impulse=equity_valuation_impulse,
            yield_curve_to_credit_impulse=credit_impulse,
            yield_curve_to_gdp_drag_placeholder=gdp_drag,
        )
        combined.append(round_record({**row, **asdict(record)}))

        state.short_rate_pct = short_rate
        state.two_year_yield_pct = two_year_yield
        state.previous_ten_year_yield_pct = state.ten_year_yield_pct
        state.ten_year_yield_pct = ten_year_yield
        state.term_premium_pct = term_premium
        state.expected_short_rate_10y_pct = expected_short_rate_10y
        state.expected_shadow_short_rate_10y_pct = expected_shadow_short_rate_10y
        state.bond_price_index = bond_price_index
        state.previous_term_spread_pct = term_spread

    return combined


def summarize_seed(records: list[dict[str, Any]]) -> dict[str, Any]:
    data = records[1:] if len(records) > 1 else records
    ten_year_values = [as_float(row, "global_10y_yield_pct") for row in data]
    spread_values = [as_float(row, "term_spread_10y_2y_pct") for row in data]
    max_10y_row = max(data, key=lambda row: as_float(row, "global_10y_yield_pct")) if data else records[-1]
    min_10y_row = min(data, key=lambda row: as_float(row, "global_10y_yield_pct")) if data else records[-1]
    inversion_years = sum(1 for row in data if as_float(row, "term_spread_10y_2y_pct") < 0.0)
    bear_steepening_years = sum(1 for row in data if str(row["yield_curve_regime"]) == "bear_steepening")
    qe_suppressed_years = sum(1 for row in data if str(row["yield_curve_regime"]) == "qe_suppressed_curve")
    final = records[-1]
    return {
        "seed": int(final["seed"]),
        "start_year": int(records[0]["year"]),
        "end_year": int(final["year"]),
        "average_10y_yield_pct": round(mean(ten_year_values), 3) if ten_year_values else 0.0,
        "average_term_spread_pct": round(mean(spread_values), 3) if spread_values else 0.0,
        "max_10y_yield_pct": as_float(max_10y_row, "global_10y_yield_pct"),
        "max_10y_yield_year": int(max_10y_row["year"]),
        "min_10y_yield_pct": as_float(min_10y_row, "global_10y_yield_pct"),
        "min_10y_yield_year": int(min_10y_row["year"]),
        "inversion_years": inversion_years,
        "bear_steepening_years": bear_steepening_years,
        "qe_suppressed_years": qe_suppressed_years,
        "final_2y_yield_pct": as_float(final, "global_2y_yield_pct"),
        "final_10y_yield_pct": as_float(final, "global_10y_yield_pct"),
        "final_term_spread_pct": as_float(final, "term_spread_10y_2y_pct"),
        "final_bond_price_index": as_float(final, "bond_price_index"),
        "final_yield_curve_regime": str(final["yield_curve_regime"]),
    }


def write_viewer_data_js(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(rows, ensure_ascii=False, separators=(",", ":"))
    path.write_text(f"window.GLOBAL_YIELD_CURVE_DATA = {payload};\n", encoding="utf-8")


def build_yield_curve_svg(records_by_seed: dict[int, list[dict[str, Any]]], path: Path) -> None:
    width = 1180
    height = 680
    left = 76
    right = 36
    top = 42
    bottom = 72
    plot_w = width - left - right
    plot_h = height - top - bottom
    all_records = [row for rows in records_by_seed.values() for row in rows]
    years = [int(row["year"]) for row in all_records]
    values = [as_float(row, "global_10y_yield_pct") for row in all_records]
    min_year, max_year = min(years), max(years)
    min_value = min(values) - 0.5
    max_value = max(6.0, max(values) + 0.5)

    def x_of(year: int) -> float:
        return left + (year - min_year) / max(1, max_year - min_year) * plot_w

    def y_of(value: float) -> float:
        return top + (max_value - value) / max(1e-9, max_value - min_value) * plot_h

    palette = ["#22d3ee", "#a78bfa", "#60a5fa", "#34d399", "#fb7185", "#f59e0b", "#f472b6", "#eab308"]
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#07090d"/>',
        f'<text x="{left}" y="27" font-family="Arial" font-size="20" fill="#f5f7fb">Global 10Y Yield Paths by Seed</text>',
        f'<text x="{left}" y="50" font-family="Arial" font-size="12" fill="#94a3b8">10Y yield after GDP, inflation, policy rate, QE, stress, and term-premium dynamics</text>',
    ]

    for i in range(7):
        y = top + i / 6 * plot_h
        value = max_value - i / 6 * (max_value - min_value)
        lines.append(f'<line x1="{left}" y1="{y:.2f}" x2="{left + plot_w}" y2="{y:.2f}" stroke="#1f2937"/>')
        lines.append(f'<text x="{left - 10}" y="{y + 4:.2f}" text-anchor="end" font-family="Arial" font-size="11" fill="#94a3b8">{value:.1f}%</text>')
    for i in range(6):
        x = left + i / 5 * plot_w
        year = round(min_year + i / 5 * (max_year - min_year))
        lines.append(f'<line x1="{x:.2f}" y1="{top}" x2="{x:.2f}" y2="{top + plot_h}" stroke="#172033"/>')
        lines.append(f'<text x="{x:.2f}" y="{top + plot_h + 24}" text-anchor="middle" font-family="Arial" font-size="11" fill="#94a3b8">{year}</text>')

    for idx, (seed, records) in enumerate(sorted(records_by_seed.items())):
        color = palette[idx % len(palette)]
        points = " ".join(
            f'{x_of(int(row["year"])):.2f},{y_of(as_float(row, "global_10y_yield_pct")):.2f}'
            for row in records
        )
        lines.append(f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round"/>')
        last = records[-1]
        lines.append(
            f'<text x="{x_of(int(last["year"])) + 6:.2f}" y="{y_of(as_float(last, "global_10y_yield_pct")) + 4:.2f}" '
            f'font-family="Arial" font-size="11" fill="{color}">seed {seed}</text>'
        )

    lines.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}" stroke="#64748b"/>')
    lines.append(f'<line x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}" stroke="#64748b"/>')
    lines.append(f'<text x="18" y="{top + plot_h / 2}" transform="rotate(-90 18 {top + plot_h / 2})" text-anchor="middle" font-family="Arial" font-size="12" fill="#94a3b8">10Y yield %</text>')
    lines.append("</svg>")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a combined global GDP + inflation + policy-rate + yield-curve annual simulation.",
    )
    parser.add_argument("--years", type=int, default=60, help="Number of simulated years after the initial year.")
    parser.add_argument("--start-year", type=int, default=2025, help="Calendar year for the initial observation.")
    parser.add_argument("--initial-gdp", type=float, default=110.0, help="Initial global GDP in trillion USD.")
    parser.add_argument("--volatility-scale", type=float, default=1.55, help="Scales GDP cycle amplitude and random shocks.")
    parser.add_argument("--seed", type=int, default=None, help="Run one seed only.")
    parser.add_argument("--seeds", type=int, nargs="*", default=None, help="Run an explicit list of seeds.")
    parser.add_argument("--seed-start", type=int, default=1, help="First seed when --seed/--seeds is omitted.")
    parser.add_argument("--seed-count", type=int, default=8, help="Number of seeds when --seed/--seeds is omitted.")
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parents[1] / "output" / "global_macro")
    parser.add_argument("--no-svg", action="store_true", help="Skip writing the SVG chart.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    seeds = resolve_seeds(args)
    if args.years < 1:
        raise SystemExit("--years must be at least 1")
    if args.volatility_scale <= 0:
        raise SystemExit("--volatility-scale must be positive")

    gdp_params = GDPParams(
        years=args.years,
        start_year=args.start_year,
        initial_gdp_trillion_usd=args.initial_gdp,
        volatility_scale=args.volatility_scale,
    )
    inflation_params = InflationParams()
    policy_params = PolicyRateParams()
    yield_curve_params = YieldCurveParams()

    records_by_seed: dict[int, list[dict[str, Any]]] = {}
    for seed in seeds:
        gdp_records = simulate_global_gdp(seed, gdp_params)
        inflation_records = simulate_inflation_for_gdp_path(seed, gdp_records, inflation_params)
        policy_records = simulate_policy_for_macro_path(inflation_records, policy_params)
        records_by_seed[seed] = simulate_yield_curve_for_policy_path(policy_records, yield_curve_params)

    all_records = [row for records in records_by_seed.values() for row in records]
    summaries = [summarize_seed(records) for records in records_by_seed.values()]

    args.output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = args.output_dir / "global_yield_curve_seed_sweep.csv"
    json_path = args.output_dir / "global_yield_curve_seed_sweep.json"
    viewer_data_path = args.output_dir / "global_yield_curve_viewer_data.js"
    svg_path = args.output_dir / "global_yield_curve_curves.svg"

    write_csv(csv_path, all_records, COMBINED_YIELD_CURVE_FIELDS)
    write_json(
        json_path,
        {
            "gdp_param_version": all_records[0]["param_version"] if all_records else "",
            "inflation_param_version": INFLATION_PARAM_VERSION,
            "policy_param_version": POLICY_PARAM_VERSION,
            "yield_curve_param_version": YIELD_CURVE_PARAM_VERSION,
            "yield_curve_interface_version": YIELD_CURVE_INTERFACE_VERSION,
            "gdp_params": asdict(gdp_params),
            "inflation_params": asdict(inflation_params),
            "policy_params": asdict(policy_params),
            "yield_curve_params": asdict(yield_curve_params),
            "seeds": seeds,
            "summary": summaries,
            "model_note": {
                "coupling": "Yield curve is downstream of GDP, inflation, and policy in this version. Short end follows policy; 2Y prices expected cuts/hikes; 10Y adds inflation expectations, term premium, QE, stress, and flight-to-quality effects.",
                "no_feedback_yet": "Yield-curve impulses to GDP, dollar, equity valuation, and credit are emitted as placeholders only; upstream paths are not recomputed in v0.1.",
                "future_connection": "The yield_curve_to_* fields are intended for later dollar, equity, credit, oil, and GDP feedback layers.",
            },
        },
    )
    write_viewer_data_js(viewer_data_path, all_records)
    if not args.no_svg:
        build_yield_curve_svg(records_by_seed, svg_path)

    print(f"Wrote {csv_path}")
    print(f"Wrote {json_path}")
    print(f"Wrote {viewer_data_path}")
    if not args.no_svg:
        print(f"Wrote {svg_path}")
    for summary in summaries:
        print(
            "seed={seed} avg_10y={average_10y_yield_pct:.2f}% "
            "avg_spread={average_term_spread_pct:.2f}% "
            "inversions={inversion_years} final_10y={final_10y_yield_pct:.2f}% "
            "final_curve={final_yield_curve_regime}".format(**summary)
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
