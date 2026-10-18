"""Cash windows, causal loss estimates and separation from operating accounts."""
import copy
import unittest

from .cash import cash_ledger, load_config, money


class CashTests(unittest.TestCase):
    def setUp(self):
        self.opening, self.policy = load_config()
        self.one = {'bureaus': [{'bureau_id': 'lhasa', 'baseline_cash_yi': 9.59,
                                'audit_2025_operating_cost_yi': 21.55,
                                'audit_2025_operating_surplus_yi': -10.56}]}
        self.rows = [{'seed': 7, 'bureau_id': 'lhasa', 'year': y, 'cost_yi': 21.55,
                      'operating_surplus_yi': -10.56} for y in range(2025, 2030)]

    def test_opening_and_no_base_year_double_count(self):
        self.assertEqual(len(self.opening['bureaus']), 100)
        self.assertEqual(sum(money(b['baseline_cash_yi']) for b in self.opening['bureaus']), money(663.91))
        ledger, events = cash_ledger(self.rows[:1], self.one, self.policy)
        self.assertEqual(ledger[0]['cash_closing_yi'], 9.59)
        self.assertEqual(ledger[0]['cash_operating_proxy_yi'], 0)
        self.assertEqual(ledger[0]['cash_cumulative_equity_yi'], 0)
        self.assertFalse(events)

    def test_annual_target_and_cash_balance(self):
        before = copy.deepcopy(self.rows)
        ledger, events = cash_ledger(self.rows, self.one, self.policy)
        first = ledger[1]
        self.assertEqual(first['cash_carryover_yi'], 9.59)
        self.assertEqual(first['cash_projected_closing_before_funding_yi'], -.97)
        self.assertEqual(first['cash_trigger_yi'], 3.59)
        self.assertEqual(first['cash_target_yi'], 15.95)
        self.assertEqual(first['cash_state_equity_yi'], 6.36)
        self.assertEqual(first['cash_opening_yi'], 15.95)
        self.assertEqual(first['cash_closing_yi'], 5.39)
        self.assertEqual(first['cash_funding_year'], 2025)
        self.assertEqual(first['cash_estimate_basis_year'], 2025)
        self.assertEqual(ledger[2]['cash_state_equity_yi'], 10.56)
        self.assertEqual(ledger[2]['cash_closing_yi'], 5.39)
        self.assertEqual(self.rows, before)
        self.assertEqual(len(events), len({e['event_id'] for e in events}))
        self.assertTrue(all(e['event_type'] == 'annual_state_equity' and not e['counts_as_operating_revenue'] for e in events))
        for r in ledger:
            self.assertEqual(money(r['cash_opening_yi']), money(r['cash_carryover_yi']) + money(r['cash_state_equity_yi']))
            self.assertEqual(money(r['cash_closing_yi']), money(r['cash_opening_yi']) + money(r['cash_operating_proxy_yi']))
        self.assertTrue(all(e['funding_year'] == e['budget_year'] - 1 == e['estimate_basis_year'] for e in events))
        self.assertTrue(all(e['year'] == e['funding_year'] for e in events))

    def test_funding_cannot_see_budget_year_results(self):
        normal, _ = cash_ledger(self.rows, self.one, self.policy)
        surprise = copy.deepcopy(self.rows)
        surprise[1].update(cost_yi=1000, operating_surplus_yi=-1000)
        changed, events = cash_ledger(surprise, self.one, self.policy)
        for key in ('cash_state_equity_yi', 'cash_opening_yi', 'cash_trigger_yi', 'cash_target_yi', 'cash_expected_loss_yi'):
            self.assertEqual(changed[1][key], normal[1][key])
        self.assertEqual(changed[1]['cash_closing_yi'], -984.05)
        self.assertTrue(changed[1]['cash_negative_closing'])
        self.assertGreater(changed[2]['cash_state_equity_yi'], normal[2]['cash_state_equity_yi'])
        self.assertEqual(len([e for e in events if e['budget_year'] == 2026]), 1)

    def test_no_emergency_rescue_and_negative_cash_is_allowed(self):
        caps = {(y, 'lhasa'): 0 for y in range(2026, 2030)}
        ledger, events = cash_ledger(self.rows, self.one, self.policy, funding_caps=caps)
        self.assertFalse(events)
        self.assertEqual(ledger[1]['cash_closing_yi'], -.97)
        self.assertTrue(ledger[-1]['cash_negative_closing'])
        self.assertEqual(ledger[-1]['cash_cumulative_equity_yi'], 0)

    def test_causal_prefix_independent_of_future(self):
        short, _ = cash_ledger(self.rows[:3], self.one, self.policy)
        changed = copy.deepcopy(self.rows)
        changed[3]['operating_surplus_yi'] = -1000
        changed[4]['cost_yi'] = 1000
        long, _ = cash_ledger(changed, self.one, self.policy)
        self.assertEqual(short, long[:3])
        self.assertEqual(short, cash_ledger(list(reversed(self.rows[:3])), self.one, self.policy)[0])

    def test_profitable_cash_accumulates_without_dividends(self):
        opening = copy.deepcopy(self.one)
        opening['bureaus'][0]['audit_2025_operating_surplus_yi'] = 2
        rows = [{**r, 'operating_surplus_yi': 2} for r in self.rows]
        ledger, events = cash_ledger(rows, opening, {**self.policy, 'dividends': False})
        self.assertFalse(events)
        self.assertEqual(ledger[-1]['cash_closing_yi'], 17.59)

    def test_profit_and_excess_dividends_match_worked_example(self):
        opening = {'bureaus': [{'bureau_id': 'example', 'baseline_cash_yi': 940,
                               'audit_2025_operating_cost_yi': 150,
                               'audit_2025_operating_surplus_yi': 60}]}
        rows = [{'seed': 1, 'year': y, 'bureau_id': 'example', 'cost_yi': 150,
                 'operating_surplus_yi': 60} for y in (2025, 2026)]
        ledger, events = cash_ledger(rows, opening, self.policy)
        r = ledger[1]
        self.assertEqual(ledger[0]['cash_dividend_yi'], 0)
        self.assertEqual(r['cash_closing_before_dividends_yi'], 1000)
        self.assertEqual(r['cash_profit_dividend_yi'], 30)
        self.assertEqual(r['cash_excess_dividend_yi'], 410)
        self.assertEqual(r['cash_dividend_yi'], 440)
        self.assertEqual(r['cash_closing_yi'], 560)
        self.assertEqual(r['cash_cumulative_state_net_investment_yi'], -440)
        self.assertEqual(events[0]['event_type'], 'annual_shareholder_dividend')
        self.assertEqual(events[0]['year'], 2026)

    def test_dividends_respect_reserve_and_capital_freeze(self):
        opening = copy.deepcopy(self.one)
        opening['bureaus'][0]['audit_2025_operating_surplus_yi'] = 2
        rows = [{**r, 'operating_surplus_yi': 2} for r in self.rows]
        ledger, _ = cash_ledger(rows, opening, self.policy)
        self.assertEqual(ledger[1]['cash_profit_dividend_yi'], .81)
        self.assertEqual(ledger[1]['cash_closing_yi'], 10.78)
        changed = copy.deepcopy(self.rows)
        changed[1]['operating_surplus_yi'] = 100
        funded, _ = cash_ledger(changed, self.one, self.policy)
        self.assertGreater(funded[1]['cash_state_equity_yi'], 0)
        self.assertEqual(funded[1]['cash_dividend_yi'], 0)
        self.assertEqual(funded[1]['cash_dividend_status'], 'received_budget_year_equity')

    def test_dividends_disabled_in_loss_year_even_with_cash(self):
        opening = copy.deepcopy(self.one)
        opening['bureaus'][0]['baseline_cash_yi'] = 1000
        ledger, events = cash_ledger(self.rows, opening, self.policy)
        self.assertTrue(all(r['cash_dividend_yi'] == 0 for r in ledger))
        self.assertFalse(events)

    def test_reject_drift_missing_duplicate_and_nonfinite(self):
        for rows in [self.rows[1:], self.rows + self.rows[:1], self.rows[:2] + self.rows[3:],
                     [{**self.rows[0], 'cost_yi': 20}]]:
            with self.assertRaises(ValueError):
                cash_ledger(rows, self.one, self.policy)
        for value in (True, float('nan'), float('inf')):
            with self.assertRaises(ValueError):
                money(value)


if __name__ == '__main__':
    unittest.main()
