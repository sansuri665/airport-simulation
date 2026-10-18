"""Annual scheduled capital and cash, independent of operating accounts.

All companies initially nationally controlled. Year-end shareholder dividends
are separate from operations. No emergency rescue, custody, share changes or
interest. Cash may be negative.
"""
import hashlib
import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

from .revenue import config_hash as operating_config_hash

ROOT = Path(__file__).parent
OPENING_PATH = ROOT / 'cash_opening_v01.json'
POLICY_PATH = ROOT / 'cash_policy_v03.json'
VERSION = 'railway-bureau-annual-cash-dividends-v0.3'
CENT = Decimal('0.01')
ZERO = Decimal(0)


def money(value):
    if isinstance(value, bool):
        raise ValueError('Boolean is not cash')
    number = Decimal(str(value))
    if not number.is_finite():
        raise ValueError('Non-finite cash')
    return number.quantize(CENT, rounding=ROUND_HALF_UP)


def load_config():
    opening = json.loads(OPENING_PATH.read_text(encoding='utf-8'))
    policy = json.loads(POLICY_PATH.read_text(encoding='utf-8'))
    bureaus = opening['bureaus']
    ids = {b['bureau_id'] for b in bureaus}
    if len(bureaus) != 100 or len(ids) != 100:
        raise ValueError('Cash opening requires 100 unique bureaus')
    if any(money(b['baseline_cash_yi']) < 0 for b in bureaus):
        raise ValueError('Negative initial cash')
    if sum(money(b['baseline_cash_yi']) for b in bureaus) != money(opening['total_initial_cash_yi']):
        raise ValueError('Initial cash total mismatch')
    if (policy['emergency_funding'] or not policy['allow_negative_cash']
            or policy['opening_variation'] or policy['ownership_changes']):
        raise ValueError('Unsupported cash policy')
    if not 0 <= policy['trigger_reserve_months'] <= policy['target_reserve_months'] <= 12:
        raise ValueError('Invalid cash reserve months')
    if (policy['expected_loss_basis'] != 'previous_year_operating_result'
            or policy['annual_window'] != 'previous_year_end_for_budget_year'):
        raise ValueError('Cash cannot read future operating losses')
    d = policy['dividend_policy']
    if (not isinstance(policy['dividends'], bool)
            or not 0 <= d['profit_payout_ratio'] <= 1
            or not 0 <= d['excess_cash_payout_ratio'] <= 1
            or not 0 <= d['minimum_reserve_months'] <= d['comfortable_reserve_months'] <= 12
            or d['state_ownership_share'] != 1
            or not d['skip_if_nonpositive_surplus']
            or not d['skip_if_received_budget_year_equity']):
        raise ValueError('Unsupported dividend policy')
    return opening, policy


def config_hash():
    digest = hashlib.sha256(operating_config_hash().encode())
    for p in (OPENING_PATH, POLICY_PATH, Path(__file__)):
        digest.update(p.name.encode() + b'\0' + p.read_bytes() + b'\0')
    return digest.hexdigest()


def cash_ledger(operating_rows, opening, policy, *, funding_caps=None):
    """Read-only postprocessing. Caps are optional annual-window funding limits.

    Caps {(budget_year, bureau_id): amount} limit prior-year-end capital;
    they are an internal research interface, not an emergency funding source.
    Complete continuous histories from 2025 are required, including base rows.
    """
    profiles = {b['bureau_id']: b for b in opening['bureaus']}
    rows = list(operating_rows)
    if not rows:
        raise ValueError('Missing operating history')
    seed_set = {r['seed'] for r in rows}
    if len(seed_set) != 1:
        raise ValueError('Mixed seed histories')
    seed = next(iter(seed_set))
    lookup = {(r['year'], r['bureau_id']): r for r in rows}
    years = sorted({r['year'] for r in rows})
    if (len(lookup) != len(rows) or years != list(range(2025, years[-1] + 1))
            or set(lookup) != {(y, bid) for y in years for bid in profiles}):
        raise ValueError('Expected complete unique annual rows from 2025')
    for bid, p in profiles.items():
        base = lookup[2025, bid]
        for field, audit in [('cost_yi', 'audit_2025_operating_cost_yi'),
                             ('operating_surplus_yi', 'audit_2025_operating_surplus_yi')]:
            if abs(Decimal(str(base[field])) - Decimal(str(p[audit]))) > Decimal('0.025'):
                raise ValueError(f'Cash opening baseline drift: {bid}/{field}')
    funding_caps = funding_caps or {}
    for key, value in funding_caps.items():
        if key not in lookup or key[0] == 2025 or money(value) < 0:
            raise ValueError('Invalid annual funding cap')
    result, events = [], []
    for bid in sorted(profiles):
        initial = money(profiles[bid]['baseline_cash_yi'])
        balance, cumulative, operation_total, funded_years = initial, ZERO, ZERO, 0
        cumulative_dividends, dividend_years = ZERO, 0
        for year in years:
            r = lookup[year, bid]
            carryover = balance
            # A budget year's funding is completed at the previous year end.
            # Only information available then may determine the amount.
            basis_year = max(2025, year - 1)
            basis = lookup[basis_year, bid]
            cost = money(basis['cost_yi'])
            expected_surplus = money(basis['operating_surplus_yi'])
            if cost < 0:
                raise ValueError('Negative operating cost')
            floor = money(policy['minimum_reserve_yi'])
            trigger = max(floor, money(cost * Decimal(str(policy['trigger_reserve_months'])) / 12))
            loss = max(ZERO, -expected_surplus) * Decimal(str(policy['expected_loss_years']))
            target = max(trigger, money(cost * Decimal(str(policy['target_reserve_months'])) / 12 + loss))
            projected = carryover + expected_surplus
            requested = max(ZERO, target - carryover) if year > 2025 and projected < trigger else ZERO
            paid = min(requested, money(funding_caps.get((year, bid), requested)))
            start = carryover + paid
            # Base row remains the unfunded opening snapshot. The 2026 row
            # records its 2025-end funding once, without booking 2025 profit.
            proxy = ZERO if year == 2025 else money(r['operating_surplus_yi'])
            pre_dividend = start + proxy
            current_cost = money(r['cost_yi'])
            if current_cost < 0:
                raise ValueError('Negative operating cost')
            d = policy['dividend_policy']
            current_loss = max(ZERO, -proxy)
            minimum = max(floor, money(current_cost * Decimal(str(d['minimum_reserve_months'])) / 12 + current_loss))
            comfortable = max(minimum, money(current_cost * Decimal(str(d['comfortable_reserve_months'])) / 12 + current_loss))
            regular, excess = ZERO, ZERO
            if year == 2025:
                dividend_status = 'base_snapshot'
            elif not policy['dividends']:
                dividend_status = 'disabled'
            elif paid > 0:
                dividend_status = 'received_budget_year_equity'
            elif proxy <= 0:
                dividend_status = 'nonpositive_operating_surplus'
            else:
                available = max(ZERO, pre_dividend - minimum)
                regular = min(money(proxy * Decimal(str(d['profit_payout_ratio']))), available)
                excess = min(money(max(ZERO, pre_dividend - regular - comfortable)
                                   * Decimal(str(d['excess_cash_payout_ratio']))), available - regular)
                dividend_status = 'paid' if regular + excess > 0 else 'insufficient_cash_reserve'
            dividends = regular + excess
            balance = pre_dividend - dividends
            cumulative += paid
            cumulative_dividends += dividends
            operation_total += proxy
            funded_years += int(paid > 0)
            dividend_years += int(dividends > 0)
            entry = {
                'seed': seed, 'year': year, 'bureau_id': bid,
                'cash_initial_yi': float(initial), 'cash_carryover_yi': float(carryover),
                'cash_funding_year': year - 1 if year > 2025 else None,
                'cash_estimate_basis_year': basis_year if year > 2025 else None,
                'cash_opening_yi': float(start), 'cash_operating_proxy_yi': float(proxy),
                'cash_projected_closing_before_funding_yi': float(projected) if year > 2025 else float(initial),
                'cash_trigger_yi': float(trigger), 'cash_target_yi': float(target),
                'cash_expected_loss_yi': float(loss), 'cash_requested_equity_yi': float(requested),
                'cash_state_equity_yi': float(paid), 'cash_closing_yi': float(balance),
                'cash_closing_before_dividends_yi': float(pre_dividend),
                'cash_dividend_minimum_yi': float(minimum), 'cash_dividend_comfortable_yi': float(comfortable),
                'cash_profit_dividend_yi': float(regular), 'cash_excess_dividend_yi': float(excess),
                'cash_dividend_yi': float(dividends), 'cash_state_dividend_yi': float(dividends),
                'cash_dividend_status': dividend_status, 'cash_dividend_years': dividend_years,
                'cash_cumulative_dividend_yi': float(cumulative_dividends),
                'cash_cumulative_state_dividend_yi': float(cumulative_dividends),
                'cash_state_net_investment_yi': float(paid - dividends),
                'cash_cumulative_state_net_investment_yi': float(cumulative - cumulative_dividends),
                'cash_cumulative_equity_yi': float(cumulative),
                'cash_cumulative_operating_proxy_yi': float(operation_total),
                'cash_injection_years': funded_years,
                'cash_negative_carryover': carryover < 0,
                'cash_negative_closing': balance < 0,
            }
            result.append(entry)
            if balance != initial + operation_total + cumulative - cumulative_dividends:
                raise AssertionError('Cash does not reconcile')
            if dividends > 0 and (balance < minimum or paid > 0 or proxy <= 0):
                raise AssertionError('Dividend eligibility or reserve violated')
            if paid > 0:
                events.append({'event_id': f'{seed}-{year}-{bid}-annual-state-equity',
                               'seed': seed, 'year': year - 1, 'funding_year': year - 1,
                               'budget_year': year, 'estimate_basis_year': basis_year, 'bureau_id': bid,
                               'event_type': 'annual_state_equity', 'amount_yi': float(paid),
                               'cash_flow_direction': 'in', 'recipient': bid,
                               'counts_as_operating_revenue': False,
                               'changes_ownership': False})
            if dividends > 0:
                events.append({'event_id': f'{seed}-{year}-{bid}-annual-shareholder-dividend',
                               'seed': seed, 'year': year, 'funding_year': None,
                               'budget_year': year, 'estimate_basis_year': year, 'bureau_id': bid,
                               'event_type': 'annual_shareholder_dividend', 'amount_yi': float(dividends),
                               'cash_flow_direction': 'out', 'recipient': 'national_rail',
                               'counts_as_operating_revenue': False, 'changes_ownership': False})
    # At a calendar year end, dividends precede the next budget year's funding.
    events.sort(key=lambda e: (e['year'], e['event_type'] == 'annual_state_equity', e['bureau_id']))
    return sorted(result, key=lambda r: (r['year'], r['bureau_id'])), events
