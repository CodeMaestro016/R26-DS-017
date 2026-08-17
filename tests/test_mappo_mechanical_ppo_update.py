"""Step 5J.3B.4 offline PPO update evidence and mathematical tests."""

import inspect
import json

import torch

from negotiation_learning.mappo_returns import ppo_clipped_surrogate_terms
from negotiation_training import (
    MechanicalMAPPOTrainer, build_mechanical_mappo_behavior_policy_bundle,
    parameter_hash)


def _artifacts():
    return (json.load(open("results/mappo_behavior_rollout.json", encoding="utf-8")),
            json.load(open("results/mappo_mechanical_ppo_update.json", encoding="utf-8")))


def test_rollout_identity_and_exact_sample_parsing():
    rollout, update = _artifacts()
    assert rollout["status"] == "REAL_MAPPO_BEHAVIOR_ROLLOUT_VALIDATED"
    assert rollout["step_5j_3b_4_readiness"] == (
        "READY_FOR_FIRST_MECHANICAL_PPO_UPDATE")
    assert update["source_rollout_identity"] == rollout["behavior_rollout_identity"]
    factors = rollout["policy_factors"]
    assert len(factors) == 227
    assert sum(x["decision_role"] == "PROPOSER" for x in factors) == 179
    assert sum(x["decision_role"] == "RESPONDER" for x in factors) == 48
    assert len(rollout["critic_samples"]) == 36
    assert all(x["behavior_policy_source"] == "MAPPO_BEHAVIOR_POLICY" and
               x["ppo_update_eligible"] for x in factors)


def test_exact_behavior_model_hash_reconstruction_and_frozen_gnn():
    rollout, _ = _artifacts()
    bundle = build_mechanical_mappo_behavior_policy_bundle()
    hashes = {"gnn": parameter_hash(bundle.gnn),
              "proposer": parameter_hash(bundle.proposer_actor),
              "responder": parameter_hash(bundle.responder_actor),
              "critic": parameter_hash(bundle.centralized_critic)}
    assert hashes == rollout["initial_parameter_hashes"]
    assert not any(parameter.requires_grad for parameter in bundle.gnn.parameters())


def test_positive_and_negative_advantage_clipping_semantics():
    ratio = torch.tensor([1.3, 0.7], dtype=torch.float64)
    positive = ppo_clipped_surrogate_terms(ratio, 2.0, 0.2)
    negative = ppo_clipped_surrogate_terms(ratio, -2.0, 0.2)
    assert torch.equal(positive[2], torch.tensor([2.4, 1.4], dtype=torch.float64))
    assert torch.equal(negative[2], torch.tensor([-2.6, -1.6], dtype=torch.float64))


def test_full_batch_actor_and_one_per_joint_batch_critic_contract():
    rollout, update = _artifacts()
    assert update["sample_counts"] == {
        "actor": 227, "proposer": 179, "responder": 48, "critic": 36}
    assert update["ppo_configuration"]["full_batch"]
    assert update["ppo_configuration"]["actor_aggregation"] == (
        "PER_POLICY_FACTOR_EMPIRICAL_MEAN")
    assert len({repr(x["joint_batch_id"]) for x in rollout["critic_samples"]}) == 36
    assert rollout["critic_samples_duplicated_per_policy_factor"] is False


def test_explicit_adam_membership_and_two_optimizer_execution():
    _, update = _artifacts()
    optimizer = update["optimizer_configuration"]
    assert optimizer["instances"] == 2 and optimizer["silent_defaults"] == 0
    assert optimizer["family"] == "ADAM"
    assert optimizer["lr"] == 0.0005
    assert optimizer["betas"] == [0.9, 0.999]
    assert optimizer["eps"] == 1e-8
    assert optimizer["weight_decay"] == 0
    assert optimizer["amsgrad"] is False
    assert optimizer["foreach"] is optimizer["maximize"] is False
    assert optimizer["capturable"] is optimizer["differentiable"] is False
    assert optimizer["fused"] is False
    assert update["gnn_optimizer_membership"] == 0
    names = update["parameter_membership"]
    assert not set(names["proposer"] + names["responder"]) & set(names["critic"])


def test_five_epoch_gradients_steps_and_parameter_hashes():
    _, update = _artifacts()
    epochs = update["epoch_diagnostics"]
    assert len(epochs) == update["ppo_configuration"]["epochs"] == 5
    assert update["actor_optimizer_steps"] == update["critic_optimizer_steps"] == 5
    assert update["total_optimizer_steps"] == 10
    assert update["actor_backward_calls"] == update["critic_backward_calls"] == 5
    assert update["total_backward_calls"] == 10
    for epoch in epochs:
        assert epoch["proposer_gradient"]["finite"]
        assert epoch["responder_gradient"]["finite"]
        assert epoch["critic_gradient"]["finite"]
        assert epoch["proposer_gradient"]["nonzero_element_count"] > 0
        assert epoch["responder_gradient"]["nonzero_element_count"] > 0
        assert epoch["critic_gradient"]["nonzero_element_count"] > 0
        assert epoch["parameter_hashes_after_epoch"]["gnn"] == (
            update["initial_parameter_hashes"]["gnn"])
    assert update["proposer_parameter_changed"]
    assert update["responder_parameter_changed"]
    assert update["critic_parameter_changed"]
    assert update["gnn_hash_unchanged"]


def test_no_entropy_gradient_clipping_environment_or_selection_leakage():
    _, update = _artifacts()
    config = update["ppo_configuration"]
    assert config["entropy_term"] == "NONE"
    assert config["gradient_clipping"] == "NONE"
    assert config["value_loss_mixing_coefficient"] == "NONE_SEPARATE_OPTIMIZERS"
    assert update["actions_resampled"] == 0
    assert update["new_sumo_rollouts"] == 0
    assert update["new_training_environment_episodes"] == 0
    assert update["validation_runs"] == update["held_out_runs"] == 0
    assert update["profiling_ppo_samples_used"] == 0
    assert update["new_reward_terms"] == 0
    assert update["new_selected_hyperparameters"] == 0
    assert update["mechanical_update_only"]
    assert update["final_model"] is False
    assert update["final_selection_eligible"] is False


def test_trainer_source_has_no_environment_collection_or_forbidden_terms():
    source = inspect.getsource(MechanicalMAPPOTrainer)
    assert "CoupledNegotiationTrainingEnvironment" not in source
    assert "SUMO" not in source
    assert "clip_grad_norm" not in source
    assert "entropy *" not in source
