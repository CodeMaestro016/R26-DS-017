"""Validate Step 5J.3B.2 without constructing an optimizer or training."""

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
# Import CentralizedNegotiationCritic, DecentralizedNegotiationActor, DecentralizedNegotiationResponseActor from
# negotiation_learning.ctde for the operations below.
from negotiation_learning.ctde import (
    CentralizedNegotiationCritic, DecentralizedNegotiationActor,
    DecentralizedNegotiationResponseActor)
# Import EdgeAwareMPNNEncoder from negotiation_learning.gnn for the operations below.
from negotiation_learning.gnn import EdgeAwareMPNNEncoder
# Import assess_step_5j_3b_behavior_policy_readiness, audit_parameter_membership,
# build_mechanical_adam_optimization_contract, build_mechanical_pilot_architecture_contract,... from
# negotiation_training for the operations below.
from negotiation_training import (
    assess_step_5j_3b_behavior_policy_readiness, audit_parameter_membership,
    build_mechanical_adam_optimization_contract,
    build_mechanical_pilot_architecture_contract,
    build_mechanical_pilot_configuration_audit,
    joint_batch_critic_mean_squared_error)

# Set ARTIFACT to the result of Path(the text 'results/mappo_optimizer_contract.json').
ARTIFACT = Path("results/mappo_optimizer_contract.json")


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


# Main using the inputs and processing steps below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def main():
    # Set before to build_design()['freeze'].freeze_id.
    before = build_design()["freeze"].freeze_id
    # Set architecture to the result of build_mechanical_pilot_architecture_contract().
    architecture = build_mechanical_pilot_architecture_contract()
    # Set contract to the result of build_mechanical_adam_optimization_contract().
    contract = build_mechanical_adam_optimization_contract()
    # Set proposer to the result of DecentralizedNegotiationActor(architecture.proposer_input_dimension, 2).
    proposer = DecentralizedNegotiationActor(
        # Supply architecture.proposer_input_dimension to DecentralizedNegotiationActor.
        architecture.proposer_input_dimension, 2)
    # Set responder to the result of DecentralizedNegotiationResponseActor(architecture.responder_input_dimension,
    # 2).
    responder = DecentralizedNegotiationResponseActor(
        # Supply architecture.responder_input_dimension to DecentralizedNegotiationResponseActor.
        architecture.responder_input_dimension, 2)
    # Set critic to the result of CentralizedNegotiationCritic(architecture.critic_input_dimension).
    critic = CentralizedNegotiationCritic(architecture.critic_input_dimension)
    # Set gnn to the result of EdgeAwareMPNNEncoder(8, 9, architecture.gnn_hidden_dimension,
    # architecture.gnn_message_passing_layers).
    gnn = EdgeAwareMPNNEncoder(
        # Supply architecture.gnn_hidden_dimension to EdgeAwareMPNNEncoder.
        8, 9, architecture.gnn_hidden_dimension,
        # Supply architecture.gnn_message_passing_layers to EdgeAwareMPNNEncoder.
        architecture.gnn_message_passing_layers)
    # Set membership to the result of audit_parameter_membership(proposer, responder, critic, gnn).
    membership = audit_parameter_membership(proposer, responder, critic, gnn)
    # Set single_loss to the result of joint_batch_critic_mean_squared_error(a tensor built from a list containing
    # 3.0, a tensor built from a list containing 1.0).
    single_loss = joint_batch_critic_mean_squared_error(
        # Supply a tensor built from a list containing 3.0 to joint_batch_critic_mean_squared_error.
        torch.tensor([3.0]), torch.tensor([1.0]))
    # Set multiple_loss to the result of joint_batch_critic_mean_squared_error(a tensor built from a list
    # containing 1.0, 3.0, a tensor built from a list containing 0.0, 1.0).
    multiple_loss = joint_batch_critic_mean_squared_error(
        # Supply a tensor built from a list containing 1.0, 3.0 to joint_batch_critic_mean_squared_error.
        torch.tensor([1.0, 3.0]), torch.tensor([0.0, 1.0]))
    # Set audit to the result of build_mechanical_pilot_configuration_audit().
    audit = build_mechanical_pilot_configuration_audit()
    # Set readiness to the result of assess_step_5j_3b_behavior_policy_readiness().
    readiness = assess_step_5j_3b_behavior_policy_readiness()
    # Require before equals build_design()['freeze'].freeze_id; equals contract.frozen_design_id; otherwise raise
    # AssertionError.
    assert before == build_design()["freeze"].freeze_id == contract.frozen_design_id
    # Require contract.architecture_contract_id equals architecture.contract_id; otherwise raise AssertionError.
    assert contract.architecture_contract_id == architecture.contract_id
    # Require the result of single_loss.item() equals 4.0 and the result of multiple_loss.item() equals 2.5;
    # otherwise raise AssertionError.
    assert single_loss.item() == 4.0 and multiple_loss.item() == 2.5
    # Require audit.unresolved_choice_ids equals an empty tuple and audit.silent_default_count equals 0; otherwise
    # raise AssertionError.
    assert audit.unresolved_choice_ids == () and audit.silent_default_count == 0
    # Require membership at 'duplicate_trainable_parameter_membership' equals 0; otherwise raise AssertionError.
    assert membership["duplicate_trainable_parameter_membership"] == 0
    # Set payload to the result of _json(contract).
    payload = _json(contract)
    # Update payload with the supplied entries.
    payload.update({
        # Store the result of _json(membership) under 'parameter_membership'.
        "parameter_membership": _json(membership),
        # Store a dictionary containing single_batch, multiple_batch under 'critic_loss_validation'.
        # Store the result of single_loss.item() under 'single_batch'.
        "critic_loss_validation": {"single_batch": single_loss.item(),
                                   # Store the result of multiple_loss.item() under 'multiple_batch'.
                                   "multiple_batch": multiple_loss.item()},
        # Store False under 'policy_factor_count_used_for_critic_weighting'.
        "policy_factor_count_used_for_critic_weighting": False,
        # Store False under 'frozen_design_changed'.
        "frozen_design_changed": False,
        # Store audit.status under 'configuration_status'.
        "configuration_status": audit.status,
        # Store 0 under 'remaining_unresolved_operational_parameters'.
        "remaining_unresolved_operational_parameters": 0,
        # Store audit.next_blocker under 'next_blocker'.
        "next_blocker": audit.next_blocker,
        # Store readiness under 'next_readiness'.
        "next_readiness": readiness,
        # Store 0 under 'optimizer_instances'.
        # Store 0 under 'backward_calls'.
        "optimizer_instances": 0, "backward_calls": 0,
        # Store 0 under 'parameter_updates'.
        "parameter_updates": 0,
    })
    # Write the supplied text to ARTIFACT.
    ARTIFACT.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    # Display the text 'Step 5J.3B.2 Adam + Critic Optimization Contract'.
    print("Step 5J.3B.2 Adam + Critic Optimization Contract\n")
    # Display the text 'Adam'.
    print("Adam")
    # Display formatted text built from the embedded values.
    print(f"  Optimizer family: {contract.optimizer_family}")
    # Display formatted text built from the embedded values.
    print(f"  Learning rate: {contract.learning_rate}")
    # Display the text 'LR source: FROZEN_PILOT_CANDIDATE'.
    print("  LR source: FROZEN_PILOT_CANDIDATE")
    # Display the text 'Project-selected LR: False'.
    print("  Project-selected LR: False")
    # Display formatted text built from the embedded values.
    print(f"  beta1: {contract.beta1}")
    # Display formatted text built from the embedded values.
    print(f"  beta2: {contract.beta2}")
    # Display formatted text built from the embedded values.
    print(f"  epsilon: {contract.epsilon}")
    # Display the text 'Adam internal source: Kingma & Ba original Adam reference'.
    print("  Adam internal source: Kingma & Ba original Adam reference")
    # Display the text 'Values claimed project-optimal: False'.
    print("  Values claimed project-optimal: False")
    # Display formatted text built from the embedded values.
    print(f"  Weight decay: {contract.weight_decay:g}")
    # Display the text 'Weight-decay meaning: NO_ADDITIONAL_REGULARIZATION'.
    print("  Weight-decay meaning: NO_ADDITIONAL_REGULARIZATION")
    # Display formatted text built from the embedded values.
    print(f"  AMSGrad: {contract.amsgrad}")
    # Display the text 'Optimizer variant: PLAIN_ADAM'.
    print("  Optimizer variant: PLAIN_ADAM\n")
    # Display the text 'Parameter grouping'.
    print("Parameter grouping")
    # Display the text 'Actor optimizer: proposer + responder trainable heads'.
    print("  Actor optimizer: proposer + responder trainable heads")
    # Display the text 'Critic optimizer: centralized critic'.
    print("  Critic optimizer: centralized critic")
    # Display the text 'Frozen GNN excluded: PASS'.
    print("  Frozen GNN excluded: PASS")
    # Display the text 'Proposer parameter names:'.
    print("  Proposer parameter names:", list(membership["proposer"]))
    # Display the text 'Responder parameter names:'.
    print("  Responder parameter names:", list(membership["responder"]))
    # Display the text 'Critic parameter names:'.
    print("  Critic parameter names:", list(membership["critic"]))
    # Display the text 'GNN parameter names:'.
    print("  GNN parameter names:", list(membership["gnn"]))
    # Display the text 'Duplicate trainable parameter membership: 0'.
    print("  Duplicate trainable parameter membership: 0\n")
    # Display the text 'Critic objective'.
    print("Critic objective")
    # Display the text 'Form: squared error'.
    print("  Form: squared error")
    # Display the text 'Reduction: PER_JOINT_DECISION_BATCH_EMPIRICAL_MEAN'.
    print("  Reduction: PER_JOINT_DECISION_BATCH_EMPIRICAL_MEAN")
    # Display the text 'Policy factor count used for critic weighting: False'.
    print("  Policy factor count used for critic weighting: False")
    # Display the text 'Value-loss coefficient: NOT_USED'.
    print("  Value-loss coefficient: NOT_USED\n")
    # Display the text 'Framework defaults'.
    print("Framework defaults")
    # Display the text 'Silent Adam defaults accepted: 0'.
    print("  Silent Adam defaults accepted: 0")
    # Display formatted text built from the embedded values.
    print(f"  Installed PyTorch: {contract.torch_version}")
    # Iterate over contract.adam_argument_audit, binding each item to item.
    for item in contract.adam_argument_audit:
        # Display formatted text built from the embedded values.
        print(f"  {item.name}: {item.explicit_mechanical_value} "
              # Evaluate {item.classification} as part of the enclosing expression.
              f"[{item.classification}]")
    # Display the text 'Research boundary'.
    print("\nResearch boundary")
    # Display the text 'Mechanical reference only: True'.
    print("  Mechanical reference only: True")
    # Display the text 'Project selected: False'.
    print("  Project selected: False")
    # Display the text 'Final method selection eligible: False'.
    print("  Final method selection eligible: False")
    # Display the text 'Frozen design changed: False'.
    print("  Frozen design changed: False\n")
    # Display the text 'Training boundary'.
    print("Training boundary")
    # Display the text 'Optimizer instantiated: False'.
    print("  Optimizer instantiated: False")
    # Display the text 'backward calls: 0'.
    print("  backward calls: 0")
    # Display the text 'Parameter updates: 0'.
    print("  Parameter updates: 0\n")
    # Display the text 'Configuration'.
    print("Configuration")
    # Display the text 'Unresolved operational parameters: 0'.
    print("  Unresolved operational parameters: 0")
    # Display formatted text built from the embedded values.
    print(f"  STEP_5J_3B_CONFIGURATION_STATUS: {audit.status}")
    # Display formatted text built from the embedded values.
    print(f"  NEXT_BLOCKER: {audit.next_blocker}")
    # Display formatted text built from the embedded values.
    print(f"  NEXT_READINESS: {readiness}")


# Run this branch when __name__ equals the text '__main__'.
# Call main with the supplied arguments.
if __name__ == "__main__": main()
