from __future__ import annotations

import math
from importlib import import_module
from typing import Any, Mapping, Sequence


_SIBLING_PREFIX = f"{__package__}." if __package__ else ""
accounting = import_module(f"{_SIBLING_PREFIX}asset_accounting_v04")


REGIONAL_WEALTH_BRIDGE_V04_PARAM_VERSION = "regional-wealth-bridge-v0.4"

REGION_HOLDING_TEMPLATE: Mapping[str, str] = {
    "north_america": "market_based",
    "china_mainland": "bank_centered",
    "west_north_europe": "balanced",
    "japan_korea": "bank_centered",
    "southeast_asia": "balanced",
    "south_asia_india": "bank_centered",
    "hk_macao_taiwan": "market_based",
    "middle_east_gulf": "balanced",
    "oceania": "market_based",
    "south_east_europe_mediterranean": "bank_centered",
    "central_asia_turkey_eurasia": "bank_centered",
    "north_africa": "bank_centered",
    "latin_america_caribbean": "balanced",
    "sub_saharan_africa": "bank_centered",
}

REGIONAL_WEALTH_BRIDGE_FIELDS = (
    "regional_wealth_bridge_v04_param_version",
    "regional_household_holding_template_id",
    "regional_household_equity_weight",
    "regional_household_sovereign_bond_weight",
    "regional_household_cash_weight",
    "regional_household_cash_nominal_return_pct",
    "regional_household_cash_dividend_signal_pct",
    "regional_asset_market_impulse_index",
    "regional_household_financial_wealth_index",
    "regional_real_household_wealth_growth_pct",
    "regional_household_wealth_consumption_impulse",
    "regional_real_disposable_income_growth_pct",
)


def _number(row: Mapping[str, Any], field: str) -> float:
    try:
        value = float(row[field])
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(f"missing or invalid wealth bridge field: {field}") from error
    if not math.isfinite(value):
        raise ValueError(f"wealth bridge field must be finite: {field}")
    return value


def _template_for_region(region_id: str) -> accounting.HoldingTemplate:
    try:
        template_id = REGION_HOLDING_TEMPLATE[region_id]
        return accounting.HOLDING_TEMPLATES[template_id]
    except KeyError as error:
        raise ValueError(f"no household holding template for region: {region_id}") from error


def _market_impulse(
    row: Mapping[str, Any],
    previous: Mapping[str, Any] | None,
) -> float:
    if previous is None:
        return 50.0
    price_return = _number(row, "regional_equity_price_return_pct")
    pe = _number(row, "regional_equity_valuation_pe")
    previous_pe = _number(previous, "regional_equity_valuation_pe")
    pe_change_pct = (pe / previous_pe - 1.0) * 100.0
    risk_change = _number(row, "regional_risk_appetite_index") - _number(
        previous, "regional_risk_appetite_index"
    )
    return max(
        0.0,
        min(100.0, 50.0 + 0.55 * price_return + 0.35 * pe_change_pct + 0.08 * risk_change),
    )


def simulate_regional_wealth_bridge_v04(
    records: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Publish distinct market, household-wealth and cash-income signals.

    The bridge consumes the A2 price/dividend/bond accounting exactly once. It does
    not read legacy regional equity, bond or absolute wealth-effect fields.
    """

    if not records:
        return []
    region_id = str(records[0].get("region_id") or "")
    template = _template_for_region(region_id)
    wealth_index = 100.0
    previous_impulse = 0.0
    output: list[dict[str, Any]] = []

    for position, source in enumerate(records):
        row = dict(source)
        if str(row.get("region_id") or "") != region_id:
            raise ValueError("wealth bridge records must contain one region")
        year_index = int(_number(row, "year_index"))
        if year_index != position:
            raise ValueError("wealth bridge requires contiguous year_index values starting at 0")

        previous = output[-1] if output else None
        if position == 0:
            real_wealth_growth = 0.0
            impulse = 0.0
            cash_return = 0.0
            cash_dividend = 0.0
            disposable_income_growth = 0.0
        else:
            cash_return = max(-1.0, _number(row, "regional_policy_rate_pct") - 0.75)
            cash_dividend = accounting.household_cash_dividend_signal_pct(
                template=template,
                equity_dividend_yield_pct=_number(
                    row, "regional_equity_dividend_yield_pct"
                ),
            )
            real_wealth_growth = accounting.household_real_financial_wealth_growth_pct(
                template=template,
                equity_price_return_pct=_number(
                    row, "regional_equity_price_return_pct"
                ),
                equity_dividend_yield_pct=_number(
                    row, "regional_equity_dividend_yield_pct"
                ),
                sovereign_bond_total_return_pct=_number(
                    row, "regional_sovereign_bond_total_return_pct"
                ),
                cash_nominal_return_pct=cash_return,
                inflation_pct=_number(row, "regional_headline_inflation_pct"),
            )
            wealth_index *= 1.0 + real_wealth_growth / 100.0
            impulse = accounting.wealth_consumption_impulse(
                current_real_wealth_growth_pct=real_wealth_growth,
                previous_impulse=previous_impulse,
            )
            disposable_income_growth = _number(row, "real_income_growth_pct") + cash_dividend

        candidate = {
            "regional_wealth_bridge_v04_param_version": (
                REGIONAL_WEALTH_BRIDGE_V04_PARAM_VERSION
            ),
            "regional_household_holding_template_id": template.template_id,
            "regional_household_equity_weight": template.equity_weight,
            "regional_household_sovereign_bond_weight": (
                template.sovereign_bond_weight
            ),
            "regional_household_cash_weight": template.cash_weight,
            "regional_household_cash_nominal_return_pct": cash_return,
            "regional_household_cash_dividend_signal_pct": cash_dividend,
            "regional_asset_market_impulse_index": _market_impulse(row, previous),
            "regional_household_financial_wealth_index": wealth_index,
            "regional_real_household_wealth_growth_pct": real_wealth_growth,
            "regional_household_wealth_consumption_impulse": impulse,
            "regional_real_disposable_income_growth_pct": disposable_income_growth,
        }
        for field, value in candidate.items():
            if isinstance(value, (int, float)) and not math.isfinite(float(value)):
                raise ValueError(f"wealth bridge candidate field must be finite: {field}")
        output.append({**row, **candidate})
        previous_impulse = impulse

    return output
