from __future__ import annotations

from collections.abc import Sequence

from ._delegate import invoke_module_main


def serve_command(arguments: Sequence[str]) -> int:
    """Start the existing local UI through its package import path."""

    return invoke_module_main(
        "airport_sim.server.app",
        arguments,
    )
