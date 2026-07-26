from __future__ import annotations

import copy
import inspect
import math
import random
import unittest
from dataclasses import replace

from macro_layers import asset_accounting_v04 as accounting
from macro_layers import regional_asset_accounting_v04 as regional_asset
from macro_layers.regional_macro_layer_sim import REGION_CONFIGS


def regional_row(region_id: str, year_index: int, **overrides: float | int | str) -> dict[str, float | int | str]:
    config = REGION_CONFIGS[region_id]
    row: dict[str, float | int | str] = {
        "year_index": year_index,
        "year": 2026 + year_index,
        "seed": 424242,
        "region_id": region_id,
        "regional_global_weight": config.global_weight,
        "regional_gdp_growth_pct": 2.5,
        "regional_headline_inflation_pct": 2.0,
        "regional_potential_growth_pct": config.trend_growth_pct,
        "regional_output_gap_pct": 0.0,
        "regional_real_10y_yield_pct": 1.5,
        "regional_10y_yield_pct": 3.0,
        "regional_hy_spread_bps": 350.0,
        "regional_financial_conditions_index": 0.0,
        "regional_credit_stress_index": 35.0,
        "regional_default_risk_index": 25.0,
        "regional_terms_of_trade_index": 50.0,
        "regional_energy_cost_pressure_index": 50.0,
        "regional_currency_yoy_pct": 0.0,
        "regional_geopolitical_risk_index": 20.0,
        "regional_policy_uncertainty_index": 20.0,
        "regional_risk_appetite_index": 50.0,
        "regional_macro_stress_index": 30.0,
        "regional_liquidity_index": 55.0,
        # Legacy fields are deliberately present to prove A2 ignores them.
        "regional_equity_index": 100.0 + 999.0 * year_index,
        "regional_equity_return_pct": -77.0 + year_index,
        "regional_bond_index": 100.0 + 555.0 * year_index,
        "regional_bond_return_pct": 66.0 - year_index,
    }
    row.update(overrides)
    return row


def global_row(year_index: int, **overrides: float | int) -> dict[str, float | int]:
    eps_index = 100.0 * (1.04**year_index)
    row: dict[str, float | int] = {
        "year_index": year_index,
        "realized_growth_pct": 2.0,
        "output_gap_pct": 0.0,
        "headline_inflation_pct": 2.0,
        "global_real_10y_yield_pct": 1.5,
        "global_high_yield_spread_bps": 350.0,
        "global_liquidity_index": 55.0,
        "risk_appetite_index": 50.0,
        "financial_stress_index": 30.0,
        "oil_yoy_change_pct": 0.0,
        "global_equity_eps_growth_pct": 4.0,
        "global_equity_eps_cycle_contribution_pp": 0.0,
        "global_equity_eps_margin_contribution_pp": 0.0,
        "global_equity_eps_credit_contribution_pp": 0.0,
        "global_equity_eps_dollar_contribution_pp": 0.0,
        "global_equity_eps_capital_destruction_contribution_pp": 0.0,
        "global_equity_eps_index": eps_index,
        "global_equity_valuation_pe": 18.0,
        "global_equity_price_return_pct": 4.0 if year_index else 0.0,
        "global_equity_total_return_pct": 6.5 if year_index else 0.0,
        "global_sovereign_bond_total_return_pct": 3.0 if year_index else 0.0,
    }
    row.update(overrides)
    return row


def regional_path(region_id: str, years: int, **overrides: float | int | str) -> list[dict[str, float | int | str]]:
    return [regional_row(region_id, year, **overrides) for year in range(years + 1)]


def global_path(years: int, **overrides: float | int) -> list[dict[str, float | int]]:
    return [global_row(year, **overrides) for year in range(years + 1)]


def simulate(
    region_id: str = "north_america",
    years: int = 5,
    *,
    regional_overrides: dict[str, float | int | str] | None = None,
    global_overrides: dict[str, float | int] | None = None,
    config_override=None,
    template=None,
    params=None,
):
    return regional_asset.simulate_regional_asset_v04_for_macro_path(
        regional_path(region_id, years, **(regional_overrides or {})),
        global_path(years, **(global_overrides or {})),
        region_config=config_override or REGION_CONFIGS[region_id],
        template=template,
        params=params,
    )


class RegionalAssetV04AccountingTests(unittest.TestCase):
    def test_initial_row_has_complete_a0_core_contract_and_zero_flows(self) -> None:
        inputs = regional_path("north_america", 1)
        output = regional_asset.simulate_regional_asset_v04_for_macro_path(
            inputs,
            global_path(1),
            region_config=REGION_CONFIGS["north_america"],
        )
        row = output[0]
        self.assertLessEqual(set(regional_asset.REGIONAL_ASSET_V04_FIELDS), set(row))
        self.assertEqual(100.0, row["regional_equity_eps_index"])
        self.assertEqual(18.0, row["regional_equity_valuation_pe_raw"])
        self.assertEqual(18.0, row["regional_equity_valuation_pe"])
        self.assertEqual(100.0, row["regional_equity_price_index"])
        self.assertEqual(100.0, row["regional_equity_total_return_index"])
        self.assertEqual(100.0, row["regional_sovereign_bond_total_return_index"])
        for field in (
            "regional_equity_eps_growth_raw_pct",
            "regional_equity_eps_growth_pct",
            "regional_equity_price_return_pct",
            "regional_equity_dividend_yield_pct",
            "regional_equity_total_return_pct",
            "regional_sovereign_bond_price_return_pct",
            "regional_sovereign_bond_carry_pct",
            "regional_sovereign_bond_total_return_pct",
        ):
            self.assertEqual(0.0, row[field], field)
        specs = {
            spec.name: spec
            for spec in accounting.ASSET_FIELD_SPECS
            if spec.scope == "regional_asset"
        }
        self.assertEqual(set(specs), set(regional_asset.REGIONAL_ASSET_V04_CORE_FIELDS))
        self.assertTrue(all(spec.stage == "A2" for spec in specs.values()))

    def test_equity_and_bond_identities_reconstruct_exactly(self) -> None:
        params = replace(
            regional_asset.RegionalAssetV04Params(),
            eps_smoothing=1.0,
            pe_smoothing=1.0,
            payout_smoothing=1.0,
        )
        rows = simulate("china_mainland", 12, params=params)
        for previous, current in zip(rows, rows[1:]):
            expected_price = (
                current["regional_equity_eps_index"]
                * current["regional_equity_valuation_pe"]
                / params.initial_pe
            )
            expected_price_return = (
                expected_price / previous["regional_equity_price_index"] - 1.0
            ) * 100.0
            expected_total_return = (
                expected_price_return
                + current["regional_equity_dividend_yield_pct"]
            )
            expected_total_index = previous["regional_equity_total_return_index"] * (
                1.0 + expected_total_return / 100.0
            )
            expected_bond_index = previous[
                "regional_sovereign_bond_total_return_index"
            ] * (1.0 + current["regional_sovereign_bond_total_return_pct"] / 100.0)
            self.assertAlmostEqual(expected_price, current["regional_equity_price_index"], places=12)
            self.assertAlmostEqual(expected_price_return, current["regional_equity_price_return_pct"], places=12)
            self.assertAlmostEqual(expected_total_return, current["regional_equity_total_return_pct"], places=12)
            self.assertAlmostEqual(expected_total_index, current["regional_equity_total_return_index"], places=12)
            self.assertAlmostEqual(expected_bond_index, current["regional_sovereign_bond_total_return_index"], places=12)
            for residual in (
                "regional_equity_price_identity_residual",
                "regional_equity_price_return_identity_residual",
                "regional_equity_total_return_identity_residual",
                "regional_sovereign_bond_price_return_identity_residual",
                "regional_sovereign_bond_total_return_identity_residual",
            ):
                self.assertAlmostEqual(0.0, current[residual], places=12, msg=residual)

    def test_eps_and_pe_contributions_reconstruct_raw_and_final_values(self) -> None:
        row = simulate("southeast_asia", 1)[1]
        eps_raw = sum(row[field] for field in regional_asset.REGIONAL_EPS_CONTRIBUTION_FIELDS)
        eps_final = (
            eps_raw
            + row["regional_equity_eps_smoothing_adjustment_pp"]
            + row["regional_equity_eps_boundary_adjustment_pp"]
        )
        pe_raw = sum(row[field] for field in regional_asset.REGIONAL_PE_CONTRIBUTION_FIELDS)
        pe_final = (
            pe_raw
            + row["regional_equity_pe_smoothing_adjustment"]
            + row["regional_equity_pe_boundary_adjustment"]
        )
        self.assertAlmostEqual(eps_raw, row["regional_equity_eps_growth_raw_pct"], places=12)
        self.assertAlmostEqual(eps_final, row["regional_equity_eps_growth_pct"], places=12)
        self.assertAlmostEqual(pe_raw, row["regional_equity_valuation_pe_raw"], places=12)
        self.assertAlmostEqual(pe_final, row["regional_equity_valuation_pe"], places=12)
        for residual in (
            "regional_equity_eps_growth_raw_identity_residual",
            "regional_equity_eps_growth_final_identity_residual",
            "regional_equity_pe_raw_identity_residual",
            "regional_equity_pe_final_identity_residual",
        ):
            self.assertAlmostEqual(0.0, row[residual], places=12, msg=residual)

    def test_price_return_decomposition_handles_eps_pe_and_interaction(self) -> None:
        row = simulate(
            "north_america",
            1,
            regional_overrides={"regional_headline_inflation_pct": 5.0, "regional_real_10y_yield_pct": 4.0},
            params=replace(regional_asset.RegionalAssetV04Params(), eps_smoothing=1.0, pe_smoothing=1.0),
        )[1]
        reconstructed = (
            row["regional_equity_eps_price_return_contribution_pct"]
            + row["regional_equity_pe_price_return_contribution_pct"]
            + row["regional_equity_eps_pe_interaction_price_return_contribution_pct"]
        )
        self.assertAlmostEqual(row["regional_equity_price_return_pct"], reconstructed, places=12)

    def test_eps_rises_and_price_rises_when_inflation_changes_but_pe_drivers_do_not(self) -> None:
        params = replace(regional_asset.RegionalAssetV04Params(), eps_smoothing=1.0, pe_smoothing=1.0)
        low = simulate(
            "north_america",
            1,
            regional_overrides={"regional_headline_inflation_pct": 0.5},
            params=params,
        )[1]
        high = simulate(
            "north_america",
            1,
            regional_overrides={"regional_headline_inflation_pct": 5.0},
            params=params,
        )[1]
        self.assertEqual(low["regional_equity_valuation_pe"], high["regional_equity_valuation_pe"])
        self.assertGreater(high["regional_equity_eps_index"], low["regional_equity_eps_index"])
        self.assertGreater(high["regional_equity_price_index"], low["regional_equity_price_index"])

    def test_eps_can_rise_while_strong_pe_compression_lowers_price(self) -> None:
        params = replace(regional_asset.RegionalAssetV04Params(), eps_smoothing=1.0, pe_smoothing=1.0)
        row = simulate(
            "north_america",
            1,
            regional_overrides={
                "regional_gdp_growth_pct": 5.0,
                "regional_headline_inflation_pct": 5.0,
                "regional_real_10y_yield_pct": 8.0,
                "regional_hy_spread_bps": 1000.0,
                "regional_macro_stress_index": 45.0,
            },
            params=params,
        )[1]
        self.assertGreater(row["regional_equity_eps_index"], 100.0)
        self.assertLess(row["regional_equity_valuation_pe"], 18.0)
        self.assertLess(row["regional_equity_price_index"], 100.0)
        self.assertGreater(row["regional_equity_eps_price_return_contribution_pct"], 0.0)
        self.assertLess(row["regional_equity_pe_price_return_contribution_pct"], 0.0)

    def test_bond_duration_carry_and_total_return_hand_calculation(self) -> None:
        rows = [
            regional_row("north_america", 0, regional_10y_yield_pct=3.0),
            regional_row("north_america", 1, regional_10y_yield_pct=4.0),
        ]
        output = regional_asset.simulate_regional_asset_v04_for_macro_path(
            rows,
            global_path(1),
            region_config=REGION_CONFIGS["north_america"],
        )
        row = output[1]
        duration = regional_asset.REGIONAL_ASSET_TEMPLATES[
            regional_asset.REGION_TEMPLATE_BY_REGION["north_america"]
        ].bond_duration_years
        self.assertAlmostEqual(-duration, row["regional_sovereign_bond_price_return_pct"])
        self.assertAlmostEqual(3.0, row["regional_sovereign_bond_carry_pct"])
        self.assertAlmostEqual(3.0 - duration, row["regional_sovereign_bond_total_return_pct"])
        self.assertLess(row["regional_sovereign_bond_total_return_pct"], 0.0)

    def test_bond_uses_only_local_yield_and_not_global_bond_return_or_fx(self) -> None:
        base = simulate("north_america", 2)
        changed = simulate(
            "north_america",
            2,
            regional_overrides={"regional_currency_yoy_pct": 25.0},
            global_overrides={"global_sovereign_bond_total_return_pct": -40.0},
        )
        for left, right in zip(base, changed):
            self.assertEqual(
                left["regional_sovereign_bond_total_return_pct"],
                right["regional_sovereign_bond_total_return_pct"],
            )
            self.assertEqual(
                left["regional_sovereign_bond_total_return_index"],
                right["regional_sovereign_bond_total_return_index"],
            )
        self.assertFalse(any("credit_loss" in field for field in regional_asset.REGIONAL_ASSET_V04_FIELDS))

    def test_template_mapping_covers_exactly_the_14_region_configs(self) -> None:
        self.assertEqual(set(REGION_CONFIGS), set(regional_asset.REGION_TEMPLATE_BY_REGION))
        self.assertEqual(14, len(regional_asset.REGION_TEMPLATE_BY_REGION))
        self.assertLess(len(regional_asset.REGIONAL_ASSET_TEMPLATES), 14)
        self.assertLessEqual(
            set(regional_asset.REGION_TEMPLATE_BY_REGION.values()),
            set(regional_asset.REGIONAL_ASSET_TEMPLATES),
        )
        for template in regional_asset.REGIONAL_ASSET_TEMPLATES.values():
            regional_asset.validate_template(template)

    def test_common_formula_functions_do_not_branch_on_region_names(self) -> None:
        source = "\n".join(
            inspect.getsource(function)
            for function in (
                regional_asset._eps_contributions,
                regional_asset._pe_contributions,
                regional_asset._payout_target,
            )
        )
        for region_id in REGION_CONFIGS:
            self.assertNotIn(region_id, source)

    def test_global_common_shock_is_beta_scaled_and_beta_zero_keeps_local_channels(self) -> None:
        config = replace(REGION_CONFIGS["north_america"], asset_global_beta=0.0)
        calm = simulate("north_america", 1, config_override=config)
        stressed = simulate(
            "north_america",
            1,
            config_override=config,
            global_overrides={
                "global_equity_valuation_pe": 10.0,
                "global_equity_eps_cycle_contribution_pp": -8.0,
                "global_equity_eps_margin_contribution_pp": -4.0,
                "global_equity_eps_credit_contribution_pp": -3.0,
            },
        )
        for field in (
            "regional_equity_eps_growth_pct",
            "regional_equity_valuation_pe",
            "regional_equity_price_index",
        ):
            self.assertEqual(calm[1][field], stressed[1][field], field)
        weak_local = simulate(
            "north_america",
            1,
            config_override=config,
            regional_overrides={"regional_gdp_growth_pct": -2.0},
        )[1]
        strong_local = simulate(
            "north_america",
            1,
            config_override=config,
            regional_overrides={"regional_gdp_growth_pct": 5.0},
        )[1]
        self.assertGreater(strong_local["regional_equity_eps_index"], weak_local["regional_equity_eps_index"])
        self.assertNotEqual(strong_local["regional_equity_valuation_pe"], weak_local["regional_equity_valuation_pe"])

    def test_global_pe_compression_moves_all_regions_in_common_direction(self) -> None:
        for region_id in REGION_CONFIGS:
            baseline = simulate(region_id, 1)[1]
            compressed = simulate(
                region_id,
                1,
                global_overrides={"global_equity_valuation_pe": 12.0},
            )[1]
            with self.subTest(region=region_id):
                self.assertLess(
                    compressed["regional_equity_pe_global_common_contribution"],
                    baseline["regional_equity_pe_global_common_contribution"],
                )
                self.assertLess(
                    compressed["regional_equity_valuation_pe"],
                    baseline["regional_equity_valuation_pe"],
                )

    def test_local_pe_uses_differentials_without_double_counting_common_stress(self) -> None:
        settings = replace(regional_asset.RegionalAssetV04Params(), pe_smoothing=1.0)
        global_stress = {
            "global_equity_valuation_pe": 8.5,
            "output_gap_pct": -8.0,
            "global_real_10y_yield_pct": 5.0,
            "global_high_yield_spread_bps": 1_000.0,
            "risk_appetite_index": 5.0,
            "global_liquidity_index": 20.0,
            "financial_stress_index": 90.0,
        }
        matched_regional_stress = {
            "regional_gdp_growth_pct": 2.0,
            "regional_output_gap_pct": -8.0,
            "regional_real_10y_yield_pct": 5.0,
            "regional_hy_spread_bps": 1_000.0,
            "regional_risk_appetite_index": 5.0,
            "regional_liquidity_index": 20.0,
            "regional_macro_stress_index": 90.0,
        }
        differential_fields = (
            "regional_equity_pe_real_rate_contribution",
            "regional_equity_pe_credit_contribution",
            "regional_equity_pe_cycle_contribution",
            "regional_equity_pe_event_contribution",
        )
        for region_id in REGION_CONFIGS:
            row = simulate(
                region_id,
                1,
                regional_overrides=matched_regional_stress,
                global_overrides=global_stress,
                params=settings,
            )[1]
            with self.subTest(region=region_id):
                for field in differential_fields:
                    self.assertAlmostEqual(0.0, row[field], places=12, msg=field)
                self.assertEqual("none", row["regional_equity_pe_boundary_state"])
                self.assertGreater(row["regional_equity_valuation_pe"], settings.min_pe)

    def test_oil_shock_benefits_exporter_and_hurts_energy_importer(self) -> None:
        exporter = simulate(
            "middle_east_gulf",
            1,
            global_overrides={"oil_yoy_change_pct": 30.0},
        )[1]
        importer = simulate(
            "japan_korea",
            1,
            global_overrides={"oil_yoy_change_pct": 30.0},
        )[1]
        exporter_net = (
            exporter["regional_equity_eps_commodity_producer_contribution_pp"]
            + exporter["regional_equity_eps_energy_import_contribution_pp"]
        )
        importer_net = (
            importer["regional_equity_eps_commodity_producer_contribution_pp"]
            + importer["regional_equity_eps_energy_import_contribution_pp"]
        )
        self.assertGreater(exporter_net, 0.0)
        self.assertLess(importer_net, 0.0)
        self.assertGreater(exporter_net, importer_net)

    def test_positive_gdp_can_be_overwhelmed_by_margin_credit_and_capital_damage(self) -> None:
        calm = simulate(
            "south_asia_india",
            1,
            regional_overrides={"regional_gdp_growth_pct": 4.0},
        )[1]
        stressed = simulate(
            "south_asia_india",
            1,
            regional_overrides={
                "regional_gdp_growth_pct": 4.0,
                "regional_hy_spread_bps": 1800.0,
                "regional_financial_conditions_index": 5.0,
                "regional_credit_stress_index": 90.0,
                "regional_default_risk_index": 85.0,
                "regional_energy_cost_pressure_index": 95.0,
                "regional_macro_stress_index": 95.0,
                "regional_geopolitical_risk_index": 80.0,
                "regional_policy_uncertainty_index": 90.0,
            },
            global_overrides={"oil_yoy_change_pct": 35.0},
            params=replace(regional_asset.RegionalAssetV04Params(), eps_smoothing=1.0),
        )[1]
        self.assertGreater(calm["regional_equity_eps_growth_pct"], stressed["regional_equity_eps_growth_pct"])
        self.assertLess(stressed["regional_equity_eps_growth_pct"], 0.0)

    def test_missing_non_finite_year_alignment_length_region_and_weight_errors_fail(self) -> None:
        region = regional_path("north_america", 2)
        global_rows = global_path(2)
        config = REGION_CONFIGS["north_america"]

        missing = copy.deepcopy(region)
        del missing[1]["regional_10y_yield_pct"]
        with self.assertRaisesRegex(ValueError, "regional_10y_yield_pct"):
            regional_asset.simulate_regional_asset_v04_for_macro_path(missing, global_rows, region_config=config)

        non_finite = copy.deepcopy(global_rows)
        non_finite[1]["global_equity_valuation_pe"] = float("nan")
        with self.assertRaisesRegex(ValueError, "finite"):
            regional_asset.simulate_regional_asset_v04_for_macro_path(region, non_finite, region_config=config)

        broken_year = copy.deepcopy(region)
        broken_year[1]["year_index"] = 2
        with self.assertRaisesRegex(ValueError, "contiguous"):
            regional_asset.simulate_regional_asset_v04_for_macro_path(broken_year, global_rows, region_config=config)

        with self.assertRaisesRegex(ValueError, "length mismatch"):
            regional_asset.simulate_regional_asset_v04_for_macro_path(region, global_rows[:-1], region_config=config)

        wrong_region = copy.deepcopy(region)
        wrong_region[1]["region_id"] = "china_mainland"
        with self.assertRaisesRegex(ValueError, "region_id"):
            regional_asset.simulate_regional_asset_v04_for_macro_path(wrong_region, global_rows, region_config=config)

        wrong_weight = copy.deepcopy(region)
        wrong_weight[1]["regional_global_weight"] = 0.123
        with self.assertRaisesRegex(ValueError, "regional_global_weight"):
            regional_asset.simulate_regional_asset_v04_for_macro_path(wrong_weight, global_rows, region_config=config)

        negative_spread = copy.deepcopy(region)
        negative_spread[1]["regional_hy_spread_bps"] = -1.0
        with self.assertRaisesRegex(ValueError, "regional_hy_spread_bps"):
            regional_asset.simulate_regional_asset_v04_for_macro_path(negative_spread, global_rows, region_config=config)

        nonpositive_global_pe = copy.deepcopy(global_rows)
        nonpositive_global_pe[1]["global_equity_valuation_pe"] = 0.0
        with self.assertRaisesRegex(ValueError, "global_equity_valuation_pe"):
            regional_asset.simulate_regional_asset_v04_for_macro_path(region, nonpositive_global_pe, region_config=config)

    def test_empty_paths_and_parameter_template_errors_are_explicit(self) -> None:
        self.assertEqual(
            [],
            regional_asset.simulate_regional_asset_v04_for_macro_path(
                [], [], region_config=REGION_CONFIGS["north_america"]
            ),
        )
        with self.assertRaisesRegex(ValueError, "length mismatch"):
            regional_asset.simulate_regional_asset_v04_for_macro_path(
                [], global_path(1), region_config=REGION_CONFIGS["north_america"]
            )
        with self.assertRaisesRegex(ValueError, "eps_smoothing"):
            simulate(
                "north_america",
                1,
                params=replace(regional_asset.RegionalAssetV04Params(), eps_smoothing=0.0),
            )
        with self.assertRaisesRegex(ValueError, "unknown regional asset template"):
            simulate("north_america", 1, template="not_a_template")
        with self.assertRaisesRegex(ValueError, "dilution_drag_pct"):
            simulate(
                "north_america",
                1,
                template=replace(
                    regional_asset.REGIONAL_ASSET_TEMPLATES["developed_diversified"],
                    dilution_drag_pct=-0.1,
                ),
            )
        with self.assertRaisesRegex(ValueError, "market_maturity"):
            simulate(
                "north_america",
                1,
                config_override=replace(
                    REGION_CONFIGS["north_america"],
                    market_maturity=1.1,
                ),
            )
        with self.assertRaisesRegex(ValueError, "global_weight"):
            simulate(
                "north_america",
                1,
                config_override=replace(
                    REGION_CONFIGS["north_america"],
                    global_weight=1.1,
                ),
            )

    def test_inputs_are_not_mutated_repeats_match_and_short_path_is_exact_prefix(self) -> None:
        region_short = regional_path("oceania", 12)
        global_short = global_path(12)
        region_snapshot = copy.deepcopy(region_short)
        global_snapshot = copy.deepcopy(global_short)
        first = regional_asset.simulate_regional_asset_v04_for_macro_path(
            region_short,
            global_short,
            region_config=REGION_CONFIGS["oceania"],
        )
        repeat = regional_asset.simulate_regional_asset_v04_for_macro_path(
            region_short,
            global_short,
            region_config=REGION_CONFIGS["oceania"],
        )
        long = regional_asset.simulate_regional_asset_v04_for_macro_path(
            regional_path("oceania", 60),
            global_path(60),
            region_config=REGION_CONFIGS["oceania"],
        )
        self.assertEqual(region_snapshot, region_short)
        self.assertEqual(global_snapshot, global_short)
        self.assertEqual(first, repeat)
        self.assertEqual(first, long[: len(first)])

    def test_region_call_order_does_not_change_any_output(self) -> None:
        forward = {
            region_id: simulate(region_id, 4)
            for region_id in REGION_CONFIGS
        }
        reverse = {
            region_id: simulate(region_id, 4)
            for region_id in reversed(tuple(REGION_CONFIGS))
        }
        self.assertEqual(forward, reverse)

    def test_candidate_does_not_consume_process_random_state_or_use_python_hash(self) -> None:
        random.seed(20260725)
        expected = random.Random(20260725).random()
        simulate("north_america", 5)
        self.assertEqual(expected, random.random())
        source = inspect.getsource(regional_asset)
        self.assertNotIn("import random", source)
        self.assertNotIn("hash(", source)

    def test_legacy_regional_asset_fields_do_not_affect_candidate_outputs(self) -> None:
        low_legacy = regional_path(
            "north_america",
            3,
            regional_equity_return_pct=-99.0,
            regional_bond_return_pct=-99.0,
            regional_equity_index=1.0,
            regional_bond_index=1.0,
        )
        high_legacy = regional_path(
            "north_america",
            3,
            regional_equity_return_pct=99.0,
            regional_bond_return_pct=99.0,
            regional_equity_index=99999.0,
            regional_bond_index=99999.0,
        )
        left = regional_asset.simulate_regional_asset_v04_for_macro_path(
            low_legacy, global_path(3), region_config=REGION_CONFIGS["north_america"]
        )
        right = regional_asset.simulate_regional_asset_v04_for_macro_path(
            high_legacy, global_path(3), region_config=REGION_CONFIGS["north_america"]
        )
        for left_row, right_row in zip(left, right):
            for field in regional_asset.REGIONAL_ASSET_V04_FIELDS:
                self.assertEqual(left_row[field], right_row[field], field)

    def test_all_14_regions_x_61_years_are_finite(self) -> None:
        for region_id in REGION_CONFIGS:
            rows = simulate(region_id, 60)
            self.assertEqual(61, len(rows))
            for row in rows:
                for field in regional_asset.REGIONAL_ASSET_V04_FIELDS:
                    value = row[field]
                    if isinstance(value, (int, float)) and not isinstance(value, bool):
                        self.assertTrue(math.isfinite(float(value)), f"{region_id}:{field}")

    def test_soft_reconciliation_reports_weighted_gaps_without_forcing_equality(self) -> None:
        regional_paths = {
            region_id: simulate(region_id, 3)
            for region_id in REGION_CONFIGS
        }
        diagnostics = regional_asset.regional_asset_soft_reconciliation_v04(
            regional_paths,
            global_path(3, global_sovereign_bond_total_return_pct=1.0),
        )
        self.assertEqual(4, len(diagnostics))
        for row in diagnostics:
            self.assertEqual("diagnostic_only", row["regional_asset_reconciliation_scope"])
            self.assertEqual(14, row["regional_asset_reconciliation_region_count"])
            self.assertAlmostEqual(
                sum(config.global_weight for config in REGION_CONFIGS.values()),
                row["regional_asset_reconciliation_weight_sum"],
            )
            for field in regional_asset.RECONCILIATION_NUMERIC_FIELDS:
                self.assertTrue(math.isfinite(float(row[field])), field)
        self.assertTrue(
            any(
                abs(row["regional_asset_equity_total_return_gap_pct"]) > 1e-9
                for row in diagnostics[1:]
            )
        )
        self.assertTrue(
            any(
                abs(row["regional_asset_sovereign_bond_total_return_gap_pct"]) > 1e-9
                for row in diagnostics[1:]
            )
        )

    def test_soft_reconciliation_rejects_missing_region_length_and_non_finite_inputs(self) -> None:
        regional_paths = {
            region_id: simulate(region_id, 2)
            for region_id in REGION_CONFIGS
        }
        missing = dict(regional_paths)
        missing.pop("north_america")
        with self.assertRaisesRegex(ValueError, "cover all 14 regions"):
            regional_asset.regional_asset_soft_reconciliation_v04(missing, global_path(2))

        wrong_length = dict(regional_paths)
        wrong_length["north_america"] = wrong_length["north_america"][:-1]
        with self.assertRaisesRegex(ValueError, "length mismatch"):
            regional_asset.regional_asset_soft_reconciliation_v04(wrong_length, global_path(2))

        non_finite = copy.deepcopy(regional_paths)
        non_finite["north_america"][1]["regional_equity_eps_index"] = float("inf")
        with self.assertRaisesRegex(ValueError, "finite"):
            regional_asset.regional_asset_soft_reconciliation_v04(non_finite, global_path(2))

    def test_formal_versions_activate_the_v04_contract(self) -> None:
        self.assertEqual("airport-model-v0.16", accounting.CURRENT_MODEL_VERSION)
        self.assertEqual("airport-model-output-v6", accounting.CURRENT_OUTPUT_SCHEMA_VERSION)
        self.assertEqual(
            accounting.ASSET_ACCOUNTING_CONTRACT_VERSION,
            regional_asset.REGIONAL_ASSET_V04_INTERFACE_VERSION,
        )


if __name__ == "__main__":
    unittest.main()
