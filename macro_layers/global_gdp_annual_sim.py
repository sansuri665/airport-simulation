from __future__ import annotations

import argparse
import csv
import json
import math
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean
from typing import Any, Iterable, Mapping


PARAM_VERSION = "global-gdp-cycle-v0.4"
EVENT_INTERFACE_VERSION = "macro-event-interface-v0.1"


ANNUAL_FIELDS = [
    "year_index",
    "year",
    "seed",
    "param_version",
    "global_gdp_trillion_usd",
    "real_gdp_index",
    "potential_gdp_index",
    "realized_growth_pct",
    "potential_growth_pct",
    "trend_growth_pct",
    "cycle_growth_component_pct",
    "long_wave_component_pct",
    "infrastructure_component_pct",
    "investment_component_pct",
    "inventory_component_pct",
    "stochastic_component_pct",
    "shock_component_pct",
    "output_gap_pct",
    "financial_stress_index",
    "productivity_wave_index",
    "crisis_intensity",
    "boom_intensity",
    "regime",
    "event_interface_version",
    "event_type",
    "event_phase",
    "event_severity",
    "policy_rate_impulse",
    "liquidity_impulse",
    "credit_stress_impulse",
    "dollar_pressure_impulse",
    "energy_price_impulse",
    "gdp_lagged_support",
    "feedback_growth_impulse_pct",
    "feedback_output_gap_impulse_pct",
    "feedback_financial_stress_impulse",
    "feedback_inflation_impulse_pct",
    "feedback_policy_impulse_pct",
    "feedback_source",
]


@dataclass(frozen=True)
class CycleSpec:
    name: str
    period_years: float
    amplitude_pct: float
    phase: float
    persistence: float
    noise_scale: float


@dataclass(frozen=True)
class GDPParams:
    years: int = 60
    start_year: int = 2025
    initial_gdp_trillion_usd: float = 110.0
    initial_index: float = 100.0
    base_trend_growth_pct: float = 2.75
    terminal_trend_growth_pct: float = 1.75
    trend_slowdown_half_life_years: float = 70.0
    trend_noise_pct: float = 0.16
    volatility_scale: float = 1.55
    output_gap_persistence: float = 0.68
    output_gap_adjustment_speed: float = 0.34
    output_gap_cycle_loading: float = 0.56
    output_gap_shock_loading: float = 0.92
    output_gap_cap_pct: float = 13.5
    growth_adjustment_speed: float = 0.50
    max_growth_step_pct: float = 2.05
    shock_decay: float = 0.52
    shock_release_speed: float = 0.50
    direct_cycle_growth_loading: float = 0.10
    direct_shock_growth_loading: float = 0.52
    financial_stress_decay: float = 0.62
    crisis_era_chance_per_year: float = 0.042
    crisis_cycle_sensitivity: float = 0.010
    crisis_min_duration_years: int = 3
    crisis_max_duration_years: int = 7
    crisis_severity_min: float = 0.55
    crisis_severity_max: float = 1.00
    crisis_cooldown_min_years: int = 4
    crisis_cooldown_max_years: int = 8
    crisis_chance_per_year: float = 0.018
    deep_crisis_chance_per_year: float = 0.006
    boom_chance_per_year: float = 0.060
    max_positive_growth_pct: float = 9.5
    max_negative_growth_pct: float = -8.5


@dataclass
class GDPState:
    potential_index: float = 100.0
    real_index: float = 100.0
    output_gap_pct: float = 0.0
    financial_stress_index: float = 10.0
    trend_growth_pct: float = 2.75
    last_shock_pct: float = 0.0
    last_boom_pct: float = 0.0
    shock_stock_pct: float = 0.0
    last_realized_growth_pct: float = 2.75
    crisis_years_left: int = 0
    crisis_total_years: int = 0
    crisis_age: int = 0
    crisis_severity: float = 0.0
    crisis_cooldown_years: int = 0
    cycle_memory: dict[str, float] | None = None


@dataclass(frozen=True)
class MacroEventStub:
    event_interface_version: str = EVENT_INTERFACE_VERSION
    event_type: str = "none"
    event_phase: str = "none"
    event_severity: float = 0.0
    policy_rate_impulse: float = 0.0
    liquidity_impulse: float = 0.0
    credit_stress_impulse: float = 0.0
    dollar_pressure_impulse: float = 0.0
    energy_price_impulse: float = 0.0
    gdp_lagged_support: float = 0.0


@dataclass
class YearRecord:
    year_index: int
    year: int
    seed: int
    param_version: str
    global_gdp_trillion_usd: float
    real_gdp_index: float
    potential_gdp_index: float
    realized_growth_pct: float
    potential_growth_pct: float
    trend_growth_pct: float
    cycle_growth_component_pct: float
    long_wave_component_pct: float
    infrastructure_component_pct: float
    investment_component_pct: float
    inventory_component_pct: float
    stochastic_component_pct: float
    shock_component_pct: float
    output_gap_pct: float
    financial_stress_index: float
    productivity_wave_index: float
    crisis_intensity: float
    boom_intensity: float
    regime: str
    event_interface_version: str
    event_type: str
    event_phase: str
    event_severity: float
    policy_rate_impulse: float
    liquidity_impulse: float
    credit_stress_impulse: float
    dollar_pressure_impulse: float
    energy_price_impulse: float
    gdp_lagged_support: float
    feedback_growth_impulse_pct: float
    feedback_output_gap_impulse_pct: float
    feedback_financial_stress_impulse: float
    feedback_inflation_impulse_pct: float
    feedback_policy_impulse_pct: float
    feedback_source: str


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def smooth(old: float, target: float, speed: float) -> float:
    return old * (1.0 - speed) + target * speed


def pct_change(current: float, previous: float) -> float:
    if previous <= 0:
        return 0.0
    return (current / previous - 1.0) * 100.0


def mapping_float(source: Mapping[str, Any], key: str, default: float = 0.0) -> float:
    value = source.get(key, default)
    if value in ("", None):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def feedback_for_year(
    feedback_by_year_index: Mapping[int, Mapping[str, Any]] | None,
    year_index: int,
) -> dict[str, Any]:
    if not feedback_by_year_index:
        source: Mapping[str, Any] = {}
    else:
        source = feedback_by_year_index.get(year_index, {})
    return {
        "feedback_growth_impulse_pct": clamp(mapping_float(source, "feedback_growth_impulse_pct"), -1.80, 1.05),
        "feedback_output_gap_impulse_pct": clamp(mapping_float(source, "feedback_output_gap_impulse_pct"), -2.50, 1.80),
        "feedback_financial_stress_impulse": clamp(mapping_float(source, "feedback_financial_stress_impulse"), -9.0, 18.0),
        "feedback_inflation_impulse_pct": clamp(mapping_float(source, "feedback_inflation_impulse_pct"), -1.20, 1.60),
        "feedback_policy_impulse_pct": clamp(mapping_float(source, "feedback_policy_impulse_pct"), -1.20, 1.40),
        "feedback_source": str(source.get("feedback_source", "none")) if source else "none",
    }


def sin_wave(t: int, period: float, phase: float) -> float:
    return math.sin(2.0 * math.pi * (t / period) + phase)


def draw_cycle_specs(rng: random.Random, volatility_scale: float) -> dict[str, CycleSpec]:
    return {
        "inventory": CycleSpec(
            name="inventory",
            period_years=rng.uniform(3.2, 5.2),
            amplitude_pct=rng.uniform(0.25, 0.65) * volatility_scale,
            phase=rng.uniform(0.0, 2.0 * math.pi),
            persistence=rng.uniform(0.25, 0.45),
            noise_scale=0.10 * volatility_scale,
        ),
        "investment": CycleSpec(
            name="investment",
            period_years=rng.uniform(7.0, 11.5),
            amplitude_pct=rng.uniform(0.65, 1.35) * volatility_scale,
            phase=rng.uniform(0.0, 2.0 * math.pi),
            persistence=rng.uniform(0.35, 0.58),
            noise_scale=0.12 * volatility_scale,
        ),
        "infrastructure": CycleSpec(
            name="infrastructure",
            period_years=rng.uniform(16.0, 25.0),
            amplitude_pct=rng.uniform(0.35, 0.95) * volatility_scale,
            phase=rng.uniform(0.0, 2.0 * math.pi),
            persistence=rng.uniform(0.45, 0.70),
            noise_scale=0.08 * volatility_scale,
        ),
        "long_wave": CycleSpec(
            name="long_wave",
            period_years=rng.uniform(48.0, 68.0),
            amplitude_pct=rng.uniform(0.55, 1.15) * volatility_scale,
            phase=rng.uniform(0.0, 2.0 * math.pi),
            persistence=rng.uniform(0.55, 0.80),
            noise_scale=0.05 * volatility_scale,
        ),
    }


def cycle_component(
    t: int,
    spec: CycleSpec,
    state: GDPState,
    rng: random.Random,
) -> float:
    assert state.cycle_memory is not None
    raw = spec.amplitude_pct * sin_wave(t, spec.period_years, spec.phase)
    raw += rng.gauss(0.0, spec.noise_scale)
    previous = state.cycle_memory.get(spec.name, 0.0)
    value = smooth(raw, previous, spec.persistence)
    state.cycle_memory[spec.name] = value
    return value


def long_run_trend(t: int, params: GDPParams, rng: random.Random) -> float:
    slowdown_weight = 1.0 - math.exp(-t / max(1.0, params.trend_slowdown_half_life_years))
    deterministic = (
        params.base_trend_growth_pct * (1.0 - slowdown_weight)
        + params.terminal_trend_growth_pct * slowdown_weight
    )
    return deterministic + rng.gauss(0.0, params.trend_noise_pct * params.volatility_scale)


def crisis_phase(progress: float) -> str:
    if progress < 0.26:
        return "crisis_onset"
    if progress < 0.58:
        return "deep_crisis"
    return "crisis_repair"


def maybe_start_crisis_era(
    state: GDPState,
    params: GDPParams,
    rng: random.Random,
    cycle_growth: float,
) -> None:
    if state.crisis_years_left > 0:
        return
    if state.crisis_cooldown_years > 0:
        return
    cycle_pressure = max(0.0, -cycle_growth) * params.crisis_cycle_sensitivity
    chance = params.crisis_era_chance_per_year + cycle_pressure
    if rng.random() >= chance:
        return
    state.crisis_total_years = rng.randint(
        params.crisis_min_duration_years,
        params.crisis_max_duration_years,
    )
    state.crisis_years_left = state.crisis_total_years
    state.crisis_age = 0
    state.crisis_severity = rng.uniform(
        params.crisis_severity_min,
        params.crisis_severity_max,
    )


def draw_event_shock(
    state: GDPState,
    params: GDPParams,
    rng: random.Random,
    cycle_growth: float,
) -> tuple[float, float, float, str]:
    shock_pct = 0.0
    crisis_intensity = 0.0
    boom_intensity = 0.0
    phase = ""

    maybe_start_crisis_era(state, params, rng, cycle_growth)

    if state.crisis_years_left > 0:
        progress = state.crisis_age / max(1, state.crisis_total_years - 1)
        phase = crisis_phase(progress)
        if phase == "crisis_onset":
            phase_load = 0.45 + progress / 0.26 * 0.35
            shock_pct = -(0.95 + 2.15 * phase_load) * params.volatility_scale
        elif phase == "deep_crisis":
            phase_load = 0.85 + 0.15 * math.sin(math.pi * (progress - 0.26) / 0.32)
            shock_pct = -(1.45 + 2.95 * phase_load) * params.volatility_scale
        else:
            repair_left = max(0.0, (1.0 - progress) / 0.42)
            phase_load = 0.20 + 0.65 * repair_left
            shock_pct = -(0.25 + 1.35 * phase_load) * params.volatility_scale
            boom_intensity = clamp(0.25 * (1.0 - repair_left), 0.0, 0.35)

        crisis_intensity = clamp(phase_load * state.crisis_severity, 0.0, 1.0)
        shock_pct *= 0.72 + 0.55 * state.crisis_severity
        state.crisis_age += 1
        state.crisis_years_left -= 1
        if state.crisis_years_left <= 0:
            state.crisis_total_years = 0
            state.crisis_age = 0
            state.crisis_severity = 0.0
            state.crisis_cooldown_years = rng.randint(
                params.crisis_cooldown_min_years,
                params.crisis_cooldown_max_years,
            )

        return shock_pct, crisis_intensity, boom_intensity, phase

    if state.crisis_cooldown_years > 0:
        state.crisis_cooldown_years -= 1

    if rng.random() < params.deep_crisis_chance_per_year:
        crisis_intensity = rng.uniform(0.70, 1.00)
        shock_pct -= rng.uniform(3.5, 7.5) * params.volatility_scale * crisis_intensity
        phase = "deep_crisis"
    elif rng.random() < params.crisis_chance_per_year:
        crisis_intensity = rng.uniform(0.25, 0.75)
        shock_pct -= rng.uniform(1.0, 3.5) * params.volatility_scale * crisis_intensity
        phase = "stress_slowdown"

    if rng.random() < params.boom_chance_per_year and crisis_intensity < 0.20:
        boom_intensity = rng.uniform(0.25, 1.00)
        shock_pct += rng.uniform(0.8, 2.6) * params.volatility_scale * boom_intensity

    return shock_pct, crisis_intensity, boom_intensity, phase


def classify_regime(
    realized_growth_pct: float,
    output_gap_pct: float,
    financial_stress_index: float,
    crisis_intensity: float,
    boom_intensity: float,
    crisis_phase_name: str = "",
) -> str:
    if crisis_phase_name == "crisis_onset":
        return "crisis_onset"
    if crisis_phase_name == "deep_crisis":
        return "deep_crisis"
    if crisis_phase_name == "crisis_repair":
        return "crisis_repair" if realized_growth_pct < 2.4 else "recovery"
    if crisis_intensity >= 0.70 or realized_growth_pct <= -2.0:
        return "deep_crisis"
    if realized_growth_pct < 0.0:
        return "recession"
    if financial_stress_index >= 65.0 and realized_growth_pct < 1.2:
        return "stress_slowdown"
    if output_gap_pct <= -3.0 and realized_growth_pct >= 2.0:
        return "recovery"
    if boom_intensity >= 0.65 or (output_gap_pct >= 4.0 and realized_growth_pct >= 4.0):
        return "overheating_boom"
    if realized_growth_pct >= 3.5:
        return "high_expansion"
    if realized_growth_pct <= 1.2:
        return "slowdown"
    return "normal_expansion"


def build_macro_event_stub(
    *,
    regime: str,
    crisis_phase_name: str,
    crisis_intensity: float,
    boom_intensity: float,
    shock_component_pct: float,
    output_gap_pct: float,
    financial_stress_index: float,
) -> MacroEventStub:
    severity = clamp(
        max(
            crisis_intensity,
            boom_intensity * 0.70,
            max(0.0, -shock_component_pct) / 7.0,
            max(0.0, financial_stress_index - 35.0) / 60.0,
            max(0.0, -output_gap_pct) / 10.0,
        ),
        0.0,
        1.0,
    )

    if regime == "crisis_onset":
        return MacroEventStub(
            event_type="financial_stress_event",
            event_phase="onset",
            event_severity=severity,
            policy_rate_impulse=0.10 * severity,
            liquidity_impulse=-0.25 * severity,
            credit_stress_impulse=1.00 * severity,
            dollar_pressure_impulse=0.35 * severity,
            energy_price_impulse=-0.25 * severity,
            gdp_lagged_support=-0.35 * severity,
        )

    if regime == "deep_crisis":
        return MacroEventStub(
            event_type="systemic_crisis",
            event_phase="trough",
            event_severity=severity,
            policy_rate_impulse=-0.20 * severity,
            liquidity_impulse=0.20 * severity,
            credit_stress_impulse=1.20 * severity,
            dollar_pressure_impulse=0.50 * severity,
            energy_price_impulse=-0.40 * severity,
            gdp_lagged_support=-0.55 * severity,
        )

    if regime in {"crisis_repair", "recovery"}:
        return MacroEventStub(
            event_type="central_bank_easing_placeholder",
            event_phase="repair",
            event_severity=severity,
            policy_rate_impulse=-0.85 * severity,
            liquidity_impulse=1.10 * severity,
            credit_stress_impulse=-0.70 * severity,
            dollar_pressure_impulse=-0.20 * severity,
            energy_price_impulse=0.15 * severity,
            gdp_lagged_support=0.45 * severity,
        )

    if regime == "stress_slowdown":
        return MacroEventStub(
            event_type="credit_stress_event",
            event_phase=crisis_phase_name or "slowdown",
            event_severity=severity,
            policy_rate_impulse=-0.25 * severity,
            liquidity_impulse=0.30 * severity,
            credit_stress_impulse=0.65 * severity,
            dollar_pressure_impulse=0.20 * severity,
            energy_price_impulse=-0.10 * severity,
            gdp_lagged_support=-0.20 * severity,
        )

    if regime in {"high_expansion", "overheating_boom"}:
        hot_severity = clamp(max(boom_intensity, max(0.0, output_gap_pct) / 8.0), 0.0, 1.0)
        return MacroEventStub(
            event_type="tightening_risk_placeholder",
            event_phase="late_cycle",
            event_severity=hot_severity,
            policy_rate_impulse=0.45 * hot_severity,
            liquidity_impulse=-0.35 * hot_severity,
            credit_stress_impulse=0.15 * hot_severity,
            dollar_pressure_impulse=0.10 * hot_severity,
            energy_price_impulse=0.25 * hot_severity,
            gdp_lagged_support=-0.10 * hot_severity,
        )

    if regime in {"recession", "slowdown"}:
        return MacroEventStub(
            event_type="demand_slowdown_event",
            event_phase="slowdown",
            event_severity=severity,
            policy_rate_impulse=-0.15 * severity,
            liquidity_impulse=0.15 * severity,
            credit_stress_impulse=0.35 * severity,
            dollar_pressure_impulse=0.10 * severity,
            energy_price_impulse=-0.15 * severity,
            gdp_lagged_support=-0.15 * severity,
        )

    return MacroEventStub()


def round_record(record: YearRecord) -> dict[str, Any]:
    result = asdict(record)
    for key, value in list(result.items()):
        if isinstance(value, float):
            result[key] = round(value, 4)
    return result


def simulate_global_gdp(
    seed: int,
    params: GDPParams,
    feedback_by_year_index: Mapping[int, Mapping[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    cycle_specs = draw_cycle_specs(rng, params.volatility_scale)
    state = GDPState(
        potential_index=params.initial_index,
        real_index=params.initial_index,
        output_gap_pct=rng.uniform(-1.2, 1.2),
        financial_stress_index=rng.uniform(8.0, 22.0),
        trend_growth_pct=params.base_trend_growth_pct,
        cycle_memory={name: 0.0 for name in cycle_specs},
    )

    records: list[dict[str, Any]] = []
    previous_real_index = state.real_index

    for t in range(params.years + 1):
        feedback = feedback_for_year(feedback_by_year_index, t)
        if t == 0:
            productivity_wave = 50.0 + 50.0 * sin_wave(t, cycle_specs["long_wave"].period_years, cycle_specs["long_wave"].phase)
            event_stub = MacroEventStub()
            record = YearRecord(
                year_index=t,
                year=params.start_year + t,
                seed=seed,
                param_version=PARAM_VERSION,
                global_gdp_trillion_usd=params.initial_gdp_trillion_usd,
                real_gdp_index=state.real_index,
                potential_gdp_index=state.potential_index,
                realized_growth_pct=state.trend_growth_pct,
                potential_growth_pct=state.trend_growth_pct,
                trend_growth_pct=state.trend_growth_pct,
                cycle_growth_component_pct=0.0,
                long_wave_component_pct=0.0,
                infrastructure_component_pct=0.0,
                investment_component_pct=0.0,
                inventory_component_pct=0.0,
                stochastic_component_pct=0.0,
                shock_component_pct=0.0,
                output_gap_pct=state.output_gap_pct,
                financial_stress_index=state.financial_stress_index,
                productivity_wave_index=productivity_wave,
                crisis_intensity=0.0,
                boom_intensity=0.0,
                regime="initial",
                **asdict(event_stub),
                **feedback,
            )
            records.append(round_record(record))
            continue

        trend_growth = long_run_trend(t, params, rng)
        inventory = cycle_component(t, cycle_specs["inventory"], state, rng)
        investment = cycle_component(t, cycle_specs["investment"], state, rng)
        infrastructure = cycle_component(t, cycle_specs["infrastructure"], state, rng)
        long_wave = cycle_component(t, cycle_specs["long_wave"], state, rng)

        productivity_wave = 50.0 + 50.0 * sin_wave(t, cycle_specs["long_wave"].period_years, cycle_specs["long_wave"].phase)
        potential_growth = trend_growth + 0.35 * long_wave + 0.15 * infrastructure
        potential_growth = clamp(potential_growth, 0.15, 5.50)
        state.potential_index *= 1.0 + potential_growth / 100.0

        cycle_growth = inventory + investment + infrastructure + long_wave
        stochastic = rng.gauss(0.0, 0.32 * params.volatility_scale)
        event_shock, crisis_intensity, boom_intensity, crisis_phase_name = draw_event_shock(
            state,
            params,
            rng,
            cycle_growth,
        )
        state.shock_stock_pct = state.shock_stock_pct * params.shock_decay + event_shock
        shock = state.shock_stock_pct * params.shock_release_speed

        stress_target = 10.0 + max(0.0, -shock) * 11.0 + max(0.0, -cycle_growth) * 5.0
        stress_target += rng.uniform(0.0, 9.0) * crisis_intensity
        stress_target += feedback["feedback_financial_stress_impulse"]
        state.financial_stress_index = clamp(
            smooth(state.financial_stress_index, stress_target, 1.0 - params.financial_stress_decay),
            0.0,
            100.0,
        )

        stress_drag = -0.018 * max(0.0, state.financial_stress_index - 45.0)
        output_gap_target = (
            state.output_gap_pct * params.output_gap_persistence
            + params.output_gap_cycle_loading * cycle_growth
            + params.output_gap_shock_loading * shock
            + stochastic
            + stress_drag
            + feedback["feedback_output_gap_impulse_pct"]
            + 0.45 * feedback["feedback_growth_impulse_pct"]
        )
        state.output_gap_pct = clamp(
            smooth(state.output_gap_pct, output_gap_target, params.output_gap_adjustment_speed),
            -params.output_gap_cap_pct,
            params.output_gap_cap_pct,
        )

        desired_real_index = state.potential_index * math.exp(state.output_gap_pct / 100.0)
        target_growth = pct_change(desired_real_index, previous_real_index)
        target_growth += params.direct_cycle_growth_loading * cycle_growth
        target_growth += params.direct_shock_growth_loading * shock
        target_growth += feedback["feedback_growth_impulse_pct"]
        target_growth = clamp(
            target_growth,
            state.last_realized_growth_pct - params.max_growth_step_pct,
            state.last_realized_growth_pct + params.max_growth_step_pct,
        )
        realized_growth = smooth(
            state.last_realized_growth_pct,
            target_growth,
            params.growth_adjustment_speed,
        )
        realized_growth = clamp(
            realized_growth,
            params.max_negative_growth_pct,
            params.max_positive_growth_pct,
        )
        state.real_index = previous_real_index * (1.0 + realized_growth / 100.0)
        previous_real_index = state.real_index
        state.last_realized_growth_pct = realized_growth

        gdp_trillion = params.initial_gdp_trillion_usd * (state.real_index / params.initial_index)
        regime = classify_regime(
            realized_growth,
            state.output_gap_pct,
            state.financial_stress_index,
            crisis_intensity,
            boom_intensity,
            crisis_phase_name,
        )
        event_stub = build_macro_event_stub(
            regime=regime,
            crisis_phase_name=crisis_phase_name,
            crisis_intensity=crisis_intensity,
            boom_intensity=boom_intensity,
            shock_component_pct=shock,
            output_gap_pct=state.output_gap_pct,
            financial_stress_index=state.financial_stress_index,
        )

        record = YearRecord(
            year_index=t,
            year=params.start_year + t,
            seed=seed,
            param_version=PARAM_VERSION,
            global_gdp_trillion_usd=gdp_trillion,
            real_gdp_index=state.real_index,
            potential_gdp_index=state.potential_index,
            realized_growth_pct=realized_growth,
            potential_growth_pct=potential_growth,
            trend_growth_pct=trend_growth,
            cycle_growth_component_pct=cycle_growth,
            long_wave_component_pct=long_wave,
            infrastructure_component_pct=infrastructure,
            investment_component_pct=investment,
            inventory_component_pct=inventory,
            stochastic_component_pct=stochastic,
            shock_component_pct=shock,
            output_gap_pct=state.output_gap_pct,
            financial_stress_index=state.financial_stress_index,
            productivity_wave_index=productivity_wave,
            crisis_intensity=crisis_intensity,
            boom_intensity=boom_intensity,
            regime=regime,
            **asdict(event_stub),
            **feedback,
        )
        records.append(round_record(record))

    return records


def summarize_seed(records: list[dict[str, Any]]) -> dict[str, Any]:
    data = records[1:] if len(records) > 1 else records
    growth_values = [float(row["realized_growth_pct"]) for row in data]
    final = records[-1]
    recession_years = sum(1 for row in data if float(row["realized_growth_pct"]) < 0.0)
    crisis_years = sum(
        1
        for row in data
        if str(row["regime"]) in {"crisis_onset", "deep_crisis", "crisis_repair", "recession"}
    )
    min_growth_row = min(data, key=lambda row: float(row["realized_growth_pct"])) if data else final
    max_growth_row = max(data, key=lambda row: float(row["realized_growth_pct"])) if data else final
    return {
        "seed": int(final["seed"]),
        "start_year": int(records[0]["year"]),
        "end_year": int(final["year"]),
        "years": len(records) - 1,
        "initial_gdp_trillion_usd": round(float(records[0]["global_gdp_trillion_usd"]), 3),
        "final_gdp_trillion_usd": round(float(final["global_gdp_trillion_usd"]), 3),
        "final_real_gdp_index": round(float(final["real_gdp_index"]), 3),
        "average_growth_pct": round(mean(growth_values), 3) if growth_values else 0.0,
        "min_growth_pct": float(min_growth_row["realized_growth_pct"]),
        "min_growth_year": int(min_growth_row["year"]),
        "max_growth_pct": float(max_growth_row["realized_growth_pct"]),
        "max_growth_year": int(max_growth_row["year"]),
        "recession_years": recession_years,
        "crisis_years": crisis_years,
    }


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def write_viewer_data_js(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(rows, ensure_ascii=False, separators=(",", ":"))
    path.write_text(f"window.GLOBAL_GDP_VIEWER_DATA = {payload};\n", encoding="utf-8")


def build_svg(records_by_seed: dict[int, list[dict[str, Any]]], path: Path) -> None:
    width = 1180
    height = 680
    left = 78
    right = 28
    top = 42
    bottom = 72
    plot_w = width - left - right
    plot_h = height - top - bottom

    all_records = [row for records in records_by_seed.values() for row in records]
    years = [int(row["year"]) for row in all_records]
    values = [float(row["global_gdp_trillion_usd"]) for row in all_records]
    min_year, max_year = min(years), max(years)
    min_value, max_value = min(values), max(values)
    y_pad = (max_value - min_value) * 0.08 if max_value > min_value else 10.0
    min_value = max(0.0, min_value - y_pad)
    max_value += y_pad

    def x_of(year: int) -> float:
        span = max(1, max_year - min_year)
        return left + (year - min_year) / span * plot_w

    def y_of(value: float) -> float:
        span = max(1e-9, max_value - min_value)
        return top + (max_value - value) / span * plot_h

    palette = [
        "#2563eb",
        "#dc2626",
        "#059669",
        "#7c3aed",
        "#ea580c",
        "#0891b2",
        "#be123c",
        "#4d7c0f",
    ]

    lines: list[str] = []
    lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">')
    lines.append('<rect width="100%" height="100%" fill="#fbfbf7"/>')
    lines.append(f'<text x="{left}" y="26" font-family="Arial" font-size="20" fill="#111827">Simulated Global GDP Paths by Seed</text>')
    lines.append(f'<text x="{left}" y="50" font-family="Arial" font-size="12" fill="#4b5563">Long trend + inventory/Juglar/infrastructure/Kondratiev cycles + event shocks</text>')

    for i in range(6):
        y = top + i / 5 * plot_h
        value = max_value - i / 5 * (max_value - min_value)
        lines.append(f'<line x1="{left}" y1="{y:.2f}" x2="{left + plot_w}" y2="{y:.2f}" stroke="#e5e7eb" stroke-width="1"/>')
        lines.append(f'<text x="{left - 10}" y="{y + 4:.2f}" text-anchor="end" font-family="Arial" font-size="11" fill="#6b7280">{value:.0f}</text>')

    for i in range(0, 6):
        x = left + i / 5 * plot_w
        year = round(min_year + i / 5 * (max_year - min_year))
        lines.append(f'<line x1="{x:.2f}" y1="{top}" x2="{x:.2f}" y2="{top + plot_h}" stroke="#f1f5f9" stroke-width="1"/>')
        lines.append(f'<text x="{x:.2f}" y="{top + plot_h + 24}" text-anchor="middle" font-family="Arial" font-size="11" fill="#6b7280">{year}</text>')

    lines.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}" stroke="#111827" stroke-width="1.2"/>')
    lines.append(f'<line x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}" stroke="#111827" stroke-width="1.2"/>')
    lines.append(f'<text x="18" y="{top + plot_h / 2}" transform="rotate(-90 18 {top + plot_h / 2})" text-anchor="middle" font-family="Arial" font-size="12" fill="#374151">Trillion USD, real-index scaled</text>')

    for idx, (seed, records) in enumerate(sorted(records_by_seed.items())):
        color = palette[idx % len(palette)]
        points = " ".join(
            f'{x_of(int(row["year"])):.2f},{y_of(float(row["global_gdp_trillion_usd"])):.2f}'
            for row in records
        )
        lines.append(f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round"/>')
        last = records[-1]
        lines.append(
            f'<text x="{x_of(int(last["year"])) + 6:.2f}" y="{y_of(float(last["global_gdp_trillion_usd"])) + 4:.2f}" '
            f'font-family="Arial" font-size="11" fill="{color}">seed {seed}</text>'
        )

    legend_x = left
    legend_y = height - 24
    for idx, seed in enumerate(sorted(records_by_seed)):
        color = palette[idx % len(palette)]
        x = legend_x + idx * 112
        lines.append(f'<line x1="{x}" y1="{legend_y}" x2="{x + 22}" y2="{legend_y}" stroke="{color}" stroke-width="3"/>')
        lines.append(f'<text x="{x + 28}" y="{legend_y + 4}" font-family="Arial" font-size="12" fill="#374151">seed {seed}</text>')

    lines.append("</svg>")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Simulate annual global GDP paths with long trend, cyclical waves, and large stochastic shocks.",
    )
    parser.add_argument("--years", type=int, default=60, help="Number of simulated years after the initial year.")
    parser.add_argument("--start-year", type=int, default=2025, help="Calendar year for the initial observation.")
    parser.add_argument("--initial-gdp", type=float, default=110.0, help="Initial global GDP in trillion USD.")
    parser.add_argument("--volatility-scale", type=float, default=1.55, help="Scales cycle amplitude and random shocks.")
    parser.add_argument("--seed", type=int, default=None, help="Run one seed only.")
    parser.add_argument("--seeds", type=int, nargs="*", default=None, help="Run an explicit list of seeds.")
    parser.add_argument("--seed-start", type=int, default=1, help="First seed when --seed/--seeds is omitted.")
    parser.add_argument("--seed-count", type=int, default=8, help="Number of seeds when --seed/--seeds is omitted.")
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parents[1] / "output" / "global_gdp")
    parser.add_argument("--no-svg", action="store_true", help="Skip writing the SVG chart.")
    return parser.parse_args()


def resolve_seeds(args: argparse.Namespace) -> list[int]:
    if args.seed is not None:
        return [args.seed]
    if args.seeds:
        return list(dict.fromkeys(args.seeds))
    return list(range(args.seed_start, args.seed_start + args.seed_count))


def main() -> int:
    args = parse_args()
    seeds = resolve_seeds(args)
    if args.years < 1:
        raise SystemExit("--years must be at least 1")
    if args.volatility_scale <= 0:
        raise SystemExit("--volatility-scale must be positive")

    params = GDPParams(
        years=args.years,
        start_year=args.start_year,
        initial_gdp_trillion_usd=args.initial_gdp,
        volatility_scale=args.volatility_scale,
    )

    records_by_seed: dict[int, list[dict[str, Any]]] = {
        seed: simulate_global_gdp(seed, params) for seed in seeds
    }
    all_records = [row for records in records_by_seed.values() for row in records]
    summaries = [summarize_seed(records) for records in records_by_seed.values()]

    args.output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = args.output_dir / "global_gdp_seed_sweep.csv"
    json_path = args.output_dir / "global_gdp_seed_sweep.json"
    viewer_data_path = args.output_dir / "global_gdp_viewer_data.js"
    write_csv(csv_path, all_records, ANNUAL_FIELDS)
    write_json(
        json_path,
        {
            "param_version": PARAM_VERSION,
            "event_interface_version": EVENT_INTERFACE_VERSION,
            "params": asdict(params),
            "seeds": seeds,
            "summary": summaries,
            "model_note": {
                "trend": "Potential GDP grows with a slow-moving long-run trend plus productivity-wave support.",
                "cycles": "Actual GDP swings around potential GDP through inventory, Juglar investment, infrastructure, and long-wave components.",
                "shocks": "Random crisis and boom events move the output gap and financial stress, so different seeds can diverge strongly.",
                "event_interface": "The event_* and *_impulse fields remain placeholders in the standalone GDP CLI. The simulate_global_gdp() function can now accept a lagged feedback_by_year_index path from the macro feedback calibration layer.",
            },
        },
    )
    write_viewer_data_js(viewer_data_path, all_records)

    svg_path = args.output_dir / "global_gdp_curves.svg"
    if not args.no_svg:
        build_svg(records_by_seed, svg_path)

    print(f"Wrote {csv_path}")
    print(f"Wrote {json_path}")
    print(f"Wrote {viewer_data_path}")
    if not args.no_svg:
        print(f"Wrote {svg_path}")
    for summary in summaries:
        print(
            "seed={seed} final_gdp={final_gdp_trillion_usd:.1f}T "
            "avg_growth={average_growth_pct:.2f}% "
            "min_growth={min_growth_pct:.2f}%({min_growth_year}) "
            "recession_years={recession_years}".format(**summary)
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
