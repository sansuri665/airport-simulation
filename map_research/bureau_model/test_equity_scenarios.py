"""Unified prices: boundary continuity, limited liability, funding and replay."""
import copy
import unittest
from unittest.mock import patch

from .valuation import load_config, valuation_history, continuity_check
from .equity_scenarios import path_equity, scenario_equity, innovations


class EquityScenarioTests(unittest.TestCase):
    def setUp(self):
        self.p, self.q = load_config()
        self.ops = [{'seed':7,'bureau_id':'example','year':y,'cost_yi':100.,'revenue_yi':110.,
                     'operating_surplus_yi':10.} for y in range(2025,2086)]
        self.cash = [{'seed':7,'bureau_id':'example','year':y,'cash_closing_yi':20.} for y in range(2025,2086)]
        self.national = [{'calendar_year':y,'rate':2.} for y in range(2025,2086)]

    def value(self, ops=None, cash=None, policy=None):
        return valuation_history(self.ops if ops is None else ops,self.cash if cash is None else cash,
                                 self.national,policy=policy,quote_policy=self.q,as_of_years={2025})[0]

    def test_perfect_no_reserve_constant_perpetuity(self):
        p=copy.deepcopy(self.p);p['expected_score']=100
        p['equity_scenarios'].update(minimum_cash_reserve_yi=0,funding_reserve_months=0,
                                     dividend_reserve_months=0,profit_payout_ratio=1)
        a=self.value(cash=[{**r,'cash_closing_yi':0.} for r in self.cash],policy=p)
        self.assertAlmostEqual(a['valuation_official_yi'],10/.08)
        self.assertEqual(a['valuation_official_yi'],a['valuation_full_future_reference_yi'])
        self.assertEqual(a['valuation_expected_funding_yi'],0)

    def test_cash_updates_financing_not_random_samples(self):
        before=copy.deepcopy((self.ops,self.cash,self.national))
        a=self.value();b=self.value(cash=[{**r,'cash_closing_yi':70.} for r in self.cash])
        self.assertEqual(a['forecastRows'],b['forecastRows'])
        self.assertEqual(a['valuation_recovery_probability'],b['valuation_recovery_probability'])
        self.assertGreater(b['valuation_official_yi'],a['valuation_official_yi'])
        self.assertLessEqual(b['valuation_expected_funding_yi'],a['valuation_expected_funding_yi'])
        self.assertEqual(before,(self.ops,self.cash,self.national))
        z=innovations(7,'example',512)
        self.assertEqual(z,innovations(7,'example',512))
        self.assertEqual(z[0],tuple(-v for v in z[1]))

    def test_heavy_loss_keeps_only_small_diluted_residual(self):
        ops=[{**r,'operating_surplus_yi':-20.,'revenue_yi':80.} for r in self.ops]
        a=self.value(ops=ops,policy={**self.p,'expected_score':100})
        self.assertEqual(a['valuation_v02_reference_yi'],0)
        self.assertTrue(0<a['valuation_official_yi']<1)
        self.assertLess(a['valuation_expected_retention'],.01)
        self.assertGreater(a['valuation_expected_funding_yi'],0)
        self.assertLess(a['valuation_follow_equity_yi'],0)
        self.assertEqual(a['valuation_strategy'],'passive')

    def test_accounting_no_second_cash_or_loss_addition(self):
        a=self.value()
        self.assertEqual(a['valuation_method'],'unified_scenario_equity')
        self.assertAlmostEqual(a['valuation_official_yi'],max(0,a['valuation_passive_equity_yi'],a['valuation_follow_equity_yi']))
        self.assertAlmostEqual(a['valuation_official_yi'],a['valuation_dividends_pv_yi']+a['valuation_residual_pv_yi']-a['valuation_own_funding_pv_yi'])
        self.assertAlmostEqual(a['valuation_official_yi'],a['valuation_recovery_contribution_yi']+a['valuation_distress_contribution_yi'])
        self.assertEqual(a['valuation_own_funding_pv_yi'],a['valuation_expected_funding_pv_yi'] if a['valuation_strategy']=='follow' else 0)

    def test_follow_cost_paid_once_passive_dilution(self):
        a=path_equity([-10.]*10,[100.]*10,90.,20.,-10.,100.,.08,self.p)
        self.assertGreater(a['funding_pv'],0)
        self.assertAlmostEqual(a['follow'],a['all_div']+a['all_residual']-a['funding_pv'])
        self.assertAlmostEqual(a['passive'],a['passive_div']+a['retention']*a['all_residual'])
        self.assertTrue(0<a['retention']<1)

    def test_no_hindsight_strategy_selection(self):
        p=copy.deepcopy(self.p);p['equity_scenarios']['scenario_count']=2
        draws=((2.,)*10,(-2.,)*10)
        paths=[[max(-100.,v+100*.12*z) for v,z in zip([2.]*10,shock)] for shock in draws]
        outcomes=[path_equity(v,[100.]*10,100.,0.,-10.,100.,.08,p) for v in paths]
        expected=max(0,sum(x['passive'] for x in outcomes)/2,sum(x['follow'] for x in outcomes)/2)
        with patch('bureau_model.equity_scenarios.innovations',return_value=draws):
            a=scenario_equity([2.]*10,[100.]*10,100.,0.,-10.,100.,.08,seed=7,bureau_id='example',policy=p)
        self.assertAlmostEqual(a['valuation_official_yi'],expected)
        self.assertLess(expected,sum(max(x['passive'],x['follow'],0) for x in outcomes)/2)

    def test_current_profit_crossing_zero(self):
        check=continuity_check(self.ops,self.cash,self.national)
        self.assertLess(check['newGapYi'],.01)
        values=[r['value_yi'] for r in check['points']]
        self.assertLessEqual(values[0],values[1]);self.assertLessEqual(values[1],values[2])

    def test_profitability_label_does_not_change_payoff_rule(self):
        args=([100.]*10,100.,50.,3.,100.,.08,self.p)
        lo=path_equity([3.-1e-7]*10,*args);hi=path_equity([3.+1e-7]*10,*args)
        self.assertFalse(lo['profitable']);self.assertTrue(hi['profitable'])
        self.assertLess(abs(hi['passive']-lo['passive']),.0001)

    def test_unaffected_history_prefix(self):
        a=valuation_history(self.ops[:31],self.cash[:31],self.national,as_of_years={2025,2045})
        b=valuation_history(self.ops,self.cash,self.national,as_of_years={2025,2045})
        self.assertEqual(a,b)


if __name__=='__main__':unittest.main()
