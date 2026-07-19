from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Iterable
from typing import Any

from .validation import as_float


CITY_COMPONENTS = ("business", "leisure", "vfr", "long_haul", "transfer")
CITY_MARKET_VIEWER_LAZY_INDEX_VERSION = "airport-city-market-viewer-lazy-index-v2"
CITY_MARKET_VIEWER_CHUNK_VERSION = "airport-city-market-viewer-chunk-v2"
GLOBAL_VIEWER_LAZY_INDEX_VERSION = "airport-global-viewer-lazy-index-v1"
GLOBAL_VIEWER_REGION_CHUNK_VERSION = "airport-global-viewer-region-chunk-v1"
GLOBAL_VIEWER_OPTIONAL_SCENARIO_FIELDS = frozenset(
    {
        "scenario_credit_stress_impulse",
        "scenario_dollar_pressure_impulse",
        "scenario_energy_price_impulse",
        "scenario_event_phase",
        "scenario_event_severity",
        "scenario_event_type",
        "scenario_feedback_source",
        "scenario_gdp_lagged_support",
        "scenario_impact_years",
        "scenario_liquidity_impulse",
        "scenario_phase",
        "scenario_policy_rate_impulse",
        "scenario_risk_id",
        "scenario_risk_label",
        "scenario_state",
        "scenario_tail_years",
        "scenario_trigger_index",
        "scenario_trigger_year",
    }
)
_JSON_NUMBER_PATTERN = re.compile(
    r"^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?$"
)


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


def serialize_city_market_viewer_rows(
    rows: list[dict[str, str]],
    *,
    source: str = "city market rows",
) -> dict[str, Any]:
    """Build the public city Viewer projection without airport operations fields."""

    if not rows:
        raise ValueError(f"city market Viewer source contains no rows: {source}")
    summary = summarize_city(rows)
    market_id = str(summary["id"])
    if not market_id or not market_id.replace("_", "").isalnum():
        raise ValueError(f"unsafe city market id in {source}: {market_id!r}")

    city_points: list[dict[str, Any]] = []
    for point in summary["points"]:
        components = {
            component_id: {
                key: component[key]
                for key in (
                    "potential",
                    "offeredCapacity",
                    "airlineSupply",
                    "supplyGap",
                    "supplyFulfillmentPct",
                    "potentialSharePct",
                    "supplySharePct",
                    "priorityWeight",
                )
            }
            for component_id, component in point["components"].items()
        }
        city_points.append(
            {
                key: point[key]
                for key in (
                    "year",
                    "potential",
                    "airlineOffered",
                    "airlineSupply",
                    "serviceable",
                    "unusedAirlineCapacity",
                    "supplyGap",
                    "supplyFulfillmentPct",
                    "supplyRegime",
                    "supplyVolatilityRegime",
                    "supplyBehaviorPhase",
                    "supplyPhaseAgeYears",
                    "supplyCycleNumber",
                    "supplyDeviationFromFundamentalPct",
                    "supplyDeviationFromPotentialPct",
                    "supplyExcessOverPotentialPct",
                    "supplyEventImpulsePct",
                    "supplyShockImpulsePct",
                )
            }
            | {"components": components}
        )

    viewer_city = {
        key: summary[key]
        for key in (
            "id",
            "name",
            "region",
            "marketTier",
            "marketType",
            "startYear",
            "finalYear",
            "finalPotential",
            "finalAirlineSupply",
            "finalEffective",
            "finalSupplyGap",
            "effectiveCagrPct",
            "peakEffective",
        )
    } | {"points": city_points}
    filename = f"c_{market_id}.json"
    chunk_payload = {
        "schemaVersion": CITY_MARKET_VIEWER_CHUNK_VERSION,
        "marketId": market_id,
        "rowCount": len(rows),
        "city": viewer_city,
    }
    raw = json.dumps(
        chunk_payload,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    ranking_points = [
        {
            "year": point["year"],
            "potential": point["potential"],
            "airlineSupply": point["airlineSupply"],
            "serviceable": point["serviceable"],
            "supplyGap": point["supplyGap"],
            "supplyFulfillmentPct": point["supplyFulfillmentPct"],
            "unusedAirlineCapacity": point["unusedAirlineCapacity"],
        }
        for point in city_points
    ]
    city_meta = {
        key: summary[key]
        for key in (
            "id",
            "name",
            "region",
            "marketTier",
            "marketType",
            "startYear",
            "finalYear",
            "finalPotential",
            "finalAirlineSupply",
            "finalEffective",
            "finalSupplyGap",
            "effectiveCagrPct",
            "peakEffective",
        )
    } | {
        "rowCount": len(rows),
        "file": filename,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
        "rankingPoints": ranking_points,
    }
    return {
        "marketId": market_id,
        "filename": filename,
        "seedValues": {int(as_float(row.get("seed"))) for row in rows},
        "startYear": int(summary["startYear"]),
        "finalYear": int(summary["finalYear"]),
        "cityMeta": city_meta,
        "chunkPayload": chunk_payload,
        "raw": raw,
    }


def serialize_city_market_viewer_dataset(
    market_rows: Iterable[tuple[str, list[dict[str, str]]]],
    *,
    chunk_dir_name: str = "city_market_viewer_chunks",
) -> dict[str, Any]:
    """Build a deterministic index and per-city chunks without writing files."""

    serialized_cities = [
        serialize_city_market_viewer_rows(rows, source=source)
        for source, rows in market_rows
        if rows
    ]
    if not serialized_cities:
        raise ValueError("city market Viewer sources contain no rows")

    seeds: set[int] = set()
    start_years: set[int] = set()
    final_years: set[int] = set()
    cities: list[dict[str, Any]] = []
    chunks: dict[str, dict[str, Any]] = {}
    for serialized in serialized_cities:
        seeds.update(serialized["seedValues"])
        start_years.add(serialized["startYear"])
        final_years.add(serialized["finalYear"])
        cities.append(serialized["cityMeta"])
        chunks[serialized["marketId"]] = serialized

    if len(start_years) != 1 or len(final_years) != 1:
        raise ValueError("city market Viewer requires a shared year range")
    cities.sort(key=lambda city: (-float(city["finalEffective"]), str(city["id"])))
    index = {
        "schemaVersion": CITY_MARKET_VIEWER_LAZY_INDEX_VERSION,
        "chunkSchemaVersion": CITY_MARKET_VIEWER_CHUNK_VERSION,
        "chunkBase": f"./{chunk_dir_name}/",
        "seed": next(iter(seeds)) if len(seeds) == 1 else None,
        "startYear": next(iter(start_years)),
        "finalYear": next(iter(final_years)),
        "cityCount": len(cities),
        "cities": cities,
    }
    return {"index": index, "chunks": chunks}


def decode_viewer_csv_rows(
    rows: Iterable[dict[str, Any]],
    *,
    null_fields: frozenset[str] = frozenset(),
    omit_empty_fields: frozenset[str] = frozenset(),
) -> list[dict[str, Any]]:
    """Restore JSON scalar types from model CSV rows without changing values."""

    decoded: list[dict[str, Any]] = []
    for row in rows:
        item: dict[str, Any] = {}
        for key, value in row.items():
            if value == "" and key in omit_empty_fields:
                continue
            if not isinstance(value, str):
                item[key] = value
            elif value == "" and key in null_fields:
                item[key] = None
            elif value and _JSON_NUMBER_PATTERN.fullmatch(value):
                item[key] = (
                    float(value)
                    if any(marker in value for marker in (".", "e", "E"))
                    else int(value)
                )
            else:
                item[key] = value
        decoded.append(item)
    return decoded


def serialize_global_viewer_core(
    global_rows: Iterable[dict[str, Any]],
    reconciled_rows: Iterable[dict[str, Any]],
    diagnostic_rows: Iterable[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Build the immutable global Viewer core payload without writing files."""

    return {
        "globalRows": [dict(row) for row in global_rows],
        "regionalReconciledRows": [dict(row) for row in reconciled_rows],
        "regionalReconciliationRows": [dict(row) for row in diagnostic_rows],
    }


def global_viewer_core_scripts(
    core: dict[str, list[dict[str, Any]]],
) -> dict[str, str]:
    """Render the two existing Release scripts from a serialized core payload."""

    compact = lambda value: json.dumps(  # noqa: E731 - keeps both scripts identical
        value,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return {
        "global": (
            "window.GLOBAL_MACRO_FEEDBACK_DATA = "
            + compact(core["globalRows"])
            + ";\n"
        ),
        "reconciliation": (
            "window.REGIONAL_MACRO_RECONCILED_DATA = "
            + compact(core["regionalReconciledRows"])
            + ";\nwindow.REGIONAL_MACRO_RECONCILIATION_DATA = "
            + compact(core["regionalReconciliationRows"])
            + ";\n"
        ),
    }


def serialize_global_viewer_region(
    region_id: str,
    region_name: str,
    regional_rows: Iterable[dict[str, Any]],
    aviation_rows: Iterable[dict[str, Any]],
    supply_rows: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    """Build one regional macro/aviation/supply chunk and its index metadata."""

    clean_region_id = str(region_id).strip()
    if not clean_region_id or not clean_region_id.replace("_", "").isalnum():
        raise ValueError(f"unsafe global Viewer region id: {region_id!r}")
    regional = [dict(row) for row in regional_rows]
    aviation = [dict(row) for row in aviation_rows]
    supply = [dict(row) for row in supply_rows]
    filename = f"r_{clean_region_id}.json"
    chunk_payload = {
        "schemaVersion": GLOBAL_VIEWER_REGION_CHUNK_VERSION,
        "regionId": clean_region_id,
        "regionalMacroRows": regional,
        "aviationDemandRows": aviation,
        "airCapacitySupplyRows": supply,
    }
    raw = json.dumps(
        chunk_payload,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return {
        "regionId": clean_region_id,
        "filename": filename,
        "chunkPayload": chunk_payload,
        "raw": raw,
        "regionMeta": {
            "regionId": clean_region_id,
            "regionName": str(region_name),
            "regionalMacroRowCount": len(regional),
            "aviationDemandRowCount": len(aviation),
            "airCapacitySupplyRowCount": len(supply),
            "file": filename,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw),
        },
    }


def serialize_global_viewer_dataset(
    region_inputs: Iterable[
        tuple[
            str,
            str,
            Iterable[dict[str, Any]],
            Iterable[dict[str, Any]],
            Iterable[dict[str, Any]],
        ]
    ],
    *,
    chunk_dir_name: str = "global_viewer_chunks",
) -> dict[str, Any]:
    """Build the deterministic regional index and chunks without file writes."""

    serialized_regions: list[dict[str, Any]] = []
    seen: set[str] = set()
    for region_id, region_name, regional_rows, aviation_rows, supply_rows in region_inputs:
        serialized = serialize_global_viewer_region(
            region_id,
            region_name,
            regional_rows,
            aviation_rows,
            supply_rows,
        )
        if serialized["regionId"] in seen:
            raise ValueError(f"duplicate global Viewer region id: {serialized['regionId']}")
        seen.add(serialized["regionId"])
        serialized_regions.append(serialized)
    if not serialized_regions:
        raise ValueError("global Viewer requires at least one regional dataset")
    index = {
        "schemaVersion": GLOBAL_VIEWER_LAZY_INDEX_VERSION,
        "chunkSchemaVersion": GLOBAL_VIEWER_REGION_CHUNK_VERSION,
        "chunkBase": f"./{chunk_dir_name}/",
        "regions": [item["regionMeta"] for item in serialized_regions],
    }
    return {
        "index": index,
        "chunks": {item["regionId"]: item for item in serialized_regions},
    }
