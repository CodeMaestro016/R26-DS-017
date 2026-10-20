"""Step 5J.3C.2E.1 resource evidence and fixed-horizon derivation."""

# Import asdict, dataclass from dataclasses for the operations below.
from dataclasses import asdict, dataclass
# Import hashlib for use in this module.
import hashlib
# Import json for use in this module.
import json
# Import math for use in this module.
import math
# Import Path from pathlib for the operations below.
from pathlib import Path
# Import Any, Mapping, Optional, Tuple from typing for the operations below.
from typing import Any, Mapping, Optional, Tuple

# Import EPISODE_STEPS from config for the operations below.
from config import EPISODE_STEPS
# Import ScenarioRole, build_design from experimentation for the operations below.
from experimentation import ScenarioRole, build_design


# Set SOURCE_PROTOCOL_PATH to the result of Path(the text 'results/mappo_predeclared_selection_protocol.json').
SOURCE_PROTOCOL_PATH = Path("results/mappo_predeclared_selection_protocol.json")
# Set EXTENDED_EVIDENCE_PATH to the result of Path(the text
# 'results/mappo_extended_learning_curve_evidence.json').
EXTENDED_EVIDENCE_PATH = Path(
    "results/mappo_extended_learning_curve_evidence.json")
# Set PILOT_EVIDENCE_PATH to the result of Path(the text 'results/mappo_closed_loop_pilot_evidence.json').
PILOT_EVIDENCE_PATH = Path("results/mappo_closed_loop_pilot_evidence.json")
# Set INPUT_PATH to the result of Path(the text 'research_inputs/mappo_selection_external_inputs.json').
INPUT_PATH = Path("research_inputs/mappo_selection_external_inputs.json")
# Set RESOLUTION_PATH to the result of Path(the text 'results/mappo_training_resource_budget_resolution.json').
RESOLUTION_PATH = Path("results/mappo_training_resource_budget_resolution.json")
# Set V2_PATH to the result of Path(the text 'results/mappo_selection_protocol_v2.json').
V2_PATH = Path("results/mappo_selection_protocol_v2.json")

# Set EXPECTED_V1_ID to a tuple containing the text 'MAPPO_SELECTION_PROTOCOL_V1', the text...
EXPECTED_V1_ID = (
    "MAPPO_SELECTION_PROTOCOL_V1",
    "cc2ac385d9ac8134f621f792a037700d5fb1dfaee74ef2f0f8317ecef3e3331e")
# Set ALLOWED_BUDGET_TYPES to a tuple containing the text 'PPO_UPDATE_CYCLES_PER_REPLICATION', the text
# 'TRAINING_MANIFEST_COLLECTIONS_PER_REPLICATION',...
ALLOWED_BUDGET_TYPES = (
    "PPO_UPDATE_CYCLES_PER_REPLICATION",
    "TRAINING_MANIFEST_COLLECTIONS_PER_REPLICATION",
    "SUMO_STEPS_PER_REPLICATION",
    "WALL_CLOCK_SECONDS_PER_REPLICATION")
# Set ALLOWED_APPROVALS to a tuple containing the text 'PROJECT_APPROVED', the text 'SUPERVISOR_APPROVED'.
ALLOWED_APPROVALS = ("PROJECT_APPROVED", "SUPERVISOR_APPROVED")
# Set EXPECTED_UNITS to a dictionary containing PPO_UPDATE_CYCLES_PER_REPLICATION,
# TRAINING_MANIFEST_COLLECTIONS_PER_REPLICATION,...
EXPECTED_UNITS = {
    "PPO_UPDATE_CYCLES_PER_REPLICATION": "PPO-update-cycles",
    "TRAINING_MANIFEST_COLLECTIONS_PER_REPLICATION":
        "TRAINING-manifest-collections",
    "SUMO_STEPS_PER_REPLICATION": "SUMO-steps",
    "WALL_CLOCK_SECONDS_PER_REPLICATION": "seconds"}
# Set REMAINING_INPUT_ORDER to a tuple containing the text
# 'MINIMUM_PRACTICALLY_IMPORTANT_DIFFERENCE_TEAM_TRAVEL_TIME_SECONDS', the text...
REMAINING_INPUT_ORDER = (
    "MINIMUM_PRACTICALLY_IMPORTANT_DIFFERENCE_TEAM_TRAVEL_TIME_SECONDS",
    "STATISTICAL_CONFIDENCE_OR_PRECISION_TARGET",
    "STATISTICAL_POWER_TARGET",
    "UNCERTAINTY_MONTE_CARLO_RESOLUTION",
    "MULTIPLE_COMPARISON_CONTROL",
    "CANDIDATE_SEARCH_SEQUENCE")


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define TrainingResourceBudgetInput to group the state and operations declared below.
# Declared fields: input_id, scope, budget_type, budget_value, unit, justification_source, approval_status,
# provenance.
# Construction and attribute behavior follow the declared decorators and base classes.
class TrainingResourceBudgetInput:
    # Declare input_id as tuple for this data structure.
    input_id: tuple
    # Declare scope as str for this data structure.
    scope: str
    # Declare budget_type as Optional[str] for this data structure.
    budget_type: Optional[str]
    # Declare budget_value as Optional[float] for this data structure.
    budget_value: Optional[float]
    # Declare unit as Optional[str] for this data structure.
    unit: Optional[str]
    # Declare justification_source as Optional[str] for this data structure.
    justification_source: Optional[str]
    # Declare approval_status as str for this data structure.
    approval_status: str
    # Declare provenance as Tuple[Tuple[str, Any], ...] for this data structure.
    provenance: Tuple[Tuple[str, Any], ...]


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define TrainingResourceEvidence to group the state and operations declared below.
# Declared fields: training_manifest_scenario_count, steps_per_scenario, sumo_steps_per_training_manifest,
# observed_manifest_runtime_values, observed_update_runtime_values, observed_replication_overhead_values,....
# Construction and attribute behavior follow the declared decorators and base classes.
class TrainingResourceEvidence:
    # Declare training_manifest_scenario_count as int for this data structure.
    training_manifest_scenario_count: int
    # Declare steps_per_scenario as int for this data structure.
    steps_per_scenario: int
    # Declare sumo_steps_per_training_manifest as int for this data structure.
    sumo_steps_per_training_manifest: int
    # Declare observed_manifest_runtime_values as tuple for this data structure.
    observed_manifest_runtime_values: tuple
    # Declare observed_update_runtime_values as tuple for this data structure.
    observed_update_runtime_values: tuple
    # Declare observed_replication_overhead_values as tuple for this data structure.
    observed_replication_overhead_values: tuple
    # Declare manifest_runtime_bound as float for this data structure.
    manifest_runtime_bound: float
    # Declare update_runtime_bound as float for this data structure.
    update_runtime_bound: float
    # Declare overhead_bound as float for this data structure.
    overhead_bound: float
    # Declare wall_clock_mapping_status as str for this data structure.
    wall_clock_mapping_status: str
    # Declare source_artifact_ids as tuple for this data structure.
    source_artifact_ids: tuple
    # Set performance_values_used to False; declare its type as bool.
    performance_values_used: bool = False


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define TrainingResourceBudgetResolution to group the state and operations declared below.
# Declared fields: resolution_id, source_protocol_id, input_requirement_name, resource_input, resource_evidence,
# derived_H, derived_policy_state_count, derived_manifest_collection_count,
# derived_sumo_steps_per_replication,....
# Construction and attribute behavior follow the declared decorators and base classes.
class TrainingResourceBudgetResolution:
    # Declare resolution_id as tuple for this data structure.
    resolution_id: tuple
    # Declare source_protocol_id as tuple for this data structure.
    source_protocol_id: tuple
    # Declare input_requirement_name as str for this data structure.
    input_requirement_name: str
    # Declare resource_input as TrainingResourceBudgetInput for this data structure.
    resource_input: TrainingResourceBudgetInput
    # Declare resource_evidence as TrainingResourceEvidence for this data structure.
    resource_evidence: TrainingResourceEvidence
    # Declare derived_H as Optional[int] for this data structure.
    derived_H: Optional[int]
    # Declare derived_policy_state_count as Optional[int] for this data structure.
    derived_policy_state_count: Optional[int]
    # Declare derived_manifest_collection_count as Optional[int] for this data structure.
    derived_manifest_collection_count: Optional[int]
    # Declare derived_sumo_steps_per_replication as Optional[int] for this data structure.
    derived_sumo_steps_per_replication: Optional[int]
    # Declare derived_conservative_wall_clock_bound as Optional[float] for this data structure.
    derived_conservative_wall_clock_bound: Optional[float]
    # Declare unused_capacity as Optional[float] for this data structure.
    unused_capacity: Optional[float]
    # Declare resource_budget_resolved as bool for this data structure.
    resource_budget_resolved: bool
    # Declare performance_used_to_choose_budget as bool for this data structure.
    performance_used_to_choose_budget: bool
    # Declare performance_used_to_derive_H as bool for this data structure.
    performance_used_to_derive_H: bool
    # Declare project_selected as bool for this data structure.
    project_selected: bool
    # Declare provenance as Tuple[Tuple[str, Any], ...] for this data structure.
    provenance: Tuple[Tuple[str, Any], ...]


# Canonical using the inputs and processing steps below.
# Input value: the supplied value.
# Output: the serialized data produced by json.dumps.
def _canonical(value):
    # Return the serialized data produced by json.dumps to the caller.
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


# Load and validate v1 using the inputs and processing steps below.
# Input path: the path or path object supplied by the caller.
# Output: source.
# Processing: select branches using the stated conditions.
def load_and_validate_v1(path=SOURCE_PROTOCOL_PATH):
    # Set source to the decoded data produced by json.loads from the text read from Path(path).
    source = json.loads(Path(path).read_text(encoding="utf-8"))
    # Run this branch when 'checkpoint' from source; use None if absent differs from the text 'STEP_5J_3C_2D' or
    # 'status' from source; use None if absent differs from the text
    # 'PREDECLARED_SELECTION_PROTOCOL_STRUCTURE_COMPLETE' or 'protocol_readiness' from source; use None if absent
    # differs from the text 'STRUCTURE_DEFINED_EXTERNAL_INPUTS_REQUIRED' or a tuple built from 'protocol_id' from
    # source.get('protocol', {}); use () if absent differs from EXPECTED_V1_ID or 'next_blocker' from source; use
    # None if absent differs from the text 'MAXIMUM_ACCEPTABLE_TRAINING_RESOURCE_BUDGET'.
    if (source.get("checkpoint") != "STEP_5J_3C_2D" or
            # Evaluate 'status' from source; use None if absent differs from the text
            # 'PREDECLARED_SELECTION_PROTOCOL_STRUCTURE_COMPLETE' as part of the enclosing expression.
            source.get("status") !=
            # Supply the text 'PREDECLARED_SELECTION_PROTOCOL_STRUCTURE_COMPLETE' to the enclosing expression.
            "PREDECLARED_SELECTION_PROTOCOL_STRUCTURE_COMPLETE" or
            # Evaluate 'protocol_readiness' from source; use None if absent differs from the text
            # 'STRUCTURE_DEFINED_EXTERNAL_INPUTS_REQUIRED' as part of the enclosing expression.
            source.get("protocol_readiness") !=
            # Supply the text 'STRUCTURE_DEFINED_EXTERNAL_INPUTS_REQUIRED' to the enclosing expression.
            "STRUCTURE_DEFINED_EXTERNAL_INPUTS_REQUIRED" or
            # Evaluate a tuple built from 'protocol_id' from source.get('protocol', {}); use an empty tuple if
            # absent differs from EXPECTED_V1_ID as part of the enclosing expression.
            tuple(source.get("protocol", {}).get("protocol_id", ())) !=
            # Evaluate EXPECTED_V1_ID as part of the enclosing expression.
            EXPECTED_V1_ID or
            # Evaluate 'next_blocker' from source; use None if absent differs from the text
            # 'MAXIMUM_ACCEPTABLE_TRAINING_RESOURCE_BUDGET' as part of the enclosing expression.
            source.get("next_blocker") !=
            "MAXIMUM_ACCEPTABLE_TRAINING_RESOURCE_BUDGET"):
        # Raise ValueError with the text 'RESOURCE_BUDGET_SOURCE_PROTOCOL_INVALID' to stop this execution path.
        raise ValueError("RESOURCE_BUDGET_SOURCE_PROTOCOL_INVALID")
    # Return source to the caller.
    return source


# Derive resource evidence using the inputs and processing steps below.
# Input evidence_path: the supplied evidence path.
# Output: the result of TrainingResourceEvidence().
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def derive_resource_evidence(evidence_path=EXTENDED_EVIDENCE_PATH):
    # Set evidence to the decoded data produced by json.loads from the text read from Path(evidence_path).
    evidence = json.loads(Path(evidence_path).read_text(encoding="utf-8"))
    # Run this branch when 'status' from evidence; use None if absent differs from the text
    # 'EXTENDED_MULTI_UPDATE_EVIDENCE_ACQUIRED'.
    if evidence.get("status") != "EXTENDED_MULTI_UPDATE_EVIDENCE_ACQUIRED":
        # Raise ValueError with the text 'RESOURCE_EVIDENCE_IDENTITY_INVALID' to stop this execution path.
        raise ValueError("RESOURCE_EVIDENCE_IDENTITY_INVALID")
    # Set design to the result of build_design().
    design = build_design()
    # Set scenario_count to the number of entries in design['manifests'][ScenarioRole.TRAINING].scenario_ids.
    scenario_count = len(
        # Supply design['manifests'][ScenarioRole.TRAINING].scenario_ids to len.
        design["manifests"][ScenarioRole.TRAINING].scenario_ids)
    # Set steps_per_manifest to scenario_count multiplied by EPISODE_STEPS.
    steps_per_manifest = scenario_count * EPISODE_STEPS
    # Set (manifest_runtimes, update_runtimes, overheads) to a tuple containing an empty list, an empty list, an
    # empty list.
    manifest_runtimes, update_runtimes, overheads = [], [], []
    # Iterate over evidence at 'replications', binding each item to replication.
    for replication in evidence["replications"]:
        # Set states to replication at 'policy_states'.
        states = replication["policy_states"]
        # Set updates to replication at 'updates'.
        updates = replication["updates"]
        # Run this branch when the number of entries in states differs from 3 or whether any item is true in a
        # lazy sequence of state['sumo_step_count'] differs from steps_per_manifest for state in states.
        if (len(states) != 3 or any(
                # Evaluate state at 'sumo_step_count' differs from steps_per_manifest as part of the enclosing
                # expression.
                state["sumo_step_count"] != steps_per_manifest
                # Evaluate states as part of the enclosing expression.
                for state in states)):
            # Raise ValueError with the text 'STRUCTURAL_SUMO_STEP_MAPPING_MISMATCH' to stop this execution path.
            raise ValueError("STRUCTURAL_SUMO_STEP_MAPPING_MISMATCH")
        # Set state_times to a list of a floating-point number built from state at 'wall_clock_runtime_seconds'
        # for state in states.
        state_times = [float(state["wall_clock_runtime_seconds"])
                       # Evaluate states as part of the enclosing expression.
                       for state in states]
        # Set update_times to a list of a floating-point number built from update at 'wall_clock_runtime_seconds'
        # for update in updates.
        update_times = [float(update["wall_clock_runtime_seconds"])
                        # Evaluate updates as part of the enclosing expression.
                        for update in updates]
        # Extend manifest_runtimes with state_times.
        manifest_runtimes.extend(state_times)
        # Extend update_runtimes with update_times.
        update_runtimes.extend(update_times)
        # Set overhead to a floating-point number built from replication at 'wall_clock_runtime_seconds' minus the
        # sum of state_times minus the sum of update_times.
        overhead = (float(replication["wall_clock_runtime_seconds"]) -
                    # Evaluate the sum of update_times as part of the enclosing expression.
                    sum(state_times) - sum(update_times))
        # Run this branch when overhead is less than 0.
        if overhead < 0:
            # Raise ValueError with the text 'REPLICATION_OVERHEAD_NOT_DERIVABLE' to stop this execution path.
            raise ValueError("REPLICATION_OVERHEAD_NOT_DERIVABLE")
        # Append overhead to overheads.
        overheads.append(overhead)
    # Run this branch when evidence['compute_cost_evidence'] at 'total_sumo_steps' differs from the number of
    # entries in evidence['replications'] multiplied by the number of entries in
    # evidence['replications'][0]['policy_states'] multiplied by steps_per_manifest.
    if (evidence["compute_cost_evidence"]["total_sumo_steps"] !=
            # Evaluate the number of entries in evidence at 'replications' multiplied by the number of entries in
            # evidence['replications'][0] at 'policy_states' multiplied by steps_per_manifest as part of the
            # enclosing expression.
            len(evidence["replications"]) * len(
                # Supply evidence['replications'][0] at 'policy_states' to len.
                evidence["replications"][0]["policy_states"]) *
            # Evaluate steps_per_manifest as part of the enclosing expression.
            steps_per_manifest):
        # Raise ValueError with the text 'STRUCTURAL_SUMO_STEP_MAPPING_MISMATCH' to stop this execution path.
        raise ValueError("STRUCTURAL_SUMO_STEP_MAPPING_MISMATCH")
    # Return the result of TrainingResourceEvidence() to the caller.
    return TrainingResourceEvidence(
        # Supply training_manifest_scenario_count as scenario_count.
        training_manifest_scenario_count=scenario_count,
        # Supply steps_per_scenario as EPISODE_STEPS.
        steps_per_scenario=EPISODE_STEPS,
        # Supply sumo_steps_per_training_manifest as steps_per_manifest.
        sumo_steps_per_training_manifest=steps_per_manifest,
        # Supply observed_manifest_runtime_values as a tuple built from manifest_runtimes.
        observed_manifest_runtime_values=tuple(manifest_runtimes),
        # Supply observed_update_runtime_values as a tuple built from update_runtimes.
        observed_update_runtime_values=tuple(update_runtimes),
        # Supply observed_replication_overhead_values as a tuple built from overheads.
        observed_replication_overhead_values=tuple(overheads),
        # Supply manifest_runtime_bound as the maximum of manifest_runtimes.
        manifest_runtime_bound=max(manifest_runtimes),
        # Supply update_runtime_bound as the maximum of update_runtimes.
        update_runtime_bound=max(update_runtimes),
        # Supply overhead_bound as the maximum of overheads.
        overhead_bound=max(overheads),
        # Supply wall_clock_mapping_status as the text 'CONSERVATIVE_HISTORICAL_MAX_COMPONENT_MAPPING_AVAILABLE'.
        wall_clock_mapping_status=
            "CONSERVATIVE_HISTORICAL_MAX_COMPONENT_MAPPING_AVAILABLE",
        # Supply source_artifact_ids as a tuple containing a tuple built from evidence at
        # 'evidence_tranche_identity', a tuple containing the text...
        source_artifact_ids=(
            # Include a tuple built from evidence at 'evidence_tranche_identity' in this tuple.
            tuple(evidence["evidence_tranche_identity"]),
            # Include a tuple containing the text 'CLOSED_LOOP_PILOT_EVIDENCE_PATH', a string built from
            # PILOT_EVIDENCE_PATH in this tuple.
            ("CLOSED_LOOP_PILOT_EVIDENCE_PATH",
             # Include a string built from PILOT_EVIDENCE_PATH in this tuple.
             str(PILOT_EVIDENCE_PATH))),
        # Supply performance_values_used as False.
        performance_values_used=False)


# Load resource input using the inputs and processing steps below.
# Input path: the path or path object supplied by the caller.
# Output: the result of TrainingResourceBudgetInput().
def load_resource_input(path=INPUT_PATH):
    # Set raw to json.loads(Path(path).read_text(encoding='utf-8')) at
    # 'MAXIMUM_ACCEPTABLE_TRAINING_RESOURCE_BUDGET'.
    raw = json.loads(Path(path).read_text(encoding="utf-8"))[
        "MAXIMUM_ACCEPTABLE_TRAINING_RESOURCE_BUDGET"]
    # Set identity_fields to a dictionary of key mapped to key from raw; use None if absent for key in a tuple
    # containing the text 'status', the text 'scope', the text 'budget_type', the text 'budget_value', the text
    # 'unit', the...
    identity_fields = {key: raw.get(key) for key in (
        "status", "scope", "budget_type", "budget_value", "unit",
        "justification_source", "approval_status")}
    # Set identity to a tuple containing the text 'TRAINING_RESOURCE_BUDGET_INPUT_V1', the hexadecimal digest
    # from...
    identity = ("TRAINING_RESOURCE_BUDGET_INPUT_V1",
                # Include the hexadecimal digest from hashlib.sha256(_canonical(identity_fields).encode()) in this
                # tuple.
                hashlib.sha256(_canonical(identity_fields).encode()).hexdigest())
    # Return the result of TrainingResourceBudgetInput() to the caller.
    return TrainingResourceBudgetInput(
        # Supply input_id as identity.
        # Supply scope as 'scope' from raw; use None if absent.
        input_id=identity, scope=raw.get("scope"),
        # Supply budget_type as 'budget_type' from raw; use None if absent.
        budget_type=raw.get("budget_type"),
        # Supply budget_value as 'budget_value' from raw; use None if absent.
        # Supply unit as 'unit' from raw; use None if absent.
        budget_value=raw.get("budget_value"), unit=raw.get("unit"),
        # Supply justification_source as 'justification_source' from raw; use None if absent.
        justification_source=raw.get("justification_source"),
        # Supply approval_status as 'approval_status' from raw; use None if absent.
        approval_status=raw.get("approval_status"),
        # Supply provenance as a tuple containing a tuple containing the text 'status', 'status' from raw; use
        # None if absent, a tuple containing the text...
        provenance=(("status", raw.get("status")),
                    # Include a tuple containing the text 'source_path', a string built from path in this tuple.
                    ("source_path", str(path))))


# Validate resource input using the inputs and processing steps below.
# Input resource_input: the supplied resource input.
# Output: return the value selected by the matching return branch below.
# Processing: select branches using the stated conditions.
def validate_resource_input(resource_input):
    # Set status to 'status' from dict(resource_input.provenance); use None if absent.
    status = dict(resource_input.provenance).get("status")
    # Run this branch when status equals the text 'UNRESOLVED'.
    if status == "UNRESOLVED":
        # Run this branch when whether any item is true in a lazy sequence of value is a different object from
        # None for value in a tuple containing resource_input.budget_type, resource_input.budget_value,
        # resource_input.unit,... or resource_input.approval_status differs from the text 'NOT_SUPPLIED'.
        if any(value is not None for value in (
                # Include resource_input.budget_value in this tuple.
                resource_input.budget_type, resource_input.budget_value,
                # Include resource_input.justification_source in this tuple.
                resource_input.unit, resource_input.justification_source)) or \
                resource_input.approval_status != "NOT_SUPPLIED":
            # Return the text 'RESOURCE_BUDGET_VALUE_PRESENT_BUT_NOT_JUSTIFIED' to the caller.
            return "RESOURCE_BUDGET_VALUE_PRESENT_BUT_NOT_JUSTIFIED"
        # Return the text 'EXTERNAL_RESOURCE_BUDGET_NOT_SUPPLIED' to the caller.
        return "EXTERNAL_RESOURCE_BUDGET_NOT_SUPPLIED"
    # Run this branch when status differs from the text 'RESOLVED'.
    if status != "RESOLVED":
        # Raise ValueError with the text 'RESOURCE_BUDGET_INPUT_STATUS_INVALID' to stop this execution path.
        raise ValueError("RESOURCE_BUDGET_INPUT_STATUS_INVALID")
    # Run this branch when resource_input.scope differs from the text 'PER_REPLICATION'.
    if resource_input.scope != "PER_REPLICATION":
        # Raise ValueError with the text 'RESOURCE_BUDGET_SCOPE_MUST_BE_PER_REPLICATION' to stop this execution
        # path.
        raise ValueError("RESOURCE_BUDGET_SCOPE_MUST_BE_PER_REPLICATION")
    # Run this branch when resource_input.budget_type does not belong to ALLOWED_BUDGET_TYPES.
    if resource_input.budget_type not in ALLOWED_BUDGET_TYPES:
        # Raise ValueError with the text 'RESOURCE_BUDGET_TYPE_INVALID' to stop this execution path.
        raise ValueError("RESOURCE_BUDGET_TYPE_INVALID")
    # Set value to resource_input.budget_value.
    value = resource_input.budget_value
    # Run this branch when whether value has type bool or the negation of whether value has type a tuple
    # containing int, float or value is at most 0.
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
        # Raise ValueError with the text 'RESOURCE_BUDGET_VALUE_INVALID' to stop this execution path.
        raise ValueError("RESOURCE_BUDGET_VALUE_INVALID")
    # Run this branch when resource_input.budget_type differs from the text 'WALL_CLOCK_SECONDS_PER_REPLICATION'
    # and the negation of whether value has type int or whether value has type bool.
    if (resource_input.budget_type != "WALL_CLOCK_SECONDS_PER_REPLICATION" and
            # Evaluate the negation of whether value has type int or whether value has type bool as part of the
            # enclosing expression.
            (not isinstance(value, int) or isinstance(value, bool))):
        # Raise ValueError with the text 'STRUCTURAL_RESOURCE_BUDGET_MUST_BE_INTEGER' to stop this execution path.
        raise ValueError("STRUCTURAL_RESOURCE_BUDGET_MUST_BE_INTEGER")
    # Run this branch when the negation of resource_input.unit or the negation of
    # resource_input.justification_source.
    if not resource_input.unit or not resource_input.justification_source:
        # Return the text 'RESOURCE_BUDGET_VALUE_PRESENT_BUT_NOT_JUSTIFIED' to the caller.
        return "RESOURCE_BUDGET_VALUE_PRESENT_BUT_NOT_JUSTIFIED"
    # Run this branch when resource_input.unit differs from EXPECTED_UNITS at resource_input.budget_type.
    if resource_input.unit != EXPECTED_UNITS[resource_input.budget_type]:
        # Raise ValueError with the text 'RESOURCE_BUDGET_UNIT_MISMATCH' to stop this execution path.
        raise ValueError("RESOURCE_BUDGET_UNIT_MISMATCH")
    # Run this branch when resource_input.approval_status does not belong to ALLOWED_APPROVALS.
    if resource_input.approval_status not in ALLOWED_APPROVALS:
        # Run this branch when resource_input.approval_status belongs to a tuple containing the text
        # 'AUTO_SELECTED', the text 'PERFORMANCE_SELECTED', the text 'INFERRED_FROM_C0_C1_C2', the text...
        if resource_input.approval_status in (
                "AUTO_SELECTED", "PERFORMANCE_SELECTED",
                "INFERRED_FROM_C0_C1_C2", "CONVENTIONAL_DEFAULT"):
            # Raise ValueError with the text 'RESOURCE_BUDGET_APPROVAL_PROVENANCE_FORBIDDEN' to stop this
            # execution path.
            raise ValueError("RESOURCE_BUDGET_APPROVAL_PROVENANCE_FORBIDDEN")
        # Return the text 'RESOURCE_BUDGET_VALUE_PRESENT_BUT_NOT_JUSTIFIED' to the caller.
        return "RESOURCE_BUDGET_VALUE_PRESENT_BUT_NOT_JUSTIFIED"
    # Return the text 'APPROVED_RESOURCE_BUDGET_VALID' to the caller.
    return "APPROVED_RESOURCE_BUDGET_VALID"


# Derive horizon using the inputs and processing steps below.
# Input resource_input: the supplied resource input.
# Input evidence: the supplied evidence.
# Output: a tuple containing an integer built from h, unused, wall_bound.
# Processing: select branches using the stated conditions.
def derive_horizon(resource_input, evidence):
    # Set budget to resource_input.budget_value.
    budget = resource_input.budget_value
    # Set kind to resource_input.budget_type.
    kind = resource_input.budget_type
    # Set unused to None.
    unused = None
    # Run this branch when kind equals the text 'PPO_UPDATE_CYCLES_PER_REPLICATION'.
    if kind == "PPO_UPDATE_CYCLES_PER_REPLICATION":
        # Set h to budget.
        h = budget
    # Run this branch when kind equals the text 'TRAINING_MANIFEST_COLLECTIONS_PER_REPLICATION'.
    elif kind == "TRAINING_MANIFEST_COLLECTIONS_PER_REPLICATION":
        # Set h to budget minus 1.
        h = budget - 1
    # Run this branch when kind equals the text 'SUMO_STEPS_PER_REPLICATION'.
    elif kind == "SUMO_STEPS_PER_REPLICATION":
        # Set h to the result of math.floor(budget divided by evidence.sumo_steps_per_training_manifest) minus 1.
        h = math.floor(budget / evidence.sumo_steps_per_training_manifest) - 1
        # Set unused to budget minus h plus 1 multiplied by evidence.sumo_steps_per_training_manifest.
        unused = budget - (h + 1) * evidence.sumo_steps_per_training_manifest
    # Run this branch when kind equals the text 'WALL_CLOCK_SECONDS_PER_REPLICATION'.
    elif kind == "WALL_CLOCK_SECONDS_PER_REPLICATION":
        # Run this branch when evidence.wall_clock_mapping_status differs from the text
        # 'CONSERVATIVE_HISTORICAL_MAX_COMPONENT_MAPPING_AVAILABLE'.
        if evidence.wall_clock_mapping_status != \
                "CONSERVATIVE_HISTORICAL_MAX_COMPONENT_MAPPING_AVAILABLE":
            # Raise ValueError with the text 'WALL_CLOCK_RESOURCE_MAPPING_NOT_CONSERVATIVELY_DERIVABLE' to stop
            # this execution path.
            raise ValueError("WALL_CLOCK_RESOURCE_MAPPING_NOT_CONSERVATIVELY_DERIVABLE")
        # Set h to the result of math.floor(budget minus evidence.manifest_runtime_bound minus
        # evidence.overhead_bound divided by...).
        h = math.floor((budget - evidence.manifest_runtime_bound -
                        # Evaluate evidence.overhead_bound as part of the enclosing expression.
                        evidence.overhead_bound) /
                       # Evaluate evidence.manifest_runtime_bound plus evidence.update_runtime_bound as part of
                       # the enclosing expression.
                       (evidence.manifest_runtime_bound +
                        # Evaluate evidence.update_runtime_bound as part of the enclosing expression.
                        evidence.update_runtime_bound))
        # Set bound to h plus 1 multiplied by evidence.manifest_runtime_bound plus h multiplied by
        # evidence.update_runtime_bound plus evidence.overhead_bound.
        bound = ((h + 1) * evidence.manifest_runtime_bound +
                 # Evaluate h multiplied by evidence.update_runtime_bound as part of the enclosing expression.
                 h * evidence.update_runtime_bound + evidence.overhead_bound)
        # Set unused to budget minus bound.
        unused = budget - bound
    # Run this alternative branch when the preceding branch does not apply.
    else:
        # Raise ValueError with the text 'RESOURCE_BUDGET_TYPE_INVALID' to stop this execution path.
        raise ValueError("RESOURCE_BUDGET_TYPE_INVALID")
    # Run this branch when h is less than 1.
    if h < 1:
        # Raise ValueError with the text 'RESOURCE_BUDGET_TOO_SMALL_FOR_ONE_UPDATE' to stop this execution path.
        raise ValueError("RESOURCE_BUDGET_TOO_SMALL_FOR_ONE_UPDATE")
    # Set wall_bound to h plus 1 multiplied by evidence.manifest_runtime_bound plus h multiplied by
    # evidence.update_runtime_bound plus evidence.overhead_bound.
    wall_bound = ((h + 1) * evidence.manifest_runtime_bound +
                  # Evaluate h multiplied by evidence.update_runtime_bound as part of the enclosing expression.
                  h * evidence.update_runtime_bound + evidence.overhead_bound)
    # Return a tuple containing an integer built from h, unused, wall_bound to the caller.
    return int(h), unused, wall_bound


# Create v2 using the inputs and processing steps below.
# Input v1: the supplied v1.
# Input resource_input: the supplied resource input.
# Input evidence: the supplied evidence.
# Input h: the supplied h.
# Input wall_bound: the supplied wall bound.
# Input output_path: the supplied output path.
# Output: protocol_id.
def _create_v2(v1, resource_input, evidence, h, wall_bound, output_path):
    # Set protocol to the decoded data produced by json.loads from the serialized data produced by json.dumps.
    protocol = json.loads(json.dumps(v1["protocol"]))
    # Update protocol['training_budget_protocol'] with the supplied entries.
    protocol["training_budget_protocol"].update({
        # Store h under 'maximum_update_horizon_H'.
        "maximum_update_horizon_H": h,
        "resource_horizon_status": "RESOLVED_PROJECT_RESOURCE_CONSTRAINT",
        # Store formatted text built from the embedded values under 'policy_states'.
        "policy_states": f"STATE_0_THROUGH_STATE_{h}_INCLUSIVE",
        # Store h plus 1 under 'training_manifest_collections_per_replication'.
        "training_manifest_collections_per_replication": h + 1,
        "exact_sumo_steps_per_replication":
            # Evaluate h plus 1 multiplied by evidence.sumo_steps_per_training_manifest as part of the enclosing
            # expression.
            (h + 1) * evidence.sumo_steps_per_training_manifest,
        # Store wall_bound under 'derived_conservative_wall_clock_bound_seconds'.
        "derived_conservative_wall_clock_bound_seconds": wall_bound,
        # Store a dictionary containing input_id, budget_type, budget_value, unit, justification_source,
        # approval_status under 'resource_constraint_source'.
        "resource_constraint_source": {
            # Store resource_input.input_id under 'input_id'.
            "input_id": resource_input.input_id,
            # Store resource_input.budget_type under 'budget_type'.
            "budget_type": resource_input.budget_type,
            # Store resource_input.budget_value under 'budget_value'.
            "budget_value": resource_input.budget_value,
            # Store resource_input.unit under 'unit'.
            "unit": resource_input.unit,
            # Store resource_input.justification_source under 'justification_source'.
            "justification_source": resource_input.justification_source,
            # Store resource_input.approval_status under 'approval_status'.
            "approval_status": resource_input.approval_status},
        "horizon_semantics":
            "DETERMINISTICALLY_DERIVED_FROM_PROJECT_RESOURCE_CONSTRAINT",
        # Store False under 'optimality_claim'.
        "optimality_claim": False})
    # Set protocol['unresolved_external_inputs'] to a list of item for item in protocol at
    # 'unresolved_external_inputs'; retain entries satisfying item at 'input_name' differs from the text
    # 'MAXIMUM_ACCEPTABLE_TRAINING_RESOURCE_BUDGET'.
    protocol["unresolved_external_inputs"] = [
        # Evaluate protocol at 'unresolved_external_inputs' as part of the enclosing expression.
        item for item in protocol["unresolved_external_inputs"]
        # Evaluate item at 'input_name' differs from the text 'MAXIMUM_ACCEPTABLE_TRAINING_RESOURCE_BUDGET' as
        # part of the enclosing expression.
        if item["input_name"] !=
        "MAXIMUM_ACCEPTABLE_TRAINING_RESOURCE_BUDGET"]
    # Set protocol['freeze_status'] to the text 'RESOURCE_BUDGET_RESOLVED_ADDITIONAL_EXTERNAL_INPUTS_UNRESOLVED'.
    protocol["freeze_status"] = \
        "RESOURCE_BUDGET_RESOLVED_ADDITIONAL_EXTERNAL_INPUTS_UNRESOLVED"
    # Remove the requested entry from protocol.
    protocol.pop("protocol_id", None)
    # Set digest to the hexadecimal digest from hashlib.sha256(_canonical(protocol).encode()).
    digest = hashlib.sha256(_canonical(protocol).encode()).hexdigest()
    # Set protocol_id to a tuple containing the text 'MAPPO_SELECTION_PROTOCOL_V2_RESOURCE_BUDGET_RESOLVED',
    # digest.
    protocol_id = (
        # Include digest in this tuple.
        "MAPPO_SELECTION_PROTOCOL_V2_RESOURCE_BUDGET_RESOLVED", digest)
    # Set protocol['protocol_id'] to protocol_id.
    protocol["protocol_id"] = protocol_id
    # Set artifact to a dictionary containing checkpoint, protocol_version, protocol_readiness, protocol,
    # remaining_external_inputs.
    artifact = {
        "checkpoint": "STEP_5J_3C_2E_1",
        # Store protocol_id at 0 under 'protocol_version'.
        "protocol_version": protocol_id[0],
        "protocol_readiness":
            "STRUCTURE_DEFINED_ADDITIONAL_EXTERNAL_INPUTS_REQUIRED",
        # Store protocol under 'protocol'.
        "protocol": protocol,
        # Store a list built from REMAINING_INPUT_ORDER under 'remaining_external_inputs'.
        "remaining_external_inputs": list(REMAINING_INPUT_ORDER)}
    # Write the supplied text to Path(output_path).
    Path(output_path).write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    # Return protocol_id to the caller.
    return protocol_id


# Resolve training resource budget using the inputs and processing steps below.
# Input source_protocol_path: the supplied source protocol path.
# Input external_input_path: the supplied external input path.
# Input evidence_path: the supplied evidence path.
# Input resolution_path: the supplied resolution path.
# Input v2_path: the supplied v2 path.
# Output: a tuple containing resolution, artifact.
# Processing: select branches using the stated conditions.
def resolve_training_resource_budget(
        # Declare source_protocol_path as input parameter.
        source_protocol_path=SOURCE_PROTOCOL_PATH,
        # Declare external_input_path as input parameter.
        external_input_path=INPUT_PATH,
        # Declare evidence_path as input parameter.
        evidence_path=EXTENDED_EVIDENCE_PATH,
        # Declare resolution_path, v2_path as input parameters.
        resolution_path=RESOLUTION_PATH, v2_path=V2_PATH):
    # Set v1 to the result of load_and_validate_v1(source_protocol_path).
    v1 = load_and_validate_v1(source_protocol_path)
    # Set evidence to the result of derive_resource_evidence(evidence_path).
    evidence = derive_resource_evidence(evidence_path)
    # Set resource_input to the result of load_resource_input(external_input_path).
    resource_input = load_resource_input(external_input_path)
    # Set input_status to the result of validate_resource_input(resource_input).
    input_status = validate_resource_input(resource_input)
    # Set resolved to input_status equals the text 'APPROVED_RESOURCE_BUDGET_VALID'.
    resolved = input_status == "APPROVED_RESOURCE_BUDGET_VALID"
    # Set h and unused and wall_bound and protocol_id to None.
    h = unused = wall_bound = protocol_id = None
    # Run this branch when resolved.
    if resolved:
        # Set (h, unused, wall_bound) to the result of derive_horizon(resource_input, evidence).
        h, unused, wall_bound = derive_horizon(resource_input, evidence)
        # Set protocol_id to the result of _create_v2(v1, resource_input, evidence, h, wall_bound, v2_path).
        protocol_id = _create_v2(
            # Supply resource_input to _create_v2.
            v1, resource_input, evidence, h, wall_bound, v2_path)
    # Set resolution_fields to a tuple containing EXPECTED_V1_ID, resource_input.input_id, the result of
    # asdict(evidence), h, resolved, input_status.
    resolution_fields = (
        # Include resource_input.input_id in this tuple.
        EXPECTED_V1_ID, resource_input.input_id, asdict(evidence), h,
        # Include input_status in this tuple.
        resolved, input_status)
    # Set resolution_id to a tuple containing the text 'TRAINING_RESOURCE_BUDGET_RESOLUTION_V1', the hexadecimal
    # digest from...
    resolution_id = (
        "TRAINING_RESOURCE_BUDGET_RESOLUTION_V1",
        # Include the hexadecimal digest from hashlib.sha256(repr(resolution_fields).encode()) in this tuple.
        hashlib.sha256(repr(resolution_fields).encode()).hexdigest())
    # Set resolution to the result of TrainingResourceBudgetResolution().
    resolution = TrainingResourceBudgetResolution(
        # Supply resolution_id as resolution_id.
        # Supply source_protocol_id as EXPECTED_V1_ID.
        resolution_id=resolution_id, source_protocol_id=EXPECTED_V1_ID,
        # Supply input_requirement_name as the text 'MAXIMUM_ACCEPTABLE_TRAINING_RESOURCE_BUDGET'.
        input_requirement_name="MAXIMUM_ACCEPTABLE_TRAINING_RESOURCE_BUDGET",
        # Supply resource_input as resource_input.
        # Supply resource_evidence as evidence.
        resource_input=resource_input, resource_evidence=evidence,
        # Supply derived_H as h.
        # Supply derived_policy_state_count as h plus 1 when resolved, otherwise None.
        derived_H=h, derived_policy_state_count=h + 1 if resolved else None,
        # Supply derived_manifest_collection_count as h plus 1 when resolved, otherwise None.
        derived_manifest_collection_count=h + 1 if resolved else None,
        # Supply derived_sumo_steps_per_replication as h plus 1 multiplied by
        # evidence.sumo_steps_per_training_manifest when resolved, otherwise None.
        derived_sumo_steps_per_replication=(
            # Evaluate h plus 1 multiplied by evidence.sumo_steps_per_training_manifest when resolved, otherwise
            # None as part of the enclosing expression.
            (h + 1) * evidence.sumo_steps_per_training_manifest
            # Evaluate resolved as part of the enclosing expression.
            if resolved else None),
        # Supply derived_conservative_wall_clock_bound as wall_bound.
        derived_conservative_wall_clock_bound=wall_bound,
        # Supply unused_capacity as unused.
        # Supply resource_budget_resolved as resolved.
        unused_capacity=unused, resource_budget_resolved=resolved,
        # Supply performance_used_to_choose_budget as False.
        performance_used_to_choose_budget=False,
        # Supply performance_used_to_derive_H as False.
        performance_used_to_derive_H=False,
        # Supply project_selected as resolved.
        project_selected=resolved,
        # Supply provenance as a tuple containing a tuple containing the text 'checkpoint', the text
        # 'STEP_5J_3C_2E_1', a tuple containing the text...
        provenance=(("checkpoint", "STEP_5J_3C_2E_1"),
                    # Include a tuple containing the text 'input_validation_status', input_status in this tuple.
                    ("input_validation_status", input_status)))
    # Set artifact to a dictionary containing checkpoint, status, resource_budget_resolution_status,
    # resolution,...
    artifact = {
        "checkpoint": "STEP_5J_3C_2E_1",
        # Store the text 'TRAINING_RESOURCE_BUDGET_RESOLVED' when resolved, otherwise the text
        # 'TRAINING_RESOURCE_BUDGET_EXTERNAL_INPUT_REQUIRED' under 'status'.
        "status": ("TRAINING_RESOURCE_BUDGET_RESOLVED" if resolved else
                   "TRAINING_RESOURCE_BUDGET_EXTERNAL_INPUT_REQUIRED"),
        # Store input_status under 'resource_budget_resolution_status'.
        "resource_budget_resolution_status": input_status,
        # Store the result of asdict(resolution) under 'resolution'.
        "resolution": asdict(resolution),
        # Store resolved under 'training_horizon_selected'.
        "training_horizon_selected": resolved,
        # Store False under 'training_horizon_optimal_claim'.
        "training_horizon_optimal_claim": False,
        # Store False under 'performance_used_to_choose_resource_budget'.
        "performance_used_to_choose_resource_budget": False,
        # Store False under 'performance_used_to_derive_H'.
        "performance_used_to_derive_H": False,
        # Store False under 'v1_modified'.
        "v1_modified": False,
        # Store resolved under 'new_protocol_identity_created'.
        "new_protocol_identity_created": resolved,
        # Store protocol_id under 'new_v2_protocol_identity'.
        "new_v2_protocol_identity": protocol_id,
        # Store a list built from REMAINING_INPUT_ORDER when resolved, otherwise a list containing the text
        # 'MAXIMUM_ACCEPTABLE_TRAINING_RESOURCE_BUDGET' plus a list built from REMAINING_INPUT_ORDER under
        # 'remaining_external_blockers'.
        "remaining_external_blockers": (
            # Evaluate a list built from REMAINING_INPUT_ORDER when resolved, otherwise a list containing the text
            # 'MAXIMUM_ACCEPTABLE_TRAINING_RESOURCE_BUDGET' plus a list built from REMAINING_INPUT_ORDER as part
            # of the enclosing expression.
            list(REMAINING_INPUT_ORDER) if resolved else
            # Evaluate a list containing the text 'MAXIMUM_ACCEPTABLE_TRAINING_RESOURCE_BUDGET' plus a list built
            # from REMAINING_INPUT_ORDER as part of the enclosing expression.
            ["MAXIMUM_ACCEPTABLE_TRAINING_RESOURCE_BUDGET"] +
            # Evaluate a list built from REMAINING_INPUT_ORDER as part of the enclosing expression.
            list(REMAINING_INPUT_ORDER)),
        # Store 0 under 'new_sumo_executions'.
        # Store 0 under 'training_episodes'.
        "new_sumo_executions": 0, "training_episodes": 0,
        # Store 0 under 'optimizer_invocations'.
        # Store 0 under 'backward_calls'.
        "optimizer_invocations": 0, "backward_calls": 0,
        # Store 0 under 'parameter_updates'.
        # Store 0 under 'validation_executions'.
        "parameter_updates": 0, "validation_executions": 0,
        # Store 0 under 'held_out_executions'.
        "held_out_executions": 0,
        # Store the text 'STRUCTURE_DEFINED_ADDITIONAL_EXTERNAL_INPUTS_REQUIRED' when resolved, otherwise the text
        # 'STRUCTURE_DEFINED_EXTERNAL_INPUTS_REQUIRED' under 'protocol_readiness'.
        "protocol_readiness": (
            "STRUCTURE_DEFINED_ADDITIONAL_EXTERNAL_INPUTS_REQUIRED"
            # Evaluate resolved as part of the enclosing expression.
            if resolved else "STRUCTURE_DEFINED_EXTERNAL_INPUTS_REQUIRED"),
        # Store the text 'MINIMUM_PRACTICALLY_IMPORTANT_DIFFERENCE_TEAM_TRAVEL_TIME_SECONDS' when resolved,
        # otherwise the text 'MAXIMUM_ACCEPTABLE_TRAINING_RESOURCE_BUDGET_VALUE_REQUIRED' under 'next_blocker'.
        "next_blocker": (
            "MINIMUM_PRACTICALLY_IMPORTANT_DIFFERENCE_TEAM_TRAVEL_TIME_SECONDS"
            # Evaluate resolved as part of the enclosing expression.
            if resolved else
            "MAXIMUM_ACCEPTABLE_TRAINING_RESOURCE_BUDGET_VALUE_REQUIRED")}
    # Write the supplied text to Path(resolution_path).
    Path(resolution_path).write_text(json.dumps(artifact, indent=2),
                                     # Supply encoding as the text 'utf-8'.
                                     encoding="utf-8")
    # Return a tuple containing resolution, artifact to the caller.
    return resolution, artifact
