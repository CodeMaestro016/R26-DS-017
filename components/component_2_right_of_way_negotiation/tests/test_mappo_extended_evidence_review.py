import json
from pathlib import Path

import pytest

from negotiation_training.extended_evidence_review import (
    BLOCKERS, build_extended_evidence_review,
    load_and_validate_extended_evidence)


@pytest.fixture(scope="module")
def review(tmp_path_factory):
    return build_extended_evidence_review(
        output_path=tmp_path_factory.mktemp("extended_review") / "review.json")


def test_source_artifact_identity_and_exact_structure():
    source = load_and_validate_extended_evidence()
    assert source["checkpoint"] == "STEP_5J_3C_2B"
    assert source["status"] == "EXTENDED_MULTI_UPDATE_EVIDENCE_ACQUIRED"
    assert source["replications_observed"] == 3
    assert source["policy_states_per_replication"] == 3
    assert source["update_intervals_observed_per_replication"] == 2
    assert all(len(item["policy_states"]) == 3 and len(item["updates"]) == 2
               for item in source["replications"])


def test_invalid_source_identity_stops_review(tmp_path):
    source = load_and_validate_extended_evidence()
    source["replications_observed"] = 4
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(source), encoding="utf-8")
    with pytest.raises(ValueError, match="EXTENDED_EVIDENCE_IDENTITY_INVALID"):
        load_and_validate_extended_evidence(path)


def test_c_values_preserved(review):
    curve = review["learning_curve_evidence"]
    assert curve["C0"] == pytest.approx([19035.08, 14027.04, 18130.24])
    assert curve["C1"] == pytest.approx([19464.16, 11334.8, 17817.12])
    assert curve["C2"] == pytest.approx([18847.0, 11763.36, 16929.56])


def test_deltas_recomputed_from_states(review):
    curve = review["learning_curve_evidence"]
    for index in range(3):
        assert curve["delta_0_to_1"][index] == pytest.approx(
            curve["C1"][index] - curve["C0"][index])
        assert curve["delta_1_to_2"][index] == pytest.approx(
            curve["C2"][index] - curve["C1"][index])
        assert curve["delta_0_to_2"][index] == pytest.approx(
            curve["C2"][index] - curve["C0"][index])


def test_cross_replication_statistics_preserved(review):
    stats = review["learning_curve_evidence"]["descriptive_statistics"]
    assert stats["C0"]["sample_mean"] == pytest.approx(17064.12)
    assert stats["C1"]["sample_mean"] == pytest.approx(16205.36)
    assert stats["C2"]["sample_mean"] == pytest.approx(15846.64)
    assert stats["delta_0_to_2"]["sample_variance_n_minus_1"] == \
        pytest.approx(1077240.52)


def test_latest_update_directions_are_mixed(review):
    curve = review["learning_curve_evidence"]
    assert curve["latest_update_directions"] == [
        "IMPROVEMENT", "WORSENING", "IMPROVEMENT"]
    assert curve["latest_update_direction_consistent"] is False


def test_mean_decrease_is_observation_not_convergence(review):
    curve = review["learning_curve_evidence"]
    assert curve["mean_C0_greater_than_C1_greater_than_C2"] is True
    assert curve["all_replications_C2_lower_than_C0"] is True
    assert curve["mean_decrease_is_empirical_observation"] is True
    assert curve["mean_decrease_is_selection_rule"] is False
    assert curve["mean_decrease_proves_convergence"] is False


def test_no_plateau_or_final_training_budget_inferred(review):
    assessment = review["training_budget_assessment"]
    assert assessment["plateau_established"] is False
    assert assessment["convergence_established"] is False
    assert assessment["final_training_budget_justified"] is False
    assert assessment["final_training_budget_selected"] is False
    assert assessment["final_update_count"] == "NOT_SELECTED"


def test_all_replications_retained_without_outliers(review):
    assessment = review["replication_assessment"]
    assert assessment["all_retained"] is True
    assert assessment["replications_discarded"] == 0
    assert assessment["outliers_declared"] == 0
    assert assessment["performance_selected_replications"] == 0
    assert assessment["final_replication_count_selected"] is False
    assert assessment["final_replication_count"] == "NOT_SELECTED"


def test_no_checkpoint_selected_and_resume_states_remain_ineligible(review):
    assessment = review["checkpoint_selection_assessment"]
    assert assessment["model_selected"] is False
    assert assessment["final_checkpoint_selected"] is False
    assert len(assessment["checkpoint_audits"]) == 9
    assert all(not item[flag] for item in assessment["checkpoint_audits"]
               for flag in ("best_model", "final_model", "selected_model",
                            "selection_eligible"))


def test_no_new_threshold_or_hyperparameter(review):
    rules = review["statistical_rule_assessment"]
    assert rules["status"] == "REQUIRES_PREDECLARATION"
    assert rules["new_convergence_thresholds"] == 0
    assert rules["new_replication_adequacy_thresholds"] == 0
    assert review["new_hyperparameters"] == 0


def test_data_and_execution_boundaries(review):
    assert review["new_training_executions"] == 0
    assert review["new_sumo_executions"] == 0
    assert review["validation_executions"] == 0
    assert review["held_out_executions"] == 0
    assert review["optimizer_instances"] == 0
    assert review["optimizer_invocations"] == 0
    assert review["backward_calls"] == 0
    assert review["parameter_updates"] == 0
    assert review["update_3_performed"] is False
    assert review["replication_3_created"] is False


def test_candidate_comparison_not_ready(review):
    readiness = review["candidate_comparison_readiness"]
    assert readiness["ready"] is False
    assert readiness["status"] == "NOT_READY_SELECTION_PROTOCOL_INCOMPLETE"
    assert readiness["candidate_comparisons_started"] == 0


def test_every_prior_methodological_blocker_remains(review):
    assert set(review["methodological_blockers"]) == set(BLOCKERS)
    assert set(review["methodological_blocker_assessment"].values()) == {
        "STILL_REQUIRES_PREDECLARATION"}


def test_validator_and_review_do_not_import_execution_runner_or_traci():
    sources = "\n".join(Path(path).read_text(encoding="utf-8") for path in (
        "negotiation_training/extended_evidence_review.py",
        "scripts/validation/validate_mappo_extended_evidence_review.py"))
    assert "ExtendedMAPLearningCurveRunner" not in sources
    assert "MechanicalMAPPOTrainer" not in sources
    assert "CoupledNegotiationTrainingEnvironment" not in sources
    assert "traci" not in sources.lower()
    assert "optimizer.step" not in sources
    assert ".backward(" not in sources


def test_next_checkpoint_is_protocol_not_more_training(review):
    assert review["next_checkpoint"] == \
        "STEP_5J_3C_2D_PREDECLARED_SELECTION_PROTOCOL"
    assert review["next_checkpoint_reason"] == \
        "PREDECLARE_AND_FREEZE_SELECTION_AND_TERMINATION_RULES_BEFORE_ACQUIRING_MORE_EVIDENCE"
