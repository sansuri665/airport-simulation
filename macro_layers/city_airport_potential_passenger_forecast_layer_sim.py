from __future__ import annotations

from importlib import import_module

_SIBLING_PREFIX = f"{__package__}." if __package__ else ""
simulation_io = import_module(f"{_SIBLING_PREFIX}simulation_io")
simulation_utils = import_module(f"{_SIBLING_PREFIX}simulation_utils")

read_csv = simulation_io.read_csv_utf8_sig
write_csv = simulation_io.write_csv_utf8_sig_with_extra_fields
write_json = simulation_io.write_json_utf8_data
as_float = simulation_utils.as_float_convert_lookup_default
clamp = simulation_utils.clamp
safe_divide = simulation_utils.safe_divide

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from statistics import mean
from typing import Any


CITY_AIRPORT_POTENTIAL_PASSENGER_FORECAST_PARAM_VERSION = "city-airport-effective-passenger-forecast-layer-v0.3"
CITY_AIRPORT_POTENTIAL_PASSENGER_FORECAST_INTERFACE_VERSION = "city-airport-effective-passenger-forecast-interface-v0.2"
FORECAST_VIEWER_LAZY_INDEX_VERSION = "airport-forecast-viewer-lazy-index-v1"
FORECAST_VIEWER_CHUNK_VERSION = "airport-forecast-viewer-report-chunk-v1"

AIRPORT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_DIR = AIRPORT_DIR / "config" / "city_airport_potential_passenger_forecast"
COMPONENTS = ("business", "leisure", "vfr", "long_haul", "transfer")
COMPONENT_SCORE_WEIGHTS = {
    "business": 1.30,
    "leisure": 1.00,
    "vfr": 0.75,
    "long_haul": 1.35,
    "transfer": 1.15,
}
COMPONENT_SHARE_UNCERTAINTY_MULTIPLIER = {
    "business": 0.80,
    "leisure": 0.78,
    "vfr": 0.92,
    "long_haul": 1.08,
    "transfer": 1.22,
}

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
    "forecast_report_source",
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
    "forecast_market_bottleneck",
    "forecast_downside_band_pct",
    "forecast_upside_band_pct",
    "forecast_error_band_pct",
    "forecast_confidence_pct",
    "realized_score_method_version",
    "realized_report_quality_score",
    "realized_point_quality_score",
    "realized_midpoint_accuracy_score",
    "realized_trend_accuracy_score",
    "realized_shape_accuracy_score",
    "realized_component_structure_score",
    "realized_bottleneck_accuracy_score",
    "realized_interval_calibration_score",
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
]


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


def load_config(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if raw.get("schema_version") != "city-airport-potential-passenger-forecast-config-v1":
        raise ValueError(f"Unsupported city airport potential passenger forecast config schema in {path}")
    return raw


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
    airline_supply = as_float(row, "city_airline_supply_passengers_million", potential)
    effective = min(potential, airline_supply)
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
    values = market_values(row)
    potential_total = float(values["potential"])
    airline_supply_total = float(values["airline_supply"])
    effective_total = float(values["effective"])
    bottleneck = str(values["bottleneck"])
    output: dict[str, dict[str, float]] = {}
    for component in COMPONENTS:
        potential = as_float(row, f"{component}_passengers_million")
        airline_supply = as_float(row, f"{component}_airline_supply_passengers_million", potential)
        if bottleneck == "airline_supply_limited":
            share = safe_divide(airline_supply, airline_supply_total, 1.0 / len(COMPONENTS))
        else:
            share = safe_divide(potential, potential_total, 1.0 / len(COMPONENTS))
        effective = effective_total * share
        output[component] = {
            "potential": potential,
            "airline_supply": airline_supply,
            "effective": effective,
            "effective_share_pct": share * 100.0,
        }
    return output


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


def tier_by_id(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(item.get("forecast_report_id")): item for item in config.get("forecast_reports", [])}


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


def forecast_lag_years(tier: dict[str, Any], quality: float, future_peek: bool) -> int:
    if future_peek:
        return 0
    if tier.get("derive_lag_from_quality", False):
        return int(round(interpolate(
            float(tier.get("lag_years_at_score_0", 8.0)),
            float(tier.get("lag_years_at_score_70", 2.0)),
            quality_ratio(quality),
        )))
    return int(tier.get("forecast_lag_years", 4))


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


def degraded_metric_midpoint(
    row_map: dict[int, dict[str, Any]],
    as_of_year: int,
    target_year: int,
    lagged_year: int,
    config: dict[str, Any],
    tier: dict[str, Any],
    metric: str,
    quality: float,
    capture_pct: float,
    future_peek: bool,
) -> dict[str, float]:
    target_row = row_for_year(row_map, target_year)
    hidden_true = market_value_for_metric(target_row, metric)
    lagged_hidden = market_value_for_metric(row_for_year(row_map, lagged_year), metric)
    naive_curve = naive_public_curve(row_map, as_of_year, target_year, config, metric)
    if future_peek:
        return {
            "hidden_true": hidden_true,
            "lagged_hidden": hidden_true,
            "naive_curve": hidden_true,
            "forecast_mid": hidden_true,
            "bias_pct": 0.0,
            "herding_bias_pct": 0.0,
        }

    capture = capture_pct / 100.0
    visible = naive_curve * (1.0 - capture) + lagged_hidden * capture
    bias_cap = deterministic_bias_cap_pct(tier, quality)
    if metric == "airline_supply":
        bias_cap *= float(tier.get("airline_supply_bias_multiplier", 1.25))
    bias_unit = stable_unit_float(
        "forecast_bias",
        metric,
        tier.get("forecast_report_id"),
        row_for_year(row_map, as_of_year).get("seed"),
        config["city_airport_market_id"],
        as_of_year,
        target_year,
    )
    bias_pct = oriented_bias_pct(tier, bias_cap, bias_unit)
    herding_cap = float(tier.get("consensus_herding_bias_cap_pct", 0.0))
    if metric == "airline_supply":
        herding_cap *= float(tier.get("airline_supply_herding_multiplier", 1.15))
    herding_unit = stable_unit_float(
        "consensus_herding",
        metric,
        tier.get("forecast_report_id"),
        row_for_year(row_map, as_of_year).get("seed"),
        config["city_airport_market_id"],
        as_of_year,
    )
    herding_bias_pct = interpolate(-herding_cap, herding_cap, herding_unit)
    return {
        "hidden_true": hidden_true,
        "lagged_hidden": lagged_hidden,
        "naive_curve": naive_curve,
        "forecast_mid": max(0.0, visible * (1.0 + (bias_pct + herding_bias_pct) / 100.0)),
        "bias_pct": bias_pct,
        "herding_bias_pct": herding_bias_pct,
    }


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


def component_basis_share_map(row: dict[str, Any], bottleneck: str) -> dict[str, float]:
    if bottleneck == "airline_supply_limited":
        return normalize_share_map({
            component: as_float(
                row,
                f"{component}_airline_supply_passengers_million",
                as_float(row, f"{component}_passengers_million"),
            )
            for component in COMPONENTS
        })
    if bottleneck == "demand_limited":
        return normalize_share_map({
            component: as_float(row, f"{component}_passengers_million")
            for component in COMPONENTS
        })
    return effective_component_share_map(row)


def forecast_component_share_map(
    row_map: dict[int, dict[str, Any]],
    as_of_year: int,
    target_year: int,
    lagged_year: int,
    config: dict[str, Any],
    tier: dict[str, Any],
    quality: float,
    capture_pct: float,
    forecast_bottleneck: str,
    future_peek: bool,
) -> dict[str, float]:
    if future_peek:
        return effective_component_share_map(row_for_year(row_map, target_year))

    horizon = max(1, target_year - as_of_year)
    quality_unit = quality_ratio(quality)
    current_share = component_basis_share_map(row_for_year(row_map, as_of_year), forecast_bottleneck)
    start_year = max(min(row_map), as_of_year - int(config.get("forecast", {}).get("naive_history_years", 5)))
    start_share = component_basis_share_map(row_for_year(row_map, start_year), forecast_bottleneck)
    lagged_share = component_basis_share_map(row_for_year(row_map, lagged_year), forecast_bottleneck)
    component_capture_multiplier = float(tier.get("component_seed_capture_multiplier", interpolate(0.62, 0.82, quality_unit)))
    component_capture = clamp(capture_pct * component_capture_multiplier, 0.0, 82.0) / 100.0
    trend_strength = interpolate(0.18, 0.32, quality_unit)
    public_share = normalize_share_map({
        component: current_share[component] + trend_strength * (current_share[component] - start_share[component])
        for component in COMPONENTS
    })
    raw: dict[str, float] = {}
    for component in COMPONENTS:
        anchor = public_share[component] * (1.0 - component_capture) + lagged_share[component] * component_capture
        uncertainty = COMPONENT_SHARE_UNCERTAINTY_MULTIPLIER[component]
        horizon_multiplier = 0.88 + 0.035 * min(horizon, 12)
        absolute_bias_cap_pp = interpolate(
            float(tier.get("component_share_bias_cap_at_score_0_pp", 4.2)),
            float(tier.get("component_share_bias_cap_at_score_70_pp", 0.85)),
            quality_unit,
        ) * uncertainty * horizon_multiplier
        relative_bias_cap_pp = anchor * 100.0 * interpolate(0.48, 0.16, quality_unit) * uncertainty * horizon_multiplier
        bias_cap_pp = min(absolute_bias_cap_pp, max(0.35, relative_bias_cap_pp))
        bias_unit = stable_unit_float(
            "component_share_bias",
            component,
            tier.get("forecast_report_id"),
            row_for_year(row_map, as_of_year).get("seed"),
            config["city_airport_market_id"],
            as_of_year,
            target_year,
        )
        bias = interpolate(-bias_cap_pp, bias_cap_pp, bias_unit) / 100.0
        raw[component] = max(0.0, anchor + bias)
    return normalize_share_map(raw)


REALIZED_SCORE_METHOD_VERSION = "effective-passenger-realized-score-v0.2"


def accuracy_score_from_gap(gap_pct: float, catastrophic_gap_pct: float, exponent: float = 1.12) -> float:
    if catastrophic_gap_pct <= 0.0:
        return 100.0 if gap_pct <= 0.0 else 0.0
    unit = clamp(abs(gap_pct) / catastrophic_gap_pct, 0.0, 1.0)
    return 100.0 * (1.0 - math.pow(unit, exponent))


def direction_accuracy_score(predicted_growth_pct: float, true_growth_pct: float) -> float:
    if abs(true_growth_pct) <= 1.5:
        return 100.0 if abs(predicted_growth_pct) <= 4.0 else 62.0
    if predicted_growth_pct == 0.0:
        return 45.0
    return 100.0 if (predicted_growth_pct > 0.0) == (true_growth_pct > 0.0) else 18.0


def interval_calibration_score(row: dict[str, Any], horizon: float) -> float:
    low = as_float(row, "forecast_effective_passengers_low_million")
    high = as_float(row, "forecast_effective_passengers_high_million")
    mid = as_float(row, "forecast_effective_passengers_mid_million")
    true_value = as_float(row, "debug_hidden_true_effective_passengers_million")
    if true_value <= 0.0 or mid <= 0.0:
        return 0.0
    width_pct = (high - low) / mid * 100.0
    reasonable_width_pct = 7.0 + 1.8 * horizon
    inside = low <= true_value <= high
    if inside:
        wide_penalty = max(0.0, width_pct - reasonable_width_pct) * 1.25
        return clamp(94.0 - wide_penalty, 55.0, 100.0)
    miss_pct = 0.0
    if true_value < low:
        miss_pct = (low - true_value) / true_value * 100.0
    elif true_value > high:
        miss_pct = (true_value - high) / true_value * 100.0
    overconfidence_penalty = max(0.0, reasonable_width_pct - width_pct) * 0.7
    return clamp(44.0 - 4.0 * miss_pct - overconfidence_penalty, 0.0, 45.0)


def component_structure_score(row: dict[str, Any], horizon: float) -> float:
    weighted_gaps: list[tuple[float, float]] = []
    for component in COMPONENTS:
        forecast_share = as_float(row, f"{component}_forecast_effective_share_pct")
        true_share = as_float(row, f"{component}_debug_hidden_true_effective_share_pct")
        weighted_gaps.append((abs(forecast_share - true_share), COMPONENT_SCORE_WEIGHTS[component]))
    weighted_gap_pp = weighted_mean(weighted_gaps)
    return accuracy_score_from_gap(weighted_gap_pp, 12.0 + 0.35 * horizon, 1.05)


def bottleneck_accuracy_score(row: dict[str, Any]) -> float:
    forecast = str(row.get("forecast_market_bottleneck") or "unknown")
    true = str(row.get("debug_hidden_true_market_bottleneck") or "unknown")
    if forecast == true:
        return 100.0
    potential = as_float(row, "debug_hidden_true_potential_passengers_million")
    airline_supply = as_float(row, "debug_hidden_true_airline_supply_passengers_million")
    effective = as_float(row, "debug_hidden_true_effective_passengers_million")
    if effective > 0.0 and abs(potential - airline_supply) / effective <= 0.025:
        return 72.0
    return 25.0


def weighted_mean(values: list[tuple[float, float]]) -> float:
    total_weight = sum(weight for _, weight in values)
    if total_weight <= 0.0:
        return 0.0
    return sum(value * weight for value, weight in values) / total_weight


def realized_bias_label(bias_pct: float, avg_abs_error_pct: float, interval_hit_rate_pct: float) -> str:
    if avg_abs_error_pct <= 2.5 and interval_hit_rate_pct >= 85.0:
        return "near_true_curve"
    if bias_pct >= 8.0:
        return "systematically_optimistic"
    if bias_pct <= -8.0:
        return "systematically_pessimistic"
    if interval_hit_rate_pct < 45.0 and avg_abs_error_pct >= 10.0:
        return "poorly_calibrated"
    if interval_hit_rate_pct < 55.0:
        return "range_misaligned"
    if avg_abs_error_pct <= 5.0:
        return "well_calibrated"
    return "mixed_quality"


def annotate_realized_quality_scores(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for row in rows:
        key = (
            row.get("city_airport_market_id"),
            row.get("seed"),
            row.get("as_of_year"),
            row.get("forecast_report_id"),
        )
        grouped.setdefault(key, []).append(row)

    for report_rows in grouped.values():
        ordered = sorted(report_rows, key=lambda item: as_float(item, "forecast_horizon_years"))
        if not ordered:
            continue
        if str(ordered[0].get("future_peek_mode")) == "true":
            for row in ordered:
                row.update(round_record({
                    "realized_score_method_version": REALIZED_SCORE_METHOD_VERSION,
                    "realized_report_quality_score": 100.0,
                    "realized_point_quality_score": 100.0,
                    "realized_midpoint_accuracy_score": 100.0,
                    "realized_trend_accuracy_score": 100.0,
                    "realized_shape_accuracy_score": 100.0,
                    "realized_component_structure_score": 100.0,
                    "realized_bottleneck_accuracy_score": 100.0,
                    "realized_interval_calibration_score": 100.0,
                    "realized_report_weighted_abs_error_pct": 0.0,
                    "realized_report_interval_hit_rate_pct": 100.0,
                    "realized_report_bias_pct": 0.0,
                    "realized_report_bias_label": "future_peek_exact",
                }))
            continue

        current = as_float(ordered[0], "current_effective_passengers_million")
        prev_horizon = 0.0
        prev_mid = current
        prev_true = current
        point_metrics: list[dict[str, float]] = []
        for row in ordered:
            horizon = as_float(row, "forecast_horizon_years")
            weight = 1.0 + 0.08 * horizon
            mid = as_float(row, "forecast_effective_passengers_mid_million")
            true_value = as_float(row, "debug_hidden_true_effective_passengers_million")
            signed_gap_pct = safe_divide(mid - true_value, true_value, 0.0) * 100.0
            abs_gap_pct = abs(signed_gap_pct)
            midpoint_score = accuracy_score_from_gap(abs_gap_pct, 30.0 + 1.5 * horizon)

            predicted_growth_pct = safe_divide(mid - current, current, 0.0) * 100.0
            true_growth_pct = safe_divide(true_value - current, current, 0.0) * 100.0
            growth_gap_pct = abs(predicted_growth_pct - true_growth_pct)
            growth_score = accuracy_score_from_gap(growth_gap_pct, 34.0 + 2.0 * horizon)
            trend_score = 0.72 * growth_score + 0.28 * direction_accuracy_score(predicted_growth_pct, true_growth_pct)

            step_years = max(1.0, horizon - prev_horizon)
            predicted_step_growth_pct = cagr_pct(prev_mid, mid, int(round(step_years)), 0.0)
            true_step_growth_pct = cagr_pct(prev_true, true_value, int(round(step_years)), 0.0)
            shape_score = accuracy_score_from_gap(abs(predicted_step_growth_pct - true_step_growth_pct), 12.0)

            interval_score = interval_calibration_score(row, horizon)
            component_score = component_structure_score(row, horizon)
            bottleneck_score = bottleneck_accuracy_score(row)
            point_score = (
                0.50 * midpoint_score
                + 0.18 * trend_score
                + 0.10 * shape_score
                + 0.10 * component_score
                + 0.07 * interval_score
                + 0.05 * bottleneck_score
            )

            point_metrics.append({
                "weight": weight,
                "signed_gap_pct": signed_gap_pct,
                "abs_gap_pct": abs_gap_pct,
                "midpoint_score": midpoint_score,
                "trend_score": trend_score,
                "shape_score": shape_score,
                "component_score": component_score,
                "bottleneck_score": bottleneck_score,
                "interval_score": interval_score,
                "point_score": point_score,
                "inside": 1.0 if str(row.get("debug_hidden_true_inside_forecast_range")) == "true" else 0.0,
            })
            prev_horizon = horizon
            prev_mid = mid
            prev_true = true_value

        report_midpoint_score = weighted_mean([(item["midpoint_score"], item["weight"]) for item in point_metrics])
        report_trend_score = weighted_mean([(item["trend_score"], item["weight"]) for item in point_metrics])
        report_shape_score = weighted_mean([(item["shape_score"], item["weight"]) for item in point_metrics])
        report_component_score = weighted_mean([(item["component_score"], item["weight"]) for item in point_metrics])
        report_bottleneck_score = weighted_mean([(item["bottleneck_score"], item["weight"]) for item in point_metrics])
        report_interval_score = weighted_mean([(item["interval_score"], item["weight"]) for item in point_metrics])
        report_score = (
            0.50 * report_midpoint_score
            + 0.18 * report_trend_score
            + 0.10 * report_shape_score
            + 0.10 * report_component_score
            + 0.07 * report_interval_score
            + 0.05 * report_bottleneck_score
        )
        weighted_abs_error_pct = weighted_mean([(item["abs_gap_pct"], item["weight"]) for item in point_metrics])
        weighted_bias_pct = weighted_mean([(item["signed_gap_pct"], item["weight"]) for item in point_metrics])
        interval_hit_rate_pct = 100.0 * mean(item["inside"] for item in point_metrics)
        bias_label = realized_bias_label(weighted_bias_pct, weighted_abs_error_pct, interval_hit_rate_pct)

        for row, metric in zip(ordered, point_metrics):
            row.update(round_record({
                "realized_score_method_version": REALIZED_SCORE_METHOD_VERSION,
                "realized_report_quality_score": report_score,
                "realized_point_quality_score": metric["point_score"],
                "realized_midpoint_accuracy_score": metric["midpoint_score"],
                "realized_trend_accuracy_score": metric["trend_score"],
                "realized_shape_accuracy_score": metric["shape_score"],
                "realized_component_structure_score": metric["component_score"],
                "realized_bottleneck_accuracy_score": metric["bottleneck_score"],
                "realized_interval_calibration_score": metric["interval_score"],
                "realized_report_weighted_abs_error_pct": weighted_abs_error_pct,
                "realized_report_interval_hit_rate_pct": interval_hit_rate_pct,
                "realized_report_bias_pct": weighted_bias_pct,
                "realized_report_bias_label": bias_label,
            }))
    return rows


def simulate_potential_passenger_forecast(
    city_airport_rows: list[dict[str, Any]],
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    if not city_airport_rows:
        return []
    sorted_rows = sorted(city_airport_rows, key=lambda item: (int(as_float(item, "seed")), int(as_float(item, "year"))))
    seed_values = sorted({int(as_float(row, "seed")) for row in sorted_rows})
    if len(seed_values) != 1:
        raise ValueError("Effective passenger forecast currently expects one seed per input row set.")
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
        str(tier.get("forecast_report_id")): forecast_horizons_for_tier(tier, forecast_settings)
        for tier in config.get("forecast_reports", [])
    }
    all_horizons = sorted({horizon for horizons in tier_horizons.values() for horizon in horizons})
    max_year = years[-1]
    min_horizon = min(all_horizons) if all_horizons else 1
    as_of_years = [
        year for year in years
        if year >= as_of_start and year + min_horizon <= max_year and (year - as_of_start) % as_of_frequency == 0
    ]

    output: list[dict[str, Any]] = []
    for as_of_year in as_of_years:
        as_of_row = row_for_year(row_map, as_of_year)
        as_of_index = int(as_float(as_of_row, "year_index", as_of_year - years[0]))
        current_values = market_values(as_of_row)
        current_effective = float(current_values["effective"])
        current_potential = float(current_values["potential"])
        current_airline_supply = float(current_values["airline_supply"])
        current_bottleneck = str(current_values["bottleneck"])
        for tier in config.get("forecast_reports", []):
            report_id = str(tier.get("forecast_report_id"))
            future_peek = bool(tier.get("future_peek_mode", False))
            configured_quality = float(tier.get("forecast_quality_score", 0.0))
            for horizon in tier_horizons.get(report_id, []):
                target_year = as_of_year + horizon
                if target_year > max_year:
                    continue
                quality = effective_quality_score(tier, seed, config["city_airport_market_id"], as_of_year, target_year)
                capture_pct = seed_signal_capture_pct(tier, quality, future_peek)
                lag_years = forecast_lag_years(tier, quality, future_peek)
                target_row = row_for_year(row_map, target_year)
                lagged_year = target_year if future_peek else clamp(target_year - lag_years, as_of_year, max_year)
                lagged_year_int = int(lagged_year)
                target_values = market_values(target_row)
                hidden_true_effective = float(target_values["effective"])
                hidden_true_potential = float(target_values["potential"])
                hidden_true_airline_supply = float(target_values["airline_supply"])
                hidden_true_bottleneck = str(target_values["bottleneck"])
                potential_forecast = degraded_metric_midpoint(
                    row_map,
                    as_of_year,
                    target_year,
                    lagged_year_int,
                    config,
                    tier,
                    "potential",
                    quality,
                    capture_pct,
                    future_peek,
                )
                airline_supply_forecast = degraded_metric_midpoint(
                    row_map,
                    as_of_year,
                    target_year,
                    lagged_year_int,
                    config,
                    tier,
                    "airline_supply",
                    quality,
                    capture_pct,
                    future_peek,
                )
                effective_forecast_mid = min(
                    float(potential_forecast["forecast_mid"]),
                    float(airline_supply_forecast["forecast_mid"]),
                )
                forecast_bottleneck = market_bottleneck_from_values(
                    float(potential_forecast["forecast_mid"]),
                    float(airline_supply_forecast["forecast_mid"]),
                )
                naive_effective = min(
                    float(potential_forecast["naive_curve"]),
                    float(airline_supply_forecast["naive_curve"]),
                )
                lagged_effective = min(
                    float(potential_forecast["lagged_hidden"]),
                    float(airline_supply_forecast["lagged_hidden"]),
                )
                if future_peek:
                    effective_forecast_low = hidden_true_effective
                    effective_forecast_high = hidden_true_effective
                    base_band = 0.0
                    downside_band = 0.0
                    upside_band = 0.0
                    bias_pct = 0.0
                    herding_bias_pct = 0.0
                    method_note = "future_peek_god_mode"
                    calibration_score = 100.0
                else:
                    base_band = forecast_band_pct(tier, float(horizon))
                    down_unit = stable_unit_float("forecast_downside_band", report_id, seed, config["city_airport_market_id"], as_of_year, target_year)
                    up_unit = stable_unit_float("forecast_upside_band", report_id, seed, config["city_airport_market_id"], target_year, as_of_year)
                    downside_band = max(0.0, base_band * interpolate(0.82, 1.24, down_unit))
                    upside_band = max(0.0, base_band * interpolate(0.82, 1.24, up_unit))
                    effective_forecast_low = max(0.0, effective_forecast_mid * (1.0 - downside_band / 100.0))
                    effective_forecast_high = max(effective_forecast_low, effective_forecast_mid * (1.0 + upside_band / 100.0))
                    bias_pct = (
                        float(potential_forecast["bias_pct"])
                        if forecast_bottleneck == "demand_limited"
                        else float(airline_supply_forecast["bias_pct"])
                    )
                    herding_bias_pct = (
                        float(potential_forecast["herding_bias_pct"])
                        if forecast_bottleneck == "demand_limited"
                        else float(airline_supply_forecast["herding_bias_pct"])
                    )
                    method_note = "degraded_potential_and_airline_supply_min_curve"
                    calibration_score = float(tier.get("calibration_score", quality))

                avg_band = (downside_band + upside_band) / 2.0
                confidence = reported_confidence_pct(tier, horizon, future_peek)
                hidden_position = safe_divide(hidden_true_effective - effective_forecast_low, effective_forecast_high - effective_forecast_low, 0.0) * 100.0
                hidden_inside = effective_forecast_low <= hidden_true_effective <= effective_forecast_high
                model_gap_pct = safe_divide(effective_forecast_mid - hidden_true_effective, hidden_true_effective, 0.0) * 100.0
                market_gap_pct = 0.0 if naive_effective <= 0 else (effective_forecast_mid / naive_effective - 1.0) * 100.0
                source_seed_label = str(as_of_row.get("seed_city_momentum_label") or "balanced")
                source_seed_multiplier = as_float(as_of_row, "seed_city_potential_multiplier", 1.0)
                upside_factors, downside_factors = factor_tags(as_of_row, effective_forecast_mid, current_effective, horizon)
                forecast_component_shares = forecast_component_share_map(
                    row_map,
                    as_of_year,
                    target_year,
                    lagged_year_int,
                    config,
                    tier,
                    quality,
                    capture_pct,
                    forecast_bottleneck,
                    future_peek,
                )
                true_components = component_market_values(target_row)
                component_fields: dict[str, float] = {}
                for component in COMPONENTS:
                    forecast_share = forecast_component_shares[component]
                    component_fields[f"{component}_forecast_effective_passengers_mid_million"] = (
                        effective_forecast_mid * forecast_share
                    )
                    component_fields[f"{component}_forecast_effective_share_pct"] = forecast_share * 100.0
                    component_fields[f"{component}_debug_hidden_true_effective_passengers_million"] = (
                        true_components[component]["effective"]
                    )
                    component_fields[f"{component}_debug_hidden_true_effective_share_pct"] = (
                        true_components[component]["effective_share_pct"]
                    )
                    component_fields[f"{component}_debug_hidden_true_potential_passengers_million"] = (
                        true_components[component]["potential"]
                    )
                    component_fields[f"{component}_debug_hidden_true_airline_supply_passengers_million"] = (
                        true_components[component]["airline_supply"]
                    )

                output.append(round_record({
                    "city_airport_potential_passenger_forecast_param_version": CITY_AIRPORT_POTENTIAL_PASSENGER_FORECAST_PARAM_VERSION,
                    "city_airport_potential_passenger_forecast_interface_version": CITY_AIRPORT_POTENTIAL_PASSENGER_FORECAST_INTERFACE_VERSION,
                    "forecast_config_version": config["config_version"],
                    "forecast_model_version": str(forecast_settings.get("forecast_model_version", "potential-passenger-forecast-v0.1")),
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
                    "forecast_report_tier": str(tier.get("forecast_report_tier", report_id)),
                    "forecast_report_source": str(tier.get("forecast_report_source", report_id)),
                    "reported_confidence_style": str(tier.get("reported_confidence_style", "unspecified")),
                    "forecast_bias_direction": str(tier.get("forecast_bias_direction", "mixed")),
                    "configured_forecast_quality_score": configured_quality,
                    "forecast_quality_score": quality,
                    "future_peek_mode": str(future_peek).lower(),
                    "forecast_year": target_year,
                    "forecast_year_index": int(as_float(target_row, "year_index", target_year - years[0])),
                    "forecast_horizon_years": horizon,
                    "current_effective_passengers_million": current_effective,
                    "current_potential_passengers_million": current_potential,
                    "current_airline_supply_passengers_million": current_airline_supply,
                    "current_market_bottleneck": current_bottleneck,
                    "naive_public_curve_effective_million": naive_effective,
                    "naive_public_curve_potential_million": potential_forecast["naive_curve"],
                    "naive_public_curve_airline_supply_million": airline_supply_forecast["naive_curve"],
                    "lagged_hidden_curve_effective_million": lagged_effective,
                    "lagged_hidden_curve_potential_million": potential_forecast["lagged_hidden"],
                    "lagged_hidden_curve_airline_supply_million": airline_supply_forecast["lagged_hidden"],
                    "forecast_effective_passengers_mid_million": effective_forecast_mid,
                    "forecast_effective_passengers_low_million": effective_forecast_low,
                    "forecast_effective_passengers_high_million": effective_forecast_high,
                    "forecast_potential_passengers_mid_million": potential_forecast["forecast_mid"],
                    "forecast_airline_supply_passengers_mid_million": airline_supply_forecast["forecast_mid"],
                    "forecast_market_bottleneck": forecast_bottleneck,
                    "forecast_downside_band_pct": downside_band,
                    "forecast_upside_band_pct": upside_band,
                    "forecast_error_band_pct": avg_band,
                    "forecast_confidence_pct": confidence,
                    "calibration_score": calibration_score,
                    "seed_signal_capture_pct": capture_pct,
                    "forecast_lag_years": lag_years,
                    "deterministic_forecast_bias_pct": bias_pct,
                    "public_consensus_anchor_pct": 100.0 - capture_pct,
                    "consensus_herding_bias_pct": herding_bias_pct,
                    "market_consensus_gap_pct": market_gap_pct,
                    "forecast_momentum_label": momentum_label(current_effective, effective_forecast_mid, horizon),
                    "forecast_long_term_tier_label": long_term_tier_label(effective_forecast_mid),
                    "forecast_reliability_label": reliability_label(confidence, future_peek),
                    "forecast_main_upside_factors": upside_factors,
                    "forecast_main_downside_factors": downside_factors,
                    "source_seed_city_momentum_label": source_seed_label,
                    "source_seed_city_potential_multiplier": source_seed_multiplier,
                    "forecast_method_note": method_note,
                    **component_fields,
                    "debug_hidden_true_effective_passengers_million": hidden_true_effective,
                    "debug_hidden_true_potential_passengers_million": hidden_true_potential,
                    "debug_hidden_true_airline_supply_passengers_million": hidden_true_airline_supply,
                    "debug_hidden_true_market_bottleneck": hidden_true_bottleneck,
                    "debug_hidden_true_inside_forecast_range": str(hidden_inside).lower(),
                    "debug_hidden_true_position_pct": hidden_position,
                    "debug_model_gap_to_true_pct": model_gap_pct,
                }))
    return annotate_realized_quality_scores(output)


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


def forecast_viewer_config(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "config_version": config.get("config_version"),
        "forecast_model_version": (
            config.get("forecast_model_version")
            or config.get("forecast", {}).get("forecast_model_version")
        ),
        "city_airport_market_id": config.get("city_airport_market_id"),
        "city_name": config.get("city_name"),
        "region_id": config.get("region_id"),
        "forecast_reports": config.get("forecast_reports", []),
    }


def write_viewer_data_js(path: Path, rows: list[dict[str, Any]], config: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"config": forecast_viewer_config(config), "rows": rows}
    path.write_text(
        "window.CITY_AIRPORT_POTENTIAL_PASSENGER_FORECAST_DATA = "
        + json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        + ";\n",
        encoding="utf-8",
    )


def safe_report_filename(report_id: str) -> str:
    clean = "".join(char if char.isalnum() or char in ("-", "_") else "_" for char in report_id)
    return clean.strip("_") or "forecast_report"


def write_viewer_lazy_assets(
    output_dir: Path,
    rows: list[dict[str, Any]],
    config: dict[str, Any],
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    market_id = str(config.get("city_airport_market_id") or "city_airport_market")
    index_filename = f"{market_id}_forecast_index.js"
    chunk_dir_name = f"{market_id}_forecast_chunks"
    chunk_dir = output_dir / chunk_dir_name
    chunk_dir.mkdir(parents=True, exist_ok=True)

    configured_ids = [
        str(item.get("forecast_report_id") or "").strip()
        for item in config.get("forecast_reports", [])
        if str(item.get("forecast_report_id") or "").strip()
    ]
    row_ids = {str(row.get("forecast_report_id") or "").strip() for row in rows}
    report_ids = [report_id for report_id in configured_ids if report_id in row_ids]
    report_ids.extend(sorted(report_id for report_id in row_ids if report_id and report_id not in report_ids))

    reports: list[dict[str, Any]] = []
    for report_id in report_ids:
        report_rows = [row for row in rows if str(row.get("forecast_report_id") or "") == report_id]
        filename = f"r_{safe_report_filename(report_id)}.json"
        chunk_payload = {
            "schemaVersion": FORECAST_VIEWER_CHUNK_VERSION,
            "reportId": report_id,
            "rowCount": len(report_rows),
            "rows": report_rows,
        }
        raw = json.dumps(chunk_payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        (chunk_dir / filename).write_bytes(raw)
        reports.append(
            {
                "reportId": report_id,
                "rowCount": len(report_rows),
                "file": filename,
                "sha256": hashlib.sha256(raw).hexdigest(),
                "bytes": len(raw),
            }
        )

    seeds = sorted({int(float(row.get("seed", 0))) for row in rows})
    default_report_id = "public_consensus" if "public_consensus" in report_ids else (report_ids[0] if report_ids else "")
    index = {
        "schemaVersion": FORECAST_VIEWER_LAZY_INDEX_VERSION,
        "chunkSchemaVersion": FORECAST_VIEWER_CHUNK_VERSION,
        "config": forecast_viewer_config(config),
        "totalRows": len(rows),
        "seeds": seeds,
        "defaultReportId": default_report_id,
        "chunkBase": f"./{chunk_dir_name}/",
        "reports": reports,
    }
    index_json = json.dumps(index, ensure_ascii=False, separators=(",", ":"))
    index_script = (
        "(() => { const index = "
        + index_json
        + "; index.baseUrl = new URL(index.chunkBase, document.currentScript.src).href; "
        + "window.AIRPORT_FORECAST_LAZY_INDEX = index; })();\n"
    )
    (output_dir / index_filename).write_text(index_script, encoding="utf-8")
    return {
        "index": str((output_dir / index_filename).as_posix()),
        "chunkDir": str(chunk_dir.as_posix()),
        "totalRows": len(rows),
        "reportCount": len(reports),
        "chunkBytes": sum(int(report["bytes"]) for report in reports),
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
    js_path = args.output_dir / f"{market_id}_potential_passenger_forecast_viewer_data.js"
    write_csv(csv_path, rows, POTENTIAL_PASSENGER_FORECAST_FIELDS)
    write_json(summary_path, summarize(rows, config))
    write_viewer_data_js(js_path, rows, config)
    lazy_assets = write_viewer_lazy_assets(args.output_dir, rows, config)
    print(json.dumps({
        "rows": len(rows),
        "csv": str(csv_path),
        "summary": str(summary_path),
        "viewer_data": str(js_path),
        "viewer_lazy": lazy_assets,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
