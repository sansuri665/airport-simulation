from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

from macro_layers import city_airport_financial_state_layer_sim as finance_model


ROOT_DIR = Path(__file__).resolve().parents[1]
RATE_MODULE = ROOT_DIR / "web" / "static" / "js" / "seed-explorer" / "financing-rate.js"


def rate_policy() -> dict:
    return {
        "model_version": "general-loan-rate-v0.3",
        "fallback_short_term_rate_pct": 3.6,
        "fallback_long_term_rate_pct": 4.8,
        "short_term_reference_adjustment_pct": -0.25,
        "long_term_reference_adjustment_pct": 0.0,
        "short_term_spread_bps": 60.0,
        "long_term_spread_bps": 145.0,
        "hy_spread_baseline_bps": 420.0,
        "hy_spread_capture_ratio": 0.1,
        "city_risk_spread_bps": 0.0,
        "min_annual_interest_rate_pct": 1.0,
        "max_annual_interest_rate_pct": 9.5,
        "leverage_spread_model": {
            "enabled": True,
            "spread_curve": [
                {"liability_ratio_pct": 45.0, "additional_spread_bps": 0.0},
                {"liability_ratio_pct": 60.0, "additional_spread_bps": 60.0},
                {"liability_ratio_pct": 70.0, "additional_spread_bps": 150.0},
                {"liability_ratio_pct": 80.0, "additional_spread_bps": 300.0},
            ],
            "block_if_begin_ratio_at_or_above_pct": 80.0,
            "block_if_post_draw_ratio_at_or_above_pct": 80.0,
        },
    }


def operation(*, policy_rate: float = 2.5, ten_year: float = 3.5) -> dict:
    return {
        "input_policy_rate_pct": policy_rate,
        "input_policy_rate_source": "regional_macro_annual",
        "input_10y_yield_pct": ten_year,
        "input_10y_yield_source": "regional_macro_annual",
        "input_hy_spread_bps": 520.0,
    }


def loan(loan_type: str, **overrides) -> dict:
    payload = {
        "loan_id": "test-loan",
        "loan_type": loan_type,
        "start_year": 2026,
        "start_quarter": "Q1",
        "principal_million_cny": 10_000.0,
        "tenor_quarters": 8,
        "repayment_style": "bullet_principal",
        "term_spread_bps": 15.0,
        "grace_spread_bps": 0.0,
    }
    payload.update(overrides)
    return payload


class LoanRateV03ContractTests(unittest.TestCase):
    def assert_quote_conserves(self, quote: dict) -> None:
        expected = (
            quote["benchmark_rate_pct"]
            + quote["product_spread_bps"] / 100.0
            + quote["term_and_grace_spread_bps"] / 100.0
            + quote["credit_spread_bps"] / 100.0
            + quote["leverage_spread_bps"] / 100.0
        )
        self.assertAlmostEqual(expected, quote["unclamped_annual_rate_pct"], places=4)
        self.assertLessEqual(quote["annual_rate_pct"], 9.5)
        self.assertGreaterEqual(quote["annual_rate_pct"], 1.0)

    def test_short_and_long_products_use_different_authoritative_benchmarks(self) -> None:
        policy = rate_policy()
        short_quote = finance_model.build_loan_rate_quote(
            loan("short_term"), operation(policy_rate=2.4, ten_year=4.2), {"loan_rate_model": policy}
        )
        long_quote = finance_model.build_loan_rate_quote(
            loan("long_term"), operation(policy_rate=2.4, ten_year=4.2), {"loan_rate_model": policy}
        )

        self.assertEqual("policy_rate", short_quote["benchmark_type"])
        self.assertEqual(2.4, short_quote["benchmark_rate_pct"])
        self.assertEqual("ten_year_yield", long_quote["benchmark_type"])
        self.assertEqual(4.2, long_quote["benchmark_rate_pct"])
        self.assert_quote_conserves(short_quote)
        self.assert_quote_conserves(long_quote)

    def test_curve_inversion_is_visible_instead_of_forcing_product_order(self) -> None:
        policy = rate_policy()
        macro = operation(policy_rate=5.0, ten_year=2.0)
        short_quote = finance_model.build_loan_rate_quote(loan("short_term"), macro, {"loan_rate_model": policy})
        long_quote = finance_model.build_loan_rate_quote(loan("long_term"), macro, {"loan_rate_model": policy})
        self.assertGreater(short_quote["annual_rate_pct"], long_quote["annual_rate_pct"])

    def test_zero_and_negative_policy_rates_are_valid_and_floor_is_explicit(self) -> None:
        policy = rate_policy()
        zero_quote = finance_model.build_loan_rate_quote(
            loan("short_term"), operation(policy_rate=0.0), {"loan_rate_model": policy}
        )
        negative_quote = finance_model.build_loan_rate_quote(
            loan("short_term"), operation(policy_rate=-1.5), {"loan_rate_model": policy}
        )
        self.assertFalse(zero_quote["benchmark_fallback_used"])
        self.assertEqual(0.0, zero_quote["benchmark_rate_pct"])
        self.assertFalse(negative_quote["benchmark_fallback_used"])
        self.assertEqual(-1.5, negative_quote["benchmark_rate_pct"])
        self.assertTrue(negative_quote["rate_floor_applied"])
        self.assertEqual(1.0, negative_quote["annual_rate_pct"])

    def test_missing_or_mismatched_source_falls_back_only_for_selected_benchmark(self) -> None:
        policy = rate_policy()
        macro = operation(policy_rate=2.0, ten_year=4.1)
        macro.pop("input_policy_rate_pct")
        short_quote = finance_model.build_loan_rate_quote(loan("short_term"), macro, {"loan_rate_model": policy})
        long_quote = finance_model.build_loan_rate_quote(loan("long_term"), macro, {"loan_rate_model": policy})
        self.assertTrue(short_quote["benchmark_fallback_used"])
        self.assertEqual("fallback_short_term_rate_pct", short_quote["benchmark_source"])
        self.assertFalse(long_quote["benchmark_fallback_used"])

        macro = operation(policy_rate=2.0, ten_year=4.1)
        macro["input_10y_yield_source"] = "unexpected_source"
        short_quote = finance_model.build_loan_rate_quote(loan("short_term"), macro, {"loan_rate_model": policy})
        long_quote = finance_model.build_loan_rate_quote(loan("long_term"), macro, {"loan_rate_model": policy})
        self.assertFalse(short_quote["benchmark_fallback_used"])
        self.assertTrue(long_quote["benchmark_fallback_used"])
        self.assertEqual("source_mismatch", long_quote["benchmark_fallback_reason"])

    def test_drawdown_quote_and_rate_remain_locked_after_macro_rates_move(self) -> None:
        policy = rate_policy()
        states: dict[str, dict] = {}
        product = loan("short_term", tenor_quarters=4)
        first = finance_model.process_general_loans(
            states,
            [product],
            operation(policy_rate=2.0, ten_year=3.5),
            {"loan_rate_model": policy},
            2026,
            "Q1",
            100_000.0,
            20_000.0,
        )
        locked = states["test-loan"]["annual_interest_rate_pct"]
        locked_quote = dict(states["test-loan"]["rate_quote"])

        second = finance_model.process_general_loans(
            states,
            [product],
            operation(policy_rate=8.0, ten_year=8.5),
            {"loan_rate_model": policy},
            2026,
            "Q2",
            100_000.0,
            20_000.0,
        )
        self.assertEqual(locked, first["drawdown_weighted_interest_rate_pct"])
        self.assertEqual(locked, second["weighted_interest_rate_pct"])
        self.assertEqual(locked_quote, states["test-loan"]["rate_quote"])
        serialized = json.loads(second["locked_rate_quotes_json"])
        self.assertEqual(locked_quote["benchmark_rate_pct"], serialized[0]["benchmark_rate_pct"])

    def test_browser_quote_matches_python_components(self) -> None:
        policy = rate_policy()
        product = {
            "loan_type": "long_term",
            "tenor_spread_bps": {"60": 20},
            "grace_spread_bps": {"8": 10},
        }
        finance = {
            "macroPolicyRatePct": 2.25,
            "macroPolicyRateSource": "regional_macro_annual",
            "macroTenYearYieldPct": 3.75,
            "macroTenYearYieldSource": "regional_macro_annual",
            "macroHySpreadBps": 520.0,
            "totalAssets": 100_000.0,
            "totalLiabilities": 20_000.0,
        }
        principal = 10_000.0
        post_leverage = (20_000.0 + principal) / (100_000.0 + principal) * 100.0
        leverage_spread = finance_model.loan_leverage_spread_bps(
            {"loan_rate_model": policy}, post_leverage
        )
        python_quote = finance_model.build_loan_rate_quote(
            loan("long_term", term_spread_bps=20.0, grace_spread_bps=10.0),
            operation(policy_rate=2.25, ten_year=3.75),
            {"loan_rate_model": policy},
            leverage_spread,
        )
        js_input = {
            "product": product,
            "policy": policy,
            "finance": finance,
            "principalMillion": principal,
            "tenor": 60,
            "grace": 8,
        }
        script = (
            f"require({json.dumps(str(RATE_MODULE))});"
            f"const result=globalThis.AirportFinancingRate.buildLoanRateQuote({json.dumps(js_input)});"
            "process.stdout.write(JSON.stringify(result));"
        )
        completed = subprocess.run(
            ["node", "-e", script],
            cwd=ROOT_DIR,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        browser_quote = json.loads(completed.stdout)
        for field in (
            "benchmark_type",
            "benchmark_source",
            "benchmark_rate_pct",
            "product_spread_bps",
            "term_and_grace_spread_bps",
            "credit_spread_bps",
            "leverage_spread_bps",
            "unclamped_annual_rate_pct",
            "annual_rate_pct",
        ):
            if isinstance(python_quote[field], float):
                self.assertAlmostEqual(python_quote[field], browser_quote[field], places=4, msg=field)
            else:
                self.assertEqual(python_quote[field], browser_quote[field], field)


if __name__ == "__main__":
    unittest.main()
