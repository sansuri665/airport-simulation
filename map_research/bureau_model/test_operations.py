"""Accounting and behavior checks: py -m unittest bureau_model.test_operations."""
import copy
import math
import unittest

from economy_model.scenarios import simulate_scenario
from .operations import INPUTS, SEGMENTS, finance, load_profiles, simulate_bureaus, validate_profiles

PRICES = {'energy_real_index': 100., 'wage_real_index': 100., 'materials_real_index': 100.}


class CostTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profiles = load_profiles()

    def test_all_baselines_and_three_reconciliations(self):
        self.assertEqual(len(self.profiles), 12)
        for p in self.profiles:
            for qp, qf, energy, wage in [(100, 100, 100, 100), (0, 0, 120, 130), (35, 180, 170, 115), (800, 900, 80, 120)]:
                r = finance(p, {**PRICES, 'energy_real_index': energy, 'wage_real_index': wage}, qp, qf)
                self.assertAlmostEqual(r['cost_yi'], sum(r[k + '_cost_yi'] for k in INPUTS))
                self.assertAlmostEqual(r['cost_yi'], sum(r[s + '_cost_yi'] for s in SEGMENTS))
                self.assertAlmostEqual(r['cost_yi'], r['fixed_operating_cost_yi'] + r['volume_operating_cost_yi'])
                self.assertAlmostEqual(r['revenue_yi'] - r['cost_yi'], r['operating_surplus_yi'])
            base = finance(p, PRICES, 100, 100)
            for s in SEGMENTS:
                self.assertAlmostEqual(base[s + '_cost_yi'], p['finance_base_yi'][s + '_cost'])
        self.assertAlmostEqual(finance(self.profiles[0], PRICES, 100, 100)['operating_surplus_yi'], -.15)

    def test_independent_price_and_changing_composition(self):
        p = self.profiles[0]
        a = finance(p, PRICES, 80, 80)
        for kind in INPUTS[:-1]:
            b = finance(p, {**PRICES, kind + '_real_index': 150}, 80, 80)
            factor = 1.5 ** p['exposure'][kind + '_price_beta']
            self.assertAlmostEqual(b[kind + '_cost_yi'], a[kind + '_cost_yi'] * factor)
            for other in set(INPUTS) - {kind}:
                self.assertEqual(b[other + '_cost_yi'], a[other + '_cost_yi'])
            self.assertGreater(b[kind + '_cost_yi'] / b['cost_yi'], a[kind + '_cost_yi'] / a['cost_yi'])
            self.assertEqual(a['revenue_yi'], b['revenue_yi'])

    def test_labor_is_stickier_and_fixed_cost_survives_zero_volume(self):
        p = self.profiles[0]
        base = finance(p, PRICES, 100, 100)
        low = finance(p, PRICES, 50, 50)
        self.assertGreater(low['wage_cost_yi'] / base['wage_cost_yi'], low['energy_cost_yi'] / base['energy_cost_yi'])
        zero = finance(p, PRICES, 0, 0)
        self.assertEqual(zero['volume_operating_cost_yi'], 0)
        self.assertEqual(zero['revenue_yi'], 0)
        self.assertEqual(zero['cost_yi'], zero['fixed_operating_cost_yi'])
        self.assertGreater(zero['cost_yi'], 0)

    def test_congestion_is_per_input_and_does_not_cap_volume(self):
        p = self.profiles[0]
        high = finance(p, PRICES, 200, 200)
        plain = copy.deepcopy(p)
        for inputs in plain['cost_inputs'].values():
            for c in inputs.values():
                c['passenger_congestion'] = c['freight_congestion'] = 0
        normal = finance(plain, PRICES, 200, 200)
        for kind in ('wage', 'other'):
            self.assertEqual(high[kind + '_cost_yi'], normal[kind + '_cost_yi'])
        for kind in ('energy', 'materials'):
            self.assertGreater(high[kind + '_cost_yi'], normal[kind + '_cost_yi'])
        self.assertEqual(high['passenger_trips_10k'], 2 * p['transport']['base_passenger_trips_10k'])

    def test_each_input_can_have_its_own_volume_weights(self):
        p = copy.deepcopy(self.profiles[0])
        p['cost_inputs']['conventional']['wage']['variable_passenger_share'] = 1.
        a = finance(self.profiles[0], PRICES, 50, 100)
        b = finance(p, PRICES, 50, 100)
        self.assertLess(b['wage_cost_yi'], a['wage_cost_yi'])
        for kind in ('energy', 'materials', 'other'):
            self.assertEqual(b[kind + '_cost_yi'], a[kind + '_cost_yi'])

    def test_bad_parameters_and_inputs_fail(self):
        for key, value in [('fixed_share', 1.1), ('fixed_share', math.nan),
                           ('base_cost_yi', -1), ('passenger_congestion', -.1),
                           ('variable_passenger_share', True)]:
            bad = copy.deepcopy(self.profiles)
            bad[0]['cost_inputs']['station']['energy'][key] = value
            with self.assertRaises(ValueError):
                validate_profiles(bad)
        bad = copy.deepcopy(self.profiles)
        bad[0]['cost_inputs']['station']['energy']['base_cost_yi'] += .1
        with self.assertRaises(ValueError):
            validate_profiles(bad)
        for q in (-1, math.nan, math.inf, True):
            with self.assertRaises(ValueError):
                finance(self.profiles[0], PRICES, q, 100)
        for price in (0, -1, math.nan):
            with self.assertRaises(ValueError):
                finance(self.profiles[0], {**PRICES, 'wage_real_index': price}, 100, 100)

    def test_replay_order_prefix_and_no_profile_mutation(self):
        original = copy.deepcopy(self.profiles)
        macro = simulate_scenario(seed=20261014, years=10)
        rows = simulate_bureaus(macro, self.profiles)
        self.assertEqual(rows, simulate_bureaus(macro, self.profiles))
        reordered = simulate_bureaus(macro, list(reversed(self.profiles)))
        index = lambda rs: {(r['year_index'], r['bureau_id']): r for r in rs}
        self.assertEqual(index(rows), index(reordered))
        short = simulate_bureaus(simulate_scenario(seed=20261014, years=3), self.profiles)
        self.assertEqual(short, [r for r in rows if r['year_index'] <= 3])
        self.assertEqual(original, self.profiles)


if __name__ == '__main__':
    unittest.main()
