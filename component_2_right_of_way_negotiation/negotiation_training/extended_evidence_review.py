"""Analysis-only Step 5J.3C.2C extended-evidence sufficiency review."""

# Import hashlib for use in this module.
import hashlib
# Import json for use in this module.
import json
# Import math for use in this module.
import math
# Import Path from pathlib for the operations below.
from pathlib import Path
# Import mean, median, stdev, variance from statistics for the operations below.
from statistics import mean, median, stdev, variance

# Import torch for use in this module.
import torch


# Set SOURCE_PATH to the result of Path(the text 'results/mappo_extended_learning_curve_evidence.json').
SOURCE_PATH = Path("results/mappo_extended_learning_curve_evidence.json")
# Set PRIOR_REVIEW_PATH to the result of Path(the text 'results/mappo_pilot_evidence_review.json').
PRIOR_REVIEW_PATH = Path("results/mappo_pilot_evidence_review.json")
# Set OUTPUT_PATH to the result of Path(the text 'results/mappo_extended_evidence_review.json').
OUTPUT_PATH = Path("results/mappo_extended_evidence_review.json")


# Set BLOCKERS to a tuple containing the text 'TRAINING_BUDGET_SELECTION_CRITERION_REQUIRES_PREDECLARATION', the
# text...
BLOCKERS = (
    "TRAINING_BUDGET_SELECTION_CRITERION_REQUIRES_PREDECLARATION",
    "REPLICATION_COUNT_ADEQUACY_CRITERION_REQUIRES_PREDECLARATION",
    "CANDIDATE_COMPARISON_STATISTIC_REQUIRES_PREDECLARATION",
    "TIE_RULE_REQUIRES_PREDECLARATION",
    "CHECKPOINT_MODEL_SELECTION_RULE_REQUIRES_PREDECLARATION",
    "STATISTICAL_SELECTION_RULE_REQUIRES_PREDECLARATION",
)


# Digest using the inputs and processing steps below.
# Input payload: the supplied payload.
# Output: the hexadecimal digest from hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',',
# ':')).encode()).
def _digest(payload):
    # Return the hexadecimal digest from hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',',
    # ':')).encode()) to the caller.
    return hashlib.sha256(json.dumps(
        # Supply sort_keys as True.
        # Supply separators as a tuple containing the text ',', the text ':'.
        payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


# Statistics using the inputs and processing steps below.
# Input values: the supplied values.
# Output: a dictionary containing values, sample_mean, sample_variance_n_minus_1, sample_standard_deviation,
# minimum,...
def _statistics(values):
    # Set values to a tuple built from a lazy sequence of a floating-point number built from value for value in
    # values.
    values = tuple(float(value) for value in values)
    # Return a dictionary containing values, sample_mean, sample_variance_n_minus_1, sample_standard_deviation,
    # minimum,... to the caller.
    return {
        # Store values under 'values'.
        # Store the result of mean(values) under 'sample_mean'.
        "values": values, "sample_mean": mean(values),
        # Store the result of variance(values) under 'sample_variance_n_minus_1'.
        "sample_variance_n_minus_1": variance(values),
        # Store the result of stdev(values) under 'sample_standard_deviation'.
        "sample_standard_deviation": stdev(values),
        # Store the minimum of values under 'minimum'.
        # Store the maximum of values under 'maximum'.
        "minimum": min(values), "maximum": max(values),
        # Store the result of median(values) under 'median'.
        "median": median(values)}


# Same statistics using the inputs and processing steps below.
# Input actual: the supplied actual.
# Input expected: the supplied expected.
# Output: whether every item is true in a lazy sequence of tuple(actual[key]) equals tuple(expected[key]) when key
# equals 'values', otherwise the result of math.isclose(actual[key], expected[key])...
def _same_statistics(actual, expected):
    # Return whether every item is true in a lazy sequence of tuple(actual[key]) equals tuple(expected[key]) when
    # key equals 'values', otherwise the result of math.isclose(actual[key], expected[key]) for key in actual to
    # the caller.
    return all(
        # Evaluate a tuple built from actual at key equals a tuple built from expected at key when key equals the
        # text 'values', otherwise the result of math.isclose(actual at key, expected at key) as part of the
        # enclosing expression.
        tuple(actual[key]) == tuple(expected[key]) if key == "values" else
        # Supply rel_tol as 0.0.
        # Supply abs_tol as 1e-09.
        math.isclose(actual[key], expected[key], rel_tol=0.0, abs_tol=1e-9)
        # Evaluate actual as part of the enclosing expression.
        for key in actual)


# Load and validate extended evidence using the inputs and processing steps below.
# Input path: the path or path object supplied by the caller.
# Output: evidence.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def load_and_validate_extended_evidence(path=SOURCE_PATH):
    # Set evidence to the decoded data produced by json.loads from the text read from Path(path).
    evidence = json.loads(Path(path).read_text(encoding="utf-8"))
    # Set required to a dictionary containing checkpoint, status, replications_observed,
    # update_intervals_observed_per_replication,...
    required = {
        "checkpoint": "STEP_5J_3C_2B",
        "status": "EXTENDED_MULTI_UPDATE_EVIDENCE_ACQUIRED",
        # Store 3 under 'replications_observed'.
        "replications_observed": 3,
        # Store 2 under 'update_intervals_observed_per_replication'.
        "update_intervals_observed_per_replication": 2,
        # Store 3 under 'policy_states_per_replication'.
        "policy_states_per_replication": 3,
        # Store 9 under 'training_manifest_collections'.
        "training_manifest_collections": 9,
        # Store 324 under 'training_scenario_executions'.
        "training_scenario_executions": 324,
        # Store 0 under 'replications_discarded'.
        "replications_discarded": 0,
        # Store 0 under 'outliers_declared'.
        "outliers_declared": 0,
        # Store False under 'final_replication_count_selected'.
        "final_replication_count_selected": False,
        # Store False under 'final_training_budget_selected'.
        "final_training_budget_selected": False,
    }
    # Iterate over key/value pairs from required, binding each item to (field, expected).
    for field, expected in required.items():
        # Run this branch when field from evidence; use None if absent differs from expected.
        if evidence.get(field) != expected:
            # Raise ValueError with the text 'EXTENDED_EVIDENCE_IDENTITY_INVALID' to stop this execution path.
            raise ValueError("EXTENDED_EVIDENCE_IDENTITY_INVALID")
    # Set boundary to 'data_boundary_evidence' from evidence; use an empty dictionary if absent.
    boundary = evidence.get("data_boundary_evidence", {})
    # Set safety to 'safety_evidence' from evidence; use an empty dictionary if absent.
    safety = evidence.get("safety_evidence", {})
    # Run this branch when 'validation_scenario_executions' from boundary; use None if absent differs from 0 or
    # 'held_out_scenario_executions' from boundary; use None if absent differs from 0 or 'candidate_comparisons'
    # from boundary; use None if absent differs from 0 or 'collisions' from safety; use None if absent differs
    # from 0 or 'blocked_zone_violations' from safety; use None if absent differs from 0.
    if (boundary.get("validation_scenario_executions") != 0 or
            # Evaluate 'held_out_scenario_executions' from boundary; use None if absent differs from 0 as part of
            # the enclosing expression.
            boundary.get("held_out_scenario_executions") != 0 or
            # Evaluate 'candidate_comparisons' from boundary; use None if absent differs from 0 as part of the
            # enclosing expression.
            boundary.get("candidate_comparisons") != 0 or
            # Evaluate 'collisions' from safety; use None if absent differs from 0 as part of the enclosing
            # expression.
            safety.get("collisions") != 0 or
            # Evaluate 'blocked_zone_violations' from safety; use None if absent differs from 0 as part of the
            # enclosing expression.
            safety.get("blocked_zone_violations") != 0):
        # Raise ValueError with the text 'EXTENDED_EVIDENCE_IDENTITY_INVALID' to stop this execution path.
        raise ValueError("EXTENDED_EVIDENCE_IDENTITY_INVALID")
    # Set replications to 'replications' from evidence; use an empty tuple if absent.
    replications = evidence.get("replications", ())
    # Run this branch when the number of entries in replications differs from 3 or a list of 'replication_index'
    # from item; use None if absent for item in replications differs from a list containing 0, 1, 2 or whether any
    # item is true in a lazy sequence of len(item.get('policy_states', ())) != 3 or len(item.get('updates', ()))
    # != 2 for item in replications.
    if (len(replications) != 3 or
            # Evaluate a list of 'replication_index' from item; use None if absent for item in replications
            # differs from a list containing 0, 1, 2 as part of the enclosing expression.
            [item.get("replication_index") for item in replications] !=
            # Evaluate a list containing 0, 1, 2 as part of the enclosing expression.
            [0, 1, 2] or
            # Evaluate whether any item is true in a lazy sequence of len(item.get('policy_states', ())) differs
            # from 3 or len(item.get('updates', ())) differs from 2 for item in replications as part of the
            # enclosing expression.
            any(len(item.get("policy_states", ())) != 3 or
                # Evaluate the number of entries in 'updates' from item; use an empty tuple if absent differs from
                # 2 as part of the enclosing expression.
                len(item.get("updates", ())) != 2
                # Evaluate replications as part of the enclosing expression.
                for item in replications)):
        # Raise ValueError with the text 'EXTENDED_EVIDENCE_IDENTITY_INVALID' to stop this execution path.
        raise ValueError("EXTENDED_EVIDENCE_IDENTITY_INVALID")
    # Return evidence to the caller.
    return evidence


# Recompute learning curve using the inputs and processing steps below.
# Input evidence: the supplied evidence.
# Output: a tuple containing c, deltas, statistics.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def recompute_learning_curve(evidence):
    # Set c to a dictionary of formatted text built from the embedded values mapped to a list of
    # replication['policy_states'][index] at 'team_travel_time_seconds' for replication in evidence at
    # 'replications' for index in the integer range defined by 3.
    c = {f"C{index}": [
        # Evaluate replication['policy_states'][index] at 'team_travel_time_seconds' as part of the enclosing
        # expression.
        replication["policy_states"][index]["team_travel_time_seconds"]
        # Evaluate evidence at 'replications' as part of the enclosing expression.
        for replication in evidence["replications"]]
        # Evaluate the integer range defined by 3 as part of the enclosing expression.
        for index in range(3)}
    # Set deltas to a dictionary containing delta_0_to_1, delta_1_to_2, delta_0_to_2.
    deltas = {
        # Store a list of b minus a for (a, b) in corresponding items paired from c at 'C0', c at 'C1' under
        # 'delta_0_to_1'.
        "delta_0_to_1": [b - a for a, b in zip(c["C0"], c["C1"])],
        # Store a list of b minus a for (a, b) in corresponding items paired from c at 'C1', c at 'C2' under
        # 'delta_1_to_2'.
        "delta_1_to_2": [b - a for a, b in zip(c["C1"], c["C2"])],
        # Store a list of b minus a for (a, b) in corresponding items paired from c at 'C0', c at 'C2' under
        # 'delta_0_to_2'.
        "delta_0_to_2": [b - a for a, b in zip(c["C0"], c["C2"])]}
    # Set sources to a dictionary of the supplied entries.
    sources = {**c, **deltas}
    # Set statistics to a dictionary of name mapped to the result of _statistics(values) for (name, values) in
    # key/value pairs from sources.
    statistics = {name: _statistics(values)
                  # Evaluate key/value pairs from sources as part of the enclosing expression.
                  for name, values in sources.items()}
    # Set stored to evidence at 'cross_replication_descriptive_statistics'.
    stored = evidence["cross_replication_descriptive_statistics"]
    # Run this branch when whether any item is true in a lazy sequence of the negation of the result of
    # _same_statistics(statistics[name], stored[name]) for name in sources.
    if any(not _same_statistics(statistics[name], stored[name])
           # Evaluate sources as part of the enclosing expression.
           for name in sources):
        # Raise ValueError with the text 'EXTENDED_EVIDENCE_STATISTIC_MISMATCH' to stop this execution path.
        raise ValueError("EXTENDED_EVIDENCE_STATISTIC_MISMATCH")
    # Iterate over index/value pairs from evidence at 'replications', binding each item to (index, replication).
    for index, replication in enumerate(evidence["replications"]):
        # Iterate over deltas, binding each item to name.
        for name in deltas:
            # Run this branch when the negation of the result of math.isclose(replication['learning_curve_deltas']
            # at name, deltas[name] at index).
            if not math.isclose(
                    # Supply replication['learning_curve_deltas'] at name to math.isclose.
                    replication["learning_curve_deltas"][name],
                    # Supply rel_tol as 0.0.
                    # Supply abs_tol as 1e-09.
                    deltas[name][index], rel_tol=0.0, abs_tol=1e-9):
                # Raise ValueError with the text 'EXTENDED_EVIDENCE_DELTA_MISMATCH' to stop this execution path.
                raise ValueError("EXTENDED_EVIDENCE_DELTA_MISMATCH")
    # Return a tuple containing c, deltas, statistics to the caller.
    return c, deltas, statistics


# Audit resume checkpoint selection flags using the inputs and processing steps below.
# Input evidence: the supplied evidence.
# Output: audits.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def audit_resume_checkpoint_selection_flags(evidence):
    # Set audits to an empty list.
    audits = []
    # Iterate over evidence at 'replications', binding each item to replication.
    for replication in evidence["replications"]:
        # Iterate over replication at 'resume_checkpoints', binding each item to checkpoint_path.
        for checkpoint_path in replication["resume_checkpoints"]:
            # Metadata-only audit: state is never loaded into a model or used
            # to continue training.
            # Set payload to the decoded data produced by torch.load from checkpoint_path.
            payload = torch.load(
                # Supply map_location as the text 'cpu'.
                # Supply weights_only as False.
                checkpoint_path, map_location="cpu", weights_only=False)
            # Set valid to 'checkpoint_type' from payload; use None if absent equals the text
            # 'EVIDENCE_RESUME_CHECKPOINT_ONLY' and 'best_model' from payload; use None if absent is the same
            # object as False and 'final_model' from payload; use None if absent is the same object as False and
            # 'selected_model' from payload; use None if absent is the same object as False and
            # 'selection_eligible' from payload; use None if absent is the same object as False and 'purpose' from
            # payload; use None if absent equals the text 'LONG_RUNNING_EXPERIMENT_RESUME_ONLY'.
            valid = (
                # Evaluate 'checkpoint_type' from payload; use None if absent equals the text
                # 'EVIDENCE_RESUME_CHECKPOINT_ONLY' and 'best_model' from payload; use None if absent is the same
                # object as False and 'final_model' from payload; use None if absent is the same object as False
                # and 'selected_model' from payload; use None if absent is the same object as False and
                # 'selection_eligible' from payload; use None if absent is the same object as False and 'purpose'
                # from payload; use None if absent equals the text 'LONG_RUNNING_EXPERIMENT_RESUME_ONLY' as part
                # of the enclosing expression.
                payload.get("checkpoint_type") ==
                    # Supply the text 'EVIDENCE_RESUME_CHECKPOINT_ONLY' to the enclosing expression.
                    "EVIDENCE_RESUME_CHECKPOINT_ONLY" and
                # Evaluate 'best_model' from payload; use None if absent is the same object as False as part of
                # the enclosing expression.
                payload.get("best_model") is False and
                # Evaluate 'final_model' from payload; use None if absent is the same object as False as part of
                # the enclosing expression.
                payload.get("final_model") is False and
                # Evaluate 'selected_model' from payload; use None if absent is the same object as False as part
                # of the enclosing expression.
                payload.get("selected_model") is False and
                # Evaluate 'selection_eligible' from payload; use None if absent is the same object as False as
                # part of the enclosing expression.
                payload.get("selection_eligible") is False and
                # Evaluate 'purpose' from payload; use None if absent equals the text
                # 'LONG_RUNNING_EXPERIMENT_RESUME_ONLY' as part of the enclosing expression.
                payload.get("purpose") ==
                    "LONG_RUNNING_EXPERIMENT_RESUME_ONLY")
            # Run this branch when the negation of valid.
            if not valid:
                # Raise ValueError with the text 'RESUME_CHECKPOINT_SELECTION_METADATA_INVALID' to stop this
                # execution path.
                raise ValueError("RESUME_CHECKPOINT_SELECTION_METADATA_INVALID")
            # Append a dictionary containing checkpoint_path, checkpoint_identity, best_model, final_model,
            # selected_model,... to audits.
            audits.append({
                # Store checkpoint_path under 'checkpoint_path'.
                "checkpoint_path": checkpoint_path,
                # Store payload at 'checkpoint_identity' under 'checkpoint_identity'.
                "checkpoint_identity": payload["checkpoint_identity"],
                # Store False under 'best_model'.
                # Store False under 'final_model'.
                "best_model": False, "final_model": False,
                # Store False under 'selected_model'.
                # Store False under 'selection_eligible'.
                "selected_model": False, "selection_eligible": False,
                "purpose": "LONG_RUNNING_EXPERIMENT_RESUME_ONLY"})
    # Run this branch when the number of entries in audits differs from 9.
    if len(audits) != 9:
        # Raise ValueError with the text 'RESUME_CHECKPOINT_COUNT_INVALID' to stop this execution path.
        raise ValueError("RESUME_CHECKPOINT_COUNT_INVALID")
    # Return audits to the caller.
    return audits


# Build extended evidence review using the inputs and processing steps below.
# Input source_path: the supplied source path.
# Input output_path: the supplied output path.
# Output: result.
# Processing: select branches using the stated conditions.
def build_extended_evidence_review(source_path=SOURCE_PATH,
                                   # Declare output_path as input parameter.
                                   output_path=OUTPUT_PATH):
    # Set evidence to the result of load_and_validate_extended_evidence(source_path).
    evidence = load_and_validate_extended_evidence(source_path)
    # Set prior to the decoded data produced by json.loads from the text read from PRIOR_REVIEW_PATH.
    prior = json.loads(PRIOR_REVIEW_PATH.read_text(encoding="utf-8"))
    # Set prior_blockers to a set built from 'remaining_methodological_blockers' from prior; use an empty tuple if
    # absent.
    prior_blockers = set(prior.get("remaining_methodological_blockers", ()))
    # Run this branch when the negation of the result of set(BLOCKERS).issubset(prior_blockers).
    if not set(BLOCKERS).issubset(prior_blockers):
        # Raise ValueError with the text 'PRIOR_METHODOLOGICAL_BLOCKER_IDENTITY_INVALID' to stop this execution
        # path.
        raise ValueError("PRIOR_METHODOLOGICAL_BLOCKER_IDENTITY_INVALID")
    # Set (c, deltas, statistics) to the result of recompute_learning_curve(evidence).
    c, deltas, statistics = recompute_learning_curve(evidence)
    # Set checkpoint_audits to the result of audit_resume_checkpoint_selection_flags(evidence).
    checkpoint_audits = audit_resume_checkpoint_selection_flags(evidence)
    # Set latest_directions to a list of the text 'IMPROVEMENT' when value is less than 0, otherwise the text
    # 'WORSENING' when value is greater than 0, otherwise the text 'NO_CHANGE' for value in deltas at
    # 'delta_1_to_2'.
    latest_directions = ["IMPROVEMENT" if value < 0 else
                         # Evaluate the text 'WORSENING' when value is greater than 0, otherwise the text
                         # 'NO_CHANGE' as part of the enclosing expression.
                         "WORSENING" if value > 0 else "NO_CHANGE"
                         # Evaluate deltas at 'delta_1_to_2' as part of the enclosing expression.
                         for value in deltas["delta_1_to_2"]]
    # Set all_end_to_end_improve to whether every item is true in a lazy sequence of value is less than 0 for
    # value in deltas at 'delta_0_to_2'.
    all_end_to_end_improve = all(value < 0 for value in
                                 # Evaluate deltas at 'delta_0_to_2' as part of the enclosing expression.
                                 deltas["delta_0_to_2"])
    # Set mean_decreases to statistics['C0'] at 'sample_mean' is greater than statistics['C1'] at 'sample_mean';
    # is greater than statistics['C2'] at 'sample_mean'.
    mean_decreases = (statistics["C0"]["sample_mean"] >
                      # Evaluate statistics['C1'] at 'sample_mean' as part of the enclosing expression.
                      statistics["C1"]["sample_mean"] >
                      # Evaluate statistics['C2'] at 'sample_mean' as part of the enclosing expression.
                      statistics["C2"]["sample_mean"])
    # Set blocker_status to a dictionary of blocker mapped to the text 'STILL_REQUIRES_PREDECLARATION' for blocker
    # in BLOCKERS.
    blocker_status = {blocker: "STILL_REQUIRES_PREDECLARATION"
                      # Evaluate BLOCKERS as part of the enclosing expression.
                      for blocker in BLOCKERS}
    # Set result to a dictionary containing checkpoint, source_evidence_identity, status, observed_structure,...
    result = {
        "checkpoint": "STEP_5J_3C_2C",
        # Store a dictionary containing evidence_tranche_identity, sha256, checkpoint, status under
        # 'source_evidence_identity'.
        "source_evidence_identity": {
            # Store evidence at 'evidence_tranche_identity' under 'evidence_tranche_identity'.
            "evidence_tranche_identity": evidence["evidence_tranche_identity"],
            # Store the result of _digest(evidence) under 'sha256'.
            "sha256": _digest(evidence),
            # Store evidence at 'checkpoint' under 'checkpoint'.
            "checkpoint": evidence["checkpoint"],
            # Store evidence at 'status' under 'status'.
            "status": evidence["status"]},
        "status": "EXTENDED_EVIDENCE_REVIEW_COMPLETE",
        # Store a dictionary containing replications, policy_states_per_replication,
        # update_intervals_per_replication,... under 'observed_structure'.
        "observed_structure": {
            # Store 3 under 'replications'.
            # Store 3 under 'policy_states_per_replication'.
            "replications": 3, "policy_states_per_replication": 3,
            # Store 2 under 'update_intervals_per_replication'.
            "update_intervals_per_replication": 2,
            # Store 9 under 'training_manifest_collections'.
            "training_manifest_collections": 9,
            # Store 324 under 'training_scenario_executions'.
            "training_scenario_executions": 324,
            "total_sumo_steps":
                # Evaluate evidence['compute_cost_evidence'] at 'total_sumo_steps' as part of the enclosing
                # expression.
                evidence["compute_cost_evidence"]["total_sumo_steps"]},
        # Store a dictionary containing C0, C1, C2, delta_0_to_1, delta_1_to_2, delta_0_to_2,
        # descriptive_statistics,... under 'learning_curve_evidence'.
        "learning_curve_evidence": {
            # Store c at 'C0' under 'C0'.
            # Store c at 'C1' under 'C1'.
            # Store c at 'C2' under 'C2'.
            "C0": c["C0"], "C1": c["C1"], "C2": c["C2"],
            # Store deltas at 'delta_0_to_1' under 'delta_0_to_1'.
            "delta_0_to_1": deltas["delta_0_to_1"],
            # Store deltas at 'delta_1_to_2' under 'delta_1_to_2'.
            "delta_1_to_2": deltas["delta_1_to_2"],
            # Store deltas at 'delta_0_to_2' under 'delta_0_to_2'.
            "delta_0_to_2": deltas["delta_0_to_2"],
            # Store statistics under 'descriptive_statistics'.
            "descriptive_statistics": statistics,
            # Store latest_directions under 'latest_update_directions'.
            "latest_update_directions": latest_directions,
            "latest_update_direction_consistent":
                # Evaluate the number of entries in a set built from latest_directions equals 1 as part of the
                # enclosing expression.
                len(set(latest_directions)) == 1,
            # Store mean_decreases under 'mean_C0_greater_than_C1_greater_than_C2'.
            "mean_C0_greater_than_C1_greater_than_C2": mean_decreases,
            # Store all_end_to_end_improve under 'all_replications_C2_lower_than_C0'.
            "all_replications_C2_lower_than_C0": all_end_to_end_improve,
            # Store True under 'mean_decrease_is_empirical_observation'.
            "mean_decrease_is_empirical_observation": True,
            # Store False under 'mean_decrease_is_selection_rule'.
            "mean_decrease_is_selection_rule": False,
            # Store False under 'mean_decrease_proves_convergence'.
            "mean_decrease_proves_convergence": False},
        # Store a dictionary containing status, states_observed, update_intervals_observed,
        # plateau_established,... under 'training_budget_assessment'.
        "training_budget_assessment": {
            "status":
                "INSUFFICIENT_NO_PREDECLARED_STABILITY_CRITERION_AND_CURVE_STILL_EVOLVING",
            # Store 3 under 'states_observed'.
            # Store 2 under 'update_intervals_observed'.
            "states_observed": 3, "update_intervals_observed": 2,
            # Store False under 'plateau_established'.
            "plateau_established": False,
            # Store False under 'convergence_established'.
            "convergence_established": False,
            # Store False under 'later_degradation_characterized'.
            "later_degradation_characterized": False,
            # Store False under 'consistent_latest_update_direction'.
            "consistent_latest_update_direction": False,
            # Store False under 'final_training_budget_justified'.
            "final_training_budget_justified": False,
            # Store False under 'final_training_budget_selected'.
            "final_training_budget_selected": False,
            "final_update_count": "NOT_SELECTED"},
        # Store a dictionary containing status, independent_replications, all_retained, replications_discarded,...
        # under 'replication_assessment'.
        "replication_assessment": {
            "status":
                "INSUFFICIENT_NO_PREDECLARED_REPLICATION_ADEQUACY_CRITERION",
            # Store 3 under 'independent_replications'.
            "independent_replications": 3,
            # Store True under 'all_retained'.
            "all_retained": True,
            # Store 0 under 'replications_discarded'.
            "replications_discarded": 0,
            # Store 0 under 'outliers_declared'.
            "outliers_declared": 0,
            # Store 0 under 'performance_selected_replications'.
            "performance_selected_replications": 0,
            # Store False under 'learning_trajectories_identical'.
            "learning_trajectories_identical": False,
            # Store True under 'seed_variability_observed'.
            "seed_variability_observed": True,
            # Store False under 'adequacy_criterion_predeclared'.
            "adequacy_criterion_predeclared": False,
            # Store False under 'final_replication_count_justified'.
            "final_replication_count_justified": False,
            # Store False under 'final_replication_count_selected'.
            "final_replication_count_selected": False,
            "final_replication_count": "NOT_SELECTED"},
        # Store a dictionary containing status, state_2_selected_because_mean_is_lowest, model_selected,... under
        # 'checkpoint_selection_assessment'.
        "checkpoint_selection_assessment": {
            "status": "REQUIRES_PREDECLARED_SELECTION_RULE",
            # Store False under 'state_2_selected_because_mean_is_lowest'.
            "state_2_selected_because_mean_is_lowest": False,
            # Store False under 'model_selected'.
            "model_selected": False,
            # Store False under 'final_checkpoint_selected'.
            "final_checkpoint_selected": False,
            # Store checkpoint_audits under 'checkpoint_audits'.
            "checkpoint_audits": checkpoint_audits},
        # Store a dictionary containing status, new_convergence_thresholds,
        # new_replication_adequacy_thresholds,... under 'statistical_rule_assessment'.
        "statistical_rule_assessment": {
            "status": "REQUIRES_PREDECLARATION",
            # Store 0 under 'new_convergence_thresholds'.
            "new_convergence_thresholds": 0,
            # Store 0 under 'new_replication_adequacy_thresholds'.
            "new_replication_adequacy_thresholds": 0,
            # Store False under 'post_hoc_stopping_rule_created'.
            "post_hoc_stopping_rule_created": False},
        # Store a dictionary containing status, ready, candidate_comparisons_started under
        # 'candidate_comparison_readiness'.
        "candidate_comparison_readiness": {
            "status": "NOT_READY_SELECTION_PROTOCOL_INCOMPLETE",
            # Store False under 'ready'.
            "ready": False,
            # Store 0 under 'candidate_comparisons_started'.
            "candidate_comparisons_started": 0},
        # Store a dictionary containing new_unique_training_scenario_identities_required_now,... under
        # 'scenario_assessment'.
        "scenario_assessment": {
            # Store False under 'new_unique_training_scenario_identities_required_now'.
            "new_unique_training_scenario_identities_required_now": False,
            # Store True under 'repeated_on_policy_frozen_training_manifest_exposure'.
            "repeated_on_policy_frozen_training_manifest_exposure": True,
            # Store False under 'scenario_manifests_modified'.
            "scenario_manifests_modified": False},
        # Store a dictionary containing validation, held_out under 'future_data_roles'.
        "future_data_roles": {
            "validation": "CONFIGURATION_AND_CHECKPOINT_COMPARISON_ONLY_AFTER_SELECTION_METHODOLOGY_IS_FROZEN",
            "held_out": "FINAL_UNBIASED_EVALUATION_AFTER_ALL_CHOICES_ARE_FROZEN"},
        # Store evidence at 'safety_evidence' under 'safety_evidence'.
        "safety_evidence": evidence["safety_evidence"],
        # Store evidence at 'compute_cost_evidence' under 'compute_evidence'.
        "compute_evidence": evidence["compute_cost_evidence"],
        # Store blocker_status under 'methodological_blocker_assessment'.
        "methodological_blocker_assessment": blocker_status,
        # Store a list built from BLOCKERS under 'methodological_blockers'.
        "methodological_blockers": list(BLOCKERS),
        # Store 0 under 'new_hyperparameters'.
        "new_hyperparameters": 0,
        # Store 0 under 'new_training_executions'.
        "new_training_executions": 0,
        # Store 0 under 'new_sumo_executions'.
        "new_sumo_executions": 0,
        # Store 0 under 'validation_executions'.
        "validation_executions": 0,
        # Store 0 under 'held_out_executions'.
        "held_out_executions": 0,
        # Store 0 under 'optimizer_instances'.
        "optimizer_instances": 0,
        # Store 0 under 'optimizer_invocations'.
        "optimizer_invocations": 0,
        # Store 0 under 'backward_calls'.
        "backward_calls": 0,
        # Store 0 under 'parameter_updates'.
        "parameter_updates": 0,
        # Store False under 'update_3_performed'.
        "update_3_performed": False,
        # Store False under 'replication_3_created'.
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
    # Write the supplied text to Path(output_path).
    Path(output_path).write_text(json.dumps(result, indent=2), encoding="utf-8")
    # Return result to the caller.
    return result
