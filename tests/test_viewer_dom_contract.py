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
            "cachedRunCount",
            "saveCount",
        },
        "web/pages/global_gdp_viewer.html": {
            "dataStatus",
            "runSelect",
            "variantSelect",
            "viewSelect",
            "scopeSelect",
            "seedSelect",
            "randomSeedButton",
            "statsGrid",
            "chart",
            "dataBody",
        },
        "web/pages/beijing_airport_operations_viewer.html": {
            "statusText",
            "seedSelect",
            "summaryGrid",
            "chartModeSwitch",
            "financeChart",
            "financeMetrics",
            "assetDetailPanel",
        },
        "web/pages/beijing_potential_passenger_forecast_viewer.html": {
            "statusText",
            "seedSelect",
            "summaryGrid",
            "asOfRange",
            "reportSelect",
            "forecastChart",
            "componentGrid",
            "forecastTable",
        },
        "web/pages/seed_explorer_viewer.html": {
            "seedInput",
            "yearsInput",
            "runButton",
            "randomButton",
            "status",
            "cityView",
            "operationsView",
            "opsSummaryGrid",
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

    def test_city_viewer_labels_city_supply_as_the_operating_constraint(self) -> None:
        html = (PAGES_DIR / "seed_explorer_viewer.html").read_text(encoding="utf-8")
        regional_renderer = (ROOT_DIR / "web" / "static" / "js" / "global-gdp" / "renderers.js").read_text(
            encoding="utf-8"
        )

        self.assertIn("城市航司供给", html)
        self.assertIn("城市航司满足率", html)
        self.assertNotIn("区域未满足", html)
        self.assertIn("区域参考满足", regional_renderer)


if __name__ == "__main__":
    unittest.main()
