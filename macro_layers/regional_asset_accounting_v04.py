from __future__ import annotations

import math
from dataclasses import dataclass, fields
from importlib import import_module
from typing import Any, Mapping, Sequence


_SIBLING_PREFIX = f"{__package__}." if __package__ else ""
accounting = import_module(f"{_SIBLING_PREFIX}asset_accounting_v04")

ASSET_ACCOUNTING_CONTRACT_VERSION = accounting.ASSET_ACCOUNTING_CONTRACT_VERSION
REGIONAL_ASSET_V04_PARAM_VERSION = "regional-asset-accounting-v0.4"
REGIONAL_ASSET_V04_INTERFACE_VERSION = ASSET_ACCOUNTING_CONTRACT_VERSION


REGIONAL_EPS_CONTRIBUTION_FIELDS = (
    "regional_equity_eps_nominal_growth_contribution_pp",
    "regional_equity_eps_industry_margin_contribution_pp",
    "regional_equity_eps_external_demand_contribution_pp",
    "regional_equity_eps_commodity_producer_contribution_pp",
    "regional_equity_eps_energy_import_contribution_pp",
    "regional_equity_eps_financing_credit_contribution_pp",
    "regional_equity_eps_dilution_contribution_pp",
    "regional_equity_eps_capital_destruction_contribution_pp",
    "regional_equity_eps_global_common_contribution_pp",
)

REGIONAL_PE_CONTRIBUTION_FIELDS = (
    "regional_equity_pe_anchor",
    "regional_equity_pe_global_common_contribution",
    "regional_equity_pe_local_growth_contribution",
    "regional_equity_pe_real_rate_contribution",
    "regional_equity_pe_credit_contribution",
    "regional_equity_pe_institution_contribution",
    "regional_equity_pe_external_risk_contribution",
    "regional_equity_pe_cycle_contribution",
    "regional_equity_pe_event_contribution",
)

REGIONAL_ASSET_V04_CORE_FIELDS = tuple(
    spec.name
    for spec in accounting.ASSET_FIELD_SPECS
    if spec.scope == "regional_asset"
)

REGIONAL_ASSET_V04_DIAGNOSTIC_FIELDS = (
    "regional_asset_v04_param_version",
    "asset_accounting_contract_version",
    "regional_asset_template_id",
    "regional_asset_global_weight",
    "regional_equity_initial_pe",
    "regional_equity_eps_smoothing_adjustment_pp",
    "regional_equity_eps_boundary_adjustment_pp",
    "regional_equity_eps_boundary_state",
    "regional_equity_eps_growth_raw_identity_residual",
    "regional_equity_eps_growth_final_identity_residual",
    *REGIONAL_EPS_CONTRIBUTION_FIELDS,
    "regional_equity_pe_smoothing_adjustment",
    "regional_equity_pe_boundary_adjustment",
    "regional_equity_pe_boundary_state",
    "regional_equity_pe_raw_identity_residual",
    "regional_equity_pe_final_identity_residual",
    *REGIONAL_PE_CONTRIBUTION_FIELDS,
    "regional_equity_payout_target_pct",
    "regional_equity_payout_smoothing_adjustment_pct",
    "regional_equity_payout_boundary_adjustment_pct",
    "regional_equity_payout_boundary_state",
    "regional_equity_eps_price_return_contribution_pct",
    "regional_equity_pe_price_return_contribution_pct",
    "regional_equity_eps_pe_interaction_price_return_contribution_pct",
    "regional_equity_price_identity_residual",
    "regional_equity_price_return_identity_residual",
    "regional_equity_total_return_identity_residual",
    "regional_sovereign_bond_duration_years",
    "regional_sovereign_bond_yield_change_pct",
    "regional_sovereign_bond_duration_price_contribution_pct",
    "regional_sovereign_bond_price_return_identity_residual",
    "regional_sovereign_bond_total_return_identity_residual",
)

REGIONAL_ASSET_V04_FIELDS = (
    *REGIONAL_ASSET_V04_CORE_FIELDS,
    *REGIONAL_ASSET_V04_DIAGNOSTIC_FIELDS,
)


@dataclass(frozen=True)
class RegionalAssetV04Params:
    initial_eps_index: float = accounting.INITIAL_INDEX
    initial_pe: float = accounting.INITIAL_GLOBAL_EQUITY_PE
    initial_price_index: float = accounting.INITIAL_INDEX
    initial_total_return_index: float = accounting.INITIAL_INDEX
    initial_bond_total_return_index: float = accounting.INITIAL_INDEX
    initial_payout_ratio_pct: float = accounting.DEFAULT_EQUITY_PAYOUT_RATIO_PCT
    eps_smoothing: float = 0.55
    pe_smoothing: float = 0.45
    payout_smoothing: float = 0.35
    min_eps_growth_pct: float = -45.0
    max_eps_growth_pct: float = 45.0
    min_eps_index: float = 1.0
    min_pe: float = 6.5
    max_pe: float = 34.0
    min_payout_ratio_pct: float = accounting.MIN_EQUITY_PAYOUT_RATIO_PCT
    max_payout_ratio_pct: float = accounting.MAX_EQUITY_PAYOUT_RATIO_PCT


@dataclass(frozen=True)
class RegionalAssetTemplate:
    template_id: str
    base_payout_ratio_pct: float
    nominal_growth_pass_through: float
    margin_cycle_sensitivity: float
    external_demand_sensitivity: float
    commodity_producer_sensitivity: float
    energy_import_sensitivity: float
    financing_sensitivity: float
    dilution_drag_pct: float
    capital_destruction_sensitivity: float
    global_eps_common_sensitivity: float
    pe_growth_sensitivity: float
    pe_real_rate_sensitivity: float
    pe_credit_spread_sensitivity_per_bp: float
    pe_institution_discount: float
    pe_external_risk_sensitivity: float
    pe_cycle_sensitivity: float
    pe_event_sensitivity: float
    global_pe_common_sensitivity: float
    bond_duration_years: float
    payout_growth_opportunity_sensitivity: float
    payout_stress_sensitivity: float


REGIONAL_ASSET_TEMPLATES: Mapping[str, RegionalAssetTemplate] = {
    "developed_diversified": RegionalAssetTemplate(
        template_id="developed_diversified",
        base_payout_ratio_pct=46.0,
        nominal_growth_pass_through=0.74,
        margin_cycle_sensitivity=0.52,
        external_demand_sensitivity=0.34,
        commodity_producer_sensitivity=0.24,
        energy_import_sensitivity=0.34,
        financing_sensitivity=0.72,
        dilution_drag_pct=0.24,
        capital_destruction_sensitivity=0.52,
        global_eps_common_sensitivity=0.24,
        pe_growth_sensitivity=0.52,
        pe_real_rate_sensitivity=1.05,
        pe_credit_spread_sensitivity_per_bp=0.0035,
        pe_institution_discount=0.25,
        pe_external_risk_sensitivity=0.22,
        pe_cycle_sensitivity=0.050,
        pe_event_sensitivity=0.050,
        global_pe_common_sensitivity=0.88,
        bond_duration_years=7.2,
        payout_growth_opportunity_sensitivity=0.35,
        payout_stress_sensitivity=0.18,
    ),
    "mature_export_manufacturing": RegionalAssetTemplate(
        template_id="mature_export_manufacturing",
        base_payout_ratio_pct=43.0,
        nominal_growth_pass_through=0.78,
        margin_cycle_sensitivity=0.70,
        external_demand_sensitivity=0.62,
        commodity_producer_sensitivity=0.16,
        energy_import_sensitivity=0.78,
        financing_sensitivity=0.78,
        dilution_drag_pct=0.30,
        capital_destruction_sensitivity=0.58,
        global_eps_common_sensitivity=0.30,
        pe_growth_sensitivity=0.62,
        pe_real_rate_sensitivity=1.10,
        pe_credit_spread_sensitivity_per_bp=0.0038,
        pe_institution_discount=0.35,
        pe_external_risk_sensitivity=0.27,
        pe_cycle_sensitivity=0.060,
        pe_event_sensitivity=0.060,
        global_pe_common_sensitivity=0.92,
        bond_duration_years=7.8,
        payout_growth_opportunity_sensitivity=0.42,
        payout_stress_sensitivity=0.20,
    ),
    "emerging_manufacturing": RegionalAssetTemplate(
        template_id="emerging_manufacturing",
        base_payout_ratio_pct=36.0,
        nominal_growth_pass_through=0.78,
        margin_cycle_sensitivity=0.82,
        external_demand_sensitivity=0.66,
        commodity_producer_sensitivity=0.24,
        energy_import_sensitivity=0.76,
        financing_sensitivity=0.98,
        dilution_drag_pct=0.58,
        capital_destruction_sensitivity=0.74,
        global_eps_common_sensitivity=0.31,
        pe_growth_sensitivity=0.74,
        pe_real_rate_sensitivity=0.88,
        pe_credit_spread_sensitivity_per_bp=0.0047,
        pe_institution_discount=0.78,
        pe_external_risk_sensitivity=0.38,
        pe_cycle_sensitivity=0.075,
        pe_event_sensitivity=0.078,
        global_pe_common_sensitivity=0.76,
        bond_duration_years=5.8,
        payout_growth_opportunity_sensitivity=0.62,
        payout_stress_sensitivity=0.26,
    ),
    "domestic_growth": RegionalAssetTemplate(
        template_id="domestic_growth",
        base_payout_ratio_pct=33.0,
        nominal_growth_pass_through=0.82,
        margin_cycle_sensitivity=0.76,
        external_demand_sensitivity=0.34,
        commodity_producer_sensitivity=0.14,
        energy_import_sensitivity=0.88,
        financing_sensitivity=1.04,
        dilution_drag_pct=0.66,
        capital_destruction_sensitivity=0.82,
        global_eps_common_sensitivity=0.20,
        pe_growth_sensitivity=0.88,
        pe_real_rate_sensitivity=0.78,
        pe_credit_spread_sensitivity_per_bp=0.0052,
        pe_institution_discount=0.96,
        pe_external_risk_sensitivity=0.44,
        pe_cycle_sensitivity=0.085,
        pe_event_sensitivity=0.090,
        global_pe_common_sensitivity=0.64,
        bond_duration_years=5.2,
        payout_growth_opportunity_sensitivity=0.72,
        payout_stress_sensitivity=0.29,
    ),
    "commodity_exporter": RegionalAssetTemplate(
        template_id="commodity_exporter",
        base_payout_ratio_pct=48.0,
        nominal_growth_pass_through=0.68,
        margin_cycle_sensitivity=0.64,
        external_demand_sensitivity=0.42,
        commodity_producer_sensitivity=1.00,
        energy_import_sensitivity=0.20,
        financing_sensitivity=0.86,
        dilution_drag_pct=0.42,
        capital_destruction_sensitivity=0.80,
        global_eps_common_sensitivity=0.22,
        pe_growth_sensitivity=0.46,
        pe_real_rate_sensitivity=0.82,
        pe_credit_spread_sensitivity_per_bp=0.0044,
        pe_institution_discount=0.64,
        pe_external_risk_sensitivity=0.34,
        pe_cycle_sensitivity=0.070,
        pe_event_sensitivity=0.078,
        global_pe_common_sensitivity=0.74,
        bond_duration_years=6.0,
        payout_growth_opportunity_sensitivity=0.34,
        payout_stress_sensitivity=0.25,
    ),
    "frontier_mixed": RegionalAssetTemplate(
        template_id="frontier_mixed",
        base_payout_ratio_pct=38.0,
        nominal_growth_pass_through=0.72,
        margin_cycle_sensitivity=0.60,
        external_demand_sensitivity=0.30,
        commodity_producer_sensitivity=0.55,
        energy_import_sensitivity=0.56,
        financing_sensitivity=1.18,
        dilution_drag_pct=0.86,
        capital_destruction_sensitivity=1.08,
        global_eps_common_sensitivity=0.18,
        pe_growth_sensitivity=0.50,
        pe_real_rate_sensitivity=0.66,
        pe_credit_spread_sensitivity_per_bp=0.0060,
        pe_institution_discount=1.30,
        pe_external_risk_sensitivity=0.54,
        pe_cycle_sensitivity=0.090,
        pe_event_sensitivity=0.115,
        global_pe_common_sensitivity=0.52,
        bond_duration_years=4.5,
        payout_growth_opportunity_sensitivity=0.45,
        payout_stress_sensitivity=0.34,
    ),
}


REGION_TEMPLATE_BY_REGION: Mapping[str, str] = {
    "north_america": "developed_diversified",
    "china_mainland": "emerging_manufacturing",
    "hk_macao_taiwan": "mature_export_manufacturing",
    "japan_korea": "mature_export_manufacturing",
    "southeast_asia": "emerging_manufacturing",
    "south_asia_india": "domestic_growth",
    "middle_east_gulf": "commodity_exporter",
    "central_asia_turkey_eurasia": "commodity_exporter",
    "oceania": "commodity_exporter",
    "north_africa": "frontier_mixed",
    "latin_america_caribbean": "commodity_exporter",
    "sub_saharan_africa": "frontier_mixed",
    "west_north_europe": "developed_diversified",
    "south_east_europe_mediterranean": "emerging_manufacturing",
}


@dataclass(frozen=True)
class _ResolvedRegionConfig:
    region_id: str
    global_weight: float
    trend_growth_pct: float
    market_maturity: float
    international_exposure: float
    credit_sensitivity: float
    geopolitical_sensitivity: float
    asset_global_beta: float
    energy_import_sensitivity: float
    commodity_export_sensitivity: float


@dataclass
class _RegionalAssetState:
    eps_index: float
    eps_growth_pct: float
    valuation_pe: float
    price_index: float
    total_return_index: float
    payout_ratio_pct: float
    bond_total_return_index: float


REGIONAL_REQUIRED_FIELDS = (
    "year_index",
    "region_id",
    "regional_global_weight",
    "regional_gdp_growth_pct",
    "regional_headline_inflation_pct",
    "regional_potential_growth_pct",
    "regional_output_gap_pct",
    "regional_real_10y_yield_pct",
    "regional_10y_yield_pct",
    "regional_hy_spread_bps",
    "regional_financial_conditions_index",
    "regional_credit_stress_index",
    "regional_default_risk_index",
    "regional_terms_of_trade_index",
    "regional_energy_cost_pressure_index",
    "regional_currency_yoy_pct",
    "regional_geopolitical_risk_index",
    "regional_policy_uncertainty_index",
    "regional_risk_appetite_index",
    "regional_macro_stress_index",
    "regional_liquidity_index",
)

GLOBAL_REQUIRED_FIELDS = (
    "year_index",
    "realized_growth_pct",
    "output_gap_pct",
    "headline_inflation_pct",
    "global_real_10y_yield_pct",
    "global_high_yield_spread_bps",
    "global_liquidity_index",
    "risk_appetite_index",
    "financial_stress_index",
    "oil_yoy_change_pct",
    "global_equity_eps_growth_pct",
    "global_equity_eps_cycle_contribution_pp",
    "global_equity_eps_margin_contribution_pp",
    "global_equity_eps_credit_contribution_pp",
    "global_equity_eps_dollar_contribution_pp",
    "global_equity_eps_capital_destruction_contribution_pp",
    "global_equity_valuation_pe",
    "global_equity_price_return_pct",
    "global_equity_total_return_pct",
    "global_sovereign_bond_total_return_pct",
)

GLOBAL_RECONCILIATION_REQUIRED_FIELDS = (
    "year_index",
    "global_equity_eps_index",
    "global_equity_valuation_pe",
    "global_equity_price_return_pct",
    "global_equity_total_return_pct",
    "global_sovereign_bond_total_return_pct",
)


RECONCILIATION_NUMERIC_FIELDS = (
    "regional_asset_reconciliation_region_count",
    "regional_asset_reconciliation_weight_sum",
    "regional_asset_reconciliation_weight_normalization_gap",
    "regional_asset_weighted_equity_eps_index",
    "global_equity_eps_index_reference",
    "regional_asset_equity_eps_gap_index_points",
    "regional_asset_weighted_equity_valuation_pe",
    "global_equity_valuation_pe_reference",
    "regional_asset_equity_pe_gap",
    "regional_asset_weighted_equity_price_return_pct",
    "global_equity_price_return_pct_reference",
    "regional_asset_equity_price_return_gap_pct",
    "regional_asset_weighted_equity_total_return_pct",
    "global_equity_total_return_pct_reference",
    "regional_asset_equity_total_return_gap_pct",
    "regional_asset_weighted_sovereign_bond_total_return_pct",
    "global_sovereign_bond_total_return_pct_reference",
    "regional_asset_sovereign_bond_total_return_gap_pct",
)


RECONCILIATION_FIELDS = (
    "year_index",
    "regional_asset_reconciliation_scope",
    *RECONCILIATION_NUMERIC_FIELDS,
    "regional_asset_equity_gap_source",
    "regional_asset_bond_gap_source",
)


def _finite_number(name: str, value: Any) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be a finite number")
    try:
        result = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{name} must be a finite number") from error
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def _required_number(row: Mapping[str, Any], field: str) -> float:
    if field not in row:
        raise ValueError(f"missing required field: {field}")
    return _finite_number(field, row[field])


def _config_value(config: Mapping[str, Any] | Any, field: str) -> Any:
    if isinstance(config, Mapping):
        if field not in config:
            raise ValueError(f"region_config missing required field: {field}")
        return config[field]
    if not hasattr(config, field):
        raise ValueError(f"region_config missing required field: {field}")
    return getattr(config, field)


def _resolve_region_config(config: Mapping[str, Any] | Any) -> _ResolvedRegionConfig:
    if config is None:
        raise ValueError("region_config is required")
    region_id = str(_config_value(config, "region_id"))
    if not region_id:
        raise ValueError("region_config.region_id must be non-empty")
    resolved = _ResolvedRegionConfig(
        region_id=region_id,
        global_weight=_finite_number("region_config.global_weight", _config_value(config, "global_weight")),
        trend_growth_pct=_finite_number("region_config.trend_growth_pct", _config_value(config, "trend_growth_pct")),
        market_maturity=_finite_number("region_config.market_maturity", _config_value(config, "market_maturity")),
        international_exposure=_finite_number(
            "region_config.international_exposure",
            _config_value(config, "international_exposure"),
        ),
        credit_sensitivity=_finite_number(
            "region_config.credit_sensitivity",
            _config_value(config, "credit_sensitivity"),
        ),
        geopolitical_sensitivity=_finite_number(
            "region_config.geopolitical_sensitivity",
            _config_value(config, "geopolitical_sensitivity"),
        ),
        asset_global_beta=_finite_number(
            "region_config.asset_global_beta",
            _config_value(config, "asset_global_beta"),
        ),
        energy_import_sensitivity=_finite_number(
            "region_config.energy_import_sensitivity",
            _config_value(config, "energy_import_sensitivity"),
        ),
        commodity_export_sensitivity=_finite_number(
            "region_config.commodity_export_sensitivity",
            _config_value(config, "commodity_export_sensitivity"),
        ),
    )
    if resolved.global_weight <= 0.0:
        raise ValueError("region_config.global_weight must be positive")
    if resolved.global_weight > 1.0:
        raise ValueError("region_config.global_weight must not exceed 1")
    if not 0.0 <= resolved.market_maturity <= 1.0:
        raise ValueError("region_config.market_maturity must be in [0, 1]")
    for name in (
        "market_maturity",
        "international_exposure",
        "credit_sensitivity",
        "geopolitical_sensitivity",
        "asset_global_beta",
        "energy_import_sensitivity",
        "commodity_export_sensitivity",
    ):
        if getattr(resolved, name) < 0.0:
            raise ValueError(f"region_config.{name} must be non-negative")
    return resolved


def _resolve_template(
    region_id: str,
    template: str | RegionalAssetTemplate | Mapping[str, Any] | None,
) -> RegionalAssetTemplate:
    if template is None:
        try:
            template_id = REGION_TEMPLATE_BY_REGION[region_id]
        except KeyError as error:
            raise ValueError(f"no regional asset template mapping for {region_id}") from error
        return REGIONAL_ASSET_TEMPLATES[template_id]
    if isinstance(template, str):
        try:
            return REGIONAL_ASSET_TEMPLATES[template]
        except KeyError as error:
            raise ValueError(f"unknown regional asset template: {template}") from error
    if isinstance(template, RegionalAssetTemplate):
        return template
    if isinstance(template, Mapping):
        try:
            return RegionalAssetTemplate(**dict(template))
        except TypeError as error:
            raise ValueError("invalid regional asset template mapping") from error
    raise ValueError("template must be a template id, RegionalAssetTemplate, mapping, or None")


def validate_params(params: RegionalAssetV04Params) -> None:
    for field in fields(params):
        _finite_number(field.name, getattr(params, field.name))
    for name in (
        "initial_eps_index",
        "initial_pe",
        "initial_price_index",
        "initial_total_return_index",
        "initial_bond_total_return_index",
        "min_eps_index",
    ):
        if getattr(params, name) <= 0.0:
            raise ValueError(f"{name} must be positive")
    if not math.isclose(
        params.initial_price_index,
        params.initial_eps_index,
        rel_tol=0.0,
        abs_tol=1e-12,
    ):
        raise ValueError("initial_price_index must equal initial_eps_index")
    for name in ("eps_smoothing", "pe_smoothing", "payout_smoothing"):
        if not 0.0 < getattr(params, name) <= 1.0:
            raise ValueError(f"{name} must be in (0, 1]")
    if not -100.0 < params.min_eps_growth_pct < params.max_eps_growth_pct:
        raise ValueError("EPS growth boundaries must satisfy -100 < min < max")
    if not 0.0 < params.min_pe < params.initial_pe < params.max_pe:
        raise ValueError("initial_pe must be strictly inside PE boundaries")
    if not (
        params.min_payout_ratio_pct
        <= params.initial_payout_ratio_pct
        <= params.max_payout_ratio_pct
    ):
        raise ValueError("initial_payout_ratio_pct is outside payout boundaries")


def validate_template(template: RegionalAssetTemplate) -> None:
    if not template.template_id:
        raise ValueError("template_id must be non-empty")
    for field in fields(template):
        if field.name == "template_id":
            continue
        value = _finite_number(f"template.{field.name}", getattr(template, field.name))
        if field.name == "bond_duration_years" and value <= 0.0:
            raise ValueError("template.bond_duration_years must be positive")
        if value < 0.0:
            raise ValueError(f"template.{field.name} must be non-negative")
    if not (
        accounting.MIN_EQUITY_PAYOUT_RATIO_PCT
        <= template.base_payout_ratio_pct
        <= accounting.MAX_EQUITY_PAYOUT_RATIO_PCT
    ):
        raise ValueError("template.base_payout_ratio_pct is outside payout boundaries")


def _validate_path_records(
    records: Sequence[Mapping[str, Any]],
    *,
    label: str,
    required_fields: Sequence[str],
) -> None:
    if isinstance(records, (str, bytes)) or not isinstance(records, Sequence):
        raise ValueError(f"{label} must be a sequence of mappings")
    for position, row in enumerate(records):
        if not isinstance(row, Mapping):
            raise ValueError(f"{label}[{position}] must be a mapping")
        if "year_index" not in row:
            raise ValueError(f"{label}[{position}] missing required field: year_index")
        year_value = _required_number(row, "year_index")
        if not year_value.is_integer() or int(year_value) != position:
            raise ValueError(f"{label} requires contiguous year_index values starting at 0")
        for field in required_fields:
            if field in {"year_index", "region_id"}:
                continue
            _required_number(row, field)


def _validate_aligned_inputs(
    regional_records: Sequence[Mapping[str, Any]],
    global_records: Sequence[Mapping[str, Any]],
    config: _ResolvedRegionConfig,
) -> None:
    _validate_path_records(
        regional_records,
        label="regional_records",
        required_fields=REGIONAL_REQUIRED_FIELDS,
    )
    _validate_path_records(
        global_records,
        label="global_records",
        required_fields=GLOBAL_REQUIRED_FIELDS,
    )
    if len(regional_records) != len(global_records):
        raise ValueError("regional_records and global_records length mismatch")
    for position, (regional_row, global_row) in enumerate(zip(regional_records, global_records)):
        region_id = str(regional_row.get("region_id", ""))
        if region_id != config.region_id:
            raise ValueError(
                f"regional_records[{position}].region_id must equal region_config.region_id"
            )
        regional_weight = _required_number(regional_row, "regional_global_weight")
        if _required_number(regional_row, "regional_hy_spread_bps") < 0.0:
            raise ValueError("regional_hy_spread_bps must be non-negative")
        if _required_number(global_row, "global_equity_valuation_pe") <= 0.0:
            raise ValueError("global_equity_valuation_pe must be positive")
        if not math.isclose(
            regional_weight,
            config.global_weight,
            rel_tol=0.0,
            abs_tol=1e-12,
        ):
            raise ValueError(
                "regional_global_weight must equal region_config.global_weight"
            )
        if int(_required_number(global_row, "year_index")) != position:
            raise ValueError("global_records year_index is not aligned")


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _boundary_state(value: float, low: float, high: float) -> str:
    if value < low:
        return "floor"
    if value > high:
        return "cap"
    return "none"


def _global_common_eps_shock(global_row: Mapping[str, Any]) -> float:
    return sum(
        _required_number(global_row, field)
        for field in (
            "global_equity_eps_cycle_contribution_pp",
            "global_equity_eps_margin_contribution_pp",
            "global_equity_eps_credit_contribution_pp",
            "global_equity_eps_dollar_contribution_pp",
            "global_equity_eps_capital_destruction_contribution_pp",
        )
    )


def _eps_contributions(
    regional_row: Mapping[str, Any],
    global_row: Mapping[str, Any],
    config: _ResolvedRegionConfig,
    template: RegionalAssetTemplate,
) -> dict[str, float]:
    local_growth = _required_number(regional_row, "regional_gdp_growth_pct")
    local_inflation = _required_number(regional_row, "regional_headline_inflation_pct")
    output_gap = _required_number(regional_row, "regional_output_gap_pct")
    terms_of_trade = _required_number(regional_row, "regional_terms_of_trade_index")
    energy_cost = _required_number(regional_row, "regional_energy_cost_pressure_index")
    hy_spread = _required_number(regional_row, "regional_hy_spread_bps")
    fci = _required_number(regional_row, "regional_financial_conditions_index")
    credit_stress = _required_number(regional_row, "regional_credit_stress_index")
    default_risk = _required_number(regional_row, "regional_default_risk_index")
    policy_uncertainty = _required_number(regional_row, "regional_policy_uncertainty_index")
    macro_stress = _required_number(regional_row, "regional_macro_stress_index")
    geopolitical_risk = _required_number(regional_row, "regional_geopolitical_risk_index")
    global_growth = _required_number(global_row, "realized_growth_pct")
    oil_yoy = _required_number(global_row, "oil_yoy_change_pct")

    maturity_gap = max(0.0, 1.0 - config.market_maturity)
    financing_pressure = (
        0.0018 * max(0.0, hy_spread - 350.0)
        + 0.22 * max(0.0, fci)
        + 0.012 * max(0.0, credit_stress - 35.0)
        + 0.008 * max(0.0, default_risk - 25.0)
    )
    capital_damage = (
        0.035 * max(0.0, macro_stress - 35.0)
        + 0.018
        * max(0.0, geopolitical_risk - 25.0)
        * config.geopolitical_sensitivity
    )
    global_common = _global_common_eps_shock(global_row)

    return {
        "regional_equity_eps_nominal_growth_contribution_pp": (
            template.nominal_growth_pass_through * (local_growth + local_inflation)
        ),
        "regional_equity_eps_industry_margin_contribution_pp": (
            template.margin_cycle_sensitivity
            * (
                0.55 * output_gap
                + 0.020 * (terms_of_trade - 50.0)
                - 0.025 * max(0.0, energy_cost - 50.0)
            )
        ),
        "regional_equity_eps_external_demand_contribution_pp": (
            template.external_demand_sensitivity
            * config.international_exposure
            * (global_growth - 2.0)
        ),
        "regional_equity_eps_commodity_producer_contribution_pp": (
            0.055
            * oil_yoy
            * template.commodity_producer_sensitivity
            * config.commodity_export_sensitivity
        ),
        "regional_equity_eps_energy_import_contribution_pp": (
            -0.045
            * oil_yoy
            * template.energy_import_sensitivity
            * config.energy_import_sensitivity
        ),
        "regional_equity_eps_financing_credit_contribution_pp": (
            -template.financing_sensitivity
            * config.credit_sensitivity
            * financing_pressure
        ),
        "regional_equity_eps_dilution_contribution_pp": -(
            template.dilution_drag_pct
            + 0.004 * max(0.0, hy_spread - 500.0) * maturity_gap
            + 0.012 * max(0.0, policy_uncertainty - 30.0) * maturity_gap
        ),
        "regional_equity_eps_capital_destruction_contribution_pp": (
            -template.capital_destruction_sensitivity * capital_damage
        ),
        "regional_equity_eps_global_common_contribution_pp": (
            config.asset_global_beta
            * template.global_eps_common_sensitivity
            * global_common
        ),
    }


def _pe_contributions(
    regional_row: Mapping[str, Any],
    global_row: Mapping[str, Any],
    config: _ResolvedRegionConfig,
    template: RegionalAssetTemplate,
    params: RegionalAssetV04Params,
) -> dict[str, float]:
    local_growth = _required_number(regional_row, "regional_gdp_growth_pct")
    potential_growth = _required_number(regional_row, "regional_potential_growth_pct")
    output_gap = _required_number(regional_row, "regional_output_gap_pct")
    real_10y = _required_number(regional_row, "regional_real_10y_yield_pct")
    hy_spread = _required_number(regional_row, "regional_hy_spread_bps")
    currency_yoy = _required_number(regional_row, "regional_currency_yoy_pct")
    geopolitical_risk = _required_number(regional_row, "regional_geopolitical_risk_index")
    policy_uncertainty = _required_number(regional_row, "regional_policy_uncertainty_index")
    risk_appetite = _required_number(regional_row, "regional_risk_appetite_index")
    macro_stress = _required_number(regional_row, "regional_macro_stress_index")
    liquidity = _required_number(regional_row, "regional_liquidity_index")
    global_growth = _required_number(global_row, "realized_growth_pct")
    global_output_gap = _required_number(global_row, "output_gap_pct")
    global_real_10y = _required_number(global_row, "global_real_10y_yield_pct")
    global_hy_spread = _required_number(global_row, "global_high_yield_spread_bps")
    global_liquidity = _required_number(global_row, "global_liquidity_index")
    global_risk_appetite = _required_number(global_row, "risk_appetite_index")
    global_financial_stress = _required_number(global_row, "financial_stress_index")
    global_pe = _required_number(global_row, "global_equity_valuation_pe")

    external_risk_load = (
        0.040 * abs(currency_yoy)
        + 0.020 * geopolitical_risk * config.geopolitical_sensitivity
        + 0.015 * policy_uncertainty
    )
    # The global PE soft anchor already prices the common rate, credit, liquidity,
    # risk-appetite and stress state. Local PE contributions therefore use regional
    # differentials, preventing the same global crisis from being charged twice.
    cycle_load = (
        (risk_appetite - global_risk_appetite)
        + 1.5 * (output_gap - global_output_gap)
        + 0.4 * (liquidity - global_liquidity)
    )
    local_growth_premium = (
        0.45 * (potential_growth - config.trend_growth_pct)
        + 0.30 * (local_growth - global_growth)
    )

    return {
        "regional_equity_pe_anchor": params.initial_pe,
        "regional_equity_pe_global_common_contribution": (
            config.asset_global_beta
            * template.global_pe_common_sensitivity
            * (global_pe - params.initial_pe)
        ),
        "regional_equity_pe_local_growth_contribution": (
            template.pe_growth_sensitivity * local_growth_premium
        ),
        "regional_equity_pe_real_rate_contribution": (
            -template.pe_real_rate_sensitivity * (real_10y - global_real_10y)
        ),
        "regional_equity_pe_credit_contribution": (
            -template.pe_credit_spread_sensitivity_per_bp
            * (hy_spread - global_hy_spread)
        ),
        "regional_equity_pe_institution_contribution": (
            -template.pe_institution_discount * (1.0 - config.market_maturity)
        ),
        "regional_equity_pe_external_risk_contribution": (
            -template.pe_external_risk_sensitivity * external_risk_load
        ),
        "regional_equity_pe_cycle_contribution": (
            template.pe_cycle_sensitivity * cycle_load
        ),
        "regional_equity_pe_event_contribution": (
            -template.pe_event_sensitivity
            * max(0.0, macro_stress - global_financial_stress)
        ),
    }


def _payout_target(
    regional_row: Mapping[str, Any],
    eps_growth_pct: float,
    config: _ResolvedRegionConfig,
    template: RegionalAssetTemplate,
) -> float:
    macro_stress = _required_number(regional_row, "regional_macro_stress_index")
    hy_spread = _required_number(regional_row, "regional_hy_spread_bps")
    maturity_adjustment = 8.0 * (config.market_maturity - 0.70)
    return (
        template.base_payout_ratio_pct
        + maturity_adjustment
        + 0.10 * max(0.0, eps_growth_pct)
        - template.payout_growth_opportunity_sensitivity
        * max(0.0, eps_growth_pct - 3.0)
        - template.payout_stress_sensitivity * max(0.0, macro_stress - 35.0)
        - 0.002 * max(0.0, hy_spread - 450.0)
    )


def _initial_candidate(
    config: _ResolvedRegionConfig,
    template: RegionalAssetTemplate,
    params: RegionalAssetV04Params,
) -> dict[str, Any]:
    candidate: dict[str, Any] = {
        field: 0.0 for field in REGIONAL_ASSET_V04_FIELDS
    }
    candidate.update(
        regional_asset_v04_param_version=REGIONAL_ASSET_V04_PARAM_VERSION,
        asset_accounting_contract_version=REGIONAL_ASSET_V04_INTERFACE_VERSION,
        regional_asset_template_id=template.template_id,
        regional_asset_global_weight=config.global_weight,
        regional_equity_initial_pe=params.initial_pe,
        regional_equity_eps_index=params.initial_eps_index,
        regional_equity_valuation_pe_raw=params.initial_pe,
        regional_equity_valuation_pe=params.initial_pe,
        regional_equity_pe_anchor=params.initial_pe,
        regional_equity_price_index=params.initial_price_index,
        regional_equity_payout_ratio_pct=params.initial_payout_ratio_pct,
        regional_equity_payout_target_pct=params.initial_payout_ratio_pct,
        regional_equity_total_return_index=params.initial_total_return_index,
        regional_sovereign_bond_duration_years=template.bond_duration_years,
        regional_sovereign_bond_total_return_index=(
            params.initial_bond_total_return_index
        ),
        regional_equity_eps_boundary_state="none",
        regional_equity_pe_boundary_state="none",
        regional_equity_payout_boundary_state="none",
    )
    return candidate


def _validate_candidate(candidate: Mapping[str, Any]) -> None:
    missing = [field for field in REGIONAL_ASSET_V04_FIELDS if field not in candidate]
    if missing:
        raise ValueError(f"regional asset candidate missing fields: {', '.join(missing)}")
    for field in REGIONAL_ASSET_V04_FIELDS:
        value = candidate[field]
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if not math.isfinite(float(value)):
                raise ValueError(f"candidate field {field} must be finite")


def simulate_regional_asset_v04_for_macro_path(
    regional_records: Sequence[Mapping[str, Any]],
    global_records: Sequence[Mapping[str, Any]],
    *,
    region_config: Mapping[str, Any] | Any,
    template: str | RegionalAssetTemplate | Mapping[str, Any] | None = None,
    params: RegionalAssetV04Params | None = None,
) -> list[dict[str, Any]]:
    """Build an isolated regional equity and local-currency sovereign-bond path.

    The function consumes explicit raw regional macro fields and merged A1a/A1b
    candidate rows. It never reads legacy regional asset return/index fields, never
    mutates inputs, and is not connected to the formal v0.15 orchestrator.
    """

    settings = params or RegionalAssetV04Params()
    validate_params(settings)
    config = _resolve_region_config(region_config)
    market_template = _resolve_template(config.region_id, template)
    validate_template(market_template)

    if not regional_records and not global_records:
        return []
    _validate_aligned_inputs(regional_records, global_records, config)
    if not regional_records:
        return []

    state = _RegionalAssetState(
        eps_index=settings.initial_eps_index,
        eps_growth_pct=0.0,
        valuation_pe=settings.initial_pe,
        price_index=settings.initial_price_index,
        total_return_index=settings.initial_total_return_index,
        payout_ratio_pct=settings.initial_payout_ratio_pct,
        bond_total_return_index=settings.initial_bond_total_return_index,
    )
    result: list[dict[str, Any]] = []

    for position, (regional_row, global_row) in enumerate(
        zip(regional_records, global_records)
    ):
        if position == 0:
            candidate = _initial_candidate(config, market_template, settings)
            _validate_candidate(candidate)
            result.append({**dict(regional_row), **candidate})
            continue

        eps_parts = _eps_contributions(
            regional_row, global_row, config, market_template
        )
        eps_raw = sum(eps_parts.values())
        eps_smoothed = (
            state.eps_growth_pct * (1.0 - settings.eps_smoothing)
            + eps_raw * settings.eps_smoothing
        )
        eps_smoothing_adjustment = eps_smoothed - eps_raw
        eps_boundary_state = _boundary_state(
            eps_smoothed,
            settings.min_eps_growth_pct,
            settings.max_eps_growth_pct,
        )
        bounded_eps_growth = _clamp(
            eps_smoothed,
            settings.min_eps_growth_pct,
            settings.max_eps_growth_pct,
        )
        proposed_eps_index = state.eps_index * (
            1.0 + bounded_eps_growth / 100.0
        )
        eps_index = max(settings.min_eps_index, proposed_eps_index)
        eps_growth = (eps_index / state.eps_index - 1.0) * 100.0
        eps_boundary_adjustment = eps_growth - eps_smoothed
        if proposed_eps_index < settings.min_eps_index:
            eps_boundary_state = "floor"

        pe_parts = _pe_contributions(
            regional_row,
            global_row,
            config,
            market_template,
            settings,
        )
        pe_raw = sum(pe_parts.values())
        pe_smoothed = (
            state.valuation_pe * (1.0 - settings.pe_smoothing)
            + pe_raw * settings.pe_smoothing
        )
        pe_smoothing_adjustment = pe_smoothed - pe_raw
        pe_boundary_state = _boundary_state(
            pe_smoothed, settings.min_pe, settings.max_pe
        )
        valuation_pe = _clamp(pe_smoothed, settings.min_pe, settings.max_pe)
        pe_boundary_adjustment = valuation_pe - pe_smoothed

        payout_target = _payout_target(
            regional_row, eps_growth, config, market_template
        )
        payout_smoothed = (
            state.payout_ratio_pct * (1.0 - settings.payout_smoothing)
            + payout_target * settings.payout_smoothing
        )
        payout_smoothing_adjustment = payout_smoothed - payout_target
        payout_boundary_state = _boundary_state(
            payout_smoothed,
            settings.min_payout_ratio_pct,
            settings.max_payout_ratio_pct,
        )
        payout_ratio = _clamp(
            payout_smoothed,
            settings.min_payout_ratio_pct,
            settings.max_payout_ratio_pct,
        )
        payout_boundary_adjustment = payout_ratio - payout_smoothed

        equity_returns = accounting.equity_return_breakdown(
            previous_price_index=state.price_index,
            previous_total_return_index=state.total_return_index,
            eps_index=eps_index,
            valuation_pe=valuation_pe,
            payout_ratio_pct=payout_ratio,
            initial_pe=settings.initial_pe,
        )
        eps_price_contribution = (eps_index / state.eps_index - 1.0) * 100.0
        pe_price_contribution = (valuation_pe / state.valuation_pe - 1.0) * 100.0
        interaction_contribution = (
            eps_price_contribution * pe_price_contribution / 100.0
        )

        current_yield = _required_number(regional_row, "regional_10y_yield_pct")
        previous_yield = _required_number(
            regional_records[position - 1], "regional_10y_yield_pct"
        )
        bond = accounting.sovereign_bond_return_breakdown(
            previous_yield_pct=previous_yield,
            current_yield_pct=current_yield,
            duration_years=market_template.bond_duration_years,
            convexity=0.0,
        )
        bond_index = accounting.compound_total_return_index(
            state.bond_total_return_index, bond.total_return_pct
        )
        yield_change = current_yield - previous_yield
        duration_price_contribution = -market_template.bond_duration_years * yield_change

        candidate = {
            "regional_asset_v04_param_version": REGIONAL_ASSET_V04_PARAM_VERSION,
            "asset_accounting_contract_version": REGIONAL_ASSET_V04_INTERFACE_VERSION,
            "regional_asset_template_id": market_template.template_id,
            "regional_asset_global_weight": config.global_weight,
            "regional_equity_initial_pe": settings.initial_pe,
            "regional_equity_eps_index": eps_index,
            "regional_equity_eps_growth_raw_pct": eps_raw,
            "regional_equity_eps_growth_pct": eps_growth,
            **eps_parts,
            "regional_equity_eps_smoothing_adjustment_pp": eps_smoothing_adjustment,
            "regional_equity_eps_boundary_adjustment_pp": eps_boundary_adjustment,
            "regional_equity_eps_boundary_state": eps_boundary_state,
            "regional_equity_eps_growth_raw_identity_residual": (
                eps_raw - sum(eps_parts.values())
            ),
            "regional_equity_eps_growth_final_identity_residual": (
                eps_growth
                - eps_raw
                - eps_smoothing_adjustment
                - eps_boundary_adjustment
            ),
            "regional_equity_valuation_pe_raw": pe_raw,
            "regional_equity_valuation_pe": valuation_pe,
            **pe_parts,
            "regional_equity_pe_smoothing_adjustment": pe_smoothing_adjustment,
            "regional_equity_pe_boundary_adjustment": pe_boundary_adjustment,
            "regional_equity_pe_boundary_state": pe_boundary_state,
            "regional_equity_pe_raw_identity_residual": (
                pe_raw - sum(pe_parts.values())
            ),
            "regional_equity_pe_final_identity_residual": (
                valuation_pe
                - pe_raw
                - pe_smoothing_adjustment
                - pe_boundary_adjustment
            ),
            "regional_equity_price_index": equity_returns.price_index,
            "regional_equity_price_return_pct": equity_returns.price_return_pct,
            "regional_equity_payout_ratio_pct": payout_ratio,
            "regional_equity_payout_target_pct": payout_target,
            "regional_equity_payout_smoothing_adjustment_pct": (
                payout_smoothing_adjustment
            ),
            "regional_equity_payout_boundary_adjustment_pct": (
                payout_boundary_adjustment
            ),
            "regional_equity_payout_boundary_state": payout_boundary_state,
            "regional_equity_dividend_yield_pct": equity_returns.dividend_yield_pct,
            "regional_equity_total_return_pct": equity_returns.total_return_pct,
            "regional_equity_total_return_index": equity_returns.total_return_index,
            "regional_equity_eps_price_return_contribution_pct": (
                eps_price_contribution
            ),
            "regional_equity_pe_price_return_contribution_pct": (
                pe_price_contribution
            ),
            "regional_equity_eps_pe_interaction_price_return_contribution_pct": (
                interaction_contribution
            ),
            "regional_equity_price_identity_residual": (
                equity_returns.price_index
                - eps_index * valuation_pe / settings.initial_pe
            ),
            "regional_equity_price_return_identity_residual": (
                equity_returns.price_return_pct
                - eps_price_contribution
                - pe_price_contribution
                - interaction_contribution
            ),
            "regional_equity_total_return_identity_residual": (
                equity_returns.total_return_pct
                - equity_returns.price_return_pct
                - equity_returns.dividend_yield_pct
            ),
            "regional_sovereign_bond_duration_years": (
                market_template.bond_duration_years
            ),
            "regional_sovereign_bond_yield_change_pct": yield_change,
            "regional_sovereign_bond_duration_price_contribution_pct": (
                duration_price_contribution
            ),
            "regional_sovereign_bond_price_return_pct": bond.price_return_pct,
            "regional_sovereign_bond_carry_pct": bond.carry_pct,
            "regional_sovereign_bond_total_return_pct": bond.total_return_pct,
            "regional_sovereign_bond_total_return_index": bond_index,
            "regional_sovereign_bond_price_return_identity_residual": (
                bond.price_return_pct - duration_price_contribution
            ),
            "regional_sovereign_bond_total_return_identity_residual": (
                bond.total_return_pct - bond.price_return_pct - bond.carry_pct
            ),
        }
        _validate_candidate(candidate)
        result.append({**dict(regional_row), **candidate})

        state.eps_index = eps_index
        state.eps_growth_pct = eps_growth
        state.valuation_pe = valuation_pe
        state.price_index = equity_returns.price_index
        state.total_return_index = equity_returns.total_return_index
        state.payout_ratio_pct = payout_ratio
        state.bond_total_return_index = bond_index

    return result


def regional_asset_soft_reconciliation_v04(
    regional_paths: Mapping[str, Sequence[Mapping[str, Any]]],
    global_records: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Return diagnostic weighted regional/global gaps without forcing equality."""

    if not isinstance(regional_paths, Mapping) or not regional_paths:
        raise ValueError("regional_paths must be a non-empty mapping")
    expected_regions = set(REGION_TEMPLATE_BY_REGION)
    actual_regions = set(regional_paths)
    if actual_regions != expected_regions:
        missing = sorted(expected_regions - actual_regions)
        extra = sorted(actual_regions - expected_regions)
        details = []
        if missing:
            details.append(f"missing={','.join(missing)}")
        if extra:
            details.append(f"extra={','.join(extra)}")
        raise ValueError("regional_paths must cover all 14 regions: " + "; ".join(details))

    _validate_path_records(
        global_records,
        label="global_records",
        required_fields=GLOBAL_RECONCILIATION_REQUIRED_FIELDS,
    )
    path_length = len(global_records)
    if path_length == 0:
        raise ValueError("global_records must be non-empty")

    region_weights: dict[str, float] = {}
    for region_id, rows in regional_paths.items():
        _validate_path_records(
            rows,
            label=f"regional_paths[{region_id}]",
            required_fields=(
                "year_index",
                "regional_global_weight",
                "regional_equity_eps_index",
                "regional_equity_valuation_pe",
                "regional_equity_price_return_pct",
                "regional_equity_total_return_pct",
                "regional_sovereign_bond_total_return_pct",
            ),
        )
        if len(rows) != path_length:
            raise ValueError("regional path and global_records length mismatch")
        for position, row in enumerate(rows):
            if str(row.get("region_id", "")) != region_id:
                raise ValueError(
                    f"regional_paths[{region_id}][{position}].region_id mismatch"
                )
        first_weight = _required_number(rows[0], "regional_global_weight")
        if first_weight <= 0.0:
            raise ValueError("regional_global_weight must be positive")
        for row in rows[1:]:
            if not math.isclose(
                _required_number(row, "regional_global_weight"),
                first_weight,
                rel_tol=0.0,
                abs_tol=1e-12,
            ):
                raise ValueError("regional_global_weight must be constant within a path")
        region_weights[region_id] = first_weight

    weight_sum = sum(region_weights.values())
    if not math.isfinite(weight_sum) or weight_sum <= 0.0:
        raise ValueError("regional weights must have a positive finite sum")

    result: list[dict[str, Any]] = []
    for position, global_row in enumerate(global_records):
        def weighted(field: str) -> float:
            return sum(
                region_weights[region_id]
                * _required_number(regional_paths[region_id][position], field)
                for region_id in REGION_TEMPLATE_BY_REGION
            ) / weight_sum

        weighted_eps = weighted("regional_equity_eps_index")
        weighted_pe = weighted("regional_equity_valuation_pe")
        weighted_price_return = weighted("regional_equity_price_return_pct")
        weighted_total_return = weighted("regional_equity_total_return_pct")
        weighted_bond_return = weighted(
            "regional_sovereign_bond_total_return_pct"
        )
        global_eps = _required_number(global_row, "global_equity_eps_index")
        global_pe = _required_number(global_row, "global_equity_valuation_pe")
        global_price_return = _required_number(
            global_row, "global_equity_price_return_pct"
        )
        global_total_return = _required_number(
            global_row, "global_equity_total_return_pct"
        )
        global_bond_return = _required_number(
            global_row, "global_sovereign_bond_total_return_pct"
        )

        diagnostic = {
            "year_index": position,
            "regional_asset_reconciliation_scope": "diagnostic_only",
            "regional_asset_reconciliation_region_count": len(regional_paths),
            "regional_asset_reconciliation_weight_sum": weight_sum,
            "regional_asset_reconciliation_weight_normalization_gap": (
                weight_sum - 1.0
            ),
            "regional_asset_weighted_equity_eps_index": weighted_eps,
            "global_equity_eps_index_reference": global_eps,
            "regional_asset_equity_eps_gap_index_points": weighted_eps - global_eps,
            "regional_asset_weighted_equity_valuation_pe": weighted_pe,
            "global_equity_valuation_pe_reference": global_pe,
            "regional_asset_equity_pe_gap": weighted_pe - global_pe,
            "regional_asset_weighted_equity_price_return_pct": (
                weighted_price_return
            ),
            "global_equity_price_return_pct_reference": global_price_return,
            "regional_asset_equity_price_return_gap_pct": (
                weighted_price_return - global_price_return
            ),
            "regional_asset_weighted_equity_total_return_pct": (
                weighted_total_return
            ),
            "global_equity_total_return_pct_reference": global_total_return,
            "regional_asset_equity_total_return_gap_pct": (
                weighted_total_return - global_total_return
            ),
            "regional_asset_weighted_sovereign_bond_total_return_pct": (
                weighted_bond_return
            ),
            "global_sovereign_bond_total_return_pct_reference": (
                global_bond_return
            ),
            "regional_asset_sovereign_bond_total_return_gap_pct": (
                weighted_bond_return - global_bond_return
            ),
            "regional_asset_equity_gap_source": (
                "local_eps_pe_payout_industry_and_listing_mix"
            ),
            "regional_asset_bond_gap_source": (
                "local_yield_duration_and_local_currency_scope"
            ),
        }
        for field in RECONCILIATION_NUMERIC_FIELDS:
            if not math.isfinite(float(diagnostic[field])):
                raise ValueError(f"reconciliation field {field} must be finite")
        result.append(diagnostic)

    return result
