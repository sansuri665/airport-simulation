"""Northwest provenance, region membership and causal integration."""
import hashlib
import json
import unittest

from economy_model.scenarios import simulate_scenario
from .operations import NORTHWEST_PROFILE_PATH, load_profiles, load_all_profiles, simulate_bureaus


class NorthwestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.profiles=load_profiles(NORTHWEST_PROFILE_PATH)

    def test_provenance_and_economic_region_membership(self):
        root=NORTHWEST_PROFILE_PATH.parent.parent
        active=json.loads(NORTHWEST_PROFILE_PATH.read_text(encoding='utf-8'))
        self.assertRegex(active['source_sha256'],r'^[0-9a-f]{64}$')
        source_path=root/active['source_file']
        # The reviewed candidate is optional local input, not a runtime dependency.
        if source_path.is_file():
            self.assertEqual(hashlib.sha256(source_path.read_bytes()).hexdigest(),active['source_sha256'])
            self.assertEqual(self.profiles,json.loads(source_path.read_text(encoding='utf-8'))['bureau_profiles'])
        text=(root/'railway-economy-data.js').read_text(encoding='utf-8')
        data=json.loads(text.split('=',1)[1].strip().rstrip(';'))
        expected=next(r['divisions'] for r in data['regions'] if r['id']=='northwest')
        self.assertEqual({p['bureau_id'] for p in self.profiles},set(expected))
        self.assertEqual(len(self.profiles),20)
        self.assertAlmostEqual(sum(p['hidden_freight']['base_net_receipts_yi'] for p in self.profiles),11.14)

    def test_subset_order_and_prefix_and_existing_bureaus(self):
        all_profiles=load_all_profiles()
        macro=simulate_scenario(seed=20261014,years=5)
        combined=simulate_bureaus(macro,all_profiles)
        ids={p['bureau_id'] for p in self.profiles}
        nw=[r for r in combined if r['bureau_id'] in ids]
        self.assertEqual(nw,simulate_bureaus(macro,self.profiles))
        index=lambda rows:{(r['year_index'],r['bureau_id']):r for r in rows}
        self.assertEqual(index(nw),index(simulate_bureaus(macro,list(reversed(self.profiles)))))
        short=simulate_bureaus(simulate_scenario(seed=20261014,years=2),self.profiles)
        self.assertEqual(short,[r for r in nw if r['year_index']<=2])
        old=[p for p in all_profiles if p['bureau_id'] not in ids]
        self.assertEqual([r for r in combined if r['bureau_id'] not in ids],simulate_bureaus(macro,old))


if __name__=='__main__': unittest.main()
