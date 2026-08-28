"""Failure-tolerant reader for qualitative Component 2 panel evidence."""

import json
from pathlib import Path


def read_panel_results(path):
    target = Path(path)
    if not target.is_file():
        return {"available": False, "message": "No panel-demo result is available yet."}
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return {"available": False, "message": f"Results could not be read: {error}"}
    metrics = payload.get("metrics")
    if not isinstance(metrics, dict):
        return {"available": False, "message": "The result file has no metrics section."}
    return {"available": True, "payload": payload, "metrics": metrics,
            "latest_mappo_event": latest_authorized_event(payload)}


def latest_authorized_event(payload):
    events = payload.get("events", ())
    return next((event for event in reversed(events)
                 if event.get("mappo_invocation") == "AUTHORIZED"), None)


def short_vehicle_id(value):
    text = str(value)
    return text.replace("PANEL_AV_", "").replace("_", "")


def format_edge(edge):
    return " → ".join(short_vehicle_id(item) for item in edge)

