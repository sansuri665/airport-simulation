from __future__ import annotations

import shutil
import subprocess
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, ContextManager


def aggregate_run(
    run_dir: Path,
    seed: int,
    years: int,
    elapsed_sec: float,
    cached: bool,
    *,
    root_dir: Path,
    read_csv: Callable[[Path], list[dict[str, str]]],
    summarize_city: Callable[[list[dict[str, str]]], dict[str, Any]],
) -> dict[str, Any]:
    city_dir = (
        run_dir
        / "baseline"
        / "city_airport_market_demand"
        / "china_mainland"
    )
    files = sorted(city_dir.glob("*_city_airport_demand_seed_sweep.csv"))
    if not files:
        raise FileNotFoundError(f"no city airport market output found in {city_dir}")
    cities = []
    for path in files:
        rows = read_csv(path)
        if rows:
            cities.append(summarize_city(rows))
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
    return {
        "seed": seed,
        "years": years,
        "cached": cached,
        "elapsedSec": round(elapsed_sec, 2),
        "runId": run_dir.name,
        "runDir": str(run_dir.relative_to(root_dir).as_posix()),
        "generatedAt": time.strftime("%Y-%m-%d %H:%M:%S"),
        "cityCount": len(cities),
        "startYear": min(city["startYear"] for city in cities),
        "finalYear": max(city["finalYear"] for city in cities),
        "cities": cities,
        "rankings": rankings,
    }


def run_orchestrator(
    seed: int,
    years: int,
    run_dir: Path,
    force: bool,
    *,
    root_dir: Path,
    run_root: Path,
    orchestrator: Path,
    migrate_legacy_save: Callable[[int, int], Path | None],
    ensure_inside: Callable[[Path, Path], Path],
    structured_log: Callable[..., None],
    executable: str,
    run_process: Callable[..., Any] = subprocess.run,
    clock: Callable[[], float] = time.perf_counter,
) -> tuple[float, str]:
    if run_dir.exists():
        migrate_legacy_save(seed, years)
        resolved = ensure_inside(run_root, run_dir)
        shutil.rmtree(resolved)
    run_root.mkdir(parents=True, exist_ok=True)
    started = clock()
    structured_log(
        "orchestrator_start",
        run_id=run_dir.name,
        seed=seed,
        years=years,
        force=force,
    )
    cmd = [
        executable,
        str(orchestrator),
        "--seed",
        str(seed),
        "--years",
        str(years),
        "--scenario-state",
        "none",
        "--run-id",
        run_dir.name,
        "--output-root",
        str(run_root),
        "--viewer-output-root",
        str(root_dir / "output" / "seed_explorer_viewer"),
        "--publish-viewer",
        "none",
        "--artifact-profile",
        "seed-cache",
    ]
    result = run_process(
        cmd,
        cwd=str(root_dir),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=240,
    )
    elapsed = clock() - started
    output_tail = (result.stdout + "\n" + result.stderr)[-6000:]
    if result.returncode != 0:
        structured_log(
            "orchestrator_failed",
            run_id=run_dir.name,
            seed=seed,
            years=years,
            return_code=result.returncode,
            elapsed_sec=round(elapsed, 4),
        )
        raise RuntimeError(
            f"orchestrator failed with code {result.returncode}\n{output_tail}"
        )
    structured_log(
        "orchestrator_complete",
        run_id=run_dir.name,
        seed=seed,
        years=years,
        elapsed_sec=round(elapsed, 4),
    )
    return elapsed, output_tail


def run_seed(
    seed: int,
    years: int,
    force: bool,
    *,
    run_root: Path,
    run_id_for: Callable[[int, int], str],
    update_task_progress: Callable[..., Any],
    load_cached: Callable[[Path], dict[str, Any] | None],
    lock_for_run: Callable[[str], ContextManager[Any]],
    run_orchestrator: Callable[[int, int, Path, bool], tuple[float, str]],
    aggregate_run: Callable[[Path, int, int, float, bool], dict[str, Any]],
    save_cached: Callable[[Path, dict[str, Any]], None],
    prune_cached_runs: Callable[[], None],
) -> dict[str, Any]:
    run_dir = run_root / run_id_for(seed, years)
    update_task_progress(
        run_dir.name,
        seed,
        years,
        "running",
        "cache_check",
        5,
        "正在检查缓存",
    )
    cached_payload = None if force else load_cached(run_dir)
    if cached_payload:
        cached_payload["cached"] = True
        cached_payload["elapsedSec"] = 0.0
        update_task_progress(
            run_dir.name,
            seed,
            years,
            "complete",
            "cache_hit",
            100,
            "已读取缓存",
            cached=True,
        )
        return cached_payload

    with lock_for_run(run_dir.name):
        cached_payload = None if force else load_cached(run_dir)
        if cached_payload:
            cached_payload["cached"] = True
            cached_payload["elapsedSec"] = 0.0
            update_task_progress(
                run_dir.name,
                seed,
                years,
                "complete",
                "cache_hit",
                100,
                "已读取缓存",
                cached=True,
            )
            return cached_payload
        try:
            update_task_progress(
                run_dir.name,
                seed,
                years,
                "running",
                "model_run",
                15,
                "Python 正在运行完整模型",
            )
            elapsed, _ = run_orchestrator(seed, years, run_dir, force)
            update_task_progress(
                run_dir.name,
                seed,
                years,
                "running",
                "aggregate",
                88,
                "正在聚合城市结果",
            )
            payload = aggregate_run(run_dir, seed, years, elapsed, cached=False)
            save_cached(run_dir, payload)
            prune_cached_runs()
            update_task_progress(
                run_dir.name,
                seed,
                years,
                "complete",
                "complete",
                100,
                "完整 Run 已就绪",
                cached=False,
            )
            return payload
        except Exception as error:
            update_task_progress(
                run_dir.name,
                seed,
                years,
                "failed",
                "failed",
                100,
                f"{type(error).__name__}: {str(error).splitlines()[0][:240]}",
                cached=False,
            )
            raise
