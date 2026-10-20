
import json
import os
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request

from carla_app.config.simulation_config import (
    ML_SERVICE_AUTOSTART,
    ML_SERVICE_PYTHON,
    ML_SERVICE_URL,
    ML_SERVICE_DIR,
)


_process = None


# ============================================================
# HTTP HELPERS
# ============================================================

def _request(method, path, params=None, body=None, headers=None, timeout=30.0):
    url = ML_SERVICE_URL + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, data=body, method=method, headers=headers or {})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def health(timeout=2.0):
    """The service's /health answer, or None if it is not running."""
    try:
        return _request("GET", "/health", timeout=timeout)
    except Exception:
        return None


def load(vehicle_id, timeout=300.0):
    """Load and select a vehicle pipeline (first load ~10-40 s)."""
    return _request("POST", "/load", params={"vehicle": vehicle_id}, timeout=timeout)


def unload(timeout=10.0):
    try:
        return _request("POST", "/unload", timeout=timeout)
    except Exception:
        return None


def process_frame(jpeg_bytes, frame_number, sign_boxes, timeout=60.0):
    return _request(
        "POST", "/process_frame",
        params={"frame_number": int(frame_number or 0)},
        body=jpeg_bytes,
        headers={
            "Content-Type": "application/octet-stream",
            "X-Sign-Boxes": json.dumps(sign_boxes or []),
        },
        timeout=timeout,
    )


def broadcast(timeout=120.0):
    return _request("POST", "/broadcast", timeout=timeout)


def retrain(vehicle_id, timeout=30.0):
    return _request("POST", "/retrain", params={"vehicle": vehicle_id}, timeout=timeout)


# ============================================================
# START / STOP THE SERVICE
# ============================================================

def start_service(wait_seconds=60.0):
    """
    Start ml_service.py (unless it is already running) and wait
    until it answers. Its output appears in this terminal.
    Returns True when the service is ready.
    """
    global _process

    if health() is not None:
        print("[ML] ML service already running at " + ML_SERVICE_URL)
        return True

    if not ML_SERVICE_AUTOSTART:
        print("[ML] ML service is not running (autostart disabled).")
        return False

    script = os.path.join(ML_SERVICE_DIR, "ml_service.py")
    if not os.path.exists(script):
        print("[ML] Not found: " + script)
        return False
    if not os.path.exists(ML_SERVICE_PYTHON):
        print("[ML] Python not found: " + ML_SERVICE_PYTHON)
        return False

    print("[ML] Starting ML service: {} -u {}".format(ML_SERVICE_PYTHON, script))
    environment = dict(os.environ)
    environment["PYTHONUNBUFFERED"] = "1"
    _process = subprocess.Popen(
        [ML_SERVICE_PYTHON, "-u", script],
        cwd=ML_SERVICE_DIR,
        env=environment,
    )

    deadline = time.time() + wait_seconds
    while time.time() < deadline:
        if _process.poll() is not None:
            print("[ML] ML service exited (code {}).".format(_process.returncode))
            return False
        if health() is not None:
            print("[OK] ML service ready at " + ML_SERVICE_URL)
            return True
        time.sleep(1.0)

    print("[ML] ML service did not answer within {:.0f} s.".format(wait_seconds))
    return False


def stop_service():
    """Stop ml_service.py if this program started it."""
    global _process
    if _process is None:
        return
    if _process.poll() is None:
        print("[ML] Stopping ML service...")
        _process.terminate()
        try:
            _process.wait(timeout=10)
        except Exception:
            _process.kill()
    _process = None
