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
        self.assertEqual(len(catalog['bureaus']), 100)
        self.assertEqual({b['region_id'] for b in catalog['bureaus']}, {r['id'] for r in catalog['regions']})

    def test_seed_validation_and_unconfigured_bureau(self):
        for path in ('?seed=-1', '?seed=', '?seed=9007199254740992', '?seed=1&seed=2', '?bureau=unknown', '?bureau=jiamusi&bureau=harbin'):
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

    def test_cash_layer_separate_matching_and_reconciled(self):
        data = self.fetch('/api/bureau?seed=7&bureau=lhasa')
        cash = data['cash']
        self.assertEqual(cash['modelVersion'], 'railway-bureau-annual-cash-dividends-v0.3')
        self.assertEqual(cash['policy']['annual_window'], 'previous_year_end_for_budget_year')
        self.assertFalse(cash['policy']['emergency_funding'])
        self.assertTrue(cash['policy']['allow_negative_cash'])
        self.assertEqual(len(cash['rows']), 61)
        self.assertEqual(cash['rows'][0]['cash_closing_yi'], 9.59)
        self.assertEqual(cash['rows'][0]['cash_operating_proxy_yi'], 0)
        self.assertEqual(cash['calibrationAudit']['seedCount'], 96)
        self.assertEqual(cash['calibrationAudit']['configHash'], cash['configHash'])
        self.assertEqual(cash['calibrationAudit']['bureau']['bureau_id'], 'lhasa')
        for operating, row in zip(data['rows'], cash['rows']):
            self.assertEqual(row['seed'], data['seed'])
            self.assertEqual(row['year'], operating['year'])
            self.assertAlmostEqual(row['cash_opening_yi'], row['cash_carryover_yi'] + row['cash_state_equity_yi'])
            self.assertAlmostEqual(row['cash_closing_yi'], row['cash_opening_yi'] + row['cash_operating_proxy_yi'] - row['cash_dividend_yi'])
            if row['year'] > 2025:
                self.assertEqual(row['cash_funding_year'], row['year'] - 1)
                self.assertEqual(row['cash_estimate_basis_year'], row['year'] - 1)
            self.assertAlmostEqual(operating['revenue_yi'] - operating['cost_yi'], operating['operating_surplus_yi'])
            self.assertNotIn('cash_closing_yi', operating)
        self.assertAlmostEqual(sum(e['amount_yi'] for e in cash['capitalEvents'] if e['event_type']=='annual_state_equity'), cash['rows'][-1]['cash_cumulative_equity_yi'])
        self.assertAlmostEqual(sum(e['amount_yi'] for e in cash['capitalEvents'] if e['event_type']=='annual_shareholder_dividend'), cash['rows'][-1]['cash_cumulative_dividend_yi'])
        self.assertEqual(len({e['event_id'] for e in cash['capitalEvents']}), len(cash['capitalEvents']))

    def test_dividends_and_cash_accumulation_reference(self):
        data = self.fetch('/api/bureau?seed=5767783356797806&bureau=shanghai')
        cash = data['cash']
        self.assertTrue(cash['policy']['dividends'])
        self.assertEqual(cash['policy']['dividend_policy']['state_ownership_share'], 1)
        self.assertEqual(cash['rows'][0]['cash_dividend_yi'], 0)
        end = cash['rows'][-1]
        self.assertGreater(end['cash_cumulative_dividend_yi'], 0)
        self.assertLess(end['cash_closing_yi'], end['cash_without_dividends_closing_yi'])
        self.assertAlmostEqual(end['cash_cumulative_state_net_investment_yi'], end['cash_cumulative_equity_yi'] - end['cash_cumulative_state_dividend_yi'])
        self.assertAlmostEqual(end['cash_closing_yi'], end['cash_initial_yi'] + end['cash_cumulative_operating_proxy_yi'] + end['cash_cumulative_equity_yi'] - end['cash_cumulative_dividend_yi'])
        for r in cash['rows']:
            if r['cash_dividend_yi'] > 0:
                self.assertEqual(r['cash_state_equity_yi'], 0)
                self.assertGreater(r['cash_operating_proxy_yi'], 0)
                self.assertGreaterEqual(r['cash_closing_yi'], r['cash_dividend_minimum_yi'])
        self.assertIn('withoutDividends', cash['calibrationAudit']['bureau'])

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

    def test_remaining_regions_and_scenario_group_accounting(self):
        for bureau,rid,count in [('wuhan','central',11),('shanghai','east',14),('taipei','southeast',13)]:
            with self.subTest(bureau=bureau):
                data=self.fetch(f'/api/bureau?seed=20261014&bureau={bureau}')
                self.assertEqual(data['profile']['region_id'],rid)
                self.assertEqual(len(data['rows']),61)
                audit=data['calibrationAudit']
                self.assertEqual(len(audit['bureaus']),count)
                self.assertEqual(set(audit['modes']),{'legacy_v03','combined_v04'})
                self.assertEqual(data['bureauConfigHash'],audit['configHash'])
                groups=audit['scenarioGroups'].values()
                self.assertEqual(sum(g['seedCount'] for g in groups),96)
                self.assertAlmostEqual(sum(g['seedCount']*g['pooled_end_loss_fraction'] for g in groups)/96,
                                       audit['region']['combined_v04']['pooled_end_loss_fraction'])
                self.assertEqual(data,self.fetch(f'/api/bureau?seed=20261014&bureau={bureau}'))


if __name__ == '__main__':
    unittest.main()
