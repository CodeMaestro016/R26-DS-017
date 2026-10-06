"""Step 5J.3A post-freeze coupled-environment contracts."""

import inspect
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from experimentation import ScenarioRole, build_design
from negotiation_training import (
    DeterministicEnvironmentProfilingActionProvider,
    PROFILING_RULE, assess_step_5j_3a_environment_readiness,
    assess_step_5j_3b_pilot_readiness, load_coupling_evidence)
from negotiation_training.environment import CoupledNegotiationTrainingEnvironment
from negotiation_training.profiling import deterministic_seed_from_design


PROFILE = Path("results/coupled_environment_profile.json")


def test_post_freeze_evidence_preserves_exact_design_identity():
    before = build_design()
    identity = before["freeze"].freeze_id
    evidence = assess_step_5j_3a_environment_readiness(
        before, load_coupling_evidence())
    after = build_design()
    assert before["freeze"].freeze_id == identity == after["freeze"].freeze_id
    assert evidence.frozen_design_id == identity
    assert evidence.readiness_status == "READY_TO_BUILD_COUPLED_MAPPO_ENVIRONMENT"


def test_coupling_loader_requires_real_success_fields(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text(json.dumps({"status": "CAUSAL_EXECUTION_PATH_VALIDATED"}))
    with pytest.raises(ValueError, match="CAUSAL_COUPLING_EVIDENCE_NOT_VALIDATED"):
        load_coupling_evidence(path)


def test_profiling_provider_is_canonical_and_outcome_blind():
    provider = DeterministicEnvironmentProfilingActionProvider()
    branches = (SimpleNamespace(branch_id=("B",), graph_executable=True),
                SimpleNamespace(branch_id=("A",), graph_executable=True))
    assert provider.select_joint_actions(branches, ()).branch_id == ("A",)
    assert provider.selection_rule == PROFILING_RULE
    assert provider.outcome_data_used is False
    source = inspect.getsource(provider.select_joint_actions).lower()
    assert not any(word in source for word in
                   ("reward", "travel_time", "throughput", "completion_time"))


def test_complete_profile_visits_training_once_and_never_other_roles():
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    design = build_design()
    training = design["manifests"][ScenarioRole.TRAINING]
    assert profile["training_scenarios_attempted"] == len(training.scenario_ids) == 36
    assert profile["training_scenarios_completed"] == 36
    assert sorted(profile["visited_scenario_ids"]) == sorted(
        repr(item) for item in training.scenario_ids)
    assert len(set(profile["visited_scenario_ids"])) == 36
    assert profile["validation_performance_executions"] == 0
    assert profile["held_out_performance_executions"] == 0


def test_profile_reward_safety_and_ppo_boundaries():
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    assert profile["interval_rewards_reconcile"]
    assert profile["hard_validity_gates_passed"]
    assert not profile["profiling_samples_ppo_eligible"]
    assert all(item["collision_count"] == 0 and
               item["blocked_zone_entry_violation_count"] == 0
               for item in profile["episodes"])
    for episode in profile["episodes"]:
        assert episode["interval_reward_sum"] == episode["raw_shared_team_reward"]
        for batch in episode["joint_decision_batches"]:
            for factor in batch["policy_factors"]:
                assert factor["behavior_policy_source"] == (
                    "NON_LEARNED_PROFILING_PROVIDER")
                assert factor["ppo_update_eligible"] is False
                assert factor["selected_action"] in tuple(
                    action for action, allowed in zip(
                        factor["action_names"], factor["hard_action_mask"])
                    if allowed)
                assert factor["claim_representation_shape"] == [34]
                if factor["role"] == "RESPONDER":
                    assert factor["protocol_representation_shape"] == [16]
                assert factor["return_record_id"] is not None
                assert factor["advantage_record_id"] is not None


def test_no_training_budget_seed_optimizer_or_learning_was_instantiated():
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    assert profile["actual_rl_seeds_instantiated"] == 0
    assert profile["optimizer_instances"] == 0
    assert profile["backward_calls"] == 0
    assert profile["parameter_updates"] == 0
    assert profile["mappo_pilot_runs"] == 0
    assert profile["selected_hyperparameter_values"] == 0
    assert profile["training_budget_status"].startswith(
        "LEARNING_BUDGET_STILL_REQUIRES")
    source = inspect.getsource(CoupledNegotiationTrainingEnvironment)
    assert "torch.optim" not in source and "backward(" not in source


def test_seed_procedure_is_deterministic_but_profile_instantiates_none():
    identity = build_design()["freeze"].freeze_id
    assert deterministic_seed_from_design(identity, 7) == (
        deterministic_seed_from_design(identity, 7))
    assert deterministic_seed_from_design(identity, 7) != (
        deterministic_seed_from_design(identity, 8))


def test_step_5j_3b_readiness_is_evidence_aware():
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    assert assess_step_5j_3b_pilot_readiness(profile) == (
        "READY_TO_IMPLEMENT_FIRST_CONTROLLED_MAPPO_PILOT")
