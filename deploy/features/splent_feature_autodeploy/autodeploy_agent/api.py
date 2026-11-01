"""The agent's HTTP API, on port 8080 of the product network only.

    GET  /status            what the agent is doing and what runs
    GET  /history?limit=N   the newest N deploys, newest first (1 to 200)
    POST /check             look for a new image now
    POST /pause             stop deploying until resumed
    POST /resume            deploy again, and check right away

Every request carries ``Authorization: Bearer <AUTODEPLOY_SECRET>``, compared
in constant time. Anything else is a 401, whatever the path, so the API says
nothing to a caller without the secret, not even which paths exist. An agent
without a secret refuses every request.

There is deliberately no rollback endpoint: a rollback restores the backup
taken before the deploy, so done by hand later it would throw away whatever
was written since.
"""

from __future__ import annotations

import hmac
import json
import logging
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

logger = logging.getLogger("autodeploy.api")

DEFAULT_HISTORY_LIMIT = 20
MAX_HISTORY_LIMIT = 200
#: The POST endpoints take no body. Anything larger than this is drained no
#: further and the connection closed.
MAX_BODY = 4096


class Api:
    """Routing and authentication, without sockets, so it can be tested."""

    def __init__(self, deployer, secret: str, trigger):
        self.deployer = deployer
        self._secret = (secret or "").encode("utf-8")
        self.trigger = trigger

    def authorized(self, header: str | None) -> bool:
        scheme, _sep, value = (header or "").strip().partition(" ")
        if scheme.lower() != "bearer" or not self._secret:
            return False
        return hmac.compare_digest(value.strip().encode("utf-8"), self._secret)

    def handle(self, method: str, target: str, authorization: str | None):
        """Answer one request. Returns (HTTP status, JSON payload)."""
        if not self.authorized(authorization):
            return 401, {"error": "unauthorized"}

        parts = urlsplit(target)
        path = parts.path.rstrip("/") or "/"
        routes = {
            "/status": ("GET", self._status),
            "/history": ("GET", self._history),
            "/check": ("POST", self._check),
            "/pause": ("POST", self._pause),
            "/resume": ("POST", self._resume),
        }
        if path not in routes:
            return 404, {"error": "not_found"}
        allowed, view = routes[path]
        if method != allowed:
            return 405, {"error": "method_not_allowed", "allowed": allowed}
        return view(parse_qs(parts.query))

    def _status(self, _query):
        return 200, self.deployer.status()

    def _history(self, query):
        raw = (query.get("limit") or [str(DEFAULT_HISTORY_LIMIT)])[0]
        try:
            limit = int(raw)
        except ValueError:
            return 400, {"error": "invalid_limit"}
        limit = max(1, min(MAX_HISTORY_LIMIT, limit))
        return 200, {"entries": self.deployer.store.history(limit), "limit": limit}

    def _check(self, _query):
        # A person asked, so the update window does not hold this one back.
        self.trigger(ignore_window=True)
        return 202, {"accepted": True, "status": self.deployer.status()}

    def _pause(self, _query):
        return 200, self.deployer.pause()

    def _resume(self, _query):
        status = self.deployer.resume()
        self.trigger()
        return 200, status


def make_handler(api: Api):
    class Handler(BaseHTTPRequestHandler):
        server_version = "splent-autodeploy"
        sys_version = ""
        protocol_version = "HTTP/1.1"

        def _answer(self):
            length = self.headers.get("Content-Length")
            try:
                length = int(length) if length else 0
            except ValueError:
                length = 0
            if length > MAX_BODY:
                self.close_connection = True
            elif length > 0:
                self.rfile.read(length)
            status, payload = api.handle(
                self.command, self.path, self.headers.get("Authorization")
            )
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            if status == 401:
                self.send_header("WWW-Authenticate", 'Bearer realm="autodeploy"')
            self.end_headers()
            self.wfile.write(body)

        do_GET = _answer
        do_POST = _answer
        do_PUT = _answer
        do_DELETE = _answer
        do_PATCH = _answer

        def log_message(self, format, *args):  # noqa: A002 - BaseHTTPRequestHandler's name
            # Method, path and status only. Never the headers: one of them
            # is the secret.
            logger.info("%s %s", self.address_string(), format % args)

    return Handler


def make_server(
    api: Api, host: str = "0.0.0.0", port: int = 8080
) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer((host, port), make_handler(api))
    server.daemon_threads = True
    return server
