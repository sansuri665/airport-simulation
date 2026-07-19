from __future__ import annotations

import tempfile
import unittest
from contextlib import nullcontext
from pathlib import Path

from airport_sim.server import forecast_viewer, serializers
from macro_layers.forecast_system import viewer_assets


class ForecastViewerContextServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.rows = [
            {
                "seed": "7",
                "as_of_year": "2030",
                "forecast_year": "2085",
                "forecast_report_id": "public_consensus",
                "future_peek_mode": "false",
                "forecast_effective_passengers_mid_million": "123.5",
                "debug_hidden_true_effective_passengers_million": "130.0",
            },
            {
                "seed": "7",
                "as_of_year": "2030",
                "forecast_year": "2085",
                "forecast_report_id": "god_mode",
                "future_peek_mode": "true",
                "forecast_effective_passengers_mid_million": "130.0",
                "debug_hidden_true_effective_passengers_million": "130.0",
            },
        ]
        self.config = {
            "config_version": "v1",
            "forecast_model_version": "m1",
            "city_airport_market_id": "beijing_airport_system",
            "city_name": "北京",
            "region_id": "china_mainland",
            "forecast_reports": [
                {"forecast_report_id": "public_consensus", "future_peek_mode": False},
                {"forecast_report_id": "god_mode", "future_peek_mode": True},
            ],
        }
        self.manifest = {
            "run_id": "seed_7_years_60",
            "seed": 7,
            "start_year": 2025,
            "years": 60,
        }

    def dependencies(self, root: Path, *, cache_status: str = "ready") -> dict[str, object]:
        run_root = root / "runs"
        run_dir = run_root / "seed_7_years_60"
        manifest_path = run_dir / forecast_viewer.RUN_MANIFEST_RELATIVE_PATH
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text("placeholder", encoding="utf-8")
        csv_path = run_dir / forecast_viewer.FORECAST_RELATIVE_CSV
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        csv_path.write_text("placeholder", encoding="utf-8")
        return {
            "workspace_payload": lambda: {
                "workspaceRevision": 3,
                "slots": [{
                    "slotId": "seed_7_years_60",
                    "cacheStatus": cache_status,
                    "cacheRunId": "seed_7_years_60",
                }],
            },
            "run_root": run_root,
            "run_id_for": lambda seed, years: f"seed_{seed}_years_{years}",
            "ensure_inside": lambda expected_root, path: path,
            "lock_for_run": lambda run_id: nullcontext(),
            "read_json": lambda path: dict(self.manifest),
            "read_csv": lambda path: self.rows,
            "decode_rows": serializers.decode_viewer_csv_rows,
            "null_fields": viewer_assets.FORECAST_VIEWER_NULL_FIELDS,
        }

    def test_player_index_and_report_never_project_audit_truth(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            dependencies = self.dependencies(root)
            index = forecast_viewer.index_payload(
                7, 60, "player",
                **dependencies,
                read_config=lambda path: self.config,
                config_path=root / "config.json",
                serialize_index=viewer_assets.serialize_viewer_index,
            )
            report = forecast_viewer.report_payload(
                7, 60, "player", "public_consensus",
                **dependencies,
                serialize_report=viewer_assets.serialize_viewer_report,
            )

        self.assertEqual(["public_consensus"], [item["reportId"] for item in index["index"]["reports"]])
        self.assertEqual("player", index["context"]["dataMode"])
        self.assertNotIn(
            "debug_hidden_true_effective_passengers_million",
            report["chunk"]["rows"][0],
        )
        with self.assertRaisesRegex(FileNotFoundError, "不存在报告"):
            with tempfile.TemporaryDirectory() as temporary_dir:
                root = Path(temporary_dir)
                forecast_viewer.report_payload(
                    7, 60, "player", "god_mode",
                    **self.dependencies(root),
                    serialize_report=viewer_assets.serialize_viewer_report,
                )

    def test_audit_report_keeps_truth_but_is_context_bound(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            report = forecast_viewer.report_payload(
                7, 60, "audit", "god_mode",
                **self.dependencies(Path(temporary_dir)),
                serialize_report=viewer_assets.serialize_viewer_report,
            )
        self.assertEqual("audit", report["context"]["dataMode"])
        self.assertEqual(130.0, report["chunk"]["rows"][0]["debug_hidden_true_effective_passengers_million"])

    def test_stale_cache_and_wrong_manifest_horizon_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            dependencies = self.dependencies(root, cache_status="stale")
            with self.assertRaises(forecast_viewer.ForecastViewerContextUnavailableError):
                forecast_viewer.report_payload(
                    7, 60, "player", "public_consensus",
                    **dependencies,
                    serialize_report=viewer_assets.serialize_viewer_report,
                )
            dependencies = self.dependencies(root)
            dependencies["read_json"] = lambda path: {
                **self.manifest,
                "years": 59,
            }
            with self.assertRaisesRegex(
                forecast_viewer.ForecastViewerContextUnavailableError,
                "年数与请求上下文不一致",
            ):
                forecast_viewer.report_payload(
                    7, 60, "player", "public_consensus",
                    **dependencies,
                    serialize_report=viewer_assets.serialize_viewer_report,
                )

    def test_forecast_years_must_stay_inside_manifest_timeline(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            dependencies = self.dependencies(Path(temporary_dir))
            dependencies["read_csv"] = lambda path: [
                {**row, "forecast_year": "2086"} for row in self.rows
            ]
            with self.assertRaisesRegex(
                forecast_viewer.ForecastViewerContextUnavailableError,
                "超出 Run Manifest 时间范围",
            ):
                forecast_viewer.report_payload(
                    7, 60, "player", "public_consensus",
                    **dependencies,
                    serialize_report=viewer_assets.serialize_viewer_report,
                )


if __name__ == "__main__":
    unittest.main()
