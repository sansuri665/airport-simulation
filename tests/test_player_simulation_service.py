from __future__ import annotations

import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest import mock

from airport_sim.server import app as local_ui
from airport_sim.server import player_service


class PlayerServiceCompatibilityTests(unittest.TestCase):
    def test_app_save_surface_delegates_to_player_service(self) -> None:
        expected = {"schemaVersion": "test"}
        with mock.patch.object(player_service, "save_sim_save", return_value=expected) as save:
            actual = local_ui.save_sim_save({"seed": 7})

        self.assertIs(expected, actual)
        self.assertEqual({"seed": 7}, save.call_args.args[0])
        self.assertIs(local_ui.clean_player_actions, save.call_args.kwargs["clean_player_actions"])
        self.assertIs(local_ui.write_json, save.call_args.kwargs["write_json"])

    def test_app_locked_surface_preserves_existing_patch_points(self) -> None:
        expected = {"ok": True}
        with (
            mock.patch.object(local_ui, "run_seed", return_value={"runId": "seed_7_years_60", "cached": True}),
            mock.patch.object(local_ui, "clean_player_actions", return_value=[]) as clean,
            mock.patch.object(local_ui, "ensure_player_simulation_outputs", return_value=True) as ensure,
            mock.patch.object(local_ui, "aggregate_beijing_operations", return_value={"quarters": []}) as aggregate,
            mock.patch.object(player_service, "build_player_response", return_value=expected) as build,
        ):
            actual = local_ui._load_player_simulation_locked(7, 60, False, [{"type": "bad"}], None)

        self.assertIs(expected, actual)
        clean.assert_called_once_with([{"type": "bad"}])
        ensure.assert_called_once()
        aggregate.assert_called_once()
        build.assert_called_once()


class PlayerSaveContractTests(unittest.TestCase):
    def test_save_serialization_keeps_schema_and_writes_once_after_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            run_root = root / "runs"
            save_path = root / "saves" / "dynamic_test_save.json"
            (run_root / "seed_7_years_60").mkdir(parents=True)
            writes: list[tuple[Path, dict[str, object]]] = []

            payload = player_service.save_sim_save(
                {"seed": "7", "years": 60, "mode": "simulate_default", "playerActions": [{"type": "kept"}]},
                clean_seed=int,
                clean_years=int,
                clean_operation_mode=str,
                as_float=lambda value, default=0.0: float(value if value is not None else default),
                clean_player_actions=lambda actions: list(actions),
                run_root=run_root,
                run_id_for=lambda seed, years: f"seed_{seed}_years_{years}",
                sim_save_path=lambda seed, years: save_path,
                write_json=lambda path, value: writes.append((path, value)),
                clock=lambda: 1_700_000_000.125,
            )

        self.assertEqual("seed-explorer-simulation-save-v0.3", payload["schemaVersion"])
        self.assertEqual([{"type": "kept"}], payload["playerActions"])
        self.assertEqual(1_700_000_000.125, payload["savedAtUnix"])
        self.assertEqual([(save_path, payload)], writes)

    def test_missing_run_fails_before_cleaning_or_writing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            forbidden = mock.Mock(side_effect=AssertionError("must not be called"))
            with self.assertRaises(FileNotFoundError):
                player_service.save_sim_save(
                    {"seed": 7, "years": 60, "mode": "simulate_default"},
                    clean_seed=int,
                    clean_years=int,
                    clean_operation_mode=str,
                    as_float=float,
                    clean_player_actions=forbidden,
                    run_root=Path(temporary_dir) / "runs",
                    run_id_for=lambda seed, years: f"seed_{seed}_years_{years}",
                    sim_save_path=forbidden,
                    write_json=forbidden,
                )


class PlayerOutputOrchestrationTests(unittest.TestCase):
    def paths(self, root: Path) -> player_service.SimulationPaths:
        dependencies = root / "dependencies"
        dependencies.mkdir()
        paths = {
            "operations_config": dependencies / "operations.json",
            "finance_config": dependencies / "finance.json",
            "quarterly_operations_script": dependencies / "operations.py",
            "financial_state_script": dependencies / "finance.py",
        }
        for path in paths.values():
            path.write_text(path.name, encoding="utf-8")
        return player_service.SimulationPaths(
            root_dir=root,
            simulation_dir_name="simulation_default",
            operations_relative_csv=Path("simulation_default/operations.csv"),
            financial_relative_csv=Path("simulation_default/finance.csv"),
            **paths,
        )

    def test_formal_player_config_does_not_inherit_reference_projects(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            operations_path = root / "reference-operations.json"
            finance_path = root / "reference-finance.json"
            reference_operations = {
                "config_version": "reference",
                "facility_renovation_events": [{"event_id": "reference-renovation"}],
                "facility_construction_events": [
                    {"event_id": "PKX_SLOT_2_CONSTRUCTION_2065Q3"}
                ],
                "facility_rebuild_events": [{"event_id": "reference-rebuild"}],
            }
            reference_finance = {
                "config_version": "reference-finance",
                "general_loans": [{"loan_id": "reference-loan"}],
            }
            writes: dict[str, dict[str, object]] = {}

            player_service.write_player_simulation_configs(
                root / "run",
                [],
                simulation_dir_name="simulation_default",
                operations_config_path=operations_path,
                finance_config_path=finance_path,
                read_config_json=lambda path: dict(
                    reference_operations if path == operations_path else reference_finance
                ),
                player_project_events=lambda actions: {
                    "facility_renovation_events": [],
                    "facility_construction_events": [],
                    "facility_rebuild_events": [],
                },
                player_general_loans=lambda actions: [],
                write_json=lambda path, payload: writes.setdefault(path.name, payload),
            )

        generated = writes[
            "beijing_airport_system_quarterly_operations_simulate_default.json"
        ]
        self.assertEqual([], generated["facility_renovation_events"])
        self.assertEqual([], generated["facility_construction_events"])
        self.assertEqual([], generated["facility_rebuild_events"])
        self.assertNotIn(
            "PKX_SLOT_2_CONSTRUCTION_2065Q3",
            str(generated),
        )

    def test_cache_hit_does_not_rebuild_or_run_commands(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            run_dir = root / "run"
            paths = self.paths(root)
            operations_path = run_dir / paths.operations_relative_csv
            financial_path = run_dir / paths.financial_relative_csv
            manifest_path = run_dir / paths.simulation_dir_name / "action_cache_manifest.json"
            operations_path.parent.mkdir(parents=True)
            financial_path.parent.mkdir(parents=True, exist_ok=True)
            operations_path.write_text("ok", encoding="utf-8")
            financial_path.write_text("ok", encoding="utf-8")
            fingerprint = player_service.simulation_fingerprint([], paths, [Path(player_service.__file__)])
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            manifest_path.write_text("{}", encoding="utf-8")
            forbidden = mock.Mock(side_effect=AssertionError("must not rebuild"))

            cached = player_service.ensure_player_simulation_outputs(
                run_dir,
                [],
                False,
                paths=paths,
                simulation_dependency_files=[Path(player_service.__file__)],
                read_json=lambda path: {"fingerprint": fingerprint},
                write_json=forbidden,
                ensure_inside=lambda root, path: path,
                remove_tree=forbidden,
                write_default_city_demand_csv=forbidden,
                write_player_simulation_configs=forbidden,
                run_layer_command=forbidden,
                executable="python",
            )

        self.assertTrue(cached)

    def test_service_dependency_digest_is_content_sensitive_but_workspace_stable(self) -> None:
        with tempfile.TemporaryDirectory() as first_dir, tempfile.TemporaryDirectory() as second_dir:
            first = Path(first_dir) / "player_service.py"
            second = Path(second_dir) / "player_service.py"
            first.write_text("same", encoding="utf-8")
            second.write_text("same", encoding="utf-8")

            first_digest = player_service.dependency_digest([first])
            second_digest = player_service.dependency_digest([second])
            second.write_text("changed", encoding="utf-8")

            self.assertEqual(first_digest, second_digest)
            self.assertNotEqual(first_digest, player_service.dependency_digest([second]))

    def test_cache_miss_runs_operations_then_finance_then_commits_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            run_dir = root / "run"
            paths = self.paths(root)
            events: list[str] = []
            city_path = run_dir / "city.csv"
            operations_config_path = run_dir / "operations-config.json"
            finance_config_path = run_dir / "finance-config.json"

            cached = player_service.ensure_player_simulation_outputs(
                run_dir,
                [{"type": "kept"}],
                False,
                paths=paths,
                simulation_dependency_files=[Path(player_service.__file__)],
                read_json=lambda path: {},
                write_json=lambda path, value: events.append("manifest"),
                ensure_inside=lambda root, path: path,
                remove_tree=lambda path: events.append("remove"),
                write_default_city_demand_csv=lambda path: events.append("city") or city_path,
                write_player_simulation_configs=lambda path, actions: events.append("configs") or (operations_config_path, finance_config_path),
                run_layer_command=lambda command, label: events.append("operations" if "quarterly" in label else "finance"),
                executable="python",
            )

        self.assertFalse(cached)
        self.assertEqual(["city", "configs", "operations", "finance", "manifest"], events)

    def test_failed_finance_command_does_not_commit_success_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            run_dir = root / "run"
            paths = self.paths(root)
            writes: list[Path] = []
            command_count = 0

            def run_command(command: list[str], label: str) -> None:
                nonlocal command_count
                command_count += 1
                if command_count == 2:
                    raise RuntimeError("finance failed")

            with self.assertRaisesRegex(RuntimeError, "finance failed"):
                player_service.ensure_player_simulation_outputs(
                    run_dir,
                    [],
                    True,
                    paths=paths,
                    simulation_dependency_files=[Path(player_service.__file__)],
                    read_json=lambda path: {},
                    write_json=lambda path, value: writes.append(path),
                    ensure_inside=lambda root, path: path,
                    remove_tree=lambda path: None,
                    write_default_city_demand_csv=lambda path: run_dir / "city.csv",
                    write_player_simulation_configs=lambda path, actions: (run_dir / "operations.json", run_dir / "finance.json"),
                    run_layer_command=run_command,
                    executable="python",
                )

        self.assertEqual([], writes)


class PlayerResponseContractTests(unittest.TestCase):
    def test_build_response_clamps_visible_history_without_dropping_world_contract(self) -> None:
        quarters = [{"label": f"Q{index}", "operations": {}} for index in range(5)]
        payload = {"quarters": quarters, "playerStartIndex": 2}

        result = player_service.build_player_response(
            payload,
            [{"type": "kept"}],
            99,
            player_slot_names=lambda actions: {"slot": "name"},
            project_catalog=lambda: [{"id": "project"}],
            financing_products={"loan": {}},
            financing_policy={"rate": 1},
            player_contract_previews=lambda all_quarters, active_index: {"active": active_index},
        )

        self.assertEqual(4, result["currentQuarterIndex"])
        self.assertEqual(5, result["periodCount"])
        self.assertEqual(quarters, result["allQuarters"])
        self.assertEqual("Q4", result["worldFinalLabel"])
        self.assertEqual({"active": 4}, result["contractPreviews"])

    def test_load_surface_locks_full_horizon_and_preserves_argument_order(self) -> None:
        events: list[object] = []

        @contextmanager
        def lock(run_id: str):
            events.append(("lock", run_id))
            yield
            events.append("unlock")

        result = player_service.load_player_simulation(
            7,
            5,
            False,
            [],
            None,
            minimum_years=60,
            clean_years=int,
            run_id_for=lambda seed, years: f"seed_{seed}_years_{years}",
            lock_for_run=lock,
            load_locked=lambda *args: events.append(("load", args)) or {"ok": True},
        )

        self.assertEqual({"ok": True}, result)
        self.assertEqual(("lock", "seed_7_years_60"), events[0])
        self.assertEqual(("load", (7, 60, False, [], None)), events[1])
        self.assertEqual("unlock", events[2])


if __name__ == "__main__":
    unittest.main()
