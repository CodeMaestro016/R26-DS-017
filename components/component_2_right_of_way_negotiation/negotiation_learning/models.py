"""Immutable semantic interfaces for future graph-based MARL work."""

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Optional, Tuple


class NegotiationStatus(str, Enum):
    NO_ACTIVE_CONFLICT = "NO_ACTIVE_CONFLICT"
    REGULATORY_ORDER_RESOLVED = "REGULATORY_ORDER_RESOLVED"
    NEGOTIATION_REQUIRED_REGULATORY_CYCLE = "NEGOTIATION_REQUIRED_REGULATORY_CYCLE"
    NEGOTIATION_REQUIRED_UNRESOLVED_PRECEDENCE = "NEGOTIATION_REQUIRED_UNRESOLVED_PRECEDENCE"
    NEGOTIATION_BLOCKED_REGULATORY_INPUT_UNRESOLVED = "NEGOTIATION_BLOCKED_REGULATORY_INPUT_UNRESOLVED"
    SOURCE_SNAPSHOT_MISMATCH = "SOURCE_SNAPSHOT_MISMATCH"
    REGULATORY_PROFILE_MISMATCH = "REGULATORY_PROFILE_MISMATCH"
    COMMUNICATED_PRECEDENCE_DISAGREEMENT = "COMMUNICATED_PRECEDENCE_DISAGREEMENT"


class NegotiationAction(str, Enum):
    """Coordination messages, never longitudinal/lateral driving commands."""

    KEEP_CLAIM = "KEEP_CLAIM"
    RELINQUISH_CLAIM = "RELINQUISH_CLAIM"


@dataclass(frozen=True)
class GraphObservation:
    ego_id: str
    node_ids: Tuple[str, ...]
    node_features: Tuple[dict, ...]
    edge_index: Tuple[Tuple[int, int], ...]
    edge_features: Tuple[dict, ...]
    hard_constraint_evidence: dict
    learning_features: dict
    metadata: dict

    def to_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class NegotiationProblemSnapshot:
    ego_id: str
    timestamp: float
    participant_ids: Tuple[str, ...]
    local_participant_ids: Tuple[str, ...]
    local_precedence_edges: Tuple[dict, ...]
    communicated_precedence_edges: Tuple[dict, ...]
    joint_precedence_edges: Tuple[dict, ...]
    precedence_edges: Tuple[dict, ...]
    messages_received: int
    messages_adopted: int
    messages_ignored_unconnected: int
    duplicate_claims_merged: int
    communicated_disagreements: Tuple[dict, ...]
    regulatory_profile_mismatches: Tuple[dict, ...]
    communication_model: str
    unresolved_relations: Tuple[dict, ...]
    cycle_detected: bool
    cycle_members: Tuple[str, ...]
    strongly_connected_components: Tuple[Tuple[str, ...], ...]
    yield_precedence_graph_topological_order: Optional[Tuple[str, ...]]
    regulatory_service_order: Optional[Tuple[str, ...]]
    negotiation_status: str
    explicit_coordination_permitted_or_required: bool
    graph_observation: dict
    available_action_schema: Tuple[str, ...]
    action_feasibility_evidence: dict
    future_objective_measurements: Tuple[str, ...]
    source_conflict_graph_timestamp: Optional[float]
    source_temporal_assessment_timestamp: Optional[float]
    source_regulatory_assessment_timestamp: Optional[float]
    source_snapshot_consistent: bool
    control_actions_issued: int = 0

    def to_dict(self):
        return asdict(self)
