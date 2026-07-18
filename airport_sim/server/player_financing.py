from __future__ import annotations

from typing import Any, Callable


FINANCING_PRODUCTS = {
    "short_turnover": {
        "label": "短期周转贷款",
        "loan_type": "short_term",
        "repayment_style": "bullet_principal",
        "tenors": [4, 8, 12],
        "grace": [0],
        "tenor_spread_bps": {4: 0, 8: 15, 12: 30},
    },
    "long_construction": {
        "label": "长期建设贷款",
        "loan_type": "long_term",
        "repayment_style": "equal_principal",
        "tenors": [40, 60, 80],
        "grace": [0],
        "tenor_spread_bps": {40: 0, 60: 20, 80: 45},
    },
    "grace_construction": {
        "label": "宽限期建设贷款",
        "loan_type": "long_term",
        "repayment_style": "grace_then_equal_principal",
        "tenors": [60, 80],
        "grace": [8, 16],
        "tenor_spread_bps": {60: 20, 80: 45},
        "grace_spread_bps": {8: 10, 16: 25},
    },
}


def normalize_financing_action(
    raw: dict[str, Any],
    *,
    seen_quarters: set[int],
    financing_products: dict[str, dict[str, Any]],
    minimum_action_index: int,
    as_float: Callable[[Any, float], float],
) -> dict[str, Any] | None:
    started_at_index = int(as_float(raw.get("startedAtIndex"), -1.0))
    product_id = str(raw.get("productId") or "").strip()
    product = financing_products.get(product_id)
    principal = round(as_float(raw.get("principalMillionCny"), 0.0), 4)
    tenor = int(as_float(raw.get("tenorQuarters"), 0.0))
    grace = int(as_float(raw.get("gracePeriodQuarters"), 0.0))
    if (
        not product
        or started_at_index < minimum_action_index
        or started_at_index in seen_quarters
        or principal < 1000.0
        or principal > 100000.0
        or tenor not in product["tenors"]
        or grace not in product["grace"]
    ):
        return None
    seen_quarters.add(started_at_index)
    return {
        "id": str(raw.get("id") or f"loan:{product_id}:{started_at_index}"),
        "type": "draw_loan",
        "productId": product_id,
        "principalMillionCny": principal,
        "tenorQuarters": tenor,
        "gracePeriodQuarters": grace,
        "termSpreadBps": int(product.get("tenor_spread_bps", {}).get(tenor, 0))
        + int(product.get("grace_spread_bps", {}).get(grace, 0)),
        "startedAtIndex": started_at_index,
        "startedAtLabel": str(raw.get("startedAtLabel") or ""),
    }


def player_general_loans(
    actions: list[dict[str, Any]],
    *,
    financing_products: dict[str, dict[str, Any]],
    relative_index_to_year_quarter: Callable[[int], tuple[int, str]],
) -> list[dict[str, Any]]:
    loans: list[dict[str, Any]] = []
    for action in actions:
        if action.get("type") != "draw_loan":
            continue
        product = financing_products.get(str(action.get("productId") or ""))
        if not product:
            continue
        year, quarter = relative_index_to_year_quarter(int(action["startedAtIndex"]))
        loans.append(
            {
                "loan_id": str(action["id"]),
                "loan_name": str(product["label"]),
                "loan_type": product["loan_type"],
                "start_year": year,
                "start_quarter": quarter,
                "principal_million_cny": action["principalMillionCny"],
                "tenor_quarters": action["tenorQuarters"],
                "repayment_style": product["repayment_style"],
                "grace_period_quarters": action["gracePeriodQuarters"],
                "term_spread_bps": action.get("termSpreadBps", 0),
                "purpose_note": "玩家融资事务",
            }
        )
    return loans
