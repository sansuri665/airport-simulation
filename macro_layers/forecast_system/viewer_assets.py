from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .scoring import COMPONENTS


FORECAST_VIEWER_LAZY_INDEX_VERSION = "airport-forecast-viewer-lazy-index-v2"
FORECAST_VIEWER_CHUNK_VERSION = "airport-forecast-viewer-report-chunk-v2"

VIEWER_REPORT_METADATA_FIELDS = (
    "forecast_report_id",
    "forecast_report_display_name",
    "forecast_report_tier",
    "forecast_report_tier_profile_id",
    "forecast_report_source",
    "forecast_narrative_profile_id",
    "forecast_narrative_modifier_ids",
    "narrative_style_label",
    "narrative_style_summary",
    "narrative_style_method",
    "narrative_style_blind_spot",
    "forecast_narrative_modifier_labels",
    "forecast_narrative_modifier_groups",
    "forecast_narrative_modifier_descriptions",
    "forecast_narrative_modifier_tradeoffs",
    "reported_confidence_style",
    "forecast_horizon_min_years",
    "forecast_horizon_max_years",
    "forecast_horizon_step_years",
    "future_peek_mode",
)


def forecast_viewer_config(
    config: dict[str, Any],
    *,
    include_audit: bool = False,
) -> dict[str, Any]:
    reports = []
    for report in config.get("forecast_reports", []):
        if bool(report.get("future_peek_mode", False)) and not include_audit:
            continue
        reports.append(
            {
                key: report[key]
                for key in VIEWER_REPORT_METADATA_FIELDS
                if key in report
            }
        )
    return {
        "config_version": config.get("config_version"),
        "forecast_model_version": (
            config.get("forecast_model_version")
            or config.get("forecast", {}).get("forecast_model_version")
        ),
        "city_airport_market_id": config.get("city_airport_market_id"),
        "city_name": config.get("city_name"),
        "region_id": config.get("region_id"),
        "forecast_reports": reports,
    }


PLAYER_FORECAST_FIELDS = {
    "city_airport_potential_passenger_forecast_param_version",
    "city_airport_potential_passenger_forecast_interface_version",
    "forecast_config_version",
    "forecast_model_version",
    "city_airport_market_id",
    "city_name",
    "region_id",
    "seed",
    "as_of_year",
    "as_of_quarter",
    "data_cutoff_year",
    "data_cutoff_quarter",
    "forecast_report_id",
    "forecast_report_tier",
    "forecast_report_tier_profile_id",
    "forecast_report_source",
    "forecast_narrative_profile_id",
    "forecast_narrative_modifier_ids",
    "forecast_narrative_style_label",
    "forecast_narrative_style_summary",
    "forecast_narrative_style_method",
    "forecast_narrative_style_blind_spot",
    "forecast_narrative_modifier_labels",
    "forecast_narrative_modifier_groups",
    "forecast_narrative_modifier_descriptions",
    "forecast_narrative_modifier_tradeoffs",
    "forecast_narrative_headline",
    "forecast_primary_driver",
    "forecast_secondary_driver",
    "forecast_expected_regime",
    "forecast_turn_window_start_year",
    "forecast_turn_window_end_year",
    "forecast_conviction_pct",
    "forecast_revision_reason",
    "forecast_revision_pct",
    "forecast_component_revision_pp",
    "forecast_previous_mid_million",
    "forecast_signal_demand_direction",
    "forecast_signal_supply_direction",
    "forecast_signal_turn_direction",
    "forecast_signal_confidence_pct",
    "reported_confidence_style",
    "future_peek_mode",
    "forecast_year",
    "forecast_horizon_years",
    "current_effective_passengers_million",
    "current_potential_passengers_million",
    "current_airline_supply_passengers_million",
    "current_airline_serviceable_supply_million",
    "current_market_bottleneck",
    "naive_public_curve_effective_million",
    "forecast_effective_passengers_mid_million",
    "forecast_effective_passengers_low_million",
    "forecast_effective_passengers_high_million",
    "forecast_potential_passengers_mid_million",
    "forecast_airline_supply_passengers_mid_million",
    "forecast_airline_serviceable_supply_mid_million",
    "forecast_airline_unused_capacity_mid_million",
    "forecast_market_bottleneck",
    "forecast_downside_band_pct",
    "forecast_upside_band_pct",
    "forecast_error_band_pct",
    "forecast_confidence_pct",
    "market_consensus_gap_pct",
    "forecast_momentum_label",
    "forecast_long_term_tier_label",
    "forecast_reliability_label",
    "forecast_main_upside_factors",
    "forecast_main_downside_factors",
    "forecast_method_note",
}
for _component in COMPONENTS:
    PLAYER_FORECAST_FIELDS.update(
        {
            f"{_component}_forecast_effective_passengers_mid_million",
            f"{_component}_forecast_effective_passengers_low_million",
            f"{_component}_forecast_effective_passengers_high_million",
            f"{_component}_forecast_effective_share_band_pp",
            f"{_component}_forecast_potential_passengers_mid_million",
            f"{_component}_forecast_potential_share_pct",
            f"{_component}_forecast_airline_priority_weight",
            f"{_component}_forecast_airline_offered_capacity_million",
            f"{_component}_forecast_airline_supply_passengers_mid_million",
            f"{_component}_forecast_airline_supply_share_pct",
            f"{_component}_forecast_airline_supply_fulfillment_pct",
            f"{_component}_forecast_airline_supply_gap_million",
            f"{_component}_forecast_effective_share_pct",
            f"current_{_component}_potential_passengers_million",
            f"current_{_component}_airline_supply_passengers_million",
            f"current_{_component}_effective_passengers_million",
        }
    )


# Audit chunks deliberately extend the player contract.  They do not inherit
# every CSV column: deprecated lagged-curve fields remain CSV compatibility
# columns and can no longer leak into browser payloads.
AUDIT_FORECAST_FIELDS = PLAYER_FORECAST_FIELDS | {
    "region_name",
    "as_of_year_index",
    "forecast_year_index",
    "naive_public_curve_potential_million",
    "naive_public_curve_airline_supply_million",
    "configured_forecast_quality_score",
    "forecast_quality_score",
    "realized_score_method_version",
    "realized_report_quality_score",
    "realized_result_quality_score",
    "realized_report_process_quality_score",
    "realized_total_result_quality_score",
    "realized_component_result_quality_score",
    "realized_point_quality_score",
    "realized_midpoint_accuracy_score",
    "realized_trend_accuracy_score",
    "realized_shape_accuracy_score",
    "realized_component_structure_score",
    "realized_component_potential_structure_score",
    "realized_component_supply_structure_score",
    "realized_component_fulfillment_score",
    "realized_component_interval_calibration_score",
    "realized_bottleneck_accuracy_score",
    "realized_interval_calibration_score",
    "realized_turn_timing_score",
    "realized_revision_discipline_score",
    "realized_total_revision_discipline_score",
    "realized_component_revision_discipline_score",
    "realized_report_weighted_abs_error_pct",
    "realized_report_interval_hit_rate_pct",
    "realized_report_bias_pct",
    "realized_report_bias_label",
    "calibration_score",
    "seed_signal_capture_pct",
    "deterministic_forecast_bias_pct",
    "public_consensus_anchor_pct",
    "consensus_herding_bias_pct",
    "source_seed_city_momentum_label",
    "source_seed_city_potential_multiplier",
    "debug_hidden_true_effective_passengers_million",
    "debug_hidden_true_potential_passengers_million",
    "debug_hidden_true_airline_supply_passengers_million",
    "debug_hidden_true_market_bottleneck",
    "debug_hidden_true_inside_forecast_range",
    "debug_hidden_true_position_pct",
    "debug_model_gap_to_true_pct",
    "debug_hidden_signal_demand_direction",
    "debug_hidden_signal_supply_direction",
    "debug_hidden_signal_turn_year",
    "debug_hidden_signal_turn_direction",
}
for _component in COMPONENTS:
    AUDIT_FORECAST_FIELDS.update(
        {
            f"{_component}_debug_hidden_true_effective_passengers_million",
            f"{_component}_debug_hidden_true_effective_share_pct",
            f"{_component}_debug_hidden_true_potential_passengers_million",
            f"{_component}_debug_hidden_true_potential_share_pct",
            f"{_component}_debug_hidden_true_airline_supply_passengers_million",
            f"{_component}_debug_hidden_true_airline_offered_capacity_million",
            f"{_component}_debug_hidden_true_airline_supply_share_pct",
            f"{_component}_debug_hidden_true_airline_supply_fulfillment_pct",
            f"{_component}_debug_hidden_true_airline_supply_gap_million",
            f"{_component}_debug_hidden_true_inside_forecast_range",
            f"debug_hidden_signal_{_component}_demand_direction",
            f"debug_hidden_signal_{_component}_supply_direction",
        }
    )


def forecast_player_row(row: dict[str, Any]) -> dict[str, Any] | None:
    if str(row.get("future_peek_mode")).lower() == "true":
        return None
    return {key: value for key, value in row.items() if key in PLAYER_FORECAST_FIELDS}


def forecast_audit_row(row: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in row.items() if key in AUDIT_FORECAST_FIELDS}


def safe_report_filename(report_id: str) -> str:
    clean = "".join(
        char if char.isalnum() or char in ("-", "_") else "_"
        for char in report_id
    )
    return clean.strip("_") or "forecast_report"


FORECAST_VIEWER_NULL_FIELDS = frozenset(
    {
        "forecast_previous_mid_million",
        "forecast_turn_window_start_year",
        "forecast_turn_window_end_year",
        "debug_hidden_signal_turn_year",
    }
)


def _chunk_payload(
    *,
    data_mode: str,
    report_id: str,
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "schemaVersion": FORECAST_VIEWER_CHUNK_VERSION,
        "dataMode": data_mode,
        "reportId": report_id,
        "rowCount": len(rows),
        "rows": rows,
    }


def _encode_chunk(payload: dict[str, Any]) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")


def serialize_viewer_report(
    rows: list[dict[str, Any]],
    report_id: str,
    *,
    data_mode: str,
) -> dict[str, Any]:
    """Project one immutable player or audit report without writing files."""

    clean_report_id = str(report_id or "").strip()
    if not clean_report_id:
        raise ValueError("forecast report id is required")
    if data_mode not in {"player", "audit"}:
        raise ValueError(f"unsupported forecast Viewer data mode: {data_mode}")
    report_rows = [
        row
        for row in rows
        if str(row.get("forecast_report_id") or "").strip() == clean_report_id
    ]
    if data_mode == "player":
        projected_rows = [
            projected
            for row in report_rows
            if (projected := forecast_player_row(row)) is not None
        ]
    else:
        projected_rows = [forecast_audit_row(row) for row in report_rows]
    filename = f"r_{safe_report_filename(clean_report_id)}.json"
    payload = _chunk_payload(
        data_mode=data_mode,
        report_id=clean_report_id,
        rows=projected_rows,
    )
    raw = _encode_chunk(payload)
    return {
        "reportId": clean_report_id,
        "filename": filename,
        "chunkPayload": payload,
        "raw": raw,
        "reportMeta": {
            "reportId": clean_report_id,
            "rowCount": len(projected_rows),
            "file": filename,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw),
        },
    }


def _ordered_report_ids(
    rows: list[dict[str, Any]],
    config: dict[str, Any],
) -> list[str]:
    configured_ids = [
        str(item.get("forecast_report_id") or "").strip()
        for item in config.get("forecast_reports", [])
        if str(item.get("forecast_report_id") or "").strip()
    ]
    row_ids = {str(row.get("forecast_report_id") or "").strip() for row in rows}
    report_ids = [report_id for report_id in configured_ids if report_id in row_ids]
    report_ids.extend(
        sorted(
            report_id
            for report_id in row_ids
            if report_id and report_id not in report_ids
        )
    )
    return report_ids


def _viewer_index(
    *,
    data_mode: str,
    config: dict[str, Any],
    reports: list[dict[str, Any]],
    seeds: list[int],
    default_report_id: str,
    chunk_dir_name: str,
    audit_index_filename: str,
) -> dict[str, Any]:
    index = {
        "schemaVersion": FORECAST_VIEWER_LAZY_INDEX_VERSION,
        "chunkSchemaVersion": FORECAST_VIEWER_CHUNK_VERSION,
        "dataMode": data_mode,
        "config": forecast_viewer_config(config, include_audit=data_mode == "audit"),
        "totalRows": sum(int(report["rowCount"]) for report in reports),
        "seeds": seeds,
        "defaultReportId": default_report_id,
        "chunkBase": f"./{chunk_dir_name}/",
        "reports": reports,
    }
    if data_mode == "player":
        index["auditIndexFile"] = audit_index_filename
    return index


def _index_dataset(
    rows: list[dict[str, Any]],
    config: dict[str, Any],
    *,
    player_reports: list[dict[str, Any]],
    audit_reports: list[dict[str, Any]],
) -> dict[str, Any]:
    market_id = str(config.get("city_airport_market_id") or "city_airport_market")
    audit_index_filename = f"{market_id}_forecast_audit_index.js"
    chunk_dir_name = f"{market_id}_forecast_chunks"
    audit_chunk_dir_name = f"{market_id}_audit_forecast_chunks"
    seeds = sorted({int(float(row.get("seed", 0))) for row in rows})
    player_report_ids = [item["reportId"] for item in player_reports]
    default_report_id = (
        "public_consensus"
        if "public_consensus" in player_report_ids
        else (player_report_ids[0] if player_report_ids else "")
    )
    index = _viewer_index(
        data_mode="player",
        config=config,
        reports=player_reports,
        seeds=seeds,
        default_report_id=default_report_id,
        chunk_dir_name=chunk_dir_name,
        audit_index_filename=audit_index_filename,
    )
    audit_index = _viewer_index(
        data_mode="audit",
        config=config,
        reports=audit_reports,
        seeds=seeds,
        default_report_id=default_report_id,
        chunk_dir_name=audit_chunk_dir_name,
        audit_index_filename=audit_index_filename,
    )
    return {
        "marketId": market_id,
        "indexFilename": f"{market_id}_forecast_index.js",
        "auditIndexFilename": audit_index_filename,
        "chunkDirName": chunk_dir_name,
        "auditChunkDirName": audit_chunk_dir_name,
        "index": index,
        "auditIndex": audit_index,
    }


def serialize_viewer_indices(
    rows: list[dict[str, Any]],
    config: dict[str, Any],
) -> dict[str, Any]:
    """Build deterministic player/audit indices without retaining all chunks."""

    player_reports: list[dict[str, Any]] = []
    audit_reports: list[dict[str, Any]] = []
    for report_id in _ordered_report_ids(rows, config):
        audit = serialize_viewer_report(rows, report_id, data_mode="audit")
        audit_reports.append(audit["reportMeta"])
        player = serialize_viewer_report(rows, report_id, data_mode="player")
        if player["reportMeta"]["rowCount"]:
            player_reports.append(player["reportMeta"])
    return _index_dataset(
        rows,
        config,
        player_reports=player_reports,
        audit_reports=audit_reports,
    )


def serialize_viewer_index(
    rows: list[dict[str, Any]],
    config: dict[str, Any],
    *,
    data_mode: str,
) -> dict[str, Any]:
    """Build one mode-specific index without projecting the other information tier."""

    if data_mode not in {"player", "audit"}:
        raise ValueError(f"unsupported forecast Viewer data mode: {data_mode}")
    reports: list[dict[str, Any]] = []
    for report_id in _ordered_report_ids(rows, config):
        serialized = serialize_viewer_report(rows, report_id, data_mode=data_mode)
        if data_mode == "player" and not serialized["reportMeta"]["rowCount"]:
            continue
        reports.append(serialized["reportMeta"])
    market_id = str(config.get("city_airport_market_id") or "city_airport_market")
    report_ids = [item["reportId"] for item in reports]
    default_report_id = (
        "public_consensus"
        if "public_consensus" in report_ids
        else (report_ids[0] if report_ids else "")
    )
    return _viewer_index(
        data_mode=data_mode,
        config=config,
        reports=reports,
        seeds=sorted({int(float(row.get("seed", 0))) for row in rows}),
        default_report_id=default_report_id,
        chunk_dir_name=(
            f"{market_id}_forecast_chunks"
            if data_mode == "player"
            else f"{market_id}_audit_forecast_chunks"
        ),
        audit_index_filename=f"{market_id}_forecast_audit_index.js",
    )


def viewer_index_scripts(dataset: dict[str, Any]) -> dict[str, str]:
    """Render the existing Release index scripts from a pure dataset."""

    index_json = json.dumps(
        dataset["index"],
        ensure_ascii=False,
        separators=(",", ":"),
    )
    audit_index_json = json.dumps(
        dataset["auditIndex"],
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return {
        "player": (
            "(() => { const index = "
            + index_json
            + "; index.baseUrl = new URL(index.chunkBase, document.currentScript.src).href; "
            + "index.auditIndexUrl = new URL(index.auditIndexFile, document.currentScript.src).href; "
            + "window.AIRPORT_FORECAST_LAZY_INDEX = index; })();\n"
        ),
        "audit": (
            "(() => { const index = "
            + audit_index_json
            + "; index.baseUrl = new URL(index.chunkBase, document.currentScript.src).href; "
            + "window.AIRPORT_FORECAST_AUDIT_LAZY_INDEX = index; })();\n"
        ),
    }
    raw = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    path.write_bytes(raw)
    return len(raw), hashlib.sha256(raw).hexdigest()


def write_viewer_lazy_assets(
    output_dir: Path,
    rows: list[dict[str, Any]],
    config: dict[str, Any],
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    report_ids = _ordered_report_ids(rows, config)
    market_id = str(config.get("city_airport_market_id") or "city_airport_market")
    chunk_dir = output_dir / f"{market_id}_forecast_chunks"
    audit_chunk_dir = output_dir / f"{market_id}_audit_forecast_chunks"
    chunk_dir.mkdir(parents=True, exist_ok=True)
    audit_chunk_dir.mkdir(parents=True, exist_ok=True)
    player_reports: list[dict[str, Any]] = []
    audit_reports: list[dict[str, Any]] = []
    for report_id in report_ids:
        serialized = serialize_viewer_report(rows, report_id, data_mode="audit")
        (audit_chunk_dir / serialized["filename"]).write_bytes(serialized["raw"])
        audit_reports.append(serialized["reportMeta"])
        serialized = serialize_viewer_report(rows, report_id, data_mode="player")
        if serialized["reportMeta"]["rowCount"]:
            (chunk_dir / serialized["filename"]).write_bytes(serialized["raw"])
            player_reports.append(serialized["reportMeta"])
    dataset = _index_dataset(
        rows,
        config,
        player_reports=player_reports,
        audit_reports=audit_reports,
    )
    index_filename = dataset["indexFilename"]
    audit_index_filename = dataset["auditIndexFilename"]
    scripts = viewer_index_scripts(dataset)
    (output_dir / index_filename).write_text(scripts["player"], encoding="utf-8")
    (output_dir / audit_index_filename).write_text(scripts["audit"], encoding="utf-8")
    return {
        "index": str((output_dir / index_filename).as_posix()),
        "auditIndex": str((output_dir / audit_index_filename).as_posix()),
        "chunkDir": str(chunk_dir.as_posix()),
        "auditChunkDir": str(audit_chunk_dir.as_posix()),
        "totalRows": dataset["index"]["totalRows"],
        "auditTotalRows": dataset["auditIndex"]["totalRows"],
        "reportCount": len(dataset["index"]["reports"]),
        "auditReportCount": len(dataset["auditIndex"]["reports"]),
        "chunkBytes": sum(
            int(report["bytes"])
            for report in dataset["index"]["reports"]
        ),
        "auditChunkBytes": sum(
            int(report["bytes"])
            for report in dataset["auditIndex"]["reports"]
        ),
    }
