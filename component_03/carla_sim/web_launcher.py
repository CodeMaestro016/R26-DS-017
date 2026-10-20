# -*- coding: utf-8 -*-
"""
web_launcher.py

Runs UNDER THE INSTANCE'S NORMAL PYTHON (3.12, not the CARLA venv) --
same Python as pose_server.py and ensemble_server.py.

This is the piece that turns "run carla_live_demo.py from a terminal"
into "click a scenario button on a website". It does three things:

  1. Serves index.html (the website) and a small JSON API.
  2. On a "Run scenario" click, makes sure pose_server.py and
     ensemble_server.py are up (starting them if not), then launches
     carla_live_demo.py --scenario <id> in the CARLA venv as a
     background process.
  3. Tells the browser where to find the live video/state feed that
     carla_live_demo.py itself serves (see WEB STREAMING SERVER in
     that file) -- by default that's this same machine on port 8093.

It does NOT start CARLA itself (the CarlaUE4 server/simulator). Start
that the way you already do, before clicking anything on the website.

------------------------------------------------------------------
EDIT THE CONFIG BLOCK BELOW BEFORE RUNNING.
------------------------------------------------------------------

Run this, then open http://localhost:8090 in a browser:

    python3 web_launcher.py
"""

import json
import os
import socket
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# ============================================================================
# CONFIG -- edit these for your setup
# ============================================================================

# Folder containing carla_live_demo.py, scenario_suite.py, feature_pipeline.py,
# rule_based_agent.py, pose_server.py, ensemble_server.py, and this file.
# Default: the folder this script lives in.
DEMO_DIR = os.path.dirname(os.path.abspath(__file__))

# Python interpreter INSIDE the CARLA venv (the one that has the `carla`
# package installed -- CARLA 0.9.15's client wheel needs Python 3.7).
# Examples:
#   Linux/macOS: "/home/you/carla_venv/bin/python3"
#   Windows:     r"C:\Users\you\carla_venv\Scripts\python.exe"
CARLA_VENV_PYTHON = "/workspace/carla_venv/bin/python3"

# Folder containing your trained models (lstm_mental_state_best.keras,
# gru_mental_state_best.keras, scaler.pkl) -- passed to ensemble_server.py.
MODEL_DIR = os.path.join(DEMO_DIR, "models")

# Where CARLA's own server (CarlaUE4) is listening. carla_live_demo.py
# connects here -- this script does not start CarlaUE4 for you.
CARLA_HOST = "localhost"
CARLA_PORT = 2000

# Host the BROWSER should use to reach carla_live_demo.py's video/state
# feed (port 8093, see WEB_STREAM_PORT in carla_live_demo.py). "localhost"
# is correct when the browser and CARLA run on the same machine. If they
# run on different machines, set this to the CARLA machine's IP/hostname
# and make sure port 8093 is reachable from the browser's machine.
STREAM_HOST_FOR_BROWSER = "localhost"
STREAM_PORT = 8093

# This website's own port.
WEB_LAUNCHER_PORT = 8090

# Seed passed to carla_live_demo.py's --seed. IMPORTANT: for "waiting" and
# "jaywalk" specifically, this number directly picks which vehicle spawn
# point gets used (see choose_vehicle_spawn() in carla_live_demo.py --
# committed/hesitant/distracted/aggressive don't depend on it, they anchor
# to a real crosswalk or a fixed spawn index instead). A different seed on
# every launch means a different location on the map every time you click
# those two scenarios. Fixed at 1 to match carla_live_demo.py's own
# --seed default (so this matches what you'd get running it manually
# without passing --seed). Change this only if you deliberately want
# waiting/jaywalk to vary between runs.
SCENARIO_SEED = 1

# Ports pose_server.py / ensemble_server.py listen on (must match those
# files -- do not change unless you changed them there too).
POSE_SERVER_PORT = 8091
ENSEMBLE_SERVER_PORT = 8092

# ============================================================================
# END CONFIG
# ============================================================================


def _port_open(host, port, timeout=0.5):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _wait_for_port(host, port, timeout_s):
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if _port_open(host, port):
            return True
        time.sleep(0.5)
    return False


class DemoOrchestrator(object):
    """Owns the child processes. One instance for the whole server."""

    def __init__(self):
        self._lock = threading.Lock()
        self.pose_proc = None
        self.ensemble_proc = None
        self.demo_proc = None
        self.current_scenario_id = None
        self.last_launch_error = None
        self.demo_log_path = os.path.join(DEMO_DIR, "carla_live_demo.log")

    # ---- support services -------------------------------------------------

    def _ensure_pose_server(self):
        if _port_open("127.0.0.1", POSE_SERVER_PORT):
            return
        self.pose_proc = subprocess.Popen(
            [sys.executable, "pose_server.py"],
            cwd=DEMO_DIR,
        )

    def _ensure_ensemble_server(self):
        if _port_open("127.0.0.1", ENSEMBLE_SERVER_PORT):
            return
        self.ensemble_proc = subprocess.Popen(
            [sys.executable, "ensemble_server.py", "--model-dir", MODEL_DIR],
            cwd=DEMO_DIR,
        )

    # ---- the demo itself ----------------------------------------------------

    def launch(self, scenario_id):
        with self._lock:
            self.last_launch_error = None

            # Stop whatever scenario is currently running first.
            self._stop_locked()

            self._ensure_pose_server()
            self._ensure_ensemble_server()

        # Wait for support services OUTSIDE the lock -- loading the pose
        # model and the two Keras models can take a while the first time.
        if not _wait_for_port("127.0.0.1", POSE_SERVER_PORT, timeout_s=60):
            self.last_launch_error = "pose_server.py did not come up on port %d within 60s." % POSE_SERVER_PORT
            return False, self.last_launch_error
        if not _wait_for_port("127.0.0.1", ENSEMBLE_SERVER_PORT, timeout_s=90):
            self.last_launch_error = "ensemble_server.py did not come up on port %d within 90s." % ENSEMBLE_SERVER_PORT
            return False, self.last_launch_error

        with self._lock:
            log_file = open(self.demo_log_path, "ab", buffering=0)
            try:
                self.demo_proc = subprocess.Popen(
                    [CARLA_VENV_PYTHON, "carla_live_demo.py",
                     "--scenario", scenario_id,
                     "--seed", str(SCENARIO_SEED),
                     "--host", CARLA_HOST,
                     "--port", str(CARLA_PORT)],
                    cwd=DEMO_DIR,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                )
                self.current_scenario_id = scenario_id
            except FileNotFoundError as exc:
                self.last_launch_error = (
                    "Could not start carla_live_demo.py -- check "
                    "CARLA_VENV_PYTHON in web_launcher.py's config. (%s)" % exc)
                return False, self.last_launch_error

        return True, None

    def _stop_locked(self):
        """Caller must hold self._lock."""
        proc = self.demo_proc
        if proc is not None and proc.poll() is None:
            proc.terminate()  # SIGTERM -- carla_live_demo.py catches this
            try:               # and exits its loop cleanly (see _STOP_REQUESTED)
                proc.wait(timeout=8)
            except subprocess.TimeoutExpired:
                proc.kill()
        self.demo_proc = None

    def stop(self):
        with self._lock:
            self._stop_locked()

    def status(self):
        with self._lock:
            demo_running = self.demo_proc is not None and self.demo_proc.poll() is None
            demo_exit_code = None if self.demo_proc is None else self.demo_proc.poll()
            return {
                "demo_running": demo_running,
                "demo_exit_code": demo_exit_code,
                "scenario_id": self.current_scenario_id if demo_running else None,
                "last_launch_error": self.last_launch_error,
                "pose_server_up": _port_open("127.0.0.1", POSE_SERVER_PORT),
                "ensemble_server_up": _port_open("127.0.0.1", ENSEMBLE_SERVER_PORT),
            }

    def tail_log(self, max_bytes=6000):
        if not os.path.exists(self.demo_log_path):
            return ""
        with open(self.demo_log_path, "rb") as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            f.seek(max(0, size - max_bytes))
            data = f.read()
        return data.decode("utf-8", errors="replace")


ORCH = DemoOrchestrator()


# ============================================================================
# HTTP SERVER
# ============================================================================

class Handler(BaseHTTPRequestHandler):
    def _send_json(self, payload, code=200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self._serve_file("index.html", "text/html")

        elif self.path == "/api/config":
            self._send_json({
                "stream_host": STREAM_HOST_FOR_BROWSER,
                "stream_port": STREAM_PORT,
            })

        elif self.path == "/api/scenarios":
            try:
                sys.path.insert(0, DEMO_DIR)
                import scenario_suite
                scenarios = [
                    {
                        "id": s.id,
                        "behavior": s.behavior,
                        "description": s.description,
                        "true_state": s.true_state,
                    }
                    for s in scenario_suite.SCENARIO_SUITE
                ]
                self._send_json({"scenarios": scenarios})
            except Exception as exc:
                self._send_json({"error": str(exc)}, code=500)

        elif self.path == "/api/status":
            self._send_json(ORCH.status())

        elif self.path == "/api/log":
            self._send_json({"log": ORCH.tail_log()})

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/api/launch":
            length = int(self.headers.get("Content-Length", 0))
            try:
                body = json.loads(self.rfile.read(length).decode("utf-8"))
                scenario_id = body["scenario_id"]
            except Exception:
                self._send_json({"ok": False, "error": "Bad request body."}, code=400)
                return

            ok, error = ORCH.launch(scenario_id)
            self._send_json({"ok": ok, "error": error})

        elif self.path == "/api/stop":
            ORCH.stop()
            self._send_json({"ok": True})

        else:
            self.send_response(404)
            self.end_headers()

    def _serve_file(self, filename, content_type):
        path = os.path.join(DEMO_DIR, filename)
        if not os.path.exists(path):
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Missing file: " + filename.encode("utf-8"))
            return
        with open(path, "rb") as f:
            data = f.read()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format, *args):
        pass


def main():
    if CARLA_VENV_PYTHON == "/path/to/your/carla_venv/bin/python3":
        print("=" * 72)
        print("WARNING: CARLA_VENV_PYTHON is still the placeholder value.")
        print("Edit the CONFIG block at the top of web_launcher.py before")
        print("clicking a scenario button, or launching will fail.")
        print("=" * 72)

    server = ThreadingHTTPServer(("0.0.0.0", WEB_LAUNCHER_PORT), Handler)
    print("Website running at: http://localhost:%d" % WEB_LAUNCHER_PORT)
    print("(Make sure CARLA itself -- CarlaUE4 -- is already running "
          "and reachable at %s:%d)" % (CARLA_HOST, CARLA_PORT))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        ORCH.stop()


if __name__ == "__main__":
    main()