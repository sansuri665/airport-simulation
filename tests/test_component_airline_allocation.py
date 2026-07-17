from __future__ import annotations

import argparse
import sys
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MACRO_DIR = ROOT_DIR / "macro_layers"
if str(MACRO_DIR) not in sys.path:
    sys.path.insert(0, str(MACRO_DIR))

import macro_run_orchestrator_sim as orchestrator
from city_airport_market_demand_layer_sim import (
    COMPONENTS,
    COMPONENT_ALLOCATION_PROFILES,
    capped_weighted_allocation,
)


TOLERANCE = 0.001


class ComponentAirlineAllocationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        args = argparse.Namespace(
            years=12,
            start_year=2025,
            initial_gdp=100.0,
            volatility_scale=1.0,
            feedback_iterations=1,
        )
        global_result = orchestrator.run_global_variant(20261324, args, "baseline")
        regional = orchestrator.run_regional_and_reconciliation(
            20261324,
            global_result["rows"],
        )
        cls.city_rows_by_market = regional["city_airport_rows_by_market"]
        cls.city_rows = cls.city_rows_by_market["beijing_airport_system"]
        cls.operations_rows = regional["quarterly_operations_rows_by_market"][
            "beijing_airport_system"
        ]
        cls.forecast_rows = regional["potential_passenger_forecast_rows_by_market"][
            "beijing_airport_system"
        ]

    def test_generic_profiles_and_beijing_override_are_separate(self) -> None:
        self.assertIn("china_balanced_city_v1", COMPONENT_ALLOCATION_PROFILES)
        self.assertIn("china_dual_hub_v1", COMPONENT_ALLOCATION_PROFILES)
        params = orchestrator.CITY_MARKET_CONFIGS["beijing_airport_system"]
        self.assertEqual("china_dual_hub_v1", params.airline_component_allocation_profile_id)
        self.assertGreater(
            params.airline_component_priority_biases["business"],
            params.airline_component_priority_biases["leisure"],
        )
        self.assertEqual(
            "china_balanced_city_v1",
            orchestrator.CITY_MARKET_CONFIGS[
                "shanghai_airport_system"
            ].airline_component_allocation_profile_id,
        )

    def test_capped_weighted_allocation_conserves_total_and_respects_caps(self) -> None:
        demand = {
            "business": 20.0,
            "leisure": 40.0,
            "vfr": 15.0,
            "long_haul": 10.0,
            "transfer": 15.0,
        }
        weights = {
            "business": 30.0,
            "leisure": 25.0,
            "vfr": 10.0,
            "long_haul": 8.0,
            "transfer": 12.0,
        }
        allocated = capped_weighted_allocation(demand, weights, 65.0)
        self.assertAlmostEqual(65.0, sum(allocated.values()), places=8)
        for component in COMPONENTS:
            self.assertGreaterEqual(allocated[component], 0.0)
            self.assertLessEqual(allocated[component], demand[component])

    def test_annual_city_result_is_the_component_authority(self) -> None:
        for market_id, rows in self.city_rows_by_market.items():
            with self.subTest(market_id=market_id):
                for row in rows:
                    offered = row["city_airline_offered_capacity_million"]
                    serviceable = row["city_airline_serviceable_supply_million"]
                    unused = row["city_airline_unused_capacity_million"]
                    component_supply = sum(
                        row[f"{component}_airline_supply_passengers_million"]
                        for component in COMPONENTS
                    )
                    component_served = sum(
                        row[f"{component}_served_passengers_million"]
                        for component in COMPONENTS
                    )
                    self.assertAlmostEqual(offered, serviceable + unused, delta=TOLERANCE)
                    self.assertAlmostEqual(serviceable, component_supply, delta=TOLERANCE)
                    self.assertAlmostEqual(
                        row["city_served_passengers_million"],
                        component_served,
                        delta=TOLERANCE,
                    )
                    for component in COMPONENTS:
                        potential = row[f"{component}_passengers_million"]
                        supply = row[f"{component}_airline_supply_passengers_million"]
                        served = row[f"{component}_served_passengers_million"]
                        self.assertLessEqual(supply, potential + TOLERANCE)
                        self.assertLessEqual(served, supply + TOLERANCE)

    def test_beijing_business_supply_is_protected_relative_to_leisure(self) -> None:
        constrained = [
            row
            for row in self.city_rows
            if row["city_airline_supply_fulfillment_pct"] < 99.999
        ]
        self.assertTrue(constrained)
        business_mean = sum(
            row["business_airline_supply_fulfillment_pct"] for row in constrained
        ) / len(constrained)
        leisure_mean = sum(
            row["leisure_airline_supply_fulfillment_pct"] for row in constrained
        ) / len(constrained)
        self.assertGreater(business_mean, leisure_mean)

    def test_quarters_preserve_annual_component_supply_and_caps(self) -> None:
        city_by_year = {int(row["year"]): row for row in self.city_rows}
        operations_by_year: dict[int, list[dict[str, object]]] = {}
        for row in self.operations_rows:
            operations_by_year.setdefault(int(row["year"]), []).append(row)
            supply_total = sum(
                row[f"{component}_quarter_airline_supply_passengers_million"]
                for component in COMPONENTS
            )
            served_total = sum(
                row[f"{component}_quarter_served_passengers_million"]
                for component in COMPONENTS
            )
            self.assertAlmostEqual(
                row["quarter_airline_serviceable_supply_million"],
                supply_total,
                delta=TOLERANCE,
            )
            self.assertAlmostEqual(
                row["quarter_served_passengers_million"],
                served_total,
                delta=TOLERANCE,
            )
            for component in COMPONENTS:
                potential = row[f"{component}_quarter_potential_passengers_million"]
                supply = row[f"{component}_quarter_airline_supply_passengers_million"]
                served = row[f"{component}_quarter_served_passengers_million"]
                self.assertLessEqual(supply, potential + TOLERANCE)
                self.assertLessEqual(served, supply + TOLERANCE)

        for year, quarter_rows in operations_by_year.items():
            annual = city_by_year[year]
            for component in COMPONENTS:
                quarterly_supply = sum(
                    row[f"{component}_quarter_airline_supply_passengers_million"]
                    for row in quarter_rows
                )
                self.assertAlmostEqual(
                    annual[f"{component}_airline_supply_passengers_million"],
                    quarterly_supply,
                    delta=TOLERANCE,
                )

    def test_forecast_hidden_truth_reads_city_component_authority(self) -> None:
        city_by_year = {int(row["year"]): row for row in self.city_rows}
        for row in self.forecast_rows:
            annual = city_by_year[int(row["forecast_year"])]
            share_total = 0.0
            for component in COMPONENTS:
                true_effective = row[
                    f"{component}_debug_hidden_true_effective_passengers_million"
                ]
                authoritative = annual[f"{component}_airline_supply_passengers_million"]
                potential = row[f"{component}_debug_hidden_true_potential_passengers_million"]
                self.assertAlmostEqual(true_effective, authoritative, delta=TOLERANCE)
                self.assertLessEqual(true_effective, potential + TOLERANCE)
                share_total += row[f"{component}_debug_hidden_true_effective_share_pct"]
            self.assertAlmostEqual(100.0, share_total, delta=TOLERANCE)

    def test_forecast_uses_capped_component_allocation_for_ordinary_reports(self) -> None:
        constrained_rows = []
        for row in self.forecast_rows:
            if str(row["future_peek_mode"]).lower() == "true":
                continue
            potential_total = sum(
                row[f"{component}_forecast_potential_passengers_mid_million"]
                for component in COMPONENTS
            )
            offered_total = sum(
                row[f"{component}_forecast_airline_offered_capacity_million"]
                for component in COMPONENTS
            )
            serviceable_total = sum(
                row[f"{component}_forecast_airline_supply_passengers_mid_million"]
                for component in COMPONENTS
            )
            self.assertAlmostEqual(
                row["forecast_potential_passengers_mid_million"],
                potential_total,
                delta=TOLERANCE,
            )
            self.assertAlmostEqual(
                row["forecast_airline_supply_passengers_mid_million"],
                offered_total,
                delta=TOLERANCE,
            )
            self.assertAlmostEqual(
                row["forecast_effective_passengers_mid_million"],
                serviceable_total,
                delta=TOLERANCE,
            )
            for component in COMPONENTS:
                self.assertLessEqual(
                    row[f"{component}_forecast_airline_supply_passengers_mid_million"],
                    row[f"{component}_forecast_potential_passengers_mid_million"]
                    + TOLERANCE,
                )
            if (
                row["forecast_airline_supply_passengers_mid_million"]
                < row["forecast_potential_passengers_mid_million"]
            ):
                constrained_rows.append(row)

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


if __name__ == "__main__":
    unittest.main()
