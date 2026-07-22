from __future__ import annotations

import argparse
import math
import sys
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
MACRO_DIR = ROOT_DIR / "macro_layers"
if str(MACRO_DIR) not in sys.path:
    sys.path.insert(0, str(MACRO_DIR))

import global_dollar_liquidity_layer_sim as dollar
import global_yield_curve_layer_sim as yields
import macro_run_orchestrator_sim as orchestrator
from global_macro_feedback_calibration_sim import MacroFeedbackParams


def policy_path(
    policies: list[float],
    *,
    qe: float | list[float] = 0.0,
    neutral: float = 2.5,
    headline: float = 2.3,
    expectation: float = 2.2,
    output_gap: float = 0.0,
    potential_growth: float = 2.0,
    stress: float = 30.0,
    crisis: float = 0.0,
    stance: float | None = None,
    seed: int = 20261324,
) -> list[dict[str, float | int]]:
    qes = qe if isinstance(qe, list) else [qe] * len(policies)
    rows: list[dict[str, float | int]] = []
    previous = policies[0]
    for index, (policy_rate, qe_value) in enumerate(zip(policies, qes, strict=True)):
        effective_stance = (
            stance if stance is not None else policy_rate - expectation - 0.75
        )
        rows.append(
            {
                "seed": seed,
                "year_index": index,
                "year": 2025 + index,
                "global_policy_rate_pct": policy_rate,
                "policy_rate_change_pct": policy_rate - previous,
                "neutral_policy_rate_pct": neutral,
                "real_policy_rate_pct": policy_rate - expectation,
                "policy_stance_index": effective_stance,
                "headline_inflation_pct": headline,
                "inflation_expectation_pct": expectation,
                "output_gap_pct": output_gap,
                "potential_growth_pct": potential_growth,
                "financial_stress_index": stress,
                "crisis_intensity": crisis,
                "qe_liquidity_index": qe_value,
                "balance_sheet_impulse": 0.0,
                "rate_hike_pressure": 20.0,
                "rate_cut_pressure": 20.0,
                "inflation_to_long_rate_impulse": 0.0,
                "realized_growth_pct": potential_growth,
            }
        )
        previous = policy_rate
    return rows


class YieldCurveDiagnosticTests(unittest.TestCase):
    def test_diagnostic_targets_and_boundary_flags_are_prebound_values(self) -> None:
        params = yields.YieldCurveParams(
            initial_short_rate_pct=0.4,
            initial_2y_yield_pct=0.4,
            initial_10y_yield_pct=0.4,
            initial_term_premium_pct=0.0,
            initial_expected_short_rate_10y_pct=0.4,
            initial_expected_shadow_short_rate_10y_pct=0.4,
            max_yield_pct=0.5,
            max_observable_expected_short_rate_pct=0.5,
            max_shadow_expected_short_rate_pct=0.5,
            max_term_premium_pct=0.10,
        )
        rows = policy_path(
            [0.4, 8.0],
            neutral=6.0,
            headline=7.0,
            expectation=4.0,
            output_gap=3.0,
            stress=70.0,
            stance=3.0,
        )
        # year_index=0 is now the configured initial state; diagnose the first
        # real transition at year_index=1.
        result = yields.simulate_yield_curve_for_policy_path(rows, params)[1]

        self.assertGreater(result["unclamped_short_rate_target_pct"], params.max_yield_pct)
        self.assertTrue(result["short_rate_cap_applied"])
        self.assertEqual(params.max_yield_pct, result["global_short_rate_pct"])
        self.assertGreater(
            result["unclamped_expected_short_rate_10y_target_pct"],
            params.max_observable_expected_short_rate_pct,
        )
        self.assertTrue(result["expected_short_rate_cap_applied"])
        self.assertGreater(
            result["unclamped_term_premium_target_pct"],
            params.max_term_premium_pct,
        )
        self.assertTrue(result["term_premium_cap_applied"])
        self.assertNotEqual(
            result["unclamped_2y_yield_target_pct"], result["global_2y_yield_pct"]
        )
        self.assertNotEqual(
            result["unclamped_10y_yield_target_pct"], result["global_10y_yield_pct"]
        )

    def test_observable_short_rate_is_not_the_negative_qe_state(self) -> None:
        no_qe = yields.simulate_yield_curve_for_policy_path(
            policy_path([0.05] * 20, qe=0.0, neutral=0.35, stance=-2.0),
            yields.YieldCurveParams(),
        )
        with_qe = yields.simulate_yield_curve_for_policy_path(
            policy_path([0.05] * 20, qe=100.0, neutral=0.35, stance=-2.0),
            yields.YieldCurveParams(),
        )
        self.assertEqual(
            [row["expected_short_rate_10y_pct"] for row in no_qe],
            [row["expected_short_rate_10y_pct"] for row in with_qe],
        )
        self.assertGreaterEqual(
            min(row["expected_short_rate_10y_pct"] for row in with_qe), 0.05
        )
        self.assertLess(
            with_qe[-1]["expected_shadow_short_rate_10y_pct"],
            with_qe[-1]["expected_short_rate_10y_pct"],
        )
        self.assertLess(with_qe[-1]["expected_shadow_short_rate_10y_pct"], 0.0)
        self.assertLess(with_qe[-1]["term_premium_pct"], no_qe[-1]["term_premium_pct"])

    def test_shadow_short_rate_reverts_smoothly_after_qe_exit(self) -> None:
        qes = [80.0] * 5 + [0.0] * 15
        rows = yields.simulate_yield_curve_for_policy_path(
            policy_path([0.5] * len(qes), qe=qes, neutral=1.5, stance=-1.0),
            yields.YieldCurveParams(),
        )
        gap_at_exit = abs(
            rows[5]["expected_shadow_short_rate_10y_pct"]
            - rows[5]["expected_short_rate_10y_pct"]
        )
        final_gap = abs(
            rows[-1]["expected_shadow_short_rate_10y_pct"]
            - rows[-1]["expected_short_rate_10y_pct"]
        )
        self.assertLess(final_gap, gap_at_exit)
        self.assertLess(final_gap, 0.05)
        max_jump = max(
            abs(current["global_10y_yield_pct"] - previous["global_10y_yield_pct"])
            for previous, current in zip(rows[:-1], rows[1:], strict=True)
        )
        self.assertLess(max_jump, 1.0)

    def test_sustained_zero_qe_exit_closes_shadow_gap_in_late_window(self) -> None:
        qes = [80.0] * 5 + [0.0] * 20
        rows = yields.simulate_yield_curve_for_policy_path(
            policy_path([0.5] * len(qes), qe=qes, neutral=1.5, stance=-1.0),
            yields.YieldCurveParams(),
        )
        late_gaps = [
            abs(
                row["expected_shadow_short_rate_10y_pct"]
                - row["expected_short_rate_10y_pct"]
            )
            for row in rows[-10:]
        ]
        self.assertTrue(
            all(
                current <= previous + 1e-4
                for previous, current in zip(
                    late_gaps[:-1], late_gaps[1:], strict=True
                )
            )
        )
        self.assertLess(late_gaps[-1], 0.02)
        self.assertFalse(any(row["shadow_short_rate_floor_applied"] for row in rows[5:]))

    def test_yield_identities_and_consecutive_boundary_counts_hold(self) -> None:
        params = yields.YieldCurveParams(
            initial_short_rate_pct=-0.30,
            initial_2y_yield_pct=-0.30,
            initial_10y_yield_pct=0.20,
            initial_expected_short_rate_10y_pct=0.10,
            initial_expected_shadow_short_rate_10y_pct=-0.20,
        )
        rows = yields.simulate_yield_curve_for_policy_path(
            policy_path(
                [0.05] * 8,
                qe=90.0,
                neutral=0.35,
                expectation=1.5,
                output_gap=-5.0,
                stress=70.0,
                crisis=0.8,
                stance=-2.0,
            ),
            params,
        )
        for row in rows:
            self.assertAlmostEqual(
                row["global_10y_yield_pct"] - row["inflation_expectation_pct"],
                row["global_real_10y_yield_pct"],
                delta=0.00011,
            )
            self.assertAlmostEqual(
                row["global_10y_yield_pct"] - row["global_2y_yield_pct"],
                row["term_spread_10y_2y_pct"],
                delta=0.00011,
            )
        for field, flag_a, flag_b in (
            ("yield_2y_consecutive_boundary_years", "yield_2y_floor_applied", "yield_2y_cap_applied"),
            ("yield_10y_consecutive_boundary_years", "yield_10y_floor_applied", "yield_10y_cap_applied"),
        ):
            run = 0
            for row in rows:
                run = run + 1 if row[flag_a] or row[flag_b] else 0
                self.assertEqual(run, row[field])


class DirectionMatrixTests(unittest.TestCase):
    def test_normal_expansion_rate_cut_and_inversion_directions(self) -> None:
        normal = yields.simulate_yield_curve_for_policy_path(
            policy_path([3.0] * 8, qe=0.0), yields.YieldCurveParams()
        )
        self.assertGreater(normal[-1]["global_2y_yield_pct"], 2.0)
        self.assertNotEqual(
            normal[-1]["global_10y_yield_pct"], normal[-1]["global_2y_yield_pct"]
        )

        cut = yields.simulate_yield_curve_for_policy_path(
            policy_path([4.0, 4.0, 4.0, 2.0, 1.0, 1.0]),
            yields.YieldCurveParams(),
        )
        two_year_move = cut[3]["global_2y_yield_pct"] - cut[2]["global_2y_yield_pct"]
        ten_year_move = cut[3]["global_10y_yield_pct"] - cut[2]["global_10y_yield_pct"]
        self.assertLess(two_year_move, 0.0)
        self.assertLess(ten_year_move, 0.0)
        self.assertGreater(abs(two_year_move), abs(ten_year_move))

        inverted = yields.simulate_yield_curve_for_policy_path(
            policy_path(
                [5.0] * 8,
                neutral=2.0,
                headline=1.0,
                expectation=1.0,
                output_gap=-1.0,
                potential_growth=1.5,
                stance=2.0,
            ),
            yields.YieldCurveParams(),
        )
        self.assertTrue(any(row["global_2y_yield_pct"] > row["global_10y_yield_pct"] for row in inverted))
        self.assertTrue(
            all(row["term_spread_10y_2y_pct"] < 0.0 for row in inverted[1:])
        )

    def test_qe_and_inflation_directions(self) -> None:
        no_qe = yields.simulate_yield_curve_for_policy_path(
            policy_path([0.5] * 12, qe=0.0, neutral=1.5, stance=-1.0),
            yields.YieldCurveParams(),
        )
        qe = yields.simulate_yield_curve_for_policy_path(
            policy_path([0.5] * 12, qe=80.0, neutral=1.5, stance=-1.0),
            yields.YieldCurveParams(),
        )
        self.assertLess(qe[-1]["expected_shadow_short_rate_10y_pct"], no_qe[-1]["expected_shadow_short_rate_10y_pct"])
        self.assertLess(qe[-1]["term_premium_pct"], no_qe[-1]["term_premium_pct"])
        self.assertLess(qe[-1]["global_10y_yield_pct"], no_qe[-1]["global_10y_yield_pct"])
        self.assertEqual(qe[-1]["expected_short_rate_10y_pct"], no_qe[-1]["expected_short_rate_10y_pct"])

        calm = yields.simulate_yield_curve_for_policy_path(
            policy_path([2.0] * 8, headline=2.0, expectation=2.0),
            yields.YieldCurveParams(),
        )
        inflation = yields.simulate_yield_curve_for_policy_path(
            policy_path([2.0] * 8, headline=5.0, expectation=4.0),
            yields.YieldCurveParams(),
        )
        self.assertGreater(inflation[-1]["term_premium_pct"], calm[-1]["term_premium_pct"])
        self.assertGreater(inflation[-1]["global_10y_yield_pct"], calm[-1]["global_10y_yield_pct"])

    def test_crisis_safe_haven_and_liquidity_repair_directions(self) -> None:
        calm_yields = yields.simulate_yield_curve_for_policy_path(
            policy_path([1.0] * 10, stress=30.0, crisis=0.0, stance=-0.5),
            yields.YieldCurveParams(),
        )
        crisis_yields = yields.simulate_yield_curve_for_policy_path(
            policy_path([1.0] * 10, stress=70.0, crisis=0.8, stance=-0.5),
            yields.YieldCurveParams(),
        )
        calm = dollar.simulate_dollar_liquidity_for_yield_path(
            calm_yields, dollar.DollarLiquidityParams()
        )
        crisis = dollar.simulate_dollar_liquidity_for_yield_path(
            crisis_yields, dollar.DollarLiquidityParams()
        )
        self.assertGreater(crisis[-1]["global_dollar_index"], calm[-1]["global_dollar_index"])
        self.assertGreater(
            crisis[-1]["global_financial_conditions_index"],
            calm[-1]["global_financial_conditions_index"],
        )

        repair_qe = [80.0] * 5 + [0.0] * 15
        repair_yields = yields.simulate_yield_curve_for_policy_path(
            policy_path([0.5] * 20, qe=repair_qe, neutral=1.5, stance=-1.0),
            yields.YieldCurveParams(),
        )
        repair = dollar.simulate_dollar_liquidity_for_yield_path(
            repair_yields, dollar.DollarLiquidityParams()
        )
        self.assertLess(
            abs(repair[-1]["global_financial_conditions_index"]),
            abs(repair[4]["global_financial_conditions_index"]),
        )
        self.assertLess(repair[-1]["financial_conditions_consecutive_boundary_years"], 3)


class DollarDiagnosticAndIntegrationTests(unittest.TestCase):
    def test_dollar_and_fci_diagnostics_are_true_prebound_targets(self) -> None:
        yield_rows = yields.simulate_yield_curve_for_policy_path(
            policy_path([4.0] * 5, stress=90.0, crisis=1.0, stance=2.0),
            yields.YieldCurveParams(),
        )
        params = dollar.DollarLiquidityParams(
            initial_dollar_index=100.0,
            min_dollar_index=99.0,
            max_dollar_index=101.0,
            min_financial_conditions_index=-0.2,
            max_financial_conditions_index=0.2,
        )
        rows = dollar.simulate_dollar_liquidity_for_yield_path(yield_rows, params)
        self.assertTrue(any(row["dollar_cap_applied"] for row in rows))
        capped = next(row for row in rows if row["dollar_cap_applied"])
        self.assertGreater(capped["unclamped_dollar_target_index"], params.max_dollar_index)
        self.assertEqual(params.max_dollar_index, capped["global_dollar_index"])
        self.assertTrue(any(row["financial_conditions_cap_applied"] for row in rows))
        fci_capped = next(row for row in rows if row["financial_conditions_cap_applied"])
        self.assertGreater(
            fci_capped["unclamped_financial_conditions_target_index"],
            params.max_financial_conditions_index,
        )
        self.assertEqual(
            params.max_financial_conditions_index,
            fci_capped["global_financial_conditions_index"],
        )

    def test_versioned_boundaries_and_viewer_proxy_wording(self) -> None:
        self.assertEqual("yield-curve-boundaries-v1", yields.YIELD_CURVE_BOUNDARY_VERSION)
        self.assertEqual(
            "dollar-liquidity-boundaries-v1", dollar.DOLLAR_LIQUIDITY_BOUNDARY_VERSION
        )
        renderer = (ROOT_DIR / "web/static/js/global-gdp/renderers.js").read_text(encoding="utf-8")
        html = (ROOT_DIR / "web/pages/global_gdp_viewer.html").read_text(encoding="utf-8")
        client = (ROOT_DIR / "web/static/js/global-gdp/data-client.js").read_text(encoding="utf-8")
        self.assertIn("美元资金条件指数", renderer)
        self.assertIn("美元资金", html)
        self.assertNotIn('const currencyLabel = isRegional ? "货币指数" : "美元指数"', renderer)
        self.assertIn("expected_shadow_short_rate_10y_pct", client)
        self.assertIn("unclamped_dollar_target_index", client)

    def test_global_candidate_propagates_without_new_regional_bound_clusters(self) -> None:
        defaults = MacroFeedbackParams()
        args = argparse.Namespace(
            years=4,
            start_year=2025,
            initial_gdp=100.0,
            volatility_scale=1.0,
            feedback_iterations=defaults.max_feedback_iterations,
            min_feedback_iterations=defaults.min_feedback_iterations,
        )
        global_result = orchestrator.run_global_variant(20261324, args, "baseline")
        self.assertTrue(global_result["convergence"]["converged"])
        rows = global_result["rows"]
        self.assertIn("expected_shadow_short_rate_10y_pct", rows[0])
        regional = orchestrator.run_regional_and_reconciliation(20261324, rows)
        for region_rows in regional["regional_rows_by_region"].values():
            for row in region_rows:
                self.assertGreaterEqual(row["regional_10y_yield_pct"], 0.05)
                self.assertLessEqual(row["regional_10y_yield_pct"], 11.0)
        for diagnostic in regional["diagnostics"]:
            self.assertTrue(math.isfinite(diagnostic["ten_year_gap_reconciled_pp"]))
            self.assertTrue(math.isfinite(diagnostic["policy_rate_gap_reconciled_pp"]))


if __name__ == "__main__":
    unittest.main()
