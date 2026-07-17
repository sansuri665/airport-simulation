from __future__ import annotations

import json
import subprocess
import sys
import threading
import time
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest import mock


ROOT_DIR = Path(__file__).resolve().parents[1]
SEED_EXPLORER_DIR = ROOT_DIR / "dynamic_tests" / "seed_explorer"

from airport_sim.server import app as local_ui


class QuietAirportHandler(local_ui.SeedExplorerHandler):
    def log_message(self, format: str, *args: object) -> None:
        return


class LocalUIIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
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

    def get(self, path: str) -> tuple[int, str, str]:
        with urllib.request.urlopen(f"{self.base_url}{path}", timeout=5) as response:
            return response.status, response.headers.get_content_type(), response.read().decode("utf-8")

    def post_error(
        self,
        path: str,
        body: bytes,
        content_type: str | None = "application/json",
        extra_headers: dict[str, str] | None = None,
    ) -> tuple[int, dict[str, object]]:
        headers = {} if content_type is None else {"Content-Type": content_type}
        headers.update(extra_headers or {})
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=body,
            headers=headers,
            method="POST",
        )
        with self.assertRaises(urllib.error.HTTPError) as context:
            urllib.request.urlopen(request, timeout=5)
        payload = json.loads(context.exception.read().decode("utf-8"))
        return context.exception.code, payload

    def post(self, path: str, payload: dict[str, object]) -> tuple[int, dict[str, object]]:
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status, json.loads(response.read().decode("utf-8"))

    def test_formal_server_uses_canonical_web_tree(self) -> None:
        self.assertEqual(ROOT_DIR / "web" / "pages" / "airport_home.html", local_ui.HOME_HTML)
        self.assertEqual(ROOT_DIR / "web" / "pages" / "seed_explorer_viewer.html", local_ui.VIEWER_HTML)
        self.assertEqual(ROOT_DIR / "web" / "static", local_ui.STATIC_ROOT)

    def test_home_and_all_viewer_routes_are_served(self) -> None:
        expected_titles = {
            "/": "机场模拟工作台",
            "/seed-explorer": "Seed",
            "/seed-explorer/": "Seed",
            "/global-gdp": "GDP",
            "/city-markets": "城市航空市场",
            "/beijing-operations": "城市航空市场",
            "/beijing-forecast": "预测",
        }
        for path, marker in expected_titles.items():
            status, content_type, body = self.get(path)
            self.assertEqual(200, status, path)
            self.assertEqual("text/html", content_type, path)
            self.assertIn(marker, body, path)

    def test_workspace_status_identifies_service_and_data_mode(self) -> None:
        status, content_type, body = self.get("/api/workspace-status")
        payload = json.loads(body)
        self.assertEqual(200, status)
        self.assertEqual("application/json", content_type)
        self.assertEqual(local_ui.LOCAL_UI_SERVICE_ID, payload["serviceId"])
        self.assertEqual(local_ui.SEED_EXPLORER_API_SCHEMA_VERSION, payload["apiSchemaVersion"])
        self.assertEqual(local_ui.MODEL_VERSION, payload["modelVersion"])
        self.assertEqual(local_ui.OUTPUT_SCHEMA_VERSION, payload["outputSchemaVersion"])
        self.assertIn("pythonVersion", payload)
        self.assertIn(payload["viewerRelease"]["mode"], {"legacy_canonical", "versioned_release"})
        self.assertEqual("/seed-explorer", payload["pages"]["seedExplorer"])
        self.assertEqual("/city-markets", payload["pages"]["cityMarkets"])
        self.assertGreaterEqual(payload["cachedRunCount"], 0)
        self.assertGreaterEqual(payload["saveCount"], 0)

    def test_random_seed_is_generated_by_python_service(self) -> None:
        status, content_type, body = self.get("/api/random-seed")
        payload = json.loads(body)
        self.assertEqual(200, status)
        self.assertEqual("application/json", content_type)
        self.assertEqual("python-secrets", payload["source"])
        self.assertGreaterEqual(payload["seed"], 20_260_000)
        self.assertLessEqual(payload["seed"], 20_261_999)

    def test_forecast_candidate_endpoints_are_audit_only_services(self) -> None:
        catalog_payload = {
            "catalog": {
                "generatorVersion": "audit-forecast-candidate-generator-v2",
                "tiers": [],
                "styles": [],
                "modifiers": [],
            },
            "release": {"releaseId": "release-test", "seed": 424242},
        }
        with mock.patch.object(
            local_ui,
            "forecast_candidate_catalog_payload",
            return_value=catalog_payload,
        ):
            status, content_type, body = self.get("/api/forecast-candidate-catalog")
        payload = json.loads(body)
        self.assertEqual(200, status)
        self.assertEqual("application/json", content_type)
        self.assertTrue(payload["ok"])
        self.assertEqual("release-test", payload["release"]["releaseId"])

        candidate_payload = {
            "releaseId": "release-test",
            "generatorVersion": "audit-forecast-candidate-generator-v2",
            "candidate": {"candidateId": "audit_candidate_0123456789abcdef", "rows": []},
        }
        request = {
            "seed": 424242,
            "asOfYear": 2030,
            "tierProfileId": "initial_v1",
            "narrativeProfileId": "public_consensus_v2",
            "modifierMode": "pure",
            "modifierIds": [],
            "scoreMin": 70,
            "scoreMax": 80,
            "generationNonce": 0,
        }
        with mock.patch.object(
            local_ui,
            "generate_forecast_candidate_payload",
            return_value=candidate_payload,
        ) as generate:
            status, payload = self.post("/api/forecast-candidate", request)
        self.assertEqual(200, status)
        self.assertTrue(payload["ok"])
        self.assertEqual(
            "audit_candidate_0123456789abcdef",
            payload["candidate"]["candidateId"],
        )
        generate.assert_called_once_with(request)

    def test_player_simulation_expands_short_run_to_full_horizon(self) -> None:
        expected = {"seed": 77, "years": local_ui.PLAYER_SIMULATION_MIN_YEARS}
        with mock.patch.object(
            local_ui,
            "_load_player_simulation_locked",
            return_value=expected,
        ) as load:
            payload = local_ui.load_player_simulation(77, 5, False, [], None)

        self.assertEqual(expected, payload)
        load.assert_called_once_with(
            77,
            local_ui.PLAYER_SIMULATION_MIN_YEARS,
            False,
            [],
            None,
        )

    def test_task_status_exposes_structured_progress(self) -> None:
        seed = 98_765_432
        years = 12
        run_id = local_ui.run_id_for(seed, years)
        with mock.patch.object(local_ui, "structured_log") as log:
            local_ui.update_task_progress(run_id, seed, years, "running", "model_run", 15, "正在运行")
        log.assert_called_once()
        status, content_type, body = self.get(f"/api/task-status?seed={seed}&years={years}")
        payload = json.loads(body)
        self.assertEqual(200, status)
        self.assertEqual("application/json", content_type)
        self.assertEqual(local_ui.TASK_PROGRESS_VERSION, payload["schemaVersion"])
        self.assertEqual("model_run", payload["phase"])
        self.assertEqual(15, payload["progressPct"])

    def test_task_progress_registry_evicts_old_entries(self) -> None:
        with local_ui.TASK_PROGRESS_LOCK:
            original = dict(local_ui.TASK_PROGRESS)
            local_ui.TASK_PROGRESS.clear()
        try:
            with (
                mock.patch.object(local_ui, "MAX_TASK_PROGRESS_ENTRIES", 2),
                mock.patch.object(local_ui, "structured_log"),
            ):
                local_ui.update_task_progress("old", 1, 12, "running", "one", 10, "old")
                local_ui.update_task_progress("middle", 2, 12, "running", "two", 20, "middle")
                local_ui.update_task_progress("current", 3, 12, "running", "three", 30, "current")
            with local_ui.TASK_PROGRESS_LOCK:
                self.assertNotIn("old", local_ui.TASK_PROGRESS)
                self.assertEqual({"middle", "current"}, set(local_ui.TASK_PROGRESS))
        finally:
            with local_ui.TASK_PROGRESS_LOCK:
                local_ui.TASK_PROGRESS.clear()
                local_ui.TASK_PROGRESS.update(original)

    def test_post_rejects_wrong_content_type_invalid_json_and_large_body(self) -> None:
        status, payload = self.post_error("/api/run", b"{}", "text/plain")
        self.assertEqual(415, status)
        self.assertEqual("unsupported_media_type", payload["errorCode"])

        status, payload = self.post_error("/api/run", b"{broken")
        self.assertEqual(400, status)
        self.assertEqual("invalid_request", payload["errorCode"])

        with mock.patch.object(local_ui, "MAX_REQUEST_BODY_BYTES", 4):
            status, payload = self.post_error("/api/run", b'{"seed":1}')
        self.assertEqual(413, status)
        self.assertEqual("request_too_large", payload["errorCode"])

        status, payload = self.post_error(
            "/api/run",
            b"{}",
            extra_headers={"Origin": "https://example.invalid"},
        )
        self.assertEqual(403, status)
        self.assertEqual("non_local_request", payload["errorCode"])

    def test_loopback_host_detection_requires_explicit_external_opt_in(self) -> None:
        self.assertTrue(local_ui.is_loopback_host("127.0.0.1"))
        self.assertTrue(local_ui.is_loopback_host("::1"))
        self.assertTrue(local_ui.is_loopback_host("localhost"))
        self.assertFalse(local_ui.is_loopback_host("0.0.0.0"))
        self.assertFalse(local_ui.is_loopback_host("192.168.1.10"))

    def test_optional_background_run_job_preserves_sync_api(self) -> None:
        result = {"seed": 77, "years": 12, "runId": "seed_77_years_12", "cached": True}
        with (
            mock.patch.object(local_ui, "run_seed", return_value=result) as run_seed,
            mock.patch.object(local_ui, "structured_log"),
        ):
            status, submitted = self.post("/api/run-job", {"seed": 77, "years": 12})
            self.assertEqual(202, status)
            job_id = str(submitted["jobId"])
            completed: dict[str, object] | None = None
            for _ in range(100):
                _, _, body = self.get(f"/api/jobs/{job_id}")
                completed = json.loads(body)
                if completed["status"] in {"complete", "failed"}:
                    break
                time.sleep(0.01)

        self.assertIsNotNone(completed)
        self.assertEqual("complete", completed["status"])
        self.assertEqual(result, completed["result"])
        run_seed.assert_called_once_with(77, 12, False)

    def test_background_run_job_reports_a_full_bounded_queue(self) -> None:
        with mock.patch.object(local_ui.background_jobs, "MAX_ACTIVE_JOB_ENTRIES", 0):
            status, payload = self.post_error(
                "/api/run-job",
                json.dumps({"seed": 77, "years": 12}).encode("utf-8"),
            )
        self.assertEqual(503, status)
        self.assertEqual("job_queue_full", payload["errorCode"])

    def test_output_path_cannot_escape_output_root(self) -> None:
        self.assertIsNone(local_ui.safe_output_file("/output/../README.md"))
        self.assertIsNone(local_ui.safe_output_file("/output/%2e%2e/README.md"))
        with self.assertRaises(urllib.error.HTTPError) as context:
            self.get("/output/%2e%2e/README.md")
        self.assertEqual(404, context.exception.code)

    def test_schema_catalog_and_schema_files_are_served(self) -> None:
        status, content_type, body = self.get("/api/schema")
        catalog = json.loads(body)
        self.assertEqual(200, status)
        self.assertEqual("application/json", content_type)
        self.assertEqual(local_ui.SCHEMA_CATALOG_VERSION, catalog["catalogVersion"])

        schema_url = catalog["schemas"]["seedExplorerRun"]
        status, content_type, body = self.get(schema_url)
        schema = json.loads(body)
        self.assertEqual(200, status)
        self.assertEqual("application/schema+json", content_type)
        self.assertEqual(
            "https://json-schema.org/draft/2020-12/schema",
            schema["$schema"],
        )

    def test_static_stylesheet_is_served_and_cannot_escape(self) -> None:
        status, content_type, body = self.get("/static/css/airport_home.css")
        self.assertEqual(200, status)
        self.assertEqual("text/css", content_type)
        self.assertIn(":root", body)
        self.assertIsNone(local_ui.safe_static_file("/static/../README.md"))
        self.assertIsNone(local_ui.safe_static_file("/static/%2e%2e/README.md"))

        status, content_type, body = self.get("/static/js/home/page.js")
        self.assertEqual(200, status)
        self.assertEqual("text/javascript", content_type)
        self.assertIn("workspace-status", body)

    def test_start_scripts_do_not_kill_an_unknown_port_owner(self) -> None:
        root_start = (ROOT_DIR / "start_airport_ui.bat").read_text(encoding="utf-8")
        legacy_start = (SEED_EXPLORER_DIR / "start_seed_explorer.bat").read_text(encoding="utf-8")
        self.assertNotIn("Stop-Process", root_start)
        self.assertNotIn("Stop-Process", legacy_start)
        self.assertIn(local_ui.LOCAL_UI_SERVICE_ID, root_start)
        self.assertIn("-m airport_sim serve", root_start)
        self.assertIn("start_airport_ui.bat", legacy_start)
        root_stop = (ROOT_DIR / "stop_airport_ui.bat").read_text(encoding="utf-8")
        self.assertIn("seed_explorer_server\\.py", root_stop)
        self.assertIn("airport_ui", root_stop)
        self.assertIn("airport_sim\\s+serve", root_stop)
        self.assertIn("--port\\s+8776", root_stop)

    def test_cross_platform_module_entrypoint(self) -> None:
        completed = subprocess.run(
            [sys.executable, "-m", "airport_ui", "--help"],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("Airport local UI", completed.stdout)


if __name__ == "__main__":
    unittest.main()
