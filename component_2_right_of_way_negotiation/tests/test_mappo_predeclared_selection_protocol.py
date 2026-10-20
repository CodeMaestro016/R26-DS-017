# Import json for use in this module.
import json
# Import FrozenInstanceError from dataclasses for the operations below.
from dataclasses import FrozenInstanceError

# Import pytest for use in this module.
import pytest

# Import build_mappo_selection_protocol, load_and_validate_source_review from
# negotiation_training.selection_protocol for the operations below.
from negotiation_training.selection_protocol import (
    build_mappo_selection_protocol, load_and_validate_source_review)


# Apply pytest.fixture(scope='module') as a decorator to configure the following definition.
@pytest.fixture(scope="module")
# Built using the inputs and processing steps below.
# Input tmp_path_factory: the supplied tmp path factory.
# Output: the result of build_mappo_selection_protocol().
def built(tmp_path_factory):
    # Return the result of build_mappo_selection_protocol() to the caller.
    return build_mappo_selection_protocol(
        # Supply output_path as the result of tmp_path_factory.mktemp(the text 'protocol') joined with the path segment
        # 'protocol.json'.
        output_path=tmp_path_factory.mktemp("protocol") / "protocol.json")


# Check source review identity and six blockers using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_source_review_identity_and_six_blockers():
    # Set source to the result of load_and_validate_source_review().
    source = load_and_validate_source_review()
    # Require source at 'checkpoint' equals the text 'STEP_5J_3C_2C'; otherwise raise AssertionError.
    assert source["checkpoint"] == "STEP_5J_3C_2C"
    # Require source at 'status' equals the text 'EXTENDED_EVIDENCE_REVIEW_COMPLETE'; otherwise raise
    # AssertionError.
    assert source["status"] == "EXTENDED_EVIDENCE_REVIEW_COMPLETE"
    # Require the number of entries in source at 'methodological_blockers' equals 6; otherwise raise
    # AssertionError.
    assert len(source["methodological_blockers"]) == 6
    # Require a set built from values from source['methodological_blocker_assessment'] equals a set containing the
    # text 'STILL_REQUIRES_PREDECLARATION'; otherwise raise AssertionError.
    assert set(source["methodological_blocker_assessment"].values()) == {
        "STILL_REQUIRES_PREDECLARATION"}


# Check protocol hash is deterministic using the setup, calls, and assertions below.
# Input tmp_path: the supplied tmp path.
# Output: no explicit value; normal completion returns None.
def test_protocol_hash_is_deterministic(tmp_path):
    # Set (first, _) to the result of build_mappo_selection_protocol().
    first, _ = build_mappo_selection_protocol(output_path=tmp_path / "a.json")
    # Set (second, _) to the result of build_mappo_selection_protocol().
    second, _ = build_mappo_selection_protocol(output_path=tmp_path / "b.json")
    # Require first.protocol_id equals second.protocol_id; otherwise raise AssertionError.
    assert first.protocol_id == second.protocol_id
    # Require first.protocol_id at 0 equals the text 'MAPPO_SELECTION_PROTOCOL_V1'; otherwise raise
    # AssertionError.
    assert first.protocol_id[0] == "MAPPO_SELECTION_PROTOCOL_V1"


# Check protocol and nested mappings are immutable using the setup, calls, and assertions below.
# Input built: the supplied built.
# Output: no explicit value; normal completion returns None.
def test_protocol_and_nested_mappings_are_immutable(built):
    # Set (protocol, _) to built.
    protocol, _ = built
    # Enter the result of pytest.raises(FrozenInstanceError) and run the enclosed operations within that context.
    with pytest.raises(FrozenInstanceError):
        # Set protocol.freeze_status to the text 'CHANGED'.
        protocol.freeze_status = "CHANGED"
    # Enter the result of pytest.raises(TypeError) and run the enclosed operations within that context.
    with pytest.raises(TypeError):
        # Set protocol.primary_metric['direction'] to the text 'HIGHER_IS_BETTER'.
        protocol.primary_metric["direction"] = "HIGHER_IS_BETTER"
    # Enter the result of pytest.raises(TypeError) and run the enclosed operations within that context.
    with pytest.raises(TypeError):
        # Set protocol.training_budget_protocol['mapping_to_H']['x'] to the text 'y'.
        protocol.training_budget_protocol["mapping_to_H"]["x"] = "y"


# Check primary metric and hard validity are preserved using the setup, calls, and assertions below.
# Input built: the supplied built.
# Output: no explicit value; normal completion returns None.
def test_primary_metric_and_hard_validity_are_preserved(built):
    # Set (protocol, _) to built.
    protocol, _ = built
    # Require protocol.primary_metric at 'metric_id' equals the text 'TOTAL_TEAM_TRAVEL_TIME_SECONDS'; otherwise
    # raise AssertionError.
    assert protocol.primary_metric["metric_id"] == "TOTAL_TEAM_TRAVEL_TIME_SECONDS"
    # Require protocol.primary_metric at 'direction' equals the text 'LOWER_IS_BETTER'; otherwise raise
    # AssertionError.
    assert protocol.primary_metric["direction"] == "LOWER_IS_BETTER"
    # Require protocol.primary_metric at 'weighted_performance_score' is the same object as False; otherwise raise
    # AssertionError.
    assert protocol.primary_metric["weighted_performance_score"] is False
    # Require the text 'ZERO_COLLISIONS' belongs to protocol.hard_validity_gates; otherwise raise AssertionError.
    assert "ZERO_COLLISIONS" in protocol.hard_validity_gates
    # Require the text 'ZERO_BLOCKED_ZONE_VIOLATIONS' belongs to protocol.hard_validity_gates; otherwise raise
    # AssertionError.
    assert "ZERO_BLOCKED_ZONE_VIOLATIONS" in protocol.hard_validity_gates
    # Require the text 'TRAFFIC_RULE_HARD_CONSTRAINTS_PRESERVED' belongs to protocol.hard_validity_gates;
    # otherwise raise AssertionError.
    assert "TRAFFIC_RULE_HARD_CONSTRAINTS_PRESERVED" in protocol.hard_validity_gates


# Check fixed resource horizon has no adaptive threshold or final H using the setup, calls, and assertions below.
# Input built: the supplied built.
# Output: no explicit value; normal completion returns None.
def test_fixed_resource_horizon_has_no_adaptive_threshold_or_final_H(built):
    # Set (protocol, artifact) to built.
    protocol, artifact = built
    # Set budget to protocol.training_budget_protocol.
    budget = protocol.training_budget_protocol
    # Require budget at 'architecture' equals the text
    # 'FIXED_RESOURCE_HORIZON_WITH_VALIDATION_CHECKPOINT_SELECTION'; otherwise raise AssertionError.
    assert budget["architecture"] == \
        "FIXED_RESOURCE_HORIZON_WITH_VALIDATION_CHECKPOINT_SELECTION"
    # Require budget at 'maximum_update_horizon_H' equals the text 'UNRESOLVED_EXTERNAL_INPUT'; otherwise raise
    # AssertionError.
    assert budget["maximum_update_horizon_H"] == "UNRESOLVED_EXTERNAL_INPUT"
    # Require budget at 'adaptive_curve_inspection_stopping' is the same object as False; otherwise raise
    # AssertionError.
    assert budget["adaptive_curve_inspection_stopping"] is False
    # Require budget at 'convergence_threshold' equals the text 'NONE'; otherwise raise AssertionError.
    assert budget["convergence_threshold"] == "NONE"
    # Require artifact at 'training_horizon_selected' is the same object as False; otherwise raise AssertionError.
    assert artifact["training_horizon_selected"] is False


# Check canonical replication stream and no final n using the setup, calls, and assertions below.
# Input built: the supplied built.
# Output: no explicit value; normal completion returns None.
def test_canonical_replication_stream_and_no_final_n(built):
    # Set (protocol, artifact) to built.
    protocol, artifact = built
    # Set replication to protocol.replication_protocol.
    replication = protocol.replication_protocol
    # Require replication at 'stream' equals the text 'CANONICAL_DETERMINISTIC_REPLICATION_STREAM'; otherwise
    # raise AssertionError.
    assert replication["stream"] == "CANONICAL_DETERMINISTIC_REPLICATION_STREAM"
    # Require replication at 'indices' equals the text '0_THROUGH_N_MINUS_1_NO_SKIPPING'; otherwise raise
    # AssertionError.
    assert replication["indices"] == "0_THROUGH_N_MINUS_1_NO_SKIPPING"
    # Require replication at 'performance_seed_replacement' equals the text 'FORBIDDEN'; otherwise raise
    # AssertionError.
    assert replication["performance_seed_replacement"] == "FORBIDDEN"
    # Require replication at 'bad_seed_reruns' equals the text 'FORBIDDEN'; otherwise raise AssertionError.
    assert replication["bad_seed_reruns"] == "FORBIDDEN"
    # Require replication at 'final_replication_count_n' equals the text 'NOT_CALCULABLE_INPUTS_INCOMPLETE';
    # otherwise raise AssertionError.
    assert replication["final_replication_count_n"] == \
        "NOT_CALCULABLE_INPUTS_INCOMPLETE"
    # Require artifact at 'replication_count_selected' is the same object as False; otherwise raise
    # AssertionError.
    assert artifact["replication_count_selected"] is False


# Check resource mpid confidence and power are external using the setup, calls, and assertions below.
# Input built: the supplied built.
# Output: no explicit value; normal completion returns None.
def test_resource_mpid_confidence_and_power_are_external(built):
    # Set (protocol, artifact) to built.
    protocol, artifact = built
    # Set requirements to a dictionary of item.input_name mapped to item for item in
    # protocol.unresolved_external_inputs.
    requirements = {item.input_name: item
                    # Evaluate protocol.unresolved_external_inputs as part of the enclosing expression.
                    for item in protocol.unresolved_external_inputs}
    # Require the text 'MAXIMUM_ACCEPTABLE_TRAINING_RESOURCE_BUDGET' belongs to requirements; otherwise raise
    # AssertionError.
    assert "MAXIMUM_ACCEPTABLE_TRAINING_RESOURCE_BUDGET" in requirements
    # Require the text 'MINIMUM_PRACTICALLY_IMPORTANT_DIFFERENCE_TEAM_TRAVEL_TIME_SECONDS' belongs to
    # requirements; otherwise raise AssertionError.
    assert "MINIMUM_PRACTICALLY_IMPORTANT_DIFFERENCE_TEAM_TRAVEL_TIME_SECONDS" in requirements
    # Require the text 'STATISTICAL_CONFIDENCE_OR_PRECISION_TARGET' belongs to requirements; otherwise raise
    # AssertionError.
    assert "STATISTICAL_CONFIDENCE_OR_PRECISION_TARGET" in requirements
    # Require the text 'STATISTICAL_POWER_TARGET' belongs to requirements; otherwise raise AssertionError.
    assert "STATISTICAL_POWER_TARGET" in requirements
    # Require whether every item is true in a lazy sequence of item.cannot_be_derived_from_existing_results for
    # item in values from requirements; otherwise raise AssertionError.
    assert all(item.cannot_be_derived_from_existing_results
               # Evaluate values from requirements as part of the enclosing expression.
               for item in requirements.values())
    # Require artifact at 'confidence_level_silently_assumed' is the same object as False; otherwise raise
    # AssertionError.
    assert artifact["confidence_level_silently_assumed"] is False
    # Require artifact at 'power_silently_assumed' is the same object as False; otherwise raise AssertionError.
    assert artifact["power_silently_assumed"] is False
    # Require artifact at 'mpid_silently_invented' is the same object as False; otherwise raise AssertionError.
    assert artifact["mpid_silently_invented"] is False
    # Require artifact at 'resource_budget_silently_invented' is the same object as False; otherwise raise
    # AssertionError.
    assert artifact["resource_budget_silently_invented"] is False


# Check candidate comparison is matched paired validation using the setup, calls, and assertions below.
# Input built: the supplied built.
# Output: no explicit value; normal completion returns None.
def test_candidate_comparison_is_matched_paired_validation(built):
    # Set (protocol, _) to built.
    protocol, _ = built
    # Set comparison to protocol.candidate_comparison_protocol.
    comparison = protocol.candidate_comparison_protocol
    # Require comparison at 'design' equals the text 'MATCHED_PAIRED_VALIDATION_COMPARISON'; otherwise raise
    # AssertionError.
    assert comparison["design"] == "MATCHED_PAIRED_VALIDATION_COMPARISON"
    # Require comparison at 'paired_quantity' equals the text 'D_i_EQUALS_C_A_i_MINUS_C_B_i'; otherwise raise
    # AssertionError.
    assert comparison["paired_quantity"] == "D_i_EQUALS_C_A_i_MINUS_C_B_i"
    # Require comparison at 'primary_statistic' equals the text 'PAIRED_EMPIRICAL_MEAN_DIFFERENCE_TTT'; otherwise
    # raise AssertionError.
    assert comparison["primary_statistic"] == \
        "PAIRED_EMPIRICAL_MEAN_DIFFERENCE_TTT"
    # Require comparison at 'point_estimate_ranking_alone_sufficient' is the same object as False; otherwise raise
    # AssertionError.
    assert comparison["point_estimate_ranking_alone_sufficient"] is False


# Check uncertainty preserves independent units and no defaults using the setup, calls, and assertions below.
# Input built: the supplied built.
# Output: no explicit value; normal completion returns None.
def test_uncertainty_preserves_independent_units_and_no_defaults(built):
    # Set (protocol, _) to built.
    protocol, _ = built
    # Set uncertainty to protocol.uncertainty_reporting_protocol.
    uncertainty = protocol.uncertainty_reporting_protocol
    # Require uncertainty at 'primary_method' equals the text 'PAIRED_BOOTSTRAP_CONFIDENCE_INTERVAL'; otherwise
    # raise AssertionError.
    assert uncertainty["primary_method"] == "PAIRED_BOOTSTRAP_CONFIDENCE_INTERVAL"
    # Require uncertainty at 'bootstrap_time_steps' is the same object as False; otherwise raise AssertionError.
    assert uncertainty["bootstrap_time_steps"] is False
    # Require uncertainty at 'bootstrap_policy_factors' is the same object as False; otherwise raise
    # AssertionError.
    assert uncertainty["bootstrap_policy_factors"] is False
    # Require uncertainty at 'confidence_level' equals the text 'REQUIRES_PREDECLARATION'; otherwise raise
    # AssertionError.
    assert uncertainty["confidence_level"] == "REQUIRES_PREDECLARATION"
    # Require uncertainty at 'bootstrap_resample_count' equals the text 'REQUIRES_PREDECLARATION'; otherwise raise
    # AssertionError.
    assert uncertainty["bootstrap_resample_count"] == "REQUIRES_PREDECLARATION"


# Check checkpoint selection is validation only and not retrospective using the setup, calls, and assertions
# below.
# Input built: the supplied built.
# Output: no explicit value; normal completion returns None.
def test_checkpoint_selection_is_validation_only_and_not_retrospective(built):
    # Set (protocol, artifact) to built.
    protocol, artifact = built
    # Set checkpoint to protocol.checkpoint_selection_protocol.
    checkpoint = protocol.checkpoint_selection_protocol
    # Require checkpoint at 'training_performance_used_for_selection' is the same object as False; otherwise raise
    # AssertionError.
    assert checkpoint["training_performance_used_for_selection"] is False
    # Require checkpoint at 'selection_data_role' equals the text 'VALIDATION_ONLY'; otherwise raise
    # AssertionError.
    assert checkpoint["selection_data_role"] == "VALIDATION_ONLY"
    # Require checkpoint at 'current_state_2_retrospectively_selected' is the same object as False; otherwise
    # raise AssertionError.
    assert checkpoint["current_state_2_retrospectively_selected"] is False
    # Require checkpoint at 'existing_resume_checkpoints_selection_eligible' is the same object as False;
    # otherwise raise AssertionError.
    assert checkpoint["existing_resume_checkpoints_selection_eligible"] is False
    # Require artifact at 'checkpoint_selected' is the same object as False; otherwise raise AssertionError.
    assert artifact["checkpoint_selected"] is False


# Check held out is excluded from selection and final only using the setup, calls, and assertions below.
# Input built: the supplied built.
# Output: no explicit value; normal completion returns None.
def test_held_out_is_excluded_from_selection_and_final_only(built):
    # Set (protocol, _) to built.
    protocol, _ = built
    # Set roles to protocol.data_role_protocol.
    roles = protocol.data_role_protocol
    # Require roles at 'HELD_OUT_TEST' equals the text 'FINAL_CONFIGURATION_EVALUATION_ONLY'; otherwise raise
    # AssertionError.
    assert roles["HELD_OUT_TEST"] == "FINAL_CONFIGURATION_EVALUATION_ONLY"
    # Require roles at 'held_out_for_checkpoint_selection' is the same object as False; otherwise raise
    # AssertionError.
    assert roles["held_out_for_checkpoint_selection"] is False
    # Require roles at 'held_out_for_training_budget_selection' is the same object as False; otherwise raise
    # AssertionError.
    assert roles["held_out_for_training_budget_selection"] is False
    # Require roles at 'held_out_for_hyperparameter_or_architecture_selection' is the same object as False;
    # otherwise raise AssertionError.
    assert roles["held_out_for_hyperparameter_or_architecture_selection"] is False
    # Require roles at 'held_out_for_tie_resolution' is the same object as False; otherwise raise AssertionError.
    assert roles["held_out_for_tie_resolution"] is False
    # Require roles at 'adaptive_decisions_after_held_out' is the same object as False; otherwise raise
    # AssertionError.
    assert roles["adaptive_decisions_after_held_out"] is False


# Check tie rules are earliest and reference preserving using the setup, calls, and assertions below.
# Input built: the supplied built.
# Output: no explicit value; normal completion returns None.
def test_tie_rules_are_earliest_and_reference_preserving(built):
    # Set (protocol, _) to built.
    protocol, _ = built
    # Set ties to protocol.tie_protocol.
    ties = protocol.tie_protocol
    # Require ties at 'checkpoint' equals the text 'EARLIEST_EQUIVALENT_CHECKPOINT_RULE'; otherwise raise
    # AssertionError.
    assert ties["checkpoint"] == "EARLIEST_EQUIVALENT_CHECKPOINT_RULE"
    # Require ties at 'candidate_pair' equals the text 'REFERENCE_PRESERVING_TIE_RULE'; otherwise raise
    # AssertionError.
    assert ties["candidate_pair"] == "REFERENCE_PRESERVING_TIE_RULE"
    # Require ties at 'sample_until_one_wins' is the same object as False; otherwise raise AssertionError.
    assert ties["sample_until_one_wins"] is False
    # Require ties at 'multi_candidate_reference_not_in_tied_set' equals the text
    # 'UNRESOLVED_MULTI_CANDIDATE_TIE'; otherwise raise AssertionError.
    assert ties["multi_candidate_reference_not_in_tied_set"] == \
        "UNRESOLVED_MULTI_CANDIDATE_TIE"


# Check current results did not optimize rules or select candidate using the setup, calls, and assertions below.
# Input built: the supplied built.
# Output: no explicit value; normal completion returns None.
def test_current_results_did_not_optimize_rules_or_select_candidate(built):
    # Set (protocol, artifact) to built.
    protocol, artifact = built
    # Require protocol.provenance at 'current_results_used_to_optimize_selection_rules' is the same object as
    # False; otherwise raise AssertionError.
    assert protocol.provenance[
        # Supply False to the enclosing expression.
        "current_results_used_to_optimize_selection_rules"] is False
    # Require protocol.provenance at 'state_2_selected' is the same object as False; otherwise raise
    # AssertionError.
    assert protocol.provenance["state_2_selected"] is False
    # Require protocol.provenance at 'replication_count_3_selected' is the same object as False; otherwise raise
    # AssertionError.
    assert protocol.provenance["replication_count_3_selected"] is False
    # Require artifact at 'candidate_selected' is the same object as False; otherwise raise AssertionError.
    assert artifact["candidate_selected"] is False


# Check external inputs have deterministic dependency order using the setup, calls, and assertions below.
# Input built: the supplied built.
# Output: no explicit value; normal completion returns None.
def test_external_inputs_have_deterministic_dependency_order(built):
    # Set (protocol, artifact) to built.
    protocol, artifact = built
    # Set names to a list of item.input_name for item in protocol.unresolved_external_inputs.
    names = [item.input_name for item in protocol.unresolved_external_inputs]
    # Require names sliced by :4 equals a list containing the text 'MAXIMUM_ACCEPTABLE_TRAINING_RESOURCE_BUDGET',
    # the text...; otherwise raise AssertionError.
    assert names[:4] == [
        "MAXIMUM_ACCEPTABLE_TRAINING_RESOURCE_BUDGET",
        "MINIMUM_PRACTICALLY_IMPORTANT_DIFFERENCE_TEAM_TRAVEL_TIME_SECONDS",
        "STATISTICAL_CONFIDENCE_OR_PRECISION_TARGET",
        "STATISTICAL_POWER_TARGET"]
    # Require artifact at 'next_blocker' equals names at 0; otherwise raise AssertionError.
    assert artifact["next_blocker"] == names[0]


# Check analysis only execution boundaries using the setup, calls, and assertions below.
# Input built: the supplied built.
# Output: no explicit value; normal completion returns None.
def test_analysis_only_execution_boundaries(built):
    # Set (_, artifact) to built.
    _, artifact = built
    # Require artifact at 'new_sumo_executions' equals 0; otherwise raise AssertionError.
    assert artifact["new_sumo_executions"] == 0
    # Require artifact at 'training_episodes' equals 0; otherwise raise AssertionError.
    assert artifact["training_episodes"] == 0
    # Require artifact at 'optimizer_invocations' equals 0; otherwise raise AssertionError.
    assert artifact["optimizer_invocations"] == 0
    # Require artifact at 'backward_calls' equals 0; otherwise raise AssertionError.
    assert artifact["backward_calls"] == 0
    # Require artifact at 'parameter_updates' equals 0; otherwise raise AssertionError.
    assert artifact["parameter_updates"] == 0
    # Require artifact at 'validation_executions' equals 0; otherwise raise AssertionError.
    assert artifact["validation_executions"] == 0
    # Require artifact at 'held_out_executions' equals 0; otherwise raise AssertionError.
    assert artifact["held_out_executions"] == 0


# Check protocol requires external inputs before evidence using the setup, calls, and assertions below.
# Input built: the supplied built.
# Output: no explicit value; normal completion returns None.
def test_protocol_requires_external_inputs_before_evidence(built):
    # Set (protocol, artifact) to built.
    protocol, artifact = built
    # Require artifact at 'status' equals the text 'PREDECLARED_SELECTION_PROTOCOL_STRUCTURE_COMPLETE'; otherwise
    # raise AssertionError.
    assert artifact["status"] == \
        "PREDECLARED_SELECTION_PROTOCOL_STRUCTURE_COMPLETE"
    # Require artifact at 'protocol_readiness' equals the text 'STRUCTURE_DEFINED_EXTERNAL_INPUTS_REQUIRED';
    # otherwise raise AssertionError.
    assert artifact["protocol_readiness"] == \
        "STRUCTURE_DEFINED_EXTERNAL_INPUTS_REQUIRED"
    # Require protocol.extension_protocol at 'additional_evidence_before_final_protocol' is the same object as
    # False; otherwise raise AssertionError.
    assert protocol.extension_protocol["additional_evidence_before_final_protocol"] is False


# Check protocol module has no training or sumo execution code using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_protocol_module_has_no_training_or_sumo_execution_code():
    # Set source to the result of open('negotiation_training/selection_protocol.py',
    # encoding='utf-8').read().lower().
    source = open("negotiation_training/selection_protocol.py",
                  # Supply encoding as the text 'utf-8'.
                  encoding="utf-8").read().lower()
    # Require the text 'traci' does not belong to source; otherwise raise AssertionError.
    assert "traci" not in source
    # Require the text 'extendedmappolearningcurverunner' does not belong to source; otherwise raise
    # AssertionError.
    assert "extendedmappolearningcurverunner" not in source
    # Require the text 'mechanicalmappotrainer' does not belong to source; otherwise raise AssertionError.
    assert "mechanicalmappotrainer" not in source
    # Require the text 'optimizer.step' does not belong to source; otherwise raise AssertionError.
    assert "optimizer.step" not in source
    # Require the text '.backward(' does not belong to source; otherwise raise AssertionError.
    assert ".backward(" not in source
