from __future__ import annotations

import copy
import secrets
import threading
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from typing import Any


JOB_STATUS_VERSION = "airport-background-job-v1"
MAX_JOB_ENTRIES = 64
MAX_ACTIVE_JOB_ENTRIES = 16
JOB_EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="airport-job")
JOB_LOCK = threading.Lock()
JOBS: dict[str, dict[str, Any]] = {}
ACTIVE_JOB_BY_KEY: dict[str, str] = {}


class JobQueueFullError(RuntimeError):
    """Raised before submission when the bounded background queue is full."""


def _timestamp() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


def _public_job(job: dict[str, Any], *, deduplicated: bool = False) -> dict[str, Any]:
    payload = copy.deepcopy(job)
    payload["deduplicated"] = deduplicated
    return payload


def _prune_jobs() -> None:
    if len(JOBS) <= MAX_JOB_ENTRIES:
        return
    completed = sorted(
        (
            job
            for job in JOBS.values()
            if job["status"] in {"complete", "failed"}
        ),
        key=lambda job: float(job.get("updatedEpoch", 0)),
    )
    for job in completed:
        if len(JOBS) <= MAX_JOB_ENTRIES:
            break
        JOBS.pop(str(job["jobId"]), None)


def submit_job(
    kind: str,
    key: str,
    work: Callable[[], dict[str, Any]],
    *,
    logger: Callable[..., None],
) -> dict[str, Any]:
    with JOB_LOCK:
        active_id = ACTIVE_JOB_BY_KEY.get(key)
        if active_id and active_id in JOBS:
            return _public_job(JOBS[active_id], deduplicated=True)
        if len(ACTIVE_JOB_BY_KEY) >= MAX_ACTIVE_JOB_ENTRIES:
            raise JobQueueFullError(
                f"后台任务队列已满（最多 {MAX_ACTIVE_JOB_ENTRIES} 个排队或运行任务），请稍后重试"
            )
        now = time.time()
        job_id = secrets.token_hex(12)
        job = {
            "ok": True,
            "schemaVersion": JOB_STATUS_VERSION,
            "jobId": job_id,
            "kind": kind,
            "key": key,
            "status": "queued",
            "submittedAt": _timestamp(),
            "startedAt": None,
            "completedAt": None,
            "updatedEpoch": now,
            "result": None,
            "error": None,
        }
        JOBS[job_id] = job
        ACTIVE_JOB_BY_KEY[key] = job_id
        _prune_jobs()

    def execute() -> None:
        with JOB_LOCK:
            job["status"] = "running"
            job["startedAt"] = _timestamp()
            job["updatedEpoch"] = time.time()
        logger("background_job_start", job_id=job_id, job_kind=kind, job_key=key)
        try:
            result = work()
        except Exception as error:
            with JOB_LOCK:
                job["status"] = "failed"
                job["error"] = str(error).splitlines()[0][:240] or type(error).__name__
                job["completedAt"] = _timestamp()
                job["updatedEpoch"] = time.time()
            logger(
                "background_job_failed",
                job_id=job_id,
                job_kind=kind,
                job_key=key,
                error_type=type(error).__name__,
            )
        else:
            with JOB_LOCK:
                job["status"] = "complete"
                job["result"] = result
                job["completedAt"] = _timestamp()
                job["updatedEpoch"] = time.time()
            logger("background_job_complete", job_id=job_id, job_kind=kind, job_key=key)
        finally:
            with JOB_LOCK:
                if ACTIVE_JOB_BY_KEY.get(key) == job_id:
                    ACTIVE_JOB_BY_KEY.pop(key, None)

    JOB_EXECUTOR.submit(execute)
    return _public_job(job)


def get_job(job_id: str) -> dict[str, Any] | None:
    with JOB_LOCK:
        job = JOBS.get(str(job_id).strip())
        return _public_job(job) if job is not None else None
