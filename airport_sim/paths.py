"""Canonical workspace paths that never depend on the current directory."""

from __future__ import annotations

from pathlib import Path


PACKAGE_DIR = Path(__file__).resolve().parent
ROOT_DIR = PACKAGE_DIR.parent

CONFIG_ROOT = ROOT_DIR / "config"
OUTPUT_ROOT = ROOT_DIR / "output"
SCHEMA_ROOT = ROOT_DIR / "schemas"
SAVES_ROOT = ROOT_DIR / "saves"
WEB_ROOT = ROOT_DIR / "web"
WEB_PAGES_ROOT = WEB_ROOT / "pages"
STATIC_ROOT = WEB_ROOT / "static"

# Seed Explorer cache and save roots retain the names already used by the local
# service so lifecycle code can migrate without changing their meaning.
RUN_ROOT = OUTPUT_ROOT / "seed_explorer_runs"
SAVE_ROOT = SAVES_ROOT / "seed_explorer"
MACRO_RUN_ROOT = OUTPUT_ROOT / "macro_runs"
VIEWER_RELEASE_ROOT = OUTPUT_ROOT / "viewer_releases"

MACRO_LAYERS_ROOT = ROOT_DIR / "macro_layers"
DYNAMIC_TESTS_ROOT = ROOT_DIR / "dynamic_tests"
SEED_EXPLORER_ROOT = DYNAMIC_TESTS_ROOT / "seed_explorer"
SERVER_ROOT = PACKAGE_DIR / "server"

CURRENT_VIEWER_MANIFEST_PATH = OUTPUT_ROOT / "current_viewer_manifest.json"
CURRENT_VIEWER_MANIFEST_JS_PATH = OUTPUT_ROOT / "current_viewer_manifest.js"
LEGACY_NESTED_OUTPUT_ROOT = ROOT_DIR / "airport" / "output"

# Descriptive aliases make new callers readable while preserving the concise
# constants expected by the cache lifecycle layer.
CONFIG_DIR = CONFIG_ROOT
OUTPUT_DIR = OUTPUT_ROOT
SCHEMA_DIR = SCHEMA_ROOT
SAVES_DIR = SAVES_ROOT
SEED_EXPLORER_RUNS_DIR = RUN_ROOT
SEED_EXPLORER_SAVES_DIR = SAVE_ROOT
VIEWER_RELEASES_DIR = VIEWER_RELEASE_ROOT


def project_path(*parts: str) -> Path:
    """Return an absolute path below the workspace root."""

    return ROOT_DIR.joinpath(*parts)
