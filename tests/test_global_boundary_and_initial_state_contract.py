from __future__ import annotations

import argparse
import unittest
from dataclasses import replace
from unittest import mock

from macro_layers import global_asset_price_layer_sim as asset
from macro_layers import global_credit_spread_layer_sim as credit
from macro_layers import global_dollar_liquidity_layer_sim as dollar
from macro_layers import global_gdp_annual_sim as gdp
from macro_layers import global_inflation_annual_sim as inflation
from macro_layers import global_oil_commodity_layer_sim as oil
from macro_layers import global_policy_rate_layer_sim as policy
from macro_layers import global_yield_curve_layer_sim as yield_curve
from macro_layers import macro_run_orchestrator_sim as orchestrator
from macro_layers import regional_macro_layer_sim as regional
from macro_layers.global_macro_feedback_calibration_sim import MacroFeedbackParams




class RaisingRandom:
    """Random-compatible sentinel that fails on every draw."""

    def __init__(self, *_args, **_kwargs) -> None:
        pass

    def _fail(self, *_args, **_kwargs):
        raise AssertionError("year_index=0 consumed a random draw")

    random = _fail
    uniform = _fail
    gauss = _fail
    randint = _fail
    randrange = _fail
    choice = _fail
    choices = _fail
    sample = _fail


class GlobalInitialStateContractTests(unittest.TestCase):
    @staticmethod
    def _args(years: int) -> argparse.Namespace:
        feedback = MacroFeedbackParams()
        return argparse.Namespace(
            years=years,
            start_year=2025,
            initial_gdp=100.0,
            volatility_scale=1.0,
            feedback_iterations=feedback.max_feedback_iterations,
            min_feedback_iterations=feedback.min_feedback_iterations,
        )

    @classmethod
    def _rows(cls, seed: int, years: int) -> list[dict]:
        return orchestrator.run_global_variant(
            seed, cls._args(years), "baseline"
        )["rows"]

    def test_year_zero_is_configured_initial_state(self) -> None:
        row = self._rows(20261001, 0)[0]
        expected = {
            "year_index": 0,
            "real_gdp_index": 100.0,
            "potential_gdp_index": 100.0,
            "output_gap_pct": 0.0,
            "financial_stress_index": 10.0,
            "headline_inflation_pct": 2.4,
            "core_inflation_pct": 2.25,
            "global_policy_rate_pct": 3.25,
            "global_2y_yield_pct": 3.4,
            "global_10y_yield_pct": 4.05,
            "global_dollar_index": 100.0,
            "global_high_yield_spread_bps": 420.0,
            "equity_earnings_index": 100.0,
            "brent_oil_price_usd": 82.0,
        }
        for field, value in expected.items():
            self.assertEqual(row[field], value, field)
        for field in (
            "regime",
            "inflation_regime",
            "central_bank_reaction_regime",
            "yield_curve_regime",
            "dollar_liquidity_regime",
            "credit_regime",
            "asset_risk_regime",
            "oil_regime",
        ):
            self.assertEqual(row[field], "initial", field)

    def test_year_zero_is_seed_invariant_except_seed_identity(self) -> None:
        left = dict(self._rows(20261001, 0)[0])
        right = dict(self._rows(20269999, 0)[0])
        left.pop("seed")
        right.pop("seed")
        self.assertEqual(left, right)

    def test_short_runs_are_exact_prefixes_of_long_run(self) -> None:
        seed = 20261017
        rows_0 = self._rows(seed, 0)
        rows_1 = self._rows(seed, 1)
        rows_2 = self._rows(seed, 2)
        rows_60 = self._rows(seed, 60)
        self.assertEqual(len(rows_0), 1)
        self.assertEqual(len(rows_1), 2)
        self.assertEqual(len(rows_2), 3)
        self.assertEqual(len(rows_60), 61)
        self.assertEqual(rows_0, rows_60[:1])
        self.assertEqual(rows_1, rows_60[:2])
        self.assertEqual(rows_2, rows_60[:3])

    def test_region_reads_the_same_global_initial_anchors(self) -> None:
        global_row = self._rows(20261001, 0)[0]
        region_rows = regional.simulate_region_for_global_path(
            [global_row], regional.REGION_CONFIGS["north_america"], 20261001
        )
        self.assertEqual(len(region_rows), 1)
        row = region_rows[0]
        self.assertEqual(row["year_index"], 0)
        self.assertEqual(row["global_growth_anchor_pct"], global_row["realized_growth_pct"])
        self.assertEqual(row["global_output_gap_anchor_pct"], global_row["output_gap_pct"])
        self.assertEqual(row["global_inflation_anchor_pct"], global_row["headline_inflation_pct"])
        self.assertEqual(row["global_policy_anchor_pct"], global_row["global_policy_rate_pct"])
        self.assertEqual(row["global_10y_anchor_pct"], global_row["global_10y_yield_pct"])
        self.assertEqual(row["global_hy_anchor_bps"], global_row["global_high_yield_spread_bps"])

    def test_year_zero_draws_no_random_numbers_in_all_eight_layers(self) -> None:
        seed = 20261001
        with mock.patch.object(gdp.random, "Random", RaisingRandom):
            gdp_rows = gdp.simulate_global_gdp(seed, gdp.GDPParams(years=0))
        with mock.patch.object(inflation.random, "Random", RaisingRandom):
            inflation_rows = inflation.simulate_inflation_for_gdp_path(
                seed, gdp_rows, inflation.InflationParams()
            )
        # The policy layer is deterministic and imports no RNG at all.
        policy_rows = policy.simulate_policy_for_macro_path(
            inflation_rows, policy.PolicyRateParams()
        )
        with mock.patch.object(yield_curve.random, "Random", RaisingRandom):
            yield_rows = yield_curve.simulate_yield_curve_for_policy_path(
                policy_rows, yield_curve.YieldCurveParams()
            )
        with mock.patch.object(dollar.random, "Random", RaisingRandom):
            dollar_rows = dollar.simulate_dollar_liquidity_for_yield_path(
                yield_rows, dollar.DollarLiquidityParams()
            )
        with mock.patch.object(credit.random, "Random", RaisingRandom):
            credit_rows = credit.simulate_credit_spreads_for_dollar_path(
                dollar_rows, credit.CreditSpreadParams()
            )
        with mock.patch.object(asset.random, "Random", RaisingRandom):
            asset_rows = asset.simulate_asset_prices_for_credit_path(
                credit_rows, asset.AssetPriceParams()
            )
        with mock.patch.object(oil.random, "Random", RaisingRandom):
            oil_rows = oil.simulate_oil_commodities_for_asset_path(
                asset_rows, oil.OilCommodityParams()
            )
        self.assertEqual(len(oil_rows), 1)
        self.assertEqual(oil_rows[0]["year_index"], 0)


class GlobalInitialParameterValidationTests(unittest.TestCase):
    def test_all_eight_layers_reject_out_of_domain_initial_values(self) -> None:
        invalid_calls = {
            "gdp": lambda: gdp.simulate_global_gdp(
                1, replace(gdp.GDPParams(years=0), initial_index=0.0)
            ),
            "inflation": lambda: inflation.simulate_inflation_for_gdp_path(
                1,
                [],
                replace(
                    inflation.InflationParams(),
                    initial_headline_pct=inflation.InflationParams().max_headline_pct + 0.1,
                ),
            ),
            "policy": lambda: policy.simulate_policy_for_macro_path(
                [],
                replace(
                    policy.PolicyRateParams(),
                    initial_policy_rate_pct=policy.PolicyRateParams().min_policy_rate_pct - 0.1,
                ),
            ),
            "yield_curve": lambda: yield_curve.simulate_yield_curve_for_policy_path(
                [],
                replace(
                    yield_curve.YieldCurveParams(),
                    initial_10y_yield_pct=yield_curve.YieldCurveParams().min_yield_pct - 0.1,
                ),
            ),
            "dollar": lambda: dollar.simulate_dollar_liquidity_for_yield_path(
                [], replace(dollar.DollarLiquidityParams(), initial_liquidity_index=100.1)
            ),
            "credit": lambda: credit.simulate_credit_spreads_for_dollar_path(
                [], replace(credit.CreditSpreadParams(), initial_credit_availability_index=100.1)
            ),
            "asset": lambda: asset.simulate_asset_prices_for_credit_path(
                [], replace(asset.AssetPriceParams(), initial_equity_index=0.0)
            ),
            "oil": lambda: oil.simulate_oil_commodities_for_asset_path(
                [],
                replace(
                    oil.OilCommodityParams(),
                    initial_brent_price_usd=oil.OilCommodityParams().oil_price_floor_usd - 0.1,
                ),
            ),
        }
        for layer, call in invalid_calls.items():
            with self.subTest(layer=layer), self.assertRaises(ValueError):
                call()

    def test_non_finite_initial_value_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "initial_gdp_trillion_usd must be finite"):
            gdp.simulate_global_gdp(
                1, replace(gdp.GDPParams(years=0), initial_gdp_trillion_usd=float("nan"))
            )


class GlobalBoundaryContractTests(unittest.TestCase):
    def test_soft_upper_saturation_preserves_severity_ordering(self) -> None:
        for helper, knee, asymptote in (
            (credit.soft_upper_saturate, 78.0, 99.0),
            (asset.soft_upper_saturate, 8.0, 11.8),
            (oil.soft_upper_saturate, 82.0, 99.0),
        ):
            ordinary = helper(knee + 1.0, knee, asymptote)
            severe = helper(knee + 15.0, knee, asymptote)
            disaster = helper(knee + 50.0, knee, asymptote)
            self.assertLess(ordinary, severe)
            self.assertLess(severe, disaster)
            self.assertLess(disaster, asymptote)

    def test_credit_soft_floor_preserves_raw_severity(self) -> None:
        ordinary = credit.soft_lower_saturate(6.0, 8.0, 0.5)
        severe = credit.soft_lower_saturate(-2.0, 8.0, 0.5)
        disaster = credit.soft_lower_saturate(-12.0, 8.0, 0.5)
        self.assertGreater(ordinary, severe)
        self.assertGreater(severe, disaster)
        self.assertGreater(disaster, 0.5)

    def test_earnings_index_is_not_fixed_at_460(self) -> None:
        rows = []
        for year_index in range(61):
            rows.append(
                {
                    "seed": 20261017,
                    "year_index": year_index,
                    "year": 2025 + year_index,
                    "realized_growth_pct": 7.0,
                    "potential_growth_pct": 2.0,
                    "output_gap_pct": 4.0,
                    "headline_inflation_pct": 2.0,
                    "core_inflation_pct": 2.0,
                    "global_high_yield_spread_bps": 300.0,
                    "global_investment_grade_spread_bps": 80.0,
                    "credit_availability_index": 75.0,
                    "risk_appetite_index": 65.0,
                    "global_liquidity_index": 65.0,
                }
            )
        result = asset.simulate_asset_prices_for_credit_path(
            rows, asset.AssetPriceParams(noise_scale=0.0)
        )
        self.assertGreater(max(float(row["equity_earnings_index"]) for row in result), 460.0)
        self.assertFalse(any(bool(row["equity_earnings_index_cap_applied"]) for row in result))

    def test_goal5a_diagnostics_are_emitted(self) -> None:
        feedback = MacroFeedbackParams()
        args = argparse.Namespace(
            years=2,
            start_year=2025,
            initial_gdp=100.0,
            volatility_scale=1.0,
            feedback_iterations=feedback.max_feedback_iterations,
            min_feedback_iterations=feedback.min_feedback_iterations,
        )
        rows = orchestrator.run_global_variant(20261001, args, "baseline")["rows"]
        fields = (
            "global_credit_spread_index",
            "credit_availability_index",
            "credit_impairment_stock_index",
            "equity_earnings_index",
            "equity_risk_premium_pct",
            "brent_oil_price_usd",
            "energy_cost_pressure_index",
        )
        for row in rows:
            for field in fields:
                self.assertIn(f"unclamped_{field}_target", row)
                self.assertIn(f"{field}_floor_applied", row)
                self.assertIn(f"{field}_cap_applied", row)
                self.assertIn(f"{field}_boundary_state", row)
                self.assertIn(f"{field}_consecutive_boundary_years", row)


if __name__ == "__main__":
    unittest.main()
