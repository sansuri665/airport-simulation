"""Regression checks for regional differentiation and scenario contracts.

Run from map_research: py -m unittest economy_model.test_regional
"""
import math
import unittest

from .scenarios import build_plan, simulate_scenario
from .simulate import CORE_METRICS, public_market_snapshot, simulate


class RegionalScenarioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seed = 5767783356797806
        cls.result = simulate_scenario(seed=cls.seed)

    def test_replay_and_history_prefix(self):
        self.assertEqual(self.result, simulate_scenario(seed=self.seed))
        short = simulate_scenario(seed=self.seed, years=15)
        self.assertEqual(short['rows'], self.result['rows'][:16 * 8])
        self.assertEqual(short['regional_phases'], self.result['regional_phases'][:16])
        self.assertEqual(short['national_factors'], self.result['national_factors'][:16])

    def test_region_order_does_not_change_paths(self):
        cfg, shocks, _, _ = build_plan(self.seed)
        cfg['regions'].reverse()
        reordered = simulate(cfg, seed=self.seed, shocks=shocks)
        self.assertEqual(reordered['rows'], self.result['rows'])

    def test_regional_paths_preserve_common_finance(self):
        cfg, shocks, _, _ = build_plan(self.seed)
        cfg.pop('regional_development_paths')
        common = simulate(cfg, seed=self.seed, shocks=shocks)
        self.assertEqual(common['national_factors'], self.result['national_factors'])

    def test_common_base_and_safe_seed_limits(self):
        base = public_market_snapshot(self.result, 0)
        for seed in (0, 1, 9007199254740991):
            result = simulate_scenario(seed=seed)
            self.assertEqual(public_market_snapshot(result, 0), base)
            for row in result['rows']:
                for metric in CORE_METRICS:
                    self.assertTrue(math.isfinite(row[metric]))
                    if metric != 'real_rate_pct':
                        self.assertGreater(row[metric], 0)

    def test_released_history_excludes_future_and_internal_paths(self):
        public = public_market_snapshot(self.result, 10)
        self.assertEqual(len(public['regional_rows']), 11 * 8)
        self.assertEqual(len(public['national_rows']), 11)
        for row in public['regional_rows']:
            self.assertLessEqual(row['year_index'], 10)
            self.assertNotIn('regional_development_paths', row)
            self.assertNotIn('passenger_trend_growth_pct', row)

    def test_decline_is_possible_but_not_fixed_and_metrics_can_diverge(self):
        northeast_20 = []
        opposite_metrics = False
        regional_turns = False
        for seed in range(16):
            result = simulate_scenario(seed=seed)
            northeast_20.append(next(row['passenger_demand_index'] for row in result['rows']
                                     if row['region_id'] == 'northeast' and row['year_index'] == 20))
            opposite_metrics |= any((row['passenger_demand_index'] - 100) * (row['freight_demand_index'] - 100) < 0
                                    for row in result['rows'] if row['year_index'] == 60)
            regional_turns |= any(phase['regions']['northeast'].startswith('转向') for phase in result['regional_phases'])
        self.assertLess(min(northeast_20), 100)
        self.assertGreater(max(northeast_20), 100)
        self.assertTrue(opposite_metrics)
        self.assertTrue(regional_turns)


if __name__ == '__main__':
    unittest.main()
