from __future__ import annotations

import ipaddress
import secrets
import subprocess
import sys
from collections.abc import Collection
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from types import ModuleType
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

from airport_sim.paths import WEB_PAGES_ROOT

from . import http as http_utils
from . import jobs as background_jobs


VIEWER_HTML = WEB_PAGES_ROOT / "seed_explorer_viewer.html"
HOME_HTML = WEB_PAGES_ROOT / "airport_home.html"
VIEWER_ROUTES = {
    "/seed-explorer": VIEWER_HTML,
    "/global-gdp": WEB_PAGES_ROOT / "global_gdp_viewer.html",
    "/city-markets": WEB_PAGES_ROOT / "city_market_viewer.html",
    "/beijing-forecast": WEB_PAGES_ROOT / "beijing_potential_passenger_forecast_viewer.html",
}
VIEWER_REDIRECTS = {
    "/seed-explorer/": "/seed-explorer",
    "/global-gdp/": "/global-gdp",
    "/city-markets/": "/city-markets",
    "/beijing-forecast/": "/beijing-forecast",
}
STATIC_CONTENT_TYPES = {
    ".css": "text/css; charset=utf-8",
    ".ico": "image/x-icon",
    ".js": "text/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".png": "image/png",
    ".svg": "image/svg+xml",
    ".webp": "image/webp",
}
GET_API_ROUTES = (
    "/api/health",
    "/api/workspace-status",
    "/api/seed-workspace",
    "/api/city-market-viewer/index",
    "/api/city-market-viewer/chunk",
    "/api/global-viewer/index",
    "/api/global-viewer/region",
    "/api/forecast-viewer/index",
    "/api/forecast-viewer/report",
    "/api/random-seed",
    "/api/forecast-candidate-catalog",
    "/api/task-status",
    "/api/jobs/<jobId>",
    "/api/schema",
    "/api/cached-runs",
)
POST_API_ROUTES = frozenset(
    {
        "/api/run",
        "/api/run-job",
        "/api/seed-workspace",
        "/api/beijing-operations",
        "/api/player-simulation",
        "/api/forecast-candidate",
        "/api/sim-save",
    }
)


@dataclass(frozen=True)
class RouteContract:
    method: str
    path: str
    response_type: str
    cache_policy: str


def route_contract() -> tuple[RouteContract, ...]:
    routes = [
        RouteContract("GET", "/", "html", "no-cache"),
    ]
    routes.extend(
        RouteContract("GET", path, "html", "no-cache")
        for path in VIEWER_ROUTES
    )
    routes.extend(
        RouteContract("GET", path, "redirect", "no-store")
        for path in VIEWER_REDIRECTS
    )
    routes.extend(
        (
            RouteContract("GET", "/output/<path>", "file", "content-dependent"),
            RouteContract("GET", "/schemas/<name>.schema.json", "schema", "no-cache"),
            RouteContract("GET", "/static/<path>", "static", "no-cache"),
        )
    )
    routes.extend(
        RouteContract("GET", path, "json", "no-store")
        for path in GET_API_ROUTES
    )
    routes.extend(
        RouteContract("POST", path, "json", "no-store")
        for path in sorted(POST_API_ROUTES)
    )
    return tuple(routes)


def safe_tree_file(
    request_path: str,
    *,
    prefix: str,
    root: Path,
    allowed_suffixes: Collection[str],
) -> Path | None:
    if not request_path.startswith(prefix):
        return None
    relative_text = unquote(request_path[len(prefix) :]).replace("\\", "/")
    if not relative_text or relative_text.startswith("/"):
        return None
    resolved_root = root.resolve()
    candidate = (root / relative_text).resolve()
    try:
        candidate.relative_to(resolved_root)
    except ValueError:
        return None
    if candidate.suffix.lower() not in allowed_suffixes:
        return None
    return candidate if candidate.is_file() else None


def safe_schema_file(request_path: str, *, root: Path) -> Path | None:
    prefix = "/schemas/"
    if not request_path.startswith(prefix):
        return None
    name = unquote(request_path[len(prefix) :])
    if not name or "/" in name or "\\" in name or not name.endswith(".schema.json"):
        return None
    resolved_root = root.resolve()
    candidate = (root / name).resolve()
    try:
        candidate.relative_to(resolved_root)
    except ValueError:
        return None
    return candidate if candidate.is_file() else None


def is_loopback_host(host: str | None) -> bool:
    clean_host = str(host or "").strip().strip("[]").lower()
    if clean_host == "localhost":
        return True
    try:
        return ipaddress.ip_address(clean_host).is_loopback
    except ValueError:
        return False


def request_is_local(handler: BaseHTTPRequestHandler) -> bool:
    if bool(getattr(handler.server, "allow_non_loopback", False)):
        return True
    host_name = urlparse(f"//{handler.headers.get('Host', '')}").hostname
    if not is_loopback_host(host_name):
        return False
    origin = str(handler.headers.get("Origin") or "").strip()
    if not origin:
        return True
    return is_loopback_host(urlparse(origin).hostname)


def _services() -> ModuleType:
    # Imported lazily so app.py can re-export this handler while preserving its
    # existing monkeypatch and compatibility surface during staged extraction.
    from . import app

    return app


class SeedExplorerHandler(BaseHTTPRequestHandler):
    server_version = "AirportLocalUI/2.0"

    def log_message(self, format: str, *args: Any) -> None:
        sys.stderr.write(
            "%s - - [%s] %s\n"
            % (self.address_string(), self.log_date_time_string(), format % args)
        )

    def do_GET(self) -> None:
        services = _services()
        if not services.request_is_local(self):
            services.api_error_response(
                self,
                403,
                "non_local_request",
                "本地服务拒绝了非本机来源的请求",
            )
            return
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        if path == "/":
            services.file_response(self, services.HOME_HTML, "text/html; charset=utf-8")
            return
        redirect_target = services.VIEWER_REDIRECTS.get(path)
        if redirect_target is not None:
            services.redirect_response(self, redirect_target)
            return
        viewer_path = services.VIEWER_ROUTES.get(path)
        if viewer_path is not None:
            services.file_response(self, viewer_path, "text/html; charset=utf-8")
            return
        output_path = services.safe_output_file(path)
        if output_path is not None:
            services.file_response(
                self,
                output_path,
                services.STATIC_CONTENT_TYPES[output_path.suffix.lower()],
            )
            return
        schema_path = services.safe_schema_file(path)
        if schema_path is not None:
            services.file_response(
                self,
                schema_path,
                "application/schema+json; charset=utf-8",
            )
            return
        static_path = services.safe_static_file(path)
        if static_path is not None:
            services.file_response(
                self,
                static_path,
                services.STATIC_CONTENT_TYPES[static_path.suffix.lower()],
            )
            return
        if path == "/api/health":
            services.json_response(
                self,
                200,
                {
                    "ok": True,
                    "serviceId": services.LOCAL_UI_SERVICE_ID,
                    "servicePid": services.os.getpid(),
                    "runRoot": str(
                        services.RUN_ROOT.relative_to(services.ROOT_DIR).as_posix()
                    ),
                    "saveRoot": str(
                        services.SAVE_ROOT.relative_to(services.ROOT_DIR).as_posix()
                    ),
                    "maxCachedRuns": services.cache_retention_policy()["maxCachedRuns"],
                    "cacheFingerprintVersion": services.CACHE_FINGERPRINT_VERSION,
                },
            )
            return
        if path == "/api/workspace-status":
            services.json_response(self, 200, services.workspace_status())
            return
        if path == "/api/seed-workspace":
            services.json_response(self, 200, services.seed_workspace_payload())
            return
        if path in {
            "/api/city-market-viewer/index",
            "/api/city-market-viewer/chunk",
        }:
            query = parse_qs(parsed_url.query)
            try:
                seed = services.clean_seed(query.get("seed", [""])[0])
                years = services.clean_years(query.get("years", [""])[0])
                if path.endswith("/index"):
                    payload = services.city_market_viewer_index_payload(seed, years)
                else:
                    market_id = query.get("city", [""])[0]
                    payload = services.city_market_viewer_chunk_payload(
                        seed,
                        years,
                        market_id,
                    )
                services.json_response(self, 200, payload)
            except services.CityMarketContextUnavailableError as exc:
                services.api_error_response(
                    self,
                    409,
                    "city_market_context_unavailable",
                    str(exc),
                )
            except ValueError as exc:
                services.api_error_response(self, 400, "invalid_request", str(exc))
            except FileNotFoundError as exc:
                services.api_error_response(self, 404, "resource_not_found", str(exc))
            return
        if path in {
            "/api/global-viewer/index",
            "/api/global-viewer/region",
        }:
            query = parse_qs(parsed_url.query)
            try:
                seed = services.clean_seed(query.get("seed", [""])[0])
                years = services.clean_years(query.get("years", [""])[0])
                if path.endswith("/index"):
                    payload = services.global_viewer_index_payload(seed, years)
                else:
                    region_id = query.get("region", [""])[0]
                    payload = services.global_viewer_region_payload(
                        seed,
                        years,
                        region_id,
                    )
                services.json_response(self, 200, payload)
            except services.GlobalViewerContextUnavailableError as exc:
                services.api_error_response(
                    self,
                    409,
                    "global_viewer_context_unavailable",
                    str(exc),
                )
            except ValueError as exc:
                services.api_error_response(self, 400, "invalid_request", str(exc))
            except FileNotFoundError as exc:
                services.api_error_response(self, 404, "resource_not_found", str(exc))
            return
        if path in {
            "/api/forecast-viewer/index",
            "/api/forecast-viewer/report",
        }:
            query = parse_qs(parsed_url.query)
            try:
                seed = services.clean_seed(query.get("seed", [""])[0])
                years = services.clean_years(query.get("years", [""])[0])
                data_mode = query.get("mode", [""])[0]
                if path.endswith("/index"):
                    payload = services.forecast_viewer_index_payload(
                        seed,
                        years,
                        data_mode,
                    )
                else:
                    report_id = query.get("report", [""])[0]
                    payload = services.forecast_viewer_report_payload(
                        seed,
                        years,
                        data_mode,
                        report_id,
                    )
                services.json_response(self, 200, payload)
            except services.ForecastViewerContextUnavailableError as exc:
                services.api_error_response(
                    self,
                    409,
                    "forecast_viewer_context_unavailable",
                    str(exc),
                )
            except ValueError as exc:
                services.api_error_response(self, 400, "invalid_request", str(exc))
            except FileNotFoundError as exc:
                services.api_error_response(self, 404, "resource_not_found", str(exc))
            return
        if path == "/api/random-seed":
            services.json_response(
                self,
                200,
                {
                    "ok": True,
                    "seed": 20_260_000 + secrets.randbelow(2_000),
                    "source": "python-secrets",
                },
            )
            return
        if path == "/api/forecast-candidate-catalog":
            query = parse_qs(parsed_url.query)
            try:
                seed = services.clean_seed(query.get("seed", [""])[0])
                years = services.clean_years(query.get("years", [""])[0])
                source = query.get("source", [""])[0]
                services.json_response(
                    self,
                    200,
                    {
                        "ok": True,
                        **services.forecast_candidate_catalog_payload(
                            seed,
                            years,
                            source,
                        ),
                    },
                )
            except FileNotFoundError as exc:
                services.api_error_response(self, 404, "resource_not_found", str(exc))
            except services.ForecastCandidateContextUnavailableError as exc:
                services.api_error_response(
                    self,
                    409,
                    "forecast_candidate_context_unavailable",
                    str(exc),
                )
            except ValueError as exc:
                services.api_error_response(self, 400, "invalid_request", str(exc))
            return
        if path == "/api/task-status":
            query = parse_qs(parsed_url.query)
            try:
                seed = services.clean_seed(query.get("seed", [""])[0])
                years = services.clean_years(query.get("years", [60])[0])
            except ValueError as error:
                services.json_response(self, 400, {"ok": False, "error": str(error)})
                return
            run_id = services.run_id_for(seed, years)
            services.json_response(
                self,
                200,
                services.task_progress(run_id, seed, years),
            )
            return
        if path.startswith("/api/jobs/"):
            job_id = path.removeprefix("/api/jobs/").strip()
            payload = services.background_jobs.get_job(job_id)
            if payload is None:
                services.api_error_response(
                    self,
                    404,
                    "job_not_found",
                    "后台任务不存在或已经过期",
                )
            else:
                services.json_response(self, 200, payload)
            return
        if path == "/api/schema":
            services.json_response(self, 200, services.api_schema_catalog())
            return
        if path == "/api/cached-runs":
            services.json_response(
                self,
                200,
                {
                    "ok": True,
                    "runRoot": str(
                        services.RUN_ROOT.relative_to(services.ROOT_DIR).as_posix()
                    ),
                    "saveRoot": str(
                        services.SAVE_ROOT.relative_to(services.ROOT_DIR).as_posix()
                    ),
                    "maxCachedRuns": services.cache_retention_policy()["maxCachedRuns"],
                    "cacheFingerprintVersion": services.CACHE_FINGERPRINT_VERSION,
                    "runs": services.list_cached_runs(),
                },
            )
            return
        services.json_response(self, 404, {"ok": False, "error": "not found"})

    def do_POST(self) -> None:
        services = _services()
        if not services.request_is_local(self):
            services.api_error_response(
                self,
                403,
                "non_local_request",
                "本地服务拒绝了非本机来源的请求",
            )
            return
        path = urlparse(self.path).path
        if path not in POST_API_ROUTES:
            services.json_response(self, 404, {"ok": False, "error": "not found"})
            return
        try:
            body = services.read_json_request(self)
            if path == "/api/forecast-candidate":
                services.json_response(
                    self,
                    200,
                    {"ok": True, **services.generate_forecast_candidate_payload(body)},
                )
                return
            if path == "/api/run-job":
                seed = services.clean_seed(body.get("seed"))
                years = services.clean_years(body.get("years", 60))
                force = bool(body.get("force", False))
                services.json_response(
                    self,
                    202,
                    services.submit_run_job(seed, years, force),
                )
                return
            if path == "/api/seed-workspace":
                services.json_response(
                    self,
                    200,
                    services.seed_workspace_action(body),
                )
                return
            if path == "/api/sim-save":
                seed = services.clean_seed(body.get("seed"))
                years = services.clean_years(body.get("years", 60))
                action = str(body.get("action") or "load").strip().lower()
                if action == "save":
                    save_payload = services.save_sim_save(body)
                    payload = {
                        "save": save_payload,
                        "summary": services.sim_save_summary(
                            seed,
                            years,
                            save_payload,
                        ),
                    }
                elif action == "load":
                    save_payload = services.read_sim_save(seed, years)
                    if not save_payload:
                        raise FileNotFoundError("当前 seed 没有动态测试存档")
                    payload = {
                        "save": save_payload,
                        "summary": services.sim_save_summary(
                            seed,
                            years,
                            save_payload,
                        ),
                    }
                elif action == "status":
                    save_payload = services.read_sim_save(seed, years)
                    payload = {
                        "save": save_payload,
                        "summary": services.sim_save_summary(
                            seed,
                            years,
                            save_payload,
                        ),
                    }
                elif action == "clear":
                    services.clear_sim_save(seed, years)
                    payload = {"summary": services.sim_save_summary(seed, years)}
                else:
                    raise ValueError(f"unsupported save action: {action}")
                services.json_response(self, 200, {"ok": True, **payload})
                return
            seed = services.clean_seed(body.get("seed"))
            years = services.clean_years(body.get("years", 60))
            force = bool(body.get("force", False))
            if path == "/api/player-simulation":
                current_value = body.get("currentQuarterIndex")
                current_index = (
                    None
                    if current_value in (None, "")
                    else int(services.as_float(current_value, 0.0))
                )
                payload = services.load_player_simulation(
                    seed,
                    years,
                    force,
                    services.clean_player_actions(body.get("playerActions", [])),
                    current_index,
                )
            elif path == "/api/beijing-operations":
                mode = services.clean_operation_mode(body.get("mode", "replay"))
                payload = services.load_beijing_operations(seed, years, force, mode)
            else:
                payload = services.run_seed(seed, years, force)
            services.json_response(self, 200, {"ok": True, **payload})
        except http_utils.UnsupportedMediaTypeError as exc:
            services.api_error_response(
                self,
                415,
                "unsupported_media_type",
                str(exc),
            )
        except http_utils.RequestTooLargeError as exc:
            services.api_error_response(self, 413, "request_too_large", str(exc))
        except services.ForecastCandidateContextUnavailableError as exc:
            services.api_error_response(
                self,
                409,
                "forecast_candidate_context_unavailable",
                str(exc),
            )
        except ValueError as exc:
            services.api_error_response(self, 400, "invalid_request", str(exc))
        except FileNotFoundError as exc:
            services.api_error_response(self, 404, "resource_not_found", str(exc))
        except FileExistsError as exc:
            services.api_error_response(self, 409, "resource_conflict", str(exc))
        except background_jobs.JobQueueFullError as exc:
            services.api_error_response(self, 503, "job_queue_full", str(exc))
        except subprocess.TimeoutExpired:
            services.structured_log("api_error", path=path, error_type="TimeoutExpired")
            services.api_error_response(
                self,
                504,
                "task_timeout",
                "模型运行超时，请稍后重试",
            )
        except Exception as exc:
            services.structured_log(
                "api_error",
                path=path,
                error_type=type(exc).__name__,
            )
            services.api_error_response(
                self,
                500,
                "internal_error",
                "服务运行失败，请查看启动窗口中的错误日志",
            )
