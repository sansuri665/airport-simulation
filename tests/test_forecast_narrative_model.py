from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MACRO_DIR = ROOT_DIR / "macro_layers"
if str(MACRO_DIR) not in sys.path:
    sys.path.insert(0, str(MACRO_DIR))

import city_airport_potential_passenger_forecast_layer_sim as forecast_layer


COMPONENTS = ("business", "leisure", "vfr", "long_haul", "transfer")
SHARES = {
    "business": 0.24,
    "leisure": 0.31,
    "vfr": 0.18,
    "long_haul": 0.15,
    "transfer": 0.12,
}
CONFIG_PATH = (
    ROOT_DIR
    / "config"
    / "city_airport_potential_passenger_forecast"
    / "beijing_airport_system_potential_passenger_forecast_v1.json"
)


def synthetic_market_rows(
    *,
    seed: int = 77,
    future_demand_growth_pct: float = 1.6,
    future_supply_growth_pct: float = 1.4,
) -> list[dict[str, object]]:
    potential = 90.0
    supply = 86.0
    rows: list[dict[str, object]] = []
    for index, year in enumerate(range(2025, 2046)):
        if year > 2025:
            if year <= 2030:
                potential *= 1.018
                supply *= 1.016
            else:
                potential *= 1.0 + future_demand_growth_pct / 100.0
                supply *= 1.0 + future_supply_growth_pct / 100.0
        effective = min(potential, supply)
        row: dict[str, object] = {
            "seed": seed,
            "year": year,
            "year_index": index,
            "city_potential_passengers_million": potential,
            "city_airline_offered_capacity_million": supply,
            "city_airline_serviceable_supply_million": effective,
            "city_air_demand_growth_pct": (
                1.8 if year <= 2030 else future_demand_growth_pct
            ),
            "seed_city_momentum_label": "balanced",
            "seed_city_potential_multiplier": 1.0,
            "city_demand_regime": "mature_growth",
        }
        for component, share in SHARES.items():
            row[f"{component}_passengers_million"] = potential * share
            row[f"{component}_airline_supply_passengers_million"] = effective * share
        rows.append(row)
    return rows


class ForecastNarrativeModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = forecast_layer.load_config(CONFIG_PATH)
        cls.rows = forecast_layer.simulate_potential_passenger_forecast(
            synthetic_market_rows(),
            cls.config,
        )

    def test_all_reports_resolve_shared_tier_narrative_and_modifier_profiles(self) -> None:
        reports = self.config["forecast_reports"]
        self.assertEqual(13, len(reports))
        self.assertEqual(13, len({row["forecast_report_id"] for row in reports}))
        self.assertEqual(
            9,
            len({row["forecast_narrative_profile_id"] for row in reports}),
        )
        by_id = {row["forecast_report_id"]: row for row in reports}
        self.assertEqual(
            by_id["public_consensus"]["forecast_narrative_profile_id"],
            by_id["initial_local_bureau_note"]["forecast_narrative_profile_id"],
        )
        self.assertEqual(
            by_id["basic_research"]["forecast_narrative_profile_id"],
            by_id["middle_growth_desk"]["forecast_narrative_profile_id"],
        )
        shared_balanced = {
            by_id[report_id]["forecast_narrative_profile_id"]
            for report_id in (
                "middle_balanced_panel",
                "professional_consulting",
                "top_institution",
            )
        }
        self.assertEqual(1, len(shared_balanced))
        self.assertAlmostEqual(
            0.92,
            by_id["top_institution"]["component_signal_quality"],
        )
        self.assertEqual(
            ["供给敏感", "客群敏感"],
            by_id["top_institution"]["forecast_narrative_modifier_labels"],
        )
        for report in reports:
            self.assertTrue(report["forecast_report_tier_profile_id"])
            self.assertTrue(report["forecast_narrative_profile_id"])
            self.assertEqual(
                report["narrative_style_label"],
                report["forecast_report_display_name"],
            )
            self.assertLessEqual(
                len(report["forecast_narrative_modifier_ids"]),
                2,
            )
            self.assertIn("signal_observation_quality", report)
            self.assertIn("narrative_revision_speed", report)
            self.assertTrue(report["narrative_style_summary"])
            self.assertTrue(report["narrative_style_method"])
            self.assertTrue(report["narrative_style_blind_spot"])
            self.assertEqual(
                len(report["forecast_narrative_modifier_ids"]),
                len(report["forecast_narrative_modifier_labels"]),
            )
            self.assertEqual(
                len(report["forecast_narrative_modifier_ids"]),
                len(report["forecast_narrative_modifier_groups"]),
            )

        catalog_path = (
            ROOT_DIR
            / "config"
            / "forecast_narrative_profiles"
            / "forecast_narrative_profiles_v2.json"
        )
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        self.assertEqual(9, len(catalog["profiles"]))
        self.assertEqual(15, len(catalog["modifiers"]))
        self.assertEqual(
            {"position", "method_focus", "revision_behavior", "uncertainty"},
            {modifier["modifier_group"] for modifier in catalog["modifiers"]},
        )

    def test_total_component_and_bottleneck_constraints_hold(self) -> None:
        for row in self.rows:
            with self.subTest(
                report=row["forecast_report_id"],
                as_of=row["as_of_year"],
                target=row["forecast_year"],
            ):
                self.assertAlmostEqual(
                    row["forecast_effective_passengers_mid_million"],
                    min(
                        row["forecast_potential_passengers_mid_million"],
                        row["forecast_airline_supply_passengers_mid_million"],
                    ),
                    places=4,
                )
                component_total = sum(
                    row[f"{component}_forecast_effective_passengers_mid_million"]
                    for component in COMPONENTS
                )
                self.assertAlmostEqual(
                    row["forecast_effective_passengers_mid_million"],
                    component_total,
                    delta=0.001,
                )
                self.assertAlmostEqual(
                    row["forecast_potential_passengers_mid_million"],
                    sum(
                        row[f"{component}_forecast_potential_passengers_mid_million"]
                        for component in COMPONENTS
                    ),
                    delta=0.001,
                )
                self.assertAlmostEqual(
                    row["forecast_airline_supply_passengers_mid_million"],
                    sum(
                        row[f"{component}_forecast_airline_offered_capacity_million"]
                        for component in COMPONENTS
                    ),
                    delta=0.001,
                )
                for component in COMPONENTS:
                    effective = row[
                        f"{component}_forecast_effective_passengers_mid_million"
                    ]
                    self.assertLessEqual(
                        effective,
                        row[
                            f"{component}_forecast_potential_passengers_mid_million"
                        ]
                        + 0.001,
                    )
                    self.assertLessEqual(
                        effective,
                        row[
                            f"{component}_forecast_airline_supply_passengers_mid_million"
                        ]
                        + 0.001,
                    )
                    self.assertAlmostEqual(
                        effective,
                        row[
                            f"{component}_forecast_airline_supply_passengers_mid_million"
                        ],
                        delta=0.001,
                    )
                    self.assertLessEqual(
                        row[f"{component}_forecast_effective_passengers_low_million"],
                        effective + 0.001,
                    )
                    self.assertGreaterEqual(
                        row[f"{component}_forecast_effective_passengers_high_million"],
                        effective - 0.001,
                    )

    def test_component_forecast_can_express_different_supply_fulfillment(self) -> None:
        constrained_rows = [
            row
            for row in self.rows
            if row["forecast_airline_supply_passengers_mid_million"]
            < row["forecast_potential_passengers_mid_million"]
            and row["forecast_report_id"] != "god_future_peek"
        ]
        self.assertTrue(constrained_rows)
        self.assertTrue(
            any(
                max(
                    row[f"{component}_forecast_airline_supply_fulfillment_pct"]
                    for component in COMPONENTS
                )
                - min(
                    row[f"{component}_forecast_airline_supply_fulfillment_pct"]
                    for component in COMPONENTS
                )
                > 0.1
                for row in constrained_rows
            )
        )
    def test_god_report_remains_exact(self) -> None:
        god_rows = [
            row
            for row in self.rows
            if row["forecast_report_id"] == "god_future_peek"
        ]
        self.assertTrue(god_rows)
        for row in god_rows:
            self.assertEqual(
                row["debug_hidden_true_effective_passengers_million"],
                row["forecast_effective_passengers_mid_million"],
            )
            self.assertEqual(100.0, row["realized_report_quality_score"])

    def test_realized_score_v12_uses_total_component_and_process_weights(self) -> None:
        self.assertEqual(
            {
                "midpoint": 0.30,
                "trend": 0.12,
                "shape": 0.08,
                "bottleneck": 0.05,
                "interval": 0.15,
                "component_potential_structure": 0.04,
                "component_supply_structure": 0.05,
                "component_fulfillment": 0.03,
                "component_interval": 0.03,
            },
            forecast_layer.REALIZED_RESULT_SCORE_WEIGHTS,
        )
        self.assertEqual(
            {"turn_timing": 0.08, "revision_discipline": 0.07},
            forecast_layer.REALIZED_PROCESS_SCORE_WEIGHTS,
        )
        self.assertAlmostEqual(
            0.85,
            forecast_layer.REALIZED_RESULT_WEIGHT_TOTAL,
        )

        report_rows = [
            row
            for row in self.rows
            if row["forecast_report_id"] == "public_consensus"
            and row["as_of_year"] == 2030
        ]
        weights = [
            1.0 + 0.08 * row["forecast_horizon_years"]
            for row in report_rows
        ]
        total_weight = sum(weights)

        def weighted(field: str) -> float:
            return sum(
                row[field] * weight
                for row, weight in zip(report_rows, weights)
            ) / total_weight

        expected_result = (
            0.30 * weighted("realized_midpoint_accuracy_score")
            + 0.12 * weighted("realized_trend_accuracy_score")
            + 0.08 * weighted("realized_shape_accuracy_score")
            + 0.05 * weighted("realized_bottleneck_accuracy_score")
            + 0.15 * weighted("realized_interval_calibration_score")
            + 0.04 * weighted("realized_component_potential_structure_score")
            + 0.05 * weighted("realized_component_supply_structure_score")
            + 0.03 * weighted("realized_component_fulfillment_score")
            + 0.03 * weighted("realized_component_interval_calibration_score")
        ) / 0.85
        first = report_rows[0]
        expected_actual = (
            0.85 * expected_result
            + 0.08 * first["realized_turn_timing_score"]
            + 0.07 * first["realized_revision_discipline_score"]
        )
        self.assertEqual(
            "narrative-passenger-realized-score-v1.2",
            first["realized_score_method_version"],
        )
        self.assertAlmostEqual(
            expected_result,
            first["realized_result_quality_score"],
            delta=0.001,
        )
        self.assertAlmostEqual(
            expected_actual,
            first["realized_report_process_quality_score"],
            delta=0.001,
        )
        self.assertEqual(
            first["realized_report_process_quality_score"],
            first["realized_report_quality_score"],
        )

    def test_ordinary_reports_do_not_follow_exact_future_values_inside_same_signal_bucket(
        self,
    ) -> None:
        variant_rows = synthetic_market_rows(
            future_demand_growth_pct=2.2,
            future_supply_growth_pct=1.9,
        )
        variant = forecast_layer.simulate_potential_passenger_forecast(
            variant_rows,
            copy.deepcopy(self.config),
        )
        ordinary_fields = (
            "forecast_effective_passengers_mid_million",
            "forecast_potential_passengers_mid_million",
            "forecast_airline_supply_passengers_mid_million",
            "forecast_narrative_headline",
            "forecast_turn_window_start_year",
            "forecast_turn_window_end_year",
        )
        baseline_by_key = {
            (row["forecast_report_id"], row["forecast_year"]): row
            for row in self.rows
            if row["as_of_year"] == 2030
        }
        variant_by_key = {
            (row["forecast_report_id"], row["forecast_year"]): row
            for row in variant
            if row["as_of_year"] == 2030
        }
        for key, baseline in baseline_by_key.items():
            changed = variant_by_key[key]
            if key[0] == "god_future_peek":
                self.assertNotEqual(
                    baseline["forecast_effective_passengers_mid_million"],
                    changed["forecast_effective_passengers_mid_million"],
                )
                continue
            for field in ordinary_fields:
                self.assertEqual(baseline[field], changed[field])

    def test_component_structure_changes_score_without_changing_total_path(self) -> None:
        variant_rows = copy.deepcopy(synthetic_market_rows())
        for row in variant_rows:
            year = int(row["year"])
            progress = max(0.0, min(1.0, (year - 2030) / 10.0))
            demand_shares = dict(SHARES)
            demand_shares["business"] += 0.05 * progress
            demand_shares["leisure"] -= 0.05 * progress
            priority = {
                "business": 1.0 + 0.35 * progress,
                "leisure": 1.0 - 0.25 * progress,
                "vfr": 1.0,
                "long_haul": 1.0 + 0.15 * progress,
                "transfer": 1.0,
            }
            potential = float(row["city_potential_passengers_million"])
            effective = float(row["city_airline_serviceable_supply_million"])
            allocation = forecast_layer.forecast_component_allocation(
                potential,
                effective,
                demand_shares,
                priority,
            )
            for component in COMPONENTS:
                row[f"{component}_passengers_million"] = allocation[component][
                    "potential"
                ]
                row[f"{component}_airline_supply_passengers_million"] = allocation[
                    component
                ]["serviceable"]
                row[f"{component}_airline_supply_priority_weight"] = priority[
                    component
                ]

        variant = forecast_layer.simulate_potential_passenger_forecast(
            variant_rows,
            copy.deepcopy(self.config),
        )
        baseline = next(
            row
            for row in self.rows
            if row["forecast_report_id"] == "public_consensus"
            and row["as_of_year"] == 2030
        )
        changed = next(
            row
            for row in variant
            if row["forecast_report_id"] == "public_consensus"
            and row["as_of_year"] == 2030
        )
        self.assertEqual(
            baseline["forecast_effective_passengers_mid_million"],
            changed["forecast_effective_passengers_mid_million"],
        )
        self.assertNotEqual(
            baseline["realized_component_result_quality_score"],
            changed["realized_component_result_quality_score"],
        )
        self.assertNotEqual(
            baseline["realized_report_process_quality_score"],
            changed["realized_report_process_quality_score"],
        )

    def test_joint_paths_respect_tier_growth_smoothing(self) -> None:
        report_config = {
            report["forecast_report_id"]: report
            for report in self.config["forecast_reports"]
        }
        for report_id, tier in report_config.items():
            if report_id == "god_future_peek":
                continue
            sample = sorted(
                (
                    row
                    for row in self.rows
                    if row["forecast_report_id"] == report_id
                    and row["as_of_year"] == 2030
                ),
                key=lambda row: row["forecast_year"],
            )
            max_change = float(tier["max_annual_growth_change_pp"]) + 0.25
            for metric, current_field in (
                (
                    "forecast_potential_passengers_mid_million",
                    "current_potential_passengers_million",
                ),
                (
                    "forecast_airline_supply_passengers_mid_million",
                    "current_airline_supply_passengers_million",
                ),
            ):
                previous_value = sample[0][current_field]
                growth_rates = []
                for row in sample:
                    growth_rates.append((row[metric] / previous_value - 1) * 100)
                    previous_value = row[metric]
                for left, right in zip(growth_rates, growth_rates[1:]):
                    self.assertLessEqual(abs(right - left), max_change)
                changes = [
                    right - left
                    for left, right in zip(growth_rates, growth_rates[1:])
                ]
                directions = [
                    1 if change > 0.10 else -1 if change < -0.10 else 0
                    for change in changes
                ]
                directions = [direction for direction in directions if direction]
                inflections = sum(
                    left != right
                    for left, right in zip(directions, directions[1:])
                )
                self.assertLessEqual(
                    inflections,
                    int(tier["max_unexplained_inflections"]),
                )

    def test_routine_vintage_updates_are_bounded_and_explained(self) -> None:
        routine_rows = [
            row
            for row in self.rows
            if row["forecast_revision_reason"] == "routine_inherited_update"
            and row["forecast_previous_mid_million"] is not None
        ]
        self.assertTrue(routine_rows)
        self.assertLessEqual(
            max(abs(row["forecast_revision_pct"]) for row in routine_rows),
            10.5,
        )
        component_revisions = [
            abs(row["forecast_component_revision_pp"])
            for row in routine_rows
        ]
        self.assertTrue(all(value > 0.0 for value in component_revisions))
        self.assertLessEqual(max(component_revisions), 1.0)

    def test_player_projection_excludes_hidden_truth_scores_and_god_report(self) -> None:
        ordinary = next(
            row for row in self.rows if row["forecast_report_id"] == "public_consensus"
        )
        player = forecast_layer.forecast_player_row(ordinary)
        self.assertIsNotNone(player)
        self.assertFalse(any(key.startswith("debug_") for key in player))
        self.assertFalse(any(key.startswith("realized_") for key in player))
        self.assertEqual("公开共识", player["forecast_narrative_style_label"])
        self.assertIn("共识跟随", player["forecast_narrative_modifier_labels"])
        self.assertTrue(player["forecast_narrative_style_method"])
        self.assertTrue(player["forecast_narrative_style_blind_spot"])
        for component in COMPONENTS:
            self.assertIn(
                f"{component}_forecast_airline_offered_capacity_million",
                player,
            )
            self.assertIn(
                f"{component}_forecast_airline_supply_fulfillment_pct",
                player,
            )
            self.assertIn(
                f"{component}_forecast_airline_supply_gap_million",
                player,
            )
            self.assertIn(
                f"{component}_forecast_effective_passengers_low_million",
                player,
            )
            self.assertIn(
                f"{component}_forecast_effective_passengers_high_million",
                player,
            )
        god = next(
            row for row in self.rows if row["forecast_report_id"] == "god_future_peek"
        )
        self.assertIsNone(forecast_layer.forecast_player_row(god))


if __name__ == "__main__":
    unittest.main()
