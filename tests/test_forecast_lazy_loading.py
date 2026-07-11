from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT_DIR = Path(__file__).resolve().parents[1]
PAGES_DIR = ROOT_DIR / "web" / "pages"
STATIC_DIR = ROOT_DIR / "web" / "static"
MACRO_DIR = ROOT_DIR / "macro_layers"
if str(MACRO_DIR) not in sys.path:
    sys.path.insert(0, str(MACRO_DIR))

import city_airport_potential_passenger_forecast_layer_sim as forecast_layer
import macro_run_orchestrator_sim as orchestrator
import test_viewer_release
from schema_support import load_schema_registry, validate_named_schema


SCHEMA_REGISTRY = load_schema_registry(ROOT_DIR / "schemas")


def sample_config() -> dict[str, object]:
    return {
        "config_version": "test-config-v1",
        "forecast": {"forecast_model_version": "test-model-v1"},
        "city_airport_market_id": "beijing_airport_system",
        "city_name": "北京",
        "region_id": "china_mainland",
        "forecast_reports": [
            {"forecast_report_id": "public_consensus", "forecast_report_display_name": "初级预测"},
            {"forecast_report_id": "basic_research", "forecast_report_display_name": "中级预测"},
        ],
    }


def sample_rows() -> list[dict[str, object]]:
    return [
        {
            "seed": 7,
            "as_of_year": 2030,
            "forecast_report_id": "public_consensus",
            "forecast_year": 2031,
            "forecast_effective_passengers_mid_million": 101.5,
        },
        {
            "seed": 7,
            "as_of_year": 2030,
            "forecast_report_id": "basic_research",
            "forecast_year": 2031,
            "forecast_effective_passengers_mid_million": 102.5,
        },
        {
            "seed": 7,
            "as_of_year": 2031,
            "forecast_report_id": "public_consensus",
            "forecast_year": 2032,
            "forecast_effective_passengers_mid_million": 103.5,
        },
    ]


def read_index_script(path: Path) -> dict[str, object]:
    content = path.read_text(encoding="utf-8")
    prefix = "(() => { const index = "
    marker = "; index.baseUrl ="
    if not content.startswith(prefix) or marker not in content:
        raise AssertionError("unexpected forecast lazy index script")
    return json.loads(content[len(prefix) : content.index(marker)])


class ForecastLazyLoadingTests(unittest.TestCase):
    def test_lazy_assets_partition_rows_without_data_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            output_dir = Path(temporary_dir)
            rows = sample_rows()
            result = forecast_layer.write_viewer_lazy_assets(output_dir, rows, sample_config())
            index_path = Path(result["index"])
            index = read_index_script(index_path)

            self.assertEqual(len(rows), index["totalRows"])
            self.assertEqual(2, result["reportCount"])
            self.assertEqual(
                ["public_consensus", "basic_research"],
                [report["reportId"] for report in index["reports"]],
            )
            self.assertNotIn("forecast_effective_passengers_mid_million", index_path.read_text(encoding="utf-8"))
            validate_named_schema(index, "forecast-viewer-lazy-index.schema.json", SCHEMA_REGISTRY)

            reconstructed: list[dict[str, object]] = []
            for report in index["reports"]:
                chunk_path = output_dir / index["chunkBase"] / report["file"]
                raw = chunk_path.read_bytes()
                chunk = json.loads(raw)
                self.assertEqual(report["sha256"], hashlib.sha256(raw).hexdigest())
                self.assertEqual(report["rowCount"], len(chunk["rows"]))
                validate_named_schema(
                    chunk,
                    "forecast-viewer-report-chunk.schema.json",
                    SCHEMA_REGISTRY,
                )
                reconstructed.extend(chunk["rows"])

            expected = [
                row
                for report_id in ("public_consensus", "basic_research")
                for row in rows
                if row["forecast_report_id"] == report_id
            ]
            self.assertEqual(expected, reconstructed)

    def test_atomic_viewer_release_uses_lazy_index_and_copies_chunks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            temporary_root = Path(temporary_dir)
            variant = test_viewer_release.build_minimal_variant(temporary_root)
            forecast_dir = variant / "city_airport_potential_passenger_forecast" / "china_mainland"
            forecast_layer.write_viewer_lazy_assets(forecast_dir, sample_rows(), sample_config())
            viewer_root = temporary_root / "output"

            with mock.patch.object(orchestrator, "AIRPORT_DIR", temporary_root):
                result = orchestrator.publish_variant_to_viewer(variant, viewer_root)

            release_dir = viewer_root / "viewer_releases" / result["release_id"]
            bundle = (release_dir / "beijing_potential_passenger_forecast_viewer_bundle.js").read_text(
                encoding="utf-8"
            )
            self.assertIn("AIRPORT_FORECAST_LAZY_INDEX", bundle)
            self.assertIn("document.currentScript.src", bundle)
            self.assertNotIn("CITY_AIRPORT_POTENTIAL_PASSENGER_FORECAST_DATA", bundle)

            chunk_dir_name = "beijing_airport_system_forecast_chunks"
            self.assertEqual(2, len(list((release_dir / chunk_dir_name).glob("*.json"))))
            canonical_dir = viewer_root / "city_airport_potential_passenger_forecast" / "china_mainland"
            self.assertTrue(
                (canonical_dir / "beijing_airport_system_forecast_index.js").is_file()
            )
            self.assertEqual(2, len(list((canonical_dir / chunk_dir_name).glob("*.json"))))

    def test_forecast_viewer_contains_lazy_loader_and_legacy_fallback(self) -> None:
        html = (PAGES_DIR / "beijing_potential_passenger_forecast_viewer.html").read_text(encoding="utf-8")
        bootstrap_script = "/static/js/beijing-forecast/bootstrap.js"
        bootstrap_js = (STATIC_DIR / "js" / "beijing-forecast" / "bootstrap.js").read_text(encoding="utf-8")
        page_script = "/static/js/beijing-forecast/page.js"
        page_js = (STATIC_DIR / "js" / "beijing-forecast" / "page.js").read_text(encoding="utf-8")

        self.assertIn(f'<script src="{bootstrap_script}"></script>', html)
        self.assertIn(f'<script src="{page_script}"></script>', html)
        self.assertIn("AIRPORT_FORECAST_DATA_READY", bootstrap_js)
        self.assertIn("legacyBeijingForecastDataScripts", html)
        self.assertIn("beijing_airport_system_forecast_index.js", bootstrap_js)
        self.assertIn("potential_passenger_forecast_viewer_data.js", html)
        self.assertIn("async function ensureReportLoaded(", page_js)
        self.assertIn("window.AIRPORT_FORECAST_LAZY_INDEX", page_js)
        self.assertIn("window.CITY_AIRPORT_POTENTIAL_PASSENGER_FORECAST_DATA", page_js)


if __name__ == "__main__":
    unittest.main()
