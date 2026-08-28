"""Read-only standard-library research dashboard server."""

import copy
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


LATEST = {"payload": None}
LOCK = threading.Lock()
HTML_PATH = Path(__file__).with_name("debug_dashboard.html")
HTML = HTML_PATH.read_text(encoding="utf-8")


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self._send(
                200, "text/html; charset=utf-8",
                HTML.encode("utf-8"),
            )
        elif self.path == "/api/latest":
            with LOCK:
                payload = copy.deepcopy(LATEST["payload"])
            self._json(200, payload or {})
        else:
            self._json(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/simulation/update":
            self._json(404, {"error": "not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length))
            with LOCK:
                LATEST["payload"] = copy.deepcopy(payload)
            self._json(202, {"accepted": True})
        except (ValueError, json.JSONDecodeError):
            self._json(400, {"error": "invalid JSON"})

    def _json(self, status, value):
        self._send(status, "application/json", json.dumps(value).encode())

    def _send(self, status, content_type, body):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, _format, *_args):
        return


def main():
    server = ThreadingHTTPServer(("localhost", 8000), Handler)
    print("Dashboard: http://localhost:8000")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
