from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
PAGES_DIR = ROOT_DIR / "web" / "pages"
STATIC_DIR = ROOT_DIR / "web" / "static"
VIEWERS = (
    PAGES_DIR / "airport_home.html",
    PAGES_DIR / "global_gdp_viewer.html",
    PAGES_DIR / "beijing_airport_operations_viewer.html",
    PAGES_DIR / "beijing_potential_passenger_forecast_viewer.html",
    PAGES_DIR / "seed_explorer_viewer.html",
)
VIEWER_MANIFEST_KEYS = {
    PAGES_DIR / "global_gdp_viewer.html": "global_gdp_viewer",
    PAGES_DIR / "beijing_airport_operations_viewer.html": "beijing_airport_operations_viewer",
    PAGES_DIR / "beijing_potential_passenger_forecast_viewer.html": "beijing_potential_passenger_forecast_viewer",
}
VIEWER_BOOTSTRAP_SCRIPTS = {
    PAGES_DIR / "global_gdp_viewer.html": STATIC_DIR / "js" / "global-gdp" / "bootstrap.js",
    PAGES_DIR / "beijing_airport_operations_viewer.html": (
        STATIC_DIR / "js" / "beijing-operations" / "bootstrap.js"
    ),
    PAGES_DIR / "beijing_potential_passenger_forecast_viewer.html": (
        STATIC_DIR / "js" / "beijing-forecast" / "bootstrap.js"
    ),
}
VIEWER_MAIN_SCRIPTS = {
    PAGES_DIR / "airport_home.html": "/static/js/home/page.js",
    PAGES_DIR / "global_gdp_viewer.html": "/static/js/global-gdp/page.js",
    PAGES_DIR / "beijing_airport_operations_viewer.html": "/static/js/beijing-operations/page.js",
    PAGES_DIR / "beijing_potential_passenger_forecast_viewer.html": "/static/js/beijing-forecast/page.js",
    PAGES_DIR / "seed_explorer_viewer.html": (
        "/static/js/seed-explorer/page.js"
    ),
}
VIEWER_STATE_SCRIPTS = {
    PAGES_DIR / "global_gdp_viewer.html": "/static/js/global-gdp/state.js",
    PAGES_DIR / "beijing_airport_operations_viewer.html": "/static/js/beijing-operations/state.js",
    PAGES_DIR / "beijing_potential_passenger_forecast_viewer.html": "/static/js/beijing-forecast/state.js",
    PAGES_DIR / "seed_explorer_viewer.html": (
        "/static/js/seed-explorer/state.js"
    ),
}
SCRIPT_SOURCE_PATTERN = re.compile(r'<script\s+[^>]*src=["\']([^"\']+)["\']', re.IGNORECASE)
STYLESHEET_SOURCE_PATTERN = re.compile(
    r'<link\s+[^>]*rel=["\']stylesheet["\'][^>]*href=["\']([^"\']+)["\']',
    re.IGNORECASE,
)


def local_resource_path(viewer: Path, source: str) -> Path:
    """Map the public HTTP resource URL to its workspace file."""

    clean_source = source.split("?", 1)[0].split("#", 1)[0]
    if clean_source.startswith("/static/"):
        return STATIC_DIR / clean_source.removeprefix("/static/")
    if clean_source.startswith("/output/"):
        return ROOT_DIR / "output" / clean_source.removeprefix("/output/")
    if clean_source.startswith("./output/"):
        return ROOT_DIR / clean_source.removeprefix("./")
    return (viewer.parent / clean_source).resolve()


class ViewerResourceSmokeTests(unittest.TestCase):
    def test_viewers_and_local_script_dependencies_exist(self) -> None:
        missing: list[str] = []
        for viewer in VIEWERS:
            if not viewer.exists():
                missing.append(str(viewer.relative_to(ROOT_DIR)))
                continue
            html = viewer.read_text(encoding="utf-8")
            sources = SCRIPT_SOURCE_PATTERN.findall(html) + STYLESHEET_SOURCE_PATTERN.findall(html)
            for source in sources:
                if "JSON.stringify" in source or "+" in source:
                    continue
                if source.startswith(("http://", "https://", "//")):
                    continue
                dependency = local_resource_path(viewer, source)
                if not dependency.exists():
                    missing.append(str(dependency.relative_to(ROOT_DIR)))

        self.assertEqual([], missing, f"Missing Viewer resources: {missing}")

    def test_viewer_css_is_externalized(self) -> None:
        for viewer in VIEWERS:
            html = viewer.read_text(encoding="utf-8")
            self.assertNotIn("<style", html.lower(), viewer.name)
            self.assertTrue(STYLESHEET_SOURCE_PATTERN.findall(html), viewer.name)

    def test_viewer_main_scripts_are_externalized(self) -> None:
        for viewer, expected_source in VIEWER_MAIN_SCRIPTS.items():
            html = viewer.read_text(encoding="utf-8")
            self.assertIn(expected_source, SCRIPT_SOURCE_PATTERN.findall(html), viewer.name)

    def test_viewer_state_is_loaded_before_main_script(self) -> None:
        for viewer, state_source in VIEWER_STATE_SCRIPTS.items():
            sources = SCRIPT_SOURCE_PATTERN.findall(viewer.read_text(encoding="utf-8"))
            main_source = VIEWER_MAIN_SCRIPTS[viewer]
            self.assertIn(state_source, sources, viewer.name)
            self.assertLess(sources.index(state_source), sources.index(main_source), viewer.name)

    def test_seed_explorer_uses_shared_api_client(self) -> None:
        viewer = PAGES_DIR / "seed_explorer_viewer.html"
        html = viewer.read_text(encoding="utf-8")
        sources = SCRIPT_SOURCE_PATTERN.findall(html)
        self.assertIn("/static/js/shared/api-client.js", sources)
        self.assertLess(
            sources.index("/static/js/shared/api-client.js"),
            sources.index("/static/js/seed-explorer/page.js"),
        )
        scripts = [
            local_resource_path(viewer, source)
            for source in sources
            if "static/js/seed-explorer/" in source
        ]
        combined_js = "".join(path.read_text(encoding="utf-8") for path in scripts)
        self.assertIn("apiClient.requestJson", combined_js)
        self.assertNotIn("await fetch(", combined_js)

    def test_seed_explorer_scripts_are_split_by_responsibility(self) -> None:
        viewer = PAGES_DIR / "seed_explorer_viewer.html"
        sources = SCRIPT_SOURCE_PATTERN.findall(viewer.read_text(encoding="utf-8"))
        expected = [
            "/static/js/seed-explorer/core.js",
            "/static/js/seed-explorer/operations-financial.js",
            "/static/js/seed-explorer/operations-facilities.js",
            "/static/js/seed-explorer/operations-debt.js",
            "/static/js/seed-explorer/operations-commercial.js",
            "/static/js/seed-explorer/operations-actions.js",
            "/static/js/seed-explorer/operations-renderer.js",
            "/static/js/seed-explorer/city-renderer.js",
            "/static/js/seed-explorer/page.js",
        ]
        positions = [sources.index(source) for source in expected]
        self.assertEqual(sorted(positions), positions)
        self.assertTrue(all(local_resource_path(viewer, source).is_file() for source in expected))

    def test_contract_affairs_uses_full_horizon_when_quarters_advance_locally(self) -> None:
        source = (
            STATIC_DIR / "js" / "seed-explorer" / "operations-actions.js"
        ).read_text(encoding="utf-8")
        self.assertIn("state.operations.allQuarters?.length", source)
        self.assertIn(
            "contractCycleRange(contract, currentTerm.cycleId, fullQuarters)",
            source,
        )
        self.assertIn(
            "contractNextCycleQuarter(contract, currentTerm.cycleId, fullQuarters)",
            source,
        )
        self.assertIn("const withinNegotiationWindow", source)
        self.assertIn("下一期条款将在到期前 4 季开放。", source)

    def test_global_viewer_scripts_are_split_by_responsibility(self) -> None:
        viewer = PAGES_DIR / "global_gdp_viewer.html"
        sources = SCRIPT_SOURCE_PATTERN.findall(viewer.read_text(encoding="utf-8"))
        expected = [
            "/static/js/global-gdp/state.js",
            "/static/js/global-gdp/data-client.js",
            "/static/js/global-gdp/formatters.js",
            "/static/js/global-gdp/preview-model.js",
            "/static/js/global-gdp/controls.js",
            "/static/js/global-gdp/renderers.js",
            "/static/js/global-gdp/page.js",
        ]
        positions = [sources.index(source) for source in expected]
        self.assertEqual(sorted(positions), positions)
        self.assertTrue(all(local_resource_path(viewer, source).is_file() for source in expected))

    def test_operations_viewer_scripts_are_split_by_responsibility(self) -> None:
        viewer = PAGES_DIR / "beijing_airport_operations_viewer.html"
        sources = SCRIPT_SOURCE_PATTERN.findall(viewer.read_text(encoding="utf-8"))
        expected = [
            "/static/js/beijing-operations/state.js",
            "/static/js/beijing-operations/data-client.js",
            "/static/js/beijing-operations/renderers.js",
            "/static/js/beijing-operations/page.js",
        ]
        positions = [sources.index(source) for source in expected]
        self.assertEqual(sorted(positions), positions)
        self.assertTrue(all(local_resource_path(viewer, source).is_file() for source in expected))

    def test_static_viewers_use_atomic_release_manifest_with_legacy_fallback(self) -> None:
        for viewer, manifest_key in VIEWER_MANIFEST_KEYS.items():
            html = viewer.read_text(encoding="utf-8")
            bootstrap = VIEWER_BOOTSTRAP_SCRIPTS[viewer].read_text(encoding="utf-8")
            self.assertIn("./output/current_viewer_manifest.js", html, viewer.name)
            self.assertIn(f"scripts?.{manifest_key}", bootstrap, viewer.name)
            self.assertIn("legacy", html.lower(), viewer.name)


if __name__ == "__main__":
    unittest.main()
