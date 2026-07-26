from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import sysconfig
import time
import unittest
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
TEST_ROOT = ROOT_DIR / "tests"
for import_root in (ROOT_DIR, TEST_ROOT):
    import_path = str(import_root)
    if import_path not in sys.path:
        sys.path.insert(0, import_path)


QUICK_MODULES = (
    "test_airport_sim_cli",
    "test_asset_a3_integration",
    "test_asset_a4_distribution_audit",
    "test_asset_v04_field_contract",
    "test_background_jobs",
    "test_config_validation",
    "test_forecast_candidate_generator",
    "test_global_bond_accounting_v04",
    "test_global_equity_accounting_v04",
    "test_regional_asset_accounting_v04",
    "test_http_file_response",
    "test_json_schemas",
    "test_loan_rate_v03_contract",
    "test_package_imports",
    "test_regional_air_supply_boundaries",
    "test_seed_context_contract",
    "test_test_suite_runner",
    "test_viewer_dom_contract",
    "test_viewer_smoke",
)

ASSET_MODULES = (
    "test_asset_a3_integration",
    "test_asset_a4_distribution_audit",
    "test_asset_v04_field_contract",
    "test_global_bond_accounting_v04",
    "test_global_equity_accounting_v04",
    "test_regional_asset_accounting_v04",
)

MACRO_MODULES = (
    "test_global_boundary_and_initial_state_contract",
    "test_global_gdp_gap_and_growth_contract",
    "test_global_yield_dollar_contract",
    "test_long_horizon_contract",
    "test_macro_feedback_and_reconciliation_boundaries",
    "test_macro_feedback_convergence_contract",
    "test_safety_baseline",
)

PASSENGER_MODULES = (
    "test_airline_supply_dynamics_profiles",
    "test_city_passenger_demand_contract",
    "test_component_airline_allocation",
    "test_g4_airline_supply_integration",
    "test_passenger_demand_audit",
    "test_regional_air_supply_boundaries",
    "test_regional_aviation_demand_contract",
)

FORECAST_MODULES = (
    "test_forecast_candidate_generator",
    "test_forecast_lazy_loading",
    "test_forecast_narrative_model",
    "test_forecast_viewer_context_service",
    "test_forecast_workspace_services",
)

OPERATIONS_MODULES = (
    "test_beijing_operations_service",
    "test_loan_rate_v03_contract",
    "test_long_horizon_contract",
    "test_player_action_domains",
    "test_player_simulation_service",
)

SERVICE_MODULES = (
    "test_airport_sim_cli",
    "test_api_snapshot",
    "test_atomic_run",
    "test_background_jobs",
    "test_cache_save_api_schemas",
    "test_cache_service",
    "test_city_market_context_service",
    "test_forecast_viewer_context_service",
    "test_forecast_workspace_services",
    "test_global_viewer_context_service",
    "test_http_file_response",
    "test_local_ui",
    "test_orchestrator_release_index_services",
    "test_orchestrator_run_lifecycle_service",
    "test_orchestrator_run_validation_service",
    "test_orchestrator_variant_outputs_service",
    "test_orchestrator_viewer_assets_service",
    "test_run_cache_service",
    "test_seed_workspace_actions",
    "test_seed_workspace_service",
    "test_server_routes",
)

VIEWER_MODULES = (
    "test_city_market_context_service",
    "test_city_market_viewer_lazy_loading",
    "test_forecast_lazy_loading",
    "test_forecast_viewer_context_service",
    "test_global_viewer_context_service",
    "test_global_viewer_lazy_loading",
    "test_local_ui",
    "test_orchestrator_release_index_services",
    "test_orchestrator_viewer_assets_service",
    "test_viewer_dom_contract",
    "test_viewer_release",
    "test_viewer_smoke",
)


@dataclass(frozen=True)
class SuiteDefinition:
    description: str
    modules: tuple[str, ...]
    checks: bool = False


def unique_modules(*groups: Iterable[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(module for group in groups for module in group))


MODEL_MODULES = unique_modules(
    ASSET_MODULES,
    MACRO_MODULES,
    PASSENGER_MODULES,
    FORECAST_MODULES,
    OPERATIONS_MODULES,
)

SUITES = {
    "quick": SuiteDefinition(
        "Static/configuration checks plus lightweight cross-cutting contracts.",
        QUICK_MODULES,
        checks=True,
    ),
    "asset": SuiteDefinition(
        "Asset field, accounting, wealth-bridge, version and migration contracts.",
        ASSET_MODULES,
    ),
    "macro": SuiteDefinition("Global/regional macro, convergence, boundary and long-horizon contracts.", MACRO_MODULES),
    "passenger": SuiteDefinition("Regional demand, city demand, airline supply and passenger audit contracts.", PASSENGER_MODULES),
    "forecast": SuiteDefinition("Forecast narratives, candidates, workspace and lazy-loading contracts.", FORECAST_MODULES),
    "operations": SuiteDefinition("Airport operations, financing and player-action contracts.", OPERATIONS_MODULES),
    "service": SuiteDefinition("API, cache/save, Seed workspace and Run/Release lifecycle contracts.", SERVICE_MODULES),
    "viewer": SuiteDefinition("Viewer publication, context, lazy loading, DOM and HTTP contracts.", VIEWER_MODULES),
    "model": SuiteDefinition(
        "Combined asset, macro, passenger, forecast and operations model contracts.",
        MODEL_MODULES,
    ),
}


@dataclass(frozen=True)
class CheckCommand:
    label: str
    command: tuple[str, ...]


def static_check_commands() -> tuple[CheckCommand, ...]:
    return (
        CheckCommand(
            "Python syntax",
            (sys.executable, "-m", "compileall", "-q", "airport_sim", "macro_layers", "tests", "tools"),
        ),
        CheckCommand("Markdown links", (sys.executable, "tools/check_markdown_links.py")),
        CheckCommand("Browser JavaScript syntax", (sys.executable, "tools/check_javascript_syntax.py")),
        CheckCommand("Configuration contracts", (sys.executable, "-m", "airport_sim", "validate-config")),
    )


def installed_airport_entrypoint() -> str:
    on_path = shutil.which("airport-sim")
    if on_path:
        return on_path
    scripts_dir = Path(sysconfig.get_path("scripts"))
    for name in ("airport-sim", "airport-sim.exe", "airport-sim-script.py"):
        candidate = scripts_dir / name
        if candidate.is_file():
            return str(candidate)
    return "airport-sim"


def release_check_commands() -> tuple[CheckCommand, ...]:
    return (
        *static_check_commands(),
        CheckCommand("Module entrypoint", (sys.executable, "-m", "airport_sim", "--help")),
        CheckCommand("Installed entrypoint", (installed_airport_entrypoint(), "--help")),
        CheckCommand("Whitespace errors", ("git", "diff", "--check")),
    )


def run_checks(commands: Sequence[CheckCommand]) -> bool:
    for check in commands:
        print(f"\n[check] {check.label}", flush=True)
        try:
            result = subprocess.run(check.command, cwd=ROOT_DIR, check=False)
        except FileNotFoundError as error:
            print(f"[failed] {check.label}: {error}", file=sys.stderr)
            return False
        if result.returncode:
            print(f"[failed] {check.label}: exit {result.returncode}", file=sys.stderr)
            return False
    return True


class TimingTextTestResult(unittest.TextTestResult):
    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self.test_timings: list[tuple[float, str]] = []
        self._test_started_at = 0.0

    def startTest(self, test: unittest.case.TestCase) -> None:  # noqa: N802
        self._test_started_at = time.perf_counter()
        super().startTest(test)

    def stopTest(self, test: unittest.case.TestCase) -> None:  # noqa: N802
        elapsed = time.perf_counter() - self._test_started_at
        self.test_timings.append((elapsed, test.id()))
        super().stopTest(test)


def named_test_suite(modules: Sequence[str]) -> unittest.TestSuite:
    return unittest.TestLoader().loadTestsFromNames(list(modules))


def discovered_test_suite() -> unittest.TestSuite:
    return unittest.TestLoader().discover(
        start_dir=str(TEST_ROOT),
        pattern="test_*.py",
    )


def selected_modules(suite_names: Sequence[str]) -> tuple[str, ...]:
    return unique_modules(*(SUITES[name].modules for name in suite_names))


def run_tests(
    suite: unittest.TestSuite,
    *,
    verbosity: int,
    timing_limit: int,
) -> bool:
    count = suite.countTestCases()
    print(f"\n[tests] running {count} test case(s)", flush=True)
    runner = unittest.TextTestRunner(verbosity=verbosity, resultclass=TimingTextTestResult)
    result = runner.run(suite)
    assert isinstance(result, TimingTextTestResult)
    if timing_limit > 0 and result.test_timings:
        print(f"\n[timing] slowest {min(timing_limit, len(result.test_timings))} test case(s)")
        for elapsed, test_id in sorted(result.test_timings, reverse=True)[:timing_limit]:
            print(f"{elapsed:8.3f}s  {test_id}")
    return result.wasSuccessful()


def all_registered_domain_modules() -> set[str]:
    return {
        module
        for name, definition in SUITES.items()
        if name != "model"
        for module in definition.modules
    }


def repository_test_modules() -> set[str]:
    return {
        path.stem
        for path in TEST_ROOT.glob("test_*.py")
        if path.is_file()
    }


def print_suite_catalog() -> None:
    print("Composable local suites:")
    for name, definition in SUITES.items():
        print(f"- {name:10} {len(definition.modules):2} module(s): {definition.description}")
    print("- full        unittest discovery across every tests/test_*.py module")
    print("- release     release checks plus full unittest discovery")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Airport tests by development tier or release gate.",
    )
    parser.add_argument(
        "--suite",
        action="append",
        choices=(*SUITES, "full", "release"),
        help="Suite to run. Repeat to combine domain suites. Defaults to quick.",
    )
    parser.add_argument("--list", action="store_true", help="List suites without running checks or tests.")
    parser.add_argument("--verbosity", type=int, choices=(0, 1, 2), default=1)
    parser.add_argument("--top", type=int, default=10, help="Print the N slowest test cases; use 0 to disable.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.list:
        print_suite_catalog()
        return 0

    requested = args.suite or ["quick"]
    if "release" in requested and len(requested) != 1:
        print("release cannot be combined with other suites.", file=sys.stderr)
        return 2
    if "full" in requested and len(requested) != 1:
        print("full cannot be combined with other suites.", file=sys.stderr)
        return 2

    started = time.perf_counter()
    if requested == ["release"]:
        if not run_checks(release_check_commands()):
            return 1
        success = run_tests(discovered_test_suite(), verbosity=args.verbosity, timing_limit=args.top)
        if success:
            print("\n[release] automated gate passed; complete the documented browser checklist when UI or output changed.")
    elif requested == ["full"]:
        success = run_tests(discovered_test_suite(), verbosity=args.verbosity, timing_limit=args.top)
    else:
        if any(SUITES[name].checks for name in requested) and not run_checks(static_check_commands()):
            return 1
        modules = selected_modules(requested)
        print(f"[suite] {', '.join(requested)} -> {len(modules)} unique module(s)")
        success = run_tests(named_test_suite(modules), verbosity=args.verbosity, timing_limit=args.top)

    elapsed = time.perf_counter() - started
    print(f"\n[summary] suites={','.join(requested)} elapsed={elapsed:.2f}s status={'passed' if success else 'failed'}")
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
