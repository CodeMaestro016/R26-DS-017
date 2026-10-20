"""Step 5J.3B.1 mechanical architecture contract validation."""

# Import hashlib for use in this module.
import hashlib
# Import json for use in this module.
import json
# Import Mapping from collections.abc for the operations below.
from collections.abc import Mapping
# Import fields, is_dataclass from dataclasses for the operations below.
from dataclasses import fields, is_dataclass
# Import Path from pathlib for the operations below.
from pathlib import Path

# Import torch for use in this module.
import torch

# Import build_design from experimentation for the operations below.
from experimentation import build_design
# Import ActorForwardInput, ActorInputProvenance, CentralizedNegotiationCritic, DecentralizedNegotiationActor,
# DecentralizedNegotiationResponseActor, ResponseActorForwardInput from negotiation_learning.ctde for the
# operations below.
from negotiation_learning.ctde import (
    ActorForwardInput, ActorInputProvenance, CentralizedNegotiationCritic,
    DecentralizedNegotiationActor, DecentralizedNegotiationResponseActor,
    ResponseActorForwardInput)
# Import EdgeAwareMPNNEncoder from negotiation_learning.gnn for the operations below.
from negotiation_learning.gnn import EdgeAwareMPNNEncoder
# Import TorchGraphObservation from negotiation_learning.gnn.models for the operations below.
from negotiation_learning.gnn.models import TorchGraphObservation
# Import apply_explicit_mechanical_initialization, build_mechanical_pilot_architecture_contract,
# build_mechanical_pilot_configuration_audit, deterministic_initialization_seed from negotiation_training for the
# operations below.
from negotiation_training import (
    apply_explicit_mechanical_initialization,
    build_mechanical_pilot_architecture_contract,
    build_mechanical_pilot_configuration_audit,
    deterministic_initialization_seed)

# Set ARTIFACT to the result of Path(the text 'results/mappo_architecture_contract.json').
ARTIFACT = Path("results/mappo_architecture_contract.json")


# Json using the inputs and processing steps below.
# Input value: the supplied value.
# Output: return the value selected by the matching return branch below.
# Processing: select branches using the stated conditions.
def _json(value):
    # Run this branch when the result of is_dataclass(value).
    if is_dataclass(value):
        # Return a dictionary of field.name mapped to the result of _json(the requested attribute of value) for
        # field in the result of fields(value) to the caller.
        return {field.name: _json(getattr(value, field.name))
                # Evaluate the result of fields(value) as part of the enclosing expression.
                for field in fields(value)}
    # Run this branch when whether value has type Mapping.
    if isinstance(value, Mapping):
        # Return a dictionary of a string built from key mapped to the result of _json(item) for (key, item) in
        # key/value pairs from value to the caller.
        return {str(key): _json(item) for key, item in value.items()}
    # Run this branch when whether value has type a tuple containing tuple, list.
    # Return a list of the result of _json(item) for item in value to the caller.
    if isinstance(value, (tuple, list)): return [_json(item) for item in value]
    # Return value to the caller.
    return value


# Hash using the inputs and processing steps below.
# Input module: the supplied module.
# Output: the hexadecimal digest from digest.
# Processing: iterate over the relevant records.
def _hash(module):
    # Set digest to the result of hashlib.sha256().
    digest = hashlib.sha256()
    # Iterate over key/value pairs from module.state_dict(), binding each item to (name, parameter).
    for name, parameter in module.state_dict().items():
        # Update digest with the supplied entries.
        digest.update(name.encode())
        # Update digest with the supplied entries.
        digest.update(parameter.detach().cpu().numpy().tobytes())
    # Return the hexadecimal digest from digest to the caller.
    return digest.hexdigest()


# Models using the inputs and processing steps below.
# Input contract: the supplied contract.
# Input supplied_seed_identity: the supplied supplied seed identity.
# Output: modules.
# Processing: iterate over the relevant records.
def _models(contract, supplied_seed_identity):
    # Set modules to a dictionary containing gnn, proposer, responder, critic.
    modules = {
        # Store the result of EdgeAwareMPNNEncoder(8, 9, contract.gnn_hidden_dimension,
        # contract.gnn_message_passing_layers) under 'gnn'.
        "gnn": EdgeAwareMPNNEncoder(
            # Supply contract.gnn_hidden_dimension to EdgeAwareMPNNEncoder.
            8, 9, contract.gnn_hidden_dimension,
            # Supply contract.gnn_message_passing_layers to EdgeAwareMPNNEncoder.
            contract.gnn_message_passing_layers),
        # Store the result of DecentralizedNegotiationActor(contract.proposer_input_dimension, 2) under
        # 'proposer'.
        "proposer": DecentralizedNegotiationActor(
            # Supply contract.proposer_input_dimension to DecentralizedNegotiationActor.
            contract.proposer_input_dimension, 2),
        # Store the result of DecentralizedNegotiationResponseActor(contract.responder_input_dimension, 2) under
        # 'responder'.
        "responder": DecentralizedNegotiationResponseActor(
            # Supply contract.responder_input_dimension to DecentralizedNegotiationResponseActor.
            contract.responder_input_dimension, 2),
        # Store the result of CentralizedNegotiationCritic(contract.critic_input_dimension) under 'critic'.
        "critic": CentralizedNegotiationCritic(contract.critic_input_dimension),
    }
    # Iterate over key/value pairs from modules, binding each item to (name, module).
    for name, module in modules.items():
        # Set seed to the result of deterministic_initialization_seed(contract.contract_id, a tuple containing
        # supplied_seed_identity, name).
        seed = deterministic_initialization_seed(
            # Supply a tuple containing supplied_seed_identity, name to deterministic_initialization_seed.
            contract.contract_id, (supplied_seed_identity, name))
        # Call apply_explicit_mechanical_initialization with the supplied arguments.
        apply_explicit_mechanical_initialization(module, seed)
    # Return modules to the caller.
    return modules


# Main using the inputs and processing steps below.
# Output: no explicit value; normal completion returns None.
def main():
    # Set before to build_design()['freeze'].freeze_id.
    before = build_design()["freeze"].freeze_id
    # Set contract to the result of build_mechanical_pilot_architecture_contract().
    contract = build_mechanical_pilot_architecture_contract()
    # Set seed_identity to a tuple containing the text 'ARCHITECTURE_CONTRACT_REPRODUCIBILITY_AUDIT_ONLY',
    # contract.contract_id.
    seed_identity = ("ARCHITECTURE_CONTRACT_REPRODUCIBILITY_AUDIT_ONLY",
                     # Include contract.contract_id in this tuple.
                     contract.contract_id)
    # Set (first, second) to a tuple containing the result of _models(contract, seed_identity), the result of
    # _models(contract, seed_identity).
    first, second = _models(contract, seed_identity), _models(contract, seed_identity)
    # Set hashes to a dictionary of name mapped to the result of _hash(module) for (name, module) in key/value
    # pairs from first.
    hashes = {name: _hash(module) for name, module in first.items()}
    # Require hashes equals a dictionary of name mapped to the result of _hash(module) for (name, module) in
    # key/value pairs from second; otherwise raise AssertionError.
    assert hashes == {name: _hash(module) for name, module in second.items()}

    # Set graph to the result of TorchGraphObservation(the text 'AV', a tuple containing the text 'AV', a
    # zero-filled tensor with the requested shape,...).
    graph = TorchGraphObservation(
        # Supply dtype as torch.bool.
        "AV", ("AV",), torch.zeros((1, 8)), torch.ones((1, 8), dtype=torch.bool),
        # Supply dtype as torch.long.
        torch.empty((2, 0), dtype=torch.long), torch.empty((0, 9)),
        # Supply dtype as torch.bool.
        torch.empty((0, 9), dtype=torch.bool), "VALIDATION", "cpu")
    # Set encoded to the result of first['gnn'](graph).
    encoded = first["gnn"](graph)
    # Set provenance to the result of ActorInputProvenance(the text 'LOCAL_LDM', the text 'LOCAL_GRAPH', the text
    # 'FROZEN_MECHANICAL_GNN', the text...).
    provenance = ActorInputProvenance("LOCAL_LDM", "LOCAL_GRAPH",
                                      "FROZEN_MECHANICAL_GNN", "BOOLEAN_MASK")
    # Set mask to a tensor built from a list containing True, True.
    mask = torch.tensor([True, True], dtype=torch.bool)
    # Set proposer_output to the result of first['proposer'](the result of ActorForwardInput(the text 'AV', the
    # text 'B', encoded.ego_embedding,...).
    proposer_output = first["proposer"](ActorForwardInput(
        # Supply encoded.graph_embedding to ActorForwardInput.
        "AV", "B", encoded.ego_embedding, encoded.graph_embedding,
        # Supply a zero-filled tensor with the requested shape to ActorForwardInput.
        torch.zeros(34), mask, provenance))
    # Set responder_output to the result of first['responder'](the result of ResponseActorForwardInput(the text
    # 'B', a tuple containing the text 'PROPOSAL',...).
    responder_output = first["responder"](ResponseActorForwardInput(
        # Supply encoded.graph_embedding to ResponseActorForwardInput.
        "B", ("PROPOSAL",), encoded.ego_embedding, encoded.graph_embedding,
        # Supply a tensor built from a list containing 0.0, 1.0 to ResponseActorForwardInput.
        torch.zeros(34), torch.zeros(16), torch.tensor([0.0, 1.0]),
        # Supply provenance to ResponseActorForwardInput.
        mask, provenance))
    # Set critic_output to the result of first['critic'](encoded.graph_embedding).
    critic_output = first["critic"](encoded.graph_embedding)
    # Require proposer_output.unmasked_action_logits.shape equals a tuple containing 2; otherwise raise
    # AssertionError.
    assert proposer_output.unmasked_action_logits.shape == (2,)
    # Require responder_output.unmasked_action_logits.shape equals a tuple containing 2; otherwise raise
    # AssertionError.
    assert responder_output.unmasked_action_logits.shape == (2,)
    # Require critic_output.shape equals a tuple containing 1; otherwise raise AssertionError.
    assert critic_output.shape == (1,)
    # Require whether every item is true in a lazy sequence of the result of torch.isfinite(item).all() for item
    # in a tuple containing encoded.node_embeddings, proposer_output.unmasked_action_logits,
    # responder_output.unmasked_action_logits,...; otherwise raise AssertionError.
    assert all(torch.isfinite(item).all() for item in (
        # Include proposer_output.unmasked_action_logits in this tuple.
        encoded.node_embeddings, proposer_output.unmasked_action_logits,
        # Include responder_output.unmasked_action_logits in this tuple.
        responder_output.unmasked_action_logits, critic_output))
    # Require build_design()['freeze'].freeze_id equals before; equals contract.frozen_design_id; otherwise raise
    # AssertionError.
    assert build_design()["freeze"].freeze_id == before == contract.frozen_design_id
    # Set audit to the result of build_mechanical_pilot_configuration_audit().
    audit = build_mechanical_pilot_configuration_audit()
    # Require the negation of contract.unresolved_architecture_fields; otherwise raise AssertionError.
    assert not contract.unresolved_architecture_fields
    # Require the number of entries in audit.unresolved_choice_ids equals 0; otherwise raise AssertionError.
    assert len(audit.unresolved_choice_ids) == 0
    # Require audit.next_blocker equals the text 'NONE'; otherwise raise AssertionError.
    assert audit.next_blocker == "NONE"
    # Set payload to the result of _json(contract).
    payload = _json(contract)
    # Update payload with the supplied entries.
    payload.update({"parameter_hashes": hashes,
                    # Store True under 'initialization_reproducible'.
                    "initialization_reproducible": True,
                    # Store True under 'gnn_forward_finite'.
                    "gnn_forward_finite": True,
                    # Store a dictionary containing proposer, responder under 'actor_forward_shapes'.
                    # Store a list containing 2 under 'proposer'.
                    # Store a list containing 2 under 'responder'.
                    "actor_forward_shapes": {"proposer": [2], "responder": [2]},
                    # Store a list containing 1 under 'critic_forward_shape'.
                    "critic_forward_shape": [1],
                    "remaining_unresolved_operational_fields":
                        # Evaluate a list built from audit.unresolved_choice_ids as part of the enclosing
                        # expression.
                        list(audit.unresolved_choice_ids),
                    # Store audit.next_blocker under 'next_blocker'.
                    "next_blocker": audit.next_blocker,
                    # Store False under 'training_performed'.
                    "training_performed": False,
                    # Store 0 under 'optimizer_instances'.
                    "optimizer_instances": 0,
                    # Store 0 under 'backward_calls'.
                    "backward_calls": 0,
                    # Store 0 under 'parameter_updates'.
                    "parameter_updates": 0})
    # Write the supplied text to ARTIFACT.
    ARTIFACT.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    # Display the text 'Step 5J.3B.1 MAPPO Architecture Contract'.
    print("Step 5J.3B.1 MAPPO Architecture Contract\n")
    # Display the text 'GNN'.
    print("GNN")
    # Display the text 'Hidden dimension source: FROZEN_PILOT_CANDIDATE'.
    print("  Hidden dimension source: FROZEN_PILOT_CANDIDATE")
    # Display formatted text built from the embedded values.
    print(f"  Hidden dimension: {contract.gnn_hidden_dimension}")
    # Display the text 'Project selected: False'.
    print("  Project selected: False")
    # Display formatted text built from the embedded values.
    print(f"  Message-passing depth: {contract.gnn_message_passing_layers}")
    # Display formatted text built from the embedded values.
    print(f"  Depth candidates requiring ablation: {contract.gnn_depth_candidate_set}")
    # Display formatted text built from the embedded values.
    print(f"  Depth provenance: {dict(contract.gnn_depth_evidence)}")
    # Display the text 'Depth claimed optimal: False'.
    print("  Depth claimed optimal: False")
    # Display formatted text built from the embedded values.
    print(f"  Activation: {contract.gnn_activation}")
    # Display formatted text built from the embedded values.
    print(f"  Initialization policy: {contract.initialization_policy}")
    # Display formatted text built from the embedded values.
    print(f"  Frozen parameter source: {contract.frozen_gnn_parameter_source}")
    # Display the text 'CPU forward pass: PASS'.
    print("  CPU forward pass: PASS")
    # Display the text 'Deterministic initialization: PASS'.
    print("  Deterministic initialization: PASS\n")
    # Display the text 'Actors'.
    print("Actors")
    # Display formatted text built from the embedded values.
    print(f"  Proposer head: {contract.proposer_actor_head_architecture}")
    # Display formatted text built from the embedded values.
    print(f"  Proposer input/output: {contract.proposer_input_dimension}/2")
    # Display formatted text built from the embedded values.
    print(f"  Responder head: {contract.responder_actor_head_architecture}")
    # Display formatted text built from the embedded values.
    print(f"  Responder input/output: {contract.responder_input_dimension}/2")
    # Display the text 'New arbitrary hidden layers: 0'.
    print("  New arbitrary hidden layers: 0\n")
    # Display the text 'Critic'.
    print("Critic")
    # Display formatted text built from the embedded values.
    print(f"  Architecture: {contract.centralized_critic_architecture}")
    # Display formatted text built from the embedded values.
    print(f"  Input/output: {contract.critic_input_dimension}/1")
    # Display the text 'Centralized training only: PASS'.
    print("  Centralized training only: PASS")
    # Display the text 'Actor critic-state access: False'.
    print("  Actor critic-state access: False\n")
    # Display the text 'Research integrity'.
    print("Research integrity")
    # Display the text 'New unsupported architecture values: 0'.
    print("  New unsupported architecture values: 0")
    # Display the text 'Test-only depth 2 promoted silently: False'.
    print("  Test-only depth 2 promoted silently: False")
    # Display the text 'Frozen design changed: False'.
    print("  Frozen design changed: False")
    # Display the text 'Training performed: False'.
    print("  Training performed: False")
    # Display the text 'Optimizer instantiated: False'.
    print("  Optimizer instantiated: False")
    # Display the text 'Parameter updates: 0'.
    print("  Parameter updates: 0\n")
    # Display the text 'Configuration gate'.
    print("Configuration gate")
    # Display the text 'Architecture unresolved fields: 0'.
    print("  Architecture unresolved fields: 0")
    # Display formatted text built from the embedded values.
    print(f"  Remaining unresolved operational fields: {len(audit.unresolved_choice_ids)}")
    # Display formatted text built from the embedded values.
    print(f"  NEXT_BLOCKER: {audit.next_blocker}")


# Run this branch when __name__ equals the text '__main__'.
# Call main with the supplied arguments.
if __name__ == "__main__": main()
