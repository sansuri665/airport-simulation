from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


class PackageImportCompatibilityTests(unittest.TestCase):
    def run_python(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-B", *arguments],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )

    def test_model_and_formal_server_modules_support_package_imports(self) -> None:
        completed = self.run_python(
            "-c",
            "import importlib, pathlib; "
            "model_modules = [f'macro_layers.{path.stem}' for path in pathlib.Path('macro_layers').glob('*_sim.py')]; "
            "server_modules = [f'airport_sim.server.{path.stem}' for path in "
            "pathlib.Path('airport_sim/server').glob('*.py') if path.stem != '__init__']; "
            "legacy_modules = ['dynamic_tests.seed_explorer.seed_explorer_server']; "
            "[importlib.import_module(name) for name in model_modules + server_modules + legacy_modules]",
        )
        self.assertEqual(0, completed.returncode, completed.stderr)

    def test_legacy_server_module_reexports_formal_runtime_objects(self) -> None:
        from airport_sim.server import app
        from dynamic_tests.seed_explorer import seed_explorer_server as legacy

        self.assertIs(app.main, legacy.main)
        self.assertIs(app.SeedExplorerHandler, legacy.SeedExplorerHandler)
        self.assertEqual(app.LOCAL_UI_SERVICE_ID, legacy.LOCAL_UI_SERVICE_ID)

    def test_formal_and_legacy_server_entrypoints_keep_help_contract(self) -> None:
        formal = self.run_python("-m", "airport_sim", "serve", "--help")
        self.assertEqual(0, formal.returncode, formal.stderr)
        self.assertIn("Airport local UI", formal.stdout)

        legacy_module = self.run_python(
            "-m",
            "dynamic_tests.seed_explorer.seed_explorer_server",
            "--help",
        )
        self.assertEqual(0, legacy_module.returncode, legacy_module.stderr)
        self.assertIn("Airport local UI", legacy_module.stdout)

        legacy_script_path = ROOT_DIR / "dynamic_tests" / "seed_explorer" / "seed_explorer_server.py"
        legacy_script = self.run_python(str(legacy_script_path), "--help")
        self.assertEqual(0, legacy_script.returncode, legacy_script.stderr)
        self.assertIn("Airport local UI", legacy_script.stdout)

        with tempfile.TemporaryDirectory() as temporary_dir:
            arbitrary_cwd = subprocess.run(
                [sys.executable, "-B", str(legacy_script_path), "--help"],
                cwd=temporary_dir,
                capture_output=True,
                text=True,
                timeout=20,
                check=False,
            )
        self.assertEqual(0, arbitrary_cwd.returncode, arbitrary_cwd.stderr)
        self.assertIn("Airport local UI", arbitrary_cwd.stdout)

    def test_orchestrator_supports_module_and_direct_script_entrypoints(self) -> None:
        module_entry = self.run_python("-m", "macro_layers.macro_run_orchestrator_sim", "--help")
        self.assertEqual(0, module_entry.returncode, module_entry.stderr)
        self.assertIn("Run one coherent", module_entry.stdout)

        script_entry = self.run_python("macro_layers/macro_run_orchestrator_sim.py", "--help")
        self.assertEqual(0, script_entry.returncode, script_entry.stderr)
        self.assertIn("Run one coherent", script_entry.stdout)


if __name__ == "__main__":
    unittest.main()
