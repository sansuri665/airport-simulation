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

import global_gdp_annual_sim as gdp
import global_macro_feedback_calibration_sim as feedback
import global_policy_rate_layer_sim as policy
import macro_run_orchestrator_sim as orchestrator
from global_macro_feedback_calibration_sim import MacroFeedbackParams


class GrowthSoftLimiterTests(unittest.TestCase):
    def test_soft_limiter_is_symmetric_continuous_and_strictly_monotone(self) -> None:
        knee = 1.30
        scale = 1.80
        self.assertEqual(knee, gdp.soft_compress_growth_target_step(knee, knee, scale))
        self.assertAlmostEqual(
            -gdp.soft_compress_growth_target_step(4.0, knee, scale),
            gdp.soft_compress_growth_target_step(-4.0, knee, scale),
        )
        left = gdp.soft_compress_growth_target_step(knee - 1e-7, knee, scale)
        right = gdp.soft_compress_growth_target_step(knee + 1e-7, knee, scale)
        self.assertAlmostEqual(left, right, delta=3e-7)
        values = [
            gdp.soft_compress_growth_target_step(value, knee, scale)
            for value in (0.0, 0.5, 1.3, 1.5, 2.0, 3.0, 6.0)
        ]
        self.assertTrue(all(a < b for a, b in zip(values, values[1:])))
        self.assertLess(values[-1], 6.0)

    def test_invalid_soft_limiter_parameters_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            gdp.soft_compress_growth_target_step(1.0, 0.0, 1.0)
        with self.assertRaises(ValueError):
            gdp.soft_compress_growth_target_step(1.0, 1.0, 0.0)


class GDPGapDiagnosticTests(unittest.TestCase):
    def test_financial_stress_channel_is_symmetric_around_its_anchor(self) -> None:
        params = gdp.GDPParams(
            output_gap_financial_stress_anchor_index=35.0,
            output_gap_financial_stress_loading=0.03,
        )
        self.assertEqual(0.0, gdp.financial_stress_gap_impulse(35.0, params))
        recovery = gdp.financial_stress_gap_impulse(20.0, params)
        drag = gdp.financial_stress_gap_impulse(50.0, params)
        self.assertGreater(recovery, 0.0)
        self.assertLess(drag, 0.0)
        self.assertAlmostEqual(recovery, -drag)

    def test_strict_gap_and_residual_are_computed_from_published_indices(self) -> None:
        rows = gdp.simulate_global_gdp(
            20261324,
            gdp.GDPParams(years=12, volatility_scale=1.0),
        )
        for row in rows:
            strict_gap = 100.0 * math.log(
                float(row["real_gdp_index"]) / float(row["potential_gdp_index"])
            )
            self.assertAlmostEqual(strict_gap, float(row["gdp_level_gap_pct"]), delta=0.000051)
            self.assertAlmostEqual(
                float(row["output_gap_pct"]) - float(row["gdp_level_gap_pct"]),
                float(row["output_gap_measurement_residual_pct"]),
                delta=0.000051,
            )

    def test_gap_bound_diagnostics_use_the_true_preclamp_candidate(self) -> None:
        params = gdp.GDPParams(
            years=3,
            volatility_scale=0.01,
            output_gap_cap_pct=0.05,
        )
        feedback = {
            index: {
                "feedback_output_gap_impulse_pct": 1.8,
                "feedback_source": "contract_test",
            }
            for index in range(1, 4)
        }
        rows = gdp.simulate_global_gdp(20261324, params, feedback)
        capped = [row for row in rows[1:] if row["output_gap_cap_applied"]]
        self.assertTrue(capped)
        for row in capped:
            self.assertGreater(float(row["unclamped_output_gap_target_pct"]), 0.05)
            self.assertEqual(0.05, float(row["output_gap_pct"]))
            self.assertFalse(row["output_gap_floor_applied"])

    def test_growth_diagnostics_distinguish_soft_and_hard_limits(self) -> None:
        params = gdp.GDPParams(
            years=8,
            volatility_scale=0.01,
            growth_soft_limit_knee_pct=0.05,
            growth_soft_limit_scale_pct=0.08,
            max_growth_step_pct=0.10,
        )
        feedback = {
            index: {
                "feedback_growth_impulse_pct": 1.05 if index % 2 else -1.8,
                "feedback_output_gap_impulse_pct": 1.4 if index % 2 else -2.2,
                "feedback_source": "contract_test",
            }
            for index in range(1, 9)
        }
        rows = gdp.simulate_global_gdp(20261324, params, feedback)
        self.assertTrue(any(row["growth_soft_limit_applied"] for row in rows[1:]))
        self.assertTrue(any(row["growth_step_cap_applied"] for row in rows[1:]))
        for previous, row in zip(rows, rows[1:], strict=False):
            step = float(row["realized_growth_pct"]) - float(previous["realized_growth_pct"])
            if row["growth_step_cap_applied"]:
                self.assertAlmostEqual(abs(step), 0.10, delta=0.00011)
                self.assertEqual("up" if step > 0 else "down", row["growth_step_cap_direction"])


class DownstreamGapSemanticsTests(unittest.TestCase):
    def test_output_gap_feedback_does_not_reinject_growth_or_hy(self) -> None:
        common = {
            "year_index": 1,
            "year": 2026,
            "bank_lending_sentiment_index": 48.0,
            "credit_impairment_stock_index": 10.0,
            "risk_appetite_index": 50.0,
        }
        quiet_rows = [
            {"year_index": 0, "year": 2025},
            dict(common),
            {"year_index": 2, "year": 2027},
        ]
        stressed_rows = [
            {"year_index": 0, "year": 2025},
            {
                **common,
                "credit_to_gdp_drag_placeholder": -4.0,
                "global_high_yield_spread_bps": 1000.0,
            },
            {"year_index": 2, "year": 2027},
        ]
        quiet = feedback.derive_feedback_path(
            quiet_rows,
            feedback.MacroFeedbackParams(),
        )[2]
        stressed = feedback.derive_feedback_path(
            stressed_rows,
            feedback.MacroFeedbackParams(),
        )[2]
        self.assertEqual(
            quiet["feedback_output_gap_impulse_pct"],
            stressed["feedback_output_gap_impulse_pct"],
        )
        self.assertNotEqual(
            quiet["feedback_growth_impulse_pct"],
            stressed["feedback_growth_impulse_pct"],
        )
        self.assertNotEqual(
            quiet["feedback_financial_stress_impulse"],
            stressed["feedback_financial_stress_impulse"],
        )

    def test_policy_reaction_uses_estimated_output_gap(self) -> None:
        params = policy.PolicyRateParams()
        common = dict(
            params=params,
            neutral_policy_rate=3.0,
            headline=2.35,
            core=2.20,
            stress=20.0,
            crisis_intensity=0.0,
            inflation_policy_impulse=0.0,
            event_policy_impulse=0.0,
            feedback_policy_impulse=0.0,
        )
        low = policy.policy_reaction_target_rate(output_gap=-2.0, **common)
        high = policy.policy_reaction_target_rate(output_gap=2.0, **common)
        self.assertLess(low, high)

    def test_regional_rows_propagate_both_global_gap_semantics(self) -> None:
        defaults = MacroFeedbackParams()
        args = argparse.Namespace(
            years=2,
            start_year=2025,
            initial_gdp=100.0,
            volatility_scale=1.0,
            feedback_iterations=defaults.max_feedback_iterations,
            min_feedback_iterations=defaults.min_feedback_iterations,
        )
        global_rows = orchestrator.run_global_variant(20261324, args, "baseline")["rows"]
        regional = orchestrator.run_regional_and_reconciliation(20261324, global_rows)
        for rows in regional["regional_rows_by_region"].values():
            self.assertEqual(len(global_rows), len(rows))
            for global_row, regional_row in zip(global_rows, rows, strict=True):
                self.assertEqual(
                    global_row["output_gap_pct"],
                    regional_row["global_output_gap_anchor_pct"],
                )
                self.assertEqual(
                    global_row["gdp_level_gap_pct"],
                    regional_row["global_gdp_level_gap_anchor_pct"],
                )
                self.assertEqual(
                    global_row["output_gap_measurement_residual_pct"],
                    regional_row["global_output_gap_measurement_residual_anchor_pct"],
                )

    def test_viewer_labels_distinguish_estimated_and_strict_gaps(self) -> None:
        renderer = (ROOT_DIR / "web/static/js/global-gdp/renderers.js").read_text()
        client = (ROOT_DIR / "web/static/js/global-gdp/data-client.js").read_text()
        self.assertIn("模型估计周期缺口", renderer)
        self.assertIn("严格 GDP 水平缺口", renderer)
        self.assertIn("output_gap_measurement_residual_pct", renderer)
        self.assertIn("global_gdp_level_gap_anchor_pct", client)


if __name__ == "__main__":
    unittest.main()
