from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any


def variant_label(variant_id: str, manifest: dict[str, Any]) -> str:
    if variant_id == "baseline":
        return "Baseline"
    scenario = (
        manifest.get("scenario")
        if isinstance(manifest.get("scenario"), dict)
        else None
    )
    if scenario and scenario.get("state") == "probabilistic":
        event_count = (
            len(scenario.get("selected_events", []))
            if isinstance(scenario.get("selected_events"), list)
            else 0
        )
        return f"概率历史岔路: {event_count} events"
    selected = scenario.get("selected", {}) if scenario else {}
    risk = selected.get("risk", {}) if isinstance(selected.get("risk"), dict) else {}
    state = str(scenario.get("state") or "").strip() if scenario else ""
    label = str(risk.get("label") or risk.get("id") or "").strip()
    year = selected.get("trigger_year")
    if label and str(risk.get("id") or "") in variant_id:
        state_label = (
            "发生"
            if state == "occurred"
            else "反事实"
            if state == "counterfactual"
            else state or "情景"
        )
        return f"{state_label}: {label} {year}".strip()
    return variant_id.replace("_", " ")


def build_run_index(
    output_root: Path,
    *,
    version: str,
    time_module: Any,
    read_json_file: Callable[[Path], dict[str, Any]],
    variant_label: Callable[[str, dict[str, Any]], str],
    airport_relative: Callable[[Path], str],
) -> dict[str, Any]:
    runs: list[dict[str, Any]] = []
    if output_root.exists():
        manifest_paths = sorted(
            (
                path
                for path in output_root.glob("*/manifest.json")
                if not path.parent.name.startswith(".staging_")
            ),
            key=lambda item: item.stat().st_mtime,
            reverse=True,
        )
        for manifest_path in manifest_paths:
            try:
                manifest = read_json_file(manifest_path)
            except (OSError, json.JSONDecodeError):
                continue
            run_dir = manifest_path.parent
            variants = []
            manifest_variants = manifest.get("variants", {})
            if isinstance(manifest_variants, dict):
                for variant_id, variant_meta in manifest_variants.items():
                    variant_dir = run_dir / variant_id
                    if not variant_dir.exists():
                        continue
                    meta = variant_meta if isinstance(variant_meta, dict) else {}
                    variants.append(
                        {
                            "id": variant_id,
                            "label": variant_label(variant_id, manifest),
                            "path": airport_relative(variant_dir),
                            "global_rows": meta.get("global_rows", 0),
                            "regional_rows": meta.get("regional_rows", 0),
                            "reconciled_rows": meta.get("reconciled_rows", 0),
                            "aviation_rows": meta.get("aviation_rows", 0),
                            "supply_rows": meta.get("supply_rows", 0),
                            "city_airport_rows": meta.get("city_airport_rows", 0),
                            "potential_passenger_forecast_rows": meta.get(
                                "potential_passenger_forecast_rows",
                                0,
                            ),
                            "quarterly_operations_rows": meta.get(
                                "quarterly_operations_rows",
                                0,
                            ),
                            "financial_state_rows": meta.get(
                                "financial_state_rows",
                                0,
                            ),
                            "valuation_rows": meta.get("valuation_rows", 0),
                            "city_airport_downstream_skips": meta.get(
                                "city_airport_downstream_skips",
                                0,
                            ),
                            "active_global_scenario_rows": meta.get(
                                "active_global_scenario_rows",
                                0,
                            ),
                        }
                    )
            if not variants:
                continue
            runs.append(
                {
                    "id": str(manifest.get("run_id") or run_dir.name),
                    "label": str(manifest.get("run_id") or run_dir.name),
                    "seed": manifest.get("seed"),
                    "start_year": manifest.get("start_year"),
                    "years": manifest.get("years"),
                    "feedback_iterations": manifest.get("feedback_iterations"),
                    "path": airport_relative(run_dir),
                    "variants": variants,
                    "scenario": manifest.get("scenario"),
                    "published": manifest.get("published"),
                }
            )
    return {
        "version": version,
        "generated_at": time_module.strftime("%Y-%m-%d %H:%M:%S"),
        "runs": runs,
    }


def write_run_index(
    output_root: Path,
    *,
    build_run_index: Callable[[Path], dict[str, Any]],
    write_json_file: Callable[[Path, dict[str, Any]], None],
    atomic_write_text_file: Callable[[Path, str], None],
    airport_relative: Callable[[Path], str],
) -> dict[str, Any]:
    output_root.mkdir(parents=True, exist_ok=True)
    payload = build_run_index(output_root)
    json_path = output_root / "macro_run_index.json"
    js_path = output_root / "macro_run_index.js"
    write_json_file(json_path, payload)
    js_payload = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    atomic_write_text_file(js_path, f"window.MACRO_RUN_INDEX = {js_payload};\n")
    return {
        "index_json": airport_relative(json_path),
        "index_js": airport_relative(js_path),
        "run_count": len(payload["runs"]),
    }
