from __future__ import annotations

import argparse
import sys
import unittest
from collections import defaultdict
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
MACRO_DIR = ROOT_DIR / "macro_layers"
if str(MACRO_DIR) not in sys.path:
    sys.path.insert(0, str(MACRO_DIR))

import macro_run_orchestrator_sim as orchestrator  # noqa: E402
import regional_macro_reconciliation_sim as reconciliation  # noqa: E402


RECONCILED_OUTPUT_FIELDS = {
    "regional_headline_inflation_pct_reconciled": "regional_headline_inflation_pct",
    "regional_core_inflation_pct_reconciled": "regional_core_inflation_pct",
    "regional_policy_rate_pct_reconciled": "regional_policy_rate_pct",
    "regional_10y_yield_pct_reconciled": "regional_10y_yield_pct",
    "regional_hy_spread_bps_reconciled": "regional_hy_spread_bps",
    "regional_ig_spread_bps_reconciled": "regional_ig_spread_bps",
    "regional_macro_stress_index_reconciled": "regional_macro_stress_index",
    "regional_equity_return_pct_reconciled": "regional_equity_return_pct",
    "regional_equity_valuation_pe_reconciled": "regional_equity_valuation_pe",
    "regional_energy_cost_pressure_index_reconciled": "regional_energy_cost_pressure_index",
}

RECONCILIATION_DIAGNOSTICS = (
    (
        "regional_headline_inflation_pct_reconciled",
        "weighted_regional_headline_inflation_reconciled_pct",
        "global_headline_inflation_anchor_pct",
        "headline_inflation_gap_reconciled_pp",
    ),
    (
        "regional_core_inflation_pct_reconciled",
        "weighted_regional_core_inflation_reconciled_pct",
        "global_core_inflation_anchor_pct",
        "core_inflation_gap_reconciled_pp",
    ),
    (
        "regional_policy_rate_pct_reconciled",
        "weighted_regional_policy_rate_reconciled_pct",
        "global_policy_rate_anchor_pct",
        "policy_rate_gap_reconciled_pp",
    ),
    (
        "regional_10y_yield_pct_reconciled",
        "weighted_regional_10y_reconciled_pct",
        "global_10y_anchor_pct",
        "ten_year_gap_reconciled_pp",
    ),
    (
        "regional_hy_spread_bps_reconciled",
        "weighted_regional_hy_reconciled_bps",
        "global_hy_anchor_bps",
        "hy_gap_reconciled_bps",
    ),
    (
        "regional_ig_spread_bps_reconciled",
        "weighted_regional_ig_reconciled_bps",
        "global_ig_anchor_bps",
        "ig_gap_reconciled_bps",
    ),
    (
        "regional_macro_stress_index_reconciled",
        "weighted_regional_macro_stress_reconciled_index",
        "global_financial_stress_anchor_index",
        "macro_stress_gap_reconciled_index",
    ),
    (
        "regional_equity_return_pct_reconciled",
        "weighted_regional_equity_return_reconciled_pct",
        "global_equity_return_anchor_pct",
        "equity_return_gap_reconciled_pp",
    ),
    (
        "regional_equity_valuation_pe_reconciled",
        "weighted_regional_equity_valuation_pe_reconciled",
        "global_equity_valuation_pe_anchor",
        "equity_valuation_pe_gap_reconciled",
    ),
    (
        "regional_energy_cost_pressure_index_reconciled",
        "weighted_regional_energy_cost_reconciled_index",
        "global_energy_cost_anchor_index",
        "energy_cost_gap_reconciled_index",
    ),
)


def _baseline_args() -> argparse.Namespace:
    return argparse.Namespace(
        years=60,
        start_year=2025,
        initial_gdp=100.0,
        volatility_scale=1.0,
        feedback_iterations=3,
    )


class MergeFeedbackPathsTests(unittest.TestCase):
    """Working Guide 1.1: preserve macro feedback diagnostics when paths merge."""

    def test_baseline_keeps_macro_raw_diagnostics_and_intensity(self) -> None:
        # No scenario feedback, so the macro path is the only contributor. The
        # merged path must keep the raw diagnostics and the intensity index instead
        # of zeroing them the way the orchestrator used to.
        macro = {
            3: {
                "feedback_growth_impulse_pct": -0.18,
                "feedback_output_gap_impulse_pct": -0.12,
                "feedback_financial_stress_impulse": 1.4,
                "feedback_inflation_impulse_pct": 0.06,
                "feedback_policy_impulse_pct": 0.04,
                "feedback_source": "lagged_macro_feedback_from_year_2025",
                "macro_feedback_intensity_index": 9.5,
                "macro_feedback_growth_raw_pct": -0.22,
                "macro_feedback_stress_raw": 2.1,
                "macro_feedback_inflation_raw_pct": 0.07,
                "macro_feedback_policy_raw_pct": 0.05,
            }
        }
        merged = orchestrator.merge_feedback_paths(macro, None)
        row = merged[3]
        self.assertAlmostEqual(row["macro_feedback_growth_raw_pct"], -0.22)
        self.assertAlmostEqual(row["macro_feedback_stress_raw"], 2.1)
        self.assertAlmostEqual(row["macro_feedback_inflation_raw_pct"], 0.07)
        self.assertAlmostEqual(row["macro_feedback_policy_raw_pct"], 0.05)
        # Intensity is recomputed from the applied macro impulses (not the stored
        # blended value), so it matches the calibration formula for these inputs.
        expected = orchestrator.macro_feedback_intensity_from_applied(
            -0.18, 1.4, 0.06, 0.04
        )
        self.assertAlmostEqual(row["macro_feedback_intensity_index"], expected)
        self.assertTrue(row["macro_feedback_intensity_index"] > 0.0)

    def test_scenario_does_not_masquerade_as_macro_raw_diagnostics(self) -> None:
        macro = {
            3: {
                "feedback_growth_impulse_pct": -0.10,
                "feedback_financial_stress_impulse": 0.5,
                "feedback_inflation_impulse_pct": 0.02,
                "feedback_policy_impulse_pct": 0.01,
                "feedback_source": "lagged_macro_feedback",
                "macro_feedback_intensity_index": 3.0,
                "macro_feedback_growth_raw_pct": -0.12,
                "macro_feedback_stress_raw": 0.8,
                "macro_feedback_inflation_raw_pct": 0.03,
                "macro_feedback_policy_raw_pct": 0.02,
            }
        }
        scenario = {
            3: {
                "feedback_growth_impulse_pct": -0.80,
                "feedback_financial_stress_impulse": 4.0,
                "feedback_inflation_impulse_pct": 0.30,
                "feedback_policy_impulse_pct": 0.20,
                "feedback_source": "branch_credit_accident_impact",
                "macro_feedback_growth_raw_pct": 99.0,  # must not leak through
                "macro_feedback_stress_raw": 99.0,
                "scenario_risk_id": "credit_accident",
            }
        }
        merged = orchestrator.merge_feedback_paths(macro, scenario)
        row = merged[3]
        # Applied impulses add (macro + scenario).
        self.assertAlmostEqual(row["feedback_growth_impulse_pct"], -0.90)
        self.assertAlmostEqual(row["feedback_financial_stress_impulse"], 4.5)
        # Macro raw diagnostics keep the macro values, never the scenario values.
        self.assertAlmostEqual(row["macro_feedback_growth_raw_pct"], -0.12)
        self.assertAlmostEqual(row["macro_feedback_stress_raw"], 0.8)
        self.assertAlmostEqual(row["macro_feedback_inflation_raw_pct"], 0.03)
        self.assertAlmostEqual(row["macro_feedback_policy_raw_pct"], 0.02)
        # Intensity reflects macro-applied impulses only, so a loud scenario branch
        # cannot inflate the macro feedback intensity read by the regional layer.
        macro_only_intensity = orchestrator.macro_feedback_intensity_from_applied(
            -0.10, 0.5, 0.02, 0.01
        )
        self.assertAlmostEqual(row["macro_feedback_intensity_index"], macro_only_intensity)
        self.assertTrue(row["macro_feedback_intensity_index"] < macro_only_intensity + 1e-9)

    def test_years_without_feedback_remain_zero(self) -> None:
        merged = orchestrator.merge_feedback_paths({}, None)
        self.assertEqual(merged, {})

    def test_global_rows_carry_nonzero_intensity_for_feedback_years(self) -> None:
        args = _baseline_args()
        result = orchestrator.run_global_variant(20261324, args, "baseline")
        rows = result["rows"]
        nonzero = [r for r in rows if r["macro_feedback_intensity_index"]]
        self.assertTrue(nonzero, "feedback years must carry nonzero intensity")
        # Year 0 has no lagged feedback yet.
        self.assertEqual(rows[0]["macro_feedback_intensity_index"], 0.0)
        self.assertEqual(rows[0]["macro_feedback_growth_raw_pct"], 0.0)


class ReconciliationBoundaryTests(unittest.TestCase):
    """Working Guide 1.2: re-clamp reconciled regional fields to published bounds."""

    @classmethod
    def setUpClass(cls) -> None:
        args = _baseline_args()
        global_result = orchestrator.run_global_variant(20261324, args, "baseline")
        cls.regional = orchestrator.run_regional_and_reconciliation(
            20261324, global_result["rows"]
        )

    def test_reconciled_fields_respect_published_bounds(self) -> None:
        rows = self.regional["reconciled_rows"]
        self.assertTrue(rows)
        for row in rows:
            bounds = reconciliation.reconciled_field_bounds(str(row["region_id"]))
            for output_field, source_field in RECONCILED_OUTPUT_FIELDS.items():
                value = float(row[output_field])
                floor, ceiling = bounds[source_field]
                self.assertGreaterEqual(value, floor, output_field)
                self.assertLessEqual(value, ceiling, output_field)

    def test_diagnostics_record_clamp_counts_and_residuals(self) -> None:
        diagnostics = self.regional["diagnostics"]
        self.assertTrue(diagnostics)
        # New diagnostic fields exist on every row.
        for diag in diagnostics:
            self.assertIn("total_field_clamps", diag)
            self.assertIn("fields_with_clamped_regions", diag)
            self.assertIn("policy_rate_clamped_region_count", diag)
            self.assertIn("ten_year_clamped_region_count", diag)
            self.assertEqual(
                diag["fields_with_clamped_regions"],
                sum(1 for key in diag if key.endswith("_clamped_region_count") and diag[key] > 0),
            )
        # Over a 60-year path the clamps must actually trigger somewhere.
        total_clamps = sum(int(diag["total_field_clamps"]) for diag in diagnostics)
        self.assertGreater(total_clamps, 0)

        rows_by_key: dict[tuple[int, int], list[dict[str, object]]] = defaultdict(list)
        for row in self.regional["reconciled_rows"]:
            rows_by_key[(int(row["seed"]), int(row["year_index"]))].append(row)

        for diag in diagnostics:
            key = (int(diag["seed"]), int(diag["year_index"]))
            year_rows = rows_by_key[key]
            for output_field, weighted_field, anchor_field, gap_field in RECONCILIATION_DIAGNOSTICS:
                weighted_from_rows = sum(
                    float(row["regional_reconciled_share_of_global_gdp_pct"])
                    / 100.0
                    * float(row[output_field])
                    for row in year_rows
                )
                self.assertAlmostEqual(
                    weighted_from_rows,
                    float(diag[weighted_field]),
                    delta=0.002,
                    msg=weighted_field,
                )
                self.assertAlmostEqual(
                    float(diag[weighted_field]) - float(diag[anchor_field]),
                    float(diag[gap_field]),
                    delta=0.0002,
                    msg=gap_field,
                )

    def test_gdp_hard_reconciliation_unaffected_by_clamping(self) -> None:
        rows = self.regional["reconciled_rows"]
        shares = defaultdict(float)
        for row in rows:
            key = (int(row["seed"]), int(row["year_index"]))
            shares[key] += float(row["regional_reconciled_share_of_global_gdp_pct"])
        # Regional reconciled shares still sum to 100% (hard GDP reconciliation);
        # residual is display rounding from round_record, not a reconciliation break.
        self.assertLess(max(abs(value - 100.0) for value in shares.values()), 1e-3)

    def test_clamp_table_matches_raw_layer_bounds(self) -> None:
        bounds = reconciliation.RECONCILED_FIELD_BOUNDS
        self.assertIs(
            bounds,
            orchestrator.regional_macro_layer.REGIONAL_RECONCILED_FIELD_BOUNDS,
        )
        self.assertEqual(bounds["regional_10y_yield_pct"], (0.05, 11.0))
        self.assertEqual(bounds["regional_macro_stress_index"], (0.0, 100.0))
        self.assertEqual(bounds["regional_energy_cost_pressure_index"], (0.0, 100.0))
        # Policy-rate bounds are per-region, resolved at clamp time.
        na_bounds = reconciliation.reconciled_field_bounds("north_america")
        self.assertIn("regional_policy_rate_pct", na_bounds)
        self.assertEqual(
            reconciliation.RECONCILIATION_PARAM_VERSION,
            "regional-macro-reconciliation-v0.4",
        )


if __name__ == "__main__":
    unittest.main()
