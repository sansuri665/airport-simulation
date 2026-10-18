"""Yield behavior and independent net-receipt accounting, without pool coupling."""
import copy
import math
import unittest

from economy_model.scenarios import simulate_scenario
from .operations import finance, load_all_profiles, simulate_bureaus
from .revenue import CURRENT_POLICY, LINEAR_POLICY, unit_yield, validate_policy
from .settlement import apply_hidden_freight

PRICES = {'energy_real_index':100.,'wage_real_index':100.,'materials_real_index':100.}


class RevenueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.profiles = load_all_profiles()

    def test_independent_baseline_income_not_zero_sum(self):
        macro = simulate_scenario(seed=0, years=0)
        current = simulate_bureaus(macro, self.profiles)
        totals = {rid:sum(r['hidden_freight_income_yi'] for r,p in zip(current,self.profiles) if p['region_id']==rid)
                  for rid in ('northeast','north')}
        self.assertAlmostEqual(totals['northeast'],8.)
        self.assertAlmostEqual(totals['north'],63.)
        old_ids = {p['bureau_id'] for p in self.profiles if p['region_id'] in ('northeast','north')}
        self.assertAlmostEqual(sum(r['operating_surplus_yi'] for r in current if r['bureau_id'] in old_ids),93.05)
        for r,p in zip(current,self.profiles):
            no_net = finance(p,PRICES,100,100,wage_peak_index=100,revenue_policy=LINEAR_POLICY)
            self.assertAlmostEqual(r['core_operating_surplus_yi'],no_net['operating_surplus_yi'])

    def test_yield_changes_income_only_and_applies_once(self):
        p = self.profiles[0]
        for f in (0,.1,.8,1.,1.2,2.,10.):
            a = finance(p,PRICES,120,f*100,wage_peak_index=100,revenue_policy=LINEAR_POLICY)
            b = finance(p,PRICES,120,f*100,wage_peak_index=100)
            expected = min(1.15,max(.85,f**.15))
            self.assertAlmostEqual(b['freight_income_yi'],p['finance_base_yi']['freight_revenue']*f*expected)
            w = p['station_revenue_passenger_share']
            self.assertAlmostEqual(b['station_income_yi'],p['finance_base_yi']['station_revenue']*
                                   (w*1.2*1.2**.1+(1-w)*f*min(1.1,max(.9,f**.1))))
            for key in ('cost_breakdown','passenger_trips_10k','freight_tons_10k','passenger_income_yi'):
                self.assertEqual(a[key],b[key])
            row = apply_hidden_freight({'freight_index':f*100,**b},p)
            self.assertAlmostEqual(row['hidden_freight_income_yi'],.8*f*expected)
            self.assertAlmostEqual(row['hidden_equivalent_freight_tons_10k']*
                                   p['hidden_freight']['accounting_yield_yuan_per_ton']/10000,row['hidden_freight_income_yi'])
            if f==0: self.assertEqual(row['hidden_freight_income_yi'],0)

    def test_other_region_profiles_and_requested_subset_cannot_change_receipts(self):
        macro = simulate_scenario(seed=20261014,years=3)
        baseline = simulate_bureaus(macro,self.profiles)
        changed = copy.deepcopy(self.profiles)
        for p in changed:
            if p['region_id']=='north': p['hidden_freight']['settlement_scale']=0.
        actual = simulate_bureaus(macro,changed)
        ne = {p['bureau_id'] for p in changed if p['region_id']=='northeast'}
        selected = lambda rows:[r for r in rows if r['bureau_id'] in ne]
        self.assertEqual(selected(baseline),selected(actual))
        self.assertEqual(selected(baseline),simulate_bureaus(macro,[p for p in self.profiles if p['bureau_id'] in ne]))
        self.assertGreater(sum(r['hidden_freight_income_yi'] for r in baseline),sum(r['hidden_freight_income_yi'] for r in actual))

    def test_policy_validation_and_toggles(self):
        for key,value in [('freight_exponent',math.nan),('freight_exponent',-.1),('station_floor',1.1),
                          ('freight_ceiling',.9),('station_exponent',True),('settlement_uses_freight_yield',1),
                          ('settlement_basis','pool')]:
            with self.subTest(key=key),self.assertRaises(ValueError): validate_policy({**CURRENT_POLICY,key:value})
        for q in (-1,math.nan,math.inf,True):
            with self.assertRaises(ValueError): unit_yield(q,'freight',CURRENT_POLICY)
        self.assertEqual(unit_yield(2.,'freight',LINEAR_POLICY),1.)
        p = self.profiles[0]
        r = finance(p,PRICES,100,200,wage_peak_index=100)
        result = apply_hidden_freight({'freight_index':200.,**r},p,
                                     revenue_policy={**CURRENT_POLICY,'settlement_uses_freight_yield':False})
        self.assertAlmostEqual(result['hidden_freight_income_yi'],1.6)


if __name__=='__main__': unittest.main()
