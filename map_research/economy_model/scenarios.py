"""Seeded game scenario presets layered on the railway v0.2 engine.

Profile selection, parameter draws, events and macro innovations have separate
random streams. Plans always use the same 60-year design window, preserving
the prefix when a shorter history is requested. Presets are game assumptions.
"""
from __future__ import annotations

import copy
import json
import math
from pathlib import Path

from .simulate import config_hash, load_config, simulate, stream, validate_config
from .regional import PRESETS as REGIONAL_PRESETS, build_regional_paths

VERSION = 'railway-real-macro-v0.5.0'
PRESETS = json.loads(Path(__file__).with_name('scenario_profiles.json').read_text(encoding='utf-8'))


def build_plan(seed: int, config: dict | None = None) -> tuple[dict, dict, dict, dict]:
    if isinstance(seed, bool) or not isinstance(seed, int) or not 0 <= seed <= 9_007_199_254_740_991:
        raise ValueError('Invalid scenario seed')
    cfg = copy.deepcopy(config if config is not None else load_config())
    selector = stream(seed, 'scenario-profile-v03')
    parameter_rng = stream(seed, 'scenario-parameters-v03')
    event_rng = stream(seed, 'scenario-events-v03')
    profiles = PRESETS['profiles']
    point = selector.random() * sum(profile['weight'] for profile in profiles)
    selected = profiles[-1]
    for profile in profiles:
        point -= profile['weight']
        if point < 0:
            selected = profile
            break
    draws = {key: parameter_rng.uniform(*bounds) for key, bounds in selected['ranges'].items()}
    p = cfg['parameters']
    p.update(PRESETS['wage_dynamics'])
    for key, value in draws.items():
        if key in p:
            p[key] = value
    for key, factor in selected['multipliers'].items():
        if key == 'impulse':
            cfg['regime_business_impulse'] = [x * factor for x in cfg['regime_business_impulse']]
        else:
            p[key] *= factor
    cfg['transition_matrix'] = copy.deepcopy(selected['transition_matrix'])
    # Change future growth rates, preserving identical base indices and prices.
    trend = draws['trend_multiplier']
    wage = draws['wage_multiplier']
    for key in ('passenger_terminal_trend', 'freight_terminal_trend'):
        p[key] *= trend
    p['wage_terminal_trend'] *= wage
    for region in sorted(cfg['regions'], key=lambda r: r['id']):
        regional_tilt = parameter_rng.uniform(0.9, 1.1)
        region['passenger_initial_trend'] *= trend * regional_tilt
        region['freight_initial_trend'] *= trend * regional_tilt
        region['wage_initial_trend'] *= wage
    cfg['regional_development_paths'] = build_regional_paths(seed, cfg['regions'], growth=trend, wage=wage)
    cfg['schema_version'] = VERSION
    validate_config(cfg)
    shocks, phases = {}, {}
    episode = selected.get('episode')
    if episode:
        start = event_rng.randint(*episode['start'])
        duration = event_rng.randint(*episode['duration'])
        delay = event_rng.randint(*episode['recovery_delay'])
        recovery_start = start + duration + delay
        recovery_duration = event_rng.randint(*episode['recovery_duration'])
        passenger_loss = -math.log1p(-event_rng.uniform(*episode['passenger_loss']))
        freight_loss = -math.log1p(-event_rng.uniform(*episode['freight_loss']))
        recovery_fraction = event_rng.uniform(*episode['recovery_fraction'])
        # Multi-year losses enter persistent demand trends; recovery is earned
        # gradually, with only partial restitution in the large-crisis preset.
        weights = [math.sin(math.pi * (i + 1) / (duration + 1)) for i in range(duration)]
        total = sum(weights)
        for i, weight in enumerate(weights):
            share = weight / total
            t = start + i
            shocks[t] = {'passenger_log': -passenger_loss * share,
                         'freight_log': -freight_loss * share,
                         'energy_log': -0.045 * weight, 'materials_log': -0.065 * weight,
                         'rate_pp': 0.35 * weight, 'regime_index': 3}
            phases[t] = '危机冲击'
        for t in range(start + duration, recovery_start):
            shocks[t] = {'regime_index': 2}
            phases[t] = '危机余波'
        weights = [math.sin(math.pi * (i + 1) / (recovery_duration + 1)) for i in range(recovery_duration)]
        total = sum(weights)
        for i, weight in enumerate(weights):
            t = recovery_start + i
            shocks[t] = {'passenger_log': passenger_loss * recovery_fraction * weight / total,
                         'freight_log': freight_loss * recovery_fraction * weight / total,
                         'regime_index': 4}
            phases[t] = '逐步修复' if selected['id'] == 'crisis' else '复苏回升'
    scenario = {'id': selected['id'], 'name': selected['name'], 'description': selected['description'],
                'presetVersion': PRESETS['version'],
                'cyclePeriodYears': round(p['cycle_period_years'], 1),
                'cyclePersistence': round(p['cycle_radius'], 3),
                'growthMultiplier': round(trend, 2)}
    return cfg, shocks, phases, scenario


def simulate_scenario(*, seed: int, years: int = 60, config: dict | None = None) -> dict:
    if isinstance(years, bool) or not isinstance(years, int) or not 0 <= years <= 60:
        raise ValueError('Scenario horizon must be within 0..60 years')
    cfg, shocks, phases, scenario = build_plan(seed, config)
    result = simulate(cfg, seed=seed, years=years, shocks={t: shock for t, shock in shocks.items() if t <= years})
    result['metadata']['scenario_config_sha256'] = config_hash({'config': cfg, 'shocks': shocks, 'preset_version': PRESETS['version'], 'regional_presets': REGIONAL_PRESETS})
    result['scenario'] = scenario
    result['phases'] = [{'year': row['calendar_year'],
                         'name': '基期' if row['year_index'] == 0 else phases.get(row['year_index'], row['regime_name'])}
                        for row in result['national_factors']]
    result['regional_phases'] = [{'year': cfg['base_year'] + t,
                                 'regions': {rid: path[t]['name'] for rid, path in cfg['regional_development_paths'].items()}}
                                for t in range(years + 1)]
    return result
