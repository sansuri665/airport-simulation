from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
MACRO_DIR = ROOT_DIR / "macro_layers"
if str(MACRO_DIR) not in sys.path:
    sys.path.insert(0, str(MACRO_DIR))

import macro_run_orchestrator_sim as orchestrator
from airport_sim.server import app as seed_explorer_server


SEED = 20261334
YEARS = 60
SEMANTIC_FIELDS = (
    "year_index",
    "global_gdp_trillion_usd",
    "realized_growth_pct",
    "headline_inflation_pct",
    "global_policy_rate_pct",
    "global_10y_yield_pct",
    "global_dollar_index",
    "global_high_yield_spread_bps",
    "global_equity_index",
    "brent_oil_price_usd",
    "financial_stress_index",
    "scenario_risk_id",
    "scenario_state",
    "scenario_phase",
)


def run_args(scenario_state: str = "none") -> argparse.Namespace:
    return argparse.Namespace(
        years=YEARS,
        start_year=2025,
        initial_gdp=100.0,
        volatility_scale=1.0,
        feedback_iterations=1,
        scenario_state=scenario_state,
        scenario_branch_id="auto",
        scenario_year=None,
        scenario_year_index=None,
        scenario_impact_years=None,
        scenario_tail_years=None,
        probabilistic_scenario_frequency=0.12,
        probabilistic_scenario_cooldown_years=6,
        probabilistic_scenario_min_events=1,
        probabilistic_scenario_max_events=0,
        probabilistic_scenario_min_year_index=2,
    )


def normalize_signed_zero(value: Any) -> Any:
    if isinstance(value, float) and value == 0.0:
        return 0.0
    return value


def semantic_digest(rows: list[dict[str, Any]]) -> str:
    selected = [
        [normalize_signed_zero(row.get(field)) for field in SEMANTIC_FIELDS]
        for row in rows
    ]
    raw = json.dumps(
        selected,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def header_digest(fields: list[str]) -> str:
    return hashlib.sha256("\x1f".join(fields).encode("utf-8")).hexdigest()


class LongHorizonModelContractTests(unittest.TestCase):
    """Protect long-run structure and scenario semantics before deeper refactors."""

    EXPECTED_SEMANTIC_DIGESTS = {
        "baseline": "1dbeb1583fd73554aa58cd70382be04f4c704ddd38bf7e492ac12bed429f207a",
        "occurred": "a6abe287c4d7ba4593b119fc6ed1865a08b5669f50d0308b15c39b1c6eefebe2",
        "probabilistic": "c8a32f095119bba434c415ab7fdd967a83299ff93be4f23d3a214600f7409cdc",
    }
    EXPECTED_HEADERS = {
        "global": (231, "e78c31293df90e6179847d239234eb4f0630c13b6eef93696ecd53dc5da7456f"),
        "reconciled": (97, "ae063d7f3b6e3e85a59b45450644f19121ce2c222b8c21c03f69830617de6d1f"),
        "city_beijing": (195, "256b25a80228eab581df0db695c5c94deee6bab54e03536c9238c7981c3e303b"),
        "operations_beijing": (261, "69db9b46ab78437b00a929cb8d3804de3d00a590a0f165c8f8472a51c3914358"),
    }

    @classmethod
    def setUpClass(cls) -> None:
        baseline_args = run_args()
        cls.baseline = orchestrator.run_global_variant(SEED, baseline_args, "baseline")["rows"]
        cls.regional = orchestrator.run_regional_and_reconciliation(SEED, cls.baseline)

        occurred_args = run_args("occurred")
        cls.occurred_selection = orchestrator.select_branch_scenario(cls.baseline, occurred_args)
        cls.occurred_path = orchestrator.build_scenario_event_path(
            cls.occurred_selection,
            occurred_args.years,
        )
        cls.occurred = orchestrator.run_global_variant(
            SEED,
            occurred_args,
            "occurred_contract_test",
            cls.occurred_path,
        )["rows"]

        probabilistic_args = run_args("probabilistic")
        cls.probabilistic_events = orchestrator.select_probabilistic_branch_scenarios(
            cls.baseline,
            probabilistic_args,
            SEED,
        )
        cls.probabilistic_path = orchestrator.build_scenario_timeline_event_path(
            cls.probabilistic_events,
            probabilistic_args.years,
        )
        cls.probabilistic = orchestrator.run_global_variant(
            SEED,
            probabilistic_args,
            "probabilistic_contract_test",
            cls.probabilistic_path,
        )["rows"]

    def test_60_year_scenario_semantics_are_stable(self) -> None:
        self.assertEqual(YEARS + 1, len(self.baseline))
        self.assertEqual(YEARS + 1, len(self.occurred))
        self.assertEqual(YEARS + 1, len(self.probabilistic))
        self.assertEqual(
            self.EXPECTED_SEMANTIC_DIGESTS,
            {
                "baseline": semantic_digest(self.baseline),
                "occurred": semantic_digest(self.occurred),
                "probabilistic": semantic_digest(self.probabilistic),
            },
        )

        self.assertEqual(
            ("false_dawn", 55, 2080),
            (
                self.occurred_selection["risk"]["id"],
                self.occurred_selection["trigger_index"],
                self.occurred_selection["trigger_year"],
            ),
        )
        self.assertEqual([56, 57, 58, 59, 60], sorted(self.occurred_path))
        self.assertEqual(
            [("false_dawn", 9, 2034), ("false_dawn", 55, 2080)],
            [
                (event["risk"]["id"], event["trigger_index"], event["trigger_year"])
                for event in self.probabilistic_events
            ],
        )
        self.assertEqual(
            [10, 11, 12, 13, 14, 15, 16, 56, 57, 58, 59, 60],
            sorted(self.probabilistic_path),
        )
        self.assertEqual(5, orchestrator.active_scenario_rows(self.occurred))
        self.assertEqual(12, orchestrator.active_scenario_rows(self.probabilistic))

    def test_60_year_regional_and_city_structure_is_complete(self) -> None:
        expected_regions = set(orchestrator.REGION_ORDER)
        self.assertEqual(14, len(expected_regions))
        self.assertEqual(expected_regions, set(self.regional["regional_rows_by_region"]))
        self.assertEqual(expected_regions, set(self.regional["aviation_rows_by_region"]))
        self.assertEqual(expected_regions, set(self.regional["supply_rows_by_region"]))

        for dataset_name in (
            "regional_rows_by_region",
            "aviation_rows_by_region",
            "supply_rows_by_region",
        ):
            for rows in self.regional[dataset_name].values():
                self.assertEqual(YEARS + 1, len(rows), dataset_name)
                self.assertEqual(list(range(YEARS + 1)), [int(row["year_index"]) for row in rows])
                self.assertEqual({SEED}, {int(row["seed"]) for row in rows})

        reconciled = self.regional["reconciled_rows"]
        self.assertEqual(14 * (YEARS + 1), len(reconciled))
        self.assertEqual(expected_regions, {str(row["region_id"]) for row in reconciled})
        self.assertEqual(
            {year_index: 14 for year_index in range(YEARS + 1)},
            Counter(int(row["year_index"]) for row in reconciled),
        )

        city_rows_by_market = self.regional["city_airport_rows_by_market"]
        self.assertEqual(set(orchestrator.CITY_MARKET_CONFIGS), set(city_rows_by_market))
        self.assertEqual(47, len(city_rows_by_market))
        self.assertTrue(all(len(rows) == YEARS + 1 for rows in city_rows_by_market.values()))

        self.assertEqual(
            {"beijing_airport_system": 7018},
            {
                market_id: len(rows)
                for market_id, rows in self.regional["potential_passenger_forecast_rows_by_market"].items()
            },
        )
        self.assertEqual(
            {"beijing_airport_system": 244},
            {
                market_id: len(rows)
                for market_id, rows in self.regional["quarterly_operations_rows_by_market"].items()
            },
        )
        self.assertEqual(
            {"beijing_airport_system": 244},
            {
                market_id: len(rows)
                for market_id, rows in self.regional["financial_state_rows_by_market"].items()
            },
        )
        self.assertEqual(
            {"beijing_airport_system": 224},
            {
                market_id: len(rows)
                for market_id, rows in self.regional["valuation_forecast_rows_by_market"].items()
            },
        )
        self.assertEqual(46, len(self.regional["city_airport_downstream_skips"]))

    def test_long_horizon_forecasts_remain_finite_smooth_and_revision_bounded(self) -> None:
        rows = self.regional["potential_passenger_forecast_rows_by_market"][
            "beijing_airport_system"
        ]
        numeric_fields = (
            "forecast_effective_passengers_mid_million",
            "forecast_potential_passengers_mid_million",
            "forecast_airline_supply_passengers_mid_million",
            "forecast_effective_passengers_low_million",
            "forecast_effective_passengers_high_million",
            "forecast_revision_pct",
        )
        for row in rows:
            for field in numeric_fields:
                self.assertTrue(
                    math.isfinite(float(row[field])),
                    msg=f"{field} is not finite for {row['forecast_report_id']} "
                    f"{row['as_of_year']}->{row['forecast_year']}",
                )
            self.assertLess(
                float(row["forecast_effective_passengers_mid_million"]),
                1000.0,
            )

        routine_revisions = [
            abs(float(row["forecast_revision_pct"]))
            for row in rows
            if row["forecast_revision_reason"] == "routine_inherited_update"
            and row["forecast_previous_mid_million"] is not None
        ]
        self.assertTrue(routine_revisions)
        self.assertLessEqual(max(routine_revisions), 10.5)

        grouped: dict[tuple[object, object], list[dict[str, Any]]] = {}
        for row in rows:
            if row["future_peek_mode"] == "true":
                continue
            grouped.setdefault(
                (row["forecast_report_id"], row["as_of_year"]),
                [],
            ).append(row)
        for report_rows in grouped.values():
            report_rows.sort(key=lambda row: int(row["forecast_year"]))
            for metric, current_field in (
                (
                    "forecast_potential_passengers_mid_million",
                    "current_potential_passengers_million",
                ),
                (
                    "forecast_airline_supply_passengers_mid_million",
                    "current_airline_supply_passengers_million",
                ),
            ):
                previous = float(report_rows[0][current_field])
                growth_rates: list[float] = []
                for row in report_rows:
                    value = float(row[metric])
                    growth_rates.append(
                        ((value / previous) - 1.0) * 100.0 if previous else 0.0
                    )
                    previous = value
                changes = [
                    right - left
                    for left, right in zip(growth_rates, growth_rates[1:])
                ]
                directions = [
                    1 if change > 0.35 else -1 if change < -0.35 else 0
                    for change in changes
                ]
                directions = [direction for direction in directions if direction]
                inflections = sum(
                    left != right
                    for left, right in zip(directions, directions[1:])
                )
                self.assertLessEqual(inflections, 2)

    def test_key_csv_headers_are_stable(self) -> None:
        csv_specs = {
            "global": (orchestrator.GLOBAL_OUTPUT_FIELDS, self.baseline),
            "reconciled": (orchestrator.REGIONAL_VALUE_FIELDS, self.regional["reconciled_rows"]),
            "city_beijing": (
                orchestrator.CITY_AIRPORT_DEMAND_FIELDS,
                self.regional["city_airport_rows_by_market"]["beijing_airport_system"],
            ),
            "operations_beijing": (
                orchestrator.QUARTERLY_OPERATIONS_FIELDS,
                self.regional["quarterly_operations_rows_by_market"]["beijing_airport_system"],
            ),
        }
        with tempfile.TemporaryDirectory() as temporary_dir:
            output_dir = Path(temporary_dir)
            actual: dict[str, tuple[int, str]] = {}
            for name, (base_fields, rows) in csv_specs.items():
                path = output_dir / f"{name}.csv"
                orchestrator.write_csv_file(path, rows, base_fields)
                with path.open("r", newline="", encoding="utf-8") as handle:
                    fields = next(csv.reader(handle))
                actual[name] = (len(fields), header_digest(fields))

        self.assertEqual(self.EXPECTED_HEADERS, actual)

    def test_player_financing_action_replays_through_operations_and_finance(self) -> None:
        actions = seed_explorer_server.clean_player_actions(
            [
                {
                    "type": "draw_loan",
                    "productId": "short_turnover",
                    "principalMillionCny": 5000,
                    "tenorQuarters": 4,
                    "gracePeriodQuarters": 0,
                    "startedAtIndex": 20,
                    "startedAtLabel": "2030 Q1",
                }
            ]
        )
        self.assertEqual(1, len(actions))
        self.assertEqual("loan:short_turnover:20", actions[0]["id"])

        city_rows = self.regional["city_airport_rows_by_market"]["beijing_airport_system"]
        with tempfile.TemporaryDirectory() as temporary_dir:
            operations_config_path, finance_config_path = seed_explorer_server.write_player_simulation_configs(
                Path(temporary_dir),
                actions,
            )
            operations_rows = orchestrator.simulate_quarterly_operations(
                city_rows,
                orchestrator.load_quarterly_operations_config(operations_config_path),
            )
            finance_rows = orchestrator.simulate_financial_state(
                operations_rows,
                orchestrator.load_financial_state_config(finance_config_path),
            )

        rows_2030 = {row["quarter"]: row for row in finance_rows if int(row["year"]) == 2030}
        self.assertEqual("loan:short_turnover:20", rows_2030["Q1"]["loan_drawdown_ids"])
        self.assertEqual(5000.0, rows_2030["Q1"]["period_loan_drawdown_million_cny"])
        self.assertEqual("loan:short_turnover:20", rows_2030["Q4"]["loan_principal_repayment_ids"])
        self.assertEqual(5000.0, rows_2030["Q4"]["period_principal_repayment_million_cny"])


if __name__ == "__main__":
    unittest.main()
