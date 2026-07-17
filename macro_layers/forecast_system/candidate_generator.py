from __future__ import annotations

import hashlib
from importlib import import_module
import json
from pathlib import Path
from typing import Any, Callable

from .profile_config import (
    DEFAULT_NARRATIVE_CATALOG,
    DEFAULT_TIER_CATALOG,
    catalog_items,
    catalog_path,
    resolve_forecast_report_profiles,
)
from .scoring import REALIZED_SCORE_METHOD_VERSION
from .viewer_assets import forecast_viewer_config


_PARENT_PACKAGE = (
    (__package__ or "").rsplit(".", 1)[0]
    if "." in (__package__ or "")
    else ""
)
_PARENT_PREFIX = f"{_PARENT_PACKAGE}." if _PARENT_PACKAGE else ""
simulation_utils = import_module(f"{_PARENT_PREFIX}simulation_utils")
as_float = simulation_utils.as_float_convert_lookup_default

FORECAST_CANDIDATE_GENERATOR_VERSION = "audit-forecast-candidate-generator-v2"
FORECAST_CANDIDATE_MIN_SCORE_BAND_WIDTH = 8.0
FORECAST_CANDIDATE_MAX_ATTEMPTS = 48
FORECAST_CANDIDATE_INCOMPATIBLE_MODIFIER_PAIRS = (
    ("optimistic_v2", "pessimistic_v2"),
    ("trend_following_v2", "mean_reverting_v2"),
    ("slow_revision_v2", "fast_revision_v2"),
    ("overconfident_v2", "wide_uncertainty_v2"),
)


def stable_unit_float(*parts: Any) -> float:
    raw = "::".join(str(part) for part in parts).encode("utf-8")
    digest = hashlib.sha256(raw).digest()
    return int.from_bytes(digest[:8], "big") / float(1 << 64)


def interpolate(low: float, high: float, unit: float) -> float:
    return low + (high - low) * simulation_utils.clamp(unit, 0.0, 1.0)


def _forecast_candidate_catalog_sources(
    config_path: Path,
) -> tuple[
    dict[str, Any],
    dict[str, dict[str, Any]],
    dict[str, dict[str, Any]],
    dict[str, dict[str, Any]],
]:
    config_path = config_path.resolve()
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    if raw.get("schema_version") != "city-airport-potential-passenger-forecast-config-v1":
        raise ValueError(f"Unsupported forecast candidate config schema in {config_path}")
    tier_profiles = catalog_items(
        catalog_path(
            config_path,
            raw.get("forecast_report_tier_catalog"),
            DEFAULT_TIER_CATALOG,
        ),
        expected_schema="forecast-report-tier-profile-catalog-v1",
        collection="profiles",
        id_field="forecast_report_tier_profile_id",
    )
    narrative_catalog_path = catalog_path(
        config_path,
        raw.get("forecast_narrative_catalog"),
        DEFAULT_NARRATIVE_CATALOG,
    )
    narrative_profiles = catalog_items(
        narrative_catalog_path,
        expected_schema="forecast-narrative-profile-catalog-v1",
        collection="profiles",
        id_field="forecast_narrative_profile_id",
    )
    narrative_modifiers = catalog_items(
        narrative_catalog_path,
        expected_schema="forecast-narrative-profile-catalog-v1",
        collection="modifiers",
        id_field="forecast_narrative_modifier_id",
    )
    return raw, tier_profiles, narrative_profiles, narrative_modifiers


def forecast_candidate_catalog(config_path: Path) -> dict[str, Any]:
    _, tier_profiles, narrative_profiles, narrative_modifiers = (
        _forecast_candidate_catalog_sources(config_path)
    )
    tiers: list[dict[str, Any]] = []
    for profile_id, profile in tier_profiles.items():
        settings = profile.get("candidate_generation")
        if not isinstance(settings, dict):
            continue
        tiers.append(
            {
                "tierProfileId": profile_id,
                "tierId": str(settings.get("tier_id") or profile_id),
                "label": str(settings.get("tier_label") or profile_id),
                "naturalHorizonYears": int(settings.get("natural_horizon_years", 0)),
                "qualityMinScore": float(settings.get("quality_min_score", 0.0)),
                "qualityMaxScore": float(settings.get("quality_max_score", 0.0)),
            }
        )
    styles: list[dict[str, Any]] = []
    for profile_id, profile in narrative_profiles.items():
        if profile_id == "future_truth_v2":
            continue
        modifier_ids = [
            str(value)
            for value in profile.get("candidate_modifier_ids", [])
            if str(value) in narrative_modifiers
        ]
        styles.append(
            {
                "narrativeProfileId": profile_id,
                "label": str(profile.get("narrative_style_label") or profile_id),
                "summary": str(profile.get("narrative_style_summary") or ""),
                "method": str(profile.get("narrative_style_method") or ""),
                "blindSpot": str(profile.get("narrative_style_blind_spot") or ""),
                "candidateModifierIds": modifier_ids,
            }
        )
    modifiers = [
        {
            "modifierId": modifier_id,
            "label": str(modifier.get("modifier_label") or modifier_id),
            "group": str(modifier.get("modifier_group") or "other"),
            "description": str(modifier.get("modifier_description") or ""),
            "tradeoff": str(modifier.get("modifier_tradeoff") or ""),
        }
        for modifier_id, modifier in narrative_modifiers.items()
    ]
    return {
        "generatorVersion": FORECAST_CANDIDATE_GENERATOR_VERSION,
        "scoreMethodVersion": REALIZED_SCORE_METHOD_VERSION,
        "minimumScoreBandWidth": FORECAST_CANDIDATE_MIN_SCORE_BAND_WIDTH,
        "maximumAttempts": FORECAST_CANDIDATE_MAX_ATTEMPTS,
        "tiers": tiers,
        "styles": styles,
        "modifiers": modifiers,
        "incompatibleModifierPairs": [
            list(pair) for pair in FORECAST_CANDIDATE_INCOMPATIBLE_MODIFIER_PAIRS
        ],
    }


def _candidate_modifiers_are_compatible(modifier_ids: list[str]) -> bool:
    selected = set(modifier_ids)
    return not any(set(pair).issubset(selected) for pair in FORECAST_CANDIDATE_INCOMPATIBLE_MODIFIER_PAIRS)


def _validated_candidate_modifier_ids(
    modifier_ids: list[str],
    *,
    style: dict[str, Any],
    modifiers: dict[str, dict[str, Any]],
) -> list[str]:
    clean = [str(value).strip() for value in modifier_ids if str(value).strip()]
    if len(clean) != len(set(clean)):
        raise ValueError("forecast candidate modifiers must be unique")
    if len(clean) > 2:
        raise ValueError("forecast candidate may use at most two modifiers")
    allowed = {str(value) for value in style.get("candidate_modifier_ids", [])}
    unknown = [value for value in clean if value not in modifiers]
    if unknown:
        raise ValueError(f"unknown forecast candidate modifier: {unknown[0]}")
    disallowed = [value for value in clean if value not in allowed]
    if disallowed:
        raise ValueError(f"modifier is not compatible with selected style: {disallowed[0]}")
    if not _candidate_modifiers_are_compatible(clean):
        raise ValueError("forecast candidate modifiers contain an incompatible pair")
    return clean


def _candidate_modifier_options(
    style: dict[str, Any],
    modifiers: dict[str, dict[str, Any]],
) -> list[list[str]]:
    pool = [
        str(value)
        for value in style.get("candidate_modifier_ids", [])
        if str(value) in modifiers
    ]
    options: list[list[str]] = [[]]
    options.extend([[value] for value in pool])
    for left_index, left in enumerate(pool):
        for right in pool[left_index + 1 :]:
            pair = [left, right]
            if _candidate_modifiers_are_compatible(pair):
                options.append(pair)
    return options


def _candidate_modifier_ids_for_attempt(
    *,
    mode: str,
    requested_modifier_ids: list[str],
    style: dict[str, Any],
    modifiers: dict[str, dict[str, Any]],
    seed: int,
    as_of_year: int,
    tier_profile_id: str,
    narrative_profile_id: str,
    generation_nonce: int,
    attempt: int,
) -> list[str]:
    if mode == "pure":
        return []
    if mode == "manual":
        return _validated_candidate_modifier_ids(
            requested_modifier_ids,
            style=style,
            modifiers=modifiers,
        )
    if mode != "auto":
        raise ValueError("modifier mode must be auto, pure, or manual")
    options = _candidate_modifier_options(style, modifiers)
    unit = stable_unit_float(
        "forecast_candidate_modifier_set",
        seed,
        as_of_year,
        tier_profile_id,
        narrative_profile_id,
        generation_nonce,
        attempt,
    )
    index = min(len(options) - 1, int(unit * len(options)))
    return options[index]


def _candidate_bias_direction(
    narrative_profile_id: str,
    modifier_ids: list[str],
) -> str:
    if "optimistic_v2" in modifier_ids:
        return "mostly_optimistic"
    if "pessimistic_v2" in modifier_ids:
        return "mostly_pessimistic"
    if narrative_profile_id == "hot_growth_story_v2":
        return "mostly_optimistic"
    if narrative_profile_id in {"conservative_scenario_v2", "macro_aviation_research_v2"}:
        return "mostly_pessimistic"
    return "mixed"


def _candidate_report_id(
    *,
    seed: int,
    as_of_year: int,
    tier_profile_id: str,
    narrative_profile_id: str,
    modifier_ids: list[str],
    generation_nonce: int,
    attempt: int,
) -> str:
    identity = "|".join(
        [
            str(seed),
            str(as_of_year),
            tier_profile_id,
            narrative_profile_id,
            ",".join(modifier_ids),
            str(generation_nonce),
            str(attempt),
        ]
    )
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16]
    return f"audit_candidate_{digest}"


def _build_forecast_candidate_attempt(
    city_airport_rows: list[dict[str, Any]],
    *,
    config_path: Path,
    raw_config: dict[str, Any],
    tier_profile: dict[str, Any],
    narrative_profile: dict[str, Any],
    narrative_modifiers: dict[str, dict[str, Any]],
    seed: int,
    as_of_year: int,
    tier_profile_id: str,
    narrative_profile_id: str,
    modifier_mode: str,
    requested_modifier_ids: list[str],
    generation_nonce: int,
    attempt: int,
    simulate_forecast: Callable[[list[dict[str, Any]], dict[str, Any]], list[dict[str, Any]]],
) -> dict[str, Any]:
    modifier_ids = _candidate_modifier_ids_for_attempt(
        mode=modifier_mode,
        requested_modifier_ids=requested_modifier_ids,
        style=narrative_profile,
        modifiers=narrative_modifiers,
        seed=seed,
        as_of_year=as_of_year,
        tier_profile_id=tier_profile_id,
        narrative_profile_id=narrative_profile_id,
        generation_nonce=generation_nonce,
        attempt=attempt,
    )
    report_id = _candidate_report_id(
        seed=seed,
        as_of_year=as_of_year,
        tier_profile_id=tier_profile_id,
        narrative_profile_id=narrative_profile_id,
        modifier_ids=modifier_ids,
        generation_nonce=generation_nonce,
        attempt=attempt,
    )
    settings = tier_profile.get("candidate_generation")
    if not isinstance(settings, dict):
        raise ValueError(f"tier does not support candidate generation: {tier_profile_id}")
    quality_min = float(settings.get("quality_min_score", 0.0))
    quality_max = float(settings.get("quality_max_score", quality_min))
    quality = interpolate(
        quality_min,
        quality_max,
        stable_unit_float("forecast_candidate_quality", report_id),
    )
    error_band_points = list(settings.get("reported_error_band_points", []))
    default_band = (
        float(error_band_points[-1].get("value", 15.0))
        if error_band_points
        else 15.0
    )
    report = {
        "forecast_report_id": report_id,
        "forecast_report_tier_profile_id": tier_profile_id,
        "forecast_narrative_profile_id": narrative_profile_id,
        "forecast_narrative_modifier_ids": modifier_ids,
        "forecast_report_display_name": str(
            narrative_profile.get("narrative_style_label") or narrative_profile_id
        ),
        "forecast_report_tier": str(settings.get("tier_id") or tier_profile_id),
        "forecast_report_source": "audit_candidate_generator",
        "reported_confidence_style": "standalone_audit_candidate",
        "forecast_bias_direction": _candidate_bias_direction(
            narrative_profile_id,
            modifier_ids,
        ),
        "forecast_quality_score": quality,
        "calibration_score": quality,
        "future_peek_mode": False,
        "forecast_horizon_max_years": int(settings["natural_horizon_years"]),
        "derive_seed_signal_from_quality": True,
        "seed_signal_min_pct": float(settings.get("signal_capture_min_pct", 15.0)),
        "seed_signal_max_pct": float(settings.get("signal_capture_max_pct", 70.0)),
        "derive_bias_cap_from_quality": True,
        "bias_cap_at_score_0_pct": float(settings.get("bias_cap_at_score_0_pct", 18.0)),
        "bias_cap_at_score_70_pct": float(settings.get("bias_cap_at_score_70_pct", 3.5)),
        "consensus_herding_bias_cap_pct": float(
            settings.get("consensus_herding_bias_cap_pct", 0.0)
        ),
        "reported_confidence_base_pct": float(
            settings.get("reported_confidence_base_pct", 70.0)
        ),
        "reported_confidence_horizon_decay_pct": float(
            settings.get("reported_confidence_horizon_decay_pct", 1.0)
        ),
        "reported_confidence_noise_pct": float(
            settings.get("reported_confidence_noise_pct", 2.5)
        ),
        "default_reported_error_band_pct": default_band,
        "reported_error_band_points": error_band_points,
    }
    candidate_config = json.loads(json.dumps(raw_config, ensure_ascii=False))
    candidate_config["config_version"] = (
        f"{raw_config.get('config_version', 'forecast-config')}-candidate-v2"
    )
    candidate_config.setdefault("timeline", {})["player_decision_start_year"] = as_of_year
    years = sorted(int(as_float(row, "year")) for row in city_airport_rows)
    candidate_config.setdefault("forecast", {})["as_of_frequency_years"] = (
        years[-1] - years[0] + 2
    )
    candidate_config["forecast_reports"] = [report]
    candidate_config["forecast_reports"] = resolve_forecast_report_profiles(
        candidate_config,
        config_path.resolve(),
    )
    rows = simulate_forecast(
        city_airport_rows,
        candidate_config,
    )
    rows = [row for row in rows if int(as_float(row, "as_of_year")) == as_of_year]
    if len(rows) != int(settings["natural_horizon_years"]):
        raise ValueError("forecast candidate did not produce its full natural horizon")
    first = rows[0]
    if str(first.get("forecast_revision_reason")) != "initial_report":
        raise ValueError("standalone forecast candidate must be an initial report")
    return {
        "candidateId": report_id,
        "attempt": attempt,
        "configuredQualityScore": round(quality, 4),
        "modifierIds": modifier_ids,
        "modifierLabels": list(
            candidate_config["forecast_reports"][0].get(
                "forecast_narrative_modifier_labels",
                [],
            )
        ),
        "actualScore": float(first["realized_report_process_quality_score"]),
        "resultScore": float(first["realized_result_quality_score"]),
        "totalResultScore": float(first["realized_total_result_quality_score"]),
        "componentResultScore": float(
            first["realized_component_result_quality_score"]
        ),
        "componentPotentialStructureScore": float(
            first["realized_component_potential_structure_score"]
        ),
        "componentSupplyStructureScore": float(
            first["realized_component_supply_structure_score"]
        ),
        "componentFulfillmentScore": float(
            first["realized_component_fulfillment_score"]
        ),
        "componentIntervalScore": float(
            first["realized_component_interval_calibration_score"]
        ),
        "turnTimingScore": float(first["realized_turn_timing_score"]),
        "revisionDisciplineScore": float(first["realized_revision_discipline_score"]),
        "weightedAbsErrorPct": float(first["realized_report_weighted_abs_error_pct"]),
        "intervalHitRatePct": float(first["realized_report_interval_hit_rate_pct"]),
        "reportMeta": forecast_viewer_config(
            candidate_config,
            include_audit=True,
        )["forecast_reports"][0],
        "rows": rows,
    }


def generate_forecast_candidate(
    city_airport_rows: list[dict[str, Any]],
    *,
    config_path: Path,
    seed: int,
    as_of_year: int,
    tier_profile_id: str,
    narrative_profile_id: str,
    modifier_mode: str,
    modifier_ids: list[str],
    score_min: float,
    score_max: float,
    generation_nonce: int,
    simulate_forecast: Callable[[list[dict[str, Any]], dict[str, Any]], list[dict[str, Any]]],
) -> dict[str, Any]:
    if not city_airport_rows:
        raise ValueError("forecast candidate requires city market rows")
    row_seeds = {int(as_float(row, "seed")) for row in city_airport_rows}
    if row_seeds != {int(seed)}:
        raise ValueError("forecast candidate seed does not match city market rows")
    years = sorted({int(as_float(row, "year")) for row in city_airport_rows})
    if as_of_year not in years:
        raise ValueError("forecast candidate as-of year is not available")
    if not 0.0 <= score_min < score_max <= 100.0:
        raise ValueError("forecast candidate score range must be within 0 to 100")
    if score_max - score_min < FORECAST_CANDIDATE_MIN_SCORE_BAND_WIDTH:
        raise ValueError(
            f"forecast candidate score range must be at least {FORECAST_CANDIDATE_MIN_SCORE_BAND_WIDTH:g} points wide"
        )
    if not 0 <= generation_nonce <= 1_000_000:
        raise ValueError("forecast candidate generation nonce is out of range")

    raw, tier_profiles, narrative_profiles, narrative_modifiers = (
        _forecast_candidate_catalog_sources(config_path)
    )
    tier_profile = tier_profiles.get(tier_profile_id)
    if tier_profile is None or not isinstance(tier_profile.get("candidate_generation"), dict):
        raise ValueError("unknown or unsupported forecast candidate tier")
    narrative_profile = narrative_profiles.get(narrative_profile_id)
    if narrative_profile is None or narrative_profile_id == "future_truth_v2":
        raise ValueError("unknown or unsupported forecast candidate style")
    settings = tier_profile["candidate_generation"]
    natural_horizon = int(settings["natural_horizon_years"])
    if as_of_year + natural_horizon > years[-1]:
        raise ValueError(
            f"insufficient future years: {settings.get('tier_label', tier_profile_id)} requires {natural_horizon} years through {as_of_year + natural_horizon}, but the current data ends in {years[-1]}"
        )
    if modifier_mode == "manual":
        _validated_candidate_modifier_ids(
            modifier_ids,
            style=narrative_profile,
            modifiers=narrative_modifiers,
        )
    elif modifier_mode not in {"auto", "pure"}:
        raise ValueError("modifier mode must be auto, pure, or manual")

    center = (score_min + score_max) / 2.0
    hits: list[dict[str, Any]] = []
    nearest: dict[str, Any] | None = None
    attempts_evaluated = 0
    for attempt in range(FORECAST_CANDIDATE_MAX_ATTEMPTS):
        candidate = _build_forecast_candidate_attempt(
            city_airport_rows,
            simulate_forecast=simulate_forecast,
            config_path=config_path,
            raw_config=raw,
            tier_profile=tier_profile,
            narrative_profile=narrative_profile,
            narrative_modifiers=narrative_modifiers,
            seed=seed,
            as_of_year=as_of_year,
            tier_profile_id=tier_profile_id,
            narrative_profile_id=narrative_profile_id,
            modifier_mode=modifier_mode,
            requested_modifier_ids=modifier_ids,
            generation_nonce=generation_nonce,
            attempt=attempt,
        )
        attempts_evaluated += 1
        score = float(candidate["actualScore"])
        distance = 0.0 if score_min <= score <= score_max else min(
            abs(score - score_min),
            abs(score - score_max),
        )
        candidate["scoreDistanceToTarget"] = round(distance, 4)
        if nearest is None or (
            distance,
            abs(score - center),
            candidate["candidateId"],
        ) < (
            float(nearest["scoreDistanceToTarget"]),
            abs(float(nearest["actualScore"]) - center),
            str(nearest["candidateId"]),
        ):
            nearest = candidate
        if distance == 0.0:
            hits.append(candidate)
        if attempts_evaluated >= 16 and len(hits) >= 4:
            break

    selected = min(
        hits,
        key=lambda item: (
            abs(float(item["actualScore"]) - center),
            str(item["candidateId"]),
        ),
    ) if hits else nearest
    if selected is None:
        raise ValueError("forecast candidate search produced no candidates")
    match_status = "matched" if hits else "nearest"
    return {
        "generatorVersion": FORECAST_CANDIDATE_GENERATOR_VERSION,
        "scoreMethodVersion": REALIZED_SCORE_METHOD_VERSION,
        "request": {
            "seed": seed,
            "asOfYear": as_of_year,
            "tierProfileId": tier_profile_id,
            "narrativeProfileId": narrative_profile_id,
            "modifierMode": modifier_mode,
            "modifierIds": modifier_ids,
            "scoreMin": score_min,
            "scoreMax": score_max,
            "generationNonce": generation_nonce,
        },
        "matchStatus": match_status,
        "attemptsEvaluated": attempts_evaluated,
        "naturalHorizonYears": natural_horizon,
        "dataFinalYear": years[-1],
        "firstPublication": True,
        "candidate": selected,
    }


