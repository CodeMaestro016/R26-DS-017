"""Read backend-authored panel values; never import or run the evaluator."""
import hashlib
import json
from pathlib import Path
from socialmind_drive_showcase.config import COMPONENT2_ROOT

PANEL_ROOT = COMPONENT2_ROOT / "results/targeted_validation/v2/latest"

def read_targeted_validation(path=None):
    target = Path(path) if path is not None else PANEL_ROOT / "panel_summary.json"
    if path is None and not target.is_file():
        target = COMPONENT2_ROOT / "results/panel_validation/v2/latest/panel_summary.json"
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
        checksum = json.loads(target.with_name("panel_summary.sha256.json").read_text(encoding="utf-8"))
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
        if hashlib.sha256(raw).hexdigest() != checksum["payload_hash"]:
            raise ValueError("Panel summary checksum mismatch")
        if payload.get("schema_version") != 1 or payload.get("evidence_classification") != "TARGETED_PANEL_VALIDATION" or not isinstance(payload.get("cases"), list):
            raise ValueError("Unsupported panel summary")
        return dict(available=True, payload=payload)
    except (OSError, ValueError, TypeError, KeyError) as error:
        return dict(available=False, message="Targeted Validation recorded outputs are unavailable: " + str(error))
