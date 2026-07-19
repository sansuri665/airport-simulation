from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from airport_sim.server import api_contract, routes
from airport_sim.server import app as local_ui


class ServerRouteContractTests(unittest.TestCase):
    def test_app_reexports_route_and_api_contract_boundaries(self) -> None:
        self.assertIs(local_ui.SeedExplorerHandler, routes.SeedExplorerHandler)
        self.assertIs(local_ui.VIEWER_ROUTES, routes.VIEWER_ROUTES)
        self.assertIs(local_ui.VIEWER_REDIRECTS, routes.VIEWER_REDIRECTS)
        self.assertIs(local_ui.SCHEMA_FILES, api_contract.SCHEMA_FILES)

    def test_public_route_inventory_is_explicit_and_stable(self) -> None:
        actual = {(entry.method, entry.path) for entry in routes.route_contract()}
        expected = {
            ("GET", "/"),
            ("GET", "/seed-explorer"),
            ("GET", "/global-gdp"),
            ("GET", "/city-markets"),
            ("GET", "/beijing-forecast"),
            ("GET", "/seed-explorer/"),
            ("GET", "/global-gdp/"),
            ("GET", "/city-markets/"),
            ("GET", "/beijing-forecast/"),
            ("GET", "/output/<path>"),
            ("GET", "/schemas/<name>.schema.json"),
            ("GET", "/static/<path>"),
            ("GET", "/api/health"),
            ("GET", "/api/workspace-status"),
            ("GET", "/api/seed-workspace"),
            ("GET", "/api/city-market-viewer/index"),
            ("GET", "/api/city-market-viewer/chunk"),
            ("GET", "/api/global-viewer/index"),
            ("GET", "/api/global-viewer/region"),
            ("GET", "/api/forecast-viewer/index"),
            ("GET", "/api/forecast-viewer/report"),
            ("GET", "/api/random-seed"),
            ("GET", "/api/forecast-candidate-catalog"),
            ("GET", "/api/task-status"),
            ("GET", "/api/jobs/<jobId>"),
            ("GET", "/api/schema"),
            ("GET", "/api/cached-runs"),
            ("POST", "/api/run"),
            ("POST", "/api/run-job"),
            ("POST", "/api/seed-workspace"),
            ("POST", "/api/beijing-operations"),
            ("POST", "/api/player-simulation"),
            ("POST", "/api/forecast-candidate"),
            ("POST", "/api/sim-save"),
        }

        self.assertEqual(expected, actual)
        self.assertTrue(
            all(
                entry.cache_policy == "no-store"
                for entry in routes.route_contract()
                if entry.response_type in {"json", "redirect"}
            )
        )

    def test_schema_catalog_builder_preserves_endpoint_contract(self) -> None:
        self.assertEqual(local_ui.api_schema_catalog(), api_contract.schema_catalog())
        self.assertEqual(
            "/schemas/player-simulation-response.schema.json",
            api_contract.ENDPOINT_SCHEMAS["POST /api/player-simulation"],
        )

    def test_generic_tree_resolver_rejects_escape_and_unknown_suffix(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            temporary_root = Path(temporary_dir)
            root = temporary_root / "root"
            asset = root / "nested" / "asset.js"
            asset.parent.mkdir(parents=True)
            asset.write_text("window.TEST = true;\n", encoding="utf-8")
            outside = temporary_root / "outside.txt"
            outside.write_text("outside\n", encoding="utf-8")

            self.assertEqual(
                asset.resolve(),
                routes.safe_tree_file(
                    "/assets/nested/asset.js",
                    prefix="/assets/",
                    root=root,
                    allowed_suffixes={".js"},
                ),
            )
            self.assertIsNone(
                routes.safe_tree_file(
                    "/assets/%2e%2e/outside.txt",
                    prefix="/assets/",
                    root=root,
                    allowed_suffixes={".txt"},
                )
            )
            self.assertIsNone(
                routes.safe_tree_file(
                    "/assets/nested/asset.js",
                    prefix="/assets/",
                    root=root,
                    allowed_suffixes={".json"},
                )
            )
            self.assertFalse(outside.is_relative_to(root))


if __name__ == "__main__":
    unittest.main()
