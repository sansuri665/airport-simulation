"""2025 fixed loss cohort, one Seed; read-only V0.2 vs unified V0.3, plus 100-bureau continuity.

Run from map_research: py -3 -m bureau_model.audit_loss_valuation --seed 5767783356797806
This is a valuation sensitivity report, not a 96-Seed probability calibration.
"""
import argparse
import csv
import json
from pathlib import Path

from economy_model.scenarios import simulate_scenario
from .cash import cash_ledger, load_config as cash_config, config_hash as cash_hash
from .operations import load_all_profiles, simulate_bureaus
from .revenue import config_hash as operating_hash
from .valuation import VERSION, config_hash, loss_comparison, continuity_check


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=int, default=5767783356797806)
    parser.add_argument('--out', type=Path, default=Path(__file__).with_name('reports'))
    args = parser.parse_args()
    if not 0 <= args.seed <= 9007199254740991:
        parser.error('Seed outside supported range')
    profiles = load_all_profiles()
    macro = simulate_scenario(seed=args.seed, years=60)
    operating = simulate_bureaus(macro, profiles)
    opening, policy = cash_config()
    cash, _ = cash_ledger(operating, opening, policy)
    report = loss_comparison(operating, cash, macro['national_factors'], profiles)
    report.update(modelVersion=VERSION, configHash=config_hash(), cashConfigHash=cash_hash(),
                  operatingConfigHash=operating_hash(), probabilityCalibrated=False,
                  description='One Seed, 24 fixed 2025 loss bureaus. No macro, operating or cash changes. No equity issuance or dilution executed.')
    assert len(report['rows']) == 24
    args.out.mkdir(parents=True, exist_ok=True)
    stem = f'loss_valuation_24_seed_{args.seed}_v03'
    (args.out / f'{stem}.json').write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    with (args.out / f'{stem}.csv').open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(report['rows'][0]))
        writer.writeheader()
        writer.writerows(report['rows'])
    print(json.dumps(report['summary'], ensure_ascii=False))
    print(args.out / f'{stem}.csv')
    groups, cash_groups = {}, {}
    for r in operating: groups.setdefault(r['bureau_id'], []).append(r)
    for r in cash: cash_groups.setdefault(r['bureau_id'], []).append(r)
    probes = []
    for i, p in enumerate(profiles):
        bid = p['bureau_id']
        check = continuity_check(groups[bid], cash_groups[bid], macro['national_factors'])
        probes.append({'bureau_id': bid, 'name': p['name'], **check})
        if (i+1) % 25 == 0: print('continuity checked', i+1, flush=True)
    continuity = {'seed':args.seed, 'modelVersion':VERSION, 'configHash':config_hash(),
                  'definition':'2025: current revenue/cash/future fixed; change current cost so surplus is -10000, 0, +10000 CNY',
                  'bureauCount':len(probes), 'maxNewGapYi':max(p['newGapYi'] for p in probes),
                  'maxV02GapYi':max(p['v02GapYi'] for p in probes), 'rows':probes}
    (args.out / f'valuation_continuity_100_seed_{args.seed}_v03.json').write_text(
        json.dumps(continuity, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    assert continuity['maxNewGapYi'] < .01, 'Unexpected zero-profit discontinuity'
    print(json.dumps({k:v for k,v in continuity.items() if k!='rows'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
