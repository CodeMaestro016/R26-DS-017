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
    simulation_step_seconds: Optional[float] = None
    action_step_length_seconds: Optional[float] = None
    continuous_reference_cap_mps: Optional[float] = None
    discrete_euler_brake_gap_m: Optional[float] = None
    sumo_stop_speed_mps: Optional[float] = None
    comfortable_min_next_speed_mps: Optional[float] = None
    native_sumo_speed_without_traci_mps: Optional[float] = None
    requested_precedence_speed_mps: Optional[float] = None
    comfortable_feasible: Optional[bool] = None
    integration_method: Optional[str] = None
    comfortable_feasibility_status: Optional[str] = None
    actual_realized_next_speed_mps: Optional[float] = None
    actual_realized_acceleration_mps2: Optional[float] = None
    sumo_max_deceleration_enforcement_active: Optional[bool] = None
    sumo_safe_speed_enforcement_active: Optional[bool] = None
    sumo_max_acceleration_enforcement_active: Optional[bool] = None
    sumo_junction_priority_enforcement_active: Optional[bool] = None
    runtime_authority: Optional[str] = None
    precommand_python_feasibility_rejection: Optional[bool] = None
    speed_mode: Optional[int] = None

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
