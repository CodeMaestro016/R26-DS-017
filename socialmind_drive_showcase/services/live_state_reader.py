"""Read and render the display-only Component 2 browser state."""

import json
from pathlib import Path
import time


def read_live_state(path, *, stale_after_seconds=5.0, clock=time.time):
    target = Path(path)
    if not target.is_file():
        return {"available": False, "stale": False,
                "message": "Start the live demo to view the intersection."}
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return {"available": False, "stale": False,
                "message": "Live state is temporarily unavailable."}
    stale = bool(payload.get("running")) and (
        clock() - target.stat().st_mtime > stale_after_seconds)
    return {"available": True, "stale": stale, "payload": payload,
            "message": ("Waiting for a fresh simulation frame…" if stale
                        else "")}

