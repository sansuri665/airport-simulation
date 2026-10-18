"""Southwest/South import provenance, economic scope and independent replay."""
import copy
import hashlib
import json
import unittest

from economy_model.scenarios import simulate_scenario
from .operations import SOUTH_PROFILE_PATH, load_profiles, load_all_profiles, simulate_bureaus


class SouthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.profiles=load_profiles(SOUTH_PROFILE_PATH)

    def test_provenance_and_regional_membership(self):
        root=SOUTH_PROFILE_PATH.parent.parent
        active=json.loads(SOUTH_PROFILE_PATH.read_text(encoding='utf-8'))
        self.assertRegex(active['source_sha256'],r'^[0-9a-f]{64}$')
        source=root/active['source_file']
        if source.is_file():
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),active['source_sha256'])
            self.assertEqual(self.profiles,json.loads(source.read_text(encoding='utf-8'))['bureau_profiles'])
        data=json.loads((root/'railway-economy-data.js').read_text(encoding='utf-8').split('=',1)[1].strip().rstrip(';'))
        for rid,count,net in [('southwest',12,5.59),('south',8,4.28)]:
            ps=[p for p in self.profiles if p['region_id']==rid]
            expected=next(r['divisions'] for r in data['regions'] if r['id']==rid)
            self.assertEqual({p['bureau_id'] for p in ps},set(expected))
            self.assertEqual(len(ps),count)
            self.assertAlmostEqual(sum(p['hidden_freight']['base_net_receipts_yi']*p['hidden_freight']['settlement_scale'] for p in ps),net)

    def test_causal_prefix_order_and_original42_independence(self):
        ps=load_all_profiles(); macro=simulate_scenario(seed=20261014,years=4)
        rows=simulate_bureaus(macro,ps)
        new_ids={p['bureau_id'] for p in self.profiles}
        new=[r for r in rows if r['bureau_id'] in new_ids]
        self.assertEqual(new,simulate_bureaus(macro,self.profiles))
        index=lambda rs:{(r['year_index'],r['bureau_id']):r for r in rs}
        self.assertEqual(index(new),index(simulate_bureaus(macro,list(reversed(self.profiles)))))
        self.assertEqual([r for r in new if r['year_index']<=2],simulate_bureaus(simulate_scenario(seed=20261014,years=2),self.profiles))
        self.assertEqual([r for r in rows if r['bureau_id'] not in new_ids],simulate_bureaus(macro,[p for p in ps if p['bureau_id'] not in new_ids]))

    def test_zero_net_income_and_no_cross_region_funding(self):
        macro=simulate_scenario(seed=0,years=1)
        before=simulate_bureaus(macro,self.profiles)
        changed=copy.deepcopy(self.profiles)
        for p in changed:
            if p['region_id']=='south':p['hidden_freight']['settlement_scale']=0.
        after=simulate_bureaus(macro,changed)
        sw_ids={p['bureau_id'] for p in changed if p['region_id']=='southwest'}
        self.assertEqual([r for r in before if r['bureau_id'] in sw_ids],[r for r in after if r['bureau_id'] in sw_ids])
        for r in before:
            if r['bureau_id']=='haikou':
                self.assertEqual(r['hidden_freight_income_yi'],0.)
                self.assertEqual(r['hidden_equivalent_freight_tons_10k'],0.)


if __name__=='__main__': unittest.main()
