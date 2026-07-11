from __future__ import annotations

import argparse
import functools
import hashlib
import json
import sys
import unittest
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
MACRO_DIR = ROOT_DIR / "macro_layers"
if str(MACRO_DIR) not in sys.path:
    sys.path.insert(0, str(MACRO_DIR))

import macro_run_orchestrator_sim as orchestrator
from airport_sim.server import app as seed_explorer_server


FIXTURE_PATH = ROOT_DIR / "tests" / "fixtures" / "seed_explorer_api_snapshot_seed_20261324_years_12.json"


def canonical_digest(payload: Any) -> str:
    raw = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def selected_city_values(city: dict[str, Any]) -> dict[str, Any]:
    fields = (
        "id",
        "finalPotential",
        "finalAirlineSupply",
        "finalEffective",
        "finalSupplyGap",
        "effectiveCagrPct",
        "finalBottleneck",
    )
    return {field: city[field] for field in fields}


def selected_quarter_values(quarter: dict[str, Any]) -> dict[str, Any]:
    return {
        "label": quarter["label"],
        "gamePhase": quarter["gamePhase"],
        "playerDecisionEnabled": quarter["playerDecisionEnabled"],
        "annualServed": quarter["demand"]["annualServed"],
        "quarterServed": quarter["demand"]["quarterServed"],
        "totalRevenue": quarter["operations"]["totalRevenue"],
        "operatingProfit": quarter["operations"]["operatingProfit"],
        "endCash": quarter["finance"]["endCash"],
        "totalAssets": quarter["finance"]["totalAssets"],
        "grossDebt": quarter["finance"]["grossDebt"],
        "warnings": quarter["warnings"],
    }


@functools.lru_cache(maxsize=1)
def build_fixed_seed_api_artifacts() -> tuple[
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
]:
    seed = 20261324
    years = 12
    args = argparse.Namespace(
        years=years,
        start_year=2025,
        initial_gdp=100.0,
        volatility_scale=1.0,
        feedback_iterations=1,
    )
    global_result = orchestrator.run_global_variant(seed, args, "baseline")
    regional = orchestrator.run_regional_and_reconciliation(seed, global_result["rows"])

    cities = [
        seed_explorer_server.summarize_city(rows)
        for rows in regional["city_airport_rows_by_market"].values()
        if rows
    ]
    cities.sort(key=lambda item: item["finalEffective"], reverse=True)
    rankings = [
        {
            "rank": index + 1,
            "id": city["id"],
            "name": city["name"],
            "finalEffective": city["finalEffective"],
            "finalPotential": city["finalPotential"],
            "finalAirlineSupply": city["finalAirlineSupply"],
        }
        for index, city in enumerate(cities)
    ]
    city_payload = {
        "seed": seed,
        "years": years,
        "cityCount": len(cities),
        "startYear": min(city["startYear"] for city in cities),
        "finalYear": max(city["finalYear"] for city in cities),
        "cities": cities,
        "rankings": rankings,
    }

    operation_rows = regional["quarterly_operations_rows_by_market"]["beijing_airport_system"]
    financial_rows = regional["financial_state_rows_by_market"]["beijing_airport_system"]
    financial_by_quarter = {
        seed_explorer_server.quarter_key(row): row
        for row in financial_rows
    }
    quarters = [
        seed_explorer_server.summarize_beijing_quarter(
            index,
            row,
            financial_by_quarter.get(seed_explorer_server.quarter_key(row), {}),
        )
        for index, row in enumerate(operation_rows)
    ]
    player_start_index = next(
        index for index, quarter in enumerate(quarters) if quarter["playerDecisionEnabled"]
    )
    operations_payload = {
        "seed": seed,
        "years": years,
        "mode": "replay",
        "cityName": "北京",
        "periodCount": len(quarters),
        "playerStartIndex": player_start_index,
        "startLabel": quarters[0]["label"],
        "finalLabel": quarters[-1]["label"],
        "quarters": quarters,
    }
    nested_keys = {
        key: list(quarters[0][key])
        for key in ("demand", "capacity", "operations", "finance", "projects")
    }
    beijing = next(city for city in cities if city["id"] == "beijing_airport_system")
    snapshot = {
        "snapshotSchemaVersion": "seed-explorer-api-snapshot-v1",
        "apiSchemaVersion": seed_explorer_server.SEED_EXPLORER_API_SCHEMA_VERSION,
        "modelVersion": seed_explorer_server.MODEL_VERSION,
        "outputSchemaVersion": seed_explorer_server.OUTPUT_SCHEMA_VERSION,
        "schemaCatalog": "/api/schema",
        "seed": seed,
        "years": years,
        "cityMarket": {
            "sha256": canonical_digest(city_payload),
            "cityCount": len(cities),
            "cityKeys": list(cities[0]),
            "pointKeys": list(cities[0]["points"][0]),
            "leader": selected_city_values(cities[0]),
            "beijing": selected_city_values(beijing),
        },
        "beijingOperations": {
            "sha256": canonical_digest(operations_payload),
            "periodCount": len(quarters),
            "playerStartIndex": player_start_index,
            "quarterKeys": list(quarters[0]),
            "nestedKeysSha256": canonical_digest(nested_keys),
            "nestedKeyCounts": {key: len(value) for key, value in nested_keys.items()},
            "firstQuarter": selected_quarter_values(quarters[0]),
            "playerStartQuarter": selected_quarter_values(quarters[player_start_index]),
            "finalQuarter": selected_quarter_values(quarters[-1]),
        },
    }
    run_response = seed_explorer_server.api_envelope(
        {
            "ok": True,
            "cached": False,
            "elapsedSec": 0.0,
            "runId": "seed_20261324_years_12",
            "runDir": "output/seed_explorer_runs/seed_20261324_years_12",
            "generatedAt": "snapshot",
            **city_payload,
        }
    )
    operations_response = seed_explorer_server.api_envelope(
        {
            "ok": True,
            "cached": False,
            "modeLabel": "加载历史",
            "modeDescription": "固定 Seed API Schema 测试",
            "runId": "seed_20261324_years_12",
            "runDir": "output/seed_explorer_runs/seed_20261324_years_12",
            "operationSource": "baseline/city_airport_quarterly_operations/china_mainland",
            **operations_payload,
        }
    )
    player_response = {
        **operations_response,
        "mode": "simulate_default",
        "modeLabel": "模拟运营",
        "modeDescription": "固定 Seed 玩家模拟 Schema 测试",
        "quarters": quarters[: player_start_index + 1],
        "allQuarters": quarters,
        "periodCount": player_start_index + 1,
        "worldPeriodCount": len(quarters),
        "worldFinalLabel": quarters[-1]["label"],
        "finalLabel": quarters[player_start_index]["label"],
        "currentQuarterIndex": player_start_index,
        "playerActions": [],
        "actionCount": 0,
        "slotNames": seed_explorer_server.player_slot_names([]),
        "projectCatalog": seed_explorer_server.project_catalog(),
        "financingProducts": seed_explorer_server.FINANCING_PRODUCTS,
        "financingPolicy": seed_explorer_server.read_json(
            seed_explorer_server.BEIJING_FINANCE_CONFIG
        ).get("debt_policy", {}).get("loan_rate_model", {}),
        "contractPreviews": {},
        "operationSource": "simulation_default/server_action_journal",
    }
    return snapshot, run_response, operations_response, player_response


def build_fixed_seed_api_snapshot() -> dict[str, Any]:
    return build_fixed_seed_api_artifacts()[0]


class SeedExplorerAPISnapshotTests(unittest.TestCase):
    def test_fixed_seed_api_snapshot(self) -> None:
        expected = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(expected, build_fixed_seed_api_snapshot())


if __name__ == "__main__":
    unittest.main()
