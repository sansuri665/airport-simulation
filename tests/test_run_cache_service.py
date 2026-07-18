from __future__ import annotations

import hashlib
import platform
import sys
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from airport_sim.server import run_cache, run_service
from airport_sim.server import app as local_ui


class RunCacheBoundaryTests(unittest.TestCase):
    def test_app_cache_path_delegates_to_run_cache_module(self) -> None:
        run_dir = Path("example")
        expected = Path("delegated-cache.json")
        with mock.patch.object(run_cache, "cache_path", return_value=expected) as delegated:
            actual = local_ui.cache_path(run_dir)

        self.assertEqual(expected, actual)
        delegated.assert_called_once_with(run_dir)

    def test_dependency_inventory_includes_all_formal_server_modules(self) -> None:
        dependencies = set(
            run_cache.dependency_files(local_ui.SERVER_DIR, local_ui.ROOT_DIR)
        )
        expected = {
            path.resolve()
            for path in local_ui.SERVER_DIR.glob("*.py")
            if path.is_file()
        }

        self.assertTrue(expected.issubset(dependencies))
        self.assertIn((local_ui.SERVER_DIR / "run_cache.py").resolve(), dependencies)
        self.assertIn((local_ui.SERVER_DIR / "run_service.py").resolve(), dependencies)

    def test_fingerprint_keeps_legacy_byte_protocol(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            dependency = root / "model.py"
            dependency.write_bytes(b"VALUE = 1\n")
            version = "cache-contract-v1"

            digest = hashlib.sha256()
            for value in (
                version,
                platform.python_implementation(),
                sys.version,
                platform.platform(),
            ):
                digest.update(value.encode("utf-8"))
                digest.update(b"\0")
            digest.update(b"model.py\0VALUE = 1\n\0")

            actual = run_cache.current_fingerprint(
                version=version,
                root_dir=root,
                dependencies=[dependency],
            )

        self.assertEqual(digest.hexdigest(), actual)

    def test_app_run_seed_preserves_compatibility_injection_points(self) -> None:
        expected = {"seed": 7, "years": 12}
        with mock.patch.object(run_service, "run_seed", return_value=expected) as delegated:
            actual = local_ui.run_seed(7, 12, False)

        self.assertEqual(expected, actual)
        delegated.assert_called_once()
        args = delegated.call_args.args
        kwargs = delegated.call_args.kwargs
        self.assertEqual((7, 12, False), args)
        self.assertIs(local_ui.load_cached, kwargs["load_cached"])
        self.assertIs(local_ui.run_orchestrator, kwargs["run_orchestrator"])
        self.assertIs(local_ui.aggregate_run, kwargs["aggregate_run"])
        self.assertIs(local_ui.prune_cached_runs, kwargs["prune_cached_runs"])


class RunServiceSequenceTests(unittest.TestCase):
    def test_cache_hit_returns_before_lock_or_model_execution(self) -> None:
        progress: list[tuple[str, str, bool | None]] = []

        def update_progress(
            run_id: str,
            seed: int,
            years: int,
            status: str,
            phase: str,
            progress_pct: int,
            message: str,
            *,
            cached: bool | None = None,
        ) -> None:
            del run_id, seed, years, status, progress_pct, message
            progress.append((phase, "updated", cached))

        def forbidden(*args: object, **kwargs: object) -> object:
            del args, kwargs
            self.fail("cache hit must not lock or execute the model")

        payload = run_service.run_seed(
            7,
            12,
            False,
            run_root=Path("runs"),
            run_id_for=lambda seed, years: f"seed_{seed}_years_{years}",
            update_task_progress=update_progress,
            load_cached=lambda run_dir: {"seed": 7, "years": 12},
            lock_for_run=forbidden,
            run_orchestrator=forbidden,
            aggregate_run=forbidden,
            save_cached=forbidden,
            prune_cached_runs=forbidden,
        )

        self.assertTrue(payload["cached"])
        self.assertEqual(0.0, payload["elapsedSec"])
        self.assertEqual(
            [("cache_check", "updated", None), ("cache_hit", "updated", True)],
            progress,
        )

    def test_cache_miss_keeps_lock_run_aggregate_save_prune_order(self) -> None:
        events: list[str] = []
        cache_reads = iter((None, None))

        @contextmanager
        def lock_for_run(run_id: str):
            events.append(f"lock:{run_id}")
            yield

        def update_progress(
            run_id: str,
            seed: int,
            years: int,
            status: str,
            phase: str,
            progress_pct: int,
            message: str,
            *,
            cached: bool | None = None,
        ) -> None:
            del run_id, seed, years, status, progress_pct, message, cached
            events.append(f"progress:{phase}")

        def load_cached(run_dir: Path) -> None:
            del run_dir
            events.append("cache-read")
            return next(cache_reads)

        def run_orchestrator(
            seed: int,
            years: int,
            run_dir: Path,
            force: bool,
        ) -> tuple[float, str]:
            del seed, years, run_dir, force
            events.append("orchestrator")
            return 1.25, "tail"

        def aggregate_run(
            run_dir: Path,
            seed: int,
            years: int,
            elapsed: float,
            cached: bool,
        ) -> dict[str, object]:
            del run_dir, seed, years, elapsed, cached
            events.append("aggregate")
            return {"seed": 7, "years": 12}

        def save_cached(run_dir: Path, payload: dict[str, object]) -> None:
            del run_dir, payload
            events.append("save")

        def prune_cached_runs() -> None:
            events.append("prune")

        payload = run_service.run_seed(
            7,
            12,
            False,
            run_root=Path("runs"),
            run_id_for=lambda seed, years: f"seed_{seed}_years_{years}",
            update_task_progress=update_progress,
            load_cached=load_cached,
            lock_for_run=lock_for_run,
            run_orchestrator=run_orchestrator,
            aggregate_run=aggregate_run,
            save_cached=save_cached,
            prune_cached_runs=prune_cached_runs,
        )

        self.assertEqual({"seed": 7, "years": 12}, payload)
        self.assertEqual(
            [
                "progress:cache_check",
                "cache-read",
                "lock:seed_7_years_12",
                "cache-read",
                "progress:model_run",
                "orchestrator",
                "progress:aggregate",
                "aggregate",
                "save",
                "prune",
                "progress:complete",
            ],
            events,
        )

    def test_orchestrator_command_preserves_seed_cache_profile(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            run_root = root / "runs"
            run_dir = run_root / "seed_7_years_12"
            command: list[str] = []
            logs: list[str] = []
            clock = iter((10.0, 12.5))

            def run_process(args: list[str], **kwargs: object) -> SimpleNamespace:
                command.extend(args)
                self.assertEqual(str(root), kwargs["cwd"])
                self.assertEqual(240, kwargs["timeout"])
                return SimpleNamespace(returncode=0, stdout="done", stderr="")

            elapsed, tail = run_service.run_orchestrator(
                7,
                12,
                run_dir,
                False,
                root_dir=root,
                run_root=run_root,
                orchestrator=root / "macro.py",
                migrate_legacy_save=lambda seed, years: None,
                ensure_inside=lambda expected_root, path: path,
                structured_log=lambda event, **fields: logs.append(event),
                executable="python-test",
                run_process=run_process,
                clock=lambda: next(clock),
            )

        self.assertEqual(2.5, elapsed)
        self.assertIn("done", tail)
        self.assertEqual("python-test", command[0])
        self.assertEqual("seed-cache", command[command.index("--artifact-profile") + 1])
        self.assertEqual("none", command[command.index("--publish-viewer") + 1])
        self.assertEqual(["orchestrator_start", "orchestrator_complete"], logs)

    def test_model_failure_updates_progress_before_reraising(self) -> None:
        phases: list[tuple[str, str, bool | None]] = []

        @contextmanager
        def lock_for_run(run_id: str):
            del run_id
            yield

        def update_progress(
            run_id: str,
            seed: int,
            years: int,
            status: str,
            phase: str,
            progress_pct: int,
            message: str,
            *,
            cached: bool | None = None,
        ) -> None:
            del run_id, seed, years, progress_pct, message
            phases.append((status, phase, cached))

        def fail_model(
            seed: int,
            years: int,
            run_dir: Path,
            force: bool,
        ) -> tuple[float, str]:
            del seed, years, run_dir, force
            raise RuntimeError("expected failure")

        with self.assertRaisesRegex(RuntimeError, "expected failure"):
            run_service.run_seed(
                7,
                12,
                False,
                run_root=Path("runs"),
                run_id_for=lambda seed, years: f"seed_{seed}_years_{years}",
                update_task_progress=update_progress,
                load_cached=lambda run_dir: None,
                lock_for_run=lock_for_run,
                run_orchestrator=fail_model,
                aggregate_run=lambda *args, **kwargs: {},
                save_cached=lambda run_dir, payload: None,
                prune_cached_runs=lambda: None,
            )

        self.assertEqual(("failed", "failed", False), phases[-1])


if __name__ == "__main__":
    unittest.main()
