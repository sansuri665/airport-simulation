"""Independent energy, wage, materials and other costs; constant 2025 yuan.

The macro engine and bureau volume paths are unchanged. All financial profile
parameters are game placeholders, not observed railway accounts.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from .exposure import Exposure, bureau_specific_states, compute_transport_index, national_factors, validate_profile
from .settlement import apply_hidden_freight, validate_hidden_freight
from .revenue import CURRENT_POLICY, LINEAR_POLICY, unit_yield, validate_policy

VERSION = 'railway-bureau-operations-v0.4'
INPUTS = ('energy', 'wage', 'materials', 'other')
SEGMENTS = ('high_speed', 'conventional', 'station')
PROFILE_PATH = Path(__file__).with_name('northeast12_profiles.json')
NORTH_PROFILE_PATH = Path(__file__).with_name('north10_profiles.json')
NORTHWEST_PROFILE_PATH = Path(__file__).with_name('northwest20_profiles.json')


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
        validate_hidden_freight(p.get('hidden_freight'))
        number(p['reference_v02_wage_price_beta'], 'reference V0.2 wage elasticity', positive=True, high=4.)
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
                if kind == 'wage':
                    number(c['labor_adjustment_theta'], 'labor adjustment theta', high=1.)
            if not math.isclose(sum(c['base_cost_yi'] for c in inputs.values()),
                                p['finance_base_yi'][segment + '_cost'], rel_tol=1e-10, abs_tol=1e-10):
                raise ValueError(f'{p["bureau_id"]}/{segment} input budgets do not sum to segment budget')


def load_profiles(path: Path = PROFILE_PATH) -> list[dict]:
    obj = json.loads(Path(path).read_text(encoding='utf-8'))
    if obj['schema'] not in ('ne12-prototype-v0.3', 'north10-settlement-v0.1', 'nw20-prototype-v0.1'):
        raise ValueError('Unsupported bureau cost schema')
    profiles = obj['bureau_profiles']
    validate_profiles(profiles)
    return profiles


def load_all_profiles() -> list[dict]:
    profiles = load_profiles() + load_profiles(NORTH_PROFILE_PATH) + load_profiles(NORTHWEST_PROFILE_PATH)
    validate_profiles(profiles)
    return profiles


def finance(profile: dict, macro: dict, p_index: float, f_index: float, *,
            wage_peak_index: float, labor_model: str = 'peak', revenue_policy: dict | None = None) -> dict:
    """Compute one year's accounts without state, future information or caps.

    Volumes are already realized business volumes. 'Fixed' means independent
    of current volume, not immune to prices. Congestion affects variable cost
    only and is configured separately for each input. The caller must supply
    the RAW regional wage high observed so far, never a future maximum.
    'v02' is reserved for replaying the original cost-splitting audit.
    """
    qp = number(p_index, 'passenger volume') / 100
    qf = number(f_index, 'freight volume') / 100
    policy = validate_policy(revenue_policy if revenue_policy is not None else
                             (LINEAR_POLICY if labor_model == 'v02' else CURRENT_POLICY))
    uf = unit_yield(qf, 'freight', policy)
    usp, usf = unit_yield(qp, 'station', policy), unit_yield(qf, 'station', policy)
    prices = {'other': 1.}
    if labor_model not in ('peak', 'full_wage', 'v02'):
        raise ValueError('Unsupported labor model')
    wage_peak_index = number(wage_peak_index, 'historical wage peak', low=100.)
    wage_index = number(macro['wage_real_index'], 'wage price', positive=True)
    if labor_model == 'peak' and wage_peak_index < wage_index:
        raise ValueError('Historical wage peak cannot be below current wage')
    for kind in ('energy', 'materials'):
        index = number(macro[kind + '_real_index'], kind + ' price', positive=True)
        prices[kind] = (index / 100) ** profile['exposure'][kind + '_price_beta']
    wage_raw = wage_index / 100
    wage_legacy = wage_raw ** profile['reference_v02_wage_price_beta']
    prices['wage'] = wage_legacy if labor_model == 'v02' else wage_raw

    base = profile['finance_base_yi']
    share = profile['station_revenue_passenger_share']
    result = {
        'passenger_trips_10k': profile['transport']['base_passenger_trips_10k'] * qp,
        'freight_tons_10k': profile['transport']['base_freight_tons_10k'] * qf,
        'passenger_income_yi': base['passenger_revenue'] * qp,
        'freight_income_yi': base['freight_revenue'] * qf * uf,
        'station_income_yi': base['station_revenue'] * (share * qp * usp + (1 - share) * qf * usf),
        'freight_unit_yield_factor': uf,
        'station_passenger_unit_yield_factor': usp,
        'station_freight_unit_yield_factor': usf,
    }
    detail = {}
    wage_units = 0.
    for segment in SEGMENTS:
        detail[segment] = {}
        for kind in INPUTS:
            c = profile['cost_inputs'][segment][kind]
            passenger_load = qp * (1 + c['passenger_congestion'] * max(0., qp - 1) ** 2)
            freight_load = qf * (1 + c['freight_congestion'] * max(0., qf - 1) ** 2)
            workload = c['variable_passenger_share'] * passenger_load + (1 - c['variable_passenger_share']) * freight_load
            adjustment = (wage_peak_index / 100) ** -c['labor_adjustment_theta'] if kind == 'wage' and labor_model == 'peak' else 1.
            unit_cost_factor = prices[kind] * adjustment
            fixed = c['base_cost_yi'] * c['fixed_share'] * unit_cost_factor
            variable = c['base_cost_yi'] * (1 - c['fixed_share']) * workload * unit_cost_factor
            detail[segment][kind] = {
                'fixed_cost_yi': fixed, 'variable_cost_yi': variable,
                'cost_yi': fixed + variable, 'price_factor': prices[kind],
                'workload_factor': workload,
                'cost_adjustment_factor': adjustment, 'unit_cost_factor': unit_cost_factor,
            }
            if kind == 'wage':
                workload_units = c['fixed_share'] + (1 - c['fixed_share']) * workload
                wage_units += c['base_cost_yi'] * workload_units
                detail[segment][kind]['labor_retention_index'] = 100 * adjustment
                detail[segment][kind]['equivalent_staff_index'] = 100 * workload_units * adjustment
        result[segment + '_cost_yi'] = sum(c['cost_yi'] for c in detail[segment].values())
    for kind in INPUTS:
        result[kind + '_cost_yi'] = sum(detail[s][kind]['cost_yi'] for s in SEGMENTS)
    for output, key in [('fixed_operating_cost_yi', 'fixed_cost_yi'), ('volume_operating_cost_yi', 'variable_cost_yi')]:
        result[output] = sum(c[key] for inputs in detail.values() for c in inputs.values())
    result['revenue_yi'] = sum(result[k + '_income_yi'] for k in ('passenger', 'freight', 'station'))
    result['cost_yi'] = sum(result[s + '_cost_yi'] for s in SEGMENTS)
    result['operating_surplus_yi'] = result['revenue_yi'] - result['cost_yi']
    result['electricity_price_yuan_kwh'] = .75 * prices['energy']
    result['wage_reference_yuan_per_year'] = 120000 * wage_raw
    result['materials_basket_real_index'] = 100 * prices['materials']
    result['regional_wage_index'] = wage_index
    result['historical_wage_peak_index'] = wage_peak_index
    result['v02_wage_cost_yi'] = wage_units * wage_legacy
    result['full_wage_cost_yi'] = wage_units * wage_raw
    for name in ('v02', 'full'):
        result[name + '_cost_yi'] = result['cost_yi'] - result['wage_cost_yi'] + result[name + '_wage_cost_yi']
        result[name + '_operating_surplus_yi'] = result['revenue_yi'] - result[name + '_cost_yi']
    for key, value in result.items():
        if not math.isfinite(value):
            raise ValueError(f'Nonfinite calculated account: {key}')
    result['cost_breakdown'] = detail
    return result


def simulate_bureaus(macro_result: dict, profiles: list[dict] | None = None, *, labor_model: str = 'peak',
                     revenue_policy: dict | None = None) -> list[dict]:
    """Run against the existing macro engine's INTERNAL trend/cycle rows.

    This is a research backend, not a game-facing future-data API.
    """
    profiles = load_profiles() if profiles is None else profiles
    validate_profiles(profiles)
    policy = revenue_policy if revenue_policy is not None else (LINEAR_POLICY if labor_model == 'v02' else CURRENT_POLICY)
    validate_policy(policy)
    source = {}
    for row in macro_result['rows']:
        source.setdefault(row['year_index'], {})[row['region_id']] = row
    last = max(source)
    if set(source) != set(range(last + 1)):
        raise ValueError('Expected continuous annual macro history starting at zero')
    seed = macro_result['metadata']['seed']
    paths = {p['bureau_id']: bureau_specific_states(profile_exposure(p), seed, last) for p in profiles}
    result = []
    wage_peaks = {}
    for t in range(last + 1):
        regions = source[t]
        for rid, regional in regions.items():
            wage_peaks[rid] = max(wage_peaks.get(rid, 100.), number(regional['wage_real_index'], 'wage price', positive=True))
        national = national_factors(regions)
        for p in profiles:
            volumes = compute_transport_index(profile_exposure(p), regions[p['region_id']], national, paths[p['bureau_id']][t])
            accounts = finance(p, regions[p['region_id']], volumes['passenger_index'], volumes['freight_index'],
                               wage_peak_index=wage_peaks[p['region_id']], labor_model=labor_model, revenue_policy=policy)
            row = {
                'seed': seed, 'year_index': t, 'year': macro_result['metadata']['base_year'] + t,
                'bureau_id': p['bureau_id'], 'bureau_name': p['name'],
                'model_version': 'railway-bureau-operations-v0.2' if labor_model == 'v02' else VERSION,
                'macro_scenario': macro_result.get('scenario', {}).get('name', ''),
                **volumes, **accounts,
            }
            result.append(apply_hidden_freight(row, p, revenue_policy=policy))
    return result
