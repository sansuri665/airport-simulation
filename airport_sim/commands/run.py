from __future__ import annotations

from collections.abc import Sequence

from ._delegate import invoke_module_main


def run_command(arguments: Sequence[str]) -> int:
    """Forward a full-chain run to the existing, numerically stable runner."""

    return invoke_module_main("macro_layers.macro_run_orchestrator_sim", arguments)

