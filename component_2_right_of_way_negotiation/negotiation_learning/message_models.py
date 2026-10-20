"""Immutable messages for the ideal same-step V2V research baseline."""

# Import asdict, dataclass from dataclasses for the operations below.
from dataclasses import asdict, dataclass
# Import Optional, Tuple from typing for the operations below.
from typing import Optional, Tuple


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# A sender-local claim: yielding_vehicle_id -> priority_vehicle_id.
# Declared fields: sender_id, timestamp, yielding_vehicle_id, priority_vehicle_id, applicable_rule_ids,
# source_sections, regulatory_profile, shared_conflict_zone_ids, conflict_types, target_candidate_path_ids,....
# Construction and attribute behavior follow the declared decorators and base classes.
class PrecedenceClaimMessage:
    """A sender-local claim: yielding_vehicle_id -> priority_vehicle_id."""

    # Declare sender_id as str for this data structure.
    sender_id: str
    # Declare timestamp as float for this data structure.
    timestamp: float
    # Declare yielding_vehicle_id as str for this data structure.
    yielding_vehicle_id: str
    # Declare priority_vehicle_id as str for this data structure.
    priority_vehicle_id: str
    # Declare applicable_rule_ids as Tuple[str, ...] for this data structure.
    applicable_rule_ids: Tuple[str, ...]
    # Declare source_sections as Tuple[str, ...] for this data structure.
    source_sections: Tuple[str, ...]
    # Declare regulatory_profile as str for this data structure.
    regulatory_profile: str
    # Declare shared_conflict_zone_ids as Tuple[str, ...] for this data structure.
    shared_conflict_zone_ids: Tuple[str, ...]
    # Declare conflict_types as Tuple[str, ...] for this data structure.
    conflict_types: Tuple[str, ...]
    # Declare target_candidate_path_ids as Tuple[str, ...] for this data structure.
    target_candidate_path_ids: Tuple[str, ...]
    # Declare source_conflict_graph_timestamp as float for this data structure.
    source_conflict_graph_timestamp: float
    # Declare source_regulatory_assessment_timestamp as float for this data structure.
    source_regulatory_assessment_timestamp: float
    # Set source_observation_age_seconds to None; declare its type as Optional[float].
    source_observation_age_seconds: Optional[float] = None
    # Set negotiation_eligible_ambiguity to False; declare its type as bool.
    negotiation_eligible_ambiguity: bool = False

    # To dict using the inputs and processing steps below.
    # Output: the result of asdict(self).
    def to_dict(self):
        # Return the result of asdict(self) to the caller.
        return asdict(self)
