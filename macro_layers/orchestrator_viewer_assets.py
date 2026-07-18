from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any


GLOBAL_CANONICAL_FILES = (
    "global_macro_feedback_seed_sweep.csv",
    "global_macro_feedback_viewer_data.js",
)


def copy_files(
    source_dir: Path,
    target_dir: Path,
    pattern: str = "*",
    *,
    copy_file: Callable[[Path, Path], Any],
) -> list[str]:
    target_dir.mkdir(parents=True, exist_ok=True)
    copied = []
    for source in sorted(source_dir.glob(pattern)):
        if not source.is_file():
            continue
        target = target_dir / source.name
        copy_file(source, target)
        copied.append(str(target.as_posix()))
    return copied


def copy_tree_files(
    source_dir: Path,
    target_dir: Path,
    *,
    copy_file: Callable[[Path, Path], Any],
) -> list[str]:
    copied: list[str] = []
    if not source_dir.is_dir():
        return copied
    for source in sorted(source_dir.rglob("*")):
        if not source.is_file():
            continue
        relative = source.relative_to(source_dir)
        target = target_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        copy_file(source, target)
        copied.append(str(target.as_posix()))
    return copied


def copy_tree_files_exact(
    source_dir: Path,
    target_dir: Path,
    *,
    copy_tree_files: Callable[[Path, Path], list[str]],
    resolve_path: Callable[[Path], Path],
) -> list[str]:
    """Copy a generated tree and remove files absent from the new source tree."""

    expected = {
        source.relative_to(source_dir)
        for source in source_dir.rglob("*")
        if source.is_file()
    }
    copied = copy_tree_files(source_dir, target_dir)
    if not target_dir.is_dir():
        return copied
    target_root = resolve_path(target_dir)
    for target in sorted(target_dir.rglob("*"), reverse=True):
        if not target.is_file() or target.relative_to(target_dir) in expected:
            continue
        resolved = resolve_path(target)
        if target_root not in resolved.parents:
            raise ValueError(f"refusing to prune file outside Viewer tree: {target}")
        target.unlink()
    return copied


def copy_variant_to_legacy_viewer(
    variant_dir: Path,
    viewer_output_root: Path,
    *,
    copy_file: Callable[[Path, Path], Any],
    copy_files: Callable[..., list[str]],
    copy_tree_files: Callable[[Path, Path], list[str]],
    copy_tree_files_exact: Callable[[Path, Path], list[str]],
) -> list[str]:
    copied: list[str] = []
    global_source = variant_dir / "global_macro"
    global_target = viewer_output_root / "global_macro"
    global_index = global_source / "global_viewer_index.js"
    for name in GLOBAL_CANONICAL_FILES:
        source = global_source / name
        if source.is_file():
            target = global_target / source.name
            target.parent.mkdir(parents=True, exist_ok=True)
            copy_file(source, target)
            copied.append(str(target.as_posix()))
    global_chunks = global_source / "global_viewer_chunks"
    if global_chunks.is_dir():
        copied.extend(
            copy_tree_files(global_chunks, global_target / global_chunks.name)
        )
    # The index is the compatibility pointer and must become visible after its chunks.
    if global_index.is_file():
        target = global_target / global_index.name
        target.parent.mkdir(parents=True, exist_ok=True)
        copy_file(global_index, target)
        copied.append(str(target.as_posix()))
    reconciled_source = variant_dir / "regional_macro_reconciled"
    reconciled_target = viewer_output_root / "regional_macro_reconciled"
    copied.extend(
        copy_files(
            reconciled_source,
            reconciled_target,
            "regional_macro_reconciled_seed_sweep.csv",
        )
    )
    copied.extend(
        copy_files(
            reconciled_source,
            reconciled_target,
            "regional_macro_reconciled_viewer_data.js",
        )
    )

    regional_target = viewer_output_root / "regional_macro"
    for region_dir in sorted((variant_dir / "regional_macro").glob("*")):
        if region_dir.is_dir():
            copied.extend(
                copy_files(
                    region_dir,
                    regional_target,
                    "*_regional_macro_seed_sweep.csv",
                )
            )

    aviation_target = viewer_output_root / "regional_aviation_demand"
    aviation_source = variant_dir / "regional_aviation_demand"
    if aviation_source.exists():
        for region_dir in sorted(aviation_source.glob("*")):
            if region_dir.is_dir():
                copied.extend(
                    copy_files(
                        region_dir,
                        aviation_target,
                        "*_aviation_demand_seed_sweep.csv",
                    )
                )

    supply_target = viewer_output_root / "regional_air_capacity_supply"
    supply_source = variant_dir / "regional_air_capacity_supply"
    if supply_source.exists():
        for region_dir in sorted(supply_source.glob("*")):
            if region_dir.is_dir():
                copied.extend(
                    copy_files(
                        region_dir,
                        supply_target,
                        "*_air_capacity_supply_seed_sweep.csv",
                    )
                )

    city_airport_target = viewer_output_root / "city_airport_market_demand"
    city_airport_source = variant_dir / "city_airport_market_demand"
    if city_airport_source.exists():
        for region_dir in sorted(city_airport_source.glob("*")):
            if region_dir.is_dir():
                copied.extend(
                    copy_files(
                        region_dir,
                        city_airport_target / region_dir.name,
                        "*_city_airport_demand_seed_sweep.csv",
                    )
                )

    potential_forecast_target = (
        viewer_output_root / "city_airport_potential_passenger_forecast"
    )
    potential_forecast_source = (
        variant_dir / "city_airport_potential_passenger_forecast"
    )
    if potential_forecast_source.exists():
        for region_dir in sorted(potential_forecast_source.glob("*")):
            if region_dir.is_dir():
                target_region_dir = potential_forecast_target / region_dir.name
                obsolete_full_js = (
                    target_region_dir
                    / "beijing_airport_system_potential_passenger_forecast_viewer_data.js"
                )
                if obsolete_full_js.is_file():
                    obsolete_full_js.unlink()
                index_files = sorted(region_dir.glob("*_forecast_index.js"))
                for source in sorted(region_dir.glob("*")):
                    if source.is_dir() and source.name.endswith(
                        "_forecast_chunks"
                    ):
                        copied.extend(
                            copy_tree_files_exact(
                                source,
                                target_region_dir / source.name,
                            )
                        )
                # The lightweight index is the compatibility pointer and is copied last.
                for source in index_files:
                    target = target_region_dir / source.name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    copy_file(source, target)
                    copied.append(str(target.as_posix()))

    quarterly_operations_target = (
        viewer_output_root / "city_airport_quarterly_operations"
    )
    quarterly_operations_source = (
        variant_dir / "city_airport_quarterly_operations"
    )
    if quarterly_operations_source.exists():
        for region_dir in sorted(quarterly_operations_source.glob("*")):
            if region_dir.is_dir():
                target_region_dir = quarterly_operations_target / region_dir.name
                copied.extend(
                    copy_files(
                        region_dir,
                        target_region_dir,
                        "*_quarterly_operations_seed_sweep.csv",
                    )
                )

    financial_state_target = viewer_output_root / "city_airport_financial_state"
    financial_state_source = variant_dir / "city_airport_financial_state"
    if financial_state_source.exists():
        for region_dir in sorted(financial_state_source.glob("*")):
            if region_dir.is_dir():
                copied.extend(
                    copy_files(
                        region_dir,
                        financial_state_target / region_dir.name,
                        "*_financial_state_seed_sweep.csv",
                    )
                )

    return copied


def viewer_script_source(path: Path, default_script: str) -> str:
    if not path.exists():
        return default_script.rstrip() + "\n"
    return path.read_text(encoding="utf-8").rstrip() + "\n"


def viewer_run_metadata(
    variant_dir: Path,
    *,
    model_version: str,
    output_schema_version: str,
) -> dict[str, Any]:
    run_manifest_path = variant_dir.parent / "manifest.json"
    run_manifest: dict[str, Any] = {}
    if run_manifest_path.is_file():
        try:
            loaded = json.loads(run_manifest_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                run_manifest = loaded
        except (OSError, ValueError, json.JSONDecodeError):
            run_manifest = {}
    return {
        "seed": run_manifest.get("seed"),
        "start_year": run_manifest.get("start_year"),
        "years": run_manifest.get("years"),
        "model_version": str(
            run_manifest.get("model_version") or model_version
        ),
        "output_schema_version": str(
            run_manifest.get("output_schema_version") or output_schema_version
        ),
    }


def viewer_release_info_script(
    release_id: str,
    variant_dir: Path,
    *,
    manifest_version: str,
    viewer_run_metadata: Callable[[Path], dict[str, Any]],
) -> str:
    payload = json.dumps(
        {
            "schema_version": manifest_version,
            "release_id": release_id,
            "run_id": variant_dir.parent.name,
            "variant": variant_dir.name,
            **viewer_run_metadata(variant_dir),
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return f"window.AIRPORT_VIEWER_RELEASE_INFO = {payload};\n"


def build_global_viewer_bundle(
    variant_dir: Path,
    release_id: str,
    *,
    region_order: tuple[str, ...] | list[str],
    viewer_script_source: Callable[[Path, str], str],
    viewer_release_info_script: Callable[[str, Path], str],
) -> str:
    lazy_index = variant_dir / "global_macro" / "global_viewer_index.js"
    if lazy_index.exists():
        return "".join(
            [
                f"/* Atomic airport Viewer release: {release_id} */\n",
                viewer_script_source(
                    variant_dir
                    / "global_macro"
                    / "global_macro_feedback_viewer_data.js",
                    "window.GLOBAL_MACRO_FEEDBACK_DATA = [];",
                ),
                viewer_script_source(
                    variant_dir
                    / "regional_macro_reconciled"
                    / "regional_macro_reconciled_viewer_data.js",
                    "window.REGIONAL_MACRO_RECONCILED_DATA = [];\n"
                    "window.REGIONAL_MACRO_RECONCILIATION_DATA = [];",
                ),
                viewer_script_source(
                    lazy_index,
                    "window.AIRPORT_GLOBAL_VIEWER_LAZY_INDEX = null;",
                ),
                viewer_release_info_script(release_id, variant_dir),
            ]
        )

    parts = [
        f"/* Atomic airport Viewer release: {release_id} */\n",
        viewer_script_source(
            variant_dir
            / "global_macro"
            / "global_macro_feedback_viewer_data.js",
            "window.GLOBAL_MACRO_FEEDBACK_DATA = [];",
        ),
        "window.REGIONAL_MACRO_DATASETS = {};\n",
    ]
    for region_id in region_order:
        parts.append("window.REGIONAL_MACRO_DATA = [];\n")
        parts.append(
            viewer_script_source(
                variant_dir
                / "regional_macro"
                / region_id
                / f"{region_id}_regional_macro_viewer_data.js",
                "window.REGIONAL_MACRO_DATA = [];",
            )
        )
        parts.append(
            f"window.REGIONAL_MACRO_DATASETS[{json.dumps(region_id)}] = "
            "window.REGIONAL_MACRO_DATA || [];\n"
        )

    parts.append(
        viewer_script_source(
            variant_dir
            / "regional_macro_reconciled"
            / "regional_macro_reconciled_viewer_data.js",
            "window.REGIONAL_MACRO_RECONCILED_DATA = [];\n"
            "window.REGIONAL_MACRO_RECONCILIATION_DATA = [];",
        )
    )
    parts.append("window.REGIONAL_AVIATION_DEMAND_DATASETS = {};\n")
    for region_id in region_order:
        parts.append("window.REGIONAL_AVIATION_DEMAND_DATA = [];\n")
        parts.append(
            viewer_script_source(
                variant_dir
                / "regional_aviation_demand"
                / region_id
                / f"{region_id}_aviation_demand_viewer_data.js",
                "window.REGIONAL_AVIATION_DEMAND_DATA = [];",
            )
        )
        parts.append(
            "window.REGIONAL_AVIATION_DEMAND_DATASETS"
            f"[{json.dumps(region_id)}] = "
            "window.REGIONAL_AVIATION_DEMAND_DATA || [];\n"
        )

    parts.append("window.REGIONAL_AIR_CAPACITY_SUPPLY_DATASETS = {};\n")
    for region_id in region_order:
        parts.append("window.REGIONAL_AIR_CAPACITY_SUPPLY_DATA = [];\n")
        parts.append(
            viewer_script_source(
                variant_dir
                / "regional_air_capacity_supply"
                / region_id
                / f"{region_id}_air_capacity_supply_viewer_data.js",
                "window.REGIONAL_AIR_CAPACITY_SUPPLY_DATA = [];",
            )
        )
        parts.append(
            "window.REGIONAL_AIR_CAPACITY_SUPPLY_DATASETS"
            f"[{json.dumps(region_id)}] = "
            "window.REGIONAL_AIR_CAPACITY_SUPPLY_DATA || [];\n"
        )
    parts.append(viewer_release_info_script(release_id, variant_dir))
    return "".join(parts)


def build_city_market_viewer_bundle(
    index_path: Path,
    variant_dir: Path,
    release_id: str,
    *,
    viewer_script_source: Callable[[Path, str], str],
    viewer_release_info_script: Callable[[str, Path], str],
) -> str:
    return "".join(
        [
            f"/* Atomic airport Viewer release: {release_id} */\n",
            viewer_script_source(
                index_path,
                "window.AIRPORT_CITY_MARKET_VIEWER_INDEX = null;",
            ),
            viewer_release_info_script(release_id, variant_dir),
        ]
    )


def build_beijing_forecast_viewer_bundle(
    variant_dir: Path,
    release_id: str,
    *,
    viewer_script_source: Callable[[Path, str], str],
    viewer_release_info_script: Callable[[str, Path], str],
) -> str:
    forecast_dir = (
        variant_dir
        / "city_airport_potential_passenger_forecast"
        / "china_mainland"
    )
    lazy_index = forecast_dir / "beijing_airport_system_forecast_index.js"
    if not lazy_index.is_file():
        raise FileNotFoundError(
            f"missing Beijing forecast lazy index: {lazy_index}"
        )
    data_script = viewer_script_source(
        lazy_index,
        "window.AIRPORT_FORECAST_LAZY_INDEX = null;",
    )
    return "".join(
        [
            f"/* Atomic airport Viewer release: {release_id} */\n",
            data_script,
            viewer_release_info_script(release_id, variant_dir),
        ]
    )


def viewer_script_url(path: Path, *, airport_dir: Path) -> str:
    try:
        relative = path.resolve().relative_to(airport_dir.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_uri()
    return f"./{relative}"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_viewer_gzip_sidecar(
    path: Path,
    *,
    gzip_module: Any,
    replace_file: Callable[[Path, Path], Any],
    chunk_bytes: int,
) -> tuple[int, int]:
    target = Path(f"{path}.gz")
    temporary = Path(f"{target}.tmp")
    try:
        with path.open("rb") as source, temporary.open("wb") as raw_target:
            with gzip_module.GzipFile(
                filename="",
                mode="wb",
                fileobj=raw_target,
                compresslevel=9,
                mtime=0,
            ) as compressed_target:
                while chunk := source.read(chunk_bytes):
                    compressed_target.write(chunk)
        replace_file(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
    return path.stat().st_size, target.stat().st_size


def write_viewer_release_gzip_sidecars(
    release_dir: Path,
    *,
    suffixes: frozenset[str],
    min_bytes: int,
    write_viewer_gzip_sidecar: Callable[[Path], tuple[int, int]],
) -> dict[str, int]:
    file_count = 0
    raw_bytes = 0
    gzip_bytes = 0
    candidates = sorted(
        path
        for path in release_dir.rglob("*")
        if path.is_file()
        and path.suffix.lower() in suffixes
        and path.stat().st_size >= min_bytes
    )
    for path in candidates:
        raw_size, gzip_size = write_viewer_gzip_sidecar(path)
        file_count += 1
        raw_bytes += raw_size
        gzip_bytes += gzip_size
    return {
        "gzip_file_count": file_count,
        "gzip_raw_bytes": raw_bytes,
        "gzip_bytes": gzip_bytes,
    }
