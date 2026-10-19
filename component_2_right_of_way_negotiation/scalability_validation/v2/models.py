"""Separate immutable manifest, evidence validation and conservative verdicts."""
import json
import platform
import xml.etree.ElementTree as ET
from pathlib import Path
from dataclasses import asdict
from config import SIM_TIME_STEP, DEADLOCK_DURATION_SECONDS
from post_training_evaluation.models import digest, file_hash, write_json, POLICY, EXPECTED_POLICY_HASH, finite
from post_training_evaluation.scenarios import source_identities, sumo_version
from targeted_validation.models import METRIC_DEFINITIONS, panel_sources
from .cases import CASES, BUDGET, HEADWAY, INTERARRIVAL, MOVEMENTS, PHASE, template, frozen_cases

ROOT = Path("results/scalability_validation/v2")
PROTOCOL = "SCALABILITY_VALIDATION_V2"
INSERTION_TOLERANCE = 2 * SIM_TIME_STEP

def sources():
    base = Path(__file__).resolve().parents[2]
    return {str(p.relative_to(base)).replace("\\", "/"): file_hash(p)
            for p in sorted((base / "scalability_validation" / "v2").glob("*.py"))}

def geometry():
    network = ET.parse("networks/intersection.net.xml")
    vehicle = ET.parse("networks/intersection.rou.xml").find("vType[@id='AV']")
    length, gap = float(vehicle.get("length")), float(vehicle.get("minGap"))
    lanes = {a: float(network.find(f".//lane[@id='{a.lower()}_in_0']").get("length")) for a in "NESW"}
    return dict(incoming_lane_lengths_metres=lanes, vehicle_length_metres=length,
                minimum_gap_metres=gap,
                static_storage_vehicles_per_approach={a: int((v + gap) // (length + gap)) for a, v in lanes.items()},
                caveat="Static jam-storage estimate, not guaranteed dynamic insertion at departSpeed=max.")

def design():
    if file_hash(POLICY) != EXPECTED_POLICY_HASH:
        raise RuntimeError("FROZEN_E5_CHECKPOINT_MISMATCH")
    return dict(protocol_id=PROTOCOL, schema_version=1, policy_sha256=EXPECTED_POLICY_HASH,
        source_identities=source_identities(), study_sources=sources(), panel_sources=panel_sources(),
        python_version=platform.python_version(), sumo_version=sumo_version(),
        cases=frozen_cases(), demand_sequence=[asdict(row) for row in template()],
        arrival_rule="Ordered NESW round robin: demand index k departs at round(k * 0.4, 10) seconds, k=0..39; exact prefix per load.",
        interarrival_seconds=INTERARRIVAL, per_approach_headway_seconds=HEADWAY,
        parent_evidence="SCALABILITY_VALIDATION_V1 synchronized demand and all recorded evidence preserved unchanged.",
        objective="Measure increasing total traffic load while avoiding artificially synchronized initial four-way departures as a common confound. Staggered departures do not guarantee separated junction arrivals or liveness.",
        movement_rule=dict(cycle=list(MOVEMENTS), approach_phase_offsets=PHASE), budget_rule=f"Fixed {BUDGET} simulated seconds per scientific case.",
        scientific_episode_count=7, maximum_simulated_seconds=7*BUDGET,
        preflight="One separate SV-04 episode, maximum 180 s; PREFLIGHT_NOT_SCIENTIFIC_RESULT.",
        action_seed_rule="Shared across loads: SHA256(protocol_id, scalability_prefix_family, None, PROPOSED_MAPPO) modulo 2**31. SUMO seed 0.",
        geometry=geometry(), insertion_delay_tolerance_seconds=INSERTION_TOLERANCE,
        metric_definitions={**METRIC_DEFINITIONS,
            "spawn": "Scheduled, physically departed, completed and pending are separate; raw spawn delay = observed departure minus requested time. Delayed count exceeds two simulation steps; never-spawned separate.",
            "completion_rates": "Report completed/scheduled AND completed/spawned (N/A if no spawn).",
            "capacity": "Requires pending due demand, full static lane storage continuously for existing 15-s duration, and no observed SAFE_HOLD/BLOCKED_BY_PRECEDENCE on that approach. Controller backpressure and indeterminate insertion remain explicit; pending alone never proves capacity.",
            "spawned_TTT": "Sum of physical departure-to-exit/stop exposure for spawned vehicles only; original scheduled-demand team exposure also retained and labeled."},
        classification_rules={
            "INVALID_EXPERIMENT": "Invalid/missing evidence, any guard breach, changed sources/weights, runtime error, >4 participants.",
            "UNSAFE_FAILURE": "Valid experiment with collision or blocked-zone violation.",
            "PASS": "Integrity valid, safe and all scheduled vehicles complete.",
            "NETWORK_CAPACITY_LIMIT": "Safe, valid, incomplete with demonstrable primary insertion/storage limitation under frozen capacity predicate.",
            "SAFE_DEGRADATION": "Safe, valid, incomplete; observed control blockage or indeterminate insertion explicitly described, never unspawned negotiation failure."},
        early_stop="Unmodified PanelTelemetry exact stationary-all-held criterion AND all demand spawned; collisions, blocked-zone violation, all-completed, or hard budget. Existing 15-s threshold.",
        inference_mode="SEEDED_STOCHASTIC_MASKED_SAMPLE with one fixed common action seed; not argmax or multi-seed inference.",
        scope="Seven targeted observations in one AV-only SUMO intersection; no statistical universal capacity claim; no panel evidence replacement.")

def protect(root):
    root = Path(root).resolve()
    results = Path(__file__).resolve().parents[2] / "results"
    for name in ("targeted_validation", "targeted_validation_archives", "post_training_evaluation", "repair_diagnostics", "scalability_validation/v1", "scalability_validation_archives",
                 "panel_validation", "panel_validation_archives", "final_evaluation"):
        forbidden = (results / name).resolve()
        if root == forbidden or forbidden in root.parents:
            raise RuntimeError("EXISTING_EVIDENCE_READ_ONLY")

def read_manifest(root=ROOT):
    saved = json.loads((Path(root)/"manifest.json").read_text())
    if digest(saved["manifest"]) != saved["manifest_hash"]:
        raise RuntimeError("SCALABILITY_MANIFEST_CHECKSUM_MISMATCH")
    return saved

def prepare(root=ROOT):
    protect(root)
    current = json.loads(json.dumps(design()))
    path = Path(root)/"manifest.json"
    if path.exists():
        saved = read_manifest(root)
        if saved["manifest"] != current:
            raise RuntimeError("SCALABILITY_MANIFEST_CHANGED: restore frozen implementation; no silent version replacement")
        return saved
    frozen = dict(manifest=current, manifest_hash=digest(current))
    write_json(path, frozen, exclusive=True)
    return frozen

def classify(metrics, integrity, error=None):
    counters = ("training_operations", "backward_calls", "optimizer_steps", "parameter_updates", "centralized_critic_runtime_calls", "global_execution_calls")
    if (not integrity.get("valid") or not finite(metrics) or not integrity.get("policy_hash_unchanged")
        or not integrity.get("decentralized_execution") or integrity.get("centralized_execution_graph_used_for_control", True)
        or any(integrity.get(k, 0) for k in counters) or metrics.get("maximum_negotiation_participants", 5) > 4):
        return "INVALID_EXPERIMENT"
    if metrics.get("collision_count", 0) or metrics.get("blocked_zone_violation_count", 0):
        return "UNSAFE_FAILURE"
    if error:
        return "INVALID_EXPERIMENT"
    if metrics["total_vehicles_completed"] == metrics["total_vehicles_scheduled"]:
        return "PASS"
    if metrics.get("primary_network_capacity_limit_demonstrated", False):
        return "NETWORK_CAPACITY_LIMIT"
    return "SAFE_DEGRADATION"

def checked_json(path, key):
    value = json.loads(path.read_text())
    checksum = json.loads(path.with_name(path.stem+".sha256.json").read_text())[key]
    if checksum != digest(value):
        raise RuntimeError("SCALABILITY_EVIDENCE_CHECKSUM_MISMATCH")
    return value

def records(root=ROOT, suite="scalability"):
    frozen = read_manifest(root)
    found = []
    for path in sorted((Path(root)/"runs").glob("*/study_result.json")):
        value = checked_json(path, "study_result_hash")
        if value["suite"] != suite:
            continue
        if value["manifest_hash"] != frozen["manifest_hash"]:
            raise RuntimeError("SCALABILITY_RESULT_MANIFEST_MISMATCH")
        if not value.get("interrupted"):
            raw = checked_json(path.with_name("result.json"), "result_hash")
            provenance = checked_json(path.with_name("provenance.json"), "provenance_hash")
            case = next(c for c in frozen["manifest"]["cases"] if c["case_id"] == value["scenario_id"])
            if (provenance["schedule"] != case["schedule"] or raw["schedule_hash"] != digest(case["schedule"])
                or provenance["manifest_hash"] != frozen["manifest_hash"] or raw["manifest_hash"] != frozen["manifest_hash"]
                or value["raw_result_hash"] != digest(raw)):
                raise RuntimeError("SCALABILITY_PROVENANCE_MISMATCH")
            if (value["metrics"] != raw["metrics"] or value["integrity"] != raw["integrity"]
                or value["classification"] != classify(raw["metrics"],raw["integrity"],raw["error"])):
                raise RuntimeError("SCALABILITY_DERIVED_EVIDENCE_MISMATCH")
            for name, sha in raw["artifact_sha256"].items():
                if Path(name).name != name or file_hash(path.parent/name) != sha:
                    raise RuntimeError("SCALABILITY_ARTIFACT_MISMATCH")
        found.append(value)
    ids = [r["scenario_id"] for r in found]
    if len(set(ids)) != len(ids):
        raise RuntimeError("DUPLICATE_SCALABILITY_EPISODES")
    return found
