from __future__ import annotations

import argparse
import errno
import json
import os
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
from airport_sim.server import app as seed_explorer_server


def run_args(output_root: Path) -> argparse.Namespace:
    return argparse.Namespace(
        output_root=output_root,
        viewer_output_root=output_root.parent / "viewer",
        index_only=False,
        seed=7,
        random_seed=False,
        seed_min=1,
        seed_max=9,
        run_id="atomic_test_run",
        years=2,
        start_year=2025,
        initial_gdp=100.0,
        volatility_scale=1.0,
        feedback_iterations=1,
        scenario_state="none",
        publish_viewer="none",
        artifact_profile="full",
    )


def minimal_regional_result() -> dict[str, object]:
    return {
        "regional_rows_by_region": {},
        "reconciled_rows": [],
        "aviation_rows_by_region": {},
        "supply_rows_by_region": {},
        "city_airport_rows_by_market": {},
        "potential_passenger_forecast_rows_by_market": {},
        "quarterly_operations_rows_by_market": {},
        "financial_state_rows_by_market": {},
        "valuation_forecast_rows_by_market": {},
        "city_airport_downstream_skips": [],
    }


def write_minimal_variant(
    variant_dir: Path,
    seed: int,
    variant_name: str,
    global_result: dict[str, object],
    regional_result: dict[str, object],
    scenario: dict[str, object] | None,
    *,
    artifact_profile: str = "full",
) -> None:
    del variant_name, regional_result, scenario, artifact_profile
    orchestrator.write_csv_file(
        variant_dir / "global_macro" / "global_macro_feedback_seed_sweep.csv",
        [{"seed": seed, "year": 2025, "year_index": 0, **row} for row in global_result["rows"]],
        ["seed", "year", "year_index", "x"],
    )
    orchestrator.write_json_file(
        variant_dir / "city_airport_downstream_skips.json",
        {"skips": []},
    )


class AtomicMacroRunTests(unittest.TestCase):
    def test_directory_replace_retries_transient_windows_access_error(self) -> None:
        transient = PermissionError(errno.EACCES, "temporarily locked")
        with (
            mock.patch.object(orchestrator.os, "name", "nt"),
            mock.patch.object(orchestrator.os, "replace", side_effect=[transient, None]) as replace,
            mock.patch.object(orchestrator.time, "sleep") as sleep,
        ):
            orchestrator.replace_directory_with_retry(Path("staging"), Path("final"))

        self.assertEqual(2, replace.call_count)
        sleep.assert_called_once_with(0.05)

    def execute_with_minimal_model(self, output_root: Path) -> dict[str, object]:
        with (
            mock.patch.object(
                orchestrator,
                "run_global_variant",
                return_value={"rows": [{"x": 1}]},
            ),
            mock.patch.object(
                orchestrator,
                "run_regional_and_reconciliation",
                return_value=minimal_regional_result(),
            ),
            mock.patch.object(
                orchestrator,
                "write_variant_outputs",
                side_effect=write_minimal_variant,
            ),
        ):
            return orchestrator.execute_run(run_args(output_root))

    def test_complete_run_is_atomically_finalized_with_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            output_root = Path(temporary_dir) / "macro_runs"
            manifest = self.execute_with_minimal_model(output_root)
            final_run = output_root / "atomic_test_run"

            self.assertTrue(final_run.is_dir())
            self.assertEqual("complete", manifest["run_state"])
            self.assertEqual(orchestrator.RUN_MANIFEST_SCHEMA_VERSION, manifest["schema_version"])
            self.assertEqual(orchestrator.MODEL_VERSION, manifest["model_version"])
            self.assertEqual(1, manifest["validation"]["row_counts"]["baseline"]["global_rows"])
            self.assertFalse(any(path.name.startswith(".staging_") for path in output_root.iterdir()))

            stored = json.loads((final_run / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual("complete", stored["run_state"])
            self.assertTrue(
                os.path.samefile(final_run, stored["output_dir"]),
                f"Stored output directory does not identify {final_run}: {stored['output_dir']}",
            )
            self.assertEqual(1, stored["run_index"]["run_count"])

    def test_build_failure_leaves_no_formal_or_staging_run(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            output_root = Path(temporary_dir) / "macro_runs"

            def fail_after_partial_write(variant_dir: Path, *_: object, **__: object) -> None:
                variant_dir.mkdir(parents=True)
                (variant_dir / "partial.txt").write_text("partial", encoding="utf-8")
                raise RuntimeError("simulated layer failure")

            with (
                mock.patch.object(
                    orchestrator,
                    "run_global_variant",
                    return_value={"rows": [{"x": 1}]},
                ),
                mock.patch.object(
                    orchestrator,
                    "run_regional_and_reconciliation",
                    return_value=minimal_regional_result(),
                ),
                mock.patch.object(
                    orchestrator,
                    "write_variant_outputs",
                    side_effect=fail_after_partial_write,
                ),
            ):
                with self.assertRaisesRegex(RuntimeError, "simulated layer failure"):
                    orchestrator.execute_run(run_args(output_root))

            self.assertFalse((output_root / "atomic_test_run").exists())
            self.assertFalse(any(path.name.startswith(".staging_") for path in output_root.iterdir()))

    def test_validation_failure_does_not_publish_incomplete_run(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            output_root = Path(temporary_dir) / "macro_runs"

            def write_wrong_row_count(variant_dir: Path, *_: object, **__: object) -> None:
                orchestrator.write_csv_file(
                    variant_dir / "global_macro" / "global_macro_feedback_seed_sweep.csv",
                    [],
                    ["seed", "year", "year_index", "x"],
                )
                orchestrator.write_json_file(
                    variant_dir / "city_airport_downstream_skips.json",
                    {"skips": []},
                )

            with (
                mock.patch.object(
                    orchestrator,
                    "run_global_variant",
                    return_value={"rows": [{"x": 1}]},
                ),
                mock.patch.object(
                    orchestrator,
                    "run_regional_and_reconciliation",
                    return_value=minimal_regional_result(),
                ),
                mock.patch.object(
                    orchestrator,
                    "write_variant_outputs",
                    side_effect=write_wrong_row_count,
                ),
            ):
                with self.assertRaisesRegex(ValueError, "staged row count mismatch"):
                    orchestrator.execute_run(run_args(output_root))

            self.assertFalse((output_root / "atomic_test_run").exists())
            self.assertFalse(any(path.name.startswith(".staging_") for path in output_root.iterdir()))

    def test_validation_rejects_wrong_seed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            run_dir = Path(temporary_dir)
            variant_dir = run_dir / "baseline"
            orchestrator.write_csv_file(
                variant_dir / "global_macro" / "global_macro_feedback_seed_sweep.csv",
                [{"seed": 8, "year": 2025, "year_index": 0, "x": 1}],
                ["seed", "year", "year_index", "x"],
            )
            orchestrator.write_json_file(variant_dir / "city_airport_downstream_skips.json", {"skips": []})
            manifest = {
                "seed": 7,
                "start_year": 2025,
                "years": 2,
                "variants": {"baseline": {"global_rows": 1}},
            }

            with self.assertRaisesRegex(ValueError, "seed mismatch"):
                orchestrator.validate_staged_run(run_dir, manifest)

    def test_validation_requires_all_regions(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            run_dir = Path(temporary_dir)
            variant_dir = run_dir / "baseline"
            orchestrator.write_csv_file(
                variant_dir / "regional_macro" / "north_america" / "north_america_regional_macro_seed_sweep.csv",
                [{"seed": 7, "year": 2025, "year_index": 0, "region_id": "north_america"}],
                ["seed", "year", "year_index", "region_id"],
            )
            orchestrator.write_json_file(variant_dir / "city_airport_downstream_skips.json", {"skips": []})
            manifest = {
                "seed": 7,
                "start_year": 2025,
                "years": 2,
                "variants": {"baseline": {"regional_rows": 1}},
            }

            with self.assertRaisesRegex(ValueError, "region coverage mismatch"):
                orchestrator.validate_staged_run(run_dir, manifest)

    def test_run_index_ignores_orphan_staging_directories(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            output_root = Path(temporary_dir) / "macro_runs"
            staging = output_root / ".staging_interrupted"
            (staging / "baseline").mkdir(parents=True)
            orchestrator.write_json_file(
                staging / "manifest.json",
                {
                    "run_id": "interrupted",
                    "variants": {"baseline": {"global_rows": 1}},
                },
            )

            self.assertEqual([], orchestrator.build_run_index(output_root)["runs"])

    def test_version_record_matches_runtime_constants(self) -> None:
        record = json.loads((ROOT_DIR / "config" / "airport_versions.json").read_text(encoding="utf-8"))
        self.assertEqual(orchestrator.ORCHESTRATOR_VERSION, record["orchestrator_version"])
        self.assertEqual(orchestrator.RUN_MANIFEST_SCHEMA_VERSION, record["run_manifest_schema_version"])
        self.assertEqual(orchestrator.OUTPUT_SCHEMA_VERSION, record["output_schema_version"])
        self.assertEqual(orchestrator.MODEL_VERSION, record["model_version"])
        self.assertEqual(
            seed_explorer_server.SEED_EXPLORER_API_SCHEMA_VERSION,
            record["seed_explorer_api_schema_version"],
        )

    def test_api_envelope_adds_version_metadata_without_removing_payload(self) -> None:
        envelope = seed_explorer_server.api_envelope({"ok": True, "seed": 7})
        self.assertTrue(envelope["ok"])
        self.assertEqual(7, envelope["seed"])
        self.assertEqual(seed_explorer_server.MODEL_VERSION, envelope["modelVersion"])
        self.assertEqual(
            seed_explorer_server.SEED_EXPLORER_API_SCHEMA_VERSION,
            envelope["apiSchemaVersion"],
        )
        self.assertIn("pythonVersion", envelope)


if __name__ == "__main__":
    unittest.main()
