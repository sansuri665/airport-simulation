"""Paired 96-seed calibration: independent receipts and bounded unit yields.

Run from map_research: py -3 -m bureau_model.audit_v04
Historical V0.2/V0.3 reports are never overwritten.
"""
import collections
import argparse
import copy
import csv
import json
from pathlib import Path
import statistics

from economy_model.scenarios import simulate_scenario
from .operations import VERSION, load_all_profiles, simulate_bureaus
from .revenue import CURRENT_POLICY, LINEAR_POLICY, config_hash
from .settlement import VERSION as SETTLEMENT_VERSION

OUT = Path(__file__).with_name('reports')
MODES = {'legacy_v03': '调整前', 'independent_only': '只增加东北结算',
         'elasticity_only': '只加入收益弹性', 'combined_v04': '当前合并方案'}
DEMO = (0, 1, 2, 7, 9, 13, 20261014, 5767783356797806)


def percentile(values, fraction):
    values = sorted(values)
    at = (len(values)-1)*fraction
    lo = int(at)
    return values[lo] + (values[min(lo+1, len(values)-1)]-values[lo])*(at-lo)


def summary(records):
    vals = [r['end_surplus_yi'] for r in records]
    return {'end_surplus_median_yi': statistics.median(vals),
            'end_surplus_p10_yi': percentile(vals, .1), 'end_surplus_p90_yi': percentile(vals, .9),
            'end_loss_fraction': sum(v < 0 for v in vals)/len(vals),
            'end_wage_cost_yi_median': statistics.median(r['end_wage_cost_yi'] for r in records),
            'end_net_receipts_median_yi': statistics.median(r['end_net_receipts_yi'] for r in records),
            'cumulative_surplus_median_yi': statistics.median(r['cumulative_surplus_yi'] for r in records),
            'loss_years_median': statistics.median(r['loss_years'] for r in records)}


def write_csv(name, rows):
    with (OUT/name).open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument('--three-north', action='store_true', help='Replay original 42 bureaus; write separate three_north reports')
    scope.add_argument('--five-regions', action='store_true', help='Replay original 62 bureaus; write separate five_region reports')
    scope.add_argument('--all-configured', action='store_true', help='Replay all 100 active bureaus; write separate national reports')
    args = parser.parse_args()
    included = {'northeast', 'north', 'northwest'} if args.three_north else {'northeast','north'}
    if args.five_regions: included.update(('northwest','southwest','south'))
    profiles = [p for p in load_all_profiles() if args.all_configured or p['region_id'] in included]
    count = len(profiles)
    region_ids = tuple(dict.fromkeys(p['region_id'] for p in profiles)) + ('all',)
    prefix = ('national_revenue' if args.all_configured else 'five_region_revenue' if args.five_regions
              else 'three_north_revenue' if args.three_north else 'revenue')
    old_profiles = copy.deepcopy(profiles)
    for p in old_profiles:
        if p['region_id'] == 'northeast': p.pop('hidden_freight', None)
    samples, annual, attribution, base = [], [], [], {}
    max_balance = max_unchanged = 0.
    annual_count = 0
    for seed in list(range(96)) + list(DEMO[-2:]):
        macro = simulate_scenario(seed=seed)
        scenarios = {}
        for mode in MODES:
            ps = profiles if mode in ('independent_only', 'combined_v04') else old_profiles
            policy = CURRENT_POLICY if mode in ('elasticity_only', 'combined_v04') else LINEAR_POLICY
            scenarios[mode] = simulate_bureaus(macro, ps, revenue_policy=policy)
        reference = scenarios['legacy_v03']
        for mode, rows in scenarios.items():
            groups = collections.defaultdict(list)
            for before, r, p in zip(reference, rows, profiles * 61):
                annual_count += 1
                groups[r['bureau_id']].append(r)
                for key in ('passenger_index', 'freight_index', 'passenger_trips_10k', 'ordinary_freight_tons_10k',
                            'cost_yi', 'wage_cost_yi', 'energy_cost_yi', 'materials_cost_yi', 'other_cost_yi',
                            'fixed_operating_cost_yi', 'volume_operating_cost_yi'):
                    max_unchanged = max(max_unchanged, abs(r[key]-before[key]))
                if r['cost_breakdown'] != before['cost_breakdown']: raise AssertionError('Costs changed')
                residuals = [r['revenue_yi']-r['cost_yi']-r['operating_surplus_yi'],
                             r['freight_income_yi']-r['ordinary_freight_income_yi']-r['hidden_freight_income_yi'],
                             r['revenue_yi']-sum(r[k+'_income_yi'] for k in ('passenger', 'freight', 'station')),
                             r['operating_surplus_yi']-r['core_operating_surplus_yi']-r['hidden_freight_income_yi']]
                for name in ('v02', 'full'):
                    residuals.append(r['operating_surplus_yi']-r[name+'_operating_surplus_yi']-
                                     (r[name+'_wage_cost_yi']-r['wage_cost_yi']))
                rec = p.get('hidden_freight')
                if rec:
                    residuals.append(r['hidden_equivalent_freight_tons_10k']*rec['accounting_yield_yuan_per_ton']/10000-r['hidden_freight_income_yi'])
                max_balance = max(max_balance, *(abs(v) for v in residuals))
                if r['freight_tons_10k'] != r['ordinary_freight_tons_10k']: raise AssertionError('Physical tonnes contaminated')
                # Other regions' two Northeast-only comparison modes are exact
                # duplicates; store their two distinct paths in the new export.
                if seed in DEMO and (not args.all_configured or p['region_id'] in ('northeast','north')
                                     or mode in ('legacy_v03','combined_v04')):
                    keys = ('seed', 'year', 'bureau_id', 'bureau_name', 'passenger_index', 'freight_index',
                            'passenger_trips_10k', 'ordinary_freight_tons_10k', 'hidden_equivalent_freight_tons_10k',
                            'passenger_income_yi', 'ordinary_freight_income_yi', 'hidden_freight_income_yi', 'freight_income_yi',
                            'station_income_yi', 'revenue_yi', 'cost_yi', 'wage_cost_yi', 'operating_surplus_yi',
                            'freight_unit_yield_factor', 'station_passenger_unit_yield_factor', 'station_freight_unit_yield_factor',
                            'settlement_unit_yield_factor')
                    annual.append({'mode': mode, **{k:r[k] for k in keys}})
            if seed == 0:
                base[mode] = {rid: sum(r['operating_surplus_yi'] for r, p in zip(rows[:count], profiles)
                                     if rid == 'all' or p['region_id'] == rid) for rid in region_ids}
            if seed >= 96: continue
            for p in profiles:
                history = groups[p['bureau_id']][1:]; end = history[-1]
                samples.append({'seed': seed, 'mode': mode, 'bureau_id': p['bureau_id'], 'name':p['name'],
                                'macro_scenario_id':macro['scenario']['id'], 'macro_scenario_name':macro['scenario']['name'],
                                'region_id':p['region_id'], 'end_surplus_yi':end['operating_surplus_yi'],
                                'end_wage_cost_yi':end['wage_cost_yi'], 'end_net_receipts_yi':end['hidden_freight_income_yi'],
                                'cumulative_surplus_yi':sum(r['operating_surplus_yi'] for r in history),
                                'loss_years':sum(r['operating_surplus_yi']<0 for r in history)})
        if seed < 96:
            for mode in MODES:
                for rid in region_ids:
                    delta = {'ordinary_freight_yield_yi': 0., 'station_yield_yi':0., 'net_receipts_change_yi':0., 'surplus_change_yi':0.}
                    for before, after, p in zip(reference[-count:], scenarios[mode][-count:], profiles):
                        if rid != 'all' and p['region_id'] != rid: continue
                        for field, key in [('ordinary_freight_income_yi','ordinary_freight_yield_yi'),
                                           ('station_income_yi','station_yield_yi'),('hidden_freight_income_yi','net_receipts_change_yi'),
                                           ('operating_surplus_yi','surplus_change_yi')]:
                            delta[key] += after[field]-before[field]
                    max_balance = max(max_balance, abs(delta['surplus_change_yi']-sum(delta[k] for k in
                                      ('ordinary_freight_yield_yi','station_yield_yi','net_receipts_change_yi'))))
                    attribution.append({'seed':seed,'mode':mode,'region_id':rid,**delta})
        if seed < 96 and (seed+1)%16 == 0: print(f'Paired replay {seed+1}/96', flush=True)
    if max_balance > 1e-8 or max_unchanged != 0: raise AssertionError('Accounting / unchanged-path check failed')
    bureaus = []
    for p in profiles:
        bs = [r for r in samples if r['bureau_id'] == p['bureau_id']]
        bureaus.append({'bureau_id':p['bureau_id'], 'name':p['name'], 'region_id':p['region_id'],
                        'base_net_yi':p['hidden_freight']['base_net_receipts_yi']*p['hidden_freight']['settlement_scale'],
                        'scenarios':{mode:summary([r for r in bs if r['mode']==mode]) for mode in MODES}})
    regions = {}
    for rid in region_ids:
        regions[rid] = {}
        for mode in MODES:
            rs = [r for r in samples if r['mode']==mode and (rid=='all' or r['region_id']==rid)]
            totals = []
            for seed in range(96):
                sr = [r for r in rs if r['seed']==seed]
                totals.append({k:sum(r[k] for r in sr) for k in ('end_surplus_yi','cumulative_surplus_yi','end_wage_cost_yi','end_net_receipts_yi','loss_years')})
            stats = summary(totals)
            stats['pooled_end_loss_fraction'] = sum(r['end_surplus_yi']<0 for r in rs)/len(rs)
            regions[rid][mode] = stats
    # Existing regions must retain all four 96-seed comparison outcomes.
    preserved_error = 0.
    preserved_count = 0
    if args.three_north or args.five_regions or args.all_configured:
        previous = ('five_region_revenue_samples_96seeds_v04.csv' if args.all_configured else
                    'three_north_revenue_samples_96seeds_v04.csv' if args.five_regions else 'revenue_samples_96seeds_v04.csv')
        with (OUT/previous).open(encoding='utf-8-sig', newline='') as f:
            old = {(int(r['seed']),r['mode'],r['bureau_id']):r for r in csv.DictReader(f)}
        preserved_ids = {key[2] for key in old}
        preserved_count = len(preserved_ids)
        for r in samples:
            if r['bureau_id'] not in preserved_ids: continue
            before = old[(r['seed'],r['mode'],r['bureau_id'])]
            for key in ('end_surplus_yi','end_wage_cost_yi','end_net_receipts_yi','cumulative_surplus_yi','loss_years'):
                preserved_error = max(preserved_error, abs(r[key]-float(before[key])))
        if preserved_error > 1e-8: raise AssertionError('Existing bureau outcomes changed')
    scenario_groups = {}
    for rid in region_ids:
        rs = [r for r in samples if r['mode']=='combined_v04' and (rid=='all' or r['region_id']==rid)]
        scenario_groups[rid] = {}
        for sid in sorted({r['macro_scenario_id'] for r in rs}):
            selected = [r for r in rs if r['macro_scenario_id']==sid]
            seeds = sorted({r['seed'] for r in selected})
            totals = [sum(r['end_surplus_yi'] for r in selected if r['seed']==seed) for seed in seeds]
            scenario_groups[rid][sid] = {'name':selected[0]['macro_scenario_name'],'seedCount':len(seeds),
                                        'end_total_surplus_median_yi':statistics.median(totals),
                                        'pooled_end_loss_fraction':sum(r['end_surplus_yi']<0 for r in selected)/len(selected)}
    report = {'modelVersion':VERSION, 'settlementVersion':SETTLEMENT_VERSION, 'configHash':config_hash(),
              'seedCount':96,'seedRange':[0,95], 'endYear':2085,'operatingYears':[2026,2085],
              'policy':CURRENT_POLICY,'modes':MODES,'baselineSurplusYi':base,'bureaus':bureaus,'regions':regions,
              'scenarioGroups':scenario_groups,
              'regionModeLabels': {rid: {'legacy_v03':'候选基值 · 线性收益参考',
                                       'combined_v04':'当前V0.4 · 收益弹性'}
                                   for rid in region_ids if rid not in ('northeast','north','all')},
              'verification':{'annualRecords':annual_count,'maxAccountingErrorYi':max_balance,
                              'maxVolumeOrCostDifference':max_unchanged,'existingBureauCount':preserved_count,
                              'maxExistingSampleDifference':preserved_error,
                              'settlementBasis':'independent_bureau_business'},
              'note':'Independent bureau receipts. New-region references use the same candidate bases and costs with linear yields, not historical models. North retains 90% original base. No pool.'}
    OUT.mkdir(exist_ok=True)
    (OUT/(prefix+'_comparison_v04.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    write_csv(prefix+'_samples_96seeds_v04.csv', samples)
    write_csv(prefix+'_8seed_annual_v04.csv', annual)
    write_csv(prefix+'_attribution_v04.csv', attribution)
    write_csv(prefix+'_summary_v04.csv', [dict(bureau_id=b['bureau_id'],name=b['name'],region_id=b['region_id'],mode=mode,**s)
                                       for b in bureaus for mode,s in b['scenarios'].items()])
    print(json.dumps({'baseline':base,'regions':regions,'verification':report['verification']},ensure_ascii=False,indent=2))


if __name__ == '__main__': main()
