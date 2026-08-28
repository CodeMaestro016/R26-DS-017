"""Immutable messages for the ideal same-step V2V research baseline."""

from dataclasses import asdict, dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class PrecedenceClaimMessage:
    """A sender-local claim: yielding_vehicle_id -> priority_vehicle_id."""

    sender_id: str
    timestamp: float
    yielding_vehicle_id: str
    priority_vehicle_id: str
    applicable_rule_ids: Tuple[str, ...]
    source_sections: Tuple[str, ...]
    regulatory_profile: str
    shared_conflict_zone_ids: Tuple[str, ...]
    conflict_types: Tuple[str, ...]
    target_candidate_path_ids: Tuple[str, ...]
    source_conflict_graph_timestamp: float
    source_regulatory_assessment_timestamp: float
    source_observation_age_seconds: Optional[float] = None

    def to_dict(self):
        return asdict(self)
