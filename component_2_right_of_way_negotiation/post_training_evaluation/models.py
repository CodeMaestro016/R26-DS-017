"""Versioned experiment constants and fail-closed classifications."""
import hashlib
import json
import math
from dataclasses import asdict, is_dataclass
from pathlib import Path

METHODS = ("PROPOSED_MAPPO", "RULE_PLUS_FCFS", "RULES_ONLY")
V1_DIAGNOSTIC_SEEDS = (101, 202, 303, 404, 505, 606, 707, 808, 909, 1010)
SEEDS = (1103, 2207, 3301, 4409, 5501, 6607, 7703, 8807, 9901, 11003)
ROOT = Path("results/post_training_evaluation/v2_candidate")
POLICY = Path("results/final_mappo_selection_v2/selected_policy.pt")
EXPECTED_POLICY_HASH = "2ab2029fdd66f96c3ba0acf5e76487c96740161e898539f93c726228097eaf57"
CONTROLLER_VERSION = "EGO_ADMISSION_V2"
SHIELD_VERSION = "PAIR_ORDER_V2_1"

def protect_v1(root):
    """Existing V1 root and reports are permanently read-only to V2 code."""
    path = Path(root).resolve()
    old = Path(__file__).resolve().parents[1] / "results" / "final_evaluation"
    if path == old or old in path.parents:
        raise RuntimeError("V1_EVIDENCE_IS_READ_ONLY: use results/post_training_evaluation")
    legacy = Path(__file__).resolve().parents[1] / "results" / "post_training_evaluation"
    if path == legacy or any(path == legacy / name or (legacy / name) in path.parents
                            for name in ("runs", "latest")):
        raise RuntimeError("V1_EVIDENCE_IS_READ_ONLY: use a separate V2 output root")

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      allow_nan=False, default=lambda x: asdict(x) if is_dataclass(x) else str(x))

def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()

def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def write_json(path, value, *, exclusive=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x" if exclusive else "w", encoding="utf-8") as handle:
        handle.write(canonical(value))

def finite(value):
    if isinstance(value, dict):
        return all(finite(x) for x in value.values())
    if isinstance(value, (tuple, list)):
        return all(finite(x) for x in value)
    return not isinstance(value, float) or math.isfinite(value)

def classify(metrics, integrity, error=None):
    if not integrity.get("valid", False) or not finite(metrics):
        return "INVALID_EXPERIMENT"
    if metrics.get("collision_count", 0) or metrics.get("blocked_zone_violation_count", 0):
        return "UNSAFE_FAILURE"
    if error:
        return "INVALID_EXPERIMENT"
    if metrics.get("unfinished_vehicles", 0) or metrics.get("timeout", False):
        return "SAFE_DEGRADATION"
    return "PASS"

def normalize_nonfinite(value):
    """Keep invalid measurements archivable as N/A, never fabricated zeros."""
    if isinstance(value, dict):
        return {k: normalize_nonfinite(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [normalize_nonfinite(v) for v in value]
    return None if isinstance(value, float) and not math.isfinite(value) else value
