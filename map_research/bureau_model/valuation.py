"""Read-only game valuations from true future plus locked synthetic errors.

Signed operating cash proxies are discounted; capital receipts and dividends
are excluded from those proxies. This module does not execute transactions.
"""
import hashlib
import json
import math
import random
from pathlib import Path

from .cash import config_hash as cash_hash

ROOT = Path(__file__).parent
POLICY_PATH = ROOT / 'valuation_policy_v01.json'
QUOTE_PATH = ROOT / 'capital_quote_policy_v01.json'
VERSION = 'railway-official-valuation-v0.1'


def load_config():
    p = json.loads(POLICY_PATH.read_text(encoding='utf-8'))
    q = json.loads(QUOTE_PATH.read_text(encoding='utf-8'))
    if p['forecast_years'] != 10 or not 0 <= p['expected_score'] <= 100:
        raise ValueError('Unsupported valuation forecast')
    if not 0 < p['discount_rate_floor_pct'] <= p['discount_rate_ceiling_pct']:
        raise ValueError('Invalid valuation discount bounds')
    if p['terminal_growth_pct'] != 0 or p['cost_scale_floor_fraction'] <= 0:
        raise ValueError('Unsupported terminal or error metric')
    m = q['merchant']
    if not m['old_share_bid_unconditional'] or m['voluntary_equity_subscriptions']['random_investment_willingness_check']:
        raise ValueError('Merchant must provide deterministic standing quotes')
    return p, q


def config_hash():
    h = hashlib.sha256(cash_hash().encode())
    for path in (POLICY_PATH, QUOTE_PATH, Path(__file__)):
        h.update(path.name.encode() + b'\0' + path.read_bytes() + b'\0')
    return h.hexdigest()


def error_for_score(score, horizon, policy):
    knots = sorted((int(k), v / 100) for k, v in policy['score_error_percent'][str(horizon)].items())
    for (s0, e0), (s1, e1) in zip(knots, knots[1:]):
        if score <= s1:
            return e0 + (e1 - e0) * (score - s0) / (s1 - s0)
    return 0.


def score_for_error(error, horizon, policy):
    knots = sorted((int(k), v / 100) for k, v in policy['score_error_percent'][str(horizon)].items())
    if error >= knots[0][1]:
        return 0.
    for (s0, e0), (s1, e1) in zip(knots, knots[1:]):
        if error >= e1:
            return s0 + (s1 - s0) * (e0 - error) / (e0 - e1)
    return 100.


def locked_forecast(actual, costs, *, seed, bureau_id, year, policy):
    """One-year point is shared by the ten-year path. Errors allow negative cash.

    Quality uses abs(error)/max(abs(actual surplus), 10% annual cost), with a
    small numerical floor. It is a game score, not a probability of being right.
    """
    if len(actual) != 10 or len(costs) != 10:
        raise ValueError('Valuation needs a ten-year future/continuation window')
    if any(not math.isfinite(v) for v in actual + costs) or any(v < 0 for v in costs):
        raise ValueError('Invalid valuation forecast inputs')
    scales = [max(abs(v), c * policy['cost_scale_floor_fraction'], .01) for v, c in zip(actual, costs)]
    if policy['expected_score'] == 100:
        return {'values': list(actual), 'actual_score': 100., 'one_year_score': 100.,
                'normalized_error_pct': 0., 'error_scales': scales}
    key = f'{VERSION}|{seed}|{bureau_id}|{year}|{policy["expected_score"]}'
    rng = random.Random(int.from_bytes(hashlib.sha256(key.encode()).digest(), 'big'))
    expected = policy['expected_score']
    targets = [100. if expected == 100 else max(.1, min(99.9, expected + rng.uniform(-policy['score_jitter'], policy['score_jitter']))) for _ in range(2)]
    first_error = error_for_score(targets[0], 1, policy) * rng.choice((-1, 1))
    target_total = error_for_score(targets[1], 10, policy) * 10
    bias, slope, phase = rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(0, math.pi * 2)
    shape = [bias + .45 * math.sin(phase + i / 9 * math.pi * 1.5) + .35 * slope * i / 9 + rng.uniform(-.08, .08) for i in range(1, 10)]
    shape = [math.copysign(max(.06, abs(v)), v or 1.) for v in shape]
    cap = policy['annual_error_cap_multiplier'] * error_for_score(targets[1], 10, policy)
    needed = max(0., target_total - abs(first_error))
    lo, hi = 0., 1000.
    for _ in range(60):
        mid = (lo + hi) / 2
        if sum(min(cap, abs(v) * mid) for v in shape) < needed:
            lo = mid
        else:
            hi = mid
    relative = [first_error] + [max(-cap, min(cap, v * (lo + hi) / 2)) for v in shape]
    values = [v + e * scale for v, e, scale in zip(actual, relative, scales)]
    mean_error = sum(abs(e) for e in relative) / 10
    return {'values': values, 'actual_score': score_for_error(mean_error, 10, policy),
            'one_year_score': score_for_error(abs(first_error), 1, policy),
            'normalized_error_pct': mean_error * 100, 'error_scales': scales}


def weighted_recent(values, weights):
    selected = list(reversed(values))[:len(weights)]
    return sum(v * w for v, w in zip(selected, weights)) / sum(weights[:len(selected)])


def discounted_right(values, rate, weights):
    explicit = sum(value / (1 + rate) ** (i + 1) for i, value in enumerate(values))
    sustainable = weighted_recent(values, weights)
    terminal = sustainable / rate / (1 + rate) ** len(values)
    return explicit, terminal


def quotation(value, cash, next_surplus, cost, quote_policy, committed=0.):
    """Standing informational quotes; no ownership or cash mutations."""
    m = quote_policy['merchant']
    months = 12 * (cash + next_surplus - committed) / max(cost, .01)
    bands = m['voluntary_equity_subscriptions']['bands']
    band = next(b for b in bands if months >= b.get('months_min_inclusive', -math.inf)
                and months < b.get('months_max_exclusive', math.inf))
    units = quote_policy['shares']['total_units']
    return {'valuation_cash_cover_months': months, 'valuation_active_band': band['state'],
            'valuation_issue_multiplier': band['issue_prevaluation_mult'],
            'valuation_issue_pre_yi': value * band['issue_prevaluation_mult'],
            'valuation_old_share_ask_yi': value * m['old_share_ask_mult'],
            'valuation_old_share_state_bid_yi': value * m['old_share_state_bid_mult'],
            'valuation_old_share_ask_per_unit_yi': value * m['old_share_ask_mult'] / units,
            'valuation_old_share_state_bid_per_unit_yi': value * m['old_share_state_bid_mult'] / units}


def valuation_history(operating_rows, cash_rows, national_rows, *, policy=None, quote_policy=None):
    if policy is None or quote_policy is None:
        p, q = load_config()
        policy, quote_policy = policy or p, quote_policy or q
    ops = sorted(operating_rows, key=lambda r: r['year'])
    if not ops or len({r['bureau_id'] for r in ops}) != 1 or len({r['seed'] for r in ops}) != 1:
        raise ValueError('One bureau/seed required')
    by_year = {r['year']: r for r in ops}
    if len(by_year) != len(ops) or list(by_year) != list(range(ops[0]['year'], ops[-1]['year'] + 1)):
        raise ValueError('Continuous operating history required')
    cash = {r['year']: r for r in cash_rows}
    national = {r['calendar_year']: r for r in national_rows}
    bid, seed, last = ops[0]['bureau_id'], ops[0]['seed'], ops[-1]['year']
    if any(r['bureau_id'] != bid or r['seed'] != seed for r in cash_rows) or set(cash) != set(by_year):
        raise ValueError('Cash/valuation identity mismatch')
    result = []
    for year, current in by_year.items():
        future = [by_year[min(last, year + i)] for i in range(1, 11)]
        actual = [r['operating_surplus_yi'] for r in future]
        costs = [r['cost_yi'] for r in future]
        forecast = locked_forecast(actual, costs, seed=seed, bureau_id=bid, year=year, policy=policy)
        rate_pct = max(policy['discount_rate_floor_pct'], min(policy['discount_rate_ceiling_pct'], national[year]['rate'] + policy['risk_premium_pct']))
        rate = rate_pct / 100
        explicit, terminal = discounted_right(forecast['values'], rate, policy['terminal_profit_weights'])
        truth_explicit, truth_terminal = discounted_right(actual, rate, policy['terminal_profit_weights'])
        cash_value = cash[year]['cash_closing_yi']
        value = max(0., explicit + terminal + cash_value)
        past = [r['operating_surplus_yi'] for r in ops if r['year'] <= year]
        row = {'year': year, 'seed': seed, 'bureau_id': bid,
               'valuation_official_yi': value,
               'valuation_full_future_reference_yi': max(0., truth_explicit + truth_terminal + cash_value),
               'valuation_operating_right_yi': explicit + terminal, 'valuation_cash_yi': cash_value,
               'valuation_forecast_pv_yi': explicit, 'valuation_terminal_pv_yi': terminal,
               'valuation_discount_rate_pct': rate_pct, 'valuation_quality_target': policy['expected_score'],
               'valuation_forecast_score': forecast['actual_score'], 'valuation_one_year_score': forecast['one_year_score'],
               'valuation_normalized_error_pct': forecast['normalized_error_pct'],
               'valuation_next_surplus_forecast_yi': forecast['values'][0], 'valuation_next_surplus_actual_yi': actual[0],
               'valuation_historical_normalized_surplus_yi': weighted_recent(past, policy['history_profit_weights']),
               'valuation_tail_years': sum(year + i > last for i in range(1, 11)),
               'valuation_at_floor': value == 0.,
               **quotation(value, cash_value, forecast['values'][0], current['cost_yi'], quote_policy,
                           policy['committed_cash_outflows_yi']),
               'forecastRows': [{'year': year + i, 'predicted_surplus_yi': pred, 'reference_surplus_yi': truth,
                                 'error_scale_yi': scale, 'sample_extension': year + i > last}
                                for i, (pred, truth, scale) in enumerate(zip(forecast['values'], actual, forecast['error_scales']), 1)]}
        if any(not math.isfinite(v) for v in row.values() if isinstance(v, (float, int))):
            raise ValueError('Nonfinite valuation')
        result.append(row)
    return result
