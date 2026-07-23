from __future__ import annotations

import math
import random
import unittest
from dataclasses import fields, replace
from pathlib import Path

from macro_layers import regional_aviation_demand_layer_sim as demand


COMPONENTS = ("business", "leisure", "vfr", "long_haul", "transfer")
INDEX_FIELDS = {
    "business": "business_travel_demand_index",
    "leisure": "leisure_travel_demand_index",
    "vfr": "vfr_travel_demand_index",
    "long_haul": "long_haul_demand_index",
    "transfer": "transfer_demand_index",
}
GROWTH_FIELDS = {
    "business": "business_travel_growth_pct",
    "leisure": "leisure_travel_growth_pct",
    "vfr": "vfr_travel_growth_pct",
    "long_haul": "long_haul_growth_pct",
    "transfer": "transfer_growth_pct",
}
SHARE_FIELDS = {
    "business": "business_travel_share_pct",
    "leisure": "leisure_travel_share_pct",
    "vfr": "vfr_travel_share_pct",
    "long_haul": "long_haul_share_pct",
    "transfer": "transfer_share_pct",
}
ELASTICITY_FIELDS = {
    "business": "business_fare_elasticity_base",
    "leisure": "leisure_fare_elasticity_base",
    "vfr": "vfr_fare_elasticity_base",
    "long_haul": "long_haul_fare_elasticity_base",
    "transfer": "transfer_fare_elasticity_base",
}


def neutral_row(year_index: int, *, seed: int = 17, **overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "seed": seed,
        "year_index": year_index,
        "year": 2025 + year_index,
        "reconciliation_scope": "test",
        "regional_reconciled_gdp_trillion_usd": 10.0,
        "regional_gdp_growth_pct_reconciled": 2.0,
        "regional_potential_growth_pct": 2.0,
        "real_income_growth_pct": 0.0,
        "regional_income_index": 100.0,
        "consumer_confidence_index": 50.0,
        "regional_headline_inflation_pct_reconciled": 2.4,
        "currency_pressure_index": 35.0,
        "regional_macro_stress_index_reconciled": 35.0,
        "regional_hy_spread_bps_reconciled": 480.0,
        "regional_credit_availability_index": 55.0,
        "regional_equity_return_pct_reconciled": 0.0,
        "regional_equity_valuation_pe_reconciled": 17.0,
        "regional_wealth_effect_index": 50.0,
        "regional_energy_cost_pressure_index_reconciled": 50.0,
        "regional_risk_appetite_index": 50.0,
        "regional_geopolitical_risk_index": 25.0,
        "regional_seed_momentum_label": "neutral",
        "regional_seed_effective_growth_bias_pct": 0.0,
        "regional_seed_aviation_propensity_bias_pct": 0.0,
        "regional_seed_investment_cycle_bias_pct": 0.0,
        "regional_seed_openness_bias_pct": 0.0,
        "regional_seed_demand_multiplier": 1.0,
        "branch_scenario_id": "none",
        "branch_scenario_state": "baseline",
        "branch_effect_phase": "none",
        "regional_branch_transmission_active": "false",
        "regional_branch_strength_index": 0.0,
        "regional_branch_growth_impulse_pct": 0.0,
        "regional_branch_credit_impulse_bps": 0.0,
        "regional_branch_fx_pressure_impulse": 0.0,
        "regional_branch_energy_impulse": 0.0,
        "regional_branch_asset_impulse_pct": 0.0,
        "regional_branch_confidence_impulse": 0.0,
        "regional_branch_tail_scarring_index": 0.0,
    }
    row.update(overrides)
    return row


def metrics(**overrides: float) -> dict[str, float]:
    result = demand.input_metrics(neutral_row(1))
    result.update(overrides)
    return result


def target(metrics_value: dict[str, float], params: demand.RegionalAviationDemandParams) -> dict[str, float]:
    price = demand.price_sensitivity(metrics_value, params)
    return demand.target_component_growth(metrics_value, params, price, 0.0)



class RegionalAviationDemandInterfaceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.params = demand.AVIATION_REGION_CONFIGS["china_mainland"]

    def test_interface_versions_fields_and_first_row_are_stable(self) -> None:
        self.assertEqual("regional-aviation-demand-layer-v0.3", demand.AVIATION_DEMAND_PARAM_VERSION)
        self.assertEqual("regional-aviation-demand-interface-v0.2", demand.AVIATION_DEMAND_INTERFACE_VERSION)
        self.assertEqual(66, len(demand.AVIATION_DEMAND_FIELDS))
        self.assertEqual("regional_aviation_demand_param_version", demand.AVIATION_DEMAND_FIELDS[0])
        self.assertEqual("input_equity_valuation_pe", demand.AVIATION_DEMAND_FIELDS[-1])

        first = demand.simulate_region_aviation_demand([neutral_row(0)], self.params)[0]
        weights = demand.component_weights(self.params)
        self.assertEqual(100.0, first["regional_air_demand_index"])
        self.assertEqual(0.0, first["regional_air_demand_growth_pct"])
        for component in COMPONENTS:
            self.assertEqual(100.0, first[INDEX_FIELDS[component]])
            self.assertEqual(0.0, first[GROWTH_FIELDS[component]])
            self.assertAlmostEqual(weights[component] * 100.0, first[SHARE_FIELDS[component]], places=8)
        self.assertAlmostEqual(100.0, sum(first[field] for field in SHARE_FIELDS.values()), places=8)

    def test_determinism_rng_non_consumption_and_prefix_contract(self) -> None:
        rows = [neutral_row(i, seed=999, regional_seed_aviation_propensity_bias_pct=0.4) for i in range(15)]
        random.seed(4312)
        before = random.getstate()
        first = demand.simulate_region_aviation_demand(rows, self.params)
        after = random.getstate()
        second = demand.simulate_region_aviation_demand(rows, self.params)
        prefix = demand.simulate_region_aviation_demand(rows[:6], self.params)
        self.assertEqual(before, after)
        self.assertEqual(first, second)
        self.assertEqual(prefix, first[:6])

    def test_demand_growth_persistence_removed_instead_of_overlapping_speed(self) -> None:
        self.assertNotIn("demand_growth_persistence", {field.name for field in fields(type(self.params))})


class RegionalAviationDemandDecompositionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.params = demand.AVIATION_REGION_CONFIGS["china_mainland"]

    def test_neutral_sixty_year_path_has_no_mechanical_mix_rotation(self) -> None:
        rows = demand.simulate_region_aviation_demand([neutral_row(i) for i in range(61)], self.params)
        for component in COMPONENTS:
            drift = rows[-1][SHARE_FIELDS[component]] - rows[0][SHARE_FIELDS[component]]
            self.assertLessEqual(abs(drift), 0.5, component)
        self.assertAlmostEqual(rows[-1]["transfer_share_pct"], rows[0]["transfer_share_pct"], places=8)

    def test_centered_relative_adjustments_are_weight_neutral(self) -> None:
        raw = {"business": 2.0, "leisure": -1.0, "vfr": 0.4, "long_haul": -0.3, "transfer": 0.8}
        centered = demand.center_relative_component_adjustments(raw, self.params)
        self.assertAlmostEqual(0.0, demand.weighted_component_average(centered, self.params), places=12)
        self.assertGreater(centered["business"], centered["leisure"])

        scenario = metrics(income_growth=2.0, confidence=60.0)
        low = replace(self.params, tourism_exposure=0.20)
        high = replace(self.params, tourism_exposure=0.90)
        low_target = target(scenario, low)
        high_target = target(scenario, high)
        self.assertGreater(high_target["leisure"], low_target["leisure"])
        self.assertAlmostEqual(
            demand.weighted_component_average(low_target, low),
            demand.weighted_component_average(high_target, high),
            places=10,
        )

    def test_growth_surprise_is_symmetric_and_not_double_counted(self) -> None:
        neutral = metrics(growth=2.0, potential=2.0)
        positive = metrics(growth=4.0, potential=2.0)
        negative = metrics(growth=0.0, potential=2.0)
        price = demand.price_sensitivity(neutral, self.params)
        center = demand.common_total_growth(neutral, self.params, price, 0.0)
        above = demand.common_total_growth(positive, self.params, price, 0.0)
        below = demand.common_total_growth(negative, self.params, price, 0.0)
        self.assertGreater(above, center)
        self.assertLess(below, center)
        self.assertAlmostEqual(above - center, center - below, places=12)
        self.assertLess(above - center, 1.5)
        self.assertGreater(above - center, 0.2)

    def test_component_fare_elasticities_drive_all_five_demands(self) -> None:
        scenario = metrics(headline=6.0, energy=82.0, confidence=42.0, income_growth=-0.5)
        pairs = {
            "business": (0.18, 0.38),
            "leisure": (1.00, 1.90),
            "vfr": (0.45, 1.00),
            "long_haul": (0.60, 1.25),
            "transfer": (0.75, 1.45),
        }
        for component, (low_value, high_value) in pairs.items():
            field = ELASTICITY_FIELDS[component]
            low = replace(self.params, **{field: low_value})
            high = replace(self.params, **{field: high_value})
            low_price = demand.price_sensitivity(scenario, low)
            high_price = demand.price_sensitivity(scenario, high)
            self.assertGreater(
                demand.fare_elasticities(high_price, high)[component],
                demand.fare_elasticities(low_price, low)[component],
                component,
            )
            self.assertLess(target(scenario, high)[component], target(scenario, low)[component], component)

    def test_tourism_exposure_is_two_sided_and_aggregate_neutral(self) -> None:
        low = replace(self.params, tourism_exposure=0.20)
        high = replace(self.params, tourism_exposure=0.90)
        positive = metrics(income_growth=2.0, confidence=60.0)
        stress = metrics(income_growth=0.0, confidence=40.0, headline=5.5, energy=85.0)
        self.assertGreater(target(positive, high)["leisure"], target(positive, low)["leisure"])
        self.assertLess(target(stress, high)["leisure"], target(stress, low)["leisure"])
        for scenario in (positive, stress):
            self.assertAlmostEqual(
                demand.weighted_component_average(target(scenario, low), low),
                demand.weighted_component_average(target(scenario, high), high),
                places=10,
            )

    def test_international_exposure_is_two_sided(self) -> None:
        low = replace(self.params, international_exposure=0.30)
        high = replace(self.params, international_exposure=0.90)
        open_path = metrics(seed_openness_bias=2.0, risk_appetite=60.0)
        stress = metrics(currency_pressure=45.0, geopolitical=45.0, energy=75.0)
        for component in ("long_haul", "transfer"):
            self.assertGreater(target(open_path, high)[component], target(open_path, low)[component], component)
            self.assertLess(target(stress, high)[component], target(stress, low)[component], component)

    def test_domestic_market_depth_gives_transition_and_vfr_stress_resilience(self) -> None:
        low = replace(self.params, domestic_market_depth=0.30)
        high = replace(self.params, domestic_market_depth=0.95)
        previous = metrics(hy=520.0, stress=40.0, currency_pressure=36.0)
        stress = metrics(hy=900.0, stress=55.0, currency_pressure=42.0)
        low_target = demand.target_component_growth(
            stress,
            low,
            demand.price_sensitivity(stress, low),
            0.0,
            previous,
        )
        high_target = demand.target_component_growth(
            stress,
            high,
            demand.price_sensitivity(stress, high),
            0.0,
            previous,
        )
        self.assertGreater(high_target["vfr"], low_target["vfr"])
        self.assertGreater(
            demand.weighted_component_average(high_target, high),
            demand.weighted_component_average(low_target, low),
        )
        for params in (low, high):
            centered = demand.center_relative_component_adjustments(
                demand.raw_relative_component_adjustments(
                    stress,
                    params,
                    demand.price_sensitivity(stress, params),
                    0.0,
                ),
                params,
            )
            self.assertAlmostEqual(
                demand.weighted_component_average(centered, params),
                0.0,
                places=12,
            )

    def test_geopolitical_25_is_neutral_and_higher_risk_is_worse(self) -> None:
        at_center = metrics(geopolitical=25.0)
        high_risk = metrics(geopolitical=45.0)
        center_target = target(at_center, self.params)
        self.assertAlmostEqual(center_target["transfer"], center_target["business"], places=12)
        self.assertLess(target(high_risk, self.params)["transfer"], center_target["transfer"])


class RegionalAviationDemandParameterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.params = demand.AVIATION_REGION_CONFIGS["china_mainland"]

    def test_adjustment_speed_income_sensitivity_hub_weight_and_premium_elasticity_are_effective(self) -> None:
        shock_row = neutral_row(1, regional_gdp_growth_pct_reconciled=5.0, real_income_growth_pct=2.0)
        base_row = neutral_row(0)
        slow = replace(self.params, demand_adjustment_speed=0.20)
        fast = replace(self.params, demand_adjustment_speed=0.80)
        slow_output = demand.simulate_region_aviation_demand([base_row, shock_row], slow)[1]
        fast_output = demand.simulate_region_aviation_demand([base_row, shock_row], fast)[1]
        shock_metrics = demand.input_metrics(shock_row)
        target_growth = demand.weighted_component_average(target(shock_metrics, self.params), self.params)
        self.assertLess(
            abs(fast_output["regional_air_demand_growth_pct"] - target_growth),
            abs(slow_output["regional_air_demand_growth_pct"] - target_growth),
        )

        positive_income = metrics(income_growth=2.0)
        low_income = replace(self.params, income_sensitivity=0.60)
        high_income = replace(self.params, income_sensitivity=1.10)
        self.assertGreater(
            demand.weighted_component_average(target(positive_income, high_income), high_income),
            demand.weighted_component_average(target(positive_income, low_income), low_income),
        )

        open_path = metrics(seed_openness_bias=2.0)
        low_hub = replace(self.params, transfer_hub_weight=0.05)
        high_hub = replace(self.params, transfer_hub_weight=0.18)
        self.assertGreater(target(open_path, high_hub)["transfer"], target(open_path, low_hub)["transfer"])

        low_premium = replace(self.params, premium_fare_elasticity_base=0.10)
        high_premium = replace(self.params, premium_fare_elasticity_base=0.28)
        self.assertGreater(
            demand.fare_elasticities(70.0, high_premium)["premium"],
            demand.fare_elasticities(70.0, low_premium)["premium"],
        )

    def test_multiple_regions_and_seeds_remain_distinct_finite_and_noncollapsed(self) -> None:
        region_ids = ("china_mainland", "middle_east_gulf")
        final_signatures: dict[str, tuple[float, ...]] = {}
        for region_id in region_ids:
            params = demand.AVIATION_REGION_CONFIGS[region_id]
            rows = []
            for seed, bias in ((101, -0.4), (202, 0.6)):
                for year_index in range(61):
                    cycle = math.sin(year_index / 6.0)
                    rows.append(
                        neutral_row(
                            year_index,
                            seed=seed,
                            regional_gdp_growth_pct_reconciled=2.2 + 0.5 * cycle,
                            regional_potential_growth_pct=2.1,
                            real_income_growth_pct=0.8 + 0.2 * cycle,
                            consumer_confidence_index=50.0 + 4.0 * cycle,
                            regional_seed_aviation_propensity_bias_pct=bias,
                            regional_seed_openness_bias_pct=0.5 * bias,
                        )
                    )
            output = demand.simulate_region_aviation_demand(rows, params)
            self.assertEqual(122, len(output))
            for row in output:
                self.assertTrue(math.isfinite(row["regional_air_demand_index"]))
                self.assertGreater(row["regional_air_demand_index"], 0.0)
                self.assertAlmostEqual(100.0, sum(row[field] for field in SHARE_FIELDS.values()), places=3)
                for component in COMPONENTS:
                    self.assertGreater(row[INDEX_FIELDS[component]], 0.0)
                    self.assertGreater(row[SHARE_FIELDS[component]], 0.5)
            final = [row for row in output if row["year_index"] == 60]
            self.assertNotEqual(final[0]["regional_air_demand_index"], final[1]["regional_air_demand_index"])
            final_signatures[region_id] = tuple(final[0][field] for field in SHARE_FIELDS.values())
        self.assertNotEqual(final_signatures[region_ids[0]], final_signatures[region_ids[1]])


    def test_stress_cycle_does_not_depend_on_regional_growth_clamps(self) -> None:
        limits = {
            "business": (-9.0, 10.5),
            "leisure": (-10.0, 12.0),
            "vfr": (-4.5, 6.5),
            "long_haul": (-11.0, 12.5),
            "transfer": (-7.5, 8.5),
        }
        for region_id in ("china_mainland", "middle_east_gulf", "north_america"):
            params = demand.AVIATION_REGION_CONFIGS[region_id]
            rows = [
                neutral_row(
                    year_index,
                    seed=424242,
                    regional_gdp_growth_pct_reconciled=2.2 + 0.9 * math.sin(year_index / 5.0),
                    regional_potential_growth_pct=2.1,
                    real_income_growth_pct=0.8 + 0.5 * math.sin(year_index / 7.0),
                    consumer_confidence_index=50.0 + 8.0 * math.sin(year_index / 6.0),
                    regional_headline_inflation_pct_reconciled=2.4 + 1.2 * max(0.0, math.sin(year_index / 9.0)),
                    regional_energy_cost_pressure_index_reconciled=50.0 + 18.0 * max(0.0, math.sin(year_index / 8.0)),
                    currency_pressure_index=35.0 + 8.0 * max(0.0, math.sin(year_index / 10.0)),
                    regional_geopolitical_risk_index=25.0 + 10.0 * max(0.0, math.sin(year_index / 11.0)),
                    regional_seed_aviation_propensity_bias_pct=0.35,
                    regional_seed_openness_bias_pct=0.25,
                )
                for year_index in range(61)
            ]
            output = demand.simulate_region_aviation_demand(rows, params)
            with self.subTest(region_id=region_id):
                for row in output[1:]:
                    for component, (lower, upper) in limits.items():
                        self.assertNotEqual(lower, row[GROWTH_FIELDS[component]])
                        self.assertNotEqual(upper, row[GROWTH_FIELDS[component]])
                for component in COMPONENTS:
                    self.assertGreater(output[-1][SHARE_FIELDS[component]], 1.0)
                    self.assertLess(output[-1][SHARE_FIELDS[component]], 60.0)


if __name__ == "__main__":
    unittest.main()
