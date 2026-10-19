"""Step 5J.3B.2 Adam provenance, grouping, and critic-reduction tests."""

import inspect
from dataclasses import FrozenInstanceError

import pytest
import torch

from experimentation import build_design
from negotiation_learning.ctde import (
    CentralizedNegotiationCritic, DecentralizedNegotiationActor,
    DecentralizedNegotiationResponseActor)
from negotiation_learning.gnn import EdgeAwareMPNNEncoder
from negotiation_training.adam_contract import (
    ADAM_PAPER_SOURCE, ORIGINAL_ADAM_MECHANICAL_REFERENCE,
    audit_parameter_membership, build_mechanical_adam_optimization_contract,
    joint_batch_critic_mean_squared_error)
from negotiation_training.architecture_contract import (
    build_mechanical_pilot_architecture_contract)
from negotiation_training.optimizer_contract import (
    build_mechanical_pilot_configuration_audit)
from negotiation_training.readiness import (
    assess_step_5j_3b_behavior_policy_readiness)


def _models():
    contract = build_mechanical_pilot_architecture_contract()
    return (
        DecentralizedNegotiationActor(contract.proposer_input_dimension, 2),
        DecentralizedNegotiationResponseActor(
            contract.responder_input_dimension, 2),
        CentralizedNegotiationCritic(contract.critic_input_dimension),
        EdgeAwareMPNNEncoder(8, 9, contract.gnn_hidden_dimension,
                             contract.gnn_message_passing_layers),
    )


def test_adam_values_have_original_reference_provenance_not_optimality():
    contract = build_mechanical_adam_optimization_contract()
    assert (contract.beta1, contract.beta2, contract.epsilon) == (0.9, 0.999, 1e-8)
    assert contract.beta1_source == contract.beta2_source == ADAM_PAPER_SOURCE
    assert contract.epsilon_source == ADAM_PAPER_SOURCE
    assert contract.provenance["beta_classification"] == ORIGINAL_ADAM_MECHANICAL_REFERENCE
    assert contract.provenance["claimed_optimal"] is False
    assert contract.project_selected is False
    assert contract.final_selection_eligible is False
    with pytest.raises(FrozenInstanceError):
        contract.beta1 = 0.8


def test_plain_adam_has_no_added_regularization_or_variant():
    contract = build_mechanical_adam_optimization_contract()
    assert contract.optimizer_family == "ADAM"
    assert contract.learning_rate == 0.0005
    assert contract.weight_decay == 0
    assert contract.amsgrad is False
    assert "ADAMW" not in contract.weight_decay_semantics
    assert contract.value_loss_mixing_coefficient == "NOT_APPLICABLE_SEPARATE_OPTIMIZERS"
    assert contract.provenance["role_specific_optimizer_weights"] == 0


def test_exact_parameter_sets_are_complete_disjoint_and_exclude_gnn():
    proposer, responder, critic, gnn = _models()
    membership = audit_parameter_membership(proposer, responder, critic, gnn)
    assert membership["proposer"] == (
        "proposer_actor.logit_head.weight", "proposer_actor.logit_head.bias")
    assert membership["responder"] == (
        "responder_actor.logit_head.weight", "responder_actor.logit_head.bias")
    assert membership["critic"] == (
        "centralized_critic.value_head.weight", "centralized_critic.value_head.bias")
    assert membership["gnn"]
    assert membership["duplicate_trainable_parameter_membership"] == 0


def test_critic_loss_is_mean_over_joint_batches_not_policy_factors():
    assert joint_batch_critic_mean_squared_error(
        torch.tensor([3.0]), torch.tensor([1.0])).item() == 4.0
    actual = joint_batch_critic_mean_squared_error(
        torch.tensor([1.0, 3.0]), torch.tensor([0.0, 1.0]))
    assert actual.item() == 2.5
    # The function accepts exactly one value per joint state; no factor counts.
    assert len(inspect.signature(
        joint_batch_critic_mean_squared_error).parameters) == 2


def test_installed_adam_signature_is_exhaustively_and_explicitly_audited():
    contract = build_mechanical_adam_optimization_contract()
    installed = set(inspect.signature(torch.optim.Adam).parameters)
    audited = {item.name for item in contract.adam_argument_audit}
    assert installed <= audited
    assert all(item.classification != "UNRESOLVED" for item in
               contract.adam_argument_audit)
    values = {item.name: item.explicit_mechanical_value for item in
              contract.adam_argument_audit}
    assert values["foreach"] == values["fused"] == "False"
    assert values["maximize"] == values["capturable"] == "False"
    assert values["differentiable"] == "False"
    assert values["decoupled_weight_decay"] == "False"
    assert contract.provenance["silent_adam_defaults"] == 0


def test_contracts_preserve_freeze_and_complete_configuration_readiness():
    before = build_design()["freeze"].freeze_id
    optimization = build_mechanical_adam_optimization_contract()
    architecture = build_mechanical_pilot_architecture_contract()
    audit = build_mechanical_pilot_configuration_audit()
    assert before == build_design()["freeze"].freeze_id
    assert optimization.frozen_design_id == architecture.frozen_design_id == before
    assert optimization.architecture_contract_id == architecture.contract_id
    assert optimization.unresolved_optimizer_fields == ()
    assert audit.unresolved_choice_ids == ()
    assert audit.status == "MECHANICAL_PILOT_CONFIGURATION_COMPLETE"
    assert audit.next_blocker == "NONE"
    assert assess_step_5j_3b_behavior_policy_readiness() == (
        "READY_TO_IMPLEMENT_REAL_MAPPO_BEHAVIOR_POLICY")


def test_contract_source_has_no_optimizer_training_operations():
    import negotiation_training.adam_contract as module

    source = inspect.getsource(module)
    assert "torch.optim.Adam(" not in source
    assert ".backward(" not in source
    assert ".step(" not in source
    contract = build_mechanical_adam_optimization_contract()
    assert contract.provenance["optimizer_instances"] == 0
    assert contract.provenance["backward_calls"] == 0
    assert contract.provenance["parameter_updates"] == 0
