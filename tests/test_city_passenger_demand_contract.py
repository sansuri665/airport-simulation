from __future__ import annotations

import argparse
from dataclasses import replace
import math
import sys
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MACRO_DIR = ROOT_DIR / "macro_layers"
if str(MACRO_DIR) not in sys.path:
    sys.path.insert(0, str(MACRO_DIR))

import macro_run_orchestrator_sim as orchestrator
from city_airport_market_demand_layer_sim import (
    CITY_AIRPORT_DEMAND_FIELDS,
    CITY_MARKET_CONFIGS,
    COMPONENTS,
    city_component_passengers,
    simulate_city_airport_demand,
)
from city_passenger_demand_model import (
    CITY_INDEX_BOUNDARIES,
    advance_boundary_streak,
    bounded_long_term_factor,
    component_boundary_diagnostic,
    component_passenger_volumes,
    component_relative_diagnostics,
    city_total_potential,
    normalized_component_shares,
    regional_total_factor,
)


def demand_row(
    *,
    total: float = 100.0,
    components: dict[str, float] | None = None,
    year_index: int = 0,
    seed: int = 7,
    **overrides: object,
) -> dict[str, object]:
    values = components or {component: total for component in COMPONENTS}
    row: dict[str, object] = {
        "seed": seed,
        "year_index": year_index,
        "year": 2025 + year_index,
        "regional_air_demand_index": total,
        "regional_air_demand_growth_pct": 0.0,
        "business_travel_demand_index": values["business"],
        "leisure_travel_demand_index": values["leisure"],
        "vfr_travel_demand_index": values["vfr"],
        "long_haul_demand_index": values["long_haul"],
        "transfer_demand_index": values["transfer"],
        "supply_potential_passengers_million": 820.0,
        "supply_reference_served_passengers_million": 700.0,
        "supply_reference_unmet_passengers_million": 120.0,
        "airport_event_hint": "none",
        "branch_scenario_state": "baseline",
        "branch_effect_phase": "none",
    }
    row.update(overrides)
    return row


def demand_projection(row: dict[str, object], market_id: str = "beijing_airport_system") -> dict[str, object]:
    params = CITY_MARKET_CONFIGS[market_id]
    indices, passengers, shares, seed_profile, diagnostics = city_component_passengers(row, params)
    return {
        "indices": indices,
        "passengers": passengers,
        "shares": shares,
        "seed_multiplier": seed_profile["potential_multiplier"],
        "diagnostics": diagnostics,
        "total": sum(passengers.values()),
    }


class CityPassengerDemandPureContractTests(unittest.TestCase):
    def test_common_growth_enters_total_once_and_does_not_change_structure(self) -> None:
        baseline = demand_projection(demand_row(total=100.0))
        for total_index in (120.0, 300.0, 600.0):
            with self.subTest(total_index=total_index):
                scaled = demand_projection(demand_row(total=total_index))
                self.assertAlmostEqual(
                    baseline["total"] * regional_total_factor(total_index),
                    scaled["total"],
                    places=10,
                )
                self.assertEqual(baseline["shares"], scaled["shares"])
                self.assertEqual(baseline["indices"], scaled["indices"])
        self.assertAlmostEqual(1.2, regional_total_factor(120.0))
        self.assertGreater(regional_total_factor(600.0), regional_total_factor(300.0))
        self.assertGreater(
            regional_total_factor(600.0) / regional_total_factor(300.0),
            1.2,
        )
        self.assertLess(regional_total_factor(600.0), 6.0)
        self.assertGreater(regional_total_factor(10_000.0), regional_total_factor(600.0))

    def test_city_long_term_factor_uses_explicit_common_elasticity(self) -> None:
        self.assertAlmostEqual(1.42**0.40, bounded_long_term_factor(60, 0.7, 42.0))
        self.assertAlmostEqual(0.80**0.40, bounded_long_term_factor(20, -1.0, 35.0))

    def test_pure_structure_changes_shares_not_city_total(self) -> None:
        neutral = demand_projection(demand_row(total=100.0))
        shifted = demand_projection(
            demand_row(
                total=100.0,
                components={
                    "business": 125.0,
                    "leisure": 80.0,
                    "vfr": 100.0,
                    "long_haul": 115.0,
                    "transfer": 75.0,
                },
            )
        )
        self.assertAlmostEqual(neutral["total"], shifted["total"], places=10)
        self.assertGreater(shifted["shares"]["business"], neutral["shares"]["business"])
        self.assertGreater(shifted["shares"]["long_haul"], neutral["shares"]["long_haul"])
        self.assertLess(shifted["shares"]["leisure"], neutral["shares"]["leisure"])
        self.assertLess(shifted["shares"]["transfer"], neutral["shares"]["transfer"])

    def test_component_accounting_is_exact_before_csv_rounding(self) -> None:
        result = demand_projection(
            demand_row(
                total=137.0,
                components={
                    "business": 151.0,
                    "leisure": 122.0,
                    "vfr": 144.0,
                    "long_haul": 130.0,
                    "transfer": 118.0,
                },
                year_index=31,
                seed=42,
            )
        )
        self.assertAlmostEqual(100.0, sum(result["shares"].values()), places=12)
        self.assertAlmostEqual(result["total"], sum(result["passengers"].values()), places=12)
        self.assertTrue(all(value >= 0.0 for value in result["passengers"].values()))

    def test_reference_quantities_and_legacy_ratio_are_diagnostic_only(self) -> None:
        row_a = demand_row(supply_potential_passengers_million=820.0)
        row_b = demand_row(supply_potential_passengers_million=1640.0)
        params = CITY_MARKET_CONFIGS["beijing_airport_system"]
        changed_ratio = replace(params, baseline_region_demand_share_pct=99.0)
        a = city_component_passengers(row_a, params)
        b = city_component_passengers(row_b, params)
        c = city_component_passengers(row_a, changed_ratio)
        self.assertEqual(a[:3], b[:3])
        self.assertEqual(a[:3], c[:3])

    def test_city_configurations_create_directional_bounded_structure(self) -> None:
        upstream = demand_row(total=100.0)
        beijing = demand_projection(upstream, "beijing_airport_system")
        guilin = demand_projection(upstream, "guilin_airport_system")
        chengdu = demand_projection(upstream, "chengdu_airport_system")
        self.assertGreater(beijing["shares"]["business"], guilin["shares"]["business"])
        self.assertGreater(guilin["shares"]["leisure"], beijing["shares"]["leisure"])
        self.assertGreater(chengdu["shares"]["transfer"], beijing["shares"]["transfer"])
        for result in (beijing, guilin, chengdu):
            self.assertAlmostEqual(100.0, sum(result["shares"].values()), places=12)
            self.assertTrue(all(0.0 <= value <= 100.0 for value in result["shares"].values()))

    def test_seed_is_deterministic_bounded_distinguishable_and_prefix_stable(self) -> None:
        def path(seed: int, years: int) -> list[tuple[float, tuple[float, ...]]]:
            output = []
            for year_index in range(years + 1):
                result = demand_projection(demand_row(year_index=year_index, seed=seed))
                output.append(
                    (
                        float(result["seed_multiplier"]),
                        tuple(result["passengers"][component] for component in COMPONENTS),
                    )
                )
            return output

        full = path(111111, 60)
        self.assertEqual(full, path(111111, 60))
        self.assertEqual(full[:1], path(111111, 0))
        self.assertEqual(full[:2], path(111111, 1))
        self.assertEqual(full[:3], path(111111, 2))
        other = path(222222, 60)
        self.assertNotEqual(full[-1], other[-1])
        params = CITY_MARKET_CONFIGS["beijing_airport_system"]
        for multiplier, _ in full + other:
            self.assertGreaterEqual(multiplier, params.seed_potential_multiplier_floor)
            self.assertLessEqual(multiplier, params.seed_potential_multiplier_ceiling)

    def test_full_city_simulation_is_prefix_stable_without_sequential_rng(self) -> None:
        params = CITY_MARKET_CONFIGS["beijing_airport_system"]
        rows = [demand_row(year_index=index, seed=314159) for index in range(11)]
        full = simulate_city_airport_demand(rows, params)
        for years in (0, 1, 2, 10):
            with self.subTest(years=years):
                short = simulate_city_airport_demand(rows[: years + 1], params)
                self.assertEqual(full[: years + 1], short)

    def test_event_labels_are_not_consumed_twice_by_city_demand(self) -> None:
        baseline = demand_projection(demand_row())
        labeled = demand_projection(
            demand_row(
                airport_event_hint="broad_travel_recovery",
                branch_scenario_state="occurred",
                branch_effect_phase="impact",
            )
        )
        self.assertEqual(baseline, labeled)

    def test_true_boundary_diagnostics_and_streak_reset(self) -> None:
        params = CITY_MARKET_CONFIGS["beijing_airport_system"]
        rows = [
            demand_row(components={**{c: 100.0 for c in COMPONENTS}, "business": value}, year_index=index)
            for index, value in enumerate((100.0, 300.0, 300.0, 100.0, 1.0))
        ]
        output = simulate_city_airport_demand(rows, params)
        observed = [
            (
                row["business_city_demand_raw_index"],
                row["business_city_demand_index"],
                row["business_city_demand_boundary_state"],
                row["business_city_demand_floor_applied"],
                row["business_city_demand_cap_applied"],
                row["business_city_demand_consecutive_boundary_years"],
            )
            for row in output
        ]
        self.assertEqual(
            [
                (100.0, 100.0, "none", 0, 0, 0),
                (300.0, 245.0, "cap", 0, 1, 1),
                (300.0, 245.0, "cap", 0, 1, 2),
                (100.0, 100.0, "none", 0, 0, 0),
                (1.0, 65.0, "floor", 1, 0, 1),
            ],
            observed,
        )

    def test_extreme_inputs_remain_finite_nonnegative_and_conserved(self) -> None:
        diagnostics = component_relative_diagnostics(
            regional_total_index=1.0e308,
            regional_component_indices={
                "business": 1.0e308,
                "leisure": 1.0,
                "vfr": 1.0e307,
                "long_haul": 1.0e-300,
                "transfer": 1.0e308,
            },
            city_response_elasticities={component: 2.0 for component in COMPONENTS},
        )
        shares = normalized_component_shares(
            base_shares_pct={component: 20.0 for component in COMPONENTS},
            diagnostics=diagnostics,
        )
        total = city_total_potential(
            baseline_million=100.0,
            regional_total_index=1.0e308,
            long_term_factor=5.0,
            seed_relative_factor=5.0,
        )
        passengers = component_passenger_volumes(total, shares)
        self.assertTrue(math.isfinite(total))
        self.assertGreaterEqual(total, 0.0)
        self.assertAlmostEqual(100.0, sum(shares.values()), places=12)
        self.assertTrue(
            math.isclose(
                total,
                sum(passengers.values()),
                rel_tol=1.0e-12,
                abs_tol=1.0e-9,
            )
        )
        for component, diagnostic in diagnostics.items():
            lower, upper = CITY_INDEX_BOUNDARIES[component]
            self.assertTrue(math.isfinite(diagnostic.raw_index))
            self.assertGreaterEqual(diagnostic.final_index, lower)
            self.assertLessEqual(diagnostic.final_index, upper)

    def test_all_47_configs_load_and_base_shares_sum_to_100(self) -> None:
        self.assertEqual(47, len(CITY_MARKET_CONFIGS))
        for market_id, params in CITY_MARKET_CONFIGS.items():
            with self.subTest(market_id=market_id):
                shares = (
                    params.business_base_share_pct,
                    params.leisure_base_share_pct,
                    params.vfr_base_share_pct,
                    params.long_haul_base_share_pct,
                    params.transfer_base_share_pct,
                )
                self.assertAlmostEqual(100.0, sum(shares), places=10)
                self.assertTrue(all(value > 0.0 for value in shares))

    def test_new_diagnostic_fields_are_exported_without_removing_old_indices(self) -> None:
        for component in COMPONENTS:
            self.assertIn(f"{component}_city_demand_index", CITY_AIRPORT_DEMAND_FIELDS)
            self.assertIn(f"{component}_city_demand_raw_index", CITY_AIRPORT_DEMAND_FIELDS)
            self.assertIn(f"{component}_city_demand_boundary_state", CITY_AIRPORT_DEMAND_FIELDS)
            self.assertIn(f"{component}_city_demand_floor_applied", CITY_AIRPORT_DEMAND_FIELDS)
            self.assertIn(f"{component}_city_demand_cap_applied", CITY_AIRPORT_DEMAND_FIELDS)
            self.assertIn(
                f"{component}_city_demand_consecutive_boundary_years",
                CITY_AIRPORT_DEMAND_FIELDS,
            )


class CityPassengerDemandPublicPathTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        args = argparse.Namespace(
            years=60,
            start_year=2025,
            initial_gdp=100.0,
            volatility_scale=1.0,
            feedback_iterations=1,
        )
        global_result = orchestrator.run_global_variant(424242, args, "baseline")
        regional = orchestrator.run_regional_and_reconciliation(424242, global_result["rows"])
        cls.rows_by_market = regional["city_airport_rows_by_market"]

    def test_representative_60_year_path_is_not_shaped_by_exact_boundaries(self) -> None:
        self.assertEqual(47, len(self.rows_by_market))
        for market_id, rows in self.rows_by_market.items():
            with self.subTest(market_id=market_id):
                self.assertEqual(61, len(rows))
                for component in COMPONENTS:
                    states = [row[f"{component}_city_demand_boundary_state"] for row in rows]
                    self.assertNotIn("floor", states)
                    self.assertNotIn("cap", states)
                    self.assertEqual(
                        0,
                        max(row[f"{component}_city_demand_consecutive_boundary_years"] for row in rows),
                    )


if __name__ == "__main__":
    unittest.main()
