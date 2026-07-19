from __future__ import annotations

from collections.abc import Callable
from contextlib import nullcontext
from pathlib import Path
from typing import Any, ContextManager


BEIJING_CITY_DEMAND_RELATIVE_CSV = Path(
    "city_airport_market_demand/china_mainland/"
    "beijing_airport_system_city_airport_demand_seed_sweep.csv"
)
SOURCES = frozenset({"viewer_release", "seed_cache"})


class ForecastCandidateContextUnavailableError(RuntimeError):
    """The requested explicit source cannot serve an audit candidate."""


def _clean_source(value: Any) -> str:
    source = str(value or "").strip().lower()
    if source not in SOURCES:
        raise ValueError("candidate source must be viewer_release or seed_cache")
    return source


def forecast_candidate_source_context(
    seed: int,
    years: int,
    source: str,
    *,
    output_root: Path,
    root_dir: Path,
    run_root: Path,
    workspace_payload: Callable[[], dict[str, Any]],
    run_id_for: Callable[[int, int], str],
    lock_for_run: Callable[[str], ContextManager[None]],
    read_json: Callable[[Path], Any],
    ensure_inside: Callable[[Path, Path], Path],
    read_csv: Callable[[Path], list[dict[str, str]]],
    as_float: Callable[[Any, float], float],
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    """Resolve exactly one registered source; never fall back to another source."""

    clean_source = _clean_source(source)
    slot_id = run_id_for(seed, years)
    workspace = workspace_payload()
    slot = next(
        (item for item in workspace.get("slots", []) if item.get("slotId") == slot_id),
        None,
    )
    if slot is None:
        raise FileNotFoundError(f"工作区没有 Seed {seed} / {years} 年槽位")

    context: dict[str, Any] = {
        "seed": seed,
        "years": years,
        "slotId": slot_id,
        "source": clean_source,
        "dataMode": "audit",
        "workspaceRevision": int(workspace.get("workspaceRevision", 0)),
    }
    source_root: Path
    guard: ContextManager[None]
    if clean_source == "viewer_release":
        if not slot.get("isCurrentViewerRelease"):
            raise ForecastCandidateContextUnavailableError(
                "请求槽位不是当前 Viewer Release；不会隐式改读其他 Release"
            )
        manifest_path = output_root / "current_viewer_manifest.json"
        if not manifest_path.is_file():
            raise FileNotFoundError("当前没有可用于候选报告的 Viewer Release")
        manifest = read_json(manifest_path)
        if not isinstance(manifest, dict):
            raise ForecastCandidateContextUnavailableError("当前 Viewer Release 清单无效")
        release_id = str(manifest.get("release_id") or "").strip()
        release_seed = int(as_float(manifest.get("seed"), -1))
        release_years = int(as_float(manifest.get("years"), -1))
        if not release_id or release_seed != seed or release_years != years:
            raise ForecastCandidateContextUnavailableError(
                "当前 Viewer Release 与请求的 Seed/年数上下文不一致"
            )
        source_value = str(manifest.get("source_variant") or "").strip()
        if not source_value:
            raise ForecastCandidateContextUnavailableError(
                "当前 Viewer Release 没有记录数据来源"
            )
        source_root = Path(source_value)
        if not source_root.is_absolute():
            source_root = root_dir / source_root
        source_root = ensure_inside(output_root, source_root)
        context.update(
            {
                "releaseId": release_id,
                "runId": str(manifest.get("run_id") or ""),
                "modelVersion": str(manifest.get("model_version") or ""),
            }
        )
        guard = nullcontext()
    else:
        if slot.get("cacheStatus") != "ready":
            raise ForecastCandidateContextUnavailableError(
                "请求槽位没有可用的 Seed 缓存；不会隐式改读当前 Release"
            )
        cache_run_id = str(slot.get("cacheRunId") or "")
        if cache_run_id != slot_id:
            raise ForecastCandidateContextUnavailableError(
                "候选报告缓存身份与工作区槽位不一致"
            )
        run_dir = ensure_inside(run_root, run_root / cache_run_id)
        if not run_dir.is_dir():
            raise FileNotFoundError(f"Seed 缓存目录不存在: {cache_run_id}")
        source_root = ensure_inside(run_dir, run_dir / "baseline")
        context["cacheRunId"] = cache_run_id
        guard = lock_for_run(cache_run_id)

    with guard:
        city_path = ensure_inside(source_root, source_root / BEIJING_CITY_DEMAND_RELATIVE_CSV)
        if not city_path.is_file():
            raise FileNotFoundError("请求来源缺少北京城市航空市场数据")
        rows = read_csv(city_path)
    if not rows:
        raise ForecastCandidateContextUnavailableError(
            "请求来源的北京城市航空市场数据为空"
        )
    row_seeds = {int(as_float(row.get("seed"), -2)) for row in rows}
    data_years = sorted({int(as_float(row.get("year"), 0)) for row in rows})
    if row_seeds != {seed}:
        raise ForecastCandidateContextUnavailableError(
            "候选报告来源 Seed 与请求上下文不一致"
        )
    if not data_years or data_years[-1] - data_years[0] != years:
        raise ForecastCandidateContextUnavailableError(
            "候选报告来源年数与请求上下文不一致"
        )
    context.update({"startYear": data_years[0], "finalYear": data_years[-1]})
    return context, rows


def forecast_candidate_catalog_payload(
    seed: int,
    years: int,
    source: str,
    *,
    source_context: Callable[[int, int, str], tuple[dict[str, Any], list[dict[str, str]]]],
    candidate_layer: Any,
    config_path: Path,
    as_float: Callable[[Any, float], float],
) -> dict[str, Any]:
    context, rows = source_context(seed, years, source)
    catalog = candidate_layer.forecast_candidate_catalog(config_path)
    final_year = max(int(as_float(row.get("year"), 0)) for row in rows)
    for tier in catalog.get("tiers", []):
        tier["maxFullAsOfYear"] = final_year - int(tier["naturalHorizonYears"])
    return {"catalog": catalog, "context": context}


def generate_forecast_candidate_payload(
    body: dict[str, Any],
    *,
    source_context: Callable[[int, int, str], tuple[dict[str, Any], list[dict[str, str]]]],
    candidate_layer: Any,
    config_path: Path,
    clean_seed: Callable[[Any], int],
    clean_years: Callable[[Any], int],
) -> dict[str, Any]:
    seed = clean_seed(body.get("seed"))
    years = clean_years(body.get("years"))
    source = _clean_source(body.get("source"))
    context, rows = source_context(seed, years, source)
    modifier_values = body.get("modifierIds", [])
    if not isinstance(modifier_values, list):
        raise ValueError("modifierIds must be an array")
    try:
        as_of_year = int(body.get("asOfYear"))
        score_min = float(body.get("scoreMin"))
        score_max = float(body.get("scoreMax"))
        generation_nonce = int(body.get("generationNonce", 0))
    except (TypeError, ValueError) as error:
        raise ValueError("候选报告年份、分数范围或候选编号无效") from error
    result = candidate_layer.generate_forecast_candidate(
        rows,
        config_path=config_path,
        seed=seed,
        as_of_year=as_of_year,
        tier_profile_id=str(body.get("tierProfileId") or "").strip(),
        narrative_profile_id=str(body.get("narrativeProfileId") or "").strip(),
        modifier_mode=str(body.get("modifierMode") or "auto").strip(),
        modifier_ids=[str(value).strip() for value in modifier_values],
        score_min=score_min,
        score_max=score_max,
        generation_nonce=generation_nonce,
    )
    return {"context": context, **result}
