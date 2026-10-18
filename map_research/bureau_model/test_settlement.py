"""Net settlement semantics and isolation from existing operating costs."""
import copy
import math
import unittest

from economy_model.scenarios import simulate_scenario
from .operations import NORTH_PROFILE_PATH, finance, load_profiles, load_all_profiles, simulate_bureaus, validate_profiles
from .settlement import apply_hidden_freight
from .revenue import LINEAR_POLICY

PRICES={'energy_real_index':100.,'wage_real_index':100.,'materials_real_index':100.}


class SettlementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.profiles=load_profiles(NORTH_PROFILE_PATH)

    def core(self,p,fidx):
        return {'freight_index':fidx,**finance(p,PRICES,100,fidx,wage_peak_index=100)}

    def test_dynamic_net_receipts_and_separate_tonnes(self):
        p=next(p for p in self.profiles if p['bureau_id']=='datong')
        for index in (0,25,100,150,400):
            original=self.core(p,index); before=copy.deepcopy(original)
            result=apply_hidden_freight(original,p,revenue_policy=LINEAR_POLICY)
            self.assertEqual(original,before)
            self.assertEqual(result['freight_tons_10k'],original['freight_tons_10k'])
            self.assertAlmostEqual(result['hidden_freight_income_yi'],14.4*index/100)
            self.assertAlmostEqual(result['hidden_equivalent_freight_tons_10k']*41/10000,result['hidden_freight_income_yi'])
            for key in ('cost_yi','wage_cost_yi','energy_cost_yi','materials_cost_yi','other_cost_yi','station_income_yi','cost_breakdown','fixed_operating_cost_yi','volume_operating_cost_yi'):
                self.assertEqual(result[key],original[key])
            self.assertAlmostEqual(result['operating_surplus_yi'],original['operating_surplus_yi']+result['hidden_freight_income_yi'])
            self.assertAlmostEqual(result['revenue_yi'],sum(result[k+'_income_yi'] for k in ('passenger','freight','station')))
            with self.assertRaises(ValueError): apply_hidden_freight(result,p)

    def test_zero_scale_and_xiongan_baseline(self):
        for p in self.profiles:
            zero=copy.deepcopy(p);zero['hidden_freight']['settlement_scale']=0
            original=self.core(p,150)
            result=apply_hidden_freight(original,zero)
            self.assertEqual(result['operating_surplus_yi'],original['operating_surplus_yi'])
            self.assertEqual(result['hidden_equivalent_freight_tons_10k'],0)
        x=next(p for p in self.profiles if p['bureau_id']=='xiongan')
        base=apply_hidden_freight(self.core(x,100),x)
        self.assertEqual(base['passenger_trips_10k'],2000)
        self.assertAlmostEqual(base['operating_surplus_yi'],.04)
        self.assertEqual(base['hidden_freight_income_yi'],0)

    def test_invalid_settlement_config(self):
        for key,value in [('settlement_scale',-1),('settlement_scale',1.1),('settlement_scale',math.nan),
                          ('base_equivalent_tons_10k',1),('extra_modeled_cost_yi',.1),
                          ('station_income_increment_yi',.1),('volume_driver','national'),('demand_beta',2)]:
            bad=copy.deepcopy(self.profiles)
            bad[0]['hidden_freight'][key]=value
            with self.subTest(key=key,value=value),self.assertRaises(ValueError): validate_profiles(bad)

    def test_combined_catalog_keeps_northeast_results_and_prefix(self):
        all_profiles=load_all_profiles()
        self.assertEqual(len(all_profiles),62)
        macro=simulate_scenario(seed=20261014,years=5)
        combined=simulate_bureaus(macro,all_profiles)
        northeast_ids={p['bureau_id'] for p in load_profiles()}
        self.assertEqual([r for r in combined if r['bureau_id'] in northeast_ids],simulate_bureaus(macro))
        north_ids={p['bureau_id'] for p in self.profiles}
        north=[r for r in combined if r['bureau_id'] in north_ids and r['year_index']<=2]
        short=simulate_bureaus(simulate_scenario(seed=20261014,years=2),self.profiles)
        self.assertEqual(north,short)


if __name__=='__main__': unittest.main()
