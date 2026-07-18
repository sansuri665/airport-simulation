from __future__ import annotations

import json
import sys
from argparse import ArgumentParser, Namespace
from importlib import import_module
from typing import Any


def configure_cache_parser(parser: ArgumentParser) -> None:
    actions = parser.add_subparsers(dest="cache_action", required=True)

    list_parser = actions.add_parser("list", help="List cache inventory without changing files.")
    _add_output_option(list_parser)

    plan_parser = actions.add_parser("plan", help="Preview protected and removable cache entries.")
    _add_output_option(plan_parser)

    clean_parser = actions.add_parser("clean", help="Preview first, then clean cache after confirmation.")
    clean_parser.add_argument(
        "--confirm",
        action="store_true",
        help="Execute the displayed plan without an interactive prompt.",
    )
    _add_output_option(clean_parser)

    pin_parser = actions.add_parser("pin", help="Protect one cache Run from automatic cleanup.")
    pin_parser.add_argument("run_id", metavar="RUN_ID")
    _add_output_option(pin_parser)

    unpin_parser = actions.add_parser("unpin", help="Remove explicit protection from one cache Run.")
    unpin_parser.add_argument("run_id", metavar="RUN_ID")
    _add_output_option(unpin_parser)

    retention_parser = actions.add_parser("retention", help="Set how many newest valid caches are retained.")
    retention_parser.add_argument("max_runs", metavar="MAX_RUNS", type=int)
    _add_output_option(retention_parser)

    viewer_retention_parser = actions.add_parser(
        "viewer-retention",
        help="Set how many newest Viewer releases are retained, including the current release.",
    )
    viewer_retention_parser.add_argument("max_releases", metavar="MAX_RELEASES", type=int)
    _add_output_option(viewer_retention_parser)


def _add_output_option(parser: ArgumentParser) -> None:
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output.")


def _cache_service() -> Any:
    # Import lazily so help and non-cache commands remain usable even while the
    # lifecycle service is being migrated behind this stable command contract.
    return import_module("airport_sim.cache_service")


def _print_payload(payload: dict[str, Any], *, json_output: bool) -> None:
    if json_output:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
        return
    if "result" in payload and "plan" in payload:
        _print_payload(payload["plan"], json_output=False)
        _print_payload(payload["result"], json_output=False)
        return
    if "plan" in payload and isinstance(payload["plan"], dict):
        plan = payload["plan"]
        print(
            f"Cache cleanup plan: {plan.get('candidateCount', 0)} candidate(s), "
            f"{_format_bytes(plan.get('releasableBytes', 0))} releasable."
        )
        if plan.get("blockedBecauseServiceRunning"):
            print("Cleanup is blocked while the Airport service is running on port 8776.")
        for item in plan.get("candidates", []):
            print(f"- {item.get('path')} ({_format_bytes(item.get('bytes', 0))})")
        return
    if "entries" in payload:
        entries = payload.get("entries", [])
        print(f"Cache inventory: {len(entries)} entry/entries, {_format_bytes(payload.get('totalBytes', 0))} total.")
        for item in entries:
            print(
                f"- [{item.get('status', 'unknown')}] {item.get('path')} "
                f"({_format_bytes(item.get('bytes', 0))}; {item.get('reason', 'no reason')})"
            )
        return
    if "deleted" in payload:
        deleted = payload.get("deleted", [])
        failed = payload.get("failed", [])
        print(
            f"Cache cleanup completed: {len(deleted)} target(s) removed, "
            f"{_format_bytes(payload.get('releasedBytes', 0))} released, {len(failed)} failure(s)."
        )
        for item in deleted:
            print(f"- removed {item.get('path')}")
        for item in failed:
            print(f"- failed {item.get('path')}: {item.get('error')}")
        return
    if "runId" in payload and "pinned" in payload:
        state = "pinned" if payload["pinned"] else "unpinned"
        print(f"Cache Run {payload['runId']} is now {state}.")
        return
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))


def _format_bytes(value: Any) -> str:
    size = max(0.0, float(value or 0))
    units = ("B", "KiB", "MiB", "GiB", "TiB")
    for unit in units:
        if size < 1024.0 or unit == units[-1]:
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TiB"


def _confirmed_interactively() -> bool:
    answer = input("Type CLEAN to apply this cache plan, or press Enter to cancel: ")
    return answer.strip() == "CLEAN"


def _clean_cache(service: Any, args: Namespace) -> int:
    plan = service.plan_cache()
    if args.confirm:
        result = service.clean_cache(confirm=True)
        _print_payload(
            {"plan": plan, "executed": True, "result": result},
            json_output=args.json,
        )
        return 0

    if args.json or not sys.stdin.isatty():
        _print_payload(
            {
                "plan": plan,
                "executed": False,
                "reason": "confirmation_required",
                "nextCommand": "python -m airport_sim cache clean --confirm",
            },
            json_output=args.json,
        )
        return 0

    _print_payload(plan, json_output=False)
    if not _confirmed_interactively():
        print("Cache cleanup cancelled.")
        return 0
    result = service.clean_cache(confirm=True)
    _print_payload(result, json_output=False)
    return 0


def cache_command(args: Namespace) -> int:
    service = _cache_service()
    try:
        if args.cache_action == "list":
            payload = service.list_cache()
        elif args.cache_action == "plan":
            payload = service.plan_cache()
        elif args.cache_action == "clean":
            return _clean_cache(service, args)
        elif args.cache_action == "pin":
            payload = service.pin_cache(args.run_id)
        elif args.cache_action == "unpin":
            payload = service.unpin_cache(args.run_id)
        elif args.cache_action == "retention":
            payload = service.set_retention(args.max_runs)
        elif args.cache_action == "viewer-retention":
            payload = service.set_viewer_retention(args.max_releases)
        else:  # pragma: no cover - argparse enforces the known choices.
            raise RuntimeError(f"unsupported cache action: {args.cache_action}")
    except (OSError, RuntimeError, ValueError) as error:
        failure = {"ok": False, "error": f"{type(error).__name__}: {error}"}
        if args.json:
            _print_payload(failure, json_output=True)
        else:
            print(f"Cache command failed: {error}", file=sys.stderr)
        return 2
    _print_payload(payload, json_output=args.json)
    return 0
