from __future__ import annotations

import json
import io
import shutil
import tempfile
import unittest
from collections.abc import Callable
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any

from airport_sim.cli import main
from airport_sim.commands.validate_config import validate_config_tree
from airport_sim.paths import CONFIG_ROOT, SCHEMA_ROOT


class ConfigValidationTests(unittest.TestCase):
    def copied_config_root(self, temporary_dir: str) -> Path:
        target = Path(temporary_dir) / "config"
        shutil.copytree(CONFIG_ROOT, target)
        return target

    def mutate(
        self,
        root: Path,
        relative_path: str,
        update: Callable[[dict[str, Any]], None],
    ) -> None:
        path = root / relative_path
        payload = json.loads(path.read_text(encoding="utf-8"))
        update(payload)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def errors_with_code(self, report: dict[str, Any], code: str) -> list[dict[str, Any]]:
        return [error for error in report["errors"] if error["code"] == code]

    def test_workspace_inventory_classifies_every_config_family(self) -> None:
        report = validate_config_tree()

        self.assertEqual("airport-config-validation-v2", report["schemaVersion"])
        self.assertEqual(59, report["fileCount"])
        self.assertEqual(59, report["validCount"])
        self.assertEqual(0, report["invalidCount"])
        self.assertEqual(0, report["unclassifiedCount"])
        self.assertEqual(13, report["familyCount"])
        self.assertEqual(59, sum(family["fileCount"] for family in report["families"]))
        self.assertTrue(all(family["schema"] for family in report["families"]))
        self.assertTrue(
            all((SCHEMA_ROOT / family["schema"]).is_file() for family in report["families"])
        )
        self.assertIn("json_schema", report["checks"])
        self.assertIn("cross_file_references", report["checks"])
        self.assertIn("weight_balance", report["checks"])
        self.assertIn("curve_order", report["checks"])

    def test_schema_range_error_has_code_and_json_location(self) -> None:
        relative_path = (
            "city_airport_potential_passenger_forecast/"
            "beijing_airport_system_potential_passenger_forecast_v1.json"
        )
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = self.copied_config_root(temporary_dir)
            self.mutate(
                root,
                relative_path,
                lambda payload: payload["forecast_reports"][0].__setitem__(
                    "forecast_quality_score", 101
                ),
            )
            report = validate_config_tree(root, require_classified=True)

        errors = self.errors_with_code(report, "schema_validation")
        self.assertEqual(1, report["invalidCount"])
        self.assertTrue(errors)
        self.assertEqual(relative_path, errors[0]["path"])
        self.assertIn("forecast_quality_score", errors[0]["location"])
        self.assertIn("maximum", errors[0]["message"])

    def test_unknown_city_profile_is_reported_as_cross_file_reference(self) -> None:
        relative_path = "city_airport_markets/china_mainland/beijing_airport_system.json"
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = self.copied_config_root(temporary_dir)
            self.mutate(
                root,
                relative_path,
                lambda payload: payload["airline_supply_model"].__setitem__(
                    "dynamics_profile_id", "missing_profile"
                ),
            )
            report = validate_config_tree(root, require_classified=True)

        errors = self.errors_with_code(report, "reference_not_found")
        self.assertEqual(1, report["invalidCount"])
        self.assertTrue(errors)
        self.assertIn("dynamics_profile_id", errors[0]["location"])
        self.assertIn("missing_profile", errors[0]["message"])

    def test_city_component_mix_must_conserve_one_hundred_percent(self) -> None:
        relative_path = "city_airport_markets/china_mainland/beijing_airport_system.json"
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = self.copied_config_root(temporary_dir)
            self.mutate(
                root,
                relative_path,
                lambda payload: payload["component_mix"].__setitem__(
                    "business_base_share_pct", 31.0
                ),
            )
            report = validate_config_tree(root, require_classified=True)

        errors = self.errors_with_code(report, "weight_balance")
        self.assertEqual(1, report["invalidCount"])
        self.assertTrue(errors)
        self.assertEqual("$.component_mix", errors[0]["location"])
        self.assertIn("100", errors[0]["message"])

    def test_operations_quarter_weights_must_sum_to_one(self) -> None:
        relative_path = "city_airport_operations/beijing_airport_system_quarterly_operations_v1.json"
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = self.copied_config_root(temporary_dir)
            self.mutate(
                root,
                relative_path,
                lambda payload: payload["quarter_component_weights"]["business"].__setitem__(
                    0, 0.1
                ),
            )
            report = validate_config_tree(root, require_classified=True)

        errors = self.errors_with_code(report, "weight_balance")
        self.assertEqual(1, report["invalidCount"])
        self.assertTrue(errors)
        self.assertEqual("$.quarter_component_weights.business", errors[0]["location"])

    def test_finance_spread_curve_requires_strictly_increasing_axis(self) -> None:
        relative_path = "city_airport_finance/beijing_airport_group_financial_state_v1.json"

        def break_curve(payload: dict[str, Any]) -> None:
            curve = payload["debt_policy"]["loan_rate_model"]["leverage_spread_model"][
                "spread_curve"
            ]
            curve[1]["liability_ratio_pct"] = curve[0]["liability_ratio_pct"]

        with tempfile.TemporaryDirectory() as temporary_dir:
            root = self.copied_config_root(temporary_dir)
            self.mutate(root, relative_path, break_curve)
            report = validate_config_tree(root, require_classified=True)

        errors = self.errors_with_code(report, "curve_order")
        self.assertEqual(1, report["invalidCount"])
        self.assertTrue(errors)
        self.assertIn("spread_curve", errors[0]["location"])
        self.assertIn("strictly increasing", errors[0]["message"])

    def test_strict_inventory_rejects_new_unclassified_config(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = self.copied_config_root(temporary_dir)
            unknown = root / "new_family" / "example.json"
            unknown.parent.mkdir()
            unknown.write_text('{"schema_version": "example-v1"}\n', encoding="utf-8")
            report = validate_config_tree(root, require_classified=True)

        errors = self.errors_with_code(report, "family_unclassified")
        self.assertEqual(60, report["fileCount"])
        self.assertEqual(1, report["unclassifiedCount"])
        self.assertEqual(1, report["invalidCount"])
        self.assertEqual("new_family/example.json", errors[0]["path"])

    def test_cli_json_output_preserves_structured_error_location(self) -> None:
        relative_path = (
            "city_airport_potential_passenger_forecast/"
            "beijing_airport_system_potential_passenger_forecast_v1.json"
        )
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = self.copied_config_root(temporary_dir)
            self.mutate(
                root,
                relative_path,
                lambda payload: payload["forecast_reports"][0].__setitem__(
                    "forecast_quality_score", 101
                ),
            )
            output = io.StringIO()
            with redirect_stdout(output):
                exit_code = main(
                    ["validate-config", "--config-root", str(root), "--json"]
                )

        report = json.loads(output.getvalue())
        self.assertEqual(1, exit_code)
        self.assertEqual("schema_validation", report["errors"][0]["code"])
        self.assertIn("forecast_quality_score", report["errors"][0]["location"])


if __name__ == "__main__":
    unittest.main()
