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
from .equity_scenarios import scenario_equity

ROOT = Path(__file__).parent
POLICY_PATH = ROOT / 'valuation_policy_v03.json'
QUOTE_PATH = ROOT / 'capital_quote_policy_v01.json'
VERSION = 'railway-official-valuation-v0.3'
FORECAST_VERSION = 'railway-official-valuation-v0.1'  # Preserve existing locked forecasts.


def load_config():
    p = json.loads(POLICY_PATH.read_text(encoding='utf-8'))
    q = json.loads(QUOTE_PATH.read_text(encoding='utf-8'))
    if p['forecast_years'] != 10 or not 0 <= p['expected_score'] <= 100:
        raise ValueError('Unsupported valuation forecast')
    if not 0 < p['discount_rate_floor_pct'] <= p['discount_rate_ceiling_pct']:
        raise ValueError('Invalid valuation discount bounds')
    if p['terminal_growth_pct'] != 0 or p['cost_scale_floor_fraction'] <= 0:
        raise ValueError('Unsupported terminal or error metric')
    loss = p['loss_valuation']
    if (loss['scenario_count'] < 2 or loss['scenario_count'] % 2
            or not 0 <= loss['recovery_margin_min'] < 1
            or loss['recovery_profit_multiple'] <= 0
            or loss['distress_revenue_multiple'] < 0
            or loss['terminal_margin_sigma'] < 0):
        raise ValueError('Invalid loss valuation assumptions')
    e = p['equity_scenarios']
    if (not isinstance(e['scenario_count'], int) or e['scenario_count'] < 2 or e['scenario_count'] % 2
            or e['franchise_revenue_multiple'] <= 0 or e['minimum_cash_reserve_yi'] < 0
            or not 0 <= e['funding_reserve_months'] <= e['dividend_reserve_months'] <= 12
            or e['terminal_margin_sigma'] < 0
            or any(not 0 <= e[k] <= 1 for k in ('profit_payout_ratio', 'excess_cash_payout_ratio', 'sustained_margin_min', 'low_value_revenue_ratio'))):
        raise ValueError('Invalid unified equity assumptions')
    m = q['merchant']
    if not m['old_share_bid_unconditional'] or m['voluntary_equity_subscriptions']['random_investment_willingness_check']:
        raise ValueError('Merchant must provide deterministic standing quotes')
    return p, q


def config_hash():
    h = hashlib.sha256(cash_hash().encode())
    for path in (POLICY_PATH, QUOTE_PATH, Path(__file__), ROOT / 'equity_scenarios.py'):
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
    key = f'{FORECAST_VERSION}|{seed}|{bureau_id}|{year}|{policy["expected_score"]}'
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


def loss_right(values, revenue, rate, *, seed, bureau_id, year, policy):
    """Probability-weighted OPERATING rights, before cash and future financing.

    Antithetic scenarios perturb the existing forecast, not the macro engine.
    Positive interim surplus enters branch values; negative surplus enters the
    funding burden once. No capital receipts, rescue grants or dilution payoff.
    All branch values and burdens are present values at the appraisal date.
    """
    p = policy['loss_valuation']
    if revenue <= 0 or not math.isfinite(revenue) or len(values) != 10:
        raise ValueError('Loss valuation needs revenue and ten forecast years')
    rng = random.Random(int.from_bytes(hashlib.sha256(
        f'loss-right-v0.1|{seed}|{bureau_id}|{year}'.encode()).digest(), 'big'))
    sigma = p['terminal_margin_sigma'] * (100 - policy['expected_score']) / 30
    discounts = [(1 + rate) ** (i + 1) for i in range(10)]
    recovery_count = 0
    recovery_sum = distress_sum = burden_sum = 0.
    for _ in range(p['scenario_count'] // 2):
        common, drift = rng.gauss(0, 1), rng.gauss(0, 1)
        shocks = [revenue * sigma * math.sqrt((i + 1) / 10)
                  * (.85 * common + .35 * drift * (i + 1) / 10
                     + .25 * rng.gauss(0, 1)) for i in range(10)]
        for sign in (-1, 1):
            path = [v + sign * shock for v, shock in zip(values, shocks)]
            positive_pv = sum(max(0., v) / d for v, d in zip(path, discounts))
            burden_sum += sum(max(0., -v) / d for v, d in zip(path, discounts))
            normal_profit = weighted_recent(path, policy['terminal_profit_weights'])
            recovered = all(v > 0 for v in path[-3:]) and normal_profit >= revenue * p['recovery_margin_min']
            if recovered:
                recovery_count += 1
                recovery_sum += positive_pv + normal_profit * p['recovery_profit_multiple'] / discounts[-1]
            else:
                # Low present-value franchise multiple is an explicit game assumption.
                distress_sum += positive_pv + revenue * p['distress_revenue_multiple']
    n = p['scenario_count']
    probability = recovery_count / n
    recovery_value = recovery_sum / recovery_count if recovery_count else 0.
    distress_value = distress_sum / (n - recovery_count) if recovery_count < n else 0.
    weighted_value = (recovery_sum + distress_sum) / n
    burden = burden_sum / n
    return {'valuation_recovery_probability': probability,
            'valuation_recovery_right_yi': recovery_value,
            'valuation_distress_right_yi': distress_value,
            'valuation_weighted_right_before_burden_yi': weighted_value,
            'valuation_transition_loss_pv_yi': burden,
            'valuation_loss_scenario_count': n,
            'valuation_normalized_revenue_yi': revenue,
            'valuation_loss_right_yi': weighted_value - burden}


def quotation(value, cash, next_surplus, cost, quote_policy, committed=0.):
    """Standing informational quotes; no ownership or cash mutations."""
    m = quote_policy['merchant']
    months = 12 * (cash + next_surplus - committed) / max(cost, .01)
    bands = m['voluntary_equity_subscriptions']['bands']
    band = next(b for b in bands if months >= b.get('months_min_inclusive', -math.inf)
                and months < b.get('months_max_exclusive', math.inf))
    units = quote_policy['shares']['total_units']
    available = value > 0
    return {'valuation_quote_status': 'quoted' if available else 'restructuring_required',
            'valuation_cash_cover_months': months, 'valuation_active_band': band['state'],
            'valuation_issue_multiplier': band['issue_prevaluation_mult'],
            'valuation_issue_pre_yi': value * band['issue_prevaluation_mult'] if available else None,
            'valuation_old_share_ask_yi': value * m['old_share_ask_mult'] if available else None,
            'valuation_old_share_state_bid_yi': value * m['old_share_state_bid_mult'] if available else None,
            'valuation_old_share_ask_per_unit_yi': value * m['old_share_ask_mult'] / units if available else None,
            'valuation_old_share_state_bid_per_unit_yi': value * m['old_share_state_bid_mult'] / units if available else None}


def valuation_history_v02(operating_rows, cash_rows, national_rows, *, policy=None, quote_policy=None, as_of_years=None):
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
        if as_of_years is not None and year not in as_of_years:
            continue
        future = [by_year[min(last, year + i)] for i in range(1, 11)]
        actual = [r['operating_surplus_yi'] for r in future]
        costs = [r['cost_yi'] for r in future]
        forecast = locked_forecast(actual, costs, seed=seed, bureau_id=bid, year=year, policy=policy)
        rate_pct = max(policy['discount_rate_floor_pct'], min(policy['discount_rate_ceiling_pct'], national[year]['rate'] + policy['risk_premium_pct']))
        rate = rate_pct / 100
        explicit, terminal = discounted_right(forecast['values'], rate, policy['terminal_profit_weights'])
        truth_explicit, truth_terminal = discounted_right(actual, rate, policy['terminal_profit_weights'])
        cash_value = cash[year]['cash_closing_yi']
        net_cash = cash_value - policy['committed_cash_outflows_yi']
        legacy_value = max(0., explicit + terminal + net_cash)
        right, truth_right = explicit + terminal, truth_explicit + truth_terminal
        loss_details = {'valuation_recovery_probability': None, 'valuation_recovery_right_yi': None,
                        'valuation_distress_right_yi': None, 'valuation_weighted_right_before_burden_yi': None,
                        'valuation_transition_loss_pv_yi': None, 'valuation_loss_scenario_count': 0,
                        'valuation_normalized_revenue_yi': None, 'valuation_loss_right_yi': None}
        is_loss = current['operating_surplus_yi'] < -1e-9
        if is_loss:
            revenue = weighted_recent([r['revenue_yi'] for r in ops if r['year'] <= year],
                                      policy['history_profit_weights'])
            identity = dict(seed=seed, bureau_id=bid, year=year, policy=policy)
            loss_details = loss_right(forecast['values'], revenue, rate, **identity)
            right = loss_details['valuation_loss_right_yi']
            truth_right = loss_right(actual, revenue, rate, **identity)['valuation_loss_right_yi']
        value = max(0., right + net_cash)
        past = [r['operating_surplus_yi'] for r in ops if r['year'] <= year]
        row = {'year': year, 'seed': seed, 'bureau_id': bid,
               'valuation_official_yi': value,
               'valuation_full_future_reference_yi': max(0., truth_right + net_cash),
               'valuation_method': 'loss_probability' if is_loss else 'dcf',
               'valuation_legacy_dcf_yi': legacy_value,
               'valuation_operating_right_yi': right, 'valuation_cash_yi': cash_value,
               'valuation_net_cash_yi': net_cash,
               'valuation_forecast_pv_yi': explicit, 'valuation_terminal_pv_yi': terminal,
               'valuation_discount_rate_pct': rate_pct, 'valuation_quality_target': policy['expected_score'],
               'valuation_forecast_score': forecast['actual_score'], 'valuation_one_year_score': forecast['one_year_score'],
               'valuation_normalized_error_pct': forecast['normalized_error_pct'],
               'valuation_next_surplus_forecast_yi': forecast['values'][0], 'valuation_next_surplus_actual_yi': actual[0],
               'valuation_historical_normalized_surplus_yi': weighted_recent(past, policy['history_profit_weights']),
               'valuation_tail_years': sum(year + i > last for i in range(1, 11)),
               'valuation_at_floor': value == 0.,
               **loss_details,
               **quotation(value, cash_value, forecast['values'][0], current['cost_yi'], quote_policy,
                           policy['committed_cash_outflows_yi']),
               'forecastRows': [{'year': year + i, 'predicted_surplus_yi': pred, 'reference_surplus_yi': truth,
                                 'error_scale_yi': scale, 'sample_extension': year + i > last}
                                for i, (pred, truth, scale) in enumerate(zip(forecast['values'], actual, forecast['error_scales']), 1)]}
        if any(not math.isfinite(v) for v in row.values() if isinstance(v, (float, int))):
            raise ValueError('Nonfinite valuation')
        result.append(row)
    return result


def valuation_history(operating_rows, cash_rows, national_rows, *, policy=None, quote_policy=None, as_of_years=None):
    if policy is None or quote_policy is None:
        p, q = load_config()
        policy, quote_policy = policy or p, quote_policy or q
    # V0.2 is a benchmark only. Its loss/profit branch does not set new prices.
    benchmark = valuation_history_v02(operating_rows, cash_rows, national_rows,
                                     policy=policy, quote_policy=quote_policy, as_of_years=as_of_years)
    ops = sorted(operating_rows, key=lambda r: r['year'])
    by_year = {r['year']: r for r in ops}
    result = []
    for old in benchmark:
        year = old['year']
        current = by_year[year]
        future = [by_year[min(ops[-1]['year'], year+i)] for i in range(1, 11)]
        revenue = weighted_recent([r['revenue_yi'] for r in ops if r['year'] <= year], policy['history_profit_weights'])
        args = ([r['cost_yi'] for r in future], revenue, old['valuation_net_cash_yi'],
                current['operating_surplus_yi'], current['cost_yi'], old['valuation_discount_rate_pct']/100)
        identity = dict(seed=old['seed'], bureau_id=old['bureau_id'], policy=policy)
        new = scenario_equity([f['predicted_surplus_yi'] for f in old['forecastRows']], *args, **identity)
        reference = scenario_equity([r['operating_surplus_yi'] for r in future], *args, **identity)
        row = {**old, **new,
               'valuation_v02_reference_yi': old['valuation_official_yi'],
               'valuation_full_future_reference_yi': reference['valuation_official_yi'],
               # Compatibility attribution, not a separately appraised asset.
               'valuation_operating_right_yi': new['valuation_official_yi']-old['valuation_net_cash_yi'],
               'valuation_at_floor': new['valuation_official_yi'] <= 0,
               'valuation_weighted_right_before_burden_yi': None,
               'valuation_recovery_right_yi': None, 'valuation_distress_right_yi': None,
               'valuation_loss_right_yi': None,
               **quotation(new['valuation_official_yi'], old['valuation_cash_yi'], old['valuation_next_surplus_forecast_yi'],
                           current['cost_yi'], quote_policy, policy['committed_cash_outflows_yi'])}
        if any(not math.isfinite(v) for v in row.values() if isinstance(v, (float, int))):
            raise ValueError('Nonfinite unified equity value')
        result.append(row)
    return result


def loss_comparison(operating_rows, cash_rows, national_rows, profiles, *, policy=None, quote_policy=None):
    """Current Seed, 2025 fixed loss cohort; not a 96-Seed calibration report."""
    lookup = {p['bureau_id']: p for p in profiles}
    ops, cash = {}, {}
    for row in operating_rows:
        ops.setdefault(row['bureau_id'], []).append(row)
    for row in cash_rows:
        cash.setdefault(row['bureau_id'], []).append(row)
    rows = []
    for bid, history in ops.items():
        base = min(history, key=lambda r: r['year'])
        if base['year'] != 2025 or base['operating_surplus_yi'] >= -1e-9:
            continue
        value = valuation_history(history, cash[bid], national_rows, policy=policy,
                                  quote_policy=quote_policy, as_of_years={2025})[0]
        rows.append({k: v for k, v in value.items() if k != 'forecastRows'} | {
            'name': lookup[bid]['name'], 'region_id': lookup[bid]['region_id'],
            'base_revenue_yi': base['revenue_yi'], 'base_surplus_yi': base['operating_surplus_yi']})
    rows.sort(key=lambda r: (-r['valuation_official_yi'], r['bureau_id']))
    return {'year': 2025, 'seed': operating_rows[0]['seed'], 'rows': rows,
            'summary': {'bureauCount': len(rows),
                        'oldDcfTotalYi': sum(r['valuation_legacy_dcf_yi'] for r in rows),
                        'newTotalYi': sum(r['valuation_official_yi'] for r in rows),
                        'v02TotalYi': sum(r['valuation_v02_reference_yi'] for r in rows),
                        'v02ZeroCount': sum(r['valuation_v02_reference_yi'] == 0 for r in rows),
                        'lowValueCount': sum(r['valuation_low_value_option'] for r in rows),
                        'oldZeroCount': sum(r['valuation_legacy_dcf_yi'] == 0 for r in rows),
                        'newZeroCount': sum(r['valuation_at_floor'] for r in rows),
                        'cashTotalYi': sum(r['valuation_cash_yi'] for r in rows)}}


def continuity_check(operating_rows, cash_rows, national_rows, *, policy=None, quote_policy=None):
    """2025 counterfactual: fixed revenue/cash/future, move current cost across zero.

    These probes never replace real operating rows or their cost breakdown.
    Small +/- 0.0001 yi profits equal +/- 10,000 CNY around break-even.
    """
    base = min(operating_rows, key=lambda r: r['year'])
    points = []
    for surplus in (-.0001, 0., .0001):
        probe = [{**r, 'operating_surplus_yi': surplus, 'cost_yi': r['revenue_yi']-surplus}
                 if r['year'] == base['year'] else r for r in operating_rows]
        r = valuation_history(probe, cash_rows, national_rows, policy=policy, quote_policy=quote_policy,
                              as_of_years={base['year']})[0]
        points.append({'surplus_yi': surplus, 'value_yi': r['valuation_official_yi'],
                       'v02_value_yi': r['valuation_v02_reference_yi']})
    return {'year': base['year'], 'points': points,
            'newGapYi': abs(points[-1]['value_yi']-points[0]['value_yi']),
            'v02GapYi': abs(points[-1]['v02_value_yi']-points[0]['v02_value_yi'])}
