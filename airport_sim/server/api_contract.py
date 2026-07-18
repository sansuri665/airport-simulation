from __future__ import annotations

import platform
from typing import Any


SCHEMA_CATALOG_VERSION = "airport-schema-catalog-v1"
SCHEMA_FILES = {
    "versionRecord": "airport-version-record.schema.json",
    "macroRunManifest": "macro-run-manifest.schema.json",
    "viewerReleaseManifest": "viewer-release-manifest.schema.json",
    "apiEnvelope": "api-envelope.schema.json",
    "apiError": "api-error-response.schema.json",
    "health": "health-response.schema.json",
    "workspaceStatus": "workspace-status-response.schema.json",
    "seedExplorerRun": "seed-explorer-run-response.schema.json",
    "beijingOperations": "beijing-operations-response.schema.json",
    "playerSimulation": "player-simulation-response.schema.json",
    "forecastLazyIndex": "forecast-viewer-lazy-index.schema.json",
    "forecastReportChunk": "forecast-viewer-report-chunk.schema.json",
    "forecastConfig": "forecast-config.schema.json",
    "forecastTierCatalog": "forecast-tier-catalog.schema.json",
    "forecastNarrativeCatalog": "forecast-narrative-catalog.schema.json",
    "forecastCandidateCatalog": "forecast-candidate-catalog-response.schema.json",
    "forecastCandidate": "forecast-candidate-response.schema.json",
    "cityMarketLazyIndex": "city-market-viewer-lazy-index.schema.json",
    "cityMarketChunk": "city-market-viewer-chunk.schema.json",
    "randomSeed": "random-seed-response.schema.json",
    "taskProgress": "task-progress-response.schema.json",
    "backgroundJob": "background-job-response.schema.json",
    "cachedRuns": "cached-runs-response.schema.json",
    "simulationSave": "simulation-save.schema.json",
    "simSave": "sim-save-response.schema.json",
    "simSaveSlots": "sim-save-slots-response.schema.json",
}
ENDPOINT_SCHEMAS = {
    "GET /api/health": "/schemas/health-response.schema.json",
    "GET /api/workspace-status": "/schemas/workspace-status-response.schema.json",
    "GET /api/random-seed": "/schemas/random-seed-response.schema.json",
    "GET /api/forecast-candidate-catalog": "/schemas/forecast-candidate-catalog-response.schema.json",
    "GET /api/task-status": "/schemas/task-progress-response.schema.json",
    "POST /api/run-job": "/schemas/background-job-response.schema.json",
    "GET /api/jobs/<jobId>": "/schemas/background-job-response.schema.json",
    "GET /api/cached-runs": "/schemas/cached-runs-response.schema.json",
    "GET /api/sim-save-slots": "/schemas/sim-save-slots-response.schema.json",
    "POST /api/run": "/schemas/seed-explorer-run-response.schema.json",
    "POST /api/beijing-operations": "/schemas/beijing-operations-response.schema.json",
    "POST /api/player-simulation": "/schemas/player-simulation-response.schema.json",
    "POST /api/forecast-candidate": "/schemas/forecast-candidate-response.schema.json",
    "POST /api/sim-save": "/schemas/sim-save-response.schema.json",
    "POST /api/sim-save-slot": "/schemas/sim-save-response.schema.json",
    "error": "/schemas/api-error-response.schema.json",
}


def schema_catalog() -> dict[str, Any]:
    return {
        "ok": True,
        "catalogVersion": SCHEMA_CATALOG_VERSION,
        "jsonSchemaDraft": "https://json-schema.org/draft/2020-12/schema",
        "schemas": {
            schema_id: f"/schemas/{filename}"
            for schema_id, filename in SCHEMA_FILES.items()
        },
        "endpoints": dict(ENDPOINT_SCHEMAS),
    }


def api_metadata(
    *,
    api_schema_version: str,
    model_version: str,
    output_schema_version: str,
) -> dict[str, str]:
    return {
        "apiSchemaVersion": api_schema_version,
        "modelVersion": model_version,
        "outputSchemaVersion": output_schema_version,
        "pythonVersion": platform.python_version(),
        "schemaCatalog": "/api/schema",
    }
