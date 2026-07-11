"""Stable package entry points for the Airport simulation workspace.

The package starts as a thin command and path layer around the existing model
modules.  Keeping that boundary small lets the project adopt one public entry
without changing simulation calculations or removing legacy commands.
"""

from .paths import ROOT_DIR

__all__ = ["ROOT_DIR"]

