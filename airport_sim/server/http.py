from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from typing import Any


class UnsupportedMediaTypeError(ValueError):
    """The local API accepts JSON request bodies only."""


class RequestTooLargeError(ValueError):
    """The request exceeds the bounded local API payload size."""


FILE_STREAM_CHUNK_BYTES = 64 * 1024


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


@lru_cache(maxsize=2048)
def _content_etag(path_text: str, size: int, modified_ns: int) -> str:
    del size, modified_ns
    path = Path(path_text)
    with path.open("rb") as handle:
        digest = hashlib.file_digest(handle, "sha256").hexdigest()
    return f'"{digest}"'


def _accepts_gzip(header_value: str | None) -> bool:
    qualities: dict[str, float] = {}
    for raw_item in str(header_value or "").split(","):
        parts = [part.strip() for part in raw_item.split(";")]
        coding = parts[0].lower()
        if not coding:
            continue
        quality = 1.0
        for parameter in parts[1:]:
            key, separator, value = parameter.partition("=")
            if separator and key.strip().lower() == "q":
                try:
                    quality = max(0.0, min(1.0, float(value.strip())))
                except ValueError:
                    quality = 0.0
        qualities[coding] = quality
    if "gzip" in qualities:
        return qualities["gzip"] > 0.0
    return qualities.get("*", 0.0) > 0.0


def _etag_matches(header_value: str | None, etag: str) -> bool:
    for candidate in str(header_value or "").split(","):
        clean = candidate.strip()
        if clean == "*":
            return True
        if clean.startswith("W/"):
            clean = clean[2:].strip()
        if clean == etag:
            return True
    return False


def _stream_file(handler: BaseHTTPRequestHandler, path: Path) -> None:
    with path.open("rb") as handle:
        while chunk := handle.read(FILE_STREAM_CHUNK_BYTES):
            handler.wfile.write(chunk)


def file_response(
    handler: BaseHTTPRequestHandler,
    path: Path,
    content_type: str,
    *,
    cache_control: str = "no-cache",
    allow_gzip: bool = False,
) -> None:
    gzip_path = Path(f"{path}.gz")
    use_gzip = allow_gzip and gzip_path.is_file() and _accepts_gzip(handler.headers.get("Accept-Encoding"))
    response_path = gzip_path if use_gzip else path
    stat = response_path.stat()
    etag = _content_etag(str(response_path.resolve()), stat.st_size, stat.st_mtime_ns)

    not_modified = _etag_matches(handler.headers.get("If-None-Match"), etag)
    handler.send_response(304 if not_modified else 200)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Cache-Control", cache_control)
    handler.send_header("ETag", etag)
    handler.send_header("X-Content-Type-Options", "nosniff")
    if allow_gzip:
        handler.send_header("Vary", "Accept-Encoding")
    if use_gzip:
        handler.send_header("Content-Encoding", "gzip")
    if not_modified:
        handler.end_headers()
        return
    handler.send_header("Content-Length", str(stat.st_size))
    handler.end_headers()
    _stream_file(handler, response_path)
