from __future__ import annotations

import json
import unittest
from pathlib import Path

from airport_sim.schema_validation import validate_schema
from macro_layers import macro_run_orchestrator_sim as orchestrator
from macro_layers import regional_aviation_demand_layer_sim as aviation
from macro_layers import regional_wealth_bridge_v04 as wealth_bridge


ROOT_DIR = Path(__file__).resolve().parents[1]
TARGETS = ("total", "business", "leisure", "vfr", "long_haul", "transfer")
FAMILIES = ("asset_market", "household_wealth", "cash_income", "credit_confidence", "fare_cost")


def regional_row(year_index: int) -> dict[str, object]:
    return {
        "region_id": "china_mainland",
        "region_name": "中国大陆",
        "seed": 20260726,
        "year_index": year_index,
        "year": 2025 + year_index,
        "reconciliation_scope": "a3_test",
        "regional_reconciled_gdp_trillion_usd": 19.0,
        "regional_gdp_growth_pct": 4.2,
        "regional_gdp_growth_pct_reconciled": 4.2,
        "regional_potential_growth_pct": 4.0,
        "real_income_growth_pct": 3.0,
        "regional_income_index": 100.0 + year_index * 3.0,
        "consumer_confidence_index": 53.0,
        "regional_headline_inflation_pct": 2.0,
        "regional_headline_inflation_pct_reconciled": 2.0,
        "currency_pressure_index": 35.0,
        "regional_macro_stress_index": 34.0,
        "regional_macro_stress_index_reconciled": 34.0,
        "regional_hy_spread_bps": 410.0,
        "regional_hy_spread_bps_reconciled": 410.0,
        "regional_credit_availability_index": 58.0,
        "regional_equity_price_return_pct": 0.0 if year_index == 0 else 8.0,
        "regional_equity_valuation_pe": 17.0 + year_index * 0.2,
        "regional_equity_dividend_yield_pct": 2.5,
        "regional_sovereign_bond_total_return_pct": 0.0 if year_index == 0 else 2.0,
        "regional_policy_rate_pct": 2.2,
        "regional_energy_cost_pressure_index": 48.0,
        "regional_energy_cost_pressure_index_reconciled": 48.0,
        "regional_risk_appetite_index": 50.0 + year_index,
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


class AssetA3IntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.bridge_rows = wealth_bridge.simulate_regional_wealth_bridge_v04(
            [regional_row(index) for index in range(3)]
        )
        self.aviation_rows = aviation.simulate_region_aviation_demand(
            self.bridge_rows,
            aviation.AVIATION_REGION_CONFIGS["china_mainland"],
        )

    def test_bridge_keeps_market_wealth_and_cash_signals_distinct(self) -> None:
        first, second = self.bridge_rows[:2]
        self.assertEqual(50.0, first["regional_asset_market_impulse_index"])
        self.assertEqual(0.0, first["regional_household_wealth_consumption_impulse"])
        self.assertEqual(0.0, first["regional_real_disposable_income_growth_pct"])
        self.assertNotEqual(50.0, second["regional_asset_market_impulse_index"])
        self.assertNotEqual(0.0, second["regional_household_wealth_consumption_impulse"])
        self.assertAlmostEqual(
            1.0,
            second["regional_household_equity_weight"]
            + second["regional_household_sovereign_bond_weight"]
            + second["regional_household_cash_weight"],
        )
        self.assertGreater(second["regional_real_disposable_income_growth_pct"], 3.0)

    def test_demand_decomposition_reconstructs_each_target(self) -> None:
        row = self.aviation_rows[1]
        for target in TARGETS:
            raw = row[f"demand_{target}_base_contribution_pp"] + sum(
                row[f"demand_{target}_{family}_contribution_pp"] for family in FAMILIES
            )
            self.assertAlmostEqual(raw, row[f"demand_{target}_raw_growth_pct"], places=3)
            final = (
                row[f"demand_{target}_raw_growth_pct"]
                + row[f"demand_{target}_boundary_adjustment_pp"]
                + row[f"demand_{target}_smoothing_adjustment_pp"]
            )
            self.assertAlmostEqual(final, row[f"demand_{target}_final_growth_pct"], places=3)

    def test_commercial_propensities_publish_reconstructable_contributions(self) -> None:
        row = self.aviation_rows[1]
        for segment, names in aviation._COMMERCIAL_CONTRIBUTIONS.items():
            reconstructed = sum(
                row[f"{segment}_propensity_{name}_contribution_points"] for name in names
            )
            self.assertAlmostEqual(reconstructed, row[f"{segment}_propensity_raw_index"], places=3)
        premium_raw = 100.0 + sum(
            row[f"premium_propensity_{name}_contribution_points"]
            for name in ("asset_market", "household_wealth", "cash_income", "traffic_mix")
        )
        self.assertAlmostEqual(premium_raw, row["premium_propensity_raw_index"], places=3)

    def test_schema_accepts_the_formal_a3_row(self) -> None:
        schema = json.loads(
            (ROOT_DIR / "schemas" / "asset-accounting-v04-fields.schema.json").read_text(
                encoding="utf-8"
            )
        )
        row_schema = schema["$defs"]["aviationDemandA3Row"]
        validate_schema(
            self.aviation_rows[1],
            row_schema,
            {"asset-accounting-v04-fields.schema.json": schema},
            current_name="asset-accounting-v04-fields.schema.json",
        )

    def test_publication_rejects_legacy_asset_aliases(self) -> None:
        source = {field: 1.0 for field in orchestrator.LEGACY_ASSET_OUTPUT_FIELDS}
        source.update({"bond_price_index": 101.0, "bond_total_return_pct": 1.25})
        published = orchestrator.public_asset_row(source)
        self.assertFalse(set(orchestrator.LEGACY_ASSET_OUTPUT_FIELDS) & set(published))
        self.assertEqual(101.0, published["yield_curve_reference_10y_bond_total_return_index"])
        self.assertEqual(1.25, published["yield_curve_reference_10y_bond_total_return_pct"])


if __name__ == "__main__":
    unittest.main()
