from __future__ import annotations

import unittest
from unittest import mock

from tools import check_javascript_syntax
from tools import check_markdown_links
from tools import run_test_suite as runner


class TestSuiteRegistryTests(unittest.TestCase):
    def test_every_test_module_belongs_to_a_domain_or_quick_suite(self) -> None:
        self.assertEqual(
            runner.repository_test_modules(),
            runner.all_registered_domain_modules(),
        )

    def test_registered_modules_exist(self) -> None:
        existing = runner.repository_test_modules()
        for suite_name, definition in runner.SUITES.items():
            with self.subTest(suite=suite_name):
                self.assertTrue(definition.modules)
                self.assertLessEqual(set(definition.modules), existing)

    def test_combining_suites_preserves_order_and_removes_duplicates(self) -> None:
        selected = runner.selected_modules(("quick", "viewer"))
        self.assertEqual(len(selected), len(set(selected)))
        self.assertEqual(runner.QUICK_MODULES, selected[: len(runner.QUICK_MODULES)])

    def test_full_discovery_includes_the_registry_contract(self) -> None:
        discovered = runner.discovered_test_suite()
        self.assertGreaterEqual(discovered.countTestCases(), len(runner.repository_test_modules()))

    def test_installed_entrypoint_prefers_an_executable_on_path(self) -> None:
        with mock.patch.object(runner.shutil, "which", return_value="C:/tools/airport-sim.exe"):
            self.assertEqual("C:/tools/airport-sim.exe", runner.installed_airport_entrypoint())

    def test_markdown_check_ignores_handoff_transport_but_keeps_readme(self) -> None:
        files = {
            path.relative_to(check_markdown_links.ROOT_DIR).as_posix()
            for path in check_markdown_links.markdown_files()
        }
        self.assertIn("handoff/README.md", files)
        self.assertFalse(any(path.startswith("handoff/inbox/") for path in files))
        self.assertFalse(any(path.startswith("handoff/outbox/") for path in files))
        self.assertFalse(any(path.startswith("handoff/work/") for path in files))

    def test_javascript_check_includes_standalone_map_research(self) -> None:
        self.assertIn(
            check_javascript_syntax.ROOT_DIR / "map_research",
            check_javascript_syntax.JAVASCRIPT_ROOTS,
        )


if __name__ == "__main__":
    unittest.main()
