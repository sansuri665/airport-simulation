from __future__ import annotations

import random
import unittest
from dataclasses import replace

from macro_layers import global_equity_accounting_v04 as equity


def macro_row(seed: int, year_index: int, **overrides: float) -> dict[str, float | int]:
    row: dict[str, float | int] = {
        "seed": seed,
        "year_index": year_index,
        "year": 2026 + year_index,
        "realized_growth_pct": 2.4,
        "potential_growth_pct": 2.1,
        "output_gap_pct": 0.2,
        "headline_inflation_pct": 2.3,
        "core_inflation_pct": 2.2,
        "crisis_intensity": 0.0,
        "global_real_10y_yield_pct": 1.0,
        "policy_stance_index": 0.0,
        "global_liquidity_index": 55.0,
        "global_financial_conditions_index": 0.0,
        "risk_appetite_index": 50.0,
        "global_dollar_index": 100.0,
        "global_high_yield_spread_bps": 420.0,
        "default_risk_index": 30.0,
        "credit_impairment_stock_index": 0.0,
        "credit_to_equity_risk_premium_impulse": 0.0,
        "yield_curve_to_equity_valuation_impulse": 0.0,
        "liquidity_to_equity_impulse": 0.0,
    }
    row.update(overrides)
    return row


def path(seed: int, years: int, **overrides: float) -> list[dict[str, float | int]]:
    return [macro_row(seed, year, **overrides) for year in range(years + 1)]


class GlobalEquityV04AccountingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.params = replace(
            equity.GlobalEquityV04Params(),
            eps_noise_scale=0.0,
            pe_noise_scale=0.0,
        )

    def test_initial_row_has_complete_equity_contract(self) -> None:
        inputs = path(424242, 1)
        row = equity.simulate_global_equity_v04_for_macro_path(inputs, self.params)[0]
        self.assertEqual(
            set(equity.GLOBAL_EQUITY_V04_FIELDS),
            set(row) - set(inputs[0]),
        )
        self.assertEqual(100.0, row["global_equity_eps_index"])
        self.assertEqual(100.0, row["global_equity_price_index"])
        self.assertEqual(100.0, row["global_equity_total_return_index"])
        self.assertEqual(0.0, row["global_equity_total_return_pct"])

    def test_eps_contributions_reconstruct_raw_and_final_growth(self) -> None:
        row = equity.simulate_global_equity_v04_for_macro_path(path(101, 2), self.params)[1]
        raw = sum(float(row[field]) for field in equity.EPS_CONTRIBUTION_FIELDS)
        final = (
            raw
            + float(row["global_equity_eps_smoothing_adjustment_pp"])
            + float(row["global_equity_eps_boundary_adjustment_pp"])
        )
        self.assertAlmostEqual(float(row["global_equity_eps_growth_raw_pct"]), raw, places=3)
        self.assertAlmostEqual(float(row["global_equity_eps_growth_pct"]), final, places=3)

    def test_pe_contributions_reconstruct_raw_and_final_pe(self) -> None:
        row = equity.simulate_global_equity_v04_for_macro_path(path(102, 2), self.params)[1]
        raw = sum(float(row[field]) for field in equity.PE_CONTRIBUTION_FIELDS)
        final = (
            raw
            + float(row["global_equity_pe_smoothing_adjustment"])
            + float(row["global_equity_pe_boundary_adjustment"])
        )
        self.assertAlmostEqual(float(row["global_equity_valuation_pe_raw"]), raw, places=3)
        self.assertAlmostEqual(float(row["global_equity_valuation_pe"]), final, places=3)

    def test_price_dividend_and_total_return_identities_hold(self) -> None:
        rows = equity.simulate_global_equity_v04_for_macro_path(path(103, 12), self.params)
        for previous, current in zip(rows, rows[1:]):
            expected_price = (
                float(current["global_equity_eps_index"])
                * float(current["global_equity_valuation_pe"])
                / self.params.initial_pe
            )
            price_return = (
                expected_price / float(previous["global_equity_price_index"]) - 1.0
            ) * 100.0
            total_return = price_return + float(current["global_equity_dividend_yield_pct"])
            total_index = float(previous["global_equity_total_return_index"]) * (
                1.0 + total_return / 100.0
            )
            self.assertAlmostEqual(expected_price, float(current["global_equity_price_index"]), places=2)
            self.assertAlmostEqual(price_return, float(current["global_equity_price_return_pct"]), places=2)
            self.assertAlmostEqual(total_return, float(current["global_equity_total_return_pct"]), places=2)
            self.assertAlmostEqual(total_index, float(current["global_equity_total_return_index"]), places=2)
            self.assertAlmostEqual(0.0, float(current["global_equity_price_identity_residual"]), places=4)
            self.assertAlmostEqual(0.0, float(current["global_equity_total_return_identity_residual"]), places=4)

    def test_growth_lifts_eps_and_price_when_pe_drivers_are_unchanged(self) -> None:
        low = equity.simulate_global_equity_v04_for_macro_path(
            path(104, 1, realized_growth_pct=0.5), self.params
        )[-1]
        high = equity.simulate_global_equity_v04_for_macro_path(
            path(104, 1, realized_growth_pct=5.0), self.params
        )[-1]
        self.assertEqual(low["global_equity_valuation_pe"], high["global_equity_valuation_pe"])
        self.assertGreater(high["global_equity_eps_index"], low["global_equity_eps_index"])
        self.assertGreater(high["global_equity_price_index"], low["global_equity_price_index"])

    def test_higher_real_rate_compresses_pe_and_price_with_same_eps(self) -> None:
        low_rate = equity.simulate_global_equity_v04_for_macro_path(
            path(105, 1, global_real_10y_yield_pct=-0.5), self.params
        )[-1]
        high_rate = equity.simulate_global_equity_v04_for_macro_path(
            path(105, 1, global_real_10y_yield_pct=5.0), self.params
        )[-1]
        self.assertEqual(low_rate["global_equity_eps_index"], high_rate["global_equity_eps_index"])
        self.assertGreater(low_rate["global_equity_valuation_pe"], high_rate["global_equity_valuation_pe"])
        self.assertGreater(low_rate["global_equity_price_index"], high_rate["global_equity_price_index"])

    def test_eps_can_rise_while_strong_pe_compression_lowers_price(self) -> None:
        params = replace(self.params, eps_smoothing=1.0, pe_smoothing=1.0)
        row = equity.simulate_global_equity_v04_for_macro_path(
            path(106, 1, realized_growth_pct=4.0, global_real_10y_yield_pct=8.0),
            params,
        )[-1]
        self.assertGreater(row["global_equity_eps_index"], 100.0)
        self.assertLess(row["global_equity_valuation_pe"], 18.0)
        self.assertLess(row["global_equity_price_index"], 100.0)

    def test_crisis_reduces_eps_pe_and_payout(self) -> None:
        calm = equity.simulate_global_equity_v04_for_macro_path(path(107, 1), self.params)[-1]
        crisis = equity.simulate_global_equity_v04_for_macro_path(
            path(
                107,
                1,
                crisis_intensity=1.0,
                global_high_yield_spread_bps=900.0,
                credit_impairment_stock_index=30.0,
            ),
            self.params,
        )[-1]
        self.assertLess(crisis["global_equity_eps_index"], calm["global_equity_eps_index"])
        self.assertLess(crisis["global_equity_valuation_pe"], calm["global_equity_valuation_pe"])
        self.assertLess(crisis["global_equity_payout_ratio_pct"], calm["global_equity_payout_ratio_pct"])

    def test_long_growth_path_has_no_legacy_price_or_total_return_cap(self) -> None:
        params = replace(self.params, eps_smoothing=1.0, pe_smoothing=1.0)
        rows = equity.simulate_global_equity_v04_for_macro_path(
            path(108, 80, realized_growth_pct=5.0, potential_growth_pct=3.0), params
        )
        self.assertGreater(rows[-1]["global_equity_price_index"], 620.0)
        self.assertGreater(rows[-1]["global_equity_total_return_index"], 620.0)

    def test_repeated_calls_and_short_long_prefix_are_exact(self) -> None:
        settings = equity.GlobalEquityV04Params()
        short = equity.simulate_global_equity_v04_for_macro_path(path(109, 12), settings)
        long = equity.simulate_global_equity_v04_for_macro_path(path(109, 60), settings)
        repeat = equity.simulate_global_equity_v04_for_macro_path(path(109, 12), settings)
        self.assertEqual(short, repeat)
        self.assertEqual(short, long[: len(short)])

    def test_candidate_does_not_consume_process_random_state(self) -> None:
        random.seed(8675309)
        expected = random.random()
        random.seed(8675309)
        equity.simulate_global_equity_v04_for_macro_path(path(110, 12))
        self.assertEqual(expected, random.random())

    def test_empty_path_is_supported_and_parameter_errors_are_explicit(self) -> None:
        self.assertEqual([], equity.simulate_global_equity_v04_for_macro_path([]))
        with self.assertRaisesRegex(ValueError, "eps_smoothing"):
            equity.simulate_global_equity_v04_for_macro_path(
                path(111, 1), replace(self.params, eps_smoothing=0.0)
            )


if __name__ == "__main__":
    unittest.main()
