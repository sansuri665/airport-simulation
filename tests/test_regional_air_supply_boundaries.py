from __future__ import annotations

import unittest
from dataclasses import replace

from macro_layers.city_airport_market_demand_layer_sim import (
    CITY_MARKET_CONFIGS,
    merge_region_inputs,
    simulate_city_airport_demand,
)
from macro_layers.regional_air_capacity_supply_layer_sim import (
    AIR_SUPPLY_INTERFACE_VERSION,
    AIR_SUPPLY_PARAM_VERSION,
    AIR_SUPPLY_REGION_CONFIGS,
    simulate_region_air_supply,
)


class RegionalAirSupplyBoundaryTests(unittest.TestCase):
    @staticmethod
    def demand_rows() -> list[dict[str, object]]:
        rows = []
        for year_index, (demand_index, demand_growth) in enumerate(
            ((100.0, 0.0), (110.0, 10.0), (116.0, 5.4545))
        ):
            rows.append(
                {
                    "region_id": "china_mainland",
                    "region_name": "中国大陆",
                    "aviation_demand_scope": "test",
                    "seed": 7,
                    "year_index": year_index,
                    "year": 2025 + year_index,
                    "regional_air_demand_index": demand_index,
                    "regional_air_demand_growth_pct": demand_growth,
                    "business_travel_demand_index": demand_index,
                    "leisure_travel_demand_index": demand_index,
                    "vfr_travel_demand_index": demand_index,
                    "long_haul_demand_index": demand_index,
                    "transfer_demand_index": demand_index,
                    "airport_event_hint": "none",
                    "branch_scenario_state": "baseline",
                    "branch_effect_phase": "none",
                }
            )
        return rows

    def test_reference_passenger_amounts_are_algebraically_consistent(self) -> None:
        rows = simulate_region_air_supply(
            self.demand_rows(),
            AIR_SUPPLY_REGION_CONFIGS["china_mainland"],
        )

        self.assertEqual("regional-air-capacity-supply-layer-v0.3", AIR_SUPPLY_PARAM_VERSION)
        self.assertEqual("regional-air-capacity-supply-interface-v0.3", AIR_SUPPLY_INTERFACE_VERSION)
        for row in rows:
            potential = float(row["potential_passengers_million"])
            scheduled_seats = float(row["scheduled_seats_million"])
            availability = float(row["operational_availability_pct"])
            available_seats = float(row["available_seats_million"])
            target_load_factor = float(row["target_load_factor_pct"])
            effective_capacity = float(row["reference_effective_passenger_capacity_million"])
            served = float(row["reference_served_passengers_million"])
            unmet = float(row["reference_unmet_passengers_million"])

            self.assertAlmostEqual(available_seats, scheduled_seats * availability / 100.0, places=3)
            self.assertAlmostEqual(effective_capacity, available_seats * target_load_factor / 100.0, places=3)
            self.assertAlmostEqual(served, min(potential, effective_capacity), places=3)
            self.assertAlmostEqual(unmet, potential - served, places=3)
            self.assertAlmostEqual(float(row["load_factor_pct"]), served / available_seats * 100.0, places=3)
            self.assertAlmostEqual(float(row["capacity_fulfillment_pct"]), served / potential * 100.0, places=3)
            self.assertEqual(served, row["served_passengers_million"])
            self.assertEqual(unmet, row["unmet_passengers_million"])

    def test_reference_math_does_not_change_regional_driver_signals(self) -> None:
        params = AIR_SUPPLY_REGION_CONFIGS["china_mainland"]
        lower_reference_load_factor = replace(params, baseline_load_factor_pct=72.0)
        original = simulate_region_air_supply(self.demand_rows(), params)
        changed = simulate_region_air_supply(self.demand_rows(), lower_reference_load_factor)
        driver_fields = (
            "regional_air_capacity_index",
            "regional_air_capacity_growth_pct",
            "airline_capacity_confidence_index",
            "airline_profit_pressure_index",
            "fleet_expansion_appetite_index",
            "route_growth_appetite_index",
            "capacity_cut_risk_index",
            "aircraft_delivery_constraint_index",
            "crew_labor_constraint_index",
            "maintenance_cost_pressure_index",
            "airport_slot_constraint_index",
            "capacity_fare_pressure_index",
        )

        for original_row, changed_row in zip(original, changed, strict=True):
            for field in driver_fields:
                self.assertEqual(original_row[field], changed_row[field], field)
        self.assertNotEqual(
            original[-1]["reference_served_passengers_million"],
            changed[-1]["reference_served_passengers_million"],
        )

    def test_regional_reference_amounts_do_not_cap_beijing_city_results(self) -> None:
        demand_rows = self.demand_rows()
        supply_rows = simulate_region_air_supply(
            demand_rows,
            AIR_SUPPLY_REGION_CONFIGS["china_mainland"],
        )
        altered_reference_rows = []
        for row in supply_rows:
            altered = dict(row)
            altered["reference_served_passengers_million"] = 1.0
            altered["reference_unmet_passengers_million"] = max(
                0.0,
                float(row["potential_passengers_million"]) - 1.0,
            )
            altered["served_passengers_million"] = 1.0
            altered["unmet_passengers_million"] = altered["reference_unmet_passengers_million"]
            altered_reference_rows.append(altered)

        params = CITY_MARKET_CONFIGS["beijing_airport_system"]
        baseline = simulate_city_airport_demand(
            merge_region_inputs("china_mainland", demand_rows, supply_rows),
            params,
        )
        altered = simulate_city_airport_demand(
            merge_region_inputs("china_mainland", demand_rows, altered_reference_rows),
            params,
        )
        reference_only_fields = {
            "source_region_reference_served_passengers_million",
            "source_region_reference_unmet_passengers_million",
            "source_region_served_passengers_million",
        }

        for baseline_row, altered_row in zip(baseline, altered, strict=True):
            baseline_core = {key: value for key, value in baseline_row.items() if key not in reference_only_fields}
            altered_core = {key: value for key, value in altered_row.items() if key not in reference_only_fields}
            self.assertEqual(baseline_core, altered_core)
            self.assertEqual(1.0, altered_row["source_region_reference_served_passengers_million"])


if __name__ == "__main__":
    unittest.main()
