"""Serve the independent railway research UI and seeded macro scenarios.

Usage: py map_research/serve.py
Only binds to localhost. No Airport services or production models are changed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from functools import lru_cache
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from economy_model.simulate import REGIONAL_METRICS, load_config, public_market_snapshot
from economy_model.scenarios import simulate_scenario
from bureau_model.operations import PROFILE_PATH, NORTH_PROFILE_PATH, NORTHWEST_PROFILE_PATH, SOUTH_PROFILE_PATH, REMAINING_PROFILE_PATH, VERSION as BUREAU_VERSION, load_all_profiles, simulate_bureaus
from bureau_model.settlement import VERSION as SETTLEMENT_VERSION
from bureau_model.revenue import CURRENT_POLICY, config_hash
from bureau_model.cash import VERSION as CASH_VERSION, load_config as load_cash_config, cash_ledger, config_hash as cash_config_hash
from bureau_model.valuation import VERSION as VALUATION_VERSION, load_config as load_valuation_config, valuation_history, config_hash as valuation_config_hash

ROOT = Path(__file__).resolve().parent
MAX_SEED = 9_007_199_254_740_991
REGION_IDS = ('northeast', 'north', 'northwest', 'southwest', 'south', 'central', 'east', 'southeast')
CONFIG = load_config()
BUREAU_PROFILES = load_all_profiles()
PROFILE_HASHES = {'northeast': hashlib.sha256(PROFILE_PATH.read_bytes()).hexdigest(),
                  'north': hashlib.sha256(NORTH_PROFILE_PATH.read_bytes()).hexdigest(),
                  'northwest': hashlib.sha256(NORTHWEST_PROFILE_PATH.read_bytes()).hexdigest(),
                  'southwest': hashlib.sha256(SOUTH_PROFILE_PATH.read_bytes()).hexdigest(),
                  'south': hashlib.sha256(SOUTH_PROFILE_PATH.read_bytes()).hexdigest(),
                  **{rid:hashlib.sha256(REMAINING_PROFILE_PATH.read_bytes()).hexdigest() for rid in ('central','east','southeast')}}
CONFIG_HASH = config_hash()
CASH_OPENING, CASH_POLICY = load_cash_config()
CASH_CONFIG_HASH = cash_config_hash()
VALUATION_POLICY, CAPITAL_QUOTE_POLICY = load_valuation_config()
VALUATION_CONFIG_HASH = valuation_config_hash()
CASH_AUDIT = None
_cash_report = ROOT / 'bureau_model' / 'reports' / 'cash_capital_summary_v03.json'
if _cash_report.is_file():
    _cash_audit = json.loads(_cash_report.read_text(encoding='utf-8'))
    if (_cash_audit.get('configHash') == CASH_CONFIG_HASH
            and _cash_audit.get('operatingConfigHash') == CONFIG_HASH
            and _cash_audit.get('modelVersion') == CASH_VERSION):
        CASH_AUDIT = _cash_audit
CALIBRATION_AUDIT = None
_report = ROOT / 'bureau_model' / 'reports' / 'national_revenue_comparison_v04.json'
if _report.is_file():
    _audit = json.loads(_report.read_text(encoding='utf-8'))
    if (_audit.get('configHash') == CONFIG_HASH and _audit.get('modelVersion') == BUREAU_VERSION
            and _audit.get('settlementVersion') == SETTLEMENT_VERSION):
        CALIBRATION_AUDIT = _audit


@lru_cache(maxsize=4)
def scenario_result(seed: int) -> dict:
    return simulate_scenario(config=CONFIG, years=60, seed=seed)


def bureau_catalog() -> bytes:
    regions = [{'id': r['id'], 'name': r['name'], 'scope': r['scope']} for r in CONFIG['regions']]
    bureaus = [{k: p[k] for k in ('bureau_id', 'name', 'region_id', 'type')} for p in BUREAU_PROFILES]
    return json.dumps({'regions': regions, 'bureaus': bureaus, 'modelVersion': BUREAU_VERSION, 'settlementVersion':SETTLEMENT_VERSION},
                      ensure_ascii=False, allow_nan=False).encode('utf-8')


@lru_cache(maxsize=4)
def bureau_rows(seed: int) -> list[dict]:
    return simulate_bureaus(scenario_result(seed), BUREAU_PROFILES)


@lru_cache(maxsize=4)
def bureau_cash(seed: int):
    rows, events = cash_ledger(bureau_rows(seed), CASH_OPENING, CASH_POLICY)
    reference, _ = cash_ledger(bureau_rows(seed), CASH_OPENING, {**CASH_POLICY, 'dividends': False})
    lookup = {(r['year'], r['bureau_id']): r for r in reference}
    return [{**r, 'cash_without_dividends_closing_yi': lookup[r['year'],r['bureau_id']]['cash_closing_yi'],
             'cash_without_dividends_cumulative_equity_yi': lookup[r['year'],r['bureau_id']]['cash_cumulative_equity_yi']}
            for r in rows], events


@lru_cache(maxsize=12)
def bureau_valuations(seed: int, bureau_id: str):
    cash_rows, _ = bureau_cash(seed)
    return valuation_history([r for r in bureau_rows(seed) if r['bureau_id'] == bureau_id],
                             [r for r in cash_rows if r['bureau_id'] == bureau_id],
                             scenario_result(seed)['national_factors'],
                             policy=VALUATION_POLICY, quote_policy=CAPITAL_QUOTE_POLICY)


def bureau_payload(seed: int, bureau_id: str) -> bytes:
    profile = next((p for p in BUREAU_PROFILES if p['bureau_id'] == bureau_id), None)
    if profile is None:
        raise KeyError(bureau_id)
    result = scenario_result(seed)
    cash_rows, cash_events = bureau_cash(seed)
    cash_audit = None
    if CASH_AUDIT:
        rid = profile['region_id']
        cash_audit = {k: CASH_AUDIT[k] for k in ('seedCount', 'seedRange', 'endYear', 'configHash')}
        cash_audit.update(region=CASH_AUDIT['regions'][rid],
                          bureau=next(b for b in CASH_AUDIT['bureaus'] if b['bureau_id'] == bureau_id),
                          bureaus=[b for b in CASH_AUDIT['bureaus'] if b['region_id'] == rid])
    payload = {
        'seed': seed, 'modelVersion': BUREAU_VERSION,
        'macroModelVersion': result['metadata']['model_version'],
        'macroConfigHash': result['metadata']['scenario_config_sha256'],
        'bureauConfigHash': CONFIG_HASH, 'profileConfigHash': PROFILE_HASHES[profile['region_id']],
        'revenuePolicy': CURRENT_POLICY, 'baseYear': CONFIG['base_year'],
        'settlementVersion': SETTLEMENT_VERSION,
        'priceBasis': 'constant_2025_purchasing_power', 'currencyUnit': '100_million_CNY',
        'scenario': result['scenario'], 'profile': profile,
        'officialValuation': {'modelVersion': VALUATION_VERSION, 'configHash': VALUATION_CONFIG_HASH,
                             'policy': VALUATION_POLICY, 'quotePolicy': CAPITAL_QUOTE_POLICY,
                             'rows': bureau_valuations(seed, bureau_id)},
        'cash': {'modelVersion': CASH_VERSION, 'configHash': CASH_CONFIG_HASH,
                 'policy': CASH_POLICY, 'calibrationAudit': cash_audit,
                 'rows': [r for r in cash_rows if r['bureau_id'] == bureau_id],
                 'capitalEvents': [e for e in cash_events if e['bureau_id'] == bureau_id]},
        'calibrationAudit': ({**{k: CALIBRATION_AUDIT[k] for k in ('seedCount','seedRange','endYear','configHash')},
                              'modes': CALIBRATION_AUDIT.get('regionModeLabels', {}).get(profile['region_id'], CALIBRATION_AUDIT['modes']),
                              'region': CALIBRATION_AUDIT['regions'][profile['region_id']],
                              'scenarioGroups': CALIBRATION_AUDIT.get('scenarioGroups', {}).get(profile['region_id'], {}),
                              'bureaus': [b for b in CALIBRATION_AUDIT['bureaus'] if b['region_id']==profile['region_id']]}
                             if CALIBRATION_AUDIT else None),
        'rows': [r for r in bureau_rows(seed) if r['bureau_id'] == bureau_id],
        'regionalPrices': [{k: r[k] for k in ('calendar_year', 'energy_real_index', 'wage_real_index', 'materials_real_index')}
                           for r in result['rows'] if r['region_id'] == profile['region_id']],
    }
    # Full future results are intentionally available only for this localhost
    # research viewer. Do not reuse as an in-game prediction/decision endpoint.
    return json.dumps(payload, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')


@lru_cache(maxsize=16)
def scenario_payload(seed: int) -> bytes:
    result = scenario_result(seed)
    public = public_market_snapshot(result, 60)
    lookup = {(row['year_index'], row['region_id']): row for row in public['regional_rows']}
    columns = ['year_index', 'calendar_year']
    columns += [f'{region}__{metric}' for metric in REGIONAL_METRICS for region in REGION_IDS]
    columns += ['national__real_rate_pct', 'national__valuation_index']
    values = []
    national = []
    for row in public['national_rows']:
        year_index = row['year_index']
        values.append([year_index, row['calendar_year']]
                      + [lookup[year_index, region][metric] for metric in REGIONAL_METRICS for region in REGION_IDS]
                      + [row['real_rate_pct'], row['valuation_index']])
        national.append({'year': row['calendar_year'], 'rate': row['real_rate_pct'],
                         'pe': row['pe_multiple'], 'valuation': row['valuation_index']})
    payload = {'seed': seed, 'modelVersion': result['metadata']['model_version'],
               'configHash': result['metadata']['scenario_config_sha256'], 'baseYear': result['metadata']['base_year'],
               'columns': columns, 'values': values, 'national': national,
               'scenario': result['scenario'], 'phases': result['phases'],
               'regionalPhases': result['regional_phases']}
    return json.dumps(payload, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def json_response(self, status: int, content: bytes):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        url = urlsplit(self.path)
        if url.path == '/api/bureau-catalog':
            return self.json_response(200, bureau_catalog())
        if url.path not in ('/api/economy', '/api/bureau'):
            return super().do_GET()
        query = parse_qs(url.query, keep_blank_values=True)
        seeds = query.get('seed', ['20261014'])
        raw = seeds[0]
        if len(seeds) != 1 or not raw.isascii() or not raw.isdigit() or len(raw) > 16:
            return self.json_response(400, b'{"error":"seed must be an integer between 0 and 9007199254740991"}')
        seed = int(raw)
        if not 0 <= seed <= MAX_SEED:
            return self.json_response(400, b'{"error":"seed is outside the supported range"}')
        if url.path == '/api/bureau':
            bureaus = query.get('bureau', ['jiamusi'])
            if len(bureaus) != 1 or bureaus[0] not in {p['bureau_id'] for p in BUREAU_PROFILES}:
                return self.json_response(400, b'{"error":"bureau is not configured"}')
            try:
                payload = bureau_payload(seed, bureaus[0])
            except Exception:
                self.log_error('Bureau scenario generation failed for seed %s', seed)
                return self.json_response(500, b'{"error":"bureau scenario generation failed"}')
            return self.json_response(200, payload)
        try:
            payload = scenario_payload(seed)
        except Exception:
            self.log_error('Macro scenario generation failed for seed %s', seed)
            return self.json_response(500, b'{"error":"scenario generation failed"}')
        self.json_response(200, payload)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8780)
    args = parser.parse_args()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    print(f'Railway research: http://127.0.0.1:{args.port}/railway.html', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
