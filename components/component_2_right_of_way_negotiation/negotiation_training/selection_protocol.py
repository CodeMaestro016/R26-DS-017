"""Immutable, analysis-only Step 5J.3C.2D MAPPO selection protocol."""

from collections.abc import Mapping
from dataclasses import dataclass, fields
import hashlib
import json
from pathlib import Path
from types import MappingProxyType
from typing import Any, Tuple

from experimentation import build_design


SOURCE_PATH = Path("results/mappo_extended_evidence_review.json")
OUTPUT_PATH = Path("results/mappo_predeclared_selection_protocol.json")

PRIOR_BLOCKERS = (
    "TRAINING_BUDGET_SELECTION_CRITERION_REQUIRES_PREDECLARATION",
    "REPLICATION_COUNT_ADEQUACY_CRITERION_REQUIRES_PREDECLARATION",
    "CANDIDATE_COMPARISON_STATISTIC_REQUIRES_PREDECLARATION",
    "TIE_RULE_REQUIRES_PREDECLARATION",
    "CHECKPOINT_MODEL_SELECTION_RULE_REQUIRES_PREDECLARATION",
    "STATISTICAL_SELECTION_RULE_REQUIRES_PREDECLARATION",
)


def _freeze(value):
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze(item)
                                 for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    return value


def _thaw(value):
    if isinstance(value, Mapping):
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    return value


@dataclass(frozen=True)
class ExternalInputRequirement:
    input_name: str
    status: str
    why_required: str
    unit: str
    allowed_source_of_justification: Tuple[str, ...]
    cannot_be_derived_from_existing_results: bool
    blocks_which_next_action: Tuple[str, ...]


@dataclass(frozen=True)
class MAPPOSelectionProtocol:
    protocol_id: tuple
    source_review_identity: Mapping[str, Any]
    frozen_experimental_design_id: tuple
    primary_metric: Mapping[str, Any]
    hard_validity_gates: tuple
    training_budget_protocol: Mapping[str, Any]
    replication_protocol: Mapping[str, Any]
    checkpoint_selection_protocol: Mapping[str, Any]
    candidate_comparison_protocol: Mapping[str, Any]
    uncertainty_reporting_protocol: Mapping[str, Any]
    tie_protocol: Mapping[str, Any]
    extension_protocol: Mapping[str, Any]
    data_role_protocol: Mapping[str, Any]
    unresolved_external_inputs: Tuple[ExternalInputRequirement, ...]
    freeze_status: str
    provenance: Mapping[str, Any]

    def __post_init__(self):
        for field in fields(self):
            if field.name not in ("protocol_id", "unresolved_external_inputs"):
                object.__setattr__(self, field.name,
                                   _freeze(getattr(self, field.name)))


def _canonical_json(value):
    return json.dumps(_thaw(value), sort_keys=True,
                      separators=(",", ":"))


def _external_input(name, why, unit, sources, blocks,
                    status="REQUIRES_PREDECLARATION"):
    return ExternalInputRequirement(
        input_name=name, status=status, why_required=why, unit=unit,
        allowed_source_of_justification=tuple(sources),
        cannot_be_derived_from_existing_results=True,
        blocks_which_next_action=tuple(blocks))


def load_and_validate_source_review(path=SOURCE_PATH):
    review = json.loads(Path(path).read_text(encoding="utf-8"))
    if (review.get("checkpoint") != "STEP_5J_3C_2C" or
            review.get("status") != "EXTENDED_EVIDENCE_REVIEW_COMPLETE" or
            review.get("next_checkpoint") !=
            "STEP_5J_3C_2D_PREDECLARED_SELECTION_PROTOCOL" or
            tuple(review.get("methodological_blockers", ())) != PRIOR_BLOCKERS or
            any(value != "STILL_REQUIRES_PREDECLARATION" for value in
                review.get("methodological_blocker_assessment", {}).values())):
        raise ValueError("SELECTION_PROTOCOL_SOURCE_REVIEW_INVALID")
    return review


def evaluate_selection_protocol_readiness(protocol):
    if protocol.unresolved_external_inputs:
        return "STRUCTURE_DEFINED_EXTERNAL_INPUTS_REQUIRED"
    if protocol.freeze_status != "FROZEN":
        return "READY_TO_FREEZE_FINAL_SELECTION_PROTOCOL"
    return "FROZEN_SELECTION_PROTOCOL_READY_FOR_EVIDENCE_ACQUISITION"


def _protocol_payload(source_review, design):
    plans = tuple({
        "plan_id": plan.pilot_plan_id,
        "choice_ids_under_test": plan.choice_ids_under_test,
        "execution_status": plan.execution_status}
        for plan in design["plans"])
    unresolved = (
        _external_input(
            "MAXIMUM_ACCEPTABLE_TRAINING_RESOURCE_BUDGET",
            "DERIVE_FIXED_MAXIMUM_TRAINING_UPDATE_HORIZON_H",
            "ONE_OF_PPO_UPDATES_MANIFEST_COLLECTIONS_SUMO_STEPS_OR_WALL_CLOCK",
            ("EXPLICIT_PROJECT_RESOURCE_ALLOCATION",
             "SUPERVISOR_APPROVED_EXPERIMENTAL_RESOURCE_CEILING"),
            ("FINALIZE_TRAINING_HORIZON", "ACQUIRE_ADDITIONAL_EVIDENCE"),
            "REQUIRES_EXTERNAL_RESOURCE_BUDGET"),
        _external_input(
            "MINIMUM_PRACTICALLY_IMPORTANT_DIFFERENCE_TEAM_TRAVEL_TIME_SECONDS",
            "REPLICATION_PRECISION_OR_POWER_AND_PRACTICAL_SUPERIORITY",
            "vehicle-seconds",
            ("TRANSPORTATION_DOMAIN_JUSTIFICATION", "RESEARCH_OBJECTIVE",
             "SUPERVISOR_APPROVED_EXPERIMENTAL_SPECIFICATION",
             "EXPLICIT_PRACTICAL_REQUIREMENT"),
            ("CALCULATE_REPLICATION_COUNT", "CLASSIFY_PRACTICAL_SUPERIORITY"),
            "REQUIRES_DOMAIN_OR_RESEARCH_JUSTIFICATION"),
        _external_input(
            "STATISTICAL_CONFIDENCE_OR_PRECISION_TARGET",
            "DEFINE_REQUIRED_UNCERTAINTY_PRECISION_AND_INTERVAL_INTERPRETATION",
            "confidence-level-or-vehicle-seconds",
            ("APPROVED_RESEARCH_METHODOLOGY", "CITED_METHODOLOGICAL_REFERENCE"),
            ("CALCULATE_REPLICATION_COUNT", "INTERPRET_UNCERTAINTY")),
        _external_input(
            "STATISTICAL_POWER_TARGET",
            "CALCULATE_REPLICATION_COUNT_IF_POWER_BASED_DESIGN_IS_USED",
            "probability",
            ("APPROVED_RESEARCH_METHODOLOGY", "CITED_METHODOLOGICAL_REFERENCE"),
            ("CALCULATE_POWER_BASED_REPLICATION_COUNT",)),
        _external_input(
            "UNCERTAINTY_MONTE_CARLO_RESOLUTION",
            "FIX_PAIRED_BOOTSTRAP_COMPUTATIONAL_RESOLUTION",
            "bootstrap-resamples",
            ("CITED_METHOD_IMPLEMENTATION", "APPROVED_COMPUTATIONAL_PROTOCOL"),
            ("EXECUTE_BOOTSTRAP_UNCERTAINTY_ESTIMATION",),
            "BOOTSTRAP_MONTE_CARLO_RESOLUTION_REQUIRES_PREDECLARATION"),
        _external_input(
            "MULTIPLE_COMPARISON_CONTROL",
            "CONTROL_SIMULTANEOUS_INFERENCE_AFTER_FINAL_COMPARISON_FAMILY_IS_KNOWN",
            "method",
            ("FINAL_CANDIDATE_COMPARISON_FAMILY_DEFINITION",
             "CITED_MULTIPLE_COMPARISON_METHOD"),
            ("RUN_MULTI_CANDIDATE_INFERENCE",),
            "REQUIRES_FINAL_CANDIDATE_COMPARISON_FAMILY_DEFINITION"),
        _external_input(
            "CANDIDATE_SEARCH_SEQUENCE",
            "ORDER_EXISTING_FROZEN_ABLATION_PLANS_WITHOUT_INVENTING_A_SEARCH_STRATEGY",
            "ordered-plan-identities",
            ("SUPERVISOR_APPROVED_EXPERIMENTAL_SPECIFICATION",
             "FROZEN_PROJECT_RESEARCH_PLAN"),
            ("BEGIN_CANDIDATE_COMPARISON",)))
    return {
        "source_review_identity": {
            "checkpoint": source_review["checkpoint"],
            "status": source_review["status"],
            "source_evidence_identity": source_review["source_evidence_identity"],
            "sha256": hashlib.sha256(_canonical_json(source_review).encode()).hexdigest()},
        "frozen_experimental_design_id": design["freeze"].freeze_id,
        "primary_metric": {
            "metric_id": "TOTAL_TEAM_TRAVEL_TIME_SECONDS",
            "direction": "LOWER_IS_BETTER",
            "secondary_quantities_are_diagnostics_only": True,
            "weighted_performance_score": False},
        "hard_validity_gates": (
            "ZERO_COLLISIONS", "ZERO_BLOCKED_ZONE_VIOLATIONS",
            "TRAFFIC_RULE_HARD_CONSTRAINTS_PRESERVED",
            "HARD_ACTION_MASKS_RESPECTED", "PROTOCOL_VALIDITY_PRESERVED"),
        "training_budget_protocol": {
            "architecture":
                "FIXED_RESOURCE_HORIZON_WITH_VALIDATION_CHECKPOINT_SELECTION",
            "maximum_update_horizon_H": "UNRESOLVED_EXTERNAL_INPUT",
            "resource_horizon_status": "REQUIRES_EXTERNAL_RESOURCE_BUDGET",
            "states": "STATE_0_THROUGH_STATE_H_INCLUSIVE",
            "adaptive_curve_inspection_stopping": False,
            "convergence_threshold": "NONE",
            "mapping_to_H": {
                "ppo_update_cycles_per_replication": "H_EQUALS_CYCLE_LIMIT",
                "training_manifest_collections_per_replication":
                    "H_EQUALS_COLLECTION_LIMIT_MINUS_ONE",
                "sumo_steps_per_replication":
                    "FINAL_PROTOCOL_MUST_PREDECLARE_EXACT_FULL_MANIFEST_STEP_MAPPING",
                "wall_clock_allocation":
                    "FINAL_PROTOCOL_MUST_PREDECLARE_CONSERVATIVE_DETERMINISTIC_MAPPING_BEFORE_RUN"}},
        "replication_protocol": {
            "stream": "CANONICAL_DETERMINISTIC_REPLICATION_STREAM",
            "indices": "0_THROUGH_N_MINUS_1_NO_SKIPPING",
            "performance_seed_replacement": "FORBIDDEN",
            "bad_seed_reruns": "FORBIDDEN",
            "target_quantity": "PAIRED_TOTAL_TEAM_TRAVEL_TIME_DIFFERENCE",
            "calculation_method": "REPLICATION_ADEQUACY_CALCULATOR",
            "required_inputs": (
                "MPID_TTT_SECONDS", "ESTIMATED_VARIABILITY",
                "STATISTICAL_CONFIDENCE_OR_PRECISION_TARGET",
                "STATISTICAL_POWER_TARGET_IF_POWER_BASED",
                "PAIRED_DEPENDENCY_STRUCTURE"),
            "estimated_variability_source":
                "CANONICAL_PRIOR_PILOT_EVIDENCE_WITHOUT_SEED_FILTERING",
            "final_replication_count_n": "NOT_CALCULABLE_INPUTS_INCOMPLETE",
            "early_significance_stopping": False,
            "extend_because_preferred_candidate_loses": False},
        "checkpoint_selection_protocol": {
            "eligible_states": "STATE_0_THROUGH_STATE_H",
            "training_performance_used_for_selection": False,
            "selection_data_role": "VALIDATION_ONLY",
            "metric": "TOTAL_TEAM_TRAVEL_TIME_SECONDS",
            "direction": "LOWER_IS_BETTER",
            "uncertainty_and_practical_rule_required": True,
            "tie_rule": "EARLIEST_EQUIVALENT_CHECKPOINT_RULE",
            "current_state_2_retrospectively_selected": False,
            "existing_resume_checkpoints_selection_eligible": False},
        "candidate_comparison_protocol": {
            "design": "MATCHED_PAIRED_VALIDATION_COMPARISON",
            "matched_conditions": (
                "SAME_VALIDATION_SCENARIO_IDENTITIES",
                "SAME_CANONICAL_REPLICATION_IDENTITIES",
                "SAME_EVALUATION_PROTOCOL",
                "SAME_CHECKPOINT_SELECTION_RULE",
                "SAME_HARD_VALIDITY_GATES"),
            "paired_quantity": "D_i_EQUALS_C_A_i_MINUS_C_B_i",
            "interpretation": {"D_LESS_THAN_ZERO": "A_LOWER_BETTER",
                               "D_GREATER_THAN_ZERO": "B_LOWER_BETTER"},
            "primary_statistic": "PAIRED_EMPIRICAL_MEAN_DIFFERENCE_TTT",
            "median_and_interquartile_mean": "ROBUST_DESCRIPTIVE_ONLY",
            "point_estimate_ranking_alone_sufficient": False,
            "practical_significance_requires_MPID": True,
            "formal_test_family": "REQUIRES_PREDECLARATION_IF_LATER_REQUIRED",
            "existing_frozen_ablation_plans": plans,
            "search_sequence": "REQUIRES_PREDECLARATION",
            "cartesian_product_search": False},
        "uncertainty_reporting_protocol": {
            "primary_method": "PAIRED_BOOTSTRAP_CONFIDENCE_INTERVAL",
            "independent_unit":
                "MATCHED_REPLICATION_WITH_SCENARIO_DEPENDENCY_PRESERVED",
            "bootstrap_time_steps": False,
            "bootstrap_policy_factors": False,
            "confidence_level": "REQUIRES_PREDECLARATION",
            "bootstrap_resample_count": "REQUIRES_PREDECLARATION",
            "multiple_comparison_control":
                "REQUIRES_FINAL_CANDIDATE_COMPARISON_FAMILY_DEFINITION",
            "estimation_preferred_over_unjustified_parametric_test": True},
        "tie_protocol": {
            "candidate_pair": "REFERENCE_PRESERVING_TIE_RULE",
            "candidate_pair_action":
                "RETAIN_EXISTING_REFERENCE_OR_PROVISIONAL_CONFIGURATION",
            "multi_candidate_reference_in_tied_set": "RETAIN_REFERENCE",
            "multi_candidate_reference_not_in_tied_set":
                "UNRESOLVED_MULTI_CANDIDATE_TIE",
            "checkpoint": "EARLIEST_EQUIVALENT_CHECKPOINT_RULE",
            "sample_until_one_wins": False},
        "extension_protocol": {
            "replications": "COLLECT_EXACTLY_0_THROUGH_N_MINUS_1_AFTER_N_IS_FROZEN",
            "training": "COLLECT_EXACTLY_STATE_0_THROUGH_STATE_H_AFTER_H_IS_FROZEN",
            "adaptive_extension": False,
            "new_protocol_identity_required_after_external_inputs": True,
            "additional_evidence_before_final_protocol": False},
        "data_role_protocol": {
            "TRAINING": "OPTIMIZE_POLICY_WEIGHTS_ONLY",
            "VALIDATION": "CHECKPOINT_AND_CONFIGURATION_SELECTION_ONLY",
            "HELD_OUT_TEST": "FINAL_CONFIGURATION_EVALUATION_ONLY",
            "held_out_for_checkpoint_selection": False,
            "held_out_for_training_budget_selection": False,
            "held_out_for_hyperparameter_or_architecture_selection": False,
            "held_out_for_tie_resolution": False,
            "adaptive_decisions_after_held_out": False},
        "unresolved_external_inputs": unresolved,
        "freeze_status": "STRUCTURE_FROZEN_EXTERNAL_INPUTS_UNRESOLVED",
        "provenance": {
            "checkpoint": "STEP_5J_3C_2D",
            "current_results_used_to_optimize_selection_rules": False,
            "state_2_selected": False, "replication_count_3_selected": False,
            "new_sumo_executions": 0, "training_episodes": 0,
            "optimizer_invocations": 0, "backward_calls": 0,
            "parameter_updates": 0, "validation_executions": 0,
            "held_out_executions": 0}}


def build_mappo_selection_protocol(source_path=SOURCE_PATH,
                                   output_path=OUTPUT_PATH):
    source = load_and_validate_source_review(source_path)
    design = build_design()
    payload = _protocol_payload(source, design)
    hash_payload = {key: (_thaw(value) if key != "unresolved_external_inputs"
                          else [_thaw(item.__dict__) for item in value])
                    for key, value in payload.items()}
    digest = hashlib.sha256(_canonical_json(hash_payload).encode()).hexdigest()
    protocol = MAPPOSelectionProtocol(
        protocol_id=("MAPPO_SELECTION_PROTOCOL_V1", digest), **payload)
    readiness = evaluate_selection_protocol_readiness(protocol)
    artifact = {
        "checkpoint": "STEP_5J_3C_2D",
        "status": "PREDECLARED_SELECTION_PROTOCOL_STRUCTURE_COMPLETE",
        "protocol_readiness": readiness,
        "protocol": {field.name: (
            [_thaw(item.__dict__) for item in getattr(protocol, field.name)]
            if field.name == "unresolved_external_inputs" else
            _thaw(getattr(protocol, field.name)))
            for field in fields(protocol)},
        "resolved_methodological_rules": {
            "primary_metric": True, "metric_direction": True,
            "hard_validity_gates": True,
            "fixed_resource_horizon_architecture": True,
            "canonical_replication_stream": True,
            "paired_candidate_comparison": True,
            "data_role_separation": True,
            "validation_checkpoint_selection": True,
            "earliest_checkpoint_tie_rule": True,
            "reference_preserving_candidate_tie_rule": True,
            "held_out_final_use": True},
        "training_horizon_selected": False,
        "replication_count_selected": False,
        "checkpoint_selected": False,
        "candidate_selected": False,
        "confidence_level_silently_assumed": False,
        "power_silently_assumed": False,
        "mpid_silently_invented": False,
        "resource_budget_silently_invented": False,
        "new_sumo_executions": 0, "training_episodes": 0,
        "optimizer_invocations": 0, "backward_calls": 0,
        "parameter_updates": 0, "validation_executions": 0,
        "held_out_executions": 0,
        "next_blocker": protocol.unresolved_external_inputs[0].input_name,
        "next_action":
            "RESOLVE_EXTERNAL_INPUTS_AND_CREATE_NEW_FINALIZED_PROTOCOL_IDENTITY"}
    Path(output_path).write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    return protocol, artifact
