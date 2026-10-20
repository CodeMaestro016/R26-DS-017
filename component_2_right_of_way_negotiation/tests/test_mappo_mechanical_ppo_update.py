"""Step 5J.3B.4 offline PPO update evidence and mathematical tests."""

# Import inspect for use in this module.
import inspect
# Import json for use in this module.
import json

# Import torch for use in this module.
import torch

# Import ppo_clipped_surrogate_terms from negotiation_learning.mappo_returns for the operations below.
from negotiation_learning.mappo_returns import ppo_clipped_surrogate_terms
# Import MechanicalMAPPOTrainer, build_mechanical_mappo_behavior_policy_bundle, parameter_hash from
# negotiation_training for the operations below.
from negotiation_training import (
    MechanicalMAPPOTrainer, build_mechanical_mappo_behavior_policy_bundle,
    parameter_hash)


# Artifacts using the inputs and processing steps below.
# Output: a tuple containing the decoded data produced by json.load from the result of open(the text...
def _artifacts():
    # Return a tuple containing the decoded data produced by json.load from the result of open(the text... to the
    # caller.
    return (json.load(open("results/mappo_behavior_rollout.json", encoding="utf-8")),
            # Supply encoding as the text 'utf-8'.
            json.load(open("results/mappo_mechanical_ppo_update.json", encoding="utf-8")))


# Check rollout identity and exact sample parsing using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_rollout_identity_and_exact_sample_parsing():
    # Set (rollout, update) to the result of _artifacts().
    rollout, update = _artifacts()
    # Require rollout at 'status' equals the text 'REAL_MAPPO_BEHAVIOR_ROLLOUT_VALIDATED'; otherwise raise
    # AssertionError.
    assert rollout["status"] == "REAL_MAPPO_BEHAVIOR_ROLLOUT_VALIDATED"
    # Require rollout at 'step_5j_3b_4_readiness' equals the text 'READY_FOR_FIRST_MECHANICAL_PPO_UPDATE';
    # otherwise raise AssertionError.
    assert rollout["step_5j_3b_4_readiness"] == (
        "READY_FOR_FIRST_MECHANICAL_PPO_UPDATE")
    # Require update at 'source_rollout_identity' equals rollout at 'behavior_rollout_identity'; otherwise raise
    # AssertionError.
    assert update["source_rollout_identity"] == rollout["behavior_rollout_identity"]
    # Set factors to rollout at 'policy_factors'.
    factors = rollout["policy_factors"]
    # Require the number of entries in factors equals 227; otherwise raise AssertionError.
    assert len(factors) == 227
    # Require the sum of a lazy sequence of x['decision_role'] equals 'PROPOSER' for x in factors equals 179;
    # otherwise raise AssertionError.
    assert sum(x["decision_role"] == "PROPOSER" for x in factors) == 179
    # Require the sum of a lazy sequence of x['decision_role'] equals 'RESPONDER' for x in factors equals 48;
    # otherwise raise AssertionError.
    assert sum(x["decision_role"] == "RESPONDER" for x in factors) == 48
    # Require the number of entries in rollout at 'critic_samples' equals 36; otherwise raise AssertionError.
    assert len(rollout["critic_samples"]) == 36
    # Require whether every item is true in a lazy sequence of x['behavior_policy_source'] equals
    # 'MAPPO_BEHAVIOR_POLICY' and x at 'ppo_update_eligible' for x in factors; otherwise raise AssertionError.
    assert all(x["behavior_policy_source"] == "MAPPO_BEHAVIOR_POLICY" and
               # Evaluate x at 'ppo_update_eligible' as part of the enclosing expression.
               x["ppo_update_eligible"] for x in factors)


# Check exact behavior model hash reconstruction and frozen gnn using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_exact_behavior_model_hash_reconstruction_and_frozen_gnn():
    # Set (rollout, _) to the result of _artifacts().
    rollout, _ = _artifacts()
    # Set bundle to the result of build_mechanical_mappo_behavior_policy_bundle().
    bundle = build_mechanical_mappo_behavior_policy_bundle()
    # Set hashes to a dictionary containing gnn, proposer, responder, critic.
    hashes = {"gnn": parameter_hash(bundle.gnn),
              # Store the result of parameter_hash(bundle.proposer_actor) under 'proposer'.
              "proposer": parameter_hash(bundle.proposer_actor),
              # Store the result of parameter_hash(bundle.responder_actor) under 'responder'.
              "responder": parameter_hash(bundle.responder_actor),
              # Store the result of parameter_hash(bundle.centralized_critic) under 'critic'.
              "critic": parameter_hash(bundle.centralized_critic)}
    # Require hashes equals rollout at 'initial_parameter_hashes'; otherwise raise AssertionError.
    assert hashes == rollout["initial_parameter_hashes"]
    # Require the negation of whether any item is true in a lazy sequence of parameter.requires_grad for parameter
    # in the result of bundle.gnn.parameters(); otherwise raise AssertionError.
    assert not any(parameter.requires_grad for parameter in bundle.gnn.parameters())


# Check positive and negative advantage clipping semantics using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_positive_and_negative_advantage_clipping_semantics():
    # Set ratio to a tensor built from a list containing 1.3, 0.7.
    ratio = torch.tensor([1.3, 0.7], dtype=torch.float64)
    # Set positive to the result of ppo_clipped_surrogate_terms(ratio, 2.0, 0.2).
    positive = ppo_clipped_surrogate_terms(ratio, 2.0, 0.2)
    # Set negative to the result of ppo_clipped_surrogate_terms(ratio, the negative of 2.0, 0.2).
    negative = ppo_clipped_surrogate_terms(ratio, -2.0, 0.2)
    # Require the result of torch.equal(positive at 2, a tensor built from a list containing 2.4, 1.4); otherwise
    # raise AssertionError.
    assert torch.equal(positive[2], torch.tensor([2.4, 1.4], dtype=torch.float64))
    # Require the result of torch.equal(negative at 2, a tensor built from a list containing the negative of 2.6,
    # the negative of 1.6); otherwise raise AssertionError.
    assert torch.equal(negative[2], torch.tensor([-2.6, -1.6], dtype=torch.float64))


# Check full batch actor and one per joint batch critic contract using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_full_batch_actor_and_one_per_joint_batch_critic_contract():
    # Set (rollout, update) to the result of _artifacts().
    rollout, update = _artifacts()
    # Require update at 'sample_counts' equals a dictionary containing actor, proposer, responder, critic;
    # otherwise raise AssertionError.
    assert update["sample_counts"] == {
        # Store 227 under 'actor'.
        # Store 179 under 'proposer'.
        # Store 48 under 'responder'.
        # Store 36 under 'critic'.
        "actor": 227, "proposer": 179, "responder": 48, "critic": 36}
    # Require update['ppo_configuration'] at 'full_batch'; otherwise raise AssertionError.
    assert update["ppo_configuration"]["full_batch"]
    # Require update['ppo_configuration'] at 'actor_aggregation' equals the text
    # 'PER_POLICY_FACTOR_EMPIRICAL_MEAN'; otherwise raise AssertionError.
    assert update["ppo_configuration"]["actor_aggregation"] == (
        "PER_POLICY_FACTOR_EMPIRICAL_MEAN")
    # Require the number of entries in a set of the result of repr(x['joint_batch_id']) for x in rollout at
    # 'critic_samples' equals 36; otherwise raise AssertionError.
    assert len({repr(x["joint_batch_id"]) for x in rollout["critic_samples"]}) == 36
    # Require rollout at 'critic_samples_duplicated_per_policy_factor' is the same object as False; otherwise
    # raise AssertionError.
    assert rollout["critic_samples_duplicated_per_policy_factor"] is False


# Check explicit adam membership and two optimizer execution using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_explicit_adam_membership_and_two_optimizer_execution():
    # Set (_, update) to the result of _artifacts().
    _, update = _artifacts()
    # Set optimizer to update at 'optimizer_configuration'.
    optimizer = update["optimizer_configuration"]
    # Require optimizer at 'instances' equals 2 and optimizer at 'silent_defaults' equals 0; otherwise raise
    # AssertionError.
    assert optimizer["instances"] == 2 and optimizer["silent_defaults"] == 0
    # Require optimizer at 'family' equals the text 'ADAM'; otherwise raise AssertionError.
    assert optimizer["family"] == "ADAM"
    # Require optimizer at 'lr' equals 0.0005; otherwise raise AssertionError.
    assert optimizer["lr"] == 0.0005
    # Require optimizer at 'betas' equals a list containing 0.9, 0.999; otherwise raise AssertionError.
    assert optimizer["betas"] == [0.9, 0.999]
    # Require optimizer at 'eps' equals 1e-08; otherwise raise AssertionError.
    assert optimizer["eps"] == 1e-8
    # Require optimizer at 'weight_decay' equals 0; otherwise raise AssertionError.
    assert optimizer["weight_decay"] == 0
    # Require optimizer at 'amsgrad' is the same object as False; otherwise raise AssertionError.
    assert optimizer["amsgrad"] is False
    # Require optimizer at 'foreach' is the same object as optimizer at 'maximize'; is the same object as False;
    # otherwise raise AssertionError.
    assert optimizer["foreach"] is optimizer["maximize"] is False
    # Require optimizer at 'capturable' is the same object as optimizer at 'differentiable'; is the same object as
    # False; otherwise raise AssertionError.
    assert optimizer["capturable"] is optimizer["differentiable"] is False
    # Require optimizer at 'fused' is the same object as False; otherwise raise AssertionError.
    assert optimizer["fused"] is False
    # Require update at 'gnn_optimizer_membership' equals 0; otherwise raise AssertionError.
    assert update["gnn_optimizer_membership"] == 0
    # Set names to update at 'parameter_membership'.
    names = update["parameter_membership"]
    # Require the negation of a set built from names['proposer'] plus names['responder'] intersected with a set
    # built from names at 'critic'; otherwise raise AssertionError.
    assert not set(names["proposer"] + names["responder"]) & set(names["critic"])


# Check five epoch gradients steps and parameter hashes using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def test_five_epoch_gradients_steps_and_parameter_hashes():
    # Set (_, update) to the result of _artifacts().
    _, update = _artifacts()
    # Set epochs to update at 'epoch_diagnostics'.
    epochs = update["epoch_diagnostics"]
    # Require the number of entries in epochs equals update['ppo_configuration'] at 'epochs'; equals 5; otherwise
    # raise AssertionError.
    assert len(epochs) == update["ppo_configuration"]["epochs"] == 5
    # Require update at 'actor_optimizer_steps' equals update at 'critic_optimizer_steps'; equals 5; otherwise
    # raise AssertionError.
    assert update["actor_optimizer_steps"] == update["critic_optimizer_steps"] == 5
    # Require update at 'total_optimizer_steps' equals 10; otherwise raise AssertionError.
    assert update["total_optimizer_steps"] == 10
    # Require update at 'actor_backward_calls' equals update at 'critic_backward_calls'; equals 5; otherwise raise
    # AssertionError.
    assert update["actor_backward_calls"] == update["critic_backward_calls"] == 5
    # Require update at 'total_backward_calls' equals 10; otherwise raise AssertionError.
    assert update["total_backward_calls"] == 10
    # Iterate over epochs, binding each item to epoch.
    for epoch in epochs:
        # Require epoch['proposer_gradient'] at 'finite'; otherwise raise AssertionError.
        assert epoch["proposer_gradient"]["finite"]
        # Require epoch['responder_gradient'] at 'finite'; otherwise raise AssertionError.
        assert epoch["responder_gradient"]["finite"]
        # Require epoch['critic_gradient'] at 'finite'; otherwise raise AssertionError.
        assert epoch["critic_gradient"]["finite"]
        # Require epoch['proposer_gradient'] at 'nonzero_element_count' is greater than 0; otherwise raise
        # AssertionError.
        assert epoch["proposer_gradient"]["nonzero_element_count"] > 0
        # Require epoch['responder_gradient'] at 'nonzero_element_count' is greater than 0; otherwise raise
        # AssertionError.
        assert epoch["responder_gradient"]["nonzero_element_count"] > 0
        # Require epoch['critic_gradient'] at 'nonzero_element_count' is greater than 0; otherwise raise
        # AssertionError.
        assert epoch["critic_gradient"]["nonzero_element_count"] > 0
        # Require epoch['parameter_hashes_after_epoch'] at 'gnn' equals update['initial_parameter_hashes'] at
        # 'gnn'; otherwise raise AssertionError.
        assert epoch["parameter_hashes_after_epoch"]["gnn"] == (
            # Evaluate update['initial_parameter_hashes'] at 'gnn' as part of the enclosing expression.
            update["initial_parameter_hashes"]["gnn"])
    # Require update at 'proposer_parameter_changed'; otherwise raise AssertionError.
    assert update["proposer_parameter_changed"]
    # Require update at 'responder_parameter_changed'; otherwise raise AssertionError.
    assert update["responder_parameter_changed"]
    # Require update at 'critic_parameter_changed'; otherwise raise AssertionError.
    assert update["critic_parameter_changed"]
    # Require update at 'gnn_hash_unchanged'; otherwise raise AssertionError.
    assert update["gnn_hash_unchanged"]


# Check no entropy gradient clipping environment or selection leakage using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_no_entropy_gradient_clipping_environment_or_selection_leakage():
    # Set (_, update) to the result of _artifacts().
    _, update = _artifacts()
    # Set config to update at 'ppo_configuration'.
    config = update["ppo_configuration"]
    # Require config at 'entropy_term' equals the text 'NONE'; otherwise raise AssertionError.
    assert config["entropy_term"] == "NONE"
    # Require config at 'gradient_clipping' equals the text 'NONE'; otherwise raise AssertionError.
    assert config["gradient_clipping"] == "NONE"
    # Require config at 'value_loss_mixing_coefficient' equals the text 'NONE_SEPARATE_OPTIMIZERS'; otherwise
    # raise AssertionError.
    assert config["value_loss_mixing_coefficient"] == "NONE_SEPARATE_OPTIMIZERS"
    # Require update at 'actions_resampled' equals 0; otherwise raise AssertionError.
    assert update["actions_resampled"] == 0
    # Require update at 'new_sumo_rollouts' equals 0; otherwise raise AssertionError.
    assert update["new_sumo_rollouts"] == 0
    # Require update at 'new_training_environment_episodes' equals 0; otherwise raise AssertionError.
    assert update["new_training_environment_episodes"] == 0
    # Require update at 'validation_runs' equals update at 'held_out_runs'; equals 0; otherwise raise
    # AssertionError.
    assert update["validation_runs"] == update["held_out_runs"] == 0
    # Require update at 'profiling_ppo_samples_used' equals 0; otherwise raise AssertionError.
    assert update["profiling_ppo_samples_used"] == 0
    # Require update at 'new_reward_terms' equals 0; otherwise raise AssertionError.
    assert update["new_reward_terms"] == 0
    # Require update at 'new_selected_hyperparameters' equals 0; otherwise raise AssertionError.
    assert update["new_selected_hyperparameters"] == 0
    # Require update at 'mechanical_update_only'; otherwise raise AssertionError.
    assert update["mechanical_update_only"]
    # Require update at 'final_model' is the same object as False; otherwise raise AssertionError.
    assert update["final_model"] is False
    # Require update at 'final_selection_eligible' is the same object as False; otherwise raise AssertionError.
    assert update["final_selection_eligible"] is False


# Check trainer source has no environment collection or forbidden terms using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_trainer_source_has_no_environment_collection_or_forbidden_terms():
    # Set source to the result of inspect.getsource(MechanicalMAPPOTrainer).
    source = inspect.getsource(MechanicalMAPPOTrainer)
    # Require the text 'CoupledNegotiationTrainingEnvironment' does not belong to source; otherwise raise
    # AssertionError.
    assert "CoupledNegotiationTrainingEnvironment" not in source
    # Require the text 'SUMO' does not belong to source; otherwise raise AssertionError.
    assert "SUMO" not in source
    # Require the text 'clip_grad_norm' does not belong to source; otherwise raise AssertionError.
    assert "clip_grad_norm" not in source
    # Require the text 'entropy *' does not belong to source; otherwise raise AssertionError.
    assert "entropy *" not in source
