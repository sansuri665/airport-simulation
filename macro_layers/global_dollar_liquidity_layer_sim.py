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
require_in_range = simulation_utils.require_in_range

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
yield_curve_layer = import_module(f"{_SIBLING_PREFIX}global_yield_curve_layer_sim")

GDPParams = global_gdp_layer.GDPParams
simulate_global_gdp = global_gdp_layer.simulate_global_gdp
INFLATION_PARAM_VERSION = inflation_layer.INFLATION_PARAM_VERSION
InflationParams = inflation_layer.InflationParams
as_float = inflation_layer.as_float
simulate_inflation_for_gdp_path = inflation_layer.simulate_inflation_for_gdp_path
POLICY_PARAM_VERSION = policy_rate_layer.POLICY_PARAM_VERSION
PolicyRateParams = policy_rate_layer.PolicyRateParams
simulate_policy_for_macro_path = policy_rate_layer.simulate_policy_for_macro_path
COMBINED_YIELD_CURVE_FIELDS = yield_curve_layer.COMBINED_YIELD_CURVE_FIELDS
YIELD_CURVE_PARAM_VERSION = yield_curve_layer.YIELD_CURVE_PARAM_VERSION
YieldCurveParams = yield_curve_layer.YieldCurveParams
simulate_yield_curve_for_policy_path = yield_curve_layer.simulate_yield_curve_for_policy_path


DOLLAR_LIQUIDITY_PARAM_VERSION = "global-dollar-liquidity-layer-v0.4"
DOLLAR_LIQUIDITY_INTERFACE_VERSION = "dollar-liquidity-feedback-interface-v0.3"
DOLLAR_LIQUIDITY_BOUNDARY_VERSION = "dollar-liquidity-boundaries-v1"


DOLLAR_LIQUIDITY_FIELDS = [
    "dollar_liquidity_param_version",
    "dollar_liquidity_interface_version",
    "dollar_liquidity_boundary_version",
    "global_dollar_index",
    "unclamped_dollar_target_index",
    "dollar_floor_applied",
    "dollar_cap_applied",
    "dollar_consecutive_boundary_years",
    "dollar_yoy_change_pct",
    "dollar_momentum_index",
    "global_liquidity_index",
    "liquidity_impulse_index",
    "global_financial_conditions_index",
    "unclamped_financial_conditions_target_index",
    "financial_conditions_floor_applied",
    "financial_conditions_cap_applied",
    "financial_conditions_consecutive_boundary_years",
    "risk_appetite_index",
    "em_stress_index",
    "dollar_funding_stress_index",
    "dollar_liquidity_regime",
    "dollar_to_import_inflation_impulse",
    "dollar_to_oil_pressure_impulse",
    "dollar_to_gdp_drag_placeholder",
    "dollar_to_credit_tightening_impulse",
    "liquidity_to_equity_impulse",
    "liquidity_to_credit_easing_impulse",
]


COMBINED_DOLLAR_LIQUIDITY_FIELDS = COMBINED_YIELD_CURVE_FIELDS + DOLLAR_LIQUIDITY_FIELDS


@dataclass(frozen=True)
class DollarLiquidityParams:
    initial_dollar_index: float = 100.0
    initial_liquidity_index: float = 55.0
    initial_financial_conditions_index: float = 0.0
    initial_risk_appetite_index: float = 50.0
    initial_em_stress_index: float = 35.0
    dollar_speed: float = 0.30
    liquidity_speed: float = 0.34
    financial_conditions_speed: float = 0.42
    risk_appetite_speed: float = 0.36
    em_stress_speed: float = 0.36
    funding_stress_speed: float = 0.40
    base_dollar_index: float = 100.0
    dollar_real_rate_beta: float = 3.20
    dollar_policy_stance_beta: float = 2.15
    dollar_safe_haven_beta: float = 7.80
    dollar_stress_beta: float = 0.10
    dollar_inversion_beta: float = 0.0
    dollar_qe_beta: float = 0.0
    dollar_yield_curve_impulse_beta: float = 4.25
    liquidity_qe_beta: float = 0.58
    liquidity_balance_sheet_beta: float = 0.36
    liquidity_real_rate_beta: float = 4.15
    liquidity_dollar_drag_beta: float = 0.30
    liquidity_stress_drag_beta: float = 0.20
    fci_dollar_beta: float = 0.040
    fci_real_rate_beta: float = 0.38
    fci_policy_stance_beta: float = 0.26
    fci_stress_beta: float = 0.024
    fci_inversion_beta: float = 0.014
    fci_liquidity_ease_beta: float = 0.030
    risk_fci_beta: float = 7.80
    risk_stress_beta: float = 0.30
    risk_crisis_beta: float = 16.0
    risk_growth_beta: float = 2.60
    noise_scale: float = 0.85
    min_dollar_index: float = 82.0
    max_dollar_index: float = 124.0
    min_financial_conditions_index: float = -4.0
    max_financial_conditions_index: float = 4.0
    dollar_seed_offset: int = 9_500_117


def validate_initial_parameters(params: DollarLiquidityParams) -> None:
    require_in_range(
        "initial_dollar_index",
        params.initial_dollar_index,
        params.min_dollar_index,
        params.max_dollar_index,
    )
    require_in_range("initial_liquidity_index", params.initial_liquidity_index, 0.0, 100.0)
    require_in_range(
        "initial_financial_conditions_index",
        params.initial_financial_conditions_index,
        params.min_financial_conditions_index,
        params.max_financial_conditions_index,
    )
    require_in_range("initial_risk_appetite_index", params.initial_risk_appetite_index, 0.0, 100.0)
    require_in_range("initial_em_stress_index", params.initial_em_stress_index, 0.0, 100.0)


@dataclass
class DollarLiquidityState:
    dollar_index: float = 100.0
    previous_dollar_index: float = 100.0
    liquidity_index: float = 55.0
    previous_liquidity_index: float = 55.0
    financial_conditions_index: float = 0.0
    risk_appetite_index: float = 50.0
    em_stress_index: float = 35.0
    dollar_funding_stress_index: float = 35.0


@dataclass
class DollarLiquidityRecord:
    dollar_liquidity_param_version: str
    dollar_liquidity_interface_version: str
    dollar_liquidity_boundary_version: str
    global_dollar_index: float
    unclamped_dollar_target_index: float
    dollar_floor_applied: bool
    dollar_cap_applied: bool
    dollar_consecutive_boundary_years: int
    dollar_yoy_change_pct: float
    dollar_momentum_index: float
    global_liquidity_index: float
    liquidity_impulse_index: float
    global_financial_conditions_index: float
    unclamped_financial_conditions_target_index: float
    financial_conditions_floor_applied: bool
    financial_conditions_cap_applied: bool
    financial_conditions_consecutive_boundary_years: int
    risk_appetite_index: float
    em_stress_index: float
    dollar_funding_stress_index: float
    dollar_liquidity_regime: str
    dollar_to_import_inflation_impulse: float
    dollar_to_oil_pressure_impulse: float
    dollar_to_gdp_drag_placeholder: float
    dollar_to_credit_tightening_impulse: float
    liquidity_to_equity_impulse: float
    liquidity_to_credit_easing_impulse: float



def smooth(old: float, target: float, speed: float) -> float:
    return old * (1.0 - speed) + target * speed


def boundary_flags(value: float, floor: float, cap: float) -> tuple[bool, bool]:
    return value < floor, value > cap


def advance_boundary_run(previous: int, floor_applied: bool, cap_applied: bool) -> int:
    return previous + 1 if floor_applied or cap_applied else 0


def pct_change(current: float, previous: float) -> float:
    if previous <= 0.0:
        return 0.0
    return (current / previous - 1.0) * 100.0


def classify_dollar_liquidity_regime(
    *,
    year_index: int,
    dollar_index: float,
    dollar_momentum: float,
    liquidity_index: float,
    liquidity_impulse: float,
    financial_conditions: float,
    risk_appetite: float,
    em_stress: float,
    funding_stress: float,
    crisis_intensity: float,
    qe_liquidity_index: float,
) -> str:
    if year_index == 0:
        return "initial"
    if crisis_intensity >= 0.55 and dollar_momentum > 0.5 and funding_stress >= 50.0:
        return "crisis_dollar_squeeze"
    if dollar_index >= 106.0 and risk_appetite < 42.0:
        return "safe_haven_dollar_bid"
    if liquidity_impulse >= 7.0 and qe_liquidity_index >= 35.0 and dollar_momentum <= 1.5:
        return "liquidity_easing_reflation"
    if financial_conditions >= 1.75:
        return "tight_financial_conditions"
    if dollar_index <= 96.0 and liquidity_index >= 62.0 and risk_appetite >= 55.0:
        return "dollar_bear_liquidity_wave"
    if liquidity_index >= 64.0 and risk_appetite >= 58.0:
        return "risk_on_liquidity_expansion"
    if em_stress >= 62.0 and dollar_index >= 103.0:
        return "em_dollar_pressure"
    if dollar_index >= 104.0 and financial_conditions >= 0.75:
        return "disinflationary_dollar_strength"
    if dollar_index <= 97.0 and financial_conditions <= -0.35:
        return "easy_dollar_liquidity"
    return "neutral_dollar_liquidity"


def simulate_dollar_liquidity_for_yield_path(
    records: list[dict[str, Any]],
    params: DollarLiquidityParams,
) -> list[dict[str, Any]]:
    validate_initial_parameters(params)
    if not records:
        return []

    seed = int(records[0].get("seed", 0))
    rng = random.Random(seed + params.dollar_seed_offset)
    state = DollarLiquidityState(
        dollar_index=params.initial_dollar_index,
        previous_dollar_index=params.initial_dollar_index,
        liquidity_index=params.initial_liquidity_index,
        previous_liquidity_index=params.initial_liquidity_index,
        financial_conditions_index=params.initial_financial_conditions_index,
        risk_appetite_index=params.initial_risk_appetite_index,
        em_stress_index=params.initial_em_stress_index,
        dollar_funding_stress_index=params.initial_em_stress_index,
    )

    boundary_runs = {"dollar": 0, "financial_conditions": 0}
    combined: list[dict[str, Any]] = []

    for row in records:
        year_index = int(row["year_index"])
        gdp_growth = as_float(row, "realized_growth_pct")
        potential_growth = as_float(row, "potential_growth_pct", 2.0)
        output_gap = as_float(row, "output_gap_pct")
        stress = as_float(row, "financial_stress_index")
        crisis_intensity = as_float(row, "crisis_intensity")
        qe = as_float(row, "qe_liquidity_index")
        balance_sheet_impulse = as_float(row, "balance_sheet_impulse")
        policy_stance = as_float(row, "policy_stance_index")
        real_policy_rate = as_float(row, "real_policy_rate_pct")
        real_10y = as_float(row, "global_real_10y_yield_pct")
        ten_year_change = as_float(row, "duration_pressure_index") / 7.4
        term_spread = as_float(row, "term_spread_10y_2y_pct")
        inversion_pressure = as_float(row, "curve_inversion_pressure")
        term_premium = as_float(row, "term_premium_pct")
        yield_curve_dollar_impulse = as_float(row, "yield_curve_to_dollar_impulse")
        yield_curve_credit_impulse = as_float(row, "yield_curve_to_credit_impulse")
        equity_valuation_impulse = as_float(row, "yield_curve_to_equity_valuation_impulse")

        if year_index == 0:
            initial_record = DollarLiquidityRecord(
                dollar_liquidity_param_version=DOLLAR_LIQUIDITY_PARAM_VERSION,
                dollar_liquidity_interface_version=DOLLAR_LIQUIDITY_INTERFACE_VERSION,
                dollar_liquidity_boundary_version=DOLLAR_LIQUIDITY_BOUNDARY_VERSION,
                global_dollar_index=params.initial_dollar_index,
                unclamped_dollar_target_index=params.initial_dollar_index,
                dollar_floor_applied=False,
                dollar_cap_applied=False,
                dollar_consecutive_boundary_years=0,
                dollar_yoy_change_pct=0.0,
                dollar_momentum_index=0.0,
                global_liquidity_index=params.initial_liquidity_index,
                liquidity_impulse_index=0.0,
                global_financial_conditions_index=params.initial_financial_conditions_index,
                unclamped_financial_conditions_target_index=params.initial_financial_conditions_index,
                financial_conditions_floor_applied=False,
                financial_conditions_cap_applied=False,
                financial_conditions_consecutive_boundary_years=0,
                risk_appetite_index=params.initial_risk_appetite_index,
                em_stress_index=params.initial_em_stress_index,
                dollar_funding_stress_index=params.initial_em_stress_index,
                dollar_liquidity_regime="initial",
                dollar_to_import_inflation_impulse=0.0,
                dollar_to_oil_pressure_impulse=0.0,
                dollar_to_gdp_drag_placeholder=0.0,
                dollar_to_credit_tightening_impulse=0.0,
                liquidity_to_equity_impulse=0.0,
                liquidity_to_credit_easing_impulse=0.0,
            )
            combined.append(round_record({**row, **asdict(initial_record)}))
            continue

        safe_haven_pressure = clamp(crisis_intensity + max(0.0, stress - 48.0) / 52.0, 0.0, 1.6)
        dollar_target = (
            params.base_dollar_index
            + params.dollar_real_rate_beta * real_10y
            + params.dollar_policy_stance_beta * policy_stance
            + params.dollar_safe_haven_beta * safe_haven_pressure
            + params.dollar_stress_beta * max(0.0, stress - 35.0)
            + params.dollar_inversion_beta * inversion_pressure
            + params.dollar_yield_curve_impulse_beta * yield_curve_dollar_impulse
            - params.dollar_qe_beta * qe
            - 0.60 * max(0.0, gdp_growth - potential_growth)
            + rng.gauss(0.0, params.noise_scale)
        )
        unclamped_dollar_next = smooth(state.dollar_index, dollar_target, params.dollar_speed)
        dollar_floor_applied, dollar_cap_applied = boundary_flags(
            unclamped_dollar_next, params.min_dollar_index, params.max_dollar_index
        )
        dollar_index = clamp(
            unclamped_dollar_next, params.min_dollar_index, params.max_dollar_index
        )
        boundary_runs["dollar"] = advance_boundary_run(
            boundary_runs["dollar"], dollar_floor_applied, dollar_cap_applied
        )
        dollar_yoy = pct_change(dollar_index, state.dollar_index)
        dollar_momentum = clamp(dollar_yoy * 2.2 + (dollar_index - 100.0) * 0.22, -20.0, 20.0)

        liquidity_target = (
            55.0
            + params.liquidity_qe_beta * qe
            + params.liquidity_balance_sheet_beta * balance_sheet_impulse
            - params.liquidity_real_rate_beta * max(0.0, real_10y)
            - 1.35 * max(0.0, real_policy_rate)
            - params.liquidity_dollar_drag_beta * max(0.0, dollar_index - 100.0)
            - params.liquidity_stress_drag_beta * max(0.0, stress - 35.0)
            - 3.0 * max(0.0, term_premium - 0.75)
            + 1.5 * max(0.0, -term_spread)
            + rng.gauss(0.0, params.noise_scale * 0.65)
        )
        liquidity_index = clamp(smooth(state.liquidity_index, liquidity_target, params.liquidity_speed), 0.0, 100.0)
        liquidity_impulse = liquidity_index - state.liquidity_index

        fci_target = (
            params.fci_dollar_beta * (dollar_index - 100.0)
            + params.fci_real_rate_beta * real_10y
            + params.fci_policy_stance_beta * policy_stance
            + params.fci_stress_beta * max(0.0, stress - 35.0)
            + params.fci_inversion_beta * inversion_pressure
            + 0.36 * max(0.0, yield_curve_credit_impulse)
            + 0.24 * max(0.0, ten_year_change)
            - params.fci_liquidity_ease_beta * (liquidity_index - 50.0)
        )
        unclamped_financial_conditions_next = smooth(
            state.financial_conditions_index, fci_target, params.financial_conditions_speed
        )
        financial_conditions_floor_applied, financial_conditions_cap_applied = boundary_flags(
            unclamped_financial_conditions_next,
            params.min_financial_conditions_index,
            params.max_financial_conditions_index,
        )
        financial_conditions = clamp(
            unclamped_financial_conditions_next,
            params.min_financial_conditions_index,
            params.max_financial_conditions_index,
        )
        boundary_runs["financial_conditions"] = advance_boundary_run(
            boundary_runs["financial_conditions"],
            financial_conditions_floor_applied,
            financial_conditions_cap_applied,
        )

        risk_target = (
            50.0
            - params.risk_fci_beta * financial_conditions
            - params.risk_stress_beta * max(0.0, stress - 35.0)
            - params.risk_crisis_beta * crisis_intensity
            + params.risk_growth_beta * (gdp_growth - potential_growth)
            + 0.28 * (liquidity_index - 50.0)
            - 0.16 * max(0.0, dollar_index - 100.0)
            + 5.0 * max(0.0, equity_valuation_impulse)
            + rng.gauss(0.0, params.noise_scale)
        )
        risk_appetite = clamp(smooth(state.risk_appetite_index, risk_target, params.risk_appetite_speed), 0.0, 100.0)

        em_stress_target = (
            34.0
            + 0.86 * max(0.0, dollar_index - 100.0)
            + 1.35 * max(0.0, dollar_momentum)
            + 8.5 * max(0.0, financial_conditions)
            + 0.28 * max(0.0, stress - 35.0)
            + 16.0 * crisis_intensity
            - 0.20 * (liquidity_index - 50.0)
            - 0.16 * max(0.0, output_gap)
        )
        em_stress = clamp(smooth(state.em_stress_index, em_stress_target, params.em_stress_speed), 0.0, 100.0)

        funding_stress_target = (
            32.0
            + 0.42 * stress
            + 1.15 * max(0.0, dollar_momentum)
            + 0.55 * inversion_pressure
            + 9.0 * max(0.0, financial_conditions)
            + 15.0 * crisis_intensity
            - 0.24 * liquidity_index
        )
        funding_stress = clamp(
            smooth(state.dollar_funding_stress_index, funding_stress_target, params.funding_stress_speed),
            0.0,
            100.0,
        )

        regime = classify_dollar_liquidity_regime(
            year_index=year_index,
            dollar_index=dollar_index,
            dollar_momentum=dollar_momentum,
            liquidity_index=liquidity_index,
            liquidity_impulse=liquidity_impulse,
            financial_conditions=financial_conditions,
            risk_appetite=risk_appetite,
            em_stress=em_stress,
            funding_stress=funding_stress,
            crisis_intensity=crisis_intensity,
            qe_liquidity_index=qe,
        )

        dollar_to_import_inflation = clamp(
            -0.018 * (dollar_index - 100.0) - 0.030 * dollar_momentum,
            -1.0,
            1.0,
        )
        dollar_to_oil_pressure = clamp(
            -0.015 * (dollar_index - 100.0)
            - 0.032 * dollar_momentum
            + 0.018 * (risk_appetite - 50.0)
            + 0.008 * liquidity_impulse,
            -1.5,
            1.5,
        )
        dollar_to_gdp_drag = clamp(
            -0.045 * max(0.0, dollar_index - 102.0)
            - 0.060 * max(0.0, financial_conditions)
            - 0.010 * max(0.0, em_stress - 50.0),
            -1.5,
            0.35,
        )
        dollar_credit_tightening = clamp(
            0.030 * max(0.0, dollar_index - 100.0)
            + 0.045 * max(0.0, dollar_momentum)
            + 0.25 * max(0.0, financial_conditions)
            + 0.012 * max(0.0, funding_stress - 45.0),
            -1.0,
            2.0,
        )
        liquidity_to_equity = clamp(
            0.030 * (liquidity_index - 50.0)
            + 0.028 * (risk_appetite - 50.0)
            - 0.40 * max(0.0, financial_conditions)
            - 0.025 * max(0.0, dollar_index - 103.0),
            -2.0,
            2.0,
        )
        liquidity_to_credit_easing = clamp(
            0.026 * (liquidity_index - 50.0)
            - 0.30 * max(0.0, financial_conditions)
            - 0.018 * max(0.0, funding_stress - 45.0),
            -2.0,
            2.0,
        )

        record = DollarLiquidityRecord(
            dollar_liquidity_param_version=DOLLAR_LIQUIDITY_PARAM_VERSION,
            dollar_liquidity_interface_version=DOLLAR_LIQUIDITY_INTERFACE_VERSION,
            dollar_liquidity_boundary_version=DOLLAR_LIQUIDITY_BOUNDARY_VERSION,
            global_dollar_index=dollar_index,
            unclamped_dollar_target_index=dollar_target,
            dollar_floor_applied=dollar_floor_applied,
            dollar_cap_applied=dollar_cap_applied,
            dollar_consecutive_boundary_years=boundary_runs["dollar"],
            dollar_yoy_change_pct=dollar_yoy,
            dollar_momentum_index=dollar_momentum,
            global_liquidity_index=liquidity_index,
            liquidity_impulse_index=liquidity_impulse,
            global_financial_conditions_index=financial_conditions,
            unclamped_financial_conditions_target_index=fci_target,
            financial_conditions_floor_applied=financial_conditions_floor_applied,
            financial_conditions_cap_applied=financial_conditions_cap_applied,
            financial_conditions_consecutive_boundary_years=boundary_runs["financial_conditions"],
            risk_appetite_index=risk_appetite,
            em_stress_index=em_stress,
            dollar_funding_stress_index=funding_stress,
            dollar_liquidity_regime=regime,
            dollar_to_import_inflation_impulse=dollar_to_import_inflation,
            dollar_to_oil_pressure_impulse=dollar_to_oil_pressure,
            dollar_to_gdp_drag_placeholder=dollar_to_gdp_drag,
            dollar_to_credit_tightening_impulse=dollar_credit_tightening,
            liquidity_to_equity_impulse=liquidity_to_equity,
            liquidity_to_credit_easing_impulse=liquidity_to_credit_easing,
        )
        combined.append(round_record({**row, **asdict(record)}))

        state.previous_dollar_index = state.dollar_index
        state.dollar_index = dollar_index
        state.previous_liquidity_index = state.liquidity_index
        state.liquidity_index = liquidity_index
        state.financial_conditions_index = financial_conditions
        state.risk_appetite_index = risk_appetite
        state.em_stress_index = em_stress
        state.dollar_funding_stress_index = funding_stress

    return combined


def summarize_seed(records: list[dict[str, Any]]) -> dict[str, Any]:
    data = records[1:] if len(records) > 1 else records
    dollar_values = [as_float(row, "global_dollar_index") for row in data]
    liquidity_values = [as_float(row, "global_liquidity_index") for row in data]
    fci_values = [as_float(row, "global_financial_conditions_index") for row in data]
    max_dollar_row = max(data, key=lambda row: as_float(row, "global_dollar_index")) if data else records[-1]
    min_liquidity_row = min(data, key=lambda row: as_float(row, "global_liquidity_index")) if data else records[-1]
    dollar_squeeze_years = sum(1 for row in data if str(row["dollar_liquidity_regime"]) in {"crisis_dollar_squeeze", "safe_haven_dollar_bid", "em_dollar_pressure"})
    easy_liquidity_years = sum(1 for row in data if str(row["dollar_liquidity_regime"]) in {"liquidity_easing_reflation", "dollar_bear_liquidity_wave", "risk_on_liquidity_expansion", "easy_dollar_liquidity"})
    final = records[-1]
    return {
        "seed": int(final["seed"]),
        "start_year": int(records[0]["year"]),
        "end_year": int(final["year"]),
        "average_dollar_index": round(mean(dollar_values), 3) if dollar_values else 0.0,
        "average_liquidity_index": round(mean(liquidity_values), 3) if liquidity_values else 0.0,
        "average_financial_conditions_index": round(mean(fci_values), 3) if fci_values else 0.0,
        "max_dollar_index": as_float(max_dollar_row, "global_dollar_index"),
        "max_dollar_year": int(max_dollar_row["year"]),
        "min_liquidity_index": as_float(min_liquidity_row, "global_liquidity_index"),
        "min_liquidity_year": int(min_liquidity_row["year"]),
        "dollar_squeeze_years": dollar_squeeze_years,
        "easy_liquidity_years": easy_liquidity_years,
        "final_dollar_index": as_float(final, "global_dollar_index"),
        "final_liquidity_index": as_float(final, "global_liquidity_index"),
        "final_financial_conditions_index": as_float(final, "global_financial_conditions_index"),
        "final_dollar_liquidity_regime": str(final["dollar_liquidity_regime"]),
    }


def write_viewer_data_js(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(rows, ensure_ascii=False, separators=(",", ":"))
    path.write_text(f"window.GLOBAL_DOLLAR_LIQUIDITY_DATA = {payload};\n", encoding="utf-8")


def build_dollar_liquidity_svg(records_by_seed: dict[int, list[dict[str, Any]]], path: Path) -> None:
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
    values = [as_float(row, "global_dollar_index") for row in all_records]
    min_year, max_year = min(years), max(years)
    min_value = min(90.0, min(values) - 2.0)
    max_value = max(110.0, max(values) + 2.0)

    def x_of(year: int) -> float:
        return left + (year - min_year) / max(1, max_year - min_year) * plot_w

    def y_of(value: float) -> float:
        return top + (max_value - value) / max(1e-9, max_value - min_value) * plot_h

    palette = ["#38bdf8", "#facc15", "#a78bfa", "#34d399", "#fb7185", "#f59e0b", "#f472b6", "#eab308"]
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#07090d"/>',
        f'<text x="{left}" y="27" font-family="Arial" font-size="20" fill="#f5f7fb">Global Dollar Index Paths by Seed</text>',
        f'<text x="{left}" y="50" font-family="Arial" font-size="12" fill="#94a3b8">Dollar pressure after GDP, inflation, policy, yield curve, QE, and stress dynamics</text>',
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
            f'{x_of(int(row["year"])):.2f},{y_of(as_float(row, "global_dollar_index")):.2f}'
            for row in records
        )
        lines.append(f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round"/>')
        last = records[-1]
        lines.append(
            f'<text x="{x_of(int(last["year"])) + 6:.2f}" y="{y_of(as_float(last, "global_dollar_index")) + 4:.2f}" '
            f'font-family="Arial" font-size="11" fill="{color}">seed {seed}</text>'
        )

    lines.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}" stroke="#64748b"/>')
    lines.append(f'<line x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}" stroke="#64748b"/>')
    lines.append(f'<text x="18" y="{top + plot_h / 2}" transform="rotate(-90 18 {top + plot_h / 2})" text-anchor="middle" font-family="Arial" font-size="12" fill="#94a3b8">dollar index</text>')
    lines.append("</svg>")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a combined global GDP + inflation + policy-rate + yield-curve + dollar-liquidity annual simulation.",
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
    dollar_liquidity_params = DollarLiquidityParams()

    records_by_seed: dict[int, list[dict[str, Any]]] = {}
    for seed in seeds:
        gdp_records = simulate_global_gdp(seed, gdp_params)
        inflation_records = simulate_inflation_for_gdp_path(seed, gdp_records, inflation_params)
        policy_records = simulate_policy_for_macro_path(inflation_records, policy_params)
        yield_records = simulate_yield_curve_for_policy_path(policy_records, yield_curve_params)
        records_by_seed[seed] = simulate_dollar_liquidity_for_yield_path(yield_records, dollar_liquidity_params)

    all_records = [row for records in records_by_seed.values() for row in records]
    summaries = [summarize_seed(records) for records in records_by_seed.values()]

    args.output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = args.output_dir / "global_dollar_liquidity_seed_sweep.csv"
    json_path = args.output_dir / "global_dollar_liquidity_seed_sweep.json"
    viewer_data_path = args.output_dir / "global_dollar_liquidity_viewer_data.js"
    svg_path = args.output_dir / "global_dollar_liquidity_curves.svg"

    write_csv(csv_path, all_records, COMBINED_DOLLAR_LIQUIDITY_FIELDS)
    write_json(
        json_path,
        {
            "gdp_param_version": all_records[0]["param_version"] if all_records else "",
            "inflation_param_version": INFLATION_PARAM_VERSION,
            "policy_param_version": POLICY_PARAM_VERSION,
            "yield_curve_param_version": YIELD_CURVE_PARAM_VERSION,
            "dollar_liquidity_param_version": DOLLAR_LIQUIDITY_PARAM_VERSION,
            "dollar_liquidity_interface_version": DOLLAR_LIQUIDITY_INTERFACE_VERSION,
            "gdp_params": asdict(gdp_params),
            "inflation_params": asdict(inflation_params),
            "policy_params": asdict(policy_params),
            "yield_curve_params": asdict(yield_curve_params),
            "dollar_liquidity_params": asdict(dollar_liquidity_params),
            "seeds": seeds,
            "summary": summaries,
            "model_note": {
                "coupling": "Dollar/liquidity is downstream of GDP, inflation, policy, and the yield curve. It reads real rates, yield-curve dollar impulse, QE, balance-sheet impulse, crisis stress, and risk conditions.",
                "no_feedback_yet": "Dollar and liquidity impulses to inflation, oil, GDP, credit, and equity are emitted as placeholders only; upstream paths are not recomputed in v0.1.",
                "future_connection": "The dollar_to_* and liquidity_to_* fields are intended for later credit, equity, oil, EM, and multi-pass macro feedback layers.",
            },
        },
    )
    write_viewer_data_js(viewer_data_path, all_records)
    if not args.no_svg:
        build_dollar_liquidity_svg(records_by_seed, svg_path)

    print(f"Wrote {csv_path}")
    print(f"Wrote {json_path}")
    print(f"Wrote {viewer_data_path}")
    if not args.no_svg:
        print(f"Wrote {svg_path}")
    for summary in summaries:
        print(
            "seed={seed} avg_dollar={average_dollar_index:.1f} "
            "avg_liquidity={average_liquidity_index:.1f} "
            "squeeze_years={dollar_squeeze_years} easy_years={easy_liquidity_years} "
            "final_regime={final_dollar_liquidity_regime}".format(**summary)
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
