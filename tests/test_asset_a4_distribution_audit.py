from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools import audit_asset_joint_distribution as audit


class AssetA4PureAuditTests(unittest.TestCase):
    def test_default_cohort_has_eighty_baseline_seeds_plus_named_seed(self) -> None:
        self.assertEqual(81, len(audit.DEFAULT_AUDIT_SEEDS))
        self.assertEqual(81, len(set(audit.DEFAULT_AUDIT_SEEDS)))
        self.assertIn(20260622, audit.DEFAULT_AUDIT_SEEDS)

    def test_longest_bond_outperformance_run_is_contiguous(self) -> None:
        self.assertEqual(
            {"years": 3, "start_year": 2031, "end_year": 2033},
            audit.longest_true_run(
                [False, True, True, True, False, True],
                [2030, 2031, 2032, 2033, 2034, 2035],
            ),
        )

    def test_named_seed_diagnosis_distinguishes_pe_compression_from_earnings_failure(self) -> None:
        summary = {
            "seed": 20260622,
            "late_eps_growth_avg_pct": 4.1,
            "late_pe_start": 19.4,
            "late_pe_end": 9.4,
            "late_pe_change_pct": -51.5,
            "late_equity_total_return_avg_pct": 3.9,
            "late_sovereign_bond_total_return_avg_pct": 2.5,
            "trailing_10_equity_minus_bond_avg_pp": -2.2,
            "late_real_10y_yield_avg_pct": 1.0,
            "late_sovereign_bond_carry_avg_pct": 3.1,
            "longest_bond_outperformance_run": {
                "years": 8,
                "start_year": 2076,
                "end_year": 2083,
            },
            "late_pe_contribution_means": {
                "rate": -1.5,
                "credit": -0.4,
                "liquidity": -0.2,
                "risk_appetite": -0.1,
            },
        }
        diagnosis = audit.diagnose_named_seed(summary)
        self.assertEqual(
            "valuation_compression_with_positive_earnings_and_high_bond_carry",
            diagnosis["classification"],
        )
        self.assertTrue(diagnosis["economically_plausible"])
        self.assertEqual("rate", diagnosis["negative_pe_drivers"][0]["driver"])

    def test_percentiles_use_linear_interpolation(self) -> None:
        values = [1.0, 2.0, 3.0, 4.0]
        self.assertEqual(2.5, audit.percentile(values, 0.5))
        self.assertEqual(1.75, audit.percentile(values, 0.25))


class AssetA4EndToEndAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = audit.run_audit(
            [20260622],
            years=4,
            late_start_year_index=2,
            named_seed=20260622,
        )

    def test_short_formal_audit_covers_all_regions_and_reconstructs_consumers(self) -> None:
        self.assertEqual("airport-model-v0.16", self.report["model_version"])
        self.assertEqual("airport-model-output-v6", self.report["output_schema_version"])
        self.assertEqual(1, self.report["seed_count"])
        regional = self.report["seed_summaries"][0]["regional_aviation"]
        self.assertEqual(14, regional["region_count"])
        self.assertLessEqual(regional["regional_identity_max_abs_residual"], 0.0001)
        self.assertLessEqual(regional["demand_reconstruction_max_abs_error"], 0.0002)
        self.assertLessEqual(regional["commercial_reconstruction_max_abs_error"], 0.0002)

    def test_reports_round_trip_as_json_and_csv(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            json_path, csv_path = audit.write_reports(
                self.report,
                Path(temporary_dir),
            )
            loaded = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(audit.AUDIT_VERSION, loaded["audit_version"])
            self.assertEqual(2, len(csv_path.read_text(encoding="utf-8").splitlines()))

    def test_controlled_deflation_world_is_explicit_and_reaches_all_downstream_regions(self) -> None:
        world = audit.run_controlled_deflation_world(
            years=60,
            late_start_year_index=40,
        )
        self.assertEqual(
            "controlled_parameter_counterexample_not_baseline_seed",
            world["authority"],
        )
        self.assertGreater(world["global"]["regime_year_counts"]["deflation"], 0)
        self.assertEqual(14, world["regional_aviation"]["region_count"])


if __name__ == "__main__":
    unittest.main()
