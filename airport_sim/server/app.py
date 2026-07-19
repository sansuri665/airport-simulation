from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import webbrowser
from importlib import import_module
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from airport_sim.paths import (
    CONFIG_ROOT,
    MACRO_LAYERS_ROOT,
    OUTPUT_ROOT,
    ROOT_DIR,
    RUN_ROOT,
    SAVE_ROOT,
    SCHEMA_ROOT,
    STATIC_ROOT,
)

from . import api_contract
from . import beijing_operations
from . import city_market_viewer
from . import forecast_candidates
from . import forecast_viewer
from . import global_viewer
from . import http as http_utils
from . import jobs as background_jobs
from . import player_actions
from . import player_financing
from . import player_projects
from . import player_service
from . import progress as progress_store
from . import repository as repositories
from . import routes as server_routes
from . import run_cache
from . import run_locks
from . import run_service
from . import seed_workspace as seed_workspace_service
from . import seed_workspace_actions as seed_workspace_action_service
from . import serializers, storage, validation
from . import workspace_service

_read_config_json_cached = storage._read_config_json_cached
atomic_write_text = storage.atomic_write_text
ensure_inside = storage.ensure_inside
read_config_json = storage.read_config_json
read_csv = storage.read_csv
read_json = storage.read_json
write_csv = storage.write_csv
write_json = storage.write_json


SERVER_DIR = Path(__file__).resolve().parent
VIEWER_HTML = server_routes.VIEWER_HTML
HOME_HTML = server_routes.HOME_HTML
ORCHESTRATOR = MACRO_LAYERS_ROOT / "macro_run_orchestrator_sim.py"
MAX_CACHED_RUNS = max(1, int(os.environ.get("AIRPORT_MAX_CACHED_RUNS", "2")))
MAX_REQUEST_BODY_BYTES = 2 * 1024 * 1024
CACHE_FINGERPRINT_VERSION = "seed-explorer-run-cache-v4"
TASK_PROGRESS_VERSION = progress_store.TASK_PROGRESS_VERSION
MAX_TASK_PROGRESS_ENTRIES = progress_store.MAX_TASK_PROGRESS_ENTRIES
LOCAL_UI_SERVICE_ID = "airport-local-ui-v1"
VERSION_RECORD_PATH = CONFIG_ROOT / "airport_versions.json"
VERSION_RECORD = json.loads(VERSION_RECORD_PATH.read_text(encoding="utf-8"))
MODEL_VERSION = str(VERSION_RECORD["model_version"])
OUTPUT_SCHEMA_VERSION = str(VERSION_RECORD["output_schema_version"])
SEED_EXPLORER_API_SCHEMA_VERSION = str(VERSION_RECORD["seed_explorer_api_schema_version"])
SEED_WORKSPACE_REGISTRY_PATH = SAVE_ROOT.parent / "seed_workspace.json"
VIEWER_ROUTES = server_routes.VIEWER_ROUTES
VIEWER_REDIRECTS = server_routes.VIEWER_REDIRECTS
STATIC_CONTENT_TYPES = server_routes.STATIC_CONTENT_TYPES
SCHEMA_CATALOG_VERSION = api_contract.SCHEMA_CATALOG_VERSION
SCHEMA_FILES = api_contract.SCHEMA_FILES


UnsupportedMediaTypeError = http_utils.UnsupportedMediaTypeError
RequestTooLargeError = http_utils.RequestTooLargeError
CityMarketContextUnavailableError = city_market_viewer.CityMarketContextUnavailableError
GlobalViewerContextUnavailableError = global_viewer.GlobalViewerContextUnavailableError
ForecastViewerContextUnavailableError = forecast_viewer.ForecastViewerContextUnavailableError
ForecastCandidateContextUnavailableError = (
    forecast_candidates.ForecastCandidateContextUnavailableError
)
BEIJING_OPERATIONS_RELATIVE_CSV = Path(
    "baseline/city_airport_quarterly_operations/china_mainland/"
    "beijing_airport_system_quarterly_operations_seed_sweep.csv"
)
BEIJING_FINANCIAL_RELATIVE_CSV = Path(
    "baseline/city_airport_financial_state/china_mainland/"
    "beijing_airport_system_financial_state_seed_sweep.csv"
)
BEIJING_CITY_DEMAND_RELATIVE_CSV = Path(
    "baseline/city_airport_market_demand/china_mainland/"
    "beijing_airport_system_city_airport_demand_seed_sweep.csv"
)
BEIJING_FORECAST_CONFIG = (
    CONFIG_ROOT
    / "city_airport_potential_passenger_forecast"
    / "beijing_airport_system_potential_passenger_forecast_v1.json"
)
if str(MACRO_LAYERS_ROOT) not in sys.path:
    sys.path.insert(0, str(MACRO_LAYERS_ROOT))
forecast_candidate_layer = import_module(
    "city_airport_potential_passenger_forecast_layer_sim"
)
SIMULATION_DIR_NAME = "simulation_default"
SIMULATION_CITY_DEMAND_RELATIVE_CSV = Path(
    f"{SIMULATION_DIR_NAME}/city_airport_market_demand/china_mainland/"
    "beijing_airport_system_city_airport_demand_seed_sweep.csv"
)
SIMULATION_OPERATIONS_RELATIVE_CSV = Path(
    f"{SIMULATION_DIR_NAME}/city_airport_quarterly_operations/china_mainland/"
    "beijing_airport_system_quarterly_operations_seed_sweep.csv"
)
SIMULATION_FINANCIAL_RELATIVE_CSV = Path(
    f"{SIMULATION_DIR_NAME}/city_airport_financial_state/china_mainland/"
    "beijing_airport_system_financial_state_seed_sweep.csv"
)
QUARTERLY_OPERATIONS_SCRIPT = ROOT_DIR / "macro_layers" / "city_airport_quarterly_operations_layer_sim.py"
FINANCIAL_STATE_SCRIPT = ROOT_DIR / "macro_layers" / "city_airport_financial_state_layer_sim.py"
BEIJING_OPERATIONS_CONFIG = (
    ROOT_DIR / "config" / "city_airport_operations" / "beijing_airport_system_quarterly_operations_v1.json"
)
BEIJING_FINANCE_CONFIG = (
    ROOT_DIR / "config" / "city_airport_finance" / "beijing_airport_group_financial_state_v1.json"
)
INITIAL_ACTIVE_FACILITY_SLOTS = "PEK_SLOT_1:extra_large;PEK_SLOT_2:large;PKX_SLOT_1:giant"
INITIAL_DESIGN_CAPACITY_MILLION = 154.0
INITIAL_MAX_CAPACITY_MILLION = 200.0
PLAYER_DECISION_START_YEAR = 2030
SIMULATION_START_YEAR = 2025
PLAYER_SIMULATION_MIN_YEARS = 60
RENOVATION_COOLDOWN_QUARTERS = player_projects.RENOVATION_COOLDOWN_QUARTERS
REBUILD_COOLDOWN_QUARTERS = player_projects.REBUILD_COOLDOWN_QUARTERS
DEMOLITION_CLEARANCE_QUARTERS = player_projects.DEMOLITION_CLEARANCE_QUARTERS
PROJECT_TEMPLATES = player_projects.PROJECT_TEMPLATES
RENAMABLE_SLOT_IDS = player_projects.RENAMABLE_SLOT_IDS
INITIAL_TERMINAL_NUMBERS_BY_AIRPORT = (
    player_projects.INITIAL_TERMINAL_NUMBERS_BY_AIRPORT
)
TERMINAL_NAME_PREFIX_BY_AIRPORT = player_projects.TERMINAL_NAME_PREFIX_BY_AIRPORT
INITIAL_TERMINAL_NUMBER_BY_SLOT = player_projects.INITIAL_TERMINAL_NUMBER_BY_SLOT
INITIAL_SLOT_SIZES = player_projects.INITIAL_SLOT_SIZES
FINANCING_PRODUCTS = player_financing.FINANCING_PRODUCTS
OPERATION_MODE_DETAILS = {
    "replay": {
        "label": "回放模式",
        "description": "读取完整结果，包含测试贷款、测试项目和自动合同续期。",
    },
    "simulate_default": {
        "label": "模拟模式",
        "description": "复用同一 seed 的外部世界，机场侧使用默认初始设施；玩家行动由服务端重算。",
    },
}

RUN_LOCKS_GUARD = run_locks.RUN_LOCKS_GUARD
RUN_LOCKS = run_locks.RUN_LOCKS
RUN_LOCK_USERS = run_locks.RUN_LOCK_USERS
TASK_PROGRESS_LOCK = progress_store.TASK_PROGRESS_LOCK
TASK_PROGRESS = progress_store.TASK_PROGRESS


def structured_log(event: str, **fields: Any) -> None:
    progress_store.structured_log(event, **fields)


def update_task_progress(
    run_id: str,
    seed: int,
    years: int,
    status: str,
    phase: str,
    progress_pct: int,
    message: str,
    *,
    cached: bool | None = None,
) -> dict[str, Any]:
    return progress_store.update_task_progress(
        run_id,
        seed,
        years,
        status,
        phase,
        progress_pct,
        message,
        cached=cached,
        max_entries=MAX_TASK_PROGRESS_ENTRIES,
        logger=structured_log,
    )


def task_progress(run_id: str, seed: int, years: int) -> dict[str, Any]:
    return progress_store.task_progress(run_id, seed, years)


def submit_run_job(seed: int, years: int, force: bool) -> dict[str, Any]:
    run_id = run_id_for(seed, years)
    job_key = f"{run_id}:force={int(force)}"
    return background_jobs.submit_job(
        "seed_run",
        job_key,
        lambda: run_seed(seed, years, force),
        logger=structured_log,
    )


lock_for_run = run_locks.lock_for_run
try_lock_for_run = run_locks.try_lock_for_run


def as_float(value: Any, default: float = 0.0) -> float:
    return validation.as_float(value, default)


def as_bool(value: Any) -> bool:
    return validation.as_bool(value)


def facility_size_catalog() -> dict[str, Any]:
    catalog_path = ROOT_DIR / "config" / "facility_size_catalogs" / "standard_terminal_sizes_v1.json"
    return read_config_json(catalog_path) if catalog_path.exists() else {}


def allowed_rebuild_target_sizes(template: dict[str, Any]) -> list[str]:
    return player_projects.allowed_target_sizes(template, facility_size_catalog())


def allowed_construction_target_sizes(template: dict[str, Any]) -> list[str]:
    return allowed_rebuild_target_sizes(template)


def construction_event_config(target_size: str) -> dict[str, Any]:
    return player_projects.construction_event_config(
        target_size,
        operations_config=read_config_json(BEIJING_OPERATIONS_CONFIG),
        as_float=as_float,
    )


def rebuild_event_config(source_size: str, target_size: str) -> dict[str, Any]:
    return player_projects.rebuild_event_config(
        source_size,
        target_size,
        operations_config=read_config_json(BEIJING_OPERATIONS_CONFIG),
        as_float=as_float,
    )


def demolition_event_config(source_size: str) -> dict[str, Any]:
    return player_projects.demolition_event_config(
        source_size,
        operations_config=read_config_json(BEIJING_OPERATIONS_CONFIG),
        as_float=as_float,
    )


def renovation_event_config(facility_size: str) -> dict[str, Any]:
    return player_projects.renovation_event_config(
        facility_size,
        operations_config=read_config_json(BEIJING_OPERATIONS_CONFIG),
        as_float=as_float,
    )


def as_text(row: dict[str, str], key: str) -> str:
    return str(row.get(key) or "").strip()


def rounded(row: dict[str, str], key: str, digits: int = 4) -> float:
    return round(as_float(row.get(key)), digits)


def clean_seed(value: Any) -> int:
    return validation.clean_seed(value)


def clean_years(value: Any) -> int:
    return validation.clean_years(value)


def clean_operation_mode(value: Any) -> str:
    return validation.clean_operation_mode(value, OPERATION_MODE_DETAILS)


def clean_player_actions(value: Any) -> list[dict[str, Any]]:
    return player_actions.clean_player_actions(
        value,
        as_float=as_float,
        minimum_action_index=(PLAYER_DECISION_START_YEAR - SIMULATION_START_YEAR) * 4,
        project_templates=PROJECT_TEMPLATES,
        financing_products=FINANCING_PRODUCTS,
        renamable_slot_ids=RENAMABLE_SLOT_IDS,
        initial_terminal_numbers_by_airport=INITIAL_TERMINAL_NUMBERS_BY_AIRPORT,
        initial_terminal_number_by_slot=INITIAL_TERMINAL_NUMBER_BY_SLOT,
        initial_slot_sizes=INITIAL_SLOT_SIZES,
        terminal_name_prefix_by_airport=TERMINAL_NAME_PREFIX_BY_AIRPORT,
        renovation_cooldown_quarters=RENOVATION_COOLDOWN_QUARTERS,
        rebuild_cooldown_quarters=REBUILD_COOLDOWN_QUARTERS,
        demolition_clearance_quarters=DEMOLITION_CLEARANCE_QUARTERS,
        allowed_rebuild_target_sizes=allowed_rebuild_target_sizes,
        allowed_construction_target_sizes=allowed_construction_target_sizes,
        construction_event_config=construction_event_config,
        rebuild_event_config=rebuild_event_config,
        demolition_event_config=demolition_event_config,
        renovation_event_config=renovation_event_config,
    )


def player_general_loans(actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return player_financing.player_general_loans(
        actions,
        financing_products=FINANCING_PRODUCTS,
        relative_index_to_year_quarter=relative_index_to_year_quarter,
    )


def relative_index_to_year_quarter(index: int) -> tuple[int, str]:
    return player_actions.relative_index_to_year_quarter(
        index,
        simulation_start_year=SIMULATION_START_YEAR,
    )


def player_slot_names(actions: list[dict[str, Any]]) -> dict[str, str]:
    return player_actions.player_slot_names(
        actions,
        renamable_slot_ids=RENAMABLE_SLOT_IDS,
    )


def player_project_events(
    actions: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    return player_projects.player_project_events(
        actions,
        project_templates=PROJECT_TEMPLATES,
        relative_index_to_year_quarter=relative_index_to_year_quarter,
    )


def project_catalog() -> list[dict[str, Any]]:
    return player_projects.project_catalog(
        root_dir=ROOT_DIR,
        operations_config_path=BEIJING_OPERATIONS_CONFIG,
        read_config_json=read_config_json,
        project_templates=PROJECT_TEMPLATES,
        demolition_clearance_quarters=DEMOLITION_CLEARANCE_QUARTERS,
        as_float=as_float,
        allowed_rebuild_target_sizes=allowed_rebuild_target_sizes,
        allowed_construction_target_sizes=allowed_construction_target_sizes,
        construction_event_config=construction_event_config,
        rebuild_event_config=rebuild_event_config,
        demolition_event_config=demolition_event_config,
        renovation_event_config=renovation_event_config,
    )


def run_id_for(seed: int, years: int) -> str:
    return repositories.run_id_for(seed, years)


def parse_run_id(run_id: str) -> tuple[int | None, int | None]:
    return repositories.parse_run_id(run_id)


def save_repository() -> repositories.SaveRepository:
    return repositories.SaveRepository(ROOT_DIR, SAVE_ROOT)


def sim_save_path(seed: int, years: int) -> Path:
    return save_repository().save_path(seed, years)


def sim_save_summary(seed: int, years: int, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    return save_repository().summary(seed, years, payload)


def read_sim_save(seed: int, years: int) -> dict[str, Any] | None:
    return save_repository().read(seed, years)


def save_sim_save(body: dict[str, Any]) -> dict[str, Any]:
    return player_service.save_sim_save(
        body,
        clean_seed=clean_seed,
        clean_years=clean_years,
        clean_operation_mode=clean_operation_mode,
        as_float=as_float,
        clean_player_actions=clean_player_actions,
        run_root=RUN_ROOT,
        run_id_for=run_id_for,
        sim_save_path=sim_save_path,
        write_json=write_json,
        clock=time.time,
    )


def clear_sim_save(seed: int, years: int) -> None:
    save_repository().clear(seed, years)


cagr_pct = serializers.cagr_pct
market_bottleneck = serializers.market_bottleneck
summarize_city = serializers.summarize_city


def aggregate_run(run_dir: Path, seed: int, years: int, elapsed_sec: float, cached: bool) -> dict[str, Any]:
    return run_service.aggregate_run(
        run_dir,
        seed,
        years,
        elapsed_sec,
        cached,
        root_dir=ROOT_DIR,
        read_csv=read_csv,
        summarize_city=summarize_city,
    )


def cache_path(run_dir: Path) -> Path:
    return run_cache.cache_path(run_dir)


def cache_dependency_files() -> list[Path]:
    return run_cache.dependency_files(SERVER_DIR, ROOT_DIR)


def dependency_bytes(path: Path) -> bytes:
    return run_cache.dependency_bytes(path)


def current_cache_fingerprint() -> str:
    return run_cache.current_fingerprint(
        version=CACHE_FINGERPRINT_VERSION,
        root_dir=ROOT_DIR,
        dependencies=cache_dependency_files(),
        read_dependency=dependency_bytes,
    )


def cache_metadata() -> dict[str, Any]:
    return run_cache.cache_metadata(
        version=CACHE_FINGERPRINT_VERSION,
        fingerprint=current_cache_fingerprint(),
    )


def load_cached(run_dir: Path, expected_fingerprint: str | None = None) -> dict[str, Any] | None:
    return run_cache.load_cached(
        run_dir,
        version=CACHE_FINGERPRINT_VERSION,
        expected_fingerprint=expected_fingerprint,
        current_fingerprint=current_cache_fingerprint,
    )


def save_cached(run_dir: Path, payload: dict[str, Any]) -> None:
    run_cache.save_cached(
        run_dir,
        payload,
        metadata=cache_metadata(),
        atomic_write_text=atomic_write_text,
    )


def cached_run_entry(run_dir: Path, expected_fingerprint: str | None = None) -> dict[str, Any]:
    return run_cache.cached_run_entry(
        run_dir,
        expected_fingerprint,
        load_cached=load_cached,
        parse_run_id=parse_run_id,
        operations_relative_csv=BEIJING_OPERATIONS_RELATIVE_CSV,
    )


def list_cached_runs() -> list[dict[str, Any]]:
    return run_cache.list_cached_runs(
        run_root=RUN_ROOT,
        current_fingerprint=current_cache_fingerprint,
        cached_run_entry=cached_run_entry,
    )


def cache_retention_policy() -> dict[str, Any]:
    return run_cache.retention_policy(MAX_CACHED_RUNS)


def set_cache_retention(max_cached_runs: int) -> dict[str, Any]:
    from airport_sim.cache_service import set_retention

    return set_retention(max_cached_runs)


def prune_cached_runs() -> None:
    run_cache.prune_cached_runs(
        run_root=RUN_ROOT,
        run_locks_guard=RUN_LOCKS_GUARD,
        run_lock_users=RUN_LOCK_USERS,
        cache_retention_policy=cache_retention_policy,
        current_fingerprint=current_cache_fingerprint,
        load_cached=load_cached,
        try_lock_for_run=try_lock_for_run,
        ensure_inside=ensure_inside,
    )


def run_orchestrator(seed: int, years: int, run_dir: Path, force: bool) -> tuple[float, str]:
    return run_service.run_orchestrator(
        seed,
        years,
        run_dir,
        force,
        root_dir=ROOT_DIR,
        run_root=RUN_ROOT,
        orchestrator=ORCHESTRATOR,
        ensure_inside=ensure_inside,
        structured_log=structured_log,
        executable=sys.executable,
        run_process=subprocess.run,
        clock=time.perf_counter,
    )


def run_seed(seed: int, years: int, force: bool) -> dict[str, Any]:
    return run_service.run_seed(
        seed,
        years,
        force,
        run_root=RUN_ROOT,
        run_id_for=run_id_for,
        update_task_progress=update_task_progress,
        load_cached=load_cached,
        lock_for_run=lock_for_run,
        run_orchestrator=run_orchestrator,
        aggregate_run=aggregate_run,
        save_cached=save_cached,
        prune_cached_runs=prune_cached_runs,
    )


def update_simulation_city_row(row: dict[str, str]) -> dict[str, Any]:
    return beijing_operations.update_simulation_city_row(
        row,
        as_float=as_float,
        active_facility_slots=INITIAL_ACTIVE_FACILITY_SLOTS,
        design_capacity=INITIAL_DESIGN_CAPACITY_MILLION,
        max_capacity=INITIAL_MAX_CAPACITY_MILLION,
    )


def write_default_simulation_city_demand_csv(run_dir: Path) -> Path:
    return beijing_operations.write_default_simulation_city_demand_csv(
        run_dir,
        source_relative_csv=BEIJING_CITY_DEMAND_RELATIVE_CSV,
        target_relative_csv=SIMULATION_CITY_DEMAND_RELATIVE_CSV,
        read_csv=read_csv,
        write_csv=write_csv,
        update_row=update_simulation_city_row,
    )


def write_player_simulation_configs(
    run_dir: Path,
    player_actions: list[dict[str, Any]],
) -> tuple[Path, Path]:
    return player_service.write_player_simulation_configs(
        run_dir,
        player_actions,
        simulation_dir_name=SIMULATION_DIR_NAME,
        operations_config_path=BEIJING_OPERATIONS_CONFIG,
        finance_config_path=BEIJING_FINANCE_CONFIG,
        read_config_json=read_config_json,
        player_project_events=player_project_events,
        player_general_loans=player_general_loans,
        write_json=write_json,
    )


def run_layer_command(cmd: list[str], label: str) -> None:
    player_service.run_layer_command(
        cmd,
        label,
        root_dir=ROOT_DIR,
        run_process=subprocess.run,
    )


def ensure_player_simulation_outputs(
    run_dir: Path,
    player_actions: list[dict[str, Any]],
    force: bool,
) -> bool:
    paths = player_service.SimulationPaths(
        root_dir=ROOT_DIR,
        simulation_dir_name=SIMULATION_DIR_NAME,
        operations_relative_csv=SIMULATION_OPERATIONS_RELATIVE_CSV,
        financial_relative_csv=SIMULATION_FINANCIAL_RELATIVE_CSV,
        operations_config=BEIJING_OPERATIONS_CONFIG,
        finance_config=BEIJING_FINANCE_CONFIG,
        quarterly_operations_script=QUARTERLY_OPERATIONS_SCRIPT,
        financial_state_script=FINANCIAL_STATE_SCRIPT,
    )
    return player_service.ensure_player_simulation_outputs(
        run_dir,
        player_actions,
        force,
        paths=paths,
        simulation_dependency_files=(
            Path(__file__),
            Path(beijing_operations.__file__),
            *sorted(SERVER_DIR.glob("player_*.py"), key=lambda path: path.name),
        ),
        read_json=read_json,
        write_json=write_json,
        ensure_inside=ensure_inside,
        remove_tree=shutil.rmtree,
        write_default_city_demand_csv=write_default_simulation_city_demand_csv,
        write_player_simulation_configs=write_player_simulation_configs,
        run_layer_command=run_layer_command,
        executable=sys.executable,
    )


def non_empty_ids(*values: str) -> list[str]:
    return beijing_operations.non_empty_ids(*values)


def quarter_key(row: dict[str, str]) -> tuple[int, str]:
    return beijing_operations.quarter_key(
        row,
        as_float=as_float,
        as_text=as_text,
    )


def quarter_warnings(ops: dict[str, str], finance: dict[str, str]) -> list[str]:
    return beijing_operations.quarter_warnings(
        ops,
        finance,
        rounded=rounded,
        as_text=as_text,
    )


def summarize_beijing_quarter(
    index: int,
    ops: dict[str, str],
    finance: dict[str, str],
) -> dict[str, Any]:
    return beijing_operations.summarize_beijing_quarter(
        index,
        ops,
        finance,
        as_float=as_float,
        as_bool=as_bool,
        as_text=as_text,
        rounded=rounded,
        non_empty_ids=non_empty_ids,
        quarter_warnings=quarter_warnings,
    )


def aggregate_beijing_operations(
    run_dir: Path,
    seed: int,
    years: int,
    cached: bool,
    mode: str = "replay",
    operations_relative_csv: Path = BEIJING_OPERATIONS_RELATIVE_CSV,
    financial_relative_csv: Path = BEIJING_FINANCIAL_RELATIVE_CSV,
) -> dict[str, Any]:
    return beijing_operations.aggregate_beijing_operations(
        run_dir,
        seed,
        years,
        cached,
        mode=mode,
        operations_relative_csv=operations_relative_csv,
        financial_relative_csv=financial_relative_csv,
        root_dir=ROOT_DIR,
        operation_mode_details=OPERATION_MODE_DETAILS,
        read_csv=read_csv,
        quarter_key=quarter_key,
        summarize_quarter=summarize_beijing_quarter,
    )


def _load_beijing_operations_locked(seed: int, years: int, force: bool, mode: str = "replay") -> dict[str, Any]:
    return beijing_operations.load_beijing_operations_locked(
        seed,
        years,
        force,
        mode,
        run_root=RUN_ROOT,
        run_seed=run_seed,
        ensure_player_simulation_outputs=ensure_player_simulation_outputs,
        aggregate_beijing_operations=aggregate_beijing_operations,
        simulation_operations_relative_csv=SIMULATION_OPERATIONS_RELATIVE_CSV,
        simulation_financial_relative_csv=SIMULATION_FINANCIAL_RELATIVE_CSV,
    )


def load_beijing_operations(seed: int, years: int, force: bool, mode: str = "replay") -> dict[str, Any]:
    return beijing_operations.load_beijing_operations(
        seed,
        years,
        force,
        mode,
        run_id_for=run_id_for,
        lock_for_run=lock_for_run,
        load_locked=_load_beijing_operations_locked,
    )


def player_contract_previews(
    quarters: list[dict[str, Any]],
    active_index: int,
) -> dict[str, dict[str, Any]]:
    return player_service.player_contract_previews(
        quarters,
        active_index,
        as_float=as_float,
    )


def _load_player_simulation_locked(
    seed: int,
    years: int,
    force: bool,
    player_actions: list[dict[str, Any]],
    current_quarter_index: int | None,
) -> dict[str, Any]:
    return player_service.load_player_simulation_locked(
        seed,
        years,
        force,
        player_actions,
        current_quarter_index,
        run_root=RUN_ROOT,
        run_seed=run_seed,
        clean_player_actions=clean_player_actions,
        ensure_player_simulation_outputs=ensure_player_simulation_outputs,
        aggregate_beijing_operations=aggregate_beijing_operations,
        simulation_operations_relative_csv=SIMULATION_OPERATIONS_RELATIVE_CSV,
        simulation_financial_relative_csv=SIMULATION_FINANCIAL_RELATIVE_CSV,
        player_slot_names=player_slot_names,
        project_catalog=project_catalog,
        financing_products=FINANCING_PRODUCTS,
        load_financing_policy=lambda: read_config_json(BEIJING_FINANCE_CONFIG)
        .get("debt_policy", {})
        .get("loan_rate_model", {}),
        player_contract_previews=player_contract_previews,
        build_player_response=player_service.build_player_response,
    )


def load_player_simulation(
    seed: int,
    years: int,
    force: bool,
    player_actions: list[dict[str, Any]],
    current_quarter_index: int | None,
) -> dict[str, Any]:
    return player_service.load_player_simulation(
        seed,
        years,
        force,
        player_actions,
        current_quarter_index,
        minimum_years=PLAYER_SIMULATION_MIN_YEARS,
        clean_years=clean_years,
        run_id_for=run_id_for,
        lock_for_run=lock_for_run,
        load_locked=_load_player_simulation_locked,
    )


def current_viewer_release_status() -> dict[str, Any]:
    return workspace_service.current_viewer_release_status(
        output_root=OUTPUT_ROOT,
        read_json=read_json,
    )


def forecast_candidate_source_context(
    seed: int,
    years: int,
    source: str,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    return forecast_candidates.forecast_candidate_source_context(
        seed,
        years,
        source,
        output_root=OUTPUT_ROOT,
        root_dir=ROOT_DIR,
        run_root=RUN_ROOT,
        workspace_payload=seed_workspace_payload,
        run_id_for=run_id_for,
        lock_for_run=lock_for_run,
        read_json=read_json,
        ensure_inside=ensure_inside,
        read_csv=read_csv,
        as_float=as_float,
    )


def forecast_candidate_catalog_payload(
    seed: int,
    years: int,
    source: str,
) -> dict[str, Any]:
    return forecast_candidates.forecast_candidate_catalog_payload(
        seed,
        years,
        source,
        source_context=forecast_candidate_source_context,
        candidate_layer=forecast_candidate_layer,
        config_path=BEIJING_FORECAST_CONFIG,
        as_float=as_float,
    )


def generate_forecast_candidate_payload(body: dict[str, Any]) -> dict[str, Any]:
    return forecast_candidates.generate_forecast_candidate_payload(
        body,
        source_context=forecast_candidate_source_context,
        candidate_layer=forecast_candidate_layer,
        config_path=BEIJING_FORECAST_CONFIG,
        clean_seed=clean_seed,
        clean_years=clean_years,
    )


def workspace_status() -> dict[str, Any]:
    return workspace_service.workspace_status(
        root_dir=ROOT_DIR,
        run_root=RUN_ROOT,
        save_root=SAVE_ROOT,
        service_id=LOCAL_UI_SERVICE_ID,
        list_cached_runs=list_cached_runs,
        current_viewer_release_status=current_viewer_release_status,
        getpid=os.getpid,
    )


def seed_workspace_payload() -> dict[str, Any]:
    return seed_workspace_service.seed_workspace_payload(
        root_dir=ROOT_DIR,
        run_root=RUN_ROOT,
        save_root=SAVE_ROOT,
        registry_path=SEED_WORKSPACE_REGISTRY_PATH,
        read_json=read_json,
        list_cached_runs=list_cached_runs,
        current_viewer_release_status=current_viewer_release_status,
        cache_retention_policy=cache_retention_policy,
        parse_run_id=parse_run_id,
        run_id_for=run_id_for,
    )


def initialise_seed_workspace() -> dict[str, Any]:
    return seed_workspace_service.initialise_registry_if_missing(
        seed_workspace_payload(),
        registry_path=SEED_WORKSPACE_REGISTRY_PATH,
        read_json=read_json,
        atomic_write_text=atomic_write_text,
        parse_run_id=parse_run_id,
        run_id_for=run_id_for,
    )


def seed_workspace_action(body: dict[str, Any]) -> dict[str, Any]:
    return seed_workspace_action_service.handle_action(
        body,
        root_dir=ROOT_DIR,
        run_root=RUN_ROOT,
        save_root=SAVE_ROOT,
        registry_path=SEED_WORKSPACE_REGISTRY_PATH,
        read_json=read_json,
        atomic_write_text=atomic_write_text,
        workspace_payload=seed_workspace_payload,
        parse_run_id=parse_run_id,
        run_id_for=run_id_for,
        try_lock_for_run=try_lock_for_run,
        set_cache_retention=set_cache_retention,
    )


def city_market_viewer_index_payload(seed: int, years: int) -> dict[str, Any]:
    return city_market_viewer.index_payload(
        seed,
        years,
        workspace_payload=seed_workspace_payload,
        run_root=RUN_ROOT,
        run_id_for=run_id_for,
        ensure_inside=ensure_inside,
        lock_for_run=lock_for_run,
        read_csv=read_csv,
        serialize_dataset=serializers.serialize_city_market_viewer_dataset,
    )


def city_market_viewer_chunk_payload(
    seed: int,
    years: int,
    market_id: str,
) -> dict[str, Any]:
    return city_market_viewer.chunk_payload(
        seed,
        years,
        market_id,
        workspace_payload=seed_workspace_payload,
        run_root=RUN_ROOT,
        run_id_for=run_id_for,
        ensure_inside=ensure_inside,
        lock_for_run=lock_for_run,
        read_csv=read_csv,
        serialize_rows=serializers.serialize_city_market_viewer_rows,
    )


def global_viewer_index_payload(seed: int, years: int) -> dict[str, Any]:
    return global_viewer.index_payload(
        seed,
        years,
        workspace_payload=seed_workspace_payload,
        run_root=RUN_ROOT,
        run_id_for=run_id_for,
        ensure_inside=ensure_inside,
        lock_for_run=lock_for_run,
        read_csv=read_csv,
        decode_rows=serializers.decode_viewer_csv_rows,
        optional_scenario_fields=serializers.GLOBAL_VIEWER_OPTIONAL_SCENARIO_FIELDS,
        serialize_core=serializers.serialize_global_viewer_core,
        serialize_dataset=serializers.serialize_global_viewer_dataset,
    )


def global_viewer_region_payload(
    seed: int,
    years: int,
    region_id: str,
) -> dict[str, Any]:
    return global_viewer.region_payload(
        seed,
        years,
        region_id,
        workspace_payload=seed_workspace_payload,
        run_root=RUN_ROOT,
        run_id_for=run_id_for,
        ensure_inside=ensure_inside,
        lock_for_run=lock_for_run,
        read_csv=read_csv,
        decode_rows=serializers.decode_viewer_csv_rows,
        serialize_region=serializers.serialize_global_viewer_region,
    )


def forecast_viewer_index_payload(
    seed: int,
    years: int,
    data_mode: str,
) -> dict[str, Any]:
    return forecast_viewer.index_payload(
        seed,
        years,
        data_mode,
        workspace_payload=seed_workspace_payload,
        run_root=RUN_ROOT,
        run_id_for=run_id_for,
        ensure_inside=ensure_inside,
        lock_for_run=lock_for_run,
        read_csv=read_csv,
        read_config=read_config_json,
        config_path=BEIJING_FORECAST_CONFIG,
        decode_rows=serializers.decode_viewer_csv_rows,
        null_fields=forecast_candidate_layer.FORECAST_VIEWER_NULL_FIELDS,
        serialize_index=forecast_candidate_layer.serialize_viewer_index,
    )


def forecast_viewer_report_payload(
    seed: int,
    years: int,
    data_mode: str,
    report_id: str,
) -> dict[str, Any]:
    return forecast_viewer.report_payload(
        seed,
        years,
        data_mode,
        report_id,
        workspace_payload=seed_workspace_payload,
        run_root=RUN_ROOT,
        run_id_for=run_id_for,
        ensure_inside=ensure_inside,
        lock_for_run=lock_for_run,
        read_csv=read_csv,
        decode_rows=serializers.decode_viewer_csv_rows,
        null_fields=forecast_candidate_layer.FORECAST_VIEWER_NULL_FIELDS,
        serialize_report=forecast_candidate_layer.serialize_viewer_report,
    )


def safe_output_file(request_path: str) -> Path | None:
    return server_routes.safe_tree_file(
        request_path,
        prefix="/output/",
        root=OUTPUT_ROOT,
        allowed_suffixes=STATIC_CONTENT_TYPES,
    )


def safe_schema_file(request_path: str) -> Path | None:
    return server_routes.safe_schema_file(request_path, root=SCHEMA_ROOT)


def safe_static_file(request_path: str) -> Path | None:
    return server_routes.safe_tree_file(
        request_path,
        prefix="/static/",
        root=STATIC_ROOT,
        allowed_suffixes=STATIC_CONTENT_TYPES,
    )


def is_loopback_host(host: str | None) -> bool:
    return server_routes.is_loopback_host(host)


def request_is_local(handler: BaseHTTPRequestHandler) -> bool:
    return server_routes.request_is_local(handler)


def api_schema_catalog() -> dict[str, Any]:
    return api_contract.schema_catalog()


def api_metadata() -> dict[str, Any]:
    return api_contract.api_metadata(
        api_schema_version=SEED_EXPLORER_API_SCHEMA_VERSION,
        model_version=MODEL_VERSION,
        output_schema_version=OUTPUT_SCHEMA_VERSION,
    )


def api_envelope(payload: dict[str, Any]) -> dict[str, Any]:
    return http_utils.api_envelope(payload, api_metadata())


def json_response(handler: BaseHTTPRequestHandler, status: int, payload: dict[str, Any]) -> None:
    http_utils.json_response(handler, status, payload, api_metadata())


def api_error_response(
    handler: BaseHTTPRequestHandler,
    status: int,
    error_code: str,
    message: str,
) -> None:
    http_utils.api_error_response(handler, status, error_code, message, api_metadata())


def read_json_request(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    return http_utils.read_json_request(handler, MAX_REQUEST_BODY_BYTES)


def redirect_response(handler: BaseHTTPRequestHandler, location: str) -> None:
    http_utils.redirect_response(handler, location)


def file_response_policy(path: Path, content_type: str) -> tuple[str, bool]:
    del content_type
    try:
        relative = path.resolve().relative_to(OUTPUT_ROOT.resolve())
    except ValueError:
        return "no-cache", False
    if len(relative.parts) >= 3 and relative.parts[0] == "viewer_releases":
        return "public, max-age=31536000, immutable", path.suffix.lower() in {".js", ".json"}
    return "no-cache", False


def file_response(handler: BaseHTTPRequestHandler, path: Path, content_type: str) -> None:
    cache_control, allow_gzip = file_response_policy(path, content_type)
    http_utils.file_response(
        handler,
        path,
        content_type,
        cache_control=cache_control,
        allow_gzip=allow_gzip,
    )


SeedExplorerHandler = server_routes.SeedExplorerHandler


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Airport local UI and full-chain seed explorer.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8776)
    parser.add_argument(
        "--allow-non-loopback",
        action="store_true",
        help="Explicitly allow binding outside localhost; disables local Host/Origin checks.",
    )
    parser.add_argument("--open", action="store_true", help="Open the local UI in the default browser.")
    parser.add_argument("--open-path", default="/", help="Local page to open after starting the server.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not is_loopback_host(args.host) and not args.allow_non_loopback:
        raise ValueError("non-loopback --host requires explicit --allow-non-loopback")
    if not ORCHESTRATOR.exists():
        raise FileNotFoundError(f"missing orchestrator: {ORCHESTRATOR}")
    if not HOME_HTML.exists():
        raise FileNotFoundError(f"missing local UI home page: {HOME_HTML}")
    if not VIEWER_HTML.exists():
        raise FileNotFoundError(f"missing viewer: {VIEWER_HTML}")
    missing_schemas = [
        str((SCHEMA_ROOT / filename).relative_to(ROOT_DIR).as_posix())
        for filename in SCHEMA_FILES.values()
        if not (SCHEMA_ROOT / filename).is_file()
    ]
    if missing_schemas:
        raise FileNotFoundError(f"missing API Schema files: {', '.join(missing_schemas)}")
    seed_workspace_initialisation = initialise_seed_workspace()
    if seed_workspace_initialisation["status"] != "ready":
        structured_log(
            "seed_workspace_registry_warning",
            status=seed_workspace_initialisation["status"],
            warnings=seed_workspace_initialisation["warnings"],
        )
    server = ThreadingHTTPServer((args.host, args.port), SeedExplorerHandler)
    server.allow_non_loopback = bool(args.allow_non_loopback)
    base_url = f"http://{args.host}:{args.port}"
    open_path = str(args.open_path or "/").strip()
    if not open_path.startswith("/") or open_path.startswith("//"):
        raise ValueError("--open-path must be a local absolute path beginning with one '/'")
    url = f"{base_url}{open_path}"
    print(f"Airport local UI listening on {base_url}/")
    print("Press Ctrl+C to stop.")
    if args.open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Seed Explorer.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
