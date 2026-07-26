from __future__ import annotations

import math
import random
from dataclasses import dataclass
from importlib import import_module
from typing import Any, Mapping


_SIBLING_PREFIX = f"{__package__}." if __package__ else ""
accounting = import_module(f"{_SIBLING_PREFIX}asset_accounting_v04")
simulation_utils = import_module(f"{_SIBLING_PREFIX}simulation_utils")

ASSET_ACCOUNTING_CONTRACT_VERSION = accounting.ASSET_ACCOUNTING_CONTRACT_VERSION
equity_return_breakdown = accounting.equity_return_breakdown
stable_substream_seed = accounting.stable_substream_seed
round_record = simulation_utils.round_record


GLOBAL_EQUITY_V04_PARAM_VERSION = accounting.GLOBAL_EQUITY_V04_PARAM_VERSION
GLOBAL_EQUITY_V04_INTERFACE_VERSION = ASSET_ACCOUNTING_CONTRACT_VERSION

EPS_CONTRIBUTION_FIELDS = (
    "global_equity_eps_base_contribution_pp",
    "global_equity_eps_growth_contribution_pp",
    "global_equity_eps_inflation_contribution_pp",
    "global_equity_eps_cycle_contribution_pp",
    "global_equity_eps_margin_contribution_pp",
    "global_equity_eps_credit_contribution_pp",
    "global_equity_eps_dollar_contribution_pp",
    "global_equity_eps_capital_destruction_contribution_pp",
    "global_equity_eps_noise_contribution_pp",
)

PE_CONTRIBUTION_FIELDS = (
    "global_equity_pe_anchor",
    "global_equity_pe_rate_contribution",
    "global_equity_pe_credit_contribution",
    "global_equity_pe_fci_contribution",
    "global_equity_pe_policy_contribution",
    "global_equity_pe_dollar_contribution",
    "global_equity_pe_liquidity_contribution",
    "global_equity_pe_risk_appetite_contribution",
    "global_equity_pe_impulse_contribution",
    "global_equity_pe_crisis_contribution",
    "global_equity_pe_noise_contribution",
)

GLOBAL_EQUITY_V04_FIELDS = (
    "global_equity_v04_param_version",
    "asset_accounting_contract_version",
    "global_equity_eps_index",
    "global_equity_eps_growth_raw_pct",
    "global_equity_eps_growth_pct",
    *EPS_CONTRIBUTION_FIELDS,
    "global_equity_eps_smoothing_adjustment_pp",
    "global_equity_eps_boundary_adjustment_pp",
    "global_equity_eps_boundary_state",
    "global_equity_valuation_pe_raw",
    "global_equity_valuation_pe",
    *PE_CONTRIBUTION_FIELDS,
    "global_equity_pe_smoothing_adjustment",
    "global_equity_pe_boundary_adjustment",
    "global_equity_pe_boundary_state",
    "global_equity_price_index",
    "global_equity_price_return_pct",
    "global_equity_payout_ratio_pct",
    "global_equity_dividend_yield_pct",
    "global_equity_total_return_pct",
    "global_equity_total_return_index",
    "global_equity_drawdown_pct",
    "global_equity_price_identity_residual",
    "global_equity_total_return_identity_residual",
)


@dataclass(frozen=True)
class GlobalEquityV04Params:
    initial_eps_index: float = 100.0
    initial_pe: float = 18.0
    initial_price_index: float = 100.0
    initial_total_return_index: float = 100.0
    initial_payout_ratio_pct: float = 45.0
    base_eps_growth_pct: float = 1.20
    eps_smoothing: float = 0.38
    min_eps_growth_pct: float = -35.0
    max_eps_growth_pct: float = 35.0
    min_eps_index: float = 1.0
    pe_anchor: float = 19.0
    pe_smoothing: float = 0.32
    min_pe: float = 8.5
    max_pe: float = 32.0
    payout_smoothing: float = 0.25
    min_payout_ratio_pct: float = accounting.MIN_EQUITY_PAYOUT_RATIO_PCT
    max_payout_ratio_pct: float = accounting.MAX_EQUITY_PAYOUT_RATIO_PCT
    eps_noise_scale: float = 0.90
    pe_noise_scale: float = 0.315


@dataclass
class GlobalEquityV04State:
    eps_index: float
    eps_growth_pct: float
    valuation_pe: float
    price_index: float
    total_return_index: float
    payout_ratio_pct: float
    peak_price_index: float


def _number(row: Mapping[str, Any], field: str, default: float = 0.0) -> float:
    value = row.get(field, default)
    if value is None or value == "":
        return float(default)
    try:
        result = float(value)
    except (TypeError, ValueError):
        return float(default)
    return result if math.isfinite(result) else float(default)


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _boundary_state(value: float, low: float, high: float) -> str:
    if value < low:
        return "floor"
    if value > high:
        return "cap"
    return "none"


def _normal(seed: int, year_index: int, shock_id: str, scale: float) -> float:
    substream = stable_substream_seed(
        seed,
        layer_id="global_equity_v04",
        region_id="global",
        year_index=year_index,
        shock_id=shock_id,
    )
    return random.Random(substream).gauss(0.0, scale)


def validate_params(params: GlobalEquityV04Params) -> None:
    for name in (
        "initial_eps_index",
        "initial_pe",
        "initial_price_index",
        "initial_total_return_index",
    ):
        value = float(getattr(params, name))
        if not math.isfinite(value) or value <= 0.0:
            raise ValueError(f"{name} must be finite and positive")
    if not math.isclose(
        params.initial_price_index,
        params.initial_eps_index,
        rel_tol=0.0,
        abs_tol=1e-12,
    ):
        raise ValueError("initial_price_index must equal initial_eps_index when PE equals its anchor")
    for name in ("eps_smoothing", "pe_smoothing", "payout_smoothing"):
        value = float(getattr(params, name))
        if value <= 0.0 or value > 1.0:
            raise ValueError(f"{name} must be in (0, 1]")
    if not params.min_pe < params.initial_pe < params.max_pe:
        raise ValueError("initial_pe must be strictly inside the PE boundaries")
    if not params.min_payout_ratio_pct <= params.initial_payout_ratio_pct <= params.max_payout_ratio_pct:
        raise ValueError("initial_payout_ratio_pct is outside payout boundaries")


def _initial_values(params: GlobalEquityV04Params) -> dict[str, Any]:
    values: dict[str, Any] = {field: 0.0 for field in GLOBAL_EQUITY_V04_FIELDS}
    values.update(
        global_equity_v04_param_version=GLOBAL_EQUITY_V04_PARAM_VERSION,
        asset_accounting_contract_version=GLOBAL_EQUITY_V04_INTERFACE_VERSION,
        global_equity_eps_index=params.initial_eps_index,
        global_equity_valuation_pe_raw=params.initial_pe,
        global_equity_valuation_pe=params.initial_pe,
        global_equity_pe_anchor=params.initial_pe,
        global_equity_eps_boundary_state="none",
        global_equity_pe_boundary_state="none",
        global_equity_price_index=params.initial_price_index,
        global_equity_payout_ratio_pct=params.initial_payout_ratio_pct,
        global_equity_total_return_index=params.initial_total_return_index,
    )
    return values


def _eps_contributions(
    row: Mapping[str, Any],
    *,
    seed: int,
    year_index: int,
    params: GlobalEquityV04Params,
) -> dict[str, float]:
    growth = _number(row, "realized_growth_pct")
    potential = _number(row, "potential_growth_pct", 2.0)
    gap = _number(row, "output_gap_pct")
    headline = _number(row, "headline_inflation_pct", 2.35)
    core = _number(row, "core_inflation_pct", 2.2)
    impairment = _number(row, "credit_impairment_stock_index")
    dollar = _number(row, "global_dollar_index", 100.0)
    crisis = _number(row, "crisis_intensity")
    return {
        "global_equity_eps_base_contribution_pp": params.base_eps_growth_pct,
        "global_equity_eps_growth_contribution_pp": 1.15 * growth,
        "global_equity_eps_inflation_contribution_pp": 0.28 * headline,
        "global_equity_eps_cycle_contribution_pp": (
            0.42 * gap
            - 1.20 * max(0.0, potential - growth)
            - 2.20 * max(0.0, -growth)
        ),
        "global_equity_eps_margin_contribution_pp": -(
            0.65 * max(0.0, headline - 4.0)
            + 0.35 * max(0.0, core - 3.5)
        ),
        # Realised impairment belongs to earnings; market spreads stay in PE.
        "global_equity_eps_credit_contribution_pp": -0.025 * max(0.0, impairment),
        "global_equity_eps_dollar_contribution_pp": -0.40 * max(0.0, dollar - 103.0),
        "global_equity_eps_capital_destruction_contribution_pp": -3.50 * max(0.0, crisis),
        "global_equity_eps_noise_contribution_pp": _normal(
            seed, year_index, "eps", params.eps_noise_scale
        ),
    }


def _pe_contributions(
    row: Mapping[str, Any],
    *,
    seed: int,
    year_index: int,
    params: GlobalEquityV04Params,
) -> dict[str, float]:
    real_10y = _number(row, "global_real_10y_yield_pct")
    hy_spread = _number(row, "global_high_yield_spread_bps", 420.0)
    default_risk = _number(row, "default_risk_index", 30.0)
    fci = _number(row, "global_financial_conditions_index")
    policy = _number(row, "policy_stance_index")
    dollar = _number(row, "global_dollar_index", 100.0)
    liquidity = _number(row, "global_liquidity_index", 55.0)
    risk_appetite = _number(row, "risk_appetite_index", 50.0)
    credit_impulse = _number(row, "credit_to_equity_risk_premium_impulse")
    yield_impulse = _number(row, "yield_curve_to_equity_valuation_impulse")
    liquidity_impulse = _number(row, "liquidity_to_equity_impulse")
    crisis = _number(row, "crisis_intensity")
    return {
        "global_equity_pe_anchor": params.pe_anchor,
        "global_equity_pe_rate_contribution": (
            -1.65 * max(0.0, real_10y) + 0.75 * max(0.0, -real_10y)
        ),
        "global_equity_pe_credit_contribution": -(
            0.0025 * max(0.0, hy_spread - 420.0)
            + 0.006 * max(0.0, default_risk - 30.0)
        ),
        "global_equity_pe_fci_contribution": (
            -0.85 * max(0.0, fci) + 0.20 * max(0.0, -fci)
        ),
        "global_equity_pe_policy_contribution": (
            -0.65 * max(0.0, policy) + 0.15 * max(0.0, -policy)
        ),
        "global_equity_pe_dollar_contribution": -0.030 * max(0.0, dollar - 100.0),
        "global_equity_pe_liquidity_contribution": 0.075 * (liquidity - 55.0),
        "global_equity_pe_risk_appetite_contribution": 0.065 * (risk_appetite - 50.0),
        "global_equity_pe_impulse_contribution": (
            -0.85 * max(0.0, credit_impulse)
            + 0.70 * yield_impulse
            + 0.55 * liquidity_impulse
        ),
        "global_equity_pe_crisis_contribution": -2.80 * max(0.0, crisis),
        "global_equity_pe_noise_contribution": _normal(
            seed, year_index, "pe", params.pe_noise_scale
        ),
    }


def simulate_global_equity_v04_for_macro_path(
    records: list[dict[str, Any]],
    params: GlobalEquityV04Params | None = None,
) -> list[dict[str, Any]]:
    """Build the isolated v0.4 global-equity candidate without altering legacy rows."""

    settings = params or GlobalEquityV04Params()
    validate_params(settings)
    if not records:
        return []

    seed = int(records[0].get("seed", 0))
    state = GlobalEquityV04State(
        eps_index=settings.initial_eps_index,
        eps_growth_pct=0.0,
        valuation_pe=settings.initial_pe,
        price_index=settings.initial_price_index,
        total_return_index=settings.initial_total_return_index,
        payout_ratio_pct=settings.initial_payout_ratio_pct,
        peak_price_index=settings.initial_price_index,
    )
    result: list[dict[str, Any]] = []

    for position, row in enumerate(records):
        year_index = int(row.get("year_index", position))
        if year_index != position:
            raise ValueError("global equity v0.4 requires contiguous year_index values starting at 0")
        if position == 0:
            result.append(round_record({**row, **_initial_values(settings)}))
            continue

        eps_parts = _eps_contributions(
            row, seed=seed, year_index=year_index, params=settings
        )
        eps_raw = sum(eps_parts.values())
        eps_smoothed = (
            state.eps_growth_pct * (1.0 - settings.eps_smoothing)
            + eps_raw * settings.eps_smoothing
        )
        eps_smoothing_adjustment = eps_smoothed - eps_raw
        eps_boundary_state = _boundary_state(
            eps_smoothed, settings.min_eps_growth_pct, settings.max_eps_growth_pct
        )
        bounded_growth = _clamp(
            eps_smoothed, settings.min_eps_growth_pct, settings.max_eps_growth_pct
        )
        proposed_eps = state.eps_index * (1.0 + bounded_growth / 100.0)
        eps_index = max(settings.min_eps_index, proposed_eps)
        eps_growth = (eps_index / state.eps_index - 1.0) * 100.0
        eps_boundary_adjustment = eps_growth - eps_smoothed
        if proposed_eps < settings.min_eps_index:
            eps_boundary_state = "floor"

        pe_parts = _pe_contributions(
            row, seed=seed, year_index=year_index, params=settings
        )
        pe_raw = sum(pe_parts.values())
        pe_smoothed = (
            state.valuation_pe * (1.0 - settings.pe_smoothing)
            + pe_raw * settings.pe_smoothing
        )
        pe_smoothing_adjustment = pe_smoothed - pe_raw
        pe_boundary_state = _boundary_state(pe_smoothed, settings.min_pe, settings.max_pe)
        valuation_pe = _clamp(pe_smoothed, settings.min_pe, settings.max_pe)
        pe_boundary_adjustment = valuation_pe - pe_smoothed

        crisis = _number(row, "crisis_intensity")
        hy_spread = _number(row, "global_high_yield_spread_bps", 420.0)
        impairment = _number(row, "credit_impairment_stock_index")
        payout_target = (
            45.0
            + 0.10 * max(0.0, eps_growth)
            - 0.25 * max(0.0, -eps_growth)
            - 5.0 * max(0.0, crisis)
            - 0.010 * max(0.0, hy_spread - 450.0)
            - 0.025 * max(0.0, impairment)
        )
        payout_ratio = _clamp(
            state.payout_ratio_pct * (1.0 - settings.payout_smoothing)
            + payout_target * settings.payout_smoothing,
            settings.min_payout_ratio_pct,
            settings.max_payout_ratio_pct,
        )

        returns = equity_return_breakdown(
            previous_price_index=state.price_index,
            previous_total_return_index=state.total_return_index,
            eps_index=eps_index,
            valuation_pe=valuation_pe,
            payout_ratio_pct=payout_ratio,
            initial_pe=settings.initial_pe,
        )
        peak_price = max(state.peak_price_index, returns.price_index)
        drawdown = (returns.price_index / peak_price - 1.0) * 100.0
        expected_price = eps_index * valuation_pe / settings.initial_pe
        expected_total_return = returns.price_return_pct + returns.dividend_yield_pct

        candidate = {
            "global_equity_v04_param_version": GLOBAL_EQUITY_V04_PARAM_VERSION,
            "asset_accounting_contract_version": GLOBAL_EQUITY_V04_INTERFACE_VERSION,
            "global_equity_eps_index": eps_index,
            "global_equity_eps_growth_raw_pct": eps_raw,
            "global_equity_eps_growth_pct": eps_growth,
            **eps_parts,
            "global_equity_eps_smoothing_adjustment_pp": eps_smoothing_adjustment,
            "global_equity_eps_boundary_adjustment_pp": eps_boundary_adjustment,
            "global_equity_eps_boundary_state": eps_boundary_state,
            "global_equity_valuation_pe_raw": pe_raw,
            "global_equity_valuation_pe": valuation_pe,
            **pe_parts,
            "global_equity_pe_smoothing_adjustment": pe_smoothing_adjustment,
            "global_equity_pe_boundary_adjustment": pe_boundary_adjustment,
            "global_equity_pe_boundary_state": pe_boundary_state,
            "global_equity_price_index": returns.price_index,
            "global_equity_price_return_pct": returns.price_return_pct,
            "global_equity_payout_ratio_pct": payout_ratio,
            "global_equity_dividend_yield_pct": returns.dividend_yield_pct,
            "global_equity_total_return_pct": returns.total_return_pct,
            "global_equity_total_return_index": returns.total_return_index,
            "global_equity_drawdown_pct": drawdown,
            "global_equity_price_identity_residual": returns.price_index - expected_price,
            "global_equity_total_return_identity_residual": (
                returns.total_return_pct - expected_total_return
            ),
        }
        result.append(round_record({**row, **candidate}))

        state.eps_index = eps_index
        state.eps_growth_pct = eps_growth
        state.valuation_pe = valuation_pe
        state.price_index = returns.price_index
        state.total_return_index = returns.total_return_index
        state.payout_ratio_pct = payout_ratio
        state.peak_price_index = peak_price

    return result
