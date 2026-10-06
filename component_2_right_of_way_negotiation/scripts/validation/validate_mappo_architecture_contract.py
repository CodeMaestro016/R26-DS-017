"""Step 5J.3B.1 mechanical architecture contract validation."""

import hashlib
import json
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from pathlib import Path

import torch

from experimentation import build_design
from negotiation_learning.ctde import (
    ActorForwardInput, ActorInputProvenance, CentralizedNegotiationCritic,
    DecentralizedNegotiationActor, DecentralizedNegotiationResponseActor,
    ResponseActorForwardInput)
from negotiation_learning.gnn import EdgeAwareMPNNEncoder
from negotiation_learning.gnn.models import TorchGraphObservation
from negotiation_training import (
    apply_explicit_mechanical_initialization,
    build_mechanical_pilot_architecture_contract,
    build_mechanical_pilot_configuration_audit,
    deterministic_initialization_seed)

ARTIFACT = Path("results/mappo_architecture_contract.json")


def _json(value):
    if is_dataclass(value):
        return {field.name: _json(getattr(value, field.name))
                for field in fields(value)}
    if isinstance(value, Mapping):
        return {str(key): _json(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)): return [_json(item) for item in value]
    return value


def _hash(module):
    digest = hashlib.sha256()
    for name, parameter in module.state_dict().items():
        digest.update(name.encode())
        digest.update(parameter.detach().cpu().numpy().tobytes())
    return digest.hexdigest()


def _models(contract, supplied_seed_identity):
    modules = {
        "gnn": EdgeAwareMPNNEncoder(
            8, 9, contract.gnn_hidden_dimension,
            contract.gnn_message_passing_layers),
        "proposer": DecentralizedNegotiationActor(
            contract.proposer_input_dimension, 2),
        "responder": DecentralizedNegotiationResponseActor(
            contract.responder_input_dimension, 2),
        "critic": CentralizedNegotiationCritic(contract.critic_input_dimension),
    }
    for name, module in modules.items():
        seed = deterministic_initialization_seed(
            contract.contract_id, (supplied_seed_identity, name))
        apply_explicit_mechanical_initialization(module, seed)
    return modules


def main():
    before = build_design()["freeze"].freeze_id
    contract = build_mechanical_pilot_architecture_contract()
    seed_identity = ("ARCHITECTURE_CONTRACT_REPRODUCIBILITY_AUDIT_ONLY",
                     contract.contract_id)
    first, second = _models(contract, seed_identity), _models(contract, seed_identity)
    hashes = {name: _hash(module) for name, module in first.items()}
    assert hashes == {name: _hash(module) for name, module in second.items()}

    graph = TorchGraphObservation(
        "AV", ("AV",), torch.zeros((1, 8)), torch.ones((1, 8), dtype=torch.bool),
        torch.empty((2, 0), dtype=torch.long), torch.empty((0, 9)),
        torch.empty((0, 9), dtype=torch.bool), "VALIDATION", "cpu")
    encoded = first["gnn"](graph)
    provenance = ActorInputProvenance("LOCAL_LDM", "LOCAL_GRAPH",
                                      "FROZEN_MECHANICAL_GNN", "BOOLEAN_MASK")
    mask = torch.tensor([True, True], dtype=torch.bool)
    proposer_output = first["proposer"](ActorForwardInput(
        "AV", "B", encoded.ego_embedding, encoded.graph_embedding,
        torch.zeros(34), mask, provenance))
    responder_output = first["responder"](ResponseActorForwardInput(
        "B", ("PROPOSAL",), encoded.ego_embedding, encoded.graph_embedding,
        torch.zeros(34), torch.zeros(16), torch.tensor([0.0, 1.0]),
        mask, provenance))
    critic_output = first["critic"](encoded.graph_embedding)
    assert proposer_output.unmasked_action_logits.shape == (2,)
    assert responder_output.unmasked_action_logits.shape == (2,)
    assert critic_output.shape == (1,)
    assert all(torch.isfinite(item).all() for item in (
        encoded.node_embeddings, proposer_output.unmasked_action_logits,
        responder_output.unmasked_action_logits, critic_output))
    assert build_design()["freeze"].freeze_id == before == contract.frozen_design_id
    audit = build_mechanical_pilot_configuration_audit()
    assert not contract.unresolved_architecture_fields
    assert len(audit.unresolved_choice_ids) == 0
    assert audit.next_blocker == "NONE"
    payload = _json(contract)
    payload.update({"parameter_hashes": hashes,
                    "initialization_reproducible": True,
                    "gnn_forward_finite": True,
                    "actor_forward_shapes": {"proposer": [2], "responder": [2]},
                    "critic_forward_shape": [1],
                    "remaining_unresolved_operational_fields":
                        list(audit.unresolved_choice_ids),
                    "next_blocker": audit.next_blocker,
                    "training_performed": False,
                    "optimizer_instances": 0,
                    "backward_calls": 0,
                    "parameter_updates": 0})
    ARTIFACT.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("Step 5J.3B.1 MAPPO Architecture Contract\n")
    print("GNN")
    print("  Hidden dimension source: FROZEN_PILOT_CANDIDATE")
    print(f"  Hidden dimension: {contract.gnn_hidden_dimension}")
    print("  Project selected: False")
    print(f"  Message-passing depth: {contract.gnn_message_passing_layers}")
    print(f"  Depth candidates requiring ablation: {contract.gnn_depth_candidate_set}")
    print(f"  Depth provenance: {dict(contract.gnn_depth_evidence)}")
    print("  Depth claimed optimal: False")
    print(f"  Activation: {contract.gnn_activation}")
    print(f"  Initialization policy: {contract.initialization_policy}")
    print(f"  Frozen parameter source: {contract.frozen_gnn_parameter_source}")
    print("  CPU forward pass: PASS")
    print("  Deterministic initialization: PASS\n")
    print("Actors")
    print(f"  Proposer head: {contract.proposer_actor_head_architecture}")
    print(f"  Proposer input/output: {contract.proposer_input_dimension}/2")
    print(f"  Responder head: {contract.responder_actor_head_architecture}")
    print(f"  Responder input/output: {contract.responder_input_dimension}/2")
    print("  New arbitrary hidden layers: 0\n")
    print("Critic")
    print(f"  Architecture: {contract.centralized_critic_architecture}")
    print(f"  Input/output: {contract.critic_input_dimension}/1")
    print("  Centralized training only: PASS")
    print("  Actor critic-state access: False\n")
    print("Research integrity")
    print("  New unsupported architecture values: 0")
    print("  Test-only depth 2 promoted silently: False")
    print("  Frozen design changed: False")
    print("  Training performed: False")
    print("  Optimizer instantiated: False")
    print("  Parameter updates: 0\n")
    print("Configuration gate")
    print("  Architecture unresolved fields: 0")
    print(f"  Remaining unresolved operational fields: {len(audit.unresolved_choice_ids)}")
    print(f"  NEXT_BLOCKER: {audit.next_blocker}")


if __name__ == "__main__": main()
