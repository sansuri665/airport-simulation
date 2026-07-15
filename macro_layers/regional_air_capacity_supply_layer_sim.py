from __future__ import annotations

from importlib import import_module

_SIBLING_PREFIX = f"{__package__}." if __package__ else ""
simulation_io = import_module(f"{_SIBLING_PREFIX}simulation_io")
simulation_utils = import_module(f"{_SIBLING_PREFIX}simulation_utils")

read_csv = simulation_io.read_csv_utf8
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


AIR_SUPPLY_PARAM_VERSION = "regional-air-capacity-supply-layer-v0.3"
AIR_SUPPLY_INTERFACE_VERSION = "regional-air-capacity-supply-interface-v0.3"


AIR_SUPPLY_FIELDS = [
    "regional_air_supply_param_version",
    "regional_air_supply_interface_version",
    "region_id",
    "region_name",
    "year_index",
    "year",
    "seed",
    "source_aviation_demand_scope",
    "baseline_region_passenger_demand_million",
    "potential_passenger_demand_index",
    "regional_air_capacity_index",
    "regional_air_capacity_growth_pct",
    "available_seat_capacity_index",
    "normalized_capacity_pressure_index",
    "capacity_utilization_pct",
    "target_load_factor_pct",
    "load_factor_pct",
    "capacity_fulfillment_pct",
    "served_passenger_demand_index",
    "unmet_passenger_demand_index",
    "capacity_fare_pressure_index",
    "supply_regime",
    "potential_passengers_million",
    "scheduled_seats_million",
    "operational_availability_pct",
    "available_seats_million",
    "reference_effective_passenger_capacity_million",
    "reference_served_passengers_million",
    "reference_unmet_passengers_million",
    "served_passengers_million",
    "unmet_passengers_million",
    "business_served_index",
    "leisure_served_index",
    "vfr_served_index",
    "long_haul_served_index",
    "transfer_served_index",
    "business_fulfillment_pct",
    "leisure_fulfillment_pct",
    "vfr_fulfillment_pct",
    "long_haul_fulfillment_pct",
    "transfer_fulfillment_pct",
    "airline_capacity_confidence_index",
    "airline_profit_pressure_index",
    "fleet_expansion_appetite_index",
    "route_growth_appetite_index",
    "capacity_cut_risk_index",
    "aircraft_delivery_constraint_index",
    "crew_labor_constraint_index",
    "maintenance_cost_pressure_index",
    "airport_slot_constraint_index",
    "supply_event_impulse_pct",
    "airport_event_hint",
    "airport_event_pressure_index",
    "branch_scenario_id",
    "branch_scenario_state",
    "branch_effect_phase",
    "source_regional_seed_momentum_label",
    "source_regional_seed_aviation_propensity_bias_pct",
    "source_regional_seed_investment_cycle_bias_pct",
    "source_regional_seed_openness_bias_pct",
    "source_regional_seed_demand_multiplier",
    "input_regional_air_demand_growth_pct",
    "input_airfare_pressure_index",
    "input_price_sensitivity_index",
    "input_business_travel_share_pct",
    "input_leisure_travel_share_pct",
    "input_vfr_travel_share_pct",
    "input_long_haul_share_pct",
    "input_transfer_share_pct",
    "input_premium_passenger_share_pct",
    "input_macro_stress_index",
    "input_energy_cost_pressure_index",
    "input_currency_pressure_index",
    "input_hy_spread_bps",
    "input_consumer_confidence_index",
]


@dataclass(frozen=True)
class RegionalAirSupplyParams:
    region_id: str
    region_name: str
    baseline_region_passenger_demand_million: float
    baseline_load_factor_pct: float
    base_air_capacity_index: float
    domestic_supply_depth: float
    international_supply_flexibility: float
    transfer_hub_priority: float
    airport_slot_constraint_base: float
    aircraft_delivery_constraint_base: float
    crew_labor_constraint_base: float
    maintenance_cost_pressure_base: float
    supply_growth_persistence: float
    supply_adjustment_speed: float
    max_capacity_growth_pct: float
    max_capacity_contraction_pct: float
    business_displacement_weight: float
    leisure_displacement_weight: float
    vfr_displacement_weight: float
    long_haul_displacement_weight: float
    transfer_displacement_weight: float


AIR_SUPPLY_REGION_CONFIGS = {
    "north_america": RegionalAirSupplyParams(
        region_id="north_america",
        region_name="北美",
        baseline_region_passenger_demand_million=1200.0,
        baseline_load_factor_pct=83.0,
        base_air_capacity_index=100.0,
        domestic_supply_depth=0.92,
        international_supply_flexibility=0.64,
        transfer_hub_priority=0.46,
        airport_slot_constraint_base=22.0,
        aircraft_delivery_constraint_base=18.0,
        crew_labor_constraint_base=22.0,
        maintenance_cost_pressure_base=20.0,
        supply_growth_persistence=0.42,
        supply_adjustment_speed=0.52,
        max_capacity_growth_pct=5.2,
        max_capacity_contraction_pct=5.8,
        business_displacement_weight=0.34,
        leisure_displacement_weight=1.32,
        vfr_displacement_weight=0.72,
        long_haul_displacement_weight=0.86,
        transfer_displacement_weight=0.94,
    ),
    "china_mainland": RegionalAirSupplyParams(
        region_id="china_mainland",
        region_name="中国大陆",
        baseline_region_passenger_demand_million=820.0,
        baseline_load_factor_pct=82.0,
        base_air_capacity_index=100.0,
        domestic_supply_depth=0.94,
        international_supply_flexibility=0.54,
        transfer_hub_priority=0.34,
        airport_slot_constraint_base=26.0,
        aircraft_delivery_constraint_base=20.0,
        crew_labor_constraint_base=20.0,
        maintenance_cost_pressure_base=22.0,
        supply_growth_persistence=0.34,
        supply_adjustment_speed=0.60,
        max_capacity_growth_pct=6.7,
        max_capacity_contraction_pct=6.0,
        business_displacement_weight=0.42,
        leisure_displacement_weight=1.42,
        vfr_displacement_weight=0.78,
        long_haul_displacement_weight=1.02,
        transfer_displacement_weight=1.06,
    ),
    "west_north_europe": RegionalAirSupplyParams(
        region_id="west_north_europe",
        region_name="西欧/北欧",
        baseline_region_passenger_demand_million=900.0,
        baseline_load_factor_pct=84.0,
        base_air_capacity_index=100.0,
        domestic_supply_depth=0.70,
        international_supply_flexibility=0.72,
        transfer_hub_priority=0.52,
        airport_slot_constraint_base=38.0,
        aircraft_delivery_constraint_base=21.0,
        crew_labor_constraint_base=23.0,
        maintenance_cost_pressure_base=23.0,
        supply_growth_persistence=0.46,
        supply_adjustment_speed=0.48,
        max_capacity_growth_pct=4.0,
        max_capacity_contraction_pct=5.2,
        business_displacement_weight=0.30,
        leisure_displacement_weight=1.46,
        vfr_displacement_weight=0.74,
        long_haul_displacement_weight=0.82,
        transfer_displacement_weight=0.78,
    ),
    "japan_korea": RegionalAirSupplyParams(
        region_id="japan_korea",
        region_name="日韩",
        baseline_region_passenger_demand_million=330.0,
        baseline_load_factor_pct=81.5,
        base_air_capacity_index=100.0,
        domestic_supply_depth=0.78,
        international_supply_flexibility=0.62,
        transfer_hub_priority=0.36,
        airport_slot_constraint_base=32.0,
        aircraft_delivery_constraint_base=20.0,
        crew_labor_constraint_base=25.0,
        maintenance_cost_pressure_base=24.0,
        supply_growth_persistence=0.48,
        supply_adjustment_speed=0.46,
        max_capacity_growth_pct=3.6,
        max_capacity_contraction_pct=4.7,
        business_displacement_weight=0.28,
        leisure_displacement_weight=1.36,
        vfr_displacement_weight=0.70,
        long_haul_displacement_weight=0.88,
        transfer_displacement_weight=0.92,
    ),
    "southeast_asia": RegionalAirSupplyParams(
        region_id="southeast_asia",
        region_name="东南亚",
        baseline_region_passenger_demand_million=520.0,
        baseline_load_factor_pct=83.5,
        base_air_capacity_index=100.0,
        domestic_supply_depth=0.70,
        international_supply_flexibility=0.82,
        transfer_hub_priority=0.58,
        airport_slot_constraint_base=30.0,
        aircraft_delivery_constraint_base=24.0,
        crew_labor_constraint_base=24.0,
        maintenance_cost_pressure_base=23.0,
        supply_growth_persistence=0.38,
        supply_adjustment_speed=0.56,
        max_capacity_growth_pct=5.6,
        max_capacity_contraction_pct=6.2,
        business_displacement_weight=0.42,
        leisure_displacement_weight=1.56,
        vfr_displacement_weight=0.82,
        long_haul_displacement_weight=0.98,
        transfer_displacement_weight=0.76,
    ),
    "south_asia_india": RegionalAirSupplyParams(
        region_id="south_asia_india",
        region_name="南亚/印度",
        baseline_region_passenger_demand_million=390.0,
        baseline_load_factor_pct=84.0,
        base_air_capacity_index=100.0,
        domestic_supply_depth=0.88,
        international_supply_flexibility=0.48,
        transfer_hub_priority=0.30,
        airport_slot_constraint_base=34.0,
        aircraft_delivery_constraint_base=27.0,
        crew_labor_constraint_base=26.0,
        maintenance_cost_pressure_base=25.0,
        supply_growth_persistence=0.38,
        supply_adjustment_speed=0.56,
        max_capacity_growth_pct=5.4,
        max_capacity_contraction_pct=6.5,
        business_displacement_weight=0.48,
        leisure_displacement_weight=1.72,
        vfr_displacement_weight=0.74,
        long_haul_displacement_weight=1.10,
        transfer_displacement_weight=1.18,
    ),
    "hk_macao_taiwan": RegionalAirSupplyParams(
        region_id="hk_macao_taiwan",
        region_name="港澳台",
        baseline_region_passenger_demand_million=230.0,
        baseline_load_factor_pct=82.5,
        base_air_capacity_index=100.0,
        domestic_supply_depth=0.32,
        international_supply_flexibility=0.86,
        transfer_hub_priority=0.70,
        airport_slot_constraint_base=44.0,
        aircraft_delivery_constraint_base=21.0,
        crew_labor_constraint_base=25.0,
        maintenance_cost_pressure_base=23.0,
        supply_growth_persistence=0.50,
        supply_adjustment_speed=0.45,
        max_capacity_growth_pct=3.9,
        max_capacity_contraction_pct=5.2,
        business_displacement_weight=0.26,
        leisure_displacement_weight=1.40,
        vfr_displacement_weight=0.70,
        long_haul_displacement_weight=0.82,
        transfer_displacement_weight=0.64,
    ),
    "middle_east_gulf": RegionalAirSupplyParams(
        region_id="middle_east_gulf",
        region_name="中东/海湾",
        baseline_region_passenger_demand_million=310.0,
        baseline_load_factor_pct=82.5,
        base_air_capacity_index=100.0,
        domestic_supply_depth=0.38,
        international_supply_flexibility=0.94,
        transfer_hub_priority=0.88,
        airport_slot_constraint_base=28.0,
        aircraft_delivery_constraint_base=19.0,
        crew_labor_constraint_base=22.0,
        maintenance_cost_pressure_base=21.0,
        supply_growth_persistence=0.32,
        supply_adjustment_speed=0.62,
        max_capacity_growth_pct=6.4,
        max_capacity_contraction_pct=5.8,
        business_displacement_weight=0.24,
        leisure_displacement_weight=1.20,
        vfr_displacement_weight=0.72,
        long_haul_displacement_weight=0.58,
        transfer_displacement_weight=0.38,
    ),
    "oceania": RegionalAirSupplyParams(
        region_id="oceania",
        region_name="大洋洲",
        baseline_region_passenger_demand_million=165.0,
        baseline_load_factor_pct=82.0,
        base_air_capacity_index=100.0,
        domestic_supply_depth=0.64,
        international_supply_flexibility=0.62,
        transfer_hub_priority=0.28,
        airport_slot_constraint_base=30.0,
        aircraft_delivery_constraint_base=22.0,
        crew_labor_constraint_base=23.0,
        maintenance_cost_pressure_base=23.0,
        supply_growth_persistence=0.48,
        supply_adjustment_speed=0.46,
        max_capacity_growth_pct=4.2,
        max_capacity_contraction_pct=5.4,
        business_displacement_weight=0.34,
        leisure_displacement_weight=1.46,
        vfr_displacement_weight=0.74,
        long_haul_displacement_weight=0.92,
        transfer_displacement_weight=1.02,
    ),
    "south_east_europe_mediterranean": RegionalAirSupplyParams(
        region_id="south_east_europe_mediterranean",
        region_name="南欧/东欧/地中海",
        baseline_region_passenger_demand_million=430.0,
        baseline_load_factor_pct=84.0,
        base_air_capacity_index=100.0,
        domestic_supply_depth=0.58,
        international_supply_flexibility=0.78,
        transfer_hub_priority=0.34,
        airport_slot_constraint_base=27.0,
        aircraft_delivery_constraint_base=22.0,
        crew_labor_constraint_base=22.0,
        maintenance_cost_pressure_base=24.0,
        supply_growth_persistence=0.30,
        supply_adjustment_speed=0.62,
        max_capacity_growth_pct=5.2,
        max_capacity_contraction_pct=1.2,
        business_displacement_weight=0.42,
        leisure_displacement_weight=1.62,
        vfr_displacement_weight=0.78,
        long_haul_displacement_weight=1.04,
        transfer_displacement_weight=0.96,
    ),
    "central_asia_turkey_eurasia": RegionalAirSupplyParams(
        region_id="central_asia_turkey_eurasia",
        region_name="中亚/土耳其/欧亚桥",
        baseline_region_passenger_demand_million=260.0,
        baseline_load_factor_pct=82.0,
        base_air_capacity_index=100.0,
        domestic_supply_depth=0.58,
        international_supply_flexibility=0.76,
        transfer_hub_priority=0.72,
        airport_slot_constraint_base=31.0,
        aircraft_delivery_constraint_base=25.0,
        crew_labor_constraint_base=25.0,
        maintenance_cost_pressure_base=25.0,
        supply_growth_persistence=0.40,
        supply_adjustment_speed=0.50,
        max_capacity_growth_pct=4.8,
        max_capacity_contraction_pct=6.4,
        business_displacement_weight=0.44,
        leisure_displacement_weight=1.58,
        vfr_displacement_weight=0.82,
        long_haul_displacement_weight=0.98,
        transfer_displacement_weight=0.62,
    ),
    "north_africa": RegionalAirSupplyParams(
        region_id="north_africa",
        region_name="北非",
        baseline_region_passenger_demand_million=210.0,
        baseline_load_factor_pct=82.5,
        base_air_capacity_index=100.0,
        domestic_supply_depth=0.54,
        international_supply_flexibility=0.66,
        transfer_hub_priority=0.34,
        airport_slot_constraint_base=29.0,
        aircraft_delivery_constraint_base=28.0,
        crew_labor_constraint_base=27.0,
        maintenance_cost_pressure_base=27.0,
        supply_growth_persistence=0.44,
        supply_adjustment_speed=0.44,
        max_capacity_growth_pct=4.4,
        max_capacity_contraction_pct=6.8,
        business_displacement_weight=0.54,
        leisure_displacement_weight=1.82,
        vfr_displacement_weight=0.90,
        long_haul_displacement_weight=1.14,
        transfer_displacement_weight=1.12,
    ),
    "latin_america_caribbean": RegionalAirSupplyParams(
        region_id="latin_america_caribbean",
        region_name="拉美/加勒比",
        baseline_region_passenger_demand_million=620.0,
        baseline_load_factor_pct=83.0,
        base_air_capacity_index=100.0,
        domestic_supply_depth=0.74,
        international_supply_flexibility=0.68,
        transfer_hub_priority=0.36,
        airport_slot_constraint_base=30.0,
        aircraft_delivery_constraint_base=24.0,
        crew_labor_constraint_base=25.0,
        maintenance_cost_pressure_base=25.0,
        supply_growth_persistence=0.42,
        supply_adjustment_speed=0.50,
        max_capacity_growth_pct=4.8,
        max_capacity_contraction_pct=6.2,
        business_displacement_weight=0.48,
        leisure_displacement_weight=1.66,
        vfr_displacement_weight=0.76,
        long_haul_displacement_weight=1.04,
        transfer_displacement_weight=1.08,
    ),
    "sub_saharan_africa": RegionalAirSupplyParams(
        region_id="sub_saharan_africa",
        region_name="撒哈拉以南非洲",
        baseline_region_passenger_demand_million=180.0,
        baseline_load_factor_pct=81.5,
        base_air_capacity_index=100.0,
        domestic_supply_depth=0.56,
        international_supply_flexibility=0.48,
        transfer_hub_priority=0.44,
        airport_slot_constraint_base=36.0,
        aircraft_delivery_constraint_base=34.0,
        crew_labor_constraint_base=32.0,
        maintenance_cost_pressure_base=31.0,
        supply_growth_persistence=0.50,
        supply_adjustment_speed=0.38,
        max_capacity_growth_pct=4.2,
        max_capacity_contraction_pct=7.0,
        business_displacement_weight=0.62,
        leisure_displacement_weight=1.92,
        vfr_displacement_weight=0.82,
        long_haul_displacement_weight=1.18,
        transfer_displacement_weight=0.94,
    ),
}



def pct_change(current: float, previous: float) -> float:
    if previous == 0:
        return 0.0
    return (current / previous - 1.0) * 100.0


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


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_viewer_data_js(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(rows, ensure_ascii=False, separators=(",", ":"))
    path.write_text(f"window.REGIONAL_AIR_CAPACITY_SUPPLY_DATA = {payload};\n", encoding="utf-8")


def supply_event_impulse(row: dict[str, Any]) -> float:
    hint = str(row.get("airport_event_hint") or "none")
    pressure = as_float(row, "airport_event_pressure_index")
    branch_state = str(row.get("branch_scenario_state") or "baseline")
    phase = str(row.get("branch_effect_phase") or "none")
    if hint == "fare_shock_leisure_drag":
        return -0.55 - 0.010 * pressure
    if hint == "outbound_fx_squeeze":
        return -0.38 - 0.007 * pressure
    if hint == "business_travel_credit_drag":
        return -0.62 - 0.010 * pressure
    if hint == "recovery_reversal_warning":
        return -0.42 - 0.006 * pressure
    if hint == "broad_travel_recovery":
        return 0.32 + 0.005 * pressure
    if hint == "premium_mix_volatility":
        return -0.12 - 0.002 * pressure
    if branch_state in {"occurred", "counterfactual"} and phase in {"impact", "tail"}:
        return -0.20 - 0.004 * pressure
    return 0.0


def derive_supply_pressures(
    row: dict[str, Any],
    params: RegionalAirSupplyParams,
    previous_capacity_index: float,
) -> dict[str, float]:
    demand_index = as_float(row, "regional_air_demand_index", 100.0)
    demand_growth = as_float(row, "regional_air_demand_growth_pct")
    fare_pressure = as_float(row, "airfare_pressure_index", 50.0)
    premium_share = as_float(row, "premium_passenger_share_pct", 15.0)
    business_share = as_float(row, "business_travel_share_pct", 25.0)
    leisure_share = as_float(row, "leisure_travel_share_pct", 30.0)
    transfer_share = as_float(row, "transfer_share_pct", 8.0)
    confidence = as_float(row, "input_consumer_confidence_index", 50.0)
    stress = as_float(row, "input_macro_stress_index", 25.0)
    energy = as_float(row, "input_energy_cost_pressure_index", 50.0)
    currency = as_float(row, "input_currency_pressure_index", 35.0)
    hy = as_float(row, "input_hy_spread_bps", 450.0)

    demand_gap = demand_index - previous_capacity_index
    positive_gap = max(0.0, demand_gap)
    financing_pressure = max(0.0, hy - 500.0) / 100.0

    delivery = clamp(
        params.aircraft_delivery_constraint_base
        + max(0.0, demand_growth) * 3.0
        + positive_gap * 0.07
        + max(0.0, hy - 550.0) * 0.022
        + max(0.0, energy - 62.0) * 0.20,
        4.0,
        85.0,
    )
    crew = clamp(
        params.crew_labor_constraint_base
        + max(0.0, demand_growth) * 1.8
        + positive_gap * 0.08
        + max(0.0, stress - 30.0) * 0.36,
        4.0,
        85.0,
    )
    maintenance = clamp(
        params.maintenance_cost_pressure_base
        + max(0.0, energy - 52.0) * 0.34
        + max(0.0, currency - 40.0) * 0.16
        + max(0.0, stress - 30.0) * 0.20,
        5.0,
        90.0,
    )
    slot = clamp(
        params.airport_slot_constraint_base
        + positive_gap * 0.11
        + max(0.0, business_share - 30.0) * 0.16
        + max(0.0, transfer_share - 8.0) * 0.22,
        5.0,
        95.0,
    )
    profit_pressure = clamp(
        43.0
        + (energy - 50.0) * 0.32
        + (fare_pressure - 50.0) * 0.20
        + financing_pressure * 1.8
        - (premium_share - 16.0) * 0.22
        - (business_share - 28.0) * 0.12,
        5.0,
        100.0,
    )
    capacity_confidence = clamp(
        53.0
        + demand_growth * 0.82
        + (confidence - 45.0) * 0.22
        - (stress - 25.0) * 0.22
        - financing_pressure * 1.6
        - max(0.0, energy - 65.0) * 0.10,
        0.0,
        100.0,
    )
    fleet_appetite = clamp(
        42.0
        + demand_growth * 0.78
        + positive_gap * 0.17
        + capacity_confidence * 0.24
        - delivery * 0.19
        - profit_pressure * 0.15,
        0.0,
        100.0,
    )
    route_appetite = clamp(
        46.0
        + demand_growth * 0.62
        + max(0.0, business_share - 26.0) * 0.16
        + max(0.0, leisure_share - 28.0) * 0.10
        + capacity_confidence * 0.18
        - slot * 0.16
        - profit_pressure * 0.12,
        0.0,
        100.0,
    )
    cut_risk = clamp(
        24.0
        - demand_growth * 1.15
        + profit_pressure * 0.26
        + stress * 0.18
        + financing_pressure * 2.0
        - capacity_confidence * 0.16,
        0.0,
        100.0,
    )
    return {
        "demand_gap": demand_gap,
        "delivery": delivery,
        "crew": crew,
        "maintenance": maintenance,
        "slot": slot,
        "profit_pressure": profit_pressure,
        "capacity_confidence": capacity_confidence,
        "fleet_appetite": fleet_appetite,
        "route_appetite": route_appetite,
        "cut_risk": cut_risk,
    }


def target_capacity_growth(
    row: dict[str, Any],
    params: RegionalAirSupplyParams,
    previous_capacity_index: float,
    pressures: dict[str, float],
) -> float:
    demand_growth = as_float(row, "regional_air_demand_growth_pct")
    business_share = as_float(row, "business_travel_share_pct", 28.0)
    premium_share = as_float(row, "premium_passenger_share_pct", 16.0)
    confidence = as_float(row, "input_consumer_confidence_index", 50.0)
    stress = as_float(row, "input_macro_stress_index", 25.0)
    energy = as_float(row, "input_energy_cost_pressure_index", 50.0)
    fare_pressure = as_float(row, "airfare_pressure_index", 50.0)
    hy = as_float(row, "input_hy_spread_bps", 450.0)
    aviation_seed = as_float(row, "source_regional_seed_aviation_propensity_bias_pct")
    investment_seed = as_float(row, "source_regional_seed_investment_cycle_bias_pct")
    openness_seed = as_float(row, "source_regional_seed_openness_bias_pct")
    demand_multiplier_gap = (as_float(row, "source_regional_seed_demand_multiplier", 1.0) - 1.0) * 100.0

    demand_gap = pressures["demand_gap"]
    event_impulse = supply_event_impulse(row)
    demand_signal = (
        0.74 * demand_growth
        + 0.040 * max(0.0, demand_gap)
        + 0.020 * aviation_seed
        + 0.012 * demand_multiplier_gap
    )
    profit_signal = (
        +0.025 * (business_share - 28.0)
        + 0.020 * (premium_share - 16.0)
        - 0.030 * max(0.0, energy - 55.0)
        - 0.018 * max(0.0, fare_pressure - 60.0)
    )
    financing_signal = (
        -0.28 * max(0.0, hy - 520.0) / 100.0
        - 0.014 * max(0.0, stress - 28.0)
        + 0.014 * max(0.0, confidence - 48.0)
        + 0.018 * investment_seed
    )
    operating_drag = (
        0.006 * max(0.0, pressures["delivery"] - 24.0)
        + 0.005 * max(0.0, pressures["crew"] - 26.0)
        + 0.006 * max(0.0, pressures["maintenance"] - 25.0)
        + 0.004 * max(0.0, pressures["slot"] - 30.0)
    )
    route_openness_signal = 0.012 * openness_seed + 0.008 * investment_seed
    target = demand_signal + profit_signal + financing_signal + route_openness_signal - operating_drag + event_impulse
    return clamp(target, -params.max_capacity_contraction_pct, params.max_capacity_growth_pct)


def segment_fulfillment(
    row: dict[str, Any],
    params: RegionalAirSupplyParams,
    total_fulfillment: float,
    capacity_fare_pressure: float,
) -> dict[str, float]:
    shortage = max(0.0, 100.0 - total_fulfillment)
    price_squeeze = max(0.0, capacity_fare_pressure - 62.0) / 10.0
    energy = as_float(row, "input_energy_cost_pressure_index", 50.0)
    return {
        "business": clamp(
            100.0
            - shortage * params.business_displacement_weight
            - price_squeeze * as_float(row, "business_fare_elasticity", 0.25) * 1.2,
            72.0,
            100.0,
        ),
        "leisure": clamp(
            100.0
            - shortage * params.leisure_displacement_weight
            - price_squeeze * as_float(row, "leisure_fare_elasticity", 1.35) * 2.2,
            48.0,
            100.0,
        ),
        "vfr": clamp(
            100.0
            - shortage * params.vfr_displacement_weight
            - price_squeeze * as_float(row, "vfr_fare_elasticity", 0.70) * 1.5,
            58.0,
            100.0,
        ),
        "long_haul": clamp(
            100.0
            - shortage * params.long_haul_displacement_weight
            - price_squeeze * as_float(row, "long_haul_fare_elasticity", 0.90) * 1.8
            - max(0.0, energy - 65.0) * 0.04,
            52.0,
            100.0,
        ),
        "transfer": clamp(
            100.0
            - shortage * params.transfer_displacement_weight
            - price_squeeze * as_float(row, "transfer_fare_elasticity", 1.05) * 1.8
            + params.transfer_hub_priority * 1.8,
            52.0,
            100.0,
        ),
    }


def supply_regime(
    row: dict[str, Any],
    capacity_growth: float,
    utilization: float,
    fulfillment: float,
    load_factor: float,
    fare_pressure: float,
) -> str:
    hint = str(row.get("airport_event_hint") or "none")
    if hint in {"business_travel_credit_drag", "fare_shock_leisure_drag", "outbound_fx_squeeze"}:
        return f"supply_{hint}"
    if fulfillment < 82.0:
        return "capacity_rationing"
    if fulfillment < 91.0 or utilization >= 110.0:
        return "capacity_shortage"
    if load_factor >= 90.0 and fare_pressure >= 68.0:
        return "high_load_fare_pressure"
    if capacity_growth >= 3.0:
        return "capacity_expansion"
    if capacity_growth <= -2.0:
        return "capacity_drawdown"
    return "balanced_supply"


def simulate_region_air_supply(
    demand_rows: list[dict[str, Any]],
    params: RegionalAirSupplyParams,
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    state_by_seed: dict[int, dict[str, float]] = {}

    for row in demand_rows:
        seed = int(as_float(row, "seed"))
        previous = state_by_seed.get(seed)
        previous_capacity = previous["capacity_index"] if previous else params.base_air_capacity_index
        previous_growth = previous["capacity_growth"] if previous else 0.0

        demand_index = as_float(row, "regional_air_demand_index", 100.0)
        pressures = derive_supply_pressures(row, params, previous_capacity)
        target_growth = target_capacity_growth(row, params, previous_capacity, pressures)

        if previous is None:
            capacity_growth = 0.0
            capacity_index = params.base_air_capacity_index
        else:
            effective_speed = params.supply_adjustment_speed * (1.0 - params.supply_growth_persistence * 0.35)
            capacity_growth = clamp(
                smooth(previous_growth, target_growth, effective_speed),
                -params.max_capacity_contraction_pct,
                params.max_capacity_growth_pct,
            )
            capacity_index = previous_capacity * (1.0 + capacity_growth / 100.0)

        # This normalized pressure ratio remains the regional signal consumed by
        # fare, regime, and downstream city-supply calculations.  It is not a
        # literal passenger-to-seat utilization rate.
        normalized_capacity_pressure = clamp(
            demand_index / max(1.0, capacity_index) * 100.0,
            45.0,
            145.0,
        )
        operational_drag = max(0.0, pressures["maintenance"] - 70.0) * 0.03 + max(0.0, pressures["crew"] - 76.0) * 0.02
        target_load_factor = clamp(
            params.baseline_load_factor_pct
            + (normalized_capacity_pressure - 100.0) * 0.32
            - max(0.0, 92.0 - normalized_capacity_pressure) * 0.06,
            58.0,
            97.5,
        )
        potential_passengers = params.baseline_region_passenger_demand_million * demand_index / 100.0
        scheduled_seats = (
            params.baseline_region_passenger_demand_million
            / max(0.01, params.baseline_load_factor_pct / 100.0)
            * capacity_index
            / 100.0
        )
        operational_availability = clamp(100.0 - operational_drag, 0.0, 100.0)
        available_seats = scheduled_seats * operational_availability / 100.0
        reference_effective_capacity = available_seats * target_load_factor / 100.0
        reference_served_passengers = min(potential_passengers, reference_effective_capacity)
        reference_unmet_passengers = max(0.0, potential_passengers - reference_served_passengers)
        fulfillment = clamp(
            reference_served_passengers / potential_passengers * 100.0 if potential_passengers else 100.0,
            0.0,
            100.0,
        )
        load_factor = clamp(
            reference_served_passengers / available_seats * 100.0 if available_seats else 0.0,
            0.0,
            100.0,
        )
        capacity_utilization = potential_passengers / available_seats * 100.0 if available_seats else 0.0
        served_index = demand_index * fulfillment / 100.0
        unmet_index = max(0.0, demand_index - served_index)
        capacity_fare_pressure = clamp(
            50.0
            + max(0.0, normalized_capacity_pressure - 94.0) * 0.80
            + max(0.0, target_load_factor - 86.0) * 0.64
            + (pressures["profit_pressure"] - 50.0) * 0.16
            + (as_float(row, "airfare_pressure_index", 50.0) - 50.0) * 0.20,
            20.0,
            98.0,
        )
        segment = segment_fulfillment(row, params, fulfillment, capacity_fare_pressure)
        regime = supply_regime(
            row,
            capacity_growth,
            normalized_capacity_pressure,
            fulfillment,
            load_factor,
            capacity_fare_pressure,
        )

        item = round_record(
            {
                "regional_air_supply_param_version": AIR_SUPPLY_PARAM_VERSION,
                "regional_air_supply_interface_version": AIR_SUPPLY_INTERFACE_VERSION,
                "region_id": params.region_id,
                "region_name": params.region_name,
                "year_index": int(as_float(row, "year_index")),
                "year": int(as_float(row, "year")),
                "seed": seed,
                "source_aviation_demand_scope": str(row.get("aviation_demand_scope") or ""),
                "baseline_region_passenger_demand_million": params.baseline_region_passenger_demand_million,
                "potential_passenger_demand_index": demand_index,
                "regional_air_capacity_index": capacity_index,
                "regional_air_capacity_growth_pct": capacity_growth,
                "available_seat_capacity_index": capacity_index,
                "normalized_capacity_pressure_index": normalized_capacity_pressure,
                "capacity_utilization_pct": capacity_utilization,
                "target_load_factor_pct": target_load_factor,
                "load_factor_pct": load_factor,
                "capacity_fulfillment_pct": fulfillment,
                "served_passenger_demand_index": served_index,
                "unmet_passenger_demand_index": unmet_index,
                "capacity_fare_pressure_index": capacity_fare_pressure,
                "supply_regime": regime,
                "potential_passengers_million": potential_passengers,
                "scheduled_seats_million": scheduled_seats,
                "operational_availability_pct": operational_availability,
                "available_seats_million": available_seats,
                "reference_effective_passenger_capacity_million": reference_effective_capacity,
                "reference_served_passengers_million": reference_served_passengers,
                "reference_unmet_passengers_million": reference_unmet_passengers,
                # Compatibility aliases retained for existing readers.  These
                # are regional reference estimates, never city hard limits.
                "served_passengers_million": reference_served_passengers,
                "unmet_passengers_million": reference_unmet_passengers,
                "business_served_index": as_float(row, "business_travel_demand_index", 100.0) * segment["business"] / 100.0,
                "leisure_served_index": as_float(row, "leisure_travel_demand_index", 100.0) * segment["leisure"] / 100.0,
                "vfr_served_index": as_float(row, "vfr_travel_demand_index", 100.0) * segment["vfr"] / 100.0,
                "long_haul_served_index": as_float(row, "long_haul_demand_index", 100.0) * segment["long_haul"] / 100.0,
                "transfer_served_index": as_float(row, "transfer_demand_index", 100.0) * segment["transfer"] / 100.0,
                "business_fulfillment_pct": segment["business"],
                "leisure_fulfillment_pct": segment["leisure"],
                "vfr_fulfillment_pct": segment["vfr"],
                "long_haul_fulfillment_pct": segment["long_haul"],
                "transfer_fulfillment_pct": segment["transfer"],
                "airline_capacity_confidence_index": pressures["capacity_confidence"],
                "airline_profit_pressure_index": pressures["profit_pressure"],
                "fleet_expansion_appetite_index": pressures["fleet_appetite"],
                "route_growth_appetite_index": pressures["route_appetite"],
                "capacity_cut_risk_index": pressures["cut_risk"],
                "aircraft_delivery_constraint_index": pressures["delivery"],
                "crew_labor_constraint_index": pressures["crew"],
                "maintenance_cost_pressure_index": pressures["maintenance"],
                "airport_slot_constraint_index": pressures["slot"],
                "supply_event_impulse_pct": supply_event_impulse(row),
                "airport_event_hint": str(row.get("airport_event_hint") or "none"),
                "airport_event_pressure_index": as_float(row, "airport_event_pressure_index"),
                "branch_scenario_id": str(row.get("branch_scenario_id") or "none"),
                "branch_scenario_state": str(row.get("branch_scenario_state") or "baseline"),
                "branch_effect_phase": str(row.get("branch_effect_phase") or "none"),
                "source_regional_seed_momentum_label": str(row.get("source_regional_seed_momentum_label") or "none"),
                "source_regional_seed_aviation_propensity_bias_pct": as_float(row, "source_regional_seed_aviation_propensity_bias_pct"),
                "source_regional_seed_investment_cycle_bias_pct": as_float(row, "source_regional_seed_investment_cycle_bias_pct"),
                "source_regional_seed_openness_bias_pct": as_float(row, "source_regional_seed_openness_bias_pct"),
                "source_regional_seed_demand_multiplier": as_float(row, "source_regional_seed_demand_multiplier", 1.0),
                "input_regional_air_demand_growth_pct": as_float(row, "regional_air_demand_growth_pct"),
                "input_airfare_pressure_index": as_float(row, "airfare_pressure_index", 50.0),
                "input_price_sensitivity_index": as_float(row, "airfare_price_sensitivity_index", 50.0),
                "input_business_travel_share_pct": as_float(row, "business_travel_share_pct"),
                "input_leisure_travel_share_pct": as_float(row, "leisure_travel_share_pct"),
                "input_vfr_travel_share_pct": as_float(row, "vfr_travel_share_pct"),
                "input_long_haul_share_pct": as_float(row, "long_haul_share_pct"),
                "input_transfer_share_pct": as_float(row, "transfer_share_pct"),
                "input_premium_passenger_share_pct": as_float(row, "premium_passenger_share_pct"),
                "input_macro_stress_index": as_float(row, "input_macro_stress_index"),
                "input_energy_cost_pressure_index": as_float(row, "input_energy_cost_pressure_index"),
                "input_currency_pressure_index": as_float(row, "input_currency_pressure_index"),
                "input_hy_spread_bps": as_float(row, "input_hy_spread_bps"),
                "input_consumer_confidence_index": as_float(row, "input_consumer_confidence_index"),
            }
        )
        output.append(item)
        state_by_seed[seed] = {
            "capacity_index": capacity_index,
            "capacity_growth": capacity_growth,
        }

    return output


def summarize_region_seed(rows: list[dict[str, Any]]) -> dict[str, Any]:
    data = rows[1:] if len(rows) > 1 else rows
    capacity_growth = [as_float(row, "regional_air_capacity_growth_pct") for row in data]
    fulfillment = [as_float(row, "capacity_fulfillment_pct") for row in rows]
    utilization = [as_float(row, "capacity_utilization_pct") for row in rows]
    unmet = [as_float(row, "unmet_passenger_demand_index") for row in rows]
    final = rows[-1]
    return {
        "region_id": final["region_id"],
        "region_name": final["region_name"],
        "seed": int(as_float(final, "seed")),
        "start_year": int(as_float(rows[0], "year")),
        "end_year": int(as_float(final, "year")),
        "average_capacity_growth_pct": round(mean(capacity_growth), 3) if capacity_growth else 0.0,
        "capacity_growth_std_pct": round(pstdev(capacity_growth), 3) if len(capacity_growth) > 1 else 0.0,
        "average_capacity_utilization_pct": round(mean(utilization), 2) if utilization else 0.0,
        "minimum_fulfillment_pct": round(min(fulfillment), 2) if fulfillment else 0.0,
        "maximum_unmet_demand_index": round(max(unmet), 3) if unmet else 0.0,
        "source_regional_seed_momentum_label": final.get("source_regional_seed_momentum_label", "none"),
        "source_regional_seed_investment_cycle_bias_pct": as_float(final, "source_regional_seed_investment_cycle_bias_pct"),
        "source_regional_seed_openness_bias_pct": as_float(final, "source_regional_seed_openness_bias_pct"),
        "final_capacity_index": as_float(final, "regional_air_capacity_index"),
        "final_served_passenger_demand_index": as_float(final, "served_passenger_demand_index"),
        "final_served_passengers_million": as_float(final, "served_passengers_million"),
        "final_unmet_passengers_million": as_float(final, "unmet_passengers_million"),
        "final_supply_regime": final.get("supply_regime"),
    }


def parse_args() -> argparse.Namespace:
    airport_dir = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Generate regional air capacity supply fulfillment from aviation demand.")
    parser.add_argument("--region", default="north_america", choices=sorted(AIR_SUPPLY_REGION_CONFIGS))
    parser.add_argument(
        "--aviation-demand-csv",
        type=Path,
        default=None,
        help="Defaults to airport/output/regional_aviation_demand/<region>_aviation_demand_seed_sweep.csv.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=airport_dir / "output" / "regional_air_capacity_supply",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    params = AIR_SUPPLY_REGION_CONFIGS[args.region]
    if args.aviation_demand_csv is None:
        airport_dir = Path(__file__).resolve().parents[1]
        args.aviation_demand_csv = (
            airport_dir
            / "output"
            / "regional_aviation_demand"
            / f"{args.region}_aviation_demand_seed_sweep.csv"
        )
    demand_rows = read_csv(args.aviation_demand_csv)
    if not demand_rows:
        raise SystemExit(f"No aviation demand rows found for region {args.region}")
    rows = simulate_region_air_supply(demand_rows, params)

    output_dir = args.output_dir
    csv_path = output_dir / f"{args.region}_air_capacity_supply_seed_sweep.csv"
    json_path = output_dir / f"{args.region}_air_capacity_supply_summary.json"
    js_path = output_dir / f"{args.region}_air_capacity_supply_viewer_data.js"
    write_csv(csv_path, rows, AIR_SUPPLY_FIELDS)
    write_json(
        json_path,
        {
            "regional_air_supply_param_version": AIR_SUPPLY_PARAM_VERSION,
            "regional_air_supply_interface_version": AIR_SUPPLY_INTERFACE_VERSION,
            "region": args.region,
            "params": asdict(params),
            "summaries": [summarize_region_seed(rows)],
        },
    )
    write_viewer_data_js(js_path, rows)
    print(json.dumps({"csv": str(csv_path), "summary": str(json_path), "viewer": str(js_path)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
