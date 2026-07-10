from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean, pstdev
from typing import Any, Iterable, Mapping

from global_asset_price_layer_sim import ASSET_PRICE_PARAM_VERSION, AssetPriceParams, simulate_asset_prices_for_credit_path
from global_credit_spread_layer_sim import CREDIT_SPREAD_PARAM_VERSION, CreditSpreadParams, simulate_credit_spreads_for_dollar_path
from global_dollar_liquidity_layer_sim import DOLLAR_LIQUIDITY_PARAM_VERSION, DollarLiquidityParams, simulate_dollar_liquidity_for_yield_path
from global_gdp_annual_sim import GDPParams, PARAM_VERSION as GDP_PARAM_VERSION, simulate_global_gdp
from global_inflation_annual_sim import INFLATION_PARAM_VERSION, InflationParams, as_float, simulate_inflation_for_gdp_path
from global_oil_commodity_layer_sim import (
    COMBINED_OIL_COMMODITY_FIELDS,
    OIL_COMMODITY_PARAM_VERSION,
    OilCommodityParams,
    simulate_oil_commodities_for_asset_path,
)
from global_policy_rate_layer_sim import POLICY_PARAM_VERSION, PolicyRateParams, simulate_policy_for_macro_path
from global_yield_curve_layer_sim import YIELD_CURVE_PARAM_VERSION, YieldCurveParams, simulate_yield_curve_for_policy_path


MACRO_FEEDBACK_PARAM_VERSION = "global-macro-feedback-calibration-v0.1"
MACRO_FEEDBACK_INTERFACE_VERSION = "macro-feedback-interface-v0.1"


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
    "macro_feedback_converged",
    "macro_feedback_last_pass_delta_index",
    "macro_feedback_max_pass_delta_index",
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
    feedback_iterations: int = 3
    feedback_iteration_relaxation: float = 0.25
    feedback_smoothing: float = 0.42
    stress_smoothing: float = 0.38
    inflation_smoothing: float = 0.40
    policy_smoothing: float = 0.36
    max_growth_drag_pct: float = -1.15
    max_growth_support_pct: float = 0.85
    max_output_gap_drag_pct: float = -2.20
    max_output_gap_support_pct: float = 1.40
    max_stress_easing: float = -8.0
    max_stress_tightening: float = 16.0
    max_inflation_drag_pct: float = -1.00
    max_inflation_push_pct: float = 1.35
    max_policy_easing_pct: float = -1.00
    max_policy_tightening_pct: float = 1.25
    convergence_growth_tolerance_pct: float = 0.65
    convergence_inflation_tolerance_pct: float = 0.75
    convergence_policy_tolerance_pct: float = 1.15
    convergence_hy_tolerance_bps: float = 300.0
    convergence_oil_tolerance_usd: float = 135.0
    convergence_delta_index_tolerance: float = 75.0


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def smooth(old: float, target: float, speed: float) -> float:
    return old * (1.0 - speed) + target * speed


def round_record(record: dict[str, Any]) -> dict[str, Any]:
    result = dict(record)
    for key, value in list(result.items()):
        if isinstance(value, float):
            result[key] = round(value, 4)
    return result


def calibrated_gdp_params(args: argparse.Namespace) -> GDPParams:
    return GDPParams(
        years=args.years,
        start_year=args.start_year,
        initial_gdp_trillion_usd=args.initial_gdp,
        volatility_scale=args.volatility_scale,
        output_gap_adjustment_speed=0.34,
        growth_adjustment_speed=0.50,
        max_growth_step_pct=2.05,
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

        output_gap_applied = clamp(
            0.72 * growth_applied
            - 0.018 * max(0.0, hy_spread - 650.0)
            - 0.014 * max(0.0, 45.0 - as_float(row, "bank_lending_sentiment_index", 55.0))
            - 0.006 * credit_impairment
            + 0.020 * (as_float(row, "risk_appetite_index", 50.0) - 50.0),
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

        intensity = clamp(
            24.0 * abs(growth_applied)
            + 2.0 * max(0.0, stress_applied)
            + 18.0 * abs(inflation_applied)
            + 18.0 * abs(policy_applied),
            0.0,
            100.0,
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
    if not previous:
        return {key: dict(value) for key, value in current.items()}

    blended: dict[int, dict[str, Any]] = {}
    keys = set(previous) | set(current)
    numeric_fields = {
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
    }
    for key in keys:
        old = previous.get(key, {})
        new = current.get(key, {})
        row: dict[str, Any] = {}
        for field in numeric_fields:
            old_value = as_float(old, field)
            new_value = as_float(new, field)
            row[field] = old_value * (1.0 - relaxation) + new_value * relaxation
        row["feedback_source"] = str(new.get("feedback_source") or old.get("feedback_source") or "lagged_macro_feedback")
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


def annotate_feedback_records(
    records: list[dict[str, Any]],
    feedback_path: Mapping[int, Mapping[str, Any]],
    iteration: int,
    convergence: Mapping[str, Any],
) -> list[dict[str, Any]]:
    annotated: list[dict[str, Any]] = []
    for row in records:
        feedback = feedback_path.get(int(row["year_index"]), {})
        note = "none" if not feedback else str(feedback.get("feedback_source", "lagged_macro_feedback"))
        annotated.append(
            round_record(
                {
                    **row,
                    "macro_feedback_param_version": MACRO_FEEDBACK_PARAM_VERSION,
                    "macro_feedback_interface_version": MACRO_FEEDBACK_INTERFACE_VERSION,
                    "macro_feedback_iteration": iteration,
                    "macro_feedback_intensity_index": as_float(feedback, "macro_feedback_intensity_index"),
                    "macro_feedback_growth_raw_pct": as_float(feedback, "macro_feedback_growth_raw_pct"),
                    "macro_feedback_stress_raw": as_float(feedback, "macro_feedback_stress_raw"),
                    "macro_feedback_inflation_raw_pct": as_float(feedback, "macro_feedback_inflation_raw_pct"),
                    "macro_feedback_policy_raw_pct": as_float(feedback, "macro_feedback_policy_raw_pct"),
                    "macro_feedback_iterations_requested": iteration,
                    "macro_feedback_converged": str(convergence.get("converged", False)).lower(),
                    "macro_feedback_last_pass_delta_index": as_float(convergence, "last_pass_delta_index"),
                    "macro_feedback_max_pass_delta_index": as_float(convergence, "max_pass_delta_index"),
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
    previous_by_index = {int(row["year_index"]): row for row in previous}
    current_by_index = {int(row["year_index"]): row for row in current}
    shared_indices = sorted(set(previous_by_index) & set(current_by_index))
    rows = [
        (previous_by_index[index], current_by_index[index])
        for index in shared_indices
        if index > 0
    ]

    def max_abs_delta(field: str) -> float:
        if not rows:
            return 0.0
        return max(abs(as_float(curr, field) - as_float(prev, field)) for prev, curr in rows)

    def mean_abs_delta(field: str) -> float:
        if not rows:
            return 0.0
        return mean(abs(as_float(curr, field) - as_float(prev, field)) for prev, curr in rows)

    max_growth = max_abs_delta("realized_growth_pct")
    max_inflation = max_abs_delta("headline_inflation_pct")
    max_policy = max_abs_delta("global_policy_rate_pct")
    max_hy = max_abs_delta("global_high_yield_spread_bps")
    max_oil = max_abs_delta("brent_oil_price_usd")
    delta_index = (
        22.0 * max_growth
        + 18.0 * max_inflation
        + 16.0 * max_policy
        + max_hy / 8.0
        + max_oil / 6.0
    )
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
        "max_hy_spread_delta_bps": round(max_hy, 4),
        "mean_hy_spread_delta_bps": round(mean_abs_delta("global_high_yield_spread_bps"), 4),
        "max_brent_delta_usd": round(max_oil, 4),
        "mean_brent_delta_usd": round(mean_abs_delta("brent_oil_price_usd"), 4),
        "pass_delta_index": round(delta_index, 4),
        "pass_converged": (
            delta_index <= params.convergence_delta_index_tolerance
            and max_growth <= params.convergence_growth_tolerance_pct
            and max_inflation <= params.convergence_inflation_tolerance_pct
            and max_policy <= params.convergence_policy_tolerance_pct
            and max_hy <= params.convergence_hy_tolerance_bps
            and max_oil <= params.convergence_oil_tolerance_usd
        ),
    }


def convergence_summary(pass_records: list[list[dict[str, Any]]], seed: int, params: MacroFeedbackParams) -> dict[str, Any]:
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
    last = diagnostics[-1] if diagnostics else {
        "pass_delta_index": 0.0,
        "pass_converged": True,
    }
    return {
        "seed": seed,
        "iterations": len(pass_records) - 1,
        "converged": bool(last["pass_converged"]),
        "last_pass_delta_index": float(last["pass_delta_index"]),
        "max_pass_delta_index": max((float(item["pass_delta_index"]) for item in diagnostics), default=0.0),
        "pass_diagnostics": diagnostics,
    }


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


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


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
    parser.add_argument("--feedback-iterations", type=int, default=3, help="Number of feedback calibration reruns after the baseline pass.")
    parser.add_argument("--seed", type=int, default=None, help="Run one seed only.")
    parser.add_argument("--seeds", type=int, nargs="*", default=None, help="Run an explicit list of seeds.")
    parser.add_argument("--seed-start", type=int, default=1, help="First seed when --seed/--seeds is omitted.")
    parser.add_argument("--seed-count", type=int, default=8, help="Number of seeds when --seed/--seeds is omitted.")
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parents[1] / "output" / "global_macro")
    parser.add_argument("--no-svg", action="store_true", help="Skip writing the SVG chart.")
    return parser.parse_args()


def resolve_seeds(args: argparse.Namespace) -> list[int]:
    if args.seed is not None:
        return [args.seed]
    if args.seeds:
        return list(dict.fromkeys(args.seeds))
    return list(range(args.seed_start, args.seed_start + args.seed_count))


def main() -> int:
    args = parse_args()
    seeds = resolve_seeds(args)
    if args.years < 1:
        raise SystemExit("--years must be at least 1")
    if args.volatility_scale <= 0:
        raise SystemExit("--volatility-scale must be positive")
    if args.feedback_iterations < 0:
        raise SystemExit("--feedback-iterations must be non-negative")

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
    feedback_params = MacroFeedbackParams(feedback_iterations=args.feedback_iterations)

    records_by_seed: dict[int, list[dict[str, Any]]] = {}
    convergence_by_seed: dict[int, dict[str, Any]] = {}
    for seed in seeds:
        records = run_full_chain(
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
        pass_records = [records]
        feedback_path: dict[int, dict[str, Any]] = {}
        for _ in range(args.feedback_iterations):
            raw_feedback_path = derive_feedback_path(records, feedback_params)
            feedback_path = blend_feedback_paths(
                feedback_path,
                raw_feedback_path,
                feedback_params.feedback_iteration_relaxation,
            )
            records = run_full_chain(
                seed,
                gdp_params=gdp_params,
                inflation_params=inflation_params,
                policy_params=policy_params,
                yield_curve_params=yield_curve_params,
                dollar_liquidity_params=dollar_liquidity_params,
                credit_spread_params=credit_spread_params,
                asset_price_params=asset_price_params,
                oil_commodity_params=oil_commodity_params,
                feedback_path=feedback_path,
            )
            pass_records.append(records)
        convergence = convergence_summary(pass_records, seed, feedback_params)
        convergence_by_seed[seed] = convergence
        records_by_seed[seed] = annotate_feedback_records(records, feedback_path, args.feedback_iterations, convergence)

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
                "convergence": "Pass diagnostics compare GDP growth, headline inflation, policy rate, HY spread, and Brent oil price across consecutive passes.",
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
