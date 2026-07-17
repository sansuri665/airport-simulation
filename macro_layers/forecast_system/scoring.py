from __future__ import annotations

from importlib import import_module
import math
from statistics import mean
from typing import Any


_PARENT_PACKAGE = (
    (__package__ or "").rsplit(".", 1)[0]
    if "." in (__package__ or "")
    else ""
)
_PARENT_PREFIX = f"{_PARENT_PACKAGE}." if _PARENT_PACKAGE else ""
simulation_utils = import_module(f"{_PARENT_PREFIX}simulation_utils")

as_float = simulation_utils.as_float_convert_lookup_default
clamp = simulation_utils.clamp
safe_divide = simulation_utils.safe_divide

COMPONENTS = ("business", "leisure", "vfr", "long_haul", "transfer")
COMPONENT_SCORE_WEIGHTS = {
    "business": 1.30,
    "leisure": 1.00,
    "vfr": 0.75,
    "long_haul": 1.35,
    "transfer": 1.15,
}
COMPONENT_SHARE_UNCERTAINTY_MULTIPLIER = {
    "business": 0.80,
    "leisure": 0.78,
    "vfr": 0.92,
    "long_haul": 1.08,
    "transfer": 1.22,
}

REALIZED_SCORE_METHOD_VERSION = "narrative-passenger-realized-score-v1.2"
REALIZED_TOTAL_RESULT_SCORE_WEIGHTS = {
    "midpoint": 0.30,
    "trend": 0.12,
    "shape": 0.08,
    "bottleneck": 0.05,
    "interval": 0.15,
}
REALIZED_COMPONENT_RESULT_SCORE_WEIGHTS = {
    "component_potential_structure": 0.04,
    "component_supply_structure": 0.05,
    "component_fulfillment": 0.03,
    "component_interval": 0.03,
}
REALIZED_RESULT_SCORE_WEIGHTS = {
    **REALIZED_TOTAL_RESULT_SCORE_WEIGHTS,
    **REALIZED_COMPONENT_RESULT_SCORE_WEIGHTS,
}
REALIZED_PROCESS_SCORE_WEIGHTS = {
    "turn_timing": 0.08,
    "revision_discipline": 0.07,
}
REALIZED_RESULT_WEIGHT_TOTAL = sum(REALIZED_RESULT_SCORE_WEIGHTS.values())


def _round_record(record: dict[str, Any]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key, value in record.items():
        output[key] = round(value, 4) if isinstance(value, float) else value
    return output


def _cagr_pct(
    start_value: float,
    end_value: float,
    years: int,
    fallback_pct: float,
) -> float:
    if years <= 0 or start_value <= 0.0 or end_value <= 0.0:
        return fallback_pct
    return (math.pow(end_value / start_value, 1.0 / years) - 1.0) * 100.0


def accuracy_score_from_gap(
    gap_pct: float,
    catastrophic_gap_pct: float,
    exponent: float = 1.12,
) -> float:
    if catastrophic_gap_pct <= 0.0:
        return 100.0 if gap_pct <= 0.0 else 0.0
    unit = clamp(abs(gap_pct) / catastrophic_gap_pct, 0.0, 1.0)
    return 100.0 * (1.0 - math.pow(unit, exponent))


def direction_accuracy_score(
    predicted_growth_pct: float,
    true_growth_pct: float,
) -> float:
    if abs(true_growth_pct) <= 1.5:
        return 100.0 if abs(predicted_growth_pct) <= 4.0 else 62.0
    if predicted_growth_pct == 0.0:
        return 45.0
    return (
        100.0
        if (predicted_growth_pct > 0.0) == (true_growth_pct > 0.0)
        else 18.0
    )


def interval_calibration_score(row: dict[str, Any], horizon: float) -> float:
    low = as_float(row, "forecast_effective_passengers_low_million")
    high = as_float(row, "forecast_effective_passengers_high_million")
    mid = as_float(row, "forecast_effective_passengers_mid_million")
    true_value = as_float(row, "debug_hidden_true_effective_passengers_million")
    if true_value <= 0.0 or mid <= 0.0:
        return 0.0
    width_pct = (high - low) / mid * 100.0
    reasonable_width_pct = 7.0 + 1.8 * horizon
    inside = low <= true_value <= high
    if inside:
        wide_penalty = max(0.0, width_pct - reasonable_width_pct) * 1.25
        return clamp(94.0 - wide_penalty, 55.0, 100.0)
    miss_pct = 0.0
    if true_value < low:
        miss_pct = (low - true_value) / true_value * 100.0
    elif true_value > high:
        miss_pct = (true_value - high) / true_value * 100.0
    overconfidence_penalty = max(0.0, reasonable_width_pct - width_pct) * 0.7
    return clamp(44.0 - 4.0 * miss_pct - overconfidence_penalty, 0.0, 45.0)


def weighted_mean(values: list[tuple[float, float]]) -> float:
    total_weight = sum(weight for _, weight in values)
    if total_weight <= 0.0:
        return 0.0
    return sum(value * weight for value, weight in values) / total_weight


def weighted_component_share_gap(
    row: dict[str, Any],
    forecast_suffix: str,
    true_suffix: str,
) -> float:
    weighted_gaps: list[tuple[float, float]] = []
    for component in COMPONENTS:
        forecast_share = as_float(row, f"{component}_{forecast_suffix}")
        true_share = as_float(row, f"{component}_{true_suffix}")
        weighted_gaps.append(
            (abs(forecast_share - true_share), COMPONENT_SCORE_WEIGHTS[component])
        )
    return weighted_mean(weighted_gaps)


def component_potential_structure_score(
    row: dict[str, Any],
    horizon: float,
) -> float:
    weighted_gap_pp = weighted_component_share_gap(
        row,
        "forecast_potential_share_pct",
        "debug_hidden_true_potential_share_pct",
    )
    return accuracy_score_from_gap(weighted_gap_pp, 10.0 + 0.30 * horizon, 1.05)


def component_supply_structure_score(
    row: dict[str, Any],
    horizon: float,
) -> float:
    weighted_gap_pp = weighted_component_share_gap(
        row,
        "forecast_airline_supply_share_pct",
        "debug_hidden_true_airline_supply_share_pct",
    )
    return accuracy_score_from_gap(weighted_gap_pp, 12.0 + 0.35 * horizon, 1.05)


def component_fulfillment_score(row: dict[str, Any], horizon: float) -> float:
    weighted_gaps = [
        (
            abs(
                as_float(
                    row,
                    f"{component}_forecast_airline_supply_fulfillment_pct",
                )
                - as_float(
                    row,
                    f"{component}_debug_hidden_true_airline_supply_fulfillment_pct",
                )
            ),
            COMPONENT_SCORE_WEIGHTS[component],
        )
        for component in COMPONENTS
    ]
    return accuracy_score_from_gap(
        weighted_mean(weighted_gaps),
        30.0 + 0.8 * horizon,
        1.08,
    )


def component_interval_calibration_score(
    row: dict[str, Any],
    horizon: float,
) -> float:
    scores: list[tuple[float, float]] = []
    for component in COMPONENTS:
        low = as_float(
            row,
            f"{component}_forecast_effective_passengers_low_million",
        )
        high = as_float(
            row,
            f"{component}_forecast_effective_passengers_high_million",
        )
        mid = as_float(
            row,
            f"{component}_forecast_effective_passengers_mid_million",
        )
        true_value = as_float(
            row,
            f"{component}_debug_hidden_true_effective_passengers_million",
        )
        if true_value <= 0.0 or mid <= 0.0:
            score = 0.0
        else:
            width_pct = safe_divide(high - low, mid, 0.0) * 100.0
            reasonable_width_pct = (
                9.0 + 2.0 * horizon
            ) * COMPONENT_SHARE_UNCERTAINTY_MULTIPLIER[component]
            inside = low <= true_value <= high
            if inside:
                score = clamp(
                    94.0 - max(0.0, width_pct - reasonable_width_pct) * 1.05,
                    55.0,
                    100.0,
                )
            else:
                miss_pct = (
                    safe_divide(low - true_value, true_value, 0.0) * 100.0
                    if true_value < low
                    else safe_divide(true_value - high, true_value, 0.0) * 100.0
                )
                score = clamp(
                    44.0
                    - 3.6 * miss_pct
                    - max(0.0, reasonable_width_pct - width_pct) * 0.55,
                    0.0,
                    45.0,
                )
        scores.append((score, COMPONENT_SCORE_WEIGHTS[component]))
    return weighted_mean(scores)


def bottleneck_accuracy_score(row: dict[str, Any]) -> float:
    forecast = str(row.get("forecast_market_bottleneck") or "unknown")
    true = str(row.get("debug_hidden_true_market_bottleneck") or "unknown")
    if forecast == true:
        return 100.0
    potential = as_float(row, "debug_hidden_true_potential_passengers_million")
    airline_supply = as_float(
        row,
        "debug_hidden_true_airline_supply_passengers_million",
    )
    effective = as_float(row, "debug_hidden_true_effective_passengers_million")
    if effective > 0.0 and abs(potential - airline_supply) / effective <= 0.025:
        return 72.0
    return 25.0


def realized_bias_label(
    bias_pct: float,
    avg_abs_error_pct: float,
    interval_hit_rate_pct: float,
) -> str:
    if avg_abs_error_pct <= 2.5 and interval_hit_rate_pct >= 85.0:
        return "near_true_curve"
    if bias_pct >= 8.0:
        return "systematically_optimistic"
    if bias_pct <= -8.0:
        return "systematically_pessimistic"
    if interval_hit_rate_pct < 45.0 and avg_abs_error_pct >= 10.0:
        return "poorly_calibrated"
    if interval_hit_rate_pct < 55.0:
        return "range_misaligned"
    if avg_abs_error_pct <= 5.0:
        return "well_calibrated"
    return "mixed_quality"


def turn_timing_score(report_rows: list[dict[str, Any]]) -> float:
    if not report_rows:
        return 0.0
    first = report_rows[0]
    actual = int(as_float(first, "debug_hidden_signal_turn_year", 0))
    start = int(as_float(first, "forecast_turn_window_start_year", 0))
    end = int(as_float(first, "forecast_turn_window_end_year", 0))
    if actual <= 0 and start <= 0:
        return 90.0
    if actual <= 0 or start <= 0:
        return 42.0
    if start <= actual <= end:
        return 100.0
    distance = min(abs(actual - start), abs(actual - end))
    return clamp(100.0 - 17.0 * distance, 15.0, 95.0)


def total_revision_discipline_score(
    report_rows: list[dict[str, Any]],
) -> float:
    if not report_rows:
        return 0.0
    reason = str(report_rows[0].get("forecast_revision_reason") or "initial_report")
    if reason == "initial_report":
        return 92.0
    revision_magnitudes = [
        abs(as_float(row, "forecast_revision_pct"))
        for row in report_rows
        if row.get("forecast_previous_mid_million") not in (None, "")
    ]
    if not revision_magnitudes:
        return 86.0
    average_revision = mean(revision_magnitudes)
    evidence_reason = reason in {
        "realized_result_above_previous_view",
        "realized_result_below_previous_view",
        "airline_supply_signal_changed",
        "city_demand_signal_changed",
        "turning_window_shifted",
    }
    reasonable_revision = 7.0 if evidence_reason else 3.2
    excess = max(0.0, average_revision - reasonable_revision)
    timid_penalty = 12.0 if evidence_reason and average_revision < 0.35 else 0.0
    return clamp(94.0 - 7.5 * excess - timid_penalty, 0.0, 100.0)


def component_revision_discipline_score(
    report_rows: list[dict[str, Any]],
) -> float:
    if not report_rows:
        return 0.0
    reason = str(report_rows[0].get("forecast_revision_reason") or "initial_report")
    if reason == "initial_report":
        return 92.0
    revision_magnitudes = [
        abs(as_float(row, "forecast_component_revision_pp"))
        for row in report_rows
        if row.get("forecast_previous_mid_million") not in (None, "")
    ]
    if not revision_magnitudes:
        return 86.0
    average_revision = mean(revision_magnitudes)
    evidence_reason = reason in {
        "realized_result_above_previous_view",
        "realized_result_below_previous_view",
        "airline_supply_signal_changed",
        "city_demand_signal_changed",
        "turning_window_shifted",
    }
    reasonable_revision_pp = 2.8 if evidence_reason else 1.25
    excess = max(0.0, average_revision - reasonable_revision_pp)
    timid_penalty = 10.0 if evidence_reason and average_revision < 0.12 else 0.0
    return clamp(94.0 - 12.0 * excess - timid_penalty, 0.0, 100.0)


def revision_discipline_scores(
    report_rows: list[dict[str, Any]],
) -> tuple[float, float, float]:
    total_score = total_revision_discipline_score(report_rows)
    component_score = component_revision_discipline_score(report_rows)
    return total_score, component_score, 0.80 * total_score + 0.20 * component_score


def annotate_realized_quality_scores(
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for row in rows:
        key = (
            row.get("city_airport_market_id"),
            row.get("seed"),
            row.get("as_of_year"),
            row.get("forecast_report_id"),
        )
        grouped.setdefault(key, []).append(row)

    for report_rows in grouped.values():
        ordered = sorted(
            report_rows,
            key=lambda item: as_float(item, "forecast_horizon_years"),
        )
        if not ordered:
            continue
        if str(ordered[0].get("future_peek_mode")) == "true":
            for row in ordered:
                row.update(
                    _round_record(
                        {
                            "realized_score_method_version": REALIZED_SCORE_METHOD_VERSION,
                            "realized_report_quality_score": 100.0,
                            "realized_result_quality_score": 100.0,
                            "realized_report_process_quality_score": 100.0,
                            "realized_total_result_quality_score": 100.0,
                            "realized_component_result_quality_score": 100.0,
                            "realized_point_quality_score": 100.0,
                            "realized_midpoint_accuracy_score": 100.0,
                            "realized_trend_accuracy_score": 100.0,
                            "realized_shape_accuracy_score": 100.0,
                            "realized_component_structure_score": 100.0,
                            "realized_component_potential_structure_score": 100.0,
                            "realized_component_supply_structure_score": 100.0,
                            "realized_component_fulfillment_score": 100.0,
                            "realized_component_interval_calibration_score": 100.0,
                            "realized_bottleneck_accuracy_score": 100.0,
                            "realized_interval_calibration_score": 100.0,
                            "realized_turn_timing_score": 100.0,
                            "realized_revision_discipline_score": 100.0,
                            "realized_total_revision_discipline_score": 100.0,
                            "realized_component_revision_discipline_score": 100.0,
                            "realized_report_weighted_abs_error_pct": 0.0,
                            "realized_report_interval_hit_rate_pct": 100.0,
                            "realized_report_bias_pct": 0.0,
                            "realized_report_bias_label": "future_peek_exact",
                        }
                    )
                )
            continue

        current = as_float(ordered[0], "current_effective_passengers_million")
        prev_horizon = 0.0
        prev_mid = current
        prev_true = current
        point_metrics: list[dict[str, float]] = []
        for row in ordered:
            horizon = as_float(row, "forecast_horizon_years")
            weight = 1.0 + 0.08 * horizon
            mid = as_float(row, "forecast_effective_passengers_mid_million")
            true_value = as_float(
                row,
                "debug_hidden_true_effective_passengers_million",
            )
            signed_gap_pct = safe_divide(mid - true_value, true_value, 0.0) * 100.0
            abs_gap_pct = abs(signed_gap_pct)
            midpoint_score = accuracy_score_from_gap(
                abs_gap_pct,
                30.0 + 1.5 * horizon,
            )

            predicted_growth_pct = safe_divide(mid - current, current, 0.0) * 100.0
            true_growth_pct = safe_divide(true_value - current, current, 0.0) * 100.0
            growth_gap_pct = abs(predicted_growth_pct - true_growth_pct)
            growth_score = accuracy_score_from_gap(
                growth_gap_pct,
                34.0 + 2.0 * horizon,
            )
            trend_score = (
                0.72 * growth_score
                + 0.28
                * direction_accuracy_score(predicted_growth_pct, true_growth_pct)
            )

            step_years = max(1.0, horizon - prev_horizon)
            predicted_step_growth_pct = _cagr_pct(
                prev_mid,
                mid,
                int(round(step_years)),
                0.0,
            )
            true_step_growth_pct = _cagr_pct(
                prev_true,
                true_value,
                int(round(step_years)),
                0.0,
            )
            shape_score = accuracy_score_from_gap(
                abs(predicted_step_growth_pct - true_step_growth_pct),
                12.0,
            )

            interval_score = interval_calibration_score(row, horizon)
            component_potential_score = component_potential_structure_score(
                row,
                horizon,
            )
            component_supply_score = component_supply_structure_score(row, horizon)
            component_fulfillment = component_fulfillment_score(row, horizon)
            component_interval = component_interval_calibration_score(row, horizon)
            component_score = (
                REALIZED_COMPONENT_RESULT_SCORE_WEIGHTS[
                    "component_potential_structure"
                ]
                * component_potential_score
                + REALIZED_COMPONENT_RESULT_SCORE_WEIGHTS[
                    "component_supply_structure"
                ]
                * component_supply_score
                + REALIZED_COMPONENT_RESULT_SCORE_WEIGHTS["component_fulfillment"]
                * component_fulfillment
                + REALIZED_COMPONENT_RESULT_SCORE_WEIGHTS["component_interval"]
                * component_interval
            ) / sum(REALIZED_COMPONENT_RESULT_SCORE_WEIGHTS.values())
            bottleneck_score = bottleneck_accuracy_score(row)
            point_score = (
                REALIZED_RESULT_SCORE_WEIGHTS["midpoint"] * midpoint_score
                + REALIZED_RESULT_SCORE_WEIGHTS["trend"] * trend_score
                + REALIZED_RESULT_SCORE_WEIGHTS["shape"] * shape_score
                + REALIZED_RESULT_SCORE_WEIGHTS["bottleneck"] * bottleneck_score
                + REALIZED_RESULT_SCORE_WEIGHTS["interval"] * interval_score
                + REALIZED_RESULT_SCORE_WEIGHTS["component_potential_structure"]
                * component_potential_score
                + REALIZED_RESULT_SCORE_WEIGHTS["component_supply_structure"]
                * component_supply_score
                + REALIZED_RESULT_SCORE_WEIGHTS["component_fulfillment"]
                * component_fulfillment
                + REALIZED_RESULT_SCORE_WEIGHTS["component_interval"]
                * component_interval
            ) / REALIZED_RESULT_WEIGHT_TOTAL

            point_metrics.append(
                {
                    "weight": weight,
                    "signed_gap_pct": signed_gap_pct,
                    "abs_gap_pct": abs_gap_pct,
                    "midpoint_score": midpoint_score,
                    "trend_score": trend_score,
                    "shape_score": shape_score,
                    "component_score": component_score,
                    "component_potential_score": component_potential_score,
                    "component_supply_score": component_supply_score,
                    "component_fulfillment_score": component_fulfillment,
                    "component_interval_score": component_interval,
                    "bottleneck_score": bottleneck_score,
                    "interval_score": interval_score,
                    "point_score": point_score,
                    "inside": (
                        1.0
                        if str(row.get("debug_hidden_true_inside_forecast_range"))
                        == "true"
                        else 0.0
                    ),
                }
            )
            prev_horizon = horizon
            prev_mid = mid
            prev_true = true_value

        report_midpoint_score = weighted_mean(
            [(item["midpoint_score"], item["weight"]) for item in point_metrics]
        )
        report_trend_score = weighted_mean(
            [(item["trend_score"], item["weight"]) for item in point_metrics]
        )
        report_shape_score = weighted_mean(
            [(item["shape_score"], item["weight"]) for item in point_metrics]
        )
        report_component_score = weighted_mean(
            [(item["component_score"], item["weight"]) for item in point_metrics]
        )
        report_component_potential_score = weighted_mean(
            [
                (item["component_potential_score"], item["weight"])
                for item in point_metrics
            ]
        )
        report_component_supply_score = weighted_mean(
            [
                (item["component_supply_score"], item["weight"])
                for item in point_metrics
            ]
        )
        report_component_fulfillment_score = weighted_mean(
            [
                (item["component_fulfillment_score"], item["weight"])
                for item in point_metrics
            ]
        )
        report_component_interval_score = weighted_mean(
            [
                (item["component_interval_score"], item["weight"])
                for item in point_metrics
            ]
        )
        report_bottleneck_score = weighted_mean(
            [(item["bottleneck_score"], item["weight"]) for item in point_metrics]
        )
        report_interval_score = weighted_mean(
            [(item["interval_score"], item["weight"]) for item in point_metrics]
        )
        report_score = (
            REALIZED_RESULT_SCORE_WEIGHTS["midpoint"] * report_midpoint_score
            + REALIZED_RESULT_SCORE_WEIGHTS["trend"] * report_trend_score
            + REALIZED_RESULT_SCORE_WEIGHTS["shape"] * report_shape_score
            + REALIZED_RESULT_SCORE_WEIGHTS["bottleneck"] * report_bottleneck_score
            + REALIZED_RESULT_SCORE_WEIGHTS["interval"] * report_interval_score
            + REALIZED_RESULT_SCORE_WEIGHTS["component_potential_structure"]
            * report_component_potential_score
            + REALIZED_RESULT_SCORE_WEIGHTS["component_supply_structure"]
            * report_component_supply_score
            + REALIZED_RESULT_SCORE_WEIGHTS["component_fulfillment"]
            * report_component_fulfillment_score
            + REALIZED_RESULT_SCORE_WEIGHTS["component_interval"]
            * report_component_interval_score
        ) / REALIZED_RESULT_WEIGHT_TOTAL
        report_total_score = (
            REALIZED_TOTAL_RESULT_SCORE_WEIGHTS["midpoint"] * report_midpoint_score
            + REALIZED_TOTAL_RESULT_SCORE_WEIGHTS["trend"] * report_trend_score
            + REALIZED_TOTAL_RESULT_SCORE_WEIGHTS["shape"] * report_shape_score
            + REALIZED_TOTAL_RESULT_SCORE_WEIGHTS["bottleneck"]
            * report_bottleneck_score
            + REALIZED_TOTAL_RESULT_SCORE_WEIGHTS["interval"]
            * report_interval_score
        ) / sum(REALIZED_TOTAL_RESULT_SCORE_WEIGHTS.values())
        weighted_abs_error_pct = weighted_mean(
            [(item["abs_gap_pct"], item["weight"]) for item in point_metrics]
        )
        weighted_bias_pct = weighted_mean(
            [(item["signed_gap_pct"], item["weight"]) for item in point_metrics]
        )
        interval_hit_rate_pct = 100.0 * mean(
            item["inside"] for item in point_metrics
        )
        bias_label = realized_bias_label(
            weighted_bias_pct,
            weighted_abs_error_pct,
            interval_hit_rate_pct,
        )
        report_turn_score = turn_timing_score(ordered)
        (
            report_total_revision_score,
            report_component_revision_score,
            report_revision_score,
        ) = revision_discipline_scores(ordered)
        report_process_score = (
            REALIZED_RESULT_WEIGHT_TOTAL * report_score
            + REALIZED_PROCESS_SCORE_WEIGHTS["turn_timing"] * report_turn_score
            + REALIZED_PROCESS_SCORE_WEIGHTS["revision_discipline"]
            * report_revision_score
        )

        for row, metric in zip(ordered, point_metrics):
            row.update(
                _round_record(
                    {
                        "realized_score_method_version": REALIZED_SCORE_METHOD_VERSION,
                        "realized_report_quality_score": report_process_score,
                        "realized_result_quality_score": report_score,
                        "realized_report_process_quality_score": report_process_score,
                        "realized_total_result_quality_score": report_total_score,
                        "realized_component_result_quality_score": report_component_score,
                        "realized_point_quality_score": metric["point_score"],
                        "realized_midpoint_accuracy_score": metric["midpoint_score"],
                        "realized_trend_accuracy_score": metric["trend_score"],
                        "realized_shape_accuracy_score": metric["shape_score"],
                        "realized_component_structure_score": metric[
                            "component_score"
                        ],
                        "realized_component_potential_structure_score": metric[
                            "component_potential_score"
                        ],
                        "realized_component_supply_structure_score": metric[
                            "component_supply_score"
                        ],
                        "realized_component_fulfillment_score": metric[
                            "component_fulfillment_score"
                        ],
                        "realized_component_interval_calibration_score": metric[
                            "component_interval_score"
                        ],
                        "realized_bottleneck_accuracy_score": metric[
                            "bottleneck_score"
                        ],
                        "realized_interval_calibration_score": metric[
                            "interval_score"
                        ],
                        "realized_turn_timing_score": report_turn_score,
                        "realized_revision_discipline_score": report_revision_score,
                        "realized_total_revision_discipline_score": (
                            report_total_revision_score
                        ),
                        "realized_component_revision_discipline_score": (
                            report_component_revision_score
                        ),
                        "realized_report_weighted_abs_error_pct": (
                            weighted_abs_error_pct
                        ),
                        "realized_report_interval_hit_rate_pct": (
                            interval_hit_rate_pct
                        ),
                        "realized_report_bias_pct": weighted_bias_pct,
                        "realized_report_bias_label": bias_label,
                    }
                )
            )
    return rows
