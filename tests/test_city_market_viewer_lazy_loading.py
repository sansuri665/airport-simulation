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
try:
    from . import test_viewer_release
    from .schema_support import load_schema_registry, validate_named_schema
except ImportError:
    import test_viewer_release
    from schema_support import load_schema_registry, validate_named_schema


SCHEMA_REGISTRY = load_schema_registry(ROOT_DIR / "schemas")
MARKET_ID = "beijing_airport_system"


def read_index_script(path: Path) -> dict[str, object]:
    content = path.read_text(encoding="utf-8")
    prefix = "(() => { const index = "
    marker = "; index.baseUrl ="
    if not content.startswith(prefix) or marker not in content:
        raise AssertionError("unexpected city market Viewer lazy index script")
    return json.loads(content[len(prefix) : content.index(marker)])


class CityMarketViewerLazyLoadingTests(unittest.TestCase):
    def test_city_chunk_contains_demand_and_airline_supply_without_airport_operations(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            market_dir = root / "markets"
            test_viewer_release.write_city_market_csv(
                market_dir / f"{MARKET_ID}_city_airport_demand_seed_sweep.csv"
            )
            result = orchestrator.write_city_market_viewer_lazy_assets(market_dir, root / "release")
            index = read_index_script(Path(result["index"]))
            validate_named_schema(index, "city-market-viewer-lazy-index.schema.json", SCHEMA_REGISTRY)
            self.assertEqual(1, index["cityCount"])
            self.assertNotIn("aggregate", index)

            city_meta = index["cities"][0]
            raw = (Path(result["chunkDir"]) / city_meta["file"]).read_bytes()
            chunk = json.loads(raw)
            validate_named_schema(chunk, "city-market-viewer-chunk.schema.json", SCHEMA_REGISTRY)
            self.assertEqual(city_meta["sha256"], hashlib.sha256(raw).hexdigest())
            final = chunk["city"]["points"][-1]
            self.assertEqual(110.0, final["potential"])
            self.assertEqual(108.0, final["airlineSupply"])
            self.assertEqual(108.0, final["serviceable"])
            for field in (
                "served", "unmet", "maxCapacity", "designCapacity",
                "airportCapacityGap", "bindingBottleneck",
            ):
                self.assertNotIn(field, final)
                self.assertNotIn(field, city_meta["rankingPoints"][-1])
            self.assertEqual(
                {"business", "leisure", "vfr", "long_haul", "transfer"},
                set(final["components"]),
            )
            self.assertTrue(
                all("served" not in component for component in final["components"].values())
            )

    def test_atomic_release_publishes_city_index_and_chunks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            temporary_root = Path(temporary_dir)
            variant = test_viewer_release.build_minimal_variant(temporary_root)
            viewer_root = temporary_root / "output"
            with mock.patch.object(orchestrator, "AIRPORT_DIR", temporary_root):
                result = orchestrator.publish_variant_to_viewer(variant, viewer_root)

            release_dir = viewer_root / "viewer_releases" / result["release_id"]
            bundle = (release_dir / "city_market_viewer_bundle.js").read_text(encoding="utf-8")
            self.assertIn("AIRPORT_CITY_MARKET_VIEWER_INDEX", bundle)
            self.assertNotIn("CITY_AIRPORT_QUARTERLY_OPERATIONS_DATA", bundle)
            self.assertTrue(
                (release_dir / "city_market_viewer_chunks" / f"c_{MARKET_ID}.json").is_file()
            )

    def test_viewer_loads_only_selected_city_without_legacy_fallback(self) -> None:
        html = (PAGES_DIR / "city_market_viewer.html").read_text(encoding="utf-8")
        bootstrap_js = (STATIC_DIR / "js" / "city-markets" / "bootstrap.js").read_text(encoding="utf-8")
        data_client_js = (STATIC_DIR / "js" / "city-markets" / "data-client.js").read_text(encoding="utf-8")

        self.assertIn('/static/js/city-markets/bootstrap.js', html)
        self.assertIn('/static/js/city-markets/data-client.js', html)
        self.assertIn('/static/js/city-markets/page.js', html)
        self.assertIn("scripts?.city_market_viewer", bootstrap_js)
        self.assertNotIn("legacy", html.lower())
        self.assertIn("async function loadCity(", data_client_js)
        self.assertIn("window.AIRPORT_CITY_MARKET_VIEWER_INDEX", data_client_js)
        self.assertNotIn('cache: "no-store"', data_client_js)
        self.assertNotIn("机场实际承接", html)
        self.assertNotIn("机场最大容量", html)
        self.assertNotIn("机场容量", html)
        self.assertEqual(6, html.count("data-market-scope="))
        self.assertNotIn("五类客群需求与航司供给", html)


if __name__ == "__main__":
    unittest.main()
