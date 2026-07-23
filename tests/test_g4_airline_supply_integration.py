from __future__ import annotations

import argparse
import csv
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MACRO = ROOT / "macro_layers"
if str(MACRO) not in sys.path:
    sys.path.insert(0, str(MACRO))

import city_airline_supply_model as supply_model
import city_airport_market_demand_layer_sim as city_market
import macro_run_orchestrator_sim as orchestrator
from tools.audit_passenger_demand import audit_passenger_demand
from airport_sim.server import serializers

COMPONENTS = city_market.COMPONENTS
TOLERANCE = 1e-7


class G4AirlineEquilibriumChannelTests(unittest.TestCase):
    def test_capture_changes_speed_not_long_run_fixed_point(self) -> None:
        for capture in (0.55, 0.75, 0.95, 1.15):
            supply = 70.0
            for _ in range(80):
                channels = supply_model.equilibrium_channels(
                    potential_anchor_index=120.0,
                    regional_trend_index=90.0,
                    previous_supply_index=supply,
                    demand_pull_capture=capture,
                    macro_adjustment_index=2.0,
                    constraint_drag_index=3.0,
                )
                supply += (channels.captured_target_index - supply) * 0.40
            with self.subTest(capture=capture):
                self.assertAlmostEqual(119.0, supply, places=5)

    def test_initial_state_preserves_historical_channel_decomposition(self) -> None:
        channels = supply_model.equilibrium_channels(
            potential_anchor_index=130.0,
            regional_trend_index=100.0,
            previous_supply_index=None,
            demand_pull_capture=0.90,
            macro_adjustment_index=3.0,
            constraint_drag_index=2.0,
        )
        self.assertTrue(channels.is_initial_state)
        self.assertAlmostEqual(27.0, channels.captured_gap_index)
        self.assertAlmostEqual(128.0, channels.captured_target_index)
        self.assertAlmostEqual(131.0, channels.long_run_equilibrium_index)
        self.assertEqual(0.0, channels.regional_planning_signal_index)

    def test_regional_trend_is_a_bounded_signal_not_the_fixed_point(self) -> None:
        channels = supply_model.equilibrium_channels(
            potential_anchor_index=140.0,
            regional_trend_index=40.0,
            previous_supply_index=100.0,
            previous_regional_trend_index=100.0,
            demand_pull_capture=0.90,
            macro_adjustment_index=0.0,
            constraint_drag_index=0.0,
        )
        self.assertAlmostEqual(140.0, channels.long_run_equilibrium_index)
        self.assertAlmostEqual(136.0, channels.captured_target_index)
        self.assertEqual(-30.0, channels.regional_planning_signal_index)

        unchanged = supply_model.equilibrium_channels(
            potential_anchor_index=140.0,
            regional_trend_index=40.0,
            previous_supply_index=100.0,
            previous_regional_trend_index=40.0,
            demand_pull_capture=0.90,
            macro_adjustment_index=0.0,
            constraint_drag_index=0.0,
        )
        self.assertEqual(0.0, unchanged.regional_planning_signal_index)

    def test_nonfinite_and_invalid_capture_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            supply_model.equilibrium_channels(
                potential_anchor_index=100.0,
                regional_trend_index=100.0,
                previous_supply_index=100.0,
                demand_pull_capture=0.0,
                macro_adjustment_index=0.0,
                constraint_drag_index=0.0,
            )


class G4AirlineDynamicScenarioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        base = orchestrator.CITY_MARKET_CONFIGS["changsha_airport_system"]
        cls.params = replace(
            base,
            airline_supply_overexpansion_bias_pct=0.0,
            airline_supply_overcapacity_target_pct=0.0,
            airline_supply_pessimism_bias_pct=0.0,
            airline_supply_shock_amplitude_pct=0.0,
        )
        cls.base_supply = cls.params.base_airline_supply_passengers_million

    def simulate(self, potential_path: list[float], seed: int = 17) -> list[dict[str, object]]:
        state = None
        output: list[dict[str, object]] = []
        for year_index, potential in enumerate(potential_path):
            row = {
                "seed": seed,
                "year_index": year_index,
                "year": 2025 + year_index,
                "airport_event_hint": "none",
            }
            profile = city_market.city_airline_supply_profile(
                row, self.params, potential, state
            )
            state = profile["state"]
            supply = self.base_supply * float(profile["supply_index"]) / 100.0
            output.append({**profile, "potential": potential, "supply": supply})
        return output

    def test_stable_demand_has_no_mechanical_gap(self) -> None:
        rows = self.simulate([self.base_supply] * 25)
        self.assertTrue(all(abs(row["supply"] - self.base_supply) < 1e-8 for row in rows))

    def test_sustained_moderate_growth_keeps_a_lag_but_not_a_fixed_fraction_gap(self) -> None:
        potential = [self.base_supply * 1.02**year for year in range(31)]
        rows = self.simulate(potential)
        ratios = [float(row["supply"]) / float(row["potential"]) for row in rows]
        self.assertLess(min(ratios), 0.98)
        self.assertGreater(ratios[-1], 0.96)
        self.assertLess(ratios[-1], 1.01)

    def test_sudden_growth_creates_shortage_then_closes(self) -> None:
        potential = [self.base_supply] * 5 + [self.base_supply * 1.40] * 20
        rows = self.simulate(potential)
        ratios = [float(row["supply"]) / float(row["potential"]) for row in rows]
        self.assertLess(ratios[5], 0.85)
        self.assertGreater(ratios[-1], 0.995)

    def test_demand_fall_creates_idle_supply_then_contracts(self) -> None:
        potential = [self.base_supply * 1.30] * 5 + [self.base_supply * 0.90] * 20
        rows = self.simulate(potential)
        ratios = [float(row["supply"]) / float(row["potential"]) for row in rows]
        self.assertGreater(ratios[5], 1.25)
        self.assertLess(abs(ratios[-1] - 1.0), 0.01)

    def test_inverted_v_has_shortage_on_ascent_and_idle_supply_on_descent(self) -> None:
        potential = (
            [self.base_supply * (1.0 + 0.03 * year) for year in range(11)]
            + [self.base_supply * (1.30 - 0.03 * year) for year in range(1, 11)]
            + [self.base_supply] * 10
        )
        rows = self.simulate(potential)
        ratios = [float(row["supply"]) / float(row["potential"]) for row in rows]
        self.assertLess(min(ratios[:11]), 0.97)
        self.assertGreater(max(ratios[11:21]), 1.04)
        self.assertLess(abs(ratios[-1] - 1.0), 0.01)

    def test_seeded_phase_and_shock_path_remains_deterministic_and_distinct(self) -> None:
        params = orchestrator.CITY_MARKET_CONFIGS["sanya_airport_system"]

        def path(seed: int) -> list[tuple[str, float]]:
            state = None
            result = []
            for year_index in range(31):
                row = {"seed": seed, "year_index": year_index, "year": 2025 + year_index}
                profile = city_market.city_airline_supply_profile(
                    row,
                    params,
                    params.baseline_city_potential_passengers_million * 1.015**year_index,
                    state,
                )
                state = profile["state"]
                result.append((str(profile["behavior_phase"]), round(float(profile["supply_index"]), 8)))
            return result

        first = path(424242)
        self.assertEqual(first, path(424242))
        self.assertNotEqual(first, path(20260282))


class G4ComponentAndCapacityContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        args = argparse.Namespace(
            years=12,
            start_year=2025,
            initial_gdp=100.0,
            volatility_scale=1.0,
            feedback_iterations=1,
        )
        cls.global_result = orchestrator.run_global_variant(20261324, args, "baseline")
        cls.regional = orchestrator.run_regional_and_reconciliation(
            20261324, cls.global_result["rows"]
        )

    def test_component_allocation_and_airport_compression_conserve_totals(self) -> None:
        params = orchestrator.CITY_MARKET_CONFIGS["beijing_airport_system"]
        demand = {
            "business": 30.0,
            "leisure": 35.0,
            "vfr": 12.0,
            "long_haul": 10.0,
            "transfer": 13.0,
        }
        result = city_market.component_airline_service_profile(
            {}, demand, airline_supply=82.0, airport_capacity=70.0, params=params
        )
        self.assertAlmostEqual(82.0, sum(result["offered_capacity"].values()), places=8)
        self.assertAlmostEqual(82.0, sum(result["serviceable_supply"].values()), places=8)
        self.assertAlmostEqual(70.0, sum(result["final_served"].values()), places=8)
        self.assertEqual(0.0, result["unused_capacity"])
        for component in COMPONENTS:
            self.assertLessEqual(result["serviceable_supply"][component], demand[component] + TOLERANCE)
            self.assertLessEqual(result["final_served"][component], result["serviceable_supply"][component] + TOLERANCE)

    def test_unused_supply_is_nonnegative_when_demand_is_below_offer(self) -> None:
        params = orchestrator.CITY_MARKET_CONFIGS["shanghai_airport_system"]
        demand = {component: 5.0 for component in COMPONENTS}
        result = city_market.component_airline_service_profile(
            {}, demand, airline_supply=40.0, airport_capacity=100.0, params=params
        )
        self.assertAlmostEqual(25.0, result["serviceable_total"], places=8)
        self.assertAlmostEqual(15.0, result["unused_capacity"], places=8)
        self.assertAlmostEqual(25.0, sum(result["final_served"].values()), places=8)

    def test_real_chain_uses_minimum_of_demand_supply_and_airport_capacity(self) -> None:
        for market_id, rows in self.regional["city_airport_rows_by_market"].items():
            for row in rows:
                with self.subTest(market=market_id, year=row["year"]):
                    expected = min(
                        float(row["city_potential_passengers_million"]),
                        float(row["city_airline_serviceable_supply_million"]),
                        float(row["city_effective_capacity_million"]),
                    )
                    self.assertAlmostEqual(expected, float(row["city_served_passengers_million"]), places=7)
                    self.assertGreaterEqual(float(row["city_unmet_passengers_million"]), 0.0)
                    self.assertGreaterEqual(float(row["city_airline_unused_capacity_million"]), 0.0)

    def test_beijing_annual_to_quarterly_supply_and_served_totals_conserve(self) -> None:
        city_rows = self.regional["city_airport_rows_by_market"]["beijing_airport_system"]
        operations_rows = self.regional["quarterly_operations_rows_by_market"][
            "beijing_airport_system"
        ]
        city_by_year = {int(row["year"]): row for row in city_rows}
        operations_by_year: dict[int, list[dict[str, object]]] = {}
        for row in operations_rows:
            operations_by_year.setdefault(int(row["year"]), []).append(row)
            component_served = sum(
                float(row[f"{component}_quarter_served_passengers_million"])
                for component in COMPONENTS
            )
            self.assertAlmostEqual(
                float(row["quarter_served_passengers_million"]),
                component_served,
                delta=2e-4,
            )

        for year, quarter_rows in operations_by_year.items():
            annual = city_by_year[year]
            self.assertAlmostEqual(
                float(annual["city_served_passengers_million"]),
                sum(float(row["quarter_served_passengers_million"]) for row in quarter_rows),
                delta=2e-4,
            )
            self.assertAlmostEqual(
                float(annual["city_airline_serviceable_supply_million"]),
                sum(
                    float(row["quarter_airline_serviceable_supply_million"])
                    for row in quarter_rows
                ),
                delta=2e-4,
            )
            for component in COMPONENTS:
                self.assertAlmostEqual(
                    float(annual[f"{component}_airline_supply_passengers_million"]),
                    sum(
                        float(
                            row[f"{component}_quarter_airline_supply_passengers_million"]
                        )
                        for row in quarter_rows
                    ),
                    delta=2e-4,
                )

    def test_forecast_hidden_truth_uses_authoritative_component_supply(self) -> None:
        city_rows = self.regional["city_airport_rows_by_market"]["beijing_airport_system"]
        forecasts = self.regional["potential_passenger_forecast_rows_by_market"][
            "beijing_airport_system"
        ]
        city_by_year = {int(row["year"]): row for row in city_rows}
        for forecast in forecasts:
            annual = city_by_year[int(forecast["forecast_year"])]
            for component in COMPONENTS:
                self.assertAlmostEqual(
                    float(
                        forecast[
                            f"{component}_debug_hidden_true_effective_passengers_million"
                        ]
                    ),
                    float(annual[f"{component}_airline_supply_passengers_million"]),
                    delta=TOLERANCE,
                )

    def test_api_serializer_keeps_potential_offered_serviceable_and_served_distinct(self) -> None:
        rows = self.regional["city_airport_rows_by_market"]["beijing_airport_system"]
        summary = serializers.summarize_city(rows)
        final_row = rows[-1]
        final_point = summary["points"][-1]
        self.assertEqual(
            round(float(final_row["city_potential_passengers_million"]), 4),
            final_point["potential"],
        )
        self.assertEqual(
            round(float(final_row["city_airline_offered_capacity_million"]), 4),
            final_point["airlineOffered"],
        )
        self.assertEqual(
            round(float(final_row["city_airline_supply_passengers_million"]), 4),
            final_point["airlineSupply"],
        )
        self.assertEqual(
            round(float(final_row["city_airline_serviceable_supply_million"]), 4),
            final_point["serviceable"],
        )
        self.assertEqual(
            round(float(final_row["city_served_passengers_million"]), 4),
            final_point["served"],
        )
        for component in COMPONENTS:
            component_point = final_point["components"][component]
            self.assertEqual(
                round(float(final_row[f"{component}_passengers_million"]), 4),
                component_point["potential"],
            )
            self.assertEqual(
                round(
                    float(
                        final_row[f"{component}_airline_offered_capacity_million"]
                    ),
                    4,
                ),
                component_point["offeredCapacity"],
            )
            self.assertEqual(
                round(
                    float(final_row[f"{component}_airline_supply_passengers_million"]),
                    4,
                ),
                component_point["airlineSupply"],
            )
            self.assertEqual(
                round(float(final_row[f"{component}_served_passengers_million"]), 4),
                component_point["served"],
            )

    def test_short_run_is_strict_prefix_of_long_run_for_supply_fields(self) -> None:
        short_args = argparse.Namespace(
            years=6,
            start_year=2025,
            initial_gdp=100.0,
            volatility_scale=1.0,
            feedback_iterations=1,
        )
        short_global = orchestrator.run_global_variant(424242, short_args, "baseline")
        short = orchestrator.run_regional_and_reconciliation(
            424242, short_global["rows"]
        )
        long_args = argparse.Namespace(
            years=12,
            start_year=2025,
            initial_gdp=100.0,
            volatility_scale=1.0,
            feedback_iterations=1,
        )
        long_global = orchestrator.run_global_variant(424242, long_args, "baseline")
        long = orchestrator.run_regional_and_reconciliation(424242, long_global["rows"])
        fields = (
            "city_airline_offered_capacity_million",
            "city_airline_serviceable_supply_million",
            "city_airline_unused_capacity_million",
            "city_served_passengers_million",
            "city_binding_bottleneck",
            *(f"{component}_airline_offered_capacity_million" for component in COMPONENTS),
            *(f"{component}_airline_supply_passengers_million" for component in COMPONENTS),
            *(f"{component}_served_passengers_million" for component in COMPONENTS),
        )
        for market_id, short_rows in short["city_airport_rows_by_market"].items():
            long_rows = long["city_airport_rows_by_market"][market_id]
            for short_row, long_row in zip(short_rows, long_rows):
                with self.subTest(market=market_id, year=short_row["year"]):
                    for field in fields:
                        self.assertEqual(short_row[field], long_row[field])


class G4AuditContractTests(unittest.TestCase):
    @staticmethod
    def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)

    def make_input(
        self,
        root: Path,
        *,
        break_offered_identity: bool = False,
        break_served_identity: bool = False,
    ) -> Path:
        regional_demand_fields = [
            "regional_aviation_demand_param_version",
            "regional_aviation_demand_interface_version",
            "region_id",
            "region_name",
            "year_index",
            "year",
            "seed",
            "business_travel_share_pct",
            "leisure_travel_share_pct",
            "vfr_travel_share_pct",
            "long_haul_share_pct",
            "transfer_share_pct",
        ]
        regional_supply_fields = [
            "regional_air_supply_param_version",
            "regional_air_supply_interface_version",
            "region_id",
            "region_name",
            "year_index",
            "year",
            "seed",
            "potential_passengers_million",
            "reference_effective_passenger_capacity_million",
            "reference_served_passengers_million",
            "reference_unmet_passengers_million",
        ]
        city_fields = [
            "city_airport_demand_param_version",
            "city_airport_demand_interface_version",
            "city_airport_market_id",
            "city_name",
            "region_id",
            "region_name",
            "year_index",
            "year",
            "seed",
            "baseline_region_demand_share_pct",
            "source_region_reference_potential_passengers_million",
            "city_potential_passengers_million",
            "city_effective_capacity_million",
            "city_airline_offered_capacity_million",
            "city_airline_serviceable_supply_million",
            "city_airline_unused_capacity_million",
            "city_airline_supply_fulfillment_pct",
            "city_served_passengers_million",
            "city_unmet_passengers_million",
            "city_binding_bottleneck",
            "airline_supply_dynamics_profile_id",
            "airline_supply_dynamics_modifier_ids",
            "airline_component_allocation_profile_id",
            "city_airline_supply_behavior_phase",
            *(f"{component}_city_demand_index" for component in COMPONENTS),
            *(f"{component}_passenger_share_pct" for component in COMPONENTS),
            *(f"{component}_passengers_million" for component in COMPONENTS),
            *(f"{component}_airline_offered_capacity_million" for component in COMPONENTS),
            *(f"{component}_airline_supply_passengers_million" for component in COMPONENTS),
            *(f"{component}_airline_supply_fulfillment_pct" for component in COMPONENTS),
            *(f"{component}_airline_supply_gap_million" for component in COMPONENTS),
            *(f"{component}_served_passengers_million" for component in COMPONENTS),
        ]
        demand_rows = []
        supply_rows = []
        city_rows = []
        for index in range(3):
            demand_rows.append(
                {
                    "regional_aviation_demand_param_version": "demand-test-v1",
                    "regional_aviation_demand_interface_version": "demand-interface-test-v1",
                    "region_id": "test_region",
                    "region_name": "测试区域",
                    "year_index": index,
                    "year": 2025 + index,
                    "seed": 7,
                    "business_travel_share_pct": 20,
                    "leisure_travel_share_pct": 20,
                    "vfr_travel_share_pct": 20,
                    "long_haul_share_pct": 20,
                    "transfer_share_pct": 20,
                }
            )
            supply_rows.append(
                {
                    "regional_air_supply_param_version": "supply-test-v1",
                    "regional_air_supply_interface_version": "supply-interface-test-v1",
                    "region_id": "test_region",
                    "region_name": "测试区域",
                    "year_index": index,
                    "year": 2025 + index,
                    "seed": 7,
                    "potential_passengers_million": 100,
                    "reference_effective_passenger_capacity_million": 90,
                    "reference_served_passengers_million": 90,
                    "reference_unmet_passengers_million": 10,
                }
            )
            row: dict[str, object] = {
                "city_airport_demand_param_version": "city-test-v1",
                "city_airport_demand_interface_version": "city-interface-test-v1",
                "city_airport_market_id": "test_city",
                "city_name": "测试城市",
                "region_id": "test_region",
                "region_name": "测试区域",
                "year_index": index,
                "year": 2025 + index,
                "seed": 7,
                "baseline_region_demand_share_pct": 60,
                "source_region_reference_potential_passengers_million": 100,
                "city_potential_passengers_million": 60,
                "city_effective_capacity_million": 50,
                "city_airline_offered_capacity_million": 56 if break_offered_identity and index == 1 else 55,
                "city_airline_serviceable_supply_million": 55,
                "city_airline_unused_capacity_million": 0,
                "city_airline_supply_fulfillment_pct": 91.6666667,
                "city_served_passengers_million": 50,
                "city_unmet_passengers_million": 10,
                "city_binding_bottleneck": "airport_bottleneck",
                "airline_supply_dynamics_profile_id": "test_profile",
                "airline_supply_dynamics_modifier_ids": "",
                "airline_component_allocation_profile_id": "test_allocation",
                "city_airline_supply_behavior_phase": "balanced",
            }
            for component in COMPONENTS:
                row[f"{component}_city_demand_index"] = 100
                row[f"{component}_passenger_share_pct"] = 20
                row[f"{component}_passengers_million"] = 12
                row[f"{component}_airline_offered_capacity_million"] = 11
                row[f"{component}_airline_supply_passengers_million"] = 11
                row[f"{component}_airline_supply_fulfillment_pct"] = 91.6666667
                row[f"{component}_airline_supply_gap_million"] = 1
                row[f"{component}_served_passengers_million"] = (
                    11 if break_served_identity and index == 1 and component == "business" else 10
                )
            city_rows.append(row)

        self.write_csv(
            root / "regional_aviation_demand/test_region_aviation_demand_seed_sweep.csv",
            regional_demand_fields,
            demand_rows,
        )
        self.write_csv(
            root / "regional_air_capacity_supply/test_region_air_capacity_supply_seed_sweep.csv",
            regional_supply_fields,
            supply_rows,
        )
        self.write_csv(
            root / "city_airport_market_demand/test_city_city_airport_demand_seed_sweep.csv",
            city_fields,
            city_rows,
        )
        return root

    def test_audit_reports_g4_supply_accounting_and_streaks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            audit = audit_passenger_demand(self.make_input(Path(temporary) / "sample"))
        integration = audit["supply_and_capacity"]["city_airline_integration"]
        self.assertEqual("supported", integration["status"])
        self.assertTrue(integration["all_accounting_checks_passed"])
        self.assertEqual(3, integration["maximum_city_streaks"]["below_95_pct_years"])
        self.assertAlmostEqual(
            91.6666667,
            integration["terminal_fulfillment_distribution_pct"]["median"],
            places=6,
        )


    def test_audit_detects_component_served_total_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            audit = audit_passenger_demand(
                self.make_input(Path(temporary) / "sample", break_served_identity=True)
            )
        integration = audit["supply_and_capacity"]["city_airline_integration"]
        self.assertFalse(integration["all_accounting_checks_passed"])
        checks = {item["check_name"]: item for item in integration["accounting_checks"]}
        self.assertEqual(
            1,
            checks["component_served_sum_equals_city_served"]["failure_count"],
        )

    def test_audit_detects_offered_serviceable_unused_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            audit = audit_passenger_demand(
                self.make_input(Path(temporary) / "sample", break_offered_identity=True)
            )
        integration = audit["supply_and_capacity"]["city_airline_integration"]
        self.assertFalse(integration["all_accounting_checks_passed"])
        checks = {item["check_name"]: item for item in integration["accounting_checks"]}
        self.assertEqual(
            1,
            checks["city_airline_offered_equals_serviceable_plus_unused"]["failure_count"],
        )


if __name__ == "__main__":
    unittest.main()
