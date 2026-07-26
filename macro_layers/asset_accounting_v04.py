from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from typing import Any, Mapping


ASSET_ACCOUNTING_CONTRACT_VERSION = "asset-accounting-v0.4-contract-v1"
GLOBAL_EQUITY_V04_PARAM_VERSION = "global-equity-v0.4"
CURRENT_MODEL_VERSION = "airport-model-v0.16"
CURRENT_OUTPUT_SCHEMA_VERSION = "airport-model-output-v6"
CANDIDATE_MODEL_VERSION = "airport-model-v0.16"
CANDIDATE_OUTPUT_SCHEMA_VERSION = "airport-model-output-v6"

INITIAL_INDEX = 100.0
INITIAL_GLOBAL_EQUITY_PE = 18.0
DEFAULT_EQUITY_PAYOUT_RATIO_PCT = 45.0
MIN_EQUITY_PAYOUT_RATIO_PCT = 15.0
MAX_EQUITY_PAYOUT_RATIO_PCT = 75.0


@dataclass(frozen=True)
class AssetFieldSpec:
    name: str
    scope: str
    unit: str
    nominality: str
    producer: str
    consumer: str
    stage: str
    initial_value: float | str | None = None


@dataclass(frozen=True)
class VersionPolicy:
    current_model_version: str
    current_output_schema_version: str
    candidate_model_version: str
    candidate_output_schema_version: str
    legacy_read_policy: str
    compatibility_aliases_allowed: bool


@dataclass(frozen=True)
class EquityReturnBreakdown:
    eps_index: float
    valuation_pe: float
    price_index: float
    price_return_pct: float
    payout_ratio_pct: float
    dividend_yield_pct: float
    total_return_pct: float
    total_return_index: float


@dataclass(frozen=True)
class BondReturnBreakdown:
    price_return_pct: float
    carry_pct: float
    credit_loss_pct: float
    total_return_pct: float


@dataclass(frozen=True)
class HoldingTemplate:
    template_id: str
    equity_weight: float
    sovereign_bond_weight: float
    cash_weight: float


ASSET_VERSION_POLICY = VersionPolicy(
    current_model_version=CURRENT_MODEL_VERSION,
    current_output_schema_version=CURRENT_OUTPUT_SCHEMA_VERSION,
    candidate_model_version=CANDIDATE_MODEL_VERSION,
    candidate_output_schema_version=CANDIDATE_OUTPUT_SCHEMA_VERSION,
    legacy_read_policy="explicit_legacy_viewer_or_reject",
    compatibility_aliases_allowed=False,
)


HOLDING_TEMPLATES: Mapping[str, HoldingTemplate] = {
    "market_based": HoldingTemplate("market_based", 0.50, 0.30, 0.20),
    "balanced": HoldingTemplate("balanced", 0.35, 0.40, 0.25),
    "bank_centered": HoldingTemplate("bank_centered", 0.20, 0.45, 0.35),
}


LEGACY_FIELD_REPLACEMENTS: Mapping[str, tuple[str, ...]] = {
    "global_equity_index": (
        "global_equity_price_index",
        "global_equity_total_return_index",
    ),
    "equity_earnings_index": ("global_equity_eps_index",),
    "equity_eps_growth_pct": ("global_equity_eps_growth_pct",),
    "equity_valuation_pe": ("global_equity_valuation_pe",),
    "equity_total_return_pct": ("global_equity_total_return_pct",),
    "bond_price_index": ("yield_curve_reference_10y_bond_total_return_index",),
    "bond_total_return_pct": ("yield_curve_reference_10y_bond_total_return_pct",),
    "global_sovereign_bond_index": ("global_sovereign_bond_total_return_index",),
    "sovereign_bond_total_return_pct": ("global_sovereign_bond_total_return_pct",),
    "global_corporate_bond_index": ("global_corporate_bond_total_return_index",),
    "corporate_bond_total_return_pct": ("global_corporate_bond_total_return_pct",),
    "global_60_40_portfolio_index": ("global_60_40_total_return_index",),
    "portfolio_60_40_total_return_pct": ("global_60_40_total_return_pct",),
    "regional_equity_index": (
        "regional_equity_price_index",
        "regional_equity_total_return_index",
    ),
    "regional_equity_return_pct": (
        "regional_equity_price_return_pct",
        "regional_equity_total_return_pct",
    ),
    "regional_bond_index": ("regional_sovereign_bond_total_return_index",),
    "regional_bond_return_pct": ("regional_sovereign_bond_total_return_pct",),
    "regional_wealth_effect_index": (
        "regional_household_financial_wealth_index",
        "regional_household_wealth_consumption_impulse",
    ),
}


LEGACY_CONSUMER_INVENTORY: Mapping[str, tuple[str, ...]] = {
    "global_equity_index": (
        "macro_layers/global_asset_price_layer_sim.py",
        "macro_layers/macro_run_orchestrator_sim.py",
    ),
    "equity_earnings_index": (
        "macro_layers/global_asset_price_layer_sim.py",
        "macro_layers/macro_run_orchestrator_sim.py",
    ),
    "bond_price_index": (
        "macro_layers/global_yield_curve_layer_sim.py",
        "macro_layers/macro_run_orchestrator_sim.py",
    ),
    "bond_total_return_pct": (
        "macro_layers/global_asset_price_layer_sim.py",
        "macro_layers/global_yield_curve_layer_sim.py",
        "macro_layers/macro_run_orchestrator_sim.py",
    ),
    "equity_eps_growth_pct": (
        "macro_layers/global_asset_price_layer_sim.py",
        "macro_layers/macro_run_orchestrator_sim.py",
    ),
    "equity_valuation_pe": (
        "macro_layers/city_airport_valuation_forecast_layer_sim.py",
        "macro_layers/global_asset_price_layer_sim.py",
        "macro_layers/macro_run_orchestrator_sim.py",
        "macro_layers/regional_aviation_demand_layer_sim.py",
    ),
    "equity_total_return_pct": (
        "macro_layers/global_asset_price_layer_sim.py",
        "macro_layers/global_oil_commodity_layer_sim.py",
        "macro_layers/macro_run_orchestrator_sim.py",
    ),
    "global_sovereign_bond_index": (
        "macro_layers/global_asset_price_layer_sim.py",
        "macro_layers/macro_run_orchestrator_sim.py",
    ),
    "sovereign_bond_total_return_pct": (
        "macro_layers/global_asset_price_layer_sim.py",
        "macro_layers/macro_run_orchestrator_sim.py",
        "macro_layers/regional_wealth_bridge_v04.py",
    ),
    "global_corporate_bond_index": (
        "macro_layers/global_asset_price_layer_sim.py",
        "macro_layers/macro_run_orchestrator_sim.py",
    ),
    "corporate_bond_total_return_pct": (
        "macro_layers/global_asset_price_layer_sim.py",
        "macro_layers/macro_run_orchestrator_sim.py",
    ),
    "global_60_40_portfolio_index": (
        "macro_layers/global_asset_price_layer_sim.py",
        "macro_layers/macro_run_orchestrator_sim.py",
    ),
    "portfolio_60_40_total_return_pct": (
        "macro_layers/global_asset_price_layer_sim.py",
        "macro_layers/macro_run_orchestrator_sim.py",
    ),
    "regional_equity_index": (
        "macro_layers/regional_macro_layer_sim.py",
        "macro_layers/macro_run_orchestrator_sim.py",
    ),
    "regional_equity_return_pct": (
        "macro_layers/regional_macro_layer_sim.py",
        "macro_layers/macro_run_orchestrator_sim.py",
    ),
    "regional_bond_index": (
        "macro_layers/regional_macro_layer_sim.py",
        "macro_layers/macro_run_orchestrator_sim.py",
    ),
    "regional_bond_return_pct": (
        "macro_layers/regional_macro_layer_sim.py",
        "macro_layers/macro_run_orchestrator_sim.py",
    ),
    "regional_wealth_effect_index": (
        "macro_layers/regional_macro_layer_sim.py",
        "macro_layers/macro_run_orchestrator_sim.py",
    ),
}

LEGACY_NON_PRODUCTION_INVENTORY: Mapping[str, tuple[str, ...]] = {
    "global_equity_index": (),
    "equity_earnings_index": ("tests/test_global_boundary_and_initial_state_contract.py",),
    "equity_eps_growth_pct": (),
    "equity_valuation_pe": (),
    "equity_total_return_pct": (),
    "bond_price_index": ("tests/test_asset_a3_integration.py",),
    "bond_total_return_pct": ("tests/test_asset_a3_integration.py",),
    "global_sovereign_bond_index": (),
    "sovereign_bond_total_return_pct": (),
    "global_corporate_bond_index": (),
    "corporate_bond_total_return_pct": (),
    "global_60_40_portfolio_index": (),
    "portfolio_60_40_total_return_pct": (),
    "regional_equity_index": (),
    "regional_equity_return_pct": (),
    "regional_bond_index": (),
    "regional_bond_return_pct": (),
    "regional_wealth_effect_index": (),
}


def _field(
    name: str,
    scope: str,
    unit: str,
    nominality: str,
    producer: str,
    consumer: str,
    stage: str,
    initial_value: float | str | None = None,
) -> AssetFieldSpec:
    return AssetFieldSpec(
        name=name,
        scope=scope,
        unit=unit,
        nominality=nominality,
        producer=producer,
        consumer=consumer,
        stage=stage,
        initial_value=initial_value,
    )


_GLOBAL_EQUITY_EPS_CONTRIBUTION_FIELDS = (
    "global_equity_eps_base_contribution_pp",
    "global_equity_eps_growth_contribution_pp",
    "global_equity_eps_inflation_contribution_pp",
    "global_equity_eps_cycle_contribution_pp",
    "global_equity_eps_margin_contribution_pp",
    "global_equity_eps_credit_contribution_pp",
    "global_equity_eps_dollar_contribution_pp",
    "global_equity_eps_capital_destruction_contribution_pp",
    "global_equity_eps_noise_contribution_pp",
)

_GLOBAL_EQUITY_PE_CONTRIBUTION_FIELDS = (
    "global_equity_pe_anchor",
    "global_equity_pe_rate_contribution",
    "global_equity_pe_credit_contribution",
    "global_equity_pe_fci_contribution",
    "global_equity_pe_policy_contribution",
    "global_equity_pe_dollar_contribution",
    "global_equity_pe_liquidity_contribution",
    "global_equity_pe_risk_appetite_contribution",
    "global_equity_pe_impulse_contribution",
    "global_equity_pe_crisis_contribution",
    "global_equity_pe_noise_contribution",
)


_GLOBAL_FIELD_SPECS = (
    _field(
        "asset_accounting_contract_version",
        "global_asset",
        "version",
        "not_applicable",
        "global_asset",
        "protocol",
        "A1a",
        ASSET_ACCOUNTING_CONTRACT_VERSION,
    ),
    _field(
        "global_equity_v04_param_version",
        "global_asset",
        "version",
        "not_applicable",
        "global_asset",
        "protocol",
        "A1a",
        GLOBAL_EQUITY_V04_PARAM_VERSION,
    ),
    _field(
        "yield_curve_reference_10y_bond_total_return_pct",
        "global_asset",
        "percent",
        "nominal",
        "yield_curve",
        "asset_audit",
        "A1b",
        0.0,
    ),
    _field(
        "yield_curve_reference_10y_bond_total_return_index",
        "global_asset",
        "index",
        "nominal",
        "yield_curve",
        "asset_audit",
        "A1b",
        100.0,
    ),
    _field("global_equity_eps_index", "global_asset", "index", "nominal", "global_asset", "asset", "A1a", 100.0),
    _field(
        "global_equity_eps_growth_raw_pct",
        "global_asset",
        "percent",
        "nominal",
        "global_asset",
        "audit",
        "A1a",
        0.0,
    ),
    _field(
        "global_equity_eps_growth_pct",
        "global_asset",
        "percent",
        "nominal",
        "global_asset",
        "asset",
        "A1a",
        0.0,
    ),
    *tuple(
        _field(
            name,
            "global_asset",
            "percentage_points",
            "nominal",
            "global_asset",
            "audit",
            "A1a",
            0.0,
        )
        for name in _GLOBAL_EQUITY_EPS_CONTRIBUTION_FIELDS
    ),
    _field(
        "global_equity_eps_smoothing_adjustment_pp",
        "global_asset",
        "percentage_points",
        "nominal",
        "global_asset",
        "audit",
        "A1a",
        0.0,
    ),
    _field(
        "global_equity_eps_boundary_adjustment_pp",
        "global_asset",
        "percentage_points",
        "nominal",
        "global_asset",
        "audit",
        "A1a",
        0.0,
    ),
    _field(
        "global_equity_eps_boundary_state",
        "global_asset",
        "enum",
        "not_applicable",
        "global_asset",
        "audit",
        "A1a",
        "none",
    ),
    _field(
        "global_equity_valuation_pe_raw",
        "global_asset",
        "ratio",
        "not_applicable",
        "global_asset",
        "audit",
        "A1a",
        INITIAL_GLOBAL_EQUITY_PE,
    ),
    _field(
        "global_equity_valuation_pe",
        "global_asset",
        "ratio",
        "not_applicable",
        "global_asset",
        "asset",
        "A1a",
        INITIAL_GLOBAL_EQUITY_PE,
    ),
    *tuple(
        _field(
            name,
            "global_asset",
            "ratio_points",
            "not_applicable",
            "global_asset",
            "audit",
            "A1a",
            INITIAL_GLOBAL_EQUITY_PE if name == "global_equity_pe_anchor" else 0.0,
        )
        for name in _GLOBAL_EQUITY_PE_CONTRIBUTION_FIELDS
    ),
    _field(
        "global_equity_pe_smoothing_adjustment",
        "global_asset",
        "ratio_points",
        "not_applicable",
        "global_asset",
        "audit",
        "A1a",
        0.0,
    ),
    _field(
        "global_equity_pe_boundary_adjustment",
        "global_asset",
        "ratio_points",
        "not_applicable",
        "global_asset",
        "audit",
        "A1a",
        0.0,
    ),
    _field(
        "global_equity_pe_boundary_state",
        "global_asset",
        "enum",
        "not_applicable",
        "global_asset",
        "audit",
        "A1a",
        "none",
    ),
    _field("global_equity_price_index", "global_asset", "index", "nominal", "global_asset", "viewer", "A1a", 100.0),
    _field(
        "global_equity_price_return_pct",
        "global_asset",
        "percent",
        "nominal",
        "global_asset",
        "asset",
        "A1a",
        0.0,
    ),
    _field(
        "global_equity_payout_ratio_pct",
        "global_asset",
        "percent",
        "not_applicable",
        "global_asset",
        "asset",
        "A1a",
        DEFAULT_EQUITY_PAYOUT_RATIO_PCT,
    ),
    _field(
        "global_equity_dividend_yield_pct",
        "global_asset",
        "percent",
        "nominal",
        "global_asset",
        "wealth_bridge",
        "A1a",
        0.0,
    ),
    _field(
        "global_equity_total_return_pct",
        "global_asset",
        "percent",
        "nominal",
        "global_asset",
        "regional_asset",
        "A1a",
        0.0,
    ),
    _field(
        "global_equity_total_return_index",
        "global_asset",
        "index",
        "nominal",
        "global_asset",
        "viewer",
        "A1a",
        100.0,
    ),
    _field(
        "global_equity_drawdown_pct",
        "global_asset",
        "percent",
        "nominal",
        "global_asset",
        "audit",
        "A1a",
        0.0,
    ),
    _field(
        "global_equity_price_identity_residual",
        "global_asset",
        "index_points",
        "nominal",
        "global_asset",
        "audit",
        "A1a",
        0.0,
    ),
    _field(
        "global_equity_total_return_identity_residual",
        "global_asset",
        "percentage_points",
        "nominal",
        "global_asset",
        "audit",
        "A1a",
        0.0,
    ),
    _field(
        "global_sovereign_bond_price_return_pct",
        "global_asset",
        "percent",
        "nominal",
        "global_asset",
        "audit",
        "A1b",
        0.0,
    ),
    _field(
        "global_sovereign_bond_carry_pct",
        "global_asset",
        "percent",
        "nominal",
        "global_asset",
        "audit",
        "A1b",
        0.0,
    ),
    _field(
        "global_sovereign_bond_total_return_pct",
        "global_asset",
        "percent",
        "nominal",
        "global_asset",
        "regional_asset",
        "A1b",
        0.0,
    ),
    _field(
        "global_sovereign_bond_total_return_index",
        "global_asset",
        "index",
        "nominal",
        "global_asset",
        "viewer",
        "A1b",
        100.0,
    ),
    _field(
        "global_corporate_bond_price_return_pct",
        "global_asset",
        "percent",
        "nominal",
        "global_asset",
        "audit",
        "A1b",
        0.0,
    ),
    _field(
        "global_corporate_bond_carry_pct",
        "global_asset",
        "percent",
        "nominal",
        "global_asset",
        "audit",
        "A1b",
        0.0,
    ),
    _field(
        "global_corporate_bond_credit_loss_pct",
        "global_asset",
        "percent",
        "nominal",
        "global_asset",
        "audit",
        "A1b",
        0.0,
    ),
    _field(
        "global_corporate_bond_total_return_pct",
        "global_asset",
        "percent",
        "nominal",
        "global_asset",
        "viewer",
        "A1b",
        0.0,
    ),
    _field(
        "global_corporate_bond_total_return_index",
        "global_asset",
        "index",
        "nominal",
        "global_asset",
        "viewer",
        "A1b",
        100.0,
    ),
    _field(
        "global_60_40_total_return_pct",
        "global_asset",
        "percent",
        "nominal",
        "global_asset",
        "viewer",
        "A1b",
        0.0,
    ),
    _field(
        "global_60_40_total_return_index",
        "global_asset",
        "index",
        "nominal",
        "global_asset",
        "viewer",
        "A1b",
        100.0,
    ),
)


_REGIONAL_FIELD_SPECS = (
    _field("regional_equity_eps_index", "regional_asset", "index", "nominal", "regional_asset", "asset", "A2", 100.0),
    _field(
        "regional_equity_eps_growth_raw_pct",
        "regional_asset",
        "percent",
        "nominal",
        "regional_asset",
        "audit",
        "A2",
        0.0,
    ),
    _field(
        "regional_equity_eps_growth_pct",
        "regional_asset",
        "percent",
        "nominal",
        "regional_asset",
        "asset",
        "A2",
        0.0,
    ),
    _field(
        "regional_equity_valuation_pe_raw",
        "regional_asset",
        "ratio",
        "not_applicable",
        "regional_asset",
        "audit",
        "A2",
        INITIAL_GLOBAL_EQUITY_PE,
    ),
    _field(
        "regional_equity_valuation_pe",
        "regional_asset",
        "ratio",
        "not_applicable",
        "regional_asset",
        "asset",
        "A2",
        INITIAL_GLOBAL_EQUITY_PE,
    ),
    _field("regional_equity_price_index", "regional_asset", "index", "nominal", "regional_asset", "viewer", "A2", 100.0),
    _field(
        "regional_equity_price_return_pct",
        "regional_asset",
        "percent",
        "nominal",
        "regional_asset",
        "wealth_bridge",
        "A2",
        0.0,
    ),
    _field(
        "regional_equity_payout_ratio_pct",
        "regional_asset",
        "percent",
        "not_applicable",
        "regional_asset",
        "wealth_bridge",
        "A2",
        DEFAULT_EQUITY_PAYOUT_RATIO_PCT,
    ),
    _field(
        "regional_equity_dividend_yield_pct",
        "regional_asset",
        "percent",
        "nominal",
        "regional_asset",
        "wealth_bridge",
        "A2",
        0.0,
    ),
    _field(
        "regional_equity_total_return_pct",
        "regional_asset",
        "percent",
        "nominal",
        "regional_asset",
        "wealth_bridge",
        "A2",
        0.0,
    ),
    _field(
        "regional_equity_total_return_index",
        "regional_asset",
        "index",
        "nominal",
        "regional_asset",
        "viewer",
        "A2",
        100.0,
    ),
    _field(
        "regional_sovereign_bond_price_return_pct",
        "regional_asset",
        "percent",
        "nominal",
        "regional_asset",
        "audit",
        "A2",
        0.0,
    ),
    _field(
        "regional_sovereign_bond_carry_pct",
        "regional_asset",
        "percent",
        "nominal",
        "regional_asset",
        "wealth_bridge",
        "A2",
        0.0,
    ),
    _field(
        "regional_sovereign_bond_total_return_pct",
        "regional_asset",
        "percent",
        "nominal",
        "regional_asset",
        "wealth_bridge",
        "A2",
        0.0,
    ),
    _field(
        "regional_sovereign_bond_total_return_index",
        "regional_asset",
        "index",
        "nominal",
        "regional_asset",
        "viewer",
        "A2",
        100.0,
    ),
)


_SIGNAL_FIELD_SPECS = (
    _field(
        "regional_asset_market_impulse_index",
        "regional_signal",
        "index",
        "not_applicable",
        "wealth_bridge",
        "aviation",
        "A3",
        50.0,
    ),
    _field(
        "regional_household_financial_wealth_index",
        "regional_signal",
        "index",
        "real",
        "wealth_bridge",
        "audit",
        "A3",
        100.0,
    ),
    _field(
        "regional_real_household_wealth_growth_pct",
        "regional_signal",
        "percent",
        "real",
        "wealth_bridge",
        "audit",
        "A3",
        0.0,
    ),
    _field(
        "regional_household_wealth_consumption_impulse",
        "regional_signal",
        "percentage_points",
        "real",
        "wealth_bridge",
        "aviation",
        "A3",
        0.0,
    ),
    _field(
        "regional_real_disposable_income_growth_pct",
        "regional_signal",
        "percent",
        "real",
        "regional_macro",
        "aviation",
        "A3",
        0.0,
    ),
)


_DEMAND_TARGETS = ("total", "business", "leisure", "vfr", "long_haul", "transfer")
_DEMAND_CONTRIBUTIONS = (
    "asset_market",
    "household_wealth",
    "cash_income",
    "credit_confidence",
    "fare_cost",
)

_DEMAND_FIELD_SPECS = tuple(
    _field(
        f"demand_{target}_{contribution}_contribution_pp",
        "regional_demand",
        "percentage_points",
        "not_applicable",
        "aviation",
        "audit",
        "A3",
        0.0,
    )
    for target in _DEMAND_TARGETS
    for contribution in _DEMAND_CONTRIBUTIONS
)

_PREMIUM_FIELD_SPECS = (
    _field(
        "premium_propensity_raw_index",
        "regional_demand",
        "index",
        "not_applicable",
        "aviation",
        "commercial",
        "A3",
        50.0,
    ),
    *tuple(
        _field(
            f"premium_propensity_{contribution}_contribution_points",
            "regional_demand",
            "index_points",
            "not_applicable",
            "aviation",
            "audit",
            "A3",
            0.0,
        )
        for contribution in ("asset_market", "household_wealth", "cash_income", "traffic_mix")
    ),
    _field(
        "premium_propensity_final_index",
        "regional_demand",
        "index",
        "not_applicable",
        "aviation",
        "commercial",
        "A3",
        50.0,
    ),
    _field(
        "premium_propensity_boundary_state",
        "regional_demand",
        "enum",
        "not_applicable",
        "aviation",
        "audit",
        "A3",
        "none",
    ),
)


ASSET_FIELD_SPECS = (
    *_GLOBAL_FIELD_SPECS,
    *_REGIONAL_FIELD_SPECS,
    *_SIGNAL_FIELD_SPECS,
    *_DEMAND_FIELD_SPECS,
    *_PREMIUM_FIELD_SPECS,
)
ASSET_FIELD_SPECS_BY_NAME = {spec.name: spec for spec in ASSET_FIELD_SPECS}
CANONICAL_ASSET_FIELDS = tuple(spec.name for spec in ASSET_FIELD_SPECS)


def require_finite(name: str, value: float) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def require_positive(name: str, value: float) -> float:
    result = require_finite(name, value)
    if result <= 0.0:
        raise ValueError(f"{name} must be positive")
    return result


def require_pct_above_negative_hundred(name: str, value: float) -> float:
    result = require_finite(name, value)
    if result <= -100.0:
        raise ValueError(f"{name} must be greater than -100")
    return result


def equity_price_index(eps_index: float, valuation_pe: float, initial_pe: float) -> float:
    eps = require_positive("eps_index", eps_index)
    pe = require_positive("valuation_pe", valuation_pe)
    anchor = require_positive("initial_pe", initial_pe)
    return eps * pe / anchor


def price_return_pct(current_price_index: float, previous_price_index: float) -> float:
    current = require_positive("current_price_index", current_price_index)
    previous = require_positive("previous_price_index", previous_price_index)
    return (current / previous - 1.0) * 100.0


def dividend_yield_pct(
    eps_index: float,
    payout_ratio_pct: float,
    previous_price_index: float,
    initial_pe: float,
) -> float:
    eps = require_positive("eps_index", eps_index)
    previous_price = require_positive("previous_price_index", previous_price_index)
    pe_anchor = require_positive("initial_pe", initial_pe)
    payout = require_finite("payout_ratio_pct", payout_ratio_pct)
    if payout < MIN_EQUITY_PAYOUT_RATIO_PCT or payout > MAX_EQUITY_PAYOUT_RATIO_PCT:
        raise ValueError(
            "payout_ratio_pct must be in "
            f"[{MIN_EQUITY_PAYOUT_RATIO_PCT}, {MAX_EQUITY_PAYOUT_RATIO_PCT}]"
        )
    return eps * payout / (previous_price * pe_anchor)


def compound_total_return_index(previous_index: float, total_return_pct: float) -> float:
    previous = require_positive("previous_index", previous_index)
    total_return = require_pct_above_negative_hundred("total_return_pct", total_return_pct)
    return previous * (1.0 + total_return / 100.0)


def equity_return_breakdown(
    *,
    previous_price_index: float,
    previous_total_return_index: float,
    eps_index: float,
    valuation_pe: float,
    payout_ratio_pct: float = DEFAULT_EQUITY_PAYOUT_RATIO_PCT,
    initial_pe: float = INITIAL_GLOBAL_EQUITY_PE,
) -> EquityReturnBreakdown:
    price_index = equity_price_index(eps_index, valuation_pe, initial_pe)
    price_return = price_return_pct(price_index, previous_price_index)
    dividend_yield = dividend_yield_pct(
        eps_index,
        payout_ratio_pct,
        previous_price_index,
        initial_pe,
    )
    total_return = price_return + dividend_yield
    return EquityReturnBreakdown(
        eps_index=float(eps_index),
        valuation_pe=float(valuation_pe),
        price_index=price_index,
        price_return_pct=price_return,
        payout_ratio_pct=float(payout_ratio_pct),
        dividend_yield_pct=dividend_yield,
        total_return_pct=total_return,
        total_return_index=compound_total_return_index(previous_total_return_index, total_return),
    )


def sovereign_bond_return_breakdown(
    *,
    previous_yield_pct: float,
    current_yield_pct: float,
    duration_years: float = 7.0,
    convexity: float = 50.0,
) -> BondReturnBreakdown:
    previous_yield = require_finite("previous_yield_pct", previous_yield_pct)
    current_yield = require_finite("current_yield_pct", current_yield_pct)
    duration = require_positive("duration_years", duration_years)
    convexity_value = require_finite("convexity", convexity)
    if convexity_value < 0.0:
        raise ValueError("convexity must be non-negative")
    yield_change = (current_yield - previous_yield) / 100.0
    price_return = (-duration * yield_change + 0.5 * convexity_value * yield_change**2) * 100.0
    carry = previous_yield
    return BondReturnBreakdown(
        price_return_pct=price_return,
        carry_pct=carry,
        credit_loss_pct=0.0,
        total_return_pct=price_return + carry,
    )


def corporate_bond_return_breakdown(
    *,
    previous_yield_pct: float,
    current_yield_pct: float,
    previous_ig_spread_bps: float,
    current_ig_spread_bps: float,
    credit_loss_pct: float,
    risk_free_duration_years: float = 5.0,
    spread_duration_years: float = 4.2,
    convexity: float = 28.0,
) -> BondReturnBreakdown:
    sovereign = sovereign_bond_return_breakdown(
        previous_yield_pct=previous_yield_pct,
        current_yield_pct=current_yield_pct,
        duration_years=risk_free_duration_years,
        convexity=convexity,
    )
    previous_spread = require_finite("previous_ig_spread_bps", previous_ig_spread_bps)
    current_spread = require_finite("current_ig_spread_bps", current_ig_spread_bps)
    spread_duration = require_positive("spread_duration_years", spread_duration_years)
    loss = require_finite("credit_loss_pct", credit_loss_pct)
    if loss < 0.0:
        raise ValueError("credit_loss_pct must be non-negative")
    spread_change_decimal = (current_spread - previous_spread) / 10_000.0
    spread_price_return = -spread_duration * spread_change_decimal * 100.0
    price_return = sovereign.price_return_pct + spread_price_return
    carry = require_finite("previous_yield_pct", previous_yield_pct) + previous_spread / 100.0
    return BondReturnBreakdown(
        price_return_pct=price_return,
        carry_pct=carry,
        credit_loss_pct=loss,
        total_return_pct=price_return + carry - loss,
    )


def rebalanced_60_40_return_pct(
    equity_total_return_pct: float,
    sovereign_bond_total_return_pct: float,
) -> float:
    equity_return = require_finite("equity_total_return_pct", equity_total_return_pct)
    bond_return = require_finite(
        "sovereign_bond_total_return_pct",
        sovereign_bond_total_return_pct,
    )
    return 0.60 * equity_return + 0.40 * bond_return


def validate_holding_template(template: HoldingTemplate) -> None:
    weights = (
        template.equity_weight,
        template.sovereign_bond_weight,
        template.cash_weight,
    )
    for name, value in zip(("equity", "sovereign_bond", "cash"), weights):
        weight = require_finite(f"{name}_weight", value)
        if weight < 0.0 or weight > 1.0:
            raise ValueError(f"{name}_weight must be in [0, 1]")
    if not math.isclose(sum(weights), 1.0, rel_tol=0.0, abs_tol=1e-12):
        raise ValueError("holding weights must sum to 1")


def real_return_pct(nominal_return_pct: float, inflation_pct: float) -> float:
    nominal = require_pct_above_negative_hundred("nominal_return_pct", nominal_return_pct)
    inflation = require_pct_above_negative_hundred("inflation_pct", inflation_pct)
    return ((1.0 + nominal / 100.0) / (1.0 + inflation / 100.0) - 1.0) * 100.0


def household_real_financial_wealth_growth_pct(
    *,
    template: HoldingTemplate,
    equity_price_return_pct: float,
    equity_dividend_yield_pct: float,
    sovereign_bond_total_return_pct: float,
    cash_nominal_return_pct: float,
    inflation_pct: float,
    dividend_reinvestment_share: float = 0.70,
) -> float:
    validate_holding_template(template)
    reinvestment_share = require_finite(
        "dividend_reinvestment_share",
        dividend_reinvestment_share,
    )
    if reinvestment_share < 0.0 or reinvestment_share > 1.0:
        raise ValueError("dividend_reinvestment_share must be in [0, 1]")
    equity_return = require_finite("equity_price_return_pct", equity_price_return_pct) + (
        require_finite("equity_dividend_yield_pct", equity_dividend_yield_pct)
        * reinvestment_share
    )
    nominal_return = (
        template.equity_weight * equity_return
        + template.sovereign_bond_weight
        * require_finite(
            "sovereign_bond_total_return_pct",
            sovereign_bond_total_return_pct,
        )
        + template.cash_weight * require_finite("cash_nominal_return_pct", cash_nominal_return_pct)
    )
    return real_return_pct(nominal_return, inflation_pct)


def household_cash_dividend_signal_pct(
    *,
    template: HoldingTemplate,
    equity_dividend_yield_pct: float,
    dividend_cash_share: float = 0.30,
) -> float:
    validate_holding_template(template)
    cash_share = require_finite("dividend_cash_share", dividend_cash_share)
    if cash_share < 0.0 or cash_share > 1.0:
        raise ValueError("dividend_cash_share must be in [0, 1]")
    dividend_yield = require_finite("equity_dividend_yield_pct", equity_dividend_yield_pct)
    return template.equity_weight * dividend_yield * cash_share


def wealth_consumption_impulse(
    *,
    current_real_wealth_growth_pct: float,
    previous_impulse: float,
    current_weight: float = 0.45,
    persistence: float = 0.55,
    lower_bound: float = -8.0,
    upper_bound: float = 8.0,
) -> float:
    current = require_finite(
        "current_real_wealth_growth_pct",
        current_real_wealth_growth_pct,
    )
    previous = require_finite("previous_impulse", previous_impulse)
    current_weight_value = require_finite("current_weight", current_weight)
    persistence_value = require_finite("persistence", persistence)
    if current_weight_value < 0.0 or persistence_value < 0.0:
        raise ValueError("wealth impulse weights must be non-negative")
    if not math.isclose(
        current_weight_value + persistence_value,
        1.0,
        rel_tol=0.0,
        abs_tol=1e-12,
    ):
        raise ValueError("wealth impulse weights must sum to 1")
    low = require_finite("lower_bound", lower_bound)
    high = require_finite("upper_bound", upper_bound)
    if low >= high:
        raise ValueError("lower_bound must be less than upper_bound")
    raw = current_weight_value * current + persistence_value * previous
    return max(low, min(high, raw))


def stable_substream_seed(
    seed: int,
    *,
    layer_id: str,
    region_id: str = "",
    year_index: int = 0,
    shock_id: str = "",
) -> int:
    if not layer_id:
        raise ValueError("layer_id must be non-empty")
    if year_index < 0:
        raise ValueError("year_index must be non-negative")
    canonical = "\x1f".join(
        (
            ASSET_ACCOUNTING_CONTRACT_VERSION,
            str(int(seed)),
            layer_id,
            region_id,
            str(int(year_index)),
            shock_id,
        )
    )
    return int.from_bytes(hashlib.sha256(canonical.encode("utf-8")).digest()[:8], "big")


def required_fields_for_scope(scope: str) -> tuple[str, ...]:
    fields = tuple(spec.name for spec in ASSET_FIELD_SPECS if spec.scope == scope)
    if not fields:
        raise ValueError(f"unknown asset field scope: {scope}")
    return fields


def initial_contract_row(scope: str) -> dict[str, Any]:
    return {
        spec.name: spec.initial_value
        for spec in ASSET_FIELD_SPECS
        if spec.scope == scope and spec.initial_value is not None
    }


def validate_candidate_row(
    row: Mapping[str, Any],
    *,
    scope: str,
    year_index: int,
    output_schema_version: str,
) -> None:
    if output_schema_version != CANDIDATE_OUTPUT_SCHEMA_VERSION:
        raise ValueError(
            "asset v0.4 rows require "
            f"{CANDIDATE_OUTPUT_SCHEMA_VERSION}, got {output_schema_version}"
        )
    legacy = sorted(set(row).intersection(LEGACY_FIELD_REPLACEMENTS))
    if legacy:
        raise ValueError(f"asset v0.4 row contains legacy fields: {', '.join(legacy)}")
    required = required_fields_for_scope(scope)
    missing = [field for field in required if field not in row]
    if missing:
        raise ValueError(f"asset v0.4 row missing fields: {', '.join(missing)}")
    if year_index == 0:
        for spec in ASSET_FIELD_SPECS:
            if spec.scope != scope or spec.initial_value is None:
                continue
            if row[spec.name] != spec.initial_value:
                raise ValueError(
                    f"asset v0.4 initial field {spec.name} must be {spec.initial_value!r}"
                )


def validate_contract_definition() -> None:
    if len(ASSET_FIELD_SPECS_BY_NAME) != len(ASSET_FIELD_SPECS):
        raise ValueError("asset v0.4 field names must be unique")
    valid_scopes = {"global_asset", "regional_asset", "regional_signal", "regional_demand"}
    valid_units = {
        "enum",
        "index",
        "index_points",
        "percent",
        "percentage_points",
        "ratio",
        "ratio_points",
        "version",
    }
    valid_nominality = {"nominal", "real", "not_applicable"}
    valid_stages = {"A1a", "A1b", "A2", "A3"}
    for spec in ASSET_FIELD_SPECS:
        if spec.scope not in valid_scopes:
            raise ValueError(f"invalid scope for {spec.name}: {spec.scope}")
        if spec.unit not in valid_units:
            raise ValueError(f"invalid unit for {spec.name}: {spec.unit}")
        if spec.nominality not in valid_nominality:
            raise ValueError(f"invalid nominality for {spec.name}: {spec.nominality}")
        if spec.stage not in valid_stages:
            raise ValueError(f"invalid stage for {spec.name}: {spec.stage}")
    legacy_fields = set(LEGACY_FIELD_REPLACEMENTS)
    if legacy_fields != set(LEGACY_CONSUMER_INVENTORY):
        raise ValueError("legacy field replacements and production inventory must cover the same fields")
    if legacy_fields != set(LEGACY_NON_PRODUCTION_INVENTORY):
        raise ValueError(
            "legacy field replacements and non-production inventory must cover the same fields"
        )
    for template in HOLDING_TEMPLATES.values():
        validate_holding_template(template)


validate_contract_definition()
