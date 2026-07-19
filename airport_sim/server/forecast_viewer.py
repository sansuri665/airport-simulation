from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any, ContextManager


INDEX_RESPONSE_SCHEMA_VERSION = "airport-forecast-viewer-context-index-v1"
REPORT_RESPONSE_SCHEMA_VERSION = "airport-forecast-viewer-context-report-v1"
FORECAST_RELATIVE_CSV = Path(
    "baseline/city_airport_potential_passenger_forecast/china_mainland/"
    "beijing_airport_system_potential_passenger_forecast_seed_sweep.csv"
)
DATA_MODES = frozenset({"player", "audit"})


class ForecastViewerContextUnavailableError(RuntimeError):
    """The requested slot cannot currently serve forecast Viewer data."""


def _clean_data_mode(value: Any) -> str:
    data_mode = str(value or "").strip().lower()
    if data_mode not in DATA_MODES:
        raise ValueError("forecast data mode must be player or audit")
    return data_mode


def _clean_report_id(value: Any) -> str:
    report_id = str(value or "").strip()
    if (
        not report_id
        or not report_id.replace("_", "").replace("-", "").isalnum()
    ):
        raise ValueError(
            "forecast report id must contain only letters, numbers, underscores, and hyphens"
        )
    return report_id


def _context_and_run_dir(
    seed: int,
    years: int,
    data_mode: str,
    *,
    workspace_payload: Callable[[], dict[str, Any]],
    run_root: Path,
    run_id_for: Callable[[int, int], str],
    ensure_inside: Callable[[Path, Path], Path],
) -> tuple[dict[str, Any], Path]:
    slot_id = run_id_for(seed, years)
    workspace = workspace_payload()
    slot = next(
        (item for item in workspace.get("slots", []) if item.get("slotId") == slot_id),
        None,
    )
    if slot is None:
        raise FileNotFoundError(f"工作区没有 Seed {seed} / {years} 年槽位")
    if slot.get("cacheStatus") != "ready":
        raise ForecastViewerContextUnavailableError(
            "当前 Seed 的预测缓存尚未生成或已经过期，请先在首页生成当前世界"
        )
    cache_run_id = str(slot.get("cacheRunId") or "")
    if cache_run_id != slot_id:
        raise ForecastViewerContextUnavailableError("预测缓存身份与工作区槽位不一致")
    run_dir = ensure_inside(run_root, run_root / cache_run_id)
    if not run_dir.is_dir():
        raise FileNotFoundError(f"Seed 缓存目录不存在: {cache_run_id}")
    return (
        {
            "seed": seed,
            "years": years,
            "slotId": slot_id,
            "source": "seed_cache",
            "dataMode": data_mode,
            "workspaceRevision": int(workspace.get("workspaceRevision", 0)),
            "cacheRunId": cache_run_id,
        },
        run_dir,
    )


def _forecast_rows(
    run_dir: Path,
    *,
    seed: int,
    years: int,
    ensure_inside: Callable[[Path, Path], Path],
    read_csv: Callable[[Path], list[dict[str, str]]],
    decode_rows: Callable[..., list[dict[str, Any]]],
    null_fields: frozenset[str],
) -> list[dict[str, Any]]:
    csv_path = ensure_inside(run_dir, run_dir / FORECAST_RELATIVE_CSV)
    if not csv_path.is_file():
        raise FileNotFoundError(f"Seed 缓存缺少北京预测 CSV: {csv_path}")
    rows = decode_rows(read_csv(csv_path), null_fields=null_fields)
    if not rows:
        raise ForecastViewerContextUnavailableError("北京预测缓存没有数据")
    try:
        seeds = {int(row.get("seed")) for row in rows}
        as_of_years = {int(row.get("as_of_year")) for row in rows}
        forecast_years = {int(row.get("forecast_year")) for row in rows}
    except (TypeError, ValueError) as exc:
        raise ForecastViewerContextUnavailableError(
            "北京预测缓存缺少可校验的 Seed 或年份上下文"
        ) from exc
    if seeds != {seed}:
        raise ForecastViewerContextUnavailableError("北京预测缓存 Seed 与请求上下文不一致")
    if not as_of_years or not forecast_years:
        raise ForecastViewerContextUnavailableError("北京预测缓存年份为空")
    if max(forecast_years) - min(as_of_years) != years:
        raise ForecastViewerContextUnavailableError("北京预测缓存年数与请求上下文不一致")
    return rows


def index_payload(
    seed: int,
    years: int,
    data_mode: str,
    *,
    workspace_payload: Callable[[], dict[str, Any]],
    run_root: Path,
    run_id_for: Callable[[int, int], str],
    ensure_inside: Callable[[Path, Path], Path],
    lock_for_run: Callable[[str], ContextManager[None]],
    read_csv: Callable[[Path], list[dict[str, str]]],
    read_config: Callable[[Path], dict[str, Any]],
    config_path: Path,
    decode_rows: Callable[..., list[dict[str, Any]]],
    null_fields: frozenset[str],
    serialize_index: Callable[..., dict[str, Any]],
) -> dict[str, Any]:
    clean_mode = _clean_data_mode(data_mode)
    run_id = run_id_for(seed, years)
    with lock_for_run(run_id):
        context, run_dir = _context_and_run_dir(
            seed,
            years,
            clean_mode,
            workspace_payload=workspace_payload,
            run_root=run_root,
            run_id_for=run_id_for,
            ensure_inside=ensure_inside,
        )
        rows = _forecast_rows(
            run_dir,
            seed=seed,
            years=years,
            ensure_inside=ensure_inside,
            read_csv=read_csv,
            decode_rows=decode_rows,
            null_fields=null_fields,
        )
        index = serialize_index(
            rows,
            read_config(config_path),
            data_mode=clean_mode,
        )
        if index.get("seeds") != [seed]:
            raise ForecastViewerContextUnavailableError(
                "预测索引 Seed 与请求上下文不一致"
            )
        return {
            "ok": True,
            "schemaVersion": INDEX_RESPONSE_SCHEMA_VERSION,
            "context": context,
            "index": index,
        }


def report_payload(
    seed: int,
    years: int,
    data_mode: str,
    report_id: str,
    *,
    workspace_payload: Callable[[], dict[str, Any]],
    run_root: Path,
    run_id_for: Callable[[int, int], str],
    ensure_inside: Callable[[Path, Path], Path],
    lock_for_run: Callable[[str], ContextManager[None]],
    read_csv: Callable[[Path], list[dict[str, str]]],
    decode_rows: Callable[..., list[dict[str, Any]]],
    null_fields: frozenset[str],
    serialize_report: Callable[..., dict[str, Any]],
) -> dict[str, Any]:
    clean_mode = _clean_data_mode(data_mode)
    clean_report_id = _clean_report_id(report_id)
    run_id = run_id_for(seed, years)
    with lock_for_run(run_id):
        context, run_dir = _context_and_run_dir(
            seed,
            years,
            clean_mode,
            workspace_payload=workspace_payload,
            run_root=run_root,
            run_id_for=run_id_for,
            ensure_inside=ensure_inside,
        )
        rows = _forecast_rows(
            run_dir,
            seed=seed,
            years=years,
            ensure_inside=ensure_inside,
            read_csv=read_csv,
            decode_rows=decode_rows,
            null_fields=null_fields,
        )
        serialized = serialize_report(rows, clean_report_id, data_mode=clean_mode)
        chunk = serialized["chunkPayload"]
        if not chunk.get("rowCount"):
            raise FileNotFoundError(
                f"{clean_mode} 预测目录中不存在报告: {clean_report_id}"
            )
        if {int(row.get("seed")) for row in chunk["rows"]} != {seed}:
            raise ForecastViewerContextUnavailableError(
                "预测报告 Seed 与请求上下文不一致"
            )
        return {
            "ok": True,
            "schemaVersion": REPORT_RESPONSE_SCHEMA_VERSION,
            "context": context,
            "chunk": chunk,
        }
