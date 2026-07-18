from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT_DIR = Path(__file__).resolve().parents[1]
MACRO_DIR = ROOT_DIR / "macro_layers"
if str(MACRO_DIR) not in sys.path:
    sys.path.insert(0, str(MACRO_DIR))

import macro_run_orchestrator_sim as orchestrator
import orchestrator_run_validation as run_validation

from airport_sim.server import run_cache


def write_raw(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="")


def write_rows(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def validation_manifest(**variant_meta: int) -> dict[str, object]:
    return {
        "seed": 7,
        "start_year": 2025,
        "years": 2,
        "variants": {"baseline": variant_meta},
    }


class RunValidationCompatibilityTests(unittest.TestCase):
    def test_csv_helpers_delegate_with_current_csv_and_callback_surfaces(self) -> None:
        path = Path("rows.csv")
        with mock.patch.object(run_validation, "csv_data_row_count", return_value=3) as row_count:
            self.assertEqual(3, orchestrator.csv_data_row_count(path))
        self.assertEqual((path,), row_count.call_args.args)
        self.assertIs(orchestrator.csv, row_count.call_args.kwargs["csv_module"])

        with mock.patch.object(run_validation, "glob_csv_row_count", return_value=4) as glob_count:
            self.assertEqual(4, orchestrator.glob_csv_row_count(Path("root"), "*.csv"))
        self.assertIs(
            orchestrator.csv_data_row_count,
            glob_count.call_args.kwargs["csv_data_row_count"],
        )

        sentinel = {"row_count": 1}
        with mock.patch.object(run_validation, "inspect_staged_csv", return_value=sentinel) as inspect:
            self.assertIs(sentinel, orchestrator.inspect_staged_csv(path, 7, 2025, 2027))
        self.assertIs(orchestrator.csv, inspect.call_args.kwargs["csv_module"])

    def test_validation_and_manifest_surfaces_keep_existing_dependencies(self) -> None:
        sentinel = {"validated": True}
        manifest = {"variants": {"baseline": {}}}
        with mock.patch.object(run_validation, "validate_staged_run", return_value=sentinel) as validate:
            self.assertIs(sentinel, orchestrator.validate_staged_run(Path("run"), manifest))
        self.assertEqual(orchestrator.REGION_ORDER, validate.call_args.kwargs["region_order"])
        self.assertIs(orchestrator.inspect_staged_csv, validate.call_args.kwargs["inspect_staged_csv"])
        self.assertIs(orchestrator.hashlib, validate.call_args.kwargs["hashlib_module"])
        self.assertIs(orchestrator.time, validate.call_args.kwargs["time_module"])

        with mock.patch.object(
            run_validation,
            "write_validated_run_manifest",
            return_value=manifest,
        ) as write_manifest:
            self.assertIs(manifest, orchestrator.write_validated_run_manifest(Path("run"), manifest))
        self.assertIs(orchestrator.write_json_file, write_manifest.call_args.kwargs["write_json_file"])
        self.assertIs(orchestrator.validate_staged_run, write_manifest.call_args.kwargs["validate_staged_run"])

    def test_manifest_builders_and_publish_selection_delegate(self) -> None:
        expected = {"delegated": True}
        global_result = {"rows": [1]}
        regional_result = {"regional_rows_by_region": {}}
        with mock.patch.object(run_validation, "build_variant_manifest", return_value=expected) as variant:
            self.assertIs(
                expected,
                orchestrator.build_variant_manifest(
                    Path("final"),
                    "baseline",
                    global_result,
                    regional_result,
                ),
            )
        self.assertEqual(
            (Path("final"), "baseline", global_result, regional_result),
            variant.call_args.args,
        )

        args = argparse.Namespace(artifact_profile="full")
        with mock.patch.object(run_validation, "build_run_manifest", return_value=expected) as run_manifest:
            self.assertIs(
                expected,
                orchestrator.build_run_manifest(
                    args,
                    7,
                    "run_7",
                    Path("final/run_7"),
                    {"baseline": {}},
                    None,
                    None,
                ),
            )
        self.assertEqual(orchestrator.RUN_MANIFEST_SCHEMA_VERSION, run_manifest.call_args.kwargs["schema_version"])
        self.assertIs(orchestrator.platform, run_manifest.call_args.kwargs["platform_module"])
        self.assertIs(orchestrator.BRANCH_SCENARIO_PROFILES, run_manifest.call_args.kwargs["branch_profiles"])

        publish_args = argparse.Namespace(publish_viewer="baseline")
        with mock.patch.object(run_validation, "requested_publish_variant", return_value="baseline") as publish:
            self.assertEqual("baseline", orchestrator.requested_publish_variant(publish_args, {"x": 1}))
        self.assertEqual((publish_args, {"x": 1}), publish.call_args.args)

    def test_new_validation_module_is_a_seed_cache_dependency(self) -> None:
        names = {
            path.name
            for path in run_cache.dependency_files(
                ROOT_DIR / "airport_sim" / "server",
                ROOT_DIR,
            )
        }
        self.assertIn("orchestrator_run_validation.py", names)


class CsvInspectionTests(unittest.TestCase):
    def test_row_count_and_glob_count_keep_header_only_protocol(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            write_raw(root / "a.csv", "seed\n7\n8\n")
            write_raw(root / "b.csv", "seed\n9\n")
            write_raw(root / "nested" / "ignored.csv", "seed\n10\n")

            self.assertEqual(
                2,
                run_validation.csv_data_row_count(root / "a.csv", csv_module=csv),
            )
            self.assertEqual(
                3,
                run_validation.glob_csv_row_count(
                    root,
                    "*.csv",
                    csv_data_row_count=lambda path: run_validation.csv_data_row_count(
                        path,
                        csv_module=csv,
                    ),
                ),
            )

    def test_inspection_returns_header_regions_and_inclusive_run_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            path = Path(temporary_dir) / "rows.csv"
            write_raw(
                path,
                "seed,year,year_index,region_id,value\n"
                "7.0,2025.0,0.0,r1,a\n"
                "7,2027,2,r1,b\n",
            )
            inspection = run_validation.inspect_staged_csv(
                path,
                7,
                2025,
                2027,
                csv_module=csv,
            )

        self.assertEqual(2, inspection["row_count"])
        self.assertEqual(["seed", "year", "year_index", "region_id", "value"], inspection["header"])
        self.assertEqual({"r1"}, inspection["regions"])

    def test_header_contract_failures_keep_current_messages(self) -> None:
        cases = {
            "empty header": ("\n", "empty header"),
            "blank header field": ("seed,,year\n7,x,2025\n", "empty header"),
            "duplicate header": ("seed,seed\n7,7\n", "duplicate header fields"),
            "missing seed": ("year\n2025\n", "missing seed field"),
        }
        with tempfile.TemporaryDirectory() as temporary_dir:
            path = Path(temporary_dir) / "rows.csv"
            for label, (content, message) in cases.items():
                with self.subTest(label=label):
                    write_raw(path, content)
                    with self.assertRaisesRegex(ValueError, message):
                        run_validation.inspect_staged_csv(path, 7, 2025, 2027, csv_module=csv)

    def test_row_contract_failures_keep_current_messages_and_line_numbers(self) -> None:
        cases = {
            "width": ("seed,year\n7\n", "row width mismatch.*:2"),
            "invalid seed": ("seed\nbad\n", "invalid seed.*:2"),
            "wrong seed": ("seed\n8\n", "seed mismatch.*expected 7, got 8"),
            "invalid year": ("seed,year\n7,bad\n", "invalid year.*:2"),
            "low year": ("seed,year\n7,2024\n", "year outside Run range.*2024"),
            "high year": ("seed,year\n7,2028\n", "year outside Run range.*2028"),
            "invalid index": ("seed,year_index\n7,bad\n", "invalid year_index.*:2"),
            "low index": ("seed,year_index\n7,-1\n", "year_index outside Run range.*-1"),
            "high index": ("seed,year_index\n7,3\n", "year_index outside Run range.*3"),
        }
        with tempfile.TemporaryDirectory() as temporary_dir:
            path = Path(temporary_dir) / "rows.csv"
            for label, (content, message) in cases.items():
                with self.subTest(label=label):
                    write_raw(path, content)
                    with self.assertRaisesRegex(ValueError, message):
                        run_validation.inspect_staged_csv(path, 7, 2025, 2027, csv_module=csv)


class StagedRunValidationTests(unittest.TestCase):
    def validate(self, run_dir: Path, manifest: dict[str, object], *, regions: tuple[str, ...] = ("r1", "r2")):
        return run_validation.validate_staged_run(
            run_dir,
            manifest,
            region_order=regions,
            inspect_staged_csv=lambda path, seed, start, final: run_validation.inspect_staged_csv(
                path,
                seed,
                start,
                final,
                csv_module=csv,
            ),
            hashlib_module=hashlib,
            time_module=mock.Mock(strftime=mock.Mock(return_value="fixed-time")),
        )

    def test_manifest_variant_and_skip_file_failures_are_distinct(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            run_dir = Path(temporary_dir)
            with self.assertRaisesRegex(ValueError, "Run manifest has no variants"):
                self.validate(run_dir, {"variants": {}})
            with self.assertRaisesRegex(FileNotFoundError, "missing staged variant directory"):
                self.validate(run_dir, validation_manifest())
            (run_dir / "baseline").mkdir()
            with self.assertRaisesRegex(FileNotFoundError, "missing staged downstream skip manifest"):
                self.validate(run_dir, validation_manifest())

    def test_validation_summary_preserves_counts_sorted_headers_regions_and_timestamp(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            run_dir = Path(temporary_dir)
            variant = run_dir / "baseline"
            write_raw(variant / "city_airport_downstream_skips.json", "{}")
            global_path = variant / "global_macro" / "global_macro_feedback_seed_sweep.csv"
            write_rows(
                global_path,
                [{"seed": 7, "year": 2025, "year_index": 0}],
                ["seed", "year", "year_index"],
            )
            regional_paths = [
                variant / "regional_macro" / "r2" / "r2_regional_macro_seed_sweep.csv",
                variant / "regional_macro" / "r1" / "r1_regional_macro_seed_sweep.csv",
            ]
            for region, path in (("r2", regional_paths[0]), ("r1", regional_paths[1])):
                write_rows(
                    path,
                    [{"seed": 7, "year": 2027, "year_index": 2, "region_id": region}],
                    ["seed", "year", "year_index", "region_id"],
                )

            summary = self.validate(
                run_dir,
                validation_manifest(global_rows=1, regional_rows=2),
            )

            digest = hashlib.sha256()
            for path in sorted(regional_paths):
                digest.update(path.relative_to(variant).as_posix().encode("utf-8"))
                digest.update(b"\0")
                digest.update(b"seed,year,year_index,region_id")
                digest.update(b"\0")

        self.assertEqual("airport-run-validation-v1", summary["schema_version"])
        self.assertEqual("fixed-time", summary["validated_at"])
        self.assertEqual(1, summary["variant_count"])
        self.assertEqual(1, summary["row_counts"]["baseline"]["global_rows"])
        self.assertEqual(2, summary["file_counts"]["baseline"]["regional_rows"])
        self.assertEqual(digest.hexdigest(), summary["header_digests"]["baseline"]["regional_rows"])
        self.assertEqual(["r1", "r2"], summary["region_coverage"]["baseline"]["regional_rows"])
        self.assertEqual(hashlib.sha256().hexdigest(), summary["header_digests"]["baseline"]["valuation_rows"])

    def test_row_count_and_region_coverage_mismatches_remain_separate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            run_dir = Path(temporary_dir)
            variant = run_dir / "baseline"
            write_raw(variant / "city_airport_downstream_skips.json", "{}")
            global_path = variant / "global_macro" / "global_macro_feedback_seed_sweep.csv"
            write_rows(global_path, [{"seed": 7}], ["seed"])
            with self.assertRaisesRegex(ValueError, "row count mismatch.*expected 2, got 1"):
                self.validate(run_dir, validation_manifest(global_rows=2))

            regional_path = variant / "regional_macro" / "r1" / "r1_regional_macro_seed_sweep.csv"
            write_rows(regional_path, [{"seed": 7, "region_id": "r1"}], ["seed", "region_id"])
            with self.assertRaisesRegex(ValueError, r"region coverage mismatch.*missing=\['r2'\]"):
                self.validate(run_dir, validation_manifest(global_rows=1, regional_rows=1))


class ManifestConstructionTests(unittest.TestCase):
    def test_validated_manifest_write_order_and_payload_snapshots_are_stable(self) -> None:
        events: list[tuple[str, object]] = []
        manifest: dict[str, object] = {"run_id": "run_7"}

        def write_json(path: Path, payload: dict[str, object]) -> None:
            events.append(("write", (path, copy.deepcopy(payload))))

        def validate(run_dir: Path, payload: dict[str, object]) -> dict[str, object]:
            events.append(("validate", (run_dir, copy.deepcopy(payload))))
            return {"schema_version": "validation-v1"}

        result = run_validation.write_validated_run_manifest(
            Path("staging"),
            manifest,
            write_json_file=write_json,
            validate_staged_run=validate,
        )

        self.assertIs(manifest, result)
        self.assertEqual(["write", "validate", "write"], [event[0] for event in events])
        self.assertEqual("staging", events[0][1][1]["run_state"])
        self.assertNotIn("validation", events[0][1][1])
        self.assertEqual("staging", events[1][1][1]["run_state"])
        self.assertEqual("complete", events[2][1][1]["run_state"])
        self.assertEqual({"schema_version": "validation-v1"}, events[2][1][1]["validation"])
        self.assertEqual(Path("staging/manifest.json"), events[0][1][0])

    def test_validation_failure_leaves_only_staging_manifest_write(self) -> None:
        writes: list[dict[str, object]] = []
        manifest: dict[str, object] = {"run_id": "run_7"}
        with self.assertRaisesRegex(ValueError, "validation failed"):
            run_validation.write_validated_run_manifest(
                Path("staging"),
                manifest,
                write_json_file=lambda path, payload: writes.append(copy.deepcopy(payload)),
                validate_staged_run=mock.Mock(side_effect=ValueError("validation failed")),
            )

        self.assertEqual([{"run_id": "run_7", "run_state": "staging"}], writes)
        self.assertEqual("staging", manifest["run_state"])
        self.assertNotIn("validation", manifest)

    def test_variant_manifest_preserves_all_count_fields_and_optional_scenario_count(self) -> None:
        regional = {
            "regional_rows_by_region": {"r1": [1, 2], "r2": [3]},
            "reconciled_rows": [1, 2],
            "aviation_rows_by_region": {"r1": [1]},
            "supply_rows_by_region": {"r1": [1, 2, 3]},
            "city_airport_rows_by_market": {"c1": [1]},
            "potential_passenger_forecast_rows_by_market": {"c1": [1, 2]},
            "quarterly_operations_rows_by_market": {"c1": [1, 2, 3]},
            "financial_state_rows_by_market": {"c1": [1, 2, 3, 4]},
            "valuation_forecast_rows_by_market": {"c1": [1, 2, 3, 4, 5]},
            "city_airport_downstream_skips": ["skip"],
        }
        baseline = run_validation.build_variant_manifest(
            Path("final"),
            "baseline",
            {"rows": [1, 2]},
            regional,
        )
        scenario = run_validation.build_variant_manifest(
            Path("final"),
            "scenario",
            {"rows": [1, 2]},
            regional,
            active_global_scenario_rows=1,
        )

        self.assertEqual(
            [
                "path",
                "global_rows",
                "regional_rows",
                "reconciled_rows",
                "aviation_rows",
                "supply_rows",
                "city_airport_rows",
                "potential_passenger_forecast_rows",
                "quarterly_operations_rows",
                "financial_state_rows",
                "valuation_rows",
                "city_airport_downstream_skips",
            ],
            list(baseline),
        )
        self.assertEqual("final/baseline", baseline["path"])
        self.assertEqual(3, baseline["regional_rows"])
        self.assertEqual(5, baseline["valuation_rows"])
        self.assertNotIn("active_global_scenario_rows", baseline)
        self.assertEqual(1, scenario["active_global_scenario_rows"])

    def test_run_manifest_preserves_field_order_defaults_versions_and_profile_ids(self) -> None:
        args = argparse.Namespace(
            artifact_profile="seed-cache",
            start_year=2025,
            years=60,
            feedback_iterations=3,
            volatility_scale=1.25,
            initial_gdp=100.0,
        )
        platform_module = mock.Mock()
        platform_module.python_version.return_value = "3.13.test"
        platform_module.python_implementation.return_value = "CPython-test"
        variants = {"baseline": {"global_rows": 60}}
        manifest = run_validation.build_run_manifest(
            args,
            7,
            "run_7",
            Path("final/run_7"),
            variants,
            {"state": "occurred"},
            "scenario_1",
            schema_version="manifest-v1",
            model_version="model-v1",
            output_schema_version="output-v1",
            orchestrator_version="orchestrator-v1",
            platform_module=platform_module,
            branch_profiles={"z": {}, "a": {}},
        )

        self.assertEqual(
            [
                "schema_version",
                "model_version",
                "output_schema_version",
                "orchestrator_version",
                "python_version",
                "python_implementation",
                "artifact_profile",
                "run_id",
                "seed",
                "start_year",
                "years",
                "feedback_iterations",
                "volatility_scale",
                "initial_gdp",
                "output_dir",
                "variants",
                "scenario",
                "scenario_variant",
                "branch_scenario_profile_count",
                "branch_scenario_profile_ids",
                "published",
            ],
            list(manifest),
        )
        self.assertEqual("3.13.test", manifest["python_version"])
        self.assertEqual("CPython-test", manifest["python_implementation"])
        self.assertEqual("seed-cache", manifest["artifact_profile"])
        self.assertIs(variants, manifest["variants"])
        self.assertEqual(["a", "z"], manifest["branch_scenario_profile_ids"])
        self.assertIsNone(manifest["published"])

    def test_publish_variant_selection_keeps_none_baseline_scenario_and_error_paths(self) -> None:
        manifest = {"scenario_variant": " scenario_1 "}
        self.assertIsNone(
            run_validation.requested_publish_variant(
                argparse.Namespace(publish_viewer="none"),
                manifest,
            )
        )
        self.assertEqual(
            "baseline",
            run_validation.requested_publish_variant(
                argparse.Namespace(publish_viewer="baseline"),
                manifest,
            ),
        )
        self.assertEqual(
            "scenario_1",
            run_validation.requested_publish_variant(
                argparse.Namespace(publish_viewer="scenario"),
                manifest,
            ),
        )
        with self.assertRaisesRegex(ValueError, "requires --scenario-state"):
            run_validation.requested_publish_variant(
                argparse.Namespace(publish_viewer="scenario"),
                {"scenario_variant": None},
            )


if __name__ == "__main__":
    unittest.main()
