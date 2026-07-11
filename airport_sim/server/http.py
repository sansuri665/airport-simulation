from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from typing import Any


class UnsupportedMediaTypeError(ValueError):
    """The local API accepts JSON request bodies only."""


class RequestTooLargeError(ValueError):
    """The request exceeds the bounded local API payload size."""


def api_envelope(payload: dict[str, Any], metadata: dict[str, Any]) -> dict[str, Any]:
    return {**payload, **metadata}


def json_response(
    handler: BaseHTTPRequestHandler,
    status: int,
    payload: dict[str, Any],
    metadata: dict[str, Any],
) -> None:
    raw = json.dumps(api_envelope(payload, metadata), ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(raw)))
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("X-Content-Type-Options", "nosniff")
    handler.end_headers()
    handler.wfile.write(raw)


def api_error_response(
    handler: BaseHTTPRequestHandler,
    status: int,
    error_code: str,
    message: str,
    metadata: dict[str, Any],
) -> None:
    json_response(
        handler,
        status,
        {
            "ok": False,
            "error": message,
            "errorCode": error_code,
        },
        metadata,
    )


def read_json_request(handler: BaseHTTPRequestHandler, max_body_bytes: int) -> dict[str, Any]:
    if handler.headers.get_content_type() != "application/json":
        raise UnsupportedMediaTypeError("请求必须使用 application/json")
    raw_length = handler.headers.get("Content-Length", "0")
    try:
        length = int(raw_length)
    except (TypeError, ValueError) as error:
        raise ValueError("Content-Length 必须是整数") from error
    if length < 0:
        raise ValueError("Content-Length 不能为负数")
    if length > max_body_bytes:
        raise RequestTooLargeError(f"请求内容不能超过 {max_body_bytes // 1024} KiB")
    try:
        raw = handler.rfile.read(length).decode("utf-8") if length else "{}"
    except UnicodeDecodeError as error:
        raise ValueError("请求内容必须使用 UTF-8 编码") from error
    try:
        body = json.loads(raw or "{}")
    except json.JSONDecodeError as error:
        raise ValueError("请求内容不是有效 JSON") from error
    if not isinstance(body, dict):
        raise ValueError("JSON 请求顶层必须是对象")
    return body


def redirect_response(handler: BaseHTTPRequestHandler, location: str) -> None:
    handler.send_response(302)
    handler.send_header("Location", location)
    handler.send_header("Content-Length", "0")
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("X-Content-Type-Options", "nosniff")
    handler.end_headers()


def file_response(handler: BaseHTTPRequestHandler, path: Path, content_type: str) -> None:
    raw = path.read_bytes()
    handler.send_response(200)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(raw)))
    handler.send_header("X-Content-Type-Options", "nosniff")
    if content_type.startswith("text/html"):
        handler.send_header("Cache-Control", "no-cache")
    handler.end_headers()
    handler.wfile.write(raw)
