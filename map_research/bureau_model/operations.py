"""Independent energy, wage, materials and other costs; constant 2025 yuan.

The macro engine and bureau volume paths are unchanged. All financial profile
parameters are game placeholders, not observed railway accounts.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from .exposure import Exposure, bureau_specific_states, compute_transport_index, national_factors, validate_profile

VERSION = 'railway-bureau-operations-v0.2'
INPUTS = ('energy', 'wage', 'materials', 'other')
SEGMENTS = ('high_speed', 'conventional', 'station')
PROFILE_PATH = Path(__file__).with_name('northeast12_profiles.json')


def number(value, label, *, low=0., high=math.inf, positive=False):
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value) or not low <= value <= high
            or (positive and value <= 0)):
        raise ValueError(f'Invalid {label}: {value!r}')
    return value


def profile_exposure(profile: dict) -> Exposure:
    return Exposure(bureau_id=profile['bureau_id'], name=profile['name'],
                    region_id=profile['region_id'], **profile['exposure'])


def validate_profiles(profiles: list[dict]) -> None:
    if not profiles or len({p['bureau_id'] for p in profiles}) != len(profiles):
        raise ValueError('Expected nonempty profiles with unique bureau IDs')
    for p in profiles:
        validate_profile(profile_exposure(p))
        for key, value in p['exposure'].items():
            number(value, key, low=-math.inf)
        for key in ('base_passenger_trips_10k', 'base_freight_tons_10k'):
            number(p['transport'][key], key, positive=True)
        for key, value in p['finance_base_yi'].items():
            number(value, key, positive=True)
        number(p['station_revenue_passenger_share'], 'station revenue weight', high=1.)
        if set(p['cost_inputs']) != set(SEGMENTS):
            raise ValueError('Expected three cost segments')
        for segment in SEGMENTS:
            inputs = p['cost_inputs'][segment]
            if set(inputs) != set(INPUTS):
                raise ValueError('Expected four independent cost inputs')
            for kind, c in inputs.items():
                number(c['base_cost_yi'], f'{segment}/{kind} base cost')
                for key in ('fixed_share', 'variable_passenger_share'):
                    number(c[key], key, high=1.)
                for key in ('passenger_congestion', 'freight_congestion'):
                    number(c[key], key)
            if not math.isclose(sum(c['base_cost_yi'] for c in inputs.values()),
                                p['finance_base_yi'][segment + '_cost'], rel_tol=1e-10, abs_tol=1e-10):
                raise ValueError(f'{p["bureau_id"]}/{segment} input budgets do not sum to segment budget')


def load_profiles(path: Path = PROFILE_PATH) -> list[dict]:
    obj = json.loads(Path(path).read_text(encoding='utf-8'))
    if obj['schema'] != 'ne12-prototype-v0.2':
        raise ValueError('Unsupported bureau cost schema')
    profiles = obj['bureau_profiles']
    validate_profiles(profiles)
    return profiles


def finance(profile: dict, macro: dict, p_index: float, f_index: float) -> dict:
    """Compute one year's accounts without state, future information or caps.

    Volumes are already realized business volumes. 'Fixed' means independent
    of current volume, not immune to prices. Congestion affects variable cost
    only and is configured separately for each input.
    """
    qp = number(p_index, 'passenger volume') / 100
    qf = number(f_index, 'freight volume') / 100
    prices = {'other': 1.}
    for kind in INPUTS[:-1]:
        index = number(macro[kind + '_real_index'], kind + ' price', positive=True)
        prices[kind] = (index / 100) ** profile['exposure'][kind + '_price_beta']

    base = profile['finance_base_yi']
    share = profile['station_revenue_passenger_share']
    result = {
        'passenger_trips_10k': profile['transport']['base_passenger_trips_10k'] * qp,
        'freight_tons_10k': profile['transport']['base_freight_tons_10k'] * qf,
        'passenger_income_yi': base['passenger_revenue'] * qp,
        'freight_income_yi': base['freight_revenue'] * qf,
        'station_income_yi': base['station_revenue'] * (share * qp + (1 - share) * qf),
    }
    detail = {}
    for segment in SEGMENTS:
        detail[segment] = {}
        for kind in INPUTS:
            c = profile['cost_inputs'][segment][kind]
            passenger_load = qp * (1 + c['passenger_congestion'] * max(0., qp - 1) ** 2)
            freight_load = qf * (1 + c['freight_congestion'] * max(0., qf - 1) ** 2)
            workload = c['variable_passenger_share'] * passenger_load + (1 - c['variable_passenger_share']) * freight_load
            fixed = c['base_cost_yi'] * c['fixed_share'] * prices[kind]
            variable = c['base_cost_yi'] * (1 - c['fixed_share']) * workload * prices[kind]
            detail[segment][kind] = {
                'fixed_cost_yi': fixed, 'variable_cost_yi': variable,
                'cost_yi': fixed + variable, 'price_factor': prices[kind],
                'workload_factor': workload,
            }
        result[segment + '_cost_yi'] = sum(c['cost_yi'] for c in detail[segment].values())
    for kind in INPUTS:
        result[kind + '_cost_yi'] = sum(detail[s][kind]['cost_yi'] for s in SEGMENTS)
    for output, key in [('fixed_operating_cost_yi', 'fixed_cost_yi'), ('volume_operating_cost_yi', 'variable_cost_yi')]:
        result[output] = sum(c[key] for inputs in detail.values() for c in inputs.values())
    result['revenue_yi'] = sum(result[k + '_income_yi'] for k in ('passenger', 'freight', 'station'))
    result['cost_yi'] = sum(result[s + '_cost_yi'] for s in SEGMENTS)
    result['operating_surplus_yi'] = result['revenue_yi'] - result['cost_yi']
    result['electricity_price_yuan_kwh'] = .75 * prices['energy']
    result['wage_reference_yuan_per_year'] = 120000 * prices['wage']
    result['materials_basket_real_index'] = 100 * prices['materials']
    for key, value in result.items():
        if not math.isfinite(value):
            raise ValueError(f'Nonfinite calculated account: {key}')
    result['cost_breakdown'] = detail
    return result


def simulate_bureaus(macro_result: dict, profiles: list[dict] | None = None) -> list[dict]:
    """Run against the existing macro engine's INTERNAL trend/cycle rows.

    This is a research backend, not a game-facing future-data API.
    """
    profiles = load_profiles() if profiles is None else profiles
    validate_profiles(profiles)
    source = {}
    for row in macro_result['rows']:
        source.setdefault(row['year_index'], {})[row['region_id']] = row
    last = max(source)
    if set(source) != set(range(last + 1)):
        raise ValueError('Expected continuous annual macro history starting at zero')
    seed = macro_result['metadata']['seed']
    paths = {p['bureau_id']: bureau_specific_states(profile_exposure(p), seed, last) for p in profiles}
    result = []
    for t in range(last + 1):
        regions = source[t]
        national = national_factors(regions)
        for p in profiles:
            volumes = compute_transport_index(profile_exposure(p), regions[p['region_id']], national, paths[p['bureau_id']][t])
            accounts = finance(p, regions[p['region_id']], volumes['passenger_index'], volumes['freight_index'])
            result.append({
                'seed': seed, 'year_index': t, 'year': macro_result['metadata']['base_year'] + t,
                'bureau_id': p['bureau_id'], 'bureau_name': p['name'], 'model_version': VERSION,
                'macro_scenario': macro_result.get('scenario', {}).get('name', ''),
                **volumes, **accounts,
            })
    return result
