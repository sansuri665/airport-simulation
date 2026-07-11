from __future__ import annotations

import threading
from contextlib import contextmanager


RUN_LOCKS_GUARD = threading.Lock()
RUN_LOCKS: dict[str, threading.RLock] = {}
RUN_LOCK_USERS: dict[str, int] = {}


@contextmanager
def lock_for_run(run_id: str):
    """Serialize writes to one Run while allowing unrelated Runs to progress."""
    clean_run_id = str(run_id).strip()
    if not clean_run_id:
        raise ValueError("run_id is required for locking")
    with RUN_LOCKS_GUARD:
        lock = RUN_LOCKS.setdefault(clean_run_id, threading.RLock())
        RUN_LOCK_USERS[clean_run_id] = RUN_LOCK_USERS.get(clean_run_id, 0) + 1
    lock.acquire()
    try:
        yield
    finally:
        lock.release()
        with RUN_LOCKS_GUARD:
            remaining = RUN_LOCK_USERS.get(clean_run_id, 1) - 1
            if remaining <= 0:
                RUN_LOCK_USERS.pop(clean_run_id, None)
                if RUN_LOCKS.get(clean_run_id) is lock:
                    RUN_LOCKS.pop(clean_run_id, None)
            else:
                RUN_LOCK_USERS[clean_run_id] = remaining


@contextmanager
def try_lock_for_run(run_id: str):
    """Reserve a Run for maintenance without waiting on active work."""
    clean_run_id = str(run_id).strip()
    lock: threading.RLock | None = None
    with RUN_LOCKS_GUARD:
        if clean_run_id and not RUN_LOCK_USERS.get(clean_run_id):
            candidate = RUN_LOCKS.setdefault(clean_run_id, threading.RLock())
            if candidate.acquire(blocking=False):
                RUN_LOCK_USERS[clean_run_id] = 1
                lock = candidate
    try:
        yield lock is not None
    finally:
        if lock is not None:
            lock.release()
            with RUN_LOCKS_GUARD:
                RUN_LOCK_USERS.pop(clean_run_id, None)
                if RUN_LOCKS.get(clean_run_id) is lock:
                    RUN_LOCKS.pop(clean_run_id, None)
