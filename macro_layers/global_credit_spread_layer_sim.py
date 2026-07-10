from __future__ import annotations

import argparse
import csv
import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean
from typing import Any, Iterable

from global_dollar_liquidity_layer_sim import (
    COMBINED_DOLLAR_LIQUIDITY_FIELDS,
    DOLLAR_LIQUIDITY_PARAM_VERSION,
    DollarLiquidityParams,
    simulate_dollar_liquidity_for_yield_path,
)
from global_gdp_annual_sim import GDPParams, simulate_global_gdp
from global_inflation_annual_sim import (
    INFLATION_PARAM_VERSION,
    InflationParams,
    as_float,
    simulate_inflation_for_gdp_path,
)
from global_policy_rate_layer_sim import POLICY_PARAM_VERSION, PolicyRateParams, simulate_policy_for_macro_path
from global_yield_curve_layer_sim import YIELD_CURVE_PARAM_VERSION, YieldCurveParams, simulate_yield_curve_for_policy_path


CREDIT_SPREAD_PARAM_VERSION = "global-credit-spread-layer-v0.2"
CREDIT_SPREAD_INTERFACE_VERSION = "credit-spread-feedback-interface-v0.2"


CREDIT_SPREAD_FIELDS = [
    "credit_spread_param_version",
    "credit_spread_interface_version",
    "global_investment_grade_spread_bps",
    "global_high_yield_spread_bps",
    "global_credit_spread_index",
    "credit_spread_change_bps",
    "default_risk_index",
    "lending_standards_index",
    "credit_availability_index",
    "corporate_refinancing_pressure_index",
    "bank_credit_stress_index",
    "bank_lending_sentiment_index",
    "bank_balance_sheet_stress_index",
    "credit_convexity_pressure_index",
    "credit_impairment_stock_index",
    "credit_regime",
    "credit_to_gdp_drag_placeholder",
    "credit_to_equity_risk_premium_impulse",
    "credit_to_policy_easing_pressure",
    "credit_to_inflation_demand_drag_placeholder",
    "credit_to_oil_demand_impulse",
]


COMBINED_CREDIT_SPREAD_FIELDS = COMBINED_DOLLAR_LIQUIDITY_FIELDS + CREDIT_SPREAD_FIELDS


@dataclass(frozen=True)
class CreditSpreadParams:
    initial_ig_spread_bps: float = 115.0
    initial_hy_spread_bps: float = 420.0
    initial_default_risk_index: float = 30.0
    initial_lending_standards_index: float = 42.0
    initial_credit_availability_index: float = 58.0
    initial_bank_credit_stress_index: float = 35.0
    initial_bank_lending_sentiment_index: float = 54.0
    initial_bank_balance_sheet_stress_index: float = 34.0
    initial_credit_impairment_stock_index: float = 0.0
    ig_spread_speed: float = 0.34
    hy_spread_speed: float = 0.38
    default_risk_speed: float = 0.34
    lending_standards_speed: float = 0.36
    bank_credit_stress_speed: float = 0.36
    bank_lending_sentiment_speed: float = 0.34
    bank_balance_sheet_stress_speed: float = 0.34
    credit_impairment_persistence: float = 0.84
    min_ig_spread_bps: float = 35.0
    max_ig_spread_bps: float = 650.0
    min_hy_spread_bps: float = 150.0
    max_hy_spread_bps: float = 2200.0
    base_ig_spread_bps: float = 60.0
    base_hy_spread_bps: float = 275.0
    default_risk_ig_beta: float = 1.25
    lending_standards_ig_beta: float = 0.90
    funding_stress_ig_beta: float = 0.85
    default_risk_hy_beta: float = 5.20
    lending_standards_hy_beta: float = 4.40
    funding_stress_hy_beta: float = 3.20
    fci_ig_beta: float = 12.0
    fci_hy_beta: float = 45.0
    liquidity_ig_beta: float = 0.65
    liquidity_hy_beta: float = 2.40
    risk_appetite_ig_beta: float = 0.28
    risk_appetite_hy_beta: float = 1.20
    credit_tightening_ig_beta: float = 18.0
    credit_tightening_hy_beta: float = 95.0
    crisis_hy_beta: float = 170.0
    spread_noise_scale_bps: float = 12.0
    credit_seed_offset: int = 12_700_091


@dataclass
class CreditSpreadState:
    ig_spread_bps: float = 115.0
    hy_spread_bps: float = 420.0
    previous_weighted_spread_bps: float = 237.0
    default_risk_index: float = 30.0
    lending_standards_index: float = 42.0
    bank_credit_stress_index: float = 35.0
    bank_lending_sentiment_index: float = 54.0
    bank_balance_sheet_stress_index: float = 34.0
    credit_impairment_stock_index: float = 0.0


@dataclass
class CreditSpreadRecord:
    credit_spread_param_version: str
    credit_spread_interface_version: str
    global_investment_grade_spread_bps: float
    global_high_yield_spread_bps: float
    global_credit_spread_index: float
    credit_spread_change_bps: float
    default_risk_index: float
    lending_standards_index: float
    credit_availability_index: float
    corporate_refinancing_pressure_index: float
    bank_credit_stress_index: float
    bank_lending_sentiment_index: float
    bank_balance_sheet_stress_index: float
    credit_convexity_pressure_index: float
    credit_impairment_stock_index: float
    credit_regime: str
    credit_to_gdp_drag_placeholder: float
    credit_to_equity_risk_premium_impulse: float
    credit_to_policy_easing_pressure: float
    credit_to_inflation_demand_drag_placeholder: float
    credit_to_oil_demand_impulse: float


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


def piecewise_credit_convexity_pressure(hy_spread: float) -> float:
    return clamp(
        0.030 * max(0.0, min(hy_spread, 800.0) - 500.0)
        + 0.075 * max(0.0, min(hy_spread, 1200.0) - 800.0)
        + 0.120 * max(0.0, hy_spread - 1200.0),
        0.0,
        100.0,
    )


def piecewise_credit_gdp_drag(hy_spread: float) -> float:
    return (
        -0.0022 * max(0.0, min(hy_spread, 800.0) - 500.0)
        -0.0050 * max(0.0, min(hy_spread, 1200.0) - 800.0)
        -0.0070 * max(0.0, hy_spread - 1200.0)
    )


def classify_credit_regime(
    *,
    year_index: int,
    hy_spread: float,
    ig_spread: float,
    spread_change: float,
    default_risk: float,
    lending_standards: float,
    credit_availability: float,
    refinancing_pressure: float,
    bank_credit_stress: float,
    bank_lending_sentiment: float,
    bank_balance_sheet_stress: float,
    credit_convexity_pressure: float,
    credit_impairment_stock: float,
    financial_conditions: float,
    liquidity_index: float,
    liquidity_impulse: float,
    risk_appetite: float,
    crisis_intensity: float,
) -> str:
    if year_index == 0:
        return "initial"
    if crisis_intensity >= 0.65 and (hy_spread >= 850.0 or default_risk >= 72.0 or credit_convexity_pressure >= 35.0):
        return "recession_default_wave"
    if bank_balance_sheet_stress >= 78.0 and bank_lending_sentiment <= 24.0:
        return "bank_lending_freeze"
    if credit_impairment_stock >= 32.0 and bank_lending_sentiment <= 52.0:
        return "balance_sheet_repair"
    if bank_credit_stress >= 68.0 and spread_change >= 55.0:
        return "funding_stress_credit_shock"
    if credit_convexity_pressure >= 45.0 and spread_change >= 35.0:
        return "convex_credit_selloff"
    if hy_spread >= 720.0 and financial_conditions >= 1.0:
        return "credit_squeeze"
    if spread_change >= 65.0 and financial_conditions >= 0.50:
        return "rapid_spread_widening"
    if liquidity_impulse >= 5.0 and spread_change <= -35.0 and credit_impairment_stock <= 24.0:
        return "credit_easing_repair"
    if hy_spread <= 340.0 and ig_spread <= 95.0 and risk_appetite >= 64.0 and liquidity_index >= 62.0 and credit_impairment_stock <= 14.0:
        return "credit_goldilocks"
    if refinancing_pressure >= 65.0 and credit_availability <= 42.0:
        return "refinancing_wall"
    if hy_spread <= 420.0 and lending_standards >= 55.0 and financial_conditions > 0.0:
        return "late_cycle_tightening"
    if credit_availability >= 66.0 and risk_appetite >= 58.0 and hy_spread <= 520.0 and bank_lending_sentiment >= 55.0 and credit_impairment_stock <= 18.0:
        return "easy_credit_expansion"
    return "normal_credit_cycle"


def simulate_credit_spreads_for_dollar_path(
    records: list[dict[str, Any]],
    params: CreditSpreadParams,
) -> list[dict[str, Any]]:
    if not records:
        return []

    seed = int(records[0].get("seed", 0))
    rng = random.Random(seed + params.credit_seed_offset)
    state = CreditSpreadState(
        ig_spread_bps=params.initial_ig_spread_bps,
        hy_spread_bps=params.initial_hy_spread_bps,
        previous_weighted_spread_bps=0.35 * params.initial_ig_spread_bps + 0.65 * params.initial_hy_spread_bps,
        default_risk_index=params.initial_default_risk_index,
        lending_standards_index=params.initial_lending_standards_index,
        bank_credit_stress_index=params.initial_bank_credit_stress_index,
        bank_lending_sentiment_index=params.initial_bank_lending_sentiment_index,
        bank_balance_sheet_stress_index=params.initial_bank_balance_sheet_stress_index,
        credit_impairment_stock_index=params.initial_credit_impairment_stock_index,
    )

    combined: list[dict[str, Any]] = []

    for row in records:
        year_index = int(row["year_index"])
        gdp_growth = as_float(row, "realized_growth_pct")
        potential_growth = as_float(row, "potential_growth_pct", 2.0)
        output_gap = as_float(row, "output_gap_pct")
        stress = as_float(row, "financial_stress_index")
        crisis_intensity = as_float(row, "crisis_intensity")
        policy_credit_tightening = as_float(row, "policy_to_credit_tightening_impulse")
        yield_credit_tightening = as_float(row, "yield_curve_to_credit_impulse")
        dollar_credit_tightening = as_float(row, "dollar_to_credit_tightening_impulse")
        liquidity_credit_easing = as_float(row, "liquidity_to_credit_easing_impulse")
        liquidity_index = as_float(row, "global_liquidity_index", 55.0)
        liquidity_impulse = as_float(row, "liquidity_impulse_index")
        financial_conditions = as_float(row, "global_financial_conditions_index")
        risk_appetite = as_float(row, "risk_appetite_index", 50.0)
        dollar_index = as_float(row, "global_dollar_index", 100.0)
        dollar_momentum = as_float(row, "dollar_momentum_index")
        funding_stress = as_float(row, "dollar_funding_stress_index", 35.0)
        em_stress = as_float(row, "em_stress_index", 35.0)
        qe_liquidity = as_float(row, "qe_liquidity_index")
        real_10y = as_float(row, "global_real_10y_yield_pct")
        inversion_pressure = as_float(row, "curve_inversion_pressure")
        term_premium = as_float(row, "term_premium_pct")
        impairment_memory = state.credit_impairment_stock_index

        growth_shortfall = max(0.0, potential_growth - gdp_growth)
        recession_signal = max(0.0, -gdp_growth)
        negative_gap = max(0.0, -output_gap)
        credit_tightening_stack = (
            0.70 * policy_credit_tightening
            + 0.85 * yield_credit_tightening
            + 1.10 * dollar_credit_tightening
            - 0.85 * liquidity_credit_easing
        )

        default_risk_target = (
            24.0
            + 5.2 * growth_shortfall
            + 8.5 * recession_signal
            + 2.2 * negative_gap
            + 0.36 * max(0.0, stress - 32.0)
            + 14.0 * crisis_intensity
            + 6.0 * max(0.0, financial_conditions)
            + 7.0 * max(0.0, credit_tightening_stack)
            + 2.2 * max(0.0, real_10y)
            + 0.06 * impairment_memory
            - 0.16 * max(0.0, liquidity_index - 50.0)
            - 0.12 * max(0.0, risk_appetite - 50.0)
        )
        default_risk = clamp(smooth(state.default_risk_index, default_risk_target, params.default_risk_speed), 0.0, 100.0)

        lending_standards_target = (
            38.0
            + 0.34 * funding_stress
            + 0.18 * em_stress
            + 4.8 * max(0.0, financial_conditions)
            + 0.28 * inversion_pressure
            + 6.5 * max(0.0, credit_tightening_stack)
            + 0.24 * max(0.0, dollar_index - 100.0)
            + 0.20 * max(0.0, dollar_momentum)
            + 0.22 * max(0.0, stress - 35.0)
            + 0.06 * impairment_memory
            - 0.26 * max(0.0, liquidity_index - 50.0)
            - 0.18 * max(0.0, liquidity_impulse)
        )
        lending_standards = clamp(smooth(state.lending_standards_index, lending_standards_target, params.lending_standards_speed), 0.0, 100.0)

        bank_credit_stress_target = (
            26.0
            + 0.46 * funding_stress
            + 0.28 * stress
            + 0.22 * em_stress
            + 5.5 * max(0.0, financial_conditions)
            + 0.16 * inversion_pressure
            + 4.0 * max(0.0, term_premium - 0.75)
            + 0.08 * impairment_memory
            - 0.22 * max(0.0, liquidity_index - 50.0)
        )
        bank_credit_stress = clamp(smooth(state.bank_credit_stress_index, bank_credit_stress_target, params.bank_credit_stress_speed), 0.0, 100.0)

        ig_target = (
            params.base_ig_spread_bps
            + params.default_risk_ig_beta * default_risk
            + params.lending_standards_ig_beta * lending_standards
            + params.funding_stress_ig_beta * funding_stress
            + params.fci_ig_beta * max(0.0, financial_conditions)
            + params.credit_tightening_ig_beta * max(0.0, credit_tightening_stack)
            + 0.20 * impairment_memory
            + 5.0 * max(0.0, real_10y)
            - params.liquidity_ig_beta * liquidity_index
            - params.risk_appetite_ig_beta * risk_appetite
            + rng.gauss(0.0, params.spread_noise_scale_bps * 0.45)
        )
        ig_spread = clamp(
            smooth(state.ig_spread_bps, ig_target, params.ig_spread_speed),
            params.min_ig_spread_bps,
            params.max_ig_spread_bps,
        )

        hy_target = (
            params.base_hy_spread_bps
            + params.default_risk_hy_beta * default_risk
            + params.lending_standards_hy_beta * lending_standards
            + params.funding_stress_hy_beta * funding_stress
            + params.fci_hy_beta * max(0.0, financial_conditions)
            + params.credit_tightening_hy_beta * max(0.0, credit_tightening_stack)
            + params.crisis_hy_beta * crisis_intensity
            + 0.95 * impairment_memory
            + 22.0 * max(0.0, real_10y)
            + 18.0 * max(0.0, growth_shortfall)
            - params.liquidity_hy_beta * liquidity_index
            - params.risk_appetite_hy_beta * risk_appetite
            + rng.gauss(0.0, params.spread_noise_scale_bps)
        )
        hy_spread = clamp(
            smooth(state.hy_spread_bps, hy_target, params.hy_spread_speed),
            params.min_hy_spread_bps,
            params.max_hy_spread_bps,
        )

        hy_ig_quality_gap = max(0.0, hy_spread - ig_spread)
        credit_convexity_pressure = piecewise_credit_convexity_pressure(hy_spread)
        bank_balance_sheet_stress_target = (
            20.0
            + 0.32 * bank_credit_stress
            + 0.26 * default_risk
            + 0.022 * max(0.0, hy_spread - 500.0)
            + 0.012 * max(0.0, hy_ig_quality_gap - 300.0)
            + 0.22 * max(0.0, funding_stress - 35.0)
            + 0.25 * credit_convexity_pressure
            + 0.12 * impairment_memory
            - 0.16 * max(0.0, qe_liquidity - 25.0)
            - 0.16 * max(0.0, liquidity_index - 55.0)
        )
        bank_balance_sheet_stress = clamp(
            smooth(state.bank_balance_sheet_stress_index, bank_balance_sheet_stress_target, params.bank_balance_sheet_stress_speed),
            0.0,
            100.0,
        )
        bank_lending_sentiment_target = (
            78.0
            - 0.24 * lending_standards
            - 0.22 * default_risk
            - 0.18 * bank_balance_sheet_stress
            - 0.012 * max(0.0, hy_spread - 500.0)
            - 0.010 * max(0.0, hy_ig_quality_gap - 300.0)
            - 0.14 * credit_convexity_pressure
            - 0.12 * impairment_memory
            + 0.18 * max(0.0, liquidity_index - 50.0)
            + 0.14 * max(0.0, qe_liquidity - 20.0)
            + 0.09 * max(0.0, risk_appetite - 50.0)
        )
        bank_lending_sentiment = clamp(
            smooth(state.bank_lending_sentiment_index, bank_lending_sentiment_target, params.bank_lending_sentiment_speed),
            0.0,
            100.0,
        )

        weighted_spread = 0.35 * ig_spread + 0.65 * hy_spread
        spread_change = weighted_spread - state.previous_weighted_spread_bps
        credit_spread_index = clamp(
            (ig_spread - 70.0) / 4.2
            + (hy_spread - 280.0) / 13.0
            + 0.22 * default_risk
            + 0.16 * lending_standards,
            0.0,
            100.0,
        )
        credit_availability = clamp(
            100.0
            - 0.56 * lending_standards
            - 0.35 * default_risk
            - 0.16 * max(0.0, hy_spread - 420.0) / 10.0
            - 0.22 * max(0.0, bank_balance_sheet_stress - 45.0)
            - 0.12 * impairment_memory
            + 0.30 * max(0.0, bank_lending_sentiment - 50.0)
            + 0.28 * (liquidity_index - 50.0)
            + 0.12 * max(0.0, risk_appetite - 50.0),
            0.0,
            100.0,
        )
        impairment_inflow = clamp(
            0.025 * max(0.0, hy_spread - 560.0)
            + 0.12 * max(0.0, default_risk - 58.0)
            + 0.10 * max(0.0, lending_standards - 58.0)
            + 0.10 * max(0.0, bank_balance_sheet_stress - 55.0)
            + 0.08 * max(0.0, spread_change)
            + 1.80 * recession_signal
            + 0.35 * max(0.0, negative_gap - 2.0)
            + 8.0 * max(0.0, crisis_intensity - 0.45),
            0.0,
            28.0,
        )
        repair_relief = (
            0.12 * max(0.0, credit_availability - 55.0)
            + 0.10 * max(0.0, bank_lending_sentiment - 52.0)
            + 0.08 * max(0.0, liquidity_impulse)
            + 0.03 * max(0.0, liquidity_index - 60.0)
        )
        credit_impairment_stock = clamp(
            impairment_memory * params.credit_impairment_persistence + impairment_inflow - repair_relief,
            0.0,
            100.0,
        )
        refinancing_pressure = clamp(
            0.035 * max(0.0, hy_spread - 350.0)
            + 0.026 * max(0.0, ig_spread - 110.0)
            + 7.0 * max(0.0, real_10y)
            + 0.24 * funding_stress
            + 0.22 * max(0.0, dollar_index - 100.0)
            + 8.0 * max(0.0, financial_conditions)
            + 0.08 * credit_impairment_stock
            - 0.18 * max(0.0, liquidity_index - 50.0),
            0.0,
            100.0,
        )
        regime = classify_credit_regime(
            year_index=year_index,
            hy_spread=hy_spread,
            ig_spread=ig_spread,
            spread_change=spread_change,
            default_risk=default_risk,
            lending_standards=lending_standards,
            credit_availability=credit_availability,
            refinancing_pressure=refinancing_pressure,
            bank_credit_stress=bank_credit_stress,
            bank_lending_sentiment=bank_lending_sentiment,
            bank_balance_sheet_stress=bank_balance_sheet_stress,
            credit_convexity_pressure=credit_convexity_pressure,
            credit_impairment_stock=credit_impairment_stock,
            financial_conditions=financial_conditions,
            liquidity_index=liquidity_index,
            liquidity_impulse=liquidity_impulse,
            risk_appetite=risk_appetite,
            crisis_intensity=crisis_intensity,
        )

        credit_to_gdp_drag = clamp(
            piecewise_credit_gdp_drag(hy_spread)
            - 0.0040 * max(0.0, ig_spread - 120.0)
            - 0.012 * max(0.0, lending_standards - 55.0)
            - 0.012 * max(0.0, 50.0 - bank_lending_sentiment)
            - 0.007 * max(0.0, bank_balance_sheet_stress - 55.0)
            - 0.005 * credit_impairment_stock
            + 0.004 * max(0.0, credit_availability - 65.0),
            -3.5,
            0.35,
        )
        equity_risk_premium = clamp(
            0.0060 * max(0.0, hy_spread - 350.0)
            + 0.010 * max(0.0, default_risk - 45.0)
            + 0.008 * max(0.0, bank_credit_stress - 50.0)
            + 0.006 * max(0.0, bank_balance_sheet_stress - 55.0)
            + 0.004 * credit_convexity_pressure
            + 0.003 * credit_impairment_stock
            - 0.006 * max(0.0, liquidity_index - 60.0),
            -1.0,
            2.5,
        )
        policy_easing_pressure = clamp(
            0.010 * max(0.0, hy_spread - 520.0)
            + 0.012 * max(0.0, default_risk - 55.0)
            + 0.010 * max(0.0, lending_standards - 60.0)
            + 0.006 * max(0.0, bank_balance_sheet_stress - 60.0)
            + 0.004 * max(0.0, credit_impairment_stock - 25.0)
            + 0.50 * crisis_intensity,
            0.0,
            2.0,
        )
        inflation_drag = clamp(
            -0.006 * max(0.0, hy_spread - 500.0)
            - 0.012 * max(0.0, default_risk - 55.0)
            - 0.006 * max(0.0, 50.0 - bank_lending_sentiment)
            - 0.002 * credit_impairment_stock
            + 0.004 * max(0.0, credit_availability - 65.0),
            -1.5,
            0.25,
        )
        oil_demand_impulse = clamp(
            -0.0045 * max(0.0, hy_spread - 450.0)
            - 0.012 * max(0.0, default_risk - 50.0)
            - 0.006 * max(0.0, 50.0 - bank_lending_sentiment)
            - 0.002 * credit_impairment_stock
            + 0.005 * max(0.0, credit_availability - 65.0),
            -1.5,
            0.35,
        )

        record = CreditSpreadRecord(
            credit_spread_param_version=CREDIT_SPREAD_PARAM_VERSION,
            credit_spread_interface_version=CREDIT_SPREAD_INTERFACE_VERSION,
            global_investment_grade_spread_bps=ig_spread,
            global_high_yield_spread_bps=hy_spread,
            global_credit_spread_index=credit_spread_index,
            credit_spread_change_bps=spread_change,
            default_risk_index=default_risk,
            lending_standards_index=lending_standards,
            credit_availability_index=credit_availability,
            corporate_refinancing_pressure_index=refinancing_pressure,
            bank_credit_stress_index=bank_credit_stress,
            bank_lending_sentiment_index=bank_lending_sentiment,
            bank_balance_sheet_stress_index=bank_balance_sheet_stress,
            credit_convexity_pressure_index=credit_convexity_pressure,
            credit_impairment_stock_index=credit_impairment_stock,
            credit_regime=regime,
            credit_to_gdp_drag_placeholder=credit_to_gdp_drag,
            credit_to_equity_risk_premium_impulse=equity_risk_premium,
            credit_to_policy_easing_pressure=policy_easing_pressure,
            credit_to_inflation_demand_drag_placeholder=inflation_drag,
            credit_to_oil_demand_impulse=oil_demand_impulse,
        )
        combined.append(round_record({**row, **asdict(record)}))

        state.ig_spread_bps = ig_spread
        state.hy_spread_bps = hy_spread
        state.previous_weighted_spread_bps = weighted_spread
        state.default_risk_index = default_risk
        state.lending_standards_index = lending_standards
        state.bank_credit_stress_index = bank_credit_stress
        state.bank_lending_sentiment_index = bank_lending_sentiment
        state.bank_balance_sheet_stress_index = bank_balance_sheet_stress
        state.credit_impairment_stock_index = credit_impairment_stock

    return combined


def summarize_seed(records: list[dict[str, Any]]) -> dict[str, Any]:
    data = records[1:] if len(records) > 1 else records
    ig_values = [as_float(row, "global_investment_grade_spread_bps") for row in data]
    hy_values = [as_float(row, "global_high_yield_spread_bps") for row in data]
    max_hy_row = max(data, key=lambda row: as_float(row, "global_high_yield_spread_bps")) if data else records[-1]
    min_hy_row = min(data, key=lambda row: as_float(row, "global_high_yield_spread_bps")) if data else records[-1]
    squeeze_years = sum(1 for row in data if str(row["credit_regime"]) in {"credit_squeeze", "convex_credit_selloff", "bank_lending_freeze", "balance_sheet_repair", "funding_stress_credit_shock", "recession_default_wave", "rapid_spread_widening", "refinancing_wall"})
    easy_credit_years = sum(1 for row in data if str(row["credit_regime"]) in {"credit_goldilocks", "easy_credit_expansion", "credit_easing_repair"})
    final = records[-1]
    return {
        "seed": int(final["seed"]),
        "start_year": int(records[0]["year"]),
        "end_year": int(final["year"]),
        "average_ig_spread_bps": round(mean(ig_values), 3) if ig_values else 0.0,
        "average_hy_spread_bps": round(mean(hy_values), 3) if hy_values else 0.0,
        "max_hy_spread_bps": as_float(max_hy_row, "global_high_yield_spread_bps"),
        "max_hy_spread_year": int(max_hy_row["year"]),
        "min_hy_spread_bps": as_float(min_hy_row, "global_high_yield_spread_bps"),
        "min_hy_spread_year": int(min_hy_row["year"]),
        "credit_squeeze_years": squeeze_years,
        "easy_credit_years": easy_credit_years,
        "final_ig_spread_bps": as_float(final, "global_investment_grade_spread_bps"),
        "final_hy_spread_bps": as_float(final, "global_high_yield_spread_bps"),
        "final_credit_regime": str(final["credit_regime"]),
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
    path.write_text(f"window.GLOBAL_CREDIT_SPREAD_DATA = {payload};\n", encoding="utf-8")


def build_credit_spread_svg(records_by_seed: dict[int, list[dict[str, Any]]], path: Path) -> None:
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
    values = [as_float(row, "global_high_yield_spread_bps") for row in all_records]
    min_year, max_year = min(years), max(years)
    min_value = max(100.0, min(values) - 50.0)
    max_value = max(900.0, max(values) + 100.0)

    def x_of(year: int) -> float:
        return left + (year - min_year) / max(1, max_year - min_year) * plot_w

    def y_of(value: float) -> float:
        return top + (max_value - value) / max(1e-9, max_value - min_value) * plot_h

    palette = ["#fb923c", "#38bdf8", "#facc15", "#a78bfa", "#34d399", "#fb7185", "#f472b6", "#eab308"]
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#07090d"/>',
        f'<text x="{left}" y="27" font-family="Arial" font-size="20" fill="#f5f7fb">Global High Yield Spread Paths by Seed</text>',
        f'<text x="{left}" y="50" font-family="Arial" font-size="12" fill="#94a3b8">HY credit spreads after dollar, liquidity, financial conditions, funding stress, and default-risk dynamics</text>',
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
            f'{x_of(int(row["year"])):.2f},{y_of(as_float(row, "global_high_yield_spread_bps")):.2f}'
            for row in records
        )
        lines.append(f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round"/>')
        last = records[-1]
        lines.append(
            f'<text x="{x_of(int(last["year"])) + 6:.2f}" y="{y_of(as_float(last, "global_high_yield_spread_bps")) + 4:.2f}" '
            f'font-family="Arial" font-size="11" fill="{color}">seed {seed}</text>'
        )

    lines.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}" stroke="#64748b"/>')
    lines.append(f'<line x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}" stroke="#64748b"/>')
    lines.append(f'<text x="18" y="{top + plot_h / 2}" transform="rotate(-90 18 {top + plot_h / 2})" text-anchor="middle" font-family="Arial" font-size="12" fill="#94a3b8">HY spread bps</text>')
    lines.append("</svg>")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a combined global GDP + inflation + policy + yield + dollar-liquidity + credit-spread annual simulation.",
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

    gdp_params = GDPParams(
        years=args.years,
        start_year=args.start_year,
        initial_gdp_trillion_usd=args.initial_gdp,
        volatility_scale=args.volatility_scale,
    )
    inflation_params = InflationParams()
    policy_params = PolicyRateParams()
    yield_curve_params = YieldCurveParams()
    dollar_liquidity_params = DollarLiquidityParams()
    credit_spread_params = CreditSpreadParams()

    records_by_seed: dict[int, list[dict[str, Any]]] = {}
    for seed in seeds:
        gdp_records = simulate_global_gdp(seed, gdp_params)
        inflation_records = simulate_inflation_for_gdp_path(seed, gdp_records, inflation_params)
        policy_records = simulate_policy_for_macro_path(inflation_records, policy_params)
        yield_records = simulate_yield_curve_for_policy_path(policy_records, yield_curve_params)
        dollar_records = simulate_dollar_liquidity_for_yield_path(yield_records, dollar_liquidity_params)
        records_by_seed[seed] = simulate_credit_spreads_for_dollar_path(dollar_records, credit_spread_params)

    all_records = [row for records in records_by_seed.values() for row in records]
    summaries = [summarize_seed(records) for records in records_by_seed.values()]

    args.output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = args.output_dir / "global_credit_spread_seed_sweep.csv"
    json_path = args.output_dir / "global_credit_spread_seed_sweep.json"
    viewer_data_path = args.output_dir / "global_credit_spread_viewer_data.js"
    svg_path = args.output_dir / "global_credit_spread_curves.svg"

    write_csv(csv_path, all_records, COMBINED_CREDIT_SPREAD_FIELDS)
    write_json(
        json_path,
        {
            "gdp_param_version": all_records[0]["param_version"] if all_records else "",
            "inflation_param_version": INFLATION_PARAM_VERSION,
            "policy_param_version": POLICY_PARAM_VERSION,
            "yield_curve_param_version": YIELD_CURVE_PARAM_VERSION,
            "dollar_liquidity_param_version": DOLLAR_LIQUIDITY_PARAM_VERSION,
            "credit_spread_param_version": CREDIT_SPREAD_PARAM_VERSION,
            "credit_spread_interface_version": CREDIT_SPREAD_INTERFACE_VERSION,
            "gdp_params": asdict(gdp_params),
            "inflation_params": asdict(inflation_params),
            "policy_params": asdict(policy_params),
            "yield_curve_params": asdict(yield_curve_params),
            "dollar_liquidity_params": asdict(dollar_liquidity_params),
            "credit_spread_params": asdict(credit_spread_params),
            "seeds": seeds,
            "summary": summaries,
            "model_note": {
                "coupling": "Credit spreads are downstream of GDP, inflation, policy, yield curve, dollar, liquidity, funding stress, and financial conditions.",
                "no_feedback_yet": "Credit impulses to GDP, equity risk premium, policy easing pressure, inflation demand drag, and oil demand are emitted as placeholders only; upstream paths are not recomputed in v0.1.",
                "future_connection": "The credit_to_* fields are intended for later equity, bond, oil, and multi-pass macro feedback layers.",
            },
        },
    )
    write_viewer_data_js(viewer_data_path, all_records)
    if not args.no_svg:
        build_credit_spread_svg(records_by_seed, svg_path)

    print(f"Wrote {csv_path}")
    print(f"Wrote {json_path}")
    print(f"Wrote {viewer_data_path}")
    if not args.no_svg:
        print(f"Wrote {svg_path}")
    for summary in summaries:
        print(
            "seed={seed} avg_ig={average_ig_spread_bps:.0f}bps "
            "avg_hy={average_hy_spread_bps:.0f}bps "
            "squeeze_years={credit_squeeze_years} easy_years={easy_credit_years} "
            "final_regime={final_credit_regime}".format(**summary)
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
