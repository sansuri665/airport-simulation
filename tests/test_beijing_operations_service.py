from __future__ import annotations

import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest import mock

from airport_sim.server import app as local_ui
from airport_sim.server import beijing_operations
from airport_sim.server import player_service


class BeijingOperationsCompatibilityTests(unittest.TestCase):
    def test_app_city_row_surface_delegates_with_current_capacity_contract(self) -> None:
        expected = {"delegated": True}
        with mock.patch.object(
            beijing_operations,
            "update_simulation_city_row",
            return_value=expected,
        ) as update:
            actual = local_ui.update_simulation_city_row({"year": "2030"})

        self.assertIs(expected, actual)
        self.assertEqual({"year": "2030"}, update.call_args.args[0])
        self.assertEqual(local_ui.INITIAL_MAX_CAPACITY_MILLION, update.call_args.kwargs["max_capacity"])
        self.assertIs(local_ui.as_float, update.call_args.kwargs["as_float"])

    def test_app_aggregate_surface_delegates_with_existing_mock_points(self) -> None:
        expected = {"delegated": True}
        run_dir = Path("run")
        with mock.patch.object(
            beijing_operations,
            "aggregate_beijing_operations",
            return_value=expected,
        ) as aggregate:
            actual = local_ui.aggregate_beijing_operations(run_dir, 7, 12, True)

        self.assertIs(expected, actual)
        self.assertEqual((run_dir, 7, 12, True), aggregate.call_args.args[:4])
        self.assertIs(local_ui.read_csv, aggregate.call_args.kwargs["read_csv"])
        self.assertIs(local_ui.summarize_beijing_quarter, aggregate.call_args.kwargs["summarize_quarter"])

    def test_player_action_fingerprint_includes_beijing_service(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            with mock.patch.object(player_service, "ensure_player_simulation_outputs", return_value=True) as ensure:
                self.assertTrue(local_ui.ensure_player_simulation_outputs(Path(temporary_dir), [], False))

        names = {Path(path).name for path in ensure.call_args.kwargs["simulation_dependency_files"]}
        self.assertIn("beijing_operations.py", names)


class SimulationCityDemandTests(unittest.TestCase):
    def update(self, row: dict[str, str]) -> dict[str, object]:
        return beijing_operations.update_simulation_city_row(
            row,
            as_float=local_ui.as_float,
            active_facility_slots="slots",
            design_capacity=154.0,
            max_capacity=200.0,
        )

    def test_default_capacity_classifies_airport_airline_and_demand_bottlenecks(self) -> None:
        airport = self.update(
            {
                "city_potential_passengers_million": "250",
                "city_airline_supply_passengers_million": "220",
                "business_passengers_million": "100",
                "business_airline_supply_passengers_million": "80",
            }
        )
        airline = self.update(
            {
                "city_potential_passengers_million": "180",
                "city_airline_supply_passengers_million": "150",
            }
        )
        demand = self.update(
            {
                "city_potential_passengers_million": "150",
                "city_airline_supply_passengers_million": "180",
            }
        )

        self.assertEqual("airport_capacity_limited", airport["city_binding_bottleneck"])
        self.assertEqual(200.0, airport["city_served_passengers_million"])
        self.assertEqual(80.0, airport["business_served_passengers_million"])
        self.assertEqual("airline_supply_limited", airline["city_binding_bottleneck"])
        self.assertEqual("demand_limited", demand["city_binding_bottleneck"])

    def test_zero_demand_keeps_original_empty_value_contract(self) -> None:
        row = self.update({"city_potential_passengers_million": "0"})

        self.assertEqual(100.0, row["city_capacity_fulfillment_pct"])
        self.assertEqual(100.0, row["city_total_fulfillment_pct"])
        self.assertEqual(0.0, row["business_served_passengers_million"])
        self.assertEqual(100.0, row["business_airline_supply_fulfillment_pct"])

    def test_csv_preparation_preserves_first_row_field_order_and_row_order(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            run_dir = Path(temporary_dir)
            source_relative = Path("baseline/source.csv")
            target_relative = Path("simulation/target.csv")
            source_path = run_dir / source_relative
            source_path.parent.mkdir(parents=True)
            source_path.write_text("placeholder", encoding="utf-8")
            writes: list[tuple[Path, list[dict[str, object]], list[str]]] = []
            rows = [{"b": "1", "a": "2"}, {"b": "3", "a": "4"}]

            target = beijing_operations.write_default_simulation_city_demand_csv(
                run_dir,
                source_relative_csv=source_relative,
                target_relative_csv=target_relative,
                read_csv=lambda path: rows,
                write_csv=lambda path, values, fields: writes.append((path, values, fields)),
                update_row=lambda row: {**row, "updated": True},
            )

        self.assertEqual(run_dir / target_relative, target)
        self.assertEqual(["b", "a"], writes[0][2])
        self.assertEqual(["1", "3"], [row["b"] for row in writes[0][1]])

    def test_csv_preparation_fails_before_write_for_missing_or_empty_source(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            run_dir = Path(temporary_dir)
            forbidden = mock.Mock(side_effect=AssertionError("must not write"))
            with self.assertRaises(FileNotFoundError):
                beijing_operations.write_default_simulation_city_demand_csv(
                    run_dir,
                    source_relative_csv=Path("missing.csv"),
                    target_relative_csv=Path("target.csv"),
                    read_csv=forbidden,
                    write_csv=forbidden,
                    update_row=forbidden,
                )
            source = run_dir / "source.csv"
            source.write_text("placeholder", encoding="utf-8")
            with self.assertRaises(FileNotFoundError):
                beijing_operations.write_default_simulation_city_demand_csv(
                    run_dir,
                    source_relative_csv=Path("source.csv"),
                    target_relative_csv=Path("target.csv"),
                    read_csv=lambda path: [],
                    write_csv=forbidden,
                    update_row=forbidden,
                )


class BeijingQuarterContractTests(unittest.TestCase):
    def test_non_empty_ids_preserves_first_occurrence_across_delimiters(self) -> None:
        self.assertEqual(
            ["a", "b", "c", "d"],
            beijing_operations.non_empty_ids("a|b", "b,c", " c ; d "),
        )

    def test_warning_thresholds_and_order_are_stable(self) -> None:
        warnings = beijing_operations.quarter_warnings(
            {
                "quarter_design_utilization_pct": "100.004",
                "quarter_max_utilization_pct": "94.995",
                "quarter_crowding_index": "0.004",
                "renovation_active_event_ids": "r",
                "construction_active_event_ids": "c",
                "rebuild_active_event_ids": "b",
            },
            {"period_end_cash_million_cny": "-0.01", "loan_blocked_ids": "loan"},
            rounded=local_ui.rounded,
            as_text=local_ui.as_text,
        )

        self.assertEqual(
            ["超过设计容量", "接近极限容量", "现金为负", "贷款被拒", "翻新施工", "新建施工", "重建施工"],
            warnings,
        )

    def test_missing_finance_defaults_to_zero_and_operations_capex_fallback(self) -> None:
        ops = {
            "year": "2030",
            "quarter": "Q1",
            "player_decision_enabled": "true",
            "renovation_quarter_capex_outlay_million_cny": "1.25",
            "construction_quarter_capex_outlay_million_cny": "2.5",
            "rebuild_quarter_capex_outlay_million_cny": "3.75",
        }
        quarter = beijing_operations.summarize_beijing_quarter(
            4,
            ops,
            {},
            as_float=local_ui.as_float,
            as_bool=local_ui.as_bool,
            as_text=local_ui.as_text,
            rounded=local_ui.rounded,
            non_empty_ids=beijing_operations.non_empty_ids,
            quarter_warnings=lambda ops, finance: [],
        )

        self.assertEqual("2030 Q1", quarter["label"])
        self.assertTrue(quarter["playerDecisionEnabled"])
        self.assertEqual(0.0, quarter["finance"]["totalAssets"])
        self.assertEqual(7.5, quarter["finance"]["capexOutlay"])

    def test_nonzero_finance_capex_overrides_operations_sum(self) -> None:
        quarter = beijing_operations.summarize_beijing_quarter(
            0,
            {"year": "2025", "quarter": "Q1", "renovation_quarter_capex_outlay_million_cny": "10"},
            {"period_total_capex_outlay_million_cny": "2.25"},
            as_float=local_ui.as_float,
            as_bool=local_ui.as_bool,
            as_text=local_ui.as_text,
            rounded=local_ui.rounded,
            non_empty_ids=beijing_operations.non_empty_ids,
            quarter_warnings=lambda ops, finance: [],
        )

        self.assertEqual(2.25, quarter["finance"]["capexOutlay"])


class BeijingAggregationTests(unittest.TestCase):
    def test_aggregate_pairs_finance_by_quarter_and_defaults_missing_rows(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            run_dir = root / "output" / "run-1"
            operations_relative = Path("operations.csv")
            financial_relative = Path("finance.csv")
            run_dir.mkdir(parents=True)
            (run_dir / operations_relative).write_text("ops", encoding="utf-8")
            (run_dir / financial_relative).write_text("finance", encoding="utf-8")
            operation_rows = [
                {"year": "2030", "quarter": "Q1"},
                {"year": "2030", "quarter": "Q2"},
            ]
            financial_rows = [{"year": "2030", "quarter": "Q2", "cash": "matched"}]
            pairs: list[tuple[int, str]] = []

            payload = beijing_operations.aggregate_beijing_operations(
                run_dir,
                7,
                12,
                True,
                mode="replay",
                operations_relative_csv=operations_relative,
                financial_relative_csv=financial_relative,
                root_dir=root,
                operation_mode_details={"replay": {"label": "Replay", "description": "Description"}},
                read_csv=lambda path: operation_rows if path.name == "operations.csv" else financial_rows,
                quarter_key=lambda row: (int(row["year"]), row["quarter"]),
                summarize_quarter=lambda index, ops, finance: pairs.append((index, finance.get("cash", "missing"))) or {
                    "label": f"{ops['year']} {ops['quarter']}",
                    "playerDecisionEnabled": index == 1,
                },
            )

        self.assertEqual([(0, "missing"), (1, "matched")], pairs)
        self.assertEqual(1, payload["playerStartIndex"])
        self.assertEqual("2030 Q1", payload["startLabel"])
        self.assertEqual("2030 Q2", payload["finalLabel"])

    def test_missing_operations_or_finance_file_fails_before_read(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            run_dir = Path(temporary_dir)
            forbidden = mock.Mock(side_effect=AssertionError("must not read"))
            with self.assertRaisesRegex(FileNotFoundError, "quarterly operations"):
                beijing_operations.aggregate_beijing_operations(
                    run_dir,
                    7,
                    12,
                    False,
                    operations_relative_csv=Path("ops.csv"),
                    financial_relative_csv=Path("finance.csv"),
                    root_dir=run_dir.parent,
                    operation_mode_details=local_ui.OPERATION_MODE_DETAILS,
                    read_csv=forbidden,
                    quarter_key=forbidden,
                    summarize_quarter=forbidden,
                )


class BeijingLoadSequenceTests(unittest.TestCase):
    def test_simulate_default_reuses_seed_and_action_cache_only_when_both_hit(self) -> None:
        events: list[str] = []
        payload = beijing_operations.load_beijing_operations_locked(
            7,
            60,
            False,
            "simulate_default",
            run_root=Path("runs"),
            run_seed=lambda seed, years, force: events.append("run") or {"runId": "seed_7_years_60", "cached": True},
            ensure_player_simulation_outputs=lambda run_dir, actions, force: events.append("simulation") or False,
            aggregate_beijing_operations=lambda *args: events.append("aggregate") or {"cached": args[3]},
            simulation_operations_relative_csv=Path("simulation/ops.csv"),
            simulation_financial_relative_csv=Path("simulation/finance.csv"),
        )

        self.assertEqual(["run", "simulation", "aggregate"], events)
        self.assertFalse(payload["cached"])

    def test_replay_missing_output_retries_forced_once_when_request_was_not_forced(self) -> None:
        run_calls: list[bool] = []
        aggregate_calls: list[bool] = []

        def aggregate(*args):
            aggregate_calls.append(args[3])
            if len(aggregate_calls) == 1:
                raise FileNotFoundError("missing")
            return {"cached": args[3]}

        payload = beijing_operations.load_beijing_operations_locked(
            7,
            12,
            False,
            "replay",
            run_root=Path("runs"),
            run_seed=lambda seed, years, force: run_calls.append(force) or {"runId": "seed_7_years_12", "cached": True},
            ensure_player_simulation_outputs=mock.Mock(),
            aggregate_beijing_operations=aggregate,
            simulation_operations_relative_csv=Path("simulation/ops.csv"),
            simulation_financial_relative_csv=Path("simulation/finance.csv"),
        )

        self.assertEqual([False, True], run_calls)
        self.assertEqual([True, False], aggregate_calls)
        self.assertFalse(payload["cached"])

    def test_forced_replay_propagates_missing_output_without_second_run(self) -> None:
        run_calls: list[bool] = []
        with self.assertRaises(FileNotFoundError):
            beijing_operations.load_beijing_operations_locked(
                7,
                12,
                True,
                "replay",
                run_root=Path("runs"),
                run_seed=lambda seed, years, force: run_calls.append(force) or {"runId": "seed_7_years_12", "cached": False},
                ensure_player_simulation_outputs=mock.Mock(),
                aggregate_beijing_operations=mock.Mock(side_effect=FileNotFoundError("missing")),
                simulation_operations_relative_csv=Path("simulation/ops.csv"),
                simulation_financial_relative_csv=Path("simulation/finance.csv"),
            )

        self.assertEqual([True], run_calls)

    def test_public_load_surface_locks_run_and_preserves_argument_order(self) -> None:
        events: list[object] = []

        @contextmanager
        def lock(run_id: str):
            events.append(("lock", run_id))
            yield
            events.append("unlock")

        result = beijing_operations.load_beijing_operations(
            7,
            12,
            False,
            "replay",
            run_id_for=lambda seed, years: f"seed_{seed}_years_{years}",
            lock_for_run=lock,
            load_locked=lambda *args: events.append(("load", args)) or {"ok": True},
        )

        self.assertEqual({"ok": True}, result)
        self.assertEqual(("lock", "seed_7_years_12"), events[0])
        self.assertEqual(("load", (7, 12, False, "replay")), events[1])
        self.assertEqual("unlock", events[2])


if __name__ == "__main__":
    unittest.main()
