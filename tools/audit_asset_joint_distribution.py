from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from collections import Counter
from dataclasses import replace
from pathlib import Path
from typing import Any, Iterable, Sequence

from macro_layers import macro_run_orchestrator_sim as orchestrator
from macro_layers import regional_macro_layer_sim as regional_macro
from macro_layers.global_bond_accounting_v04 import simulate_global_bond_v04_for_macro_path
from macro_layers.global_equity_accounting_v04 import simulate_global_equity_v04_for_macro_path
from macro_layers.global_macro_feedback_calibration_sim import MacroFeedbackParams, run_full_chain


AUDIT_VERSION = "asset-joint-distribution-audit-v1"
DEFAULT_AUDIT_SEEDS = (
    *range(20261001, 20261041),
    *range(20262001, 20262041),
    20260622,
)
REGIME_NAMES = (
    "normal_growth",
    "stagflation",
    "credit_crisis",
    "deflation",
    "energy_shock",
    "high_real_rates",
)
DEMAND_TARGETS = ("total", "business", "leisure", "vfr", "long_haul", "transfer")
DEMAND_FAMILIES = ("asset_market", "household_wealth", "cash_income", "credit_confidence", "fare_cost")
COMMERCIAL_CONTRIBUTIONS = {
    "duty_free": ("base", "traffic_mix", "premium", "culture_currency"),
    "luxury_retail": ("base", "premium", "traffic_mix", "culture"),
    "electronics_retail": ("base", "cash_income", "traffic_mix", "culture_currency"),
    "food_beverage": ("base", "traffic_mix", "fare_cost"),
    "general_retail": ("base", "cash_income", "traffic_mix", "fare_cost"),
}
PE_CONTRIBUTION_FIELDS = (
    "global_equity_pe_rate_contribution",
    "global_equity_pe_credit_contribution",
    "global_equity_pe_fci_contribution",
    "global_equity_pe_policy_contribution",
    "global_equity_pe_dollar_contribution",
    "global_equity_pe_liquidity_contribution",
    "global_equity_pe_risk_appetite_contribution",
    "global_equity_pe_impulse_contribution",
    "global_equity_pe_crisis_contribution",
)
GLOBAL_IDENTITY_FIELDS = (
    "global_equity_price_identity_residual",
    "global_equity_total_return_identity_residual",
    "global_sovereign_bond_total_return_identity_residual",
    "global_corporate_bond_total_return_identity_residual",
    "global_60_40_total_return_identity_residual",
)
REGIONAL_IDENTITY_FIELDS = (
    "regional_equity_eps_growth_raw_identity_residual",
    "regional_equity_eps_growth_final_identity_residual",
    "regional_equity_price_identity_residual",
    "regional_equity_price_return_identity_residual",
    "regional_equity_total_return_identity_residual",
    "regional_sovereign_bond_price_return_identity_residual",
    "regional_sovereign_bond_total_return_identity_residual",
)


class AssetAuditError(RuntimeError):
    pass


def number(row: dict[str, Any], field: str) -> float:
    try:
        value = float(row[field])
    except (KeyError, TypeError, ValueError) as error:
        raise AssetAuditError(f"missing or invalid field: {field}") from error
    if not math.isfinite(value):
        raise AssetAuditError(f"non-finite field: {field}")
    return value


def mean_field(rows: Sequence[dict[str, Any]], field: str) -> float:
    return statistics.fmean(number(row, field) for row in rows) if rows else 0.0


def rounded(value: float, digits: int = 6) -> float:
    return round(float(value), digits)


def percentile(values: Sequence[float], probability: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(float(value) for value in values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def distribution(values: Sequence[float]) -> dict[str, float]:
    return {
        "min": rounded(min(values)) if values else 0.0,
        "p05": rounded(percentile(values, 0.05)),
        "p25": rounded(percentile(values, 0.25)),
        "median": rounded(percentile(values, 0.50)),
        "p75": rounded(percentile(values, 0.75)),
        "p95": rounded(percentile(values, 0.95)),
        "max": rounded(max(values)) if values else 0.0,
        "mean": rounded(statistics.fmean(values)) if values else 0.0,
    }


def annualized_index_return(start: float, end: float, years: int) -> float:
    if start <= 0.0 or end <= 0.0 or years <= 0:
        raise AssetAuditError("annualized index return requires positive indices and years")
    return (pow(end / start, 1.0 / years) - 1.0) * 100.0


def classify_regimes(row: dict[str, Any]) -> tuple[str, ...]:
    growth = number(row, "realized_growth_pct")
    inflation = number(row, "headline_inflation_pct")
    stress = number(row, "financial_stress_index")
    regimes: list[str] = []
    if growth >= 1.5 and 1.0 <= inflation <= 3.5 and stress < 55.0:
        regimes.append("normal_growth")
    if growth < 1.5 and inflation > 3.5:
        regimes.append("stagflation")
    if (
        number(row, "global_high_yield_spread_bps") >= 750.0
        or number(row, "credit_impairment_stock_index") >= 45.0
        or number(row, "crisis_intensity") >= 0.35
    ):
        regimes.append("credit_crisis")
    if inflation < 0.0:
        regimes.append("deflation")
    if (
        number(row, "energy_cost_pressure_index") >= 70.0
        or number(row, "oil_yoy_change_pct") >= 25.0
    ):
        regimes.append("energy_shock")
    if (
        number(row, "global_real_10y_yield_pct") >= 1.75
        or number(row, "global_policy_rate_pct") >= 5.0
    ):
        regimes.append("high_real_rates")
    return tuple(regimes)


def longest_true_run(flags: Sequence[bool], labels: Sequence[int]) -> dict[str, int]:
    best_length = 0
    best_start = 0
    best_end = 0
    current_length = 0
    current_start = 0
    for flag, label in zip(flags, labels, strict=True):
        if flag:
            if current_length == 0:
                current_start = label
            current_length += 1
            if current_length > best_length:
                best_length = current_length
                best_start = current_start
                best_end = label
        else:
            current_length = 0
    return {"years": best_length, "start_year": best_start, "end_year": best_end}


def max_abs_field(rows: Iterable[dict[str, Any]], fields: Sequence[str]) -> float:
    maximum = 0.0
    for row in rows:
        for field in fields:
            maximum = max(maximum, abs(number(row, field)))
    return maximum


def global_seed_summary(
    seed: int,
    rows: Sequence[dict[str, Any]],
    *,
    late_start_year_index: int,
) -> dict[str, Any]:
    if len(rows) < 2:
        raise AssetAuditError("global audit requires at least two rows")
    transition = list(rows[1:])
    late = [row for row in transition if int(number(row, "year_index")) >= late_start_year_index]
    if not late:
        raise AssetAuditError("late horizon contains no rows")
    trailing = transition[-min(10, len(transition)) :]
    outperform = [
        number(row, "global_sovereign_bond_total_return_pct")
        > number(row, "global_equity_total_return_pct")
        for row in transition
    ]
    regime_year_counts = Counter(
        regime for row in transition for regime in classify_regimes(row)
    )
    pe_start = number(late[0], "global_equity_valuation_pe")
    pe_end = number(late[-1], "global_equity_valuation_pe")
    identity_max = max_abs_field(rows, GLOBAL_IDENTITY_FIELDS)
    boundary_counts = {
        "equity_eps": sum(
            str(row["global_equity_eps_boundary_state"]) != "none" for row in rows
        ),
        "equity_pe": sum(
            str(row["global_equity_pe_boundary_state"]) != "none" for row in rows
        ),
        "corporate_default_probability": sum(
            str(row["global_corporate_bond_default_probability_boundary_state"])
            != "none"
            for row in rows
        ),
    }
    result = {
        "seed": seed,
        "years": len(rows) - 1,
        "terminal_equity_price_index": number(rows[-1], "global_equity_price_index"),
        "terminal_equity_total_return_index": number(rows[-1], "global_equity_total_return_index"),
        "terminal_sovereign_bond_total_return_index": number(rows[-1], "global_sovereign_bond_total_return_index"),
        "terminal_corporate_bond_total_return_index": number(rows[-1], "global_corporate_bond_total_return_index"),
        "terminal_60_40_total_return_index": number(rows[-1], "global_60_40_total_return_index"),
        "equity_total_return_cagr_pct": annualized_index_return(
            number(rows[0], "global_equity_total_return_index"),
            number(rows[-1], "global_equity_total_return_index"),
            len(rows) - 1,
        ),
        "sovereign_bond_total_return_cagr_pct": annualized_index_return(
            number(rows[0], "global_sovereign_bond_total_return_index"),
            number(rows[-1], "global_sovereign_bond_total_return_index"),
            len(rows) - 1,
        ),
        "equity_total_return_avg_pct": mean_field(transition, "global_equity_total_return_pct"),
        "sovereign_bond_total_return_avg_pct": mean_field(transition, "global_sovereign_bond_total_return_pct"),
        "late_equity_price_return_avg_pct": mean_field(late, "global_equity_price_return_pct"),
        "late_equity_dividend_yield_avg_pct": mean_field(late, "global_equity_dividend_yield_pct"),
        "late_equity_total_return_avg_pct": mean_field(late, "global_equity_total_return_pct"),
        "late_sovereign_bond_total_return_avg_pct": mean_field(late, "global_sovereign_bond_total_return_pct"),
        "late_equity_minus_bond_avg_pp": (
            mean_field(late, "global_equity_total_return_pct")
            - mean_field(late, "global_sovereign_bond_total_return_pct")
        ),
        "trailing_10_equity_total_return_avg_pct": mean_field(trailing, "global_equity_total_return_pct"),
        "trailing_10_bond_total_return_avg_pct": mean_field(trailing, "global_sovereign_bond_total_return_pct"),
        "trailing_10_equity_minus_bond_avg_pp": (
            mean_field(trailing, "global_equity_total_return_pct")
            - mean_field(trailing, "global_sovereign_bond_total_return_pct")
        ),
        "late_eps_growth_avg_pct": mean_field(late, "global_equity_eps_growth_pct"),
        "late_pe_start": pe_start,
        "late_pe_end": pe_end,
        "late_pe_change_pct": (pe_end / pe_start - 1.0) * 100.0,
        "late_real_10y_yield_avg_pct": mean_field(late, "global_real_10y_yield_pct"),
        "late_sovereign_bond_carry_avg_pct": mean_field(late, "global_sovereign_bond_carry_pct"),
        "bond_outperform_year_count": sum(outperform),
        "longest_bond_outperformance_run": longest_true_run(
            outperform,
            [int(number(row, "year")) for row in transition],
        ),
        "global_identity_max_abs_residual": identity_max,
        "global_boundary_counts": boundary_counts,
        "minimum_equity_pe": min(
            number(row, "global_equity_valuation_pe") for row in rows
        ),
        "maximum_equity_pe": max(
            number(row, "global_equity_valuation_pe") for row in rows
        ),
        "maximum_equity_drawdown_pct": min(
            number(row, "global_equity_drawdown_pct") for row in rows
        ),
        "regime_year_counts": {name: regime_year_counts[name] for name in REGIME_NAMES},
        "late_pe_contribution_means": {
            field.removeprefix("global_equity_pe_").removesuffix("_contribution"): mean_field(late, field)
            for field in PE_CONTRIBUTION_FIELDS
        },
    }
    return _round_nested(result)


def _round_nested(value: Any) -> Any:
    if isinstance(value, float):
        return rounded(value)
    if isinstance(value, dict):
        return {key: _round_nested(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_round_nested(item) for item in value]
    return value


def regional_aviation_summary(
    result: dict[str, Any],
    global_rows: Sequence[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    regional_rows = [
        row
        for rows in result["regional_rows_by_region"].values()
        for row in rows
    ]
    aviation_rows = [
        row
        for rows in result["aviation_rows_by_region"].values()
        for row in rows
    ]
    if not regional_rows or not aviation_rows:
        raise AssetAuditError("regional and aviation rows are required")
    demand_reconstruction_max = 0.0
    commercial_reconstruction_max = 0.0
    for row in aviation_rows:
        for target in DEMAND_TARGETS:
            raw = number(row, f"demand_{target}_base_contribution_pp") + sum(
                number(row, f"demand_{target}_{family}_contribution_pp")
                for family in DEMAND_FAMILIES
            )
            demand_reconstruction_max = max(
                demand_reconstruction_max,
                abs(raw - number(row, f"demand_{target}_raw_growth_pct")),
                abs(
                    number(row, f"demand_{target}_raw_growth_pct")
                    + number(row, f"demand_{target}_boundary_adjustment_pp")
                    + number(row, f"demand_{target}_smoothing_adjustment_pp")
                    - number(row, f"demand_{target}_final_growth_pct")
                ),
            )
        premium_raw = 100.0 + sum(
            number(row, f"premium_propensity_{name}_contribution_points")
            for name in ("asset_market", "household_wealth", "cash_income", "traffic_mix")
        )
        commercial_reconstruction_max = max(
            commercial_reconstruction_max,
            abs(premium_raw - number(row, "premium_propensity_raw_index")),
        )
        for segment, names in COMMERCIAL_CONTRIBUTIONS.items():
            raw = sum(
                number(row, f"{segment}_propensity_{name}_contribution_points")
                for name in names
            )
            commercial_reconstruction_max = max(
                commercial_reconstruction_max,
                abs(raw - number(row, f"{segment}_propensity_raw_index")),
            )
    transition_regional = [row for row in regional_rows if int(number(row, "year_index")) > 0]
    transition_aviation = [row for row in aviation_rows if int(number(row, "year_index")) > 0]
    regional_boundary_counts = {
        "equity_eps": sum(
            str(row["regional_equity_eps_boundary_state"]) != "none"
            for row in regional_rows
        ),
        "equity_pe": sum(
            str(row["regional_equity_pe_boundary_state"]) != "none"
            for row in regional_rows
        ),
    }
    direction_metrics: dict[str, float] = {}
    if global_rows is not None:
        global_by_year = {
            int(number(row, "year_index")): row for row in global_rows
        }
        equity_pairs = [
            (
                number(global_by_year[int(number(row, "year_index"))], "global_equity_price_return_pct"),
                number(row, "regional_equity_price_return_pct"),
            )
            for row in transition_regional
        ]
        bond_pairs = [
            (
                number(global_by_year[int(number(row, "year_index"))], "global_sovereign_bond_total_return_pct"),
                number(row, "regional_sovereign_bond_total_return_pct"),
            )
            for row in transition_regional
        ]

        def direction_share(pairs: Sequence[tuple[float, float]]) -> float:
            material = [pair for pair in pairs if abs(pair[0]) >= 0.25 and abs(pair[1]) >= 0.25]
            if not material:
                return 100.0
            return 100.0 * sum(left * right > 0.0 for left, right in material) / len(material)

        direction_metrics = {
            "equity_global_regional_same_direction_pct": direction_share(equity_pairs),
            "bond_global_regional_same_direction_pct": direction_share(bond_pairs),
            "equity_global_regional_mean_abs_gap_pp": statistics.fmean(
                abs(left - right) for left, right in equity_pairs
            ),
            "bond_global_regional_mean_abs_gap_pp": statistics.fmean(
                abs(left - right) for left, right in bond_pairs
            ),
        }
    return _round_nested(
        {
            "region_count": len(result["regional_rows_by_region"]),
            "regional_row_count": len(regional_rows),
            "aviation_row_count": len(aviation_rows),
            "regional_identity_max_abs_residual": max_abs_field(
                regional_rows, REGIONAL_IDENTITY_FIELDS
            ),
            "demand_reconstruction_max_abs_error": demand_reconstruction_max,
            "commercial_reconstruction_max_abs_error": commercial_reconstruction_max,
            "regional_boundary_counts": regional_boundary_counts,
            "wealth_impulse_min": min(
                number(row, "regional_household_wealth_consumption_impulse")
                for row in transition_regional
            ),
            "wealth_impulse_max": max(
                number(row, "regional_household_wealth_consumption_impulse")
                for row in transition_regional
            ),
            "real_household_wealth_growth_avg_pct": mean_field(
                transition_regional, "regional_real_household_wealth_growth_pct"
            ),
            "air_demand_growth_avg_pct": mean_field(
                transition_aviation, "regional_air_demand_growth_pct"
            ),
            "premium_propensity_min": min(
                number(row, "premium_propensity_final_index") for row in aviation_rows
            ),
            "premium_propensity_max": max(
                number(row, "premium_propensity_final_index") for row in aviation_rows
            ),
            **direction_metrics,
        }
    )


def diagnose_named_seed(summary: dict[str, Any]) -> dict[str, Any]:
    eps_positive = summary["late_eps_growth_avg_pct"] > 0.0
    pe_compression = summary["late_pe_change_pct"] < -20.0
    trailing_underperformance = summary["trailing_10_equity_minus_bond_avg_pp"] < 0.0
    if eps_positive and pe_compression and trailing_underperformance:
        classification = "valuation_compression_with_positive_earnings_and_high_bond_carry"
    elif summary["late_eps_growth_avg_pct"] <= 0.0:
        classification = "earnings_weakness"
    elif pe_compression:
        classification = "valuation_compression"
    else:
        classification = "mixed_or_normal_relative_return_variation"
    contributions = summary["late_pe_contribution_means"]
    negative_drivers = sorted(
        (
            {"driver": name, "mean_pe_points": value}
            for name, value in contributions.items()
            if value < 0.0
        ),
        key=lambda item: item["mean_pe_points"],
    )
    return {
        "seed": summary["seed"],
        "classification": classification,
        "economically_plausible": bool(eps_positive and pe_compression),
        "late_eps_growth_avg_pct": summary["late_eps_growth_avg_pct"],
        "late_pe_start": summary["late_pe_start"],
        "late_pe_end": summary["late_pe_end"],
        "late_pe_change_pct": summary["late_pe_change_pct"],
        "late_equity_total_return_avg_pct": summary["late_equity_total_return_avg_pct"],
        "late_bond_total_return_avg_pct": summary["late_sovereign_bond_total_return_avg_pct"],
        "trailing_10_equity_minus_bond_avg_pp": summary["trailing_10_equity_minus_bond_avg_pp"],
        "late_real_10y_yield_avg_pct": summary["late_real_10y_yield_avg_pct"],
        "late_bond_carry_avg_pct": summary["late_sovereign_bond_carry_avg_pct"],
        "longest_bond_outperformance_run": summary["longest_bond_outperformance_run"],
        "negative_pe_drivers": negative_drivers,
    }


def aggregate_report(
    seed_summaries: Sequence[dict[str, Any]],
    controlled_worlds: Sequence[dict[str, Any]] = (),
) -> dict[str, Any]:
    metric_names = (
        "equity_total_return_cagr_pct",
        "sovereign_bond_total_return_cagr_pct",
        "terminal_equity_total_return_index",
        "terminal_sovereign_bond_total_return_index",
        "terminal_60_40_total_return_index",
        "late_equity_minus_bond_avg_pp",
        "trailing_10_equity_minus_bond_avg_pp",
        "late_pe_change_pct",
        "late_real_10y_yield_avg_pct",
    )
    regime_year_counts = Counter()
    regime_seed_counts = Counter()
    for summary in seed_summaries:
        for name, count in summary["regime_year_counts"].items():
            regime_year_counts[name] += int(count)
            if count:
                regime_seed_counts[name] += 1
    controlled_regime_counts = Counter(
        regime
        for world in controlled_worlds
        for regime, count in world["global"]["regime_year_counts"].items()
        if count
    )
    regional_max = max(
        (summary["regional_aviation"]["regional_identity_max_abs_residual"] for summary in seed_summaries),
        default=0.0,
    )
    demand_max = max(
        (summary["regional_aviation"]["demand_reconstruction_max_abs_error"] for summary in seed_summaries),
        default=0.0,
    )
    commercial_max = max(
        (summary["regional_aviation"]["commercial_reconstruction_max_abs_error"] for summary in seed_summaries),
        default=0.0,
    )
    regional_metric_names = (
        "real_household_wealth_growth_avg_pct",
        "air_demand_growth_avg_pct",
        "wealth_impulse_min",
        "wealth_impulse_max",
        "premium_propensity_min",
        "premium_propensity_max",
        "equity_global_regional_same_direction_pct",
        "bond_global_regional_same_direction_pct",
        "equity_global_regional_mean_abs_gap_pp",
        "bond_global_regional_mean_abs_gap_pp",
    )
    return {
        "seed_count": len(seed_summaries),
        "controlled_world_count": len(controlled_worlds),
        "metric_distributions": {
            name: distribution([float(summary[name]) for summary in seed_summaries])
            for name in metric_names
        },
        "regional_aviation_distributions": {
            name: distribution(
                [float(summary["regional_aviation"][name]) for summary in seed_summaries]
            )
            for name in regional_metric_names
        },
        "late_equity_underperforms_bond_seed_count": sum(
            summary["late_equity_minus_bond_avg_pp"] < 0.0 for summary in seed_summaries
        ),
        "trailing_10_equity_underperforms_bond_seed_count": sum(
            summary["trailing_10_equity_minus_bond_avg_pp"] < 0.0 for summary in seed_summaries
        ),
        "terminal_equity_below_bond_seed_count": sum(
            summary["terminal_equity_total_return_index"]
            < summary["terminal_sovereign_bond_total_return_index"]
            for summary in seed_summaries
        ),
        "global_identity_max_abs_residual": max(
            summary["global_identity_max_abs_residual"] for summary in seed_summaries
        ),
        "regional_identity_max_abs_residual": regional_max,
        "demand_reconstruction_max_abs_error": demand_max,
        "commercial_reconstruction_max_abs_error": commercial_max,
        "global_equity_pe_boundary_seed_count": sum(
            summary["global_boundary_counts"]["equity_pe"] > 0
            for summary in seed_summaries
        ),
        "regional_equity_pe_boundary_seed_count": sum(
            summary["regional_aviation"]["regional_boundary_counts"]["equity_pe"] > 0
            for summary in seed_summaries
        ),
        "regime_coverage": {
            name: {
                "year_count": regime_year_counts[name],
                "seed_count": regime_seed_counts[name],
                "controlled_world_count": controlled_regime_counts[name],
            }
            for name in REGIME_NAMES
        },
        "all_required_regimes_observed": all(
            regime_year_counts[name] > 0 or controlled_regime_counts[name] > 0
            for name in REGIME_NAMES
        ),
    }


def calibration_decision(aggregate: dict[str, Any]) -> dict[str, Any]:
    seed_count = int(aggregate["seed_count"])
    triggers: list[str] = []
    if aggregate["terminal_equity_below_bond_seed_count"] >= math.ceil(seed_count * 0.20):
        triggers.append("terminal_equity_underperformance_is_systemic")
    if aggregate["late_equity_underperforms_bond_seed_count"] >= math.ceil(seed_count * 0.30):
        triggers.append("late_horizon_equity_underperformance_is_systemic")
    if aggregate["global_equity_pe_boundary_seed_count"] >= math.ceil(seed_count * 0.20):
        triggers.append("global_pe_boundary_is_systemic")
    if aggregate["global_identity_max_abs_residual"] > 0.001:
        triggers.append("global_accounting_identity_failure")
    if aggregate["regional_identity_max_abs_residual"] > 0.001:
        triggers.append("regional_accounting_identity_failure")
    if aggregate["demand_reconstruction_max_abs_error"] > 0.001:
        triggers.append("aviation_demand_reconstruction_failure")
    return {
        "decision": "calibration_review_required" if triggers else "no_parameter_change_supported",
        "triggered_criteria": triggers,
        "policy": (
            "Do not tune to a single Seed; require a systemic distribution, boundary, "
            "or accounting failure before changing parameters."
        ),
    }


def run_controlled_deflation_world(
    *,
    years: int,
    late_start_year_index: int,
) -> dict[str, Any]:
    """Run an explicit low-anchor deflation counterexample.

    This is deliberately separate from the baseline Seed distribution: it changes
    versioned inflation parameters to create a controlled economic world and does
    not masquerade as a naturally sampled production Seed.
    """

    seed = 20269901
    args = argparse.Namespace(
        years=years,
        start_year=2025,
        initial_gdp=100.0,
        volatility_scale=1.0,
        feedback_iterations=1,
        min_feedback_iterations=1,
    )
    params = regional_macro.build_global_params(args)
    inflation_params = replace(
        params["inflation_params"],
        initial_headline_pct=0.2,
        initial_core_pct=0.1,
        initial_expectation_pct=0.2,
        initial_wage_pressure_pct=0.3,
        headline_anchor_pct=0.0,
        core_anchor_pct=0.0,
        expectation_anchor_pct=0.0,
        credit_stress_disinflation_beta=0.5,
        crisis_disinflation_beta=0.7,
    )
    legacy_rows = run_full_chain(
        seed,
        gdp_params=params["gdp_params"],
        inflation_params=inflation_params,
        policy_params=params["policy_params"],
        yield_curve_params=params["yield_curve_params"],
        dollar_liquidity_params=params["dollar_liquidity_params"],
        credit_spread_params=params["credit_spread_params"],
        asset_price_params=params["asset_price_params"],
        oil_commodity_params=params["oil_commodity_params"],
    )
    global_rows = simulate_global_bond_v04_for_macro_path(
        simulate_global_equity_v04_for_macro_path(legacy_rows)
    )
    regional_result = orchestrator.run_regional_and_reconciliation(
        seed,
        global_rows,
        include_downstream=False,
    )
    global_summary = global_seed_summary(
        seed,
        global_rows,
        late_start_year_index=late_start_year_index,
    )
    if global_summary["regime_year_counts"]["deflation"] <= 0:
        raise AssetAuditError("controlled deflation world did not produce deflation")
    return {
        "world_id": "controlled_low_anchor_deflation",
        "authority": "controlled_parameter_counterexample_not_baseline_seed",
        "seed": seed,
        "parameter_overrides": {
            "initial_headline_pct": 0.2,
            "headline_anchor_pct": 0.0,
            "core_anchor_pct": 0.0,
            "expectation_anchor_pct": 0.0,
            "credit_stress_disinflation_beta": 0.5,
            "crisis_disinflation_beta": 0.7,
        },
        "global": global_summary,
        "regional_aviation": regional_aviation_summary(regional_result, global_rows),
    }


def run_audit(
    seeds: Sequence[int],
    *,
    years: int = 60,
    late_start_year_index: int = 40,
    named_seed: int = 20260622,
    include_controlled_worlds: bool = True,
    progress: bool = False,
) -> dict[str, Any]:
    if not seeds:
        raise AssetAuditError("at least one seed is required")
    if years < 1:
        raise AssetAuditError("years must be positive")
    if not 1 <= late_start_year_index <= years:
        raise AssetAuditError("late_start_year_index must fall within the horizon")
    defaults = MacroFeedbackParams()
    args = argparse.Namespace(
        years=years,
        start_year=2025,
        initial_gdp=100.0,
        volatility_scale=1.0,
        feedback_iterations=defaults.max_feedback_iterations,
        min_feedback_iterations=defaults.min_feedback_iterations,
    )
    summaries: list[dict[str, Any]] = []
    for position, seed in enumerate(seeds, start=1):
        if progress:
            print(f"[asset-audit] seed {position}/{len(seeds)}: {seed}", flush=True)
        global_result = orchestrator.run_global_variant(seed, args, "baseline")
        if not global_result["convergence"]["converged"]:
            raise AssetAuditError(f"global feedback did not converge for seed {seed}")
        regional_result = orchestrator.run_regional_and_reconciliation(
            seed,
            global_result["rows"],
            include_downstream=False,
        )
        summary = global_seed_summary(
            seed,
            global_result["rows"],
            late_start_year_index=late_start_year_index,
        )
        summary["regional_aviation"] = regional_aviation_summary(
            regional_result, global_result["rows"]
        )
        summaries.append(summary)
    controlled_worlds = (
        [
            run_controlled_deflation_world(
                years=years,
                late_start_year_index=late_start_year_index,
            )
        ]
        if include_controlled_worlds and years >= 40
        else []
    )
    aggregate = aggregate_report(summaries, controlled_worlds)
    named = next((summary for summary in summaries if summary["seed"] == named_seed), None)
    return {
        "audit_version": AUDIT_VERSION,
        "model_version": orchestrator.MODEL_VERSION,
        "output_schema_version": orchestrator.OUTPUT_SCHEMA_VERSION,
        "years": years,
        "late_start_year_index": late_start_year_index,
        "seed_count": len(summaries),
        "seeds": [int(seed) for seed in seeds],
        "aggregate": _round_nested(aggregate),
        "calibration_decision": calibration_decision(aggregate),
        "controlled_worlds": controlled_worlds,
        "named_seed_diagnosis": diagnose_named_seed(named) if named else None,
        "seed_summaries": summaries,
    }


def write_reports(report: dict[str, Any], output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "asset_joint_distribution_audit.json"
    csv_path = output_dir / "asset_joint_distribution_seed_summary.csv"
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    rows = report["seed_summaries"]
    fieldnames = (
        "seed",
        "years",
        "equity_total_return_cagr_pct",
        "sovereign_bond_total_return_cagr_pct",
        "terminal_equity_total_return_index",
        "terminal_sovereign_bond_total_return_index",
        "terminal_60_40_total_return_index",
        "late_equity_total_return_avg_pct",
        "late_sovereign_bond_total_return_avg_pct",
        "late_equity_minus_bond_avg_pp",
        "trailing_10_equity_minus_bond_avg_pp",
        "late_eps_growth_avg_pct",
        "late_pe_start",
        "late_pe_end",
        "late_pe_change_pct",
        "late_real_10y_yield_avg_pct",
        "late_sovereign_bond_carry_avg_pct",
        "bond_outperform_year_count",
        "global_identity_max_abs_residual",
    )
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows({field: row[field] for field in fieldnames} for row in rows)
    return json_path, csv_path


def parse_seeds(value: str) -> tuple[int, ...]:
    seeds = tuple(int(item.strip()) for item in value.split(",") if item.strip())
    if len(seeds) != len(set(seeds)):
        raise argparse.ArgumentTypeError("seeds must be unique")
    return seeds


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit long-horizon asset, wealth, aviation and commercial distributions.")
    parser.add_argument("--seeds", type=parse_seeds, default=DEFAULT_AUDIT_SEEDS)
    parser.add_argument("--years", type=int, default=60)
    parser.add_argument("--late-start-year-index", type=int, default=40)
    parser.add_argument("--named-seed", type=int, default=20260622)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output") / "audits" / "asset_a4",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = run_audit(
        args.seeds,
        years=args.years,
        late_start_year_index=args.late_start_year_index,
        named_seed=args.named_seed,
        progress=True,
    )
    json_path, csv_path = write_reports(report, args.output_dir)
    print(f"[asset-audit] json: {json_path}")
    print(f"[asset-audit] csv: {csv_path}")
    print(json.dumps(report["aggregate"], ensure_ascii=False, indent=2))
    print(json.dumps(report["calibration_decision"], ensure_ascii=False, indent=2))
    if report["named_seed_diagnosis"]:
        print(json.dumps(report["named_seed_diagnosis"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
