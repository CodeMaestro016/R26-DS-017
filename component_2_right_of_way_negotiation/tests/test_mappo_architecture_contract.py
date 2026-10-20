"""Step 5J.3B.1 architecture provenance and reproducibility tests."""

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
# Import apply_explicit_mechanical_initialization, build_mechanical_pilot_architecture_contract,
# deterministic_initialization_seed from negotiation_training.architecture_contract for the operations below.
from negotiation_training.architecture_contract import (
    apply_explicit_mechanical_initialization,
    build_mechanical_pilot_architecture_contract,
    deterministic_initialization_seed)


# Parameters using the inputs and processing steps below.
# Input module: the supplied module.
# Output: a tuple built from a lazy sequence of the result of item.detach().clone() for item in the result of
# module.parameters().
def _parameters(module):
    # Return a tuple built from a lazy sequence of the result of item.detach().clone() for item in the result of
    # module.parameters() to the caller.
    return tuple(item.detach().clone() for item in module.parameters())


# Check contract is immutable post freeze and not selected using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_contract_is_immutable_post_freeze_and_not_selected():
    # Set before to build_design()['freeze'].freeze_id.
    before = build_design()["freeze"].freeze_id
    # Set contract to the result of build_mechanical_pilot_architecture_contract().
    contract = build_mechanical_pilot_architecture_contract()
    # Require contract.frozen_design_id equals before; equals build_design()['freeze'].freeze_id; otherwise raise
    # AssertionError.
    assert contract.frozen_design_id == before == build_design()["freeze"].freeze_id
    # Require contract.mechanical_reference_only; otherwise raise AssertionError.
    assert contract.mechanical_reference_only
    # Require contract.project_selected is the same object as False; otherwise raise AssertionError.
    assert contract.project_selected is False
    # Require contract.final_selection_eligible is the same object as False; otherwise raise AssertionError.
    assert contract.final_selection_eligible is False
    # Require contract.unresolved_architecture_fields equals an empty tuple; otherwise raise AssertionError.
    assert contract.unresolved_architecture_fields == ()
    # Enter the result of pytest.raises(FrozenInstanceError) and run the enclosed operations within that context.
    with pytest.raises(FrozenInstanceError):
        # Set contract.gnn_message_passing_layers to 2.
        contract.gnn_message_passing_layers = 2


# Check depth is profile structural reference not test depth promotion using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_depth_is_profile_structural_reference_not_test_depth_promotion():
    # Set contract to the result of build_mechanical_pilot_architecture_contract().
    contract = build_mechanical_pilot_architecture_contract()
    # Require contract.gnn_depth_candidate_set equals a tuple containing 1, 2, 3; otherwise raise AssertionError.
    assert contract.gnn_depth_candidate_set == (1, 2, 3)
    # Require contract.gnn_message_passing_layers equals 3; otherwise raise AssertionError.
    assert contract.gnn_message_passing_layers == 3
    # Require contract.gnn_depth_evidence at 'derivation' equals the text 'MAX_OBSERVED_NODE_COUNT_MINUS_ONE';
    # otherwise raise AssertionError.
    assert contract.gnn_depth_evidence["derivation"] == (
        "MAX_OBSERVED_NODE_COUNT_MINUS_ONE")
    # Require contract.gnn_depth_evidence at 'maximum_observed_node_count' equals 4; otherwise raise
    # AssertionError.
    assert contract.gnn_depth_evidence["maximum_observed_node_count"] == 4
    # Require the negation of contract.gnn_depth_evidence at 'claim_of_optimality'; otherwise raise
    # AssertionError.
    assert not contract.gnn_depth_evidence["claim_of_optimality"]
    # Require the negation of contract.gnn_depth_evidence at 'validation_only_depth_promoted'; otherwise raise
    # AssertionError.
    assert not contract.gnn_depth_evidence["validation_only_depth_promoted"]


# Check existing actor and critic dimensions introduce no hidden layers using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_existing_actor_and_critic_dimensions_introduce_no_hidden_layers():
    # Set contract to the result of build_mechanical_pilot_architecture_contract().
    contract = build_mechanical_pilot_architecture_contract()
    # Set proposer to the result of DecentralizedNegotiationActor(contract.proposer_input_dimension, 2).
    proposer = DecentralizedNegotiationActor(contract.proposer_input_dimension, 2)
    # Set responder to the result of DecentralizedNegotiationResponseActor(contract.responder_input_dimension, 2).
    responder = DecentralizedNegotiationResponseActor(
        # Supply contract.responder_input_dimension to DecentralizedNegotiationResponseActor.
        contract.responder_input_dimension, 2)
    # Set critic to the result of CentralizedNegotiationCritic(contract.critic_input_dimension).
    critic = CentralizedNegotiationCritic(contract.critic_input_dimension)
    # Require contract.proposer_input_dimension equals 162; otherwise raise AssertionError.
    assert contract.proposer_input_dimension == 162
    # Require contract.responder_input_dimension equals 180; otherwise raise AssertionError.
    assert contract.responder_input_dimension == 180
    # Require contract.critic_input_dimension equals 64; otherwise raise AssertionError.
    assert contract.critic_input_dimension == 64
    # Require proposer.logit_head.in_features equals 162 and proposer.logit_head.out_features equals 2; otherwise
    # raise AssertionError.
    assert proposer.logit_head.in_features == 162 and proposer.logit_head.out_features == 2
    # Require responder.logit_head.in_features equals 180 and responder.logit_head.out_features equals 2;
    # otherwise raise AssertionError.
    assert responder.logit_head.in_features == 180 and responder.logit_head.out_features == 2
    # Require critic.value_head.in_features equals 64 and critic.value_head.out_features equals 1; otherwise raise
    # AssertionError.
    assert critic.value_head.in_features == 64 and critic.value_head.out_features == 1


# Check explicit initialization is reproducible from supplied identity using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_explicit_initialization_is_reproducible_from_supplied_identity():
    # Set contract to the result of build_mechanical_pilot_architecture_contract().
    contract = build_mechanical_pilot_architecture_contract()
    # Set identity to a tuple containing the text 'TEST_SUPPLIED_SEED_IDENTITY', contract.contract_id.
    identity = ("TEST_SUPPLIED_SEED_IDENTITY", contract.contract_id)
    # Set seed to the result of deterministic_initialization_seed(contract.contract_id, identity).
    seed = deterministic_initialization_seed(contract.contract_id, identity)
    # Set first to the result of EdgeAwareMPNNEncoder(8, 9, 64, 3).
    first = EdgeAwareMPNNEncoder(8, 9, 64, 3)
    # Set second to the result of EdgeAwareMPNNEncoder(8, 9, 64, 3).
    second = EdgeAwareMPNNEncoder(8, 9, 64, 3)
    # Call apply_explicit_mechanical_initialization with the supplied arguments.
    apply_explicit_mechanical_initialization(first, seed)
    # Call apply_explicit_mechanical_initialization with the supplied arguments.
    apply_explicit_mechanical_initialization(second, seed)
    # Require whether every item is true in a lazy sequence of the result of torch.equal(a, b) for (a, b) in
    # corresponding items paired from the result of _parameters(first), the result of _parameters(second);
    # otherwise raise AssertionError.
    assert all(torch.equal(a, b) for a, b in
               # Evaluate corresponding items paired from the result of _parameters(first), the result of
               # _parameters(second) as part of the enclosing expression.
               zip(_parameters(first), _parameters(second)))
    # Require contract.initialization_evidence at 'silent_framework_default' is the same object as False;
    # otherwise raise AssertionError.
    assert contract.initialization_evidence["silent_framework_default"] is False


# Check frozen gnn source is explicitly mechanical only using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_frozen_gnn_source_is_explicitly_mechanical_only():
    # Set contract to the result of build_mechanical_pilot_architecture_contract().
    contract = build_mechanical_pilot_architecture_contract()
    # Require contract.gnn_training_mode equals the text 'FROZEN_GNN'; otherwise raise AssertionError.
    assert contract.gnn_training_mode == "FROZEN_GNN"
    # Require contract.frozen_gnn_parameter_source equals the text
    # 'DETERMINISTIC_EXPLICITLY_INITIALIZED_MECHANICAL_REPRESENTATION...'; otherwise raise AssertionError.
    assert contract.frozen_gnn_parameter_source == (
        "DETERMINISTIC_EXPLICITLY_INITIALIZED_MECHANICAL_REPRESENTATION_ONLY")
    # Require contract.provenance at 'training_performed' is the same object as False; otherwise raise
    # AssertionError.
    assert contract.provenance["training_performed"] is False
    # Require contract.provenance at 'optimizer_instances' equals 0; otherwise raise AssertionError.
    assert contract.provenance["optimizer_instances"] == 0
