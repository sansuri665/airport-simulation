from __future__ import annotations

from importlib import import_module

_SIBLING_PREFIX = f"{__package__}." if __package__ else ""
simulation_io = import_module(f"{_SIBLING_PREFIX}simulation_io")
simulation_utils = import_module(f"{_SIBLING_PREFIX}simulation_utils")
city_market_demand = import_module(
    f"{_SIBLING_PREFIX}city_airport_market_demand_layer_sim"
)
forecast_profile_config = import_module(
    f"{_SIBLING_PREFIX}forecast_system.profile_config"
)
forecast_scoring = import_module(f"{_SIBLING_PREFIX}forecast_system.scoring")
forecast_viewer_assets = import_module(
    f"{_SIBLING_PREFIX}forecast_system.viewer_assets"
)
forecast_candidate_generator = import_module(
    f"{_SIBLING_PREFIX}forecast_system.candidate_generator"
)

read_csv = simulation_io.read_csv_utf8_sig
write_csv = simulation_io.write_csv_utf8_sig_with_extra_fields
write_json = simulation_io.write_json_utf8_data
as_float = simulation_utils.as_float_convert_lookup_default
clamp = simulation_utils.clamp
safe_divide = simulation_utils.safe_divide
capped_weighted_allocation = city_market_demand.capped_weighted_allocation
AIRPORT_DIR = forecast_profile_config.AIRPORT_DIR
DEFAULT_CONFIG_DIR = forecast_profile_config.DEFAULT_CONFIG_DIR
DEFAULT_TIER_CATALOG = forecast_profile_config.DEFAULT_TIER_CATALOG
DEFAULT_NARRATIVE_CATALOG = forecast_profile_config.DEFAULT_NARRATIVE_CATALOG
catalog_path = forecast_profile_config.catalog_path
catalog_items = forecast_profile_config.catalog_items
apply_narrative_modifier = forecast_profile_config.apply_narrative_modifier
resolve_forecast_report_profiles = forecast_profile_config.resolve_forecast_report_profiles
load_config = forecast_profile_config.load_config
COMPONENTS = forecast_scoring.COMPONENTS
COMPONENT_SCORE_WEIGHTS = forecast_scoring.COMPONENT_SCORE_WEIGHTS
COMPONENT_SHARE_UNCERTAINTY_MULTIPLIER = (
    forecast_scoring.COMPONENT_SHARE_UNCERTAINTY_MULTIPLIER
)
REALIZED_SCORE_METHOD_VERSION = forecast_scoring.REALIZED_SCORE_METHOD_VERSION
REALIZED_TOTAL_RESULT_SCORE_WEIGHTS = (
    forecast_scoring.REALIZED_TOTAL_RESULT_SCORE_WEIGHTS
)
REALIZED_COMPONENT_RESULT_SCORE_WEIGHTS = (
    forecast_scoring.REALIZED_COMPONENT_RESULT_SCORE_WEIGHTS
)
REALIZED_RESULT_SCORE_WEIGHTS = forecast_scoring.REALIZED_RESULT_SCORE_WEIGHTS
REALIZED_PROCESS_SCORE_WEIGHTS = forecast_scoring.REALIZED_PROCESS_SCORE_WEIGHTS
REALIZED_RESULT_WEIGHT_TOTAL = forecast_scoring.REALIZED_RESULT_WEIGHT_TOTAL
accuracy_score_from_gap = forecast_scoring.accuracy_score_from_gap
direction_accuracy_score = forecast_scoring.direction_accuracy_score
interval_calibration_score = forecast_scoring.interval_calibration_score
weighted_component_share_gap = forecast_scoring.weighted_component_share_gap
component_potential_structure_score = (
    forecast_scoring.component_potential_structure_score
)
component_supply_structure_score = forecast_scoring.component_supply_structure_score
component_fulfillment_score = forecast_scoring.component_fulfillment_score
component_interval_calibration_score = (
    forecast_scoring.component_interval_calibration_score
)
bottleneck_accuracy_score = forecast_scoring.bottleneck_accuracy_score
weighted_mean = forecast_scoring.weighted_mean
realized_bias_label = forecast_scoring.realized_bias_label
turn_timing_score = forecast_scoring.turn_timing_score
total_revision_discipline_score = forecast_scoring.total_revision_discipline_score
component_revision_discipline_score = (
    forecast_scoring.component_revision_discipline_score
)
revision_discipline_scores = forecast_scoring.revision_discipline_scores
annotate_realized_quality_scores = forecast_scoring.annotate_realized_quality_scores
FORECAST_VIEWER_LAZY_INDEX_VERSION = (
    forecast_viewer_assets.FORECAST_VIEWER_LAZY_INDEX_VERSION
)
FORECAST_VIEWER_CHUNK_VERSION = forecast_viewer_assets.FORECAST_VIEWER_CHUNK_VERSION
VIEWER_REPORT_METADATA_FIELDS = forecast_viewer_assets.VIEWER_REPORT_METADATA_FIELDS
PLAYER_FORECAST_FIELDS = forecast_viewer_assets.PLAYER_FORECAST_FIELDS
AUDIT_FORECAST_FIELDS = forecast_viewer_assets.AUDIT_FORECAST_FIELDS
FORECAST_VIEWER_NULL_FIELDS = forecast_viewer_assets.FORECAST_VIEWER_NULL_FIELDS
forecast_viewer_config = forecast_viewer_assets.forecast_viewer_config
forecast_player_row = forecast_viewer_assets.forecast_player_row
forecast_audit_row = forecast_viewer_assets.forecast_audit_row
safe_report_filename = forecast_viewer_assets.safe_report_filename
serialize_viewer_index = forecast_viewer_assets.serialize_viewer_index
serialize_viewer_report = forecast_viewer_assets.serialize_viewer_report
write_viewer_lazy_assets = forecast_viewer_assets.write_viewer_lazy_assets
FORECAST_CANDIDATE_GENERATOR_VERSION = (
    forecast_candidate_generator.FORECAST_CANDIDATE_GENERATOR_VERSION
)
FORECAST_CANDIDATE_MIN_SCORE_BAND_WIDTH = (
    forecast_candidate_generator.FORECAST_CANDIDATE_MIN_SCORE_BAND_WIDTH
)
FORECAST_CANDIDATE_MAX_ATTEMPTS = (
    forecast_candidate_generator.FORECAST_CANDIDATE_MAX_ATTEMPTS
)
FORECAST_CANDIDATE_INCOMPATIBLE_MODIFIER_PAIRS = (
    forecast_candidate_generator.FORECAST_CANDIDATE_INCOMPATIBLE_MODIFIER_PAIRS
)
_forecast_candidate_catalog_sources = (
    forecast_candidate_generator._forecast_candidate_catalog_sources
)
forecast_candidate_catalog = forecast_candidate_generator.forecast_candidate_catalog
_candidate_modifiers_are_compatible = (
    forecast_candidate_generator._candidate_modifiers_are_compatible
)
_validated_candidate_modifier_ids = (
    forecast_candidate_generator._validated_candidate_modifier_ids
)
_candidate_modifier_options = forecast_candidate_generator._candidate_modifier_options
_candidate_modifier_ids_for_attempt = (
    forecast_candidate_generator._candidate_modifier_ids_for_attempt
)
_candidate_bias_direction = forecast_candidate_generator._candidate_bias_direction
_candidate_report_id = forecast_candidate_generator._candidate_report_id

import argparse
import hashlib
import json
import math
from pathlib import Path
from statistics import mean
from typing import Any


CITY_AIRPORT_POTENTIAL_PASSENGER_FORECAST_PARAM_VERSION = "city-airport-narrative-passenger-forecast-layer-v1.2"
CITY_AIRPORT_POTENTIAL_PASSENGER_FORECAST_INTERFACE_VERSION = "city-airport-narrative-passenger-forecast-interface-v1.2"
POTENTIAL_PASSENGER_FORECAST_FIELDS = [
    "city_airport_potential_passenger_forecast_param_version",
    "city_airport_potential_passenger_forecast_interface_version",
    "forecast_config_version",
    "forecast_model_version",
    "city_airport_market_id",
    "city_name",
    "region_id",
    "region_name",
    "seed",
    "as_of_year",
    "as_of_year_index",
    "as_of_quarter",
    "data_cutoff_year",
    "data_cutoff_quarter",
    "forecast_report_id",
    "forecast_report_tier",
    "forecast_report_tier_profile_id",
    "forecast_report_source",
    "forecast_narrative_profile_id",
    "forecast_narrative_modifier_ids",
    "forecast_narrative_style_label",
    "forecast_narrative_style_summary",
    "forecast_narrative_style_method",
    "forecast_narrative_style_blind_spot",
    "forecast_narrative_modifier_labels",
    "forecast_narrative_modifier_groups",
    "forecast_narrative_modifier_descriptions",
    "forecast_narrative_modifier_tradeoffs",
    "forecast_narrative_headline",
    "forecast_primary_driver",
    "forecast_secondary_driver",
    "forecast_expected_regime",
    "forecast_turn_window_start_year",
    "forecast_turn_window_end_year",
    "forecast_conviction_pct",
    "forecast_revision_reason",
    "forecast_revision_pct",
    "forecast_component_revision_pp",
    "forecast_previous_mid_million",
    "forecast_signal_demand_direction",
    "forecast_signal_supply_direction",
    "forecast_signal_turn_direction",
    "forecast_signal_confidence_pct",
    "reported_confidence_style",
    "forecast_bias_direction",
    "configured_forecast_quality_score",
    "forecast_quality_score",
    "future_peek_mode",
    "forecast_year",
    "forecast_year_index",
    "forecast_horizon_years",
    "current_effective_passengers_million",
    "current_potential_passengers_million",
    "current_airline_supply_passengers_million",
    "current_airline_serviceable_supply_million",
    "current_market_bottleneck",
    "naive_public_curve_effective_million",
    "naive_public_curve_potential_million",
    "naive_public_curve_airline_supply_million",
    "lagged_hidden_curve_effective_million",
    "lagged_hidden_curve_potential_million",
    "lagged_hidden_curve_airline_supply_million",
    "forecast_effective_passengers_mid_million",
    "forecast_effective_passengers_low_million",
    "forecast_effective_passengers_high_million",
    "forecast_potential_passengers_mid_million",
    "forecast_airline_supply_passengers_mid_million",
    "forecast_airline_serviceable_supply_mid_million",
    "forecast_airline_unused_capacity_mid_million",
    "forecast_market_bottleneck",
    "forecast_downside_band_pct",
    "forecast_upside_band_pct",
    "forecast_error_band_pct",
    "forecast_confidence_pct",
    "realized_score_method_version",
    "realized_report_quality_score",
    "realized_result_quality_score",
    "realized_report_process_quality_score",
    "realized_total_result_quality_score",
    "realized_component_result_quality_score",
    "realized_point_quality_score",
    "realized_midpoint_accuracy_score",
    "realized_trend_accuracy_score",
    "realized_shape_accuracy_score",
    "realized_component_structure_score",
    "realized_component_potential_structure_score",
    "realized_component_supply_structure_score",
    "realized_component_fulfillment_score",
    "realized_component_interval_calibration_score",
    "realized_bottleneck_accuracy_score",
    "realized_interval_calibration_score",
    "realized_turn_timing_score",
    "realized_revision_discipline_score",
    "realized_total_revision_discipline_score",
    "realized_component_revision_discipline_score",
    "realized_report_weighted_abs_error_pct",
    "realized_report_interval_hit_rate_pct",
    "realized_report_bias_pct",
    "realized_report_bias_label",
    "calibration_score",
    "seed_signal_capture_pct",
    "forecast_lag_years",
    "deterministic_forecast_bias_pct",
    "public_consensus_anchor_pct",
    "consensus_herding_bias_pct",
    "market_consensus_gap_pct",
    "forecast_momentum_label",
    "forecast_long_term_tier_label",
    "forecast_reliability_label",
    "forecast_main_upside_factors",
    "forecast_main_downside_factors",
    "source_seed_city_momentum_label",
    "source_seed_city_potential_multiplier",
    "forecast_method_note",
    "business_forecast_effective_passengers_mid_million",
    "leisure_forecast_effective_passengers_mid_million",
    "vfr_forecast_effective_passengers_mid_million",
    "long_haul_forecast_effective_passengers_mid_million",
    "transfer_forecast_effective_passengers_mid_million",
    "business_forecast_potential_passengers_mid_million",
    "leisure_forecast_potential_passengers_mid_million",
    "vfr_forecast_potential_passengers_mid_million",
    "long_haul_forecast_potential_passengers_mid_million",
    "transfer_forecast_potential_passengers_mid_million",
    "business_forecast_airline_supply_passengers_mid_million",
    "leisure_forecast_airline_supply_passengers_mid_million",
    "vfr_forecast_airline_supply_passengers_mid_million",
    "long_haul_forecast_airline_supply_passengers_mid_million",
    "transfer_forecast_airline_supply_passengers_mid_million",
    "business_forecast_effective_share_pct",
    "leisure_forecast_effective_share_pct",
    "vfr_forecast_effective_share_pct",
    "long_haul_forecast_effective_share_pct",
    "transfer_forecast_effective_share_pct",
    "business_debug_hidden_true_effective_passengers_million",
    "leisure_debug_hidden_true_effective_passengers_million",
    "vfr_debug_hidden_true_effective_passengers_million",
    "long_haul_debug_hidden_true_effective_passengers_million",
    "transfer_debug_hidden_true_effective_passengers_million",
    "business_debug_hidden_true_effective_share_pct",
    "leisure_debug_hidden_true_effective_share_pct",
    "vfr_debug_hidden_true_effective_share_pct",
    "long_haul_debug_hidden_true_effective_share_pct",
    "transfer_debug_hidden_true_effective_share_pct",
    "business_debug_hidden_true_potential_passengers_million",
    "leisure_debug_hidden_true_potential_passengers_million",
    "vfr_debug_hidden_true_potential_passengers_million",
    "long_haul_debug_hidden_true_potential_passengers_million",
    "transfer_debug_hidden_true_potential_passengers_million",
    "business_debug_hidden_true_airline_supply_passengers_million",
    "leisure_debug_hidden_true_airline_supply_passengers_million",
    "vfr_debug_hidden_true_airline_supply_passengers_million",
    "long_haul_debug_hidden_true_airline_supply_passengers_million",
    "transfer_debug_hidden_true_airline_supply_passengers_million",
    "debug_hidden_true_effective_passengers_million",
    "debug_hidden_true_potential_passengers_million",
    "debug_hidden_true_airline_supply_passengers_million",
    "debug_hidden_true_market_bottleneck",
    "debug_hidden_true_inside_forecast_range",
    "debug_hidden_true_position_pct",
    "debug_model_gap_to_true_pct",
    "debug_hidden_signal_demand_direction",
    "debug_hidden_signal_supply_direction",
    "debug_hidden_signal_turn_year",
    "debug_hidden_signal_turn_direction",
]

for _component in COMPONENTS:
    POTENTIAL_PASSENGER_FORECAST_FIELDS.extend(
        [
            f"current_{_component}_potential_passengers_million",
            f"current_{_component}_airline_supply_passengers_million",
            f"current_{_component}_effective_passengers_million",
            f"{_component}_forecast_potential_share_pct",
            f"{_component}_forecast_airline_priority_weight",
            f"{_component}_forecast_airline_offered_capacity_million",
            f"{_component}_forecast_airline_supply_share_pct",
            f"{_component}_forecast_airline_supply_fulfillment_pct",
            f"{_component}_forecast_airline_supply_gap_million",
            f"{_component}_forecast_effective_passengers_low_million",
            f"{_component}_forecast_effective_passengers_high_million",
            f"{_component}_forecast_effective_share_band_pp",
            f"{_component}_debug_hidden_true_potential_share_pct",
            f"{_component}_debug_hidden_true_airline_offered_capacity_million",
            f"{_component}_debug_hidden_true_airline_supply_share_pct",
            f"{_component}_debug_hidden_true_airline_supply_fulfillment_pct",
            f"{_component}_debug_hidden_true_airline_supply_gap_million",
            f"{_component}_debug_hidden_true_inside_forecast_range",
            f"debug_hidden_signal_{_component}_demand_direction",
            f"debug_hidden_signal_{_component}_supply_direction",
        ]
    )


def stable_unit_float(*parts: Any) -> float:
    raw = "::".join(str(part) for part in parts).encode("utf-8")
    digest = hashlib.sha256(raw).digest()
    return int.from_bytes(digest[:8], "big") / float(1 << 64)


def interpolate(low: float, high: float, unit: float) -> float:
    return low + (high - low) * clamp(unit, 0.0, 1.0)


def round_record(record: dict[str, Any]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key, value in record.items():
        if isinstance(value, float):
            output[key] = round(value, 4)
        else:
            output[key] = value
    return output


def rows_by_year(rows: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    return {int(as_float(row, "year")): row for row in rows}


def row_for_year(row_map: dict[int, dict[str, Any]], year: int) -> dict[str, Any]:
    if year in row_map:
        return row_map[year]
    available = sorted(row_map)
    if not available:
        return {}
    closest = min(available, key=lambda item: abs(item - year))
    return row_map[closest]


def market_values(row: dict[str, Any]) -> dict[str, float | str]:
    potential = as_float(row, "city_potential_passengers_million")
    airline_supply = as_float(
        row,
        "city_airline_offered_capacity_million",
        as_float(row, "city_airline_supply_passengers_million", potential),
    )
    effective = as_float(
        row,
        "city_airline_serviceable_supply_million",
        min(potential, airline_supply),
    )
    effective = min(potential, airline_supply, max(0.0, effective))
    if potential <= 0.0 and airline_supply <= 0.0:
        bottleneck = "unknown"
    elif potential <= airline_supply:
        bottleneck = "demand_limited"
    else:
        bottleneck = "airline_supply_limited"
    return {
        "potential": potential,
        "airline_supply": airline_supply,
        "effective": effective,
        "bottleneck": bottleneck,
    }


def component_market_values(row: dict[str, Any]) -> dict[str, dict[str, float]]:
    output: dict[str, dict[str, float]] = {}
    for component in COMPONENTS:
        potential = as_float(row, f"{component}_passengers_million")
        offered = max(
            0.0,
            as_float(
                row,
                f"{component}_airline_offered_capacity_million",
                as_float(row, f"{component}_airline_supply_passengers_million", potential),
            ),
        )
        airline_supply = min(
            potential,
            max(
                0.0,
                as_float(row, f"{component}_airline_supply_passengers_million", potential),
            ),
        )
        output[component] = {
            "potential": potential,
            "offered": offered,
            "airline_supply": airline_supply,
            "effective": airline_supply,
            "priority_weight": max(
                0.0,
                as_float(
                    row,
                    f"{component}_airline_supply_priority_weight",
                    safe_divide(airline_supply, potential, 1.0),
                ),
            ),
            "potential_share_pct": 0.0,
            "airline_supply_share_pct": 0.0,
            "fulfillment_pct": safe_divide(airline_supply, potential, 1.0) * 100.0,
            "gap": max(0.0, potential - airline_supply),
            "effective_share_pct": 0.0,
        }
    potential_total = sum(item["potential"] for item in output.values())
    supply_total = sum(item["airline_supply"] for item in output.values())
    effective_total = sum(item["effective"] for item in output.values())
    for component in COMPONENTS:
        output[component]["potential_share_pct"] = safe_divide(
            output[component]["potential"],
            potential_total,
            1.0 / len(COMPONENTS),
        ) * 100.0
        output[component]["airline_supply_share_pct"] = safe_divide(
            output[component]["airline_supply"],
            supply_total,
            1.0 / len(COMPONENTS),
        ) * 100.0
        output[component]["effective_share_pct"] = safe_divide(
            output[component]["effective"],
            effective_total,
            1.0 / len(COMPONENTS),
        ) * 100.0
    return output


def component_potential_share_map(row: dict[str, Any]) -> dict[str, float]:
    values = component_market_values(row)
    return normalize_share_map(
        {component: values[component]["potential"] for component in COMPONENTS}
    )


def component_priority_share_map(row: dict[str, Any]) -> dict[str, float]:
    values = component_market_values(row)
    return normalize_share_map(
        {component: values[component]["priority_weight"] for component in COMPONENTS}
    )


def market_value_for_metric(row: dict[str, Any], metric: str) -> float:
    values = market_values(row)
    if metric == "airline_supply":
        return float(values["airline_supply"])
    if metric == "effective":
        return float(values["effective"])
    return float(values["potential"])


def cagr_pct(start_value: float, end_value: float, years: int, fallback_pct: float) -> float:
    if years <= 0 or start_value <= 0.0 or end_value <= 0.0:
        return fallback_pct
    return (math.pow(end_value / start_value, 1.0 / years) - 1.0) * 100.0


def interpolate_points(points: list[dict[str, Any]], horizon: float, default: float) -> float:
    if not points:
        return default
    ordered = sorted(
        (
            {
                "horizon_years": float(item.get("horizon_years", 0.0)),
                "value": float(item.get("value", default)),
            }
            for item in points
        ),
        key=lambda item: item["horizon_years"],
    )
    if horizon <= ordered[0]["horizon_years"]:
        return ordered[0]["value"]
    if horizon >= ordered[-1]["horizon_years"]:
        return ordered[-1]["value"]
    for left, right in zip(ordered, ordered[1:]):
        if left["horizon_years"] <= horizon <= right["horizon_years"]:
            span = right["horizon_years"] - left["horizon_years"]
            if span <= 0:
                return left["value"]
            unit = (horizon - left["horizon_years"]) / span
            return interpolate(left["value"], right["value"], unit)
    return default


def forecast_horizons_for_tier(tier: dict[str, Any], forecast_settings: dict[str, Any]) -> list[int]:
    configured = tier.get("forecast_horizon_years", forecast_settings.get("forecast_horizon_years"))
    if configured:
        return sorted({int(value) for value in configured if int(value) > 0})

    max_horizon = tier.get("forecast_horizon_max_years", forecast_settings.get("forecast_horizon_max_years"))
    if max_horizon is not None:
        start = max(1, int(tier.get("forecast_horizon_min_years", forecast_settings.get("forecast_horizon_min_years", 1))))
        end = max(start, int(max_horizon))
        step = max(1, int(tier.get("forecast_horizon_step_years", forecast_settings.get("forecast_horizon_step_years", 1))))
        return list(range(start, end + 1, step))

    return [5, 10, 15, 20]


def naive_public_curve(
    row_map: dict[int, dict[str, Any]],
    as_of_year: int,
    target_year: int,
    config: dict[str, Any],
    metric: str = "potential",
) -> float:
    forecast_settings = config.get("forecast", {})
    as_of_row = row_for_year(row_map, as_of_year)
    if metric == "effective":
        return min(
            naive_public_curve(row_map, as_of_year, target_year, config, "potential"),
            naive_public_curve(row_map, as_of_year, target_year, config, "airline_supply"),
        )
    current = market_value_for_metric(as_of_row, metric)
    lookback_years = int(forecast_settings.get("naive_history_years", 5))
    start_year = max(min(row_map), as_of_year - lookback_years)
    start = market_value_for_metric(row_for_year(row_map, start_year), metric) or current
    recent_growth = cagr_pct(start, current, max(1, as_of_year - start_year), float(forecast_settings.get("naive_long_term_growth_pct", 1.5)))
    if metric == "airline_supply":
        previous_supply = market_value_for_metric(row_for_year(row_map, max(min(row_map), as_of_year - 1)), metric) or current
        annual_signal = safe_divide(current - previous_supply, previous_supply, recent_growth / 100.0) * 100.0
    else:
        annual_signal = as_float(
            as_of_row,
            "city_air_demand_growth_pct",
            as_float(as_of_row, "source_regional_air_demand_growth_pct", recent_growth),
        )
    long_term_growth = float(forecast_settings.get("naive_long_term_growth_pct", 1.5))
    horizon = max(0, target_year - as_of_year)
    trend_weight = clamp(1.0 - horizon / float(forecast_settings.get("naive_trend_fade_years", 24.0)), 0.25, 0.75)
    blended_growth = (
        0.62 * trend_weight * recent_growth
        + 0.22 * trend_weight * annual_signal
        + (1.0 - 0.84 * trend_weight) * long_term_growth
    )
    blended_growth = clamp(
        blended_growth,
        float(forecast_settings.get("naive_growth_floor_pct", -3.0)),
        float(forecast_settings.get("naive_growth_cap_pct", 5.5)),
    )
    return max(0.0, current * math.pow(1.0 + blended_growth / 100.0, horizon))


def forecast_band_pct(tier: dict[str, Any], horizon: float) -> float:
    points = tier.get("reported_error_band_points") or tier.get("reported_band_points") or tier.get("error_band_points", [])
    return interpolate_points(points, horizon, float(tier.get("default_reported_error_band_pct", tier.get("default_error_band_pct", 15.0))))


def reported_confidence_pct(tier: dict[str, Any], horizon: int, future_peek: bool) -> float:
    if future_peek:
        return 100.0
    base = float(tier.get("reported_confidence_base_pct", 64.0))
    decay = float(tier.get("reported_confidence_horizon_decay_pct", 1.1))
    noise = interpolate(
        -float(tier.get("reported_confidence_noise_pct", 4.0)),
        float(tier.get("reported_confidence_noise_pct", 4.0)),
        stable_unit_float(
            "reported_confidence",
            tier.get("forecast_report_id"),
            horizon,
            tier.get("forecast_report_source"),
        ),
    )
    return clamp(base - decay * horizon + noise, 12.0, 96.0)


def effective_quality_score(
    tier: dict[str, Any],
    seed: int,
    market_id: str,
    as_of_year: int,
    target_year: int,
) -> float:
    if bool(tier.get("future_peek_mode", False)):
        return 100.0
    configured = float(tier.get("forecast_quality_score", 0.0))
    dynamic = tier.get("dynamic_quality", {})
    if isinstance(dynamic, dict) and dynamic.get("enabled", False):
        low = float(dynamic.get("min_score", configured))
        high = float(dynamic.get("max_score", configured))
        scope = str(dynamic.get("scope", "as_of_and_horizon"))
        parts: tuple[Any, ...]
        if scope == "report":
            parts = ("dynamic_quality", tier.get("forecast_report_id"), seed, market_id)
        elif scope == "as_of":
            parts = ("dynamic_quality", tier.get("forecast_report_id"), seed, market_id, as_of_year)
        else:
            parts = ("dynamic_quality", tier.get("forecast_report_id"), seed, market_id, as_of_year, target_year)
        configured = interpolate(low, high, stable_unit_float(*parts))
    return clamp(configured, 0.0, 70.0)


def quality_ratio(quality: float) -> float:
    return clamp(quality / 70.0, 0.0, 1.0)


def seed_signal_capture_pct(tier: dict[str, Any], quality: float, future_peek: bool) -> float:
    if future_peek:
        return 100.0
    if tier.get("derive_seed_signal_from_quality", False):
        return interpolate(
            float(tier.get("seed_signal_min_pct", 15.0)),
            float(tier.get("seed_signal_max_pct", 70.0)),
            quality_ratio(quality),
        )
    return clamp(float(tier.get("seed_signal_capture_pct", 0.0)), 0.0, 70.0)


def deterministic_bias_cap_pct(tier: dict[str, Any], quality: float) -> float:
    if tier.get("derive_bias_cap_from_quality", False):
        return interpolate(
            float(tier.get("bias_cap_at_score_0_pct", 18.0)),
            float(tier.get("bias_cap_at_score_70_pct", 3.5)),
            quality_ratio(quality),
        )
    return float(tier.get("deterministic_bias_cap_pct", 7.0))


def oriented_bias_pct(tier: dict[str, Any], cap: float, unit: float) -> float:
    direction = str(tier.get("forecast_bias_direction", "mixed"))
    if direction == "optimistic":
        return interpolate(0.0, cap, unit)
    if direction == "pessimistic":
        return interpolate(-cap, 0.0, unit)
    if direction == "mostly_optimistic":
        return interpolate(-0.25 * cap, cap, unit)
    if direction == "mostly_pessimistic":
        return interpolate(-cap, 0.25 * cap, unit)
    return interpolate(-cap, cap, unit)


def reliability_label(confidence: float, future_peek: bool) -> str:
    if future_peek:
        return "future_peek"
    if confidence >= 76.0:
        return "high"
    if confidence >= 58.0:
        return "medium"
    if confidence >= 40.0:
        return "low"
    return "speculative"


def momentum_label(current: float, forecast_mid: float, horizon: int) -> str:
    growth = cagr_pct(current, forecast_mid, max(1, horizon), 0.0)
    if growth >= 3.2:
        return "strong_upside"
    if growth >= 1.8:
        return "upside"
    if growth <= -1.0:
        return "strong_downside"
    if growth <= 0.3:
        return "downside"
    return "balanced"


def long_term_tier_label(potential_million: float) -> str:
    if potential_million >= 300.0:
        return "global_super_gateway"
    if potential_million >= 180.0:
        return "global_core_gateway"
    if potential_million >= 110.0:
        return "national_core_gateway"
    if potential_million >= 70.0:
        return "strong_regional_hub"
    if potential_million >= 40.0:
        return "regional_growth_gateway"
    return "local_or_specialized_market"


def factor_tags(source_row: dict[str, Any], forecast_mid: float, current: float, horizon: int) -> tuple[str, str]:
    upside: list[str] = []
    downside: list[str] = []
    seed_label = str(source_row.get("seed_city_momentum_label") or "balanced")
    if seed_label in {"strong_upside", "upside"}:
        upside.append(f"seed_city_{seed_label}")
    if seed_label in {"strong_downside", "downside"}:
        downside.append(f"seed_city_{seed_label}")
    growth = cagr_pct(current, forecast_mid, max(1, horizon), 0.0)
    if growth >= 2.0:
        upside.append("forecast_growth_above_mature_trend")
    elif growth <= 0.5:
        downside.append("forecast_growth_below_mature_trend")
    demand_regime = str(source_row.get("city_demand_regime") or "")
    if "growth" in demand_regime and "slow" not in demand_regime:
        upside.append(demand_regime)
    if "slow" in demand_regime or "shock" in demand_regime:
        downside.append(demand_regime)
    if not upside:
        upside.append("no_clear_upside_signal")
    if not downside:
        downside.append("no_clear_downside_signal")
    return ";".join(upside), ";".join(downside)


def market_bottleneck_from_values(potential: float, airline_supply: float) -> str:
    return "demand_limited" if potential <= airline_supply else "airline_supply_limited"


def normalize_share_map(values: dict[str, float]) -> dict[str, float]:
    clean = {component: max(0.0, values.get(component, 0.0)) for component in COMPONENTS}
    total = sum(clean.values())
    if total <= 0.0:
        return {component: 1.0 / len(COMPONENTS) for component in COMPONENTS}
    return {component: clean[component] / total for component in COMPONENTS}


def effective_component_share_map(row: dict[str, Any]) -> dict[str, float]:
    component_values = component_market_values(row)
    total = sum(item["effective"] for item in component_values.values())
    if total <= 0.0:
        return {component: 1.0 / len(COMPONENTS) for component in COMPONENTS}
    return {component: component_values[component]["effective"] / total for component in COMPONENTS}


DIRECTION_BUCKETS = (
    ("strong_decline", -2.6),
    ("decline", -0.8),
    ("stable", 0.4),
    ("moderate_growth", 1.7),
    ("strong_growth", 3.2),
)
DIRECTION_INDEX = {label: index for index, (label, _) in enumerate(DIRECTION_BUCKETS)}
DIRECTION_CENTER = dict(DIRECTION_BUCKETS)
COMPONENT_SHIFT_CENTER = {
    "down": -0.018,
    "stable": 0.0,
    "up": 0.018,
    "unclear": 0.0,
}


def direction_bucket(growth_pct: float) -> str:
    if growth_pct <= -1.4:
        return "strong_decline"
    if growth_pct <= -0.1:
        return "decline"
    if growth_pct < 1.0:
        return "stable"
    if growth_pct < 2.5:
        return "moderate_growth"
    return "strong_growth"


def component_shift_bucket(shift_pp: float) -> str:
    if shift_pp <= -1.25:
        return "down"
    if shift_pp >= 1.25:
        return "up"
    return "stable"


def annual_metric_growth_series(
    row_map: dict[int, dict[str, Any]],
    as_of_year: int,
    end_year: int,
    metric: str,
) -> list[tuple[int, float]]:
    output: list[tuple[int, float]] = []
    previous = market_value_for_metric(row_for_year(row_map, as_of_year), metric)
    for year in range(as_of_year + 1, end_year + 1):
        current = market_value_for_metric(row_for_year(row_map, year), metric)
        growth = safe_divide(current - previous, previous, 0.0) * 100.0
        output.append((year, growth))
        previous = current
    return output


def detect_hidden_turn(
    row_map: dict[int, dict[str, Any]],
    as_of_year: int,
    end_year: int,
    metric: str,
) -> tuple[int | None, str]:
    series = annual_metric_growth_series(row_map, as_of_year, end_year, metric)
    if len(series) < 3:
        return None, "none"
    candidates: list[tuple[float, int, str]] = []
    previous_growth = series[0][1]
    for year, growth in series[1:]:
        acceleration = growth - previous_growth
        if abs(acceleration) >= 1.15:
            direction = "acceleration" if acceleration > 0.0 else "deceleration"
            sign_bonus = 1.4 if previous_growth * growth < 0.0 else 1.0
            candidates.append((abs(acceleration) * sign_bonus, year, direction))
        previous_growth = growth
    if not candidates:
        return None, "none"
    _, year, direction = max(candidates, key=lambda item: (item[0], -item[1]))
    return year, direction


def build_hidden_signal_packet(
    row_map: dict[int, dict[str, Any]],
    as_of_year: int,
    max_horizon: int,
) -> dict[str, Any]:
    end_year = min(max(row_map), as_of_year + max(1, max_horizon))
    years = max(1, end_year - as_of_year)
    current_row = row_for_year(row_map, as_of_year)
    end_row = row_for_year(row_map, end_year)
    current_values = market_values(current_row)
    end_values = market_values(end_row)
    demand_growth = cagr_pct(
        float(current_values["potential"]),
        float(end_values["potential"]),
        years,
        0.0,
    )
    supply_growth = cagr_pct(
        float(current_values["airline_supply"]),
        float(end_values["airline_supply"]),
        years,
        0.0,
    )
    demand_turn_year, demand_turn_direction = detect_hidden_turn(
        row_map,
        as_of_year,
        end_year,
        "potential",
    )
    supply_turn_year, supply_turn_direction = detect_hidden_turn(
        row_map,
        as_of_year,
        end_year,
        "airline_supply",
    )
    turn_candidates = [
        (year, direction, metric)
        for year, direction, metric in (
            (supply_turn_year, supply_turn_direction, "airline_supply"),
            (demand_turn_year, demand_turn_direction, "potential_demand"),
        )
        if year is not None
    ]
    turn_year: int | None = None
    turn_direction = "none"
    turn_driver = "none"
    if turn_candidates:
        turn_year, turn_direction, turn_driver = min(
            turn_candidates,
            key=lambda item: (int(item[0]), 0 if item[2] == "airline_supply" else 1),
        )

    current_components = effective_component_share_map(current_row)
    end_components = effective_component_share_map(end_row)
    current_demand_components = component_potential_share_map(current_row)
    end_demand_components = component_potential_share_map(end_row)
    current_supply_priorities = component_priority_share_map(current_row)
    end_supply_priorities = component_priority_share_map(end_row)
    component_directions = {
        component: component_shift_bucket(
            (end_components[component] - current_components[component]) * 100.0
        )
        for component in COMPONENTS
    }
    component_demand_directions = {
        component: component_shift_bucket(
            (end_demand_components[component] - current_demand_components[component])
            * 100.0
        )
        for component in COMPONENTS
    }
    component_supply_directions = {
        component: component_shift_bucket(
            (end_supply_priorities[component] - current_supply_priorities[component])
            * 100.0
        )
        for component in COMPONENTS
    }
    return {
        "demand_direction": direction_bucket(demand_growth),
        "supply_direction": direction_bucket(supply_growth),
        "turn_year": turn_year,
        "turn_direction": turn_direction,
        "turn_driver": turn_driver,
        "component_directions": component_directions,
        "component_demand_directions": component_demand_directions,
        "component_supply_directions": component_supply_directions,
    }


def degraded_direction_label(
    label: str,
    *,
    tier: dict[str, Any],
    quality: float,
    seed: int,
    market_id: str,
    as_of_year: int,
    report_id: str,
    signal_name: str,
) -> str:
    ability = clamp(
        0.45 * quality_ratio(quality)
        + 0.55 * float(tier.get("signal_observation_quality", 0.5)),
        0.0,
        1.0,
    )
    miss_rate = float(tier.get("signal_miss_rate", 0.15)) * (1.25 - 0.65 * ability)
    miss_unit = stable_unit_float(
        "forecast_signal_miss",
        signal_name,
        report_id,
        seed,
        market_id,
        as_of_year,
    )
    if miss_unit < miss_rate:
        return "unclear"
    misclassification_rate = (
        float(tier.get("signal_misclassification_rate", 0.1))
        * (1.2 - 0.55 * ability)
    )
    classify_unit = stable_unit_float(
        "forecast_signal_classification",
        signal_name,
        report_id,
        seed,
        market_id,
        as_of_year,
    )
    if classify_unit >= misclassification_rate or label not in DIRECTION_INDEX:
        return label
    shift_unit = stable_unit_float(
        "forecast_signal_classification_shift",
        signal_name,
        report_id,
        seed,
        market_id,
        as_of_year,
    )
    shift = -1 if shift_unit < 0.5 else 1
    index = int(clamp(DIRECTION_INDEX[label] + shift, 0, len(DIRECTION_BUCKETS) - 1))
    return DIRECTION_BUCKETS[index][0]


def degrade_component_direction(
    label: str,
    *,
    tier: dict[str, Any],
    quality: float,
    seed: int,
    market_id: str,
    as_of_year: int,
    report_id: str,
    component: str,
) -> str:
    ability = clamp(
        0.5 * quality_ratio(quality)
        + 0.5 * float(tier.get("component_signal_quality", 0.5)),
        0.0,
        1.0,
    )
    unit = stable_unit_float(
        "forecast_component_signal",
        component,
        report_id,
        seed,
        market_id,
        as_of_year,
    )
    if unit < 0.22 * (1.0 - ability):
        return "unclear"
    if unit > 1.0 - 0.15 * (1.0 - ability):
        return {"up": "down", "down": "up"}.get(label, label)
    return label


def observe_hidden_signal_packet(
    raw: dict[str, Any],
    *,
    tier: dict[str, Any],
    quality: float,
    seed: int,
    market_id: str,
    as_of_year: int,
    report_id: str,
) -> dict[str, Any]:
    demand_direction = degraded_direction_label(
        str(raw.get("demand_direction") or "stable"),
        tier=tier,
        quality=quality,
        seed=seed,
        market_id=market_id,
        as_of_year=as_of_year,
        report_id=report_id,
        signal_name="potential_demand",
    )
    supply_direction = degraded_direction_label(
        str(raw.get("supply_direction") or "stable"),
        tier=tier,
        quality=quality,
        seed=seed,
        market_id=market_id,
        as_of_year=as_of_year,
        report_id=report_id,
        signal_name="airline_supply",
    )
    ability = clamp(
        0.45 * quality_ratio(quality)
        + 0.55 * float(tier.get("signal_observation_quality", 0.5)),
        0.0,
        1.0,
    )
    raw_turn_year = raw.get("turn_year")
    turn_year: int | None = None
    turn_direction = str(raw.get("turn_direction") or "none")
    if raw_turn_year is not None:
        turn_miss_unit = stable_unit_float(
            "forecast_turn_signal_miss",
            report_id,
            seed,
            market_id,
            as_of_year,
        )
        if turn_miss_unit >= float(tier.get("signal_miss_rate", 0.15)) * (1.15 - 0.55 * ability):
            max_error = max(0, int(tier.get("turn_window_error_years", 2)))
            error_unit = stable_unit_float(
                "forecast_turn_signal_error",
                report_id,
                seed,
                market_id,
                as_of_year,
            )
            error = int(round(interpolate(-max_error, max_error, error_unit) * (1.1 - 0.45 * ability)))
            coarse_year = as_of_year + int(round((int(raw_turn_year) - as_of_year) / 2.0) * 2)
            turn_year = max(as_of_year + 1, coarse_year + error)
        else:
            turn_direction = "none"
    component_directions = {
        component: degrade_component_direction(
            str(raw.get("component_directions", {}).get(component) or "stable"),
            tier=tier,
            quality=quality,
            seed=seed,
            market_id=market_id,
            as_of_year=as_of_year,
            report_id=report_id,
            component=component,
        )
        for component in COMPONENTS
    }
    component_demand_directions = {
        component: degrade_component_direction(
            str(
                raw.get("component_demand_directions", {}).get(component)
                or raw.get("component_directions", {}).get(component)
                or "stable"
            ),
            tier=tier,
            quality=quality,
            seed=seed,
            market_id=market_id,
            as_of_year=as_of_year,
            report_id=report_id,
            component=f"{component}:demand",
        )
        for component in COMPONENTS
    }
    component_supply_directions = {
        component: degrade_component_direction(
            str(
                raw.get("component_supply_directions", {}).get(component)
                or raw.get("component_directions", {}).get(component)
                or "stable"
            ),
            tier=tier,
            quality=quality,
            seed=seed,
            market_id=market_id,
            as_of_year=as_of_year,
            report_id=report_id,
            component=f"{component}:supply",
        )
        for component in COMPONENTS
    }
    confidence = clamp(
        100.0
        * (
            0.52 * ability
            + 0.24 * (demand_direction != "unclear")
            + 0.18 * (supply_direction != "unclear")
            + 0.06 * (turn_year is not None)
        ),
        5.0,
        96.0,
    )
    window_radius = max(1, int(tier.get("turn_window_error_years", 2)))
    return {
        "demand_direction": demand_direction,
        "supply_direction": supply_direction,
        "turn_year": turn_year,
        "turn_window_start_year": turn_year - window_radius if turn_year else None,
        "turn_window_end_year": turn_year + window_radius if turn_year else None,
        "turn_direction": turn_direction,
        "turn_driver": str(raw.get("turn_driver") or "none"),
        "component_directions": component_directions,
        "component_demand_directions": component_demand_directions,
        "component_supply_directions": component_supply_directions,
        "confidence_pct": confidence,
    }


def signal_growth_center(label: str, fallback: float) -> float:
    return float(DIRECTION_CENTER.get(label, fallback))


def signal_packet_changed(
    previous: dict[str, Any] | None,
    current: dict[str, Any],
) -> bool:
    if not previous:
        return True
    direction_changed = any(
        previous.get(key) != current.get(key)
        for key in ("demand_direction", "supply_direction", "turn_direction")
    )
    component_changed = any(
        previous.get(key) != current.get(key)
        for key in ("component_demand_directions", "component_supply_directions")
    )
    return direction_changed or component_changed or abs(
        int(previous.get("turn_year") or 0) - int(current.get("turn_year") or 0)
    ) >= 2


def narrative_state(
    tier: dict[str, Any],
    signal: dict[str, Any],
    previous_signal: dict[str, Any] | None,
    previous_surprise_pct: float,
) -> dict[str, Any]:
    demand = str(signal.get("demand_direction") or "unclear")
    supply = str(signal.get("supply_direction") or "unclear")
    if demand in {"moderate_growth", "strong_growth"} and supply in {"decline", "strong_decline"}:
        headline = "需求仍有增长基础，但航司供给可能在中期形成约束"
        regime = "demand_growth_with_supply_constraint"
        primary = "airline_supply_cycle"
        secondary = "city_demand_growth"
    elif demand in {"decline", "strong_decline"}:
        headline = "需求基本面转弱，供给扩张也难以完全转化为有效客流"
        regime = "demand_slowdown"
        primary = "city_demand_slowdown"
        secondary = "airline_capacity_response"
    elif supply in {"moderate_growth", "strong_growth"}:
        headline = "航司供给保持扩张，市场承接能力取决于需求能否同步兑现"
        regime = "supply_expansion"
        primary = "airline_supply_expansion"
        secondary = "city_demand_realization"
    elif signal.get("turn_year") is not None:
        headline = "总量趋势相对平稳，但中期周期转向值得重点关注"
        regime = "turning_window"
        primary = str(signal.get("turn_driver") or "market_cycle")
        secondary = "stable_city_fundamentals"
    else:
        headline = "市场大体沿成熟趋势运行，暂未观察到明确结构性转向"
        regime = "mature_stable_growth"
        primary = "mature_market_trend"
        secondary = "long_term_mean_reversion"

    changed = signal_packet_changed(previous_signal, signal)
    if previous_signal is None:
        revision_reason = "initial_report"
    elif previous_surprise_pct >= 4.0:
        revision_reason = "realized_result_above_previous_view"
    elif previous_surprise_pct <= -4.0:
        revision_reason = "realized_result_below_previous_view"
    elif previous_signal.get("supply_direction") != signal.get("supply_direction"):
        revision_reason = "airline_supply_signal_changed"
    elif previous_signal.get("demand_direction") != signal.get("demand_direction"):
        revision_reason = "city_demand_signal_changed"
    elif changed:
        revision_reason = "turning_window_shifted"
    else:
        revision_reason = "routine_inherited_update"
    conviction = clamp(
        0.48 * float(signal.get("confidence_pct", 50.0))
        + 0.52 * float(tier.get("reported_confidence_base_pct", 65.0)),
        10.0,
        96.0,
    )
    return {
        "headline": headline,
        "expected_regime": regime,
        "primary_driver": primary,
        "secondary_driver": secondary,
        "revision_reason": revision_reason,
        "conviction_pct": conviction,
    }


def report_path_biases(
    tier: dict[str, Any],
    quality: float,
    *,
    seed: int,
    market_id: str,
    as_of_year: int,
    report_id: str,
    metric: str,
) -> tuple[float, float]:
    cap = deterministic_bias_cap_pct(tier, quality)
    if metric == "airline_supply":
        cap *= float(tier.get("airline_supply_bias_multiplier", 1.25))
    unit = stable_unit_float(
        "narrative_path_bias",
        metric,
        report_id,
        seed,
        market_id,
        as_of_year,
    )
    bias_pct = oriented_bias_pct(tier, cap, unit)
    herding_cap = float(tier.get("consensus_herding_bias_cap_pct", 0.0))
    herding_unit = stable_unit_float(
        "narrative_path_herding",
        metric,
        report_id,
        seed,
        market_id,
        as_of_year,
    )
    herding_pct = interpolate(-herding_cap, herding_cap, herding_unit)
    return bias_pct, herding_pct


def build_joint_metric_path(
    row_map: dict[int, dict[str, Any]],
    as_of_year: int,
    horizons: list[int],
    config: dict[str, Any],
    tier: dict[str, Any],
    signal: dict[str, Any],
    quality: float,
    capture_pct: float,
    *,
    metric: str,
    seed: int,
    future_peek: bool,
) -> dict[str, Any]:
    if future_peek:
        values = {
            horizon: market_value_for_metric(row_for_year(row_map, as_of_year + horizon), metric)
            for horizon in horizons
        }
        return {
            "values": values,
            "naive": dict(values),
            "bias_pct": 0.0,
            "herding_bias_pct": 0.0,
        }
    forecast_settings = config.get("forecast", {})
    current = market_value_for_metric(row_for_year(row_map, as_of_year), metric)
    max_horizon = max(horizons)
    lookback_years = int(forecast_settings.get("naive_history_years", 5))
    start_year = max(min(row_map), as_of_year - lookback_years)
    recent = cagr_pct(
        market_value_for_metric(row_for_year(row_map, start_year), metric),
        current,
        max(1, as_of_year - start_year),
        float(forecast_settings.get("naive_long_term_growth_pct", 1.6)),
    )
    long_term = float(forecast_settings.get("naive_long_term_growth_pct", 1.6))
    direction_key = "supply_direction" if metric == "airline_supply" else "demand_direction"
    signal_center = signal_growth_center(str(signal.get(direction_key) or "unclear"), long_term)
    signal_weight_key = (
        "narrative_supply_signal_weight"
        if metric == "airline_supply"
        else "narrative_demand_signal_weight"
    )
    observation = float(tier.get("signal_observation_quality", 0.5))
    signal_weight = clamp(
        capture_pct
        / 100.0
        * (0.52 + 0.48 * observation)
        * (0.55 + 0.55 * float(tier.get(signal_weight_key, 0.5))),
        0.0,
        0.82,
    )
    trend_weight = float(tier.get("narrative_trend_extrapolation", 0.5))
    mean_reversion = float(tier.get("narrative_mean_reversion", 0.4))
    style_growth = (
        recent * trend_weight
        + long_term * mean_reversion
        + long_term * max(0.0, 1.0 - trend_weight - mean_reversion)
    )
    narrative_bias_pp = float(
        tier.get(
            "narrative_supply_bias_pct"
            if metric == "airline_supply"
            else "narrative_growth_bias_pct",
            0.0,
        )
    )
    report_id = str(tier.get("forecast_report_id"))
    bias_pct, herding_pct = report_path_biases(
        tier,
        quality,
        seed=seed,
        market_id=str(config["city_airport_market_id"]),
        as_of_year=as_of_year,
        report_id=report_id,
        metric=metric,
    )
    persistent_bias_pp = (bias_pct + herding_pct) / max(4.0, max_horizon * 0.85)
    turn_year = signal.get("turn_year")
    turn_direction = str(signal.get("turn_direction") or "none")
    turn_sensitivity = float(tier.get("narrative_turn_sensitivity", 0.5))
    max_growth_change = float(tier.get("max_annual_growth_change_pp", 2.0))

    naive_values = {
        horizon: naive_public_curve(
            row_map,
            as_of_year,
            as_of_year + horizon,
            config,
            metric,
        )
        for horizon in horizons
    }
    values: dict[int, float] = {}
    previous_value = current
    previous_growth = cagr_pct(
        current,
        naive_values[horizons[0]],
        max(1, horizons[0]),
        style_growth,
    )
    growth_direction = 0
    growth_inflections = 0
    max_inflections = max(0, int(tier.get("max_unexplained_inflections", 2)))
    inflection_materiality = float(tier.get("inflection_materiality_pp", 0.35))
    for horizon in horizons:
        target_year = as_of_year + horizon
        previous_naive = current if horizon == 1 else naive_values.get(
            horizon - 1,
            naive_public_curve(row_map, as_of_year, target_year - 1, config, metric),
        )
        base_step_growth = cagr_pct(
            previous_naive,
            naive_values[horizon],
            1,
            style_growth,
        )
        signal_fade = 1.0 - 0.42 * max(0, horizon - 1) / max(1, max_horizon - 1)
        desired_growth = (
            (1.0 - signal_weight) * (0.72 * base_step_growth + 0.28 * style_growth)
            + signal_weight * (signal_center * signal_fade + long_term * (1.0 - signal_fade))
            + narrative_bias_pp
            + persistent_bias_pp
        )
        if turn_year is not None:
            distance = target_year - int(turn_year)
            transition = math.tanh(distance / 1.8)
            turn_effect = 0.85 * turn_sensitivity * transition
            if turn_direction == "deceleration":
                desired_growth -= turn_effect
            elif turn_direction == "acceleration":
                desired_growth += turn_effect
        growth = clamp(
            desired_growth,
            previous_growth - max_growth_change,
            previous_growth + max_growth_change,
        )
        growth = clamp(
            growth,
            float(forecast_settings.get("naive_growth_floor_pct", -2.5)) - 4.0,
            float(forecast_settings.get("naive_growth_cap_pct", 5.0)) + 5.0,
        )
        growth_delta = growth - previous_growth
        candidate_direction = (
            1
            if growth_delta > inflection_materiality
            else -1
            if growth_delta < -inflection_materiality
            else 0
        )
        if candidate_direction:
            if growth_direction == 0:
                growth_direction = candidate_direction
            elif candidate_direction != growth_direction:
                if growth_inflections >= max_inflections:
                    growth = previous_growth + growth_direction * min(
                        abs(growth_delta),
                        inflection_materiality,
                    )
                else:
                    growth_inflections += 1
                    growth_direction = candidate_direction
        value = max(0.0, previous_value * (1.0 + growth / 100.0))
        values[horizon] = value
        previous_value = value
        previous_growth = growth
    return {
        "values": values,
        "naive": naive_values,
        "bias_pct": bias_pct,
        "herding_bias_pct": herding_pct,
    }


def previous_vintage_surprise_pct(
    previous_state: dict[str, Any] | None,
    as_of_year: int,
    current_effective: float,
) -> float:
    if not previous_state or current_effective <= 0.0:
        return 0.0
    previous_row = previous_state.get("by_target_year", {}).get(as_of_year)
    if not previous_row:
        return 0.0
    previous_mid = float(previous_row.get("effective", current_effective))
    return safe_divide(current_effective - previous_mid, current_effective, 0.0) * 100.0


def inherit_previous_vintage(
    fresh_potential: dict[int, float],
    fresh_supply: dict[int, float],
    *,
    as_of_year: int,
    horizons: list[int],
    tier: dict[str, Any],
    signal: dict[str, Any],
    previous_state: dict[str, Any] | None,
    surprise_pct: float,
) -> tuple[dict[int, float], dict[int, float], dict[int, float], dict[int, float | None]]:
    if not previous_state:
        effective = {
            horizon: min(fresh_potential[horizon], fresh_supply[horizon])
            for horizon in horizons
        }
        return fresh_potential, fresh_supply, {horizon: 0.0 for horizon in horizons}, {
            horizon: None for horizon in horizons
        }
    changed = signal_packet_changed(previous_state.get("signal"), signal)
    speed = clamp(
        float(tier.get("narrative_revision_speed", tier.get("base_revision_speed", 0.35))),
        0.08,
        0.92,
    )
    information_strength = clamp(
        0.18 + (0.42 if changed else 0.0) + min(abs(surprise_pct) / 12.0, 0.35),
        0.12,
        0.95,
    )
    alpha = clamp(speed * (0.55 + information_strength) + 0.08, 0.12, 0.92)
    previous_by_target = previous_state.get("by_target_year", {})
    potential: dict[int, float] = {}
    supply: dict[int, float] = {}
    revisions: dict[int, float] = {}
    previous_midpoints: dict[int, float | None] = {}
    for horizon in horizons:
        target_year = as_of_year + horizon
        prior = previous_by_target.get(target_year)
        if not prior:
            previous_horizon = horizon - 1
            if previous_horizon in potential:
                fresh_potential_step = safe_divide(
                    fresh_potential[horizon],
                    fresh_potential[previous_horizon],
                    1.0,
                )
                fresh_supply_step = safe_divide(
                    fresh_supply[horizon],
                    fresh_supply[previous_horizon],
                    1.0,
                )
                potential[horizon] = potential[previous_horizon] * fresh_potential_step
                supply[horizon] = supply[previous_horizon] * fresh_supply_step
            else:
                potential[horizon] = fresh_potential[horizon]
                supply[horizon] = fresh_supply[horizon]
            revisions[horizon] = 0.0
            previous_midpoints[horizon] = None
            continue
        potential[horizon] = float(prior["potential"]) + alpha * (
            fresh_potential[horizon] - float(prior["potential"])
        )
        supply[horizon] = float(prior["airline_supply"]) + alpha * (
            fresh_supply[horizon] - float(prior["airline_supply"])
        )
        previous_mid = float(prior["effective"])
        current_mid = min(potential[horizon], supply[horizon])
        revisions[horizon] = safe_divide(current_mid - previous_mid, previous_mid, 0.0) * 100.0
        previous_midpoints[horizon] = previous_mid
    return potential, supply, revisions, previous_midpoints


def smooth_inherited_metric_path(
    current_value: float,
    values: dict[int, float],
    horizons: list[int],
    tier: dict[str, Any],
) -> dict[int, float]:
    if not horizons:
        return {}
    max_growth_change = float(tier.get("max_annual_growth_change_pp", 2.0))
    max_inflections = max(0, int(tier.get("max_unexplained_inflections", 2)))
    growth_floor = float(tier.get("path_growth_floor_pct", -6.5))
    growth_cap = float(tier.get("path_growth_cap_pct", 10.0))
    raw_growths: list[float] = []
    previous_value = current_value
    for horizon in horizons:
        value = max(0.0, float(values[horizon]))
        raw_growths.append(
            clamp(
                safe_divide(value - previous_value, previous_value, 0.0) * 100.0,
                growth_floor,
                growth_cap,
            )
        )
        previous_value = value

    growths = [clamp(raw_growths[0], growth_floor, growth_cap)]
    for raw_growth in raw_growths[1:]:
        bounded = clamp(
            raw_growth,
            growths[-1] - max_growth_change,
            growths[-1] + max_growth_change,
        )
        growths.append(
            clamp(
                0.58 * growths[-1] + 0.42 * bounded,
                growth_floor,
                growth_cap,
            )
        )

    direction = 0
    inflections = 0
    for index in range(1, len(growths)):
        delta = growths[index] - growths[index - 1]
        candidate_direction = 1 if delta > 0.10 else -1 if delta < -0.10 else 0
        if candidate_direction == 0:
            continue
        if direction == 0:
            direction = candidate_direction
            continue
        if candidate_direction != direction:
            if inflections >= max_inflections:
                continuation = min(abs(delta), 0.16)
                growths[index] = growths[index - 1] + direction * continuation
            else:
                inflections += 1
                direction = candidate_direction

    output: dict[int, float] = {}
    previous_value = current_value
    for horizon, growth in zip(horizons, growths):
        previous_value = max(0.0, previous_value * (1.0 + growth / 100.0))
        output[horizon] = previous_value
    if current_value > 0.0 and output[horizons[-1]] > 0.0:
        max_horizon = max(horizons)
        minimum_final = current_value * math.pow(
            max(0.01, 1.0 + growth_floor / 100.0),
            max_horizon,
        )
        maximum_final = current_value * math.pow(
            1.0 + growth_cap / 100.0,
            max_horizon,
        )
        raw_final = float(values[horizons[-1]])
        target_final = clamp(
            raw_final if math.isfinite(raw_final) else maximum_final,
            minimum_final,
            maximum_final,
        )
        correction_ratio = target_final / output[horizons[-1]]
        for horizon in horizons:
            progress = horizon / max_horizon
            output[horizon] *= math.pow(correction_ratio, progress)
    return output


def build_joint_component_share_path(
    row_map: dict[int, dict[str, Any]],
    as_of_year: int,
    horizons: list[int],
    tier: dict[str, Any],
    signal: dict[str, Any],
    quality: float,
    *,
    seed: int,
    market_id: str,
    future_peek: bool,
    basis: str = "potential",
) -> dict[int, dict[str, float]]:
    if basis not in {"potential", "priority"}:
        raise ValueError(f"Unsupported component forecast basis {basis!r}")
    share_reader = (
        component_potential_share_map
        if basis == "potential"
        else component_priority_share_map
    )
    signal_key = (
        "component_demand_directions"
        if basis == "potential"
        else "component_supply_directions"
    )
    axis_quality_key = (
        "narrative_demand_signal_weight"
        if basis == "potential"
        else "narrative_supply_signal_weight"
    )
    if future_peek:
        return {
            horizon: share_reader(row_for_year(row_map, as_of_year + horizon))
            for horizon in horizons
        }
    current_share = share_reader(row_for_year(row_map, as_of_year))
    start_year = max(min(row_map), as_of_year - 5)
    start_share = share_reader(row_for_year(row_map, start_year))
    max_horizon = max(horizons)
    ability = clamp(
        0.45 * quality_ratio(quality)
        + 0.40 * float(tier.get("component_signal_quality", 0.5))
        + 0.15 * float(tier.get(axis_quality_key, 0.5)),
        0.0,
        1.0,
    )
    output: dict[int, dict[str, float]] = {}
    for horizon in horizons:
        progress = horizon / max_horizon
        raw: dict[str, float] = {}
        for component in COMPONENTS:
            historical_drift = (
                current_share[component] - start_share[component]
            ) / max(1, as_of_year - start_year)
            signal_drift = COMPONENT_SHIFT_CENTER.get(
                str(
                    signal.get(signal_key, {}).get(component)
                    or signal.get("component_directions", {}).get(component)
                    or "unclear"
                ),
                0.0,
            )
            bias_cap = interpolate(
                0.028 if basis == "potential" else 0.040,
                0.006 if basis == "potential" else 0.009,
                ability,
            )
            bias_unit = stable_unit_float(
                f"narrative_component_{basis}_path_bias",
                component,
                tier.get("forecast_report_id"),
                seed,
                market_id,
                as_of_year,
            )
            persistent_bias = interpolate(-bias_cap, bias_cap, bias_unit) * progress
            raw[component] = max(
                0.001,
                current_share[component]
                + 0.55 * historical_drift * horizon
                + ability * signal_drift * progress
                + persistent_bias,
            )
        output[horizon] = normalize_share_map(raw)
    return output


def component_revision_alpha(
    tier: dict[str, Any],
    signal: dict[str, Any],
    previous_state: dict[str, Any] | None,
    surprise_pct: float,
) -> float:
    if not previous_state:
        return 1.0
    changed = signal_packet_changed(previous_state.get("signal"), signal)
    speed = clamp(
        float(tier.get("narrative_revision_speed", tier.get("base_revision_speed", 0.35))),
        0.08,
        0.92,
    )
    information_strength = clamp(
        0.18 + (0.42 if changed else 0.0) + min(abs(surprise_pct) / 12.0, 0.35),
        0.12,
        0.95,
    )
    return clamp(speed * (0.55 + information_strength) + 0.08, 0.12, 0.92)


def inherit_previous_component_paths(
    fresh_demand_shares: dict[int, dict[str, float]],
    fresh_priority_weights: dict[int, dict[str, float]],
    *,
    as_of_year: int,
    horizons: list[int],
    tier: dict[str, Any],
    signal: dict[str, Any],
    previous_state: dict[str, Any] | None,
    surprise_pct: float,
) -> tuple[
    dict[int, dict[str, float]],
    dict[int, dict[str, float]],
    dict[int, float],
]:
    alpha = component_revision_alpha(tier, signal, previous_state, surprise_pct)
    previous_by_target = (
        previous_state.get("by_target_year", {}) if previous_state else {}
    )
    demand_paths: dict[int, dict[str, float]] = {}
    priority_paths: dict[int, dict[str, float]] = {}
    revision_pp: dict[int, float] = {}
    for horizon in horizons:
        target_year = as_of_year + horizon
        prior = previous_by_target.get(target_year)
        prior_demand = prior.get("component_demand_shares") if prior else None
        prior_priority = prior.get("component_priority_weights") if prior else None
        if not prior_demand or not prior_priority:
            demand_paths[horizon] = dict(fresh_demand_shares[horizon])
            priority_paths[horizon] = dict(fresh_priority_weights[horizon])
            revision_pp[horizon] = 0.0
            continue
        blended_demand = normalize_share_map(
            {
                component: float(prior_demand.get(component, 0.0))
                + alpha
                * (
                    fresh_demand_shares[horizon][component]
                    - float(prior_demand.get(component, 0.0))
                )
                for component in COMPONENTS
            }
        )
        blended_priority = normalize_share_map(
            {
                component: float(prior_priority.get(component, 0.0))
                + alpha
                * (
                    fresh_priority_weights[horizon][component]
                    - float(prior_priority.get(component, 0.0))
                )
                for component in COMPONENTS
            }
        )
        demand_paths[horizon] = blended_demand
        priority_paths[horizon] = blended_priority
        demand_revision = mean(
            abs(blended_demand[component] - float(prior_demand.get(component, 0.0)))
            * 100.0
            for component in COMPONENTS
        )
        priority_revision = mean(
            abs(
                blended_priority[component]
                - float(prior_priority.get(component, 0.0))
            )
            * 100.0
            for component in COMPONENTS
        )
        revision_pp[horizon] = 0.5 * demand_revision + 0.5 * priority_revision
    return demand_paths, priority_paths, revision_pp


def forecast_component_allocation(
    forecast_potential: float,
    forecast_offered_capacity: float,
    demand_shares: dict[str, float],
    priority_weights: dict[str, float],
) -> dict[str, dict[str, float]]:
    normalized_demand = normalize_share_map(demand_shares)
    normalized_priority = normalize_share_map(priority_weights)
    potential = {
        component: max(0.0, forecast_potential) * normalized_demand[component]
        for component in COMPONENTS
    }
    allocation_weights = {
        component: potential[component] * max(0.0001, normalized_priority[component])
        for component in COMPONENTS
    }
    total_allocation_weight = sum(allocation_weights.values())
    if total_allocation_weight <= 0.0:
        allocation_weights = {component: 1.0 for component in COMPONENTS}
        total_allocation_weight = float(len(COMPONENTS))
    offered = {
        component: max(0.0, forecast_offered_capacity)
        * allocation_weights[component]
        / total_allocation_weight
        for component in COMPONENTS
    }
    serviceable = capped_weighted_allocation(
        potential,
        allocation_weights,
        max(0.0, forecast_offered_capacity),
    )
    serviceable_total = sum(serviceable.values())
    output: dict[str, dict[str, float]] = {}
    for component in COMPONENTS:
        output[component] = {
            "potential": potential[component],
            "potential_share_pct": normalized_demand[component] * 100.0,
            "priority_weight": normalized_priority[component],
            "offered": offered[component],
            "serviceable": serviceable[component],
            "serviceable_share_pct": safe_divide(
                serviceable[component],
                serviceable_total,
                1.0 / len(COMPONENTS),
            )
            * 100.0,
            "fulfillment_pct": safe_divide(
                serviceable[component], potential[component], 1.0
            )
            * 100.0,
            "gap": max(0.0, potential[component] - serviceable[component]),
        }
    return output


def component_effective_interval(
    *,
    component: str,
    mid: float,
    share: float,
    total_low: float,
    total_high: float,
    horizon: int,
    quality: float,
    tier: dict[str, Any],
    future_peek: bool,
) -> tuple[float, float, float]:
    if future_peek:
        return mid, mid, 0.0
    ability = clamp(
        0.45 * quality_ratio(quality)
        + 0.55 * float(tier.get("component_signal_quality", 0.5)),
        0.0,
        1.0,
    )
    interval_multiplier = float(tier.get("narrative_interval_multiplier", 1.0))
    share_band_pp = (
        interpolate(2.8, 1.0, ability)
        * (0.88 + 0.055 * min(max(1, horizon), 12))
        * COMPONENT_SHARE_UNCERTAINTY_MULTIPLIER[component]
        * interval_multiplier
    )
    low_share = max(0.0, share - share_band_pp / 100.0)
    high_share = min(1.0, share + share_band_pp / 100.0)
    low = min(mid, max(0.0, total_low * low_share))
    high = max(mid, total_high * high_share)
    return low, high, share_band_pp


def simulate_potential_passenger_forecast(
    city_airport_rows: list[dict[str, Any]],
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    if not city_airport_rows:
        return []
    sorted_rows = sorted(
        city_airport_rows,
        key=lambda item: (int(as_float(item, "seed")), int(as_float(item, "year"))),
    )
    seed_values = sorted({int(as_float(row, "seed")) for row in sorted_rows})
    if len(seed_values) != 1:
        raise ValueError("Narrative passenger forecast expects one seed per input row set.")
    seed = seed_values[0]
    row_map = rows_by_year(sorted_rows)
    years = sorted(row_map)
    if not years:
        return []

    forecast_settings = config.get("forecast", {})
    timeline = config.get("timeline", {})
    as_of_start = int(timeline.get("player_decision_start_year", years[0]))
    as_of_frequency = max(1, int(forecast_settings.get("as_of_frequency_years", 1)))
    tier_horizons = {
        str(tier.get("forecast_report_id")): forecast_horizons_for_tier(
            tier,
            forecast_settings,
        )
        for tier in config.get("forecast_reports", [])
    }
    all_horizons = sorted(
        {horizon for horizons in tier_horizons.values() for horizon in horizons}
    )
    max_year = years[-1]
    min_horizon = min(all_horizons) if all_horizons else 1
    as_of_years = [
        year
        for year in years
        if year >= as_of_start
        and year + min_horizon <= max_year
        and (year - as_of_start) % as_of_frequency == 0
    ]

    output: list[dict[str, Any]] = []
    previous_vintages: dict[str, dict[str, Any]] = {}
    for as_of_year in as_of_years:
        as_of_row = row_for_year(row_map, as_of_year)
        as_of_index = int(as_float(as_of_row, "year_index", as_of_year - years[0]))
        current_values = market_values(as_of_row)
        current_effective = float(current_values["effective"])
        current_potential = float(current_values["potential"])
        current_airline_supply = float(current_values["airline_supply"])
        current_bottleneck = str(current_values["bottleneck"])
        current_components = component_market_values(as_of_row)
        for tier in config.get("forecast_reports", []):
            report_id = str(tier.get("forecast_report_id"))
            future_peek = bool(tier.get("future_peek_mode", False))
            configured_quality = float(tier.get("forecast_quality_score", 0.0))
            horizons = [
                horizon
                for horizon in tier_horizons.get(report_id, [])
                if as_of_year + horizon <= max_year
            ]
            if not horizons:
                continue
            qualities = {
                horizon: effective_quality_score(
                    tier,
                    seed,
                    str(config["city_airport_market_id"]),
                    as_of_year,
                    as_of_year + horizon,
                )
                for horizon in horizons
            }
            path_quality = mean(qualities.values())
            capture_pct = seed_signal_capture_pct(
                tier,
                path_quality,
                future_peek,
            )
            raw_signal = build_hidden_signal_packet(
                row_map,
                as_of_year,
                max(horizons),
            )
            if future_peek:
                signal = {
                    **raw_signal,
                    "turn_window_start_year": raw_signal.get("turn_year"),
                    "turn_window_end_year": raw_signal.get("turn_year"),
                    "confidence_pct": 100.0,
                }
            else:
                signal = observe_hidden_signal_packet(
                    raw_signal,
                    tier=tier,
                    quality=path_quality,
                    seed=seed,
                    market_id=str(config["city_airport_market_id"]),
                    as_of_year=as_of_year,
                    report_id=report_id,
                )
            previous_state = previous_vintages.get(report_id)
            surprise_pct = previous_vintage_surprise_pct(
                previous_state,
                as_of_year,
                current_effective,
            )
            narrative = narrative_state(
                tier,
                signal,
                previous_state.get("signal") if previous_state else None,
                surprise_pct,
            )
            if future_peek:
                narrative = {
                    "headline": "开发审计模式：逐年读取隐藏真实路径",
                    "expected_regime": "future_truth",
                    "primary_driver": "hidden_true_path",
                    "secondary_driver": "development_audit",
                    "revision_reason": (
                        "initial_report" if previous_state is None else "future_truth_refresh"
                    ),
                    "conviction_pct": 100.0,
                }

            potential_path = build_joint_metric_path(
                row_map,
                as_of_year,
                horizons,
                config,
                tier,
                signal,
                path_quality,
                capture_pct,
                metric="potential",
                seed=seed,
                future_peek=future_peek,
            )
            supply_path = build_joint_metric_path(
                row_map,
                as_of_year,
                horizons,
                config,
                tier,
                signal,
                path_quality,
                capture_pct,
                metric="airline_supply",
                seed=seed,
                future_peek=future_peek,
            )
            inherited_potential, inherited_supply, revisions, previous_midpoints = (
                inherit_previous_vintage(
                    dict(potential_path["values"]),
                    dict(supply_path["values"]),
                    as_of_year=as_of_year,
                    horizons=horizons,
                    tier=tier,
                    signal=signal,
                    previous_state=previous_state,
                    surprise_pct=surprise_pct,
                )
            )
            if not future_peek:
                inherited_potential = smooth_inherited_metric_path(
                    current_potential,
                    inherited_potential,
                    horizons,
                    tier,
                )
                inherited_supply = smooth_inherited_metric_path(
                    current_airline_supply,
                    inherited_supply,
                    horizons,
                    tier,
                )
                for horizon in horizons:
                    previous_mid = previous_midpoints[horizon]
                    if previous_mid is not None:
                        current_mid = min(
                            inherited_potential[horizon],
                            inherited_supply[horizon],
                        )
                        revisions[horizon] = safe_divide(
                            current_mid - previous_mid,
                            previous_mid,
                            0.0,
                        ) * 100.0
            fresh_component_demand_paths = build_joint_component_share_path(
                row_map,
                as_of_year,
                horizons,
                tier,
                signal,
                path_quality,
                seed=seed,
                market_id=str(config["city_airport_market_id"]),
                future_peek=future_peek,
                basis="potential",
            )
            fresh_component_priority_paths = build_joint_component_share_path(
                row_map,
                as_of_year,
                horizons,
                tier,
                signal,
                path_quality,
                seed=seed,
                market_id=str(config["city_airport_market_id"]),
                future_peek=future_peek,
                basis="priority",
            )
            (
                component_demand_paths,
                component_priority_paths,
                component_revisions,
            ) = inherit_previous_component_paths(
                fresh_component_demand_paths,
                fresh_component_priority_paths,
                as_of_year=as_of_year,
                horizons=horizons,
                tier=tier,
                signal=signal,
                previous_state=previous_state,
                surprise_pct=surprise_pct,
            )
            vintage_rows: dict[int, dict[str, float]] = {}
            for horizon in horizons:
                target_year = as_of_year + horizon
                target_row = row_for_year(row_map, target_year)
                target_values = market_values(target_row)
                hidden_true_effective = float(target_values["effective"])
                hidden_true_potential = float(target_values["potential"])
                hidden_true_airline_supply = float(target_values["airline_supply"])
                hidden_true_bottleneck = str(target_values["bottleneck"])
                forecast_potential = inherited_potential[horizon]
                forecast_supply = inherited_supply[horizon]
                component_allocation = forecast_component_allocation(
                    forecast_potential,
                    forecast_supply,
                    component_demand_paths[horizon],
                    component_priority_paths[horizon],
                )
                effective_forecast_mid = sum(
                    component_allocation[component]["serviceable"]
                    for component in COMPONENTS
                )
                forecast_bottleneck = market_bottleneck_from_values(
                    forecast_potential,
                    forecast_supply,
                )
                naive_potential = float(potential_path["naive"][horizon])
                naive_supply = float(supply_path["naive"][horizon])
                naive_effective = min(naive_potential, naive_supply)
                if future_peek:
                    base_band = 0.0
                    downside_band = 0.0
                    upside_band = 0.0
                    effective_forecast_low = hidden_true_effective
                    effective_forecast_high = hidden_true_effective
                    bias_pct = 0.0
                    herding_bias_pct = 0.0
                    method_note = "future_peek_god_mode"
                    calibration_score = 100.0
                else:
                    interval_multiplier = float(
                        tier.get("narrative_interval_multiplier", 1.0)
                    )
                    base_band = forecast_band_pct(tier, float(horizon)) * interval_multiplier
                    down_unit = stable_unit_float(
                        "narrative_forecast_downside_band",
                        report_id,
                        seed,
                        config["city_airport_market_id"],
                        as_of_year,
                        target_year,
                    )
                    up_unit = stable_unit_float(
                        "narrative_forecast_upside_band",
                        report_id,
                        seed,
                        config["city_airport_market_id"],
                        target_year,
                        as_of_year,
                    )
                    downside_band = max(
                        0.0,
                        base_band * interpolate(0.86, 1.18, down_unit),
                    )
                    upside_band = max(
                        0.0,
                        base_band * interpolate(0.86, 1.18, up_unit),
                    )
                    effective_forecast_low = max(
                        0.0,
                        effective_forecast_mid * (1.0 - downside_band / 100.0),
                    )
                    effective_forecast_high = max(
                        effective_forecast_low,
                        effective_forecast_mid * (1.0 + upside_band / 100.0),
                    )
                    bias_pct = float(
                        potential_path["bias_pct"]
                        if forecast_bottleneck == "demand_limited"
                        else supply_path["bias_pct"]
                    )
                    herding_bias_pct = float(
                        potential_path["herding_bias_pct"]
                        if forecast_bottleneck == "demand_limited"
                        else supply_path["herding_bias_pct"]
                    )
                    method_note = "coarse_signal_narrative_joint_path_with_vintage_inheritance"
                    calibration_score = float(
                        tier.get("calibration_score", qualities[horizon])
                    )

                confidence = reported_confidence_pct(tier, horizon, future_peek)
                hidden_position = safe_divide(
                    hidden_true_effective - effective_forecast_low,
                    effective_forecast_high - effective_forecast_low,
                    0.0,
                ) * 100.0
                hidden_inside = (
                    effective_forecast_low
                    <= hidden_true_effective
                    <= effective_forecast_high
                )
                model_gap_pct = safe_divide(
                    effective_forecast_mid - hidden_true_effective,
                    hidden_true_effective,
                    0.0,
                ) * 100.0
                market_gap_pct = safe_divide(
                    effective_forecast_mid - naive_effective,
                    naive_effective,
                    0.0,
                ) * 100.0
                upside_factors, downside_factors = factor_tags(
                    as_of_row,
                    effective_forecast_mid,
                    current_effective,
                    horizon,
                )
                true_components = component_market_values(target_row)
                if future_peek:
                    component_allocation = {
                        component: {
                            "potential": true_components[component]["potential"],
                            "potential_share_pct": true_components[component][
                                "potential_share_pct"
                            ],
                            "priority_weight": true_components[component][
                                "priority_weight"
                            ],
                            "offered": true_components[component]["offered"],
                            "serviceable": true_components[component]["airline_supply"],
                            "serviceable_share_pct": true_components[component][
                                "airline_supply_share_pct"
                            ],
                            "fulfillment_pct": true_components[component][
                                "fulfillment_pct"
                            ],
                            "gap": true_components[component]["gap"],
                        }
                        for component in COMPONENTS
                    }
                    effective_forecast_mid = hidden_true_effective
                component_fields: dict[str, Any] = {}
                for component in COMPONENTS:
                    allocation = component_allocation[component]
                    effective_share = safe_divide(
                        allocation["serviceable"],
                        effective_forecast_mid,
                        1.0 / len(COMPONENTS),
                    )
                    component_low, component_high, component_share_band_pp = (
                        component_effective_interval(
                            component=component,
                            mid=allocation["serviceable"],
                            share=effective_share,
                            total_low=effective_forecast_low,
                            total_high=effective_forecast_high,
                            horizon=horizon,
                            quality=qualities[horizon],
                            tier=tier,
                            future_peek=future_peek,
                        )
                    )
                    component_fields[
                        f"{component}_forecast_effective_passengers_mid_million"
                    ] = allocation["serviceable"]
                    component_fields[
                        f"{component}_forecast_effective_passengers_low_million"
                    ] = component_low
                    component_fields[
                        f"{component}_forecast_effective_passengers_high_million"
                    ] = component_high
                    component_fields[
                        f"{component}_forecast_effective_share_band_pp"
                    ] = component_share_band_pp
                    component_fields[
                        f"{component}_forecast_potential_passengers_mid_million"
                    ] = allocation["potential"]
                    component_fields[
                        f"{component}_forecast_potential_share_pct"
                    ] = allocation["potential_share_pct"]
                    component_fields[
                        f"{component}_forecast_airline_priority_weight"
                    ] = allocation["priority_weight"]
                    component_fields[
                        f"{component}_forecast_airline_offered_capacity_million"
                    ] = allocation["offered"]
                    component_fields[
                        f"{component}_forecast_airline_supply_passengers_mid_million"
                    ] = allocation["serviceable"]
                    component_fields[
                        f"{component}_forecast_airline_supply_share_pct"
                    ] = allocation["serviceable_share_pct"]
                    component_fields[
                        f"{component}_forecast_airline_supply_fulfillment_pct"
                    ] = allocation["fulfillment_pct"]
                    component_fields[
                        f"{component}_forecast_airline_supply_gap_million"
                    ] = allocation["gap"]
                    component_fields[
                        f"{component}_forecast_effective_share_pct"
                    ] = effective_share * 100.0
                    component_fields[
                        f"current_{component}_potential_passengers_million"
                    ] = current_components[component]["potential"]
                    component_fields[
                        f"current_{component}_airline_supply_passengers_million"
                    ] = current_components[component]["airline_supply"]
                    component_fields[
                        f"current_{component}_effective_passengers_million"
                    ] = current_components[component]["effective"]
                    component_fields[
                        f"{component}_debug_hidden_true_effective_passengers_million"
                    ] = true_components[component]["effective"]
                    component_fields[
                        f"{component}_debug_hidden_true_effective_share_pct"
                    ] = true_components[component]["effective_share_pct"]
                    component_fields[
                        f"{component}_debug_hidden_true_potential_passengers_million"
                    ] = true_components[component]["potential"]
                    component_fields[
                        f"{component}_debug_hidden_true_potential_share_pct"
                    ] = true_components[component]["potential_share_pct"]
                    component_fields[
                        f"{component}_debug_hidden_true_airline_offered_capacity_million"
                    ] = true_components[component]["offered"]
                    component_fields[
                        f"{component}_debug_hidden_true_airline_supply_passengers_million"
                    ] = true_components[component]["airline_supply"]
                    component_fields[
                        f"{component}_debug_hidden_true_airline_supply_share_pct"
                    ] = true_components[component]["airline_supply_share_pct"]
                    component_fields[
                        f"{component}_debug_hidden_true_airline_supply_fulfillment_pct"
                    ] = true_components[component]["fulfillment_pct"]
                    component_fields[
                        f"{component}_debug_hidden_true_airline_supply_gap_million"
                    ] = true_components[component]["gap"]
                    component_fields[
                        f"{component}_debug_hidden_true_inside_forecast_range"
                    ] = str(
                        component_low
                        <= true_components[component]["effective"]
                        <= component_high
                    ).lower()
                    component_fields[
                        f"debug_hidden_signal_{component}_demand_direction"
                    ] = raw_signal.get("component_demand_directions", {}).get(
                        component
                    )
                    component_fields[
                        f"debug_hidden_signal_{component}_supply_direction"
                    ] = raw_signal.get("component_supply_directions", {}).get(
                        component
                    )

                output.append(
                    round_record(
                        {
                            "city_airport_potential_passenger_forecast_param_version": CITY_AIRPORT_POTENTIAL_PASSENGER_FORECAST_PARAM_VERSION,
                            "city_airport_potential_passenger_forecast_interface_version": CITY_AIRPORT_POTENTIAL_PASSENGER_FORECAST_INTERFACE_VERSION,
                            "forecast_config_version": config["config_version"],
                            "forecast_model_version": str(
                                forecast_settings.get(
                                    "forecast_model_version",
                                    "narrative-component-passenger-forecast-v1.2",
                                )
                            ),
                            "city_airport_market_id": config["city_airport_market_id"],
                            "city_name": config["city_name"],
                            "region_id": config["region_id"],
                            "region_name": config["region_name"],
                            "seed": seed,
                            "as_of_year": as_of_year,
                            "as_of_year_index": as_of_index,
                            "as_of_quarter": "FY",
                            "data_cutoff_year": as_of_year,
                            "data_cutoff_quarter": "FY",
                            "forecast_report_id": report_id,
                            "forecast_report_tier": str(
                                tier.get("forecast_report_tier", report_id)
                            ),
                            "forecast_report_tier_profile_id": str(
                                tier.get("forecast_report_tier_profile_id", "")
                            ),
                            "forecast_report_source": str(
                                tier.get("forecast_report_source", report_id)
                            ),
                            "forecast_narrative_profile_id": str(
                                tier.get("forecast_narrative_profile_id", "")
                            ),
                            "forecast_narrative_modifier_ids": ";".join(
                                tier.get("forecast_narrative_modifier_ids", [])
                            ),
                            "forecast_narrative_style_label": str(
                                tier.get("narrative_style_label", "")
                            ),
                            "forecast_narrative_style_summary": str(
                                tier.get("narrative_style_summary", "")
                            ),
                            "forecast_narrative_style_method": str(
                                tier.get("narrative_style_method", "")
                            ),
                            "forecast_narrative_style_blind_spot": str(
                                tier.get("narrative_style_blind_spot", "")
                            ),
                            "forecast_narrative_modifier_labels": ";".join(
                                tier.get("forecast_narrative_modifier_labels", [])
                            ),
                            "forecast_narrative_modifier_groups": ";".join(
                                tier.get("forecast_narrative_modifier_groups", [])
                            ),
                            "forecast_narrative_modifier_descriptions": ";".join(
                                tier.get(
                                    "forecast_narrative_modifier_descriptions",
                                    [],
                                )
                            ),
                            "forecast_narrative_modifier_tradeoffs": ";".join(
                                tier.get(
                                    "forecast_narrative_modifier_tradeoffs",
                                    [],
                                )
                            ),
                            "forecast_narrative_headline": narrative["headline"],
                            "forecast_primary_driver": narrative["primary_driver"],
                            "forecast_secondary_driver": narrative["secondary_driver"],
                            "forecast_expected_regime": narrative["expected_regime"],
                            "forecast_turn_window_start_year": signal.get(
                                "turn_window_start_year"
                            ),
                            "forecast_turn_window_end_year": signal.get(
                                "turn_window_end_year"
                            ),
                            "forecast_conviction_pct": narrative["conviction_pct"],
                            "forecast_revision_reason": narrative["revision_reason"],
                            "forecast_revision_pct": revisions[horizon],
                            "forecast_component_revision_pp": component_revisions[
                                horizon
                            ],
                            "forecast_previous_mid_million": previous_midpoints[horizon],
                            "forecast_signal_demand_direction": signal.get(
                                "demand_direction"
                            ),
                            "forecast_signal_supply_direction": signal.get(
                                "supply_direction"
                            ),
                            "forecast_signal_turn_direction": signal.get(
                                "turn_direction"
                            ),
                            "forecast_signal_confidence_pct": signal.get(
                                "confidence_pct"
                            ),
                            "reported_confidence_style": str(
                                tier.get("reported_confidence_style", "unspecified")
                            ),
                            "forecast_bias_direction": str(
                                tier.get("forecast_bias_direction", "mixed")
                            ),
                            "configured_forecast_quality_score": configured_quality,
                            "forecast_quality_score": qualities[horizon],
                            "future_peek_mode": str(future_peek).lower(),
                            "forecast_year": target_year,
                            "forecast_year_index": int(
                                as_float(
                                    target_row,
                                    "year_index",
                                    target_year - years[0],
                                )
                            ),
                            "forecast_horizon_years": horizon,
                            "current_effective_passengers_million": current_effective,
                            "current_potential_passengers_million": current_potential,
                            "current_airline_supply_passengers_million": current_airline_supply,
                            "current_airline_serviceable_supply_million": current_effective,
                            "current_market_bottleneck": current_bottleneck,
                            "naive_public_curve_effective_million": naive_effective,
                            "naive_public_curve_potential_million": naive_potential,
                            "naive_public_curve_airline_supply_million": naive_supply,
                            "lagged_hidden_curve_effective_million": naive_effective,
                            "lagged_hidden_curve_potential_million": naive_potential,
                            "lagged_hidden_curve_airline_supply_million": naive_supply,
                            "forecast_effective_passengers_mid_million": effective_forecast_mid,
                            "forecast_effective_passengers_low_million": effective_forecast_low,
                            "forecast_effective_passengers_high_million": effective_forecast_high,
                            "forecast_potential_passengers_mid_million": forecast_potential,
                            "forecast_airline_supply_passengers_mid_million": forecast_supply,
                            "forecast_airline_serviceable_supply_mid_million": effective_forecast_mid,
                            "forecast_airline_unused_capacity_mid_million": max(
                                0.0, forecast_supply - effective_forecast_mid
                            ),
                            "forecast_market_bottleneck": forecast_bottleneck,
                            "forecast_downside_band_pct": downside_band,
                            "forecast_upside_band_pct": upside_band,
                            "forecast_error_band_pct": (
                                downside_band + upside_band
                            )
                            / 2.0,
                            "forecast_confidence_pct": confidence,
                            "calibration_score": calibration_score,
                            "seed_signal_capture_pct": capture_pct,
                            "forecast_lag_years": 0,
                            "deterministic_forecast_bias_pct": bias_pct,
                            "public_consensus_anchor_pct": 100.0 - capture_pct,
                            "consensus_herding_bias_pct": herding_bias_pct,
                            "market_consensus_gap_pct": market_gap_pct,
                            "forecast_momentum_label": momentum_label(
                                current_effective,
                                effective_forecast_mid,
                                horizon,
                            ),
                            "forecast_long_term_tier_label": long_term_tier_label(
                                effective_forecast_mid
                            ),
                            "forecast_reliability_label": reliability_label(
                                confidence,
                                future_peek,
                            ),
                            "forecast_main_upside_factors": upside_factors,
                            "forecast_main_downside_factors": downside_factors,
                            "source_seed_city_momentum_label": str(
                                as_of_row.get("seed_city_momentum_label")
                                or "balanced"
                            ),
                            "source_seed_city_potential_multiplier": as_float(
                                as_of_row,
                                "seed_city_potential_multiplier",
                                1.0,
                            ),
                            "forecast_method_note": method_note,
                            **component_fields,
                            "debug_hidden_true_effective_passengers_million": hidden_true_effective,
                            "debug_hidden_true_potential_passengers_million": hidden_true_potential,
                            "debug_hidden_true_airline_supply_passengers_million": hidden_true_airline_supply,
                            "debug_hidden_true_market_bottleneck": hidden_true_bottleneck,
                            "debug_hidden_true_inside_forecast_range": str(
                                hidden_inside
                            ).lower(),
                            "debug_hidden_true_position_pct": hidden_position,
                            "debug_model_gap_to_true_pct": model_gap_pct,
                            "debug_hidden_signal_demand_direction": raw_signal.get(
                                "demand_direction"
                            ),
                            "debug_hidden_signal_supply_direction": raw_signal.get(
                                "supply_direction"
                            ),
                            "debug_hidden_signal_turn_year": raw_signal.get(
                                "turn_year"
                            ),
                            "debug_hidden_signal_turn_direction": raw_signal.get(
                                "turn_direction"
                            ),
                        }
                    )
                )
                vintage_rows[target_year] = {
                    "potential": forecast_potential,
                    "airline_supply": forecast_supply,
                    "effective": effective_forecast_mid,
                    "component_demand_shares": dict(
                        component_demand_paths[horizon]
                    ),
                    "component_priority_weights": dict(
                        component_priority_paths[horizon]
                    ),
                }
            previous_vintages[report_id] = {
                "as_of_year": as_of_year,
                "signal": signal,
                "narrative": narrative,
                "by_target_year": vintage_rows,
            }
    return annotate_realized_quality_scores(output)


def generate_forecast_candidate(
    city_airport_rows: list[dict[str, Any]],
    *,
    config_path: Path,
    seed: int,
    as_of_year: int,
    tier_profile_id: str,
    narrative_profile_id: str,
    modifier_mode: str,
    modifier_ids: list[str],
    score_min: float,
    score_max: float,
    generation_nonce: int,
) -> dict[str, Any]:
    return forecast_candidate_generator.generate_forecast_candidate(
        city_airport_rows,
        config_path=config_path,
        seed=seed,
        as_of_year=as_of_year,
        tier_profile_id=tier_profile_id,
        narrative_profile_id=narrative_profile_id,
        modifier_mode=modifier_mode,
        modifier_ids=modifier_ids,
        score_min=score_min,
        score_max=score_max,
        generation_nonce=generation_nonce,
        simulate_forecast=simulate_potential_passenger_forecast,
    )


def summarize(rows: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, Any]:
    if not rows:
        return {
            "forecast_config_version": config.get("config_version"),
            "rows": 0,
        }
    by_report: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_report.setdefault(str(row.get("forecast_report_id")), []).append(row)
    report_summaries = []
    for report_id, report_rows in sorted(by_report.items()):
        gaps = [abs(as_float(row, "debug_model_gap_to_true_pct")) for row in report_rows if str(row.get("future_peek_mode")) != "true"]
        report_scores_by_as_of: dict[tuple[Any, Any], float] = {}
        weighted_errors_by_as_of: dict[tuple[Any, Any], float] = {}
        for row in report_rows:
            key = (row.get("seed"), row.get("as_of_year"))
            report_scores_by_as_of.setdefault(key, as_float(row, "realized_report_quality_score"))
            weighted_errors_by_as_of.setdefault(key, as_float(row, "realized_report_weighted_abs_error_pct"))
        report_summaries.append({
            "forecast_report_id": report_id,
            "rows": len(report_rows),
            "average_abs_model_gap_to_true_pct": round(mean(gaps), 4) if gaps else 0.0,
            "average_realized_report_quality_score": round(mean(report_scores_by_as_of.values()), 4) if report_scores_by_as_of else 0.0,
            "average_realized_weighted_abs_error_pct": round(mean(weighted_errors_by_as_of.values()), 4) if weighted_errors_by_as_of else 0.0,
            "average_confidence_pct": round(mean(as_float(row, "forecast_confidence_pct") for row in report_rows), 4),
            "hidden_true_inside_range_pct": round(
                100.0 * sum(1 for row in report_rows if str(row.get("debug_hidden_true_inside_forecast_range")) == "true") / len(report_rows),
                4,
            ),
        })
    return {
        "forecast_config_version": config["config_version"],
        "city_airport_market_id": config["city_airport_market_id"],
        "city_name": config["city_name"],
        "region_id": config["region_id"],
        "rows": len(rows),
        "as_of_start_year": min(int(as_float(row, "as_of_year")) for row in rows),
        "as_of_end_year": max(int(as_float(row, "as_of_year")) for row in rows),
        "forecast_end_year": max(int(as_float(row, "forecast_year")) for row in rows),
        "report_summaries": report_summaries,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate city airport effective passenger forecast rows.")
    parser.add_argument(
        "--city-airport-demand-csv",
        type=Path,
        default=AIRPORT_DIR / "output" / "city_airport_market_demand" / "china_mainland" / "beijing_airport_system_city_airport_demand_seed_sweep.csv",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_DIR / "beijing_airport_system_potential_passenger_forecast_v1.json",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=AIRPORT_DIR / "output" / "city_airport_potential_passenger_forecast" / "china_mainland",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    city_rows = read_csv(args.city_airport_demand_csv)
    rows = simulate_potential_passenger_forecast(city_rows, config)
    market_id = config["city_airport_market_id"]
    csv_path = args.output_dir / f"{market_id}_potential_passenger_forecast_seed_sweep.csv"
    summary_path = args.output_dir / f"{market_id}_potential_passenger_forecast_summary.json"
    write_csv(csv_path, rows, POTENTIAL_PASSENGER_FORECAST_FIELDS)
    write_json(summary_path, summarize(rows, config))
    lazy_assets = write_viewer_lazy_assets(args.output_dir, rows, config)
    print(json.dumps({
        "rows": len(rows),
        "csv": str(csv_path),
        "summary": str(summary_path),
        "viewer_lazy": lazy_assets,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
