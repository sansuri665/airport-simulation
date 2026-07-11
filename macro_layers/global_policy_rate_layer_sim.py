from __future__ import annotations

from importlib import import_module

_SIBLING_PREFIX = f"{__package__}." if __package__ else ""
simulation_io = import_module(f"{_SIBLING_PREFIX}simulation_io")
simulation_utils = import_module(f"{_SIBLING_PREFIX}simulation_utils")

write_csv = simulation_io.write_csv
write_json = simulation_io.write_json
clamp = simulation_utils.clamp
resolve_seeds = simulation_utils.resolve_seeds
round_record = simulation_utils.round_record

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean
from typing import Any

global_gdp_layer = import_module(f"{_SIBLING_PREFIX}global_gdp_annual_sim")
inflation_layer = import_module(f"{_SIBLING_PREFIX}global_inflation_annual_sim")

GDPParams = global_gdp_layer.GDPParams
simulate_global_gdp = global_gdp_layer.simulate_global_gdp
GDP_INFLATION_FIELDS = inflation_layer.COMBINED_FIELDS
INFLATION_PARAM_VERSION = inflation_layer.INFLATION_PARAM_VERSION
InflationParams = inflation_layer.InflationParams
as_float = inflation_layer.as_float
simulate_inflation_for_gdp_path = inflation_layer.simulate_inflation_for_gdp_path


POLICY_PARAM_VERSION = "global-policy-rate-layer-v0.1"
POLICY_INTERFACE_VERSION = "policy-feedback-interface-v0.1"


POLICY_FIELDS = [
    "policy_param_version",
    "policy_interface_version",
    "global_policy_rate_pct",
    "policy_reaction_target_rate_pct",
    "neutral_policy_rate_pct",
    "real_policy_rate_pct",
    "shadow_policy_rate_pct",
    "policy_rate_change_pct",
    "rate_hike_pressure",
    "rate_cut_pressure",
    "qe_liquidity_index",
    "balance_sheet_impulse",
    "policy_stance_index",
    "central_bank_reaction_regime",
    "policy_to_credit_tightening_impulse",
    "policy_to_dollar_pressure_impulse",
    "policy_to_equity_valuation_impulse",
    "policy_to_gdp_drag_placeholder",
    "policy_to_inflation_lagged_impulse",
]


COMBINED_POLICY_FIELDS = GDP_INFLATION_FIELDS + POLICY_FIELDS


@dataclass(frozen=True)
class PolicyRateParams:
    initial_policy_rate_pct: float = 3.25
    min_policy_rate_pct: float = 0.05
    max_policy_rate_pct: float = 8.50
    base_real_neutral_rate_pct: float = 0.75
    potential_growth_neutral_beta: float = 0.18
    stress_neutral_drag_beta: float = 0.20
    inflation_headline_target_pct: float = 2.35
    inflation_core_target_pct: float = 2.20
    headline_inflation_beta: float = 0.42
    core_inflation_beta: float = 0.78
    output_gap_beta: float = 0.22
    financial_stress_easing_beta: float = 0.035
    crisis_easing_beta: float = 1.10
    inflation_policy_impulse_beta: float = 1.35
    event_policy_impulse_beta: float = 0.70
    feedback_policy_impulse_beta: float = 0.60
    policy_adjustment_speed: float = 0.38
    max_hike_per_year_pct: float = 1.10
    max_cut_per_year_pct: float = 1.45
    emergency_cut_per_year_pct: float = 2.20
    qe_activation_cut_pressure: float = 42.0
    qe_decay: float = 0.78
    qe_build_speed: float = 0.34
    qe_policy_floor_pct: float = 1.25
    qe_shadow_rate_beta: float = 0.025


@dataclass
class PolicyRateState:
    policy_rate_pct: float = 3.25
    qe_liquidity_index: float = 8.0
    previous_policy_rate_pct: float = 3.25


@dataclass
class PolicyRateRecord:
    policy_param_version: str
    policy_interface_version: str
    global_policy_rate_pct: float
    policy_reaction_target_rate_pct: float
    neutral_policy_rate_pct: float
    real_policy_rate_pct: float
    shadow_policy_rate_pct: float
    policy_rate_change_pct: float
    rate_hike_pressure: float
    rate_cut_pressure: float
    qe_liquidity_index: float
    balance_sheet_impulse: float
    policy_stance_index: float
    central_bank_reaction_regime: str
    policy_to_credit_tightening_impulse: float
    policy_to_dollar_pressure_impulse: float
    policy_to_equity_valuation_impulse: float
    policy_to_gdp_drag_placeholder: float
    policy_to_inflation_lagged_impulse: float



def smooth(old: float, target: float, speed: float) -> float:
    return old * (1.0 - speed) + target * speed


def classify_policy_regime(
    *,
    policy_rate: float,
    policy_change: float,
    real_policy_rate: float,
    neutral_policy_rate: float,
    qe_liquidity_index: float,
    headline_inflation: float,
    core_inflation: float,
    gdp_growth: float,
    output_gap: float,
    stress: float,
    crisis_intensity: float,
    hike_pressure: float,
    cut_pressure: float,
    inflation_regime: str,
) -> str:
    if crisis_intensity >= 0.65 or (stress >= 55.0 and cut_pressure >= 48.0):
        return "emergency_easing"
    if headline_inflation >= 4.0 and gdp_growth < 1.5:
        return "stagflation_dilemma"
    if policy_change >= 0.45 and hike_pressure > cut_pressure:
        return "hawkish_tightening"
    if policy_change <= -0.45 and cut_pressure >= hike_pressure:
        return "rate_cut_cycle"
    if qe_liquidity_index >= 45.0 and real_policy_rate < neutral_policy_rate - 1.0:
        return "qe_repair"
    if real_policy_rate > neutral_policy_rate + 1.0 and gdp_growth <= 2.0:
        return "restrictive_pause"
    if headline_inflation > 3.4 or core_inflation > 3.0 or inflation_regime == "overheating_inflation":
        return "inflation_watch"
    if output_gap < -2.0 or cut_pressure > hike_pressure + 15.0:
        return "dovish_support"
    if abs(real_policy_rate - neutral_policy_rate) <= 0.55:
        return "neutral_hold"
    if policy_rate < neutral_policy_rate:
        return "accommodative_hold"
    return "mildly_restrictive"


def policy_reaction_target_rate(
    *,
    params: PolicyRateParams,
    neutral_policy_rate: float,
    headline: float,
    core: float,
    output_gap: float,
    stress: float,
    crisis_intensity: float,
    inflation_policy_impulse: float,
    event_policy_impulse: float,
    feedback_policy_impulse: float,
) -> float:
    headline_gap = headline - params.inflation_headline_target_pct
    core_gap = core - params.inflation_core_target_pct
    stress_easing = params.financial_stress_easing_beta * max(0.0, stress - 35.0)
    crisis_easing = params.crisis_easing_beta * crisis_intensity
    target_rate = (
        neutral_policy_rate
        + params.headline_inflation_beta * headline_gap
        + params.core_inflation_beta * core_gap
        + params.output_gap_beta * output_gap
        + params.inflation_policy_impulse_beta * inflation_policy_impulse
        + params.event_policy_impulse_beta * event_policy_impulse
        + params.feedback_policy_impulse_beta * feedback_policy_impulse
        - stress_easing
        - crisis_easing
    )
    return clamp(target_rate, params.min_policy_rate_pct, params.max_policy_rate_pct)


def simulate_policy_for_macro_path(
    records: list[dict[str, Any]],
    params: PolicyRateParams,
) -> list[dict[str, Any]]:
    state = PolicyRateState(
        policy_rate_pct=params.initial_policy_rate_pct,
        previous_policy_rate_pct=params.initial_policy_rate_pct,
        qe_liquidity_index=8.0,
    )

    combined: list[dict[str, Any]] = []

    for row in records:
        year_index = int(row["year_index"])
        headline = as_float(row, "headline_inflation_pct", params.inflation_headline_target_pct)
        core = as_float(row, "core_inflation_pct", params.inflation_core_target_pct)
        expectation = as_float(row, "inflation_expectation_pct", params.inflation_headline_target_pct)
        output_gap = as_float(row, "output_gap_pct")
        potential_growth = as_float(row, "potential_growth_pct", 2.0)
        gdp_growth = as_float(row, "realized_growth_pct")
        stress = as_float(row, "financial_stress_index")
        crisis_intensity = as_float(row, "crisis_intensity")
        event_policy_impulse = as_float(row, "policy_rate_impulse")
        inflation_policy_impulse = as_float(row, "inflation_to_policy_rate_impulse")
        tightening_pressure = as_float(row, "monetary_tightening_pressure")
        easing_pressure = as_float(row, "monetary_easing_pressure")
        feedback_policy_impulse = as_float(row, "feedback_policy_impulse_pct")
        inflation_regime = str(row.get("inflation_regime", "none"))

        real_neutral_rate = clamp(
            params.base_real_neutral_rate_pct
            + params.potential_growth_neutral_beta * (potential_growth - 2.0)
            - params.stress_neutral_drag_beta * max(0.0, stress - 35.0) / 40.0,
            -0.25,
            2.25,
        )
        neutral_policy_rate = clamp(real_neutral_rate + expectation, 0.35, 6.00)

        if year_index == 0:
            real_policy_rate = state.policy_rate_pct - expectation
            shadow_policy_rate = state.policy_rate_pct - params.qe_shadow_rate_beta * state.qe_liquidity_index
            policy_record = PolicyRateRecord(
                policy_param_version=POLICY_PARAM_VERSION,
                policy_interface_version=POLICY_INTERFACE_VERSION,
                global_policy_rate_pct=state.policy_rate_pct,
                policy_reaction_target_rate_pct=neutral_policy_rate,
                neutral_policy_rate_pct=neutral_policy_rate,
                real_policy_rate_pct=real_policy_rate,
                shadow_policy_rate_pct=shadow_policy_rate,
                policy_rate_change_pct=0.0,
                rate_hike_pressure=0.0,
                rate_cut_pressure=0.0,
                qe_liquidity_index=state.qe_liquidity_index,
                balance_sheet_impulse=0.0,
                policy_stance_index=real_policy_rate - real_neutral_rate,
                central_bank_reaction_regime="initial",
                policy_to_credit_tightening_impulse=0.0,
                policy_to_dollar_pressure_impulse=0.0,
                policy_to_equity_valuation_impulse=0.0,
                policy_to_gdp_drag_placeholder=0.0,
                policy_to_inflation_lagged_impulse=0.0,
            )
            combined.append(round_record({**row, **asdict(policy_record)}))
            continue

        headline_gap = headline - params.inflation_headline_target_pct
        core_gap = core - params.inflation_core_target_pct
        target_rate = policy_reaction_target_rate(
            params=params,
            neutral_policy_rate=neutral_policy_rate,
            headline=headline,
            core=core,
            output_gap=output_gap,
            stress=stress,
            crisis_intensity=crisis_intensity,
            inflation_policy_impulse=inflation_policy_impulse,
            event_policy_impulse=event_policy_impulse,
            feedback_policy_impulse=feedback_policy_impulse,
        )

        desired_change = target_rate - state.policy_rate_pct
        max_cut = params.emergency_cut_per_year_pct if crisis_intensity >= 0.65 else params.max_cut_per_year_pct
        desired_change = clamp(desired_change, -max_cut, params.max_hike_per_year_pct)
        new_policy_rate = clamp(
            smooth(state.policy_rate_pct, state.policy_rate_pct + desired_change, params.policy_adjustment_speed),
            params.min_policy_rate_pct,
            params.max_policy_rate_pct,
        )
        policy_change = new_policy_rate - state.policy_rate_pct
        state.previous_policy_rate_pct = state.policy_rate_pct
        state.policy_rate_pct = new_policy_rate

        hike_pressure = clamp(
            0.55 * tightening_pressure
            + 12.0 * max(0.0, headline_gap)
            + 16.0 * max(0.0, core_gap)
            + 4.0 * max(0.0, output_gap),
            0.0,
            100.0,
        )
        cut_pressure = clamp(
            0.60 * easing_pressure
            + 0.42 * stress
            + 22.0 * crisis_intensity
            + 5.0 * max(0.0, -output_gap)
            + 8.0 * max(0.0, params.inflation_headline_target_pct - headline),
            0.0,
            100.0,
        )

        qe_target = 0.0
        if state.policy_rate_pct <= params.qe_policy_floor_pct or cut_pressure >= params.qe_activation_cut_pressure:
            qe_target = clamp(
                20.0
                + 0.80 * max(0.0, cut_pressure - params.qe_activation_cut_pressure)
                + 35.0 * crisis_intensity
                - 0.40 * max(0.0, hike_pressure - cut_pressure),
                0.0,
                100.0,
            )
        old_qe = state.qe_liquidity_index
        if qe_target > state.qe_liquidity_index:
            state.qe_liquidity_index = smooth(state.qe_liquidity_index, qe_target, params.qe_build_speed)
        else:
            state.qe_liquidity_index *= params.qe_decay
        state.qe_liquidity_index = clamp(state.qe_liquidity_index, 0.0, 100.0)
        balance_sheet_impulse = state.qe_liquidity_index - old_qe

        real_policy_rate = state.policy_rate_pct - expectation
        shadow_policy_rate = state.policy_rate_pct - params.qe_shadow_rate_beta * state.qe_liquidity_index
        policy_stance_index = real_policy_rate - real_neutral_rate - 0.018 * state.qe_liquidity_index
        regime = classify_policy_regime(
            policy_rate=state.policy_rate_pct,
            policy_change=policy_change,
            real_policy_rate=real_policy_rate,
            neutral_policy_rate=neutral_policy_rate,
            qe_liquidity_index=state.qe_liquidity_index,
            headline_inflation=headline,
            core_inflation=core,
            gdp_growth=gdp_growth,
            output_gap=output_gap,
            stress=stress,
            crisis_intensity=crisis_intensity,
            hike_pressure=hike_pressure,
            cut_pressure=cut_pressure,
            inflation_regime=inflation_regime,
        )

        credit_tightening = clamp(
            0.28 * policy_stance_index + 0.55 * max(0.0, policy_change) - 0.018 * state.qe_liquidity_index,
            -2.0,
            2.0,
        )
        dollar_pressure = clamp(0.22 * policy_stance_index + 0.35 * policy_change - 0.010 * state.qe_liquidity_index, -2.0, 2.0)
        equity_valuation = clamp(-0.35 * policy_stance_index - 0.45 * max(0.0, policy_change) + 0.018 * state.qe_liquidity_index, -2.0, 2.0)
        gdp_drag = clamp(-0.18 * max(0.0, policy_stance_index) - 0.15 * max(0.0, policy_change), -1.5, 0.35)
        inflation_lagged = clamp(-0.20 * max(0.0, policy_stance_index) - 0.12 * max(0.0, policy_change) + 0.010 * state.qe_liquidity_index, -1.0, 1.0)

        policy_record = PolicyRateRecord(
            policy_param_version=POLICY_PARAM_VERSION,
            policy_interface_version=POLICY_INTERFACE_VERSION,
            global_policy_rate_pct=state.policy_rate_pct,
            policy_reaction_target_rate_pct=target_rate,
            neutral_policy_rate_pct=neutral_policy_rate,
            real_policy_rate_pct=real_policy_rate,
            shadow_policy_rate_pct=shadow_policy_rate,
            policy_rate_change_pct=policy_change,
            rate_hike_pressure=hike_pressure,
            rate_cut_pressure=cut_pressure,
            qe_liquidity_index=state.qe_liquidity_index,
            balance_sheet_impulse=balance_sheet_impulse,
            policy_stance_index=policy_stance_index,
            central_bank_reaction_regime=regime,
            policy_to_credit_tightening_impulse=credit_tightening,
            policy_to_dollar_pressure_impulse=dollar_pressure,
            policy_to_equity_valuation_impulse=equity_valuation,
            policy_to_gdp_drag_placeholder=gdp_drag,
            policy_to_inflation_lagged_impulse=inflation_lagged,
        )
        combined.append(round_record({**row, **asdict(policy_record)}))

    return combined


def summarize_seed(records: list[dict[str, Any]]) -> dict[str, Any]:
    data = records[1:] if len(records) > 1 else records
    policy_values = [as_float(row, "global_policy_rate_pct") for row in data]
    max_rate_row = max(data, key=lambda row: as_float(row, "global_policy_rate_pct")) if data else records[-1]
    min_rate_row = min(data, key=lambda row: as_float(row, "global_policy_rate_pct")) if data else records[-1]
    easing_years = sum(1 for row in data if str(row["central_bank_reaction_regime"]) in {"emergency_easing", "rate_cut_cycle", "qe_repair", "dovish_support"})
    tightening_years = sum(1 for row in data if str(row["central_bank_reaction_regime"]) in {"hawkish_tightening", "inflation_watch", "restrictive_pause"})
    qe_years = sum(1 for row in data if as_float(row, "qe_liquidity_index") >= 35.0)
    final = records[-1]
    return {
        "seed": int(final["seed"]),
        "start_year": int(records[0]["year"]),
        "end_year": int(final["year"]),
        "average_policy_rate_pct": round(mean(policy_values), 3) if policy_values else 0.0,
        "max_policy_rate_pct": as_float(max_rate_row, "global_policy_rate_pct"),
        "max_policy_rate_year": int(max_rate_row["year"]),
        "min_policy_rate_pct": as_float(min_rate_row, "global_policy_rate_pct"),
        "min_policy_rate_year": int(min_rate_row["year"]),
        "easing_years": easing_years,
        "tightening_years": tightening_years,
        "qe_years": qe_years,
        "final_policy_rate_pct": as_float(final, "global_policy_rate_pct"),
        "final_policy_regime": str(final["central_bank_reaction_regime"]),
    }


def write_viewer_data_js(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(rows, ensure_ascii=False, separators=(",", ":"))
    path.write_text(f"window.GLOBAL_POLICY_RATE_DATA = {payload};\n", encoding="utf-8")


def build_policy_svg(records_by_seed: dict[int, list[dict[str, Any]]], path: Path) -> None:
    width = 1180
    height = 680
    left = 76
    right = 36
    top = 42
    bottom = 72
    plot_w = width - left - right
    plot_h = height - top - bottom
    all_records = [row for rows in records_by_seed.values() for row in rows]
    years = [int(row["year"]) for row in all_records]
    values = [as_float(row, "global_policy_rate_pct") for row in all_records]
    min_year, max_year = min(years), max(years)
    min_value = max(0.0, min(values) - 0.5)
    max_value = max(6.0, max(values) + 0.5)

    def x_of(year: int) -> float:
        return left + (year - min_year) / max(1, max_year - min_year) * plot_w

    def y_of(value: float) -> float:
        return top + (max_value - value) / max(1e-9, max_value - min_value) * plot_h

    palette = ["#a78bfa", "#60a5fa", "#34d399", "#fb7185", "#f59e0b", "#22d3ee", "#f472b6", "#eab308"]
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#07090d"/>',
        f'<text x="{left}" y="27" font-family="Arial" font-size="20" fill="#f5f7fb">Global Policy Rate Paths by Seed</text>',
        f'<text x="{left}" y="50" font-family="Arial" font-size="12" fill="#94a3b8">Policy-rate reaction to GDP gap, inflation, stress, crisis, and liquidity placeholders</text>',
    ]

    for i in range(7):
        y = top + i / 6 * plot_h
        value = max_value - i / 6 * (max_value - min_value)
        lines.append(f'<line x1="{left}" y1="{y:.2f}" x2="{left + plot_w}" y2="{y:.2f}" stroke="#1f2937"/>')
        lines.append(f'<text x="{left - 10}" y="{y + 4:.2f}" text-anchor="end" font-family="Arial" font-size="11" fill="#94a3b8">{value:.1f}%</text>')
    for i in range(6):
        x = left + i / 5 * plot_w
        year = round(min_year + i / 5 * (max_year - min_year))
        lines.append(f'<line x1="{x:.2f}" y1="{top}" x2="{x:.2f}" y2="{top + plot_h}" stroke="#172033"/>')
        lines.append(f'<text x="{x:.2f}" y="{top + plot_h + 24}" text-anchor="middle" font-family="Arial" font-size="11" fill="#94a3b8">{year}</text>')

    for idx, (seed, records) in enumerate(sorted(records_by_seed.items())):
        color = palette[idx % len(palette)]
        points = " ".join(
            f'{x_of(int(row["year"])):.2f},{y_of(as_float(row, "global_policy_rate_pct")):.2f}'
            for row in records
        )
        lines.append(f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round"/>')
        last = records[-1]
        lines.append(
            f'<text x="{x_of(int(last["year"])) + 6:.2f}" y="{y_of(as_float(last, "global_policy_rate_pct")) + 4:.2f}" '
            f'font-family="Arial" font-size="11" fill="{color}">seed {seed}</text>'
        )

    lines.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}" stroke="#64748b"/>')
    lines.append(f'<line x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}" stroke="#64748b"/>')
    lines.append(f'<text x="18" y="{top + plot_h / 2}" transform="rotate(-90 18 {top + plot_h / 2})" text-anchor="middle" font-family="Arial" font-size="12" fill="#94a3b8">policy rate %</text>')
    lines.append("</svg>")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a combined global GDP + inflation + policy-rate annual simulation.",
    )
    parser.add_argument("--years", type=int, default=60, help="Number of simulated years after the initial year.")
    parser.add_argument("--start-year", type=int, default=2025, help="Calendar year for the initial observation.")
    parser.add_argument("--initial-gdp", type=float, default=110.0, help="Initial global GDP in trillion USD.")
    parser.add_argument("--volatility-scale", type=float, default=1.55, help="Scales GDP cycle amplitude and random shocks.")
    parser.add_argument("--seed", type=int, default=None, help="Run one seed only.")
    parser.add_argument("--seeds", type=int, nargs="*", default=None, help="Run an explicit list of seeds.")
    parser.add_argument("--seed-start", type=int, default=1, help="First seed when --seed/--seeds is omitted.")
    parser.add_argument("--seed-count", type=int, default=8, help="Number of seeds when --seed/--seeds is omitted.")
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parents[1] / "output" / "global_macro")
    parser.add_argument("--no-svg", action="store_true", help="Skip writing the SVG chart.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    seeds = resolve_seeds(args)
    if args.years < 1:
        raise SystemExit("--years must be at least 1")
    if args.volatility_scale <= 0:
        raise SystemExit("--volatility-scale must be positive")

    gdp_params = GDPParams(
        years=args.years,
        start_year=args.start_year,
        initial_gdp_trillion_usd=args.initial_gdp,
        volatility_scale=args.volatility_scale,
    )
    inflation_params = InflationParams()
    policy_params = PolicyRateParams()

    records_by_seed: dict[int, list[dict[str, Any]]] = {}
    for seed in seeds:
        gdp_records = simulate_global_gdp(seed, gdp_params)
        inflation_records = simulate_inflation_for_gdp_path(seed, gdp_records, inflation_params)
        records_by_seed[seed] = simulate_policy_for_macro_path(inflation_records, policy_params)

    all_records = [row for records in records_by_seed.values() for row in records]
    summaries = [summarize_seed(records) for records in records_by_seed.values()]

    args.output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = args.output_dir / "global_policy_rate_seed_sweep.csv"
    json_path = args.output_dir / "global_policy_rate_seed_sweep.json"
    viewer_data_path = args.output_dir / "global_policy_viewer_data.js"
    svg_path = args.output_dir / "global_policy_rate_curves.svg"

    write_csv(csv_path, all_records, COMBINED_POLICY_FIELDS)
    write_json(
        json_path,
        {
            "gdp_param_version": all_records[0]["param_version"] if all_records else "",
            "inflation_param_version": INFLATION_PARAM_VERSION,
            "policy_param_version": POLICY_PARAM_VERSION,
            "policy_interface_version": POLICY_INTERFACE_VERSION,
            "gdp_params": asdict(gdp_params),
            "inflation_params": asdict(inflation_params),
            "policy_params": asdict(policy_params),
            "seeds": seeds,
            "summary": summaries,
            "model_note": {
                "coupling": "Policy rate is downstream of GDP and inflation in this version. It reads output gap, inflation, stress, and macro event placeholders.",
                "no_feedback_yet": "Policy-to-GDP, policy-to-dollar, policy-to-credit, and policy-to-asset impulses are emitted as placeholders only; upstream paths are not recomputed in v0.1.",
                "future_connection": "The policy_to_* fields are intended for later yield-curve, dollar, equity, credit, and GDP feedback layers.",
            },
        },
    )
    write_viewer_data_js(viewer_data_path, all_records)
    if not args.no_svg:
        build_policy_svg(records_by_seed, svg_path)

    print(f"Wrote {csv_path}")
    print(f"Wrote {json_path}")
    print(f"Wrote {viewer_data_path}")
    if not args.no_svg:
        print(f"Wrote {svg_path}")
    for summary in summaries:
        print(
            "seed={seed} avg_policy={average_policy_rate_pct:.2f}% "
            "max_policy={max_policy_rate_pct:.2f}%({max_policy_rate_year}) "
            "min_policy={min_policy_rate_pct:.2f}%({min_policy_rate_year}) "
            "qe_years={qe_years}".format(**summary)
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
