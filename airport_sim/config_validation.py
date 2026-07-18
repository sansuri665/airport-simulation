from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from airport_sim.paths import CONFIG_ROOT, SCHEMA_ROOT
from airport_sim.schema_validation import (
    SchemaValidationError,
    load_schema_registry,
    validate_named_schema,
)


COMPONENTS = ("business", "leisure", "vfr", "long_haul", "transfer")
QUARTERS = ("Q1", "Q2", "Q3", "Q4")
AIRLINE_SUPPLY_FIELDS = (
    "demand_pull_capture",
    "balanced_adjustment_speed",
    "expansion_adjustment_speed",
    "contraction_adjustment_speed",
    "recovery_adjustment_speed",
    "overexpansion_bias_pct",
    "overcapacity_target_pct",
    "pessimism_bias_pct",
    "expansion_trigger_pct",
    "contraction_trigger_pct",
    "minimum_supply_index",
    "shock_amplitude_pct",
    "phase_persistence",
    "upward_change_limit_pct",
    "downward_change_limit_pct",
)
AIRLINE_SUPPLY_BOUNDS = {
    "demand_pull_capture": (0.50, 1.20),
    "balanced_adjustment_speed": (0.15, 0.75),
    "expansion_adjustment_speed": (0.15, 0.75),
    "contraction_adjustment_speed": (0.20, 0.85),
    "recovery_adjustment_speed": (0.15, 0.75),
    "overexpansion_bias_pct": (0.0, 18.0),
    "overcapacity_target_pct": (0.0, 20.0),
    "pessimism_bias_pct": (0.0, 18.0),
    "expansion_trigger_pct": (0.0, 12.0),
    "contraction_trigger_pct": (0.0, 12.0),
    "minimum_supply_index": (45.0, 100.0),
    "shock_amplitude_pct": (0.0, 20.0),
    "phase_persistence": (0.60, 1.50),
    "upward_change_limit_pct": (3.0, 20.0),
    "downward_change_limit_pct": (4.0, 25.0),
}


@dataclass(frozen=True)
class ConfigFamilySpec:
    family: str
    pattern: str
    schema: str
    consumers: tuple[str, ...]

    def matches(self, relative_path: str) -> bool:
        return PurePosixPath(relative_path).match(self.pattern)


CONFIG_FAMILY_SPECS = (
    ConfigFamilySpec(
        "airport_versions",
        "airport_versions.json",
        "airport-version-record.schema.json",
        ("airport_sim/server/app.py",),
    ),
    ConfigFamilySpec(
        "airline_supply_component_allocation_profiles",
        "airline_supply_component_allocation_profiles/*.json",
        "airline-supply-component-allocation-catalog.schema.json",
        ("macro_layers/city_airport_market_demand_layer_sim.py",),
    ),
    ConfigFamilySpec(
        "airline_supply_dynamics_profiles",
        "airline_supply_dynamics_profiles/*.json",
        "airline-supply-dynamics-catalog.schema.json",
        ("macro_layers/city_airport_market_demand_layer_sim.py",),
    ),
    ConfigFamilySpec(
        "city_airport_markets",
        "city_airport_markets/**/*.json",
        "city-airport-market-config.schema.json",
        ("macro_layers/city_airport_market_demand_layer_sim.py",),
    ),
    ConfigFamilySpec(
        "city_airport_finance",
        "city_airport_finance/*.json",
        "city-airport-financial-state-config.schema.json",
        ("macro_layers/city_airport_financial_state_layer_sim.py", "airport_sim/server/app.py"),
    ),
    ConfigFamilySpec(
        "city_airport_operations_reference_defaults",
        "city_airport_operations/reference_defaults/*.json",
        "city-airport-operations-reference-defaults.schema.json",
        ("documentation-only reference defaults",),
    ),
    ConfigFamilySpec(
        "city_airport_operations_parameter_templates",
        "city_airport_operations/templates/*.json",
        "city-airport-operations-parameter-template.schema.json",
        ("documentation-only parameter template",),
    ),
    ConfigFamilySpec(
        "city_airport_operations",
        "city_airport_operations/*.json",
        "city-airport-operations-config.schema.json",
        ("macro_layers/city_airport_quarterly_operations_layer_sim.py", "airport_sim/server/app.py"),
    ),
    ConfigFamilySpec(
        "city_airport_potential_passenger_forecast",
        "city_airport_potential_passenger_forecast/*.json",
        "forecast-config.schema.json",
        ("macro_layers/forecast_system/profile_config.py",),
    ),
    ConfigFamilySpec(
        "city_airport_valuation",
        "city_airport_valuation/*.json",
        "city-airport-valuation-config.schema.json",
        ("macro_layers/city_airport_valuation_forecast_layer_sim.py",),
    ),
    ConfigFamilySpec(
        "facility_size_catalogs",
        "facility_size_catalogs/*.json",
        "facility-size-catalog.schema.json",
        (
            "macro_layers/city_airport_market_demand_layer_sim.py",
            "macro_layers/city_airport_quarterly_operations_layer_sim.py",
        ),
    ),
    ConfigFamilySpec(
        "forecast_narrative_profiles",
        "forecast_narrative_profiles/*.json",
        "forecast-narrative-catalog.schema.json",
        ("macro_layers/forecast_system/profile_config.py",),
    ),
    ConfigFamilySpec(
        "forecast_report_tier_profiles",
        "forecast_report_tier_profiles/*.json",
        "forecast-tier-catalog.schema.json",
        ("macro_layers/forecast_system/profile_config.py",),
    ),
)


@dataclass(frozen=True)
class ConfigRecord:
    path: Path
    relative_path: str
    family: ConfigFamilySpec | None
    payload: dict[str, Any]


def _issue(
    record: ConfigRecord | None,
    code: str,
    location: str,
    message: str,
    *,
    path: str | None = None,
) -> dict[str, str]:
    label = path if path is not None else (record.relative_path if record else "<config-root>")
    return {
        "path": label,
        "code": code,
        "location": location,
        "message": message,
        "error": f"{code} at {location}: {message}",
    }


def _family_for(relative_path: str) -> ConfigFamilySpec | None:
    matches = [spec for spec in CONFIG_FAMILY_SPECS if spec.matches(relative_path)]
    if len(matches) > 1:
        raise ValueError(f"ambiguous configuration family for {relative_path}: {matches!r}")
    return matches[0] if matches else None


def _reject_nonfinite_json_number(value: str) -> None:
    raise ValueError(f"non-finite JSON number is not allowed: {value}")


def _number(value: Any) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        parsed = float(value)
        return parsed if math.isfinite(parsed) else None
    return None


def _register_unique(
    index: dict[str, ConfigRecord],
    identifier: Any,
    record: ConfigRecord,
    location: str,
    errors: list[dict[str, str]],
) -> str | None:
    clean = str(identifier or "").strip()
    if not clean:
        return None
    previous = index.get(clean)
    if previous is not None:
        errors.append(
            _issue(
                record,
                "duplicate_id",
                location,
                f"identifier {clean!r} is already defined in {previous.relative_path}",
            )
        )
        return None
    index[clean] = record
    return clean


def _reference(
    record: ConfigRecord,
    identifier: Any,
    index: dict[str, ConfigRecord],
    location: str,
    label: str,
    errors: list[dict[str, str]],
) -> bool:
    clean = str(identifier or "").strip()
    if clean in index:
        return True
    errors.append(
        _issue(
            record,
            "reference_not_found",
            location,
            f"unknown {label} {clean!r}",
        )
    )
    return False


def _range_order(
    record: ConfigRecord,
    values: Any,
    location: str,
    errors: list[dict[str, str]],
) -> None:
    if not isinstance(values, list) or len(values) != 2:
        return
    lower, upper = (_number(value) for value in values)
    if lower is not None and upper is not None and lower > upper:
        errors.append(
            _issue(
                record,
                "range_order",
                location,
                f"range lower bound {lower} exceeds upper bound {upper}",
            )
        )


def _ordered_curve(
    record: ConfigRecord,
    points: Any,
    axis: str,
    location: str,
    errors: list[dict[str, str]],
) -> None:
    if not isinstance(points, list) or len(points) < 2:
        return
    values = [_number(point.get(axis)) if isinstance(point, dict) else None for point in points]
    if any(value is None for value in values):
        return
    numeric_values = [value for value in values if value is not None]
    if any(right <= left for left, right in zip(numeric_values, numeric_values[1:])):
        errors.append(
            _issue(
                record,
                "curve_order",
                location,
                f"curve axis {axis!r} must be strictly increasing",
            )
        )


CURVE_AXES = {
    "age_curve_points": "age_year",
    "curve_points": "index",
    "spread_curve": "liability_ratio_pct",
    "error_band_points": "horizon_years",
    "reported_error_band_points": "horizon_years",
}


def _validate_curves(
    record: ConfigRecord,
    value: Any,
    location: str,
    errors: list[dict[str, str]],
) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            child_location = f"{location}.{key}"
            axis = CURVE_AXES.get(str(key))
            if axis:
                _ordered_curve(record, child, axis, child_location, errors)
            _validate_curves(record, child, child_location, errors)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _validate_curves(record, child, f"{location}[{index}]", errors)


def _timeline(record: ConfigRecord) -> dict[str, Any]:
    timeline = record.payload.get("game_timeline", record.payload.get("timeline", {}))
    return timeline if isinstance(timeline, dict) else {}


def _resolve_file_reference(
    root: Path,
    records_by_path: dict[Path, ConfigRecord],
    record: ConfigRecord,
    reference: Any,
    location: str,
    errors: list[dict[str, str]],
) -> ConfigRecord | None:
    candidate = Path(str(reference or ""))
    target = (record.path.parent / candidate).resolve() if not candidate.is_absolute() else candidate.resolve()
    try:
        target.relative_to(root)
    except ValueError:
        errors.append(
            _issue(record, "reference_outside_config", location, f"reference escapes config root: {reference!r}")
        )
        return None
    target_record = records_by_path.get(target)
    if target_record is None:
        errors.append(
            _issue(record, "reference_not_found", location, f"configuration file does not exist: {reference!r}")
        )
    return target_record


def _family_records(records: list[ConfigRecord], family: str) -> list[ConfigRecord]:
    return [record for record in records if record.family and record.family.family == family]


def _validate_semantics(
    root: Path,
    records: list[ConfigRecord],
    schema_valid_paths: set[str],
    errors: list[dict[str, str]],
) -> None:
    valid_records = [record for record in records if record.relative_path in schema_valid_paths]
    records_by_path = {record.path.resolve(): record for record in valid_records}

    facility_catalogs: dict[str, ConfigRecord] = {}
    facility_sizes: dict[str, dict[str, Any]] = {}
    facility_roles: dict[str, dict[str, set[str]]] = {}
    facility_templates: dict[str, dict[int, tuple[str, ...]]] = {}
    for record in _family_records(valid_records, "facility_size_catalogs"):
        payload = record.payload
        catalog_id = _register_unique(
            facility_catalogs, payload.get("catalog_id"), record, "$.catalog_id", errors
        )
        if not catalog_id:
            continue
        sizes = payload.get("facility_sizes", {})
        roles = payload.get("slot_role_allowed_sizes", {})
        templates = payload.get("slot_count_role_templates", {})
        if "empty" not in sizes:
            errors.append(_issue(record, "required_value", "$.facility_sizes", "catalog must define 'empty'"))
        parsed_sizes: dict[str, Any] = {}
        for size_id, spec in sizes.items():
            parsed_sizes[str(size_id)] = spec
            design = _number(spec.get("design_capacity_million")) if isinstance(spec, dict) else None
            maximum = _number(spec.get("max_capacity_million")) if isinstance(spec, dict) else None
            if design is not None and maximum is not None and design > maximum:
                errors.append(
                    _issue(
                        record,
                        "range_order",
                        f"$.facility_sizes[{size_id!r}]",
                        f"design capacity {design} exceeds maximum capacity {maximum}",
                    )
                )
        parsed_roles: dict[str, set[str]] = {}
        for role, allowed in roles.items():
            parsed_roles[str(role)] = {str(value) for value in allowed}
            for size_id in allowed:
                if str(size_id) not in parsed_sizes:
                    errors.append(
                        _issue(
                            record,
                            "reference_not_found",
                            f"$.slot_role_allowed_sizes[{role!r}]",
                            f"unknown facility size {size_id!r}",
                        )
                    )
        parsed_templates: dict[int, tuple[str, ...]] = {}
        for count_text, role_values in templates.items():
            try:
                count = int(count_text)
            except (TypeError, ValueError):
                errors.append(
                    _issue(record, "invalid_id", "$.slot_count_role_templates", f"invalid slot count {count_text!r}")
                )
                continue
            role_tuple = tuple(str(value) for value in role_values)
            parsed_templates[count] = role_tuple
            if len(role_tuple) != count:
                errors.append(
                    _issue(
                        record,
                        "count_mismatch",
                        f"$.slot_count_role_templates[{count_text!r}]",
                        f"template declares {count} slots but contains {len(role_tuple)} roles",
                    )
                )
            for role in role_tuple:
                if role not in parsed_roles:
                    errors.append(
                        _issue(
                            record,
                            "reference_not_found",
                            f"$.slot_count_role_templates[{count_text!r}]",
                            f"unknown slot role {role!r}",
                        )
                    )
        facility_sizes[catalog_id] = parsed_sizes
        facility_roles[catalog_id] = parsed_roles
        facility_templates[catalog_id] = parsed_templates

    component_profiles: dict[str, ConfigRecord] = {}
    for record in _family_records(valid_records, "airline_supply_component_allocation_profiles"):
        profiles = record.payload.get("profiles", {})
        for profile_id in profiles:
            _register_unique(
                component_profiles,
                profile_id,
                record,
                f"$.profiles[{profile_id!r}]",
                errors,
            )
        default_id = str(record.payload.get("default_profile_id") or "")
        _reference(record, default_id, component_profiles, "$.default_profile_id", "component profile", errors)

    dynamics_profiles: dict[str, ConfigRecord] = {}
    dynamics_modifiers: dict[str, ConfigRecord] = {}
    dynamics_values: dict[str, dict[str, float]] = {}
    dynamics_adjustments: dict[str, dict[str, float]] = {}
    for record in _family_records(valid_records, "airline_supply_dynamics_profiles"):
        for profile_id, spec in record.payload.get("base_profiles", {}).items():
            if _register_unique(
                dynamics_profiles,
                profile_id,
                record,
                f"$.base_profiles[{profile_id!r}]",
                errors,
            ):
                dynamics_values[str(profile_id)] = {
                    field: float(spec[field]) for field in AIRLINE_SUPPLY_FIELDS
                }
        for modifier_id, spec in record.payload.get("modifier_profiles", {}).items():
            if _register_unique(
                dynamics_modifiers,
                modifier_id,
                record,
                f"$.modifier_profiles[{modifier_id!r}]",
                errors,
            ):
                adjustments = spec.get("adjustments", {})
                unknown = sorted(set(adjustments) - set(AIRLINE_SUPPLY_FIELDS))
                if unknown:
                    errors.append(
                        _issue(
                            record,
                            "unknown_field",
                            f"$.modifier_profiles[{modifier_id!r}].adjustments",
                            f"unknown airline dynamics fields: {unknown!r}",
                        )
                    )
                dynamics_adjustments[str(modifier_id)] = {
                    str(key): float(value) for key, value in adjustments.items() if key in AIRLINE_SUPPLY_FIELDS
                }

    city_markets: dict[str, ConfigRecord] = {}
    city_airports: dict[str, dict[str, dict[str, Any]]] = {}
    city_slots: dict[str, dict[str, dict[str, Any]]] = {}
    for record in _family_records(valid_records, "city_airport_markets"):
        payload = record.payload
        market = payload.get("market", {})
        market_id = _register_unique(
            city_markets,
            market.get("city_airport_market_id"),
            record,
            "$.market.city_airport_market_id",
            errors,
        )
        if not market_id:
            continue
        if record.path.stem != market_id:
            errors.append(
                _issue(
                    record,
                    "id_path_mismatch",
                    "$.market.city_airport_market_id",
                    f"market id {market_id!r} must match filename stem {record.path.stem!r}",
                )
            )
        mix = payload.get("component_mix", {})
        mix_sum = sum(float(mix.get(f"{component}_base_share_pct", 0.0)) for component in COMPONENTS)
        if not math.isclose(mix_sum, 100.0, abs_tol=1e-9):
            errors.append(
                _issue(
                    record,
                    "weight_balance",
                    "$.component_mix",
                    f"component shares must sum to 100; got {mix_sum}",
                )
            )
        demand = payload.get("demand_model", {})
        seed_model = demand.get("seed_potential_model", {})
        _range_order(record, demand.get("target_long_term_potential_range_million"), "$.demand_model.target_long_term_potential_range_million", errors)
        _range_order(record, seed_model.get("annual_growth_bias_range_pct"), "$.demand_model.seed_potential_model.annual_growth_bias_range_pct", errors)
        _range_order(record, seed_model.get("max_growth_bias_range_pct"), "$.demand_model.seed_potential_model.max_growth_bias_range_pct", errors)
        release_start = _number(seed_model.get("release_start_year_index"))
        full_effect = _number(seed_model.get("full_effect_year_index"))
        if release_start is not None and full_effect is not None and release_start > full_effect:
            errors.append(_issue(record, "range_order", "$.demand_model.seed_potential_model", "release start must not exceed full effect year index"))
        floor = _number(seed_model.get("potential_multiplier_floor"))
        ceiling = _number(seed_model.get("potential_multiplier_ceiling"))
        if floor is not None and ceiling is not None and floor > ceiling:
            errors.append(_issue(record, "range_order", "$.demand_model.seed_potential_model", "potential multiplier floor exceeds ceiling"))

        supply = payload.get("airline_supply_model", {})
        profile_id = str(supply.get("dynamics_profile_id") or "")
        profile_ok = _reference(record, profile_id, dynamics_profiles, "$.airline_supply_model.dynamics_profile_id", "airline dynamics profile", errors)
        modifier_ids = [str(value) for value in supply.get("dynamics_modifier_ids", [])]
        modifiers_ok = True
        for index, modifier_id in enumerate(modifier_ids):
            modifiers_ok &= _reference(
                record,
                modifier_id,
                dynamics_modifiers,
                f"$.airline_supply_model.dynamics_modifier_ids[{index}]",
                "airline dynamics modifier",
                errors,
            )
        overrides = supply.get("dynamics_overrides", {})
        unknown_overrides = sorted(set(overrides) - set(AIRLINE_SUPPLY_FIELDS)) if isinstance(overrides, dict) else []
        if unknown_overrides:
            errors.append(_issue(record, "unknown_field", "$.airline_supply_model.dynamics_overrides", f"unknown airline dynamics fields: {unknown_overrides!r}"))
        if profile_ok and modifiers_ok:
            effective = dict(dynamics_values[profile_id])
            for modifier_id in modifier_ids:
                for field, adjustment in dynamics_adjustments[modifier_id].items():
                    effective[field] += adjustment
            for field, value in (overrides.items() if isinstance(overrides, dict) else []):
                if field in effective:
                    effective[field] = float(value)
            for field, (lower, upper) in AIRLINE_SUPPLY_BOUNDS.items():
                if not lower <= effective[field] <= upper:
                    errors.append(
                        _issue(
                            record,
                            "range_validation",
                            f"$.airline_supply_model.{field}",
                            f"effective value {effective[field]} must stay within {lower} and {upper}",
                        )
                    )

        allocation = payload.get("airline_supply_component_allocation")
        if isinstance(allocation, dict):
            _reference(record, allocation.get("profile_id"), component_profiles, "$.airline_supply_component_allocation.profile_id", "component allocation profile", errors)

        facility_model = payload.get("facility_model", {})
        catalog_id = str(facility_model.get("facility_size_catalog") or "")
        catalog_ok = _reference(record, catalog_id, facility_catalogs, "$.facility_model.facility_size_catalog", "facility size catalog", errors)
        airports: dict[str, dict[str, Any]] = {}
        slots: dict[str, dict[str, Any]] = {}
        for airport_index, airport in enumerate(payload.get("airports", [])):
            airport_id = str(airport.get("airport_id") or "")
            if airport_id in airports:
                errors.append(_issue(record, "duplicate_id", f"$.airports[{airport_index}].airport_id", f"duplicate airport id {airport_id!r}"))
            airports[airport_id] = airport
            airport_slots = airport.get("slots", [])
            if int(airport.get("slot_count", 0)) != len(airport_slots):
                errors.append(_issue(record, "count_mismatch", f"$.airports[{airport_index}].slot_count", f"slot_count does not match {len(airport_slots)} slots"))
            role_sequence: list[str] = []
            for slot_index, slot in enumerate(airport_slots):
                slot_id = str(slot.get("slot_id") or "")
                slot_location = f"$.airports[{airport_index}].slots[{slot_index}]"
                if slot_id in slots:
                    errors.append(_issue(record, "duplicate_id", f"{slot_location}.slot_id", f"duplicate slot id {slot_id!r}"))
                slots[slot_id] = slot
                role = str(slot.get("slot_role") or "")
                role_sequence.append(role)
                if catalog_ok:
                    sizes = facility_sizes[catalog_id]
                    roles = facility_roles[catalog_id]
                    configured_size = str(slot.get("facility_size") or "")
                    configured_allowed = slot.get("allowed_sizes")
                    allowed = (
                        {str(value) for value in configured_allowed}
                        if isinstance(configured_allowed, list)
                        else roles.get(role, set())
                    )
                    if configured_size not in sizes:
                        errors.append(_issue(record, "reference_not_found", f"{slot_location}.facility_size", f"unknown facility size {configured_size!r}"))
                    if role not in roles:
                        errors.append(_issue(record, "reference_not_found", f"{slot_location}.slot_role", f"unknown slot role {role!r}"))
                    elif configured_size not in roles[role]:
                        errors.append(_issue(record, "reference_not_found", f"{slot_location}.facility_size", f"facility size {configured_size!r} is not allowed for catalog role {role!r}"))
                    elif configured_allowed is not None and configured_size not in allowed:
                        errors.append(_issue(record, "reference_not_found", f"{slot_location}.facility_size", f"facility size {configured_size!r} is not in allowed_sizes"))
                    if role in roles and configured_allowed is not None and allowed != roles[role]:
                        errors.append(_issue(record, "inventory_mismatch", f"{slot_location}.allowed_sizes", f"allowed sizes must match catalog role {role!r}"))
            if catalog_ok:
                expected_roles = facility_templates[catalog_id].get(len(airport_slots))
                if expected_roles and tuple(role_sequence) != expected_roles:
                    errors.append(_issue(record, "inventory_mismatch", f"$.airports[{airport_index}].slots", f"slot roles do not match catalog template for {len(airport_slots)} slots"))
        city_airports[market_id] = airports
        city_slots[market_id] = slots

        profile_ids: set[str] = set()
        for profile_index, profile in enumerate(payload.get("capacity_reference_profiles", [])):
            profile_id_value = profile.get("profile_id", profile.get("preset_id"))
            profile_id_clean = str(profile_id_value or "")
            if not profile_id_clean:
                errors.append(_issue(record, "required_value", f"$.capacity_reference_profiles[{profile_index}]", "profile_id or preset_id is required"))
            elif profile_id_clean in profile_ids:
                errors.append(_issue(record, "duplicate_id", f"$.capacity_reference_profiles[{profile_index}]", f"duplicate capacity profile id {profile_id_clean!r}"))
            profile_ids.add(profile_id_clean)
            assignments = profile.get("slot_assignments", {})
            if set(assignments) != set(slots):
                errors.append(_issue(record, "inventory_mismatch", f"$.capacity_reference_profiles[{profile_index}].slot_assignments", "slot assignments must cover every configured slot exactly once"))
            if catalog_ok and set(assignments) == set(slots):
                sizes = facility_sizes[catalog_id]
                unknown_sizes = sorted({str(value) for value in assignments.values()} - set(sizes))
                if unknown_sizes:
                    errors.append(_issue(record, "reference_not_found", f"$.capacity_reference_profiles[{profile_index}].slot_assignments", f"unknown facility sizes: {unknown_sizes!r}"))
                else:
                    design = sum(float(sizes[str(value)]["design_capacity_million"]) for value in assignments.values())
                    maximum = sum(float(sizes[str(value)]["max_capacity_million"]) for value in assignments.values())
                    if not math.isclose(design, float(profile.get("design_capacity_million", -1)), abs_tol=1e-9):
                        errors.append(_issue(record, "derived_value_mismatch", f"$.capacity_reference_profiles[{profile_index}].design_capacity_million", f"expected derived design capacity {design}"))
                    if not math.isclose(maximum, float(profile.get("max_capacity_million", -1)), abs_tol=1e-9):
                        errors.append(_issue(record, "derived_value_mismatch", f"$.capacity_reference_profiles[{profile_index}].max_capacity_million", f"expected derived maximum capacity {maximum}"))

    for record in _family_records(valid_records, "city_airport_operations_reference_defaults") + _family_records(valid_records, "city_airport_operations"):
        weights = record.payload.get("quarter_component_weights", {})
        for component in COMPONENTS:
            values = weights.get(component, [])
            if isinstance(values, list):
                total = sum(float(value) for value in values)
                if not math.isclose(total, 1.0, abs_tol=1e-9):
                    errors.append(_issue(record, "weight_balance", f"$.quarter_component_weights.{component}", f"quarter weights must sum to 1; got {total}"))

    for record in _family_records(valid_records, "city_airport_operations"):
        market_id = str(record.payload.get("city_airport_market_id") or "")
        market_ok = _reference(record, market_id, city_markets, "$.city_airport_market_id", "city airport market", errors)
        template_record = _resolve_file_reference(root, records_by_path, record, record.payload.get("parameter_schema"), "$.parameter_schema", errors)
        defaults_record = _resolve_file_reference(root, records_by_path, record, record.payload.get("reference_defaults"), "$.reference_defaults", errors)
        if template_record and (not template_record.family or template_record.family.family != "city_airport_operations_parameter_templates"):
            errors.append(_issue(record, "reference_type_mismatch", "$.parameter_schema", "reference must target an operations parameter template"))
        if defaults_record and (not defaults_record.family or defaults_record.family.family != "city_airport_operations_reference_defaults"):
            errors.append(_issue(record, "reference_type_mismatch", "$.reference_defaults", "reference must target operations reference defaults"))
        if template_record:
            required_fields = template_record.payload.get("required_top_level_fields", [])
            missing = [field for field in required_fields if field not in record.payload]
            if missing:
                errors.append(_issue(record, "inventory_mismatch", "$", f"parameter template requires missing fields: {missing!r}"))
        for model_name in ("facility_renovation_model", "facility_construction_model", "facility_rebuild_model"):
            model = record.payload.get(model_name, {})
            _reference(record, model.get("facility_size_catalog"), facility_catalogs, f"$.{model_name}.facility_size_catalog", "facility size catalog", errors)
        quality_model = record.payload.get("commercial", {}).get("perceived_quality_model", {})
        if quality_model:
            _reference(record, quality_model.get("facility_size_catalog"), facility_catalogs, "$.commercial.perceived_quality_model.facility_size_catalog", "facility size catalog", errors)
        if market_ok:
            airports = city_airports[market_id]
            slots = city_slots[market_id]
            catalog_id = str(city_markets[market_id].payload.get("facility_model", {}).get("facility_size_catalog") or "")
            sizes = facility_sizes.get(catalog_id, {})
            event_ids: set[str] = set()
            for collection_name in ("facility_renovation_events", "facility_construction_events", "facility_rebuild_events"):
                for event_index, event in enumerate(record.payload.get(collection_name, [])):
                    base = f"$.{collection_name}[{event_index}]"
                    event_id = str(event.get("event_id") or "")
                    if event_id in event_ids:
                        errors.append(_issue(record, "duplicate_id", f"{base}.event_id", f"duplicate facility event id {event_id!r}"))
                    event_ids.add(event_id)
                    if str(event.get("airport_id") or "") not in airports:
                        errors.append(_issue(record, "reference_not_found", f"{base}.airport_id", f"unknown airport id {event.get('airport_id')!r}"))
                    if str(event.get("slot_id") or "") not in slots:
                        errors.append(_issue(record, "reference_not_found", f"{base}.slot_id", f"unknown slot id {event.get('slot_id')!r}"))
                    for size_key in ("facility_size", "from_facility_size", "target_facility_size"):
                        if size_key in event and str(event[size_key]) not in sizes:
                            errors.append(_issue(record, "reference_not_found", f"{base}.{size_key}", f"unknown facility size {event[size_key]!r}"))

    for record in _family_records(valid_records, "city_airport_finance"):
        market_id = str(record.payload.get("city_airport_market_id") or "")
        market_ok = _reference(record, market_id, city_markets, "$.city_airport_market_id", "city airport market", errors)
        loan_ids: set[str] = set()
        for index, loan in enumerate(record.payload.get("general_loans", [])):
            loan_id = str(loan.get("loan_id") or "")
            if loan_id in loan_ids:
                errors.append(_issue(record, "duplicate_id", f"$.general_loans[{index}].loan_id", f"duplicate loan id {loan_id!r}"))
            loan_ids.add(loan_id)
            grace = int(loan.get("grace_period_quarters", 0))
            tenor = int(loan.get("tenor_quarters", 0))
            if grace >= tenor and grace > 0:
                errors.append(_issue(record, "range_order", f"$.general_loans[{index}].grace_period_quarters", "grace period must be shorter than loan tenor"))
        assets: set[str] = set()
        for index, asset in enumerate(record.payload.get("initial_assets", [])):
            base = f"$.initial_assets[{index}]"
            asset_id = str(asset.get("asset_id") or "")
            if asset_id in assets:
                errors.append(_issue(record, "duplicate_id", f"{base}.asset_id", f"duplicate asset id {asset_id!r}"))
            assets.add(asset_id)
            if market_ok:
                if str(asset.get("airport_id") or "") not in city_airports[market_id]:
                    errors.append(_issue(record, "reference_not_found", f"{base}.airport_id", f"unknown airport id {asset.get('airport_id')!r}"))
                slot = city_slots[market_id].get(str(asset.get("slot_id") or ""))
                if slot is None:
                    errors.append(_issue(record, "reference_not_found", f"{base}.slot_id", f"unknown slot id {asset.get('slot_id')!r}"))
                elif str(asset.get("facility_size") or "") != str(slot.get("facility_size") or ""):
                    errors.append(_issue(record, "inventory_mismatch", f"{base}.facility_size", "initial asset facility size must match the city slot"))
        rate_model = record.payload.get("debt_policy", {}).get("loan_rate_model", {})
        minimum_rate = _number(rate_model.get("min_annual_interest_rate_pct"))
        maximum_rate = _number(rate_model.get("max_annual_interest_rate_pct"))
        if minimum_rate is not None and maximum_rate is not None and minimum_rate > maximum_rate:
            errors.append(_issue(record, "range_order", "$.debt_policy.loan_rate_model", "minimum interest rate exceeds maximum interest rate"))

    for record in _family_records(valid_records, "city_airport_valuation"):
        market_id = str(record.payload.get("city_airport_market_id") or "")
        _reference(record, market_id, city_markets, "$.city_airport_market_id", "city airport market", errors)
        forecast = record.payload.get("forecast", {})
        valuation = record.payload.get("valuation", {})
        ordered_pairs = (
            (forecast, "annual_growth_floor_pct", "annual_growth_cap_pct", "$.forecast"),
            (valuation, "risk_free_rate_floor_pct", "risk_free_rate_cap_pct", "$.valuation"),
            (valuation, "discount_rate_floor_pct", "discount_rate_cap_pct", "$.valuation"),
            (valuation, "terminal_growth_floor_pct", "terminal_growth_cap_pct", "$.valuation"),
            (valuation, "leverage_risk_start_pct", "leverage_risk_full_pct", "$.valuation"),
            (valuation.get("operating_value", {}), "operating_discount_rate_floor_pct", "operating_discount_rate_cap_pct", "$.valuation.operating_value"),
            (valuation.get("uncertainty", {}), "range_floor_pct", "range_cap_pct", "$.valuation.uncertainty"),
        )
        for container, lower_key, upper_key, location in ordered_pairs:
            lower = _number(container.get(lower_key)) if isinstance(container, dict) else None
            upper = _number(container.get(upper_key)) if isinstance(container, dict) else None
            if lower is not None and upper is not None and lower > upper:
                errors.append(_issue(record, "range_order", location, f"{lower_key} exceeds {upper_key}"))

    tier_profiles: dict[str, ConfigRecord] = {}
    for record in _family_records(valid_records, "forecast_report_tier_profiles"):
        for index, profile in enumerate(record.payload.get("profiles", [])):
            _register_unique(tier_profiles, profile.get("forecast_report_tier_profile_id"), record, f"$.profiles[{index}].forecast_report_tier_profile_id", errors)
            candidate = profile.get("candidate_generation", {})
            for lower_key, upper_key in (("quality_min_score", "quality_max_score"), ("signal_capture_min_pct", "signal_capture_max_pct")):
                lower = _number(candidate.get(lower_key))
                upper = _number(candidate.get(upper_key))
                if lower is not None and upper is not None and lower > upper:
                    errors.append(_issue(record, "range_order", f"$.profiles[{index}].candidate_generation", f"{lower_key} exceeds {upper_key}"))

    narrative_profiles: dict[str, ConfigRecord] = {}
    narrative_modifiers: dict[str, ConfigRecord] = {}
    narrative_profile_payloads: list[tuple[ConfigRecord, int, dict[str, Any]]] = []
    for record in _family_records(valid_records, "forecast_narrative_profiles"):
        for index, profile in enumerate(record.payload.get("profiles", [])):
            _register_unique(narrative_profiles, profile.get("forecast_narrative_profile_id"), record, f"$.profiles[{index}].forecast_narrative_profile_id", errors)
            narrative_profile_payloads.append((record, index, profile))
        for index, modifier in enumerate(record.payload.get("modifiers", [])):
            _register_unique(narrative_modifiers, modifier.get("forecast_narrative_modifier_id"), record, f"$.modifiers[{index}].forecast_narrative_modifier_id", errors)
    for record, index, profile in narrative_profile_payloads:
        for modifier_index, modifier_id in enumerate(profile.get("candidate_modifier_ids", [])):
            _reference(record, modifier_id, narrative_modifiers, f"$.profiles[{index}].candidate_modifier_ids[{modifier_index}]", "forecast narrative modifier", errors)

    for record in _family_records(valid_records, "city_airport_potential_passenger_forecast"):
        _reference(record, record.payload.get("city_airport_market_id"), city_markets, "$.city_airport_market_id", "city airport market", errors)
        _resolve_file_reference(root, records_by_path, record, record.payload.get("forecast_report_tier_catalog"), "$.forecast_report_tier_catalog", errors)
        _resolve_file_reference(root, records_by_path, record, record.payload.get("forecast_narrative_catalog"), "$.forecast_narrative_catalog", errors)
        report_ids: set[str] = set()
        for index, report in enumerate(record.payload.get("forecast_reports", [])):
            base = f"$.forecast_reports[{index}]"
            report_id = str(report.get("forecast_report_id") or "")
            if report_id in report_ids:
                errors.append(_issue(record, "duplicate_id", f"{base}.forecast_report_id", f"duplicate forecast report id {report_id!r}"))
            report_ids.add(report_id)
            _reference(record, report.get("forecast_report_tier_profile_id"), tier_profiles, f"{base}.forecast_report_tier_profile_id", "forecast tier profile", errors)
            _reference(record, report.get("forecast_narrative_profile_id"), narrative_profiles, f"{base}.forecast_narrative_profile_id", "forecast narrative profile", errors)
            for modifier_index, modifier_id in enumerate(report.get("forecast_narrative_modifier_ids", [])):
                _reference(record, modifier_id, narrative_modifiers, f"{base}.forecast_narrative_modifier_ids[{modifier_index}]", "forecast narrative modifier", errors)
            quality = report.get("dynamic_quality", {})
            if isinstance(quality, dict):
                minimum = _number(quality.get("min_score"))
                maximum = _number(quality.get("max_score"))
                if minimum is not None and maximum is not None and minimum > maximum:
                    errors.append(_issue(record, "range_order", f"{base}.dynamic_quality", "min_score exceeds max_score"))
        forecast = record.payload.get("forecast", {})
        minimum_horizon = int(forecast.get("forecast_horizon_min_years", 0))
        maximum_horizon = int(forecast.get("forecast_horizon_max_years", 0))
        step = int(forecast.get("forecast_horizon_step_years", 0))
        if minimum_horizon > maximum_horizon:
            errors.append(_issue(record, "range_order", "$.forecast", "minimum forecast horizon exceeds maximum"))
        elif step > 0 and (maximum_horizon - minimum_horizon) % step:
            errors.append(_issue(record, "range_alignment", "$.forecast.forecast_horizon_step_years", "forecast horizon range is not divisible by the configured step"))

    timeline_by_market: dict[str, list[tuple[ConfigRecord, dict[str, Any]]]] = {}
    for family in ("city_airport_operations", "city_airport_finance", "city_airport_valuation"):
        for record in _family_records(valid_records, family):
            market_id = str(record.payload.get("city_airport_market_id") or "")
            timeline_by_market.setdefault(market_id, []).append((record, _timeline(record)))
    for market_id, entries in timeline_by_market.items():
        if len(entries) < 2:
            continue
        keys = ("simulation_start_year", "startup_operating_history_years", "player_decision_start_year")
        expected = {key: entries[0][1].get(key) for key in keys}
        for record, timeline in entries[1:]:
            for key in keys:
                if timeline.get(key) != expected[key]:
                    errors.append(_issue(record, "cross_file_mismatch", f"$.{key}", f"timeline field {key!r} for {market_id!r} differs from {entries[0][0].relative_path}"))

    for record in valid_records:
        _validate_curves(record, record.payload, "$", errors)


def validate_config_tree(
    config_root: Path = CONFIG_ROOT,
    *,
    schema_root: Path = SCHEMA_ROOT,
    require_classified: bool | None = None,
) -> dict[str, Any]:
    root = config_root.expanduser().resolve()
    schemas = schema_root.expanduser().resolve()
    if require_classified is None:
        require_classified = root == CONFIG_ROOT.resolve()
    errors: list[dict[str, str]] = []
    if not root.is_dir():
        errors.append(
            _issue(
                None,
                "config_root_missing",
                "$",
                "configuration directory does not exist",
                path=str(root),
            )
        )
        paths: list[Path] = []
    else:
        paths = sorted(path for path in root.rglob("*.json") if path.is_file())

    try:
        registry = load_schema_registry(schemas)
    except (OSError, UnicodeError, json.JSONDecodeError, SchemaValidationError) as exc:
        registry = {}
        errors.append(_issue(None, "schema_registry", "$", str(exc), path=str(schemas)))

    records: list[ConfigRecord] = []
    schema_valid_paths: set[str] = set()
    unclassified_count = 0
    for path in paths:
        relative_path = path.relative_to(root).as_posix()
        try:
            with path.open("r", encoding="utf-8") as handle:
                payload = json.load(
                    handle,
                    object_pairs_hook=_object_without_duplicate_keys,
                    parse_constant=_reject_nonfinite_json_number,
                )
            if not isinstance(payload, dict):
                raise ValueError("configuration document must be a JSON object")
        except DuplicateJsonKeyError as exc:
            errors.append(_issue(None, "duplicate_object_keys", "$", str(exc), path=relative_path))
            continue
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
            errors.append(_issue(None, "json_syntax", "$", str(exc), path=relative_path))
            continue

        family = _family_for(relative_path)
        record = ConfigRecord(path.resolve(), relative_path, family, payload)
        records.append(record)
        if family is None:
            unclassified_count += 1
            if require_classified:
                errors.append(
                    _issue(
                        record,
                        "family_unclassified",
                        "$",
                        "configuration file is not covered by a registered family",
                    )
                )
            continue
        if family.schema not in registry:
            errors.append(
                _issue(
                    record,
                    "schema_not_found",
                    "$",
                    f"registered schema does not exist: {family.schema}",
                )
            )
            continue
        try:
            validate_named_schema(payload, family.schema, registry)
        except SchemaValidationError as exc:
            errors.append(
                _issue(
                    record,
                    "schema_validation",
                    exc.location,
                    exc.message,
                )
            )
            continue
        schema_valid_paths.add(relative_path)

    _validate_semantics(root, records, schema_valid_paths, errors)
    invalid_paths = {error["path"] for error in errors if error["path"] in {path.relative_to(root).as_posix() for path in paths}}
    family_summaries: list[dict[str, Any]] = []
    for spec in CONFIG_FAMILY_SPECS:
        family_records = [record for record in records if record.family == spec]
        invalid = sum(record.relative_path in invalid_paths for record in family_records)
        family_summaries.append(
            {
                "family": spec.family,
                "pattern": spec.pattern,
                "schema": spec.schema,
                "consumers": list(spec.consumers),
                "fileCount": len(family_records),
                "validCount": len(family_records) - invalid,
                "invalidCount": invalid,
            }
        )

    return {
        "schemaVersion": "airport-config-validation-v2",
        "configRoot": str(root),
        "schemaRoot": str(schemas),
        "fileCount": len(paths),
        "validCount": max(0, len(paths) - len(invalid_paths)),
        "invalidCount": len(invalid_paths) + sum(
            error["path"] not in {path.relative_to(root).as_posix() for path in paths}
            for error in errors
        ),
        "issueCount": len(errors),
        "familyCount": len(CONFIG_FAMILY_SPECS),
        "unclassifiedCount": unclassified_count,
        "checks": [
            "json_syntax",
            "duplicate_object_keys",
            "family_classification",
            "json_schema",
            "id_uniqueness",
            "numeric_ranges",
            "cross_file_references",
            "weight_balance",
            "curve_order",
            "derived_capacity",
        ],
        "families": family_summaries,
        "errors": errors,
    }


class DuplicateJsonKeyError(ValueError):
    """Raised when a JSON object contains an ambiguous duplicate key."""


def _object_without_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateJsonKeyError(f"duplicate JSON key: {key}")
        result[key] = value
    return result
