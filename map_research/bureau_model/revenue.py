"""Bounded unit yields. Independent bureau receipts; no shared funding pool."""
import hashlib
import json
import math
from pathlib import Path

POLICY_PATH = Path(__file__).with_name('revenue_policy_v04.json')


def validate_policy(policy):
    for kind in ('freight', 'station'):
        for key in ('exponent', 'floor', 'ceiling'):
            v = policy[kind + '_' + key]
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0:
                raise ValueError('Invalid revenue policy ' + kind + '_' + key)
        if not 0 < policy[kind+'_floor'] <= 1 <= policy[kind+'_ceiling']:
            raise ValueError('Unit yield bounds must contain one')
    if not isinstance(policy['settlement_uses_freight_yield'], bool):
        raise ValueError('Settlement yield flag must be boolean')
    if policy['settlement_basis'] != 'independent_bureau_business':
        raise ValueError('Only independent bureau settlement is supported')
    return policy


def load_policy():
    return validate_policy(json.loads(POLICY_PATH.read_text(encoding='utf-8')))


CURRENT_POLICY = load_policy()
LINEAR_POLICY = {**CURRENT_POLICY, 'version': 'linear-v0.3-reference',
                 'freight_exponent': 0., 'station_exponent': 0.,
                 'settlement_uses_freight_yield': False}


def unit_yield(q, kind, policy):
    if isinstance(q, bool) or not isinstance(q, (float, int)) or not math.isfinite(q) or q < 0:
        raise ValueError('Invalid revenue volume ratio')
    return min(policy[kind+'_ceiling'], max(policy[kind+'_floor'], q ** policy[kind+'_exponent']))


def config_hash():
    """Whole experiment identity, including macro and all active regional profiles."""
    root = POLICY_PATH.parent.parent
    paths = [POLICY_PATH, POLICY_PATH.with_name('northeast12_profiles.json'),
             POLICY_PATH.with_name('north10_profiles.json'), POLICY_PATH.with_name('northwest20_profiles.json'),
             POLICY_PATH.with_name('southwest12_south8_profiles.json'),
             POLICY_PATH.with_name('central11_east14_southeast13_profiles.json')]
    paths += sorted((root/'economy_model').glob('*.json'))
    paths += [POLICY_PATH.with_name(n) for n in ('operations.py', 'settlement.py', 'revenue.py', 'exposure.py')]
    paths += sorted((root/'economy_model').glob('*.py'))
    digest = hashlib.sha256()
    for path in paths:
        digest.update(str(path.relative_to(root)).replace('\\', '/').encode())
        digest.update(b'\0' + path.read_bytes() + b'\0')
    return digest.hexdigest()
