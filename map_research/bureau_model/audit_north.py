"""Replay North ten with the existing macro and operating engine.

py -3 -m bureau_model.audit_north [--archive reviewed-package.zip]
Outputs compare no settlement, 80%, 90% and 100% original net receipts.
"""
import argparse
import collections
import csv
import hashlib
import io
import json
from pathlib import Path
import statistics
import zipfile

from economy_model.scenarios import simulate_scenario
from .operations import NORTH_PROFILE_PATH, VERSION, load_profiles, simulate_bureaus
from .settlement import VERSION as SETTLEMENT_VERSION

OUT = Path(__file__).with_name('reports')
SCALES = {'core': 0., 'scale80': .8, 'scale90': .9, 'scale100': 1.}


def metrics(records, key):
    return {'end_surplus_median_yi': statistics.median(r[key+'_end_surplus_yi'] for r in records),
            'end_loss_count': sum(r[key+'_end_surplus_yi']<0 for r in records),
            'end_loss_fraction': sum(r[key+'_end_surplus_yi']<0 for r in records)/len(records),
            'cumulative_surplus_median_yi':statistics.median(r[key+'_cumulative_surplus_yi'] for r in records),
            'loss_years_median':statistics.median(r[key+'_loss_years'] for r in records)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive',type=Path)
    args=parser.parse_args()
    profiles=load_profiles(NORTH_PROFILE_PATH)
    scales={p['hidden_freight']['settlement_scale'] for p in profiles}
    if len(scales)!=1: raise ValueError('This calibration expects one regional settlement scale')
    scale=scales.pop()
    candidates={**SCALES,'current':scale}
    reference={}; package_summary=[]
    if args.archive:
        with zipfile.ZipFile(args.archive) as z:
            def read(suffix): return z.read(next(n for n in z.namelist() if n.endswith('/'+suffix))).decode('utf-8-sig')
            reference={(int(r['seed']),int(r['year']),r['bureau_id']):r for r in csv.DictReader(io.StringIO(read('outputs/representative_8seed_annual.csv')))}
            package_summary=list(csv.DictReader(io.StringIO(read('outputs/96seed_summary.csv'))))
    samples=[]; checkpoints=[]; annual=[]; matched=0; reference_error=balance_error=0.
    for seed in list(range(96))+[20261014,5767783356797806]:
        macro=simulate_scenario(seed=seed)
        rows=simulate_bureaus(macro,profiles)
        groups=collections.defaultdict(list)
        for r in rows:
            groups[r['bureau_id']].append(r)
            balance_error=max(balance_error,abs(r['revenue_yi']-r['cost_yi']-r['operating_surplus_yi']),
                              abs(r['freight_income_yi']-r['ordinary_freight_income_yi']-r['hidden_freight_income_yi']),
                              abs(r['operating_surplus_yi']-r['core_operating_surplus_yi']-r['hidden_freight_income_yi']))
            if r['freight_tons_10k']!=r['ordinary_freight_tons_10k']: raise AssertionError('Equivalent tonnes contaminated ordinary traffic')
            ref=reference.get((seed,r['year'],r['bureau_id']))
            if ref:
                matched+=1
                for ours,original in [('passenger_index','passenger_index'),('freight_index','freight_index'),('ordinary_freight_tons_10k','ordinary_freight_tons_10k'),
                                      ('ordinary_freight_income_yi','ordinary_freight_income_yi'),('passenger_income_yi','passenger_income_yi'),('station_income_yi','station_income_yi'),
                                      ('cost_yi','cost_yi'),('high_speed_cost_yi','high_speed_cost_yi'),('conventional_cost_yi','conventional_cost_yi'),('station_cost_yi','station_cost_yi'),
                                      ('energy_cost_yi','energy_cost_yi'),('wage_cost_yi','wage_cost_yi'),('materials_cost_yi','materials_cost_yi'),('other_cost_yi','other_cost_yi'),
                                      ('core_operating_surplus_yi','core_operating_surplus_yi'),('unscaled_hidden_freight_income_yi','hidden_freight_income_yi')]:
                    reference_error=max(reference_error,abs(r[ours]-float(ref[original])))
                original_profit=r['core_operating_surplus_yi']+r['unscaled_hidden_freight_income_yi']
                reference_error=max(reference_error,abs(original_profit-float(ref['operating_surplus_yi'])))
            if seed in (0,1,2,7,9,13,20261014,5767783356797806):
                annual.append({k:r[k] for k in ('seed','year','bureau_id','bureau_name','passenger_index','freight_index','passenger_trips_10k',
                    'ordinary_freight_tons_10k','hidden_equivalent_freight_tons_10k','ordinary_freight_income_yi','hidden_freight_income_yi',
                    'freight_income_yi','passenger_income_yi','station_income_yi','revenue_yi','cost_yi','core_operating_surplus_yi','operating_surplus_yi')})
            if seed in (20261014,5767783356797806) and r['year'] in (2025,2035,2055,2085):
                checkpoints.append(annual[-1])
        if seed<96:
            for p in profiles:
                history=groups[p['bureau_id']][1:]; end=history[-1]
                item={'seed':seed,'bureau_id':p['bureau_id'],'name':p['name'],
                      'end_passenger_index':end['passenger_index'],'end_freight_index':end['freight_index']}
                for key,factor in candidates.items():
                    profit=lambda r:r['core_operating_surplus_yi']+factor*r['unscaled_hidden_freight_income_yi']
                    item[key+'_end_surplus_yi']=profit(end)
                    item[key+'_cumulative_surplus_yi']=sum(profit(r) for r in history)
                    item[key+'_loss_years']=sum(profit(r)<0 for r in history)
                samples.append(item)
            if (seed+1)%32==0: print(f'Replayed {seed+1}/96 North seeds using current engine',flush=True)
    bureaus=[]
    for p in profiles:
        records=[r for r in samples if r['bureau_id']==p['bureau_id']]
        scenarios={key:metrics(records,key) for key in candidates}
        old=next((r for r in package_summary if r['bureau_id']==p['bureau_id']),None)
        if old:
            reference_error=max(reference_error,abs(scenarios['scale100']['end_surplus_median_yi']-float(old['2085_dynamic_surplus_median_yi'])),
                                abs(scenarios['scale100']['end_loss_count']-int(old['2085_dynamic_loss_count'])),
                                abs(scenarios['scale100']['cumulative_surplus_median_yi']-float(old['60y_dynamic_cumulative_surplus_median_yi'])))
        bureaus.append({'bureau_id':p['bureau_id'],'name':p['name'],
                        'original_base_net_yi':p['hidden_freight']['base_net_receipts_yi'],
                        'current_base_net_yi':p['hidden_freight']['base_net_receipts_yi']*scale,'scenarios':scenarios})
    region={}
    shanxi={'datong','taiyuan','changzhi','houma'}
    for key in candidates:
        totals=[sum(r[key+'_end_surplus_yi'] for r in samples if r['seed']==seed) for seed in range(96)]
        region[key]={'end_total_surplus_median_yi':statistics.median(totals),
                     'pooled_end_loss_fraction':sum(r[key+'_end_surplus_yi']<0 for r in samples)/len(samples),
                     'shanxi_four_all_profitable_seeds':sum(all(r[key+'_end_surplus_yi']>0 for r in samples if r['seed']==seed and r['bureau_id'] in shanxi) for seed in range(96))}
    if balance_error>1e-8 or reference_error>1e-7 or (reference and matched!=4880): raise AssertionError('Accounting or package replay mismatch')
    report={'modelVersion':VERSION,'settlementVersion':SETTLEMENT_VERSION,'regionId':'north',
            'bureauConfigHash':hashlib.sha256(NORTH_PROFILE_PATH.read_bytes()).hexdigest(),
            'seedCount':96,'seedRange':[0,95],'endYear':2085,'operatingYears':[2026,2085],
            'selectedScale':scale,'originalBaseNetTotalYi':sum(b['original_base_net_yi'] for b in bureaus),
            'currentBaseNetTotalYi':sum(b['current_base_net_yi'] for b in bureaus),
            'coreDefinition':'Same fully operating baseline, including revised Xiongan passenger assumptions; hidden settlement excluded',
            'verification':{'current_engine_annual_records':96*10*61,'package_annual_records_matched':matched,
                            'max_package_replay_difference':reference_error,'max_account_error':balance_error},
            'bureaus':bureaus,'region':region,'demonstrationCheckpoints':checkpoints}
    OUT.mkdir(exist_ok=True)
    (OUT/'north_settlement_v01.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    def write_csv(path,records):
        with path.open('w',encoding='utf-8-sig',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
    write_csv(OUT/'north_96seed_samples_v01.csv',samples)
    write_csv(OUT/'north_8seed_annual_v01.csv',annual)
    summary=[]
    for b in bureaus:
        r={k:b[k] for k in ('bureau_id','name','original_base_net_yi','current_base_net_yi')}
        for key,m in b['scenarios'].items():r.update({key+'_'+k:v for k,v in m.items()})
        summary.append(r)
    write_csv(OUT/'north_96seed_summary_v01.csv',summary)
    print(json.dumps({k:report[k] for k in ('selectedScale','currentBaseNetTotalYi','verification','region')},ensure_ascii=False,indent=2))
    for b in bureaus:
        a,c=b['scenarios']['scale100'],b['scenarios']['current']
        print(f"{b['name']}: original {a['end_surplus_median_yi']:.2f} / current {c['end_surplus_median_yi']:.2f} yi; loss {a['end_loss_fraction']:.1%} -> {c['end_loss_fraction']:.1%}")


if __name__=='__main__': main()
