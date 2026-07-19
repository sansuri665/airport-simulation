from __future__ import annotations

import json
import os
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path

from airport_sim.server import app as local_ui
from airport_sim.server import seed_workspace, seed_workspace_actions, storage
from unittest import mock


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


class ActionFixture:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.run_root = root / "output" / "seed_explorer_runs"
        self.save_root = root / "saves" / "seed_explorer"
        self.registry_path = root / "saves" / "seed_workspace.json"
        self.policy = {"maxCachedRuns": 2, "pinnedRunIds": []}
        self.cache_states: dict[str, str] = {}
        self.lock_available = True
        self.write_registry(
            revision=1,
            active_slot_id="seed_1_years_12",
            slots=[self.registry_slot(1, 12, label="当前世界")],
        )

    @staticmethod
    def registry_slot(seed: int, years: int, *, label: str = "") -> dict[str, object]:
        return {
            "slotId": local_ui.run_id_for(seed, years),
            "seed": seed,
            "years": years,
            "label": label,
            "createdAt": "2026-07-19T00:00:00Z",
            "lastUsedAt": "2026-07-19T00:00:00Z",
        }

    def write_registry(
        self,
        *,
        revision: int,
        active_slot_id: str | None,
        slots: list[dict[str, object]],
    ) -> None:
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        self.registry_path.write_text(
            json.dumps(
                {
                    "schemaVersion": seed_workspace.REGISTRY_SCHEMA_VERSION,
                    "revision": revision,
                    "activeSlotId": active_slot_id,
                    "slots": slots,
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    def create_cache(
        self,
        seed: int,
        years: int,
        *,
        status: str = "valid",
        modified: float = 10.0,
    ) -> Path:
        slot_id = local_ui.run_id_for(seed, years)
        path = self.run_root / slot_id
        path.mkdir(parents=True, exist_ok=True)
        (path / "data.bin").write_bytes(b"cache-data")
        os.utime(path, (modified, modified))
        self.cache_states[slot_id] = status
        return path

    def create_save(self, seed: int, years: int) -> Path:
        slot_id = local_ui.run_id_for(seed, years)
        path = self.save_root / slot_id / seed_workspace.SAVE_FILENAME
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps({"seed": seed, "years": years, "savedAt": "2026-07-19T01:00:00Z"}),
            encoding="utf-8",
        )
        return path

    def cached_runs(self) -> list[dict[str, object]]:
        results: list[dict[str, object]] = []
        for slot_id, status in self.cache_states.items():
            path = self.run_root / slot_id
            if not path.is_dir():
                continue
            seed, years = local_ui.parse_run_id(slot_id)
            results.append(
                {
                    "runId": slot_id,
                    "seed": seed,
                    "years": years,
                    "generatedAt": "2026-07-19 00:00:00",
                    "lastWriteTime": "2026-07-19 00:00:00",
                    "cacheStatus": status,
                    "hasBeijingOperations": True,
                }
            )
        return results

    def workspace(self) -> dict[str, object]:
        return seed_workspace.seed_workspace_payload(
            root_dir=self.root,
            run_root=self.run_root,
            save_root=self.save_root,
            registry_path=self.registry_path,
            read_json=storage.read_json,
            list_cached_runs=self.cached_runs,
            current_viewer_release_status=unavailable_release,
            cache_retention_policy=lambda: self.policy,
            parse_run_id=local_ui.parse_run_id,
            run_id_for=local_ui.run_id_for,
        )

    @contextmanager
    def try_lock(self, run_id: str):
        del run_id
        yield self.lock_available

    def set_retention(self, maximum: int) -> dict[str, object]:
        self.policy["maxCachedRuns"] = maximum
        return {"ok": True, "policy": dict(self.policy)}

    def action(self, body: dict[str, object]) -> dict[str, object]:
        return seed_workspace_actions.handle_action(
            body,
            root_dir=self.root,
            run_root=self.run_root,
            save_root=self.save_root,
            registry_path=self.registry_path,
            read_json=storage.read_json,
            atomic_write_text=storage.atomic_write_text,
            workspace_payload=self.workspace,
            parse_run_id=local_ui.parse_run_id,
            run_id_for=local_ui.run_id_for,
            try_lock_for_run=self.try_lock,
            set_cache_retention=self.set_retention,
            clock=lambda: 100.0,
            random_below=lambda maximum: 7 if maximum == 2_000 else 0,
        )


class SeedWorkspaceActionTests(unittest.TestCase):
    def test_random_create_is_atomic_active_and_revisioned(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            fixture = ActionFixture(Path(temporary_dir))
            result = fixture.action(
                {
                    "action": "create-random",
                    "years": 60,
                    "label": "新世界",
                    "expectedRevision": 1,
                }
            )
            persisted = storage.read_json(fixture.registry_path)

        self.assertEqual("seed_20260007_years_60", result["slotId"])
        self.assertEqual(2, result["workspaceRevision"])
        self.assertEqual(result["slotId"], persisted["activeSlotId"])
        self.assertEqual("新世界", persisted["slots"][-1]["label"])

    def test_stale_revision_rejects_import_without_touching_registry(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            fixture = ActionFixture(Path(temporary_dir))
            before = fixture.registry_path.read_bytes()
            with self.assertRaises(FileExistsError):
                fixture.action(
                    {
                        "action": "import",
                        "seed": 99,
                        "years": 12,
                        "expectedRevision": 9,
                    }
                )
            self.assertEqual(before, fixture.registry_path.read_bytes())

    def test_only_inactive_empty_draft_can_be_removed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            fixture = ActionFixture(Path(temporary_dir))
            fixture.action(
                {
                    "action": "import",
                    "seed": 2,
                    "years": 12,
                    "activate": False,
                    "expectedRevision": 1,
                }
            )
            result = fixture.action(
                {
                    "action": "remove-slot",
                    "slotId": "seed_2_years_12",
                    "expectedRevision": 2,
                }
            )
            with self.assertRaises(FileExistsError):
                fixture.action(
                    {
                        "action": "remove-slot",
                        "slotId": "seed_1_years_12",
                        "expectedRevision": 3,
                    }
                )

        self.assertTrue(result["changed"])
        self.assertEqual(3, result["workspaceRevision"])

    def test_cache_delete_requires_fresh_plan_and_preserves_player_save(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            fixture = ActionFixture(Path(temporary_dir))
            cache_path = fixture.create_cache(2, 12)
            save_path = fixture.create_save(2, 12)
            fixture.write_registry(
                revision=1,
                active_slot_id="seed_1_years_12",
                slots=[fixture.registry_slot(1, 12), fixture.registry_slot(2, 12)],
            )
            preview = fixture.action(
                {"action": "plan-delete", "slotId": "seed_2_years_12", "target": "cache"}
            )
            self.assertTrue(preview["plan"]["canExecute"])
            self.assertIn("player_save", preview["plan"]["preserves"])
            result = fixture.action(
                {
                    "action": "delete",
                    "slotId": "seed_2_years_12",
                    "target": "cache",
                    "expectedRevision": 1,
                    "planId": preview["plan"]["planId"],
                    "confirm": True,
                }
            )

            self.assertFalse(cache_path.exists())
            self.assertTrue(save_path.exists())
            self.assertEqual("cache", result["deleted"]["target"])
            self.assertEqual(2, result["workspaceRevision"])

    def test_save_delete_is_independent_and_active_lock_blocks_execution(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            fixture = ActionFixture(Path(temporary_dir))
            cache_path = fixture.create_cache(2, 12)
            save_path = fixture.create_save(2, 12)
            fixture.write_registry(
                revision=1,
                active_slot_id="seed_1_years_12",
                slots=[fixture.registry_slot(1, 12), fixture.registry_slot(2, 12)],
            )
            preview = fixture.action(
                {"action": "plan-delete", "slotId": "seed_2_years_12", "target": "save"}
            )
            fixture.lock_available = False
            with self.assertRaises(FileExistsError):
                fixture.action(
                    {
                        "action": "delete",
                        "slotId": "seed_2_years_12",
                        "target": "save",
                        "expectedRevision": 1,
                        "planId": preview["plan"]["planId"],
                        "confirm": True,
                    }
                )
            fixture.lock_available = True
            fixture.action(
                {
                    "action": "delete",
                    "slotId": "seed_2_years_12",
                    "target": "save",
                    "expectedRevision": 1,
                    "planId": preview["plan"]["planId"],
                    "confirm": True,
                }
            )

            self.assertFalse(save_path.exists())
            self.assertTrue(cache_path.exists())

    def test_retention_preview_and_apply_remove_only_unprotected_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            fixture = ActionFixture(Path(temporary_dir))
            active = fixture.create_cache(1, 12, modified=40)
            keep = fixture.create_cache(2, 12, modified=30)
            old = fixture.create_cache(3, 12, modified=20)
            stale = fixture.create_cache(4, 12, status="stale", modified=10)
            fixture.write_registry(
                revision=1,
                active_slot_id="seed_1_years_12",
                slots=[fixture.registry_slot(seed, 12) for seed in range(1, 5)],
            )
            preview = fixture.action({"action": "plan-retention", "maxCachedRuns": 1})
            candidate_ids = {item["slotId"] for item in preview["plan"]["candidates"]}
            protected_ids = {item["slotId"] for item in preview["plan"]["protected"]}
            self.assertEqual({"seed_3_years_12", "seed_4_years_12"}, candidate_ids)
            self.assertEqual({"seed_1_years_12"}, protected_ids)
            result = fixture.action(
                {
                    "action": "apply-retention",
                    "maxCachedRuns": 1,
                    "expectedRevision": 1,
                    "planId": preview["plan"]["planId"],
                    "confirm": True,
                }
            )

            self.assertTrue(active.exists())
            self.assertTrue(keep.exists())
            self.assertFalse(old.exists())
            self.assertFalse(stale.exists())
            self.assertEqual(1, fixture.policy["maxCachedRuns"])
            self.assertEqual(2, len(result["deleted"]))


class SeedWorkspaceActionWiringTests(unittest.TestCase):
    def test_app_delegates_action_dependencies_without_embedding_domain_rules(self) -> None:
        expected = {"ok": True, "action": "activate"}
        body = {"action": "activate", "slotId": "seed_7_years_12", "expectedRevision": 1}
        with mock.patch.object(
            seed_workspace_actions,
            "handle_action",
            return_value=expected,
        ) as delegated:
            actual = local_ui.seed_workspace_action(body)

        self.assertIs(expected, actual)
        self.assertIs(body, delegated.call_args.args[0])
        kwargs = delegated.call_args.kwargs
        self.assertEqual(local_ui.ROOT_DIR, kwargs["root_dir"])
        self.assertEqual(local_ui.RUN_ROOT, kwargs["run_root"])
        self.assertEqual(local_ui.SAVE_ROOT, kwargs["save_root"])
        self.assertIs(local_ui.try_lock_for_run, kwargs["try_lock_for_run"])
        self.assertIs(local_ui.set_cache_retention, kwargs["set_cache_retention"])


if __name__ == "__main__":
    unittest.main()
