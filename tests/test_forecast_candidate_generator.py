from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MACRO_DIR = ROOT_DIR / "macro_layers"
if str(MACRO_DIR) not in sys.path:
    sys.path.insert(0, str(MACRO_DIR))

import city_airport_potential_passenger_forecast_layer_sim as forecast_layer
from tests.test_forecast_narrative_model import CONFIG_PATH, synthetic_market_rows


class ForecastCandidateGeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rows = synthetic_market_rows()

    def generate(self, **overrides: object) -> dict[str, object]:
        request = {
            "config_path": CONFIG_PATH,
            "seed": 77,
            "as_of_year": 2030,
            "tier_profile_id": "initial_v1",
            "narrative_profile_id": "public_consensus_v2",
            "modifier_mode": "auto",
            "modifier_ids": [],
            "score_min": 70.0,
            "score_max": 80.0,
            "generation_nonce": 0,
        }
        request.update(overrides)
        return forecast_layer.generate_forecast_candidate(self.rows, **request)

    def test_catalog_exposes_four_tiers_eight_styles_and_fifteen_modifiers(self) -> None:
        catalog = forecast_layer.forecast_candidate_catalog(CONFIG_PATH)
        self.assertEqual(
            [6, 8, 10, 12],
            [tier["naturalHorizonYears"] for tier in catalog["tiers"]],
        )
        self.assertEqual(8, len(catalog["styles"]))
        self.assertEqual(15, len(catalog["modifiers"]))
        self.assertNotIn(
            "future_truth_v2",
            {style["narrativeProfileId"] for style in catalog["styles"]},
        )
        self.assertEqual(8.0, catalog["minimumScoreBandWidth"])

    def test_candidate_is_deterministic_full_horizon_and_uses_authoritative_score(self) -> None:
        first = self.generate()
        second = self.generate()
        self.assertEqual(first, second)
        self.assertEqual("matched", first["matchStatus"])
        self.assertEqual(6, first["naturalHorizonYears"])
        candidate = first["candidate"]
        rows = candidate["rows"]
        self.assertEqual(6, len(rows))
        self.assertEqual(list(range(2031, 2037)), [row["forecast_year"] for row in rows])
        self.assertTrue(all(row["as_of_year"] == 2030 for row in rows))
        self.assertTrue(all(row["forecast_revision_reason"] == "initial_report" for row in rows))
        self.assertEqual(92.0, candidate["revisionDisciplineScore"])
        self.assertGreaterEqual(candidate["componentResultScore"], 0.0)
        self.assertLessEqual(candidate["componentResultScore"], 100.0)
        self.assertEqual(
            "narrative-passenger-realized-score-v1.2",
            first["scoreMethodVersion"],
        )
        self.assertEqual(
            candidate["actualScore"],
            rows[0]["realized_report_process_quality_score"],
        )
        self.assertGreaterEqual(candidate["actualScore"], 70.0)
        self.assertLessEqual(candidate["actualScore"], 80.0)
        self.assertLessEqual(len(candidate["modifierIds"]), 2)
        self.assertTrue(
            forecast_layer._candidate_modifiers_are_compatible(
                candidate["modifierIds"]
            )
        )

    def test_nonce_changes_candidate_without_changing_request_contract(self) -> None:
        first = self.generate(generation_nonce=0)
        second = self.generate(generation_nonce=1)
        self.assertNotEqual(
            first["candidate"]["candidateId"],
            second["candidate"]["candidateId"],
        )
        self.assertEqual(6, len(second["candidate"]["rows"]))

    def test_pure_and_manual_modes_preserve_one_base_style(self) -> None:
        pure = self.generate(
            tier_profile_id="middle_v1",
            narrative_profile_id="fundamental_research_v2",
            modifier_mode="pure",
            score_min=75.0,
            score_max=85.0,
        )
        self.assertEqual([], pure["candidate"]["modifierIds"])
        self.assertEqual(8, len(pure["candidate"]["rows"]))
        self.assertEqual(
            "fundamental_research_v2",
            pure["candidate"]["reportMeta"]["forecast_narrative_profile_id"],
        )

        manual = self.generate(
            modifier_mode="manual",
            modifier_ids=["sticky_thesis_v2", "overconfident_v2"],
        )
        self.assertEqual(
            ["sticky_thesis_v2", "overconfident_v2"],
            manual["candidate"]["modifierIds"],
        )
        self.assertEqual(
            "public_consensus_v2",
            manual["candidate"]["reportMeta"]["forecast_narrative_profile_id"],
        )

    def test_impossible_band_returns_nearest_without_silent_widening(self) -> None:
        result = self.generate(
            tier_profile_id="professional_v1",
            narrative_profile_id="contrarian_research_v2",
            score_min=20.0,
            score_max=28.0,
        )
        self.assertEqual("nearest", result["matchStatus"])
        self.assertGreater(result["candidate"]["actualScore"], 28.0)
        self.assertGreater(result["candidate"]["scoreDistanceToTarget"], 0.0)
        self.assertEqual(48, result["attemptsEvaluated"])

    def test_tail_narrow_band_and_incompatible_modifiers_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "insufficient future years"):
            self.generate(
                as_of_year=2040,
                tier_profile_id="initial_v1",
            )
        with self.assertRaisesRegex(ValueError, "at least 8 points"):
            self.generate(score_min=75.0, score_max=80.0)
        with self.assertRaisesRegex(ValueError, "incompatible pair"):
            self.generate(
                narrative_profile_id="fundamental_research_v2",
                modifier_mode="manual",
                modifier_ids=["optimistic_v2", "pessimistic_v2"],
            )


if __name__ == "__main__":
    unittest.main()
