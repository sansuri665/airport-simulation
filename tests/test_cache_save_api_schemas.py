from __future__ import annotations

import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest import mock

from airport_sim.schema_validation import SchemaValidationError, load_schema_registry, validate_named_schema
from airport_sim.server import api_contract, player_service, run_cache
from airport_sim.server import app as local_ui


ROOT_DIR = Path(__file__).resolve().parents[1]
SCHEMA_ROOT = ROOT_DIR / "schemas"


class QuietAirportHandler(local_ui.SeedExplorerHandler):
    def log_message(self, format: str, *args: object) -> None:
        return


def simulation_save() -> dict[str, object]:
    return {
        "schemaVersion": "seed-explorer-simulation-save-v0.3",
        "seed": 7,
        "years": 12,
        "mode": "simulate_default",
        "runId": "seed_7_years_12",
        "runDir": "output/seed_explorer_runs/seed_7_years_12",
        "currentQuarterIndex": 4,
        "currentLabel": "2026 Q1",
        "contractSignatures": {"DUTY_FREE_MAIN:cycle-1": {"share": 20}},
        "contractAffairsContractId": "DUTY_FREE_MAIN",
        "playerActions": [{"id": "rename-1", "type": "rename_slot"}],
        "savedAtUnix": 100.125,
        "savedAt": "1970-01-01 08:01:40",
        "note": (
            "Seed-bound dynamic-test save. Stores the current quarter and player action journal; "
            "server-generated quarterly results are rebuilt and are not copied into the save."
        ),
    }


def save_summary(*, occupied: bool) -> dict[str, object]:
    summary: dict[str, object] = {
        "label": "当前 seed 存档",
        "occupied": occupied,
        "seed": 7,
        "years": 12,
        "runId": "seed_7_years_12",
        "savePath": "saves/seed_explorer/seed_7_years_12/dynamic_test_save.json",
    }
    if occupied:
        summary.update(
            {
                "mode": "simulate_default",
                "currentQuarterIndex": 4,
                "currentLabel": "2026 Q1",
                "savedAt": "1970-01-01 08:01:40",
                "savedAtUnix": 100.125,
                "contractSignatureCount": 1,
                "playerActionCount": 1,
                "projectActionCount": 0,
                "slotRenameCount": 1,
                "operationOverrideQuarterCount": 0,
            }
        )
    return summary


def cache_entries(root: Path) -> list[dict[str, object]]:
    valid_dir = root / "seed_7_years_12"
    stale_dir = root / "legacy_unknown"
    valid_dir.mkdir(parents=True)
    stale_dir.mkdir()
    valid = run_cache.cached_run_entry(
        valid_dir,
        "fingerprint",
        load_cached=lambda path, expected: {
            "seed": 7,
            "years": 12,
            "cityCount": 47,
            "startYear": 2025,
            "finalYear": 2036,
            "generatedAt": "2026-07-18 12:00:00",
        },
        parse_run_id=local_ui.parse_run_id,
        operations_relative_csv=Path("simulation_default/operations.csv"),
    )
    stale = run_cache.cached_run_entry(
        stale_dir,
        "fingerprint",
        load_cached=lambda path, expected: None,
        parse_run_id=local_ui.parse_run_id,
        operations_relative_csv=Path("simulation_default/operations.csv"),
    )
    return [valid, stale]


class CacheSaveApiSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = load_schema_registry(SCHEMA_ROOT)
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), QuietAirportHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        host, port = cls.server.server_address
        cls.base_url = f"http://{host}:{port}"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=3)

    def get_json(self, path: str) -> dict[str, object]:
        with urllib.request.urlopen(f"{self.base_url}{path}", timeout=5) as response:
            self.assertEqual(200, response.status)
            return json.loads(response.read().decode("utf-8"))

    def post_json(self, path: str, payload: dict[str, object]) -> dict[str, object]:
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            self.assertEqual(200, response.status)
            return json.loads(response.read().decode("utf-8"))

    def test_catalog_registers_current_cache_and_save_schemas(self) -> None:
        expected_schemas = {
            "cachedRuns": "cached-runs-response.schema.json",
            "simulationSave": "simulation-save.schema.json",
            "simSave": "sim-save-response.schema.json",
        }
        for schema_id, filename in expected_schemas.items():
            self.assertEqual(filename, api_contract.SCHEMA_FILES[schema_id])
            self.assertIn(filename, self.registry)

        expected_endpoints = {
            "GET /api/cached-runs": "/schemas/cached-runs-response.schema.json",
            "POST /api/sim-save": "/schemas/sim-save-response.schema.json",
        }
        for endpoint, schema_url in expected_endpoints.items():
            self.assertEqual(schema_url, api_contract.ENDPOINT_SCHEMAS[endpoint])

    def test_direct_cache_entry_serialization_covers_valid_and_nullable_stale_values(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            entries = cache_entries(Path(temporary_dir))

        payload = local_ui.api_envelope(
            {
                "ok": True,
                "runRoot": "output/seed_explorer_runs",
                "saveRoot": "saves/seed_explorer",
                "maxCachedRuns": 2,
                "cacheFingerprintVersion": local_ui.CACHE_FINGERPRINT_VERSION,
                "runs": entries,
            }
        )
        validate_named_schema(payload, "cached-runs-response.schema.json", self.registry)
        self.assertEqual("valid", entries[0]["cacheStatus"])
        self.assertIsNone(entries[1]["seed"])
        self.assertIsNone(entries[1]["years"])

    def test_direct_save_serialization_matches_persisted_save_schema_without_writing(self) -> None:
        captured: list[tuple[Path, dict[str, object]]] = []
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            run_root = root / "runs"
            (run_root / "seed_7_years_12").mkdir(parents=True)
            payload = player_service.save_sim_save(
                {
                    "seed": 7,
                    "years": 12,
                    "mode": "simulate_default",
                    "runDir": "output/seed_explorer_runs/seed_7_years_12",
                    "currentQuarterIndex": 4,
                    "currentLabel": "2026 Q1",
                    "contractSignatures": {"contract": {"share": 20}},
                    "playerActions": [{"id": "rename-1", "type": "rename_slot"}],
                },
                clean_seed=local_ui.clean_seed,
                clean_years=local_ui.clean_years,
                clean_operation_mode=local_ui.clean_operation_mode,
                as_float=local_ui.as_float,
                clean_player_actions=lambda actions: list(actions),
                run_root=run_root,
                run_id_for=local_ui.run_id_for,
                sim_save_path=lambda seed, years: root / "would-write.json",
                write_json=lambda path, value: captured.append((path, value)),
                clock=lambda: 100.125,
            )

        validate_named_schema(payload, "simulation-save.schema.json", self.registry)
        self.assertEqual([(Path(temporary_dir) / "would-write.json", payload)], captured)

    def test_all_current_sim_save_response_shapes_match_one_schema(self) -> None:
        saved = simulation_save()
        occupied = save_summary(occupied=True)
        empty = save_summary(occupied=False)
        responses = (
            {"ok": True, "save": saved, "summary": occupied},
            {"ok": True, "save": None, "summary": empty},
            {"ok": True, "summary": empty},
        )
        for response in responses:
            with self.subTest(keys=sorted(response)):
                validate_named_schema(
                    local_ui.api_envelope(response),
                    "sim-save-response.schema.json",
                    self.registry,
                )

    def test_real_cached_runs_route_response_matches_schema(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            entries = cache_entries(Path(temporary_dir))
            with (
                mock.patch.object(local_ui, "list_cached_runs", return_value=entries),
                mock.patch.object(local_ui, "cache_retention_policy", return_value={"maxCachedRuns": 2}),
            ):
                payload = self.get_json("/api/cached-runs")

        validate_named_schema(payload, "cached-runs-response.schema.json", self.registry)

    def test_real_sim_save_route_covers_status_save_load_and_clear(self) -> None:
        saved = simulation_save()
        occupied = save_summary(occupied=True)
        empty = save_summary(occupied=False)
        responses: list[dict[str, object]] = []

        with (
            mock.patch.object(local_ui, "read_sim_save", side_effect=[None, saved]) as read,
            mock.patch.object(local_ui, "save_sim_save", return_value=saved) as save,
            mock.patch.object(local_ui, "clear_sim_save") as clear,
            mock.patch.object(
                local_ui,
                "sim_save_summary",
                side_effect=[empty, occupied, occupied, empty],
            ),
        ):
            responses.append(self.post_json("/api/sim-save", {"action": "status", "seed": 7, "years": 12}))
            responses.append(self.post_json("/api/sim-save", {"action": "save", "seed": 7, "years": 12}))
            responses.append(self.post_json("/api/sim-save", {"action": "load", "seed": 7, "years": 12}))
            responses.append(self.post_json("/api/sim-save", {"action": "clear", "seed": 7, "years": 12}))

        for payload in responses:
            validate_named_schema(payload, "sim-save-response.schema.json", self.registry)
        self.assertEqual(2, read.call_count)
        save.assert_called_once()
        clear.assert_called_once_with(7, 12)

    def test_retired_save_routes_return_not_found(self) -> None:
        with self.assertRaises(urllib.error.HTTPError) as get_context:
            urllib.request.urlopen(f"{self.base_url}/api/sim-save-slots", timeout=5)
        self.assertEqual(404, get_context.exception.code)

        request = urllib.request.Request(
            f"{self.base_url}/api/sim-save-slot",
            data=b'{}',
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with self.assertRaises(urllib.error.HTTPError) as post_context:
            urllib.request.urlopen(request, timeout=5)
        self.assertEqual(404, post_context.exception.code)

    def test_schemas_reject_missing_contract_fields_and_wrong_types(self) -> None:
        invalid_cache = local_ui.api_envelope(
            {
                "ok": True,
                "runRoot": "output/seed_explorer_runs",
                "saveRoot": "saves/seed_explorer",
                "maxCachedRuns": 2,
                "cacheFingerprintVersion": local_ui.CACHE_FINGERPRINT_VERSION,
                "runs": [{"runId": "seed_7_years_12"}],
            }
        )
        invalid_save = simulation_save()
        invalid_save["playerActions"] = "not-an-array"
        invalid_response = local_ui.api_envelope({"ok": True, "save": None})
        invalid_nested_response = local_ui.api_envelope(
            {
                "ok": True,
                "save": invalid_save,
                "summary": save_summary(occupied=True),
            }
        )
        cases = (
            (invalid_cache, "cached-runs-response.schema.json"),
            (invalid_save, "simulation-save.schema.json"),
            (invalid_response, "sim-save-response.schema.json"),
            (invalid_nested_response, "sim-save-response.schema.json"),
        )
        for payload, schema_name in cases:
            with self.subTest(schema=schema_name):
                with self.assertRaises(SchemaValidationError):
                    validate_named_schema(payload, schema_name, self.registry)


if __name__ == "__main__":
    unittest.main()
