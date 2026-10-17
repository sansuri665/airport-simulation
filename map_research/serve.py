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
from bureau_model.operations import PROFILE_PATH, VERSION as BUREAU_VERSION, load_profiles, simulate_bureaus

ROOT = Path(__file__).resolve().parent
MAX_SEED = 9_007_199_254_740_991
REGION_IDS = ('northeast', 'north', 'northwest', 'southwest', 'south', 'central', 'east', 'southeast')
CONFIG = load_config()
BUREAU_PROFILES = load_profiles()
BUREAU_CONFIG_HASH = hashlib.sha256(PROFILE_PATH.read_bytes()).hexdigest()


@lru_cache(maxsize=4)
def scenario_result(seed: int) -> dict:
    return simulate_scenario(config=CONFIG, years=60, seed=seed)


def bureau_catalog() -> bytes:
    regions = [{'id': r['id'], 'name': r['name'], 'scope': r['scope']} for r in CONFIG['regions']]
    bureaus = [{k: p[k] for k in ('bureau_id', 'name', 'region_id', 'type')} for p in BUREAU_PROFILES]
    return json.dumps({'regions': regions, 'bureaus': bureaus, 'modelVersion': BUREAU_VERSION},
                      ensure_ascii=False, allow_nan=False).encode('utf-8')


@lru_cache(maxsize=4)
def bureau_rows(seed: int) -> list[dict]:
    return simulate_bureaus(scenario_result(seed), BUREAU_PROFILES)


def bureau_payload(seed: int, bureau_id: str) -> bytes:
    profile = next((p for p in BUREAU_PROFILES if p['bureau_id'] == bureau_id), None)
    if profile is None:
        raise KeyError(bureau_id)
    result = scenario_result(seed)
    payload = {
        'seed': seed, 'modelVersion': BUREAU_VERSION,
        'macroModelVersion': result['metadata']['model_version'],
        'macroConfigHash': result['metadata']['scenario_config_sha256'],
        'bureauConfigHash': BUREAU_CONFIG_HASH, 'baseYear': CONFIG['base_year'],
        'priceBasis': 'constant_2025_purchasing_power', 'currencyUnit': '100_million_CNY',
        'scenario': result['scenario'], 'profile': profile,
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
