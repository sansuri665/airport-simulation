from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from airport_sim.server import seed_workspace
from airport_sim.server import app as local_ui
from airport_sim.server import storage


def release_status(seed: int = 9, years: int = 12) -> dict[str, object]:
    return {
        "mode": "versioned_release",
        "releaseId": "release-1",
        "runId": "formal-run-1",
        "variant": "baseline",
        "seed": seed,
        "startYear": 2025,
        "years": years,
        "modelVersion": "m1",
        "outputSchemaVersion": "o1",
        "generatedAt": "2026-07-19 10:00:00",
        "schemaVersion": "airport-viewer-release-manifest-v2",
    }


def unavailable_release() -> dict[str, object]:
    return {
        "mode": "unavailable",
        "releaseId": None,
        "runId": None,
        "variant": None,
        "seed": None,
        "startYear": None,
        "years": None,
        "modelVersion": None,
        "outputSchemaVersion": None,
        "generatedAt": None,
        "schemaVersion": None,
    }


class SeedWorkspaceServiceTests(unittest.TestCase):
    def roots(self, root: Path) -> tuple[Path, Path, Path]:
        return (
            root / "output" / "seed_explorer_runs",
            root / "saves" / "seed_explorer",
            root / "saves" / "seed_workspace.json",
        )

    def cache_entry(
        self,
        run_root: Path,
        seed: int,
        years: int,
        *,
        status: str = "valid",
        modified: float = 10.0,
        operations: bool = True,
    ) -> dict[str, object]:
        run_id = local_ui.run_id_for(seed, years)
        run_dir = run_root / run_id
        run_dir.mkdir(parents=True)
        (run_dir / "data.csv").write_text("value\n1\n", encoding="utf-8")
        os.utime(run_dir, (modified, modified))
        return {
            "runId": run_id,
            "seed": seed,
            "years": years,
            "cityCount": 47,
            "startYear": 2025,
            "finalYear": 2036,
            "generatedAt": "2026-07-19 09:00:00",
            "lastWriteTime": "2026-07-19 09:00:00",
            "hasCityCache": status == "valid",
            "cacheStatus": status,
            "hasBeijingOperations": operations,
        }

    def write_save(self, save_root: Path, seed: int, years: int, *, modified: float) -> Path:
        path = save_root / local_ui.run_id_for(seed, years) / "dynamic_test_save.json"
        path.parent.mkdir(parents=True)
        path.write_text(
            json.dumps(
                {
                    "seed": seed,
                    "years": years,
                    "runId": local_ui.run_id_for(seed, years),
                    "savedAt": "2026-07-19 08:00:00",
                }
            ),
            encoding="utf-8",
        )
        os.utime(path, (modified, modified))
        return path

    def payload(
        self,
        root: Path,
        *,
        cached_runs: list[dict[str, object]] | None = None,
        release: dict[str, object] | None = None,
        policy: dict[str, object] | None = None,
    ) -> dict[str, object]:
        run_root, save_root, registry_path = self.roots(root)
        return seed_workspace.seed_workspace_payload(
            root_dir=root,
            run_root=run_root,
            save_root=save_root,
            registry_path=registry_path,
            read_json=storage.read_json,
            list_cached_runs=lambda: list(cached_runs or []),
            current_viewer_release_status=lambda: release or unavailable_release(),
            cache_retention_policy=lambda: policy
            or {"maxCachedRuns": 2, "pinnedRunIds": []},
            parse_run_id=local_ui.parse_run_id,
            run_id_for=local_ui.run_id_for,
        )

    def test_read_only_discovery_deduplicates_cache_save_and_release_slots(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            run_root, save_root, registry_path = self.roots(root)
            cache = self.cache_entry(run_root, 7, 12, modified=30)
            save_with_cache = self.write_save(save_root, 7, 12, modified=20)
            save_only = self.write_save(save_root, 8, 12, modified=10)
            before_save_bytes = (save_with_cache.read_bytes(), save_only.read_bytes())

            payload = self.payload(
                root,
                cached_runs=[cache],
                release=release_status(9, 12),
                policy={"maxCachedRuns": 2, "pinnedRunIds": ["seed_7_years_12"]},
            )

            self.assertFalse(registry_path.exists())
            self.assertEqual(before_save_bytes, (save_with_cache.read_bytes(), save_only.read_bytes()))
            self.assertEqual(3, payload["counts"]["slotCount"])
            self.assertEqual(2, payload["counts"]["playerSaveCount"])
            self.assertEqual("seed_7_years_12", payload["activeSlotId"])
            self.assertEqual("newest_ready_cache", payload["activeSelectionSource"])

            slots = {slot["slotId"]: slot for slot in payload["slots"]}
            combined = slots["seed_7_years_12"]
            self.assertEqual(["seed_cache", "player_save"], combined["discoveredFrom"])
            self.assertEqual("ready", combined["cacheStatus"])
            self.assertTrue(combined["hasPlayerSave"])
            self.assertTrue(combined["canOpenOperations"])
            self.assertTrue(combined["canOpenGlobal"])
            self.assertTrue(combined["canOpenCityMarkets"])
            self.assertEqual("seed_cache", combined["viewerSource"])
            self.assertIn("pinned_cache", combined["protectedReasons"])
            self.assertGreater(combined["cacheBytes"], 0)
            self.assertEqual(1, combined["cacheFileCount"])

            published = slots["seed_9_years_12"]
            self.assertEqual("published", published["status"])
            self.assertTrue(published["canOpenGlobal"])
            self.assertTrue(published["canOpenCityMarkets"])
            self.assertTrue(published["canOpenForecastAudit"])
            self.assertEqual("viewer_release", published["viewerSource"])

            orphan = slots["seed_8_years_12"]
            self.assertEqual("save_only", orphan["status"])
            self.assertEqual("missing", orphan["cacheStatus"])

    def test_persisted_active_slot_wins_and_is_stable_across_reads(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            run_root, _, registry_path = self.roots(root)
            cache = self.cache_entry(run_root, 7, 12, modified=30)
            registry_path.parent.mkdir(parents=True)
            registry_path.write_text(
                json.dumps(
                    {
                        "schemaVersion": seed_workspace.REGISTRY_SCHEMA_VERSION,
                        "revision": 5,
                        "activeSlotId": "seed_10_years_12",
                        "slots": [
                            {
                                "slotId": "seed_10_years_12",
                                "seed": 10,
                                "years": 12,
                                "label": "手工槽位",
                                "createdAt": "2026-07-18T00:00:00Z",
                                "lastUsedAt": "2026-07-19T00:00:00Z",
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            original = registry_path.read_bytes()

            first = self.payload(root, cached_runs=[cache], release=release_status())
            second = self.payload(root, cached_runs=[cache], release=release_status())

            self.assertEqual("seed_10_years_12", first["activeSlotId"])
            self.assertEqual("registry", first["activeSelectionSource"])
            self.assertEqual(5, first["workspaceRevision"])
            self.assertEqual(first, second)
            self.assertEqual(original, registry_path.read_bytes())
            active = next(slot for slot in first["slots"] if slot["isActive"])
            self.assertEqual("手工槽位", active["label"])
            self.assertEqual("draft", active["status"])

    def test_invalid_registry_is_never_overwritten_and_discovery_still_works(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            _, save_root, registry_path = self.roots(root)
            self.write_save(save_root, 8, 12, modified=10)
            registry_path.parent.mkdir(parents=True, exist_ok=True)
            registry_path.write_text("{broken", encoding="utf-8")
            original = registry_path.read_bytes()

            payload = self.payload(root)
            result = seed_workspace.initialise_registry_if_missing(
                payload,
                registry_path=registry_path,
                read_json=storage.read_json,
                atomic_write_text=storage.atomic_write_text,
                parse_run_id=local_ui.parse_run_id,
                run_id_for=local_ui.run_id_for,
                clock=lambda: 100.0,
            )

            self.assertEqual("invalid", payload["registry"]["status"])
            self.assertEqual("seed_8_years_12", payload["activeSlotId"])
            self.assertEqual("newest_player_save", payload["activeSelectionSource"])
            self.assertFalse(result["created"])
            self.assertEqual("invalid", result["status"])
            self.assertEqual(original, registry_path.read_bytes())

    def test_missing_registry_initialises_once_and_persists_active_slot(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            run_root, _, registry_path = self.roots(root)
            cache = self.cache_entry(run_root, 7, 12, modified=30)
            workspace = self.payload(root, cached_runs=[cache], release=release_status())

            first = seed_workspace.initialise_registry_if_missing(
                workspace,
                registry_path=registry_path,
                read_json=storage.read_json,
                atomic_write_text=storage.atomic_write_text,
                parse_run_id=local_ui.parse_run_id,
                run_id_for=local_ui.run_id_for,
                clock=lambda: 100.0,
            )
            original = registry_path.read_bytes()
            second = seed_workspace.initialise_registry_if_missing(
                workspace,
                registry_path=registry_path,
                read_json=storage.read_json,
                atomic_write_text=storage.atomic_write_text,
                parse_run_id=local_ui.parse_run_id,
                run_id_for=local_ui.run_id_for,
                clock=lambda: 200.0,
            )
            reloaded = self.payload(root, cached_runs=[cache], release=release_status())

            self.assertTrue(first["created"])
            self.assertFalse(second["created"])
            self.assertEqual(original, registry_path.read_bytes())
            persisted = json.loads(original.decode("utf-8"))
            self.assertEqual(seed_workspace.REGISTRY_SCHEMA_VERSION, persisted["schemaVersion"])
            self.assertEqual(1, persisted["revision"])
            self.assertEqual("seed_7_years_12", persisted["activeSlotId"])
            self.assertEqual("seed_7_years_12", reloaded["activeSlotId"])
            self.assertEqual("registry", reloaded["activeSelectionSource"])

    def test_registry_write_failure_keeps_read_only_workspace_available(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            _, _, registry_path = self.roots(root)
            workspace = self.payload(root, release=release_status())

            result = seed_workspace.initialise_registry_if_missing(
                workspace,
                registry_path=registry_path,
                read_json=storage.read_json,
                atomic_write_text=mock.Mock(side_effect=OSError("read only")),
                parse_run_id=local_ui.parse_run_id,
                run_id_for=local_ui.run_id_for,
                clock=lambda: 100.0,
            )

        self.assertFalse(result["created"])
        self.assertEqual("missing", result["status"])
        self.assertIn("只读磁盘发现", result["warnings"][0])

    def test_same_seed_with_different_years_remains_two_slots(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            run_root, _, _ = self.roots(root)
            twelve = self.cache_entry(run_root, 7, 12, modified=10)
            sixty = self.cache_entry(run_root, 7, 60, modified=20)

            payload = self.payload(root, cached_runs=[twelve, sixty])

        self.assertEqual(
            {"seed_7_years_12", "seed_7_years_60"},
            {slot["slotId"] for slot in payload["slots"]},
        )
        self.assertEqual("seed_7_years_60", payload["activeSlotId"])


class SeedWorkspaceAppWiringTests(unittest.TestCase):
    def test_app_delegates_seed_workspace_dependencies(self) -> None:
        expected = {"ok": True, "slots": []}
        with mock.patch.object(
            seed_workspace,
            "seed_workspace_payload",
            return_value=expected,
        ) as delegated:
            actual = local_ui.seed_workspace_payload()

        self.assertIs(expected, actual)
        kwargs = delegated.call_args.kwargs
        self.assertEqual(local_ui.ROOT_DIR, kwargs["root_dir"])
        self.assertEqual(local_ui.RUN_ROOT, kwargs["run_root"])
        self.assertEqual(local_ui.SAVE_ROOT, kwargs["save_root"])
        self.assertEqual(local_ui.SEED_WORKSPACE_REGISTRY_PATH, kwargs["registry_path"])
        self.assertIs(local_ui.list_cached_runs, kwargs["list_cached_runs"])
        self.assertIs(local_ui.current_viewer_release_status, kwargs["current_viewer_release_status"])
        self.assertIs(local_ui.cache_retention_policy, kwargs["cache_retention_policy"])


if __name__ == "__main__":
    unittest.main()
