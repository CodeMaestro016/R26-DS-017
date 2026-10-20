"""Immutable event-driven negotiation transition contracts for Step 5G."""

# Import dataclass, replace from dataclasses for the operations below.
from dataclasses import dataclass, replace
# Import Enum from enum for the operations below.
from enum import Enum
# Import MappingProxyType from types for the operations below.
from types import MappingProxyType
# Import Any, Mapping, Optional, Tuple from typing for the operations below.
from typing import Any, Mapping, Optional, Tuple

# Import numpy as np for use in this module.
import numpy as np

# Import NegotiationDecisionRole, PolicyDecisionProvenance from ..mappo_interface.models for the operations below.
from ..mappo_interface.models import NegotiationDecisionRole, PolicyDecisionProvenance
# Import ProtocolState from ..protocol.message_models for the operations below.
from ..protocol.message_models import ProtocolState
# Import EncodedGraphObservation from ..tensor_encoding.models for the operations below.
from ..tensor_encoding.models import EncodedGraphObservation


# Set TRANSITION_SEMANTICS_STATUS to the text 'IMPLEMENTED_STEP_5G'.
TRANSITION_SEMANTICS_STATUS = "IMPLEMENTED_STEP_5G"
# Set TEMPORAL_FORMULATION_STATUS to the text 'EVENT_DRIVEN_VARIABLE_DURATION_SEMANTICS_VALIDATED'.
TEMPORAL_FORMULATION_STATUS = "EVENT_DRIVEN_VARIABLE_DURATION_SEMANTICS_VALIDATED"
# Set BOOTSTRAP_SEMANTICS_STATUS to the text 'NOT_DEFINED_STEP_5G'.
BOOTSTRAP_SEMANTICS_STATUS = "NOT_DEFINED_STEP_5G"
# Set REWARD_DESIGN_STATUS to the text 'NOT_IMPLEMENTED'.
REWARD_DESIGN_STATUS = "NOT_IMPLEMENTED"
# Set GNN_POLICY_TRAINING_MODE to the text 'REQUIRES_EXPERIMENTAL_SELECTION'.
GNN_POLICY_TRAINING_MODE = "REQUIRES_EXPERIMENTAL_SELECTION"


# Define DecisionEpochReason to group the state and operations declared below.
# Base classes: str, Enum.
# Instances expose the attributes and methods implemented in this class.
class DecisionEpochReason(str, Enum):
    # Set NEW_NEGOTIABLE_PRECEDENCE_CLAIM to the text 'NEW_NEGOTIABLE_PRECEDENCE_CLAIM'.
    NEW_NEGOTIABLE_PRECEDENCE_CLAIM = "NEW_NEGOTIABLE_PRECEDENCE_CLAIM"
    # Set NEW_PENDING_RELINQUISHMENT_PROPOSAL to the text 'NEW_PENDING_RELINQUISHMENT_PROPOSAL'.
    NEW_PENDING_RELINQUISHMENT_PROPOSAL = "NEW_PENDING_RELINQUISHMENT_PROPOSAL"
    # Set NEGOTIATION_STATUS_CHANGED to the text 'NEGOTIATION_STATUS_CHANGED'.
    NEGOTIATION_STATUS_CHANGED = "NEGOTIATION_STATUS_CHANGED"
    # Set POLICY_AUTHORITY_CHANGED to the text 'POLICY_AUTHORITY_CHANGED'.
    POLICY_AUTHORITY_CHANGED = "POLICY_AUTHORITY_CHANGED"
    # Set HARD_ACTION_FEASIBILITY_CHANGED to the text 'HARD_ACTION_FEASIBILITY_CHANGED'.
    HARD_ACTION_FEASIBILITY_CHANGED = "HARD_ACTION_FEASIBILITY_CHANGED"
    # Set PROTOCOL_STATE_CHANGED to the text 'PROTOCOL_STATE_CHANGED'.
    PROTOCOL_STATE_CHANGED = "PROTOCOL_STATE_CHANGED"
    # Set NEGOTIATION_SUBJECT_REENTERED to the text 'NEGOTIATION_SUBJECT_REENTERED'.
    NEGOTIATION_SUBJECT_REENTERED = "NEGOTIATION_SUBJECT_REENTERED"


# Define ImmediateConsequenceType to group the state and operations declared below.
# Base classes: str, Enum.
# Instances expose the attributes and methods implemented in this class.
class ImmediateConsequenceType(str, Enum):
    # Set CLAIM_RETAINED to the text 'CLAIM_RETAINED'.
    CLAIM_RETAINED = "CLAIM_RETAINED"
    # Set RELINQUISHMENT_PROPOSAL_CREATED to the text 'RELINQUISHMENT_PROPOSAL_CREATED'.
    RELINQUISHMENT_PROPOSAL_CREATED = "RELINQUISHMENT_PROPOSAL_CREATED"
    # Set RELINQUISHMENT_ACCEPT_RESPONSE_CREATED to the text 'RELINQUISHMENT_ACCEPT_RESPONSE_CREATED'.
    RELINQUISHMENT_ACCEPT_RESPONSE_CREATED = "RELINQUISHMENT_ACCEPT_RESPONSE_CREATED"
    # Set RELINQUISHMENT_REJECT_RESPONSE_CREATED to the text 'RELINQUISHMENT_REJECT_RESPONSE_CREATED'.
    RELINQUISHMENT_REJECT_RESPONSE_CREATED = "RELINQUISHMENT_REJECT_RESPONSE_CREATED"


# Define TransitionStatus to group the state and operations declared below.
# Base classes: str, Enum.
# Instances expose the attributes and methods implemented in this class.
class TransitionStatus(str, Enum):
    # Set OPEN to the text 'OPEN'.
    OPEN = "OPEN"
    # Set WAITING_FOR_PROTOCOL_RESPONSE to the text 'WAITING_FOR_PROTOCOL_RESPONSE'.
    WAITING_FOR_PROTOCOL_RESPONSE = "WAITING_FOR_PROTOCOL_RESPONSE"
    # Set RESOLVED_CLAIM_RETAINED to the text 'RESOLVED_CLAIM_RETAINED'.
    RESOLVED_CLAIM_RETAINED = "RESOLVED_CLAIM_RETAINED"
    # Set RESOLVED_AGREEMENT_ESTABLISHED to the text 'RESOLVED_AGREEMENT_ESTABLISHED'.
    RESOLVED_AGREEMENT_ESTABLISHED = "RESOLVED_AGREEMENT_ESTABLISHED"
    # Set RESOLVED_PROPOSAL_REJECTED to the text 'RESOLVED_PROPOSAL_REJECTED'.
    RESOLVED_PROPOSAL_REJECTED = "RESOLVED_PROPOSAL_REJECTED"
    # Set RESOLVED_SOURCE_CLAIM_INVALID to the text 'RESOLVED_SOURCE_CLAIM_INVALID'.
    RESOLVED_SOURCE_CLAIM_INVALID = "RESOLVED_SOURCE_CLAIM_INVALID"
    # Set RESOLVED_PROTOCOL_BLOCKED to the text 'RESOLVED_PROTOCOL_BLOCKED'.
    RESOLVED_PROTOCOL_BLOCKED = "RESOLVED_PROTOCOL_BLOCKED"
    # Set RESOLVED_PROTOCOL_DISAGREEMENT to the text 'RESOLVED_PROTOCOL_DISAGREEMENT'.
    RESOLVED_PROTOCOL_DISAGREEMENT = "RESOLVED_PROTOCOL_DISAGREEMENT"
    # Set RESOLVED_NEGOTIATION_SUBJECT_DISAPPEARED to the text 'RESOLVED_NEGOTIATION_SUBJECT_DISAPPEARED'.
    RESOLVED_NEGOTIATION_SUBJECT_DISAPPEARED = "RESOLVED_NEGOTIATION_SUBJECT_DISAPPEARED"
    # Set EPISODE_TERMINATED to the text 'EPISODE_TERMINATED'.
    EPISODE_TERMINATED = "EPISODE_TERMINATED"


# Define ContinuationClassification to group the state and operations declared below.
# Base classes: str, Enum.
# Instances expose the attributes and methods implemented in this class.
class ContinuationClassification(str, Enum):
    # Set NEGOTIATION_SUBJECT_RESOLVED to the text 'NEGOTIATION_SUBJECT_RESOLVED'.
    NEGOTIATION_SUBJECT_RESOLVED = "NEGOTIATION_SUBJECT_RESOLVED"
    # Set AGENT_DECISION_SEQUENCE_CONTINUES to the text 'AGENT_DECISION_SEQUENCE_CONTINUES'.
    AGENT_DECISION_SEQUENCE_CONTINUES = "AGENT_DECISION_SEQUENCE_CONTINUES"
    # Set EGO_LEFT_NEGOTIATION_SCOPE to the text 'EGO_LEFT_NEGOTIATION_SCOPE'.
    EGO_LEFT_NEGOTIATION_SCOPE = "EGO_LEFT_NEGOTIATION_SCOPE"
    # Set EGO_REMOVED_FROM_SIMULATION to the text 'EGO_REMOVED_FROM_SIMULATION'.
    EGO_REMOVED_FROM_SIMULATION = "EGO_REMOVED_FROM_SIMULATION"
    # Set SIMULATION_EPISODE_TERMINATED to the text 'SIMULATION_EPISODE_TERMINATED'.
    SIMULATION_EPISODE_TERMINATED = "SIMULATION_EPISODE_TERMINATED"
    # Set AWAITING_PROTOCOL_RESOLUTION to the text 'AWAITING_PROTOCOL_RESOLUTION'.
    AWAITING_PROTOCOL_RESOLUTION = "AWAITING_PROTOCOL_RESOLUTION"


# Immutable graph copy using the inputs and processing steps below.
# Input graph: the supplied graph; annotated as EncodedGraphObservation.
# Output: the returned value, annotated as EncodedGraphObservation.
def immutable_graph_copy(graph: EncodedGraphObservation) -> EncodedGraphObservation:
    # Set arrays to a list of the result of np.array(value) for value in a tuple containing graph.node_features,
    # graph.node_feature_mask, graph.edge_index, graph.edge_features, graph.edge_feature_mask.
    arrays = [np.array(value, copy=True) for value in (
        # Include graph.node_feature_mask in this tuple.
        graph.node_features, graph.node_feature_mask, graph.edge_index,
        # Include graph.edge_feature_mask in this tuple.
        graph.edge_features, graph.edge_feature_mask,
    )]
    # Return the result of EncodedGraphObservation(graph.ego_id, a tuple built from graph.node_ids, the unpacked
    # values from arrays, a tuple built...) to the caller.
    return EncodedGraphObservation(
        # Supply a tuple built from graph.node_ids to EncodedGraphObservation.
        graph.ego_id, tuple(graph.node_ids), *arrays,
        # Supply a tuple built from graph.node_feature_names to EncodedGraphObservation.
        tuple(graph.node_feature_names), tuple(graph.edge_feature_names),
        # Supply a dictionary built from graph.categorical_encoding_metadata to EncodedGraphObservation.
        dict(graph.categorical_encoding_metadata),
        # Supply a dictionary built from graph.hard_constraint_metadata to EncodedGraphObservation.
        dict(graph.hard_constraint_metadata), dict(graph.identifier_metadata),
        # Supply graph.communication_model to EncodedGraphObservation.
        graph.source_graph_scope, graph.communication_model,
        # Supply graph.normalization_status to EncodedGraphObservation.
        graph.normalization_status, graph.tensor_backend,
    )


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define ActorObservationSnapshot to group the state and operations declared below.
# Declared fields: snapshot_id, source_snapshot_timestamp, graph_observation, decision_role, claim_identity,
# counterparty_id, proposal, protocol_state, action_names, hard_action_feasibility_mask, regulatory_profile,....
# Construction and attribute behavior follow the declared decorators and base classes.
class ActorObservationSnapshot:
    # Declare snapshot_id as tuple for this data structure.
    snapshot_id: tuple
    # Declare source_snapshot_timestamp as float for this data structure.
    source_snapshot_timestamp: float
    # Declare graph_observation as EncodedGraphObservation for this data structure.
    graph_observation: EncodedGraphObservation
    # Declare decision_role as NegotiationDecisionRole for this data structure.
    decision_role: NegotiationDecisionRole
    # Declare claim_identity as Tuple[str, str] for this data structure.
    claim_identity: Tuple[str, str]
    # Declare counterparty_id as str for this data structure.
    counterparty_id: str
    # Declare proposal as Optional[Any] for this data structure.
    proposal: Optional[Any]
    # Declare protocol_state as Optional[ProtocolState] for this data structure.
    protocol_state: Optional[ProtocolState]
    # Declare action_names as Tuple[str, ...] for this data structure.
    action_names: Tuple[str, ...]
    # Declare hard_action_feasibility_mask as Tuple[bool, ...] for this data structure.
    hard_action_feasibility_mask: Tuple[bool, ...]
    # Declare regulatory_profile as str for this data structure.
    regulatory_profile: str
    # Declare communication_model as str for this data structure.
    communication_model: str
    # Declare provenance as PolicyDecisionProvenance for this data structure.
    provenance: PolicyDecisionProvenance

    # Post init using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    def __post_init__(self):
        # Call object.__setattr__ with the supplied arguments.
        object.__setattr__(self, "graph_observation", immutable_graph_copy(self.graph_observation))
        # Call object.__setattr__ with the supplied arguments.
        object.__setattr__(self, "hard_action_feasibility_mask",
                           # Supply a tuple built from a lazy sequence of a Boolean built from v for v in
                           # self.hard_action_feasibility_mask to object.__setattr__.
                           tuple(bool(v) for v in self.hard_action_feasibility_mask))


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define CentralizedTrainingObservationSnapshot to group the state and operations declared below.
# Declared fields: snapshot_id, decision_timestamp, participant_actor_snapshots, participant_ids, aggregation,
# provenance, availability.
# Construction and attribute behavior follow the declared decorators and base classes.
class CentralizedTrainingObservationSnapshot:
    # Declare snapshot_id as tuple for this data structure.
    snapshot_id: tuple
    # Declare decision_timestamp as float for this data structure.
    decision_timestamp: float
    # Declare participant_actor_snapshots as Tuple[ActorObservationSnapshot, ...] for this data structure.
    participant_actor_snapshots: Tuple[ActorObservationSnapshot, ...]
    # Declare participant_ids as Tuple[str, ...] for this data structure.
    participant_ids: Tuple[str, ...]
    # Declare aggregation as str for this data structure.
    aggregation: str
    # Declare provenance as Mapping[str, str] for this data structure.
    provenance: Mapping[str, str]
    # Set availability to the text 'TRAINING_ONLY'; declare its type as str.
    availability: str = "TRAINING_ONLY"

    # Post init using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    def __post_init__(self):
        # Set ordered to a tuple built from the sorted values from self.participant_actor_snapshots.
        ordered = tuple(sorted(self.participant_actor_snapshots,
                               # Declare item as input parameter.
                               key=lambda item: item.graph_observation.ego_id))
        # Call object.__setattr__ with the supplied arguments.
        object.__setattr__(self, "participant_actor_snapshots", ordered)
        # Call object.__setattr__ with the supplied arguments.
        object.__setattr__(self, "participant_ids",
                           # Supply a tuple built from a lazy sequence of item.graph_observation.ego_id for item
                           # in ordered to object.__setattr__.
                           tuple(item.graph_observation.ego_id for item in ordered))
        # Call object.__setattr__ with the supplied arguments.
        object.__setattr__(self, "provenance", MappingProxyType(dict(self.provenance)))


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define NegotiationDecisionEpoch to group the state and operations declared below.
# Declared fields: decision_event_id, ego_id, decision_role, counterparty_id, claim_identity, lifecycle_identity,
# proposal_id, parent_decision_event_id, decision_timestamp, decision_epoch_reason, negotiation_status,....
# Construction and attribute behavior follow the declared decorators and base classes.
class NegotiationDecisionEpoch:
    # Declare decision_event_id as tuple for this data structure.
    decision_event_id: tuple
    # Declare ego_id as str for this data structure.
    ego_id: str
    # Declare decision_role as NegotiationDecisionRole for this data structure.
    decision_role: NegotiationDecisionRole
    # Declare counterparty_id as str for this data structure.
    counterparty_id: str
    # Declare claim_identity as Tuple[str, str] for this data structure.
    claim_identity: Tuple[str, str]
    # Declare lifecycle_identity as tuple for this data structure.
    lifecycle_identity: tuple
    # Declare proposal_id as Optional[tuple] for this data structure.
    proposal_id: Optional[tuple]
    # Declare parent_decision_event_id as Optional[tuple] for this data structure.
    parent_decision_event_id: Optional[tuple]
    # Declare decision_timestamp as float for this data structure.
    decision_timestamp: float
    # Declare decision_epoch_reason as DecisionEpochReason for this data structure.
    decision_epoch_reason: DecisionEpochReason
    # Declare negotiation_status as str for this data structure.
    negotiation_status: str
    # Declare protocol_state as Optional[ProtocolState] for this data structure.
    protocol_state: Optional[ProtocolState]
    # Declare policy_authority as str for this data structure.
    policy_authority: str
    # Declare action_names as Tuple[str, ...] for this data structure.
    action_names: Tuple[str, ...]
    # Declare hard_action_feasibility_mask as Tuple[bool, ...] for this data structure.
    hard_action_feasibility_mask: Tuple[bool, ...]
    # Declare actor_observation_snapshot_id as tuple for this data structure.
    actor_observation_snapshot_id: tuple
    # Declare regulatory_profile as str for this data structure.
    regulatory_profile: str
    # Declare communication_model as str for this data structure.
    communication_model: str
    # Declare semantic_signature as tuple for this data structure.
    semantic_signature: tuple
    # Declare provenance as Mapping[str, str] for this data structure.
    provenance: Mapping[str, str]

    # Post init using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    def __post_init__(self):
        # Call object.__setattr__ with the supplied arguments.
        object.__setattr__(self, "provenance", MappingProxyType(dict(self.provenance)))


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define NegotiationActionConsequence to group the state and operations declared below.
# Declared fields: decision_event_id, semantic_action, claim_identity, proposal_id, immediate_consequence_type,
# consequence_timestamp, semantic_message, provenance.
# Construction and attribute behavior follow the declared decorators and base classes.
class NegotiationActionConsequence:
    # Declare decision_event_id as tuple for this data structure.
    decision_event_id: tuple
    # Declare semantic_action as str for this data structure.
    semantic_action: str
    # Declare claim_identity as Tuple[str, str] for this data structure.
    claim_identity: Tuple[str, str]
    # Declare proposal_id as Optional[tuple] for this data structure.
    proposal_id: Optional[tuple]
    # Declare immediate_consequence_type as ImmediateConsequenceType for this data structure.
    immediate_consequence_type: ImmediateConsequenceType
    # Declare consequence_timestamp as float for this data structure.
    consequence_timestamp: float
    # Declare semantic_message as Optional[Any] for this data structure.
    semantic_message: Optional[Any]
    # Declare provenance as Mapping[str, str] for this data structure.
    provenance: Mapping[str, str]

    # Post init using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    def __post_init__(self):
        # Call object.__setattr__ with the supplied arguments.
        object.__setattr__(self, "provenance", MappingProxyType(dict(self.provenance)))


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define NegotiationTransition to group the state and operations declared below.
# Declared fields: transition_id, decision_event_id, parent_decision_event_id, ego_id, decision_role,
# claim_identity, proposal_id, decision_timestamp, decision_epoch_reason, semantic_action,
# immediate_action_consequence,....
# Construction and attribute behavior follow the declared decorators and base classes.
class NegotiationTransition:
    # Declare transition_id as tuple for this data structure.
    transition_id: tuple
    # Declare decision_event_id as tuple for this data structure.
    decision_event_id: tuple
    # Declare parent_decision_event_id as Optional[tuple] for this data structure.
    parent_decision_event_id: Optional[tuple]
    # Declare ego_id as str for this data structure.
    ego_id: str
    # Declare decision_role as NegotiationDecisionRole for this data structure.
    decision_role: NegotiationDecisionRole
    # Declare claim_identity as Tuple[str, str] for this data structure.
    claim_identity: Tuple[str, str]
    # Declare proposal_id as Optional[tuple] for this data structure.
    proposal_id: Optional[tuple]
    # Declare decision_timestamp as float for this data structure.
    decision_timestamp: float
    # Declare decision_epoch_reason as DecisionEpochReason for this data structure.
    decision_epoch_reason: DecisionEpochReason
    # Declare semantic_action as str for this data structure.
    semantic_action: str
    # Declare immediate_action_consequence as Optional[NegotiationActionConsequence] for this data structure.
    immediate_action_consequence: Optional[NegotiationActionConsequence]
    # Declare transition_status as TransitionStatus for this data structure.
    transition_status: TransitionStatus
    # Declare resolution_reason as Optional[str] for this data structure.
    resolution_reason: Optional[str]
    # Declare resolution_timestamp as Optional[float] for this data structure.
    resolution_timestamp: Optional[float]
    # Declare elapsed_seconds as Optional[float] for this data structure.
    elapsed_seconds: Optional[float]
    # Declare actor_observation_snapshot as ActorObservationSnapshot for this data structure.
    actor_observation_snapshot: ActorObservationSnapshot
    # Declare behavior_policy_log_probability as Optional[float] for this data structure.
    behavior_policy_log_probability: Optional[float]
    # Declare critic_observation_snapshot as Optional[CentralizedTrainingObservationSnapshot] for this data
    # structure.
    critic_observation_snapshot: Optional[CentralizedTrainingObservationSnapshot]
    # Declare critic_value_at_collection as Optional[float] for this data structure.
    critic_value_at_collection: Optional[float]
    # Declare successor_actor_observation_snapshot as Optional[ActorObservationSnapshot] for this data structure.
    successor_actor_observation_snapshot: Optional[ActorObservationSnapshot]
    # Declare successor_semantic_state as Optional[str] for this data structure.
    successor_semantic_state: Optional[str]
    # Declare continuation_classification as ContinuationClassification for this data structure.
    continuation_classification: ContinuationClassification
    # Set reward_status to the text 'NOT_IMPLEMENTED_STEP_5G'; declare its type as str.
    reward_status: str = "NOT_IMPLEMENTED_STEP_5G"
