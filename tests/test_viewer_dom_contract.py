from __future__ import annotations

import unittest
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


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
        "airport_home.html": {
            "serviceState",
            "serviceStateText",
            "releaseMode",
            "releaseRun",
            "releaseSeed",
            "releaseModel",
            "cachedRunCount",
            "saveCount",
        },
        "global_gdp_viewer.html": {
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
        "beijing_airport_operations_viewer.html": {
            "statusText",
            "seedSelect",
            "summaryGrid",
            "chartModeSwitch",
            "financeChart",
            "financeMetrics",
            "assetDetailPanel",
        },
        "beijing_potential_passenger_forecast_viewer.html": {
            "statusText",
            "seedSelect",
            "summaryGrid",
            "asOfRange",
            "reportSelect",
            "forecastChart",
            "componentGrid",
            "forecastTable",
        },
        "dynamic_tests/seed_explorer/seed_explorer_viewer.html": {
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
        viewer = ROOT_DIR / "dynamic_tests" / "seed_explorer" / "seed_explorer_viewer.html"
        html = viewer.read_text(encoding="utf-8")

        traffic_panel = html.index('id="trafficCapacityChartPanel"')
        traffic_chart = html.index('id="trafficCapacityMetricChart"')
        service_panel = html.index('id="serviceQualityChartPanel"')
        service_chart = html.index('id="serviceQualityMetricChart"')

        self.assertLess(traffic_panel, traffic_chart)
        self.assertLess(traffic_chart, service_panel)
        self.assertLess(service_panel, service_chart)


if __name__ == "__main__":
    unittest.main()
