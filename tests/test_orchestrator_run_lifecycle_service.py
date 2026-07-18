from __future__ import annotations

import argparse
import shutil
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
from airport_sim.server import run_cache
from orchestrator_run_lifecycle import RunLifecycleDependencies, execute_run


def run_args(output_root: Path, **overrides: object) -> argparse.Namespace:
    values: dict[str, object] = {
        "output_root": output_root,
        "viewer_output_root": output_root.parent / "viewer",
        "index_only": False,
        "seed": 7,
        "run_id": None,
        "publish_viewer": "none",
        "artifact_profile": "full",
    }
    values.update(overrides)
    return argparse.Namespace(**values)


def dependencies(**overrides: object) -> RunLifecycleDependencies:
    values: dict[str, object] = {
        "time_module": SimpleNamespace(
            strftime=mock.Mock(return_value="20260718_123456"),
            time_ns=mock.Mock(return_value=26),
        ),
        "process_id": mock.Mock(return_value=123),
        "resolve_path": mock.Mock(side_effect=lambda path: path.resolve()),
        "resolve_seed": mock.Mock(return_value=7),
        "clean_run_id": mock.Mock(return_value="fixed_run"),
        "write_run_index": mock.Mock(return_value={"run_count": 1}),
        "build_run_in_directory": mock.Mock(return_value={"run_id": "fixed_run"}),
        "requested_publish_variant": mock.Mock(return_value=None),
        "write_validated_run_manifest": mock.Mock(),
        "replace_directory_with_retry": mock.Mock(
            side_effect=lambda source, target: source.rename(target)
        ),
        "remove_tree": mock.Mock(side_effect=shutil.rmtree),
        "publish_variant_to_viewer": mock.Mock(return_value={"release_id": "release-1"}),
        "write_json_file": mock.Mock(),
    }
    values.update(overrides)
    return RunLifecycleDependencies(**values)


class RunLifecycleServiceTests(unittest.TestCase):
    def test_lifecycle_module_is_a_seed_cache_dependency(self) -> None:
        names = {
            path.name
            for path in run_cache.dependency_files(
                ROOT_DIR / "airport_sim" / "server",
                ROOT_DIR,
            )
        }

        self.assertIn("orchestrator_run_lifecycle.py", names)

    def test_orchestrator_wrapper_injects_legacy_mock_points(self) -> None:
        args = run_args(Path("output"))
        sentinel = {"result": "delegated"}

        with mock.patch.object(
            orchestrator.run_lifecycle_service,
            "execute_run",
            return_value=sentinel,
        ) as delegated:
            result = orchestrator.execute_run(args)

        self.assertIs(sentinel, result)
        delegated.assert_called_once()
        call_args, call_kwargs = delegated.call_args
        self.assertEqual((args,), call_args)
        injected = call_kwargs["dependencies"]
        self.assertIs(orchestrator.time, injected.time_module)
        self.assertIs(orchestrator.os.getpid, injected.process_id)
        self.assertIs(orchestrator.resolve_seed, injected.resolve_seed)
        self.assertIs(orchestrator.clean_run_id, injected.clean_run_id)
        self.assertIs(orchestrator.write_run_index, injected.write_run_index)
        self.assertIs(orchestrator.build_run_in_directory, injected.build_run_in_directory)
        self.assertIs(orchestrator.requested_publish_variant, injected.requested_publish_variant)
        self.assertIs(orchestrator.write_validated_run_manifest, injected.write_validated_run_manifest)
        self.assertIs(orchestrator.replace_directory_with_retry, injected.replace_directory_with_retry)
        self.assertIs(orchestrator.shutil.rmtree, injected.remove_tree)
        self.assertIs(orchestrator.publish_variant_to_viewer, injected.publish_variant_to_viewer)
        self.assertIs(orchestrator.write_json_file, injected.write_json_file)

    def test_invalid_profile_and_publish_rejects_before_index_seed_or_output_creation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            output_root = Path(temporary_dir) / "missing" / "runs"
            deps = dependencies()

            with self.assertRaisesRegex(ValueError, "seed-cache cannot be combined"):
                execute_run(
                    run_args(
                        output_root,
                        artifact_profile="seed-cache",
                        publish_viewer="baseline",
                        index_only=True,
                    ),
                    dependencies=deps,
                )

            self.assertFalse(output_root.exists())
            deps.write_run_index.assert_not_called()
            deps.resolve_seed.assert_not_called()

    def test_index_only_resolves_root_and_short_circuits_without_creating_it(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            output_root = Path(temporary_dir) / "missing" / ".." / "runs"
            deps = dependencies(write_run_index=mock.Mock(return_value={"runs": []}))

            result = execute_run(run_args(output_root, index_only=True), dependencies=deps)

            self.assertEqual({"runs": []}, result)
            deps.write_run_index.assert_called_once_with(output_root.resolve())
            deps.resolve_seed.assert_not_called()
            self.assertFalse(output_root.resolve().exists())

    def test_success_without_publish_preserves_naming_order_and_return_identity(self) -> None:
        events: list[tuple[object, ...]] = []
        manifest = {"run_id": "fixed_run"}

        def build(
            args: argparse.Namespace,
            seed: int,
            run_id: str,
            staging: Path,
            final: Path,
        ) -> dict[str, object]:
            self.assertTrue(staging.is_dir())
            events.append(("build", seed, run_id, staging.name, final.name))
            return manifest

        def replace(staging: Path, final: Path) -> None:
            events.append(("replace", staging.name, final.name))
            staging.rename(final)

        with tempfile.TemporaryDirectory() as temporary_dir:
            output_root = Path(temporary_dir) / "nested" / ".." / "runs"
            deps = dependencies(
                resolve_seed=mock.Mock(side_effect=lambda args: events.append(("seed",)) or 7),
                clean_run_id=mock.Mock(
                    side_effect=lambda value: events.append(("clean", value)) or "fixed_run"
                ),
                build_run_in_directory=mock.Mock(side_effect=build),
                requested_publish_variant=mock.Mock(
                    side_effect=lambda args, value: events.append(("requested", value)) or None
                ),
                write_validated_run_manifest=mock.Mock(
                    side_effect=lambda directory, value: events.append(("validate", directory.name, value))
                ),
                replace_directory_with_retry=mock.Mock(side_effect=replace),
                write_run_index=mock.Mock(
                    side_effect=lambda root: events.append(("index", root)) or {"run_count": 1}
                ),
                write_json_file=mock.Mock(
                    side_effect=lambda path, value: events.append(("json", path.name, dict(value)))
                ),
            )

            result = execute_run(run_args(output_root), dependencies=deps)

            self.assertIs(manifest, result)
            self.assertEqual({"run_count": 1}, manifest["run_index"])
            self.assertTrue((output_root.resolve() / "fixed_run").is_dir())
            self.assertEqual(
                ["seed", "clean", "build", "requested", "validate", "replace", "index", "json"],
                [event[0] for event in events],
            )
            self.assertEqual("run_20260718_123456_seed_7", events[1][1])
            self.assertEqual(("build", 7, "fixed_run", ".staging_123_1a", "fixed_run"), events[2])
            deps.write_json_file.assert_called_once()

    def test_explicit_run_id_is_cleaned_but_timestamp_is_still_read(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            time_module = SimpleNamespace(
                strftime=mock.Mock(return_value="unused"),
                time_ns=mock.Mock(return_value=26),
            )
            deps = dependencies(time_module=time_module)

            execute_run(
                run_args(Path(temporary_dir) / "runs", run_id=" Raw Run "),
                dependencies=deps,
            )

            time_module.strftime.assert_called_once_with("%Y%m%d_%H%M%S")
            deps.clean_run_id.assert_called_once_with(" Raw Run ")

    def test_duplicate_run_is_rejected_after_root_creation_before_staging(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            output_root = Path(temporary_dir) / "runs"
            (output_root / "fixed_run").mkdir(parents=True)
            deps = dependencies()

            with self.assertRaisesRegex(FileExistsError, "will not be overwritten"):
                execute_run(run_args(output_root), dependencies=deps)

            self.assertTrue(output_root.is_dir())
            deps.resolve_seed.assert_called_once()
            deps.clean_run_id.assert_called_once()
            deps.build_run_in_directory.assert_not_called()
            deps.remove_tree.assert_not_called()

    def test_failure_after_staging_creation_removes_only_staging_and_reraises(self) -> None:
        for failing_dependency in (
            "build_run_in_directory",
            "requested_publish_variant",
            "write_validated_run_manifest",
            "replace_directory_with_retry",
        ):
            with self.subTest(failing_dependency=failing_dependency):
                with tempfile.TemporaryDirectory() as temporary_dir:
                    output_root = Path(temporary_dir) / "runs"
                    failure = mock.Mock(side_effect=RuntimeError(failing_dependency))
                    deps = dependencies(**{failing_dependency: failure})

                    with self.assertRaisesRegex(RuntimeError, failing_dependency):
                        execute_run(run_args(output_root), dependencies=deps)

                    self.assertFalse(any(output_root.iterdir()))
                    deps.remove_tree.assert_called_once()
                    deps.publish_variant_to_viewer.assert_not_called()
                    deps.write_run_index.assert_not_called()

    def test_cleanup_guard_does_not_remove_when_resolved_parent_is_outside_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            output_root = Path(temporary_dir) / "runs"
            outside = Path(temporary_dir) / "outside"
            resolver = mock.Mock(side_effect=[output_root.resolve(), outside.resolve()])
            deps = dependencies(
                resolve_path=resolver,
                build_run_in_directory=mock.Mock(side_effect=RuntimeError("failure")),
            )

            with self.assertRaisesRegex(RuntimeError, "failure"):
                execute_run(run_args(output_root), dependencies=deps)

            deps.remove_tree.assert_not_called()
            self.assertTrue((output_root / ".staging_123_1a").is_dir())

    def test_publish_occurs_after_replace_then_manifest_is_written_before_and_after_index(self) -> None:
        events: list[tuple[object, ...]] = []
        manifest: dict[str, object] = {"run_id": "fixed_run"}

        def replace(staging: Path, final: Path) -> None:
            events.append(("replace",))
            staging.rename(final)

        def publish(variant: Path, viewer: Path) -> dict[str, object]:
            self.assertTrue(variant.parent.is_dir())
            events.append(("publish", variant, viewer))
            return {"release_id": "release-1"}

        def write_json(path: Path, value: dict[str, object]) -> None:
            events.append(("json", path, dict(value)))

        with tempfile.TemporaryDirectory() as temporary_dir:
            output_root = Path(temporary_dir) / "runs"
            viewer_root = Path(temporary_dir) / "viewer"
            deps = dependencies(
                build_run_in_directory=mock.Mock(return_value=manifest),
                requested_publish_variant=mock.Mock(return_value="baseline"),
                replace_directory_with_retry=mock.Mock(side_effect=replace),
                publish_variant_to_viewer=mock.Mock(side_effect=publish),
                write_run_index=mock.Mock(
                    side_effect=lambda root: events.append(("index", root)) or {"run_count": 1}
                ),
                write_json_file=mock.Mock(side_effect=write_json),
            )

            result = execute_run(
                run_args(output_root, publish_viewer="baseline", viewer_output_root=viewer_root),
                dependencies=deps,
            )

            self.assertIs(manifest, result)
            self.assertEqual(["replace", "publish", "json", "index", "json"], [e[0] for e in events])
            self.assertEqual(output_root.resolve() / "fixed_run" / "baseline", events[1][1])
            self.assertEqual(viewer_root, events[1][2])
            self.assertNotIn("run_index", events[2][2])
            self.assertEqual({"run_count": 1}, events[4][2]["run_index"])
            self.assertEqual(
                {"variant": "baseline", "release_id": "release-1"},
                manifest["published"],
            )


if __name__ == "__main__":
    unittest.main()
