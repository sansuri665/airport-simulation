from __future__ import annotations

import json
from importlib import import_module
from pathlib import Path
from typing import Any


_PARENT_PACKAGE = (
    (__package__ or "").rsplit(".", 1)[0]
    if "." in (__package__ or "")
    else ""
)
_PARENT_PREFIX = f"{_PARENT_PACKAGE}." if _PARENT_PACKAGE else ""
simulation_utils = import_module(f"{_PARENT_PREFIX}simulation_utils")
clamp = simulation_utils.clamp

AIRPORT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_DIR = AIRPORT_DIR / "config" / "city_airport_potential_passenger_forecast"
DEFAULT_TIER_CATALOG = (
    AIRPORT_DIR
    / "config"
    / "forecast_report_tier_profiles"
    / "forecast_report_tier_profiles_v1.json"
)
DEFAULT_NARRATIVE_CATALOG = (
    AIRPORT_DIR
    / "config"
    / "forecast_narrative_profiles"
    / "forecast_narrative_profiles_v2.json"
)
def catalog_path(config_path: Path, configured: Any, fallback: Path) -> Path:
    if not configured:
        return fallback
    candidate = Path(str(configured))
    if candidate.is_absolute():
        return candidate
    return (config_path.parent / candidate).resolve()


def catalog_items(
    path: Path,
    *,
    expected_schema: str,
    collection: str,
    id_field: str,
) -> dict[str, dict[str, Any]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if raw.get("schema_version") != expected_schema:
        raise ValueError(f"Unsupported forecast catalog schema in {path}")
    output: dict[str, dict[str, Any]] = {}
    for item in raw.get(collection, []):
        item_id = str(item.get(id_field) or "").strip()
        if not item_id:
            raise ValueError(f"Missing {id_field} in {path}")
        if item_id in output:
            raise ValueError(f"Duplicate {id_field}={item_id} in {path}")
        output[item_id] = dict(item)
    return output


def apply_narrative_modifier(target: dict[str, Any], modifier: dict[str, Any]) -> None:
    for key, delta in modifier.get("parameter_deltas", {}).items():
        target[key] = float(target.get(key, 0.0)) + float(delta)
    for key, multiplier in modifier.get("parameter_multipliers", {}).items():
        target[key] = float(target.get(key, 0.0)) * float(multiplier)


def resolve_forecast_report_profiles(
    raw: dict[str, Any],
    config_path: Path,
) -> list[dict[str, Any]]:
    tier_profiles = catalog_items(
        catalog_path(
            config_path,
            raw.get("forecast_report_tier_catalog"),
            DEFAULT_TIER_CATALOG,
        ),
        expected_schema="forecast-report-tier-profile-catalog-v1",
        collection="profiles",
        id_field="forecast_report_tier_profile_id",
    )
    narrative_catalog_path = catalog_path(
        config_path,
        raw.get("forecast_narrative_catalog"),
        DEFAULT_NARRATIVE_CATALOG,
    )
    narrative_profiles = catalog_items(
        narrative_catalog_path,
        expected_schema="forecast-narrative-profile-catalog-v1",
        collection="profiles",
        id_field="forecast_narrative_profile_id",
    )
    narrative_modifiers = catalog_items(
        narrative_catalog_path,
        expected_schema="forecast-narrative-profile-catalog-v1",
        collection="modifiers",
        id_field="forecast_narrative_modifier_id",
    )

    resolved: list[dict[str, Any]] = []
    seen_report_ids: set[str] = set()
    for report in raw.get("forecast_reports", []):
        report_id = str(report.get("forecast_report_id") or "").strip()
        if not report_id or report_id in seen_report_ids:
            raise ValueError(f"Invalid or duplicate forecast_report_id={report_id!r}")
        seen_report_ids.add(report_id)
        tier_profile_id = str(report.get("forecast_report_tier_profile_id") or "").strip()
        narrative_profile_id = str(report.get("forecast_narrative_profile_id") or "").strip()
        if tier_profile_id not in tier_profiles:
            raise ValueError(f"Unknown forecast report tier profile {tier_profile_id!r}")
        if narrative_profile_id not in narrative_profiles:
            raise ValueError(f"Unknown forecast narrative profile {narrative_profile_id!r}")

        merged = {
            **tier_profiles[tier_profile_id],
            **narrative_profiles[narrative_profile_id],
        }
        modifier_ids = [
            str(value).strip()
            for value in report.get("forecast_narrative_modifier_ids", [])
            if str(value).strip()
        ]
        if len(modifier_ids) > 2:
            raise ValueError(f"Forecast report {report_id} may use at most two narrative modifiers")
        for modifier_id in modifier_ids:
            if modifier_id not in narrative_modifiers:
                raise ValueError(f"Unknown forecast narrative modifier {modifier_id!r}")
            apply_narrative_modifier(merged, narrative_modifiers[modifier_id])
        merged.update(report)
        merged["forecast_report_tier_profile_id"] = tier_profile_id
        merged["forecast_narrative_profile_id"] = narrative_profile_id
        merged["forecast_narrative_modifier_ids"] = modifier_ids
        merged["forecast_narrative_modifier_labels"] = [
            str(narrative_modifiers[modifier_id].get("modifier_label") or modifier_id)
            for modifier_id in modifier_ids
        ]
        merged["forecast_narrative_modifier_groups"] = [
            str(narrative_modifiers[modifier_id].get("modifier_group") or "other")
            for modifier_id in modifier_ids
        ]
        merged["forecast_narrative_modifier_descriptions"] = [
            str(narrative_modifiers[modifier_id].get("modifier_description") or "")
            for modifier_id in modifier_ids
        ]
        merged["forecast_narrative_modifier_tradeoffs"] = [
            str(narrative_modifiers[modifier_id].get("modifier_tradeoff") or "")
            for modifier_id in modifier_ids
        ]
        for bounded_key in (
            "signal_observation_quality",
            "signal_miss_rate",
            "signal_misclassification_rate",
            "component_signal_quality",
            "narrative_demand_signal_weight",
            "narrative_supply_signal_weight",
            "narrative_trend_extrapolation",
            "narrative_mean_reversion",
            "narrative_turn_sensitivity",
            "narrative_thesis_persistence",
            "narrative_revision_speed",
        ):
            if bounded_key in merged:
                merged[bounded_key] = clamp(float(merged[bounded_key]), 0.0, 1.0)
        resolved.append(merged)
    return resolved


def load_config(path: Path) -> dict[str, Any]:
    path = path.resolve()
    raw = json.loads(path.read_text(encoding="utf-8"))
    if raw.get("schema_version") != "city-airport-potential-passenger-forecast-config-v1":
        raise ValueError(
            f"Unsupported city airport potential passenger forecast config schema in {path}"
        )
    raw["forecast_reports"] = resolve_forecast_report_profiles(raw, path)
    return raw
