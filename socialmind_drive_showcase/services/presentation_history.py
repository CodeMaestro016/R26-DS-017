"""Read immutable, qualitative presentation-run summaries."""

import json
from pathlib import Path


def read_presentation_runs(path, *, limit=20):
    root = Path(path)
    if not root.is_dir():
        return ()
    records = []
    for target in sorted(root.glob("run_*.json"), reverse=True):
        try:
            payload = json.loads(target.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            continue
        if payload.get("evidence_classification") == "QUALITATIVE_PRESENTATION_ONLY":
            records.append(payload)
        if len(records) >= limit:
            break
    return tuple(records)
