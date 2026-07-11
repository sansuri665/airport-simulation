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
MARKET_ID = "beijing_airport_system"


def read_index_script(path: Path) -> dict[str, object]:
    content = path.read_text(encoding="utf-8")
    prefix = "(() => { const index = "
    marker = "; index.baseUrl ="
    if not content.startswith(prefix) or marker not in content:
        raise AssertionError("unexpected operations Viewer lazy index script")
    return json.loads(content[len(prefix) : content.index(marker)])


class OperationsViewerLazyLoadingTests(unittest.TestCase):
    def test_valuation_chunk_preserves_rows_and_core_counts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            output_dir = Path(temporary_dir)
            quarterly = [{"seed": 7, "year": 2030, "quarter": "Q1"}]
            financial = [{"seed": 7, "year": 2030, "quarter": "Q1"}]
            valuation = [{"seed": 7, "as_of_year": 2030, "as_of_quarter": "Q4"}]
            result = orchestrator.write_operations_viewer_lazy_assets(
                output_dir, MARKET_ID, quarterly, financial, valuation
            )
            index = read_index_script(Path(result["index"]))
            validate_named_schema(index, "operations-viewer-lazy-index.schema.json", SCHEMA_REGISTRY)
            self.assertEqual(1, index["core"]["quarterlyOperationsRowCount"])
            self.assertEqual(1, index["core"]["financialStateRowCount"])

            dataset = index["datasets"][0]
            raw = (output_dir / index["chunkBase"] / dataset["file"]).read_bytes()
            chunk = json.loads(raw)
            self.assertEqual(dataset["sha256"], hashlib.sha256(raw).hexdigest())
            self.assertEqual(valuation, chunk["rows"])
            validate_named_schema(chunk, "operations-viewer-chunk.schema.json", SCHEMA_REGISTRY)

    def test_atomic_release_defers_valuation_and_copies_chunk(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            temporary_root = Path(temporary_dir)
            variant = test_viewer_release.build_minimal_variant(temporary_root)
            operations_dir = variant / "city_airport_quarterly_operations" / "china_mainland"
            orchestrator.write_operations_viewer_lazy_assets(
                operations_dir,
                MARKET_ID,
                [{"seed": 7}],
                [{"seed": 7}],
                [{"seed": 7, "as_of_year": 2030}],
            )
            viewer_root = temporary_root / "output"

            with mock.patch.object(orchestrator, "AIRPORT_DIR", temporary_root):
                result = orchestrator.publish_variant_to_viewer(variant, viewer_root)

            release_dir = viewer_root / "viewer_releases" / result["release_id"]
            bundle = (release_dir / "beijing_airport_operations_viewer_bundle.js").read_text(encoding="utf-8")
            self.assertIn("AIRPORT_OPERATIONS_VIEWER_LAZY_INDEX", bundle)
            self.assertNotIn("CITY_AIRPORT_VALUATION_FORECAST_DATA", bundle)
            chunk_name = f"{MARKET_ID}_operations_chunks"
            self.assertTrue((release_dir / chunk_name / "d_valuation.json").is_file())
            canonical_dir = viewer_root / "city_airport_quarterly_operations" / "china_mainland"
            self.assertTrue((canonical_dir / f"{MARKET_ID}_operations_index.js").is_file())
            self.assertTrue((canonical_dir / chunk_name / "d_valuation.json").is_file())

    def test_viewer_loads_valuation_on_demand_with_legacy_fallback(self) -> None:
        html = (PAGES_DIR / "beijing_airport_operations_viewer.html").read_text(encoding="utf-8")
        bootstrap_script = "/static/js/beijing-operations/bootstrap.js"
        bootstrap_js = (STATIC_DIR / "js" / "beijing-operations" / "bootstrap.js").read_text(encoding="utf-8")
        page_script = "/static/js/beijing-operations/page.js"
        data_client_script = "/static/js/beijing-operations/data-client.js"
        data_client_js = (STATIC_DIR / "js" / "beijing-operations" / "data-client.js").read_text(encoding="utf-8")

        self.assertIn(f'<script src="{bootstrap_script}"></script>', html)
        self.assertIn(f'<script src="{data_client_script}"></script>', html)
        self.assertIn(f'<script src="{page_script}"></script>', html)
        self.assertIn("AIRPORT_OPERATIONS_VIEWER_LAZY_INDEX", bootstrap_js)
        self.assertIn("beijing_airport_system_operations_index.js", bootstrap_js)
        self.assertIn("legacyBeijingOperationsDataScripts", html)
        self.assertIn("async function ensureValuationLoaded(", data_client_js)
        self.assertIn("window.AIRPORT_OPERATIONS_VIEWER_LAZY_INDEX", data_client_js)
        self.assertIn("window.CITY_AIRPORT_VALUATION_FORECAST_DATA", data_client_js)


if __name__ == "__main__":
    unittest.main()
