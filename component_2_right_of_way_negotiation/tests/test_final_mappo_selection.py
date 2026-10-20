"""Scientific-boundary tests for the bounded final MAPPO selection study."""

# Import inspect for use in this module.
import inspect
# Import json for use in this module.
import json
# Import Path from pathlib for the operations below.
from pathlib import Path
# Import SimpleNamespace from types for the operations below.
from types import SimpleNamespace

# Import pytest for use in this module.
import pytest

# Import ScenarioRole, build_design from experimentation for the operations below.
from experimentation import ScenarioRole, build_design
# Import build_mechanical_pilot_architecture_contract from negotiation_training.architecture_contract for the
# operations below.
from negotiation_training.architecture_contract import (
    build_mechanical_pilot_architecture_contract,
)
# Import CANDIDATE_EPOCHS, PROTOCOL_ID, REPLICATION_COUNT, UPDATE_HORIZON,
# DeterministicNoNegotiationRegulatoryBaseline, _baseline_summary, _eligible, _episode_record,... from
# negotiation_training.final_selection for the operations below.
from negotiation_training.final_selection import (
    CANDIDATE_EPOCHS, PROTOCOL_ID, REPLICATION_COUNT, UPDATE_HORIZON,
    DeterministicNoNegotiationRegulatoryBaseline,
    _baseline_summary, _eligible, _episode_record,
    _hard_safety_failure_record, _summary, baseline, report,
    build_protocol, candidate_configurations, candidate_runtime_audit,
    file_sha256, heldout, prepare, select, smoke,
)
# Import CoupledNegotiationTrainingEnvironment from negotiation_training.environment for the operations below.
from negotiation_training.environment import CoupledNegotiationTrainingEnvironment
# Import PhysicalReplayError from negotiation_execution.replay for the operations below.
from negotiation_execution.replay import PhysicalReplayError
# Import build_mechanical_pilot_configuration_audit from negotiation_training.optimizer_contract for the
# operations below.
from negotiation_training.optimizer_contract import (
    build_mechanical_pilot_configuration_audit,
)


# Check candidate set and bounded resource protocol are exact using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_candidate_set_and_bounded_resource_protocol_are_exact():
    # Set protocol to the result of build_protocol().
    protocol = build_protocol()
    # Require CANDIDATE_EPOCHS equals a dictionary containing E5, E10, E15; otherwise raise AssertionError.
    assert CANDIDATE_EPOCHS == {"E5": 5, "E10": 10, "E15": 15}
    # Require protocol at 'candidate_ids' equals a list containing the text 'E5', the text 'E10', the text 'E15';
    # otherwise raise AssertionError.
    assert protocol["candidate_ids"] == ["E5", "E10", "E15"]
    # Require REPLICATION_COUNT equals protocol at 'replication_count_n'; equals 3; otherwise raise
    # AssertionError.
    assert REPLICATION_COUNT == protocol["replication_count_n"] == 3
    # Require UPDATE_HORIZON equals protocol at 'update_horizon_h'; equals 2; otherwise raise AssertionError.
    assert UPDATE_HORIZON == protocol["update_horizon_h"] == 2
    # Require protocol at 'adaptive_early_stopping' is the same object as False; otherwise raise AssertionError.
    assert protocol["adaptive_early_stopping"] is False
    # Require protocol at 'adaptive_horizon_extension' is the same object as False; otherwise raise
    # AssertionError.
    assert protocol["adaptive_horizon_extension"] is False
    # Require protocol at 'bad_seed_replacement' is the same object as False; otherwise raise AssertionError.
    assert protocol["bad_seed_replacement"] is False
    # Require protocol at 'globally_optimal_claim' is the same object as False; otherwise raise AssertionError.
    assert protocol["globally_optimal_claim"] is False


# Check only ppo epochs differ and reference values remain fixed using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def test_only_ppo_epochs_differ_and_reference_values_remain_fixed():
    # Set candidates to the result of candidate_configurations().
    candidates = candidate_configurations()
    # Set differing to a set of key for key in candidates[0].__dict__; retain entries satisfying the number of
    # entries in a set of getattr(x, key) for x in candidates is greater than 1.
    differing = {key for key in candidates[0].__dict__
                 # Evaluate the number of entries in a set of the requested attribute of x for x in candidates is
                 # greater than 1 as part of the enclosing expression.
                 if len({getattr(x, key) for x in candidates}) > 1}
    # Require differing equals a set containing the text 'candidate_id', the text 'ppo_update_epochs'; otherwise
    # raise AssertionError.
    assert differing == {"candidate_id", "ppo_update_epochs"}
    # Iterate over candidates, binding each item to candidate.
    for candidate in candidates:
        # Require candidate.learning_rate equals 0.0005; otherwise raise AssertionError.
        assert candidate.learning_rate == 0.0005
        # Require candidate.ppo_clip_epsilon equals 0.2; otherwise raise AssertionError.
        assert candidate.ppo_clip_epsilon == 0.2
        # Require candidate.gnn_hidden_dimension equals 64; otherwise raise AssertionError.
        assert candidate.gnn_hidden_dimension == 64
        # Require candidate.gnn_training_mode equals the text 'FROZEN_GNN'; otherwise raise AssertionError.
        assert candidate.gnn_training_mode == "FROZEN_GNN"


# Check historical contracts are unchanged by candidate audit using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_historical_contracts_are_unchanged_by_candidate_audit():
    # Set architecture_before to the result of build_mechanical_pilot_architecture_contract().
    architecture_before = build_mechanical_pilot_architecture_contract()
    # Set historical_before to the result of build_mechanical_pilot_configuration_audit().
    historical_before = build_mechanical_pilot_configuration_audit()
    # Set candidate to candidate_configurations() at 2.
    candidate = candidate_configurations()[2]
    # Set audit to the result of candidate_runtime_audit(candidate).
    audit = candidate_runtime_audit(candidate)
    # Set historical_after to the result of build_mechanical_pilot_configuration_audit().
    historical_after = build_mechanical_pilot_configuration_audit()
    # Set architecture_after to the result of build_mechanical_pilot_architecture_contract().
    architecture_after = build_mechanical_pilot_architecture_contract()
    # Require historical_before equals historical_after; otherwise raise AssertionError.
    assert historical_before == historical_after
    # Require architecture_before equals architecture_after; otherwise raise AssertionError.
    assert architecture_before == architecture_after
    # Set historical_epochs to the next item from a lazy sequence of x.value for x in
    # historical_after.runtime_choices; retain entries satisfying x.choice_id equals the text 'ppo_update_epochs'.
    historical_epochs = next(x.value for x in historical_after.runtime_choices
                             # Evaluate x.choice_id equals the text 'ppo_update_epochs' as part of the enclosing
                             # expression.
                             if x.choice_id == "ppo_update_epochs")
    # Set candidate_epochs to the next item from a lazy sequence of x.value for x in audit.runtime_choices; retain
    # entries satisfying x.choice_id equals the text 'ppo_update_epochs'.
    candidate_epochs = next(x.value for x in audit.runtime_choices
                            # Evaluate x.choice_id equals the text 'ppo_update_epochs' as part of the enclosing
                            # expression.
                            if x.choice_id == "ppo_update_epochs")
    # Require historical_epochs equals 5; otherwise raise AssertionError.
    assert historical_epochs == 5
    # Require candidate_epochs equals 15; otherwise raise AssertionError.
    assert candidate_epochs == 15


# Check all candidates share manifests and replication identities using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_all_candidates_share_manifests_and_replication_identities():
    # Set protocol to the result of build_protocol().
    protocol = build_protocol()
    # Require whether every item is true in a lazy sequence of protocol['manifests'][role] at 'scenario_count'
    # equals 36 for role in a tuple containing the text 'TRAINING', the text 'VALIDATION', the text
    # 'HELD_OUT_TEST'; otherwise raise AssertionError.
    assert all(protocol["manifests"][role]["scenario_count"] == 36
               # Evaluate a tuple containing the text 'TRAINING', the text 'VALIDATION', the text 'HELD_OUT_TEST'
               # as part of the enclosing expression.
               for role in ("TRAINING", "VALIDATION", "HELD_OUT_TEST"))
    # Set design to the result of build_design().
    design = build_design()
    # Set sets to a list of a set built from design['manifests'][role].scenario_ids for role in ScenarioRole.
    sets = [set(design["manifests"][role].scenario_ids)
            # Evaluate ScenarioRole as part of the enclosing expression.
            for role in ScenarioRole]
    # Require the negation of whether any item is true in a lazy sequence of sets[i] intersected with sets[j] for
    # i in the integer range defined by 3; otherwise raise AssertionError.
    assert not any(sets[i] & sets[j] for i in range(3) for j in range(i + 1, 3))
    # Require protocol at 'replication_identities' equals a list of a list containing the text
    # 'FINAL_MAPPO_CANONICAL_REPLICATION_V2', i for i in the integer range defined by 3; otherwise raise
    # AssertionError.
    assert protocol["replication_identities"] == [
        # Evaluate a list containing the text 'FINAL_MAPPO_CANONICAL_REPLICATION_V2', i as part of the enclosing
        # expression.
        ["FINAL_MAPPO_CANONICAL_REPLICATION_V2", i] for i in range(3)]


# Check prepare and smoke do not consume held out or create selection using the setup, calls, and assertions
# below.
# Input tmp_path: the supplied tmp path.
# Output: no explicit value; normal completion returns None.
def test_prepare_and_smoke_do_not_consume_held_out_or_create_selection(tmp_path):
    # Set protocol to the result of prepare(tmp_path).
    protocol = prepare(tmp_path)
    # Set result to the result of smoke(tmp_path).
    result = smoke(tmp_path)
    # Require protocol at 'held_out_used_for_selection' is the same object as False; otherwise raise
    # AssertionError.
    assert protocol["held_out_used_for_selection"] is False
    # Require result at 'status' equals the text 'SMOKE_TEST_ONLY'; otherwise raise AssertionError.
    assert result["status"] == "SMOKE_TEST_ONLY"
    # Require result at 'held_out_scenarios_consumed' equals 0; otherwise raise AssertionError.
    assert result["held_out_scenarios_consumed"] == 0
    # Require the negation of whether (tmp_path / 'selected_configuration.json') exists; otherwise raise
    # AssertionError.
    assert not (tmp_path / "selected_configuration.json").exists()
    # Require the negation of whether (tmp_path / 'selected_policy.pt') exists; otherwise raise AssertionError.
    assert not (tmp_path / "selected_policy.pt").exists()


# Validation payload using the inputs and processing steps below.
# Input means: the supplied means.
# Input eligible: the supplied eligible.
# Output: a dictionary containing protocol_id, data_role, held_out_consumed, candidates.
# Processing: iterate over the relevant records.
def _validation_payload(means, eligible):
    # Set candidates to an empty dictionary.
    candidates = {}
    # Iterate over CANDIDATE_EPOCHS, binding each item to key.
    for key in CANDIDATE_EPOCHS:
        # Set candidates[key] to a dictionary containing candidate_id, eligible, hard_gate_result, summary.
        candidates[key] = {"candidate_id": key, "eligible": eligible[key],
            # Store the text 'ELIGIBLE' when eligible at key, otherwise the text 'INELIGIBLE' under
            # 'hard_gate_result'.
            "hard_gate_result": "ELIGIBLE" if eligible[key] else "INELIGIBLE",
            # Store a dictionary containing mean under 'summary'.
            # Store means at key under 'mean'.
            "summary": {"mean": means[key]}}
    # Return a dictionary containing protocol_id, data_role, held_out_consumed, candidates to the caller.
    return {"protocol_id": PROTOCOL_ID, "data_role": "VALIDATION",
            # Store False under 'held_out_consumed'.
            # Store candidates under 'candidates'.
            "held_out_consumed": False, "candidates": candidates}


# Selection fixture using the inputs and processing steps below.
# Input root: the base directory used to resolve files.
# Input means: the supplied means.
# Input eligible: the supplied eligible.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def _selection_fixture(root, means, eligible):
    # Create the directory requested by (root / 'comparison').
    (root / "comparison").mkdir(parents=True)
    # Write the supplied text to (root / 'comparison' / 'candidate_validation_summary.json').
    (root / "comparison" / "candidate_validation_summary.json").write_text(
        # Supply encoding as the text 'utf-8'.
        json.dumps(_validation_payload(means, eligible)), encoding="utf-8")
    # Iterate over CANDIDATE_EPOCHS, binding each item to candidate.
    for candidate in CANDIDATE_EPOCHS:
        # Set directory to root joined with the path segment 'training' divided by candidate.
        directory = root / "training" / candidate
        # Create the directory requested by directory.
        directory.mkdir(parents=True)
        # Iterate over the integer range defined by 3, binding each item to index.
        for index in range(3):
            # Write the supplied bytes to (directory / f'replication_{index}_state_2.pt').
            (directory / f"replication_{index}_state_2.pt").write_bytes(
                # Supply the result of f'{candidate}-{index}'.encode() to (directory /
                # f'replication_{index}_state_2.pt').write_bytes.
                f"{candidate}-{index}".encode())


# Check selection applies hard gates before lower validation ttt using the setup, calls, and assertions below.
# Input tmp_path: the supplied tmp path.
# Output: no explicit value; normal completion returns None.
def test_selection_applies_hard_gates_before_lower_validation_ttt(tmp_path):
    # Call _selection_fixture with the supplied arguments.
    _selection_fixture(tmp_path, {"E5": 100, "E10": 1, "E15": 90},
                       # Store True under 'E5'.
                       # Store False under 'E10'.
                       # Store True under 'E15'.
                       {"E5": True, "E10": False, "E15": True})
    # Set result to the result of select(tmp_path).
    result = select(tmp_path)
    # Require result at 'selected_candidate_id' equals the text 'E15'; otherwise raise AssertionError.
    assert result["selected_candidate_id"] == "E15"
    # Require result at 'selection_data_role' equals the text 'VALIDATION'; otherwise raise AssertionError.
    assert result["selection_data_role"] == "VALIDATION"
    # Require result at 'held_out_used_for_selection' is the same object as False; otherwise raise AssertionError.
    assert result["held_out_used_for_selection"] is False


# Check exact tie retains e5 and selected policy is byte identical using the setup, calls, and assertions below.
# Input tmp_path: the supplied tmp path.
# Output: no explicit value; normal completion returns None.
def test_exact_tie_retains_e5_and_selected_policy_is_byte_identical(tmp_path):
    # Call _selection_fixture with the supplied arguments.
    _selection_fixture(tmp_path, {"E5": 10, "E10": 10, "E15": 20},
                       # Supply a dictionary of key mapped to True for key in CANDIDATE_EPOCHS to
                       # _selection_fixture.
                       {key: True for key in CANDIDATE_EPOCHS})
    # Set result to the result of select(tmp_path).
    result = select(tmp_path)
    # Require result at 'selected_candidate_id' equals the text 'E5'; otherwise raise AssertionError.
    assert result["selected_candidate_id"] == "E5"
    # Set source to tmp_path joined with the path segment 'training' joined with the path segment 'E5' joined with the path segment
    # 'replication_0_state_2.pt'.
    source = tmp_path / "training" / "E5" / "replication_0_state_2.pt"
    # Require the result of file_sha256(tmp_path joined with the path segment 'selected_policy.pt') equals the result of
    # file_sha256(source); otherwise raise AssertionError.
    assert file_sha256(tmp_path / "selected_policy.pt") == file_sha256(source)
    # Require result at 'demo_replication_selected_by_performance' is the same object as False; otherwise raise
    # AssertionError.
    assert result["demo_replication_selected_by_performance"] is False


# Check held out refuses before frozen selection using the setup, calls, and assertions below.
# Input tmp_path: the supplied tmp path.
# Output: no explicit value; normal completion returns None.
def test_held_out_refuses_before_frozen_selection(tmp_path):
    # Enter the result of pytest.raises(RuntimeError) and run the enclosed operations within that context.
    with pytest.raises(RuntimeError, match="HELD_OUT_LOCKED"):
        # Call heldout with the supplied arguments.
        heldout(tmp_path)


# Check baseline is nonlearned nonreward and has no id priority using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_baseline_is_nonlearned_nonreward_and_has_no_id_priority():
    # Set baseline to the result of DeterministicNoNegotiationRegulatoryBaseline().
    baseline = DeterministicNoNegotiationRegulatoryBaseline()
    # Require baseline.neural_actor_calls equals 0; otherwise raise AssertionError.
    assert baseline.neural_actor_calls == 0
    # Require baseline.reward_used_for_selection is the same object as False; otherwise raise AssertionError.
    assert baseline.reward_used_for_selection is False
    # Require baseline.future_outcome_used_for_selection is the same object as False; otherwise raise
    # AssertionError.
    assert baseline.future_outcome_used_for_selection is False
    # Require baseline.vehicle_id_priority_rule is the same object as False; otherwise raise AssertionError.
    assert baseline.vehicle_id_priority_rule is False
    # Set source to the result of inspect.getsource(baseline.select_joint_actions).
    source = inspect.getsource(baseline.select_joint_actions)
    # Require the text 'KEEP_CLAIM' belongs to source; otherwise raise AssertionError.
    assert "KEEP_CLAIM" in source
    # Require the text 'REJECT_RELINQUISHMENT' belongs to source; otherwise raise AssertionError.
    assert "REJECT_RELINQUISHMENT" in source
    # Require the text 'min(' does not belong to source and the text 'sorted(' does not belong to source;
    # otherwise raise AssertionError.
    assert "min(" not in source and "sorted(" not in source


# Check baseline keeps only unique executable no negotiation branch using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_baseline_keeps_only_unique_executable_no_negotiation_branch():
    # Set keep to the result of SimpleNamespace().
    keep = SimpleNamespace(
        # Supply proposer_assignment as the result of SimpleNamespace().
        proposer_assignment=SimpleNamespace(
            # Supply claim_action_assignments as a tuple containing a tuple containing the text 'claim', the text
            # 'KEEP_CLAIM'.
            claim_action_assignments=(("claim", "KEEP_CLAIM"),)),
        # Supply responder_assignment as the result of SimpleNamespace().
        # Supply response_action_assignments as an empty tuple.
        responder_assignment=SimpleNamespace(response_action_assignments=()),
        # Supply graph_executable as True.
        graph_executable=True)
    # Set relinquish to the result of SimpleNamespace().
    relinquish = SimpleNamespace(
        # Supply proposer_assignment as the result of SimpleNamespace().
        proposer_assignment=SimpleNamespace(
            # Supply claim_action_assignments as a tuple containing a tuple containing the text 'claim', the text
            # 'RELINQUISH_CLAIM'.
            claim_action_assignments=(("claim", "RELINQUISH_CLAIM"),)),
        # Supply responder_assignment as the result of SimpleNamespace().
        # Supply response_action_assignments as an empty tuple.
        responder_assignment=SimpleNamespace(response_action_assignments=()),
        # Supply graph_executable as True.
        graph_executable=True)
    # Set baseline to the result of DeterministicNoNegotiationRegulatoryBaseline().
    baseline = DeterministicNoNegotiationRegulatoryBaseline()
    # Require the result of baseline.select_joint_actions(a tuple containing relinquish, keep, an empty tuple) is
    # the same object as keep; otherwise raise AssertionError.
    assert baseline.select_joint_actions((relinquish, keep), ()) is keep
    # Require the result of baseline.select_joint_actions(a tuple containing relinquish, an empty tuple) is the
    # same object as None; otherwise raise AssertionError.
    assert baseline.select_joint_actions((relinquish,), ()) is None


# Check only opted in baseline can finish an observed unresolved context using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_only_opted_in_baseline_can_finish_an_observed_unresolved_context():
    # Set baseline_environment to the result of CoupledNegotiationTrainingEnvironment(the result of
    # DeterministicNoNegotiationRegulatoryBaseline()).
    baseline_environment = CoupledNegotiationTrainingEnvironment(
        # Supply the result of DeterministicNoNegotiationRegulatoryBaseline() to
        # CoupledNegotiationTrainingEnvironment.
        DeterministicNoNegotiationRegulatoryBaseline())
    # Require the result of baseline_environment._terminal_coordination_status(None, True, the text
    # 'NO_EXECUTABLE_KEEP_REGULATORY_BRANCH') equals the text 'UNRESOLVED_COORDINATION_BASELINE'; otherwise raise
    # AssertionError.
    assert baseline_environment._terminal_coordination_status(
        # Supply None to the enclosing expression.
        None, True, "NO_EXECUTABLE_KEEP_REGULATORY_BRANCH") == (
            "UNRESOLVED_COORDINATION_BASELINE")

    # Set ordinary_provider to the result of SimpleNamespace().
    ordinary_provider = SimpleNamespace(selection_rule="STRICT_PROVIDER")
    # Set ordinary_environment to the result of CoupledNegotiationTrainingEnvironment(ordinary_provider).
    ordinary_environment = CoupledNegotiationTrainingEnvironment(
        # Supply ordinary_provider to CoupledNegotiationTrainingEnvironment.
        ordinary_provider)
    # Enter the result of pytest.raises(PhysicalReplayError) and run the enclosed operations within that context.
    with pytest.raises(PhysicalReplayError, match=
                       "SEMANTIC_NEGOTIATION_EVENT_NOT_OBSERVED"):
        # Call ordinary_environment._terminal_coordination_status with the supplied arguments.
        ordinary_environment._terminal_coordination_status(
            # Supply None to the enclosing expression.
            None, True, "NO_EXECUTABLE_KEEP_REGULATORY_BRANCH")
    # Enter the result of pytest.raises(PhysicalReplayError) and run the enclosed operations within that context.
    with pytest.raises(PhysicalReplayError, match=
                       "SEMANTIC_NEGOTIATION_EVENT_NOT_OBSERVED"):
        # Call baseline_environment._terminal_coordination_status with the supplied arguments.
        baseline_environment._terminal_coordination_status(None, False, None)


# Check unresolved episode record is explicit even when all vehicles complete using the setup, calls, and
# assertions below.
# Output: no explicit value; normal completion returns None.
def test_unresolved_episode_record_is_explicit_even_when_all_vehicles_complete():
    # Set episode to the result of SimpleNamespace().
    episode = SimpleNamespace(
        # Supply scenario_id as a tuple containing the text 'HELD_OUT', 1.
        # Supply team_travel_time_seconds as 42.0.
        scenario_id=("HELD_OUT", 1), team_travel_time_seconds=42.0,
        # Supply scheduled_vehicle_count as 2.
        # Supply completed_vehicle_count as 2.
        scheduled_vehicle_count=2, completed_vehicle_count=2,
        # Supply episode_completion_status as the text 'UNRESOLVED_COORDINATION_BASELINE'.
        episode_completion_status="UNRESOLVED_COORDINATION_BASELINE",
        # Supply simulation_duration_seconds as 10.0.
        # Supply collision_count as 0.
        simulation_duration_seconds=10.0, collision_count=0,
        # Supply blocked_zone_entry_violation_count as 0.
        blocked_zone_entry_violation_count=0,
        # Supply native_sumo_safety_intervention_count as 1.
        # Supply joint_decision_batches as an empty tuple.
        native_sumo_safety_intervention_count=1, joint_decision_batches=(),
        # Supply proposer_factor_count as 0.
        # Supply responder_factor_count as 0.
        proposer_factor_count=0, responder_factor_count=0,
        # Store True under 'collision_free'.
        hard_validity_gate_results={"collision_free": True,
                                    # Store True under 'blocked_zone_invariant'.
                                    "blocked_zone_invariant": True},
        # Supply provenance as a dictionary containing unresolved_coordination_reason, neural_actor_calls,
        # fabricated_negotiation_branches,...
        provenance={
            "unresolved_coordination_reason":
                "NO_EXECUTABLE_KEEP_REGULATORY_BRANCH",
            # Store 0 under 'neural_actor_calls'.
            # Store 0 under 'fabricated_negotiation_branches'.
            "neural_actor_calls": 0, "fabricated_negotiation_branches": 0,
            # Store 0 under 'vehicle_id_priority_decisions'.
            "vehicle_id_priority_decisions": 0},
        # Supply sumo_step_count as 100.
        # Supply wall_clock_runtime_seconds as 2.0.
        sumo_step_count=100, wall_clock_runtime_seconds=2.0)
    # Set record to the result of _episode_record(episode, the text 'BASELINE').
    record = _episode_record(episode, "BASELINE")
    # Require record at 'unresolved_coordination_case' is the same object as True; otherwise raise AssertionError.
    assert record["unresolved_coordination_case"] is True
    # Require record at 'unresolved_coordination_reason' equals the text 'NO_EXECUTABLE_KEEP_REGULATORY_BRANCH';
    # otherwise raise AssertionError.
    assert record["unresolved_coordination_reason"] == (
        "NO_EXECUTABLE_KEEP_REGULATORY_BRANCH")
    # Require record at 'learned_proposer_actions' equals 0; otherwise raise AssertionError.
    assert record["learned_proposer_actions"] == 0
    # Require record at 'learned_responder_actions' equals 0; otherwise raise AssertionError.
    assert record["learned_responder_actions"] == 0
    # Require record at 'neural_actor_calls' equals 0; otherwise raise AssertionError.
    assert record["neural_actor_calls"] == 0
    # Require record at 'fabricated_negotiation_branches' equals 0; otherwise raise AssertionError.
    assert record["fabricated_negotiation_branches"] == 0
    # Require record at 'vehicle_id_priority_decisions' equals 0; otherwise raise AssertionError.
    assert record["vehicle_id_priority_decisions"] == 0
    # Require _summary([record]) at 'unresolved_coordination_cases' equals 1; otherwise raise AssertionError.
    assert _summary([record])["unresolved_coordination_cases"] == 1


# Check unresolved status does not relax collision or blocked zone gates using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_unresolved_status_does_not_relax_collision_or_blocked_zone_gates():
    # Set base to a dictionary containing collisions, blocked_zone_violations, hard_mask_violations,...
    base = {"collisions": 0, "blocked_zone_violations": 0,
            # Store 0 under 'hard_mask_violations'.
            # Store 0 under 'regulatory_invariant_violations'.
            "hard_mask_violations": 0, "regulatory_invariant_violations": 0,
            # Store 0 under 'protocol_invariant_failures'.
            "protocol_invariant_failures": 0,
            # Store 0 under 'route_truth_actor_fields_consumed'.
            "route_truth_actor_fields_consumed": 0,
            # Store a dictionary containing collision_free, blocked_zone_invariant under
            # 'hard_validity_gate_results'.
            # Store True under 'collision_free'.
            "hard_validity_gate_results": {"collision_free": True,
                                            # Store True under 'blocked_zone_invariant'.
                                            "blocked_zone_invariant": True},
            # Store 1.0 under 'total_team_travel_time_seconds'.
            "total_team_travel_time_seconds": 1.0}
    # Require the negation of the result of _eligible(a list containing a dictionary containing collisions);
    # otherwise raise AssertionError.
    assert not _eligible([{**base, "collisions": 1}])
    # Require the negation of the result of _eligible(a list containing a dictionary containing
    # blocked_zone_violations); otherwise raise AssertionError.
    assert not _eligible([{**base, "blocked_zone_violations": 1}])
    # Set source to the result of inspect.getsource(CoupledNegotiationTrainingEnvironment.run_episode).
    source = inspect.getsource(CoupledNegotiationTrainingEnvironment.run_episode)
    # Require the text 'PHYSICAL_CAUSAL_BRANCH_COLLISION_OBSERVED' belongs to source; otherwise raise
    # AssertionError.
    assert "PHYSICAL_CAUSAL_BRANCH_COLLISION_OBSERVED" in source


# Check blocked zone exception becomes factual failed baseline record only using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_blocked_zone_exception_becomes_factual_failed_baseline_record_only():
    # Set error to the result of PhysicalReplayError(the text 'BLOCKED_VEHICLE_ENTERED_CONFLICT_ZONE', a tuple
    # containing the text 'SCENARIO_AV_2',...).
    error = PhysicalReplayError(
        "BLOCKED_VEHICLE_ENTERED_CONFLICT_ZONE",
        # Supply a tuple containing the text 'SCENARIO_AV_2', the text 'CZ_7', 23.32 to PhysicalReplayError.
        ("SCENARIO_AV_2", "CZ_7", 23.32))
    # Set record to the result of _hard_safety_failure_record(a tuple containing the text 'HELD_OUT', 4, error).
    record = _hard_safety_failure_record(("HELD_OUT", 4), error)
    # Require record at 'status' equals the text 'HARD_SAFETY_FAILURE'; otherwise raise AssertionError.
    assert record["status"] == "HARD_SAFETY_FAILURE"
    # Require record at 'hard_validity_eligible' is the same object as False; otherwise raise AssertionError.
    assert record["hard_validity_eligible"] is False
    # Require record at 'safety_failure_type' equals the text 'BLOCKED_VEHICLE_ENTERED_CONFLICT_ZONE'; otherwise
    # raise AssertionError.
    assert record["safety_failure_type"] == (
        "BLOCKED_VEHICLE_ENTERED_CONFLICT_ZONE")
    # Require record at 'total_team_travel_time_seconds' is the same object as None; otherwise raise
    # AssertionError.
    assert record["total_team_travel_time_seconds"] is None
    # Require record at 'safety_failure_provenance' equals a dictionary containing exception_type,
    # failure_message, raw_evidence, vehicle_id, conflict_zone_id,...; otherwise raise AssertionError.
    assert record["safety_failure_provenance"] == {
        "exception_type": "PhysicalReplayError",
        "failure_message": "BLOCKED_VEHICLE_ENTERED_CONFLICT_ZONE",
        # Store a list containing the text 'SCENARIO_AV_2', the text 'CZ_7', 23.32 under 'raw_evidence'.
        "raw_evidence": ["SCENARIO_AV_2", "CZ_7", 23.32],
        "vehicle_id": "SCENARIO_AV_2", "conflict_zone_id": "CZ_7",
        # Store 23.32 under 'simulation_time'.
        "simulation_time": 23.32}


# Successful baseline episode using the inputs and processing steps below.
# Input scenario_id: the supplied scenario id.
# Output: the result of SimpleNamespace().
def _successful_baseline_episode(scenario_id):
    # Return the result of SimpleNamespace() to the caller.
    return SimpleNamespace(
        # Supply scenario_id as scenario_id.
        # Supply team_travel_time_seconds as 20.0.
        scenario_id=scenario_id, team_travel_time_seconds=20.0,
        # Supply scheduled_vehicle_count as 2.
        # Supply completed_vehicle_count as 2.
        scheduled_vehicle_count=2, completed_vehicle_count=2,
        # Supply episode_completion_status as the text 'COMPLETE'.
        episode_completion_status="COMPLETE",
        # Supply simulation_duration_seconds as 10.0.
        # Supply collision_count as 0.
        simulation_duration_seconds=10.0, collision_count=0,
        # Supply blocked_zone_entry_violation_count as 0.
        blocked_zone_entry_violation_count=0,
        # Supply native_sumo_safety_intervention_count as 2.
        # Supply joint_decision_batches as an empty tuple.
        native_sumo_safety_intervention_count=2, joint_decision_batches=(),
        # Supply proposer_factor_count as 0.
        # Supply responder_factor_count as 0.
        proposer_factor_count=0, responder_factor_count=0,
        # Store True under 'collision_free'.
        hard_validity_gate_results={"collision_free": True,
                                    # Store True under 'blocked_zone_invariant'.
                                    "blocked_zone_invariant": True},
        # Store None under 'unresolved_coordination_reason'.
        provenance={"unresolved_coordination_reason": None,
                    # Store 0 under 'neural_actor_calls'.
                    "neural_actor_calls": 0,
                    # Store 0 under 'fabricated_negotiation_branches'.
                    "fabricated_negotiation_branches": 0,
                    # Store 0 under 'vehicle_id_priority_decisions'.
                    "vehicle_id_priority_decisions": 0},
        # Supply sumo_step_count as 100.
        # Supply wall_clock_runtime_seconds as 1.0.
        sumo_step_count=100, wall_clock_runtime_seconds=1.0)


# Check baseline records failure continues and atomically accounts for 36 using the setup, calls, and assertions
# below.
# Input tmp_path: the supplied tmp path.
# Input monkeypatch: the supplied monkeypatch.
# Output: no explicit value; normal completion returns None.
def test_baseline_records_failure_continues_and_atomically_accounts_for_36(
        # Declare tmp_path, monkeypatch as input parameters.
        tmp_path, monkeypatch):
    # Import negotiation_training.final_selection as module for use in this module.
    import negotiation_training.final_selection as module
    # Write the supplied text to (tmp_path / 'selected_configuration.json').
    (tmp_path / "selected_configuration.json").write_text("{}")
    # Set calls to an empty list.
    calls = []

    # Define FakeEnvironment to group the state and operations declared below.
    # Instances expose the attributes and methods implemented in this class.
    class FakeEnvironment:
        # Initialize the instance attributes and collaborators used by the operations below.
        # Input provider: the supplied provider.
        # Output: no explicit value; normal completion returns None.
        def __init__(self, provider):
            # Require provider.allows_unresolved_coordination; otherwise raise AssertionError.
            assert provider.allows_unresolved_coordination

        # Run episode using the inputs and processing steps below.
        # Input specification: the supplied specification.
        # Input manifest_id: the supplied manifest id.
        # Output: the result of _successful_baseline_episode(specification).
        # Processing: select branches using the stated conditions.
        def run_episode(self, specification, manifest_id):
            # Delete manifest_id from its containing namespace or collection.
            del manifest_id
            # Append specification to calls.
            calls.append(specification)
            # Run this branch when the number of entries in calls equals 1.
            if len(calls) == 1:
                # Raise PhysicalReplayError with the text 'BLOCKED_VEHICLE_ENTERED_CONFLICT_ZONE' to stop this
                # execution path.
                raise PhysicalReplayError(
                    "BLOCKED_VEHICLE_ENTERED_CONFLICT_ZONE",
                    # Supply a tuple containing the text 'SCENARIO_AV_0', the text 'CZ', 5.0 to
                    # PhysicalReplayError.
                    ("SCENARIO_AV_0", "CZ", 5.0))
            # Return the result of _successful_baseline_episode(specification) to the caller.
            return _successful_baseline_episode(specification)

    # Call monkeypatch.setattr with the supplied arguments.
    monkeypatch.setattr(module, "CoupledNegotiationTrainingEnvironment",
                        # Supply FakeEnvironment to monkeypatch.setattr.
                        FakeEnvironment)
    # Call monkeypatch.setattr with the supplied arguments.
    monkeypatch.setattr(module, "_specification", lambda payload, sid: sid)
    # Set result to the result of baseline(tmp_path).
    result = baseline(tmp_path)
    # Require the number of entries in calls equals the number of entries in result at 'scenario_results'; equals
    # 36; otherwise raise AssertionError.
    assert len(calls) == len(result["scenario_results"]) == 36
    # Require result['scenario_results'][0] at 'status' equals the text 'HARD_SAFETY_FAILURE'; otherwise raise
    # AssertionError.
    assert result["scenario_results"][0]["status"] == "HARD_SAFETY_FAILURE"
    # Require result['scenario_results'][0] at 'total_team_travel_time_seconds' is the same object as None;
    # otherwise raise AssertionError.
    assert result["scenario_results"][0][
        # Supply None to the enclosing expression.
        "total_team_travel_time_seconds"] is None
    # Require result['summary'] at 'scenario_count' equals 36; otherwise raise AssertionError.
    assert result["summary"]["scenario_count"] == 36
    # Require result['summary'] at 'completed_episode_count' equals 35; otherwise raise AssertionError.
    assert result["summary"]["completed_episode_count"] == 35
    # Require result['summary'] at 'hard_safety_failure_count' equals 1; otherwise raise AssertionError.
    assert result["summary"]["hard_safety_failure_count"] == 1
    # Require result['summary'] at 'blocked_zone_failure_count' equals 1; otherwise raise AssertionError.
    assert result["summary"]["blocked_zone_failure_count"] == 1
    # Require result['summary'] at 'safety_eligible' is the same object as False; otherwise raise AssertionError.
    assert result["summary"]["safety_eligible"] is False
    # Require result['summary'] at 'native_sumo_safety_interventions' equals 70; otherwise raise AssertionError.
    assert result["summary"]["native_sumo_safety_interventions"] == 70
    # Require the number of entries in a list built from the result of (tmp_path / 'held_out' /
    # 'baseline_scenario_records').glob('*.json') equals 36; otherwise raise AssertionError.
    assert len(list((tmp_path / "held_out" /
                     # Supply 36 to the enclosing expression.
                     "baseline_scenario_records").glob("*.json"))) == 36


# Check report prioritizes safety and uses only completed matched subset using the setup, calls, and assertions
# below.
# Input tmp_path: the supplied tmp path.
# Output: no explicit value; normal completion returns None.
def test_report_prioritizes_safety_and_uses_only_completed_matched_subset(
        # Declare tmp_path as input parameter.
        tmp_path):
    # Create the directory requested by (tmp_path / 'comparison').
    (tmp_path / "comparison").mkdir()
    # Create the directory requested by (tmp_path / 'held_out').
    (tmp_path / "held_out").mkdir()
    # Set validation to the result of _validation_payload(a dictionary containing E5, E10, E15, a dictionary of
    # key mapped to True for key in CANDIDATE_EPOCHS).
    validation = _validation_payload(
        # Store 1 under 'E5'.
        # Store 2 under 'E10'.
        # Store 3 under 'E15'.
        {"E5": 1, "E10": 2, "E15": 3},
        # Supply a dictionary of key mapped to True for key in CANDIDATE_EPOCHS to _validation_payload.
        {key: True for key in CANDIDATE_EPOCHS})
    # Write the supplied text to (tmp_path / 'comparison' / 'candidate_validation_summary.json').
    (tmp_path / "comparison" / "candidate_validation_summary.json").write_text(
        # Supply the serialized data produced by json.dumps to (tmp_path / 'comparison' /
        # 'candidate_validation_summary.json').write_text.
        json.dumps(validation))
    # Write the supplied text to (tmp_path / 'selected_configuration.json').
    (tmp_path / "selected_configuration.json").write_text(json.dumps({
        "selected_candidate_id": "E5"}))
    # Set learned to a dictionary containing scenario_id, total_team_travel_time_seconds, completed_vehicles,
    # collisions,...
    learned = {"scenario_id": ["S", 1],
               # Store 10.0 under 'total_team_travel_time_seconds'.
               "total_team_travel_time_seconds": 10.0,
               # Store 2 under 'completed_vehicles'.
               # Store 0 under 'collisions'.
               "completed_vehicles": 2, "collisions": 0,
               # Store 0 under 'blocked_zone_violations'.
               "blocked_zone_violations": 0,
               # Store 0 under 'native_sumo_safety_interventions'.
               "native_sumo_safety_interventions": 0}
    # Write the supplied text to (tmp_path / 'held_out' / 'selected_mappo_results.json').
    (tmp_path / "held_out" / "selected_mappo_results.json").write_text(
        # Store a list containing a dictionary containing scenario_results under 'replications'.
        # Store a list containing learned under 'scenario_results'.
        json.dumps({"replications": [{"scenario_results": [learned]}]}))
    # Set failed to the result of _hard_safety_failure_record(a tuple containing the text 'S', 1, the result of
    # PhysicalReplayError(the text...).
    failed = _hard_safety_failure_record(
        # Supply the result of PhysicalReplayError(the text 'BLOCKED_VEHICLE_ENTERED_CONFLICT_ZONE', a tuple
        # containing the text 'V', the text 'Z', 1.0) to _hard_safety_failure_record.
        ("S", 1), PhysicalReplayError(
            # Supply a tuple containing the text 'V', the text 'Z', 1.0 to PhysicalReplayError.
            "BLOCKED_VEHICLE_ENTERED_CONFLICT_ZONE", ("V", "Z", 1.0)))
    # Write the supplied text to (tmp_path / 'held_out' / 'baseline_results.json').
    (tmp_path / "held_out" / "baseline_results.json").write_text(json.dumps({
        # Store a list containing failed under 'scenario_results'.
        "scenario_results": [failed],
        # Store the result of _baseline_summary(a list containing failed) under 'summary'.
        "summary": _baseline_summary([failed])}))
    # Call report with the supplied arguments.
    report(tmp_path)
    # Set comparison to the decoded data produced by json.loads from the text read from (tmp_path / 'comparison' /
    # 'held_out_mappo_vs_baseline.json').
    comparison = json.loads((tmp_path / "comparison" /
        # Supply the text 'held_out_mappo_vs_baseline.json' to the enclosing expression.
        "held_out_mappo_vs_baseline.json").read_text())
    # Require comparison at 'baseline_safety_eligible' is the same object as False; otherwise raise
    # AssertionError.
    assert comparison["baseline_safety_eligible"] is False
    # Require comparison at 'overall_mean_difference' is the same object as None; otherwise raise AssertionError.
    assert comparison["overall_mean_difference"] is None
    # Require comparison at 'matched_completed_scenario_count' equals 0; otherwise raise AssertionError.
    assert comparison["matched_completed_scenario_count"] == 0
    # Require comparison at 'efficiency_comparison_scope' equals the text
    # 'DESCRIPTIVE_MATCHED_COMPLETED_SCENARIO_SUBSET_ONLY'; otherwise raise AssertionError.
    assert comparison["efficiency_comparison_scope"] == (
        "DESCRIPTIVE_MATCHED_COMPLETED_SCENARIO_SUBSET_ONLY")
    # Set conclusion to comparison at 'truthful_conclusion'.
    conclusion = comparison["truthful_conclusion"]
    # Require the text 'failed the predefined hard safety-validity gate' belongs to conclusion; otherwise raise
    # AssertionError.
    assert "failed the predefined hard safety-validity gate" in conclusion
    # Require the text 'reduced total team travel time' does not belong to conclusion; otherwise raise
    # AssertionError.
    assert "reduced total team travel time" not in conclusion


# Check runner source does not promote historical demo checkpoint using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_runner_source_does_not_promote_historical_demo_checkpoint():
    # Import negotiation_training.final_selection as module for use in this module.
    import negotiation_training.final_selection as module
    # Set source to the result of inspect.getsource(module).
    source = inspect.getsource(module)
    # Require the text 'replication_0_state_2.pt' belongs to source; otherwise raise AssertionError.
    assert "replication_0_state_2.pt" in source
    # Require the text 'mappo_extended_resume' does not belong to source; otherwise raise AssertionError.
    assert "mappo_extended_resume" not in source
    # Require the text 'mappo_demo_policy.pt' does not belong to source; otherwise raise AssertionError.
    assert "mappo_demo_policy.pt" not in source
    # Require the text 'ground_truth_route_id' does not belong to source; otherwise raise AssertionError.
    assert "ground_truth_route_id" not in source
