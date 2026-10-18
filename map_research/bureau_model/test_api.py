"""Local research endpoint contracts: py -3 -m unittest bureau_model.test_api."""
import json
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import urlopen

from serve import Handler, ThreadingHTTPServer


class QuietHandler(Handler):
    def log_message(self, *args):
        pass


class BureauAPITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), QuietHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.root = f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def fetch(self, path):
        with urlopen(self.root + path, timeout=10) as response:
            return json.load(response)

    def test_catalog_only_enables_configured_regions(self):
        catalog = self.fetch('/api/bureau-catalog')
        self.assertEqual(len(catalog['regions']), 8)
        self.assertEqual(len(catalog['bureaus']), 62)
        self.assertEqual({b['region_id'] for b in catalog['bureaus']}, {'northeast','north','northwest','southwest','south'})

    def test_seed_validation_and_unconfigured_bureau(self):
        for path in ('?seed=-1', '?seed=', '?seed=9007199254740992', '?seed=1&seed=2', '?bureau=wuhan', '?bureau=jiamusi&bureau=harbin'):
            with self.subTest(path=path), self.assertRaises(HTTPError) as error:
                self.fetch('/api/bureau' + path)
            self.assertEqual(error.exception.code, 400)

    def test_full_series_replay_and_accounts(self):
        path = '/api/bureau?seed=20261014&bureau=jiamusi'
        data = self.fetch(path)
        self.assertEqual(data, self.fetch(path))
        self.assertEqual([r['year'] for r in data['rows']], list(range(2025, 2086)))
        self.assertEqual(len(data['regionalPrices']), 61)
        self.assertEqual(len(data['bureauConfigHash']), 64)
        self.assertAlmostEqual(data['rows'][0]['cost_yi'], 10.65)
        self.assertEqual(data['modelVersion'], 'railway-bureau-operations-v0.4')
        self.assertIsNotNone(data['calibrationAudit'])
        self.assertEqual(data['calibrationAudit']['configHash'],data['bureauConfigHash'])
        self.assertEqual(data['calibrationAudit']['seedCount'],96)
        self.assertEqual(len(data['calibrationAudit']['bureaus']),12)
        self.assertAlmostEqual(data['rows'][0]['hidden_freight_income_yi'],.8)
        peak=100.
        for row in data['rows']:
            self.assertEqual(row['bureau_id'], 'jiamusi')
            self.assertAlmostEqual(row['cost_yi'], sum(row[k + '_cost_yi'] for k in ('energy', 'wage', 'materials', 'other')))
            peak=max(peak,row['regional_wage_index'])
            self.assertEqual(row['historical_wage_peak_index'],peak)
            self.assertAlmostEqual(row['operating_surplus_yi']-row['v02_operating_surplus_yi'],row['v02_wage_cost_yi']-row['wage_cost_yi'])
        # The existing macro endpoint must still carry the same seed/version.
        macro = self.fetch('/api/economy?seed=20261014')
        self.assertEqual(macro['modelVersion'], data['macroModelVersion'])
        self.assertEqual(macro['configHash'], data['macroConfigHash'])
        self.assertNotIn('regional_development_paths', data)

    def test_north_volume_semantics_and_matching_audit(self):
        data=self.fetch('/api/bureau?seed=20261014&bureau=datong')
        self.assertEqual(data['profile']['region_id'],'north')
        self.assertEqual(data['calibrationAudit']['seedCount'],96)
        self.assertEqual(len(data['calibrationAudit']['bureaus']),10)
        self.assertEqual(data['profile']['hidden_freight']['settlement_scale'],.9)
        base=data['rows'][0]
        self.assertEqual(base['freight_tons_10k'],6000)
        self.assertEqual(base['ordinary_freight_tons_10k'],6000)
        self.assertAlmostEqual(base['hidden_freight_income_yi'],14.4)
        self.assertAlmostEqual(base['operating_surplus_yi'],18.11)
        for r in data['rows']:
            self.assertEqual(r['freight_tons_10k'],r['ordinary_freight_tons_10k'])
            self.assertAlmostEqual(r['freight_income_yi'],r['ordinary_freight_income_yi']+r['hidden_freight_income_yi'])
            self.assertAlmostEqual(r['hidden_freight_income_yi'],14.4*r['freight_index']/100*r['settlement_unit_yield_factor'])

    def test_northwest_profile_report_and_replay(self):
        data=self.fetch('/api/bureau?seed=20261014&bureau=xian')
        self.assertEqual(data['profile']['region_id'],'northwest')
        self.assertEqual(len(data['rows']),61)
        self.assertEqual(len(data['calibrationAudit']['bureaus']),20)
        self.assertEqual(set(data['calibrationAudit']['modes']),{'legacy_v03','combined_v04'})
        self.assertEqual(data['calibrationAudit']['configHash'],data['bureauConfigHash'])
        self.assertAlmostEqual(data['rows'][0]['operating_surplus_yi'],10.594988)
        self.assertEqual(data,self.fetch('/api/bureau?seed=20261014&bureau=xian'))

    def test_southwest_and_south_profiles_and_matching_reports(self):
        for bureau,rid,count,net in [('chengdu','southwest',12,.8),('guangzhou','south',8,1.)]:
            with self.subTest(bureau=bureau):
                data=self.fetch(f'/api/bureau?seed=20261014&bureau={bureau}')
                self.assertEqual(data['profile']['region_id'],rid)
                self.assertEqual(len(data['rows']),61)
                audit=data['calibrationAudit']
                self.assertEqual(audit['seedCount'],96)
                self.assertEqual(len(audit['bureaus']),count)
                self.assertEqual(set(audit['modes']),{'legacy_v03','combined_v04'})
                self.assertEqual(audit['configHash'],data['bureauConfigHash'])
                self.assertAlmostEqual(data['rows'][0]['hidden_freight_income_yi'],net)
                for r in data['rows']:
                    self.assertEqual(r['freight_tons_10k'],r['ordinary_freight_tons_10k'])
                    self.assertAlmostEqual(r['freight_income_yi'],r['ordinary_freight_income_yi']+r['hidden_freight_income_yi'])
                    self.assertAlmostEqual(r['revenue_yi']-r['cost_yi'],r['operating_surplus_yi'])


if __name__ == '__main__':
    unittest.main()
