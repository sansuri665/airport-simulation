"""96-seed paired labor calibration: py -3 -m bureau_model.audit_labor.

A = original V0.2 wage beta; B = full raw wage pass-through; C = running-peak
adjustment. Every comparison uses identical macro, traffic and nonlabor costs.
"""
from __future__ import annotations

import collections
import csv
import hashlib
import json
from pathlib import Path
import statistics

from economy_model.scenarios import simulate_scenario
from .operations import PROFILE_PATH, SEGMENTS, VERSION, finance, load_profiles, simulate_bureaus

OUTPUT = Path(__file__).with_name('reports')
GROUPS = {
    'v02': ('v02_operating_surplus_yi', 'v02_wage_cost_yi', 'v02_cost_yi'),
    'full': ('full_operating_surplus_yi', 'full_wage_cost_yi', 'full_cost_yi'),
    'adjusted': ('operating_surplus_yi', 'wage_cost_yi', 'cost_yi'),
}


def main():
    profiles = load_profiles()
    old = json.loads((OUTPUT/'cost_comparison_v02.json').read_text(encoding='utf-8'))
    checkpoints = {(r['seed'],r['year'],r['bureau_id']):r for r in old['demonstration_checkpoints']}
    samples, demonstration = [], []
    max_balance = max_reference = max_nonlabor = max_decomposition = 0.
    checked = 0
    for seed in list(range(96)) + [20261014,5767783356797806]:
        macro = simulate_scenario(seed=seed)
        rows = simulate_bureaus(macro, profiles)
        grouped = collections.defaultdict(list)
        for r in rows:
            grouped[r['bureau_id']].append(r)
            max_balance = max(max_balance, abs(r['cost_yi']-sum(r[s+'_cost_yi'] for s in SEGMENTS)),
                              abs(r['cost_yi']-sum(r[k+'_cost_yi'] for k in ('energy','wage','materials','other'))))
            max_nonlabor = max(max_nonlabor, abs((r['v02_cost_yi']-r['v02_wage_cost_yi'])-(r['cost_yi']-r['wage_cost_yi'])))
            max_decomposition = max(max_decomposition, abs((r['operating_surplus_yi']-r['v02_operating_surplus_yi'])-(r['v02_wage_cost_yi']-r['wage_cost_yi'])))
            ref = checkpoints.get((seed,r['year'],r['bureau_id']))
            if ref:
                checked += 1
                for a,b in [('passenger_index','passenger_index'),('freight_index','freight_index'),
                            ('revenue_yi','revenue_yi'),('v02_wage_cost_yi','wage_cost_yi'),
                            ('v02_operating_surplus_yi','operating_surplus_yi')]:
                    max_reference = max(max_reference, abs(r[a]-ref[b]))
                demonstration.append(r)
        if seed < 96:
            for p in profiles:
                history = grouped[p['bureau_id']][1:]  # 2026..2085
                end = history[-1]
                record = {'seed':seed,'bureau_id':p['bureau_id'],'name':p['name'],
                          'end_passenger_index':end['passenger_index'],'end_freight_index':end['freight_index']}
                for name,(surplus,wage,total) in GROUPS.items():
                    record.update({
                        name+'_end_surplus_yi':end[surplus], name+'_end_wage_cost_yi':end[wage],
                        name+'_end_labor_share':end[wage]/end[total],
                        name+'_loss_years':sum(r[surplus]<0 for r in history),
                        name+'_cumulative_surplus_yi':sum(r[surplus] for r in history),
                        name+'_cumulative_wage_yi':sum(r[wage] for r in history),
                    })
                for s in SEGMENTS:
                    record[s+'_end_labor_retention_index'] = end['cost_breakdown'][s]['wage']['labor_retention_index']
                    record[s+'_end_equivalent_staff_index'] = end['cost_breakdown'][s]['wage']['equivalent_staff_index']
                samples.append(record)
            if (seed+1)%32 == 0: print(f'Audited {seed+1}/96 paired seeds',flush=True)
    distribution = []
    for p in profiles:
        selected = [r for r in samples if r['bureau_id']==p['bureau_id']]
        groups = {}
        for group in GROUPS:
            groups[group] = {
                'end_loss_count':sum(r[group+'_end_surplus_yi']<0 for r in selected),
                'end_loss_fraction':sum(r[group+'_end_surplus_yi']<0 for r in selected)/96,
            }
            for metric in ('end_surplus_yi','end_wage_cost_yi','end_labor_share','loss_years','cumulative_surplus_yi','cumulative_wage_yi'):
                groups[group][metric+'_median'] = statistics.median(r[group+'_'+metric] for r in selected)
        previous = next(r for r in old['distribution'] if r['bureau_id']==p['bureau_id'])
        for key, previous_key in [('end_loss_fraction','new_fraction_end_loss'),('end_surplus_yi_median','new_end_surplus_median_yi'),('cumulative_surplus_yi_median','new_cumulative_60_median_yi')]:
            max_reference = max(max_reference, abs(groups['v02'][key]-previous[previous_key]))
        difference = lambda a,b: statistics.mean(r[a+'_end_wage_cost_yi']-r[b+'_end_wage_cost_yi'] for r in selected)
        distribution.append({'bureau_id':p['bureau_id'],'name':p['name'],'groups':groups,
                             'labor_cost_effect_mean_yi':{'full_minus_v02':difference('full','v02'),
                                                         'adjusted_minus_full':difference('adjusted','full'),
                                                         'adjusted_minus_v02':difference('adjusted','v02')},
                             'diagnostic_medians':{s:{k:statistics.median(r[s+'_end_'+k] for r in selected) for k in ('labor_retention_index','equivalent_staff_index')} for s in SEGMENTS}})
    if checked!=96 or max_reference>1e-8 or max_balance>1e-8 or max_nonlabor>1e-8 or max_decomposition>1e-8:
        raise AssertionError('Paired comparison, historical replay, or accounting checks failed')
    pooled = {}
    for group in GROUPS:
        yearly_totals = [sum(r[group+'_end_wage_cost_yi'] for r in samples if r['seed']==seed) for seed in range(96)]
        pooled[group] = {'end_loss_count':sum(r[group+'_end_surplus_yi']<0 for r in samples),
                         'end_loss_fraction':sum(r[group+'_end_surplus_yi']<0 for r in samples)/len(samples),
                         'twelve_bureau_end_wage_total_median_yi':statistics.median(yearly_totals)}
    reference_prices={'energy_real_index':100.,'wage_real_index':160.,'materials_real_index':100.}
    example = finance(profiles[0],reference_prices,100,100,wage_peak_index=160.)
    report = {
        'modelVersion':VERSION,'bureauConfigHash':hashlib.sha256(PROFILE_PATH.read_bytes()).hexdigest(),
        'seedCount':96,'seedRange':[0,95],'endYear':2085,'operatingYears':[2026,2085],
        'thetaBySegment':{s:profiles[0]['cost_inputs'][s]['wage']['labor_adjustment_theta'] for s in SEGMENTS},
        'groupDefinitions':{'v02':'A: V0.2 wage beta, no peak adjustment','full':'B: raw wage fully transmitted, no peak adjustment','adjusted':'C: raw wage times historical peak raised to minus segment theta'},
        'verification':{'annual_records':96*12*61,'demonstration_checkpoints':checked,'max_v02_reference_difference':max_reference,
                        'max_account_balance_error':max_balance,'max_nonlabor_difference':max_nonlabor,'max_profit_labor_decomposition_error':max_decomposition},
        'pooled':pooled,'bureaus':distribution,'demonstrationCheckpoints':demonstration,
        'jiamusi_wage160_constant_workload':{k:example[k] for k in ('v02_wage_cost_yi','full_wage_cost_yi','wage_cost_yi')},
    }
    OUTPUT.mkdir(exist_ok=True)
    (OUTPUT/'labor_comparison_v03.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    def write_csv(path,records):
        with path.open('w',encoding='utf-8-sig',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(records[0]));writer.writeheader();writer.writerows(records)
    write_csv(OUTPUT/'labor_samples_96seeds_v03.csv',samples)
    summary=[]
    for b in distribution:
        r={'bureau_id':b['bureau_id'],'name':b['name']}
        for g,metrics in b['groups'].items():r.update({g+'_'+k:v for k,v in metrics.items()})
        summary.append(r)
    write_csv(OUTPUT/'labor_comparison_v03.csv',summary)
    print(json.dumps({k:report[k] for k in ('verification','pooled','jiamusi_wage160_constant_workload')},ensure_ascii=False,indent=2))
    print('Bureau | loss A -> C | 2085 median labor A -> C (yi)')
    for b in distribution:
        a,c=b['groups']['v02'],b['groups']['adjusted']
        print(f"{b['name']} | {a['end_loss_fraction']:.1%} -> {c['end_loss_fraction']:.1%} | {a['end_wage_cost_yi_median']:.3f} -> {c['end_wage_cost_yi_median']:.3f}")


if __name__=='__main__': main()
