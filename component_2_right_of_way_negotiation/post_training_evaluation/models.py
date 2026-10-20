"""Versioned experiment constants and fail-closed classifications."""
# Import hashlib for use in this module.
import hashlib
# Import json for use in this module.
import json
# Import math for use in this module.
import math
# Import asdict, is_dataclass from dataclasses for the operations below.
from dataclasses import asdict, is_dataclass
# Import Path from pathlib for the operations below.
from pathlib import Path

# Set METHODS to a tuple containing the text 'PROPOSED_MAPPO', the text 'RULE_PLUS_FCFS', the text 'RULES_ONLY'.
METHODS = ("PROPOSED_MAPPO", "RULE_PLUS_FCFS", "RULES_ONLY")
# Set V1_DIAGNOSTIC_SEEDS to a tuple containing 101, 202, 303, 404, 505, 606, 707, 808, 909, 1010.
V1_DIAGNOSTIC_SEEDS = (101, 202, 303, 404, 505, 606, 707, 808, 909, 1010)
# Set SEEDS to a tuple containing 1103, 2207, 3301, 4409, 5501, 6607, 7703, 8807, 9901, 11003.
SEEDS = (1103, 2207, 3301, 4409, 5501, 6607, 7703, 8807, 9901, 11003)
# Set ROOT to the result of Path(the text 'results/post_training_evaluation/v2_candidate').
ROOT = Path("results/post_training_evaluation/v2_candidate")
# Set POLICY to the result of Path(the text 'results/final_mappo_selection_v2/selected_policy.pt').
POLICY = Path("results/final_mappo_selection_v2/selected_policy.pt")
# Set EXPECTED_POLICY_HASH to the text '2ab2029fdd66f96c3ba0acf5e76487c96740161e898539f93c726228097eaf57'.
EXPECTED_POLICY_HASH = "2ab2029fdd66f96c3ba0acf5e76487c96740161e898539f93c726228097eaf57"
# Set CONTROLLER_VERSION to the text 'EGO_ADMISSION_V2'.
CONTROLLER_VERSION = "EGO_ADMISSION_V2"
# Set SHIELD_VERSION to the text 'PAIR_ORDER_V2_1'.
SHIELD_VERSION = "PAIR_ORDER_V2_1"

# Existing V1 root and reports are permanently read-only to V2 code.
# Input root: the base directory used to resolve files.
# Output: no explicit value; normal completion returns None.
# Processing: select branches using the stated conditions.
def protect_v1(root):
    """Existing V1 root and reports are permanently read-only to V2 code."""
    # Set path to the result of Path(root).resolve().
    path = Path(root).resolve()
    # Set old to Path(__file__).resolve().parents at 1 joined with the path segment 'results' joined with the path segment
    # 'final_evaluation'.
    old = Path(__file__).resolve().parents[1] / "results" / "final_evaluation"
    # Run this branch when path equals old or old belongs to path.parents.
    if path == old or old in path.parents:
        # Raise RuntimeError with the text 'V1_EVIDENCE_IS_READ_ONLY: use results/post_training_evaluation' to
        # stop this execution path.
        raise RuntimeError("V1_EVIDENCE_IS_READ_ONLY: use results/post_training_evaluation")
    # Set legacy to Path(__file__).resolve().parents at 1 joined with the path segment 'results' joined with the path segment
    # 'post_training_evaluation'.
    legacy = Path(__file__).resolve().parents[1] / "results" / "post_training_evaluation"
    # Run this branch when path equals legacy or whether any item is true in a lazy sequence of path == legacy /
    # name or legacy / name in path.parents for name in a tuple containing 'runs', 'latest'.
    if path == legacy or any(path == legacy / name or (legacy / name) in path.parents
                            # Evaluate a tuple containing the text 'runs', the text 'latest' as part of the
                            # enclosing expression.
                            for name in ("runs", "latest")):
        # Raise RuntimeError with the text 'V1_EVIDENCE_IS_READ_ONLY: use a separate V2 output root' to stop this
        # execution path.
        raise RuntimeError("V1_EVIDENCE_IS_READ_ONLY: use a separate V2 output root")

# Canonical using the inputs and processing steps below.
# Input value: the supplied value.
# Output: the serialized data produced by json.dumps.
def canonical(value):
    # Return the serialized data produced by json.dumps to the caller.
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      # Declare x as input parameter.
                      allow_nan=False, default=lambda x: asdict(x) if is_dataclass(x) else str(x))

# Digest using the inputs and processing steps below.
# Input value: the supplied value.
# Output: the hexadecimal digest from hashlib.sha256(canonical(value).encode()).
def digest(value):
    # Return the hexadecimal digest from hashlib.sha256(canonical(value).encode()) to the caller.
    return hashlib.sha256(canonical(value).encode()).hexdigest()

# File hash using the inputs and processing steps below.
# Input path: the path or path object supplied by the caller.
# Output: the hexadecimal digest from hashlib.sha256(Path(path).read_bytes()).
def file_hash(path):
    # Return the hexadecimal digest from hashlib.sha256(Path(path).read_bytes()) to the caller.
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

# Write json using the inputs and processing steps below.
# Input path: the path or path object supplied by the caller.
# Input value: the supplied value.
# Input exclusive: the supplied exclusive.
# Output: no explicit value; normal completion returns None.
def write_json(path, value, *, exclusive=False):
    # Set path to the result of Path(path).
    path = Path(path)
    # Create the directory requested by path.parent.
    path.parent.mkdir(parents=True, exist_ok=True)
    # Enter the result of path.open(the text 'x' when exclusive, otherwise the text 'w') as handle and run the
    # enclosed operations within that context.
    with path.open("x" if exclusive else "w", encoding="utf-8") as handle:
        # Call handle.write with the supplied arguments.
        handle.write(canonical(value))

# Finite using the inputs and processing steps below.
# Input value: the supplied value.
# Output: return the value selected by the matching return branch below.
# Processing: select branches using the stated conditions.
def finite(value):
    # Run this branch when whether value has type dict.
    if isinstance(value, dict):
        # Return whether every item is true in a lazy sequence of the result of finite(x) for x in values from
        # value to the caller.
        return all(finite(x) for x in value.values())
    # Run this branch when whether value has type a tuple containing tuple, list.
    if isinstance(value, (tuple, list)):
        # Return whether every item is true in a lazy sequence of the result of finite(x) for x in value to the
        # caller.
        return all(finite(x) for x in value)
    # Return the negation of whether value has type float or whether value contains finite numeric values to the
    # caller.
    return not isinstance(value, float) or math.isfinite(value)

# Classify using the inputs and processing steps below.
# Input metrics: the supplied metrics.
# Input integrity: the supplied integrity.
# Input error: the supplied error.
# Output: return the value selected by the matching return branch below.
# Processing: select branches using the stated conditions.
def classify(metrics, integrity, error=None):
    # Run this branch when the negation of 'valid' from integrity; use False if absent or the negation of the
    # result of finite(metrics).
    if not integrity.get("valid", False) or not finite(metrics):
        # Return the text 'INVALID_EXPERIMENT' to the caller.
        return "INVALID_EXPERIMENT"
    # Run this branch when 'collision_count' from metrics; use 0 if absent or 'blocked_zone_violation_count' from
    # metrics; use 0 if absent.
    if metrics.get("collision_count", 0) or metrics.get("blocked_zone_violation_count", 0):
        # Return the text 'UNSAFE_FAILURE' to the caller.
        return "UNSAFE_FAILURE"
    # Run this branch when error.
    if error:
        # Return the text 'INVALID_EXPERIMENT' to the caller.
        return "INVALID_EXPERIMENT"
    # Run this branch when 'unfinished_vehicles' from metrics; use 0 if absent or 'timeout' from metrics; use
    # False if absent.
    if metrics.get("unfinished_vehicles", 0) or metrics.get("timeout", False):
        # Return the text 'SAFE_DEGRADATION' to the caller.
        return "SAFE_DEGRADATION"
    # Return the text 'PASS' to the caller.
    return "PASS"

# Keep invalid measurements archivable as N/A, never fabricated zeros.
# Input value: the supplied value.
# Output: return the value selected by the matching return branch below.
# Processing: select branches using the stated conditions.
def normalize_nonfinite(value):
    """Keep invalid measurements archivable as N/A, never fabricated zeros."""
    # Run this branch when whether value has type dict.
    if isinstance(value, dict):
        # Return a dictionary of k mapped to the result of normalize_nonfinite(v) for (k, v) in key/value pairs
        # from value to the caller.
        return {k: normalize_nonfinite(v) for k, v in value.items()}
    # Run this branch when whether value has type a tuple containing tuple, list.
    if isinstance(value, (tuple, list)):
        # Return a list of the result of normalize_nonfinite(v) for v in value to the caller.
        return [normalize_nonfinite(v) for v in value]
    # Return None when whether value has type float and the negation of whether value contains finite numeric
    # values, otherwise value to the caller.
    return None if isinstance(value, float) and not math.isfinite(value) else value
