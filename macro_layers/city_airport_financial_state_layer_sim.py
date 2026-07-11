from __future__ import annotations

from importlib import import_module

_SIBLING_PREFIX = f"{__package__}." if __package__ else ""
simulation_io = import_module(f"{_SIBLING_PREFIX}simulation_io")
simulation_utils = import_module(f"{_SIBLING_PREFIX}simulation_utils")

read_csv = simulation_io.read_csv_utf8_sig
write_csv = simulation_io.write_csv_utf8_sig_ignore
write_json = simulation_io.write_json_utf8_data
as_float = simulation_utils.as_float_convert_lookup_default
clamp = simulation_utils.clamp

import argparse
import csv
import json
from pathlib import Path
from statistics import mean
from typing import Any


CITY_AIRPORT_FINANCIAL_STATE_PARAM_VERSION = "city-airport-financial-state-layer-v0.6"
CITY_AIRPORT_FINANCIAL_STATE_INTERFACE_VERSION = "city-airport-financial-state-interface-v0.6"

AIRPORT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_DIR = AIRPORT_DIR / "config" / "city_airport_finance"
QUARTERS = ("Q1", "Q2", "Q3", "Q4")

FINANCIAL_STATE_FIELDS = [
    "city_airport_financial_state_param_version",
    "city_airport_financial_state_interface_version",
    "finance_config_version",
    "operator_id",
    "operator_name",
    "city_airport_market_id",
    "city_name",
    "region_id",
    "region_name",
    "year_index",
    "year",
    "quarter",
    "seed",
    "currency",
    "amount_unit",
    "game_phase",
    "player_decision_enabled",
    "player_decision_start_year",
    "startup_operating_history_years",
    "debt_enabled",
    "opening_cash_million_cny",
    "period_begin_cash_million_cny",
    "period_operating_profit_million_cny",
    "period_accounting_depreciation_million_cny",
    "period_interest_expense_million_cny",
    "period_pretax_accounting_profit_million_cny",
    "period_taxable_income_million_cny",
    "period_income_tax_prepayment_million_cny",
    "period_income_tax_settlement_million_cny",
    "period_income_tax_expense_million_cny",
    "period_cash_tax_paid_million_cny",
    "period_effective_tax_rate_pct",
    "period_tax_loss_carryforward_opening_million_cny",
    "period_tax_loss_used_million_cny",
    "period_tax_loss_generated_million_cny",
    "period_tax_loss_expired_million_cny",
    "period_tax_loss_carryforward_ending_million_cny",
    "period_tax_loss_carryforward_detail",
    "period_annual_taxable_income_after_loss_million_cny",
    "period_annual_income_tax_payable_million_cny",
    "period_accounting_profit_million_cny",
    "period_renovation_capex_outlay_million_cny",
    "period_construction_capex_outlay_million_cny",
    "period_rebuild_capex_outlay_million_cny",
    "period_rebuild_demolition_expense_million_cny",
    "period_rebuild_old_initial_asset_writeoff_million_cny",
    "period_rebuild_old_renovation_asset_writeoff_million_cny",
    "period_rebuild_old_rebuild_asset_writeoff_million_cny",
    "period_rebuild_old_asset_writeoff_million_cny",
    "period_total_capex_outlay_million_cny",
    "period_free_cash_flow_before_financing_million_cny",
    "period_loan_drawdown_million_cny",
    "period_interest_payment_million_cny",
    "period_principal_repayment_million_cny",
    "period_debt_service_million_cny",
    "period_financing_cash_flow_million_cny",
    "period_end_cash_million_cny",
    "loan_active_ids",
    "loan_drawdown_ids",
    "loan_principal_repayment_ids",
    "loan_weighted_interest_rate_pct",
    "loan_drawdown_weighted_interest_rate_pct",
    "loan_drawdown_leverage_before_pct",
    "loan_drawdown_leverage_after_pct",
    "loan_drawdown_leverage_spread_bps",
    "loan_blocked_ids",
    "loan_blocked_reasons",
    "initial_fixed_asset_original_million_cny",
    "initial_fixed_asset_residual_floor_million_cny",
    "initial_fixed_asset_accumulated_depreciation_million_cny",
    "initial_fixed_asset_book_value_million_cny",
    "initial_fixed_asset_period_depreciation_million_cny",
    "renovation_asset_original_million_cny",
    "renovation_asset_residual_floor_million_cny",
    "renovation_asset_accumulated_depreciation_million_cny",
    "renovation_asset_book_value_million_cny",
    "renovation_asset_period_depreciation_million_cny",
    "construction_asset_original_million_cny",
    "construction_asset_residual_floor_million_cny",
    "construction_asset_accumulated_depreciation_million_cny",
    "construction_asset_book_value_million_cny",
    "construction_asset_period_depreciation_million_cny",
    "rebuild_asset_original_million_cny",
    "rebuild_asset_residual_floor_million_cny",
    "rebuild_asset_accumulated_depreciation_million_cny",
    "rebuild_asset_book_value_million_cny",
    "rebuild_asset_period_depreciation_million_cny",
    "construction_in_progress_million_cny",
    "fixed_asset_original_million_cny",
    "fixed_asset_residual_floor_million_cny",
    "fixed_asset_accumulated_depreciation_million_cny",
    "fixed_asset_book_value_million_cny",
    "total_noncurrent_assets_million_cny",
    "total_assets_million_cny",
    "short_term_debt_million_cny",
    "long_term_debt_million_cny",
    "total_liabilities_million_cny",
    "contributed_capital_million_cny",
    "retained_earnings_million_cny",
    "total_equity_million_cny",
    "balance_check_million_cny",
    "annual_city_binding_bottleneck",
    "branch_scenario_id",
    "branch_scenario_state",
]


def split_semicolon_values(value: Any) -> list[str]:
    return [part.strip() for part in str(value or "").split(";") if part.strip()]


def tax_loss_total(buckets: list[dict[str, float]]) -> float:
    return sum(max(0.0, float(bucket.get("amount_million_cny", 0.0))) for bucket in buckets)


def format_tax_loss_buckets(buckets: list[dict[str, float]]) -> str:
    parts = []
    for bucket in buckets:
        amount = max(0.0, float(bucket.get("amount_million_cny", 0.0)))
        if amount <= 1e-9:
            continue
        generated = int(bucket.get("generated_year", 0))
        expiry = int(bucket.get("expiry_year", 0))
        parts.append(f"{generated}->{expiry}:{amount:.4f}")
    return ";".join(parts)


def expire_tax_losses(buckets: list[dict[str, float]], year: int) -> float:
    expired = 0.0
    kept: list[dict[str, float]] = []
    for bucket in buckets:
        amount = max(0.0, float(bucket.get("amount_million_cny", 0.0)))
        if amount <= 1e-9:
            continue
        if int(bucket.get("expiry_year", 0)) < year:
            expired += amount
        else:
            kept.append({**bucket, "amount_million_cny": amount})
    buckets[:] = kept
    return expired


def use_tax_losses(buckets: list[dict[str, float]], taxable_income: float) -> float:
    remaining_income = max(0.0, taxable_income)
    used = 0.0
    buckets.sort(key=lambda item: (int(item.get("expiry_year", 0)), int(item.get("generated_year", 0))))
    for bucket in buckets:
        if remaining_income <= 1e-9:
            break
        amount = max(0.0, float(bucket.get("amount_million_cny", 0.0)))
        take = min(amount, remaining_income)
        bucket["amount_million_cny"] = amount - take
        remaining_income -= take
        used += take
    buckets[:] = [bucket for bucket in buckets if float(bucket.get("amount_million_cny", 0.0)) > 1e-9]
    return used


def write_viewer_data_js(path: Path, rows: list[dict[str, Any]], config: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "param_version": CITY_AIRPORT_FINANCIAL_STATE_PARAM_VERSION,
        "interface_version": CITY_AIRPORT_FINANCIAL_STATE_INTERFACE_VERSION,
        "finance_config_version": config["config_version"],
        "operator_id": config["operator_id"],
        "operator_name": config["operator_name"],
        "initial_assets": config.get("initial_assets", []),
        "general_loans": config.get("general_loans", []),
        "rows": rows,
    }
    path.write_text(
        "window.CITY_AIRPORT_FINANCIAL_STATE_DATA = "
        + json.dumps(payload, ensure_ascii=False)
        + ";\n",
        encoding="utf-8",
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
    if raw.get("schema_version") != "city-airport-financial-state-config-v1":
        raise ValueError(f"Unsupported city airport financial state config schema in {path}")
    return raw


def quarter_number(quarter: str) -> int:
    if quarter in QUARTERS:
        return QUARTERS.index(quarter) + 1
    try:
        parsed = int(str(quarter).replace("Q", ""))
    except ValueError:
        parsed = 1
    return int(clamp(float(parsed), 1.0, 4.0))


def quarter_start_fraction(year: int, quarter: str) -> float:
    return float(year) + (quarter_number(quarter) - 1) / 4.0


def quarter_period_index(year: int, quarter: str) -> int:
    return int(year) * 4 + quarter_number(quarter) - 1


def asset_profile(
    assets: list[dict[str, Any]],
    period_start_fraction: float,
    period_end_fraction: float,
) -> dict[str, float]:
    original = 0.0
    residual_floor = 0.0
    accumulated = 0.0
    book_value = 0.0
    period_depreciation = 0.0

    for asset in assets:
        asset_original = float(asset.get("asset_original_million_cny", 0.0))
        useful_life = float(asset.get("useful_life_years", 0.0))
        in_service_year = asset.get("in_service_year")
        if asset_original <= 0 or useful_life <= 0 or in_service_year is None:
            continue
        service_start = float(in_service_year)
        if period_end_fraction <= service_start:
            continue
        residual = asset_original * float(asset.get("residual_value_pct", 0.0)) / 100.0
        annual_depreciation = (asset_original - residual) / useful_life
        elapsed_start = clamp(period_start_fraction - service_start, 0.0, useful_life)
        elapsed_end = clamp(period_end_fraction - service_start, 0.0, useful_life)
        accumulated_start = annual_depreciation * elapsed_start
        accumulated_end = annual_depreciation * elapsed_end

        original += asset_original
        residual_floor += residual
        accumulated += accumulated_end
        period_depreciation += max(0.0, accumulated_end - accumulated_start)
        book_value += max(asset_original - accumulated_end, residual)

    return {
        "original": original,
        "residual_floor": residual_floor,
        "accumulated_depreciation": accumulated,
        "book_value": book_value,
        "period_depreciation": period_depreciation,
    }


def opening_asset_profile(config: dict[str, Any]) -> dict[str, float]:
    timeline = config.get("game_timeline", {})
    start_year = int(timeline.get("simulation_start_year", 2025))
    start_fraction = float(start_year)
    return asset_profile(config.get("initial_assets", []), start_fraction, start_fraction)


def loan_start_index(loan: dict[str, Any]) -> int:
    return quarter_period_index(int(loan.get("start_year", 0)), str(loan.get("start_quarter", "Q1")))


def loan_interest_rate_pct(
    loan: dict[str, Any],
    operation: dict[str, Any],
    debt_policy: dict[str, Any],
    leverage_spread_bps: float = 0.0,
) -> float:
    if loan.get("annual_interest_rate_pct") not in (None, ""):
        return max(0.0, float(loan["annual_interest_rate_pct"]))

    model = debt_policy.get("loan_rate_model", {})
    loan_type = str(loan.get("loan_type", "long_term"))
    fallback = float(
        model.get(
            f"fallback_{loan_type}_rate_pct",
            model.get("fallback_annual_interest_rate_pct", 4.8),
        )
    )
    ten_year = as_float(operation, "input_10y_yield_pct", fallback)
    if ten_year <= 0:
        ten_year = fallback
    reference_adjustment = float(model.get(f"{loan_type}_reference_adjustment_pct", 0.0))
    type_spread_bps = float(model.get(f"{loan_type}_spread_bps", 0.0))
    hy_baseline = float(model.get("hy_spread_baseline_bps", 420.0))
    hy_capture = float(model.get("hy_spread_capture_ratio", 0.10))
    hy_spread = as_float(operation, "input_hy_spread_bps", hy_baseline)
    credit_stress_spread_bps = max(0.0, hy_spread - hy_baseline) * hy_capture
    city_spread_bps = float(loan.get("city_risk_spread_bps", model.get("city_risk_spread_bps", 0.0)))
    rate = (
        ten_year
        + reference_adjustment
        + type_spread_bps / 100.0
        + credit_stress_spread_bps / 100.0
        + city_spread_bps / 100.0
        + leverage_spread_bps / 100.0
        + float(loan.get("term_spread_bps", 0.0)) / 100.0
    )
    return clamp(
        rate,
        float(model.get("min_annual_interest_rate_pct", 0.5)),
        float(model.get("max_annual_interest_rate_pct", 12.0)),
    )


def liability_ratio_pct(total_liabilities: float, total_assets: float) -> float:
    if total_assets <= 0:
        return 0.0
    return max(0.0, total_liabilities / total_assets * 100.0)


def loan_leverage_model(debt_policy: dict[str, Any]) -> dict[str, Any]:
    return debt_policy.get("loan_rate_model", {}).get("leverage_spread_model", {})


def loan_leverage_spread_bps(debt_policy: dict[str, Any], leverage_pct: float) -> float:
    model = loan_leverage_model(debt_policy)
    if not bool(model.get("enabled", False)):
        return 0.0
    curve = sorted(
        [
            (
                float(point.get("liability_ratio_pct", 0.0)),
                float(point.get("additional_spread_bps", 0.0)),
            )
            for point in model.get("spread_curve", [])
        ],
        key=lambda item: item[0],
    )
    if curve:
        if leverage_pct <= curve[0][0]:
            return curve[0][1]
        for (left_ratio, left_spread), (right_ratio, right_spread) in zip(curve, curve[1:]):
            if leverage_pct <= right_ratio:
                ratio_span = right_ratio - left_ratio
                if ratio_span <= 0:
                    return right_spread
                progress = (leverage_pct - left_ratio) / ratio_span
                return left_spread + (right_spread - left_spread) * progress
        return curve[-1][1]

    tiers = list(model.get("tiers", []))
    for tier in tiers:
        max_pct = float(tier.get("max_liability_ratio_pct", 100.0))
        if leverage_pct < max_pct:
            return float(tier.get("additional_spread_bps", 0.0))
    if tiers:
        return float(tiers[-1].get("additional_spread_bps", 0.0))
    return 0.0


def loan_block_reason(
    debt_policy: dict[str, Any],
    before_leverage_pct: float,
    after_leverage_pct: float,
) -> str:
    model = loan_leverage_model(debt_policy)
    if not bool(model.get("enabled", False)):
        return ""
    before_limit = float(model.get("block_if_begin_ratio_at_or_above_pct", 80.0))
    after_limit = float(model.get("block_if_post_draw_ratio_at_or_above_pct", 80.0))
    if before_leverage_pct >= before_limit:
        return f"begin_leverage_at_or_above_{before_limit:g}%"
    if after_leverage_pct >= after_limit:
        return f"post_draw_leverage_at_or_above_{after_limit:g}%"
    return ""


def process_general_loans(
    loan_states: dict[str, dict[str, Any]],
    loans: list[dict[str, Any]],
    operation: dict[str, Any],
    debt_policy: dict[str, Any],
    year: int,
    quarter: str,
    opening_total_assets: float,
    opening_total_liabilities: float,
) -> dict[str, Any]:
    period = quarter_period_index(year, quarter)
    drawdown = 0.0
    interest = 0.0
    principal_repayment = 0.0
    drawdown_leverage_before = 0.0
    drawdown_leverage_after = 0.0
    drawdown_leverage_spread_numerator = 0.0
    drawdown_leverage_spread_denominator = 0.0
    drawdown_rate_numerator = 0.0
    drawdown_rate_denominator = 0.0
    weighted_rate_numerator = 0.0
    weighted_rate_denominator = 0.0
    active_ids: list[str] = []
    drawdown_ids: list[str] = []
    repayment_ids: list[str] = []
    blocked_ids: list[str] = []
    blocked_reasons: list[str] = []
    working_assets = max(0.0, opening_total_assets)
    working_liabilities = max(0.0, opening_total_liabilities)

    for loan in loans:
        loan_id = str(loan.get("loan_id", ""))
        if not loan_id or not bool(loan.get("enabled", True)):
            continue
        principal = max(0.0, float(loan.get("principal_million_cny", 0.0)))
        tenor = max(1, int(loan.get("tenor_quarters", 1)))
        start = loan_start_index(loan)
        end = start + tenor
        state = loan_states.setdefault(
            loan_id,
            {
                "balance": 0.0,
                "drawn": False,
                "annual_interest_rate_pct": None,
                "loan_type": str(loan.get("loan_type", "long_term")),
            },
        )

        if period == start and not state["drawn"] and principal > 0:
            before_leverage = liability_ratio_pct(working_liabilities, working_assets)
            after_leverage = liability_ratio_pct(working_liabilities + principal, working_assets + principal)
            leverage_spread_bps = loan_leverage_spread_bps(debt_policy, after_leverage)
            block_reason = loan_block_reason(debt_policy, before_leverage, after_leverage)
            drawdown_leverage_before = max(drawdown_leverage_before, before_leverage)
            drawdown_leverage_after = max(drawdown_leverage_after, after_leverage)
            if block_reason:
                state["blocked"] = True
                blocked_ids.append(loan_id)
                blocked_reasons.append(f"{loan_id}:{block_reason}")
                continue
            annual_interest_rate = loan_interest_rate_pct(
                loan,
                operation,
                debt_policy,
                leverage_spread_bps,
            )
            state["balance"] = float(state.get("balance", 0.0)) + principal
            state["drawn"] = True
            state["annual_interest_rate_pct"] = annual_interest_rate
            state["loan_type"] = str(loan.get("loan_type", "long_term"))
            drawdown += principal
            drawdown_ids.append(loan_id)
            drawdown_leverage_spread_numerator += principal * leverage_spread_bps
            drawdown_leverage_spread_denominator += principal
            drawdown_rate_numerator += principal * annual_interest_rate
            drawdown_rate_denominator += principal
            working_assets += principal
            working_liabilities += principal

        balance = float(state.get("balance", 0.0))
        if period < start or period >= end or balance <= 0:
            continue

        active_ids.append(loan_id)
        rate = float(state.get("annual_interest_rate_pct") or loan_interest_rate_pct(loan, operation, debt_policy))
        period_interest = balance * rate / 100.0 / 4.0
        interest += period_interest
        weighted_rate_numerator += balance * rate
        weighted_rate_denominator += balance

        elapsed = period - start
        repayment_style = str(loan.get("repayment_style", "equal_principal"))
        if repayment_style == "bullet_principal":
            period_principal = balance if elapsed == tenor - 1 else 0.0
        elif repayment_style == "grace_then_equal_principal":
            grace = int(clamp(float(loan.get("grace_period_quarters", 0)), 0.0, float(max(0, tenor - 1))))
            repayment_periods = max(1, tenor - grace)
            period_principal = 0.0 if elapsed < grace else principal / repayment_periods
            if elapsed == tenor - 1:
                period_principal = balance
        else:
            period_principal = principal / tenor
            if elapsed == tenor - 1:
                period_principal = balance

        period_principal = min(balance, max(0.0, period_principal))
        if period_principal > 0:
            principal_repayment += period_principal
            repayment_ids.append(loan_id)
            state["balance"] = balance - period_principal

    short_debt = 0.0
    long_debt = 0.0
    for state in loan_states.values():
        balance = max(0.0, float(state.get("balance", 0.0)))
        if str(state.get("loan_type", "long_term")) == "short_term":
            short_debt += balance
        else:
            long_debt += balance

    return {
        "drawdown": drawdown,
        "interest": interest,
        "principal_repayment": principal_repayment,
        "debt_service": interest + principal_repayment,
        "financing_cash_flow": drawdown - principal_repayment,
        "short_debt": short_debt,
        "long_debt": long_debt,
        "active_ids": ";".join(active_ids),
        "drawdown_ids": ";".join(drawdown_ids),
        "repayment_ids": ";".join(repayment_ids),
        "weighted_interest_rate_pct": (
            weighted_rate_numerator / weighted_rate_denominator if weighted_rate_denominator > 0 else 0.0
        ),
        "drawdown_weighted_interest_rate_pct": (
            drawdown_rate_numerator / drawdown_rate_denominator if drawdown_rate_denominator > 0 else 0.0
        ),
        "drawdown_leverage_before_pct": drawdown_leverage_before,
        "drawdown_leverage_after_pct": drawdown_leverage_after,
        "drawdown_leverage_spread_bps": (
            drawdown_leverage_spread_numerator / drawdown_leverage_spread_denominator
            if drawdown_leverage_spread_denominator > 0
            else 0.0
        ),
        "blocked_ids": ";".join(blocked_ids),
        "blocked_reasons": ";".join(blocked_reasons),
    }


def simulate_financial_state(
    operation_rows: list[dict[str, str]],
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    timeline = config.get("game_timeline", {})
    opening = config.get("opening_balance", {})
    debt_policy = config.get("debt_policy", {})
    debt_enabled = int(bool(debt_policy.get("debt_enabled", False)))
    general_loans = list(config.get("general_loans", []))
    opening_cash = float(opening.get("opening_cash_million_cny", 0.0))
    opening_short_debt = float(opening.get("opening_short_term_debt_million_cny", 0.0))
    opening_long_debt = float(opening.get("opening_long_term_debt_million_cny", 0.0))
    opening_debt = opening_short_debt + opening_long_debt
    opening_assets = opening_asset_profile(config)
    contributed_capital = float(
        opening.get(
            "opening_contributed_capital_million_cny",
            opening_cash + opening_assets["book_value"] - opening_debt,
        )
    )

    rows: list[dict[str, Any]] = []
    state_by_seed: dict[int, dict[str, Any]] = {}
    sorted_rows = sorted(
        operation_rows,
        key=lambda row: (
            int(as_float(row, "seed")),
            int(as_float(row, "year")),
            quarter_number(str(row.get("quarter", "Q1"))),
        ),
    )

    for operation in sorted_rows:
        seed = int(as_float(operation, "seed"))
        state = state_by_seed.setdefault(
            seed,
            {
                "cash": opening_cash,
                "retained_earnings": float(opening.get("opening_retained_earnings_million_cny", 0.0)),
                "auto_long_term_debt": 0.0,
                "loan_states": {},
                "last_total_assets": opening_cash + opening_assets["book_value"],
                "last_total_liabilities": opening_debt,
                "disposed_initial_asset_ids": set(),
                "tax_loss_carryforwards": [],
                "tax_year": None,
                "tax_year_pretax_profit": 0.0,
                "tax_year_prepayment": 0.0,
            },
        )
        year = int(as_float(operation, "year"))
        quarter = str(operation.get("quarter", "Q1"))
        start_fraction = quarter_start_fraction(year, quarter)
        end_fraction = start_fraction + 0.25
        disposed_initial_asset_ids = state["disposed_initial_asset_ids"]
        initial_asset_rows = list(config.get("initial_assets", []))
        active_initial_asset_rows = [
            asset
            for asset in initial_asset_rows
            if str(asset.get("asset_id", "")) not in disposed_initial_asset_ids
        ]
        rebuild_started_slot_ids = set(split_semicolon_values(operation.get("rebuild_started_slot_ids", "")))
        initial_assets_to_writeoff = [
            asset
            for asset in active_initial_asset_rows
            if str(asset.get("slot_id", "")) in rebuild_started_slot_ids
        ]
        initial_asset_writeoff = asset_profile(
            initial_assets_to_writeoff,
            start_fraction,
            start_fraction,
        )["book_value"]
        for asset in initial_assets_to_writeoff:
            asset_id = str(asset.get("asset_id", ""))
            if asset_id:
                disposed_initial_asset_ids.add(asset_id)
        active_initial_asset_rows = [
            asset
            for asset in initial_asset_rows
            if str(asset.get("asset_id", "")) not in disposed_initial_asset_ids
        ]
        initial_assets = asset_profile(active_initial_asset_rows, start_fraction, end_fraction)

        operating_profit = as_float(operation, "quarter_operating_profit_million_cny")
        renovation_capex = as_float(operation, "renovation_quarter_capex_outlay_million_cny")
        construction_capex = as_float(operation, "construction_quarter_capex_outlay_million_cny")
        rebuild_capex = as_float(operation, "rebuild_quarter_capex_outlay_million_cny")
        rebuild_demolition_expense = as_float(operation, "rebuild_quarter_demolition_expense_million_cny")
        rebuild_renovation_writeoff = as_float(
            operation,
            "rebuild_old_renovation_asset_writeoff_million_cny",
        )
        rebuild_rebuild_writeoff = as_float(
            operation,
            "rebuild_old_rebuild_asset_writeoff_million_cny",
        )
        rebuild_old_asset_writeoff = initial_asset_writeoff + rebuild_renovation_writeoff + rebuild_rebuild_writeoff
        total_capex = renovation_capex + construction_capex + rebuild_capex
        renovation_depreciation = as_float(operation, "renovation_asset_period_depreciation_million_cny")
        construction_depreciation = as_float(operation, "construction_asset_period_depreciation_million_cny")
        rebuild_depreciation = as_float(operation, "rebuild_asset_period_depreciation_million_cny")
        accounting_depreciation = (
            initial_assets["period_depreciation"]
            + renovation_depreciation
            + construction_depreciation
            + rebuild_depreciation
        )
        begin_cash = state["cash"]
        loan_activity = process_general_loans(
            state["loan_states"],
            general_loans if debt_enabled else [],
            operation,
            debt_policy,
            year,
            quarter,
            float(state.get("last_total_assets", opening_cash + opening_assets["book_value"])),
            float(state.get("last_total_liabilities", opening_debt)),
        )
        interest_expense = float(loan_activity["interest"])
        pretax_accounting_profit = (
            operating_profit
            - accounting_depreciation
            - rebuild_demolition_expense
            - rebuild_old_asset_writeoff
            - interest_expense
        )
        tax_policy = config.get("tax_policy", {})
        income_tax_rate_pct = float(tax_policy.get("corporate_income_tax_rate_pct", 25.0))
        loss_carryforward_enabled = bool(tax_policy.get("loss_carryforward_enabled", True))
        loss_carryforward_years = int(tax_policy.get("loss_carryforward_years", 5))
        prepayment_ratio = float(tax_policy.get("quarterly_prepayment_ratio", 1.0))
        annual_settlement_quarter = str(tax_policy.get("annual_settlement_quarter", "Q4"))
        tax_loss_buckets = state["tax_loss_carryforwards"]
        tax_loss_expired = 0.0
        if state.get("tax_year") != year:
            state["tax_year"] = year
            state["tax_year_pretax_profit"] = 0.0
            state["tax_year_prepayment"] = 0.0
            if loss_carryforward_enabled:
                tax_loss_expired = expire_tax_losses(tax_loss_buckets, year)

        tax_loss_opening = tax_loss_total(tax_loss_buckets)
        taxable_income = max(0.0, pretax_accounting_profit)
        income_tax_prepayment = taxable_income * income_tax_rate_pct / 100.0 * prepayment_ratio
        state["tax_year_pretax_profit"] += pretax_accounting_profit
        state["tax_year_prepayment"] += income_tax_prepayment

        tax_loss_used = 0.0
        tax_loss_generated = 0.0
        income_tax_settlement = 0.0
        annual_taxable_income_after_loss = 0.0
        annual_income_tax_payable = 0.0
        if quarter == annual_settlement_quarter:
            annual_pretax_profit = float(state["tax_year_pretax_profit"])
            annual_prepayment = float(state["tax_year_prepayment"])
            if annual_pretax_profit > 0:
                if loss_carryforward_enabled:
                    tax_loss_used = use_tax_losses(tax_loss_buckets, annual_pretax_profit)
                annual_taxable_income_after_loss = max(0.0, annual_pretax_profit - tax_loss_used)
                annual_income_tax_payable = annual_taxable_income_after_loss * income_tax_rate_pct / 100.0
            elif annual_pretax_profit < 0 and loss_carryforward_enabled:
                tax_loss_generated = -annual_pretax_profit
                tax_loss_buckets.append(
                    {
                        "generated_year": float(year),
                        "expiry_year": float(year + loss_carryforward_years),
                        "amount_million_cny": tax_loss_generated,
                    }
                )
            income_tax_settlement = annual_income_tax_payable - annual_prepayment

        income_tax_expense = income_tax_prepayment + income_tax_settlement
        cash_tax_paid = income_tax_expense
        accounting_profit = pretax_accounting_profit - income_tax_expense
        effective_tax_rate_pct = (
            income_tax_expense / pretax_accounting_profit * 100.0
            if pretax_accounting_profit > 0
            else 0.0
        )
        tax_loss_ending = tax_loss_total(tax_loss_buckets)
        tax_loss_detail = format_tax_loss_buckets(tax_loss_buckets)
        free_cash_flow = operating_profit - total_capex - rebuild_demolition_expense - cash_tax_paid

        loan_drawdown = float(loan_activity["drawdown"])
        principal_repayment = float(loan_activity["principal_repayment"])
        interest_payment = float(loan_activity["interest"])
        debt_service = float(loan_activity["debt_service"])
        financing_cash_flow = float(loan_activity["financing_cash_flow"])
        end_cash = begin_cash + free_cash_flow + financing_cash_flow - interest_payment
        if debt_enabled and bool(debt_policy.get("auto_borrow_on_negative_cash", False)) and end_cash < 0:
            auto_borrowing = -end_cash
            financing_cash_flow += auto_borrowing
            state["auto_long_term_debt"] += auto_borrowing
            end_cash = 0.0

        state["cash"] = end_cash
        state["retained_earnings"] += accounting_profit

        renovation_original = as_float(operation, "renovation_asset_original_million_cny")
        renovation_residual = as_float(operation, "renovation_asset_residual_floor_million_cny")
        renovation_accumulated = as_float(operation, "renovation_asset_accumulated_depreciation_million_cny")
        renovation_book = as_float(operation, "renovation_asset_book_value_million_cny")
        construction_original = as_float(operation, "construction_asset_original_million_cny")
        construction_residual = as_float(operation, "construction_asset_residual_floor_million_cny")
        construction_accumulated = as_float(operation, "construction_asset_accumulated_depreciation_million_cny")
        construction_book = as_float(operation, "construction_asset_book_value_million_cny")
        rebuild_original = as_float(operation, "rebuild_asset_original_million_cny")
        rebuild_residual = as_float(operation, "rebuild_asset_residual_floor_million_cny")
        rebuild_accumulated = as_float(operation, "rebuild_asset_accumulated_depreciation_million_cny")
        rebuild_book = as_float(operation, "rebuild_asset_book_value_million_cny")
        construction_in_progress = (
            as_float(operation, "renovation_construction_in_progress_million_cny")
            + as_float(operation, "construction_in_progress_million_cny")
            + as_float(operation, "rebuild_construction_in_progress_million_cny")
        )

        fixed_original = initial_assets["original"] + renovation_original + construction_original + rebuild_original
        fixed_residual = initial_assets["residual_floor"] + renovation_residual + construction_residual + rebuild_residual
        fixed_accumulated = (
            initial_assets["accumulated_depreciation"]
            + renovation_accumulated
            + construction_accumulated
            + rebuild_accumulated
        )
        fixed_book = initial_assets["book_value"] + renovation_book + construction_book + rebuild_book
        total_noncurrent_assets = fixed_book + construction_in_progress
        total_assets = end_cash + total_noncurrent_assets
        short_term_debt = opening_short_debt + float(loan_activity["short_debt"])
        long_term_debt = opening_long_debt + state["auto_long_term_debt"] + float(loan_activity["long_debt"])
        total_liabilities = short_term_debt + long_term_debt
        total_equity = contributed_capital + state["retained_earnings"]
        balance_check = total_assets - total_liabilities - total_equity
        state["last_total_assets"] = total_assets
        state["last_total_liabilities"] = total_liabilities

        rows.append(
            round_record(
                {
                    "city_airport_financial_state_param_version": CITY_AIRPORT_FINANCIAL_STATE_PARAM_VERSION,
                    "city_airport_financial_state_interface_version": CITY_AIRPORT_FINANCIAL_STATE_INTERFACE_VERSION,
                    "finance_config_version": config["config_version"],
                    "operator_id": config["operator_id"],
                    "operator_name": config["operator_name"],
                    "city_airport_market_id": config["city_airport_market_id"],
                    "city_name": config["city_name"],
                    "region_id": operation.get("region_id", config.get("region_id", "")),
                    "region_name": operation.get("region_name", config.get("region_name", "")),
                    "year_index": int(as_float(operation, "year_index")),
                    "year": year,
                    "quarter": quarter,
                    "seed": seed,
                    "currency": config["currency"],
                    "amount_unit": config["amount_unit"],
                    "game_phase": operation.get("game_phase", ""),
                    "player_decision_enabled": int(as_float(operation, "player_decision_enabled")),
                    "player_decision_start_year": int(
                        as_float(operation, "player_decision_start_year", timeline.get("player_decision_start_year", 2030))
                    ),
                    "startup_operating_history_years": int(
                        as_float(
                            operation,
                            "startup_operating_history_years",
                            timeline.get("startup_operating_history_years", 5),
                        )
                    ),
                    "debt_enabled": debt_enabled,
                    "opening_cash_million_cny": opening_cash,
                    "period_begin_cash_million_cny": begin_cash,
                    "period_operating_profit_million_cny": operating_profit,
                    "period_accounting_depreciation_million_cny": accounting_depreciation,
                    "period_interest_expense_million_cny": interest_expense,
                    "period_pretax_accounting_profit_million_cny": pretax_accounting_profit,
                    "period_taxable_income_million_cny": taxable_income,
                    "period_income_tax_prepayment_million_cny": income_tax_prepayment,
                    "period_income_tax_settlement_million_cny": income_tax_settlement,
                    "period_income_tax_expense_million_cny": income_tax_expense,
                    "period_cash_tax_paid_million_cny": cash_tax_paid,
                    "period_effective_tax_rate_pct": effective_tax_rate_pct,
                    "period_tax_loss_carryforward_opening_million_cny": tax_loss_opening,
                    "period_tax_loss_used_million_cny": tax_loss_used,
                    "period_tax_loss_generated_million_cny": tax_loss_generated,
                    "period_tax_loss_expired_million_cny": tax_loss_expired,
                    "period_tax_loss_carryforward_ending_million_cny": tax_loss_ending,
                    "period_tax_loss_carryforward_detail": tax_loss_detail,
                    "period_annual_taxable_income_after_loss_million_cny": annual_taxable_income_after_loss,
                    "period_annual_income_tax_payable_million_cny": annual_income_tax_payable,
                    "period_accounting_profit_million_cny": accounting_profit,
                    "period_renovation_capex_outlay_million_cny": renovation_capex,
                    "period_construction_capex_outlay_million_cny": construction_capex,
                    "period_rebuild_capex_outlay_million_cny": rebuild_capex,
                    "period_rebuild_demolition_expense_million_cny": rebuild_demolition_expense,
                    "period_rebuild_old_initial_asset_writeoff_million_cny": initial_asset_writeoff,
                    "period_rebuild_old_renovation_asset_writeoff_million_cny": (
                        rebuild_renovation_writeoff
                    ),
                    "period_rebuild_old_rebuild_asset_writeoff_million_cny": rebuild_rebuild_writeoff,
                    "period_rebuild_old_asset_writeoff_million_cny": rebuild_old_asset_writeoff,
                    "period_total_capex_outlay_million_cny": total_capex,
                    "period_free_cash_flow_before_financing_million_cny": free_cash_flow,
                    "period_loan_drawdown_million_cny": loan_drawdown,
                    "period_interest_payment_million_cny": interest_payment,
                    "period_principal_repayment_million_cny": principal_repayment,
                    "period_debt_service_million_cny": debt_service,
                    "period_financing_cash_flow_million_cny": financing_cash_flow,
                    "period_end_cash_million_cny": end_cash,
                    "loan_active_ids": loan_activity["active_ids"],
                    "loan_drawdown_ids": loan_activity["drawdown_ids"],
                    "loan_principal_repayment_ids": loan_activity["repayment_ids"],
                    "loan_weighted_interest_rate_pct": loan_activity["weighted_interest_rate_pct"],
                    "loan_drawdown_weighted_interest_rate_pct": loan_activity[
                        "drawdown_weighted_interest_rate_pct"
                    ],
                    "loan_drawdown_leverage_before_pct": loan_activity["drawdown_leverage_before_pct"],
                    "loan_drawdown_leverage_after_pct": loan_activity["drawdown_leverage_after_pct"],
                    "loan_drawdown_leverage_spread_bps": loan_activity["drawdown_leverage_spread_bps"],
                    "loan_blocked_ids": loan_activity["blocked_ids"],
                    "loan_blocked_reasons": loan_activity["blocked_reasons"],
                    "initial_fixed_asset_original_million_cny": initial_assets["original"],
                    "initial_fixed_asset_residual_floor_million_cny": initial_assets["residual_floor"],
                    "initial_fixed_asset_accumulated_depreciation_million_cny": (
                        initial_assets["accumulated_depreciation"]
                    ),
                    "initial_fixed_asset_book_value_million_cny": initial_assets["book_value"],
                    "initial_fixed_asset_period_depreciation_million_cny": (
                        initial_assets["period_depreciation"]
                    ),
                    "renovation_asset_original_million_cny": renovation_original,
                    "renovation_asset_residual_floor_million_cny": renovation_residual,
                    "renovation_asset_accumulated_depreciation_million_cny": renovation_accumulated,
                    "renovation_asset_book_value_million_cny": renovation_book,
                    "renovation_asset_period_depreciation_million_cny": renovation_depreciation,
                    "construction_asset_original_million_cny": construction_original,
                    "construction_asset_residual_floor_million_cny": construction_residual,
                    "construction_asset_accumulated_depreciation_million_cny": construction_accumulated,
                    "construction_asset_book_value_million_cny": construction_book,
                    "construction_asset_period_depreciation_million_cny": construction_depreciation,
                    "rebuild_asset_original_million_cny": rebuild_original,
                    "rebuild_asset_residual_floor_million_cny": rebuild_residual,
                    "rebuild_asset_accumulated_depreciation_million_cny": rebuild_accumulated,
                    "rebuild_asset_book_value_million_cny": rebuild_book,
                    "rebuild_asset_period_depreciation_million_cny": rebuild_depreciation,
                    "construction_in_progress_million_cny": construction_in_progress,
                    "fixed_asset_original_million_cny": fixed_original,
                    "fixed_asset_residual_floor_million_cny": fixed_residual,
                    "fixed_asset_accumulated_depreciation_million_cny": fixed_accumulated,
                    "fixed_asset_book_value_million_cny": fixed_book,
                    "total_noncurrent_assets_million_cny": total_noncurrent_assets,
                    "total_assets_million_cny": total_assets,
                    "short_term_debt_million_cny": short_term_debt,
                    "long_term_debt_million_cny": long_term_debt,
                    "total_liabilities_million_cny": total_liabilities,
                    "contributed_capital_million_cny": contributed_capital,
                    "retained_earnings_million_cny": state["retained_earnings"],
                    "total_equity_million_cny": total_equity,
                    "balance_check_million_cny": balance_check,
                    "annual_city_binding_bottleneck": operation.get("annual_city_binding_bottleneck", ""),
                    "branch_scenario_id": operation.get("branch_scenario_id", "none"),
                    "branch_scenario_state": operation.get("branch_scenario_state", "baseline"),
                }
            )
        )

    return rows


def summarize(rows: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, Any]:
    grouped: dict[tuple[int, int], list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault((int(row["seed"]), int(row["year"])), []).append(row)

    annual_summaries: list[dict[str, Any]] = []
    for (seed, year), items in sorted(grouped.items()):
        items = sorted(items, key=lambda row: quarter_number(str(row["quarter"])))
        first = items[0]
        latest = items[-1]
        annual_operating_profit = sum(as_float(item, "period_operating_profit_million_cny") for item in items)
        annual_depreciation = sum(as_float(item, "period_accounting_depreciation_million_cny") for item in items)
        annual_interest = sum(as_float(item, "period_interest_expense_million_cny") for item in items)
        annual_pretax_accounting_profit = sum(
            as_float(item, "period_pretax_accounting_profit_million_cny") for item in items
        )
        annual_taxable_income = sum(as_float(item, "period_taxable_income_million_cny") for item in items)
        annual_taxable_income_after_loss = sum(
            as_float(item, "period_annual_taxable_income_after_loss_million_cny") for item in items
        )
        annual_tax_loss_used = sum(as_float(item, "period_tax_loss_used_million_cny") for item in items)
        annual_tax_loss_generated = sum(as_float(item, "period_tax_loss_generated_million_cny") for item in items)
        annual_tax_loss_expired = sum(as_float(item, "period_tax_loss_expired_million_cny") for item in items)
        annual_income_tax_prepayment = sum(as_float(item, "period_income_tax_prepayment_million_cny") for item in items)
        annual_income_tax_settlement = sum(as_float(item, "period_income_tax_settlement_million_cny") for item in items)
        annual_income_tax = sum(as_float(item, "period_income_tax_expense_million_cny") for item in items)
        annual_cash_tax_paid = sum(as_float(item, "period_cash_tax_paid_million_cny") for item in items)
        annual_accounting_profit = sum(as_float(item, "period_accounting_profit_million_cny") for item in items)
        annual_capex = sum(as_float(item, "period_total_capex_outlay_million_cny") for item in items)
        annual_rebuild_capex = sum(as_float(item, "period_rebuild_capex_outlay_million_cny") for item in items)
        annual_rebuild_demolition_expense = sum(
            as_float(item, "period_rebuild_demolition_expense_million_cny") for item in items
        )
        annual_rebuild_writeoff = sum(as_float(item, "period_rebuild_old_asset_writeoff_million_cny") for item in items)
        annual_free_cash_flow = sum(
            as_float(item, "period_free_cash_flow_before_financing_million_cny") for item in items
        )
        annual_loan_drawdown = sum(as_float(item, "period_loan_drawdown_million_cny") for item in items)
        annual_principal_repayment = sum(
            as_float(item, "period_principal_repayment_million_cny") for item in items
        )
        annual_debt_service = sum(as_float(item, "period_debt_service_million_cny") for item in items)
        drawdown_spread_weight = sum(
            as_float(item, "period_loan_drawdown_million_cny")
            * as_float(item, "loan_drawdown_leverage_spread_bps")
            for item in items
        )
        drawdown_rate_weight = sum(
            as_float(item, "period_loan_drawdown_million_cny")
            * as_float(item, "loan_drawdown_weighted_interest_rate_pct")
            for item in items
        )
        drawdown_before = max(as_float(item, "loan_drawdown_leverage_before_pct") for item in items)
        drawdown_after = max(as_float(item, "loan_drawdown_leverage_after_pct") for item in items)
        annual_blocked_ids = ";".join(
            split_semicolon_values(";".join(str(item.get("loan_blocked_ids", "")) for item in items))
        )
        annual_summaries.append(
            round_record(
                {
                    "seed": seed,
                    "year": year,
                    "period_begin_cash_million_cny": as_float(first, "period_begin_cash_million_cny"),
                    "period_end_cash_million_cny": as_float(latest, "period_end_cash_million_cny"),
                    "annual_operating_profit_million_cny": annual_operating_profit,
                    "annual_accounting_depreciation_million_cny": annual_depreciation,
                    "annual_interest_expense_million_cny": annual_interest,
                    "annual_pretax_accounting_profit_million_cny": annual_pretax_accounting_profit,
                    "annual_taxable_income_million_cny": annual_taxable_income,
                    "annual_taxable_income_after_loss_million_cny": annual_taxable_income_after_loss,
                    "annual_tax_loss_used_million_cny": annual_tax_loss_used,
                    "annual_tax_loss_generated_million_cny": annual_tax_loss_generated,
                    "annual_tax_loss_expired_million_cny": annual_tax_loss_expired,
                    "annual_tax_loss_carryforward_ending_million_cny": as_float(
                        latest, "period_tax_loss_carryforward_ending_million_cny"
                    ),
                    "annual_income_tax_prepayment_million_cny": annual_income_tax_prepayment,
                    "annual_income_tax_settlement_million_cny": annual_income_tax_settlement,
                    "annual_cash_tax_paid_million_cny": annual_cash_tax_paid,
                    "annual_income_tax_expense_million_cny": annual_income_tax,
                    "annual_effective_tax_rate_pct": (
                        annual_income_tax / annual_pretax_accounting_profit * 100.0
                        if annual_pretax_accounting_profit > 0
                        else 0.0
                    ),
                    "annual_accounting_profit_million_cny": annual_accounting_profit,
                    "annual_capex_outlay_million_cny": annual_capex,
                    "annual_rebuild_capex_outlay_million_cny": annual_rebuild_capex,
                    "annual_rebuild_demolition_expense_million_cny": annual_rebuild_demolition_expense,
                    "annual_rebuild_old_asset_writeoff_million_cny": annual_rebuild_writeoff,
                    "annual_free_cash_flow_before_financing_million_cny": annual_free_cash_flow,
                    "annual_loan_drawdown_million_cny": annual_loan_drawdown,
                    "annual_principal_repayment_million_cny": annual_principal_repayment,
                    "annual_debt_service_million_cny": annual_debt_service,
                    "annual_loan_drawdown_leverage_before_pct": drawdown_before,
                    "annual_loan_drawdown_leverage_after_pct": drawdown_after,
                    "annual_loan_drawdown_weighted_interest_rate_pct": (
                        drawdown_rate_weight / annual_loan_drawdown if annual_loan_drawdown > 0 else 0.0
                    ),
                    "annual_loan_drawdown_leverage_spread_bps": (
                        drawdown_spread_weight / annual_loan_drawdown if annual_loan_drawdown > 0 else 0.0
                    ),
                    "annual_loan_blocked_ids": annual_blocked_ids,
                    "fixed_asset_book_value_million_cny": as_float(latest, "fixed_asset_book_value_million_cny"),
                    "construction_in_progress_million_cny": as_float(latest, "construction_in_progress_million_cny"),
                    "total_assets_million_cny": as_float(latest, "total_assets_million_cny"),
                    "total_liabilities_million_cny": as_float(latest, "total_liabilities_million_cny"),
                    "retained_earnings_million_cny": as_float(latest, "retained_earnings_million_cny"),
                    "total_equity_million_cny": as_float(latest, "total_equity_million_cny"),
                    "balance_check_million_cny": as_float(latest, "balance_check_million_cny"),
                    "game_phase": latest.get("game_phase", ""),
                }
            )
        )

    selected_years = {2025, 2030, 2031, 2035, 2050, 2085}
    selected = [item for item in annual_summaries if int(item["year"]) in selected_years]
    return {
        "city_airport_financial_state_param_version": CITY_AIRPORT_FINANCIAL_STATE_PARAM_VERSION,
        "city_airport_financial_state_interface_version": CITY_AIRPORT_FINANCIAL_STATE_INTERFACE_VERSION,
        "finance_config_version": config["config_version"],
        "operator_id": config["operator_id"],
        "operator_name": config["operator_name"],
        "city_airport_market_id": config["city_airport_market_id"],
        "currency": config["currency"],
        "amount_unit": config["amount_unit"],
        "row_count": len(rows),
        "annual_summary_count": len(annual_summaries),
        "selected_annual_summaries": selected,
        "latest_annual_summary": annual_summaries[-1] if annual_summaries else {},
        "average_balance_check_million_cny": round(
            mean(abs(as_float(item, "balance_check_million_cny")) for item in annual_summaries),
            6,
        )
        if annual_summaries
        else 0.0,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate city airport operator financial state rows from quarterly operations."
    )
    parser.add_argument("--market", default="beijing_airport_system")
    parser.add_argument(
        "--quarterly-operations-csv",
        type=Path,
        default=None,
        help="Defaults to airport/output/city_airport_quarterly_operations/china_mainland/<market>_quarterly_operations_seed_sweep.csv.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_DIR / "beijing_airport_group_financial_state_v1.json",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=AIRPORT_DIR / "output" / "city_airport_financial_state",
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

    config = load_config(args.config)
    operation_rows = read_csv(args.quarterly_operations_csv)
    if not operation_rows:
        raise SystemExit(f"No quarterly operations rows found in {args.quarterly_operations_csv}")
    rows = simulate_financial_state(operation_rows, config)

    region_id = str(operation_rows[0].get("region_id") or config.get("region_id", "unknown_region"))
    market_id = str(config["city_airport_market_id"])
    output_dir = args.output_dir / region_id
    csv_path = output_dir / f"{market_id}_financial_state_seed_sweep.csv"
    summary_path = output_dir / f"{market_id}_financial_state_summary.json"
    js_path = output_dir / f"{market_id}_financial_state_viewer_data.js"

    write_csv(csv_path, rows, FINANCIAL_STATE_FIELDS)
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
