from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


from airport_sim import cache_service


class CacheServiceTests(unittest.TestCase):
    def roots(self, temporary_root: Path):
        output_root = temporary_root / "output"
        run_root = output_root / "seed_explorer_runs"
        save_root = temporary_root / "saves" / "seed_explorer"
        release_root = output_root / "viewer_releases"
        return (
            mock.patch.object(cache_service, "ROOT_DIR", temporary_root),
            mock.patch.object(cache_service, "OUTPUT_ROOT", output_root),
            mock.patch.object(cache_service, "RUN_ROOT", run_root),
            mock.patch.object(cache_service, "SAVE_ROOT", save_root),
            mock.patch.object(cache_service, "VIEWER_RELEASE_ROOT", release_root),
            mock.patch.object(cache_service, "CACHE_POLICY_PATH", save_root.parent / "cache_policy.json"),
            mock.patch.object(cache_service, "LEGACY_OUTPUT_ROOT", temporary_root / "airport" / "output"),
            mock.patch.object(cache_service, "_service_state", return_value={"port": 8776, "status": "stopped"}),
            mock.patch.object(cache_service, "_current_seed_cache_fingerprint", return_value=("test-v1", "fixed")),
        )

    def test_plan_keeps_newest_two_and_never_targets_saves(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            patches = self.roots(root)
            with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6], patches[7], patches[8]:
                for index in range(4):
                    run = cache_service.RUN_ROOT / f"seed_{index}_years_60"
                    run.mkdir(parents=True)
                    (run / "data.csv").write_text("x\n1\n", encoding="utf-8")
                    (run / "seed_explorer_city_market_cache.json").write_text(
                        json.dumps({"cacheFingerprintVersion": "test-v1", "cacheFingerprint": "fixed"}),
                        encoding="utf-8",
                    )
                    run.touch()
                    run_stat_time = index + 1
                    cache_service.os.utime(run, (run_stat_time, run_stat_time))
                save = cache_service.SAVE_ROOT / "seed_0_years_60" / "dynamic_test_save.json"
                save.parent.mkdir(parents=True)
                save.write_text('{"seed": 0}', encoding="utf-8")

                plan = cache_service.plan_cache()

                seed_candidates = {
                    item["runId"]
                    for item in plan["entries"]
                    if item["category"] == "seed_cache" and item["status"] == "deletable"
                }
                self.assertEqual({"seed_0_years_60", "seed_1_years_60"}, seed_candidates)
                self.assertTrue(save.exists())
                self.assertFalse(any(item["path"].startswith("saves/") for item in plan["plan"]["candidates"]))

    def test_pin_survives_plan_and_policy_is_outside_model_config(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            patches = self.roots(root)
            with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6], patches[7], patches[8]:
                run = cache_service.RUN_ROOT / "seed_7_years_60"
                run.mkdir(parents=True)
                result = cache_service.pin_cache(run.name)
                self.assertTrue(result["pinned"])
                policy = json.loads(cache_service.CACHE_POLICY_PATH.read_text(encoding="utf-8"))
                self.assertEqual([run.name], policy["pinnedRunIds"])
                status = next(item for item in cache_service.list_cache()["entries"] if item.get("runId") == run.name)
                self.assertEqual("protected", status["status"])

    def test_retention_is_persisted_outside_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            patches = self.roots(root)
            with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6], patches[7], patches[8]:
                result = cache_service.set_retention(3)
                self.assertEqual(3, result["maxCachedRuns"])
                self.assertEqual(3, cache_service.load_policy()["maxCachedRuns"])
                self.assertTrue(cache_service.CACHE_POLICY_PATH.is_relative_to(cache_service.SAVE_ROOT.parent))
                self.assertFalse(cache_service.CACHE_POLICY_PATH.is_relative_to(cache_service.OUTPUT_ROOT))
                with self.assertRaises(ValueError):
                    cache_service.set_retention(0)

    def test_cleanup_refuses_while_8776_is_active(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            patches = self.roots(root)
            with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6]:
                candidate = cache_service.OUTPUT_ROOT / "old_smoke_output"
                candidate.mkdir(parents=True)
                with mock.patch.object(
                    cache_service,
                    "_service_state",
                    return_value={"port": 8776, "status": "running", "serviceId": cache_service.SERVICE_ID},
                ):
                    with self.assertRaisesRegex(RuntimeError, "stop the Airport service"):
                        cache_service.clean_cache(confirm=True)
                self.assertTrue(candidate.exists())

    def test_confirmed_cleanup_stays_inside_output_and_preserves_current_release(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            patches = self.roots(root)
            with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6], patches[7], patches[8]:
                current_release = cache_service.VIEWER_RELEASE_ROOT / "current"
                old_release = cache_service.VIEWER_RELEASE_ROOT / "old"
                current_release.mkdir(parents=True)
                old_release.mkdir(parents=True)
                (old_release / "bundle.js").write_text("old", encoding="utf-8")
                cache_service.OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
                (cache_service.OUTPUT_ROOT / "current_viewer_manifest.json").write_text(
                    json.dumps({"release_path": "output/viewer_releases/current"}),
                    encoding="utf-8",
                )
                save = cache_service.SAVE_ROOT / "seed_1_years_60" / "dynamic_test_save.json"
                save.parent.mkdir(parents=True)
                save.write_text("{}", encoding="utf-8")

                result = cache_service.clean_cache(confirm=True)

                self.assertTrue(result["executed"])
                self.assertTrue(current_release.exists())
                self.assertFalse(old_release.exists())
                self.assertTrue(save.exists())

    def test_path_guard_rejects_output_root_and_external_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            output = root / "output"
            output.mkdir()
            with mock.patch.object(cache_service, "OUTPUT_ROOT", output):
                with self.assertRaises(ValueError):
                    cache_service._ensure_inside(output, output)
                with self.assertRaises(ValueError):
                    cache_service._ensure_inside(output, root / "outside")

    def test_plan_is_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            patches = self.roots(root)
            with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6], patches[7], patches[8]:
                run = cache_service.RUN_ROOT / "seed_1_years_60"
                run.mkdir(parents=True)
                cache_file = run / "seed_explorer_city_market_cache.json"
                cache_file.write_text(
                    json.dumps({"cacheFingerprintVersion": "test-v1", "cacheFingerprint": "fixed"}),
                    encoding="utf-8",
                )
                before = {
                    path.relative_to(root).as_posix(): (path.stat().st_size, path.stat().st_mtime_ns)
                    for path in root.rglob("*")
                    if path.is_file()
                }

                cache_service.plan_cache()

                after = {
                    path.relative_to(root).as_posix(): (path.stat().st_size, path.stat().st_mtime_ns)
                    for path in root.rglob("*")
                    if path.is_file()
                }
                self.assertEqual(before, after)

    def test_invalid_manifest_fails_closed_for_runs_and_releases(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            patches = self.roots(root)
            with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6], patches[7], patches[8]:
                macro_run = cache_service.OUTPUT_ROOT / "macro_runs" / "old_validation"
                release = cache_service.VIEWER_RELEASE_ROOT / "old"
                macro_run.mkdir(parents=True)
                release.mkdir(parents=True)
                (cache_service.OUTPUT_ROOT / "current_viewer_manifest.json").write_text(
                    json.dumps({"release_path": "../outside"}),
                    encoding="utf-8",
                )

                inventory = cache_service.list_cache()

                protected = {
                    item["path"]
                    for item in inventory["entries"]
                    if item["status"] == "protected"
                }
                self.assertIn("output/macro_runs/old_validation", protected)
                self.assertIn("output/viewer_releases/old", protected)

    def test_cleanup_reports_one_failure_and_continues(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            patches = self.roots(root)
            with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6], patches[7], patches[8]:
                first = cache_service.OUTPUT_ROOT / "first_test"
                second = cache_service.OUTPUT_ROOT / "second_test"
                first.mkdir(parents=True)
                second.mkdir(parents=True)
                original_delete = cache_service._delete_target

                def delete_with_one_failure(path: Path) -> None:
                    if path.name == "first_test":
                        raise PermissionError("simulated lock")
                    original_delete(path)

                with mock.patch.object(cache_service, "_delete_target", side_effect=delete_with_one_failure):
                    result = cache_service.clean_cache(confirm=True)

                self.assertEqual(1, len(result["failed"]))
                self.assertTrue(first.exists())
                self.assertFalse(second.exists())

    def test_cleanup_refreshes_run_index_after_macro_run_removal(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            patches = self.roots(root)
            with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6], patches[7], patches[8]:
                macro_run = cache_service.OUTPUT_ROOT / "macro_runs" / "old_validation"
                macro_run.mkdir(parents=True)
                current_release = cache_service.VIEWER_RELEASE_ROOT / "current"
                current_release.mkdir(parents=True)
                (cache_service.OUTPUT_ROOT / "current_viewer_manifest.json").write_text(
                    json.dumps({"release_path": "output/viewer_releases/current"}),
                    encoding="utf-8",
                )
                with mock.patch.object(cache_service, "_refresh_macro_run_index", return_value={"run_count": 0}) as refresh:
                    result = cache_service.clean_cache(confirm=True)
                refresh.assert_called_once_with()
                self.assertEqual({"run_count": 0}, result["runIndex"])


if __name__ == "__main__":
    unittest.main()
