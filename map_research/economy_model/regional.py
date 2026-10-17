"""Persistent regional game paths. Weights are design assumptions, not forecasts."""
from __future__ import annotations

import json
from pathlib import Path

from .simulate import stream

PRESETS = json.loads(Path(__file__).with_name('regional_profiles.json').read_text(encoding='utf-8'))
FIELDS = ('passenger', 'freight', 'wage', 'activity', 'energy', 'materials')


def build_regional_paths(seed: int, regions: list[dict], *, growth: float, wage: float) -> dict:
    """Always plan 60 years; separate RNG streams preserve prefix and region order."""
    paths = {}
    for region in sorted(regions, key=lambda item: item['id']):
        rid = region['id']
        selector = stream(seed, 'regional-path-selection-v04:' + rid)
        parameters = stream(seed, 'regional-path-parameters-v04:' + rid)
        durations = stream(seed, 'regional-path-durations-v04:' + rid)
        current = dict(passenger=region['passenger_initial_trend'],
                       freight=region['freight_initial_trend'], wage=region['wage_initial_trend'],
                       activity=0., energy=0., materials=0.)
        path = [{'name': '基期', **current}]
        state_id, remaining, age = None, 0, 0
        for year in range(1, 61):
            if remaining == 0:
                previous = state_id
                weights = dict(PRESETS['regions'][rid])
                for key in weights:
                    weights[key] *= PRESETS['transitions'].get(previous, {}).get(key, 1.)
                    if key == previous:
                        weights[key] *= PRESETS['repeat_weight']
                point = selector.random() * sum(weights.values())
                for key, weight in weights.items():
                    point -= weight
                    if point < 0:
                        state_id = key
                        break
                state = PRESETS['states'][state_id]
                target = {key: parameters.uniform(*state[key]) for key in FIELDS[:3]}
                target.update({key: state[key] for key in FIELDS[3:]})
                # National scenario tilts local trends without fixing their sign.
                target['passenger'] += .008 * (growth - 1.)
                target['freight'] += .008 * (growth - 1.)
                target['wage'] += .004 * (wage - 1.)
                remaining = durations.randint(*PRESETS['duration_years'])
                age = 0
            age += 1
            for key in FIELDS:
                current[key] += PRESETS['adjustment'] * (target[key] - current[key])
            label = ('转向' if previous is not None and previous != state_id and age <= 3 else '') + state['name']
            path.append({'name': label, **current})
            remaining -= 1
        paths[rid] = path
    return paths
