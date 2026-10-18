"""100 bureaus × 96 seeds; cash-only postprocessing of unchanged V0.4.

Run: py -3 -m bureau_model.audit_cash
"""
import collections
import csv
import json
import statistics
from pathlib import Path

from economy_model.scenarios import simulate_scenario
from .cash import VERSION, cash_ledger, config_hash, load_config
from .operations import load_all_profiles, simulate_bureaus
from .revenue import config_hash as operating_hash

OUT = Path(__file__).with_name('reports')


def summarize(records):
    return {
        'cumulative_equity_median_yi': statistics.median(r['cumulative_equity_yi'] for r in records),
        'ending_cash_median_yi': statistics.median(r['ending_cash_yi'] for r in records),
        'injection_years_median': statistics.median(r['injection_years'] for r in records),
        'ever_negative_carryover_fraction': sum(r['negative_carryover_years'] > 0 for r in records) / len(records),
        'ever_negative_closing_fraction': sum(r['negative_closing_years'] > 0 for r in records) / len(records),
        'ever_funded_fraction': sum(r['injection_years'] > 0 for r in records) / len(records),
        'negative_carryover_years_median': statistics.median(r['negative_carryover_years'] for r in records),
        'cumulative_dividend_median_yi': statistics.median(r['cumulative_dividend_yi'] for r in records),
        'cumulative_state_net_investment_median_yi': statistics.median(r['cumulative_state_net_investment_yi'] for r in records),
        'dividend_years_median': statistics.median(r['dividend_years'] for r in records),
        'withoutDividends': {
            'ending_cash_median_yi': statistics.median(r['without_dividends_ending_cash_yi'] for r in records),
            'cumulative_equity_median_yi': statistics.median(r['without_dividends_cumulative_equity_yi'] for r in records),
            'ever_negative_closing_fraction': sum(r['without_dividends_negative_closing_years'] > 0 for r in records) / len(records),
        },
    }


def write_csv(name, records):
    with (OUT / name).open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)


def main():
    opening, policy = load_config()
    profiles = load_all_profiles()
    assert {p['bureau_id'] for p in profiles} == {p['bureau_id'] for p in opening['bureaus']}
    previous = json.loads((OUT / 'national_revenue_comparison_v04.json').read_text(encoding='utf-8'))
    assert previous['configHash'] == operating_hash(), 'Operating audit is stale'
    with (OUT / 'national_revenue_samples_96seeds_v04.csv').open(encoding='utf-8-sig', newline='') as f:
        reference = {(int(r['seed']), r['bureau_id']): r for r in csv.DictReader(f) if r['mode'] == 'combined_v04'}
    with (OUT / 'cash_capital_samples_96seeds_v02.csv').open(encoding='utf-8-sig', newline='') as f:
        cash_reference = {(int(r['seed']),r['bureau_id']):r for r in csv.DictReader(f)}
    samples, examples = [], []
    max_cash_reference_difference = 0.
    max_difference = 0.
    annual_records = 0
    for seed in range(96):
        macro = simulate_scenario(seed=seed, years=60)
        native = simulate_bureaus(macro, profiles)
        ledger, events = cash_ledger(native, opening, policy)
        no_dividends, _ = cash_ledger(native, opening, {**policy, 'dividends': False})
        reference_groups = collections.defaultdict(list)
        for r in no_dividends: reference_groups[r['bureau_id']].append(r)
        annual_records += len(ledger)
        groups, operating = collections.defaultdict(list), collections.defaultdict(list)
        for row in ledger:
            groups[row['bureau_id']].append(row)
        for row in native:
            operating[row['bureau_id']].append(row)
        for p in profiles:
            bid = p['bureau_id']
            rs, ops = groups[bid], operating[bid]
            end = rs[-1]
            old_rs = reference_groups[bid]
            old_end = old_rs[-1]
            for current, key in [('cash_closing_yi','ending_cash_yi'),('cash_cumulative_equity_yi','cumulative_equity_yi')]:
                max_cash_reference_difference = max(max_cash_reference_difference,abs(old_end[current]-float(cash_reference[seed,bid][key])))
            check = {'end_surplus_yi': ops[-1]['operating_surplus_yi'],
                     'end_wage_cost_yi': ops[-1]['wage_cost_yi'],
                     'cumulative_surplus_yi': sum(r['operating_surplus_yi'] for r in ops[1:])}
            for key, value in check.items():
                max_difference = max(max_difference, abs(value - float(reference[seed, bid][key])))
            samples.append({'seed': seed, 'bureau_id': bid, 'name': p['name'], 'region_id': p['region_id'],
                            'initial_cash_yi': end['cash_initial_yi'],
                            'ending_cash_yi': end['cash_closing_yi'],
                            'cumulative_equity_yi': end['cash_cumulative_equity_yi'],
                            'injection_years': end['cash_injection_years'],
                            'cumulative_dividend_yi': end['cash_cumulative_dividend_yi'],
                            'cumulative_state_net_investment_yi': end['cash_cumulative_state_net_investment_yi'],
                            'dividend_years': end['cash_dividend_years'],
                            'without_dividends_ending_cash_yi': old_end['cash_closing_yi'],
                            'without_dividends_cumulative_equity_yi': old_end['cash_cumulative_equity_yi'],
                            'without_dividends_negative_closing_years': sum(r['cash_negative_closing'] for r in old_rs[1:]),
                            'negative_carryover_years': sum(r['cash_negative_carryover'] for r in rs[1:]),
                            'negative_closing_years': sum(r['cash_negative_closing'] for r in rs[1:]),
                            'first_injection_year': next((r['year'] for r in rs if r['cash_state_equity_yi'] > 0), ''),
                            'first_funding_calendar_year': next((r['cash_funding_year'] for r in rs if r['cash_state_equity_yi'] > 0), ''),
                            'minimum_carryover_yi': min(r['cash_carryover_yi'] for r in rs),
                            'cumulative_operating_proxy_yi': end['cash_cumulative_operating_proxy_yi']})
        if seed in (0, 1, 2, 7, 9, 13):
            examples.extend(events)
        if (seed + 1) % 8 == 0:
            print(f'Cash replay {seed + 1}/96; operating difference {max_difference:.3g}', flush=True)
    assert max_difference < 1e-8, 'Operating results changed'
    assert max_cash_reference_difference < 1e-8, 'Without-dividend reference changed'
    bureaus = [{**{k: p[k] for k in ('bureau_id', 'name', 'region_id')},
                **summarize([r for r in samples if r['bureau_id'] == p['bureau_id']])} for p in profiles]
    regions = {}
    for rid in list(dict.fromkeys(p['region_id'] for p in profiles)) + ['all']:
        selected = [r for r in samples if rid == 'all' or r['region_id'] == rid]
        totals = []
        for seed in range(96):
            rs = [r for r in selected if r['seed'] == seed]
            totals.append({k: sum(r[k] for r in rs) for k in ('cumulative_equity_yi', 'ending_cash_yi',
                          'injection_years', 'negative_carryover_years', 'negative_closing_years',
                          'cumulative_dividend_yi','cumulative_state_net_investment_yi','dividend_years',
                          'without_dividends_ending_cash_yi','without_dividends_cumulative_equity_yi','without_dividends_negative_closing_years')})
        regions[rid] = summarize(totals)
        regions[rid]['pooled_ever_negative_carryover_fraction'] = sum(r['negative_carryover_years'] > 0 for r in selected) / len(selected)
        regions[rid]['pooled_ever_funded_fraction'] = sum(r['injection_years'] > 0 for r in selected) / len(selected)
        regions[rid]['bureauCount'] = len(selected) // 96
    report = {'modelVersion': VERSION, 'configHash': config_hash(), 'operatingConfigHash': operating_hash(),
              'seedCount': 96, 'seedRange': [0, 95], 'baseYear': 2025, 'endYear': 2085,
              'annualRecordCount': annual_records, 'initialCashTotalYi': opening['total_initial_cash_yi'],
              'maxOperatingDifference': max_difference, 'maxWithoutDividendReferenceDifference': max_cash_reference_difference,
              'pairedAnnualRecordCount': annual_records*2, 'policy': policy, 'regions': regions, 'bureaus': bureaus,
              'negativeCashBasis': 'actual_year_end',
              'note': '2025 opening snapshot only. Budget years 2026-2085 funded at previous calendar year end from previous-year information. Cash proxy rounded to 0.01 yi. After operations, eligible companies pay 50% profit and 50% excess-cash dividends, retaining six months costs; no payouts in budget years with capital or nonpositive profit. State owns 100%. No emergency advances; actual year-end cash may be negative. Regional totals summed within each seed before median.'}
    report['comparisonBasis'] = 'Paired identical operating paths; only dividend policy toggled. No-dividend closing cash and capital match stored V0.2 samples.'
    (OUT / 'cash_capital_summary_v03.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    write_csv('cash_capital_samples_96seeds_v03.csv', samples)
    write_csv('cash_capital_6seed_events_v03.csv', examples)
    print(json.dumps({'all': regions['all'], 'records': annual_records, 'maxOperatingDifference': max_difference}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
