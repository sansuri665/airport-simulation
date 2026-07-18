from __future__ import annotations

from typing import Any, Callable


ALLOWED_CONTRACT_IDS = {"DUTY_FREE_MAIN", "LUXURY_RETAIL_MAIN"}


def normalize_contract_action(
    raw: dict[str, Any],
    *,
    as_float: Callable[[Any, float], float],
) -> dict[str, Any] | None:
    contract_id = str(raw.get("contractId") or raw.get("contract_id") or "").strip()
    cycle_id = str(raw.get("cycleId") or raw.get("cycle_id") or "").strip()
    terms = raw.get("terms", {})
    if contract_id not in ALLOWED_CONTRACT_IDS or not cycle_id or not isinstance(terms, dict):
        return None
    return {
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


def apply_contract_action(
    actions: list[dict[str, Any]],
    seen_contracts: set[tuple[str, str, str]],
    action: dict[str, Any],
) -> None:
    key = ("sign_contract", str(action["contractId"]), str(action["cycleId"]))
    if key in seen_contracts:
        actions[:] = [
            existing
            for existing in actions
            if (
                existing.get("type"),
                existing.get("contractId"),
                existing.get("cycleId"),
            )
            != key
        ]
    seen_contracts.add(key)
    actions.append(action)
