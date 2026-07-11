from __future__ import annotations

import argparse
import csv
import errno
import hashlib
import json
import os
import platform
import random
import shutil
import time
from importlib import import_module
from pathlib import Path
from typing import Any

_SIBLING_PREFIX = f"{__package__}." if __package__ else ""


def _sibling_module(name: str):
    return import_module(f"{_SIBLING_PREFIX}{name}")


financial_state_layer = _sibling_module("city_airport_financial_state_layer_sim")
city_market_layer = _sibling_module("city_airport_market_demand_layer_sim")
potential_forecast_layer = _sibling_module("city_airport_potential_passenger_forecast_layer_sim")
quarterly_operations_layer = _sibling_module("city_airport_quarterly_operations_layer_sim")
valuation_layer = _sibling_module("city_airport_valuation_forecast_layer_sim")
global_feedback_layer = _sibling_module("global_macro_feedback_calibration_sim")
air_supply_layer = _sibling_module("regional_air_capacity_supply_layer_sim")
aviation_demand_layer = _sibling_module("regional_aviation_demand_layer_sim")
regional_macro_layer = _sibling_module("regional_macro_layer_sim")
reconciliation_layer = _sibling_module("regional_macro_reconciliation_sim")
simulation_utils = _sibling_module("simulation_utils")

FINANCIAL_STATE_CONFIG_DIR = financial_state_layer.DEFAULT_CONFIG_DIR
FINANCIAL_STATE_FIELDS = financial_state_layer.FINANCIAL_STATE_FIELDS
load_financial_state_config = financial_state_layer.load_config
simulate_financial_state = financial_state_layer.simulate_financial_state
summarize_financial_state = financial_state_layer.summarize
write_financial_state_viewer_data_js = financial_state_layer.write_viewer_data_js

CITY_AIRPORT_DEMAND_FIELDS = city_market_layer.CITY_AIRPORT_DEMAND_FIELDS
CITY_MARKET_CONFIGS = city_market_layer.CITY_MARKET_CONFIGS
merge_city_airport_inputs = city_market_layer.merge_region_inputs
simulate_city_airport_demand = city_market_layer.simulate_city_airport_demand
summarize_city_airport_seed = city_market_layer.summarize_market_seed
write_city_airport_viewer_data_js = city_market_layer.write_viewer_data_js

POTENTIAL_PASSENGER_FORECAST_CONFIG_DIR = potential_forecast_layer.DEFAULT_CONFIG_DIR
POTENTIAL_PASSENGER_FORECAST_FIELDS = potential_forecast_layer.POTENTIAL_PASSENGER_FORECAST_FIELDS
load_potential_passenger_forecast_config = potential_forecast_layer.load_config
simulate_potential_passenger_forecast = potential_forecast_layer.simulate_potential_passenger_forecast
summarize_potential_passenger_forecast = potential_forecast_layer.summarize
write_potential_passenger_forecast_viewer_data_js = potential_forecast_layer.write_viewer_data_js
write_potential_passenger_forecast_lazy_assets = potential_forecast_layer.write_viewer_lazy_assets

QUARTERLY_OPERATIONS_CONFIG_DIR = quarterly_operations_layer.DEFAULT_CONFIG_DIR
QUARTERLY_OPERATIONS_FIELDS = quarterly_operations_layer.QUARTERLY_OPERATIONS_FIELDS
load_quarterly_operations_config = quarterly_operations_layer.load_config
simulate_quarterly_operations = quarterly_operations_layer.simulate_quarterly_operations
summarize_quarterly_operations = quarterly_operations_layer.summarize
write_quarterly_operations_viewer_data_js = quarterly_operations_layer.write_viewer_data_js

VALUATION_FORECAST_CONFIG_DIR = valuation_layer.DEFAULT_CONFIG_DIR
VALUATION_FORECAST_FIELDS = valuation_layer.VALUATION_FORECAST_FIELDS
load_valuation_forecast_config = valuation_layer.load_config
simulate_valuation_forecast = valuation_layer.simulate_valuation_forecast
summarize_valuation_forecast = valuation_layer.summarize
write_valuation_forecast_viewer_data_js = valuation_layer.write_viewer_data_js

COMBINED_MACRO_FEEDBACK_FIELDS = global_feedback_layer.COMBINED_MACRO_FEEDBACK_FIELDS
annotate_feedback_records = global_feedback_layer.annotate_feedback_records
blend_feedback_paths = global_feedback_layer.blend_feedback_paths
convergence_summary = global_feedback_layer.convergence_summary
derive_feedback_path = global_feedback_layer.derive_feedback_path
run_full_chain = global_feedback_layer.run_full_chain
summarize_seed = global_feedback_layer.summarize_seed
write_global_viewer_data_js = global_feedback_layer.write_viewer_data_js

AIR_SUPPLY_FIELDS = air_supply_layer.AIR_SUPPLY_FIELDS
AIR_SUPPLY_REGION_CONFIGS = air_supply_layer.AIR_SUPPLY_REGION_CONFIGS
simulate_region_air_supply = air_supply_layer.simulate_region_air_supply
summarize_supply_seed = air_supply_layer.summarize_region_seed
write_supply_viewer_data_js = air_supply_layer.write_viewer_data_js

AVIATION_DEMAND_FIELDS = aviation_demand_layer.AVIATION_DEMAND_FIELDS
AVIATION_REGION_CONFIGS = aviation_demand_layer.AVIATION_REGION_CONFIGS
merge_region_inputs = aviation_demand_layer.merge_region_inputs
simulate_region_aviation_demand = aviation_demand_layer.simulate_region_aviation_demand
summarize_aviation_seed = aviation_demand_layer.summarize_region_seed
write_aviation_viewer_data_js = aviation_demand_layer.write_viewer_data_js

REGION_CONFIGS = regional_macro_layer.REGION_CONFIGS
REGIONAL_MACRO_FIELDS = regional_macro_layer.REGIONAL_MACRO_FIELDS
build_global_params = regional_macro_layer.build_global_params
simulate_region_for_global_path = regional_macro_layer.simulate_region_for_global_path
summarize_region_seed = regional_macro_layer.summarize_region_seed
write_regional_viewer_data_js = regional_macro_layer.write_viewer_data_js

DIAGNOSTIC_FIELDS = reconciliation_layer.DIAGNOSTIC_FIELDS
REGION_ORDER = reconciliation_layer.REGION_ORDER
REGIONAL_VALUE_FIELDS = reconciliation_layer.REGIONAL_VALUE_FIELDS
build_reconciliation = reconciliation_layer.build_reconciliation
key_for = reconciliation_layer.key_for
write_reconciliation_viewer_js = reconciliation_layer.write_viewer_js

clamp = simulation_utils.clamp
round_record = simulation_utils.round_record


ORCHESTRATOR_VERSION = "macro-run-orchestrator-v0.5"
RUN_INDEX_VERSION = "macro-run-index-v0.5"
RUN_MANIFEST_SCHEMA_VERSION = "airport-macro-run-manifest-v1"
OUTPUT_SCHEMA_VERSION = "airport-model-output-v1"
MODEL_VERSION = "airport-model-v0.5"
AIRPORT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_ROOT = AIRPORT_DIR / "output" / "macro_runs"
DEFAULT_VIEWER_OUTPUT_ROOT = AIRPORT_DIR / "output"
VIEWER_RELEASE_MANIFEST_VERSION = "airport-viewer-release-manifest-v1"
GLOBAL_VIEWER_LAZY_INDEX_VERSION = "airport-global-viewer-lazy-index-v1"
GLOBAL_VIEWER_REGION_CHUNK_VERSION = "airport-global-viewer-region-chunk-v1"
OPERATIONS_VIEWER_LAZY_INDEX_VERSION = "airport-operations-viewer-lazy-index-v1"
OPERATIONS_VIEWER_CHUNK_VERSION = "airport-operations-viewer-chunk-v1"

FEEDBACK_NUMERIC_FIELDS = (
    "feedback_growth_impulse_pct",
    "feedback_output_gap_impulse_pct",
    "feedback_financial_stress_impulse",
    "feedback_inflation_impulse_pct",
    "feedback_policy_impulse_pct",
)

SCENARIO_NUMERIC_FIELDS = (
    "scenario_impact_years",
    "scenario_tail_years",
    "scenario_event_severity",
    "scenario_policy_rate_impulse",
    "scenario_liquidity_impulse",
    "scenario_credit_stress_impulse",
    "scenario_dollar_pressure_impulse",
    "scenario_energy_price_impulse",
    "scenario_gdp_lagged_support",
)

SCENARIO_TEXT_FIELDS = (
    "global_path_variant",
    "scenario_state",
    "scenario_risk_id",
    "scenario_risk_label",
    "scenario_trigger_index",
    "scenario_trigger_year",
    "scenario_phase",
    "scenario_event_type",
    "scenario_event_phase",
    "scenario_feedback_source",
)

SCENARIO_FIELDS = tuple(SCENARIO_TEXT_FIELDS) + tuple(SCENARIO_NUMERIC_FIELDS)

GLOBAL_OUTPUT_FIELDS = tuple(COMBINED_MACRO_FEEDBACK_FIELDS) + tuple(
    field for field in SCENARIO_FIELDS if field not in COMBINED_MACRO_FEEDBACK_FIELDS
)


BRANCH_SCENARIO_PROFILES: dict[str, dict[str, Any]] = {
    "false_dawn_reversal": {
        "label": "虚假黎明",
        "growth": -1.05,
        "gap": -1.35,
        "stress": 0.42,
        "inflation": -0.18,
        "policy": -0.36,
        "policy_rate": -0.22,
        "liquidity": 0.20,
        "credit_stress": 0.48,
        "dollar": 0.14,
        "energy": -0.08,
        "support": 0.10,
        "event_phase": "double_dip",
        "event_type": "credit_crisis",
    },
    "policy_mistake_tightening": {
        "label": "政策失误：过早收紧",
        "growth": -0.78,
        "gap": -1.05,
        "stress": 0.34,
        "inflation": -0.08,
        "policy": 0.32,
        "policy_rate": 0.42,
        "liquidity": -0.22,
        "credit_stress": 0.38,
        "dollar": 0.16,
        "energy": -0.04,
        "support": -0.06,
        "event_phase": "over_tightening",
        "event_type": "policy_mistake",
    },
    "energy_supply_squeeze": {
        "label": "Energy Supply Squeeze",
        "growth": -0.72,
        "gap": -0.58,
        "stress": 0.22,
        "inflation": 0.86,
        "policy": 0.18,
        "policy_rate": 0.28,
        "liquidity": -0.08,
        "credit_stress": 0.18,
        "dollar": 0.10,
        "energy": 0.95,
        "support": -0.05,
        "event_phase": "oil_shock",
        "event_type": "energy_crisis",
    },
    "dollar_funding_squeeze": {
        "label": "Dollar Funding Squeeze",
        "growth": -0.70,
        "gap": -0.82,
        "stress": 0.50,
        "inflation": -0.04,
        "policy": -0.24,
        "policy_rate": -0.18,
        "liquidity": -0.44,
        "credit_stress": 0.58,
        "dollar": 0.72,
        "energy": -0.05,
        "support": 0.04,
        "event_phase": "funding_squeeze",
        "event_type": "dollar_squeeze",
    },
    "credit_crunch_amplification": {
        "label": "Credit Crunch",
        "growth": -0.92,
        "gap": -1.12,
        "stress": 0.58,
        "inflation": -0.12,
        "policy": -0.38,
        "policy_rate": -0.30,
        "liquidity": 0.10,
        "credit_stress": 0.68,
        "dollar": 0.22,
        "energy": -0.10,
        "support": 0.08,
        "event_phase": "credit_freeze",
        "event_type": "credit_crisis",
    },
    "stagflation_entrenchment": {
        "label": "Stagflation Entrenchment",
        "growth": -0.62,
        "gap": -0.72,
        "stress": 0.28,
        "inflation": 0.78,
        "policy": 0.28,
        "policy_rate": 0.36,
        "liquidity": -0.14,
        "credit_stress": 0.32,
        "dollar": 0.12,
        "energy": 0.42,
        "support": -0.04,
        "event_phase": "sticky_inflation",
        "event_type": "stagflation",
    },
    "soft_landing_success": {
        "label": "软着陆成功",
        "growth": 0.35,
        "gap": 0.42,
        "stress": -0.20,
        "inflation": -0.18,
        "policy": -0.16,
        "policy_rate": -0.18,
        "liquidity": 0.12,
        "credit_stress": -0.22,
        "dollar": -0.08,
        "energy": -0.03,
        "support": 0.06,
        "event_phase": "orderly_slowdown",
        "event_type": "soft_landing",
    },
    "policy_reflation_boost": {
        "label": "Policy Reflation",
        "growth": 0.58,
        "gap": 0.64,
        "stress": -0.26,
        "inflation": 0.24,
        "policy": -0.28,
        "policy_rate": -0.32,
        "liquidity": 0.36,
        "credit_stress": -0.28,
        "dollar": -0.12,
        "energy": 0.10,
        "support": 0.16,
        "event_phase": "reflation",
        "event_type": "policy_reflation",
    },
    "risk_asset_boom_overheat": {
        "label": "Risk Asset Boom",
        "growth": 0.42,
        "gap": 0.36,
        "stress": -0.18,
        "inflation": 0.22,
        "policy": 0.12,
        "policy_rate": 0.10,
        "liquidity": 0.24,
        "credit_stress": -0.18,
        "dollar": -0.10,
        "energy": 0.18,
        "support": 0.08,
        "event_phase": "risk_on",
        "event_type": "asset_boom",
    },
    "bank_lending_freeze": {
        "label": "Bank Lending Freeze",
        "growth": -0.88,
        "gap": -1.00,
        "stress": 0.48,
        "inflation": -0.18,
        "policy": -0.34,
        "policy_rate": -0.28,
        "liquidity": 0.05,
        "credit_stress": 0.56,
        "dollar": 0.18,
        "energy": -0.08,
        "support": 0.06,
        "event_phase": "bank_credit_freeze",
        "event_type": "banking_stress",
    },
    "inflation_expectation_unanchor": {
        "label": "Inflation Unanchoring",
        "growth": -0.45,
        "gap": -0.52,
        "stress": 0.24,
        "inflation": 0.92,
        "policy": 0.46,
        "policy_rate": 0.48,
        "liquidity": -0.20,
        "credit_stress": 0.30,
        "dollar": 0.10,
        "energy": 0.26,
        "support": -0.05,
        "event_phase": "expectation_shock",
        "event_type": "inflation_unanchor",
    },
    "commodity_disinflation_relief": {
        "label": "Commodity Disinflation Relief",
        "growth": 0.30,
        "gap": 0.30,
        "stress": -0.16,
        "inflation": -0.52,
        "policy": -0.20,
        "policy_rate": -0.22,
        "liquidity": 0.10,
        "credit_stress": -0.14,
        "dollar": -0.06,
        "energy": -0.55,
        "support": 0.04,
        "event_phase": "energy_relief",
        "event_type": "disinflation_relief",
    },
    "debt_deflation_loop": {
        "label": "Debt Deflation Loop",
        "growth": -1.08,
        "gap": -1.28,
        "stress": 0.66,
        "inflation": -0.42,
        "policy": -0.48,
        "policy_rate": -0.42,
        "liquidity": 0.18,
        "credit_stress": 0.72,
        "dollar": 0.26,
        "energy": -0.18,
        "support": 0.10,
        "event_phase": "balance_sheet_recession",
        "event_type": "debt_deflation",
    },
}

BRANCH_SCENARIO_PROFILES.update(
    {
        "false_dawn": {
            **BRANCH_SCENARIO_PROFILES["false_dawn_reversal"],
            "label": "虚假黎明",
            "event_type": "false_dawn",
        },
        "policy_behind_curve": {
            **BRANCH_SCENARIO_PROFILES["inflation_expectation_unanchor"],
            "label": "政策失误：落后曲线",
            "event_type": "policy_behind_curve",
        },
        "credit_accident": {
            **BRANCH_SCENARIO_PROFILES["credit_crunch_amplification"],
            "label": "信用事故",
            "event_type": "credit_accident",
        },
        "bank_lending_trap": {
            **BRANCH_SCENARIO_PROFILES["bank_lending_freeze"],
            "label": "银行惜贷循环",
            "event_type": "bank_lending_trap",
        },
        "dollar_squeeze_escalation": {
            **BRANCH_SCENARIO_PROFILES["dollar_funding_squeeze"],
            "label": "美元挤兑升级",
            "event_type": "dollar_squeeze_escalation",
        },
        "energy_shock_escalation": {
            **BRANCH_SCENARIO_PROFILES["energy_supply_squeeze"],
            "label": "能源冲击升级",
            "event_type": "energy_shock_escalation",
        },
        "bond_market_accident": {
            "label": "债券市场失控",
            "growth": -0.70,
            "gap": -0.68,
            "stress": 0.54,
            "inflation": 0.18,
            "policy": 0.28,
            "policy_rate": 0.38,
            "liquidity": -0.32,
            "credit_stress": 0.50,
            "dollar": 0.22,
            "energy": 0.05,
            "support": -0.06,
            "event_phase": "bond_selloff",
            "event_type": "bond_market_accident",
        },
        "liquidity_bubble": {
            **BRANCH_SCENARIO_PROFILES["risk_asset_boom_overheat"],
            "label": "流动性牛市脱实向虚",
            "event_type": "liquidity_bubble",
        },
        "refinancing_wall": {
            **BRANCH_SCENARIO_PROFILES["credit_crunch_amplification"],
            "label": "再融资墙",
            "event_type": "refinancing_wall",
        },
        "demand_destruction_disinflation": {
            "label": "需求破坏式降通胀",
            "growth": -0.72,
            "gap": -0.88,
            "stress": 0.34,
            "inflation": -0.46,
            "policy": -0.34,
            "policy_rate": -0.30,
            "liquidity": 0.06,
            "credit_stress": 0.34,
            "dollar": 0.12,
            "energy": -0.38,
            "support": 0.04,
            "event_phase": "demand_destruction",
            "event_type": "demand_destruction_disinflation",
        },
        "stagflation_trap": {
            **BRANCH_SCENARIO_PROFILES["stagflation_entrenchment"],
            "label": "滞胀陷阱",
            "event_type": "stagflation_trap",
        },
        "risk_asset_bull_fragility": {
            "label": "风险资产牛市脆弱化",
            "growth": -0.34,
            "gap": -0.28,
            "stress": 0.32,
            "inflation": 0.08,
            "policy": 0.08,
            "policy_rate": 0.10,
            "liquidity": -0.10,
            "credit_stress": 0.28,
            "dollar": 0.08,
            "energy": 0.04,
            "support": -0.02,
            "event_phase": "risk_asset_fragility",
            "event_type": "risk_asset_bull_fragility",
        },
    }
)

CANONICAL_BRANCH_SCENARIO_IDS = (
    "soft_landing_success",
    "false_dawn",
    "policy_mistake_tightening",
    "policy_behind_curve",
    "credit_accident",
    "bank_lending_trap",
    "refinancing_wall",
    "dollar_squeeze_escalation",
    "energy_shock_escalation",
    "bond_market_accident",
    "liquidity_bubble",
    "stagflation_trap",
)

BRANCH_SCENARIO_ALIASES = {
    "false_dawn_reversal": "false_dawn",
    "credit_crunch_amplification": "credit_accident",
    "debt_deflation_loop": "credit_accident",
    "bank_lending_freeze": "bank_lending_trap",
    "dollar_funding_squeeze": "dollar_squeeze_escalation",
    "energy_supply_squeeze": "energy_shock_escalation",
    "inflation_expectation_unanchor": "policy_behind_curve",
    "policy_reflation_boost": "soft_landing_success",
    "commodity_disinflation_relief": "soft_landing_success",
    "demand_destruction_disinflation": "false_dawn",
    "stagflation_entrenchment": "stagflation_trap",
    "risk_asset_boom_overheat": "liquidity_bubble",
    "risk_asset_bull_fragility": "liquidity_bubble",
}

BRANCH_SCENARIO_PROFILES = {
    key: BRANCH_SCENARIO_PROFILES[key]
    for key in CANONICAL_BRANCH_SCENARIO_IDS
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run one coherent global/regional/city airport path, with optional manual or probabilistic branch paths."
    )
    parser.add_argument("--seed", type=int, default=None, help="Fixed seed. If omitted, a large random seed is used.")
    parser.add_argument("--random-seed", action="store_true", help="Force a new large random seed.")
    parser.add_argument("--seed-min", type=int, default=1_000_000)
    parser.add_argument("--seed-max", type=int, default=9_999_999_999)
    parser.add_argument("--start-year", type=int, default=2025)
    parser.add_argument("--years", type=int, default=60)
    parser.add_argument("--initial-gdp", type=float, default=100.0)
    parser.add_argument("--volatility-scale", type=float, default=1.0)
    parser.add_argument("--feedback-iterations", type=int, default=3)
    parser.add_argument(
        "--scenario-state",
        choices=("none", "occurred", "counterfactual", "probabilistic"),
        default="none",
        help="Run a second path where branch risk becomes active manually or by seeded probability.",
    )
    parser.add_argument(
        "--scenario-branch-id",
        default="auto",
        help="Branch risk id to activate. Use auto to select the strongest baseline watchlist risk.",
    )
    parser.add_argument("--scenario-year", type=int, default=None, help="Calendar year of the branch trigger.")
    parser.add_argument("--scenario-year-index", type=int, default=None, help="Zero-based year index of the trigger.")
    parser.add_argument("--scenario-impact-years", type=int, default=None)
    parser.add_argument("--scenario-tail-years", type=int, default=None)
    parser.add_argument(
        "--probabilistic-scenario-frequency",
        type=float,
        default=0.12,
        help="Annual probability multiplier for --scenario-state probabilistic.",
    )
    parser.add_argument(
        "--probabilistic-scenario-cooldown-years",
        type=int,
        default=6,
        help="Minimum quiet years after an automatically triggered branch event and its tail.",
    )
    parser.add_argument(
        "--probabilistic-scenario-min-events",
        type=int,
        default=1,
        help="Minimum automatic branch events to force from strongest candidates if probability draws miss.",
    )
    parser.add_argument(
        "--probabilistic-scenario-max-events",
        type=int,
        default=0,
        help="Maximum automatic branch events. Use 0 for an auto cap based on run length.",
    )
    parser.add_argument(
        "--probabilistic-scenario-min-year-index",
        type=int,
        default=2,
        help="Earliest zero-based year index eligible for automatic branch triggering.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_OUTPUT_ROOT,
        help="Run archive root. Defaults to <airport>/output/macro_runs regardless of the current working directory.",
    )
    parser.add_argument("--index-only", action="store_true", help="Refresh macro_run_index.js without running simulation.")
    parser.add_argument(
        "--publish-viewer",
        choices=("none", "baseline", "scenario"),
        default="none",
        help="Also copy one variant to <airport>/output so global_gdp_viewer.html reads it.",
    )
    parser.add_argument(
        "--viewer-output-root",
        type=Path,
        default=DEFAULT_VIEWER_OUTPUT_ROOT,
        help="Canonical viewer data root. Defaults to <airport>/output regardless of the current working directory.",
    )
    parser.add_argument(
        "--artifact-profile",
        choices=("full", "seed-cache"),
        default="full",
        help=(
            "Output artifact profile. 'full' keeps static Viewer bundles and lazy assets; "
            "'seed-cache' keeps only model/API data needed by Seed Explorer."
        ),
    )
    parser.add_argument("--run-id", default=None)
    return parser.parse_args()


def resolve_seed(args: argparse.Namespace) -> int:
    if args.random_seed or args.seed is None:
        low = min(args.seed_min, args.seed_max)
        high = max(args.seed_min, args.seed_max)
        return random.SystemRandom().randint(low, high)
    return args.seed


def clean_run_id(value: str) -> str:
    chars = []
    for char in value:
        if char.isalnum() or char in ("-", "_"):
            chars.append(char)
        else:
            chars.append("_")
    return "".join(chars).strip("_") or "macro_run"


def ordered_fields(base_fields: tuple[str, ...] | list[str], rows: list[dict[str, Any]]) -> list[str]:
    fields = list(dict.fromkeys(base_fields))
    seen = set(fields)
    for row in rows:
        for key in row:
            if key not in seen:
                fields.append(key)
                seen.add(key)
    return fields


def write_csv_file(path: Path, rows: list[dict[str, Any]], base_fields: tuple[str, ...] | list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ordered_fields(base_fields, rows)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def atomic_write_text_file(path: Path, content: str, encoding: str = "utf-8") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Keep the temporary basename short: deeply nested regional output paths can
    # otherwise exceed the traditional Windows path limit during staging.
    temporary_path = path.with_name(f".__tmp_{os.getpid()}_{time.time_ns():x}")
    try:
        temporary_path.write_text(content, encoding=encoding)
        os.replace(temporary_path, path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def replace_directory_with_retry(source: Path, target: Path, attempts: int = 4) -> None:
    """Retry only transient Windows directory sharing/access failures."""
    for attempt in range(attempts):
        try:
            os.replace(source, target)
            return
        except OSError as error:
            windows_code = getattr(error, "winerror", None)
            retryable = os.name == "nt" and (
                windows_code in {5, 32}
                or error.errno in {errno.EACCES, errno.EBUSY}
            )
            if not retryable or attempt + 1 >= attempts:
                raise
            time.sleep(0.05 * (2**attempt))


def write_json_file(path: Path, payload: dict[str, Any]) -> None:
    atomic_write_text_file(path, json.dumps(payload, ensure_ascii=False, indent=2))


def read_json_file(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_global_viewer_lazy_assets(
    global_dir: Path,
    regional_result: dict[str, Any],
) -> dict[str, Any]:
    """Publish one compact Viewer chunk per region without changing model rows."""
    global_dir.mkdir(parents=True, exist_ok=True)
    chunk_dir_name = "global_viewer_chunks"
    chunk_dir = global_dir / chunk_dir_name
    chunk_dir.mkdir(parents=True, exist_ok=True)

    regions: list[dict[str, Any]] = []
    for region_id in REGION_ORDER:
        regional_rows = regional_result.get("regional_rows_by_region", {}).get(region_id, [])
        aviation_rows = regional_result.get("aviation_rows_by_region", {}).get(region_id, [])
        supply_rows = regional_result.get("supply_rows_by_region", {}).get(region_id, [])
        filename = f"r_{region_id}.json"
        chunk_payload = {
            "schemaVersion": GLOBAL_VIEWER_REGION_CHUNK_VERSION,
            "regionId": region_id,
            "regionalMacroRows": regional_rows,
            "aviationDemandRows": aviation_rows,
            "airCapacitySupplyRows": supply_rows,
        }
        raw = json.dumps(chunk_payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        atomic_write_text_file(chunk_dir / filename, raw.decode("utf-8"))
        regions.append(
            {
                "regionId": region_id,
                "regionName": REGION_CONFIGS[region_id].region_name,
                "regionalMacroRowCount": len(regional_rows),
                "aviationDemandRowCount": len(aviation_rows),
                "airCapacitySupplyRowCount": len(supply_rows),
                "file": filename,
                "sha256": hashlib.sha256(raw).hexdigest(),
                "bytes": len(raw),
            }
        )

    index = {
        "schemaVersion": GLOBAL_VIEWER_LAZY_INDEX_VERSION,
        "chunkSchemaVersion": GLOBAL_VIEWER_REGION_CHUNK_VERSION,
        "chunkBase": f"./{chunk_dir_name}/",
        "regions": regions,
    }
    index_json = json.dumps(index, ensure_ascii=False, separators=(",", ":"))
    index_script = (
        "(() => { const index = "
        + index_json
        + "; index.baseUrl = new URL(index.chunkBase, document.currentScript.src).href; "
        + "window.AIRPORT_GLOBAL_VIEWER_LAZY_INDEX = index; })();\n"
    )
    index_path = global_dir / "global_viewer_index.js"
    atomic_write_text_file(index_path, index_script)
    return {
        "index": str(index_path.as_posix()),
        "chunkDir": str(chunk_dir.as_posix()),
        "regionCount": len(regions),
        "chunkBytes": sum(int(region["bytes"]) for region in regions),
    }


def write_operations_viewer_lazy_assets(
    output_dir: Path,
    market_id: str,
    quarterly_rows: list[dict[str, Any]],
    financial_rows: list[dict[str, Any]],
    valuation_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    """Keep the default operations view in the core bundle and defer valuation rows."""
    output_dir.mkdir(parents=True, exist_ok=True)
    chunk_dir_name = f"{market_id}_operations_chunks"
    chunk_dir = output_dir / chunk_dir_name
    chunk_dir.mkdir(parents=True, exist_ok=True)

    filename = "d_valuation.json"
    chunk_payload = {
        "schemaVersion": OPERATIONS_VIEWER_CHUNK_VERSION,
        "datasetId": "valuation",
        "marketId": market_id,
        "rowCount": len(valuation_rows),
        "rows": valuation_rows,
    }
    raw = json.dumps(chunk_payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    atomic_write_text_file(chunk_dir / filename, raw.decode("utf-8"))
    index = {
        "schemaVersion": OPERATIONS_VIEWER_LAZY_INDEX_VERSION,
        "chunkSchemaVersion": OPERATIONS_VIEWER_CHUNK_VERSION,
        "marketId": market_id,
        "chunkBase": f"./{chunk_dir_name}/",
        "core": {
            "quarterlyOperationsRowCount": len(quarterly_rows),
            "financialStateRowCount": len(financial_rows),
        },
        "datasets": [
            {
                "datasetId": "valuation",
                "rowCount": len(valuation_rows),
                "file": filename,
                "sha256": hashlib.sha256(raw).hexdigest(),
                "bytes": len(raw),
            }
        ],
    }
    index_json = json.dumps(index, ensure_ascii=False, separators=(",", ":"))
    index_script = (
        "(() => { const index = "
        + index_json
        + "; index.baseUrl = new URL(index.chunkBase, document.currentScript.src).href; "
        + "window.AIRPORT_OPERATIONS_VIEWER_LAZY_INDEX = index; })();\n"
    )
    index_path = output_dir / f"{market_id}_operations_index.js"
    atomic_write_text_file(index_path, index_script)
    return {
        "index": str(index_path.as_posix()),
        "chunkDir": str(chunk_dir.as_posix()),
        "valuationRows": len(valuation_rows),
        "chunkBytes": len(raw),
    }


def load_city_configs_by_market(config_dir: Path, loader: Any) -> dict[str, dict[str, Any]]:
    configs: dict[str, dict[str, Any]] = {}
    for path in sorted(config_dir.glob("*.json")):
        config = loader(path)
        market_id = str(config.get("city_airport_market_id") or "").strip()
        if market_id:
            configs[market_id] = config
    return configs


def airport_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(AIRPORT_DIR).as_posix()
    except ValueError:
        return path.as_posix()


def to_float(value: Any, default: float = 0.0) -> float:
    if value in (None, ""):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def compact_float(value: Any, digits: int = 6) -> float:
    return round(to_float(value), digits)


def risk_list_from_row(row: dict[str, Any]) -> list[dict[str, Any]]:
    raw = row.get("branch_risk_watchlist")
    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, dict)]
    if not raw:
        return []
    try:
        parsed = json.loads(str(raw))
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [item for item in parsed if isinstance(item, dict)]


def risk_from_primary_fields(row: dict[str, Any]) -> dict[str, Any] | None:
    risk_id = str(row.get("branch_risk_primary_id") or "").strip()
    if not risk_id:
        return None
    return {
        "id": risk_id,
        "label": str(row.get("branch_risk_primary_label") or risk_id),
        "probability_pct": compact_float(row.get("branch_risk_primary_probability_pct")),
        "severity_index": compact_float(row.get("branch_risk_primary_severity_index")),
        "impact_years": int(to_float(row.get("branch_risk_primary_impact_years")) or 2),
        "tail_years": int(to_float(row.get("branch_risk_primary_tail_years")) or 1),
        "narrative": str(row.get("branch_risk_primary_narrative") or ""),
    }


def default_risk(branch_id: str) -> dict[str, Any]:
    profile = BRANCH_SCENARIO_PROFILES[branch_id]
    return {
        "id": branch_id,
        "label": str(profile.get("label") or branch_id),
        "probability_pct": 38.0,
        "severity_index": 0.78,
        "impact_years": 2,
        "tail_years": 2,
        "narrative": "",
    }


def normalize_risk(risk: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    source_branch_id = str(risk.get("id") or "").strip()
    branch_id = BRANCH_SCENARIO_ALIASES.get(source_branch_id, source_branch_id)
    if branch_id not in BRANCH_SCENARIO_PROFILES:
        branch_id = "credit_accident"
    normalized = dict(default_risk(branch_id))
    normalized.update({key: value for key, value in risk.items() if value not in (None, "")})
    normalized["id"] = branch_id
    if source_branch_id and source_branch_id != branch_id:
        normalized["source_id"] = source_branch_id
        if normalized.get("label"):
            normalized["source_label"] = normalized["label"]
        normalized["label"] = str(BRANCH_SCENARIO_PROFILES[branch_id]["label"])
    else:
        normalized["label"] = str(normalized.get("label") or BRANCH_SCENARIO_PROFILES[branch_id]["label"])
    normalized["probability_pct"] = compact_float(normalized.get("probability_pct", 38.0))
    normalized["severity_index"] = compact_float(normalized.get("severity_index", 0.78))
    normalized["impact_years"] = int(
        args.scenario_impact_years
        if args.scenario_impact_years is not None
        else max(1, to_float(normalized.get("impact_years", 2)))
    )
    normalized["tail_years"] = int(
        args.scenario_tail_years
        if args.scenario_tail_years is not None
        else max(0, to_float(normalized.get("tail_years", 2)))
    )
    return normalized


def risk_score(row: dict[str, Any], risk: dict[str, Any]) -> float:
    probability = to_float(risk.get("probability_pct"))
    severity = to_float(risk.get("severity_index"))
    year_index = to_float(row.get("year_index"))
    early_penalty = 0.82 if year_index <= 1 else 1.0
    return (probability * 0.015 + severity) * early_penalty


def select_trigger_row(rows: list[dict[str, Any]], args: argparse.Namespace) -> dict[str, Any]:
    if args.scenario_year_index is not None:
        target = max(0, min(int(args.scenario_year_index), len(rows) - 1))
        return rows[target]
    if args.scenario_year is not None:
        return min(rows, key=lambda row: abs(int(to_float(row.get("year"))) - args.scenario_year))

    candidates: list[tuple[float, dict[str, Any], dict[str, Any]]] = []
    for row in rows:
        primary = risk_from_primary_fields(row)
        if primary:
            candidates.append((risk_score(row, primary), row, primary))
        for risk in risk_list_from_row(row):
            candidates.append((risk_score(row, risk), row, risk))
    if candidates:
        _, row, _risk = max(candidates, key=lambda item: item[0])
        return row
    return rows[min(8, max(0, len(rows) - 1))]


def select_branch_scenario(rows: list[dict[str, Any]], args: argparse.Namespace) -> dict[str, Any]:
    row = select_trigger_row(rows, args)
    requested = str(args.scenario_branch_id or "auto").strip()
    requested = BRANCH_SCENARIO_ALIASES.get(requested, requested)

    if requested != "auto":
        if requested not in BRANCH_SCENARIO_PROFILES:
            valid = ", ".join(sorted(BRANCH_SCENARIO_PROFILES))
            raise ValueError(f"Unknown scenario branch id: {requested}. Valid ids: {valid}")
        selected = None
        for risk in [risk_from_primary_fields(row), *risk_list_from_row(row)]:
            if risk and str(risk.get("id")) == requested:
                selected = risk
                break
        risk = selected or default_risk(requested)
    else:
        risk = risk_from_primary_fields(row)
        if not risk:
            risks = risk_list_from_row(row)
            risk = max(risks, key=lambda item: risk_score(row, item)) if risks else default_risk("credit_accident")

    normalized = normalize_risk(risk, args)
    trigger_index = int(to_float(row.get("year_index")))
    return {
        "state": args.scenario_state,
        "trigger_index": trigger_index,
        "trigger_year": int(to_float(row.get("year"))),
        "risk": normalized,
        "source_row": {
            "year": row.get("year"),
            "year_index": row.get("year_index"),
            "branch_risk_count": row.get("branch_risk_count"),
            "branch_risk_primary_id": row.get("branch_risk_primary_id"),
        },
    }


def risks_for_row(row: dict[str, Any], args: argparse.Namespace) -> list[dict[str, Any]]:
    risks: list[dict[str, Any]] = []
    primary = risk_from_primary_fields(row)
    if primary:
        risks.append(primary)
    risks.extend(risk_list_from_row(row))
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for risk in risks:
        item = normalize_risk(risk, args)
        risk_id = str(item.get("id") or "")
        if risk_id and risk_id not in seen:
            normalized.append(item)
            seen.add(risk_id)
    return normalized


def normalized_severity_unit(risk: dict[str, Any]) -> float:
    severity = to_float(risk.get("severity_index"))
    if severity > 3.0:
        severity /= 100.0
    return clamp(severity, 0.0, 1.5)


def probabilistic_event_cap(args: argparse.Namespace) -> int:
    explicit = int(args.probabilistic_scenario_max_events or 0)
    if explicit > 0:
        return explicit
    return max(1, min(12, round(max(1, int(args.years)) / 15)))


def probabilistic_trigger_probability(risk: dict[str, Any], args: argparse.Namespace) -> float:
    probability = clamp(to_float(risk.get("probability_pct")) / 100.0, 0.0, 1.0)
    severity = normalized_severity_unit(risk)
    frequency = max(0.0, float(args.probabilistic_scenario_frequency))
    return clamp(probability * frequency * (0.75 + 0.50 * severity), 0.0, 0.24)


def selected_event_gap(selected: dict[str, Any], args: argparse.Namespace) -> int:
    risk = selected["risk"]
    return (
        max(1, int(risk.get("impact_years", 2)))
        + max(0, int(risk.get("tail_years", 2)))
        + max(0, int(args.probabilistic_scenario_cooldown_years))
    )


def overlaps_selected_events(
    trigger_index: int,
    selected_events: list[dict[str, Any]],
    args: argparse.Namespace,
    candidate_risk: dict[str, Any] | None = None,
) -> bool:
    candidate_gap = (
        selected_event_gap({"risk": candidate_risk}, args)
        if candidate_risk is not None
        else 0
    )
    for selected in selected_events:
        existing = int(selected["trigger_index"])
        if abs(trigger_index - existing) < max(selected_event_gap(selected, args), candidate_gap):
            return True
    return False


def select_probabilistic_branch_scenarios(
    rows: list[dict[str, Any]],
    args: argparse.Namespace,
    seed: int,
) -> list[dict[str, Any]]:
    rng = random.Random(f"{seed}:probabilistic_branch_timeline:{args.start_year}:{args.years}")
    max_events = probabilistic_event_cap(args)
    min_events = max(0, int(args.probabilistic_scenario_min_events))
    min_index = max(0, int(args.probabilistic_scenario_min_year_index))
    next_allowed_index = min_index
    selected_events: list[dict[str, Any]] = []
    fallback_candidates: list[tuple[float, dict[str, Any], dict[str, Any]]] = []

    for row in rows:
        year_index = int(to_float(row.get("year_index")))
        if year_index < min_index:
            continue
        risks = risks_for_row(row, args)
        if not risks:
            continue
        for risk in risks:
            fallback_candidates.append((risk_score(row, risk), row, risk))
        if year_index < next_allowed_index or len(selected_events) >= max_events:
            continue

        probabilities = [probabilistic_trigger_probability(risk, args) for risk in risks]
        no_event_probability = 1.0
        for probability in probabilities:
            no_event_probability *= 1.0 - probability
        trigger_probability = 1.0 - no_event_probability
        draw = rng.random()
        if draw >= trigger_probability:
            continue

        weight_total = sum(probabilities)
        threshold = rng.random() * weight_total if weight_total > 0 else 0.0
        running = 0.0
        chosen = risks[-1]
        chosen_probability = probabilities[-1] if probabilities else 0.0
        for risk, probability in zip(risks, probabilities):
            running += probability
            if threshold <= running:
                chosen = risk
                chosen_probability = probability
                break
        selected = {
            "state": "occurred",
            "trigger_index": year_index,
            "trigger_year": int(to_float(row.get("year"))),
            "risk": chosen,
            "selection_probability_pct": compact_float(trigger_probability * 100.0),
            "risk_draw_probability_pct": compact_float(chosen_probability * 100.0),
            "random_draw": compact_float(draw),
            "source_row": {
                "year": row.get("year"),
                "year_index": row.get("year_index"),
                "branch_risk_count": row.get("branch_risk_count"),
                "branch_risk_primary_id": row.get("branch_risk_primary_id"),
            },
        }
        selected_events.append(selected)
        next_allowed_index = year_index + selected_event_gap(selected, args)

    if len(selected_events) < min_events:
        for _score, row, risk in sorted(fallback_candidates, key=lambda item: item[0], reverse=True):
            if len(selected_events) >= min(min_events, max_events):
                break
            trigger_index = int(to_float(row.get("year_index")))
            if trigger_index < min_index or overlaps_selected_events(trigger_index, selected_events, args, risk):
                continue
            selected_events.append(
                {
                    "state": "occurred",
                    "trigger_index": trigger_index,
                    "trigger_year": int(to_float(row.get("year"))),
                    "risk": risk,
                    "selection_probability_pct": compact_float(
                        probabilistic_trigger_probability(risk, args) * 100.0
                    ),
                    "risk_draw_probability_pct": compact_float(
                        probabilistic_trigger_probability(risk, args) * 100.0
                    ),
                    "random_draw": None,
                    "forced_by_min_events": True,
                    "source_row": {
                        "year": row.get("year"),
                        "year_index": row.get("year_index"),
                        "branch_risk_count": row.get("branch_risk_count"),
                        "branch_risk_primary_id": row.get("branch_risk_primary_id"),
                    },
                }
            )

    return sorted(selected_events, key=lambda item: int(item["trigger_index"]))


def scenario_shape(offset: int, impact_years: int, tail_years: int) -> dict[str, Any]:
    if offset <= impact_years:
        progress = offset / max(1, impact_years)
        strength = 0.82 + 0.24 * (1.0 - abs(0.5 - progress) * 2.0)
        return {"phase": "impact", "strength": strength}
    tail_offset = offset - impact_years
    progress = tail_offset / max(1, tail_years + 1)
    strength = max(0.08, 0.52 * (1.0 - progress))
    return {"phase": "tail", "strength": strength}


def build_scenario_event_path(
    selected: dict[str, Any],
    max_year_index: int,
) -> dict[int, dict[str, Any]]:
    risk = selected["risk"]
    branch_id = str(risk["id"])
    profile = BRANCH_SCENARIO_PROFILES[branch_id]
    impact_years = max(1, int(risk.get("impact_years", 2)))
    tail_years = max(0, int(risk.get("tail_years", 2)))
    severity = clamp(
        0.62 * to_float(risk.get("severity_index")) + 0.006 * to_float(risk.get("probability_pct")),
        0.46,
        1.28,
    )
    trigger_index = int(selected["trigger_index"])
    trigger_year = int(selected["trigger_year"])
    event_path: dict[int, dict[str, Any]] = {}

    for offset in range(1, impact_years + tail_years + 1):
        target_index = trigger_index + offset
        if target_index > max_year_index:
            break
        shape = scenario_shape(offset, impact_years, tail_years)
        multiplier = severity * float(shape["strength"])
        phase = str(shape["phase"])
        feedback_source = f"branch_{branch_id}_{phase}_from_{trigger_year}"
        event_path[target_index] = {
            "feedback_growth_impulse_pct": compact_float(profile["growth"] * multiplier),
            "feedback_output_gap_impulse_pct": compact_float(profile["gap"] * multiplier),
            "feedback_financial_stress_impulse": compact_float(profile["stress"] * multiplier),
            "feedback_inflation_impulse_pct": compact_float(profile["inflation"] * multiplier),
            "feedback_policy_impulse_pct": compact_float(profile["policy"] * multiplier),
            "feedback_source": feedback_source,
            "scenario_feedback_source": feedback_source,
            "scenario_state": selected["state"],
            "scenario_risk_id": branch_id,
            "scenario_risk_label": str(risk.get("label") or profile["label"]),
            "scenario_trigger_index": trigger_index,
            "scenario_trigger_year": trigger_year,
            "scenario_impact_years": impact_years,
            "scenario_tail_years": tail_years,
            "scenario_phase": phase,
            "scenario_event_type": str(profile["event_type"]),
            "scenario_event_phase": str(profile["event_phase"]),
            "scenario_event_severity": compact_float(severity * float(shape["strength"])),
            "scenario_policy_rate_impulse": compact_float(profile["policy_rate"] * multiplier),
            "scenario_liquidity_impulse": compact_float(profile["liquidity"] * multiplier),
            "scenario_credit_stress_impulse": compact_float(profile["credit_stress"] * multiplier),
            "scenario_dollar_pressure_impulse": compact_float(profile["dollar"] * multiplier),
            "scenario_energy_price_impulse": compact_float(profile["energy"] * multiplier),
            "scenario_gdp_lagged_support": compact_float(profile["support"] * multiplier),
        }

    return event_path


def build_scenario_timeline_event_path(
    selected_events: list[dict[str, Any]],
    max_year_index: int,
) -> dict[int, dict[str, Any]]:
    event_path: dict[int, dict[str, Any]] = {}
    for selected in selected_events:
        for year_index, row in build_scenario_event_path(selected, max_year_index).items():
            if year_index not in event_path:
                event_path[year_index] = row
                continue
            merged = dict(event_path[year_index])
            for field in FEEDBACK_NUMERIC_FIELDS:
                merged[field] = compact_float(to_float(merged.get(field)) + to_float(row.get(field)))
            for field in (
                "scenario_policy_rate_impulse",
                "scenario_liquidity_impulse",
                "scenario_credit_stress_impulse",
                "scenario_dollar_pressure_impulse",
                "scenario_energy_price_impulse",
                "scenario_gdp_lagged_support",
            ):
                merged[field] = compact_float(to_float(merged.get(field)) + to_float(row.get(field)))
            merged["feedback_source"] = "+".join(
                item for item in [str(merged.get("feedback_source") or ""), str(row.get("feedback_source") or "")]
                if item
            )
            merged["scenario_feedback_source"] = "+".join(
                item
                for item in [
                    str(merged.get("scenario_feedback_source") or ""),
                    str(row.get("scenario_feedback_source") or ""),
                ]
                if item
            )
            merged["scenario_risk_id"] = "+".join(
                item for item in [str(merged.get("scenario_risk_id") or ""), str(row.get("scenario_risk_id") or "")]
                if item
            )
            merged["scenario_risk_label"] = "+".join(
                item
                for item in [
                    str(merged.get("scenario_risk_label") or ""),
                    str(row.get("scenario_risk_label") or ""),
                ]
                if item
            )
            merged["scenario_phase"] = "overlap"
            merged["scenario_event_type"] = "compound"
            merged["scenario_event_phase"] = "compound"
            merged["scenario_event_severity"] = max(
                to_float(merged.get("scenario_event_severity")),
                to_float(row.get("scenario_event_severity")),
            )
            event_path[year_index] = merged
    return event_path


def merge_feedback_paths(
    macro_feedback: dict[int, dict[str, Any]],
    scenario_feedback: dict[int, dict[str, Any]] | None,
) -> dict[int, dict[str, Any]]:
    merged: dict[int, dict[str, Any]] = {}
    keys = set(macro_feedback)
    if scenario_feedback:
        keys.update(scenario_feedback)

    for year_index in sorted(keys):
        row: dict[str, Any] = {}
        macro_row = macro_feedback.get(year_index, {})
        scenario_row = (scenario_feedback or {}).get(year_index, {})
        for field in FEEDBACK_NUMERIC_FIELDS:
            value = to_float(macro_row.get(field)) + to_float(scenario_row.get(field))
            if value:
                row[field] = compact_float(value)
        sources = [str(item) for item in (macro_row.get("feedback_source"), scenario_row.get("feedback_source")) if item]
        if sources:
            row["feedback_source"] = "+".join(dict.fromkeys(sources))
        for field in SCENARIO_FIELDS:
            if field in scenario_row:
                row[field] = scenario_row[field]
        merged[year_index] = row

    return merged


def apply_path_metadata(
    rows: list[dict[str, Any]],
    variant: str,
    scenario_feedback: dict[int, dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    output = []
    for row in rows:
        item = dict(row)
        item["global_path_variant"] = variant
        year_index = int(to_float(item.get("year_index")))
        scenario_row = (scenario_feedback or {}).get(year_index)
        if scenario_row:
            for field in SCENARIO_FIELDS:
                if field in scenario_row:
                    item[field] = scenario_row[field]
        output.append(item)
    return output


def run_global_variant(
    seed: int,
    args: argparse.Namespace,
    variant: str,
    scenario_feedback: dict[int, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    params = build_global_params(args)
    feedback_params = params["feedback_params"]
    macro_feedback: dict[int, dict[str, Any]] = {}
    combined_feedback = merge_feedback_paths(macro_feedback, scenario_feedback)

    records = run_full_chain(
        seed,
        gdp_params=params["gdp_params"],
        inflation_params=params["inflation_params"],
        policy_params=params["policy_params"],
        yield_curve_params=params["yield_curve_params"],
        dollar_liquidity_params=params["dollar_liquidity_params"],
        credit_spread_params=params["credit_spread_params"],
        asset_price_params=params["asset_price_params"],
        oil_commodity_params=params["oil_commodity_params"],
        feedback_path=combined_feedback if combined_feedback else None,
    )
    pass_records = [records]

    for _iteration in range(max(0, args.feedback_iterations)):
        derived = derive_feedback_path(records, feedback_params)
        macro_feedback = blend_feedback_paths(
            macro_feedback,
            derived,
            feedback_params.feedback_iteration_relaxation,
        )
        combined_feedback = merge_feedback_paths(macro_feedback, scenario_feedback)
        records = run_full_chain(
            seed,
            gdp_params=params["gdp_params"],
            inflation_params=params["inflation_params"],
            policy_params=params["policy_params"],
            yield_curve_params=params["yield_curve_params"],
            dollar_liquidity_params=params["dollar_liquidity_params"],
            credit_spread_params=params["credit_spread_params"],
            asset_price_params=params["asset_price_params"],
            oil_commodity_params=params["oil_commodity_params"],
            feedback_path=combined_feedback if combined_feedback else None,
        )
        pass_records.append(records)

    convergence = convergence_summary(pass_records, seed, feedback_params)
    annotated = annotate_feedback_records(
        records,
        combined_feedback,
        args.feedback_iterations,
        convergence,
    )
    annotated = apply_path_metadata(annotated, variant, scenario_feedback)
    return {
        "rows": [round_record(row) for row in annotated],
        "convergence": convergence,
        "params": params,
        "summary": summarize_seed(annotated),
    }


def run_regional_and_reconciliation(
    seed: int,
    global_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    regional_rows_by_region: dict[str, list[dict[str, Any]]] = {}
    regional_summaries: list[dict[str, Any]] = []
    for region_id in REGION_ORDER:
        rows = simulate_region_for_global_path(global_rows, REGION_CONFIGS[region_id], seed)
        rows = [round_record(row) for row in rows]
        regional_rows_by_region[region_id] = rows
        regional_summaries.append(summarize_region_seed(rows))

    global_by_key = {key_for(row): row for row in global_rows}
    reconciled_rows, diagnostics, reconciliation_summaries = build_reconciliation(
        REGION_ORDER,
        regional_rows_by_region,
        global_by_key,
    )
    rounded_reconciled_rows = [round_record(row) for row in reconciled_rows]
    aviation_rows_by_region: dict[str, list[dict[str, Any]]] = {}
    aviation_summaries: list[dict[str, Any]] = []
    for region_id, params in AVIATION_REGION_CONFIGS.items():
        merged_inputs = merge_region_inputs(
            region_id,
            regional_rows_by_region.get(region_id, []),
            rounded_reconciled_rows,
        )
        if not merged_inputs:
            continue
        aviation_rows = [
            round_record(row)
            for row in simulate_region_aviation_demand(merged_inputs, params)
        ]
        aviation_rows_by_region[region_id] = aviation_rows
        aviation_summaries.append(summarize_aviation_seed(aviation_rows))

    supply_rows_by_region: dict[str, list[dict[str, Any]]] = {}
    supply_summaries: list[dict[str, Any]] = []
    for region_id in REGION_ORDER:
        params = AIR_SUPPLY_REGION_CONFIGS.get(region_id)
        aviation_rows = aviation_rows_by_region.get(region_id, [])
        if params is None or not aviation_rows:
            continue
        supply_rows = [
            round_record(row)
            for row in simulate_region_air_supply(aviation_rows, params)
        ]
        supply_rows_by_region[region_id] = supply_rows
        supply_summaries.append(summarize_supply_seed(supply_rows))

    city_airport_rows_by_market: dict[str, list[dict[str, Any]]] = {}
    city_airport_summaries: list[dict[str, Any]] = []
    potential_passenger_forecast_configs_by_market = load_city_configs_by_market(
        POTENTIAL_PASSENGER_FORECAST_CONFIG_DIR,
        load_potential_passenger_forecast_config,
    )
    operations_configs_by_market = load_city_configs_by_market(
        QUARTERLY_OPERATIONS_CONFIG_DIR,
        load_quarterly_operations_config,
    )
    financial_configs_by_market = load_city_configs_by_market(
        FINANCIAL_STATE_CONFIG_DIR,
        load_financial_state_config,
    )
    valuation_configs_by_market = load_city_configs_by_market(
        VALUATION_FORECAST_CONFIG_DIR,
        load_valuation_forecast_config,
    )
    potential_passenger_forecast_rows_by_market: dict[str, list[dict[str, Any]]] = {}
    potential_passenger_forecast_summaries: dict[str, dict[str, Any]] = {}
    quarterly_operations_rows_by_market: dict[str, list[dict[str, Any]]] = {}
    quarterly_operations_summaries: dict[str, dict[str, Any]] = {}
    financial_state_rows_by_market: dict[str, list[dict[str, Any]]] = {}
    financial_state_summaries: dict[str, dict[str, Any]] = {}
    valuation_forecast_rows_by_market: dict[str, list[dict[str, Any]]] = {}
    valuation_forecast_summaries: dict[str, dict[str, Any]] = {}
    city_airport_downstream_skips: list[dict[str, Any]] = []
    for market_id, params in sorted(CITY_MARKET_CONFIGS.items()):
        aviation_rows = aviation_rows_by_region.get(params.region_id, [])
        supply_rows = supply_rows_by_region.get(params.region_id, [])
        regional_macro_rows = regional_rows_by_region.get(params.region_id, [])
        if not aviation_rows or not supply_rows:
            continue
        merged_city_inputs = merge_city_airport_inputs(
            params.region_id,
            aviation_rows,
            supply_rows,
            regional_macro_rows,
        )
        if not merged_city_inputs:
            continue
        city_rows = [
            round_record(row)
            for row in simulate_city_airport_demand(merged_city_inputs, params)
        ]
        if not city_rows:
            continue
        city_airport_rows_by_market[market_id] = city_rows
        for seed_value in sorted({int(to_float(row.get("seed"))) for row in city_rows}):
            seed_rows = [row for row in city_rows if int(to_float(row.get("seed"))) == seed_value]
            city_airport_summaries.append(summarize_city_airport_seed(seed_rows))

        potential_forecast_config = potential_passenger_forecast_configs_by_market.get(market_id)
        if potential_forecast_config is not None:
            potential_forecast_rows = [
                round_record(row)
                for row in simulate_potential_passenger_forecast(city_rows, potential_forecast_config)
            ]
            if potential_forecast_rows:
                potential_passenger_forecast_rows_by_market[market_id] = potential_forecast_rows
                potential_passenger_forecast_summaries[market_id] = summarize_potential_passenger_forecast(
                    potential_forecast_rows,
                    potential_forecast_config,
                )

        operations_config = operations_configs_by_market.get(market_id)
        if operations_config is None:
            city_airport_downstream_skips.append(
                {
                    "market": market_id,
                    "region": params.region_id,
                    "layer": "city_airport_quarterly_operations",
                    "reason": "missing_operations_config",
                }
            )
            continue
        operations_rows = [
            round_record(row)
            for row in simulate_quarterly_operations(city_rows, operations_config)
        ]
        if not operations_rows:
            city_airport_downstream_skips.append(
                {
                    "market": market_id,
                    "region": params.region_id,
                    "layer": "city_airport_quarterly_operations",
                    "reason": "no_operations_rows",
                }
            )
            continue
        quarterly_operations_rows_by_market[market_id] = operations_rows
        quarterly_operations_summaries[market_id] = summarize_quarterly_operations(
            operations_rows,
            operations_config,
        )

        financial_config = financial_configs_by_market.get(market_id)
        if financial_config is None:
            city_airport_downstream_skips.append(
                {
                    "market": market_id,
                    "region": params.region_id,
                    "layer": "city_airport_financial_state",
                    "reason": "missing_financial_config",
                }
            )
            continue
        financial_rows = [
            round_record(row)
            for row in simulate_financial_state(operations_rows, financial_config)
        ]
        if not financial_rows:
            city_airport_downstream_skips.append(
                {
                    "market": market_id,
                    "region": params.region_id,
                    "layer": "city_airport_financial_state",
                    "reason": "no_financial_rows",
                }
            )
            continue
        financial_state_rows_by_market[market_id] = financial_rows
        financial_state_summaries[market_id] = summarize_financial_state(
            financial_rows,
            financial_config,
        )

        valuation_config = valuation_configs_by_market.get(market_id)
        if valuation_config is None:
            city_airport_downstream_skips.append(
                {
                    "market": market_id,
                    "region": params.region_id,
                    "layer": "city_airport_valuation_forecast",
                    "reason": "missing_valuation_config",
                }
            )
            continue
        valuation_rows = [
            round_record(row)
            for row in simulate_valuation_forecast(operations_rows, financial_rows, valuation_config)
        ]
        if not valuation_rows:
            city_airport_downstream_skips.append(
                {
                    "market": market_id,
                    "region": params.region_id,
                    "layer": "city_airport_valuation_forecast",
                    "reason": "no_valuation_rows",
                }
            )
            continue
        valuation_forecast_rows_by_market[market_id] = valuation_rows
        valuation_forecast_summaries[market_id] = summarize_valuation_forecast(
            valuation_rows,
            valuation_config,
        )

    return {
        "regional_rows_by_region": regional_rows_by_region,
        "regional_summaries": regional_summaries,
        "reconciled_rows": rounded_reconciled_rows,
        "diagnostics": [round_record(row) for row in diagnostics],
        "reconciliation_summaries": reconciliation_summaries,
        "aviation_rows_by_region": aviation_rows_by_region,
        "aviation_summaries": aviation_summaries,
        "supply_rows_by_region": supply_rows_by_region,
        "supply_summaries": supply_summaries,
        "city_airport_rows_by_market": city_airport_rows_by_market,
        "city_airport_summaries": city_airport_summaries,
        "potential_passenger_forecast_rows_by_market": potential_passenger_forecast_rows_by_market,
        "potential_passenger_forecast_summaries": potential_passenger_forecast_summaries,
        "quarterly_operations_rows_by_market": quarterly_operations_rows_by_market,
        "quarterly_operations_summaries": quarterly_operations_summaries,
        "financial_state_rows_by_market": financial_state_rows_by_market,
        "financial_state_summaries": financial_state_summaries,
        "valuation_forecast_rows_by_market": valuation_forecast_rows_by_market,
        "valuation_forecast_summaries": valuation_forecast_summaries,
        "city_airport_downstream_skips": city_airport_downstream_skips,
    }


def write_variant_outputs(
    variant_dir: Path,
    seed: int,
    variant_name: str,
    global_result: dict[str, Any],
    regional_result: dict[str, Any],
    scenario: dict[str, Any] | None,
    artifact_profile: str = "full",
) -> None:
    write_viewer_artifacts = artifact_profile == "full"
    global_dir = variant_dir / "global_macro"
    regional_dir = variant_dir / "regional_macro"
    reconciled_dir = variant_dir / "regional_macro_reconciled"
    aviation_dir = variant_dir / "regional_aviation_demand"
    supply_dir = variant_dir / "regional_air_capacity_supply"
    city_airport_dir = variant_dir / "city_airport_market_demand"
    potential_passenger_forecast_dir = variant_dir / "city_airport_potential_passenger_forecast"
    quarterly_operations_dir = variant_dir / "city_airport_quarterly_operations"
    financial_state_dir = variant_dir / "city_airport_financial_state"
    valuation_forecast_dir = variant_dir / "city_airport_valuation"

    global_rows = global_result["rows"]
    write_csv_file(global_dir / "global_macro_feedback_seed_sweep.csv", global_rows, GLOBAL_OUTPUT_FIELDS)
    write_json_file(
        global_dir / "global_macro_feedback_seed_sweep_summary.json",
        {
            "orchestrator_version": ORCHESTRATOR_VERSION,
            "variant": variant_name,
            "seed": seed,
            "scenario": scenario,
            "params": {key: getattr(value, "__dict__", value) for key, value in global_result["params"].items()},
            "summaries": [global_result["summary"]],
            "convergence": [global_result["convergence"]],
        },
    )
    if write_viewer_artifacts:
        write_global_viewer_data_js(
            global_dir / "global_macro_feedback_viewer_data.js",
            global_rows,
        )

    for region_id in REGION_ORDER:
        rows = regional_result["regional_rows_by_region"][region_id]
        region_dir = regional_dir / region_id
        write_csv_file(region_dir / f"{region_id}_regional_macro_seed_sweep.csv", rows, REGIONAL_MACRO_FIELDS)
        write_json_file(
            region_dir / f"{region_id}_regional_macro_summary.json",
            {
                "orchestrator_version": ORCHESTRATOR_VERSION,
                "variant": variant_name,
                "region": region_id,
                "summaries": [
                    summary
                    for summary in regional_result["regional_summaries"]
                    if summary.get("region_id") == region_id
                ],
            },
        )
        if write_viewer_artifacts:
            write_regional_viewer_data_js(
                region_dir / f"{region_id}_regional_macro_viewer_data.js",
                rows,
            )

    write_csv_file(
        reconciled_dir / "regional_macro_reconciled_seed_sweep.csv",
        regional_result["reconciled_rows"],
        REGIONAL_VALUE_FIELDS,
    )
    write_csv_file(
        reconciled_dir / "regional_macro_reconciliation_seed_sweep.csv",
        regional_result["diagnostics"],
        DIAGNOSTIC_FIELDS,
    )
    write_json_file(
        reconciled_dir / "regional_macro_reconciliation_seed_sweep.json",
        {
            "orchestrator_version": ORCHESTRATOR_VERSION,
            "variant": variant_name,
            "seed": seed,
            "diagnostics": len(regional_result["diagnostics"]),
            "summaries": regional_result["reconciliation_summaries"],
        },
    )
    write_json_file(
        reconciled_dir / "regional_macro_reconciled_summary.json",
        {
            "orchestrator_version": ORCHESTRATOR_VERSION,
            "variant": variant_name,
            "seed": seed,
            "rows": len(regional_result["reconciled_rows"]),
            "diagnostics": len(regional_result["diagnostics"]),
            "summaries": regional_result["reconciliation_summaries"],
        },
    )
    if write_viewer_artifacts:
        write_reconciliation_viewer_js(
            reconciled_dir / "regional_macro_reconciled_viewer_data.js",
            regional_result["reconciled_rows"],
            regional_result["diagnostics"],
        )

    for region_id, rows in regional_result.get("aviation_rows_by_region", {}).items():
        region_dir = aviation_dir / region_id
        write_csv_file(region_dir / f"{region_id}_aviation_demand_seed_sweep.csv", rows, AVIATION_DEMAND_FIELDS)
        write_json_file(
            region_dir / f"{region_id}_aviation_demand_summary.json",
            {
                "orchestrator_version": ORCHESTRATOR_VERSION,
                "variant": variant_name,
                "region": region_id,
                "summaries": [
                    summary
                    for summary in regional_result.get("aviation_summaries", [])
                    if summary.get("region_id") == region_id
                ],
            },
        )
        if write_viewer_artifacts:
            write_aviation_viewer_data_js(
                region_dir / f"{region_id}_aviation_demand_viewer_data.js",
                rows,
            )

    for region_id, rows in regional_result.get("supply_rows_by_region", {}).items():
        region_dir = supply_dir / region_id
        write_csv_file(region_dir / f"{region_id}_air_capacity_supply_seed_sweep.csv", rows, AIR_SUPPLY_FIELDS)
        write_json_file(
            region_dir / f"{region_id}_air_capacity_supply_summary.json",
            {
                "orchestrator_version": ORCHESTRATOR_VERSION,
                "variant": variant_name,
                "region": region_id,
                "summaries": [
                    summary
                    for summary in regional_result.get("supply_summaries", [])
                    if summary.get("region_id") == region_id
                ],
            },
        )
        if write_viewer_artifacts:
            write_supply_viewer_data_js(
                region_dir / f"{region_id}_air_capacity_supply_viewer_data.js",
                rows,
            )

    if write_viewer_artifacts:
        write_global_viewer_lazy_assets(global_dir, regional_result)

    for market_id, rows in regional_result.get("city_airport_rows_by_market", {}).items():
        if not rows:
            continue
        region_id = str(rows[0].get("region_id") or "unknown_region")
        region_dir = city_airport_dir / region_id
        write_csv_file(region_dir / f"{market_id}_city_airport_demand_seed_sweep.csv", rows, CITY_AIRPORT_DEMAND_FIELDS)
        write_json_file(
            region_dir / f"{market_id}_city_airport_demand_summary.json",
            {
                "orchestrator_version": ORCHESTRATOR_VERSION,
                "variant": variant_name,
                "market": market_id,
                "region": region_id,
                "summaries": [
                    summary
                    for summary in regional_result.get("city_airport_summaries", [])
                    if summary.get("city_airport_market_id") == market_id
                ],
            },
        )
        if write_viewer_artifacts:
            write_city_airport_viewer_data_js(
                region_dir / f"{market_id}_city_airport_demand_viewer_data.js",
                rows,
            )

    for market_id, rows in regional_result.get("potential_passenger_forecast_rows_by_market", {}).items():
        if not rows:
            continue
        region_id = str(rows[0].get("region_id") or "unknown_region")
        region_dir = potential_passenger_forecast_dir / region_id
        summary = regional_result.get("potential_passenger_forecast_summaries", {}).get(market_id, {})
        write_csv_file(
            region_dir / f"{market_id}_potential_passenger_forecast_seed_sweep.csv",
            rows,
            POTENTIAL_PASSENGER_FORECAST_FIELDS,
        )
        write_json_file(
            region_dir / f"{market_id}_potential_passenger_forecast_summary.json",
            {
                "orchestrator_version": ORCHESTRATOR_VERSION,
                "variant": variant_name,
                "market": market_id,
                "region": region_id,
                "summary": summary,
            },
        )
        if write_viewer_artifacts:
            potential_forecast_config = load_city_configs_by_market(
                POTENTIAL_PASSENGER_FORECAST_CONFIG_DIR,
                load_potential_passenger_forecast_config,
            ).get(market_id, {})
            write_potential_passenger_forecast_viewer_data_js(
                region_dir / f"{market_id}_potential_passenger_forecast_viewer_data.js",
                rows,
                potential_forecast_config,
            )
            write_potential_passenger_forecast_lazy_assets(
                region_dir,
                rows,
                potential_forecast_config,
            )

    for market_id, rows in regional_result.get("quarterly_operations_rows_by_market", {}).items():
        if not rows:
            continue
        region_id = str(rows[0].get("region_id") or "unknown_region")
        region_dir = quarterly_operations_dir / region_id
        summary = regional_result.get("quarterly_operations_summaries", {}).get(market_id, {})
        write_csv_file(region_dir / f"{market_id}_quarterly_operations_seed_sweep.csv", rows, QUARTERLY_OPERATIONS_FIELDS)
        write_json_file(
            region_dir / f"{market_id}_quarterly_operations_summary.json",
            {
                "orchestrator_version": ORCHESTRATOR_VERSION,
                "variant": variant_name,
                "market": market_id,
                "region": region_id,
                "summary": summary,
            },
        )
        if write_viewer_artifacts:
            write_quarterly_operations_viewer_data_js(
                region_dir / f"{market_id}_quarterly_operations_viewer_data.js",
                rows,
            )

    for market_id, rows in regional_result.get("financial_state_rows_by_market", {}).items():
        if not rows:
            continue
        region_id = str(rows[0].get("region_id") or "unknown_region")
        region_dir = financial_state_dir / region_id
        summary = regional_result.get("financial_state_summaries", {}).get(market_id, {})
        write_csv_file(region_dir / f"{market_id}_financial_state_seed_sweep.csv", rows, FINANCIAL_STATE_FIELDS)
        write_json_file(
            region_dir / f"{market_id}_financial_state_summary.json",
            {
                "orchestrator_version": ORCHESTRATOR_VERSION,
                "variant": variant_name,
                "market": market_id,
                "region": region_id,
                "summary": summary,
            },
        )
        if write_viewer_artifacts:
            financial_config = load_city_configs_by_market(
                FINANCIAL_STATE_CONFIG_DIR,
                load_financial_state_config,
            ).get(market_id, {})
            write_financial_state_viewer_data_js(
                region_dir / f"{market_id}_financial_state_viewer_data.js",
                rows,
                financial_config,
            )

    for market_id, rows in regional_result.get("valuation_forecast_rows_by_market", {}).items():
        if not rows:
            continue
        region_id = str(rows[0].get("region_id") or "unknown_region")
        region_dir = valuation_forecast_dir / region_id
        summary = regional_result.get("valuation_forecast_summaries", {}).get(market_id, {})
        write_csv_file(region_dir / f"{market_id}_valuation_forecast_seed_sweep.csv", rows, VALUATION_FORECAST_FIELDS)
        write_json_file(
            region_dir / f"{market_id}_valuation_forecast_summary.json",
            {
                "orchestrator_version": ORCHESTRATOR_VERSION,
                "variant": variant_name,
                "market": market_id,
                "region": region_id,
                "summary": summary,
            },
        )
        if write_viewer_artifacts:
            valuation_config = load_city_configs_by_market(
                VALUATION_FORECAST_CONFIG_DIR,
                load_valuation_forecast_config,
            ).get(market_id, {})
            write_valuation_forecast_viewer_data_js(
                region_dir / f"{market_id}_valuation_forecast_viewer_data.js",
                rows,
                valuation_config,
            )

    if write_viewer_artifacts:
        for market_id, quarterly_rows in regional_result.get("quarterly_operations_rows_by_market", {}).items():
            if not quarterly_rows:
                continue
            region_id = str(quarterly_rows[0].get("region_id") or "unknown_region")
            write_operations_viewer_lazy_assets(
                quarterly_operations_dir / region_id,
                market_id,
                quarterly_rows,
                regional_result.get("financial_state_rows_by_market", {}).get(market_id, []),
                regional_result.get("valuation_forecast_rows_by_market", {}).get(market_id, []),
            )

    write_json_file(
        variant_dir / "city_airport_downstream_skips.json",
        {
            "orchestrator_version": ORCHESTRATOR_VERSION,
            "variant": variant_name,
            "skips": regional_result.get("city_airport_downstream_skips", []),
        },
    )


def active_scenario_rows(rows: list[dict[str, Any]]) -> int:
    return sum(1 for row in rows if row.get("scenario_risk_id") and row.get("scenario_state") in ("occurred", "counterfactual"))


def copy_files(source_dir: Path, target_dir: Path, pattern: str = "*") -> list[str]:
    target_dir.mkdir(parents=True, exist_ok=True)
    copied = []
    for source in sorted(source_dir.glob(pattern)):
        if not source.is_file():
            continue
        target = target_dir / source.name
        shutil.copy2(source, target)
        copied.append(str(target.as_posix()))
    return copied


def copy_tree_files(source_dir: Path, target_dir: Path) -> list[str]:
    copied: list[str] = []
    if not source_dir.is_dir():
        return copied
    for source in sorted(source_dir.rglob("*")):
        if not source.is_file():
            continue
        relative = source.relative_to(source_dir)
        target = target_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        copied.append(str(target.as_posix()))
    return copied


def copy_variant_to_legacy_viewer(variant_dir: Path, viewer_output_root: Path) -> list[str]:
    copied: list[str] = []
    global_source = variant_dir / "global_macro"
    global_target = viewer_output_root / "global_macro"
    global_index = global_source / "global_viewer_index.js"
    for source in sorted(global_source.glob("*")):
        if source.is_file() and source != global_index:
            target = global_target / source.name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            copied.append(str(target.as_posix()))
        elif source.is_dir() and source.name == "global_viewer_chunks":
            copied.extend(copy_tree_files(source, global_target / source.name))
    # The index is the compatibility pointer and must become visible after its chunks.
    if global_index.is_file():
        target = global_target / global_index.name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(global_index, target)
        copied.append(str(target.as_posix()))
    copied.extend(copy_files(variant_dir / "regional_macro_reconciled", viewer_output_root / "regional_macro_reconciled"))

    regional_target = viewer_output_root / "regional_macro"
    for region_dir in sorted((variant_dir / "regional_macro").glob("*")):
        if region_dir.is_dir():
            copied.extend(copy_files(region_dir, regional_target))

    aviation_target = viewer_output_root / "regional_aviation_demand"
    aviation_source = variant_dir / "regional_aviation_demand"
    if aviation_source.exists():
        for region_dir in sorted(aviation_source.glob("*")):
            if region_dir.is_dir():
                copied.extend(copy_files(region_dir, aviation_target))

    supply_target = viewer_output_root / "regional_air_capacity_supply"
    supply_source = variant_dir / "regional_air_capacity_supply"
    if supply_source.exists():
        for region_dir in sorted(supply_source.glob("*")):
            if region_dir.is_dir():
                copied.extend(copy_files(region_dir, supply_target))

    city_airport_target = viewer_output_root / "city_airport_market_demand"
    city_airport_source = variant_dir / "city_airport_market_demand"
    if city_airport_source.exists():
        for region_dir in sorted(city_airport_source.glob("*")):
            if region_dir.is_dir():
                copied.extend(copy_files(region_dir, city_airport_target / region_dir.name))

    potential_forecast_target = viewer_output_root / "city_airport_potential_passenger_forecast"
    potential_forecast_source = variant_dir / "city_airport_potential_passenger_forecast"
    if potential_forecast_source.exists():
        for region_dir in sorted(potential_forecast_source.glob("*")):
            if region_dir.is_dir():
                target_region_dir = potential_forecast_target / region_dir.name
                index_files = sorted(region_dir.glob("*_forecast_index.js"))
                for source in sorted(region_dir.glob("*")):
                    if source.is_file() and source not in index_files:
                        target = target_region_dir / source.name
                        target.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(source, target)
                        copied.append(str(target.as_posix()))
                    elif source.is_dir() and source.name.endswith("_forecast_chunks"):
                        copied.extend(copy_tree_files(source, target_region_dir / source.name))
                # The lightweight index is the compatibility pointer and is copied last.
                for source in index_files:
                    target = target_region_dir / source.name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, target)
                    copied.append(str(target.as_posix()))

    quarterly_operations_target = viewer_output_root / "city_airport_quarterly_operations"
    quarterly_operations_source = variant_dir / "city_airport_quarterly_operations"
    if quarterly_operations_source.exists():
        for region_dir in sorted(quarterly_operations_source.glob("*")):
            if region_dir.is_dir():
                target_region_dir = quarterly_operations_target / region_dir.name
                index_files = sorted(region_dir.glob("*_operations_index.js"))
                for source in sorted(region_dir.glob("*")):
                    if source.is_file() and source not in index_files:
                        target = target_region_dir / source.name
                        target.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(source, target)
                        copied.append(str(target.as_posix()))
                    elif source.is_dir() and source.name.endswith("_operations_chunks"):
                        copied.extend(copy_tree_files(source, target_region_dir / source.name))
                # Publish deferred datasets before switching the lightweight index pointer.
                for source in index_files:
                    target = target_region_dir / source.name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, target)
                    copied.append(str(target.as_posix()))

    financial_state_target = viewer_output_root / "city_airport_financial_state"
    financial_state_source = variant_dir / "city_airport_financial_state"
    if financial_state_source.exists():
        for region_dir in sorted(financial_state_source.glob("*")):
            if region_dir.is_dir():
                copied.extend(copy_files(region_dir, financial_state_target / region_dir.name))

    valuation_target = viewer_output_root / "city_airport_valuation"
    valuation_source = variant_dir / "city_airport_valuation"
    if valuation_source.exists():
        for region_dir in sorted(valuation_source.glob("*")):
            if region_dir.is_dir():
                copied.extend(copy_files(region_dir, valuation_target / region_dir.name))

    return copied


def viewer_script_source(path: Path, default_script: str) -> str:
    if not path.exists():
        return default_script.rstrip() + "\n"
    return path.read_text(encoding="utf-8").rstrip() + "\n"


def viewer_run_metadata(variant_dir: Path) -> dict[str, Any]:
    run_manifest_path = variant_dir.parent / "manifest.json"
    run_manifest: dict[str, Any] = {}
    if run_manifest_path.is_file():
        try:
            loaded = json.loads(run_manifest_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                run_manifest = loaded
        except (OSError, ValueError, json.JSONDecodeError):
            run_manifest = {}
    return {
        "seed": run_manifest.get("seed"),
        "start_year": run_manifest.get("start_year"),
        "years": run_manifest.get("years"),
        "model_version": str(run_manifest.get("model_version") or MODEL_VERSION),
        "output_schema_version": str(
            run_manifest.get("output_schema_version") or OUTPUT_SCHEMA_VERSION
        ),
    }


def viewer_release_info_script(release_id: str, variant_dir: Path) -> str:
    payload = json.dumps(
        {
            "schema_version": VIEWER_RELEASE_MANIFEST_VERSION,
            "release_id": release_id,
            "run_id": variant_dir.parent.name,
            "variant": variant_dir.name,
            **viewer_run_metadata(variant_dir),
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return f"window.AIRPORT_VIEWER_RELEASE_INFO = {payload};\n"


def build_global_viewer_bundle(variant_dir: Path, release_id: str) -> str:
    lazy_index = variant_dir / "global_macro" / "global_viewer_index.js"
    if lazy_index.exists():
        return "".join(
            [
                f"/* Atomic airport Viewer release: {release_id} */\n",
                viewer_script_source(
                    variant_dir / "global_macro" / "global_macro_feedback_viewer_data.js",
                    "window.GLOBAL_MACRO_FEEDBACK_DATA = [];",
                ),
                viewer_script_source(
                    variant_dir / "regional_macro_reconciled" / "regional_macro_reconciled_viewer_data.js",
                    "window.REGIONAL_MACRO_RECONCILED_DATA = [];\nwindow.REGIONAL_MACRO_RECONCILIATION_DATA = [];",
                ),
                viewer_script_source(lazy_index, "window.AIRPORT_GLOBAL_VIEWER_LAZY_INDEX = null;"),
                viewer_release_info_script(release_id, variant_dir),
            ]
        )

    parts = [
        f"/* Atomic airport Viewer release: {release_id} */\n",
        viewer_script_source(
            variant_dir / "global_macro" / "global_macro_feedback_viewer_data.js",
            "window.GLOBAL_MACRO_FEEDBACK_DATA = [];",
        ),
        "window.REGIONAL_MACRO_DATASETS = {};\n",
    ]
    for region_id in REGION_ORDER:
        parts.append("window.REGIONAL_MACRO_DATA = [];\n")
        parts.append(
            viewer_script_source(
                variant_dir / "regional_macro" / region_id / f"{region_id}_regional_macro_viewer_data.js",
                "window.REGIONAL_MACRO_DATA = [];",
            )
        )
        parts.append(
            f"window.REGIONAL_MACRO_DATASETS[{json.dumps(region_id)}] = window.REGIONAL_MACRO_DATA || [];\n"
        )

    parts.append(
        viewer_script_source(
            variant_dir / "regional_macro_reconciled" / "regional_macro_reconciled_viewer_data.js",
            "window.REGIONAL_MACRO_RECONCILED_DATA = [];\nwindow.REGIONAL_MACRO_RECONCILIATION_DATA = [];",
        )
    )
    parts.append("window.REGIONAL_AVIATION_DEMAND_DATASETS = {};\n")
    for region_id in REGION_ORDER:
        parts.append("window.REGIONAL_AVIATION_DEMAND_DATA = [];\n")
        parts.append(
            viewer_script_source(
                variant_dir
                / "regional_aviation_demand"
                / region_id
                / f"{region_id}_aviation_demand_viewer_data.js",
                "window.REGIONAL_AVIATION_DEMAND_DATA = [];",
            )
        )
        parts.append(
            "window.REGIONAL_AVIATION_DEMAND_DATASETS"
            f"[{json.dumps(region_id)}] = window.REGIONAL_AVIATION_DEMAND_DATA || [];\n"
        )

    parts.append("window.REGIONAL_AIR_CAPACITY_SUPPLY_DATASETS = {};\n")
    for region_id in REGION_ORDER:
        parts.append("window.REGIONAL_AIR_CAPACITY_SUPPLY_DATA = [];\n")
        parts.append(
            viewer_script_source(
                variant_dir
                / "regional_air_capacity_supply"
                / region_id
                / f"{region_id}_air_capacity_supply_viewer_data.js",
                "window.REGIONAL_AIR_CAPACITY_SUPPLY_DATA = [];",
            )
        )
        parts.append(
            "window.REGIONAL_AIR_CAPACITY_SUPPLY_DATASETS"
            f"[{json.dumps(region_id)}] = window.REGIONAL_AIR_CAPACITY_SUPPLY_DATA || [];\n"
        )
    parts.append(viewer_release_info_script(release_id, variant_dir))
    return "".join(parts)


def build_beijing_operations_viewer_bundle(variant_dir: Path, release_id: str) -> str:
    operations_dir = (
        variant_dir
        / "city_airport_quarterly_operations"
        / "china_mainland"
    )
    lazy_index = operations_dir / "beijing_airport_system_operations_index.js"
    parts = [
        f"/* Atomic airport Viewer release: {release_id} */\n",
        viewer_script_source(
            operations_dir
            / "beijing_airport_system_quarterly_operations_viewer_data.js",
            "window.CITY_AIRPORT_QUARTERLY_OPERATIONS_DATA = {rows: []};",
        ),
        viewer_script_source(
            variant_dir
            / "city_airport_financial_state"
            / "china_mainland"
            / "beijing_airport_system_financial_state_viewer_data.js",
            "window.CITY_AIRPORT_FINANCIAL_STATE_DATA = {rows: [], initial_assets: [], general_loans: []};",
        ),
    ]
    if lazy_index.exists():
        parts.append(viewer_script_source(lazy_index, "window.AIRPORT_OPERATIONS_VIEWER_LAZY_INDEX = null;"))
    else:
        parts.append(
            viewer_script_source(
                variant_dir
                / "city_airport_valuation"
                / "china_mainland"
                / "beijing_airport_system_valuation_forecast_viewer_data.js",
                "window.CITY_AIRPORT_VALUATION_FORECAST_DATA = {rows: []};",
            )
        )
    parts.append(viewer_release_info_script(release_id, variant_dir))
    return "".join(parts)


def build_beijing_forecast_viewer_bundle(variant_dir: Path, release_id: str) -> str:
    forecast_dir = (
        variant_dir
        / "city_airport_potential_passenger_forecast"
        / "china_mainland"
    )
    lazy_index = forecast_dir / "beijing_airport_system_forecast_index.js"
    if lazy_index.exists():
        data_script = viewer_script_source(
            lazy_index,
            "window.AIRPORT_FORECAST_LAZY_INDEX = null;",
        )
    else:
        data_script = viewer_script_source(
            forecast_dir / "beijing_airport_system_potential_passenger_forecast_viewer_data.js",
            "window.CITY_AIRPORT_POTENTIAL_PASSENGER_FORECAST_DATA = {config: {}, rows: []};",
        )
    return "".join(
        [
            f"/* Atomic airport Viewer release: {release_id} */\n",
            data_script,
            viewer_release_info_script(release_id, variant_dir),
        ]
    )


def write_viewer_release_bundles(variant_dir: Path, release_dir: Path, release_id: str) -> dict[str, str]:
    global_chunk_dir = variant_dir / "global_macro" / "global_viewer_chunks"
    if global_chunk_dir.is_dir():
        copy_tree_files(global_chunk_dir, release_dir / global_chunk_dir.name)

    operations_chunk_root = (
        variant_dir
        / "city_airport_quarterly_operations"
        / "china_mainland"
    )
    for chunk_dir in sorted(operations_chunk_root.glob("*_operations_chunks")):
        if chunk_dir.is_dir():
            copy_tree_files(chunk_dir, release_dir / chunk_dir.name)

    forecast_dir = (
        variant_dir
        / "city_airport_potential_passenger_forecast"
        / "china_mainland"
    )
    for chunk_dir in sorted(forecast_dir.glob("*_forecast_chunks")):
        if chunk_dir.is_dir():
            copy_tree_files(chunk_dir, release_dir / chunk_dir.name)

    bundles = {
        "global_gdp_viewer": ("global_gdp_viewer_bundle.js", build_global_viewer_bundle(variant_dir, release_id)),
        "beijing_airport_operations_viewer": (
            "beijing_airport_operations_viewer_bundle.js",
            build_beijing_operations_viewer_bundle(variant_dir, release_id),
        ),
        "beijing_potential_passenger_forecast_viewer": (
            "beijing_potential_passenger_forecast_viewer_bundle.js",
            build_beijing_forecast_viewer_bundle(variant_dir, release_id),
        ),
    }
    filenames: dict[str, str] = {}
    for viewer_id, (filename, content) in bundles.items():
        if not content.strip():
            raise ValueError(f"empty Viewer bundle for {viewer_id}")
        atomic_write_text_file(release_dir / filename, content)
        filenames[viewer_id] = filename
    return filenames


def viewer_script_url(path: Path) -> str:
    try:
        relative = path.resolve().relative_to(AIRPORT_DIR.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_uri()
    return f"./{relative}"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def publish_variant_to_viewer(variant_dir: Path, viewer_output_root: Path) -> dict[str, Any]:
    variant_dir = variant_dir.resolve()
    viewer_output_root = viewer_output_root.resolve()
    if not variant_dir.exists():
        raise FileNotFoundError(f"missing Viewer source variant: {variant_dir}")

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    unique_suffix = f"{time.time_ns() % 1_000_000_000:09d}"
    release_id = clean_run_id(f"{variant_dir.parent.name}_{variant_dir.name}_{timestamp}_{unique_suffix}")
    releases_root = viewer_output_root / "viewer_releases"
    staging_dir = releases_root / f".staging_{release_id}"
    release_dir = releases_root / release_id
    if staging_dir.exists() or release_dir.exists():
        raise FileExistsError(f"Viewer release already exists: {release_id}")

    releases_root.mkdir(parents=True, exist_ok=True)
    try:
        staging_dir.mkdir()
        bundle_filenames = write_viewer_release_bundles(variant_dir, staging_dir, release_id)
        bundle_hashes = {
            viewer_id: sha256_file(staging_dir / filename)
            for viewer_id, filename in bundle_filenames.items()
        }
        replace_directory_with_retry(staging_dir, release_dir)

        # Keep the established canonical output tree for compatibility with older pages/tools.
        canonical_copied = copy_variant_to_legacy_viewer(variant_dir, viewer_output_root)

        manifest = {
            "schema_version": VIEWER_RELEASE_MANIFEST_VERSION,
            "release_id": release_id,
            "run_id": variant_dir.parent.name,
            "variant": variant_dir.name,
            **viewer_run_metadata(variant_dir),
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "source_variant": airport_relative(variant_dir),
            "release_path": airport_relative(release_dir),
            "scripts": {
                viewer_id: viewer_script_url(release_dir / filename)
                for viewer_id, filename in bundle_filenames.items()
            },
            "bundle_sha256": bundle_hashes,
            "bundle_count": len(bundle_filenames),
            "canonical_copy_count": len(canonical_copied),
        }
        manifest_json_path = viewer_output_root / "current_viewer_manifest.json"
        manifest_js_path = viewer_output_root / "current_viewer_manifest.js"
        write_json_file(manifest_json_path, manifest)
        compact_manifest = json.dumps(manifest, ensure_ascii=False, separators=(",", ":"))
        # This JS pointer is the final atomic switch used by the static Viewer pages.
        atomic_write_text_file(
            manifest_js_path,
            f"window.AIRPORT_VIEWER_MANIFEST = {compact_manifest};\n",
        )
    except Exception:
        if staging_dir.exists() and staging_dir.parent.resolve() == releases_root.resolve():
            shutil.rmtree(staging_dir)
        raise

    return {
        "viewer_output_root": str(viewer_output_root.as_posix()),
        "copied_files": len(canonical_copied),
        "release_id": release_id,
        "release_path": airport_relative(release_dir),
        "release_manifest_json": airport_relative(manifest_json_path),
        "release_manifest_js": airport_relative(manifest_js_path),
        "bundle_count": len(bundle_filenames),
    }


def variant_label(variant_id: str, manifest: dict[str, Any]) -> str:
    if variant_id == "baseline":
        return "Baseline"
    scenario = manifest.get("scenario") if isinstance(manifest.get("scenario"), dict) else None
    if scenario and scenario.get("state") == "probabilistic":
        event_count = len(scenario.get("selected_events", [])) if isinstance(scenario.get("selected_events"), list) else 0
        return f"概率历史岔路: {event_count} events"
    selected = scenario.get("selected", {}) if scenario else {}
    risk = selected.get("risk", {}) if isinstance(selected.get("risk"), dict) else {}
    state = str(scenario.get("state") or "").strip() if scenario else ""
    label = str(risk.get("label") or risk.get("id") or "").strip()
    year = selected.get("trigger_year")
    if label and str(risk.get("id") or "") in variant_id:
        state_label = "发生" if state == "occurred" else "反事实" if state == "counterfactual" else state or "情景"
        return f"{state_label}: {label} {year}".strip()
    return variant_id.replace("_", " ")


def build_run_index(output_root: Path) -> dict[str, Any]:
    runs: list[dict[str, Any]] = []
    if output_root.exists():
        manifest_paths = sorted(
            (
                path
                for path in output_root.glob("*/manifest.json")
                if not path.parent.name.startswith(".staging_")
            ),
            key=lambda item: item.stat().st_mtime,
            reverse=True,
        )
        for manifest_path in manifest_paths:
            try:
                manifest = read_json_file(manifest_path)
            except (OSError, json.JSONDecodeError):
                continue
            run_dir = manifest_path.parent
            variants = []
            manifest_variants = manifest.get("variants", {})
            if isinstance(manifest_variants, dict):
                for variant_id, variant_meta in manifest_variants.items():
                    variant_dir = run_dir / variant_id
                    if not variant_dir.exists():
                        continue
                    meta = variant_meta if isinstance(variant_meta, dict) else {}
                    variants.append(
                        {
                            "id": variant_id,
                            "label": variant_label(variant_id, manifest),
                            "path": airport_relative(variant_dir),
                            "global_rows": meta.get("global_rows", 0),
                            "regional_rows": meta.get("regional_rows", 0),
                            "reconciled_rows": meta.get("reconciled_rows", 0),
                            "aviation_rows": meta.get("aviation_rows", 0),
                            "supply_rows": meta.get("supply_rows", 0),
                            "city_airport_rows": meta.get("city_airport_rows", 0),
                            "potential_passenger_forecast_rows": meta.get("potential_passenger_forecast_rows", 0),
                            "quarterly_operations_rows": meta.get("quarterly_operations_rows", 0),
                            "financial_state_rows": meta.get("financial_state_rows", 0),
                            "valuation_rows": meta.get("valuation_rows", 0),
                            "city_airport_downstream_skips": meta.get("city_airport_downstream_skips", 0),
                            "active_global_scenario_rows": meta.get("active_global_scenario_rows", 0),
                        }
                    )
            if not variants:
                continue
            runs.append(
                {
                    "id": str(manifest.get("run_id") or run_dir.name),
                    "label": str(manifest.get("run_id") or run_dir.name),
                    "seed": manifest.get("seed"),
                    "start_year": manifest.get("start_year"),
                    "years": manifest.get("years"),
                    "feedback_iterations": manifest.get("feedback_iterations"),
                    "path": airport_relative(run_dir),
                    "variants": variants,
                    "scenario": manifest.get("scenario"),
                    "published": manifest.get("published"),
                }
            )
    return {
        "version": RUN_INDEX_VERSION,
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "runs": runs,
    }


def write_run_index(output_root: Path) -> dict[str, Any]:
    output_root.mkdir(parents=True, exist_ok=True)
    payload = build_run_index(output_root)
    json_path = output_root / "macro_run_index.json"
    js_path = output_root / "macro_run_index.js"
    write_json_file(json_path, payload)
    js_payload = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    atomic_write_text_file(js_path, f"window.MACRO_RUN_INDEX = {js_payload};\n")
    return {
        "index_json": airport_relative(json_path),
        "index_js": airport_relative(js_path),
        "run_count": len(payload["runs"]),
    }


def csv_data_row_count(path: Path) -> int:
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        next(reader, None)
        return sum(1 for _ in reader)


def glob_csv_row_count(root: Path, pattern: str) -> int:
    return sum(csv_data_row_count(path) for path in root.glob(pattern) if path.is_file())


def inspect_staged_csv(
    path: Path,
    expected_seed: int,
    start_year: int,
    final_year: int,
) -> dict[str, Any]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        header = next(reader, None)
        if not header or any(not str(field).strip() for field in header):
            raise ValueError(f"staged CSV has an empty header: {path}")
        if len(header) != len(set(header)):
            raise ValueError(f"staged CSV has duplicate header fields: {path}")
        if "seed" not in header:
            raise ValueError(f"staged CSV is missing seed field: {path}")

        seed_index = header.index("seed")
        year_index = header.index("year") if "year" in header else None
        year_offset_index = header.index("year_index") if "year_index" in header else None
        region_index = header.index("region_id") if "region_id" in header else None
        regions: set[str] = set()
        row_count = 0
        for row_number, row in enumerate(reader, start=2):
            if len(row) != len(header):
                raise ValueError(
                    f"staged CSV row width mismatch at {path}:{row_number}: "
                    f"expected {len(header)}, got {len(row)}"
                )
            try:
                row_seed = int(float(row[seed_index]))
            except (TypeError, ValueError) as error:
                raise ValueError(f"staged CSV has invalid seed at {path}:{row_number}") from error
            if row_seed != expected_seed:
                raise ValueError(
                    f"staged CSV seed mismatch at {path}:{row_number}: "
                    f"expected {expected_seed}, got {row_seed}"
                )
            if year_index is not None:
                try:
                    row_year = int(float(row[year_index]))
                except (TypeError, ValueError) as error:
                    raise ValueError(f"staged CSV has invalid year at {path}:{row_number}") from error
                if row_year < start_year or row_year > final_year:
                    raise ValueError(
                        f"staged CSV year outside Run range at {path}:{row_number}: {row_year}"
                    )
            if year_offset_index is not None:
                try:
                    row_year_index = int(float(row[year_offset_index]))
                except (TypeError, ValueError) as error:
                    raise ValueError(f"staged CSV has invalid year_index at {path}:{row_number}") from error
                if row_year_index < 0 or row_year_index > final_year - start_year:
                    raise ValueError(
                        f"staged CSV year_index outside Run range at {path}:{row_number}: {row_year_index}"
                    )
            if region_index is not None and row[region_index]:
                regions.add(row[region_index])
            row_count += 1

    return {
        "row_count": row_count,
        "header": header,
        "regions": regions,
    }


def validate_staged_run(run_dir: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    variants = manifest.get("variants")
    if not isinstance(variants, dict) or not variants:
        raise ValueError("Run manifest has no variants")

    expected_seed = int(manifest["seed"])
    start_year = int(manifest["start_year"])
    final_year = start_year + int(manifest["years"])
    checks: dict[str, dict[str, int]] = {}
    file_counts: dict[str, dict[str, int]] = {}
    header_digests: dict[str, dict[str, str]] = {}
    region_coverage: dict[str, dict[str, list[str]]] = {}
    count_patterns = {
        "global_rows": "global_macro/global_macro_feedback_seed_sweep.csv",
        "regional_rows": "regional_macro/*/*_regional_macro_seed_sweep.csv",
        "reconciled_rows": "regional_macro_reconciled/regional_macro_reconciled_seed_sweep.csv",
        "aviation_rows": "regional_aviation_demand/*/*_aviation_demand_seed_sweep.csv",
        "supply_rows": "regional_air_capacity_supply/*/*_air_capacity_supply_seed_sweep.csv",
        "city_airport_rows": "city_airport_market_demand/*/*_city_airport_demand_seed_sweep.csv",
        "potential_passenger_forecast_rows": (
            "city_airport_potential_passenger_forecast/*/*_potential_passenger_forecast_seed_sweep.csv"
        ),
        "quarterly_operations_rows": "city_airport_quarterly_operations/*/*_quarterly_operations_seed_sweep.csv",
        "financial_state_rows": "city_airport_financial_state/*/*_financial_state_seed_sweep.csv",
        "valuation_rows": "city_airport_valuation/*/*_valuation_forecast_seed_sweep.csv",
    }
    full_region_fields = {"regional_rows", "reconciled_rows", "aviation_rows", "supply_rows"}
    for variant_id, raw_meta in variants.items():
        meta = raw_meta if isinstance(raw_meta, dict) else {}
        variant_dir = run_dir / str(variant_id)
        if not variant_dir.is_dir():
            raise FileNotFoundError(f"missing staged variant directory: {variant_dir}")
        skip_manifest = variant_dir / "city_airport_downstream_skips.json"
        if not skip_manifest.is_file():
            raise FileNotFoundError(f"missing staged downstream skip manifest: {skip_manifest}")
        variant_checks: dict[str, int] = {}
        variant_file_counts: dict[str, int] = {}
        variant_header_digests: dict[str, str] = {}
        variant_region_coverage: dict[str, list[str]] = {}
        for field, pattern in count_patterns.items():
            expected = int(meta.get(field, 0) or 0)
            paths = sorted(path for path in variant_dir.glob(pattern) if path.is_file())
            header_digest = hashlib.sha256()
            regions: set[str] = set()
            actual = 0
            for path in paths:
                inspection = inspect_staged_csv(path, expected_seed, start_year, final_year)
                actual += int(inspection["row_count"])
                regions.update(inspection["regions"])
                header_digest.update(path.relative_to(variant_dir).as_posix().encode("utf-8"))
                header_digest.update(b"\0")
                header_digest.update(",".join(inspection["header"]).encode("utf-8"))
                header_digest.update(b"\0")
            if actual != expected:
                raise ValueError(
                    f"staged row count mismatch for {variant_id}/{field}: expected {expected}, got {actual}"
                )
            if expected > 0 and field in full_region_fields and regions != set(REGION_ORDER):
                missing = sorted(set(REGION_ORDER) - regions)
                unexpected = sorted(regions - set(REGION_ORDER))
                raise ValueError(
                    f"staged region coverage mismatch for {variant_id}/{field}: "
                    f"missing={missing}, unexpected={unexpected}"
                )
            variant_checks[field] = actual
            variant_file_counts[field] = len(paths)
            variant_header_digests[field] = header_digest.hexdigest()
            if field in full_region_fields:
                variant_region_coverage[field] = sorted(regions)
        checks[str(variant_id)] = variant_checks
        file_counts[str(variant_id)] = variant_file_counts
        header_digests[str(variant_id)] = variant_header_digests
        region_coverage[str(variant_id)] = variant_region_coverage
    return {
        "schema_version": "airport-run-validation-v1",
        "validated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "variant_count": len(variants),
        "row_counts": checks,
        "file_counts": file_counts,
        "header_digests": header_digests,
        "region_coverage": region_coverage,
    }


def build_run_in_directory(
    args: argparse.Namespace,
    seed: int,
    run_id: str,
    run_dir: Path,
    final_run_dir: Path,
) -> dict[str, Any]:
    baseline_global = run_global_variant(seed, args, "baseline")
    baseline_regional = run_regional_and_reconciliation(seed, baseline_global["rows"])
    write_variant_outputs(
        run_dir / "baseline",
        seed,
        "baseline",
        baseline_global,
        baseline_regional,
        None,
        artifact_profile=getattr(args, "artifact_profile", "full"),
    )

    variants = {
        "baseline": {
            "path": str((final_run_dir / "baseline").as_posix()),
            "global_rows": len(baseline_global["rows"]),
            "regional_rows": sum(len(rows) for rows in baseline_regional["regional_rows_by_region"].values()),
            "reconciled_rows": len(baseline_regional["reconciled_rows"]),
            "aviation_rows": sum(len(rows) for rows in baseline_regional.get("aviation_rows_by_region", {}).values()),
            "supply_rows": sum(len(rows) for rows in baseline_regional.get("supply_rows_by_region", {}).values()),
            "city_airport_rows": sum(
                len(rows) for rows in baseline_regional.get("city_airport_rows_by_market", {}).values()
            ),
            "potential_passenger_forecast_rows": sum(
                len(rows) for rows in baseline_regional.get("potential_passenger_forecast_rows_by_market", {}).values()
            ),
            "quarterly_operations_rows": sum(
                len(rows) for rows in baseline_regional.get("quarterly_operations_rows_by_market", {}).values()
            ),
            "financial_state_rows": sum(
                len(rows) for rows in baseline_regional.get("financial_state_rows_by_market", {}).values()
            ),
            "valuation_rows": sum(
                len(rows) for rows in baseline_regional.get("valuation_forecast_rows_by_market", {}).values()
            ),
            "city_airport_downstream_skips": len(baseline_regional.get("city_airport_downstream_skips", [])),
        }
    }

    scenario_manifest = None
    scenario_variant_name = None
    if args.scenario_state != "none":
        if args.scenario_state == "probabilistic":
            selected_events = select_probabilistic_branch_scenarios(baseline_global["rows"], args, seed)
            scenario_feedback = build_scenario_timeline_event_path(selected_events, args.years)
            scenario_variant_name = clean_run_id(f"probabilistic_branch_timeline_{len(selected_events)}events")
            scenario_manifest = {
                "state": args.scenario_state,
                "selected_events": [
                    {key: value for key, value in selected.items() if key != "source_row"}
                    for selected in selected_events
                ],
                "source_rows": [selected["source_row"] for selected in selected_events],
                "event_year_indices": sorted(scenario_feedback),
            }
        else:
            selected = select_branch_scenario(baseline_global["rows"], args)
            scenario_feedback = build_scenario_event_path(selected, args.years)
            scenario_label = f"{args.scenario_state}_{selected['risk']['id']}_{selected['trigger_year']}"
            scenario_variant_name = clean_run_id(scenario_label)
            scenario_manifest = {
                "state": args.scenario_state,
                "selected": {
                    key: value for key, value in selected.items() if key != "source_row"
                },
                "source_row": selected["source_row"],
                "event_year_indices": sorted(scenario_feedback),
            }
        scenario_global = run_global_variant(
            seed,
            args,
            scenario_variant_name,
            scenario_feedback=scenario_feedback,
        )
        scenario_regional = run_regional_and_reconciliation(seed, scenario_global["rows"])
        scenario_manifest["active_global_rows"] = active_scenario_rows(scenario_global["rows"])
        write_variant_outputs(
            run_dir / scenario_variant_name,
            seed,
            scenario_variant_name,
            scenario_global,
            scenario_regional,
            scenario_manifest,
            artifact_profile=getattr(args, "artifact_profile", "full"),
        )
        variants[scenario_variant_name] = {
            "path": str((final_run_dir / scenario_variant_name).as_posix()),
            "global_rows": len(scenario_global["rows"]),
            "regional_rows": sum(len(rows) for rows in scenario_regional["regional_rows_by_region"].values()),
            "reconciled_rows": len(scenario_regional["reconciled_rows"]),
            "aviation_rows": sum(len(rows) for rows in scenario_regional.get("aviation_rows_by_region", {}).values()),
            "supply_rows": sum(len(rows) for rows in scenario_regional.get("supply_rows_by_region", {}).values()),
            "city_airport_rows": sum(
                len(rows) for rows in scenario_regional.get("city_airport_rows_by_market", {}).values()
            ),
            "potential_passenger_forecast_rows": sum(
                len(rows) for rows in scenario_regional.get("potential_passenger_forecast_rows_by_market", {}).values()
            ),
            "quarterly_operations_rows": sum(
                len(rows) for rows in scenario_regional.get("quarterly_operations_rows_by_market", {}).values()
            ),
            "financial_state_rows": sum(
                len(rows) for rows in scenario_regional.get("financial_state_rows_by_market", {}).values()
            ),
            "valuation_rows": sum(
                len(rows) for rows in scenario_regional.get("valuation_forecast_rows_by_market", {}).values()
            ),
            "city_airport_downstream_skips": len(scenario_regional.get("city_airport_downstream_skips", [])),
            "active_global_scenario_rows": active_scenario_rows(scenario_global["rows"]),
        }

    return {
        "schema_version": RUN_MANIFEST_SCHEMA_VERSION,
        "model_version": MODEL_VERSION,
        "output_schema_version": OUTPUT_SCHEMA_VERSION,
        "orchestrator_version": ORCHESTRATOR_VERSION,
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "artifact_profile": getattr(args, "artifact_profile", "full"),
        "run_id": run_id,
        "seed": seed,
        "start_year": args.start_year,
        "years": args.years,
        "feedback_iterations": args.feedback_iterations,
        "volatility_scale": args.volatility_scale,
        "initial_gdp": args.initial_gdp,
        "output_dir": str(final_run_dir.as_posix()),
        "variants": variants,
        "scenario": scenario_manifest,
        "scenario_variant": scenario_variant_name,
        "branch_scenario_profile_count": len(BRANCH_SCENARIO_PROFILES),
        "branch_scenario_profile_ids": sorted(BRANCH_SCENARIO_PROFILES),
        "published": None,
    }


def requested_publish_variant(args: argparse.Namespace, manifest: dict[str, Any]) -> str | None:
    if args.publish_viewer == "none":
        return None
    if args.publish_viewer == "baseline":
        return "baseline"
    scenario_variant = str(manifest.get("scenario_variant") or "").strip()
    if not scenario_variant:
        raise ValueError(
            "--publish-viewer scenario requires --scenario-state occurred, counterfactual, or probabilistic"
        )
    return scenario_variant


def execute_run(args: argparse.Namespace) -> dict[str, Any]:
    output_root = Path(args.output_root).resolve()
    if getattr(args, "artifact_profile", "full") != "full" and args.publish_viewer != "none":
        raise ValueError("--artifact-profile seed-cache cannot be combined with --publish-viewer")
    if args.index_only:
        return write_run_index(output_root)

    seed = resolve_seed(args)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    run_id = clean_run_id(args.run_id or f"run_{timestamp}_seed_{seed}")
    final_run_dir = output_root / run_id
    staging_dir = output_root / f".staging_{os.getpid()}_{time.time_ns():x}"
    output_root.mkdir(parents=True, exist_ok=True)
    if final_run_dir.exists():
        raise FileExistsError(f"Run already exists and will not be overwritten: {final_run_dir}")

    try:
        staging_dir.mkdir()
        manifest = build_run_in_directory(args, seed, run_id, staging_dir, final_run_dir)
        publish_name = requested_publish_variant(args, manifest)
        manifest["run_state"] = "staging"
        write_json_file(staging_dir / "manifest.json", manifest)
        manifest["validation"] = validate_staged_run(staging_dir, manifest)
        manifest["run_state"] = "complete"
        write_json_file(staging_dir / "manifest.json", manifest)
        replace_directory_with_retry(staging_dir, final_run_dir)
    except Exception:
        if staging_dir.exists() and staging_dir.parent.resolve() == output_root:
            shutil.rmtree(staging_dir)
        raise

    if publish_name is not None:
        manifest["published"] = {
            "variant": publish_name,
            **publish_variant_to_viewer(final_run_dir / publish_name, Path(args.viewer_output_root)),
        }
        write_json_file(final_run_dir / "manifest.json", manifest)

    manifest["run_index"] = write_run_index(output_root)
    write_json_file(final_run_dir / "manifest.json", manifest)
    return manifest


def main() -> None:
    manifest = execute_run(parse_args())
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
