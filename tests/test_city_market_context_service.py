from __future__ import annotations

import csv
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path

from airport_sim.schema_validation import load_schema_registry, validate_named_schema
from airport_sim.server import app as local_ui
from airport_sim.server import city_market_viewer, serializers, storage


ROOT_DIR = Path(__file__).resolve().parents[1]
SCHEMA_REGISTRY = load_schema_registry(ROOT_DIR / "schemas")


def write_market_csv(
    path: Path,
    *,
    seed: int = 7,
    start_year: int = 2025,
    final_year: int = 2030,
    market_id: str = "beijing_airport_system",
    name: str = "北京",
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "city_airport_market_id",
        "city_name",
        "region_id",
        "region_name",
        "market_tier",
        "market_type",
        "year",
        "seed",
        "city_potential_passengers_million",
        "city_airline_supply_passengers_million",
        "city_airline_supply_fulfillment_pct",
    ]
    rows = [
        {
            "city_airport_market_id": market_id,
            "city_name": name,
            "region_id": "china_mainland",
            "region_name": "中国大陆",
            "market_tier": "global_hub",
            "market_type": "test",
            "year": year,
            "seed": seed,
            "city_potential_passengers_million": potential,
            "city_airline_supply_passengers_million": supply,
            "city_airline_supply_fulfillment_pct": supply / potential * 100,
        }
        for year, potential, supply in (
            (start_year, 100.0, 95.0),
            (final_year, 110.0, 108.0),
        )
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


@contextmanager
def unlocked(_run_id: str):
    yield


class CityMarketContextServiceTests(unittest.TestCase):
    def fixture(self, root: Path) -> tuple[Path, Path]:
        run_root = root / "output" / "seed_explorer_runs"
        run_dir = run_root / "seed_7_years_5"
        market_dir = run_dir / city_market_viewer.CITY_MARKET_RELATIVE_DIR
        write_market_csv(
            market_dir / "beijing_airport_system_city_airport_demand_seed_sweep.csv"
        )
        write_market_csv(
            market_dir / "shanghai_airport_system_city_airport_demand_seed_sweep.csv",
            market_id="shanghai_airport_system",
            name="上海",
        )
        return run_root, run_dir

    def workspace(self, status: str = "ready") -> dict[str, object]:
        return {
            "workspaceRevision": 4,
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

    def test_ready_cache_serves_context_bound_index_and_chunk_without_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            run_root, run_dir = self.fixture(root)
            before = {
                path.relative_to(run_dir).as_posix(): path.read_bytes()
                for path in run_dir.rglob("*")
                if path.is_file()
            }
            common = {
                "workspace_payload": self.workspace,
                "run_root": run_root,
                "run_id_for": local_ui.run_id_for,
                "ensure_inside": storage.ensure_inside,
                "lock_for_run": unlocked,
                "read_csv": storage.read_csv,
            }
            index = city_market_viewer.index_payload(
                7,
                5,
                serialize_dataset=serializers.serialize_city_market_viewer_dataset,
                **common,
            )
            chunk = city_market_viewer.chunk_payload(
                7,
                5,
                "beijing_airport_system",
                serialize_rows=serializers.serialize_city_market_viewer_rows,
                **common,
            )
            after = {
                path.relative_to(run_dir).as_posix(): path.read_bytes()
                for path in run_dir.rglob("*")
                if path.is_file()
            }

        self.assertEqual(before, after)
        self.assertEqual("seed_cache", index["context"]["source"])
        self.assertEqual("seed_7_years_5", index["context"]["slotId"])
        self.assertEqual(2, index["index"]["cityCount"])
        self.assertEqual("beijing_airport_system", chunk["chunk"]["marketId"])
        final = chunk["chunk"]["city"]["points"][-1]
        self.assertEqual(108.0, final["serviceable"])
        self.assertNotIn("served", final)
        validate_named_schema(
            local_ui.api_envelope(index),
            "city-market-context-index-response.schema.json",
            SCHEMA_REGISTRY,
        )
        validate_named_schema(
            local_ui.api_envelope(chunk),
            "city-market-context-chunk-response.schema.json",
            SCHEMA_REGISTRY,
        )

    def test_missing_stale_and_unsafe_contexts_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            run_root, _ = self.fixture(root)
            common = {
                "run_root": run_root,
                "run_id_for": local_ui.run_id_for,
                "ensure_inside": storage.ensure_inside,
                "lock_for_run": unlocked,
                "read_csv": storage.read_csv,
            }
            with self.assertRaises(city_market_viewer.CityMarketContextUnavailableError):
                city_market_viewer.index_payload(
                    7,
                    5,
                    workspace_payload=lambda: self.workspace("stale"),
                    serialize_dataset=serializers.serialize_city_market_viewer_dataset,
                    **common,
                )
            with self.assertRaises(FileNotFoundError):
                city_market_viewer.index_payload(
                    8,
                    5,
                    workspace_payload=lambda: self.workspace(),
                    serialize_dataset=serializers.serialize_city_market_viewer_dataset,
                    **common,
                )
            with self.assertRaises(ValueError):
                city_market_viewer.chunk_payload(
                    7,
                    5,
                    "../beijing",
                    workspace_payload=lambda: self.workspace(),
                    serialize_rows=serializers.serialize_city_market_viewer_rows,
                    **common,
                )
            market_dir = (
                run_root
                / "seed_7_years_5"
                / city_market_viewer.CITY_MARKET_RELATIVE_DIR
            )
            write_market_csv(
                market_dir / "shanghai_airport_system_city_airport_demand_seed_sweep.csv",
                seed=8,
                market_id="shanghai_airport_system",
                name="上海",
            )
            with self.assertRaises(city_market_viewer.CityMarketContextUnavailableError):
                city_market_viewer.index_payload(
                    7,
                    5,
                    workspace_payload=lambda: self.workspace(),
                    serialize_dataset=serializers.serialize_city_market_viewer_dataset,
                    **common,
                )


if __name__ == "__main__":
    unittest.main()
