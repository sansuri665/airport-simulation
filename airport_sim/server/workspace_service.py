from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any


def current_viewer_release_status(
    *,
    output_root: Path,
    read_json: Callable[[Path], Any],
) -> dict[str, Any]:
    manifest_path = output_root / "current_viewer_manifest.json"
    manifest: dict[str, Any] = {}
    if manifest_path.exists():
        try:
            loaded = read_json(manifest_path)
            if isinstance(loaded, dict):
                manifest = loaded
        except (OSError, ValueError, json.JSONDecodeError):
            manifest = {}
    release_id = str(manifest.get("release_id") or "").strip()
    return {
        "mode": "versioned_release" if release_id else "legacy_canonical",
        "releaseId": release_id or None,
        "runId": manifest.get("run_id"),
        "variant": manifest.get("variant"),
        "seed": manifest.get("seed"),
        "startYear": manifest.get("start_year"),
        "years": manifest.get("years"),
        "modelVersion": manifest.get("model_version"),
        "outputSchemaVersion": manifest.get("output_schema_version"),
        "generatedAt": manifest.get("generated_at"),
        "schemaVersion": manifest.get("schema_version"),
    }


def workspace_status(
    *,
    root_dir: Path,
    run_root: Path,
    save_root: Path,
    service_id: str,
    list_cached_runs: Callable[[], list[dict[str, Any]]],
    current_viewer_release_status: Callable[[], dict[str, Any]],
    getpid: Callable[[], int],
) -> dict[str, Any]:
    cached_runs = list_cached_runs()
    save_count = sum(
        1
        for path in save_root.glob("**/dynamic_test_save.json")
        if path.is_file()
    )
    return {
        "ok": True,
        "serviceId": service_id,
        "servicePid": getpid(),
        "viewerRelease": current_viewer_release_status(),
        "cachedRunCount": len(cached_runs),
        "saveCount": save_count,
        "runRoot": str(run_root.relative_to(root_dir).as_posix()),
        "saveRoot": str(save_root.relative_to(root_dir).as_posix()),
        "pages": {
            "home": "/",
            "seedExplorer": "/seed-explorer",
            "globalGdp": "/global-gdp",
            "cityMarkets": "/city-markets",
            "beijingForecast": "/beijing-forecast",
        },
    }
