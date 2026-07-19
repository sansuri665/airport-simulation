from __future__ import annotations

from collections.abc import Callable, Collection
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class VariantOutputDependencies:
    orchestrator_version: str
    region_order: Collection[str]
    global_output_fields: Collection[str]
    regional_macro_fields: Collection[str]
    regional_value_fields: Collection[str]
    diagnostic_fields: Collection[str]
    aviation_demand_fields: Collection[str]
    air_supply_fields: Collection[str]
    city_airport_demand_fields: Collection[str]
    potential_passenger_forecast_fields: Collection[str]
    quarterly_operations_fields: Collection[str]
    financial_state_fields: Collection[str]
    valuation_forecast_fields: Collection[str]
    potential_passenger_forecast_config_dir: Path
    load_potential_passenger_forecast_config: Any
    write_csv_file: Callable[[Path, list[dict[str, Any]], Collection[str]], None]
    write_json_file: Callable[[Path, dict[str, Any]], None]
    write_global_viewer_data_js: Callable[[Path, list[dict[str, Any]]], None]
    write_reconciliation_viewer_js: Callable[..., None]
    write_global_viewer_lazy_assets: Callable[..., Any]
    load_city_configs_by_market: Callable[[Path, Any], dict[str, dict[str, Any]]]
    write_potential_passenger_forecast_lazy_assets: Callable[..., Any]
    write_operations_viewer_lazy_assets: Callable[..., Any]


def write_variant_outputs(
    variant_dir: Path,
    seed: int,
    variant_name: str,
    global_result: dict[str, Any],
    regional_result: dict[str, Any],
    scenario: dict[str, Any] | None,
    *,
    artifact_profile: str,
    dependencies: VariantOutputDependencies,
) -> None:
    write_viewer_artifacts = artifact_profile == "full"
    global_dir = variant_dir / "global_macro"
    regional_dir = variant_dir / "regional_macro"
    reconciled_dir = variant_dir / "regional_macro_reconciled"
    aviation_dir = variant_dir / "regional_aviation_demand"
    supply_dir = variant_dir / "regional_air_capacity_supply"
    city_airport_dir = variant_dir / "city_airport_market_demand"
    potential_passenger_forecast_dir = (
        variant_dir / "city_airport_potential_passenger_forecast"
    )
    quarterly_operations_dir = variant_dir / "city_airport_quarterly_operations"
    financial_state_dir = variant_dir / "city_airport_financial_state"
    valuation_forecast_dir = variant_dir / "city_airport_valuation"

    global_rows = global_result["rows"]
    dependencies.write_csv_file(
        global_dir / "global_macro_feedback_seed_sweep.csv",
        global_rows,
        dependencies.global_output_fields,
    )
    dependencies.write_json_file(
        global_dir / "global_macro_feedback_seed_sweep_summary.json",
        {
            "orchestrator_version": dependencies.orchestrator_version,
            "variant": variant_name,
            "seed": seed,
            "scenario": scenario,
            "params": {
                key: getattr(value, "__dict__", value)
                for key, value in global_result["params"].items()
            },
            "summaries": [global_result["summary"]],
            "convergence": [global_result["convergence"]],
        },
    )
    if write_viewer_artifacts:
        dependencies.write_global_viewer_data_js(
            global_dir / "global_macro_feedback_viewer_data.js",
            global_rows,
        )

    for region_id in dependencies.region_order:
        rows = regional_result["regional_rows_by_region"][region_id]
        region_dir = regional_dir / region_id
        dependencies.write_csv_file(
            region_dir / f"{region_id}_regional_macro_seed_sweep.csv",
            rows,
            dependencies.regional_macro_fields,
        )
        dependencies.write_json_file(
            region_dir / f"{region_id}_regional_macro_summary.json",
            {
                "orchestrator_version": dependencies.orchestrator_version,
                "variant": variant_name,
                "region": region_id,
                "summaries": [
                    summary
                    for summary in regional_result["regional_summaries"]
                    if summary.get("region_id") == region_id
                ],
            },
        )
    dependencies.write_csv_file(
        reconciled_dir / "regional_macro_reconciled_seed_sweep.csv",
        regional_result["reconciled_rows"],
        dependencies.regional_value_fields,
    )
    dependencies.write_csv_file(
        reconciled_dir / "regional_macro_reconciliation_seed_sweep.csv",
        regional_result["diagnostics"],
        dependencies.diagnostic_fields,
    )
    dependencies.write_json_file(
        reconciled_dir / "regional_macro_reconciliation_seed_sweep.json",
        {
            "orchestrator_version": dependencies.orchestrator_version,
            "variant": variant_name,
            "seed": seed,
            "diagnostics": len(regional_result["diagnostics"]),
            "summaries": regional_result["reconciliation_summaries"],
        },
    )
    dependencies.write_json_file(
        reconciled_dir / "regional_macro_reconciled_summary.json",
        {
            "orchestrator_version": dependencies.orchestrator_version,
            "variant": variant_name,
            "seed": seed,
            "rows": len(regional_result["reconciled_rows"]),
            "diagnostics": len(regional_result["diagnostics"]),
            "summaries": regional_result["reconciliation_summaries"],
        },
    )
    if write_viewer_artifacts:
        dependencies.write_reconciliation_viewer_js(
            reconciled_dir / "regional_macro_reconciled_viewer_data.js",
            regional_result["reconciled_rows"],
            regional_result["diagnostics"],
        )

    for region_id, rows in regional_result.get(
        "aviation_rows_by_region",
        {},
    ).items():
        region_dir = aviation_dir / region_id
        dependencies.write_csv_file(
            region_dir / f"{region_id}_aviation_demand_seed_sweep.csv",
            rows,
            dependencies.aviation_demand_fields,
        )
        dependencies.write_json_file(
            region_dir / f"{region_id}_aviation_demand_summary.json",
            {
                "orchestrator_version": dependencies.orchestrator_version,
                "variant": variant_name,
                "region": region_id,
                "summaries": [
                    summary
                    for summary in regional_result.get(
                        "aviation_summaries",
                        [],
                    )
                    if summary.get("region_id") == region_id
                ],
            },
        )
    for region_id, rows in regional_result.get(
        "supply_rows_by_region",
        {},
    ).items():
        region_dir = supply_dir / region_id
        dependencies.write_csv_file(
            region_dir / f"{region_id}_air_capacity_supply_seed_sweep.csv",
            rows,
            dependencies.air_supply_fields,
        )
        dependencies.write_json_file(
            region_dir / f"{region_id}_air_capacity_supply_summary.json",
            {
                "orchestrator_version": dependencies.orchestrator_version,
                "variant": variant_name,
                "region": region_id,
                "summaries": [
                    summary
                    for summary in regional_result.get(
                        "supply_summaries",
                        [],
                    )
                    if summary.get("region_id") == region_id
                ],
            },
        )
    if write_viewer_artifacts:
        dependencies.write_global_viewer_lazy_assets(global_dir, regional_result)

    for market_id, rows in regional_result.get(
        "city_airport_rows_by_market",
        {},
    ).items():
        if not rows:
            continue
        region_id = str(rows[0].get("region_id") or "unknown_region")
        region_dir = city_airport_dir / region_id
        dependencies.write_csv_file(
            region_dir / f"{market_id}_city_airport_demand_seed_sweep.csv",
            rows,
            dependencies.city_airport_demand_fields,
        )
        dependencies.write_json_file(
            region_dir / f"{market_id}_city_airport_demand_summary.json",
            {
                "orchestrator_version": dependencies.orchestrator_version,
                "variant": variant_name,
                "market": market_id,
                "region": region_id,
                "summaries": [
                    summary
                    for summary in regional_result.get(
                        "city_airport_summaries",
                        [],
                    )
                    if summary.get("city_airport_market_id") == market_id
                ],
            },
        )
    for market_id, rows in regional_result.get(
        "potential_passenger_forecast_rows_by_market",
        {},
    ).items():
        if not rows:
            continue
        region_id = str(rows[0].get("region_id") or "unknown_region")
        region_dir = potential_passenger_forecast_dir / region_id
        summary = regional_result.get(
            "potential_passenger_forecast_summaries",
            {},
        ).get(market_id, {})
        dependencies.write_csv_file(
            region_dir
            / f"{market_id}_potential_passenger_forecast_seed_sweep.csv",
            rows,
            dependencies.potential_passenger_forecast_fields,
        )
        dependencies.write_json_file(
            region_dir / f"{market_id}_potential_passenger_forecast_summary.json",
            {
                "orchestrator_version": dependencies.orchestrator_version,
                "variant": variant_name,
                "market": market_id,
                "region": region_id,
                "summary": summary,
            },
        )
        if write_viewer_artifacts:
            potential_forecast_config = dependencies.load_city_configs_by_market(
                dependencies.potential_passenger_forecast_config_dir,
                dependencies.load_potential_passenger_forecast_config,
            ).get(market_id, {})
            dependencies.write_potential_passenger_forecast_lazy_assets(
                region_dir,
                rows,
                potential_forecast_config,
            )

    for market_id, rows in regional_result.get(
        "quarterly_operations_rows_by_market",
        {},
    ).items():
        if not rows:
            continue
        region_id = str(rows[0].get("region_id") or "unknown_region")
        region_dir = quarterly_operations_dir / region_id
        summary = regional_result.get(
            "quarterly_operations_summaries",
            {},
        ).get(market_id, {})
        dependencies.write_csv_file(
            region_dir / f"{market_id}_quarterly_operations_seed_sweep.csv",
            rows,
            dependencies.quarterly_operations_fields,
        )
        dependencies.write_json_file(
            region_dir / f"{market_id}_quarterly_operations_summary.json",
            {
                "orchestrator_version": dependencies.orchestrator_version,
                "variant": variant_name,
                "market": market_id,
                "region": region_id,
                "summary": summary,
            },
        )
    for market_id, rows in regional_result.get(
        "financial_state_rows_by_market",
        {},
    ).items():
        if not rows:
            continue
        region_id = str(rows[0].get("region_id") or "unknown_region")
        region_dir = financial_state_dir / region_id
        summary = regional_result.get(
            "financial_state_summaries",
            {},
        ).get(market_id, {})
        dependencies.write_csv_file(
            region_dir / f"{market_id}_financial_state_seed_sweep.csv",
            rows,
            dependencies.financial_state_fields,
        )
        dependencies.write_json_file(
            region_dir / f"{market_id}_financial_state_summary.json",
            {
                "orchestrator_version": dependencies.orchestrator_version,
                "variant": variant_name,
                "market": market_id,
                "region": region_id,
                "summary": summary,
            },
        )
    for market_id, rows in regional_result.get(
        "valuation_forecast_rows_by_market",
        {},
    ).items():
        if not rows:
            continue
        region_id = str(rows[0].get("region_id") or "unknown_region")
        region_dir = valuation_forecast_dir / region_id
        summary = regional_result.get(
            "valuation_forecast_summaries",
            {},
        ).get(market_id, {})
        dependencies.write_csv_file(
            region_dir / f"{market_id}_valuation_forecast_seed_sweep.csv",
            rows,
            dependencies.valuation_forecast_fields,
        )
        dependencies.write_json_file(
            region_dir / f"{market_id}_valuation_forecast_summary.json",
            {
                "orchestrator_version": dependencies.orchestrator_version,
                "variant": variant_name,
                "market": market_id,
                "region": region_id,
                "summary": summary,
            },
        )
    if write_viewer_artifacts:
        for market_id, quarterly_rows in regional_result.get(
            "quarterly_operations_rows_by_market",
            {},
        ).items():
            if not quarterly_rows:
                continue
            region_id = str(
                quarterly_rows[0].get("region_id") or "unknown_region"
            )
            dependencies.write_operations_viewer_lazy_assets(
                quarterly_operations_dir / region_id,
                market_id,
                quarterly_rows,
                regional_result.get(
                    "financial_state_rows_by_market",
                    {},
                ).get(market_id, []),
                regional_result.get(
                    "valuation_forecast_rows_by_market",
                    {},
                ).get(market_id, []),
            )

    dependencies.write_json_file(
        variant_dir / "city_airport_downstream_skips.json",
        {
            "orchestrator_version": dependencies.orchestrator_version,
            "variant": variant_name,
            "skips": regional_result.get("city_airport_downstream_skips", []),
        },
    )
