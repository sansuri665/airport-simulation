from __future__ import annotations

import hashlib
import json
import subprocess
import time
from contextlib import AbstractContextManager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable


@dataclass(frozen=True)
class SimulationPaths:
    root_dir: Path
    simulation_dir_name: str
    operations_relative_csv: Path
    financial_relative_csv: Path
    operations_config: Path
    finance_config: Path
    quarterly_operations_script: Path
    financial_state_script: Path


def save_sim_save(
    body: dict[str, Any],
    *,
    clean_seed: Callable[[Any], int],
    clean_years: Callable[[Any], int],
    clean_operation_mode: Callable[[Any], str],
    as_float: Callable[[Any, float], float],
    clean_player_actions: Callable[[Any], list[dict[str, Any]]],
    run_root: Path,
    run_id_for: Callable[[int, int], str],
    sim_save_path: Callable[[int, int], Path],
    write_json: Callable[[Path, dict[str, Any]], None],
    clock: Callable[[], float] = time.time,
) -> dict[str, Any]:
    seed = clean_seed(body.get("seed"))
    years = clean_years(body.get("years", 60))
    mode = clean_operation_mode(body.get("mode", "simulate_default"))
    if mode != "simulate_default":
        raise ValueError("dynamic test save only supports simulate_default mode")
    run_dir = run_root / run_id_for(seed, years)
    if not run_dir.exists():
        raise FileNotFoundError("请先加载当前 seed 的模拟运营，再保存动态测试存档")
    current_index = int(as_float(body.get("currentQuarterIndex"), 0.0))
    contract_signatures = body.get("contractSignatures", {})
    if not isinstance(contract_signatures, dict):
        contract_signatures = {}
    player_actions = clean_player_actions(body.get("playerActions", []))
    now = clock()
    payload = {
        "schemaVersion": "seed-explorer-simulation-save-v0.3",
        "seed": seed,
        "years": years,
        "mode": mode,
        "runId": str(body.get("runId") or run_id_for(seed, years)),
        "runDir": str(body.get("runDir") or ""),
        "currentQuarterIndex": max(0, current_index),
        "currentLabel": str(body.get("currentLabel") or ""),
        "contractSignatures": contract_signatures,
        "contractAffairsContractId": str(body.get("contractAffairsContractId") or "DUTY_FREE_MAIN"),
        "playerActions": player_actions,
        "savedAtUnix": round(now, 3),
        "savedAt": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now)),
        "note": "Seed-bound dynamic-test save. Stores the current quarter and player action journal; server-generated quarterly results are rebuilt and are not copied into the save.",
    }
    write_json(sim_save_path(seed, years), payload)
    return payload


def write_player_simulation_configs(
    run_dir: Path,
    player_actions: list[dict[str, Any]],
    *,
    simulation_dir_name: str,
    operations_config_path: Path,
    finance_config_path: Path,
    read_config_json: Callable[[Path], dict[str, Any]],
    player_project_events: Callable[[list[dict[str, Any]]], dict[str, list[dict[str, Any]]]],
    player_general_loans: Callable[[list[dict[str, Any]]], list[dict[str, Any]]],
    write_json: Callable[[Path, dict[str, Any]], None],
) -> tuple[Path, Path]:
    config_dir = run_dir / simulation_dir_name / "configs"
    operations_config = read_config_json(operations_config_path)
    operations_config["config_version"] = f"{operations_config.get('config_version', 'beijing-operations')}-simulate-default"
    operations_config["simulation_mode"] = "simulate_default"
    operations_config["simulation_design_note"] = (
        "Player-operation sandbox: commercial signatures and slot-level project starts are replayed "
        "from the seed-bound player action journal."
    )
    project_events = player_project_events(player_actions)
    operations_config["facility_renovation_events"] = project_events["facility_renovation_events"]
    operations_config["facility_construction_events"] = project_events["facility_construction_events"]
    operations_config["facility_rebuild_events"] = project_events["facility_rebuild_events"]
    operations_config["player_contract_actions"] = player_actions

    finance_config = read_config_json(finance_config_path)
    finance_config["config_version"] = f"{finance_config.get('config_version', 'beijing-finance')}-simulate-default"
    finance_config["simulation_mode"] = "simulate_default"
    finance_config["simulation_design_note"] = "Player-operation sandbox: loans are replayed from the seed-bound player action journal."
    finance_config["general_loans"] = player_general_loans(player_actions)

    generated_operations_path = config_dir / "beijing_airport_system_quarterly_operations_simulate_default.json"
    generated_finance_path = config_dir / "beijing_airport_group_financial_state_simulate_default.json"
    write_json(generated_operations_path, operations_config)
    write_json(generated_finance_path, finance_config)
    return generated_operations_path, generated_finance_path


def run_layer_command(
    cmd: list[str],
    label: str,
    *,
    root_dir: Path,
    run_process: Callable[..., Any] = subprocess.run,
) -> None:
    result = run_process(
        cmd,
        cwd=str(root_dir),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=180,
    )
    if result.returncode != 0:
        output_tail = (result.stdout + "\n" + result.stderr)[-6000:]
        raise RuntimeError(f"{label} failed with code {result.returncode}\n{output_tail}")


def dependency_digest(paths: Iterable[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted((Path(path) for path in paths), key=lambda item: item.name):
        digest.update(path.name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def simulation_fingerprint(
    player_actions: list[dict[str, Any]],
    paths: SimulationPaths,
    simulation_dependency_files: Iterable[Path],
) -> str:
    fingerprint_source = {
        "player_actions": player_actions,
        "operations_config": hashlib.sha256(paths.operations_config.read_bytes()).hexdigest(),
        "finance_config": hashlib.sha256(paths.finance_config.read_bytes()).hexdigest(),
        "operations_script": hashlib.sha256(paths.quarterly_operations_script.read_bytes()).hexdigest(),
        "finance_script": hashlib.sha256(paths.financial_state_script.read_bytes()).hexdigest(),
        "simulation_server": dependency_digest(simulation_dependency_files),
    }
    return hashlib.sha256(
        json.dumps(fingerprint_source, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def ensure_player_simulation_outputs(
    run_dir: Path,
    player_actions: list[dict[str, Any]],
    force: bool,
    *,
    paths: SimulationPaths,
    simulation_dependency_files: Iterable[Path],
    read_json: Callable[[Path], dict[str, Any]],
    write_json: Callable[[Path, dict[str, Any]], None],
    ensure_inside: Callable[[Path, Path], Path],
    remove_tree: Callable[[Path], None],
    write_default_city_demand_csv: Callable[[Path], Path],
    write_player_simulation_configs: Callable[[Path, list[dict[str, Any]]], tuple[Path, Path]],
    run_layer_command: Callable[[list[str], str], None],
    executable: str,
) -> bool:
    simulation_dir = run_dir / paths.simulation_dir_name
    operations_path = run_dir / paths.operations_relative_csv
    financial_path = run_dir / paths.financial_relative_csv
    manifest_path = simulation_dir / "action_cache_manifest.json"
    fingerprint = simulation_fingerprint(player_actions, paths, simulation_dependency_files)
    if not force and operations_path.exists() and financial_path.exists() and manifest_path.exists():
        try:
            manifest = read_json(manifest_path)
            if manifest.get("fingerprint") == fingerprint:
                return True
        except (OSError, ValueError, json.JSONDecodeError):
            pass

    # Player actions can alter any later quarter. Rebuild only when their
    # journal or a simulation dependency changed; quarter browsing is cached.
    if simulation_dir.exists():
        remove_tree(ensure_inside(run_dir, simulation_dir))

    city_demand_path = write_default_city_demand_csv(run_dir)
    generated_operations_config, generated_finance_config = write_player_simulation_configs(run_dir, player_actions)
    operations_output_dir = run_dir / paths.simulation_dir_name / "city_airport_quarterly_operations"
    financial_output_dir = run_dir / paths.simulation_dir_name / "city_airport_financial_state"

    run_layer_command(
        [
            executable,
            str(paths.quarterly_operations_script),
            "--market",
            "beijing_airport_system",
            "--city-demand-csv",
            str(city_demand_path),
            "--config",
            str(generated_operations_config),
            "--output-dir",
            str(operations_output_dir),
        ],
        "default simulation quarterly operations",
    )
    run_layer_command(
        [
            executable,
            str(paths.financial_state_script),
            "--market",
            "beijing_airport_system",
            "--quarterly-operations-csv",
            str(operations_path),
            "--config",
            str(generated_finance_config),
            "--output-dir",
            str(financial_output_dir),
        ],
        "default simulation financial state",
    )
    write_json(manifest_path, {"fingerprint": fingerprint})
    return False


def player_contract_previews(
    quarters: list[dict[str, Any]],
    active_index: int,
    *,
    as_float: Callable[[Any], float],
) -> dict[str, dict[str, Any]]:
    """Expose only the next-term card when a contract has entered its talk window."""
    definitions = {
        "DUTY_FREE_MAIN": {
            "cycle": "dutyFreeContractCycle",
            "status": "dutyFreeContractStatus",
            "type": "dutyFreeContractType",
            "share": "dutyFreeRevenueSharePct",
            "coverage": "dutyFreeMinimumGuaranteeCoveragePct",
            "guarantee": "dutyFreeMinimumGuarantee",
            "forecastQuarterSales": "dutyFreeContractForecastQuarterSales",
            "forecastAnnualSales": "dutyFreeContractForecastAnnualSales",
            "historyYearsUsed": "dutyFreeContractHistoryYearsUsed",
            "trendMultiplier": "dutyFreeContractTrendMultiplier",
            "macroRiskDiscountMultiplier": "dutyFreeContractMacroRiskDiscountMultiplier",
            "bargainingPowerMultiplier": "dutyFreeContractBargainingPowerMultiplier",
        },
        "LUXURY_RETAIL_MAIN": {
            "cycle": "luxuryContractCycle",
            "status": "luxuryContractStatus",
            "type": "luxuryContractType",
            "share": "luxuryRevenueSharePct",
            "coverage": "luxuryMinimumGuaranteeCoveragePct",
            "guarantee": "luxuryMinimumGuarantee",
            "forecastQuarterSales": "luxuryContractForecastQuarterSales",
            "forecastAnnualSales": "luxuryContractForecastAnnualSales",
            "historyYearsUsed": "luxuryContractHistoryYearsUsed",
            "trendMultiplier": "luxuryContractTrendMultiplier",
            "macroRiskDiscountMultiplier": "luxuryContractMacroRiskDiscountMultiplier",
            "bargainingPowerMultiplier": "luxuryContractBargainingPowerMultiplier",
        },
    }
    if active_index < 0 or active_index >= len(quarters):
        return {}
    previews: dict[str, dict[str, Any]] = {}
    for contract_id, fields in definitions.items():
        current = quarters[active_index]
        current_ops = current.get("operations", {})
        cycle_id = str(current_ops.get(fields["cycle"]) or "")
        if not cycle_id:
            continue
        cycle_indices = [
            index
            for index, quarter in enumerate(quarters)
            if str(quarter.get("operations", {}).get(fields["cycle"]) or "") == cycle_id
        ]
        if not cycle_indices:
            continue
        cycle_end_index = max(cycle_indices)
        remaining = cycle_end_index - active_index + 1
        if remaining < 1 or remaining > 4:
            continue
        next_quarter = next(
            (
                quarter
                for quarter in quarters[cycle_end_index + 1 :]
                if str(quarter.get("operations", {}).get(fields["cycle"]) or "") not in {"", cycle_id}
            ),
            None,
        )
        if not next_quarter:
            continue
        ops = next_quarter.get("operations", {})
        previews[contract_id] = {
            "currentCycleEndIndex": cycle_end_index,
            "remainingQuarters": remaining,
            "nextTerm": {
                "cycleId": str(ops.get(fields["cycle"]) or ""),
                "status": str(ops.get(fields["status"]) or ""),
                "type": str(ops.get(fields["type"]) or ""),
                "sharePct": as_float(ops.get(fields["share"])),
                "coveragePct": as_float(ops.get(fields["coverage"])),
                "guarantee": as_float(ops.get(fields["guarantee"])),
                "forecastQuarterSales": as_float(ops.get(fields["forecastQuarterSales"])),
                "forecastAnnualSales": as_float(ops.get(fields["forecastAnnualSales"])),
                "historyYearsUsed": as_float(ops.get(fields["historyYearsUsed"])),
                "trendMultiplier": as_float(ops.get(fields["trendMultiplier"])),
                "macroRiskDiscountMultiplier": as_float(ops.get(fields["macroRiskDiscountMultiplier"])),
                "bargainingPowerMultiplier": as_float(ops.get(fields["bargainingPowerMultiplier"])),
                "cycleStartYear": as_float(
                    ops.get("dutyFreeContractCycleStartYear")
                    if contract_id == "DUTY_FREE_MAIN"
                    else ops.get("luxuryContractCycleStartYear")
                ),
                "cycleEndYear": as_float(
                    ops.get("dutyFreeContractCycleEndYear")
                    if contract_id == "DUTY_FREE_MAIN"
                    else ops.get("luxuryContractCycleEndYear")
                ),
            },
        }
    return previews


def build_player_response(
    payload: dict[str, Any],
    clean_actions: list[dict[str, Any]],
    current_quarter_index: int | None,
    *,
    player_slot_names: Callable[[list[dict[str, Any]]], dict[str, str]],
    project_catalog: Callable[[], list[dict[str, Any]]],
    financing_products: dict[str, Any],
    financing_policy: dict[str, Any],
    player_contract_previews: Callable[[list[dict[str, Any]], int], dict[str, dict[str, Any]]],
) -> dict[str, Any]:
    all_quarters = payload.get("quarters", [])
    player_start_index = int(payload.get("playerStartIndex", 0))
    requested_index = player_start_index if current_quarter_index is None else int(current_quarter_index)
    active_index = min(max(player_start_index, requested_index), max(player_start_index, len(all_quarters) - 1))
    visible_quarters = all_quarters[: active_index + 1]
    payload.update(
        {
            "quarters": visible_quarters,
            "allQuarters": all_quarters,
            "periodCount": len(visible_quarters),
            "worldPeriodCount": len(all_quarters),
            "worldFinalLabel": all_quarters[-1]["label"] if all_quarters else "",
            "finalLabel": visible_quarters[-1]["label"] if visible_quarters else "",
            "currentQuarterIndex": active_index,
            "playerActions": clean_actions,
            "actionCount": len(clean_actions),
            "slotNames": player_slot_names(clean_actions),
            "projectCatalog": project_catalog(),
            "financingProducts": financing_products,
            "financingPolicy": financing_policy,
            "contractPreviews": player_contract_previews(all_quarters, active_index),
            "operationSource": "simulation_default/server_action_journal",
        }
    )
    return payload


def load_player_simulation_locked(
    seed: int,
    years: int,
    force: bool,
    player_actions: list[dict[str, Any]],
    current_quarter_index: int | None,
    *,
    run_root: Path,
    run_seed: Callable[[int, int, bool], dict[str, Any]],
    clean_player_actions: Callable[[Any], list[dict[str, Any]]],
    ensure_player_simulation_outputs: Callable[[Path, list[dict[str, Any]], bool], bool],
    aggregate_beijing_operations: Callable[..., dict[str, Any]],
    simulation_operations_relative_csv: Path,
    simulation_financial_relative_csv: Path,
    player_slot_names: Callable[[list[dict[str, Any]]], dict[str, str]],
    project_catalog: Callable[[], list[dict[str, Any]]],
    financing_products: dict[str, Any],
    load_financing_policy: Callable[[], dict[str, Any]],
    player_contract_previews: Callable[[list[dict[str, Any]], int], dict[str, dict[str, Any]]],
    build_player_response: Callable[..., dict[str, Any]],
) -> dict[str, Any]:
    """Rebuild a player run and expose only the history through the active quarter."""
    run_payload = run_seed(seed, years, force)
    run_dir = run_root / str(run_payload["runId"])
    clean_actions = clean_player_actions(player_actions)
    simulation_cached = ensure_player_simulation_outputs(run_dir, clean_actions, force)
    payload = aggregate_beijing_operations(
        run_dir,
        seed,
        years,
        bool(run_payload.get("cached")) and simulation_cached,
        "simulate_default",
        simulation_operations_relative_csv,
        simulation_financial_relative_csv,
    )
    return build_player_response(
        payload,
        clean_actions,
        current_quarter_index,
        player_slot_names=player_slot_names,
        project_catalog=project_catalog,
        financing_products=financing_products,
        financing_policy=load_financing_policy(),
        player_contract_previews=player_contract_previews,
    )


def load_player_simulation(
    seed: int,
    years: int,
    force: bool,
    player_actions: list[dict[str, Any]],
    current_quarter_index: int | None,
    *,
    minimum_years: int,
    clean_years: Callable[[Any], int],
    run_id_for: Callable[[int, int], str],
    lock_for_run: Callable[[str], AbstractContextManager[Any]],
    load_locked: Callable[[int, int, bool, list[dict[str, Any]], int | None], dict[str, Any]],
) -> dict[str, Any]:
    # Short runs remain useful for fast inspection, but a playable operations
    # world always uses the full long-horizon contract.
    years = max(minimum_years, clean_years(years))
    with lock_for_run(run_id_for(seed, years)):
        return load_locked(seed, years, force, player_actions, current_quarter_index)
