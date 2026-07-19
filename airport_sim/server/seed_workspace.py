from __future__ import annotations

import json
import time
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any


REGISTRY_SCHEMA_VERSION = "airport-seed-workspace-v1"
RESPONSE_SCHEMA_VERSION = "airport-seed-workspace-response-v1"
SAVE_FILENAME = "dynamic_test_save.json"
REGISTRY_LOCK = RLock()

_DISCOVERY_ORDER = ("registry", "viewer_release", "seed_cache", "player_save")


def _integer(value: Any, *, minimum: int, maximum: int | None = None) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    result = value
    if result < minimum or (maximum is not None and result > maximum):
        return None
    return result


def _identity(
    seed: Any,
    years: Any,
    *,
    run_id_for: Callable[[int, int], str],
) -> tuple[str, int, int] | None:
    clean_seed = _integer(seed, minimum=0)
    clean_years = _integer(years, minimum=5, maximum=90)
    if clean_seed is None or clean_years is None:
        return None
    return run_id_for(clean_seed, clean_years), clean_seed, clean_years


def _identity_from_slot_id(
    slot_id: Any,
    *,
    parse_run_id: Callable[[str], tuple[int | None, int | None]],
    run_id_for: Callable[[int, int], str],
) -> tuple[str, int, int] | None:
    clean_slot_id = str(slot_id or "").strip()
    if not clean_slot_id:
        return None
    seed, years = parse_run_id(clean_slot_id)
    identity = _identity(seed, years, run_id_for=run_id_for)
    if identity is None or identity[0] != clean_slot_id:
        return None
    return identity


def _empty_registry() -> dict[str, Any]:
    return {
        "schemaVersion": REGISTRY_SCHEMA_VERSION,
        "revision": 0,
        "activeSlotId": None,
        "slots": [],
    }


def _normalise_registry(
    payload: Any,
    *,
    parse_run_id: Callable[[str], tuple[int | None, int | None]],
    run_id_for: Callable[[int, int], str],
) -> tuple[dict[str, Any], str, list[str]]:
    if not isinstance(payload, dict):
        return _empty_registry(), "invalid", ["Seed 工作区注册表顶层必须是 JSON 对象"]
    if payload.get("schemaVersion") != REGISTRY_SCHEMA_VERSION:
        return _empty_registry(), "invalid", ["Seed 工作区注册表版本不受支持"]

    warnings: list[str] = []
    revision = _integer(payload.get("revision"), minimum=1)
    if revision is None:
        return _empty_registry(), "invalid", ["Seed 工作区注册表 revision 无效"]

    raw_slots = payload.get("slots")
    if not isinstance(raw_slots, list):
        return _empty_registry(), "invalid", ["Seed 工作区注册表 slots 必须是数组"]

    slots: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, raw_slot in enumerate(raw_slots):
        if not isinstance(raw_slot, dict):
            warnings.append(f"注册表槽位 {index} 不是对象，已跳过")
            continue
        identity = _identity(
            raw_slot.get("seed"),
            raw_slot.get("years"),
            run_id_for=run_id_for,
        )
        if identity is None:
            warnings.append(f"注册表槽位 {index} 的 Seed 或年数无效，已跳过")
            continue
        slot_id, seed, years = identity
        supplied_slot_id = str(raw_slot.get("slotId") or "").strip()
        if supplied_slot_id != slot_id:
            warnings.append(f"注册表槽位 {index} 的 slotId 与 Seed/年数不一致，已跳过")
            continue
        if slot_id in seen:
            warnings.append(f"注册表槽位 {slot_id} 重复，已保留第一项")
            continue
        seen.add(slot_id)
        slots.append(
            {
                "slotId": slot_id,
                "seed": seed,
                "years": years,
                "label": str(raw_slot.get("label") or "").strip(),
                "createdAt": str(raw_slot.get("createdAt") or "").strip(),
                "lastUsedAt": str(raw_slot.get("lastUsedAt") or "").strip(),
            }
        )

    active_slot_id: str | None = None
    raw_active = payload.get("activeSlotId")
    if raw_active is not None:
        active_identity = _identity_from_slot_id(
            raw_active,
            parse_run_id=parse_run_id,
            run_id_for=run_id_for,
        )
        if active_identity is None or active_identity[0] not in seen:
            warnings.append("注册表 activeSlotId 没有对应的有效槽位，已忽略")
        else:
            active_slot_id = active_identity[0]

    return (
        {
            "schemaVersion": REGISTRY_SCHEMA_VERSION,
            "revision": revision,
            "activeSlotId": active_slot_id,
            "slots": slots,
        },
        "degraded" if warnings else "ready",
        warnings,
    )


def load_registry(
    *,
    registry_path: Path,
    read_json: Callable[[Path], Any],
    parse_run_id: Callable[[str], tuple[int | None, int | None]],
    run_id_for: Callable[[int, int], str],
) -> tuple[dict[str, Any], str, list[str]]:
    if not registry_path.exists():
        return _empty_registry(), "missing", []
    try:
        payload = read_json(registry_path)
    except (OSError, ValueError, json.JSONDecodeError):
        return (
            _empty_registry(),
            "invalid",
            ["Seed 工作区注册表无法读取；本次仅使用磁盘发现结果，原文件未被覆盖"],
        )
    return _normalise_registry(
        payload,
        parse_run_id=parse_run_id,
        run_id_for=run_id_for,
    )


def write_registry(
    payload: dict[str, Any],
    *,
    registry_path: Path,
    atomic_write_text: Callable[[Path, str], None],
    parse_run_id: Callable[[str], tuple[int | None, int | None]],
    run_id_for: Callable[[int, int], str],
) -> dict[str, Any]:
    """Validate and atomically persist a complete workspace registry snapshot."""
    normalised, status, warnings = _normalise_registry(
        payload,
        parse_run_id=parse_run_id,
        run_id_for=run_id_for,
    )
    if status != "ready" or warnings:
        raise ValueError("Seed 工作区注册表写入内容无效")
    atomic_write_text(
        registry_path,
        json.dumps(normalised, ensure_ascii=False, indent=2) + "\n",
    )
    return normalised


def _relative(path: Path, root_dir: Path) -> str:
    try:
        return path.resolve().relative_to(root_dir.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def _safe_child(parent: Path, child: Path) -> Path | None:
    parent_resolved = parent.resolve()
    child_resolved = child.resolve()
    if parent_resolved == child_resolved or parent_resolved not in child_resolved.parents:
        return None
    return child_resolved


def _measure(path: Path) -> tuple[int, int]:
    if not path.exists():
        return 0, 0
    if path.is_file():
        try:
            return path.stat().st_size, 1
        except OSError:
            return 0, 1
    byte_count = 0
    file_count = 0
    try:
        children = path.rglob("*")
        for child in children:
            if not child.is_file():
                continue
            file_count += 1
            try:
                byte_count += child.stat().st_size
            except OSError:
                continue
    except OSError:
        return byte_count, file_count
    return byte_count, file_count


def _modified(path: Path) -> tuple[float, str]:
    try:
        epoch = path.stat().st_mtime
    except OSError:
        return 0.0, ""
    return epoch, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(epoch))


def _timestamp_epoch(value: Any) -> float:
    clean = str(value or "").strip()
    if not clean:
        return 0.0
    candidates = (clean, clean.replace(" ", "T", 1))
    for candidate in candidates:
        try:
            parsed = datetime.fromisoformat(candidate.replace("Z", "+00:00"))
        except ValueError:
            continue
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.timestamp()
    return 0.0


def _slot_record(slot_id: str, seed: int, years: int) -> dict[str, Any]:
    return {
        "slotId": slot_id,
        "seed": seed,
        "years": years,
        "label": "",
        "createdAt": "",
        "lastUsedAt": "",
        "lastActivityAt": "",
        "_lastActivityEpoch": 0.0,
        "_discoveredFrom": set(),
        "cacheStatus": "missing",
        "cacheRunId": None,
        "cachePath": None,
        "cacheBytes": 0,
        "cacheFileCount": 0,
        "cacheGeneratedAt": "",
        "cacheLastWriteTime": "",
        "hasBeijingOperations": False,
        "isPinnedCache": False,
        "saveStatus": "missing",
        "savePath": None,
        "saveBytes": 0,
        "savedAt": "",
        "isCurrentViewerRelease": False,
        "releaseId": None,
        "releaseRunId": None,
        "releaseVariant": None,
    }


def _note_activity(slot: dict[str, Any], epoch: float, label: Any) -> None:
    if epoch <= float(slot["_lastActivityEpoch"]):
        return
    slot["_lastActivityEpoch"] = epoch
    slot["lastActivityAt"] = str(label or "").strip()


def _discover_save(
    path: Path,
    *,
    read_json: Callable[[Path], Any],
    expected_seed: int,
    expected_years: int,
) -> tuple[str, dict[str, Any]]:
    byte_count, _ = _measure(path)
    epoch, modified_at = _modified(path)
    metadata = {
        "saveBytes": byte_count,
        "savedAt": modified_at,
        "activityEpoch": epoch,
    }
    try:
        payload = read_json(path)
    except (OSError, ValueError, json.JSONDecodeError):
        return "invalid", metadata
    if not isinstance(payload, dict):
        return "invalid", metadata
    seed = _integer(payload.get("seed"), minimum=0)
    years = _integer(payload.get("years"), minimum=5, maximum=90)
    if seed != expected_seed or years != expected_years:
        return "invalid", metadata
    saved_at = str(payload.get("savedAt") or "").strip()
    if saved_at:
        metadata["savedAt"] = saved_at
        metadata["activityEpoch"] = max(epoch, _timestamp_epoch(saved_at))
    return "ready", metadata


def _status_for(slot: dict[str, Any]) -> str:
    if slot["isCurrentViewerRelease"]:
        return "published"
    if slot["cacheStatus"] == "ready":
        return "ready"
    if slot["cacheStatus"] == "stale":
        return "stale"
    if slot["saveStatus"] == "ready":
        return "save_only"
    return "draft"


def seed_workspace_payload(
    *,
    root_dir: Path,
    run_root: Path,
    save_root: Path,
    registry_path: Path,
    read_json: Callable[[Path], Any],
    list_cached_runs: Callable[[], list[dict[str, Any]]],
    current_viewer_release_status: Callable[[], dict[str, Any]],
    cache_retention_policy: Callable[[], dict[str, Any]],
    parse_run_id: Callable[[str], tuple[int | None, int | None]],
    run_id_for: Callable[[int, int], str],
) -> dict[str, Any]:
    registry, registry_status, registry_warnings = load_registry(
        registry_path=registry_path,
        read_json=read_json,
        parse_run_id=parse_run_id,
        run_id_for=run_id_for,
    )
    discovery_warnings: list[str] = []
    slots: dict[str, dict[str, Any]] = {}

    def ensure_slot(seed: Any, years: Any) -> dict[str, Any] | None:
        identity = _identity(seed, years, run_id_for=run_id_for)
        if identity is None:
            return None
        slot_id, clean_seed, clean_years = identity
        return slots.setdefault(slot_id, _slot_record(slot_id, clean_seed, clean_years))

    for registry_slot in registry["slots"]:
        slot = ensure_slot(registry_slot["seed"], registry_slot["years"])
        if slot is None:
            continue
        slot["_discoveredFrom"].add("registry")
        slot["label"] = registry_slot["label"]
        slot["createdAt"] = registry_slot["createdAt"]
        slot["lastUsedAt"] = registry_slot["lastUsedAt"]
        for key in ("createdAt", "lastUsedAt"):
            value = registry_slot[key]
            _note_activity(slot, _timestamp_epoch(value), value)

    release = current_viewer_release_status()
    release_slot: dict[str, Any] | None = None
    if release.get("mode") == "versioned_release" and str(release.get("releaseId") or "").strip():
        release_slot = ensure_slot(release.get("seed"), release.get("years"))
        if release_slot is None:
            discovery_warnings.append("当前 Viewer Release 的 Seed 或年数无效，未加入工作区")
        else:
            release_slot["_discoveredFrom"].add("viewer_release")
            release_slot["isCurrentViewerRelease"] = True
            release_slot["releaseId"] = str(release.get("releaseId") or "").strip()
            release_slot["releaseRunId"] = release.get("runId")
            release_slot["releaseVariant"] = release.get("variant")
            _note_activity(
                release_slot,
                _timestamp_epoch(release.get("generatedAt")),
                release.get("generatedAt"),
            )

    policy = cache_retention_policy()
    pinned_run_ids = {
        str(value).strip()
        for value in policy.get("pinnedRunIds", [])
        if str(value).strip()
    }
    for index, cache_entry in enumerate(list_cached_runs()):
        if not isinstance(cache_entry, dict):
            discovery_warnings.append(f"缓存清单条目 {index} 不是对象，已跳过")
            continue
        identity = _identity(
            cache_entry.get("seed"),
            cache_entry.get("years"),
            run_id_for=run_id_for,
        )
        if identity is None:
            run_seed, run_years = parse_run_id(str(cache_entry.get("runId") or ""))
            identity = _identity(run_seed, run_years, run_id_for=run_id_for)
        if identity is None:
            discovery_warnings.append(f"缓存清单条目 {index} 没有可识别的 Seed/年数，已跳过")
            continue
        slot_id, seed, years = identity
        run_id = str(cache_entry.get("runId") or "").strip()
        if run_id != slot_id:
            discovery_warnings.append(f"缓存 {run_id or index} 的 Run ID 与 Seed/年数不一致，已跳过")
            continue
        run_path = _safe_child(run_root, run_root / run_id)
        if run_path is None or not run_path.is_dir():
            discovery_warnings.append(f"缓存 {run_id} 的目录不存在或越界，已跳过")
            continue
        slot = ensure_slot(seed, years)
        if slot is None:
            continue
        slot["_discoveredFrom"].add("seed_cache")
        byte_count, file_count = _measure(run_path)
        modified_epoch, modified_at = _modified(run_path)
        cache_status = "ready" if cache_entry.get("cacheStatus") == "valid" else "stale"
        if (
            slot["cacheStatus"] == "missing"
            or cache_status == "ready"
            or modified_epoch > float(slot["_lastActivityEpoch"])
        ):
            slot["cacheStatus"] = cache_status
            slot["cacheRunId"] = run_id
            slot["cachePath"] = _relative(run_path, root_dir)
            slot["cacheBytes"] = byte_count
            slot["cacheFileCount"] = file_count
            slot["cacheGeneratedAt"] = str(cache_entry.get("generatedAt") or "")
            slot["cacheLastWriteTime"] = str(cache_entry.get("lastWriteTime") or modified_at)
            slot["hasBeijingOperations"] = bool(cache_entry.get("hasBeijingOperations"))
            slot["isPinnedCache"] = run_id in pinned_run_ids
        _note_activity(slot, modified_epoch, modified_at)

    if save_root.exists():
        try:
            save_paths = sorted(save_root.glob(f"*/{SAVE_FILENAME}"), key=lambda path: path.as_posix())
        except OSError:
            save_paths = []
            discovery_warnings.append("玩家存档目录无法读取")
        for save_path in save_paths:
            identity = _identity_from_slot_id(
                save_path.parent.name,
                parse_run_id=parse_run_id,
                run_id_for=run_id_for,
            )
            if identity is None:
                discovery_warnings.append(f"存档目录 {save_path.parent.name} 不是规范槽位，已跳过")
                continue
            _, seed, years = identity
            safe_path = _safe_child(save_root, save_path)
            if safe_path is None or not safe_path.is_file():
                discovery_warnings.append(f"存档 {save_path.parent.name} 不存在或越界，已跳过")
                continue
            slot = ensure_slot(seed, years)
            if slot is None:
                continue
            slot["_discoveredFrom"].add("player_save")
            save_status, save_metadata = _discover_save(
                safe_path,
                read_json=read_json,
                expected_seed=seed,
                expected_years=years,
            )
            slot["saveStatus"] = save_status
            slot["savePath"] = _relative(safe_path, root_dir)
            slot["saveBytes"] = save_metadata["saveBytes"]
            slot["savedAt"] = save_metadata["savedAt"]
            _note_activity(
                slot,
                float(save_metadata["activityEpoch"]),
                save_metadata["savedAt"],
            )
            if save_status == "invalid":
                discovery_warnings.append(f"存档 {save_path.parent.name} 内容无效，已作为损坏存档标记")

    active_slot_id: str | None = None
    active_selection_source = "none"
    registered_active = registry.get("activeSlotId")
    if registered_active in slots:
        active_slot_id = str(registered_active)
        active_selection_source = "registry"
    else:
        ready_caches = [slot for slot in slots.values() if slot["cacheStatus"] == "ready"]
        if ready_caches:
            selected = max(
                ready_caches,
                key=lambda slot: (float(slot["_lastActivityEpoch"]), slot["slotId"]),
            )
            active_slot_id = selected["slotId"]
            active_selection_source = "newest_ready_cache"
        elif release_slot is not None:
            active_slot_id = release_slot["slotId"]
            active_selection_source = "current_viewer_release"
        else:
            ready_saves = [slot for slot in slots.values() if slot["saveStatus"] == "ready"]
            if ready_saves:
                selected = max(
                    ready_saves,
                    key=lambda slot: (float(slot["_lastActivityEpoch"]), slot["slotId"]),
                )
                active_slot_id = selected["slotId"]
                active_selection_source = "newest_player_save"
            else:
                registered_slots = [
                    slot for slot in slots.values() if "registry" in slot["_discoveredFrom"]
                ]
                if registered_slots:
                    selected = max(
                        registered_slots,
                        key=lambda slot: (float(slot["_lastActivityEpoch"]), slot["slotId"]),
                    )
                    active_slot_id = selected["slotId"]
                    active_selection_source = "newest_registry_slot"

    response_slots: list[dict[str, Any]] = []
    for slot in slots.values():
        is_active = slot["slotId"] == active_slot_id
        available_sources: list[str] = []
        if slot["isCurrentViewerRelease"]:
            available_sources.append("viewer_release")
        if slot["cacheStatus"] == "ready":
            available_sources.append("seed_cache")
        if slot["saveStatus"] == "ready":
            available_sources.append("player_save")
        protected_reasons: list[str] = []
        if is_active:
            protected_reasons.append("active_slot")
        if slot["isCurrentViewerRelease"]:
            protected_reasons.append("current_viewer_release")
        if slot["isPinnedCache"]:
            protected_reasons.append("pinned_cache")

        can_open_release_viewers = bool(slot["isCurrentViewerRelease"])
        can_open_cache_viewers = slot["cacheStatus"] == "ready"
        can_open_city_markets = can_open_release_viewers or can_open_cache_viewers
        response_slots.append(
            {
                "slotId": slot["slotId"],
                "seed": slot["seed"],
                "years": slot["years"],
                "label": slot["label"],
                "status": _status_for(slot),
                "isActive": is_active,
                "discoveredFrom": [
                    source for source in _DISCOVERY_ORDER if source in slot["_discoveredFrom"]
                ],
                "createdAt": slot["createdAt"],
                "lastUsedAt": slot["lastUsedAt"],
                "lastActivityAt": slot["lastActivityAt"],
                "cacheStatus": slot["cacheStatus"],
                "cacheRunId": slot["cacheRunId"],
                "cachePath": slot["cachePath"],
                "cacheBytes": slot["cacheBytes"],
                "cacheFileCount": slot["cacheFileCount"],
                "cacheGeneratedAt": slot["cacheGeneratedAt"],
                "cacheLastWriteTime": slot["cacheLastWriteTime"],
                "hasBeijingOperations": slot["hasBeijingOperations"],
                "isPinnedCache": slot["isPinnedCache"],
                "saveStatus": slot["saveStatus"],
                "hasPlayerSave": slot["saveStatus"] == "ready",
                "savePath": slot["savePath"],
                "saveBytes": slot["saveBytes"],
                "savedAt": slot["savedAt"],
                "isCurrentViewerRelease": slot["isCurrentViewerRelease"],
                "releaseId": slot["releaseId"],
                "releaseRunId": slot["releaseRunId"],
                "releaseVariant": slot["releaseVariant"],
                "viewerSource": (
                    "viewer_release"
                    if can_open_release_viewers
                    else "seed_cache" if slot["cacheStatus"] == "ready" else "unavailable"
                ),
                "availableSources": available_sources,
                "canOpenOperations": (
                    slot["cacheStatus"] == "ready" and slot["hasBeijingOperations"]
                ),
                "canOpenGlobal": can_open_release_viewers or can_open_cache_viewers,
                "canOpenCityMarkets": can_open_city_markets,
                "canOpenForecastPlayer": can_open_release_viewers or can_open_cache_viewers,
                "canOpenForecastAudit": can_open_release_viewers or can_open_cache_viewers,
                "protectedReasons": protected_reasons,
                "_lastActivityEpoch": slot["_lastActivityEpoch"],
            }
        )

    response_slots.sort(
        key=lambda slot: (
            not bool(slot["isActive"]),
            -float(slot["_lastActivityEpoch"]),
            str(slot["slotId"]),
        )
    )
    for slot in response_slots:
        slot.pop("_lastActivityEpoch", None)

    ready_cache_count = sum(slot["cacheStatus"] == "ready" for slot in response_slots)
    stale_cache_count = sum(slot["cacheStatus"] == "stale" for slot in response_slots)
    save_count = sum(slot["hasPlayerSave"] for slot in response_slots)
    invalid_save_count = sum(slot["saveStatus"] == "invalid" for slot in response_slots)
    published_slot_count = sum(slot["isCurrentViewerRelease"] for slot in response_slots)
    total_cache_bytes = sum(int(slot["cacheBytes"]) for slot in response_slots)
    total_cache_file_count = sum(int(slot["cacheFileCount"]) for slot in response_slots)
    try:
        max_cached_runs = max(1, int(policy.get("maxCachedRuns", 1)))
    except (TypeError, ValueError):
        max_cached_runs = 1

    return {
        "ok": True,
        "schemaVersion": RESPONSE_SCHEMA_VERSION,
        "workspaceRevision": int(registry["revision"]),
        "activeSlotId": active_slot_id,
        "activeSelectionSource": active_selection_source,
        "registry": {
            "schemaVersion": REGISTRY_SCHEMA_VERSION,
            "status": registry_status,
            "path": _relative(registry_path, root_dir),
            "warningCount": len(registry_warnings),
            "warnings": registry_warnings,
        },
        "retention": {
            "maxCachedRuns": max_cached_runs,
            "pinnedRunIds": sorted(pinned_run_ids),
            "cacheCount": ready_cache_count + stale_cache_count,
            "readyCacheCount": ready_cache_count,
            "staleCacheCount": stale_cache_count,
            "totalCacheBytes": total_cache_bytes,
            "totalCacheFileCount": total_cache_file_count,
        },
        "counts": {
            "slotCount": len(response_slots),
            "playerSaveCount": save_count,
            "invalidSaveCount": invalid_save_count,
            "publishedSlotCount": published_slot_count,
        },
        "viewerRelease": release,
        "discoveryWarningCount": len(discovery_warnings),
        "discoveryWarnings": discovery_warnings,
        "slots": response_slots,
    }


def initialise_registry_if_missing(
    workspace: dict[str, Any],
    *,
    registry_path: Path,
    read_json: Callable[[Path], Any],
    atomic_write_text: Callable[[Path, str], None],
    parse_run_id: Callable[[str], tuple[int | None, int | None]],
    run_id_for: Callable[[int, int], str],
    clock: Callable[[], float] = time.time,
) -> dict[str, Any]:
    with REGISTRY_LOCK:
        _, status, warnings = load_registry(
            registry_path=registry_path,
            read_json=read_json,
            parse_run_id=parse_run_id,
            run_id_for=run_id_for,
        )
        if status != "missing":
            return {
                "created": False,
                "status": status,
                "path": str(registry_path),
                "warnings": warnings,
            }

        now = datetime.fromtimestamp(clock(), timezone.utc).isoformat().replace("+00:00", "Z")
        registry_slots = [
            {
                "slotId": slot["slotId"],
                "seed": slot["seed"],
                "years": slot["years"],
                "label": slot.get("label", ""),
                "createdAt": now,
                "lastUsedAt": now if slot["slotId"] == workspace.get("activeSlotId") else "",
            }
            for slot in workspace.get("slots", [])
        ]
        payload = {
            "schemaVersion": REGISTRY_SCHEMA_VERSION,
            "revision": 1,
            "activeSlotId": workspace.get("activeSlotId"),
            "slots": registry_slots,
        }
        normalised, normalised_status, normalised_warnings = _normalise_registry(
            payload,
            parse_run_id=parse_run_id,
            run_id_for=run_id_for,
        )
        if normalised_status != "ready":
            raise ValueError("cannot initialise invalid Seed workspace registry")
        try:
            atomic_write_text(
                registry_path,
                json.dumps(normalised, ensure_ascii=False, indent=2) + "\n",
            )
        except OSError:
            return {
                "created": False,
                "status": "missing",
                "path": str(registry_path),
                "warnings": ["Seed 工作区注册表无法写入；服务将继续使用只读磁盘发现结果"],
            }
        return {
            "created": True,
            "status": "ready",
            "path": str(registry_path),
            "warnings": normalised_warnings,
        }
