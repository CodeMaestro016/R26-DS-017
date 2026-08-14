"""Immutable event-driven negotiation transition contracts for Step 5G."""

from dataclasses import dataclass, replace
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping, Optional, Tuple

import numpy as np

from ..mappo_interface.models import NegotiationDecisionRole, PolicyDecisionProvenance
from ..protocol.message_models import ProtocolState
from ..tensor_encoding.models import EncodedGraphObservation


TRANSITION_SEMANTICS_STATUS = "IMPLEMENTED_STEP_5G"
TEMPORAL_FORMULATION_STATUS = "EVENT_DRIVEN_VARIABLE_DURATION_SEMANTICS_VALIDATED"
BOOTSTRAP_SEMANTICS_STATUS = "NOT_DEFINED_STEP_5G"
REWARD_DESIGN_STATUS = "NOT_IMPLEMENTED"
GNN_POLICY_TRAINING_MODE = "REQUIRES_EXPERIMENTAL_SELECTION"


class DecisionEpochReason(str, Enum):
    NEW_NEGOTIABLE_PRECEDENCE_CLAIM = "NEW_NEGOTIABLE_PRECEDENCE_CLAIM"
    NEW_PENDING_RELINQUISHMENT_PROPOSAL = "NEW_PENDING_RELINQUISHMENT_PROPOSAL"
    NEGOTIATION_STATUS_CHANGED = "NEGOTIATION_STATUS_CHANGED"
    POLICY_AUTHORITY_CHANGED = "POLICY_AUTHORITY_CHANGED"
    HARD_ACTION_FEASIBILITY_CHANGED = "HARD_ACTION_FEASIBILITY_CHANGED"
    PROTOCOL_STATE_CHANGED = "PROTOCOL_STATE_CHANGED"
    NEGOTIATION_SUBJECT_REENTERED = "NEGOTIATION_SUBJECT_REENTERED"


class ImmediateConsequenceType(str, Enum):
    CLAIM_RETAINED = "CLAIM_RETAINED"
    RELINQUISHMENT_PROPOSAL_CREATED = "RELINQUISHMENT_PROPOSAL_CREATED"
    RELINQUISHMENT_ACCEPT_RESPONSE_CREATED = "RELINQUISHMENT_ACCEPT_RESPONSE_CREATED"
    RELINQUISHMENT_REJECT_RESPONSE_CREATED = "RELINQUISHMENT_REJECT_RESPONSE_CREATED"


class TransitionStatus(str, Enum):
    OPEN = "OPEN"
    WAITING_FOR_PROTOCOL_RESPONSE = "WAITING_FOR_PROTOCOL_RESPONSE"
    RESOLVED_CLAIM_RETAINED = "RESOLVED_CLAIM_RETAINED"
    RESOLVED_AGREEMENT_ESTABLISHED = "RESOLVED_AGREEMENT_ESTABLISHED"
    RESOLVED_PROPOSAL_REJECTED = "RESOLVED_PROPOSAL_REJECTED"
    RESOLVED_SOURCE_CLAIM_INVALID = "RESOLVED_SOURCE_CLAIM_INVALID"
    RESOLVED_PROTOCOL_BLOCKED = "RESOLVED_PROTOCOL_BLOCKED"
    RESOLVED_PROTOCOL_DISAGREEMENT = "RESOLVED_PROTOCOL_DISAGREEMENT"
    RESOLVED_NEGOTIATION_SUBJECT_DISAPPEARED = "RESOLVED_NEGOTIATION_SUBJECT_DISAPPEARED"
    EPISODE_TERMINATED = "EPISODE_TERMINATED"


class ContinuationClassification(str, Enum):
    NEGOTIATION_SUBJECT_RESOLVED = "NEGOTIATION_SUBJECT_RESOLVED"
    AGENT_DECISION_SEQUENCE_CONTINUES = "AGENT_DECISION_SEQUENCE_CONTINUES"
    EGO_LEFT_NEGOTIATION_SCOPE = "EGO_LEFT_NEGOTIATION_SCOPE"
    EGO_REMOVED_FROM_SIMULATION = "EGO_REMOVED_FROM_SIMULATION"
    SIMULATION_EPISODE_TERMINATED = "SIMULATION_EPISODE_TERMINATED"
    AWAITING_PROTOCOL_RESOLUTION = "AWAITING_PROTOCOL_RESOLUTION"


def immutable_graph_copy(graph: EncodedGraphObservation) -> EncodedGraphObservation:
    arrays = [np.array(value, copy=True) for value in (
        graph.node_features, graph.node_feature_mask, graph.edge_index,
        graph.edge_features, graph.edge_feature_mask,
    )]
    return EncodedGraphObservation(
        graph.ego_id, tuple(graph.node_ids), *arrays,
        tuple(graph.node_feature_names), tuple(graph.edge_feature_names),
        dict(graph.categorical_encoding_metadata),
        dict(graph.hard_constraint_metadata), dict(graph.identifier_metadata),
        graph.source_graph_scope, graph.communication_model,
        graph.normalization_status, graph.tensor_backend,
    )


@dataclass(frozen=True)
class ActorObservationSnapshot:
    snapshot_id: tuple
    source_snapshot_timestamp: float
    graph_observation: EncodedGraphObservation
    decision_role: NegotiationDecisionRole
    claim_identity: Tuple[str, str]
    counterparty_id: str
    proposal: Optional[Any]
    protocol_state: Optional[ProtocolState]
    action_names: Tuple[str, ...]
    hard_action_feasibility_mask: Tuple[bool, ...]
    regulatory_profile: str
    communication_model: str
    provenance: PolicyDecisionProvenance

    def __post_init__(self):
        object.__setattr__(self, "graph_observation", immutable_graph_copy(self.graph_observation))
        object.__setattr__(self, "hard_action_feasibility_mask",
                           tuple(bool(v) for v in self.hard_action_feasibility_mask))


@dataclass(frozen=True)
class CentralizedTrainingObservationSnapshot:
    snapshot_id: tuple
    decision_timestamp: float
    participant_actor_snapshots: Tuple[ActorObservationSnapshot, ...]
    participant_ids: Tuple[str, ...]
    aggregation: str
    provenance: Mapping[str, str]
    availability: str = "TRAINING_ONLY"

    def __post_init__(self):
        ordered = tuple(sorted(self.participant_actor_snapshots,
                               key=lambda item: item.graph_observation.ego_id))
        object.__setattr__(self, "participant_actor_snapshots", ordered)
        object.__setattr__(self, "participant_ids",
                           tuple(item.graph_observation.ego_id for item in ordered))
        object.__setattr__(self, "provenance", MappingProxyType(dict(self.provenance)))


@dataclass(frozen=True)
class NegotiationDecisionEpoch:
    decision_event_id: tuple
    ego_id: str
    decision_role: NegotiationDecisionRole
    counterparty_id: str
    claim_identity: Tuple[str, str]
    lifecycle_identity: tuple
    proposal_id: Optional[tuple]
    parent_decision_event_id: Optional[tuple]
    decision_timestamp: float
    decision_epoch_reason: DecisionEpochReason
    negotiation_status: str
    protocol_state: Optional[ProtocolState]
    policy_authority: str
    action_names: Tuple[str, ...]
    hard_action_feasibility_mask: Tuple[bool, ...]
    actor_observation_snapshot_id: tuple
    regulatory_profile: str
    communication_model: str
    semantic_signature: tuple
    provenance: Mapping[str, str]

    def __post_init__(self):
        object.__setattr__(self, "provenance", MappingProxyType(dict(self.provenance)))


@dataclass(frozen=True)
class NegotiationActionConsequence:
    decision_event_id: tuple
    semantic_action: str
    claim_identity: Tuple[str, str]
    proposal_id: Optional[tuple]
    immediate_consequence_type: ImmediateConsequenceType
    consequence_timestamp: float
    semantic_message: Optional[Any]
    provenance: Mapping[str, str]

    def __post_init__(self):
        object.__setattr__(self, "provenance", MappingProxyType(dict(self.provenance)))


@dataclass(frozen=True)
class NegotiationTransition:
    transition_id: tuple
    decision_event_id: tuple
    parent_decision_event_id: Optional[tuple]
    ego_id: str
    decision_role: NegotiationDecisionRole
    claim_identity: Tuple[str, str]
    proposal_id: Optional[tuple]
    decision_timestamp: float
    decision_epoch_reason: DecisionEpochReason
    semantic_action: str
    immediate_action_consequence: Optional[NegotiationActionConsequence]
    transition_status: TransitionStatus
    resolution_reason: Optional[str]
    resolution_timestamp: Optional[float]
    elapsed_seconds: Optional[float]
    actor_observation_snapshot: ActorObservationSnapshot
    behavior_policy_log_probability: Optional[float]
    critic_observation_snapshot: Optional[CentralizedTrainingObservationSnapshot]
    critic_value_at_collection: Optional[float]
    successor_actor_observation_snapshot: Optional[ActorObservationSnapshot]
    successor_semantic_state: Optional[str]
    continuation_classification: ContinuationClassification
    reward_status: str = "NOT_IMPLEMENTED_STEP_5G"
