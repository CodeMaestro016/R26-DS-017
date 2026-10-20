"""Post-freeze evidence-backed mechanical architecture contract."""

# Import hashlib for use in this module.
import hashlib
# Import json for use in this module.
import json
# Import math for use in this module.
import math
# Import dataclass from dataclasses for the operations below.
from dataclasses import dataclass
# Import Path from pathlib for the operations below.
from pathlib import Path
# Import MappingProxyType from types for the operations below.
from types import MappingProxyType
# Import Mapping, Tuple from typing for the operations below.
from typing import Mapping, Tuple

# Import build_design from experimentation for the operations below.
from experimentation import build_design


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define MechanicalPilotArchitectureContract to group the state and operations declared below.
# Declared fields: contract_id, frozen_design_id, gnn_hidden_dimension, gnn_hidden_dimension_evidence_id,
# gnn_message_passing_layers, gnn_depth_candidate_set, gnn_depth_evidence, gnn_activation,
# initialization_policy,....
# Construction and attribute behavior follow the declared decorators and base classes.
class MechanicalPilotArchitectureContract:
    # Declare contract_id as tuple for this data structure.
    contract_id: tuple
    # Declare frozen_design_id as tuple for this data structure.
    frozen_design_id: tuple
    # Declare gnn_hidden_dimension as int for this data structure.
    gnn_hidden_dimension: int
    # Declare gnn_hidden_dimension_evidence_id as tuple for this data structure.
    gnn_hidden_dimension_evidence_id: tuple
    # Declare gnn_message_passing_layers as int for this data structure.
    gnn_message_passing_layers: int
    # Declare gnn_depth_candidate_set as Tuple[int, ...] for this data structure.
    gnn_depth_candidate_set: Tuple[int, ...]
    # Declare gnn_depth_evidence as Mapping for this data structure.
    gnn_depth_evidence: Mapping
    # Declare gnn_activation as str for this data structure.
    gnn_activation: str
    # Declare initialization_policy as str for this data structure.
    initialization_policy: str
    # Declare initialization_evidence as Mapping for this data structure.
    initialization_evidence: Mapping
    # Declare gnn_training_mode as str for this data structure.
    gnn_training_mode: str
    # Declare frozen_gnn_parameter_source as str for this data structure.
    frozen_gnn_parameter_source: str
    # Declare proposer_actor_head_architecture as str for this data structure.
    proposer_actor_head_architecture: str
    # Declare responder_actor_head_architecture as str for this data structure.
    responder_actor_head_architecture: str
    # Declare centralized_critic_architecture as str for this data structure.
    centralized_critic_architecture: str
    # Declare proposer_input_dimension as int for this data structure.
    proposer_input_dimension: int
    # Declare responder_input_dimension as int for this data structure.
    responder_input_dimension: int
    # Declare critic_input_dimension as int for this data structure.
    critic_input_dimension: int
    # Declare parameter_sharing_strategy as str for this data structure.
    parameter_sharing_strategy: str
    # Declare mechanical_reference_only as bool for this data structure.
    mechanical_reference_only: bool
    # Declare project_selected as bool for this data structure.
    project_selected: bool
    # Declare final_selection_eligible as bool for this data structure.
    final_selection_eligible: bool
    # Declare unresolved_architecture_fields as Tuple[str, ...] for this data structure.
    unresolved_architecture_fields: Tuple[str, ...]
    # Declare provenance as Mapping for this data structure.
    provenance: Mapping

    # Post init using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    # Processing: iterate over the relevant records.
    def __post_init__(self):
        # Iterate over a tuple containing the text 'gnn_depth_evidence', the text 'initialization_evidence', the
        # text 'provenance', binding each item to name.
        for name in ("gnn_depth_evidence", "initialization_evidence", "provenance"):
            # Call object.__setattr__ with the supplied arguments.
            object.__setattr__(self, name,
                               # Supply the result of MappingProxyType(a dictionary built from the requested
                               # attribute of self) to object.__setattr__.
                               MappingProxyType(dict(getattr(self, name))))


# Build mechanical pilot architecture contract using the inputs and processing steps below.
# Input profile_path: the supplied profile path.
# Output: the result of MechanicalPilotArchitectureContract(a tuple containing the text
# 'MECHANICAL_PILOT_ARCHITECTURE_CONTRACT_V1', the hexadecimal digest...).
# Processing: select branches using the stated conditions.
def build_mechanical_pilot_architecture_contract(
        # Declare profile_path as input parameter.
        profile_path="results/coupled_environment_profile.json"):
    # Set design to the result of build_design().
    design = build_design()
    # Set profile to the decoded data produced by json.loads from the text read from Path(profile_path).
    profile = json.loads(Path(profile_path).read_text(encoding="utf-8"))
    # Run this branch when 'status' from profile; use None if absent differs from the text
    # 'COUPLED_ENVIRONMENT_PROFILE_COMPLETE'.
    if profile.get("status") != "COUPLED_ENVIRONMENT_PROFILE_COMPLETE":
        # Raise ValueError with the text 'STEP_5J_3A_PROFILE_NOT_COMPLETE' to stop this execution path.
        raise ValueError("STEP_5J_3A_PROFILE_NOT_COMPLETE")
    # Set assignments to a dictionary of item.choice_id mapped to item for item in
    # design['provisional'].assignments.
    assignments = {item.choice_id: item for item in
                   # Evaluate design['provisional'].assignments as part of the enclosing expression.
                   design["provisional"].assignments}
    # Set hidden to assignments at 'gnn_hidden_dimension'.
    hidden = assignments["gnn_hidden_dimension"]
    # Set training_mode to assignments at 'gnn_training_mode'.
    training_mode = assignments["gnn_training_mode"]
    # Set sharing to assignments at 'parameter_sharing_strategy'.
    sharing = assignments["parameter_sharing_strategy"]
    # Set observed_node_counts to a tuple built from a lazy sequence of shape[0] at 0 for episode in profile at
    # 'episodes'.
    observed_node_counts = tuple(
        # Evaluate profile at 'episodes' as part of the enclosing expression.
        shape[0][0] for episode in profile["episodes"]
        # Evaluate episode at 'joint_decision_batches' as part of the enclosing expression.
        for batch in episode["joint_decision_batches"]
        # Evaluate batch at 'encoded_graph_shapes' as part of the enclosing expression.
        for shape in batch["encoded_graph_shapes"])
    # Set maximum_nodes to the maximum of observed_node_counts.
    maximum_nodes = max(observed_node_counts)
    # Set maximum_simple_path_edges to maximum_nodes minus 1.
    maximum_simple_path_edges = maximum_nodes - 1
    # Set depth_candidates to a tuple built from the integer range defined by 1, maximum_simple_path_edges plus 1.
    depth_candidates = tuple(range(1, maximum_simple_path_edges + 1))
    # Set mechanical_depth to maximum_simple_path_edges.
    mechanical_depth = maximum_simple_path_edges
    # Set (node_dim, edge_dim) to a tuple containing 8, 9.
    node_dim, edge_dim = 8, 9
    # Set (claim_dim, protocol_dim, role_dim) to a tuple containing 2 multiplied by node_dim plus edge_dim, 16, 2.
    claim_dim, protocol_dim, role_dim = 2 * (node_dim + edge_dim), 16, 2
    # Set proposer_input to 2 multiplied by hidden.candidate_value_or_method plus claim_dim.
    proposer_input = 2 * hidden.candidate_value_or_method + claim_dim
    # Set responder_input to proposer_input plus protocol_dim plus role_dim.
    responder_input = proposer_input + protocol_dim + role_dim
    # Set critic_input to hidden.candidate_value_or_method.
    critic_input = hidden.candidate_value_or_method
    # Set identity to a tuple containing design['freeze'].freeze_id, hidden.candidate_evidence_id, maximum_nodes,
    # depth_candidates,...
    identity = (design["freeze"].freeze_id, hidden.candidate_evidence_id,
                # Include depth_candidates in this tuple.
                maximum_nodes, depth_candidates, mechanical_depth,
                # Include responder_input in this tuple.
                proposer_input, responder_input, critic_input)
    # Return the result of MechanicalPilotArchitectureContract(a tuple containing the text
    # 'MECHANICAL_PILOT_ARCHITECTURE_CONTRACT_V1', the hexadecimal digest...) to the caller.
    return MechanicalPilotArchitectureContract(
        # Supply a tuple containing the text 'MECHANICAL_PILOT_ARCHITECTURE_CONTRACT_V1', the hexadecimal digest
        # from... to MechanicalPilotArchitectureContract.
        ("MECHANICAL_PILOT_ARCHITECTURE_CONTRACT_V1",
         # Include the hexadecimal digest from hashlib.sha256(repr(identity).encode()) in this tuple.
         hashlib.sha256(repr(identity).encode()).hexdigest()),
        # Supply design['freeze'].freeze_id to MechanicalPilotArchitectureContract.
        design["freeze"].freeze_id,
        # Supply hidden.candidate_value_or_method to MechanicalPilotArchitectureContract.
        hidden.candidate_value_or_method, hidden.candidate_evidence_id,
        # Supply mechanical_depth to MechanicalPilotArchitectureContract.
        mechanical_depth, depth_candidates,
        # Store the text 'REQUIRES_CONTROLLED_ABLATION' under 'classification'.
        {"classification": "REQUIRES_CONTROLLED_ABLATION",
         "mechanical_value_classification":
             "LITERATURE_INFORMED_MECHANICAL_REFERENCE",
         "derivation": "MAX_OBSERVED_NODE_COUNT_MINUS_ONE",
         # Store maximum_nodes under 'maximum_observed_node_count'.
         "maximum_observed_node_count": maximum_nodes,
         # Store maximum_simple_path_edges under 'maximum_simple_path_edge_count'.
         "maximum_simple_path_edge_count": maximum_simple_path_edges,
         "primary_source":
             "Gilmer et al. (2017), Neural Message Passing for Quantum Chemistry",
         # Store False under 'claim_of_optimality'.
         "claim_of_optimality": False,
         # Store False under 'validation_only_depth_promoted'.
         "validation_only_depth_promoted": False},
        "RELU",
        "PYTORCH_LINEAR_RESET_PARAMETERS_EXPLICIT_REPLAY_V1",
        # Store the text 'LITERATURE_INFORMED_MECHANICAL_REFERENCE' under 'classification'.
        {"classification": "LITERATURE_INFORMED_MECHANICAL_REFERENCE",
         "framework": "PyTorch 2.6.0+cpu",
         "weight": "kaiming_uniform_(a=sqrt(5), generator=supplied)",
         "bias": "uniform_(-1/sqrt(fan_in),1/sqrt(fan_in),generator=supplied)",
         "source": "torch.nn.Linear.reset_parameters implementation",
         # Store False under 'silent_framework_default'.
         "silent_framework_default": False,
         # Store False under 'project_selected'.
         "project_selected": False},
        # Supply training_mode.candidate_value_or_method to MechanicalPilotArchitectureContract.
        training_mode.candidate_value_or_method,
        "DETERMINISTIC_EXPLICITLY_INITIALIZED_MECHANICAL_REPRESENTATION_ONLY",
        "CONCAT_EGO_GRAPH_CLAIM_TO_SINGLE_LINEAR_TWO_LOGIT_HEAD",
        "CONCAT_EGO_GRAPH_PROPOSAL_PROTOCOL_ROLE_TO_SINGLE_LINEAR_TWO_LOGIT_HEAD",
        "TRAINING_ONLY_DEEP_SETS_SUM_TO_SINGLE_LINEAR_SCALAR_VALUE_HEAD",
        # Supply responder_input to MechanicalPilotArchitectureContract.
        proposer_input, responder_input, critic_input,
        # Supply sharing.candidate_value_or_method to MechanicalPilotArchitectureContract.
        sharing.candidate_value_or_method,
        # Supply an empty tuple to MechanicalPilotArchitectureContract.
        True, False, False, (),
        # Store True under 'post_freeze_evidence'.
        {"post_freeze_evidence": True,
         # Store False under 'frozen_design_mutated'.
         "frozen_design_mutated": False,
         # Store 0 under 'new_hidden_layers'.
         "new_hidden_layers": 0,
         # Store 0 under 'new_dropout_layers'.
         "new_dropout_layers": 0,
         # Store 0 under 'route_truth_actor_fields'.
         "route_truth_actor_fields": 0,
         # Store False under 'training_performed'.
         "training_performed": False,
         # Store 0 under 'optimizer_instances'.
         "optimizer_instances": 0})


# Derive an initialization seed from an externally supplied seed identity.
# Input contract_id: the supplied contract id.
# Input supplied_seed_identity: the supplied supplied seed identity.
# Output: the result of int.from_bytes(digest sliced by :8, the text 'big') modulo 2 raised to the power 63 minus
# 1.
def deterministic_initialization_seed(contract_id, supplied_seed_identity):
    """Derive an initialization seed from an externally supplied seed identity."""
    # Set digest to the result of hashlib.sha256(repr((contract_id, supplied_seed_identity)).encode()).digest().
    digest = hashlib.sha256(
        # Supply the result of repr((contract_id, supplied_seed_identity)).encode() to hashlib.sha256.
        repr((contract_id, supplied_seed_identity)).encode()).digest()
    # Return the result of int.from_bytes(digest sliced by :8, the text 'big') modulo 2 raised to the power 63
    # minus 1 to the caller.
    return int.from_bytes(digest[:8], "big") % (2 ** 63 - 1)


# Replay the documented nn.Linear policy explicitly and reproducibly.
# Input module: the supplied module.
# Input seed_value: the supplied seed value.
# Output: module.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def apply_explicit_mechanical_initialization(module, seed_value):
    """Replay the documented nn.Linear policy explicitly and reproducibly."""
    # Import torch for use in this module.
    import torch
    # Import nn from torch for the operations below.
    from torch import nn

    # Set generator to the result of torch.Generator().
    generator = torch.Generator(device="cpu")
    # Call generator.manual_seed with the supplied arguments.
    generator.manual_seed(int(seed_value))
    # Enter the result of torch.no_grad() and run the enclosed operations within that context.
    with torch.no_grad():
        # Iterate over the result of module.modules(), binding each item to layer.
        for layer in module.modules():
            # Run this branch when whether layer has type nn.Linear.
            if isinstance(layer, nn.Linear):
                # Call nn.init.kaiming_uniform_ with the supplied arguments.
                nn.init.kaiming_uniform_(
                    # Supply a as the square root of 5.
                    # Supply generator as generator.
                    layer.weight, a=math.sqrt(5), generator=generator)
                # Run this branch when layer.bias is a different object from None.
                if layer.bias is not None:
                    # Set (fan_in, _) to the result of nn.init._calculate_fan_in_and_fan_out(layer.weight).
                    fan_in, _ = nn.init._calculate_fan_in_and_fan_out(
                        # Supply layer.weight to nn.init._calculate_fan_in_and_fan_out.
                        layer.weight)
                    # Set bound to 1.0 divided by the square root of fan_in when fan_in is greater than 0,
                    # otherwise 0.0.
                    bound = 1.0 / math.sqrt(fan_in) if fan_in > 0 else 0.0
                    # Call nn.init.uniform_ with the supplied arguments.
                    nn.init.uniform_(layer.bias, -bound, bound,
                                     # Supply generator as generator.
                                     generator=generator)
    # Return module to the caller.
    return module
