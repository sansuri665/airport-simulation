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
import math
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean
from typing import Any

global_gdp_layer = import_module(f"{_SIBLING_PREFIX}global_gdp_annual_sim")

GDP_ANNUAL_FIELDS = global_gdp_layer.ANNUAL_FIELDS
GDPParams = global_gdp_layer.GDPParams
simulate_global_gdp = global_gdp_layer.simulate_global_gdp


INFLATION_PARAM_VERSION = "global-inflation-layer-v0.1"
INFLATION_INTERFACE_VERSION = "inflation-feedback-interface-v0.1"


INFLATION_FIELDS = [
    "inflation_param_version",
    "inflation_interface_version",
    "headline_inflation_pct",
    "core_inflation_pct",
    "energy_inflation_pct",
    "import_inflation_pct",
    "wage_pressure_pct",
    "inflation_expectation_pct",
    "demand_pull_component_pct",
    "energy_component_pct",
    "external_supply_shock_component_pct",
    "import_component_pct",
    "liquidity_component_pct",
    "stress_disinflation_component_pct",
    "inflation_noise_component_pct",
    "monetary_tightening_pressure",
    "monetary_easing_pressure",
    "inflation_regime",
    "inflation_to_policy_rate_impulse",
    "inflation_to_long_rate_impulse",
    "inflation_to_gdp_drag_placeholder",
]


COMBINED_FIELDS = GDP_ANNUAL_FIELDS + INFLATION_FIELDS


@dataclass(frozen=True)
class InflationParams:
    headline_anchor_pct: float = 2.35
    core_anchor_pct: float = 2.20
    expectation_anchor_pct: float = 2.25
    initial_headline_pct: float = 2.40
    initial_core_pct: float = 2.25
    initial_expectation_pct: float = 2.30
    initial_wage_pressure_pct: float = 2.65
    core_persistence: float = 0.74
    headline_persistence: float = 0.56
    expectation_persistence: float = 0.84
    wage_persistence: float = 0.70
    demand_gap_beta: float = 0.18
    growth_surprise_beta: float = 0.20
    wage_gap_beta: float = 0.12
    expectation_feedback_beta: float = 0.22
    liquidity_beta: float = 0.36
    energy_beta: float = 0.92
    external_supply_shock_chance_per_year: float = 0.055
    external_supply_shock_cycle_sensitivity: float = 0.006
    external_supply_shock_min_duration_years: int = 2
    external_supply_shock_max_duration_years: int = 5
    external_supply_shock_min_severity: float = 0.65
    external_supply_shock_max_severity: float = 1.00
    external_supply_shock_cooldown_years: int = 5
    import_beta: float = 0.48
    credit_stress_disinflation_beta: float = 0.34
    crisis_disinflation_beta: float = 0.42
    noise_scale: float = 0.16
    energy_noise_scale: float = 0.55
    import_noise_scale: float = 0.25
    inflation_seed_offset: int = 3_100_003
    max_headline_pct: float = 9.5
    min_headline_pct: float = -1.5
    max_core_pct: float = 7.0
    min_core_pct: float = -0.5


@dataclass
class InflationState:
    headline_inflation_pct: float = 2.40
    core_inflation_pct: float = 2.25
    inflation_expectation_pct: float = 2.30
    wage_pressure_pct: float = 2.65
    energy_inflation_pct: float = 2.60
    import_inflation_pct: float = 2.30
    energy_shock_stock: float = 0.0
    import_shock_stock: float = 0.0
    external_supply_shock_years_left: int = 0
    external_supply_shock_total_years: int = 0
    external_supply_shock_age: int = 0
    external_supply_shock_severity: float = 0.0
    external_supply_shock_cooldown: int = 0


@dataclass
class InflationRecord:
    inflation_param_version: str
    inflation_interface_version: str
    headline_inflation_pct: float
    core_inflation_pct: float
    energy_inflation_pct: float
    import_inflation_pct: float
    wage_pressure_pct: float
    inflation_expectation_pct: float
    demand_pull_component_pct: float
    energy_component_pct: float
    external_supply_shock_component_pct: float
    import_component_pct: float
    liquidity_component_pct: float
    stress_disinflation_component_pct: float
    inflation_noise_component_pct: float
    monetary_tightening_pressure: float
    monetary_easing_pressure: float
    inflation_regime: str
    inflation_to_policy_rate_impulse: float
    inflation_to_long_rate_impulse: float
    inflation_to_gdp_drag_placeholder: float



def smooth(old: float, target: float, speed: float) -> float:
    return old * (1.0 - speed) + target * speed


def as_float(row: dict[str, Any], key: str, default: float = 0.0) -> float:
    try:
        return float(row.get(key, default))
    except (TypeError, ValueError):
        return default


def classify_inflation_regime(
    headline: float,
    core: float,
    gdp_growth: float,
    output_gap: float,
    financial_stress: float,
    event_type: str,
    energy_component: float,
) -> str:
    if headline < 0.5 and (financial_stress >= 45.0 or gdp_growth < 0.5):
        return "deflationary_crisis"
    if headline >= 5.0 and gdp_growth < 1.4:
        return "stagflation_pressure"
    if headline >= 4.2 and output_gap >= 1.5:
        return "overheating_inflation"
    if energy_component >= 1.2 and headline >= 3.6:
        return "energy_cost_push"
    if event_type == "central_bank_easing_placeholder" and headline < 3.5:
        return "policy_reflation"
    if headline <= 1.4 and core <= 1.8:
        return "lowflation"
    if headline < core - 0.8:
        return "disinflation"
    return "anchored_normal"


def draw_external_supply_shock(
    state: InflationState,
    params: InflationParams,
    rng: random.Random,
    gdp_growth: float,
    output_gap: float,
) -> float:
    if state.external_supply_shock_years_left <= 0 and state.external_supply_shock_cooldown > 0:
        state.external_supply_shock_cooldown -= 1

    if state.external_supply_shock_years_left <= 0 and state.external_supply_shock_cooldown <= 0:
        demand_heat = max(0.0, gdp_growth - 2.8) + max(0.0, output_gap) * 0.35
        chance = params.external_supply_shock_chance_per_year + demand_heat * params.external_supply_shock_cycle_sensitivity
        if rng.random() < chance:
            state.external_supply_shock_total_years = rng.randint(
                params.external_supply_shock_min_duration_years,
                params.external_supply_shock_max_duration_years,
            )
            state.external_supply_shock_years_left = state.external_supply_shock_total_years
            state.external_supply_shock_age = 0
            state.external_supply_shock_severity = rng.uniform(
                params.external_supply_shock_min_severity,
                params.external_supply_shock_max_severity,
            )

    if state.external_supply_shock_years_left <= 0:
        return 0.0

    progress = state.external_supply_shock_age / max(1, state.external_supply_shock_total_years - 1)
    phase_shape = math.sin(math.pi * clamp(progress, 0.0, 1.0))
    if state.external_supply_shock_total_years <= 2:
        phase_shape = 1.0
    component = (1.10 + 2.40 * phase_shape) * state.external_supply_shock_severity
    state.external_supply_shock_age += 1
    state.external_supply_shock_years_left -= 1
    if state.external_supply_shock_years_left <= 0:
        state.external_supply_shock_total_years = 0
        state.external_supply_shock_age = 0
        state.external_supply_shock_severity = 0.0
        state.external_supply_shock_cooldown = params.external_supply_shock_cooldown_years
    return component


def simulate_inflation_for_gdp_path(
    seed: int,
    gdp_records: list[dict[str, Any]],
    params: InflationParams,
) -> list[dict[str, Any]]:
    rng = random.Random(seed + params.inflation_seed_offset)
    state = InflationState(
        headline_inflation_pct=params.initial_headline_pct + rng.uniform(-0.25, 0.25),
        core_inflation_pct=params.initial_core_pct + rng.uniform(-0.18, 0.18),
        inflation_expectation_pct=params.initial_expectation_pct + rng.uniform(-0.12, 0.12),
        wage_pressure_pct=params.initial_wage_pressure_pct + rng.uniform(-0.20, 0.20),
    )

    combined: list[dict[str, Any]] = []

    for row in gdp_records:
        year_index = int(row["year_index"])
        gdp_growth = as_float(row, "realized_growth_pct")
        potential_growth = as_float(row, "potential_growth_pct")
        output_gap = as_float(row, "output_gap_pct")
        stress = as_float(row, "financial_stress_index")
        crisis_intensity = as_float(row, "crisis_intensity")
        boom_intensity = as_float(row, "boom_intensity")
        liquidity_impulse = as_float(row, "liquidity_impulse")
        dollar_pressure_impulse = as_float(row, "dollar_pressure_impulse")
        energy_price_impulse = as_float(row, "energy_price_impulse")
        credit_stress_impulse = as_float(row, "credit_stress_impulse")
        feedback_inflation_impulse = as_float(row, "feedback_inflation_impulse_pct")
        event_type = str(row.get("event_type", "none"))

        if year_index == 0:
            inflation_record = InflationRecord(
                inflation_param_version=INFLATION_PARAM_VERSION,
                inflation_interface_version=INFLATION_INTERFACE_VERSION,
                headline_inflation_pct=state.headline_inflation_pct,
                core_inflation_pct=state.core_inflation_pct,
                energy_inflation_pct=state.energy_inflation_pct,
                import_inflation_pct=state.import_inflation_pct,
                wage_pressure_pct=state.wage_pressure_pct,
                inflation_expectation_pct=state.inflation_expectation_pct,
                demand_pull_component_pct=0.0,
                energy_component_pct=0.0,
                external_supply_shock_component_pct=0.0,
                import_component_pct=0.0,
                liquidity_component_pct=0.0,
                stress_disinflation_component_pct=0.0,
                inflation_noise_component_pct=0.0,
                monetary_tightening_pressure=0.0,
                monetary_easing_pressure=0.0,
                inflation_regime="initial",
                inflation_to_policy_rate_impulse=0.0,
                inflation_to_long_rate_impulse=0.0,
                inflation_to_gdp_drag_placeholder=0.0,
            )
            combined.append(round_record({**row, **asdict(inflation_record)}))
            continue

        growth_surprise = gdp_growth - potential_growth
        demand_pull = params.demand_gap_beta * output_gap + params.growth_surprise_beta * growth_surprise
        demand_pull += 0.18 * boom_intensity
        demand_pull += 0.08 * feedback_inflation_impulse

        state.energy_shock_stock = state.energy_shock_stock * 0.58 + energy_price_impulse + 0.42 * feedback_inflation_impulse
        state.import_shock_stock = state.import_shock_stock * 0.62 + dollar_pressure_impulse

        external_supply_shock = draw_external_supply_shock(
            state,
            params,
            rng,
            gdp_growth,
            output_gap,
        )
        energy_component = (
            params.energy_beta * state.energy_shock_stock
            + external_supply_shock
            + rng.gauss(0.0, params.energy_noise_scale)
        )
        import_component = (
            params.import_beta * state.import_shock_stock
            + 0.22 * external_supply_shock
            + rng.gauss(0.0, params.import_noise_scale)
        )
        liquidity_component = params.liquidity_beta * liquidity_impulse
        stress_disinflation = -params.credit_stress_disinflation_beta * max(0.0, stress - 35.0) / 20.0
        stress_disinflation -= 0.22 * max(0.0, credit_stress_impulse)
        crisis_disinflation = -params.crisis_disinflation_beta * crisis_intensity
        noise = rng.gauss(0.0, params.noise_scale)

        wage_target = (
            params.initial_wage_pressure_pct
            + params.wage_gap_beta * output_gap
            + 0.35 * max(0.0, state.inflation_expectation_pct - params.expectation_anchor_pct)
            - 0.18 * max(0.0, stress - 45.0) / 20.0
        )
        state.wage_pressure_pct = clamp(
            smooth(state.wage_pressure_pct, wage_target, 1.0 - params.wage_persistence),
            -0.5,
            7.0,
        )

        expectation_target = (
            params.expectation_anchor_pct
            + 0.35 * (state.headline_inflation_pct - params.headline_anchor_pct)
            + 0.25 * (state.core_inflation_pct - params.core_anchor_pct)
            + 0.08 * external_supply_shock
            + 0.12 * liquidity_impulse
            + 0.08 * feedback_inflation_impulse
            - 0.10 * crisis_intensity
        )
        state.inflation_expectation_pct = clamp(
            smooth(state.inflation_expectation_pct, expectation_target, 1.0 - params.expectation_persistence),
            0.4,
            6.5,
        )

        core_target = (
            params.core_anchor_pct
            + demand_pull
            + liquidity_component
            + 0.26 * import_component
            + 0.32 * (state.wage_pressure_pct - params.initial_wage_pressure_pct)
            + params.expectation_feedback_beta * (state.inflation_expectation_pct - params.expectation_anchor_pct)
            + stress_disinflation
            + crisis_disinflation
            + 0.16 * feedback_inflation_impulse
            + noise
        )
        state.core_inflation_pct = clamp(
            smooth(state.core_inflation_pct, core_target, 1.0 - params.core_persistence),
            params.min_core_pct,
            params.max_core_pct,
        )

        state.energy_inflation_pct = clamp(
            params.headline_anchor_pct + 3.0 * energy_component + rng.gauss(0.0, 0.35),
            -8.0,
            15.0,
        )
        state.import_inflation_pct = clamp(
            params.headline_anchor_pct + 2.2 * import_component + rng.gauss(0.0, 0.20),
            -4.0,
            10.0,
        )

        headline_target = (
            0.62 * state.core_inflation_pct
            + 0.28 * state.energy_inflation_pct
            + 0.10 * state.import_inflation_pct
            + 0.55 * feedback_inflation_impulse
        )
        state.headline_inflation_pct = clamp(
            smooth(state.headline_inflation_pct, headline_target, 1.0 - params.headline_persistence),
            params.min_headline_pct,
            params.max_headline_pct,
        )

        inflation_regime = classify_inflation_regime(
            state.headline_inflation_pct,
            state.core_inflation_pct,
            gdp_growth,
            output_gap,
            stress,
            event_type,
            energy_component,
        )

        inflation_gap = state.headline_inflation_pct - params.headline_anchor_pct
        tightening_pressure = clamp(
            18.0 * max(0.0, inflation_gap)
            + 5.0 * max(0.0, output_gap)
            - 3.0 * crisis_intensity,
            0.0,
            100.0,
        )
        easing_pressure = clamp(
            16.0 * max(0.0, params.headline_anchor_pct - state.headline_inflation_pct)
            + 5.0 * max(0.0, -output_gap)
            + 0.35 * stress
            + 10.0 * crisis_intensity,
            0.0,
            100.0,
        )

        policy_impulse = clamp((tightening_pressure - easing_pressure) / 100.0, -1.0, 1.0)
        long_rate_impulse = clamp(
            (0.60 * inflation_gap + 0.20 * max(0.0, state.inflation_expectation_pct - params.expectation_anchor_pct)) / 4.0,
            -1.0,
            1.0,
        )
        gdp_drag_placeholder = clamp(-max(0.0, inflation_gap - 1.2) * 0.20, -1.0, 0.0)

        inflation_record = InflationRecord(
            inflation_param_version=INFLATION_PARAM_VERSION,
            inflation_interface_version=INFLATION_INTERFACE_VERSION,
            headline_inflation_pct=state.headline_inflation_pct,
            core_inflation_pct=state.core_inflation_pct,
            energy_inflation_pct=state.energy_inflation_pct,
            import_inflation_pct=state.import_inflation_pct,
            wage_pressure_pct=state.wage_pressure_pct,
            inflation_expectation_pct=state.inflation_expectation_pct,
            demand_pull_component_pct=demand_pull,
            energy_component_pct=energy_component,
            external_supply_shock_component_pct=external_supply_shock,
            import_component_pct=import_component,
            liquidity_component_pct=liquidity_component,
            stress_disinflation_component_pct=stress_disinflation + crisis_disinflation,
            inflation_noise_component_pct=noise,
            monetary_tightening_pressure=tightening_pressure,
            monetary_easing_pressure=easing_pressure,
            inflation_regime=inflation_regime,
            inflation_to_policy_rate_impulse=policy_impulse,
            inflation_to_long_rate_impulse=long_rate_impulse,
            inflation_to_gdp_drag_placeholder=gdp_drag_placeholder,
        )
        combined.append(round_record({**row, **asdict(inflation_record)}))

    return combined


def summarize_seed(records: list[dict[str, Any]]) -> dict[str, Any]:
    data = records[1:] if len(records) > 1 else records
    headline_values = [as_float(row, "headline_inflation_pct") for row in data]
    core_values = [as_float(row, "core_inflation_pct") for row in data]
    max_headline_row = max(data, key=lambda row: as_float(row, "headline_inflation_pct")) if data else records[-1]
    min_headline_row = min(data, key=lambda row: as_float(row, "headline_inflation_pct")) if data else records[-1]
    stagflation_years = sum(1 for row in data if str(row["inflation_regime"]) == "stagflation_pressure")
    high_inflation_years = sum(1 for row in data if as_float(row, "headline_inflation_pct") >= 4.0)
    lowflation_years = sum(1 for row in data if as_float(row, "headline_inflation_pct") <= 1.4)
    final = records[-1]
    return {
        "seed": int(final["seed"]),
        "start_year": int(records[0]["year"]),
        "end_year": int(final["year"]),
        "average_headline_inflation_pct": round(mean(headline_values), 3) if headline_values else 0.0,
        "average_core_inflation_pct": round(mean(core_values), 3) if core_values else 0.0,
        "max_headline_inflation_pct": as_float(max_headline_row, "headline_inflation_pct"),
        "max_headline_year": int(max_headline_row["year"]),
        "min_headline_inflation_pct": as_float(min_headline_row, "headline_inflation_pct"),
        "min_headline_year": int(min_headline_row["year"]),
        "high_inflation_years": high_inflation_years,
        "lowflation_years": lowflation_years,
        "stagflation_years": stagflation_years,
        "final_headline_inflation_pct": as_float(final, "headline_inflation_pct"),
        "final_core_inflation_pct": as_float(final, "core_inflation_pct"),
    }


def write_viewer_data_js(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(rows, ensure_ascii=False, separators=(",", ":"))
    path.write_text(f"window.GLOBAL_GDP_INFLATION_DATA = {payload};\n", encoding="utf-8")


def build_inflation_svg(records_by_seed: dict[int, list[dict[str, Any]]], path: Path) -> None:
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
    values = [as_float(row, "headline_inflation_pct") for row in all_records]
    min_year, max_year = min(years), max(years)
    min_value = min(-1.0, min(values) - 0.5)
    max_value = max(6.0, max(values) + 0.5)

    def x_of(year: int) -> float:
        return left + (year - min_year) / max(1, max_year - min_year) * plot_w

    def y_of(value: float) -> float:
        return top + (max_value - value) / max(1e-9, max_value - min_value) * plot_h

    palette = ["#60a5fa", "#34d399", "#fb7185", "#f59e0b", "#a78bfa", "#22d3ee", "#f472b6", "#eab308"]
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#07090d"/>',
        f'<text x="{left}" y="27" font-family="Arial" font-size="20" fill="#f5f7fb">Global Inflation Paths by Seed</text>',
        f'<text x="{left}" y="50" font-family="Arial" font-size="12" fill="#94a3b8">Headline inflation generated from GDP output gap, stress, liquidity, dollar, and energy placeholders</text>',
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
    lines.append(f'<line x1="{left}" y1="{y_of(2.0):.2f}" x2="{left + plot_w}" y2="{y_of(2.0):.2f}" stroke="#64748b" stroke-dasharray="5 5"/>')
    lines.append(f'<text x="{left + plot_w - 5}" y="{y_of(2.0) - 6:.2f}" text-anchor="end" font-family="Arial" font-size="11" fill="#94a3b8">2% anchor</text>')

    for idx, (seed, records) in enumerate(sorted(records_by_seed.items())):
        color = palette[idx % len(palette)]
        points = " ".join(
            f'{x_of(int(row["year"])):.2f},{y_of(as_float(row, "headline_inflation_pct")):.2f}'
            for row in records
        )
        lines.append(f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round"/>')
        last = records[-1]
        lines.append(
            f'<text x="{x_of(int(last["year"])) + 6:.2f}" y="{y_of(as_float(last, "headline_inflation_pct")) + 4:.2f}" '
            f'font-family="Arial" font-size="11" fill="{color}">seed {seed}</text>'
        )

    lines.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}" stroke="#64748b"/>')
    lines.append(f'<line x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}" stroke="#64748b"/>')
    lines.append(f'<text x="18" y="{top + plot_h / 2}" transform="rotate(-90 18 {top + plot_h / 2})" text-anchor="middle" font-family="Arial" font-size="12" fill="#94a3b8">headline inflation %</text>')
    lines.append("</svg>")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a combined global GDP + inflation annual simulation.",
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

    records_by_seed: dict[int, list[dict[str, Any]]] = {}
    for seed in seeds:
        gdp_records = simulate_global_gdp(seed, gdp_params)
        records_by_seed[seed] = simulate_inflation_for_gdp_path(seed, gdp_records, inflation_params)

    all_records = [row for records in records_by_seed.values() for row in records]
    summaries = [summarize_seed(records) for records in records_by_seed.values()]

    args.output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = args.output_dir / "global_gdp_inflation_seed_sweep.csv"
    json_path = args.output_dir / "global_gdp_inflation_seed_sweep.json"
    viewer_data_path = args.output_dir / "global_gdp_inflation_viewer_data.js"
    svg_path = args.output_dir / "global_inflation_curves.svg"

    write_csv(csv_path, all_records, COMBINED_FIELDS)
    write_json(
        json_path,
        {
            "gdp_param_version": gdp_records[0]["param_version"] if seeds else "",
            "inflation_param_version": INFLATION_PARAM_VERSION,
            "inflation_interface_version": INFLATION_INTERFACE_VERSION,
            "gdp_params": asdict(gdp_params),
            "inflation_params": asdict(inflation_params),
            "seeds": seeds,
            "summary": summaries,
            "model_note": {
                "coupling": "Inflation is downstream of the GDP layer in this version. It reads output gap, growth surprise, financial stress, and macro-event placeholder impulses.",
                "no_feedback_yet": "Inflation-to-GDP feedback is emitted as placeholder impulse fields only; GDP paths are not recomputed from inflation in v0.1.",
                "future_connection": "The inflation_to_policy_rate_impulse and inflation_to_long_rate_impulse fields are intended for a later rate/yield-curve layer.",
            },
        },
    )
    write_viewer_data_js(viewer_data_path, all_records)
    if not args.no_svg:
        build_inflation_svg(records_by_seed, svg_path)

    print(f"Wrote {csv_path}")
    print(f"Wrote {json_path}")
    print(f"Wrote {viewer_data_path}")
    if not args.no_svg:
        print(f"Wrote {svg_path}")
    for summary in summaries:
        print(
            "seed={seed} avg_headline={average_headline_inflation_pct:.2f}% "
            "max_headline={max_headline_inflation_pct:.2f}%({max_headline_year}) "
            "min_headline={min_headline_inflation_pct:.2f}%({min_headline_year}) "
            "high_inflation_years={high_inflation_years}".format(**summary)
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
