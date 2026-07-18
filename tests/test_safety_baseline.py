from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock


ROOT_DIR = Path(__file__).resolve().parents[1]
MACRO_DIR = ROOT_DIR / "macro_layers"
SERVER_DIR = ROOT_DIR / "airport_sim" / "server"
if str(MACRO_DIR) not in sys.path:
    sys.path.insert(0, str(MACRO_DIR))

import macro_run_orchestrator_sim as orchestrator
from airport_sim.server import app as seed_explorer_server
import simulation_io
import simulation_utils
from simulation_utils import clamp as shared_clamp


def normalize_signed_zero(value: object) -> object:
    if isinstance(value, float) and value == 0.0:
        return 0.0
    if isinstance(value, dict):
        return {key: normalize_signed_zero(item) for key, item in value.items()}
    if isinstance(value, list):
        return [normalize_signed_zero(item) for item in value]
    return value


def serialized_rows_digest(rows: object) -> str:
    raw = json.dumps(
        rows,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def rows_digest(rows: list[dict[str, object]]) -> str:
    return serialized_rows_digest(normalize_signed_zero(rows))


def raw_rows_digest(rows: list[dict[str, object]]) -> str:
    return serialized_rows_digest(rows)


class FixedSeedCharacterizationTests(unittest.TestCase):
    """Protect the current numerical model before structural refactoring."""

    EXPECTED = {
        "global": (13, "c68446bfb269bbbbf1809c210c14dc9b5375708c8b78b2a0f54ef1b97008570b"),
        "reconciled": (182, "0f7cc109c94ff7460d5d23204ed4913cdb255ff6fbd380222a9a78cdc9623feb"),
        "aviation_china": (13, "2937efb00e477fda05ec25f1c088dbfab5b998c51c3e3002e802897577638969"),
        "supply_china": (13, "c65d63da0a55e2303a51d3a05f44668165eecf12f9ac2a4d2d11f4a9b41ba887"),
        "city_beijing": (13, "a27d58f756384a3ac66ceefddd54d5e46ef3e3c4cfc0c08d77004849c9c4dcc7"),
        "forecast_beijing": (361, "a38a80b0b00fc7bb6c832b05f4303b9aa7261d2fb5783ff20609fb13b9f68e7b"),
        "operations_beijing": (52, "749300a1e9b449e3a342b5b72b1804af1a97d173351c285087d80b446222a674"),
        "finance_beijing": (52, "b36baa4d427a65d39f067753349af5a39c3d7719f2dccc75f95b6349250f20fd"),
        "valuation_beijing": (32, "6f8d2c2855c52d1203ff0d0b68962a3fd54817f10b0f4cfd337ff43ff6ad11f0"),
    }
    CANONICAL_PYTHON_313_EXPECTED = {
        "global": (13, "bc8049043a8a3e05fd70c1d57d9419ecccdab5f5dce2997201e577b146350f4b"),
        "reconciled": (182, "58a32aa5e4880708d6ac20d7818880833111d95bcbe7431f260b08642801d432"),
        "aviation_china": (13, "d99ebde1fbf861304227889e48311b2496a82302921d05db900fd169d958e7fb"),
        "supply_china": (13, "dcca960c482f1266b7329bf2bc083a62818dbfd9062683271b40b8c93f777875"),
        "city_beijing": (13, "11f9767973c1060628dce7c83ed744edc6d803a77d10bc690cae9d90c7bcbc00"),
        "forecast_beijing": (361, "a38a80b0b00fc7bb6c832b05f4303b9aa7261d2fb5783ff20609fb13b9f68e7b"),
        "operations_beijing": (52, "749300a1e9b449e3a342b5b72b1804af1a97d173351c285087d80b446222a674"),
        "finance_beijing": (52, "5490edf7550563cc7c9536c8477ac45d618f583931eb14b4fccc931dcecd9afd"),
        "valuation_beijing": (32, "6f8d2c2855c52d1203ff0d0b68962a3fd54817f10b0f4cfd337ff43ff6ad11f0"),
    }

    @classmethod
    def setUpClass(cls) -> None:
        args = argparse.Namespace(
            years=12,
            start_year=2025,
            initial_gdp=100.0,
            volatility_scale=1.0,
            feedback_iterations=1,
        )
        seed = 20261324
        global_result = orchestrator.run_global_variant(seed, args, "baseline")
        regional = orchestrator.run_regional_and_reconciliation(seed, global_result["rows"])
        cls.parts = {
            "global": global_result["rows"],
            "reconciled": regional["reconciled_rows"],
            "aviation_china": regional["aviation_rows_by_region"]["china_mainland"],
            "supply_china": regional["supply_rows_by_region"]["china_mainland"],
            "city_beijing": regional["city_airport_rows_by_market"]["beijing_airport_system"],
            "forecast_beijing": regional["potential_passenger_forecast_rows_by_market"]["beijing_airport_system"],
            "operations_beijing": regional["quarterly_operations_rows_by_market"]["beijing_airport_system"],
            "finance_beijing": regional["financial_state_rows_by_market"]["beijing_airport_system"],
            "valuation_beijing": regional["valuation_forecast_rows_by_market"]["beijing_airport_system"],
        }

    def test_fixed_seed_numerical_digests(self) -> None:
        actual = {name: (len(rows), rows_digest(rows)) for name, rows in self.parts.items()}
        self.assertEqual(self.EXPECTED, actual)

    @unittest.skipUnless(sys.version_info[:2] == (3, 13), "canonical byte representation is Python 3.13")
    def test_python_313_canonical_float_representation(self) -> None:
        actual = {name: (len(rows), raw_rows_digest(rows)) for name, rows in self.parts.items()}
        self.assertEqual(self.CANONICAL_PYTHON_313_EXPECTED, actual)


class RuntimeSafetyTests(unittest.TestCase):
    def test_shared_global_io_preserves_encoding_and_field_order(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            csv_path = root / "nested" / "rows.csv"
            json_path = root / "nested" / "payload.json"
            simulation_io.write_csv(csv_path, [{"second": 2, "first": 1}], ["first", "second"])
            simulation_io.write_json(json_path, {"second": 2, "first": 1})

            csv_bytes = csv_path.read_bytes()
            json_bytes = json_path.read_bytes()

        self.assertFalse(csv_bytes.startswith(b"\xef\xbb\xbf"))
        self.assertEqual(["first,second", "1,2"], csv_bytes.decode("utf-8").splitlines())
        self.assertFalse(json_bytes.startswith(b"\xef\xbb\xbf"))
        self.assertFalse(json_bytes.endswith((b"\n", b"\r")))
        self.assertEqual(["second", "first"], list(json.loads(json_bytes.decode("utf-8"))))

    def test_shared_csv_variants_preserve_bom_and_extra_field_rules(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            bom_path = root / "bom.csv"
            utf8_path = root / "utf8.csv"
            extended_path = root / "extended.csv"
            simulation_io.write_csv_utf8_sig_ignore(
                bom_path,
                [{"a": 1, "ignored": 2}],
                ["a"],
            )
            simulation_io.write_csv_utf8_ignore(
                utf8_path,
                [{"a": 1, "ignored": 2}],
                ["a"],
            )
            simulation_io.write_csv_utf8_sig_with_extra_fields(
                extended_path,
                [{"a": 1, "z": 2}, {"a": 3, "y": 4}],
                ["a"],
            )

            self.assertTrue(bom_path.read_bytes().startswith(b"\xef\xbb\xbf"))
            self.assertFalse(utf8_path.read_bytes().startswith(b"\xef\xbb\xbf"))
            self.assertEqual([{"a": "1"}], simulation_io.read_csv_utf8_sig(bom_path))
            self.assertEqual([{"a": "1"}], simulation_io.read_csv_utf8(utf8_path))
            self.assertEqual("a,z,y", extended_path.read_text(encoding="utf-8-sig").splitlines()[0])

    def test_shared_json_variants_preserve_keyword_and_failure_contracts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            data_path = root / "data.json"
            payload_path = root / "payload.json"
            simulation_io.write_json_utf8_data(path=data_path, data={"中文": 1})
            simulation_io.write_json_utf8_payload(path=payload_path, payload={"中文": 1})
            self.assertEqual(data_path.read_bytes(), payload_path.read_bytes())

            data_path.write_text("old", encoding="utf-8")
            with self.assertRaises(TypeError):
                simulation_io.write_json_utf8_data(data_path, {"bad": object()})
            self.assertEqual("old", data_path.read_text(encoding="utf-8"))

    def test_shared_conversion_variants_keep_distinct_missing_default_semantics(self) -> None:
        converted = simulation_utils.as_float_convert_lookup_default({}, "missing", 2)
        returned = simulation_utils.as_float_return_missing_default({}, "missing", 2)
        self.assertIsInstance(converted, float)
        self.assertIsInstance(returned, int)
        self.assertEqual(7.0, simulation_utils.safe_divide(7.0, 1.0))
        self.assertEqual(3.0, simulation_utils.safe_divide(7.0, 1e-10, 3.0))

    def test_shared_clamp_preserves_inclusive_bounds(self) -> None:
        self.assertEqual(-1.0, shared_clamp(-2.0, -1.0, 1.0))
        self.assertEqual(0.25, shared_clamp(0.25, -1.0, 1.0))
        self.assertEqual(1.0, shared_clamp(2.0, -1.0, 1.0))

    def test_config_cache_invalidates_and_returns_isolated_copies(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            path = Path(temporary_dir) / "config.json"
            path.write_text('{"nested":{"value":1}}', encoding="utf-8")
            seed_explorer_server._read_config_json_cached.cache_clear()

            first = seed_explorer_server.read_config_json(path)
            first["nested"]["value"] = 99
            second = seed_explorer_server.read_config_json(path)
            self.assertEqual(1, second["nested"]["value"])

            path.write_text('{"nested":{"value":2},"changed":true}', encoding="utf-8")
            third = seed_explorer_server.read_config_json(path)
            self.assertEqual(2, third["nested"]["value"])
            self.assertTrue(third["changed"])

    def test_run_locks_serialize_same_run_but_not_different_runs(self) -> None:
        same_acquired = threading.Event()
        other_acquired = threading.Event()

        def acquire(run_id: str, event: threading.Event) -> None:
            with seed_explorer_server.lock_for_run(run_id):
                event.set()

        with seed_explorer_server.lock_for_run("lock_test_same"):
            same_thread = threading.Thread(target=acquire, args=("lock_test_same", same_acquired))
            other_thread = threading.Thread(target=acquire, args=("lock_test_other", other_acquired))
            same_thread.start()
            other_thread.start()
            self.assertTrue(other_acquired.wait(timeout=2))
            self.assertFalse(same_acquired.wait(timeout=0.1))

        self.assertTrue(same_acquired.wait(timeout=2))
        same_thread.join(timeout=2)
        other_thread.join(timeout=2)
        self.assertFalse(same_thread.is_alive())
        self.assertFalse(other_thread.is_alive())

    def test_cache_maintenance_cannot_reserve_an_active_run(self) -> None:
        with seed_explorer_server.lock_for_run("maintenance_race"):
            with seed_explorer_server.try_lock_for_run("maintenance_race") as reserved:
                self.assertFalse(reserved)
        with seed_explorer_server.try_lock_for_run("maintenance_race") as reserved:
            self.assertTrue(reserved)

    def test_orchestrator_default_paths_do_not_depend_on_cwd(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            previous_cwd = Path.cwd()
            try:
                os.chdir(temporary_dir)
                with mock.patch.object(sys, "argv", ["macro_run_orchestrator_sim.py"]):
                    args = orchestrator.parse_args()
            finally:
                os.chdir(previous_cwd)

        self.assertEqual(ROOT_DIR / "output" / "macro_runs", args.output_root)
        self.assertEqual(ROOT_DIR / "output", args.viewer_output_root)

    def test_full_run_cache_rejects_wrong_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            run_dir = Path(temporary_dir) / "seed_1_years_2"
            payload = {"seed": 1, "years": 2, "cities": []}
            seed_explorer_server.save_cached(run_dir, payload)
            self.assertIsNotNone(seed_explorer_server.load_cached(run_dir))

            path = seed_explorer_server.cache_path(run_dir)
            stale = json.loads(path.read_text(encoding="utf-8"))
            stale["cacheFingerprint"] = "stale"
            path.write_text(json.dumps(stale, ensure_ascii=False), encoding="utf-8")
            self.assertIsNone(seed_explorer_server.load_cached(run_dir))

    def test_cache_fingerprint_changes_when_dependency_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            temporary_root = Path(temporary_dir)
            dependency = temporary_root / "model.py"
            dependency.write_text("VERSION = 1\n", encoding="utf-8")
            original_stat = dependency.stat()
            with (
                mock.patch.object(seed_explorer_server, "ROOT_DIR", temporary_root),
                mock.patch.object(seed_explorer_server, "cache_dependency_files", return_value=[dependency]),
            ):
                before = seed_explorer_server.current_cache_fingerprint()
                dependency.write_text("VERSION = 2\n", encoding="utf-8")
                os.utime(
                    dependency,
                    ns=(original_stat.st_atime_ns, original_stat.st_mtime_ns),
                )
                self.assertEqual(original_stat.st_size, dependency.stat().st_size)
                self.assertEqual(original_stat.st_mtime_ns, dependency.stat().st_mtime_ns)
                after = seed_explorer_server.current_cache_fingerprint()

        self.assertNotEqual(before, after)

    def test_cache_dependencies_include_formal_server_modules(self) -> None:
        dependencies = set(seed_explorer_server.cache_dependency_files())
        expected = {
            path.resolve()
            for path in SERVER_DIR.glob("*.py")
            if path.is_file()
        }
        self.assertTrue(expected)
        self.assertTrue(expected.issubset(dependencies))

    def test_cached_run_listing_computes_fingerprint_once(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            run_root = Path(temporary_dir) / "cache"
            fingerprint = "fixed-test-fingerprint"
            for seed in (1, 2, 3):
                run_dir = run_root / seed_explorer_server.run_id_for(seed, 12)
                run_dir.mkdir(parents=True)
                seed_explorer_server.write_json(
                    seed_explorer_server.cache_path(run_dir),
                    {
                        "seed": seed,
                        "years": 12,
                        "cacheFingerprintVersion": seed_explorer_server.CACHE_FINGERPRINT_VERSION,
                        "cacheFingerprint": fingerprint,
                    },
                )

            with (
                mock.patch.object(seed_explorer_server, "RUN_ROOT", run_root),
                mock.patch.object(
                    seed_explorer_server,
                    "current_cache_fingerprint",
                    return_value=fingerprint,
                ) as current_fingerprint,
            ):
                entries = seed_explorer_server.list_cached_runs()

        self.assertEqual(3, len(entries))
        self.assertTrue(all(entry["cacheStatus"] == "valid" for entry in entries))
        current_fingerprint.assert_called_once_with()

    def test_listing_cache_does_not_prune_and_pruning_preserves_save(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            temporary_root = Path(temporary_dir)
            run_root = temporary_root / "cache"
            save_root = temporary_root / "saves"
            with (
                mock.patch.object(seed_explorer_server, "RUN_ROOT", run_root),
                mock.patch.object(seed_explorer_server, "SAVE_ROOT", save_root),
            ):
                for index in range(seed_explorer_server.MAX_CACHED_RUNS + 1):
                    run_dir = run_root / seed_explorer_server.run_id_for(index, 12)
                    run_dir.mkdir(parents=True)
                    seed_explorer_server.save_cached(run_dir, {"seed": index, "years": 12})
                    os.utime(run_dir, (index + 1, index + 1))

                durable_save = seed_explorer_server.sim_save_path(0, 12)
                seed_explorer_server.write_json(durable_save, {"seed": 0, "years": 12})

                self.assertEqual(seed_explorer_server.MAX_CACHED_RUNS + 1, len(seed_explorer_server.list_cached_runs()))
                seed_explorer_server.prune_cached_runs()

                self.assertEqual(seed_explorer_server.MAX_CACHED_RUNS, len(list(run_root.iterdir())))
                self.assertTrue(durable_save.exists())

    def test_pruning_skips_staging_and_active_run_directories(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            run_root = Path(temporary_dir) / "cache"
            run_root.mkdir()
            for index in range(seed_explorer_server.MAX_CACHED_RUNS + 2):
                run_dir = run_root / seed_explorer_server.run_id_for(index, 12)
                run_dir.mkdir()
                seed_explorer_server.save_cached(run_dir, {"seed": index, "years": 12})
                os.utime(run_dir, (index + 1, index + 1))
            active = run_root / seed_explorer_server.run_id_for(0, 12)
            staging = run_root / ".staging_in_progress"
            staging.mkdir()
            os.utime(staging, (0, 0))

            with (
                mock.patch.object(seed_explorer_server, "RUN_ROOT", run_root),
                seed_explorer_server.lock_for_run(active.name),
            ):
                seed_explorer_server.prune_cached_runs()

            completed = [path for path in run_root.iterdir() if not path.name.startswith(".staging_")]
            self.assertEqual(seed_explorer_server.MAX_CACHED_RUNS + 1, len(completed))
            self.assertTrue(active.exists())
            self.assertTrue(staging.exists())

    def test_pruning_honors_persisted_pin_and_retention_policy(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            run_root = Path(temporary_dir) / "cache"
            run_root.mkdir()
            run_ids = []
            for index in range(3):
                run_dir = run_root / seed_explorer_server.run_id_for(index, 12)
                run_dir.mkdir()
                seed_explorer_server.save_cached(run_dir, {"seed": index, "years": 12})
                os.utime(run_dir, (index + 1, index + 1))
                run_ids.append(run_dir.name)

            with (
                mock.patch.object(seed_explorer_server, "RUN_ROOT", run_root),
                mock.patch.object(
                    seed_explorer_server,
                    "cache_retention_policy",
                    return_value={"maxCachedRuns": 1, "pinnedRunIds": [run_ids[0]]},
                ),
            ):
                seed_explorer_server.prune_cached_runs()

            remaining = {path.name for path in run_root.iterdir() if path.is_dir()}
            self.assertEqual({run_ids[0], run_ids[2]}, remaining)


if __name__ == "__main__":
    unittest.main()
