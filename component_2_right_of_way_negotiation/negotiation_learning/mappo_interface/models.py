"""Immutable role-aware policy and future rollout contracts for Step 5F."""

# Import dataclass from dataclasses for the operations below.
from dataclasses import dataclass
# Import Enum from enum for the operations below.
from enum import Enum
# Import Optional, Tuple from typing for the operations below.
from typing import Optional, Tuple

# Import torch for use in this module.
import torch


# Define NegotiationDecisionRole to group the state and operations declared below.
# Base classes: str, Enum.
# Instances expose the attributes and methods implemented in this class.
class NegotiationDecisionRole(str, Enum):
    # Set PROPOSER to the text 'PROPOSER'.
    PROPOSER = "PROPOSER"
    # Set RESPONDER to the text 'RESPONDER'.
    RESPONDER = "RESPONDER"


# Set ROLE_ENCODING_COLUMNS to a tuple containing NegotiationDecisionRole.PROPOSER,
# NegotiationDecisionRole.RESPONDER.
ROLE_ENCODING_COLUMNS = (
    # Include NegotiationDecisionRole.PROPOSER in this tuple.
    NegotiationDecisionRole.PROPOSER,
    # Include NegotiationDecisionRole.RESPONDER in this tuple.
    NegotiationDecisionRole.RESPONDER,
)
# Set ROLE_ONE_HOT to a dictionary of the supplied entries.
ROLE_ONE_HOT = {
    # Store a tuple containing 1.0, 0.0 under NegotiationDecisionRole.PROPOSER.
    NegotiationDecisionRole.PROPOSER: (1.0, 0.0),
    # Store a tuple containing 0.0, 1.0 under NegotiationDecisionRole.RESPONDER.
    NegotiationDecisionRole.RESPONDER: (0.0, 1.0),
}


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define PolicyDecisionProvenance to group the state and operations declared below.
# Declared fields: local_observation_identity, local_graph_identity, local_mpnn_identity,
# semantic_subject_identity, hard_mask_identity.
# Construction and attribute behavior follow the declared decorators and base classes.
class PolicyDecisionProvenance:
    # Declare local_observation_identity as str for this data structure.
    local_observation_identity: str
    # Declare local_graph_identity as str for this data structure.
    local_graph_identity: str
    # Declare local_mpnn_identity as str for this data structure.
    local_mpnn_identity: str
    # Declare semantic_subject_identity as str for this data structure.
    semantic_subject_identity: str
    # Declare hard_mask_identity as str for this data structure.
    hard_mask_identity: str


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define NegotiationPolicyDecisionContext to group the state and operations declared below.
# Declared fields: ego_id, decision_role, counterparty_id, claim_identity, proposal_id,
# local_observation_identity, source_snapshot_timestamp, ego_embedding, local_graph_embedding,
# claim_or_proposal_representation,....
# Construction and attribute behavior follow the declared decorators and base classes.
class NegotiationPolicyDecisionContext:
    # Declare ego_id as str for this data structure.
    ego_id: str
    # Declare decision_role as NegotiationDecisionRole for this data structure.
    decision_role: NegotiationDecisionRole
    # Declare counterparty_id as str for this data structure.
    counterparty_id: str
    # Declare claim_identity as Tuple[str, str] for this data structure.
    claim_identity: Tuple[str, str]
    # Declare proposal_id as Optional[tuple] for this data structure.
    proposal_id: Optional[tuple]
    # Declare local_observation_identity as str for this data structure.
    local_observation_identity: str
    # Declare source_snapshot_timestamp as float for this data structure.
    source_snapshot_timestamp: float
    # Declare ego_embedding as torch.Tensor for this data structure.
    ego_embedding: torch.Tensor
    # Declare local_graph_embedding as torch.Tensor for this data structure.
    local_graph_embedding: torch.Tensor
    # Declare claim_or_proposal_representation as torch.Tensor for this data structure.
    claim_or_proposal_representation: torch.Tensor
    # Declare protocol_state_representation as Optional[torch.Tensor] for this data structure.
    protocol_state_representation: Optional[torch.Tensor]
    # Declare action_names as Tuple[str, ...] for this data structure.
    action_names: Tuple[str, ...]
    # Declare action_feasibility_mask as torch.Tensor for this data structure.
    action_feasibility_mask: torch.Tensor
    # Declare provenance as PolicyDecisionProvenance for this data structure.
    provenance: PolicyDecisionProvenance
    # Declare regulatory_profile as str for this data structure.
    regulatory_profile: str
    # Declare communication_model as str for this data structure.
    communication_model: str


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define NegotiationPolicyDecision to group the state and operations declared below.
# Declared fields: ego_id, decision_role, claim_identity, proposal_id, action_names, action_feasibility_mask,
# unmasked_logits, masked_logits, action_probabilities, selected_action_index, selected_semantic_action,....
# Construction and attribute behavior follow the declared decorators and base classes.
class NegotiationPolicyDecision:
    # Declare ego_id as str for this data structure.
    ego_id: str
    # Declare decision_role as NegotiationDecisionRole for this data structure.
    decision_role: NegotiationDecisionRole
    # Declare claim_identity as Tuple[str, str] for this data structure.
    claim_identity: Tuple[str, str]
    # Declare proposal_id as Optional[tuple] for this data structure.
    proposal_id: Optional[tuple]
    # Declare action_names as Tuple[str, ...] for this data structure.
    action_names: Tuple[str, ...]
    # Declare action_feasibility_mask as torch.Tensor for this data structure.
    action_feasibility_mask: torch.Tensor
    # Declare unmasked_logits as torch.Tensor for this data structure.
    unmasked_logits: torch.Tensor
    # Declare masked_logits as torch.Tensor for this data structure.
    masked_logits: torch.Tensor
    # Declare action_probabilities as torch.Tensor for this data structure.
    action_probabilities: torch.Tensor
    # Declare selected_action_index as int for this data structure.
    selected_action_index: int
    # Declare selected_semantic_action as str for this data structure.
    selected_semantic_action: str
    # Declare action_log_probability as torch.Tensor for this data structure.
    action_log_probability: torch.Tensor
    # Declare policy_entropy as torch.Tensor for this data structure.
    policy_entropy: torch.Tensor
    # Declare source_snapshot_timestamp as float for this data structure.
    source_snapshot_timestamp: float
    # Declare observation_provenance as PolicyDecisionProvenance for this data structure.
    observation_provenance: PolicyDecisionProvenance
    # Set policy_status to the text 'POLICY_DECISION_SELECTED_TRAINING_INTERFACE_ONLY'; declare its type as str.
    policy_status: str = "POLICY_DECISION_SELECTED_TRAINING_INTERFACE_ONLY"


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Collection schema only: no reward, advantage, return, or PPO ratio.
# Declared fields: decision_event_id, episode_identity, transition_identity, simulation_timestamp, ego_id,
# decision_role, claim_identity, proposal_id, local_observation_identity, observation_provenance,
# action_names,....
# Construction and attribute behavior follow the declared decorators and base classes.
class NegotiationRolloutStep:
    """Collection schema only: no reward, advantage, return, or PPO ratio."""

    # Declare decision_event_id as tuple for this data structure.
    decision_event_id: tuple
    # Declare episode_identity as str for this data structure.
    episode_identity: str
    # Declare transition_identity as str for this data structure.
    transition_identity: str
    # Declare simulation_timestamp as float for this data structure.
    simulation_timestamp: float
    # Declare ego_id as str for this data structure.
    ego_id: str
    # Declare decision_role as NegotiationDecisionRole for this data structure.
    decision_role: NegotiationDecisionRole
    # Declare claim_identity as Tuple[str, str] for this data structure.
    claim_identity: Tuple[str, str]
    # Declare proposal_id as Optional[tuple] for this data structure.
    proposal_id: Optional[tuple]
    # Declare local_observation_identity as str for this data structure.
    local_observation_identity: str
    # Declare observation_provenance as PolicyDecisionProvenance for this data structure.
    observation_provenance: PolicyDecisionProvenance
    # Declare action_names as Tuple[str, ...] for this data structure.
    action_names: Tuple[str, ...]
    # Declare action_feasibility_mask as Tuple[bool, ...] for this data structure.
    action_feasibility_mask: Tuple[bool, ...]
    # Declare semantic_action_taken as str for this data structure.
    semantic_action_taken: str
    # Declare action_index as int for this data structure.
    action_index: int
    # Declare behavior_policy_log_probability as float for this data structure.
    behavior_policy_log_probability: float
    # Declare critic_value_at_collection as float for this data structure.
    critic_value_at_collection: float
    # Declare continuation_status as str for this data structure.
    continuation_status: str
    # Set reward_status to the text 'NOT_IMPLEMENTED_STEP_5F'; declare its type as str.
    reward_status: str = "NOT_IMPLEMENTED_STEP_5F"


# Deterministic decision event id using the inputs and processing steps below.
# Input context: the supplied context.
# Output: a tuple containing a floating-point number built from context.source_snapshot_timestamp,
# context.ego_id,...
def deterministic_decision_event_id(context):
    # Return a tuple containing a floating-point number built from context.source_snapshot_timestamp,
    # context.ego_id,... to the caller.
    return (
        # Include a floating-point number built from context.source_snapshot_timestamp in this tuple.
        float(context.source_snapshot_timestamp), context.ego_id,
        # Include context.decision_role.value in this tuple.
        context.decision_role.value, context.claim_identity,
        # Include context.proposal_id in this tuple.
        context.proposal_id,
    )
