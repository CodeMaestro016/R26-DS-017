"""Talks directly to the CARLA demo's two HTTP endpoints:

  COMPONENT3_LAUNCHER_URL (web_launcher.py) -- scenario list, launch, stop,
  status.
  COMPONENT3_STREAM_URL (carla_live_demo.py's own dashboard server) --
  live video (/stream.mjpg) and prediction/decision state (/state).

This exists so pages/component_detail.py can render Component 3's live
demo with this app's OWN UI components -- scenario buttons, video, HUD --
instead of loading the standalone index.html in an iframe. Every function
here returns (value, error) rather than raising, since the remote instance
being unreachable is an expected, common state (tunnel not up yet, no
scenario running yet), not a bug to crash on.
"""

import json
import urllib.error
import urllib.request

from socialmind_drive_showcase.config import COMPONENT3_LAUNCHER_URL, COMPONENT3_STREAM_URL


def _get_json(url, timeout=6.0):
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _post_json(url, payload, timeout=6.0):
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_scenarios():
    """[{id, behavior, description, true_state}, ...], error"""
    try:
        return _get_json(f"{COMPONENT3_LAUNCHER_URL}/api/scenarios").get("scenarios", []), None
    except Exception as exc:
        return [], str(exc)


def fetch_launcher_status():
    """{demo_running, demo_exit_code, scenario_id, last_launch_error, ...}, error"""
    try:
        return _get_json(f"{COMPONENT3_LAUNCHER_URL}/api/status"), None
    except Exception as exc:
        return None, str(exc)


def fetch_live_state():
    """{phase, message, predicted_label, confidence, action, ttc_s,
    distance_m, elapsed_s, duration_s, finished, log, ...}, error"""
    try:
        return _get_json(f"{COMPONENT3_STREAM_URL}/state"), None
    except Exception as exc:
        return None, str(exc)


def launch_scenario(scenario_id):
    """ok (bool), error"""
    try:
        result = _post_json(f"{COMPONENT3_LAUNCHER_URL}/api/launch", {"scenario_id": scenario_id})
        return bool(result.get("ok")), result.get("error")
    except Exception as exc:
        return False, str(exc)


def stop_scenario():
    """ok (bool), error"""
    try:
        _post_json(f"{COMPONENT3_LAUNCHER_URL}/api/stop", {})
        return True, None
    except Exception as exc:
        return False, str(exc)


def stream_image_url(cache_bust=None):
    """URL for the live MJPEG stream. cache_bust (e.g. time.time()) forces
    the browser to open a fresh connection instead of reusing a dead one
    from a previous scenario run."""
    if cache_bust is None:
        return f"{COMPONENT3_STREAM_URL}/stream.mjpg"
    return f"{COMPONENT3_STREAM_URL}/stream.mjpg?_={cache_bust}"