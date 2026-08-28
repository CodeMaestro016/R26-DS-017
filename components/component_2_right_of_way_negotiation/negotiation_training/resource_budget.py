"""Step 5J.3C.2E.1 resource evidence and fixed-horizon derivation."""

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping, Optional, Tuple

from config import EPISODE_STEPS
from experimentation import ScenarioRole, build_design


SOURCE_PROTOCOL_PATH = Path("results/mappo_predeclared_selection_protocol.json")
EXTENDED_EVIDENCE_PATH = Path(
    "results/mappo_extended_learning_curve_evidence.json")
PILOT_EVIDENCE_PATH = Path("results/mappo_closed_loop_pilot_evidence.json")
INPUT_PATH = Path("research_inputs/mappo_selection_external_inputs.json")
RESOLUTION_PATH = Path("results/mappo_training_resource_budget_resolution.json")
V2_PATH = Path("results/mappo_selection_protocol_v2.json")

EXPECTED_V1_ID = (
    "MAPPO_SELECTION_PROTOCOL_V1",
    "cc2ac385d9ac8134f621f792a037700d5fb1dfaee74ef2f0f8317ecef3e3331e")
ALLOWED_BUDGET_TYPES = (
    "PPO_UPDATE_CYCLES_PER_REPLICATION",
    "TRAINING_MANIFEST_COLLECTIONS_PER_REPLICATION",
    "SUMO_STEPS_PER_REPLICATION",
    "WALL_CLOCK_SECONDS_PER_REPLICATION")
ALLOWED_APPROVALS = ("PROJECT_APPROVED", "SUPERVISOR_APPROVED")
EXPECTED_UNITS = {
    "PPO_UPDATE_CYCLES_PER_REPLICATION": "PPO-update-cycles",
    "TRAINING_MANIFEST_COLLECTIONS_PER_REPLICATION":
        "TRAINING-manifest-collections",
    "SUMO_STEPS_PER_REPLICATION": "SUMO-steps",
    "WALL_CLOCK_SECONDS_PER_REPLICATION": "seconds"}
REMAINING_INPUT_ORDER = (
    "MINIMUM_PRACTICALLY_IMPORTANT_DIFFERENCE_TEAM_TRAVEL_TIME_SECONDS",
    "STATISTICAL_CONFIDENCE_OR_PRECISION_TARGET",
    "STATISTICAL_POWER_TARGET",
    "UNCERTAINTY_MONTE_CARLO_RESOLUTION",
    "MULTIPLE_COMPARISON_CONTROL",
    "CANDIDATE_SEARCH_SEQUENCE")


@dataclass(frozen=True)
class TrainingResourceBudgetInput:
    input_id: tuple
    scope: str
    budget_type: Optional[str]
    budget_value: Optional[float]
    unit: Optional[str]
    justification_source: Optional[str]
    approval_status: str
    provenance: Tuple[Tuple[str, Any], ...]


@dataclass(frozen=True)
class TrainingResourceEvidence:
    training_manifest_scenario_count: int
    steps_per_scenario: int
    sumo_steps_per_training_manifest: int
    observed_manifest_runtime_values: tuple
    observed_update_runtime_values: tuple
    observed_replication_overhead_values: tuple
    manifest_runtime_bound: float
    update_runtime_bound: float
    overhead_bound: float
    wall_clock_mapping_status: str
    source_artifact_ids: tuple
    performance_values_used: bool = False


@dataclass(frozen=True)
class TrainingResourceBudgetResolution:
    resolution_id: tuple
    source_protocol_id: tuple
    input_requirement_name: str
    resource_input: TrainingResourceBudgetInput
    resource_evidence: TrainingResourceEvidence
    derived_H: Optional[int]
    derived_policy_state_count: Optional[int]
    derived_manifest_collection_count: Optional[int]
    derived_sumo_steps_per_replication: Optional[int]
    derived_conservative_wall_clock_bound: Optional[float]
    unused_capacity: Optional[float]
    resource_budget_resolved: bool
    performance_used_to_choose_budget: bool
    performance_used_to_derive_H: bool
    project_selected: bool
    provenance: Tuple[Tuple[str, Any], ...]


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def load_and_validate_v1(path=SOURCE_PROTOCOL_PATH):
    source = json.loads(Path(path).read_text(encoding="utf-8"))
    if (source.get("checkpoint") != "STEP_5J_3C_2D" or
            source.get("status") !=
            "PREDECLARED_SELECTION_PROTOCOL_STRUCTURE_COMPLETE" or
            source.get("protocol_readiness") !=
            "STRUCTURE_DEFINED_EXTERNAL_INPUTS_REQUIRED" or
            tuple(source.get("protocol", {}).get("protocol_id", ())) !=
            EXPECTED_V1_ID or
            source.get("next_blocker") !=
            "MAXIMUM_ACCEPTABLE_TRAINING_RESOURCE_BUDGET"):
        raise ValueError("RESOURCE_BUDGET_SOURCE_PROTOCOL_INVALID")
    return source


def derive_resource_evidence(evidence_path=EXTENDED_EVIDENCE_PATH):
    evidence = json.loads(Path(evidence_path).read_text(encoding="utf-8"))
    if evidence.get("status") != "EXTENDED_MULTI_UPDATE_EVIDENCE_ACQUIRED":
        raise ValueError("RESOURCE_EVIDENCE_IDENTITY_INVALID")
    design = build_design()
    scenario_count = len(
        design["manifests"][ScenarioRole.TRAINING].scenario_ids)
    steps_per_manifest = scenario_count * EPISODE_STEPS
    manifest_runtimes, update_runtimes, overheads = [], [], []
    for replication in evidence["replications"]:
        states = replication["policy_states"]
        updates = replication["updates"]
        if (len(states) != 3 or any(
                state["sumo_step_count"] != steps_per_manifest
                for state in states)):
            raise ValueError("STRUCTURAL_SUMO_STEP_MAPPING_MISMATCH")
        state_times = [float(state["wall_clock_runtime_seconds"])
                       for state in states]
        update_times = [float(update["wall_clock_runtime_seconds"])
                        for update in updates]
        manifest_runtimes.extend(state_times)
        update_runtimes.extend(update_times)
        overhead = (float(replication["wall_clock_runtime_seconds"]) -
                    sum(state_times) - sum(update_times))
        if overhead < 0:
            raise ValueError("REPLICATION_OVERHEAD_NOT_DERIVABLE")
        overheads.append(overhead)
    if (evidence["compute_cost_evidence"]["total_sumo_steps"] !=
            len(evidence["replications"]) * len(
                evidence["replications"][0]["policy_states"]) *
            steps_per_manifest):
        raise ValueError("STRUCTURAL_SUMO_STEP_MAPPING_MISMATCH")
    return TrainingResourceEvidence(
        training_manifest_scenario_count=scenario_count,
        steps_per_scenario=EPISODE_STEPS,
        sumo_steps_per_training_manifest=steps_per_manifest,
        observed_manifest_runtime_values=tuple(manifest_runtimes),
        observed_update_runtime_values=tuple(update_runtimes),
        observed_replication_overhead_values=tuple(overheads),
        manifest_runtime_bound=max(manifest_runtimes),
        update_runtime_bound=max(update_runtimes),
        overhead_bound=max(overheads),
        wall_clock_mapping_status=
            "CONSERVATIVE_HISTORICAL_MAX_COMPONENT_MAPPING_AVAILABLE",
        source_artifact_ids=(
            tuple(evidence["evidence_tranche_identity"]),
            ("CLOSED_LOOP_PILOT_EVIDENCE_PATH",
             str(PILOT_EVIDENCE_PATH))),
        performance_values_used=False)


def load_resource_input(path=INPUT_PATH):
    raw = json.loads(Path(path).read_text(encoding="utf-8"))[
        "MAXIMUM_ACCEPTABLE_TRAINING_RESOURCE_BUDGET"]
    identity_fields = {key: raw.get(key) for key in (
        "status", "scope", "budget_type", "budget_value", "unit",
        "justification_source", "approval_status")}
    identity = ("TRAINING_RESOURCE_BUDGET_INPUT_V1",
                hashlib.sha256(_canonical(identity_fields).encode()).hexdigest())
    return TrainingResourceBudgetInput(
        input_id=identity, scope=raw.get("scope"),
        budget_type=raw.get("budget_type"),
        budget_value=raw.get("budget_value"), unit=raw.get("unit"),
        justification_source=raw.get("justification_source"),
        approval_status=raw.get("approval_status"),
        provenance=(("status", raw.get("status")),
                    ("source_path", str(path))))


def validate_resource_input(resource_input):
    status = dict(resource_input.provenance).get("status")
    if status == "UNRESOLVED":
        if any(value is not None for value in (
                resource_input.budget_type, resource_input.budget_value,
                resource_input.unit, resource_input.justification_source)) or \
                resource_input.approval_status != "NOT_SUPPLIED":
            return "RESOURCE_BUDGET_VALUE_PRESENT_BUT_NOT_JUSTIFIED"
        return "EXTERNAL_RESOURCE_BUDGET_NOT_SUPPLIED"
    if status != "RESOLVED":
        raise ValueError("RESOURCE_BUDGET_INPUT_STATUS_INVALID")
    if resource_input.scope != "PER_REPLICATION":
        raise ValueError("RESOURCE_BUDGET_SCOPE_MUST_BE_PER_REPLICATION")
    if resource_input.budget_type not in ALLOWED_BUDGET_TYPES:
        raise ValueError("RESOURCE_BUDGET_TYPE_INVALID")
    value = resource_input.budget_value
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
        raise ValueError("RESOURCE_BUDGET_VALUE_INVALID")
    if (resource_input.budget_type != "WALL_CLOCK_SECONDS_PER_REPLICATION" and
            (not isinstance(value, int) or isinstance(value, bool))):
        raise ValueError("STRUCTURAL_RESOURCE_BUDGET_MUST_BE_INTEGER")
    if not resource_input.unit or not resource_input.justification_source:
        return "RESOURCE_BUDGET_VALUE_PRESENT_BUT_NOT_JUSTIFIED"
    if resource_input.unit != EXPECTED_UNITS[resource_input.budget_type]:
        raise ValueError("RESOURCE_BUDGET_UNIT_MISMATCH")
    if resource_input.approval_status not in ALLOWED_APPROVALS:
        if resource_input.approval_status in (
                "AUTO_SELECTED", "PERFORMANCE_SELECTED",
                "INFERRED_FROM_C0_C1_C2", "CONVENTIONAL_DEFAULT"):
            raise ValueError("RESOURCE_BUDGET_APPROVAL_PROVENANCE_FORBIDDEN")
        return "RESOURCE_BUDGET_VALUE_PRESENT_BUT_NOT_JUSTIFIED"
    return "APPROVED_RESOURCE_BUDGET_VALID"


def derive_horizon(resource_input, evidence):
    budget = resource_input.budget_value
    kind = resource_input.budget_type
    unused = None
    if kind == "PPO_UPDATE_CYCLES_PER_REPLICATION":
        h = budget
    elif kind == "TRAINING_MANIFEST_COLLECTIONS_PER_REPLICATION":
        h = budget - 1
    elif kind == "SUMO_STEPS_PER_REPLICATION":
        h = math.floor(budget / evidence.sumo_steps_per_training_manifest) - 1
        unused = budget - (h + 1) * evidence.sumo_steps_per_training_manifest
    elif kind == "WALL_CLOCK_SECONDS_PER_REPLICATION":
        if evidence.wall_clock_mapping_status != \
                "CONSERVATIVE_HISTORICAL_MAX_COMPONENT_MAPPING_AVAILABLE":
            raise ValueError("WALL_CLOCK_RESOURCE_MAPPING_NOT_CONSERVATIVELY_DERIVABLE")
        h = math.floor((budget - evidence.manifest_runtime_bound -
                        evidence.overhead_bound) /
                       (evidence.manifest_runtime_bound +
                        evidence.update_runtime_bound))
        bound = ((h + 1) * evidence.manifest_runtime_bound +
                 h * evidence.update_runtime_bound + evidence.overhead_bound)
        unused = budget - bound
    else:
        raise ValueError("RESOURCE_BUDGET_TYPE_INVALID")
    if h < 1:
        raise ValueError("RESOURCE_BUDGET_TOO_SMALL_FOR_ONE_UPDATE")
    wall_bound = ((h + 1) * evidence.manifest_runtime_bound +
                  h * evidence.update_runtime_bound + evidence.overhead_bound)
    return int(h), unused, wall_bound


def _create_v2(v1, resource_input, evidence, h, wall_bound, output_path):
    protocol = json.loads(json.dumps(v1["protocol"]))
    protocol["training_budget_protocol"].update({
        "maximum_update_horizon_H": h,
        "resource_horizon_status": "RESOLVED_PROJECT_RESOURCE_CONSTRAINT",
        "policy_states": f"STATE_0_THROUGH_STATE_{h}_INCLUSIVE",
        "training_manifest_collections_per_replication": h + 1,
        "exact_sumo_steps_per_replication":
            (h + 1) * evidence.sumo_steps_per_training_manifest,
        "derived_conservative_wall_clock_bound_seconds": wall_bound,
        "resource_constraint_source": {
            "input_id": resource_input.input_id,
            "budget_type": resource_input.budget_type,
            "budget_value": resource_input.budget_value,
            "unit": resource_input.unit,
            "justification_source": resource_input.justification_source,
            "approval_status": resource_input.approval_status},
        "horizon_semantics":
            "DETERMINISTICALLY_DERIVED_FROM_PROJECT_RESOURCE_CONSTRAINT",
        "optimality_claim": False})
    protocol["unresolved_external_inputs"] = [
        item for item in protocol["unresolved_external_inputs"]
        if item["input_name"] !=
        "MAXIMUM_ACCEPTABLE_TRAINING_RESOURCE_BUDGET"]
    protocol["freeze_status"] = \
        "RESOURCE_BUDGET_RESOLVED_ADDITIONAL_EXTERNAL_INPUTS_UNRESOLVED"
    protocol.pop("protocol_id", None)
    digest = hashlib.sha256(_canonical(protocol).encode()).hexdigest()
    protocol_id = (
        "MAPPO_SELECTION_PROTOCOL_V2_RESOURCE_BUDGET_RESOLVED", digest)
    protocol["protocol_id"] = protocol_id
    artifact = {
        "checkpoint": "STEP_5J_3C_2E_1",
        "protocol_version": protocol_id[0],
        "protocol_readiness":
            "STRUCTURE_DEFINED_ADDITIONAL_EXTERNAL_INPUTS_REQUIRED",
        "protocol": protocol,
        "remaining_external_inputs": list(REMAINING_INPUT_ORDER)}
    Path(output_path).write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    return protocol_id


def resolve_training_resource_budget(
        source_protocol_path=SOURCE_PROTOCOL_PATH,
        external_input_path=INPUT_PATH,
        evidence_path=EXTENDED_EVIDENCE_PATH,
        resolution_path=RESOLUTION_PATH, v2_path=V2_PATH):
    v1 = load_and_validate_v1(source_protocol_path)
    evidence = derive_resource_evidence(evidence_path)
    resource_input = load_resource_input(external_input_path)
    input_status = validate_resource_input(resource_input)
    resolved = input_status == "APPROVED_RESOURCE_BUDGET_VALID"
    h = unused = wall_bound = protocol_id = None
    if resolved:
        h, unused, wall_bound = derive_horizon(resource_input, evidence)
        protocol_id = _create_v2(
            v1, resource_input, evidence, h, wall_bound, v2_path)
    resolution_fields = (
        EXPECTED_V1_ID, resource_input.input_id, asdict(evidence), h,
        resolved, input_status)
    resolution_id = (
        "TRAINING_RESOURCE_BUDGET_RESOLUTION_V1",
        hashlib.sha256(repr(resolution_fields).encode()).hexdigest())
    resolution = TrainingResourceBudgetResolution(
        resolution_id=resolution_id, source_protocol_id=EXPECTED_V1_ID,
        input_requirement_name="MAXIMUM_ACCEPTABLE_TRAINING_RESOURCE_BUDGET",
        resource_input=resource_input, resource_evidence=evidence,
        derived_H=h, derived_policy_state_count=h + 1 if resolved else None,
        derived_manifest_collection_count=h + 1 if resolved else None,
        derived_sumo_steps_per_replication=(
            (h + 1) * evidence.sumo_steps_per_training_manifest
            if resolved else None),
        derived_conservative_wall_clock_bound=wall_bound,
        unused_capacity=unused, resource_budget_resolved=resolved,
        performance_used_to_choose_budget=False,
        performance_used_to_derive_H=False,
        project_selected=resolved,
        provenance=(("checkpoint", "STEP_5J_3C_2E_1"),
                    ("input_validation_status", input_status)))
    artifact = {
        "checkpoint": "STEP_5J_3C_2E_1",
        "status": ("TRAINING_RESOURCE_BUDGET_RESOLVED" if resolved else
                   "TRAINING_RESOURCE_BUDGET_EXTERNAL_INPUT_REQUIRED"),
        "resource_budget_resolution_status": input_status,
        "resolution": asdict(resolution),
        "training_horizon_selected": resolved,
        "training_horizon_optimal_claim": False,
        "performance_used_to_choose_resource_budget": False,
        "performance_used_to_derive_H": False,
        "v1_modified": False,
        "new_protocol_identity_created": resolved,
        "new_v2_protocol_identity": protocol_id,
        "remaining_external_blockers": (
            list(REMAINING_INPUT_ORDER) if resolved else
            ["MAXIMUM_ACCEPTABLE_TRAINING_RESOURCE_BUDGET"] +
            list(REMAINING_INPUT_ORDER)),
        "new_sumo_executions": 0, "training_episodes": 0,
        "optimizer_invocations": 0, "backward_calls": 0,
        "parameter_updates": 0, "validation_executions": 0,
        "held_out_executions": 0,
        "protocol_readiness": (
            "STRUCTURE_DEFINED_ADDITIONAL_EXTERNAL_INPUTS_REQUIRED"
            if resolved else "STRUCTURE_DEFINED_EXTERNAL_INPUTS_REQUIRED"),
        "next_blocker": (
            "MINIMUM_PRACTICALLY_IMPORTANT_DIFFERENCE_TEAM_TRAVEL_TIME_SECONDS"
            if resolved else
            "MAXIMUM_ACCEPTABLE_TRAINING_RESOURCE_BUDGET_VALUE_REQUIRED")}
    Path(resolution_path).write_text(json.dumps(artifact, indent=2),
                                     encoding="utf-8")
    return resolution, artifact
