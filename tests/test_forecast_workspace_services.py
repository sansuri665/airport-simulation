from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from airport_sim.server import app as local_ui
from airport_sim.server import forecast_candidates
from airport_sim.server import run_cache
from airport_sim.server import workspace_service


class ServiceCompatibilityTests(unittest.TestCase):
    def test_app_forecast_context_delegates_with_existing_paths_and_mock_points(self) -> None:
        expected = ({"release_id": "r1"}, [{"year": "2030"}])
        with mock.patch.object(
            forecast_candidates,
            "forecast_candidate_release_context",
            return_value=expected,
        ) as delegated:
            actual = local_ui.forecast_candidate_release_context()

        self.assertIs(expected, actual)
        self.assertEqual(local_ui.OUTPUT_ROOT, delegated.call_args.kwargs["output_root"])
        self.assertEqual(local_ui.ROOT_DIR, delegated.call_args.kwargs["root_dir"])
        self.assertIs(local_ui.read_json, delegated.call_args.kwargs["read_json"])
        self.assertIs(local_ui.ensure_inside, delegated.call_args.kwargs["ensure_inside"])
        self.assertIs(local_ui.read_csv, delegated.call_args.kwargs["read_csv"])
        self.assertIs(local_ui.as_float, delegated.call_args.kwargs["as_float"])

    def test_app_forecast_payload_surfaces_keep_existing_callbacks(self) -> None:
        catalog_expected = {"catalog": {"tiers": []}}
        candidate_expected = {"candidate": {"candidateId": "candidate"}}
        body = {"seed": 7}
        with mock.patch.object(
            forecast_candidates,
            "forecast_candidate_catalog_payload",
            return_value=catalog_expected,
        ) as catalog, mock.patch.object(
            forecast_candidates,
            "generate_forecast_candidate_payload",
            return_value=candidate_expected,
        ) as generate:
            self.assertIs(catalog_expected, local_ui.forecast_candidate_catalog_payload())
            self.assertIs(candidate_expected, local_ui.generate_forecast_candidate_payload(body))

        self.assertIs(
            local_ui.forecast_candidate_release_context,
            catalog.call_args.kwargs["release_context"],
        )
        self.assertIs(local_ui.forecast_candidate_layer, catalog.call_args.kwargs["candidate_layer"])
        self.assertEqual(local_ui.BEIJING_FORECAST_CONFIG, catalog.call_args.kwargs["config_path"])
        self.assertEqual((body,), generate.call_args.args)
        self.assertIs(
            local_ui.forecast_candidate_release_context,
            generate.call_args.kwargs["release_context"],
        )
        self.assertIs(local_ui.clean_seed, generate.call_args.kwargs["clean_seed"])

    def test_app_workspace_surfaces_delegate_with_existing_mock_points(self) -> None:
        release_expected = {"mode": "unavailable"}
        workspace_expected = {"ok": True, "delegated": True}
        with mock.patch.object(
            workspace_service,
            "current_viewer_release_status",
            return_value=release_expected,
        ) as release, mock.patch.object(
            workspace_service,
            "workspace_status",
            return_value=workspace_expected,
        ) as workspace:
            self.assertIs(release_expected, local_ui.current_viewer_release_status())
            self.assertIs(workspace_expected, local_ui.workspace_status())

        self.assertEqual(local_ui.OUTPUT_ROOT, release.call_args.kwargs["output_root"])
        self.assertIs(local_ui.read_json, release.call_args.kwargs["read_json"])
        self.assertIs(local_ui.list_cached_runs, workspace.call_args.kwargs["list_cached_runs"])
        self.assertIs(
            local_ui.current_viewer_release_status,
            workspace.call_args.kwargs["current_viewer_release_status"],
        )

    def test_run_cache_dependency_inventory_includes_both_new_services(self) -> None:
        names = {
            path.name
            for path in run_cache.dependency_files(local_ui.SERVER_DIR, local_ui.ROOT_DIR)
        }

        self.assertIn("forecast_candidates.py", names)
        self.assertIn("workspace_service.py", names)


class ForecastReleaseContextTests(unittest.TestCase):
    def call_context(
        self,
        root: Path,
        *,
        manifest: object,
        rows: list[dict[str, str]],
        source_value: str = "output/macro_runs/run_1/baseline",
    ) -> tuple[dict[str, object], list[dict[str, str]]]:
        output_root = root / "output"
        manifest_path = output_root / "current_viewer_manifest.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text("{}", encoding="utf-8")
        source_path = root / source_value
        city_path = source_path / forecast_candidates.BEIJING_CITY_DEMAND_RELATIVE_CSV
        city_path.parent.mkdir(parents=True, exist_ok=True)
        city_path.write_text("placeholder", encoding="utf-8")
        if isinstance(manifest, dict):
            manifest = {**manifest, "source_variant": source_value}
        return forecast_candidates.forecast_candidate_release_context(
            output_root=output_root,
            root_dir=root,
            read_json=lambda path: manifest,
            ensure_inside=lambda expected_root, path: path,
            read_csv=lambda path: rows,
            as_float=lambda value, default=0.0: float(value) if value is not None else default,
        )

    def test_missing_manifest_fails_before_reading(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            forbidden = mock.Mock(side_effect=AssertionError("must not read"))
            with self.assertRaisesRegex(FileNotFoundError, "当前没有可用于候选报告"):
                forecast_candidates.forecast_candidate_release_context(
                    output_root=Path(temporary_dir) / "output",
                    root_dir=Path(temporary_dir),
                    read_json=forbidden,
                    ensure_inside=lambda root, path: path,
                    read_csv=forbidden,
                    as_float=float,
                )

        forbidden.assert_not_called()

    def test_invalid_manifest_or_missing_source_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            output_root = root / "output"
            output_root.mkdir()
            (output_root / "current_viewer_manifest.json").write_text("{}", encoding="utf-8")
            kwargs = {
                "output_root": output_root,
                "root_dir": root,
                "ensure_inside": lambda expected_root, path: path,
                "read_csv": mock.Mock(),
                "as_float": float,
            }
            with self.assertRaisesRegex(ValueError, "清单无效"):
                forecast_candidates.forecast_candidate_release_context(
                    read_json=lambda path: [],
                    **kwargs,
                )
            with self.assertRaisesRegex(ValueError, "没有记录正式数据来源"):
                forecast_candidates.forecast_candidate_release_context(
                    read_json=lambda path: {"release_id": "r1"},
                    **kwargs,
                )

    def test_relative_source_is_resolved_inside_output_and_rows_keep_order(self) -> None:
        rows = [{"seed": "7", "year": "2031"}, {"seed": "7", "year": "2030"}]
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            output_root = root / "output"
            source_value = "output/macro_runs/run_1/baseline"
            source_path = root / source_value
            city_path = source_path / forecast_candidates.BEIJING_CITY_DEMAND_RELATIVE_CSV
            city_path.parent.mkdir(parents=True)
            city_path.write_text("placeholder", encoding="utf-8")
            output_root.mkdir(exist_ok=True)
            (output_root / "current_viewer_manifest.json").write_text("{}", encoding="utf-8")
            checked: list[tuple[Path, Path]] = []
            manifest = {"release_id": "r1", "source_variant": source_value, "seed": 7}

            actual_manifest, actual_rows = forecast_candidates.forecast_candidate_release_context(
                output_root=output_root,
                root_dir=root,
                read_json=lambda path: manifest,
                ensure_inside=lambda expected_root, path: checked.append((expected_root, path)) or path,
                read_csv=lambda path: rows,
                as_float=lambda value, default=0.0: float(value),
            )

        self.assertIs(manifest, actual_manifest)
        self.assertIs(rows, actual_rows)
        self.assertEqual([(output_root, source_path)], checked)
        self.assertEqual(["2031", "2030"], [row["year"] for row in actual_rows])

    def test_missing_empty_or_seed_mismatched_city_data_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            output_root = root / "output"
            output_root.mkdir()
            (output_root / "current_viewer_manifest.json").write_text("{}", encoding="utf-8")
            source = output_root / "run" / "baseline"
            manifest = {"release_id": "r1", "source_variant": str(source), "seed": 7}
            common = {
                "output_root": output_root,
                "root_dir": root,
                "read_json": lambda path: manifest,
                "ensure_inside": lambda expected_root, path: path,
                "as_float": lambda value, default=0.0: float(value),
            }
            with self.assertRaisesRegex(FileNotFoundError, "缺少北京城市航空市场数据"):
                forecast_candidates.forecast_candidate_release_context(
                    read_csv=mock.Mock(),
                    **common,
                )
            city_path = source / forecast_candidates.BEIJING_CITY_DEMAND_RELATIVE_CSV
            city_path.parent.mkdir(parents=True)
            city_path.write_text("placeholder", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "数据为空"):
                forecast_candidates.forecast_candidate_release_context(
                    read_csv=lambda path: [],
                    **common,
                )
            with self.assertRaisesRegex(ValueError, "Seed 与城市市场数据不一致"):
                forecast_candidates.forecast_candidate_release_context(
                    read_csv=lambda path: [{"seed": "7"}, {"seed": "8"}],
                    **common,
                )


class ForecastPayloadTests(unittest.TestCase):
    def test_catalog_uses_sorted_data_bounds_and_preserves_tier_order(self) -> None:
        manifest = {"release_id": "r1", "run_id": "run1", "seed": 7, "model_version": "m1"}
        rows = [{"year": "2040"}, {"year": "2025"}, {"year": "2030"}]
        catalog = {
            "tiers": [
                {"tierProfileId": "long", "naturalHorizonYears": 12},
                {"tierProfileId": "short", "naturalHorizonYears": 6},
            ]
        }
        layer = SimpleNamespace(forecast_candidate_catalog=mock.Mock(return_value=catalog))

        payload = forecast_candidates.forecast_candidate_catalog_payload(
            release_context=lambda: (manifest, rows),
            candidate_layer=layer,
            config_path=Path("forecast.json"),
            as_float=lambda value, default=0.0: float(value),
        )

        layer.forecast_candidate_catalog.assert_called_once_with(Path("forecast.json"))
        self.assertIs(catalog, payload["catalog"])
        self.assertEqual(["long", "short"], [tier["tierProfileId"] for tier in catalog["tiers"]])
        self.assertEqual([2028, 2034], [tier["maxFullAsOfYear"] for tier in catalog["tiers"]])
        self.assertEqual(
            {
                "releaseId": "r1",
                "runId": "run1",
                "seed": 7,
                "startYear": 2025,
                "finalYear": 2040,
                "modelVersion": "m1",
            },
            payload["release"],
        )

    def test_generate_passes_rows_unchanged_and_normalizes_request_exactly(self) -> None:
        manifest = {"release_id": "r1", "run_id": "run1", "seed": 7}
        rows = [{"year": "2031"}, {"year": "2030"}]
        generated = {"generatorVersion": "v2", "candidate": {"candidateId": "c1"}}
        layer = SimpleNamespace(generate_forecast_candidate=mock.Mock(return_value=generated))
        body = {
            "seed": "7",
            "asOfYear": "2030",
            "tierProfileId": " tier ",
            "narrativeProfileId": " style ",
            "modifierIds": [" first ", 2, None],
            "scoreMin": "70.5",
            "scoreMax": 80,
        }

        payload = forecast_candidates.generate_forecast_candidate_payload(
            body,
            release_context=lambda: (manifest, rows),
            candidate_layer=layer,
            config_path=Path("forecast.json"),
            clean_seed=int,
            as_float=lambda value, default=0.0: float(value),
        )

        self.assertEqual({"releaseId": "r1", "runId": "run1", **generated}, payload)
        call = layer.generate_forecast_candidate.call_args
        self.assertIs(rows, call.args[0])
        self.assertEqual(Path("forecast.json"), call.kwargs["config_path"])
        self.assertEqual(7, call.kwargs["seed"])
        self.assertEqual(2030, call.kwargs["as_of_year"])
        self.assertEqual("tier", call.kwargs["tier_profile_id"])
        self.assertEqual("style", call.kwargs["narrative_profile_id"])
        self.assertEqual("auto", call.kwargs["modifier_mode"])
        self.assertEqual(["first", "2", "None"], call.kwargs["modifier_ids"])
        self.assertEqual(70.5, call.kwargs["score_min"])
        self.assertEqual(80.0, call.kwargs["score_max"])
        self.assertEqual(0, call.kwargs["generation_nonce"])

    def test_generate_keeps_validation_order_and_never_calls_layer_on_invalid_input(self) -> None:
        layer = SimpleNamespace(
            generate_forecast_candidate=mock.Mock(side_effect=AssertionError("must not generate"))
        )
        common = {
            "release_context": lambda: ({"release_id": "r1", "seed": 7}, [{"seed": "7"}]),
            "candidate_layer": layer,
            "config_path": Path("forecast.json"),
            "clean_seed": int,
            "as_float": lambda value, default=0.0: float(value),
        }
        with self.assertRaisesRegex(ValueError, "Seed 必须与当前正式 Viewer 发布一致"):
            forecast_candidates.generate_forecast_candidate_payload(
                {"seed": 8, "modifierIds": "invalid"},
                **common,
            )
        with self.assertRaisesRegex(ValueError, "modifierIds must be an array"):
            forecast_candidates.generate_forecast_candidate_payload(
                {"seed": 7, "modifierIds": "invalid"},
                **common,
            )
        with self.assertRaisesRegex(ValueError, "年份、分数范围或候选编号无效"):
            forecast_candidates.generate_forecast_candidate_payload(
                {
                    "seed": 7,
                    "modifierIds": [],
                    "asOfYear": "invalid",
                    "scoreMin": 70,
                    "scoreMax": 80,
                },
                **common,
            )
        layer.generate_forecast_candidate.assert_not_called()


class WorkspaceServiceTests(unittest.TestCase):
    def test_missing_or_unreadable_manifest_reports_unavailable_with_stable_shape(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            output_root = Path(temporary_dir)
            missing = workspace_service.current_viewer_release_status(
                output_root=output_root,
                read_json=mock.Mock(side_effect=AssertionError("must not read")),
            )
            (output_root / "current_viewer_manifest.json").write_text("invalid", encoding="utf-8")
            unreadable = workspace_service.current_viewer_release_status(
                output_root=output_root,
                read_json=mock.Mock(side_effect=OSError("broken")),
            )

        expected_keys = [
            "mode", "releaseId", "runId", "variant", "seed", "startYear", "years",
            "modelVersion", "outputSchemaVersion", "generatedAt", "schemaVersion",
        ]
        self.assertEqual(expected_keys, list(missing))
        self.assertEqual(missing, unreadable)
        self.assertEqual("unavailable", missing["mode"])
        self.assertIsNone(missing["releaseId"])

    def test_valid_manifest_maps_only_existing_public_fields(self) -> None:
        manifest = {
            "release_id": " release-1 ",
            "run_id": "run-1",
            "variant": "baseline",
            "seed": 7,
            "start_year": 2025,
            "years": 60,
            "model_version": "m1",
            "output_schema_version": "o1",
            "generated_at": "now",
            "schema_version": "s1",
            "private": "ignored",
        }
        with tempfile.TemporaryDirectory() as temporary_dir:
            output_root = Path(temporary_dir)
            (output_root / "current_viewer_manifest.json").write_text("{}", encoding="utf-8")
            payload = workspace_service.current_viewer_release_status(
                output_root=output_root,
                read_json=lambda path: manifest,
            )

        self.assertEqual("versioned_release", payload["mode"])
        self.assertEqual("release-1", payload["releaseId"])
        self.assertEqual("run-1", payload["runId"])
        self.assertNotIn("private", payload)

    def test_workspace_counts_recursive_saves_and_keeps_relative_posix_roots(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            run_root = root / "output" / "seed_explorer_runs"
            save_root = root / "saves" / "seed_explorer"
            (save_root / "a").mkdir(parents=True)
            (save_root / "b" / "nested").mkdir(parents=True)
            (save_root / "a" / "dynamic_test_save.json").write_text("{}", encoding="utf-8")
            (save_root / "b" / "nested" / "dynamic_test_save.json").write_text("{}", encoding="utf-8")
            (save_root / "b" / "other.json").write_text("{}", encoding="utf-8")
            release = {"mode": "unavailable", "releaseId": None}
            cached = [{"runId": "a"}, {"runId": "b"}]

            payload = workspace_service.workspace_status(
                root_dir=root,
                run_root=run_root,
                save_root=save_root,
                service_id="service-v1",
                list_cached_runs=lambda: cached,
                current_viewer_release_status=lambda: release,
                getpid=lambda: 4321,
            )

        self.assertEqual(
            [
                "ok", "serviceId", "servicePid", "viewerRelease", "cachedRunCount",
                "saveCount", "runRoot", "saveRoot", "pages",
            ],
            list(payload),
        )
        self.assertEqual(2, payload["cachedRunCount"])
        self.assertEqual(2, payload["saveCount"])
        self.assertEqual("output/seed_explorer_runs", payload["runRoot"])
        self.assertEqual("saves/seed_explorer", payload["saveRoot"])
        self.assertIs(release, payload["viewerRelease"])
        self.assertEqual(
            {
                "home": "/",
                "seedExplorer": "/seed-explorer",
                "globalGdp": "/global-gdp",
                "cityMarkets": "/city-markets",
                "beijingForecast": "/beijing-forecast",
            },
            payload["pages"],
        )


if __name__ == "__main__":
    unittest.main()
