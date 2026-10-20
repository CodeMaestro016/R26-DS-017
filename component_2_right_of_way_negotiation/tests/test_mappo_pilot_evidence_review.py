# Import json for use in this module.
import json
# Import Path from pathlib for the operations below.
from pathlib import Path

# Import pytest for use in this module.
import pytest

# Import build_pilot_evidence_review, load_and_validate_pilot_evidence from
# negotiation_training.pilot_evidence_review for the operations below.
from negotiation_training.pilot_evidence_review import (
    build_pilot_evidence_review,
    load_and_validate_pilot_evidence,
)


# Apply pytest.fixture(scope='module') as a decorator to configure the following definition.
@pytest.fixture(scope="module")
# Review using the inputs and processing steps below.
# Input tmp_path_factory: the supplied tmp path factory.
# Output: the result of build_pilot_evidence_review().
def review(tmp_path_factory):
    # Return the result of build_pilot_evidence_review() to the caller.
    return build_pilot_evidence_review(
        # Supply output_path as the result of tmp_path_factory.mktemp(the text 'review') joined with the path segment
        # 'review.json'.
        output_path=tmp_path_factory.mktemp("review") / "review.json")


# Check pilot artifact identity validation using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_pilot_artifact_identity_validation():
    # Set evidence to the result of load_and_validate_pilot_evidence().
    evidence = load_and_validate_pilot_evidence()
    # Require evidence at 'status' equals the text 'CLOSED_LOOP_PROGRESS_AND_VARIANCE_PROBE_COMPLETE'; otherwise
    # raise AssertionError.
    assert evidence["status"] == "CLOSED_LOOP_PROGRESS_AND_VARIANCE_PROBE_COMPLETE"
    # Require evidence at 'replication_probe_reason' equals the text 'MINIMUM_SAMPLE_VARIANCE_PROBE'; otherwise
    # raise AssertionError.
    assert evidence["replication_probe_reason"] == "MINIMUM_SAMPLE_VARIANCE_PROBE"


# Check invalid pilot identity is rejected using the setup, calls, and assertions below.
# Input tmp_path: the supplied tmp path.
# Output: no explicit value; normal completion returns None.
def test_invalid_pilot_identity_is_rejected(tmp_path):
    # Set evidence to the result of load_and_validate_pilot_evidence().
    evidence = load_and_validate_pilot_evidence()
    # Set evidence['status'] to the text 'WRONG'.
    evidence["status"] = "WRONG"
    # Set path to tmp_path joined with the path segment 'bad.json'.
    path = tmp_path / "bad.json"
    # Write the supplied text to path.
    path.write_text(json.dumps(evidence), encoding="utf-8")
    # Enter the result of pytest.raises(ValueError) and run the enclosed operations within that context.
    with pytest.raises(ValueError, match="INVALID_PILOT_EVIDENCE_STATUS"):
        # Call load_and_validate_pilot_evidence with the supplied arguments.
        load_and_validate_pilot_evidence(path)


# Check two replications and both effects are preserved using the setup, calls, and assertions below.
# Input review: the supplied review.
# Output: no explicit value; normal completion returns None.
def test_two_replications_and_both_effects_are_preserved(review):
    # Set pilot to review at 'pilot_statistics'.
    pilot = review["pilot_statistics"]
    # Require pilot at 'replications_observed' equals 2; otherwise raise AssertionError.
    assert pilot["replications_observed"] == 2
    # Require pilot at 'replication_indices_preserved' equals a list containing 0, 1; otherwise raise
    # AssertionError.
    assert pilot["replication_indices_preserved"] == [0, 1]
    # Require pilot at 'replications_discarded' equals 0; otherwise raise AssertionError.
    assert pilot["replications_discarded"] == 0
    # Require pilot at 'delta_values' equals the result of pytest.approx(a list containing the negative of 150.8,
    # the negative of 2939.52); otherwise raise AssertionError.
    assert pilot["delta_values"] == pytest.approx([-150.8, -2939.52])


# Check variance values are preserved exactly using the setup, calls, and assertions below.
# Input review: the supplied review.
# Output: no explicit value; normal completion returns None.
def test_variance_values_are_preserved_exactly(review):
    # Set pilot to review at 'pilot_statistics'.
    pilot = review["pilot_statistics"]
    # Require pilot at 'delta_sample_mean' equals the result of pytest.approx(the negative of 1545.16); otherwise
    # raise AssertionError.
    assert pilot["delta_sample_mean"] == pytest.approx(-1545.16)
    # Require pilot at 'delta_sample_variance_n_minus_1' equals the result of pytest.approx(3888479.6192);
    # otherwise raise AssertionError.
    assert pilot["delta_sample_variance_n_minus_1"] == pytest.approx(
        # Supply 3888479.6192 to the enclosing expression.
        3888479.6192)
    # Require pilot at 'delta_sample_standard_deviation' equals the result of pytest.approx(1971.922823613034);
    # otherwise raise AssertionError.
    assert pilot["delta_sample_standard_deviation"] == pytest.approx(
        # Supply 1971.922823613034 to the enclosing expression.
        1971.922823613034)


# Check single update interval is insufficient using the setup, calls, and assertions below.
# Input review: the supplied review.
# Output: no explicit value; normal completion returns None.
def test_single_update_interval_is_insufficient(review):
    # Set assessment to review at 'training_budget_sufficiency_assessment'.
    assessment = review["training_budget_sufficiency_assessment"]
    # Require assessment at 'status' equals the text 'INSUFFICIENT_SINGLE_UPDATE_INTERVAL'; otherwise raise
    # AssertionError.
    assert assessment["status"] == "INSUFFICIENT_SINGLE_UPDATE_INTERVAL"
    # Require assessment at 'final_training_budget_selected' is the same object as False; otherwise raise
    # AssertionError.
    assert assessment["final_training_budget_selected"] is False


# Check two run variance probe is insufficient using the setup, calls, and assertions below.
# Input review: the supplied review.
# Output: no explicit value; normal completion returns None.
def test_two_run_variance_probe_is_insufficient(review):
    # Set assessment to review at 'replication_sufficiency_assessment'.
    assessment = review["replication_sufficiency_assessment"]
    # Require assessment at 'status' equals the text 'INSUFFICIENT_MINIMUM_TWO_RUN_VARIANCE_PROBE'; otherwise
    # raise AssertionError.
    assert assessment["status"] == "INSUFFICIENT_MINIMUM_TWO_RUN_VARIANCE_PROBE"
    # Require assessment at 'final_replication_count_selected' is the same object as False; otherwise raise
    # AssertionError.
    assert assessment["final_replication_count_selected"] is False
    # Require assessment at 'observations_called_outliers' equals 0; otherwise raise AssertionError.
    assert assessment["observations_called_outliers"] == 0


# Check scenario count terminology and manifest reuse using the setup, calls, and assertions below.
# Input review: the supplied review.
# Output: no explicit value; normal completion returns None.
def test_scenario_count_terminology_and_manifest_reuse(review):
    # Set scenario to review at 'scenario_design_assessment'.
    scenario = review["scenario_design_assessment"]
    # Require a set built from scenario at 'terminology' equals a set containing the text
    # 'UNIQUE_TRAINING_SCENARIOS', the text 'TRAINING_MANIFEST_PASS', the text 'PPO_UPDATE_CYCLE', the...;
    # otherwise raise AssertionError.
    assert set(scenario["terminology"]) == {
        "UNIQUE_TRAINING_SCENARIOS", "TRAINING_MANIFEST_PASS",
        "PPO_UPDATE_CYCLE", "TRAINING_EXPOSURE"}
    # Require scenario at 'new_unique_training_scenarios_required_now' is the same object as False; otherwise
    # raise AssertionError.
    assert scenario["new_unique_training_scenarios_required_now"] is False
    # Require scenario at 'repeated_training_manifest_exposure_required' is the same object as True; otherwise
    # raise AssertionError.
    assert scenario["repeated_training_manifest_exposure_required"] is True
    # Require scenario at 'partitions_modified' is the same object as False; otherwise raise AssertionError.
    assert scenario["partitions_modified"] is False


# Check validation unused and held out sealed using the setup, calls, and assertions below.
# Input review: the supplied review.
# Output: no explicit value; normal completion returns None.
def test_validation_unused_and_held_out_sealed(review):
    # Require review['pilot_statistics'] at 'validation_runs' equals 0; otherwise raise AssertionError.
    assert review["pilot_statistics"]["validation_runs"] == 0
    # Require review['pilot_statistics'] at 'held_out_runs' equals 0; otherwise raise AssertionError.
    assert review["pilot_statistics"]["held_out_runs"] == 0
    # Set acquisition to review at 'extended_evidence_acquisition_design'.
    acquisition = review["extended_evidence_acquisition_design"]
    # Require acquisition at 'held_out_sealed' is the same object as True; otherwise raise AssertionError.
    assert acquisition["held_out_sealed"] is True


# Check no final counts selected using the setup, calls, and assertions below.
# Input review: the supplied review.
# Output: no explicit value; normal completion returns None.
def test_no_final_counts_selected(review):
    # Set acquisition to review at 'extended_evidence_acquisition_design'.
    acquisition = review["extended_evidence_acquisition_design"]
    # Require review at 'final_counts_selected' is the same object as False; otherwise raise AssertionError.
    assert review["final_counts_selected"] is False
    # Require acquisition at 'final_counts_selected' is the same object as False; otherwise raise AssertionError.
    assert acquisition["final_counts_selected"] is False
    # Require acquisition['replication_extension_rule'] at 'termination_count' equals the text 'NOT_YET_SELECTED';
    # otherwise raise AssertionError.
    assert acquisition["replication_extension_rule"]["termination_count"] == "NOT_YET_SELECTED"
    # Require acquisition['training_curve_extension_rule'] at 'final_update_count' equals the text
    # 'NOT_YET_SELECTED'; otherwise raise AssertionError.
    assert acquisition["training_curve_extension_rule"]["final_update_count"] == "NOT_YET_SELECTED"


# Check canonical replication stream continues without skipping using the setup, calls, and assertions below.
# Input review: the supplied review.
# Output: no explicit value; normal completion returns None.
def test_canonical_replication_stream_continues_without_skipping(review):
    # Set rule to review['extended_evidence_acquisition_design'] at 'replication_extension_rule'.
    rule = review["extended_evidence_acquisition_design"]["replication_extension_rule"]
    # Require rule at 'next_index' equals 2; otherwise raise AssertionError.
    assert rule["next_index"] == 2
    # Require rule at 'order' equals the text '2,3,4,..._WITHOUT_SKIPPING'; otherwise raise AssertionError.
    assert rule["order"] == "2,3,4,..._WITHOUT_SKIPPING"
    # Require rule at 'performance_based_replacement' is the same object as False; otherwise raise AssertionError.
    assert rule["performance_based_replacement"] is False


# Check no performance seed selection using the setup, calls, and assertions below.
# Input review: the supplied review.
# Output: no explicit value; normal completion returns None.
def test_no_performance_seed_selection(review):
    # Set acquisition to review at 'extended_evidence_acquisition_design'.
    acquisition = review["extended_evidence_acquisition_design"]
    # Require acquisition at 'performance_seed_selection_forbidden' is the same object as True; otherwise raise
    # AssertionError.
    assert acquisition["performance_seed_selection_forbidden"] is True


# Check no arbitrary convergence threshold using the setup, calls, and assertions below.
# Input review: the supplied review.
# Output: no explicit value; normal completion returns None.
def test_no_arbitrary_convergence_threshold(review):
    # Set rule to review['extended_evidence_acquisition_design'] at 'training_curve_extension_rule'.
    rule = review["extended_evidence_acquisition_design"]["training_curve_extension_rule"]
    # Require review at 'arbitrary_convergence_thresholds' equals 0; otherwise raise AssertionError.
    assert review["arbitrary_convergence_thresholds"] == 0
    # Require rule at 'convergence_rule' equals the text 'STATISTICAL_SELECTION_RULE_REQUIRES_PREDECLARATION';
    # otherwise raise AssertionError.
    assert rule["convergence_rule"] == "STATISTICAL_SELECTION_RULE_REQUIRES_PREDECLARATION"


# Check analysis performs no training or parameter update using the setup, calls, and assertions below.
# Input review: the supplied review.
# Output: no explicit value; normal completion returns None.
def test_analysis_performs_no_training_or_parameter_update(review):
    # Require review at 'sumo_invocations' equals 0; otherwise raise AssertionError.
    assert review["sumo_invocations"] == 0
    # Require review at 'optimizer_invocations' equals 0; otherwise raise AssertionError.
    assert review["optimizer_invocations"] == 0
    # Require review at 'backward_calls' equals 0; otherwise raise AssertionError.
    assert review["backward_calls"] == 0
    # Require review at 'model_parameter_updates' equals 0; otherwise raise AssertionError.
    assert review["model_parameter_updates"] == 0


# Check review module has no execution or optimizer imports using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_review_module_has_no_execution_or_optimizer_imports():
    # Set source to the text read from Path('negotiation_training/pilot_evidence_review.py').
    source = Path("negotiation_training/pilot_evidence_review.py").read_text(
        # Supply encoding as the text 'utf-8'.
        encoding="utf-8")
    # Require the text 'CoupledNegotiationTrainingEnvironment' does not belong to source; otherwise raise
    # AssertionError.
    assert "CoupledNegotiationTrainingEnvironment" not in source
    # Require the text 'MechanicalMAPPOTrainer' does not belong to source; otherwise raise AssertionError.
    assert "MechanicalMAPPOTrainer" not in source
    # Require the text 'torch' does not belong to source; otherwise raise AssertionError.
    assert "torch" not in source
    # Require the text 'traci' does not belong to the result of source.lower(); otherwise raise AssertionError.
    assert "traci" not in source.lower()


# Check all methodological blockers remain explicit using the setup, calls, and assertions below.
# Input review: the supplied review.
# Output: no explicit value; normal completion returns None.
def test_all_methodological_blockers_remain_explicit(review):
    # Set blockers to a set built from review at 'remaining_methodological_blockers'.
    blockers = set(review["remaining_methodological_blockers"])
    # Require a set containing the text 'TRAINING_BUDGET_SELECTION_CRITERION_REQUIRES_PREDECLARATION', the text...
    # is at most blockers; otherwise raise AssertionError.
    assert {
        "TRAINING_BUDGET_SELECTION_CRITERION_REQUIRES_PREDECLARATION",
        "REPLICATION_COUNT_ADEQUACY_CRITERION_REQUIRES_PREDECLARATION",
        "CANDIDATE_COMPARISON_STATISTIC_REQUIRES_PREDECLARATION",
        "TIE_RULE_REQUIRES_PREDECLARATION",
        "CHECKPOINT_MODEL_SELECTION_RULE_REQUIRES_PREDECLARATION",
    # Evaluate blockers as part of the enclosing expression.
    } <= blockers
