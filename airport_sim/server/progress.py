from __future__ import annotations

import json
import sys
import threading
import time
from collections.abc import Callable
from typing import Any


TASK_PROGRESS_VERSION = "airport-task-progress-v1"
MAX_TASK_PROGRESS_ENTRIES = 128
TASK_PROGRESS_LOCK = threading.Lock()
TASK_PROGRESS: dict[str, dict[str, Any]] = {}


def structured_log(event: str, **fields: Any) -> None:
    payload = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "event": event,
        **fields,
    }
    sys.stderr.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")


def update_task_progress(
    run_id: str,
    seed: int,
    years: int,
    status: str,
    phase: str,
    progress_pct: int,
    message: str,
    *,
    cached: bool | None = None,
    max_entries: int = MAX_TASK_PROGRESS_ENTRIES,
    logger: Callable[..., None] = structured_log,
) -> dict[str, Any]:
    now = time.time()
    payload = {
        "ok": True,
        "schemaVersion": TASK_PROGRESS_VERSION,
        "runId": run_id,
        "seed": seed,
        "years": years,
        "status": status,
        "phase": phase,
        "progressPct": max(0, min(100, int(progress_pct))),
        "message": message,
        "cached": cached,
        "updatedAt": time.strftime("%Y-%m-%d %H:%M:%S"),
        "updatedEpoch": now,
    }
    with TASK_PROGRESS_LOCK:
        TASK_PROGRESS[run_id] = payload
        if len(TASK_PROGRESS) > max_entries:
            eviction_candidates = [key for key in TASK_PROGRESS if key != run_id]
            oldest = min(
                eviction_candidates,
                key=lambda key: float(TASK_PROGRESS[key].get("updatedEpoch", 0)),
            )
            TASK_PROGRESS.pop(oldest, None)
    logger(
        "task_progress",
        run_id=run_id,
        seed=seed,
        years=years,
        status=status,
        phase=phase,
        progress_pct=payload["progressPct"],
        cached=cached,
    )
    return dict(payload)


def task_progress(run_id: str, seed: int, years: int) -> dict[str, Any]:
    with TASK_PROGRESS_LOCK:
        existing = TASK_PROGRESS.get(run_id)
        if existing is not None:
            return dict(existing)
    return {
        "ok": True,
        "schemaVersion": TASK_PROGRESS_VERSION,
        "runId": run_id,
        "seed": seed,
        "years": years,
        "status": "idle",
        "phase": "idle",
        "progressPct": 0,
        "message": "尚未开始",
        "cached": None,
        "updatedAt": None,
        "updatedEpoch": None,
    }
