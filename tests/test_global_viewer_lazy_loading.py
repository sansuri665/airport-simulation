from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT_DIR = Path(__file__).resolve().parents[1]
PAGES_DIR = ROOT_DIR / "web" / "pages"
STATIC_DIR = ROOT_DIR / "web" / "static"
MACRO_DIR = ROOT_DIR / "macro_layers"
if str(MACRO_DIR) not in sys.path:
    sys.path.insert(0, str(MACRO_DIR))

import macro_run_orchestrator_sim as orchestrator
import test_viewer_release
from schema_support import load_schema_registry, validate_named_schema


SCHEMA_REGISTRY = load_schema_registry(ROOT_DIR / "schemas")


def sample_regional_result() -> dict[str, object]:
    return {
        "regional_rows_by_region": {
            "china_mainland": [{"region_id": "china_mainland", "seed": 7, "year": 2030}],
        },
        "aviation_rows_by_region": {
            "china_mainland": [{"region_id": "china_mainland", "seed": 7, "year": 2030}],
        },
        "supply_rows_by_region": {
            "china_mainland": [{"region_id": "china_mainland", "seed": 7, "year": 2030}],
        },
    }


def read_index_script(path: Path) -> dict[str, object]:
    content = path.read_text(encoding="utf-8")
    prefix = "(() => { const index = "
    marker = "; index.baseUrl ="
    if not content.startswith(prefix) or marker not in content:
        raise AssertionError("unexpected global Viewer lazy index script")
    return json.loads(content[len(prefix) : content.index(marker)])


class GlobalViewerLazyLoadingTests(unittest.TestCase):
    def test_region_chunks_preserve_all_three_input_groups(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            global_dir = Path(temporary_dir) / "global_macro"
            result = orchestrator.write_global_viewer_lazy_assets(global_dir, sample_regional_result())
            index = read_index_script(Path(result["index"]))

            self.assertEqual(len(orchestrator.REGION_ORDER), result["regionCount"])
            validate_named_schema(index, "global-viewer-lazy-index.schema.json", SCHEMA_REGISTRY)
            china = next(region for region in index["regions"] if region["regionId"] == "china_mainland")
            raw = (global_dir / index["chunkBase"] / china["file"]).read_bytes()
            chunk = json.loads(raw)
            self.assertEqual(china["sha256"], hashlib.sha256(raw).hexdigest())
            self.assertEqual(sample_regional_result()["regional_rows_by_region"]["china_mainland"], chunk["regionalMacroRows"])
            self.assertEqual(sample_regional_result()["aviation_rows_by_region"]["china_mainland"], chunk["aviationDemandRows"])
            self.assertEqual(sample_regional_result()["supply_rows_by_region"]["china_mainland"], chunk["airCapacitySupplyRows"])
            validate_named_schema(chunk, "global-viewer-region-chunk.schema.json", SCHEMA_REGISTRY)

    def test_atomic_release_uses_index_and_copies_region_chunks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            temporary_root = Path(temporary_dir)
            variant = test_viewer_release.build_minimal_variant(temporary_root)
            orchestrator.write_global_viewer_lazy_assets(variant / "global_macro", sample_regional_result())
            viewer_root = temporary_root / "output"

            with mock.patch.object(orchestrator, "AIRPORT_DIR", temporary_root):
                result = orchestrator.publish_variant_to_viewer(variant, viewer_root)

            release_dir = viewer_root / "viewer_releases" / result["release_id"]
            bundle = (release_dir / "global_gdp_viewer_bundle.js").read_text(encoding="utf-8")
            self.assertIn("AIRPORT_GLOBAL_VIEWER_LAZY_INDEX", bundle)
            self.assertNotIn('REGIONAL_MACRO_DATASETS["china_mainland"]', bundle)
            self.assertEqual(len(orchestrator.REGION_ORDER), len(list((release_dir / "global_viewer_chunks").glob("*.json"))))
            self.assertFalse((viewer_root / "global_macro" / "global_viewer_index.js").exists())
            self.assertFalse((viewer_root / "global_macro" / "global_viewer_chunks").exists())

    def test_viewer_requires_region_loader_without_legacy_script_fallback(self) -> None:
        html = (PAGES_DIR / "global_gdp_viewer.html").read_text(encoding="utf-8")
        bootstrap_script = "/static/js/global-gdp/bootstrap.js"
        bootstrap_js = (STATIC_DIR / "js" / "global-gdp" / "bootstrap.js").read_text(encoding="utf-8")
        page_script = "/static/js/global-gdp/page.js"
        data_client_script = "/static/js/global-gdp/data-client.js"
        data_client_js = (STATIC_DIR / "js" / "global-gdp" / "data-client.js").read_text(encoding="utf-8")

        self.assertIn(f'<script src="{bootstrap_script}"></script>', html)
        self.assertIn(f'<script src="{data_client_script}"></script>', html)
        self.assertIn(f'<script src="{page_script}"></script>', html)
        self.assertNotIn("macro_run_index.js", html)
        self.assertNotIn("global_viewer_index.js", bootstrap_js)
        self.assertIn("scripts?.global_gdp_viewer", bootstrap_js)
        self.assertIn("AIRPORT_GLOBAL_VIEWER_LOAD_ERROR", bootstrap_js)
        self.assertNotIn(" onerror=", bootstrap_js)
        self.assertNotIn("legacyGlobalViewerDataScripts", html)
        self.assertNotIn("legacyGlobalViewerDataScripts", bootstrap_js)
        self.assertIn("async function ensureRegionLoaded(", data_client_js)
        self.assertIn("window.AIRPORT_GLOBAL_VIEWER_LAZY_INDEX", data_client_js)
        self.assertIn("window.REGIONAL_MACRO_DATASETS", data_client_js)
        self.assertNotIn("CSV_PATH", data_client_js)
        self.assertNotIn("regional_macro/${config.id}", data_client_js)
        self.assertNotIn("macro_runs", data_client_js)
        self.assertNotIn("loadArchivedVariantData", data_client_js)
        self.assertNotIn('cache: "no-store"', data_client_js)
        self.assertIn("没有按区域分块", data_client_js)


if __name__ == "__main__":
    unittest.main()
