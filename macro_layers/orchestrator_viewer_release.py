from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any


def write_viewer_release_bundles(
    variant_dir: Path,
    release_dir: Path,
    release_id: str,
    *,
    copy_tree_files: Callable[[Path, Path], list[str]],
    write_city_market_viewer_lazy_assets: Callable[[Path, Path], dict[str, Any]],
    copy_file: Callable[[Path, Path], Any],
    build_global_viewer_bundle: Callable[[Path, str], str],
    build_city_market_viewer_bundle: Callable[[Path, Path, str], str],
    build_beijing_forecast_viewer_bundle: Callable[[Path, str], str],
    atomic_write_text_file: Callable[[Path, str], None],
) -> dict[str, str]:
    global_chunk_dir = variant_dir / "global_macro" / "global_viewer_chunks"
    if global_chunk_dir.is_dir():
        copy_tree_files(global_chunk_dir, release_dir / global_chunk_dir.name)

    city_market_assets = write_city_market_viewer_lazy_assets(
        variant_dir
        / "city_airport_market_demand"
        / "china_mainland",
        release_dir,
    )

    forecast_dir = (
        variant_dir
        / "city_airport_potential_passenger_forecast"
        / "china_mainland"
    )
    for chunk_dir in sorted(forecast_dir.glob("*_forecast_chunks")):
        if chunk_dir.is_dir():
            copy_tree_files(chunk_dir, release_dir / chunk_dir.name)
    for audit_index in sorted(forecast_dir.glob("*_forecast_audit_index.js")):
        copy_file(audit_index, release_dir / audit_index.name)

    bundles = {
        "global_gdp_viewer": (
            "global_gdp_viewer_bundle.js",
            build_global_viewer_bundle(variant_dir, release_id),
        ),
        "city_market_viewer": (
            "city_market_viewer_bundle.js",
            build_city_market_viewer_bundle(
                Path(city_market_assets["index"]),
                variant_dir,
                release_id,
            ),
        ),
        "beijing_potential_passenger_forecast_viewer": (
            "beijing_potential_passenger_forecast_viewer_bundle.js",
            build_beijing_forecast_viewer_bundle(variant_dir, release_id),
        ),
    }
    filenames: dict[str, str] = {}
    for viewer_id, (filename, content) in bundles.items():
        if not content.strip():
            raise ValueError(f"empty Viewer bundle for {viewer_id}")
        atomic_write_text_file(release_dir / filename, content)
        filenames[viewer_id] = filename
    # The city index is embedded in the atomic bundle so that its base URL is
    # tied to the same release. Keep only the bundle, not a duplicate index file.
    Path(city_market_assets["index"]).unlink(missing_ok=True)
    return filenames


def publish_variant_to_viewer(
    variant_dir: Path,
    viewer_output_root: Path,
    *,
    time_module: Any,
    clean_run_id: Callable[[str], str],
    write_viewer_release_bundles: Callable[[Path, Path, str], dict[str, str]],
    sha256_file: Callable[[Path], str],
    write_viewer_release_gzip_sidecars: Callable[[Path], dict[str, int]],
    replace_directory_with_retry: Callable[[Path, Path], None],
    copy_variant_to_legacy_viewer: Callable[[Path, Path], list[str]],
    manifest_version: str,
    viewer_run_metadata: Callable[[Path], dict[str, Any]],
    airport_relative: Callable[[Path], str],
    viewer_script_url: Callable[[Path], str],
    write_json_file: Callable[[Path, dict[str, Any]], None],
    atomic_write_text_file: Callable[[Path, str], None],
    remove_tree: Callable[[Path], None],
) -> dict[str, Any]:
    variant_dir = variant_dir.resolve()
    viewer_output_root = viewer_output_root.resolve()
    if not variant_dir.exists():
        raise FileNotFoundError(f"missing Viewer source variant: {variant_dir}")

    timestamp = time_module.strftime("%Y%m%d_%H%M%S")
    unique_suffix = f"{time_module.time_ns() % 1_000_000_000:09d}"
    release_id = clean_run_id(
        f"{variant_dir.parent.name}_{variant_dir.name}_{timestamp}_{unique_suffix}"
    )
    releases_root = viewer_output_root / "viewer_releases"
    staging_dir = releases_root / f".staging_{release_id}"
    release_dir = releases_root / release_id
    if staging_dir.exists() or release_dir.exists():
        raise FileExistsError(f"Viewer release already exists: {release_id}")

    releases_root.mkdir(parents=True, exist_ok=True)
    try:
        staging_dir.mkdir()
        bundle_filenames = write_viewer_release_bundles(
            variant_dir,
            staging_dir,
            release_id,
        )
        bundle_hashes = {
            viewer_id: sha256_file(staging_dir / filename)
            for viewer_id, filename in bundle_filenames.items()
        }
        gzip_summary = write_viewer_release_gzip_sidecars(staging_dir)
        replace_directory_with_retry(staging_dir, release_dir)

        # Keep the established canonical output tree for compatibility with older pages/tools.
        canonical_copied = copy_variant_to_legacy_viewer(
            variant_dir,
            viewer_output_root,
        )

        manifest = {
            "schema_version": manifest_version,
            "release_id": release_id,
            "run_id": variant_dir.parent.name,
            "variant": variant_dir.name,
            **viewer_run_metadata(variant_dir),
            "generated_at": time_module.strftime("%Y-%m-%d %H:%M:%S"),
            "source_variant": airport_relative(variant_dir),
            "release_path": airport_relative(release_dir),
            "scripts": {
                viewer_id: viewer_script_url(release_dir / filename)
                for viewer_id, filename in bundle_filenames.items()
            },
            "bundle_sha256": bundle_hashes,
            "bundle_count": len(bundle_filenames),
            "canonical_copy_count": len(canonical_copied),
            **gzip_summary,
        }
        manifest_json_path = viewer_output_root / "current_viewer_manifest.json"
        manifest_js_path = viewer_output_root / "current_viewer_manifest.js"
        write_json_file(manifest_json_path, manifest)
        compact_manifest = json.dumps(
            manifest,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        # This JS pointer is the final atomic switch used by the static Viewer pages.
        atomic_write_text_file(
            manifest_js_path,
            f"window.AIRPORT_VIEWER_MANIFEST = {compact_manifest};\n",
        )
    except Exception:
        if (
            staging_dir.exists()
            and staging_dir.parent.resolve() == releases_root.resolve()
        ):
            remove_tree(staging_dir)
        raise

    return {
        "viewer_output_root": str(viewer_output_root.as_posix()),
        "copied_files": len(canonical_copied),
        "release_id": release_id,
        "release_path": airport_relative(release_dir),
        "release_manifest_json": airport_relative(manifest_json_path),
        "release_manifest_js": airport_relative(manifest_js_path),
        "bundle_count": len(bundle_filenames),
        **gzip_summary,
    }
