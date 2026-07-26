from __future__ import annotations

import csv
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path

from airport_sim.schema_validation import load_schema_registry, validate_named_schema
from airport_sim.server import app as local_ui
from airport_sim.server import global_viewer, serializers, storage
from macro_layers.asset_accounting_v04 import initial_contract_row


ROOT_DIR = Path(__file__).resolve().parents[1]
SCHEMA_REGISTRY = load_schema_registry(ROOT_DIR / "schemas")


def write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def years_rows(seed: int, **extra: object) -> list[dict[str, object]]:
    return [
        {"year_index": index, "year": year, "seed": seed, **extra}
        for index, year in ((0, 2025), (5, 2030))
    ]


@contextmanager
def unlocked(_run_id: str):
    yield


class GlobalViewerContextServiceTests(unittest.TestCase):
    def fixture(self, root: Path, *, seed: int = 7) -> tuple[Path, Path]:
        run_root = root / "output" / "seed_explorer_runs"
        run_dir = run_root / "seed_7_years_5"
        write_rows(
            run_dir / global_viewer.GLOBAL_RELATIVE_CSV,
            years_rows(
                seed,
                global_gdp_trillion_usd=100.0,
                scenario_risk_id="",
                branch_risk_primary_id="",
            ),
        )
        write_rows(
            run_dir / global_viewer.RECONCILED_RELATIVE_CSV,
            years_rows(seed, region_id="china_mainland", region_name="中国大陆"),
        )
        write_rows(
            run_dir / global_viewer.DIAGNOSTIC_RELATIVE_CSV,
            years_rows(seed, reconciliation_quality="balanced"),
        )
        for region_id in global_viewer.REGION_ORDER:
            write_rows(
                run_dir
                / "baseline"
                / "regional_macro"
                / region_id
                / f"{region_id}_regional_macro_seed_sweep.csv",
                years_rows(
                    seed,
                    region_id=region_id,
                    region_name=f"区域 {region_id}",
                    regional_gdp_index=100.0,
                    **initial_contract_row("regional_asset"),
                    **initial_contract_row("regional_signal"),
                    asset_accounting_contract_version="asset-accounting-v0.4-contract-v1",
                    regional_asset_v04_param_version="regional-asset-accounting-v0.4",
                ),
            )
            write_rows(
                run_dir
                / "baseline"
                / "regional_aviation_demand"
                / region_id
                / f"{region_id}_aviation_demand_seed_sweep.csv",
                years_rows(
                    seed,
                    region_id=region_id,
                    regional_air_demand_index=100.0,
                    regional_aviation_demand_param_version="regional-aviation-demand-layer-v0.4",
                    input_asset_market_impulse_index=50.0,
                    input_household_wealth_consumption_impulse=0.0,
                    input_real_disposable_income_growth_pct=0.0,
                    premium_propensity_raw_index=100.0,
                    premium_propensity_final_index=100.0,
                    demand_total_asset_market_contribution_pp=0.0,
                    demand_total_household_wealth_contribution_pp=0.0,
                    demand_total_cash_income_contribution_pp=0.0,
                    demand_total_credit_confidence_contribution_pp=0.0,
                    demand_total_fare_cost_contribution_pp=0.0,
                ),
            )
            write_rows(
                run_dir
                / "baseline"
                / "regional_air_capacity_supply"
                / region_id
                / f"{region_id}_air_capacity_supply_seed_sweep.csv",
                years_rows(seed, region_id=region_id, regional_air_capacity_index=100.0),
            )
        return run_root, run_dir

    def workspace(self, status: str = "ready") -> dict[str, object]:
        return {
            "workspaceRevision": 9,
            "slots": [
                {
                    "slotId": "seed_7_years_5",
                    "seed": 7,
                    "years": 5,
                    "cacheStatus": status,
                    "cacheRunId": "seed_7_years_5",
                }
            ],
        }

    def common(self, run_root: Path) -> dict[str, object]:
        return {
            "workspace_payload": self.workspace,
            "run_root": run_root,
            "run_id_for": local_ui.run_id_for,
            "ensure_inside": storage.ensure_inside,
            "lock_for_run": unlocked,
            "read_csv": storage.read_csv,
            "decode_rows": serializers.decode_viewer_csv_rows,
        }

    def test_ready_cache_serves_core_and_region_without_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            run_root, run_dir = self.fixture(Path(temporary_dir))
            before = {
                path.relative_to(run_dir).as_posix(): path.read_bytes()
                for path in run_dir.rglob("*")
                if path.is_file()
            }
            common = self.common(run_root)
            index = global_viewer.index_payload(
                7,
                5,
                optional_scenario_fields=serializers.GLOBAL_VIEWER_OPTIONAL_SCENARIO_FIELDS,
                serialize_core=serializers.serialize_global_viewer_core,
                serialize_dataset=serializers.serialize_global_viewer_dataset,
                **common,
            )
            region = global_viewer.region_payload(
                7,
                5,
                "china_mainland",
                serialize_region=serializers.serialize_global_viewer_region,
                **common,
            )
            after = {
                path.relative_to(run_dir).as_posix(): path.read_bytes()
                for path in run_dir.rglob("*")
                if path.is_file()
            }

        self.assertEqual(before, after)
        self.assertEqual("seed_cache", index["context"]["source"])
        self.assertEqual(14, len(index["index"]["regions"]))
        self.assertEqual(2, len(index["core"]["globalRows"]))
        self.assertNotIn("scenario_risk_id", index["core"]["globalRows"][0])
        self.assertEqual("", index["core"]["globalRows"][0]["branch_risk_primary_id"])
        self.assertEqual("china_mainland", region["chunk"]["regionId"])
        self.assertEqual(2, len(region["chunk"]["aviationDemandRows"]))
        validate_named_schema(
            local_ui.api_envelope(index),
            "global-viewer-context-index-response.schema.json",
            SCHEMA_REGISTRY,
        )
        validate_named_schema(
            local_ui.api_envelope(region),
            "global-viewer-context-region-response.schema.json",
            SCHEMA_REGISTRY,
        )

    def test_stale_missing_unsafe_and_mixed_seed_contexts_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            run_root, run_dir = self.fixture(root)
            common = self.common(run_root)
            with self.assertRaises(global_viewer.GlobalViewerContextUnavailableError):
                global_viewer.index_payload(
                    7,
                    5,
                    workspace_payload=lambda: self.workspace("stale"),
                    optional_scenario_fields=serializers.GLOBAL_VIEWER_OPTIONAL_SCENARIO_FIELDS,
                    serialize_core=serializers.serialize_global_viewer_core,
                    serialize_dataset=serializers.serialize_global_viewer_dataset,
                    **{key: value for key, value in common.items() if key != "workspace_payload"},
                )
            with self.assertRaises(FileNotFoundError):
                global_viewer.region_payload(
                    7,
                    5,
                    "../china_mainland",
                    serialize_region=serializers.serialize_global_viewer_region,
                    **common,
                )
            write_rows(
                run_dir / global_viewer.GLOBAL_RELATIVE_CSV,
                years_rows(8, global_gdp_trillion_usd=100.0),
            )
            with self.assertRaises(global_viewer.GlobalViewerContextUnavailableError):
                global_viewer.index_payload(
                    7,
                    5,
                    optional_scenario_fields=serializers.GLOBAL_VIEWER_OPTIONAL_SCENARIO_FIELDS,
                    serialize_core=serializers.serialize_global_viewer_core,
                    serialize_dataset=serializers.serialize_global_viewer_dataset,
                    **common,
                )


if __name__ == "__main__":
    unittest.main()
