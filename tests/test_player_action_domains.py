from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from airport_sim.server import app as local_ui
from airport_sim.server import player_actions, player_contracts, player_financing, player_projects
from airport_sim.server import player_service


class PlayerActionCompatibilityTests(unittest.TestCase):
    def test_app_reexports_domain_catalogs_without_copying_them(self) -> None:
        self.assertIs(player_projects.PROJECT_TEMPLATES, local_ui.PROJECT_TEMPLATES)
        self.assertIs(player_financing.FINANCING_PRODUCTS, local_ui.FINANCING_PRODUCTS)
        self.assertIs(player_projects.RENAMABLE_SLOT_IDS, local_ui.RENAMABLE_SLOT_IDS)

    def test_app_clean_surface_delegates_with_current_rule_dependencies(self) -> None:
        expected = [{"type": "test"}]
        with mock.patch.object(player_actions, "clean_player_actions", return_value=expected) as clean:
            actual = local_ui.clean_player_actions([{"type": "raw"}])

        self.assertIs(expected, actual)
        self.assertEqual([{"type": "raw"}], clean.call_args.args[0])
        self.assertIs(local_ui.PROJECT_TEMPLATES, clean.call_args.kwargs["project_templates"])
        self.assertIs(local_ui.FINANCING_PRODUCTS, clean.call_args.kwargs["financing_products"])
        self.assertIs(local_ui.renovation_event_config, clean.call_args.kwargs["renovation_event_config"])

    def test_app_derived_surfaces_delegate_to_domain_modules(self) -> None:
        with (
            mock.patch.object(player_financing, "player_general_loans", return_value=[{"loan": True}]) as loans,
            mock.patch.object(player_actions, "player_slot_names", return_value={"slot": "name"}) as names,
            mock.patch.object(player_projects, "player_project_events", return_value={"events": []}) as events,
            mock.patch.object(player_projects, "project_catalog", return_value=[{"project": True}]) as catalog,
        ):
            self.assertEqual([{"loan": True}], local_ui.player_general_loans([]))
            self.assertEqual({"slot": "name"}, local_ui.player_slot_names([]))
            self.assertEqual({"events": []}, local_ui.player_project_events([]))
            self.assertEqual([{"project": True}], local_ui.project_catalog())

        loans.assert_called_once()
        names.assert_called_once()
        events.assert_called_once()
        catalog.assert_called_once()

    def test_all_player_domain_modules_enter_simulation_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            with mock.patch.object(player_service, "ensure_player_simulation_outputs", return_value=True) as ensure:
                self.assertTrue(local_ui.ensure_player_simulation_outputs(Path(temporary_dir), [], False))

        names = {Path(path).name for path in ensure.call_args.kwargs["simulation_dependency_files"]}
        self.assertTrue(
            {"app.py", "player_service.py", "player_actions.py", "player_contracts.py", "player_financing.py", "player_projects.py"}
            <= names
        )


class PlayerJournalCharacterizationTests(unittest.TestCase):
    def test_mixed_journal_keeps_input_order_after_latest_rename_and_contract_replacement(self) -> None:
        actions = local_ui.clean_player_actions(
            [
                {"id": "rename-old", "type": "rename_slot", "slotId": "PEK_SLOT_1", "name": "旧名称"},
                {
                    "id": "contract-old",
                    "type": "sign_contract",
                    "contractId": "DUTY_FREE_MAIN",
                    "cycleId": "cycle-1",
                    "terms": {"share": 10},
                },
                {
                    "id": "loan-first",
                    "type": "draw_loan",
                    "productId": "short_turnover",
                    "principalMillionCny": 5000,
                    "tenorQuarters": 4,
                    "gracePeriodQuarters": 0,
                    "startedAtIndex": 20,
                },
                {"id": "rename-new", "type": "rename_slot", "slotId": "PEK_SLOT_1", "name": "  新  名称  "},
                {
                    "id": "contract-new",
                    "type": "sign_contract",
                    "contractId": "DUTY_FREE_MAIN",
                    "cycleId": "cycle-1",
                    "terms": {"share": 20},
                },
            ]
        )

        self.assertEqual(["loan-first", "rename-new", "contract-new"], [action["id"] for action in actions])
        self.assertEqual("新 名称", actions[1]["name"])
        self.assertEqual({"share": 20}, actions[2]["terms"])

    def test_invalid_or_unsupported_actions_are_silently_dropped(self) -> None:
        actions = local_ui.clean_player_actions(
            [
                None,
                {"type": "unknown"},
                {"type": "rename_slot", "slotId": "UNKNOWN", "name": "有效名称"},
                {"type": "rename_slot", "slotId": "PEK_SLOT_1", "name": "X"},
                {"type": "sign_contract", "contractId": "UNKNOWN", "cycleId": "c", "terms": {}},
                {"type": "sign_contract", "contractId": "DUTY_FREE_MAIN", "cycleId": "", "terms": {}},
                {
                    "type": "draw_loan",
                    "productId": "short_turnover",
                    "principalMillionCny": 999,
                    "tenorQuarters": 4,
                    "gracePeriodQuarters": 0,
                    "startedAtIndex": 20,
                },
                {
                    "type": "draw_loan",
                    "productId": "short_turnover",
                    "principalMillionCny": 5000,
                    "tenorQuarters": 5,
                    "gracePeriodQuarters": 0,
                    "startedAtIndex": 20,
                },
                {"type": "start_project", "templateId": "UNKNOWN", "startedAtIndex": 20},
                {"type": "start_project", "templateId": "PEK_T3_RENOVATION", "startedAtIndex": 19},
            ]
        )

        self.assertEqual([], actions)

    def test_first_valid_loan_wins_per_quarter_and_spread_is_frozen(self) -> None:
        actions = local_ui.clean_player_actions(
            [
                {
                    "id": "first",
                    "type": "draw_loan",
                    "productId": "grace_construction",
                    "principalMillionCny": 12000.123456,
                    "tenorQuarters": 60,
                    "gracePeriodQuarters": 8,
                    "startedAtIndex": 23,
                },
                {
                    "id": "second",
                    "type": "draw_loan",
                    "productId": "long_construction",
                    "principalMillionCny": 20000,
                    "tenorQuarters": 40,
                    "gracePeriodQuarters": 0,
                    "startedAtIndex": 23,
                },
            ]
        )

        self.assertEqual(1, len(actions))
        self.assertEqual("first", actions[0]["id"])
        self.assertEqual(12000.1235, actions[0]["principalMillionCny"])
        self.assertEqual(20, actions[0]["termSpreadBps"])
        self.assertEqual(10, actions[0]["graceSpreadBps"])
        self.assertEqual(
            {
                "loan_id": "first",
                "loan_name": "宽限期建设贷款",
                "loan_type": "long_term",
                "start_year": 2030,
                "start_quarter": "Q4",
                "principal_million_cny": 12000.1235,
                "tenor_quarters": 60,
                "repayment_style": "grace_then_equal_principal",
                "grace_period_quarters": 8,
                "term_spread_bps": 20,
                "grace_spread_bps": 10,
                "purpose_note": "玩家融资事务",
            },
            local_ui.player_general_loans(actions)[0],
        )

    def test_construction_recomputes_frozen_config_and_assigns_terminal_number(self) -> None:
        actions = local_ui.clean_player_actions(
            [
                {
                    "id": "construct",
                    "type": "start_project",
                    "templateId": "PEK_SLOT_3_CONSTRUCTION",
                    "startedAtIndex": 20,
                    "eventConfig": {
                        "target_facility_size": "large",
                        "duration_quarters": 999,
                        "capex_million_cny": 1,
                        "terminal_number": 99,
                    },
                }
            ]
        )

        self.assertEqual(1, len(actions))
        event = actions[0]["eventConfig"]
        expected = local_ui.construction_event_config("large")
        self.assertEqual(expected["duration_quarters"], event["duration_quarters"])
        self.assertEqual(expected["capex_million_cny"], event["capex_million_cny"])
        self.assertEqual(4, event["terminal_number"])
        self.assertEqual("首都T4航站楼", event["terminal_name"])

    def test_demolition_requires_completion_plus_clearance_before_construction(self) -> None:
        demolition = local_ui.demolition_event_config("extra_large")
        completion = 20 + int(demolition["duration_quarters"])
        actions = local_ui.clean_player_actions(
            [
                {"id": "demolish", "type": "start_project", "templateId": "PEK_SLOT_1_DEMOLITION", "startedAtIndex": 20},
                {
                    "id": "too-early",
                    "type": "start_project",
                    "templateId": "PEK_SLOT_1_CONSTRUCTION",
                    "targetFacilitySize": "large",
                    "startedAtIndex": completion + local_ui.DEMOLITION_CLEARANCE_QUARTERS - 1,
                },
                {
                    "id": "allowed",
                    "type": "start_project",
                    "templateId": "PEK_SLOT_1_CONSTRUCTION",
                    "targetFacilitySize": "large",
                    "startedAtIndex": completion + local_ui.DEMOLITION_CLEARANCE_QUARTERS,
                },
            ]
        )

        self.assertEqual(["demolish", "allowed"], [action["id"] for action in actions])
        self.assertEqual("extra_large", actions[0]["eventConfig"]["source_facility_size"])
        self.assertEqual("large", actions[1]["eventConfig"]["target_facility_size"])

    def test_renovation_cooldown_starts_after_prior_completion(self) -> None:
        first_config = local_ui.renovation_event_config("extra_large")
        first_completion = 20 + int(first_config["duration_quarters"])
        actions = local_ui.clean_player_actions(
            [
                {"id": "first", "type": "start_project", "templateId": "PEK_T3_RENOVATION", "startedAtIndex": 20},
                {
                    "id": "too-early",
                    "type": "start_project",
                    "templateId": "PEK_T3_RENOVATION",
                    "startedAtIndex": first_completion + local_ui.RENOVATION_COOLDOWN_QUARTERS - 1,
                },
                {
                    "id": "allowed",
                    "type": "start_project",
                    "templateId": "PEK_T3_RENOVATION",
                    "startedAtIndex": first_completion + local_ui.RENOVATION_COOLDOWN_QUARTERS,
                },
            ]
        )

        self.assertEqual(["first", "allowed"], [action["id"] for action in actions])

    def test_rebuild_cooldown_starts_after_prior_completion(self) -> None:
        first_config = local_ui.rebuild_event_config("large", "extra_large")
        first_completion = 20 + int(first_config["duration_quarters"])
        actions = local_ui.clean_player_actions(
            [
                {
                    "id": "first",
                    "type": "start_project",
                    "templateId": "PEK_T2_REBUILD",
                    "targetFacilitySize": "extra_large",
                    "startedAtIndex": 20,
                },
                {
                    "id": "too-early",
                    "type": "start_project",
                    "templateId": "PEK_T2_REBUILD",
                    "targetFacilitySize": "extra_large",
                    "startedAtIndex": first_completion + local_ui.REBUILD_COOLDOWN_QUARTERS - 1,
                },
                {
                    "id": "allowed",
                    "type": "start_project",
                    "templateId": "PEK_T2_REBUILD",
                    "targetFacilitySize": "extra_large",
                    "startedAtIndex": first_completion + local_ui.REBUILD_COOLDOWN_QUARTERS,
                },
            ]
        )

        self.assertEqual(["first", "allowed"], [action["id"] for action in actions])

    def test_project_state_follows_input_order_instead_of_sorting_by_quarter(self) -> None:
        actions = local_ui.clean_player_actions(
            [
                {"id": "future-demolition", "type": "start_project", "templateId": "PEK_SLOT_1_DEMOLITION", "startedAtIndex": 40},
                {"id": "earlier-renovation", "type": "start_project", "templateId": "PEK_T3_RENOVATION", "startedAtIndex": 20},
            ]
        )

        self.assertEqual(["future-demolition"], [action["id"] for action in actions])

    def test_project_events_preserve_frozen_construction_and_demolition_fields(self) -> None:
        demolition = {
            "id": "demolish",
            "type": "start_project",
            "templateId": "PEK_SLOT_1_DEMOLITION",
            "projectId": "demolition-instance",
            "startedAtIndex": 20,
            "eventConfig": {
                "source_facility_size": "extra_large",
                "target_facility_size": "empty",
                "duration_quarters": 1,
                "demolition_expense_million_cny": 25,
            },
        }
        events = local_ui.player_project_events([demolition])
        rebuilt = events["facility_rebuild_events"][0]

        self.assertEqual("demolition", rebuilt["project_type"])
        self.assertEqual("extra_large", rebuilt["from_facility_size"])
        self.assertEqual("empty", rebuilt["target_facility_size"])
        self.assertEqual(2030, rebuilt["start_year"])
        self.assertEqual("Q1", rebuilt["start_quarter"])


class DomainUnitTests(unittest.TestCase):
    def test_contract_normalizer_replaces_same_contract_cycle_only(self) -> None:
        actions: list[dict[str, object]] = []
        seen: set[tuple[str, str, str]] = set()
        first = player_contracts.normalize_contract_action(
            {"id": "first", "type": "sign_contract", "contractId": "DUTY_FREE_MAIN", "cycleId": "c1", "terms": {"x": 1}},
            as_float=local_ui.as_float,
        )
        second = player_contracts.normalize_contract_action(
            {"id": "second", "type": "sign_contract", "contractId": "DUTY_FREE_MAIN", "cycleId": "c1", "terms": {"x": 2}},
            as_float=local_ui.as_float,
        )
        self.assertIsNotNone(first)
        self.assertIsNotNone(second)
        player_contracts.apply_contract_action(actions, seen, first)
        player_contracts.apply_contract_action(actions, seen, second)

        self.assertEqual(["second"], [action["id"] for action in actions])

    def test_financing_normalizer_rejects_second_action_in_quarter(self) -> None:
        seen: set[int] = set()
        raw = {
            "type": "draw_loan",
            "productId": "short_turnover",
            "principalMillionCny": 5000,
            "tenorQuarters": 4,
            "gracePeriodQuarters": 0,
            "startedAtIndex": 20,
        }
        first = player_financing.normalize_financing_action(
            raw,
            seen_quarters=seen,
            financing_products=local_ui.FINANCING_PRODUCTS,
            minimum_action_index=20,
            as_float=local_ui.as_float,
        )
        second = player_financing.normalize_financing_action(
            raw,
            seen_quarters=seen,
            financing_products=local_ui.FINANCING_PRODUCTS,
            minimum_action_index=20,
            as_float=local_ui.as_float,
        )

        self.assertIsNotNone(first)
        self.assertIsNone(second)


if __name__ == "__main__":
    unittest.main()
