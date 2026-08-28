"""Immutable role-aware policy and future rollout contracts for Step 5F."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

import torch


class NegotiationDecisionRole(str, Enum):
    PROPOSER = "PROPOSER"
    RESPONDER = "RESPONDER"


ROLE_ENCODING_COLUMNS = (
    NegotiationDecisionRole.PROPOSER,
    NegotiationDecisionRole.RESPONDER,
)
ROLE_ONE_HOT = {
    NegotiationDecisionRole.PROPOSER: (1.0, 0.0),
    NegotiationDecisionRole.RESPONDER: (0.0, 1.0),
}


@dataclass(frozen=True)
class PolicyDecisionProvenance:
    local_observation_identity: str
    local_graph_identity: str
    local_mpnn_identity: str
    semantic_subject_identity: str
    hard_mask_identity: str


@dataclass(frozen=True)
class NegotiationPolicyDecisionContext:
    ego_id: str
    decision_role: NegotiationDecisionRole
    counterparty_id: str
    claim_identity: Tuple[str, str]
    proposal_id: Optional[tuple]
    local_observation_identity: str
    source_snapshot_timestamp: float
    ego_embedding: torch.Tensor
    local_graph_embedding: torch.Tensor
    claim_or_proposal_representation: torch.Tensor
    protocol_state_representation: Optional[torch.Tensor]
    action_names: Tuple[str, ...]
    action_feasibility_mask: torch.Tensor
    provenance: PolicyDecisionProvenance
    regulatory_profile: str
    communication_model: str


@dataclass(frozen=True)
class NegotiationPolicyDecision:
    ego_id: str
    decision_role: NegotiationDecisionRole
    claim_identity: Tuple[str, str]
    proposal_id: Optional[tuple]
    action_names: Tuple[str, ...]
    action_feasibility_mask: torch.Tensor
    unmasked_logits: torch.Tensor
    masked_logits: torch.Tensor
    action_probabilities: torch.Tensor
    selected_action_index: int
    selected_semantic_action: str
    action_log_probability: torch.Tensor
    policy_entropy: torch.Tensor
    source_snapshot_timestamp: float
    observation_provenance: PolicyDecisionProvenance
    policy_status: str = "POLICY_DECISION_SELECTED_TRAINING_INTERFACE_ONLY"


@dataclass(frozen=True)
class NegotiationRolloutStep:
    """Collection schema only: no reward, advantage, return, or PPO ratio."""

    decision_event_id: tuple
    episode_identity: str
    transition_identity: str
    simulation_timestamp: float
    ego_id: str
    decision_role: NegotiationDecisionRole
    claim_identity: Tuple[str, str]
    proposal_id: Optional[tuple]
    local_observation_identity: str
    observation_provenance: PolicyDecisionProvenance
    action_names: Tuple[str, ...]
    action_feasibility_mask: Tuple[bool, ...]
    semantic_action_taken: str
    action_index: int
    behavior_policy_log_probability: float
    critic_value_at_collection: float
    continuation_status: str
    reward_status: str = "NOT_IMPLEMENTED_STEP_5F"


def deterministic_decision_event_id(context):
    return (
        float(context.source_snapshot_timestamp), context.ego_id,
        context.decision_role.value, context.claim_identity,
        context.proposal_id,
    )
