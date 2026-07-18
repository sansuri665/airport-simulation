from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


class PackageImportTests(unittest.TestCase):
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
            "[importlib.import_module(name) for name in model_modules + server_modules]",
        )
        self.assertEqual(0, completed.returncode, completed.stderr)

    def test_formal_server_entrypoint_keeps_help_contract(self) -> None:
        formal = self.run_python("-m", "airport_sim", "serve", "--help")
        self.assertEqual(0, formal.returncode, formal.stderr)
        self.assertIn("Airport local UI", formal.stdout)

    def test_orchestrator_supports_module_and_direct_script_entrypoints(self) -> None:
        module_entry = self.run_python("-m", "macro_layers.macro_run_orchestrator_sim", "--help")
        self.assertEqual(0, module_entry.returncode, module_entry.stderr)
        self.assertIn("Run one coherent", module_entry.stdout)

        script_entry = self.run_python("macro_layers/macro_run_orchestrator_sim.py", "--help")
        self.assertEqual(0, script_entry.returncode, script_entry.stderr)
        self.assertIn("Run one coherent", script_entry.stdout)


if __name__ == "__main__":
    unittest.main()
