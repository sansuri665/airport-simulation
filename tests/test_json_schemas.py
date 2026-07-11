from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT_DIR = Path(__file__).resolve().parents[1]
SCHEMA_ROOT = ROOT_DIR / "schemas"
MACRO_DIR = ROOT_DIR / "macro_layers"
SEED_EXPLORER_DIR = ROOT_DIR / "dynamic_tests" / "seed_explorer"
for import_dir in (MACRO_DIR, SEED_EXPLORER_DIR):
    if str(import_dir) not in sys.path:
        sys.path.insert(0, str(import_dir))

import seed_explorer_server
try:
    from .schema_support import SchemaValidationError, load_schema_registry, validate_named_schema
    from .test_api_snapshot import build_fixed_seed_api_artifacts
    from . import test_atomic_run, test_viewer_release
except ImportError:
    from schema_support import SchemaValidationError, load_schema_registry, validate_named_schema
    from test_api_snapshot import build_fixed_seed_api_artifacts
    import test_atomic_run
    import test_viewer_release


class JsonSchemaContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = load_schema_registry(SCHEMA_ROOT)
        (
            cls.api_snapshot,
            cls.run_response,
            cls.operations_response,
            cls.player_response,
        ) = build_fixed_seed_api_artifacts()

    def test_schema_documents_use_draft_2020_12_and_unique_ids(self) -> None:
        paths = sorted(SCHEMA_ROOT.glob("*.schema.json"))
        self.assertGreaterEqual(len(paths), 9)
        schema_ids: list[str] = []
        for path in paths:
            schema = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(
                "https://json-schema.org/draft/2020-12/schema",
                schema.get("$schema"),
                path.name,
            )
            self.assertTrue(str(schema.get("$id") or "").startswith("https://airport.local/schemas/"))
            schema_ids.append(schema["$id"])
        self.assertEqual(len(schema_ids), len(set(schema_ids)))

    def test_version_record_matches_its_schema(self) -> None:
        payload = json.loads((ROOT_DIR / "config" / "airport_versions.json").read_text(encoding="utf-8"))
        validate_named_schema(payload, "airport-version-record.schema.json", self.registry)

    def test_fixed_seed_api_payloads_match_response_schemas(self) -> None:
        validate_named_schema(
            self.run_response,
            "seed-explorer-run-response.schema.json",
            self.registry,
        )
        validate_named_schema(
            self.operations_response,
            "beijing-operations-response.schema.json",
            self.registry,
        )
        validate_named_schema(
            self.player_response,
            "player-simulation-response.schema.json",
            self.registry,
        )

    def test_real_complete_manifest_matches_manifest_schema(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            output_root = Path(temporary_dir) / "macro_runs"
            manifest = test_atomic_run.AtomicMacroRunTests().execute_with_minimal_model(output_root)
        validate_named_schema(manifest, "macro-run-manifest.schema.json", self.registry)

    def test_viewer_release_manifest_matches_schema(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            temporary_root = Path(temporary_dir)
            variant = test_viewer_release.build_minimal_variant(temporary_root)
            viewer_root = temporary_root / "output"
            with mock.patch.object(
                test_viewer_release.orchestrator,
                "AIRPORT_DIR",
                temporary_root,
            ):
                test_viewer_release.orchestrator.publish_variant_to_viewer(variant, viewer_root)
            manifest = json.loads(
                (viewer_root / "current_viewer_manifest.json").read_text(encoding="utf-8")
            )
        validate_named_schema(manifest, "viewer-release-manifest.schema.json", self.registry)
        current_manifest_path = ROOT_DIR / "output" / "current_viewer_manifest.json"
        if current_manifest_path.is_file():
            current_manifest = json.loads(current_manifest_path.read_text(encoding="utf-8"))
            validate_named_schema(
                current_manifest,
                "viewer-release-manifest.schema.json",
                self.registry,
            )

    def test_health_workspace_and_error_envelopes_match_schemas(self) -> None:
        health = seed_explorer_server.api_envelope(
            {
                "ok": True,
                "serviceId": seed_explorer_server.LOCAL_UI_SERVICE_ID,
                "servicePid": 1,
                "runRoot": "output/seed_explorer_runs",
                "saveRoot": "saves/seed_explorer",
                "maxCachedRuns": seed_explorer_server.MAX_CACHED_RUNS,
                "cacheFingerprintVersion": seed_explorer_server.CACHE_FINGERPRINT_VERSION,
            }
        )
        workspace = seed_explorer_server.api_envelope(seed_explorer_server.workspace_status())
        error = seed_explorer_server.api_envelope({"ok": False, "error": "not found"})
        validate_named_schema(health, "health-response.schema.json", self.registry)
        validate_named_schema(workspace, "workspace-status-response.schema.json", self.registry)
        validate_named_schema(error, "api-error-response.schema.json", self.registry)

        random_seed = seed_explorer_server.api_envelope(
            {"ok": True, "seed": 20_260_123, "source": "python-secrets"}
        )
        validate_named_schema(random_seed, "random-seed-response.schema.json", self.registry)

        progress = seed_explorer_server.api_envelope(
            seed_explorer_server.task_progress("seed_7_years_12", 7, 12)
        )
        validate_named_schema(progress, "task-progress-response.schema.json", self.registry)

        background_job = seed_explorer_server.api_envelope(
            {
                "ok": True,
                "schemaVersion": "airport-background-job-v1",
                "jobId": "0123456789abcdef01234567",
                "kind": "seed_run",
                "key": "seed_7_years_12",
                "status": "queued",
                "submittedAt": "2026-07-11 12:00:00",
                "startedAt": None,
                "completedAt": None,
                "updatedEpoch": 1.0,
                "deduplicated": False,
                "result": None,
                "error": None,
            }
        )
        validate_named_schema(background_job, "background-job-response.schema.json", self.registry)

    def test_schema_catalog_points_only_to_existing_schema_files(self) -> None:
        catalog = seed_explorer_server.api_schema_catalog()
        self.assertEqual(seed_explorer_server.SCHEMA_CATALOG_VERSION, catalog["catalogVersion"])
        for schema_url in catalog["schemas"].values():
            schema_path = SCHEMA_ROOT / str(schema_url).removeprefix("/schemas/")
            self.assertTrue(schema_path.is_file(), schema_url)
        for schema_url in catalog["endpoints"].values():
            schema_path = SCHEMA_ROOT / str(schema_url).removeprefix("/schemas/")
            self.assertTrue(schema_path.is_file(), schema_url)

    def test_missing_required_api_field_is_rejected(self) -> None:
        invalid = dict(self.run_response)
        invalid.pop("cities")
        with self.assertRaisesRegex(SchemaValidationError, "missing required keys"):
            validate_named_schema(
                invalid,
                "seed-explorer-run-response.schema.json",
                self.registry,
            )


if __name__ == "__main__":
    unittest.main()
