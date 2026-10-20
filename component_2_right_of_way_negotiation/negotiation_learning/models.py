"""Immutable semantic interfaces for future graph-based MARL work."""

# Import asdict, dataclass from dataclasses for the operations below.
from dataclasses import asdict, dataclass
# Import Enum from enum for the operations below.
from enum import Enum
# Import Optional, Tuple from typing for the operations below.
from typing import Optional, Tuple


# Define NegotiationStatus to group the state and operations declared below.
# Base classes: str, Enum.
# Instances expose the attributes and methods implemented in this class.
class NegotiationStatus(str, Enum):
    # Set NO_ACTIVE_CONFLICT to the text 'NO_ACTIVE_CONFLICT'.
    NO_ACTIVE_CONFLICT = "NO_ACTIVE_CONFLICT"
    # Set REGULATORY_ORDER_RESOLVED to the text 'REGULATORY_ORDER_RESOLVED'.
    REGULATORY_ORDER_RESOLVED = "REGULATORY_ORDER_RESOLVED"
    # Set NEGOTIATION_REQUIRED_REGULATORY_CYCLE to the text 'NEGOTIATION_REQUIRED_REGULATORY_CYCLE'.
    NEGOTIATION_REQUIRED_REGULATORY_CYCLE = "NEGOTIATION_REQUIRED_REGULATORY_CYCLE"
    # Set NEGOTIATION_REQUIRED_UNRESOLVED_PRECEDENCE to the text 'NEGOTIATION_REQUIRED_UNRESOLVED_PRECEDENCE'.
    NEGOTIATION_REQUIRED_UNRESOLVED_PRECEDENCE = "NEGOTIATION_REQUIRED_UNRESOLVED_PRECEDENCE"
    # Set NEGOTIATION_BLOCKED_REGULATORY_INPUT_UNRESOLVED to the text
    # 'NEGOTIATION_BLOCKED_REGULATORY_INPUT_UNRESOLVED'.
    NEGOTIATION_BLOCKED_REGULATORY_INPUT_UNRESOLVED = "NEGOTIATION_BLOCKED_REGULATORY_INPUT_UNRESOLVED"
    # Set SOURCE_SNAPSHOT_MISMATCH to the text 'SOURCE_SNAPSHOT_MISMATCH'.
    SOURCE_SNAPSHOT_MISMATCH = "SOURCE_SNAPSHOT_MISMATCH"
    # Set REGULATORY_PROFILE_MISMATCH to the text 'REGULATORY_PROFILE_MISMATCH'.
    REGULATORY_PROFILE_MISMATCH = "REGULATORY_PROFILE_MISMATCH"
    # Set COMMUNICATED_PRECEDENCE_DISAGREEMENT to the text 'COMMUNICATED_PRECEDENCE_DISAGREEMENT'.
    COMMUNICATED_PRECEDENCE_DISAGREEMENT = "COMMUNICATED_PRECEDENCE_DISAGREEMENT"


# Coordination messages, never longitudinal/lateral driving commands.
# Base classes: str, Enum.
# Instances expose the attributes and methods implemented in this class.
class NegotiationAction(str, Enum):
    """Coordination messages, never longitudinal/lateral driving commands."""

    # Set KEEP_CLAIM to the text 'KEEP_CLAIM'.
    KEEP_CLAIM = "KEEP_CLAIM"
    # Set RELINQUISH_CLAIM to the text 'RELINQUISH_CLAIM'.
    RELINQUISH_CLAIM = "RELINQUISH_CLAIM"


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define GraphObservation to group the state and operations declared below.
# Declared fields: ego_id, node_ids, node_features, edge_index, edge_features, hard_constraint_evidence,
# learning_features, metadata.
# Construction and attribute behavior follow the declared decorators and base classes.
class GraphObservation:
    # Declare ego_id as str for this data structure.
    ego_id: str
    # Declare node_ids as Tuple[str, ...] for this data structure.
    node_ids: Tuple[str, ...]
    # Declare node_features as Tuple[dict, ...] for this data structure.
    node_features: Tuple[dict, ...]
    # Declare edge_index as Tuple[Tuple[int, int], ...] for this data structure.
    edge_index: Tuple[Tuple[int, int], ...]
    # Declare edge_features as Tuple[dict, ...] for this data structure.
    edge_features: Tuple[dict, ...]
    # Declare hard_constraint_evidence as dict for this data structure.
    hard_constraint_evidence: dict
    # Declare learning_features as dict for this data structure.
    learning_features: dict
    # Declare metadata as dict for this data structure.
    metadata: dict

    # To dict using the inputs and processing steps below.
    # Output: the result of asdict(self).
    def to_dict(self):
        # Return the result of asdict(self) to the caller.
        return asdict(self)


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define NegotiationProblemSnapshot to group the state and operations declared below.
# Declared fields: ego_id, timestamp, participant_ids, local_participant_ids, local_precedence_edges,
# communicated_precedence_edges, joint_precedence_edges, precedence_edges, messages_received,
# messages_adopted,....
# Construction and attribute behavior follow the declared decorators and base classes.
class NegotiationProblemSnapshot:
    # Declare ego_id as str for this data structure.
    ego_id: str
    # Declare timestamp as float for this data structure.
    timestamp: float
    # Declare participant_ids as Tuple[str, ...] for this data structure.
    participant_ids: Tuple[str, ...]
    # Declare local_participant_ids as Tuple[str, ...] for this data structure.
    local_participant_ids: Tuple[str, ...]
    # Declare local_precedence_edges as Tuple[dict, ...] for this data structure.
    local_precedence_edges: Tuple[dict, ...]
    # Declare communicated_precedence_edges as Tuple[dict, ...] for this data structure.
    communicated_precedence_edges: Tuple[dict, ...]
    # Declare joint_precedence_edges as Tuple[dict, ...] for this data structure.
    joint_precedence_edges: Tuple[dict, ...]
    # Declare precedence_edges as Tuple[dict, ...] for this data structure.
    precedence_edges: Tuple[dict, ...]
    # Declare messages_received as int for this data structure.
    messages_received: int
    # Declare messages_adopted as int for this data structure.
    messages_adopted: int
    # Declare messages_ignored_unconnected as int for this data structure.
    messages_ignored_unconnected: int
    # Declare duplicate_claims_merged as int for this data structure.
    duplicate_claims_merged: int
    # Declare communicated_disagreements as Tuple[dict, ...] for this data structure.
    communicated_disagreements: Tuple[dict, ...]
    # Declare regulatory_profile_mismatches as Tuple[dict, ...] for this data structure.
    regulatory_profile_mismatches: Tuple[dict, ...]
    # Declare communication_model as str for this data structure.
    communication_model: str
    # Declare unresolved_relations as Tuple[dict, ...] for this data structure.
    unresolved_relations: Tuple[dict, ...]
    # Declare cycle_detected as bool for this data structure.
    cycle_detected: bool
    # Declare cycle_members as Tuple[str, ...] for this data structure.
    cycle_members: Tuple[str, ...]
    # Declare strongly_connected_components as Tuple[Tuple[str, ...], ...] for this data structure.
    strongly_connected_components: Tuple[Tuple[str, ...], ...]
    # Declare yield_precedence_graph_topological_order as Optional[Tuple[str, ...]] for this data structure.
    yield_precedence_graph_topological_order: Optional[Tuple[str, ...]]
    # Declare regulatory_service_order as Optional[Tuple[str, ...]] for this data structure.
    regulatory_service_order: Optional[Tuple[str, ...]]
    # Declare negotiation_status as str for this data structure.
    negotiation_status: str
    # Declare explicit_coordination_permitted_or_required as bool for this data structure.
    explicit_coordination_permitted_or_required: bool
    # Declare graph_observation as dict for this data structure.
    graph_observation: dict
    # Declare available_action_schema as Tuple[str, ...] for this data structure.
    available_action_schema: Tuple[str, ...]
    # Declare action_feasibility_evidence as dict for this data structure.
    action_feasibility_evidence: dict
    # Declare future_objective_measurements as Tuple[str, ...] for this data structure.
    future_objective_measurements: Tuple[str, ...]
    # Declare source_conflict_graph_timestamp as Optional[float] for this data structure.
    source_conflict_graph_timestamp: Optional[float]
    # Declare source_temporal_assessment_timestamp as Optional[float] for this data structure.
    source_temporal_assessment_timestamp: Optional[float]
    # Declare source_regulatory_assessment_timestamp as Optional[float] for this data structure.
    source_regulatory_assessment_timestamp: Optional[float]
    # Declare source_snapshot_consistent as bool for this data structure.
    source_snapshot_consistent: bool
    # Set control_actions_issued to 0; declare its type as int.
    control_actions_issued: int = 0

    # To dict using the inputs and processing steps below.
    # Output: the result of asdict(self).
    def to_dict(self):
        # Return the result of asdict(self) to the caller.
        return asdict(self)
