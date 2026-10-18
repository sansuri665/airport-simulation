"""Compare independent input costs with the original aggregate formula.

Run from map_research: py -m bureau_model.audit_costs
The archive is read as data only. Audit seeds 0..95 plus two demonstration seeds.
"""
from __future__ import annotations

import collections
import copy
import csv
import io
import json
from pathlib import Path
import statistics
import zipfile

from economy_model.scenarios import simulate_scenario
from .import_prototype import read_prototype
from .operations import INPUTS, SEGMENTS, finance as current_finance, load_profiles, simulate_bureaus as current_simulate

VERSION = 'railway-bureau-operations-v0.2'


def finance(profile, macro, p_index, f_index):
    return current_finance(profile, macro, p_index, f_index,
                           wage_peak_index=max(100., macro['wage_real_index']), labor_model='v02')


def simulate_bureaus(macro, profiles):
    return current_simulate(macro, profiles, labor_model='v02')

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / 'northeast12_bureau_prototype_v01.zip'
PRICES = {'energy_real_index': 100., 'wage_real_index': 100., 'materials_real_index': 100.}


def legacy_cost(profile: dict, macro: dict, p_index: float, f_index: float) -> float:
    """Original v0.1 formula, retained ONLY as an audit comparator."""
    qp, qf = p_index / 100, f_index / 100
    prices = {k: (macro[k + '_real_index'] / 100) ** profile['exposure'][k + '_price_beta'] for k in INPUTS[:-1]}
    prices['other'] = 1.
    congestion = profile['congestion_surcharge']
    lp = qp * (1 + congestion['passenger'] * max(0., qp - 1) ** 2)
    lf = qf * (1 + congestion['freight'] * max(0., qf - 1) ** 2)
    total = 0.
    for s in SEGMENTS:
        fixed = profile['cost_fixed_share'][s]
        passenger = profile['variable_passenger_share'][s]
        price = sum(prices[k] * v for k, v in profile['cost_mix_by_segment'][s].items())
        total += profile['finance_base_yi'][s + '_cost'] * (fixed + (1 - fixed) * (passenger * lp + (1 - passenger) * lf)) * price
    return total


def main():
    profiles = load_profiles()
    for p in profiles: p.pop('hidden_freight', None)
    old = {p['bureau_id']: p for p in read_prototype(ARCHIVE)['bureau_profiles']}
    split_only = {p['bureau_id']: copy.deepcopy(p) for p in profiles}
    for bid, p in split_only.items():
        for inputs in p['cost_inputs'].values():
            for c in inputs.values():
                c['passenger_congestion'] = old[bid]['congestion_surcharge']['passenger']
                c['freight_congestion'] = old[bid]['congestion_surcharge']['freight']
    seeds = list(range(96)) + [20261014, 5767783356797806]
    # Check migration against the supplied annual data without executing archived code.
    with zipfile.ZipFile(ARCHIVE) as archive:
        name = next(n for n in archive.namelist() if n.endswith('/reports/annual_8seed_12bureau.csv'))
        reference = {(int(r['seed']), int(r['year_index']), r['bureau_id']): r
                     for r in csv.DictReader(io.StringIO(archive.read(name).decode('utf-8-sig')))}
    summary = collections.defaultdict(list)
    max_volume_error = max_old_cost_error = max_balance_error = max_baseline_error = max_fixed_budget_error = 0.
    for p in profiles:
        r = finance(p, PRICES, 100, 100)
        for s in SEGMENTS:
            max_baseline_error = max(max_baseline_error, abs(r[s + '_cost_yi'] - p['finance_base_yi'][s + '_cost']))
            expected = old[p['bureau_id']]['cost_fixed_share'][s] * p['finance_base_yi'][s + '_cost']
            actual = sum(c['fixed_cost_yi'] for c in r['cost_breakdown'][s].values())
            max_fixed_budget_error = max(max_fixed_budget_error, abs(actual - expected))
    matched = 0
    sample_rows = []
    for seed in seeds:
        macro = simulate_scenario(seed=seed)
        regional = {(r['year_index'], r['region_id']): r for r in macro['rows']}
        rows = simulate_bureaus(macro, profiles)
        groups = collections.defaultdict(list)
        for row in rows:
            groups[row['bureau_id']].append(row)
            source = regional[row['year_index'], 'northeast']
            before_cost = legacy_cost(old[row['bureau_id']], source, row['passenger_index'], row['freight_index'])
            row['old_cost_yi'] = before_cost
            row['old_operating_surplus_yi'] = row['revenue_yi'] - before_cost
            row['split_only_operating_surplus_yi'] = row['revenue_yi'] - finance(split_only[row['bureau_id']], source, row['passenger_index'], row['freight_index'])['cost_yi']
            max_balance_error = max(max_balance_error,
                abs(row['cost_yi'] - sum(row[k + '_cost_yi'] for k in INPUTS)),
                abs(row['cost_yi'] - row['fixed_operating_cost_yi'] - row['volume_operating_cost_yi']))
            ref = reference.get((seed, row['year_index'], row['bureau_id']))
            if ref:
                matched += 1
                for key in ('passenger_index', 'freight_index'):
                    max_volume_error = max(max_volume_error, abs(row[key] - float(ref[key])))
                max_old_cost_error = max(max_old_cost_error, abs(before_cost - float(ref['cost_yi'])))
            if seed in seeds[-2:] and row['year'] in (2025, 2035, 2055, 2085):
                sample_rows.append(row)
        if seed < 96:
            for bid, rs in groups.items():
                summary[bid].append({
                    'seed': seed,
                    'old_end_surplus': rs[-1]['old_operating_surplus_yi'],
                    'new_end_surplus': rs[-1]['operating_surplus_yi'],
                    'split_only_end_surplus': rs[-1]['split_only_operating_surplus_yi'],
                    'old_cumulative_60': sum(r['old_operating_surplus_yi'] for r in rs[1:]),
                    'new_cumulative_60': sum(r['operating_surplus_yi'] for r in rs[1:]),
                })
        if seed < 96 and (seed + 1) % 32 == 0:
            print(f'Audited {seed + 1}/96 distribution seeds', flush=True)
    if (matched != 5856 or max_volume_error > 1e-7 or max_old_cost_error > 1e-7
            or max_balance_error > 1e-8 or max_baseline_error > 1e-8 or max_fixed_budget_error > 1e-8):
        raise AssertionError('Prototype comparison/account reconciliation failed')
    distribution = []
    for p in profiles:
        rs = summary[p['bureau_id']]
        rec = {'bureau_id': p['bureau_id'], 'name': p['name']}
        rec['split_only_end_surplus_median_yi'] = statistics.median(r['split_only_end_surplus'] for r in rs)
        for model in ('old', 'new'):
            rec[model + '_end_surplus_median_yi'] = statistics.median(r[model + '_end_surplus'] for r in rs)
            rec[model + '_fraction_end_loss'] = sum(r[model + '_end_surplus'] < 0 for r in rs) / len(rs)
            rec[model + '_cumulative_60_median_yi'] = statistics.median(r[model + '_cumulative_60'] for r in rs)
        distribution.append(rec)
    p = profiles[0]
    scenarios = [('base', 100, 100, PRICES), ('volume_80', 80, 80, PRICES),
                 ('volume_50', 50, 50, PRICES), ('zero_volume', 0, 0, PRICES),
                 ('energy_150', 100, 100, {**PRICES, 'energy_real_index': 150}),
                 ('volume_80_energy_150', 80, 80, {**PRICES, 'energy_real_index': 150}),
                 ('volume_200', 200, 200, PRICES)]
    sensitivity = []
    for name, qp, qf, price in scenarios:
        result = finance(p, price, qp, qf)
        result['case'] = name
        result['old_cost_yi'] = legacy_cost(old[p['bureau_id']], price, qp, qf)
        result['old_operating_surplus_yi'] = result['revenue_yi'] - result['old_cost_yi']
        sensitivity.append(result)
    report = {
        'model_version': VERSION, 'currency': '100_million_constant_2025_CNY',
        'seed_count_distribution': 96, 'additional_demonstration_seeds': seeds[-2:],
        'years': [2025, 2085], 'cumulative_years': '2026..2085; base year excluded',
        'prototype_records_matched': matched, 'max_volume_difference': max_volume_error,
        'max_legacy_cost_difference': max_old_cost_error, 'max_account_balance_error': max_balance_error,
        'max_baseline_cost_difference': max_baseline_error, 'max_fixed_budget_difference': max_fixed_budget_error,
        'split_only_definition': 'independent input fixed shares with original congestion on all inputs; final new model applies congestion to energy/materials only',
        'distribution': distribution, 'jiamusi_sensitivity': sensitivity,
        'demonstration_checkpoints': sample_rows,
    }
    output = Path(__file__).with_name('reports')
    output.mkdir(exist_ok=True)
    (output / 'cost_comparison_v02.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    with (output / 'cost_comparison_v02.csv').open('w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=list(distribution[0]))
        writer.writeheader()
        writer.writerows(distribution)
    print(json.dumps({'verification': {k: report[k] for k in ('prototype_records_matched', 'max_volume_difference', 'max_legacy_cost_difference', 'max_account_balance_error')},
                      'distribution': distribution,
                      'jiamusi_sensitivity': [{k: r[k] for k in ('case', 'old_cost_yi', 'cost_yi', 'operating_surplus_yi', 'energy_cost_yi', 'wage_cost_yi')} for r in sensitivity]}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
