from __future__ import annotations

import tempfile
import unittest
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from airport_sim.server import app as local_ui
from airport_sim.server import forecast_candidates, run_cache, workspace_service


def rows_for(seed: int, start_year: int = 2025, years: int = 5) -> list[dict[str, str]]:
    return [
        {"seed": str(seed), "year": str(year)}
        for year in range(start_year, start_year + years + 1)
    ]


class ServiceDelegationTests(unittest.TestCase):
    def test_app_candidate_source_context_delegates_all_identity_boundaries(self) -> None:
        expected = ({"source": "seed_cache"}, [{"year": "2025"}])
        with mock.patch.object(
            forecast_candidates,
            "forecast_candidate_source_context",
            return_value=expected,
        ) as delegated:
            actual = local_ui.forecast_candidate_source_context(7, 60, "seed_cache")

        self.assertIs(expected, actual)
        self.assertEqual((7, 60, "seed_cache"), delegated.call_args.args)
        self.assertIs(local_ui.seed_workspace_payload, delegated.call_args.kwargs["workspace_payload"])
        self.assertIs(local_ui.lock_for_run, delegated.call_args.kwargs["lock_for_run"])
        self.assertEqual(local_ui.RUN_ROOT, delegated.call_args.kwargs["run_root"])

    def test_app_candidate_payloads_keep_explicit_source_callback(self) -> None:
        body = {"seed": 7, "years": 60, "source": "seed_cache"}
        with (
            mock.patch.object(
                forecast_candidates,
                "forecast_candidate_catalog_payload",
                return_value={"catalog": {}},
            ) as catalog,
            mock.patch.object(
                forecast_candidates,
                "generate_forecast_candidate_payload",
                return_value={"candidate": {}},
            ) as generate,
        ):
            local_ui.forecast_candidate_catalog_payload(7, 60, "seed_cache")
            local_ui.generate_forecast_candidate_payload(body)

        self.assertEqual((7, 60, "seed_cache"), catalog.call_args.args)
        self.assertIs(
            local_ui.forecast_candidate_source_context,
            catalog.call_args.kwargs["source_context"],
        )
        self.assertIs(
            local_ui.forecast_candidate_source_context,
            generate.call_args.kwargs["source_context"],
        )
        self.assertIs(local_ui.clean_years, generate.call_args.kwargs["clean_years"])

    def test_run_cache_dependency_inventory_includes_forecast_services(self) -> None:
        names = {
            path.name
            for path in run_cache.dependency_files(local_ui.SERVER_DIR, local_ui.ROOT_DIR)
        }
        self.assertIn("forecast_candidates.py", names)
        self.assertIn("forecast_viewer.py", names)
        self.assertIn("workspace_service.py", names)


class ForecastSourceContextTests(unittest.TestCase):
    def common(self, root: Path, workspace: dict[str, object]) -> dict[str, object]:
        return {
            "output_root": root / "output",
            "root_dir": root,
            "run_root": root / "output" / "seed_explorer_runs",
            "workspace_payload": lambda: workspace,
            "run_id_for": lambda seed, years: f"seed_{seed}_years_{years}",
            "lock_for_run": lambda run_id: nullcontext(),
            "read_json": lambda path: {},
            "ensure_inside": lambda expected_root, path: path,
            "read_csv": lambda path: rows_for(7),
            "as_float": lambda value, default=0.0: float(value) if value is not None else default,
        }

    def test_release_source_is_explicit_and_carries_audit_context(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            output = root / "output"
            source = output / "macro_runs" / "release-run" / "baseline"
            city_path = source / forecast_candidates.BEIJING_CITY_DEMAND_RELATIVE_CSV
            city_path.parent.mkdir(parents=True)
            city_path.write_text("placeholder", encoding="utf-8")
            (output / "current_viewer_manifest.json").write_text("{}", encoding="utf-8")
            workspace = {
                "workspaceRevision": 9,
                "slots": [{
                    "slotId": "seed_7_years_5",
                    "isCurrentViewerRelease": True,
                    "cacheStatus": "missing",
                }],
            }
            manifest = {
                "release_id": "release-7",
                "run_id": "release-run",
                "seed": 7,
                "years": 5,
                "source_variant": str(source),
                "model_version": "m1",
            }
            common = self.common(root, workspace)
            common["read_json"] = lambda path: manifest
            context, actual_rows = forecast_candidates.forecast_candidate_source_context(
                7, 5, "viewer_release", **common
            )

        self.assertEqual("viewer_release", context["source"])
        self.assertEqual("audit", context["dataMode"])
        self.assertEqual("release-7", context["releaseId"])
        self.assertEqual((2025, 2030), (context["startYear"], context["finalYear"]))
        self.assertEqual(rows_for(7), actual_rows)

    def test_cache_source_locks_exact_registered_run_and_never_reads_release(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            run_dir = root / "output" / "seed_explorer_runs" / "seed_7_years_5"
            city_path = run_dir / "baseline" / forecast_candidates.BEIJING_CITY_DEMAND_RELATIVE_CSV
            city_path.parent.mkdir(parents=True)
            city_path.write_text("placeholder", encoding="utf-8")
            workspace = {
                "workspaceRevision": 4,
                "slots": [{
                    "slotId": "seed_7_years_5",
                    "isCurrentViewerRelease": False,
                    "cacheStatus": "ready",
                    "cacheRunId": "seed_7_years_5",
                }],
            }
            locks: list[str] = []
            common = self.common(root, workspace)
            common["read_json"] = mock.Mock(side_effect=AssertionError("must not read manifest"))
            common["lock_for_run"] = lambda run_id: locks.append(run_id) or nullcontext()
            context, _ = forecast_candidates.forecast_candidate_source_context(
                7, 5, "seed_cache", **common
            )

        self.assertEqual(["seed_7_years_5"], locks)
        self.assertEqual("seed_7_years_5", context["cacheRunId"])
        self.assertNotIn("releaseId", context)

    def test_wrong_source_or_identity_is_rejected_without_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            workspace = {
                "workspaceRevision": 1,
                "slots": [{
                    "slotId": "seed_7_years_5",
                    "isCurrentViewerRelease": True,
                    "cacheStatus": "missing",
                }],
            }
            common = self.common(root, workspace)
            with self.assertRaisesRegex(
                forecast_candidates.ForecastCandidateContextUnavailableError,
                "不会隐式改读当前 Release",
            ):
                forecast_candidates.forecast_candidate_source_context(
                    7, 5, "seed_cache", **common
                )
            with self.assertRaisesRegex(ValueError, "source must"):
                forecast_candidates.forecast_candidate_source_context(
                    7, 5, "automatic", **common
                )


class ForecastPayloadTests(unittest.TestCase):
    def test_catalog_preserves_explicit_context_and_data_bounds(self) -> None:
        context = {"seed": 7, "years": 5, "source": "seed_cache"}
        rows = rows_for(7)
        catalog = {"tiers": [{"tierProfileId": "short", "naturalHorizonYears": 2}]}
        layer = SimpleNamespace(forecast_candidate_catalog=mock.Mock(return_value=catalog))
        payload = forecast_candidates.forecast_candidate_catalog_payload(
            7,
            5,
            "seed_cache",
            source_context=lambda seed, years, source: (context, rows),
            candidate_layer=layer,
            config_path=Path("forecast.json"),
            as_float=lambda value, default=0.0: float(value),
        )
        self.assertIs(context, payload["context"])
        self.assertEqual(2028, catalog["tiers"][0]["maxFullAsOfYear"])

    def test_generate_normalizes_request_and_returns_source_context(self) -> None:
        context = {"seed": 7, "years": 5, "source": "seed_cache"}
        rows = rows_for(7)
        generated = {"generatorVersion": "v2", "candidate": {"candidateId": "c1"}}
        layer = SimpleNamespace(generate_forecast_candidate=mock.Mock(return_value=generated))
        payload = forecast_candidates.generate_forecast_candidate_payload(
            {
                "seed": "7", "years": "5", "source": "seed_cache",
                "asOfYear": "2025", "tierProfileId": " tier ",
                "narrativeProfileId": " style ", "modifierIds": [" first ", 2],
                "scoreMin": "70.5", "scoreMax": 80,
            },
            source_context=lambda seed, years, source: (context, rows),
            candidate_layer=layer,
            config_path=Path("forecast.json"),
            clean_seed=int,
            clean_years=int,
        )
        self.assertEqual({"context": context, **generated}, payload)
        call = layer.generate_forecast_candidate.call_args
        self.assertIs(rows, call.args[0])
        self.assertEqual(["first", "2"], call.kwargs["modifier_ids"])
        self.assertEqual(70.5, call.kwargs["score_min"])

    def test_generate_rejects_missing_explicit_source_before_generator(self) -> None:
        layer = SimpleNamespace(
            generate_forecast_candidate=mock.Mock(side_effect=AssertionError("must not generate"))
        )
        with self.assertRaisesRegex(ValueError, "source must"):
            forecast_candidates.generate_forecast_candidate_payload(
                {"seed": 7, "years": 5, "modifierIds": []},
                source_context=mock.Mock(),
                candidate_layer=layer,
                config_path=Path("forecast.json"),
                clean_seed=int,
                clean_years=int,
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
        self.assertEqual(missing, unreadable)
        self.assertEqual("unavailable", missing["mode"])
        self.assertIsNone(missing["releaseId"])

    def test_valid_manifest_maps_only_existing_public_fields(self) -> None:
        manifest = {
            "release_id": " release-1 ", "run_id": "run-1", "variant": "baseline",
            "seed": 7, "start_year": 2025, "years": 60, "model_version": "m1",
            "output_schema_version": "o1", "generated_at": "now", "schema_version": "s1",
            "private": "ignored",
        }
        with tempfile.TemporaryDirectory() as temporary_dir:
            output_root = Path(temporary_dir)
            (output_root / "current_viewer_manifest.json").write_text("{}", encoding="utf-8")
            payload = workspace_service.current_viewer_release_status(
                output_root=output_root, read_json=lambda path: manifest
            )
        self.assertEqual("versioned_release", payload["mode"])
        self.assertEqual("release-1", payload["releaseId"])
        self.assertNotIn("private", payload)

    def test_workspace_counts_recursive_saves_and_keeps_relative_roots(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            run_root = root / "output" / "seed_explorer_runs"
            save_root = root / "saves" / "seed_explorer"
            (save_root / "a").mkdir(parents=True)
            (save_root / "b" / "nested").mkdir(parents=True)
            (save_root / "a" / "dynamic_test_save.json").write_text("{}", encoding="utf-8")
            (save_root / "b" / "nested" / "dynamic_test_save.json").write_text("{}", encoding="utf-8")
            payload = workspace_service.workspace_status(
                root_dir=root, run_root=run_root, save_root=save_root,
                service_id="service-v1", list_cached_runs=lambda: [{}, {}],
                current_viewer_release_status=lambda: {"mode": "unavailable"},
                getpid=lambda: 4321,
            )
        self.assertEqual(2, payload["cachedRunCount"])
        self.assertEqual(2, payload["saveCount"])
        self.assertEqual("output/seed_explorer_runs", payload["runRoot"])


if __name__ == "__main__":
    unittest.main()
