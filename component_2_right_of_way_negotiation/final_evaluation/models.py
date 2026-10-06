"""Versioned experiment constants and fail-closed classifications."""
import hashlib
import json
import math
from dataclasses import asdict, is_dataclass
from pathlib import Path

METHODS = ("PROPOSED_MAPPO", "RULE_PLUS_FCFS", "RULES_ONLY")
SEEDS = (101, 202, 303, 404, 505, 606, 707, 808, 909, 1010)
ROOT = Path("results/final_evaluation")
POLICY = Path("results/final_mappo_selection_v2/selected_policy.pt")
EXPECTED_POLICY_HASH = "2ab2029fdd66f96c3ba0acf5e76487c96740161e898539f93c726228097eaf57"

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
