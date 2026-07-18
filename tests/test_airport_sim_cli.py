from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from airport_sim import cli, paths
from airport_sim.commands import cache as cache_command_module
from airport_sim.commands import serve as serve_command_module
from airport_sim.commands._delegate import invoke_module_main
from airport_sim.commands.validate_config import validate_config_tree


ROOT_DIR = Path(__file__).resolve().parents[1]


class AirportSimPathTests(unittest.TestCase):
    def test_canonical_paths_do_not_depend_on_current_directory(self) -> None:
        original_cwd = Path.cwd()
        with tempfile.TemporaryDirectory() as temporary_dir:
            try:
                os.chdir(temporary_dir)
                self.assertEqual(ROOT_DIR, paths.ROOT_DIR)
                self.assertEqual(ROOT_DIR / "output", paths.OUTPUT_ROOT)
                self.assertEqual(ROOT_DIR / "output" / "seed_explorer_runs", paths.RUN_ROOT)
                self.assertEqual(ROOT_DIR / "saves" / "seed_explorer", paths.SAVE_ROOT)
                self.assertEqual(ROOT_DIR / "schemas", paths.SCHEMA_ROOT)
                self.assertEqual(ROOT_DIR / "config", paths.CONFIG_ROOT)
                self.assertEqual(ROOT_DIR / "web", paths.WEB_ROOT)
                self.assertEqual(ROOT_DIR / "web" / "pages", paths.WEB_PAGES_ROOT)
                self.assertEqual(ROOT_DIR / "web" / "static", paths.STATIC_ROOT)
                self.assertEqual(ROOT_DIR / "airport_sim" / "server", paths.SERVER_ROOT)
            finally:
                os.chdir(original_cwd)


class AirportSimCliTests(unittest.TestCase):
    def test_run_forwards_all_model_arguments(self) -> None:
        with mock.patch.object(cli, "run_command", return_value=0) as command:
            self.assertEqual(0, cli.main(["run", "--seed", "1234", "--years", "5"]))
        command.assert_called_once_with(["--seed", "1234", "--years", "5"])

    def test_serve_forwards_all_server_arguments(self) -> None:
        with mock.patch.object(cli, "serve_command", return_value=0) as command:
            self.assertEqual(0, cli.main(["serve", "--port", "9000", "--open"]))
        command.assert_called_once_with(["--port", "9000", "--open"])

    def test_serve_delegates_to_formal_server_module(self) -> None:
        with mock.patch.object(serve_command_module, "invoke_module_main", return_value=0) as invoke:
            self.assertEqual(0, serve_command_module.serve_command(["--port", "9000"]))
        invoke.assert_called_once_with("airport_sim.server.app", ["--port", "9000"])

    def test_delegate_restores_sys_argv(self) -> None:
        captured: list[str] = []
        fake_module = SimpleNamespace(main=lambda: captured.extend(sys.argv) or 7)
        original = sys.argv
        with mock.patch("airport_sim.commands._delegate.importlib.import_module", return_value=fake_module):
            result = invoke_module_main("example.module", ["--value", "42"])
        self.assertEqual(7, result)
        self.assertEqual(["example.module", "--value", "42"], captured)
        self.assertIs(original, sys.argv)

    def test_validate_config_detects_duplicate_keys(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            (root / "valid.json").write_text('{"value": 1}', encoding="utf-8")
            (root / "duplicate.json").write_text('{"value": 1, "value": 2}', encoding="utf-8")
            report = validate_config_tree(root)
        self.assertEqual(2, report["fileCount"])
        self.assertEqual(1, report["invalidCount"])
        self.assertEqual("duplicate.json", report["errors"][0]["path"])
        self.assertIn("duplicate JSON key", report["errors"][0]["error"])

    def test_validate_config_default_is_independent_of_current_directory(self) -> None:
        report = validate_config_tree()
        self.assertEqual(str(paths.CONFIG_ROOT), report["configRoot"])
        self.assertGreater(report["fileCount"], 0)
        self.assertEqual([], report["errors"])

    def test_cache_commands_use_the_lifecycle_service_contract(self) -> None:
        service = SimpleNamespace(
            list_cache=mock.Mock(return_value={"entries": []}),
            plan_cache=mock.Mock(return_value={"remove": ["run-old"]}),
            clean_cache=mock.Mock(return_value={"removed": ["run-old"]}),
            pin_cache=mock.Mock(return_value={"pinned": "run-a"}),
            unpin_cache=mock.Mock(return_value={"unpinned": "run-a"}),
            set_retention=mock.Mock(return_value={"maxCachedRuns": 3}),
            set_viewer_retention=mock.Mock(return_value={"maxViewerReleases": 2}),
        )
        output = io.StringIO()
        with mock.patch.object(cache_command_module, "_cache_service", return_value=service):
            with contextlib.redirect_stdout(output):
                self.assertEqual(0, cli.main(["cache", "list", "--json"]))
                self.assertEqual(0, cli.main(["cache", "clean", "--confirm", "--json"]))
                self.assertEqual(0, cli.main(["cache", "pin", "run-a", "--json"]))
                self.assertEqual(0, cli.main(["cache", "unpin", "run-a", "--json"]))
                self.assertEqual(0, cli.main(["cache", "retention", "3", "--json"]))
                self.assertEqual(0, cli.main(["cache", "viewer-retention", "2", "--json"]))
        service.list_cache.assert_called_once_with()
        service.plan_cache.assert_called_once_with()
        service.clean_cache.assert_called_once_with(confirm=True)
        service.pin_cache.assert_called_once_with("run-a")
        service.unpin_cache.assert_called_once_with("run-a")
        service.set_retention.assert_called_once_with(3)
        service.set_viewer_retention.assert_called_once_with(2)

    def test_noninteractive_clean_only_returns_plan(self) -> None:
        service = SimpleNamespace(
            plan_cache=mock.Mock(return_value={"estimatedBytes": 100}),
            clean_cache=mock.Mock(),
        )
        output = io.StringIO()
        with mock.patch.object(cache_command_module, "_cache_service", return_value=service):
            with mock.patch.object(cache_command_module.sys.stdin, "isatty", return_value=False):
                with contextlib.redirect_stdout(output):
                    self.assertEqual(0, cli.main(["cache", "clean", "--json"]))
        service.clean_cache.assert_not_called()
        payload = json.loads(output.getvalue())
        self.assertFalse(payload["executed"])
        self.assertEqual("confirmation_required", payload["reason"])

    def test_cache_failure_is_reported_without_traceback(self) -> None:
        service = SimpleNamespace(plan_cache=mock.Mock(side_effect=RuntimeError("service is active")))
        output = io.StringIO()
        with mock.patch.object(cache_command_module, "_cache_service", return_value=service):
            with contextlib.redirect_stdout(output):
                self.assertEqual(2, cli.main(["cache", "plan", "--json"]))
        payload = json.loads(output.getvalue())
        self.assertFalse(payload["ok"])
        self.assertIn("service is active", payload["error"])

    def test_human_cache_inventory_omits_nested_metadata_dump(self) -> None:
        service = SimpleNamespace(
            list_cache=mock.Mock(
                return_value={
                    "entries": [
                        {
                            "status": "keep",
                            "path": "output/seed_explorer_runs/seed_1_years_5",
                            "bytes": 2048,
                            "reason": "newest cache",
                            "cacheMetadata": {"large": [1, 2, 3]},
                        }
                    ],
                    "totalBytes": 2048,
                }
            )
        )
        output = io.StringIO()
        with mock.patch.object(cache_command_module, "_cache_service", return_value=service):
            with contextlib.redirect_stdout(output):
                self.assertEqual(0, cli.main(["cache", "list"]))
        rendered = output.getvalue()
        self.assertIn("Cache inventory: 1 entry/entries, 2.0 KiB total.", rendered)
        self.assertIn("seed_1_years_5", rendered)
        self.assertNotIn("cacheMetadata", rendered)

    def test_pyproject_exposes_only_the_unified_console_entry(self) -> None:
        content = (ROOT_DIR / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('airport-sim = "airport_sim.cli:main"', content)
        self.assertNotIn("airport-ui", content)
        self.assertNotIn("airport_ui", content)
        self.assertNotIn("dynamic_tests", content)


if __name__ == "__main__":
    unittest.main()
