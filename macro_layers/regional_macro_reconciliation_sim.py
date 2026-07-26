from __future__ import annotations

from importlib import import_module

_SIBLING_PREFIX = f"{__package__}." if __package__ else ""
simulation_io = import_module(f"{_SIBLING_PREFIX}simulation_io")
simulation_utils = import_module(f"{_SIBLING_PREFIX}simulation_utils")

write_json = simulation_io.write_json_utf8_payload
clamp = simulation_utils.clamp

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

regional_macro_layer = import_module(f"{_SIBLING_PREFIX}regional_macro_layer_sim")
REGION_CONFIGS = regional_macro_layer.REGION_CONFIGS
RECONCILED_FIELD_BOUNDS = regional_macro_layer.REGIONAL_RECONCILED_FIELD_BOUNDS


RECONCILIATION_PARAM_VERSION = "regional-macro-reconciliation-v0.4"
RECONCILIATION_INTERFACE_VERSION = "regional-macro-reconciliation-interface-v0.4"


def reconciled_field_bounds(region_id: str) -> dict[str, tuple[float, float]]:
    """Bounds for reconciled regional fields, including per-region policy-rate limits."""
    config = REGION_CONFIGS[region_id]
    bounds = dict(RECONCILED_FIELD_BOUNDS)
    bounds["regional_policy_rate_pct"] = (
        float(config.policy_floor_pct),
        float(config.policy_ceiling_pct),
    )
    return bounds


def clamp_reconciled_value(region_id: str, field: str, value: float) -> float:
    bounds = reconciled_field_bounds(region_id).get(field)
    if bounds is None:
        return value
    floor, ceiling = bounds
    return clamp(value, floor, ceiling)


REGION_ORDER = [
    "north_america",
    "china_mainland",
    "west_north_europe",
    "japan_korea",
    "southeast_asia",
    "south_asia_india",
    "hk_macao_taiwan",
    "middle_east_gulf",
    "oceania",
    "south_east_europe_mediterranean",
    "central_asia_turkey_eurasia",
    "north_africa",
    "latin_america_caribbean",
    "sub_saharan_africa",
]


REGIONAL_BRANCH_FIELDS = [
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
]


REGIONAL_BRANCH_TEXT_FIELDS = {
    "regional_branch_transmission_version",
    "branch_scenario_id",
    "branch_scenario_label",
    "branch_scenario_state",
    "branch_effect_phase",
    "regional_branch_transmission_active",
}


REGIONAL_VALUE_FIELDS = [
    "reconciliation_param_version",
    "reconciliation_interface_version",
    "reconciliation_scope",
    "year_index",
    "year",
    "seed",
    "region_id",
    "region_name",
    "regional_global_weight_config",
    "regional_normalized_initial_weight",
    "regional_normalized_initial_weight_pct",
    "regional_structural_seed_version",
    "regional_seed_potential_enabled",
    "regional_seed_potential_template_id",
    "regional_seed_primary_theme",
    "regional_seed_secondary_theme",
    "regional_seed_structural_score",
    "regional_seed_momentum_label",
    "regional_seed_effective_growth_bias_pct",
    "regional_seed_aviation_propensity_bias_pct",
    "regional_seed_investment_cycle_bias_pct",
    "regional_seed_openness_bias_pct",
    "regional_seed_demand_multiplier",
    "global_gdp_anchor_trillion_usd",
    "global_growth_anchor_pct",
    "global_real_gdp_index",
    "regional_gdp_index",
    "regional_gdp_growth_pct_raw",
    "regional_gdp_growth_pct_reconciled",
    "regional_potential_growth_pct",
    "regional_output_gap_pct",
    "regional_raw_gdp_trillion_usd",
    "regional_reconciled_gdp_trillion_usd",
    "regional_raw_share_of_global_gdp_pct",
    "regional_reconciled_share_of_global_gdp_pct",
    "regional_share_change_from_start_pct",
    "regional_weight_drift_pp",
    "regional_rank_by_gdp",
    "regional_growth_contribution_pp_raw",
    "regional_growth_contribution_pp_reconciled",
    "regional_headline_inflation_pct_raw",
    "regional_headline_inflation_pct_reconciled",
    "regional_core_inflation_pct_raw",
    "regional_core_inflation_pct_reconciled",
    "regional_policy_rate_pct_raw",
    "regional_policy_rate_pct_reconciled",
    "regional_10y_yield_pct_raw",
    "regional_10y_yield_pct_reconciled",
    "regional_hy_spread_bps_raw",
    "regional_hy_spread_bps_reconciled",
    "regional_ig_spread_bps_raw",
    "regional_ig_spread_bps_reconciled",
    "regional_macro_stress_index_raw",
    "regional_macro_stress_index_reconciled",
    "regional_equity_price_return_pct_raw",
    "regional_equity_price_return_pct_reconciled",
    "regional_equity_valuation_pe_raw",
    "regional_equity_valuation_pe_reconciled",
    "regional_energy_cost_pressure_index_raw",
    "regional_energy_cost_pressure_index_reconciled",
    "regional_growth_regime",
    "regional_macro_regime",
    *REGIONAL_BRANCH_FIELDS,
    "gdp_level_scale_factor",
    "growth_reconciliation_adjustment_pp",
    "inflation_reconciliation_adjustment_pp",
    "core_inflation_reconciliation_adjustment_pp",
    "policy_reconciliation_adjustment_pp",
    "ten_year_reconciliation_adjustment_pp",
    "hy_reconciliation_adjustment_bps",
    "ig_reconciliation_adjustment_bps",
    "stress_reconciliation_adjustment_index",
    "equity_return_reconciliation_adjustment_pp",
    "equity_valuation_pe_reconciliation_adjustment",
    "energy_reconciliation_adjustment_index",
]


DIAGNOSTIC_FIELDS = [
    "reconciliation_param_version",
    "reconciliation_interface_version",
    "reconciliation_scope",
    "year_index",
    "year",
    "seed",
    "region_count",
    "regional_weight_config_sum",
    "regional_weight_normalized_sum",
    "global_gdp_anchor_trillion_usd",
    "weighted_regional_raw_gdp_trillion_usd",
    "weighted_regional_reconciled_gdp_trillion_usd",
    "raw_total_to_global_gap_pct",
    "gdp_level_scale_factor",
    "global_growth_anchor_pct",
    "weighted_regional_growth_raw_pct",
    "weighted_regional_growth_reconciled_pct",
    "growth_gap_raw_pp",
    "growth_gap_reconciled_pp",
    "global_headline_inflation_anchor_pct",
    "weighted_regional_headline_inflation_raw_pct",
    "weighted_regional_headline_inflation_reconciled_pct",
    "headline_inflation_gap_raw_pp",
    "headline_inflation_gap_reconciled_pp",
    "global_core_inflation_anchor_pct",
    "weighted_regional_core_inflation_raw_pct",
    "weighted_regional_core_inflation_reconciled_pct",
    "core_inflation_gap_raw_pp",
    "core_inflation_gap_reconciled_pp",
    "global_policy_rate_anchor_pct",
    "weighted_regional_policy_rate_raw_pct",
    "weighted_regional_policy_rate_reconciled_pct",
    "policy_rate_gap_raw_pp",
    "policy_rate_gap_reconciled_pp",
    "global_10y_anchor_pct",
    "weighted_regional_10y_raw_pct",
    "weighted_regional_10y_reconciled_pct",
    "ten_year_gap_raw_pp",
    "ten_year_gap_reconciled_pp",
    "global_hy_anchor_bps",
    "weighted_regional_hy_raw_bps",
    "weighted_regional_hy_reconciled_bps",
    "hy_gap_raw_bps",
    "hy_gap_reconciled_bps",
    "global_ig_anchor_bps",
    "weighted_regional_ig_raw_bps",
    "weighted_regional_ig_reconciled_bps",
    "ig_gap_raw_bps",
    "ig_gap_reconciled_bps",
    "global_financial_stress_anchor_index",
    "weighted_regional_macro_stress_raw_index",
    "weighted_regional_macro_stress_reconciled_index",
    "macro_stress_gap_raw_index",
    "macro_stress_gap_reconciled_index",
    "global_equity_return_anchor_pct",
    "weighted_regional_equity_return_raw_pct",
    "weighted_regional_equity_return_reconciled_pct",
    "equity_return_gap_raw_pp",
    "equity_return_gap_reconciled_pp",
    "global_equity_valuation_pe_anchor",
    "weighted_regional_equity_valuation_pe_raw",
    "weighted_regional_equity_valuation_pe_reconciled",
    "equity_valuation_pe_gap_raw",
    "equity_valuation_pe_gap_reconciled",
    "global_energy_cost_anchor_index",
    "weighted_regional_energy_cost_raw_index",
    "weighted_regional_energy_cost_reconciled_index",
    "energy_cost_gap_raw_index",
    "energy_cost_gap_reconciled_index",
    "headline_inflation_reconciliation_adjustment_pp",
    "core_inflation_reconciliation_adjustment_pp",
    "policy_rate_reconciliation_adjustment_pp",
    "ten_year_reconciliation_adjustment_pp",
    "hy_reconciliation_adjustment_bps",
    "ig_reconciliation_adjustment_bps",
    "stress_reconciliation_adjustment_index",
    "equity_return_reconciliation_adjustment_pp",
    "equity_valuation_pe_reconciliation_adjustment",
    "energy_reconciliation_adjustment_index",
    "headline_inflation_clamped_region_count",
    "core_inflation_clamped_region_count",
    "policy_rate_clamped_region_count",
    "ten_year_clamped_region_count",
    "hy_clamped_region_count",
    "ig_clamped_region_count",
    "macro_stress_clamped_region_count",
    "equity_return_clamped_region_count",
    "equity_valuation_pe_clamped_region_count",
    "energy_cost_clamped_region_count",
    "fields_with_clamped_regions",
    "total_field_clamps",
    "reconciliation_quality",
    "largest_region_id",
    "largest_region_share_pct",
    "top3_region_ids",
    "top3_share_pct",
]



def as_float(row: dict[str, Any], key: str, default: float = 0.0) -> float:
    try:
        value = row.get(key, default)
        if value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def read_csv(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_viewer_js(path: Path, regional_rows: list[dict[str, Any]], diagnostic_rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    regional_json = json.dumps(regional_rows, ensure_ascii=False, separators=(",", ":"))
    diagnostic_json = json.dumps(diagnostic_rows, ensure_ascii=False, separators=(",", ":"))
    path.write_text(
        "window.REGIONAL_MACRO_RECONCILED_DATA = "
        + regional_json
        + ";\nwindow.REGIONAL_MACRO_RECONCILIATION_DATA = "
        + diagnostic_json
        + ";\n",
        encoding="utf-8",
    )


def round_value(value: Any) -> Any:
    if isinstance(value, float):
        return round(value, 4)
    return value


def round_record(record: dict[str, Any]) -> dict[str, Any]:
    return {key: round_value(value) for key, value in record.items()}


def copy_branch_fields(row: dict[str, Any]) -> dict[str, Any]:
    copied: dict[str, Any] = {}
    for field in REGIONAL_BRANCH_FIELDS:
        if field in REGIONAL_BRANCH_TEXT_FIELDS:
            copied[field] = row.get(field, "none" if field != "regional_branch_transmission_active" else "false")
        elif field == "regional_branch_exposure_index":
            copied[field] = as_float(row, field, 1.0)
        else:
            copied[field] = as_float(row, field, 0.0)
    return copied


def key_for(row: dict[str, Any]) -> tuple[int, int]:
    return int(row["seed"]), int(row["year_index"])


def weighted_average(items: list[dict[str, Any]], key: str, share_key: str = "share_reconciled") -> float:
    return sum(item[share_key] * as_float(item["regional"], key) for item in items)


def quality_label(growth_gap: float, inflation_gap: float, hy_gap: float, stress_gap: float, level_gap: float) -> str:
    score = 0
    score += min(abs(growth_gap) / 0.35, 2.0)
    score += min(abs(inflation_gap) / 0.25, 2.0)
    score += min(abs(hy_gap) / 40.0, 2.0)
    score += min(abs(stress_gap) / 10.0, 2.0)
    score += min(abs(level_gap) / 1.0, 2.0)
    if score < 2.0:
        return "low_gap"
    if score < 4.0:
        return "medium_gap"
    return "high_gap"


def resolve_region_ids(args: argparse.Namespace) -> list[str]:
    if args.regions:
        region_ids = args.regions
    else:
        region_ids = REGION_ORDER
    missing = [region_id for region_id in region_ids if region_id not in REGION_CONFIGS]
    if missing:
        raise SystemExit(f"Unknown region ids: {', '.join(missing)}")
    return region_ids


def load_regional_rows(region_ids: list[str], regional_dir: Path) -> dict[str, list[dict[str, Any]]]:
    rows_by_region: dict[str, list[dict[str, Any]]] = {}
    for region_id in region_ids:
        path = regional_dir / f"{region_id}_regional_macro_seed_sweep.csv"
        if not path.exists():
            raise FileNotFoundError(f"Missing regional macro output: {path}")
        rows_by_region[region_id] = read_csv(path)
    return rows_by_region


def load_global_rows(global_csv: Path) -> dict[tuple[int, int], dict[str, Any]]:
    if not global_csv.exists():
        raise FileNotFoundError(f"Missing global macro output: {global_csv}")
    return {key_for(row): row for row in read_csv(global_csv)}


def build_reconciliation(
    region_ids: list[str],
    regional_rows: dict[str, list[dict[str, Any]]],
    global_rows: dict[tuple[int, int], dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    config_weights = {region_id: float(REGION_CONFIGS[region_id].global_weight) for region_id in region_ids}
    config_weight_sum = sum(config_weights.values())
    if config_weight_sum <= 0:
        raise ValueError("Regional config weights must sum to a positive value.")
    normalized_weights = {region_id: weight / config_weight_sum for region_id, weight in config_weights.items()}

    rows_by_key: dict[tuple[int, int], list[dict[str, Any]]] = defaultdict(list)
    for region_id in region_ids:
        for row in regional_rows[region_id]:
            rows_by_key[key_for(row)].append(row)

    if not rows_by_key:
        raise ValueError("No regional rows loaded.")

    regional_output: list[dict[str, Any]] = []
    diagnostic_output: list[dict[str, Any]] = []
    previous_reconciled_level: dict[tuple[int, str], float] = {}
    previous_reconciled_share: dict[tuple[int, str], float] = {}

    for seed, year_index in sorted(rows_by_key):
        rows = rows_by_key[(seed, year_index)]
        if len(rows) != len(region_ids):
            found = sorted(row["region_id"] for row in rows)
            raise ValueError(f"Expected {len(region_ids)} regions for seed={seed}, year_index={year_index}; found {found}")

        global_row = global_rows.get((seed, year_index))
        if not global_row:
            raise ValueError(f"Missing global anchor for seed={seed}, year_index={year_index}")

        initial_global = as_float(global_rows[(seed, 0)], "global_gdp_trillion_usd", 110.0)
        global_gdp = as_float(global_row, "global_gdp_trillion_usd", initial_global)
        global_growth = as_float(global_row, "realized_growth_pct")
        global_real_gdp_index = as_float(global_row, "real_gdp_index", 100.0)

        items: list[dict[str, Any]] = []
        for row in rows:
            region_id = row["region_id"]
            normalized_weight = normalized_weights[region_id]
            raw_gdp = initial_global * normalized_weight * as_float(row, "regional_gdp_index", 100.0) / 100.0
            items.append(
                {
                    "region_id": region_id,
                    "region_name": row["region_name"],
                    "regional": row,
                    "normalized_weight": normalized_weight,
                    "raw_gdp": raw_gdp,
                }
            )

        raw_total_gdp = sum(item["raw_gdp"] for item in items)
        level_scale = global_gdp / raw_total_gdp if raw_total_gdp > 0 else 1.0
        raw_total_gap_pct = (raw_total_gdp / global_gdp - 1.0) * 100.0 if global_gdp else 0.0

        for item in items:
            item["reconciled_gdp"] = item["raw_gdp"] * level_scale
            item["share_raw"] = item["raw_gdp"] / global_gdp if global_gdp else 0.0
            item["share_reconciled"] = item["reconciled_gdp"] / global_gdp if global_gdp else 0.0

        ranked = sorted(items, key=lambda item: item["reconciled_gdp"], reverse=True)
        rank_by_region = {item["region_id"]: rank + 1 for rank, item in enumerate(ranked)}

        weighted_growth_raw = 0.0
        weighted_growth_reconciled = 0.0
        for item in items:
            region_id = item["region_id"]
            raw_growth = as_float(item["regional"], "regional_gdp_growth_pct")
            prev_share = previous_reconciled_share.get((seed, region_id), item["normalized_weight"])
            prev_level = previous_reconciled_level.get((seed, region_id))
            if prev_level and prev_level > 0:
                reconciled_growth = (item["reconciled_gdp"] / prev_level - 1.0) * 100.0
            else:
                reconciled_growth = raw_growth
            item["raw_growth_contribution"] = prev_share * raw_growth
            item["reconciled_growth_contribution"] = prev_share * reconciled_growth
            item["reconciled_growth"] = reconciled_growth
            weighted_growth_raw += item["raw_growth_contribution"]
            weighted_growth_reconciled += item["reconciled_growth_contribution"]

        headline_raw = weighted_average(items, "regional_headline_inflation_pct")
        core_raw = weighted_average(items, "regional_core_inflation_pct")
        policy_raw = weighted_average(items, "regional_policy_rate_pct")
        ten_year_raw = weighted_average(items, "regional_10y_yield_pct")
        hy_raw = weighted_average(items, "regional_hy_spread_bps")
        ig_raw = weighted_average(items, "regional_ig_spread_bps")
        stress_raw = weighted_average(items, "regional_macro_stress_index")
        equity_raw = weighted_average(items, "regional_equity_price_return_pct")
        equity_pe_raw = weighted_average(items, "regional_equity_valuation_pe")
        energy_raw = weighted_average(items, "regional_energy_cost_pressure_index")

        headline_anchor = as_float(global_row, "headline_inflation_pct")
        core_anchor = as_float(global_row, "core_inflation_pct")
        policy_anchor = as_float(global_row, "global_policy_rate_pct")
        ten_year_anchor = as_float(global_row, "global_10y_yield_pct")
        hy_anchor = as_float(global_row, "global_high_yield_spread_bps")
        ig_anchor = as_float(global_row, "global_investment_grade_spread_bps")
        stress_anchor = as_float(global_row, "financial_stress_index")
        equity_anchor = as_float(global_row, "global_equity_price_return_pct")
        equity_pe_anchor = as_float(global_row, "global_equity_valuation_pe", equity_pe_raw)
        energy_anchor = as_float(global_row, "energy_cost_pressure_index")

        headline_adjustment = clamp((headline_anchor - headline_raw) * 0.72, -0.45, 0.45)
        core_adjustment = clamp((core_anchor - core_raw) * 0.68, -0.35, 0.35)
        policy_adjustment = clamp((policy_anchor - policy_raw) * 0.62, -0.35, 0.35)
        ten_year_adjustment = clamp((ten_year_anchor - ten_year_raw) * 0.62, -0.45, 0.45)
        hy_adjustment = clamp((hy_anchor - hy_raw) * 0.58, -75.0, 75.0)
        ig_adjustment = clamp((ig_anchor - ig_raw) * 0.58, -25.0, 25.0)
        stress_adjustment = clamp((stress_anchor - stress_raw) * 0.58, -30.0, 30.0)
        # A2 uses diagnostic-only soft reconciliation. Do not force regional
        # price returns or PE toward the global aggregate.
        equity_adjustment = 0.0
        equity_pe_adjustment = 0.0
        energy_adjustment = clamp((energy_anchor - energy_raw) * 0.58, -8.0, 8.0)

        # Apply the soft reconciliation adjustment per region, then re-clamp each
        # region's reconciled value to its published field boundary. The clamped
        # per-region values are what downstream models and the Viewer read, and they
        # are what the weighted reconciled aggregates are computed from. Counting
        # how many regions were clipped gives a transparent diagnostic without
        # chasing zero residual by forcing every region onto the same boundary.
        reconciled_clamp_counts: dict[str, int] = {}

        def reconcile_field(field: str, adjustment: float) -> float:
            """Per-region clamp-then-weight; returns the weighted reconciled aggregate.

            Also stashes each region's clamped reconciled value on its item under
            ``f"{field}_reconciled_clamped"`` so the regional output rows can reuse
            the exact value the diagnostic was computed from, and records the count
            of regions whose value had to be clipped back inside the boundary.
            """
            clamp_count = 0
            weighted_total = 0.0
            for item in items:
                region_id = item["region_id"]
                raw_value = as_float(item["regional"], field)
                adjusted = raw_value + adjustment
                clamped = clamp_reconciled_value(region_id, field, adjusted)
                if clamped != adjusted:
                    clamp_count += 1
                item[f"{field}_reconciled_clamped"] = clamped
                weighted_total += item["share_reconciled"] * clamped
            reconciled_clamp_counts[field] = clamp_count
            return weighted_total

        headline_reconciled = reconcile_field("regional_headline_inflation_pct", headline_adjustment)
        core_reconciled = reconcile_field("regional_core_inflation_pct", core_adjustment)
        policy_reconciled = reconcile_field("regional_policy_rate_pct", policy_adjustment)
        ten_year_reconciled = reconcile_field("regional_10y_yield_pct", ten_year_adjustment)
        hy_reconciled = reconcile_field("regional_hy_spread_bps", hy_adjustment)
        ig_reconciled = reconcile_field("regional_ig_spread_bps", ig_adjustment)
        stress_reconciled = reconcile_field("regional_macro_stress_index", stress_adjustment)
        equity_reconciled = reconcile_field("regional_equity_price_return_pct", equity_adjustment)
        equity_pe_reconciled = reconcile_field("regional_equity_valuation_pe", equity_pe_adjustment)
        energy_reconciled = reconcile_field("regional_energy_cost_pressure_index", energy_adjustment)

        regions_clamped_by_field = sum(
            1 for count in reconciled_clamp_counts.values() if count > 0
        )
        total_field_clamps = sum(reconciled_clamp_counts.values())

        quality = quality_label(
            weighted_growth_reconciled - global_growth,
            headline_reconciled - headline_anchor,
            hy_reconciled - hy_anchor,
            stress_reconciled - stress_anchor,
            raw_total_gap_pct,
        )
        top3 = ranked[:3]

        diagnostic_output.append(
            round_record(
                {
                    "reconciliation_param_version": RECONCILIATION_PARAM_VERSION,
                    "reconciliation_interface_version": RECONCILIATION_INTERFACE_VERSION,
                    "reconciliation_scope": "weighted_14_region_soft_reconciliation",
                    "year_index": year_index,
                    "year": int(global_row["year"]),
                    "seed": seed,
                    "region_count": len(region_ids),
                    "regional_weight_config_sum": config_weight_sum,
                    "regional_weight_normalized_sum": sum(normalized_weights.values()),
                    "global_gdp_anchor_trillion_usd": global_gdp,
                    "weighted_regional_raw_gdp_trillion_usd": raw_total_gdp,
                    "weighted_regional_reconciled_gdp_trillion_usd": global_gdp,
                    "raw_total_to_global_gap_pct": raw_total_gap_pct,
                    "gdp_level_scale_factor": level_scale,
                    "global_growth_anchor_pct": global_growth,
                    "weighted_regional_growth_raw_pct": weighted_growth_raw,
                    "weighted_regional_growth_reconciled_pct": weighted_growth_reconciled,
                    "growth_gap_raw_pp": weighted_growth_raw - global_growth,
                    "growth_gap_reconciled_pp": weighted_growth_reconciled - global_growth,
                    "global_headline_inflation_anchor_pct": headline_anchor,
                    "weighted_regional_headline_inflation_raw_pct": headline_raw,
                    "weighted_regional_headline_inflation_reconciled_pct": headline_reconciled,
                    "headline_inflation_gap_raw_pp": headline_raw - headline_anchor,
                    "headline_inflation_gap_reconciled_pp": headline_reconciled - headline_anchor,
                    "global_core_inflation_anchor_pct": core_anchor,
                    "weighted_regional_core_inflation_raw_pct": core_raw,
                    "weighted_regional_core_inflation_reconciled_pct": core_reconciled,
                    "core_inflation_gap_raw_pp": core_raw - core_anchor,
                    "core_inflation_gap_reconciled_pp": core_reconciled - core_anchor,
                    "global_policy_rate_anchor_pct": policy_anchor,
                    "weighted_regional_policy_rate_raw_pct": policy_raw,
                    "weighted_regional_policy_rate_reconciled_pct": policy_reconciled,
                    "policy_rate_gap_raw_pp": policy_raw - policy_anchor,
                    "policy_rate_gap_reconciled_pp": policy_reconciled - policy_anchor,
                    "global_10y_anchor_pct": ten_year_anchor,
                    "weighted_regional_10y_raw_pct": ten_year_raw,
                    "weighted_regional_10y_reconciled_pct": ten_year_reconciled,
                    "ten_year_gap_raw_pp": ten_year_raw - ten_year_anchor,
                    "ten_year_gap_reconciled_pp": ten_year_reconciled - ten_year_anchor,
                    "global_hy_anchor_bps": hy_anchor,
                    "weighted_regional_hy_raw_bps": hy_raw,
                    "weighted_regional_hy_reconciled_bps": hy_reconciled,
                    "hy_gap_raw_bps": hy_raw - hy_anchor,
                    "hy_gap_reconciled_bps": hy_reconciled - hy_anchor,
                    "global_ig_anchor_bps": ig_anchor,
                    "weighted_regional_ig_raw_bps": ig_raw,
                    "weighted_regional_ig_reconciled_bps": ig_reconciled,
                    "ig_gap_raw_bps": ig_raw - ig_anchor,
                    "ig_gap_reconciled_bps": ig_reconciled - ig_anchor,
                    "global_financial_stress_anchor_index": stress_anchor,
                    "weighted_regional_macro_stress_raw_index": stress_raw,
                    "weighted_regional_macro_stress_reconciled_index": stress_reconciled,
                    "macro_stress_gap_raw_index": stress_raw - stress_anchor,
                    "macro_stress_gap_reconciled_index": stress_reconciled - stress_anchor,
                    "global_equity_return_anchor_pct": equity_anchor,
                    "weighted_regional_equity_return_raw_pct": equity_raw,
                    "weighted_regional_equity_return_reconciled_pct": equity_reconciled,
                    "equity_return_gap_raw_pp": equity_raw - equity_anchor,
                    "equity_return_gap_reconciled_pp": equity_reconciled - equity_anchor,
                    "global_equity_valuation_pe_anchor": equity_pe_anchor,
                    "weighted_regional_equity_valuation_pe_raw": equity_pe_raw,
                    "weighted_regional_equity_valuation_pe_reconciled": equity_pe_reconciled,
                    "equity_valuation_pe_gap_raw": equity_pe_raw - equity_pe_anchor,
                    "equity_valuation_pe_gap_reconciled": equity_pe_reconciled - equity_pe_anchor,
                    "global_energy_cost_anchor_index": energy_anchor,
                    "weighted_regional_energy_cost_raw_index": energy_raw,
                    "weighted_regional_energy_cost_reconciled_index": energy_reconciled,
                    "energy_cost_gap_raw_index": energy_raw - energy_anchor,
                    "energy_cost_gap_reconciled_index": energy_reconciled - energy_anchor,
                    "headline_inflation_reconciliation_adjustment_pp": headline_adjustment,
                    "core_inflation_reconciliation_adjustment_pp": core_adjustment,
                    "policy_rate_reconciliation_adjustment_pp": policy_adjustment,
                    "ten_year_reconciliation_adjustment_pp": ten_year_adjustment,
                    "hy_reconciliation_adjustment_bps": hy_adjustment,
                    "ig_reconciliation_adjustment_bps": ig_adjustment,
                    "stress_reconciliation_adjustment_index": stress_adjustment,
                    "equity_return_reconciliation_adjustment_pp": equity_adjustment,
                    "equity_valuation_pe_reconciliation_adjustment": equity_pe_adjustment,
                    "energy_reconciliation_adjustment_index": energy_adjustment,
                    "headline_inflation_clamped_region_count": reconciled_clamp_counts["regional_headline_inflation_pct"],
                    "core_inflation_clamped_region_count": reconciled_clamp_counts["regional_core_inflation_pct"],
                    "policy_rate_clamped_region_count": reconciled_clamp_counts["regional_policy_rate_pct"],
                    "ten_year_clamped_region_count": reconciled_clamp_counts["regional_10y_yield_pct"],
                    "hy_clamped_region_count": reconciled_clamp_counts["regional_hy_spread_bps"],
                    "ig_clamped_region_count": reconciled_clamp_counts["regional_ig_spread_bps"],
                    "macro_stress_clamped_region_count": reconciled_clamp_counts["regional_macro_stress_index"],
                    "equity_return_clamped_region_count": reconciled_clamp_counts["regional_equity_price_return_pct"],
                    "equity_valuation_pe_clamped_region_count": reconciled_clamp_counts["regional_equity_valuation_pe"],
                    "energy_cost_clamped_region_count": reconciled_clamp_counts["regional_energy_cost_pressure_index"],
                    "fields_with_clamped_regions": regions_clamped_by_field,
                    "total_field_clamps": total_field_clamps,
                    "reconciliation_quality": quality,
                    "largest_region_id": ranked[0]["region_id"],
                    "largest_region_share_pct": ranked[0]["share_reconciled"] * 100.0,
                    "top3_region_ids": "|".join(item["region_id"] for item in top3),
                    "top3_share_pct": sum(item["share_reconciled"] for item in top3) * 100.0,
                }
            )
        )

        for item in items:
            row = item["regional"]
            region_id = item["region_id"]
            normalized_weight_pct = item["normalized_weight"] * 100.0
            share_reconciled_pct = item["share_reconciled"] * 100.0
            share_raw_pct = item["share_raw"] * 100.0
            share_change = (share_reconciled_pct / normalized_weight_pct - 1.0) * 100.0 if normalized_weight_pct else 0.0
            regional_output.append(
                round_record(
                    {
                        "reconciliation_param_version": RECONCILIATION_PARAM_VERSION,
                        "reconciliation_interface_version": RECONCILIATION_INTERFACE_VERSION,
                        "reconciliation_scope": "weighted_14_region_soft_reconciliation",
                        "year_index": year_index,
                        "year": int(row["year"]),
                        "seed": seed,
                        "region_id": region_id,
                        "region_name": item["region_name"],
                        "regional_global_weight_config": config_weights[region_id],
                        "regional_normalized_initial_weight": item["normalized_weight"],
                        "regional_normalized_initial_weight_pct": normalized_weight_pct,
                        "regional_structural_seed_version": row.get("regional_structural_seed_version", "none"),
                        "regional_seed_potential_enabled": as_float(row, "regional_seed_potential_enabled"),
                        "regional_seed_potential_template_id": row.get("regional_seed_potential_template_id", "none"),
                        "regional_seed_primary_theme": row.get("regional_seed_primary_theme", "none"),
                        "regional_seed_secondary_theme": row.get("regional_seed_secondary_theme", "none"),
                        "regional_seed_structural_score": as_float(row, "regional_seed_structural_score"),
                        "regional_seed_momentum_label": row.get("regional_seed_momentum_label", "none"),
                        "regional_seed_effective_growth_bias_pct": as_float(row, "regional_seed_effective_growth_bias_pct"),
                        "regional_seed_aviation_propensity_bias_pct": as_float(row, "regional_seed_aviation_propensity_bias_pct"),
                        "regional_seed_investment_cycle_bias_pct": as_float(row, "regional_seed_investment_cycle_bias_pct"),
                        "regional_seed_openness_bias_pct": as_float(row, "regional_seed_openness_bias_pct"),
                        "regional_seed_demand_multiplier": as_float(row, "regional_seed_demand_multiplier", 1.0),
                        "global_gdp_anchor_trillion_usd": global_gdp,
                        "global_growth_anchor_pct": global_growth,
                        "global_real_gdp_index": global_real_gdp_index,
                        "regional_gdp_index": as_float(row, "regional_gdp_index", 100.0),
                        "regional_gdp_growth_pct_raw": as_float(row, "regional_gdp_growth_pct"),
                        "regional_gdp_growth_pct_reconciled": item["reconciled_growth"],
                        "regional_potential_growth_pct": as_float(row, "regional_potential_growth_pct"),
                        "regional_output_gap_pct": as_float(row, "regional_output_gap_pct"),
                        "regional_raw_gdp_trillion_usd": item["raw_gdp"],
                        "regional_reconciled_gdp_trillion_usd": item["reconciled_gdp"],
                        "regional_raw_share_of_global_gdp_pct": share_raw_pct,
                        "regional_reconciled_share_of_global_gdp_pct": share_reconciled_pct,
                        "regional_share_change_from_start_pct": share_change,
                        "regional_weight_drift_pp": share_reconciled_pct - normalized_weight_pct,
                        "regional_rank_by_gdp": rank_by_region[region_id],
                        "regional_growth_contribution_pp_raw": item["raw_growth_contribution"],
                        "regional_growth_contribution_pp_reconciled": item["reconciled_growth_contribution"],
                        "regional_headline_inflation_pct_raw": as_float(row, "regional_headline_inflation_pct"),
                        "regional_headline_inflation_pct_reconciled": item["regional_headline_inflation_pct_reconciled_clamped"],
                        "regional_core_inflation_pct_raw": as_float(row, "regional_core_inflation_pct"),
                        "regional_core_inflation_pct_reconciled": item["regional_core_inflation_pct_reconciled_clamped"],
                        "regional_policy_rate_pct_raw": as_float(row, "regional_policy_rate_pct"),
                        "regional_policy_rate_pct_reconciled": item["regional_policy_rate_pct_reconciled_clamped"],
                        "regional_10y_yield_pct_raw": as_float(row, "regional_10y_yield_pct"),
                        "regional_10y_yield_pct_reconciled": item["regional_10y_yield_pct_reconciled_clamped"],
                        "regional_hy_spread_bps_raw": as_float(row, "regional_hy_spread_bps"),
                        "regional_hy_spread_bps_reconciled": item["regional_hy_spread_bps_reconciled_clamped"],
                        "regional_ig_spread_bps_raw": as_float(row, "regional_ig_spread_bps"),
                        "regional_ig_spread_bps_reconciled": item["regional_ig_spread_bps_reconciled_clamped"],
                        "regional_macro_stress_index_raw": as_float(row, "regional_macro_stress_index"),
                        "regional_macro_stress_index_reconciled": item["regional_macro_stress_index_reconciled_clamped"],
                        "regional_equity_price_return_pct_raw": as_float(row, "regional_equity_price_return_pct"),
                        "regional_equity_price_return_pct_reconciled": item["regional_equity_price_return_pct_reconciled_clamped"],
                        "regional_equity_valuation_pe_raw": as_float(row, "regional_equity_valuation_pe"),
                        "regional_equity_valuation_pe_reconciled": item["regional_equity_valuation_pe_reconciled_clamped"],
                        "regional_energy_cost_pressure_index_raw": as_float(row, "regional_energy_cost_pressure_index"),
                        "regional_energy_cost_pressure_index_reconciled": item["regional_energy_cost_pressure_index_reconciled_clamped"],
                        "regional_growth_regime": row.get("regional_growth_regime", ""),
                        "regional_macro_regime": row.get("regional_macro_regime", ""),
                        **copy_branch_fields(row),
                        "gdp_level_scale_factor": level_scale,
                        "growth_reconciliation_adjustment_pp": item["reconciled_growth"] - as_float(row, "regional_gdp_growth_pct"),
                        "inflation_reconciliation_adjustment_pp": headline_adjustment,
                        "core_inflation_reconciliation_adjustment_pp": core_adjustment,
                        "policy_reconciliation_adjustment_pp": policy_adjustment,
                        "ten_year_reconciliation_adjustment_pp": ten_year_adjustment,
                        "hy_reconciliation_adjustment_bps": hy_adjustment,
                        "ig_reconciliation_adjustment_bps": ig_adjustment,
                        "stress_reconciliation_adjustment_index": stress_adjustment,
                        "equity_return_reconciliation_adjustment_pp": equity_adjustment,
                        "equity_valuation_pe_reconciliation_adjustment": equity_pe_adjustment,
                        "energy_reconciliation_adjustment_index": energy_adjustment,
                    }
                )
            )
            previous_reconciled_level[(seed, region_id)] = item["reconciled_gdp"]
            previous_reconciled_share[(seed, region_id)] = item["share_reconciled"]

    summaries = []
    for seed in sorted({int(row["seed"]) for row in diagnostic_output}):
        seed_diags = [row for row in diagnostic_output if int(row["seed"]) == seed]
        final_diag = max(seed_diags, key=lambda row: int(row["year_index"]))
        summaries.append(
            round_record(
                {
                    "seed": seed,
                    "avg_abs_growth_gap_reconciled_pp": mean(abs(as_float(row, "growth_gap_reconciled_pp")) for row in seed_diags),
                    "avg_abs_inflation_gap_reconciled_pp": mean(abs(as_float(row, "headline_inflation_gap_reconciled_pp")) for row in seed_diags),
                    "avg_abs_hy_gap_reconciled_bps": mean(abs(as_float(row, "hy_gap_reconciled_bps")) for row in seed_diags),
                    "final_largest_region_id": final_diag["largest_region_id"],
                    "final_largest_region_share_pct": as_float(final_diag, "largest_region_share_pct"),
                    "final_top3_region_ids": final_diag["top3_region_ids"],
                    "final_top3_share_pct": as_float(final_diag, "top3_share_pct"),
                    "final_quality": final_diag["reconciliation_quality"],
                }
            )
        )

    return regional_output, diagnostic_output, summaries


def parse_args() -> argparse.Namespace:
    airport_dir = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Reconcile 14 regional macro paths and compute GDP levels.")
    parser.add_argument("--regional-dir", type=Path, default=airport_dir / "output" / "regional_macro")
    parser.add_argument("--global-csv", type=Path, default=airport_dir / "output" / "global_macro" / "global_macro_feedback_seed_sweep.csv")
    parser.add_argument("--output-dir", type=Path, default=airport_dir / "output" / "regional_macro_reconciled")
    parser.add_argument("--regions", nargs="*", default=None, help="Optional region ids; default uses the 14-region roadmap order.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    region_ids = resolve_region_ids(args)
    regional_rows = load_regional_rows(region_ids, args.regional_dir)
    global_rows = load_global_rows(args.global_csv)
    regional_output, diagnostic_output, summaries = build_reconciliation(region_ids, regional_rows, global_rows)

    regional_csv = args.output_dir / "regional_macro_reconciled_seed_sweep.csv"
    diagnostic_csv = args.output_dir / "regional_macro_reconciliation_seed_sweep.csv"
    regional_json = args.output_dir / "regional_macro_reconciled_seed_sweep.json"
    diagnostic_json = args.output_dir / "regional_macro_reconciliation_seed_sweep.json"
    viewer_js = args.output_dir / "regional_macro_reconciled_viewer_data.js"

    write_csv(regional_csv, regional_output, REGIONAL_VALUE_FIELDS)
    write_csv(diagnostic_csv, diagnostic_output, DIAGNOSTIC_FIELDS)
    write_json(
        regional_json,
        {
            "reconciliation_param_version": RECONCILIATION_PARAM_VERSION,
            "reconciliation_interface_version": RECONCILIATION_INTERFACE_VERSION,
            "reconciliation_scope": "weighted_14_region_soft_reconciliation",
            "region_ids": region_ids,
            "region_count": len(region_ids),
            "rows": len(regional_output),
            "diagnostic_rows": len(diagnostic_output),
            "outputs": {
                "regional_csv": str(regional_csv),
                "diagnostic_csv": str(diagnostic_csv),
                "regional_json": str(regional_json),
                "diagnostic_json": str(diagnostic_json),
                "viewer_data_js": str(viewer_js),
            },
            "summaries": summaries,
        },
    )
    write_json(
        diagnostic_json,
        {
            "reconciliation_param_version": RECONCILIATION_PARAM_VERSION,
            "reconciliation_interface_version": RECONCILIATION_INTERFACE_VERSION,
            "reconciliation_scope": "weighted_14_region_soft_reconciliation",
            "region_ids": region_ids,
            "region_count": len(region_ids),
            "rows": len(diagnostic_output),
            "summaries": summaries,
        },
    )
    write_viewer_js(viewer_js, regional_output, diagnostic_output)

    print(f"Wrote {regional_csv}")
    print(f"Wrote {diagnostic_csv}")
    print(f"Wrote {regional_json}")
    print(f"Wrote {diagnostic_json}")
    print(f"Wrote {viewer_js}")
    for summary in summaries:
        print(
            "Seed {seed}: avg growth gap {growth:.3f}pp, avg inflation gap {inflation:.3f}pp, "
            "avg HY gap {hy:.1f}bps, final largest {largest} {share:.2f}%".format(
                seed=summary["seed"],
                growth=summary["avg_abs_growth_gap_reconciled_pp"],
                inflation=summary["avg_abs_inflation_gap_reconciled_pp"],
                hy=summary["avg_abs_hy_gap_reconciled_bps"],
                largest=summary["final_largest_region_id"],
                share=summary["final_largest_region_share_pct"],
            )
        )


if __name__ == "__main__":
    main()
