from __future__ import annotations

import hashlib
import json
import secrets
import shutil
import time
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, ContextManager

from . import seed_workspace


ACTION_RESPONSE_SCHEMA_VERSION = "airport-seed-workspace-action-response-v1"
MIN_RANDOM_SEED = 20_260_000
RANDOM_SEED_COUNT = 2_000
MAX_LABEL_LENGTH = 80


def _integer(
    value: Any,
    *,
    label: str,
    minimum: int,
    maximum: int | None = None,
) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{label} 必须是整数")
    try:
        result = int(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{label} 必须是整数") from error
    if result < minimum or (maximum is not None and result > maximum):
        suffix = f" 至 {maximum}" if maximum is not None else "以上"
        raise ValueError(f"{label} 必须在 {minimum}{suffix}")
    return result


def _seed(value: Any) -> int:
    return _integer(value, label="Seed", minimum=0)


def _years(value: Any) -> int:
    return _integer(value, label="年数", minimum=5, maximum=90)


def _retention(value: Any) -> int:
    return _integer(value, label="缓存保留上限", minimum=1, maximum=50)


def _label(value: Any) -> str:
    result = str(value or "").strip()
    if len(result) > MAX_LABEL_LENGTH:
        raise ValueError(f"槽位名称不能超过 {MAX_LABEL_LENGTH} 个字符")
    return result


def _timestamp(clock: Callable[[], float]) -> str:
    return datetime.fromtimestamp(clock(), timezone.utc).isoformat().replace("+00:00", "Z")


def _measure(path: Path) -> tuple[int, int]:
    if path.is_file():
        return path.stat().st_size, 1
    byte_count = 0
    file_count = 0
    for child in path.rglob("*"):
        if not child.is_file():
            continue
        file_count += 1
        byte_count += child.stat().st_size
    return byte_count, file_count


def _safe_child(parent: Path, child: Path, *, exact_name: str) -> Path:
    parent_resolved = parent.resolve()
    child_resolved = child.resolve()
    if child_resolved.name != exact_name or parent_resolved not in child_resolved.parents:
        raise ValueError("目标路径不在允许的 Seed 槽位边界内")
    return child_resolved


def _relative(path: Path, root_dir: Path) -> str:
    return path.resolve().relative_to(root_dir.resolve()).as_posix()


def _plan_id(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _require_confirmation(body: dict[str, Any]) -> None:
    if body.get("confirm") is not True:
        raise ValueError("执行清理前必须明确确认")
    supplied = str(body.get("planId") or "").strip()
    if not supplied:
        raise ValueError("执行清理前必须提供预览计划 planId")


def _slot(workspace: dict[str, Any], slot_id: Any) -> dict[str, Any]:
    clean_slot_id = str(slot_id or "").strip()
    for candidate in workspace.get("slots", []):
        if candidate.get("slotId") == clean_slot_id:
            return candidate
    raise FileNotFoundError("Seed 槽位不存在")


def _registry(
    *,
    registry_path: Path,
    read_json: Callable[[Path], Any],
    parse_run_id: Callable[[str], tuple[int | None, int | None]],
    run_id_for: Callable[[int, int], str],
) -> dict[str, Any]:
    payload, status, _ = seed_workspace.load_registry(
        registry_path=registry_path,
        read_json=read_json,
        parse_run_id=parse_run_id,
        run_id_for=run_id_for,
    )
    if status != "ready":
        raise FileExistsError("Seed 工作区注册表不是可写状态；请先修复注册表警告")
    return payload


def _check_revision(body: dict[str, Any], registry: dict[str, Any]) -> int:
    expected = _integer(
        body.get("expectedRevision"),
        label="expectedRevision",
        minimum=1,
    )
    actual = int(registry["revision"])
    if expected != actual:
        raise FileExistsError(
            f"Seed 工作区已被其他操作更新（当前 revision {actual}）；请刷新后重试"
        )
    return actual


def _persist_registry(
    registry: dict[str, Any],
    *,
    registry_path: Path,
    atomic_write_text: Callable[[Path, str], None],
    parse_run_id: Callable[[str], tuple[int | None, int | None]],
    run_id_for: Callable[[int, int], str],
) -> dict[str, Any]:
    registry["revision"] = int(registry["revision"]) + 1
    return seed_workspace.write_registry(
        registry,
        registry_path=registry_path,
        atomic_write_text=atomic_write_text,
        parse_run_id=parse_run_id,
        run_id_for=run_id_for,
    )


def _response(
    action: str,
    *,
    changed: bool,
    workspace_revision: int,
    active_slot_id: str | None,
    message: str,
    **extra: Any,
) -> dict[str, Any]:
    return {
        "ok": True,
        "schemaVersion": ACTION_RESPONSE_SCHEMA_VERSION,
        "action": action,
        "changed": changed,
        "workspaceRevision": workspace_revision,
        "activeSlotId": active_slot_id,
        "message": message,
        **extra,
    }


def _delete_plan(
    workspace: dict[str, Any],
    *,
    slot_id: Any,
    target: Any,
    root_dir: Path,
    run_root: Path,
    save_root: Path,
) -> dict[str, Any]:
    slot = _slot(workspace, slot_id)
    clean_target = str(target or "").strip().lower()
    if clean_target not in {"cache", "save"}:
        raise ValueError("删除目标必须是 cache 或 save")

    blockers = list(slot.get("protectedReasons", []))
    preserves: list[str] = []
    if clean_target == "cache":
        path = _safe_child(
            run_root,
            run_root / str(slot["slotId"]),
            exact_name=str(slot["slotId"]),
        )
        exists = path.is_dir()
        if slot.get("hasPlayerSave"):
            preserves.append("player_save")
        preserves.append("viewer_release")
        missing_reason = "cache_missing"
    else:
        save_dir = _safe_child(
            save_root,
            save_root / str(slot["slotId"]),
            exact_name=str(slot["slotId"]),
        )
        path = _safe_child(
            save_dir,
            save_dir / seed_workspace.SAVE_FILENAME,
            exact_name=seed_workspace.SAVE_FILENAME,
        )
        exists = path.is_file()
        if slot.get("cacheStatus") != "missing":
            preserves.append("seed_cache")
        preserves.append("viewer_release")
        missing_reason = "save_missing"
    if not exists:
        blockers.append(missing_reason)

    byte_count, file_count = _measure(path) if exists else (0, 0)
    modified_ns = path.stat().st_mtime_ns if exists else 0
    basis = {
        "kind": "delete",
        "workspaceRevision": int(workspace["workspaceRevision"]),
        "slotId": slot["slotId"],
        "target": clean_target,
        "path": _relative(path, root_dir),
        "bytes": byte_count,
        "fileCount": file_count,
        "modifiedNs": modified_ns,
        "blockers": sorted(set(blockers)),
    }
    return {
        **basis,
        "planId": _plan_id(basis),
        "canExecute": not blockers,
        "preserves": sorted(set(preserves)),
    }


def _retention_plan(
    workspace: dict[str, Any],
    *,
    maximum: int,
    root_dir: Path,
    run_root: Path,
) -> dict[str, Any]:
    eligible_ready: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    protected: list[dict[str, Any]] = []
    for slot in workspace.get("slots", []):
        if slot.get("cacheStatus") == "missing":
            continue
        path = _safe_child(
            run_root,
            run_root / str(slot["slotId"]),
            exact_name=str(slot["slotId"]),
        )
        if not path.is_dir():
            continue
        byte_count, file_count = _measure(path)
        item = {
            "slotId": slot["slotId"],
            "path": _relative(path, root_dir),
            "cacheStatus": slot["cacheStatus"],
            "bytes": byte_count,
            "fileCount": file_count,
            "modifiedNs": path.stat().st_mtime_ns,
            "hasPlayerSave": bool(slot.get("hasPlayerSave")),
        }
        blockers = list(slot.get("protectedReasons", []))
        if blockers:
            protected.append({**item, "blockers": blockers})
        elif slot.get("cacheStatus") == "stale":
            candidates.append(item)
        else:
            eligible_ready.append(item)

    eligible_ready.sort(key=lambda item: (int(item["modifiedNs"]), item["slotId"]), reverse=True)
    candidates.extend(eligible_ready[maximum:])
    candidates.sort(key=lambda item: (item["cacheStatus"] != "stale", item["slotId"]))
    basis = {
        "kind": "retention",
        "workspaceRevision": int(workspace["workspaceRevision"]),
        "maxCachedRuns": maximum,
        "candidates": candidates,
    }
    return {
        **basis,
        "planId": _plan_id(basis),
        "candidateCount": len(candidates),
        "reclaimableBytes": sum(int(item["bytes"]) for item in candidates),
        "protected": protected,
    }


def handle_action(
    body: dict[str, Any],
    *,
    root_dir: Path,
    run_root: Path,
    save_root: Path,
    registry_path: Path,
    read_json: Callable[[Path], Any],
    atomic_write_text: Callable[[Path, str], None],
    workspace_payload: Callable[[], dict[str, Any]],
    parse_run_id: Callable[[str], tuple[int | None, int | None]],
    run_id_for: Callable[[int, int], str],
    try_lock_for_run: Callable[[str], ContextManager[bool]],
    set_cache_retention: Callable[[int], dict[str, Any]],
    clock: Callable[[], float] = time.time,
    random_below: Callable[[int], int] = secrets.randbelow,
) -> dict[str, Any]:
    action = str(body.get("action") or "").strip().lower()
    supported = {
        "create-random",
        "import",
        "activate",
        "remove-slot",
        "plan-delete",
        "delete",
        "plan-retention",
        "set-retention",
        "apply-retention",
    }
    if action not in supported:
        raise ValueError("不支持的 Seed 工作区操作")

    with seed_workspace.REGISTRY_LOCK:
        workspace = workspace_payload()
        registry = _registry(
            registry_path=registry_path,
            read_json=read_json,
            parse_run_id=parse_run_id,
            run_id_for=run_id_for,
        )

        if action == "plan-delete":
            plan = _delete_plan(
                workspace,
                slot_id=body.get("slotId"),
                target=body.get("target"),
                root_dir=root_dir,
                run_root=run_root,
                save_root=save_root,
            )
            return _response(
                action,
                changed=False,
                workspace_revision=int(registry["revision"]),
                active_slot_id=registry.get("activeSlotId"),
                message="清理预览已生成；尚未删除任何文件",
                plan=plan,
            )

        if action == "plan-retention":
            maximum = _retention(body.get("maxCachedRuns"))
            plan = _retention_plan(
                workspace,
                maximum=maximum,
                root_dir=root_dir,
                run_root=run_root,
            )
            return _response(
                action,
                changed=False,
                workspace_revision=int(registry["revision"]),
                active_slot_id=registry.get("activeSlotId"),
                message="保留策略预览已生成；尚未删除任何文件",
                plan=plan,
            )

        _check_revision(body, registry)

        if action in {"create-random", "import"}:
            years = _years(body.get("years", 60))
            if action == "create-random":
                occupied = {str(slot.get("slotId")) for slot in workspace.get("slots", [])}
                start = random_below(RANDOM_SEED_COUNT)
                selected_seed: int | None = None
                for offset in range(RANDOM_SEED_COUNT):
                    candidate = MIN_RANDOM_SEED + ((start + offset) % RANDOM_SEED_COUNT)
                    if run_id_for(candidate, years) not in occupied:
                        selected_seed = candidate
                        break
                if selected_seed is None:
                    raise FileExistsError("当前年数的随机 Seed 槽位已经用尽")
                seed = selected_seed
            else:
                seed = _seed(body.get("seed"))
            slot_id = run_id_for(seed, years)
            now = _timestamp(clock)
            existing = next(
                (slot for slot in registry["slots"] if slot["slotId"] == slot_id),
                None,
            )
            created = existing is None
            if existing is None:
                existing = {
                    "slotId": slot_id,
                    "seed": seed,
                    "years": years,
                    "label": _label(body.get("label")),
                    "createdAt": now,
                    "lastUsedAt": "",
                }
                registry["slots"].append(existing)
            elif body.get("label") is not None:
                existing["label"] = _label(body.get("label"))
            activate = body.get("activate", True) is not False
            if activate:
                registry["activeSlotId"] = slot_id
                existing["lastUsedAt"] = now
            persisted = _persist_registry(
                registry,
                registry_path=registry_path,
                atomic_write_text=atomic_write_text,
                parse_run_id=parse_run_id,
                run_id_for=run_id_for,
            )
            return _response(
                action,
                changed=True,
                workspace_revision=int(persisted["revision"]),
                active_slot_id=persisted.get("activeSlotId"),
                message="Seed 槽位已创建并激活" if created and activate else "Seed 槽位已保存",
                slotId=slot_id,
                seed=seed,
                years=years,
                created=created,
            )

        if action == "activate":
            slot = _slot(workspace, body.get("slotId"))
            slot_id = str(slot["slotId"])
            now = _timestamp(clock)
            registered = next(
                (item for item in registry["slots"] if item["slotId"] == slot_id),
                None,
            )
            if registered is None:
                registered = {
                    "slotId": slot_id,
                    "seed": slot["seed"],
                    "years": slot["years"],
                    "label": str(slot.get("label") or ""),
                    "createdAt": now,
                    "lastUsedAt": now,
                }
                registry["slots"].append(registered)
            else:
                registered["lastUsedAt"] = now
            changed = registry.get("activeSlotId") != slot_id
            registry["activeSlotId"] = slot_id
            persisted = _persist_registry(
                registry,
                registry_path=registry_path,
                atomic_write_text=atomic_write_text,
                parse_run_id=parse_run_id,
                run_id_for=run_id_for,
            )
            return _response(
                action,
                changed=changed,
                workspace_revision=int(persisted["revision"]),
                active_slot_id=slot_id,
                message="当前 Seed 已切换",
                slotId=slot_id,
            )

        if action == "remove-slot":
            slot = _slot(workspace, body.get("slotId"))
            slot_id = str(slot["slotId"])
            if slot.get("isActive"):
                raise FileExistsError("活动槽位不能移除；请先切换到其他 Seed")
            if set(slot.get("discoveredFrom", [])) != {"registry"}:
                raise FileExistsError("只有不含缓存、存档和 Release 的空草稿槽位可以直接移除")
            before = len(registry["slots"])
            registry["slots"] = [item for item in registry["slots"] if item["slotId"] != slot_id]
            if len(registry["slots"]) == before:
                raise FileNotFoundError("Seed 槽位没有注册表记录")
            persisted = _persist_registry(
                registry,
                registry_path=registry_path,
                atomic_write_text=atomic_write_text,
                parse_run_id=parse_run_id,
                run_id_for=run_id_for,
            )
            return _response(
                action,
                changed=True,
                workspace_revision=int(persisted["revision"]),
                active_slot_id=persisted.get("activeSlotId"),
                message="空草稿槽位已移除",
                slotId=slot_id,
            )

        if action == "delete":
            _require_confirmation(body)
            plan = _delete_plan(
                workspace,
                slot_id=body.get("slotId"),
                target=body.get("target"),
                root_dir=root_dir,
                run_root=run_root,
                save_root=save_root,
            )
            if not plan["canExecute"]:
                raise FileExistsError("清理目标受保护或已经不存在；请刷新后重新预览")
            if str(body.get("planId")) != plan["planId"]:
                raise FileExistsError("清理目标在预览后发生变化；请重新预览")
            slot_id = str(plan["slotId"])
            with try_lock_for_run(slot_id) as reserved:
                if not reserved:
                    raise FileExistsError("当前 Seed 正在生成或写入，暂时不能清理")
                refreshed = _delete_plan(
                    workspace_payload(),
                    slot_id=slot_id,
                    target=plan["target"],
                    root_dir=root_dir,
                    run_root=run_root,
                    save_root=save_root,
                )
                if refreshed["planId"] != plan["planId"] or not refreshed["canExecute"]:
                    raise FileExistsError("清理目标在预览后发生变化；请重新预览")
                path = root_dir / str(plan["path"])
                if plan["target"] == "cache":
                    shutil.rmtree(path)
                else:
                    path.unlink()
            persisted = _persist_registry(
                registry,
                registry_path=registry_path,
                atomic_write_text=atomic_write_text,
                parse_run_id=parse_run_id,
                run_id_for=run_id_for,
            )
            return _response(
                action,
                changed=True,
                workspace_revision=int(persisted["revision"]),
                active_slot_id=persisted.get("activeSlotId"),
                message="Seed 缓存已清理" if plan["target"] == "cache" else "玩家存档已删除",
                deleted={
                    "slotId": slot_id,
                    "target": plan["target"],
                    "path": plan["path"],
                    "releasedBytes": plan["bytes"],
                    "preserved": plan["preserves"],
                },
            )

        maximum = _retention(body.get("maxCachedRuns"))
        if action == "set-retention":
            result = set_cache_retention(maximum)
            persisted = _persist_registry(
                registry,
                registry_path=registry_path,
                atomic_write_text=atomic_write_text,
                parse_run_id=parse_run_id,
                run_id_for=run_id_for,
            )
            return _response(
                action,
                changed=True,
                workspace_revision=int(persisted["revision"]),
                active_slot_id=persisted.get("activeSlotId"),
                message="缓存保留上限已保存；没有立即删除文件",
                retention=result.get("policy", result),
            )

        _require_confirmation(body)
        plan = _retention_plan(
            workspace,
            maximum=maximum,
            root_dir=root_dir,
            run_root=run_root,
        )
        if str(body.get("planId")) != plan["planId"]:
            raise FileExistsError("缓存保留计划在预览后发生变化；请重新预览")
        deleted: list[dict[str, Any]] = []
        blocked: list[dict[str, str]] = []
        for candidate in plan["candidates"]:
            slot_id = str(candidate["slotId"])
            with try_lock_for_run(slot_id) as reserved:
                if not reserved:
                    blocked.append({"slotId": slot_id, "reason": "run_active"})
                    continue
                path = _safe_child(run_root, run_root / slot_id, exact_name=slot_id)
                if not path.is_dir():
                    blocked.append({"slotId": slot_id, "reason": "cache_missing"})
                    continue
                byte_count, file_count = _measure(path)
                if (
                    byte_count != candidate["bytes"]
                    or file_count != candidate["fileCount"]
                    or path.stat().st_mtime_ns != candidate["modifiedNs"]
                ):
                    blocked.append({"slotId": slot_id, "reason": "changed_since_preview"})
                    continue
                shutil.rmtree(path)
                deleted.append(
                    {
                        "slotId": slot_id,
                        "path": candidate["path"],
                        "releasedBytes": byte_count,
                        "preserved": ["player_save", "viewer_release"],
                    }
                )
        retention_result = set_cache_retention(maximum)
        persisted = _persist_registry(
            registry,
            registry_path=registry_path,
            atomic_write_text=atomic_write_text,
            parse_run_id=parse_run_id,
            run_id_for=run_id_for,
        )
        return _response(
            action,
            changed=bool(deleted) or maximum != workspace["retention"]["maxCachedRuns"],
            workspace_revision=int(persisted["revision"]),
            active_slot_id=persisted.get("activeSlotId"),
            message="缓存保留策略已应用",
            retention=retention_result.get("policy", retention_result),
            deleted=deleted,
            blocked=blocked,
            releasedBytes=sum(int(item["releasedBytes"]) for item in deleted),
        )
