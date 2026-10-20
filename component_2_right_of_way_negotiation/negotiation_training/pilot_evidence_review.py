"""Analysis-only Step 5J.3C.2 review of existing closed-loop evidence."""

# Import Mapping from collections.abc for the operations below.
from collections.abc import Mapping
# Import dataclass, fields from dataclasses for the operations below.
from dataclasses import dataclass, fields
# Import hashlib for use in this module.
import hashlib
# Import json for use in this module.
import json
# Import Path from pathlib for the operations below.
from pathlib import Path
# Import MappingProxyType from types for the operations below.
from types import MappingProxyType
# Import Tuple from typing for the operations below.
from typing import Tuple

# Import ScenarioRole, build_design from experimentation for the operations below.
from experimentation import ScenarioRole, build_design


# Set SOURCE_PATH to the result of Path(the text 'results/mappo_closed_loop_pilot_evidence.json').
SOURCE_PATH = Path("results/mappo_closed_loop_pilot_evidence.json")
# Set REVIEW_PATH to the result of Path(the text 'results/mappo_pilot_evidence_review.json').
REVIEW_PATH = Path("results/mappo_pilot_evidence_review.json")


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define ExtendedMAPPOEvidenceAcquisitionDesign to group the state and operations declared below.
# Declared fields: design_id, source_pilot_evidence_id, frozen_experimental_design_id, training_manifest_id,
# validation_manifest_id, held_out_manifest_id, current_replication_evidence_status,....
# Construction and attribute behavior follow the declared decorators and base classes.
class ExtendedMAPPOEvidenceAcquisitionDesign:
    # Declare design_id as Tuple[str, str] for this data structure.
    design_id: Tuple[str, str]
    # Declare source_pilot_evidence_id as Tuple[str, str] for this data structure.
    source_pilot_evidence_id: Tuple[str, str]
    # Declare frozen_experimental_design_id as tuple for this data structure.
    frozen_experimental_design_id: tuple
    # Declare training_manifest_id as tuple for this data structure.
    training_manifest_id: tuple
    # Declare validation_manifest_id as tuple for this data structure.
    validation_manifest_id: tuple
    # Declare held_out_manifest_id as tuple for this data structure.
    held_out_manifest_id: tuple
    # Declare current_replication_evidence_status as str for this data structure.
    current_replication_evidence_status: str
    # Declare current_training_budget_evidence_status as str for this data structure.
    current_training_budget_evidence_status: str
    # Declare replication_extension_rule as dict for this data structure.
    replication_extension_rule: dict
    # Declare training_curve_extension_rule as dict for this data structure.
    training_curve_extension_rule: dict
    # Declare measurement_schedule as tuple for this data structure.
    measurement_schedule: tuple
    # Declare selection_data_boundary as dict for this data structure.
    selection_data_boundary: dict
    # Declare held_out_sealed as bool for this data structure.
    held_out_sealed: bool
    # Declare performance_seed_selection_forbidden as bool for this data structure.
    performance_seed_selection_forbidden: bool
    # Declare final_counts_selected as bool for this data structure.
    final_counts_selected: bool
    # Declare provenance as dict for this data structure.
    provenance: dict

    # Post init using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    # Processing: iterate over the relevant records.
    def __post_init__(self):
        # Iterate over a tuple containing the text 'replication_extension_rule', the text
        # 'training_curve_extension_rule', the text..., binding each item to name.
        for name in ("replication_extension_rule",
                     "training_curve_extension_rule",
                     "selection_data_boundary", "provenance"):
            # Call object.__setattr__ with the supplied arguments.
            object.__setattr__(self, name,
                               # Supply the result of MappingProxyType(a dictionary built from the requested
                               # attribute of self) to object.__setattr__.
                               MappingProxyType(dict(getattr(self, name))))


# Jsonable using the inputs and processing steps below.
# Input value: the supplied value.
# Output: return the value selected by the matching return branch below.
# Processing: select branches using the stated conditions.
def _jsonable(value):
    # Run this branch when whether value has type Mapping.
    if isinstance(value, Mapping):
        # Return a dictionary of key mapped to the result of _jsonable(item) for (key, item) in key/value pairs
        # from value to the caller.
        return {key: _jsonable(item) for key, item in value.items()}
    # Run this branch when whether value has type a tuple containing tuple, list.
    if isinstance(value, (tuple, list)):
        # Return a list of the result of _jsonable(item) for item in value to the caller.
        return [_jsonable(item) for item in value]
    # Return value to the caller.
    return value


# Dataclass payload using the inputs and processing steps below.
# Input value: the supplied value.
# Output: a dictionary of field.name mapped to the result of _jsonable(the requested attribute of value) for field
# in the result of fields(value).
def _dataclass_payload(value):
    # Return a dictionary of field.name mapped to the result of _jsonable(the requested attribute of value) for
    # field in the result of fields(value) to the caller.
    return {field.name: _jsonable(getattr(value, field.name))
            # Evaluate the result of fields(value) as part of the enclosing expression.
            for field in fields(value)}


# Digest using the inputs and processing steps below.
# Input value: the supplied value.
# Output: the hexadecimal digest from hashlib.sha256(encoded).
def _digest(value):
    # Set encoded to the result of json.dumps(_jsonable(value), sort_keys=True, separators=(',', ':')).encode().
    encoded = json.dumps(_jsonable(value), sort_keys=True,
                         # Supply separators as a tuple containing the text ',', the text ':'.
                         separators=(",", ":")).encode()
    # Return the hexadecimal digest from hashlib.sha256(encoded) to the caller.
    return hashlib.sha256(encoded).hexdigest()


# Load and validate pilot evidence using the inputs and processing steps below.
# Input path: the path or path object supplied by the caller.
# Output: evidence.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def load_and_validate_pilot_evidence(path=SOURCE_PATH):
    # Set evidence to the decoded data produced by json.loads from the text read from Path(path).
    evidence = json.loads(Path(path).read_text(encoding="utf-8"))
    # Set required to a dictionary containing status, replication_count, validation_runs, held_out_runs,
    # collisions,...
    required = {
        "status": "CLOSED_LOOP_PROGRESS_AND_VARIANCE_PROBE_COMPLETE",
        # Store 2 under 'replication_count'.
        "replication_count": 2,
        # Store 0 under 'validation_runs'.
        "validation_runs": 0,
        # Store 0 under 'held_out_runs'.
        "held_out_runs": 0,
        # Store 0 under 'collisions'.
        "collisions": 0,
        # Store 0 under 'blocked_zone_violations'.
        "blocked_zone_violations": 0,
        "replication_probe_reason": "MINIMUM_SAMPLE_VARIANCE_PROBE",
        # Store False under 'final_training_budget_selected'.
        "final_training_budget_selected": False,
        # Store False under 'final_replication_count_selected'.
        "final_replication_count_selected": False,
    }
    # Iterate over key/value pairs from required, binding each item to (field, expected).
    for field, expected in required.items():
        # Run this branch when field from evidence; use None if absent differs from expected.
        if evidence.get(field) != expected:
            # Raise ValueError with formatted text built from the embedded values to stop this execution path.
            raise ValueError(f"INVALID_PILOT_EVIDENCE_{field.upper()}")
    # Run this branch when the number of entries in 'replications' from evidence; use an empty tuple if absent
    # differs from 2.
    if len(evidence.get("replications", ())) != 2:
        # Raise ValueError with the text 'EXACTLY_TWO_PILOT_REPLICATIONS_REQUIRED' to stop this execution path.
        raise ValueError("EXACTLY_TWO_PILOT_REPLICATIONS_REQUIRED")
    # Run this branch when whether any item is true in a lazy sequence of 'seed_selected_by_performance' from
    # item; use None if absent is a different object from False for item in evidence at 'replications'.
    if any(item.get("seed_selected_by_performance") is not False
           # Evaluate evidence at 'replications' as part of the enclosing expression.
           for item in evidence["replications"]):
        # Raise ValueError with the text 'PERFORMANCE_SELECTED_PILOT_SEED_FORBIDDEN' to stop this execution path.
        raise ValueError("PERFORMANCE_SELECTED_PILOT_SEED_FORBIDDEN")
    # Return evidence to the caller.
    return evidence


# Build extended evidence acquisition design using the inputs and processing steps below.
# Input evidence: the supplied evidence.
# Input design: the supplied design.
# Output: the result of ExtendedMAPPOEvidenceAcquisitionDesign().
def build_extended_evidence_acquisition_design(evidence, design):
    # Set source_id to a tuple containing the text 'MAPPO_CLOSED_LOOP_PILOT_EVIDENCE_V1', the result of
    # _digest(evidence).
    source_id = ("MAPPO_CLOSED_LOOP_PILOT_EVIDENCE_V1", _digest(evidence))
    # Set manifests to design at 'manifests'.
    manifests = design["manifests"]
    # Set identity_fields to a tuple containing source_id, design['freeze'].freeze_id,
    # manifests[ScenarioRole.TRAINING].manifest_id,...
    identity_fields = (
        # Include design['freeze'].freeze_id in this tuple.
        source_id, design["freeze"].freeze_id,
        # Include manifests[ScenarioRole.TRAINING].manifest_id in this tuple.
        manifests[ScenarioRole.TRAINING].manifest_id,
        # Include manifests[ScenarioRole.VALIDATION].manifest_id in this tuple.
        manifests[ScenarioRole.VALIDATION].manifest_id,
        # Include manifests[ScenarioRole.HELD_OUT_TEST].manifest_id in this tuple.
        manifests[ScenarioRole.HELD_OUT_TEST].manifest_id,
        "CANONICAL_CONTIGUOUS_REPLICATION_STREAM_FROM_INDEX_2",
        "SEQUENTIAL_CURRENT_POLICY_ON_POLICY_MANIFEST_UPDATES")
    # Return the result of ExtendedMAPPOEvidenceAcquisitionDesign() to the caller.
    return ExtendedMAPPOEvidenceAcquisitionDesign(
        # Supply design_id as a tuple containing the text 'EXTENDED_MAPPO_EVIDENCE_ACQUISITION_DESIGN_V1', the
        # result of _digest(identity_fields).
        design_id=("EXTENDED_MAPPO_EVIDENCE_ACQUISITION_DESIGN_V1",
                   # Include the result of _digest(identity_fields) in this tuple.
                   _digest(identity_fields)),
        # Supply source_pilot_evidence_id as source_id.
        source_pilot_evidence_id=source_id,
        # Supply frozen_experimental_design_id as design['freeze'].freeze_id.
        frozen_experimental_design_id=design["freeze"].freeze_id,
        # Supply training_manifest_id as manifests[ScenarioRole.TRAINING].manifest_id.
        training_manifest_id=manifests[ScenarioRole.TRAINING].manifest_id,
        # Supply validation_manifest_id as manifests[ScenarioRole.VALIDATION].manifest_id.
        validation_manifest_id=manifests[ScenarioRole.VALIDATION].manifest_id,
        # Supply held_out_manifest_id as manifests[ScenarioRole.HELD_OUT_TEST].manifest_id.
        held_out_manifest_id=manifests[ScenarioRole.HELD_OUT_TEST].manifest_id,
        # Supply current_replication_evidence_status as the text 'INSUFFICIENT_MINIMUM_TWO_RUN_VARIANCE_PROBE'.
        current_replication_evidence_status=
            "INSUFFICIENT_MINIMUM_TWO_RUN_VARIANCE_PROBE",
        # Supply current_training_budget_evidence_status as the text 'INSUFFICIENT_SINGLE_UPDATE_INTERVAL'.
        current_training_budget_evidence_status=
            "INSUFFICIENT_SINGLE_UPDATE_INTERVAL",
        # Supply replication_extension_rule as a dictionary containing stream, next_index, order,
        # termination_count, performance_based_replacement.
        replication_extension_rule={
            "stream": "CANONICAL_DETERMINISTIC_REPLICATION_STREAM",
            # Store 2 under 'next_index'.
            "next_index": 2,
            "order": "2,3,4,..._WITHOUT_SKIPPING",
            "termination_count": "NOT_YET_SELECTED",
            # Store False under 'performance_based_replacement'.
            "performance_based_replacement": False},
        # Supply training_curve_extension_rule as a dictionary containing sequence, collection, update_data,
        # stale_rollout_reuse, final_update_count,...
        training_curve_extension_rule={
            "sequence": "STATE_K_COLLECTION_THEN_UPDATE_K_PLUS_1",
            "collection": "FULL_FROZEN_TRAINING_MANIFEST",
            "update_data": "IMMEDIATELY_PRECEDING_CURRENT_POLICY_ON_POLICY_DATA_ONLY",
            # Store False under 'stale_rollout_reuse'.
            "stale_rollout_reuse": False,
            "final_update_count": "NOT_YET_SELECTED",
            "convergence_rule": "STATISTICAL_SELECTION_RULE_REQUIRES_PREDECLARATION"},
        # Supply measurement_schedule as a tuple containing the text 'policy_identity', the text
        # 'critic_identity', the text 'training_team_travel_time', the text...
        measurement_schedule=(
            "policy_identity", "critic_identity", "training_team_travel_time",
            "per_scenario_travel_times", "physical_executable_outcomes",
            "coordination_cycles", "physical_cycles", "action_frequencies",
            "completed_vehicles", "collision_count",
            "blocked_zone_violations", "policy_factor_count", "sumo_steps",
            "wall_clock_runtime"),
        # Supply selection_data_boundary as a dictionary containing configuration_selection_roles,
        # training_budget_probe_role, held_out_role,...
        selection_data_boundary={
            # Store a tuple containing the text 'TRAINING', the text 'VALIDATION' under
            # 'configuration_selection_roles'.
            "configuration_selection_roles": ("TRAINING", "VALIDATION"),
            "training_budget_probe_role": "TRAINING_ONLY",
            "held_out_role": "SEALED_FINAL_EVALUATION",
            # Store False under 'new_scenario_identities_added'.
            "new_scenario_identities_added": False,
            "future_external_stress_test_classification":
                "POST_SELECTION_EXTERNAL_GENERALIZATION_EXPERIMENT"},
        # Supply held_out_sealed as True.
        held_out_sealed=True,
        # Supply performance_seed_selection_forbidden as True.
        performance_seed_selection_forbidden=True,
        # Supply final_counts_selected as False.
        final_counts_selected=False,
        # Supply provenance as a dictionary containing checkpoint, derivation, sumo_runs, optimizer_invocations,
        # backward_calls,...
        provenance={
            "checkpoint": "STEP_5J_3C_2",
            "derivation": "EXISTING_STEP_5J_3C_1_EVIDENCE_ONLY",
            # Store 0 under 'sumo_runs'.
            # Store 0 under 'optimizer_invocations'.
            "sumo_runs": 0, "optimizer_invocations": 0,
            # Store 0 under 'backward_calls'.
            # Store 0 under 'parameter_updates'.
            "backward_calls": 0, "parameter_updates": 0})


# Build pilot evidence review using the inputs and processing steps below.
# Input source_path: the supplied source path.
# Input output_path: the supplied output path.
# Output: result.
def build_pilot_evidence_review(source_path=SOURCE_PATH,
                                # Declare output_path as input parameter.
                                output_path=REVIEW_PATH):
    # Set evidence to the result of load_and_validate_pilot_evidence(source_path).
    evidence = load_and_validate_pilot_evidence(source_path)
    # Set design to the result of build_design().
    design = build_design()
    # Set replications to evidence at 'replications'.
    replications = evidence["replications"]
    # Set deltas to a list of item at 'delta_team_travel_time_seconds' for item in replications.
    deltas = [item["delta_team_travel_time_seconds"]
              # Evaluate replications as part of the enclosing expression.
              for item in replications]
    # Set variance to evidence['variance_evidence'] at 'delta'.
    variance = evidence["variance_evidence"]["delta"]
    # Set extended to the result of build_extended_evidence_acquisition_design(evidence, design).
    extended = build_extended_evidence_acquisition_design(evidence, design)
    # Set training_manifest to design['manifests'] at ScenarioRole.TRAINING.
    training_manifest = design["manifests"][ScenarioRole.TRAINING]
    # Set result to a dictionary containing checkpoint, status, source_pilot_identity, source_pilot_path,
    # pilot_statistics,...
    result = {
        "checkpoint": "STEP_5J_3C_2",
        "status": "PILOT_EVIDENCE_REVIEW_COMPLETE",
        # Store a list built from extended.source_pilot_evidence_id under 'source_pilot_identity'.
        "source_pilot_identity": list(extended.source_pilot_evidence_id),
        # Store a string built from source_path under 'source_pilot_path'.
        "source_pilot_path": str(source_path),
        # Store a dictionary containing replications_observed, replication_indices_preserved,
        # replications_discarded,... under 'pilot_statistics'.
        "pilot_statistics": {
            # Store 2 under 'replications_observed'.
            "replications_observed": 2,
            # Store a list of item at 'replication_index' for item in replications under
            # 'replication_indices_preserved'.
            "replication_indices_preserved": [item["replication_index"]
                                                # Evaluate replications as part of the enclosing expression.
                                                for item in replications],
            # Store 0 under 'replications_discarded'.
            "replications_discarded": 0,
            # Store 1 under 'ppo_update_intervals_per_replication'.
            "ppo_update_intervals_per_replication": 1,
            # Store the number of entries in training_manifest.scenario_ids under 'unique_training_scenarios'.
            "unique_training_scenarios": len(training_manifest.scenario_ids),
            # Store evidence at 'total_training_manifest_collections' under 'training_manifest_passes'.
            "training_manifest_passes": evidence["total_training_manifest_collections"],
            # Store evidence at 'total_training_scenario_executions' under 'training_exposure_episodes'.
            "training_exposure_episodes": evidence["total_training_scenario_executions"],
            # Store deltas under 'delta_values'.
            "delta_values": deltas,
            # Store variance at 'sample_mean' under 'delta_sample_mean'.
            "delta_sample_mean": variance["sample_mean"],
            # Store variance at 'sample_variance_n_minus_1' under 'delta_sample_variance_n_minus_1'.
            "delta_sample_variance_n_minus_1": variance["sample_variance_n_minus_1"],
            # Store variance at 'sample_standard_deviation' under 'delta_sample_standard_deviation'.
            "delta_sample_standard_deviation": variance["sample_standard_deviation"],
            # Store 0 under 'validation_runs'.
            # Store 0 under 'held_out_runs'.
            "validation_runs": 0, "held_out_runs": 0,
            # Store 0 under 'collisions'.
            # Store 0 under 'blocked_zone_violations'.
            "collisions": 0, "blocked_zone_violations": 0},
        # Store a dictionary containing status, final_budget_justified, final_training_budget_selected, reason,
        # established,... under 'training_budget_sufficiency_assessment'.
        "training_budget_sufficiency_assessment": {
            "status": "INSUFFICIENT_SINGLE_UPDATE_INTERVAL",
            # Store False under 'final_budget_justified'.
            "final_budget_justified": False,
            # Store False under 'final_training_budget_selected'.
            "final_training_budget_selected": False,
            "reason": "ONLY_ONE_UPDATE_INTERVAL_OBSERVED",
            "established": "PARAMETER_LEARNING_CAN_ALTER_PHYSICAL_TRAFFIC_OUTCOME",
            # Store a list containing the text 'LEARNING_CURVE_SHAPE', the text 'PLATEAU', the text 'CONVERGENCE',
            # the text... under 'not_established'.
            "not_established": ["LEARNING_CURVE_SHAPE", "PLATEAU",
                                "CONVERGENCE", "OVER_TRAINING_BEHAVIOR",
                                "LATER_DEGRADATION", "BEST_TRAINING_DURATION"]},
        # Store a dictionary containing status, final_replication_count_justified,
        # final_replication_count_selected, reason,... under 'replication_sufficiency_assessment'.
        "replication_sufficiency_assessment": {
            "status": "INSUFFICIENT_MINIMUM_TWO_RUN_VARIANCE_PROBE",
            # Store False under 'final_replication_count_justified'.
            "final_replication_count_justified": False,
            # Store False under 'final_replication_count_selected'.
            "final_replication_count_selected": False,
            "reason": "TWO_RUN_MINIMUM_VARIANCE_PROBE_ONLY",
            # Store 0 under 'observations_called_outliers'.
            "observations_called_outliers": 0,
            "interpretation": "TWO_OBSERVATIONS_PERMIT_A_FIRST_SAMPLE_VARIANCE_CALCULATION_BUT_POORLY_CHARACTERIZE_THE_VARIANCE"},
        # Store a dictionary containing new_unique_training_scenarios_required_now,... under
        # 'scenario_design_assessment'.
        "scenario_design_assessment": {
            # Store False under 'new_unique_training_scenarios_required_now'.
            "new_unique_training_scenarios_required_now": False,
            # Store True under 'repeated_training_manifest_exposure_required'.
            "repeated_training_manifest_exposure_required": True,
            # Store False under 'partitions_modified'.
            "partitions_modified": False,
            # Store a dictionary containing UNIQUE_TRAINING_SCENARIOS, TRAINING_MANIFEST_PASS, PPO_UPDATE_CYCLE,
            # TRAINING_EXPOSURE under 'terminology'.
            "terminology": {
                "UNIQUE_TRAINING_SCENARIOS": "NUMBER_OF_FROZEN_TRAINING_SCENARIO_IDENTITIES",
                "TRAINING_MANIFEST_PASS": "ONE_EXECUTION_OF_EVERY_FROZEN_TRAINING_SCENARIO",
                "PPO_UPDATE_CYCLE": "ONE_ON_POLICY_MANIFEST_COLLECTION_FOLLOWED_BY_CONFIGURED_PPO_OPTIMIZATION",
                "TRAINING_EXPOSURE": "SCENARIO_EPISODES_GENERATED_ACROSS_MANIFEST_PASSES_AND_REPLICATIONS"}},
        # Store a dictionary containing total_wall_clock_seconds,
        # wall_clock_seconds_per_training_manifest_collection,... under 'compute_cost_evidence'.
        "compute_cost_evidence": {
            # Store evidence at 'total_wall_clock_runtime_seconds' under 'total_wall_clock_seconds'.
            "total_wall_clock_seconds": evidence["total_wall_clock_runtime_seconds"],
            "wall_clock_seconds_per_training_manifest_collection":
                # Evaluate evidence at 'total_wall_clock_runtime_seconds' divided by evidence at
                # 'total_training_manifest_collections' as part of the enclosing expression.
                evidence["total_wall_clock_runtime_seconds"] /
                # Evaluate evidence at 'total_training_manifest_collections' as part of the enclosing expression.
                evidence["total_training_manifest_collections"],
            # Store a list of item['wall_clock_measurements'] at 'total_replication_seconds' for item in
            # replications under 'complete_replication_wall_clock_seconds'.
            "complete_replication_wall_clock_seconds": [
                # Evaluate item['wall_clock_measurements'] at 'total_replication_seconds' as part of the enclosing
                # expression.
                item["wall_clock_measurements"]["total_replication_seconds"]
                # Evaluate replications as part of the enclosing expression.
                for item in replications],
            # Store evidence at 'total_update_runtime_seconds' under 'total_ppo_update_runtime_seconds'.
            "total_ppo_update_runtime_seconds": evidence["total_update_runtime_seconds"],
            # Store a list of item at 'update_runtime_seconds' for item in replications under
            # 'ppo_update_runtime_seconds'.
            "ppo_update_runtime_seconds": [item["update_runtime_seconds"]
                                            # Evaluate replications as part of the enclosing expression.
                                            for item in replications],
            "sumo_steps_per_training_manifest_collection":
                # Evaluate evidence at 'total_sumo_steps' divided by evidence at
                # 'total_training_manifest_collections' as part of the enclosing expression.
                evidence["total_sumo_steps"] /
                # Evaluate evidence at 'total_training_manifest_collections' as part of the enclosing expression.
                evidence["total_training_manifest_collections"],
            # Store False under 'runtime_threshold_imposed'.
            "runtime_threshold_imposed": False},
        # Store the result of _dataclass_payload(extended) under 'extended_evidence_acquisition_design'.
        "extended_evidence_acquisition_design": _dataclass_payload(extended),
        # Store a list containing the text 'TRAINING_BUDGET_SELECTION_CRITERION_REQUIRES_PREDECLARATION', the
        # text... under 'remaining_methodological_blockers'.
        "remaining_methodological_blockers": [
            "TRAINING_BUDGET_SELECTION_CRITERION_REQUIRES_PREDECLARATION",
            "REPLICATION_COUNT_ADEQUACY_CRITERION_REQUIRES_PREDECLARATION",
            "CANDIDATE_COMPARISON_STATISTIC_REQUIRES_PREDECLARATION",
            "TIE_RULE_REQUIRES_PREDECLARATION",
            "CHECKPOINT_MODEL_SELECTION_RULE_REQUIRES_PREDECLARATION",
            "STATISTICAL_SELECTION_RULE_REQUIRES_PREDECLARATION"],
        # Store False under 'candidate_experiments_started'.
        "candidate_experiments_started": False,
        # Store 0 under 'arbitrary_convergence_thresholds'.
        "arbitrary_convergence_thresholds": 0,
        # Store False under 'final_counts_selected'.
        "final_counts_selected": False,
        # Store 0 under 'sumo_invocations'.
        # Store 0 under 'optimizer_invocations'.
        "sumo_invocations": 0, "optimizer_invocations": 0,
        # Store 0 under 'backward_calls'.
        # Store 0 under 'model_parameter_updates'.
        "backward_calls": 0, "model_parameter_updates": 0,
        "training_budget_evidence": "INSUFFICIENT_SINGLE_UPDATE_INTERVAL",
        "replication_evidence": "INSUFFICIENT_MINIMUM_TWO_RUN_VARIANCE_PROBE",
        "next_readiness": "READY_TO_DEFINE_EXTENDED_LEARNING_EVIDENCE_PROTOCOL",
        "next_checkpoint": "STEP_5J_3C_2B"}
    # Write the supplied text to Path(output_path).
    Path(output_path).write_text(json.dumps(result, indent=2), encoding="utf-8")
    # Return result to the caller.
    return result
