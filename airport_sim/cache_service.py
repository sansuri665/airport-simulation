from __future__ import annotations

import json
import os
import shutil
import socket
import tempfile
import time
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

from .paths import OUTPUT_ROOT, ROOT_DIR, RUN_ROOT, SAVE_ROOT, VIEWER_RELEASE_ROOT


CACHE_INVENTORY_SCHEMA_VERSION = "airport-cache-inventory-v1"
CACHE_POLICY_SCHEMA_VERSION = "airport-cache-policy-v1"
CACHE_POLICY_PATH = SAVE_ROOT.parent / "cache_policy.json"
DEFAULT_MAX_CACHED_RUNS = 2
DEFAULT_MAX_VIEWER_RELEASES = 2
SERVICE_HEALTH_URL = "http://127.0.0.1:8776/api/health"
SERVICE_ID = "airport-local-ui-v1"
TEMPORARY_OUTPUT_MARKERS = ("test", "smoke", "probe", "draft", "check", "eval", "validation")
CANONICAL_OUTPUT_NAMES = {
    "city_airport_financial_state",
    "city_airport_market_demand",
    "city_airport_potential_passenger_forecast",
    "city_airport_quarterly_operations",
    "city_airport_valuation",
    "global_gdp",
    "global_macro",
    "regional_air_capacity_supply",
    "regional_aviation_demand",
    "regional_macro",
    "regional_macro_reconciled",
    "seed_explorer_runs",
    "seed_explorer_viewer",
    "viewer_releases",
}


def _relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT_DIR.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def _measure(path: Path) -> tuple[int, int]:
    if not path.exists():
        return 0, 0
    if path.is_file():
        try:
            return path.stat().st_size, 1
        except OSError:
            return 0, 1
    size = 0
    count = 0
    for child in path.rglob("*"):
        if not child.is_file():
            continue
        count += 1
        try:
            size += child.stat().st_size
        except OSError:
            pass
    return size, count


def _entry(path: Path, category: str, status: str, reason: str) -> dict[str, Any]:
    size, file_count = _measure(path)
    try:
        modified_epoch = path.stat().st_mtime
    except OSError:
        modified_epoch = 0.0
    return {
        "path": _relative(path),
        "category": category,
        "status": status,
        "reason": reason,
        "bytes": size,
        "fileCount": file_count,
        "modifiedEpoch": modified_epoch,
        "modifiedAt": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(modified_epoch)) if modified_epoch else "",
    }


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _cache_metadata_summary(payload: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "seed",
        "years",
        "generatedAt",
        "cacheFingerprintVersion",
        "cacheFingerprint",
        "cachePython",
        "cachePlatform",
    )
    return {key: payload.get(key) for key in keys if key in payload}


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def load_policy() -> dict[str, Any]:
    payload = _read_json(CACHE_POLICY_PATH)
    configured = payload.get("maxCachedRuns", DEFAULT_MAX_CACHED_RUNS)
    environment_value = os.environ.get("AIRPORT_MAX_CACHED_RUNS")
    if environment_value is not None:
        configured = environment_value
    try:
        maximum = max(1, int(configured))
    except (TypeError, ValueError):
        maximum = DEFAULT_MAX_CACHED_RUNS
    configured_viewer_releases = payload.get("maxViewerReleases", DEFAULT_MAX_VIEWER_RELEASES)
    viewer_environment_value = os.environ.get("AIRPORT_MAX_VIEWER_RELEASES")
    if viewer_environment_value is not None:
        configured_viewer_releases = viewer_environment_value
    try:
        maximum_viewer_releases = max(1, int(configured_viewer_releases))
    except (TypeError, ValueError):
        maximum_viewer_releases = DEFAULT_MAX_VIEWER_RELEASES
    pins = sorted(
        {
            str(value).strip()
            for value in payload.get("pinnedRunIds", [])
            if str(value).strip()
        }
    )
    return {
        "schemaVersion": CACHE_POLICY_SCHEMA_VERSION,
        "maxCachedRuns": maximum,
        "maxViewerReleases": maximum_viewer_releases,
        "pinnedRunIds": pins,
        "policyPath": _relative(CACHE_POLICY_PATH),
    }


def _save_policy(policy: dict[str, Any]) -> None:
    _atomic_write_json(
        CACHE_POLICY_PATH,
        {
            "schemaVersion": CACHE_POLICY_SCHEMA_VERSION,
            "maxCachedRuns": int(policy["maxCachedRuns"]),
            "maxViewerReleases": int(policy["maxViewerReleases"]),
            "pinnedRunIds": sorted(set(policy.get("pinnedRunIds", []))),
        },
    )


def pin_cache(run_id: str) -> dict[str, Any]:
    clean_run_id = str(run_id).strip()
    run_path = RUN_ROOT / clean_run_id
    _ensure_inside(RUN_ROOT, run_path)
    if not clean_run_id or not run_path.is_dir() or clean_run_id.startswith(".staging_"):
        raise ValueError(f"Seed cache does not exist: {clean_run_id}")
    policy = load_policy()
    policy["pinnedRunIds"] = sorted(set(policy["pinnedRunIds"]) | {clean_run_id})
    _save_policy(policy)
    return {"ok": True, "runId": clean_run_id, "pinned": True, "policy": load_policy()}


def unpin_cache(run_id: str) -> dict[str, Any]:
    clean_run_id = str(run_id).strip()
    policy = load_policy()
    policy["pinnedRunIds"] = [value for value in policy["pinnedRunIds"] if value != clean_run_id]
    _save_policy(policy)
    return {"ok": True, "runId": clean_run_id, "pinned": False, "policy": load_policy()}


def set_retention(max_cached_runs: int) -> dict[str, Any]:
    try:
        maximum = int(max_cached_runs)
    except (TypeError, ValueError) as error:
        raise ValueError("max cached Runs must be an integer") from error
    if maximum < 1 or maximum > 50:
        raise ValueError("max cached Runs must be between 1 and 50")
    policy = load_policy()
    policy["maxCachedRuns"] = maximum
    _save_policy(policy)
    return {"ok": True, "maxCachedRuns": maximum, "policy": load_policy()}


def set_viewer_retention(max_viewer_releases: int) -> dict[str, Any]:
    try:
        maximum = int(max_viewer_releases)
    except (TypeError, ValueError) as error:
        raise ValueError("max Viewer releases must be an integer") from error
    if maximum < 1 or maximum > 50:
        raise ValueError("max Viewer releases must be between 1 and 50")
    policy = load_policy()
    policy["maxViewerReleases"] = maximum
    _save_policy(policy)
    return {"ok": True, "maxViewerReleases": maximum, "policy": load_policy()}


def _manifest_protection() -> dict[str, Any]:
    manifest_path = OUTPUT_ROOT / "current_viewer_manifest.json"
    manifest = _read_json(manifest_path)
    protected_paths: list[Path] = []
    invalid_paths: list[str] = []
    for key in ("release_path", "source_variant"):
        raw_value = str(manifest.get(key, "")).strip()
        if not raw_value:
            continue
        candidate = (ROOT_DIR / raw_value).resolve()
        try:
            candidate.relative_to(ROOT_DIR.resolve())
        except ValueError:
            invalid_paths.append(raw_value)
            continue
        if key == "release_path":
            try:
                candidate.relative_to(VIEWER_RELEASE_ROOT.resolve())
            except ValueError:
                invalid_paths.append(raw_value)
                continue
            if not candidate.is_dir():
                invalid_paths.append(raw_value)
                continue
        protected_paths.append(candidate)
    valid = bool(manifest) and bool(str(manifest.get("release_path", "")).strip()) and not invalid_paths
    return {
        "manifestPath": _relative(manifest_path),
        "releaseId": manifest.get("release_id"),
        "runId": manifest.get("run_id"),
        "protectedPaths": sorted({_relative(path) for path in protected_paths}),
        "resolvedPaths": protected_paths,
        "valid": valid,
        "invalidPaths": invalid_paths,
    }


def _service_state() -> dict[str, Any]:
    port_open = False
    try:
        with socket.create_connection(("127.0.0.1", 8776), timeout=0.2):
            port_open = True
    except OSError:
        pass
    if not port_open:
        return {"port": 8776, "status": "stopped", "serviceId": None}
    try:
        with urlopen(SERVICE_HEALTH_URL, timeout=0.4) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, URLError, ValueError, json.JSONDecodeError):
        return {"port": 8776, "status": "unknown_listener", "serviceId": None}
    service_id = payload.get("serviceId")
    return {
        "port": 8776,
        "status": "running" if service_id == SERVICE_ID else "unknown_listener",
        "serviceId": service_id,
        "pid": payload.get("servicePid"),
    }


def _is_protected(path: Path, protected_paths: list[Path]) -> bool:
    resolved = path.resolve()
    for protected in protected_paths:
        protected_resolved = protected.resolve()
        if resolved == protected_resolved:
            return True
        try:
            protected_resolved.relative_to(resolved)
            return True
        except ValueError:
            pass
        try:
            resolved.relative_to(protected_resolved)
            return True
        except ValueError:
            pass
    return False


def _current_seed_cache_fingerprint() -> tuple[str | None, str | None]:
    try:
        from airport_sim.server import app

        return (
            app.CACHE_FINGERPRINT_VERSION,
            app.current_cache_fingerprint(),
        )
    except (ImportError, OSError, ValueError):
        return None, None


def list_cache() -> dict[str, Any]:
    policy = load_policy()
    manifest = _manifest_protection()
    protected_paths = list(manifest.pop("resolvedPaths"))
    manifest_valid = bool(manifest.get("valid"))
    entries: list[dict[str, Any]] = []

    run_paths = []
    if RUN_ROOT.exists():
        run_paths = sorted(
            (path for path in RUN_ROOT.iterdir() if path.is_dir()),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
    completed_run_paths = [path for path in run_paths if not path.name.startswith(".staging_")]
    pinned = set(policy["pinnedRunIds"])
    fingerprint_version, fingerprint = _current_seed_cache_fingerprint()
    cache_metadata_by_run = {
        path.name: _read_json(path / "seed_explorer_city_market_cache.json")
        for path in completed_run_paths
    }
    valid_run_paths = [
        path
        for path in completed_run_paths
        if fingerprint is not None
        and cache_metadata_by_run[path.name].get("cacheFingerprintVersion") == fingerprint_version
        and cache_metadata_by_run[path.name].get("cacheFingerprint") == fingerprint
    ]
    automatic_keep = {
        path.name
        for path in [path for path in valid_run_paths if path.name not in pinned][: policy["maxCachedRuns"]]
    }
    save_run_ids = {
        path.parent.name
        for path in SAVE_ROOT.glob("*/dynamic_test_save.json")
        if path.is_file()
    }

    for path in run_paths:
        if path.name.startswith(".staging_"):
            status, reason = "protected", "staging/in-flight directory"
        elif path.name in pinned:
            status, reason = "protected", "explicitly pinned cache"
        elif path not in valid_run_paths:
            status, reason = "deletable", "cache fingerprint is missing or stale"
        elif path.name in automatic_keep:
            status, reason = "keep", f"within newest {policy['maxCachedRuns']} caches"
        else:
            status, reason = "deletable", f"older than newest {policy['maxCachedRuns']} caches"
        metadata = cache_metadata_by_run.get(path.name, {})
        item = _entry(path, "seed_cache", status, reason)
        item.update(
            {
                "runId": path.name,
                "pinned": path.name in pinned,
                "hasSave": path.name in save_run_ids,
                "cacheValid": path in valid_run_paths,
                "cacheMetadata": _cache_metadata_summary(metadata),
            }
        )
        entries.append(item)

    if OUTPUT_ROOT.exists():
        for path in sorted(OUTPUT_ROOT.iterdir(), key=lambda candidate: candidate.name.lower()):
            if not path.is_dir() or path.name in CANONICAL_OUTPUT_NAMES or path.name == "macro_runs":
                continue
            lowered = path.name.lower()
            if _is_protected(path, protected_paths):
                entries.append(_entry(path, "output", "protected", "referenced by current Viewer manifest"))
            elif any(marker in lowered for marker in TEMPORARY_OUTPUT_MARKERS):
                entries.append(_entry(path, "historical_test_output", "deletable", "legacy test/probe output"))
            elif path.name == "seed_explorer_saves" and not any(child.is_file() for child in path.rglob("*")):
                entries.append(_entry(path, "legacy_empty_output", "deletable", "legacy save directory is empty"))
            else:
                entries.append(_entry(path, "output", "review", "unclassified output directory"))

    macro_root = OUTPUT_ROOT / "macro_runs"
    if macro_root.exists():
        for path in sorted(macro_root.iterdir(), key=lambda candidate: candidate.name.lower()):
            if not path.is_dir():
                continue
            lowered = path.name.lower()
            if path.name.startswith(".staging_"):
                entries.append(_entry(path, "macro_run", "protected", "staging/in-flight directory"))
            elif not manifest_valid:
                entries.append(_entry(path, "macro_run", "protected", "Viewer manifest is missing or invalid; failing closed"))
            elif _is_protected(path, protected_paths):
                entries.append(_entry(path, "macro_run", "protected", "source of current Viewer release"))
            elif any(marker in lowered for marker in TEMPORARY_OUTPUT_MARKERS):
                entries.append(_entry(path, "historical_test_output", "deletable", "legacy test/smoke Run"))
            else:
                entries.append(_entry(path, "macro_run", "review", "completed Run retained for manual review"))

    if VIEWER_RELEASE_ROOT.exists():
        current_release_paths = {path.resolve() for path in protected_paths if VIEWER_RELEASE_ROOT.resolve() in path.resolve().parents}
        release_paths = sorted(
            (path for path in VIEWER_RELEASE_ROOT.iterdir() if path.is_dir()),
            key=lambda candidate: (candidate.stat().st_mtime, candidate.name),
            reverse=True,
        )
        backup_slots = max(0, int(policy["maxViewerReleases"]) - len(current_release_paths))
        retained_backup_paths: set[Path] = set()
        for path in release_paths:
            resolved = path.resolve()
            if path.name.startswith(".staging_") or resolved in current_release_paths:
                continue
            if len(retained_backup_paths) >= backup_slots:
                break
            retained_backup_paths.add(resolved)
        for path in release_paths:
            if not path.is_dir():
                continue
            if path.name.startswith(".staging_"):
                entries.append(_entry(path, "viewer_release", "protected", "staging/in-flight release"))
            elif not manifest_valid:
                entries.append(_entry(path, "viewer_release", "protected", "Viewer manifest is missing or invalid; failing closed"))
            elif path.resolve() in current_release_paths:
                entries.append(_entry(path, "viewer_release", "protected", "current Viewer release"))
            elif path.resolve() in retained_backup_paths:
                entries.append(
                    _entry(
                        path,
                        "viewer_release",
                        "keep",
                        f"within newest {policy['maxViewerReleases']} Viewer releases",
                    )
                )
            else:
                entries.append(
                    _entry(
                        path,
                        "viewer_release",
                        "deletable",
                        f"older than newest {policy['maxViewerReleases']} Viewer releases",
                    )
                )

    total_bytes = sum(item["bytes"] for item in entries)
    return {
        "ok": True,
        "schemaVersion": CACHE_INVENTORY_SCHEMA_VERSION,
        "workspaceRoot": str(ROOT_DIR.resolve()),
        "outputRoot": _relative(OUTPUT_ROOT),
        "saveRoot": _relative(SAVE_ROOT),
        "policy": policy,
        "service": _service_state(),
        "currentViewer": manifest,
        "saveCount": len(list(SAVE_ROOT.glob("*/dynamic_test_save.json"))),
        "entries": entries,
        "totalBytes": total_bytes,
    }


def plan_cache() -> dict[str, Any]:
    inventory = list_cache()
    candidates = [dict(item) for item in inventory["entries"] if item["status"] == "deletable"]
    candidates.sort(key=lambda item: (item["category"], item["path"]))
    releasable = sum(item["bytes"] for item in candidates)
    return {
        **inventory,
        "plan": {
            "candidateCount": len(candidates),
            "releasableBytes": releasable,
            "candidates": candidates,
            "blockedBecauseServiceRunning": inventory["service"]["status"] != "stopped",
        },
    }


def _ensure_inside(root: Path, target: Path) -> Path:
    resolved_root = root.resolve()
    resolved_target = target.resolve()
    if resolved_target == resolved_root:
        raise ValueError(f"refusing to operate on root directory: {resolved_root}")
    try:
        resolved_target.relative_to(resolved_root)
    except ValueError as error:
        raise ValueError(f"path is outside allowed root {resolved_root}: {resolved_target}") from error
    return resolved_target


def _delete_target(path: Path) -> None:
    resolved = _ensure_inside(OUTPUT_ROOT, path)
    if resolved.is_dir():
        shutil.rmtree(resolved)
    elif resolved.exists():
        resolved.unlink()


def _refresh_macro_run_index() -> dict[str, Any]:
    from macro_layers.macro_run_orchestrator_sim import write_run_index

    return write_run_index(OUTPUT_ROOT / "macro_runs")


def clean_cache(*, confirm: bool) -> dict[str, Any]:
    plan = plan_cache()
    if not confirm:
        return {**plan, "executed": False, "deleted": [], "releasedBytes": 0}
    if plan["service"]["status"] != "stopped":
        raise RuntimeError("Port 8776 is active; stop the Airport service before destructive cache cleanup")
    deleted: list[dict[str, Any]] = []
    failed: list[dict[str, Any]] = []
    released = 0
    for item in plan["plan"]["candidates"]:
        target = (ROOT_DIR / item["path"]).resolve()
        try:
            _delete_target(target)
        except FileNotFoundError:
            continue
        except OSError as error:
            failed.append(
                {
                    "path": item["path"],
                    "category": item["category"],
                    "error": f"{type(error).__name__}: {error}",
                }
            )
            continue
        deleted.append({"path": item["path"], "category": item["category"], "bytes": item["bytes"]})
        released += int(item["bytes"])
    refreshed_index = None
    if any(item["path"].startswith("output/macro_runs/") for item in deleted):
        try:
            refreshed_index = _refresh_macro_run_index()
        except (OSError, ValueError) as error:
            failed.append(
                {
                    "path": "output/macro_runs/macro_run_index.js",
                    "category": "run_index_refresh",
                    "error": f"{type(error).__name__}: {error}",
                }
            )
    return {
        "ok": True,
        "schemaVersion": CACHE_INVENTORY_SCHEMA_VERSION,
        "executed": True,
        "deleted": deleted,
        "failed": failed,
        "releasedBytes": released,
        "runIndex": refreshed_index,
        "remaining": list_cache(),
    }
