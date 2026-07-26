from __future__ import annotations

import copy
import math
import unittest
from dataclasses import replace

from macro_layers import global_bond_accounting_v04 as bonds


def macro_row(year_index: int, **overrides: float) -> dict[str, float | int]:
    row: dict[str, float | int] = {
        "seed": 424242,
        "year_index": year_index,
        "year": 2026 + year_index,
        "global_10y_yield_pct": 4.0,
        "global_investment_grade_spread_bps": 100.0,
        "global_equity_total_return_pct": 8.0,
        "default_risk_index": 30.0,
        "credit_impairment_stock_index": 0.0,
        "crisis_intensity": 0.0,
    }
    row.update(overrides)
    return row


def path(*rows: dict[str, float | int]) -> list[dict[str, float | int]]:
    return list(rows)


class GlobalBondV04AccountingTests(unittest.TestCase):
    def test_empty_path_and_non_contiguous_year_index_contract(self) -> None:
        self.assertEqual([], bonds.simulate_global_bond_v04_for_macro_path([]))
        with self.assertRaisesRegex(ValueError, "contiguous year_index"):
            bonds.simulate_global_bond_v04_for_macro_path(
                path(macro_row(0), macro_row(2))
            )
        missing = macro_row(0)
        del missing["year_index"]
        with self.assertRaisesRegex(ValueError, "requires year_index"):
            bonds.simulate_global_bond_v04_for_macro_path([missing])

    def test_initial_row_has_complete_zero_flow_contract(self) -> None:
        inputs = path(macro_row(0))
        row = bonds.simulate_global_bond_v04_for_macro_path(inputs)[0]
        self.assertEqual(
            set(bonds.GLOBAL_BOND_V04_FIELDS),
            set(row) - set(inputs[0]),
        )
        self.assertEqual(
            bonds.GLOBAL_BOND_V04_PARAM_VERSION,
            row["global_bond_v04_param_version"],
        )
        self.assertEqual(
            bonds.ASSET_ACCOUNTING_CONTRACT_VERSION,
            row["asset_accounting_contract_version"],
        )
        for field in (
            "global_sovereign_bond_total_return_index",
            "global_corporate_bond_total_return_index",
            "global_60_40_total_return_index",
        ):
            self.assertEqual(100.0, row[field])
        for field in bonds.GLOBAL_BOND_V04_FIELDS:
            if field.endswith("_return_pct") or field.endswith("_loss_pct"):
                self.assertEqual(0.0, row[field])
        for field in bonds.IDENTITY_RESIDUAL_FIELDS:
            self.assertEqual(0.0, row[field])

    def test_sovereign_falling_yield_hand_calculation_and_identity(self) -> None:
        rows = bonds.simulate_global_bond_v04_for_macro_path(
            path(
                macro_row(0, global_10y_yield_pct=4.0),
                macro_row(1, global_10y_yield_pct=3.0),
            )
        )
        row = rows[1]
        dy = -0.01
        expected_price = 100.0 * (-7.0 * dy + 0.5 * 50.0 * dy**2)
        self.assertAlmostEqual(expected_price, row["global_sovereign_bond_price_return_pct"])
        self.assertEqual(4.0, row["global_sovereign_bond_carry_pct"])
        self.assertAlmostEqual(
            expected_price + 4.0,
            row["global_sovereign_bond_total_return_pct"],
        )
        self.assertAlmostEqual(
            0.0,
            row["global_sovereign_bond_total_return_identity_residual"],
            places=12,
        )

    def test_convexity_has_positive_direction_and_decimal_units(self) -> None:
        no_convexity = replace(bonds.GlobalBondV04Params(), sovereign_convexity=1e-12)
        standard = bonds.GlobalBondV04Params()
        inputs = path(
            macro_row(0, global_10y_yield_pct=4.0),
            macro_row(1, global_10y_yield_pct=3.0),
        )
        near_linear = bonds.simulate_global_bond_v04_for_macro_path(inputs, no_convexity)[1]
        curved = bonds.simulate_global_bond_v04_for_macro_path(inputs, standard)[1]
        self.assertAlmostEqual(
            7.0,
            near_linear["global_sovereign_bond_price_return_pct"],
            places=10,
        )
        self.assertAlmostEqual(
            7.25,
            curved["global_sovereign_bond_price_return_pct"],
        )
        self.assertGreater(
            curved["global_sovereign_bond_price_return_pct"],
            near_linear["global_sovereign_bond_price_return_pct"],
        )

    def test_rising_yield_can_produce_negative_sovereign_total_return(self) -> None:
        falling = bonds.simulate_global_bond_v04_for_macro_path(
            path(
                macro_row(0, global_10y_yield_pct=4.0),
                macro_row(1, global_10y_yield_pct=3.0),
            )
        )[1]
        rising = bonds.simulate_global_bond_v04_for_macro_path(
            path(
                macro_row(0, global_10y_yield_pct=3.0),
                macro_row(1, global_10y_yield_pct=5.0),
            )
        )[1]
        self.assertGreater(falling["global_sovereign_bond_price_return_pct"], 0.0)
        self.assertLess(rising["global_sovereign_bond_price_return_pct"], 0.0)
        self.assertLess(rising["global_sovereign_bond_total_return_pct"], 0.0)

    def test_corporate_components_carry_credit_loss_and_identity(self) -> None:
        rows = bonds.simulate_global_bond_v04_for_macro_path(
            path(
                macro_row(
                    0,
                    global_10y_yield_pct=4.0,
                    global_investment_grade_spread_bps=100.0,
                ),
                macro_row(
                    1,
                    global_10y_yield_pct=3.0,
                    global_investment_grade_spread_bps=150.0,
                    default_risk_index=55.0,
                    credit_impairment_stock_index=10.0,
                    crisis_intensity=0.5,
                ),
            )
        )
        row = rows[1]
        expected_rf = 100.0 * (-5.0 * -0.01 + 0.5 * 28.0 * 0.01**2)
        expected_spread = -4.2 * (50.0 / 10_000.0) * 100.0
        expected_probability = 0.05 + 0.008 * 25.0 + 0.012 * 10.0 + 0.40 * 0.5
        expected_loss = expected_probability * 0.60
        self.assertAlmostEqual(
            expected_rf,
            row["global_corporate_bond_risk_free_price_return_pct"],
        )
        self.assertAlmostEqual(
            expected_spread,
            row["global_corporate_bond_ig_spread_price_return_pct"],
        )
        self.assertAlmostEqual(
            expected_rf + expected_spread,
            row["global_corporate_bond_price_return_pct"],
        )
        self.assertEqual(5.0, row["global_corporate_bond_carry_pct"])
        self.assertAlmostEqual(
            expected_probability,
            row["global_corporate_bond_default_probability_proxy_raw_pct"],
        )
        self.assertAlmostEqual(
            expected_loss,
            row["global_corporate_bond_credit_loss_pct"],
        )
        self.assertAlmostEqual(
            expected_rf + expected_spread + 5.0 - expected_loss,
            row["global_corporate_bond_total_return_pct"],
        )
        self.assertAlmostEqual(
            0.0,
            row["global_corporate_bond_total_return_identity_residual"],
            places=12,
        )

    def test_default_probability_contributions_reconstruct_raw_final_and_loss(self) -> None:
        params = replace(
            bonds.GlobalBondV04Params(),
            max_default_probability_pct=0.5,
        )
        row = bonds.simulate_global_bond_v04_for_macro_path(
            path(
                macro_row(0),
                macro_row(
                    1,
                    default_risk_index=100.0,
                    credit_impairment_stock_index=100.0,
                    crisis_intensity=1.0,
                ),
            ),
            params,
        )[1]
        raw = sum(
            float(row[field])
            for field in bonds.DEFAULT_PROBABILITY_CONTRIBUTION_FIELDS
        )
        final = raw + float(
            row[
                "global_corporate_bond_default_probability_boundary_adjustment_pct"
            ]
        )
        self.assertAlmostEqual(
            raw,
            row["global_corporate_bond_default_probability_proxy_raw_pct"],
        )
        self.assertAlmostEqual(
            final,
            row["global_corporate_bond_default_probability_proxy_pct"],
        )
        self.assertEqual(
            "cap",
            row["global_corporate_bond_default_probability_boundary_state"],
        )
        self.assertAlmostEqual(
            final * params.loss_given_default_fraction,
            row["global_corporate_bond_credit_loss_pct"],
        )

    def test_spread_widening_and_higher_default_loss_reduce_corporate_return(self) -> None:
        base = bonds.simulate_global_bond_v04_for_macro_path(
            path(macro_row(0), macro_row(1))
        )[1]
        wider = bonds.simulate_global_bond_v04_for_macro_path(
            path(
                macro_row(0),
                macro_row(1, global_investment_grade_spread_bps=200.0),
            )
        )[1]
        impaired = bonds.simulate_global_bond_v04_for_macro_path(
            path(
                macro_row(0),
                macro_row(
                    1,
                    default_risk_index=80.0,
                    credit_impairment_stock_index=30.0,
                    crisis_intensity=0.8,
                ),
            )
        )[1]
        self.assertLess(
            wider["global_corporate_bond_price_return_pct"],
            base["global_corporate_bond_price_return_pct"],
        )
        self.assertLess(
            wider["global_corporate_bond_total_return_pct"],
            base["global_corporate_bond_total_return_pct"],
        )
        self.assertEqual(
            impaired["global_corporate_bond_price_return_pct"],
            base["global_corporate_bond_price_return_pct"],
        )
        self.assertLess(
            impaired["global_corporate_bond_total_return_pct"],
            base["global_corporate_bond_total_return_pct"],
        )

    def test_sovereign_does_not_consume_corporate_credit_loss(self) -> None:
        calm = bonds.simulate_global_bond_v04_for_macro_path(
            path(macro_row(0), macro_row(1))
        )[1]
        stressed = bonds.simulate_global_bond_v04_for_macro_path(
            path(
                macro_row(0),
                macro_row(
                    1,
                    default_risk_index=100.0,
                    credit_impairment_stock_index=100.0,
                    crisis_intensity=1.0,
                ),
            )
        )[1]
        self.assertEqual(
            calm["global_sovereign_bond_total_return_pct"],
            stressed["global_sovereign_bond_total_return_pct"],
        )
        self.assertGreater(
            stressed["global_corporate_bond_credit_loss_pct"],
            calm["global_corporate_bond_credit_loss_pct"],
        )

    def test_60_40_is_exact_annual_rebalancing(self) -> None:
        row = bonds.simulate_global_bond_v04_for_macro_path(
            path(
                macro_row(0, global_10y_yield_pct=5.0),
                macro_row(
                    1,
                    global_10y_yield_pct=5.0,
                    global_equity_total_return_pct=-20.0,
                ),
            )
        )[1]
        self.assertEqual(5.0, row["global_sovereign_bond_total_return_pct"])
        self.assertAlmostEqual(-10.0, row["global_60_40_total_return_pct"])
        self.assertAlmostEqual(90.0, row["global_60_40_total_return_index"])
        self.assertAlmostEqual(
            0.0,
            row["global_60_40_total_return_identity_residual"],
            places=12,
        )

    def test_all_three_indices_reconstruct_from_published_annual_returns(self) -> None:
        inputs = [
            macro_row(0, global_10y_yield_pct=4.0),
            macro_row(1, global_10y_yield_pct=3.5, global_equity_total_return_pct=12.0),
            macro_row(
                2,
                global_10y_yield_pct=4.2,
                global_investment_grade_spread_bps=130.0,
                global_equity_total_return_pct=-8.0,
            ),
            macro_row(
                3,
                global_10y_yield_pct=3.8,
                global_investment_grade_spread_bps=90.0,
                global_equity_total_return_pct=6.0,
            ),
        ]
        rows = bonds.simulate_global_bond_v04_for_macro_path(inputs)
        cases = (
            (
                "global_sovereign_bond_total_return_pct",
                "global_sovereign_bond_total_return_index",
            ),
            (
                "global_corporate_bond_total_return_pct",
                "global_corporate_bond_total_return_index",
            ),
            ("global_60_40_total_return_pct", "global_60_40_total_return_index"),
        )
        for return_field, index_field in cases:
            expected = 100.0
            for row in rows[1:]:
                expected *= 1.0 + float(row[return_field]) / 100.0
                self.assertAlmostEqual(expected, float(row[index_field]), places=12)

    def test_no_soft_resistance_after_old_thresholds(self) -> None:
        inputs = [macro_row(0, global_10y_yield_pct=20.0)]
        for year_index in range(1, 31):
            inputs.append(
                macro_row(
                    year_index,
                    global_10y_yield_pct=20.0,
                    global_investment_grade_spread_bps=100.0,
                    global_equity_total_return_pct=20.0,
                )
            )
        rows = bonds.simulate_global_bond_v04_for_macro_path(inputs)
        self.assertGreater(rows[-1]["global_sovereign_bond_total_return_index"], 240.0)
        self.assertGreater(rows[-1]["global_corporate_bond_total_return_index"], 360.0)
        self.assertGreater(rows[-1]["global_60_40_total_return_index"], 360.0)
        previous = rows[-2]
        current = rows[-1]
        for return_field, index_field in (
            (
                "global_sovereign_bond_total_return_pct",
                "global_sovereign_bond_total_return_index",
            ),
            (
                "global_corporate_bond_total_return_pct",
                "global_corporate_bond_total_return_index",
            ),
            ("global_60_40_total_return_pct", "global_60_40_total_return_index"),
        ):
            self.assertAlmostEqual(
                float(previous[index_field])
                * (1.0 + float(current[return_field]) / 100.0),
                float(current[index_field]),
                places=12,
            )

    def test_input_rows_are_not_mutated(self) -> None:
        inputs = path(macro_row(0), macro_row(1))
        original = copy.deepcopy(inputs)
        result = bonds.simulate_global_bond_v04_for_macro_path(inputs)
        self.assertEqual(original, inputs)
        self.assertIsNot(result[0], inputs[0])
        self.assertIsNot(result[1], inputs[1])

    def test_repeated_calls_and_short_long_paths_have_exact_prefix(self) -> None:
        long_input = [
            macro_row(
                year,
                global_10y_yield_pct=4.0 + 0.1 * ((year % 3) - 1),
                global_investment_grade_spread_bps=100.0 + 5.0 * (year % 4),
                global_equity_total_return_pct=6.0 + float(year % 2),
            )
            for year in range(21)
        ]
        short = bonds.simulate_global_bond_v04_for_macro_path(long_input[:8])
        long = bonds.simulate_global_bond_v04_for_macro_path(long_input)
        repeat = bonds.simulate_global_bond_v04_for_macro_path(long_input[:8])
        self.assertEqual(short, repeat)
        self.assertEqual(short, long[: len(short)])

    def test_parameter_validation_rejects_illegal_values(self) -> None:
        invalid = (
            (replace(bonds.GlobalBondV04Params(), sovereign_duration_years=0.0), "duration"),
            (replace(bonds.GlobalBondV04Params(), sovereign_convexity=0.0), "convexity"),
            (
                replace(
                    bonds.GlobalBondV04Params(),
                    corporate_risk_free_convexity=float("nan"),
                ),
                "convexity",
            ),
            (
                replace(bonds.GlobalBondV04Params(), loss_given_default_fraction=1.1),
                "loss_given_default_fraction",
            ),
            (
                replace(
                    bonds.GlobalBondV04Params(),
                    min_default_probability_pct=5.0,
                    max_default_probability_pct=5.0,
                ),
                "min_default_probability_pct",
            ),
            (
                replace(
                    bonds.GlobalBondV04Params(),
                    max_default_probability_pct=101.0,
                ),
                "max_default_probability_pct",
            ),
        )
        for params, message in invalid:
            with self.subTest(message=message):
                with self.assertRaisesRegex(ValueError, message):
                    bonds.simulate_global_bond_v04_for_macro_path(
                        path(macro_row(0)), params
                    )

    def test_required_inputs_and_non_finite_values_are_rejected(self) -> None:
        missing_yield = macro_row(0)
        del missing_yield["global_10y_yield_pct"]
        with self.assertRaisesRegex(ValueError, "global_10y_yield_pct is required"):
            bonds.simulate_global_bond_v04_for_macro_path([missing_yield])
        with self.assertRaisesRegex(ValueError, "must be finite"):
            bonds.simulate_global_bond_v04_for_macro_path(
                path(macro_row(0), macro_row(1, global_10y_yield_pct=float("nan")))
            )
        with self.assertRaisesRegex(ValueError, "non-negative"):
            bonds.simulate_global_bond_v04_for_macro_path(
                path(
                    macro_row(0),
                    macro_row(1, global_investment_grade_spread_bps=-1.0),
                )
            )
        with self.assertRaisesRegex(ValueError, "greater than -100"):
            bonds.simulate_global_bond_v04_for_macro_path(
                path(
                    macro_row(0),
                    macro_row(1, global_equity_total_return_pct=-100.0),
                )
            )

    def test_candidate_fields_are_finite_and_publish_no_legacy_aliases(self) -> None:
        rows = bonds.simulate_global_bond_v04_for_macro_path(
            path(macro_row(0), macro_row(1))
        )
        self.assertTrue(
            set(bonds.accounting.LEGACY_FIELD_REPLACEMENTS).isdisjoint(
                bonds.GLOBAL_BOND_V04_FIELDS
            )
        )
        for row in rows:
            for field in bonds.GLOBAL_BOND_V04_FIELDS:
                value = row[field]
                if isinstance(value, (int, float)):
                    self.assertTrue(math.isfinite(float(value)), field)


if __name__ == "__main__":
    unittest.main()
