import json
from dataclasses import FrozenInstanceError

import pytest

from negotiation_training.selection_protocol import (
    build_mappo_selection_protocol, load_and_validate_source_review)


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    return build_mappo_selection_protocol(
        output_path=tmp_path_factory.mktemp("protocol") / "protocol.json")


def test_source_review_identity_and_six_blockers():
    source = load_and_validate_source_review()
    assert source["checkpoint"] == "STEP_5J_3C_2C"
    assert source["status"] == "EXTENDED_EVIDENCE_REVIEW_COMPLETE"
    assert len(source["methodological_blockers"]) == 6
    assert set(source["methodological_blocker_assessment"].values()) == {
        "STILL_REQUIRES_PREDECLARATION"}


def test_protocol_hash_is_deterministic(tmp_path):
    first, _ = build_mappo_selection_protocol(output_path=tmp_path / "a.json")
    second, _ = build_mappo_selection_protocol(output_path=tmp_path / "b.json")
    assert first.protocol_id == second.protocol_id
    assert first.protocol_id[0] == "MAPPO_SELECTION_PROTOCOL_V1"


def test_protocol_and_nested_mappings_are_immutable(built):
    protocol, _ = built
    with pytest.raises(FrozenInstanceError):
        protocol.freeze_status = "CHANGED"
    with pytest.raises(TypeError):
        protocol.primary_metric["direction"] = "HIGHER_IS_BETTER"
    with pytest.raises(TypeError):
        protocol.training_budget_protocol["mapping_to_H"]["x"] = "y"


def test_primary_metric_and_hard_validity_are_preserved(built):
    protocol, _ = built
    assert protocol.primary_metric["metric_id"] == "TOTAL_TEAM_TRAVEL_TIME_SECONDS"
    assert protocol.primary_metric["direction"] == "LOWER_IS_BETTER"
    assert protocol.primary_metric["weighted_performance_score"] is False
    assert "ZERO_COLLISIONS" in protocol.hard_validity_gates
    assert "ZERO_BLOCKED_ZONE_VIOLATIONS" in protocol.hard_validity_gates
    assert "TRAFFIC_RULE_HARD_CONSTRAINTS_PRESERVED" in protocol.hard_validity_gates


def test_fixed_resource_horizon_has_no_adaptive_threshold_or_final_H(built):
    protocol, artifact = built
    budget = protocol.training_budget_protocol
    assert budget["architecture"] == \
        "FIXED_RESOURCE_HORIZON_WITH_VALIDATION_CHECKPOINT_SELECTION"
    assert budget["maximum_update_horizon_H"] == "UNRESOLVED_EXTERNAL_INPUT"
    assert budget["adaptive_curve_inspection_stopping"] is False
    assert budget["convergence_threshold"] == "NONE"
    assert artifact["training_horizon_selected"] is False


def test_canonical_replication_stream_and_no_final_n(built):
    protocol, artifact = built
    replication = protocol.replication_protocol
    assert replication["stream"] == "CANONICAL_DETERMINISTIC_REPLICATION_STREAM"
    assert replication["indices"] == "0_THROUGH_N_MINUS_1_NO_SKIPPING"
    assert replication["performance_seed_replacement"] == "FORBIDDEN"
    assert replication["bad_seed_reruns"] == "FORBIDDEN"
    assert replication["final_replication_count_n"] == \
        "NOT_CALCULABLE_INPUTS_INCOMPLETE"
    assert artifact["replication_count_selected"] is False


def test_resource_mpid_confidence_and_power_are_external(built):
    protocol, artifact = built
    requirements = {item.input_name: item
                    for item in protocol.unresolved_external_inputs}
    assert "MAXIMUM_ACCEPTABLE_TRAINING_RESOURCE_BUDGET" in requirements
    assert "MINIMUM_PRACTICALLY_IMPORTANT_DIFFERENCE_TEAM_TRAVEL_TIME_SECONDS" in requirements
    assert "STATISTICAL_CONFIDENCE_OR_PRECISION_TARGET" in requirements
    assert "STATISTICAL_POWER_TARGET" in requirements
    assert all(item.cannot_be_derived_from_existing_results
               for item in requirements.values())
    assert artifact["confidence_level_silently_assumed"] is False
    assert artifact["power_silently_assumed"] is False
    assert artifact["mpid_silently_invented"] is False
    assert artifact["resource_budget_silently_invented"] is False


def test_candidate_comparison_is_matched_paired_validation(built):
    protocol, _ = built
    comparison = protocol.candidate_comparison_protocol
    assert comparison["design"] == "MATCHED_PAIRED_VALIDATION_COMPARISON"
    assert comparison["paired_quantity"] == "D_i_EQUALS_C_A_i_MINUS_C_B_i"
    assert comparison["primary_statistic"] == \
        "PAIRED_EMPIRICAL_MEAN_DIFFERENCE_TTT"
    assert comparison["point_estimate_ranking_alone_sufficient"] is False


def test_uncertainty_preserves_independent_units_and_no_defaults(built):
    protocol, _ = built
    uncertainty = protocol.uncertainty_reporting_protocol
    assert uncertainty["primary_method"] == "PAIRED_BOOTSTRAP_CONFIDENCE_INTERVAL"
    assert uncertainty["bootstrap_time_steps"] is False
    assert uncertainty["bootstrap_policy_factors"] is False
    assert uncertainty["confidence_level"] == "REQUIRES_PREDECLARATION"
    assert uncertainty["bootstrap_resample_count"] == "REQUIRES_PREDECLARATION"


def test_checkpoint_selection_is_validation_only_and_not_retrospective(built):
    protocol, artifact = built
    checkpoint = protocol.checkpoint_selection_protocol
    assert checkpoint["training_performance_used_for_selection"] is False
    assert checkpoint["selection_data_role"] == "VALIDATION_ONLY"
    assert checkpoint["current_state_2_retrospectively_selected"] is False
    assert checkpoint["existing_resume_checkpoints_selection_eligible"] is False
    assert artifact["checkpoint_selected"] is False


def test_held_out_is_excluded_from_selection_and_final_only(built):
    protocol, _ = built
    roles = protocol.data_role_protocol
    assert roles["HELD_OUT_TEST"] == "FINAL_CONFIGURATION_EVALUATION_ONLY"
    assert roles["held_out_for_checkpoint_selection"] is False
    assert roles["held_out_for_training_budget_selection"] is False
    assert roles["held_out_for_hyperparameter_or_architecture_selection"] is False
    assert roles["held_out_for_tie_resolution"] is False
    assert roles["adaptive_decisions_after_held_out"] is False


def test_tie_rules_are_earliest_and_reference_preserving(built):
    protocol, _ = built
    ties = protocol.tie_protocol
    assert ties["checkpoint"] == "EARLIEST_EQUIVALENT_CHECKPOINT_RULE"
    assert ties["candidate_pair"] == "REFERENCE_PRESERVING_TIE_RULE"
    assert ties["sample_until_one_wins"] is False
    assert ties["multi_candidate_reference_not_in_tied_set"] == \
        "UNRESOLVED_MULTI_CANDIDATE_TIE"


def test_current_results_did_not_optimize_rules_or_select_candidate(built):
    protocol, artifact = built
    assert protocol.provenance[
        "current_results_used_to_optimize_selection_rules"] is False
    assert protocol.provenance["state_2_selected"] is False
    assert protocol.provenance["replication_count_3_selected"] is False
    assert artifact["candidate_selected"] is False


def test_external_inputs_have_deterministic_dependency_order(built):
    protocol, artifact = built
    names = [item.input_name for item in protocol.unresolved_external_inputs]
    assert names[:4] == [
        "MAXIMUM_ACCEPTABLE_TRAINING_RESOURCE_BUDGET",
        "MINIMUM_PRACTICALLY_IMPORTANT_DIFFERENCE_TEAM_TRAVEL_TIME_SECONDS",
        "STATISTICAL_CONFIDENCE_OR_PRECISION_TARGET",
        "STATISTICAL_POWER_TARGET"]
    assert artifact["next_blocker"] == names[0]


def test_analysis_only_execution_boundaries(built):
    _, artifact = built
    assert artifact["new_sumo_executions"] == 0
    assert artifact["training_episodes"] == 0
    assert artifact["optimizer_invocations"] == 0
    assert artifact["backward_calls"] == 0
    assert artifact["parameter_updates"] == 0
    assert artifact["validation_executions"] == 0
    assert artifact["held_out_executions"] == 0


def test_protocol_requires_external_inputs_before_evidence(built):
    protocol, artifact = built
    assert artifact["status"] == \
        "PREDECLARED_SELECTION_PROTOCOL_STRUCTURE_COMPLETE"
    assert artifact["protocol_readiness"] == \
        "STRUCTURE_DEFINED_EXTERNAL_INPUTS_REQUIRED"
    assert protocol.extension_protocol["additional_evidence_before_final_protocol"] is False


def test_protocol_module_has_no_training_or_sumo_execution_code():
    source = open("negotiation_training/selection_protocol.py",
                  encoding="utf-8").read().lower()
    assert "traci" not in source
    assert "extendedmappolearningcurverunner" not in source
    assert "mechanicalmappotrainer" not in source
    assert "optimizer.step" not in source
    assert ".backward(" not in source
