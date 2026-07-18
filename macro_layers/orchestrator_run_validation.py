from __future__ import annotations

from collections.abc import Callable, Collection, Mapping
from pathlib import Path
from typing import Any


COUNT_PATTERNS = {
    "global_rows": "global_macro/global_macro_feedback_seed_sweep.csv",
    "regional_rows": "regional_macro/*/*_regional_macro_seed_sweep.csv",
    "reconciled_rows": "regional_macro_reconciled/regional_macro_reconciled_seed_sweep.csv",
    "aviation_rows": "regional_aviation_demand/*/*_aviation_demand_seed_sweep.csv",
    "supply_rows": "regional_air_capacity_supply/*/*_air_capacity_supply_seed_sweep.csv",
    "city_airport_rows": "city_airport_market_demand/*/*_city_airport_demand_seed_sweep.csv",
    "potential_passenger_forecast_rows": (
        "city_airport_potential_passenger_forecast/*/*_potential_passenger_forecast_seed_sweep.csv"
    ),
    "quarterly_operations_rows": (
        "city_airport_quarterly_operations/*/*_quarterly_operations_seed_sweep.csv"
    ),
    "financial_state_rows": (
        "city_airport_financial_state/*/*_financial_state_seed_sweep.csv"
    ),
    "valuation_rows": "city_airport_valuation/*/*_valuation_forecast_seed_sweep.csv",
}

FULL_REGION_FIELDS = frozenset(
    {"regional_rows", "reconciled_rows", "aviation_rows", "supply_rows"}
)


def csv_data_row_count(path: Path, *, csv_module: Any) -> int:
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv_module.reader(handle)
        next(reader, None)
        return sum(1 for _ in reader)


def glob_csv_row_count(
    root: Path,
    pattern: str,
    *,
    csv_data_row_count: Callable[[Path], int],
) -> int:
    return sum(
        csv_data_row_count(path)
        for path in root.glob(pattern)
        if path.is_file()
    )


def inspect_staged_csv(
    path: Path,
    expected_seed: int,
    start_year: int,
    final_year: int,
    *,
    csv_module: Any,
) -> dict[str, Any]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv_module.reader(handle)
        header = next(reader, None)
        if not header or any(not str(field).strip() for field in header):
            raise ValueError(f"staged CSV has an empty header: {path}")
        if len(header) != len(set(header)):
            raise ValueError(f"staged CSV has duplicate header fields: {path}")
        if "seed" not in header:
            raise ValueError(f"staged CSV is missing seed field: {path}")

        seed_index = header.index("seed")
        year_index = header.index("year") if "year" in header else None
        year_offset_index = (
            header.index("year_index") if "year_index" in header else None
        )
        region_index = (
            header.index("region_id") if "region_id" in header else None
        )
        regions: set[str] = set()
        row_count = 0
        for row_number, row in enumerate(reader, start=2):
            if len(row) != len(header):
                raise ValueError(
                    f"staged CSV row width mismatch at {path}:{row_number}: "
                    f"expected {len(header)}, got {len(row)}"
                )
            try:
                row_seed = int(float(row[seed_index]))
            except (TypeError, ValueError) as error:
                raise ValueError(
                    f"staged CSV has invalid seed at {path}:{row_number}"
                ) from error
            if row_seed != expected_seed:
                raise ValueError(
                    f"staged CSV seed mismatch at {path}:{row_number}: "
                    f"expected {expected_seed}, got {row_seed}"
                )
            if year_index is not None:
                try:
                    row_year = int(float(row[year_index]))
                except (TypeError, ValueError) as error:
                    raise ValueError(
                        f"staged CSV has invalid year at {path}:{row_number}"
                    ) from error
                if row_year < start_year or row_year > final_year:
                    raise ValueError(
                        f"staged CSV year outside Run range at "
                        f"{path}:{row_number}: {row_year}"
                    )
            if year_offset_index is not None:
                try:
                    row_year_index = int(float(row[year_offset_index]))
                except (TypeError, ValueError) as error:
                    raise ValueError(
                        f"staged CSV has invalid year_index at "
                        f"{path}:{row_number}"
                    ) from error
                if row_year_index < 0 or row_year_index > final_year - start_year:
                    raise ValueError(
                        f"staged CSV year_index outside Run range at "
                        f"{path}:{row_number}: {row_year_index}"
                    )
            if region_index is not None and row[region_index]:
                regions.add(row[region_index])
            row_count += 1

    return {
        "row_count": row_count,
        "header": header,
        "regions": regions,
    }


def validate_staged_run(
    run_dir: Path,
    manifest: dict[str, Any],
    *,
    region_order: Collection[str],
    inspect_staged_csv: Callable[[Path, int, int, int], dict[str, Any]],
    hashlib_module: Any,
    time_module: Any,
    count_patterns: Mapping[str, str] = COUNT_PATTERNS,
    full_region_fields: Collection[str] = FULL_REGION_FIELDS,
) -> dict[str, Any]:
    variants = manifest.get("variants")
    if not isinstance(variants, dict) or not variants:
        raise ValueError("Run manifest has no variants")

    expected_seed = int(manifest["seed"])
    start_year = int(manifest["start_year"])
    final_year = start_year + int(manifest["years"])
    checks: dict[str, dict[str, int]] = {}
    file_counts: dict[str, dict[str, int]] = {}
    header_digests: dict[str, dict[str, str]] = {}
    region_coverage: dict[str, dict[str, list[str]]] = {}
    expected_regions = set(region_order)
    full_region_field_set = set(full_region_fields)
    for variant_id, raw_meta in variants.items():
        meta = raw_meta if isinstance(raw_meta, dict) else {}
        variant_dir = run_dir / str(variant_id)
        if not variant_dir.is_dir():
            raise FileNotFoundError(
                f"missing staged variant directory: {variant_dir}"
            )
        skip_manifest = variant_dir / "city_airport_downstream_skips.json"
        if not skip_manifest.is_file():
            raise FileNotFoundError(
                f"missing staged downstream skip manifest: {skip_manifest}"
            )
        variant_checks: dict[str, int] = {}
        variant_file_counts: dict[str, int] = {}
        variant_header_digests: dict[str, str] = {}
        variant_region_coverage: dict[str, list[str]] = {}
        for field, pattern in count_patterns.items():
            expected = int(meta.get(field, 0) or 0)
            paths = sorted(
                path for path in variant_dir.glob(pattern) if path.is_file()
            )
            header_digest = hashlib_module.sha256()
            regions: set[str] = set()
            actual = 0
            for path in paths:
                inspection = inspect_staged_csv(
                    path,
                    expected_seed,
                    start_year,
                    final_year,
                )
                actual += int(inspection["row_count"])
                regions.update(inspection["regions"])
                header_digest.update(
                    path.relative_to(variant_dir).as_posix().encode("utf-8")
                )
                header_digest.update(b"\0")
                header_digest.update(
                    ",".join(inspection["header"]).encode("utf-8")
                )
                header_digest.update(b"\0")
            if actual != expected:
                raise ValueError(
                    f"staged row count mismatch for {variant_id}/{field}: "
                    f"expected {expected}, got {actual}"
                )
            if (
                expected > 0
                and field in full_region_field_set
                and regions != expected_regions
            ):
                missing = sorted(expected_regions - regions)
                unexpected = sorted(regions - expected_regions)
                raise ValueError(
                    f"staged region coverage mismatch for {variant_id}/{field}: "
                    f"missing={missing}, unexpected={unexpected}"
                )
            variant_checks[field] = actual
            variant_file_counts[field] = len(paths)
            variant_header_digests[field] = header_digest.hexdigest()
            if field in full_region_field_set:
                variant_region_coverage[field] = sorted(regions)
        checks[str(variant_id)] = variant_checks
        file_counts[str(variant_id)] = variant_file_counts
        header_digests[str(variant_id)] = variant_header_digests
        region_coverage[str(variant_id)] = variant_region_coverage
    return {
        "schema_version": "airport-run-validation-v1",
        "validated_at": time_module.strftime("%Y-%m-%d %H:%M:%S"),
        "variant_count": len(variants),
        "row_counts": checks,
        "file_counts": file_counts,
        "header_digests": header_digests,
        "region_coverage": region_coverage,
    }


def write_validated_run_manifest(
    run_dir: Path,
    manifest: dict[str, Any],
    *,
    write_json_file: Callable[[Path, dict[str, Any]], None],
    validate_staged_run: Callable[[Path, dict[str, Any]], dict[str, Any]],
) -> dict[str, Any]:
    manifest_path = run_dir / "manifest.json"
    manifest["run_state"] = "staging"
    write_json_file(manifest_path, manifest)
    manifest["validation"] = validate_staged_run(run_dir, manifest)
    manifest["run_state"] = "complete"
    write_json_file(manifest_path, manifest)
    return manifest


def build_variant_manifest(
    final_run_dir: Path,
    variant_name: str,
    global_result: dict[str, Any],
    regional_result: dict[str, Any],
    *,
    active_global_scenario_rows: int | None = None,
) -> dict[str, Any]:
    payload = {
        "path": str((final_run_dir / variant_name).as_posix()),
        "global_rows": len(global_result["rows"]),
        "regional_rows": sum(
            len(rows)
            for rows in regional_result["regional_rows_by_region"].values()
        ),
        "reconciled_rows": len(regional_result["reconciled_rows"]),
        "aviation_rows": sum(
            len(rows)
            for rows in regional_result.get(
                "aviation_rows_by_region",
                {},
            ).values()
        ),
        "supply_rows": sum(
            len(rows)
            for rows in regional_result.get(
                "supply_rows_by_region",
                {},
            ).values()
        ),
        "city_airport_rows": sum(
            len(rows)
            for rows in regional_result.get(
                "city_airport_rows_by_market",
                {},
            ).values()
        ),
        "potential_passenger_forecast_rows": sum(
            len(rows)
            for rows in regional_result.get(
                "potential_passenger_forecast_rows_by_market",
                {},
            ).values()
        ),
        "quarterly_operations_rows": sum(
            len(rows)
            for rows in regional_result.get(
                "quarterly_operations_rows_by_market",
                {},
            ).values()
        ),
        "financial_state_rows": sum(
            len(rows)
            for rows in regional_result.get(
                "financial_state_rows_by_market",
                {},
            ).values()
        ),
        "valuation_rows": sum(
            len(rows)
            for rows in regional_result.get(
                "valuation_forecast_rows_by_market",
                {},
            ).values()
        ),
        "city_airport_downstream_skips": len(
            regional_result.get("city_airport_downstream_skips", [])
        ),
    }
    if active_global_scenario_rows is not None:
        payload["active_global_scenario_rows"] = active_global_scenario_rows
    return payload


def build_run_manifest(
    args: Any,
    seed: int,
    run_id: str,
    final_run_dir: Path,
    variants: dict[str, dict[str, Any]],
    scenario_manifest: dict[str, Any] | None,
    scenario_variant_name: str | None,
    *,
    schema_version: str,
    model_version: str,
    output_schema_version: str,
    orchestrator_version: str,
    platform_module: Any,
    branch_profiles: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": schema_version,
        "model_version": model_version,
        "output_schema_version": output_schema_version,
        "orchestrator_version": orchestrator_version,
        "python_version": platform_module.python_version(),
        "python_implementation": platform_module.python_implementation(),
        "artifact_profile": getattr(args, "artifact_profile", "full"),
        "run_id": run_id,
        "seed": seed,
        "start_year": args.start_year,
        "years": args.years,
        "feedback_iterations": args.feedback_iterations,
        "volatility_scale": args.volatility_scale,
        "initial_gdp": args.initial_gdp,
        "output_dir": str(final_run_dir.as_posix()),
        "variants": variants,
        "scenario": scenario_manifest,
        "scenario_variant": scenario_variant_name,
        "branch_scenario_profile_count": len(branch_profiles),
        "branch_scenario_profile_ids": sorted(branch_profiles),
        "published": None,
    }


def requested_publish_variant(
    args: Any,
    manifest: dict[str, Any],
) -> str | None:
    if args.publish_viewer == "none":
        return None
    if args.publish_viewer == "baseline":
        return "baseline"
    scenario_variant = str(manifest.get("scenario_variant") or "").strip()
    if not scenario_variant:
        raise ValueError(
            "--publish-viewer scenario requires --scenario-state occurred, "
            "counterfactual, or probabilistic"
        )
    return scenario_variant
