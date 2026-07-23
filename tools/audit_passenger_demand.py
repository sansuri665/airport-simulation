#!/usr/bin/env python3
"""Read-only audit surface for passenger-demand model outputs.

The audit classifies a component path as increasing, decreasing, or approximately
unchanged by comparing its end share with its start share.  Changes whose
absolute magnitude is at most ``DIRECTION_TOLERANCE_PP`` are classified as
approximately unchanged.  New G3 CSVs expose the real pre-boundary target,
state, flags, and consecutive streak.  Legacy CSVs remain supported and are
explicitly downgraded to ``final_output_only`` rather than having raw activity
inferred from rounded final values.

Only Python's standard library is used.  The output is deterministic: mappings
are constructed in sorted order and JSON serialization uses stable key order.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import statistics
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


AUDIT_SCHEMA_VERSION = "passenger-demand-audit-v2"
COMPARISON_SCHEMA_VERSION = "passenger-demand-audit-comparison-v1"
COMPONENTS = ("business", "leisure", "vfr", "long_haul", "transfer")
DIRECTION_TOLERANCE_PP = 0.0001
SHARE_TOLERANCE_PCT = 0.001
PASSENGER_TOLERANCE_MILLION = 0.001
BOUNDARY_TOLERANCE_MILLION = 0.001

CITY_INDEX_BOUNDARIES: dict[str, tuple[float, float]] = {
    "business": (65.0, 245.0),
    "leisure": (55.0, 230.0),
    "vfr": (65.0, 225.0),
    "long_haul": (55.0, 210.0),
    "transfer": (45.0, 185.0),
}

CITY_BOUNDARY_DIAGNOSTIC_STRING_FIELDS = {
    f"{component}_city_demand_boundary_state" for component in COMPONENTS
}
CITY_BOUNDARY_DIAGNOSTIC_NUMERIC_FIELDS = {
    field
    for component in COMPONENTS
    for field in (
        f"{component}_city_demand_raw_index",
        f"{component}_city_demand_floor_applied",
        f"{component}_city_demand_cap_applied",
        f"{component}_city_demand_consecutive_boundary_years",
    )
}
CITY_BOUNDARY_DIAGNOSTIC_FIELDS = (
    CITY_BOUNDARY_DIAGNOSTIC_STRING_FIELDS
    | CITY_BOUNDARY_DIAGNOSTIC_NUMERIC_FIELDS
)

CITY_G4_SUPPLY_STRING_FIELDS = {
    "airline_supply_dynamics_profile_id",
    "airline_supply_dynamics_modifier_ids",
    "airline_component_allocation_profile_id",
    "city_airline_supply_behavior_phase",
}
CITY_G4_SUPPLY_NUMERIC_FIELDS = {
    "city_airline_offered_capacity_million",
    "city_airline_serviceable_supply_million",
    "city_airline_unused_capacity_million",
    "city_airline_supply_fulfillment_pct",
    *(f"{component}_airline_offered_capacity_million" for component in COMPONENTS),
    *(f"{component}_airline_supply_passengers_million" for component in COMPONENTS),
    *(f"{component}_airline_supply_fulfillment_pct" for component in COMPONENTS),
    *(f"{component}_airline_supply_gap_million" for component in COMPONENTS),
}
CITY_G4_SUPPLY_FIELDS = CITY_G4_SUPPLY_STRING_FIELDS | CITY_G4_SUPPLY_NUMERIC_FIELDS

LAYER_DEFINITIONS: dict[str, dict[str, Any]] = {
    "regional_aviation_demand": {
        "pattern": "*_aviation_demand_seed_sweep.csv",
        "entity_id": "region_id",
        "entity_name": "region_name",
        "interface": "regional_aviation_demand_interface_version",
        "param_version": "regional_aviation_demand_param_version",
        "required_strings": {
            "region_id",
            "region_name",
            "regional_aviation_demand_interface_version",
            "regional_aviation_demand_param_version",
        },
        "required_numbers": {
            "year_index",
            "year",
            "seed",
            *(f"{component}_travel_share_pct" for component in COMPONENTS[:3]),
            "long_haul_share_pct",
            "transfer_share_pct",
        },
    },
    "regional_air_capacity_supply": {
        "pattern": "*_air_capacity_supply_seed_sweep.csv",
        "entity_id": "region_id",
        "entity_name": "region_name",
        "interface": "regional_air_supply_interface_version",
        "param_version": "regional_air_supply_param_version",
        "required_strings": {
            "region_id",
            "region_name",
            "regional_air_supply_interface_version",
            "regional_air_supply_param_version",
        },
        "required_numbers": {
            "year_index",
            "year",
            "seed",
            "potential_passengers_million",
            "reference_effective_passenger_capacity_million",
            "reference_served_passengers_million",
            "reference_unmet_passengers_million",
        },
    },
    "city_airport_market_demand": {
        "pattern": "*_city_airport_demand_seed_sweep.csv",
        "entity_id": "city_airport_market_id",
        "entity_name": "city_name",
        "interface": "city_airport_demand_interface_version",
        "param_version": "city_airport_demand_param_version",
        "required_strings": {
            "city_airport_market_id",
            "city_name",
            "region_id",
            "region_name",
            "city_airport_demand_interface_version",
            "city_airport_demand_param_version",
            "city_binding_bottleneck",
        },
        "required_numbers": {
            "year_index",
            "year",
            "seed",
            "baseline_region_demand_share_pct",
            "source_region_reference_potential_passengers_million",
            "city_potential_passengers_million",
            "city_effective_capacity_million",
            "city_airline_serviceable_supply_million",
            "city_served_passengers_million",
            "city_unmet_passengers_million",
            *(f"{component}_city_demand_index" for component in COMPONENTS),
            *(f"{component}_passenger_share_pct" for component in COMPONENTS),
            *(f"{component}_passengers_million" for component in COMPONENTS),
            *(f"{component}_served_passengers_million" for component in COMPONENTS),
        },
    },
}


class AuditError(ValueError):
    """Raised for input, schema, or consistency errors."""


@dataclass
class LayerData:
    name: str
    files: list[Path]
    rows_by_entity: dict[str, list[dict[str, Any]]]
    entity_names: dict[str, str]
    interfaces: tuple[str, ...]
    param_versions: tuple[str, ...]
    seed: int
    year_indexes: tuple[int, ...]
    year_by_index: dict[int, int]
    numeric_value_count: int
    columns: tuple[str, ...]

    @property
    def row_count(self) -> int:
        return sum(len(rows) for rows in self.rows_by_entity.values())


@dataclass
class CheckAccumulator:
    name: str
    unit: str
    tolerance: float
    sample_count: int = 0
    max_abs_error: float = 0.0
    failure_count: int = 0
    examples: list[dict[str, Any]] = field(default_factory=list)

    def add(self, error: float, location: Mapping[str, Any], **values: float) -> None:
        absolute_error = abs(error)
        self.sample_count += 1
        self.max_abs_error = max(self.max_abs_error, absolute_error)
        if absolute_error > self.tolerance:
            self.failure_count += 1
            if len(self.examples) < 5:
                example = dict(location)
                example.update({key: _clean_number(value) for key, value in values.items()})
                example["absolute_error"] = _clean_number(absolute_error)
                self.examples.append(example)

    def as_dict(self) -> dict[str, Any]:
        return {
            "check_name": self.name,
            "unit": self.unit,
            "sample_count": self.sample_count,
            "max_absolute_error": _clean_number(self.max_abs_error),
            "tolerance": self.tolerance,
            "failure_count": self.failure_count,
            "failure_examples": self.examples,
        }


def _clean_number(value: float) -> float:
    rounded = round(float(value), 10)
    return 0.0 if rounded == 0.0 else rounded


def _stable_display_name(path: Path) -> str:
    raw = path.name or "."
    pieces = [piece for piece in re.split(r"[\\/]+", raw) if piece]
    return pieces[-1] if pieces else "."


def _warning(code: str, message: str, **context: Any) -> dict[str, Any]:
    result: dict[str, Any] = {"code": code, "message": message}
    if context:
        result["context"] = context
    return result


def _relative_label(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.name


def _parse_float(value: str | None, *, field_name: str, file_label: str, row_number: int) -> float:
    if value is None or value.strip() == "":
        raise AuditError(f"{file_label}: row {row_number}: missing numeric value {field_name}")
    try:
        result = float(value)
    except ValueError as exc:
        raise AuditError(
            f"{file_label}: row {row_number}: invalid numeric value for {field_name}"
        ) from exc
    if not math.isfinite(result):
        raise AuditError(
            f"{file_label}: row {row_number}: non-finite numeric value for {field_name}"
        )
    return result


def _parse_int(value: str | None, *, field_name: str, file_label: str, row_number: int) -> int:
    parsed = _parse_float(value, field_name=field_name, file_label=file_label, row_number=row_number)
    if not parsed.is_integer():
        raise AuditError(f"{file_label}: row {row_number}: {field_name} must be an integer")
    return int(parsed)


def _read_layer(input_root: Path, layer_name: str) -> LayerData:
    definition = LAYER_DEFINITIONS[layer_name]
    layer_root = input_root / layer_name
    if not layer_root.is_dir():
        raise AuditError(f"missing required layer directory: {layer_name}")
    files = sorted(layer_root.rglob(definition["pattern"]), key=lambda path: path.as_posix())
    if not files:
        raise AuditError(f"no matching CSV files in required layer: {layer_name}")

    rows_by_entity: dict[str, list[dict[str, Any]]] = {}
    entity_names: dict[str, str] = {}
    interfaces: set[str] = set()
    param_versions: set[str] = set()
    layer_seed: int | None = None
    common_year_indexes: tuple[int, ...] | None = None
    common_year_by_index: dict[int, int] | None = None
    numeric_value_count = 0
    common_columns: set[str] | None = None

    required_columns = (
        set(definition["required_strings"])
        | set(definition["required_numbers"])
    )

    for path in files:
        label = _relative_label(path, input_root)
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None:
                raise AuditError(f"{label}: missing CSV header")
            duplicate_headers = sorted(
                {name for name in reader.fieldnames if reader.fieldnames.count(name) > 1}
            )
            if duplicate_headers:
                raise AuditError(f"{label}: duplicate CSV columns: {', '.join(duplicate_headers)}")
            fieldnames = set(reader.fieldnames)
            missing_columns = sorted(required_columns - fieldnames)
            if missing_columns:
                raise AuditError(f"{label}: missing required columns: {', '.join(missing_columns)}")
            common_columns = fieldnames if common_columns is None else common_columns & fieldnames
            optional_string_fields = (
                CITY_BOUNDARY_DIAGNOSTIC_STRING_FIELDS & fieldnames
                if layer_name == "city_airport_market_demand"
                else set()
            )
            optional_numeric_fields = (
                CITY_BOUNDARY_DIAGNOSTIC_NUMERIC_FIELDS & fieldnames
                if layer_name == "city_airport_market_demand"
                else set()
            )
            optional_supply_string_fields = (
                CITY_G4_SUPPLY_STRING_FIELDS & fieldnames
                if layer_name == "city_airport_market_demand"
                else set()
            )
            optional_supply_numeric_fields = (
                CITY_G4_SUPPLY_NUMERIC_FIELDS & fieldnames
                if layer_name == "city_airport_market_demand"
                else set()
            )

            parsed_rows: list[dict[str, Any]] = []
            for row_number, source_row in enumerate(reader, start=2):
                row: dict[str, Any] = {}
                for field_name in definition["required_strings"]:
                    raw = source_row.get(field_name)
                    if raw is None or raw.strip() == "":
                        raise AuditError(
                            f"{label}: row {row_number}: missing string value {field_name}"
                        )
                    row[field_name] = raw.strip()
                for field_name in definition["required_numbers"]:
                    if field_name in {"year_index", "year", "seed"}:
                        row[field_name] = _parse_int(
                            source_row.get(field_name),
                            field_name=field_name,
                            file_label=label,
                            row_number=row_number,
                        )
                    else:
                        row[field_name] = _parse_float(
                            source_row.get(field_name),
                            field_name=field_name,
                            file_label=label,
                            row_number=row_number,
                        )
                    numeric_value_count += 1
                for field_name in optional_string_fields:
                    raw = source_row.get(field_name)
                    if raw is None or raw.strip() == "":
                        raise AuditError(
                            f"{label}: row {row_number}: missing diagnostic string {field_name}"
                        )
                    row[field_name] = raw.strip()
                for field_name in optional_numeric_fields:
                    if field_name.endswith((
                        "consecutive_boundary_years",
                        "floor_applied",
                        "cap_applied",
                    )):
                        row[field_name] = _parse_int(
                            source_row.get(field_name),
                            field_name=field_name,
                            file_label=label,
                            row_number=row_number,
                        )
                    else:
                        row[field_name] = _parse_float(
                            source_row.get(field_name),
                            field_name=field_name,
                            file_label=label,
                            row_number=row_number,
                        )
                    numeric_value_count += 1
                for field_name in optional_supply_string_fields:
                    raw = source_row.get(field_name)
                    if raw is None:
                        raise AuditError(
                            f"{label}: row {row_number}: missing supply string {field_name}"
                        )
                    row[field_name] = raw.strip()
                for field_name in optional_supply_numeric_fields:
                    row[field_name] = _parse_float(
                        source_row.get(field_name),
                        field_name=field_name,
                        file_label=label,
                        row_number=row_number,
                    )
                    numeric_value_count += 1
                parsed_rows.append(row)

        if not parsed_rows:
            raise AuditError(f"{label}: CSV contains no data rows")

        entity_field = definition["entity_id"]
        entity_name_field = definition["entity_name"]
        entity_ids = {str(row[entity_field]) for row in parsed_rows}
        if len(entity_ids) != 1:
            raise AuditError(f"{label}: mixed {entity_field} values in one file")
        entity_id = next(iter(entity_ids))
        if entity_id in rows_by_entity:
            raise AuditError(f"duplicate {entity_field}: {entity_id}")

        names = {str(row[entity_name_field]) for row in parsed_rows}
        if len(names) != 1:
            raise AuditError(f"{label}: mixed {entity_name_field} values in one file")
        entity_name = next(iter(names))

        seeds = {int(row["seed"]) for row in parsed_rows}
        if len(seeds) != 1:
            raise AuditError(f"{label}: mixed Seed values in one file")
        file_seed = next(iter(seeds))
        if layer_seed is None:
            layer_seed = file_seed
        elif layer_seed != file_seed:
            raise AuditError(f"{layer_name}: inconsistent Seed values across files")

        if layer_name == "city_airport_market_demand":
            regions = {str(row["region_id"]) for row in parsed_rows}
            region_names = {str(row["region_name"]) for row in parsed_rows}
            if len(regions) != 1 or len(region_names) != 1:
                raise AuditError(f"{label}: city changes region identity across rows")

        indexes = [int(row["year_index"]) for row in parsed_rows]
        if len(indexes) != len(set(indexes)):
            raise AuditError(f"{label}: duplicate year_index")
        ordered = tuple(sorted(indexes))
        expected = tuple(range(ordered[0], ordered[-1] + 1))
        if ordered != expected:
            missing = sorted(set(expected) - set(ordered))
            raise AuditError(f"{label}: missing year_index values: {missing}")
        rows_sorted = sorted(parsed_rows, key=lambda row: int(row["year_index"]))
        year_by_index = {int(row["year_index"]): int(row["year"]) for row in rows_sorted}
        if len(set(year_by_index.values())) != len(year_by_index):
            raise AuditError(f"{label}: duplicate calendar year values")

        if common_year_indexes is None:
            common_year_indexes = ordered
            common_year_by_index = year_by_index
        elif common_year_indexes != ordered:
            raise AuditError(f"{layer_name}: year_index sets differ across entities")
        elif common_year_by_index != year_by_index:
            raise AuditError(f"{layer_name}: year/year_index mapping differs across entities")

        interface_values = {str(row[definition["interface"]]) for row in rows_sorted}
        param_values = {str(row[definition["param_version"]]) for row in rows_sorted}
        if len(interface_values) != 1:
            raise AuditError(f"{label}: interface version changes across rows")
        if len(param_values) != 1:
            raise AuditError(f"{label}: parameter version changes across rows")
        interfaces.update(interface_values)
        param_versions.update(param_values)

        rows_by_entity[entity_id] = rows_sorted
        entity_names[entity_id] = entity_name

    assert layer_seed is not None
    assert common_year_indexes is not None
    assert common_year_by_index is not None
    return LayerData(
        name=layer_name,
        files=files,
        rows_by_entity=dict(sorted(rows_by_entity.items())),
        entity_names=dict(sorted(entity_names.items())),
        interfaces=tuple(sorted(interfaces)),
        param_versions=tuple(sorted(param_versions)),
        seed=layer_seed,
        year_indexes=common_year_indexes,
        year_by_index=common_year_by_index,
        numeric_value_count=numeric_value_count,
        columns=tuple(sorted(common_columns or set())),
    )


def _load_manifest(input_root: Path) -> dict[str, Any] | None:
    path = input_root / "sample_manifest.json"
    if not path.exists():
        return None
    if not path.is_file():
        raise AuditError("sample_manifest.json is not a regular file")
    try:
        with path.open("r", encoding="utf-8") as handle:
            value = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise AuditError(f"invalid sample_manifest.json: {exc}") from exc
    if not isinstance(value, dict):
        raise AuditError("sample_manifest.json must contain a JSON object")
    return value


def _validate_manifest(manifest: Mapping[str, Any], layers: Mapping[str, LayerData]) -> None:
    seeds = {layer.seed for layer in layers.values()}
    seed = next(iter(seeds))
    demand = layers["regional_aviation_demand"]
    observed_start_year = min(demand.year_by_index.values())
    observed_index_min = demand.year_indexes[0]
    observed_index_max = demand.year_indexes[-1]

    checks = {
        "seed": seed,
        "start_year": observed_start_year,
        "expected_year_index_min": observed_index_min,
        "expected_year_index_max": observed_index_max,
        "years": observed_index_max - observed_index_min,
    }
    for key, observed in checks.items():
        if key in manifest and manifest[key] != observed:
            raise AuditError(
                f"sample_manifest.json mismatch for {key}: expected {observed}, got {manifest[key]}"
            )

    included = manifest.get("included_layers")
    if included is not None:
        if not isinstance(included, Mapping):
            raise AuditError("sample_manifest.json included_layers must be an object")
        for layer_name, layer in layers.items():
            declared = included.get(layer_name)
            if not isinstance(declared, Mapping):
                raise AuditError(
                    f"sample_manifest.json missing included_layers.{layer_name}"
                )
            expected_values = {"files": len(layer.files), "rows": layer.row_count}
            for key, observed in expected_values.items():
                if declared.get(key) != observed:
                    raise AuditError(
                        f"sample_manifest.json mismatch for {layer_name}.{key}: "
                        f"expected {observed}, got {declared.get(key)}"
                    )
            if layer_name == "city_airport_market_demand" and "region_scope" in declared:
                regions = {
                    str(rows[0]["region_id"])
                    for rows in layer.rows_by_entity.values()
                }
                if regions != {str(declared["region_scope"])}:
                    raise AuditError(
                        "sample_manifest.json city region_scope does not match CSV regions"
                    )


def _load_configs(config_root: Path) -> dict[str, Any]:
    if not config_root.is_dir():
        raise AuditError("config root does not exist or is not a directory")
    files = sorted(config_root.rglob("*.json"), key=lambda path: path.as_posix())
    if not files:
        raise AuditError("config root contains no JSON files")

    cities: dict[str, dict[str, Any]] = {}
    for path in files:
        label = _relative_label(path, config_root)
        try:
            with path.open("r", encoding="utf-8") as handle:
                document = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise AuditError(f"invalid config JSON {label}: {exc}") from exc
        if not isinstance(document, Mapping):
            raise AuditError(f"config {label} must contain an object")
        try:
            market = document["market"]
            demand_model = document["demand_model"]
            city_id = str(market["city_airport_market_id"])
            region_id = str(market["region_id"])
            baseline_potential = float(demand_model["baseline_city_potential_passengers_million"])
            baseline_share = float(demand_model["baseline_region_demand_share_pct"])
        except (KeyError, TypeError, ValueError) as exc:
            raise AuditError(f"config {label} lacks required city audit fields") from exc
        if not city_id or not region_id:
            raise AuditError(f"config {label} has empty city or region id")
        if not math.isfinite(baseline_potential) or not math.isfinite(baseline_share):
            raise AuditError(f"config {label} has non-finite baseline values")
        if city_id in cities:
            raise AuditError(f"duplicate configured city id: {city_id}")
        cities[city_id] = {
            "region_id": region_id,
            "baseline_city_potential_passengers_million": baseline_potential,
            "baseline_region_demand_share_pct": baseline_share,
        }
    return {"files": files, "cities": dict(sorted(cities.items()))}


def _entity_completeness(layer: LayerData, entity_key: str) -> dict[str, Any]:
    entities = []
    for entity_id, rows in layer.rows_by_entity.items():
        indexes = [int(row["year_index"]) for row in rows]
        entities.append(
            {
                entity_key: entity_id,
                "row_count": len(rows),
                "first_year_index": min(indexes),
                "last_year_index": max(indexes),
                "missing_year_indexes": [],
            }
        )
    return {
        "file_count": len(layer.files),
        "row_count": layer.row_count,
        "entities": entities,
    }


def _component_share_field(layer_name: str, component: str) -> str:
    if layer_name == "regional_aviation_demand":
        if component in {"business", "leisure", "vfr"}:
            return f"{component}_travel_share_pct"
        return f"{component}_share_pct"
    return f"{component}_passenger_share_pct"


def _direction_counts(values: Iterable[float]) -> dict[str, int]:
    increases = decreases = unchanged = 0
    for value in values:
        if value > DIRECTION_TOLERANCE_PP:
            increases += 1
        elif value < -DIRECTION_TOLERANCE_PP:
            decreases += 1
        else:
            unchanged += 1
    return {
        "increase_path_count": increases,
        "decrease_path_count": decreases,
        "approximately_unchanged_path_count": unchanged,
    }


def _summary_stats(values: Sequence[float], prefix: str = "delta") -> dict[str, Any]:
    if not values:
        return {
            f"{prefix}_min_pp": None,
            f"{prefix}_median_pp": None,
            f"{prefix}_max_pp": None,
        }
    return {
        f"{prefix}_min_pp": _clean_number(min(values)),
        f"{prefix}_median_pp": _clean_number(statistics.median(values)),
        f"{prefix}_max_pp": _clean_number(max(values)),
    }


def _regional_components(
    demand: LayerData, share_check: CheckAccumulator
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "classification_tolerance_pp": DIRECTION_TOLERANCE_PP,
    }
    for component in COMPONENTS:
        field_name = _component_share_field(demand.name, component)
        paths = []
        deltas = []
        for region_id, rows in demand.rows_by_entity.items():
            start = float(rows[0][field_name])
            end = float(rows[-1][field_name])
            delta = end - start
            deltas.append(delta)
            paths.append(
                {
                    "region_id": region_id,
                    "start_share_pct": _clean_number(start),
                    "end_share_pct": _clean_number(end),
                    "change_pp": _clean_number(delta),
                }
            )
        component_result = {
            "paths": paths,
            **_summary_stats(deltas),
            **_direction_counts(deltas),
        }
        result[component] = component_result

    max_deviation = 0.0
    max_location: dict[str, Any] | None = None
    for region_id, rows in demand.rows_by_entity.items():
        for row in rows:
            total = sum(
                float(row[_component_share_field(demand.name, component)])
                for component in COMPONENTS
            )
            error = total - 100.0
            location = {
                "region_id": region_id,
                "year": int(row["year"]),
                "year_index": int(row["year_index"]),
            }
            share_check.add(error, location, observed_sum_pct=total, expected_sum_pct=100.0)
            if abs(error) > max_deviation:
                max_deviation = abs(error)
                max_location = {**location, "observed_sum_pct": _clean_number(total)}
    result["annual_share_sum"] = {
        "sample_count": share_check.sample_count,
        "max_absolute_deviation_from_100_pct": _clean_number(max_deviation),
        "tolerance_pct": SHARE_TOLERANCE_PCT,
        "max_deviation_location": max_location,
    }
    return result


def _city_components(
    city: LayerData,
    share_check: CheckAccumulator,
    potential_check: CheckAccumulator,
    served_check: CheckAccumulator,
) -> dict[str, Any]:
    supports_internal_diagnostics = CITY_BOUNDARY_DIAGNOSTIC_FIELDS.issubset(
        set(city.columns)
    )
    result: dict[str, Any] = {
        "classification_tolerance_pp": DIRECTION_TOLERANCE_PP,
        "boundary_observation_scope": (
            "internal_raw_and_final"
            if supports_internal_diagnostics
            else "final_output_only"
        ),
    }
    boundary_summary: dict[str, Any] = {}

    for component in COMPONENTS:
        share_field = _component_share_field(city.name, component)
        index_field = f"{component}_city_demand_index"
        lower, upper = CITY_INDEX_BOUNDARIES[component]
        paths = []
        deltas = []
        lower_rows = 0
        upper_rows = 0
        boundary_cities: set[str] = set()
        true_floor_rows = 0
        true_cap_rows = 0
        true_boundary_cities: set[str] = set()
        raw_values: list[float] = []
        max_reported_streak = 0
        consistency_failure_count = 0
        consistency_failures: list[dict[str, Any]] = []

        for city_id, rows in city.rows_by_entity.items():
            start = float(rows[0][share_field])
            end = float(rows[-1][share_field])
            delta = end - start
            deltas.append(delta)
            paths.append(
                {
                    "city_airport_market_id": city_id,
                    "start_share_pct": _clean_number(start),
                    "end_share_pct": _clean_number(end),
                    "change_pp": _clean_number(delta),
                }
            )
            expected_streak = 0
            for row in rows:
                value = float(row[index_field])
                if value == lower:
                    lower_rows += 1
                    boundary_cities.add(city_id)
                if value == upper:
                    upper_rows += 1
                    boundary_cities.add(city_id)

                if not supports_internal_diagnostics:
                    continue

                raw = float(row[f"{component}_city_demand_raw_index"])
                state = str(row[f"{component}_city_demand_boundary_state"])
                floor_flag = int(row[f"{component}_city_demand_floor_applied"])
                cap_flag = int(row[f"{component}_city_demand_cap_applied"])
                reported_streak = int(
                    row[f"{component}_city_demand_consecutive_boundary_years"]
                )
                raw_values.append(raw)
                if state == "floor":
                    true_floor_rows += 1
                    true_boundary_cities.add(city_id)
                    expected_streak += 1
                    valid = floor_flag == 1 and cap_flag == 0 and value == lower and raw <= lower
                elif state == "cap":
                    true_cap_rows += 1
                    true_boundary_cities.add(city_id)
                    expected_streak += 1
                    valid = floor_flag == 0 and cap_flag == 1 and value == upper and raw >= upper
                elif state == "none":
                    expected_streak = 0
                    valid = (
                        floor_flag == 0
                        and cap_flag == 0
                        and reported_streak == 0
                        and lower <= raw <= upper
                        and value == raw
                    )
                else:
                    valid = False
                max_reported_streak = max(max_reported_streak, reported_streak)
                if reported_streak != expected_streak:
                    valid = False
                if not valid:
                    consistency_failure_count += 1
                if not valid and len(consistency_failures) < 5:
                    consistency_failures.append(
                        {
                            "city_airport_market_id": city_id,
                            "year_index": int(row["year_index"]),
                            "raw_index": _clean_number(raw),
                            "final_index": _clean_number(value),
                            "state": state,
                            "floor_applied": floor_flag,
                            "cap_applied": cap_flag,
                            "reported_streak": reported_streak,
                            "expected_streak": expected_streak,
                        }
                    )

        result[component] = {
            "paths": paths,
            **_summary_stats(deltas),
            **_direction_counts(deltas),
        }
        component_boundary: dict[str, Any] = {
            "known_final_index_lower_bound": lower,
            "known_final_index_upper_bound": upper,
            "exact_lower_boundary_row_count": lower_rows,
            "exact_upper_boundary_row_count": upper_rows,
            "observable_exact_boundary_row_count": lower_rows + upper_rows,
            "observable_exact_boundary_city_path_count": len(boundary_cities),
            "internal_diagnostics_status": (
                "supported" if supports_internal_diagnostics else "final_output_only"
            ),
        }
        if supports_internal_diagnostics:
            component_boundary.update(
                {
                    "true_floor_applied_row_count": true_floor_rows,
                    "true_cap_applied_row_count": true_cap_rows,
                    "true_boundary_row_count": true_floor_rows + true_cap_rows,
                    "true_boundary_city_path_count": len(true_boundary_cities),
                    "raw_index_min": _clean_number(min(raw_values)),
                    "raw_index_max": _clean_number(max(raw_values)),
                    "max_reported_consecutive_boundary_years": max_reported_streak,
                    "diagnostic_consistency_failure_count": consistency_failure_count,
                    "diagnostic_consistency_failure_examples": consistency_failures,
                }
            )
        boundary_summary[component] = component_boundary

    max_share_deviation = 0.0
    max_share_location: dict[str, Any] | None = None
    for city_id, rows in city.rows_by_entity.items():
        for row in rows:
            location = {
                "city_airport_market_id": city_id,
                "region_id": str(row["region_id"]),
                "year": int(row["year"]),
                "year_index": int(row["year_index"]),
            }
            share_total = sum(
                float(row[_component_share_field(city.name, component)])
                for component in COMPONENTS
            )
            share_error = share_total - 100.0
            share_check.add(
                share_error,
                location,
                observed_sum_pct=share_total,
                expected_sum_pct=100.0,
            )
            if abs(share_error) > max_share_deviation:
                max_share_deviation = abs(share_error)
                max_share_location = {
                    **location,
                    "observed_sum_pct": _clean_number(share_total),
                }

            potential_sum = sum(
                float(row[f"{component}_passengers_million"])
                for component in COMPONENTS
            )
            potential_total = float(row["city_potential_passengers_million"])
            potential_check.add(
                potential_sum - potential_total,
                location,
                component_sum_million=potential_sum,
                city_potential_million=potential_total,
            )

            served_sum = sum(
                float(row[f"{component}_served_passengers_million"])
                for component in COMPONENTS
            )
            served_total = float(row["city_served_passengers_million"])
            served_check.add(
                served_sum - served_total,
                location,
                component_sum_million=served_sum,
                city_served_million=served_total,
            )

    result["annual_share_sum"] = {
        "sample_count": share_check.sample_count,
        "max_absolute_deviation_from_100_pct": _clean_number(max_share_deviation),
        "tolerance_pct": SHARE_TOLERANCE_PCT,
        "max_deviation_location": max_share_location,
    }
    result["component_passenger_accounting"] = {
        "potential_component_sum_max_absolute_error_million": _clean_number(
            potential_check.max_abs_error
        ),
        "served_component_sum_max_absolute_error_million": _clean_number(
            served_check.max_abs_error
        ),
        "tolerance_million": PASSENGER_TOLERANCE_MILLION,
    }
    result["observable_exact_final_index_boundaries"] = boundary_summary
    return result


def _region_identity_checks(
    demand: LayerData, supply: LayerData, city: LayerData
) -> None:
    for region_id in sorted(set(demand.rows_by_entity) & set(supply.rows_by_entity)):
        if demand.entity_names[region_id] != supply.entity_names[region_id]:
            raise AuditError(f"region identity conflict across layers: {region_id}")

    regional_names = dict(demand.entity_names)
    regional_names.update(supply.entity_names)
    for city_id, rows in city.rows_by_entity.items():
        region_id = str(rows[0]["region_id"])
        region_name = str(rows[0]["region_name"])
        if region_id in regional_names and regional_names[region_id] != region_name:
            raise AuditError(
                f"region identity conflict between city {city_id} and regional layers"
            )


def _region_city_bridge(
    supply: LayerData,
    city: LayerData,
    configs: dict[str, Any] | None,
) -> dict[str, Any]:
    supply_by_region_year = {
        (region_id, int(row["year_index"])): float(row["potential_passengers_million"])
        for region_id, rows in supply.rows_by_entity.items()
        for row in rows
    }
    rows_by_region_year: dict[tuple[str, int], list[dict[str, Any]]] = {}
    for rows in city.rows_by_entity.values():
        for row in rows:
            key = (str(row["region_id"]), int(row["year_index"]))
            rows_by_region_year.setdefault(key, []).append(row)

    regions: dict[str, Any] = {}
    for region_id in sorted({key[0] for key in rows_by_region_year}):
        yearly = []
        for key in sorted(
            (key for key in rows_by_region_year if key[0] == region_id),
            key=lambda item: item[1],
        ):
            rows = rows_by_region_year[key]
            references = {
                round(float(row["source_region_reference_potential_passengers_million"]), 8)
                for row in rows
            }
            if len(references) != 1:
                raise AuditError(
                    f"city rows disagree on source regional potential for {region_id} year_index {key[1]}"
                )
            city_reference = next(iter(references))
            regional_reference = supply_by_region_year.get(key)
            if regional_reference is not None and abs(city_reference - regional_reference) > PASSENGER_TOLERANCE_MILLION:
                raise AuditError(
                    f"city/regional potential reference mismatch for {region_id} year_index {key[1]}"
                )
            reference = regional_reference if regional_reference is not None else city_reference
            city_total = sum(float(row["city_potential_passengers_million"]) for row in rows)
            baseline_share_sum = sum(float(row["baseline_region_demand_share_pct"]) for row in rows)
            ratio = None if reference == 0.0 else city_total / reference
            yearly.append(
                {
                    "year_index": key[1],
                    "year": int(rows[0]["year"]),
                    "city_path_count": len(rows),
                    "city_potential_total_million": _clean_number(city_total),
                    "region_reference_potential_million": _clean_number(reference),
                    "city_to_region_reference_ratio": None if ratio is None else _clean_number(ratio),
                    "baseline_region_demand_share_pct_sum": _clean_number(baseline_share_sum),
                }
            )
        first = yearly[0]
        last = yearly[-1]
        regions[region_id] = {
            "yearly": yearly,
            "first_year": first,
            "last_year": last,
            "ratio_change": None
            if first["city_to_region_reference_ratio"] is None
            or last["city_to_region_reference_ratio"] is None
            else _clean_number(
                float(last["city_to_region_reference_ratio"])
                - float(first["city_to_region_reference_ratio"])
            ),
        }

    config_summary: dict[str, Any]
    if configs is None:
        config_summary = {"status": "unsupported", "reason": "config_root_not_provided"}
    else:
        grouped: dict[str, dict[str, Any]] = {}
        for city_id, item in configs["cities"].items():
            region = grouped.setdefault(
                item["region_id"],
                {
                    "configured_city_count": 0,
                    "baseline_city_potential_total_million": 0.0,
                    "baseline_region_demand_share_pct_sum": 0.0,
                    "city_ids": [],
                },
            )
            region["configured_city_count"] += 1
            region["baseline_city_potential_total_million"] += float(
                item["baseline_city_potential_passengers_million"]
            )
            region["baseline_region_demand_share_pct_sum"] += float(
                item["baseline_region_demand_share_pct"]
            )
            region["city_ids"].append(city_id)
        for value in grouped.values():
            value["baseline_city_potential_total_million"] = _clean_number(
                value["baseline_city_potential_total_million"]
            )
            value["baseline_region_demand_share_pct_sum"] = _clean_number(
                value["baseline_region_demand_share_pct_sum"]
            )
            value["city_ids"].sort()
        config_summary = {"status": "supported", "regions": dict(sorted(grouped.items()))}

    return {"regions": regions, "configuration_baseline": config_summary}


def _longest_streak(indexes: Iterable[int]) -> int:
    ordered = sorted(set(indexes))
    longest = current = 0
    previous: int | None = None
    for value in ordered:
        if previous is not None and value == previous + 1:
            current += 1
        else:
            current = 1
        longest = max(longest, current)
        previous = value
    return longest


def _percentile(values: Sequence[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(float(value) for value in values)
    position = (len(ordered) - 1) * min(1.0, max(0.0, fraction))
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def _city_airline_integration(city: LayerData) -> dict[str, Any]:
    if not CITY_G4_SUPPLY_FIELDS.issubset(set(city.columns)):
        return {
            "status": "unsupported",
            "reason": "G4 airline supply/component fields are absent from this city CSV interface",
            "missing_fields": sorted(CITY_G4_SUPPLY_FIELDS - set(city.columns)),
        }

    offered_identity = CheckAccumulator(
        "city_airline_offered_equals_serviceable_plus_unused",
        "million_passengers",
        PASSENGER_TOLERANCE_MILLION,
    )
    component_offered_identity = CheckAccumulator(
        "component_offered_sum_equals_city_airline_offered",
        "million_passengers",
        PASSENGER_TOLERANCE_MILLION,
    )
    component_supply_identity = CheckAccumulator(
        "component_serviceable_sum_equals_city_airline_serviceable",
        "million_passengers",
        PASSENGER_TOLERANCE_MILLION,
    )
    component_gap_identity = CheckAccumulator(
        "component_gap_equals_potential_minus_serviceable",
        "million_passengers",
        PASSENGER_TOLERANCE_MILLION,
    )
    component_served_identity = CheckAccumulator(
        "component_served_sum_equals_city_served",
        "million_passengers",
        PASSENGER_TOLERANCE_MILLION,
    )
    component_supply_cap = CheckAccumulator(
        "component_serviceable_not_above_potential",
        "million_passengers",
        BOUNDARY_TOLERANCE_MILLION,
    )
    component_served_cap = CheckAccumulator(
        "component_served_not_above_serviceable",
        "million_passengers",
        BOUNDARY_TOLERANCE_MILLION,
    )
    unused_nonnegative = CheckAccumulator(
        "city_airline_unused_capacity_nonnegative",
        "million_passengers",
        BOUNDARY_TOLERANCE_MILLION,
    )
    component_gap_nonnegative = CheckAccumulator(
        "component_supply_gap_nonnegative",
        "million_passengers",
        BOUNDARY_TOLERANCE_MILLION,
    )

    terminal_fulfillment: list[float] = []
    city_paths: list[dict[str, Any]] = []
    profile_paths: dict[str, list[dict[str, Any]]] = {}
    component_totals = {
        component: {
            "potential": 0.0,
            "offered": 0.0,
            "serviceable": 0.0,
            "served": 0.0,
            "gap": 0.0,
            "shortage_rows": 0,
            "idle_rows": 0,
            "max_shortage_streak": 0,
            "max_idle_streak": 0,
        }
        for component in COMPONENTS
    }

    for city_id, source_rows in sorted(city.rows_by_entity.items()):
        rows = sorted(source_rows, key=lambda row: int(row["year_index"]))
        last = rows[-1]
        fulfillment = [float(row["city_airline_supply_fulfillment_pct"]) for row in rows]
        exact_airline_indexes = [
            int(row["year_index"])
            for row in rows
            if "airline" in str(row["city_binding_bottleneck"])
        ]
        below_95_indexes = [
            int(row["year_index"])
            for row in rows
            if float(row["city_airline_supply_fulfillment_pct"]) < 95.0
        ]
        below_90_indexes = [
            int(row["year_index"])
            for row in rows
            if float(row["city_airline_supply_fulfillment_pct"]) < 90.0
        ]
        unused_indexes = [
            int(row["year_index"])
            for row in rows
            if float(row["city_airline_unused_capacity_million"]) > PASSENGER_TOLERANCE_MILLION
        ]
        item = {
            "city_airport_market_id": city_id,
            "airline_supply_dynamics_profile_id": str(last["airline_supply_dynamics_profile_id"]),
            "airline_supply_dynamics_modifier_ids": str(last["airline_supply_dynamics_modifier_ids"]),
            "airline_component_allocation_profile_id": str(last["airline_component_allocation_profile_id"]),
            "terminal_fulfillment_pct": _clean_number(fulfillment[-1]),
            "all_year_mean_fulfillment_pct": _clean_number(statistics.fmean(fulfillment)),
            "years_below_95_pct": len(below_95_indexes),
            "years_below_90_pct": len(below_90_indexes),
            "longest_exact_airline_bottleneck_years": _longest_streak(exact_airline_indexes),
            "longest_below_95_pct_years": _longest_streak(below_95_indexes),
            "longest_below_90_pct_years": _longest_streak(below_90_indexes),
            "unused_supply_years": len(unused_indexes),
            "longest_unused_supply_years": _longest_streak(unused_indexes),
            "mean_unused_supply_million": _clean_number(
                statistics.fmean(float(row["city_airline_unused_capacity_million"]) for row in rows)
            ),
        }
        terminal_fulfillment.append(fulfillment[-1])
        city_paths.append(item)
        profile_paths.setdefault(item["airline_supply_dynamics_profile_id"], []).append(item)

        for row in rows:
            location = {
                "city_airport_market_id": city_id,
                "year": int(row["year"]),
                "year_index": int(row["year_index"]),
            }
            offered = float(row["city_airline_offered_capacity_million"])
            serviceable = float(row["city_airline_serviceable_supply_million"])
            unused = float(row["city_airline_unused_capacity_million"])
            offered_identity.add(
                offered - serviceable - unused,
                location,
                offered_million=offered,
                serviceable_million=serviceable,
                unused_million=unused,
            )
            unused_nonnegative.add(max(0.0, -unused), location, unused_million=unused)

            component_offered = 0.0
            component_supply = 0.0
            component_served = 0.0
            for component in COMPONENTS:
                potential = float(row[f"{component}_passengers_million"])
                offered_component = float(row[f"{component}_airline_offered_capacity_million"])
                supply_component = float(row[f"{component}_airline_supply_passengers_million"])
                served_component = float(row[f"{component}_served_passengers_million"])
                gap = float(row[f"{component}_airline_supply_gap_million"])
                component_offered += offered_component
                component_supply += supply_component
                component_served += served_component
                component_gap_identity.add(
                    gap - (potential - supply_component),
                    {**location, "component": component},
                    potential_million=potential,
                    serviceable_million=supply_component,
                    gap_million=gap,
                )
                component_supply_cap.add(
                    max(0.0, supply_component - potential),
                    {**location, "component": component},
                    potential_million=potential,
                    serviceable_million=supply_component,
                )
                component_served_cap.add(
                    max(0.0, served_component - supply_component),
                    {**location, "component": component},
                    serviceable_million=supply_component,
                    served_million=served_component,
                )
                component_gap_nonnegative.add(
                    max(0.0, -gap),
                    {**location, "component": component},
                    gap_million=gap,
                )
                totals = component_totals[component]
                totals["potential"] += potential
                totals["offered"] += offered_component
                totals["serviceable"] += supply_component
                totals["served"] += served_component
                totals["gap"] += gap
            component_offered_identity.add(
                component_offered - offered,
                location,
                component_sum_million=component_offered,
                city_offered_million=offered,
            )
            component_supply_identity.add(
                component_supply - serviceable,
                location,
                component_sum_million=component_supply,
                city_serviceable_million=serviceable,
            )
            component_served_identity.add(
                component_served - float(row["city_served_passengers_million"]),
                location,
                component_sum_million=component_served,
                city_served_million=float(row["city_served_passengers_million"]),
            )

        for component in COMPONENTS:
            shortage_indexes = [
                int(row["year_index"])
                for row in rows
                if float(row[f"{component}_airline_supply_gap_million"])
                > PASSENGER_TOLERANCE_MILLION
            ]
            idle_indexes = [
                int(row["year_index"])
                for row in rows
                if float(row[f"{component}_airline_offered_capacity_million"])
                - float(row[f"{component}_airline_supply_passengers_million"])
                > PASSENGER_TOLERANCE_MILLION
            ]
            component_totals[component]["shortage_rows"] += len(shortage_indexes)
            component_totals[component]["idle_rows"] += len(idle_indexes)
            component_totals[component]["max_shortage_streak"] = max(
                component_totals[component]["max_shortage_streak"],
                _longest_streak(shortage_indexes),
            )
            component_totals[component]["max_idle_streak"] = max(
                component_totals[component]["max_idle_streak"],
                _longest_streak(idle_indexes),
            )

    total_potential = sum(value["potential"] for value in component_totals.values())
    total_serviceable = sum(value["serviceable"] for value in component_totals.values())
    component_summary = {}
    for component, totals in component_totals.items():
        demand_share = totals["potential"] / total_potential * 100.0 if total_potential else 0.0
        supply_share = totals["serviceable"] / total_serviceable * 100.0 if total_serviceable else 0.0
        component_summary[component] = {
            **{key: _clean_number(value) for key, value in totals.items()},
            "aggregate_fulfillment_pct": _clean_number(
                totals["serviceable"] / totals["potential"] * 100.0
                if totals["potential"]
                else 100.0
            ),
            "aggregate_potential_share_pct": _clean_number(demand_share),
            "aggregate_serviceable_share_pct": _clean_number(supply_share),
            "serviceable_minus_potential_share_pp": _clean_number(supply_share - demand_share),
        }

    checks = [
        offered_identity.as_dict(),
        component_offered_identity.as_dict(),
        component_supply_identity.as_dict(),
        component_gap_identity.as_dict(),
        component_served_identity.as_dict(),
        component_supply_cap.as_dict(),
        component_served_cap.as_dict(),
        unused_nonnegative.as_dict(),
        component_gap_nonnegative.as_dict(),
    ]
    checks.sort(key=lambda item: str(item["check_name"]))

    return {
        "status": "supported",
        "city_path_count": len(city_paths),
        "row_count": city.row_count,
        "terminal_fulfillment_distribution_pct": {
            "minimum": _clean_number(min(terminal_fulfillment)),
            "p25": _clean_number(_percentile(terminal_fulfillment, 0.25)),
            "median": _clean_number(statistics.median(terminal_fulfillment)),
            "p75": _clean_number(_percentile(terminal_fulfillment, 0.75)),
            "maximum": _clean_number(max(terminal_fulfillment)),
            "city_count_below_90_pct": sum(value < 90.0 for value in terminal_fulfillment),
            "city_count_below_95_pct": sum(value < 95.0 for value in terminal_fulfillment),
        },
        "maximum_city_streaks": {
            "exact_airline_bottleneck_years": max(
                item["longest_exact_airline_bottleneck_years"] for item in city_paths
            ),
            "below_95_pct_years": max(item["longest_below_95_pct_years"] for item in city_paths),
            "below_90_pct_years": max(item["longest_below_90_pct_years"] for item in city_paths),
            "unused_supply_years": max(item["longest_unused_supply_years"] for item in city_paths),
        },
        "profiles": {
            profile_id: {
                "city_path_count": len(items),
                "terminal_mean_fulfillment_pct": _clean_number(
                    statistics.fmean(item["terminal_fulfillment_pct"] for item in items)
                ),
                "terminal_median_fulfillment_pct": _clean_number(
                    statistics.median(item["terminal_fulfillment_pct"] for item in items)
                ),
                "mean_longest_below_95_pct_years": _clean_number(
                    statistics.fmean(item["longest_below_95_pct_years"] for item in items)
                ),
                "mean_unused_supply_million": _clean_number(
                    statistics.fmean(item["mean_unused_supply_million"] for item in items)
                ),
            }
            for profile_id, items in sorted(profile_paths.items())
        },
        "components": component_summary,
        "city_paths": city_paths,
        "accounting_checks": checks,
        "all_accounting_checks_passed": all(check["failure_count"] == 0 for check in checks),
    }


def _supply_and_capacity(
    supply: LayerData,
    city: LayerData,
    regional_unmet_check: CheckAccumulator,
    city_unmet_check: CheckAccumulator,
) -> dict[str, Any]:
    city_airline_integration = _city_airline_integration(city)
    regional_served_boundary = CheckAccumulator(
        "regional_reference_served_not_above_potential",
        "million_passengers",
        BOUNDARY_TOLERANCE_MILLION,
    )
    city_served_potential_boundary = CheckAccumulator(
        "city_served_not_above_potential",
        "million_passengers",
        BOUNDARY_TOLERANCE_MILLION,
    )
    city_served_capacity_boundary = CheckAccumulator(
        "city_served_not_above_effective_capacity",
        "million_passengers",
        BOUNDARY_TOLERANCE_MILLION,
    )
    city_served_supply_boundary = CheckAccumulator(
        "city_served_not_above_airline_serviceable_supply",
        "million_passengers",
        BOUNDARY_TOLERANCE_MILLION,
    )

    for region_id, rows in supply.rows_by_entity.items():
        for row in rows:
            location = {
                "region_id": region_id,
                "year": int(row["year"]),
                "year_index": int(row["year_index"]),
            }
            potential = float(row["potential_passengers_million"])
            served = float(row["reference_served_passengers_million"])
            unmet = float(row["reference_unmet_passengers_million"])
            regional_served_boundary.add(
                max(0.0, served - potential),
                location,
                potential_million=potential,
                served_million=served,
            )
            regional_unmet_check.add(
                unmet - (potential - served),
                location,
                potential_million=potential,
                served_million=served,
                unmet_million=unmet,
            )

    bottleneck_rows: dict[str, int] = {}
    bottleneck_cities: dict[str, set[str]] = {}
    airport_indexes_by_city: dict[str, list[int]] = {}
    airport_first_by_city: dict[str, int] = {}

    for city_id, rows in city.rows_by_entity.items():
        for row in rows:
            location = {
                "city_airport_market_id": city_id,
                "region_id": str(row["region_id"]),
                "year": int(row["year"]),
                "year_index": int(row["year_index"]),
            }
            bottleneck = str(row["city_binding_bottleneck"])
            bottleneck_rows[bottleneck] = bottleneck_rows.get(bottleneck, 0) + 1
            bottleneck_cities.setdefault(bottleneck, set()).add(city_id)
            if bottleneck == "airport_bottleneck":
                airport_indexes_by_city.setdefault(city_id, []).append(int(row["year_index"]))
                airport_first_by_city.setdefault(city_id, int(row["year"]))

            potential = float(row["city_potential_passengers_million"])
            capacity = float(row["city_effective_capacity_million"])
            serviceable_supply = float(row["city_airline_serviceable_supply_million"])
            served = float(row["city_served_passengers_million"])
            unmet = float(row["city_unmet_passengers_million"])
            city_served_potential_boundary.add(
                max(0.0, served - potential), location, served_million=served, potential_million=potential
            )
            city_served_capacity_boundary.add(
                max(0.0, served - capacity), location, served_million=served, capacity_million=capacity
            )
            city_served_supply_boundary.add(
                max(0.0, served - serviceable_supply),
                location,
                served_million=served,
                serviceable_supply_million=serviceable_supply,
            )
            city_unmet_check.add(
                unmet - (potential - served),
                location,
                potential_million=potential,
                served_million=served,
                unmet_million=unmet,
            )

    bottleneck_types = {
        key: {
            "row_count": bottleneck_rows[key],
            "city_path_count": len(bottleneck_cities[key]),
        }
        for key in sorted(bottleneck_rows)
    }
    airport_rows = bottleneck_rows.get("airport_bottleneck", 0)
    airport_city_count = len(airport_indexes_by_city)
    airport_first_year = min(airport_first_by_city.values()) if airport_first_by_city else None
    longest = max((_longest_streak(values) for values in airport_indexes_by_city.values()), default=0)

    return {
        "city_airline_integration": city_airline_integration,
        "city_binding_bottleneck": {
            "types": bottleneck_types,
            "airport_bottleneck": {
                "row_count": airport_rows,
                "city_path_count": airport_city_count,
                "first_year": airport_first_year,
                "longest_consecutive_years": longest,
                "first_year_by_city": [
                    {
                        "city_airport_market_id": city_id,
                        "first_year": airport_first_by_city[city_id],
                    }
                    for city_id in sorted(airport_first_by_city)
                ],
            },
        },
        "regional_boundaries": {
            "served_not_above_potential": regional_served_boundary.as_dict(),
            "unmet_arithmetic": regional_unmet_check.as_dict(),
        },
        "city_boundaries": {
            "served_not_above_potential": city_served_potential_boundary.as_dict(),
            "served_not_above_effective_capacity": city_served_capacity_boundary.as_dict(),
            "served_not_above_airline_serviceable_supply": city_served_supply_boundary.as_dict(),
            "unmet_arithmetic": city_unmet_check.as_dict(),
        },
    }


def _build_completeness(
    demand: LayerData,
    supply: LayerData,
    city: LayerData,
    configs: dict[str, Any] | None,
) -> dict[str, Any]:
    demand_regions = set(demand.rows_by_entity)
    supply_regions = set(supply.rows_by_entity)
    output_cities = set(city.rows_by_entity)
    result: dict[str, Any] = {
        "regional_aviation_demand": _entity_completeness(demand, "region_id"),
        "regional_air_capacity_supply": _entity_completeness(supply, "region_id"),
        "city_airport_market_demand": _entity_completeness(city, "city_airport_market_id"),
        "regional_layer_set_differences": {
            "demand_only_region_ids": sorted(demand_regions - supply_regions),
            "supply_only_region_ids": sorted(supply_regions - demand_regions),
        },
    }
    if configs is None:
        result["configuration_coverage"] = {
            "status": "unsupported",
            "missing_output_city_ids": None,
            "unexpected_output_city_ids": None,
        }
    else:
        configured = set(configs["cities"])
        result["configuration_coverage"] = {
            "status": "checked",
            "configured_city_count": len(configured),
            "output_city_count": len(output_cities),
            "missing_output_city_ids": sorted(configured - output_cities),
            "unexpected_output_city_ids": sorted(output_cities - configured),
        }
    result["complete"] = (
        not result["regional_layer_set_differences"]["demand_only_region_ids"]
        and not result["regional_layer_set_differences"]["supply_only_region_ids"]
        and (
            configs is None
            or (
                not result["configuration_coverage"]["missing_output_city_ids"]
                and not result["configuration_coverage"]["unexpected_output_city_ids"]
            )
        )
    )
    return result


def _input_identity(
    input_root: Path,
    layers: Mapping[str, LayerData],
    manifest: Mapping[str, Any] | None,
) -> dict[str, Any]:
    demand = layers["regional_aviation_demand"]
    return {
        "input_root_display_name": _stable_display_name(input_root),
        "seed": demand.seed,
        "min_year_index": demand.year_indexes[0],
        "max_year_index": demand.year_indexes[-1],
        "min_year": min(demand.year_by_index.values()),
        "max_year": max(demand.year_by_index.values()),
        "regional_aviation_demand_interface_versions": list(demand.interfaces),
        "regional_air_capacity_supply_interface_versions": list(
            layers["regional_air_capacity_supply"].interfaces
        ),
        "city_airport_market_demand_interface_versions": list(
            layers["city_airport_market_demand"].interfaces
        ),
        "parameter_versions": {
            name: list(layer.param_versions) for name, layer in sorted(layers.items())
        },
        "files": {name: len(layer.files) for name, layer in sorted(layers.items())},
        "rows": {name: layer.row_count for name, layer in sorted(layers.items())},
        "manifest": None
        if manifest is None
        else {
            key: manifest[key]
            for key in (
                "schema_version",
                "source_run_id",
                "variant",
                "model_version",
                "output_schema_version",
                "orchestrator_version",
                "artifact_profile",
            )
            if key in manifest
        },
    }


def audit_passenger_demand(
    input_root: Path, *, config_root: Path | None = None
) -> dict[str, object]:
    """Audit a passenger-demand output excerpt without changing any model data."""

    input_root = Path(input_root)
    if not input_root.is_dir():
        raise AuditError("input root does not exist or is not a directory")

    layers = {
        name: _read_layer(input_root, name)
        for name in (
            "regional_aviation_demand",
            "regional_air_capacity_supply",
            "city_airport_market_demand",
        )
    }
    seeds = {layer.seed for layer in layers.values()}
    if len(seeds) != 1:
        raise AuditError("Seed differs across required layers")
    year_sets = {layer.year_indexes for layer in layers.values()}
    if len(year_sets) != 1:
        raise AuditError("year_index sets differ across required layers")
    year_maps = {tuple(sorted(layer.year_by_index.items())) for layer in layers.values()}
    if len(year_maps) != 1:
        raise AuditError("year/year_index mapping differs across required layers")

    demand = layers["regional_aviation_demand"]
    supply = layers["regional_air_capacity_supply"]
    city = layers["city_airport_market_demand"]
    _region_identity_checks(demand, supply, city)

    manifest = _load_manifest(input_root)
    if manifest is not None:
        _validate_manifest(manifest, layers)
    configs = _load_configs(Path(config_root)) if config_root is not None else None

    warnings = []
    if manifest is None:
        warnings.append(
            _warning(
                "sample_manifest_missing",
                "sample_manifest.json was not provided; manifest-level completeness checks are unavailable.",
            )
        )
    if configs is None:
        warnings.append(
            _warning(
                "config_root_not_provided",
                "Configuration coverage and configured baseline bridge totals are unavailable.",
            )
        )
    if not CITY_BOUNDARY_DIAGNOSTIC_FIELDS.issubset(set(city.columns)):
        warnings.append(
            _warning(
                "city_component_internal_clamp_unobservable",
                "City CSVs expose final component indices only; raw targets, clamp flags, directions, and streaks are unobservable.",
            )
        )

    regional_share = CheckAccumulator(
        "regional_component_share_sum_equals_100_pct",
        "percentage_points",
        SHARE_TOLERANCE_PCT,
    )
    city_share = CheckAccumulator(
        "city_component_share_sum_equals_100_pct",
        "percentage_points",
        SHARE_TOLERANCE_PCT,
    )
    city_potential = CheckAccumulator(
        "city_component_potential_passengers_sum_equals_city_potential",
        "million_passengers",
        PASSENGER_TOLERANCE_MILLION,
    )
    city_served = CheckAccumulator(
        "city_component_served_passengers_sum_equals_city_served",
        "million_passengers",
        PASSENGER_TOLERANCE_MILLION,
    )
    regional_unmet = CheckAccumulator(
        "regional_reference_unmet_equals_potential_minus_served",
        "million_passengers",
        PASSENGER_TOLERANCE_MILLION,
    )
    city_unmet = CheckAccumulator(
        "city_unmet_equals_potential_minus_served",
        "million_passengers",
        PASSENGER_TOLERANCE_MILLION,
    )

    regional_components = _regional_components(demand, regional_share)
    city_components = _city_components(city, city_share, city_potential, city_served)
    bridge = _region_city_bridge(supply, city, configs)
    supply_capacity = _supply_and_capacity(
        supply, city, regional_unmet, city_unmet
    )
    completeness = _build_completeness(demand, supply, city, configs)

    if configs is not None:
        coverage = completeness["configuration_coverage"]
        if coverage["missing_output_city_ids"] or coverage["unexpected_output_city_ids"]:
            warnings.append(
                _warning(
                    "config_output_city_set_mismatch",
                    "Configured and observed city id sets differ.",
                    missing_output_city_ids=coverage["missing_output_city_ids"],
                    unexpected_output_city_ids=coverage["unexpected_output_city_ids"],
                )
            )
    differences = completeness["regional_layer_set_differences"]
    if differences["demand_only_region_ids"] or differences["supply_only_region_ids"]:
        warnings.append(
            _warning(
                "regional_layer_set_mismatch",
                "Regional demand and supply region sets differ.",
                **differences,
            )
        )

    warnings.sort(
        key=lambda item: (
            str(item["code"]),
            str(item["message"]),
            json.dumps(item.get("context", {}), ensure_ascii=False, sort_keys=True),
        )
    )

    accounting_checks = [
        regional_share.as_dict(),
        city_share.as_dict(),
        city_potential.as_dict(),
        city_served.as_dict(),
        regional_unmet.as_dict(),
        city_unmet.as_dict(),
    ]
    accounting_checks.sort(key=lambda item: str(item["check_name"]))

    return {
        "audit_schema_version": AUDIT_SCHEMA_VERSION,
        "input_identity": _input_identity(input_root, layers, manifest),
        "completeness": completeness,
        "numeric_validity": {
            "status": "valid",
            "all_required_numeric_values_finite": True,
            "required_numeric_value_count": sum(
                layer.numeric_value_count for layer in layers.values()
            ),
            "by_layer": {
                name: {
                    "required_numeric_value_count": layer.numeric_value_count,
                    "all_finite": True,
                }
                for name, layer in sorted(layers.items())
            },
        },
        "regional_components": regional_components,
        "city_components": city_components,
        "region_city_bridge": bridge,
        "supply_and_capacity": supply_capacity,
        "accounting_invariants": {
            "tolerances": {
                "share_sum_percentage_points": SHARE_TOLERANCE_PCT,
                "passenger_accounting_million": PASSENGER_TOLERANCE_MILLION,
                "boundary_violation_million": BOUNDARY_TOLERANCE_MILLION,
                "rounding_basis": "CSV values are rounded to four decimal places; 0.001 million/percentage-point tolerances cover accumulated rounding without masking million-passenger errors.",
            },
            "checks": accounting_checks,
            "all_passed": all(check["failure_count"] == 0 for check in accounting_checks),
        },
        "diagnostic_capabilities": {
            "city_component_raw_target": {
                "status": (
                    "supported"
                    if CITY_BOUNDARY_DIAGNOSTIC_FIELDS.issubset(
                        set(layers["city_airport_market_demand"].columns)
                    )
                    else "unobservable"
                ),
                "scope": city_components["boundary_observation_scope"],
                "reason": (
                    "real pre-boundary target fields are present"
                    if CITY_BOUNDARY_DIAGNOSTIC_FIELDS.issubset(
                        set(layers["city_airport_market_demand"].columns)
                    )
                    else "raw target fields are absent from this legacy city CSV interface"
                ),
            },
            "city_component_internal_clamp_flag": {
                "status": (
                    "supported"
                    if CITY_BOUNDARY_DIAGNOSTIC_FIELDS.issubset(
                        set(layers["city_airport_market_demand"].columns)
                    )
                    else "unobservable"
                ),
                "scope": city_components["boundary_observation_scope"],
                "reason": (
                    "state, direction flags, and consecutive streak fields are present"
                    if CITY_BOUNDARY_DIAGNOSTIC_FIELDS.issubset(
                        set(layers["city_airport_market_demand"].columns)
                    )
                    else "clamp flag/direction/streak fields are absent from this legacy city CSV interface"
                ),
            },
            "city_component_exact_boundary_observation": {
                "status": "supported",
                "scope": city_components["boundary_observation_scope"],
                "interpretation": (
                    "Final exact-boundary counts are retained alongside true internal diagnostics."
                    if city_components["boundary_observation_scope"] == "internal_raw_and_final"
                    else "Counts only final indices exactly equal to known bounds; zero does not prove that an internal raw target was never clamped."
                ),
            },
            "sample_manifest_validation": {
                "status": "supported" if manifest is not None else "unsupported",
            },
            "configuration_coverage": {
                "status": "supported" if configs is not None else "unsupported",
            },
            "parameter_effect_comparison": {
                "status": "supported",
                "interface": "compare_passenger_audits",
            },
        },
        "warnings": warnings,
    }


def _resolve_metric_path(document: Mapping[str, Any], path: str) -> float:
    if not isinstance(path, str) or not path:
        raise AuditError("comparison metric path must be a non-empty string")
    current: Any = document
    for segment in path.split("."):
        if isinstance(current, Mapping):
            if segment not in current:
                raise AuditError(f"comparison metric path is missing: {path}")
            current = current[segment]
        elif isinstance(current, Sequence) and not isinstance(current, (str, bytes, bytearray)):
            try:
                index = int(segment)
                current = current[index]
            except (ValueError, IndexError) as exc:
                raise AuditError(f"comparison metric path is missing: {path}") from exc
        else:
            raise AuditError(f"comparison metric path is missing: {path}")
    if isinstance(current, bool) or not isinstance(current, (int, float)):
        raise AuditError(f"comparison metric is not numeric: {path}")
    value = float(current)
    if not math.isfinite(value):
        raise AuditError(f"comparison metric is non-finite: {path}")
    return value


def _normalize_metric_specs(
    contract: Mapping[str, Any], keys: tuple[str, ...], *, non_target: bool = False
) -> list[dict[str, Any]]:
    raw: Any = None
    for key in keys:
        if key in contract:
            raw = contract[key]
            break
    if raw is None:
        return []
    specs: list[dict[str, Any]] = []
    if isinstance(raw, Mapping):
        for path, spec in sorted(raw.items()):
            if isinstance(spec, str):
                specs.append({"path": path, "expected_direction": spec})
            elif isinstance(spec, Mapping):
                specs.append({"path": path, **dict(spec)})
            else:
                raise AuditError("comparison metric spec must be a string or object")
    elif isinstance(raw, Sequence) and not isinstance(raw, (str, bytes, bytearray)):
        for item in raw:
            if not isinstance(item, Mapping):
                raise AuditError("comparison metric list entries must be objects")
            specs.append(dict(item))
    else:
        raise AuditError("comparison metric collection must be a list or object")

    for spec in specs:
        if "path" not in spec:
            raise AuditError("comparison metric spec is missing path")
        if non_target and "expected_direction" not in spec:
            spec["expected_direction"] = "unchanged"
    return sorted(specs, key=lambda item: str(item["path"]))


def _threshold(spec: Mapping[str, Any], *names: str, default: float = 0.0) -> float:
    for name in names:
        if name in spec:
            try:
                value = float(spec[name])
            except (TypeError, ValueError) as exc:
                raise AuditError(f"comparison threshold {name} must be numeric") from exc
            if not math.isfinite(value) or value < 0:
                raise AuditError(f"comparison threshold {name} must be finite and non-negative")
            return value
    return default


def _compare_metric(
    baseline: Mapping[str, Any], candidate: Mapping[str, Any], spec: Mapping[str, Any], *, non_target: bool
) -> dict[str, Any]:
    path = str(spec["path"])
    baseline_value = _resolve_metric_path(baseline, path)
    candidate_value = _resolve_metric_path(candidate, path)
    delta = candidate_value - baseline_value
    relative_change = None if baseline_value == 0.0 else delta / abs(baseline_value)
    direction = str(spec.get("expected_direction", "unchanged"))
    if direction not in {"increase", "decrease", "change", "unchanged"}:
        raise AuditError(f"unsupported expected_direction for {path}: {direction}")

    if non_target or direction == "unchanged":
        maximum_absolute = _threshold(
            spec,
            "maximum_absolute_change",
            "max_absolute_change",
            "allowed_absolute_drift",
            "max_absolute_drift",
            default=0.0,
        )
        maximum_relative = _threshold(
            spec,
            "maximum_relative_change",
            "max_relative_change",
            "allowed_relative_drift",
            "max_relative_drift",
            default=math.inf,
        )
        absolute_pass = abs(delta) <= maximum_absolute
        if relative_change is None:
            relative_pass = math.isinf(maximum_relative) or delta == 0.0
        else:
            relative_pass = abs(relative_change) <= maximum_relative
        passed = absolute_pass and relative_pass
        thresholds = {
            "maximum_absolute_change": maximum_absolute,
            "maximum_relative_change": None if math.isinf(maximum_relative) else maximum_relative,
        }
    else:
        minimum_absolute = _threshold(
            spec,
            "minimum_absolute_change",
            "min_absolute_change",
            default=0.0,
        )
        minimum_relative = _threshold(
            spec,
            "minimum_relative_change",
            "min_relative_change",
            default=0.0,
        )
        if minimum_relative > 0.0 and relative_change is None:
            raise AuditError(
                f"relative change threshold cannot be evaluated from zero baseline: {path}"
            )
        magnitude_pass = abs(delta) >= minimum_absolute and (
            minimum_relative == 0.0
            or (relative_change is not None and abs(relative_change) >= minimum_relative)
        )
        direction_pass = (
            delta > 0.0
            if direction == "increase"
            else delta < 0.0
            if direction == "decrease"
            else delta != 0.0
        )
        passed = direction_pass and magnitude_pass
        thresholds = {
            "minimum_absolute_change": minimum_absolute,
            "minimum_relative_change": minimum_relative,
        }

    return {
        "path": path,
        "expected_direction": direction,
        "baseline_value": _clean_number(baseline_value),
        "candidate_value": _clean_number(candidate_value),
        "absolute_change": _clean_number(delta),
        "relative_change": None if relative_change is None else _clean_number(relative_change),
        "thresholds": thresholds,
        "passed": passed,
    }


def compare_passenger_audits(
    baseline: dict[str, object],
    candidate: dict[str, object],
    comparison_contract: dict[str, object],
) -> dict[str, object]:
    """Compare named metrics from two audits against a parameter-effect contract."""

    if not isinstance(comparison_contract, Mapping):
        raise AuditError("comparison contract must be an object")
    parameter_name = comparison_contract.get("parameter_name")
    if not isinstance(parameter_name, str) or not parameter_name:
        raise AuditError("comparison contract requires parameter_name")

    targets = _normalize_metric_specs(
        comparison_contract, ("target_metric_paths", "target_metrics")
    )
    if not targets:
        raise AuditError("comparison contract requires at least one target metric")
    non_targets = _normalize_metric_specs(
        comparison_contract,
        ("non_target_metrics", "non_target_metric_paths"),
        non_target=True,
    )

    target_results = [
        _compare_metric(baseline, candidate, spec, non_target=False) for spec in targets
    ]
    non_target_results = [
        _compare_metric(baseline, candidate, spec, non_target=True)
        for spec in non_targets
    ]
    return {
        "comparison_schema_version": COMPARISON_SCHEMA_VERSION,
        "parameter_name": parameter_name,
        "passed": all(item["passed"] for item in target_results + non_target_results),
        "target_metrics": target_results,
        "non_target_metrics": non_target_results,
    }


def _json_text(document: Mapping[str, Any]) -> str:
    return json.dumps(document, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Audit passenger-demand CSV outputs without modifying the model."
    )
    parser.add_argument("--input-root", required=True, type=Path)
    parser.add_argument("--config-root", type=Path)
    parser.add_argument("--json-output", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        result = audit_passenger_demand(args.input_root, config_root=args.config_root)
        text = _json_text(result)
        if args.json_output is None:
            sys.stdout.write(text)
        else:
            parent = args.json_output.parent
            if not parent.is_dir():
                raise AuditError(
                    f"json output parent directory does not exist: {_stable_display_name(parent)}"
                )
            with args.json_output.open("w", encoding="utf-8", newline="\n") as handle:
                handle.write(text)
        return 0
    except (AuditError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
