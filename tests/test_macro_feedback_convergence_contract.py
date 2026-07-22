"""Working Guide sub-Goal 2: macro feedback convergence contract tests.

The contract is deliberately field-based and deterministic: at least three
feedback reruns, followed by two consecutive adjacent-pass comparisons and an
undamped fixed-point residual comparison in which every authoritative field is
within its versioned tolerance. Composite delta and floor/cap counts remain
diagnostics; final rows must come from the last complete model pass, and an
unverified Run cannot be published.
"""

from __future__ import annotations

import argparse
import copy
import math
import os
import subprocess
import sys
import unittest
import warnings
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any
from unittest import mock

ROOT_DIR = Path(__file__).resolve().parents[1]
MACRO_DIR = ROOT_DIR / "macro_layers"
if str(MACRO_DIR) not in sys.path:
    sys.path.insert(0, str(MACRO_DIR))

import macro_run_orchestrator_sim as orchestrator  # noqa: E402
import orchestrator_run_validation as run_validation  # noqa: E402
import regional_macro_layer_sim as regional  # noqa: E402
from global_macro_feedback_calibration_sim import (  # noqa: E402
    CONVERGENCE_TOLERANCE_VERSION,
    FEEDBACK_BLEND_NUMERIC_FIELDS,
    FEEDBACK_RELAXATION_STRATEGY_VERSION,
    FIXED_POINT_VERIFICATION_VERSION,
    GLOBAL_BOUNDARY_FIELDS,
    MINIMUM_FEEDBACK_ITERATIONS,
    MacroFeedbackParams,
    blend_feedback_paths,
    compare_pass_records,
    convergence_summary,
    count_boundary_hits,
    derive_feedback_path,
    feedback_relaxation_for_iteration,
    resolve_iteration_bounds,
    run_convergence_aware_feedback_loop,
)


def _make_row(
    year_index: int,
    *,
    growth: float = 2.5,
    inflation: float = 2.0,
    policy: float = 3.0,
    two_y: float = 2.8,
    ten_y: float = 3.5,
    dollar: float = 100.0,
    hy: float = 300.0,
    oil: float = 75.0,
    short_rate: float | None = None,
    fci: float = 0.0,
) -> dict[str, Any]:
    """Build a minimal global row used by the synthetic solver tests."""
    return {
        "year_index": year_index,
        "year": 2025 + year_index,
        "seed": 20261324,
        "realized_growth_pct": growth,
        "headline_inflation_pct": inflation,
        "global_policy_rate_pct": policy,
        "global_2y_yield_pct": two_y,
        "global_10y_yield_pct": ten_y,
        "global_dollar_index": dollar,
        "global_high_yield_spread_bps": hy,
        "brent_oil_price_usd": oil,
        "global_short_rate_pct": short_rate if short_rate is not None else policy,
        "global_financial_conditions_index": fci,
    }


def _make_pass(
    years: int = 5,
    *,
    growth_delta: float = 0.0,
    inflation_delta: float = 0.0,
    policy_delta: float = 0.0,
    two_y_delta: float = 0.0,
    ten_y_delta: float = 0.0,
    dollar_delta: float = 0.0,
    hy_delta: float = 0.0,
    oil_delta: float = 0.0,
) -> list[dict[str, Any]]:
    """Build one pass with optional uniform offsets from the baseline."""
    return [
        _make_row(
            year_index,
            growth=2.5 + growth_delta,
            inflation=2.0 + inflation_delta,
            policy=3.0 + policy_delta,
            two_y=2.8 + two_y_delta,
            ten_y=3.5 + ten_y_delta,
            dollar=100.0 + dollar_delta,
            hy=300.0 + hy_delta,
            oil=75.0 + oil_delta,
        )
        for year_index in range(years + 1)
    ]


FIELD_BREACH_CASES: tuple[tuple[str, str, str], ...] = (
    ("growth_delta", "max_growth_delta_pct", "convergence_growth_tolerance_pct"),
    (
        "inflation_delta",
        "max_inflation_delta_pct",
        "convergence_inflation_tolerance_pct",
    ),
    ("policy_delta", "max_policy_rate_delta_pct", "convergence_policy_tolerance_pct"),
    ("two_y_delta", "max_2y_yield_delta_pct", "convergence_2y_tolerance_pct"),
    ("ten_y_delta", "max_10y_yield_delta_pct", "convergence_10y_tolerance_pct"),
    ("dollar_delta", "max_dollar_index_delta", "convergence_dollar_tolerance_index"),
    ("hy_delta", "max_hy_spread_delta_bps", "convergence_hy_tolerance_bps"),
    ("oil_delta", "max_brent_delta_usd", "convergence_oil_tolerance_usd"),
)


class ResolveIterationBoundsTests(unittest.TestCase):
    def test_defaults_match_params(self) -> None:
        params = MacroFeedbackParams()
        self.assertEqual(
            (MINIMUM_FEEDBACK_ITERATIONS, params.max_feedback_iterations),
            resolve_iteration_bounds(params),
        )

    def test_caller_overrides_win(self) -> None:
        self.assertEqual(
            (5, 12),
            resolve_iteration_bounds(
                MacroFeedbackParams(),
                min_iterations=5,
                max_iterations=12,
            ),
        )

    def test_max_below_min_preserves_authoritative_minimum(self) -> None:
        self.assertEqual(
            (3, 1),
            resolve_iteration_bounds(
                MacroFeedbackParams(),
                min_iterations=3,
                max_iterations=1,
            ),
        )

    def test_legacy_zero_max_normalizes_to_one_rerun(self) -> None:
        self.assertEqual((3, 1), resolve_iteration_bounds(MacroFeedbackParams(), max_iterations=0))

    def test_minimum_cannot_be_configured_below_three(self) -> None:
        self.assertEqual(
            (3, 8),
            resolve_iteration_bounds(
                MacroFeedbackParams(),
                min_iterations=1,
                max_iterations=8,
            ),
        )

    def test_negative_bounds_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "min feedback iterations"):
            resolve_iteration_bounds(MacroFeedbackParams(), min_iterations=-1)
        with self.assertRaisesRegex(ValueError, "max feedback iterations"):
            resolve_iteration_bounds(MacroFeedbackParams(), max_iterations=-1)


class CountBoundaryHitsTests(unittest.TestCase):
    def test_interior_rows_have_no_hits(self) -> None:
        hits = count_boundary_hits([_make_row(index) for index in range(5)])
        self.assertEqual(0, hits["total_floor_hits"])
        self.assertEqual(0, hits["total_cap_hits"])
        self.assertEqual(0, hits["total_boundary_hits"])

    def test_floor_and_cap_hits_counted_per_field(self) -> None:
        hits = count_boundary_hits(
            [
                _make_row(0, dollar=82.0, ten_y=-0.35),
                _make_row(1, dollar=124.0, two_y=10.50),
                _make_row(2),
            ]
        )
        per_field = hits["per_field"]
        self.assertEqual(1, per_field["global_dollar_index"]["floor_hits"])
        self.assertEqual(1, per_field["global_dollar_index"]["cap_hits"])
        self.assertEqual(1, per_field["global_10y_yield_pct"]["floor_hits"])
        self.assertEqual(1, per_field["global_2y_yield_pct"]["cap_hits"])
        self.assertEqual(4, hits["total_boundary_hits"])

    def test_boundary_epsilon_tolerates_floating_point_noise(self) -> None:
        hits = count_boundary_hits([_make_row(0, dollar=82.0 + 1e-9)])
        self.assertEqual(1, hits["per_field"]["global_dollar_index"]["floor_hits"])

    def test_every_published_boundary_field_is_covered(self) -> None:
        hits = count_boundary_hits([_make_row(0)])
        self.assertEqual(
            {field for field, _, _ in GLOBAL_BOUNDARY_FIELDS},
            set(hits["per_field"]),
        )


class ComparePassRecordsTests(unittest.TestCase):
    def test_strict_default_tolerances_are_restored(self) -> None:
        params = MacroFeedbackParams()
        self.assertEqual(
            (0.15, 0.20, 0.25, 0.25, 0.25, 1.5, 100.0, 20.0),
            (
                params.convergence_growth_tolerance_pct,
                params.convergence_inflation_tolerance_pct,
                params.convergence_policy_tolerance_pct,
                params.convergence_2y_tolerance_pct,
                params.convergence_10y_tolerance_pct,
                params.convergence_dollar_tolerance_index,
                params.convergence_hy_tolerance_bps,
                params.convergence_oil_tolerance_usd,
            ),
        )

    def test_identical_passes_pass_all_tolerances(self) -> None:
        diag = compare_pass_records(
            seed=42,
            from_pass=0,
            to_pass=1,
            previous=_make_pass(),
            current=_make_pass(),
            params=MacroFeedbackParams(),
        )
        self.assertTrue(diag["pass_converged"])
        self.assertEqual(0.0, diag["max_growth_delta_pct"])
        self.assertEqual(0.0, diag["max_hy_spread_delta_bps"])
        self.assertEqual(0.0, diag["pass_delta_index"])
        self.assertIn("previous_boundary_hits", diag)
        self.assertIn("current_boundary_hits", diag)

    def test_each_field_has_max_and_mean_deltas(self) -> None:
        params = MacroFeedbackParams()
        growth_delta = params.convergence_growth_tolerance_pct * 0.5
        inflation_delta = params.convergence_inflation_tolerance_pct * 0.5
        diag = compare_pass_records(
            seed=42,
            from_pass=0,
            to_pass=1,
            previous=_make_pass(),
            current=_make_pass(
                growth_delta=growth_delta,
                inflation_delta=inflation_delta,
            ),
            params=params,
        )
        self.assertAlmostEqual(growth_delta, diag["max_growth_delta_pct"])
        self.assertAlmostEqual(growth_delta, diag["mean_growth_delta_pct"])
        self.assertAlmostEqual(inflation_delta, diag["max_inflation_delta_pct"])
        self.assertAlmostEqual(inflation_delta, diag["mean_inflation_delta_pct"])
        self.assertTrue(diag["pass_converged"])

    def test_each_authoritative_field_fails_when_it_alone_breaches(self) -> None:
        params = MacroFeedbackParams()
        for input_name, diagnostic_name, tolerance_attribute in FIELD_BREACH_CASES:
            with self.subTest(field=input_name):
                tolerance = float(getattr(params, tolerance_attribute))
                delta = tolerance + max(0.01, tolerance * 0.10)
                diag = compare_pass_records(
                    seed=42,
                    from_pass=0,
                    to_pass=1,
                    previous=_make_pass(),
                    current=_make_pass(**{input_name: delta}),
                    params=params,
                )
                self.assertFalse(diag["pass_converged"])
                self.assertGreater(diag[diagnostic_name], tolerance)

    def test_composite_index_is_diagnostic_only(self) -> None:
        params = MacroFeedbackParams(convergence_delta_index_tolerance=0.0001)
        diag = compare_pass_records(
            seed=42,
            from_pass=0,
            to_pass=1,
            previous=_make_pass(),
            current=_make_pass(growth_delta=params.convergence_growth_tolerance_pct * 0.5),
            params=params,
        )
        self.assertGreater(diag["pass_delta_index"], params.convergence_delta_index_tolerance)
        self.assertTrue(diag["pass_converged"])

    def test_tolerance_source_is_versioned_and_complete(self) -> None:
        params = MacroFeedbackParams()
        diag = compare_pass_records(
            seed=42,
            from_pass=0,
            to_pass=1,
            previous=_make_pass(),
            current=_make_pass(),
            params=params,
        )
        self.assertEqual(CONVERGENCE_TOLERANCE_VERSION, diag["convergence_tolerance_version"])
        contracts = diag["convergence_tolerances"]
        self.assertEqual(8, len(contracts))
        for _, _, tolerance_attribute in FIELD_BREACH_CASES:
            matching = [
                contract
                for contract in contracts.values()
                if contract["parameter"] == tolerance_attribute
            ]
            self.assertEqual(1, len(matching), tolerance_attribute)
            self.assertEqual(
                float(getattr(params, tolerance_attribute)),
                float(matching[0]["max_abs_delta"]),
            )

    def test_year_zero_is_excluded_from_deltas(self) -> None:
        previous = _make_pass()
        current = _make_pass()
        current[0] = _make_row(0, growth=99.0)
        diag = compare_pass_records(
            seed=42,
            from_pass=0,
            to_pass=1,
            previous=previous,
            current=current,
            params=MacroFeedbackParams(),
        )
        self.assertTrue(diag["pass_converged"])
        self.assertEqual(0.0, diag["max_growth_delta_pct"])

    def test_empty_positive_year_domain_cannot_converge(self) -> None:
        diag = compare_pass_records(
            seed=42,
            from_pass=0,
            to_pass=1,
            previous=[_make_row(0)],
            current=[_make_row(0)],
            params=MacroFeedbackParams(),
        )
        self.assertFalse(diag["comparison_complete"])
        self.assertFalse(diag["pass_converged"])
        self.assertEqual(0, diag["compared_year_count"])

    def test_mismatched_or_duplicate_year_domains_cannot_converge(self) -> None:
        previous = _make_pass(years=3)
        current = _make_pass(years=2)
        current.append(copy.deepcopy(current[-1]))
        diag = compare_pass_records(
            seed=42,
            from_pass=0,
            to_pass=1,
            previous=previous,
            current=current,
            params=MacroFeedbackParams(),
        )
        self.assertFalse(diag["comparison_complete"])
        self.assertFalse(diag["pass_converged"])
        self.assertEqual([3], diag["missing_from_current"])


class ConvergenceSummaryTests(unittest.TestCase):
    def _params(
        self,
        *,
        consecutive: int = 2,
        min_iter: int = 3,
        max_iter: int = 16,
    ) -> MacroFeedbackParams:
        return MacroFeedbackParams(
            min_feedback_iterations=min_iter,
            max_feedback_iterations=max_iter,
            convergence_consecutive_passes=consecutive,
        )

    def _growth_breach(self) -> float:
        return self._params().convergence_growth_tolerance_pct * 2.0

    def test_no_passes_is_not_publishable_convergence(self) -> None:
        summary = convergence_summary([_make_pass()], seed=42, params=self._params())
        self.assertFalse(summary["converged"])
        self.assertFalse(summary["last_pass_converged"])
        self.assertEqual(0, summary["iterations_run"])
        self.assertEqual("no_passes", summary["convergence_reason"])

    def test_single_converged_delta_below_minimum_is_not_converged(self) -> None:
        summary = convergence_summary(
            [_make_pass(), _make_pass()],
            seed=42,
            params=self._params(),
        )
        self.assertFalse(summary["converged"])
        self.assertEqual("min_iterations_not_met", summary["convergence_reason"])
        self.assertTrue(summary["last_pass_converged"])

    def test_two_trailing_converged_deltas_at_three_pass_minimum_converge(self) -> None:
        summary = convergence_summary(
            [_make_pass(), _make_pass(), _make_pass(), _make_pass()],
            seed=42,
            params=self._params(),
        )
        self.assertTrue(summary["converged"])
        self.assertEqual("converged", summary["convergence_reason"])
        self.assertEqual(2, summary["consecutive_converged_passes"])
        self.assertEqual(3, summary["iterations_run"])

    def test_configured_minimum_below_three_does_not_weaken_contract(self) -> None:
        summary = convergence_summary(
            [_make_pass(), _make_pass(), _make_pass()],
            seed=42,
            params=self._params(min_iter=1),
            min_iterations=1,
        )
        self.assertFalse(summary["converged"])
        self.assertEqual(3, summary["min_iterations"])
        self.assertEqual("min_iterations_not_met", summary["convergence_reason"])

    def test_diverged_middle_pass_with_two_trailing_converged_is_converged(self) -> None:
        base = _make_pass()
        diverged = _make_pass(growth_delta=self._growth_breach())
        summary = convergence_summary(
            [base, diverged, base, base, base],
            seed=42,
            params=self._params(min_iter=4),
        )
        self.assertTrue(summary["converged"])
        self.assertEqual(2, summary["consecutive_converged_passes"])

    def test_diverged_middle_breaks_chain_when_three_consecutive_required(self) -> None:
        base = _make_pass()
        diverged = _make_pass(growth_delta=self._growth_breach())
        summary = convergence_summary(
            [base, diverged, base, base, base],
            seed=42,
            params=self._params(min_iter=4, consecutive=3),
        )
        self.assertFalse(summary["converged"])
        self.assertEqual("not_converged", summary["convergence_reason"])
        self.assertEqual(2, summary["consecutive_converged_passes"])

    def test_configured_single_converged_pass_is_still_insufficient(self) -> None:
        base = _make_pass()
        diverged = _make_pass(growth_delta=self._growth_breach())
        summary = convergence_summary(
            [base, diverged, base, base],
            seed=42,
            params=self._params(consecutive=1),
        )
        self.assertFalse(summary["converged"])
        self.assertEqual(1, summary["consecutive_converged_passes"])

    def test_diverged_last_pass_breaks_convergence(self) -> None:
        base = _make_pass()
        diverged = _make_pass(growth_delta=self._growth_breach())
        summary = convergence_summary(
            [base, base, base, diverged],
            seed=42,
            params=self._params(),
        )
        self.assertFalse(summary["converged"])
        self.assertEqual(0, summary["consecutive_converged_passes"])
        self.assertFalse(summary["last_pass_converged"])

    def test_max_iterations_reached_reason(self) -> None:
        breach = self._growth_breach()
        summary = convergence_summary(
            [_make_pass(growth_delta=breach * index) for index in range(4)],
            seed=42,
            params=self._params(max_iter=3),
        )
        self.assertFalse(summary["converged"])
        self.assertEqual("max_iterations_reached", summary["convergence_reason"])
        self.assertEqual(3, summary["iterations_run"])

    def test_delta_bounced_detected(self) -> None:
        summary = convergence_summary(
            [
                _make_pass(),
                _make_pass(growth_delta=0.05),
                _make_pass(growth_delta=0.05),
                _make_pass(growth_delta=0.20),
            ],
            seed=42,
            params=self._params(),
        )
        self.assertTrue(summary["delta_bounced"])

    def test_delta_not_bounced_when_final_delta_decreases(self) -> None:
        summary = convergence_summary(
            [
                _make_pass(),
                _make_pass(growth_delta=0.30),
                _make_pass(growth_delta=0.10),
                _make_pass(growth_delta=0.05),
            ],
            seed=42,
            params=self._params(),
        )
        self.assertFalse(summary["delta_bounced"])

    def test_summary_carries_manifest_and_solver_trace_fields(self) -> None:
        summary = convergence_summary(
            [_make_pass(), _make_pass(), _make_pass(), _make_pass()],
            seed=42,
            params=self._params(),
        )
        required = {
            "converged",
            "last_pass_converged",
            "consecutive_converged_passes",
            "iterations_run",
            "min_iterations",
            "max_iterations",
            "convergence_reason",
            "delta_bounced",
            "last_pass_delta_index",
            "max_pass_delta_index",
            "convergence_tolerance_version",
            "feedback_relaxation_strategy",
            "fixed_point_verification_version",
            "fixed_point_residual_checked",
            "fixed_point_residual_converged",
            "fixed_point_residual_delta_index",
            "fixed_point_residual_diagnostic",
            "pass_diagnostics",
        }
        self.assertTrue(required.issubset(summary))
        self.assertEqual(
            FEEDBACK_RELAXATION_STRATEGY_VERSION,
            summary["feedback_relaxation_strategy"],
        )
        self.assertEqual(
            FIXED_POINT_VERIFICATION_VERSION,
            summary["fixed_point_verification_version"],
        )

    def test_pass_diagnostics_include_boundary_hits_and_relaxation(self) -> None:
        relaxations = [1.0, 0.5, 1.0 / 3.0]
        summary = convergence_summary(
            [_make_pass(), _make_pass(), _make_pass(), _make_pass()],
            seed=42,
            params=self._params(),
            pass_relaxations=relaxations,
        )
        for index, diagnostic in enumerate(summary["pass_diagnostics"]):
            self.assertIn("previous_boundary_hits", diagnostic)
            self.assertIn("current_boundary_hits", diagnostic)
            self.assertAlmostEqual(relaxations[index], diagnostic["feedback_relaxation"])

    def test_relaxation_trace_length_must_match_diagnostics(self) -> None:
        with self.assertRaisesRegex(ValueError, "pass_relaxations"):
            convergence_summary(
                [_make_pass(), _make_pass()],
                seed=42,
                params=self._params(),
                pass_relaxations=[],
            )


class RunConvergenceAwareLoopTests(unittest.TestCase):
    def test_constant_relaxation_schedule_is_seed_independent(self) -> None:
        params = MacroFeedbackParams(feedback_iteration_relaxation=0.5)
        expected = [1.0, 0.5, 0.5, 0.5, 0.5]
        actual = [feedback_relaxation_for_iteration(params, index) for index in range(5)]
        for expected_value, actual_value in zip(expected, actual, strict=True):
            self.assertAlmostEqual(expected_value, actual_value)

    def test_invalid_relaxation_and_iteration_are_rejected(self) -> None:
        params = MacroFeedbackParams(feedback_iteration_relaxation=0.0)
        self.assertEqual(1.0, feedback_relaxation_for_iteration(params, 0))
        with self.assertRaisesRegex(ValueError, "feedback_iteration_relaxation"):
            feedback_relaxation_for_iteration(params, 1)
        with self.assertRaisesRegex(ValueError, "non-negative"):
            feedback_relaxation_for_iteration(params, -1)

    def test_blend_order_is_deterministic(self) -> None:
        current = {
            2: {"feedback_growth_impulse_pct": 0.2, "feedback_source": "two"},
            1: {"feedback_growth_impulse_pct": 0.1, "feedback_source": "one"},
        }
        blended = blend_feedback_paths({}, current, 1.0)
        self.assertEqual([1, 2], list(blended))
        blended_again = blend_feedback_paths(blended, current, 0.5)
        self.assertEqual([1, 2], list(blended_again))
        self.assertEqual(
            [*FEEDBACK_BLEND_NUMERIC_FIELDS, "feedback_source"],
            list(blended_again[1]),
        )

    def test_min_iterations_gate_delays_convergence_check(self) -> None:
        records = _make_pass()
        call_count = {"n": 0}

        def run_pass(_feedback: Any, _iteration: int) -> list[dict[str, Any]]:
            call_count["n"] += 1
            return copy.deepcopy(records)

        _, _, convergence = run_convergence_aware_feedback_loop(
            seed=42,
            feedback_params=MacroFeedbackParams(),
            initial_records=copy.deepcopy(records),
            run_pass=run_pass,
        )
        self.assertEqual(4, call_count["n"])
        self.assertTrue(convergence["converged"])
        self.assertEqual(
            [1.0, 1.0, 1.0],
            [item["feedback_relaxation"] for item in convergence["pass_diagnostics"]],
        )
        self.assertTrue(convergence["fixed_point_residual_checked"])
        self.assertTrue(convergence["fixed_point_residual_converged"])

    def test_max_iterations_cap_stops_without_convergence(self) -> None:
        params = MacroFeedbackParams(max_feedback_iterations=3)
        breach = params.convergence_growth_tolerance_pct * 2.0

        def run_pass(_feedback: Any, iteration: int) -> list[dict[str, Any]]:
            return _make_pass(growth_delta=breach * (iteration + 1))

        _, _, convergence = run_convergence_aware_feedback_loop(
            seed=42,
            feedback_params=params,
            initial_records=_make_pass(),
            run_pass=run_pass,
        )
        self.assertFalse(convergence["converged"])
        self.assertEqual("max_iterations_reached", convergence["convergence_reason"])
        self.assertEqual(3, convergence["iterations_run"])

    def test_one_rerun_keeps_full_first_feedback_update(self) -> None:
        base = _make_pass()
        params = MacroFeedbackParams(max_feedback_iterations=1)
        expected_feedback = derive_feedback_path(base, params)
        received: list[dict[int, dict[str, Any]]] = []

        def run_pass(feedback: dict[int, dict[str, Any]], _iteration: int) -> list[dict[str, Any]]:
            received.append(copy.deepcopy(feedback))
            return copy.deepcopy(base)

        _, final_feedback, convergence = run_convergence_aware_feedback_loop(
            seed=42,
            feedback_params=params,
            initial_records=copy.deepcopy(base),
            run_pass=run_pass,
            max_iterations=1,
        )
        self.assertEqual([expected_feedback], received)
        self.assertEqual(expected_feedback, final_feedback)
        self.assertEqual(1, convergence["iterations_run"])
        self.assertEqual(3, convergence["min_iterations"])
        self.assertEqual(1, convergence["max_iterations"])
        self.assertEqual("min_iterations_not_met", convergence["convergence_reason"])

    def test_returned_records_are_last_complete_model_pass(self) -> None:
        produced: list[list[dict[str, Any]]] = []

        def run_pass(_feedback: Any, iteration: int) -> list[dict[str, Any]]:
            records = _make_pass(growth_delta=0.01 * (iteration + 1))
            produced.append(records)
            return records

        final_records, _, convergence = run_convergence_aware_feedback_loop(
            seed=42,
            feedback_params=MacroFeedbackParams(max_feedback_iterations=3),
            initial_records=_make_pass(),
            run_pass=run_pass,
        )
        self.assertTrue(convergence["converged"])
        self.assertIs(produced[-2], final_records)
        self.assertTrue(convergence["fixed_point_residual_converged"])

    def test_adjacent_stability_cannot_hide_failed_fixed_point_residual(self) -> None:
        calls = {"n": 0}
        stable = _make_pass()
        residual_breach = _make_pass(
            growth_delta=MacroFeedbackParams().convergence_growth_tolerance_pct * 2.0
        )

        def run_pass(_feedback: Any, _iteration: int) -> list[dict[str, Any]]:
            calls["n"] += 1
            if calls["n"] <= 3:
                return copy.deepcopy(stable)
            return copy.deepcopy(residual_breach)

        final_records, _, convergence = run_convergence_aware_feedback_loop(
            seed=42,
            feedback_params=MacroFeedbackParams(max_feedback_iterations=3),
            initial_records=copy.deepcopy(stable),
            run_pass=run_pass,
        )
        self.assertEqual(stable, final_records)
        self.assertFalse(convergence["converged"])
        self.assertEqual(
            "fixed_point_residual_not_met",
            convergence["convergence_reason"],
        )
        self.assertTrue(convergence["fixed_point_residual_checked"])
        self.assertFalse(convergence["fixed_point_residual_converged"])

    def test_same_inputs_produce_identical_pass_sequence_and_summary(self) -> None:
        def execute() -> tuple[list[dict[str, Any]], dict[int, dict[str, Any]], dict[str, Any]]:
            def run_pass(_feedback: Any, iteration: int) -> list[dict[str, Any]]:
                return _make_pass(
                    growth_delta=0.02 * (iteration + 1),
                    inflation_delta=0.01 * (iteration + 1),
                )

            return run_convergence_aware_feedback_loop(
                seed=42,
                feedback_params=MacroFeedbackParams(max_feedback_iterations=5),
                initial_records=_make_pass(),
                run_pass=run_pass,
            )

        self.assertEqual(execute(), execute())


class RequestedPublishVariantGuardrailTests(unittest.TestCase):
    def test_publish_guard_contract_matches_solver_versions_and_tolerances(self) -> None:
        self.assertEqual(
            CONVERGENCE_TOLERANCE_VERSION,
            run_validation.CURRENT_CONVERGENCE_TOLERANCE_VERSION,
        )
        self.assertEqual(
            FEEDBACK_RELAXATION_STRATEGY_VERSION,
            run_validation.CURRENT_FEEDBACK_RELAXATION_STRATEGY,
        )
        params = MacroFeedbackParams()
        for _, _, _, parameter_name, tolerance in (
            run_validation.PUBLISH_CONVERGENCE_FIELD_CONTRACTS
        ):
            self.assertEqual(float(getattr(params, parameter_name)), tolerance)

    def _manifest(
        self,
        *,
        converged: Any,
        reason: str = "converged",
        scenario_variant: str = "scenario_1",
    ) -> dict[str, Any]:
        defaults = MacroFeedbackParams()
        exact_converged = converged is True
        current_pass = _make_pass()
        failed_pass = _make_pass(
            growth_delta=defaults.convergence_growth_tolerance_pct * 2.0
        )
        diagnostics = [
            compare_pass_records(
                seed=42,
                from_pass=from_pass,
                to_pass=from_pass + 1,
                previous=current_pass,
                current=current_pass if exact_converged else failed_pass,
                params=defaults,
            )
            for from_pass in range(7)
        ]
        fixed_point_residual = compare_pass_records(
            seed=42,
            from_pass=7,
            to_pass=8,
            previous=current_pass,
            current=current_pass if exact_converged else failed_pass,
            params=defaults,
        )
        convergence = {
            "converged": converged,
            "last_pass_converged": exact_converged,
            "consecutive_converged_passes": 2 if exact_converged else 0,
            "convergence_reason": reason,
            "iterations_run": 7,
            "min_iterations": defaults.min_feedback_iterations,
            "max_iterations": defaults.max_feedback_iterations,
            "delta_bounced": False,
            "last_pass_delta_index": diagnostics[-1]["pass_delta_index"],
            "max_pass_delta_index": max(
                item["pass_delta_index"] for item in diagnostics
            ),
            "convergence_tolerance_version": CONVERGENCE_TOLERANCE_VERSION,
            "feedback_relaxation_strategy": FEEDBACK_RELAXATION_STRATEGY_VERSION,
            "fixed_point_verification_version": FIXED_POINT_VERIFICATION_VERSION,
            "fixed_point_residual_checked": exact_converged,
            "fixed_point_residual_converged": exact_converged,
            "fixed_point_residual_delta_index": fixed_point_residual[
                "pass_delta_index"
            ],
            "fixed_point_residual_diagnostic": fixed_point_residual,
            "pass_diagnostics": diagnostics,
        }
        return {
            "scenario_variant": scenario_variant,
            "variants": {
                "baseline": {"convergence": dict(convergence)},
                scenario_variant: {"convergence": dict(convergence)},
            },
        }

    def test_converged_baseline_can_publish(self) -> None:
        name = run_validation.requested_publish_variant(
            argparse.Namespace(publish_viewer="baseline"),
            self._manifest(converged=True),
        )
        self.assertEqual("baseline", name)

    def test_converged_scenario_can_publish(self) -> None:
        name = run_validation.requested_publish_variant(
            argparse.Namespace(publish_viewer="scenario"),
            self._manifest(converged=True),
        )
        self.assertEqual("scenario_1", name)

    def test_nonconverged_variant_is_refused(self) -> None:
        with self.assertRaisesRegex(ValueError, "did not satisfy"):
            run_validation.requested_publish_variant(
                argparse.Namespace(publish_viewer="baseline"),
                self._manifest(converged=False, reason="max_iterations_reached"),
            )

    def test_truthy_non_boolean_converged_value_is_refused(self) -> None:
        with self.assertRaisesRegex(ValueError, "did not satisfy"):
            run_validation.requested_publish_variant(
                argparse.Namespace(publish_viewer="baseline"),
                self._manifest(converged="true"),
            )

    def test_missing_variants_block_is_refused(self) -> None:
        with self.assertRaisesRegex(ValueError, "has no variants manifest block"):
            run_validation.requested_publish_variant(
                argparse.Namespace(publish_viewer="baseline"),
                {"scenario_variant": "baseline"},
            )

    def test_missing_variant_entry_is_refused(self) -> None:
        with self.assertRaisesRegex(ValueError, "missing from the Run manifest"):
            run_validation.requested_publish_variant(
                argparse.Namespace(publish_viewer="baseline"),
                {"scenario_variant": "baseline", "variants": {}},
            )

    def test_variant_without_convergence_block_is_refused(self) -> None:
        with self.assertRaisesRegex(ValueError, "has no macro feedback convergence summary"):
            run_validation.requested_publish_variant(
                argparse.Namespace(publish_viewer="baseline"),
                {"scenario_variant": "baseline", "variants": {"baseline": {}}},
            )

    def test_converged_headline_without_final_diagnostics_is_refused(self) -> None:
        manifest = self._manifest(converged=True)
        del manifest["variants"]["baseline"]["convergence"]["pass_diagnostics"]
        with self.assertRaisesRegex(ValueError, "lacks two auditable final"):
            run_validation.requested_publish_variant(
                argparse.Namespace(publish_viewer="baseline"),
                manifest,
            )

    def test_converged_headline_without_fixed_point_residual_is_refused(self) -> None:
        manifest = self._manifest(converged=True)
        convergence = manifest["variants"]["baseline"]["convergence"]
        del convergence["fixed_point_residual_diagnostic"]
        with self.assertRaisesRegex(ValueError, "incomplete or stale|lacks two"):
            run_validation.requested_publish_variant(
                argparse.Namespace(publish_viewer="baseline"),
                manifest,
            )

    def test_failed_fixed_point_residual_is_refused(self) -> None:
        manifest = self._manifest(converged=True)
        convergence = manifest["variants"]["baseline"]["convergence"]
        convergence["fixed_point_residual_converged"] = False
        with self.assertRaisesRegex(ValueError, "incomplete or stale"):
            run_validation.requested_publish_variant(
                argparse.Namespace(publish_viewer="baseline"),
                manifest,
            )

    def test_converged_headline_with_failed_final_diagnostic_is_refused(self) -> None:
        manifest = self._manifest(converged=True)
        manifest["variants"]["baseline"]["convergence"]["pass_diagnostics"][-1][
            "pass_converged"
        ] = False
        with self.assertRaisesRegex(ValueError, "lacks two auditable final"):
            run_validation.requested_publish_variant(
                argparse.Namespace(publish_viewer="baseline"),
                manifest,
            )

    def test_converged_headline_with_inflated_diagnostic_tolerance_is_refused(self) -> None:
        manifest = self._manifest(converged=True)
        diagnostic = manifest["variants"]["baseline"]["convergence"][
            "pass_diagnostics"
        ][-1]
        diagnostic["convergence_tolerances"]["realized_growth_pct"][
            "max_abs_delta"
        ] = 9.0
        with self.assertRaisesRegex(ValueError, "lacks two auditable final"):
            run_validation.requested_publish_variant(
                argparse.Namespace(publish_viewer="baseline"),
                manifest,
            )

    def test_converged_headline_with_missing_mean_delta_is_refused(self) -> None:
        manifest = self._manifest(converged=True)
        diagnostic = manifest["variants"]["baseline"]["convergence"][
            "pass_diagnostics"
        ][-1]
        del diagnostic["mean_growth_delta_pct"]
        with self.assertRaisesRegex(ValueError, "lacks two auditable final"):
            run_validation.requested_publish_variant(
                argparse.Namespace(publish_viewer="baseline"),
                manifest,
            )

    def test_stale_tolerance_version_is_refused(self) -> None:
        manifest = self._manifest(converged=True)
        manifest["variants"]["baseline"]["convergence"][
            "convergence_tolerance_version"
        ] = "legacy-tolerances"
        with self.assertRaisesRegex(ValueError, "incomplete or stale"):
            run_validation.requested_publish_variant(
                argparse.Namespace(publish_viewer="baseline"),
                manifest,
            )

    def test_scenario_publish_requires_scenario_variant(self) -> None:
        with self.assertRaisesRegex(ValueError, "requires --scenario-state"):
            run_validation.requested_publish_variant(
                argparse.Namespace(publish_viewer="scenario"),
                {"scenario_variant": None},
            )

    def test_none_publish_skips_guardrail(self) -> None:
        self.assertIsNone(
            run_validation.requested_publish_variant(
                argparse.Namespace(publish_viewer="none"),
                self._manifest(converged=False, reason="max_iterations_reached"),
            )
        )


class EndToEndConvergenceContractTests(unittest.TestCase):
    def _args(
        self,
        *,
        feedback_iterations: int | None = None,
        min_feedback_iterations: int | None = None,
    ) -> argparse.Namespace:
        defaults = MacroFeedbackParams()
        return argparse.Namespace(
            years=12,
            start_year=2025,
            initial_gdp=100.0,
            volatility_scale=1.0,
            feedback_iterations=(
                defaults.max_feedback_iterations
                if feedback_iterations is None
                else feedback_iterations
            ),
            min_feedback_iterations=(
                defaults.min_feedback_iterations
                if min_feedback_iterations is None
                else min_feedback_iterations
            ),
        )

    def test_default_run_converges_within_contract(self) -> None:
        result = orchestrator.run_global_variant(20261324, self._args(), "baseline")
        convergence = result["convergence"]
        self.assertGreaterEqual(convergence["iterations_run"], convergence["min_iterations"])
        self.assertLessEqual(convergence["iterations_run"], convergence["max_iterations"])
        self.assertTrue(
            convergence["converged"],
            f"expected convergence, reason={convergence['convergence_reason']}",
        )
        self.assertEqual("converged", convergence["convergence_reason"])
        self.assertTrue(all(item["pass_converged"] for item in convergence["pass_diagnostics"][-2:]))
        self.assertTrue(convergence["fixed_point_residual_checked"])
        self.assertTrue(convergence["fixed_point_residual_converged"])
        self.assertTrue(
            convergence["fixed_point_residual_diagnostic"]["pass_converged"]
        )

    def test_rows_carry_convergence_annotation_fields(self) -> None:
        rows = orchestrator.run_global_variant(20261324, self._args(), "baseline")["rows"]
        required_fields = {
            "macro_feedback_iterations_run",
            "macro_feedback_min_iterations",
            "macro_feedback_max_iterations",
            "macro_feedback_converged",
            "macro_feedback_last_pass_converged",
            "macro_feedback_consecutive_converged_passes",
            "macro_feedback_convergence_reason",
            "macro_feedback_delta_bounced",
            "macro_feedback_last_pass_delta_index",
            "macro_feedback_max_pass_delta_index",
            "macro_feedback_fixed_point_residual_checked",
            "macro_feedback_fixed_point_residual_converged",
            "macro_feedback_fixed_point_residual_delta_index",
        }
        self.assertTrue(rows)
        for row in rows:
            self.assertTrue(required_fields.issubset(row))
            self.assertIn(
                row["macro_feedback_convergence_reason"],
                {"row_adjacent_pass_converged", "row_adjacent_pass_not_converged"},
            )
            self.assertEqual("false", row["macro_feedback_fixed_point_residual_checked"])
            self.assertEqual("false", row["macro_feedback_fixed_point_residual_converged"])
            self.assertEqual(0.0, row["macro_feedback_fixed_point_residual_delta_index"])

    def test_determinism_two_runs_produce_identical_rows(self) -> None:
        args = self._args()
        result_a = orchestrator.run_global_variant(20261324, args, "baseline")
        result_b = orchestrator.run_global_variant(20261324, args, "baseline")
        self.assertEqual(result_a["rows"], result_b["rows"])
        self.assertEqual(result_a["convergence"], result_b["convergence"])

    def test_scenario_variant_is_deterministic(self) -> None:
        scenario_feedback = {
            2: {
                "feedback_growth_impulse_pct": -0.35,
                "feedback_inflation_impulse_pct": 0.20,
                "feedback_policy_impulse_pct": 0.15,
                "feedback_source": "scenario_determinism_test",
                "scenario_state": "occurred",
            }
        }
        args = self._args()
        result_a = orchestrator.run_global_variant(
            20261324,
            args,
            "scenario_1",
            scenario_feedback,
        )
        result_b = orchestrator.run_global_variant(
            20261324,
            args,
            "scenario_1",
            scenario_feedback,
        )
        self.assertEqual(result_a["rows"], result_b["rows"])
        self.assertEqual(result_a["convergence"], result_b["convergence"])

    def test_one_rerun_preserves_minimum_and_reports_min_not_met(self) -> None:
        result = orchestrator.run_global_variant(
            20261324,
            self._args(feedback_iterations=1, min_feedback_iterations=3),
            "baseline",
        )
        convergence = result["convergence"]
        self.assertFalse(convergence["converged"])
        self.assertEqual("min_iterations_not_met", convergence["convergence_reason"])
        self.assertEqual(1, convergence["iterations_run"])
        self.assertEqual(3, convergence["min_iterations"])
        self.assertEqual(1, convergence["max_iterations"])

    def test_zero_and_one_request_same_economic_one_rerun_path(self) -> None:
        zero = orchestrator.run_global_variant(
            20261324,
            self._args(feedback_iterations=0),
            "baseline",
        )
        one = orchestrator.run_global_variant(
            20261324,
            self._args(feedback_iterations=1),
            "baseline",
        )
        fields = (
            "realized_growth_pct",
            "headline_inflation_pct",
            "global_policy_rate_pct",
            "global_2y_yield_pct",
            "global_10y_yield_pct",
            "global_dollar_index",
            "global_high_yield_spread_bps",
            "brent_oil_price_usd",
        )
        self.assertEqual(
            [[row[field] for field in fields] for row in zero["rows"]],
            [[row[field] for field in fields] for row in one["rows"]],
        )
        self.assertEqual(zero["convergence"], one["convergence"])

    def test_missing_iteration_attributes_use_current_solver_defaults(self) -> None:
        args = argparse.Namespace(
            years=12,
            start_year=2025,
            initial_gdp=100.0,
            volatility_scale=1.0,
        )
        convergence = orchestrator.run_global_variant(20261324, args, "baseline")["convergence"]
        defaults = MacroFeedbackParams()
        self.assertEqual(defaults.min_feedback_iterations, convergence["min_iterations"])
        self.assertEqual(defaults.max_feedback_iterations, convergence["max_iterations"])
        self.assertTrue(convergence["converged"])

    def test_scenario_feedback_is_present_in_pass_zero(self) -> None:
        captured_feedback: list[Any] = []

        def fake_full_chain(_seed: int, **kwargs: Any) -> list[dict[str, Any]]:
            captured_feedback.append(copy.deepcopy(kwargs.get("feedback_path")))
            return _make_pass(years=3)

        scenario_feedback = {
            1: {
                "feedback_growth_impulse_pct": -0.4,
                "feedback_source": "scenario_test",
                "scenario_state": "occurred",
            }
        }
        with mock.patch.object(orchestrator, "run_full_chain", side_effect=fake_full_chain):
            orchestrator.run_global_variant(
                20261324,
                self._args(feedback_iterations=1),
                "scenario_1",
                scenario_feedback,
            )
        self.assertTrue(captured_feedback)
        self.assertEqual(-0.4, captured_feedback[0][1]["feedback_growth_impulse_pct"])
        self.assertEqual("scenario_test", captured_feedback[0][1]["feedback_source"])


class CrossProcessDeterminismTests(unittest.TestCase):
    def test_global_rows_and_convergence_match_across_python_hash_seeds(self) -> None:
        child_code = r"""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

root = Path(sys.argv[1])
sys.path.insert(0, str(root / "macro_layers"))
import regional_macro_layer_sim as regional
from global_macro_feedback_calibration_sim import MacroFeedbackParams

defaults = MacroFeedbackParams()
args = argparse.Namespace(
    years=12,
    start_year=2025,
    initial_gdp=100.0,
    volatility_scale=1.0,
    feedback_iterations=defaults.max_feedback_iterations,
    min_feedback_iterations=defaults.min_feedback_iterations,
)
params = regional.build_global_params(args)
rows, convergence = regional.run_global_macro_for_seed(
    20261324,
    params,
    args.feedback_iterations,
    min_feedback_iterations=args.min_feedback_iterations,
)
payload = {"rows": rows, "convergence": convergence}
encoded = json.dumps(
    payload,
    sort_keys=True,
    separators=(",", ":"),
    ensure_ascii=True,
).encode("utf-8")
print(hashlib.sha256(encoded).hexdigest())
"""
        digests: dict[str, str] = {}
        for hash_seed in ("1", "2", "3"):
            environment = dict(os.environ)
            environment["PYTHONHASHSEED"] = hash_seed
            completed = subprocess.run(
                [sys.executable, "-c", child_code, str(ROOT_DIR)],
                cwd=ROOT_DIR,
                env=environment,
                check=True,
                capture_output=True,
                text=True,
            )
            digest = completed.stdout.strip()
            self.assertEqual(64, len(digest), completed.stderr)
            digests[hash_seed] = digest
        self.assertEqual(1, len(set(digests.values())), digests)


class EntryPointConsistencyTests(unittest.TestCase):
    def test_all_three_entry_modules_reference_the_same_solver(self) -> None:
        self.assertIs(
            regional.run_convergence_aware_feedback_loop,
            run_convergence_aware_feedback_loop,
        )
        self.assertIs(
            orchestrator.run_convergence_aware_feedback_loop,
            run_convergence_aware_feedback_loop,
        )

    def test_regional_standalone_and_orchestrator_share_global_contract(self) -> None:
        defaults = MacroFeedbackParams()
        args = argparse.Namespace(
            years=12,
            start_year=2025,
            initial_gdp=100.0,
            volatility_scale=1.0,
            feedback_iterations=defaults.max_feedback_iterations,
            min_feedback_iterations=defaults.min_feedback_iterations,
        )
        params = regional.build_global_params(args)
        regional_rows, regional_convergence = regional.run_global_macro_for_seed(
            20261324,
            params,
            args.feedback_iterations,
            min_feedback_iterations=args.min_feedback_iterations,
        )
        orchestrated = orchestrator.run_global_variant(20261324, args, "baseline")
        fields = (
            "realized_growth_pct",
            "headline_inflation_pct",
            "global_policy_rate_pct",
            "global_2y_yield_pct",
            "global_10y_yield_pct",
            "global_dollar_index",
            "global_high_yield_spread_bps",
            "brent_oil_price_usd",
        )
        # The orchestrator's historical scenario-merge adapter compacts applied
        # feedback inputs to four decimals before the full pass, even when no
        # scenario is active. Most published fields can differ by one final
        # rounding unit; recursive HY and Brent paths can amplify that input
        # quantization by a few thousandths while remaining economically and
        # contractually identical. The shared convergence summary must still be
        # exact.
        field_tolerances = {
            "global_high_yield_spread_bps": 0.0051,
            "brent_oil_price_usd": 0.00061,
        }
        for regional_row, orchestrated_row in zip(
            regional_rows,
            orchestrated["rows"],
            strict=True,
        ):
            for field in fields:
                self.assertAlmostEqual(
                    float(regional_row[field]),
                    float(orchestrated_row[field]),
                    delta=field_tolerances.get(field, 0.00011),
                )
        orchestrated_convergence = orchestrated["convergence"]
        for key in (
            "converged",
            "last_pass_converged",
            "consecutive_converged_passes",
            "iterations_run",
            "min_iterations",
            "max_iterations",
            "convergence_reason",
            "convergence_tolerance_version",
            "feedback_relaxation_strategy",
            "fixed_point_residual_checked",
            "fixed_point_residual_converged",
        ):
            self.assertEqual(regional_convergence[key], orchestrated_convergence[key], key)
        self.assertEqual(
            [item["pass_converged"] for item in regional_convergence["pass_diagnostics"]],
            [item["pass_converged"] for item in orchestrated_convergence["pass_diagnostics"]],
        )
        self.assertAlmostEqual(
            regional_convergence["last_pass_delta_index"],
            orchestrated_convergence["last_pass_delta_index"],
            delta=0.01,
        )
        self.assertAlmostEqual(
            regional_convergence["fixed_point_residual_delta_index"],
            orchestrated_convergence["fixed_point_residual_delta_index"],
            delta=0.001,
        )


TUNING_AUDIT_SEEDS: tuple[int, ...] = tuple(20261001 + offset for offset in range(40))
HOLDOUT_AUDIT_SEEDS: tuple[int, ...] = tuple(20262001 + offset for offset in range(40))
AUDIT_SEED_GROUPS: dict[str, tuple[int, ...]] = {
    "tuning": TUNING_AUDIT_SEEDS,
    "holdout": HOLDOUT_AUDIT_SEEDS,
}
AUDIT_SEEDS: tuple[int, ...] = TUNING_AUDIT_SEEDS + HOLDOUT_AUDIT_SEEDS


class EightySeedConvergenceAuditTests(unittest.TestCase):
    """Run the 40-seed tuning cohort plus a disjoint 40-seed holdout cohort."""

    @classmethod
    def setUpClass(cls) -> None:
        defaults = MacroFeedbackParams()
        args = argparse.Namespace(
            years=60,
            start_year=2025,
            initial_gdp=100.0,
            volatility_scale=1.0,
            feedback_iterations=defaults.max_feedback_iterations,
            min_feedback_iterations=defaults.min_feedback_iterations,
        )
        cls.results: dict[int, dict[str, Any]] = {
            seed: orchestrator.run_global_variant(seed, args, "baseline")
            for seed in AUDIT_SEEDS
        }

    def test_seed_groups_are_disjoint_and_complete(self) -> None:
        self.assertEqual(40, len(TUNING_AUDIT_SEEDS))
        self.assertEqual(40, len(HOLDOUT_AUDIT_SEEDS))
        self.assertFalse(set(TUNING_AUDIT_SEEDS) & set(HOLDOUT_AUDIT_SEEDS))
        self.assertEqual(80, len(AUDIT_SEEDS))

    def test_all_seeds_converge(self) -> None:
        failures = []
        for seed, result in self.results.items():
            convergence = result["convergence"]
            if not convergence["converged"]:
                failures.append(
                    f"seed {seed}: reason={convergence['convergence_reason']}, "
                    f"iterations={convergence['iterations_run']}"
                )
        self.assertFalse(failures, "Convergence contract failures:\n" + "\n".join(failures))

    def test_all_seeds_have_two_final_adjacent_passing_diagnostics(self) -> None:
        for seed, result in self.results.items():
            convergence = result["convergence"]
            final_two = convergence["pass_diagnostics"][-2:]
            self.assertGreaterEqual(convergence["consecutive_converged_passes"], 2)
            self.assertEqual(2, len(final_two), f"seed {seed} lacks two final diagnostics")
            self.assertTrue(
                all(item["pass_converged"] for item in final_two),
                f"seed {seed} final adjacent passes do not both satisfy every tolerance",
            )
            for diagnostic in final_two:
                self.assertEqual(
                    CONVERGENCE_TOLERANCE_VERSION,
                    diagnostic["convergence_tolerance_version"],
                )
                self.assertEqual(8, len(diagnostic["convergence_tolerances"]))

    def test_all_seeds_pass_undamped_fixed_point_residual(self) -> None:
        for seed, result in self.results.items():
            convergence = result["convergence"]
            self.assertTrue(
                convergence["fixed_point_residual_checked"],
                f"seed {seed} lacks a fixed-point residual check",
            )
            self.assertTrue(
                convergence["fixed_point_residual_converged"],
                f"seed {seed} failed its fixed-point residual check",
            )
            diagnostic = convergence["fixed_point_residual_diagnostic"]
            self.assertTrue(diagnostic["pass_converged"])
            self.assertEqual(
                convergence["iterations_run"],
                diagnostic["from_pass"],
            )
            self.assertEqual(
                convergence["iterations_run"] + 1,
                diagnostic["to_pass"],
            )

    def test_no_seed_hit_max_iterations_cap(self) -> None:
        for seed, result in self.results.items():
            self.assertNotEqual(
                "max_iterations_reached",
                result["convergence"]["convergence_reason"],
                f"seed {seed} hit the hard cap",
            )

    def test_all_seeds_respect_iteration_bounds(self) -> None:
        for seed, result in self.results.items():
            convergence = result["convergence"]
            self.assertGreaterEqual(
                convergence["iterations_run"],
                convergence["min_iterations"],
                f"seed {seed} ran fewer than the minimum",
            )
            self.assertLessEqual(
                convergence["iterations_run"],
                convergence["max_iterations"],
                f"seed {seed} exceeded the hard cap",
            )

    def test_all_seeds_carry_convergence_annotation(self) -> None:
        for seed, result in self.results.items():
            self.assertTrue(result["rows"], f"seed {seed} produced no rows")
            self.assertEqual("true", result["rows"][-1]["macro_feedback_converged"])

    def test_goal3_gap_distribution_and_growth_guardrails(self) -> None:
        for group_name, seeds in AUDIT_SEED_GROUPS.items():
            group_results = [self.results[seed] for seed in seeds]
            mean_gaps = [
                mean(float(row["output_gap_pct"]) for row in result["rows"])
                for result in group_results
            ]
            last_ten_gaps = [
                mean(float(row["output_gap_pct"]) for row in result["rows"][-10:])
                for result in group_results
            ]
            self.assertLess(
                sum(value < 0.0 for value in mean_gaps),
                40,
                f"{group_name} remains 40/40 negative",
            )
            self.assertLessEqual(
                sum(value < -2.0 for value in last_ten_gaps),
                8,
                f"{group_name} last-ten-year negative tail regressed",
            )

            transitions: list[float] = []
            hard_hits = 0
            longest = 0
            for result in group_results:
                run = 0
                rows = result["rows"]
                for previous, current in zip(rows, rows[1:], strict=False):
                    step = float(current["realized_growth_pct"]) - float(
                        previous["realized_growth_pct"]
                    )
                    transitions.append(step)
                    hit = bool(current["growth_step_cap_applied"])
                    hard_hits += int(hit)
                    run = run + 1 if hit else 0
                    longest = max(longest, run)
                    self.assertEqual(
                        run,
                        int(current["growth_step_cap_consecutive_years"]),
                    )
                    if hit:
                        self.assertAlmostEqual(
                            abs(step),
                            float(current["growth_step_limit_pct"]),
                            delta=0.00011,
                        )
                        self.assertEqual(
                            "up" if step > 0.0 else "down",
                            current["growth_step_cap_direction"],
                        )
                    else:
                        self.assertEqual("none", current["growth_step_cap_direction"])

            self.assertLess(hard_hits / len(transitions), 0.02, group_name)
            self.assertLessEqual(longest, 2, group_name)
            platform_counts = Counter(round(abs(value), 4) for value in transitions)
            nonzero_max = max(
                (count for step, count in platform_counts.items() if step > 0.0),
                default=0,
            )
            self.assertLess(
                nonzero_max / len(transitions),
                0.02,
                f"{group_name} formed a new fixed growth-step platform",
            )

    def test_goal3_published_gap_and_gdp_identities_hold_for_all_audit_seeds(self) -> None:
        for seed, result in self.results.items():
            rows = result["rows"]
            for index, row in enumerate(rows):
                real_index = float(row["real_gdp_index"])
                potential_index = float(row["potential_gdp_index"])
                strict_gap = 100.0 * math.log(real_index / potential_index)
                self.assertAlmostEqual(
                    strict_gap,
                    float(row["gdp_level_gap_pct"]),
                    delta=0.000051,
                    msg=f"seed={seed}, year_index={index}",
                )
                self.assertAlmostEqual(
                    float(row["output_gap_pct"]) - float(row["gdp_level_gap_pct"]),
                    float(row["output_gap_measurement_residual_pct"]),
                    delta=0.000051,
                )
                self.assertAlmostEqual(
                    float(row["global_gdp_trillion_usd"]),
                    100.0 * real_index / 100.0,
                    delta=0.00011,
                )
                self.assertEqual(
                    "gdp-gap-measurement-v1",
                    row["output_gap_measurement_version"],
                )
                self.assertEqual(
                    "soft-log-target-step-with-hard-realized-bound-v1",
                    row["growth_step_limiter_version"],
                )
                if index:
                    previous = rows[index - 1]
                    implied_growth = (
                        real_index / float(previous["real_gdp_index"]) - 1.0
                    ) * 100.0
                    implied_potential_growth = (
                        potential_index / float(previous["potential_gdp_index"]) - 1.0
                    ) * 100.0
                    # Both level indices and published growth are rounded to
                    # four decimals. The exact 80-seed worst case after the
                    # unified initial row is 0.0001344 percentage points, so
                    # 0.00014 is the tight rounding envelope rather than an
                    # economic tolerance.
                    self.assertAlmostEqual(
                        implied_growth,
                        float(row["realized_growth_pct"]),
                        delta=0.00014,
                    )
                    self.assertAlmostEqual(
                        implied_potential_growth,
                        float(row["potential_growth_pct"]),
                        delta=0.00014,
                    )

    def test_bounce_and_over_eight_are_reported_as_diagnostics(self) -> None:
        bounced = [
            seed
            for seed, result in self.results.items()
            if result["convergence"]["delta_bounced"]
        ]
        over_eight = [
            seed
            for seed, result in self.results.items()
            if result["convergence"]["iterations_run"] > 8
        ]
        if bounced:
            warnings.warn(
                f"{len(bounced)} audit seeds ended with delta_bounced=True: {bounced}",
                stacklevel=2,
            )
        if over_eight:
            warnings.warn(
                f"{len(over_eight)} audit seeds required more than 8 reruns: {over_eight}",
                stacklevel=2,
            )


if __name__ == "__main__":
    unittest.main()
