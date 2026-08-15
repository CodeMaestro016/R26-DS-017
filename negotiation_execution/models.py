"""Immutable Step 5J.2B physical precedence-execution records."""

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping, Optional, Tuple


def _freeze(value): return MappingProxyType(dict(value))


@dataclass(frozen=True)
class ConflictZoneExecutionConstraint:
    yielding_vehicle_id: str
    priority_vehicle_id: str
    conflict_zone_id: str
    source_precedence_edge: tuple
    source_protocol_state: str
    source_snapshot_id: tuple
    constraint_status: str
    provenance: Mapping[str, str]

    def __post_init__(self):
        object.__setattr__(self, "provenance", _freeze(self.provenance))


@dataclass(frozen=True)
class VehicleConflictZonePermission:
    vehicle_id: str
    conflict_zone_id: str
    permission_status: str
    blocking_vehicle_ids: Tuple[str, ...]
    source_effective_graph: Tuple[tuple, ...]
    timestamp: float
    provenance: Mapping[str, str]

    def __post_init__(self):
        object.__setattr__(self, "provenance", _freeze(self.provenance))


@dataclass(frozen=True)
class ConflictZoneExecutionPlan:
    plan_id: tuple
    source_snapshot_id: tuple
    effective_coordination_graph: Tuple[tuple, ...]
    active_vehicle_ids: Tuple[str, ...]
    constraints: Tuple[ConflictZoneExecutionConstraint, ...]
    vehicle_permissions: Tuple[VehicleConflictZonePermission, ...]
    ready_vehicle_ids: Tuple[str, ...]
    blocked_vehicle_ids: Tuple[str, ...]
    graph_status: str
    provenance: Mapping[str, str]

    def __post_init__(self):
        object.__setattr__(self, "provenance", _freeze(self.provenance))


@dataclass(frozen=True)
class SpeedConstraintRecord:
    vehicle_id: str
    conflict_zone_id: str
    distance_to_zone_entry: float
    comfortable_deceleration_mps2: float
    current_speed_mps: float
    requested_speed_cap_mps: float
    physically_feasible: bool
    provenance: Mapping[str, str]

    def __post_init__(self):
        object.__setattr__(self, "provenance", _freeze(self.provenance))


@dataclass(frozen=True)
class NegotiationTrafficCausalTrace:
    trace_id: tuple
    scenario_id: tuple
    protocol_branch: str
    source_snapshot_id: tuple
    original_precedence_graph: Tuple[tuple, ...]
    effective_precedence_graph: Tuple[tuple, ...]
    execution_plan_ids: Tuple[tuple, ...]
    vehicle_permission_transitions: Tuple[tuple, ...]
    speed_constraint_records: Tuple[SpeedConstraintRecord, ...]
    conflict_zone_entry_events: Tuple[tuple, ...]
    conflict_zone_clear_events: Tuple[tuple, ...]
    episode_team_travel_time_seconds: Optional[float]
    episode_raw_team_reward: Optional[float]
    causal_status: str
    action_source: str
    provenance: Mapping[str, str]

    def __post_init__(self):
        object.__setattr__(self, "provenance", _freeze(self.provenance))

