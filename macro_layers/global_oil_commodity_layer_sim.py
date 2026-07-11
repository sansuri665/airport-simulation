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

asset_price_layer = import_module(f"{_SIBLING_PREFIX}global_asset_price_layer_sim")
credit_spread_layer = import_module(f"{_SIBLING_PREFIX}global_credit_spread_layer_sim")
dollar_liquidity_layer = import_module(f"{_SIBLING_PREFIX}global_dollar_liquidity_layer_sim")
global_gdp_layer = import_module(f"{_SIBLING_PREFIX}global_gdp_annual_sim")
inflation_layer = import_module(f"{_SIBLING_PREFIX}global_inflation_annual_sim")
policy_rate_layer = import_module(f"{_SIBLING_PREFIX}global_policy_rate_layer_sim")
yield_curve_layer = import_module(f"{_SIBLING_PREFIX}global_yield_curve_layer_sim")

ASSET_PRICE_PARAM_VERSION = asset_price_layer.ASSET_PRICE_PARAM_VERSION
COMBINED_ASSET_PRICE_FIELDS = asset_price_layer.COMBINED_ASSET_PRICE_FIELDS
AssetPriceParams = asset_price_layer.AssetPriceParams
simulate_asset_prices_for_credit_path = asset_price_layer.simulate_asset_prices_for_credit_path
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


OIL_COMMODITY_PARAM_VERSION = "global-oil-commodity-layer-v0.1"
OIL_COMMODITY_INTERFACE_VERSION = "oil-commodity-feedback-interface-v0.1"


OIL_COMMODITY_FIELDS = [
    "oil_commodity_param_version",
    "oil_commodity_interface_version",
    "brent_oil_price_usd",
    "global_oil_price_index",
    "oil_yoy_change_pct",
    "broad_commodity_index",
    "commodity_yoy_change_pct",
    "oil_demand_pressure_index",
    "oil_supply_shock_index",
    "oil_inventory_pressure_index",
    "energy_cost_pressure_index",
    "oil_financial_pressure_index",
    "oil_regime",
    "oil_to_headline_inflation_impulse",
    "oil_to_gdp_drag_placeholder",
    "oil_to_credit_stress_impulse",
    "oil_to_policy_pressure_impulse",
    "commodity_to_terms_of_trade_impulse",
]


COMBINED_OIL_COMMODITY_FIELDS = COMBINED_ASSET_PRICE_FIELDS + OIL_COMMODITY_FIELDS


@dataclass(frozen=True)
class OilCommodityParams:
    initial_brent_price_usd: float = 82.0
    initial_oil_price_index: float = 100.0
    initial_broad_commodity_index: float = 100.0
    oil_seed_offset: int = 18_400_111
    demand_pressure_speed: float = 0.35
    supply_shock_speed: float = 0.42
    inventory_pressure_speed: float = 0.32
    energy_cost_pressure_speed: float = 0.40
    oil_return_speed: float = 0.44
    commodity_return_speed: float = 0.35
    supply_shortage_base_chance: float = 0.055
    supply_glut_base_chance: float = 0.025
    supply_event_min_duration: int = 1
    supply_event_max_duration: int = 4
    oil_price_floor_usd: float = 18.0
    oil_index_floor: float = 22.0
    broad_commodity_floor: float = 28.0
    noise_scale: float = 1.0


@dataclass
class OilCommodityState:
    brent_price_usd: float = 82.0
    oil_price_index: float = 100.0
    broad_commodity_index: float = 100.0
    oil_return_pct: float = 0.0
    commodity_return_pct: float = 0.0
    demand_pressure_index: float = 50.0
    supply_shock_index: float = 0.0
    inventory_pressure_index: float = 0.0
    energy_cost_pressure_index: float = 50.0
    supply_event_years_remaining: int = 0
    supply_event_target: float = 0.0


@dataclass
class OilCommodityRecord:
    oil_commodity_param_version: str
    oil_commodity_interface_version: str
    brent_oil_price_usd: float
    global_oil_price_index: float
    oil_yoy_change_pct: float
    broad_commodity_index: float
    commodity_yoy_change_pct: float
    oil_demand_pressure_index: float
    oil_supply_shock_index: float
    oil_inventory_pressure_index: float
    energy_cost_pressure_index: float
    oil_financial_pressure_index: float
    oil_regime: str
    oil_to_headline_inflation_impulse: float
    oil_to_gdp_drag_placeholder: float
    oil_to_credit_stress_impulse: float
    oil_to_policy_pressure_impulse: float
    commodity_to_terms_of_trade_impulse: float



def smooth(old: float, target: float, speed: float) -> float:
    return old * (1.0 - speed) + target * speed


def compound_index_with_soft_drag(
    previous: float,
    total_return_pct: float,
    *,
    floor: float,
    soft_start: float,
    softness: float = 0.55,
) -> float:
    adjusted_return = total_return_pct
    if total_return_pct > 0.0 and previous > soft_start:
        adjusted_return *= (soft_start / previous) ** softness
    return max(floor, previous * (1.0 + adjusted_return / 100.0))


def classify_oil_regime(
    *,
    year_index: int,
    oil_yoy: float,
    commodity_yoy: float,
    brent_price: float,
    demand_pressure: float,
    supply_shock: float,
    inventory_pressure: float,
    energy_pressure: float,
    gdp_growth: float,
    headline_inflation: float,
    dollar_index: float,
    liquidity_index: float,
    risk_appetite: float,
    crisis_intensity: float,
) -> str:
    if year_index == 0:
        return "initial"
    if oil_yoy >= 18.0 and headline_inflation >= 3.6 and gdp_growth <= 1.7:
        return "stagflationary_energy_squeeze"
    if supply_shock >= 24.0 and oil_yoy >= 16.0:
        return "geopolitical_oil_shock"
    if supply_shock <= -22.0 and oil_yoy <= -10.0:
        return "supply_glut_disinflation"
    if demand_pressure <= 38.0 and oil_yoy <= -14.0:
        return "oil_demand_slump"
    if demand_pressure >= 63.0 and commodity_yoy >= 10.0 and dollar_index <= 99.0:
        return "commodity_supercycle"
    if oil_yoy >= 12.0 and risk_appetite >= 58.0 and liquidity_index >= 60.0:
        return "risk_on_commodity_bid"
    if dollar_index >= 106.0 and oil_yoy <= 3.0:
        return "strong_dollar_oil_pressure"
    if energy_pressure >= 64.0 and headline_inflation >= 4.0:
        return "energy_inflation_pressure"
    if brent_price <= 45.0 and inventory_pressure <= -20.0:
        return "oil_glut_disinflation"
    if crisis_intensity >= 0.55 and oil_yoy < 0.0:
        return "crisis_oil_liquidation"
    return "normal_oil_cycle"


def maybe_update_supply_event(
    *,
    state: OilCommodityState,
    params: OilCommodityParams,
    rng: random.Random,
    year_index: int,
    gdp_growth: float,
    headline_inflation: float,
    dollar_index: float,
    crisis_intensity: float,
    energy_event_impulse: float,
) -> None:
    if year_index == 0:
        state.supply_event_target = 0.0
        state.supply_event_years_remaining = 0
        return

    if state.supply_event_years_remaining > 0:
        state.supply_event_years_remaining -= 1
        return

    state.supply_event_target *= 0.45
    shortage_chance = (
        params.supply_shortage_base_chance
        + 0.025 * crisis_intensity
        + 0.008 * max(0.0, headline_inflation - 4.0)
        + 0.012 * max(0.0, energy_event_impulse)
    )
    glut_chance = (
        params.supply_glut_base_chance
        + 0.010 * max(0.0, 1.0 - gdp_growth)
        + 0.002 * max(0.0, 100.0 - dollar_index)
        + 0.008 * max(0.0, -energy_event_impulse)
    )
    roll = rng.random()
    if roll < shortage_chance:
        state.supply_event_years_remaining = rng.randint(params.supply_event_min_duration, params.supply_event_max_duration)
        state.supply_event_target = rng.uniform(18.0, 42.0) * (1.0 + 0.45 * crisis_intensity) + 8.0 * max(0.0, energy_event_impulse)
    elif roll < shortage_chance + glut_chance:
        state.supply_event_years_remaining = rng.randint(2, params.supply_event_max_duration + 2)
        state.supply_event_target = -rng.uniform(16.0, 38.0) * (1.0 + 0.20 * max(0.0, 1.0 - gdp_growth))


def simulate_oil_commodities_for_asset_path(
    records: list[dict[str, Any]],
    params: OilCommodityParams,
) -> list[dict[str, Any]]:
    if not records:
        return []

    seed = int(records[0].get("seed", 0))
    rng = random.Random(seed + params.oil_seed_offset)
    state = OilCommodityState(
        brent_price_usd=params.initial_brent_price_usd,
        oil_price_index=params.initial_oil_price_index,
        broad_commodity_index=params.initial_broad_commodity_index,
    )

    combined: list[dict[str, Any]] = []
    for row in records:
        year_index = int(row["year_index"])
        gdp_growth = as_float(row, "realized_growth_pct")
        potential_growth = as_float(row, "potential_growth_pct", 2.0)
        output_gap = as_float(row, "output_gap_pct")
        headline = as_float(row, "headline_inflation_pct", 2.35)
        crisis_intensity = as_float(row, "crisis_intensity")
        financial_stress = as_float(row, "financial_stress_index", 30.0)
        energy_event_impulse = as_float(row, "energy_price_impulse")
        dollar_index = as_float(row, "global_dollar_index", 100.0)
        dollar_momentum = as_float(row, "dollar_momentum_index")
        dollar_oil_impulse = as_float(row, "dollar_to_oil_pressure_impulse")
        liquidity_index = as_float(row, "global_liquidity_index", 55.0)
        liquidity_impulse = as_float(row, "liquidity_impulse_index")
        financial_conditions = as_float(row, "global_financial_conditions_index")
        risk_appetite = as_float(row, "risk_appetite_index", 50.0)
        hy_spread = as_float(row, "global_high_yield_spread_bps", 420.0)
        credit_oil_impulse = as_float(row, "credit_to_oil_demand_impulse")
        equity_return = as_float(row, "equity_total_return_pct")
        asset_volatility = as_float(row, "asset_volatility_index", 18.0)

        maybe_update_supply_event(
            state=state,
            params=params,
            rng=rng,
            year_index=year_index,
            gdp_growth=gdp_growth,
            headline_inflation=headline,
            dollar_index=dollar_index,
            crisis_intensity=crisis_intensity,
            energy_event_impulse=energy_event_impulse,
        )

        price_demand_drag = (
            0.16 * max(0.0, state.brent_price_usd - 105.0)
            + 0.04 * max(0.0, state.oil_return_pct - 15.0)
            + 0.04 * max(0.0, asset_volatility - 38.0)
        )
        demand_target = (
            54.0
            + 4.3 * (gdp_growth - potential_growth)
            + 1.8 * output_gap
            + 0.18 * (risk_appetite - 50.0)
            + 0.12 * (liquidity_index - 50.0)
            + 0.09 * liquidity_impulse
            + 0.045 * equity_return
            + 3.0 * credit_oil_impulse
            - 7.0 * crisis_intensity
            - 0.010 * max(0.0, hy_spread - 500.0)
            - 0.10 * max(0.0, financial_stress - 40.0)
            - price_demand_drag
            + rng.gauss(0.0, params.noise_scale * 2.0)
        )
        demand_pressure = clamp(smooth(state.demand_pressure_index, demand_target, params.demand_pressure_speed), 0.0, 100.0)

        supply_target = (
            state.supply_event_target
            + 7.0 * energy_event_impulse
            + rng.gauss(0.0, params.noise_scale * 2.2)
        )
        supply_shock = clamp(smooth(state.supply_shock_index, supply_target, params.supply_shock_speed), -55.0, 70.0)

        inventory_target = (
            0.58 * (demand_pressure - 50.0)
            + 0.62 * supply_shock
            - 0.16 * (state.brent_price_usd - params.initial_brent_price_usd)
            - 0.14 * max(0.0, state.oil_return_pct)
        )
        inventory_pressure = clamp(
            smooth(state.inventory_pressure_index, inventory_target, params.inventory_pressure_speed),
            -65.0,
            80.0,
        )

        financial_pressure = clamp(
            -0.30 * (dollar_index - 100.0)
            - 0.42 * dollar_momentum
            + 0.16 * (liquidity_index - 50.0)
            + 0.13 * (risk_appetite - 50.0)
            - 3.2 * max(0.0, financial_conditions)
            + 5.5 * dollar_oil_impulse
            + 0.045 * equity_return
            - 0.020 * max(0.0, hy_spread - 500.0),
            -28.0,
            28.0,
        )

        price_level_gravity = -0.12 * max(0.0, state.brent_price_usd - 135.0) + 0.20 * max(0.0, 62.0 - state.brent_price_usd)
        oil_return_target = (
            1.2
            + 0.35 * headline
            + 0.44 * (demand_pressure - 50.0)
            + 0.82 * supply_shock
            + 0.28 * inventory_pressure
            + 0.38 * financial_pressure
            + 10.0 * energy_event_impulse
            + price_level_gravity
            + rng.gauss(0.0, params.noise_scale * 5.5)
        )
        if year_index == 0:
            oil_yoy = 0.0
            brent_price = params.initial_brent_price_usd
            oil_index = params.initial_oil_price_index
        else:
            oil_yoy = clamp(smooth(state.oil_return_pct, oil_return_target, params.oil_return_speed), -42.0, 85.0)
            brent_price = max(params.oil_price_floor_usd, state.brent_price_usd * (1.0 + oil_yoy / 100.0))
            oil_index = max(params.oil_index_floor, state.oil_price_index * (1.0 + oil_yoy / 100.0))

        commodity_return_target = (
            0.46 * oil_yoy
            + 0.20 * (demand_pressure - 50.0)
            + 0.17 * financial_pressure
            - 0.18 * (dollar_index - 100.0)
            + 0.06 * equity_return
            + rng.gauss(0.0, params.noise_scale * 3.0)
        )
        if year_index == 0:
            commodity_yoy = 0.0
            commodity_index = params.initial_broad_commodity_index
        else:
            commodity_yoy = clamp(
                smooth(state.commodity_return_pct, commodity_return_target, params.commodity_return_speed),
                -38.0,
                60.0,
            )
            commodity_index = compound_index_with_soft_drag(
                state.broad_commodity_index,
                commodity_yoy,
                floor=params.broad_commodity_floor,
                soft_start=260.0,
                softness=0.75,
            )

        energy_pressure_target = (
            50.0
            + 0.38 * (brent_price - params.initial_brent_price_usd)
            + 0.52 * oil_yoy
            + 0.28 * inventory_pressure
            + 0.18 * supply_shock
        )
        energy_pressure = clamp(
            smooth(state.energy_cost_pressure_index, energy_pressure_target, params.energy_cost_pressure_speed),
            0.0,
            100.0,
        )

        regime = classify_oil_regime(
            year_index=year_index,
            oil_yoy=oil_yoy,
            commodity_yoy=commodity_yoy,
            brent_price=brent_price,
            demand_pressure=demand_pressure,
            supply_shock=supply_shock,
            inventory_pressure=inventory_pressure,
            energy_pressure=energy_pressure,
            gdp_growth=gdp_growth,
            headline_inflation=headline,
            dollar_index=dollar_index,
            liquidity_index=liquidity_index,
            risk_appetite=risk_appetite,
            crisis_intensity=crisis_intensity,
        )

        headline_impulse = clamp(
            0.018 * oil_yoy + 0.010 * (energy_pressure - 50.0) + 0.004 * supply_shock,
            -1.4,
            2.4,
        )
        gdp_drag = clamp(
            -0.020 * max(0.0, oil_yoy - 15.0)
            - 0.018 * max(0.0, brent_price - 110.0)
            - 0.008 * max(0.0, energy_pressure - 65.0)
            + 0.014 * max(0.0, -oil_yoy - 10.0),
            -2.2,
            0.8,
        )
        credit_stress = clamp(
            0.012 * max(0.0, oil_yoy - 15.0)
            + 0.012 * max(0.0, energy_pressure - 65.0)
            + 0.006 * max(0.0, brent_price - 110.0)
            - 0.006 * max(0.0, -oil_yoy - 15.0),
            -0.8,
            1.8,
        )
        policy_pressure = clamp(
            0.016 * max(0.0, oil_yoy)
            + 0.010 * max(0.0, energy_pressure - 55.0)
            - 0.010 * max(0.0, -oil_yoy - 12.0),
            -1.0,
            1.8,
        )
        terms_of_trade = clamp(
            0.018 * commodity_yoy
            - 0.010 * (dollar_index - 100.0)
            + 0.004 * (demand_pressure - 50.0),
            -1.2,
            1.2,
        )

        record = OilCommodityRecord(
            oil_commodity_param_version=OIL_COMMODITY_PARAM_VERSION,
            oil_commodity_interface_version=OIL_COMMODITY_INTERFACE_VERSION,
            brent_oil_price_usd=brent_price,
            global_oil_price_index=oil_index,
            oil_yoy_change_pct=oil_yoy,
            broad_commodity_index=commodity_index,
            commodity_yoy_change_pct=commodity_yoy,
            oil_demand_pressure_index=demand_pressure,
            oil_supply_shock_index=supply_shock,
            oil_inventory_pressure_index=inventory_pressure,
            energy_cost_pressure_index=energy_pressure,
            oil_financial_pressure_index=financial_pressure,
            oil_regime=regime,
            oil_to_headline_inflation_impulse=headline_impulse,
            oil_to_gdp_drag_placeholder=gdp_drag,
            oil_to_credit_stress_impulse=credit_stress,
            oil_to_policy_pressure_impulse=policy_pressure,
            commodity_to_terms_of_trade_impulse=terms_of_trade,
        )
        combined.append(round_record({**row, **asdict(record)}))

        state.brent_price_usd = brent_price
        state.oil_price_index = oil_index
        state.broad_commodity_index = commodity_index
        state.oil_return_pct = oil_yoy
        state.commodity_return_pct = commodity_yoy
        state.demand_pressure_index = demand_pressure
        state.supply_shock_index = supply_shock
        state.inventory_pressure_index = inventory_pressure
        state.energy_cost_pressure_index = energy_pressure

    return combined


def summarize_seed(records: list[dict[str, Any]]) -> dict[str, Any]:
    data = records[1:] if len(records) > 1 else records
    oil_returns = [as_float(row, "oil_yoy_change_pct") for row in data]
    commodity_returns = [as_float(row, "commodity_yoy_change_pct") for row in data]
    max_oil_row = max(data, key=lambda row: as_float(row, "brent_oil_price_usd")) if data else records[-1]
    min_oil_row = min(data, key=lambda row: as_float(row, "brent_oil_price_usd")) if data else records[-1]
    shock_years = sum(
        1
        for row in data
        if str(row["oil_regime"])
        in {"geopolitical_oil_shock", "stagflationary_energy_squeeze", "energy_inflation_pressure"}
    )
    slump_years = sum(
        1
        for row in data
        if str(row["oil_regime"])
        in {"oil_demand_slump", "supply_glut_disinflation", "oil_glut_disinflation", "crisis_oil_liquidation"}
    )
    final = records[-1]
    return {
        "seed": int(final["seed"]),
        "start_year": int(records[0]["year"]),
        "end_year": int(final["year"]),
        "average_oil_yoy_change_pct": round(mean(oil_returns), 3) if oil_returns else 0.0,
        "average_commodity_yoy_change_pct": round(mean(commodity_returns), 3) if commodity_returns else 0.0,
        "max_brent_oil_price_usd": as_float(max_oil_row, "brent_oil_price_usd"),
        "max_brent_year": int(max_oil_row["year"]),
        "min_brent_oil_price_usd": as_float(min_oil_row, "brent_oil_price_usd"),
        "min_brent_year": int(min_oil_row["year"]),
        "shock_years": shock_years,
        "slump_years": slump_years,
        "final_brent_oil_price_usd": as_float(final, "brent_oil_price_usd"),
        "final_broad_commodity_index": as_float(final, "broad_commodity_index"),
        "final_oil_regime": str(final["oil_regime"]),
    }


def write_viewer_data_js(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(rows, ensure_ascii=False, separators=(",", ":"))
    path.write_text(f"window.GLOBAL_OIL_COMMODITY_DATA = {payload};\n", encoding="utf-8")


def build_oil_commodity_svg(records_by_seed: dict[int, list[dict[str, Any]]], path: Path) -> None:
    width = 1180
    height = 680
    left = 78
    right = 38
    top = 42
    bottom = 72
    plot_w = width - left - right
    plot_h = height - top - bottom
    all_records = [row for rows in records_by_seed.values() for row in rows]
    years = [int(row["year"]) for row in all_records]
    values = [as_float(row, "brent_oil_price_usd") for row in all_records]
    min_year, max_year = min(years), max(years)
    min_value = max(10.0, min(values) * 0.86)
    max_value = max(120.0, max(values) * 1.10)

    def x_of(year: int) -> float:
        return left + (year - min_year) / max(1, max_year - min_year) * plot_w

    def y_of(value: float) -> float:
        return top + (max_value - value) / max(1e-9, max_value - min_value) * plot_h

    palette = ["#f97316", "#f59e0b", "#facc15", "#fb7185", "#a78bfa", "#38bdf8", "#22c55e", "#eab308"]
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#07090d"/>',
        f'<text x="{left}" y="27" font-family="Arial" font-size="20" fill="#f5f7fb">Global Brent Oil Paths by Seed</text>',
        f'<text x="{left}" y="50" font-family="Arial" font-size="12" fill="#94a3b8">Oil layer after GDP, inflation, policy, yield curve, dollar, credit, and asset-price dynamics</text>',
    ]

    for i in range(7):
        y = top + i / 6 * plot_h
        value = max_value - i / 6 * (max_value - min_value)
        lines.append(f'<line x1="{left}" y1="{y:.2f}" x2="{left + plot_w}" y2="{y:.2f}" stroke="#1f2937"/>')
        lines.append(f'<text x="{left - 10}" y="{y + 4:.2f}" text-anchor="end" font-family="Arial" font-size="11" fill="#94a3b8">${value:.0f}</text>')
    for i in range(6):
        x = left + i / 5 * plot_w
        year = round(min_year + i / 5 * (max_year - min_year))
        lines.append(f'<line x1="{x:.2f}" y1="{top}" x2="{x:.2f}" y2="{top + plot_h}" stroke="#172033"/>')
        lines.append(f'<text x="{x:.2f}" y="{top + plot_h + 24}" text-anchor="middle" font-family="Arial" font-size="11" fill="#94a3b8">{year}</text>')

    for idx, (seed, records) in enumerate(sorted(records_by_seed.items())):
        color = palette[idx % len(palette)]
        points = " ".join(
            f'{x_of(int(row["year"])):.2f},{y_of(as_float(row, "brent_oil_price_usd")):.2f}'
            for row in records
        )
        lines.append(f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round"/>')
        last = records[-1]
        lines.append(
            f'<text x="{x_of(int(last["year"])) + 6:.2f}" y="{y_of(as_float(last, "brent_oil_price_usd")) + 4:.2f}" '
            f'font-family="Arial" font-size="11" fill="{color}">seed {seed}</text>'
        )

    lines.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}" stroke="#64748b"/>')
    lines.append(f'<line x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}" stroke="#64748b"/>')
    lines.append(f'<text x="18" y="{top + plot_h / 2}" transform="rotate(-90 18 {top + plot_h / 2})" text-anchor="middle" font-family="Arial" font-size="12" fill="#94a3b8">Brent oil, USD/barrel</text>')
    lines.append("</svg>")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a combined global GDP + inflation + policy + yield + dollar + credit + asset + oil annual simulation.",
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
    oil_commodity_params = OilCommodityParams()

    records_by_seed: dict[int, list[dict[str, Any]]] = {}
    for seed in seeds:
        gdp_records = simulate_global_gdp(seed, gdp_params)
        inflation_records = simulate_inflation_for_gdp_path(seed, gdp_records, inflation_params)
        policy_records = simulate_policy_for_macro_path(inflation_records, policy_params)
        yield_records = simulate_yield_curve_for_policy_path(policy_records, yield_curve_params)
        dollar_records = simulate_dollar_liquidity_for_yield_path(yield_records, dollar_liquidity_params)
        credit_records = simulate_credit_spreads_for_dollar_path(dollar_records, credit_spread_params)
        asset_records = simulate_asset_prices_for_credit_path(credit_records, asset_price_params)
        records_by_seed[seed] = simulate_oil_commodities_for_asset_path(asset_records, oil_commodity_params)

    all_records = [row for records in records_by_seed.values() for row in records]
    summaries = [summarize_seed(records) for records in records_by_seed.values()]

    args.output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = args.output_dir / "global_oil_commodity_seed_sweep.csv"
    json_path = args.output_dir / "global_oil_commodity_seed_sweep.json"
    viewer_data_path = args.output_dir / "global_oil_commodity_viewer_data.js"
    svg_path = args.output_dir / "global_oil_commodity_curves.svg"

    write_csv(csv_path, all_records, COMBINED_OIL_COMMODITY_FIELDS)
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
            "oil_commodity_param_version": OIL_COMMODITY_PARAM_VERSION,
            "oil_commodity_interface_version": OIL_COMMODITY_INTERFACE_VERSION,
            "gdp_params": asdict(gdp_params),
            "inflation_params": asdict(inflation_params),
            "policy_params": asdict(policy_params),
            "yield_curve_params": asdict(yield_curve_params),
            "dollar_liquidity_params": asdict(dollar_liquidity_params),
            "credit_spread_params": asdict(credit_spread_params),
            "asset_price_params": asdict(asset_price_params),
            "oil_commodity_params": asdict(oil_commodity_params),
            "seeds": seeds,
            "summary": summaries,
            "model_note": {
                "coupling": "Oil and broad commodities are downstream of GDP demand, dollar pressure, liquidity, credit stress, and asset risk appetite.",
                "event_texture": "The layer includes exogenous supply shortage and glut episodes, plus demand-led slumps and financial/oil feedback signals.",
                "no_feedback_yet": "Oil impulses to headline inflation, GDP, credit stress, and policy are emitted as placeholders only; upstream paths are not recomputed in v0.1.",
                "future_connection": "The oil_to_* fields are intended for later multi-pass macro feedback, energy inflation, terms-of-trade, and sector-profit layers.",
            },
        },
    )
    write_viewer_data_js(viewer_data_path, all_records)
    if not args.no_svg:
        build_oil_commodity_svg(records_by_seed, svg_path)

    print(f"Wrote {csv_path}")
    print(f"Wrote {json_path}")
    print(f"Wrote {viewer_data_path}")
    if not args.no_svg:
        print(f"Wrote {svg_path}")
    for summary in summaries:
        print(
            "seed={seed} avg_oil={average_oil_yoy_change_pct:.1f}% "
            "max_brent=${max_brent_oil_price_usd:.1f} "
            "shock_years={shock_years} slump_years={slump_years} "
            "final_regime={final_oil_regime}".format(**summary)
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
