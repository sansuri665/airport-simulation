from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any, ContextManager


INDEX_RESPONSE_SCHEMA_VERSION = "airport-city-market-context-index-v1"
CHUNK_RESPONSE_SCHEMA_VERSION = "airport-city-market-context-chunk-v1"
CITY_MARKET_RELATIVE_DIR = Path(
    "baseline/city_airport_market_demand/china_mainland"
)


class CityMarketContextUnavailableError(RuntimeError):
    """The requested workspace slot exists but cannot currently serve city data."""


def _clean_market_id(value: Any) -> str:
    market_id = str(value or "").strip()
    if not market_id or not market_id.replace("_", "").isalnum():
        raise ValueError("city market id must contain only letters, numbers, and underscores")
    return market_id


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
        raise CityMarketContextUnavailableError(
            "当前 Seed 的城市缓存尚未生成或已经过期，请先在首页生成当前世界"
        )
    cache_run_id = str(slot.get("cacheRunId") or "")
    if cache_run_id != slot_id:
        raise CityMarketContextUnavailableError("Seed 缓存身份与工作区槽位不一致")
    run_dir = ensure_inside(run_root, run_root / cache_run_id)
    if not run_dir.is_dir():
        raise FileNotFoundError(f"Seed 缓存目录不存在: {cache_run_id}")
    context = {
        "seed": seed,
        "years": years,
        "slotId": slot_id,
        "source": "seed_cache",
        "workspaceRevision": int(workspace.get("workspaceRevision", 0)),
        "cacheRunId": cache_run_id,
    }
    return context, run_dir


def _validate_dataset_context(
    index: dict[str, Any],
    *,
    seed: int,
    years: int,
) -> None:
    try:
        index_seed = int(index.get("seed"))
        start_year = int(index.get("startYear"))
        final_year = int(index.get("finalYear"))
    except (TypeError, ValueError) as exc:
        raise CityMarketContextUnavailableError(
            "城市缓存缺少可校验的 Seed 或年份上下文"
        ) from exc
    if index_seed != seed:
        raise CityMarketContextUnavailableError("城市缓存 Seed 与请求上下文不一致")
    if final_year - start_year != years:
        raise CityMarketContextUnavailableError("城市缓存年数与请求上下文不一致")


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
        market_dir = ensure_inside(run_dir, run_dir / CITY_MARKET_RELATIVE_DIR)
        csv_paths = sorted(market_dir.glob("*_city_airport_demand_seed_sweep.csv"))
        if not csv_paths:
            raise FileNotFoundError(f"Seed 缓存缺少城市市场 CSV: {market_dir}")
        dataset = serialize_dataset(
            [(str(path), read_csv(path)) for path in csv_paths],
        )
        index = dataset["index"]
        _validate_dataset_context(index, seed=seed, years=years)
        return {
            "ok": True,
            "schemaVersion": INDEX_RESPONSE_SCHEMA_VERSION,
            "context": context,
            "index": index,
        }


def chunk_payload(
    seed: int,
    years: int,
    market_id: str,
    *,
    workspace_payload: Callable[[], dict[str, Any]],
    run_root: Path,
    run_id_for: Callable[[int, int], str],
    ensure_inside: Callable[[Path, Path], Path],
    lock_for_run: Callable[[str], ContextManager[None]],
    read_csv: Callable[[Path], list[dict[str, str]]],
    serialize_rows: Callable[..., dict[str, Any]],
) -> dict[str, Any]:
    clean_market_id = _clean_market_id(market_id)
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
        market_dir = ensure_inside(run_dir, run_dir / CITY_MARKET_RELATIVE_DIR)
        csv_path = ensure_inside(
            market_dir,
            market_dir / f"{clean_market_id}_city_airport_demand_seed_sweep.csv",
        )
        if not csv_path.is_file():
            raise FileNotFoundError(f"城市市场不存在: {clean_market_id}")
        serialized = serialize_rows(read_csv(csv_path), source=str(csv_path))
        if serialized["marketId"] != clean_market_id:
            raise CityMarketContextUnavailableError("城市分块身份与请求不一致")
        seed_values = serialized["seedValues"]
        if seed_values != {seed}:
            raise CityMarketContextUnavailableError("城市分块 Seed 与请求上下文不一致")
        if serialized["finalYear"] - serialized["startYear"] != years:
            raise CityMarketContextUnavailableError("城市分块年数与请求上下文不一致")
        return {
            "ok": True,
            "schemaVersion": CHUNK_RESPONSE_SCHEMA_VERSION,
            "context": context,
            "chunk": serialized["chunkPayload"],
        }
