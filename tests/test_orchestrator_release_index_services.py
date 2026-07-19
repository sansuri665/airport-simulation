from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


ROOT_DIR = Path(__file__).resolve().parents[1]
MACRO_DIR = ROOT_DIR / "macro_layers"
if str(MACRO_DIR) not in sys.path:
    sys.path.insert(0, str(MACRO_DIR))

import macro_run_orchestrator_sim as orchestrator
import orchestrator_run_index as run_index_service
import orchestrator_viewer_release as viewer_release_service

from airport_sim.server import run_cache


class OrchestratorCompatibilityTests(unittest.TestCase):
    def test_bundle_surface_delegates_with_existing_mock_points(self) -> None:
        expected = {"viewer": "bundle.js"}
        variant = Path("run/baseline")
        release = Path("release")
        with mock.patch.object(
            viewer_release_service,
            "write_viewer_release_bundles",
            return_value=expected,
        ) as delegated:
            actual = orchestrator.write_viewer_release_bundles(
                variant,
                release,
                "release-1",
            )

        self.assertIs(expected, actual)
        self.assertEqual((variant, release, "release-1"), delegated.call_args.args)
        kwargs = delegated.call_args.kwargs
        self.assertIs(orchestrator.copy_tree_files, kwargs["copy_tree_files"])
        self.assertIs(
            orchestrator.write_city_market_viewer_lazy_assets,
            kwargs["write_city_market_viewer_lazy_assets"],
        )
        self.assertIs(orchestrator.build_global_viewer_bundle, kwargs["build_global_viewer_bundle"])
        self.assertIs(orchestrator.atomic_write_text_file, kwargs["atomic_write_text_file"])

    def test_publish_surface_delegates_with_existing_mock_points(self) -> None:
        expected = {"release_id": "delegated"}
        variant = Path("run/baseline")
        viewer_root = Path("output")
        with mock.patch.object(
            viewer_release_service,
            "publish_variant_to_viewer",
            return_value=expected,
        ) as delegated:
            actual = orchestrator.publish_variant_to_viewer(variant, viewer_root)

        self.assertIs(expected, actual)
        self.assertEqual((variant, viewer_root), delegated.call_args.args)
        kwargs = delegated.call_args.kwargs
        self.assertIs(orchestrator.time, kwargs["time_module"])
        self.assertIs(orchestrator.clean_run_id, kwargs["clean_run_id"])
        self.assertIs(
            orchestrator.write_viewer_release_bundles,
            kwargs["write_viewer_release_bundles"],
        )
        self.assertIs(
            orchestrator.sync_variant_downstream_csv,
            kwargs["sync_variant_downstream_csv"],
        )
        self.assertIs(orchestrator.write_json_file, kwargs["write_json_file"])
        self.assertIs(orchestrator.atomic_write_text_file, kwargs["atomic_write_text_file"])

    def test_run_index_surfaces_delegate_with_existing_mock_points(self) -> None:
        output_root = Path("runs")
        build_expected = {"runs": []}
        write_expected = {"run_count": 0}
        with mock.patch.object(
            run_index_service,
            "variant_label",
            return_value="delegated label",
        ) as label, mock.patch.object(
            run_index_service,
            "build_run_index",
            return_value=build_expected,
        ) as build, mock.patch.object(
            run_index_service,
            "write_run_index",
            return_value=write_expected,
        ) as write:
            self.assertEqual("delegated label", orchestrator.variant_label("baseline", {}))
            self.assertIs(build_expected, orchestrator.build_run_index(output_root))
            self.assertIs(write_expected, orchestrator.write_run_index(output_root))

        label.assert_called_once_with("baseline", {})
        self.assertIs(orchestrator.read_json_file, build.call_args.kwargs["read_json_file"])
        self.assertIs(orchestrator.variant_label, build.call_args.kwargs["variant_label"])
        self.assertIs(orchestrator.build_run_index, write.call_args.kwargs["build_run_index"])
        self.assertIs(orchestrator.write_json_file, write.call_args.kwargs["write_json_file"])

    def test_new_macro_services_are_seed_cache_dependencies(self) -> None:
        names = {
            path.name
            for path in run_cache.dependency_files(
                ROOT_DIR / "airport_sim" / "server",
                ROOT_DIR,
            )
        }

        self.assertIn("orchestrator_viewer_release.py", names)
        self.assertIn("orchestrator_run_index.py", names)


class ViewerReleaseLifecycleTests(unittest.TestCase):
    def test_release_sequence_and_manifest_protocol_are_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir).resolve()
            variant = root / "output" / "macro_runs" / "run_1" / "baseline"
            variant.mkdir(parents=True)
            viewer_root = root / "output"
            events: list[str] = []
            captured_manifest: dict[str, object] = {}
            fake_time = SimpleNamespace(
                strftime=mock.Mock(
                    side_effect=["20260718_123456", "2026-07-18 12:34:56"]
                ),
                time_ns=mock.Mock(return_value=123),
            )

            def write_bundles(source: Path, staging: Path, release_id: str) -> dict[str, str]:
                events.append("bundles")
                self.assertTrue(source.samefile(variant))
                self.assertTrue(staging.name.startswith(".staging_"))
                (staging / "global.js").write_text("global", encoding="utf-8")
                (staging / "city.json").write_text("city", encoding="utf-8")
                return {"global": "global.js", "city": "city.json"}

            def hash_file(path: Path) -> str:
                events.append(f"hash:{path.name}")
                return f"hash-{path.name}"

            def gzip_sidecars(staging: Path) -> dict[str, int]:
                events.append("gzip")
                self.assertTrue((staging / "global.js").is_file())
                return {"gzip_file_count": 2, "gzip_raw_bytes": 10, "gzip_bytes": 4}

            def replace(source: Path, target: Path) -> None:
                events.append("formalize")
                source.rename(target)

            def sync_downstream(source: Path, target: Path) -> list[str]:
                events.append("downstream")
                release = target / "viewer_releases" / "run_1_baseline_20260718_123456_000000123"
                self.assertTrue(release.is_dir())
                return ["downstream-a", "downstream-b"]

            def write_json(path: Path, payload: dict[str, object]) -> None:
                events.append("manifest-json")
                captured_manifest.update(payload)
                path.write_text(json.dumps(payload), encoding="utf-8")

            def write_text(path: Path, content: str, encoding: str = "utf-8") -> None:
                events.append("manifest-js")
                path.write_text(content, encoding=encoding)

            result = viewer_release_service.publish_variant_to_viewer(
                variant,
                viewer_root,
                time_module=fake_time,
                clean_run_id=lambda value: value,
                write_viewer_release_bundles=write_bundles,
                sha256_file=hash_file,
                write_viewer_release_gzip_sidecars=gzip_sidecars,
                replace_directory_with_retry=replace,
                sync_variant_downstream_csv=sync_downstream,
                manifest_version="manifest-v1",
                viewer_run_metadata=lambda path: {
                    "seed": 7,
                    "start_year": 2025,
                    "years": 60,
                    "model_version": "model-v1",
                    "output_schema_version": "output-v1",
                },
                airport_relative=lambda path: path.relative_to(root).as_posix(),
                viewer_script_url=lambda path: f"./{path.relative_to(root).as_posix()}",
                write_json_file=write_json,
                atomic_write_text_file=write_text,
                remove_tree=lambda path: self.fail("successful publish must not clean staging"),
            )

        self.assertEqual(
            [
                "bundles",
                "hash:global.js",
                "hash:city.json",
                "gzip",
                "formalize",
                "downstream",
                "manifest-json",
                "manifest-js",
            ],
            events,
        )
        self.assertEqual("run_1_baseline_20260718_123456_000000123", result["release_id"])
        self.assertEqual("manifest-v1", captured_manifest["schema_version"])
        self.assertEqual("run_1", captured_manifest["run_id"])
        self.assertEqual("baseline", captured_manifest["variant"])
        self.assertEqual(
            {"global": "hash-global.js", "city": "hash-city.json"},
            captured_manifest["bundle_sha256"],
        )
        self.assertEqual(2, captured_manifest["downstream_csv_copy_count"])
        self.assertEqual(2, result["downstream_csv_files"])
        self.assertEqual(2, result["bundle_count"])

    def test_compression_failure_removes_only_staging_before_formalization(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            variant = root / "run" / "baseline"
            variant.mkdir(parents=True)
            viewer_root = root / "viewer"
            removed: list[Path] = []
            fake_time = SimpleNamespace(
                strftime=mock.Mock(return_value="20260718_123456"),
                time_ns=mock.Mock(return_value=1),
            )

            def write_bundles(source: Path, staging: Path, release_id: str) -> dict[str, str]:
                (staging / "bundle.js").write_text("bundle", encoding="utf-8")
                return {"viewer": "bundle.js"}

            def remove_tree(path: Path) -> None:
                removed.append(path)
                for child in path.iterdir():
                    child.unlink()
                path.rmdir()

            with self.assertRaisesRegex(OSError, "compression failed"):
                viewer_release_service.publish_variant_to_viewer(
                    variant,
                    viewer_root,
                    time_module=fake_time,
                    clean_run_id=lambda value: value,
                    write_viewer_release_bundles=write_bundles,
                    sha256_file=lambda path: "hash",
                    write_viewer_release_gzip_sidecars=mock.Mock(
                        side_effect=OSError("compression failed")
                    ),
                    replace_directory_with_retry=mock.Mock(),
                    sync_variant_downstream_csv=mock.Mock(),
                    manifest_version="v1",
                    viewer_run_metadata=mock.Mock(),
                    airport_relative=lambda path: str(path),
                    viewer_script_url=lambda path: str(path),
                    write_json_file=mock.Mock(),
                    atomic_write_text_file=mock.Mock(),
                    remove_tree=remove_tree,
                )

            release_root = viewer_root / "viewer_releases"
            self.assertEqual(1, len(removed))
            self.assertTrue(removed[0].name.startswith(".staging_"))
            self.assertFalse(any(release_root.iterdir()))

    def test_downstream_csv_failure_leaves_formal_release_but_not_manifest_pointers(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            variant = root / "run" / "baseline"
            variant.mkdir(parents=True)
            viewer_root = root / "viewer"
            viewer_root.mkdir()
            old_json = viewer_root / "current_viewer_manifest.json"
            old_js = viewer_root / "current_viewer_manifest.js"
            old_json.write_text('{"old":true}', encoding="utf-8")
            old_js.write_text("window.OLD = true;\n", encoding="utf-8")
            fake_time = SimpleNamespace(
                strftime=mock.Mock(return_value="20260718_123456"),
                time_ns=mock.Mock(return_value=2),
            )

            def write_bundles(source: Path, staging: Path, release_id: str) -> dict[str, str]:
                (staging / "bundle.js").write_text("bundle", encoding="utf-8")
                return {"viewer": "bundle.js"}

            with self.assertRaisesRegex(RuntimeError, "copy failed"):
                viewer_release_service.publish_variant_to_viewer(
                    variant,
                    viewer_root,
                    time_module=fake_time,
                    clean_run_id=lambda value: value,
                    write_viewer_release_bundles=write_bundles,
                    sha256_file=lambda path: "hash",
                    write_viewer_release_gzip_sidecars=lambda path: {
                        "gzip_file_count": 0,
                        "gzip_raw_bytes": 0,
                        "gzip_bytes": 0,
                    },
                    replace_directory_with_retry=lambda source, target: source.rename(target),
                    sync_variant_downstream_csv=mock.Mock(
                        side_effect=RuntimeError("copy failed")
                    ),
                    manifest_version="v1",
                    viewer_run_metadata=mock.Mock(),
                    airport_relative=lambda path: str(path),
                    viewer_script_url=lambda path: str(path),
                    write_json_file=mock.Mock(),
                    atomic_write_text_file=mock.Mock(),
                    remove_tree=mock.Mock(),
                )

            releases = list((viewer_root / "viewer_releases").iterdir())
            self.assertEqual(1, len(releases))
            self.assertFalse(releases[0].name.startswith(".staging_"))
            self.assertEqual('{"old":true}', old_json.read_text(encoding="utf-8"))
            self.assertEqual("window.OLD = true;\n", old_js.read_text(encoding="utf-8"))

    def test_missing_source_and_duplicate_release_fail_before_staging(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            viewer_root = root / "viewer"
            common = {
                "time_module": SimpleNamespace(
                    strftime=mock.Mock(return_value="20260718_123456"),
                    time_ns=mock.Mock(return_value=3),
                ),
                "clean_run_id": lambda value: value,
                "write_viewer_release_bundles": mock.Mock(),
                "sha256_file": mock.Mock(),
                "write_viewer_release_gzip_sidecars": mock.Mock(),
                "replace_directory_with_retry": mock.Mock(),
                "sync_variant_downstream_csv": mock.Mock(),
                "manifest_version": "v1",
                "viewer_run_metadata": mock.Mock(),
                "airport_relative": lambda path: str(path),
                "viewer_script_url": lambda path: str(path),
                "write_json_file": mock.Mock(),
                "atomic_write_text_file": mock.Mock(),
                "remove_tree": mock.Mock(),
            }
            with self.assertRaisesRegex(FileNotFoundError, "missing Viewer source variant"):
                viewer_release_service.publish_variant_to_viewer(
                    root / "missing" / "baseline",
                    viewer_root,
                    **common,
                )

            variant = root / "run" / "baseline"
            variant.mkdir(parents=True)
            release_id = "run_baseline_20260718_123456_000000003"
            (viewer_root / "viewer_releases" / release_id).mkdir(parents=True)
            with self.assertRaisesRegex(FileExistsError, "Viewer release already exists"):
                viewer_release_service.publish_variant_to_viewer(
                    variant,
                    viewer_root,
                    **common,
                )


class RunIndexServiceTests(unittest.TestCase):
    def test_variant_labels_keep_baseline_scenario_and_fallback_rules(self) -> None:
        self.assertEqual("Baseline", run_index_service.variant_label("baseline", {}))
        probabilistic = {
            "scenario": {
                "state": "probabilistic",
                "selected_events": [{}, {}],
            }
        }
        self.assertEqual(
            "概率历史岔路: 2 events",
            run_index_service.variant_label("probabilistic", probabilistic),
        )
        occurred = {
            "scenario": {
                "state": "occurred",
                "selected": {
                    "trigger_year": 2030,
                    "risk": {"id": "oil_shock", "label": "油价冲击"},
                },
            }
        }
        self.assertEqual(
            "发生: 油价冲击 2030",
            run_index_service.variant_label("occurred_oil_shock", occurred),
        )
        self.assertEqual("custom branch", run_index_service.variant_label("custom_branch", {}))

    def test_build_index_sorts_by_manifest_mtime_and_filters_invalid_entries(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            output_root = root / "macro_runs"
            manifests: dict[Path, dict[str, object]] = {}

            def add_run(name: str, mtime: int, manifest: dict[str, object]) -> Path:
                run_dir = output_root / name
                manifest_path = run_dir / "manifest.json"
                manifest_path.parent.mkdir(parents=True)
                manifest_path.write_text("{}", encoding="utf-8")
                os.utime(manifest_path, (mtime, mtime))
                manifests[manifest_path] = manifest
                return run_dir

            older = add_run(
                "older",
                100,
                {
                    "run_id": "older-id",
                    "seed": 1,
                    "variants": {
                        "baseline": {"global_rows": 10},
                        "missing": {"global_rows": 99},
                    },
                },
            )
            (older / "baseline").mkdir()
            newer = add_run(
                "newer",
                200,
                {
                    "seed": 2,
                    "start_year": 2025,
                    "years": 60,
                    "feedback_iterations": 3,
                    "variants": {"custom_branch": "legacy-meta"},
                    "scenario": {"state": "none"},
                    "published": {"variant": "custom_branch"},
                },
            )
            (newer / "custom_branch").mkdir()
            staging = add_run(
                ".staging_interrupted",
                300,
                {"variants": {"baseline": {"global_rows": 1}}},
            )
            (staging / "baseline").mkdir()
            invalid = add_run("invalid", 250, {})
            manifests.pop(invalid / "manifest.json")

            def read_manifest(path: Path) -> dict[str, object]:
                if path.parent.name == "invalid":
                    raise OSError("broken")
                return manifests[path]

            payload = run_index_service.build_run_index(
                output_root,
                version="index-v1",
                time_module=SimpleNamespace(strftime=lambda value: "2026-07-18 12:34:56"),
                read_json_file=read_manifest,
                variant_label=run_index_service.variant_label,
                airport_relative=lambda path: path.relative_to(root).as_posix(),
            )

        self.assertEqual("index-v1", payload["version"])
        self.assertEqual("2026-07-18 12:34:56", payload["generated_at"])
        self.assertEqual(["newer", "older-id"], [run["id"] for run in payload["runs"]])
        self.assertEqual(["custom_branch"], [item["id"] for item in payload["runs"][0]["variants"]])
        self.assertEqual(0, payload["runs"][0]["variants"][0]["global_rows"])
        self.assertEqual(["baseline"], [item["id"] for item in payload["runs"][1]["variants"]])
        self.assertEqual(10, payload["runs"][1]["variants"][0]["global_rows"])
        self.assertEqual("macro_runs/newer", payload["runs"][0]["path"])

    def test_write_index_writes_machine_readable_json_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            output_root = Path(temporary_dir) / "macro_runs"
            events: list[tuple[str, Path, object]] = []
            payload = {
                "version": "index-v1",
                "generated_at": "now",
                "runs": [{"id": "运行一"}],
            }

            result = run_index_service.write_run_index(
                output_root,
                build_run_index=lambda root: payload,
                write_json_file=lambda path, value: events.append(("json", path, value)),
                airport_relative=lambda path: path.relative_to(output_root.parent).as_posix(),
            )

        self.assertEqual(["json"], [event[0] for event in events])
        self.assertIs(payload, events[0][2])
        self.assertEqual(
            {
                "index_json": "macro_runs/macro_run_index.json",
                "run_count": 1,
            },
            result,
        )


if __name__ == "__main__":
    unittest.main()
