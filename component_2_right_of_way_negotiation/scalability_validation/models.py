"""Separate immutable manifest, evidence validation and conservative verdicts."""
# Import json for use in this module.
import json
# Import platform for use in this module.
import platform
# Import xml.etree.ElementTree as ET for use in this module.
import xml.etree.ElementTree as ET
# Import Path from pathlib for the operations below.
from pathlib import Path
# Import asdict from dataclasses for the operations below.
from dataclasses import asdict
# Import SIM_TIME_STEP, DEADLOCK_DURATION_SECONDS from config for the operations below.
from config import SIM_TIME_STEP, DEADLOCK_DURATION_SECONDS
# Import digest, file_hash, write_json, POLICY, EXPECTED_POLICY_HASH, finite from post_training_evaluation.models
# for the operations below.
from post_training_evaluation.models import digest, file_hash, write_json, POLICY, EXPECTED_POLICY_HASH, finite
# Import source_identities, sumo_version from post_training_evaluation.scenarios for the operations below.
from post_training_evaluation.scenarios import source_identities, sumo_version
# Import METRIC_DEFINITIONS, panel_sources from targeted_validation.models for the operations below.
from targeted_validation.models import METRIC_DEFINITIONS, panel_sources
# Import CASES, BUDGET, HEADWAY, MOVEMENTS, PHASE, template, frozen_cases from .cases for the operations below.
from .cases import CASES, BUDGET, HEADWAY, MOVEMENTS, PHASE, template, frozen_cases

# Set ROOT to the result of Path(the text 'results/scalability_validation/v1').
ROOT = Path("results/scalability_validation/v1")
# Set PROTOCOL to the text 'SCALABILITY_VALIDATION_V1'.
PROTOCOL = "SCALABILITY_VALIDATION_V1"
# Set INSERTION_TOLERANCE to 2 multiplied by SIM_TIME_STEP.
INSERTION_TOLERANCE = 2 * SIM_TIME_STEP

# Sources using the inputs and processing steps below.
# Output: a dictionary of the result of str(p.relative_to(base)).replace(the text '\\', the text '/') mapped to
# the result of file_hash(p) for p in the sorted values from the result of (base /...
def sources():
    # Set base to Path(__file__).resolve().parents at 1.
    base = Path(__file__).resolve().parents[1]
    # Return a dictionary of the result of str(p.relative_to(base)).replace(the text '\\', the text '/') mapped to
    # the result of file_hash(p) for p in the sorted values from the result of (base /
    # 'scalability_validation').glob(the text '*.py') to the caller.
    return {str(p.relative_to(base)).replace("\\", "/"): file_hash(p)
            # Evaluate the sorted values from the result of (base / 'scalability_validation').glob(the text
            # '*.py') as part of the enclosing expression.
            for p in sorted((base / "scalability_validation").glob("*.py"))}

# Geometry using the inputs and processing steps below.
# Output: a dictionary built from the supplied values.
def geometry():
    # Set network to the result of ET.parse(the text 'networks/intersection.net.xml').
    network = ET.parse("networks/intersection.net.xml")
    # Set vehicle to the result of ET.parse('networks/intersection.rou.xml').find(the text "vType[@id='AV']").
    vehicle = ET.parse("networks/intersection.rou.xml").find("vType[@id='AV']")
    # Set (length, gap) to a tuple containing a floating-point number built from 'length' from vehicle; use None
    # if absent, a floating-point number...
    length, gap = float(vehicle.get("length")), float(vehicle.get("minGap"))
    # Set lanes to a dictionary of a mapped to a floating-point number built from 'length' from
    # network.find(f".//lane[@id='{a.lower()}_in_0']"); use None if absent for a in the text 'NESW'.
    lanes = {a: float(network.find(f".//lane[@id='{a.lower()}_in_0']").get("length")) for a in "NESW"}
    # Return a dictionary built from the supplied values to the caller.
    return dict(incoming_lane_lengths_metres=lanes, vehicle_length_metres=length,
                # Supply minimum_gap_metres as gap.
                minimum_gap_metres=gap,
                # Supply static_storage_vehicles_per_approach as a dictionary of a mapped to an integer built from
                # v plus gap integer-divided by length plus gap for (a, v) in key/value pairs from lanes.
                static_storage_vehicles_per_approach={a: int((v + gap) // (length + gap)) for a, v in lanes.items()},
                # Supply caveat as the text 'Static jam-storage estimate, not guaranteed dynamic insertion...'.
                caveat="Static jam-storage estimate, not guaranteed dynamic insertion at departSpeed=max.")

# Design using the inputs and processing steps below.
# Output: a dictionary built from the supplied values.
# Processing: select branches using the stated conditions.
def design():
    # Run this branch when the result of file_hash(POLICY) differs from EXPECTED_POLICY_HASH.
    if file_hash(POLICY) != EXPECTED_POLICY_HASH:
        # Raise RuntimeError with the text 'FROZEN_E5_CHECKPOINT_MISMATCH' to stop this execution path.
        raise RuntimeError("FROZEN_E5_CHECKPOINT_MISMATCH")
    # Return a dictionary built from the supplied values to the caller.
    return dict(protocol_id=PROTOCOL, schema_version=1, policy_sha256=EXPECTED_POLICY_HASH,
        # Supply source_identities as the result of source_identities().
        # Supply study_sources as the result of sources().
        # Supply panel_sources as the result of panel_sources().
        source_identities=source_identities(), study_sources=sources(), panel_sources=panel_sources(),
        # Supply python_version as the result of platform.python_version().
        # Supply sumo_version as the result of sumo_version().
        python_version=platform.python_version(), sumo_version=sumo_version(),
        # Supply cases as the result of frozen_cases().
        # Supply demand_sequence as a list of the result of asdict(row) for row in the result of template().
        cases=frozen_cases(), demand_sequence=[asdict(row) for row in template()],
        # Supply arrival_rule as formatted text built from the embedded values.
        arrival_rule=f"Round i departs simultaneously on NESW at {HEADWAY}*i seconds; prefix in round/NESW order.",
        # Supply movement_rule as a dictionary built from the supplied values.
        # Supply budget_rule as formatted text built from the embedded values.
        # Supply cycle as a list built from MOVEMENTS.
        # Supply approach_phase_offsets as PHASE.
        movement_rule=dict(cycle=list(MOVEMENTS), approach_phase_offsets=PHASE), budget_rule=f"Fixed {BUDGET} simulated seconds per scientific case.",
        # Supply scientific_episode_count as 7.
        # Supply maximum_simulated_seconds as 7 multiplied by BUDGET.
        scientific_episode_count=7, maximum_simulated_seconds=7*BUDGET,
        # Supply preflight as the text 'One separate SV-04 episode, maximum 180 s;...'.
        preflight="One separate SV-04 episode, maximum 180 s; PREFLIGHT_NOT_SCIENTIFIC_RESULT.",
        # Supply action_seed_rule as the text 'Shared across loads: SHA256(protocol_id,...'.
        action_seed_rule="Shared across loads: SHA256(protocol_id, scalability_prefix_family, None, PROPOSED_MAPPO) modulo 2**31. SUMO seed 0.",
        # Supply geometry as the result of geometry().
        # Supply insertion_delay_tolerance_seconds as INSERTION_TOLERANCE.
        geometry=geometry(), insertion_delay_tolerance_seconds=INSERTION_TOLERANCE,
        # Supply metric_definitions as a dictionary containing spawn, completion_rates, capacity, spawned_TTT.
        metric_definitions={**METRIC_DEFINITIONS,
            "spawn": "Scheduled, physically departed, completed and pending are separate; raw spawn delay = observed departure minus requested time. Delayed count exceeds two simulation steps; never-spawned separate.",
            "completion_rates": "Report completed/scheduled AND completed/spawned (N/A if no spawn).",
            "capacity": "Requires pending due demand, full static lane storage continuously for existing 15-s duration, and no observed SAFE_HOLD/BLOCKED_BY_PRECEDENCE on that approach. Controller backpressure and indeterminate insertion remain explicit; pending alone never proves capacity.",
            "spawned_TTT": "Sum of physical departure-to-exit/stop exposure for spawned vehicles only; original scheduled-demand team exposure also retained and labeled."},
        # Supply classification_rules as a dictionary containing INVALID_EXPERIMENT, UNSAFE_FAILURE, PASS,
        # NETWORK_CAPACITY_LIMIT, SAFE_DEGRADATION.
        classification_rules={
            "INVALID_EXPERIMENT": "Invalid/missing evidence, any guard breach, changed sources/weights, runtime error, >4 participants.",
            "UNSAFE_FAILURE": "Valid experiment with collision or blocked-zone violation.",
            "PASS": "Integrity valid, safe and all scheduled vehicles complete.",
            "NETWORK_CAPACITY_LIMIT": "Safe, valid, incomplete with demonstrable primary insertion/storage limitation under frozen capacity predicate.",
            "SAFE_DEGRADATION": "Safe, valid, incomplete; observed control blockage or indeterminate insertion explicitly described, never unspawned negotiation failure."},
        # Supply early_stop as the text 'Unmodified PanelTelemetry exact stationary-all-held criterion...'.
        early_stop="Unmodified PanelTelemetry exact stationary-all-held criterion AND all demand spawned; collisions, blocked-zone violation, all-completed, or hard budget. Existing 15-s threshold.",
        # Supply inference_mode as the text 'SEEDED_STOCHASTIC_MASKED_SAMPLE with one fixed common action...'.
        inference_mode="SEEDED_STOCHASTIC_MASKED_SAMPLE with one fixed common action seed; not argmax or multi-seed inference.",
        # Supply scope as the text 'Seven targeted observations in one AV-only SUMO intersection;...'.
        scope="Seven targeted observations in one AV-only SUMO intersection; no statistical universal capacity claim; no panel evidence replacement.")

# Protect using the inputs and processing steps below.
# Input root: the base directory used to resolve files.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def protect(root):
    # Set root to the result of Path(root).resolve().
    root = Path(root).resolve()
    # Set results to Path(__file__).resolve().parents at 1 joined with the path segment 'results'.
    results = Path(__file__).resolve().parents[1] / "results"
    # Iterate over a tuple containing the text 'targeted_validation', the text 'targeted_validation_archives', the
    # text..., binding each item to name.
    for name in ("targeted_validation", "targeted_validation_archives", "post_training_evaluation", "repair_diagnostics",
                 "panel_validation", "panel_validation_archives", "final_evaluation"):
        # Set forbidden to the result of (results / name).resolve().
        forbidden = (results / name).resolve()
        # Run this branch when root equals forbidden or forbidden belongs to root.parents.
        if root == forbidden or forbidden in root.parents:
            # Raise RuntimeError with the text 'EXISTING_EVIDENCE_READ_ONLY' to stop this execution path.
            raise RuntimeError("EXISTING_EVIDENCE_READ_ONLY")

# Read manifest using the inputs and processing steps below.
# Input root: the base directory used to resolve files.
# Output: saved.
# Processing: select branches using the stated conditions.
def read_manifest(root=ROOT):
    # Set saved to the decoded data produced by json.loads from the text read from (Path(root) / 'manifest.json').
    saved = json.loads((Path(root)/"manifest.json").read_text())
    # Run this branch when the result of digest(saved at 'manifest') differs from saved at 'manifest_hash'.
    if digest(saved["manifest"]) != saved["manifest_hash"]:
        # Raise RuntimeError with the text 'SCALABILITY_MANIFEST_CHECKSUM_MISMATCH' to stop this execution path.
        raise RuntimeError("SCALABILITY_MANIFEST_CHECKSUM_MISMATCH")
    # Return saved to the caller.
    return saved

# Prepare using the inputs and processing steps below.
# Input root: the base directory used to resolve files.
# Output: return the value selected by the matching return branch below.
# Processing: select branches using the stated conditions.
def prepare(root=ROOT):
    # Call protect with the supplied arguments.
    protect(root)
    # Set current to the decoded data produced by json.loads from the serialized data produced by json.dumps.
    current = json.loads(json.dumps(design()))
    # Set path to the result of Path(root) joined with the path segment 'manifest.json'.
    path = Path(root)/"manifest.json"
    # Run this branch when whether path exists.
    if path.exists():
        # Set saved to the result of read_manifest(root).
        saved = read_manifest(root)
        # Run this branch when saved at 'manifest' differs from current.
        if saved["manifest"] != current:
            # Raise RuntimeError with the text 'SCALABILITY_MANIFEST_CHANGED: restore frozen implementation;...'
            # to stop this execution path.
            raise RuntimeError("SCALABILITY_MANIFEST_CHANGED: restore frozen implementation; no silent version replacement")
        # Return saved to the caller.
        return saved
    # Set frozen to a dictionary built from the supplied values.
    frozen = dict(manifest=current, manifest_hash=digest(current))
    # Call write_json with the supplied arguments.
    write_json(path, frozen, exclusive=True)
    # Return frozen to the caller.
    return frozen

# Classify using the inputs and processing steps below.
# Input metrics: the supplied metrics.
# Input integrity: the supplied integrity.
# Input error: the supplied error.
# Output: return the value selected by the matching return branch below.
# Processing: select branches using the stated conditions.
def classify(metrics, integrity, error=None):
    # Set counters to a tuple containing the text 'training_operations', the text 'backward_calls', the text
    # 'optimizer_steps', the text...
    counters = ("training_operations", "backward_calls", "optimizer_steps", "parameter_updates", "centralized_critic_runtime_calls", "global_execution_calls")
    # Run this branch when the negation of 'valid' from integrity; use None if absent or the negation of the
    # result of finite(metrics) or the negation of 'policy_hash_unchanged' from integrity; use None if absent or
    # the negation of 'decentralized_execution' from integrity; use None if absent or
    # 'centralized_execution_graph_used_for_control' from integrity; use True if absent or whether any item is
    # true in a lazy sequence of k from integrity; use 0 if absent for k in counters or
    # 'maximum_negotiation_participants' from metrics; use 5 if absent is greater than 4.
    if (not integrity.get("valid") or not finite(metrics) or not integrity.get("policy_hash_unchanged")
        # Evaluate 'centralized_execution_graph_used_for_control' from integrity; use True if absent as part of
        # the enclosing expression.
        or not integrity.get("decentralized_execution") or integrity.get("centralized_execution_graph_used_for_control", True)
        # Evaluate 'maximum_negotiation_participants' from metrics; use 5 if absent is greater than 4 as part of
        # the enclosing expression.
        or any(integrity.get(k, 0) for k in counters) or metrics.get("maximum_negotiation_participants", 5) > 4):
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
    # Run this branch when metrics at 'total_vehicles_completed' equals metrics at 'total_vehicles_scheduled'.
    if metrics["total_vehicles_completed"] == metrics["total_vehicles_scheduled"]:
        # Return the text 'PASS' to the caller.
        return "PASS"
    # Run this branch when 'primary_network_capacity_limit_demonstrated' from metrics; use False if absent.
    if metrics.get("primary_network_capacity_limit_demonstrated", False):
        # Return the text 'NETWORK_CAPACITY_LIMIT' to the caller.
        return "NETWORK_CAPACITY_LIMIT"
    # Return the text 'SAFE_DEGRADATION' to the caller.
    return "SAFE_DEGRADATION"

# Checked json using the inputs and processing steps below.
# Input path: the path or path object supplied by the caller.
# Input key: the supplied key.
# Output: value.
# Processing: select branches using the stated conditions.
def checked_json(path, key):
    # Set value to the decoded data produced by json.loads from the text read from path.
    value = json.loads(path.read_text())
    # Set checksum to json.loads(path.with_name(path.stem + '.sha256.json').read_text()) at key.
    checksum = json.loads(path.with_name(path.stem+".sha256.json").read_text())[key]
    # Run this branch when checksum differs from the result of digest(value).
    if checksum != digest(value):
        # Raise RuntimeError with the text 'SCALABILITY_EVIDENCE_CHECKSUM_MISMATCH' to stop this execution path.
        raise RuntimeError("SCALABILITY_EVIDENCE_CHECKSUM_MISMATCH")
    # Return value to the caller.
    return value

# Records using the inputs and processing steps below.
# Input root: the base directory used to resolve files.
# Input suite: the supplied suite.
# Output: found.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def records(root=ROOT, suite="scalability"):
    # Set frozen to the result of read_manifest(root).
    frozen = read_manifest(root)
    # Set found to an empty list.
    found = []
    # Iterate over the sorted values from the result of (Path(root) / 'runs').glob(the text
    # '*/study_result.json'), binding each item to path.
    for path in sorted((Path(root)/"runs").glob("*/study_result.json")):
        # Set value to the result of checked_json(path, the text 'study_result_hash').
        value = checked_json(path, "study_result_hash")
        # Run this branch when value at 'suite' differs from suite.
        if value["suite"] != suite:
            # Skip the rest of this loop iteration and process the next item.
            continue
        # Run this branch when value at 'manifest_hash' differs from frozen at 'manifest_hash'.
        if value["manifest_hash"] != frozen["manifest_hash"]:
            # Raise RuntimeError with the text 'SCALABILITY_RESULT_MANIFEST_MISMATCH' to stop this execution path.
            raise RuntimeError("SCALABILITY_RESULT_MANIFEST_MISMATCH")
        # Run this branch when the negation of 'interrupted' from value; use None if absent.
        if not value.get("interrupted"):
            # Set raw to the result of checked_json(the result of path.with_name(the text 'result.json'), the text
            # 'result_hash').
            raw = checked_json(path.with_name("result.json"), "result_hash")
            # Set provenance to the result of checked_json(the result of path.with_name(the text
            # 'provenance.json'), the text 'provenance_hash').
            provenance = checked_json(path.with_name("provenance.json"), "provenance_hash")
            # Set case to the next item from a lazy sequence of c for c in frozen['manifest'] at 'cases'; retain
            # entries satisfying c at 'case_id' equals value at 'scenario_id'.
            case = next(c for c in frozen["manifest"]["cases"] if c["case_id"] == value["scenario_id"])
            # Run this branch when provenance at 'schedule' differs from case at 'schedule' or raw at
            # 'schedule_hash' differs from the result of digest(case at 'schedule') or provenance at
            # 'manifest_hash' differs from frozen at 'manifest_hash' or raw at 'manifest_hash' differs from frozen
            # at 'manifest_hash' or value at 'raw_result_hash' differs from the result of digest(raw).
            if (provenance["schedule"] != case["schedule"] or raw["schedule_hash"] != digest(case["schedule"])
                # Evaluate provenance at 'manifest_hash' differs from frozen at 'manifest_hash' as part of the
                # enclosing expression.
                or provenance["manifest_hash"] != frozen["manifest_hash"] or raw["manifest_hash"] != frozen["manifest_hash"]
                # Evaluate value at 'raw_result_hash' differs from the result of digest(raw) as part of the
                # enclosing expression.
                or value["raw_result_hash"] != digest(raw)):
                # Raise RuntimeError with the text 'SCALABILITY_PROVENANCE_MISMATCH' to stop this execution path.
                raise RuntimeError("SCALABILITY_PROVENANCE_MISMATCH")
            # Run this branch when value at 'metrics' differs from raw at 'metrics' or value at 'integrity'
            # differs from raw at 'integrity' or value at 'classification' differs from the result of classify(raw
            # at 'metrics', raw at 'integrity', raw at 'error').
            if (value["metrics"] != raw["metrics"] or value["integrity"] != raw["integrity"]
                # Evaluate value at 'classification' differs from the result of classify(raw at 'metrics', raw at
                # 'integrity', raw at 'error') as part of the enclosing expression.
                or value["classification"] != classify(raw["metrics"],raw["integrity"],raw["error"])):
                # Raise RuntimeError with the text 'SCALABILITY_DERIVED_EVIDENCE_MISMATCH' to stop this execution
                # path.
                raise RuntimeError("SCALABILITY_DERIVED_EVIDENCE_MISMATCH")
            # Iterate over key/value pairs from raw['artifact_sha256'], binding each item to (name, sha).
            for name, sha in raw["artifact_sha256"].items():
                # Run this branch when Path(name).name differs from name or the result of file_hash(path.parent
                # divided by name) differs from sha.
                if Path(name).name != name or file_hash(path.parent/name) != sha:
                    # Raise RuntimeError with the text 'SCALABILITY_ARTIFACT_MISMATCH' to stop this execution
                    # path.
                    raise RuntimeError("SCALABILITY_ARTIFACT_MISMATCH")
        # Append value to found.
        found.append(value)
    # Set ids to a list of r at 'scenario_id' for r in found.
    ids = [r["scenario_id"] for r in found]
    # Run this branch when the number of entries in a set built from ids differs from the number of entries in
    # ids.
    if len(set(ids)) != len(ids):
        # Raise RuntimeError with the text 'DUPLICATE_SCALABILITY_EPISODES' to stop this execution path.
        raise RuntimeError("DUPLICATE_SCALABILITY_EPISODES")
    # Return found to the caller.
    return found
