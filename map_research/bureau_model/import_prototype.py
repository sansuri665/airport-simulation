"""Migrate the reviewed prototype's JSON; never execute code from the archive.

Run from map_research:
    py -m bureau_model.import_prototype northeast12_bureau_prototype_v01.zip
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import zipfile

INPUTS = ('energy', 'wage', 'materials', 'other')
LABOR_THETA = {'high_speed': .35, 'conventional': .22, 'station': .18}
PREFERRED_FIXED = {
    'high_speed': (.20, .85, .55, .74),
    'conventional': (.25, .85, .50, .788),
    'station': (.65, .90, .55, .528),
}


def calibrated_fixed_shares(weights: dict, target: float, preferred: tuple) -> dict:
    """A common log-odds offset preserves rankings and the old fixed budget.

    Avoid solving solely for 'other', which would exceed 100% for some bureaus.
    """
    if target in (0., 1.):
        return dict.fromkeys(INPUTS, target)
    logits = [math.log(x / (1 - x)) for x in preferred]
    low, high = -50., 50.
    for _ in range(100):
        offset = (low + high) / 2
        shares = [1 / (1 + math.exp(-(x + offset))) for x in logits]
        if sum(weights[k] * f for k, f in zip(INPUTS, shares)) < target:
            low = offset
        else:
            high = offset
    return dict(zip(INPUTS, shares))


def read_prototype(path: Path) -> dict:
    with zipfile.ZipFile(path) as archive:
        matches = [n for n in archive.namelist() if n.endswith('/data/northeast12_profiles.json')]
        if len(matches) != 1:
            raise ValueError('Expected one prototype profile file')
        return json.loads(archive.read(matches[0]).decode('utf-8-sig'))


def migrate(original: dict) -> dict:
    data = copy.deepcopy(original)
    data['schema'] = 'ne12-prototype-v0.3'
    data['cost_model'] = 'independent-input-peak-wage-adjustment-v0.3'
    data['labor_adjustment'] = {'peak': 'running_max_raw_regional_wage_at_least_100',
                                'theta_by_segment': LABOR_THETA,
                                'reference_beta': 'reference_v02_wage_price_beta is used for audit only'}
    data['fixed_share_calibration'] = 'common_log_odds_shift_preserving_each_segment_fixed_budget'
    for profile in data['bureau_profiles']:
        profile['reference_v02_wage_price_beta'] = profile['exposure'].pop('wage_price_beta')
        profile['cost_inputs'] = {}
        for segment, preferred in PREFERRED_FIXED.items():
            weights = profile['cost_mix_by_segment'][segment]
            fixed = calibrated_fixed_shares(weights, profile['cost_fixed_share'][segment], preferred)
            base = profile['finance_base_yi'][segment + '_cost']
            profile['cost_inputs'][segment] = {
                kind: {
                    'base_cost_yi': base * weights[kind],
                    'fixed_share': fixed[kind],
                    'variable_passenger_share': profile['variable_passenger_share'][segment],
                    'passenger_congestion': profile['congestion_surcharge']['passenger'] if kind in ('energy', 'materials') else 0.,
                    'freight_congestion': profile['congestion_surcharge']['freight'] if kind in ('energy', 'materials') else 0.,
                }
                for kind in INPUTS
            }
            profile['cost_inputs'][segment]['wage']['labor_adjustment_theta'] = LABOR_THETA[segment]
        for key in ('cost_fixed_share', 'cost_mix_by_segment', 'variable_passenger_share', 'congestion_surcharge'):
            del profile[key]
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    args = parser.parse_args()
    data = migrate(read_prototype(args.archive))
    data['source_archive_sha256'] = hashlib.sha256(args.archive.read_bytes()).hexdigest()
    output = Path(__file__).with_name('northeast12_profiles.json')
    output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Wrote {len(data["bureau_profiles"])} profiles to {output}')


if __name__ == '__main__':
    main()
