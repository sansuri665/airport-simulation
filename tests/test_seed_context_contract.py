from __future__ import annotations

import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
PAGES_DIR = ROOT_DIR / "web" / "pages"
STATIC_DIR = ROOT_DIR / "web" / "static" / "js"


class SeedContextContractTests(unittest.TestCase):
    def test_shared_context_owns_url_workspace_and_response_identity(self) -> None:
        source = (STATIC_DIR / "shared" / "seed-context.js").read_text(encoding="utf-8")

        self.assertIn('url.searchParams.get("seed")', source)
        self.assertIn('url.searchParams.get("years")', source)
        self.assertIn('requestJson("/api/seed-workspace"', source)
        self.assertIn("window.history.replaceState", source)
        self.assertIn("function requestBody", source)
        self.assertIn("function assertResponse", source)
        self.assertIn("candidate.slotId", source)
        self.assertIn("candidate.cacheRunId", source)
        self.assertIn("activeSlotChanged", source)
        self.assertIn("window.AirportSeedContext", source)

    def test_operations_page_uses_one_context_for_every_seed_request(self) -> None:
        sources = [
            (STATIC_DIR / "seed-explorer" / name).read_text(encoding="utf-8")
            for name in ("core.js", "operations-renderer.js", "page.js")
        ]
        combined = "\n".join(sources)

        for retired_reference in (
            "seedInput",
            "yearsInput",
            "cachedRunSelect",
            "randomButton",
            '"/api/cached-runs"',
            '"/api/random-seed"',
        ):
            self.assertNotIn(retired_reference, combined)
        self.assertGreaterEqual(combined.count("contextRequestBody("), 7)
        self.assertGreaterEqual(combined.count("assertContextResponse("), 6)
        self.assertIn('requestJson("/api/run-job"', combined)
        self.assertIn("/api/jobs/", combined)
        self.assertIn('requestJson("/api/player-simulation"', combined)
        self.assertIn('requestJson("/api/sim-save"', combined)
        self.assertNotIn('requestJson("/api/run"', combined)

    def test_home_operations_link_carries_active_seed_and_years(self) -> None:
        html = (PAGES_DIR / "airport_home.html").read_text(encoding="utf-8")
        source = (STATIC_DIR / "home" / "page.js").read_text(encoding="utf-8")

        self.assertIn('id="seedExplorerLink"', html)
        self.assertIn('seedExplorerLink.href = `/seed-explorer?', source)
        self.assertIn('seed: String(active.seed)', source)
        self.assertIn('years: String(active.years)', source)

    def test_city_page_uses_shared_context_and_context_scoped_chunks(self) -> None:
        html = (PAGES_DIR / "city_market_viewer.html").read_text(encoding="utf-8")
        home = (PAGES_DIR / "airport_home.html").read_text(encoding="utf-8")
        home_source = (STATIC_DIR / "home" / "page.js").read_text(encoding="utf-8")
        client = (STATIC_DIR / "city-markets" / "data-client.js").read_text(encoding="utf-8")
        page = (STATIC_DIR / "city-markets" / "page.js").read_text(encoding="utf-8")

        self.assertIn('/static/js/shared/seed-context.js', html)
        self.assertIn('id="cityMarketsLink"', home)
        self.assertIn('cityMarketsLink.href = `/city-markets?', home_source)
        self.assertIn("await seedContext.resolve()", page)
        self.assertIn("seedContext.refresh()", page)
        self.assertIn("activeSlotChanged", page)
        self.assertIn("/api/city-market-viewer/index", client)
        self.assertIn("/api/city-market-viewer/chunk", client)
        self.assertIn("`${context.slotId}:${cityId}`", client)
        self.assertIn("seedContext.assertResponse", client)

    def test_global_page_uses_shared_context_and_context_scoped_regions(self) -> None:
        html = (PAGES_DIR / "global_gdp_viewer.html").read_text(encoding="utf-8")
        home = (PAGES_DIR / "airport_home.html").read_text(encoding="utf-8")
        home_source = (STATIC_DIR / "home" / "page.js").read_text(encoding="utf-8")
        client = (STATIC_DIR / "global-gdp" / "data-client.js").read_text(encoding="utf-8")
        controls = (STATIC_DIR / "global-gdp" / "controls.js").read_text(encoding="utf-8")
        page = (STATIC_DIR / "global-gdp" / "page.js").read_text(encoding="utf-8")

        self.assertIn('/static/js/shared/seed-context.js', html)
        self.assertIn('id="globalViewerLink"', home)
        self.assertIn('globalViewerLink.href = `/global-gdp?', home_source)
        self.assertIn("await sharedSeedContext.resolve()", page)
        self.assertIn("sharedSeedContext.refresh()", page)
        self.assertIn("activeSlotChanged", page)
        self.assertIn("/api/global-viewer/index", client)
        self.assertIn("/api/global-viewer/region", client)
        self.assertIn("`${data.contextKey}:${regionId}`", client)
        self.assertIn("sharedSeedContext.assertResponse", client)
        self.assertNotIn("randomLargeSeed", controls)
        self.assertNotIn('id="seedSelect"', html)
        self.assertNotIn('id="randomSeedButton"', html)

    def test_short_context_is_not_silently_expanded_for_player_simulation(self) -> None:
        source = (STATIC_DIR / "seed-explorer" / "operations-renderer.js").read_text(
            encoding="utf-8"
        )

        self.assertIn("years < PLAYER_SIMULATION_MIN_YEARS", source)
        self.assertIn("请在首页为同一 Seed 创建 60 年槽位", source)
        self.assertNotIn("expandedForPlayerSimulation", source)


if __name__ == "__main__":
    unittest.main()
