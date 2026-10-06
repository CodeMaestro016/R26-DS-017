"""Step 5J.3B.1 architecture provenance and reproducibility tests."""

from dataclasses import FrozenInstanceError

import pytest
import torch

from experimentation import build_design
from negotiation_learning.ctde import (
    CentralizedNegotiationCritic, DecentralizedNegotiationActor,
    DecentralizedNegotiationResponseActor)
from negotiation_learning.gnn import EdgeAwareMPNNEncoder
from negotiation_training.architecture_contract import (
    apply_explicit_mechanical_initialization,
    build_mechanical_pilot_architecture_contract,
    deterministic_initialization_seed)


def _parameters(module):
    return tuple(item.detach().clone() for item in module.parameters())


def test_contract_is_immutable_post_freeze_and_not_selected():
    before = build_design()["freeze"].freeze_id
    contract = build_mechanical_pilot_architecture_contract()
    assert contract.frozen_design_id == before == build_design()["freeze"].freeze_id
    assert contract.mechanical_reference_only
    assert contract.project_selected is False
    assert contract.final_selection_eligible is False
    assert contract.unresolved_architecture_fields == ()
    with pytest.raises(FrozenInstanceError):
        contract.gnn_message_passing_layers = 2


def test_depth_is_profile_structural_reference_not_test_depth_promotion():
    contract = build_mechanical_pilot_architecture_contract()
    assert contract.gnn_depth_candidate_set == (1, 2, 3)
    assert contract.gnn_message_passing_layers == 3
    assert contract.gnn_depth_evidence["derivation"] == (
        "MAX_OBSERVED_NODE_COUNT_MINUS_ONE")
    assert contract.gnn_depth_evidence["maximum_observed_node_count"] == 4
    assert not contract.gnn_depth_evidence["claim_of_optimality"]
    assert not contract.gnn_depth_evidence["validation_only_depth_promoted"]


def test_existing_actor_and_critic_dimensions_introduce_no_hidden_layers():
    contract = build_mechanical_pilot_architecture_contract()
    proposer = DecentralizedNegotiationActor(contract.proposer_input_dimension, 2)
    responder = DecentralizedNegotiationResponseActor(
        contract.responder_input_dimension, 2)
    critic = CentralizedNegotiationCritic(contract.critic_input_dimension)
    assert contract.proposer_input_dimension == 162
    assert contract.responder_input_dimension == 180
    assert contract.critic_input_dimension == 64
    assert proposer.logit_head.in_features == 162 and proposer.logit_head.out_features == 2
    assert responder.logit_head.in_features == 180 and responder.logit_head.out_features == 2
    assert critic.value_head.in_features == 64 and critic.value_head.out_features == 1


def test_explicit_initialization_is_reproducible_from_supplied_identity():
    contract = build_mechanical_pilot_architecture_contract()
    identity = ("TEST_SUPPLIED_SEED_IDENTITY", contract.contract_id)
    seed = deterministic_initialization_seed(contract.contract_id, identity)
    first = EdgeAwareMPNNEncoder(8, 9, 64, 3)
    second = EdgeAwareMPNNEncoder(8, 9, 64, 3)
    apply_explicit_mechanical_initialization(first, seed)
    apply_explicit_mechanical_initialization(second, seed)
    assert all(torch.equal(a, b) for a, b in
               zip(_parameters(first), _parameters(second)))
    assert contract.initialization_evidence["silent_framework_default"] is False


def test_frozen_gnn_source_is_explicitly_mechanical_only():
    contract = build_mechanical_pilot_architecture_contract()
    assert contract.gnn_training_mode == "FROZEN_GNN"
    assert contract.frozen_gnn_parameter_source == (
        "DETERMINISTIC_EXPLICITLY_INITIALIZED_MECHANICAL_REPRESENTATION_ONLY")
    assert contract.provenance["training_performed"] is False
    assert contract.provenance["optimizer_instances"] == 0
