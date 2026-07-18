from __future__ import annotations

import gzip
import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT_DIR = Path(__file__).resolve().parents[1]
MACRO_DIR = ROOT_DIR / "macro_layers"
if str(MACRO_DIR) not in sys.path:
    sys.path.insert(0, str(MACRO_DIR))

import macro_run_orchestrator_sim as orchestrator
import orchestrator_viewer_assets as viewer_assets

from airport_sim.server import run_cache


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


class ViewerAssetsCompatibilityTests(unittest.TestCase):
    def test_copy_surfaces_delegate_with_current_file_and_tree_callbacks(self) -> None:
        expected = ["delegated"]
        source = Path("source")
        target = Path("target")
        with mock.patch.object(viewer_assets, "copy_files", return_value=expected) as flat:
            self.assertIs(expected, orchestrator.copy_files(source, target, "*.js"))
        self.assertEqual((source, target, "*.js"), flat.call_args.args)
        self.assertIs(orchestrator.shutil.copy2, flat.call_args.kwargs["copy_file"])

        with mock.patch.object(viewer_assets, "copy_tree_files", return_value=expected) as tree:
            self.assertIs(expected, orchestrator.copy_tree_files(source, target))
        self.assertIs(orchestrator.shutil.copy2, tree.call_args.kwargs["copy_file"])

        with mock.patch.object(
            viewer_assets,
            "copy_tree_files_exact",
            return_value=expected,
        ) as exact:
            self.assertIs(expected, orchestrator.copy_tree_files_exact(source, target))
        self.assertIs(orchestrator.copy_tree_files, exact.call_args.kwargs["copy_tree_files"])

        with mock.patch.object(
            viewer_assets,
            "copy_variant_to_legacy_viewer",
            return_value=expected,
        ) as legacy:
            self.assertIs(expected, orchestrator.copy_variant_to_legacy_viewer(source, target))
        self.assertIs(orchestrator.copy_files, legacy.call_args.kwargs["copy_files"])
        self.assertIs(orchestrator.copy_tree_files_exact, legacy.call_args.kwargs["copy_tree_files_exact"])

    def test_bundle_metadata_and_url_surfaces_keep_existing_mock_points(self) -> None:
        variant = Path("run/baseline")
        with mock.patch.object(
            viewer_assets,
            "viewer_run_metadata",
            return_value={"seed": 7},
        ) as metadata:
            self.assertEqual({"seed": 7}, orchestrator.viewer_run_metadata(variant))
        self.assertEqual(orchestrator.MODEL_VERSION, metadata.call_args.kwargs["model_version"])

        with mock.patch.object(
            viewer_assets,
            "viewer_release_info_script",
            return_value="release-info",
        ) as release_info:
            self.assertEqual(
                "release-info",
                orchestrator.viewer_release_info_script("r1", variant),
            )
        self.assertIs(orchestrator.viewer_run_metadata, release_info.call_args.kwargs["viewer_run_metadata"])

        with mock.patch.object(
            viewer_assets,
            "build_global_viewer_bundle",
            return_value="global-bundle",
        ) as global_bundle:
            self.assertEqual("global-bundle", orchestrator.build_global_viewer_bundle(variant, "r1"))
        self.assertEqual(orchestrator.REGION_ORDER, global_bundle.call_args.kwargs["region_order"])
        self.assertIs(orchestrator.viewer_script_source, global_bundle.call_args.kwargs["viewer_script_source"])

        with mock.patch.object(viewer_assets, "viewer_script_url", return_value="./asset") as url:
            self.assertEqual("./asset", orchestrator.viewer_script_url(Path("asset")))
        self.assertEqual(orchestrator.AIRPORT_DIR, url.call_args.kwargs["airport_dir"])

    def test_hash_and_gzip_surfaces_keep_protocol_constants_and_callbacks(self) -> None:
        path = Path("bundle.js")
        with mock.patch.object(viewer_assets, "sha256_file", return_value="digest"):
            self.assertEqual("digest", orchestrator.sha256_file(path))

        with mock.patch.object(
            viewer_assets,
            "write_viewer_gzip_sidecar",
            return_value=(100, 10),
        ) as sidecar:
            self.assertEqual((100, 10), orchestrator.write_viewer_gzip_sidecar(path))
        self.assertIs(orchestrator.gzip, sidecar.call_args.kwargs["gzip_module"])
        self.assertIs(orchestrator.os.replace, sidecar.call_args.kwargs["replace_file"])
        self.assertEqual(orchestrator.VIEWER_GZIP_CHUNK_BYTES, sidecar.call_args.kwargs["chunk_bytes"])

        with mock.patch.object(
            viewer_assets,
            "write_viewer_release_gzip_sidecars",
            return_value={"gzip_file_count": 0, "gzip_raw_bytes": 0, "gzip_bytes": 0},
        ) as release_sidecars:
            orchestrator.write_viewer_release_gzip_sidecars(Path("release"))
        self.assertEqual(orchestrator.VIEWER_GZIP_SUFFIXES, release_sidecars.call_args.kwargs["suffixes"])
        self.assertIs(
            orchestrator.write_viewer_gzip_sidecar,
            release_sidecars.call_args.kwargs["write_viewer_gzip_sidecar"],
        )

    def test_new_asset_module_is_a_seed_cache_dependency(self) -> None:
        names = {
            path.name
            for path in run_cache.dependency_files(
                ROOT_DIR / "airport_sim" / "server",
                ROOT_DIR,
            )
        }
        self.assertIn("orchestrator_viewer_assets.py", names)


class CopyUtilityTests(unittest.TestCase):
    def test_flat_and_recursive_copy_are_sorted_and_preserve_relative_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            source = root / "source"
            write_text(source / "b.js", "b")
            write_text(source / "a.js", "a")
            write_text(source / "nested" / "c.js", "c")
            flat_target = root / "flat"
            tree_target = root / "tree"

            flat = viewer_assets.copy_files(
                source,
                flat_target,
                "*.js",
                copy_file=shutil.copy2,
            )
            tree = viewer_assets.copy_tree_files(
                source,
                tree_target,
                copy_file=shutil.copy2,
            )

        self.assertEqual(
            [(flat_target / "a.js").as_posix(), (flat_target / "b.js").as_posix()],
            flat,
        )
        self.assertEqual(
            [
                (tree_target / "a.js").as_posix(),
                (tree_target / "b.js").as_posix(),
                (tree_target / "nested" / "c.js").as_posix(),
            ],
            tree,
        )

    def test_missing_recursive_source_returns_empty_without_creating_target(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            target = root / "target"
            copied = viewer_assets.copy_tree_files(
                root / "missing",
                target,
                copy_file=mock.Mock(side_effect=AssertionError("must not copy")),
            )

        self.assertEqual([], copied)
        self.assertFalse(target.exists())

    def test_exact_tree_prunes_only_stale_files_and_preserves_expected_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            source = root / "source"
            target = root / "target"
            write_text(source / "keep.json", "new")
            write_text(source / "nested" / "keep.js", "new nested")
            write_text(target / "keep.json", "old")
            write_text(target / "nested" / "keep.js", "old nested")
            write_text(target / "stale.json", "stale")
            write_text(target / "nested" / "stale.js", "stale nested")

            copied = viewer_assets.copy_tree_files_exact(
                source,
                target,
                copy_tree_files=lambda src, dst: viewer_assets.copy_tree_files(
                    src,
                    dst,
                    copy_file=shutil.copy2,
                ),
                resolve_path=lambda path: path.resolve(),
            )

            self.assertEqual("new", (target / "keep.json").read_text(encoding="utf-8"))
            self.assertEqual("new nested", (target / "nested" / "keep.js").read_text(encoding="utf-8"))
            self.assertFalse((target / "stale.json").exists())
            self.assertFalse((target / "nested" / "stale.js").exists())
        self.assertEqual(2, len(copied))

    def test_exact_tree_refuses_to_prune_resolved_path_outside_target(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            source = root / "source"
            target = root / "target"
            source.mkdir()
            stale = target / "stale.js"
            write_text(stale, "stale")
            outside = root / "outside.js"

            def resolve(path: Path) -> Path:
                return outside if path == stale else path.absolute()

            with self.assertRaisesRegex(ValueError, "outside Viewer tree"):
                viewer_assets.copy_tree_files_exact(
                    source,
                    target,
                    copy_tree_files=lambda src, dst: [],
                    resolve_path=resolve,
                )
            self.assertTrue(stale.is_file())


class LegacyCanonicalCopyTests(unittest.TestCase):
    def test_chunks_are_copied_before_global_and_forecast_indexes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            variant = root / "variant"
            viewer = root / "viewer"
            write_text(variant / "global_macro" / "data.js", "global")
            write_text(variant / "global_macro" / "global_viewer_chunks" / "r.json", "chunk")
            write_text(variant / "global_macro" / "global_viewer_index.js", "index")

            forecast = variant / "city_airport_potential_passenger_forecast" / "china_mainland"
            write_text(forecast / "data.js", "forecast data")
            write_text(forecast / "beijing_forecast_chunks" / "report.json", "report")
            write_text(forecast / "beijing_forecast_index.js", "forecast index")
            obsolete = (
                viewer
                / "city_airport_potential_passenger_forecast"
                / "china_mainland"
                / "beijing_airport_system_potential_passenger_forecast_viewer_data.js"
            )
            write_text(obsolete, "obsolete")

            operations = variant / "city_airport_quarterly_operations" / "china_mainland"
            write_text(operations / "data.js", "operations data")
            write_text(operations / "beijing_operations_chunks" / "valuation.json", "valuation")
            write_text(operations / "beijing_operations_index.js", "operations index")
            events: list[str] = []

            def copy_file(source: Path, target: Path) -> None:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
                events.append(source.name)

            def copy_tree(source: Path, target: Path) -> list[str]:
                events.append(source.name)
                return viewer_assets.copy_tree_files(source, target, copy_file=shutil.copy2)

            def copy_exact(source: Path, target: Path) -> list[str]:
                events.append(source.name)
                return viewer_assets.copy_tree_files_exact(
                    source,
                    target,
                    copy_tree_files=lambda src, dst: viewer_assets.copy_tree_files(
                        src,
                        dst,
                        copy_file=shutil.copy2,
                    ),
                    resolve_path=lambda path: path.resolve(),
                )

            viewer_assets.copy_variant_to_legacy_viewer(
                variant,
                viewer,
                copy_file=copy_file,
                copy_files=lambda source, target, pattern="*": [],
                copy_tree_files=copy_tree,
                copy_tree_files_exact=copy_exact,
            )

            self.assertFalse(obsolete.exists())
            self.assertLess(events.index("global_viewer_chunks"), events.index("global_viewer_index.js"))
            self.assertLess(events.index("beijing_forecast_chunks"), events.index("beijing_forecast_index.js"))
            self.assertFalse(
                (
                    viewer
                    / "city_airport_potential_passenger_forecast"
                    / "china_mainland"
                    / "data.js"
                ).exists()
            )
            self.assertFalse(
                (
                    viewer
                    / "city_airport_quarterly_operations"
                    / "china_mainland"
                    / "beijing_operations_index.js"
                ).exists()
            )

    def test_only_runtime_fallbacks_and_standalone_cli_inputs_are_copied(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            variant = root / "variant"
            viewer = root / "viewer"
            fixtures = {
                "global_macro/global_macro_feedback_seed_sweep.csv": True,
                "global_macro/global_macro_feedback_viewer_data.js": True,
                "global_macro/global_macro_feedback_seed_sweep.json": False,
                "regional_macro/r1/r1_regional_macro_seed_sweep.csv": True,
                "regional_macro/r1/r1_regional_macro_viewer_data.js": False,
                "regional_macro_reconciled/regional_macro_reconciled_seed_sweep.csv": True,
                "regional_macro_reconciled/regional_macro_reconciled_viewer_data.js": True,
                "regional_macro_reconciled/regional_macro_reconciled_summary.json": False,
                "regional_aviation_demand/r1/r1_aviation_demand_seed_sweep.csv": True,
                "regional_aviation_demand/r1/r1_aviation_demand_viewer_data.js": False,
                "regional_air_capacity_supply/r1/r1_air_capacity_supply_seed_sweep.csv": True,
                "regional_air_capacity_supply/r1/r1_air_capacity_supply_viewer_data.js": False,
                "city_airport_market_demand/r1/c1_city_airport_demand_seed_sweep.csv": True,
                "city_airport_market_demand/r1/c1_city_airport_demand_viewer_data.js": False,
                "city_airport_quarterly_operations/r1/c1_quarterly_operations_seed_sweep.csv": True,
                "city_airport_quarterly_operations/r1/c1_quarterly_operations_viewer_data.js": False,
                "city_airport_financial_state/r1/c1_financial_state_seed_sweep.csv": True,
                "city_airport_financial_state/r1/c1_financial_state_viewer_data.js": False,
                "city_airport_valuation/r1/c1_valuation_forecast_seed_sweep.csv": False,
            }
            for relative in fixtures:
                write_text(variant / relative, relative)

            viewer_assets.copy_variant_to_legacy_viewer(
                variant,
                viewer,
                copy_file=shutil.copy2,
                copy_files=lambda source, target, pattern="*": viewer_assets.copy_files(
                    source,
                    target,
                    pattern,
                    copy_file=shutil.copy2,
                ),
                copy_tree_files=lambda source, target: viewer_assets.copy_tree_files(
                    source,
                    target,
                    copy_file=shutil.copy2,
                ),
                copy_tree_files_exact=lambda source, target: viewer_assets.copy_tree_files_exact(
                    source,
                    target,
                    copy_tree_files=lambda src, dst: viewer_assets.copy_tree_files(
                        src,
                        dst,
                        copy_file=shutil.copy2,
                    ),
                    resolve_path=lambda path: path.resolve(),
                ),
            )

            for relative, expected in fixtures.items():
                target_relative = Path(relative)
                if target_relative.parts[0] in {
                    "regional_macro",
                    "regional_aviation_demand",
                    "regional_air_capacity_supply",
                }:
                    target_relative = Path(target_relative.parts[0]) / target_relative.name
                self.assertEqual(expected, (viewer / target_relative).is_file(), relative)


class BundleContentTests(unittest.TestCase):
    def test_script_source_uses_default_or_normalizes_one_trailing_newline(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            path = Path(temporary_dir) / "script.js"
            missing = viewer_assets.viewer_script_source(path, "window.DEFAULT = true;\n\n")
            path.write_text("window.ACTUAL = true;\n\n", encoding="utf-8")
            actual = viewer_assets.viewer_script_source(path, "unused")

        self.assertEqual("window.DEFAULT = true;\n", missing)
        self.assertEqual("window.ACTUAL = true;\n", actual)

    def test_run_metadata_defaults_on_missing_or_invalid_manifest_and_maps_valid_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            variant = root / "run" / "baseline"
            variant.mkdir(parents=True)
            missing = viewer_assets.viewer_run_metadata(
                variant,
                model_version="model-default",
                output_schema_version="output-default",
            )
            (variant.parent / "manifest.json").write_text("invalid", encoding="utf-8")
            invalid = viewer_assets.viewer_run_metadata(
                variant,
                model_version="model-default",
                output_schema_version="output-default",
            )
            (variant.parent / "manifest.json").write_text(
                json.dumps(
                    {
                        "seed": 7,
                        "start_year": 2025,
                        "years": 60,
                        "model_version": "model-real",
                        "output_schema_version": "output-real",
                    }
                ),
                encoding="utf-8",
            )
            valid = viewer_assets.viewer_run_metadata(
                variant,
                model_version="model-default",
                output_schema_version="output-default",
            )

        self.assertEqual(missing, invalid)
        self.assertEqual("model-default", missing["model_version"])
        self.assertEqual(
            {
                "seed": 7,
                "start_year": 2025,
                "years": 60,
                "model_version": "model-real",
                "output_schema_version": "output-real",
            },
            valid,
        )

    def test_global_bundle_prefers_lazy_index_and_legacy_fallback_keeps_region_order(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            variant = Path(temporary_dir) / "variant"
            lazy = variant / "global_macro" / "global_viewer_index.js"
            write_text(lazy, "window.LAZY = true;")
            release_info = lambda release_id, path: "window.RELEASE = true;\n"
            lazy_bundle = viewer_assets.build_global_viewer_bundle(
                variant,
                "r1",
                region_order=("b", "a"),
                viewer_script_source=viewer_assets.viewer_script_source,
                viewer_release_info_script=release_info,
            )
            lazy.unlink()
            legacy_bundle = viewer_assets.build_global_viewer_bundle(
                variant,
                "r1",
                region_order=("b", "a"),
                viewer_script_source=viewer_assets.viewer_script_source,
                viewer_release_info_script=release_info,
            )

        self.assertIn("window.LAZY = true;", lazy_bundle)
        self.assertNotIn("REGIONAL_MACRO_DATASETS[\"b\"]", lazy_bundle)
        self.assertLess(
            legacy_bundle.index('REGIONAL_MACRO_DATASETS["b"]'),
            legacy_bundle.index('REGIONAL_MACRO_DATASETS["a"]'),
        )
        self.assertTrue(legacy_bundle.endswith("window.RELEASE = true;\n"))

    def test_city_and_forecast_bundles_keep_headers_release_info_and_missing_index_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            variant = root / "run" / "baseline"
            index = root / "city-index.js"
            write_text(index, "window.CITY = true;")
            release_info = lambda release_id, path: f"window.RELEASE = '{release_id}';\n"
            city = viewer_assets.build_city_market_viewer_bundle(
                index,
                variant,
                "r1",
                viewer_script_source=viewer_assets.viewer_script_source,
                viewer_release_info_script=release_info,
            )
            with self.assertRaisesRegex(FileNotFoundError, "missing Beijing forecast lazy index"):
                viewer_assets.build_beijing_forecast_viewer_bundle(
                    variant,
                    "r1",
                    viewer_script_source=viewer_assets.viewer_script_source,
                    viewer_release_info_script=release_info,
                )
            forecast_index = (
                variant
                / "city_airport_potential_passenger_forecast"
                / "china_mainland"
                / "beijing_airport_system_forecast_index.js"
            )
            write_text(forecast_index, "window.FORECAST = true;")
            forecast = viewer_assets.build_beijing_forecast_viewer_bundle(
                variant,
                "r1",
                viewer_script_source=viewer_assets.viewer_script_source,
                viewer_release_info_script=release_info,
            )

        self.assertTrue(city.startswith("/* Atomic airport Viewer release: r1 */\n"))
        self.assertIn("window.CITY = true;", city)
        self.assertIn("window.FORECAST = true;", forecast)
        self.assertTrue(forecast.endswith("window.RELEASE = 'r1';\n"))


class PathHashAndGzipTests(unittest.TestCase):
    def test_viewer_url_and_sha256_keep_relative_and_external_protocols(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            inside = root / "output" / "bundle.js"
            outside = root.parent / f"{root.name}-outside.js"
            write_text(inside, "bundle")
            write_text(outside, "outside")
            try:
                inside_url = viewer_assets.viewer_script_url(inside, airport_dir=root)
                outside_url = viewer_assets.viewer_script_url(outside, airport_dir=root)
                digest = viewer_assets.sha256_file(inside)
            finally:
                outside.unlink(missing_ok=True)

        self.assertEqual("./output/bundle.js", inside_url)
        self.assertTrue(outside_url.startswith("file:"))
        self.assertEqual(hashlib.sha256(b"bundle").hexdigest(), digest)

    def test_gzip_sidecar_is_deterministic_and_cleans_temporary_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            path = Path(temporary_dir) / "bundle.json"
            content = b'{"data":"' + b"repeat" * 1_000 + b'"}'
            path.write_bytes(content)
            first = viewer_assets.write_viewer_gzip_sidecar(
                path,
                gzip_module=gzip,
                replace_file=lambda source, target: source.replace(target),
                chunk_bytes=37,
            )
            first_bytes = Path(f"{path}.gz").read_bytes()
            second = viewer_assets.write_viewer_gzip_sidecar(
                path,
                gzip_module=gzip,
                replace_file=lambda source, target: source.replace(target),
                chunk_bytes=103,
            )
            second_bytes = Path(f"{path}.gz").read_bytes()

        self.assertEqual(first, second)
        self.assertEqual(content, gzip.decompress(first_bytes))
        self.assertEqual(first_bytes, second_bytes)
        self.assertFalse(Path(f"{path}.gz.tmp").exists())

    def test_gzip_replace_failure_removes_temp_and_keeps_existing_target(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            path = Path(temporary_dir) / "bundle.js"
            path.write_bytes(b"new content" * 100)
            target = Path(f"{path}.gz")
            target.write_bytes(b"old target")
            with self.assertRaisesRegex(OSError, "replace failed"):
                viewer_assets.write_viewer_gzip_sidecar(
                    path,
                    gzip_module=gzip,
                    replace_file=mock.Mock(side_effect=OSError("replace failed")),
                    chunk_bytes=64,
                )
            self.assertEqual(b"old target", target.read_bytes())
            self.assertFalse(Path(f"{target}.tmp").exists())

    def test_release_gzip_filters_and_sorts_candidates_before_aggregation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            release = Path(temporary_dir)
            write_text(release / "b.json", "b" * 20)
            write_text(release / "a.js", "a" * 20)
            write_text(release / "small.js", "s")
            write_text(release / "ignored.txt", "x" * 20)
            seen: list[str] = []

            summary = viewer_assets.write_viewer_release_gzip_sidecars(
                release,
                suffixes=frozenset({".js", ".json"}),
                min_bytes=10,
                write_viewer_gzip_sidecar=lambda path: seen.append(path.name) or (20, 5),
            )

        self.assertEqual(["a.js", "b.json"], seen)
        self.assertEqual(
            {"gzip_file_count": 2, "gzip_raw_bytes": 40, "gzip_bytes": 10},
            summary,
        )


if __name__ == "__main__":
    unittest.main()
