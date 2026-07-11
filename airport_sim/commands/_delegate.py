from __future__ import annotations

import importlib
import sys
from collections.abc import Sequence
from typing import Any


def invoke_module_main(module_name: str, arguments: Sequence[str]) -> int:
    """Invoke an existing module entry point with an isolated ``sys.argv``.

    The legacy parsers still read ``sys.argv``.  This adapter keeps their exact
    options and defaults while allowing the new CLI to become the public entry.
    """

    module: Any = importlib.import_module(module_name)
    module_main = getattr(module, "main", None)
    if not callable(module_main):
        raise RuntimeError(f"module has no callable main(): {module_name}")

    original_argv = sys.argv
    sys.argv = [module_name, *arguments]
    try:
        result = module_main()
    finally:
        sys.argv = original_argv
    return int(result) if isinstance(result, int) else 0

