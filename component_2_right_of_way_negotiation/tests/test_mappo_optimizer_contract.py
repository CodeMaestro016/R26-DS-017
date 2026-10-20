"""Step 5J.3B.2 Adam provenance, grouping, and critic-reduction tests."""

# Import inspect for use in this module.
import inspect
# Import FrozenInstanceError from dataclasses for the operations below.
from dataclasses import FrozenInstanceError

# Import pytest for use in this module.
import pytest
# Import torch for use in this module.
import torch

# Import build_design from experimentation for the operations below.
from experimentation import build_design
# Import CentralizedNegotiationCritic, DecentralizedNegotiationActor, DecentralizedNegotiationResponseActor from
# negotiation_learning.ctde for the operations below.
from negotiation_learning.ctde import (
    CentralizedNegotiationCritic, DecentralizedNegotiationActor,
    DecentralizedNegotiationResponseActor)
# Import EdgeAwareMPNNEncoder from negotiation_learning.gnn for the operations below.
from negotiation_learning.gnn import EdgeAwareMPNNEncoder
# Import ADAM_PAPER_SOURCE, ORIGINAL_ADAM_MECHANICAL_REFERENCE, audit_parameter_membership,
# build_mechanical_adam_optimization_contract, joint_batch_critic_mean_squared_error from
# negotiation_training.adam_contract for the operations below.
from negotiation_training.adam_contract import (
    ADAM_PAPER_SOURCE, ORIGINAL_ADAM_MECHANICAL_REFERENCE,
    audit_parameter_membership, build_mechanical_adam_optimization_contract,
    joint_batch_critic_mean_squared_error)
# Import build_mechanical_pilot_architecture_contract from negotiation_training.architecture_contract for the
# operations below.
from negotiation_training.architecture_contract import (
    build_mechanical_pilot_architecture_contract)
# Import build_mechanical_pilot_configuration_audit from negotiation_training.optimizer_contract for the
# operations below.
from negotiation_training.optimizer_contract import (
    build_mechanical_pilot_configuration_audit)
# Import assess_step_5j_3b_behavior_policy_readiness from negotiation_training.readiness for the operations below.
from negotiation_training.readiness import (
    assess_step_5j_3b_behavior_policy_readiness)


# Models using the inputs and processing steps below.
# Output: a tuple containing the result of DecentralizedNegotiationActor(contract.proposer_input_dimension, 2),
# the result of...
def _models():
    # Set contract to the result of build_mechanical_pilot_architecture_contract().
    contract = build_mechanical_pilot_architecture_contract()
    # Return a tuple containing the result of DecentralizedNegotiationActor(contract.proposer_input_dimension, 2),
    # the result of... to the caller.
    return (
        # Include the result of DecentralizedNegotiationActor(contract.proposer_input_dimension, 2) in this tuple.
        DecentralizedNegotiationActor(contract.proposer_input_dimension, 2),
        # Include the result of DecentralizedNegotiationResponseActor(contract.responder_input_dimension, 2) in
        # this tuple.
        DecentralizedNegotiationResponseActor(
            # Supply contract.responder_input_dimension to DecentralizedNegotiationResponseActor.
            contract.responder_input_dimension, 2),
        # Include the result of CentralizedNegotiationCritic(contract.critic_input_dimension) in this tuple.
        CentralizedNegotiationCritic(contract.critic_input_dimension),
        # Include the result of EdgeAwareMPNNEncoder(8, 9, contract.gnn_hidden_dimension,
        # contract.gnn_message_passing_layers) in this tuple.
        EdgeAwareMPNNEncoder(8, 9, contract.gnn_hidden_dimension,
                             # Supply contract.gnn_message_passing_layers to EdgeAwareMPNNEncoder.
                             contract.gnn_message_passing_layers),
    )


# Check adam values have original reference provenance not optimality using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_adam_values_have_original_reference_provenance_not_optimality():
    # Set contract to the result of build_mechanical_adam_optimization_contract().
    contract = build_mechanical_adam_optimization_contract()
    # Require a tuple containing contract.beta1, contract.beta2, contract.epsilon equals a tuple containing 0.9,
    # 0.999, 1e-08; otherwise raise AssertionError.
    assert (contract.beta1, contract.beta2, contract.epsilon) == (0.9, 0.999, 1e-8)
    # Require contract.beta1_source equals contract.beta2_source; equals ADAM_PAPER_SOURCE; otherwise raise
    # AssertionError.
    assert contract.beta1_source == contract.beta2_source == ADAM_PAPER_SOURCE
    # Require contract.epsilon_source equals ADAM_PAPER_SOURCE; otherwise raise AssertionError.
    assert contract.epsilon_source == ADAM_PAPER_SOURCE
    # Require contract.provenance at 'beta_classification' equals ORIGINAL_ADAM_MECHANICAL_REFERENCE; otherwise
    # raise AssertionError.
    assert contract.provenance["beta_classification"] == ORIGINAL_ADAM_MECHANICAL_REFERENCE
    # Require contract.provenance at 'claimed_optimal' is the same object as False; otherwise raise
    # AssertionError.
    assert contract.provenance["claimed_optimal"] is False
    # Require contract.project_selected is the same object as False; otherwise raise AssertionError.
    assert contract.project_selected is False
    # Require contract.final_selection_eligible is the same object as False; otherwise raise AssertionError.
    assert contract.final_selection_eligible is False
    # Enter the result of pytest.raises(FrozenInstanceError) and run the enclosed operations within that context.
    with pytest.raises(FrozenInstanceError):
        # Set contract.beta1 to 0.8.
        contract.beta1 = 0.8


# Check plain adam has no added regularization or variant using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_plain_adam_has_no_added_regularization_or_variant():
    # Set contract to the result of build_mechanical_adam_optimization_contract().
    contract = build_mechanical_adam_optimization_contract()
    # Require contract.optimizer_family equals the text 'ADAM'; otherwise raise AssertionError.
    assert contract.optimizer_family == "ADAM"
    # Require contract.learning_rate equals 0.0005; otherwise raise AssertionError.
    assert contract.learning_rate == 0.0005
    # Require contract.weight_decay equals 0; otherwise raise AssertionError.
    assert contract.weight_decay == 0
    # Require contract.amsgrad is the same object as False; otherwise raise AssertionError.
    assert contract.amsgrad is False
    # Require the text 'ADAMW' does not belong to contract.weight_decay_semantics; otherwise raise AssertionError.
    assert "ADAMW" not in contract.weight_decay_semantics
    # Require contract.value_loss_mixing_coefficient equals the text 'NOT_APPLICABLE_SEPARATE_OPTIMIZERS';
    # otherwise raise AssertionError.
    assert contract.value_loss_mixing_coefficient == "NOT_APPLICABLE_SEPARATE_OPTIMIZERS"
    # Require contract.provenance at 'role_specific_optimizer_weights' equals 0; otherwise raise AssertionError.
    assert contract.provenance["role_specific_optimizer_weights"] == 0


# Check exact parameter sets are complete disjoint and exclude gnn using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_exact_parameter_sets_are_complete_disjoint_and_exclude_gnn():
    # Set (proposer, responder, critic, gnn) to the result of _models().
    proposer, responder, critic, gnn = _models()
    # Set membership to the result of audit_parameter_membership(proposer, responder, critic, gnn).
    membership = audit_parameter_membership(proposer, responder, critic, gnn)
    # Require membership at 'proposer' equals a tuple containing the text 'proposer_actor.logit_head.weight', the
    # text 'proposer_actor.logit_head.bias'; otherwise raise AssertionError.
    assert membership["proposer"] == (
        "proposer_actor.logit_head.weight", "proposer_actor.logit_head.bias")
    # Require membership at 'responder' equals a tuple containing the text 'responder_actor.logit_head.weight',
    # the text 'responder_actor.logit_head.bias'; otherwise raise AssertionError.
    assert membership["responder"] == (
        "responder_actor.logit_head.weight", "responder_actor.logit_head.bias")
    # Require membership at 'critic' equals a tuple containing the text 'centralized_critic.value_head.weight',
    # the text 'centralized_critic.value_head.bias'; otherwise raise AssertionError.
    assert membership["critic"] == (
        "centralized_critic.value_head.weight", "centralized_critic.value_head.bias")
    # Require membership at 'gnn'; otherwise raise AssertionError.
    assert membership["gnn"]
    # Require membership at 'duplicate_trainable_parameter_membership' equals 0; otherwise raise AssertionError.
    assert membership["duplicate_trainable_parameter_membership"] == 0


# Check critic loss is mean over joint batches not policy factors using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_critic_loss_is_mean_over_joint_batches_not_policy_factors():
    # Require the result of joint_batch_critic_mean_squared_error(torch.tensor([3.0]), torch.tensor([1.0])).item()
    # equals 4.0; otherwise raise AssertionError.
    assert joint_batch_critic_mean_squared_error(
        # Supply a tensor built from a list containing 3.0 to joint_batch_critic_mean_squared_error.
        torch.tensor([3.0]), torch.tensor([1.0])).item() == 4.0
    # Set actual to the result of joint_batch_critic_mean_squared_error(a tensor built from a list containing 1.0,
    # 3.0, a tensor built from a list containing 0.0, 1.0).
    actual = joint_batch_critic_mean_squared_error(
        # Supply a tensor built from a list containing 1.0, 3.0 to joint_batch_critic_mean_squared_error.
        torch.tensor([1.0, 3.0]), torch.tensor([0.0, 1.0]))
    # Require the result of actual.item() equals 2.5; otherwise raise AssertionError.
    assert actual.item() == 2.5
    # The function accepts exactly one value per joint state; no factor counts.
    # Require the number of entries in inspect.signature(joint_batch_critic_mean_squared_error).parameters equals
    # 2; otherwise raise AssertionError.
    assert len(inspect.signature(
        # Supply joint_batch_critic_mean_squared_error to inspect.signature.
        joint_batch_critic_mean_squared_error).parameters) == 2


# Check installed adam signature is exhaustively and explicitly audited using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_installed_adam_signature_is_exhaustively_and_explicitly_audited():
    # Set contract to the result of build_mechanical_adam_optimization_contract().
    contract = build_mechanical_adam_optimization_contract()
    # Set installed to a set built from inspect.signature(torch.optim.Adam).parameters.
    installed = set(inspect.signature(torch.optim.Adam).parameters)
    # Set audited to a set of item.name for item in contract.adam_argument_audit.
    audited = {item.name for item in contract.adam_argument_audit}
    # Require installed is at most audited; otherwise raise AssertionError.
    assert installed <= audited
    # Require whether every item is true in a lazy sequence of item.classification differs from the text
    # 'UNRESOLVED' for item in contract.adam_argument_audit; otherwise raise AssertionError.
    assert all(item.classification != "UNRESOLVED" for item in
               # Evaluate contract.adam_argument_audit as part of the enclosing expression.
               contract.adam_argument_audit)
    # Set values to a dictionary of item.name mapped to item.explicit_mechanical_value for item in
    # contract.adam_argument_audit.
    values = {item.name: item.explicit_mechanical_value for item in
              # Evaluate contract.adam_argument_audit as part of the enclosing expression.
              contract.adam_argument_audit}
    # Require values at 'foreach' equals values at 'fused'; equals the text 'False'; otherwise raise
    # AssertionError.
    assert values["foreach"] == values["fused"] == "False"
    # Require values at 'maximize' equals values at 'capturable'; equals the text 'False'; otherwise raise
    # AssertionError.
    assert values["maximize"] == values["capturable"] == "False"
    # Require values at 'differentiable' equals the text 'False'; otherwise raise AssertionError.
    assert values["differentiable"] == "False"
    # Require values at 'decoupled_weight_decay' equals the text 'False'; otherwise raise AssertionError.
    assert values["decoupled_weight_decay"] == "False"
    # Require contract.provenance at 'silent_adam_defaults' equals 0; otherwise raise AssertionError.
    assert contract.provenance["silent_adam_defaults"] == 0


# Check contracts preserve freeze and complete configuration readiness using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_contracts_preserve_freeze_and_complete_configuration_readiness():
    # Set before to build_design()['freeze'].freeze_id.
    before = build_design()["freeze"].freeze_id
    # Set optimization to the result of build_mechanical_adam_optimization_contract().
    optimization = build_mechanical_adam_optimization_contract()
    # Set architecture to the result of build_mechanical_pilot_architecture_contract().
    architecture = build_mechanical_pilot_architecture_contract()
    # Set audit to the result of build_mechanical_pilot_configuration_audit().
    audit = build_mechanical_pilot_configuration_audit()
    # Require before equals build_design()['freeze'].freeze_id; otherwise raise AssertionError.
    assert before == build_design()["freeze"].freeze_id
    # Require optimization.frozen_design_id equals architecture.frozen_design_id; equals before; otherwise raise
    # AssertionError.
    assert optimization.frozen_design_id == architecture.frozen_design_id == before
    # Require optimization.architecture_contract_id equals architecture.contract_id; otherwise raise
    # AssertionError.
    assert optimization.architecture_contract_id == architecture.contract_id
    # Require optimization.unresolved_optimizer_fields equals an empty tuple; otherwise raise AssertionError.
    assert optimization.unresolved_optimizer_fields == ()
    # Require audit.unresolved_choice_ids equals an empty tuple; otherwise raise AssertionError.
    assert audit.unresolved_choice_ids == ()
    # Require audit.status equals the text 'MECHANICAL_PILOT_CONFIGURATION_COMPLETE'; otherwise raise
    # AssertionError.
    assert audit.status == "MECHANICAL_PILOT_CONFIGURATION_COMPLETE"
    # Require audit.next_blocker equals the text 'NONE'; otherwise raise AssertionError.
    assert audit.next_blocker == "NONE"
    # Require the result of assess_step_5j_3b_behavior_policy_readiness() equals the text
    # 'READY_TO_IMPLEMENT_REAL_MAPPO_BEHAVIOR_POLICY'; otherwise raise AssertionError.
    assert assess_step_5j_3b_behavior_policy_readiness() == (
        "READY_TO_IMPLEMENT_REAL_MAPPO_BEHAVIOR_POLICY")


# Check contract source has no optimizer training operations using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_contract_source_has_no_optimizer_training_operations():
    # Import negotiation_training.adam_contract as module for use in this module.
    import negotiation_training.adam_contract as module

    # Set source to the result of inspect.getsource(module).
    source = inspect.getsource(module)
    # Require the text 'torch.optim.Adam(' does not belong to source; otherwise raise AssertionError.
    assert "torch.optim.Adam(" not in source
    # Require the text '.backward(' does not belong to source; otherwise raise AssertionError.
    assert ".backward(" not in source
    # Require the text '.step(' does not belong to source; otherwise raise AssertionError.
    assert ".step(" not in source
    # Set contract to the result of build_mechanical_adam_optimization_contract().
    contract = build_mechanical_adam_optimization_contract()
    # Require contract.provenance at 'optimizer_instances' equals 0; otherwise raise AssertionError.
    assert contract.provenance["optimizer_instances"] == 0
    # Require contract.provenance at 'backward_calls' equals 0; otherwise raise AssertionError.
    assert contract.provenance["backward_calls"] == 0
    # Require contract.provenance at 'parameter_updates' equals 0; otherwise raise AssertionError.
    assert contract.provenance["parameter_updates"] == 0
