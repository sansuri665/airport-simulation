from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean
from typing import Any, Iterable


CITY_AIRPORT_DEMAND_PARAM_VERSION = "city-airport-market-demand-layer-v0.18"
CITY_AIRPORT_DEMAND_INTERFACE_VERSION = "city-airport-market-demand-interface-v0.18"


AIRPORT_DIR = Path(__file__).resolve().parents[1]
CITY_AIRPORT_CONFIG_DIR = AIRPORT_DIR / "config" / "city_airport_markets"
FACILITY_SIZE_CATALOG_DIR = AIRPORT_DIR / "config" / "facility_size_catalogs"
DEFAULT_FACILITY_SIZE_CATALOG_ID = "standard_terminal_sizes_v1"
COMPONENTS = ("business", "leisure", "vfr", "long_haul", "transfer")


CITY_AIRPORT_DEMAND_FIELDS = [
    "city_airport_demand_param_version",
    "city_airport_demand_interface_version",
    "city_airport_market_id",
    "city_name",
    "region_id",
    "region_name",
    "year_index",
    "year",
    "seed",
    "market_tier",
    "market_type",
    "airport_system",
    "airport_facility_slot_profile_id",
    "facility_size_catalog_id",
    "active_airport_facility_slots",
    "source_regional_air_demand_index",
    "source_regional_air_demand_growth_pct",
    "source_region_potential_passengers_million",
    "source_region_served_passengers_million",
    "source_regional_seed_momentum_label",
    "source_regional_seed_effective_growth_bias_pct",
    "source_regional_seed_aviation_propensity_bias_pct",
    "source_regional_seed_investment_cycle_bias_pct",
    "source_regional_seed_openness_bias_pct",
    "source_regional_seed_demand_multiplier",
    "baseline_region_demand_share_pct",
    "city_share_adjustment_pp",
    "city_demand_share_pct",
    "city_air_demand_growth_pct",
    "seed_city_potential_enabled",
    "seed_city_potential_template_id",
    "seed_city_structural_momentum_score",
    "seed_city_regional_alignment_score",
    "seed_city_momentum_label",
    "seed_city_annual_growth_bias_pct",
    "seed_city_max_growth_bias_pct",
    "seed_city_effect_release_pct",
    "seed_city_effective_bias_pct",
    "seed_city_potential_multiplier",
    "city_potential_passengers_million",
    "city_airport_design_capacity_million",
    "city_airport_max_capacity_million",
    "city_effective_capacity_million",
    "city_airline_supply_potential_anchor_index",
    "city_airline_supply_trend_index",
    "city_airline_supply_demand_pull_pct",
    "city_airline_supply_macro_adjustment_pct",
    "city_airline_supply_constraint_drag_pct",
    "city_airline_supply_cycle_impulse_pct",
    "city_airline_supply_shock_impulse_pct",
    "city_airline_supply_event_impulse_pct",
    "city_airline_supply_target_index",
    "city_airline_supply_lag_adjustment_pct",
    "city_airline_supply_ceiling_index",
    "city_airline_supply_index",
    "city_airline_supply_volatility_regime",
    "city_airline_supply_passengers_million",
    "airport_capacity_allocation_ratio_pct",
    "airport_capacity_limited_airline_supply_million",
    "city_effective_service_capacity_million",
    "city_capacity_utilization_pct",
    "city_airport_design_utilization_pct",
    "city_airport_max_utilization_pct",
    "city_capacity_fulfillment_pct",
    "city_airport_throughput_utilization_pct",
    "city_airport_crowding_index",
    "city_airline_supply_utilization_pct",
    "city_airline_supply_fulfillment_pct",
    "city_total_fulfillment_pct",
    "final_passenger_service_ratio_pct",
    "city_served_passengers_million",
    "city_unmet_passengers_million",
    "city_unmet_demand_share_pct",
    "city_airline_supply_gap_million",
    "city_airport_capacity_gap_million",
    "city_binding_bottleneck",
    "business_city_demand_index",
    "leisure_city_demand_index",
    "vfr_city_demand_index",
    "long_haul_city_demand_index",
    "transfer_city_demand_index",
    "business_passenger_share_pct",
    "leisure_passenger_share_pct",
    "vfr_passenger_share_pct",
    "long_haul_passenger_share_pct",
    "transfer_passenger_share_pct",
    "business_passengers_million",
    "leisure_passengers_million",
    "vfr_passengers_million",
    "long_haul_passengers_million",
    "transfer_passengers_million",
    "business_airline_supply_share_pct",
    "leisure_airline_supply_share_pct",
    "vfr_airline_supply_share_pct",
    "long_haul_airline_supply_share_pct",
    "transfer_airline_supply_share_pct",
    "business_airline_supply_passengers_million",
    "leisure_airline_supply_passengers_million",
    "vfr_airline_supply_passengers_million",
    "long_haul_airline_supply_passengers_million",
    "transfer_airline_supply_passengers_million",
    "business_airline_supply_fulfillment_pct",
    "leisure_airline_supply_fulfillment_pct",
    "vfr_airline_supply_fulfillment_pct",
    "long_haul_airline_supply_fulfillment_pct",
    "transfer_airline_supply_fulfillment_pct",
    "business_airline_supply_gap_million",
    "leisure_airline_supply_gap_million",
    "vfr_airline_supply_gap_million",
    "long_haul_airline_supply_gap_million",
    "transfer_airline_supply_gap_million",
    "business_served_passengers_million",
    "leisure_served_passengers_million",
    "vfr_served_passengers_million",
    "long_haul_served_passengers_million",
    "transfer_served_passengers_million",
    "premium_passenger_propensity_index",
    "premium_passenger_share_pct",
    "duty_free_propensity_index",
    "luxury_retail_propensity_index",
    "electronics_retail_propensity_index",
    "food_beverage_propensity_index",
    "general_retail_propensity_index",
    "city_demand_regime",
    "city_capacity_regime",
    "city_airline_supply_regime",
    "source_aviation_demand_regime",
    "source_supply_regime",
    "airport_event_hint",
    "branch_scenario_id",
    "branch_scenario_state",
    "branch_effect_phase",
    "input_macro_stress_index",
    "input_consumer_confidence_index",
    "input_airfare_pressure_index",
    "input_currency_pressure_index",
    "input_regional_gdp_index",
    "input_regional_gdp_growth_pct",
    "input_regional_output_gap_pct",
    "input_headline_inflation_pct",
    "input_core_inflation_pct",
    "input_headline_inflation_cost_index",
    "input_core_inflation_cost_index",
    "input_energy_cost_pressure_index",
    "input_10y_yield_pct",
    "input_hy_spread_bps",
    "input_equity_return_pct",
    "input_equity_valuation_pe",
    "input_regional_macro_stress_index",
]


@dataclass(frozen=True)
class FacilitySizeSpec:
    code: str
    design_capacity_million: float
    max_capacity_million: float


@dataclass(frozen=True)
class FacilitySizeCatalog:
    catalog_id: str
    facility_sizes: dict[str, FacilitySizeSpec]
    slot_role_allowed_sizes: dict[str, frozenset[str]]
    slot_count_role_templates: dict[int, tuple[str, ...]]
    description: str = ""


@dataclass(frozen=True)
class AirportFacilitySlot:
    airport_id: str
    airport_name: str
    slot_id: str
    slot_name: str
    slot_role: str
    facility_size: str
    open_year: int = 2025


FALLBACK_FACILITY_SIZE_CATALOG = FacilitySizeCatalog(
    catalog_id=DEFAULT_FACILITY_SIZE_CATALOG_ID,
    description="Built-in fallback used only when the JSON catalog is unavailable.",
    facility_sizes={
        "empty": FacilitySizeSpec("empty", 0.0, 0.0),
        "small": FacilitySizeSpec("small", 8.0, 12.0),
        "medium": FacilitySizeSpec("medium", 16.0, 24.0),
        "large": FacilitySizeSpec("large", 32.0, 45.0),
        "extra_large": FacilitySizeSpec("extra_large", 50.0, 65.0),
        "giant": FacilitySizeSpec("giant", 72.0, 90.0),
    },
    slot_role_allowed_sizes={
        "main_slot": frozenset({"empty", "small", "medium", "large", "extra_large", "giant"}),
        "secondary_slot": frozenset({"empty", "small", "medium", "large", "extra_large"}),
        "auxiliary_slot": frozenset({"empty", "small", "medium", "large"}),
    },
    slot_count_role_templates={
        3: ("auxiliary_slot", "auxiliary_slot", "auxiliary_slot"),
        4: ("secondary_slot", "auxiliary_slot", "auxiliary_slot", "auxiliary_slot"),
        5: ("main_slot", "secondary_slot", "auxiliary_slot", "auxiliary_slot", "auxiliary_slot"),
    },
)


def facility_size_catalog_from_config(raw: dict[str, Any]) -> FacilitySizeCatalog:
    catalog_id = str(raw["catalog_id"])
    facility_sizes = {
        str(code): FacilitySizeSpec(
            code=str(code),
            design_capacity_million=float(spec["design_capacity_million"]),
            max_capacity_million=float(spec["max_capacity_million"]),
        )
        for code, spec in raw.get("facility_sizes", {}).items()
    }
    slot_role_allowed_sizes = {
        str(role): frozenset(str(size) for size in sizes)
        for role, sizes in raw.get("slot_role_allowed_sizes", {}).items()
    }
    slot_count_role_templates = {
        int(slot_count): tuple(str(role) for role in roles)
        for slot_count, roles in raw.get("slot_count_role_templates", {}).items()
    }
    if "empty" not in facility_sizes:
        raise ValueError(f"Facility catalog {catalog_id!r} must define an empty facility size")
    return FacilitySizeCatalog(
        catalog_id=catalog_id,
        description=str(raw.get("description") or ""),
        facility_sizes=facility_sizes,
        slot_role_allowed_sizes=slot_role_allowed_sizes,
        slot_count_role_templates=slot_count_role_templates,
    )


def load_facility_size_catalogs(
    config_dir: Path = FACILITY_SIZE_CATALOG_DIR,
) -> dict[str, FacilitySizeCatalog]:
    if not config_dir.exists():
        return {}

    catalogs: dict[str, FacilitySizeCatalog] = {}
    for path in sorted(config_dir.rglob("*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        if raw.get("schema_version") != "facility-size-catalog-v1":
            continue
        catalog = facility_size_catalog_from_config(raw)
        catalogs[catalog.catalog_id] = catalog
    return catalogs


FACILITY_SIZE_CATALOGS = {
    FALLBACK_FACILITY_SIZE_CATALOG.catalog_id: FALLBACK_FACILITY_SIZE_CATALOG,
}
FACILITY_SIZE_CATALOGS.update(load_facility_size_catalogs())

# Compatibility aliases for older imports; runtime logic resolves catalogs per city config.
FACILITY_SIZE_SPECS = FACILITY_SIZE_CATALOGS[DEFAULT_FACILITY_SIZE_CATALOG_ID].facility_sizes
SLOT_ROLE_ALLOWED_SIZES = FACILITY_SIZE_CATALOGS[DEFAULT_FACILITY_SIZE_CATALOG_ID].slot_role_allowed_sizes


@dataclass(frozen=True)
class CityAirportMarketDemandParams:
    city_airport_market_id: str
    city_name: str
    region_id: str
    region_name: str
    market_tier: str
    market_type: str
    airport_system: str
    airport_facility_slot_profile_id: str
    facility_size_catalog_id: str
    airport_facility_slots: tuple[AirportFacilitySlot, ...]
    baseline_region_demand_share_pct: float
    baseline_city_potential_passengers_million: float
    annual_long_term_city_growth_bias_pct: float
    max_long_term_city_growth_bias_pct: float
    base_airline_supply_passengers_million: float
    regional_airline_capacity_growth_capture: float
    annual_local_airline_supply_growth_pct: float
    max_local_airline_supply_growth_pct: float
    airline_supply_confidence_bias: float
    airline_supply_appetite_bias: float
    airline_supply_constraint_bias: float
    business_base_share_pct: float
    leisure_base_share_pct: float
    vfr_base_share_pct: float
    long_haul_base_share_pct: float
    transfer_base_share_pct: float
    business_share_bias: float
    leisure_share_bias: float
    vfr_share_bias: float
    long_haul_share_bias: float
    transfer_share_bias: float
    premium_propensity_bias: float
    premium_share_bias: float
    duty_free_bias: float
    luxury_retail_bias: float
    electronics_retail_bias: float
    food_beverage_bias: float
    general_retail_bias: float
    seed_potential_enabled: bool = False
    seed_potential_template_id: str = "none"
    seed_potential_release_start_year_index: float = 5.0
    seed_potential_full_effect_year_index: float = 25.0
    seed_potential_annual_growth_bias_min_pct: float = 0.0
    seed_potential_annual_growth_bias_max_pct: float = 0.0
    seed_potential_max_growth_bias_min_pct: float = 0.0
    seed_potential_max_growth_bias_max_pct: float = 0.0
    seed_potential_regional_correlation_weight: float = 0.25
    seed_potential_multiplier_floor: float = 0.85
    seed_potential_multiplier_ceiling: float = 1.15
    airline_supply_demand_pull_capture: float = 0.92
    airline_supply_cycle_amplitude_pct: float = 11.5
    airline_supply_shock_amplitude_pct: float = 9.0
    airline_supply_adjustment_speed: float = 0.64
    airline_supply_volatility_bias: float = 1.0


def slots_from_city_config(raw: dict[str, Any]) -> tuple[AirportFacilitySlot, ...]:
    slots: list[AirportFacilitySlot] = []
    for airport in raw.get("airports", []):
        airport_id = str(airport["airport_id"])
        airport_name = str(airport["airport_name"])
        for slot in airport.get("slots", []):
            slots.append(
                AirportFacilitySlot(
                    airport_id=airport_id,
                    airport_name=airport_name,
                    slot_id=str(slot["slot_id"]),
                    slot_name=str(slot["slot_name"]),
                    slot_role=str(slot["slot_role"]),
                    facility_size=str(slot["facility_size"]),
                    open_year=int(slot.get("open_year", 2025)),
                )
            )
    return tuple(slots)


def config_range_pair(value: Any, default_low: float = 0.0, default_high: float = 0.0) -> tuple[float, float]:
    if isinstance(value, (list, tuple)) and len(value) >= 2:
        low = float(value[0])
        high = float(value[1])
        return (min(low, high), max(low, high))
    if isinstance(value, dict):
        low = float(value.get("min", default_low))
        high = float(value.get("max", default_high))
        return (min(low, high), max(low, high))
    return (default_low, default_high)


def city_market_params_from_config(raw: dict[str, Any]) -> CityAirportMarketDemandParams:
    market = raw["market"]
    facility_model = raw["facility_model"]
    demand_model = raw["demand_model"]
    airline_supply_model = raw["airline_supply_model"]
    component_mix = raw["component_mix"]
    component_biases = raw.get("component_biases", {})
    commercial_biases = raw.get("commercial_biases", {})
    seed_potential_model = demand_model.get("seed_potential_model", {})
    seed_annual_range = config_range_pair(seed_potential_model.get("annual_growth_bias_range_pct"))
    seed_max_range = config_range_pair(seed_potential_model.get("max_growth_bias_range_pct"))

    return CityAirportMarketDemandParams(
        city_airport_market_id=str(market["city_airport_market_id"]),
        city_name=str(market["city_name"]),
        region_id=str(market["region_id"]),
        region_name=str(market["region_name"]),
        market_tier=str(market["market_tier"]),
        market_type=str(market["market_type"]),
        airport_system=str(market["airport_system"]),
        airport_facility_slot_profile_id=str(facility_model["airport_facility_slot_profile_id"]),
        facility_size_catalog_id=str(facility_model.get("facility_size_catalog", DEFAULT_FACILITY_SIZE_CATALOG_ID)),
        airport_facility_slots=slots_from_city_config(raw),
        baseline_region_demand_share_pct=float(demand_model["baseline_region_demand_share_pct"]),
        baseline_city_potential_passengers_million=float(demand_model["baseline_city_potential_passengers_million"]),
        annual_long_term_city_growth_bias_pct=float(demand_model["annual_long_term_city_growth_bias_pct"]),
        max_long_term_city_growth_bias_pct=float(demand_model["max_long_term_city_growth_bias_pct"]),
        base_airline_supply_passengers_million=float(airline_supply_model["base_airline_supply_passengers_million"]),
        regional_airline_capacity_growth_capture=float(airline_supply_model["regional_airline_capacity_growth_capture"]),
        annual_local_airline_supply_growth_pct=float(airline_supply_model["annual_local_airline_supply_growth_pct"]),
        max_local_airline_supply_growth_pct=float(airline_supply_model["max_local_airline_supply_growth_pct"]),
        airline_supply_confidence_bias=float(airline_supply_model.get("airline_supply_confidence_bias", 1.0)),
        airline_supply_appetite_bias=float(airline_supply_model.get("airline_supply_appetite_bias", 1.0)),
        airline_supply_constraint_bias=float(airline_supply_model.get("airline_supply_constraint_bias", 1.0)),
        business_base_share_pct=float(component_mix["business_base_share_pct"]),
        leisure_base_share_pct=float(component_mix["leisure_base_share_pct"]),
        vfr_base_share_pct=float(component_mix["vfr_base_share_pct"]),
        long_haul_base_share_pct=float(component_mix["long_haul_base_share_pct"]),
        transfer_base_share_pct=float(component_mix["transfer_base_share_pct"]),
        business_share_bias=float(component_biases.get("business_share_bias", 1.0)),
        leisure_share_bias=float(component_biases.get("leisure_share_bias", 1.0)),
        vfr_share_bias=float(component_biases.get("vfr_share_bias", 1.0)),
        long_haul_share_bias=float(component_biases.get("long_haul_share_bias", 1.0)),
        transfer_share_bias=float(component_biases.get("transfer_share_bias", 1.0)),
        premium_propensity_bias=float(commercial_biases.get("premium_propensity_bias", 1.0)),
        premium_share_bias=float(commercial_biases.get("premium_share_bias", 1.0)),
        duty_free_bias=float(commercial_biases.get("duty_free_bias", 1.0)),
        luxury_retail_bias=float(commercial_biases.get("luxury_retail_bias", 1.0)),
        electronics_retail_bias=float(commercial_biases.get("electronics_retail_bias", 1.0)),
        food_beverage_bias=float(commercial_biases.get("food_beverage_bias", 1.0)),
        general_retail_bias=float(commercial_biases.get("general_retail_bias", 1.0)),
        seed_potential_enabled=bool(seed_potential_model.get("enabled", False)),
        seed_potential_template_id=str(seed_potential_model.get("template_id", "none")),
        seed_potential_release_start_year_index=float(seed_potential_model.get("release_start_year_index", 5.0)),
        seed_potential_full_effect_year_index=float(seed_potential_model.get("full_effect_year_index", 25.0)),
        seed_potential_annual_growth_bias_min_pct=seed_annual_range[0],
        seed_potential_annual_growth_bias_max_pct=seed_annual_range[1],
        seed_potential_max_growth_bias_min_pct=seed_max_range[0],
        seed_potential_max_growth_bias_max_pct=seed_max_range[1],
        seed_potential_regional_correlation_weight=float(
            seed_potential_model.get("regional_correlation_weight", 0.25)
        ),
        seed_potential_multiplier_floor=float(seed_potential_model.get("potential_multiplier_floor", 0.85)),
        seed_potential_multiplier_ceiling=float(seed_potential_model.get("potential_multiplier_ceiling", 1.15)),
        airline_supply_demand_pull_capture=float(airline_supply_model.get("demand_pull_capture", 0.92)),
        airline_supply_cycle_amplitude_pct=float(airline_supply_model.get("cycle_amplitude_pct", 11.5)),
        airline_supply_shock_amplitude_pct=float(airline_supply_model.get("shock_amplitude_pct", 9.0)),
        airline_supply_adjustment_speed=float(airline_supply_model.get("adjustment_speed", 0.64)),
        airline_supply_volatility_bias=float(airline_supply_model.get("volatility_bias", 1.0)),
    )


def load_city_market_configs(config_dir: Path = CITY_AIRPORT_CONFIG_DIR) -> dict[str, CityAirportMarketDemandParams]:
    if not config_dir.exists():
        return {}

    configs: dict[str, CityAirportMarketDemandParams] = {}
    for path in sorted(config_dir.rglob("*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        if raw.get("schema_version") != "city-airport-market-config-v1":
            continue
        params = city_market_params_from_config(raw)
        configs[params.city_airport_market_id] = params
    return configs


CITY_MARKET_CONFIGS = {
    "beijing_airport_system": CityAirportMarketDemandParams(
        city_airport_market_id="beijing_airport_system",
        city_name="北京",
        region_id="china_mainland",
        region_name="中国大陆",
        market_tier="global_hub",
        market_type="dual_airport_capital_gateway",
        airport_system="首都 + 大兴",
        airport_facility_slot_profile_id="beijing_dual_airport_5_slot_v1",
        facility_size_catalog_id=DEFAULT_FACILITY_SIZE_CATALOG_ID,
        airport_facility_slots=(
            AirportFacilitySlot(
                airport_id="PEK",
                airport_name="北京首都",
                slot_id="PEK_SLOT_1",
                slot_name="首都T3航站楼",
                slot_role="main_slot",
                facility_size="extra_large",
            ),
            AirportFacilitySlot(
                airport_id="PEK",
                airport_name="北京首都",
                slot_id="PEK_SLOT_2",
                slot_name="首都T2航站楼",
                slot_role="secondary_slot",
                facility_size="large",
            ),
            AirportFacilitySlot(
                airport_id="PEK",
                airport_name="北京首都",
                slot_id="PEK_SLOT_3",
                slot_name="首都玩家扩建槽位 1",
                slot_role="auxiliary_slot",
                facility_size="empty",
            ),
            AirportFacilitySlot(
                airport_id="PEK",
                airport_name="北京首都",
                slot_id="PEK_SLOT_4",
                slot_name="首都玩家扩建槽位 2",
                slot_role="auxiliary_slot",
                facility_size="empty",
            ),
            AirportFacilitySlot(
                airport_id="PEK",
                airport_name="北京首都",
                slot_id="PEK_SLOT_5",
                slot_name="首都玩家扩建槽位 3",
                slot_role="auxiliary_slot",
                facility_size="empty",
            ),
            AirportFacilitySlot(
                airport_id="PKX",
                airport_name="北京大兴",
                slot_id="PKX_SLOT_1",
                slot_name="大兴T1航站楼",
                slot_role="main_slot",
                facility_size="giant",
            ),
            AirportFacilitySlot(
                airport_id="PKX",
                airport_name="北京大兴",
                slot_id="PKX_SLOT_2",
                slot_name="大兴T2航站楼",
                slot_role="secondary_slot",
                facility_size="empty",
            ),
            AirportFacilitySlot(
                airport_id="PKX",
                airport_name="北京大兴",
                slot_id="PKX_SLOT_3",
                slot_name="大兴玩家扩建槽位 1",
                slot_role="auxiliary_slot",
                facility_size="empty",
            ),
            AirportFacilitySlot(
                airport_id="PKX",
                airport_name="北京大兴",
                slot_id="PKX_SLOT_4",
                slot_name="大兴玩家扩建槽位 2",
                slot_role="auxiliary_slot",
                facility_size="empty",
            ),
            AirportFacilitySlot(
                airport_id="PKX",
                airport_name="北京大兴",
                slot_id="PKX_SLOT_5",
                slot_name="大兴玩家扩建槽位 3",
                slot_role="auxiliary_slot",
                facility_size="empty",
            ),
        ),
        baseline_region_demand_share_pct=14.5,
        baseline_city_potential_passengers_million=118.9,
        annual_long_term_city_growth_bias_pct=0.70,
        max_long_term_city_growth_bias_pct=42.0,
        base_airline_supply_passengers_million=122.0,
        regional_airline_capacity_growth_capture=0.40,
        annual_local_airline_supply_growth_pct=0.28,
        max_local_airline_supply_growth_pct=22.0,
        airline_supply_confidence_bias=1.0,
        airline_supply_appetite_bias=1.0,
        airline_supply_constraint_bias=1.0,
        business_base_share_pct=32.0,
        leisure_base_share_pct=38.0,
        vfr_base_share_pct=13.0,
        long_haul_base_share_pct=10.0,
        transfer_base_share_pct=7.0,
        business_share_bias=1.0,
        leisure_share_bias=1.0,
        vfr_share_bias=1.0,
        long_haul_share_bias=1.0,
        transfer_share_bias=1.0,
        premium_propensity_bias=1.18,
        premium_share_bias=1.24,
        duty_free_bias=1.10,
        luxury_retail_bias=1.20,
        electronics_retail_bias=1.08,
        food_beverage_bias=0.98,
        general_retail_bias=0.96,
    )
}


CITY_MARKET_CONFIGS.update(load_city_market_configs())


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def as_float(row: dict[str, Any], key: str, default: float = 0.0) -> float:
    value = row.get(key)
    if value in (None, ""):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def first_float(row: dict[str, Any], keys: Iterable[str], default: float = 0.0) -> float:
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            return as_float(row, key, default)
    return default


def inflation_cost_pressure_index(inflation_pct: float) -> float:
    return clamp(50.0 + (inflation_pct - 2.0) * 7.5, 25.0, 85.0)


def pct_change(current: float, previous: float) -> float:
    if previous == 0:
        return 0.0
    return (current / previous - 1.0) * 100.0


def round_record(record: dict[str, Any]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key, value in record.items():
        if isinstance(value, float):
            output[key] = round(value, 4)
        else:
            output[key] = value
    return output


def stable_unit_float(*parts: Any) -> float:
    raw = "::".join(str(part) for part in parts).encode("utf-8")
    digest = hashlib.sha256(raw).digest()
    return int.from_bytes(digest[:8], "big") / float(1 << 64)


def interpolate(low: float, high: float, unit: float) -> float:
    return low + (high - low) * clamp(unit, 0.0, 1.0)


def seed_momentum_label(score: float) -> str:
    if score >= 0.66:
        return "strong_upside"
    if score >= 0.25:
        return "upside"
    if score <= -0.66:
        return "strong_downside"
    if score <= -0.25:
        return "downside"
    return "balanced"


def regional_alignment_score(row: dict[str, Any]) -> float:
    regional_demand_gap = (as_float(row, "regional_air_demand_index", 100.0) - 100.0) / 85.0
    regional_gdp_gap = (first_float(row, ("macro_regional_gdp_index",), 100.0) - 100.0) / 160.0
    confidence_gap = (as_float(row, "input_consumer_confidence_index", 50.0) - 50.0) / 70.0
    stress_gap = max(0.0, as_float(row, "input_macro_stress_index", 25.0) - 28.0) / 70.0
    fare_gap = max(0.0, as_float(row, "airfare_pressure_index", 50.0) - 52.0) / 90.0
    raw = (
        0.38 * regional_demand_gap
        + 0.22 * regional_gdp_gap
        + 0.18 * confidence_gap
        - 0.14 * stress_gap
        - 0.08 * fare_gap
    )
    return clamp(raw, -1.0, 1.0)


def city_seed_potential_profile(row: dict[str, Any], params: CityAirportMarketDemandParams) -> dict[str, Any]:
    if not params.seed_potential_enabled:
        return {
            "enabled": 0,
            "template_id": params.seed_potential_template_id,
            "structural_momentum_score": 0.0,
            "regional_alignment_score": 0.0,
            "momentum_label": "disabled",
            "annual_growth_bias_pct": 0.0,
            "max_growth_bias_pct": 0.0,
            "effect_release_pct": 0.0,
            "effective_bias_pct": 0.0,
            "potential_multiplier": 1.0,
        }

    seed = int(as_float(row, "seed"))
    year_index = as_float(row, "year_index")
    unit = stable_unit_float(
        "city_seed_potential",
        params.seed_potential_template_id,
        params.city_airport_market_id,
        seed,
    )
    structural_score = unit * 2.0 - 1.0
    annual_bias = interpolate(
        params.seed_potential_annual_growth_bias_min_pct,
        params.seed_potential_annual_growth_bias_max_pct,
        unit,
    )
    max_bias = interpolate(
        params.seed_potential_max_growth_bias_min_pct,
        params.seed_potential_max_growth_bias_max_pct,
        unit,
    )
    start = params.seed_potential_release_start_year_index
    full = max(start + 1.0, params.seed_potential_full_effect_year_index)
    release = clamp((year_index - start) / (full - start), 0.0, 1.0)
    raw_effective_bias = 0.0
    active_years = max(0.0, year_index - start)
    if abs(annual_bias) > 1e-9 and abs(max_bias) > 1e-9:
        raw_effective_bias = (1.0 if max_bias >= 0.0 else -1.0) * min(
            abs(max_bias),
            active_years * abs(annual_bias),
        )

    alignment_score = regional_alignment_score(row)
    correlation_weight = clamp(params.seed_potential_regional_correlation_weight, 0.0, 0.75)
    sign = 1.0 if raw_effective_bias >= 0.0 else -1.0
    alignment_multiplier = clamp(1.0 + sign * correlation_weight * alignment_score, 0.65, 1.35)
    effective_bias = clamp(
        raw_effective_bias * release * alignment_multiplier,
        (params.seed_potential_multiplier_floor - 1.0) * 100.0,
        (params.seed_potential_multiplier_ceiling - 1.0) * 100.0,
    )
    multiplier = 1.0 + effective_bias / 100.0

    return {
        "enabled": 1,
        "template_id": params.seed_potential_template_id,
        "structural_momentum_score": structural_score,
        "regional_alignment_score": alignment_score,
        "momentum_label": seed_momentum_label(structural_score),
        "annual_growth_bias_pct": annual_bias,
        "max_growth_bias_pct": max_bias,
        "effect_release_pct": release * 100.0,
        "effective_bias_pct": effective_bias,
        "potential_multiplier": multiplier,
    }


def read_csv(path: Path) -> list[dict[str, Any]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_viewer_data_js(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(rows, ensure_ascii=False, separators=(",", ":"))
    path.write_text(f"window.CITY_AIRPORT_MARKET_DEMAND_DATA = {payload};\n", encoding="utf-8")


def key_for(row: dict[str, Any]) -> tuple[int, int]:
    return int(as_float(row, "seed")), int(as_float(row, "year_index"))


def merge_region_inputs(
    region_id: str,
    demand_rows: Iterable[dict[str, Any]],
    supply_rows: Iterable[dict[str, Any]],
    regional_macro_rows: Iterable[dict[str, Any]] = (),
) -> list[dict[str, Any]]:
    filtered_demand = [row for row in demand_rows if row.get("region_id") == region_id]
    filtered_supply = [row for row in supply_rows if row.get("region_id") == region_id]
    filtered_macro = [row for row in regional_macro_rows if row.get("region_id") == region_id]
    supply_by_key = {key_for(row): row for row in filtered_supply}
    macro_by_key = {key_for(row): row for row in filtered_macro}
    merged = []
    for demand in sorted(filtered_demand, key=lambda item: key_for(item)):
        supply = supply_by_key.get(key_for(demand), {})
        macro = macro_by_key.get(key_for(demand), {})
        item = dict(demand)
        for key, value in supply.items():
            item[f"supply_{key}"] = value
        for key, value in macro.items():
            item[f"macro_{key}"] = value
        merged.append(item)
    return merged


def component_event_impulse(row: dict[str, Any], component: str) -> float:
    hint = str(row.get("airport_event_hint") or "none")
    branch_state = str(row.get("branch_scenario_state") or "baseline")
    branch_phase = str(row.get("branch_effect_phase") or "none")
    impulse = 0.0

    if hint == "business_travel_credit_drag" and component == "business":
        impulse -= 12.0
    if hint == "outbound_fx_squeeze" and component in {"leisure", "vfr", "long_haul"}:
        impulse -= 10.0 if component == "leisure" else 7.0
    if hint == "fare_shock_leisure_drag" and component in {"leisure", "vfr"}:
        impulse -= 9.0
    if hint == "broad_travel_recovery" and component in {"leisure", "vfr"}:
        impulse += 6.0
    if hint == "premium_mix_volatility" and component in {"business", "long_haul"}:
        impulse -= 3.0

    if branch_state in {"occurred", "counterfactual"} and branch_phase == "impact":
        impulse -= 5.0
    elif branch_state in {"occurred", "counterfactual"} and branch_phase == "tail":
        impulse -= 2.0

    return impulse


def city_component_indices(row: dict[str, Any], params: CityAirportMarketDemandParams) -> dict[str, float]:
    regional_gap = as_float(row, "regional_air_demand_index", 100.0) - 100.0
    business_gap = as_float(row, "business_travel_demand_index", 100.0) - 100.0
    leisure_gap = as_float(row, "leisure_travel_demand_index", 100.0) - 100.0
    vfr_gap = as_float(row, "vfr_travel_demand_index", 100.0) - 100.0
    long_haul_gap = as_float(row, "long_haul_demand_index", 100.0) - 100.0
    transfer_gap = as_float(row, "transfer_demand_index", 100.0) - 100.0
    premium_gap = as_float(row, "premium_passenger_propensity_index", 100.0) - 100.0
    capacity_gap = as_float(row, "supply_regional_air_capacity_index", 100.0) - 100.0
    confidence_gap = as_float(row, "input_consumer_confidence_index", 50.0) - 50.0
    stress_gap = max(0.0, as_float(row, "input_macro_stress_index", 25.0) - 32.0)
    fare_gap = max(0.0, as_float(row, "airfare_pressure_index", 50.0) - 52.0)
    currency_gap = max(0.0, as_float(row, "input_currency_pressure_index", 35.0) - 34.0)
    slot_gap = max(0.0, as_float(row, "supply_airport_slot_constraint_index", 26.0) - 30.0)

    raw = {
        "business": (
            100.0
            + params.business_share_bias * (0.52 * business_gap + 0.08 * regional_gap)
            + 0.12 * premium_gap
            + 0.10 * confidence_gap
            - 0.34 * stress_gap
            + component_event_impulse(row, "business")
        ),
        "leisure": (
            100.0
            + params.leisure_share_bias * (0.62 * leisure_gap + 0.10 * regional_gap)
            + 0.18 * confidence_gap
            - 0.22 * fare_gap
            - 0.16 * currency_gap
            + component_event_impulse(row, "leisure")
        ),
        "vfr": (
            100.0
            + params.vfr_share_bias * 0.58 * vfr_gap
            + 0.08 * regional_gap
            - 0.12 * fare_gap
            - 0.10 * currency_gap
            + component_event_impulse(row, "vfr")
        ),
        "long_haul": (
            100.0
            + params.long_haul_share_bias * 0.64 * long_haul_gap
            + 0.10 * business_gap
            + 0.08 * premium_gap
            - 0.22 * currency_gap
            - 0.16 * fare_gap
            + component_event_impulse(row, "long_haul")
        ),
        "transfer": (
            100.0
            + params.transfer_share_bias * 0.58 * transfer_gap
            + 0.08 * capacity_gap
            + 0.08 * long_haul_gap
            - 0.35 * slot_gap
            + component_event_impulse(row, "transfer")
        ),
    }

    return {
        "business": clamp(raw["business"], 65.0, 245.0),
        "leisure": clamp(raw["leisure"], 55.0, 230.0),
        "vfr": clamp(raw["vfr"], 65.0, 225.0),
        "long_haul": clamp(raw["long_haul"], 55.0, 210.0),
        "transfer": clamp(raw["transfer"], 45.0, 185.0),
    }


def city_component_passengers(
    row: dict[str, Any], params: CityAirportMarketDemandParams
) -> tuple[dict[str, float], dict[str, float], dict[str, float], dict[str, Any]]:
    indices = city_component_indices(row, params)
    year_index = as_float(row, "year_index")
    long_term_growth_bias = min(
        params.max_long_term_city_growth_bias_pct,
        year_index * params.annual_long_term_city_growth_bias_pct,
    )
    seed_profile = city_seed_potential_profile(row, params)
    long_term_growth_multiplier = 1.0 + long_term_growth_bias / 100.0
    seed_potential_multiplier = float(seed_profile["potential_multiplier"])
    base_shares = {
        "business": params.business_base_share_pct,
        "leisure": params.leisure_base_share_pct,
        "vfr": params.vfr_base_share_pct,
        "long_haul": params.long_haul_base_share_pct,
        "transfer": params.transfer_base_share_pct,
    }
    passengers = {
        key: (
            params.baseline_city_potential_passengers_million
            * long_term_growth_multiplier
            * seed_potential_multiplier
            * base_shares[key]
            / 100.0
            * indices[key]
            / 100.0
        )
        for key in indices
    }
    total = sum(passengers.values()) or 1.0
    shares = {key: value / total * 100.0 for key, value in passengers.items()}
    return indices, passengers, shares, seed_profile


def component_airline_supply_passengers(
    row: dict[str, Any],
    component_passengers: dict[str, float],
    airline_supply: float,
) -> tuple[dict[str, float], dict[str, float], dict[str, float], dict[str, float]]:
    route_gap = as_float(row, "supply_route_growth_appetite_index", 45.0) - 45.0
    fleet_gap = as_float(row, "supply_fleet_expansion_appetite_index", 45.0) - 45.0
    confidence_gap = as_float(row, "supply_airline_capacity_confidence_index", 50.0) - 50.0
    profit_pressure = max(0.0, as_float(row, "supply_airline_profit_pressure_index", 45.0) - 45.0)
    slot_pressure = max(0.0, as_float(row, "supply_airport_slot_constraint_index", 30.0) - 30.0)
    fare_pressure = max(0.0, as_float(row, "airfare_pressure_index", 50.0) - 52.0)
    currency_pressure = max(0.0, as_float(row, "input_currency_pressure_index", 35.0) - 34.0)
    macro_stress = max(0.0, as_float(row, "input_macro_stress_index", 25.0) - 32.0)
    openness_bias = first_float(
        row,
        (
            "source_regional_seed_openness_bias_pct",
            "supply_source_regional_seed_openness_bias_pct",
            "macro_regional_seed_openness_bias_pct",
        ),
        0.0,
    )
    investment_bias = first_float(
        row,
        (
            "source_regional_seed_investment_cycle_bias_pct",
            "supply_source_regional_seed_investment_cycle_bias_pct",
            "macro_regional_seed_investment_cycle_bias_pct",
        ),
        0.0,
    )

    multipliers = {
        "business": 1.0
        + 0.0028 * confidence_gap
        + 0.0016 * route_gap
        - 0.0028 * macro_stress
        - 0.0014 * profit_pressure,
        "leisure": 1.0
        + 0.0022 * route_gap
        + 0.0014 * fleet_gap
        - 0.0026 * fare_pressure
        - 0.0022 * currency_pressure
        - 0.0012 * profit_pressure,
        "vfr": 1.0
        + 0.0008 * route_gap
        - 0.0016 * fare_pressure
        - 0.0015 * currency_pressure
        - 0.0010 * macro_stress,
        "long_haul": 1.0
        + 0.0028 * route_gap
        + 0.0018 * openness_bias
        + 0.0012 * confidence_gap
        - 0.0032 * currency_pressure
        - 0.0020 * macro_stress
        - 0.0014 * profit_pressure,
        "transfer": 1.0
        + 0.0030 * route_gap
        + 0.0025 * fleet_gap
        + 0.0020 * investment_bias
        - 0.0030 * slot_pressure
        - 0.0014 * profit_pressure,
    }
    weighted = {
        component: component_passengers.get(component, 0.0) * clamp(multipliers[component], 0.68, 1.38)
        for component in COMPONENTS
    }
    total_weight = sum(weighted.values())
    if total_weight <= 0.0:
        weighted = {component: 1.0 for component in COMPONENTS}
        total_weight = float(len(COMPONENTS))

    supply = {
        component: airline_supply * weighted[component] / total_weight
        for component in COMPONENTS
    }
    shares = {
        component: supply[component] / airline_supply * 100.0 if airline_supply else 0.0
        for component in COMPONENTS
    }
    fulfillment = {
        component: supply[component] / component_passengers.get(component, 0.0) * 100.0
        if component_passengers.get(component, 0.0)
        else 100.0
        for component in COMPONENTS
    }
    gaps = {
        component: max(0.0, component_passengers.get(component, 0.0) - supply[component])
        for component in COMPONENTS
    }
    return supply, shares, fulfillment, gaps


def active_facility_slots(year: int, params: CityAirportMarketDemandParams) -> list[AirportFacilitySlot]:
    return [
        slot
        for slot in params.airport_facility_slots
        if slot.facility_size != "empty" and slot.open_year <= year
    ]


def facility_catalog_for_params(params: CityAirportMarketDemandParams) -> FacilitySizeCatalog:
    try:
        return FACILITY_SIZE_CATALOGS[params.facility_size_catalog_id]
    except KeyError as exc:
        available = ", ".join(sorted(FACILITY_SIZE_CATALOGS))
        raise ValueError(
            f"Unknown facility size catalog {params.facility_size_catalog_id!r} "
            f"for {params.city_airport_market_id}; available catalogs: {available}"
        ) from exc


def validate_airport_facility_slots(params: CityAirportMarketDemandParams) -> None:
    catalog = facility_catalog_for_params(params)
    slots_by_airport: dict[str, list[AirportFacilitySlot]] = {}
    for slot in params.airport_facility_slots:
        slots_by_airport.setdefault(slot.airport_id, []).append(slot)
        if slot.facility_size not in catalog.facility_sizes:
            raise ValueError(f"Unknown facility size {slot.facility_size!r} for {slot.slot_id}")
        allowed_sizes = catalog.slot_role_allowed_sizes.get(slot.slot_role)
        if allowed_sizes is None:
            raise ValueError(f"Unknown slot role {slot.slot_role!r} for {slot.slot_id}")
        if slot.facility_size not in allowed_sizes:
            raise ValueError(
                f"{slot.slot_id} role {slot.slot_role} cannot use {slot.facility_size}; "
                f"allowed sizes: {sorted(allowed_sizes)}"
            )

    if params.region_id == "china_mainland":
        for airport_id, slots in slots_by_airport.items():
            expected_roles = catalog.slot_count_role_templates.get(len(slots))
            if expected_roles is None:
                continue
            actual_roles = tuple(slot.slot_role for slot in slots)
            if actual_roles != expected_roles:
                raise ValueError(
                    f"{params.city_airport_market_id} {airport_id} uses {len(slots)} slots "
                    f"with roles {actual_roles}; expected {expected_roles}"
                )


def facility_slot_spec(slot: AirportFacilitySlot, params: CityAirportMarketDemandParams) -> FacilitySizeSpec:
    catalog = facility_catalog_for_params(params)
    try:
        return catalog.facility_sizes[slot.facility_size]
    except KeyError as exc:
        raise ValueError(f"Unknown facility size {slot.facility_size!r} for {slot.slot_id}") from exc


def airport_capacity_profile(year: int, params: CityAirportMarketDemandParams) -> dict[str, Any]:
    slots = active_facility_slots(year, params)
    design_capacity = 0.0
    max_capacity = 0.0
    design_by_airport: dict[str, float] = {}
    max_by_airport: dict[str, float] = {}
    active_slot_labels = []

    for slot in slots:
        spec = facility_slot_spec(slot, params)
        design_capacity += spec.design_capacity_million
        max_capacity += spec.max_capacity_million
        design_by_airport[slot.airport_id] = design_by_airport.get(slot.airport_id, 0.0) + spec.design_capacity_million
        max_by_airport[slot.airport_id] = max_by_airport.get(slot.airport_id, 0.0) + spec.max_capacity_million
        active_slot_labels.append(f"{slot.slot_id}:{slot.facility_size}")

    return {
        "design_capacity_million": design_capacity,
        "max_capacity_million": max_capacity,
        "design_by_airport": design_by_airport,
        "max_by_airport": max_by_airport,
        "active_slot_labels": active_slot_labels,
    }


def city_capacity_million(row: dict[str, Any], params: CityAirportMarketDemandParams) -> float:
    year = int(as_float(row, "year"))
    return airport_capacity_profile(year, params)["max_capacity_million"]


def airport_crowding_index(served: float, design_capacity: float, max_capacity: float) -> float:
    if served <= design_capacity:
        return 0.0
    crowded_band = max(0.01, max_capacity - design_capacity)
    return clamp((served - design_capacity) / crowded_band * 100.0, 0.0, 100.0)


def airline_supply_event_impulse(row: dict[str, Any]) -> float:
    hint = str(row.get("airport_event_hint") or "none")
    branch_state = str(row.get("branch_scenario_state") or "baseline")
    branch_phase = str(row.get("branch_effect_phase") or "none")
    impulse = 0.0

    if hint == "business_travel_credit_drag":
        impulse -= 2.0
    if hint == "outbound_fx_squeeze":
        impulse -= 2.5
    if hint == "fare_shock_leisure_drag":
        impulse -= 3.0
    if hint == "broad_travel_recovery":
        impulse += 3.0
    if hint == "premium_mix_volatility":
        impulse -= 1.0

    if branch_state in {"occurred", "counterfactual"} and branch_phase == "impact":
        impulse -= 4.0
    elif branch_state in {"occurred", "counterfactual"} and branch_phase == "tail":
        impulse -= 2.0
    elif branch_state == "watch" and branch_phase == "watch":
        impulse -= 0.6

    return impulse


def city_airline_supply_cycle_impulse(row: dict[str, Any], params: CityAirportMarketDemandParams) -> float:
    seed = int(as_float(row, "seed"))
    year_index = as_float(row, "year_index")
    volatility = clamp(params.airline_supply_volatility_bias, 0.4, 1.8)
    amplitude = (
        params.airline_supply_cycle_amplitude_pct
        * volatility
        * interpolate(0.75, 1.35, stable_unit_float("airline_cycle_amplitude", params.city_airport_market_id, seed))
    )
    period = interpolate(4.0, 8.0, stable_unit_float("airline_cycle_period", params.city_airport_market_id, seed))
    phase = interpolate(0.0, period, stable_unit_float("airline_cycle_phase", params.city_airport_market_id, seed))
    short_period = max(2.4, period * 0.47)
    short_phase = interpolate(0.0, short_period, stable_unit_float("airline_cycle_short_phase", params.city_airport_market_id, seed))
    regional_investment_bias = first_float(
        row,
        (
            "source_regional_seed_investment_cycle_bias_pct",
            "supply_source_regional_seed_investment_cycle_bias_pct",
            "macro_regional_seed_investment_cycle_bias_pct",
        ),
        0.0,
    )
    investment_tilt = clamp(regional_investment_bias * 0.35, -3.0, 3.0)
    primary_cycle = math.sin((year_index + phase) / period * math.tau) * amplitude
    secondary_cycle = math.sin((year_index + short_phase) / short_period * math.tau) * amplitude * 0.36
    return primary_cycle + secondary_cycle + investment_tilt


def city_airline_supply_shock_impulse(row: dict[str, Any], params: CityAirportMarketDemandParams) -> float:
    seed = int(as_float(row, "seed"))
    year_index = as_float(row, "year_index")
    volatility = clamp(params.airline_supply_volatility_bias, 0.4, 1.8)
    shock = 0.0
    for slot in range(3):
        center = interpolate(
            5.0,
            56.0,
            stable_unit_float("airline_supply_shock_center", params.city_airport_market_id, seed, slot),
        )
        width = interpolate(
            1.25,
            3.75,
            stable_unit_float("airline_supply_shock_width", params.city_airport_market_id, seed, slot),
        )
        direction_unit = stable_unit_float("airline_supply_shock_direction", params.city_airport_market_id, seed, slot)
        magnitude = (
            params.airline_supply_shock_amplitude_pct
            * volatility
            * interpolate(0.35, 1.0, stable_unit_float("airline_supply_shock_size", params.city_airport_market_id, seed, slot))
        )
        direction = -1.0 if direction_unit < 0.58 else 0.75
        distance = (year_index - center) / width
        shock += direction * magnitude * math.exp(-0.5 * distance * distance)

    cut_risk = max(0.0, as_float(row, "supply_capacity_cut_risk_index", 32.0) - 60.0)
    stress = max(0.0, first_float(row, ("input_macro_stress_index", "macro_stress_index"), 25.0) - 55.0)
    return shock - cut_risk * 0.10 - stress * 0.08


def airline_supply_volatility_regime(cycle_impulse: float, shock_impulse: float, event_impulse: float) -> str:
    pressure = abs(cycle_impulse) + abs(shock_impulse) + abs(event_impulse)
    if pressure >= 18.0:
        return "highly_volatile_airline_supply"
    if pressure >= 10.0:
        return "volatile_airline_supply"
    return "normal_airline_supply_cycle"


def city_airline_supply_profile(
    row: dict[str, Any],
    params: CityAirportMarketDemandParams,
    city_potential: float,
    previous_supply_index: float | None = None,
) -> dict[str, Any]:
    regional_seat_index = as_float(
        row,
        "supply_available_seat_capacity_index",
        as_float(row, "supply_regional_air_capacity_index", 100.0),
    )
    regional_growth_pct = max(0.0, regional_seat_index - 100.0)
    year_index = as_float(row, "year_index")
    local_growth_pct = min(
        params.max_local_airline_supply_growth_pct,
        year_index * params.annual_local_airline_supply_growth_pct,
    )
    confidence_adjustment = (
        (as_float(row, "supply_airline_capacity_confidence_index", 50.0) - 50.0)
        * 0.08
        * params.airline_supply_confidence_bias
    )
    appetite_adjustment = (
        (as_float(row, "supply_fleet_expansion_appetite_index", 45.0) - 45.0) * 0.10
        + (as_float(row, "supply_route_growth_appetite_index", 45.0) - 45.0) * 0.12
    ) * params.airline_supply_appetite_bias
    constraint_drag = (
        max(0.0, as_float(row, "supply_aircraft_delivery_constraint_index", 25.0) - 25.0) * 0.16
        + max(0.0, as_float(row, "supply_crew_labor_constraint_index", 22.0) - 22.0) * 0.12
        + max(0.0, as_float(row, "supply_maintenance_cost_pressure_index", 25.0) - 25.0) * 0.10
        + max(0.0, as_float(row, "supply_capacity_cut_risk_index", 32.0) - 32.0) * 0.12
        + max(0.0, as_float(row, "supply_airline_profit_pressure_index", 45.0) - 45.0) * 0.08
        + max(0.0, as_float(row, "supply_airport_slot_constraint_index", 30.0) - 30.0) * 0.12
    ) * params.airline_supply_constraint_bias

    trend_index = (
        100.0
        + regional_growth_pct * params.regional_airline_capacity_growth_capture
        + local_growth_pct
    )
    potential_anchor_index = city_potential / params.base_airline_supply_passengers_million * 100.0
    demand_pull_pct = clamp(
        (potential_anchor_index - trend_index) * params.airline_supply_demand_pull_capture,
        -28.0,
        155.0,
    )
    macro_adjustment = confidence_adjustment + appetite_adjustment
    cycle_impulse = city_airline_supply_cycle_impulse(row, params)
    shock_impulse = city_airline_supply_shock_impulse(row, params)
    event_impulse = airline_supply_event_impulse(row)
    target_index = (
        trend_index
        + demand_pull_pct
        + confidence_adjustment
        + appetite_adjustment
        - constraint_drag
        + cycle_impulse
        + shock_impulse
        + event_impulse
    )
    if previous_supply_index is None:
        lag_adjustment = 0.0
        raw_index = target_index
    else:
        adjustment_speed = clamp(params.airline_supply_adjustment_speed, 0.25, 0.85)
        lag_adjustment = (target_index - previous_supply_index) * adjustment_speed
        raw_index = previous_supply_index + lag_adjustment

    supply_ceiling_index = max(255.0, min(380.0, potential_anchor_index * 1.10))
    supply_index = clamp(raw_index, 62.0, supply_ceiling_index)
    return {
        "potential_anchor_index": potential_anchor_index,
        "trend_index": trend_index,
        "demand_pull_pct": demand_pull_pct,
        "macro_adjustment_pct": macro_adjustment,
        "constraint_drag_pct": constraint_drag,
        "cycle_impulse_pct": cycle_impulse,
        "shock_impulse_pct": shock_impulse,
        "event_impulse_pct": event_impulse,
        "target_index": target_index,
        "lag_adjustment_pct": lag_adjustment,
        "ceiling_index": supply_ceiling_index,
        "supply_index": supply_index,
        "volatility_regime": airline_supply_volatility_regime(cycle_impulse, shock_impulse, event_impulse),
    }


def city_airline_supply_index(row: dict[str, Any], params: CityAirportMarketDemandParams) -> float:
    city_potential = as_float(row, "city_potential_passengers_million", params.baseline_city_potential_passengers_million)
    return float(city_airline_supply_profile(row, params, city_potential)["supply_index"])


def city_airline_supply_passengers_million(row: dict[str, Any], params: CityAirportMarketDemandParams) -> float:
    return params.base_airline_supply_passengers_million * city_airline_supply_index(row, params) / 100.0


def demand_regime(growth_pct: float) -> str:
    if growth_pct >= 5.0:
        return "fast_city_demand_growth"
    if growth_pct >= 2.5:
        return "steady_city_demand_growth"
    if growth_pct >= 0.0:
        return "slow_city_demand_growth"
    return "city_demand_contraction"


def capacity_regime(fulfillment_pct: float, design_utilization_pct: float, max_utilization_pct: float) -> str:
    if fulfillment_pct < 85.0 or max_utilization_pct > 100.0:
        return "severe_city_capacity_bottleneck"
    if fulfillment_pct < 100.0:
        return "city_capacity_shortage"
    if design_utilization_pct > 100.0:
        return "crowded_city_capacity"
    if design_utilization_pct >= 92.0:
        return "full_design_city_capacity"
    return "comfortable_city_capacity"


def airline_supply_regime(fulfillment_pct: float, utilization_pct: float) -> str:
    if fulfillment_pct >= 99.0 and utilization_pct < 90.0:
        return "comfortable_airline_supply"
    if fulfillment_pct >= 96.0:
        return "tight_airline_supply"
    if fulfillment_pct >= 88.0:
        return "airline_supply_shortage"
    return "severe_airline_supply_bottleneck"


def binding_bottleneck(city_potential: float, airline_supply: float, airport_capacity: float) -> str:
    if city_potential <= min(airline_supply, airport_capacity):
        return "demand_limited"

    airline_gap = max(0.0, city_potential - airline_supply)
    airport_gap = max(0.0, city_potential - airport_capacity)
    if airline_gap > 0.0 and airport_gap > 0.0:
        gap_delta = abs(airline_supply - airport_capacity)
        if city_potential and gap_delta / city_potential <= 0.02:
            return "dual_airline_airport_bottleneck"
        return "airline_bottleneck" if airline_supply < airport_capacity else "airport_bottleneck"
    if airline_gap > 0.0:
        return "airline_bottleneck"
    if airport_gap > 0.0:
        return "airport_bottleneck"
    return "demand_limited"


def simulate_city_airport_demand(
    merged_rows: list[dict[str, Any]],
    params: CityAirportMarketDemandParams,
) -> list[dict[str, Any]]:
    validate_airport_facility_slots(params)
    output = []
    previous_potential_by_seed: dict[int, float] = {}
    previous_airline_supply_index_by_seed: dict[int, float] = {}

    for row in merged_rows:
        seed = int(as_float(row, "seed"))
        year = int(as_float(row, "year"))
        region_potential = as_float(row, "supply_potential_passengers_million")
        region_served = as_float(row, "supply_served_passengers_million", region_potential)
        component_indices, component_passengers, component_shares, seed_profile = city_component_passengers(row, params)
        city_potential = sum(component_passengers.values())
        city_share_pct = city_potential / region_potential * 100.0 if region_potential else 0.0
        adjustment = city_share_pct - params.baseline_region_demand_share_pct
        capacity_profile = airport_capacity_profile(year, params)
        design_capacity = float(capacity_profile["design_capacity_million"])
        max_capacity = float(capacity_profile["max_capacity_million"])
        effective_capacity = max_capacity
        airline_supply_profile = city_airline_supply_profile(
            row,
            params,
            city_potential,
            previous_airline_supply_index_by_seed.get(seed),
        )
        airline_supply_index = float(airline_supply_profile["supply_index"])
        previous_airline_supply_index_by_seed[seed] = airline_supply_index
        airline_supply = params.base_airline_supply_passengers_million * airline_supply_index / 100.0
        (
            component_airline_supply,
            component_airline_supply_shares,
            component_airline_supply_fulfillment,
            component_airline_supply_gaps,
        ) = component_airline_supply_passengers(row, component_passengers, airline_supply)
        airport_capacity_allocation_ratio_pct = clamp(
            effective_capacity / airline_supply * 100.0 if airline_supply else 100.0,
            0.0,
            100.0,
        )
        airport_capacity_limited_airline_supply = max(0.0, airline_supply - effective_capacity)
        effective_service_capacity = min(effective_capacity, airline_supply)
        fulfillment_pct = clamp(effective_capacity / city_potential * 100.0 if city_potential else 100.0, 0.0, 100.0)
        airline_fulfillment_pct = clamp(airline_supply / city_potential * 100.0 if city_potential else 100.0, 0.0, 100.0)
        total_fulfillment_pct = clamp(
            effective_service_capacity / city_potential * 100.0 if city_potential else 100.0,
            0.0,
            100.0,
        )
        served = min(city_potential, effective_service_capacity)
        final_service_ratio_pct = clamp(served / city_potential * 100.0 if city_potential else 100.0, 0.0, 100.0)
        unmet = max(0.0, city_potential - served)
        utilization_pct = city_potential / effective_capacity * 100.0 if effective_capacity else 0.0
        design_utilization_pct = served / design_capacity * 100.0 if design_capacity else 0.0
        max_utilization_pct = served / max_capacity * 100.0 if max_capacity else 0.0
        airport_throughput_utilization_pct = served / effective_capacity * 100.0 if effective_capacity else 0.0
        crowding_index = airport_crowding_index(served, design_capacity, max_capacity)
        airline_utilization_pct = served / airline_supply * 100.0 if airline_supply else 0.0
        unmet_share_pct = unmet / city_potential * 100.0 if city_potential else 0.0
        airline_supply_gap = max(0.0, city_potential - airline_supply)
        airport_capacity_gap = max(0.0, city_potential - effective_capacity)
        bottleneck = binding_bottleneck(city_potential, airline_supply, effective_capacity)
        previous_potential = previous_potential_by_seed.get(seed, city_potential)
        city_growth = pct_change(city_potential, previous_potential)
        previous_potential_by_seed[seed] = city_potential

        business_passengers = component_passengers["business"]
        leisure_passengers = component_passengers["leisure"]
        vfr_passengers = component_passengers["vfr"]
        long_haul_passengers = component_passengers["long_haul"]
        transfer_passengers = component_passengers["transfer"]
        final_service_ratio = final_service_ratio_pct / 100.0
        business_served_passengers = business_passengers * final_service_ratio
        leisure_served_passengers = leisure_passengers * final_service_ratio
        vfr_served_passengers = vfr_passengers * final_service_ratio
        long_haul_served_passengers = long_haul_passengers * final_service_ratio
        transfer_served_passengers = transfer_passengers * final_service_ratio
        business_share = business_passengers / city_potential * 100.0 if city_potential else 0.0
        leisure_share = leisure_passengers / city_potential * 100.0 if city_potential else 0.0
        vfr_share = vfr_passengers / city_potential * 100.0 if city_potential else 0.0
        long_haul_share = long_haul_passengers / city_potential * 100.0 if city_potential else 0.0
        transfer_share = transfer_passengers / city_potential * 100.0 if city_potential else 0.0

        premium_propensity = clamp(
            as_float(row, "premium_passenger_propensity_index", 100.0) * params.premium_propensity_bias
            + 0.24 * (business_share - 32.0)
            + 0.12 * (long_haul_share - 10.0),
            55.0,
            260.0,
        )
        premium_share = clamp(
            as_float(row, "premium_passenger_share_pct") * params.premium_share_bias
            + 0.035 * (business_share - 32.0),
            0.0,
            38.0,
        )
        regional_macro_stress_index = first_float(
            row,
            (
                "macro_regional_macro_stress_index",
                "macro_regional_macro_stress_index_reconciled",
                "macro_regional_macro_stress_index_raw",
            ),
            as_float(row, "input_macro_stress_index", 25.0),
        )
        headline_inflation_pct = first_float(
            row,
            (
                "macro_regional_headline_inflation_pct",
                "macro_regional_headline_inflation_pct_reconciled",
                "macro_regional_headline_inflation_pct_raw",
            ),
            2.0,
        )
        core_inflation_pct = first_float(
            row,
            (
                "macro_regional_core_inflation_pct",
                "macro_regional_core_inflation_pct_reconciled",
                "macro_regional_core_inflation_pct_raw",
            ),
            2.0,
        )
        energy_cost_pressure_index = first_float(
            row,
            (
                "macro_regional_energy_cost_pressure_index",
                "macro_regional_energy_cost_pressure_index_reconciled",
                "macro_regional_energy_cost_pressure_index_raw",
                "input_energy_cost_pressure_index",
            ),
            50.0,
        )
        consumer_confidence_index = as_float(
            row,
            "input_consumer_confidence_index",
            first_float(row, ("macro_consumer_confidence_index",), 50.0),
        )
        currency_pressure_index = as_float(
            row,
            "input_currency_pressure_index",
            first_float(row, ("macro_currency_pressure_index",), 35.0),
        )
        macro_stress_index = as_float(row, "input_macro_stress_index", regional_macro_stress_index)
        regional_seed_label = str(
            row.get("source_regional_seed_momentum_label")
            or row.get("supply_source_regional_seed_momentum_label")
            or row.get("macro_regional_seed_momentum_label")
            or "none"
        )
        regional_seed_growth_bias = first_float(
            row,
            (
                "source_regional_seed_effective_growth_bias_pct",
                "macro_regional_seed_effective_growth_bias_pct",
            ),
            0.0,
        )
        regional_seed_aviation_bias = first_float(
            row,
            (
                "source_regional_seed_aviation_propensity_bias_pct",
                "supply_source_regional_seed_aviation_propensity_bias_pct",
                "macro_regional_seed_aviation_propensity_bias_pct",
            ),
            0.0,
        )
        regional_seed_investment_bias = first_float(
            row,
            (
                "source_regional_seed_investment_cycle_bias_pct",
                "supply_source_regional_seed_investment_cycle_bias_pct",
                "macro_regional_seed_investment_cycle_bias_pct",
            ),
            0.0,
        )
        regional_seed_openness_bias = first_float(
            row,
            (
                "source_regional_seed_openness_bias_pct",
                "supply_source_regional_seed_openness_bias_pct",
                "macro_regional_seed_openness_bias_pct",
            ),
            0.0,
        )
        regional_seed_demand_multiplier = first_float(
            row,
            (
                "source_regional_seed_demand_multiplier",
                "supply_source_regional_seed_demand_multiplier",
                "macro_regional_seed_demand_multiplier",
            ),
            1.0,
        )

        item = round_record(
            {
                "city_airport_demand_param_version": CITY_AIRPORT_DEMAND_PARAM_VERSION,
                "city_airport_demand_interface_version": CITY_AIRPORT_DEMAND_INTERFACE_VERSION,
                "city_airport_market_id": params.city_airport_market_id,
                "city_name": params.city_name,
                "region_id": params.region_id,
                "region_name": params.region_name,
                "year_index": int(as_float(row, "year_index")),
                "year": int(as_float(row, "year")),
                "seed": seed,
                "market_tier": params.market_tier,
                "market_type": params.market_type,
                "airport_system": params.airport_system,
                "airport_facility_slot_profile_id": params.airport_facility_slot_profile_id,
                "facility_size_catalog_id": params.facility_size_catalog_id,
                "active_airport_facility_slots": ";".join(capacity_profile["active_slot_labels"]),
                "source_regional_air_demand_index": as_float(row, "regional_air_demand_index"),
                "source_regional_air_demand_growth_pct": as_float(row, "regional_air_demand_growth_pct"),
                "source_region_potential_passengers_million": region_potential,
                "source_region_served_passengers_million": region_served,
                "source_regional_seed_momentum_label": regional_seed_label,
                "source_regional_seed_effective_growth_bias_pct": regional_seed_growth_bias,
                "source_regional_seed_aviation_propensity_bias_pct": regional_seed_aviation_bias,
                "source_regional_seed_investment_cycle_bias_pct": regional_seed_investment_bias,
                "source_regional_seed_openness_bias_pct": regional_seed_openness_bias,
                "source_regional_seed_demand_multiplier": regional_seed_demand_multiplier,
                "baseline_region_demand_share_pct": params.baseline_region_demand_share_pct,
                "city_share_adjustment_pp": adjustment,
                "city_demand_share_pct": city_share_pct,
                "city_air_demand_growth_pct": city_growth,
                "seed_city_potential_enabled": seed_profile["enabled"],
                "seed_city_potential_template_id": seed_profile["template_id"],
                "seed_city_structural_momentum_score": seed_profile["structural_momentum_score"],
                "seed_city_regional_alignment_score": seed_profile["regional_alignment_score"],
                "seed_city_momentum_label": seed_profile["momentum_label"],
                "seed_city_annual_growth_bias_pct": seed_profile["annual_growth_bias_pct"],
                "seed_city_max_growth_bias_pct": seed_profile["max_growth_bias_pct"],
                "seed_city_effect_release_pct": seed_profile["effect_release_pct"],
                "seed_city_effective_bias_pct": seed_profile["effective_bias_pct"],
                "seed_city_potential_multiplier": seed_profile["potential_multiplier"],
                "city_potential_passengers_million": city_potential,
                "city_airport_design_capacity_million": design_capacity,
                "city_airport_max_capacity_million": max_capacity,
                "city_effective_capacity_million": effective_capacity,
                "city_airline_supply_potential_anchor_index": airline_supply_profile["potential_anchor_index"],
                "city_airline_supply_trend_index": airline_supply_profile["trend_index"],
                "city_airline_supply_demand_pull_pct": airline_supply_profile["demand_pull_pct"],
                "city_airline_supply_macro_adjustment_pct": airline_supply_profile["macro_adjustment_pct"],
                "city_airline_supply_constraint_drag_pct": airline_supply_profile["constraint_drag_pct"],
                "city_airline_supply_cycle_impulse_pct": airline_supply_profile["cycle_impulse_pct"],
                "city_airline_supply_shock_impulse_pct": airline_supply_profile["shock_impulse_pct"],
                "city_airline_supply_event_impulse_pct": airline_supply_profile["event_impulse_pct"],
                "city_airline_supply_target_index": airline_supply_profile["target_index"],
                "city_airline_supply_lag_adjustment_pct": airline_supply_profile["lag_adjustment_pct"],
                "city_airline_supply_ceiling_index": airline_supply_profile["ceiling_index"],
                "city_airline_supply_index": airline_supply_index,
                "city_airline_supply_volatility_regime": airline_supply_profile["volatility_regime"],
                "city_airline_supply_passengers_million": airline_supply,
                "airport_capacity_allocation_ratio_pct": airport_capacity_allocation_ratio_pct,
                "airport_capacity_limited_airline_supply_million": airport_capacity_limited_airline_supply,
                "city_effective_service_capacity_million": effective_service_capacity,
                "city_capacity_utilization_pct": utilization_pct,
                "city_airport_design_utilization_pct": design_utilization_pct,
                "city_airport_max_utilization_pct": max_utilization_pct,
                "city_capacity_fulfillment_pct": fulfillment_pct,
                "city_airport_throughput_utilization_pct": airport_throughput_utilization_pct,
                "city_airport_crowding_index": crowding_index,
                "city_airline_supply_utilization_pct": airline_utilization_pct,
                "city_airline_supply_fulfillment_pct": airline_fulfillment_pct,
                "city_total_fulfillment_pct": total_fulfillment_pct,
                "final_passenger_service_ratio_pct": final_service_ratio_pct,
                "city_served_passengers_million": served,
                "city_unmet_passengers_million": unmet,
                "city_unmet_demand_share_pct": unmet_share_pct,
                "city_airline_supply_gap_million": airline_supply_gap,
                "city_airport_capacity_gap_million": airport_capacity_gap,
                "city_binding_bottleneck": bottleneck,
                "business_city_demand_index": component_indices["business"],
                "leisure_city_demand_index": component_indices["leisure"],
                "vfr_city_demand_index": component_indices["vfr"],
                "long_haul_city_demand_index": component_indices["long_haul"],
                "transfer_city_demand_index": component_indices["transfer"],
                "business_passenger_share_pct": business_share,
                "leisure_passenger_share_pct": leisure_share,
                "vfr_passenger_share_pct": vfr_share,
                "long_haul_passenger_share_pct": long_haul_share,
                "transfer_passenger_share_pct": transfer_share,
                "business_passengers_million": business_passengers,
                "leisure_passengers_million": leisure_passengers,
                "vfr_passengers_million": vfr_passengers,
                "long_haul_passengers_million": long_haul_passengers,
                "transfer_passengers_million": transfer_passengers,
                "business_airline_supply_share_pct": component_airline_supply_shares["business"],
                "leisure_airline_supply_share_pct": component_airline_supply_shares["leisure"],
                "vfr_airline_supply_share_pct": component_airline_supply_shares["vfr"],
                "long_haul_airline_supply_share_pct": component_airline_supply_shares["long_haul"],
                "transfer_airline_supply_share_pct": component_airline_supply_shares["transfer"],
                "business_airline_supply_passengers_million": component_airline_supply["business"],
                "leisure_airline_supply_passengers_million": component_airline_supply["leisure"],
                "vfr_airline_supply_passengers_million": component_airline_supply["vfr"],
                "long_haul_airline_supply_passengers_million": component_airline_supply["long_haul"],
                "transfer_airline_supply_passengers_million": component_airline_supply["transfer"],
                "business_airline_supply_fulfillment_pct": component_airline_supply_fulfillment["business"],
                "leisure_airline_supply_fulfillment_pct": component_airline_supply_fulfillment["leisure"],
                "vfr_airline_supply_fulfillment_pct": component_airline_supply_fulfillment["vfr"],
                "long_haul_airline_supply_fulfillment_pct": component_airline_supply_fulfillment["long_haul"],
                "transfer_airline_supply_fulfillment_pct": component_airline_supply_fulfillment["transfer"],
                "business_airline_supply_gap_million": component_airline_supply_gaps["business"],
                "leisure_airline_supply_gap_million": component_airline_supply_gaps["leisure"],
                "vfr_airline_supply_gap_million": component_airline_supply_gaps["vfr"],
                "long_haul_airline_supply_gap_million": component_airline_supply_gaps["long_haul"],
                "transfer_airline_supply_gap_million": component_airline_supply_gaps["transfer"],
                "business_served_passengers_million": business_served_passengers,
                "leisure_served_passengers_million": leisure_served_passengers,
                "vfr_served_passengers_million": vfr_served_passengers,
                "long_haul_served_passengers_million": long_haul_served_passengers,
                "transfer_served_passengers_million": transfer_served_passengers,
                "premium_passenger_propensity_index": premium_propensity,
                "premium_passenger_share_pct": premium_share,
                "duty_free_propensity_index": as_float(row, "duty_free_propensity_index", 100.0) * params.duty_free_bias,
                "luxury_retail_propensity_index": as_float(row, "luxury_retail_propensity_index", 100.0)
                * params.luxury_retail_bias,
                "electronics_retail_propensity_index": as_float(row, "electronics_retail_propensity_index", 100.0)
                * params.electronics_retail_bias,
                "food_beverage_propensity_index": as_float(row, "food_beverage_propensity_index", 100.0)
                * params.food_beverage_bias,
                "general_retail_propensity_index": as_float(row, "general_retail_propensity_index", 100.0)
                * params.general_retail_bias,
                "city_demand_regime": demand_regime(city_growth),
                "city_capacity_regime": capacity_regime(fulfillment_pct, design_utilization_pct, utilization_pct),
                "city_airline_supply_regime": airline_supply_regime(airline_fulfillment_pct, airline_utilization_pct),
                "source_aviation_demand_regime": row.get("aviation_demand_regime", ""),
                "source_supply_regime": row.get("supply_supply_regime", ""),
                "airport_event_hint": row.get("airport_event_hint", "none"),
                "branch_scenario_id": row.get("branch_scenario_id", "none"),
                "branch_scenario_state": row.get("branch_scenario_state", "baseline"),
                "branch_effect_phase": row.get("branch_effect_phase", "none"),
                "input_macro_stress_index": macro_stress_index,
                "input_consumer_confidence_index": consumer_confidence_index,
                "input_airfare_pressure_index": as_float(row, "airfare_pressure_index"),
                "input_currency_pressure_index": currency_pressure_index,
                "input_regional_gdp_index": first_float(row, ("macro_regional_gdp_index",), 100.0),
                "input_regional_gdp_growth_pct": first_float(
                    row,
                    (
                        "macro_regional_gdp_growth_pct",
                        "macro_regional_gdp_growth_pct_reconciled",
                        "macro_regional_gdp_growth_pct_raw",
                    ),
                    0.0,
                ),
                "input_regional_output_gap_pct": first_float(row, ("macro_regional_output_gap_pct",), 0.0),
                "input_headline_inflation_pct": headline_inflation_pct,
                "input_core_inflation_pct": core_inflation_pct,
                "input_headline_inflation_cost_index": inflation_cost_pressure_index(headline_inflation_pct),
                "input_core_inflation_cost_index": inflation_cost_pressure_index(core_inflation_pct),
                "input_energy_cost_pressure_index": energy_cost_pressure_index,
                "input_10y_yield_pct": first_float(
                    row,
                    (
                        "macro_regional_10y_yield_pct",
                        "macro_regional_10y_yield_pct_reconciled",
                        "macro_regional_10y_yield_pct_raw",
                    ),
                    0.0,
                ),
                "input_hy_spread_bps": first_float(
                    row,
                    (
                        "macro_regional_hy_spread_bps",
                        "macro_regional_hy_spread_bps_reconciled",
                        "macro_regional_hy_spread_bps_raw",
                    ),
                    0.0,
                ),
                "input_equity_return_pct": first_float(
                    row,
                    (
                        "macro_regional_equity_return_pct",
                        "macro_regional_equity_return_pct_reconciled",
                        "macro_regional_equity_return_pct_raw",
                    ),
                    0.0,
                ),
                "input_equity_valuation_pe": first_float(
                    row,
                    (
                        "input_equity_valuation_pe",
                        "macro_regional_equity_valuation_pe_reconciled",
                        "macro_regional_equity_valuation_pe",
                        "macro_regional_equity_valuation_pe_raw",
                    ),
                    17.0,
                ),
                "input_regional_macro_stress_index": regional_macro_stress_index,
            }
        )
        output.append(item)

    return output


def summarize_market_seed(rows: list[dict[str, Any]]) -> dict[str, Any]:
    data = rows[1:] if len(rows) > 1 else rows
    growth = [as_float(row, "city_air_demand_growth_pct") for row in data]
    fulfillment = [as_float(row, "city_capacity_fulfillment_pct") for row in rows]
    airline_fulfillment = [as_float(row, "city_airline_supply_fulfillment_pct") for row in rows]
    total_fulfillment = [as_float(row, "city_total_fulfillment_pct") for row in rows]
    airport_allocation = [as_float(row, "airport_capacity_allocation_ratio_pct") for row in rows]
    airport_limited_airline_supply = [
        as_float(row, "airport_capacity_limited_airline_supply_million") for row in rows
    ]
    unmet = [as_float(row, "city_unmet_passengers_million") for row in rows]
    final = rows[-1]
    return {
        "city_airport_market_id": final["city_airport_market_id"],
        "city_name": final["city_name"],
        "region_id": final["region_id"],
        "seed": int(as_float(final, "seed")),
        "start_year": int(as_float(rows[0], "year")),
        "end_year": int(as_float(final, "year")),
        "average_city_air_demand_growth_pct": round(mean(growth), 3) if growth else 0.0,
        "minimum_city_capacity_fulfillment_pct": round(min(fulfillment), 2) if fulfillment else 0.0,
        "minimum_city_airline_supply_fulfillment_pct": round(min(airline_fulfillment), 2)
        if airline_fulfillment
        else 0.0,
        "minimum_city_total_fulfillment_pct": round(min(total_fulfillment), 2) if total_fulfillment else 0.0,
        "minimum_airport_capacity_allocation_ratio_pct": round(min(airport_allocation), 2)
        if airport_allocation
        else 0.0,
        "maximum_airport_capacity_limited_airline_supply_million": round(max(airport_limited_airline_supply), 3)
        if airport_limited_airline_supply
        else 0.0,
        "maximum_city_unmet_passengers_million": round(max(unmet), 3) if unmet else 0.0,
        "final_city_demand_share_pct": as_float(final, "city_demand_share_pct"),
        "seed_city_potential_enabled": int(as_float(final, "seed_city_potential_enabled")),
        "seed_city_potential_template_id": final.get("seed_city_potential_template_id", ""),
        "seed_city_structural_momentum_score": as_float(final, "seed_city_structural_momentum_score"),
        "seed_city_regional_alignment_score": as_float(final, "seed_city_regional_alignment_score"),
        "seed_city_momentum_label": final.get("seed_city_momentum_label", ""),
        "seed_city_annual_growth_bias_pct": as_float(final, "seed_city_annual_growth_bias_pct"),
        "seed_city_max_growth_bias_pct": as_float(final, "seed_city_max_growth_bias_pct"),
        "final_seed_city_effective_bias_pct": as_float(final, "seed_city_effective_bias_pct"),
        "final_seed_city_potential_multiplier": as_float(final, "seed_city_potential_multiplier"),
        "final_city_potential_passengers_million": as_float(final, "city_potential_passengers_million"),
        "final_city_airport_design_capacity_million": as_float(final, "city_airport_design_capacity_million"),
        "final_city_airport_max_capacity_million": as_float(final, "city_airport_max_capacity_million"),
        "final_city_airport_crowding_index": as_float(final, "city_airport_crowding_index"),
        "final_city_airline_supply_passengers_million": as_float(final, "city_airline_supply_passengers_million"),
        "final_airport_capacity_allocation_ratio_pct": as_float(final, "airport_capacity_allocation_ratio_pct"),
        "final_airport_capacity_limited_airline_supply_million": as_float(
            final, "airport_capacity_limited_airline_supply_million"
        ),
        "final_city_effective_capacity_million": as_float(final, "city_effective_capacity_million"),
        "final_city_effective_service_capacity_million": as_float(final, "city_effective_service_capacity_million"),
        "final_city_served_passengers_million": as_float(final, "city_served_passengers_million"),
        "final_city_unmet_passengers_million": as_float(final, "city_unmet_passengers_million"),
        "final_city_total_fulfillment_pct": as_float(final, "city_total_fulfillment_pct"),
        "final_city_binding_bottleneck": final.get("city_binding_bottleneck"),
        "final_city_capacity_regime": final.get("city_capacity_regime"),
        "final_city_airline_supply_regime": final.get("city_airline_supply_regime"),
        "final_business_passengers_million": as_float(final, "business_passengers_million"),
        "final_leisure_passengers_million": as_float(final, "leisure_passengers_million"),
        "final_vfr_passengers_million": as_float(final, "vfr_passengers_million"),
        "final_long_haul_passengers_million": as_float(final, "long_haul_passengers_million"),
        "final_transfer_passengers_million": as_float(final, "transfer_passengers_million"),
        "final_business_served_passengers_million": as_float(final, "business_served_passengers_million"),
        "final_leisure_served_passengers_million": as_float(final, "leisure_served_passengers_million"),
        "final_vfr_served_passengers_million": as_float(final, "vfr_served_passengers_million"),
        "final_long_haul_served_passengers_million": as_float(final, "long_haul_served_passengers_million"),
        "final_transfer_served_passengers_million": as_float(final, "transfer_served_passengers_million"),
    }


def parse_args() -> argparse.Namespace:
    airport_dir = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Generate city airport market demand from regional aviation demand.")
    parser.add_argument("--market", default="beijing_airport_system", choices=sorted(CITY_MARKET_CONFIGS))
    parser.add_argument(
        "--aviation-demand-csv",
        type=Path,
        default=None,
        help="Defaults to airport/output/regional_aviation_demand/<region>_aviation_demand_seed_sweep.csv.",
    )
    parser.add_argument(
        "--air-capacity-supply-csv",
        type=Path,
        default=None,
        help="Defaults to airport/output/regional_air_capacity_supply/<region>_air_capacity_supply_seed_sweep.csv.",
    )
    parser.add_argument(
        "--regional-macro-csv",
        type=Path,
        default=None,
        help="Defaults to airport/output/regional_macro/<region>_regional_macro_seed_sweep.csv when present.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=airport_dir / "output" / "city_airport_market_demand",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    params = CITY_MARKET_CONFIGS[args.market]
    airport_dir = Path(__file__).resolve().parents[1]
    if args.aviation_demand_csv is None:
        args.aviation_demand_csv = (
            airport_dir
            / "output"
            / "regional_aviation_demand"
            / f"{params.region_id}_aviation_demand_seed_sweep.csv"
        )
    if args.air_capacity_supply_csv is None:
        args.air_capacity_supply_csv = (
            airport_dir
            / "output"
            / "regional_air_capacity_supply"
            / f"{params.region_id}_air_capacity_supply_seed_sweep.csv"
        )
    if args.regional_macro_csv is None:
        default_regional_macro_csv = (
            airport_dir
            / "output"
            / "regional_macro"
            / f"{params.region_id}_regional_macro_seed_sweep.csv"
        )
        if default_regional_macro_csv.exists():
            args.regional_macro_csv = default_regional_macro_csv
    elif not args.regional_macro_csv.exists():
        raise SystemExit(f"Regional macro CSV not found: {args.regional_macro_csv}")

    demand_rows = read_csv(args.aviation_demand_csv)
    supply_rows = read_csv(args.air_capacity_supply_csv)
    regional_macro_rows = read_csv(args.regional_macro_csv) if args.regional_macro_csv is not None else []
    merged = merge_region_inputs(params.region_id, demand_rows, supply_rows, regional_macro_rows)
    if not merged:
        raise SystemExit(f"No merged regional rows found for {params.region_id}")

    rows = simulate_city_airport_demand(merged, params)
    output_dir = args.output_dir / params.region_id
    csv_path = output_dir / f"{params.city_airport_market_id}_city_airport_demand_seed_sweep.csv"
    summary_path = output_dir / f"{params.city_airport_market_id}_city_airport_demand_summary.json"
    js_path = output_dir / f"{params.city_airport_market_id}_city_airport_demand_viewer_data.js"
    write_csv(csv_path, rows, CITY_AIRPORT_DEMAND_FIELDS)
    write_json(
        summary_path,
        {
            "city_airport_demand_param_version": CITY_AIRPORT_DEMAND_PARAM_VERSION,
            "city_airport_demand_interface_version": CITY_AIRPORT_DEMAND_INTERFACE_VERSION,
            "market": args.market,
            "regional_macro_csv": str(args.regional_macro_csv) if args.regional_macro_csv else None,
            "params": asdict(params),
            "summaries": [
                summarize_market_seed([row for row in rows if int(as_float(row, "seed")) == seed])
                for seed in sorted({int(as_float(row, "seed")) for row in rows})
            ],
        },
    )
    write_viewer_data_js(js_path, rows)
    print(json.dumps({"csv": str(csv_path), "summary": str(summary_path), "viewer": str(js_path)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
