from __future__ import annotations

import math
from dataclasses import dataclass
from importlib import import_module
from typing import Any, Mapping


_SIBLING_PREFIX = f"{__package__}." if __package__ else ""
accounting = import_module(f"{_SIBLING_PREFIX}asset_accounting_v04")

ASSET_ACCOUNTING_CONTRACT_VERSION = accounting.ASSET_ACCOUNTING_CONTRACT_VERSION
GLOBAL_BOND_V04_PARAM_VERSION = "global-bond-accounting-v0.4"
GLOBAL_BOND_V04_INTERFACE_VERSION = ASSET_ACCOUNTING_CONTRACT_VERSION

DEFAULT_PROBABILITY_CONTRIBUTION_FIELDS = (
    "global_corporate_bond_default_probability_base_pct",
    "global_corporate_bond_default_risk_contribution_pct",
    "global_corporate_bond_credit_impairment_contribution_pct",
    "global_corporate_bond_crisis_contribution_pct",
)

IDENTITY_RESIDUAL_FIELDS = (
    "global_sovereign_bond_total_return_identity_residual",
    "global_corporate_bond_total_return_identity_residual",
    "global_60_40_total_return_identity_residual",
)

GLOBAL_BOND_V04_FIELDS = (
    "global_bond_v04_param_version",
    "asset_accounting_contract_version",
    "global_sovereign_bond_duration_years",
    "global_sovereign_bond_convexity",
    "global_corporate_bond_risk_free_duration_years",
    "global_corporate_bond_risk_free_convexity",
    "global_corporate_bond_spread_duration_years",
    "global_corporate_bond_loss_given_default_fraction",
    "global_corporate_bond_default_probability_floor_pct",
    "global_corporate_bond_default_probability_cap_pct",
    "global_sovereign_bond_price_return_pct",
    "global_sovereign_bond_carry_pct",
    "global_sovereign_bond_total_return_pct",
    "global_sovereign_bond_total_return_index",
    "global_corporate_bond_risk_free_price_return_pct",
    "global_corporate_bond_ig_spread_price_return_pct",
    "global_corporate_bond_price_return_pct",
    "global_corporate_bond_carry_pct",
    *DEFAULT_PROBABILITY_CONTRIBUTION_FIELDS,
    "global_corporate_bond_default_probability_proxy_raw_pct",
    "global_corporate_bond_default_probability_proxy_pct",
    "global_corporate_bond_default_probability_boundary_adjustment_pct",
    "global_corporate_bond_default_probability_boundary_state",
    "global_corporate_bond_credit_loss_pct",
    "global_corporate_bond_total_return_pct",
    "global_corporate_bond_total_return_index",
    "global_60_40_total_return_pct",
    "global_60_40_total_return_index",
    *IDENTITY_RESIDUAL_FIELDS,
)



@dataclass(frozen=True)
class GlobalBondV04Params:
    initial_sovereign_total_return_index: float = 100.0
    initial_corporate_total_return_index: float = 100.0
    initial_60_40_total_return_index: float = 100.0

    sovereign_duration_years: float = 7.0
    sovereign_convexity: float = 50.0

    corporate_risk_free_duration_years: float = 5.0
    corporate_risk_free_convexity: float = 28.0
    corporate_spread_duration_years: float = 4.2

    loss_given_default_fraction: float = 0.60
    default_probability_base_pct: float = 0.05
    default_risk_neutral_index: float = 30.0
    default_risk_beta_pct_per_index_point: float = 0.008
    credit_impairment_beta_pct_per_index_point: float = 0.012
    crisis_beta_pct_at_full_intensity: float = 0.40
    min_default_probability_pct: float = 0.0
    max_default_probability_pct: float = 8.0


@dataclass
class GlobalBondV04State:
    sovereign_total_return_index: float
    corporate_total_return_index: float
    portfolio_60_40_total_return_index: float


@dataclass(frozen=True)
class CorporateDefaultProbabilityBreakdown:
    base_pct: float
    default_risk_contribution_pct: float
    credit_impairment_contribution_pct: float
    crisis_contribution_pct: float
    raw_pct: float
    final_pct: float
    boundary_adjustment_pct: float
    boundary_state: str


def _finite(name: str, value: Any) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{name} must be finite") from error
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result

def _positive(name: str, value: Any) -> float:
    result = _finite(name, value)
    if result <= 0.0:
        raise ValueError(f"{name} must be finite and positive")
    return result


def _non_negative(name: str, value: Any) -> float:
    result = _finite(name, value)
    if result < 0.0:
        raise ValueError(f"{name} must be finite and non-negative")
    return result


def _required_number(row: Mapping[str, Any], field: str) -> float:
    if field not in row or row[field] is None or row[field] == "":
        raise ValueError(f"{field} is required for global bond v0.4")
    return _finite(field, row[field])


def _optional_non_negative(
    row: Mapping[str, Any],
    field: str,
    default: float,
) -> float:
    if field not in row or row[field] is None or row[field] == "":
        return float(default)
    return _non_negative(field, row[field])


def _year_index(row: Mapping[str, Any], position: int) -> int:
    if "year_index" not in row:
        raise ValueError("global bond v0.4 requires year_index on every input row")
    raw = _finite("year_index", row["year_index"])
    if not raw.is_integer():
        raise ValueError("global bond v0.4 requires integer year_index values")
    value = int(raw)
    if value != position:
        raise ValueError(
            "global bond v0.4 requires contiguous year_index values starting at 0"
        )
    return value


def _boundary_state(value: float, low: float, high: float) -> str:
    if value < low:
        return "floor"
    if value > high:
        return "cap"
    return "none"


def validate_params(params: GlobalBondV04Params) -> None:
    for name in (
        "initial_sovereign_total_return_index",
        "initial_corporate_total_return_index",
        "initial_60_40_total_return_index",
        "sovereign_duration_years",
        "sovereign_convexity",
        "corporate_risk_free_duration_years",
        "corporate_risk_free_convexity",
        "corporate_spread_duration_years",
    ):
        _positive(name, getattr(params, name))

    lgd = _finite("loss_given_default_fraction", params.loss_given_default_fraction)
    if lgd < 0.0 or lgd > 1.0:
        raise ValueError("loss_given_default_fraction must be in [0, 1]")

    for name in (
        "default_probability_base_pct",
        "default_risk_neutral_index",
        "default_risk_beta_pct_per_index_point",
        "credit_impairment_beta_pct_per_index_point",
        "crisis_beta_pct_at_full_intensity",
        "min_default_probability_pct",
        "max_default_probability_pct",
    ):
        _non_negative(name, getattr(params, name))

    floor = float(params.min_default_probability_pct)
    cap = float(params.max_default_probability_pct)
    base = float(params.default_probability_base_pct)
    if cap > 100.0:
        raise ValueError("max_default_probability_pct must not exceed 100")
    if floor >= cap:
        raise ValueError(
            "min_default_probability_pct must be below max_default_probability_pct"
        )
    if base < floor or base > cap:
        raise ValueError(
            "default_probability_base_pct must be inside the probability boundaries"
        )


def corporate_default_probability_breakdown(
    row: Mapping[str, Any],
    params: GlobalBondV04Params,
) -> CorporateDefaultProbabilityBreakdown:
    default_risk = _optional_non_negative(row, "default_risk_index", 30.0)
    impairment = _optional_non_negative(
        row, "credit_impairment_stock_index", 0.0
    )
    crisis = _optional_non_negative(row, "crisis_intensity", 0.0)

    base = float(params.default_probability_base_pct)
    default_risk_contribution = (
        float(params.default_risk_beta_pct_per_index_point)
        * max(0.0, default_risk - float(params.default_risk_neutral_index))
    )
    impairment_contribution = (
        float(params.credit_impairment_beta_pct_per_index_point) * impairment
    )
    crisis_contribution = (
        float(params.crisis_beta_pct_at_full_intensity) * crisis
    )
    raw = (
        base
        + default_risk_contribution
        + impairment_contribution
        + crisis_contribution
    )
    floor = float(params.min_default_probability_pct)
    cap = float(params.max_default_probability_pct)
    final = max(floor, min(cap, raw))
    return CorporateDefaultProbabilityBreakdown(
        base_pct=base,
        default_risk_contribution_pct=default_risk_contribution,
        credit_impairment_contribution_pct=impairment_contribution,
        crisis_contribution_pct=crisis_contribution,
        raw_pct=raw,
        final_pct=final,
        boundary_adjustment_pct=final - raw,
        boundary_state=_boundary_state(raw, floor, cap),
    )


def _initial_values(params: GlobalBondV04Params) -> dict[str, Any]:
    values: dict[str, Any] = {field: 0.0 for field in GLOBAL_BOND_V04_FIELDS}
    values.update(
        global_bond_v04_param_version=GLOBAL_BOND_V04_PARAM_VERSION,
        asset_accounting_contract_version=GLOBAL_BOND_V04_INTERFACE_VERSION,
        global_sovereign_bond_duration_years=params.sovereign_duration_years,
        global_sovereign_bond_convexity=params.sovereign_convexity,
        global_corporate_bond_risk_free_duration_years=(
            params.corporate_risk_free_duration_years
        ),
        global_corporate_bond_risk_free_convexity=(
            params.corporate_risk_free_convexity
        ),
        global_corporate_bond_spread_duration_years=(
            params.corporate_spread_duration_years
        ),
        global_corporate_bond_loss_given_default_fraction=(
            params.loss_given_default_fraction
        ),
        global_corporate_bond_default_probability_floor_pct=(
            params.min_default_probability_pct
        ),
        global_corporate_bond_default_probability_cap_pct=(
            params.max_default_probability_pct
        ),
        global_sovereign_bond_total_return_index=(
            params.initial_sovereign_total_return_index
        ),
        global_corporate_bond_total_return_index=(
            params.initial_corporate_total_return_index
        ),
        global_60_40_total_return_index=(
            params.initial_60_40_total_return_index
        ),
        global_corporate_bond_default_probability_boundary_state="none",
    )
    return values


def _validate_candidate_values(candidate: Mapping[str, Any]) -> None:
    for field in GLOBAL_BOND_V04_FIELDS:
        value = candidate[field]
        if isinstance(value, (int, float)) and not math.isfinite(float(value)):
            raise ValueError(f"candidate field {field} must be finite")


def simulate_global_bond_v04_for_macro_path(
    records: list[dict[str, Any]],
    params: GlobalBondV04Params | None = None,
) -> list[dict[str, Any]]:
    """Build the isolated v0.4 global-bond and annual 60/40 candidate.

    The input rows are copied, never mutated. The function deliberately ignores the
    legacy mixed bond-return fields and is not connected to the formal v0.15 runner.
    """

    settings = params or GlobalBondV04Params()
    validate_params(settings)
    if not records:
        return []

    state = GlobalBondV04State(
        sovereign_total_return_index=settings.initial_sovereign_total_return_index,
        corporate_total_return_index=settings.initial_corporate_total_return_index,
        portfolio_60_40_total_return_index=settings.initial_60_40_total_return_index,
    )
    result: list[dict[str, Any]] = []

    for position, row in enumerate(records):
        _year_index(row, position)
        current_yield = _required_number(row, "global_10y_yield_pct")
        current_ig_spread = _required_number(
            row, "global_investment_grade_spread_bps"
        )
        if current_ig_spread < 0.0:
            raise ValueError(
                "global_investment_grade_spread_bps must be non-negative"
            )

        if position == 0:
            candidate = _initial_values(settings)
            _validate_candidate_values(candidate)
            result.append({**row, **candidate})
            continue

        previous_row = records[position - 1]
        previous_yield = _required_number(previous_row, "global_10y_yield_pct")
        previous_ig_spread = _required_number(
            previous_row, "global_investment_grade_spread_bps"
        )
        if previous_ig_spread < 0.0:
            raise ValueError(
                "global_investment_grade_spread_bps must be non-negative"
            )
        equity_total_return = _required_number(
            row, "global_equity_total_return_pct"
        )
        if equity_total_return <= -100.0:
            raise ValueError(
                "global_equity_total_return_pct must be greater than -100"
            )

        sovereign = accounting.sovereign_bond_return_breakdown(
            previous_yield_pct=previous_yield,
            current_yield_pct=current_yield,
            duration_years=settings.sovereign_duration_years,
            convexity=settings.sovereign_convexity,
        )
        sovereign_index = accounting.compound_total_return_index(
            state.sovereign_total_return_index,
            sovereign.total_return_pct,
        )

        default_probability = corporate_default_probability_breakdown(row, settings)
        credit_loss = (
            default_probability.final_pct * settings.loss_given_default_fraction
        )
        corporate = accounting.corporate_bond_return_breakdown(
            previous_yield_pct=previous_yield,
            current_yield_pct=current_yield,
            previous_ig_spread_bps=previous_ig_spread,
            current_ig_spread_bps=current_ig_spread,
            credit_loss_pct=credit_loss,
            risk_free_duration_years=settings.corporate_risk_free_duration_years,
            spread_duration_years=settings.corporate_spread_duration_years,
            convexity=settings.corporate_risk_free_convexity,
        )
        risk_free_yield_change_decimal = (current_yield - previous_yield) / 100.0
        corporate_risk_free_price_return = 100.0 * (
            -settings.corporate_risk_free_duration_years
            * risk_free_yield_change_decimal
            + 0.5
            * settings.corporate_risk_free_convexity
            * risk_free_yield_change_decimal**2
        )
        ig_spread_change_decimal = (
            current_ig_spread - previous_ig_spread
        ) / 10_000.0
        corporate_ig_spread_price_return = (
            -settings.corporate_spread_duration_years
            * ig_spread_change_decimal
            * 100.0
        )
        corporate_index = accounting.compound_total_return_index(
            state.corporate_total_return_index,
            corporate.total_return_pct,
        )

        portfolio_return = accounting.rebalanced_60_40_return_pct(
            equity_total_return,
            sovereign.total_return_pct,
        )
        portfolio_index = accounting.compound_total_return_index(
            state.portfolio_60_40_total_return_index,
            portfolio_return,
        )

        sovereign_identity = (
            sovereign.total_return_pct
            - sovereign.price_return_pct
            - sovereign.carry_pct
        )
        corporate_identity = (
            corporate.total_return_pct
            - corporate_risk_free_price_return
            - corporate_ig_spread_price_return
            - corporate.carry_pct
            + credit_loss
        )
        portfolio_identity = (
            portfolio_return
            - 0.60 * equity_total_return
            - 0.40 * sovereign.total_return_pct
        )

        candidate = {
            "global_bond_v04_param_version": GLOBAL_BOND_V04_PARAM_VERSION,
            "asset_accounting_contract_version": GLOBAL_BOND_V04_INTERFACE_VERSION,
            "global_sovereign_bond_duration_years": settings.sovereign_duration_years,
            "global_sovereign_bond_convexity": settings.sovereign_convexity,
            "global_corporate_bond_risk_free_duration_years": (
                settings.corporate_risk_free_duration_years
            ),
            "global_corporate_bond_risk_free_convexity": (
                settings.corporate_risk_free_convexity
            ),
            "global_corporate_bond_spread_duration_years": (
                settings.corporate_spread_duration_years
            ),
            "global_corporate_bond_loss_given_default_fraction": (
                settings.loss_given_default_fraction
            ),
            "global_corporate_bond_default_probability_floor_pct": (
                settings.min_default_probability_pct
            ),
            "global_corporate_bond_default_probability_cap_pct": (
                settings.max_default_probability_pct
            ),
            "global_sovereign_bond_price_return_pct": sovereign.price_return_pct,
            "global_sovereign_bond_carry_pct": sovereign.carry_pct,
            "global_sovereign_bond_total_return_pct": sovereign.total_return_pct,
            "global_sovereign_bond_total_return_index": sovereign_index,
            "global_corporate_bond_risk_free_price_return_pct": (
                corporate_risk_free_price_return
            ),
            "global_corporate_bond_ig_spread_price_return_pct": (
                corporate_ig_spread_price_return
            ),
            "global_corporate_bond_price_return_pct": corporate.price_return_pct,
            "global_corporate_bond_carry_pct": corporate.carry_pct,
            "global_corporate_bond_default_probability_base_pct": (
                default_probability.base_pct
            ),
            "global_corporate_bond_default_risk_contribution_pct": (
                default_probability.default_risk_contribution_pct
            ),
            "global_corporate_bond_credit_impairment_contribution_pct": (
                default_probability.credit_impairment_contribution_pct
            ),
            "global_corporate_bond_crisis_contribution_pct": (
                default_probability.crisis_contribution_pct
            ),
            "global_corporate_bond_default_probability_proxy_raw_pct": (
                default_probability.raw_pct
            ),
            "global_corporate_bond_default_probability_proxy_pct": (
                default_probability.final_pct
            ),
            "global_corporate_bond_default_probability_boundary_adjustment_pct": (
                default_probability.boundary_adjustment_pct
            ),
            "global_corporate_bond_default_probability_boundary_state": (
                default_probability.boundary_state
            ),
            "global_corporate_bond_credit_loss_pct": credit_loss,
            "global_corporate_bond_total_return_pct": corporate.total_return_pct,
            "global_corporate_bond_total_return_index": corporate_index,
            "global_60_40_total_return_pct": portfolio_return,
            "global_60_40_total_return_index": portfolio_index,
            "global_sovereign_bond_total_return_identity_residual": (
                sovereign_identity
            ),
            "global_corporate_bond_total_return_identity_residual": (
                corporate_identity
            ),
            "global_60_40_total_return_identity_residual": portfolio_identity,
        }
        _validate_candidate_values(candidate)
        result.append({**row, **candidate})

        state.sovereign_total_return_index = sovereign_index
        state.corporate_total_return_index = corporate_index
        state.portfolio_60_40_total_return_index = portfolio_index

    return result
