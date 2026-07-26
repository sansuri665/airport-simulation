from __future__ import annotations

import json
import math
import random
import re
import unittest
from dataclasses import replace
from functools import lru_cache
from pathlib import Path

from macro_layers import asset_accounting_v04 as accounting
from macro_layers import macro_run_orchestrator_sim as orchestrator


ROOT_DIR = Path(__file__).resolve().parents[1]
PRODUCTION_ROOTS = (
    ROOT_DIR / "macro_layers",
    ROOT_DIR / "airport_sim",
    ROOT_DIR / "web",
    ROOT_DIR / "schemas",
    ROOT_DIR / "config",
)
TEXT_SUFFIXES = {".py", ".js", ".json", ".html", ".css"}
NON_PRODUCTION_EXCLUDED = {
    (ROOT_DIR / "tests" / "test_asset_v04_field_contract.py").resolve(),
    (ROOT_DIR / "tests" / "test_regional_asset_accounting_v04.py").resolve(),
    (ROOT_DIR / "docs" / "plans" / "Asset_Layer_Field_Contract.md").resolve(),
    (ROOT_DIR / "docs" / "plans" / "Asset_Layer_Working_Guide.md").resolve(),
}


@lru_cache(maxsize=None)
def contract_token_pattern(field: str) -> re.Pattern[str]:
    return re.compile(rf"(?<![A-Za-z0-9_]){re.escape(field)}(?![A-Za-z0-9_])")


def contains_contract_token(content: str, field: str) -> bool:
    return contract_token_pattern(field).search(content) is not None


def inventory_token_pattern(fields: set[str]) -> re.Pattern[str]:
    alternatives = "|".join(
        re.escape(field)
        for field in sorted(fields, key=lambda value: (-len(value), value))
    )
    return re.compile(rf"(?<![A-Za-z0-9_])({alternatives})(?![A-Za-z0-9_])")


def production_consumers(field: str) -> set[str]:
    consumers: set[str] = set()
    contract_path = (ROOT_DIR / "macro_layers" / "asset_accounting_v04.py").resolve()
    for root in PRODUCTION_ROOTS:
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            if path.resolve() == contract_path:
                continue
            if contains_contract_token(path.read_text(encoding="utf-8"), field):
                consumers.add(path.relative_to(ROOT_DIR).as_posix())
    return consumers


def production_consumer_inventory(fields: set[str]) -> dict[str, set[str]]:
    inventory = {field: set() for field in fields}
    pattern = inventory_token_pattern(fields)
    contract_path = (ROOT_DIR / "macro_layers" / "asset_accounting_v04.py").resolve()
    for root in PRODUCTION_ROOTS:
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            if path.resolve() == contract_path:
                continue
            content = path.read_text(encoding="utf-8")
            relative = path.relative_to(ROOT_DIR).as_posix()
            for match in pattern.finditer(content):
                inventory[match.group(1)].add(relative)
    return inventory


def non_production_consumer_inventory(fields: set[str]) -> dict[str, set[str]]:
    inventory = {field: set() for field in fields}
    pattern = inventory_token_pattern(fields)
    for root in (ROOT_DIR / "tests", ROOT_DIR / "docs"):
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in {".py", ".md"}:
                continue
            if path.resolve() in NON_PRODUCTION_EXCLUDED:
                continue
            content = path.read_text(encoding="utf-8")
            relative = path.relative_to(ROOT_DIR).as_posix()
            for match in pattern.finditer(content):
                inventory[match.group(1)].add(relative)
    return inventory


class AssetV04FieldDefinitionTests(unittest.TestCase):
    def test_contract_definition_is_machine_valid(self) -> None:
        accounting.validate_contract_definition()
        self.assertEqual(
            len(accounting.ASSET_FIELD_SPECS),
            len(accounting.CANONICAL_ASSET_FIELDS),
        )
        self.assertEqual(
            len(accounting.ASSET_FIELD_SPECS),
            len(set(accounting.CANONICAL_ASSET_FIELDS)),
        )

    def test_global_and_regional_price_and_total_return_are_separate(self) -> None:
        fields = set(accounting.CANONICAL_ASSET_FIELDS)
        expected = {
            "global_equity_eps_index",
            "global_equity_price_index",
            "global_equity_price_return_pct",
            "global_equity_dividend_yield_pct",
            "global_equity_total_return_pct",
            "global_equity_total_return_index",
            "regional_equity_eps_index",
            "regional_equity_price_index",
            "regional_equity_price_return_pct",
            "regional_equity_dividend_yield_pct",
            "regional_equity_total_return_pct",
            "regional_equity_total_return_index",
        }
        self.assertLessEqual(expected, fields)

    def test_market_wealth_and_cash_signals_are_distinct(self) -> None:
        fields = set(accounting.required_fields_for_scope("regional_signal"))
        self.assertEqual(
            {
                "regional_asset_market_impulse_index",
                "regional_household_financial_wealth_index",
                "regional_real_household_wealth_growth_pct",
                "regional_household_wealth_consumption_impulse",
                "regional_real_disposable_income_growth_pct",
            },
            fields,
        )

    def test_each_demand_target_has_all_five_contribution_slots(self) -> None:
        fields = set(accounting.required_fields_for_scope("regional_demand"))
        for target in ("total", "business", "leisure", "vfr", "long_haul", "transfer"):
            for contribution in (
                "asset_market",
                "household_wealth",
                "cash_income",
                "credit_confidence",
                "fare_cost",
            ):
                self.assertIn(
                    f"demand_{target}_{contribution}_contribution_pp",
                    fields,
                )

    def test_legacy_fields_have_replacements_and_exact_current_consumer_inventory(self) -> None:
        self.assertEqual(
            set(accounting.LEGACY_FIELD_REPLACEMENTS),
            set(accounting.LEGACY_CONSUMER_INVENTORY),
        )
        legacy_fields = set(accounting.LEGACY_FIELD_REPLACEMENTS)
        self.assertEqual(legacy_fields, set(accounting.LEGACY_NON_PRODUCTION_INVENTORY))
        actual_inventory = production_consumer_inventory(legacy_fields)
        actual_non_production = non_production_consumer_inventory(legacy_fields)
        for field, replacements in accounting.LEGACY_FIELD_REPLACEMENTS.items():
            with self.subTest(field=field):
                self.assertTrue(replacements)
                self.assertTrue(set(replacements).issubset(accounting.ASSET_FIELD_SPECS_BY_NAME))
                self.assertEqual(
                    set(accounting.LEGACY_CONSUMER_INVENTORY[field]),
                    actual_inventory[field],
                )
                self.assertEqual(
                    set(accounting.LEGACY_NON_PRODUCTION_INVENTORY[field]),
                    actual_non_production[field],
                )

    def test_candidate_initial_rows_are_complete_and_validate(self) -> None:
        for scope in ("global_asset", "regional_asset", "regional_signal", "regional_demand"):
            with self.subTest(scope=scope):
                row = accounting.initial_contract_row(scope)
                self.assertEqual(
                    set(accounting.required_fields_for_scope(scope)),
                    set(row),
                )
                accounting.validate_candidate_row(
                    row,
                    scope=scope,
                    year_index=0,
                    output_schema_version=accounting.CANDIDATE_OUTPUT_SCHEMA_VERSION,
                )

    def test_candidate_row_rejects_old_schema_and_legacy_aliases(self) -> None:
        row = accounting.initial_contract_row("global_asset")
        with self.assertRaisesRegex(ValueError, "require airport-model-output-v6"):
            accounting.validate_candidate_row(
                row,
                scope="global_asset",
                year_index=0,
                output_schema_version="airport-model-output-v5",
            )
        row["global_equity_index"] = 100.0
        with self.assertRaisesRegex(ValueError, "contains legacy fields"):
            accounting.validate_candidate_row(
                row,
                scope="global_asset",
                year_index=0,
                output_schema_version=accounting.CANDIDATE_OUTPUT_SCHEMA_VERSION,
            )

    def test_version_policy_forbids_compatibility_aliases(self) -> None:
        policy = accounting.ASSET_VERSION_POLICY
        self.assertEqual("airport-model-v0.16", policy.current_model_version)
        self.assertEqual("airport-model-output-v6", policy.current_output_schema_version)
        self.assertEqual("airport-model-v0.16", policy.candidate_model_version)
        self.assertEqual("airport-model-output-v6", policy.candidate_output_schema_version)
        self.assertEqual("explicit_legacy_viewer_or_reject", policy.legacy_read_policy)
        self.assertFalse(policy.compatibility_aliases_allowed)

    def test_a3_activates_candidate_versions_and_the_formal_wealth_bridge(self) -> None:
        version_record = json.loads(
            (ROOT_DIR / "config" / "airport_versions.json").read_text(encoding="utf-8")
        )
        self.assertEqual(accounting.CURRENT_MODEL_VERSION, version_record["model_version"])
        self.assertEqual(
            accounting.CURRENT_OUTPUT_SCHEMA_VERSION,
            version_record["output_schema_version"],
        )
        self.assertEqual(accounting.CURRENT_MODEL_VERSION, orchestrator.MODEL_VERSION)
        self.assertEqual(
            accounting.CURRENT_OUTPUT_SCHEMA_VERSION,
            orchestrator.OUTPUT_SCHEMA_VERSION,
        )
        production_imports = production_consumers("asset_accounting_v04")
        self.assertEqual(
            {
                "macro_layers/global_bond_accounting_v04.py",
                "macro_layers/global_equity_accounting_v04.py",
                "macro_layers/regional_asset_accounting_v04.py",
                "macro_layers/regional_wealth_bridge_v04.py",
            },
            production_imports,
        )


class AssetV04PureAccountingTests(unittest.TestCase):
    def test_eps_times_pe_reconstructs_price_without_display_cap(self) -> None:
        self.assertEqual(110.0, accounting.equity_price_index(110.0, 18.0, 18.0))
        self.assertEqual(150.0, accounting.equity_price_index(100.0, 27.0, 18.0))
        self.assertGreater(
            accounting.equity_price_index(1_000.0, 30.0, 18.0),
            1_600.0,
        )

    def test_fixed_price_with_positive_dividend_only_lifts_total_return(self) -> None:
        result = accounting.equity_return_breakdown(
            previous_price_index=100.0,
            previous_total_return_index=100.0,
            eps_index=100.0,
            valuation_pe=18.0,
            payout_ratio_pct=45.0,
        )
        self.assertEqual(100.0, result.price_index)
        self.assertEqual(0.0, result.price_return_pct)
        self.assertAlmostEqual(2.5, result.dividend_yield_pct)
        self.assertAlmostEqual(2.5, result.total_return_pct)
        self.assertAlmostEqual(102.5, result.total_return_index)

    def test_price_and_dividend_reconstruct_equity_total_return(self) -> None:
        result = accounting.equity_return_breakdown(
            previous_price_index=100.0,
            previous_total_return_index=120.0,
            eps_index=108.0,
            valuation_pe=17.0,
            payout_ratio_pct=42.0,
        )
        self.assertAlmostEqual(
            result.price_return_pct + result.dividend_yield_pct,
            result.total_return_pct,
        )
        self.assertAlmostEqual(
            120.0 * (1.0 + result.total_return_pct / 100.0),
            result.total_return_index,
        )

    def test_payout_ratio_and_non_finite_inputs_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "payout_ratio_pct"):
            accounting.dividend_yield_pct(100.0, 80.0, 100.0, 18.0)
        with self.assertRaisesRegex(ValueError, "must be finite"):
            accounting.equity_price_index(float("nan"), 18.0, 18.0)
        with self.assertRaisesRegex(ValueError, "greater than -100"):
            accounting.compound_total_return_index(100.0, -100.0)

    def test_sovereign_bond_price_carry_and_total_return_are_separate(self) -> None:
        unchanged = accounting.sovereign_bond_return_breakdown(
            previous_yield_pct=4.0,
            current_yield_pct=4.0,
        )
        rising = accounting.sovereign_bond_return_breakdown(
            previous_yield_pct=4.0,
            current_yield_pct=5.0,
        )
        falling = accounting.sovereign_bond_return_breakdown(
            previous_yield_pct=4.0,
            current_yield_pct=3.0,
        )
        self.assertEqual(0.0, unchanged.price_return_pct)
        self.assertEqual(4.0, unchanged.carry_pct)
        self.assertEqual(4.0, unchanged.total_return_pct)
        self.assertLess(rising.price_return_pct, 0.0)
        self.assertGreater(falling.price_return_pct, 0.0)
        for result in (unchanged, rising, falling):
            self.assertAlmostEqual(
                result.price_return_pct + result.carry_pct - result.credit_loss_pct,
                result.total_return_pct,
            )

    def test_corporate_spread_and_credit_loss_have_unique_effects(self) -> None:
        base = accounting.corporate_bond_return_breakdown(
            previous_yield_pct=4.0,
            current_yield_pct=4.0,
            previous_ig_spread_bps=100.0,
            current_ig_spread_bps=100.0,
            credit_loss_pct=0.0,
        )
        wider = accounting.corporate_bond_return_breakdown(
            previous_yield_pct=4.0,
            current_yield_pct=4.0,
            previous_ig_spread_bps=100.0,
            current_ig_spread_bps=200.0,
            credit_loss_pct=0.0,
        )
        impaired = accounting.corporate_bond_return_breakdown(
            previous_yield_pct=4.0,
            current_yield_pct=4.0,
            previous_ig_spread_bps=100.0,
            current_ig_spread_bps=100.0,
            credit_loss_pct=2.0,
        )
        self.assertLess(wider.price_return_pct, base.price_return_pct)
        self.assertEqual(base.price_return_pct, impaired.price_return_pct)
        self.assertAlmostEqual(base.total_return_pct - 2.0, impaired.total_return_pct)

    def test_60_40_is_exact_annual_rebalancing(self) -> None:
        self.assertAlmostEqual(
            8.2,
            accounting.rebalanced_60_40_return_pct(12.0, 2.5),
        )
        index = accounting.compound_total_return_index(
            250.0,
            accounting.rebalanced_60_40_return_pct(12.0, 2.5),
        )
        self.assertAlmostEqual(270.5, index)

    def test_holding_templates_are_explicit_and_sum_to_one(self) -> None:
        self.assertEqual(
            {"market_based", "balanced", "bank_centered"},
            set(accounting.HOLDING_TEMPLATES),
        )
        for template in accounting.HOLDING_TEMPLATES.values():
            accounting.validate_holding_template(template)
        with self.assertRaisesRegex(ValueError, "sum to 1"):
            accounting.validate_holding_template(
                replace(
                    accounting.HOLDING_TEMPLATES["balanced"],
                    cash_weight=0.10,
                )
            )

    def test_zero_equity_weight_removes_household_equity_channel(self) -> None:
        no_equity = accounting.HoldingTemplate("no_equity", 0.0, 0.60, 0.40)
        low_stock = accounting.household_real_financial_wealth_growth_pct(
            template=no_equity,
            equity_price_return_pct=-50.0,
            equity_dividend_yield_pct=0.0,
            sovereign_bond_total_return_pct=4.0,
            cash_nominal_return_pct=2.0,
            inflation_pct=2.0,
        )
        high_stock = accounting.household_real_financial_wealth_growth_pct(
            template=no_equity,
            equity_price_return_pct=80.0,
            equity_dividend_yield_pct=12.0,
            sovereign_bond_total_return_pct=4.0,
            cash_nominal_return_pct=2.0,
            inflation_pct=2.0,
        )
        self.assertEqual(low_stock, high_stock)
        self.assertEqual(
            0.0,
            accounting.household_cash_dividend_signal_pct(
                template=no_equity,
                equity_dividend_yield_pct=12.0,
            ),
        )

    def test_dividend_reinvestment_and_cash_shares_do_not_both_use_full_dividend(self) -> None:
        template = accounting.HOLDING_TEMPLATES["market_based"]
        cash_signal = accounting.household_cash_dividend_signal_pct(
            template=template,
            equity_dividend_yield_pct=4.0,
            dividend_cash_share=0.30,
        )
        self.assertAlmostEqual(0.60, cash_signal)
        reinvested_equity_dividend = template.equity_weight * 4.0 * 0.70
        self.assertAlmostEqual(2.0, reinvested_equity_dividend + cash_signal)

    def test_real_wealth_return_uses_inflation_as_a_price_level_bridge(self) -> None:
        template = accounting.HOLDING_TEMPLATES["balanced"]
        growth = accounting.household_real_financial_wealth_growth_pct(
            template=template,
            equity_price_return_pct=8.0,
            equity_dividend_yield_pct=2.0,
            sovereign_bond_total_return_pct=4.0,
            cash_nominal_return_pct=3.0,
            inflation_pct=2.0,
        )
        nominal = 0.35 * (8.0 + 2.0 * 0.70) + 0.40 * 4.0 + 0.25 * 3.0
        expected = ((1.0 + nominal / 100.0) / 1.02 - 1.0) * 100.0
        self.assertAlmostEqual(expected, growth)

    def test_one_time_wealth_impulse_decays_without_repeating_stock_level(self) -> None:
        first = accounting.wealth_consumption_impulse(
            current_real_wealth_growth_pct=10.0,
            previous_impulse=0.0,
        )
        second = accounting.wealth_consumption_impulse(
            current_real_wealth_growth_pct=0.0,
            previous_impulse=first,
        )
        third = accounting.wealth_consumption_impulse(
            current_real_wealth_growth_pct=0.0,
            previous_impulse=second,
        )
        self.assertAlmostEqual(4.5, first)
        self.assertLess(second, first)
        self.assertLess(third, second)
        self.assertGreater(third, 0.0)

    def test_stable_substream_seed_is_deterministic_and_partitioned(self) -> None:
        base = accounting.stable_substream_seed(
            424242,
            layer_id="global_equity_eps",
            year_index=7,
            shock_id="noise",
        )
        self.assertEqual(
            base,
            accounting.stable_substream_seed(
                424242,
                layer_id="global_equity_eps",
                year_index=7,
                shock_id="noise",
            ),
        )
        self.assertNotEqual(
            base,
            accounting.stable_substream_seed(
                424242,
                layer_id="global_equity_pe",
                year_index=7,
                shock_id="noise",
            ),
        )
        self.assertNotEqual(
            base,
            accounting.stable_substream_seed(
                424242,
                layer_id="global_equity_eps",
                region_id="china_mainland",
                year_index=7,
                shock_id="noise",
            ),
        )

    def test_stable_substream_does_not_consume_process_random_state(self) -> None:
        random.seed(20260724)
        expected = random.Random(20260724).random()
        accounting.stable_substream_seed(
            424242,
            layer_id="regional_equity_eps",
            region_id="north_america",
            year_index=12,
            shock_id="capital_destruction",
        )
        self.assertEqual(expected, random.random())

    def test_stable_substream_rejects_ambiguous_identity(self) -> None:
        with self.assertRaisesRegex(ValueError, "layer_id"):
            accounting.stable_substream_seed(1, layer_id="")
        with self.assertRaisesRegex(ValueError, "year_index"):
            accounting.stable_substream_seed(1, layer_id="asset", year_index=-1)

    def test_all_pure_outputs_are_finite_for_representative_inputs(self) -> None:
        equity = accounting.equity_return_breakdown(
            previous_price_index=95.0,
            previous_total_return_index=130.0,
            eps_index=112.0,
            valuation_pe=16.0,
        )
        sovereign = accounting.sovereign_bond_return_breakdown(
            previous_yield_pct=5.0,
            current_yield_pct=3.5,
        )
        corporate = accounting.corporate_bond_return_breakdown(
            previous_yield_pct=5.0,
            current_yield_pct=3.5,
            previous_ig_spread_bps=150.0,
            current_ig_spread_bps=110.0,
            credit_loss_pct=0.4,
        )
        for value in (
            *equity.__dict__.values(),
            *sovereign.__dict__.values(),
            *corporate.__dict__.values(),
        ):
            self.assertTrue(math.isfinite(float(value)))


if __name__ == "__main__":
    unittest.main()
