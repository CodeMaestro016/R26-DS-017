"""Step 5J.3A post-freeze coupled-environment contracts."""

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
# Import DeterministicEnvironmentProfilingActionProvider, PROFILING_RULE, assess_step_5j_3a_environment_readiness,
# assess_step_5j_3b_pilot_readiness, load_coupling_evidence from negotiation_training for the operations below.
from negotiation_training import (
    DeterministicEnvironmentProfilingActionProvider,
    PROFILING_RULE, assess_step_5j_3a_environment_readiness,
    assess_step_5j_3b_pilot_readiness, load_coupling_evidence)
# Import CoupledNegotiationTrainingEnvironment from negotiation_training.environment for the operations below.
from negotiation_training.environment import CoupledNegotiationTrainingEnvironment
# Import deterministic_seed_from_design from negotiation_training.profiling for the operations below.
from negotiation_training.profiling import deterministic_seed_from_design


# Set PROFILE to the result of Path(the text 'results/coupled_environment_profile.json').
PROFILE = Path("results/coupled_environment_profile.json")


# Check post freeze evidence preserves exact design identity using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_post_freeze_evidence_preserves_exact_design_identity():
    # Set before to the result of build_design().
    before = build_design()
    # Set identity to before['freeze'].freeze_id.
    identity = before["freeze"].freeze_id
    # Set evidence to the result of assess_step_5j_3a_environment_readiness(before, the result of
    # load_coupling_evidence()).
    evidence = assess_step_5j_3a_environment_readiness(
        # Supply the result of load_coupling_evidence() to assess_step_5j_3a_environment_readiness.
        before, load_coupling_evidence())
    # Set after to the result of build_design().
    after = build_design()
    # Require before['freeze'].freeze_id equals identity; equals after['freeze'].freeze_id; otherwise raise
    # AssertionError.
    assert before["freeze"].freeze_id == identity == after["freeze"].freeze_id
    # Require evidence.frozen_design_id equals identity; otherwise raise AssertionError.
    assert evidence.frozen_design_id == identity
    # Require evidence.readiness_status equals the text 'READY_TO_BUILD_COUPLED_MAPPO_ENVIRONMENT'; otherwise
    # raise AssertionError.
    assert evidence.readiness_status == "READY_TO_BUILD_COUPLED_MAPPO_ENVIRONMENT"


# Check coupling loader requires real success fields using the setup, calls, and assertions below.
# Input tmp_path: the supplied tmp path.
# Output: no explicit value; normal completion returns None.
def test_coupling_loader_requires_real_success_fields(tmp_path):
    # Set path to tmp_path joined with the path segment 'bad.json'.
    path = tmp_path / "bad.json"
    # Write the supplied text to path.
    path.write_text(json.dumps({"status": "CAUSAL_EXECUTION_PATH_VALIDATED"}))
    # Enter the result of pytest.raises(ValueError) and run the enclosed operations within that context.
    with pytest.raises(ValueError, match="CAUSAL_COUPLING_EVIDENCE_NOT_VALIDATED"):
        # Call load_coupling_evidence with the supplied arguments.
        load_coupling_evidence(path)


# Check profiling provider is canonical and outcome blind using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_profiling_provider_is_canonical_and_outcome_blind():
    # Set provider to the result of DeterministicEnvironmentProfilingActionProvider().
    provider = DeterministicEnvironmentProfilingActionProvider()
    # Set branches to a tuple containing the result of SimpleNamespace(), the result of SimpleNamespace().
    branches = (SimpleNamespace(branch_id=("B",), graph_executable=True),
                # Supply branch_id as a tuple containing the text 'A'.
                # Supply graph_executable as True.
                SimpleNamespace(branch_id=("A",), graph_executable=True))
    # Require provider.select_joint_actions(branches, ()).branch_id equals a tuple containing the text 'A';
    # otherwise raise AssertionError.
    assert provider.select_joint_actions(branches, ()).branch_id == ("A",)
    # Require provider.selection_rule equals PROFILING_RULE; otherwise raise AssertionError.
    assert provider.selection_rule == PROFILING_RULE
    # Require provider.outcome_data_used is the same object as False; otherwise raise AssertionError.
    assert provider.outcome_data_used is False
    # Set source to the result of inspect.getsource(provider.select_joint_actions).lower().
    source = inspect.getsource(provider.select_joint_actions).lower()
    # Require the negation of whether any item is true in a lazy sequence of word belongs to source for word in a
    # tuple containing 'reward', 'travel_time', 'throughput', 'completion_time'; otherwise raise AssertionError.
    assert not any(word in source for word in
                   # Evaluate a tuple containing the text 'reward', the text 'travel_time', the text 'throughput',
                   # the text 'completion_time' as part of the enclosing expression.
                   ("reward", "travel_time", "throughput", "completion_time"))


# Check complete profile visits training once and never other roles using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_complete_profile_visits_training_once_and_never_other_roles():
    # Set profile to the decoded data produced by json.loads from the text read from PROFILE.
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    # Set design to the result of build_design().
    design = build_design()
    # Set training to design['manifests'] at ScenarioRole.TRAINING.
    training = design["manifests"][ScenarioRole.TRAINING]
    # Require profile at 'training_scenarios_attempted' equals the number of entries in training.scenario_ids;
    # equals 36; otherwise raise AssertionError.
    assert profile["training_scenarios_attempted"] == len(training.scenario_ids) == 36
    # Require profile at 'training_scenarios_completed' equals 36; otherwise raise AssertionError.
    assert profile["training_scenarios_completed"] == 36
    # Require the sorted values from profile at 'visited_scenario_ids' equals the sorted values from a lazy
    # sequence of the result of repr(item) for item in training.scenario_ids; otherwise raise AssertionError.
    assert sorted(profile["visited_scenario_ids"]) == sorted(
        # Evaluate training.scenario_ids as part of the enclosing expression.
        repr(item) for item in training.scenario_ids)
    # Require the number of entries in a set built from profile at 'visited_scenario_ids' equals 36; otherwise
    # raise AssertionError.
    assert len(set(profile["visited_scenario_ids"])) == 36
    # Require profile at 'validation_performance_executions' equals 0; otherwise raise AssertionError.
    assert profile["validation_performance_executions"] == 0
    # Require profile at 'held_out_performance_executions' equals 0; otherwise raise AssertionError.
    assert profile["held_out_performance_executions"] == 0


# Check profile reward safety and ppo boundaries using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def test_profile_reward_safety_and_ppo_boundaries():
    # Set profile to the decoded data produced by json.loads from the text read from PROFILE.
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    # Require profile at 'interval_rewards_reconcile'; otherwise raise AssertionError.
    assert profile["interval_rewards_reconcile"]
    # Require profile at 'hard_validity_gates_passed'; otherwise raise AssertionError.
    assert profile["hard_validity_gates_passed"]
    # Require the negation of profile at 'profiling_samples_ppo_eligible'; otherwise raise AssertionError.
    assert not profile["profiling_samples_ppo_eligible"]
    # Require whether every item is true in a lazy sequence of item['collision_count'] equals 0 and
    # item['blocked_zone_entry_violation_count'] equals 0 for item in profile at 'episodes'; otherwise raise
    # AssertionError.
    assert all(item["collision_count"] == 0 and
               # Evaluate item at 'blocked_zone_entry_violation_count' equals 0 as part of the enclosing
               # expression.
               item["blocked_zone_entry_violation_count"] == 0
               # Evaluate profile at 'episodes' as part of the enclosing expression.
               for item in profile["episodes"])
    # Iterate over profile at 'episodes', binding each item to episode.
    for episode in profile["episodes"]:
        # Require episode at 'interval_reward_sum' equals episode at 'raw_shared_team_reward'; otherwise raise
        # AssertionError.
        assert episode["interval_reward_sum"] == episode["raw_shared_team_reward"]
        # Iterate over episode at 'joint_decision_batches', binding each item to batch.
        for batch in episode["joint_decision_batches"]:
            # Iterate over batch at 'policy_factors', binding each item to factor.
            for factor in batch["policy_factors"]:
                # Require factor at 'behavior_policy_source' equals the text 'NON_LEARNED_PROFILING_PROVIDER';
                # otherwise raise AssertionError.
                assert factor["behavior_policy_source"] == (
                    "NON_LEARNED_PROFILING_PROVIDER")
                # Require factor at 'ppo_update_eligible' is the same object as False; otherwise raise
                # AssertionError.
                assert factor["ppo_update_eligible"] is False
                # Require factor at 'selected_action' belongs to a tuple built from a lazy sequence of action for
                # (action, allowed) in corresponding items paired from factor['action_names'],
                # factor['hard_action_mask']; retain entries satisfying allowed; otherwise raise AssertionError.
                assert factor["selected_action"] in tuple(
                    # Evaluate corresponding items paired from factor at 'action_names', factor at
                    # 'hard_action_mask' as part of the enclosing expression.
                    action for action, allowed in zip(
                        # Supply factor at 'hard_action_mask' to zip.
                        factor["action_names"], factor["hard_action_mask"])
                    # Evaluate allowed as part of the enclosing expression.
                    if allowed)
                # Require factor at 'claim_representation_shape' equals a list containing 34; otherwise raise
                # AssertionError.
                assert factor["claim_representation_shape"] == [34]
                # Run this branch when factor at 'role' equals the text 'RESPONDER'.
                if factor["role"] == "RESPONDER":
                    # Require factor at 'protocol_representation_shape' equals a list containing 16; otherwise
                    # raise AssertionError.
                    assert factor["protocol_representation_shape"] == [16]
                # Require factor at 'return_record_id' is a different object from None; otherwise raise
                # AssertionError.
                assert factor["return_record_id"] is not None
                # Require factor at 'advantage_record_id' is a different object from None; otherwise raise
                # AssertionError.
                assert factor["advantage_record_id"] is not None


# Check no training budget seed optimizer or learning was instantiated using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_no_training_budget_seed_optimizer_or_learning_was_instantiated():
    # Set profile to the decoded data produced by json.loads from the text read from PROFILE.
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    # Require profile at 'actual_rl_seeds_instantiated' equals 0; otherwise raise AssertionError.
    assert profile["actual_rl_seeds_instantiated"] == 0
    # Require profile at 'optimizer_instances' equals 0; otherwise raise AssertionError.
    assert profile["optimizer_instances"] == 0
    # Require profile at 'backward_calls' equals 0; otherwise raise AssertionError.
    assert profile["backward_calls"] == 0
    # Require profile at 'parameter_updates' equals 0; otherwise raise AssertionError.
    assert profile["parameter_updates"] == 0
    # Require profile at 'mappo_pilot_runs' equals 0; otherwise raise AssertionError.
    assert profile["mappo_pilot_runs"] == 0
    # Require profile at 'selected_hyperparameter_values' equals 0; otherwise raise AssertionError.
    assert profile["selected_hyperparameter_values"] == 0
    # Require the result of profile['training_budget_status'].startswith(the text
    # 'LEARNING_BUDGET_STILL_REQUIRES'); otherwise raise AssertionError.
    assert profile["training_budget_status"].startswith(
        "LEARNING_BUDGET_STILL_REQUIRES")
    # Set source to the result of inspect.getsource(CoupledNegotiationTrainingEnvironment).
    source = inspect.getsource(CoupledNegotiationTrainingEnvironment)
    # Require the text 'torch.optim' does not belong to source and the text 'backward(' does not belong to source;
    # otherwise raise AssertionError.
    assert "torch.optim" not in source and "backward(" not in source


# Check seed procedure is deterministic but profile instantiates none using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_seed_procedure_is_deterministic_but_profile_instantiates_none():
    # Set identity to build_design()['freeze'].freeze_id.
    identity = build_design()["freeze"].freeze_id
    # Require the result of deterministic_seed_from_design(identity, 7) equals the result of
    # deterministic_seed_from_design(identity, 7); otherwise raise AssertionError.
    assert deterministic_seed_from_design(identity, 7) == (
        # Evaluate the result of deterministic_seed_from_design(identity, 7) as part of the enclosing expression.
        deterministic_seed_from_design(identity, 7))
    # Require the result of deterministic_seed_from_design(identity, 7) differs from the result of
    # deterministic_seed_from_design(identity, 8); otherwise raise AssertionError.
    assert deterministic_seed_from_design(identity, 7) != (
        # Evaluate the result of deterministic_seed_from_design(identity, 8) as part of the enclosing expression.
        deterministic_seed_from_design(identity, 8))


# Check step 5j 3b readiness is evidence aware using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_step_5j_3b_readiness_is_evidence_aware():
    # Set profile to the decoded data produced by json.loads from the text read from PROFILE.
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    # Require the result of assess_step_5j_3b_pilot_readiness(profile) equals the text
    # 'READY_TO_IMPLEMENT_FIRST_CONTROLLED_MAPPO_PILOT'; otherwise raise AssertionError.
    assert assess_step_5j_3b_pilot_readiness(profile) == (
        "READY_TO_IMPLEMENT_FIRST_CONTROLLED_MAPPO_PILOT")
