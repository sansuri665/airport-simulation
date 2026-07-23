from __future__ import annotations

import argparse
import csv
import errno
import gzip
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

from airport_sim.server.serializers import (
    global_viewer_core_scripts,
    serialize_city_market_viewer_dataset,
    serialize_global_viewer_core,
    serialize_global_viewer_dataset,
    summarize_city,
)

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
run_index_service = _sibling_module("orchestrator_run_index")
run_lifecycle_service = _sibling_module("orchestrator_run_lifecycle")
run_validation_service = _sibling_module("orchestrator_run_validation")
variant_output_service = _sibling_module("orchestrator_variant_outputs")
viewer_assets_service = _sibling_module("orchestrator_viewer_assets")
viewer_release_service = _sibling_module("orchestrator_viewer_release")

FINANCIAL_STATE_CONFIG_DIR = financial_state_layer.DEFAULT_CONFIG_DIR
FINANCIAL_STATE_FIELDS = financial_state_layer.FINANCIAL_STATE_FIELDS
load_financial_state_config = financial_state_layer.load_config
simulate_financial_state = financial_state_layer.simulate_financial_state
summarize_financial_state = financial_state_layer.summarize

CITY_AIRPORT_DEMAND_FIELDS = city_market_layer.CITY_AIRPORT_DEMAND_FIELDS
CITY_MARKET_CONFIGS = city_market_layer.CITY_MARKET_CONFIGS
merge_city_airport_inputs = city_market_layer.merge_region_inputs
simulate_city_airport_demand = city_market_layer.simulate_city_airport_demand
summarize_city_airport_seed = city_market_layer.summarize_market_seed

POTENTIAL_PASSENGER_FORECAST_CONFIG_DIR = potential_forecast_layer.DEFAULT_CONFIG_DIR
POTENTIAL_PASSENGER_FORECAST_FIELDS = potential_forecast_layer.POTENTIAL_PASSENGER_FORECAST_FIELDS
load_potential_passenger_forecast_config = potential_forecast_layer.load_config
simulate_potential_passenger_forecast = potential_forecast_layer.simulate_potential_passenger_forecast
summarize_potential_passenger_forecast = potential_forecast_layer.summarize
write_potential_passenger_forecast_lazy_assets = potential_forecast_layer.write_viewer_lazy_assets

QUARTERLY_OPERATIONS_CONFIG_DIR = quarterly_operations_layer.DEFAULT_CONFIG_DIR
QUARTERLY_OPERATIONS_FIELDS = quarterly_operations_layer.QUARTERLY_OPERATIONS_FIELDS
load_quarterly_operations_config = quarterly_operations_layer.load_config
simulate_quarterly_operations = quarterly_operations_layer.simulate_quarterly_operations
summarize_quarterly_operations = quarterly_operations_layer.summarize

VALUATION_FORECAST_CONFIG_DIR = valuation_layer.DEFAULT_CONFIG_DIR
VALUATION_FORECAST_FIELDS = valuation_layer.VALUATION_FORECAST_FIELDS
load_valuation_forecast_config = valuation_layer.load_config
simulate_valuation_forecast = valuation_layer.simulate_valuation_forecast
summarize_valuation_forecast = valuation_layer.summarize

COMBINED_MACRO_FEEDBACK_FIELDS = global_feedback_layer.COMBINED_MACRO_FEEDBACK_FIELDS
MACRO_FEEDBACK_RAW_FIELDS = global_feedback_layer.MACRO_FEEDBACK_RAW_FIELDS
macro_feedback_intensity_from_applied = global_feedback_layer.macro_feedback_intensity_from_applied
annotate_feedback_records = global_feedback_layer.annotate_feedback_records
blend_feedback_paths = global_feedback_layer.blend_feedback_paths
convergence_summary = global_feedback_layer.convergence_summary
derive_feedback_path = global_feedback_layer.derive_feedback_path
run_convergence_aware_feedback_loop = global_feedback_layer.run_convergence_aware_feedback_loop
run_full_chain = global_feedback_layer.run_full_chain
summarize_seed = global_feedback_layer.summarize_seed

AIR_SUPPLY_FIELDS = air_supply_layer.AIR_SUPPLY_FIELDS
AIR_SUPPLY_REGION_CONFIGS = air_supply_layer.AIR_SUPPLY_REGION_CONFIGS
simulate_region_air_supply = air_supply_layer.simulate_region_air_supply
summarize_supply_seed = air_supply_layer.summarize_region_seed

AVIATION_DEMAND_FIELDS = aviation_demand_layer.AVIATION_DEMAND_FIELDS
AVIATION_REGION_CONFIGS = aviation_demand_layer.AVIATION_REGION_CONFIGS
merge_region_inputs = aviation_demand_layer.merge_region_inputs
simulate_region_aviation_demand = aviation_demand_layer.simulate_region_aviation_demand
summarize_aviation_seed = aviation_demand_layer.summarize_region_seed

REGION_CONFIGS = regional_macro_layer.REGION_CONFIGS
REGIONAL_MACRO_FIELDS = regional_macro_layer.REGIONAL_MACRO_FIELDS
build_global_params = regional_macro_layer.build_global_params
simulate_region_for_global_path = regional_macro_layer.simulate_region_for_global_path
summarize_region_seed = regional_macro_layer.summarize_region_seed

DIAGNOSTIC_FIELDS = reconciliation_layer.DIAGNOSTIC_FIELDS
REGION_ORDER = reconciliation_layer.REGION_ORDER
REGIONAL_VALUE_FIELDS = reconciliation_layer.REGIONAL_VALUE_FIELDS
build_reconciliation = reconciliation_layer.build_reconciliation
key_for = reconciliation_layer.key_for

clamp = simulation_utils.clamp
round_record = simulation_utils.round_record


ORCHESTRATOR_VERSION = "macro-run-orchestrator-v0.11"
RUN_INDEX_VERSION = "macro-run-index-v0.5"
RUN_MANIFEST_SCHEMA_VERSION = "airport-macro-run-manifest-v1"
OUTPUT_SCHEMA_VERSION = "airport-model-output-v5"
MODEL_VERSION = "airport-model-v0.15"
AIRPORT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_ROOT = AIRPORT_DIR / "output" / "macro_runs"
DEFAULT_VIEWER_OUTPUT_ROOT = AIRPORT_DIR / "output"
VIEWER_RELEASE_MANIFEST_VERSION = "airport-viewer-release-manifest-v2"
VIEWER_GZIP_SUFFIXES = frozenset({".js", ".json"})
VIEWER_GZIP_MIN_BYTES = 1024
VIEWER_GZIP_CHUNK_BYTES = 1024 * 1024
GLOBAL_VIEWER_LAZY_INDEX_VERSION = "airport-global-viewer-lazy-index-v2"
GLOBAL_VIEWER_REGION_CHUNK_VERSION = "airport-global-viewer-region-chunk-v2"
CITY_MARKET_VIEWER_LAZY_INDEX_VERSION = "airport-city-market-viewer-lazy-index-v2"
CITY_MARKET_VIEWER_CHUNK_VERSION = "airport-city-market-viewer-chunk-v2"
OPERATIONS_VIEWER_LAZY_INDEX_VERSION = "airport-operations-viewer-lazy-index-v1"
OPERATIONS_VIEWER_CHUNK_VERSION = "airport-operations-viewer-chunk-v1"

FEEDBACK_NUMERIC_FIELDS = (
    "feedback_growth_impulse_pct",
    "feedback_output_gap_impulse_pct",
    "feedback_financial_stress_impulse",
    "feedback_inflation_impulse_pct",
    "feedback_policy_impulse_pct",
)

# Macro feedback diagnostic fields carried alongside the applied impulses. The raw
# diagnostics describe the macro calibration layer's own measurement of stress; they
# are preserved verbatim from the macro feedback path and never blended with scenario
# impulses. The intensity index is recomputed from the merged macro-applied impulses
# (see merge_feedback_paths) rather than carried, so a scenario cannot masquerade as
# macro feedback intensity.
MACRO_FEEDBACK_INTENSITY_FIELD = "macro_feedback_intensity_index"

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
    parser.add_argument(
        "--feedback-iterations",
        type=int,
        default=16,
        help="Maximum feedback calibration reruns. The loop stops early once the convergence contract is met.",
    )
    parser.add_argument(
        "--min-feedback-iterations",
        type=int,
        default=3,
        help="Minimum feedback passes before the convergence check is applied.",
    )
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
    parser.add_argument("--index-only", action="store_true", help="Refresh macro_run_index.json without running simulation.")
    parser.add_argument(
        "--publish-viewer",
        choices=("none", "baseline", "scenario"),
        default="none",
        help="Also publish one variant as the current versioned Viewer Release under <airport>/output.",
    )
    parser.add_argument(
        "--viewer-output-root",
        type=Path,
        default=DEFAULT_VIEWER_OUTPUT_ROOT,
        help="Viewer Release publication root. Defaults to <airport>/output regardless of the current working directory.",
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


def write_global_viewer_data_js(path: Path, rows: list[dict[str, Any]]) -> None:
    core = serialize_global_viewer_core(rows, [], [])
    atomic_write_text_file(path, global_viewer_core_scripts(core)["global"])


def write_reconciliation_viewer_js(
    path: Path,
    regional_rows: list[dict[str, Any]],
    diagnostic_rows: list[dict[str, Any]],
) -> None:
    core = serialize_global_viewer_core([], regional_rows, diagnostic_rows)
    atomic_write_text_file(path, global_viewer_core_scripts(core)["reconciliation"])


def write_global_viewer_lazy_assets(
    global_dir: Path,
    regional_result: dict[str, Any],
) -> dict[str, Any]:
    """Publish one compact Viewer chunk per region without changing model rows."""
    global_dir.mkdir(parents=True, exist_ok=True)
    chunk_dir_name = "global_viewer_chunks"
    dataset = serialize_global_viewer_dataset(
        [
            (
                region_id,
                REGION_CONFIGS[region_id].region_name,
                regional_result.get("regional_rows_by_region", {}).get(region_id, []),
                regional_result.get("aviation_rows_by_region", {}).get(region_id, []),
                regional_result.get("supply_rows_by_region", {}).get(region_id, []),
            )
            for region_id in REGION_ORDER
        ],
        chunk_dir_name=chunk_dir_name,
    )
    chunk_dir = global_dir / chunk_dir_name
    chunk_dir.mkdir(parents=True, exist_ok=True)
    for serialized in dataset["chunks"].values():
        atomic_write_text_file(
            chunk_dir / serialized["filename"],
            serialized["raw"].decode("utf-8"),
        )

    index = dataset["index"]
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
        "regionCount": len(index["regions"]),
        "chunkBytes": sum(
            len(serialized["raw"])
            for serialized in dataset["chunks"].values()
        ),
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


def write_city_market_viewer_lazy_assets(
    market_dir: Path,
    output_dir: Path,
) -> dict[str, Any]:
    """Publish city demand/airline supply points without airport operations fields."""
    csv_paths = sorted(market_dir.glob("*_city_airport_demand_seed_sweep.csv"))
    if not csv_paths:
        raise FileNotFoundError(f"missing city market CSV files: {market_dir}")

    market_rows: list[tuple[str, list[dict[str, str]]]] = []
    for csv_path in csv_paths:
        with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        market_rows.append((str(csv_path), rows))
    if not any(rows for _, rows in market_rows):
        raise ValueError(f"city market CSV files contain no rows: {market_dir}")
    chunk_dir_name = "city_market_viewer_chunks"
    dataset = serialize_city_market_viewer_dataset(
        market_rows,
        chunk_dir_name=chunk_dir_name,
    )
    index = dataset["index"]
    chunk_dir = output_dir / chunk_dir_name
    chunk_dir.mkdir(parents=True, exist_ok=True)
    for serialized in dataset["chunks"].values():
        atomic_write_text_file(
            chunk_dir / serialized["filename"],
            serialized["raw"].decode("utf-8"),
        )
    index_json = json.dumps(index, ensure_ascii=False, separators=(",", ":"))
    index_script = (
        "(() => { const index = "
        + index_json
        + "; index.baseUrl = new URL(index.chunkBase, document.currentScript.src).href; "
        + "window.AIRPORT_CITY_MARKET_VIEWER_INDEX = index; })();\n"
    )
    index_path = output_dir / "city_market_viewer_index.js"
    atomic_write_text_file(index_path, index_script)
    return {
        "index": index_path,
        "chunkDir": chunk_dir,
        "cityCount": int(index["cityCount"]),
        "chunkBytes": sum(
            len(serialized["raw"])
            for serialized in dataset["chunks"].values()
        ),
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

        # Applied impulses are additive: the final run receives macro feedback plus
        # any active scenario branch impulse. Keep both the macro-only and the
        # merged totals so downstream intensity can be recomputed from macro alone.
        macro_growth_applied = to_float(macro_row.get("feedback_growth_impulse_pct"))
        macro_stress_applied = to_float(macro_row.get("feedback_financial_stress_impulse"))
        macro_inflation_applied = to_float(macro_row.get("feedback_inflation_impulse_pct"))
        macro_policy_applied = to_float(macro_row.get("feedback_policy_impulse_pct"))
        for field in FEEDBACK_NUMERIC_FIELDS:
            value = to_float(macro_row.get(field)) + to_float(scenario_row.get(field))
            if value:
                row[field] = compact_float(value)

        sources = [str(item) for item in (macro_row.get("feedback_source"), scenario_row.get("feedback_source")) if item]
        if sources:
            row["feedback_source"] = "+".join(dict.fromkeys(sources))

        # Macro raw diagnostics describe the calibration layer's own measurement of
        # macro stress. Preserve them verbatim from the macro path; never let a
        # scenario impulse masquerade as a macro raw value. Years without macro
        # feedback keep zero raw values, matching annotate_feedback_records.
        for field in MACRO_FEEDBACK_RAW_FIELDS:
            row[field] = compact_float(to_float(macro_row.get(field)))

        # The intensity index is recomputed from the final applied macro impulses
        # (macro-only, not scenario) so it reflects how active macro feedback is,
        # not how loud an overlaid scenario branch is.
        row[MACRO_FEEDBACK_INTENSITY_FIELD] = compact_float(
            macro_feedback_intensity_from_applied(
                macro_growth_applied,
                macro_stress_applied,
                macro_inflation_applied,
                macro_policy_applied,
            )
        )

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
    feedback_iterations = int(params["feedback_iterations"])

    # Pass 0 has no derived macro feedback yet, but an active scenario path is
    # already present. Every later pass keeps the same scenario impulses and
    # adds the newly solved macro feedback, preserving the historical scenario
    # merge semantics while the shared solver controls only the macro path.
    combined_feedback = merge_feedback_paths({}, scenario_feedback)
    initial_records = run_full_chain(
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

    def run_pass(macro_feedback: dict[int, dict[str, Any]], _iteration: int) -> list[dict[str, Any]]:
        # Merge the macro feedback with any active scenario branch impulses
        # before rerunning the chain. The helper owns the macro blend; this
        # callable owns the scenario merge so the convergence contract is
        # evaluated on the same combined path the Viewer will read.
        merged = merge_feedback_paths(macro_feedback, scenario_feedback)
        return run_full_chain(
            seed,
            gdp_params=params["gdp_params"],
            inflation_params=params["inflation_params"],
            policy_params=params["policy_params"],
            yield_curve_params=params["yield_curve_params"],
            dollar_liquidity_params=params["dollar_liquidity_params"],
            credit_spread_params=params["credit_spread_params"],
            asset_price_params=params["asset_price_params"],
            oil_commodity_params=params["oil_commodity_params"],
            feedback_path=merged if merged else None,
        )

    records, macro_feedback, convergence = run_convergence_aware_feedback_loop(
        seed=seed,
        feedback_params=feedback_params,
        initial_records=initial_records,
        run_pass=run_pass,
        min_iterations=getattr(args, "min_feedback_iterations", None),
        max_iterations=max(1, feedback_iterations),
    )

    combined_feedback = merge_feedback_paths(macro_feedback, scenario_feedback)
    annotated = annotate_feedback_records(
        records,
        combined_feedback,
        feedback_iterations,
        convergence,
    )
    annotated = apply_path_metadata(annotated, variant, scenario_feedback)
    public_convergence = dict(convergence)
    public_convergence.pop("row_convergence_annotations", None)
    return {
        "rows": [round_record(row) for row in annotated],
        "convergence": public_convergence,
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
    dependencies = variant_output_service.VariantOutputDependencies(
        orchestrator_version=ORCHESTRATOR_VERSION,
        region_order=REGION_ORDER,
        global_output_fields=GLOBAL_OUTPUT_FIELDS,
        regional_macro_fields=REGIONAL_MACRO_FIELDS,
        regional_value_fields=REGIONAL_VALUE_FIELDS,
        diagnostic_fields=DIAGNOSTIC_FIELDS,
        aviation_demand_fields=AVIATION_DEMAND_FIELDS,
        air_supply_fields=AIR_SUPPLY_FIELDS,
        city_airport_demand_fields=CITY_AIRPORT_DEMAND_FIELDS,
        potential_passenger_forecast_fields=POTENTIAL_PASSENGER_FORECAST_FIELDS,
        quarterly_operations_fields=QUARTERLY_OPERATIONS_FIELDS,
        financial_state_fields=FINANCIAL_STATE_FIELDS,
        valuation_forecast_fields=VALUATION_FORECAST_FIELDS,
        potential_passenger_forecast_config_dir=POTENTIAL_PASSENGER_FORECAST_CONFIG_DIR,
        load_potential_passenger_forecast_config=load_potential_passenger_forecast_config,
        write_csv_file=write_csv_file,
        write_json_file=write_json_file,
        write_global_viewer_data_js=write_global_viewer_data_js,
        write_reconciliation_viewer_js=write_reconciliation_viewer_js,
        write_global_viewer_lazy_assets=write_global_viewer_lazy_assets,
        load_city_configs_by_market=load_city_configs_by_market,
        write_potential_passenger_forecast_lazy_assets=(
            write_potential_passenger_forecast_lazy_assets
        ),
        write_operations_viewer_lazy_assets=write_operations_viewer_lazy_assets,
    )
    variant_output_service.write_variant_outputs(
        variant_dir,
        seed,
        variant_name,
        global_result,
        regional_result,
        scenario,
        artifact_profile=artifact_profile,
        dependencies=dependencies,
    )


def active_scenario_rows(rows: list[dict[str, Any]]) -> int:
    return sum(1 for row in rows if row.get("scenario_risk_id") and row.get("scenario_state") in ("occurred", "counterfactual"))


def copy_files(source_dir: Path, target_dir: Path, pattern: str = "*") -> list[str]:
    return viewer_assets_service.copy_files(
        source_dir,
        target_dir,
        pattern,
        copy_file=shutil.copy2,
    )


def copy_tree_files(source_dir: Path, target_dir: Path) -> list[str]:
    return viewer_assets_service.copy_tree_files(
        source_dir,
        target_dir,
        copy_file=shutil.copy2,
    )


def sync_variant_downstream_csv(variant_dir: Path, output_root: Path) -> list[str]:
    return viewer_assets_service.sync_variant_downstream_csv(
        variant_dir,
        output_root,
        copy_file=shutil.copy2,
        copy_files=copy_files,
    )


def viewer_script_source(path: Path, default_script: str) -> str:
    return viewer_assets_service.viewer_script_source(path, default_script)


def viewer_run_metadata(variant_dir: Path) -> dict[str, Any]:
    return viewer_assets_service.viewer_run_metadata(
        variant_dir,
        model_version=MODEL_VERSION,
        output_schema_version=OUTPUT_SCHEMA_VERSION,
    )


def viewer_release_info_script(release_id: str, variant_dir: Path) -> str:
    return viewer_assets_service.viewer_release_info_script(
        release_id,
        variant_dir,
        manifest_version=VIEWER_RELEASE_MANIFEST_VERSION,
        viewer_run_metadata=viewer_run_metadata,
    )


def build_global_viewer_bundle(variant_dir: Path, release_id: str) -> str:
    return viewer_assets_service.build_global_viewer_bundle(
        variant_dir,
        release_id,
        viewer_script_source=viewer_script_source,
        viewer_release_info_script=viewer_release_info_script,
    )


def build_city_market_viewer_bundle(index_path: Path, variant_dir: Path, release_id: str) -> str:
    return viewer_assets_service.build_city_market_viewer_bundle(
        index_path,
        variant_dir,
        release_id,
        viewer_script_source=viewer_script_source,
        viewer_release_info_script=viewer_release_info_script,
    )


def build_beijing_forecast_viewer_bundle(variant_dir: Path, release_id: str) -> str:
    return viewer_assets_service.build_beijing_forecast_viewer_bundle(
        variant_dir,
        release_id,
        viewer_script_source=viewer_script_source,
        viewer_release_info_script=viewer_release_info_script,
    )


def write_viewer_release_bundles(variant_dir: Path, release_dir: Path, release_id: str) -> dict[str, str]:
    return viewer_release_service.write_viewer_release_bundles(
        variant_dir,
        release_dir,
        release_id,
        copy_tree_files=copy_tree_files,
        write_city_market_viewer_lazy_assets=write_city_market_viewer_lazy_assets,
        copy_file=shutil.copy2,
        build_global_viewer_bundle=build_global_viewer_bundle,
        build_city_market_viewer_bundle=build_city_market_viewer_bundle,
        build_beijing_forecast_viewer_bundle=build_beijing_forecast_viewer_bundle,
        atomic_write_text_file=atomic_write_text_file,
    )


def viewer_script_url(path: Path) -> str:
    return viewer_assets_service.viewer_script_url(path, airport_dir=AIRPORT_DIR)


def sha256_file(path: Path) -> str:
    return viewer_assets_service.sha256_file(path)


def write_viewer_gzip_sidecar(path: Path) -> tuple[int, int]:
    return viewer_assets_service.write_viewer_gzip_sidecar(
        path,
        gzip_module=gzip,
        replace_file=os.replace,
        chunk_bytes=VIEWER_GZIP_CHUNK_BYTES,
    )


def write_viewer_release_gzip_sidecars(release_dir: Path) -> dict[str, int]:
    return viewer_assets_service.write_viewer_release_gzip_sidecars(
        release_dir,
        suffixes=VIEWER_GZIP_SUFFIXES,
        min_bytes=VIEWER_GZIP_MIN_BYTES,
        write_viewer_gzip_sidecar=write_viewer_gzip_sidecar,
    )


def publish_variant_to_viewer(variant_dir: Path, viewer_output_root: Path) -> dict[str, Any]:
    return viewer_release_service.publish_variant_to_viewer(
        variant_dir,
        viewer_output_root,
        time_module=time,
        clean_run_id=clean_run_id,
        write_viewer_release_bundles=write_viewer_release_bundles,
        sha256_file=sha256_file,
        write_viewer_release_gzip_sidecars=write_viewer_release_gzip_sidecars,
        replace_directory_with_retry=replace_directory_with_retry,
        sync_variant_downstream_csv=sync_variant_downstream_csv,
        manifest_version=VIEWER_RELEASE_MANIFEST_VERSION,
        viewer_run_metadata=viewer_run_metadata,
        airport_relative=airport_relative,
        viewer_script_url=viewer_script_url,
        write_json_file=write_json_file,
        atomic_write_text_file=atomic_write_text_file,
        remove_tree=shutil.rmtree,
    )


def variant_label(variant_id: str, manifest: dict[str, Any]) -> str:
    return run_index_service.variant_label(variant_id, manifest)


def build_run_index(output_root: Path) -> dict[str, Any]:
    return run_index_service.build_run_index(
        output_root,
        version=RUN_INDEX_VERSION,
        time_module=time,
        read_json_file=read_json_file,
        variant_label=variant_label,
        airport_relative=airport_relative,
    )


def write_run_index(output_root: Path) -> dict[str, Any]:
    return run_index_service.write_run_index(
        output_root,
        build_run_index=build_run_index,
        write_json_file=write_json_file,
        airport_relative=airport_relative,
    )


def csv_data_row_count(path: Path) -> int:
    return run_validation_service.csv_data_row_count(path, csv_module=csv)


def glob_csv_row_count(root: Path, pattern: str) -> int:
    return run_validation_service.glob_csv_row_count(
        root,
        pattern,
        csv_data_row_count=csv_data_row_count,
    )


def inspect_staged_csv(
    path: Path,
    expected_seed: int,
    start_year: int,
    final_year: int,
) -> dict[str, Any]:
    return run_validation_service.inspect_staged_csv(
        path,
        expected_seed,
        start_year,
        final_year,
        csv_module=csv,
    )


def validate_staged_run(run_dir: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    return run_validation_service.validate_staged_run(
        run_dir,
        manifest,
        region_order=REGION_ORDER,
        inspect_staged_csv=inspect_staged_csv,
        hashlib_module=hashlib,
        time_module=time,
    )


def write_validated_run_manifest(
    run_dir: Path,
    manifest: dict[str, Any],
) -> dict[str, Any]:
    return run_validation_service.write_validated_run_manifest(
        run_dir,
        manifest,
        write_json_file=write_json_file,
        validate_staged_run=validate_staged_run,
    )


def build_variant_manifest(
    final_run_dir: Path,
    variant_name: str,
    global_result: dict[str, Any],
    regional_result: dict[str, Any],
    *,
    active_global_scenario_rows: int | None = None,
) -> dict[str, Any]:
    return run_validation_service.build_variant_manifest(
        final_run_dir,
        variant_name,
        global_result,
        regional_result,
        active_global_scenario_rows=active_global_scenario_rows,
    )


def build_run_manifest(
    args: argparse.Namespace,
    seed: int,
    run_id: str,
    final_run_dir: Path,
    variants: dict[str, dict[str, Any]],
    scenario_manifest: dict[str, Any] | None,
    scenario_variant_name: str | None,
) -> dict[str, Any]:
    return run_validation_service.build_run_manifest(
        args,
        seed,
        run_id,
        final_run_dir,
        variants,
        scenario_manifest,
        scenario_variant_name,
        schema_version=RUN_MANIFEST_SCHEMA_VERSION,
        model_version=MODEL_VERSION,
        output_schema_version=OUTPUT_SCHEMA_VERSION,
        orchestrator_version=ORCHESTRATOR_VERSION,
        platform_module=platform,
        branch_profiles=BRANCH_SCENARIO_PROFILES,
    )


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
        "baseline": build_variant_manifest(
            final_run_dir,
            "baseline",
            baseline_global,
            baseline_regional,
        )
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
        variants[scenario_variant_name] = build_variant_manifest(
            final_run_dir,
            scenario_variant_name,
            scenario_global,
            scenario_regional,
            active_global_scenario_rows=active_scenario_rows(
                scenario_global["rows"]
            ),
        )

    return build_run_manifest(
        args,
        seed,
        run_id,
        final_run_dir,
        variants,
        scenario_manifest,
        scenario_variant_name,
    )


def requested_publish_variant(args: argparse.Namespace, manifest: dict[str, Any]) -> str | None:
    return run_validation_service.requested_publish_variant(args, manifest)


def execute_run(args: argparse.Namespace) -> dict[str, Any]:
    return run_lifecycle_service.execute_run(
        args,
        dependencies=run_lifecycle_service.RunLifecycleDependencies(
            time_module=time,
            process_id=os.getpid,
            resolve_path=lambda path: path.resolve(),
            resolve_seed=resolve_seed,
            clean_run_id=clean_run_id,
            write_run_index=write_run_index,
            build_run_in_directory=build_run_in_directory,
            requested_publish_variant=requested_publish_variant,
            write_validated_run_manifest=write_validated_run_manifest,
            replace_directory_with_retry=replace_directory_with_retry,
            remove_tree=shutil.rmtree,
            publish_variant_to_viewer=publish_variant_to_viewer,
            write_json_file=write_json_file,
        ),
    )


def main() -> None:
    manifest = execute_run(parse_args())
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
