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
        self.assertEqual(len(catalog['bureaus']), 12)
        self.assertEqual({b['region_id'] for b in catalog['bureaus']}, {'northeast'})

    def test_seed_validation_and_unconfigured_bureau(self):
        for path in ('?seed=-1', '?seed=', '?seed=9007199254740992', '?seed=1&seed=2', '?bureau=beijing', '?bureau=jiamusi&bureau=harbin'):
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
        self.assertEqual(data['modelVersion'], 'railway-bureau-operations-v0.3')
        self.assertIsNotNone(data['laborAudit'])
        self.assertEqual(data['laborAudit']['seedCount'],96)
        self.assertEqual(len(data['laborAudit']['bureaus']),12)
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


if __name__ == '__main__':
    unittest.main()
