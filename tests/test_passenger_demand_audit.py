from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.audit_passenger_demand import (
    AUDIT_SCHEMA_VERSION,
    AuditError,
    audit_passenger_demand,
    compare_passenger_audits,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
AUDIT_SCRIPT = REPO_ROOT / "tools" / "audit_passenger_demand.py"
COMPONENTS = ("business", "leisure", "vfr", "long_haul", "transfer")


REGIONAL_DEMAND_FIELDS = [
    "regional_aviation_demand_param_version",
    "regional_aviation_demand_interface_version",
    "region_id",
    "region_name",
    "year_index",
    "year",
    "seed",
    "business_travel_share_pct",
    "leisure_travel_share_pct",
    "vfr_travel_share_pct",
    "long_haul_share_pct",
    "transfer_share_pct",
]

REGIONAL_SUPPLY_FIELDS = [
    "regional_air_supply_param_version",
    "regional_air_supply_interface_version",
    "region_id",
    "region_name",
    "year_index",
    "year",
    "seed",
    "potential_passengers_million",
    "reference_effective_passenger_capacity_million",
    "reference_served_passengers_million",
    "reference_unmet_passengers_million",
]

CITY_FIELDS = [
    "city_airport_demand_param_version",
    "city_airport_demand_interface_version",
    "city_airport_market_id",
    "city_name",
    "region_id",
    "region_name",
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
    "city_binding_bottleneck",
    *(f"{component}_city_demand_index" for component in COMPONENTS),
    *(f"{component}_passenger_share_pct" for component in COMPONENTS),
    *(f"{component}_passengers_million" for component in COMPONENTS),
    *(f"{component}_served_passengers_million" for component in COMPONENTS),
]

CITY_DIAGNOSTIC_FIELDS = [
    field
    for component in COMPONENTS
    for field in (
        f"{component}_city_demand_raw_index",
        f"{component}_city_demand_boundary_state",
        f"{component}_city_demand_floor_applied",
        f"{component}_city_demand_cap_applied",
        f"{component}_city_demand_consecutive_boundary_years",
    )
]



def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _demand_row(index: int, *, seed: int = 7, shares: tuple[float, ...] | None = None) -> dict[str, object]:
    values = shares or (20.0, 20.0, 20.0, 20.0, 20.0)
    return {
        "regional_aviation_demand_param_version": "regional-param-test-v1",
        "regional_aviation_demand_interface_version": "regional-interface-test-v1",
        "region_id": "test_region",
        "region_name": "测试区域",
        "year_index": index,
        "year": 2025 + index,
        "seed": seed,
        "business_travel_share_pct": values[0],
        "leisure_travel_share_pct": values[1],
        "vfr_travel_share_pct": values[2],
        "long_haul_share_pct": values[3],
        "transfer_share_pct": values[4],
    }


def _supply_row(index: int, *, seed: int = 7, potential: float = 100.0, served: float = 90.0) -> dict[str, object]:
    return {
        "regional_air_supply_param_version": "supply-param-test-v1",
        "regional_air_supply_interface_version": "supply-interface-test-v1",
        "region_id": "test_region",
        "region_name": "测试区域",
        "year_index": index,
        "year": 2025 + index,
        "seed": seed,
        "potential_passengers_million": potential,
        "reference_effective_passenger_capacity_million": served,
        "reference_served_passengers_million": served,
        "reference_unmet_passengers_million": potential - served,
    }


def _city_row(
    index: int,
    *,
    seed: int = 7,
    city_id: str = "test_city",
    region_id: str = "test_region",
    shares: tuple[float, ...] | None = None,
    indices: tuple[float, ...] | None = None,
    potential: float = 60.0,
    served: float = 50.0,
    capacity: float = 55.0,
    bottleneck: str = "airline_supply_bottleneck",
) -> dict[str, object]:
    share_values = shares or (20.0, 20.0, 20.0, 20.0, 20.0)
    index_values = indices or (100.0, 100.0, 100.0, 100.0, 100.0)
    passenger_values = [potential * value / 100.0 for value in share_values]
    served_values = [served * value / 100.0 for value in share_values]
    row: dict[str, object] = {
        "city_airport_demand_param_version": "city-param-test-v1",
        "city_airport_demand_interface_version": "city-interface-test-v1",
        "city_airport_market_id": city_id,
        "city_name": "测试城市",
        "region_id": region_id,
        "region_name": "测试区域",
        "year_index": index,
        "year": 2025 + index,
        "seed": seed,
        "baseline_region_demand_share_pct": 60.0,
        "source_region_reference_potential_passengers_million": 100.0,
        "city_potential_passengers_million": potential,
        "city_effective_capacity_million": capacity,
        "city_airline_serviceable_supply_million": capacity,
        "city_served_passengers_million": served,
        "city_unmet_passengers_million": potential - served,
        "city_binding_bottleneck": bottleneck,
    }
    for component, value in zip(COMPONENTS, index_values):
        row[f"{component}_city_demand_index"] = value
    for component, value in zip(COMPONENTS, share_values):
        row[f"{component}_passenger_share_pct"] = value
    for component, value in zip(COMPONENTS, passenger_values):
        row[f"{component}_passengers_million"] = value
    for component, value in zip(COMPONENTS, served_values):
        row[f"{component}_served_passengers_million"] = value
    return row


def _make_input(
    root: Path,
    *,
    pressure: bool = False,
    include_manifest: bool = False,
) -> Path:
    demand_rows = [_demand_row(0), _demand_row(1)]
    city_rows = [_city_row(0), _city_row(1)]
    if pressure:
        demand_rows = [
            _demand_row(0),
            _demand_row(1, shares=(25.0, 20.0, 20.0, 20.0, 15.0)),
            _demand_row(2, shares=(30.0, 20.0, 20.0, 20.0, 10.0)),
        ]
        city_rows = [
            _city_row(0),
            _city_row(
                1,
                shares=(25.0, 20.0, 20.0, 20.0, 15.0),
                indices=(245.0, 100.0, 100.0, 100.0, 45.0),
                served=45.0,
                capacity=45.0,
                bottleneck="airport_bottleneck",
            ),
            _city_row(
                2,
                shares=(30.0, 20.0, 20.0, 20.0, 10.0),
                indices=(245.0, 100.0, 100.0, 100.0, 45.0),
                served=45.0,
                capacity=45.0,
                bottleneck="airport_bottleneck",
            ),
        ]
    supply_rows = [_supply_row(index) for index in range(len(demand_rows))]

    _write_csv(
        root / "regional_aviation_demand" / "nested" / "test_region_aviation_demand_seed_sweep.csv",
        REGIONAL_DEMAND_FIELDS,
        demand_rows,
    )
    _write_csv(
        root / "regional_air_capacity_supply" / "nested" / "test_region_air_capacity_supply_seed_sweep.csv",
        REGIONAL_SUPPLY_FIELDS,
        supply_rows,
    )
    _write_csv(
        root / "city_airport_market_demand" / "test_region" / "test_city_city_airport_demand_seed_sweep.csv",
        CITY_FIELDS,
        city_rows,
    )
    if include_manifest:
        document = {
            "schema_version": "test-manifest-v1",
            "seed": 7,
            "start_year": 2025,
            "years": len(demand_rows) - 1,
            "expected_year_index_min": 0,
            "expected_year_index_max": len(demand_rows) - 1,
            "included_layers": {
                "regional_aviation_demand": {"files": 1, "rows": len(demand_rows)},
                "regional_air_capacity_supply": {"files": 1, "rows": len(supply_rows)},
                "city_airport_market_demand": {
                    "files": 1,
                    "rows": len(city_rows),
                    "region_scope": "test_region",
                },
            },
        }
        (root / "sample_manifest.json").write_text(
            json.dumps(document, ensure_ascii=False), encoding="utf-8"
        )
    return root


def _make_diagnostic_input(root: Path) -> Path:
    input_root = _make_input(root, pressure=True)
    path = next((input_root / "city_airport_market_demand").rglob("*.csv"))
    rows = _read_csv(path)
    for row in rows:
        year_index = int(row["year_index"])
        for component in COMPONENTS:
            final = float(row[f"{component}_city_demand_index"])
            state = "none"
            raw = final
            floor = 0
            cap = 0
            streak = 0
            if component == "business" and year_index in {1, 2}:
                raw = 260.0
                state = "cap"
                cap = 1
                streak = year_index
            elif component == "transfer" and year_index in {1, 2}:
                raw = 40.0
                state = "floor"
                floor = 1
                streak = year_index
            row[f"{component}_city_demand_raw_index"] = raw
            row[f"{component}_city_demand_boundary_state"] = state
            row[f"{component}_city_demand_floor_applied"] = floor
            row[f"{component}_city_demand_cap_applied"] = cap
            row[f"{component}_city_demand_consecutive_boundary_years"] = streak
    _write_csv(path, CITY_FIELDS + CITY_DIAGNOSTIC_FIELDS, rows)
    return input_root


def _write_config(root: Path, city_id: str = "test_city") -> None:
    root.mkdir(parents=True, exist_ok=True)
    document = {
        "market": {
            "city_airport_market_id": city_id,
            "region_id": "test_region",
        },
        "demand_model": {
            "baseline_city_potential_passengers_million": 60.0,
            "baseline_region_demand_share_pct": 60.0,
        },
    }
    (root / f"{city_id}.json").write_text(
        json.dumps(document, ensure_ascii=False), encoding="utf-8"
    )


class PassengerDemandAuditSuccessTests(unittest.TestCase):
    def test_neutral_two_year_sample_satisfies_all_accounting(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            input_root = _make_input(Path(temporary) / "sample", include_manifest=True)
            audit = audit_passenger_demand(input_root)

        self.assertEqual(AUDIT_SCHEMA_VERSION, audit["audit_schema_version"])
        self.assertTrue(audit["accounting_invariants"]["all_passed"])
        self.assertEqual(0, audit["regional_components"]["business"]["increase_path_count"])
        self.assertEqual(
            1,
            audit["regional_components"]["business"][
                "approximately_unchanged_path_count"
            ],
        )
        self.assertEqual(
            "final_output_only",
            audit["city_components"]["boundary_observation_scope"],
        )
        self.assertEqual(
            "unobservable",
            audit["diagnostic_capabilities"]["city_component_internal_clamp_flag"]["status"],
        )

    def test_pressure_sample_reports_boundaries_bottleneck_and_share_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            audit = audit_passenger_demand(
                _make_input(Path(temporary) / "sample", pressure=True)
            )
        self.assertEqual(1, audit["regional_components"]["business"]["increase_path_count"])
        self.assertEqual(1, audit["city_components"]["transfer"]["decrease_path_count"])
        boundaries = audit["city_components"]["observable_exact_final_index_boundaries"]
        self.assertEqual(2, boundaries["business"]["exact_upper_boundary_row_count"])
        self.assertEqual(2, boundaries["transfer"]["exact_lower_boundary_row_count"])
        airport = audit["supply_and_capacity"]["city_binding_bottleneck"]["airport_bottleneck"]
        self.assertEqual(2, airport["row_count"])
        self.assertEqual(1, airport["city_path_count"])
        self.assertEqual(2, airport["longest_consecutive_years"])

    def test_g3_raw_flags_and_streaks_are_consumed_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            audit = audit_passenger_demand(
                _make_diagnostic_input(Path(temporary) / "sample")
            )
        self.assertEqual(
            "internal_raw_and_final",
            audit["city_components"]["boundary_observation_scope"],
        )
        self.assertEqual(
            "supported",
            audit["diagnostic_capabilities"]["city_component_raw_target"]["status"],
        )
        self.assertEqual(
            "supported",
            audit["diagnostic_capabilities"]["city_component_internal_clamp_flag"]["status"],
        )
        boundaries = audit["city_components"]["observable_exact_final_index_boundaries"]
        self.assertEqual(2, boundaries["business"]["true_cap_applied_row_count"])
        self.assertEqual(2, boundaries["transfer"]["true_floor_applied_row_count"])
        self.assertEqual(2, boundaries["business"]["max_reported_consecutive_boundary_years"])
        self.assertEqual(0, boundaries["business"]["diagnostic_consistency_failure_count"])
        self.assertEqual(260.0, boundaries["business"]["raw_index_max"])
        self.assertEqual(40.0, boundaries["transfer"]["raw_index_min"])

    def test_config_coverage_and_baseline_bridge(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            input_root = _make_input(base / "sample")
            config_root = base / "configs"
            _write_config(config_root)
            audit = audit_passenger_demand(input_root, config_root=config_root)
            coverage = audit["completeness"]["configuration_coverage"]
            self.assertEqual("checked", coverage["status"])
            self.assertEqual([], coverage["missing_output_city_ids"])
            configured = audit["region_city_bridge"]["configuration_baseline"]["regions"]["test_region"]
            self.assertEqual(60.0, configured["baseline_city_potential_total_million"])

            _write_config(config_root, "missing_city")
            mismatch = audit_passenger_demand(input_root, config_root=config_root)
            self.assertEqual(
                ["missing_city"],
                mismatch["completeness"]["configuration_coverage"]["missing_output_city_ids"],
            )
            self.assertIn(
                "config_output_city_set_mismatch",
                {warning["code"] for warning in mismatch["warnings"]},
            )

    def test_no_config_reports_machine_readable_warning_and_capability(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            audit = audit_passenger_demand(_make_input(Path(temporary) / "sample"))
        self.assertEqual(
            "unsupported",
            audit["diagnostic_capabilities"]["configuration_coverage"]["status"],
        )
        self.assertIn(
            "config_root_not_provided",
            {warning["code"] for warning in audit["warnings"]},
        )

    def test_repeated_calls_and_cli_stdout_are_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            input_root = _make_input(Path(temporary) / "sample")
            first = audit_passenger_demand(input_root)
            second = audit_passenger_demand(input_root)
            self.assertEqual(first, second)
            command = [
                sys.executable,
                str(AUDIT_SCRIPT),
                "--input-root",
                str(input_root),
            ]
            one = subprocess.run(command, check=True, capture_output=True)
            two = subprocess.run(command, check=True, capture_output=True)
        self.assertEqual(one.stdout, two.stdout)
        self.assertEqual(b"", one.stderr)

    def test_json_output_is_utf8_and_stdout_mode_creates_no_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            input_root = _make_input(base / "样例")
            before = sorted(path.relative_to(input_root) for path in input_root.rglob("*"))
            process_environment = dict(os.environ)
            process_environment["PYTHONIOENCODING"] = "cp1252"
            stdout_run = subprocess.run(
                [sys.executable, str(AUDIT_SCRIPT), "--input-root", str(input_root)],
                check=True,
                capture_output=True,
                env=process_environment,
            )
            after = sorted(path.relative_to(input_root) for path in input_root.rglob("*"))
            self.assertEqual(before, after)
            self.assertIn("样例", stdout_run.stdout.decode("utf-8"))

            output = base / "audit.json"
            file_run = subprocess.run(
                [
                    sys.executable,
                    str(AUDIT_SCRIPT),
                    "--input-root",
                    str(input_root),
                    "--json-output",
                    str(output),
                ],
                check=True,
                capture_output=True,
            )
            self.assertEqual(b"", file_run.stdout)
            loaded = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(AUDIT_SCHEMA_VERSION, loaded["audit_schema_version"])

    def test_paths_do_not_leak_into_json(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            strange = Path(temporary) / r"C:\private\sample"
            audit = audit_passenger_demand(_make_input(strange))
            serialized = json.dumps(audit, ensure_ascii=False, sort_keys=True)
        self.assertEqual("sample", audit["input_identity"]["input_root_display_name"])
        self.assertNotIn(temporary, serialized)
        self.assertNotIn("C:\\private", serialized)

class PassengerDemandAuditErrorTests(unittest.TestCase):
    def _assert_error_after_mutation(self, mutation) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = _make_input(Path(temporary) / "sample")
            mutation(root)
            with self.assertRaises(AuditError):
                audit_passenger_demand(root)

    def test_missing_required_layer_directory_fails(self) -> None:
        self._assert_error_after_mutation(
            lambda root: __import__("shutil").rmtree(root / "regional_air_capacity_supply")
        )

    def test_missing_required_column_fails(self) -> None:
        def mutate(root: Path) -> None:
            path = next((root / "regional_aviation_demand").rglob("*.csv"))
            rows = _read_csv(path)
            for row in rows:
                row.pop("transfer_share_pct", None)
            fields = [field for field in REGIONAL_DEMAND_FIELDS if field != "transfer_share_pct"]
            _write_csv(path, fields, rows)

        self._assert_error_after_mutation(mutate)

    def test_mixed_seed_fails(self) -> None:
        def mutate(root: Path) -> None:
            path = next((root / "regional_aviation_demand").rglob("*.csv"))
            rows = _read_csv(path)
            rows[1]["seed"] = "8"
            _write_csv(path, REGIONAL_DEMAND_FIELDS, rows)

        self._assert_error_after_mutation(mutate)

    def test_missing_year_index_fails(self) -> None:
        def mutate(root: Path) -> None:
            path = next((root / "city_airport_market_demand").rglob("*.csv"))
            rows = _read_csv(path)
            rows[1]["year_index"] = "2"
            rows[1]["year"] = "2027"
            _write_csv(path, CITY_FIELDS, rows)

        self._assert_error_after_mutation(mutate)

    def test_duplicate_city_fails(self) -> None:
        def mutate(root: Path) -> None:
            original = next((root / "city_airport_market_demand").rglob("*.csv"))
            duplicate = original.parent / "duplicate_city_airport_demand_seed_sweep.csv"
            duplicate.write_bytes(original.read_bytes())

        self._assert_error_after_mutation(mutate)

    def test_nan_fails(self) -> None:
        def mutate(root: Path) -> None:
            path = next((root / "regional_air_capacity_supply").rglob("*.csv"))
            rows = _read_csv(path)
            rows[0]["potential_passengers_million"] = "NaN"
            _write_csv(path, REGIONAL_SUPPLY_FIELDS, rows)

        self._assert_error_after_mutation(mutate)

    def test_city_region_change_fails(self) -> None:
        def mutate(root: Path) -> None:
            path = next((root / "city_airport_market_demand").rglob("*.csv"))
            rows = _read_csv(path)
            rows[1]["region_id"] = "other_region"
            _write_csv(path, CITY_FIELDS, rows)

        self._assert_error_after_mutation(mutate)

    def test_manifest_mismatch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = _make_input(Path(temporary) / "sample", include_manifest=True)
            path = root / "sample_manifest.json"
            manifest = json.loads(path.read_text(encoding="utf-8"))
            manifest["seed"] = 999
            path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(AuditError, "manifest"):
                audit_passenger_demand(root)

    def test_cli_missing_output_parent_is_clear_nonzero_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            input_root = _make_input(base / "sample")
            result = subprocess.run(
                [
                    sys.executable,
                    str(AUDIT_SCRIPT),
                    "--input-root",
                    str(input_root),
                    "--json-output",
                    str(base / "missing" / "audit.json"),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertNotEqual(0, result.returncode)
        self.assertIn("parent directory does not exist", result.stderr)


class PassengerDemandComparisonTests(unittest.TestCase):
    def setUp(self) -> None:
        self.baseline = {
            "metrics": {
                "up": 10.0,
                "down": 10.0,
                "changed": 10.0,
                "stable": 10.0,
            }
        }
        self.candidate = {
            "metrics": {
                "up": 12.0,
                "down": 8.0,
                "changed": 11.0,
                "stable": 10.05,
            }
        }

    def test_all_directions_thresholds_and_non_target_drift_pass(self) -> None:
        contract = {
            "parameter_name": "test_parameter",
            "target_metric_paths": {
                "metrics.up": {"expected_direction": "increase", "minimum_absolute_change": 2.0},
                "metrics.down": {"expected_direction": "decrease", "minimum_relative_change": 0.2},
                "metrics.changed": {"expected_direction": "change", "minimum_absolute_change": 0.5},
                "metrics.stable": {"expected_direction": "unchanged", "maximum_absolute_change": 0.1},
            },
            "non_target_metrics": [
                {
                    "path": "metrics.stable",
                    "maximum_absolute_change": 0.1,
                    "maximum_relative_change": 0.01,
                }
            ],
        }
        result = compare_passenger_audits(self.baseline, self.candidate, contract)
        self.assertTrue(result["passed"])
        self.assertEqual(4, len(result["target_metrics"]))
        self.assertEqual(1, len(result["non_target_metrics"]))

    def test_threshold_failure_is_reported(self) -> None:
        result = compare_passenger_audits(
            self.baseline,
            self.candidate,
            {
                "parameter_name": "test_parameter",
                "target_metrics": [
                    {
                        "path": "metrics.up",
                        "expected_direction": "increase",
                        "minimum_absolute_change": 3.0,
                    }
                ],
            },
        )
        self.assertFalse(result["passed"])
        self.assertFalse(result["target_metrics"][0]["passed"])

    def test_missing_metric_path_fails_instead_of_becoming_zero(self) -> None:
        with self.assertRaisesRegex(AuditError, "missing"):
            compare_passenger_audits(
                self.baseline,
                self.candidate,
                {
                    "parameter_name": "test_parameter",
                    "target_metrics": [
                        {"path": "metrics.absent", "expected_direction": "change"}
                    ],
                },
            )

    def test_zero_baseline_relative_threshold_fails_clearly(self) -> None:
        baseline = {"metrics": {"value": 0.0}}
        candidate = {"metrics": {"value": 1.0}}
        with self.assertRaisesRegex(AuditError, "zero baseline"):
            compare_passenger_audits(
                baseline,
                candidate,
                {
                    "parameter_name": "test_parameter",
                    "target_metrics": [
                        {
                            "path": "metrics.value",
                            "expected_direction": "increase",
                            "minimum_relative_change": 0.1,
                        }
                    ],
                },
            )


if __name__ == "__main__":
    unittest.main()
