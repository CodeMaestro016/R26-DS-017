# Import json for use in this module.
import json
# Import Path from pathlib for the operations below.
from pathlib import Path

# Import pytest for use in this module.
import pytest

# Import BLOCKERS, build_extended_evidence_review, load_and_validate_extended_evidence from
# negotiation_training.extended_evidence_review for the operations below.
from negotiation_training.extended_evidence_review import (
    BLOCKERS, build_extended_evidence_review,
    load_and_validate_extended_evidence)


# Apply pytest.fixture(scope='module') as a decorator to configure the following definition.
@pytest.fixture(scope="module")
# Review using the inputs and processing steps below.
# Input tmp_path_factory: the supplied tmp path factory.
# Output: the result of build_extended_evidence_review().
def review(tmp_path_factory):
    # Return the result of build_extended_evidence_review() to the caller.
    return build_extended_evidence_review(
        # Supply output_path as the result of tmp_path_factory.mktemp(the text 'extended_review') divided by the
        # text 'review.json'.
        output_path=tmp_path_factory.mktemp("extended_review") / "review.json")


# Check source artifact identity and exact structure using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_source_artifact_identity_and_exact_structure():
    # Set source to the result of load_and_validate_extended_evidence().
    source = load_and_validate_extended_evidence()
    # Require source at 'checkpoint' equals the text 'STEP_5J_3C_2B'; otherwise raise AssertionError.
    assert source["checkpoint"] == "STEP_5J_3C_2B"
    # Require source at 'status' equals the text 'EXTENDED_MULTI_UPDATE_EVIDENCE_ACQUIRED'; otherwise raise
    # AssertionError.
    assert source["status"] == "EXTENDED_MULTI_UPDATE_EVIDENCE_ACQUIRED"
    # Require source at 'replications_observed' equals 3; otherwise raise AssertionError.
    assert source["replications_observed"] == 3
    # Require source at 'policy_states_per_replication' equals 3; otherwise raise AssertionError.
    assert source["policy_states_per_replication"] == 3
    # Require source at 'update_intervals_observed_per_replication' equals 2; otherwise raise AssertionError.
    assert source["update_intervals_observed_per_replication"] == 2
    # Require whether every item is true in a lazy sequence of len(item['policy_states']) equals 3 and
    # len(item['updates']) equals 2 for item in source at 'replications'; otherwise raise AssertionError.
    assert all(len(item["policy_states"]) == 3 and len(item["updates"]) == 2
               # Evaluate source at 'replications' as part of the enclosing expression.
               for item in source["replications"])


# Check invalid source identity stops review using the setup, calls, and assertions below.
# Input tmp_path: the supplied tmp path.
# Output: no explicit value; normal completion returns None.
def test_invalid_source_identity_stops_review(tmp_path):
    # Set source to the result of load_and_validate_extended_evidence().
    source = load_and_validate_extended_evidence()
    # Set source['replications_observed'] to 4.
    source["replications_observed"] = 4
    # Set path to tmp_path joined with the path segment 'bad.json'.
    path = tmp_path / "bad.json"
    # Write the supplied text to path.
    path.write_text(json.dumps(source), encoding="utf-8")
    # Enter the result of pytest.raises(ValueError) and run the enclosed operations within that context.
    with pytest.raises(ValueError, match="EXTENDED_EVIDENCE_IDENTITY_INVALID"):
        # Call load_and_validate_extended_evidence with the supplied arguments.
        load_and_validate_extended_evidence(path)


# Check c values preserved using the setup, calls, and assertions below.
# Input review: the supplied review.
# Output: no explicit value; normal completion returns None.
def test_c_values_preserved(review):
    # Set curve to review at 'learning_curve_evidence'.
    curve = review["learning_curve_evidence"]
    # Require curve at 'C0' equals the result of pytest.approx(a list containing 19035.08, 14027.04, 18130.24);
    # otherwise raise AssertionError.
    assert curve["C0"] == pytest.approx([19035.08, 14027.04, 18130.24])
    # Require curve at 'C1' equals the result of pytest.approx(a list containing 19464.16, 11334.8, 17817.12);
    # otherwise raise AssertionError.
    assert curve["C1"] == pytest.approx([19464.16, 11334.8, 17817.12])
    # Require curve at 'C2' equals the result of pytest.approx(a list containing 18847.0, 11763.36, 16929.56);
    # otherwise raise AssertionError.
    assert curve["C2"] == pytest.approx([18847.0, 11763.36, 16929.56])


# Check deltas recomputed from states using the setup, calls, and assertions below.
# Input review: the supplied review.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def test_deltas_recomputed_from_states(review):
    # Set curve to review at 'learning_curve_evidence'.
    curve = review["learning_curve_evidence"]
    # Iterate over the integer range defined by 3, binding each item to index.
    for index in range(3):
        # Require curve['delta_0_to_1'] at index equals the result of pytest.approx(curve['C1'] at index minus
        # curve['C0'] at index); otherwise raise AssertionError.
        assert curve["delta_0_to_1"][index] == pytest.approx(
            # Supply curve['C1'] at index minus curve['C0'] at index to pytest.approx.
            curve["C1"][index] - curve["C0"][index])
        # Require curve['delta_1_to_2'] at index equals the result of pytest.approx(curve['C2'] at index minus
        # curve['C1'] at index); otherwise raise AssertionError.
        assert curve["delta_1_to_2"][index] == pytest.approx(
            # Supply curve['C2'] at index minus curve['C1'] at index to pytest.approx.
            curve["C2"][index] - curve["C1"][index])
        # Require curve['delta_0_to_2'] at index equals the result of pytest.approx(curve['C2'] at index minus
        # curve['C0'] at index); otherwise raise AssertionError.
        assert curve["delta_0_to_2"][index] == pytest.approx(
            # Supply curve['C2'] at index minus curve['C0'] at index to pytest.approx.
            curve["C2"][index] - curve["C0"][index])


# Check cross replication statistics preserved using the setup, calls, and assertions below.
# Input review: the supplied review.
# Output: no explicit value; normal completion returns None.
def test_cross_replication_statistics_preserved(review):
    # Set stats to review['learning_curve_evidence'] at 'descriptive_statistics'.
    stats = review["learning_curve_evidence"]["descriptive_statistics"]
    # Require stats['C0'] at 'sample_mean' equals the result of pytest.approx(17064.12); otherwise raise
    # AssertionError.
    assert stats["C0"]["sample_mean"] == pytest.approx(17064.12)
    # Require stats['C1'] at 'sample_mean' equals the result of pytest.approx(16205.36); otherwise raise
    # AssertionError.
    assert stats["C1"]["sample_mean"] == pytest.approx(16205.36)
    # Require stats['C2'] at 'sample_mean' equals the result of pytest.approx(15846.64); otherwise raise
    # AssertionError.
    assert stats["C2"]["sample_mean"] == pytest.approx(15846.64)
    # Require stats['delta_0_to_2'] at 'sample_variance_n_minus_1' equals the result of pytest.approx(1077240.52);
    # otherwise raise AssertionError.
    assert stats["delta_0_to_2"]["sample_variance_n_minus_1"] == \
        pytest.approx(1077240.52)


# Check latest update directions are mixed using the setup, calls, and assertions below.
# Input review: the supplied review.
# Output: no explicit value; normal completion returns None.
def test_latest_update_directions_are_mixed(review):
    # Set curve to review at 'learning_curve_evidence'.
    curve = review["learning_curve_evidence"]
    # Require curve at 'latest_update_directions' equals a list containing the text 'IMPROVEMENT', the text
    # 'WORSENING', the text 'IMPROVEMENT'; otherwise raise AssertionError.
    assert curve["latest_update_directions"] == [
        "IMPROVEMENT", "WORSENING", "IMPROVEMENT"]
    # Require curve at 'latest_update_direction_consistent' is the same object as False; otherwise raise
    # AssertionError.
    assert curve["latest_update_direction_consistent"] is False


# Check mean decrease is observation not convergence using the setup, calls, and assertions below.
# Input review: the supplied review.
# Output: no explicit value; normal completion returns None.
def test_mean_decrease_is_observation_not_convergence(review):
    # Set curve to review at 'learning_curve_evidence'.
    curve = review["learning_curve_evidence"]
    # Require curve at 'mean_C0_greater_than_C1_greater_than_C2' is the same object as True; otherwise raise
    # AssertionError.
    assert curve["mean_C0_greater_than_C1_greater_than_C2"] is True
    # Require curve at 'all_replications_C2_lower_than_C0' is the same object as True; otherwise raise
    # AssertionError.
    assert curve["all_replications_C2_lower_than_C0"] is True
    # Require curve at 'mean_decrease_is_empirical_observation' is the same object as True; otherwise raise
    # AssertionError.
    assert curve["mean_decrease_is_empirical_observation"] is True
    # Require curve at 'mean_decrease_is_selection_rule' is the same object as False; otherwise raise
    # AssertionError.
    assert curve["mean_decrease_is_selection_rule"] is False
    # Require curve at 'mean_decrease_proves_convergence' is the same object as False; otherwise raise
    # AssertionError.
    assert curve["mean_decrease_proves_convergence"] is False


# Check no plateau or final training budget inferred using the setup, calls, and assertions below.
# Input review: the supplied review.
# Output: no explicit value; normal completion returns None.
def test_no_plateau_or_final_training_budget_inferred(review):
    # Set assessment to review at 'training_budget_assessment'.
    assessment = review["training_budget_assessment"]
    # Require assessment at 'plateau_established' is the same object as False; otherwise raise AssertionError.
    assert assessment["plateau_established"] is False
    # Require assessment at 'convergence_established' is the same object as False; otherwise raise AssertionError.
    assert assessment["convergence_established"] is False
    # Require assessment at 'final_training_budget_justified' is the same object as False; otherwise raise
    # AssertionError.
    assert assessment["final_training_budget_justified"] is False
    # Require assessment at 'final_training_budget_selected' is the same object as False; otherwise raise
    # AssertionError.
    assert assessment["final_training_budget_selected"] is False
    # Require assessment at 'final_update_count' equals the text 'NOT_SELECTED'; otherwise raise AssertionError.
    assert assessment["final_update_count"] == "NOT_SELECTED"


# Check all replications retained without outliers using the setup, calls, and assertions below.
# Input review: the supplied review.
# Output: no explicit value; normal completion returns None.
def test_all_replications_retained_without_outliers(review):
    # Set assessment to review at 'replication_assessment'.
    assessment = review["replication_assessment"]
    # Require assessment at 'all_retained' is the same object as True; otherwise raise AssertionError.
    assert assessment["all_retained"] is True
    # Require assessment at 'replications_discarded' equals 0; otherwise raise AssertionError.
    assert assessment["replications_discarded"] == 0
    # Require assessment at 'outliers_declared' equals 0; otherwise raise AssertionError.
    assert assessment["outliers_declared"] == 0
    # Require assessment at 'performance_selected_replications' equals 0; otherwise raise AssertionError.
    assert assessment["performance_selected_replications"] == 0
    # Require assessment at 'final_replication_count_selected' is the same object as False; otherwise raise
    # AssertionError.
    assert assessment["final_replication_count_selected"] is False
    # Require assessment at 'final_replication_count' equals the text 'NOT_SELECTED'; otherwise raise
    # AssertionError.
    assert assessment["final_replication_count"] == "NOT_SELECTED"


# Check no checkpoint selected and resume states remain ineligible using the setup, calls, and assertions below.
# Input review: the supplied review.
# Output: no explicit value; normal completion returns None.
def test_no_checkpoint_selected_and_resume_states_remain_ineligible(review):
    # Set assessment to review at 'checkpoint_selection_assessment'.
    assessment = review["checkpoint_selection_assessment"]
    # Require assessment at 'model_selected' is the same object as False; otherwise raise AssertionError.
    assert assessment["model_selected"] is False
    # Require assessment at 'final_checkpoint_selected' is the same object as False; otherwise raise
    # AssertionError.
    assert assessment["final_checkpoint_selected"] is False
    # Require the number of entries in assessment at 'checkpoint_audits' equals 9; otherwise raise AssertionError.
    assert len(assessment["checkpoint_audits"]) == 9
    # Require whether every item is true in a lazy sequence of the negation of item at flag for item in assessment
    # at 'checkpoint_audits'; otherwise raise AssertionError.
    assert all(not item[flag] for item in assessment["checkpoint_audits"]
               # Evaluate a tuple containing the text 'best_model', the text 'final_model', the text
               # 'selected_model', the text 'selection_eligible' as part of the enclosing expression.
               for flag in ("best_model", "final_model", "selected_model",
                            "selection_eligible"))


# Check no new threshold or hyperparameter using the setup, calls, and assertions below.
# Input review: the supplied review.
# Output: no explicit value; normal completion returns None.
def test_no_new_threshold_or_hyperparameter(review):
    # Set rules to review at 'statistical_rule_assessment'.
    rules = review["statistical_rule_assessment"]
    # Require rules at 'status' equals the text 'REQUIRES_PREDECLARATION'; otherwise raise AssertionError.
    assert rules["status"] == "REQUIRES_PREDECLARATION"
    # Require rules at 'new_convergence_thresholds' equals 0; otherwise raise AssertionError.
    assert rules["new_convergence_thresholds"] == 0
    # Require rules at 'new_replication_adequacy_thresholds' equals 0; otherwise raise AssertionError.
    assert rules["new_replication_adequacy_thresholds"] == 0
    # Require review at 'new_hyperparameters' equals 0; otherwise raise AssertionError.
    assert review["new_hyperparameters"] == 0


# Check data and execution boundaries using the setup, calls, and assertions below.
# Input review: the supplied review.
# Output: no explicit value; normal completion returns None.
def test_data_and_execution_boundaries(review):
    # Require review at 'new_training_executions' equals 0; otherwise raise AssertionError.
    assert review["new_training_executions"] == 0
    # Require review at 'new_sumo_executions' equals 0; otherwise raise AssertionError.
    assert review["new_sumo_executions"] == 0
    # Require review at 'validation_executions' equals 0; otherwise raise AssertionError.
    assert review["validation_executions"] == 0
    # Require review at 'held_out_executions' equals 0; otherwise raise AssertionError.
    assert review["held_out_executions"] == 0
    # Require review at 'optimizer_instances' equals 0; otherwise raise AssertionError.
    assert review["optimizer_instances"] == 0
    # Require review at 'optimizer_invocations' equals 0; otherwise raise AssertionError.
    assert review["optimizer_invocations"] == 0
    # Require review at 'backward_calls' equals 0; otherwise raise AssertionError.
    assert review["backward_calls"] == 0
    # Require review at 'parameter_updates' equals 0; otherwise raise AssertionError.
    assert review["parameter_updates"] == 0
    # Require review at 'update_3_performed' is the same object as False; otherwise raise AssertionError.
    assert review["update_3_performed"] is False
    # Require review at 'replication_3_created' is the same object as False; otherwise raise AssertionError.
    assert review["replication_3_created"] is False


# Check candidate comparison not ready using the setup, calls, and assertions below.
# Input review: the supplied review.
# Output: no explicit value; normal completion returns None.
def test_candidate_comparison_not_ready(review):
    # Set readiness to review at 'candidate_comparison_readiness'.
    readiness = review["candidate_comparison_readiness"]
    # Require readiness at 'ready' is the same object as False; otherwise raise AssertionError.
    assert readiness["ready"] is False
    # Require readiness at 'status' equals the text 'NOT_READY_SELECTION_PROTOCOL_INCOMPLETE'; otherwise raise
    # AssertionError.
    assert readiness["status"] == "NOT_READY_SELECTION_PROTOCOL_INCOMPLETE"
    # Require readiness at 'candidate_comparisons_started' equals 0; otherwise raise AssertionError.
    assert readiness["candidate_comparisons_started"] == 0


# Check every prior methodological blocker remains using the setup, calls, and assertions below.
# Input review: the supplied review.
# Output: no explicit value; normal completion returns None.
def test_every_prior_methodological_blocker_remains(review):
    # Require a set built from review at 'methodological_blockers' equals a set built from BLOCKERS; otherwise
    # raise AssertionError.
    assert set(review["methodological_blockers"]) == set(BLOCKERS)
    # Require a set built from values from review['methodological_blocker_assessment'] equals a set containing the
    # text 'STILL_REQUIRES_PREDECLARATION'; otherwise raise AssertionError.
    assert set(review["methodological_blocker_assessment"].values()) == {
        "STILL_REQUIRES_PREDECLARATION"}


# Check validator and review do not import execution runner or traci using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_validator_and_review_do_not_import_execution_runner_or_traci():
    # Set sources to the result of '\n'.join(a lazy sequence of the text read from Path(path) for path in a tuple
    # containing the text...).
    sources = "\n".join(Path(path).read_text(encoding="utf-8") for path in (
        "negotiation_training/extended_evidence_review.py",
        "scripts/validation/validate_mappo_extended_evidence_review.py"))
    # Require the text 'ExtendedMAPLearningCurveRunner' does not belong to sources; otherwise raise
    # AssertionError.
    assert "ExtendedMAPLearningCurveRunner" not in sources
    # Require the text 'MechanicalMAPPOTrainer' does not belong to sources; otherwise raise AssertionError.
    assert "MechanicalMAPPOTrainer" not in sources
    # Require the text 'CoupledNegotiationTrainingEnvironment' does not belong to sources; otherwise raise
    # AssertionError.
    assert "CoupledNegotiationTrainingEnvironment" not in sources
    # Require the text 'traci' does not belong to the result of sources.lower(); otherwise raise AssertionError.
    assert "traci" not in sources.lower()
    # Require the text 'optimizer.step' does not belong to sources; otherwise raise AssertionError.
    assert "optimizer.step" not in sources
    # Require the text '.backward(' does not belong to sources; otherwise raise AssertionError.
    assert ".backward(" not in sources


# Check next checkpoint is protocol not more training using the setup, calls, and assertions below.
# Input review: the supplied review.
# Output: no explicit value; normal completion returns None.
def test_next_checkpoint_is_protocol_not_more_training(review):
    # Require review at 'next_checkpoint' equals the text 'STEP_5J_3C_2D_PREDECLARED_SELECTION_PROTOCOL';
    # otherwise raise AssertionError.
    assert review["next_checkpoint"] == \
        "STEP_5J_3C_2D_PREDECLARED_SELECTION_PROTOCOL"
    # Require review at 'next_checkpoint_reason' equals the text
    # 'PREDECLARE_AND_FREEZE_SELECTION_AND_TERMINATION_RULES_BEFORE_A...'; otherwise raise AssertionError.
    assert review["next_checkpoint_reason"] == \
        "PREDECLARE_AND_FREEZE_SELECTION_AND_TERMINATION_RULES_BEFORE_ACQUIRING_MORE_EVIDENCE"
