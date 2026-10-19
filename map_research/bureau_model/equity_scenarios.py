"""Continuous, read-only scenario equity pricing; no real capital/share events.

Two ex-ante strategies share the SAME company cash paths: passive dilution or
full proportional funding. Only the latter pays the new capital. No hindsight
selection between strategies inside individual sampled futures.
"""
import hashlib
import math
import random
from functools import lru_cache


@lru_cache(maxsize=256)
def innovations(seed, bureau_id, count):
    # Reuse innovations across as-of dates and profitability-boundary probes.
    rng = random.Random(int.from_bytes(hashlib.sha256(
        f'unified-equity-v0.1|{seed}|{bureau_id}|{count}'.encode()).digest(), 'big'))
    result = []
    for _ in range(count // 2):
        common, drift = rng.gauss(0, 1), rng.gauss(0, 1)
        shock = tuple(math.sqrt((i+1)/10) * (.85*common + .35*drift*(i+1)/10
                      + .25*rng.gauss(0, 1)) for i in range(10))
        result.extend((shock, tuple(-v for v in shock)))
    return tuple(result)


def path_equity(values, costs, revenue, cash, previous_surplus, previous_cost, rate, policy):
    """Present values for one path. All max/min operations are continuous.

    Financing is a continuous reserve-gap proxy, not the cash V0.3 actual annual
    window. New capital buys shares at a positive revenue/earnings reference;
    old holders are never silently wiped out at a zero issue price.
    """
    p = policy['equity_scenarios']
    discounts = [(1+rate)**i for i in range(1, 11)]
    retention, passive_div, all_div, funding_pv, total_funding = 1., 0., 0., 0., 0.
    for i, (surplus, cost) in enumerate(zip(values, costs)):
        reserve = max(p['minimum_cash_reserve_yi'], previous_cost*p['funding_reserve_months']/12)
        funding = max(0., reserve-cash-previous_surplus)
        # Known pre-financing cash and profit only; never this path's future.
        rights_reference = max(revenue*p['franchise_revenue_multiple'], previous_surplus/rate)
        pre_money = max(revenue*p['franchise_revenue_multiple'], cash+rights_reference)
        if funding:
            retention *= pre_money/(pre_money+funding)
        cash += funding + surplus
        total_funding += funding
        # Funding occurs at the start of the prospective year, before its profit.
        funding_pv += funding/(1+rate)**i
        minimum = max(p['minimum_cash_reserve_yi'], cost*p['dividend_reserve_months']/12)
        available = max(0., cash-minimum)
        regular = min(p['profit_payout_ratio']*max(surplus, 0.), available)
        excess = min(p['excess_cash_payout_ratio']*max(0., cash-regular-cost), max(0., available-regular))
        dividend = regular+excess
        cash -= dividend
        all_div += dividend/discounts[i]
        passive_div += retention*dividend/discounts[i]
        previous_surplus, previous_cost = surplus, cost
    normal_profit = sum(v*w for v, w in zip(reversed(values[-3:]), policy['terminal_profit_weights']))
    # A single terminal rule across negative, zero and positive margins. The
    # profitability diagnostic threshold below NEVER changes the cash payoff.
    terminal_right = max(revenue*p['franchise_revenue_multiple'], normal_profit/rate)
    residual = max(0., cash+terminal_right)/discounts[-1]
    passive_residual = retention*residual
    profitable = all(v > 0 for v in values[-3:]) and normal_profit >= revenue*p['sustained_margin_min']
    return {'passive': passive_div+passive_residual,
            'follow': all_div+residual-funding_pv,
            'passive_div': passive_div, 'passive_residual': passive_residual,
            'all_div': all_div, 'all_residual': residual,
            'funding_pv': funding_pv, 'funding': total_funding,
            'retention': retention, 'profitable': profitable}


def scenario_equity(values, costs, revenue, cash, previous_surplus, previous_cost, rate,
                    *, seed, bureau_id, policy):
    p = policy['equity_scenarios']
    if (len(values) != 10 or len(costs) != 10 or revenue <= 0 or rate <= 0
            or any(not math.isfinite(v) for v in list(values)+list(costs)+[revenue, cash, previous_surplus, previous_cost, rate])
            or any(c <= 0 for c in costs)):
        raise ValueError('Invalid scenario equity inputs')
    sigma = revenue*p['terminal_margin_sigma']*(100-policy['expected_score'])/30
    totals = dict.fromkeys(('passive','follow','passive_div','passive_residual','all_div',
                           'all_residual','funding_pv','funding','retention'), 0.)
    profit_count, passive_profitable, follow_profitable, negative_pv = 0, 0., 0., 0.
    draws = innovations(seed, bureau_id, p['scenario_count']) if sigma else ((0.,)*10,)
    for shock in draws:
        path = [max(-cost, value+sigma*z) for value, cost, z in zip(values, costs, shock)]
        result = path_equity(path, costs, revenue, cash, previous_surplus, previous_cost, rate, policy)
        for key in totals:
            totals[key] += result[key]
        negative_pv += sum(max(0., -v)/(1+rate)**(i+1) for i, v in enumerate(path))
        if result['profitable']:
            profit_count += 1
            passive_profitable += result['passive']
            follow_profitable += result['follow']
    n = len(draws)
    avg = {key: value/n for key, value in totals.items()}
    follow = avg['follow'] > avg['passive']
    value = max(0., avg['follow'] if follow else avg['passive'])
    contribution = (follow_profitable if follow else passive_profitable)/n
    return {'valuation_official_yi': value,
            'valuation_method': 'unified_scenario_equity',
            'valuation_strategy': 'follow' if follow else 'passive',
            'valuation_passive_equity_yi': avg['passive'],
            'valuation_follow_equity_yi': avg['follow'],
            'valuation_dividends_pv_yi': avg['all_div'] if follow else avg['passive_div'],
            'valuation_residual_pv_yi': avg['all_residual'] if follow else avg['passive_residual'],
            'valuation_own_funding_pv_yi': avg['funding_pv'] if follow else 0.,
            'valuation_expected_funding_pv_yi': avg['funding_pv'],
            'valuation_expected_funding_yi': avg['funding'],
            'valuation_expected_retention': avg['retention'],
            'valuation_recovery_probability': profit_count/n,
            'valuation_recovery_contribution_yi': contribution,
            'valuation_distress_contribution_yi': value-contribution,
            'valuation_transition_loss_pv_yi': negative_pv/n,  # Diagnostic, never deducted again.
            'valuation_loss_scenario_count': p['scenario_count'],
            'valuation_normalized_revenue_yi': revenue,
            'valuation_low_value_option': value < revenue*p['low_value_revenue_ratio']}
