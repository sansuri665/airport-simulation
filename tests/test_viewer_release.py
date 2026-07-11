from __future__ import annotations

import json
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


def write_script(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def build_minimal_variant(root: Path) -> Path:
    variant = root / "output" / "macro_runs" / "atomic_test_run" / "baseline"
    write_script(
        variant / "global_macro" / "global_macro_feedback_viewer_data.js",
        'window.GLOBAL_MACRO_FEEDBACK_DATA = [{"seed": 7, "year": 2025}];',
    )
    write_script(
        variant / "regional_macro" / "china_mainland" / "china_mainland_regional_macro_viewer_data.js",
        'window.REGIONAL_MACRO_DATA = [{"region_id": "china_mainland", "seed": 7}];',
    )
    write_script(
        variant / "regional_macro_reconciled" / "regional_macro_reconciled_viewer_data.js",
        "window.REGIONAL_MACRO_RECONCILED_DATA = [];\nwindow.REGIONAL_MACRO_RECONCILIATION_DATA = [];",
    )
    write_script(
        variant
        / "regional_aviation_demand"
        / "china_mainland"
        / "china_mainland_aviation_demand_viewer_data.js",
        'window.REGIONAL_AVIATION_DEMAND_DATA = [{"region_id": "china_mainland", "seed": 7}];',
    )
    write_script(
        variant
        / "regional_air_capacity_supply"
        / "china_mainland"
        / "china_mainland_air_capacity_supply_viewer_data.js",
        'window.REGIONAL_AIR_CAPACITY_SUPPLY_DATA = [{"region_id": "china_mainland", "seed": 7}];',
    )
    write_script(
        variant
        / "city_airport_quarterly_operations"
        / "china_mainland"
        / "beijing_airport_system_quarterly_operations_viewer_data.js",
        'window.CITY_AIRPORT_QUARTERLY_OPERATIONS_DATA = {"rows": [{"seed": 7}]};',
    )
    write_script(
        variant
        / "city_airport_financial_state"
        / "china_mainland"
        / "beijing_airport_system_financial_state_viewer_data.js",
        'window.CITY_AIRPORT_FINANCIAL_STATE_DATA = {"rows": [{"seed": 7}]};',
    )
    write_script(
        variant
        / "city_airport_valuation"
        / "china_mainland"
        / "beijing_airport_system_valuation_forecast_viewer_data.js",
        'window.CITY_AIRPORT_VALUATION_FORECAST_DATA = {"rows": [{"seed": 7}]};',
    )
    write_script(
        variant
        / "city_airport_potential_passenger_forecast"
        / "china_mainland"
        / "beijing_airport_system_potential_passenger_forecast_viewer_data.js",
        'window.CITY_AIRPORT_POTENTIAL_PASSENGER_FORECAST_DATA = {"config": {}, "rows": [{"seed": 7}]};',
    )
    return variant


class AtomicViewerReleaseTests(unittest.TestCase):
    def test_publish_creates_versioned_bundles_and_switches_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            temporary_root = Path(temporary_dir)
            variant = build_minimal_variant(temporary_root)
            viewer_root = temporary_root / "output"
            with mock.patch.object(orchestrator, "AIRPORT_DIR", temporary_root):
                result = orchestrator.publish_variant_to_viewer(variant, viewer_root)

            manifest_path = viewer_root / "current_viewer_manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(orchestrator.VIEWER_RELEASE_MANIFEST_VERSION, manifest["schema_version"])
            self.assertEqual(result["release_id"], manifest["release_id"])
            self.assertIsNone(manifest["seed"])
            self.assertEqual(orchestrator.MODEL_VERSION, manifest["model_version"])
            self.assertEqual(orchestrator.OUTPUT_SCHEMA_VERSION, manifest["output_schema_version"])
            self.assertEqual(3, manifest["bundle_count"])
            self.assertEqual(3, result["bundle_count"])
            self.assertFalse(any(path.name.startswith(".staging_") for path in (viewer_root / "viewer_releases").iterdir()))

            for viewer_id, script_url in manifest["scripts"].items():
                self.assertTrue(script_url.startswith("./output/viewer_releases/"), viewer_id)
                script_path = temporary_root / script_url.removeprefix("./")
                self.assertTrue(script_path.exists(), viewer_id)
                self.assertEqual(manifest["bundle_sha256"][viewer_id], orchestrator.sha256_file(script_path))

            global_bundle = temporary_root / manifest["scripts"]["global_gdp_viewer"].removeprefix("./")
            global_content = global_bundle.read_text(encoding="utf-8")
            self.assertIn("GLOBAL_MACRO_FEEDBACK_DATA", global_content)
            self.assertIn('REGIONAL_MACRO_DATASETS["china_mainland"]', global_content)
            self.assertIn(result["release_id"], (viewer_root / "current_viewer_manifest.js").read_text(encoding="utf-8"))

            self.assertTrue(
                (
                    viewer_root
                    / "city_airport_quarterly_operations"
                    / "china_mainland"
                    / "beijing_airport_system_quarterly_operations_viewer_data.js"
                ).exists()
            )

    def test_manifest_pointer_is_unchanged_when_compatibility_copy_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            temporary_root = Path(temporary_dir)
            variant = build_minimal_variant(temporary_root)
            viewer_root = temporary_root / "output"
            pointer = viewer_root / "current_viewer_manifest.js"
            pointer.parent.mkdir(parents=True, exist_ok=True)
            pointer.write_text("window.AIRPORT_VIEWER_MANIFEST = {old: true};\n", encoding="utf-8")

            with (
                mock.patch.object(orchestrator, "AIRPORT_DIR", temporary_root),
                mock.patch.object(
                    orchestrator,
                    "copy_variant_to_legacy_viewer",
                    side_effect=RuntimeError("copy failed"),
                ),
            ):
                with self.assertRaisesRegex(RuntimeError, "copy failed"):
                    orchestrator.publish_variant_to_viewer(variant, viewer_root)

            self.assertEqual(
                "window.AIRPORT_VIEWER_MANIFEST = {old: true};\n",
                pointer.read_text(encoding="utf-8"),
            )
            self.assertFalse(any(path.name.startswith(".staging_") for path in (viewer_root / "viewer_releases").iterdir()))


if __name__ == "__main__":
    unittest.main()
