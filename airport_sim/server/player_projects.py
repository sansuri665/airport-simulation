from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


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


@dataclass
class ProjectActionState:
    seen_renovation_instances: set[tuple[str, int]]
    seen_rebuild_instances: set[tuple[str, int]]
    seen_construction_instances: set[tuple[str, int]]
    seen_demolition_instances: set[tuple[str, int]]
    terminal_numbers_by_airport: dict[str, set[int]]
    terminal_number_by_slot: dict[str, int]
    renovation_completion_by_slot: dict[str, list[int]]
    rebuild_completion_by_slot: dict[str, list[int]]
    demolition_completion_by_slot: dict[str, list[int]]
    project_completion_by_slot: dict[str, list[int]]
    slot_size_by_id: dict[str, str]


def new_project_action_state(
    *,
    project_templates: dict[str, dict[str, Any]],
    initial_terminal_numbers_by_airport: dict[str, set[int]],
    initial_terminal_number_by_slot: dict[str, int],
    initial_slot_sizes: dict[str, str],
) -> ProjectActionState:
    slot_size_by_id = {
        str(template["slotId"]): "empty"
        for template in project_templates.values()
    }
    slot_size_by_id.update(initial_slot_sizes)
    return ProjectActionState(
        seen_renovation_instances=set(),
        seen_rebuild_instances=set(),
        seen_construction_instances=set(),
        seen_demolition_instances=set(),
        terminal_numbers_by_airport={
            airport_id: set(numbers)
            for airport_id, numbers in initial_terminal_numbers_by_airport.items()
        },
        terminal_number_by_slot=dict(initial_terminal_number_by_slot),
        renovation_completion_by_slot={},
        rebuild_completion_by_slot={},
        demolition_completion_by_slot={},
        project_completion_by_slot={},
        slot_size_by_id=slot_size_by_id,
    )


def allowed_target_sizes(
    template: dict[str, Any],
    facility_catalog: dict[str, Any],
) -> list[str]:
    allowed = facility_catalog.get("slot_role_allowed_sizes", {}).get(
        str(template.get("slotRole") or ""),
        [],
    )
    return [str(size) for size in allowed if str(size) != "empty"]


def construction_event_config(
    target_size: str,
    *,
    operations_config: dict[str, Any],
    as_float: Callable[[Any, float], float],
) -> dict[str, Any]:
    construction_model = operations_config.get("facility_construction_model", {})
    capex = as_float(
        construction_model.get("construction_cost_million_cny_by_facility_size", {}).get(target_size),
        0.0,
    )
    capex *= as_float(construction_model.get("city_construction_cost_multiplier"), 1.0)
    depreciation = construction_model.get(
        "new_asset_depreciation",
        construction_model.get("construction_asset_depreciation", {}),
    )
    return {
        "target_facility_size": target_size,
        "duration_quarters": max(
            1,
            int(
                as_float(
                    construction_model.get("duration_quarters_by_facility_size", {}).get(target_size),
                    12.0,
                )
            ),
        ),
        "capex_million_cny": round(capex, 4),
        "useful_life_years": round(as_float(depreciation.get("useful_life_years"), 40.0), 4),
        "residual_value_pct": round(as_float(depreciation.get("residual_value_pct"), 10.0), 4),
    }


def rebuild_event_config(
    source_size: str,
    target_size: str,
    *,
    operations_config: dict[str, Any],
    as_float: Callable[[Any, float], float],
) -> dict[str, Any]:
    rebuild_model = operations_config.get("facility_rebuild_model", {})
    construction_model = operations_config.get("facility_construction_model", {})
    capex = as_float(
        construction_model.get("construction_cost_million_cny_by_facility_size", {}).get(target_size),
        0.0,
    )
    capex *= as_float(construction_model.get("city_construction_cost_multiplier"), 1.0)
    demolition = as_float(
        rebuild_model.get("asset_cost_million_cny_by_facility_size", {}).get(source_size),
        0.0,
    )
    demolition *= as_float(
        rebuild_model.get("demolition_cost_ratio_by_source_facility_size", {}).get(source_size),
        0.10,
    )
    demolition *= as_float(rebuild_model.get("city_demolition_cost_multiplier"), 1.0)
    depreciation = rebuild_model.get(
        "new_asset_depreciation",
        construction_model.get("new_asset_depreciation", {}),
    )
    demolition_duration = max(
        1,
        int(
            as_float(
                rebuild_model.get("demolition_duration_quarters_by_source_facility_size", {}).get(source_size),
                1.0,
            )
        ),
    )
    construction_duration = max(
        1,
        int(
            as_float(
                construction_model.get("duration_quarters_by_facility_size", {}).get(target_size),
                12.0,
            )
        ),
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


def demolition_event_config(
    source_size: str,
    *,
    operations_config: dict[str, Any],
    as_float: Callable[[Any, float], float],
) -> dict[str, Any]:
    rebuild_model = operations_config.get("facility_rebuild_model", {})
    demolition = as_float(
        rebuild_model.get("asset_cost_million_cny_by_facility_size", {}).get(source_size),
        0.0,
    )
    demolition *= as_float(
        rebuild_model.get("demolition_cost_ratio_by_source_facility_size", {}).get(source_size),
        0.10,
    )
    demolition *= as_float(rebuild_model.get("city_demolition_cost_multiplier"), 1.0)
    return {
        "source_facility_size": source_size,
        "target_facility_size": "empty",
        "duration_quarters": max(
            1,
            int(
                as_float(
                    rebuild_model.get("demolition_duration_quarters_by_source_facility_size", {}).get(source_size),
                    1.0,
                )
            ),
        ),
        "asset_capex_million_cny": 0.0,
        "demolition_expense_million_cny": round(demolition, 4),
    }


def renovation_event_config(
    facility_size: str,
    *,
    operations_config: dict[str, Any],
    as_float: Callable[[Any, float], float],
) -> dict[str, Any]:
    renovation_model = operations_config.get("facility_renovation_model", {})
    replacement_cost = as_float(
        renovation_model.get("replacement_cost_million_cny_by_facility_size", {}).get(facility_size),
        0.0,
    )
    capex_ratio = as_float(
        renovation_model.get("capex_ratio_by_facility_size", {}).get(facility_size),
        0.0,
    )
    capex = replacement_cost * capex_ratio * as_float(
        renovation_model.get("city_construction_cost_multiplier"),
        1.0,
    )
    depreciation = renovation_model.get("renovation_asset_depreciation", {})
    return {
        "facility_size": facility_size,
        "duration_quarters": max(
            1,
            int(
                as_float(
                    renovation_model.get("duration_quarters_by_facility_size", {}).get(facility_size),
                    6.0,
                )
            ),
        ),
        "construction_capacity_multiplier": round(
            as_float(renovation_model.get("default_construction_capacity_multiplier"), 0.75),
            4,
        ),
        "capex_million_cny": round(capex, 4),
        "useful_life_years": round(as_float(depreciation.get("useful_life_years"), 20.0), 4),
        "residual_value_pct": round(as_float(depreciation.get("residual_value_pct"), 5.0), 4),
    }


def normalize_project_action(
    raw: dict[str, Any],
    *,
    state: ProjectActionState,
    project_templates: dict[str, dict[str, Any]],
    minimum_action_index: int,
    renovation_cooldown_quarters: int,
    rebuild_cooldown_quarters: int,
    demolition_clearance_quarters: int,
    terminal_name_prefix_by_airport: dict[str, str],
    as_float: Callable[[Any, float], float],
    allowed_rebuild_target_sizes: Callable[[dict[str, Any]], list[str]],
    allowed_construction_target_sizes: Callable[[dict[str, Any]], list[str]],
    construction_event_config: Callable[[str], dict[str, Any]],
    rebuild_event_config: Callable[[str, str], dict[str, Any]],
    demolition_event_config: Callable[[str], dict[str, Any]],
    renovation_event_config: Callable[[str], dict[str, Any]],
) -> dict[str, Any] | None:
    template_id = str(raw.get("templateId") or raw.get("template_id") or "").strip()
    template = project_templates.get(template_id)
    started_at_index = int(as_float(raw.get("startedAtIndex"), -1.0))
    if not template or started_at_index < minimum_action_index:
        return None
    project_type = str(template["projectType"])
    event_config: dict[str, Any] = {}
    project_id = str(template["projectId"])
    slot_id = str(template["slotId"])
    latest_project_completion = max(
        state.project_completion_by_slot.get(slot_id, []),
        default=-10**9,
    )
    if started_at_index < latest_project_completion:
        return None
    if project_type == "renovation":
        event_config = renovation_event_config(
            state.slot_size_by_id.get(slot_id, str(template["facilitySize"]))
        )
        instance_key = (slot_id, started_at_index)
        duration = max(1, int(event_config["duration_quarters"]))
        prior_completions = state.renovation_completion_by_slot.setdefault(slot_id, [])
        latest_completion = max(prior_completions, default=-10**9)
        latest_rebuild_completion = max(
            state.rebuild_completion_by_slot.get(slot_id, []),
            default=-10**9,
        )
        if instance_key in state.seen_renovation_instances:
            return None
        if started_at_index < max(latest_completion, latest_rebuild_completion) + renovation_cooldown_quarters:
            return None
        state.seen_renovation_instances.add(instance_key)
        completion_index = started_at_index + duration
        prior_completions.append(completion_index)
        state.project_completion_by_slot.setdefault(slot_id, []).append(completion_index)
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
        if target_size not in allowed_rebuild_target_sizes(template) or instance_key in state.seen_rebuild_instances:
            return None
        prior_completions = state.rebuild_completion_by_slot.setdefault(slot_id, [])
        latest_completion = max(prior_completions, default=-10**9)
        if started_at_index < latest_completion + rebuild_cooldown_quarters:
            return None
        source_size = state.slot_size_by_id.get(slot_id, str(template["sourceFacilitySize"]))
        event_config = rebuild_event_config(source_size, target_size)
        duration = max(1, int(event_config["duration_quarters"]))
        completion_index = started_at_index + duration
        state.seen_rebuild_instances.add(instance_key)
        prior_completions.append(completion_index)
        state.project_completion_by_slot.setdefault(slot_id, []).append(completion_index)
        state.slot_size_by_id[slot_id] = target_size
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
        latest_demolition_completion = max(
            state.demolition_completion_by_slot.get(slot_id, []),
            default=-10**9,
        )
        if (
            state.slot_size_by_id.get(slot_id, "empty") != "empty"
            or target_size not in allowed_construction_target_sizes(template)
            or instance_key in state.seen_construction_instances
            or started_at_index < latest_demolition_completion + demolition_clearance_quarters
        ):
            return None
        event_config = construction_event_config(target_size)
        airport_id = str(template["airportId"])
        assigned_numbers = state.terminal_numbers_by_airport.setdefault(airport_id, set())
        terminal_number = state.terminal_number_by_slot.get(
            slot_id,
            max(assigned_numbers, default=0) + 1,
        )
        assigned_numbers.add(terminal_number)
        state.terminal_number_by_slot[slot_id] = terminal_number
        event_config["terminal_number"] = terminal_number
        event_config["terminal_name"] = (
            f"{terminal_name_prefix_by_airport.get(airport_id, airport_id)}T{terminal_number}航站楼"
        )
        duration = max(1, int(event_config["duration_quarters"]))
        state.seen_construction_instances.add(instance_key)
        state.project_completion_by_slot.setdefault(slot_id, []).append(started_at_index + duration)
        state.slot_size_by_id[slot_id] = target_size
        project_id = f"{template['projectId']}__{started_at_index}"
    elif project_type == "demolition":
        instance_key = (slot_id, started_at_index)
        source_size = state.slot_size_by_id.get(slot_id, "empty")
        if source_size == "empty" or instance_key in state.seen_demolition_instances:
            return None
        event_config = demolition_event_config(source_size)
        duration = max(1, int(event_config["duration_quarters"]))
        completion_index = started_at_index + duration
        state.seen_demolition_instances.add(instance_key)
        state.demolition_completion_by_slot.setdefault(slot_id, []).append(completion_index)
        state.project_completion_by_slot.setdefault(slot_id, []).append(completion_index)
        state.slot_size_by_id[slot_id] = "empty"
        project_id = f"{template['projectId']}__{started_at_index}"
    else:
        return None
    return {
        "id": str(raw.get("id") or f"{template_id}:{started_at_index}"),
        "type": "start_project",
        "templateId": template_id,
        "projectId": project_id,
        "startedAtIndex": started_at_index,
        "startedAtLabel": str(raw.get("startedAtLabel") or ""),
        "eventConfig": event_config,
    }


def player_project_events(
    actions: list[dict[str, Any]],
    *,
    project_templates: dict[str, dict[str, Any]],
    relative_index_to_year_quarter: Callable[[int], tuple[int, str]],
) -> dict[str, list[dict[str, Any]]]:
    events: dict[str, list[dict[str, Any]]] = {
        "facility_renovation_events": [],
        "facility_construction_events": [],
        "facility_rebuild_events": [],
    }
    for action in actions:
        if action.get("type") != "start_project":
            continue
        template = project_templates.get(str(action.get("templateId") or ""))
        if not template:
            continue
        start_year, start_quarter = relative_index_to_year_quarter(
            int(action.get("startedAtIndex", 0))
        )
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
        event_config = action.get("eventConfig", {})
        if not isinstance(event_config, dict):
            event_config = {}
        if template["projectType"] == "renovation":
            events["facility_renovation_events"].append(
                {
                    **base_event,
                    "facility_size": str(
                        event_config.get("facility_size") or template["facilitySize"]
                    ),
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
            events["facility_construction_events"].append(
                {
                    **base_event,
                    "target_facility_size": str(
                        event_config.get("target_facility_size") or ""
                    ),
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
            events["facility_rebuild_events"].append(
                {
                    **base_event,
                    "from_facility_size": str(
                        event_config.get("source_facility_size")
                        or template["sourceFacilitySize"]
                    ),
                    "target_facility_size": str(
                        event_config.get("target_facility_size")
                        or template.get("targetFacilitySize")
                        or "empty"
                    ),
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


def project_catalog(
    *,
    root_dir: Path,
    operations_config_path: Path,
    read_config_json: Callable[[Path], dict[str, Any]],
    project_templates: dict[str, dict[str, Any]],
    demolition_clearance_quarters: int,
    as_float: Callable[[Any, float], float],
    allowed_rebuild_target_sizes: Callable[[dict[str, Any]], list[str]],
    allowed_construction_target_sizes: Callable[[dict[str, Any]], list[str]],
    construction_event_config: Callable[[str], dict[str, Any]],
    rebuild_event_config: Callable[[str, str], dict[str, Any]],
    demolition_event_config: Callable[[str], dict[str, Any]],
    renovation_event_config: Callable[[str], dict[str, Any]],
) -> list[dict[str, Any]]:
    operations_config = read_config_json(operations_config_path)
    catalog_path = root_dir / "config" / "facility_size_catalogs" / "standard_terminal_sizes_v1.json"
    facility_sizes = (
        read_config_json(catalog_path).get("facility_sizes", {})
        if catalog_path.exists()
        else {}
    )
    renovation_model = operations_config.get("facility_renovation_model", {})
    construction_model = operations_config.get("facility_construction_model", {})
    rebuild_model = operations_config.get("facility_rebuild_model", {})
    catalog: list[dict[str, Any]] = []
    for template in project_templates.values():
        project_type = str(template["projectType"])
        if project_type == "renovation":
            size = str(template["facilitySize"])
            replacement_cost = as_float(
                renovation_model.get("replacement_cost_million_cny_by_facility_size", {}).get(size),
                0.0,
            )
            ratio = as_float(
                renovation_model.get("capex_ratio_by_facility_size", {}).get(size),
                0.0,
            )
            cost_multiplier = as_float(
                renovation_model.get("city_construction_cost_multiplier"),
                1.0,
            )
            capex = replacement_cost * ratio * cost_multiplier
            duration = int(
                as_float(
                    renovation_model.get("duration_quarters_by_facility_size", {}).get(size),
                    6.0,
                )
            )
            capacity_multiplier = as_float(
                renovation_model.get("default_construction_capacity_multiplier"),
                0.75,
            )
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
            capex = as_float(
                rebuild_model.get("asset_cost_million_cny_by_facility_size", {}).get(target_size),
                0.0,
            )
            capex *= as_float(rebuild_model.get("city_construction_cost_multiplier"), 1.0)
            duration = int(
                as_float(
                    rebuild_model.get("duration_quarters_by_facility_size", {}).get(target_size),
                    18.0,
                )
            )
            capacity_multiplier = as_float(
                rebuild_model.get("default_construction_capacity_multiplier"),
                0.0,
            )
            demolition = as_float(
                rebuild_model.get("asset_cost_million_cny_by_facility_size", {}).get(source_size),
                0.0,
            )
            demolition *= as_float(
                rebuild_model.get("demolition_cost_ratio_by_source_facility_size", {}).get(source_size),
                0.0,
            )
            demolition *= as_float(
                rebuild_model.get("city_demolition_cost_multiplier"),
                1.0,
            )
        target_spec = facility_sizes.get(target_size, {})
        source_spec = facility_sizes.get(
            str(template.get("facilitySize") or template.get("sourceFacilitySize") or target_size),
            {},
        )
        renovation_details: dict[str, Any] = {}
        rebuild_details: dict[str, Any] = {}
        demolition_details: dict[str, Any] = {}
        construction_details: dict[str, Any] = {}
        if project_type == "renovation":
            depreciation = renovation_model.get("renovation_asset_depreciation", {})
            quality_model = operations_config.get("commercial", {}).get(
                "perceived_quality_model",
                {},
            )
            renovation_details = {
                "replacementCost": round(replacement_cost, 4),
                "capexRatio": round(ratio, 4),
                "constructionCostMultiplier": round(cost_multiplier, 4),
                "usefulLifeYears": round(
                    as_float(depreciation.get("useful_life_years"), 20.0),
                    4,
                ),
                "residualValuePct": round(
                    as_float(depreciation.get("residual_value_pct"), 5.0),
                    4,
                ),
                "maintenanceAgeRetentionRatio": round(
                    as_float(renovation_model.get("maintenance_age_retention_ratio"), 0.55),
                    4,
                ),
                "minimumEffectiveMaintenanceAgeYears": round(
                    as_float(
                        renovation_model.get("minimum_effective_maintenance_age_years"),
                        5.0,
                    ),
                    4,
                ),
                "constructionQualityDisruptionScore": round(
                    as_float(
                        quality_model.get("renovation_construction_disruption_score"),
                        0.0,
                    ),
                    4,
                ),
                "designCapacityLoss": round(
                    as_float(source_spec.get("design_capacity_million"), 0.0)
                    * (1.0 - capacity_multiplier),
                    4,
                ),
                "maxCapacityLoss": round(
                    as_float(source_spec.get("max_capacity_million"), 0.0)
                    * (1.0 - capacity_multiplier),
                    4,
                ),
                "renovationOptions": {
                    option_size: {
                        "durationQuarters": renovation_event_config(option_size)["duration_quarters"],
                        "totalCapex": renovation_event_config(option_size)["capex_million_cny"],
                        "designCapacityLoss": round(
                            as_float(
                                facility_sizes.get(option_size, {}).get("design_capacity_million"),
                                0.0,
                            )
                            * (
                                1.0
                                - renovation_event_config(option_size)[
                                    "construction_capacity_multiplier"
                                ]
                            ),
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
                        "targetDesignCapacity": round(
                            as_float(facility_sizes.get(size, {}).get("design_capacity_million"), 0.0),
                            4,
                        ),
                        "targetMaxCapacity": round(
                            as_float(facility_sizes.get(size, {}).get("max_capacity_million"), 0.0),
                            4,
                        ),
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
                            "targetDesignCapacity": round(
                                as_float(
                                    facility_sizes.get(target_option, {}).get("design_capacity_million"),
                                    0.0,
                                ),
                                4,
                            ),
                            "targetMaxCapacity": round(
                                as_float(
                                    facility_sizes.get(target_option, {}).get("max_capacity_million"),
                                    0.0,
                                ),
                                4,
                            ),
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
                "clearanceQuarters": demolition_clearance_quarters,
            }
        elif project_type == "construction":
            construction_details = {
                "constructionAllowedTargetSizes": allowed_construction_target_sizes(template),
                "constructionTargetOptions": {
                    size: {
                        "durationQuarters": construction_event_config(size)["duration_quarters"],
                        "totalCapex": construction_event_config(size)["capex_million_cny"],
                        "targetDesignCapacity": round(
                            as_float(facility_sizes.get(size, {}).get("design_capacity_million"), 0.0),
                            4,
                        ),
                        "targetMaxCapacity": round(
                            as_float(facility_sizes.get(size, {}).get("max_capacity_million"), 0.0),
                            4,
                        ),
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
                "targetDesignCapacity": round(
                    as_float(target_spec.get("design_capacity_million"), 0.0),
                    4,
                ),
                "targetMaxCapacity": round(
                    as_float(target_spec.get("max_capacity_million"), 0.0),
                    4,
                ),
                **renovation_details,
                **rebuild_details,
                **demolition_details,
                **construction_details,
            }
        )
    return catalog
