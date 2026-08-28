"""Analysis-only Step 5J.3C.2C extended-evidence sufficiency review."""

import hashlib
import json
import math
from pathlib import Path
from statistics import mean, median, stdev, variance

import torch


SOURCE_PATH = Path("results/mappo_extended_learning_curve_evidence.json")
PRIOR_REVIEW_PATH = Path("results/mappo_pilot_evidence_review.json")
OUTPUT_PATH = Path("results/mappo_extended_evidence_review.json")


BLOCKERS = (
    "TRAINING_BUDGET_SELECTION_CRITERION_REQUIRES_PREDECLARATION",
    "REPLICATION_COUNT_ADEQUACY_CRITERION_REQUIRES_PREDECLARATION",
    "CANDIDATE_COMPARISON_STATISTIC_REQUIRES_PREDECLARATION",
    "TIE_RULE_REQUIRES_PREDECLARATION",
    "CHECKPOINT_MODEL_SELECTION_RULE_REQUIRES_PREDECLARATION",
    "STATISTICAL_SELECTION_RULE_REQUIRES_PREDECLARATION",
)


def _digest(payload):
    return hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _statistics(values):
    values = tuple(float(value) for value in values)
    return {
        "values": values, "sample_mean": mean(values),
        "sample_variance_n_minus_1": variance(values),
        "sample_standard_deviation": stdev(values),
        "minimum": min(values), "maximum": max(values),
        "median": median(values)}


def _same_statistics(actual, expected):
    return all(
        tuple(actual[key]) == tuple(expected[key]) if key == "values" else
        math.isclose(actual[key], expected[key], rel_tol=0.0, abs_tol=1e-9)
        for key in actual)


def load_and_validate_extended_evidence(path=SOURCE_PATH):
    evidence = json.loads(Path(path).read_text(encoding="utf-8"))
    required = {
        "checkpoint": "STEP_5J_3C_2B",
        "status": "EXTENDED_MULTI_UPDATE_EVIDENCE_ACQUIRED",
        "replications_observed": 3,
        "update_intervals_observed_per_replication": 2,
        "policy_states_per_replication": 3,
        "training_manifest_collections": 9,
        "training_scenario_executions": 324,
        "replications_discarded": 0,
        "outliers_declared": 0,
        "final_replication_count_selected": False,
        "final_training_budget_selected": False,
    }
    for field, expected in required.items():
        if evidence.get(field) != expected:
            raise ValueError("EXTENDED_EVIDENCE_IDENTITY_INVALID")
    boundary = evidence.get("data_boundary_evidence", {})
    safety = evidence.get("safety_evidence", {})
    if (boundary.get("validation_scenario_executions") != 0 or
            boundary.get("held_out_scenario_executions") != 0 or
            boundary.get("candidate_comparisons") != 0 or
            safety.get("collisions") != 0 or
            safety.get("blocked_zone_violations") != 0):
        raise ValueError("EXTENDED_EVIDENCE_IDENTITY_INVALID")
    replications = evidence.get("replications", ())
    if (len(replications) != 3 or
            [item.get("replication_index") for item in replications] !=
            [0, 1, 2] or
            any(len(item.get("policy_states", ())) != 3 or
                len(item.get("updates", ())) != 2
                for item in replications)):
        raise ValueError("EXTENDED_EVIDENCE_IDENTITY_INVALID")
    return evidence


def recompute_learning_curve(evidence):
    c = {f"C{index}": [
        replication["policy_states"][index]["team_travel_time_seconds"]
        for replication in evidence["replications"]]
        for index in range(3)}
    deltas = {
        "delta_0_to_1": [b - a for a, b in zip(c["C0"], c["C1"])],
        "delta_1_to_2": [b - a for a, b in zip(c["C1"], c["C2"])],
        "delta_0_to_2": [b - a for a, b in zip(c["C0"], c["C2"])]}
    sources = {**c, **deltas}
    statistics = {name: _statistics(values)
                  for name, values in sources.items()}
    stored = evidence["cross_replication_descriptive_statistics"]
    if any(not _same_statistics(statistics[name], stored[name])
           for name in sources):
        raise ValueError("EXTENDED_EVIDENCE_STATISTIC_MISMATCH")
    for index, replication in enumerate(evidence["replications"]):
        for name in deltas:
            if not math.isclose(
                    replication["learning_curve_deltas"][name],
                    deltas[name][index], rel_tol=0.0, abs_tol=1e-9):
                raise ValueError("EXTENDED_EVIDENCE_DELTA_MISMATCH")
    return c, deltas, statistics


def audit_resume_checkpoint_selection_flags(evidence):
    audits = []
    for replication in evidence["replications"]:
        for checkpoint_path in replication["resume_checkpoints"]:
            # Metadata-only audit: state is never loaded into a model or used
            # to continue training.
            payload = torch.load(
                checkpoint_path, map_location="cpu", weights_only=False)
            valid = (
                payload.get("checkpoint_type") ==
                    "EVIDENCE_RESUME_CHECKPOINT_ONLY" and
                payload.get("best_model") is False and
                payload.get("final_model") is False and
                payload.get("selected_model") is False and
                payload.get("selection_eligible") is False and
                payload.get("purpose") ==
                    "LONG_RUNNING_EXPERIMENT_RESUME_ONLY")
            if not valid:
                raise ValueError("RESUME_CHECKPOINT_SELECTION_METADATA_INVALID")
            audits.append({
                "checkpoint_path": checkpoint_path,
                "checkpoint_identity": payload["checkpoint_identity"],
                "best_model": False, "final_model": False,
                "selected_model": False, "selection_eligible": False,
                "purpose": "LONG_RUNNING_EXPERIMENT_RESUME_ONLY"})
    if len(audits) != 9:
        raise ValueError("RESUME_CHECKPOINT_COUNT_INVALID")
    return audits


def build_extended_evidence_review(source_path=SOURCE_PATH,
                                   output_path=OUTPUT_PATH):
    evidence = load_and_validate_extended_evidence(source_path)
    prior = json.loads(PRIOR_REVIEW_PATH.read_text(encoding="utf-8"))
    prior_blockers = set(prior.get("remaining_methodological_blockers", ()))
    if not set(BLOCKERS).issubset(prior_blockers):
        raise ValueError("PRIOR_METHODOLOGICAL_BLOCKER_IDENTITY_INVALID")
    c, deltas, statistics = recompute_learning_curve(evidence)
    checkpoint_audits = audit_resume_checkpoint_selection_flags(evidence)
    latest_directions = ["IMPROVEMENT" if value < 0 else
                         "WORSENING" if value > 0 else "NO_CHANGE"
                         for value in deltas["delta_1_to_2"]]
    all_end_to_end_improve = all(value < 0 for value in
                                 deltas["delta_0_to_2"])
    mean_decreases = (statistics["C0"]["sample_mean"] >
                      statistics["C1"]["sample_mean"] >
                      statistics["C2"]["sample_mean"])
    blocker_status = {blocker: "STILL_REQUIRES_PREDECLARATION"
                      for blocker in BLOCKERS}
    result = {
        "checkpoint": "STEP_5J_3C_2C",
        "source_evidence_identity": {
            "evidence_tranche_identity": evidence["evidence_tranche_identity"],
            "sha256": _digest(evidence),
            "checkpoint": evidence["checkpoint"],
            "status": evidence["status"]},
        "status": "EXTENDED_EVIDENCE_REVIEW_COMPLETE",
        "observed_structure": {
            "replications": 3, "policy_states_per_replication": 3,
            "update_intervals_per_replication": 2,
            "training_manifest_collections": 9,
            "training_scenario_executions": 324,
            "total_sumo_steps":
                evidence["compute_cost_evidence"]["total_sumo_steps"]},
        "learning_curve_evidence": {
            "C0": c["C0"], "C1": c["C1"], "C2": c["C2"],
            "delta_0_to_1": deltas["delta_0_to_1"],
            "delta_1_to_2": deltas["delta_1_to_2"],
            "delta_0_to_2": deltas["delta_0_to_2"],
            "descriptive_statistics": statistics,
            "latest_update_directions": latest_directions,
            "latest_update_direction_consistent":
                len(set(latest_directions)) == 1,
            "mean_C0_greater_than_C1_greater_than_C2": mean_decreases,
            "all_replications_C2_lower_than_C0": all_end_to_end_improve,
            "mean_decrease_is_empirical_observation": True,
            "mean_decrease_is_selection_rule": False,
            "mean_decrease_proves_convergence": False},
        "training_budget_assessment": {
            "status":
                "INSUFFICIENT_NO_PREDECLARED_STABILITY_CRITERION_AND_CURVE_STILL_EVOLVING",
            "states_observed": 3, "update_intervals_observed": 2,
            "plateau_established": False,
            "convergence_established": False,
            "later_degradation_characterized": False,
            "consistent_latest_update_direction": False,
            "final_training_budget_justified": False,
            "final_training_budget_selected": False,
            "final_update_count": "NOT_SELECTED"},
        "replication_assessment": {
            "status":
                "INSUFFICIENT_NO_PREDECLARED_REPLICATION_ADEQUACY_CRITERION",
            "independent_replications": 3,
            "all_retained": True,
            "replications_discarded": 0,
            "outliers_declared": 0,
            "performance_selected_replications": 0,
            "learning_trajectories_identical": False,
            "seed_variability_observed": True,
            "adequacy_criterion_predeclared": False,
            "final_replication_count_justified": False,
            "final_replication_count_selected": False,
            "final_replication_count": "NOT_SELECTED"},
        "checkpoint_selection_assessment": {
            "status": "REQUIRES_PREDECLARED_SELECTION_RULE",
            "state_2_selected_because_mean_is_lowest": False,
            "model_selected": False,
            "final_checkpoint_selected": False,
            "checkpoint_audits": checkpoint_audits},
        "statistical_rule_assessment": {
            "status": "REQUIRES_PREDECLARATION",
            "new_convergence_thresholds": 0,
            "new_replication_adequacy_thresholds": 0,
            "post_hoc_stopping_rule_created": False},
        "candidate_comparison_readiness": {
            "status": "NOT_READY_SELECTION_PROTOCOL_INCOMPLETE",
            "ready": False,
            "candidate_comparisons_started": 0},
        "scenario_assessment": {
            "new_unique_training_scenario_identities_required_now": False,
            "repeated_on_policy_frozen_training_manifest_exposure": True,
            "scenario_manifests_modified": False},
        "future_data_roles": {
            "validation": "CONFIGURATION_AND_CHECKPOINT_COMPARISON_ONLY_AFTER_SELECTION_METHODOLOGY_IS_FROZEN",
            "held_out": "FINAL_UNBIASED_EVALUATION_AFTER_ALL_CHOICES_ARE_FROZEN"},
        "safety_evidence": evidence["safety_evidence"],
        "compute_evidence": evidence["compute_cost_evidence"],
        "methodological_blocker_assessment": blocker_status,
        "methodological_blockers": list(BLOCKERS),
        "new_hyperparameters": 0,
        "new_training_executions": 0,
        "new_sumo_executions": 0,
        "validation_executions": 0,
        "held_out_executions": 0,
        "optimizer_instances": 0,
        "optimizer_invocations": 0,
        "backward_calls": 0,
        "parameter_updates": 0,
        "update_3_performed": False,
        "replication_3_created": False,
        "training_budget_status":
            "INSUFFICIENT_NO_PREDECLARED_STABILITY_CRITERION_AND_CURVE_STILL_EVOLVING",
        "replication_status":
            "INSUFFICIENT_NO_PREDECLARED_REPLICATION_ADEQUACY_CRITERION",
        "checkpoint_selection_status":
            "REQUIRES_PREDECLARED_SELECTION_RULE",
        "next_checkpoint":
            "STEP_5J_3C_2D_PREDECLARED_SELECTION_PROTOCOL",
        "next_checkpoint_reason":
            "PREDECLARE_AND_FREEZE_SELECTION_AND_TERMINATION_RULES_BEFORE_ACQUIRING_MORE_EVIDENCE"}
    Path(output_path).write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result
