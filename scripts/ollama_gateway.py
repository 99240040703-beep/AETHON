"""Authenticated loopback-only gateway from Cloudflare Tunnel to local Ollama.

Run with OLLAMA_GATEWAY_TOKEN set to a long random secret. Exposes only /api/chat
and /api/tags, and only listens on 127.0.0.1 so it is not LAN-accessible directly.
"""
from __future__ import annotations

import hmac
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

HOST = "127.0.0.1"
PORT = int(os.getenv("OLLAMA_GATEWAY_PORT", "11435"))
OLLAMA_URL = os.getenv("OLLAMA_LOCAL_URL", "http://127.0.0.1:11434").rstrip("/")
TOKEN = os.getenv("OLLAMA_GATEWAY_TOKEN", "").strip()
ALLOWED_PATHS = {"/api/chat", "/api/tags"}


class Handler(BaseHTTPRequestHandler):
    server_version = "ASTRA-Ollama-Gateway"
    sys_version = ""

    def _authorized(self) -> bool:
        supplied = self.headers.get("Authorization", "")
        expected = f"Bearer {TOKEN}"
        return bool(TOKEN) and hmac.compare_digest(supplied, expected)

    def _reply(self, status: int, body: bytes, content_type: str = "application/json") -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _proxy(self) -> None:
        if not TOKEN:
            self._reply(503, b'{"error":"gateway token is not configured"}')
            return
        if not self._authorized():
            self._reply(401, b'{"error":"unauthorized"}')
            return
        if self.path not in ALLOWED_PATHS:
            self._reply(404, b'{"error":"not found"}')
            return
        body = None
        if self.command == "POST":
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                self._reply(400, b'{"error":"invalid content length"}')
                return
            if length < 1 or length > 2_000_000:
                self._reply(413, b'{"error":"request body missing or too large"}')
                return
            body = self.rfile.read(length)
        elif self.command != "GET":
            self._reply(405, b'{"error":"method not allowed"}')
            return
        req = Request(
            OLLAMA_URL + self.path,
            data=body,
            headers={"Content-Type": "application/json"} if body is not None else {},
            method=self.command,
        )
        try:
            with urlopen(req, timeout=180) as response:
                self._reply(response.status, response.read(), response.headers.get("Content-Type", "application/json"))
        except HTTPError as exc:
            self._reply(exc.code, exc.read())
        except (URLError, TimeoutError, OSError):
            self._reply(502, b'{"error":"local Ollama is unavailable"}')

    def do_GET(self) -> None:
        self._proxy()

    def do_POST(self) -> None:
        self._proxy()

    def log_message(self, format: str, *args: object) -> None:
        # Do not log request bodies or authorization headers.
        print(f"[ASTRA gateway] {self.address_string()} - {format % args}")


if __name__ == "__main__":
    if not TOKEN:
        raise SystemExit("Set OLLAMA_GATEWAY_TOKEN to a long random secret before starting.")
    print(f"Authenticated Ollama gateway listening on http://{HOST}:{PORT}")
    print("Only /api/chat and /api/tags are allowed; bearer authentication is required.")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
