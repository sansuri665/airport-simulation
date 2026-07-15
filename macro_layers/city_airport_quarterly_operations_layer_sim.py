from __future__ import annotations

from importlib import import_module

_SIBLING_PREFIX = f"{__package__}." if __package__ else ""
simulation_io = import_module(f"{_SIBLING_PREFIX}simulation_io")
simulation_utils = import_module(f"{_SIBLING_PREFIX}simulation_utils")

read_csv = simulation_io.read_csv_utf8_sig
write_csv = simulation_io.write_csv_utf8_sig_ignore
write_json = simulation_io.write_json_utf8_data
as_float = simulation_utils.as_float_convert_lookup_default
clamp = simulation_utils.clamp

import argparse
import copy
import csv
import hashlib
import json
import math
from pathlib import Path
from statistics import mean
from typing import Any


CITY_AIRPORT_QUARTERLY_OPERATIONS_PARAM_VERSION = "city-airport-quarterly-operations-layer-v0.22"
CITY_AIRPORT_QUARTERLY_OPERATIONS_INTERFACE_VERSION = "city-airport-quarterly-operations-interface-v0.22"

AIRPORT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_DIR = AIRPORT_DIR / "config" / "city_airport_operations"

COMPONENTS = ("business", "leisure", "vfr", "long_haul", "transfer")
QUARTERS = ("Q1", "Q2", "Q3", "Q4")

QUARTERLY_OPERATIONS_FIELDS = [
    "city_airport_quarterly_operations_param_version",
    "city_airport_quarterly_operations_interface_version",
    "operations_config_version",
    "city_airport_market_id",
    "city_name",
    "region_id",
    "region_name",
    "year_index",
    "year",
    "quarter",
    "seed",
    "currency",
    "amount_unit",
    "game_phase",
    "player_decision_enabled",
    "player_decision_start_year",
    "startup_operating_history_years",
    "input_10y_yield_pct",
    "input_hy_spread_bps",
    "input_equity_return_pct",
    "input_equity_valuation_pe",
    "annual_city_potential_passengers_million",
    "annual_city_airline_supply_index",
    "annual_city_airline_offered_capacity_million",
    "annual_city_airline_supply_passengers_million",
    "annual_city_airline_serviceable_supply_million",
    "annual_city_airline_unused_capacity_million",
    "annual_city_airline_supply_fulfillment_pct",
    "annual_city_airline_supply_gap_million",
    "annual_city_airline_supply_volatility_regime",
    "annual_served_passengers_million",
    "quarter_city_potential_passengers_million",
    "quarter_airline_offered_capacity_million",
    "quarter_airline_supply_passengers_million",
    "quarter_airline_serviceable_supply_million",
    "quarter_airline_unused_capacity_million",
    "quarter_airline_supply_fulfillment_pct",
    "quarter_airline_supply_gap_million",
    "quarter_serviceable_demand_million",
    "quarter_capacity_realization_factor_pct",
    "quarter_capacity_lost_passengers_million",
    "quarter_served_passengers_million",
    "business_quarter_potential_passengers_million",
    "leisure_quarter_potential_passengers_million",
    "vfr_quarter_potential_passengers_million",
    "long_haul_quarter_potential_passengers_million",
    "transfer_quarter_potential_passengers_million",
    "business_quarter_airline_supply_passengers_million",
    "leisure_quarter_airline_supply_passengers_million",
    "vfr_quarter_airline_supply_passengers_million",
    "long_haul_quarter_airline_supply_passengers_million",
    "transfer_quarter_airline_supply_passengers_million",
    "business_quarter_served_passengers_million",
    "leisure_quarter_served_passengers_million",
    "vfr_quarter_served_passengers_million",
    "long_haul_quarter_served_passengers_million",
    "transfer_quarter_served_passengers_million",
    "quarter_share_of_annual_served_pct",
    "base_city_airport_design_capacity_million",
    "base_city_airport_max_capacity_million",
    "renovation_active_event_ids",
    "renovation_completed_event_ids",
    "renovation_asset_in_service_periods",
    "renovation_construction_capacity_multiplier",
    "renovation_design_capacity_loss_million",
    "renovation_max_capacity_loss_million",
    "renovation_quarter_capex_outlay_million_cny",
    "renovation_construction_in_progress_million_cny",
    "renovation_asset_original_million_cny",
    "renovation_asset_residual_floor_million_cny",
    "renovation_asset_accumulated_depreciation_million_cny",
    "renovation_asset_book_value_million_cny",
    "renovation_asset_period_depreciation_million_cny",
    "construction_active_event_ids",
    "construction_completed_event_ids",
    "construction_asset_in_service_periods",
    "construction_quarter_capex_outlay_million_cny",
    "construction_in_progress_million_cny",
    "construction_asset_original_million_cny",
    "construction_asset_residual_floor_million_cny",
    "construction_asset_accumulated_depreciation_million_cny",
    "construction_asset_book_value_million_cny",
    "construction_asset_period_depreciation_million_cny",
    "rebuild_active_event_ids",
    "rebuild_started_event_ids",
    "rebuild_started_slot_ids",
    "rebuild_completed_event_ids",
    "rebuild_asset_in_service_periods",
    "rebuild_construction_capacity_multiplier",
    "rebuild_design_capacity_loss_million",
    "rebuild_max_capacity_loss_million",
    "rebuild_completed_design_capacity_delta_million",
    "rebuild_completed_max_capacity_delta_million",
    "rebuild_quarter_capex_outlay_million_cny",
    "rebuild_quarter_demolition_expense_million_cny",
    "rebuild_old_renovation_asset_writeoff_million_cny",
    "rebuild_old_rebuild_asset_writeoff_million_cny",
    "rebuild_construction_in_progress_million_cny",
    "rebuild_asset_original_million_cny",
    "rebuild_asset_residual_floor_million_cny",
    "rebuild_asset_accumulated_depreciation_million_cny",
    "rebuild_asset_book_value_million_cny",
    "rebuild_asset_period_depreciation_million_cny",
    "city_airport_design_capacity_million",
    "city_airport_max_capacity_million",
    "quarter_design_capacity_million",
    "quarter_max_capacity_million",
    "quarter_design_utilization_pct",
    "quarter_max_utilization_pct",
    "quarter_crowding_index",
    "quarter_over_max_pressure_passengers_million",
    "active_facility_slots",
    "effective_facility_slots",
    "perceived_quality_model_version",
    "city_airport_perceived_quality_index",
    "perceived_quality_size_score",
    "perceived_quality_age_score",
    "perceived_quality_capacity_score",
    "perceived_quality_construction_disruption_score",
    "slot_fixed_operating_cost_model_version",
    "slot_fixed_operating_cost_base_annual_million_cny",
    "slot_fixed_operating_cost_age_multiplier",
    "slot_fixed_operating_cost_macro_multiplier",
    "slot_fixed_operating_cost_city_complexity_multiplier",
    "slot_fixed_operating_cost_quarter_multiplier",
    "annual_slot_fixed_operating_cost_million_cny",
    "quarter_slot_fixed_operating_cost_million_cny",
    "aeronautical_revenue_model_version",
    "aeronautical_base_revenue_per_passenger_cny",
    "aeronautical_mix_revenue_adjustment",
    "aeronautical_quarter_revenue_multiplier",
    "aeronautical_market_yield_multiplier",
    "aeronautical_capacity_pricing_multiplier",
    "aeronautical_crowding_revenue_multiplier",
    "aeronautical_revenue_million_cny",
    "passenger_variable_cost_model_version",
    "passenger_variable_cost_base_per_passenger_cny",
    "passenger_variable_cost_complexity_adjustment",
    "passenger_variable_cost_quarter_multiplier",
    "passenger_variable_cost_macro_multiplier",
    "passenger_variable_cost_load_multiplier",
    "quarter_passenger_variable_cost_million_cny",
    "congestion_adjustment_model_version",
    "congestion_component_mix_multiplier",
    "congestion_design_utilization_adjustment_per_passenger_cny",
    "congestion_design_utilization_adjustment_million_cny",
    "congestion_over_max_pressure_cost_million_cny",
    "quarter_congestion_cost_million_cny",
    "food_retail_operation_mode",
    "food_retail_blended_propensity_index",
    "food_retail_revenue_model_version",
    "food_retail_base_revenue_per_passenger_cny",
    "food_retail_self_operated_efficiency",
    "food_retail_propensity_revenue_multiplier",
    "food_retail_quarter_revenue_multiplier",
    "food_retail_macro_revenue_multiplier",
    "food_retail_crowding_revenue_multiplier",
    "food_retail_perceived_quality_revenue_multiplier",
    "food_retail_revenue_million_cny",
    "food_retail_fixed_cost_model_version",
    "food_retail_fixed_cost_base_annual_million_cny",
    "food_retail_fixed_cost_intensity_multiplier",
    "food_retail_fixed_cost_city_complexity_multiplier",
    "food_retail_fixed_cost_macro_multiplier",
    "food_retail_fixed_cost_quarter_multiplier",
    "food_retail_fixed_cost_load_multiplier",
    "food_retail_fixed_operating_cost_million_cny",
    "food_retail_passenger_service_cost_model_version",
    "food_retail_passenger_service_base_cost_per_passenger_cny",
    "food_retail_passenger_service_consumption_multiplier",
    "food_retail_passenger_service_quarter_multiplier",
    "food_retail_passenger_service_macro_multiplier",
    "food_retail_passenger_service_load_multiplier",
    "food_retail_passenger_service_cost_million_cny",
    "food_retail_sales_cost_model_version",
    "food_retail_sales_cost_base_ratio_pct",
    "food_retail_sales_cost_mix_multiplier",
    "food_retail_sales_cost_macro_multiplier",
    "food_retail_sales_cost_ratio_pct",
    "food_retail_sales_cost_million_cny",
    "food_retail_operating_cost_million_cny",
    "food_retail_operating_profit_million_cny",
    "duty_free_contract_type",
    "duty_free_contract_model_version",
    "duty_free_contract_cycle_id",
    "duty_free_contract_cycle_start_year",
    "duty_free_contract_cycle_end_year",
    "duty_free_contract_status",
    "duty_free_revenue_share_pct",
    "duty_free_minimum_guarantee_ratio_pct",
    "duty_free_minimum_guarantee_coverage_pct",
    "duty_free_contract_history_years_used",
    "duty_free_contract_forecast_annual_sales_million_cny",
    "duty_free_contract_forecast_quarter_sales_million_cny",
    "duty_free_contract_trend_multiplier",
    "duty_free_contract_macro_risk_discount_multiplier",
    "duty_free_contract_bargaining_power_multiplier",
    "duty_free_contract_minimum_guarantee_million_cny",
    "duty_free_contract_share_revenue_million_cny",
    "duty_free_contract_revenue_basis",
    "duty_free_sales_model_version",
    "duty_free_base_sales_per_effective_passenger_cny",
    "duty_free_propensity_sales_multiplier",
    "duty_free_premium_mix_sales_multiplier",
    "duty_free_macro_sales_multiplier",
    "duty_free_currency_sales_multiplier",
    "duty_free_market_cycle_multiplier",
    "duty_free_international_exposure_multiplier",
    "duty_free_operator_capture_rate",
    "duty_free_crowding_sales_multiplier",
    "duty_free_perceived_quality_sales_multiplier",
    "duty_free_weighted_passengers_million",
    "duty_free_sales_million_cny",
    "duty_free_revenue_million_cny",
    "luxury_contract_type",
    "luxury_contract_model_version",
    "luxury_contract_cycle_id",
    "luxury_contract_cycle_start_year",
    "luxury_contract_cycle_end_year",
    "luxury_contract_status",
    "luxury_revenue_share_pct",
    "luxury_minimum_guarantee_ratio_pct",
    "luxury_minimum_guarantee_coverage_pct",
    "luxury_contract_history_years_used",
    "luxury_contract_forecast_annual_sales_million_cny",
    "luxury_contract_forecast_quarter_sales_million_cny",
    "luxury_contract_trend_multiplier",
    "luxury_contract_macro_risk_discount_multiplier",
    "luxury_contract_bargaining_power_multiplier",
    "luxury_contract_minimum_guarantee_million_cny",
    "luxury_contract_share_revenue_million_cny",
    "luxury_contract_revenue_basis",
    "luxury_sales_model_version",
    "luxury_base_sales_per_effective_passenger_cny",
    "luxury_propensity_sales_multiplier",
    "luxury_premium_mix_sales_multiplier",
    "luxury_high_value_mix_multiplier",
    "luxury_macro_sales_multiplier",
    "luxury_currency_sales_multiplier",
    "luxury_market_cycle_multiplier",
    "luxury_operator_capture_rate",
    "luxury_crowding_sales_multiplier",
    "luxury_perceived_quality_sales_multiplier",
    "luxury_weighted_passengers_million",
    "luxury_sales_million_cny",
    "luxury_retail_revenue_million_cny",
    "contract_commercial_revenue_million_cny",
    "commercial_revenue_million_cny",
    "commercial_direct_cost_million_cny",
    "commercial_operating_profit_million_cny",
    "total_operating_revenue_million_cny",
    "total_operating_cost_million_cny",
    "quarter_operating_profit_million_cny",
    "operating_margin_pct",
    "total_revenue_per_passenger_cny",
    "total_cost_per_passenger_cny",
    "annual_city_binding_bottleneck",
    "quarter_event_hint",
    "branch_scenario_id",
    "branch_scenario_state",
    "branch_effect_phase",
]


def stable_unit_float(*parts: Any) -> float:
    raw = "::".join(str(part) for part in parts).encode("utf-8")
    digest = hashlib.sha256(raw).digest()
    return int.from_bytes(digest[:8], "big") / float(1 << 64)


def quarter_capacity_realization_factor(
    seed: int,
    year: int,
    quarter_index: int,
    serviceable_demand: float,
    quarter_max_capacity: float,
    has_disruptive_project: bool,
) -> float:
    if quarter_max_capacity <= 0.0:
        return 0.0
    pressure = serviceable_demand / quarter_max_capacity
    if pressure < 0.98:
        return 1.0

    unit = stable_unit_float("quarter_capacity_realization", seed, year, quarter_index)
    factor = 0.975 + unit * 0.022
    if has_disruptive_project:
        factor -= 0.010
    if pressure >= 1.12:
        factor -= min(0.012, (pressure - 1.12) * 0.030)
    return clamp(factor, 0.955 if has_disruptive_project else 0.970, 0.997)


def write_viewer_data_js(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "param_version": CITY_AIRPORT_QUARTERLY_OPERATIONS_PARAM_VERSION,
        "interface_version": CITY_AIRPORT_QUARTERLY_OPERATIONS_INTERFACE_VERSION,
        "rows": rows,
    }
    path.write_text(
        "window.CITY_AIRPORT_QUARTERLY_OPERATIONS_DATA = "
        + json.dumps(payload, ensure_ascii=False)
        + ";\n",
        encoding="utf-8",
    )


def round_record(record: dict[str, Any]) -> dict[str, Any]:
    rounded: dict[str, Any] = {}
    for key, value in record.items():
        if isinstance(value, float):
            rounded[key] = round(value, 4)
        else:
            rounded[key] = value
    return rounded


def load_config(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if raw.get("schema_version") != "city-airport-quarterly-operations-config-v1":
        raise ValueError(f"Unsupported quarterly operations config schema in {path}")
    return raw


def active_facility_sizes(active_facility_slots: str) -> list[str]:
    sizes: list[str] = []
    for part in active_facility_slots.split(";"):
        if ":" not in part:
            continue
        size = part.rsplit(":", 1)[1].strip()
        if size and size != "empty":
            sizes.append(size)
    return sizes


def active_facility_slot_items(active_facility_slots: str) -> list[tuple[str, str]]:
    items: list[tuple[str, str]] = []
    for part in active_facility_slots.split(";"):
        if ":" not in part:
            continue
        slot_id, size = (piece.strip() for piece in part.rsplit(":", 1))
        if slot_id and size and size != "empty":
            items.append((slot_id, size))
    return items


def facility_slot_items_to_string(slot_items: list[tuple[str, str]]) -> str:
    return ";".join(f"{slot_id}:{size}" for slot_id, size in slot_items if slot_id and size and size != "empty")


def interpolate_curve(points: list[dict[str, Any]], x_value: float, x_key: str, y_key: str, default: float = 1.0) -> float:
    if not points:
        return default
    ordered = sorted(points, key=lambda item: float(item[x_key]))
    if x_value <= float(ordered[0][x_key]):
        return float(ordered[0][y_key])
    for left, right in zip(ordered, ordered[1:]):
        left_x = float(left[x_key])
        right_x = float(right[x_key])
        if x_value <= right_x:
            span = right_x - left_x
            if span <= 0:
                return float(right[y_key])
            ratio = (x_value - left_x) / span
            return float(left[y_key]) + (float(right[y_key]) - float(left[y_key])) * ratio
    return float(ordered[-1][y_key])


def quarter_number(quarter: str) -> int:
    if quarter in QUARTERS:
        return QUARTERS.index(quarter) + 1
    try:
        parsed = int(str(quarter).replace("Q", ""))
    except ValueError:
        parsed = 1
    return int(clamp(float(parsed), 1.0, 4.0))


def quarter_period_index(year: int, quarter: str) -> int:
    return int(year) * 4 + quarter_number(quarter) - 1


def period_index_to_year_fraction(period_index: int) -> float:
    return float(period_index) / 4.0


def period_index_label(period_index: int) -> str:
    year = period_index // 4
    quarter = f"Q{period_index % 4 + 1}"
    return f"{year}{quarter}"


def load_facility_size_specs(catalog_id: str) -> dict[str, dict[str, Any]]:
    path = AIRPORT_DIR / "config" / "facility_size_catalogs" / f"{catalog_id}.json"
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    return dict(raw.get("facility_sizes", {}))


def renovation_context(config: dict[str, Any]) -> dict[str, Any]:
    model = config.get("facility_renovation_model", {})
    catalog_id = str(model.get("facility_size_catalog", "standard_terminal_sizes_v1"))
    return {
        "model": model,
        "events": list(config.get("facility_renovation_events", [])),
        "facility_sizes": load_facility_size_specs(catalog_id) if model else {},
    }


def construction_context(config: dict[str, Any]) -> dict[str, Any]:
    model = config.get("facility_construction_model", {})
    catalog_id = str(model.get("facility_size_catalog", "standard_terminal_sizes_v1"))
    return {
        "model": model,
        "events": list(config.get("facility_construction_events", [])),
        "facility_sizes": load_facility_size_specs(catalog_id) if model else {},
    }


def rebuild_context(config: dict[str, Any]) -> dict[str, Any]:
    model = config.get("facility_rebuild_model", {})
    catalog_id = str(model.get("facility_size_catalog", "standard_terminal_sizes_v1"))
    return {
        "model": model,
        "events": list(config.get("facility_rebuild_events", [])),
        "facility_sizes": load_facility_size_specs(catalog_id) if model else {},
    }


def renovation_event_duration_quarters(event: dict[str, Any], model: dict[str, Any]) -> int:
    if "duration_quarters" in event:
        return max(1, int(event["duration_quarters"]))
    size = str(event.get("facility_size", ""))
    defaults = model.get("duration_quarters_by_facility_size", {})
    return max(1, int(defaults.get(size, model.get("default_duration_quarters", 6))))


def renovation_event_start_index(event: dict[str, Any]) -> int:
    return quarter_period_index(int(event.get("start_year", 0)), str(event.get("start_quarter", "Q1")))


def renovation_event_completion_index(event: dict[str, Any], model: dict[str, Any]) -> int:
    return renovation_event_start_index(event) + renovation_event_duration_quarters(event, model)


def renovation_event_capacity_multiplier(event: dict[str, Any], model: dict[str, Any]) -> float:
    return clamp(
        float(event.get("construction_capacity_multiplier", model.get("default_construction_capacity_multiplier", 0.75))),
        0.0,
        1.0,
    )


def renovation_event_capex(event: dict[str, Any], model: dict[str, Any]) -> float:
    if "capex_million_cny" in event:
        return max(0.0, float(event["capex_million_cny"]))
    size = str(event.get("facility_size", ""))
    replacement_costs = model.get("replacement_cost_million_cny_by_facility_size", {})
    ratios = model.get("capex_ratio_by_facility_size", {})
    replacement_cost = float(replacement_costs.get(size, 0.0))
    capex_ratio = float(ratios.get(size, model.get("default_capex_ratio", 0.3)))
    construction_multiplier = float(
        event.get(
            "construction_cost_multiplier",
            model.get("city_construction_cost_multiplier", 1.0),
        )
    )
    return max(0.0, replacement_cost * capex_ratio * construction_multiplier)


def active_renovation_events(
    events: list[dict[str, Any]],
    model: dict[str, Any],
    year: int,
    quarter: str,
) -> list[dict[str, Any]]:
    period = quarter_period_index(year, quarter)
    return [
        event
        for event in events
        if renovation_event_start_index(event) <= period < renovation_event_completion_index(event, model)
    ]


def completed_renovation_events(
    events: list[dict[str, Any]],
    model: dict[str, Any],
    year: int,
    quarter: str,
) -> list[dict[str, Any]]:
    period = quarter_period_index(year, quarter)
    return [event for event in events if renovation_event_completion_index(event, model) <= period]


def validate_slot_project_windows(
    renovation_events: list[dict[str, Any]],
    renovation_model: dict[str, Any],
    rebuild_events: list[dict[str, Any]],
    rebuild_model: dict[str, Any],
) -> None:
    windows: list[dict[str, Any]] = []
    for event in renovation_events:
        slot_id = str(event.get("slot_id", ""))
        if not slot_id:
            continue
        windows.append(
            {
                "slot_id": slot_id,
                "event_id": str(event.get("event_id", "unnamed_renovation")),
                "project_type": "renovation",
                "start": renovation_event_start_index(event),
                "end": renovation_event_completion_index(event, renovation_model),
            }
        )
    for event in rebuild_events:
        slot_id = str(event.get("slot_id", ""))
        if not slot_id:
            continue
        windows.append(
            {
                "slot_id": slot_id,
                "event_id": str(event.get("event_id", "unnamed_rebuild")),
                "project_type": "rebuild",
                "start": rebuild_event_start_index(event),
                "end": rebuild_event_completion_index(event, rebuild_model),
            }
        )

    by_slot: dict[str, list[dict[str, Any]]] = {}
    for window in windows:
        by_slot.setdefault(str(window["slot_id"]), []).append(window)

    for slot_id, slot_windows in by_slot.items():
        ordered = sorted(slot_windows, key=lambda item: (int(item["start"]), int(item["end"])))
        for left, right in zip(ordered, ordered[1:]):
            if int(right["start"]) < int(left["end"]):
                left_label = f"{left['event_id']}({left['project_type']},{period_index_label(int(left['start']))}-{period_index_label(int(left['end']))})"
                right_label = f"{right['event_id']}({right['project_type']},{period_index_label(int(right['start']))}-{period_index_label(int(right['end']))})"
                raise ValueError(
                    f"Overlapping slot project windows for {slot_id}: {left_label} overlaps {right_label}"
                )


def renovation_capacity_profile(
    active_events: list[dict[str, Any]],
    model: dict[str, Any],
    facility_sizes: dict[str, dict[str, Any]],
) -> dict[str, float | str]:
    design_loss = 0.0
    max_loss = 0.0
    weighted_capacity = 0.0
    weighted_multiplier = 0.0
    for event in active_events:
        size = str(event.get("facility_size", ""))
        spec = facility_sizes.get(size, {})
        design_capacity = float(spec.get("design_capacity_million", 0.0))
        max_capacity = float(spec.get("max_capacity_million", 0.0))
        multiplier = renovation_event_capacity_multiplier(event, model)
        design_loss += design_capacity * (1.0 - multiplier)
        max_loss += max_capacity * (1.0 - multiplier)
        weighted_capacity += design_capacity
        weighted_multiplier += design_capacity * multiplier
    return {
        "active_event_ids": ";".join(str(event.get("event_id", "")) for event in active_events if event.get("event_id")),
        "construction_capacity_multiplier": weighted_multiplier / weighted_capacity if weighted_capacity > 0 else 1.0,
        "design_loss": design_loss,
        "max_loss": max_loss,
    }


def renovation_asset_profile(
    events: list[dict[str, Any]],
    model: dict[str, Any],
    year: int,
    quarter: str,
    disposed_event_ids: set[str] | None = None,
) -> dict[str, float | str]:
    period = quarter_period_index(year, quarter)
    disposed_event_ids = disposed_event_ids or set()
    depreciation_model = model.get("renovation_asset_depreciation", {})
    default_life = float(depreciation_model.get("useful_life_years", 20.0))
    default_residual_pct = float(depreciation_model.get("residual_value_pct", 5.0))
    active_events_now = active_renovation_events(events, model, year, quarter)
    completed_events_now = [
        event
        for event in completed_renovation_events(events, model, year, quarter)
        if str(event.get("event_id", "")) not in disposed_event_ids
    ]

    capex_outlay = 0.0
    construction_in_progress = 0.0
    for event in active_events_now:
        capex = renovation_event_capex(event, model)
        duration = renovation_event_duration_quarters(event, model)
        elapsed_quarters = period - renovation_event_start_index(event) + 1
        capex_outlay += capex / duration
        construction_in_progress += capex * clamp(elapsed_quarters / duration, 0.0, 1.0)

    original = 0.0
    residual_floor = 0.0
    accumulated = 0.0
    period_depreciation = 0.0
    book_value = 0.0
    for event in completed_events_now:
        capex = renovation_event_capex(event, model)
        useful_life = float(event.get("useful_life_years", default_life))
        residual_pct = float(event.get("residual_value_pct", default_residual_pct))
        if capex <= 0 or useful_life <= 0:
            continue
        start_fraction = period_index_to_year_fraction(renovation_event_completion_index(event, model))
        target_fraction = period_index_to_year_fraction(period)
        elapsed_before_period = clamp(target_fraction - start_fraction, 0.0, useful_life)
        residual = capex * residual_pct / 100.0
        annual_depreciation = (capex - residual) / useful_life
        depreciates_this_period = elapsed_before_period < useful_life
        elapsed_at_period_end = clamp(
            elapsed_before_period + (0.25 if depreciates_this_period else 0.0),
            0.0,
            useful_life,
        )
        event_period_depreciation = annual_depreciation * 0.25 if depreciates_this_period else 0.0
        event_accumulated = annual_depreciation * elapsed_at_period_end
        original += capex
        residual_floor += residual
        accumulated += event_accumulated
        period_depreciation += event_period_depreciation
        book_value += max(capex - event_accumulated, residual)

    return {
        "active_event_ids": ";".join(str(event.get("event_id", "")) for event in active_events_now if event.get("event_id")),
        "completed_event_ids": ";".join(str(event.get("event_id", "")) for event in completed_events_now if event.get("event_id")),
        "in_service_periods": ";".join(
            period_index_label(renovation_event_completion_index(event, model)) for event in completed_events_now
        ),
        "quarter_capex_outlay": capex_outlay,
        "construction_in_progress": construction_in_progress,
        "asset_original": original,
        "asset_residual_floor": residual_floor,
        "asset_accumulated_depreciation": accumulated,
        "asset_book_value": book_value,
        "asset_period_depreciation": period_depreciation,
    }


def construction_event_size(event: dict[str, Any]) -> str:
    return str(event.get("target_facility_size", event.get("facility_size", "")))


def construction_event_duration_quarters(event: dict[str, Any], model: dict[str, Any]) -> int:
    if "duration_quarters" in event:
        return max(1, int(event["duration_quarters"]))
    size = construction_event_size(event)
    defaults = model.get("duration_quarters_by_facility_size", {})
    return max(1, int(defaults.get(size, model.get("default_duration_quarters", 12))))


def construction_event_start_index(event: dict[str, Any]) -> int:
    return quarter_period_index(int(event.get("start_year", 0)), str(event.get("start_quarter", "Q1")))


def construction_event_completion_index(event: dict[str, Any], model: dict[str, Any]) -> int:
    return construction_event_start_index(event) + construction_event_duration_quarters(event, model)


def construction_event_capex(event: dict[str, Any], model: dict[str, Any]) -> float:
    if "capex_million_cny" in event:
        return max(0.0, float(event["capex_million_cny"]))
    size = construction_event_size(event)
    construction_costs = model.get("construction_cost_million_cny_by_facility_size", {})
    base_cost = float(construction_costs.get(size, 0.0))
    construction_multiplier = float(
        event.get(
            "construction_cost_multiplier",
            model.get("city_construction_cost_multiplier", 1.0),
        )
    )
    return max(0.0, base_cost * construction_multiplier)


def active_construction_events(
    events: list[dict[str, Any]],
    model: dict[str, Any],
    year: int,
    quarter: str,
) -> list[dict[str, Any]]:
    period = quarter_period_index(year, quarter)
    return [
        event
        for event in events
        if construction_event_start_index(event) <= period < construction_event_completion_index(event, model)
    ]


def completed_construction_events(
    events: list[dict[str, Any]],
    model: dict[str, Any],
    year: int,
    quarter: str,
) -> list[dict[str, Any]]:
    period = quarter_period_index(year, quarter)
    return [event for event in events if construction_event_completion_index(event, model) <= period]


def construction_asset_profile(
    events: list[dict[str, Any]],
    model: dict[str, Any],
    year: int,
    quarter: str,
) -> dict[str, float | str]:
    period = quarter_period_index(year, quarter)
    depreciation_model = model.get("new_asset_depreciation", model.get("construction_asset_depreciation", {}))
    default_life = float(depreciation_model.get("useful_life_years", 40.0))
    default_residual_pct = float(depreciation_model.get("residual_value_pct", 10.0))
    active_events_now = active_construction_events(events, model, year, quarter)
    completed_events_now = completed_construction_events(events, model, year, quarter)

    capex_outlay = 0.0
    construction_in_progress = 0.0
    for event in active_events_now:
        capex = construction_event_capex(event, model)
        duration = construction_event_duration_quarters(event, model)
        elapsed_quarters = period - construction_event_start_index(event) + 1
        capex_outlay += capex / duration
        construction_in_progress += capex * clamp(elapsed_quarters / duration, 0.0, 1.0)

    original = 0.0
    residual_floor = 0.0
    accumulated = 0.0
    period_depreciation = 0.0
    book_value = 0.0
    for event in completed_events_now:
        capex = construction_event_capex(event, model)
        useful_life = float(event.get("useful_life_years", default_life))
        residual_pct = float(event.get("residual_value_pct", default_residual_pct))
        if capex <= 0 or useful_life <= 0:
            continue
        start_fraction = period_index_to_year_fraction(construction_event_completion_index(event, model))
        target_fraction = period_index_to_year_fraction(period)
        elapsed_before_period = clamp(target_fraction - start_fraction, 0.0, useful_life)
        residual = capex * residual_pct / 100.0
        annual_depreciation = (capex - residual) / useful_life
        depreciates_this_period = elapsed_before_period < useful_life
        elapsed_at_period_end = clamp(
            elapsed_before_period + (0.25 if depreciates_this_period else 0.0),
            0.0,
            useful_life,
        )
        event_period_depreciation = annual_depreciation * 0.25 if depreciates_this_period else 0.0
        event_accumulated = annual_depreciation * elapsed_at_period_end
        original += capex
        residual_floor += residual
        accumulated += event_accumulated
        period_depreciation += event_period_depreciation
        book_value += max(capex - event_accumulated, residual)

    return {
        "active_event_ids": ";".join(str(event.get("event_id", "")) for event in active_events_now if event.get("event_id")),
        "completed_event_ids": ";".join(
            str(event.get("event_id", "")) for event in completed_events_now if event.get("event_id")
        ),
        "in_service_periods": ";".join(
            period_index_label(construction_event_completion_index(event, model)) for event in completed_events_now
        ),
        "quarter_capex_outlay": capex_outlay,
        "construction_in_progress": construction_in_progress,
        "asset_original": original,
        "asset_residual_floor": residual_floor,
        "asset_accumulated_depreciation": accumulated,
        "asset_book_value": book_value,
        "asset_period_depreciation": period_depreciation,
    }


def rebuild_event_source_size(event: dict[str, Any]) -> str:
    return str(event.get("from_facility_size", event.get("source_facility_size", event.get("facility_size", ""))))


def rebuild_event_target_size(event: dict[str, Any]) -> str:
    return str(event.get("target_facility_size", event.get("facility_size", "")))


def rebuild_event_duration_quarters(event: dict[str, Any], model: dict[str, Any]) -> int:
    if "duration_quarters" in event:
        return max(1, int(event["duration_quarters"]))
    size = rebuild_event_target_size(event)
    defaults = model.get("duration_quarters_by_facility_size", {})
    return max(1, int(defaults.get(size, model.get("default_duration_quarters", 18))))


def rebuild_event_start_index(event: dict[str, Any]) -> int:
    return quarter_period_index(int(event.get("start_year", 0)), str(event.get("start_quarter", "Q1")))


def rebuild_event_completion_index(event: dict[str, Any], model: dict[str, Any]) -> int:
    return rebuild_event_start_index(event) + rebuild_event_duration_quarters(event, model)


def rebuild_event_capacity_multiplier(event: dict[str, Any], model: dict[str, Any]) -> float:
    # Demolition/rebuild v0.1 closes the slot completely during construction.
    return 0.0


def rebuild_event_asset_capex(event: dict[str, Any], model: dict[str, Any]) -> float:
    if "asset_capex_million_cny" in event:
        return max(0.0, float(event["asset_capex_million_cny"]))
    if "capex_million_cny" in event:
        return max(0.0, float(event["capex_million_cny"]))
    size = rebuild_event_target_size(event)
    costs = model.get("asset_cost_million_cny_by_facility_size", {})
    base_cost = float(costs.get(size, 0.0))
    multiplier = float(
        event.get(
            "construction_cost_multiplier",
            model.get("city_construction_cost_multiplier", 1.0),
        )
    )
    return max(0.0, base_cost * multiplier)


def rebuild_event_demolition_expense(event: dict[str, Any], model: dict[str, Any]) -> float:
    if "demolition_expense_million_cny" in event:
        return max(0.0, float(event["demolition_expense_million_cny"]))
    source_size = rebuild_event_source_size(event)
    source_costs = model.get("asset_cost_million_cny_by_facility_size", {})
    ratios = model.get("demolition_cost_ratio_by_source_facility_size", {})
    base_cost = float(source_costs.get(source_size, 0.0))
    ratio = float(ratios.get(source_size, model.get("default_demolition_cost_ratio", 0.10)))
    multiplier = float(
        event.get(
            "demolition_cost_multiplier",
            model.get("city_demolition_cost_multiplier", 1.0),
        )
    )
    return max(0.0, base_cost * ratio * multiplier)


def active_rebuild_events(
    events: list[dict[str, Any]],
    model: dict[str, Any],
    year: int,
    quarter: str,
) -> list[dict[str, Any]]:
    period = quarter_period_index(year, quarter)
    return [
        event
        for event in events
        if rebuild_event_start_index(event) <= period < rebuild_event_completion_index(event, model)
    ]


def started_rebuild_events(
    events: list[dict[str, Any]],
    model: dict[str, Any],
    year: int,
    quarter: str,
) -> list[dict[str, Any]]:
    period = quarter_period_index(year, quarter)
    return [event for event in events if rebuild_event_start_index(event) == period]


def completed_rebuild_events(
    events: list[dict[str, Any]],
    model: dict[str, Any],
    year: int,
    quarter: str,
) -> list[dict[str, Any]]:
    period = quarter_period_index(year, quarter)
    return [event for event in events if rebuild_event_completion_index(event, model) <= period]


def rebuild_capacity_profile(
    active_events: list[dict[str, Any]],
    completed_events: list[dict[str, Any]],
    model: dict[str, Any],
    facility_sizes: dict[str, dict[str, Any]],
) -> dict[str, float | str]:
    design_loss = 0.0
    max_loss = 0.0
    weighted_capacity = 0.0
    weighted_multiplier = 0.0
    completed_design_delta = 0.0
    completed_max_delta = 0.0
    active_ids = []
    completed_ids = []
    for event in active_events:
        active_ids.append(str(event.get("event_id", "")))
        source_spec = facility_sizes.get(rebuild_event_source_size(event), {})
        source_design = float(source_spec.get("design_capacity_million", 0.0))
        source_max = float(source_spec.get("max_capacity_million", 0.0))
        multiplier = rebuild_event_capacity_multiplier(event, model)
        design_loss += source_design * (1.0 - multiplier)
        max_loss += source_max * (1.0 - multiplier)
        weighted_capacity += source_design
        weighted_multiplier += source_design * multiplier
    for event in completed_events:
        completed_ids.append(str(event.get("event_id", "")))
        source_spec = facility_sizes.get(rebuild_event_source_size(event), {})
        target_spec = facility_sizes.get(rebuild_event_target_size(event), {})
        completed_design_delta += (
            float(target_spec.get("design_capacity_million", 0.0))
            - float(source_spec.get("design_capacity_million", 0.0))
        )
        completed_max_delta += (
            float(target_spec.get("max_capacity_million", 0.0))
            - float(source_spec.get("max_capacity_million", 0.0))
        )
    return {
        "active_event_ids": ";".join(event_id for event_id in active_ids if event_id),
        "completed_event_ids": ";".join(event_id for event_id in completed_ids if event_id),
        "construction_capacity_multiplier": weighted_multiplier / weighted_capacity if weighted_capacity > 0 else 1.0,
        "design_loss": design_loss,
        "max_loss": max_loss,
        "completed_design_delta": completed_design_delta,
        "completed_max_delta": completed_max_delta,
    }


def renovation_event_book_value_at_period_start(
    event: dict[str, Any],
    model: dict[str, Any],
    period: int,
) -> float:
    depreciation_model = model.get("renovation_asset_depreciation", {})
    default_life = float(depreciation_model.get("useful_life_years", 20.0))
    default_residual_pct = float(depreciation_model.get("residual_value_pct", 5.0))
    completion_index = renovation_event_completion_index(event, model)
    if completion_index > period:
        return 0.0
    capex = renovation_event_capex(event, model)
    useful_life = float(event.get("useful_life_years", default_life))
    residual_pct = float(event.get("residual_value_pct", default_residual_pct))
    if capex <= 0 or useful_life <= 0:
        return 0.0
    elapsed = clamp(
        period_index_to_year_fraction(period) - period_index_to_year_fraction(completion_index),
        0.0,
        useful_life,
    )
    residual = capex * residual_pct / 100.0
    annual_depreciation = (capex - residual) / useful_life
    return max(capex - annual_depreciation * elapsed, residual)


def disposed_renovation_event_ids_for_period(
    renovation_events: list[dict[str, Any]],
    renovation_model: dict[str, Any],
    rebuild_events: list[dict[str, Any]],
    rebuild_model: dict[str, Any],
    period: int,
) -> set[str]:
    disposed_ids: set[str] = set()
    for renovation_event in renovation_events:
        event_id = str(renovation_event.get("event_id", ""))
        slot_id = str(renovation_event.get("slot_id", ""))
        if not event_id or not slot_id:
            continue
        renovation_completion = renovation_event_completion_index(renovation_event, renovation_model)
        if renovation_completion > period:
            continue
        for rebuild_event in rebuild_events:
            if str(rebuild_event.get("slot_id", "")) != slot_id:
                continue
            rebuild_start = rebuild_event_start_index(rebuild_event)
            if renovation_completion <= rebuild_start <= period:
                disposed_ids.add(event_id)
                break
    return disposed_ids


def rebuild_old_renovation_asset_writeoff(
    started_events: list[dict[str, Any]],
    renovation_events: list[dict[str, Any]],
    renovation_model: dict[str, Any],
    rebuild_events: list[dict[str, Any]],
    rebuild_model: dict[str, Any],
    year: int,
    quarter: str,
) -> float:
    period = quarter_period_index(year, quarter)
    writeoff = 0.0
    started_slots = {str(event.get("slot_id", "")) for event in started_events if event.get("slot_id")}
    for event in renovation_events:
        slot_id = str(event.get("slot_id", ""))
        if slot_id not in started_slots:
            continue
        completion = renovation_event_completion_index(event, renovation_model)
        if completion > period:
            continue
        already_disposed = any(
            str(rebuild_event.get("slot_id", "")) == slot_id
            and completion <= rebuild_event_start_index(rebuild_event) < period
            for rebuild_event in rebuild_events
        )
        if already_disposed:
            continue
        writeoff += renovation_event_book_value_at_period_start(event, renovation_model, period)
    return writeoff


def rebuild_event_book_value_at_period_start(
    event: dict[str, Any],
    model: dict[str, Any],
    period: int,
) -> float:
    capex = rebuild_event_asset_capex(event, model)
    depreciation_model = model.get("new_asset_depreciation", model.get("rebuild_asset_depreciation", {}))
    useful_life = float(event.get("useful_life_years", depreciation_model.get("useful_life_years", 40.0)))
    residual_pct = float(event.get("residual_value_pct", depreciation_model.get("residual_value_pct", 10.0)))
    completion = rebuild_event_completion_index(event, model)
    if capex <= 0 or useful_life <= 0 or period <= completion:
        return capex if period <= completion else 0.0
    elapsed_years = max(0.0, period_index_to_year_fraction(period) - period_index_to_year_fraction(completion))
    residual = capex * residual_pct / 100.0
    return max(residual, capex - (capex - residual) * min(elapsed_years / useful_life, 1.0))


def disposed_rebuild_event_ids_for_period(
    rebuild_events: list[dict[str, Any]],
    rebuild_model: dict[str, Any],
    period: int,
) -> set[str]:
    disposed: set[str] = set()
    for event in rebuild_events:
        event_id = str(event.get("event_id", ""))
        completion = rebuild_event_completion_index(event, rebuild_model)
        if not event_id or completion > period:
            continue
        if any(
            str(later.get("slot_id", "")) == str(event.get("slot_id", ""))
            and completion <= rebuild_event_start_index(later) <= period
            and str(later.get("event_id", "")) != event_id
            for later in rebuild_events
        ):
            disposed.add(event_id)
    return disposed


def rebuild_old_rebuild_asset_writeoff(
    started_events: list[dict[str, Any]],
    rebuild_events: list[dict[str, Any]],
    rebuild_model: dict[str, Any],
    year: int,
    quarter: str,
) -> float:
    period = quarter_period_index(year, quarter)
    started_ids = {str(event.get("event_id", "")) for event in started_events}
    writeoff = 0.0
    for event in rebuild_events:
        event_id = str(event.get("event_id", ""))
        if not event_id or event_id in started_ids:
            continue
        completion = rebuild_event_completion_index(event, rebuild_model)
        if completion > period:
            continue
        if any(
            str(later.get("slot_id", "")) == str(event.get("slot_id", ""))
            and str(later.get("event_id", "")) in started_ids
            and completion <= rebuild_event_start_index(later) == period
            for later in rebuild_events
        ):
            writeoff += rebuild_event_book_value_at_period_start(event, rebuild_model, period)
    return writeoff


def rebuild_asset_profile(
    events: list[dict[str, Any]],
    model: dict[str, Any],
    year: int,
    quarter: str,
    disposed_event_ids: set[str] | None = None,
) -> dict[str, float | str]:
    period = quarter_period_index(year, quarter)
    depreciation_model = model.get("new_asset_depreciation", model.get("rebuild_asset_depreciation", {}))
    default_life = float(depreciation_model.get("useful_life_years", 40.0))
    default_residual_pct = float(depreciation_model.get("residual_value_pct", 10.0))
    active_events_now = active_rebuild_events(events, model, year, quarter)
    disposed_event_ids = disposed_event_ids or set()
    completed_events_now = [
        event for event in completed_rebuild_events(events, model, year, quarter)
        if str(event.get("event_id", "")) not in disposed_event_ids
    ]
    started_events_now = started_rebuild_events(events, model, year, quarter)

    capex_outlay = 0.0
    demolition_expense = 0.0
    construction_in_progress = 0.0
    for event in active_events_now:
        capex = rebuild_event_asset_capex(event, model)
        demolition = rebuild_event_demolition_expense(event, model)
        duration = rebuild_event_duration_quarters(event, model)
        elapsed_quarters = period - rebuild_event_start_index(event) + 1
        capex_outlay += capex / duration
        demolition_expense += demolition / duration
        construction_in_progress += capex * clamp(elapsed_quarters / duration, 0.0, 1.0)

    original = 0.0
    residual_floor = 0.0
    accumulated = 0.0
    period_depreciation = 0.0
    book_value = 0.0
    for event in completed_events_now:
        capex = rebuild_event_asset_capex(event, model)
        useful_life = float(event.get("useful_life_years", default_life))
        residual_pct = float(event.get("residual_value_pct", default_residual_pct))
        if capex <= 0 or useful_life <= 0:
            continue
        start_fraction = period_index_to_year_fraction(rebuild_event_completion_index(event, model))
        target_fraction = period_index_to_year_fraction(period)
        elapsed_before_period = clamp(target_fraction - start_fraction, 0.0, useful_life)
        residual = capex * residual_pct / 100.0
        annual_depreciation = (capex - residual) / useful_life
        depreciates_this_period = elapsed_before_period < useful_life
        elapsed_at_period_end = clamp(
            elapsed_before_period + (0.25 if depreciates_this_period else 0.0),
            0.0,
            useful_life,
        )
        event_period_depreciation = annual_depreciation * 0.25 if depreciates_this_period else 0.0
        event_accumulated = annual_depreciation * elapsed_at_period_end
        original += capex
        residual_floor += residual
        accumulated += event_accumulated
        period_depreciation += event_period_depreciation
        book_value += max(capex - event_accumulated, residual)

    return {
        "active_event_ids": ";".join(str(event.get("event_id", "")) for event in active_events_now if event.get("event_id")),
        "started_event_ids": ";".join(str(event.get("event_id", "")) for event in started_events_now if event.get("event_id")),
        "started_slot_ids": ";".join(str(event.get("slot_id", "")) for event in started_events_now if event.get("slot_id")),
        "completed_event_ids": ";".join(str(event.get("event_id", "")) for event in completed_events_now if event.get("event_id")),
        "in_service_periods": ";".join(
            period_index_label(rebuild_event_completion_index(event, model)) for event in completed_events_now
        ),
        "quarter_capex_outlay": capex_outlay,
        "quarter_demolition_expense": demolition_expense,
        "construction_in_progress": construction_in_progress,
        "asset_original": original,
        "asset_residual_floor": residual_floor,
        "asset_accumulated_depreciation": accumulated,
        "asset_book_value": book_value,
        "asset_period_depreciation": period_depreciation,
    }


def effective_facility_slot_items(
    active_slots: str,
    active_rebuilds: list[dict[str, Any]],
    completed_rebuilds: list[dict[str, Any]],
    rebuild_model: dict[str, Any],
    completed_constructions: list[dict[str, Any]] | None = None,
    construction_model: dict[str, Any] | None = None,
) -> list[tuple[str, str]]:
    active_rebuild_slot_ids = {str(event.get("slot_id", "")) for event in active_rebuilds if event.get("slot_id")}
    completed_by_slot: dict[str, dict[str, Any]] = {}
    for event in sorted(completed_rebuilds, key=lambda item: rebuild_event_completion_index(item, rebuild_model)):
        slot_id = str(event.get("slot_id", ""))
        if slot_id:
            completed_by_slot[slot_id] = event

    effective_items: list[tuple[str, str]] = []
    for slot_id, size in active_facility_slot_items(active_slots):
        if slot_id in active_rebuild_slot_ids:
            continue
        completed_event = completed_by_slot.get(slot_id)
        effective_size = rebuild_event_target_size(completed_event) if completed_event else size
        if effective_size and effective_size != "empty":
            effective_items.append((slot_id, effective_size))
    known_slot_ids = {slot_id for slot_id, _ in effective_items}
    for event in sorted(
        completed_constructions or [],
        key=lambda item: construction_event_completion_index(item, construction_model or {}),
    ):
        slot_id = str(event.get("slot_id", ""))
        size = construction_event_size(event)
        latest_rebuild = completed_by_slot.get(slot_id)
        if (
            latest_rebuild
            and rebuild_event_target_size(latest_rebuild) == "empty"
            and rebuild_event_completion_index(latest_rebuild, rebuild_model)
            >= construction_event_completion_index(event, construction_model or {})
        ):
            continue
        if slot_id and slot_id not in known_slot_ids and size and size != "empty":
            effective_items.append((slot_id, size))
            known_slot_ids.add(slot_id)
    return effective_items


def slot_effective_maintenance_age_years(
    slot_id: str,
    year: int,
    quarter: str,
    slot_model: dict[str, Any],
    renovation_model: dict[str, Any],
    renovation_events: list[dict[str, Any]],
    rebuild_model: dict[str, Any] | None = None,
    rebuild_events: list[dict[str, Any]] | None = None,
    construction_model: dict[str, Any] | None = None,
    construction_events: list[dict[str, Any]] | None = None,
) -> float | None:
    open_years = slot_model.get("slot_open_years", {})
    open_year = open_years.get(slot_id)
    target_index = quarter_period_index(year, quarter)
    anchor_fraction = float(open_year) if open_year is not None else 0.0
    effective_age_at_anchor = 0.0
    rebuild_model = rebuild_model or {}
    rebuild_events = rebuild_events or []
    construction_model = construction_model or {}
    construction_events = construction_events or []
    completed_constructions = [
        event
        for event in construction_events
        if str(event.get("slot_id", "")) == slot_id
        and construction_event_completion_index(event, construction_model) <= target_index
    ]
    if completed_constructions:
        latest_construction = max(
            completed_constructions,
            key=lambda event: construction_event_completion_index(event, construction_model),
        )
        anchor_fraction = period_index_to_year_fraction(
            construction_event_completion_index(latest_construction, construction_model)
        )
        effective_age_at_anchor = 0.0
    elif open_year is None:
        return None
    completed_rebuilds = [
        event
        for event in rebuild_events
        if str(event.get("slot_id", "")) == slot_id
        and rebuild_event_completion_index(event, rebuild_model) <= target_index
    ]
    if completed_rebuilds:
        latest_rebuild = max(
            completed_rebuilds,
            key=lambda event: rebuild_event_completion_index(event, rebuild_model),
        )
        anchor_fraction = period_index_to_year_fraction(rebuild_event_completion_index(latest_rebuild, rebuild_model))
        effective_age_at_anchor = 0.0

    retention_ratio = float(renovation_model.get("maintenance_age_retention_ratio", 1.0))
    minimum_age = float(renovation_model.get("minimum_effective_maintenance_age_years", 0.0))
    slot_events = [
        event
        for event in renovation_events
        if str(event.get("slot_id", "")) == slot_id
        and renovation_event_completion_index(event, renovation_model) <= target_index
        and period_index_to_year_fraction(renovation_event_completion_index(event, renovation_model)) >= anchor_fraction
    ]
    for event in sorted(slot_events, key=lambda item: renovation_event_completion_index(item, renovation_model)):
        completion_fraction = period_index_to_year_fraction(renovation_event_completion_index(event, renovation_model))
        age_at_completion = effective_age_at_anchor + max(0.0, completion_fraction - anchor_fraction)
        effective_age_at_anchor = max(minimum_age, age_at_completion * retention_ratio)
        anchor_fraction = completion_fraction
    target_fraction = period_index_to_year_fraction(target_index)
    return effective_age_at_anchor + max(0.0, target_fraction - anchor_fraction)


def slot_age_multiplier(
    slot_id: str,
    year: int,
    model: dict[str, Any],
    quarter: str = "Q1",
    renovation_model: dict[str, Any] | None = None,
    renovation_events: list[dict[str, Any]] | None = None,
    rebuild_model: dict[str, Any] | None = None,
    rebuild_events: list[dict[str, Any]] | None = None,
    construction_model: dict[str, Any] | None = None,
    construction_events: list[dict[str, Any]] | None = None,
) -> float:
    effective_age = slot_effective_maintenance_age_years(
        slot_id,
        year,
        quarter,
        model,
        renovation_model or {},
        renovation_events or [],
        rebuild_model or {},
        rebuild_events or [],
        construction_model or {},
        construction_events or [],
    )
    if effective_age is None:
        return 1.0
    return interpolate_curve(
        list(model.get("age_curve_points", [])),
        max(0.0, effective_age),
        "age_year",
        "multiplier",
        1.0,
    )


def sigmoid(value: float) -> float:
    bounded = clamp(value, -60.0, 60.0)
    return 1.0 / (1.0 + math.exp(-bounded))


def perceived_quality_age_score(effective_age_years: float, model: dict[str, Any]) -> float:
    age_model = model.get("age_score", {})
    max_score = float(age_model.get("max_score", 6.0))
    score_span = float(age_model.get("score_span", 18.0))
    midpoint = float(age_model.get("midpoint_years", 24.0))
    softness = float(age_model.get("softness_years", 8.0))
    if softness <= 0:
        softness = 8.0
    return max_score - score_span * sigmoid((effective_age_years - midpoint) / softness)


def perceived_quality_capacity_score(
    design_utilization_pct: float,
    max_utilization_pct: float,
    model: dict[str, Any],
) -> float:
    capacity = model.get("capacity_pressure_score", {})
    bonus_start = float(capacity.get("comfort_bonus_start_design_utilization_pct", 100.0))
    full_bonus_at = float(capacity.get("full_comfort_bonus_design_utilization_pct", 75.0))
    max_bonus = float(capacity.get("max_comfort_bonus_score", 3.0))
    comfort_bonus = 0.0
    if design_utilization_pct < bonus_start and bonus_start > full_bonus_at:
        comfort_factor = clamp(
            (bonus_start - design_utilization_pct) / (bonus_start - full_bonus_at),
            0.0,
            1.0,
        )
        comfort_bonus = max_bonus * comfort_factor

    design_start = float(capacity.get("design_penalty_start_utilization_pct", 100.0))
    design_full = float(capacity.get("design_penalty_full_utilization_pct", 135.0))
    design_max_penalty = float(capacity.get("max_design_penalty_score", 14.0))
    design_power = float(capacity.get("design_penalty_power", 1.25))
    design_penalty = 0.0
    if design_utilization_pct > design_start and design_full > design_start:
        design_factor = clamp(
            (design_utilization_pct - design_start) / (design_full - design_start),
            0.0,
            1.0,
        )
        design_penalty = design_max_penalty * (design_factor**design_power)

    hard_start = float(capacity.get("hard_penalty_start_max_utilization_pct", 88.0))
    hard_full = float(capacity.get("hard_penalty_full_max_utilization_pct", 105.0))
    hard_max_penalty = float(capacity.get("max_hard_penalty_score", 18.0))
    hard_power = float(capacity.get("hard_penalty_power", 1.15))
    hard_penalty = 0.0
    if max_utilization_pct > hard_start and hard_full > hard_start:
        hard_factor = clamp(
            (max_utilization_pct - hard_start) / (hard_full - hard_start),
            0.0,
            1.0,
        )
        hard_penalty = hard_max_penalty * (hard_factor**hard_power)

    score = comfort_bonus - max(design_penalty, hard_penalty)
    return clamp(
        score,
        float(capacity.get("min_capacity_score", -22.0)),
        float(capacity.get("max_capacity_score", 3.0)),
    )


def active_slot_renovation_capacity_multiplier(
    slot_id: str,
    active_renovations: list[dict[str, Any]],
    renovation_model: dict[str, Any],
) -> float:
    multiplier = 1.0
    for event in active_renovations:
        if str(event.get("slot_id", "")) != slot_id:
            continue
        multiplier = min(multiplier, renovation_event_capacity_multiplier(event, renovation_model))
    return multiplier


def active_slot_renovation_quality_disruption_score(
    slot_id: str,
    active_renovations: list[dict[str, Any]],
    quality_model: dict[str, Any],
) -> float:
    default_score = float(quality_model.get("renovation_construction_disruption_score", -5.0))
    total_score = 0.0
    for event in active_renovations:
        if str(event.get("slot_id", "")) != slot_id:
            continue
        total_score += float(event.get("perceived_quality_disruption_score", default_score))
    return total_score


def city_airport_perceived_quality_profile(
    annual: dict[str, str],
    quarter: str,
    quarter_served: float,
    quality_model: dict[str, Any],
    facility_sizes: dict[str, dict[str, Any]],
    slot_fixed_model: dict[str, Any],
    renovation_model: dict[str, Any],
    renovation_events: list[dict[str, Any]],
    active_renovations: list[dict[str, Any]],
    slot_items_override: list[tuple[str, str]] | None = None,
    rebuild_model: dict[str, Any] | None = None,
    rebuild_events: list[dict[str, Any]] | None = None,
    construction_model: dict[str, Any] | None = None,
    construction_events: list[dict[str, Any]] | None = None,
) -> dict[str, float | str]:
    model_version = str(quality_model.get("model_version", "city-airport-perceived-quality-v0"))
    baseline = float(quality_model.get("baseline_index", 100.0))
    size_scores = quality_model.get("facility_size_scores", {})
    slot_min = float(quality_model.get("min_slot_quality_index", 60.0))
    slot_max = float(quality_model.get("max_slot_quality_index", 140.0))
    city_min = float(quality_model.get("min_city_quality_index", 60.0))
    city_max = float(quality_model.get("max_city_quality_index", 140.0))
    default_age = float(quality_model.get("default_effective_age_years", 20.0))

    year = int(as_float(annual, "year"))
    slot_items = (
        slot_items_override
        if slot_items_override is not None
        else active_facility_slot_items(str(annual.get("active_airport_facility_slots") or ""))
    )
    slot_capacities: list[dict[str, float | str]] = []
    total_design_capacity = 0.0
    for slot_id, size in slot_items:
        spec = facility_sizes.get(size, {})
        design_capacity = float(spec.get("design_capacity_million", 0.0))
        max_capacity = float(spec.get("max_capacity_million", 0.0))
        renovation_multiplier = active_slot_renovation_capacity_multiplier(
            slot_id,
            active_renovations,
            renovation_model,
        )
        available_design = max(0.0, design_capacity * renovation_multiplier)
        available_max = max(0.0, max_capacity * renovation_multiplier)
        total_design_capacity += available_design
        slot_capacities.append(
            {
                "slot_id": slot_id,
                "size": size,
                "available_design": available_design,
                "available_max": available_max,
            }
        )

    if total_design_capacity <= 0:
        return {
            "model_version": model_version,
            "quality_index": baseline,
            "size_score": 0.0,
            "age_score": 0.0,
            "capacity_score": 0.0,
            "construction_disruption_score": 0.0,
            "active_slot_count": 0.0,
        }

    weighted_quality = 0.0
    weighted_size_score = 0.0
    weighted_age_score = 0.0
    weighted_capacity_score = 0.0
    weighted_disruption_score = 0.0
    total_weight = 0.0

    for slot in slot_capacities:
        slot_id = str(slot["slot_id"])
        size = str(slot["size"])
        available_design = float(slot["available_design"])
        available_max = float(slot["available_max"])
        if available_design <= 0:
            continue
        slot_quarter_served = quarter_served * available_design / total_design_capacity
        quarter_design_capacity = available_design / 4.0
        quarter_max_capacity = available_max / 4.0
        design_utilization_pct = (
            slot_quarter_served / quarter_design_capacity * 100.0
            if quarter_design_capacity > 0
            else 0.0
        )
        max_utilization_pct = (
            slot_quarter_served / quarter_max_capacity * 100.0
            if quarter_max_capacity > 0
            else 0.0
        )
        size_score = float(size_scores.get(size, 0.0))
        effective_age = slot_effective_maintenance_age_years(
            slot_id,
            year,
            quarter,
            slot_fixed_model,
            renovation_model,
            renovation_events,
            rebuild_model or {},
            rebuild_events or [],
            construction_model or {},
            construction_events or [],
        )
        age_score = perceived_quality_age_score(
            default_age if effective_age is None else max(0.0, effective_age),
            quality_model,
        )
        capacity_score = perceived_quality_capacity_score(
            design_utilization_pct,
            max_utilization_pct,
            quality_model,
        )
        disruption_score = active_slot_renovation_quality_disruption_score(
            slot_id,
            active_renovations,
            quality_model,
        )
        slot_quality = clamp(
            baseline + size_score + age_score + capacity_score + disruption_score,
            slot_min,
            slot_max,
        )
        weight = slot_quarter_served if quarter_served > 0 else available_design
        weighted_quality += slot_quality * weight
        weighted_size_score += size_score * weight
        weighted_age_score += age_score * weight
        weighted_capacity_score += capacity_score * weight
        weighted_disruption_score += disruption_score * weight
        total_weight += weight

    if total_weight <= 0:
        return {
            "model_version": model_version,
            "quality_index": baseline,
            "size_score": 0.0,
            "age_score": 0.0,
            "capacity_score": 0.0,
            "construction_disruption_score": 0.0,
            "active_slot_count": float(len(slot_capacities)),
        }

    return {
        "model_version": model_version,
        "quality_index": clamp(weighted_quality / total_weight, city_min, city_max),
        "size_score": weighted_size_score / total_weight,
        "age_score": weighted_age_score / total_weight,
        "capacity_score": weighted_capacity_score / total_weight,
        "construction_disruption_score": weighted_disruption_score / total_weight,
        "active_slot_count": float(len(slot_capacities)),
    }


def perceived_quality_commercial_multiplier(
    quality_index: float,
    quality_model: dict[str, Any],
    segment: str,
) -> float:
    response = quality_model.get("commercial_revenue_response", {})
    segment_response = response.get(segment, {})
    baseline = float(response.get("baseline_index", quality_model.get("baseline_index", 100.0)))
    scale = float(response.get("quality_scale", 18.0))
    if scale <= 0:
        scale = 18.0
    sensitivity = float(segment_response.get("sensitivity", 0.0))
    multiplier = 1.0 + sensitivity * math.tanh((quality_index - baseline) / scale)
    return clamp(
        multiplier,
        float(segment_response.get("min_multiplier", 1.0 - abs(sensitivity))),
        float(segment_response.get("max_multiplier", 1.0 + abs(sensitivity))),
    )


def weighted_index_multiplier(row: dict[str, str], macro: dict[str, Any]) -> float:
    weights = macro.get("weights", {})
    if not weights:
        return 1.0
    baseline_index = float(macro.get("baseline_index", 50.0))
    weighted_index = 0.0
    total_weight = 0.0
    for field, weight in weights.items():
        field_name = str(field)
        field_weight = float(weight)
        weighted_index += as_float(row, field_name, baseline_index) * field_weight
        total_weight += abs(field_weight)
    if total_weight <= 0:
        return 1.0
    weighted_index /= total_weight
    sensitivity = float(macro.get("sensitivity", 0.24))
    multiplier = 1.0 + (weighted_index - baseline_index) / 100.0 * sensitivity
    return clamp(
        multiplier,
        float(macro.get("min_multiplier", 0.88)),
        float(macro.get("max_multiplier", 1.22)),
    )


def field_pressure_multiplier(row: dict[str, str], model: dict[str, Any]) -> float:
    fields = model.get("fields", {})
    if not fields:
        return 1.0
    weighted_gap = 0.0
    total_weight = 0.0
    for field, spec in fields.items():
        if not isinstance(spec, dict):
            continue
        weight = float(spec.get("weight", 0.0))
        if weight == 0:
            continue
        baseline = float(spec.get("baseline", 50.0))
        scale = float(spec.get("scale", 25.0))
        if scale <= 0:
            scale = 25.0
        direction = float(spec.get("direction", 1.0))
        value = as_float(row, str(field), baseline)
        weighted_gap += ((value - baseline) / scale) * direction * weight
        total_weight += abs(weight)
    if total_weight <= 0:
        return 1.0
    normalized_gap = weighted_gap / total_weight
    multiplier = 1.0 + normalized_gap * float(model.get("sensitivity", 0.08))
    return clamp(
        multiplier,
        float(model.get("min_multiplier", 0.95)),
        float(model.get("max_multiplier", 1.08)),
    )


def curve_multiplier(row: dict[str, str], model: dict[str, Any], default_field: str) -> float:
    field = str(model.get("field", default_field))
    points = list(model.get("curve_points", []))
    if not points:
        return 1.0
    value = as_float(row, field, float(model.get("baseline_index", 100.0)))
    multiplier = interpolate_curve(
        points,
        value,
        str(model.get("x_key", "index")),
        str(model.get("y_key", "multiplier")),
        1.0,
    )
    return clamp(
        multiplier,
        float(model.get("min_multiplier", 0.0)),
        float(model.get("max_multiplier", 2.0)),
    )


def commercial_market_cycle_multiplier(row: dict[str, str], quarter: str, model: dict[str, Any]) -> float:
    cycle = model.get("market_cycle", {})
    if not isinstance(cycle, dict) or not bool(cycle.get("enabled", False)):
        return 1.0

    model_version = str(cycle.get("model_version", "commercial-market-cycle-v0"))
    seed = int(as_float(row, "seed", 0.0))
    year_index = as_float(row, "year_index", 0.0)
    quarter_index = QUARTERS.index(quarter) if quarter in QUARTERS else 0
    elapsed_years = year_index + quarter_index / 4.0

    tau = 2.0 * math.pi
    primary_period = max(float(cycle.get("cycle_period_years", 6.5)), 1.0)
    short_period = max(float(cycle.get("short_cycle_period_years", 2.25)), 0.75)
    primary_phase = stable_unit_float(seed, model_version, "primary-phase") * tau
    short_phase = stable_unit_float(seed, model_version, "short-phase") * tau
    primary_cycle = math.sin(elapsed_years / primary_period * tau + primary_phase)
    short_cycle = math.sin(elapsed_years / short_period * tau + short_phase)

    multiplier = (
        1.0
        + float(cycle.get("cycle_amplitude", 0.0)) * primary_cycle
        + float(cycle.get("short_cycle_amplitude", 0.0)) * short_cycle
    )
    regime_bias = (stable_unit_float(seed, model_version, "regime-bias") * 2.0 - 1.0) * float(
        cycle.get("regime_bias_amplitude", 0.0)
    )
    multiplier += regime_bias

    shock_amplitude = float(cycle.get("quarter_shock_amplitude", 0.0))
    if shock_amplitude:
        year = int(as_float(row, "year", 0.0))
        local_shock = stable_unit_float(seed, model_version, year, quarter, "quarter-shock") * 2.0 - 1.0
        multiplier += shock_amplitude * local_shock

    quarter_multipliers = cycle.get("quarter_multipliers", {})
    if isinstance(quarter_multipliers, dict):
        multiplier *= float(quarter_multipliers.get(quarter, 1.0))

    environment_multiplier = field_pressure_multiplier(row, cycle.get("environment", {}))
    multiplier *= environment_multiplier

    return clamp(
        multiplier,
        float(cycle.get("min_multiplier", 0.70)),
        float(cycle.get("max_multiplier", 1.35)),
    )


def aeronautical_capacity_pricing_multiplier(design_utilization_pct: float, model: dict[str, Any]) -> float:
    weak_start = float(model.get("weak_pricing_below_design_utilization_pct", 70.0))
    full_weak = float(model.get("full_weak_pricing_design_utilization_pct", 45.0))
    max_weak_discount = float(model.get("max_weak_pricing_discount_pct", 2.5)) / 100.0
    tight_start = float(model.get("tight_pricing_start_design_utilization_pct", 88.0))
    full_tight = float(model.get("full_tight_pricing_design_utilization_pct", 112.0))
    max_tight_premium = float(model.get("max_tight_pricing_premium_pct", 3.2)) / 100.0

    if design_utilization_pct < weak_start and weak_start > full_weak:
        weak_factor = clamp((weak_start - design_utilization_pct) / (weak_start - full_weak), 0.0, 1.0)
        return 1.0 - max_weak_discount * weak_factor
    if design_utilization_pct > tight_start and full_tight > tight_start:
        tight_factor = clamp((design_utilization_pct - tight_start) / (full_tight - tight_start), 0.0, 1.0)
        return 1.0 + max_tight_premium * tight_factor
    return 1.0


def aeronautical_crowding_revenue_multiplier(
    design_utilization_pct: float,
    max_utilization_pct: float,
    model: dict[str, Any],
) -> float:
    start = float(model.get("service_quality_penalty_start_design_utilization_pct", 108.0))
    full = float(model.get("full_service_quality_penalty_design_utilization_pct", 138.0))
    max_penalty = float(model.get("max_service_quality_revenue_penalty_pct", 5.0)) / 100.0
    over_max_full = float(model.get("over_max_penalty_full_max_utilization_pct", 118.0))
    over_max_penalty = float(model.get("over_max_revenue_penalty_pct", 3.0)) / 100.0
    penalty = 0.0
    if design_utilization_pct > start and full > start:
        penalty += max_penalty * clamp((design_utilization_pct - start) / (full - start), 0.0, 1.0)
    if max_utilization_pct > 100.0 and over_max_full > 100.0:
        penalty += over_max_penalty * clamp((max_utilization_pct - 100.0) / (over_max_full - 100.0), 0.0, 1.0)
    return clamp(1.0 - penalty, float(model.get("min_multiplier", 0.90)), 1.0)


def macro_cost_pressure_multiplier(row: dict[str, str], model: dict[str, Any]) -> float:
    return weighted_index_multiplier(row, model.get("macro_cost_pressure", {}))


def passenger_load_pressure_multiplier(design_utilization_pct: float, config: dict[str, Any]) -> float:
    load_pressure = config.get("load_pressure", {})
    start_pct = float(load_pressure.get("start_design_utilization_pct", 78.0))
    full_pct = float(load_pressure.get("full_design_utilization_pct", 118.0))
    min_multiplier = float(load_pressure.get("min_multiplier", 1.0))
    max_multiplier = float(load_pressure.get("max_multiplier", 1.08))
    if full_pct <= start_pct:
        return min_multiplier
    pressure = clamp((design_utilization_pct - start_pct) / (full_pct - start_pct), 0.0, 1.0)
    return min_multiplier + pressure * (max_multiplier - min_multiplier)


def self_operated_fixed_cost_profile(
    base_annual: float,
    annual: dict[str, str],
    quarter: str,
    design_utilization_pct: float,
    model: dict[str, Any],
) -> dict[str, float | str]:
    quarter_multipliers = model.get("quarter_cost_multipliers", {})
    intensity_multiplier = float(model.get("commercial_intensity_multiplier", 1.0))
    city_multiplier = float(model.get("city_commercial_complexity_multiplier", 1.0))
    macro_multiplier = weighted_index_multiplier(annual, model.get("macro_cost_pressure", {}))
    quarter_multiplier = float(quarter_multipliers.get(quarter, 1.0))
    load_multiplier = passenger_load_pressure_multiplier(design_utilization_pct, model)
    quarter_fixed_cost = (
        base_annual
        * intensity_multiplier
        * city_multiplier
        * macro_multiplier
        * quarter_multiplier
        * load_multiplier
        / 4.0
    )
    return {
        "model_version": str(model.get("model_version", "self-operated-commercial-fixed-cost-v0")),
        "base_annual": base_annual,
        "intensity_multiplier": intensity_multiplier,
        "city_multiplier": city_multiplier,
        "macro_multiplier": macro_multiplier,
        "quarter_multiplier": quarter_multiplier,
        "load_multiplier": load_multiplier,
        "quarter_fixed_cost": quarter_fixed_cost,
    }


def self_operated_revenue_profile(
    quarter_served: float,
    food_retail_propensity_index: float,
    annual: dict[str, str],
    quarter: str,
    crowding_index: float,
    fallback_base_revenue_per_passenger: float,
    fallback_efficiency: float,
    fallback_crowding_penalty_pct: float,
    model: dict[str, Any],
    quality_multiplier: float = 1.0,
) -> dict[str, float | str]:
    base_revenue = float(model.get("base_revenue_per_passenger_cny", fallback_base_revenue_per_passenger))
    efficiency = float(model.get("self_operated_efficiency", fallback_efficiency))
    propensity = model.get("propensity_response", {})
    baseline_index = float(propensity.get("baseline_index", 100.0))
    sensitivity = float(propensity.get("sensitivity", 1.0))
    propensity_multiplier = 1.0 + (food_retail_propensity_index - baseline_index) / 100.0 * sensitivity
    propensity_multiplier = clamp(
        propensity_multiplier,
        float(propensity.get("min_multiplier", 0.75)),
        float(propensity.get("max_multiplier", 1.45)),
    )
    quarter_multipliers = model.get("quarter_revenue_multipliers", {})
    quarter_multiplier = float(quarter_multipliers.get(quarter, 1.0))
    macro_multiplier = field_pressure_multiplier(annual, model.get("macro_demand_environment", {}))
    crowding_penalty_pct = float(model.get("max_crowding_revenue_penalty_pct", fallback_crowding_penalty_pct))
    min_crowding_multiplier = float(model.get("min_crowding_revenue_multiplier", 0.70))
    crowding_multiplier = 1.0 - crowding_penalty_pct / 100.0 * crowding_index / 100.0
    crowding_multiplier = clamp(crowding_multiplier, min_crowding_multiplier, 1.0)
    revenue = (
        quarter_served
        * base_revenue
        * propensity_multiplier
        * quarter_multiplier
        * macro_multiplier
        * efficiency
        * crowding_multiplier
        * quality_multiplier
    )
    return {
        "model_version": str(model.get("model_version", "self-operated-commercial-revenue-v0")),
        "base_revenue": base_revenue,
        "efficiency": efficiency,
        "propensity_multiplier": propensity_multiplier,
        "quarter_multiplier": quarter_multiplier,
        "macro_multiplier": macro_multiplier,
        "crowding_multiplier": crowding_multiplier,
        "quality_multiplier": quality_multiplier,
        "revenue": revenue,
    }


def self_operated_passenger_service_cost_profile(
    quarter_served: float,
    food_retail_propensity_index: float,
    annual: dict[str, str],
    quarter: str,
    design_utilization_pct: float,
    fallback_base_cost_per_passenger: float,
    model: dict[str, Any],
) -> dict[str, float | str]:
    base_cost = float(model.get("base_cost_per_passenger_cny", fallback_base_cost_per_passenger))
    consumption = model.get("consumption_intensity", {})
    baseline_index = float(consumption.get("baseline_index", 100.0))
    sensitivity = float(consumption.get("sensitivity", 0.0))
    consumption_multiplier = 1.0 + (food_retail_propensity_index - baseline_index) / 100.0 * sensitivity
    consumption_multiplier = clamp(
        consumption_multiplier,
        float(consumption.get("min_multiplier", 0.95)),
        float(consumption.get("max_multiplier", 1.08)),
    )
    quarter_multipliers = model.get("quarter_service_cost_multipliers", {})
    quarter_multiplier = float(quarter_multipliers.get(quarter, 1.0))
    macro_multiplier = weighted_index_multiplier(annual, model.get("macro_cost_pressure", {}))
    load_multiplier = passenger_load_pressure_multiplier(design_utilization_pct, model)
    service_cost = (
        quarter_served
        * base_cost
        * consumption_multiplier
        * quarter_multiplier
        * macro_multiplier
        * load_multiplier
    )
    return {
        "model_version": str(model.get("model_version", "self-operated-commercial-service-cost-v0")),
        "base_cost": base_cost,
        "consumption_multiplier": consumption_multiplier,
        "quarter_multiplier": quarter_multiplier,
        "macro_multiplier": macro_multiplier,
        "load_multiplier": load_multiplier,
        "service_cost": service_cost,
    }


def self_operated_sales_cost_profile(
    food_retail_revenue: float,
    annual: dict[str, str],
    model: dict[str, Any],
) -> dict[str, float | str]:
    base_ratio_pct = float(model.get("base_sales_cost_ratio_pct", 0.0))
    mix_multiplier = field_pressure_multiplier(annual, model.get("sales_mix_cost_pressure", {}))
    macro_multiplier = weighted_index_multiplier(annual, model.get("macro_cost_pressure", {}))
    ratio_pct = base_ratio_pct * mix_multiplier * macro_multiplier
    ratio_pct = clamp(
        ratio_pct,
        float(model.get("min_sales_cost_ratio_pct", 0.0)),
        float(model.get("max_sales_cost_ratio_pct", 100.0)),
    )
    sales_cost = food_retail_revenue * ratio_pct / 100.0
    return {
        "model_version": str(model.get("model_version", "self-operated-commercial-sales-cost-v0")),
        "base_ratio_pct": base_ratio_pct,
        "mix_multiplier": mix_multiplier,
        "macro_multiplier": macro_multiplier,
        "ratio_pct": ratio_pct,
        "sales_cost": sales_cost,
    }


def congestion_adjustment_profile(
    quarter_components: dict[str, float],
    quarter_served: float,
    design_utilization_pct: float,
    over_max_passengers: float,
    quarter_max_capacity: float,
    config: dict[str, Any],
) -> dict[str, float | str]:
    model_version = str(config.get("model_version", "congestion-relief-adjustment-v0.2"))
    component_multiplier = weighted_average_by_component(
        quarter_components,
        config.get("component_crowding_weights", {}),
        1.0,
    )
    component_multiplier = clamp(
        component_multiplier,
        float(config.get("component_mix_multiplier_min", 0.94)),
        float(config.get("component_mix_multiplier_max", 1.12)),
    )

    relief_start = float(config.get("relief_start_design_utilization_pct", 72.0))
    full_relief = float(config.get("full_relief_design_utilization_pct", 45.0))
    max_relief = float(config.get("max_relief_per_passenger_cny", 5.0))
    congestion_start = float(config.get("congestion_start_design_utilization_pct", 100.0))
    full_pressure = float(config.get("full_design_pressure_utilization_pct", 130.0))
    full_pressure_cost = float(config.get("cost_per_passenger_at_full_design_pressure_cny", 26.0))
    design_power = float(config.get("design_pressure_power", 1.35))

    if design_utilization_pct < relief_start and relief_start > full_relief:
        relief_factor = clamp((relief_start - design_utilization_pct) / (relief_start - full_relief), 0.0, 1.0)
        design_adjustment_per_passenger = -max_relief * relief_factor
    elif design_utilization_pct > congestion_start and full_pressure > congestion_start:
        pressure_factor = clamp(
            (design_utilization_pct - congestion_start) / (full_pressure - congestion_start),
            0.0,
            1.0,
        )
        design_adjustment_per_passenger = full_pressure_cost * (pressure_factor**design_power)
    else:
        design_adjustment_per_passenger = 0.0

    design_adjustment = quarter_served * design_adjustment_per_passenger * component_multiplier
    over_max_ratio = over_max_passengers / quarter_max_capacity if quarter_max_capacity > 0 else 0.0
    over_max_multiplier = (1.0 + over_max_ratio) ** float(config.get("over_max_pressure_power", 1.1))
    over_max_pressure_cost = (
        over_max_passengers
        * float(config.get("over_max_pressure_cost_per_passenger_cny", 42.0))
        * component_multiplier
        * over_max_multiplier
    )

    return {
        "model_version": model_version,
        "component_multiplier": component_multiplier,
        "design_adjustment_per_passenger": design_adjustment_per_passenger,
        "design_adjustment": design_adjustment,
        "over_max_pressure_cost": over_max_pressure_cost,
        "total": design_adjustment + over_max_pressure_cost,
    }


def slot_fixed_cost_profile(
    annual: dict[str, str],
    config: dict[str, Any],
    quarter: str,
    renovation_data: dict[str, Any],
    slot_items_override: list[tuple[str, str]] | None = None,
    rebuild_data: dict[str, Any] | None = None,
    construction_data: dict[str, Any] | None = None,
) -> dict[str, float]:
    fixed_costs = config["facility_fixed_operating_cost_million_cny_per_year"]
    model = config.get("slot_fixed_operating_cost_model", {})
    renovation_model = renovation_data.get("model", {})
    renovation_events = renovation_data.get("events", [])
    rebuild_data = rebuild_data or {}
    rebuild_model = rebuild_data.get("model", {})
    rebuild_events = rebuild_data.get("events", [])
    construction_data = construction_data or {}
    construction_model = construction_data.get("model", {})
    construction_events = construction_data.get("events", [])
    year = int(as_float(annual, "year"))
    active_slots = str(annual.get("active_airport_facility_slots") or "")
    slot_items = slot_items_override if slot_items_override is not None else active_facility_slot_items(active_slots)
    base_annual = sum(float(fixed_costs.get(size, 0.0)) for _, size in slot_items)
    age_adjusted_annual = 0.0
    for slot_id, size in slot_items:
        base_cost = float(fixed_costs.get(size, 0.0))
        age_adjusted_annual += base_cost * slot_age_multiplier(
            slot_id,
            year,
            model,
            quarter,
            renovation_model,
            renovation_events,
            rebuild_model,
            rebuild_events,
            construction_model,
            construction_events,
        )

    age_multiplier = age_adjusted_annual / base_annual if base_annual > 0 else 1.0
    macro_multiplier = macro_cost_pressure_multiplier(annual, model)
    city_multiplier = float(model.get("city_complexity_multiplier", 1.0))
    quarter_multipliers = model.get("quarter_cost_multipliers", {})
    quarter_multiplier_sum = sum(float(quarter_multipliers.get(f"Q{index}", 1.0)) for index in range(1, 5))
    if quarter_multiplier_sum <= 0:
        quarter_multiplier_sum = 4.0
    annual_fixed_cost = age_adjusted_annual * macro_multiplier * city_multiplier * quarter_multiplier_sum / 4.0
    return {
        "base_annual": base_annual,
        "age_multiplier": age_multiplier,
        "macro_multiplier": macro_multiplier,
        "city_multiplier": city_multiplier,
        "age_adjusted_annual": age_adjusted_annual,
        "annual_fixed_cost": annual_fixed_cost,
    }


def weighted_average_by_component(
    quarter_components: dict[str, float],
    weights: dict[str, float],
    default: float = 1.0,
) -> float:
    passenger_total = sum(quarter_components.values())
    if passenger_total <= 0:
        return default
    weighted = sum(quarter_components[name] * float(weights.get(name, default)) for name in COMPONENTS)
    return weighted / passenger_total


def weighted_component_passengers(
    quarter_components: dict[str, float],
    weights: dict[str, float],
) -> float:
    return sum(quarter_components[name] * float(weights.get(name, 0.0)) for name in COMPONENTS)


def bounded_component_allocation(
    demand: dict[str, float],
    preferred: dict[str, float],
    total: float,
) -> dict[str, float]:
    """Reconcile a component mix to a total without exceeding component demand."""

    clean_demand = {name: max(0.0, demand.get(name, 0.0)) for name in COMPONENTS}
    allocation = {name: 0.0 for name in COMPONENTS}
    remaining = min(max(0.0, total), sum(clean_demand.values()))
    active = {name for name in COMPONENTS if clean_demand[name] > 1e-12}
    while remaining > 1e-12 and active:
        weights = {name: max(0.0, preferred.get(name, 0.0)) for name in active}
        weight_total = sum(weights.values())
        if weight_total <= 0.0:
            weights = {name: clean_demand[name] for name in active}
            weight_total = sum(weights.values()) or float(len(active))
        proposals = {name: remaining * weights[name] / weight_total for name in active}
        saturated = [
            name
            for name in active
            if proposals[name] >= clean_demand[name] - allocation[name] - 1e-12
        ]
        if not saturated:
            for name, value in proposals.items():
                allocation[name] += value
            break
        for name in saturated:
            available = max(0.0, clean_demand[name] - allocation[name])
            allocation[name] += available
            remaining -= available
            active.remove(name)
    return allocation


def blended_propensity(row: dict[str, str], weights: dict[str, float]) -> float:
    return sum(as_float(row, field, 100.0) * float(weight) for field, weight in weights.items())


def duty_free_sales_profile(
    quarter_components: dict[str, float],
    annual: dict[str, str],
    quarter: str,
    crowding_index: float,
    fallback_sales_per_weighted_passenger: float,
    fallback_weights: dict[str, float],
    fallback_international_exposure: float,
    fallback_capture_rate: float,
    model: dict[str, Any],
    quality_multiplier: float = 1.0,
) -> dict[str, float | str]:
    effective_weights = model.get("effective_passenger_weights", fallback_weights)
    effective_passengers = weighted_component_passengers(quarter_components, effective_weights)
    base_sales = float(
        model.get("base_sales_per_effective_passenger_cny", fallback_sales_per_weighted_passenger)
    )
    propensity_curve = model.get("propensity_curve", {})
    if propensity_curve:
        propensity_multiplier = curve_multiplier(
            annual,
            propensity_curve,
            "duty_free_propensity_index",
        )
    else:
        propensity_multiplier = as_float(annual, "duty_free_propensity_index", 100.0) / 100.0
    premium_multiplier = curve_multiplier(
        annual,
        model.get("premium_mix_curve", {}),
        "premium_passenger_propensity_index",
    )
    macro_multiplier = field_pressure_multiplier(annual, model.get("macro_demand_environment", {}))
    currency_multiplier = curve_multiplier(
        annual,
        model.get("currency_pressure_curve", {}),
        "input_currency_pressure_index",
    )
    market_cycle_multiplier = commercial_market_cycle_multiplier(annual, quarter, model)
    international_exposure = float(
        model.get("international_exposure_adjustment", fallback_international_exposure)
    )
    capture_rate = float(model.get("operator_commercial_capture_rate", fallback_capture_rate))
    crowding = model.get("crowding_penalty", {})
    max_penalty_pct = float(crowding.get("max_crowding_sales_penalty_pct", 14.0))
    min_multiplier = float(crowding.get("min_crowding_sales_multiplier", 0.78))
    crowding_multiplier = 1.0 - max_penalty_pct / 100.0 * crowding_index / 100.0
    crowding_multiplier = clamp(crowding_multiplier, min_multiplier, 1.0)
    sales = (
        effective_passengers
        * base_sales
        * propensity_multiplier
        * premium_multiplier
        * macro_multiplier
        * currency_multiplier
        * market_cycle_multiplier
        * international_exposure
        * capture_rate
        * crowding_multiplier
        * quality_multiplier
    )
    return {
        "model_version": str(model.get("model_version", "duty-free-sales-v0")),
        "base_sales": base_sales,
        "effective_passengers": effective_passengers,
        "propensity_multiplier": propensity_multiplier,
        "premium_multiplier": premium_multiplier,
        "macro_multiplier": macro_multiplier,
        "currency_multiplier": currency_multiplier,
        "market_cycle_multiplier": market_cycle_multiplier,
        "international_exposure": international_exposure,
        "capture_rate": capture_rate,
        "crowding_multiplier": crowding_multiplier,
        "quality_multiplier": quality_multiplier,
        "sales": sales,
    }


def luxury_sales_profile(
    quarter_components: dict[str, float],
    annual: dict[str, str],
    quarter: str,
    crowding_index: float,
    fallback_sales_per_weighted_passenger: float,
    fallback_weights: dict[str, float],
    fallback_capture_rate: float,
    model: dict[str, Any],
    quality_multiplier: float = 1.0,
) -> dict[str, float | str]:
    effective_weights = model.get("effective_passenger_weights", fallback_weights)
    effective_passengers = weighted_component_passengers(quarter_components, effective_weights)
    base_sales = float(
        model.get("base_sales_per_effective_passenger_cny", fallback_sales_per_weighted_passenger)
    )
    luxury_propensity_curve = model.get("luxury_propensity_curve", {})
    if luxury_propensity_curve:
        luxury_multiplier = curve_multiplier(
            annual,
            luxury_propensity_curve,
            "luxury_retail_propensity_index",
        )
    else:
        luxury_multiplier = as_float(annual, "luxury_retail_propensity_index", 100.0) / 100.0
    premium_multiplier = curve_multiplier(
        annual,
        model.get("premium_mix_curve", {}),
        "premium_passenger_propensity_index",
    )
    high_value_multiplier = curve_multiplier(
        annual,
        model.get("high_value_share_curve", {}),
        "premium_passenger_share_pct",
    )
    macro_multiplier = field_pressure_multiplier(annual, model.get("macro_wealth_environment", {}))
    currency_multiplier = curve_multiplier(
        annual,
        model.get("currency_pressure_curve", {}),
        "input_currency_pressure_index",
    )
    market_cycle_multiplier = commercial_market_cycle_multiplier(annual, quarter, model)
    capture_rate = float(model.get("operator_commercial_capture_rate", fallback_capture_rate))
    crowding = model.get("crowding_penalty", {})
    max_penalty_pct = float(crowding.get("max_crowding_sales_penalty_pct", 12.0))
    min_multiplier = float(crowding.get("min_crowding_sales_multiplier", 0.80))
    crowding_multiplier = 1.0 - max_penalty_pct / 100.0 * crowding_index / 100.0
    crowding_multiplier = clamp(crowding_multiplier, min_multiplier, 1.0)
    sales = (
        effective_passengers
        * base_sales
        * luxury_multiplier
        * premium_multiplier
        * high_value_multiplier
        * macro_multiplier
        * currency_multiplier
        * market_cycle_multiplier
        * capture_rate
        * crowding_multiplier
        * quality_multiplier
    )
    return {
        "model_version": str(model.get("model_version", "luxury-sales-v0")),
        "base_sales": base_sales,
        "effective_passengers": effective_passengers,
        "luxury_multiplier": luxury_multiplier,
        "premium_multiplier": premium_multiplier,
        "high_value_multiplier": high_value_multiplier,
        "macro_multiplier": macro_multiplier,
        "currency_multiplier": currency_multiplier,
        "market_cycle_multiplier": market_cycle_multiplier,
        "capture_rate": capture_rate,
        "crowding_multiplier": crowding_multiplier,
        "quality_multiplier": quality_multiplier,
        "sales": sales,
    }


def contract_revenue(
    sales_million_cny: float,
    contract: dict[str, Any],
) -> float:
    revenue_share_pct = float(contract.get("revenue_share_pct", 0.0))
    share_revenue = sales_million_cny * revenue_share_pct / 100.0
    if contract.get("contract_type") != "minimum_guarantee_plus_share":
        return share_revenue
    guarantee = (
        float(contract.get("baseline_quarter_contract_revenue_million_cny", 0.0))
        * float(contract.get("minimum_guarantee_ratio_pct", 0.0))
        / 100.0
    )
    return max(guarantee, share_revenue)


def game_timeline_values(config: dict[str, Any], city_rows: list[dict[str, str]]) -> dict[str, int]:
    timeline = config.get("game_timeline", {})
    first_year = min((int(as_float(row, "year")) for row in city_rows), default=2025)
    simulation_start_year = int(timeline.get("simulation_start_year", first_year))
    startup_years = int(timeline.get("startup_operating_history_years", 0))
    player_start_year = int(
        timeline.get("player_decision_start_year", simulation_start_year + startup_years)
    )
    return {
        "simulation_start_year": simulation_start_year,
        "startup_operating_history_years": startup_years,
        "player_decision_start_year": player_start_year,
    }


def game_phase_for_year(year: int, timeline: dict[str, int]) -> tuple[str, int]:
    player_start = timeline["player_decision_start_year"]
    if year < player_start:
        return "startup_operating_history", 0
    return "player_operation", 1


def duty_free_contract_cycle_start(year: int, timeline: dict[str, int], contract: dict[str, Any]) -> int:
    simulation_start = timeline["simulation_start_year"]
    player_start = timeline["player_decision_start_year"]
    term_years = max(1, int(contract.get("contract_term_years", 5)))
    if year < player_start:
        return simulation_start
    return player_start + ((year - player_start) // term_years) * term_years


def sales_history_values(
    annual_sales_history: dict[int, float],
    cycle_start_year: int,
    lookback_years: int,
) -> list[tuple[int, float]]:
    years = sorted(year for year in annual_sales_history if year < cycle_start_year)
    if lookback_years > 0:
        years = years[-lookback_years:]
    return [(year, annual_sales_history[year]) for year in years]


def trend_multiplier_from_history(history: list[tuple[int, float]], model: dict[str, Any]) -> float:
    if len(history) < 2:
        return 1.0
    first_year, first_value = history[0]
    last_year, last_value = history[-1]
    if first_value <= 0 or last_year <= first_year:
        return 1.0
    annual_growth = (last_value / first_value) ** (1.0 / (last_year - first_year)) - 1.0
    forecast_horizon = float(model.get("forecast_horizon_years", 5.0))
    trend_weight = float(model.get("trend_weight", 0.35))
    multiplier = 1.0 + annual_growth * forecast_horizon * trend_weight
    return clamp(
        multiplier,
        float(model.get("min_trend_multiplier", 0.85)),
        float(model.get("max_trend_multiplier", 1.20)),
    )


def duty_free_static_contract_terms(
    year: int,
    cycle_start_year: int,
    contract: dict[str, Any],
    timeline: dict[str, int],
    startup_pricing: dict[str, Any] | None = None,
) -> dict[str, Any]:
    startup_contract = contract.get("startup_history_contract", {})
    source = {**contract, **startup_contract}
    term_years = max(1, int(source.get("contract_term_years", contract.get("contract_term_years", 5))))
    share_pct = float(source.get("revenue_share_pct", contract.get("revenue_share_pct", 0.0)))
    minimum_ratio_pct = float(
        source.get(
            "minimum_guarantee_ratio_pct",
            source.get("minimum_guarantee_coverage_pct", contract.get("minimum_guarantee_ratio_pct", 0.0)),
        )
    )
    baseline_revenue = float(source.get("baseline_quarter_contract_revenue_million_cny", 0.0))
    model_version = str(source.get("model_version", "startup-history-fixed-contract-v0.1"))
    history_years_used = 0
    if year < timeline["player_decision_start_year"] and startup_pricing:
        baseline_revenue = float(
            startup_pricing.get("baseline_quarter_contract_revenue_million_cny", baseline_revenue)
        )
        model_version = str(
            startup_pricing.get(
                "model_version",
                source.get("forward_priced_model_version", "startup-history-forward-priced-contract-v0.1"),
            )
        )
        history_years_used = int(startup_pricing.get("history_years_used", 0))
    guarantee = baseline_revenue * minimum_ratio_pct / 100.0
    baseline_sales = float(
        startup_pricing.get("forecast_quarter_sales", 0.0)
        if startup_pricing
        else 0.0
    )
    if baseline_sales <= 0:
        baseline_sales = baseline_revenue / (share_pct / 100.0) if share_pct > 0 else 0.0
    return {
        "model_version": model_version,
        "contract_type": str(source.get("contract_type", contract.get("contract_type", "minimum_guarantee_plus_share"))),
        "cycle_id": f"{cycle_start_year}-{cycle_start_year + term_years - 1}",
        "cycle_start_year": cycle_start_year,
        "cycle_end_year": cycle_start_year + term_years - 1,
        "status": "startup_history_forward_priced"
        if year < timeline["player_decision_start_year"] and startup_pricing
        else ("startup_history_fixed" if year < timeline["player_decision_start_year"] else "fixed_contract"),
        "revenue_share_pct": share_pct,
        "minimum_guarantee_ratio_pct": minimum_ratio_pct,
        "minimum_guarantee_coverage_pct": minimum_ratio_pct,
        "history_years_used": history_years_used,
        "forecast_annual_sales": baseline_sales * 4.0,
        "forecast_quarter_sales": baseline_sales,
        "trend_multiplier": 1.0,
        "macro_risk_discount_multiplier": 1.0,
        "bargaining_power_multiplier": 1.0,
        "quarter_minimum_guarantee": guarantee,
    }


def player_contract_action_for_cycle(
    player_contract_actions: list[dict[str, Any]],
    contract_id: str,
    cycle_id: str,
) -> dict[str, Any] | None:
    """Return the newest player signature for one commercial contract cycle."""
    matched: dict[str, Any] | None = None
    for action in player_contract_actions:
        if not isinstance(action, dict) or str(action.get("type") or "") != "sign_contract":
            continue
        action_contract_id = str(action.get("contract_id") or action.get("contractId") or "")
        action_cycle_id = str(action.get("cycle_id") or action.get("cycleId") or "")
        if action_contract_id != contract_id or action_cycle_id != cycle_id:
            continue
        matched = action
    return matched


def player_signed_contract_terms(
    action: dict[str, Any],
    contract: dict[str, Any],
    cycle_start_year: int,
    timeline: dict[str, int],
) -> dict[str, Any]:
    """Normalize a persisted player signature into the normal contract-term interface."""
    terms = action.get("terms", {})
    if not isinstance(terms, dict):
        terms = {}
    term_years = max(1, int(contract.get("contract_term_years", 5)))
    share_pct = float(terms.get("revenue_share_pct", terms.get("revenueSharePct", contract.get("revenue_share_pct", 0.0))))
    coverage_pct = float(
        terms.get(
            "minimum_guarantee_coverage_pct",
            terms.get(
                "minimumGuaranteeCoveragePct",
                contract.get("minimum_guarantee_coverage_pct", contract.get("minimum_guarantee_ratio_pct", 0.0)),
            ),
        )
    )
    forecast_quarter_sales = float(
        terms.get("forecast_quarter_sales", terms.get("forecastQuarterSales", 0.0))
    )
    forecast_annual_sales = float(
        terms.get("forecast_annual_sales", terms.get("forecastAnnualSales", forecast_quarter_sales * 4.0))
    )
    guarantee = float(
        terms.get(
            "quarter_minimum_guarantee",
            terms.get(
                "quarterMinimumGuarantee",
                forecast_quarter_sales * share_pct / 100.0 * coverage_pct / 100.0,
            ),
        )
    )
    return {
        "model_version": "player-signed-contract-v0.1",
        "contract_type": str(
            terms.get("contract_type", terms.get("contractType", contract.get("contract_type", "minimum_guarantee_plus_share")))
        ),
        "cycle_id": f"{cycle_start_year}-{cycle_start_year + term_years - 1}",
        "cycle_start_year": cycle_start_year,
        "cycle_end_year": cycle_start_year + term_years - 1,
        "status": "player_signed",
        "revenue_share_pct": share_pct,
        "minimum_guarantee_ratio_pct": coverage_pct,
        "minimum_guarantee_coverage_pct": coverage_pct,
        "history_years_used": float(terms.get("history_years_used", terms.get("historyYearsUsed", 0.0))),
        "forecast_annual_sales": forecast_annual_sales,
        "forecast_quarter_sales": forecast_quarter_sales,
        "trend_multiplier": float(terms.get("trend_multiplier", terms.get("trendMultiplier", 1.0))),
        "macro_risk_discount_multiplier": float(
            terms.get("macro_risk_discount_multiplier", terms.get("macroRiskDiscountMultiplier", 1.0))
        ),
        "bargaining_power_multiplier": float(
            terms.get("bargaining_power_multiplier", terms.get("bargainingPowerMultiplier", 1.0))
        ),
        "quarter_minimum_guarantee": guarantee,
    }


def duty_free_forecast_contract_terms(
    year: int,
    cycle_start_year: int,
    annual: dict[str, str],
    annual_sales_history: dict[int, float],
    contract: dict[str, Any],
    timeline: dict[str, int],
    startup_pricing: dict[str, Any] | None = None,
    player_contract_actions: list[dict[str, Any]] | None = None,
    contract_id: str = "",
) -> dict[str, Any]:
    player_action = player_contract_action_for_cycle(
        player_contract_actions or [],
        contract_id,
        f"{cycle_start_year}-{cycle_start_year + max(1, int(contract.get('contract_term_years', 5))) - 1}",
    )
    if player_action:
        return player_signed_contract_terms(player_action, contract, cycle_start_year, timeline)
    if year < timeline["player_decision_start_year"] or contract.get("contract_type") != "forecast_minimum_guarantee_plus_share":
        return duty_free_static_contract_terms(year, cycle_start_year, contract, timeline, startup_pricing)

    forecast_model = contract.get("forecast_model", {})
    term_years = max(1, int(contract.get("contract_term_years", 5)))
    lookback_years = int(forecast_model.get("lookback_years", 3))
    if cycle_start_year == timeline["player_decision_start_year"]:
        lookback_years = int(forecast_model.get("startup_history_lookback_years", lookback_years))
    history = sales_history_values(annual_sales_history, cycle_start_year, lookback_years)

    share_pct = float(contract.get("revenue_share_pct", 0.0))
    coverage_pct = float(
        contract.get("minimum_guarantee_coverage_pct", contract.get("minimum_guarantee_ratio_pct", 70.0))
    )
    if history:
        base_annual_sales = mean(value for _, value in history)
    else:
        fallback_quarter_revenue = float(contract.get("baseline_quarter_contract_revenue_million_cny", 0.0))
        fallback_quarter_sales = fallback_quarter_revenue / (share_pct / 100.0) if share_pct > 0 else 0.0
        base_annual_sales = fallback_quarter_sales * 4.0

    trend_multiplier = trend_multiplier_from_history(history, forecast_model)
    macro_risk_discount = field_pressure_multiplier(annual, forecast_model.get("macro_risk_discount", {}))
    bargaining_power = field_pressure_multiplier(annual, forecast_model.get("airport_bargaining_power", {}))
    forecast_annual_sales = base_annual_sales * trend_multiplier * macro_risk_discount * bargaining_power
    forecast_annual_sales = max(0.0, forecast_annual_sales)
    forecast_quarter_sales = forecast_annual_sales / 4.0
    guarantee = forecast_quarter_sales * share_pct / 100.0 * coverage_pct / 100.0

    return {
        "model_version": str(forecast_model.get("model_version", "duty-free-contract-forecast-v0.1")),
        "contract_type": str(contract.get("contract_type", "forecast_minimum_guarantee_plus_share")),
        "cycle_id": f"{cycle_start_year}-{cycle_start_year + term_years - 1}",
        "cycle_start_year": cycle_start_year,
        "cycle_end_year": cycle_start_year + term_years - 1,
        "status": "auto_forecast_renewal",
        "revenue_share_pct": share_pct,
        "minimum_guarantee_ratio_pct": coverage_pct,
        "minimum_guarantee_coverage_pct": coverage_pct,
        "history_years_used": len(history),
        "forecast_annual_sales": forecast_annual_sales,
        "forecast_quarter_sales": forecast_quarter_sales,
        "trend_multiplier": trend_multiplier,
        "macro_risk_discount_multiplier": macro_risk_discount,
        "bargaining_power_multiplier": bargaining_power,
        "quarter_minimum_guarantee": guarantee,
    }


def contract_revenue_from_terms(sales_million_cny: float, terms: dict[str, Any]) -> dict[str, float | str]:
    share_pct = float(terms.get("revenue_share_pct", 0.0))
    share_revenue = sales_million_cny * share_pct / 100.0
    guarantee = float(terms.get("quarter_minimum_guarantee", 0.0))
    contract_type = str(terms.get("contract_type", "minimum_guarantee_plus_share"))
    if contract_type in {"minimum_guarantee_plus_share", "forecast_minimum_guarantee_plus_share"}:
        revenue = max(share_revenue, guarantee)
        basis = "minimum_guarantee" if guarantee > share_revenue else "revenue_share"
    else:
        revenue = share_revenue
        basis = "revenue_share"
    return {
        "share_revenue": share_revenue,
        "minimum_guarantee": guarantee,
        "revenue": revenue,
        "basis": basis,
    }


def _simulate_quarterly_operations_impl(
    city_rows: list[dict[str, str]],
    config: dict[str, Any],
    startup_contract_pricing: dict[str, dict[int, dict[str, Any]]] | None = None,
) -> list[dict[str, Any]]:
    timeline = game_timeline_values(config, city_rows)
    quarter_weights = config["quarter_component_weights"]
    slot_fixed_model = config.get("slot_fixed_operating_cost_model", {})
    slot_fixed_model_version = str(slot_fixed_model.get("model_version", "slot-fixed-operating-cost-v0"))
    quarter_fixed_cost_multipliers = slot_fixed_model.get("quarter_cost_multipliers", {})
    aeronautical = config["aeronautical_revenue"]
    aeronautical_model_version = str(aeronautical.get("model_version", "aeronautical-revenue-v0.1"))
    aeronautical_base_revenue_per_passenger = float(aeronautical["base_revenue_per_passenger_cny"])
    aeronautical_quarter_multipliers = aeronautical.get("quarter_revenue_multipliers", {})
    aeronautical_market_yield = aeronautical.get("market_yield_environment", {})
    aeronautical_capacity_pricing = aeronautical.get("capacity_pricing", {})
    aeronautical_crowding_penalty = aeronautical.get("crowding_revenue_penalty", {})
    variable_cost = config["passenger_variable_cost"]
    passenger_cost_model_version = str(variable_cost.get("model_version", "passenger-variable-cost-v0.1"))
    passenger_cost_base_per_passenger = float(variable_cost["base_cost_per_passenger_cny"])
    passenger_cost_quarter_multipliers = variable_cost.get("quarter_service_pressure_multipliers", {})
    passenger_cost_macro_pressure = variable_cost.get("macro_service_cost_pressure", {})
    congestion_cost = config["congestion_cost"]
    commercial = config["commercial"]
    quality_model = commercial.get("perceived_quality_model", {})
    quality_catalog_id = str(
        quality_model.get(
            "facility_size_catalog",
            config.get("facility_renovation_model", {}).get("facility_size_catalog", "standard_terminal_sizes_v1"),
        )
    )
    quality_facility_sizes = load_facility_size_specs(quality_catalog_id)
    food_retail = commercial["food_retail"]
    food_retail_revenue_model = food_retail.get("revenue_model", {})
    food_retail_fixed_model = food_retail.get("fixed_operating_cost_model", {})
    food_retail_service_model = food_retail.get("passenger_service_cost_model", {})
    food_retail_sales_cost_model = food_retail.get("sales_cost_model", {})
    duty_free = commercial["duty_free"]
    duty_free_sales_model = duty_free.get("sales_model", {})
    luxury = commercial["luxury"]
    luxury_sales_model = luxury.get("sales_model", {})
    renovation_data = renovation_context(config)
    renovation_model = renovation_data.get("model", {})
    renovation_events = renovation_data.get("events", [])
    renovation_facility_sizes = renovation_data.get("facility_sizes", {})
    construction_data = construction_context(config)
    construction_model = construction_data.get("model", {})
    construction_events = construction_data.get("events", [])
    rebuild_data = rebuild_context(config)
    rebuild_model = rebuild_data.get("model", {})
    rebuild_events = rebuild_data.get("events", [])
    rebuild_facility_sizes = rebuild_data.get("facility_sizes", {})
    validate_slot_project_windows(renovation_events, renovation_model, rebuild_events, rebuild_model)

    rows: list[dict[str, Any]] = []
    duty_free_annual_sales_history: dict[int, dict[int, float]] = {}
    duty_free_contract_terms_cache: dict[tuple[int, int], dict[str, Any]] = {}
    luxury_annual_sales_history: dict[int, dict[int, float]] = {}
    luxury_contract_terms_cache: dict[tuple[int, int], dict[str, Any]] = {}
    player_contract_actions = [
        action for action in config.get("player_contract_actions", []) if isinstance(action, dict)
    ]
    for annual in sorted(city_rows, key=lambda row: (int(as_float(row, "seed")), int(as_float(row, "year")))):
        year = int(as_float(annual, "year"))
        seed = int(as_float(annual, "seed"))
        game_phase, player_decision_enabled = game_phase_for_year(year, timeline)
        seed_sales_history = duty_free_annual_sales_history.setdefault(seed, {})
        duty_free_cycle_start = duty_free_contract_cycle_start(year, timeline, duty_free["contract"])
        terms_key = (seed, duty_free_cycle_start)
        if terms_key not in duty_free_contract_terms_cache:
            duty_free_contract_terms_cache[terms_key] = duty_free_forecast_contract_terms(
                year,
                duty_free_cycle_start,
                annual,
                seed_sales_history,
                duty_free["contract"],
                timeline,
                (startup_contract_pricing or {}).get("duty_free", {}).get(seed),
                player_contract_actions,
                "DUTY_FREE_MAIN",
            )
        duty_free_contract_terms = duty_free_contract_terms_cache[terms_key]
        annual_duty_free_sales = 0.0
        seed_luxury_sales_history = luxury_annual_sales_history.setdefault(seed, {})
        luxury_cycle_start = duty_free_contract_cycle_start(year, timeline, luxury["contract"])
        luxury_terms_key = (seed, luxury_cycle_start)
        if luxury_terms_key not in luxury_contract_terms_cache:
            luxury_contract_terms_cache[luxury_terms_key] = duty_free_forecast_contract_terms(
                year,
                luxury_cycle_start,
                annual,
                seed_luxury_sales_history,
                luxury["contract"],
                timeline,
                (startup_contract_pricing or {}).get("luxury", {}).get(seed),
                player_contract_actions,
                "LUXURY_RETAIL_MAIN",
            )
        luxury_contract_terms = luxury_contract_terms_cache[luxury_terms_key]
        annual_luxury_sales = 0.0
        active_slots = str(annual.get("active_airport_facility_slots") or "")
        food_retail_fixed_costs = food_retail.get(
            "fixed_operating_cost_million_cny_per_year_by_facility_size",
            {},
        )

        annual_served = as_float(annual, "city_served_passengers_million")
        annual_potential = as_float(annual, "city_potential_passengers_million", annual_served)
        annual_airline_supply = as_float(
            annual,
            "city_airline_supply_passengers_million",
            annual_potential,
        )
        annual_airline_offered_capacity = as_float(
            annual,
            "city_airline_offered_capacity_million",
            annual_airline_supply,
        )
        annual_airline_serviceable_supply = as_float(
            annual,
            "city_airline_serviceable_supply_million",
            min(annual_potential, annual_airline_offered_capacity),
        )
        annual_airline_serviceable_supply = min(
            annual_potential,
            annual_airline_offered_capacity,
            max(0.0, annual_airline_serviceable_supply),
        )
        annual_airline_unused_capacity = max(
            0.0,
            annual_airline_offered_capacity - annual_airline_serviceable_supply,
        )
        annual_airline_supply_index = as_float(annual, "city_airline_supply_index", 100.0)
        annual_airline_supply_fulfillment = as_float(
            annual,
            "city_airline_supply_fulfillment_pct",
            annual_airline_serviceable_supply / annual_potential * 100.0 if annual_potential else 100.0,
        )
        annual_airline_supply_gap = as_float(
            annual,
            "city_airline_supply_gap_million",
            max(0.0, annual_potential - annual_airline_serviceable_supply),
        )
        annual_airline_supply_volatility_regime = str(
            annual.get("city_airline_supply_volatility_regime") or "normal_airline_supply_cycle"
        )
        base_design_capacity = as_float(annual, "city_airport_design_capacity_million")
        base_max_capacity = as_float(annual, "city_airport_max_capacity_million")
        annual_potential_components = {
            name: as_float(annual, f"{name}_passengers_million")
            for name in COMPONENTS
        }
        annual_potential_component_total = sum(annual_potential_components.values())
        if annual_potential_component_total <= 0.0 and annual_potential > 0.0:
            annual_potential_components = {name: annual_potential / len(COMPONENTS) for name in COMPONENTS}
            annual_potential_component_total = annual_potential
        if annual_potential_component_total > 0.0 and annual_potential > 0.0:
            potential_component_scale = annual_potential / annual_potential_component_total
            annual_potential_components = {
                name: annual_potential_components[name] * potential_component_scale
                for name in COMPONENTS
            }

        annual_airline_supply_components = {
            name: as_float(annual, f"{name}_airline_supply_passengers_million")
            for name in COMPONENTS
        }
        annual_supply_component_total = sum(annual_airline_supply_components.values())
        if annual_supply_component_total <= 0.0:
            potential_total = sum(annual_potential_components.values())
            annual_airline_supply_components = {
                name: annual_airline_serviceable_supply
                * (annual_potential_components[name] / potential_total if potential_total > 0.0 else 1.0 / len(COMPONENTS))
                for name in COMPONENTS
            }
        annual_airline_supply_components = bounded_component_allocation(
            annual_potential_components,
            annual_airline_supply_components,
            annual_airline_serviceable_supply,
        )

        for quarter_index in range(4):
            quarter = f"Q{quarter_index + 1}"
            active_renovations = active_renovation_events(
                renovation_events,
                renovation_model,
                year,
                quarter,
            )
            renovation_capacity = renovation_capacity_profile(
                active_renovations,
                renovation_model,
                renovation_facility_sizes,
            )
            active_rebuilds = active_rebuild_events(
                rebuild_events,
                rebuild_model,
                year,
                quarter,
            )
            started_rebuilds = started_rebuild_events(
                rebuild_events,
                rebuild_model,
                year,
                quarter,
            )
            completed_rebuilds = completed_rebuild_events(
                rebuild_events,
                rebuild_model,
                year,
                quarter,
            )
            rebuild_capacity = rebuild_capacity_profile(
                active_rebuilds,
                completed_rebuilds,
                rebuild_model,
                rebuild_facility_sizes,
            )
            period = quarter_period_index(year, quarter)
            disposed_renovation_ids = disposed_renovation_event_ids_for_period(
                renovation_events,
                renovation_model,
                rebuild_events,
                rebuild_model,
                period,
            )
            renovation_assets = renovation_asset_profile(
                renovation_events,
                renovation_model,
                year,
                quarter,
                disposed_renovation_ids,
            )
            disposed_rebuild_ids = disposed_rebuild_event_ids_for_period(
                rebuild_events,
                rebuild_model,
                period,
            )
            rebuild_assets = rebuild_asset_profile(
                rebuild_events,
                rebuild_model,
                year,
                quarter,
                disposed_rebuild_ids,
            )
            old_renovation_writeoff = rebuild_old_renovation_asset_writeoff(
                started_rebuilds,
                renovation_events,
                renovation_model,
                rebuild_events,
                rebuild_model,
                year,
                quarter,
            )
            old_rebuild_writeoff = rebuild_old_rebuild_asset_writeoff(
                started_rebuilds,
                rebuild_events,
                rebuild_model,
                year,
                quarter,
            )
            construction_assets = construction_asset_profile(
                construction_events,
                construction_model,
                year,
                quarter,
            )
            completed_constructions = completed_construction_events(
                construction_events,
                construction_model,
                year,
                quarter,
            )
            effective_slot_items = effective_facility_slot_items(
                active_slots,
                active_rebuilds,
                completed_rebuilds,
                rebuild_model,
                completed_constructions,
                construction_model,
            )
            effective_slots = facility_slot_items_to_string(effective_slot_items)
            effective_active_sizes = [size for _, size in effective_slot_items]
            food_retail_fixed_cost_base_annual = sum(
                float(food_retail_fixed_costs.get(size, 0.0)) for size in effective_active_sizes
            )
            effective_design_capacity = sum(
                float(renovation_facility_sizes.get(size, {}).get("design_capacity_million", 0.0))
                for _, size in effective_slot_items
            )
            effective_max_capacity = sum(
                float(renovation_facility_sizes.get(size, {}).get("max_capacity_million", 0.0))
                for _, size in effective_slot_items
            )
            design_capacity = max(0.0, effective_design_capacity - float(renovation_capacity["design_loss"]))
            max_capacity = max(0.0, effective_max_capacity - float(renovation_capacity["max_loss"]))
            quarter_design_capacity = design_capacity / 4.0
            quarter_max_capacity = max_capacity / 4.0
            slot_fixed_profile = slot_fixed_cost_profile(
                annual,
                config,
                quarter,
                renovation_data,
                effective_slot_items,
                rebuild_data,
                construction_data,
            )
            annual_fixed_cost = slot_fixed_profile["annual_fixed_cost"]
            quarter_potential_components = {
                name: annual_potential_components[name]
                * float(quarter_weights[name][quarter_index])
                for name in COMPONENTS
            }
            quarter_airline_supply_components = {
                name: annual_airline_supply_components[name]
                * float(quarter_weights[name][quarter_index])
                for name in COMPONENTS
            }
            quarter_potential = sum(quarter_potential_components.values())
            quarter_airline_serviceable_supply = sum(quarter_airline_supply_components.values())
            potential_seasonal_share = quarter_potential / annual_potential if annual_potential else 0.25
            quarter_airline_unused_capacity = annual_airline_unused_capacity * potential_seasonal_share
            quarter_airline_offered_capacity = (
                quarter_airline_serviceable_supply + quarter_airline_unused_capacity
            )
            quarter_airline_supply = quarter_airline_offered_capacity
            quarter_airline_supply_fulfillment = (
                quarter_airline_serviceable_supply / quarter_potential * 100.0
                if quarter_potential
                else 100.0
            )
            quarter_airline_supply_gap = max(
                0.0,
                quarter_potential - quarter_airline_serviceable_supply,
            )
            quarter_serviceable_demand = quarter_airline_serviceable_supply
            has_disruptive_project = bool(active_renovations or active_rebuilds)
            capacity_realization_factor = quarter_capacity_realization_factor(
                seed,
                year,
                quarter_index,
                quarter_serviceable_demand,
                quarter_max_capacity,
                has_disruptive_project,
            )
            quarter_capacity_ceiling = quarter_max_capacity * capacity_realization_factor
            quarter_served = min(quarter_serviceable_demand, quarter_capacity_ceiling)
            quarter_capacity_lost = max(0.0, quarter_serviceable_demand - quarter_served)
            component_scale = (
                quarter_served / quarter_serviceable_demand
                if quarter_serviceable_demand > 0
                else 0.0
            )
            quarter_components = {
                name: quarter_airline_supply_components[name] * component_scale
                for name in COMPONENTS
            }
            quarter_share_pct = quarter_served / annual_served * 100.0 if annual_served > 0 else 0.0
            design_utilization = (
                quarter_served / quarter_design_capacity * 100.0 if quarter_design_capacity > 0 else 0.0
            )
            max_utilization = quarter_served / quarter_max_capacity * 100.0 if quarter_max_capacity > 0 else 0.0
            if quarter_served <= quarter_design_capacity:
                crowding_index = 0.0
            elif quarter_max_capacity > quarter_design_capacity:
                crowding_index = clamp(
                    (quarter_served - quarter_design_capacity)
                    / (quarter_max_capacity - quarter_design_capacity)
                    * 100.0,
                    0.0,
                    100.0,
                )
            else:
                crowding_index = 100.0
            over_max_passengers = max(0.0, quarter_served - quarter_max_capacity)
            perceived_quality = city_airport_perceived_quality_profile(
                annual,
                quarter,
                quarter_served,
                quality_model,
                quality_facility_sizes,
                slot_fixed_model,
                renovation_model,
                renovation_events,
                active_renovations,
                effective_slot_items,
                rebuild_model,
                rebuild_events,
                construction_model,
                construction_events,
            )
            perceived_quality_index = float(perceived_quality["quality_index"])
            food_retail_quality_multiplier = perceived_quality_commercial_multiplier(
                perceived_quality_index,
                quality_model,
                "food_retail",
            )
            duty_free_quality_multiplier = perceived_quality_commercial_multiplier(
                perceived_quality_index,
                quality_model,
                "duty_free",
            )
            luxury_quality_multiplier = perceived_quality_commercial_multiplier(
                perceived_quality_index,
                quality_model,
                "luxury",
            )

            aero_mix = weighted_average_by_component(
                quarter_components,
                aeronautical["component_mix_revenue_weights"],
            )
            aero_quarter_multiplier = float(aeronautical_quarter_multipliers.get(quarter, 1.0))
            aero_market_multiplier = field_pressure_multiplier(annual, aeronautical_market_yield)
            aero_capacity_multiplier = aeronautical_capacity_pricing_multiplier(
                design_utilization,
                aeronautical_capacity_pricing,
            )
            aero_crowding_multiplier = aeronautical_crowding_revenue_multiplier(
                design_utilization,
                max_utilization,
                aeronautical_crowding_penalty,
            )
            aeronautical_revenue = (
                quarter_served
                * aeronautical_base_revenue_per_passenger
                * aero_mix
                * aero_quarter_multiplier
                * aero_market_multiplier
                * aero_capacity_multiplier
                * aero_crowding_multiplier
            )

            cost_complexity = weighted_average_by_component(
                quarter_components,
                variable_cost["component_complexity_weights"],
            )
            passenger_cost_quarter_multiplier = float(passenger_cost_quarter_multipliers.get(quarter, 1.0))
            passenger_cost_macro_multiplier = weighted_index_multiplier(annual, passenger_cost_macro_pressure)
            passenger_cost_load_multiplier = passenger_load_pressure_multiplier(design_utilization, variable_cost)
            passenger_variable_cost = (
                quarter_served
                * passenger_cost_base_per_passenger
                * cost_complexity
                * passenger_cost_quarter_multiplier
                * passenger_cost_macro_multiplier
                * passenger_cost_load_multiplier
            )
            congestion_profile = congestion_adjustment_profile(
                quarter_components,
                quarter_served,
                design_utilization,
                over_max_passengers,
                quarter_max_capacity,
                congestion_cost,
            )
            congestion_cost_value = float(congestion_profile["total"])

            food_retail_propensity = blended_propensity(annual, food_retail["propensity_weights"])
            food_retail_revenue_profile = self_operated_revenue_profile(
                quarter_served,
                food_retail_propensity,
                annual,
                quarter,
                crowding_index,
                float(food_retail.get("base_revenue_per_passenger_cny", 0.0)),
                float(food_retail.get("self_operated_efficiency", 1.0)),
                float(food_retail.get("max_crowding_revenue_penalty_pct", 0.0)),
                food_retail_revenue_model,
                quality_multiplier=food_retail_quality_multiplier,
            )
            food_retail_revenue = float(food_retail_revenue_profile["revenue"])
            crowding_revenue_adjustment = float(food_retail_revenue_profile["crowding_multiplier"])

            duty_free_sales_data = duty_free_sales_profile(
                quarter_components,
                annual,
                quarter,
                crowding_index,
                float(duty_free.get("sales_per_weighted_passenger_cny", 0.0)),
                duty_free.get("weighted_passenger_weights", {}),
                float(duty_free.get("international_exposure_adjustment", 1.0)),
                float(duty_free.get("operator_commercial_capture_rate", 1.0)),
                duty_free_sales_model,
                quality_multiplier=duty_free_quality_multiplier,
            )
            duty_free_weighted_passengers = float(duty_free_sales_data["effective_passengers"])
            duty_free_sales = float(duty_free_sales_data["sales"])
            annual_duty_free_sales += duty_free_sales
            duty_free_contract_revenue_data = contract_revenue_from_terms(
                duty_free_sales,
                duty_free_contract_terms,
            )
            duty_free_revenue = float(duty_free_contract_revenue_data["revenue"])

            luxury_sales_data = luxury_sales_profile(
                quarter_components,
                annual,
                quarter,
                crowding_index,
                float(luxury.get("sales_per_weighted_passenger_cny", 0.0)),
                luxury.get("weighted_passenger_weights", {}),
                float(luxury.get("operator_commercial_capture_rate", 1.0)),
                luxury_sales_model,
                quality_multiplier=luxury_quality_multiplier,
            )
            luxury_weighted_passengers = float(luxury_sales_data["effective_passengers"])
            luxury_sales = float(luxury_sales_data["sales"])
            annual_luxury_sales += luxury_sales
            luxury_contract_revenue_data = contract_revenue_from_terms(
                luxury_sales,
                luxury_contract_terms,
            )
            luxury_revenue = float(luxury_contract_revenue_data["revenue"])

            fixed_quarter_multiplier = float(quarter_fixed_cost_multipliers.get(quarter, 1.0))
            fixed_cost = (
                slot_fixed_profile["age_adjusted_annual"]
                * slot_fixed_profile["macro_multiplier"]
                * slot_fixed_profile["city_multiplier"]
                * fixed_quarter_multiplier
                / 4.0
            )
            food_retail_fixed_profile = self_operated_fixed_cost_profile(
                food_retail_fixed_cost_base_annual,
                annual,
                quarter,
                design_utilization,
                food_retail_fixed_model,
            )
            food_retail_fixed_cost = float(food_retail_fixed_profile["quarter_fixed_cost"])
            food_retail_service_profile = self_operated_passenger_service_cost_profile(
                quarter_served,
                food_retail_propensity,
                annual,
                quarter,
                design_utilization,
                float(food_retail.get("passenger_service_cost_per_passenger_cny", 0.0)),
                food_retail_service_model,
            )
            food_retail_passenger_service_cost = float(food_retail_service_profile["service_cost"])
            food_retail_sales_profile = self_operated_sales_cost_profile(
                food_retail_revenue,
                annual,
                food_retail_sales_cost_model,
            )
            food_retail_sales_cost = float(food_retail_sales_profile["sales_cost"])
            food_retail_operating_cost = (
                food_retail_sales_cost + food_retail_fixed_cost + food_retail_passenger_service_cost
            )
            food_retail_operating_profit = food_retail_revenue - food_retail_operating_cost
            contract_commercial_revenue = duty_free_revenue + luxury_revenue
            commercial_revenue = food_retail_revenue + duty_free_revenue + luxury_revenue
            commercial_direct_cost = food_retail_operating_cost
            commercial_operating_profit = commercial_revenue - commercial_direct_cost
            total_revenue = aeronautical_revenue + commercial_revenue
            total_cost = fixed_cost + passenger_variable_cost + congestion_cost_value + commercial_direct_cost
            profit = total_revenue - total_cost

            rows.append(
                round_record(
                    {
                        "city_airport_quarterly_operations_param_version": (
                            CITY_AIRPORT_QUARTERLY_OPERATIONS_PARAM_VERSION
                        ),
                        "city_airport_quarterly_operations_interface_version": (
                            CITY_AIRPORT_QUARTERLY_OPERATIONS_INTERFACE_VERSION
                        ),
                        "operations_config_version": config["config_version"],
                        "city_airport_market_id": annual.get("city_airport_market_id"),
                        "city_name": annual.get("city_name"),
                        "region_id": annual.get("region_id"),
                        "region_name": annual.get("region_name"),
                        "year_index": int(as_float(annual, "year_index")),
                        "year": int(as_float(annual, "year")),
                        "quarter": quarter,
                        "seed": int(as_float(annual, "seed")),
                        "currency": config["currency"],
                        "amount_unit": config["amount_unit"],
                        "game_phase": game_phase,
                        "player_decision_enabled": player_decision_enabled,
                        "player_decision_start_year": timeline["player_decision_start_year"],
                        "startup_operating_history_years": timeline["startup_operating_history_years"],
                        "input_10y_yield_pct": as_float(annual, "input_10y_yield_pct"),
                        "input_hy_spread_bps": as_float(annual, "input_hy_spread_bps"),
                        "input_equity_return_pct": as_float(annual, "input_equity_return_pct"),
                        "input_equity_valuation_pe": as_float(annual, "input_equity_valuation_pe", 17.0),
                        "annual_city_potential_passengers_million": annual_potential,
                        "annual_city_airline_supply_index": annual_airline_supply_index,
                        "annual_city_airline_offered_capacity_million": annual_airline_offered_capacity,
                        "annual_city_airline_supply_passengers_million": annual_airline_supply,
                        "annual_city_airline_serviceable_supply_million": annual_airline_serviceable_supply,
                        "annual_city_airline_unused_capacity_million": annual_airline_unused_capacity,
                        "annual_city_airline_supply_fulfillment_pct": annual_airline_supply_fulfillment,
                        "annual_city_airline_supply_gap_million": annual_airline_supply_gap,
                        "annual_city_airline_supply_volatility_regime": annual_airline_supply_volatility_regime,
                        "annual_served_passengers_million": annual_served,
                        "quarter_city_potential_passengers_million": quarter_potential,
                        "quarter_airline_offered_capacity_million": quarter_airline_offered_capacity,
                        "quarter_airline_supply_passengers_million": quarter_airline_supply,
                        "quarter_airline_serviceable_supply_million": quarter_airline_serviceable_supply,
                        "quarter_airline_unused_capacity_million": quarter_airline_unused_capacity,
                        "quarter_airline_supply_fulfillment_pct": quarter_airline_supply_fulfillment,
                        "quarter_airline_supply_gap_million": quarter_airline_supply_gap,
                        "quarter_serviceable_demand_million": quarter_serviceable_demand,
                        "quarter_capacity_realization_factor_pct": capacity_realization_factor * 100.0,
                        "quarter_capacity_lost_passengers_million": quarter_capacity_lost,
                        "quarter_served_passengers_million": quarter_served,
                        "business_quarter_potential_passengers_million": quarter_potential_components["business"],
                        "leisure_quarter_potential_passengers_million": quarter_potential_components["leisure"],
                        "vfr_quarter_potential_passengers_million": quarter_potential_components["vfr"],
                        "long_haul_quarter_potential_passengers_million": quarter_potential_components["long_haul"],
                        "transfer_quarter_potential_passengers_million": quarter_potential_components["transfer"],
                        "business_quarter_airline_supply_passengers_million": (
                            quarter_airline_supply_components["business"]
                        ),
                        "leisure_quarter_airline_supply_passengers_million": (
                            quarter_airline_supply_components["leisure"]
                        ),
                        "vfr_quarter_airline_supply_passengers_million": quarter_airline_supply_components["vfr"],
                        "long_haul_quarter_airline_supply_passengers_million": (
                            quarter_airline_supply_components["long_haul"]
                        ),
                        "transfer_quarter_airline_supply_passengers_million": (
                            quarter_airline_supply_components["transfer"]
                        ),
                        "business_quarter_served_passengers_million": quarter_components["business"],
                        "leisure_quarter_served_passengers_million": quarter_components["leisure"],
                        "vfr_quarter_served_passengers_million": quarter_components["vfr"],
                        "long_haul_quarter_served_passengers_million": quarter_components["long_haul"],
                        "transfer_quarter_served_passengers_million": quarter_components["transfer"],
                        "quarter_share_of_annual_served_pct": quarter_share_pct,
                        "base_city_airport_design_capacity_million": base_design_capacity,
                        "base_city_airport_max_capacity_million": base_max_capacity,
                        "renovation_active_event_ids": renovation_capacity["active_event_ids"],
                        "renovation_completed_event_ids": renovation_assets["completed_event_ids"],
                        "renovation_asset_in_service_periods": renovation_assets["in_service_periods"],
                        "renovation_construction_capacity_multiplier": (
                            renovation_capacity["construction_capacity_multiplier"]
                        ),
                        "renovation_design_capacity_loss_million": renovation_capacity["design_loss"],
                        "renovation_max_capacity_loss_million": renovation_capacity["max_loss"],
                        "renovation_quarter_capex_outlay_million_cny": (
                            renovation_assets["quarter_capex_outlay"]
                        ),
                        "renovation_construction_in_progress_million_cny": (
                            renovation_assets["construction_in_progress"]
                        ),
                        "renovation_asset_original_million_cny": renovation_assets["asset_original"],
                        "renovation_asset_residual_floor_million_cny": (
                            renovation_assets["asset_residual_floor"]
                        ),
                        "renovation_asset_accumulated_depreciation_million_cny": (
                            renovation_assets["asset_accumulated_depreciation"]
                        ),
                        "renovation_asset_book_value_million_cny": renovation_assets["asset_book_value"],
                        "renovation_asset_period_depreciation_million_cny": (
                            renovation_assets["asset_period_depreciation"]
                        ),
                        "construction_active_event_ids": construction_assets["active_event_ids"],
                        "construction_completed_event_ids": construction_assets["completed_event_ids"],
                        "construction_asset_in_service_periods": construction_assets["in_service_periods"],
                        "construction_quarter_capex_outlay_million_cny": (
                            construction_assets["quarter_capex_outlay"]
                        ),
                        "construction_in_progress_million_cny": construction_assets["construction_in_progress"],
                        "construction_asset_original_million_cny": construction_assets["asset_original"],
                        "construction_asset_residual_floor_million_cny": (
                            construction_assets["asset_residual_floor"]
                        ),
                        "construction_asset_accumulated_depreciation_million_cny": (
                            construction_assets["asset_accumulated_depreciation"]
                        ),
                        "construction_asset_book_value_million_cny": construction_assets["asset_book_value"],
                        "construction_asset_period_depreciation_million_cny": (
                            construction_assets["asset_period_depreciation"]
                        ),
                        "rebuild_active_event_ids": rebuild_assets["active_event_ids"],
                        "rebuild_started_event_ids": rebuild_assets["started_event_ids"],
                        "rebuild_started_slot_ids": rebuild_assets["started_slot_ids"],
                        "rebuild_completed_event_ids": rebuild_assets["completed_event_ids"],
                        "rebuild_asset_in_service_periods": rebuild_assets["in_service_periods"],
                        "rebuild_construction_capacity_multiplier": (
                            rebuild_capacity["construction_capacity_multiplier"]
                        ),
                        "rebuild_design_capacity_loss_million": rebuild_capacity["design_loss"],
                        "rebuild_max_capacity_loss_million": rebuild_capacity["max_loss"],
                        "rebuild_completed_design_capacity_delta_million": (
                            rebuild_capacity["completed_design_delta"]
                        ),
                        "rebuild_completed_max_capacity_delta_million": (
                            rebuild_capacity["completed_max_delta"]
                        ),
                        "rebuild_quarter_capex_outlay_million_cny": (
                            rebuild_assets["quarter_capex_outlay"]
                        ),
                        "rebuild_quarter_demolition_expense_million_cny": (
                            rebuild_assets["quarter_demolition_expense"]
                        ),
                        "rebuild_old_renovation_asset_writeoff_million_cny": old_renovation_writeoff,
                        "rebuild_old_rebuild_asset_writeoff_million_cny": old_rebuild_writeoff,
                        "rebuild_construction_in_progress_million_cny": (
                            rebuild_assets["construction_in_progress"]
                        ),
                        "rebuild_asset_original_million_cny": rebuild_assets["asset_original"],
                        "rebuild_asset_residual_floor_million_cny": rebuild_assets["asset_residual_floor"],
                        "rebuild_asset_accumulated_depreciation_million_cny": (
                            rebuild_assets["asset_accumulated_depreciation"]
                        ),
                        "rebuild_asset_book_value_million_cny": rebuild_assets["asset_book_value"],
                        "rebuild_asset_period_depreciation_million_cny": (
                            rebuild_assets["asset_period_depreciation"]
                        ),
                        "city_airport_design_capacity_million": design_capacity,
                        "city_airport_max_capacity_million": max_capacity,
                        "quarter_design_capacity_million": quarter_design_capacity,
                        "quarter_max_capacity_million": quarter_max_capacity,
                        "quarter_design_utilization_pct": design_utilization,
                        "quarter_max_utilization_pct": max_utilization,
                        "quarter_crowding_index": crowding_index,
                        "quarter_over_max_pressure_passengers_million": over_max_passengers,
                        "active_facility_slots": active_slots,
                        "effective_facility_slots": effective_slots,
                        "perceived_quality_model_version": perceived_quality["model_version"],
                        "city_airport_perceived_quality_index": perceived_quality_index,
                        "perceived_quality_size_score": perceived_quality["size_score"],
                        "perceived_quality_age_score": perceived_quality["age_score"],
                        "perceived_quality_capacity_score": perceived_quality["capacity_score"],
                        "perceived_quality_construction_disruption_score": (
                            perceived_quality["construction_disruption_score"]
                        ),
                        "slot_fixed_operating_cost_model_version": slot_fixed_model_version,
                        "slot_fixed_operating_cost_base_annual_million_cny": (
                            slot_fixed_profile["base_annual"]
                        ),
                        "slot_fixed_operating_cost_age_multiplier": slot_fixed_profile["age_multiplier"],
                        "slot_fixed_operating_cost_macro_multiplier": (
                            slot_fixed_profile["macro_multiplier"]
                        ),
                        "slot_fixed_operating_cost_city_complexity_multiplier": (
                            slot_fixed_profile["city_multiplier"]
                        ),
                        "slot_fixed_operating_cost_quarter_multiplier": fixed_quarter_multiplier,
                        "annual_slot_fixed_operating_cost_million_cny": annual_fixed_cost,
                        "quarter_slot_fixed_operating_cost_million_cny": fixed_cost,
                        "aeronautical_revenue_model_version": aeronautical_model_version,
                        "aeronautical_base_revenue_per_passenger_cny": aeronautical_base_revenue_per_passenger,
                        "aeronautical_mix_revenue_adjustment": aero_mix,
                        "aeronautical_quarter_revenue_multiplier": aero_quarter_multiplier,
                        "aeronautical_market_yield_multiplier": aero_market_multiplier,
                        "aeronautical_capacity_pricing_multiplier": aero_capacity_multiplier,
                        "aeronautical_crowding_revenue_multiplier": aero_crowding_multiplier,
                        "aeronautical_revenue_million_cny": aeronautical_revenue,
                        "passenger_variable_cost_model_version": passenger_cost_model_version,
                        "passenger_variable_cost_base_per_passenger_cny": passenger_cost_base_per_passenger,
                        "passenger_variable_cost_complexity_adjustment": cost_complexity,
                        "passenger_variable_cost_quarter_multiplier": passenger_cost_quarter_multiplier,
                        "passenger_variable_cost_macro_multiplier": passenger_cost_macro_multiplier,
                        "passenger_variable_cost_load_multiplier": passenger_cost_load_multiplier,
                        "quarter_passenger_variable_cost_million_cny": passenger_variable_cost,
                        "congestion_adjustment_model_version": congestion_profile["model_version"],
                        "congestion_component_mix_multiplier": congestion_profile["component_multiplier"],
                        "congestion_design_utilization_adjustment_per_passenger_cny": (
                            congestion_profile["design_adjustment_per_passenger"]
                        ),
                        "congestion_design_utilization_adjustment_million_cny": (
                            congestion_profile["design_adjustment"]
                        ),
                        "congestion_over_max_pressure_cost_million_cny": (
                            congestion_profile["over_max_pressure_cost"]
                        ),
                        "quarter_congestion_cost_million_cny": congestion_cost_value,
                        "food_retail_operation_mode": food_retail["operation_mode"],
                        "food_retail_blended_propensity_index": food_retail_propensity,
                        "food_retail_revenue_model_version": food_retail_revenue_profile["model_version"],
                        "food_retail_base_revenue_per_passenger_cny": (
                            food_retail_revenue_profile["base_revenue"]
                        ),
                        "food_retail_self_operated_efficiency": food_retail_revenue_profile["efficiency"],
                        "food_retail_propensity_revenue_multiplier": (
                            food_retail_revenue_profile["propensity_multiplier"]
                        ),
                        "food_retail_quarter_revenue_multiplier": (
                            food_retail_revenue_profile["quarter_multiplier"]
                        ),
                        "food_retail_macro_revenue_multiplier": (
                            food_retail_revenue_profile["macro_multiplier"]
                        ),
                        "food_retail_crowding_revenue_multiplier": (
                            food_retail_revenue_profile["crowding_multiplier"]
                        ),
                        "food_retail_perceived_quality_revenue_multiplier": (
                            food_retail_revenue_profile["quality_multiplier"]
                        ),
                        "food_retail_revenue_million_cny": food_retail_revenue,
                        "food_retail_fixed_cost_model_version": food_retail_fixed_profile["model_version"],
                        "food_retail_fixed_cost_base_annual_million_cny": (
                            food_retail_fixed_profile["base_annual"]
                        ),
                        "food_retail_fixed_cost_intensity_multiplier": (
                            food_retail_fixed_profile["intensity_multiplier"]
                        ),
                        "food_retail_fixed_cost_city_complexity_multiplier": (
                            food_retail_fixed_profile["city_multiplier"]
                        ),
                        "food_retail_fixed_cost_macro_multiplier": (
                            food_retail_fixed_profile["macro_multiplier"]
                        ),
                        "food_retail_fixed_cost_quarter_multiplier": (
                            food_retail_fixed_profile["quarter_multiplier"]
                        ),
                        "food_retail_fixed_cost_load_multiplier": (
                            food_retail_fixed_profile["load_multiplier"]
                        ),
                        "food_retail_fixed_operating_cost_million_cny": food_retail_fixed_cost,
                        "food_retail_passenger_service_cost_model_version": (
                            food_retail_service_profile["model_version"]
                        ),
                        "food_retail_passenger_service_base_cost_per_passenger_cny": (
                            food_retail_service_profile["base_cost"]
                        ),
                        "food_retail_passenger_service_consumption_multiplier": (
                            food_retail_service_profile["consumption_multiplier"]
                        ),
                        "food_retail_passenger_service_quarter_multiplier": (
                            food_retail_service_profile["quarter_multiplier"]
                        ),
                        "food_retail_passenger_service_macro_multiplier": (
                            food_retail_service_profile["macro_multiplier"]
                        ),
                        "food_retail_passenger_service_load_multiplier": (
                            food_retail_service_profile["load_multiplier"]
                        ),
                        "food_retail_passenger_service_cost_million_cny": (
                            food_retail_passenger_service_cost
                        ),
                        "food_retail_sales_cost_model_version": food_retail_sales_profile["model_version"],
                        "food_retail_sales_cost_base_ratio_pct": food_retail_sales_profile["base_ratio_pct"],
                        "food_retail_sales_cost_mix_multiplier": food_retail_sales_profile["mix_multiplier"],
                        "food_retail_sales_cost_macro_multiplier": (
                            food_retail_sales_profile["macro_multiplier"]
                        ),
                        "food_retail_sales_cost_ratio_pct": food_retail_sales_profile["ratio_pct"],
                        "food_retail_sales_cost_million_cny": food_retail_sales_cost,
                        "food_retail_operating_cost_million_cny": food_retail_operating_cost,
                        "food_retail_operating_profit_million_cny": food_retail_operating_profit,
                        "duty_free_contract_type": duty_free_contract_terms["contract_type"],
                        "duty_free_contract_model_version": duty_free_contract_terms["model_version"],
                        "duty_free_contract_cycle_id": duty_free_contract_terms["cycle_id"],
                        "duty_free_contract_cycle_start_year": duty_free_contract_terms["cycle_start_year"],
                        "duty_free_contract_cycle_end_year": duty_free_contract_terms["cycle_end_year"],
                        "duty_free_contract_status": duty_free_contract_terms["status"],
                        "duty_free_revenue_share_pct": duty_free_contract_terms["revenue_share_pct"],
                        "duty_free_minimum_guarantee_ratio_pct": (
                            duty_free_contract_terms["minimum_guarantee_ratio_pct"]
                        ),
                        "duty_free_minimum_guarantee_coverage_pct": (
                            duty_free_contract_terms["minimum_guarantee_coverage_pct"]
                        ),
                        "duty_free_contract_history_years_used": (
                            duty_free_contract_terms["history_years_used"]
                        ),
                        "duty_free_contract_forecast_annual_sales_million_cny": (
                            duty_free_contract_terms["forecast_annual_sales"]
                        ),
                        "duty_free_contract_forecast_quarter_sales_million_cny": (
                            duty_free_contract_terms["forecast_quarter_sales"]
                        ),
                        "duty_free_contract_trend_multiplier": (
                            duty_free_contract_terms["trend_multiplier"]
                        ),
                        "duty_free_contract_macro_risk_discount_multiplier": (
                            duty_free_contract_terms["macro_risk_discount_multiplier"]
                        ),
                        "duty_free_contract_bargaining_power_multiplier": (
                            duty_free_contract_terms["bargaining_power_multiplier"]
                        ),
                        "duty_free_contract_minimum_guarantee_million_cny": (
                            duty_free_contract_revenue_data["minimum_guarantee"]
                        ),
                        "duty_free_contract_share_revenue_million_cny": (
                            duty_free_contract_revenue_data["share_revenue"]
                        ),
                        "duty_free_contract_revenue_basis": (
                            duty_free_contract_revenue_data["basis"]
                        ),
                        "duty_free_sales_model_version": duty_free_sales_data["model_version"],
                        "duty_free_base_sales_per_effective_passenger_cny": (
                            duty_free_sales_data["base_sales"]
                        ),
                        "duty_free_propensity_sales_multiplier": (
                            duty_free_sales_data["propensity_multiplier"]
                        ),
                        "duty_free_premium_mix_sales_multiplier": (
                            duty_free_sales_data["premium_multiplier"]
                        ),
                        "duty_free_macro_sales_multiplier": duty_free_sales_data["macro_multiplier"],
                        "duty_free_currency_sales_multiplier": (
                            duty_free_sales_data["currency_multiplier"]
                        ),
                        "duty_free_market_cycle_multiplier": (
                            duty_free_sales_data["market_cycle_multiplier"]
                        ),
                        "duty_free_international_exposure_multiplier": (
                            duty_free_sales_data["international_exposure"]
                        ),
                        "duty_free_operator_capture_rate": duty_free_sales_data["capture_rate"],
                        "duty_free_crowding_sales_multiplier": (
                            duty_free_sales_data["crowding_multiplier"]
                        ),
                        "duty_free_perceived_quality_sales_multiplier": (
                            duty_free_sales_data["quality_multiplier"]
                        ),
                        "duty_free_weighted_passengers_million": duty_free_weighted_passengers,
                        "duty_free_sales_million_cny": duty_free_sales,
                        "duty_free_revenue_million_cny": duty_free_revenue,
                        "luxury_contract_type": luxury_contract_terms["contract_type"],
                        "luxury_contract_model_version": luxury_contract_terms["model_version"],
                        "luxury_contract_cycle_id": luxury_contract_terms["cycle_id"],
                        "luxury_contract_cycle_start_year": luxury_contract_terms["cycle_start_year"],
                        "luxury_contract_cycle_end_year": luxury_contract_terms["cycle_end_year"],
                        "luxury_contract_status": luxury_contract_terms["status"],
                        "luxury_revenue_share_pct": luxury_contract_terms["revenue_share_pct"],
                        "luxury_minimum_guarantee_ratio_pct": (
                            luxury_contract_terms["minimum_guarantee_ratio_pct"]
                        ),
                        "luxury_minimum_guarantee_coverage_pct": (
                            luxury_contract_terms["minimum_guarantee_coverage_pct"]
                        ),
                        "luxury_contract_history_years_used": luxury_contract_terms["history_years_used"],
                        "luxury_contract_forecast_annual_sales_million_cny": (
                            luxury_contract_terms["forecast_annual_sales"]
                        ),
                        "luxury_contract_forecast_quarter_sales_million_cny": (
                            luxury_contract_terms["forecast_quarter_sales"]
                        ),
                        "luxury_contract_trend_multiplier": luxury_contract_terms["trend_multiplier"],
                        "luxury_contract_macro_risk_discount_multiplier": (
                            luxury_contract_terms["macro_risk_discount_multiplier"]
                        ),
                        "luxury_contract_bargaining_power_multiplier": (
                            luxury_contract_terms["bargaining_power_multiplier"]
                        ),
                        "luxury_contract_minimum_guarantee_million_cny": (
                            luxury_contract_revenue_data["minimum_guarantee"]
                        ),
                        "luxury_contract_share_revenue_million_cny": (
                            luxury_contract_revenue_data["share_revenue"]
                        ),
                        "luxury_contract_revenue_basis": luxury_contract_revenue_data["basis"],
                        "luxury_sales_model_version": luxury_sales_data["model_version"],
                        "luxury_base_sales_per_effective_passenger_cny": luxury_sales_data["base_sales"],
                        "luxury_propensity_sales_multiplier": luxury_sales_data["luxury_multiplier"],
                        "luxury_premium_mix_sales_multiplier": luxury_sales_data["premium_multiplier"],
                        "luxury_high_value_mix_multiplier": luxury_sales_data["high_value_multiplier"],
                        "luxury_macro_sales_multiplier": luxury_sales_data["macro_multiplier"],
                        "luxury_currency_sales_multiplier": luxury_sales_data["currency_multiplier"],
                        "luxury_market_cycle_multiplier": (
                            luxury_sales_data["market_cycle_multiplier"]
                        ),
                        "luxury_operator_capture_rate": luxury_sales_data["capture_rate"],
                        "luxury_crowding_sales_multiplier": luxury_sales_data["crowding_multiplier"],
                        "luxury_perceived_quality_sales_multiplier": (
                            luxury_sales_data["quality_multiplier"]
                        ),
                        "luxury_weighted_passengers_million": luxury_weighted_passengers,
                        "luxury_sales_million_cny": luxury_sales,
                        "luxury_retail_revenue_million_cny": luxury_revenue,
                        "contract_commercial_revenue_million_cny": contract_commercial_revenue,
                        "commercial_revenue_million_cny": commercial_revenue,
                        "commercial_direct_cost_million_cny": commercial_direct_cost,
                        "commercial_operating_profit_million_cny": commercial_operating_profit,
                        "total_operating_revenue_million_cny": total_revenue,
                        "total_operating_cost_million_cny": total_cost,
                        "quarter_operating_profit_million_cny": profit,
                        "operating_margin_pct": profit / total_revenue * 100.0 if total_revenue else 0.0,
                        "total_revenue_per_passenger_cny": total_revenue / quarter_served
                        if quarter_served
                        else 0.0,
                        "total_cost_per_passenger_cny": total_cost / quarter_served if quarter_served else 0.0,
                        "annual_city_binding_bottleneck": annual.get("city_binding_bottleneck", ""),
                        "quarter_event_hint": annual.get("airport_event_hint", "none"),
                        "branch_scenario_id": annual.get("branch_scenario_id", "none"),
                        "branch_scenario_state": annual.get("branch_scenario_state", "baseline"),
                        "branch_effect_phase": annual.get("branch_effect_phase", "none"),
                    }
                )
            )

        seed_sales_history[year] = annual_duty_free_sales
        seed_luxury_sales_history[year] = annual_luxury_sales

    return rows


STARTUP_HISTORY_FORWARD_PRICING_MODES = {
    "future_sales_average",
    "startup_future_sales_average",
    "forward_priced_from_startup_sales",
}


def startup_history_forward_pricing_enabled(contract: dict[str, Any]) -> bool:
    startup_contract = contract.get("startup_history_contract", {})
    mode = str(startup_contract.get("pricing_mode", "fixed")).strip().lower()
    return mode in STARTUP_HISTORY_FORWARD_PRICING_MODES


def derive_startup_history_contract_pricing(
    first_pass_rows: list[dict[str, Any]],
    city_rows: list[dict[str, str]],
    config: dict[str, Any],
) -> dict[str, dict[int, dict[str, Any]]]:
    timeline = game_timeline_values(config, city_rows)
    simulation_start = timeline["simulation_start_year"]
    player_start = timeline["player_decision_start_year"]
    if player_start <= simulation_start:
        return {}

    commercial = config.get("commercial", {})
    result: dict[str, dict[int, dict[str, Any]]] = {}
    segment_specs = [
        ("duty_free", "duty_free_sales_million_cny"),
        ("luxury", "luxury_sales_million_cny"),
    ]
    for segment, sales_field in segment_specs:
        contract = commercial.get(segment, {}).get("contract", {})
        if not startup_history_forward_pricing_enabled(contract):
            continue
        startup_contract = contract.get("startup_history_contract", {})
        share_pct = float(startup_contract.get("revenue_share_pct", contract.get("revenue_share_pct", 0.0)))
        if share_pct <= 0:
            continue

        grouped_sales: dict[int, list[tuple[int, float]]] = {}
        for row in first_pass_rows:
            year = int(as_float(row, "year"))
            if year < simulation_start or year >= player_start:
                continue
            seed = int(as_float(row, "seed"))
            grouped_sales.setdefault(seed, []).append((year, as_float(row, sales_field)))

        for seed, sales_items in grouped_sales.items():
            sales_values = [sales for _, sales in sales_items if sales > 0]
            if not sales_values:
                continue
            avg_quarter_sales = mean(sales_values)
            baseline_revenue = avg_quarter_sales * share_pct / 100.0
            years_used = len({year for year, _ in sales_items})
            result.setdefault(segment, {})[seed] = {
                "model_version": str(
                    startup_contract.get(
                        "forward_priced_model_version",
                        "startup-history-forward-priced-contract-v0.1",
                    )
                ),
                "baseline_quarter_contract_revenue_million_cny": baseline_revenue,
                "forecast_quarter_sales": avg_quarter_sales,
                "history_years_used": float(years_used),
            }
    return result


def simulate_quarterly_operations(
    city_rows: list[dict[str, str]],
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    first_pass_rows = _simulate_quarterly_operations_impl(city_rows, copy.deepcopy(config))
    startup_contract_pricing = derive_startup_history_contract_pricing(first_pass_rows, city_rows, config)
    if not startup_contract_pricing:
        return first_pass_rows
    return _simulate_quarterly_operations_impl(
        city_rows,
        copy.deepcopy(config),
        startup_contract_pricing=startup_contract_pricing,
    )


def summarize(rows: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, Any]:
    grouped: dict[tuple[int, int], list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault((int(row["seed"]), int(row["year"])), []).append(row)

    annual_summaries: list[dict[str, Any]] = []
    for (seed, year), items in sorted(grouped.items()):
        annual_revenue = sum(as_float(item, "total_operating_revenue_million_cny") for item in items)
        annual_cost = sum(as_float(item, "total_operating_cost_million_cny") for item in items)
        annual_profit = sum(as_float(item, "quarter_operating_profit_million_cny") for item in items)
        annual_renovation_capex = sum(
            as_float(item, "renovation_quarter_capex_outlay_million_cny") for item in items
        )
        annual_renovation_depreciation = sum(
            as_float(item, "renovation_asset_period_depreciation_million_cny") for item in items
        )
        annual_construction_capex = sum(
            as_float(item, "construction_quarter_capex_outlay_million_cny") for item in items
        )
        annual_construction_depreciation = sum(
            as_float(item, "construction_asset_period_depreciation_million_cny") for item in items
        )
        annual_rebuild_capex = sum(
            as_float(item, "rebuild_quarter_capex_outlay_million_cny") for item in items
        )
        annual_rebuild_demolition_expense = sum(
            as_float(item, "rebuild_quarter_demolition_expense_million_cny") for item in items
        )
        annual_rebuild_renovation_writeoff = sum(
            as_float(item, "rebuild_old_renovation_asset_writeoff_million_cny") for item in items
        )
        annual_rebuild_depreciation = sum(
            as_float(item, "rebuild_asset_period_depreciation_million_cny") for item in items
        )
        quality_weight = sum(as_float(item, "quarter_served_passengers_million") for item in items)
        if quality_weight > 0:
            annual_quality_index = sum(
                as_float(item, "city_airport_perceived_quality_index")
                * as_float(item, "quarter_served_passengers_million")
                for item in items
            ) / quality_weight
            annual_food_retail_quality_multiplier = sum(
                as_float(item, "food_retail_perceived_quality_revenue_multiplier")
                * as_float(item, "quarter_served_passengers_million")
                for item in items
            ) / quality_weight
            annual_duty_free_quality_multiplier = sum(
                as_float(item, "duty_free_perceived_quality_sales_multiplier")
                * as_float(item, "quarter_served_passengers_million")
                for item in items
            ) / quality_weight
            annual_luxury_quality_multiplier = sum(
                as_float(item, "luxury_perceived_quality_sales_multiplier")
                * as_float(item, "quarter_served_passengers_million")
                for item in items
            ) / quality_weight
        else:
            annual_quality_index = 100.0
            annual_food_retail_quality_multiplier = 1.0
            annual_duty_free_quality_multiplier = 1.0
            annual_luxury_quality_multiplier = 1.0
        annual_summaries.append(
            round_record(
                {
                    "seed": seed,
                    "year": year,
                    "annual_served_passengers_million": as_float(items[0], "annual_served_passengers_million"),
                    "annual_operating_revenue_million_cny": annual_revenue,
                    "annual_operating_cost_million_cny": annual_cost,
                    "annual_operating_profit_million_cny": annual_profit,
                    "annual_renovation_capex_outlay_million_cny": annual_renovation_capex,
                    "annual_renovation_asset_depreciation_million_cny": annual_renovation_depreciation,
                    "renovation_asset_book_value_million_cny": max(
                        as_float(item, "renovation_asset_book_value_million_cny") for item in items
                    ),
                    "annual_construction_capex_outlay_million_cny": annual_construction_capex,
                    "annual_construction_asset_depreciation_million_cny": annual_construction_depreciation,
                    "construction_asset_book_value_million_cny": max(
                        as_float(item, "construction_asset_book_value_million_cny") for item in items
                    ),
                    "annual_rebuild_capex_outlay_million_cny": annual_rebuild_capex,
                    "annual_rebuild_demolition_expense_million_cny": annual_rebuild_demolition_expense,
                    "annual_rebuild_old_renovation_asset_writeoff_million_cny": (
                        annual_rebuild_renovation_writeoff
                    ),
                    "annual_rebuild_asset_depreciation_million_cny": annual_rebuild_depreciation,
                    "rebuild_asset_book_value_million_cny": max(
                        as_float(item, "rebuild_asset_book_value_million_cny") for item in items
                    ),
                    "max_rebuild_design_capacity_loss_million": max(
                        as_float(item, "rebuild_design_capacity_loss_million") for item in items
                    ),
                    "annual_city_airport_perceived_quality_index": annual_quality_index,
                    "annual_food_retail_perceived_quality_revenue_multiplier": (
                        annual_food_retail_quality_multiplier
                    ),
                    "annual_duty_free_perceived_quality_sales_multiplier": annual_duty_free_quality_multiplier,
                    "annual_luxury_perceived_quality_sales_multiplier": annual_luxury_quality_multiplier,
                    "annual_operating_margin_pct": annual_profit / annual_revenue * 100.0
                    if annual_revenue
                    else 0.0,
                    "max_quarter_design_utilization_pct": max(
                        as_float(item, "quarter_design_utilization_pct") for item in items
                    ),
                    "max_quarter_crowding_index": max(as_float(item, "quarter_crowding_index") for item in items),
                    "max_renovation_design_capacity_loss_million": max(
                        as_float(item, "renovation_design_capacity_loss_million") for item in items
                    ),
                    "binding_bottleneck": items[0].get("annual_city_binding_bottleneck", ""),
                }
            )
        )

    selected_years = {2025, 2035, 2050, 2085}
    selected = [item for item in annual_summaries if int(item["year"]) in selected_years]
    return {
        "city_airport_quarterly_operations_param_version": CITY_AIRPORT_QUARTERLY_OPERATIONS_PARAM_VERSION,
        "city_airport_quarterly_operations_interface_version": CITY_AIRPORT_QUARTERLY_OPERATIONS_INTERFACE_VERSION,
        "operations_config_version": config["config_version"],
        "city_airport_market_id": config["city_airport_market_id"],
        "currency": config["currency"],
        "amount_unit": config["amount_unit"],
        "game_timeline": config.get("game_timeline", {}),
        "row_count": len(rows),
        "annual_summary_count": len(annual_summaries),
        "selected_annual_summaries": selected,
        "latest_annual_summary": annual_summaries[-1] if annual_summaries else {},
        "average_operating_margin_pct": round(
            mean(as_float(item, "annual_operating_margin_pct") for item in annual_summaries), 4
        )
        if annual_summaries
        else 0.0,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate quarterly city airport operations with game-calibrated RMB amounts."
    )
    parser.add_argument("--market", default="beijing_airport_system")
    parser.add_argument(
        "--city-demand-csv",
        type=Path,
        default=None,
        help="Defaults to airport/output/city_airport_market_demand/china_mainland/<market>_city_airport_demand_seed_sweep.csv.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_DIR / "beijing_airport_system_quarterly_operations_v1.json",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=AIRPORT_DIR / "output" / "city_airport_quarterly_operations",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.city_demand_csv is None:
        args.city_demand_csv = (
            AIRPORT_DIR
            / "output"
            / "city_airport_market_demand"
            / "china_mainland"
            / f"{args.market}_city_airport_demand_seed_sweep.csv"
        )

    config = load_config(args.config)
    city_rows = read_csv(args.city_demand_csv)
    if not city_rows:
        raise SystemExit(f"No city airport demand rows found in {args.city_demand_csv}")
    rows = simulate_quarterly_operations(city_rows, config)

    region_id = str(city_rows[0].get("region_id") or "unknown_region")
    market_id = str(config["city_airport_market_id"])
    output_dir = args.output_dir / region_id
    csv_path = output_dir / f"{market_id}_quarterly_operations_seed_sweep.csv"
    summary_path = output_dir / f"{market_id}_quarterly_operations_summary.json"
    js_path = output_dir / f"{market_id}_quarterly_operations_viewer_data.js"

    write_csv(csv_path, rows, QUARTERLY_OPERATIONS_FIELDS)
    write_json(summary_path, summarize(rows, config))
    write_viewer_data_js(js_path, rows)
    print(
        json.dumps(
            {"csv": str(csv_path), "summary": str(summary_path), "viewer": str(js_path)},
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
