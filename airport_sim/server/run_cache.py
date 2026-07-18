from __future__ import annotations

import hashlib
import json
import platform
import shutil
import sys
import time
from collections.abc import Callable, Collection, Iterable
from pathlib import Path
from threading import RLock
from typing import Any, ContextManager


CACHE_FILENAME = "seed_explorer_city_market_cache.json"


def cache_path(run_dir: Path) -> Path:
    return run_dir / CACHE_FILENAME


def dependency_files(server_dir: Path, root_dir: Path) -> list[Path]:
    files = {
        path.resolve()
        for path in server_dir.glob("*.py")
        if path.is_file()
    }
    files.update(
        path.resolve()
        for path in (root_dir / "macro_layers").glob("*.py")
        if path.is_file()
    )
    files.update(
        path.resolve()
        for path in (root_dir / "config").rglob("*.json")
        if path.is_file()
    )
    return sorted(files, key=lambda path: path.as_posix())


def dependency_bytes(path: Path) -> bytes:
    """Read dependency content instead of trusting timestamps or file sizes."""

    return path.read_bytes()


def current_fingerprint(
    *,
    version: str,
    root_dir: Path,
    dependencies: Iterable[Path],
    read_dependency: Callable[[Path], bytes] = dependency_bytes,
) -> str:
    digest = hashlib.sha256()
    digest.update(version.encode("utf-8"))
    digest.update(b"\0")
    digest.update(platform.python_implementation().encode("utf-8"))
    digest.update(b"\0")
    digest.update(sys.version.encode("utf-8"))
    digest.update(b"\0")
    digest.update(platform.platform().encode("utf-8"))
    digest.update(b"\0")
    for path in dependencies:
        relative = path.relative_to(root_dir).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(read_dependency(path))
        digest.update(b"\0")
    return digest.hexdigest()


def cache_metadata(*, version: str, fingerprint: str) -> dict[str, str]:
    return {
        "cacheFingerprintVersion": version,
        "cacheFingerprint": fingerprint,
        "cachePython": f"{platform.python_implementation()} {platform.python_version()}",
        "cachePlatform": platform.platform(),
    }


def load_cached(
    run_dir: Path,
    *,
    version: str,
    expected_fingerprint: str | None,
    current_fingerprint: Callable[[], str],
) -> dict[str, Any] | None:
    path = cache_path(run_dir)
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return None
    if payload.get("cacheFingerprintVersion") != version:
        return None
    fingerprint = (
        expected_fingerprint
        if expected_fingerprint is not None
        else current_fingerprint()
    )
    if payload.get("cacheFingerprint") != fingerprint:
        return None
    return payload


def save_cached(
    run_dir: Path,
    payload: dict[str, Any],
    *,
    metadata: dict[str, Any],
    atomic_write_text: Callable[[Path, str], None],
) -> None:
    payload.update(metadata)
    atomic_write_text(
        cache_path(run_dir),
        json.dumps(payload, ensure_ascii=False),
    )


def cached_run_entry(
    run_dir: Path,
    expected_fingerprint: str | None,
    *,
    load_cached: Callable[[Path, str | None], dict[str, Any] | None],
    parse_run_id: Callable[[str], tuple[int | None, int | None]],
    operations_relative_csv: Path,
) -> dict[str, Any]:
    cached_payload = load_cached(run_dir, expected_fingerprint)
    payload = cached_payload or {}
    seed_from_name, years_from_name = parse_run_id(run_dir.name)
    stat = run_dir.stat()
    return {
        "runId": run_dir.name,
        "seed": payload.get("seed", seed_from_name),
        "years": payload.get("years", years_from_name),
        "cityCount": payload.get("cityCount", 0),
        "startYear": payload.get("startYear"),
        "finalYear": payload.get("finalYear"),
        "generatedAt": payload.get("generatedAt", ""),
        "lastWriteTime": time.strftime(
            "%Y-%m-%d %H:%M:%S",
            time.localtime(stat.st_mtime),
        ),
        "hasCityCache": cached_payload is not None,
        "cacheStatus": "valid" if cached_payload is not None else "missing_or_stale",
        "hasBeijingOperations": (run_dir / operations_relative_csv).exists(),
    }


def list_cached_runs(
    *,
    run_root: Path,
    current_fingerprint: Callable[[], str],
    cached_run_entry: Callable[[Path, str | None], dict[str, Any]],
) -> list[dict[str, Any]]:
    if not run_root.exists():
        return []
    run_dirs = [path for path in run_root.iterdir() if path.is_dir()]
    run_dirs.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    fingerprint = current_fingerprint() if run_dirs else None
    return [cached_run_entry(path, fingerprint) for path in run_dirs]


def retention_policy(default_max_cached_runs: int) -> dict[str, Any]:
    try:
        from airport_sim.cache_service import load_policy

        policy = load_policy()
        return {
            "maxCachedRuns": int(policy["maxCachedRuns"]),
            "pinnedRunIds": list(policy["pinnedRunIds"]),
        }
    except (ImportError, KeyError, TypeError, ValueError):
        return {
            "maxCachedRuns": default_max_cached_runs,
            "pinnedRunIds": [],
        }


def prune_cached_runs(
    *,
    run_root: Path,
    run_locks_guard: RLock,
    run_lock_users: Collection[str],
    cache_retention_policy: Callable[[], dict[str, Any]],
    current_fingerprint: Callable[[], str],
    load_cached: Callable[[Path, str | None], dict[str, Any] | None],
    try_lock_for_run: Callable[[str], ContextManager[bool]],
    ensure_inside: Callable[[Path, Path], Path],
) -> None:
    if not run_root.exists():
        return
    # Staging belongs to an in-flight or diagnosable interrupted atomic build.
    # Active Run directories remain protected while unrelated seeds may proceed.
    with run_locks_guard:
        active_run_ids = set(run_lock_users)
    run_dirs = [
        path
        for path in run_root.iterdir()
        if path.is_dir()
        and not path.name.startswith(".staging_")
        and path.name not in active_run_ids
    ]
    policy = cache_retention_policy()
    max_cached_runs = int(policy["maxCachedRuns"])
    pinned_run_ids = set(policy["pinnedRunIds"])
    eligible = [path for path in run_dirs if path.name not in pinned_run_ids]
    expected_fingerprint = current_fingerprint() if eligible else None
    valid = [
        path
        for path in eligible
        if load_cached(path, expected_fingerprint) is not None
    ]
    invalid = [path for path in eligible if path not in valid]
    stale = invalid + sorted(
        valid,
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )[max_cached_runs:]
    for path in stale:
        with try_lock_for_run(path.name) as reserved:
            if not reserved or not path.exists():
                continue
            resolved = ensure_inside(run_root, path)
            shutil.rmtree(resolved)
