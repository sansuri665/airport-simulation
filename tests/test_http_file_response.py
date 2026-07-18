from __future__ import annotations

import gzip
import tempfile
import unittest
from email.message import Message
from pathlib import Path
from unittest import mock

from airport_sim.server import app as local_ui
from airport_sim.server import http


class RecordingWriter:
    def __init__(self) -> None:
        self.parts: list[bytes] = []

    def write(self, content: bytes) -> None:
        self.parts.append(bytes(content))

    @property
    def body(self) -> bytes:
        return b"".join(self.parts)


class FakeHandler:
    def __init__(self, headers: dict[str, str] | None = None) -> None:
        self.headers = Message()
        for key, value in (headers or {}).items():
            self.headers[key] = value
        self.status: int | None = None
        self.response_headers: dict[str, str] = {}
        self.wfile = RecordingWriter()
        self.ended = False

    def send_response(self, status: int) -> None:
        self.status = status

    def send_header(self, key: str, value: str) -> None:
        self.response_headers[key] = value

    def end_headers(self) -> None:
        self.ended = True


class FileResponseTests(unittest.TestCase):
    def test_raw_file_is_streamed_with_etag_and_explicit_cache_policy(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            path = Path(temporary_dir) / "large.json"
            raw = b'{"data":"' + b"x" * 200_000 + b'"}'
            path.write_bytes(raw)
            handler = FakeHandler()

            with mock.patch.object(Path, "read_bytes", side_effect=AssertionError("whole-file read is forbidden")):
                http.file_response(
                    handler,
                    path,
                    "application/json; charset=utf-8",
                    cache_control="no-cache",
                    allow_gzip=True,
                )

            self.assertEqual(200, handler.status)
            self.assertEqual(raw, handler.wfile.body)
            self.assertGreater(len(handler.wfile.parts), 1)
            self.assertEqual(str(len(raw)), handler.response_headers["Content-Length"])
            self.assertEqual("no-cache", handler.response_headers["Cache-Control"])
            self.assertEqual("Accept-Encoding", handler.response_headers["Vary"])
            self.assertRegex(handler.response_headers["ETag"], r'^"[0-9a-f]{64}"$')
            self.assertNotIn("Content-Encoding", handler.response_headers)

    def test_gzip_sidecar_has_distinct_etag_and_supports_304(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            path = Path(temporary_dir) / "chunk.json"
            raw = b'{"data":"' + b"repeat" * 10_000 + b'"}'
            compressed = gzip.compress(raw, compresslevel=9, mtime=0)
            path.write_bytes(raw)
            Path(f"{path}.gz").write_bytes(compressed)
            gzip_handler = FakeHandler({"Accept-Encoding": "br, gzip"})

            http.file_response(
                gzip_handler,
                path,
                "application/json; charset=utf-8",
                cache_control="public, max-age=31536000, immutable",
                allow_gzip=True,
            )

            self.assertEqual(200, gzip_handler.status)
            self.assertEqual("gzip", gzip_handler.response_headers["Content-Encoding"])
            self.assertEqual(compressed, gzip_handler.wfile.body)
            self.assertEqual(raw, gzip.decompress(gzip_handler.wfile.body))
            self.assertEqual(str(len(compressed)), gzip_handler.response_headers["Content-Length"])
            gzip_etag = gzip_handler.response_headers["ETag"]

            cached_handler = FakeHandler(
                {"Accept-Encoding": "gzip", "If-None-Match": f'"unrelated", {gzip_etag}'}
            )
            http.file_response(
                cached_handler,
                path,
                "application/json; charset=utf-8",
                cache_control="public, max-age=31536000, immutable",
                allow_gzip=True,
            )
            self.assertEqual(304, cached_handler.status)
            self.assertEqual(b"", cached_handler.wfile.body)

            raw_handler = FakeHandler({"If-None-Match": gzip_etag})
            http.file_response(
                raw_handler,
                path,
                "application/json; charset=utf-8",
                cache_control="public, max-age=31536000, immutable",
                allow_gzip=True,
            )
            self.assertEqual(200, raw_handler.status)
            self.assertEqual(raw, raw_handler.wfile.body)
            self.assertNotEqual(gzip_etag, raw_handler.response_headers["ETag"])

    def test_gzip_quality_zero_uses_raw_representation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            path = Path(temporary_dir) / "chunk.js"
            raw = b"window.TEST = true;"
            path.write_bytes(raw)
            Path(f"{path}.gz").write_bytes(gzip.compress(raw, mtime=0))
            handler = FakeHandler({"Accept-Encoding": "br, gzip;q=0, *;q=0.5"})

            http.file_response(
                handler,
                path,
                "text/javascript; charset=utf-8",
                cache_control="no-cache",
                allow_gzip=True,
            )

            self.assertEqual(raw, handler.wfile.body)
            self.assertNotIn("Content-Encoding", handler.response_headers)

    def test_app_policy_is_immutable_only_for_versioned_release_assets(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            output_root = Path(temporary_dir) / "output"
            release = output_root / "viewer_releases" / "release-id" / "chunk.json"
            manifest = output_root / "current_viewer_manifest.json"
            static = Path(temporary_dir) / "web" / "page.js"
            with mock.patch.object(local_ui, "OUTPUT_ROOT", output_root):
                self.assertEqual(
                    ("public, max-age=31536000, immutable", True),
                    local_ui.file_response_policy(release, "application/json; charset=utf-8"),
                )
                self.assertEqual(
                    ("no-cache", False),
                    local_ui.file_response_policy(manifest, "application/json; charset=utf-8"),
                )
                self.assertEqual(
                    ("no-cache", False),
                    local_ui.file_response_policy(static, "text/javascript; charset=utf-8"),
                )


if __name__ == "__main__":
    unittest.main()
