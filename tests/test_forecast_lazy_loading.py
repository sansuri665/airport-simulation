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
            {
                "forecast_report_id": "god_future_peek",
                "forecast_report_display_name": "神级审计",
                "future_peek_mode": True,
            },
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
            "debug_hidden_true_effective_passengers_million": 103.0,
            "realized_report_quality_score": 82.0,
            "forecast_lag_years": 4,
            "lagged_hidden_curve_effective_million": 99.0,
        },
        {
            "seed": 7,
            "as_of_year": 2030,
            "forecast_report_id": "basic_research",
            "forecast_year": 2031,
            "forecast_effective_passengers_mid_million": 102.5,
            "debug_hidden_true_effective_passengers_million": 103.0,
            "realized_report_quality_score": 88.0,
        },
        {
            "seed": 7,
            "as_of_year": 2031,
            "forecast_report_id": "public_consensus",
            "forecast_year": 2032,
            "forecast_effective_passengers_mid_million": 103.5,
            "debug_hidden_true_effective_passengers_million": 104.0,
            "realized_report_quality_score": 82.0,
        },
        {
            "seed": 7,
            "as_of_year": 2030,
            "forecast_report_id": "god_future_peek",
            "future_peek_mode": "true",
            "forecast_year": 2031,
            "forecast_effective_passengers_mid_million": 103.0,
            "debug_hidden_true_effective_passengers_million": 103.0,
            "realized_report_quality_score": 100.0,
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

            self.assertEqual(3, index["totalRows"])
            self.assertEqual(2, result["reportCount"])
            self.assertEqual(3, result["auditReportCount"])
            self.assertEqual("player", index["dataMode"])
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
                self.assertEqual("player", chunk["dataMode"])
                self.assertTrue(
                    all(
                        "debug_hidden_true_effective_passengers_million" not in row
                        and "realized_report_quality_score" not in row
                        for row in chunk["rows"]
                    )
                )
                validate_named_schema(
                    chunk,
                    "forecast-viewer-report-chunk.schema.json",
                    SCHEMA_REGISTRY,
                )
                reconstructed.extend(chunk["rows"])

            expected = [
                forecast_layer.forecast_player_row(row)
                for report_id in ("public_consensus", "basic_research")
                for row in rows
                if row["forecast_report_id"] == report_id
            ]
            self.assertEqual(expected, reconstructed)

            audit_index = read_index_script(Path(result["auditIndex"]))
            self.assertEqual("audit", audit_index["dataMode"])
            self.assertEqual(len(rows), audit_index["totalRows"])
            self.assertEqual(
                ["public_consensus", "basic_research", "god_future_peek"],
                [report["reportId"] for report in audit_index["reports"]],
            )
            audit_reconstructed: list[dict[str, object]] = []
            for report in audit_index["reports"]:
                chunk_path = output_dir / audit_index["chunkBase"] / report["file"]
                chunk = json.loads(chunk_path.read_bytes())
                self.assertEqual("audit", chunk["dataMode"])
                validate_named_schema(
                    chunk,
                    "forecast-viewer-report-chunk.schema.json",
                    SCHEMA_REGISTRY,
                )
                audit_reconstructed.extend(chunk["rows"])
            audit_expected = [
                forecast_layer.forecast_audit_row(row)
                for report_id in (
                    "public_consensus",
                    "basic_research",
                    "god_future_peek",
                )
                for row in rows
                if row["forecast_report_id"] == report_id
            ]
            self.assertEqual(audit_expected, audit_reconstructed)
            self.assertTrue(
                all(
                    "forecast_lag_years" not in row
                    and "lagged_hidden_curve_effective_million" not in row
                    for row in audit_reconstructed
                )
            )

    def test_atomic_viewer_release_uses_lazy_index_without_canonical_copy(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            temporary_root = Path(temporary_dir)
            variant = test_viewer_release.build_minimal_variant(temporary_root)
            forecast_dir = variant / "city_airport_potential_passenger_forecast" / "china_mainland"
            forecast_layer.write_viewer_lazy_assets(forecast_dir, sample_rows(), sample_config())
            viewer_root = temporary_root / "output"
            stale_chunk = (
                viewer_root
                / "city_airport_potential_passenger_forecast"
                / "china_mainland"
                / "beijing_airport_system_forecast_chunks"
                / "r_god_future_peek.json"
            )
            stale_chunk.parent.mkdir(parents=True, exist_ok=True)
            stale_chunk.write_text("{}", encoding="utf-8")
            obsolete_full_js = (
                stale_chunk.parents[1]
                / "beijing_airport_system_potential_passenger_forecast_viewer_data.js"
            )
            obsolete_full_js.write_text("obsolete", encoding="utf-8")

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
            audit_chunk_dir_name = "beijing_airport_system_audit_forecast_chunks"
            self.assertEqual(
                3,
                len(list((release_dir / audit_chunk_dir_name).glob("*.json"))),
            )
            self.assertTrue(
                (
                    release_dir
                    / "beijing_airport_system_forecast_audit_index.js"
                ).is_file()
            )
            canonical_dir = viewer_root / "city_airport_potential_passenger_forecast" / "china_mainland"
            self.assertFalse(
                (canonical_dir / "beijing_airport_system_forecast_index.js").exists()
            )
            self.assertEqual([stale_chunk], list((canonical_dir / chunk_dir_name).glob("*.json")))
            self.assertFalse((canonical_dir / audit_chunk_dir_name).exists())
            self.assertTrue(stale_chunk.exists())
            self.assertTrue(obsolete_full_js.exists())

    def test_forecast_viewer_requires_lazy_loader_without_full_data_fallback(self) -> None:
        html = (PAGES_DIR / "beijing_potential_passenger_forecast_viewer.html").read_text(encoding="utf-8")
        bootstrap_script = "/static/js/beijing-forecast/bootstrap.js"
        bootstrap_js = (STATIC_DIR / "js" / "beijing-forecast" / "bootstrap.js").read_text(encoding="utf-8")
        page_script = "/static/js/beijing-forecast/page.js"
        page_js = (STATIC_DIR / "js" / "beijing-forecast" / "page.js").read_text(encoding="utf-8")
        renderers_js = (STATIC_DIR / "js" / "beijing-forecast" / "renderers.js").read_text(encoding="utf-8")

        self.assertIn(f'<script src="{bootstrap_script}"></script>', html)
        self.assertIn(f'<script src="{page_script}"></script>', html)
        self.assertIn('<select id="modeSelect">', html)
        self.assertIn("/static/js/beijing-forecast/data-client.js", html)
        self.assertIn("/static/js/beijing-forecast/renderers.js", html)
        self.assertIn("AIRPORT_FORECAST_DATA_READY", bootstrap_js)
        self.assertIn("scripts?.beijing_potential_passenger_forecast_viewer", bootstrap_js)
        self.assertNotIn("beijing_airport_system_forecast_index.js", bootstrap_js)
        self.assertNotIn("legacyBeijingForecastDataScripts", html)
        self.assertNotIn("potential_passenger_forecast_viewer_data.js", html)
        self.assertNotIn("potential_passenger_forecast_viewer_data.js", bootstrap_js)
        self.assertIn("async function ensureReportLoaded(", page_js)
        self.assertIn("window.AIRPORT_FORECAST_LAZY_INDEX", page_js)
        self.assertNotIn("legacyPayload", page_js)
        self.assertNotIn("window.CITY_AIRPORT_POTENTIAL_PASSENGER_FORECAST_DATA", page_js)
        self.assertIn("loadAuditIndex", page_js)
        self.assertIn("forecast_narrative_modifier_labels", page_js)
        self.assertIn("MODIFIER_GROUP_LABELS", page_js)
        self.assertIn("modifier-tag", page_js)
        self.assertEqual(6, html.count("data-scope="))
        self.assertIn("forecast_airline_supply_fulfillment_pct", page_js)
        self.assertIn("forecast_airline_supply_gap_million", page_js)
        self.assertIn("realized_component_result_quality_score", page_js)
        self.assertIn("realized_component_potential_structure_score", page_js)
        self.assertIn("realized_component_supply_structure_score", page_js)
        self.assertIn("realized_component_fulfillment_score", page_js)
        self.assertIn("realized_component_interval_calibration_score", page_js)
        self.assertIn("candidate.componentResultScore", page_js)
        self.assertIn(
            "TIER_LABELS[meta.forecast_report_tier] || meta.forecast_report_tier",
            page_js,
        )
        self.assertIn(
            "TIER_LABELS[first.forecast_report_tier] || first.forecast_report_tier",
            page_js,
        )
        self.assertIn('class="true-point"', renderers_js)
        self.assertIn("真实值 ${fmt(truth)} 百万人", renderers_js)
        self.assertIn("预测值 ${fmt(predicted)} 百万人", renderers_js)
        self.assertNotIn('class="audit-gap-line"', renderers_js)
        self.assertIn('el.actualScore.textContent = "审计基准 · 不参与评分"', page_js)
        self.assertIn("realized_report_process_quality_score", page_js)
        self.assertIn('`实际评分 ${fmt(score)} / 100`', page_js)
        self.assertIn('"actual-score-low"', page_js)


if __name__ == "__main__":
    unittest.main()
