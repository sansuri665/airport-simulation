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
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean, pstdev
from typing import Any, Mapping

asset_price_layer = import_module(f"{_SIBLING_PREFIX}global_asset_price_layer_sim")
credit_spread_layer = import_module(f"{_SIBLING_PREFIX}global_credit_spread_layer_sim")
dollar_liquidity_layer = import_module(f"{_SIBLING_PREFIX}global_dollar_liquidity_layer_sim")
global_gdp_layer = import_module(f"{_SIBLING_PREFIX}global_gdp_annual_sim")
inflation_layer = import_module(f"{_SIBLING_PREFIX}global_inflation_annual_sim")
oil_commodity_layer = import_module(f"{_SIBLING_PREFIX}global_oil_commodity_layer_sim")
policy_rate_layer = import_module(f"{_SIBLING_PREFIX}global_policy_rate_layer_sim")
yield_curve_layer = import_module(f"{_SIBLING_PREFIX}global_yield_curve_layer_sim")

ASSET_PRICE_PARAM_VERSION = asset_price_layer.ASSET_PRICE_PARAM_VERSION
AssetPriceParams = asset_price_layer.AssetPriceParams
simulate_asset_prices_for_credit_path = asset_price_layer.simulate_asset_prices_for_credit_path
CREDIT_SPREAD_PARAM_VERSION = credit_spread_layer.CREDIT_SPREAD_PARAM_VERSION
CreditSpreadParams = credit_spread_layer.CreditSpreadParams
simulate_credit_spreads_for_dollar_path = credit_spread_layer.simulate_credit_spreads_for_dollar_path
DOLLAR_LIQUIDITY_PARAM_VERSION = dollar_liquidity_layer.DOLLAR_LIQUIDITY_PARAM_VERSION
DollarLiquidityParams = dollar_liquidity_layer.DollarLiquidityParams
simulate_dollar_liquidity_for_yield_path = dollar_liquidity_layer.simulate_dollar_liquidity_for_yield_path
GDPParams = global_gdp_layer.GDPParams
GDP_PARAM_VERSION = global_gdp_layer.PARAM_VERSION
simulate_global_gdp = global_gdp_layer.simulate_global_gdp
INFLATION_PARAM_VERSION = inflation_layer.INFLATION_PARAM_VERSION
InflationParams = inflation_layer.InflationParams
as_float = inflation_layer.as_float
simulate_inflation_for_gdp_path = inflation_layer.simulate_inflation_for_gdp_path
COMBINED_OIL_COMMODITY_FIELDS = oil_commodity_layer.COMBINED_OIL_COMMODITY_FIELDS
OIL_COMMODITY_PARAM_VERSION = oil_commodity_layer.OIL_COMMODITY_PARAM_VERSION
OilCommodityParams = oil_commodity_layer.OilCommodityParams
simulate_oil_commodities_for_asset_path = oil_commodity_layer.simulate_oil_commodities_for_asset_path
POLICY_PARAM_VERSION = policy_rate_layer.POLICY_PARAM_VERSION
PolicyRateParams = policy_rate_layer.PolicyRateParams
simulate_policy_for_macro_path = policy_rate_layer.simulate_policy_for_macro_path
YIELD_CURVE_PARAM_VERSION = yield_curve_layer.YIELD_CURVE_PARAM_VERSION
YieldCurveParams = yield_curve_layer.YieldCurveParams
simulate_yield_curve_for_policy_path = yield_curve_layer.simulate_yield_curve_for_policy_path


MACRO_FEEDBACK_PARAM_VERSION = "global-macro-feedback-calibration-v0.4"
MACRO_FEEDBACK_INTERFACE_VERSION = "macro-feedback-interface-v0.4"
CONVERGENCE_TOLERANCE_VERSION = "macro-feedback-convergence-tolerances-v0.1"
FEEDBACK_RELAXATION_STRATEGY_VERSION = "constant-relaxation-with-residual-check-v1"
FIXED_POINT_VERIFICATION_VERSION = "macro-feedback-fixed-point-residual-v1"
MINIMUM_FEEDBACK_ITERATIONS = 3
MINIMUM_CONSECUTIVE_CONVERGED_PASSES = 2


FEEDBACK_BLEND_NUMERIC_FIELDS = (
    "feedback_growth_impulse_pct",
    "feedback_output_gap_impulse_pct",
    "feedback_financial_stress_impulse",
    "feedback_inflation_impulse_pct",
    "feedback_policy_impulse_pct",
    "macro_feedback_intensity_index",
    "macro_feedback_growth_raw_pct",
    "macro_feedback_stress_raw",
    "macro_feedback_inflation_raw_pct",
    "macro_feedback_policy_raw_pct",
)


MACRO_FEEDBACK_FIELDS = [
    "macro_feedback_param_version",
    "macro_feedback_interface_version",
    "macro_feedback_iteration",
    "macro_feedback_intensity_index",
    "macro_feedback_growth_raw_pct",
    "macro_feedback_stress_raw",
    "macro_feedback_inflation_raw_pct",
    "macro_feedback_policy_raw_pct",
    "macro_feedback_iterations_requested",
    "macro_feedback_iterations_run",
    "macro_feedback_min_iterations",
    "macro_feedback_max_iterations",
    "macro_feedback_converged",
    "macro_feedback_last_pass_converged",
    "macro_feedback_consecutive_converged_passes",
    "macro_feedback_convergence_reason",
    "macro_feedback_delta_bounced",
    "macro_feedback_last_pass_delta_index",
    "macro_feedback_max_pass_delta_index",
    "macro_feedback_fixed_point_residual_checked",
    "macro_feedback_fixed_point_residual_converged",
    "macro_feedback_fixed_point_residual_delta_index",
    "macro_feedback_note",
]


BRANCH_RISK_PARAM_VERSION = "global-branch-risk-layer-v0.1"
BRANCH_RISK_INTERFACE_VERSION = "branch-risk-watchlist-interface-v0.1"


BRANCH_RISK_FIELDS = [
    "branch_risk_param_version",
    "branch_risk_interface_version",
    "branch_risk_primary_id",
    "branch_risk_primary_label",
    "branch_risk_primary_probability_pct",
    "branch_risk_primary_severity_index",
    "branch_risk_primary_horizon_years",
    "branch_risk_primary_impact_years",
    "branch_risk_primary_tail_years",
    "branch_risk_primary_cooldown_years",
    "branch_risk_secondary_ids",
    "branch_risk_watchlist",
    "branch_risk_evidence",
    "branch_risk_count",
]


COMBINED_MACRO_FEEDBACK_FIELDS = COMBINED_OIL_COMMODITY_FIELDS + MACRO_FEEDBACK_FIELDS + BRANCH_RISK_FIELDS


@dataclass(frozen=True)
class MacroFeedbackParams:
    feedback_lag_years: int = 1
    feedback_iterations: int = 16
    # The first feedback rerun remains a full update for compatibility with
    # feedback_iterations=1. Later reruns use this constant deterministic
    # relaxation. The default is also a full update: the official 80-seed,
    # 60-year audit converges within the 16-pass cap, while a diminishing step
    # can make adjacent passes look stable merely because the step approaches
    # zero. A separate undamped residual pass therefore verifies the fixed
    # point before any run may be marked converged.
    feedback_iteration_relaxation: float = 1.0
    feedback_smoothing: float = 0.42
    stress_smoothing: float = 0.38
    inflation_smoothing: float = 0.40
    policy_smoothing: float = 0.36
    max_growth_drag_pct: float = -1.15
    max_growth_support_pct: float = 0.85
    max_output_gap_drag_pct: float = -2.20
    max_output_gap_support_pct: float = 1.40
    output_gap_lending_sentiment_beta: float = 0.010
    output_gap_lending_sentiment_anchor: float = 48.0
    output_gap_impairment_beta: float = 0.003
    output_gap_risk_appetite_beta: float = 0.020
    max_stress_easing: float = -8.0
    max_stress_tightening: float = 16.0
    max_inflation_drag_pct: float = -1.00
    max_inflation_push_pct: float = 1.35
    max_policy_easing_pct: float = -1.00
    max_policy_tightening_pct: float = 1.25
    # Convergence contract: at least three feedback passes, followed by two
    # consecutive adjacent-pass checks satisfying every authoritative field
    # tolerance. The composite index is diagnostic-only.
    min_feedback_iterations: int = MINIMUM_FEEDBACK_ITERATIONS
    max_feedback_iterations: int = 16
    convergence_consecutive_passes: int = 2
    convergence_growth_tolerance_pct: float = 0.15
    convergence_inflation_tolerance_pct: float = 0.20
    convergence_policy_tolerance_pct: float = 0.25
    convergence_2y_tolerance_pct: float = 0.25
    convergence_10y_tolerance_pct: float = 0.25
    convergence_dollar_tolerance_index: float = 1.5
    convergence_hy_tolerance_bps: float = 100.0
    convergence_oil_tolerance_usd: float = 20.0
    # Diagnostic-only composite index tolerance; no longer a gating condition on
    # its own — the per-field thresholds above are the authoritative check. Kept
    # so existing diagnostics remain comparable across the version bump.
    convergence_delta_index_tolerance: float = 75.0


def smooth(old: float, target: float, speed: float) -> float:
    return old * (1.0 - speed) + target * speed


def feedback_relaxation_for_iteration(
    params: MacroFeedbackParams,
    iteration: int,
) -> float:
    """Return the deterministic constant feedback relaxation for one rerun.

    ``iteration`` is zero-based. Iteration 0 deliberately applies the full
    derived feedback path so ``feedback_iterations=1`` keeps its historical
    one-rerun numerical semantics. Later iterations use the configured constant
    step. Convergence is never inferred from the damped adjacent delta alone;
    the solver separately evaluates one undamped fixed-point residual pass.
    """
    if iteration < 0:
        raise ValueError("feedback iteration must be non-negative")
    if iteration == 0:
        return 1.0

    initial = float(params.feedback_iteration_relaxation)
    if not 0.0 < initial <= 1.0:
        raise ValueError("feedback_iteration_relaxation must be in (0, 1]")
    return initial


# Diagnostic fields produced by the feedback calibration layer. These describe
# the macro feedback itself; scenario branch impulses must never be folded into
# them when the two feedback paths are merged in the orchestrator.
MACRO_FEEDBACK_RAW_FIELDS = (
    "macro_feedback_growth_raw_pct",
    "macro_feedback_stress_raw",
    "macro_feedback_inflation_raw_pct",
    "macro_feedback_policy_raw_pct",
)


def macro_feedback_intensity_from_applied(
    growth_applied: float,
    stress_applied: float,
    inflation_applied: float,
    policy_applied: float,
) -> float:
    """Recompute the macro feedback intensity index from the final applied impulses.

    The intensity index measures how active macro feedback is in a given year. It is
    a function of the applied macro impulses only, so it is recomputed here from the
    macro-applied values whenever feedback paths are merged instead of carrying a
    possibly-stale blended value. Scenario branch impulses do not contribute, so a
    scenario cannot masquerade as macro feedback intensity.
    """
    return clamp(
        24.0 * abs(growth_applied)
        + 2.0 * max(0.0, stress_applied)
        + 18.0 * abs(inflation_applied)
        + 18.0 * abs(policy_applied),
        0.0,
        100.0,
    )


# Published hard boundaries for the global rate/yield/dollar/FCI fields. These
# mirror the clamp() calls inside the yield-curve, dollar-liquidity and policy
# layers. The convergence contract records how many rows of each pass sit exactly
# on a boundary. These counts identify boundary-limited comparisons for audit;
# they do not prove that equal clamped values share the same unclamped target.
# Working Guide sub-Goal 4.1 can later add those target diagnostics.
GLOBAL_BOUNDARY_FIELDS: tuple[tuple[str, float, float], ...] = (
    ("global_2y_yield_pct", -0.35, 10.50),
    ("global_10y_yield_pct", -0.35, 10.50),
    ("global_short_rate_pct", -0.35, 10.50),
    ("global_dollar_index", 82.0, 124.0),
    ("global_financial_conditions_index", -4.0, 4.0),
)

_BOUNDARY_EPSILON = 1e-6


def count_boundary_hits(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Count rows sitting on a published floor or cap for each boundary field.

    Returns a dict with one entry per field plus a total. This lightweight
    diagnostic marks comparisons that are boundary-limited without pretending
    to recover the unclamped targets (that is sub-Goal 4.1). The authoritative
    convergence gate remains the eight published output-field deltas.
    """
    per_field: dict[str, dict[str, int]] = {}
    total_floor_hits = 0
    total_cap_hits = 0
    for field, floor, cap in GLOBAL_BOUNDARY_FIELDS:
        floor_hits = 0
        cap_hits = 0
        for row in records:
            value = as_float(row, field)
            if value <= floor + _BOUNDARY_EPSILON:
                floor_hits += 1
            elif value >= cap - _BOUNDARY_EPSILON:
                cap_hits += 1
        per_field[field] = {
            "floor_hits": floor_hits,
            "cap_hits": cap_hits,
            "boundary_hits": floor_hits + cap_hits,
        }
        total_floor_hits += floor_hits
        total_cap_hits += cap_hits
    return {
        "per_field": per_field,
        "total_floor_hits": total_floor_hits,
        "total_cap_hits": total_cap_hits,
        "total_boundary_hits": total_floor_hits + total_cap_hits,
    }


def calibrated_gdp_params(args: argparse.Namespace) -> GDPParams:
    return GDPParams(
        years=args.years,
        start_year=args.start_year,
        initial_gdp_trillion_usd=args.initial_gdp,
        volatility_scale=args.volatility_scale,
        output_gap_persistence=0.35,
        output_gap_adjustment_speed=0.34,
        output_gap_financial_stress_anchor_index=35.0,
        output_gap_financial_stress_loading=0.030,
        growth_adjustment_speed=0.50,
        growth_soft_limit_knee_pct=1.30,
        growth_soft_limit_scale_pct=1.80,
        max_growth_step_pct=1.45,
        direct_shock_growth_loading=0.52,
    )


def calibrated_credit_params() -> CreditSpreadParams:
    return CreditSpreadParams(
        base_hy_spread_bps=245.0,
        default_risk_hy_beta=4.45,
        lending_standards_hy_beta=3.65,
        funding_stress_hy_beta=2.55,
        fci_hy_beta=36.0,
        credit_tightening_hy_beta=72.0,
        crisis_hy_beta=145.0,
        hy_spread_speed=0.32,
        ig_spread_speed=0.30,
    )


def calibrated_asset_params() -> AssetPriceParams:
    return AssetPriceParams(
        earnings_growth_smooth=0.62,
        base_earnings_growth_pct=2.65,
        base_pe=21.5,
        real_rate_pe_beta=1.25,
        credit_pe_beta=0.0012,
        fci_pe_beta=0.55,
        dividend_yield_pct=3.00,
        equity_price_smooth=0.42,
        noise_scale=0.80,
    )


def calibrated_oil_params() -> OilCommodityParams:
    return OilCommodityParams(
        demand_pressure_speed=0.32,
        supply_shock_speed=0.36,
        inventory_pressure_speed=0.30,
        oil_return_speed=0.36,
        commodity_return_speed=0.32,
    )


def run_full_chain(
    seed: int,
    *,
    gdp_params: GDPParams,
    inflation_params: InflationParams,
    policy_params: PolicyRateParams,
    yield_curve_params: YieldCurveParams,
    dollar_liquidity_params: DollarLiquidityParams,
    credit_spread_params: CreditSpreadParams,
    asset_price_params: AssetPriceParams,
    oil_commodity_params: OilCommodityParams,
    feedback_path: Mapping[int, Mapping[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    gdp_records = simulate_global_gdp(seed, gdp_params, feedback_path)
    inflation_records = simulate_inflation_for_gdp_path(seed, gdp_records, inflation_params)
    policy_records = simulate_policy_for_macro_path(inflation_records, policy_params)
    yield_records = simulate_yield_curve_for_policy_path(policy_records, yield_curve_params)
    dollar_records = simulate_dollar_liquidity_for_yield_path(yield_records, dollar_liquidity_params)
    credit_records = simulate_credit_spreads_for_dollar_path(dollar_records, credit_spread_params)
    asset_records = simulate_asset_prices_for_credit_path(credit_records, asset_price_params)
    return simulate_oil_commodities_for_asset_path(asset_records, oil_commodity_params)


def derive_feedback_path(records: list[dict[str, Any]], params: MacroFeedbackParams) -> dict[int, dict[str, Any]]:
    feedback_by_year: dict[int, dict[str, Any]] = {}
    previous_growth = 0.0
    previous_stress = 0.0
    previous_inflation = 0.0
    previous_policy = 0.0

    for row in records:
        source_index = int(row["year_index"])
        if source_index <= 0:
            continue
        target_index = source_index + params.feedback_lag_years
        if target_index > int(records[-1]["year_index"]):
            continue

        credit_drag = as_float(row, "credit_to_gdp_drag_placeholder")
        dollar_drag = as_float(row, "dollar_to_gdp_drag_placeholder")
        policy_drag = as_float(row, "policy_to_gdp_drag_placeholder")
        inflation_drag = as_float(row, "inflation_to_gdp_drag_placeholder")
        yield_drag = as_float(row, "yield_curve_to_gdp_drag_placeholder")
        oil_drag = as_float(row, "oil_to_gdp_drag_placeholder")
        wealth_impulse = as_float(row, "asset_to_gdp_wealth_impulse")
        lagged_support = as_float(row, "gdp_lagged_support")
        credit_impairment = as_float(row, "credit_impairment_stock_index")

        growth_raw = (
            0.34 * credit_drag
            + 0.30 * dollar_drag
            + 0.24 * policy_drag
            + 0.22 * inflation_drag
            + 0.44 * oil_drag
            + 0.34 * wealth_impulse
            + 0.24 * yield_drag
            + 0.18 * lagged_support
            + 0.008 * (as_float(row, "risk_appetite_index", 50.0) - 50.0)
            + 0.008 * (as_float(row, "global_liquidity_index", 55.0) - 55.0)
            + 0.006 * (as_float(row, "credit_availability_index", 58.0) - 58.0)
            - 0.005 * credit_impairment
        )
        growth_applied = clamp(
            smooth(previous_growth, growth_raw, params.feedback_smoothing),
            params.max_growth_drag_pct,
            params.max_growth_support_pct,
        )

        hy_spread = as_float(row, "global_high_yield_spread_bps", 420.0)
        credit_spread_change = as_float(row, "credit_spread_change_bps")
        oil_credit_stress = as_float(row, "oil_to_credit_stress_impulse")
        asset_fci = as_float(row, "asset_to_policy_financial_conditions_impulse")
        dollar_credit = as_float(row, "dollar_to_credit_tightening_impulse")
        liquidity_credit = as_float(row, "liquidity_to_credit_easing_impulse")
        asset_credit = as_float(row, "asset_to_credit_risk_appetite_impulse")
        stress_raw = (
            0.010 * max(0.0, hy_spread - 520.0)
            + 0.030 * max(0.0, credit_spread_change)
            + 1.30 * max(0.0, oil_credit_stress)
            + 1.15 * max(0.0, asset_fci)
            + 0.90 * max(0.0, dollar_credit)
            + 0.14 * max(0.0, as_float(row, "credit_convexity_pressure_index"))
            + 0.055 * credit_impairment
            + 0.10 * max(0.0, as_float(row, "bank_balance_sheet_stress_index") - 55.0)
            + 0.12 * max(0.0, 45.0 - as_float(row, "bank_lending_sentiment_index", 55.0))
            - 0.70 * max(0.0, liquidity_credit)
            - 0.70 * max(0.0, asset_credit)
        )
        stress_applied = clamp(
            smooth(previous_stress, stress_raw, params.stress_smoothing),
            params.max_stress_easing,
            params.max_stress_tightening,
        )

        # Growth feedback already enters the GDP gap target directly and
        # credit/oil conditions already enter growth_raw. Keeping another
        # growth or HY-spread term here double-counted the same contraction.
        # This impulse therefore carries only independent balance-sheet and
        # risk-appetite information, with symmetric centered channels.
        output_gap_applied = clamp(
            params.output_gap_lending_sentiment_beta
            * (
                as_float(row, "bank_lending_sentiment_index", 55.0)
                - params.output_gap_lending_sentiment_anchor
            )
            - params.output_gap_impairment_beta * credit_impairment
            + params.output_gap_risk_appetite_beta
            * (as_float(row, "risk_appetite_index", 50.0) - 50.0),
            params.max_output_gap_drag_pct,
            params.max_output_gap_support_pct,
        )

        inflation_raw = (
            0.58 * as_float(row, "oil_to_headline_inflation_impulse")
            + 0.34 * as_float(row, "dollar_to_import_inflation_impulse")
            + 0.24 * as_float(row, "asset_to_inflation_wealth_demand_impulse")
            + 0.30 * as_float(row, "policy_to_inflation_lagged_impulse")
            + 0.28 * as_float(row, "credit_to_inflation_demand_drag_placeholder")
        )
        inflation_applied = clamp(
            smooth(previous_inflation, inflation_raw, params.inflation_smoothing),
            params.max_inflation_drag_pct,
            params.max_inflation_push_pct,
        )

        policy_raw = (
            0.42 * as_float(row, "oil_to_policy_pressure_impulse")
            + 0.36 * as_float(row, "inflation_to_policy_rate_impulse")
            + 0.20 * asset_fci
            - 0.36 * as_float(row, "credit_to_policy_easing_pressure")
        )
        policy_applied = clamp(
            smooth(previous_policy, policy_raw, params.policy_smoothing),
            params.max_policy_easing_pct,
            params.max_policy_tightening_pct,
        )

        intensity = macro_feedback_intensity_from_applied(
            growth_applied,
            stress_applied,
            inflation_applied,
            policy_applied,
        )
        feedback_by_year[target_index] = {
            "feedback_growth_impulse_pct": growth_applied,
            "feedback_output_gap_impulse_pct": output_gap_applied,
            "feedback_financial_stress_impulse": stress_applied,
            "feedback_inflation_impulse_pct": inflation_applied,
            "feedback_policy_impulse_pct": policy_applied,
            "feedback_source": f"lagged_macro_feedback_from_year_{int(row['year'])}",
            "macro_feedback_intensity_index": intensity,
            "macro_feedback_growth_raw_pct": growth_raw,
            "macro_feedback_stress_raw": stress_raw,
            "macro_feedback_inflation_raw_pct": inflation_raw,
            "macro_feedback_policy_raw_pct": policy_raw,
        }

        previous_growth = growth_applied
        previous_stress = stress_applied
        previous_inflation = inflation_applied
        previous_policy = policy_applied

    return feedback_by_year


def blend_feedback_paths(
    previous: Mapping[int, Mapping[str, Any]],
    current: Mapping[int, Mapping[str, Any]],
    relaxation: float,
) -> dict[int, dict[str, Any]]:
    """Blend feedback inputs in deterministic key and field order."""
    if not 0.0 < relaxation <= 1.0:
        raise ValueError("feedback relaxation must be in (0, 1]")
    if not previous:
        return {key: dict(current[key]) for key in sorted(current)}

    blended: dict[int, dict[str, Any]] = {}
    for key in sorted(set(previous) | set(current)):
        old = previous.get(key, {})
        new = current.get(key, {})
        row: dict[str, Any] = {}
        for field in FEEDBACK_BLEND_NUMERIC_FIELDS:
            old_value = as_float(old, field)
            new_value = as_float(new, field)
            row[field] = old_value * (1.0 - relaxation) + new_value * relaxation
        row["feedback_source"] = str(
            new.get("feedback_source")
            or old.get("feedback_source")
            or "lagged_macro_feedback"
        )
        blended[key] = row
    return blended


def branch_probability(score: float) -> float:
    return round(clamp(5.0 + 0.75 * score, 10.0, 85.0), 1)


def add_branch_candidate(
    candidates: list[dict[str, Any]],
    *,
    event_id: str,
    label: str,
    score: float,
    threshold: float,
    horizon_years: int,
    impact_years: int,
    tail_years: int,
    cooldown_years: int,
    summary: str,
    evidence: list[str],
) -> None:
    if score < threshold:
        return
    candidates.append(
        {
            "id": event_id,
            "label": label,
            "probability_pct": branch_probability(score),
            "severity_index": round(clamp(score, 0.0, 100.0), 1),
            "horizon_years": horizon_years,
            "impact_years": impact_years,
            "tail_years": tail_years,
            "cooldown_years": cooldown_years,
            "summary": summary,
            "evidence": evidence,
        }
    )


def detect_branch_risks_for_index(records: list[dict[str, Any]], index: int) -> list[dict[str, Any]]:
    row = records[index]
    if int(row.get("year_index", 0)) <= 0:
        return []

    prev = records[max(0, index - 1)]
    recent = records[max(0, index - 3): index + 1]
    growth = as_float(row, "realized_growth_pct")
    prev_growth = as_float(prev, "realized_growth_pct", growth)
    gap = as_float(row, "output_gap_pct")
    headline = as_float(row, "headline_inflation_pct", 2.35)
    prev_headline = as_float(prev, "headline_inflation_pct", headline)
    core = as_float(row, "core_inflation_pct", 2.20)
    expectation = as_float(row, "inflation_expectation_pct", 2.35)
    policy_rate = as_float(row, "global_policy_rate_pct")
    policy_change = as_float(row, "policy_rate_change_pct")
    real_policy = as_float(row, "real_policy_rate_pct")
    neutral_policy = as_float(row, "neutral_policy_rate_pct", 3.25)
    hike_pressure = as_float(row, "rate_hike_pressure")
    cut_pressure = as_float(row, "rate_cut_pressure")
    qe = as_float(row, "qe_liquidity_index")
    ten_year = as_float(row, "global_10y_yield_pct")
    prev_ten_year = as_float(prev, "global_10y_yield_pct", ten_year)
    term_spread = as_float(row, "term_spread_10y_2y_pct")
    term_premium = as_float(row, "term_premium_pct")
    dollar = as_float(row, "global_dollar_index", 100.0)
    dollar_yoy = as_float(row, "dollar_yoy_change_pct")
    liquidity = as_float(row, "global_liquidity_index", 55.0)
    liquidity_impulse = as_float(row, "liquidity_impulse_index")
    funding_stress = as_float(row, "dollar_funding_stress_index")
    em_stress = as_float(row, "em_stress_index")
    fci = as_float(row, "global_financial_conditions_index")
    risk_appetite = as_float(row, "risk_appetite_index", 50.0)
    hy = as_float(row, "global_high_yield_spread_bps", 420.0)
    prev_hy = as_float(prev, "global_high_yield_spread_bps", hy)
    spread_change = as_float(row, "credit_spread_change_bps")
    availability = as_float(row, "credit_availability_index", 58.0)
    bank_sentiment = as_float(row, "bank_lending_sentiment_index", 54.0)
    bank_stress = as_float(row, "bank_balance_sheet_stress_index", 34.0)
    impairment = as_float(row, "credit_impairment_stock_index")
    refinancing = as_float(row, "corporate_refinancing_pressure_index")
    default_risk = as_float(row, "default_risk_index")
    equity_return = as_float(row, "equity_total_return_pct")
    eps_growth = as_float(row, "equity_eps_growth_pct")
    pe = as_float(row, "equity_valuation_pe")
    prev_pe = as_float(prev, "equity_valuation_pe", pe)
    drawdown = as_float(row, "equity_drawdown_pct")
    sovereign_return = as_float(row, "sovereign_bond_total_return_pct")
    brent = as_float(row, "brent_oil_price_usd")
    oil_yoy = as_float(row, "oil_yoy_change_pct")
    oil_demand = as_float(row, "oil_demand_pressure_index", 50.0)
    oil_supply = as_float(row, "oil_supply_shock_index")
    energy_pressure = as_float(row, "energy_cost_pressure_index")

    crisis_recent = any(
        as_float(item, "realized_growth_pct") < 0.0
        or as_float(item, "output_gap_pct") < -3.5
        or as_float(item, "global_high_yield_spread_bps", 420.0) > 700.0
        or as_float(item, "credit_impairment_stock_index") > 45.0
        for item in recent
    )
    candidates: list[dict[str, Any]] = []

    score = 0.0
    score += 18.0 if crisis_recent else 0.0
    score += 14.0 if growth > 0.8 else 0.0
    score += 12.0 if hy < prev_hy - 20.0 else 0.0
    score += 10.0 if equity_return > 3.0 else 0.0
    score += 14.0 if gap < -2.0 else 0.0
    score += 14.0 if impairment > 35.0 else 7.0 if impairment > 20.0 else 0.0
    score += 8.0 if bank_sentiment < 52.0 else 0.0
    add_branch_candidate(
        candidates,
        event_id="false_dawn",
        label="虚假黎明",
        score=score,
        threshold=64.0,
        horizon_years=3,
        impact_years=3,
        tail_years=4,
        cooldown_years=3,
        summary="表面复苏已经出现，但信用疤痕和负产出缺口仍在，未来几年存在二次探底风险。",
        evidence=[f"GDP {growth:.2f}%", f"HY {hy:.0f}bps", f"信用疤痕 {impairment:.1f}", f"产出缺口 {gap:.2f}%"],
    )

    score = 0.0
    score += 18.0 if headline < 2.5 else 0.0
    score += 16.0 if gap < 0.0 else 0.0
    score += 18.0 if policy_change > 0.15 else 8.0 if policy_change > 0.0 else 0.0
    score += 12.0 if real_policy > 0.5 else 0.0
    score += 10.0 if cut_pressure > hike_pressure else 0.0
    score += 8.0 if term_spread < -0.35 else 0.0
    add_branch_candidate(
        candidates,
        event_id="policy_mistake_tightening",
        label="政策失误：过早收紧",
        score=score,
        threshold=58.0,
        horizon_years=2,
        impact_years=2,
        tail_years=3,
        cooldown_years=2,
        summary="通胀不高且产出缺口为负时仍继续收紧，软着陆路径有转向衰退的风险。",
        evidence=[f"Headline {headline:.2f}%", f"产出缺口 {gap:.2f}%", f"政策变化 {policy_change:.2f}%", f"实际政策 {real_policy:.2f}%"],
    )

    score = 0.0
    score += 18.0 if headline > 3.5 else 9.0 if headline > 3.0 else 0.0
    score += 16.0 if core > 3.0 else 8.0 if core > 2.7 else 0.0
    score += 12.0 if expectation > 3.0 else 0.0
    score += 14.0 if policy_change <= 0.05 else 0.0
    score += 10.0 if real_policy < neutral_policy - 0.5 else 0.0
    score += 8.0 if liquidity > 60.0 else 0.0
    add_branch_candidate(
        candidates,
        event_id="policy_behind_curve",
        label="政策失误：落后曲线",
        score=score,
        threshold=58.0,
        horizon_years=2,
        impact_years=2,
        tail_years=3,
        cooldown_years=2,
        summary="通胀和预期已经升温，但政策反应偏慢，未来可能走向通胀再加速或滞胀。",
        evidence=[f"Headline {headline:.2f}%", f"Core {core:.2f}%", f"政策变化 {policy_change:.2f}%", f"预期 {expectation:.2f}%"],
    )

    score = 0.0
    score += 18.0 if hy > 720.0 else 10.0 if hy > 620.0 else 0.0
    score += 16.0 if refinancing > 65.0 else 8.0 if refinancing > 55.0 else 0.0
    score += 14.0 if availability < 45.0 else 7.0 if availability < 55.0 else 0.0
    score += 12.0 if default_risk > 60.0 else 0.0
    score += 10.0 if spread_change > 45.0 else 0.0
    score += 10.0 if impairment > 35.0 else 0.0
    add_branch_candidate(
        candidates,
        event_id="credit_accident",
        label="信用事故",
        score=score,
        threshold=58.0,
        horizon_years=2,
        impact_years=2,
        tail_years=5,
        cooldown_years=3,
        summary="高收益利差、再融资压力和信用可得性同时恶化，可能触发信用市场的二次冻结。",
        evidence=[f"HY {hy:.0f}bps", f"再融资 {refinancing:.1f}", f"信用可得性 {availability:.1f}", f"违约风险 {default_risk:.1f}"],
    )

    score = 0.0
    score += 14.0 if qe > 35.0 else 0.0
    score += 12.0 if liquidity > 58.0 else 0.0
    score += 18.0 if bank_sentiment < 45.0 else 9.0 if bank_sentiment < 52.0 else 0.0
    score += 16.0 if availability < 50.0 else 8.0 if availability < 58.0 else 0.0
    score += 12.0 if impairment > 30.0 else 0.0
    add_branch_candidate(
        candidates,
        event_id="bank_lending_trap",
        label="银行惜贷循环",
        score=score,
        threshold=58.0,
        horizon_years=3,
        impact_years=3,
        tail_years=5,
        cooldown_years=3,
        summary="流动性并不稀缺，但银行仍不愿扩张贷款，政策传导可能卡在金融系统内部。",
        evidence=[f"QE {qe:.1f}", f"流动性 {liquidity:.1f}", f"银行意愿 {bank_sentiment:.1f}", f"信用可得性 {availability:.1f}"],
    )

    score = 0.0
    score += 18.0 if dollar > 108.0 else 9.0 if dollar > 104.0 else 0.0
    score += 14.0 if dollar_yoy > 4.0 else 7.0 if dollar_yoy > 2.0 else 0.0
    score += 18.0 if funding_stress > 55.0 else 9.0 if funding_stress > 45.0 else 0.0
    score += 14.0 if em_stress > 55.0 else 7.0 if em_stress > 45.0 else 0.0
    score += 10.0 if liquidity < 48.0 else 0.0
    add_branch_candidate(
        candidates,
        event_id="dollar_squeeze_escalation",
        label="美元挤兑升级",
        score=score,
        threshold=58.0,
        horizon_years=2,
        impact_years=2,
        tail_years=2,
        cooldown_years=2,
        summary="美元走强和融资压力可能进一步抽紧全球流动性，外部部门和风险资产更脆弱。",
        evidence=[f"美元 {dollar:.1f}", f"美元YoY {dollar_yoy:.2f}%", f"融资压力 {funding_stress:.1f}", f"EM压力 {em_stress:.1f}"],
    )

    score = 0.0
    score += 16.0 if brent > 115.0 else 8.0 if brent > 100.0 else 0.0
    score += 16.0 if oil_yoy > 22.0 else 8.0 if oil_yoy > 12.0 else 0.0
    score += 14.0 if energy_pressure > 68.0 else 7.0 if energy_pressure > 58.0 else 0.0
    score += 12.0 if oil_supply > 25.0 else 0.0
    score += 10.0 if headline > 3.2 else 0.0
    add_branch_candidate(
        candidates,
        event_id="energy_shock_escalation",
        label="能源冲击升级",
        score=score,
        threshold=56.0,
        horizon_years=2,
        impact_years=2,
        tail_years=3,
        cooldown_years=2,
        summary="能源价格已经在高位，若供给冲击延续，增长和通胀会同时受到压力。",
        evidence=[f"Brent {brent:.1f}", f"油价YoY {oil_yoy:.2f}%", f"能源压力 {energy_pressure:.1f}", f"供给冲击 {oil_supply:.1f}"],
    )

    score = 0.0
    score += 18.0 if ten_year - prev_ten_year > 0.55 else 9.0 if ten_year - prev_ten_year > 0.30 else 0.0
    score += 14.0 if term_premium > 1.1 else 7.0 if term_premium > 0.9 else 0.0
    score += 18.0 if sovereign_return < -5.0 else 9.0 if sovereign_return < -3.0 else 0.0
    score += 10.0 if headline > 3.2 else 0.0
    score += 10.0 if fci > 1.0 else 0.0
    add_branch_candidate(
        candidates,
        event_id="bond_market_accident",
        label="债券市场失控",
        score=score,
        threshold=56.0,
        horizon_years=1,
        impact_years=1,
        tail_years=2,
        cooldown_years=1,
        summary="长端利率或期限溢价快速上行，可能引发股债同跌和政策空间收缩。",
        evidence=[f"10Y变化 {ten_year - prev_ten_year:.2f}%", f"期限溢价 {term_premium:.2f}%", f"主权债 {sovereign_return:.2f}%", f"FCI {fci:.2f}"],
    )

    score = 0.0
    score += 16.0 if 1.4 <= growth <= 3.3 else 0.0
    score += 14.0 if -1.5 <= gap <= 0.8 else 0.0
    score += 12.0 if headline < prev_headline and 1.6 <= headline <= 3.0 else 0.0
    score += 12.0 if hy < 560.0 else 0.0
    score += 10.0 if bank_sentiment > 52.0 else 0.0
    score += 8.0 if impairment < 25.0 else 0.0
    add_branch_candidate(
        candidates,
        event_id="soft_landing_success",
        label="软着陆成功",
        score=score,
        threshold=62.0,
        horizon_years=2,
        impact_years=2,
        tail_years=2,
        cooldown_years=2,
        summary="通胀降温且增长没有破位，如果信用保持稳定，路径可能转入温和扩张。",
        evidence=[f"GDP {growth:.2f}%", f"Headline {headline:.2f}%", f"HY {hy:.0f}bps", f"信用疤痕 {impairment:.1f}"],
    )

    score = 0.0
    score += 16.0 if liquidity > 64.0 else 8.0 if liquidity > 58.0 else 0.0
    score += 12.0 if qe > 35.0 else 0.0
    score += 16.0 if equity_return > 8.0 else 8.0 if equity_return > 5.0 else 0.0
    score += 12.0 if pe - prev_pe > 0.5 or pe > 24.0 else 0.0
    score += 10.0 if growth < 2.2 or eps_growth < 1.5 else 0.0
    add_branch_candidate(
        candidates,
        event_id="liquidity_bubble",
        label="流动性牛市脱实向虚",
        score=score,
        threshold=58.0,
        horizon_years=3,
        impact_years=2,
        tail_years=3,
        cooldown_years=3,
        summary="资产上涨主要由流动性和估值驱动，若盈利跟不上，后续泡沫脆弱度会上升。",
        evidence=[f"流动性 {liquidity:.1f}", f"QE {qe:.1f}", f"股票 {equity_return:.2f}%", f"EPS {eps_growth:.2f}%"],
    )

    score = 0.0
    score += 18.0 if refinancing > 65.0 else 9.0 if refinancing > 55.0 else 0.0
    score += 14.0 if hy > 650.0 else 7.0 if hy > 560.0 else 0.0
    score += 14.0 if availability < 48.0 else 0.0
    score += 10.0 if real_policy > 1.0 else 0.0
    score += 8.0 if impairment > 30.0 else 0.0
    add_branch_candidate(
        candidates,
        event_id="refinancing_wall",
        label="再融资墙",
        score=score,
        threshold=56.0,
        horizon_years=3,
        impact_years=3,
        tail_years=5,
        cooldown_years=3,
        summary="企业到期压力和高融资成本叠加，可能延长信用拖累和盈利修复时间。",
        evidence=[f"再融资 {refinancing:.1f}", f"HY {hy:.0f}bps", f"信用可得性 {availability:.1f}", f"实际政策 {real_policy:.2f}%"],
    )

    score = 0.0
    score += 14.0 if headline < prev_headline - 0.35 else 0.0
    score += 14.0 if oil_yoy < -10.0 else 7.0 if oil_yoy < -5.0 else 0.0
    score += 14.0 if growth < 1.2 else 0.0
    score += 12.0 if gap < -2.0 else 0.0
    score += 10.0 if oil_demand < 45.0 else 0.0
    add_branch_candidate(
        candidates,
        event_id="demand_destruction_disinflation",
        label="需求破坏式降通胀",
        score=score,
        threshold=54.0,
        horizon_years=2,
        impact_years=2,
        tail_years=3,
        cooldown_years=2,
        summary="通胀回落可能来自需求坍缩而非健康降温，未来增长仍有下行分岔。",
        evidence=[f"Headline变化 {headline - prev_headline:.2f}%", f"油价YoY {oil_yoy:.2f}%", f"GDP {growth:.2f}%", f"需求压力 {oil_demand:.1f}"],
    )

    score = 0.0
    score += 16.0 if growth < 1.2 else 0.0
    score += 14.0 if gap < -1.5 else 0.0
    score += 18.0 if headline > 3.8 else 9.0 if headline > 3.2 else 0.0
    score += 14.0 if core > 3.0 else 0.0
    score += 10.0 if brent > 100.0 else 0.0
    score += 8.0 if hy > 600.0 else 0.0
    add_branch_candidate(
        candidates,
        event_id="stagflation_trap",
        label="滞胀陷阱",
        score=score,
        threshold=58.0,
        horizon_years=3,
        impact_years=3,
        tail_years=4,
        cooldown_years=3,
        summary="低增长和高通胀同时存在，政策反应很容易在稳增长和控通胀之间反复摇摆。",
        evidence=[f"GDP {growth:.2f}%", f"产出缺口 {gap:.2f}%", f"Headline {headline:.2f}%", f"Core {core:.2f}%"],
    )

    score = 0.0
    score += 18.0 if equity_return > 10.0 else 9.0 if equity_return > 7.0 else 0.0
    score += 12.0 if risk_appetite > 62.0 else 0.0
    score += 12.0 if pe > 25.0 else 0.0
    score += 10.0 if eps_growth < 1.0 else 0.0
    score += 8.0 if hy > 520.0 or fci > 0.5 else 0.0
    add_branch_candidate(
        candidates,
        event_id="risk_asset_bull_fragility",
        label="风险资产牛市脆弱化",
        score=score,
        threshold=56.0,
        horizon_years=2,
        impact_years=2,
        tail_years=2,
        cooldown_years=2,
        summary="风险资产表现很好，但盈利或信用基础不够扎实，后续对利率和流动性更敏感。",
        evidence=[f"股票 {equity_return:.2f}%", f"风险偏好 {risk_appetite:.1f}", f"PE {pe:.1f}", f"EPS {eps_growth:.2f}%"],
    )

    return sorted(candidates, key=lambda item: item["probability_pct"], reverse=True)


def annotate_branch_risks(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    annotated: list[dict[str, Any]] = []
    suppressed_until: dict[str, int] = {}
    for index, row in enumerate(records):
        risks = []
        for risk in detect_branch_risks_for_index(records, index):
            risk_id = str(risk.get("id", ""))
            if risk_id and index <= suppressed_until.get(risk_id, -1):
                continue
            risks.append(risk)
        primary = risks[0] if risks else {}
        watchlist = risks[:4]
        for risk in watchlist:
            risk_id = str(risk.get("id", ""))
            if risk_id:
                suppressed_until[risk_id] = index + int(risk.get("cooldown_years", risk.get("horizon_years", 1)) or 1)
        annotated.append(
            round_record(
                {
                    **row,
                    "branch_risk_param_version": BRANCH_RISK_PARAM_VERSION,
                    "branch_risk_interface_version": BRANCH_RISK_INTERFACE_VERSION,
                    "branch_risk_primary_id": str(primary.get("id", "")),
                    "branch_risk_primary_label": str(primary.get("label", "")),
                    "branch_risk_primary_probability_pct": as_float(primary, "probability_pct"),
                    "branch_risk_primary_severity_index": as_float(primary, "severity_index"),
                    "branch_risk_primary_horizon_years": int(primary.get("horizon_years", 0) or 0),
                    "branch_risk_primary_impact_years": int(primary.get("impact_years", 0) or 0),
                    "branch_risk_primary_tail_years": int(primary.get("tail_years", 0) or 0),
                    "branch_risk_primary_cooldown_years": int(primary.get("cooldown_years", 0) or 0),
                    "branch_risk_secondary_ids": json.dumps([item["id"] for item in risks[1:4]], ensure_ascii=False, separators=(",", ":")),
                    "branch_risk_watchlist": json.dumps(watchlist, ensure_ascii=False, separators=(",", ":")),
                    "branch_risk_evidence": json.dumps(primary.get("evidence", []), ensure_ascii=False, separators=(",", ":")),
                    "branch_risk_count": len(risks),
                }
            )
        )
    return annotated


def build_row_convergence_annotations(
    pass_records: list[list[dict[str, Any]]],
    params: MacroFeedbackParams,
    *,
    min_iterations: int,
    max_iterations: int,
) -> dict[int, dict[str, Any]]:
    """Build prefix-stable, row-local convergence annotations.

    Run-level convergence remains authoritative in the returned convergence
    object and manifest. Row annotations intentionally describe the earliest
    pass at which that specific year stabilized, so common-year rows remain
    strict prefixes across different requested horizons.
    """

    contracts = (
        ("realized_growth_pct", params.convergence_growth_tolerance_pct, 22.0),
        ("headline_inflation_pct", params.convergence_inflation_tolerance_pct, 18.0),
        ("global_policy_rate_pct", params.convergence_policy_tolerance_pct, 16.0),
        ("global_2y_yield_pct", params.convergence_2y_tolerance_pct, 10.0),
        ("global_10y_yield_pct", params.convergence_10y_tolerance_pct, 10.0),
        ("global_dollar_index", params.convergence_dollar_tolerance_index, 1.5),
        ("global_high_yield_spread_bps", params.convergence_hy_tolerance_bps, 1.0 / 8.0),
        ("brent_oil_price_usd", params.convergence_oil_tolerance_usd, 1.0 / 6.0),
    )
    by_pass = [
        {int(row["year_index"]): row for row in rows}
        for rows in pass_records
    ]
    year_indices = sorted(by_pass[-1]) if by_pass else []
    annotations: dict[int, dict[str, Any]] = {}
    consecutive_required = max(
        MINIMUM_CONSECUTIVE_CONVERGED_PASSES,
        int(params.convergence_consecutive_passes),
    )

    for year_index in year_indices:
        diagnostics: list[dict[str, Any]] = []
        for pass_index in range(1, len(by_pass)):
            previous = by_pass[pass_index - 1].get(year_index)
            current = by_pass[pass_index].get(year_index)
            if previous is None or current is None:
                diagnostics.append(
                    {"pass": pass_index, "converged": False, "delta_index": 0.0}
                )
                continue
            deltas = {
                field: abs(as_float(current, field) - as_float(previous, field))
                for field, _tolerance, _weight in contracts
            }
            diagnostics.append(
                {
                    "pass": pass_index,
                    "converged": all(
                        deltas[field] <= tolerance
                        for field, tolerance, _weight in contracts
                    ),
                    "delta_index": sum(
                        deltas[field] * weight
                        for field, _tolerance, weight in contracts
                    ),
                }
            )

        accepted_pass: int | None = None
        for diagnostic_index, diagnostic in enumerate(diagnostics):
            pass_number = int(diagnostic["pass"])
            if pass_number < min_iterations:
                continue
            start = diagnostic_index - consecutive_required + 1
            if start < 0:
                continue
            window = diagnostics[start : diagnostic_index + 1]
            if all(bool(item["converged"]) for item in window):
                accepted_pass = pass_number
                break

        if accepted_pass is None:
            accepted_pass = min(max_iterations, max(0, len(pass_records) - 1))
            accepted = False
        else:
            accepted = True
        relevant = [
            item for item in diagnostics if int(item["pass"]) <= accepted_pass
        ]
        last = relevant[-1] if relevant else {"converged": False, "delta_index": 0.0}
        trailing = 0
        for item in reversed(relevant):
            if not bool(item["converged"]):
                break
            trailing += 1
        annotations[year_index] = {
            "iterations_run": accepted_pass,
            "converged": accepted,
            "last_pass_converged": bool(last["converged"]),
            "consecutive_converged_passes": trailing,
            "convergence_reason": (
                "row_adjacent_pass_converged"
                if accepted
                else "row_adjacent_pass_not_converged"
            ),
            "last_pass_delta_index": float(last["delta_index"]),
            "max_pass_delta_index": max(
                (float(item["delta_index"]) for item in relevant),
                default=0.0,
            ),
            # A row only has adjacent-pass stability evidence. The undamped
            # shadow residual is evaluated for the complete Run and remains
            # authoritative in convergence/Manifest metadata.
            "fixed_point_residual_checked": False,
            "fixed_point_residual_converged": False,
            "fixed_point_residual_delta_index": 0.0,
        }
    return annotations


def annotate_feedback_records(
    records: list[dict[str, Any]],
    feedback_path: Mapping[int, Mapping[str, Any]],
    iteration: int,
    convergence: Mapping[str, Any],
) -> list[dict[str, Any]]:
    annotated: list[dict[str, Any]] = []
    iterations_requested = int(convergence.get("max_iterations", iteration))
    min_iterations = int(convergence.get("min_iterations", iterations_requested))
    max_iterations = int(convergence.get("max_iterations", iterations_requested))
    row_annotations = convergence.get("row_convergence_annotations", {})
    for row in records:
        year_index = int(row["year_index"])
        feedback = feedback_path.get(year_index, {})
        row_convergence = row_annotations.get(year_index, {})
        iterations_run = int(row_convergence.get("iterations_run", 0))
        note = "none" if not feedback else str(feedback.get("feedback_source", "lagged_macro_feedback"))
        annotated.append(
            round_record(
                {
                    **row,
                    "macro_feedback_param_version": MACRO_FEEDBACK_PARAM_VERSION,
                    "macro_feedback_interface_version": MACRO_FEEDBACK_INTERFACE_VERSION,
                    "macro_feedback_iteration": iterations_run,
                    "macro_feedback_intensity_index": as_float(feedback, "macro_feedback_intensity_index"),
                    "macro_feedback_growth_raw_pct": as_float(feedback, "macro_feedback_growth_raw_pct"),
                    "macro_feedback_stress_raw": as_float(feedback, "macro_feedback_stress_raw"),
                    "macro_feedback_inflation_raw_pct": as_float(feedback, "macro_feedback_inflation_raw_pct"),
                    "macro_feedback_policy_raw_pct": as_float(feedback, "macro_feedback_policy_raw_pct"),
                    "macro_feedback_iterations_requested": iterations_requested,
                    "macro_feedback_iterations_run": iterations_run,
                    "macro_feedback_min_iterations": min_iterations,
                    "macro_feedback_max_iterations": max_iterations,
                    "macro_feedback_converged": str(row_convergence.get("converged", False)).lower(),
                    "macro_feedback_last_pass_converged": str(
                        row_convergence.get("last_pass_converged", False)
                    ).lower(),
                    "macro_feedback_consecutive_converged_passes": int(
                        row_convergence.get("consecutive_converged_passes", 0)
                    ),
                    "macro_feedback_convergence_reason": str(
                        row_convergence.get(
                            "convergence_reason", "row_adjacent_pass_not_converged"
                        )
                    ),
                    "macro_feedback_delta_bounced": "false",
                    "macro_feedback_last_pass_delta_index": as_float(row_convergence, "last_pass_delta_index"),
                    "macro_feedback_max_pass_delta_index": as_float(row_convergence, "max_pass_delta_index"),
                    "macro_feedback_fixed_point_residual_checked": str(
                        row_convergence.get("fixed_point_residual_checked", False)
                    ).lower(),
                    "macro_feedback_fixed_point_residual_converged": str(
                        row_convergence.get("fixed_point_residual_converged", False)
                    ).lower(),
                    "macro_feedback_fixed_point_residual_delta_index": as_float(
                        row_convergence,
                        "fixed_point_residual_delta_index",
                    ),
                    "macro_feedback_note": note,
                }
            )
        )
    return annotate_branch_risks(annotated)


def compare_pass_records(
    *,
    seed: int,
    from_pass: int,
    to_pass: int,
    previous: list[dict[str, Any]],
    current: list[dict[str, Any]],
    params: MacroFeedbackParams,
) -> dict[str, Any]:
    previous_indices = [int(row["year_index"]) for row in previous]
    current_indices = [int(row["year_index"]) for row in current]
    previous_by_index = {int(row["year_index"]): row for row in previous}
    current_by_index = {int(row["year_index"]): row for row in current}
    previous_positive = {index for index in previous_indices if index > 0}
    current_positive = {index for index in current_indices if index > 0}
    shared_indices = sorted(previous_positive & current_positive)
    rows = [
        (previous_by_index[index], current_by_index[index])
        for index in shared_indices
    ]
    comparison_complete = bool(shared_indices) and (
        previous_positive == current_positive
        and len(previous_indices) == len(set(previous_indices))
        and len(current_indices) == len(set(current_indices))
    )

    def max_abs_delta(field: str) -> float:
        if not rows:
            return 0.0
        return max(
            abs(as_float(curr, field) - as_float(prev, field))
            for prev, curr in rows
        )

    def mean_abs_delta(field: str) -> float:
        if not rows:
            return 0.0
        return mean(
            abs(as_float(curr, field) - as_float(prev, field))
            for prev, curr in rows
        )

    max_growth = max_abs_delta("realized_growth_pct")
    max_inflation = max_abs_delta("headline_inflation_pct")
    max_policy = max_abs_delta("global_policy_rate_pct")
    max_2y = max_abs_delta("global_2y_yield_pct")
    max_10y = max_abs_delta("global_10y_yield_pct")
    max_dollar = max_abs_delta("global_dollar_index")
    max_hy = max_abs_delta("global_high_yield_spread_bps")
    max_oil = max_abs_delta("brent_oil_price_usd")
    convergence_tolerances = {
        "realized_growth_pct": {
            "parameter": "convergence_growth_tolerance_pct",
            "unit": "percentage_point",
            "max_abs_delta": params.convergence_growth_tolerance_pct,
        },
        "headline_inflation_pct": {
            "parameter": "convergence_inflation_tolerance_pct",
            "unit": "percentage_point",
            "max_abs_delta": params.convergence_inflation_tolerance_pct,
        },
        "global_policy_rate_pct": {
            "parameter": "convergence_policy_tolerance_pct",
            "unit": "percentage_point",
            "max_abs_delta": params.convergence_policy_tolerance_pct,
        },
        "global_2y_yield_pct": {
            "parameter": "convergence_2y_tolerance_pct",
            "unit": "percentage_point",
            "max_abs_delta": params.convergence_2y_tolerance_pct,
        },
        "global_10y_yield_pct": {
            "parameter": "convergence_10y_tolerance_pct",
            "unit": "percentage_point",
            "max_abs_delta": params.convergence_10y_tolerance_pct,
        },
        "global_dollar_index": {
            "parameter": "convergence_dollar_tolerance_index",
            "unit": "index_point",
            "max_abs_delta": params.convergence_dollar_tolerance_index,
        },
        "global_high_yield_spread_bps": {
            "parameter": "convergence_hy_tolerance_bps",
            "unit": "basis_point",
            "max_abs_delta": params.convergence_hy_tolerance_bps,
        },
        "brent_oil_price_usd": {
            "parameter": "convergence_oil_tolerance_usd",
            "unit": "usd",
            "max_abs_delta": params.convergence_oil_tolerance_usd,
        },
    }
    max_deltas_by_field = {
        "realized_growth_pct": max_growth,
        "headline_inflation_pct": max_inflation,
        "global_policy_rate_pct": max_policy,
        "global_2y_yield_pct": max_2y,
        "global_10y_yield_pct": max_10y,
        "global_dollar_index": max_dollar,
        "global_high_yield_spread_bps": max_hy,
        "brent_oil_price_usd": max_oil,
    }
    # Composite delta index is diagnostic-only. The per-field tolerances below
    # are the authoritative convergence check.
    delta_index = (
        22.0 * max_growth
        + 18.0 * max_inflation
        + 16.0 * max_policy
        + 10.0 * max_2y
        + 10.0 * max_10y
        + 1.5 * max_dollar
        + max_hy / 8.0
        + max_oil / 6.0
    )
    previous_boundary_hits = count_boundary_hits(previous)
    current_boundary_hits = count_boundary_hits(current)
    return {
        "seed": seed,
        "from_pass": from_pass,
        "to_pass": to_pass,
        "max_growth_delta_pct": round(max_growth, 4),
        "mean_growth_delta_pct": round(mean_abs_delta("realized_growth_pct"), 4),
        "max_inflation_delta_pct": round(max_inflation, 4),
        "mean_inflation_delta_pct": round(mean_abs_delta("headline_inflation_pct"), 4),
        "max_policy_rate_delta_pct": round(max_policy, 4),
        "mean_policy_rate_delta_pct": round(mean_abs_delta("global_policy_rate_pct"), 4),
        "max_2y_yield_delta_pct": round(max_2y, 4),
        "mean_2y_yield_delta_pct": round(mean_abs_delta("global_2y_yield_pct"), 4),
        "max_10y_yield_delta_pct": round(max_10y, 4),
        "mean_10y_yield_delta_pct": round(mean_abs_delta("global_10y_yield_pct"), 4),
        "max_dollar_index_delta": round(max_dollar, 4),
        "mean_dollar_index_delta": round(mean_abs_delta("global_dollar_index"), 4),
        "max_hy_spread_delta_bps": round(max_hy, 4),
        "mean_hy_spread_delta_bps": round(mean_abs_delta("global_high_yield_spread_bps"), 4),
        "max_brent_delta_usd": round(max_oil, 4),
        "mean_brent_delta_usd": round(mean_abs_delta("brent_oil_price_usd"), 4),
        "pass_delta_index": round(delta_index, 4),
        "convergence_tolerance_version": CONVERGENCE_TOLERANCE_VERSION,
        "convergence_tolerances": convergence_tolerances,
        "compared_year_count": len(shared_indices),
        "comparison_complete": comparison_complete,
        "missing_from_previous": sorted(current_positive - previous_positive),
        "missing_from_current": sorted(previous_positive - current_positive),
        "previous_boundary_hits": previous_boundary_hits,
        "current_boundary_hits": current_boundary_hits,
        "pass_converged": comparison_complete
        and all(
            max_deltas_by_field[field] <= float(contract["max_abs_delta"])
            for field, contract in convergence_tolerances.items()
        ),
    }


def attach_fixed_point_verification(
    convergence: dict[str, Any],
    diagnostic: dict[str, Any],
) -> dict[str, Any]:
    """Attach an undamped one-step residual check to a convergence candidate.

    Adjacent deltas are not sufficient when feedback inputs are relaxed: a
    small step can make two paths close even while the feedback mapping remains
    far from its fixed point. The diagnostic compares the candidate output with
    a shadow pass driven by the candidate's fully derived feedback path.
    """
    verified = diagnostic.get("pass_converged") is True
    result = dict(convergence)
    result.update(
        {
            "fixed_point_verification_version": FIXED_POINT_VERIFICATION_VERSION,
            "fixed_point_residual_checked": True,
            "fixed_point_residual_converged": verified,
            "fixed_point_residual_delta_index": float(
                diagnostic.get("pass_delta_index", 0.0)
            ),
            "fixed_point_residual_diagnostic": diagnostic,
        }
    )
    if not verified:
        result["converged"] = False
        result["convergence_reason"] = "fixed_point_residual_not_met"
    return result


def convergence_summary(
    pass_records: list[list[dict[str, Any]]],
    seed: int,
    params: MacroFeedbackParams,
    *,
    min_iterations: int | None = None,
    max_iterations: int | None = None,
    pass_relaxations: list[float] | None = None,
) -> dict[str, Any]:
    """Summarise adjacent-pass convergence under the authoritative contract."""
    effective_min, effective_max = resolve_iteration_bounds(
        params,
        min_iterations=min_iterations,
        max_iterations=max_iterations,
    )

    diagnostics = [
        compare_pass_records(
            seed=seed,
            from_pass=index - 1,
            to_pass=index,
            previous=pass_records[index - 1],
            current=pass_records[index],
            params=params,
        )
        for index in range(1, len(pass_records))
    ]
    if pass_relaxations is not None:
        if len(pass_relaxations) != len(diagnostics):
            raise ValueError("pass_relaxations must match every pairwise diagnostic")
        for index, diagnostic in enumerate(diagnostics):
            diagnostic["feedback_relaxation"] = round(
                float(pass_relaxations[index]),
                8,
            )
    iterations_run = len(pass_records) - 1

    common = {
        "seed": seed,
        "iterations": iterations_run,
        "iterations_run": iterations_run,
        "min_iterations": effective_min,
        "max_iterations": effective_max,
        "convergence_tolerance_version": CONVERGENCE_TOLERANCE_VERSION,
        "feedback_relaxation_strategy": FEEDBACK_RELAXATION_STRATEGY_VERSION,
        "fixed_point_verification_version": FIXED_POINT_VERIFICATION_VERSION,
        "fixed_point_residual_checked": False,
        "fixed_point_residual_converged": False,
        "fixed_point_residual_delta_index": 0.0,
        "fixed_point_residual_diagnostic": None,
        "pass_diagnostics": diagnostics,
    }
    if not diagnostics:
        return {
            **common,
            "converged": False,
            "last_pass_converged": False,
            "consecutive_converged_passes": 0,
            "convergence_reason": "no_passes",
            "delta_bounced": False,
            "last_pass_delta_index": 0.0,
            "max_pass_delta_index": 0.0,
        }

    consecutive_required = max(
        MINIMUM_CONSECUTIVE_CONVERGED_PASSES,
        int(params.convergence_consecutive_passes),
    )
    trailing_converged = [
        bool(diag["pass_converged"])
        for diag in diagnostics[-consecutive_required:]
    ]
    consecutive_converged_passes = 0
    for converged in reversed(trailing_converged):
        if not converged:
            break
        consecutive_converged_passes += 1
    last_pass_converged = bool(diagnostics[-1]["pass_converged"])
    min_iterations_met = iterations_run >= effective_min
    all_required_converged = (
        len(trailing_converged) >= consecutive_required
        and all(trailing_converged)
    )

    if all_required_converged and min_iterations_met:
        convergence_reason = "converged"
    elif not min_iterations_met:
        convergence_reason = "min_iterations_not_met"
    elif iterations_run >= effective_max:
        convergence_reason = "max_iterations_reached"
    else:
        convergence_reason = "not_converged"

    delta_bounced = False
    if len(diagnostics) >= 2:
        delta_bounced = bool(
            float(diagnostics[-1]["pass_delta_index"])
            > float(diagnostics[-2]["pass_delta_index"])
        )

    return {
        **common,
        "converged": bool(all_required_converged and min_iterations_met),
        "last_pass_converged": last_pass_converged,
        "consecutive_converged_passes": consecutive_converged_passes,
        "convergence_reason": convergence_reason,
        "delta_bounced": delta_bounced,
        "last_pass_delta_index": float(diagnostics[-1]["pass_delta_index"]),
        "max_pass_delta_index": max(
            float(item["pass_delta_index"])
            for item in diagnostics
        ),
    }


def resolve_iteration_bounds(
    feedback_params: MacroFeedbackParams,
    *,
    min_iterations: int | None = None,
    max_iterations: int | None = None,
) -> tuple[int, int]:
    """Resolve bounds without weakening the three-pass convergence gate.

    A legacy maximum of zero is normalised to one feedback rerun. If max is
    below the authoritative minimum, the loop still runs exactly max passes and
    reports ``min_iterations_not_met``; it never lowers the contract to fit the
    requested cap.
    """
    effective_min = int(
        min_iterations
        if min_iterations is not None
        else feedback_params.min_feedback_iterations
    )
    effective_max = int(
        max_iterations
        if max_iterations is not None
        else feedback_params.max_feedback_iterations
    )
    if effective_min < 0:
        raise ValueError("min feedback iterations must be non-negative")
    if effective_max < 0:
        raise ValueError("max feedback iterations must be non-negative")
    effective_min = max(MINIMUM_FEEDBACK_ITERATIONS, effective_min)
    effective_max = max(1, effective_max)
    return effective_min, effective_max


def run_convergence_aware_feedback_loop(
    *,
    seed: int,
    feedback_params: MacroFeedbackParams,
    initial_records: list[dict[str, Any]],
    run_pass: Any,
    min_iterations: int | None = None,
    max_iterations: int | None = None,
) -> tuple[list[dict[str, Any]], dict[int, dict[str, Any]], dict[str, Any]]:
    """Run the shared deterministic feedback fixed-point solver.

    Convergence can be reported only after the three-pass minimum gate, two
    consecutive adjacent all-field checks, and an undamped shadow pass proving
    that the candidate path's fixed-point residual also satisfies every field
    tolerance. Final records always come from the last accepted complete model
    pass; the shadow pass is diagnostic-only. A caller may request fewer than
    three reruns for compatibility diagnostics, but such a run cannot be marked
    converged.
    """
    effective_min, effective_max = resolve_iteration_bounds(
        feedback_params,
        min_iterations=min_iterations,
        max_iterations=max_iterations,
    )
    pass_records = [initial_records]
    macro_feedback: dict[int, dict[str, Any]] = {}
    pass_relaxations: list[float] = []
    convergence: dict[str, Any] | None = None

    for iteration in range(effective_max):
        derived = derive_feedback_path(pass_records[-1], feedback_params)
        relaxation = feedback_relaxation_for_iteration(feedback_params, iteration)
        macro_feedback = blend_feedback_paths(
            macro_feedback,
            derived,
            relaxation,
        )
        pass_relaxations.append(relaxation)
        records = run_pass(macro_feedback, iteration)
        pass_records.append(records)
        if iteration + 1 >= effective_min:
            convergence = convergence_summary(
                pass_records,
                seed,
                feedback_params,
                min_iterations=effective_min,
                max_iterations=effective_max,
                pass_relaxations=pass_relaxations,
            )
            if convergence["converged"]:
                verification_feedback = derive_feedback_path(
                    records,
                    feedback_params,
                )
                verification_records = run_pass(
                    verification_feedback,
                    iteration + 1,
                )
                verification_diagnostic = compare_pass_records(
                    seed=seed,
                    from_pass=iteration + 1,
                    to_pass=iteration + 2,
                    previous=records,
                    current=verification_records,
                    params=feedback_params,
                )
                convergence = attach_fixed_point_verification(
                    convergence,
                    verification_diagnostic,
                )
                if convergence["converged"]:
                    break

    if convergence is None:
        convergence = convergence_summary(
            pass_records,
            seed,
            feedback_params,
            min_iterations=effective_min,
            max_iterations=effective_max,
            pass_relaxations=pass_relaxations,
        )
    convergence = dict(convergence)
    convergence["row_convergence_annotations"] = build_row_convergence_annotations(
        pass_records,
        feedback_params,
        min_iterations=effective_min,
        max_iterations=effective_max,
    )
    return pass_records[-1], macro_feedback, convergence


def summarize_seed(records: list[dict[str, Any]]) -> dict[str, Any]:
    data = records[1:] if len(records) > 1 else records
    growth_values = [as_float(row, "realized_growth_pct") for row in data]
    growth_jumps = [
        abs(as_float(curr, "realized_growth_pct") - as_float(prev, "realized_growth_pct"))
        for prev, curr in zip(records, records[1:])
    ]
    hy_values = [as_float(row, "global_high_yield_spread_bps") for row in data]
    equity_returns = [as_float(row, "equity_total_return_pct") for row in data]
    oil_returns = [as_float(row, "oil_yoy_change_pct") for row in data]
    feedback_values = [as_float(row, "macro_feedback_intensity_index") for row in data]
    final = records[-1]
    return {
        "seed": int(final["seed"]),
        "start_year": int(records[0]["year"]),
        "end_year": int(final["year"]),
        "average_growth_pct": round(mean(growth_values), 3) if growth_values else 0.0,
        "growth_std_pct": round(pstdev(growth_values), 3) if len(growth_values) > 1 else 0.0,
        "max_growth_jump_pct": round(max(growth_jumps), 3) if growth_jumps else 0.0,
        "average_hy_spread_bps": round(mean(hy_values), 2) if hy_values else 0.0,
        "average_equity_return_pct": round(mean(equity_returns), 3) if equity_returns else 0.0,
        "average_oil_yoy_change_pct": round(mean(oil_returns), 3) if oil_returns else 0.0,
        "average_feedback_intensity_index": round(mean(feedback_values), 3) if feedback_values else 0.0,
        "macro_feedback_converged": str(final.get("macro_feedback_converged", "false")),
        "macro_feedback_last_pass_delta_index": as_float(final, "macro_feedback_last_pass_delta_index"),
        "final_gdp_trillion_usd": as_float(final, "global_gdp_trillion_usd"),
        "final_regime": str(final.get("regime", "none")),
    }


def write_viewer_data_js(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(rows, ensure_ascii=False, separators=(",", ":"))
    path.write_text(f"window.GLOBAL_MACRO_FEEDBACK_DATA = {payload};\n", encoding="utf-8")


def build_feedback_svg(records_by_seed: dict[int, list[dict[str, Any]]], path: Path) -> None:
    width = 1180
    height = 680
    left = 78
    right = 34
    top = 42
    bottom = 72
    plot_w = width - left - right
    plot_h = height - top - bottom
    all_records = [row for rows in records_by_seed.values() for row in rows]
    years = [int(row["year"]) for row in all_records]
    values = [as_float(row, "global_gdp_trillion_usd") for row in all_records]
    min_year, max_year = min(years), max(years)
    min_value, max_value = min(values) * 0.96, max(values) * 1.04

    def x_of(year: int) -> float:
        return left + (year - min_year) / max(1, max_year - min_year) * plot_w

    def y_of(value: float) -> float:
        return top + (max_value - value) / max(1e-9, max_value - min_value) * plot_h

    palette = ["#60a5fa", "#34d399", "#f97316", "#d946ef", "#a78bfa", "#facc15", "#fb7185", "#14b8a6"]
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#07090d"/>',
        f'<text x="{left}" y="27" font-family="Arial" font-size="20" fill="#f5f7fb">Feedback-Calibrated Global GDP Paths</text>',
        f'<text x="{left}" y="50" font-family="Arial" font-size="12" fill="#94a3b8">Second-pass macro paths with lagged feedback from credit, dollar, assets, oil, policy, and inflation</text>',
    ]
    for i in range(7):
        y = top + i / 6 * plot_h
        value = max_value - i / 6 * (max_value - min_value)
        lines.append(f'<line x1="{left}" y1="{y:.2f}" x2="{left + plot_w}" y2="{y:.2f}" stroke="#1f2937"/>')
        lines.append(f'<text x="{left - 10}" y="{y + 4:.2f}" text-anchor="end" font-family="Arial" font-size="11" fill="#94a3b8">{value:.0f}</text>')
    for i in range(6):
        x = left + i / 5 * plot_w
        year = round(min_year + i / 5 * (max_year - min_year))
        lines.append(f'<line x1="{x:.2f}" y1="{top}" x2="{x:.2f}" y2="{top + plot_h}" stroke="#172033"/>')
        lines.append(f'<text x="{x:.2f}" y="{top + plot_h + 24}" text-anchor="middle" font-family="Arial" font-size="11" fill="#94a3b8">{year}</text>')

    for idx, (seed, records) in enumerate(sorted(records_by_seed.items())):
        color = palette[idx % len(palette)]
        points = " ".join(
            f'{x_of(int(row["year"])):.2f},{y_of(as_float(row, "global_gdp_trillion_usd")):.2f}'
            for row in records
        )
        lines.append(f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round"/>')
        last = records[-1]
        lines.append(
            f'<text x="{x_of(int(last["year"])) + 6:.2f}" y="{y_of(as_float(last, "global_gdp_trillion_usd")) + 4:.2f}" '
            f'font-family="Arial" font-size="11" fill="{color}">seed {seed}</text>'
        )
    lines.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}" stroke="#64748b"/>')
    lines.append(f'<line x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}" stroke="#64748b"/>')
    lines.append("</svg>")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the full global macro stack with one or more lagged feedback calibration passes.",
    )
    parser.add_argument("--years", type=int, default=60, help="Number of simulated years after the initial year.")
    parser.add_argument("--start-year", type=int, default=2025, help="Calendar year for the initial observation.")
    parser.add_argument("--initial-gdp", type=float, default=110.0, help="Initial global GDP in trillion USD.")
    parser.add_argument("--volatility-scale", type=float, default=1.55, help="Scales GDP cycle amplitude and random shocks.")
    parser.add_argument(
        "--feedback-iterations",
        type=int,
        default=16,
        help="Maximum feedback calibration reruns. The loop stops early once the convergence contract is met.",
    )
    parser.add_argument(
        "--min-feedback-iterations",
        type=int,
        default=3,
        help="Minimum feedback passes before the convergence check is applied.",
    )
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
    if args.feedback_iterations < 0:
        raise SystemExit("--feedback-iterations must be non-negative")
    if args.min_feedback_iterations < 0:
        raise SystemExit("--min-feedback-iterations must be non-negative")

    gdp_params = calibrated_gdp_params(args)
    inflation_params = InflationParams(
        headline_anchor_pct=2.45,
        core_anchor_pct=2.30,
        expectation_anchor_pct=2.35,
        headline_persistence=0.62,
        core_persistence=0.78,
        credit_stress_disinflation_beta=0.24,
        crisis_disinflation_beta=0.34,
    )
    policy_params = PolicyRateParams(policy_adjustment_speed=0.34)
    yield_curve_params = YieldCurveParams()
    dollar_liquidity_params = DollarLiquidityParams()
    credit_spread_params = calibrated_credit_params()
    asset_price_params = calibrated_asset_params()
    oil_commodity_params = calibrated_oil_params()
    feedback_params = MacroFeedbackParams(
        feedback_iterations=args.feedback_iterations,
        min_feedback_iterations=args.min_feedback_iterations,
        max_feedback_iterations=max(1, args.feedback_iterations),
    )

    records_by_seed: dict[int, list[dict[str, Any]]] = {}
    convergence_by_seed: dict[int, dict[str, Any]] = {}
    for seed in seeds:
        initial_records = run_full_chain(
            seed,
            gdp_params=gdp_params,
            inflation_params=inflation_params,
            policy_params=policy_params,
            yield_curve_params=yield_curve_params,
            dollar_liquidity_params=dollar_liquidity_params,
            credit_spread_params=credit_spread_params,
            asset_price_params=asset_price_params,
            oil_commodity_params=oil_commodity_params,
        )

        def run_pass(macro_feedback: dict[int, dict[str, Any]], _iteration: int) -> list[dict[str, Any]]:
            return run_full_chain(
                seed,
                gdp_params=gdp_params,
                inflation_params=inflation_params,
                policy_params=policy_params,
                yield_curve_params=yield_curve_params,
                dollar_liquidity_params=dollar_liquidity_params,
                credit_spread_params=credit_spread_params,
                asset_price_params=asset_price_params,
                oil_commodity_params=oil_commodity_params,
                feedback_path=macro_feedback if macro_feedback else None,
            )

        records, feedback_path, convergence = run_convergence_aware_feedback_loop(
            seed=seed,
            feedback_params=feedback_params,
            initial_records=initial_records,
            run_pass=run_pass,
            min_iterations=args.min_feedback_iterations,
            max_iterations=max(1, args.feedback_iterations),
        )
        convergence_by_seed[seed] = convergence
        records_by_seed[seed] = annotate_feedback_records(
            records, feedback_path, args.feedback_iterations, convergence
        )

    all_records = [row for records in records_by_seed.values() for row in records]
    summaries = [summarize_seed(records) for records in records_by_seed.values()]

    args.output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = args.output_dir / "global_macro_feedback_seed_sweep.csv"
    json_path = args.output_dir / "global_macro_feedback_seed_sweep.json"
    viewer_data_path = args.output_dir / "global_macro_feedback_viewer_data.js"
    svg_path = args.output_dir / "global_macro_feedback_curves.svg"

    write_csv(csv_path, all_records, COMBINED_MACRO_FEEDBACK_FIELDS)
    write_json(
        json_path,
        {
            "macro_feedback_param_version": MACRO_FEEDBACK_PARAM_VERSION,
            "macro_feedback_interface_version": MACRO_FEEDBACK_INTERFACE_VERSION,
            "gdp_param_version": GDP_PARAM_VERSION,
            "inflation_param_version": INFLATION_PARAM_VERSION,
            "policy_param_version": POLICY_PARAM_VERSION,
            "yield_curve_param_version": YIELD_CURVE_PARAM_VERSION,
            "dollar_liquidity_param_version": DOLLAR_LIQUIDITY_PARAM_VERSION,
            "credit_spread_param_version": CREDIT_SPREAD_PARAM_VERSION,
            "asset_price_param_version": ASSET_PRICE_PARAM_VERSION,
            "oil_commodity_param_version": OIL_COMMODITY_PARAM_VERSION,
            "gdp_params": asdict(gdp_params),
            "inflation_params": asdict(inflation_params),
            "policy_params": asdict(policy_params),
            "yield_curve_params": asdict(yield_curve_params),
            "dollar_liquidity_params": asdict(dollar_liquidity_params),
            "credit_spread_params": asdict(credit_spread_params),
            "asset_price_params": asdict(asset_price_params),
            "oil_commodity_params": asdict(oil_commodity_params),
            "feedback_params": asdict(feedback_params),
            "seeds": seeds,
            "summary": summaries,
            "convergence": list(convergence_by_seed.values()),
            "model_note": {
                "scope": "This is a feedback-calibrated orchestrator, not a global event detector.",
                "method": "The stack first generates a complete macro path, derives lagged feedback from existing *_impulse fields, then reruns the path with GDP, inflation, and policy feedback inputs for the configured number of passes.",
                "convergence": "Adjacent-pass diagnostics compare growth, headline inflation, policy rate, 2Y yield, 10Y yield, dollar index, HY spread, and Brent oil against the strict versioned tolerances; two consecutive passing diagnostics are required.",
                "solver": "Feedback inputs use a deterministic constant relaxation; convergence additionally requires an undamped fixed-point residual pass, while output rows remain the final accepted complete model pass.",
                "calibration": "GDP smoothing, credit convexity, bank lending sentiment, equity valuation pressure, and oil return smoothing are calibrated to avoid overly jumpy or permanently stressed paths.",
                "future_connection": "A later event layer can classify and inject named global events on top of this feedback scheduler.",
            },
        },
    )
    write_viewer_data_js(viewer_data_path, all_records)
    if not args.no_svg:
        build_feedback_svg(records_by_seed, svg_path)

    print(f"Wrote {csv_path}")
    print(f"Wrote {json_path}")
    print(f"Wrote {viewer_data_path}")
    if not args.no_svg:
        print(f"Wrote {svg_path}")
    for summary in summaries:
        print(
            "seed={seed} avg_growth={average_growth_pct:.2f}% "
            "growth_std={growth_std_pct:.2f} max_jump={max_growth_jump_pct:.2f} "
            "avg_hy={average_hy_spread_bps:.0f} avg_eq={average_equity_return_pct:.2f}% "
            "feedback={average_feedback_intensity_index:.1f}".format(**summary)
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
