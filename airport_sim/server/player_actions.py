from __future__ import annotations

from typing import Any, Callable

from . import player_contracts, player_financing, player_projects


def normalize_rename_action(
    raw: dict[str, Any],
    *,
    renamable_slot_ids: set[str],
    as_float: Callable[[Any, float], float],
) -> dict[str, Any] | None:
    slot_id = str(raw.get("slotId") or raw.get("slot_id") or "").strip()
    name = " ".join(str(raw.get("name") or "").strip().split())
    if slot_id not in renamable_slot_ids or not 2 <= len(name) <= 24:
        return None
    return {
        "id": str(raw.get("id") or f"rename:{slot_id}"),
        "type": "rename_slot",
        "slotId": slot_id,
        "name": name,
        "renamedAtIndex": int(as_float(raw.get("renamedAtIndex"), 0.0)),
        "renamedAtLabel": str(raw.get("renamedAtLabel") or ""),
    }


def apply_rename_action(
    actions: list[dict[str, Any]],
    seen_slot_renames: set[str],
    action: dict[str, Any],
) -> None:
    slot_id = str(action["slotId"])
    if slot_id in seen_slot_renames:
        actions[:] = [
            existing
            for existing in actions
            if not (
                existing.get("type") == "rename_slot"
                and existing.get("slotId") == slot_id
            )
        ]
    seen_slot_renames.add(slot_id)
    actions.append(action)


def clean_player_actions(
    value: Any,
    *,
    as_float: Callable[[Any, float], float],
    minimum_action_index: int,
    project_templates: dict[str, dict[str, Any]],
    financing_products: dict[str, dict[str, Any]],
    renamable_slot_ids: set[str],
    initial_terminal_numbers_by_airport: dict[str, set[int]],
    initial_terminal_number_by_slot: dict[str, int],
    initial_slot_sizes: dict[str, str],
    terminal_name_prefix_by_airport: dict[str, str],
    renovation_cooldown_quarters: int,
    rebuild_cooldown_quarters: int,
    demolition_clearance_quarters: int,
    allowed_rebuild_target_sizes: Callable[[dict[str, Any]], list[str]],
    allowed_construction_target_sizes: Callable[[dict[str, Any]], list[str]],
    construction_event_config: Callable[[str], dict[str, Any]],
    rebuild_event_config: Callable[[str, str], dict[str, Any]],
    demolition_event_config: Callable[[str], dict[str, Any]],
    renovation_event_config: Callable[[str], dict[str, Any]],
) -> list[dict[str, Any]]:
    """Persist only the ordered action journal understood by the simulation."""
    if not isinstance(value, list):
        return []
    actions: list[dict[str, Any]] = []
    seen_contracts: set[tuple[str, str, str]] = set()
    seen_financing_quarters: set[int] = set()
    seen_slot_renames: set[str] = set()
    project_state = player_projects.new_project_action_state(
        project_templates=project_templates,
        initial_terminal_numbers_by_airport=initial_terminal_numbers_by_airport,
        initial_terminal_number_by_slot=initial_terminal_number_by_slot,
        initial_slot_sizes=initial_slot_sizes,
    )
    for raw in value:
        if not isinstance(raw, dict):
            continue
        action_type = str(raw.get("type") or "")
        if action_type == "rename_slot":
            action = normalize_rename_action(
                raw,
                renamable_slot_ids=renamable_slot_ids,
                as_float=as_float,
            )
            if action is not None:
                apply_rename_action(actions, seen_slot_renames, action)
            continue
        if action_type == "start_project":
            action = player_projects.normalize_project_action(
                raw,
                state=project_state,
                project_templates=project_templates,
                minimum_action_index=minimum_action_index,
                renovation_cooldown_quarters=renovation_cooldown_quarters,
                rebuild_cooldown_quarters=rebuild_cooldown_quarters,
                demolition_clearance_quarters=demolition_clearance_quarters,
                terminal_name_prefix_by_airport=terminal_name_prefix_by_airport,
                as_float=as_float,
                allowed_rebuild_target_sizes=allowed_rebuild_target_sizes,
                allowed_construction_target_sizes=allowed_construction_target_sizes,
                construction_event_config=construction_event_config,
                rebuild_event_config=rebuild_event_config,
                demolition_event_config=demolition_event_config,
                renovation_event_config=renovation_event_config,
            )
            if action is not None:
                actions.append(action)
            continue
        if action_type == "draw_loan":
            action = player_financing.normalize_financing_action(
                raw,
                seen_quarters=seen_financing_quarters,
                financing_products=financing_products,
                minimum_action_index=minimum_action_index,
                as_float=as_float,
            )
            if action is not None:
                actions.append(action)
            continue
        if action_type != "sign_contract":
            continue
        action = player_contracts.normalize_contract_action(raw, as_float=as_float)
        if action is not None:
            player_contracts.apply_contract_action(actions, seen_contracts, action)
    return actions


def relative_index_to_year_quarter(
    index: int,
    *,
    simulation_start_year: int,
) -> tuple[int, str]:
    safe_index = max(0, int(index))
    return simulation_start_year + safe_index // 4, f"Q{safe_index % 4 + 1}"


def player_slot_names(
    actions: list[dict[str, Any]],
    *,
    renamable_slot_ids: set[str],
) -> dict[str, str]:
    return {
        str(action["slotId"]): str(action["name"])
        for action in actions
        if action.get("type") == "rename_slot"
        and action.get("slotId") in renamable_slot_ids
    }
