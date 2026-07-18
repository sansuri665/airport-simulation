"""Stable package entry points for the Airport simulation workspace.

``airport_sim`` is the single public command and service package.  Model
modules remain separate so entry-point changes do not alter calculations.
"""

from .paths import ROOT_DIR

__all__ = ["ROOT_DIR"]
