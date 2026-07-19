from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any, ContextManager


INDEX_RESPONSE_SCHEMA_VERSION = "airport-global-viewer-context-index-v1"
REGION_RESPONSE_SCHEMA_VERSION = "airport-global-viewer-context-region-v1"
REGION_ORDER = (
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
)
GLOBAL_RELATIVE_CSV = Path(
    "baseline/global_macro/global_macro_feedback_seed_sweep.csv"
)
RECONCILED_RELATIVE_CSV = Path(
    "baseline/regional_macro_reconciled/regional_macro_reconciled_seed_sweep.csv"
)
DIAGNOSTIC_RELATIVE_CSV = Path(
    "baseline/regional_macro_reconciled/"
    "regional_macro_reconciliation_seed_sweep.csv"
)


class GlobalViewerContextUnavailableError(RuntimeError):
    """The requested workspace slot cannot currently serve global Viewer data."""


def _context_and_run_dir(
    seed: int,
    years: int,
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
        raise GlobalViewerContextUnavailableError(
            "当前 Seed 的全球缓存尚未生成或已经过期，请先在首页生成当前世界"
        )
    cache_run_id = str(slot.get("cacheRunId") or "")
    if cache_run_id != slot_id:
        raise GlobalViewerContextUnavailableError("Seed 缓存身份与工作区槽位不一致")
    run_dir = ensure_inside(run_root, run_root / cache_run_id)
    if not run_dir.is_dir():
        raise FileNotFoundError(f"Seed 缓存目录不存在: {cache_run_id}")
    return (
        {
            "seed": seed,
            "years": years,
            "slotId": slot_id,
            "source": "seed_cache",
            "workspaceRevision": int(workspace.get("workspaceRevision", 0)),
            "cacheRunId": cache_run_id,
        },
        run_dir,
    )


def _validated_rows(
    path: Path,
    *,
    seed: int,
    years: int,
    label: str,
    read_csv: Callable[[Path], list[dict[str, str]]],
    decode_rows: Callable[..., list[dict[str, Any]]],
    null_fields: frozenset[str] = frozenset(),
    omit_empty_fields: frozenset[str] = frozenset(),
) -> list[dict[str, Any]]:
    if not path.is_file():
        raise FileNotFoundError(f"Seed 缓存缺少{label}: {path}")
    rows = decode_rows(
        read_csv(path),
        null_fields=null_fields,
        omit_empty_fields=omit_empty_fields,
    )
    if not rows:
        raise GlobalViewerContextUnavailableError(f"{label}没有数据")
    try:
        seeds = {int(row.get("seed")) for row in rows}
        years_found = {int(row.get("year")) for row in rows}
    except (TypeError, ValueError) as exc:
        raise GlobalViewerContextUnavailableError(
            f"{label}缺少可校验的 Seed 或年份上下文"
        ) from exc
    if seeds != {seed}:
        raise GlobalViewerContextUnavailableError(f"{label} Seed 与请求上下文不一致")
    if max(years_found) - min(years_found) != years:
        raise GlobalViewerContextUnavailableError(f"{label}年数与请求上下文不一致")
    return rows


def _region_paths(
    run_dir: Path,
    region_id: str,
    *,
    ensure_inside: Callable[[Path, Path], Path],
) -> tuple[Path, Path, Path]:
    if region_id not in REGION_ORDER:
        raise FileNotFoundError(f"全球 Viewer 区域不存在: {region_id}")
    return (
        ensure_inside(
            run_dir,
            run_dir
            / "baseline"
            / "regional_macro"
            / region_id
            / f"{region_id}_regional_macro_seed_sweep.csv",
        ),
        ensure_inside(
            run_dir,
            run_dir
            / "baseline"
            / "regional_aviation_demand"
            / region_id
            / f"{region_id}_aviation_demand_seed_sweep.csv",
        ),
        ensure_inside(
            run_dir,
            run_dir
            / "baseline"
            / "regional_air_capacity_supply"
            / region_id
            / f"{region_id}_air_capacity_supply_seed_sweep.csv",
        ),
    )


def _region_input(
    run_dir: Path,
    region_id: str,
    *,
    seed: int,
    years: int,
    ensure_inside: Callable[[Path, Path], Path],
    read_csv: Callable[[Path], list[dict[str, str]]],
    decode_rows: Callable[..., list[dict[str, Any]]],
) -> tuple[
    str,
    str,
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    regional_path, aviation_path, supply_path = _region_paths(
        run_dir,
        region_id,
        ensure_inside=ensure_inside,
    )
    regional_rows = _validated_rows(
        regional_path,
        seed=seed,
        years=years,
        label=f"{region_id} 区域宏观数据",
        read_csv=read_csv,
        decode_rows=decode_rows,
    )
    aviation_rows = _validated_rows(
        aviation_path,
        seed=seed,
        years=years,
        label=f"{region_id} 航空需求数据",
        read_csv=read_csv,
        decode_rows=decode_rows,
    )
    supply_rows = _validated_rows(
        supply_path,
        seed=seed,
        years=years,
        label=f"{region_id} 航空供给数据",
        read_csv=read_csv,
        decode_rows=decode_rows,
    )
    region_name = str(regional_rows[0].get("region_name") or region_id)
    return region_id, region_name, regional_rows, aviation_rows, supply_rows


def index_payload(
    seed: int,
    years: int,
    *,
    workspace_payload: Callable[[], dict[str, Any]],
    run_root: Path,
    run_id_for: Callable[[int, int], str],
    ensure_inside: Callable[[Path, Path], Path],
    lock_for_run: Callable[[str], ContextManager[None]],
    read_csv: Callable[[Path], list[dict[str, str]]],
    decode_rows: Callable[..., list[dict[str, Any]]],
    optional_scenario_fields: frozenset[str],
    serialize_core: Callable[..., dict[str, Any]],
    serialize_dataset: Callable[..., dict[str, Any]],
) -> dict[str, Any]:
    run_id = run_id_for(seed, years)
    with lock_for_run(run_id):
        context, run_dir = _context_and_run_dir(
            seed,
            years,
            workspace_payload=workspace_payload,
            run_root=run_root,
            run_id_for=run_id_for,
            ensure_inside=ensure_inside,
        )
        global_rows = _validated_rows(
            ensure_inside(run_dir, run_dir / GLOBAL_RELATIVE_CSV),
            seed=seed,
            years=years,
            label="全球宏观主链",
            read_csv=read_csv,
            decode_rows=decode_rows,
            omit_empty_fields=optional_scenario_fields,
        )
        reconciled_rows = _validated_rows(
            ensure_inside(run_dir, run_dir / RECONCILED_RELATIVE_CSV),
            seed=seed,
            years=years,
            label="区域宏观对账数据",
            read_csv=read_csv,
            decode_rows=decode_rows,
        )
        diagnostic_rows = _validated_rows(
            ensure_inside(run_dir, run_dir / DIAGNOSTIC_RELATIVE_CSV),
            seed=seed,
            years=years,
            label="区域宏观对账诊断",
            read_csv=read_csv,
            decode_rows=decode_rows,
        )
        region_inputs = [
            _region_input(
                run_dir,
                region_id,
                seed=seed,
                years=years,
                ensure_inside=ensure_inside,
                read_csv=read_csv,
                decode_rows=decode_rows,
            )
            for region_id in REGION_ORDER
        ]
        dataset = serialize_dataset(region_inputs)
        return {
            "ok": True,
            "schemaVersion": INDEX_RESPONSE_SCHEMA_VERSION,
            "context": context,
            "core": serialize_core(global_rows, reconciled_rows, diagnostic_rows),
            "index": dataset["index"],
        }


def region_payload(
    seed: int,
    years: int,
    region_id: str,
    *,
    workspace_payload: Callable[[], dict[str, Any]],
    run_root: Path,
    run_id_for: Callable[[int, int], str],
    ensure_inside: Callable[[Path, Path], Path],
    lock_for_run: Callable[[str], ContextManager[None]],
    read_csv: Callable[[Path], list[dict[str, str]]],
    decode_rows: Callable[..., list[dict[str, Any]]],
    serialize_region: Callable[..., dict[str, Any]],
) -> dict[str, Any]:
    clean_region_id = str(region_id or "").strip()
    run_id = run_id_for(seed, years)
    with lock_for_run(run_id):
        context, run_dir = _context_and_run_dir(
            seed,
            years,
            workspace_payload=workspace_payload,
            run_root=run_root,
            run_id_for=run_id_for,
            ensure_inside=ensure_inside,
        )
        region_input = _region_input(
            run_dir,
            clean_region_id,
            seed=seed,
            years=years,
            ensure_inside=ensure_inside,
            read_csv=read_csv,
            decode_rows=decode_rows,
        )
        serialized = serialize_region(*region_input)
        return {
            "ok": True,
            "schemaVersion": REGION_RESPONSE_SCHEMA_VERSION,
            "context": context,
            "chunk": serialized["chunkPayload"],
        }
