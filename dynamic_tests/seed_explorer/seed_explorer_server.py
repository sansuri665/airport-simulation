from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import shutil
import subprocess
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


TOOL_DIR = Path(__file__).resolve().parent
ROOT_DIR = TOOL_DIR.parent.parent
RUN_ROOT = ROOT_DIR / "output" / "seed_explorer_runs"
VIEWER_HTML = TOOL_DIR / "seed_explorer_viewer.html"
ORCHESTRATOR = ROOT_DIR / "macro_layers" / "macro_run_orchestrator_sim.py"
MAX_CACHED_RUNS = 4
BEIJING_OPERATIONS_RELATIVE_CSV = Path(
    "baseline/city_airport_quarterly_operations/china_mainland/"
    "beijing_airport_system_quarterly_operations_seed_sweep.csv"
)
BEIJING_FINANCIAL_RELATIVE_CSV = Path(
    "baseline/city_airport_financial_state/china_mainland/"
    "beijing_airport_system_financial_state_seed_sweep.csv"
)
BEIJING_CITY_DEMAND_RELATIVE_CSV = Path(
    "baseline/city_airport_market_demand/china_mainland/"
    "beijing_airport_system_city_airport_demand_seed_sweep.csv"
)
SIMULATION_DIR_NAME = "simulation_default"
SIMULATION_CITY_DEMAND_RELATIVE_CSV = Path(
    f"{SIMULATION_DIR_NAME}/city_airport_market_demand/china_mainland/"
    "beijing_airport_system_city_airport_demand_seed_sweep.csv"
)
SIMULATION_OPERATIONS_RELATIVE_CSV = Path(
    f"{SIMULATION_DIR_NAME}/city_airport_quarterly_operations/china_mainland/"
    "beijing_airport_system_quarterly_operations_seed_sweep.csv"
)
SIMULATION_FINANCIAL_RELATIVE_CSV = Path(
    f"{SIMULATION_DIR_NAME}/city_airport_financial_state/china_mainland/"
    "beijing_airport_system_financial_state_seed_sweep.csv"
)
QUARTERLY_OPERATIONS_SCRIPT = ROOT_DIR / "macro_layers" / "city_airport_quarterly_operations_layer_sim.py"
FINANCIAL_STATE_SCRIPT = ROOT_DIR / "macro_layers" / "city_airport_financial_state_layer_sim.py"
BEIJING_OPERATIONS_CONFIG = (
    ROOT_DIR / "config" / "city_airport_operations" / "beijing_airport_system_quarterly_operations_v1.json"
)
BEIJING_FINANCE_CONFIG = (
    ROOT_DIR / "config" / "city_airport_finance" / "beijing_airport_group_financial_state_v1.json"
)
INITIAL_ACTIVE_FACILITY_SLOTS = "PEK_SLOT_1:extra_large;PEK_SLOT_2:large;PKX_SLOT_1:giant"
INITIAL_DESIGN_CAPACITY_MILLION = 154.0
INITIAL_MAX_CAPACITY_MILLION = 200.0
PLAYER_DECISION_START_YEAR = 2030
SIMULATION_START_YEAR = 2025
RENOVATION_COOLDOWN_QUARTERS = 6 * 4
REBUILD_COOLDOWN_QUARTERS = 20 * 4
DEMOLITION_CLEARANCE_QUARTERS = 4
PROJECT_TEMPLATES: dict[str, dict[str, Any]] = {
    "PEK_T3_RENOVATION": {
        "templateId": "PEK_T3_RENOVATION",
        "projectId": "PEK_SLOT_1_RENOVATION_STANDARD",
        "name": "首都T3航站楼翻新工程",
        "airport": "北京首都",
        "airportId": "PEK",
        "slotId": "PEK_SLOT_1",
        "slotRole": "main_slot",
        "slotName": "首都T3航站楼",
        "projectType": "renovation",
        "facilitySize": "extra_large",
    },
    "PEK_T2_RENOVATION": {
        "templateId": "PEK_T2_RENOVATION",
        "projectId": "PEK_SLOT_2_RENOVATION_2032Q1",
        "name": "首都T2航站楼翻新工程",
        "airport": "北京首都",
        "airportId": "PEK",
        "slotId": "PEK_SLOT_2",
        "slotRole": "secondary_slot",
        "slotName": "首都T2航站楼",
        "projectType": "renovation",
        "facilitySize": "large",
    },
    "PKX_T1_RENOVATION": {
        "templateId": "PKX_T1_RENOVATION",
        "projectId": "PKX_SLOT_1_RENOVATION_STANDARD",
        "name": "大兴T1航站楼翻新工程",
        "airport": "北京大兴",
        "airportId": "PKX",
        "slotId": "PKX_SLOT_1",
        "slotRole": "main_slot",
        "slotName": "大兴T1航站楼",
        "projectType": "renovation",
        "facilitySize": "giant",
    },
    "PEK_T2_REBUILD": {
        "templateId": "PEK_T2_REBUILD",
        "projectId": "PEK_SLOT_2_REBUILD_2056Q1",
        "name": "首都T2航站楼拆除重建工程",
        "airport": "北京首都",
        "airportId": "PEK",
        "slotId": "PEK_SLOT_2",
        "slotRole": "secondary_slot",
        "slotName": "首都T2航站楼",
        "projectType": "rebuild",
        "sourceFacilitySize": "large",
        "targetFacilitySize": "extra_large",
    },
    "PEK_T3_REBUILD": {
        "templateId": "PEK_T3_REBUILD",
        "projectId": "PEK_SLOT_1_REBUILD_STANDARD",
        "name": "首都T3航站楼拆除重建工程",
        "airport": "北京首都",
        "airportId": "PEK",
        "slotId": "PEK_SLOT_1",
        "slotRole": "main_slot",
        "slotName": "首都T3航站楼",
        "projectType": "rebuild",
        "sourceFacilitySize": "extra_large",
        "targetFacilitySize": "extra_large",
    },
    "PKX_T1_REBUILD": {
        "templateId": "PKX_T1_REBUILD",
        "projectId": "PKX_SLOT_1_REBUILD_STANDARD",
        "name": "大兴T1航站楼拆除重建工程",
        "airport": "北京大兴",
        "airportId": "PKX",
        "slotId": "PKX_SLOT_1",
        "slotRole": "main_slot",
        "slotName": "大兴T1航站楼",
        "projectType": "rebuild",
        "sourceFacilitySize": "giant",
        "targetFacilitySize": "giant",
    },
    "PEK_SLOT_3_CONSTRUCTION": {
        "templateId": "PEK_SLOT_3_CONSTRUCTION",
        "projectId": "PEK_SLOT_3_CONSTRUCTION",
        "name": "首都机场辅助槽位1新建工程",
        "airport": "北京首都",
        "airportId": "PEK",
        "slotId": "PEK_SLOT_3",
        "slotRole": "auxiliary_slot",
        "slotName": "空白槽位",
        "projectType": "construction",
    },
    "PEK_SLOT_4_CONSTRUCTION": {
        "templateId": "PEK_SLOT_4_CONSTRUCTION",
        "projectId": "PEK_SLOT_4_CONSTRUCTION",
        "name": "首都机场辅助槽位2新建工程",
        "airport": "北京首都",
        "airportId": "PEK",
        "slotId": "PEK_SLOT_4",
        "slotRole": "auxiliary_slot",
        "slotName": "空白槽位",
        "projectType": "construction",
    },
    "PEK_SLOT_5_CONSTRUCTION": {
        "templateId": "PEK_SLOT_5_CONSTRUCTION",
        "projectId": "PEK_SLOT_5_CONSTRUCTION",
        "name": "首都机场辅助槽位3新建工程",
        "airport": "北京首都",
        "airportId": "PEK",
        "slotId": "PEK_SLOT_5",
        "slotRole": "auxiliary_slot",
        "slotName": "空白槽位",
        "projectType": "construction",
    },
    "PKX_SLOT_2_CONSTRUCTION": {
        "templateId": "PKX_SLOT_2_CONSTRUCTION",
        "projectId": "PKX_SLOT_2_CONSTRUCTION",
        "name": "大兴机场次槽位新建工程",
        "airport": "北京大兴",
        "airportId": "PKX",
        "slotId": "PKX_SLOT_2",
        "slotRole": "secondary_slot",
        "slotName": "空白槽位",
        "projectType": "construction",
    },
    "PKX_SLOT_3_CONSTRUCTION": {
        "templateId": "PKX_SLOT_3_CONSTRUCTION",
        "projectId": "PKX_SLOT_3_CONSTRUCTION",
        "name": "大兴机场辅助槽位1新建工程",
        "airport": "北京大兴",
        "airportId": "PKX",
        "slotId": "PKX_SLOT_3",
        "slotRole": "auxiliary_slot",
        "slotName": "空白槽位",
        "projectType": "construction",
    },
    "PKX_SLOT_4_CONSTRUCTION": {
        "templateId": "PKX_SLOT_4_CONSTRUCTION",
        "projectId": "PKX_SLOT_4_CONSTRUCTION",
        "name": "大兴机场辅助槽位2新建工程",
        "airport": "北京大兴",
        "airportId": "PKX",
        "slotId": "PKX_SLOT_4",
        "slotRole": "auxiliary_slot",
        "slotName": "空白槽位",
        "projectType": "construction",
    },
    "PKX_SLOT_5_CONSTRUCTION": {
        "templateId": "PKX_SLOT_5_CONSTRUCTION",
        "projectId": "PKX_SLOT_5_CONSTRUCTION",
        "name": "大兴机场辅助槽位3新建工程",
        "airport": "北京大兴",
        "airportId": "PKX",
        "slotId": "PKX_SLOT_5",
        "slotRole": "auxiliary_slot",
        "slotName": "空白槽位",
        "projectType": "construction",
    },
}

# Empty slots receive their operating-project templates up front.  They stay
# unavailable until a completed player construction event has made the slot live.
for _construction_template in list(PROJECT_TEMPLATES.values()):
    if _construction_template.get("projectType") != "construction":
        continue
    _slot_id = str(_construction_template["slotId"])
    _airport = str(_construction_template["airport"])
    _airport_id = str(_construction_template["airportId"])
    _slot_role = str(_construction_template["slotRole"])
    PROJECT_TEMPLATES[f"{_slot_id}_RENOVATION"] = {
        "templateId": f"{_slot_id}_RENOVATION",
        "projectId": f"{_slot_id}_RENOVATION_STANDARD",
        "name": f"{_airport}槽位翻新工程",
        "airport": _airport,
        "airportId": _airport_id,
        "slotId": _slot_id,
        "slotRole": _slot_role,
        "slotName": "空白槽位",
        "projectType": "renovation",
        "facilitySize": "empty",
    }
    PROJECT_TEMPLATES[f"{_slot_id}_REBUILD"] = {
        "templateId": f"{_slot_id}_REBUILD",
        "projectId": f"{_slot_id}_REBUILD_STANDARD",
        "name": f"{_airport}槽位拆除重建工程",
        "airport": _airport,
        "airportId": _airport_id,
        "slotId": _slot_id,
        "slotRole": _slot_role,
        "slotName": "空白槽位",
        "projectType": "rebuild",
        "sourceFacilitySize": "empty",
        "targetFacilitySize": "empty",
    }

# Existing terminals can be demolished and later rebuilt in the same physical
# slot.  Construction templates remain hidden until the slot is actually empty.
for _slot_template in list(PROJECT_TEMPLATES.values()):
    _slot_id = str(_slot_template["slotId"])
    _airport = str(_slot_template["airport"])
    _airport_id = str(_slot_template["airportId"])
    _slot_role = str(_slot_template["slotRole"])
    if not any(
        candidate.get("slotId") == _slot_id and candidate.get("projectType") == "construction"
        for candidate in PROJECT_TEMPLATES.values()
    ):
        PROJECT_TEMPLATES[f"{_slot_id}_CONSTRUCTION"] = {
            "templateId": f"{_slot_id}_CONSTRUCTION",
            "projectId": f"{_slot_id}_CONSTRUCTION",
            "name": f"{_airport}槽位新建工程",
            "airport": _airport,
            "airportId": _airport_id,
            "slotId": _slot_id,
            "slotRole": _slot_role,
            "slotName": str(_slot_template.get("slotName") or "空白槽位"),
            "projectType": "construction",
        }
    if not any(
        candidate.get("slotId") == _slot_id and candidate.get("projectType") == "demolition"
        for candidate in PROJECT_TEMPLATES.values()
    ):
        PROJECT_TEMPLATES[f"{_slot_id}_DEMOLITION"] = {
            "templateId": f"{_slot_id}_DEMOLITION",
            "projectId": f"{_slot_id}_DEMOLITION",
            "name": f"{_airport}槽位拆除工程",
            "airport": _airport,
            "airportId": _airport_id,
            "slotId": _slot_id,
            "slotRole": _slot_role,
            "slotName": str(_slot_template.get("slotName") or "空白槽位"),
            "projectType": "demolition",
            "sourceFacilitySize": "empty",
        }
RENAMABLE_SLOT_IDS = {str(template["slotId"]) for template in PROJECT_TEMPLATES.values()}
INITIAL_TERMINAL_NUMBERS_BY_AIRPORT = {"PEK": {2, 3}, "PKX": {1}}
TERMINAL_NAME_PREFIX_BY_AIRPORT = {"PEK": "首都", "PKX": "大兴"}
INITIAL_TERMINAL_NUMBER_BY_SLOT = {"PEK_SLOT_1": 3, "PEK_SLOT_2": 2, "PKX_SLOT_1": 1}
INITIAL_SLOT_SIZES = {"PEK_SLOT_1": "extra_large", "PEK_SLOT_2": "large", "PKX_SLOT_1": "giant"}
FINANCING_PRODUCTS = {
    "short_turnover": {"label": "短期周转贷款", "loan_type": "short_term", "repayment_style": "bullet_principal", "tenors": [4, 8, 12], "grace": [0], "tenor_spread_bps": {4: 0, 8: 15, 12: 30}},
    "long_construction": {"label": "长期建设贷款", "loan_type": "long_term", "repayment_style": "equal_principal", "tenors": [40, 60, 80], "grace": [0], "tenor_spread_bps": {40: 0, 60: 20, 80: 45}},
    "grace_construction": {"label": "宽限期建设贷款", "loan_type": "long_term", "repayment_style": "grace_then_equal_principal", "tenors": [60, 80], "grace": [8, 16], "tenor_spread_bps": {60: 20, 80: 45}, "grace_spread_bps": {8: 10, 16: 25}},
}
OPERATION_MODE_DETAILS = {
    "replay": {
        "label": "回放模式",
        "description": "读取完整结果，包含测试贷款、测试项目和自动合同续期。",
    },
    "simulate_default": {
        "label": "模拟模式",
        "description": "复用同一 seed 的外部世界，机场侧使用默认初始设施；玩家行动由服务端重算。",
    },
}

RUN_LOCK = threading.Lock()


def as_float(value: Any, default: float = 0.0) -> float:
    if value in (None, ""):
        return default
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if math.isnan(number) or math.isinf(number):
        return default
    return number


def as_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def facility_size_catalog() -> dict[str, Any]:
    catalog_path = ROOT_DIR / "config" / "facility_size_catalogs" / "standard_terminal_sizes_v1.json"
    return read_json(catalog_path) if catalog_path.exists() else {}


def allowed_rebuild_target_sizes(template: dict[str, Any]) -> list[str]:
    catalog = facility_size_catalog()
    allowed = catalog.get("slot_role_allowed_sizes", {}).get(str(template.get("slotRole") or ""), [])
    return [str(size) for size in allowed if str(size) != "empty"]


def allowed_construction_target_sizes(template: dict[str, Any]) -> list[str]:
    return allowed_rebuild_target_sizes(template)


def construction_event_config(target_size: str) -> dict[str, Any]:
    operations_config = read_json(BEIJING_OPERATIONS_CONFIG)
    construction_model = operations_config.get("facility_construction_model", {})
    capex = as_float(construction_model.get("construction_cost_million_cny_by_facility_size", {}).get(target_size))
    capex *= as_float(construction_model.get("city_construction_cost_multiplier"), 1.0)
    depreciation = construction_model.get("new_asset_depreciation", construction_model.get("construction_asset_depreciation", {}))
    return {
        "target_facility_size": target_size,
        "duration_quarters": max(1, int(as_float(construction_model.get("duration_quarters_by_facility_size", {}).get(target_size), 12.0))),
        "capex_million_cny": round(capex, 4),
        "useful_life_years": round(as_float(depreciation.get("useful_life_years"), 40.0), 4),
        "residual_value_pct": round(as_float(depreciation.get("residual_value_pct"), 10.0), 4),
    }


def rebuild_event_config(source_size: str, target_size: str) -> dict[str, Any]:
    operations_config = read_json(BEIJING_OPERATIONS_CONFIG)
    rebuild_model = operations_config.get("facility_rebuild_model", {})
    construction_model = operations_config.get("facility_construction_model", {})
    capex = as_float(construction_model.get("construction_cost_million_cny_by_facility_size", {}).get(target_size))
    capex *= as_float(construction_model.get("city_construction_cost_multiplier"), 1.0)
    demolition = as_float(rebuild_model.get("asset_cost_million_cny_by_facility_size", {}).get(source_size))
    demolition *= as_float(rebuild_model.get("demolition_cost_ratio_by_source_facility_size", {}).get(source_size), 0.10)
    demolition *= as_float(rebuild_model.get("city_demolition_cost_multiplier"), 1.0)
    depreciation = rebuild_model.get("new_asset_depreciation", construction_model.get("new_asset_depreciation", {}))
    demolition_duration = max(
        1,
        int(as_float(rebuild_model.get("demolition_duration_quarters_by_source_facility_size", {}).get(source_size), 1.0)),
    )
    construction_duration = max(
        1,
        int(as_float(construction_model.get("duration_quarters_by_facility_size", {}).get(target_size), 12.0)),
    )
    return {
        "source_facility_size": source_size,
        "target_facility_size": target_size,
        "demolition_duration_quarters": demolition_duration,
        "construction_duration_quarters": construction_duration,
        "duration_quarters": demolition_duration + construction_duration,
        "asset_capex_million_cny": round(capex, 4),
        "demolition_expense_million_cny": round(demolition, 4),
        "useful_life_years": round(as_float(depreciation.get("useful_life_years"), 40.0), 4),
        "residual_value_pct": round(as_float(depreciation.get("residual_value_pct"), 10.0), 4),
    }


def demolition_event_config(source_size: str) -> dict[str, Any]:
    operations_config = read_json(BEIJING_OPERATIONS_CONFIG)
    rebuild_model = operations_config.get("facility_rebuild_model", {})
    demolition = as_float(rebuild_model.get("asset_cost_million_cny_by_facility_size", {}).get(source_size))
    demolition *= as_float(rebuild_model.get("demolition_cost_ratio_by_source_facility_size", {}).get(source_size), 0.10)
    demolition *= as_float(rebuild_model.get("city_demolition_cost_multiplier"), 1.0)
    return {
        "source_facility_size": source_size,
        "target_facility_size": "empty",
        "duration_quarters": max(
            1,
            int(as_float(rebuild_model.get("demolition_duration_quarters_by_source_facility_size", {}).get(source_size), 1.0)),
        ),
        "asset_capex_million_cny": 0.0,
        "demolition_expense_million_cny": round(demolition, 4),
    }


def renovation_event_config(facility_size: str) -> dict[str, Any]:
    operations_config = read_json(BEIJING_OPERATIONS_CONFIG)
    renovation_model = operations_config.get("facility_renovation_model", {})
    replacement_cost = as_float(renovation_model.get("replacement_cost_million_cny_by_facility_size", {}).get(facility_size))
    capex_ratio = as_float(renovation_model.get("capex_ratio_by_facility_size", {}).get(facility_size))
    capex = replacement_cost * capex_ratio * as_float(renovation_model.get("city_construction_cost_multiplier"), 1.0)
    depreciation = renovation_model.get("renovation_asset_depreciation", {})
    return {
        "facility_size": facility_size,
        "duration_quarters": max(1, int(as_float(renovation_model.get("duration_quarters_by_facility_size", {}).get(facility_size), 6.0))),
        "construction_capacity_multiplier": round(
            as_float(renovation_model.get("default_construction_capacity_multiplier"), 0.75), 4
        ),
        "capex_million_cny": round(capex, 4),
        "useful_life_years": round(as_float(depreciation.get("useful_life_years"), 20.0), 4),
        "residual_value_pct": round(as_float(depreciation.get("residual_value_pct"), 5.0), 4),
    }


def as_text(row: dict[str, str], key: str) -> str:
    return str(row.get(key) or "").strip()


def rounded(row: dict[str, str], key: str, digits: int = 4) -> float:
    return round(as_float(row.get(key)), digits)


def clean_seed(value: Any) -> int:
    try:
        seed = int(str(value).strip())
    except (TypeError, ValueError):
        raise ValueError("seed must be an integer")
    if seed < 0:
        raise ValueError("seed must be non-negative")
    return seed


def clean_years(value: Any) -> int:
    try:
        years = int(str(value).strip())
    except (TypeError, ValueError):
        return 60
    return max(5, min(90, years))


def clean_operation_mode(value: Any) -> str:
    mode = str(value or "replay").strip()
    if mode not in OPERATION_MODE_DETAILS:
        raise ValueError(f"unsupported operation mode: {mode}")
    return mode


def clean_player_actions(value: Any) -> list[dict[str, Any]]:
    """Persist only action data the simulation layer understands.

    The dynamic-test save is an event journal, not a second copy of calculated
    quarterly statements. Keeping this boundary here also lets old frontend
    saves be read without trusting their derived operation overrides.
    """
    if not isinstance(value, list):
        return []
    actions: list[dict[str, Any]] = []
    seen_contracts: set[tuple[str, str, str]] = set()
    seen_financing_quarters: set[int] = set()
    seen_renovation_instances: set[tuple[str, int]] = set()
    seen_rebuild_instances: set[tuple[str, int]] = set()
    seen_construction_instances: set[tuple[str, int]] = set()
    seen_demolition_instances: set[tuple[str, int]] = set()
    terminal_numbers_by_airport = {
        airport_id: set(numbers)
        for airport_id, numbers in INITIAL_TERMINAL_NUMBERS_BY_AIRPORT.items()
    }
    terminal_number_by_slot = dict(INITIAL_TERMINAL_NUMBER_BY_SLOT)
    renovation_completion_by_slot: dict[str, list[int]] = {}
    rebuild_completion_by_slot: dict[str, list[int]] = {}
    demolition_completion_by_slot: dict[str, list[int]] = {}
    project_completion_by_slot: dict[str, list[int]] = {}
    slot_size_by_id = {str(template["slotId"]): "empty" for template in PROJECT_TEMPLATES.values()}
    slot_size_by_id.update(INITIAL_SLOT_SIZES)
    seen_slot_renames: set[str] = set()
    for raw in value:
        if not isinstance(raw, dict):
            continue
        action_type = str(raw.get("type") or "")
        if action_type == "rename_slot":
            slot_id = str(raw.get("slotId") or raw.get("slot_id") or "").strip()
            name = " ".join(str(raw.get("name") or "").strip().split())
            if slot_id not in RENAMABLE_SLOT_IDS or not 2 <= len(name) <= 24:
                continue
            if slot_id in seen_slot_renames:
                actions = [
                    action
                    for action in actions
                    if not (action["type"] == "rename_slot" and action["slotId"] == slot_id)
                ]
            seen_slot_renames.add(slot_id)
            actions.append(
                {
                    "id": str(raw.get("id") or f"rename:{slot_id}"),
                    "type": "rename_slot",
                    "slotId": slot_id,
                    "name": name,
                    "renamedAtIndex": int(as_float(raw.get("renamedAtIndex"), 0.0)),
                    "renamedAtLabel": str(raw.get("renamedAtLabel") or ""),
                }
            )
            continue
        if action_type == "start_project":
            template_id = str(raw.get("templateId") or raw.get("template_id") or "").strip()
            template = PROJECT_TEMPLATES.get(template_id)
            started_at_index = int(as_float(raw.get("startedAtIndex"), -1.0))
            if not template or started_at_index < (PLAYER_DECISION_START_YEAR - SIMULATION_START_YEAR) * 4:
                continue
            project_type = str(template["projectType"])
            event_config: dict[str, Any] = {}
            project_id = str(template["projectId"])
            slot_id = str(template["slotId"])
            latest_project_completion = max(project_completion_by_slot.get(slot_id, []), default=-10**9)
            if started_at_index < latest_project_completion:
                continue
            if project_type == "renovation":
                event_config = renovation_event_config(slot_size_by_id.get(slot_id, str(template["facilitySize"])))
                instance_key = (slot_id, started_at_index)
                duration = max(1, int(event_config["duration_quarters"]))
                prior_completions = renovation_completion_by_slot.setdefault(slot_id, [])
                latest_completion = max(prior_completions, default=-10**9)
                latest_rebuild_completion = max(rebuild_completion_by_slot.get(slot_id, []), default=-10**9)
                if instance_key in seen_renovation_instances:
                    continue
                if started_at_index < max(latest_completion, latest_rebuild_completion) + RENOVATION_COOLDOWN_QUARTERS:
                    continue
                seen_renovation_instances.add(instance_key)
                completion_index = started_at_index + duration
                prior_completions.append(completion_index)
                project_completion_by_slot.setdefault(slot_id, []).append(completion_index)
                project_id = f"{template['projectId']}__{started_at_index}"
            elif project_type == "rebuild":
                instance_key = (slot_id, started_at_index)
                frozen_config = raw.get("eventConfig") if isinstance(raw.get("eventConfig"), dict) else {}
                target_size = str(
                    raw.get("targetFacilitySize")
                    or raw.get("target_facility_size")
                    or frozen_config.get("target_facility_size")
                    or ""
                ).strip()
                if target_size not in allowed_rebuild_target_sizes(template) or instance_key in seen_rebuild_instances:
                    continue
                prior_completions = rebuild_completion_by_slot.setdefault(slot_id, [])
                latest_completion = max(prior_completions, default=-10**9)
                if started_at_index < latest_completion + REBUILD_COOLDOWN_QUARTERS:
                    continue
                source_size = slot_size_by_id.get(slot_id, str(template["sourceFacilitySize"]))
                event_config = rebuild_event_config(source_size, target_size)
                duration = max(1, int(event_config["duration_quarters"]))
                completion_index = started_at_index + duration
                seen_rebuild_instances.add(instance_key)
                prior_completions.append(completion_index)
                project_completion_by_slot.setdefault(slot_id, []).append(completion_index)
                slot_size_by_id[slot_id] = target_size
                project_id = f"{template['projectId']}__{started_at_index}"
            elif project_type == "construction":
                frozen_config = raw.get("eventConfig") if isinstance(raw.get("eventConfig"), dict) else {}
                target_size = str(
                    raw.get("targetFacilitySize")
                    or raw.get("target_facility_size")
                    or frozen_config.get("target_facility_size")
                    or ""
                ).strip()
                instance_key = (slot_id, started_at_index)
                latest_demolition_completion = max(demolition_completion_by_slot.get(slot_id, []), default=-10**9)
                if (
                    slot_size_by_id.get(slot_id, "empty") != "empty"
                    or target_size not in allowed_construction_target_sizes(template)
                    or instance_key in seen_construction_instances
                    or started_at_index < latest_demolition_completion + DEMOLITION_CLEARANCE_QUARTERS
                ):
                    continue
                event_config = construction_event_config(target_size)
                airport_id = str(template["airportId"])
                assigned_numbers = terminal_numbers_by_airport.setdefault(airport_id, set())
                terminal_number = terminal_number_by_slot.get(slot_id, max(assigned_numbers, default=0) + 1)
                assigned_numbers.add(terminal_number)
                terminal_number_by_slot[slot_id] = terminal_number
                event_config["terminal_number"] = terminal_number
                event_config["terminal_name"] = f"{TERMINAL_NAME_PREFIX_BY_AIRPORT.get(airport_id, airport_id)}T{terminal_number}航站楼"
                duration = max(1, int(event_config["duration_quarters"]))
                seen_construction_instances.add(instance_key)
                project_completion_by_slot.setdefault(slot_id, []).append(started_at_index + duration)
                slot_size_by_id[slot_id] = target_size
                project_id = f"{template['projectId']}__{started_at_index}"
            elif project_type == "demolition":
                instance_key = (slot_id, started_at_index)
                source_size = slot_size_by_id.get(slot_id, "empty")
                if source_size == "empty" or instance_key in seen_demolition_instances:
                    continue
                event_config = demolition_event_config(source_size)
                duration = max(1, int(event_config["duration_quarters"]))
                completion_index = started_at_index + duration
                seen_demolition_instances.add(instance_key)
                demolition_completion_by_slot.setdefault(slot_id, []).append(completion_index)
                project_completion_by_slot.setdefault(slot_id, []).append(completion_index)
                slot_size_by_id[slot_id] = "empty"
                project_id = f"{template['projectId']}__{started_at_index}"
            else:
                continue
            actions.append(
                {
                    "id": str(raw.get("id") or f"{template_id}:{started_at_index}"),
                    "type": "start_project",
                    "templateId": template_id,
                    "projectId": project_id,
                    "startedAtIndex": started_at_index,
                    "startedAtLabel": str(raw.get("startedAtLabel") or ""),
                    "eventConfig": event_config,
                }
            )
            continue
        if action_type == "draw_loan":
            started_at_index = int(as_float(raw.get("startedAtIndex"), -1.0))
            product_id = str(raw.get("productId") or "").strip()
            product = FINANCING_PRODUCTS.get(product_id)
            principal = round(as_float(raw.get("principalMillionCny")), 4)
            tenor = int(as_float(raw.get("tenorQuarters"), 0.0))
            grace = int(as_float(raw.get("gracePeriodQuarters"), 0.0))
            if (
                not product
                or started_at_index < (PLAYER_DECISION_START_YEAR - SIMULATION_START_YEAR) * 4
                or started_at_index in seen_financing_quarters
                or principal < 1000.0
                or principal > 100000.0
                or tenor not in product["tenors"]
                or grace not in product["grace"]
            ):
                continue
            seen_financing_quarters.add(started_at_index)
            actions.append({
                "id": str(raw.get("id") or f"loan:{product_id}:{started_at_index}"),
                "type": "draw_loan",
                "productId": product_id,
                "principalMillionCny": principal,
                "tenorQuarters": tenor,
            "gracePeriodQuarters": grace,
                "termSpreadBps": int(product.get("tenor_spread_bps", {}).get(tenor, 0)) + int(product.get("grace_spread_bps", {}).get(grace, 0)),
                "startedAtIndex": started_at_index,
                "startedAtLabel": str(raw.get("startedAtLabel") or ""),
            })
            continue
        if action_type != "sign_contract":
            continue
        contract_id = str(raw.get("contractId") or raw.get("contract_id") or "").strip()
        cycle_id = str(raw.get("cycleId") or raw.get("cycle_id") or "").strip()
        terms = raw.get("terms", {})
        if contract_id not in {"DUTY_FREE_MAIN", "LUXURY_RETAIL_MAIN"} or not cycle_id or not isinstance(terms, dict):
            continue
        key = ("sign_contract", contract_id, cycle_id)
        if key in seen_contracts:
            actions = [
                action
                for action in actions
                if (action["type"], action["contractId"], action["cycleId"]) != key
            ]
        seen_contracts.add(key)
        actions.append(
            {
                "id": str(raw.get("id") or f"{contract_id}:{cycle_id}"),
                "type": "sign_contract",
                "contractId": contract_id,
                "contractName": str(raw.get("contractName") or ""),
                "segment": str(raw.get("segment") or ""),
                "cycleId": cycle_id,
                "signedAtIndex": int(as_float(raw.get("signedAtIndex"), 0.0)),
                "signedAtLabel": str(raw.get("signedAtLabel") or ""),
                "effectiveStartIndex": int(as_float(raw.get("effectiveStartIndex"), 0.0)),
                "effectiveEndIndex": int(as_float(raw.get("effectiveEndIndex"), 0.0)),
                "effectiveStartLabel": str(raw.get("effectiveStartLabel") or ""),
                "effectiveEndLabel": str(raw.get("effectiveEndLabel") or ""),
                "terms": dict(terms),
            }
        )
    return actions


def player_general_loans(actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    loans: list[dict[str, Any]] = []
    for action in actions:
        if action.get("type") != "draw_loan":
            continue
        product = FINANCING_PRODUCTS.get(str(action.get("productId") or ""))
        if not product:
            continue
        year, quarter = relative_index_to_year_quarter(int(action["startedAtIndex"]))
        loans.append({
            "loan_id": str(action["id"]), "loan_name": str(product["label"]),
            "loan_type": product["loan_type"], "start_year": year, "start_quarter": quarter,
            "principal_million_cny": action["principalMillionCny"], "tenor_quarters": action["tenorQuarters"],
            "repayment_style": product["repayment_style"], "grace_period_quarters": action["gracePeriodQuarters"],
            "term_spread_bps": action.get("termSpreadBps", 0),
            "purpose_note": "玩家融资事务",
        })
    return loans


def relative_index_to_year_quarter(index: int) -> tuple[int, str]:
    safe_index = max(0, int(index))
    return SIMULATION_START_YEAR + safe_index // 4, f"Q{safe_index % 4 + 1}"


def player_slot_names(actions: list[dict[str, Any]]) -> dict[str, str]:
    return {
        str(action["slotId"]): str(action["name"])
        for action in actions
        if action.get("type") == "rename_slot" and action.get("slotId") in RENAMABLE_SLOT_IDS
    }


def player_project_events(actions: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    events = {
        "facility_renovation_events": [],
        "facility_construction_events": [],
        "facility_rebuild_events": [],
    }
    for action in actions:
        if action.get("type") != "start_project":
            continue
        template = PROJECT_TEMPLATES.get(str(action.get("templateId") or ""))
        if not template:
            continue
        start_year, start_quarter = relative_index_to_year_quarter(int(action.get("startedAtIndex", 0)))
        base_event = {
            "event_id": str(action.get("projectId") or template["projectId"]),
            "airport_id": template["airportId"],
            "slot_id": template["slotId"],
            "slot_name": template["slotName"],
            "start_year": start_year,
            "start_quarter": start_quarter,
            "player_action_id": action.get("id", ""),
            "player_started": True,
        }
        if template["projectType"] == "renovation":
            event_config = action.get("eventConfig", {})
            if not isinstance(event_config, dict):
                event_config = {}
            events["facility_renovation_events"].append(
                {
                    **base_event,
                    "facility_size": str(event_config.get("facility_size") or template["facilitySize"]),
                    **{
                        key: event_config[key]
                        for key in (
                            "duration_quarters",
                            "construction_capacity_multiplier",
                            "capex_million_cny",
                            "useful_life_years",
                            "residual_value_pct",
                        )
                        if key in event_config
                    },
                }
            )
        elif template["projectType"] == "construction":
            event_config = action.get("eventConfig", {})
            if not isinstance(event_config, dict):
                event_config = {}
            events["facility_construction_events"].append(
                {
                    **base_event,
                    "target_facility_size": str(event_config.get("target_facility_size") or ""),
                    **{
                        key: event_config[key]
                        for key in (
                            "duration_quarters",
                            "capex_million_cny",
                            "useful_life_years",
                            "residual_value_pct",
                        )
                        if key in event_config
                    },
                }
            )
        elif template["projectType"] in {"rebuild", "demolition"}:
            event_config = action.get("eventConfig", {})
            if not isinstance(event_config, dict):
                event_config = {}
            events["facility_rebuild_events"].append(
                {
                    **base_event,
                    "from_facility_size": str(event_config.get("source_facility_size") or template["sourceFacilitySize"]),
                    "target_facility_size": str(event_config.get("target_facility_size") or template.get("targetFacilitySize") or "empty"),
                    "project_type": str(template["projectType"]),
                    **{
                        key: event_config[key]
                        for key in (
                            "duration_quarters",
                            "asset_capex_million_cny",
                            "demolition_expense_million_cny",
                            "useful_life_years",
                            "residual_value_pct",
                        )
                        if key in event_config
                    },
                }
            )
    return events


def project_catalog() -> list[dict[str, Any]]:
    operations_config = read_json(BEIJING_OPERATIONS_CONFIG)
    catalog_path = ROOT_DIR / "config" / "facility_size_catalogs" / "standard_terminal_sizes_v1.json"
    facility_sizes = read_json(catalog_path).get("facility_sizes", {}) if catalog_path.exists() else {}
    renovation_model = operations_config.get("facility_renovation_model", {})
    construction_model = operations_config.get("facility_construction_model", {})
    rebuild_model = operations_config.get("facility_rebuild_model", {})
    catalog: list[dict[str, Any]] = []
    for template in PROJECT_TEMPLATES.values():
        project_type = str(template["projectType"])
        if project_type == "renovation":
            size = str(template["facilitySize"])
            replacement_cost = as_float(renovation_model.get("replacement_cost_million_cny_by_facility_size", {}).get(size))
            ratio = as_float(renovation_model.get("capex_ratio_by_facility_size", {}).get(size))
            cost_multiplier = as_float(renovation_model.get("city_construction_cost_multiplier"), 1.0)
            capex = replacement_cost * ratio * cost_multiplier
            duration = int(as_float(renovation_model.get("duration_quarters_by_facility_size", {}).get(size), 6.0))
            capacity_multiplier = as_float(renovation_model.get("default_construction_capacity_multiplier"), 0.75)
            demolition = 0.0
            target_size = size
        elif project_type == "construction":
            construction_sizes = allowed_construction_target_sizes(template)
            target_size = str(construction_sizes[0] if construction_sizes else "empty")
            construction_config = construction_event_config(target_size)
            capex = construction_config["capex_million_cny"]
            duration = int(construction_config["duration_quarters"])
            capacity_multiplier = 0.0
            demolition = 0.0
        elif project_type == "demolition":
            source_size = str(template["sourceFacilitySize"])
            demolition_config = demolition_event_config(source_size)
            target_size = "empty"
            capex = 0.0
            duration = int(demolition_config["duration_quarters"])
            capacity_multiplier = 0.0
            demolition = demolition_config["demolition_expense_million_cny"]
        else:
            target_size = str(template["targetFacilitySize"])
            source_size = str(template["sourceFacilitySize"])
            capex = as_float(rebuild_model.get("asset_cost_million_cny_by_facility_size", {}).get(target_size))
            capex *= as_float(rebuild_model.get("city_construction_cost_multiplier"), 1.0)
            duration = int(as_float(rebuild_model.get("duration_quarters_by_facility_size", {}).get(target_size), 18.0))
            capacity_multiplier = as_float(rebuild_model.get("default_construction_capacity_multiplier"), 0.0)
            demolition = as_float(rebuild_model.get("asset_cost_million_cny_by_facility_size", {}).get(source_size))
            demolition *= as_float(rebuild_model.get("demolition_cost_ratio_by_source_facility_size", {}).get(source_size))
            demolition *= as_float(rebuild_model.get("city_demolition_cost_multiplier"), 1.0)
        target_spec = facility_sizes.get(target_size, {})
        source_spec = facility_sizes.get(str(template.get("facilitySize") or template.get("sourceFacilitySize") or target_size), {})
        renovation_details = {}
        rebuild_details = {}
        demolition_details = {}
        construction_details = {}
        if project_type == "renovation":
            depreciation = renovation_model.get("renovation_asset_depreciation", {})
            quality_model = operations_config.get("commercial", {}).get("perceived_quality_model", {})
            renovation_details = {
                "replacementCost": round(replacement_cost, 4),
                "capexRatio": round(ratio, 4),
                "constructionCostMultiplier": round(cost_multiplier, 4),
                "usefulLifeYears": round(as_float(depreciation.get("useful_life_years"), 20.0), 4),
                "residualValuePct": round(as_float(depreciation.get("residual_value_pct"), 5.0), 4),
                "maintenanceAgeRetentionRatio": round(
                    as_float(renovation_model.get("maintenance_age_retention_ratio"), 0.55), 4
                ),
                "minimumEffectiveMaintenanceAgeYears": round(
                    as_float(renovation_model.get("minimum_effective_maintenance_age_years"), 5.0), 4
                ),
                "constructionQualityDisruptionScore": round(
                    as_float(quality_model.get("renovation_construction_disruption_score"), 0.0), 4
                ),
                "designCapacityLoss": round(
                    as_float(source_spec.get("design_capacity_million")) * (1.0 - capacity_multiplier), 4
                ),
                "maxCapacityLoss": round(
                    as_float(source_spec.get("max_capacity_million")) * (1.0 - capacity_multiplier), 4
                ),
                "renovationOptions": {
                    option_size: {
                        "durationQuarters": renovation_event_config(option_size)["duration_quarters"],
                        "totalCapex": renovation_event_config(option_size)["capex_million_cny"],
                        "designCapacityLoss": round(
                            as_float(facility_sizes.get(option_size, {}).get("design_capacity_million"))
                            * (1.0 - renovation_event_config(option_size)["construction_capacity_multiplier"]),
                            4,
                        ),
                    }
                    for option_size in facility_sizes
                    if option_size != "empty"
                },
            }
        elif project_type == "rebuild":
            source_size = str(template["sourceFacilitySize"])
            rebuild_details = {
                "rebuildAllowedTargetSizes": allowed_rebuild_target_sizes(template),
                "rebuildTargetOptions": {
                    size: {
                        "durationQuarters": rebuild_event_config(source_size, size)["duration_quarters"],
                        "demolitionDurationQuarters": rebuild_event_config(source_size, size)["demolition_duration_quarters"],
                        "constructionDurationQuarters": rebuild_event_config(source_size, size)["construction_duration_quarters"],
                        "totalCapex": rebuild_event_config(source_size, size)["asset_capex_million_cny"],
                        "demolitionExpense": rebuild_event_config(source_size, size)["demolition_expense_million_cny"],
                        "targetDesignCapacity": round(as_float(facility_sizes.get(size, {}).get("design_capacity_million")), 4),
                        "targetMaxCapacity": round(as_float(facility_sizes.get(size, {}).get("max_capacity_million")), 4),
                    }
                    for size in allowed_rebuild_target_sizes(template)
                },
                "rebuildTargetOptionsBySource": {
                    source_option: {
                        target_option: {
                            "durationQuarters": rebuild_event_config(source_option, target_option)["duration_quarters"],
                            "demolitionDurationQuarters": rebuild_event_config(source_option, target_option)["demolition_duration_quarters"],
                            "constructionDurationQuarters": rebuild_event_config(source_option, target_option)["construction_duration_quarters"],
                            "totalCapex": rebuild_event_config(source_option, target_option)["asset_capex_million_cny"],
                            "demolitionExpense": rebuild_event_config(source_option, target_option)["demolition_expense_million_cny"],
                            "targetDesignCapacity": round(as_float(facility_sizes.get(target_option, {}).get("design_capacity_million")), 4),
                            "targetMaxCapacity": round(as_float(facility_sizes.get(target_option, {}).get("max_capacity_million")), 4),
                        }
                        for target_option in allowed_rebuild_target_sizes(template)
                    }
                    for source_option in facility_sizes
                    if source_option != "empty"
                },
            }
        elif project_type == "demolition":
            demolition_details = {
                "demolitionOptionsBySource": {
                    source_option: {
                        "durationQuarters": demolition_event_config(source_option)["duration_quarters"],
                        "demolitionExpense": demolition_event_config(source_option)["demolition_expense_million_cny"],
                    }
                    for source_option in facility_sizes
                    if source_option != "empty"
                },
                "clearanceQuarters": DEMOLITION_CLEARANCE_QUARTERS,
            }
        elif project_type == "construction":
            construction_details = {
                "constructionAllowedTargetSizes": allowed_construction_target_sizes(template),
                "constructionTargetOptions": {
                    size: {
                        "durationQuarters": construction_event_config(size)["duration_quarters"],
                        "totalCapex": construction_event_config(size)["capex_million_cny"],
                        "targetDesignCapacity": round(as_float(facility_sizes.get(size, {}).get("design_capacity_million")), 4),
                        "targetMaxCapacity": round(as_float(facility_sizes.get(size, {}).get("max_capacity_million")), 4),
                    }
                    for size in allowed_construction_target_sizes(template)
                },
            }
        catalog.append(
            {
                **template,
                "durationQuarters": duration,
                "totalCapex": round(capex, 4),
                "demolitionExpense": round(demolition, 4),
                "constructionCapacityMultiplier": round(capacity_multiplier, 4),
                "targetDesignCapacity": round(as_float(target_spec.get("design_capacity_million")), 4),
                "targetMaxCapacity": round(as_float(target_spec.get("max_capacity_million")), 4),
                **renovation_details,
                **rebuild_details,
                **demolition_details,
                **construction_details,
            }
        )
    return catalog


def run_id_for(seed: int, years: int) -> str:
    return f"seed_{seed}_years_{years}"


def parse_run_id(run_id: str) -> tuple[int | None, int | None]:
    parts = run_id.split("_")
    try:
        seed_index = parts.index("seed") + 1
        years_index = parts.index("years") + 1
        return int(parts[seed_index]), int(parts[years_index])
    except (ValueError, IndexError):
        return None, None


def ensure_inside(parent: Path, child: Path) -> Path:
    parent_resolved = parent.resolve()
    child_resolved = child.resolve()
    if parent_resolved != child_resolved and parent_resolved not in child_resolved.parents:
        raise ValueError(f"path outside allowed root: {child_resolved}")
    return child_resolved


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def sim_save_path(seed: int, years: int) -> Path:
    run_dir = RUN_ROOT / run_id_for(seed, years)
    return ensure_inside(run_dir, run_dir / SIMULATION_DIR_NAME / "dynamic_test_save.json")


def sim_save_summary(seed: int, years: int, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    path = sim_save_path(seed, years)
    if not payload:
        return {
            "label": "当前 seed 存档",
            "occupied": False,
            "seed": seed,
            "years": years,
            "runId": run_id_for(seed, years),
            "savePath": str(path.relative_to(ROOT_DIR).as_posix()),
        }
    return {
        "label": "当前 seed 存档",
        "occupied": True,
        "seed": payload.get("seed", seed),
        "years": payload.get("years", years),
        "mode": payload.get("mode"),
        "runId": payload.get("runId", run_id_for(seed, years)),
        "savePath": str(path.relative_to(ROOT_DIR).as_posix()),
        "currentQuarterIndex": payload.get("currentQuarterIndex"),
        "currentLabel": payload.get("currentLabel", ""),
        "savedAt": payload.get("savedAt", ""),
        "savedAtUnix": payload.get("savedAtUnix", 0),
        "contractSignatureCount": len(payload.get("contractSignatures", {}) or {}),
        "playerActionCount": len(payload.get("playerActions", []) or []),
        "projectActionCount": len(
            [action for action in payload.get("playerActions", []) if action.get("type") == "start_project"]
        ),
        "slotRenameCount": len(
            [action for action in payload.get("playerActions", []) if action.get("type") == "rename_slot"]
        ),
        "operationOverrideQuarterCount": 0,
    }


def read_sim_save(seed: int, years: int) -> dict[str, Any] | None:
    path = sim_save_path(seed, years)
    if not path.exists():
        return None
    payload = read_json(path)
    payload["seed"] = seed
    payload["years"] = years
    payload["runId"] = run_id_for(seed, years)
    return payload


def save_sim_save(body: dict[str, Any]) -> dict[str, Any]:
    seed = clean_seed(body.get("seed"))
    years = clean_years(body.get("years", 60))
    mode = clean_operation_mode(body.get("mode", "simulate_default"))
    if mode != "simulate_default":
        raise ValueError("dynamic test save only supports simulate_default mode")
    run_dir = RUN_ROOT / run_id_for(seed, years)
    if not run_dir.exists():
        raise FileNotFoundError("请先加载当前 seed 的模拟运营，再保存动态测试存档")
    current_index = int(as_float(body.get("currentQuarterIndex"), 0.0))
    contract_signatures = body.get("contractSignatures", {})
    if not isinstance(contract_signatures, dict):
        contract_signatures = {}
    player_actions = clean_player_actions(body.get("playerActions", []))
    now = time.time()
    payload = {
        "schemaVersion": "seed-explorer-simulation-save-v0.3",
        "seed": seed,
        "years": years,
        "mode": mode,
        "runId": str(body.get("runId") or run_id_for(seed, years)),
        "runDir": str(body.get("runDir") or ""),
        "currentQuarterIndex": max(0, current_index),
        "currentLabel": str(body.get("currentLabel") or ""),
        "contractSignatures": contract_signatures,
        "contractAffairsContractId": str(body.get("contractAffairsContractId") or "DUTY_FREE_MAIN"),
        "playerActions": player_actions,
        "savedAtUnix": round(now, 3),
        "savedAt": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now)),
        "note": "Seed-bound dynamic-test save. Stores the current quarter and player action journal; server-generated quarterly results are rebuilt and are not copied into the save.",
    }
    write_json(sim_save_path(seed, years), payload)
    return payload


def clear_sim_save(seed: int, years: int) -> None:
    path = sim_save_path(seed, years)
    if path.exists():
        path.unlink()


def cagr_pct(start_value: float, end_value: float, years: int) -> float:
    if start_value <= 0.0 or end_value <= 0.0 or years <= 0:
        return 0.0
    return (math.pow(end_value / start_value, 1.0 / years) - 1.0) * 100.0


def market_bottleneck(potential: float, supply: float) -> str:
    return "airline_supply_limited" if supply < potential else "demand_limited"


def summarize_city(rows: list[dict[str, str]]) -> dict[str, Any]:
    first = rows[0]
    last = rows[-1]
    start_year = int(as_float(first.get("year")))
    final_year = int(as_float(last.get("year")))
    first_effective = min(
        as_float(first.get("city_potential_passengers_million")),
        as_float(first.get("city_airline_supply_passengers_million")),
    )
    final_potential = as_float(last.get("city_potential_passengers_million"))
    final_supply = as_float(last.get("city_airline_supply_passengers_million"))
    final_effective = min(final_potential, final_supply)
    peak_effective = max(
        min(
            as_float(row.get("city_potential_passengers_million")),
            as_float(row.get("city_airline_supply_passengers_million")),
        )
        for row in rows
    )
    bottleneck_years = {
        "airline_supply_limited": 0,
        "demand_limited": 0,
    }
    points: list[dict[str, Any]] = []
    for row in rows:
        potential = as_float(row.get("city_potential_passengers_million"))
        supply = as_float(row.get("city_airline_supply_passengers_million"))
        effective = min(potential, supply)
        bottleneck = str(row.get("city_binding_bottleneck") or market_bottleneck(potential, supply))
        if bottleneck not in bottleneck_years:
            bottleneck_years[bottleneck] = 0
        bottleneck_years[bottleneck] += 1
        points.append(
            {
                "year": int(as_float(row.get("year"))),
                "potential": round(potential, 4),
                "airlineSupply": round(supply, 4),
                "effective": round(effective, 4),
                "served": round(as_float(row.get("city_served_passengers_million"), effective), 4),
                "supplyGap": round(max(0.0, potential - supply), 4),
                "supplyFulfillmentPct": round(as_float(row.get("city_airline_supply_fulfillment_pct")), 4),
                "bindingBottleneck": bottleneck,
                "supplyRegime": str(row.get("city_airline_supply_regime") or ""),
                "supplyVolatilityRegime": str(row.get("city_airline_supply_volatility_regime") or ""),
            }
        )

    return {
        "id": str(first.get("city_airport_market_id") or ""),
        "name": str(first.get("city_name") or first.get("city_airport_market_id") or ""),
        "region": str(first.get("region_name") or first.get("region_id") or ""),
        "marketTier": str(first.get("market_tier") or ""),
        "marketType": str(first.get("market_type") or ""),
        "startYear": start_year,
        "finalYear": final_year,
        "finalPotential": round(final_potential, 4),
        "finalAirlineSupply": round(final_supply, 4),
        "finalEffective": round(final_effective, 4),
        "finalSupplyGap": round(max(0.0, final_potential - final_supply), 4),
        "effectiveCagrPct": round(cagr_pct(first_effective, final_effective, final_year - start_year), 4),
        "peakEffective": round(peak_effective, 4),
        "finalBottleneck": market_bottleneck(final_potential, final_supply),
        "bottleneckYears": bottleneck_years,
        "points": points,
    }


def aggregate_run(run_dir: Path, seed: int, years: int, elapsed_sec: float, cached: bool) -> dict[str, Any]:
    city_dir = run_dir / "baseline" / "city_airport_market_demand" / "china_mainland"
    files = sorted(city_dir.glob("*_city_airport_demand_seed_sweep.csv"))
    if not files:
        raise FileNotFoundError(f"no city airport market output found in {city_dir}")
    cities = []
    for path in files:
        rows = read_csv(path)
        if rows:
            cities.append(summarize_city(rows))
    cities.sort(key=lambda item: item["finalEffective"], reverse=True)
    rankings = [
        {
            "rank": index + 1,
            "id": city["id"],
            "name": city["name"],
            "finalEffective": city["finalEffective"],
            "finalPotential": city["finalPotential"],
            "finalAirlineSupply": city["finalAirlineSupply"],
        }
        for index, city in enumerate(cities)
    ]
    return {
        "seed": seed,
        "years": years,
        "cached": cached,
        "elapsedSec": round(elapsed_sec, 2),
        "runId": run_dir.name,
        "runDir": str(run_dir.relative_to(ROOT_DIR).as_posix()),
        "generatedAt": time.strftime("%Y-%m-%d %H:%M:%S"),
        "cityCount": len(cities),
        "startYear": min(city["startYear"] for city in cities),
        "finalYear": max(city["finalYear"] for city in cities),
        "cities": cities,
        "rankings": rankings,
    }


def cache_path(run_dir: Path) -> Path:
    return run_dir / "seed_explorer_city_market_cache.json"


def load_cached(run_dir: Path) -> dict[str, Any] | None:
    path = cache_path(run_dir)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_cached(run_dir: Path, payload: dict[str, Any]) -> None:
    cache_path(run_dir).write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def cached_run_entry(run_dir: Path) -> dict[str, Any]:
    payload = load_cached(run_dir) or {}
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
        "lastWriteTime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime)),
        "hasCityCache": cache_path(run_dir).exists(),
        "hasBeijingOperations": (run_dir / BEIJING_OPERATIONS_RELATIVE_CSV).exists(),
    }


def list_cached_runs() -> list[dict[str, Any]]:
    if not RUN_ROOT.exists():
        return []
    prune_cached_runs()
    run_dirs = [path for path in RUN_ROOT.iterdir() if path.is_dir()]
    run_dirs.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    return [cached_run_entry(path) for path in run_dirs]


def prune_cached_runs() -> None:
    if not RUN_ROOT.exists():
        return
    run_dirs = [path for path in RUN_ROOT.iterdir() if path.is_dir()]
    stale = sorted(run_dirs, key=lambda path: path.stat().st_mtime, reverse=True)[MAX_CACHED_RUNS:]
    for path in stale:
        resolved = ensure_inside(RUN_ROOT, path)
        shutil.rmtree(resolved)


def run_orchestrator(seed: int, years: int, run_dir: Path, force: bool) -> tuple[float, str]:
    if force and run_dir.exists():
        resolved = ensure_inside(RUN_ROOT, run_dir)
        shutil.rmtree(resolved)
    RUN_ROOT.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    cmd = [
        sys.executable,
        str(ORCHESTRATOR),
        "--seed",
        str(seed),
        "--years",
        str(years),
        "--scenario-state",
        "none",
        "--run-id",
        run_dir.name,
        "--output-root",
        str(RUN_ROOT),
        "--viewer-output-root",
        str(ROOT_DIR / "output" / "seed_explorer_viewer"),
        "--publish-viewer",
        "none",
    ]
    result = subprocess.run(
        cmd,
        cwd=str(ROOT_DIR),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=240,
    )
    elapsed = time.perf_counter() - started
    output_tail = (result.stdout + "\n" + result.stderr)[-6000:]
    if result.returncode != 0:
        raise RuntimeError(f"orchestrator failed with code {result.returncode}\n{output_tail}")
    return elapsed, output_tail


def run_seed(seed: int, years: int, force: bool) -> dict[str, Any]:
    run_dir = RUN_ROOT / run_id_for(seed, years)
    cached_payload = None if force else load_cached(run_dir)
    if cached_payload:
        cached_payload["cached"] = True
        cached_payload["elapsedSec"] = 0.0
        return cached_payload

    with RUN_LOCK:
        cached_payload = None if force else load_cached(run_dir)
        if cached_payload:
            cached_payload["cached"] = True
            cached_payload["elapsedSec"] = 0.0
            return cached_payload
        elapsed, _ = run_orchestrator(seed, years, run_dir, force)
        payload = aggregate_run(run_dir, seed, years, elapsed, cached=False)
        save_cached(run_dir, payload)
        prune_cached_runs()
        return payload


def update_simulation_city_row(row: dict[str, str]) -> dict[str, Any]:
    updated: dict[str, Any] = dict(row)
    potential = as_float(row.get("city_potential_passengers_million"))
    airline_supply = as_float(row.get("city_airline_supply_passengers_million"), potential)
    serviceable_demand = min(potential, airline_supply)
    served = min(serviceable_demand, INITIAL_MAX_CAPACITY_MILLION)
    allocation_ratio = (
        min(100.0, INITIAL_MAX_CAPACITY_MILLION / airline_supply * 100.0)
        if airline_supply > 0
        else 100.0
    )
    capacity_fulfillment = served / serviceable_demand * 100.0 if serviceable_demand > 0 else 100.0
    total_fulfillment = served / potential * 100.0 if potential > 0 else 100.0
    design_utilization = (
        served / INITIAL_DESIGN_CAPACITY_MILLION * 100.0 if INITIAL_DESIGN_CAPACITY_MILLION > 0 else 0.0
    )
    max_utilization = served / INITIAL_MAX_CAPACITY_MILLION * 100.0 if INITIAL_MAX_CAPACITY_MILLION > 0 else 0.0
    airline_supply_gap = max(0.0, potential - airline_supply)
    airport_capacity_gap = max(0.0, serviceable_demand - INITIAL_MAX_CAPACITY_MILLION)
    if airport_capacity_gap > 0.0:
        bottleneck = "airport_capacity_limited"
    elif airline_supply < potential:
        bottleneck = "airline_supply_limited"
    else:
        bottleneck = "demand_limited"

    updated.update(
        {
            "active_airport_facility_slots": INITIAL_ACTIVE_FACILITY_SLOTS,
            "city_airport_design_capacity_million": round(INITIAL_DESIGN_CAPACITY_MILLION, 4),
            "city_airport_max_capacity_million": round(INITIAL_MAX_CAPACITY_MILLION, 4),
            "city_effective_capacity_million": round(INITIAL_MAX_CAPACITY_MILLION, 4),
            "airport_capacity_allocation_ratio_pct": round(allocation_ratio, 4),
            "airport_capacity_limited_airline_supply_million": round(max(0.0, airline_supply - INITIAL_MAX_CAPACITY_MILLION), 4),
            "city_effective_service_capacity_million": round(min(airline_supply, INITIAL_MAX_CAPACITY_MILLION), 4),
            "city_capacity_utilization_pct": round(max_utilization, 4),
            "city_airport_design_utilization_pct": round(design_utilization, 4),
            "city_airport_max_utilization_pct": round(max_utilization, 4),
            "city_capacity_fulfillment_pct": round(capacity_fulfillment, 4),
            "city_airport_throughput_utilization_pct": round(max_utilization, 4),
            "city_airport_crowding_index": round(max(0.0, design_utilization - 100.0), 4),
            "city_total_fulfillment_pct": round(total_fulfillment, 4),
            "final_passenger_service_ratio_pct": round(total_fulfillment, 4),
            "city_served_passengers_million": round(served, 4),
            "city_unmet_passengers_million": round(max(0.0, potential - served), 4),
            "city_unmet_demand_share_pct": round(100.0 - total_fulfillment, 4),
            "city_airline_supply_gap_million": round(airline_supply_gap, 4),
            "city_airport_capacity_gap_million": round(airport_capacity_gap, 4),
            "city_binding_bottleneck": bottleneck,
            "city_capacity_regime": "initial_capacity_frozen",
            "airport_event_hint": "simulation_default_no_player_projects",
        }
    )

    component_scale = served / potential if potential > 0 else 0.0
    for component in ("business", "leisure", "vfr", "long_haul", "transfer"):
        component_potential = as_float(row.get(f"{component}_passengers_million"))
        component_supply = as_float(row.get(f"{component}_airline_supply_passengers_million"))
        updated[f"{component}_served_passengers_million"] = round(component_potential * component_scale, 4)
        updated[f"{component}_airline_supply_gap_million"] = round(max(0.0, component_potential - component_supply), 4)
        updated[f"{component}_airline_supply_fulfillment_pct"] = round(
            component_supply / component_potential * 100.0 if component_potential > 0 else 100.0,
            4,
        )
    return updated


def write_default_simulation_city_demand_csv(run_dir: Path) -> Path:
    source_path = run_dir / BEIJING_CITY_DEMAND_RELATIVE_CSV
    target_path = run_dir / SIMULATION_CITY_DEMAND_RELATIVE_CSV
    if not source_path.exists():
        raise FileNotFoundError(f"no Beijing city demand output found in {source_path}")
    rows = read_csv(source_path)
    if not rows:
        raise FileNotFoundError(f"no Beijing city demand rows found in {source_path}")
    fieldnames = list(rows[0].keys())
    write_csv(target_path, [update_simulation_city_row(row) for row in rows], fieldnames)
    return target_path


def write_player_simulation_configs(
    run_dir: Path,
    player_actions: list[dict[str, Any]],
) -> tuple[Path, Path]:
    config_dir = run_dir / SIMULATION_DIR_NAME / "configs"
    operations_config = read_json(BEIJING_OPERATIONS_CONFIG)
    operations_config["config_version"] = f"{operations_config.get('config_version', 'beijing-operations')}-simulate-default"
    operations_config["simulation_mode"] = "simulate_default"
    operations_config["simulation_design_note"] = (
        "Player-operation sandbox: commercial signatures and slot-level project starts are replayed "
        "from the seed-bound player action journal."
    )
    project_events = player_project_events(player_actions)
    operations_config["facility_renovation_events"] = project_events["facility_renovation_events"]
    operations_config["facility_construction_events"] = project_events["facility_construction_events"]
    operations_config["facility_rebuild_events"] = project_events["facility_rebuild_events"]
    operations_config["player_contract_actions"] = player_actions

    finance_config = read_json(BEIJING_FINANCE_CONFIG)
    finance_config["config_version"] = f"{finance_config.get('config_version', 'beijing-finance')}-simulate-default"
    finance_config["simulation_mode"] = "simulate_default"
    finance_config["simulation_design_note"] = "Player-operation sandbox: loans are replayed from the seed-bound player action journal."
    finance_config["general_loans"] = player_general_loans(player_actions)

    operations_config_path = config_dir / "beijing_airport_system_quarterly_operations_simulate_default.json"
    finance_config_path = config_dir / "beijing_airport_group_financial_state_simulate_default.json"
    write_json(operations_config_path, operations_config)
    write_json(finance_config_path, finance_config)
    return operations_config_path, finance_config_path


def run_layer_command(cmd: list[str], label: str) -> None:
    result = subprocess.run(
        cmd,
        cwd=str(ROOT_DIR),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=180,
    )
    if result.returncode != 0:
        output_tail = (result.stdout + "\n" + result.stderr)[-6000:]
        raise RuntimeError(f"{label} failed with code {result.returncode}\n{output_tail}")


def ensure_player_simulation_outputs(
    run_dir: Path,
    player_actions: list[dict[str, Any]],
    force: bool,
) -> bool:
    simulation_dir = run_dir / SIMULATION_DIR_NAME
    operations_path = run_dir / SIMULATION_OPERATIONS_RELATIVE_CSV
    financial_path = run_dir / SIMULATION_FINANCIAL_RELATIVE_CSV
    manifest_path = simulation_dir / "action_cache_manifest.json"
    fingerprint_source = {
        "player_actions": player_actions,
        "operations_config": hashlib.sha256(BEIJING_OPERATIONS_CONFIG.read_bytes()).hexdigest(),
        "finance_config": hashlib.sha256(BEIJING_FINANCE_CONFIG.read_bytes()).hexdigest(),
        "operations_script": hashlib.sha256(QUARTERLY_OPERATIONS_SCRIPT.read_bytes()).hexdigest(),
        "finance_script": hashlib.sha256(FINANCIAL_STATE_SCRIPT.read_bytes()).hexdigest(),
        "simulation_server": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    fingerprint = hashlib.sha256(
        json.dumps(fingerprint_source, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    if not force and operations_path.exists() and financial_path.exists() and manifest_path.exists():
        try:
            manifest = read_json(manifest_path)
            if manifest.get("fingerprint") == fingerprint:
                return True
        except (OSError, ValueError, json.JSONDecodeError):
            pass

    # Player actions can alter any later quarter. Rebuild only when their
    # journal or a simulation dependency changed; quarter browsing is cached.
    if simulation_dir.exists():
        shutil.rmtree(ensure_inside(run_dir, simulation_dir))

    city_demand_path = write_default_simulation_city_demand_csv(run_dir)
    operations_config_path, finance_config_path = write_player_simulation_configs(run_dir, player_actions)
    operations_output_dir = run_dir / SIMULATION_DIR_NAME / "city_airport_quarterly_operations"
    financial_output_dir = run_dir / SIMULATION_DIR_NAME / "city_airport_financial_state"

    run_layer_command(
        [
            sys.executable,
            str(QUARTERLY_OPERATIONS_SCRIPT),
            "--market",
            "beijing_airport_system",
            "--city-demand-csv",
            str(city_demand_path),
            "--config",
            str(operations_config_path),
            "--output-dir",
            str(operations_output_dir),
        ],
        "default simulation quarterly operations",
    )
    run_layer_command(
        [
            sys.executable,
            str(FINANCIAL_STATE_SCRIPT),
            "--market",
            "beijing_airport_system",
            "--quarterly-operations-csv",
            str(operations_path),
            "--config",
            str(finance_config_path),
            "--output-dir",
            str(financial_output_dir),
        ],
        "default simulation financial state",
    )
    write_json(manifest_path, {"fingerprint": fingerprint})
    return False


def non_empty_ids(*values: str) -> list[str]:
    ids: list[str] = []
    for value in values:
        for item in str(value or "").replace("|", ";").replace(",", ";").split(";"):
            clean = item.strip()
            if clean and clean not in ids:
                ids.append(clean)
    return ids


def quarter_key(row: dict[str, str]) -> tuple[int, str]:
    return int(as_float(row.get("year"))), as_text(row, "quarter")


def quarter_warnings(ops: dict[str, str], finance: dict[str, str]) -> list[str]:
    warnings: list[str] = []
    if rounded(ops, "quarter_design_utilization_pct", 2) >= 100.0:
        warnings.append("超过设计容量")
    if rounded(ops, "quarter_max_utilization_pct", 2) >= 95.0:
        warnings.append("接近极限容量")
    if rounded(ops, "quarter_crowding_index", 2) > 0.0:
        warnings.append("拥挤成本生效")
    if rounded(finance, "period_end_cash_million_cny", 2) < 0.0:
        warnings.append("现金为负")
    if as_text(finance, "loan_blocked_ids"):
        warnings.append("贷款被拒")
    if as_text(ops, "renovation_active_event_ids"):
        warnings.append("翻新施工")
    if as_text(ops, "construction_active_event_ids"):
        warnings.append("新建施工")
    if as_text(ops, "rebuild_active_event_ids"):
        warnings.append("重建施工")
    return warnings


def summarize_beijing_quarter(index: int, ops: dict[str, str], finance: dict[str, str]) -> dict[str, Any]:
    year = int(as_float(ops.get("year")))
    quarter = as_text(ops, "quarter")
    total_assets = rounded(finance, "total_assets_million_cny")
    total_liabilities = rounded(finance, "total_liabilities_million_cny")
    end_cash = rounded(finance, "period_end_cash_million_cny")
    liability_ratio_pct = (total_liabilities / total_assets * 100.0) if total_assets > 0 else 0.0
    capex = (
        rounded(finance, "period_total_capex_outlay_million_cny")
        or rounded(ops, "renovation_quarter_capex_outlay_million_cny")
        + rounded(ops, "construction_quarter_capex_outlay_million_cny")
        + rounded(ops, "rebuild_quarter_capex_outlay_million_cny")
    )
    return {
        "index": index,
        "year": year,
        "quarter": quarter,
        "label": f"{year} {quarter}",
        "gamePhase": as_text(ops, "game_phase"),
        "playerDecisionEnabled": as_bool(ops.get("player_decision_enabled")),
        "demand": {
            "annualPotential": rounded(ops, "annual_city_potential_passengers_million"),
            "annualAirlineSupply": rounded(ops, "annual_city_airline_supply_passengers_million"),
            "annualServed": rounded(ops, "annual_served_passengers_million"),
            "quarterPotential": rounded(ops, "quarter_city_potential_passengers_million"),
            "quarterAirlineSupply": rounded(ops, "quarter_airline_supply_passengers_million"),
            "quarterServiceableDemand": rounded(ops, "quarter_serviceable_demand_million"),
            "quarterServed": rounded(ops, "quarter_served_passengers_million"),
            "capacityLost": rounded(ops, "quarter_capacity_lost_passengers_million"),
            "airlineSupplyGap": rounded(ops, "quarter_airline_supply_gap_million"),
            "bindingBottleneck": as_text(ops, "annual_city_binding_bottleneck"),
            "componentServed": {
                "business": rounded(ops, "business_quarter_served_passengers_million"),
                "leisure": rounded(ops, "leisure_quarter_served_passengers_million"),
                "vfr": rounded(ops, "vfr_quarter_served_passengers_million"),
                "longHaul": rounded(ops, "long_haul_quarter_served_passengers_million"),
                "transfer": rounded(ops, "transfer_quarter_served_passengers_million"),
            },
        },
        "capacity": {
            "cityDesignCapacity": rounded(ops, "city_airport_design_capacity_million"),
            "cityMaxCapacity": rounded(ops, "city_airport_max_capacity_million"),
            "quarterDesignCapacity": rounded(ops, "quarter_design_capacity_million"),
            "quarterMaxCapacity": rounded(ops, "quarter_max_capacity_million"),
            "designUtilizationPct": rounded(ops, "quarter_design_utilization_pct"),
            "maxUtilizationPct": rounded(ops, "quarter_max_utilization_pct"),
            "capacityRealizationPct": rounded(ops, "quarter_capacity_realization_factor_pct"),
            "crowdingIndex": rounded(ops, "quarter_crowding_index"),
            "perceivedQualityIndex": rounded(ops, "city_airport_perceived_quality_index"),
            "perceivedQualitySizeScore": rounded(ops, "perceived_quality_size_score"),
            "perceivedQualityAgeScore": rounded(ops, "perceived_quality_age_score"),
            "perceivedQualityCapacityScore": rounded(ops, "perceived_quality_capacity_score"),
            "perceivedQualityConstructionDisruptionScore": rounded(
                ops,
                "perceived_quality_construction_disruption_score",
            ),
            "activeFacilitySlots": as_text(ops, "active_facility_slots"),
            "effectiveFacilitySlots": as_text(ops, "effective_facility_slots"),
        },
        "operations": {
            "aeronauticalRevenue": rounded(ops, "aeronautical_revenue_million_cny"),
            "foodRetailRevenue": rounded(ops, "food_retail_revenue_million_cny"),
            "foodRetailFixedCost": rounded(ops, "food_retail_fixed_operating_cost_million_cny"),
            "foodRetailPassengerServiceCost": rounded(
                ops,
                "food_retail_passenger_service_cost_million_cny",
            ),
            "foodRetailSalesCost": rounded(ops, "food_retail_sales_cost_million_cny"),
            "foodRetailCost": rounded(ops, "food_retail_operating_cost_million_cny"),
            "foodRetailProfit": rounded(ops, "food_retail_operating_profit_million_cny"),
            "foodRetailQualityMultiplier": rounded(ops, "food_retail_perceived_quality_revenue_multiplier"),
            "dutyFreeRevenue": rounded(ops, "duty_free_revenue_million_cny"),
            "luxuryRevenue": rounded(ops, "luxury_retail_revenue_million_cny"),
            "commercialRevenue": rounded(ops, "commercial_revenue_million_cny"),
            "commercialDirectCost": rounded(ops, "commercial_direct_cost_million_cny"),
            "commercialProfit": rounded(ops, "commercial_operating_profit_million_cny"),
            "dutyFreeSales": rounded(ops, "duty_free_sales_million_cny"),
            "dutyFreeWeightedPassengers": rounded(ops, "duty_free_weighted_passengers_million"),
            "dutyFreeMarketCycleMultiplier": rounded(ops, "duty_free_market_cycle_multiplier"),
            "dutyFreeQualityMultiplier": rounded(ops, "duty_free_perceived_quality_sales_multiplier"),
            "dutyFreeMinimumGuarantee": rounded(ops, "duty_free_contract_minimum_guarantee_million_cny"),
            "dutyFreeShareRevenue": rounded(ops, "duty_free_contract_share_revenue_million_cny"),
            "dutyFreeRevenueSharePct": rounded(ops, "duty_free_revenue_share_pct"),
            "dutyFreeMinimumGuaranteeCoveragePct": rounded(ops, "duty_free_minimum_guarantee_coverage_pct"),
            "dutyFreeRevenueBasis": as_text(ops, "duty_free_contract_revenue_basis"),
            "dutyFreeContractType": as_text(ops, "duty_free_contract_type"),
            "dutyFreeContractStatus": as_text(ops, "duty_free_contract_status"),
            "dutyFreeContractCycle": as_text(ops, "duty_free_contract_cycle_id"),
            "dutyFreeContractCycleStartYear": rounded(ops, "duty_free_contract_cycle_start_year"),
            "dutyFreeContractCycleEndYear": rounded(ops, "duty_free_contract_cycle_end_year"),
            "dutyFreeContractForecastQuarterSales": rounded(
                ops,
                "duty_free_contract_forecast_quarter_sales_million_cny",
            ),
            "dutyFreeContractForecastAnnualSales": rounded(
                ops,
                "duty_free_contract_forecast_annual_sales_million_cny",
            ),
            "dutyFreeContractHistoryYearsUsed": rounded(ops, "duty_free_contract_history_years_used"),
            "dutyFreeContractTrendMultiplier": rounded(ops, "duty_free_contract_trend_multiplier"),
            "dutyFreeContractMacroRiskDiscountMultiplier": rounded(
                ops,
                "duty_free_contract_macro_risk_discount_multiplier",
            ),
            "dutyFreeContractBargainingPowerMultiplier": rounded(
                ops,
                "duty_free_contract_bargaining_power_multiplier",
            ),
            "luxurySales": rounded(ops, "luxury_sales_million_cny"),
            "luxuryWeightedPassengers": rounded(ops, "luxury_weighted_passengers_million"),
            "luxuryMarketCycleMultiplier": rounded(ops, "luxury_market_cycle_multiplier"),
            "luxuryQualityMultiplier": rounded(ops, "luxury_perceived_quality_sales_multiplier"),
            "luxuryMinimumGuarantee": rounded(ops, "luxury_contract_minimum_guarantee_million_cny"),
            "luxuryShareRevenue": rounded(ops, "luxury_contract_share_revenue_million_cny"),
            "luxuryRevenueSharePct": rounded(ops, "luxury_revenue_share_pct"),
            "luxuryMinimumGuaranteeCoveragePct": rounded(ops, "luxury_minimum_guarantee_coverage_pct"),
            "luxuryRevenueBasis": as_text(ops, "luxury_contract_revenue_basis"),
            "luxuryContractType": as_text(ops, "luxury_contract_type"),
            "luxuryContractStatus": as_text(ops, "luxury_contract_status"),
            "luxuryContractCycle": as_text(ops, "luxury_contract_cycle_id"),
            "luxuryContractCycleStartYear": rounded(ops, "luxury_contract_cycle_start_year"),
            "luxuryContractCycleEndYear": rounded(ops, "luxury_contract_cycle_end_year"),
            "luxuryContractForecastQuarterSales": rounded(
                ops,
                "luxury_contract_forecast_quarter_sales_million_cny",
            ),
            "luxuryContractForecastAnnualSales": rounded(
                ops,
                "luxury_contract_forecast_annual_sales_million_cny",
            ),
            "luxuryContractHistoryYearsUsed": rounded(ops, "luxury_contract_history_years_used"),
            "luxuryContractTrendMultiplier": rounded(ops, "luxury_contract_trend_multiplier"),
            "luxuryContractMacroRiskDiscountMultiplier": rounded(
                ops,
                "luxury_contract_macro_risk_discount_multiplier",
            ),
            "luxuryContractBargainingPowerMultiplier": rounded(
                ops,
                "luxury_contract_bargaining_power_multiplier",
            ),
            "totalRevenue": rounded(ops, "total_operating_revenue_million_cny"),
            "totalCost": rounded(ops, "total_operating_cost_million_cny"),
            "operatingProfit": rounded(ops, "quarter_operating_profit_million_cny"),
            "operatingMarginPct": rounded(ops, "operating_margin_pct"),
            "slotFixedCost": rounded(ops, "quarter_slot_fixed_operating_cost_million_cny"),
            "passengerVariableCost": rounded(ops, "quarter_passenger_variable_cost_million_cny"),
            "congestionCost": rounded(ops, "quarter_congestion_cost_million_cny"),
            "revenuePerPassengerCny": rounded(ops, "total_revenue_per_passenger_cny"),
            "costPerPassengerCny": rounded(ops, "total_cost_per_passenger_cny"),
        },
        "finance": {
            "beginCash": rounded(finance, "period_begin_cash_million_cny"),
            "endCash": end_cash,
            "totalAssets": total_assets,
            "totalLiabilities": total_liabilities,
            "accountingDepreciation": rounded(finance, "period_accounting_depreciation_million_cny"),
            "interestExpense": rounded(finance, "period_interest_expense_million_cny"),
            "pretaxProfit": rounded(finance, "period_pretax_accounting_profit_million_cny"),
            "incomeTaxExpense": rounded(finance, "period_income_tax_expense_million_cny"),
            "cashTaxPaid": rounded(finance, "period_cash_tax_paid_million_cny"),
            "accountingProfit": rounded(finance, "period_accounting_profit_million_cny"),
            "freeCashFlowBeforeFinancing": rounded(finance, "period_free_cash_flow_before_financing_million_cny"),
            "loanDrawdown": rounded(finance, "period_loan_drawdown_million_cny"),
            "principalRepayment": rounded(finance, "period_principal_repayment_million_cny"),
            "debtService": rounded(finance, "period_debt_service_million_cny"),
            "financingCashFlow": rounded(finance, "period_financing_cash_flow_million_cny"),
            "capexOutlay": round(capex, 4),
            "rebuildDemolitionExpense": rounded(
                finance,
                "period_rebuild_demolition_expense_million_cny",
            ),
            "rebuildOldAssetWriteoff": rounded(
                finance,
                "period_rebuild_old_asset_writeoff_million_cny",
            ),
            "constructionInProgress": rounded(finance, "construction_in_progress_million_cny"),
            "initialFixedAssetOriginal": rounded(finance, "initial_fixed_asset_original_million_cny"),
            "initialFixedAssetResidualFloor": rounded(
                finance,
                "initial_fixed_asset_residual_floor_million_cny",
            ),
            "initialFixedAssetAccumulatedDepreciation": rounded(
                finance,
                "initial_fixed_asset_accumulated_depreciation_million_cny",
            ),
            "initialFixedAssetBookValue": rounded(finance, "initial_fixed_asset_book_value_million_cny"),
            "initialFixedAssetPeriodDepreciation": rounded(
                finance,
                "initial_fixed_asset_period_depreciation_million_cny",
            ),
            "fixedAssetOriginal": rounded(finance, "fixed_asset_original_million_cny"),
            "fixedAssetAccumulatedDepreciation": rounded(
                finance,
                "fixed_asset_accumulated_depreciation_million_cny",
            ),
            "fixedAssetBookValue": rounded(finance, "fixed_asset_book_value_million_cny"),
            "totalNoncurrentAssets": rounded(finance, "total_noncurrent_assets_million_cny"),
            "totalAssets": total_assets,
            "grossDebt": total_liabilities,
            "netDebt": round(total_liabilities - end_cash, 4),
            "shortTermDebt": rounded(finance, "short_term_debt_million_cny"),
            "longTermDebt": rounded(finance, "long_term_debt_million_cny"),
            "totalLiabilities": total_liabilities,
            "totalEquity": rounded(finance, "total_equity_million_cny"),
            "liabilityRatioPct": round(liability_ratio_pct, 4),
            "loanActiveIds": as_text(finance, "loan_active_ids"),
            "loanDrawdownIds": as_text(finance, "loan_drawdown_ids"),
            "loanPrincipalRepaymentIds": as_text(finance, "loan_principal_repayment_ids"),
            "loanWeightedInterestRatePct": rounded(finance, "loan_weighted_interest_rate_pct"),
            "loanDrawdownWeightedInterestRatePct": rounded(finance, "loan_drawdown_weighted_interest_rate_pct"),
            "loanDrawdownLeverageBeforePct": rounded(finance, "loan_drawdown_leverage_before_pct"),
            "loanDrawdownLeverageAfterPct": rounded(finance, "loan_drawdown_leverage_after_pct"),
            "loanDrawdownLeverageSpreadBps": rounded(finance, "loan_drawdown_leverage_spread_bps"),
            "loanBlockedIds": as_text(finance, "loan_blocked_ids"),
            "loanBlockedReasons": as_text(finance, "loan_blocked_reasons"),
            "macroTenYearYieldPct": rounded(ops, "input_10y_yield_pct"),
            "macroHySpreadBps": rounded(ops, "input_hy_spread_bps"),
        },
        "projects": {
            "renovationActiveIds": as_text(ops, "renovation_active_event_ids"),
            "renovationCompletedIds": as_text(ops, "renovation_completed_event_ids"),
            "renovationAssetInServicePeriods": rounded(ops, "renovation_asset_in_service_periods"),
            "renovationDesignCapacityLoss": rounded(ops, "renovation_design_capacity_loss_million"),
            "renovationMaxCapacityLoss": rounded(ops, "renovation_max_capacity_loss_million"),
            "renovationCapex": rounded(ops, "renovation_quarter_capex_outlay_million_cny"),
            "renovationConstructionInProgress": rounded(
                ops,
                "renovation_construction_in_progress_million_cny",
            ),
            "renovationAssetOriginal": rounded(ops, "renovation_asset_original_million_cny"),
            "renovationAssetAccumulatedDepreciation": rounded(
                ops,
                "renovation_asset_accumulated_depreciation_million_cny",
            ),
            "renovationAssetBookValue": rounded(ops, "renovation_asset_book_value_million_cny"),
            "renovationAssetPeriodDepreciation": rounded(
                ops,
                "renovation_asset_period_depreciation_million_cny",
            ),
            "constructionActiveIds": as_text(ops, "construction_active_event_ids"),
            "constructionCompletedIds": as_text(ops, "construction_completed_event_ids"),
            "constructionAssetInServicePeriods": rounded(ops, "construction_asset_in_service_periods"),
            "constructionCapex": rounded(ops, "construction_quarter_capex_outlay_million_cny"),
            "constructionInProgress": rounded(ops, "construction_in_progress_million_cny"),
            "constructionAssetOriginal": rounded(ops, "construction_asset_original_million_cny"),
            "constructionAssetAccumulatedDepreciation": rounded(
                ops,
                "construction_asset_accumulated_depreciation_million_cny",
            ),
            "constructionAssetBookValue": rounded(ops, "construction_asset_book_value_million_cny"),
            "constructionAssetPeriodDepreciation": rounded(
                ops,
                "construction_asset_period_depreciation_million_cny",
            ),
            "rebuildActiveIds": as_text(ops, "rebuild_active_event_ids"),
            "rebuildStartedIds": as_text(ops, "rebuild_started_event_ids"),
            "rebuildStartedSlotIds": as_text(ops, "rebuild_started_slot_ids"),
            "rebuildCompletedIds": as_text(ops, "rebuild_completed_event_ids"),
            "rebuildAssetInServicePeriods": rounded(ops, "rebuild_asset_in_service_periods"),
            "rebuildDesignCapacityLoss": rounded(ops, "rebuild_design_capacity_loss_million"),
            "rebuildMaxCapacityLoss": rounded(ops, "rebuild_max_capacity_loss_million"),
            "rebuildCompletedDesignCapacityDelta": rounded(
                ops,
                "rebuild_completed_design_capacity_delta_million",
            ),
            "rebuildCompletedMaxCapacityDelta": rounded(
                ops,
                "rebuild_completed_max_capacity_delta_million",
            ),
            "rebuildCapex": rounded(ops, "rebuild_quarter_capex_outlay_million_cny"),
            "rebuildDemolitionExpense": rounded(finance, "period_rebuild_demolition_expense_million_cny"),
            "rebuildOldInitialAssetWriteoff": rounded(
                finance,
                "period_rebuild_old_initial_asset_writeoff_million_cny",
            ),
            "rebuildOldRenovationAssetWriteoff": rounded(
                finance,
                "period_rebuild_old_renovation_asset_writeoff_million_cny",
            ),
            "rebuildOldAssetWriteoff": rounded(finance, "period_rebuild_old_asset_writeoff_million_cny"),
            "rebuildConstructionInProgress": rounded(ops, "rebuild_construction_in_progress_million_cny"),
            "rebuildAssetOriginal": rounded(ops, "rebuild_asset_original_million_cny"),
            "rebuildAssetAccumulatedDepreciation": rounded(
                ops,
                "rebuild_asset_accumulated_depreciation_million_cny",
            ),
            "rebuildAssetBookValue": rounded(ops, "rebuild_asset_book_value_million_cny"),
            "rebuildAssetPeriodDepreciation": rounded(
                ops,
                "rebuild_asset_period_depreciation_million_cny",
            ),
            "activeProjectIds": non_empty_ids(
                as_text(ops, "renovation_active_event_ids"),
                as_text(ops, "construction_active_event_ids"),
                as_text(ops, "rebuild_active_event_ids"),
            ),
            "completedProjectIds": non_empty_ids(
                as_text(ops, "renovation_completed_event_ids"),
                as_text(ops, "construction_completed_event_ids"),
                as_text(ops, "rebuild_completed_event_ids"),
            ),
        },
        "warnings": quarter_warnings(ops, finance),
    }


def aggregate_beijing_operations(
    run_dir: Path,
    seed: int,
    years: int,
    cached: bool,
    mode: str = "replay",
    operations_relative_csv: Path = BEIJING_OPERATIONS_RELATIVE_CSV,
    financial_relative_csv: Path = BEIJING_FINANCIAL_RELATIVE_CSV,
) -> dict[str, Any]:
    operations_path = run_dir / operations_relative_csv
    financial_path = run_dir / financial_relative_csv
    if not operations_path.exists():
        raise FileNotFoundError(f"no Beijing quarterly operations output found in {operations_path}")
    if not financial_path.exists():
        raise FileNotFoundError(f"no Beijing financial state output found in {financial_path}")

    operation_rows = read_csv(operations_path)
    financial_rows = read_csv(financial_path)
    financial_by_quarter = {quarter_key(row): row for row in financial_rows}
    quarters: list[dict[str, Any]] = []
    for index, ops in enumerate(operation_rows):
        finance = financial_by_quarter.get(quarter_key(ops), {})
        quarters.append(summarize_beijing_quarter(index, ops, finance))

    player_start_index = next(
        (index for index, quarter in enumerate(quarters) if quarter["playerDecisionEnabled"]),
        0,
    )
    return {
        "seed": seed,
        "years": years,
        "cached": cached,
        "mode": mode,
        "modeLabel": OPERATION_MODE_DETAILS[mode]["label"],
        "modeDescription": OPERATION_MODE_DETAILS[mode]["description"],
        "runId": run_dir.name,
        "runDir": str(run_dir.relative_to(ROOT_DIR).as_posix()),
        "operationSource": operations_relative_csv.parent.as_posix(),
        "cityName": "北京",
        "periodCount": len(quarters),
        "playerStartIndex": player_start_index,
        "startLabel": quarters[0]["label"] if quarters else "",
        "finalLabel": quarters[-1]["label"] if quarters else "",
        "quarters": quarters,
    }


def load_beijing_operations(seed: int, years: int, force: bool, mode: str = "replay") -> dict[str, Any]:
    run_payload = run_seed(seed, years, force)
    run_dir = RUN_ROOT / str(run_payload["runId"])
    if mode == "simulate_default":
        simulation_cached = ensure_player_simulation_outputs(run_dir, [], force)
        return aggregate_beijing_operations(
            run_dir,
            seed,
            years,
            bool(run_payload.get("cached")) and simulation_cached,
            mode,
            SIMULATION_OPERATIONS_RELATIVE_CSV,
            SIMULATION_FINANCIAL_RELATIVE_CSV,
        )
    try:
        return aggregate_beijing_operations(run_dir, seed, years, bool(run_payload.get("cached")), mode)
    except FileNotFoundError:
        if force:
            raise
        run_payload = run_seed(seed, years, True)
        run_dir = RUN_ROOT / str(run_payload["runId"])
        return aggregate_beijing_operations(run_dir, seed, years, False, mode)


def player_contract_previews(
    quarters: list[dict[str, Any]],
    active_index: int,
) -> dict[str, dict[str, Any]]:
    """Expose only the next-term card when a contract has entered its talk window."""
    definitions = {
        "DUTY_FREE_MAIN": {
            "cycle": "dutyFreeContractCycle",
            "status": "dutyFreeContractStatus",
            "type": "dutyFreeContractType",
            "share": "dutyFreeRevenueSharePct",
            "coverage": "dutyFreeMinimumGuaranteeCoveragePct",
            "guarantee": "dutyFreeMinimumGuarantee",
            "forecastQuarterSales": "dutyFreeContractForecastQuarterSales",
            "forecastAnnualSales": "dutyFreeContractForecastAnnualSales",
            "historyYearsUsed": "dutyFreeContractHistoryYearsUsed",
            "trendMultiplier": "dutyFreeContractTrendMultiplier",
            "macroRiskDiscountMultiplier": "dutyFreeContractMacroRiskDiscountMultiplier",
            "bargainingPowerMultiplier": "dutyFreeContractBargainingPowerMultiplier",
        },
        "LUXURY_RETAIL_MAIN": {
            "cycle": "luxuryContractCycle",
            "status": "luxuryContractStatus",
            "type": "luxuryContractType",
            "share": "luxuryRevenueSharePct",
            "coverage": "luxuryMinimumGuaranteeCoveragePct",
            "guarantee": "luxuryMinimumGuarantee",
            "forecastQuarterSales": "luxuryContractForecastQuarterSales",
            "forecastAnnualSales": "luxuryContractForecastAnnualSales",
            "historyYearsUsed": "luxuryContractHistoryYearsUsed",
            "trendMultiplier": "luxuryContractTrendMultiplier",
            "macroRiskDiscountMultiplier": "luxuryContractMacroRiskDiscountMultiplier",
            "bargainingPowerMultiplier": "luxuryContractBargainingPowerMultiplier",
        },
    }
    if active_index < 0 or active_index >= len(quarters):
        return {}
    previews: dict[str, dict[str, Any]] = {}
    for contract_id, fields in definitions.items():
        current = quarters[active_index]
        current_ops = current.get("operations", {})
        cycle_id = str(current_ops.get(fields["cycle"]) or "")
        if not cycle_id:
            continue
        cycle_indices = [
            index
            for index, quarter in enumerate(quarters)
            if str(quarter.get("operations", {}).get(fields["cycle"]) or "") == cycle_id
        ]
        if not cycle_indices:
            continue
        cycle_end_index = max(cycle_indices)
        remaining = cycle_end_index - active_index + 1
        if remaining < 1 or remaining > 4:
            continue
        next_quarter = next(
            (
                quarter
                for quarter in quarters[cycle_end_index + 1 :]
                if str(quarter.get("operations", {}).get(fields["cycle"]) or "") not in {"", cycle_id}
            ),
            None,
        )
        if not next_quarter:
            continue
        ops = next_quarter.get("operations", {})
        previews[contract_id] = {
            "currentCycleEndIndex": cycle_end_index,
            "remainingQuarters": remaining,
            "nextTerm": {
                "cycleId": str(ops.get(fields["cycle"]) or ""),
                "status": str(ops.get(fields["status"]) or ""),
                "type": str(ops.get(fields["type"]) or ""),
                "sharePct": as_float(ops.get(fields["share"])),
                "coveragePct": as_float(ops.get(fields["coverage"])),
                "guarantee": as_float(ops.get(fields["guarantee"])),
                "forecastQuarterSales": as_float(ops.get(fields["forecastQuarterSales"])),
                "forecastAnnualSales": as_float(ops.get(fields["forecastAnnualSales"])),
                "historyYearsUsed": as_float(ops.get(fields["historyYearsUsed"])),
                "trendMultiplier": as_float(ops.get(fields["trendMultiplier"])),
                "macroRiskDiscountMultiplier": as_float(ops.get(fields["macroRiskDiscountMultiplier"])),
                "bargainingPowerMultiplier": as_float(ops.get(fields["bargainingPowerMultiplier"])),
                "cycleStartYear": as_float(
                    ops.get("dutyFreeContractCycleStartYear")
                    if contract_id == "DUTY_FREE_MAIN"
                    else ops.get("luxuryContractCycleStartYear")
                ),
                "cycleEndYear": as_float(
                    ops.get("dutyFreeContractCycleEndYear")
                    if contract_id == "DUTY_FREE_MAIN"
                    else ops.get("luxuryContractCycleEndYear")
                ),
            },
        }
    return previews


def load_player_simulation(
    seed: int,
    years: int,
    force: bool,
    player_actions: list[dict[str, Any]],
    current_quarter_index: int | None,
) -> dict[str, Any]:
    """Rebuild a player run and expose only the history through the active quarter."""
    run_payload = run_seed(seed, years, force)
    run_dir = RUN_ROOT / str(run_payload["runId"])
    clean_actions = clean_player_actions(player_actions)
    simulation_cached = ensure_player_simulation_outputs(run_dir, clean_actions, force)
    payload = aggregate_beijing_operations(
        run_dir,
        seed,
        years,
        bool(run_payload.get("cached")) and simulation_cached,
        "simulate_default",
        SIMULATION_OPERATIONS_RELATIVE_CSV,
        SIMULATION_FINANCIAL_RELATIVE_CSV,
    )
    all_quarters = payload.get("quarters", [])
    player_start_index = int(payload.get("playerStartIndex", 0))
    requested_index = player_start_index if current_quarter_index is None else int(current_quarter_index)
    active_index = min(max(player_start_index, requested_index), max(player_start_index, len(all_quarters) - 1))
    visible_quarters = all_quarters[: active_index + 1]
    payload.update(
        {
            "quarters": visible_quarters,
            "allQuarters": all_quarters,
            "periodCount": len(visible_quarters),
            "worldPeriodCount": len(all_quarters),
            "worldFinalLabel": all_quarters[-1]["label"] if all_quarters else "",
            "finalLabel": visible_quarters[-1]["label"] if visible_quarters else "",
            "currentQuarterIndex": active_index,
            "playerActions": clean_actions,
            "actionCount": len(clean_actions),
            "slotNames": player_slot_names(clean_actions),
            "projectCatalog": project_catalog(),
            "financingProducts": FINANCING_PRODUCTS,
            "financingPolicy": read_json(BEIJING_FINANCE_CONFIG).get("debt_policy", {}).get("loan_rate_model", {}),
            "contractPreviews": player_contract_previews(all_quarters, active_index),
            "operationSource": "simulation_default/server_action_journal",
        }
    )
    return payload


def json_response(handler: BaseHTTPRequestHandler, status: int, payload: dict[str, Any]) -> None:
    raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(raw)))
    handler.end_headers()
    handler.wfile.write(raw)


def file_response(handler: BaseHTTPRequestHandler, path: Path, content_type: str) -> None:
    raw = path.read_bytes()
    handler.send_response(200)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(raw)))
    handler.end_headers()
    handler.wfile.write(raw)


class SeedExplorerHandler(BaseHTTPRequestHandler):
    server_version = "SeedExplorer/0.1"

    def log_message(self, format: str, *args: Any) -> None:
        sys.stderr.write("%s - - [%s] %s\n" % (self.address_string(), self.log_date_time_string(), format % args))

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path in {"/", "/seed_explorer_viewer.html"}:
            file_response(self, VIEWER_HTML, "text/html; charset=utf-8")
            return
        if path == "/api/health":
            json_response(
                self,
                200,
                {
                    "ok": True,
                    "runRoot": str(RUN_ROOT.relative_to(ROOT_DIR).as_posix()),
                    "maxCachedRuns": MAX_CACHED_RUNS,
                },
            )
            return
        if path == "/api/cached-runs":
            json_response(
                self,
                200,
                {
                    "ok": True,
                    "runRoot": str(RUN_ROOT.relative_to(ROOT_DIR).as_posix()),
                    "maxCachedRuns": MAX_CACHED_RUNS,
                    "runs": list_cached_runs(),
                },
            )
            return
        if path == "/api/sim-save-slots":
            json_response(
                self,
                200,
                {
                    "ok": True,
                    "deprecated": True,
                    "message": "seed-bound single save is available through POST /api/sim-save",
                    "slots": [],
                },
            )
            return
        json_response(self, 404, {"ok": False, "error": "not found"})

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path not in {
            "/api/run",
            "/api/beijing-operations",
            "/api/player-simulation",
            "/api/sim-save",
            "/api/sim-save-slot",
        }:
            json_response(self, 404, {"ok": False, "error": "not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length).decode("utf-8") if length else "{}"
            body = json.loads(raw or "{}")
            if path in {"/api/sim-save", "/api/sim-save-slot"}:
                seed = clean_seed(body.get("seed"))
                years = clean_years(body.get("years", 60))
                action = str(body.get("action") or "load").strip().lower()
                if action == "save":
                    save_payload = save_sim_save(body)
                    payload = {
                        "save": save_payload,
                        "summary": sim_save_summary(seed, years, save_payload),
                    }
                elif action == "load":
                    save_payload = read_sim_save(seed, years)
                    if not save_payload:
                        raise FileNotFoundError("当前 seed 没有动态测试存档")
                    payload = {
                        "save": save_payload,
                        "summary": sim_save_summary(seed, years, save_payload),
                    }
                elif action == "status":
                    save_payload = read_sim_save(seed, years)
                    payload = {
                        "save": save_payload,
                        "summary": sim_save_summary(seed, years, save_payload),
                    }
                elif action == "clear":
                    clear_sim_save(seed, years)
                    payload = {
                        "summary": sim_save_summary(seed, years),
                    }
                else:
                    raise ValueError(f"unsupported save action: {action}")
                json_response(self, 200, {"ok": True, **payload})
                return
            seed = clean_seed(body.get("seed"))
            years = clean_years(body.get("years", 60))
            force = bool(body.get("force", False))
            if path == "/api/player-simulation":
                current_value = body.get("currentQuarterIndex")
                current_index = None if current_value in (None, "") else int(as_float(current_value, 0.0))
                payload = load_player_simulation(
                    seed,
                    years,
                    force,
                    clean_player_actions(body.get("playerActions", [])),
                    current_index,
                )
            elif path == "/api/beijing-operations":
                mode = clean_operation_mode(body.get("mode", "replay"))
                payload = load_beijing_operations(seed, years, force, mode)
            else:
                payload = run_seed(seed, years, force)
            json_response(self, 200, {"ok": True, **payload})
        except Exception as exc:
            json_response(self, 500, {"ok": False, "error": str(exc)})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Local full-chain city market seed explorer.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8776)
    parser.add_argument("--open", action="store_true", help="Open the explorer in the default browser.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not ORCHESTRATOR.exists():
        raise FileNotFoundError(f"missing orchestrator: {ORCHESTRATOR}")
    if not VIEWER_HTML.exists():
        raise FileNotFoundError(f"missing viewer: {VIEWER_HTML}")
    server = ThreadingHTTPServer((args.host, args.port), SeedExplorerHandler)
    url = f"http://{args.host}:{args.port}/"
    print(f"Seed Explorer listening on {url}")
    print("Press Ctrl+C to stop.")
    if args.open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Seed Explorer.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
