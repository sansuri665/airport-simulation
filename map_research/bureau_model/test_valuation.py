"""Locked errors, DCF identity, standing quotes and no operating mutations."""
import copy
import unittest

from .valuation import load_config, locked_forecast, quotation, valuation_history


class ValuationTests(unittest.TestCase):
    def setUp(self):
        self.p, self.q = load_config()
        self.ops = [{'seed': 7, 'bureau_id': 'example', 'year': y, 'cost_yi': 100.,
                     'operating_surplus_yi': 10.} for y in range(2025, 2086)]
        self.cash = [{'seed': 7, 'bureau_id': 'example', 'year': y, 'cash_closing_yi': 20.} for y in range(2025, 2086)]
        self.national = [{'calendar_year': y, 'rate': 2.} for y in range(2025, 2086)]

    def test_locked_forecast_scores_and_signed_values(self):
        values = [-20., -5., 0., 2., 10.] * 2
        f = locked_forecast(values, [100.] * 10, seed=7, bureau_id='example', year=2030, policy=self.p)
        self.assertEqual(f, locked_forecast(values, [100.] * 10, seed=7, bureau_id='example', year=2030, policy=self.p))
        self.assertGreaterEqual(f['actual_score'], 66)
        self.assertLessEqual(f['actual_score'], 74)
        self.assertGreaterEqual(f['one_year_score'], 66)
        self.assertLessEqual(f['one_year_score'], 74)
        self.assertLess(f['values'][0], 0)
        self.assertNotEqual(f['values'], locked_forecast(values, [100.] * 10, seed=8, bureau_id='example', year=2030, policy=self.p)['values'])

    def test_perfect_forecast_and_constant_perpetuity(self):
        p = {**self.p, 'expected_score': 100}
        rows = valuation_history(self.ops, self.cash, self.national, policy=p, quote_policy=self.q)
        self.assertAlmostEqual(rows[0]['valuation_official_yi'], 10 / .08 + 20)
        self.assertAlmostEqual(rows[0]['valuation_full_future_reference_yi'], rows[0]['valuation_official_yi'])
        self.assertEqual(rows[0]['valuation_forecast_score'], 100)
        self.assertEqual(rows[-1]['valuation_tail_years'], 10)
        self.assertAlmostEqual(rows[-1]['valuation_official_yi'], rows[0]['valuation_official_yi'])

    def test_cash_updates_without_redrawing_forecast(self):
        before = copy.deepcopy((self.ops, self.cash, self.national))
        a = valuation_history(self.ops, self.cash, self.national)
        changed = [{**r, 'cash_closing_yi': 70.} for r in self.cash]
        b = valuation_history(self.ops, changed, self.national)
        for x, y in zip(a, b):
            self.assertEqual(x['forecastRows'], y['forecastRows'])
            self.assertAlmostEqual(y['valuation_official_yi'] - x['valuation_official_yi'], 50)
            self.assertAlmostEqual(y['valuation_old_share_state_bid_yi'] - x['valuation_old_share_state_bid_yi'], 30)
        self.assertEqual(before, (self.ops, self.cash, self.national))

    def test_quote_bands_and_unconditional_bid(self):
        for cash, multiplier, band in [(50, .9, 'comfortable'), (49, .85, 'watch'),
                                       (100/6, .85, 'watch'), (0, .8, 'strained_before_formal_crisis')]:
            quote = quotation(100, cash, 0, 100, self.q)
            self.assertEqual(quote['valuation_issue_multiplier'], multiplier)
            self.assertEqual(quote['valuation_active_band'], band)
            self.assertEqual(quote['valuation_old_share_state_bid_yi'], 60)
            self.assertEqual(quote['valuation_old_share_ask_yi'], 105)
        self.assertTrue(self.q['merchant']['old_share_bid_unconditional'])

    def test_negative_right_value_and_equity_floor(self):
        ops = [{**r, 'operating_surplus_yi': -20.} for r in self.ops]
        rows = valuation_history(ops, self.cash, self.national, policy={**self.p, 'expected_score': 100}, quote_policy=self.q)
        self.assertLess(rows[0]['valuation_operating_right_yi'], 0)
        self.assertEqual(rows[0]['valuation_official_yi'], 0)
        self.assertEqual(rows[0]['valuation_old_share_state_bid_yi'], 0)
        self.assertTrue(rows[0]['valuation_at_floor'])

    def test_longer_history_preserves_unaffected_windows(self):
        short = valuation_history(self.ops[:31], self.cash[:31], self.national)
        full = valuation_history(self.ops, self.cash, self.national)
        self.assertEqual(short[:21], full[:21])
        bad = copy.deepcopy(self.cash)
        bad[0]['seed'] = 8
        with self.assertRaises(ValueError):
            valuation_history(self.ops, bad, self.national)


if __name__ == '__main__':
    unittest.main()
