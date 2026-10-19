"""Read and render the display-only Component 2 browser state."""

import json
from pathlib import Path
import time


def read_live_state(path, *, stale_after_seconds=5.0, clock=time.time, started_after=None):
    target = Path(path)
    if not target.is_file():
        return {"available": False, "stale": False,
                "message": "Start the live demo to view the intersection."}
    try:
        payload = json.loads(target.read_text(encoding="utf-8"),
            parse_constant=lambda value: (_ for _ in ()).throw(ValueError("Nonfinite telemetry")))
        modified = target.stat().st_mtime
        if not isinstance(payload, dict):
            raise ValueError("Invalid telemetry object")
    except (OSError, ValueError, TypeError):
        return {"available": False, "stale": False,
                "message": "Live state is temporarily unavailable."}
    if started_after is not None and modified < started_after:
        return {"available":False, "stale":False,
                "message":"Waiting for the current launch's first real frame."}
    stale = bool(payload.get("running")) and (
        clock() - modified > stale_after_seconds)
    return {"available": True, "stale": stale, "payload": payload,
            "message": ("Waiting for a fresh simulation frame…" if stale
                        else "")}

def runtime_status_label(launcher_status, state):
    """Process/telemetry state, never a scientific success classification."""
    if launcher_status in {"FAILED", "LAUNCHING", "STOPPING"}:
        return launcher_status
    if launcher_status == "READY":
        return "IDLE"
    if state.get("stale"):
        return "STALE TELEMETRY"
    return "RUNNING" if launcher_status == "RUNNING" else "RUN FINISHED"

def discharge_label(payload):
    completed, scheduled = payload.get("completed"), payload.get("scheduled")
    if completed is None or scheduled is None:
        return "RUN FINISHED — COMPLETION UNAVAILABLE"
    return "SCENARIO COMPLETE" if scheduled > 0 and completed == scheduled else "RUN FINISHED — INCOMPLETE DISCHARGE"
