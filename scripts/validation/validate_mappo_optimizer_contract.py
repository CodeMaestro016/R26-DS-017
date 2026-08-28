"""Validate Step 5J.3B.2 without constructing an optimizer or training."""

import json
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from pathlib import Path

import torch

from experimentation import build_design
from negotiation_learning.ctde import (
    CentralizedNegotiationCritic, DecentralizedNegotiationActor,
    DecentralizedNegotiationResponseActor)
from negotiation_learning.gnn import EdgeAwareMPNNEncoder
from negotiation_training import (
    assess_step_5j_3b_behavior_policy_readiness, audit_parameter_membership,
    build_mechanical_adam_optimization_contract,
    build_mechanical_pilot_architecture_contract,
    build_mechanical_pilot_configuration_audit,
    joint_batch_critic_mean_squared_error)

ARTIFACT = Path("results/mappo_optimizer_contract.json")


def _json(value):
    if is_dataclass(value):
        return {field.name: _json(getattr(value, field.name))
                for field in fields(value)}
    if isinstance(value, Mapping):
        return {str(key): _json(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)): return [_json(item) for item in value]
    return value


def main():
    before = build_design()["freeze"].freeze_id
    architecture = build_mechanical_pilot_architecture_contract()
    contract = build_mechanical_adam_optimization_contract()
    proposer = DecentralizedNegotiationActor(
        architecture.proposer_input_dimension, 2)
    responder = DecentralizedNegotiationResponseActor(
        architecture.responder_input_dimension, 2)
    critic = CentralizedNegotiationCritic(architecture.critic_input_dimension)
    gnn = EdgeAwareMPNNEncoder(
        8, 9, architecture.gnn_hidden_dimension,
        architecture.gnn_message_passing_layers)
    membership = audit_parameter_membership(proposer, responder, critic, gnn)
    single_loss = joint_batch_critic_mean_squared_error(
        torch.tensor([3.0]), torch.tensor([1.0]))
    multiple_loss = joint_batch_critic_mean_squared_error(
        torch.tensor([1.0, 3.0]), torch.tensor([0.0, 1.0]))
    audit = build_mechanical_pilot_configuration_audit()
    readiness = assess_step_5j_3b_behavior_policy_readiness()
    assert before == build_design()["freeze"].freeze_id == contract.frozen_design_id
    assert contract.architecture_contract_id == architecture.contract_id
    assert single_loss.item() == 4.0 and multiple_loss.item() == 2.5
    assert audit.unresolved_choice_ids == () and audit.silent_default_count == 0
    assert membership["duplicate_trainable_parameter_membership"] == 0
    payload = _json(contract)
    payload.update({
        "parameter_membership": _json(membership),
        "critic_loss_validation": {"single_batch": single_loss.item(),
                                   "multiple_batch": multiple_loss.item()},
        "policy_factor_count_used_for_critic_weighting": False,
        "frozen_design_changed": False,
        "configuration_status": audit.status,
        "remaining_unresolved_operational_parameters": 0,
        "next_blocker": audit.next_blocker,
        "next_readiness": readiness,
        "optimizer_instances": 0, "backward_calls": 0,
        "parameter_updates": 0,
    })
    ARTIFACT.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("Step 5J.3B.2 Adam + Critic Optimization Contract\n")
    print("Adam")
    print(f"  Optimizer family: {contract.optimizer_family}")
    print(f"  Learning rate: {contract.learning_rate}")
    print("  LR source: FROZEN_PILOT_CANDIDATE")
    print("  Project-selected LR: False")
    print(f"  beta1: {contract.beta1}")
    print(f"  beta2: {contract.beta2}")
    print(f"  epsilon: {contract.epsilon}")
    print("  Adam internal source: Kingma & Ba original Adam reference")
    print("  Values claimed project-optimal: False")
    print(f"  Weight decay: {contract.weight_decay:g}")
    print("  Weight-decay meaning: NO_ADDITIONAL_REGULARIZATION")
    print(f"  AMSGrad: {contract.amsgrad}")
    print("  Optimizer variant: PLAIN_ADAM\n")
    print("Parameter grouping")
    print("  Actor optimizer: proposer + responder trainable heads")
    print("  Critic optimizer: centralized critic")
    print("  Frozen GNN excluded: PASS")
    print("  Proposer parameter names:", list(membership["proposer"]))
    print("  Responder parameter names:", list(membership["responder"]))
    print("  Critic parameter names:", list(membership["critic"]))
    print("  GNN parameter names:", list(membership["gnn"]))
    print("  Duplicate trainable parameter membership: 0\n")
    print("Critic objective")
    print("  Form: squared error")
    print("  Reduction: PER_JOINT_DECISION_BATCH_EMPIRICAL_MEAN")
    print("  Policy factor count used for critic weighting: False")
    print("  Value-loss coefficient: NOT_USED\n")
    print("Framework defaults")
    print("  Silent Adam defaults accepted: 0")
    print(f"  Installed PyTorch: {contract.torch_version}")
    for item in contract.adam_argument_audit:
        print(f"  {item.name}: {item.explicit_mechanical_value} "
              f"[{item.classification}]")
    print("\nResearch boundary")
    print("  Mechanical reference only: True")
    print("  Project selected: False")
    print("  Final method selection eligible: False")
    print("  Frozen design changed: False\n")
    print("Training boundary")
    print("  Optimizer instantiated: False")
    print("  backward calls: 0")
    print("  Parameter updates: 0\n")
    print("Configuration")
    print("  Unresolved operational parameters: 0")
    print(f"  STEP_5J_3B_CONFIGURATION_STATUS: {audit.status}")
    print(f"  NEXT_BLOCKER: {audit.next_blocker}")
    print(f"  NEXT_READINESS: {readiness}")


if __name__ == "__main__": main()
