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
require_positive = simulation_utils.require_positive

import argparse
import json
import math
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean
from typing import Any

credit_spread_layer = import_module(f"{_SIBLING_PREFIX}global_credit_spread_layer_sim")
dollar_liquidity_layer = import_module(f"{_SIBLING_PREFIX}global_dollar_liquidity_layer_sim")
global_gdp_layer = import_module(f"{_SIBLING_PREFIX}global_gdp_annual_sim")
inflation_layer = import_module(f"{_SIBLING_PREFIX}global_inflation_annual_sim")
policy_rate_layer = import_module(f"{_SIBLING_PREFIX}global_policy_rate_layer_sim")
yield_curve_layer = import_module(f"{_SIBLING_PREFIX}global_yield_curve_layer_sim")

COMBINED_CREDIT_SPREAD_FIELDS = credit_spread_layer.COMBINED_CREDIT_SPREAD_FIELDS
CREDIT_SPREAD_PARAM_VERSION = credit_spread_layer.CREDIT_SPREAD_PARAM_VERSION
CreditSpreadParams = credit_spread_layer.CreditSpreadParams
simulate_credit_spreads_for_dollar_path = credit_spread_layer.simulate_credit_spreads_for_dollar_path
DOLLAR_LIQUIDITY_PARAM_VERSION = dollar_liquidity_layer.DOLLAR_LIQUIDITY_PARAM_VERSION
DollarLiquidityParams = dollar_liquidity_layer.DollarLiquidityParams
simulate_dollar_liquidity_for_yield_path = dollar_liquidity_layer.simulate_dollar_liquidity_for_yield_path
GDPParams = global_gdp_layer.GDPParams
simulate_global_gdp = global_gdp_layer.simulate_global_gdp
INFLATION_PARAM_VERSION = inflation_layer.INFLATION_PARAM_VERSION
InflationParams = inflation_layer.InflationParams
as_float = inflation_layer.as_float
simulate_inflation_for_gdp_path = inflation_layer.simulate_inflation_for_gdp_path
POLICY_PARAM_VERSION = policy_rate_layer.POLICY_PARAM_VERSION
PolicyRateParams = policy_rate_layer.PolicyRateParams
simulate_policy_for_macro_path = policy_rate_layer.simulate_policy_for_macro_path
YIELD_CURVE_PARAM_VERSION = yield_curve_layer.YIELD_CURVE_PARAM_VERSION
YieldCurveParams = yield_curve_layer.YieldCurveParams
simulate_yield_curve_for_policy_path = yield_curve_layer.simulate_yield_curve_for_policy_path


ASSET_PRICE_PARAM_VERSION = "global-asset-price-layer-v0.3"
ASSET_PRICE_INTERFACE_VERSION = "asset-price-feedback-interface-v0.3"
ASSET_PRICE_BOUNDARY_VERSION = "asset-price-boundary-repair-v1"


ASSET_PRICE_FIELDS = [
    "asset_price_param_version",
    "asset_price_interface_version",
    "asset_price_boundary_version",
    "global_equity_index",
    "equity_total_return_pct",
    "equity_earnings_index",
    "unclamped_equity_earnings_index_target",
    "equity_earnings_index_floor_applied",
    "equity_earnings_index_cap_applied",
    "equity_earnings_index_boundary_state",
    "equity_earnings_index_consecutive_boundary_years",
    "equity_eps_growth_pct",
    "equity_valuation_pe",
    "equity_risk_premium_pct",
    "unclamped_equity_risk_premium_pct_target",
    "equity_risk_premium_pct_floor_applied",
    "equity_risk_premium_pct_cap_applied",
    "equity_risk_premium_pct_boundary_state",
    "equity_risk_premium_pct_consecutive_boundary_years",
    "equity_drawdown_pct",
    "global_sovereign_bond_index",
    "sovereign_bond_total_return_pct",
    "global_corporate_bond_index",
    "corporate_bond_total_return_pct",
    "global_60_40_portfolio_index",
    "portfolio_60_40_total_return_pct",
    "asset_volatility_index",
    "asset_risk_regime",
    "asset_to_gdp_wealth_impulse",
    "asset_to_policy_financial_conditions_impulse",
    "asset_to_credit_risk_appetite_impulse",
    "asset_to_inflation_wealth_demand_impulse",
]


COMBINED_ASSET_PRICE_FIELDS = COMBINED_CREDIT_SPREAD_FIELDS + ASSET_PRICE_FIELDS


@dataclass(frozen=True)
class AssetPriceParams:
    initial_equity_index: float = 100.0
    initial_equity_earnings_index: float = 100.0
    initial_equity_pe: float = 18.0
    initial_sovereign_bond_index: float = 100.0
    initial_corporate_bond_index: float = 100.0
    initial_portfolio_60_40_index: float = 100.0
    earnings_growth_smooth: float = 0.38
    pe_smooth: float = 0.32
    equity_price_smooth: float = 0.38
    base_pe: float = 19.0
    min_pe: float = 8.5
    max_pe: float = 32.0
    real_rate_pe_beta: float = 1.65
    credit_pe_beta: float = 0.0025
    fci_pe_beta: float = 0.85
    liquidity_pe_beta: float = 0.075
    risk_appetite_pe_beta: float = 0.065
    dollar_pe_beta: float = 0.030
    dividend_yield_pct: float = 2.3
    sovereign_bond_return_scale: float = 0.68
    corporate_spread_duration_years: float = 4.2
    corporate_credit_beta: float = 0.55
    base_earnings_growth_pct: float = 1.20
    asset_seed_offset: int = 15_300_181
    noise_scale: float = 0.90


def validate_initial_parameters(params: AssetPriceParams) -> None:
    for name, value in (
        ("initial_equity_index", params.initial_equity_index),
        ("initial_equity_earnings_index", params.initial_equity_earnings_index),
        ("initial_sovereign_bond_index", params.initial_sovereign_bond_index),
        ("initial_corporate_bond_index", params.initial_corporate_bond_index),
        ("initial_portfolio_60_40_index", params.initial_portfolio_60_40_index),
    ):
        require_positive(name, value)
    require_in_range("initial_equity_pe", params.initial_equity_pe, params.min_pe, params.max_pe)


@dataclass
class AssetPriceState:
    equity_index: float = 100.0
    equity_earnings_index: float = 100.0
    equity_pe: float = 18.0
    equity_peak_index: float = 100.0
    sovereign_bond_index: float = 100.0
    corporate_bond_index: float = 100.0
    portfolio_60_40_index: float = 100.0
    previous_ig_spread_bps: float = 115.0
    previous_hy_spread_bps: float = 420.0
    previous_equity_return_pct: float = 0.0


@dataclass
class AssetPriceRecord:
    asset_price_param_version: str
    asset_price_interface_version: str
    asset_price_boundary_version: str
    global_equity_index: float
    equity_total_return_pct: float
    equity_earnings_index: float
    unclamped_equity_earnings_index_target: float
    equity_earnings_index_floor_applied: bool
    equity_earnings_index_cap_applied: bool
    equity_earnings_index_boundary_state: str
    equity_earnings_index_consecutive_boundary_years: int
    equity_eps_growth_pct: float
    equity_valuation_pe: float
    equity_risk_premium_pct: float
    unclamped_equity_risk_premium_pct_target: float
    equity_risk_premium_pct_floor_applied: bool
    equity_risk_premium_pct_cap_applied: bool
    equity_risk_premium_pct_boundary_state: str
    equity_risk_premium_pct_consecutive_boundary_years: int
    equity_drawdown_pct: float
    global_sovereign_bond_index: float
    sovereign_bond_total_return_pct: float
    global_corporate_bond_index: float
    corporate_bond_total_return_pct: float
    global_60_40_portfolio_index: float
    portfolio_60_40_total_return_pct: float
    asset_volatility_index: float
    asset_risk_regime: str
    asset_to_gdp_wealth_impulse: float
    asset_to_policy_financial_conditions_impulse: float
    asset_to_credit_risk_appetite_impulse: float
    asset_to_inflation_wealth_demand_impulse: float



def smooth(old: float, target: float, speed: float) -> float:
    return old * (1.0 - speed) + target * speed


def hard_boundary_state(value: float, floor: float, cap: float | None) -> tuple[bool, bool, str]:
    floor_applied = value < floor
    cap_applied = cap is not None and value > cap
    if floor_applied:
        return True, False, "floor"
    if cap_applied:
        return False, True, "cap"
    return False, False, "none"


def advance_boundary_run(previous: int, state: str) -> int:
    return previous + 1 if state != "none" else 0


def soft_upper_saturate(value: float, knee: float, asymptote: float) -> float:
    if value <= knee:
        return value
    width = asymptote - knee
    return knee + width * (1.0 - math.exp(-(value - knee) / width))


def pct_change(current: float, previous: float) -> float:
    if previous <= 0.0:
        return 0.0
    return (current / previous - 1.0) * 100.0


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


def classify_asset_risk_regime(
    *,
    year_index: int,
    equity_return: float,
    sovereign_return: float,
    corporate_return: float,
    pe_change: float,
    drawdown: float,
    headline_inflation: float,
    real_10y: float,
    liquidity_index: float,
    risk_appetite: float,
    hy_spread: float,
    credit_regime: str,
    crisis_intensity: float,
) -> str:
    if year_index == 0:
        return "initial"
    if equity_return <= -18.0 and (hy_spread >= 850.0 or crisis_intensity >= 0.65):
        return "equity_credit_crash"
    if equity_return <= -5.0 and sovereign_return <= -3.0 and headline_inflation >= 3.5:
        return "stock_bond_inflation_shock"
    if sovereign_return >= 8.0 and equity_return <= 0.0:
        return "bond_rally_recession_hedge"
    if equity_return >= 9.0 and liquidity_index >= 64.0 and risk_appetite >= 56.0:
        return "liquidity_equity_bull"
    if equity_return >= 6.0 and sovereign_return >= 0.0 and headline_inflation <= 3.4:
        return "goldilocks_asset_rally"
    if drawdown <= -25.0 and equity_return > 6.0:
        return "bear_market_rebound"
    if pe_change <= -0.8 and real_10y >= 0.8:
        return "valuation_compression"
    if credit_regime in {"credit_squeeze", "funding_stress_credit_shock", "recession_default_wave"} and corporate_return < sovereign_return:
        return "credit_drag_risk_off"
    if equity_return <= -6.0:
        return "equity_risk_off"
    if corporate_return >= 5.0 and equity_return >= 3.0:
        return "credit_beta_rally"
    return "normal_asset_cycle"


def simulate_asset_prices_for_credit_path(
    records: list[dict[str, Any]],
    params: AssetPriceParams,
) -> list[dict[str, Any]]:
    validate_initial_parameters(params)
    if not records:
        return []

    seed = int(records[0].get("seed", 0))
    rng = random.Random(seed + params.asset_seed_offset)
    state = AssetPriceState(
        equity_index=params.initial_equity_index,
        equity_earnings_index=params.initial_equity_earnings_index,
        equity_pe=params.initial_equity_pe,
        equity_peak_index=params.initial_equity_index,
        sovereign_bond_index=params.initial_sovereign_bond_index,
        corporate_bond_index=params.initial_corporate_bond_index,
        portfolio_60_40_index=params.initial_portfolio_60_40_index,
    )

    combined: list[dict[str, Any]] = []
    boundary_runs = {
        "equity_earnings_index": 0,
        "equity_risk_premium_pct": 0,
    }

    for row in records:
        year_index = int(row["year_index"])
        gdp_growth = as_float(row, "realized_growth_pct")
        potential_growth = as_float(row, "potential_growth_pct", 2.0)
        output_gap = as_float(row, "output_gap_pct")
        headline = as_float(row, "headline_inflation_pct", 2.35)
        core = as_float(row, "core_inflation_pct", 2.2)
        crisis_intensity = as_float(row, "crisis_intensity")
        real_10y = as_float(row, "global_real_10y_yield_pct")
        ten_year_yield = as_float(row, "global_10y_yield_pct")
        policy_stance = as_float(row, "policy_stance_index")
        yield_bond_return = as_float(row, "bond_total_return_pct")
        liquidity_index = as_float(row, "global_liquidity_index", 55.0)
        liquidity_impulse = as_float(row, "liquidity_impulse_index")
        financial_conditions = as_float(row, "global_financial_conditions_index")
        risk_appetite = as_float(row, "risk_appetite_index", 50.0)
        dollar_index = as_float(row, "global_dollar_index", 100.0)
        hy_spread = as_float(row, "global_high_yield_spread_bps", 420.0)
        ig_spread = as_float(row, "global_investment_grade_spread_bps", 115.0)
        credit_spread_change = as_float(row, "credit_spread_change_bps")
        default_risk = as_float(row, "default_risk_index", 30.0)
        credit_availability = as_float(row, "credit_availability_index", 58.0)
        credit_impairment = as_float(row, "credit_impairment_stock_index")
        credit_equity_impulse = as_float(row, "credit_to_equity_risk_premium_impulse")
        yield_equity_impulse = as_float(row, "yield_curve_to_equity_valuation_impulse")
        liquidity_equity_impulse = as_float(row, "liquidity_to_equity_impulse")
        credit_regime = str(row.get("credit_regime", "none"))

        if year_index == 0:
            initial_record = AssetPriceRecord(
                asset_price_param_version=ASSET_PRICE_PARAM_VERSION,
                asset_price_interface_version=ASSET_PRICE_INTERFACE_VERSION,
                asset_price_boundary_version=ASSET_PRICE_BOUNDARY_VERSION,
                global_equity_index=params.initial_equity_index,
                equity_total_return_pct=0.0,
                equity_earnings_index=params.initial_equity_earnings_index,
                unclamped_equity_earnings_index_target=params.initial_equity_earnings_index,
                equity_earnings_index_floor_applied=False,
                equity_earnings_index_cap_applied=False,
                equity_earnings_index_boundary_state="none",
                equity_earnings_index_consecutive_boundary_years=0,
                equity_eps_growth_pct=0.0,
                equity_valuation_pe=params.initial_equity_pe,
                equity_risk_premium_pct=4.8,
                unclamped_equity_risk_premium_pct_target=4.8,
                equity_risk_premium_pct_floor_applied=False,
                equity_risk_premium_pct_cap_applied=False,
                equity_risk_premium_pct_boundary_state="none",
                equity_risk_premium_pct_consecutive_boundary_years=0,
                equity_drawdown_pct=0.0,
                global_sovereign_bond_index=params.initial_sovereign_bond_index,
                sovereign_bond_total_return_pct=0.0,
                global_corporate_bond_index=params.initial_corporate_bond_index,
                corporate_bond_total_return_pct=0.0,
                global_60_40_portfolio_index=params.initial_portfolio_60_40_index,
                portfolio_60_40_total_return_pct=0.0,
                asset_volatility_index=0.0,
                asset_risk_regime="initial",
                asset_to_gdp_wealth_impulse=0.0,
                asset_to_policy_financial_conditions_impulse=0.0,
                asset_to_credit_risk_appetite_impulse=0.0,
                asset_to_inflation_wealth_demand_impulse=0.0,
            )
            combined.append(round_record({**row, **asdict(initial_record)}))
            continue

        margin_pressure = max(0.0, headline - 4.0) * 0.65 + max(0.0, core - 3.5) * 0.35
        earnings_growth_target = (
            params.base_earnings_growth_pct
            + 1.15 * gdp_growth
            + 0.28 * headline
            + 0.42 * output_gap
            - 1.20 * max(0.0, potential_growth - gdp_growth)
            - 2.20 * max(0.0, -gdp_growth)
            - margin_pressure
            - 0.009 * max(0.0, hy_spread - 450.0)
            - 0.025 * credit_impairment
            - 0.40 * max(0.0, dollar_index - 103.0)
            + rng.gauss(0.0, params.noise_scale)
        )
        eps_growth = clamp(smooth(0.0, earnings_growth_target, params.earnings_growth_smooth), -24.0, 28.0)
        unclamped_equity_earnings_index_target = (
            state.equity_earnings_index * (1.0 + eps_growth / 100.0)
        )
        equity_earnings_index_floor_applied = (
            unclamped_equity_earnings_index_target < 45.0
        )
        equity_earnings_index_cap_applied = False
        equity_earnings_index_boundary_state = (
            "floor" if equity_earnings_index_floor_applied else "none"
        )
        earnings_index = max(45.0, unclamped_equity_earnings_index_target)
        boundary_runs["equity_earnings_index"] = advance_boundary_run(
            boundary_runs["equity_earnings_index"], equity_earnings_index_boundary_state
        )

        unclamped_equity_risk_premium_pct_target = (
            4.8
            + 0.018 * max(0.0, hy_spread - 420.0)
            + 0.035 * max(0.0, default_risk - 35.0)
            + 0.42 * max(0.0, financial_conditions)
            + 0.65 * max(0.0, credit_equity_impulse)
            + 0.007 * credit_impairment
            - 0.012 * max(0.0, liquidity_index - 55.0)
            - 0.018 * max(0.0, risk_appetite - 50.0)
        )
        if unclamped_equity_risk_premium_pct_target < 2.5:
            equity_risk_premium_pct_floor_applied = True
            equity_risk_premium_pct_cap_applied = False
            equity_risk_premium_pct_boundary_state = "floor"
            equity_risk_premium = 2.5
        elif unclamped_equity_risk_premium_pct_target > 8.0:
            equity_risk_premium_pct_floor_applied = False
            equity_risk_premium_pct_cap_applied = True
            equity_risk_premium_pct_boundary_state = "soft_cap"
            equity_risk_premium = soft_upper_saturate(
                unclamped_equity_risk_premium_pct_target, 8.0, 11.8
            )
        else:
            equity_risk_premium_pct_floor_applied = False
            equity_risk_premium_pct_cap_applied = False
            equity_risk_premium_pct_boundary_state = "none"
            equity_risk_premium = unclamped_equity_risk_premium_pct_target
        equity_risk_premium = clamp(equity_risk_premium, 2.5, 12.0)
        boundary_runs["equity_risk_premium_pct"] = advance_boundary_run(
            boundary_runs["equity_risk_premium_pct"],
            equity_risk_premium_pct_boundary_state,
        )
        pe_target = (
            params.base_pe
            - params.real_rate_pe_beta * max(0.0, real_10y)
            - params.credit_pe_beta * max(0.0, hy_spread - 420.0)
            - params.fci_pe_beta * max(0.0, financial_conditions)
            - 0.65 * max(0.0, policy_stance)
            - params.dollar_pe_beta * max(0.0, dollar_index - 100.0)
            - 0.85 * max(0.0, credit_equity_impulse)
            - 0.018 * credit_impairment
            + params.liquidity_pe_beta * (liquidity_index - 55.0)
            + params.risk_appetite_pe_beta * (risk_appetite - 50.0)
            + 0.70 * max(0.0, yield_equity_impulse)
            + 0.55 * max(0.0, liquidity_equity_impulse)
            + rng.gauss(0.0, params.noise_scale * 0.35)
        )
        pe_target = clamp(pe_target, params.min_pe, params.max_pe)
        pe = smooth(state.equity_pe, pe_target, params.pe_smooth)
        pe_change = pe - state.equity_pe

        fair_equity_index = earnings_index * pe / params.initial_equity_pe
        equity_price_index = clamp(smooth(state.equity_index, fair_equity_index, params.equity_price_smooth), 20.0, 520.0)
        if year_index == 0:
            equity_return = 0.0
        else:
            equity_return = clamp(pct_change(equity_price_index, state.equity_index) + params.dividend_yield_pct, -45.0, 55.0)
        equity_index = clamp(state.equity_index * (1.0 + equity_return / 100.0), 20.0, 620.0)
        equity_peak = max(state.equity_peak_index, equity_index)
        equity_drawdown = clamp((equity_index / max(1e-9, equity_peak) - 1.0) * 100.0, -90.0, 0.0)

        if year_index == 0:
            sovereign_return = 0.0
        else:
            sovereign_return = clamp(
                params.sovereign_bond_return_scale * yield_bond_return
                - 0.35 * max(0.0, headline - 4.0)
                + 0.20 * max(0.0, crisis_intensity - 0.35) * 10.0,
                -26.0,
                24.0,
            )
        sovereign_bond_index = compound_index_with_soft_drag(
            state.sovereign_bond_index,
            sovereign_return,
            floor=30.0,
            soft_start=240.0,
        )

        ig_spread_change = ig_spread - state.previous_ig_spread_bps
        if year_index == 0:
            corporate_return = 0.0
        else:
            corporate_carry = 0.48 * ten_year_yield + 0.60 * (ig_spread / 100.0)
            spread_price_effect = -params.corporate_spread_duration_years * (ig_spread_change / 100.0)
            credit_drag = -params.corporate_credit_beta * max(0.0, credit_spread_change / 100.0)
            corporate_return = clamp(
                0.55 * sovereign_return + corporate_carry + spread_price_effect + credit_drag,
                -30.0,
                24.0,
            )
        corporate_bond_index = compound_index_with_soft_drag(
            state.corporate_bond_index,
            corporate_return,
            floor=25.0,
            soft_start=240.0,
        )

        portfolio_return = 0.60 * equity_return + 0.40 * sovereign_return
        portfolio_index = compound_index_with_soft_drag(
            state.portfolio_60_40_index,
            portfolio_return,
            floor=25.0,
            soft_start=360.0,
        )
        asset_volatility = clamp(
            12.0
            + 0.55 * abs(equity_return)
            + 0.30 * abs(sovereign_return)
            + 0.16 * max(0.0, hy_spread - 420.0) / 10.0
            + 0.20 * max(0.0, 50.0 - risk_appetite)
            + 0.12 * credit_impairment
            + 15.0 * crisis_intensity,
            5.0,
            100.0,
        )
        regime = classify_asset_risk_regime(
            year_index=year_index,
            equity_return=equity_return,
            sovereign_return=sovereign_return,
            corporate_return=corporate_return,
            pe_change=pe_change,
            drawdown=equity_drawdown,
            headline_inflation=headline,
            real_10y=real_10y,
            liquidity_index=liquidity_index,
            risk_appetite=risk_appetite,
            hy_spread=hy_spread,
            credit_regime=credit_regime,
            crisis_intensity=crisis_intensity,
        )

        wealth_impulse = clamp(
            0.018 * max(-25.0, min(25.0, equity_return))
            + 0.006 * max(-18.0, min(18.0, sovereign_return))
            - 0.012 * max(0.0, -equity_drawdown - 15.0),
            -1.5,
            1.2,
        )
        policy_fci_impulse = clamp(
            -0.012 * max(0.0, equity_return)
            + 0.020 * max(0.0, -equity_return)
            + 0.018 * max(0.0, -sovereign_return)
            + 0.012 * max(0.0, asset_volatility - 35.0),
            -1.0,
            1.5,
        )
        credit_risk_appetite_impulse = clamp(
            0.018 * equity_return
            + 0.006 * corporate_return
            - 0.010 * max(0.0, asset_volatility - 30.0),
            -1.5,
            1.5,
        )
        inflation_wealth_demand = clamp(
            0.010 * max(0.0, equity_return)
            + 0.004 * max(0.0, portfolio_return)
            - 0.012 * max(0.0, -equity_return),
            -0.8,
            0.8,
        )

        record = AssetPriceRecord(
            asset_price_param_version=ASSET_PRICE_PARAM_VERSION,
            asset_price_interface_version=ASSET_PRICE_INTERFACE_VERSION,
            asset_price_boundary_version=ASSET_PRICE_BOUNDARY_VERSION,
            global_equity_index=equity_index,
            equity_total_return_pct=equity_return,
            equity_earnings_index=earnings_index,
            unclamped_equity_earnings_index_target=unclamped_equity_earnings_index_target,
            equity_earnings_index_floor_applied=equity_earnings_index_floor_applied,
            equity_earnings_index_cap_applied=equity_earnings_index_cap_applied,
            equity_earnings_index_boundary_state=equity_earnings_index_boundary_state,
            equity_earnings_index_consecutive_boundary_years=boundary_runs["equity_earnings_index"],
            equity_eps_growth_pct=eps_growth,
            equity_valuation_pe=pe,
            equity_risk_premium_pct=equity_risk_premium,
            unclamped_equity_risk_premium_pct_target=unclamped_equity_risk_premium_pct_target,
            equity_risk_premium_pct_floor_applied=equity_risk_premium_pct_floor_applied,
            equity_risk_premium_pct_cap_applied=equity_risk_premium_pct_cap_applied,
            equity_risk_premium_pct_boundary_state=equity_risk_premium_pct_boundary_state,
            equity_risk_premium_pct_consecutive_boundary_years=boundary_runs["equity_risk_premium_pct"],
            equity_drawdown_pct=equity_drawdown,
            global_sovereign_bond_index=sovereign_bond_index,
            sovereign_bond_total_return_pct=sovereign_return,
            global_corporate_bond_index=corporate_bond_index,
            corporate_bond_total_return_pct=corporate_return,
            global_60_40_portfolio_index=portfolio_index,
            portfolio_60_40_total_return_pct=portfolio_return,
            asset_volatility_index=asset_volatility,
            asset_risk_regime=regime,
            asset_to_gdp_wealth_impulse=wealth_impulse,
            asset_to_policy_financial_conditions_impulse=policy_fci_impulse,
            asset_to_credit_risk_appetite_impulse=credit_risk_appetite_impulse,
            asset_to_inflation_wealth_demand_impulse=inflation_wealth_demand,
        )
        combined.append(round_record({**row, **asdict(record)}))

        state.equity_index = equity_index
        state.equity_earnings_index = earnings_index
        state.equity_pe = pe
        state.equity_peak_index = equity_peak
        state.sovereign_bond_index = sovereign_bond_index
        state.corporate_bond_index = corporate_bond_index
        state.portfolio_60_40_index = portfolio_index
        state.previous_ig_spread_bps = ig_spread
        state.previous_hy_spread_bps = hy_spread
        state.previous_equity_return_pct = equity_return

    return combined


def summarize_seed(records: list[dict[str, Any]]) -> dict[str, Any]:
    data = records[1:] if len(records) > 1 else records
    equity_returns = [as_float(row, "equity_total_return_pct") for row in data]
    sovereign_returns = [as_float(row, "sovereign_bond_total_return_pct") for row in data]
    max_equity_row = max(data, key=lambda row: as_float(row, "global_equity_index")) if data else records[-1]
    min_drawdown_row = min(data, key=lambda row: as_float(row, "equity_drawdown_pct")) if data else records[-1]
    selloff_years = sum(1 for row in data if str(row["asset_risk_regime"]) in {"equity_credit_crash", "stock_bond_inflation_shock", "equity_risk_off", "credit_drag_risk_off"})
    bull_years = sum(1 for row in data if str(row["asset_risk_regime"]) in {"liquidity_equity_bull", "goldilocks_asset_rally", "bear_market_rebound", "credit_beta_rally"})
    final = records[-1]
    return {
        "seed": int(final["seed"]),
        "start_year": int(records[0]["year"]),
        "end_year": int(final["year"]),
        "average_equity_return_pct": round(mean(equity_returns), 3) if equity_returns else 0.0,
        "average_sovereign_bond_return_pct": round(mean(sovereign_returns), 3) if sovereign_returns else 0.0,
        "max_equity_index": as_float(max_equity_row, "global_equity_index"),
        "max_equity_year": int(max_equity_row["year"]),
        "max_drawdown_pct": as_float(min_drawdown_row, "equity_drawdown_pct"),
        "max_drawdown_year": int(min_drawdown_row["year"]),
        "selloff_years": selloff_years,
        "bull_years": bull_years,
        "final_equity_index": as_float(final, "global_equity_index"),
        "final_sovereign_bond_index": as_float(final, "global_sovereign_bond_index"),
        "final_portfolio_60_40_index": as_float(final, "global_60_40_portfolio_index"),
        "final_asset_risk_regime": str(final["asset_risk_regime"]),
    }


def write_viewer_data_js(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(rows, ensure_ascii=False, separators=(",", ":"))
    path.write_text(f"window.GLOBAL_ASSET_PRICE_DATA = {payload};\n", encoding="utf-8")


def build_asset_price_svg(records_by_seed: dict[int, list[dict[str, Any]]], path: Path) -> None:
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
    values = [as_float(row, "global_equity_index") for row in all_records]
    min_year, max_year = min(years), max(years)
    min_value = max(20.0, min(values) * 0.90)
    max_value = max(140.0, max(values) * 1.10)

    def x_of(year: int) -> float:
        return left + (year - min_year) / max(1, max_year - min_year) * plot_w

    def y_of(value: float) -> float:
        return top + (max_value - value) / max(1e-9, max_value - min_value) * plot_h

    palette = ["#22c55e", "#38bdf8", "#facc15", "#a78bfa", "#fb923c", "#fb7185", "#f472b6", "#eab308"]
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#07090d"/>',
        f'<text x="{left}" y="27" font-family="Arial" font-size="20" fill="#f5f7fb">Global Equity Index Paths by Seed</text>',
        f'<text x="{left}" y="50" font-family="Arial" font-size="12" fill="#94a3b8">Equity index after earnings, valuation, real rates, credit risk, dollar, and liquidity dynamics</text>',
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
            f'{x_of(int(row["year"])):.2f},{y_of(as_float(row, "global_equity_index")):.2f}'
            for row in records
        )
        lines.append(f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round"/>')
        last = records[-1]
        lines.append(
            f'<text x="{x_of(int(last["year"])) + 6:.2f}" y="{y_of(as_float(last, "global_equity_index")) + 4:.2f}" '
            f'font-family="Arial" font-size="11" fill="{color}">seed {seed}</text>'
        )

    lines.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}" stroke="#64748b"/>')
    lines.append(f'<line x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}" stroke="#64748b"/>')
    lines.append(f'<text x="18" y="{top + plot_h / 2}" transform="rotate(-90 18 {top + plot_h / 2})" text-anchor="middle" font-family="Arial" font-size="12" fill="#94a3b8">equity index</text>')
    lines.append("</svg>")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a combined global GDP + inflation + policy + yield + dollar + credit + asset-price annual simulation.",
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
    credit_spread_params = CreditSpreadParams()
    asset_price_params = AssetPriceParams()

    records_by_seed: dict[int, list[dict[str, Any]]] = {}
    for seed in seeds:
        gdp_records = simulate_global_gdp(seed, gdp_params)
        inflation_records = simulate_inflation_for_gdp_path(seed, gdp_records, inflation_params)
        policy_records = simulate_policy_for_macro_path(inflation_records, policy_params)
        yield_records = simulate_yield_curve_for_policy_path(policy_records, yield_curve_params)
        dollar_records = simulate_dollar_liquidity_for_yield_path(yield_records, dollar_liquidity_params)
        credit_records = simulate_credit_spreads_for_dollar_path(dollar_records, credit_spread_params)
        records_by_seed[seed] = simulate_asset_prices_for_credit_path(credit_records, asset_price_params)

    all_records = [row for records in records_by_seed.values() for row in records]
    summaries = [summarize_seed(records) for records in records_by_seed.values()]

    args.output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = args.output_dir / "global_asset_price_seed_sweep.csv"
    json_path = args.output_dir / "global_asset_price_seed_sweep.json"
    viewer_data_path = args.output_dir / "global_asset_price_viewer_data.js"
    svg_path = args.output_dir / "global_asset_price_curves.svg"

    write_csv(csv_path, all_records, COMBINED_ASSET_PRICE_FIELDS)
    write_json(
        json_path,
        {
            "gdp_param_version": all_records[0]["param_version"] if all_records else "",
            "inflation_param_version": INFLATION_PARAM_VERSION,
            "policy_param_version": POLICY_PARAM_VERSION,
            "yield_curve_param_version": YIELD_CURVE_PARAM_VERSION,
            "dollar_liquidity_param_version": DOLLAR_LIQUIDITY_PARAM_VERSION,
            "credit_spread_param_version": CREDIT_SPREAD_PARAM_VERSION,
            "asset_price_param_version": ASSET_PRICE_PARAM_VERSION,
            "asset_price_interface_version": ASSET_PRICE_INTERFACE_VERSION,
            "gdp_params": asdict(gdp_params),
            "inflation_params": asdict(inflation_params),
            "policy_params": asdict(policy_params),
            "yield_curve_params": asdict(yield_curve_params),
            "dollar_liquidity_params": asdict(dollar_liquidity_params),
            "credit_spread_params": asdict(credit_spread_params),
            "asset_price_params": asdict(asset_price_params),
            "seeds": seeds,
            "summary": summaries,
            "model_note": {
                "coupling": "Asset prices are downstream of GDP, inflation, policy, yield curve, dollar, liquidity, and credit spreads.",
                "no_feedback_yet": "Asset impulses to GDP, policy financial conditions, credit risk appetite, and inflation demand are emitted as placeholders only; upstream paths are not recomputed in v0.1.",
                "future_connection": "The asset_to_* fields are intended for later multi-pass macro feedback, wealth effects, and portfolio allocation layers.",
            },
        },
    )
    write_viewer_data_js(viewer_data_path, all_records)
    if not args.no_svg:
        build_asset_price_svg(records_by_seed, svg_path)

    print(f"Wrote {csv_path}")
    print(f"Wrote {json_path}")
    print(f"Wrote {viewer_data_path}")
    if not args.no_svg:
        print(f"Wrote {svg_path}")
    for summary in summaries:
        print(
            "seed={seed} avg_eq_ret={average_equity_return_pct:.1f}% "
            "avg_bond_ret={average_sovereign_bond_return_pct:.1f}% "
            "selloffs={selloff_years} bulls={bull_years} "
            "final_regime={final_asset_risk_regime}".format(**summary)
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
