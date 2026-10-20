"""Immutable, analysis-only Step 5J.3C.2D MAPPO selection protocol."""

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
# Import Any, Tuple from typing for the operations below.
from typing import Any, Tuple

# Import build_design from experimentation for the operations below.
from experimentation import build_design


# Set SOURCE_PATH to the result of Path(the text 'results/mappo_extended_evidence_review.json').
SOURCE_PATH = Path("results/mappo_extended_evidence_review.json")
# Set OUTPUT_PATH to the result of Path(the text 'results/mappo_predeclared_selection_protocol.json').
OUTPUT_PATH = Path("results/mappo_predeclared_selection_protocol.json")

# Set PRIOR_BLOCKERS to a tuple containing the text 'TRAINING_BUDGET_SELECTION_CRITERION_REQUIRES_PREDECLARATION',
# the text...
PRIOR_BLOCKERS = (
    "TRAINING_BUDGET_SELECTION_CRITERION_REQUIRES_PREDECLARATION",
    "REPLICATION_COUNT_ADEQUACY_CRITERION_REQUIRES_PREDECLARATION",
    "CANDIDATE_COMPARISON_STATISTIC_REQUIRES_PREDECLARATION",
    "TIE_RULE_REQUIRES_PREDECLARATION",
    "CHECKPOINT_MODEL_SELECTION_RULE_REQUIRES_PREDECLARATION",
    "STATISTICAL_SELECTION_RULE_REQUIRES_PREDECLARATION",
)


# Freeze using the inputs and processing steps below.
# Input value: the supplied value.
# Output: return the value selected by the matching return branch below.
# Processing: select branches using the stated conditions.
def _freeze(value):
    # Run this branch when whether value has type Mapping.
    if isinstance(value, Mapping):
        # Return the result of MappingProxyType(a dictionary of key mapped to the result of _freeze(item) for
        # (key, item) in key/value pairs...) to the caller.
        return MappingProxyType({key: _freeze(item)
                                 # Evaluate key/value pairs from value as part of the enclosing expression.
                                 for key, item in value.items()})
    # Run this branch when whether value has type a tuple containing list, tuple.
    if isinstance(value, (list, tuple)):
        # Return a tuple built from a lazy sequence of the result of _freeze(item) for item in value to the
        # caller.
        return tuple(_freeze(item) for item in value)
    # Return value to the caller.
    return value


# Thaw using the inputs and processing steps below.
# Input value: the supplied value.
# Output: return the value selected by the matching return branch below.
# Processing: select branches using the stated conditions.
def _thaw(value):
    # Run this branch when whether value has type Mapping.
    if isinstance(value, Mapping):
        # Return a dictionary of key mapped to the result of _thaw(item) for (key, item) in key/value pairs from
        # value to the caller.
        return {key: _thaw(item) for key, item in value.items()}
    # Run this branch when whether value has type tuple.
    if isinstance(value, tuple):
        # Return a list of the result of _thaw(item) for item in value to the caller.
        return [_thaw(item) for item in value]
    # Return value to the caller.
    return value


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define ExternalInputRequirement to group the state and operations declared below.
# Declared fields: input_name, status, why_required, unit, allowed_source_of_justification,
# cannot_be_derived_from_existing_results, blocks_which_next_action.
# Construction and attribute behavior follow the declared decorators and base classes.
class ExternalInputRequirement:
    # Declare input_name as str for this data structure.
    input_name: str
    # Declare status as str for this data structure.
    status: str
    # Declare why_required as str for this data structure.
    why_required: str
    # Declare unit as str for this data structure.
    unit: str
    # Declare allowed_source_of_justification as Tuple[str, ...] for this data structure.
    allowed_source_of_justification: Tuple[str, ...]
    # Declare cannot_be_derived_from_existing_results as bool for this data structure.
    cannot_be_derived_from_existing_results: bool
    # Declare blocks_which_next_action as Tuple[str, ...] for this data structure.
    blocks_which_next_action: Tuple[str, ...]


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define MAPPOSelectionProtocol to group the state and operations declared below.
# Declared fields: protocol_id, source_review_identity, frozen_experimental_design_id, primary_metric,
# hard_validity_gates, training_budget_protocol, replication_protocol, checkpoint_selection_protocol,....
# Construction and attribute behavior follow the declared decorators and base classes.
class MAPPOSelectionProtocol:
    # Declare protocol_id as tuple for this data structure.
    protocol_id: tuple
    # Declare source_review_identity as Mapping[str, Any] for this data structure.
    source_review_identity: Mapping[str, Any]
    # Declare frozen_experimental_design_id as tuple for this data structure.
    frozen_experimental_design_id: tuple
    # Declare primary_metric as Mapping[str, Any] for this data structure.
    primary_metric: Mapping[str, Any]
    # Declare hard_validity_gates as tuple for this data structure.
    hard_validity_gates: tuple
    # Declare training_budget_protocol as Mapping[str, Any] for this data structure.
    training_budget_protocol: Mapping[str, Any]
    # Declare replication_protocol as Mapping[str, Any] for this data structure.
    replication_protocol: Mapping[str, Any]
    # Declare checkpoint_selection_protocol as Mapping[str, Any] for this data structure.
    checkpoint_selection_protocol: Mapping[str, Any]
    # Declare candidate_comparison_protocol as Mapping[str, Any] for this data structure.
    candidate_comparison_protocol: Mapping[str, Any]
    # Declare uncertainty_reporting_protocol as Mapping[str, Any] for this data structure.
    uncertainty_reporting_protocol: Mapping[str, Any]
    # Declare tie_protocol as Mapping[str, Any] for this data structure.
    tie_protocol: Mapping[str, Any]
    # Declare extension_protocol as Mapping[str, Any] for this data structure.
    extension_protocol: Mapping[str, Any]
    # Declare data_role_protocol as Mapping[str, Any] for this data structure.
    data_role_protocol: Mapping[str, Any]
    # Declare unresolved_external_inputs as Tuple[ExternalInputRequirement, ...] for this data structure.
    unresolved_external_inputs: Tuple[ExternalInputRequirement, ...]
    # Declare freeze_status as str for this data structure.
    freeze_status: str
    # Declare provenance as Mapping[str, Any] for this data structure.
    provenance: Mapping[str, Any]

    # Post init using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    def __post_init__(self):
        # Iterate over the result of fields(self), binding each item to field.
        for field in fields(self):
            # Run this branch when field.name does not belong to a tuple containing the text 'protocol_id', the
            # text 'unresolved_external_inputs'.
            if field.name not in ("protocol_id", "unresolved_external_inputs"):
                # Call object.__setattr__ with the supplied arguments.
                object.__setattr__(self, field.name,
                                   # Supply the result of _freeze(the requested attribute of self) to
                                   # object.__setattr__.
                                   _freeze(getattr(self, field.name)))


# Canonical json using the inputs and processing steps below.
# Input value: the supplied value.
# Output: the serialized data produced by json.dumps.
def _canonical_json(value):
    # Return the serialized data produced by json.dumps to the caller.
    return json.dumps(_thaw(value), sort_keys=True,
                      # Supply separators as a tuple containing the text ',', the text ':'.
                      separators=(",", ":"))


# External input using the inputs and processing steps below.
# Input name: the supplied name.
# Input why: the supplied why.
# Input unit: the supplied unit.
# Input sources: the supplied sources.
# Input blocks: the supplied blocks.
# Input status: the supplied status.
# Output: the result of ExternalInputRequirement().
def _external_input(name, why, unit, sources, blocks,
                    # Declare status as input parameter.
                    status="REQUIRES_PREDECLARATION"):
    # Return the result of ExternalInputRequirement() to the caller.
    return ExternalInputRequirement(
        # Supply input_name as name.
        # Supply status as status.
        # Supply why_required as why.
        # Supply unit as unit.
        input_name=name, status=status, why_required=why, unit=unit,
        # Supply allowed_source_of_justification as a tuple built from sources.
        allowed_source_of_justification=tuple(sources),
        # Supply cannot_be_derived_from_existing_results as True.
        cannot_be_derived_from_existing_results=True,
        # Supply blocks_which_next_action as a tuple built from blocks.
        blocks_which_next_action=tuple(blocks))


# Load and validate source review using the inputs and processing steps below.
# Input path: the path or path object supplied by the caller.
# Output: review.
# Processing: select branches using the stated conditions.
def load_and_validate_source_review(path=SOURCE_PATH):
    # Set review to the decoded data produced by json.loads from the text read from Path(path).
    review = json.loads(Path(path).read_text(encoding="utf-8"))
    # Run this branch when 'checkpoint' from review; use None if absent differs from the text 'STEP_5J_3C_2C' or
    # 'status' from review; use None if absent differs from the text 'EXTENDED_EVIDENCE_REVIEW_COMPLETE' or
    # 'next_checkpoint' from review; use None if absent differs from the text
    # 'STEP_5J_3C_2D_PREDECLARED_SELECTION_PROTOCOL' or a tuple built from 'methodological_blockers' from review;
    # use () if absent differs from PRIOR_BLOCKERS or whether any item is true in a lazy sequence of value differs
    # from 'STILL_REQUIRES_PREDECLARATION' for value in values from
    # review.get('methodological_blocker_assessment', {}).
    if (review.get("checkpoint") != "STEP_5J_3C_2C" or
            # Evaluate 'status' from review; use None if absent differs from the text
            # 'EXTENDED_EVIDENCE_REVIEW_COMPLETE' as part of the enclosing expression.
            review.get("status") != "EXTENDED_EVIDENCE_REVIEW_COMPLETE" or
            # Evaluate 'next_checkpoint' from review; use None if absent differs from the text
            # 'STEP_5J_3C_2D_PREDECLARED_SELECTION_PROTOCOL' as part of the enclosing expression.
            review.get("next_checkpoint") !=
            # Supply the text 'STEP_5J_3C_2D_PREDECLARED_SELECTION_PROTOCOL' to the enclosing expression.
            "STEP_5J_3C_2D_PREDECLARED_SELECTION_PROTOCOL" or
            # Evaluate a tuple built from 'methodological_blockers' from review; use an empty tuple if absent
            # differs from PRIOR_BLOCKERS as part of the enclosing expression.
            tuple(review.get("methodological_blockers", ())) != PRIOR_BLOCKERS or
            # Evaluate whether any item is true in a lazy sequence of value differs from the text
            # 'STILL_REQUIRES_PREDECLARATION' for value in values from
            # review.get('methodological_blocker_assessment', {}) as part of the enclosing expression.
            any(value != "STILL_REQUIRES_PREDECLARATION" for value in
                # Evaluate values from review.get('methodological_blocker_assessment', {}) as part of the
                # enclosing expression.
                review.get("methodological_blocker_assessment", {}).values())):
        # Raise ValueError with the text 'SELECTION_PROTOCOL_SOURCE_REVIEW_INVALID' to stop this execution path.
        raise ValueError("SELECTION_PROTOCOL_SOURCE_REVIEW_INVALID")
    # Return review to the caller.
    return review


# Evaluate selection protocol readiness using the inputs and processing steps below.
# Input protocol: the supplied protocol.
# Output: return the value selected by the matching return branch below.
# Processing: select branches using the stated conditions.
def evaluate_selection_protocol_readiness(protocol):
    # Run this branch when protocol.unresolved_external_inputs.
    if protocol.unresolved_external_inputs:
        # Return the text 'STRUCTURE_DEFINED_EXTERNAL_INPUTS_REQUIRED' to the caller.
        return "STRUCTURE_DEFINED_EXTERNAL_INPUTS_REQUIRED"
    # Run this branch when protocol.freeze_status differs from the text 'FROZEN'.
    if protocol.freeze_status != "FROZEN":
        # Return the text 'READY_TO_FREEZE_FINAL_SELECTION_PROTOCOL' to the caller.
        return "READY_TO_FREEZE_FINAL_SELECTION_PROTOCOL"
    # Return the text 'FROZEN_SELECTION_PROTOCOL_READY_FOR_EVIDENCE_ACQUISITION' to the caller.
    return "FROZEN_SELECTION_PROTOCOL_READY_FOR_EVIDENCE_ACQUISITION"


# Protocol payload using the inputs and processing steps below.
# Input source_review: the supplied source review.
# Input design: the supplied design.
# Output: a dictionary containing source_review_identity, frozen_experimental_design_id, primary_metric,...
def _protocol_payload(source_review, design):
    # Set plans to a tuple built from a lazy sequence of a dictionary containing plan_id, choice_ids_under_test,
    # execution_status for plan in design at 'plans'.
    plans = tuple({
        # Store plan.pilot_plan_id under 'plan_id'.
        "plan_id": plan.pilot_plan_id,
        # Store plan.choice_ids_under_test under 'choice_ids_under_test'.
        "choice_ids_under_test": plan.choice_ids_under_test,
        # Store plan.execution_status under 'execution_status'.
        "execution_status": plan.execution_status}
        # Evaluate design at 'plans' as part of the enclosing expression.
        for plan in design["plans"])
    # Set unresolved to a tuple containing the result of _external_input(the text
    # 'MAXIMUM_ACCEPTABLE_TRAINING_RESOURCE_BUDGET', the text...), the...
    unresolved = (
        # Include the result of _external_input(the text 'MAXIMUM_ACCEPTABLE_TRAINING_RESOURCE_BUDGET', the
        # text...) in this tuple.
        _external_input(
            "MAXIMUM_ACCEPTABLE_TRAINING_RESOURCE_BUDGET",
            "DERIVE_FIXED_MAXIMUM_TRAINING_UPDATE_HORIZON_H",
            "ONE_OF_PPO_UPDATES_MANIFEST_COLLECTIONS_SUMO_STEPS_OR_WALL_CLOCK",
            # Supply a tuple containing the text 'EXPLICIT_PROJECT_RESOURCE_ALLOCATION', the text
            # 'SUPERVISOR_APPROVED_EXPERIMENTAL_RESOURCE_CEILING' to _external_input.
            ("EXPLICIT_PROJECT_RESOURCE_ALLOCATION",
             "SUPERVISOR_APPROVED_EXPERIMENTAL_RESOURCE_CEILING"),
            # Supply a tuple containing the text 'FINALIZE_TRAINING_HORIZON', the text
            # 'ACQUIRE_ADDITIONAL_EVIDENCE' to _external_input.
            ("FINALIZE_TRAINING_HORIZON", "ACQUIRE_ADDITIONAL_EVIDENCE"),
            "REQUIRES_EXTERNAL_RESOURCE_BUDGET"),
        # Include the result of _external_input(the text
        # 'MINIMUM_PRACTICALLY_IMPORTANT_DIFFERENCE_TEAM_TRAVEL_TIME_SECONDS', the text...) in this tuple.
        _external_input(
            "MINIMUM_PRACTICALLY_IMPORTANT_DIFFERENCE_TEAM_TRAVEL_TIME_SECONDS",
            "REPLICATION_PRECISION_OR_POWER_AND_PRACTICAL_SUPERIORITY",
            "vehicle-seconds",
            # Supply a tuple containing the text 'TRANSPORTATION_DOMAIN_JUSTIFICATION', the text
            # 'RESEARCH_OBJECTIVE', the text... to _external_input.
            ("TRANSPORTATION_DOMAIN_JUSTIFICATION", "RESEARCH_OBJECTIVE",
             "SUPERVISOR_APPROVED_EXPERIMENTAL_SPECIFICATION",
             "EXPLICIT_PRACTICAL_REQUIREMENT"),
            # Supply a tuple containing the text 'CALCULATE_REPLICATION_COUNT', the text
            # 'CLASSIFY_PRACTICAL_SUPERIORITY' to _external_input.
            ("CALCULATE_REPLICATION_COUNT", "CLASSIFY_PRACTICAL_SUPERIORITY"),
            "REQUIRES_DOMAIN_OR_RESEARCH_JUSTIFICATION"),
        # Include the result of _external_input(the text 'STATISTICAL_CONFIDENCE_OR_PRECISION_TARGET', the
        # text...) in this tuple.
        _external_input(
            "STATISTICAL_CONFIDENCE_OR_PRECISION_TARGET",
            "DEFINE_REQUIRED_UNCERTAINTY_PRECISION_AND_INTERVAL_INTERPRETATION",
            "confidence-level-or-vehicle-seconds",
            # Supply a tuple containing the text 'APPROVED_RESEARCH_METHODOLOGY', the text
            # 'CITED_METHODOLOGICAL_REFERENCE' to _external_input.
            ("APPROVED_RESEARCH_METHODOLOGY", "CITED_METHODOLOGICAL_REFERENCE"),
            # Supply a tuple containing the text 'CALCULATE_REPLICATION_COUNT', the text 'INTERPRET_UNCERTAINTY'
            # to _external_input.
            ("CALCULATE_REPLICATION_COUNT", "INTERPRET_UNCERTAINTY")),
        # Include the result of _external_input(the text 'STATISTICAL_POWER_TARGET', the text...) in this tuple.
        _external_input(
            "STATISTICAL_POWER_TARGET",
            "CALCULATE_REPLICATION_COUNT_IF_POWER_BASED_DESIGN_IS_USED",
            "probability",
            # Supply a tuple containing the text 'APPROVED_RESEARCH_METHODOLOGY', the text
            # 'CITED_METHODOLOGICAL_REFERENCE' to _external_input.
            ("APPROVED_RESEARCH_METHODOLOGY", "CITED_METHODOLOGICAL_REFERENCE"),
            # Supply a tuple containing the text 'CALCULATE_POWER_BASED_REPLICATION_COUNT' to _external_input.
            ("CALCULATE_POWER_BASED_REPLICATION_COUNT",)),
        # Include the result of _external_input(the text 'UNCERTAINTY_MONTE_CARLO_RESOLUTION', the text...) in
        # this tuple.
        _external_input(
            "UNCERTAINTY_MONTE_CARLO_RESOLUTION",
            "FIX_PAIRED_BOOTSTRAP_COMPUTATIONAL_RESOLUTION",
            "bootstrap-resamples",
            # Supply a tuple containing the text 'CITED_METHOD_IMPLEMENTATION', the text
            # 'APPROVED_COMPUTATIONAL_PROTOCOL' to _external_input.
            ("CITED_METHOD_IMPLEMENTATION", "APPROVED_COMPUTATIONAL_PROTOCOL"),
            # Supply a tuple containing the text 'EXECUTE_BOOTSTRAP_UNCERTAINTY_ESTIMATION' to _external_input.
            ("EXECUTE_BOOTSTRAP_UNCERTAINTY_ESTIMATION",),
            "BOOTSTRAP_MONTE_CARLO_RESOLUTION_REQUIRES_PREDECLARATION"),
        # Include the result of _external_input(the text 'MULTIPLE_COMPARISON_CONTROL', the text...) in this
        # tuple.
        _external_input(
            "MULTIPLE_COMPARISON_CONTROL",
            "CONTROL_SIMULTANEOUS_INFERENCE_AFTER_FINAL_COMPARISON_FAMILY_IS_KNOWN",
            "method",
            # Supply a tuple containing the text 'FINAL_CANDIDATE_COMPARISON_FAMILY_DEFINITION', the text
            # 'CITED_MULTIPLE_COMPARISON_METHOD' to _external_input.
            ("FINAL_CANDIDATE_COMPARISON_FAMILY_DEFINITION",
             "CITED_MULTIPLE_COMPARISON_METHOD"),
            # Supply a tuple containing the text 'RUN_MULTI_CANDIDATE_INFERENCE' to _external_input.
            ("RUN_MULTI_CANDIDATE_INFERENCE",),
            "REQUIRES_FINAL_CANDIDATE_COMPARISON_FAMILY_DEFINITION"),
        # Include the result of _external_input(the text 'CANDIDATE_SEARCH_SEQUENCE', the text...) in this tuple.
        _external_input(
            "CANDIDATE_SEARCH_SEQUENCE",
            "ORDER_EXISTING_FROZEN_ABLATION_PLANS_WITHOUT_INVENTING_A_SEARCH_STRATEGY",
            "ordered-plan-identities",
            # Supply a tuple containing the text 'SUPERVISOR_APPROVED_EXPERIMENTAL_SPECIFICATION', the text
            # 'FROZEN_PROJECT_RESEARCH_PLAN' to _external_input.
            ("SUPERVISOR_APPROVED_EXPERIMENTAL_SPECIFICATION",
             "FROZEN_PROJECT_RESEARCH_PLAN"),
            # Supply a tuple containing the text 'BEGIN_CANDIDATE_COMPARISON' to _external_input.
            ("BEGIN_CANDIDATE_COMPARISON",)))
    # Return a dictionary containing source_review_identity, frozen_experimental_design_id, primary_metric,... to
    # the caller.
    return {
        # Store a dictionary containing checkpoint, status, source_evidence_identity, sha256 under
        # 'source_review_identity'.
        "source_review_identity": {
            # Store source_review at 'checkpoint' under 'checkpoint'.
            "checkpoint": source_review["checkpoint"],
            # Store source_review at 'status' under 'status'.
            "status": source_review["status"],
            # Store source_review at 'source_evidence_identity' under 'source_evidence_identity'.
            "source_evidence_identity": source_review["source_evidence_identity"],
            # Store the hexadecimal digest from hashlib.sha256(_canonical_json(source_review).encode()) under
            # 'sha256'.
            "sha256": hashlib.sha256(_canonical_json(source_review).encode()).hexdigest()},
        # Store design['freeze'].freeze_id under 'frozen_experimental_design_id'.
        "frozen_experimental_design_id": design["freeze"].freeze_id,
        # Store a dictionary containing metric_id, direction, secondary_quantities_are_diagnostics_only,... under
        # 'primary_metric'.
        "primary_metric": {
            "metric_id": "TOTAL_TEAM_TRAVEL_TIME_SECONDS",
            "direction": "LOWER_IS_BETTER",
            # Store True under 'secondary_quantities_are_diagnostics_only'.
            "secondary_quantities_are_diagnostics_only": True,
            # Store False under 'weighted_performance_score'.
            "weighted_performance_score": False},
        # Store a tuple containing the text 'ZERO_COLLISIONS', the text 'ZERO_BLOCKED_ZONE_VIOLATIONS', the
        # text... under 'hard_validity_gates'.
        "hard_validity_gates": (
            "ZERO_COLLISIONS", "ZERO_BLOCKED_ZONE_VIOLATIONS",
            "TRAFFIC_RULE_HARD_CONSTRAINTS_PRESERVED",
            "HARD_ACTION_MASKS_RESPECTED", "PROTOCOL_VALIDITY_PRESERVED"),
        # Store a dictionary containing architecture, maximum_update_horizon_H, resource_horizon_status,
        # states,... under 'training_budget_protocol'.
        "training_budget_protocol": {
            "architecture":
                "FIXED_RESOURCE_HORIZON_WITH_VALIDATION_CHECKPOINT_SELECTION",
            "maximum_update_horizon_H": "UNRESOLVED_EXTERNAL_INPUT",
            "resource_horizon_status": "REQUIRES_EXTERNAL_RESOURCE_BUDGET",
            "states": "STATE_0_THROUGH_STATE_H_INCLUSIVE",
            # Store False under 'adaptive_curve_inspection_stopping'.
            "adaptive_curve_inspection_stopping": False,
            "convergence_threshold": "NONE",
            # Store a dictionary containing ppo_update_cycles_per_replication,
            # training_manifest_collections_per_replication,... under 'mapping_to_H'.
            "mapping_to_H": {
                "ppo_update_cycles_per_replication": "H_EQUALS_CYCLE_LIMIT",
                "training_manifest_collections_per_replication":
                    "H_EQUALS_COLLECTION_LIMIT_MINUS_ONE",
                "sumo_steps_per_replication":
                    "FINAL_PROTOCOL_MUST_PREDECLARE_EXACT_FULL_MANIFEST_STEP_MAPPING",
                "wall_clock_allocation":
                    "FINAL_PROTOCOL_MUST_PREDECLARE_CONSERVATIVE_DETERMINISTIC_MAPPING_BEFORE_RUN"}},
        # Store a dictionary containing stream, indices, performance_seed_replacement, bad_seed_reruns,
        # target_quantity,... under 'replication_protocol'.
        "replication_protocol": {
            "stream": "CANONICAL_DETERMINISTIC_REPLICATION_STREAM",
            "indices": "0_THROUGH_N_MINUS_1_NO_SKIPPING",
            "performance_seed_replacement": "FORBIDDEN",
            "bad_seed_reruns": "FORBIDDEN",
            "target_quantity": "PAIRED_TOTAL_TEAM_TRAVEL_TIME_DIFFERENCE",
            "calculation_method": "REPLICATION_ADEQUACY_CALCULATOR",
            # Store a tuple containing the text 'MPID_TTT_SECONDS', the text 'ESTIMATED_VARIABILITY', the text...
            # under 'required_inputs'.
            "required_inputs": (
                "MPID_TTT_SECONDS", "ESTIMATED_VARIABILITY",
                "STATISTICAL_CONFIDENCE_OR_PRECISION_TARGET",
                "STATISTICAL_POWER_TARGET_IF_POWER_BASED",
                "PAIRED_DEPENDENCY_STRUCTURE"),
            "estimated_variability_source":
                "CANONICAL_PRIOR_PILOT_EVIDENCE_WITHOUT_SEED_FILTERING",
            "final_replication_count_n": "NOT_CALCULABLE_INPUTS_INCOMPLETE",
            # Store False under 'early_significance_stopping'.
            "early_significance_stopping": False,
            # Store False under 'extend_because_preferred_candidate_loses'.
            "extend_because_preferred_candidate_loses": False},
        # Store a dictionary containing eligible_states, training_performance_used_for_selection,
        # selection_data_role, metric,... under 'checkpoint_selection_protocol'.
        "checkpoint_selection_protocol": {
            "eligible_states": "STATE_0_THROUGH_STATE_H",
            # Store False under 'training_performance_used_for_selection'.
            "training_performance_used_for_selection": False,
            "selection_data_role": "VALIDATION_ONLY",
            "metric": "TOTAL_TEAM_TRAVEL_TIME_SECONDS",
            "direction": "LOWER_IS_BETTER",
            # Store True under 'uncertainty_and_practical_rule_required'.
            "uncertainty_and_practical_rule_required": True,
            "tie_rule": "EARLIEST_EQUIVALENT_CHECKPOINT_RULE",
            # Store False under 'current_state_2_retrospectively_selected'.
            "current_state_2_retrospectively_selected": False,
            # Store False under 'existing_resume_checkpoints_selection_eligible'.
            "existing_resume_checkpoints_selection_eligible": False},
        # Store a dictionary containing design, matched_conditions, paired_quantity, interpretation,
        # primary_statistic,... under 'candidate_comparison_protocol'.
        "candidate_comparison_protocol": {
            "design": "MATCHED_PAIRED_VALIDATION_COMPARISON",
            # Store a tuple containing the text 'SAME_VALIDATION_SCENARIO_IDENTITIES', the text
            # 'SAME_CANONICAL_REPLICATION_IDENTITIES', the text... under 'matched_conditions'.
            "matched_conditions": (
                "SAME_VALIDATION_SCENARIO_IDENTITIES",
                "SAME_CANONICAL_REPLICATION_IDENTITIES",
                "SAME_EVALUATION_PROTOCOL",
                "SAME_CHECKPOINT_SELECTION_RULE",
                "SAME_HARD_VALIDITY_GATES"),
            "paired_quantity": "D_i_EQUALS_C_A_i_MINUS_C_B_i",
            # Store a dictionary containing D_LESS_THAN_ZERO, D_GREATER_THAN_ZERO under 'interpretation'.
            # Store the text 'A_LOWER_BETTER' under 'D_LESS_THAN_ZERO'.
            "interpretation": {"D_LESS_THAN_ZERO": "A_LOWER_BETTER",
                               "D_GREATER_THAN_ZERO": "B_LOWER_BETTER"},
            "primary_statistic": "PAIRED_EMPIRICAL_MEAN_DIFFERENCE_TTT",
            "median_and_interquartile_mean": "ROBUST_DESCRIPTIVE_ONLY",
            # Store False under 'point_estimate_ranking_alone_sufficient'.
            "point_estimate_ranking_alone_sufficient": False,
            # Store True under 'practical_significance_requires_MPID'.
            "practical_significance_requires_MPID": True,
            "formal_test_family": "REQUIRES_PREDECLARATION_IF_LATER_REQUIRED",
            # Store plans under 'existing_frozen_ablation_plans'.
            "existing_frozen_ablation_plans": plans,
            "search_sequence": "REQUIRES_PREDECLARATION",
            # Store False under 'cartesian_product_search'.
            "cartesian_product_search": False},
        # Store a dictionary containing primary_method, independent_unit, bootstrap_time_steps,
        # bootstrap_policy_factors,... under 'uncertainty_reporting_protocol'.
        "uncertainty_reporting_protocol": {
            "primary_method": "PAIRED_BOOTSTRAP_CONFIDENCE_INTERVAL",
            "independent_unit":
                "MATCHED_REPLICATION_WITH_SCENARIO_DEPENDENCY_PRESERVED",
            # Store False under 'bootstrap_time_steps'.
            "bootstrap_time_steps": False,
            # Store False under 'bootstrap_policy_factors'.
            "bootstrap_policy_factors": False,
            "confidence_level": "REQUIRES_PREDECLARATION",
            "bootstrap_resample_count": "REQUIRES_PREDECLARATION",
            "multiple_comparison_control":
                "REQUIRES_FINAL_CANDIDATE_COMPARISON_FAMILY_DEFINITION",
            # Store True under 'estimation_preferred_over_unjustified_parametric_test'.
            "estimation_preferred_over_unjustified_parametric_test": True},
        # Store a dictionary containing candidate_pair, candidate_pair_action,
        # multi_candidate_reference_in_tied_set,... under 'tie_protocol'.
        "tie_protocol": {
            "candidate_pair": "REFERENCE_PRESERVING_TIE_RULE",
            "candidate_pair_action":
                "RETAIN_EXISTING_REFERENCE_OR_PROVISIONAL_CONFIGURATION",
            "multi_candidate_reference_in_tied_set": "RETAIN_REFERENCE",
            "multi_candidate_reference_not_in_tied_set":
                "UNRESOLVED_MULTI_CANDIDATE_TIE",
            "checkpoint": "EARLIEST_EQUIVALENT_CHECKPOINT_RULE",
            # Store False under 'sample_until_one_wins'.
            "sample_until_one_wins": False},
        # Store a dictionary containing replications, training, adaptive_extension,... under 'extension_protocol'.
        "extension_protocol": {
            "replications": "COLLECT_EXACTLY_0_THROUGH_N_MINUS_1_AFTER_N_IS_FROZEN",
            "training": "COLLECT_EXACTLY_STATE_0_THROUGH_STATE_H_AFTER_H_IS_FROZEN",
            # Store False under 'adaptive_extension'.
            "adaptive_extension": False,
            # Store True under 'new_protocol_identity_required_after_external_inputs'.
            "new_protocol_identity_required_after_external_inputs": True,
            # Store False under 'additional_evidence_before_final_protocol'.
            "additional_evidence_before_final_protocol": False},
        # Store a dictionary containing TRAINING, VALIDATION, HELD_OUT_TEST, held_out_for_checkpoint_selection,...
        # under 'data_role_protocol'.
        "data_role_protocol": {
            "TRAINING": "OPTIMIZE_POLICY_WEIGHTS_ONLY",
            "VALIDATION": "CHECKPOINT_AND_CONFIGURATION_SELECTION_ONLY",
            "HELD_OUT_TEST": "FINAL_CONFIGURATION_EVALUATION_ONLY",
            # Store False under 'held_out_for_checkpoint_selection'.
            "held_out_for_checkpoint_selection": False,
            # Store False under 'held_out_for_training_budget_selection'.
            "held_out_for_training_budget_selection": False,
            # Store False under 'held_out_for_hyperparameter_or_architecture_selection'.
            "held_out_for_hyperparameter_or_architecture_selection": False,
            # Store False under 'held_out_for_tie_resolution'.
            "held_out_for_tie_resolution": False,
            # Store False under 'adaptive_decisions_after_held_out'.
            "adaptive_decisions_after_held_out": False},
        # Store unresolved under 'unresolved_external_inputs'.
        "unresolved_external_inputs": unresolved,
        "freeze_status": "STRUCTURE_FROZEN_EXTERNAL_INPUTS_UNRESOLVED",
        # Store a dictionary containing checkpoint, current_results_used_to_optimize_selection_rules,
        # state_2_selected,... under 'provenance'.
        "provenance": {
            "checkpoint": "STEP_5J_3C_2D",
            # Store False under 'current_results_used_to_optimize_selection_rules'.
            "current_results_used_to_optimize_selection_rules": False,
            # Store False under 'state_2_selected'.
            # Store False under 'replication_count_3_selected'.
            "state_2_selected": False, "replication_count_3_selected": False,
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
            "held_out_executions": 0}}


# Build mappo selection protocol using the inputs and processing steps below.
# Input source_path: the supplied source path.
# Input output_path: the supplied output path.
# Output: a tuple containing protocol, artifact.
def build_mappo_selection_protocol(source_path=SOURCE_PATH,
                                   # Declare output_path as input parameter.
                                   output_path=OUTPUT_PATH):
    # Set source to the result of load_and_validate_source_review(source_path).
    source = load_and_validate_source_review(source_path)
    # Set design to the result of build_design().
    design = build_design()
    # Set payload to the result of _protocol_payload(source, design).
    payload = _protocol_payload(source, design)
    # Set hash_payload to a dictionary of key mapped to the result of _thaw(value) when key differs from the text
    # 'unresolved_external_inputs', otherwise a list of the result of _thaw(item.__dict__) for item in value for
    # (key, value) in key/value pairs from payload.
    hash_payload = {key: (_thaw(value) if key != "unresolved_external_inputs"
                          # Evaluate a list of the result of _thaw(item.__dict__) for item in value as part of the
                          # enclosing expression.
                          else [_thaw(item.__dict__) for item in value])
                    # Evaluate key/value pairs from payload as part of the enclosing expression.
                    for key, value in payload.items()}
    # Set digest to the hexadecimal digest from hashlib.sha256(_canonical_json(hash_payload).encode()).
    digest = hashlib.sha256(_canonical_json(hash_payload).encode()).hexdigest()
    # Set protocol to the result of MAPPOSelectionProtocol().
    protocol = MAPPOSelectionProtocol(
        # Supply protocol_id as a tuple containing the text 'MAPPO_SELECTION_PROTOCOL_V1', digest.
        # Supply the unpacked keyword arguments as payload.
        protocol_id=("MAPPO_SELECTION_PROTOCOL_V1", digest), **payload)
    # Set readiness to the result of evaluate_selection_protocol_readiness(protocol).
    readiness = evaluate_selection_protocol_readiness(protocol)
    # Set artifact to a dictionary containing checkpoint, status, protocol_readiness, protocol,
    # resolved_methodological_rules,...
    artifact = {
        "checkpoint": "STEP_5J_3C_2D",
        "status": "PREDECLARED_SELECTION_PROTOCOL_STRUCTURE_COMPLETE",
        # Store readiness under 'protocol_readiness'.
        "protocol_readiness": readiness,
        # Store a dictionary of field.name mapped to a list of the result of _thaw(item.__dict__) for item in the
        # requested attribute of protocol when field.name equals the text 'unresolved_external_inputs', otherwise
        # the result of _thaw(the requested attribute of protocol) for field in the result of fields(protocol)
        # under 'protocol'.
        "protocol": {field.name: (
            # Evaluate a list of the result of _thaw(item.__dict__) for item in the requested attribute of
            # protocol when field.name equals the text 'unresolved_external_inputs', otherwise the result of
            # _thaw(the requested attribute of protocol) as part of the enclosing expression.
            [_thaw(item.__dict__) for item in getattr(protocol, field.name)]
            # Evaluate field.name equals the text 'unresolved_external_inputs' as part of the enclosing
            # expression.
            if field.name == "unresolved_external_inputs" else
            # Evaluate the result of _thaw(the requested attribute of protocol) as part of the enclosing
            # expression.
            _thaw(getattr(protocol, field.name)))
            # Evaluate the result of fields(protocol) as part of the enclosing expression.
            for field in fields(protocol)},
        # Store a dictionary containing primary_metric, metric_direction, hard_validity_gates,... under
        # 'resolved_methodological_rules'.
        "resolved_methodological_rules": {
            # Store True under 'primary_metric'.
            # Store True under 'metric_direction'.
            "primary_metric": True, "metric_direction": True,
            # Store True under 'hard_validity_gates'.
            "hard_validity_gates": True,
            # Store True under 'fixed_resource_horizon_architecture'.
            "fixed_resource_horizon_architecture": True,
            # Store True under 'canonical_replication_stream'.
            "canonical_replication_stream": True,
            # Store True under 'paired_candidate_comparison'.
            "paired_candidate_comparison": True,
            # Store True under 'data_role_separation'.
            "data_role_separation": True,
            # Store True under 'validation_checkpoint_selection'.
            "validation_checkpoint_selection": True,
            # Store True under 'earliest_checkpoint_tie_rule'.
            "earliest_checkpoint_tie_rule": True,
            # Store True under 'reference_preserving_candidate_tie_rule'.
            "reference_preserving_candidate_tie_rule": True,
            # Store True under 'held_out_final_use'.
            "held_out_final_use": True},
        # Store False under 'training_horizon_selected'.
        "training_horizon_selected": False,
        # Store False under 'replication_count_selected'.
        "replication_count_selected": False,
        # Store False under 'checkpoint_selected'.
        "checkpoint_selected": False,
        # Store False under 'candidate_selected'.
        "candidate_selected": False,
        # Store False under 'confidence_level_silently_assumed'.
        "confidence_level_silently_assumed": False,
        # Store False under 'power_silently_assumed'.
        "power_silently_assumed": False,
        # Store False under 'mpid_silently_invented'.
        "mpid_silently_invented": False,
        # Store False under 'resource_budget_silently_invented'.
        "resource_budget_silently_invented": False,
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
        # Store protocol.unresolved_external_inputs[0].input_name under 'next_blocker'.
        "next_blocker": protocol.unresolved_external_inputs[0].input_name,
        "next_action":
            "RESOLVE_EXTERNAL_INPUTS_AND_CREATE_NEW_FINALIZED_PROTOCOL_IDENTITY"}
    # Write the supplied text to Path(output_path).
    Path(output_path).write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    # Return a tuple containing protocol, artifact to the caller.
    return protocol, artifact
