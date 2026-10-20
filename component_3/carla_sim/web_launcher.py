# -*- coding: utf-8 -*-
"""
web_launcher.py

"""

import os
import socket
import subprocess
import sys
import threading
import time

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import uvicorn


DEMO_DIR = os.path.dirname(os.path.abspath(__file__))

CARLA_VENV_PYTHON = "/workspace/carla_venv/bin/python3"

MODEL_DIR = os.path.join(DEMO_DIR, "models")

CARLA_HOST = "localhost"
CARLA_PORT = 2000


STREAM_HOST_FOR_BROWSER = "localhost"
STREAM_PORT = 8093

WEB_LAUNCHER_PORT = 8090

SCENARIO_SEED = 1
MULTI_SCENARIO_ID = "multi_pedestrian_b"
MULTI_SECONDS = 90


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
            is_multi = scenario_id == MULTI_SCENARIO_ID
            self.demo_log_path = os.path.join(DEMO_DIR, "multi_ped_web.log" if is_multi else "carla_live_demo.log")
            log_file = open(self.demo_log_path, "ab", buffering=0)
            try:
                if is_multi:
                    command = [CARLA_VENV_PYTHON, "-u", "carla_multi_option_b.py",
                               "--seconds", str(MULTI_SECONDS), "--host", CARLA_HOST,
                               "--port", str(CARLA_PORT)]
                else:
                    command = [CARLA_VENV_PYTHON, "-u", "carla_live_demo.py",
                               "--scenario", scenario_id, "--seed", str(SCENARIO_SEED),
                               "--host", CARLA_HOST, "--port", str(CARLA_PORT)]
                self.demo_proc = subprocess.Popen(
                    command, cwd=DEMO_DIR, stdout=log_file, stderr=subprocess.STDOUT,
                )
                log_file.close()
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
            proc.terminate()  
            try:               
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
# FASTAPI APP
# ============================================================================

@asynccontextmanager
async def _lifespan(_app):
    yield
    ORCH.stop()


app = FastAPI(title="CARLA demo launcher", lifespan=_lifespan)


class LaunchRequest(BaseModel):
    scenario_id: str


@app.get("/")
@app.get("/index.html")
def serve_index():
    path = os.path.join(DEMO_DIR, "index.html")
    if not os.path.exists(path):
        return JSONResponse({"error": "Missing file: index.html"}, status_code=404)
    return FileResponse(path, media_type="text/html")


@app.get("/api/config")
def get_config():
    return {"stream_host": STREAM_HOST_FOR_BROWSER, "stream_port": STREAM_PORT,
            "multi_scenario_id": MULTI_SCENARIO_ID, "multi_seconds": MULTI_SECONDS}


@app.get("/api/scenarios")
def get_scenarios():
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
        scenarios.append({"id": MULTI_SCENARIO_ID, "behavior": "multi_pedestrian",
                          "description": " ",
                          "true_state": None})
        return {"scenarios": scenarios}
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)


@app.get("/api/status")
def get_status():
    return ORCH.status()


@app.get("/api/log")
def get_log():
    return {"log": ORCH.tail_log()}


@app.post("/api/launch")
def post_launch(request: LaunchRequest):
    ok, error = ORCH.launch(request.scenario_id)
    return {"ok": ok, "error": error}


@app.post("/api/stop")
def post_stop():
    ORCH.stop()
    return {"ok": True}


def main():
    if CARLA_VENV_PYTHON == "/path/to/your/carla_venv/bin/python3":
        print("=" * 72)
        print("WARNING: CARLA_VENV_PYTHON is still the placeholder value.")
        print("Edit the CONFIG block at the top of web_launcher.py before")
        print("launching a scenario, or launching will fail.")
        print("=" * 72)

    print("Website running at: http://localhost:%d" % WEB_LAUNCHER_PORT)
    print("(Make sure CARLA itself -- CarlaUE4 -- is already running "
          "and reachable at %s:%d)" % (CARLA_HOST, CARLA_PORT))
    uvicorn.run(app, host="0.0.0.0", port=WEB_LAUNCHER_PORT, log_level="warning")


if __name__ == "__main__":
    main()
