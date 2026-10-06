"""Post-freeze evidence-backed mechanical architecture contract."""

import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Mapping, Tuple

from experimentation import build_design


@dataclass(frozen=True)
class MechanicalPilotArchitectureContract:
    contract_id: tuple
    frozen_design_id: tuple
    gnn_hidden_dimension: int
    gnn_hidden_dimension_evidence_id: tuple
    gnn_message_passing_layers: int
    gnn_depth_candidate_set: Tuple[int, ...]
    gnn_depth_evidence: Mapping
    gnn_activation: str
    initialization_policy: str
    initialization_evidence: Mapping
    gnn_training_mode: str
    frozen_gnn_parameter_source: str
    proposer_actor_head_architecture: str
    responder_actor_head_architecture: str
    centralized_critic_architecture: str
    proposer_input_dimension: int
    responder_input_dimension: int
    critic_input_dimension: int
    parameter_sharing_strategy: str
    mechanical_reference_only: bool
    project_selected: bool
    final_selection_eligible: bool
    unresolved_architecture_fields: Tuple[str, ...]
    provenance: Mapping

    def __post_init__(self):
        for name in ("gnn_depth_evidence", "initialization_evidence", "provenance"):
            object.__setattr__(self, name,
                               MappingProxyType(dict(getattr(self, name))))


def build_mechanical_pilot_architecture_contract(
        profile_path="results/coupled_environment_profile.json"):
    design = build_design()
    profile = json.loads(Path(profile_path).read_text(encoding="utf-8"))
    if profile.get("status") != "COUPLED_ENVIRONMENT_PROFILE_COMPLETE":
        raise ValueError("STEP_5J_3A_PROFILE_NOT_COMPLETE")
    assignments = {item.choice_id: item for item in
                   design["provisional"].assignments}
    hidden = assignments["gnn_hidden_dimension"]
    training_mode = assignments["gnn_training_mode"]
    sharing = assignments["parameter_sharing_strategy"]
    observed_node_counts = tuple(
        shape[0][0] for episode in profile["episodes"]
        for batch in episode["joint_decision_batches"]
        for shape in batch["encoded_graph_shapes"])
    maximum_nodes = max(observed_node_counts)
    maximum_simple_path_edges = maximum_nodes - 1
    depth_candidates = tuple(range(1, maximum_simple_path_edges + 1))
    mechanical_depth = maximum_simple_path_edges
    node_dim, edge_dim = 8, 9
    claim_dim, protocol_dim, role_dim = 2 * (node_dim + edge_dim), 16, 2
    proposer_input = 2 * hidden.candidate_value_or_method + claim_dim
    responder_input = proposer_input + protocol_dim + role_dim
    critic_input = hidden.candidate_value_or_method
    identity = (design["freeze"].freeze_id, hidden.candidate_evidence_id,
                maximum_nodes, depth_candidates, mechanical_depth,
                proposer_input, responder_input, critic_input)
    return MechanicalPilotArchitectureContract(
        ("MECHANICAL_PILOT_ARCHITECTURE_CONTRACT_V1",
         hashlib.sha256(repr(identity).encode()).hexdigest()),
        design["freeze"].freeze_id,
        hidden.candidate_value_or_method, hidden.candidate_evidence_id,
        mechanical_depth, depth_candidates,
        {"classification": "REQUIRES_CONTROLLED_ABLATION",
         "mechanical_value_classification":
             "LITERATURE_INFORMED_MECHANICAL_REFERENCE",
         "derivation": "MAX_OBSERVED_NODE_COUNT_MINUS_ONE",
         "maximum_observed_node_count": maximum_nodes,
         "maximum_simple_path_edge_count": maximum_simple_path_edges,
         "primary_source":
             "Gilmer et al. (2017), Neural Message Passing for Quantum Chemistry",
         "claim_of_optimality": False,
         "validation_only_depth_promoted": False},
        "RELU",
        "PYTORCH_LINEAR_RESET_PARAMETERS_EXPLICIT_REPLAY_V1",
        {"classification": "LITERATURE_INFORMED_MECHANICAL_REFERENCE",
         "framework": "PyTorch 2.6.0+cpu",
         "weight": "kaiming_uniform_(a=sqrt(5), generator=supplied)",
         "bias": "uniform_(-1/sqrt(fan_in),1/sqrt(fan_in),generator=supplied)",
         "source": "torch.nn.Linear.reset_parameters implementation",
         "silent_framework_default": False,
         "project_selected": False},
        training_mode.candidate_value_or_method,
        "DETERMINISTIC_EXPLICITLY_INITIALIZED_MECHANICAL_REPRESENTATION_ONLY",
        "CONCAT_EGO_GRAPH_CLAIM_TO_SINGLE_LINEAR_TWO_LOGIT_HEAD",
        "CONCAT_EGO_GRAPH_PROPOSAL_PROTOCOL_ROLE_TO_SINGLE_LINEAR_TWO_LOGIT_HEAD",
        "TRAINING_ONLY_DEEP_SETS_SUM_TO_SINGLE_LINEAR_SCALAR_VALUE_HEAD",
        proposer_input, responder_input, critic_input,
        sharing.candidate_value_or_method,
        True, False, False, (),
        {"post_freeze_evidence": True,
         "frozen_design_mutated": False,
         "new_hidden_layers": 0,
         "new_dropout_layers": 0,
         "route_truth_actor_fields": 0,
         "training_performed": False,
         "optimizer_instances": 0})


def deterministic_initialization_seed(contract_id, supplied_seed_identity):
    """Derive an initialization seed from an externally supplied seed identity."""
    digest = hashlib.sha256(
        repr((contract_id, supplied_seed_identity)).encode()).digest()
    return int.from_bytes(digest[:8], "big") % (2 ** 63 - 1)


def apply_explicit_mechanical_initialization(module, seed_value):
    """Replay the documented nn.Linear policy explicitly and reproducibly."""
    import torch
    from torch import nn

    generator = torch.Generator(device="cpu")
    generator.manual_seed(int(seed_value))
    with torch.no_grad():
        for layer in module.modules():
            if isinstance(layer, nn.Linear):
                nn.init.kaiming_uniform_(
                    layer.weight, a=math.sqrt(5), generator=generator)
                if layer.bias is not None:
                    fan_in, _ = nn.init._calculate_fan_in_and_fan_out(
                        layer.weight)
                    bound = 1.0 / math.sqrt(fan_in) if fan_in > 0 else 0.0
                    nn.init.uniform_(layer.bias, -bound, bound,
                                     generator=generator)
    return module
