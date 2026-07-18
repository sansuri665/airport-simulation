from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


ROOT_DIR = Path(__file__).resolve().parents[1]
MACRO_DIR = ROOT_DIR / "macro_layers"
if str(MACRO_DIR) not in sys.path:
    sys.path.insert(0, str(MACRO_DIR))

import macro_run_orchestrator_sim as orchestrator
import orchestrator_variant_outputs as variant_outputs

from airport_sim.server import run_cache


FIELD_NAMES = (
    "global_fields",
    "regional_fields",
    "reconciled_fields",
    "diagnostic_fields",
    "aviation_fields",
    "supply_fields",
    "city_fields",
    "forecast_fields",
    "operations_fields",
    "financial_fields",
    "valuation_fields",
)


def global_result() -> dict[str, object]:
    return {
        "rows": [{"seed": 7, "kind": "global"}],
        "params": {
            "object": SimpleNamespace(alpha=1),
            "scalar": 2,
        },
        "summary": {"summary": "global"},
        "convergence": {"converged": True},
    }


def regional_result(region_order: tuple[str, ...] = ("r1",)) -> dict[str, object]:
    return {
        "regional_rows_by_region": {
            region_id: [{"seed": 7, "region_id": region_id}]
            for region_id in region_order
        },
        "regional_summaries": [
            {"region_id": region_id, "summary": region_id}
            for region_id in reversed(region_order)
        ],
        "reconciled_rows": [{"seed": 7, "region_id": region_order[0]}],
        "diagnostics": [{"seed": 7, "diagnostic": "d"}],
        "reconciliation_summaries": [{"summary": "reconciled"}],
        "aviation_rows_by_region": {},
        "aviation_summaries": [],
        "supply_rows_by_region": {},
        "supply_summaries": [],
        "city_airport_rows_by_market": {},
        "city_airport_summaries": [],
        "potential_passenger_forecast_rows_by_market": {},
        "potential_passenger_forecast_summaries": {},
        "quarterly_operations_rows_by_market": {},
        "quarterly_operations_summaries": {},
        "financial_state_rows_by_market": {},
        "financial_state_summaries": {},
        "valuation_forecast_rows_by_market": {},
        "valuation_forecast_summaries": {},
        "city_airport_downstream_skips": [{"market": "skipped"}],
    }


def populated_regional_result() -> dict[str, object]:
    result = regional_result()
    result.update(
        {
            "aviation_rows_by_region": {
                "r1": [{"seed": 7, "region_id": "r1", "kind": "aviation"}],
            },
            "aviation_summaries": [
                {"region_id": "other", "summary": "ignore"},
                {"region_id": "r1", "summary": "aviation"},
            ],
            "supply_rows_by_region": {
                "r1": [{"seed": 7, "region_id": "r1", "kind": "supply"}],
            },
            "supply_summaries": [{"region_id": "r1", "summary": "supply"}],
            "city_airport_rows_by_market": {
                "m1": [{"seed": 7, "region_id": "r1", "kind": "city"}],
            },
            "city_airport_summaries": [
                {"city_airport_market_id": "m1", "summary": "city"},
            ],
            "potential_passenger_forecast_rows_by_market": {
                "m1": [{"seed": 7, "region_id": "r1", "kind": "forecast"}],
            },
            "potential_passenger_forecast_summaries": {
                "m1": {"summary": "forecast"},
            },
            "quarterly_operations_rows_by_market": {
                "m1": [{"seed": 7, "region_id": "r1", "kind": "operations"}],
            },
            "quarterly_operations_summaries": {
                "m1": {"summary": "operations"},
            },
            "financial_state_rows_by_market": {
                "m1": [{"seed": 7, "region_id": "r1", "kind": "financial"}],
            },
            "financial_state_summaries": {
                "m1": {"summary": "financial"},
            },
            "valuation_forecast_rows_by_market": {
                "m1": [{"seed": 7, "region_id": "r1", "kind": "valuation"}],
            },
            "valuation_forecast_summaries": {
                "m1": {"summary": "valuation"},
            },
        }
    )
    return result


def make_dependencies(
    events: list[tuple[str, tuple[object, ...]]],
    *,
    region_order: tuple[str, ...] = ("r1",),
    config_maps: dict[Path, dict[str, dict[str, object]]] | None = None,
) -> variant_outputs.VariantOutputDependencies:
    config_maps = config_maps or {}

    def record(name: str):
        def callback(*args: object) -> None:
            events.append((name, args))

        return callback

    def load_configs(config_dir: Path, loader: object) -> dict[str, dict[str, object]]:
        events.append(("load_configs", (config_dir, loader)))
        return config_maps.get(config_dir, {})

    fields = {name: (name,) for name in FIELD_NAMES}
    return variant_outputs.VariantOutputDependencies(
        orchestrator_version="orchestrator-test",
        region_order=region_order,
        global_output_fields=fields["global_fields"],
        regional_macro_fields=fields["regional_fields"],
        regional_value_fields=fields["reconciled_fields"],
        diagnostic_fields=fields["diagnostic_fields"],
        aviation_demand_fields=fields["aviation_fields"],
        air_supply_fields=fields["supply_fields"],
        city_airport_demand_fields=fields["city_fields"],
        potential_passenger_forecast_fields=fields["forecast_fields"],
        quarterly_operations_fields=fields["operations_fields"],
        financial_state_fields=fields["financial_fields"],
        valuation_forecast_fields=fields["valuation_fields"],
        potential_passenger_forecast_config_dir=Path("forecast-config"),
        financial_state_config_dir=Path("financial-config"),
        valuation_forecast_config_dir=Path("valuation-config"),
        load_potential_passenger_forecast_config="forecast-loader",
        load_financial_state_config="financial-loader",
        load_valuation_forecast_config="valuation-loader",
        write_csv_file=record("csv"),
        write_json_file=record("json"),
        write_global_viewer_data_js=record("global_viewer"),
        write_regional_viewer_data_js=record("regional_viewer"),
        write_reconciliation_viewer_js=record("reconciliation_viewer"),
        write_aviation_viewer_data_js=record("aviation_viewer"),
        write_supply_viewer_data_js=record("supply_viewer"),
        write_global_viewer_lazy_assets=record("global_lazy"),
        write_city_airport_viewer_data_js=record("city_viewer"),
        load_city_configs_by_market=load_configs,
        write_potential_passenger_forecast_lazy_assets=record("forecast_lazy"),
        write_quarterly_operations_viewer_data_js=record("operations_viewer"),
        write_financial_state_viewer_data_js=record("financial_viewer"),
        write_valuation_forecast_viewer_data_js=record("valuation_viewer"),
        write_operations_viewer_lazy_assets=record("operations_lazy"),
    )


class VariantOutputCompatibilityTests(unittest.TestCase):
    def test_orchestrator_wrapper_delegates_all_current_functions_constants_and_loaders(self) -> None:
        sentinel = object()
        with mock.patch.object(
            variant_outputs,
            "write_variant_outputs",
            return_value=sentinel,
        ) as service:
            result = orchestrator.write_variant_outputs(
                Path("variant"),
                7,
                "baseline",
                {"rows": []},
                {},
                None,
                artifact_profile="seed-cache",
            )

        self.assertIsNone(result)
        self.assertEqual(
            (Path("variant"), 7, "baseline", {"rows": []}, {}, None),
            service.call_args.args,
        )
        self.assertEqual("seed-cache", service.call_args.kwargs["artifact_profile"])
        dependencies = service.call_args.kwargs["dependencies"]
        expected_functions = {
            "write_csv_file": orchestrator.write_csv_file,
            "write_json_file": orchestrator.write_json_file,
            "write_global_viewer_data_js": orchestrator.write_global_viewer_data_js,
            "write_regional_viewer_data_js": orchestrator.write_regional_viewer_data_js,
            "write_reconciliation_viewer_js": orchestrator.write_reconciliation_viewer_js,
            "write_aviation_viewer_data_js": orchestrator.write_aviation_viewer_data_js,
            "write_supply_viewer_data_js": orchestrator.write_supply_viewer_data_js,
            "write_global_viewer_lazy_assets": orchestrator.write_global_viewer_lazy_assets,
            "write_city_airport_viewer_data_js": orchestrator.write_city_airport_viewer_data_js,
            "load_city_configs_by_market": orchestrator.load_city_configs_by_market,
            "write_potential_passenger_forecast_lazy_assets": (
                orchestrator.write_potential_passenger_forecast_lazy_assets
            ),
            "write_quarterly_operations_viewer_data_js": (
                orchestrator.write_quarterly_operations_viewer_data_js
            ),
            "write_financial_state_viewer_data_js": orchestrator.write_financial_state_viewer_data_js,
            "write_valuation_forecast_viewer_data_js": orchestrator.write_valuation_forecast_viewer_data_js,
            "write_operations_viewer_lazy_assets": orchestrator.write_operations_viewer_lazy_assets,
        }
        for name, expected in expected_functions.items():
            with self.subTest(name=name):
                self.assertIs(expected, getattr(dependencies, name))
        self.assertEqual(orchestrator.REGION_ORDER, dependencies.region_order)
        self.assertEqual(orchestrator.ORCHESTRATOR_VERSION, dependencies.orchestrator_version)
        self.assertIs(
            orchestrator.load_potential_passenger_forecast_config,
            dependencies.load_potential_passenger_forecast_config,
        )
        self.assertIs(
            orchestrator.load_financial_state_config,
            dependencies.load_financial_state_config,
        )
        self.assertIs(
            orchestrator.load_valuation_forecast_config,
            dependencies.load_valuation_forecast_config,
        )

    def test_new_variant_output_module_is_a_seed_cache_dependency(self) -> None:
        names = {
            path.name
            for path in run_cache.dependency_files(
                ROOT_DIR / "airport_sim" / "server",
                ROOT_DIR,
            )
        }
        self.assertIn("orchestrator_variant_outputs.py", names)


class VariantOutputOrderTests(unittest.TestCase):
    def test_full_profile_keeps_writer_order_paths_and_base_field_mapping(self) -> None:
        events: list[tuple[str, tuple[object, ...]]] = []
        forecast_config = {"kind": "forecast-config"}
        financial_config = {"kind": "financial-config"}
        valuation_config = {"kind": "valuation-config"}
        dependencies = make_dependencies(
            events,
            config_maps={
                Path("forecast-config"): {"m1": forecast_config},
                Path("financial-config"): {"m1": financial_config},
                Path("valuation-config"): {"m1": valuation_config},
            },
        )
        variant_dir = Path("variant")

        variant_outputs.write_variant_outputs(
            variant_dir,
            7,
            "baseline",
            global_result(),
            populated_regional_result(),
            None,
            artifact_profile="full",
            dependencies=dependencies,
        )

        self.assertEqual(
            [
                "csv", "json", "global_viewer",
                "csv", "json", "regional_viewer",
                "csv", "csv", "json", "json", "reconciliation_viewer",
                "csv", "json", "aviation_viewer",
                "csv", "json", "supply_viewer",
                "global_lazy",
                "csv", "json", "city_viewer",
                "csv", "json", "load_configs", "forecast_lazy",
                "csv", "json", "operations_viewer",
                "csv", "json", "load_configs", "financial_viewer",
                "csv", "json", "load_configs", "valuation_viewer",
                "operations_lazy",
                "json",
            ],
            [name for name, _ in events],
        )

        csv_events = [args for name, args in events if name == "csv"]
        self.assertEqual(
            [
                "global_fields",
                "regional_fields",
                "reconciled_fields",
                "diagnostic_fields",
                "aviation_fields",
                "supply_fields",
                "city_fields",
                "forecast_fields",
                "operations_fields",
                "financial_fields",
                "valuation_fields",
            ],
            [args[2][0] for args in csv_events],
        )
        self.assertEqual(
            [
                "global_macro/global_macro_feedback_seed_sweep.csv",
                "regional_macro/r1/r1_regional_macro_seed_sweep.csv",
                "regional_macro_reconciled/regional_macro_reconciled_seed_sweep.csv",
                "regional_macro_reconciled/regional_macro_reconciliation_seed_sweep.csv",
                "regional_aviation_demand/r1/r1_aviation_demand_seed_sweep.csv",
                "regional_air_capacity_supply/r1/r1_air_capacity_supply_seed_sweep.csv",
                "city_airport_market_demand/r1/m1_city_airport_demand_seed_sweep.csv",
                "city_airport_potential_passenger_forecast/r1/m1_potential_passenger_forecast_seed_sweep.csv",
                "city_airport_quarterly_operations/r1/m1_quarterly_operations_seed_sweep.csv",
                "city_airport_financial_state/r1/m1_financial_state_seed_sweep.csv",
                "city_airport_valuation/r1/m1_valuation_forecast_seed_sweep.csv",
            ],
            [args[0].relative_to(variant_dir).as_posix() for args in csv_events],
        )
        self.assertIs(forecast_config, next(args for name, args in events if name == "forecast_lazy")[2])
        self.assertIs(financial_config, next(args for name, args in events if name == "financial_viewer")[2])
        self.assertIs(valuation_config, next(args for name, args in events if name == "valuation_viewer")[2])

    def test_non_full_profiles_write_no_viewer_assets_and_do_not_load_configs(self) -> None:
        forbidden = {
            "global_viewer",
            "regional_viewer",
            "reconciliation_viewer",
            "aviation_viewer",
            "supply_viewer",
            "global_lazy",
            "city_viewer",
            "load_configs",
            "forecast_lazy",
            "operations_viewer",
            "financial_viewer",
            "valuation_viewer",
            "operations_lazy",
        }
        for profile in ("seed-cache", "unknown-profile"):
            with self.subTest(profile=profile):
                events: list[tuple[str, tuple[object, ...]]] = []
                variant_outputs.write_variant_outputs(
                    Path("variant"),
                    7,
                    "baseline",
                    global_result(),
                    populated_regional_result(),
                    None,
                    artifact_profile=profile,
                    dependencies=make_dependencies(events),
                )
                names = [name for name, _ in events]
                self.assertTrue(names)
                self.assertTrue(forbidden.isdisjoint(names))
                self.assertEqual("json", names[-1])
                self.assertTrue(str(events[-1][1][0]).endswith("city_airport_downstream_skips.json"))

    def test_region_order_mapping_insertion_order_empty_rows_and_unknown_region_are_preserved(self) -> None:
        events: list[tuple[str, tuple[object, ...]]] = []
        result = regional_result(("r1", "r2"))
        result["regional_rows_by_region"] = {
            "r1": [{"seed": 7, "region_id": "r1"}],
            "r2": [{"seed": 7, "region_id": "r2"}],
        }
        result["aviation_rows_by_region"] = {
            "z": [{"seed": 7, "region_id": "z"}],
            "a": [{"seed": 7, "region_id": "a"}],
        }
        result["city_airport_rows_by_market"] = {
            "z_market": [{"seed": 7, "region_id": ""}],
            "empty_market": [],
            "a_market": [{"seed": 7, "region_id": "a"}],
        }

        variant_outputs.write_variant_outputs(
            Path("variant"),
            7,
            "baseline",
            global_result(),
            result,
            None,
            artifact_profile="seed-cache",
            dependencies=make_dependencies(events, region_order=("r2", "r1")),
        )

        csv_paths = [str(args[0]).replace("\\", "/") for name, args in events if name == "csv"]
        regional_paths = [path for path in csv_paths if "/regional_macro/" in path]
        aviation_paths = [path for path in csv_paths if "/regional_aviation_demand/" in path]
        city_paths = [path for path in csv_paths if "/city_airport_market_demand/" in path]
        self.assertTrue(regional_paths[0].endswith("/r2/r2_regional_macro_seed_sweep.csv"))
        self.assertTrue(regional_paths[1].endswith("/r1/r1_regional_macro_seed_sweep.csv"))
        self.assertTrue(aviation_paths[0].endswith("/z/z_aviation_demand_seed_sweep.csv"))
        self.assertTrue(aviation_paths[1].endswith("/a/a_aviation_demand_seed_sweep.csv"))
        self.assertTrue(city_paths[0].endswith("/unknown_region/z_market_city_airport_demand_seed_sweep.csv"))
        self.assertTrue(city_paths[1].endswith("/a/a_market_city_airport_demand_seed_sweep.csv"))
        self.assertFalse(any("empty_market" in path for path in csv_paths))


class VariantOutputPayloadTests(unittest.TestCase):
    def test_summary_payloads_filter_and_embed_the_same_values(self) -> None:
        events: list[tuple[str, tuple[object, ...]]] = []
        scenario = {"state": "occurred"}
        result = populated_regional_result()
        variant_outputs.write_variant_outputs(
            Path("variant"),
            7,
            "scenario",
            global_result(),
            result,
            scenario,
            artifact_profile="seed-cache",
            dependencies=make_dependencies(events),
        )
        payloads = {
            Path(args[0]).name: args[1]
            for name, args in events
            if name == "json"
        }

        global_payload = payloads["global_macro_feedback_seed_sweep_summary.json"]
        self.assertEqual("orchestrator-test", global_payload["orchestrator_version"])
        self.assertEqual("scenario", global_payload["variant"])
        self.assertIs(scenario, global_payload["scenario"])
        self.assertEqual({"alpha": 1}, global_payload["params"]["object"])
        self.assertEqual(2, global_payload["params"]["scalar"])
        self.assertEqual([{"summary": "global"}], global_payload["summaries"])
        self.assertEqual([{"converged": True}], global_payload["convergence"])

        regional_payload = payloads["r1_regional_macro_summary.json"]
        self.assertEqual([{"region_id": "r1", "summary": "r1"}], regional_payload["summaries"])
        self.assertEqual(1, payloads["regional_macro_reconciliation_seed_sweep.json"]["diagnostics"])
        self.assertEqual(1, payloads["regional_macro_reconciled_summary.json"]["rows"])
        self.assertEqual(
            [{"region_id": "r1", "summary": "aviation"}],
            payloads["r1_aviation_demand_summary.json"]["summaries"],
        )
        self.assertEqual(
            [{"city_airport_market_id": "m1", "summary": "city"}],
            payloads["m1_city_airport_demand_summary.json"]["summaries"],
        )
        self.assertEqual(
            {"summary": "forecast"},
            payloads["m1_potential_passenger_forecast_summary.json"]["summary"],
        )
        self.assertEqual(
            [{"market": "skipped"}],
            payloads["city_airport_downstream_skips.json"]["skips"],
        )

    def test_full_profile_loads_configs_per_nonempty_market_and_assembles_operations_lazy_rows(self) -> None:
        events: list[tuple[str, tuple[object, ...]]] = []
        result = regional_result()
        result["potential_passenger_forecast_rows_by_market"] = {
            "m2": [{"region_id": "r2"}],
            "empty": [],
            "m1": [{"region_id": "r1"}],
        }
        result["financial_state_rows_by_market"] = {
            "m2": [{"region_id": "r2", "financial": 2}],
            "m1": [{"region_id": "r1", "financial": 1}],
        }
        result["valuation_forecast_rows_by_market"] = {
            "m2": [{"region_id": "r2", "valuation": 2}],
            "m1": [{"region_id": "r1", "valuation": 1}],
        }
        result["quarterly_operations_rows_by_market"] = {
            "m1": [{"region_id": "r1", "operations": 1}],
            "m3": [{"region_id": "r3", "operations": 3}],
        }
        forecast_m2 = {"forecast": 2}
        financial_m1 = {"financial": 1}
        valuation_m2 = {"valuation": 2}
        dependencies = make_dependencies(
            events,
            config_maps={
                Path("forecast-config"): {"m2": forecast_m2},
                Path("financial-config"): {"m1": financial_m1},
                Path("valuation-config"): {"m2": valuation_m2},
            },
        )

        variant_outputs.write_variant_outputs(
            Path("variant"),
            7,
            "baseline",
            global_result(),
            result,
            None,
            artifact_profile="full",
            dependencies=dependencies,
        )

        load_events = [args for name, args in events if name == "load_configs"]
        self.assertEqual(
            [
                Path("forecast-config"), Path("forecast-config"),
                Path("financial-config"), Path("financial-config"),
                Path("valuation-config"), Path("valuation-config"),
            ],
            [args[0] for args in load_events],
        )
        forecast_events = [args for name, args in events if name == "forecast_lazy"]
        self.assertIs(forecast_m2, forecast_events[0][2])
        self.assertEqual({}, forecast_events[1][2])
        financial_events = [args for name, args in events if name == "financial_viewer"]
        self.assertEqual({}, financial_events[0][2])
        self.assertIs(financial_m1, financial_events[1][2])
        valuation_events = [args for name, args in events if name == "valuation_viewer"]
        self.assertIs(valuation_m2, valuation_events[0][2])
        self.assertEqual({}, valuation_events[1][2])

        operations_events = [args for name, args in events if name == "operations_lazy"]
        self.assertEqual(["m1", "m3"], [args[1] for args in operations_events])
        self.assertIs(result["quarterly_operations_rows_by_market"]["m1"], operations_events[0][2])
        self.assertIs(result["financial_state_rows_by_market"]["m1"], operations_events[0][3])
        self.assertIs(result["valuation_forecast_rows_by_market"]["m1"], operations_events[0][4])
        self.assertEqual([], operations_events[1][3])
        self.assertEqual([], operations_events[1][4])


if __name__ == "__main__":
    unittest.main()
