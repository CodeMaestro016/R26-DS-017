import json
from pathlib import Path

import pytest

from negotiation_training.pilot_evidence_review import (
    build_pilot_evidence_review,
    load_and_validate_pilot_evidence,
)


@pytest.fixture(scope="module")
def review(tmp_path_factory):
    return build_pilot_evidence_review(
        output_path=tmp_path_factory.mktemp("review") / "review.json")


def test_pilot_artifact_identity_validation():
    evidence = load_and_validate_pilot_evidence()
    assert evidence["status"] == "CLOSED_LOOP_PROGRESS_AND_VARIANCE_PROBE_COMPLETE"
    assert evidence["replication_probe_reason"] == "MINIMUM_SAMPLE_VARIANCE_PROBE"


def test_invalid_pilot_identity_is_rejected(tmp_path):
    evidence = load_and_validate_pilot_evidence()
    evidence["status"] = "WRONG"
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(evidence), encoding="utf-8")
    with pytest.raises(ValueError, match="INVALID_PILOT_EVIDENCE_STATUS"):
        load_and_validate_pilot_evidence(path)


def test_two_replications_and_both_effects_are_preserved(review):
    pilot = review["pilot_statistics"]
    assert pilot["replications_observed"] == 2
    assert pilot["replication_indices_preserved"] == [0, 1]
    assert pilot["replications_discarded"] == 0
    assert pilot["delta_values"] == pytest.approx([-150.8, -2939.52])


def test_variance_values_are_preserved_exactly(review):
    pilot = review["pilot_statistics"]
    assert pilot["delta_sample_mean"] == pytest.approx(-1545.16)
    assert pilot["delta_sample_variance_n_minus_1"] == pytest.approx(
        3888479.6192)
    assert pilot["delta_sample_standard_deviation"] == pytest.approx(
        1971.922823613034)


def test_single_update_interval_is_insufficient(review):
    assessment = review["training_budget_sufficiency_assessment"]
    assert assessment["status"] == "INSUFFICIENT_SINGLE_UPDATE_INTERVAL"
    assert assessment["final_training_budget_selected"] is False


def test_two_run_variance_probe_is_insufficient(review):
    assessment = review["replication_sufficiency_assessment"]
    assert assessment["status"] == "INSUFFICIENT_MINIMUM_TWO_RUN_VARIANCE_PROBE"
    assert assessment["final_replication_count_selected"] is False
    assert assessment["observations_called_outliers"] == 0


def test_scenario_count_terminology_and_manifest_reuse(review):
    scenario = review["scenario_design_assessment"]
    assert set(scenario["terminology"]) == {
        "UNIQUE_TRAINING_SCENARIOS", "TRAINING_MANIFEST_PASS",
        "PPO_UPDATE_CYCLE", "TRAINING_EXPOSURE"}
    assert scenario["new_unique_training_scenarios_required_now"] is False
    assert scenario["repeated_training_manifest_exposure_required"] is True
    assert scenario["partitions_modified"] is False


def test_validation_unused_and_held_out_sealed(review):
    assert review["pilot_statistics"]["validation_runs"] == 0
    assert review["pilot_statistics"]["held_out_runs"] == 0
    acquisition = review["extended_evidence_acquisition_design"]
    assert acquisition["held_out_sealed"] is True


def test_no_final_counts_selected(review):
    acquisition = review["extended_evidence_acquisition_design"]
    assert review["final_counts_selected"] is False
    assert acquisition["final_counts_selected"] is False
    assert acquisition["replication_extension_rule"]["termination_count"] == "NOT_YET_SELECTED"
    assert acquisition["training_curve_extension_rule"]["final_update_count"] == "NOT_YET_SELECTED"


def test_canonical_replication_stream_continues_without_skipping(review):
    rule = review["extended_evidence_acquisition_design"]["replication_extension_rule"]
    assert rule["next_index"] == 2
    assert rule["order"] == "2,3,4,..._WITHOUT_SKIPPING"
    assert rule["performance_based_replacement"] is False


def test_no_performance_seed_selection(review):
    acquisition = review["extended_evidence_acquisition_design"]
    assert acquisition["performance_seed_selection_forbidden"] is True


def test_no_arbitrary_convergence_threshold(review):
    rule = review["extended_evidence_acquisition_design"]["training_curve_extension_rule"]
    assert review["arbitrary_convergence_thresholds"] == 0
    assert rule["convergence_rule"] == "STATISTICAL_SELECTION_RULE_REQUIRES_PREDECLARATION"


def test_analysis_performs_no_training_or_parameter_update(review):
    assert review["sumo_invocations"] == 0
    assert review["optimizer_invocations"] == 0
    assert review["backward_calls"] == 0
    assert review["model_parameter_updates"] == 0


def test_review_module_has_no_execution_or_optimizer_imports():
    source = Path("negotiation_training/pilot_evidence_review.py").read_text(
        encoding="utf-8")
    assert "CoupledNegotiationTrainingEnvironment" not in source
    assert "MechanicalMAPPOTrainer" not in source
    assert "torch" not in source
    assert "traci" not in source.lower()


def test_all_methodological_blockers_remain_explicit(review):
    blockers = set(review["remaining_methodological_blockers"])
    assert {
        "TRAINING_BUDGET_SELECTION_CRITERION_REQUIRES_PREDECLARATION",
        "REPLICATION_COUNT_ADEQUACY_CRITERION_REQUIRES_PREDECLARATION",
        "CANDIDATE_COMPARISON_STATISTIC_REQUIRES_PREDECLARATION",
        "TIE_RULE_REQUIRES_PREDECLARATION",
        "CHECKPOINT_MODEL_SELECTION_RULE_REQUIRES_PREDECLARATION",
    } <= blockers
