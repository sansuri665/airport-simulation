from __future__ import annotations

import math
from typing import Any

from .validation import as_float


CITY_COMPONENTS = ("business", "leisure", "vfr", "long_haul", "transfer")


def cagr_pct(start_value: float, end_value: float, years: int) -> float:
    if start_value <= 0.0 or end_value <= 0.0 or years <= 0:
        return 0.0
    return (math.pow(end_value / start_value, 1.0 / years) - 1.0) * 100.0


def market_bottleneck(potential: float, supply: float) -> str:
    return "airline_supply_limited" if supply < potential else "demand_limited"


def _rounded(row: dict[str, str], field: str, default: float = 0.0) -> float:
    return round(as_float(row.get(field), default), 4)


def _component_summary(row: dict[str, str], component: str) -> dict[str, Any]:
    return {
        "potential": _rounded(row, f"{component}_passengers_million"),
        "offeredCapacity": _rounded(row, f"{component}_airline_offered_capacity_million"),
        "airlineSupply": _rounded(row, f"{component}_airline_supply_passengers_million"),
        "served": _rounded(row, f"{component}_served_passengers_million"),
        "supplyGap": _rounded(row, f"{component}_airline_supply_gap_million"),
        "supplyFulfillmentPct": _rounded(
            row, f"{component}_airline_supply_fulfillment_pct"
        ),
        "potentialSharePct": _rounded(row, f"{component}_passenger_share_pct"),
        "supplySharePct": _rounded(row, f"{component}_airline_supply_share_pct"),
        "priorityWeight": _rounded(row, f"{component}_airline_supply_priority_weight"),
    }


def summarize_city(rows: list[dict[str, str]]) -> dict[str, Any]:
    first = rows[0]
    last = rows[-1]
    start_year = int(as_float(first.get("year")))
    final_year = int(as_float(last.get("year")))
    first_effective = min(
        as_float(first.get("city_potential_passengers_million")),
        as_float(first.get("city_airline_supply_passengers_million")),
    )
    final_potential = as_float(last.get("city_potential_passengers_million"))
    final_supply = as_float(last.get("city_airline_supply_passengers_million"))
    final_effective = min(final_potential, final_supply)
    peak_effective = max(
        min(
            as_float(row.get("city_potential_passengers_million")),
            as_float(row.get("city_airline_supply_passengers_million")),
        )
        for row in rows
    )
    bottleneck_years = {
        "airline_supply_limited": 0,
        "demand_limited": 0,
    }
    points: list[dict[str, Any]] = []
    for row in rows:
        potential = as_float(row.get("city_potential_passengers_million"))
        supply = as_float(row.get("city_airline_supply_passengers_million"))
        effective = min(potential, supply)
        bottleneck = str(row.get("city_binding_bottleneck") or market_bottleneck(potential, supply))
        if bottleneck not in bottleneck_years:
            bottleneck_years[bottleneck] = 0
        bottleneck_years[bottleneck] += 1
        points.append(
            {
                "year": int(as_float(row.get("year"))),
                "potential": round(potential, 4),
                "airlineOffered": _rounded(row, "city_airline_offered_capacity_million", supply),
                "airlineSupply": round(supply, 4),
                "effective": round(effective, 4),
                "serviceable": round(effective, 4),
                "served": round(as_float(row.get("city_served_passengers_million"), effective), 4),
                "unmet": _rounded(row, "city_unmet_passengers_million"),
                "unusedAirlineCapacity": _rounded(row, "city_airline_unused_capacity_million"),
                "supplyGap": round(max(0.0, potential - supply), 4),
                "supplyFulfillmentPct": round(as_float(row.get("city_airline_supply_fulfillment_pct")), 4),
                "capacityFulfillmentPct": _rounded(row, "city_capacity_fulfillment_pct"),
                "totalFulfillmentPct": _rounded(row, "city_total_fulfillment_pct"),
                "airportCapacityGap": _rounded(row, "city_airport_capacity_gap_million"),
                "designCapacity": _rounded(row, "city_airport_design_capacity_million"),
                "maxCapacity": _rounded(row, "city_airport_max_capacity_million"),
                "designUtilizationPct": _rounded(row, "city_airport_design_utilization_pct"),
                "maxUtilizationPct": _rounded(row, "city_airport_max_utilization_pct"),
                "bindingBottleneck": bottleneck,
                "supplyRegime": str(row.get("city_airline_supply_regime") or ""),
                "supplyVolatilityRegime": str(row.get("city_airline_supply_volatility_regime") or ""),
                "supplyBehaviorPhase": str(row.get("city_airline_supply_behavior_phase") or ""),
                "supplyPhaseAgeYears": _rounded(row, "city_airline_supply_phase_age_years"),
                "supplyCycleNumber": int(as_float(row.get("city_airline_supply_cycle_number"))),
                "supplyDeviationFromFundamentalPct": _rounded(
                    row, "city_airline_supply_deviation_from_fundamental_pct"
                ),
                "supplyDeviationFromPotentialPct": _rounded(
                    row, "city_airline_supply_deviation_from_potential_pct"
                ),
                "supplyExcessOverPotentialPct": _rounded(
                    row, "city_airline_supply_excess_over_potential_pct"
                ),
                "supplyEventImpulsePct": _rounded(row, "city_airline_supply_event_impulse_pct"),
                "supplyShockImpulsePct": _rounded(row, "city_airline_supply_shock_impulse_pct"),
                "components": {
                    component: _component_summary(row, component)
                    for component in CITY_COMPONENTS
                },
            }
        )

    return {
        "id": str(first.get("city_airport_market_id") or ""),
        "name": str(first.get("city_name") or first.get("city_airport_market_id") or ""),
        "region": str(first.get("region_name") or first.get("region_id") or ""),
        "marketTier": str(first.get("market_tier") or ""),
        "marketType": str(first.get("market_type") or ""),
        "startYear": start_year,
        "finalYear": final_year,
        "finalPotential": round(final_potential, 4),
        "finalAirlineSupply": round(final_supply, 4),
        "finalEffective": round(final_effective, 4),
        "finalServed": _rounded(last, "city_served_passengers_million", final_effective),
        "finalSupplyGap": round(max(0.0, final_potential - final_supply), 4),
        "effectiveCagrPct": round(cagr_pct(first_effective, final_effective, final_year - start_year), 4),
        "peakEffective": round(peak_effective, 4),
        "finalBottleneck": market_bottleneck(final_potential, final_supply),
        "bottleneckYears": bottleneck_years,
        "points": points,
    }
