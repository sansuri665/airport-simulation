from __future__ import annotations

import unittest
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
PAGES_DIR = ROOT_DIR / "web" / "pages"


class IdCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del tag
        attributes = dict(attrs)
        element_id = attributes.get("id")
        if element_id:
            self.ids.append(element_id)


class ViewerDomContractTests(unittest.TestCase):
    CONTRACTS = {
        "web/pages/airport_home.html": {
            "serviceState",
            "serviceStateText",
            "releaseMode",
            "releaseRun",
            "releaseSeed",
            "releaseModel",
            "seedWorkspaceState",
            "activeSeedValue",
            "activeYearsValue",
            "activeStatusValue",
            "activeSourceValue",
            "workspaceRevisionValue",
            "generateWorldButton",
            "generationStatus",
            "seedCreateForm",
            "suggestRandomSeedButton",
            "importSeedInput",
            "importYearsInput",
            "advancedYearsSettings",
            "newSeedModeValue",
            "newSeedYearsValue",
            "importSeedButton",
            "retentionInput",
            "planRetentionButton",
            "saveRetentionButton",
            "applyRetentionButton",
            "seedSlotList",
            "workspaceNotice",
            "actionDialog",
            "actionDialogConfirm",
            "cachedRunCount",
            "saveCount",
        },
        "web/pages/global_gdp_viewer.html": {
            "dataStatus",
            "viewSelect",
            "scopeSelect",
            "contextMeta",
            "contextSource",
            "contextChangeNotice",
            "cityMarketsLink",
            "statsGrid",
            "chart",
            "dataBody",
        },
        "web/pages/city_market_viewer.html": {
            "statusText",
            "releaseMeta",
            "contextSource",
            "contextChangeNotice",
            "operationsLink",
            "yearRange",
            "yearLabel",
            "sortSelect",
            "searchInput",
            "cityList",
            "cityTitle",
            "marketScopeTabs",
            "summaryGrid",
            "marketChart",
            "supplyStatusGrid",
            "annualTableHead",
            "annualTableBody",
        },
        "web/pages/beijing_potential_passenger_forecast_viewer.html": {
            "statusText",
            "seedContextLabel",
            "contextChangeNotice",
            "summaryGrid",
            "asOfRange",
              "reportSelect",
              "narrativeTags",
              "actualScore",
              "candidateLab",
              "candidateTier",
              "candidateStyle",
              "candidateModifierMode",
              "candidateScoreMin",
              "candidateScoreMax",
              "generateCandidate",
              "nextCandidate",
              "leaveCandidate",
              "candidateResult",
              "forecastChart",
            "componentGrid",
            "forecastTable",
        },
        "web/pages/seed_explorer_viewer.html": {
            "seedCenterLink",
            "contextSeedValue",
            "contextYearsValue",
            "contextSourceValue",
            "contextSlotValue",
            "contextRevisionValue",
            "contextStatusValue",
            "contextChangeNotice",
            "runButton",
            "status",
            "cityView",
            "operationsView",
            "opsSummaryGrid",
            "financialCashFlowSummary",
            "financialHeaderRow",
            "trafficCapacityChartPanel",
            "trafficCapacityMetricChart",
            "serviceQualityChartPanel",
            "serviceQualityMetricChart",
            "serviceQualityMaintenanceTable",
            "financingAffairsProducts",
            "contractAffairsDecisionList",
            "projectAffairsStartedRows",
        },
    }

    def test_critical_dom_ids_exist_and_are_unique(self) -> None:
        for relative_path, required_ids in self.CONTRACTS.items():
            parser = IdCollector()
            parser.feed((ROOT_DIR / relative_path).read_text(encoding="utf-8"))
            counts = Counter(parser.ids)
            duplicates = sorted(element_id for element_id, count in counts.items() if count > 1)
            self.assertEqual([], duplicates, relative_path)
            self.assertEqual(set(), required_ids - set(parser.ids), relative_path)

    def test_seed_explorer_report_charts_belong_to_their_own_panels(self) -> None:
        viewer = PAGES_DIR / "seed_explorer_viewer.html"
        html = viewer.read_text(encoding="utf-8")

        traffic_panel = html.index('id="trafficCapacityChartPanel"')
        traffic_chart = html.index('id="trafficCapacityMetricChart"')
        service_panel = html.index('id="serviceQualityChartPanel"')
        service_chart = html.index('id="serviceQualityMetricChart"')

        self.assertLess(traffic_panel, traffic_chart)
        self.assertLess(traffic_chart, service_panel)
        self.assertLess(service_panel, service_chart)

    def test_seed_explorer_has_no_page_local_seed_controls(self) -> None:
        html = (PAGES_DIR / "seed_explorer_viewer.html").read_text(encoding="utf-8")

        for retired_id in ("seedInput", "yearsInput", "cachedRunSelect", "randomButton"):
            self.assertNotIn(f'id="{retired_id}"', html)
        self.assertIn("返回 Seed 中心", html)
        self.assertIn("生成当前世界", html)

    def test_home_seed_creation_prefers_sixty_year_standard_mode(self) -> None:
        html = (PAGES_DIR / "airport_home.html").read_text(encoding="utf-8")

        self.assertIn('id="newSeedYearsValue">60 年', html)
        self.assertIn('id="importYearsInput" type="number" min="5" max="90" value="60"', html)
        self.assertIn('id="suggestRandomSeedButton"', html)
        self.assertIn('id="advancedYearsSettings"', html)
        self.assertNotIn('id="randomYearsInput"', html)
        self.assertNotIn('id="createRandomSeedButton"', html)

    def test_city_viewer_labels_city_supply_as_the_operating_constraint(self) -> None:
        html = (PAGES_DIR / "seed_explorer_viewer.html").read_text(encoding="utf-8")
        regional_renderer = (ROOT_DIR / "web" / "static" / "js" / "global-gdp" / "renderers.js").read_text(
            encoding="utf-8"
        )

        self.assertIn("城市航司供给", html)
        self.assertIn("城市航司满足率", html)
        self.assertNotIn("区域未满足", html)
        self.assertIn("区域参考满足", regional_renderer)

    def test_city_market_viewer_stops_at_airline_supply(self) -> None:
        html = (PAGES_DIR / "city_market_viewer.html").read_text(encoding="utf-8")
        renderer = (
            ROOT_DIR / "web" / "static" / "js" / "city-markets" / "renderers.js"
        ).read_text(encoding="utf-8")
        combined = html + renderer

        self.assertIn("供给约束后需求", combined)
        self.assertIn("航司供给缺口", combined)
        self.assertNotIn("机场实际承接", combined)
        self.assertNotIn("机场最大容量", combined)
        self.assertNotIn("机场容量缺口", combined)
        self.assertNotIn("五类客群需求与航司供给", html)
        self.assertEqual(6, html.count("data-market-scope="))

    def test_global_asset_chart_compares_total_return_with_total_return(self) -> None:
        renderer = (
            ROOT_DIR / "web" / "static" / "js" / "global-gdp" / "renderers.js"
        ).read_text(encoding="utf-8")

        self.assertIn("股票总回报", renderer)
        self.assertIn('makeStat("股票总回报指数", fmtIndex(row.global_equity_total_return_index)', renderer)
        self.assertIn("主权债总回报", renderer)
        self.assertIn("居民实际金融财富", renderer)
        self.assertIn("row.global_equity_total_return_index", renderer)
        self.assertIn('scenarioPath("global_equity_total_return_index"', renderer)
        self.assertNotIn("yAsset(row.global_equity_price_index)", renderer)
        self.assertNotIn("yAsset(selected.global_equity_price_index)", renderer)
        self.assertIn("<td>${hasAsset(row) ? fmtIndex(row.global_equity_total_return_index)", renderer)


if __name__ == "__main__":
    unittest.main()
