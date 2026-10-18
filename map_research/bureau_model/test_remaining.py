"""Final 38-bureau source parameters, full map membership and stable replay."""
import hashlib
import json
import unittest

from economy_model.scenarios import simulate_scenario
from .operations import REMAINING_PROFILE_PATH, load_profiles, load_all_profiles, simulate_bureaus


class RemainingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.profiles=load_profiles(REMAINING_PROFILE_PATH)

    def test_provenance_and_complete_100_bureau_membership(self):
        root=REMAINING_PROFILE_PATH.parent.parent
        active=json.loads(REMAINING_PROFILE_PATH.read_text(encoding='utf-8'))
        self.assertRegex(active['source_sha256'],r'^[0-9a-f]{64}$')
        source=root/active['source_file']
        if source.is_file():
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),active['source_sha256'])
            self.assertEqual(self.profiles,json.loads(source.read_text(encoding='utf-8'))['bureau_profiles'])
        data=json.loads((root/'railway-economy-data.js').read_text(encoding='utf-8').split('=',1)[1].strip().rstrip(';'))
        all_profiles=load_all_profiles()
        self.assertEqual(len(all_profiles),100)
        self.assertEqual({p['bureau_id'] for p in all_profiles},{bid for r in data['regions'] for bid in r['divisions']})
        for rid,count,net in [('central',11,5.45),('east',14,14.85),('southeast',13,9.25)]:
            ps=[p for p in self.profiles if p['region_id']==rid]
            self.assertEqual(len(ps),count)
            self.assertEqual({p['bureau_id'] for p in ps},set(next(r['divisions'] for r in data['regions'] if r['id']==rid)))
            self.assertAlmostEqual(sum(p['hidden_freight']['base_net_receipts_yi']*p['hidden_freight']['settlement_scale'] for p in ps),net)

    def test_subset_order_prefix_and_original62_unchanged(self):
        ps=load_all_profiles(); macro=simulate_scenario(seed=20261014,years=4)
        rows=simulate_bureaus(macro,ps)
        ids={p['bureau_id'] for p in self.profiles}
        new=[r for r in rows if r['bureau_id'] in ids]
        self.assertEqual(new,simulate_bureaus(macro,self.profiles))
        index=lambda rs:{(r['year_index'],r['bureau_id']):r for r in rs}
        self.assertEqual(index(new),index(simulate_bureaus(macro,list(reversed(self.profiles)))))
        self.assertEqual([r for r in new if r['year_index']<=2],simulate_bureaus(simulate_scenario(seed=20261014,years=2),self.profiles))
        old=[p for p in ps if p['bureau_id'] not in ids]
        self.assertEqual(len(old),62)
        self.assertEqual([r for r in rows if r['bureau_id'] not in ids],simulate_bureaus(macro,old))


if __name__=='__main__': unittest.main()
