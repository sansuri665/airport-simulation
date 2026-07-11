from __future__ import annotations

from importlib import import_module

_SIBLING_PREFIX = f"{__package__}." if __package__ else ""
simulation_io = import_module(f"{_SIBLING_PREFIX}simulation_io")
simulation_utils = import_module(f"{_SIBLING_PREFIX}simulation_utils")

read_csv = simulation_io.read_csv_utf8_sig
write_csv = simulation_io.write_csv_utf8_sig_with_extra_fields
write_json = simulation_io.write_json_utf8_data
as_float = simulation_utils.as_float_convert_lookup_default
clamp = simulation_utils.clamp
safe_divide = simulation_utils.safe_divide

import argparse
import csv
import json
import math
from pathlib import Path
from statistics import mean, pstdev
from typing import Any


CITY_AIRPORT_VALUATION_FORECAST_PARAM_VERSION = "city-airport-valuation-forecast-layer-v0.5"
CITY_AIRPORT_VALUATION_FORECAST_INTERFACE_VERSION = "city-airport-valuation-forecast-interface-v0.5"

AIRPORT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_DIR = AIRPORT_DIR / "config" / "city_airport_valuation"
QUARTERS = ("Q1", "Q2", "Q3", "Q4")

VALUATION_FORECAST_FIELDS = [
    "city_airport_valuation_forecast_param_version",
    "city_airport_valuation_forecast_interface_version",
    "valuation_config_version",
    "valuation_scenario_tag",
    "valuation_primary_method",
    "operator_id",
    "operator_name",
    "city_airport_market_id",
    "city_name",
    "region_id",
    "region_name",
    "seed",
    "currency",
    "amount_unit",
    "as_of_year",
    "as_of_quarter",
    "as_of_period_index",
    "data_cutoff_year",
    "data_cutoff_quarter",
    "game_phase",
    "player_decision_enabled",
    "forecast_horizon_quarters",
    "forecast_horizon_years",
    "history_quarters_used",
    "branch_scenario_id",
    "branch_scenario_state",
    "annual_served_passengers_million",
    "current_annual_revenue_million_cny",
    "current_annual_operating_profit_million_cny",
    "current_annual_accounting_profit_million_cny",
    "current_annual_commercial_profit_million_cny",
    "current_annual_contract_revenue_million_cny",
    "current_annual_depreciation_million_cny",
    "current_operating_margin_pct",
    "current_cash_million_cny",
    "current_short_term_debt_million_cny",
    "current_long_term_debt_million_cny",
    "current_total_debt_million_cny",
    "recognized_cash_million_cny",
    "net_debt_million_cny",
    "total_assets_million_cny",
    "total_liabilities_million_cny",
    "liability_to_asset_ratio_pct",
    "fixed_asset_book_value_million_cny",
    "construction_in_progress_million_cny",
    "city_airport_perceived_quality_index",
    "quarter_design_utilization_pct",
    "quarter_max_utilization_pct",
    "forecast_annual_passenger_growth_pct",
    "forecast_annual_revenue_growth_pct",
    "forecast_target_operating_margin_pct",
    "forecast_maintenance_capex_year1_million_cny",
    "forecast_year_1_revenue_million_cny",
    "forecast_year_1_operating_profit_million_cny",
    "forecast_year_1_maintenance_capex_million_cny",
    "forecast_year_1_fcff_million_cny",
    "forecast_year_2_revenue_million_cny",
    "forecast_year_2_operating_profit_million_cny",
    "forecast_year_2_maintenance_capex_million_cny",
    "forecast_year_2_fcff_million_cny",
    "forecast_year_3_revenue_million_cny",
    "forecast_year_3_operating_profit_million_cny",
    "forecast_year_3_maintenance_capex_million_cny",
    "forecast_year_3_fcff_million_cny",
    "forecast_year_4_revenue_million_cny",
    "forecast_year_4_operating_profit_million_cny",
    "forecast_year_4_maintenance_capex_million_cny",
    "forecast_year_4_fcff_million_cny",
    "forecast_year_5_revenue_million_cny",
    "forecast_year_5_operating_profit_million_cny",
    "forecast_year_5_maintenance_capex_million_cny",
    "forecast_year_5_fcff_million_cny",
    "forecast_5y_fcff_sum_million_cny",
    "operating_5y_normalized_fcff_sum_million_cny",
    "risk_free_rate_pct",
    "base_airport_risk_premium_pct",
    "macro_risk_premium_pct",
    "leverage_risk_premium_pct",
    "quality_risk_premium_pct",
    "crowding_risk_premium_pct",
    "branch_risk_premium_pct",
    "input_equity_return_pct",
    "input_equity_valuation_pe",
    "operating_discount_rate_pct",
    "operating_terminal_growth_pct",
    "normalized_terminal_fcff_million_cny",
    "pv_operating_forecast_fcff_million_cny",
    "operating_terminal_value_million_cny",
    "pv_operating_terminal_value_million_cny",
    "operating_enterprise_value_million_cny",
    "market_valuation_multiplier",
    "market_rate_adjustment_pct",
    "market_credit_adjustment_pct",
    "market_equity_valuation_pe",
    "market_equity_valuation_adjustment_pct",
    "market_equity_sentiment_adjustment_pct",
    "market_branch_adjustment_pct",
    "market_valuation_adjustment_pct",
    "market_valuation_adjustment_million_cny",
    "market_enterprise_value_million_cny",
    "market_enterprise_value_conservative_million_cny",
    "market_enterprise_value_optimistic_million_cny",
    "discount_rate_pct",
    "terminal_growth_pct",
    "pv_forecast_fcff_million_cny",
    "terminal_value_million_cny",
    "pv_terminal_value_million_cny",
    "asset_quality_adjustment_million_cny",
    "asset_quality_adjustment_ratio_pct",
    "contract_quality_adjustment_million_cny",
    "contract_quality_adjustment_ratio_pct",
    "net_asset_equity_value_million_cny",
    "net_asset_enterprise_value_million_cny",
    "primary_equity_value_million_cny",
    "primary_enterprise_value_million_cny",
    "experimental_operating_enterprise_value_million_cny",
    "experimental_market_enterprise_value_million_cny",
    "experimental_equity_value_million_cny",
    "experimental_equity_value_conservative_million_cny",
    "experimental_equity_value_optimistic_million_cny",
    "enterprise_value_million_cny",
    "equity_value_million_cny",
    "valuation_uncertainty_range_pct",
    "equity_value_conservative_million_cny",
    "equity_value_optimistic_million_cny",
    "operating_ev_to_current_operating_profit_multiple",
    "market_ev_to_current_operating_profit_multiple",
    "ev_to_current_operating_profit_multiple",
    "price_to_current_operating_profit_multiple",
    "price_to_current_accounting_profit_multiple",
    "price_to_book_equity_multiple",
    "equity_to_book_equity_multiple",
    "valuation_risk_tags",
    "forecast_method_note",
]


def quarter_number(quarter: str) -> int:
    if quarter in QUARTERS:
        return QUARTERS.index(quarter) + 1
    try:
        parsed = int(str(quarter).replace("Q", ""))
    except ValueError:
        parsed = 1
    return int(clamp(float(parsed), 1.0, 4.0))


def period_index(row: dict[str, Any]) -> int:
    return int(as_float(row, "year")) * 4 + quarter_number(str(row.get("quarter", "Q1"))) - 1


def row_key(row: dict[str, Any]) -> tuple[int, int, str]:
    return (
        int(as_float(row, "seed")),
        int(as_float(row, "year")),
        str(row.get("quarter", "Q1")),
    )


def round_record(record: dict[str, Any]) -> dict[str, Any]:
    rounded: dict[str, Any] = {}
    for key, value in record.items():
        if isinstance(value, float):
            rounded[key] = round(value, 4)
        else:
            rounded[key] = value
    return rounded


def load_config(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if raw.get("schema_version") != "city-airport-valuation-forecast-config-v1":
        raise ValueError(f"Unsupported city airport valuation forecast config schema in {path}")
    return raw


def sum_field(rows: list[dict[str, Any]], field: str) -> float:
    return sum(as_float(row, field) for row in rows)


def mean_field(rows: list[dict[str, Any]], field: str, default: float = 0.0) -> float:
    values = [as_float(row, field) for row in rows if row.get(field) not in (None, "")]
    return mean(values) if values else default


def recent_rows(rows: list[dict[str, Any]], count: int) -> list[dict[str, Any]]:
    return rows[-max(0, count):] if rows and count > 0 else []


def recent_annual_sum(rows: list[dict[str, Any]], field: str) -> float:
    latest = recent_rows(rows, min(4, len(rows)))
    if not latest:
        return 0.0
    value = sum_field(latest, field)
    if len(latest) < 4:
        value *= 4.0 / len(latest)
    return value


def trailing_growth_pct(rows: list[dict[str, Any]], field: str, fallback_pct: float, floor_pct: float, cap_pct: float) -> float:
    if len(rows) < 8:
        return clamp(fallback_pct, floor_pct, cap_pct)
    recent = sum_field(rows[-4:], field)
    prior = sum_field(rows[-8:-4], field)
    if prior <= 0 or recent <= 0:
        return clamp(fallback_pct, floor_pct, cap_pct)
    return clamp((recent / prior - 1.0) * 100.0, floor_pct, cap_pct)


def coefficient_of_variation(values: list[float]) -> float:
    filtered = [value for value in values if math.isfinite(value)]
    if len(filtered) < 2:
        return 0.0
    avg = mean(filtered)
    if abs(avg) <= 1e-9:
        return 0.0
    return abs(pstdev(filtered) / avg)


def annual_margin(history_ops: list[dict[str, Any]], history_fin: list[dict[str, Any]]) -> float:
    revenue = recent_annual_sum(history_ops, "total_operating_revenue_million_cny")
    profit = recent_annual_sum(history_fin, "period_operating_profit_million_cny")
    return safe_divide(profit, revenue, 0.0)


def macro_growth_adjustment_pct(operation: dict[str, Any], config: dict[str, Any]) -> float:
    settings = config["forecast"].get("macro_revenue_sensitivity", {})
    hy_baseline = float(settings.get("hy_spread_baseline_bps", 420.0))
    hy_drag = float(settings.get("hy_spread_growth_drag_per_100bps_pct", 0.0))
    hy_spread = as_float(operation, "input_hy_spread_bps", hy_baseline)
    adjustment = -max(0.0, hy_spread - hy_baseline) / 100.0 * hy_drag
    state = str(operation.get("branch_scenario_state") or "baseline")
    if state == "occurred":
        adjustment -= float(settings.get("branch_occurred_growth_drag_pct", 0.0))
    elif state == "watch":
        adjustment -= float(settings.get("branch_watch_growth_drag_pct", 0.0))
    return adjustment


def risk_premiums(operation: dict[str, Any], financial: dict[str, Any], config: dict[str, Any]) -> dict[str, float]:
    settings = config["valuation"]
    hy_baseline = float(settings.get("hy_spread_baseline_bps", 420.0))
    hy_spread = as_float(operation, "input_hy_spread_bps", hy_baseline)
    macro = max(0.0, hy_spread - hy_baseline) / 100.0 * float(
        settings.get("macro_risk_premium_per_100bps_hy_pct", 0.0)
    )
    state = str(operation.get("branch_scenario_state") or financial.get("branch_scenario_state") or "baseline")
    branch = 0.0
    if state == "occurred":
        branch = float(settings.get("branch_occurred_risk_premium_pct", 0.0))
    elif state == "watch":
        branch = float(settings.get("branch_watch_risk_premium_pct", 0.0))

    liability_ratio = as_float(financial, "total_liabilities_million_cny") / max(
        as_float(financial, "total_assets_million_cny"), 1e-9
    ) * 100.0
    leverage_start = float(settings.get("leverage_risk_start_pct", 45.0))
    leverage_full = float(settings.get("leverage_risk_full_pct", 80.0))
    leverage_cap = float(settings.get("leverage_risk_premium_cap_pct", 0.0))
    leverage = clamp((liability_ratio - leverage_start) / max(1.0, leverage_full - leverage_start), 0.0, 1.0) * leverage_cap

    quality = as_float(operation, "city_airport_perceived_quality_index", 100.0)
    quality_cap = float(settings.get("quality_risk_premium_cap_pct", 0.0))
    quality_risk = clamp((100.0 - quality) / 25.0, 0.0, 1.0) * quality_cap

    design_utilization = as_float(operation, "quarter_design_utilization_pct", 0.0)
    crowding_cap = float(settings.get("crowding_risk_premium_cap_pct", 0.0))
    crowding = clamp((design_utilization - 105.0) / 35.0, 0.0, 1.0) * crowding_cap

    return {
        "macro": macro,
        "branch": branch,
        "leverage": leverage,
        "quality": quality_risk,
        "crowding": crowding,
    }


def historical_annualized_fcff(history_fin: list[dict[str, Any]], config: dict[str, Any]) -> float:
    settings = config["valuation"].get("operating_value", {})
    forecast_config = config["forecast"]
    quarters = int(settings.get("historical_fcff_anchor_quarters", 12))
    rows = recent_rows(history_fin, quarters)
    if not rows:
        return 0.0
    maintenance_ratio = float(forecast_config.get("maintenance_capex_ratio_of_depreciation", 0.75))
    quarterly_fcff = [
        as_float(row, "period_operating_profit_million_cny")
        - as_float(row, "period_accounting_depreciation_million_cny") * maintenance_ratio
        for row in rows
    ]
    return mean(quarterly_fcff) * 4.0


def operating_discount_rate_pct(premiums: dict[str, float], config: dict[str, Any]) -> float:
    valuation_config = config["valuation"]
    settings = valuation_config.get("operating_value", {})
    normalized_risk_free = float(settings.get("normalized_risk_free_rate_pct", 3.0))
    base_premium = float(settings.get("base_operating_risk_premium_pct", valuation_config.get("base_airport_equity_risk_premium_pct", 3.6)))
    structural_weight = float(settings.get("structural_asset_risk_weight", 0.55))
    discount_rate = (
        normalized_risk_free
        + base_premium
        + structural_weight * premiums["quality"]
        + structural_weight * premiums["crowding"]
    )
    return clamp(
        discount_rate,
        float(settings.get("operating_discount_rate_floor_pct", valuation_config.get("discount_rate_floor_pct", 5.0))),
        float(settings.get("operating_discount_rate_cap_pct", valuation_config.get("discount_rate_cap_pct", 13.5))),
    )


def normalized_operating_fcff_rows(
    forecast_rows: list[dict[str, float]],
    history_fin: list[dict[str, Any]],
    config: dict[str, Any],
) -> list[dict[str, float]]:
    settings = config["valuation"].get("operating_value", {})
    historical_anchor = historical_annualized_fcff(history_fin, config)
    history_weight = clamp(float(settings.get("historical_fcff_anchor_weight", 0.30)), 0.0, 0.85)
    if abs(historical_anchor) <= 1e-9:
        history_weight = 0.0
    normalized: list[dict[str, float]] = []
    for row in forecast_rows:
        normalized_fcff = (
            row["annual_fcff"] * (1.0 - history_weight)
            + historical_anchor * history_weight
        )
        normalized.append({**row, "annual_fcff": normalized_fcff})
    return normalized


def market_valuation_adjustments(
    operation: dict[str, Any],
    risk_free_rate_pct: float,
    config: dict[str, Any],
) -> dict[str, float]:
    valuation_config = config["valuation"]
    settings = valuation_config.get("market_valuation", {})
    neutral_rate = float(settings.get("neutral_10y_yield_pct", 3.0))
    rate_adjustment = -(risk_free_rate_pct - neutral_rate) * float(
        settings.get("rate_discount_per_100bp_pct", 4.0)
    )

    hy_baseline = float(settings.get("hy_spread_baseline_bps", valuation_config.get("hy_spread_baseline_bps", 420.0)))
    hy_spread = as_float(operation, "input_hy_spread_bps", hy_baseline)
    credit_widening = max(0.0, hy_spread - hy_baseline) / 100.0
    credit_tightening = max(0.0, hy_baseline - hy_spread) / 100.0
    credit_adjustment = (
        -credit_widening * float(settings.get("credit_discount_per_100bps_pct", 3.0))
        + credit_tightening * float(settings.get("credit_premium_per_100bps_pct", 1.0))
    )

    neutral_equity_pe = float(settings.get("neutral_equity_valuation_pe", 17.0))
    equity_valuation_pe = as_float(operation, "input_equity_valuation_pe", neutral_equity_pe)
    if neutral_equity_pe > 0:
        equity_valuation_gap_pct = (equity_valuation_pe / neutral_equity_pe - 1.0) * 100.0
    else:
        equity_valuation_gap_pct = 0.0
    equity_valuation_adjustment = clamp(
        equity_valuation_gap_pct * float(settings.get("equity_valuation_pe_sensitivity", 0.30)),
        -float(settings.get("equity_valuation_discount_cap_pct", 10.0)),
        float(settings.get("equity_valuation_premium_cap_pct", 9.0)),
    )

    equity_return = as_float(operation, "input_equity_return_pct", 0.0)
    equity_adjustment = clamp(
        (equity_return - float(settings.get("neutral_equity_return_pct", 0.0)))
        * float(settings.get("equity_return_sensitivity", 0.35)),
        -float(settings.get("equity_sentiment_cap_pct", 12.0)),
        float(settings.get("equity_sentiment_cap_pct", 12.0)),
    )

    state = str(operation.get("branch_scenario_state") or "baseline")
    branch_adjustment = 0.0
    if state == "occurred":
        branch_adjustment = -float(settings.get("branch_occurred_discount_pct", 6.0))
    elif state == "watch":
        branch_adjustment = -float(settings.get("branch_watch_discount_pct", 2.0))

    total_adjustment = clamp(
        rate_adjustment + credit_adjustment + equity_valuation_adjustment + equity_adjustment + branch_adjustment,
        -float(settings.get("market_discount_cap_pct", 28.0)),
        float(settings.get("market_premium_cap_pct", 24.0)),
    )
    return {
        "rate": rate_adjustment,
        "credit": credit_adjustment,
        "equity_valuation_pe": equity_valuation_pe,
        "equity_valuation": equity_valuation_adjustment,
        "equity_sentiment": equity_adjustment,
        "branch": branch_adjustment,
        "total": total_adjustment,
        "multiplier": max(0.05, 1.0 + total_adjustment / 100.0),
    }


def forecast_annuals(
    history_ops: list[dict[str, Any]],
    history_fin: list[dict[str, Any]],
    operation: dict[str, Any],
    financial: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    forecast_config = config["forecast"]
    floor_pct = float(forecast_config.get("annual_growth_floor_pct", -8.0))
    cap_pct = float(forecast_config.get("annual_growth_cap_pct", 8.0))
    passenger_growth = trailing_growth_pct(
        history_ops,
        "quarter_served_passengers_million",
        float(forecast_config.get("fallback_annual_passenger_growth_pct", 2.0)),
        floor_pct,
        cap_pct,
    )
    revenue_growth = trailing_growth_pct(
        history_ops,
        "total_operating_revenue_million_cny",
        float(forecast_config.get("fallback_annual_revenue_growth_pct", 2.5)),
        floor_pct,
        cap_pct,
    )
    revenue_growth = clamp(
        0.55 * revenue_growth + 0.45 * passenger_growth + macro_growth_adjustment_pct(operation, config),
        floor_pct,
        cap_pct,
    )

    current_revenue = recent_annual_sum(history_ops, "total_operating_revenue_million_cny")
    current_profit = recent_annual_sum(history_fin, "period_operating_profit_million_cny")
    current_margin = safe_divide(current_profit, current_revenue, 0.0)
    margin_history: list[float] = []
    paired = list(zip(history_ops[-12:], history_fin[-12:]))
    for op_row, fin_row in paired:
        revenue = as_float(op_row, "total_operating_revenue_million_cny")
        if revenue > 0:
            margin_history.append(as_float(fin_row, "period_operating_profit_million_cny") / revenue)
    long_term_margin = mean(margin_history) if margin_history else current_margin
    target_weight = float(forecast_config.get("long_term_margin_weight", 0.55))
    target_margin = clamp(
        current_margin * (1.0 - target_weight) + long_term_margin * target_weight,
        -0.45,
        0.45,
    )

    annual_depreciation = recent_annual_sum(history_fin, "period_accounting_depreciation_million_cny")
    fixed_asset_book = as_float(financial, "fixed_asset_book_value_million_cny")
    maintenance_from_depreciation = annual_depreciation * float(
        forecast_config.get("maintenance_capex_ratio_of_depreciation", 0.75)
    )
    maintenance_from_book = fixed_asset_book * float(
        forecast_config.get("maintenance_capex_ratio_of_fixed_asset_book_value_pct", 0.0)
    ) / 100.0
    maintenance_capex = max(maintenance_from_depreciation, maintenance_from_book)
    maintenance_growth = float(forecast_config.get("maintenance_capex_annual_growth_pct", 1.5)) / 100.0
    tax_rate = float(forecast_config.get("cash_tax_rate_pct", 0.0)) / 100.0

    forecast_rows: list[dict[str, float]] = []
    revenue = current_revenue
    for year_number in range(1, int(forecast_config.get("forecast_horizon_quarters", 20)) // 4 + 1):
        fade = year_number / max(1.0, float(forecast_config.get("forecast_horizon_quarters", 20)) / 4.0)
        annual_growth = revenue_growth * (1.0 - 0.35 * fade)
        revenue *= 1.0 + annual_growth / 100.0
        margin = current_margin * (1.0 - fade) + target_margin * fade
        operating_profit = revenue * margin
        year_maintenance_capex = maintenance_capex * ((1.0 + maintenance_growth) ** (year_number - 1))
        cash_tax = max(0.0, operating_profit - annual_depreciation) * tax_rate
        fcff = operating_profit - year_maintenance_capex - cash_tax
        forecast_rows.append(
            {
                "year": float(year_number),
                "annual_revenue": revenue,
                "annual_operating_profit": operating_profit,
                "annual_maintenance_capex": year_maintenance_capex,
                "annual_fcff": fcff,
            }
        )

    return {
        "passenger_growth_pct": passenger_growth,
        "revenue_growth_pct": revenue_growth,
        "target_margin_pct": target_margin * 100.0,
        "maintenance_capex_year1": forecast_rows[0]["annual_maintenance_capex"] if forecast_rows else 0.0,
        "forecast_rows": forecast_rows,
    }


def terminal_growth_pct(passenger_growth_pct: float, discount_rate_pct: float, config: dict[str, Any]) -> float:
    settings = config["valuation"]
    terminal = float(settings.get("terminal_growth_base_pct", 1.2)) + 0.20 * passenger_growth_pct
    terminal = clamp(
        terminal,
        float(settings.get("terminal_growth_floor_pct", 0.2)),
        float(settings.get("terminal_growth_cap_pct", 2.0)),
    )
    terminal = min(terminal, max(0.0, discount_rate_pct - float(settings.get("terminal_discount_spread_min_pct", 2.8))))
    return terminal


def asset_quality_adjustment(operation: dict[str, Any], financial: dict[str, Any], config: dict[str, Any]) -> tuple[float, float]:
    settings = config["valuation"].get("asset_quality_adjustment", {})
    if not bool(settings.get("enabled", True)):
        return 0.0, 0.0
    book_value = as_float(financial, "fixed_asset_book_value_million_cny")
    if book_value <= 0:
        return 0.0, 0.0
    quality = as_float(operation, "city_airport_perceived_quality_index", 100.0)
    design_utilization = as_float(operation, "quarter_design_utilization_pct", 0.0)
    midpoint = float(settings.get("quality_index_midpoint", 100.0))
    sweet_spot = float(settings.get("capacity_sweet_spot_design_utilization_pct", 92.0))
    overcrowding_start = float(settings.get("overcrowding_penalty_start_pct", 108.0))
    quality_component = (quality - midpoint) / 100.0
    capacity_component = -abs(design_utilization - sweet_spot) / 240.0
    overcrowding_penalty = -max(0.0, design_utilization - overcrowding_start) / 160.0
    ratio = quality_component + capacity_component + overcrowding_penalty
    ratio = clamp(
        ratio,
        -float(settings.get("max_discount_pct_of_book_value", 7.0)) / 100.0,
        float(settings.get("max_premium_pct_of_book_value", 5.0)) / 100.0,
    )
    return book_value * ratio, ratio * 100.0


def contract_quality_adjustment(history_ops: list[dict[str, Any]], config: dict[str, Any]) -> tuple[float, float]:
    settings = config["valuation"].get("contract_quality_adjustment", {})
    if not bool(settings.get("enabled", True)):
        return 0.0, 0.0
    annual_revenue = recent_annual_sum(history_ops, "contract_commercial_revenue_million_cny")
    if annual_revenue <= 0:
        return 0.0, 0.0
    duty_basis = str(history_ops[-1].get("duty_free_contract_revenue_basis") or "")
    luxury_basis = str(history_ops[-1].get("luxury_contract_revenue_basis") or "")
    guarantee_score = 0.04 if "minimum" in duty_basis or "minimum" in luxury_basis else -0.02
    trend = trailing_growth_pct(history_ops, "contract_commercial_revenue_million_cny", 0.0, -20.0, 20.0) / 100.0
    ratio = guarantee_score + 0.25 * trend
    ratio = clamp(
        ratio,
        -float(settings.get("max_discount_pct_of_annual_contract_revenue", 16.0)) / 100.0,
        float(settings.get("max_premium_pct_of_annual_contract_revenue", 22.0)) / 100.0,
    )
    adjustment = annual_revenue * float(settings.get("annual_contract_revenue_multiple", 0.45)) * ratio
    return adjustment, ratio * 100.0


def valuation_for_as_of(
    history_ops: list[dict[str, Any]],
    history_fin: list[dict[str, Any]],
    operation: dict[str, Any],
    financial: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    forecast = forecast_annuals(history_ops, history_fin, operation, financial, config)
    forecast_rows = forecast["forecast_rows"]
    valuation_config = config["valuation"]
    risk_free = clamp(
        as_float(operation, "input_10y_yield_pct", 3.0),
        float(valuation_config.get("risk_free_rate_floor_pct", 1.5)),
        float(valuation_config.get("risk_free_rate_cap_pct", 6.5)),
    )
    premiums = risk_premiums(operation, financial, config)
    base_premium = float(valuation_config.get("base_airport_equity_risk_premium_pct", 3.6))
    operating_discount_rate = operating_discount_rate_pct(premiums, config)
    terminal_growth = terminal_growth_pct(float(forecast["passenger_growth_pct"]), operating_discount_rate, config)
    discount = operating_discount_rate / 100.0
    terminal_growth_rate = terminal_growth / 100.0
    normalized_forecast_rows = normalized_operating_fcff_rows(forecast_rows, history_fin, config)
    pv_operating_forecast = 0.0
    for item in normalized_forecast_rows:
        year_number = int(item["year"])
        pv_operating_forecast += item["annual_fcff"] / ((1.0 + discount) ** year_number)

    terminal_settings = valuation_config.get("operating_value", {})
    terminal_average_years = max(1, int(terminal_settings.get("terminal_fcff_average_years", 5)))
    terminal_fcff_rows = normalized_forecast_rows[-terminal_average_years:]
    normalized_terminal_fcff = mean([item["annual_fcff"] for item in terminal_fcff_rows]) if terminal_fcff_rows else 0.0
    last_fcff = forecast_rows[-1]["annual_fcff"] if forecast_rows else 0.0
    if normalized_terminal_fcff > 0 and discount > terminal_growth_rate:
        terminal_value = normalized_terminal_fcff * (1.0 + terminal_growth_rate) / (discount - terminal_growth_rate)
        terminal_value = min(
            terminal_value,
            normalized_terminal_fcff * float(valuation_config.get("terminal_fcff_multiple_cap", 18.0)),
        )
    else:
        terminal_value = normalized_terminal_fcff * float(valuation_config.get("terminal_negative_fcff_multiple", 4.0))
    pv_terminal = terminal_value / ((1.0 + discount) ** max(1, len(forecast_rows)))

    asset_adjustment, asset_adjustment_ratio = asset_quality_adjustment(operation, financial, config)
    contract_adjustment, contract_adjustment_ratio = contract_quality_adjustment(history_ops, config)
    operating_enterprise_value = pv_operating_forecast + pv_terminal + asset_adjustment + contract_adjustment

    market_adjustments = market_valuation_adjustments(operation, risk_free, config)
    market_enterprise_value = operating_enterprise_value * market_adjustments["multiplier"]
    market_adjustment_million = market_enterprise_value - operating_enterprise_value

    cash = as_float(financial, "period_end_cash_million_cny")
    short_debt = as_float(financial, "short_term_debt_million_cny")
    long_debt = as_float(financial, "long_term_debt_million_cny")
    total_debt = short_debt + long_debt
    recognized_cash = cash * float(valuation_config.get("cash_recognition_rate", 1.0))
    net_debt = total_debt - recognized_cash
    book_equity = as_float(financial, "total_equity_million_cny")
    net_asset_equity_value = book_equity
    net_asset_enterprise_value = net_asset_equity_value + net_debt
    enterprise_value = net_asset_enterprise_value
    equity_value = net_asset_equity_value
    experimental_equity_value = market_enterprise_value - net_debt

    uncertainty = valuation_config.get("uncertainty", {})
    historical_fcff = [
        as_float(row, "period_operating_profit_million_cny") - as_float(row, "period_total_capex_outlay_million_cny")
        for row in history_fin[-8:]
    ]
    range_pct = float(uncertainty.get("base_range_pct", 14.0))
    range_pct += min(8.0, coefficient_of_variation(historical_fcff) * 6.0)
    if len(history_fin) < int(config["forecast"].get("minimum_history_quarters", 4)):
        range_pct += float(uncertainty.get("short_history_add_pct", 4.0))
    if last_fcff < 0:
        range_pct += float(uncertainty.get("negative_fcff_add_pct", 5.0))
    liability_ratio = safe_divide(as_float(financial, "total_liabilities_million_cny"), as_float(financial, "total_assets_million_cny"), 0.0) * 100.0
    if liability_ratio > 60.0:
        range_pct += float(uncertainty.get("high_leverage_add_pct", 7.0)) * min(1.0, (liability_ratio - 60.0) / 20.0)
    if str(operation.get("branch_scenario_state") or "") == "occurred":
        range_pct += float(uncertainty.get("branch_occurred_add_pct", 4.0))
    range_pct = clamp(
        range_pct,
        float(uncertainty.get("range_floor_pct", 10.0)),
        float(uncertainty.get("range_cap_pct", 38.0)),
    )

    conservative_ev = market_enterprise_value * (1.0 - range_pct / 100.0)
    optimistic_ev = market_enterprise_value * (1.0 + range_pct / 100.0)
    experimental_conservative_equity = conservative_ev - net_debt
    experimental_optimistic_equity = optimistic_ev - net_debt
    conservative_equity = equity_value
    optimistic_equity = equity_value

    risk_tags: list[str] = []
    if equity_value < 0:
        risk_tags.append("negative_equity_value")
    if last_fcff < 0:
        risk_tags.append("negative_terminal_fcff")
    if liability_ratio >= 70.0:
        risk_tags.append("high_leverage")
    elif liability_ratio >= 55.0:
        risk_tags.append("elevated_leverage")
    if as_float(operation, "quarter_design_utilization_pct") > 108.0:
        risk_tags.append("capacity_pressure")
    if str(operation.get("branch_scenario_state") or "") == "occurred":
        risk_tags.append("branch_event_active")
    if str(financial.get("loan_active_ids") or ""):
        risk_tags.append("loan_stress_active")
    if market_adjustments["total"] <= -8.0:
        risk_tags.append("market_discount")
    elif market_adjustments["total"] >= 8.0:
        risk_tags.append("market_premium")
    if not risk_tags:
        risk_tags.append("normal")

    current_revenue = recent_annual_sum(history_ops, "total_operating_revenue_million_cny")
    current_profit = recent_annual_sum(history_fin, "period_operating_profit_million_cny")
    current_accounting_profit = recent_annual_sum(history_fin, "period_accounting_profit_million_cny")
    current_contract_revenue = recent_annual_sum(history_ops, "contract_commercial_revenue_million_cny")

    row: dict[str, Any] = {
        "city_airport_valuation_forecast_param_version": CITY_AIRPORT_VALUATION_FORECAST_PARAM_VERSION,
        "city_airport_valuation_forecast_interface_version": CITY_AIRPORT_VALUATION_FORECAST_INTERFACE_VERSION,
        "valuation_config_version": config["config_version"],
        "valuation_scenario_tag": config.get("valuation_scenario_tag", "reported_financial_state"),
        "valuation_primary_method": valuation_config.get("primary_method", "net_asset_value"),
        "operator_id": config["operator_id"],
        "operator_name": config["operator_name"],
        "city_airport_market_id": config["city_airport_market_id"],
        "city_name": config["city_name"],
        "region_id": config["region_id"],
        "region_name": config["region_name"],
        "seed": int(as_float(financial, "seed")),
        "currency": config.get("currency", financial.get("currency", "CNY")),
        "amount_unit": config.get("amount_unit", financial.get("amount_unit", "million_cny")),
        "as_of_year": int(as_float(financial, "year")),
        "as_of_quarter": str(financial.get("quarter", "Q1")),
        "as_of_period_index": period_index(financial),
        "data_cutoff_year": int(as_float(financial, "year")),
        "data_cutoff_quarter": str(financial.get("quarter", "Q1")),
        "game_phase": financial.get("game_phase", ""),
        "player_decision_enabled": int(as_float(financial, "player_decision_enabled")),
        "forecast_horizon_quarters": int(config["forecast"].get("forecast_horizon_quarters", 20)),
        "forecast_horizon_years": int(config["forecast"].get("forecast_horizon_quarters", 20)) / 4.0,
        "history_quarters_used": len(history_fin),
        "branch_scenario_id": financial.get("branch_scenario_id", operation.get("branch_scenario_id", "none")),
        "branch_scenario_state": financial.get("branch_scenario_state", operation.get("branch_scenario_state", "baseline")),
        "annual_served_passengers_million": recent_annual_sum(history_ops, "quarter_served_passengers_million"),
        "current_annual_revenue_million_cny": current_revenue,
        "current_annual_operating_profit_million_cny": current_profit,
        "current_annual_accounting_profit_million_cny": current_accounting_profit,
        "current_annual_commercial_profit_million_cny": recent_annual_sum(history_ops, "commercial_operating_profit_million_cny"),
        "current_annual_contract_revenue_million_cny": current_contract_revenue,
        "current_annual_depreciation_million_cny": recent_annual_sum(history_fin, "period_accounting_depreciation_million_cny"),
        "current_operating_margin_pct": safe_divide(current_profit, current_revenue, 0.0) * 100.0,
        "current_cash_million_cny": cash,
        "current_short_term_debt_million_cny": short_debt,
        "current_long_term_debt_million_cny": long_debt,
        "current_total_debt_million_cny": total_debt,
        "recognized_cash_million_cny": recognized_cash,
        "net_debt_million_cny": net_debt,
        "total_assets_million_cny": as_float(financial, "total_assets_million_cny"),
        "total_liabilities_million_cny": as_float(financial, "total_liabilities_million_cny"),
        "liability_to_asset_ratio_pct": liability_ratio,
        "fixed_asset_book_value_million_cny": as_float(financial, "fixed_asset_book_value_million_cny"),
        "construction_in_progress_million_cny": as_float(financial, "construction_in_progress_million_cny"),
        "city_airport_perceived_quality_index": as_float(operation, "city_airport_perceived_quality_index", 100.0),
        "quarter_design_utilization_pct": as_float(operation, "quarter_design_utilization_pct"),
        "quarter_max_utilization_pct": as_float(operation, "quarter_max_utilization_pct"),
        "forecast_annual_passenger_growth_pct": forecast["passenger_growth_pct"],
        "forecast_annual_revenue_growth_pct": forecast["revenue_growth_pct"],
        "forecast_target_operating_margin_pct": forecast["target_margin_pct"],
        "forecast_maintenance_capex_year1_million_cny": forecast["maintenance_capex_year1"],
        "risk_free_rate_pct": risk_free,
        "base_airport_risk_premium_pct": base_premium,
        "macro_risk_premium_pct": premiums["macro"],
        "leverage_risk_premium_pct": premiums["leverage"],
        "quality_risk_premium_pct": premiums["quality"],
        "crowding_risk_premium_pct": premiums["crowding"],
        "branch_risk_premium_pct": premiums["branch"],
        "input_equity_return_pct": as_float(operation, "input_equity_return_pct"),
        "input_equity_valuation_pe": as_float(operation, "input_equity_valuation_pe", 17.0),
        "operating_discount_rate_pct": operating_discount_rate,
        "operating_terminal_growth_pct": terminal_growth,
        "normalized_terminal_fcff_million_cny": normalized_terminal_fcff,
        "pv_operating_forecast_fcff_million_cny": pv_operating_forecast,
        "operating_terminal_value_million_cny": terminal_value,
        "pv_operating_terminal_value_million_cny": pv_terminal,
        "operating_enterprise_value_million_cny": operating_enterprise_value,
        "market_valuation_multiplier": market_adjustments["multiplier"],
        "market_rate_adjustment_pct": market_adjustments["rate"],
        "market_credit_adjustment_pct": market_adjustments["credit"],
        "market_equity_valuation_pe": market_adjustments["equity_valuation_pe"],
        "market_equity_valuation_adjustment_pct": market_adjustments["equity_valuation"],
        "market_equity_sentiment_adjustment_pct": market_adjustments["equity_sentiment"],
        "market_branch_adjustment_pct": market_adjustments["branch"],
        "market_valuation_adjustment_pct": market_adjustments["total"],
        "market_valuation_adjustment_million_cny": market_adjustment_million,
        "market_enterprise_value_million_cny": market_enterprise_value,
        "market_enterprise_value_conservative_million_cny": conservative_ev,
        "market_enterprise_value_optimistic_million_cny": optimistic_ev,
        "discount_rate_pct": operating_discount_rate,
        "terminal_growth_pct": terminal_growth,
        "pv_forecast_fcff_million_cny": pv_operating_forecast,
        "terminal_value_million_cny": terminal_value,
        "pv_terminal_value_million_cny": pv_terminal,
        "asset_quality_adjustment_million_cny": asset_adjustment,
        "asset_quality_adjustment_ratio_pct": asset_adjustment_ratio,
        "contract_quality_adjustment_million_cny": contract_adjustment,
        "contract_quality_adjustment_ratio_pct": contract_adjustment_ratio,
        "net_asset_equity_value_million_cny": net_asset_equity_value,
        "net_asset_enterprise_value_million_cny": net_asset_enterprise_value,
        "primary_equity_value_million_cny": equity_value,
        "primary_enterprise_value_million_cny": enterprise_value,
        "experimental_operating_enterprise_value_million_cny": operating_enterprise_value,
        "experimental_market_enterprise_value_million_cny": market_enterprise_value,
        "experimental_equity_value_million_cny": experimental_equity_value,
        "experimental_equity_value_conservative_million_cny": experimental_conservative_equity,
        "experimental_equity_value_optimistic_million_cny": experimental_optimistic_equity,
        "enterprise_value_million_cny": enterprise_value,
        "equity_value_million_cny": equity_value,
        "valuation_uncertainty_range_pct": range_pct,
        "equity_value_conservative_million_cny": conservative_equity,
        "equity_value_optimistic_million_cny": optimistic_equity,
        "operating_ev_to_current_operating_profit_multiple": safe_divide(operating_enterprise_value, current_profit, 0.0),
        "market_ev_to_current_operating_profit_multiple": safe_divide(market_enterprise_value, current_profit, 0.0),
        "ev_to_current_operating_profit_multiple": safe_divide(enterprise_value, current_profit, 0.0),
        "price_to_current_operating_profit_multiple": safe_divide(equity_value, current_profit, 0.0),
        "price_to_current_accounting_profit_multiple": safe_divide(equity_value, current_accounting_profit, 0.0),
        "price_to_book_equity_multiple": safe_divide(equity_value, book_equity, 0.0),
        "equity_to_book_equity_multiple": safe_divide(equity_value, book_equity, 0.0),
        "valuation_risk_tags": ";".join(risk_tags),
        "forecast_method_note": "net_asset_primary_with_experimental_operating_market_ev_observation",
    }

    for index, item in enumerate(forecast_rows[:5], start=1):
        row[f"forecast_year_{index}_revenue_million_cny"] = item["annual_revenue"]
        row[f"forecast_year_{index}_operating_profit_million_cny"] = item["annual_operating_profit"]
        row[f"forecast_year_{index}_maintenance_capex_million_cny"] = item["annual_maintenance_capex"]
        row[f"forecast_year_{index}_fcff_million_cny"] = item["annual_fcff"]
    row["forecast_5y_fcff_sum_million_cny"] = sum(item["annual_fcff"] for item in forecast_rows[:5])
    row["operating_5y_normalized_fcff_sum_million_cny"] = sum(item["annual_fcff"] for item in normalized_forecast_rows[:5])
    return round_record(row)


def simulate_valuation_forecast(
    operations_rows: list[dict[str, Any]],
    financial_rows: list[dict[str, Any]],
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    op_by_key = {row_key(row): row for row in operations_rows}
    by_seed_fin: dict[int, list[dict[str, Any]]] = {}
    by_seed_ops: dict[int, list[dict[str, Any]]] = {}
    for row in financial_rows:
        by_seed_fin.setdefault(int(as_float(row, "seed")), []).append(row)
    for row in operations_rows:
        by_seed_ops.setdefault(int(as_float(row, "seed")), []).append(row)

    player_start_year = int(config.get("timeline", {}).get("player_decision_start_year", 2030))
    history_limit = int(config["forecast"].get("history_quarters", 12))
    rows: list[dict[str, Any]] = []
    for seed, seed_fin_rows in sorted(by_seed_fin.items()):
        seed_fin_rows = sorted(seed_fin_rows, key=period_index)
        seed_ops_rows = sorted(by_seed_ops.get(seed, []), key=period_index)
        op_history_by_period = {period_index(row): row for row in seed_ops_rows}
        for idx, financial in enumerate(seed_fin_rows):
            year = int(as_float(financial, "year"))
            if year < player_start_year:
                continue
            operation = op_by_key.get(row_key(financial), op_history_by_period.get(period_index(financial), {}))
            if not operation:
                continue
            history_fin = seed_fin_rows[: idx + 1]
            cutoff = period_index(financial)
            history_ops = [row for row in seed_ops_rows if period_index(row) <= cutoff]
            history_fin_limited = recent_rows(history_fin, history_limit)
            history_ops_limited = recent_rows(history_ops, history_limit)
            rows.append(
                valuation_for_as_of(
                    history_ops_limited,
                    history_fin_limited,
                    operation,
                    financial,
                    config,
                )
            )
    return rows


def summarize(rows: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, Any]:
    if not rows:
        return {
            "city_airport_valuation_forecast_param_version": CITY_AIRPORT_VALUATION_FORECAST_PARAM_VERSION,
            "city_airport_valuation_forecast_interface_version": CITY_AIRPORT_VALUATION_FORECAST_INTERFACE_VERSION,
            "valuation_config_version": config["config_version"],
            "row_count": 0,
        }
    latest = rows[-1]
    selected_years = {2030, 2035, 2050, 2065, 2085}
    selected_rows = [
        row
        for row in rows
        if int(row.get("as_of_year", 0)) in selected_years and str(row.get("as_of_quarter")) == "Q4"
    ]
    return {
        "city_airport_valuation_forecast_param_version": CITY_AIRPORT_VALUATION_FORECAST_PARAM_VERSION,
        "city_airport_valuation_forecast_interface_version": CITY_AIRPORT_VALUATION_FORECAST_INTERFACE_VERSION,
        "valuation_config_version": config["config_version"],
        "operator_id": config["operator_id"],
        "operator_name": config["operator_name"],
        "city_airport_market_id": config["city_airport_market_id"],
        "currency": config["currency"],
        "amount_unit": config["amount_unit"],
        "row_count": len(rows),
        "latest": latest,
        "selected_rows": selected_rows,
        "average_discount_rate_pct": round(mean(as_float(row, "discount_rate_pct") for row in rows), 4),
        "average_primary_enterprise_value_million_cny": round(mean(as_float(row, "primary_enterprise_value_million_cny") for row in rows), 4),
        "average_primary_equity_value_million_cny": round(mean(as_float(row, "primary_equity_value_million_cny") for row in rows), 4),
        "average_net_asset_enterprise_value_million_cny": round(mean(as_float(row, "net_asset_enterprise_value_million_cny") for row in rows), 4),
        "average_net_asset_equity_value_million_cny": round(mean(as_float(row, "net_asset_equity_value_million_cny") for row in rows), 4),
        "average_operating_enterprise_value_million_cny": round(mean(as_float(row, "operating_enterprise_value_million_cny") for row in rows), 4),
        "average_market_enterprise_value_million_cny": round(mean(as_float(row, "market_enterprise_value_million_cny") for row in rows), 4),
        "average_equity_value_million_cny": round(mean(as_float(row, "equity_value_million_cny") for row in rows), 4),
        "average_experimental_equity_value_million_cny": round(mean(as_float(row, "experimental_equity_value_million_cny") for row in rows), 4),
        "average_market_equity_valuation_pe": round(mean(as_float(row, "market_equity_valuation_pe") for row in rows), 4),
        "average_price_to_current_operating_profit_multiple": round(mean(as_float(row, "price_to_current_operating_profit_multiple") for row in rows), 4),
        "average_price_to_book_equity_multiple": round(mean(as_float(row, "price_to_book_equity_multiple") for row in rows), 4),
        "minimum_market_enterprise_value_million_cny": round(min(as_float(row, "market_enterprise_value_million_cny") for row in rows), 4),
        "maximum_market_enterprise_value_million_cny": round(max(as_float(row, "market_enterprise_value_million_cny") for row in rows), 4),
        "minimum_equity_value_million_cny": round(min(as_float(row, "equity_value_million_cny") for row in rows), 4),
        "maximum_equity_value_million_cny": round(max(as_float(row, "equity_value_million_cny") for row in rows), 4),
    }


def write_viewer_data_js(path: Path, rows: list[dict[str, Any]], config: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "param_version": CITY_AIRPORT_VALUATION_FORECAST_PARAM_VERSION,
        "interface_version": CITY_AIRPORT_VALUATION_FORECAST_INTERFACE_VERSION,
        "valuation_config_version": config["config_version"],
        "operator_id": config["operator_id"],
        "operator_name": config["operator_name"],
        "city_airport_market_id": config["city_airport_market_id"],
        "valuation_scenario_tag": config.get("valuation_scenario_tag", "reported_financial_state"),
        "rows": rows,
    }
    path.write_text(
        "window.CITY_AIRPORT_VALUATION_FORECAST_DATA = "
        + json.dumps(payload, ensure_ascii=False)
        + ";\n",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate city airport as-of forecast and FCFF valuation rows."
    )
    parser.add_argument("--market", default="beijing_airport_system")
    parser.add_argument(
        "--quarterly-operations-csv",
        type=Path,
        default=None,
        help="Defaults to airport/output/city_airport_quarterly_operations/china_mainland/<market>_quarterly_operations_seed_sweep.csv.",
    )
    parser.add_argument(
        "--financial-state-csv",
        type=Path,
        default=None,
        help="Defaults to airport/output/city_airport_financial_state/china_mainland/<market>_financial_state_seed_sweep.csv.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_DIR / "beijing_airport_group_valuation_forecast_v1.json",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=AIRPORT_DIR / "output" / "city_airport_valuation",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.quarterly_operations_csv is None:
        args.quarterly_operations_csv = (
            AIRPORT_DIR
            / "output"
            / "city_airport_quarterly_operations"
            / "china_mainland"
            / f"{args.market}_quarterly_operations_seed_sweep.csv"
        )
    if args.financial_state_csv is None:
        args.financial_state_csv = (
            AIRPORT_DIR
            / "output"
            / "city_airport_financial_state"
            / "china_mainland"
            / f"{args.market}_financial_state_seed_sweep.csv"
        )

    config = load_config(args.config)
    operations_rows = read_csv(args.quarterly_operations_csv)
    financial_rows = read_csv(args.financial_state_csv)
    if not operations_rows:
        raise SystemExit(f"No quarterly operations rows found in {args.quarterly_operations_csv}")
    if not financial_rows:
        raise SystemExit(f"No financial state rows found in {args.financial_state_csv}")
    rows = simulate_valuation_forecast(operations_rows, financial_rows, config)

    region_id = str(config.get("region_id") or financial_rows[0].get("region_id") or "unknown_region")
    market_id = str(config["city_airport_market_id"])
    output_dir = args.output_dir / region_id
    csv_path = output_dir / f"{market_id}_valuation_forecast_seed_sweep.csv"
    summary_path = output_dir / f"{market_id}_valuation_forecast_summary.json"
    js_path = output_dir / f"{market_id}_valuation_forecast_viewer_data.js"

    write_csv(csv_path, rows, VALUATION_FORECAST_FIELDS)
    write_json(summary_path, summarize(rows, config))
    write_viewer_data_js(js_path, rows, config)
    print(
        json.dumps(
            {"csv": str(csv_path), "summary": str(summary_path), "viewer": str(js_path)},
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
