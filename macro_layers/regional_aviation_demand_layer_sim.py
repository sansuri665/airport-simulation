from __future__ import annotations

from importlib import import_module

_SIBLING_PREFIX = f"{__package__}." if __package__ else ""
simulation_io = import_module(f"{_SIBLING_PREFIX}simulation_io")
simulation_utils = import_module(f"{_SIBLING_PREFIX}simulation_utils")

read_csv = simulation_io.read_csv_utf8
write_csv = simulation_io.write_csv_utf8_ignore
write_json = simulation_io.write_json_utf8_payload
as_float = simulation_utils.as_float_return_missing_default
clamp = simulation_utils.clamp

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean, pstdev
from typing import Any, Iterable


AVIATION_DEMAND_PARAM_VERSION = "regional-aviation-demand-layer-v0.4"
AVIATION_DEMAND_INTERFACE_VERSION = "regional-aviation-demand-interface-v0.3"


AVIATION_DEMAND_FIELDS = [
    "regional_aviation_demand_param_version",
    "regional_aviation_demand_interface_version",
    "region_id",
    "region_name",
    "year_index",
    "year",
    "seed",
    "aviation_demand_scope",
    "source_reconciliation_scope",
    "regional_reconciled_gdp_trillion_usd",
    "regional_air_demand_index",
    "regional_air_demand_growth_pct",
    "business_travel_demand_index",
    "business_travel_growth_pct",
    "business_travel_share_pct",
    "leisure_travel_demand_index",
    "leisure_travel_growth_pct",
    "leisure_travel_share_pct",
    "vfr_travel_demand_index",
    "vfr_travel_growth_pct",
    "vfr_travel_share_pct",
    "long_haul_demand_index",
    "long_haul_growth_pct",
    "long_haul_share_pct",
    "transfer_demand_index",
    "transfer_growth_pct",
    "transfer_share_pct",
    "airfare_price_sensitivity_index",
    "airfare_pressure_index",
    "business_fare_elasticity",
    "leisure_fare_elasticity",
    "vfr_fare_elasticity",
    "long_haul_fare_elasticity",
    "transfer_fare_elasticity",
    "premium_fare_elasticity",
    "premium_passenger_propensity_index",
    "premium_passenger_share_pct",
    "duty_free_propensity_index",
    "luxury_retail_propensity_index",
    "electronics_retail_propensity_index",
    "food_beverage_propensity_index",
    "general_retail_propensity_index",
    "aviation_demand_regime",
    "airport_event_hint",
    "airport_event_pressure_index",
    "aviation_event_impulse_pct",
    "branch_scenario_id",
    "branch_scenario_state",
    "branch_effect_phase",
    "regional_branch_transmission_active",
    "regional_branch_strength_index",
    "source_regional_seed_momentum_label",
    "source_regional_seed_effective_growth_bias_pct",
    "source_regional_seed_aviation_propensity_bias_pct",
    "source_regional_seed_investment_cycle_bias_pct",
    "source_regional_seed_openness_bias_pct",
    "source_regional_seed_demand_multiplier",
    "input_regional_gdp_growth_pct",
    "input_real_income_growth_pct",
    "input_consumer_confidence_index",
    "input_macro_stress_index",
    "input_energy_cost_pressure_index",
    "input_currency_pressure_index",
    "input_hy_spread_bps",
    "input_asset_market_impulse_index",
    "input_household_wealth_consumption_impulse",
    "input_real_disposable_income_growth_pct",
    "input_equity_price_return_pct",
    "input_equity_valuation_pe",
]

for _target in ("total", "business", "leisure", "vfr", "long_haul", "transfer"):
    AVIATION_DEMAND_FIELDS.extend(
        [
            f"demand_{_target}_{_name}_contribution_pp"
            for _name in (
                "asset_market",
                "household_wealth",
                "cash_income",
                "credit_confidence",
                "fare_cost",
            )
        ]
    )
    AVIATION_DEMAND_FIELDS.extend(
        [
            f"demand_{_target}_base_contribution_pp",
            f"demand_{_target}_raw_growth_pct",
            f"demand_{_target}_boundary_adjustment_pp",
            f"demand_{_target}_smoothing_adjustment_pp",
            f"demand_{_target}_final_growth_pct",
        ]
    )

AVIATION_DEMAND_FIELDS.extend(
    [
        "premium_propensity_raw_index",
        "premium_propensity_asset_market_contribution_points",
        "premium_propensity_household_wealth_contribution_points",
        "premium_propensity_cash_income_contribution_points",
        "premium_propensity_traffic_mix_contribution_points",
        "premium_propensity_final_index",
        "premium_propensity_boundary_state",
    ]
)

_COMMERCIAL_CONTRIBUTIONS = {
    "duty_free": ("base", "traffic_mix", "premium", "culture_currency"),
    "luxury_retail": ("base", "premium", "traffic_mix", "culture"),
    "electronics_retail": ("base", "cash_income", "traffic_mix", "culture_currency"),
    "food_beverage": ("base", "traffic_mix", "fare_cost"),
    "general_retail": ("base", "cash_income", "traffic_mix", "fare_cost"),
}

for _commercial, _contributions in _COMMERCIAL_CONTRIBUTIONS.items():
    AVIATION_DEMAND_FIELDS.extend(
        [
            f"{_commercial}_propensity_raw_index",
            *(f"{_commercial}_propensity_{name}_contribution_points" for name in _contributions),
            f"{_commercial}_propensity_final_index",
            f"{_commercial}_propensity_boundary_state",
        ]
    )


@dataclass(frozen=True)
class RegionalAviationDemandParams:
    region_id: str
    region_name: str
    business_travel_weight: float
    leisure_travel_weight: float
    vfr_travel_weight: float
    long_haul_weight: float
    transfer_hub_weight: float
    domestic_market_depth: float
    international_exposure: float
    tourism_exposure: float
    income_sensitivity: float
    price_sensitivity_base: float
    business_fare_elasticity_base: float
    leisure_fare_elasticity_base: float
    vfr_fare_elasticity_base: float
    long_haul_fare_elasticity_base: float
    transfer_fare_elasticity_base: float
    premium_fare_elasticity_base: float
    oil_fare_sensitivity: float
    currency_travel_sensitivity: float
    premium_mix_base: float
    duty_free_culture_index: float
    luxury_retail_affinity: float
    electronics_retail_affinity: float
    premium_business_pass_through: float = 1.0
    demand_adjustment_speed: float = 0.45


AVIATION_REGION_CONFIGS = {
    "north_america": RegionalAviationDemandParams(
        region_id="north_america",
        region_name="北美",
        business_travel_weight=0.32,
        leisure_travel_weight=0.29,
        vfr_travel_weight=0.20,
        long_haul_weight=0.11,
        transfer_hub_weight=0.08,
        domestic_market_depth=0.92,
        international_exposure=0.44,
        tourism_exposure=0.34,
        income_sensitivity=0.78,
        price_sensitivity_base=42.0,
        business_fare_elasticity_base=0.24,
        leisure_fare_elasticity_base=1.35,
        vfr_fare_elasticity_base=0.68,
        long_haul_fare_elasticity_base=0.88,
        transfer_fare_elasticity_base=1.02,
        premium_fare_elasticity_base=0.18,
        oil_fare_sensitivity=0.58,
        currency_travel_sensitivity=0.28,
        premium_mix_base=17.5,
        duty_free_culture_index=0.52,
        luxury_retail_affinity=0.72,
        electronics_retail_affinity=0.58,
    ),
    "china_mainland": RegionalAviationDemandParams(
        region_id="china_mainland",
        region_name="中国大陆",
        business_travel_weight=0.29,
        leisure_travel_weight=0.35,
        vfr_travel_weight=0.18,
        long_haul_weight=0.10,
        transfer_hub_weight=0.08,
        domestic_market_depth=0.95,
        international_exposure=0.38,
        tourism_exposure=0.42,
        income_sensitivity=0.90,
        price_sensitivity_base=50.0,
        business_fare_elasticity_base=0.28,
        leisure_fare_elasticity_base=1.55,
        vfr_fare_elasticity_base=0.75,
        long_haul_fare_elasticity_base=0.98,
        transfer_fare_elasticity_base=0.95,
        premium_fare_elasticity_base=0.20,
        oil_fare_sensitivity=0.64,
        currency_travel_sensitivity=0.34,
        premium_mix_base=11.5,
        duty_free_culture_index=0.62,
        luxury_retail_affinity=0.70,
        electronics_retail_affinity=0.62,
    ),
    "west_north_europe": RegionalAviationDemandParams(
        region_id="west_north_europe",
        region_name="西欧/北欧",
        business_travel_weight=0.30,
        leisure_travel_weight=0.31,
        vfr_travel_weight=0.15,
        long_haul_weight=0.14,
        transfer_hub_weight=0.10,
        domestic_market_depth=0.63,
        international_exposure=0.76,
        tourism_exposure=0.56,
        income_sensitivity=0.72,
        price_sensitivity_base=46.0,
        business_fare_elasticity_base=0.22,
        leisure_fare_elasticity_base=1.28,
        vfr_fare_elasticity_base=0.64,
        long_haul_fare_elasticity_base=0.84,
        transfer_fare_elasticity_base=1.10,
        premium_fare_elasticity_base=0.16,
        oil_fare_sensitivity=0.72,
        currency_travel_sensitivity=0.42,
        premium_mix_base=20.5,
        duty_free_culture_index=0.55,
        luxury_retail_affinity=0.78,
        electronics_retail_affinity=0.50,
    ),
    "japan_korea": RegionalAviationDemandParams(
        region_id="japan_korea",
        region_name="日韩",
        business_travel_weight=0.28,
        leisure_travel_weight=0.32,
        vfr_travel_weight=0.14,
        long_haul_weight=0.13,
        transfer_hub_weight=0.13,
        domestic_market_depth=0.72,
        international_exposure=0.70,
        tourism_exposure=0.52,
        income_sensitivity=0.68,
        price_sensitivity_base=48.0,
        business_fare_elasticity_base=0.21,
        leisure_fare_elasticity_base=1.32,
        vfr_fare_elasticity_base=0.62,
        long_haul_fare_elasticity_base=0.86,
        transfer_fare_elasticity_base=1.00,
        premium_fare_elasticity_base=0.15,
        oil_fare_sensitivity=0.70,
        currency_travel_sensitivity=0.50,
        premium_mix_base=18.5,
        duty_free_culture_index=0.78,
        luxury_retail_affinity=0.74,
        electronics_retail_affinity=0.82,
    ),
    "southeast_asia": RegionalAviationDemandParams(
        region_id="southeast_asia",
        region_name="东南亚",
        business_travel_weight=0.22,
        leisure_travel_weight=0.40,
        vfr_travel_weight=0.16,
        long_haul_weight=0.10,
        transfer_hub_weight=0.12,
        domestic_market_depth=0.72,
        international_exposure=0.78,
        tourism_exposure=0.82,
        income_sensitivity=0.88,
        price_sensitivity_base=56.0,
        business_fare_elasticity_base=0.30,
        leisure_fare_elasticity_base=1.72,
        vfr_fare_elasticity_base=0.82,
        long_haul_fare_elasticity_base=1.05,
        transfer_fare_elasticity_base=1.22,
        premium_fare_elasticity_base=0.22,
        oil_fare_sensitivity=0.68,
        currency_travel_sensitivity=0.54,
        premium_mix_base=9.5,
        duty_free_culture_index=0.66,
        luxury_retail_affinity=0.58,
        electronics_retail_affinity=0.68,
    ),
    "south_asia_india": RegionalAviationDemandParams(
        region_id="south_asia_india",
        region_name="南亚/印度",
        business_travel_weight=0.24,
        leisure_travel_weight=0.30,
        vfr_travel_weight=0.27,
        long_haul_weight=0.11,
        transfer_hub_weight=0.08,
        domestic_market_depth=0.90,
        international_exposure=0.46,
        tourism_exposure=0.32,
        income_sensitivity=0.98,
        price_sensitivity_base=62.0,
        business_fare_elasticity_base=0.34,
        leisure_fare_elasticity_base=1.86,
        vfr_fare_elasticity_base=0.92,
        long_haul_fare_elasticity_base=1.12,
        transfer_fare_elasticity_base=1.08,
        premium_fare_elasticity_base=0.24,
        oil_fare_sensitivity=0.78,
        currency_travel_sensitivity=0.62,
        premium_mix_base=7.5,
        duty_free_culture_index=0.48,
        luxury_retail_affinity=0.48,
        electronics_retail_affinity=0.52,
    ),
    "middle_east_gulf": RegionalAviationDemandParams(
        region_id="middle_east_gulf",
        region_name="中东/海湾",
        business_travel_weight=0.24,
        leisure_travel_weight=0.20,
        vfr_travel_weight=0.10,
        long_haul_weight=0.22,
        transfer_hub_weight=0.24,
        domestic_market_depth=0.38,
        international_exposure=0.92,
        tourism_exposure=0.56,
        income_sensitivity=0.66,
        price_sensitivity_base=40.0,
        business_fare_elasticity_base=0.20,
        leisure_fare_elasticity_base=1.18,
        vfr_fare_elasticity_base=0.58,
        long_haul_fare_elasticity_base=0.78,
        transfer_fare_elasticity_base=1.18,
        premium_fare_elasticity_base=0.14,
        oil_fare_sensitivity=0.46,
        currency_travel_sensitivity=0.24,
        premium_mix_base=26.0,
        duty_free_culture_index=0.86,
        luxury_retail_affinity=0.88,
        electronics_retail_affinity=0.76,
    ),
    "hk_macao_taiwan": RegionalAviationDemandParams(
        region_id="hk_macao_taiwan",
        region_name="港澳台",
        business_travel_weight=0.30,
        leisure_travel_weight=0.30,
        vfr_travel_weight=0.12,
        long_haul_weight=0.13,
        transfer_hub_weight=0.15,
        domestic_market_depth=0.42,
        international_exposure=0.86,
        tourism_exposure=0.74,
        income_sensitivity=0.70,
        price_sensitivity_base=47.0,
        business_fare_elasticity_base=0.22,
        leisure_fare_elasticity_base=1.34,
        vfr_fare_elasticity_base=0.62,
        long_haul_fare_elasticity_base=0.88,
        transfer_fare_elasticity_base=1.06,
        premium_fare_elasticity_base=0.16,
        oil_fare_sensitivity=0.66,
        currency_travel_sensitivity=0.46,
        premium_mix_base=23.5,
        duty_free_culture_index=0.92,
        luxury_retail_affinity=0.88,
        electronics_retail_affinity=0.90,
    ),
    "oceania": RegionalAviationDemandParams(
        region_id="oceania",
        region_name="大洋洲",
        business_travel_weight=0.22,
        leisure_travel_weight=0.36,
        vfr_travel_weight=0.20,
        long_haul_weight=0.16,
        transfer_hub_weight=0.06,
        domestic_market_depth=0.68,
        international_exposure=0.70,
        tourism_exposure=0.66,
        income_sensitivity=0.76,
        price_sensitivity_base=50.0,
        business_fare_elasticity_base=0.25,
        leisure_fare_elasticity_base=1.46,
        vfr_fare_elasticity_base=0.72,
        long_haul_fare_elasticity_base=1.02,
        transfer_fare_elasticity_base=1.10,
        premium_fare_elasticity_base=0.18,
        oil_fare_sensitivity=0.76,
        currency_travel_sensitivity=0.58,
        premium_mix_base=15.5,
        duty_free_culture_index=0.55,
        luxury_retail_affinity=0.65,
        electronics_retail_affinity=0.55,
    ),
    "south_east_europe_mediterranean": RegionalAviationDemandParams(
        region_id="south_east_europe_mediterranean",
        region_name="南欧/东欧/地中海",
        business_travel_weight=0.14,
        leisure_travel_weight=0.54,
        vfr_travel_weight=0.15,
        long_haul_weight=0.06,
        transfer_hub_weight=0.11,
        domestic_market_depth=0.54,
        international_exposure=0.82,
        tourism_exposure=0.88,
        income_sensitivity=0.92,
        price_sensitivity_base=56.0,
        business_fare_elasticity_base=0.30,
        leisure_fare_elasticity_base=1.62,
        vfr_fare_elasticity_base=0.82,
        long_haul_fare_elasticity_base=1.08,
        transfer_fare_elasticity_base=1.28,
        premium_fare_elasticity_base=0.22,
        oil_fare_sensitivity=0.72,
        currency_travel_sensitivity=0.50,
        premium_mix_base=8.5,
        duty_free_culture_index=0.62,
        luxury_retail_affinity=0.54,
        electronics_retail_affinity=0.45,
    ),
    "central_asia_turkey_eurasia": RegionalAviationDemandParams(
        region_id="central_asia_turkey_eurasia",
        region_name="中亚/土耳其/欧亚桥",
        business_travel_weight=0.18,
        leisure_travel_weight=0.26,
        vfr_travel_weight=0.22,
        long_haul_weight=0.10,
        transfer_hub_weight=0.24,
        domestic_market_depth=0.58,
        international_exposure=0.74,
        tourism_exposure=0.50,
        income_sensitivity=0.88,
        price_sensitivity_base=58.0,
        business_fare_elasticity_base=0.32,
        leisure_fare_elasticity_base=1.70,
        vfr_fare_elasticity_base=0.85,
        long_haul_fare_elasticity_base=1.05,
        transfer_fare_elasticity_base=1.30,
        premium_fare_elasticity_base=0.22,
        oil_fare_sensitivity=0.70,
        currency_travel_sensitivity=0.72,
        premium_mix_base=4.0,
        duty_free_culture_index=0.52,
        luxury_retail_affinity=0.42,
        electronics_retail_affinity=0.50,
        premium_business_pass_through=0.72,
        demand_adjustment_speed=0.38,
    ),
    "north_africa": RegionalAviationDemandParams(
        region_id="north_africa",
        region_name="北非",
        business_travel_weight=0.11,
        leisure_travel_weight=0.49,
        vfr_travel_weight=0.22,
        long_haul_weight=0.07,
        transfer_hub_weight=0.11,
        domestic_market_depth=0.55,
        international_exposure=0.66,
        tourism_exposure=0.68,
        income_sensitivity=0.96,
        price_sensitivity_base=64.0,
        business_fare_elasticity_base=0.34,
        leisure_fare_elasticity_base=1.88,
        vfr_fare_elasticity_base=0.92,
        long_haul_fare_elasticity_base=1.14,
        transfer_fare_elasticity_base=1.30,
        premium_fare_elasticity_base=0.25,
        oil_fare_sensitivity=0.76,
        currency_travel_sensitivity=0.70,
        premium_mix_base=3.0,
        duty_free_culture_index=0.55,
        luxury_retail_affinity=0.36,
        electronics_retail_affinity=0.43,
        premium_business_pass_through=0.55,
        demand_adjustment_speed=0.36,
    ),
    "latin_america_caribbean": RegionalAviationDemandParams(
        region_id="latin_america_caribbean",
        region_name="拉美/加勒比",
        business_travel_weight=0.16,
        leisure_travel_weight=0.35,
        vfr_travel_weight=0.32,
        long_haul_weight=0.11,
        transfer_hub_weight=0.06,
        domestic_market_depth=0.74,
        international_exposure=0.62,
        tourism_exposure=0.64,
        income_sensitivity=0.90,
        price_sensitivity_base=60.0,
        business_fare_elasticity_base=0.31,
        leisure_fare_elasticity_base=1.74,
        vfr_fare_elasticity_base=0.86,
        long_haul_fare_elasticity_base=1.10,
        transfer_fare_elasticity_base=1.18,
        premium_fare_elasticity_base=0.23,
        oil_fare_sensitivity=0.66,
        currency_travel_sensitivity=0.76,
        premium_mix_base=3.5,
        duty_free_culture_index=0.60,
        luxury_retail_affinity=0.42,
        electronics_retail_affinity=0.48,
        premium_business_pass_through=0.65,
        demand_adjustment_speed=0.38,
    ),
    "sub_saharan_africa": RegionalAviationDemandParams(
        region_id="sub_saharan_africa",
        region_name="撒哈拉以南非洲",
        business_travel_weight=0.12,
        leisure_travel_weight=0.30,
        vfr_travel_weight=0.36,
        long_haul_weight=0.08,
        transfer_hub_weight=0.14,
        domestic_market_depth=0.62,
        international_exposure=0.48,
        tourism_exposure=0.30,
        income_sensitivity=1.05,
        price_sensitivity_base=66.0,
        business_fare_elasticity_base=0.36,
        leisure_fare_elasticity_base=1.95,
        vfr_fare_elasticity_base=0.96,
        long_haul_fare_elasticity_base=1.16,
        transfer_fare_elasticity_base=1.34,
        premium_fare_elasticity_base=0.26,
        oil_fare_sensitivity=0.76,
        currency_travel_sensitivity=0.82,
        premium_mix_base=1.5,
        duty_free_culture_index=0.34,
        luxury_retail_affinity=0.26,
        electronics_retail_affinity=0.32,
        premium_business_pass_through=0.42,
        demand_adjustment_speed=0.32,
    ),
}



def soft_limit(value: float, low_knee: float, high_knee: float, softness: float = 18.0) -> float:
    """Dampen extreme index values without turning the series into a flat cap."""
    if value < low_knee:
        shortfall = low_knee - value
        return low_knee - softness * shortfall / (softness + shortfall)
    if value > high_knee:
        excess = value - high_knee
        return high_knee + softness * excess / (softness + excess)
    return value


def smooth(old: float, target: float, speed: float) -> float:
    return old + (target - old) * clamp(speed, 0.0, 1.0)


def round_record(record: dict[str, Any]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key, value in record.items():
        if isinstance(value, float):
            output[key] = round(value, 4)
        else:
            output[key] = value
    return output


def write_viewer_data_js(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(rows, ensure_ascii=False, separators=(",", ":"))
    path.write_text(f"window.REGIONAL_AVIATION_DEMAND_DATA = {payload};\n", encoding="utf-8")


def key_for(row: dict[str, Any]) -> tuple[int, int]:
    return int(as_float(row, "seed")), int(as_float(row, "year_index"))


def merge_region_inputs(
    region_id: str,
    regional_rows: Iterable[dict[str, Any]],
    reconciled_rows: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    filtered_regional = [row for row in regional_rows if row.get("region_id") == region_id]
    filtered_reconciled = [row for row in reconciled_rows if row.get("region_id") == region_id]
    regional_by_key = {key_for(row): row for row in filtered_regional}
    merged = []
    for row in sorted(filtered_reconciled, key=lambda item: (int(as_float(item, "seed")), int(as_float(item, "year_index")))):
        raw = regional_by_key.get(key_for(row), {})
        item = dict(raw)
        item.update(row)
        merged.append(item)
    return merged


def load_region_inputs(
    region_id: str,
    regional_csv: Path,
    reconciled_csv: Path,
) -> list[dict[str, Any]]:
    return merge_region_inputs(region_id, read_csv(regional_csv), read_csv(reconciled_csv))


def weighted_index(values: dict[str, float], params: RegionalAviationDemandParams) -> float:
    weights = component_weights(params)
    return sum(values[key] * weights[key] for key in weights)


def component_shares(values: dict[str, float], params: RegionalAviationDemandParams) -> dict[str, float]:
    weights = component_weights(params)
    weighted = {key: values[key] * weights[key] for key in weights}
    total = max(1e-9, sum(weighted.values()))
    return {key: value / total * 100.0 for key, value in weighted.items()}


def pct_change(current: float, previous: float) -> float:
    if abs(previous) < 1e-9:
        return 0.0
    return (current / previous - 1.0) * 100.0


def input_metrics(row: dict[str, Any]) -> dict[str, float]:
    return {
        "growth": as_float(row, "regional_gdp_growth_pct_reconciled", as_float(row, "regional_gdp_growth_pct")),
        "potential": as_float(row, "regional_potential_growth_pct", 2.0),
        "income_growth": as_float(row, "regional_real_disposable_income_growth_pct"),
        "income_index": as_float(row, "regional_income_index", 100.0),
        "confidence": as_float(row, "consumer_confidence_index", 50.0),
        "headline": as_float(row, "regional_headline_inflation_pct_reconciled", as_float(row, "regional_headline_inflation_pct")),
        "currency_pressure": as_float(row, "currency_pressure_index", 35.0),
        "stress": as_float(row, "regional_macro_stress_index_reconciled", as_float(row, "regional_macro_stress_index", 35.0)),
        "hy": as_float(row, "regional_hy_spread_bps_reconciled", as_float(row, "regional_hy_spread_bps", 480.0)),
        "credit_availability": as_float(row, "regional_credit_availability_index", 55.0),
        "asset_market": as_float(row, "regional_asset_market_impulse_index", 50.0),
        "wealth_impulse": as_float(row, "regional_household_wealth_consumption_impulse"),
        "equity_price_return": as_float(row, "regional_equity_price_return_pct"),
        "equity_valuation_pe": as_float(row, "regional_equity_valuation_pe", 18.0),
        "energy": as_float(row, "regional_energy_cost_pressure_index_reconciled", as_float(row, "regional_energy_cost_pressure_index", 50.0)),
        "risk_appetite": as_float(row, "regional_risk_appetite_index", 50.0),
        "geopolitical": as_float(row, "regional_geopolitical_risk_index", 25.0),
        "branch_growth": as_float(row, "regional_branch_growth_impulse_pct"),
        "branch_credit": as_float(row, "regional_branch_credit_impulse_bps"),
        "branch_fx": as_float(row, "regional_branch_fx_pressure_impulse"),
        "branch_energy": as_float(row, "regional_branch_energy_impulse"),
        "branch_asset": as_float(row, "regional_branch_asset_impulse_pct"),
        "branch_confidence": as_float(row, "regional_branch_confidence_impulse"),
        "branch_stress": as_float(row, "regional_branch_strength_index"),
        "branch_tail": as_float(row, "regional_branch_tail_scarring_index"),
        "seed_growth_bias": as_float(row, "regional_seed_effective_growth_bias_pct"),
        "seed_aviation_bias": as_float(row, "regional_seed_aviation_propensity_bias_pct"),
        "seed_investment_bias": as_float(row, "regional_seed_investment_cycle_bias_pct"),
        "seed_openness_bias": as_float(row, "regional_seed_openness_bias_pct"),
        "seed_demand_multiplier": as_float(row, "regional_seed_demand_multiplier", 1.0),
    }


def price_sensitivity(metrics: dict[str, float], params: RegionalAviationDemandParams) -> float:
    inflation_pressure = max(0.0, metrics["headline"] - 2.4) * 7.0
    energy_pressure = max(0.0, metrics["energy"] - 50.0) * params.oil_fare_sensitivity
    currency_pressure = max(0.0, metrics["currency_pressure"] - 35.0) * params.currency_travel_sensitivity
    stress_pressure = max(0.0, metrics["stress"] - 38.0) * 0.22
    return clamp(
        params.price_sensitivity_base
        + inflation_pressure
        + energy_pressure
        + currency_pressure
        + stress_pressure,
        18.0,
        88.0,
    )


def fare_elasticities(price_index: float, params: RegionalAviationDemandParams) -> dict[str, float]:
    adjustment = (price_index - 50.0) / 100.0
    return {
        "business": clamp(params.business_fare_elasticity_base * (1.0 + adjustment * 0.35), 0.12, 0.42),
        "leisure": clamp(params.leisure_fare_elasticity_base * (1.0 + adjustment * 0.55), 0.90, 2.10),
        "vfr": clamp(params.vfr_fare_elasticity_base * (1.0 + adjustment * 0.42), 0.40, 1.10),
        "long_haul": clamp(params.long_haul_fare_elasticity_base * (1.0 + adjustment * 0.50), 0.55, 1.35),
        "transfer": clamp(params.transfer_fare_elasticity_base * (1.0 + adjustment * 0.52), 0.65, 1.55),
        "premium": clamp(params.premium_fare_elasticity_base * (1.0 + adjustment * 0.25), 0.08, 0.32),
    }


def airport_event_hint(row: dict[str, Any], metrics: dict[str, float]) -> tuple[str, float, float]:
    branch_id = str(row.get("branch_scenario_id") or "none")
    active = str(row.get("regional_branch_transmission_active") or "").lower() == "true"
    pressure = clamp(metrics["branch_stress"], 0.0, 100.0) if active else 0.0
    if not active or branch_id in ("", "none"):
        return "none", 0.0, 0.0
    if branch_id == "energy_shock_escalation":
        return "fare_shock_leisure_drag", pressure, -0.45 - 0.012 * pressure
    if branch_id == "dollar_squeeze_escalation":
        return "outbound_fx_squeeze", pressure, -0.30 - 0.010 * pressure
    if branch_id in {"credit_accident", "bank_lending_trap", "refinancing_wall"}:
        return "business_travel_credit_drag", pressure, -0.36 - 0.012 * pressure
    if branch_id == "false_dawn":
        return "recovery_reversal_warning", pressure, -0.20 - 0.010 * pressure
    if branch_id == "soft_landing_success":
        return "broad_travel_recovery", pressure, 0.22 + 0.008 * pressure
    if branch_id in {"liquidity_bubble", "risk_asset_bull_fragility"}:
        return "premium_mix_volatility", pressure, 0.08 - 0.004 * pressure
    return "macro_branch_air_demand_shift", pressure, -0.006 * pressure


def component_weights(params: RegionalAviationDemandParams) -> dict[str, float]:
    """Return normalized baseline mix weights used by totals and centering."""
    raw = {
        "business": params.business_travel_weight,
        "leisure": params.leisure_travel_weight,
        "vfr": params.vfr_travel_weight,
        "long_haul": params.long_haul_weight,
        "transfer": params.transfer_hub_weight,
    }
    total = sum(raw.values())
    if total <= 0.0:
        raise ValueError("regional aviation demand weights must sum to a positive value")
    return {key: value / total for key, value in raw.items()}


def weighted_component_average(values: dict[str, float], params: RegionalAviationDemandParams) -> float:
    weights = component_weights(params)
    return sum(values[key] * weights[key] for key in weights)


def fare_demand_effects(
    price_index: float,
    params: RegionalAviationDemandParams,
) -> dict[str, float]:
    """Map the displayed fare elasticities into component growth effects.

    ``price_index`` is compared with the region's configured neutral sensitivity
    base. Only an adverse gap is treated as a fare shock; benign income/confidence
    relief does not create an automatic structural bonus.
    """
    elasticities = fare_elasticities(price_index, params)
    adverse_fare_gap = max(0.0, price_index - params.price_sensitivity_base) / 10.0
    return {
        key: -0.72 * elasticities[key] * adverse_fare_gap
        for key in ("business", "leisure", "vfr", "long_haul", "transfer")
    }


def branch_component_effects(metrics: dict[str, float]) -> dict[str, float]:
    return {
        "business": (
            0.42 * metrics["branch_growth"]
            + 0.07 * metrics["branch_confidence"]
            + 0.05 * metrics["branch_asset"]
            - 0.010 * max(0.0, metrics["branch_credit"])
            - 0.020 * metrics["branch_tail"]
        ),
        "leisure": (
            0.28 * metrics["branch_growth"]
            + 0.05 * metrics["branch_confidence"]
            - 0.070 * max(0.0, metrics["branch_energy"])
            - 0.050 * max(0.0, metrics["branch_fx"])
            - 0.010 * metrics["branch_stress"]
        ),
        "vfr": (
            0.12 * metrics["branch_growth"]
            + 0.02 * metrics["branch_confidence"]
            - 0.004 * metrics["branch_stress"]
        ),
        "long_haul": (
            0.25 * metrics["branch_growth"]
            + 0.04 * metrics["branch_asset"]
            - 0.060 * max(0.0, metrics["branch_energy"])
            - 0.060 * max(0.0, metrics["branch_fx"])
            - 0.008 * metrics["branch_stress"]
        ),
        "transfer": (
            0.18 * metrics["branch_growth"]
            - 0.030 * max(0.0, metrics["branch_energy"])
            - 0.035 * max(0.0, metrics["branch_fx"])
            - 0.004 * metrics["branch_credit"]
        ),
    }


def event_component_effects(event_impulse: float) -> dict[str, float]:
    return {
        "business": event_impulse * 0.35,
        "leisure": event_impulse * 0.40,
        "vfr": event_impulse * 0.15,
        "long_haul": event_impulse * 0.45,
        "transfer": event_impulse * 0.25,
    }


def common_total_growth(
    metrics: dict[str, float],
    params: RegionalAviationDemandParams,
    price_index: float,
    event_impulse: float,
    previous_metrics: dict[str, float] | None = None,
) -> float:
    decomposition = demand_growth_decomposition(
        metrics, params, price_index, event_impulse, previous_metrics
    )
    return decomposition["total"]["final"]


def raw_relative_component_adjustments(
    metrics: dict[str, float],
    params: RegionalAviationDemandParams,
    price_index: float,
    event_impulse: float,
) -> dict[str, float]:
    decomposition = demand_growth_decomposition(
        metrics, params, price_index, event_impulse
    )
    total = decomposition["total"]["raw"]
    return {key: decomposition[key]["raw"] - total for key in ("business", "leisure", "vfr", "long_haul", "transfer")}


DEMAND_CONTRIBUTION_NAMES = (
    "asset_market",
    "household_wealth",
    "cash_income",
    "credit_confidence",
    "fare_cost",
)


def demand_growth_decomposition(
    metrics: dict[str, float],
    params: RegionalAviationDemandParams,
    price_index: float,
    event_impulse: float,
    previous_metrics: dict[str, float] | None = None,
) -> dict[str, dict[str, float]]:
    """Return reconstructable A3 growth targets with one entry per signal family."""

    keys = ("business", "leisure", "vfr", "long_haul", "transfer")
    growth_surprise = metrics["growth"] - metrics["potential"]
    demand_multiplier_gap = (metrics["seed_demand_multiplier"] - 1.0) * 100.0
    common_base = (
        0.63 * metrics["potential"]
        + 0.44 * growth_surprise
        + 0.020 * metrics["seed_growth_bias"]
        + 0.030 * metrics["seed_aviation_bias"]
        + 0.012 * demand_multiplier_gap
    )
    event = event_component_effects(event_impulse)
    bases = {
        "business": common_base + 0.040 * metrics["seed_investment_bias"] + 0.42 * metrics["branch_growth"] + event["business"],
        "leisure": common_base + 0.025 * metrics["seed_openness_bias"] + 0.28 * metrics["branch_growth"] + event["leisure"],
        "vfr": common_base + 0.12 * metrics["branch_growth"] + event["vfr"],
        "long_haul": common_base + 0.05 * params.international_exposure * metrics["seed_openness_bias"] + 0.25 * metrics["branch_growth"] + event["long_haul"],
        "transfer": common_base + 0.08 * params.international_exposure * metrics["seed_openness_bias"] + 0.35 * (params.transfer_hub_weight - 0.08) * metrics["seed_openness_bias"] + 0.030 * metrics["seed_investment_bias"] + 0.18 * metrics["branch_growth"] + event["transfer"],
    }

    market_gap = metrics["asset_market"] - 50.0
    asset_market = {
        "business": 0.14 * market_gap,
        "leisure": 0.0,
        "vfr": 0.0,
        "long_haul": 0.11 * market_gap,
        "transfer": 0.04 * market_gap,
    }
    wealth = metrics["wealth_impulse"]
    household_wealth = {
        "business": 0.08 * wealth,
        "leisure": 0.12 * wealth,
        "vfr": 0.05 * wealth,
        "long_haul": 0.08 * wealth,
        "transfer": 0.02 * wealth,
    }
    income = metrics["income_growth"]
    cash_income = {
        "business": 0.18 * income * params.income_sensitivity,
        "leisure": 0.55 * income * params.income_sensitivity * params.tourism_exposure,
        "vfr": 0.22 * income,
        "long_haul": 0.12 * income * params.income_sensitivity,
        "transfer": 0.05 * income,
    }

    confidence_gap = metrics["confidence"] - 50.0
    stress_pressure = max(0.0, metrics["stress"] - 38.0)
    hy_pressure = max(0.0, metrics["hy"] - 500.0) / 100.0
    credit_gap = (metrics["credit_availability"] - 55.0) / 10.0
    risk_gap = (metrics["risk_appetite"] - 50.0) / 10.0
    severe = max(0.0, hy_pressure - 0.8)
    previous_hy = hy_pressure if previous_metrics is None else max(0.0, previous_metrics["hy"] - 500.0) / 100.0
    severe_change = severe - max(0.0, previous_hy - 0.8)
    common_credit = (
        0.016 * confidence_gap
        + 0.045 * credit_gap
        - 0.030 * stress_pressure
        - 0.230 * hy_pressure
        + 2.50 * params.domestic_market_depth * severe_change
        + 0.07 * metrics["branch_confidence"]
        - 0.010 * max(0.0, metrics["branch_credit"])
        - 0.010 * metrics["branch_stress"]
    )
    credit_confidence = {
        "business": common_credit + 0.05 * risk_gap - 0.15 * hy_pressure,
        "leisure": common_credit + 0.020 * confidence_gap * params.tourism_exposure,
        "vfr": common_credit + 0.010 * confidence_gap,
        "long_haul": common_credit + params.international_exposure * (0.12 * risk_gap - 0.24 * ((metrics["geopolitical"] - 25.0) / 10.0)),
        "transfer": common_credit + 1.12 * params.international_exposure * (0.12 * risk_gap - 0.24 * ((metrics["geopolitical"] - 25.0) / 10.0)),
    }

    fare_cost = fare_demand_effects(price_index, params)
    fare_cost = {
        "business": fare_cost["business"],
        "leisure": fare_cost["leisure"] - 0.070 * max(0.0, metrics["branch_energy"]) - 0.050 * max(0.0, metrics["branch_fx"]),
        "vfr": fare_cost["vfr"],
        "long_haul": fare_cost["long_haul"] - params.international_exposure * (0.025 * max(0.0, metrics["energy"] - 50.0) + 0.11 * max(0.0, metrics["currency_pressure"] - 35.0)) - 0.060 * max(0.0, metrics["branch_energy"]) - 0.060 * max(0.0, metrics["branch_fx"]),
        "transfer": fare_cost["transfer"] - 1.12 * params.international_exposure * (0.025 * max(0.0, metrics["energy"] - 50.0) + 0.11 * max(0.0, metrics["currency_pressure"] - 35.0)) - 0.030 * max(0.0, metrics["branch_energy"]) - 0.035 * max(0.0, metrics["branch_fx"]),
    }

    families = {
        "asset_market": asset_market,
        "household_wealth": household_wealth,
        "cash_income": cash_income,
        "credit_confidence": credit_confidence,
        "fare_cost": fare_cost,
    }
    # Exposure parameters redistribute demand mix; they do not manufacture a
    # second aggregate growth channel. Center the affected families explicitly.
    weights = component_weights(params)
    desired_family_totals = {
        "cash_income": 0.32 * income * params.income_sensitivity,
        "credit_confidence": common_credit,
        "fare_cost": sum(fare_cost.values()) / len(fare_cost),
    }
    desired_base_total = common_base + sum(event.values()) / len(event) + 0.25 * metrics["branch_growth"]
    base_center = desired_base_total - sum(bases[key] * weights[key] for key in keys)
    bases = {key: value + base_center for key, value in bases.items()}
    for family_name, desired_total in desired_family_totals.items():
        family = families[family_name]
        center = desired_total - sum(family[key] * weights[key] for key in keys)
        families[family_name] = {key: value + center for key, value in family.items()}
    limits = {
        "business": (-9.0, 10.5),
        "leisure": (-10.0, 12.0),
        "vfr": (-4.5, 6.5),
        "long_haul": (-11.0, 12.5),
        "transfer": (-7.5, 8.5),
    }
    result: dict[str, dict[str, float]] = {}
    for key in keys:
        raw = bases[key] + sum(families[name][key] for name in DEMAND_CONTRIBUTION_NAMES)
        final = clamp(raw, *limits[key])
        result[key] = {
            "base": bases[key],
            **{name: families[name][key] for name in DEMAND_CONTRIBUTION_NAMES},
            "raw": raw,
            "boundary_adjustment": final - raw,
            "final": final,
        }

    total_raw = sum(result[key]["raw"] * weights[key] for key in keys)
    total_final = clamp(total_raw, -8.0, 10.0)
    result["total"] = {
        "base": sum(result[key]["base"] * weights[key] for key in keys),
        **{
            name: sum(result[key][name] * weights[key] for key in keys)
            for name in DEMAND_CONTRIBUTION_NAMES
        },
        "raw": total_raw,
        "boundary_adjustment": total_final - total_raw,
        "final": total_final,
    }
    return result


def center_relative_component_adjustments(
    adjustments: dict[str, float],
    params: RegionalAviationDemandParams,
) -> dict[str, float]:
    """Center relative preferences so their baseline-weighted sum is zero."""
    center = weighted_component_average(adjustments, params)
    return {key: value - center for key, value in adjustments.items()}


def target_component_growth(
    metrics: dict[str, float],
    params: RegionalAviationDemandParams,
    price_index: float,
    event_impulse: float,
    previous_metrics: dict[str, float] | None = None,
) -> dict[str, float]:
    decomposition = demand_growth_decomposition(
        metrics, params, price_index, event_impulse, previous_metrics
    )
    return {
        key: decomposition[key]["final"]
        for key in ("business", "leisure", "vfr", "long_haul", "transfer")
    }


def raw_component_growth(
    metrics: dict[str, float],
    params: RegionalAviationDemandParams,
    price_index: float,
    event_impulse: float,
    previous_metrics: dict[str, float] | None = None,
) -> dict[str, float]:
    """Backward-compatible wrapper for the v0.3 target-growth decomposition."""
    return target_component_growth(
        metrics,
        params,
        price_index,
        event_impulse,
        previous_metrics,
    )

def aviation_regime(total_growth: float, price_index: float, event_hint: str, premium_index: float, stress: float) -> str:
    if event_hint != "none":
        return event_hint
    if total_growth <= -3.0:
        return "air_demand_contraction"
    if total_growth >= 5.0 and price_index < 58.0:
        return "broad_air_travel_expansion"
    if price_index >= 70.0:
        return "fare_pressure_drag"
    if premium_index >= 118.0 and stress < 45.0:
        return "premium_resilient_demand"
    if total_growth >= 2.5:
        return "normal_air_travel_growth"
    return "stable_air_travel_demand"


def simulate_region_aviation_demand(
    rows: list[dict[str, Any]],
    params: RegionalAviationDemandParams,
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    state_by_seed: dict[int, dict[str, Any]] = {}

    for row in rows:
        seed = int(as_float(row, "seed"))
        year_index = int(as_float(row, "year_index"))
        metrics = input_metrics(row)
        price_index = price_sensitivity(metrics, params)
        fare_pressure = clamp(
            50.0
            + (metrics["energy"] - 50.0) * params.oil_fare_sensitivity
            + max(0.0, metrics["headline"] - 2.4) * 8.0
            + max(0.0, metrics["currency_pressure"] - 35.0) * 0.22,
            20.0,
            95.0,
        )
        event_hint, event_pressure, event_impulse = airport_event_hint(row, metrics)
        elasticities = fare_elasticities(price_index, params)

        previous = state_by_seed.get(seed)
        decomposition = demand_growth_decomposition(
            metrics,
            params,
            price_index,
            event_impulse,
            previous["metrics"] if previous else None,
        )
        if previous is None:
            component_values = {
                "business": 100.0,
                "leisure": 100.0,
                "vfr": 100.0,
                "long_haul": 100.0,
                "transfer": 100.0,
            }
            component_growth = {key: 0.0 for key in component_values}
            total_index = weighted_index(component_values, params)
            total_growth = 0.0
            decomposition = {
                target: {name: 0.0 for name in ("base", *DEMAND_CONTRIBUTION_NAMES, "raw", "boundary_adjustment", "final")}
                for target in ("total", "business", "leisure", "vfr", "long_haul", "transfer")
            }
        else:
            raw_growth = {
                key: decomposition[key]["final"]
                for key in ("business", "leisure", "vfr", "long_haul", "transfer")
            }
            component_growth = {
                key: smooth(previous["growth"][key], raw_growth[key], params.demand_adjustment_speed)
                for key in raw_growth
            }
            component_values = {
                key: previous["values"][key] * (1.0 + component_growth[key] / 100.0)
                for key in component_growth
            }
            total_index = weighted_index(component_values, params)
            total_growth = pct_change(total_index, previous["total_index"])

        shares = component_shares(component_values, params)
        premium_business_gap = (component_values["business"] - 100.0) * params.premium_business_pass_through
        premium_long_haul_gap = (component_values["long_haul"] - 100.0) * params.premium_business_pass_through
        premium_asset_contribution = 0.25 * (metrics["asset_market"] - 50.0)
        premium_wealth_contribution = 1.40 * metrics["wealth_impulse"]
        premium_cash_contribution = 1.20 * metrics["income_growth"]
        premium_traffic_contribution = 0.22 * premium_business_gap + 0.24 * premium_long_haul_gap
        premium_propensity_raw = 100.0 + premium_asset_contribution + premium_wealth_contribution + premium_cash_contribution + premium_traffic_contribution
        premium_propensity = soft_limit(premium_propensity_raw, 55.0, 170.0, softness=18.0)
        premium_boundary_state = "floor" if premium_propensity_raw < 55.0 else "cap" if premium_propensity_raw > 170.0 else "none"
        premium_share_raw = (
            params.premium_mix_base
            + 0.045 * (premium_propensity - 100.0)
            + 0.035 * premium_business_gap
            + 0.018 * premium_long_haul_gap
        )
        premium_share = clamp(soft_limit(premium_share_raw, 8.0, 34.0, softness=4.0), 5.0, 45.0)
        duty_free_parts = {
            "base": 92.0,
            "traffic_mix": 0.42 * (component_values["long_haul"] - 100.0) + 0.28 * (component_values["leisure"] - 100.0),
            "premium": 0.18 * (premium_propensity - 100.0),
            "culture_currency": 18.0 * (params.duty_free_culture_index - 0.5) - 0.12 * max(0.0, metrics["currency_pressure"] - 45.0),
        }
        duty_free_raw = sum(duty_free_parts.values())
        duty_free = soft_limit(duty_free_raw, 45.0, 175.0, softness=20.0)
        luxury_parts = {
            "base": 88.0,
            "premium": 0.58 * (premium_propensity - 100.0),
            "traffic_mix": 0.18 * (component_values["business"] - 100.0),
            "culture": 22.0 * (params.luxury_retail_affinity - 0.5),
        }
        luxury_raw = sum(luxury_parts.values())
        luxury = soft_limit(luxury_raw, 40.0, 180.0, softness=20.0)
        electronics_parts = {
            "base": 90.0,
            "cash_income": 2.0 * metrics["income_growth"],
            "traffic_mix": 0.18 * (component_values["long_haul"] - 100.0) + 0.16 * (component_values["transfer"] - 100.0),
            "culture_currency": 18.0 * (params.electronics_retail_affinity - 0.5) - 0.10 * max(0.0, metrics["currency_pressure"] - 45.0),
        }
        electronics_raw = sum(electronics_parts.values())
        electronics = soft_limit(electronics_raw, 42.0, 168.0, softness=18.0)
        food_beverage_parts = {
            "base": 96.0,
            "traffic_mix": 0.34 * (total_index - 100.0) + 0.12 * (component_values["transfer"] - 100.0),
            "fare_cost": -0.10 * max(0.0, price_index - 60.0),
        }
        food_beverage_raw = sum(food_beverage_parts.values())
        food_beverage = soft_limit(food_beverage_raw, 55.0, 165.0, softness=20.0)
        general_retail_parts = {
            "base": 94.0,
            "cash_income": 1.2 * metrics["income_growth"],
            "traffic_mix": 0.30 * (total_index - 100.0) + 0.15 * (component_values["leisure"] - 100.0),
            "fare_cost": -0.12 * max(0.0, price_index - 62.0),
        }
        general_retail_raw = sum(general_retail_parts.values())
        general_retail = soft_limit(general_retail_raw, 50.0, 165.0, softness=20.0)
        regime = aviation_regime(total_growth, price_index, event_hint, premium_propensity, metrics["stress"])

        item = round_record(
            {
                "regional_aviation_demand_param_version": AVIATION_DEMAND_PARAM_VERSION,
                "regional_aviation_demand_interface_version": AVIATION_DEMAND_INTERFACE_VERSION,
                "region_id": params.region_id,
                "region_name": params.region_name,
                "year_index": year_index,
                "year": int(as_float(row, "year")),
                "seed": seed,
                "aviation_demand_scope": "regional_demand_index_v0",
                "source_reconciliation_scope": str(row.get("reconciliation_scope") or ""),
                "regional_reconciled_gdp_trillion_usd": as_float(row, "regional_reconciled_gdp_trillion_usd"),
                "regional_air_demand_index": total_index,
                "regional_air_demand_growth_pct": total_growth,
                "business_travel_demand_index": component_values["business"],
                "business_travel_growth_pct": component_growth["business"],
                "business_travel_share_pct": shares["business"],
                "leisure_travel_demand_index": component_values["leisure"],
                "leisure_travel_growth_pct": component_growth["leisure"],
                "leisure_travel_share_pct": shares["leisure"],
                "vfr_travel_demand_index": component_values["vfr"],
                "vfr_travel_growth_pct": component_growth["vfr"],
                "vfr_travel_share_pct": shares["vfr"],
                "long_haul_demand_index": component_values["long_haul"],
                "long_haul_growth_pct": component_growth["long_haul"],
                "long_haul_share_pct": shares["long_haul"],
                "transfer_demand_index": component_values["transfer"],
                "transfer_growth_pct": component_growth["transfer"],
                "transfer_share_pct": shares["transfer"],
                "airfare_price_sensitivity_index": price_index,
                "airfare_pressure_index": fare_pressure,
                "business_fare_elasticity": elasticities["business"],
                "leisure_fare_elasticity": elasticities["leisure"],
                "vfr_fare_elasticity": elasticities["vfr"],
                "long_haul_fare_elasticity": elasticities["long_haul"],
                "transfer_fare_elasticity": elasticities["transfer"],
                "premium_fare_elasticity": elasticities["premium"],
                "premium_passenger_propensity_index": premium_propensity,
                "premium_propensity_raw_index": premium_propensity_raw,
                "premium_propensity_asset_market_contribution_points": premium_asset_contribution,
                "premium_propensity_household_wealth_contribution_points": premium_wealth_contribution,
                "premium_propensity_cash_income_contribution_points": premium_cash_contribution,
                "premium_propensity_traffic_mix_contribution_points": premium_traffic_contribution,
                "premium_propensity_final_index": premium_propensity,
                "premium_propensity_boundary_state": premium_boundary_state,
                "premium_passenger_share_pct": premium_share,
                "duty_free_propensity_index": duty_free,
                "duty_free_propensity_raw_index": duty_free_raw,
                **{f"duty_free_propensity_{name}_contribution_points": value for name, value in duty_free_parts.items()},
                "duty_free_propensity_final_index": duty_free,
                "duty_free_propensity_boundary_state": "floor" if duty_free_raw < 45.0 else "cap" if duty_free_raw > 175.0 else "none",
                "luxury_retail_propensity_index": luxury,
                "luxury_retail_propensity_raw_index": luxury_raw,
                **{f"luxury_retail_propensity_{name}_contribution_points": value for name, value in luxury_parts.items()},
                "luxury_retail_propensity_final_index": luxury,
                "luxury_retail_propensity_boundary_state": "floor" if luxury_raw < 40.0 else "cap" if luxury_raw > 180.0 else "none",
                "electronics_retail_propensity_index": electronics,
                "electronics_retail_propensity_raw_index": electronics_raw,
                **{f"electronics_retail_propensity_{name}_contribution_points": value for name, value in electronics_parts.items()},
                "electronics_retail_propensity_final_index": electronics,
                "electronics_retail_propensity_boundary_state": "floor" if electronics_raw < 42.0 else "cap" if electronics_raw > 168.0 else "none",
                "food_beverage_propensity_index": food_beverage,
                "food_beverage_propensity_raw_index": food_beverage_raw,
                **{f"food_beverage_propensity_{name}_contribution_points": value for name, value in food_beverage_parts.items()},
                "food_beverage_propensity_final_index": food_beverage,
                "food_beverage_propensity_boundary_state": "floor" if food_beverage_raw < 55.0 else "cap" if food_beverage_raw > 165.0 else "none",
                "general_retail_propensity_index": general_retail,
                "general_retail_propensity_raw_index": general_retail_raw,
                **{f"general_retail_propensity_{name}_contribution_points": value for name, value in general_retail_parts.items()},
                "general_retail_propensity_final_index": general_retail,
                "general_retail_propensity_boundary_state": "floor" if general_retail_raw < 50.0 else "cap" if general_retail_raw > 165.0 else "none",
                "aviation_demand_regime": regime,
                "airport_event_hint": event_hint,
                "airport_event_pressure_index": event_pressure,
                "aviation_event_impulse_pct": event_impulse,
                "branch_scenario_id": str(row.get("branch_scenario_id") or "none"),
                "branch_scenario_state": str(row.get("branch_scenario_state") or "baseline"),
                "branch_effect_phase": str(row.get("branch_effect_phase") or "none"),
                "regional_branch_transmission_active": str(row.get("regional_branch_transmission_active") or "false"),
                "regional_branch_strength_index": metrics["branch_stress"],
                "source_regional_seed_momentum_label": str(row.get("regional_seed_momentum_label") or "none"),
                "source_regional_seed_effective_growth_bias_pct": metrics["seed_growth_bias"],
                "source_regional_seed_aviation_propensity_bias_pct": metrics["seed_aviation_bias"],
                "source_regional_seed_investment_cycle_bias_pct": metrics["seed_investment_bias"],
                "source_regional_seed_openness_bias_pct": metrics["seed_openness_bias"],
                "source_regional_seed_demand_multiplier": metrics["seed_demand_multiplier"],
                "input_regional_gdp_growth_pct": metrics["growth"],
                "input_real_income_growth_pct": metrics["income_growth"],
                "input_consumer_confidence_index": metrics["confidence"],
                "input_macro_stress_index": metrics["stress"],
                "input_energy_cost_pressure_index": metrics["energy"],
                "input_currency_pressure_index": metrics["currency_pressure"],
                "input_hy_spread_bps": metrics["hy"],
                "input_asset_market_impulse_index": metrics["asset_market"],
                "input_household_wealth_consumption_impulse": metrics["wealth_impulse"],
                "input_real_disposable_income_growth_pct": metrics["income_growth"],
                "input_equity_price_return_pct": metrics["equity_price_return"],
                "input_equity_valuation_pe": metrics["equity_valuation_pe"],
                **{
                    f"demand_{target}_{name}_contribution_pp": decomposition[target][name]
                    for target in ("total", "business", "leisure", "vfr", "long_haul", "transfer")
                    for name in DEMAND_CONTRIBUTION_NAMES
                },
                **{
                    key: value
                    for target in ("total", "business", "leisure", "vfr", "long_haul", "transfer")
                    for key, value in {
                        f"demand_{target}_base_contribution_pp": decomposition[target]["base"],
                        f"demand_{target}_raw_growth_pct": decomposition[target]["raw"],
                        f"demand_{target}_boundary_adjustment_pp": decomposition[target]["boundary_adjustment"],
                        f"demand_{target}_smoothing_adjustment_pp": (
                            (total_growth if target == "total" else component_growth[target])
                            - decomposition[target]["final"]
                        ),
                        f"demand_{target}_final_growth_pct": total_growth if target == "total" else component_growth[target],
                    }.items()
                },
            }
        )
        output.append(item)
        state_by_seed[seed] = {
            "values": component_values,
            "growth": component_growth,
            "total_index": total_index,
            "metrics": metrics,
        }

    return output


def summarize_region_seed(rows: list[dict[str, Any]]) -> dict[str, Any]:
    data = rows[1:] if len(rows) > 1 else rows
    growth = [as_float(row, "regional_air_demand_growth_pct") for row in data]
    price = [as_float(row, "airfare_price_sensitivity_index") for row in data]
    event_rows = [row for row in rows if str(row.get("airport_event_hint") or "none") != "none"]
    final = rows[-1]
    return {
        "region_id": final["region_id"],
        "region_name": final["region_name"],
        "seed": int(final["seed"]),
        "start_year": int(rows[0]["year"]),
        "end_year": int(final["year"]),
        "average_air_demand_growth_pct": round(mean(growth), 3) if growth else 0.0,
        "air_demand_growth_std_pct": round(pstdev(growth), 3) if len(growth) > 1 else 0.0,
        "average_price_sensitivity_index": round(mean(price), 2) if price else 0.0,
        "event_hint_rows": len(event_rows),
        "source_regional_seed_momentum_label": final.get("source_regional_seed_momentum_label", "none"),
        "source_regional_seed_aviation_propensity_bias_pct": as_float(final, "source_regional_seed_aviation_propensity_bias_pct"),
        "source_regional_seed_demand_multiplier": as_float(final, "source_regional_seed_demand_multiplier", 1.0),
        "final_regional_air_demand_index": as_float(final, "regional_air_demand_index"),
        "final_premium_passenger_propensity_index": as_float(final, "premium_passenger_propensity_index"),
        "final_aviation_demand_regime": final["aviation_demand_regime"],
    }


def parse_args() -> argparse.Namespace:
    airport_dir = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Generate regional aviation demand indices from regional macro data.")
    parser.add_argument("--region", default="north_america", choices=sorted(AVIATION_REGION_CONFIGS))
    parser.add_argument(
        "--regional-csv",
        type=Path,
        default=None,
        help="Defaults to airport/output/regional_macro/<region>_regional_macro_seed_sweep.csv.",
    )
    parser.add_argument(
        "--reconciled-csv",
        type=Path,
        default=airport_dir / "output" / "regional_macro_reconciled" / "regional_macro_reconciled_seed_sweep.csv",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=airport_dir / "output" / "regional_aviation_demand",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    params = AVIATION_REGION_CONFIGS[args.region]
    if args.regional_csv is None:
        airport_dir = Path(__file__).resolve().parents[1]
        args.regional_csv = airport_dir / "output" / "regional_macro" / f"{args.region}_regional_macro_seed_sweep.csv"
    rows = load_region_inputs(args.region, args.regional_csv, args.reconciled_csv)
    if not rows:
        raise SystemExit(f"No rows found for region {args.region}")
    output = simulate_region_aviation_demand(rows, params)
    summaries = []
    for seed in sorted({int(row["seed"]) for row in output}):
        summaries.append(summarize_region_seed([row for row in output if int(row["seed"]) == seed]))

    csv_path = args.output_dir / f"{args.region}_aviation_demand_seed_sweep.csv"
    json_path = args.output_dir / f"{args.region}_aviation_demand_seed_sweep.json"
    summary_path = args.output_dir / f"{args.region}_aviation_demand_summary.json"
    js_path = args.output_dir / f"{args.region}_aviation_demand_viewer_data.js"

    write_csv(csv_path, output, AVIATION_DEMAND_FIELDS)
    write_json(
        json_path,
        {
            "regional_aviation_demand_param_version": AVIATION_DEMAND_PARAM_VERSION,
            "regional_aviation_demand_interface_version": AVIATION_DEMAND_INTERFACE_VERSION,
            "region": args.region,
            "rows": len(output),
            "params": asdict(params),
            "summaries": summaries,
            "outputs": {
                "csv": str(csv_path),
                "json": str(json_path),
                "summary": str(summary_path),
                "viewer_data_js": str(js_path),
            },
        },
    )
    write_json(
        summary_path,
        {
            "regional_aviation_demand_param_version": AVIATION_DEMAND_PARAM_VERSION,
            "region": args.region,
            "summaries": summaries,
        },
    )
    write_viewer_data_js(js_path, output)
    print(
        json.dumps(
            {
                "region": args.region,
                "rows": len(output),
                "csv": str(csv_path),
                "summary": str(summary_path),
                "viewer_data_js": str(js_path),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
