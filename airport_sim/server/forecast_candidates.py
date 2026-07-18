from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any


BEIJING_CITY_DEMAND_RELATIVE_CSV = Path(
    "city_airport_market_demand/china_mainland/"
    "beijing_airport_system_city_airport_demand_seed_sweep.csv"
)


def forecast_candidate_release_context(
    *,
    output_root: Path,
    root_dir: Path,
    read_json: Callable[[Path], Any],
    ensure_inside: Callable[[Path, Path], Path],
    read_csv: Callable[[Path], list[dict[str, str]]],
    as_float: Callable[[Any, float], float],
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    manifest_path = output_root / "current_viewer_manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError("当前没有可用于候选报告的正式 Viewer 发布")
    manifest = read_json(manifest_path)
    if not isinstance(manifest, dict) or not str(manifest.get("release_id") or "").strip():
        raise ValueError("当前 Viewer 发布清单无效")
    source_value = str(manifest.get("source_variant") or "").strip()
    if not source_value:
        raise ValueError("当前 Viewer 发布没有记录正式数据来源")
    source_path = Path(source_value)
    if not source_path.is_absolute():
        source_path = root_dir / source_path
    source_path = ensure_inside(output_root, source_path)
    city_path = source_path / BEIJING_CITY_DEMAND_RELATIVE_CSV
    if not city_path.is_file():
        raise FileNotFoundError("当前 Viewer 发布缺少北京城市航空市场数据")
    rows = read_csv(city_path)
    if not rows:
        raise ValueError("当前 Viewer 发布的北京城市航空市场数据为空")
    release_seed = int(as_float(manifest.get("seed"), -1))
    row_seeds = {int(as_float(row.get("seed"), -2)) for row in rows}
    if row_seeds != {release_seed}:
        raise ValueError("当前 Viewer 发布 Seed 与城市市场数据不一致")
    return manifest, rows


def forecast_candidate_catalog_payload(
    *,
    release_context: Callable[[], tuple[dict[str, Any], list[dict[str, str]]]],
    candidate_layer: Any,
    config_path: Path,
    as_float: Callable[[Any, float], float],
) -> dict[str, Any]:
    manifest, rows = release_context()
    catalog = candidate_layer.forecast_candidate_catalog(config_path)
    data_years = sorted(int(as_float(row.get("year"), 0)) for row in rows)
    final_year = data_years[-1]
    for tier in catalog.get("tiers", []):
        tier["maxFullAsOfYear"] = final_year - int(tier["naturalHorizonYears"])
    return {
        "catalog": catalog,
        "release": {
            "releaseId": manifest.get("release_id"),
            "runId": manifest.get("run_id"),
            "seed": manifest.get("seed"),
            "startYear": data_years[0],
            "finalYear": final_year,
            "modelVersion": manifest.get("model_version"),
        },
    }


def generate_forecast_candidate_payload(
    body: dict[str, Any],
    *,
    release_context: Callable[[], tuple[dict[str, Any], list[dict[str, str]]]],
    candidate_layer: Any,
    config_path: Path,
    clean_seed: Callable[[Any], int],
    as_float: Callable[[Any, float], float],
) -> dict[str, Any]:
    manifest, rows = release_context()
    seed = clean_seed(body.get("seed"))
    if seed != int(as_float(manifest.get("seed"), -1)):
        raise ValueError("候选报告 Seed 必须与当前正式 Viewer 发布一致")
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
    return {
        "releaseId": manifest.get("release_id"),
        "runId": manifest.get("run_id"),
        **result,
    }
