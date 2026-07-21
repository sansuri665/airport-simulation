from __future__ import annotations

from importlib import import_module

_SIBLING_PREFIX = f"{__package__}." if __package__ else ""
simulation_utils = import_module(f"{_SIBLING_PREFIX}simulation_utils")

clamp = simulation_utils.clamp
resolve_seeds = simulation_utils.resolve_seeds
round_record = simulation_utils.round_record

import argparse
import hashlib
import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

dollar_liquidity_layer = import_module(f"{_SIBLING_PREFIX}global_dollar_liquidity_layer_sim")
inflation_layer = import_module(f"{_SIBLING_PREFIX}global_inflation_annual_sim")
feedback_layer = import_module(f"{_SIBLING_PREFIX}global_macro_feedback_calibration_sim")
policy_rate_layer = import_module(f"{_SIBLING_PREFIX}global_policy_rate_layer_sim")
yield_curve_layer = import_module(f"{_SIBLING_PREFIX}global_yield_curve_layer_sim")

DollarLiquidityParams = dollar_liquidity_layer.DollarLiquidityParams
InflationParams = inflation_layer.InflationParams
as_float = inflation_layer.as_float
MacroFeedbackParams = feedback_layer.MacroFeedbackParams
annotate_feedback_records = feedback_layer.annotate_feedback_records
blend_feedback_paths = feedback_layer.blend_feedback_paths
calibrated_asset_params = feedback_layer.calibrated_asset_params
calibrated_credit_params = feedback_layer.calibrated_credit_params
calibrated_gdp_params = feedback_layer.calibrated_gdp_params
calibrated_oil_params = feedback_layer.calibrated_oil_params
convergence_summary = feedback_layer.convergence_summary
derive_feedback_path = feedback_layer.derive_feedback_path
run_convergence_aware_feedback_loop = feedback_layer.run_convergence_aware_feedback_loop
run_full_chain = feedback_layer.run_full_chain
smooth = feedback_layer.smooth
write_csv = feedback_layer.write_csv
write_json = feedback_layer.write_json
PolicyRateParams = policy_rate_layer.PolicyRateParams
YieldCurveParams = yield_curve_layer.YieldCurveParams


REGIONAL_MACRO_PARAM_VERSION = "regional-macro-layer-v0.3"
REGIONAL_MACRO_INTERFACE_VERSION = "regional-macro-interface-v0.3"
REGIONAL_BRANCH_TRANSMISSION_VERSION = "regional-branch-transmission-v0.1"
REGIONAL_STRUCTURAL_SEED_VERSION = "regional-structural-seed-v0.1"

# Published hard bounds shared by the raw regional layer and the reconciliation
# layer. Policy-rate bounds remain region-specific and live on RegionalMacroParams.
REGIONAL_RECONCILED_FIELD_BOUNDS: dict[str, tuple[float, float]] = {
    "regional_headline_inflation_pct": (-1.0, 8.8),
    "regional_core_inflation_pct": (-0.2, 6.8),
    "regional_10y_yield_pct": (0.05, 11.0),
    "regional_macro_stress_index": (0.0, 100.0),
    "regional_energy_cost_pressure_index": (0.0, 100.0),
    "regional_equity_valuation_pe": (7.0, 34.0),
    "regional_hy_spread_bps": (150.0, 2_200.0),
    "regional_ig_spread_bps": (55.0, 620.0),
    "regional_equity_return_pct": (-42.0, 48.0),
}


REGIONAL_MACRO_FIELDS = [
    "regional_macro_param_version",
    "regional_macro_interface_version",
    "region_id",
    "region_name",
    "regional_reconciliation_scope",
    "year_index",
    "year",
    "seed",
    "regional_global_weight",
    "regional_structural_seed_version",
    "regional_seed_potential_enabled",
    "regional_seed_potential_template_id",
    "regional_seed_primary_theme",
    "regional_seed_secondary_theme",
    "regional_seed_structural_score",
    "regional_seed_theme_score",
    "regional_seed_momentum_label",
    "regional_seed_annual_growth_bias_pct",
    "regional_seed_effect_release_pct",
    "regional_seed_effective_growth_bias_pct",
    "regional_seed_aviation_propensity_bias_pct",
    "regional_seed_investment_cycle_bias_pct",
    "regional_seed_openness_bias_pct",
    "regional_seed_demand_multiplier",
    "regional_reconciliation_pass",
    "regional_reconciliation_converged",
    "regional_reconciliation_adjustment_index",
    "regional_gdp_index",
    "regional_gdp_growth_pct",
    "regional_potential_growth_pct",
    "regional_output_gap_pct",
    "regional_financial_stress_index",
    "regional_growth_regime",
    "regional_headline_inflation_pct",
    "regional_core_inflation_pct",
    "regional_energy_inflation_pct",
    "regional_import_inflation_pct",
    "regional_inflation_expectation_pct",
    "regional_inflation_regime",
    "regional_income_index",
    "real_income_growth_pct",
    "household_consumption_power_index",
    "consumer_confidence_index",
    "regional_policy_rate_pct",
    "regional_real_policy_rate_pct",
    "regional_10y_yield_pct",
    "regional_real_10y_yield_pct",
    "regional_term_spread_pct",
    "regional_financial_conditions_index",
    "regional_currency_index",
    "regional_currency_yoy_pct",
    "currency_pressure_index",
    "fx_volatility_index",
    "regional_liquidity_index",
    "regional_risk_appetite_index",
    "regional_ig_spread_bps",
    "regional_hy_spread_bps",
    "regional_credit_availability_index",
    "regional_default_risk_index",
    "regional_credit_stress_index",
    "regional_equity_index",
    "regional_equity_return_pct",
    "regional_equity_valuation_pe",
    "regional_bond_index",
    "regional_bond_return_pct",
    "regional_wealth_effect_index",
    "regional_energy_cost_pressure_index",
    "regional_terms_of_trade_index",
    "regional_commodity_pressure_index",
    "regional_macro_stress_index",
    "regional_policy_uncertainty_index",
    "regional_geopolitical_risk_index",
    "regional_macro_regime",
    "regional_branch_transmission_version",
    "branch_scenario_id",
    "branch_scenario_label",
    "branch_scenario_state",
    "branch_source_year",
    "branch_impact_years",
    "branch_tail_years",
    "branch_year_in_effect",
    "branch_effect_phase",
    "regional_branch_transmission_active",
    "regional_branch_exposure_index",
    "regional_branch_relative_exposure_index",
    "regional_branch_strength_index",
    "regional_branch_growth_impulse_pct",
    "regional_branch_inflation_impulse_pct",
    "regional_branch_policy_impulse_pct",
    "regional_branch_credit_impulse_bps",
    "regional_branch_fx_pressure_impulse",
    "regional_branch_energy_impulse",
    "regional_branch_liquidity_impulse",
    "regional_branch_asset_impulse_pct",
    "regional_branch_confidence_impulse",
    "regional_branch_tail_scarring_index",
    "global_growth_anchor_pct",
    "global_output_gap_anchor_pct",
    "global_inflation_anchor_pct",
    "global_core_inflation_anchor_pct",
    "global_policy_anchor_pct",
    "global_10y_anchor_pct",
    "global_hy_anchor_bps",
    "global_equity_return_anchor_pct",
    "global_equity_valuation_pe_anchor",
    "growth_reconciliation_adjustment_pct",
    "inflation_reconciliation_adjustment_pct",
    "rate_reconciliation_adjustment_pct",
    "credit_reconciliation_adjustment_bps",
    "equity_reconciliation_adjustment_pct",
]


@dataclass(frozen=True)
class RegionalMacroParams:
    region_id: str = "north_america"
    region_name: str = "北美"
    global_weight: float = 0.285
    trend_growth_pct: float = 1.85
    income_level_index: float = 88.0
    market_maturity: float = 0.93
    domestic_demand_weight: float = 0.82
    international_exposure: float = 0.42
    tourism_exposure: float = 0.30
    business_exposure: float = 0.72
    oil_sensitivity: float = 0.56
    dollar_sensitivity: float = -0.12
    credit_sensitivity: float = 0.94
    equity_wealth_sensitivity: float = 1.18
    policy_rate_sensitivity: float = 1.12
    geopolitical_sensitivity: float = 0.34
    capacity_constraint: float = 0.18
    shock_volatility: float = 0.26
    reconciliation_sensitivity: float = 0.82
    potential_growth_floor_pct: float = 0.45
    potential_growth_ceiling_pct: float = 3.35
    raw_growth_floor_pct: float = -4.60
    raw_growth_ceiling_pct: float = 5.40
    growth_floor_pct: float = -4.80
    growth_ceiling_pct: float = 5.60
    output_gap_floor_pct: float = -8.00
    output_gap_ceiling_pct: float = 5.50
    inflation_anchor_pct: float = 2.28
    core_inflation_anchor_pct: float = 2.18
    policy_global_beta: float = 1.00
    policy_neutral_rate_pct: float = 3.10
    policy_floor_pct: float = -0.20
    policy_ceiling_pct: float = 9.50
    rate_anchor_weight: float = 1.00
    long_rate_global_beta: float = 1.00
    long_rate_neutral_pct: float = 3.70
    currency_dollar_beta: float = 0.84
    fx_management_strength: float = 0.00
    credit_global_beta: float = 0.91
    ig_global_beta: float = 0.94
    asset_global_beta: float = 0.72
    bond_global_beta: float = 0.82
    policy_support_sensitivity: float = 0.00
    infrastructure_sensitivity: float = 0.00
    energy_import_sensitivity: float = 0.56
    commodity_export_sensitivity: float = 0.72


@dataclass(frozen=True)
class RegionalSeedPotentialParams:
    template_id: str
    primary_theme: str
    secondary_theme: str
    annual_growth_bias_floor_pct: float
    annual_growth_bias_ceiling_pct: float
    aviation_propensity_bias_floor_pct: float
    aviation_propensity_bias_ceiling_pct: float
    investment_cycle_bias_floor_pct: float
    investment_cycle_bias_ceiling_pct: float
    openness_bias_floor_pct: float
    openness_bias_ceiling_pct: float
    release_start_year_index: float = 4.0
    full_effect_year_index: float = 34.0
    local_weight: float = 0.58
    primary_theme_weight: float = 0.30
    secondary_theme_weight: float = 0.12


@dataclass(frozen=True)
class BranchTransmissionProfile:
    label: str
    exposure_key: str
    growth_pct: float
    inflation_pct: float
    policy_pct: float
    credit_bps: float
    fx_pressure: float
    energy_index: float
    liquidity_index: float
    asset_return_pct: float
    confidence_index: float
    stress_index: float
    tail_scarring_index: float


BRANCH_TRANSMISSION_PROFILES = {
    "false_dawn": BranchTransmissionProfile(
        label="虚假黎明",
        exposure_key="credit_crunch",
        growth_pct=-0.85,
        inflation_pct=-0.12,
        policy_pct=-0.10,
        credit_bps=58.0,
        fx_pressure=2.2,
        energy_index=-1.4,
        liquidity_index=-1.8,
        asset_return_pct=-3.6,
        confidence_index=-4.2,
        stress_index=6.5,
        tail_scarring_index=7.0,
    ),
    "policy_mistake_tightening": BranchTransmissionProfile(
        label="政策失误：过早收紧",
        exposure_key="policy_mistake",
        growth_pct=-0.62,
        inflation_pct=-0.16,
        policy_pct=0.36,
        credit_bps=38.0,
        fx_pressure=1.6,
        energy_index=-0.8,
        liquidity_index=-2.6,
        asset_return_pct=-2.8,
        confidence_index=-3.4,
        stress_index=4.8,
        tail_scarring_index=4.2,
    ),
    "policy_behind_curve": BranchTransmissionProfile(
        label="政策失误：落后曲线",
        exposure_key="stagflation",
        growth_pct=-0.28,
        inflation_pct=0.62,
        policy_pct=0.32,
        credit_bps=28.0,
        fx_pressure=1.2,
        energy_index=2.0,
        liquidity_index=-1.2,
        asset_return_pct=-1.6,
        confidence_index=-2.0,
        stress_index=3.4,
        tail_scarring_index=2.5,
    ),
    "credit_accident": BranchTransmissionProfile(
        label="信用事故",
        exposure_key="credit_crunch",
        growth_pct=-1.00,
        inflation_pct=-0.22,
        policy_pct=-0.22,
        credit_bps=96.0,
        fx_pressure=3.4,
        energy_index=-1.6,
        liquidity_index=-3.4,
        asset_return_pct=-5.2,
        confidence_index=-5.4,
        stress_index=10.5,
        tail_scarring_index=10.0,
    ),
    "bank_lending_trap": BranchTransmissionProfile(
        label="银行惜贷循环",
        exposure_key="credit_crunch",
        growth_pct=-0.72,
        inflation_pct=-0.18,
        policy_pct=-0.18,
        credit_bps=66.0,
        fx_pressure=1.8,
        energy_index=-0.9,
        liquidity_index=-1.4,
        asset_return_pct=-3.2,
        confidence_index=-4.6,
        stress_index=6.8,
        tail_scarring_index=9.0,
    ),
    "dollar_squeeze_escalation": BranchTransmissionProfile(
        label="美元挤兑升级",
        exposure_key="dollar_squeeze",
        growth_pct=-0.55,
        inflation_pct=0.10,
        policy_pct=0.06,
        credit_bps=62.0,
        fx_pressure=5.2,
        energy_index=0.7,
        liquidity_index=-4.4,
        asset_return_pct=-3.8,
        confidence_index=-3.2,
        stress_index=7.8,
        tail_scarring_index=4.5,
    ),
    "energy_shock_escalation": BranchTransmissionProfile(
        label="能源冲击升级",
        exposure_key="energy_crisis",
        growth_pct=-0.52,
        inflation_pct=0.78,
        policy_pct=0.30,
        credit_bps=34.0,
        fx_pressure=1.4,
        energy_index=8.5,
        liquidity_index=-1.2,
        asset_return_pct=-2.5,
        confidence_index=-3.5,
        stress_index=4.8,
        tail_scarring_index=3.4,
    ),
    "bond_market_accident": BranchTransmissionProfile(
        label="债券市场失控",
        exposure_key="policy_mistake",
        growth_pct=-0.58,
        inflation_pct=0.18,
        policy_pct=0.34,
        credit_bps=46.0,
        fx_pressure=2.0,
        energy_index=0.4,
        liquidity_index=-3.0,
        asset_return_pct=-4.2,
        confidence_index=-3.8,
        stress_index=8.0,
        tail_scarring_index=3.5,
    ),
    "soft_landing_success": BranchTransmissionProfile(
        label="软着陆成功",
        exposure_key="risk_asset_bull",
        growth_pct=0.34,
        inflation_pct=-0.16,
        policy_pct=-0.10,
        credit_bps=-32.0,
        fx_pressure=-0.8,
        energy_index=-0.5,
        liquidity_index=1.5,
        asset_return_pct=2.6,
        confidence_index=3.4,
        stress_index=-3.4,
        tail_scarring_index=-2.0,
    ),
    "liquidity_bubble": BranchTransmissionProfile(
        label="流动性牛市脱实向虚",
        exposure_key="risk_asset_bull",
        growth_pct=0.16,
        inflation_pct=0.08,
        policy_pct=0.05,
        credit_bps=-18.0,
        fx_pressure=-1.0,
        energy_index=0.3,
        liquidity_index=4.0,
        asset_return_pct=4.2,
        confidence_index=2.2,
        stress_index=-1.4,
        tail_scarring_index=1.5,
    ),
    "refinancing_wall": BranchTransmissionProfile(
        label="再融资墙",
        exposure_key="credit_crunch",
        growth_pct=-0.70,
        inflation_pct=-0.14,
        policy_pct=-0.12,
        credit_bps=74.0,
        fx_pressure=2.0,
        energy_index=-0.8,
        liquidity_index=-1.8,
        asset_return_pct=-3.7,
        confidence_index=-4.0,
        stress_index=7.6,
        tail_scarring_index=8.0,
    ),
    "demand_destruction_disinflation": BranchTransmissionProfile(
        label="需求破坏式降通胀",
        exposure_key="credit_crunch",
        growth_pct=-0.78,
        inflation_pct=-0.62,
        policy_pct=-0.24,
        credit_bps=36.0,
        fx_pressure=1.0,
        energy_index=-4.2,
        liquidity_index=0.6,
        asset_return_pct=-2.4,
        confidence_index=-4.4,
        stress_index=4.8,
        tail_scarring_index=5.0,
    ),
    "stagflation_trap": BranchTransmissionProfile(
        label="滞胀陷阱",
        exposure_key="stagflation",
        growth_pct=-0.62,
        inflation_pct=0.72,
        policy_pct=0.28,
        credit_bps=48.0,
        fx_pressure=2.0,
        energy_index=4.6,
        liquidity_index=-1.8,
        asset_return_pct=-3.0,
        confidence_index=-4.2,
        stress_index=6.0,
        tail_scarring_index=5.2,
    ),
    "risk_asset_bull_fragility": BranchTransmissionProfile(
        label="风险资产牛市脆弱化",
        exposure_key="risk_asset_bull",
        growth_pct=0.08,
        inflation_pct=0.04,
        policy_pct=0.03,
        credit_bps=-12.0,
        fx_pressure=-0.6,
        energy_index=0.2,
        liquidity_index=2.8,
        asset_return_pct=3.0,
        confidence_index=1.6,
        stress_index=-0.8,
        tail_scarring_index=1.0,
    ),
}


BRANCH_EXPOSURE_BY_REGION = {
    "china_mainland": {
        "energy_crisis": 1.05,
        "dollar_squeeze": 0.85,
        "credit_crunch": 0.95,
        "policy_mistake": 1.10,
        "risk_asset_bull": 0.80,
        "stagflation": 1.00,
        "commodity_supercycle": 0.95,
    },
    "hk_macao_taiwan": {
        "energy_crisis": 1.10,
        "dollar_squeeze": 0.95,
        "credit_crunch": 1.05,
        "policy_mistake": 1.00,
        "risk_asset_bull": 1.10,
        "stagflation": 1.00,
        "commodity_supercycle": 0.85,
    },
    "japan_korea": {
        "energy_crisis": 1.35,
        "dollar_squeeze": 0.95,
        "credit_crunch": 0.95,
        "policy_mistake": 0.90,
        "risk_asset_bull": 0.95,
        "stagflation": 1.15,
        "commodity_supercycle": 0.70,
    },
    "southeast_asia": {
        "energy_crisis": 1.10,
        "dollar_squeeze": 1.20,
        "credit_crunch": 1.05,
        "policy_mistake": 1.00,
        "risk_asset_bull": 1.05,
        "stagflation": 1.05,
        "commodity_supercycle": 0.95,
    },
    "south_asia_india": {
        "energy_crisis": 1.30,
        "dollar_squeeze": 1.35,
        "credit_crunch": 1.10,
        "policy_mistake": 1.00,
        "risk_asset_bull": 0.85,
        "stagflation": 1.20,
        "commodity_supercycle": 0.80,
    },
    "middle_east_gulf": {
        "energy_crisis": 0.65,
        "dollar_squeeze": 0.75,
        "credit_crunch": 0.90,
        "policy_mistake": 0.80,
        "risk_asset_bull": 1.00,
        "stagflation": 0.85,
        "commodity_supercycle": 1.45,
    },
    "central_asia_turkey_eurasia": {
        "energy_crisis": 1.05,
        "dollar_squeeze": 1.30,
        "credit_crunch": 1.15,
        "policy_mistake": 1.10,
        "risk_asset_bull": 0.75,
        "stagflation": 1.20,
        "commodity_supercycle": 1.15,
    },
    "west_north_europe": {
        "energy_crisis": 1.45,
        "dollar_squeeze": 0.90,
        "credit_crunch": 1.00,
        "policy_mistake": 0.95,
        "risk_asset_bull": 0.95,
        "stagflation": 1.25,
        "commodity_supercycle": 0.70,
    },
    "south_east_europe_mediterranean": {
        "energy_crisis": 1.35,
        "dollar_squeeze": 1.05,
        "credit_crunch": 1.10,
        "policy_mistake": 1.00,
        "risk_asset_bull": 0.85,
        "stagflation": 1.25,
        "commodity_supercycle": 0.75,
    },
    "north_america": {
        "energy_crisis": 0.70,
        "dollar_squeeze": 0.55,
        "credit_crunch": 1.10,
        "policy_mistake": 1.15,
        "risk_asset_bull": 1.25,
        "stagflation": 0.95,
        "commodity_supercycle": 0.95,
    },
    "latin_america_caribbean": {
        "energy_crisis": 0.95,
        "dollar_squeeze": 1.35,
        "credit_crunch": 1.20,
        "policy_mistake": 1.10,
        "risk_asset_bull": 0.90,
        "stagflation": 1.15,
        "commodity_supercycle": 1.15,
    },
    "oceania": {
        "energy_crisis": 0.90,
        "dollar_squeeze": 0.85,
        "credit_crunch": 0.90,
        "policy_mistake": 0.90,
        "risk_asset_bull": 1.00,
        "stagflation": 0.90,
        "commodity_supercycle": 1.25,
    },
    "north_africa": {
        "energy_crisis": 1.20,
        "dollar_squeeze": 1.25,
        "credit_crunch": 1.15,
        "policy_mistake": 1.05,
        "risk_asset_bull": 0.75,
        "stagflation": 1.20,
        "commodity_supercycle": 0.90,
    },
    "sub_saharan_africa": {
        "energy_crisis": 1.15,
        "dollar_squeeze": 1.45,
        "credit_crunch": 1.30,
        "policy_mistake": 1.10,
        "risk_asset_bull": 0.70,
        "stagflation": 1.25,
        "commodity_supercycle": 1.05,
    },
}


REGIONAL_SEED_POTENTIALS = {
    "north_america": RegionalSeedPotentialParams(
        template_id="north_america_tech_finance_cycle_seed_v1",
        primary_theme="north_america_tech_cycle",
        secondary_theme="dollar_financial_architecture",
        annual_growth_bias_floor_pct=-0.95,
        annual_growth_bias_ceiling_pct=1.15,
        aviation_propensity_bias_floor_pct=-10.0,
        aviation_propensity_bias_ceiling_pct=12.0,
        investment_cycle_bias_floor_pct=-8.0,
        investment_cycle_bias_ceiling_pct=10.0,
        openness_bias_floor_pct=-6.0,
        openness_bias_ceiling_pct=6.0,
    ),
    "china_mainland": RegionalSeedPotentialParams(
        template_id="china_productivity_consumption_upgrade_seed_v1",
        primary_theme="china_productivity_cycle",
        secondary_theme="east_asia_supply_chain",
        annual_growth_bias_floor_pct=-1.25,
        annual_growth_bias_ceiling_pct=1.35,
        aviation_propensity_bias_floor_pct=-13.0,
        aviation_propensity_bias_ceiling_pct=16.0,
        investment_cycle_bias_floor_pct=-12.0,
        investment_cycle_bias_ceiling_pct=15.0,
        openness_bias_floor_pct=-11.0,
        openness_bias_ceiling_pct=10.0,
    ),
    "west_north_europe": RegionalSeedPotentialParams(
        template_id="west_north_europe_reindustrialization_seed_v1",
        primary_theme="europe_resilience_cycle",
        secondary_theme="green_industrial_policy",
        annual_growth_bias_floor_pct=-0.90,
        annual_growth_bias_ceiling_pct=1.10,
        aviation_propensity_bias_floor_pct=-9.0,
        aviation_propensity_bias_ceiling_pct=11.0,
        investment_cycle_bias_floor_pct=-8.0,
        investment_cycle_bias_ceiling_pct=11.0,
        openness_bias_floor_pct=-8.0,
        openness_bias_ceiling_pct=7.0,
    ),
    "japan_korea": RegionalSeedPotentialParams(
        template_id="japan_korea_advanced_industry_seed_v1",
        primary_theme="advanced_industry_cycle",
        secondary_theme="east_asia_supply_chain",
        annual_growth_bias_floor_pct=-0.70,
        annual_growth_bias_ceiling_pct=0.90,
        aviation_propensity_bias_floor_pct=-8.0,
        aviation_propensity_bias_ceiling_pct=10.0,
        investment_cycle_bias_floor_pct=-7.0,
        investment_cycle_bias_ceiling_pct=9.0,
        openness_bias_floor_pct=-8.0,
        openness_bias_ceiling_pct=8.0,
    ),
    "southeast_asia": RegionalSeedPotentialParams(
        template_id="southeast_asia_supply_chain_tourism_seed_v1",
        primary_theme="southeast_asia_supply_chain",
        secondary_theme="tourism_services_cycle",
        annual_growth_bias_floor_pct=-1.25,
        annual_growth_bias_ceiling_pct=1.55,
        aviation_propensity_bias_floor_pct=-15.0,
        aviation_propensity_bias_ceiling_pct=20.0,
        investment_cycle_bias_floor_pct=-13.0,
        investment_cycle_bias_ceiling_pct=17.0,
        openness_bias_floor_pct=-13.0,
        openness_bias_ceiling_pct=17.0,
    ),
    "south_asia_india": RegionalSeedPotentialParams(
        template_id="south_asia_urbanization_demographics_seed_v1",
        primary_theme="south_asia_urbanization",
        secondary_theme="services_export_cycle",
        annual_growth_bias_floor_pct=-1.45,
        annual_growth_bias_ceiling_pct=1.70,
        aviation_propensity_bias_floor_pct=-16.0,
        aviation_propensity_bias_ceiling_pct=22.0,
        investment_cycle_bias_floor_pct=-15.0,
        investment_cycle_bias_ceiling_pct=20.0,
        openness_bias_floor_pct=-11.0,
        openness_bias_ceiling_pct=13.0,
    ),
    "hk_macao_taiwan": RegionalSeedPotentialParams(
        template_id="hk_macao_taiwan_gateway_finance_seed_v1",
        primary_theme="east_asia_gateway_cycle",
        secondary_theme="china_productivity_cycle",
        annual_growth_bias_floor_pct=-0.85,
        annual_growth_bias_ceiling_pct=0.95,
        aviation_propensity_bias_floor_pct=-12.0,
        aviation_propensity_bias_ceiling_pct=13.0,
        investment_cycle_bias_floor_pct=-8.0,
        investment_cycle_bias_ceiling_pct=9.0,
        openness_bias_floor_pct=-14.0,
        openness_bias_ceiling_pct=13.0,
    ),
    "middle_east_gulf": RegionalSeedPotentialParams(
        template_id="middle_east_gulf_capital_gateway_seed_v1",
        primary_theme="energy_capital_cycle",
        secondary_theme="global_hub_airline_cycle",
        annual_growth_bias_floor_pct=-1.00,
        annual_growth_bias_ceiling_pct=1.25,
        aviation_propensity_bias_floor_pct=-11.0,
        aviation_propensity_bias_ceiling_pct=18.0,
        investment_cycle_bias_floor_pct=-10.0,
        investment_cycle_bias_ceiling_pct=18.0,
        openness_bias_floor_pct=-9.0,
        openness_bias_ceiling_pct=14.0,
    ),
    "oceania": RegionalSeedPotentialParams(
        template_id="oceania_resource_tourism_seed_v1",
        primary_theme="resource_income_cycle",
        secondary_theme="tourism_services_cycle",
        annual_growth_bias_floor_pct=-0.75,
        annual_growth_bias_ceiling_pct=0.95,
        aviation_propensity_bias_floor_pct=-9.0,
        aviation_propensity_bias_ceiling_pct=12.0,
        investment_cycle_bias_floor_pct=-7.0,
        investment_cycle_bias_ceiling_pct=9.0,
        openness_bias_floor_pct=-8.0,
        openness_bias_ceiling_pct=9.0,
    ),
    "south_east_europe_mediterranean": RegionalSeedPotentialParams(
        template_id="mediterranean_tourism_recovery_seed_v1",
        primary_theme="tourism_services_cycle",
        secondary_theme="europe_resilience_cycle",
        annual_growth_bias_floor_pct=-0.95,
        annual_growth_bias_ceiling_pct=1.15,
        aviation_propensity_bias_floor_pct=-12.0,
        aviation_propensity_bias_ceiling_pct=17.0,
        investment_cycle_bias_floor_pct=-9.0,
        investment_cycle_bias_ceiling_pct=12.0,
        openness_bias_floor_pct=-9.0,
        openness_bias_ceiling_pct=11.0,
    ),
    "central_asia_turkey_eurasia": RegionalSeedPotentialParams(
        template_id="central_asia_turkey_corridor_seed_v1",
        primary_theme="eurasia_corridor_cycle",
        secondary_theme="energy_capital_cycle",
        annual_growth_bias_floor_pct=-1.25,
        annual_growth_bias_ceiling_pct=1.45,
        aviation_propensity_bias_floor_pct=-14.0,
        aviation_propensity_bias_ceiling_pct=18.0,
        investment_cycle_bias_floor_pct=-12.0,
        investment_cycle_bias_ceiling_pct=17.0,
        openness_bias_floor_pct=-13.0,
        openness_bias_ceiling_pct=16.0,
    ),
    "north_africa": RegionalSeedPotentialParams(
        template_id="north_africa_gateway_demographics_seed_v1",
        primary_theme="africa_urbanization_cycle",
        secondary_theme="tourism_services_cycle",
        annual_growth_bias_floor_pct=-1.35,
        annual_growth_bias_ceiling_pct=1.55,
        aviation_propensity_bias_floor_pct=-15.0,
        aviation_propensity_bias_ceiling_pct=20.0,
        investment_cycle_bias_floor_pct=-14.0,
        investment_cycle_bias_ceiling_pct=18.0,
        openness_bias_floor_pct=-12.0,
        openness_bias_ceiling_pct=14.0,
    ),
    "latin_america_caribbean": RegionalSeedPotentialParams(
        template_id="latin_america_commodity_middle_class_seed_v1",
        primary_theme="latin_america_reform_cycle",
        secondary_theme="resource_income_cycle",
        annual_growth_bias_floor_pct=-1.15,
        annual_growth_bias_ceiling_pct=1.35,
        aviation_propensity_bias_floor_pct=-13.0,
        aviation_propensity_bias_ceiling_pct=16.0,
        investment_cycle_bias_floor_pct=-12.0,
        investment_cycle_bias_ceiling_pct=15.0,
        openness_bias_floor_pct=-11.0,
        openness_bias_ceiling_pct=12.0,
    ),
    "sub_saharan_africa": RegionalSeedPotentialParams(
        template_id="sub_saharan_africa_urbanization_catchup_seed_v1",
        primary_theme="africa_urbanization_cycle",
        secondary_theme="resource_income_cycle",
        annual_growth_bias_floor_pct=-1.65,
        annual_growth_bias_ceiling_pct=1.90,
        aviation_propensity_bias_floor_pct=-18.0,
        aviation_propensity_bias_ceiling_pct=25.0,
        investment_cycle_bias_floor_pct=-17.0,
        investment_cycle_bias_ceiling_pct=22.0,
        openness_bias_floor_pct=-13.0,
        openness_bias_ceiling_pct=15.0,
    ),
}


def stable_unit_float(*parts: Any) -> float:
    raw = "|".join(str(part) for part in parts).encode("utf-8")
    digest = hashlib.sha256(raw).digest()
    return int.from_bytes(digest[:8], "big") / float(2**64 - 1)


def stable_signed_score(*parts: Any) -> float:
    return stable_unit_float(*parts) * 2.0 - 1.0


def interpolate(low: float, high: float, unit: float) -> float:
    return low + (high - low) * clamp(unit, 0.0, 1.0)


def regional_seed_momentum_label(score: float) -> str:
    if score >= 0.62:
        return "strong_upside"
    if score >= 0.24:
        return "upside"
    if score <= -0.62:
        return "strong_downside"
    if score <= -0.24:
        return "downside"
    return "balanced"


def regional_seed_potential_profile(region: RegionalMacroParams, seed: int, year_index: int) -> dict[str, Any]:
    profile = REGIONAL_SEED_POTENTIALS.get(region.region_id)
    if profile is None:
        return {
            "version": REGIONAL_STRUCTURAL_SEED_VERSION,
            "enabled": 0,
            "template_id": "none",
            "primary_theme": "none",
            "secondary_theme": "none",
            "structural_score": 0.0,
            "theme_score": 0.0,
            "momentum_label": "disabled",
            "annual_growth_bias_pct": 0.0,
            "effect_release_pct": 0.0,
            "effective_growth_bias_pct": 0.0,
            "aviation_propensity_bias_pct": 0.0,
            "investment_cycle_bias_pct": 0.0,
            "openness_bias_pct": 0.0,
            "demand_multiplier": 1.0,
        }

    local_score = stable_signed_score("regional_seed_local", seed, region.region_id, profile.template_id)
    primary_score = stable_signed_score("regional_seed_theme", seed, profile.primary_theme)
    secondary_score = stable_signed_score("regional_seed_theme", seed, profile.secondary_theme)
    theme_score = clamp(primary_score * 0.72 + secondary_score * 0.28, -1.0, 1.0)
    structural_score = clamp(
        profile.local_weight * local_score
        + profile.primary_theme_weight * primary_score
        + profile.secondary_theme_weight * secondary_score,
        -1.0,
        1.0,
    )
    unit = (structural_score + 1.0) / 2.0
    release = clamp(
        (year_index - profile.release_start_year_index)
        / max(1.0, profile.full_effect_year_index - profile.release_start_year_index),
        0.0,
        1.0,
    )
    annual_growth_bias = interpolate(
        profile.annual_growth_bias_floor_pct,
        profile.annual_growth_bias_ceiling_pct,
        unit,
    )
    effective_growth_bias = annual_growth_bias * release
    aviation_bias = interpolate(
        profile.aviation_propensity_bias_floor_pct,
        profile.aviation_propensity_bias_ceiling_pct,
        unit,
    ) * release
    investment_bias = interpolate(
        profile.investment_cycle_bias_floor_pct,
        profile.investment_cycle_bias_ceiling_pct,
        unit,
    ) * release
    openness_bias = interpolate(
        profile.openness_bias_floor_pct,
        profile.openness_bias_ceiling_pct,
        unit,
    ) * release
    demand_multiplier = clamp(
        1.0 + (0.32 * aviation_bias + 0.18 * investment_bias + 0.12 * openness_bias) / 100.0,
        0.82,
        1.24,
    )
    return {
        "version": REGIONAL_STRUCTURAL_SEED_VERSION,
        "enabled": 1,
        "template_id": profile.template_id,
        "primary_theme": profile.primary_theme,
        "secondary_theme": profile.secondary_theme,
        "structural_score": structural_score,
        "theme_score": theme_score,
        "momentum_label": regional_seed_momentum_label(structural_score),
        "annual_growth_bias_pct": annual_growth_bias,
        "effect_release_pct": release * 100.0,
        "effective_growth_bias_pct": effective_growth_bias,
        "aviation_propensity_bias_pct": aviation_bias,
        "investment_cycle_bias_pct": investment_bias,
        "openness_bias_pct": openness_bias,
        "demand_multiplier": demand_multiplier,
    }


REGION_CONFIGS = {
    "north_america": RegionalMacroParams(),
    "china_mainland": RegionalMacroParams(
        region_id="china_mainland",
        region_name="中国大陆",
        global_weight=0.185,
        trend_growth_pct=3.85,
        income_level_index=62.0,
        market_maturity=0.66,
        domestic_demand_weight=0.89,
        international_exposure=0.58,
        tourism_exposure=0.36,
        business_exposure=0.60,
        oil_sensitivity=0.86,
        dollar_sensitivity=0.72,
        credit_sensitivity=1.16,
        equity_wealth_sensitivity=0.62,
        policy_rate_sensitivity=0.74,
        geopolitical_sensitivity=0.62,
        capacity_constraint=0.32,
        shock_volatility=0.30,
        reconciliation_sensitivity=0.74,
        potential_growth_floor_pct=1.20,
        potential_growth_ceiling_pct=5.25,
        raw_growth_floor_pct=-3.60,
        raw_growth_ceiling_pct=6.30,
        growth_floor_pct=-3.90,
        growth_ceiling_pct=6.50,
        output_gap_floor_pct=-6.80,
        output_gap_ceiling_pct=5.20,
        inflation_anchor_pct=1.85,
        core_inflation_anchor_pct=1.75,
        policy_global_beta=0.42,
        policy_neutral_rate_pct=2.35,
        policy_floor_pct=0.20,
        policy_ceiling_pct=6.50,
        rate_anchor_weight=0.34,
        long_rate_global_beta=0.50,
        long_rate_neutral_pct=2.75,
        currency_dollar_beta=0.38,
        fx_management_strength=0.68,
        credit_global_beta=0.68,
        ig_global_beta=0.70,
        asset_global_beta=0.54,
        bond_global_beta=0.50,
        policy_support_sensitivity=0.92,
        infrastructure_sensitivity=0.82,
        energy_import_sensitivity=1.18,
        commodity_export_sensitivity=0.36,
    ),
    "hk_macao_taiwan": RegionalMacroParams(
        region_id="hk_macao_taiwan",
        region_name="港澳台",
        global_weight=0.035,
        trend_growth_pct=1.82,
        income_level_index=82.0,
        market_maturity=0.86,
        domestic_demand_weight=0.56,
        international_exposure=0.88,
        tourism_exposure=0.78,
        business_exposure=0.76,
        oil_sensitivity=0.92,
        dollar_sensitivity=0.52,
        credit_sensitivity=0.96,
        equity_wealth_sensitivity=0.86,
        policy_rate_sensitivity=0.90,
        geopolitical_sensitivity=0.72,
        capacity_constraint=0.20,
        shock_volatility=0.32,
        reconciliation_sensitivity=0.74,
        potential_growth_floor_pct=0.05,
        potential_growth_ceiling_pct=3.25,
        raw_growth_floor_pct=-5.20,
        raw_growth_ceiling_pct=4.90,
        growth_floor_pct=-5.50,
        growth_ceiling_pct=5.10,
        output_gap_floor_pct=-8.20,
        output_gap_ceiling_pct=5.00,
        inflation_anchor_pct=2.05,
        core_inflation_anchor_pct=1.90,
        policy_global_beta=0.70,
        policy_neutral_rate_pct=2.40,
        policy_floor_pct=-0.10,
        policy_ceiling_pct=7.40,
        rate_anchor_weight=0.66,
        long_rate_global_beta=0.62,
        long_rate_neutral_pct=2.70,
        currency_dollar_beta=0.54,
        fx_management_strength=0.55,
        credit_global_beta=0.82,
        ig_global_beta=0.84,
        asset_global_beta=0.72,
        bond_global_beta=0.62,
        policy_support_sensitivity=0.22,
        infrastructure_sensitivity=0.12,
        energy_import_sensitivity=1.16,
        commodity_export_sensitivity=0.12,
    ),
    "japan_korea": RegionalMacroParams(
        region_id="japan_korea",
        region_name="日韩",
        global_weight=0.072,
        trend_growth_pct=1.05,
        income_level_index=84.0,
        market_maturity=0.90,
        domestic_demand_weight=0.68,
        international_exposure=0.64,
        tourism_exposure=0.45,
        business_exposure=0.72,
        oil_sensitivity=0.96,
        dollar_sensitivity=0.58,
        credit_sensitivity=0.88,
        equity_wealth_sensitivity=0.72,
        policy_rate_sensitivity=0.72,
        geopolitical_sensitivity=0.56,
        capacity_constraint=0.18,
        shock_volatility=0.24,
        reconciliation_sensitivity=0.78,
        potential_growth_floor_pct=-0.10,
        potential_growth_ceiling_pct=2.40,
        raw_growth_floor_pct=-4.80,
        raw_growth_ceiling_pct=3.80,
        growth_floor_pct=-5.00,
        growth_ceiling_pct=4.00,
        output_gap_floor_pct=-8.00,
        output_gap_ceiling_pct=4.50,
        inflation_anchor_pct=1.55,
        core_inflation_anchor_pct=1.45,
        policy_global_beta=0.45,
        policy_neutral_rate_pct=1.10,
        policy_floor_pct=-0.20,
        policy_ceiling_pct=5.20,
        rate_anchor_weight=0.45,
        long_rate_global_beta=0.48,
        long_rate_neutral_pct=1.45,
        currency_dollar_beta=0.72,
        fx_management_strength=0.35,
        credit_global_beta=0.78,
        ig_global_beta=0.80,
        asset_global_beta=0.58,
        bond_global_beta=0.54,
        policy_support_sensitivity=0.28,
        infrastructure_sensitivity=0.12,
        energy_import_sensitivity=1.32,
        commodity_export_sensitivity=0.18,
    ),
    "southeast_asia": RegionalMacroParams(
        region_id="southeast_asia",
        region_name="东南亚",
        global_weight=0.052,
        trend_growth_pct=4.20,
        income_level_index=50.0,
        market_maturity=0.58,
        domestic_demand_weight=0.72,
        international_exposure=0.82,
        tourism_exposure=0.78,
        business_exposure=0.52,
        oil_sensitivity=0.82,
        dollar_sensitivity=0.95,
        credit_sensitivity=1.10,
        equity_wealth_sensitivity=0.58,
        policy_rate_sensitivity=0.88,
        geopolitical_sensitivity=0.48,
        capacity_constraint=0.44,
        shock_volatility=0.38,
        reconciliation_sensitivity=0.70,
        potential_growth_floor_pct=1.40,
        potential_growth_ceiling_pct=6.20,
        raw_growth_floor_pct=-4.20,
        raw_growth_ceiling_pct=7.20,
        growth_floor_pct=-4.50,
        growth_ceiling_pct=7.40,
        output_gap_floor_pct=-7.50,
        output_gap_ceiling_pct=6.00,
        inflation_anchor_pct=2.75,
        core_inflation_anchor_pct=2.55,
        policy_global_beta=0.55,
        policy_neutral_rate_pct=3.10,
        policy_floor_pct=0.40,
        policy_ceiling_pct=8.50,
        rate_anchor_weight=0.46,
        long_rate_global_beta=0.56,
        long_rate_neutral_pct=3.50,
        currency_dollar_beta=0.82,
        fx_management_strength=0.32,
        credit_global_beta=0.72,
        ig_global_beta=0.74,
        asset_global_beta=0.62,
        bond_global_beta=0.52,
        policy_support_sensitivity=0.48,
        infrastructure_sensitivity=0.42,
        energy_import_sensitivity=0.95,
        commodity_export_sensitivity=0.58,
    ),
    "south_asia_india": RegionalMacroParams(
        region_id="south_asia_india",
        region_name="南亚/印度",
        global_weight=0.060,
        trend_growth_pct=5.25,
        income_level_index=38.0,
        market_maturity=0.48,
        domestic_demand_weight=0.86,
        international_exposure=0.50,
        tourism_exposure=0.30,
        business_exposure=0.42,
        oil_sensitivity=1.08,
        dollar_sensitivity=1.18,
        credit_sensitivity=1.22,
        equity_wealth_sensitivity=0.48,
        policy_rate_sensitivity=0.92,
        geopolitical_sensitivity=0.55,
        capacity_constraint=0.62,
        shock_volatility=0.42,
        reconciliation_sensitivity=0.68,
        potential_growth_floor_pct=2.20,
        potential_growth_ceiling_pct=7.20,
        raw_growth_floor_pct=-3.80,
        raw_growth_ceiling_pct=8.00,
        growth_floor_pct=-4.20,
        growth_ceiling_pct=8.20,
        output_gap_floor_pct=-7.20,
        output_gap_ceiling_pct=6.20,
        inflation_anchor_pct=3.60,
        core_inflation_anchor_pct=3.25,
        policy_global_beta=0.50,
        policy_neutral_rate_pct=4.40,
        policy_floor_pct=1.00,
        policy_ceiling_pct=10.50,
        rate_anchor_weight=0.40,
        long_rate_global_beta=0.50,
        long_rate_neutral_pct=5.00,
        currency_dollar_beta=0.88,
        fx_management_strength=0.22,
        credit_global_beta=0.66,
        ig_global_beta=0.68,
        asset_global_beta=0.52,
        bond_global_beta=0.44,
        policy_support_sensitivity=0.58,
        infrastructure_sensitivity=0.60,
        energy_import_sensitivity=1.28,
        commodity_export_sensitivity=0.32,
    ),
    "middle_east_gulf": RegionalMacroParams(
        region_id="middle_east_gulf",
        region_name="中东/海湾",
        global_weight=0.045,
        trend_growth_pct=3.25,
        income_level_index=78.0,
        market_maturity=0.72,
        domestic_demand_weight=0.55,
        international_exposure=0.88,
        tourism_exposure=0.58,
        business_exposure=0.70,
        oil_sensitivity=0.66,
        dollar_sensitivity=0.70,
        credit_sensitivity=0.92,
        equity_wealth_sensitivity=0.70,
        policy_rate_sensitivity=0.82,
        geopolitical_sensitivity=0.92,
        capacity_constraint=0.30,
        shock_volatility=0.40,
        reconciliation_sensitivity=0.68,
        potential_growth_floor_pct=0.95,
        potential_growth_ceiling_pct=5.50,
        raw_growth_floor_pct=-5.00,
        raw_growth_ceiling_pct=7.00,
        growth_floor_pct=-5.40,
        growth_ceiling_pct=7.20,
        output_gap_floor_pct=-7.80,
        output_gap_ceiling_pct=6.00,
        inflation_anchor_pct=2.35,
        core_inflation_anchor_pct=2.20,
        policy_global_beta=0.68,
        policy_neutral_rate_pct=3.20,
        policy_floor_pct=0.40,
        policy_ceiling_pct=8.80,
        rate_anchor_weight=0.62,
        long_rate_global_beta=0.64,
        long_rate_neutral_pct=3.65,
        currency_dollar_beta=0.46,
        fx_management_strength=0.62,
        credit_global_beta=0.76,
        ig_global_beta=0.78,
        asset_global_beta=0.66,
        bond_global_beta=0.58,
        policy_support_sensitivity=0.48,
        infrastructure_sensitivity=0.52,
        energy_import_sensitivity=0.36,
        commodity_export_sensitivity=1.55,
    ),
    "central_asia_turkey_eurasia": RegionalMacroParams(
        region_id="central_asia_turkey_eurasia",
        region_name="中亚/土耳其/欧亚桥",
        global_weight=0.030,
        trend_growth_pct=3.05,
        income_level_index=48.0,
        market_maturity=0.50,
        domestic_demand_weight=0.62,
        international_exposure=0.72,
        tourism_exposure=0.50,
        business_exposure=0.48,
        oil_sensitivity=0.88,
        dollar_sensitivity=1.22,
        credit_sensitivity=1.20,
        equity_wealth_sensitivity=0.50,
        policy_rate_sensitivity=1.05,
        geopolitical_sensitivity=0.90,
        capacity_constraint=0.48,
        shock_volatility=0.48,
        reconciliation_sensitivity=0.64,
        potential_growth_floor_pct=0.70,
        potential_growth_ceiling_pct=5.80,
        raw_growth_floor_pct=-6.20,
        raw_growth_ceiling_pct=7.20,
        growth_floor_pct=-6.50,
        growth_ceiling_pct=7.50,
        output_gap_floor_pct=-8.80,
        output_gap_ceiling_pct=6.00,
        inflation_anchor_pct=3.40,
        core_inflation_anchor_pct=3.00,
        policy_global_beta=0.52,
        policy_neutral_rate_pct=4.20,
        policy_floor_pct=0.80,
        policy_ceiling_pct=12.00,
        rate_anchor_weight=0.42,
        long_rate_global_beta=0.50,
        long_rate_neutral_pct=5.20,
        currency_dollar_beta=0.92,
        fx_management_strength=0.18,
        credit_global_beta=0.62,
        ig_global_beta=0.66,
        asset_global_beta=0.50,
        bond_global_beta=0.44,
        policy_support_sensitivity=0.42,
        infrastructure_sensitivity=0.45,
        energy_import_sensitivity=0.86,
        commodity_export_sensitivity=0.68,
    ),
    "oceania": RegionalMacroParams(
        region_id="oceania",
        region_name="大洋洲",
        global_weight=0.028,
        trend_growth_pct=2.18,
        income_level_index=80.0,
        market_maturity=0.84,
        domestic_demand_weight=0.66,
        international_exposure=0.74,
        tourism_exposure=0.70,
        business_exposure=0.54,
        oil_sensitivity=0.72,
        dollar_sensitivity=0.58,
        credit_sensitivity=0.90,
        equity_wealth_sensitivity=0.78,
        policy_rate_sensitivity=1.02,
        geopolitical_sensitivity=0.30,
        capacity_constraint=0.28,
        shock_volatility=0.28,
        reconciliation_sensitivity=0.72,
        potential_growth_floor_pct=0.45,
        potential_growth_ceiling_pct=3.75,
        raw_growth_floor_pct=-4.90,
        raw_growth_ceiling_pct=5.50,
        growth_floor_pct=-5.10,
        growth_ceiling_pct=5.70,
        output_gap_floor_pct=-7.80,
        output_gap_ceiling_pct=5.20,
        inflation_anchor_pct=2.25,
        core_inflation_anchor_pct=2.10,
        policy_global_beta=0.76,
        policy_neutral_rate_pct=3.00,
        policy_floor_pct=0.10,
        policy_ceiling_pct=8.20,
        rate_anchor_weight=0.74,
        long_rate_global_beta=0.74,
        long_rate_neutral_pct=3.35,
        currency_dollar_beta=0.70,
        fx_management_strength=0.18,
        credit_global_beta=0.82,
        ig_global_beta=0.84,
        asset_global_beta=0.68,
        bond_global_beta=0.70,
        policy_support_sensitivity=0.24,
        infrastructure_sensitivity=0.20,
        energy_import_sensitivity=0.72,
        commodity_export_sensitivity=0.92,
    ),
    "north_africa": RegionalMacroParams(
        region_id="north_africa",
        region_name="北非",
        global_weight=0.022,
        trend_growth_pct=3.65,
        income_level_index=34.0,
        market_maturity=0.42,
        domestic_demand_weight=0.70,
        international_exposure=0.68,
        tourism_exposure=0.62,
        business_exposure=0.32,
        oil_sensitivity=1.02,
        dollar_sensitivity=1.15,
        credit_sensitivity=1.25,
        equity_wealth_sensitivity=0.38,
        policy_rate_sensitivity=0.96,
        geopolitical_sensitivity=0.82,
        capacity_constraint=0.58,
        shock_volatility=0.48,
        reconciliation_sensitivity=0.60,
        potential_growth_floor_pct=0.90,
        potential_growth_ceiling_pct=6.40,
        raw_growth_floor_pct=-5.40,
        raw_growth_ceiling_pct=7.50,
        growth_floor_pct=-5.80,
        growth_ceiling_pct=7.80,
        output_gap_floor_pct=-8.50,
        output_gap_ceiling_pct=6.30,
        inflation_anchor_pct=3.50,
        core_inflation_anchor_pct=3.10,
        policy_global_beta=0.48,
        policy_neutral_rate_pct=4.60,
        policy_floor_pct=1.00,
        policy_ceiling_pct=12.00,
        rate_anchor_weight=0.38,
        long_rate_global_beta=0.48,
        long_rate_neutral_pct=5.40,
        currency_dollar_beta=0.88,
        fx_management_strength=0.24,
        credit_global_beta=0.58,
        ig_global_beta=0.60,
        asset_global_beta=0.44,
        bond_global_beta=0.38,
        policy_support_sensitivity=0.45,
        infrastructure_sensitivity=0.50,
        energy_import_sensitivity=0.95,
        commodity_export_sensitivity=0.52,
    ),
    "latin_america_caribbean": RegionalMacroParams(
        region_id="latin_america_caribbean",
        region_name="拉美/加勒比",
        global_weight=0.070,
        trend_growth_pct=2.65,
        income_level_index=45.0,
        market_maturity=0.52,
        domestic_demand_weight=0.68,
        international_exposure=0.70,
        tourism_exposure=0.66,
        business_exposure=0.42,
        oil_sensitivity=0.82,
        dollar_sensitivity=1.28,
        credit_sensitivity=1.18,
        equity_wealth_sensitivity=0.48,
        policy_rate_sensitivity=1.02,
        geopolitical_sensitivity=0.52,
        capacity_constraint=0.46,
        shock_volatility=0.46,
        reconciliation_sensitivity=0.64,
        potential_growth_floor_pct=0.55,
        potential_growth_ceiling_pct=5.30,
        raw_growth_floor_pct=-6.00,
        raw_growth_ceiling_pct=6.80,
        growth_floor_pct=-6.30,
        growth_ceiling_pct=7.00,
        output_gap_floor_pct=-8.70,
        output_gap_ceiling_pct=6.00,
        inflation_anchor_pct=3.25,
        core_inflation_anchor_pct=2.85,
        policy_global_beta=0.50,
        policy_neutral_rate_pct=4.10,
        policy_floor_pct=0.60,
        policy_ceiling_pct=11.50,
        rate_anchor_weight=0.42,
        long_rate_global_beta=0.50,
        long_rate_neutral_pct=5.10,
        currency_dollar_beta=0.94,
        fx_management_strength=0.14,
        credit_global_beta=0.62,
        ig_global_beta=0.66,
        asset_global_beta=0.50,
        bond_global_beta=0.42,
        policy_support_sensitivity=0.36,
        infrastructure_sensitivity=0.36,
        energy_import_sensitivity=0.70,
        commodity_export_sensitivity=1.05,
    ),
    "sub_saharan_africa": RegionalMacroParams(
        region_id="sub_saharan_africa",
        region_name="撒哈拉以南非洲",
        global_weight=0.038,
        trend_growth_pct=4.35,
        income_level_index=24.0,
        market_maturity=0.32,
        domestic_demand_weight=0.78,
        international_exposure=0.46,
        tourism_exposure=0.28,
        business_exposure=0.26,
        oil_sensitivity=1.02,
        dollar_sensitivity=1.38,
        credit_sensitivity=1.34,
        equity_wealth_sensitivity=0.28,
        policy_rate_sensitivity=0.92,
        geopolitical_sensitivity=0.82,
        capacity_constraint=0.76,
        shock_volatility=0.54,
        reconciliation_sensitivity=0.52,
        potential_growth_floor_pct=1.20,
        potential_growth_ceiling_pct=7.30,
        raw_growth_floor_pct=-5.80,
        raw_growth_ceiling_pct=8.20,
        growth_floor_pct=-6.20,
        growth_ceiling_pct=8.50,
        output_gap_floor_pct=-8.80,
        output_gap_ceiling_pct=6.50,
        inflation_anchor_pct=4.25,
        core_inflation_anchor_pct=3.75,
        policy_global_beta=0.42,
        policy_neutral_rate_pct=5.20,
        policy_floor_pct=1.20,
        policy_ceiling_pct=13.50,
        rate_anchor_weight=0.34,
        long_rate_global_beta=0.42,
        long_rate_neutral_pct=6.10,
        currency_dollar_beta=1.02,
        fx_management_strength=0.12,
        credit_global_beta=0.52,
        ig_global_beta=0.56,
        asset_global_beta=0.36,
        bond_global_beta=0.32,
        policy_support_sensitivity=0.50,
        infrastructure_sensitivity=0.66,
        energy_import_sensitivity=0.88,
        commodity_export_sensitivity=0.82,
    ),
    "west_north_europe": RegionalMacroParams(
        region_id="west_north_europe",
        region_name="西欧/北欧",
        global_weight=0.165,
        trend_growth_pct=1.38,
        income_level_index=86.0,
        market_maturity=0.91,
        domestic_demand_weight=0.70,
        international_exposure=0.68,
        tourism_exposure=0.54,
        business_exposure=0.78,
        oil_sensitivity=0.94,
        dollar_sensitivity=0.34,
        credit_sensitivity=0.98,
        equity_wealth_sensitivity=0.82,
        policy_rate_sensitivity=1.04,
        geopolitical_sensitivity=0.58,
        capacity_constraint=0.24,
        shock_volatility=0.25,
        reconciliation_sensitivity=0.80,
        potential_growth_floor_pct=0.10,
        potential_growth_ceiling_pct=2.70,
        raw_growth_floor_pct=-5.20,
        raw_growth_ceiling_pct=4.50,
        growth_floor_pct=-5.50,
        growth_ceiling_pct=4.80,
        output_gap_floor_pct=-8.60,
        output_gap_ceiling_pct=4.80,
        inflation_anchor_pct=2.05,
        core_inflation_anchor_pct=1.95,
        policy_global_beta=0.72,
        policy_neutral_rate_pct=2.20,
        policy_floor_pct=-0.55,
        policy_ceiling_pct=7.20,
        rate_anchor_weight=0.72,
        long_rate_global_beta=0.70,
        long_rate_neutral_pct=2.55,
        currency_dollar_beta=0.62,
        fx_management_strength=0.16,
        credit_global_beta=0.86,
        ig_global_beta=0.86,
        asset_global_beta=0.66,
        bond_global_beta=0.70,
        policy_support_sensitivity=0.32,
        infrastructure_sensitivity=0.18,
        energy_import_sensitivity=1.36,
        commodity_export_sensitivity=0.22,
    ),
    "south_east_europe_mediterranean": RegionalMacroParams(
        region_id="south_east_europe_mediterranean",
        region_name="南欧/东欧/地中海",
        global_weight=0.040,
        trend_growth_pct=2.05,
        income_level_index=58.0,
        market_maturity=0.62,
        domestic_demand_weight=0.62,
        international_exposure=0.78,
        tourism_exposure=0.86,
        business_exposure=0.42,
        oil_sensitivity=0.98,
        dollar_sensitivity=0.56,
        credit_sensitivity=1.08,
        equity_wealth_sensitivity=0.56,
        policy_rate_sensitivity=0.96,
        geopolitical_sensitivity=0.68,
        capacity_constraint=0.38,
        shock_volatility=0.36,
        reconciliation_sensitivity=0.70,
        potential_growth_floor_pct=0.25,
        potential_growth_ceiling_pct=4.10,
        raw_growth_floor_pct=-5.40,
        raw_growth_ceiling_pct=6.00,
        growth_floor_pct=-5.80,
        growth_ceiling_pct=6.20,
        output_gap_floor_pct=-8.60,
        output_gap_ceiling_pct=5.60,
        inflation_anchor_pct=2.55,
        core_inflation_anchor_pct=2.35,
        policy_global_beta=0.66,
        policy_neutral_rate_pct=2.90,
        policy_floor_pct=-0.10,
        policy_ceiling_pct=8.20,
        rate_anchor_weight=0.62,
        long_rate_global_beta=0.64,
        long_rate_neutral_pct=3.35,
        currency_dollar_beta=0.68,
        fx_management_strength=0.20,
        credit_global_beta=0.78,
        ig_global_beta=0.80,
        asset_global_beta=0.58,
        bond_global_beta=0.58,
        policy_support_sensitivity=0.28,
        infrastructure_sensitivity=0.22,
        energy_import_sensitivity=1.20,
        commodity_export_sensitivity=0.24,
    ),
}


def pct_change(current: float, previous: float) -> float:
    if abs(previous) < 1e-9:
        return 0.0
    return (current / previous - 1.0) * 100.0


def compound_index(previous: float, return_pct: float, low: float = 10.0, high: float = 10_000.0) -> float:
    return clamp(previous * (1.0 + return_pct / 100.0), low, high)


def regional_branch_exposure(region: RegionalMacroParams, exposure_key: str) -> float:
    configured = BRANCH_EXPOSURE_BY_REGION.get(region.region_id, {})
    if exposure_key in configured:
        return configured[exposure_key]
    if exposure_key == "credit_crunch":
        return clamp(0.55 + 0.45 * region.credit_sensitivity + 0.15 * region.market_maturity, 0.55, 1.55)
    if exposure_key == "dollar_squeeze":
        return clamp(0.55 + 0.55 * max(0.0, region.dollar_sensitivity) - 0.25 * region.fx_management_strength, 0.45, 1.60)
    if exposure_key == "energy_crisis":
        return clamp(0.55 + 0.42 * region.energy_import_sensitivity - 0.20 * region.commodity_export_sensitivity, 0.45, 1.60)
    if exposure_key == "risk_asset_bull":
        return clamp(0.55 + 0.38 * region.equity_wealth_sensitivity + 0.18 * region.market_maturity, 0.50, 1.55)
    if exposure_key == "policy_mistake":
        return clamp(0.55 + 0.42 * region.policy_rate_sensitivity + 0.12 * region.credit_sensitivity, 0.50, 1.55)
    if exposure_key == "stagflation":
        return clamp(0.45 + 0.34 * region.energy_import_sensitivity + 0.18 * region.policy_rate_sensitivity + 0.12 * region.credit_sensitivity, 0.50, 1.65)
    return 1.0


def branch_variable_loadings(region: RegionalMacroParams) -> dict[str, float]:
    return {
        "growth": clamp(0.55 + 0.28 * region.international_exposure + 0.16 * region.business_exposure, 0.45, 1.35),
        "inflation": clamp(0.50 + 0.32 * region.energy_import_sensitivity + 0.12 * max(0.0, region.dollar_sensitivity), 0.40, 1.55),
        "policy": clamp(0.55 + 0.34 * region.policy_rate_sensitivity, 0.40, 1.45),
        "credit": clamp(region.credit_sensitivity, 0.45, 1.60),
        "fx": clamp(0.50 + 0.40 * max(0.0, region.dollar_sensitivity) - 0.28 * region.fx_management_strength, 0.25, 1.60),
        "energy": clamp(0.50 + 0.40 * region.energy_import_sensitivity - 0.15 * region.commodity_export_sensitivity, 0.25, 1.70),
        "liquidity": clamp(0.55 + 0.22 * region.market_maturity + 0.16 * region.international_exposure, 0.45, 1.35),
        "asset": clamp(0.55 + 0.36 * region.equity_wealth_sensitivity + 0.14 * region.market_maturity, 0.45, 1.55),
        "confidence": clamp(0.55 + 0.18 * region.domestic_demand_weight + 0.12 * region.tourism_exposure, 0.45, 1.35),
        "stress": clamp(0.55 + 0.24 * region.credit_sensitivity + 0.16 * max(0.0, region.dollar_sensitivity), 0.45, 1.55),
    }


def branch_scenario_id_for_row(row: dict[str, Any]) -> str:
    for key in ("scenario_risk_id", "scenario_event_type", "branch_scenario_id", "branch_risk_primary_id"):
        value = str(row.get(key, "") or "")
        if value in BRANCH_TRANSMISSION_PROFILES:
            return value
    return ""


def build_branch_transmission(row: dict[str, Any], region: RegionalMacroParams) -> dict[str, Any]:
    branch_id = branch_scenario_id_for_row(row)
    if not branch_id:
        return {
            "regional_branch_transmission_version": REGIONAL_BRANCH_TRANSMISSION_VERSION,
            "branch_scenario_id": "none",
            "branch_scenario_label": "none",
            "branch_scenario_state": "baseline",
            "branch_source_year": 0,
            "branch_impact_years": 0,
            "branch_tail_years": 0,
            "branch_year_in_effect": 0,
            "branch_effect_phase": "none",
            "regional_branch_transmission_active": "false",
            "regional_branch_exposure_index": 1.0,
            "regional_branch_relative_exposure_index": 0.0,
            "regional_branch_strength_index": 0.0,
            "regional_branch_growth_impulse_pct": 0.0,
            "regional_branch_inflation_impulse_pct": 0.0,
            "regional_branch_policy_impulse_pct": 0.0,
            "regional_branch_credit_impulse_bps": 0.0,
            "regional_branch_fx_pressure_impulse": 0.0,
            "regional_branch_energy_impulse": 0.0,
            "regional_branch_liquidity_impulse": 0.0,
            "regional_branch_asset_impulse_pct": 0.0,
            "regional_branch_confidence_impulse": 0.0,
            "regional_branch_tail_scarring_index": 0.0,
        }

    profile = BRANCH_TRANSMISSION_PROFILES[branch_id]
    scenario_state = str(row.get("branch_scenario_state") or row.get("scenario_state") or "").strip()
    if not scenario_state:
        scenario_state = "occurred" if row.get("scenario_risk_id") or row.get("scenario_event_type") else "watch"
    scenario_state = scenario_state.lower()
    active = scenario_state in {"occurred", "counterfactual"}
    probability = as_float(row, "branch_risk_primary_probability_pct", 0.0)
    severity = as_float(row, "branch_risk_primary_severity_index", probability)
    scenario_severity = as_float(row, "scenario_event_severity", 0.0)
    if scenario_severity > 0.0:
        severity_scale = clamp(scenario_severity, 0.30, 1.60)
    else:
        severity_scale = clamp((severity or probability or 50.0) / 72.0, 0.35, 1.35)
    probability_scale = clamp((probability or 55.0) / 100.0, 0.15, 0.90)
    potential_scale = severity_scale if active else severity_scale * probability_scale
    exposure = regional_branch_exposure(region, profile.exposure_key)
    relative_exposure = exposure - 1.0
    multiplier = potential_scale * relative_exposure
    loadings = branch_variable_loadings(region)
    source_year = int(row.get("scenario_trigger_year") or row.get("branch_source_year") or row.get("year") or 0)
    year_index = int(row.get("year_index", 0) or 0)
    trigger_index = int(row.get("scenario_trigger_index", year_index) or year_index)
    phase = str(row.get("scenario_phase") or row.get("scenario_event_phase") or ("impact" if active else "watch"))
    impact_years = int(as_float(row, "scenario_impact_years", as_float(row, "branch_risk_primary_impact_years", 0.0)))
    tail_years = int(as_float(row, "scenario_tail_years", as_float(row, "branch_risk_primary_tail_years", 0.0)))

    return {
        "regional_branch_transmission_version": REGIONAL_BRANCH_TRANSMISSION_VERSION,
        "branch_scenario_id": branch_id,
        "branch_scenario_label": str(row.get("branch_risk_primary_label") or profile.label),
        "branch_scenario_state": scenario_state,
        "branch_source_year": source_year,
        "branch_impact_years": impact_years,
        "branch_tail_years": tail_years,
        "branch_year_in_effect": max(0, year_index - trigger_index) if active else 0,
        "branch_effect_phase": phase,
        "regional_branch_transmission_active": str(active).lower(),
        "regional_branch_exposure_index": exposure,
        "regional_branch_relative_exposure_index": relative_exposure,
        "regional_branch_strength_index": clamp(abs(multiplier) * 100.0, 0.0, 100.0),
        "regional_branch_growth_impulse_pct": profile.growth_pct * multiplier * loadings["growth"],
        "regional_branch_inflation_impulse_pct": profile.inflation_pct * multiplier * loadings["inflation"],
        "regional_branch_policy_impulse_pct": profile.policy_pct * multiplier * loadings["policy"],
        "regional_branch_credit_impulse_bps": profile.credit_bps * multiplier * loadings["credit"],
        "regional_branch_fx_pressure_impulse": profile.fx_pressure * multiplier * loadings["fx"],
        "regional_branch_energy_impulse": profile.energy_index * multiplier * loadings["energy"],
        "regional_branch_liquidity_impulse": profile.liquidity_index * multiplier * loadings["liquidity"],
        "regional_branch_asset_impulse_pct": profile.asset_return_pct * multiplier * loadings["asset"],
        "regional_branch_confidence_impulse": profile.confidence_index * multiplier * loadings["confidence"],
        "regional_branch_tail_scarring_index": profile.tail_scarring_index * multiplier,
    }


def branch_is_active(branch: dict[str, Any]) -> bool:
    return str(branch.get("regional_branch_transmission_active", "false")).lower() == "true"


def classify_growth_regime(
    growth: float,
    potential_growth: float,
    output_gap: float,
    credit_stress: float,
    financial_stress: float,
    real_policy_rate: float,
) -> str:
    if growth < -0.4 or output_gap < -4.0:
        return "regional_recession"
    if credit_stress > 68.0 or financial_stress > 70.0:
        return "credit_squeeze"
    if real_policy_rate > 1.4 and growth < 1.4:
        return "rate_sensitive_slowdown"
    if growth > potential_growth + 0.55 and output_gap > 0.4:
        return "above_trend_expansion"
    if growth > potential_growth - 0.55 and output_gap > -1.5:
        return "normal_expansion"
    return "mature_slow_growth"


def classify_regional_inflation(headline: float, core: float, energy: float, growth: float) -> str:
    if headline > 5.0 and growth < 1.4:
        return "stagflation_pressure"
    if headline > 4.2 or core > 3.6:
        return "high_inflation"
    if headline < 0.5 and growth < 1.0:
        return "deflation_risk"
    if 1.5 <= headline <= 3.1 and 1.4 <= core <= 2.9:
        return "anchored_normal"
    if energy > 7.0 and headline > 3.3:
        return "energy_driven_inflation"
    return "mixed_inflation"


def classify_macro_regime(
    growth: float,
    potential_growth: float,
    output_gap: float,
    headline: float,
    hy_spread: float,
    credit_stress: float,
    equity_return: float,
    stress: float,
    confidence: float,
) -> str:
    if stress > 72.0 or hy_spread > 1_100.0 or (hy_spread > 850.0 and credit_stress > 55.0):
        return "regional_financial_crisis"
    if headline > 4.5 and growth < 1.2:
        return "regional_stagflation"
    if growth < 0.0 or output_gap < -4.0:
        return "regional_recession"
    if hy_spread > 650.0:
        return "regional_credit_tightening"
    if growth > potential_growth + 0.35 and equity_return > 5.0 and confidence > 56.0:
        return "wealth_led_expansion"
    if growth >= potential_growth - 0.65 and headline < 3.2 and hy_spread < 560.0:
        return "soft_landing_or_normal"
    return "mixed_cycle"


def build_global_params(args: argparse.Namespace) -> dict[str, Any]:
    gdp_args = argparse.Namespace(
        years=args.years,
        start_year=args.start_year,
        initial_gdp=args.initial_gdp,
        volatility_scale=args.volatility_scale,
    )
    feedback_defaults = MacroFeedbackParams()
    feedback_iterations = int(
        getattr(args, "feedback_iterations", feedback_defaults.feedback_iterations)
    )
    min_feedback_iterations = int(
        getattr(args, "min_feedback_iterations", feedback_defaults.min_feedback_iterations)
    )
    return {
        "gdp_params": calibrated_gdp_params(gdp_args),
        "inflation_params": InflationParams(
            headline_anchor_pct=2.45,
            core_anchor_pct=2.30,
            expectation_anchor_pct=2.35,
            headline_persistence=0.62,
            core_persistence=0.78,
            credit_stress_disinflation_beta=0.24,
            crisis_disinflation_beta=0.34,
        ),
        "policy_params": PolicyRateParams(policy_adjustment_speed=0.34),
        "yield_curve_params": YieldCurveParams(),
        "dollar_liquidity_params": DollarLiquidityParams(),
        "credit_spread_params": calibrated_credit_params(),
        "asset_price_params": calibrated_asset_params(),
        "oil_commodity_params": calibrated_oil_params(),
        # Both bounds flow into MacroFeedbackParams so the convergence-aware
        # loop has a single source of truth regardless of which entry point
        # (orchestrator vs. standalone regional script) built the params.
        "feedback_params": MacroFeedbackParams(
            feedback_iterations=feedback_iterations,
            min_feedback_iterations=min_feedback_iterations,
            max_feedback_iterations=max(1, feedback_iterations),
        ),
        "feedback_iterations": feedback_iterations,
        "min_feedback_iterations": min_feedback_iterations,
    }


def run_global_macro_for_seed(
    seed: int,
    params: dict[str, Any],
    feedback_iterations: int,
    *,
    min_feedback_iterations: int | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Run the global macro chain with the convergence-aware feedback loop.

    The legacy signature ``(seed, params, feedback_iterations)`` is preserved so
    existing callers/tests keep working; the loop itself now goes through
    ``run_convergence_aware_feedback_loop`` (Working Guide sub-Goal 2), which
    enforces the min/max iteration bounds and the consecutive-pass tolerances
    instead of always running exactly ``feedback_iterations`` passes.
    """
    feedback_params: MacroFeedbackParams = params["feedback_params"]
    if min_feedback_iterations is None:
        min_feedback_iterations = int(
            params.get("min_feedback_iterations", feedback_params.min_feedback_iterations)
        )

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
    )

    def run_pass(macro_feedback: dict[int, dict[str, Any]], _iteration: int) -> list[dict[str, Any]]:
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
            feedback_path=macro_feedback if macro_feedback else None,
        )

    records, macro_feedback, convergence = run_convergence_aware_feedback_loop(
        seed=seed,
        feedback_params=feedback_params,
        initial_records=initial_records,
        run_pass=run_pass,
        min_iterations=min_feedback_iterations,
        max_iterations=max(1, feedback_iterations),
    )
    return annotate_feedback_records(records, macro_feedback, feedback_iterations, convergence), convergence


def simulate_region_for_global_path(
    global_records: list[dict[str, Any]],
    region: RegionalMacroParams,
    seed: int,
) -> list[dict[str, Any]]:
    rng = random.Random(seed * 1_000_003 + 79_201)
    regional_gdp_index = 100.0
    regional_income_index = 100.0
    regional_equity_index = 100.0
    regional_bond_index = 100.0
    prev_currency_index = 100.0
    prev_growth = region.trend_growth_pct
    prev_output_gap = -0.2
    prev_headline = 2.35
    prev_core = 2.30
    records: list[dict[str, Any]] = []

    anchor_strength = clamp((0.32 + region.global_weight * 0.36) * region.reconciliation_sensitivity, 0.18, 0.48)

    for row in global_records:
        year_index = int(row["year_index"])
        seed_profile = regional_seed_potential_profile(region, seed, year_index)
        seed_growth_bias = as_float(seed_profile, "effective_growth_bias_pct")
        seed_aviation_bias = as_float(seed_profile, "aviation_propensity_bias_pct")
        seed_investment_bias = as_float(seed_profile, "investment_cycle_bias_pct")
        seed_openness_bias = as_float(seed_profile, "openness_bias_pct")
        global_growth = as_float(row, "realized_growth_pct", 2.2)
        global_potential = as_float(row, "potential_growth_pct", 2.2)
        global_output_gap = as_float(row, "output_gap_pct")
        global_stress = as_float(row, "financial_stress_index", 35.0)
        global_headline = as_float(row, "headline_inflation_pct", 2.4)
        global_core = as_float(row, "core_inflation_pct", 2.3)
        global_energy = as_float(row, "energy_inflation_pct", 2.6)
        global_import = as_float(row, "import_inflation_pct", 2.4)
        global_expectation = as_float(row, "inflation_expectation_pct", 2.35)
        global_policy = as_float(row, "global_policy_rate_pct", 3.0)
        global_real_policy = as_float(row, "real_policy_rate_pct", 0.7)
        global_10y = as_float(row, "global_10y_yield_pct", 3.8)
        global_real_10y = as_float(row, "global_real_10y_yield_pct", 1.5)
        global_term_spread = as_float(row, "term_spread_10y_2y_pct", 0.4)
        global_dollar = as_float(row, "global_dollar_index", 100.0)
        global_dollar_yoy = as_float(row, "dollar_yoy_change_pct")
        global_liquidity = as_float(row, "global_liquidity_index", 55.0)
        global_fci = as_float(row, "global_financial_conditions_index")
        global_risk = as_float(row, "risk_appetite_index", 50.0)
        global_ig = as_float(row, "global_investment_grade_spread_bps", 120.0)
        global_hy = as_float(row, "global_high_yield_spread_bps", 450.0)
        global_default = as_float(row, "default_risk_index", 30.0)
        global_credit_availability = as_float(row, "credit_availability_index", 60.0)
        global_bank_stress = as_float(row, "bank_credit_stress_index", 42.0)
        global_equity_return = as_float(row, "equity_total_return_pct")
        global_equity_valuation_pe = as_float(row, "equity_valuation_pe", 17.0)
        global_bond_return = as_float(row, "sovereign_bond_total_return_pct")
        brent_price = as_float(row, "brent_oil_price_usd", 82.0)
        oil_yoy = as_float(row, "oil_yoy_change_pct")
        commodity_yoy = as_float(row, "commodity_yoy_change_pct")
        energy_pressure = as_float(row, "energy_cost_pressure_index", 50.0)
        feedback_intensity = as_float(row, "macro_feedback_intensity_index")
        branch = build_branch_transmission(row, region)
        active_branch = branch_is_active(branch)
        branch_growth = as_float(branch, "regional_branch_growth_impulse_pct") if active_branch else 0.0
        branch_inflation = as_float(branch, "regional_branch_inflation_impulse_pct") if active_branch else 0.0
        branch_policy = as_float(branch, "regional_branch_policy_impulse_pct") if active_branch else 0.0
        branch_credit = as_float(branch, "regional_branch_credit_impulse_bps") if active_branch else 0.0
        branch_fx = as_float(branch, "regional_branch_fx_pressure_impulse") if active_branch else 0.0
        branch_energy = as_float(branch, "regional_branch_energy_impulse") if active_branch else 0.0
        branch_liquidity = as_float(branch, "regional_branch_liquidity_impulse") if active_branch else 0.0
        branch_asset = as_float(branch, "regional_branch_asset_impulse_pct") if active_branch else 0.0
        branch_confidence = as_float(branch, "regional_branch_confidence_impulse") if active_branch else 0.0
        branch_stress = (
            as_float(branch, "regional_branch_strength_index") * 0.08
            + max(0.0, as_float(branch, "regional_branch_credit_impulse_bps")) / 14.0
        ) if active_branch else 0.0

        local_noise = rng.gauss(0.0, region.shock_volatility)
        stress_noise = rng.gauss(0.0, region.shock_volatility * 2.2)
        inflation_noise = rng.gauss(0.0, region.shock_volatility * 0.22)
        asset_noise = rng.gauss(0.0, region.shock_volatility * 2.1)

        regional_potential = clamp(
            region.trend_growth_pct
            + seed_growth_bias
            + 0.22 * (global_potential - 2.25)
            + 0.12 * (region.domestic_demand_weight - 0.70)
            + 0.08 * region.infrastructure_sensitivity
            + 0.010 * seed_investment_bias
            + 0.006 * seed_openness_bias
            - 0.006 * max(0.0, global_stress - 45.0),
            region.potential_growth_floor_pct,
            region.potential_growth_ceiling_pct,
        )
        base_output_gap_target = (
            0.70 * global_output_gap
            + 0.014 * (global_risk - 50.0) * region.equity_wealth_sensitivity
            - 0.32 * global_fci * region.policy_rate_sensitivity
            - 0.0032 * max(0.0, global_hy - 500.0) * region.credit_sensitivity
            - 0.10 * max(0.0, global_real_policy - 1.0) * region.policy_rate_sensitivity
            - 0.007 * max(0.0, energy_pressure - 58.0) * region.energy_import_sensitivity
            + 0.72 * branch_growth
            - 0.0045 * max(0.0, branch_credit)
            + 0.026 * seed_investment_bias
            + 0.012 * seed_openness_bias
            + local_noise
        )
        policy_support_index = clamp(
            region.policy_support_sensitivity
            * (
                0.32 * max(0.0, -base_output_gap_target)
                + 0.020 * max(0.0, global_stress - 42.0)
                + 0.012 * max(0.0, global_hy - 520.0)
                + 0.22 * max(0.0, 2.0 - global_headline)
            ),
            0.0,
            5.0,
        )
        infrastructure_impulse = clamp(policy_support_index * region.infrastructure_sensitivity, 0.0, 4.5)
        output_gap_target = base_output_gap_target + 0.16 * policy_support_index + 0.10 * infrastructure_impulse
        regional_output_gap = clamp(
            smooth(prev_output_gap, output_gap_target, 0.36),
            region.output_gap_floor_pct,
            region.output_gap_ceiling_pct,
        )

        raw_growth = (
            regional_potential
            + 0.30 * regional_output_gap
            + 0.34 * (global_growth - global_potential)
            - 0.0055 * max(0.0, global_stress - 42.0)
            - 0.0040 * max(0.0, global_hy - 520.0) * region.credit_sensitivity
            + 0.0048 * (global_risk - 50.0) * region.equity_wealth_sensitivity
            - 0.012 * max(0.0, oil_yoy - 18.0) * region.energy_import_sensitivity
            + 0.17 * policy_support_index
            + 0.11 * infrastructure_impulse
            + 0.020 * seed_investment_bias
            + 0.010 * seed_openness_bias
            + branch_growth
            - 0.0040 * max(0.0, branch_credit)
            + local_noise * 0.36
        )
        raw_growth = clamp(smooth(prev_growth, raw_growth, 0.42), region.raw_growth_floor_pct, region.raw_growth_ceiling_pct)
        growth_adjustment = clamp((global_growth - raw_growth) * anchor_strength, -0.95, 0.95)
        regional_growth = clamp(raw_growth + growth_adjustment, region.growth_floor_pct, region.growth_ceiling_pct)
        if year_index > 0:
            regional_gdp_index = compound_index(regional_gdp_index, regional_growth, 25.0)

        raw_headline = (
            0.58 * global_headline
            + 0.42 * (
                region.inflation_anchor_pct
                + 0.13 * regional_output_gap
                + 0.020 * oil_yoy * region.energy_import_sensitivity
                + 0.010 * global_import * region.international_exposure
                + 0.006 * max(0.0, global_dollar - 100.0) * max(0.0, region.dollar_sensitivity)
            )
            + inflation_noise
            + branch_inflation
        )
        raw_headline = clamp(smooth(prev_headline, raw_headline, 0.48), -0.8, 8.5)
        inflation_adjustment = clamp((global_headline - raw_headline) * anchor_strength * 0.74, -0.75, 0.75)
        regional_headline = clamp(
            raw_headline + inflation_adjustment,
            *REGIONAL_RECONCILED_FIELD_BOUNDS["regional_headline_inflation_pct"],
        )

        raw_core = (
            0.66 * global_core
            + 0.34 * (
                region.core_inflation_anchor_pct
                + 0.10 * regional_output_gap
                + 0.12 * (regional_growth - regional_potential)
            )
            + inflation_noise * 0.45
        )
        regional_core = clamp(
            smooth(prev_core, raw_core, 0.40)
            + inflation_adjustment * 0.42
            + branch_inflation * 0.36,
            *REGIONAL_RECONCILED_FIELD_BOUNDS["regional_core_inflation_pct"],
        )
        regional_energy = clamp(
            0.72 * global_energy + 0.20 * oil_yoy * region.energy_import_sensitivity + inflation_noise * 1.8 + branch_energy * 0.22,
            -8.0,
            22.0,
        )
        regional_import = clamp(
            0.62 * global_import
            + 0.20 * global_dollar_yoy * region.dollar_sensitivity
            + 0.16 * commodity_yoy * region.international_exposure
            + 0.10 * branch_fx
            + 0.06 * branch_energy,
            -3.0,
            8.5,
        )
        regional_expectation = clamp(0.68 * global_expectation + 0.22 * regional_core + 0.10 * regional_headline, 0.4, 5.8)

        raw_currency = (
            100.0
            + region.currency_dollar_beta * (global_dollar - 100.0)
            + region.dollar_sensitivity * (regional_headline - global_headline) * 2.5
            + branch_fx
            + rng.gauss(0.0, 0.30 * (1.0 - 0.55 * region.fx_management_strength))
        )
        regional_currency = clamp(
            100.0 + (raw_currency - 100.0) * (1.0 - 0.55 * region.fx_management_strength),
            82.0,
            128.0,
        )
        regional_currency_yoy = pct_change(regional_currency, prev_currency_index)
        fx_volatility = clamp(5.0 + 0.72 * abs(regional_currency_yoy) + 0.22 * abs(global_dollar_yoy), 1.0, 55.0)
        currency_pressure = clamp(
            28.0
            + 1.35 * fx_volatility
            + 0.18 * max(0.0, global_dollar - 104.0) * (0.55 + max(0.0, region.dollar_sensitivity))
            + 0.08 * max(0.0, regional_headline - 3.5) * 10.0
            + branch_fx,
            0.0,
            100.0,
        )
        regional_liquidity = clamp(
            0.78 * global_liquidity
            + 0.12 * as_float(row, "qe_liquidity_index", 8.0)
            + 0.08 * (global_credit_availability - 58.0)
            - 0.36 * max(0.0, global_real_policy - 1.2) * region.policy_rate_sensitivity
            + 4.2 * policy_support_index
            + branch_liquidity,
            0.0,
            100.0,
        )
        regional_risk_appetite = clamp(
            0.76 * global_risk
            + 0.14 * regional_liquidity
            + 0.16 * (regional_growth - regional_potential) * 8.0
            + 0.10 * seed_investment_bias
            + 0.06 * seed_openness_bias
            - 0.04 * max(0.0, global_hy - 500.0),
            0.0,
            100.0,
        )

        domestic_policy_target = (
            region.policy_neutral_rate_pct
            + 0.22 * (regional_core - region.core_inflation_anchor_pct)
            + 0.10 * regional_output_gap
            - 0.30 * policy_support_index
            + branch_policy
        )
        raw_policy = (
            region.policy_global_beta * global_policy
            + (1.0 - region.policy_global_beta) * domestic_policy_target
            + 0.08 * (regional_core - global_core)
            + 0.06 * regional_output_gap
            + 0.04 * (regional_headline - global_headline)
            + branch_policy * 0.38
        )
        rate_adjustment = clamp((global_policy - raw_policy) * anchor_strength * 0.88 * region.rate_anchor_weight, -0.60, 0.60)
        regional_policy = clamp(raw_policy + rate_adjustment, region.policy_floor_pct, region.policy_ceiling_pct)
        regional_real_policy = regional_policy - regional_expectation

        domestic_long_rate_target = (
            region.long_rate_neutral_pct
            + 0.18 * (regional_expectation - region.inflation_anchor_pct)
            + 0.06 * (regional_growth - regional_potential)
            + 0.004 * max(0.0, global_hy - 450.0)
        )
        raw_10y = (
            region.long_rate_global_beta * global_10y
            + (1.0 - region.long_rate_global_beta) * domestic_long_rate_target
            + 0.08
            + 0.10 * (regional_headline - global_headline)
            + 0.05 * (regional_growth - global_growth)
            + 0.03 * (regional_policy - global_policy)
            + branch_policy * 0.45
            + branch_credit / 550.0
        )
        regional_10y = clamp(
            raw_10y
            + (global_10y - raw_10y)
            * anchor_strength
            * 0.68
            * region.rate_anchor_weight,
            *REGIONAL_RECONCILED_FIELD_BOUNDS["regional_10y_yield_pct"],
        )
        regional_real_10y = regional_10y - regional_expectation
        regional_term_spread = clamp(
            global_term_spread
            + 0.05 * (regional_growth - global_growth)
            - 0.03 * (regional_policy - global_policy)
            - 0.004 * max(0.0, global_stress - 55.0),
            -3.2,
            4.0,
        )
        regional_fci = clamp(
            0.72 * global_fci
            + 0.18 * max(0.0, regional_real_policy)
            + 0.012 * max(0.0, regional_10y - 4.0)
            - 0.012 * (regional_liquidity - 55.0)
            + 0.0025 * max(0.0, global_hy - 500.0)
            + 0.0025 * max(0.0, branch_credit)
            - 0.010 * branch_liquidity,
            -4.0,
            5.2,
        )

        financial_stress = clamp(
            0.62 * global_stress
            + 5.5 * max(0.0, regional_fci)
            + 0.018 * max(0.0, global_hy - 520.0) * region.credit_sensitivity
            + 0.28 * currency_pressure
            - 0.10 * (regional_liquidity - 55.0)
            + branch_stress
            + stress_noise,
            0.0,
            100.0,
        )
        raw_ig = (
            region.ig_global_beta * global_ig
            + (1.0 - region.ig_global_beta) * (105.0 + 2.6 * max(0.0, financial_stress - 35.0))
            + 3.8 * max(0.0, regional_fci)
            + 0.13 * max(0.0, financial_stress - 45.0)
            - 2.8 * policy_support_index
        )
        raw_hy = (
            region.credit_global_beta * global_hy
            + (1.0 - region.credit_global_beta) * (360.0 + 5.2 * max(0.0, financial_stress - 35.0))
            + 34.0 * max(0.0, regional_fci) * region.credit_sensitivity
            + 1.10 * max(0.0, financial_stress - 38.0) * region.credit_sensitivity
            - 0.36 * (regional_liquidity - 55.0)
            - 17.5 * policy_support_index
        )
        credit_adjustment = clamp((global_hy - raw_hy) * anchor_strength * 0.52, -140.0, 140.0)
        regional_ig = clamp(
            raw_ig + credit_adjustment * 0.18 + branch_credit * 0.24,
            *REGIONAL_RECONCILED_FIELD_BOUNDS["regional_ig_spread_bps"],
        )
        regional_hy = clamp(
            raw_hy + credit_adjustment + branch_credit,
            *REGIONAL_RECONCILED_FIELD_BOUNDS["regional_hy_spread_bps"],
        )
        default_risk = clamp(
            0.72 * global_default
            + 0.030 * max(0.0, regional_hy - 450.0)
            + 0.22 * max(0.0, global_bank_stress - 45.0)
            + 0.25 * branch_stress
            - 1.2 * policy_support_index,
            0.0,
            100.0,
        )
        credit_availability = clamp(
            0.64 * global_credit_availability
            + 0.18 * regional_liquidity
            - 0.030 * max(0.0, regional_hy - 480.0)
            - 0.18 * max(0.0, regional_real_policy - 1.5) * 10.0
            + 2.2 * policy_support_index
            + branch_liquidity * 0.42,
            0.0,
            100.0,
        )
        credit_stress = clamp(
            28.0
            + 0.030 * regional_hy
            + 0.10 * default_risk
            + 0.26 * max(0.0, financial_stress - 40.0)
            - 0.20 * credit_availability,
            0.0,
            100.0,
        )

        confidence = clamp(
            50.0
            + 4.8 * regional_output_gap
            + 0.36 * (regional_risk_appetite - 50.0)
            - 0.18 * financial_stress
            - 1.05 * max(0.0, regional_headline - 3.1)
            - 0.022 * max(0.0, regional_hy - 500.0)
            + 0.18 * global_equity_return * region.equity_wealth_sensitivity
            + 0.08 * seed_aviation_bias
            + 0.06 * seed_investment_bias
            + 0.35 * policy_support_index
            + branch_confidence,
            0.0,
            100.0,
        )
        real_income_growth = clamp(
            0.58 * regional_growth
            + 0.18 * regional_potential
            - 0.38 * max(0.0, regional_headline - 2.4)
            + 0.034 * (confidence - 50.0)
            - 0.15 * max(0.0, regional_real_policy - 1.4)
            + 0.10 * branch_growth
            - 0.08 * max(0.0, branch_inflation),
            -5.5,
            6.2,
        )
        if year_index > 0:
            regional_income_index = compound_index(regional_income_index, real_income_growth, 35.0)
        consumption_power = clamp(
            50.0
            + 6.3 * real_income_growth
            + 0.12 * (regional_income_index - 100.0)
            + 0.26 * confidence
            - 2.2 * max(0.0, regional_headline - 3.0),
            0.0,
            100.0,
        )

        raw_equity_return = (
            region.asset_global_beta * global_equity_return
            + 0.11 * (regional_growth - global_growth) * 10.0
            + 0.040 * (regional_risk_appetite - 50.0) * region.equity_wealth_sensitivity
            - 0.010 * max(0.0, regional_hy - 500.0)
            - 0.70 * max(0.0, regional_real_10y - 2.0)
            + 0.85 * policy_support_index
            + branch_asset
            + asset_noise
        )
        equity_adjustment = clamp((global_equity_return - raw_equity_return) * anchor_strength * 0.42, -5.5, 5.5)
        regional_equity_return = clamp(
            raw_equity_return + equity_adjustment,
            *REGIONAL_RECONCILED_FIELD_BOUNDS["regional_equity_return_pct"],
        )
        regional_equity_valuation_pe = clamp(
            global_equity_valuation_pe
            + 0.24 * (regional_growth - global_growth)
            + 0.035 * (regional_risk_appetite - global_risk)
            - 0.55 * max(0.0, regional_real_10y - global_real_10y)
            - 0.0025 * max(0.0, regional_hy - global_hy)
            + 0.025 * branch_asset,
            *REGIONAL_RECONCILED_FIELD_BOUNDS["regional_equity_valuation_pe"],
        )
        raw_bond_return = (
            region.bond_global_beta * global_bond_return
            - 0.32 * max(0.0, regional_headline - 3.5)
            + 0.15 * max(0.0, financial_stress - 55.0)
            - 0.22 * max(0.0, regional_10y - global_10y)
        )
        regional_bond_return = clamp(raw_bond_return, -26.0, 26.0)
        if year_index > 0:
            regional_equity_index = compound_index(regional_equity_index, regional_equity_return, 12.0)
            regional_bond_index = compound_index(regional_bond_index, regional_bond_return, 25.0)
        wealth_effect = clamp(
            48.0
            + 0.61 * regional_equity_return * region.equity_wealth_sensitivity
            + 0.24 * regional_bond_return
            + 0.24 * (confidence - 50.0)
            + 0.018 * (regional_equity_index - 100.0),
            0.0,
            100.0,
        )

        energy_cost = clamp(
            0.66 * energy_pressure
            + 0.34
            * (
                50.0
                + 0.22 * (brent_price - 82.0) * region.energy_import_sensitivity
                + 0.28 * oil_yoy * region.energy_import_sensitivity
            )
            - 0.05 * (regional_currency - 100.0)
            + 2.2 * region.energy_import_sensitivity
            + branch_energy,
            *REGIONAL_RECONCILED_FIELD_BOUNDS["regional_energy_cost_pressure_index"],
        )
        terms_of_trade = clamp(
            50.0
            + 0.08 * (regional_currency - 100.0)
            + 0.04 * (brent_price - 82.0) * region.commodity_export_sensitivity
            - 0.06 * max(0.0, oil_yoy - 18.0) * region.energy_import_sensitivity
            + 0.04 * commodity_yoy
            - 0.30 * branch_energy
            - 0.08 * branch_fx,
            0.0,
            100.0,
        )
        commodity_pressure = clamp(
            50.0
            + 0.30 * commodity_yoy
            + 0.20 * oil_yoy * region.energy_import_sensitivity
            - 0.06 * (regional_currency - 100.0),
            0.0,
            100.0,
        )
        policy_uncertainty = clamp(
            18.0
            + 4.5 * abs(as_float(row, "policy_rate_change_pct"))
            + 0.18 * feedback_intensity
            + 0.10 * financial_stress
            + 2.4 * abs(regional_term_spread)
            + 0.10 * max(0.0, regional_headline - 3.5) * 10.0
            + 0.50 * abs(branch_policy)
            + 0.04 * as_float(branch, "regional_branch_strength_index"),
            0.0,
            100.0,
        )
        geopolitical_risk = clamp(
            16.0
            + 0.10 * global_stress * region.geopolitical_sensitivity
            + 0.12 * currency_pressure
            + 0.08 * energy_cost
            + 0.20 * max(0.0, branch_fx)
            + 0.05 * max(0.0, branch_energy),
            0.0,
            100.0,
        )
        macro_stress = clamp(
            0.26 * financial_stress
            + 0.28 * credit_stress
            + 0.12 * currency_pressure
            + 0.12 * policy_uncertainty
            + 0.12 * default_risk
            + 0.032 * max(0.0, regional_hy - 360.0)
            + 0.10 * max(0.0, regional_headline - 3.2) * 10.0
            + 0.04 * geopolitical_risk
            + branch_stress * 0.45,
            *REGIONAL_RECONCILED_FIELD_BOUNDS["regional_macro_stress_index"],
        )

        adjustment_index = (
            abs(growth_adjustment) * 12.0
            + abs(inflation_adjustment) * 9.0
            + abs(rate_adjustment) * 7.0
            + abs(credit_adjustment) / 32.0
            + abs(equity_adjustment) * 1.2
        )
        reconciliation_converged = str(adjustment_index < 9.0).lower()

        growth_regime = classify_growth_regime(
            regional_growth,
            regional_potential,
            regional_output_gap,
            credit_stress,
            financial_stress,
            regional_real_policy,
        )
        inflation_regime = classify_regional_inflation(
            regional_headline,
            regional_core,
            regional_energy,
            regional_growth,
        )
        macro_regime = classify_macro_regime(
            regional_growth,
            regional_potential,
            regional_output_gap,
            regional_headline,
            regional_hy,
            credit_stress,
            regional_equity_return,
            macro_stress,
            confidence,
        )

        records.append(
            round_record(
                {
                    "regional_macro_param_version": REGIONAL_MACRO_PARAM_VERSION,
                    "regional_macro_interface_version": REGIONAL_MACRO_INTERFACE_VERSION,
                    "region_id": region.region_id,
                    "region_name": region.region_name,
                    "regional_reconciliation_scope": "single_region_soft_anchor",
                    "year_index": year_index,
                    "year": int(row["year"]),
                    "seed": seed,
                    "regional_global_weight": region.global_weight,
                    "regional_structural_seed_version": seed_profile["version"],
                    "regional_seed_potential_enabled": seed_profile["enabled"],
                    "regional_seed_potential_template_id": seed_profile["template_id"],
                    "regional_seed_primary_theme": seed_profile["primary_theme"],
                    "regional_seed_secondary_theme": seed_profile["secondary_theme"],
                    "regional_seed_structural_score": seed_profile["structural_score"],
                    "regional_seed_theme_score": seed_profile["theme_score"],
                    "regional_seed_momentum_label": seed_profile["momentum_label"],
                    "regional_seed_annual_growth_bias_pct": seed_profile["annual_growth_bias_pct"],
                    "regional_seed_effect_release_pct": seed_profile["effect_release_pct"],
                    "regional_seed_effective_growth_bias_pct": seed_profile["effective_growth_bias_pct"],
                    "regional_seed_aviation_propensity_bias_pct": seed_profile["aviation_propensity_bias_pct"],
                    "regional_seed_investment_cycle_bias_pct": seed_profile["investment_cycle_bias_pct"],
                    "regional_seed_openness_bias_pct": seed_profile["openness_bias_pct"],
                    "regional_seed_demand_multiplier": seed_profile["demand_multiplier"],
                    "regional_reconciliation_pass": 2,
                    "regional_reconciliation_converged": reconciliation_converged,
                    "regional_reconciliation_adjustment_index": adjustment_index,
                    "regional_gdp_index": regional_gdp_index,
                    "regional_gdp_growth_pct": regional_growth,
                    "regional_potential_growth_pct": regional_potential,
                    "regional_output_gap_pct": regional_output_gap,
                    "regional_financial_stress_index": financial_stress,
                    "regional_growth_regime": growth_regime,
                    "regional_headline_inflation_pct": regional_headline,
                    "regional_core_inflation_pct": regional_core,
                    "regional_energy_inflation_pct": regional_energy,
                    "regional_import_inflation_pct": regional_import,
                    "regional_inflation_expectation_pct": regional_expectation,
                    "regional_inflation_regime": inflation_regime,
                    "regional_income_index": regional_income_index,
                    "real_income_growth_pct": real_income_growth,
                    "household_consumption_power_index": consumption_power,
                    "consumer_confidence_index": confidence,
                    "regional_policy_rate_pct": regional_policy,
                    "regional_real_policy_rate_pct": regional_real_policy,
                    "regional_10y_yield_pct": regional_10y,
                    "regional_real_10y_yield_pct": regional_real_10y,
                    "regional_term_spread_pct": regional_term_spread,
                    "regional_financial_conditions_index": regional_fci,
                    "regional_currency_index": regional_currency,
                    "regional_currency_yoy_pct": regional_currency_yoy,
                    "currency_pressure_index": currency_pressure,
                    "fx_volatility_index": fx_volatility,
                    "regional_liquidity_index": regional_liquidity,
                    "regional_risk_appetite_index": regional_risk_appetite,
                    "regional_ig_spread_bps": regional_ig,
                    "regional_hy_spread_bps": regional_hy,
                    "regional_credit_availability_index": credit_availability,
                    "regional_default_risk_index": default_risk,
                    "regional_credit_stress_index": credit_stress,
                    "regional_equity_index": regional_equity_index,
                    "regional_equity_return_pct": regional_equity_return,
                    "regional_equity_valuation_pe": regional_equity_valuation_pe,
                    "regional_bond_index": regional_bond_index,
                    "regional_bond_return_pct": regional_bond_return,
                    "regional_wealth_effect_index": wealth_effect,
                    "regional_energy_cost_pressure_index": energy_cost,
                    "regional_terms_of_trade_index": terms_of_trade,
                    "regional_commodity_pressure_index": commodity_pressure,
                    "regional_macro_stress_index": macro_stress,
                    "regional_policy_uncertainty_index": policy_uncertainty,
                    "regional_geopolitical_risk_index": geopolitical_risk,
                    "regional_macro_regime": macro_regime,
                    **branch,
                    "global_growth_anchor_pct": global_growth,
                    "global_output_gap_anchor_pct": global_output_gap,
                    "global_inflation_anchor_pct": global_headline,
                    "global_core_inflation_anchor_pct": global_core,
                    "global_policy_anchor_pct": global_policy,
                    "global_10y_anchor_pct": global_10y,
                    "global_hy_anchor_bps": global_hy,
                    "global_equity_return_anchor_pct": global_equity_return,
                    "global_equity_valuation_pe_anchor": global_equity_valuation_pe,
                    "growth_reconciliation_adjustment_pct": growth_adjustment,
                    "inflation_reconciliation_adjustment_pct": inflation_adjustment,
                    "rate_reconciliation_adjustment_pct": rate_adjustment,
                    "credit_reconciliation_adjustment_bps": credit_adjustment,
                    "equity_reconciliation_adjustment_pct": equity_adjustment,
                }
            )
        )

        prev_growth = regional_growth
        prev_output_gap = regional_output_gap
        prev_headline = regional_headline
        prev_core = regional_core
        prev_currency_index = regional_currency

    return records


def summarize_region_seed(records: list[dict[str, Any]]) -> dict[str, Any]:
    data = records[1:] if len(records) > 1 else records
    growth_values = [as_float(row, "regional_gdp_growth_pct") for row in data]
    inflation_values = [as_float(row, "regional_headline_inflation_pct") for row in data]
    hy_values = [as_float(row, "regional_hy_spread_bps") for row in data]
    stress_values = [as_float(row, "regional_macro_stress_index") for row in data]
    final = records[-1]
    return {
        "region_id": str(final["region_id"]),
        "region_name": str(final["region_name"]),
        "seed": int(final["seed"]),
        "start_year": int(records[0]["year"]),
        "end_year": int(final["year"]),
        "average_growth_pct": round(mean(growth_values), 3) if growth_values else 0.0,
        "growth_std_pct": round(pstdev(growth_values), 3) if len(growth_values) > 1 else 0.0,
        "average_headline_inflation_pct": round(mean(inflation_values), 3) if inflation_values else 0.0,
        "average_hy_spread_bps": round(mean(hy_values), 2) if hy_values else 0.0,
        "average_macro_stress_index": round(mean(stress_values), 2) if stress_values else 0.0,
        "regional_seed_momentum_label": str(final.get("regional_seed_momentum_label", "none")),
        "regional_seed_effective_growth_bias_pct": as_float(final, "regional_seed_effective_growth_bias_pct"),
        "regional_seed_aviation_propensity_bias_pct": as_float(final, "regional_seed_aviation_propensity_bias_pct"),
        "regional_seed_demand_multiplier": as_float(final, "regional_seed_demand_multiplier", 1.0),
        "final_regional_gdp_index": as_float(final, "regional_gdp_index"),
        "final_regional_income_index": as_float(final, "regional_income_index"),
        "final_regional_equity_index": as_float(final, "regional_equity_index"),
        "final_regional_equity_valuation_pe": as_float(final, "regional_equity_valuation_pe"),
        "final_regional_macro_regime": str(final.get("regional_macro_regime", "none")),
    }


def write_viewer_data_js(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(rows, ensure_ascii=False, separators=(",", ":"))
    path.write_text(f"window.REGIONAL_MACRO_DATA = {payload};\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate regional macro paths from the global macro stack.")
    parser.add_argument("--region", default="north_america", choices=sorted(REGION_CONFIGS), help="Region id to simulate.")
    parser.add_argument("--years", type=int, default=60, help="Number of simulated years after the initial year.")
    parser.add_argument("--start-year", type=int, default=2025, help="Calendar year for the initial observation.")
    parser.add_argument("--initial-gdp", type=float, default=110.0, help="Initial global GDP in trillion USD.")
    parser.add_argument("--volatility-scale", type=float, default=1.55, help="Scales global GDP cycle amplitude and random shocks.")
    parser.add_argument("--feedback-iterations", type=int, default=16, help="Maximum global feedback calibration reruns.")
    parser.add_argument(
        "--min-feedback-iterations",
        type=int,
        default=3,
        help="Minimum feedback passes before the convergence check is applied.",
    )
    parser.add_argument("--seed", type=int, default=None, help="Run one seed only.")
    parser.add_argument("--seeds", type=int, nargs="*", default=None, help="Run an explicit list of seeds.")
    parser.add_argument("--seed-start", type=int, default=1, help="First seed when --seed/--seeds is omitted.")
    parser.add_argument("--seed-count", type=int, default=8, help="Number of seeds when --seed/--seeds is omitted.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "output" / "regional_macro",
        help="Directory for regional macro outputs.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.years < 1:
        raise SystemExit("--years must be at least 1")
    if args.volatility_scale <= 0:
        raise SystemExit("--volatility-scale must be positive")
    if args.feedback_iterations < 0:
        raise SystemExit("--feedback-iterations must be non-negative")
    if args.min_feedback_iterations < 0:
        raise SystemExit("--min-feedback-iterations must be non-negative")
    region = REGION_CONFIGS[args.region]
    seeds = resolve_seeds(args)
    global_params = build_global_params(args)

    records_by_seed: dict[int, list[dict[str, Any]]] = {}
    convergence_by_seed: dict[int, dict[str, Any]] = {}
    all_records: list[dict[str, Any]] = []
    for seed in seeds:
        global_records, convergence = run_global_macro_for_seed(
            seed,
            global_params,
            args.feedback_iterations,
            min_feedback_iterations=args.min_feedback_iterations,
        )
        regional_records = simulate_region_for_global_path(global_records, region, seed)
        records_by_seed[seed] = regional_records
        convergence_by_seed[seed] = convergence
        all_records.extend(regional_records)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = args.output_dir / f"{region.region_id}_regional_macro_seed_sweep.csv"
    json_path = args.output_dir / f"{region.region_id}_regional_macro_seed_sweep.json"
    viewer_data_path = args.output_dir / f"{region.region_id}_regional_macro_viewer_data.js"

    write_csv(csv_path, all_records, REGIONAL_MACRO_FIELDS)
    write_json(
        json_path,
        {
            "regional_macro_param_version": REGIONAL_MACRO_PARAM_VERSION,
            "regional_macro_interface_version": REGIONAL_MACRO_INTERFACE_VERSION,
            "region": asdict(region),
            "region_configs_available": sorted(REGION_CONFIGS),
            "reconciliation_scope": "single_region_soft_anchor",
            "reconciliation_note": "Full weighted regional reconciliation starts after more regions are implemented.",
            "seeds": seeds,
            "years": args.years,
            "start_year": args.start_year,
            "feedback_iterations": args.feedback_iterations,
            "global_params": {key: asdict(value) for key, value in global_params.items() if hasattr(value, "__dataclass_fields__")},
            "global_convergence": convergence_by_seed,
            "summaries": [summarize_region_seed(records) for records in records_by_seed.values()],
            "outputs": {
                "csv": str(csv_path),
                "json": str(json_path),
                "viewer_data_js": str(viewer_data_path),
            },
        },
    )
    write_viewer_data_js(viewer_data_path, all_records)

    print(f"Wrote {csv_path}")
    print(f"Wrote {json_path}")
    print(f"Wrote {viewer_data_path}")
    for summary in [summarize_region_seed(records) for records in records_by_seed.values()]:
        print(
            "Seed {seed}: avg growth {average_growth_pct:.2f}%, avg inflation "
            "{average_headline_inflation_pct:.2f}%, final GDP index {final_regional_gdp_index:.1f}, "
            "regime {final_regional_macro_regime}".format(**summary)
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
