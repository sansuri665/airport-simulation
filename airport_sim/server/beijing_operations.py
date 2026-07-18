from __future__ import annotations

from contextlib import AbstractContextManager
from pathlib import Path
from typing import Any, Callable


COMPONENTS = ("business", "leisure", "vfr", "long_haul", "transfer")


def update_simulation_city_row(
    row: dict[str, str],
    *,
    as_float: Callable[[Any, float], float],
    active_facility_slots: str,
    design_capacity: float,
    max_capacity: float,
) -> dict[str, Any]:
    updated: dict[str, Any] = dict(row)
    potential = as_float(row.get("city_potential_passengers_million"), 0.0)
    airline_supply = as_float(
        row.get("city_airline_supply_passengers_million"),
        potential,
    )
    serviceable_demand = min(potential, airline_supply)
    served = min(serviceable_demand, max_capacity)
    allocation_ratio = (
        min(100.0, max_capacity / airline_supply * 100.0)
        if airline_supply > 0
        else 100.0
    )
    capacity_fulfillment = (
        served / serviceable_demand * 100.0
        if serviceable_demand > 0
        else 100.0
    )
    total_fulfillment = served / potential * 100.0 if potential > 0 else 100.0
    design_utilization = (
        served / design_capacity * 100.0 if design_capacity > 0 else 0.0
    )
    max_utilization = served / max_capacity * 100.0 if max_capacity > 0 else 0.0
    airline_supply_gap = max(0.0, potential - airline_supply)
    airport_capacity_gap = max(0.0, serviceable_demand - max_capacity)
    if airport_capacity_gap > 0.0:
        bottleneck = "airport_capacity_limited"
    elif airline_supply < potential:
        bottleneck = "airline_supply_limited"
    else:
        bottleneck = "demand_limited"

    updated.update(
        {
            "active_airport_facility_slots": active_facility_slots,
            "city_airport_design_capacity_million": round(design_capacity, 4),
            "city_airport_max_capacity_million": round(max_capacity, 4),
            "city_effective_capacity_million": round(max_capacity, 4),
            "airport_capacity_allocation_ratio_pct": round(allocation_ratio, 4),
            "airport_capacity_limited_airline_supply_million": round(
                max(0.0, airline_supply - max_capacity),
                4,
            ),
            "city_effective_service_capacity_million": round(
                min(airline_supply, max_capacity),
                4,
            ),
            "city_capacity_utilization_pct": round(max_utilization, 4),
            "city_airport_design_utilization_pct": round(design_utilization, 4),
            "city_airport_max_utilization_pct": round(max_utilization, 4),
            "city_capacity_fulfillment_pct": round(capacity_fulfillment, 4),
            "city_airport_throughput_utilization_pct": round(max_utilization, 4),
            "city_airport_crowding_index": round(
                max(0.0, design_utilization - 100.0),
                4,
            ),
            "city_total_fulfillment_pct": round(total_fulfillment, 4),
            "final_passenger_service_ratio_pct": round(total_fulfillment, 4),
            "city_served_passengers_million": round(served, 4),
            "city_unmet_passengers_million": round(
                max(0.0, potential - served),
                4,
            ),
            "city_unmet_demand_share_pct": round(
                100.0 - total_fulfillment,
                4,
            ),
            "city_airline_supply_gap_million": round(airline_supply_gap, 4),
            "city_airport_capacity_gap_million": round(airport_capacity_gap, 4),
            "city_binding_bottleneck": bottleneck,
            "city_capacity_regime": "initial_capacity_frozen",
            "airport_event_hint": "simulation_default_no_player_projects",
        }
    )

    component_scale = served / potential if potential > 0 else 0.0
    for component in COMPONENTS:
        component_potential = as_float(
            row.get(f"{component}_passengers_million"),
            0.0,
        )
        component_supply = as_float(
            row.get(f"{component}_airline_supply_passengers_million"),
            0.0,
        )
        updated[f"{component}_served_passengers_million"] = round(
            component_potential * component_scale,
            4,
        )
        updated[f"{component}_airline_supply_gap_million"] = round(
            max(0.0, component_potential - component_supply),
            4,
        )
        updated[f"{component}_airline_supply_fulfillment_pct"] = round(
            component_supply / component_potential * 100.0
            if component_potential > 0
            else 100.0,
            4,
        )
    return updated


def write_default_simulation_city_demand_csv(
    run_dir: Path,
    *,
    source_relative_csv: Path,
    target_relative_csv: Path,
    read_csv: Callable[[Path], list[dict[str, str]]],
    write_csv: Callable[[Path, list[dict[str, Any]], list[str]], None],
    update_row: Callable[[dict[str, str]], dict[str, Any]],
) -> Path:
    source_path = run_dir / source_relative_csv
    target_path = run_dir / target_relative_csv
    if not source_path.exists():
        raise FileNotFoundError(
            f"no Beijing city demand output found in {source_path}"
        )
    rows = read_csv(source_path)
    if not rows:
        raise FileNotFoundError(
            f"no Beijing city demand rows found in {source_path}"
        )
    fieldnames = list(rows[0].keys())
    write_csv(target_path, [update_row(row) for row in rows], fieldnames)
    return target_path


def non_empty_ids(*values: str) -> list[str]:
    ids: list[str] = []
    for value in values:
        for item in (
            str(value or "")
            .replace("|", ";")
            .replace(",", ";")
            .split(";")
        ):
            clean = item.strip()
            if clean and clean not in ids:
                ids.append(clean)
    return ids


def quarter_key(
    row: dict[str, str],
    *,
    as_float: Callable[[Any, float], float],
    as_text: Callable[[dict[str, str], str], str],
) -> tuple[int, str]:
    return int(as_float(row.get("year"), 0.0)), as_text(row, "quarter")


def quarter_warnings(
    ops: dict[str, str],
    finance: dict[str, str],
    *,
    rounded: Callable[[dict[str, str], str, int], float],
    as_text: Callable[[dict[str, str], str], str],
) -> list[str]:
    warnings: list[str] = []
    if rounded(ops, "quarter_design_utilization_pct", 2) >= 100.0:
        warnings.append("超过设计容量")
    if rounded(ops, "quarter_max_utilization_pct", 2) >= 95.0:
        warnings.append("接近极限容量")
    if rounded(ops, "quarter_crowding_index", 2) > 0.0:
        warnings.append("拥挤成本生效")
    if rounded(finance, "period_end_cash_million_cny", 2) < 0.0:
        warnings.append("现金为负")
    if as_text(finance, "loan_blocked_ids"):
        warnings.append("贷款被拒")
    if as_text(ops, "renovation_active_event_ids"):
        warnings.append("翻新施工")
    if as_text(ops, "construction_active_event_ids"):
        warnings.append("新建施工")
    if as_text(ops, "rebuild_active_event_ids"):
        warnings.append("重建施工")
    return warnings


def summarize_beijing_quarter(
    index: int,
    ops: dict[str, str],
    finance: dict[str, str],
    *,
    as_float: Callable[[Any, float], float],
    as_bool: Callable[[Any], bool],
    as_text: Callable[[dict[str, str], str], str],
    rounded: Callable[[dict[str, str], str, int], float],
    non_empty_ids: Callable[..., list[str]],
    quarter_warnings: Callable[[dict[str, str], dict[str, str]], list[str]],
) -> dict[str, Any]:
    year = int(as_float(ops.get("year")))
    quarter = as_text(ops, "quarter")
    total_assets = rounded(finance, "total_assets_million_cny")
    total_liabilities = rounded(finance, "total_liabilities_million_cny")
    begin_cash = rounded(finance, "period_begin_cash_million_cny")
    end_cash = rounded(finance, "period_end_cash_million_cny")
    liability_ratio_pct = (total_liabilities / total_assets * 100.0) if total_assets > 0 else 0.0
    capex = (
        rounded(finance, "period_total_capex_outlay_million_cny")
        or rounded(ops, "renovation_quarter_capex_outlay_million_cny")
        + rounded(ops, "construction_quarter_capex_outlay_million_cny")
        + rounded(ops, "rebuild_quarter_capex_outlay_million_cny")
    )
    operating_profit = rounded(ops, "quarter_operating_profit_million_cny")
    cash_tax_paid = rounded(finance, "period_cash_tax_paid_million_cny")
    rebuild_demolition_expense = rounded(
        finance,
        "period_rebuild_demolition_expense_million_cny",
    )
    operating_cash_flow = round(operating_profit - cash_tax_paid, 4)
    investing_cash_flow = round(-capex - rebuild_demolition_expense, 4)
    cash_net_change = round(end_cash - begin_cash, 4)
    return {
        "index": index,
        "year": year,
        "quarter": quarter,
        "label": f"{year} {quarter}",
        "gamePhase": as_text(ops, "game_phase"),
        "playerDecisionEnabled": as_bool(ops.get("player_decision_enabled")),
        "demand": {
            "annualPotential": rounded(ops, "annual_city_potential_passengers_million"),
            "annualAirlineSupply": rounded(ops, "annual_city_airline_supply_passengers_million"),
            "annualServed": rounded(ops, "annual_served_passengers_million"),
            "quarterPotential": rounded(ops, "quarter_city_potential_passengers_million"),
            "quarterAirlineSupply": rounded(ops, "quarter_airline_supply_passengers_million"),
            "quarterServiceableDemand": rounded(ops, "quarter_serviceable_demand_million"),
            "quarterServed": rounded(ops, "quarter_served_passengers_million"),
            "capacityLost": rounded(ops, "quarter_capacity_lost_passengers_million"),
            "airlineSupplyGap": rounded(ops, "quarter_airline_supply_gap_million"),
            "bindingBottleneck": as_text(ops, "annual_city_binding_bottleneck"),
            "componentServed": {
                "business": rounded(ops, "business_quarter_served_passengers_million"),
                "leisure": rounded(ops, "leisure_quarter_served_passengers_million"),
                "vfr": rounded(ops, "vfr_quarter_served_passengers_million"),
                "longHaul": rounded(ops, "long_haul_quarter_served_passengers_million"),
                "transfer": rounded(ops, "transfer_quarter_served_passengers_million"),
            },
        },
        "capacity": {
            "cityDesignCapacity": rounded(ops, "city_airport_design_capacity_million"),
            "cityMaxCapacity": rounded(ops, "city_airport_max_capacity_million"),
            "quarterDesignCapacity": rounded(ops, "quarter_design_capacity_million"),
            "quarterMaxCapacity": rounded(ops, "quarter_max_capacity_million"),
            "designUtilizationPct": rounded(ops, "quarter_design_utilization_pct"),
            "maxUtilizationPct": rounded(ops, "quarter_max_utilization_pct"),
            "capacityRealizationPct": rounded(ops, "quarter_capacity_realization_factor_pct"),
            "crowdingIndex": rounded(ops, "quarter_crowding_index"),
            "perceivedQualityIndex": rounded(ops, "city_airport_perceived_quality_index"),
            "perceivedQualitySizeScore": rounded(ops, "perceived_quality_size_score"),
            "perceivedQualityAgeScore": rounded(ops, "perceived_quality_age_score"),
            "perceivedQualityCapacityScore": rounded(ops, "perceived_quality_capacity_score"),
            "perceivedQualityConstructionDisruptionScore": rounded(
                ops,
                "perceived_quality_construction_disruption_score",
            ),
            "activeFacilitySlots": as_text(ops, "active_facility_slots"),
            "effectiveFacilitySlots": as_text(ops, "effective_facility_slots"),
        },
        "operations": {
            "aeronauticalRevenue": rounded(ops, "aeronautical_revenue_million_cny"),
            "foodRetailRevenue": rounded(ops, "food_retail_revenue_million_cny"),
            "foodRetailFixedCost": rounded(ops, "food_retail_fixed_operating_cost_million_cny"),
            "foodRetailPassengerServiceCost": rounded(
                ops,
                "food_retail_passenger_service_cost_million_cny",
            ),
            "foodRetailSalesCost": rounded(ops, "food_retail_sales_cost_million_cny"),
            "foodRetailCost": rounded(ops, "food_retail_operating_cost_million_cny"),
            "foodRetailProfit": rounded(ops, "food_retail_operating_profit_million_cny"),
            "foodRetailQualityMultiplier": rounded(ops, "food_retail_perceived_quality_revenue_multiplier"),
            "dutyFreeRevenue": rounded(ops, "duty_free_revenue_million_cny"),
            "luxuryRevenue": rounded(ops, "luxury_retail_revenue_million_cny"),
            "commercialRevenue": rounded(ops, "commercial_revenue_million_cny"),
            "commercialDirectCost": rounded(ops, "commercial_direct_cost_million_cny"),
            "commercialProfit": rounded(ops, "commercial_operating_profit_million_cny"),
            "dutyFreeSales": rounded(ops, "duty_free_sales_million_cny"),
            "dutyFreeWeightedPassengers": rounded(ops, "duty_free_weighted_passengers_million"),
            "dutyFreeMarketCycleMultiplier": rounded(ops, "duty_free_market_cycle_multiplier"),
            "dutyFreeQualityMultiplier": rounded(ops, "duty_free_perceived_quality_sales_multiplier"),
            "dutyFreeMinimumGuarantee": rounded(ops, "duty_free_contract_minimum_guarantee_million_cny"),
            "dutyFreeShareRevenue": rounded(ops, "duty_free_contract_share_revenue_million_cny"),
            "dutyFreeRevenueSharePct": rounded(ops, "duty_free_revenue_share_pct"),
            "dutyFreeMinimumGuaranteeCoveragePct": rounded(ops, "duty_free_minimum_guarantee_coverage_pct"),
            "dutyFreeRevenueBasis": as_text(ops, "duty_free_contract_revenue_basis"),
            "dutyFreeContractType": as_text(ops, "duty_free_contract_type"),
            "dutyFreeContractStatus": as_text(ops, "duty_free_contract_status"),
            "dutyFreeContractCycle": as_text(ops, "duty_free_contract_cycle_id"),
            "dutyFreeContractCycleStartYear": rounded(ops, "duty_free_contract_cycle_start_year"),
            "dutyFreeContractCycleEndYear": rounded(ops, "duty_free_contract_cycle_end_year"),
            "dutyFreeContractForecastQuarterSales": rounded(
                ops,
                "duty_free_contract_forecast_quarter_sales_million_cny",
            ),
            "dutyFreeContractForecastAnnualSales": rounded(
                ops,
                "duty_free_contract_forecast_annual_sales_million_cny",
            ),
            "dutyFreeContractHistoryYearsUsed": rounded(ops, "duty_free_contract_history_years_used"),
            "dutyFreeContractTrendMultiplier": rounded(ops, "duty_free_contract_trend_multiplier"),
            "dutyFreeContractMacroRiskDiscountMultiplier": rounded(
                ops,
                "duty_free_contract_macro_risk_discount_multiplier",
            ),
            "dutyFreeContractBargainingPowerMultiplier": rounded(
                ops,
                "duty_free_contract_bargaining_power_multiplier",
            ),
            "luxurySales": rounded(ops, "luxury_sales_million_cny"),
            "luxuryWeightedPassengers": rounded(ops, "luxury_weighted_passengers_million"),
            "luxuryMarketCycleMultiplier": rounded(ops, "luxury_market_cycle_multiplier"),
            "luxuryQualityMultiplier": rounded(ops, "luxury_perceived_quality_sales_multiplier"),
            "luxuryMinimumGuarantee": rounded(ops, "luxury_contract_minimum_guarantee_million_cny"),
            "luxuryShareRevenue": rounded(ops, "luxury_contract_share_revenue_million_cny"),
            "luxuryRevenueSharePct": rounded(ops, "luxury_revenue_share_pct"),
            "luxuryMinimumGuaranteeCoveragePct": rounded(ops, "luxury_minimum_guarantee_coverage_pct"),
            "luxuryRevenueBasis": as_text(ops, "luxury_contract_revenue_basis"),
            "luxuryContractType": as_text(ops, "luxury_contract_type"),
            "luxuryContractStatus": as_text(ops, "luxury_contract_status"),
            "luxuryContractCycle": as_text(ops, "luxury_contract_cycle_id"),
            "luxuryContractCycleStartYear": rounded(ops, "luxury_contract_cycle_start_year"),
            "luxuryContractCycleEndYear": rounded(ops, "luxury_contract_cycle_end_year"),
            "luxuryContractForecastQuarterSales": rounded(
                ops,
                "luxury_contract_forecast_quarter_sales_million_cny",
            ),
            "luxuryContractForecastAnnualSales": rounded(
                ops,
                "luxury_contract_forecast_annual_sales_million_cny",
            ),
            "luxuryContractHistoryYearsUsed": rounded(ops, "luxury_contract_history_years_used"),
            "luxuryContractTrendMultiplier": rounded(ops, "luxury_contract_trend_multiplier"),
            "luxuryContractMacroRiskDiscountMultiplier": rounded(
                ops,
                "luxury_contract_macro_risk_discount_multiplier",
            ),
            "luxuryContractBargainingPowerMultiplier": rounded(
                ops,
                "luxury_contract_bargaining_power_multiplier",
            ),
            "totalRevenue": rounded(ops, "total_operating_revenue_million_cny"),
            "totalCost": rounded(ops, "total_operating_cost_million_cny"),
            "operatingProfit": operating_profit,
            "operatingMarginPct": rounded(ops, "operating_margin_pct"),
            "slotFixedCost": rounded(ops, "quarter_slot_fixed_operating_cost_million_cny"),
            "passengerVariableCost": rounded(ops, "quarter_passenger_variable_cost_million_cny"),
            "congestionCost": rounded(ops, "quarter_congestion_cost_million_cny"),
            "revenuePerPassengerCny": rounded(ops, "total_revenue_per_passenger_cny"),
            "costPerPassengerCny": rounded(ops, "total_cost_per_passenger_cny"),
        },
        "finance": {
            "beginCash": begin_cash,
            "endCash": end_cash,
            "totalAssets": total_assets,
            "totalLiabilities": total_liabilities,
            "accountingDepreciation": rounded(finance, "period_accounting_depreciation_million_cny"),
            "interestExpense": rounded(finance, "period_interest_expense_million_cny"),
            "pretaxProfit": rounded(finance, "period_pretax_accounting_profit_million_cny"),
            "incomeTaxExpense": rounded(finance, "period_income_tax_expense_million_cny"),
            "cashTaxPaid": cash_tax_paid,
            "accountingProfit": rounded(finance, "period_accounting_profit_million_cny"),
            "operatingCashFlow": operating_cash_flow,
            "investingCashFlow": investing_cash_flow,
            "freeCashFlowBeforeFinancing": rounded(finance, "period_free_cash_flow_before_financing_million_cny"),
            "loanDrawdown": rounded(finance, "period_loan_drawdown_million_cny"),
            "principalRepayment": rounded(finance, "period_principal_repayment_million_cny"),
            "debtService": rounded(finance, "period_debt_service_million_cny"),
            "financingCashFlow": rounded(finance, "period_financing_cash_flow_million_cny"),
            "cashNetChange": cash_net_change,
            "capexOutlay": round(capex, 4),
            "rebuildDemolitionExpense": rebuild_demolition_expense,
            "rebuildOldAssetWriteoff": rounded(
                finance,
                "period_rebuild_old_asset_writeoff_million_cny",
            ),
            "constructionInProgress": rounded(finance, "construction_in_progress_million_cny"),
            "initialFixedAssetOriginal": rounded(finance, "initial_fixed_asset_original_million_cny"),
            "initialFixedAssetResidualFloor": rounded(
                finance,
                "initial_fixed_asset_residual_floor_million_cny",
            ),
            "initialFixedAssetAccumulatedDepreciation": rounded(
                finance,
                "initial_fixed_asset_accumulated_depreciation_million_cny",
            ),
            "initialFixedAssetBookValue": rounded(finance, "initial_fixed_asset_book_value_million_cny"),
            "initialFixedAssetPeriodDepreciation": rounded(
                finance,
                "initial_fixed_asset_period_depreciation_million_cny",
            ),
            "fixedAssetOriginal": rounded(finance, "fixed_asset_original_million_cny"),
            "fixedAssetAccumulatedDepreciation": rounded(
                finance,
                "fixed_asset_accumulated_depreciation_million_cny",
            ),
            "fixedAssetBookValue": rounded(finance, "fixed_asset_book_value_million_cny"),
            "totalNoncurrentAssets": rounded(finance, "total_noncurrent_assets_million_cny"),
            "totalAssets": total_assets,
            "grossDebt": total_liabilities,
            "netDebt": round(total_liabilities - end_cash, 4),
            "shortTermDebt": rounded(finance, "short_term_debt_million_cny"),
            "longTermDebt": rounded(finance, "long_term_debt_million_cny"),
            "totalLiabilities": total_liabilities,
            "totalEquity": rounded(finance, "total_equity_million_cny"),
            "liabilityRatioPct": round(liability_ratio_pct, 4),
            "loanActiveIds": as_text(finance, "loan_active_ids"),
            "loanDrawdownIds": as_text(finance, "loan_drawdown_ids"),
            "loanPrincipalRepaymentIds": as_text(finance, "loan_principal_repayment_ids"),
            "loanWeightedInterestRatePct": rounded(finance, "loan_weighted_interest_rate_pct"),
            "loanDrawdownWeightedInterestRatePct": rounded(finance, "loan_drawdown_weighted_interest_rate_pct"),
            "loanDrawdownLeverageBeforePct": rounded(finance, "loan_drawdown_leverage_before_pct"),
            "loanDrawdownLeverageAfterPct": rounded(finance, "loan_drawdown_leverage_after_pct"),
            "loanDrawdownLeverageSpreadBps": rounded(finance, "loan_drawdown_leverage_spread_bps"),
            "loanBlockedIds": as_text(finance, "loan_blocked_ids"),
            "loanBlockedReasons": as_text(finance, "loan_blocked_reasons"),
            "macroTenYearYieldPct": rounded(ops, "input_10y_yield_pct"),
            "macroHySpreadBps": rounded(ops, "input_hy_spread_bps"),
        },
        "projects": {
            "renovationActiveIds": as_text(ops, "renovation_active_event_ids"),
            "renovationCompletedIds": as_text(ops, "renovation_completed_event_ids"),
            "renovationAssetInServicePeriods": rounded(ops, "renovation_asset_in_service_periods"),
            "renovationDesignCapacityLoss": rounded(ops, "renovation_design_capacity_loss_million"),
            "renovationMaxCapacityLoss": rounded(ops, "renovation_max_capacity_loss_million"),
            "renovationCapex": rounded(ops, "renovation_quarter_capex_outlay_million_cny"),
            "renovationConstructionInProgress": rounded(
                ops,
                "renovation_construction_in_progress_million_cny",
            ),
            "renovationAssetOriginal": rounded(ops, "renovation_asset_original_million_cny"),
            "renovationAssetAccumulatedDepreciation": rounded(
                ops,
                "renovation_asset_accumulated_depreciation_million_cny",
            ),
            "renovationAssetBookValue": rounded(ops, "renovation_asset_book_value_million_cny"),
            "renovationAssetPeriodDepreciation": rounded(
                ops,
                "renovation_asset_period_depreciation_million_cny",
            ),
            "constructionActiveIds": as_text(ops, "construction_active_event_ids"),
            "constructionCompletedIds": as_text(ops, "construction_completed_event_ids"),
            "constructionAssetInServicePeriods": rounded(ops, "construction_asset_in_service_periods"),
            "constructionCapex": rounded(ops, "construction_quarter_capex_outlay_million_cny"),
            "constructionInProgress": rounded(ops, "construction_in_progress_million_cny"),
            "constructionAssetOriginal": rounded(ops, "construction_asset_original_million_cny"),
            "constructionAssetAccumulatedDepreciation": rounded(
                ops,
                "construction_asset_accumulated_depreciation_million_cny",
            ),
            "constructionAssetBookValue": rounded(ops, "construction_asset_book_value_million_cny"),
            "constructionAssetPeriodDepreciation": rounded(
                ops,
                "construction_asset_period_depreciation_million_cny",
            ),
            "rebuildActiveIds": as_text(ops, "rebuild_active_event_ids"),
            "rebuildStartedIds": as_text(ops, "rebuild_started_event_ids"),
            "rebuildStartedSlotIds": as_text(ops, "rebuild_started_slot_ids"),
            "rebuildCompletedIds": as_text(ops, "rebuild_completed_event_ids"),
            "rebuildAssetInServicePeriods": rounded(ops, "rebuild_asset_in_service_periods"),
            "rebuildDesignCapacityLoss": rounded(ops, "rebuild_design_capacity_loss_million"),
            "rebuildMaxCapacityLoss": rounded(ops, "rebuild_max_capacity_loss_million"),
            "rebuildCompletedDesignCapacityDelta": rounded(
                ops,
                "rebuild_completed_design_capacity_delta_million",
            ),
            "rebuildCompletedMaxCapacityDelta": rounded(
                ops,
                "rebuild_completed_max_capacity_delta_million",
            ),
            "rebuildCapex": rounded(ops, "rebuild_quarter_capex_outlay_million_cny"),
            "rebuildDemolitionExpense": rounded(finance, "period_rebuild_demolition_expense_million_cny"),
            "rebuildOldInitialAssetWriteoff": rounded(
                finance,
                "period_rebuild_old_initial_asset_writeoff_million_cny",
            ),
            "rebuildOldRenovationAssetWriteoff": rounded(
                finance,
                "period_rebuild_old_renovation_asset_writeoff_million_cny",
            ),
            "rebuildOldAssetWriteoff": rounded(finance, "period_rebuild_old_asset_writeoff_million_cny"),
            "rebuildConstructionInProgress": rounded(ops, "rebuild_construction_in_progress_million_cny"),
            "rebuildAssetOriginal": rounded(ops, "rebuild_asset_original_million_cny"),
            "rebuildAssetAccumulatedDepreciation": rounded(
                ops,
                "rebuild_asset_accumulated_depreciation_million_cny",
            ),
            "rebuildAssetBookValue": rounded(ops, "rebuild_asset_book_value_million_cny"),
            "rebuildAssetPeriodDepreciation": rounded(
                ops,
                "rebuild_asset_period_depreciation_million_cny",
            ),
            "activeProjectIds": non_empty_ids(
                as_text(ops, "renovation_active_event_ids"),
                as_text(ops, "construction_active_event_ids"),
                as_text(ops, "rebuild_active_event_ids"),
            ),
            "completedProjectIds": non_empty_ids(
                as_text(ops, "renovation_completed_event_ids"),
                as_text(ops, "construction_completed_event_ids"),
                as_text(ops, "rebuild_completed_event_ids"),
            ),
        },
        "warnings": quarter_warnings(ops, finance),
    }


def aggregate_beijing_operations(
    run_dir: Path,
    seed: int,
    years: int,
    cached: bool,
    *,
    mode: str = "replay",
    operations_relative_csv: Path,
    financial_relative_csv: Path,
    root_dir: Path,
    operation_mode_details: dict[str, dict[str, str]],
    read_csv: Callable[[Path], list[dict[str, str]]],
    quarter_key: Callable[[dict[str, str]], tuple[int, str]],
    summarize_quarter: Callable[
        [int, dict[str, str], dict[str, str]],
        dict[str, Any],
    ],
) -> dict[str, Any]:
    operations_path = run_dir / operations_relative_csv
    financial_path = run_dir / financial_relative_csv
    if not operations_path.exists():
        raise FileNotFoundError(
            f"no Beijing quarterly operations output found in {operations_path}"
        )
    if not financial_path.exists():
        raise FileNotFoundError(
            f"no Beijing financial state output found in {financial_path}"
        )

    operation_rows = read_csv(operations_path)
    financial_rows = read_csv(financial_path)
    financial_by_quarter = {
        quarter_key(row): row
        for row in financial_rows
    }
    quarters: list[dict[str, Any]] = []
    for index, ops in enumerate(operation_rows):
        finance = financial_by_quarter.get(quarter_key(ops), {})
        quarters.append(summarize_quarter(index, ops, finance))

    player_start_index = next(
        (
            index
            for index, quarter in enumerate(quarters)
            if quarter["playerDecisionEnabled"]
        ),
        0,
    )
    return {
        "seed": seed,
        "years": years,
        "cached": cached,
        "mode": mode,
        "modeLabel": operation_mode_details[mode]["label"],
        "modeDescription": operation_mode_details[mode]["description"],
        "runId": run_dir.name,
        "runDir": str(run_dir.relative_to(root_dir).as_posix()),
        "operationSource": operations_relative_csv.parent.as_posix(),
        "cityName": "北京",
        "periodCount": len(quarters),
        "playerStartIndex": player_start_index,
        "startLabel": quarters[0]["label"] if quarters else "",
        "finalLabel": quarters[-1]["label"] if quarters else "",
        "quarters": quarters,
    }


def load_beijing_operations_locked(
    seed: int,
    years: int,
    force: bool,
    mode: str = "replay",
    *,
    run_root: Path,
    run_seed: Callable[[int, int, bool], dict[str, Any]],
    ensure_player_simulation_outputs: Callable[
        [Path, list[dict[str, Any]], bool],
        bool,
    ],
    aggregate_beijing_operations: Callable[..., dict[str, Any]],
    simulation_operations_relative_csv: Path,
    simulation_financial_relative_csv: Path,
) -> dict[str, Any]:
    run_payload = run_seed(seed, years, force)
    run_dir = run_root / str(run_payload["runId"])
    if mode == "simulate_default":
        simulation_cached = ensure_player_simulation_outputs(
            run_dir,
            [],
            force,
        )
        return aggregate_beijing_operations(
            run_dir,
            seed,
            years,
            bool(run_payload.get("cached")) and simulation_cached,
            mode,
            simulation_operations_relative_csv,
            simulation_financial_relative_csv,
        )
    try:
        return aggregate_beijing_operations(
            run_dir,
            seed,
            years,
            bool(run_payload.get("cached")),
            mode,
        )
    except FileNotFoundError:
        if force:
            raise
        run_payload = run_seed(seed, years, True)
        run_dir = run_root / str(run_payload["runId"])
        return aggregate_beijing_operations(
            run_dir,
            seed,
            years,
            False,
            mode,
        )


def load_beijing_operations(
    seed: int,
    years: int,
    force: bool,
    mode: str = "replay",
    *,
    run_id_for: Callable[[int, int], str],
    lock_for_run: Callable[[str], AbstractContextManager[Any]],
    load_locked: Callable[[int, int, bool, str], dict[str, Any]],
) -> dict[str, Any]:
    with lock_for_run(run_id_for(seed, years)):
        return load_locked(seed, years, force, mode)
