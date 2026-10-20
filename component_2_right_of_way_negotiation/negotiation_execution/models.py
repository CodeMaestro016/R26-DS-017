"""Immutable Step 5J.2B physical precedence-execution records."""

# Import dataclass from dataclasses for the operations below.
from dataclasses import dataclass
# Import MappingProxyType from types for the operations below.
from types import MappingProxyType
# Import Mapping, Optional, Tuple from typing for the operations below.
from typing import Mapping, Optional, Tuple


# Freeze using the inputs and processing steps below.
# Input value: the supplied value.
# Output: the result of MappingProxyType(a dictionary built from value).
# Return the result of MappingProxyType(a dictionary built from value) to the caller.
def _freeze(value): return MappingProxyType(dict(value))


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define ConflictZoneExecutionConstraint to group the state and operations declared below.
# Declared fields: yielding_vehicle_id, priority_vehicle_id, conflict_zone_id, source_precedence_edge,
# source_protocol_state, source_snapshot_id, constraint_status, provenance.
# Construction and attribute behavior follow the declared decorators and base classes.
class ConflictZoneExecutionConstraint:
    # Declare yielding_vehicle_id as str for this data structure.
    yielding_vehicle_id: str
    # Declare priority_vehicle_id as str for this data structure.
    priority_vehicle_id: str
    # Declare conflict_zone_id as str for this data structure.
    conflict_zone_id: str
    # Declare source_precedence_edge as tuple for this data structure.
    source_precedence_edge: tuple
    # Declare source_protocol_state as str for this data structure.
    source_protocol_state: str
    # Declare source_snapshot_id as tuple for this data structure.
    source_snapshot_id: tuple
    # Declare constraint_status as str for this data structure.
    constraint_status: str
    # Declare provenance as Mapping[str, str] for this data structure.
    provenance: Mapping[str, str]

    # Post init using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    def __post_init__(self):
        # Call object.__setattr__ with the supplied arguments.
        object.__setattr__(self, "provenance", _freeze(self.provenance))


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define VehicleConflictZonePermission to group the state and operations declared below.
# Declared fields: vehicle_id, conflict_zone_id, permission_status, blocking_vehicle_ids, source_effective_graph,
# timestamp, provenance.
# Construction and attribute behavior follow the declared decorators and base classes.
class VehicleConflictZonePermission:
    # Declare vehicle_id as str for this data structure.
    vehicle_id: str
    # Declare conflict_zone_id as str for this data structure.
    conflict_zone_id: str
    # Declare permission_status as str for this data structure.
    permission_status: str
    # Declare blocking_vehicle_ids as Tuple[str, ...] for this data structure.
    blocking_vehicle_ids: Tuple[str, ...]
    # Declare source_effective_graph as Tuple[tuple, ...] for this data structure.
    source_effective_graph: Tuple[tuple, ...]
    # Declare timestamp as float for this data structure.
    timestamp: float
    # Declare provenance as Mapping[str, str] for this data structure.
    provenance: Mapping[str, str]

    # Post init using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    def __post_init__(self):
        # Call object.__setattr__ with the supplied arguments.
        object.__setattr__(self, "provenance", _freeze(self.provenance))


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define ConflictZoneExecutionPlan to group the state and operations declared below.
# Declared fields: plan_id, source_snapshot_id, effective_coordination_graph, active_vehicle_ids, constraints,
# vehicle_permissions, ready_vehicle_ids, blocked_vehicle_ids, graph_status, provenance.
# Construction and attribute behavior follow the declared decorators and base classes.
class ConflictZoneExecutionPlan:
    # Declare plan_id as tuple for this data structure.
    plan_id: tuple
    # Declare source_snapshot_id as tuple for this data structure.
    source_snapshot_id: tuple
    # Declare effective_coordination_graph as Tuple[tuple, ...] for this data structure.
    effective_coordination_graph: Tuple[tuple, ...]
    # Declare active_vehicle_ids as Tuple[str, ...] for this data structure.
    active_vehicle_ids: Tuple[str, ...]
    # Declare constraints as Tuple[ConflictZoneExecutionConstraint, ...] for this data structure.
    constraints: Tuple[ConflictZoneExecutionConstraint, ...]
    # Declare vehicle_permissions as Tuple[VehicleConflictZonePermission, ...] for this data structure.
    vehicle_permissions: Tuple[VehicleConflictZonePermission, ...]
    # Declare ready_vehicle_ids as Tuple[str, ...] for this data structure.
    ready_vehicle_ids: Tuple[str, ...]
    # Declare blocked_vehicle_ids as Tuple[str, ...] for this data structure.
    blocked_vehicle_ids: Tuple[str, ...]
    # Declare graph_status as str for this data structure.
    graph_status: str
    # Declare provenance as Mapping[str, str] for this data structure.
    provenance: Mapping[str, str]

    # Post init using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    def __post_init__(self):
        # Call object.__setattr__ with the supplied arguments.
        object.__setattr__(self, "provenance", _freeze(self.provenance))


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define SpeedConstraintRecord to group the state and operations declared below.
# Declared fields: vehicle_id, conflict_zone_id, distance_to_zone_entry, comfortable_deceleration_mps2,
# current_speed_mps, requested_speed_cap_mps, physically_feasible, provenance, simulation_step_seconds,....
# Construction and attribute behavior follow the declared decorators and base classes.
class SpeedConstraintRecord:
    # Declare vehicle_id as str for this data structure.
    vehicle_id: str
    # Declare conflict_zone_id as str for this data structure.
    conflict_zone_id: str
    # Declare distance_to_zone_entry as float for this data structure.
    distance_to_zone_entry: float
    # Declare comfortable_deceleration_mps2 as float for this data structure.
    comfortable_deceleration_mps2: float
    # Declare current_speed_mps as float for this data structure.
    current_speed_mps: float
    # Declare requested_speed_cap_mps as float for this data structure.
    requested_speed_cap_mps: float
    # Declare physically_feasible as bool for this data structure.
    physically_feasible: bool
    # Declare provenance as Mapping[str, str] for this data structure.
    provenance: Mapping[str, str]
    # Set simulation_step_seconds to None; declare its type as Optional[float].
    simulation_step_seconds: Optional[float] = None
    # Set action_step_length_seconds to None; declare its type as Optional[float].
    action_step_length_seconds: Optional[float] = None
    # Set continuous_reference_cap_mps to None; declare its type as Optional[float].
    continuous_reference_cap_mps: Optional[float] = None
    # Set discrete_euler_brake_gap_m to None; declare its type as Optional[float].
    discrete_euler_brake_gap_m: Optional[float] = None
    # Set sumo_stop_speed_mps to None; declare its type as Optional[float].
    sumo_stop_speed_mps: Optional[float] = None
    # Set comfortable_min_next_speed_mps to None; declare its type as Optional[float].
    comfortable_min_next_speed_mps: Optional[float] = None
    # Set native_sumo_speed_without_traci_mps to None; declare its type as Optional[float].
    native_sumo_speed_without_traci_mps: Optional[float] = None
    # Set requested_precedence_speed_mps to None; declare its type as Optional[float].
    requested_precedence_speed_mps: Optional[float] = None
    # Set comfortable_feasible to None; declare its type as Optional[bool].
    comfortable_feasible: Optional[bool] = None
    # Set integration_method to None; declare its type as Optional[str].
    integration_method: Optional[str] = None
    # Set comfortable_feasibility_status to None; declare its type as Optional[str].
    comfortable_feasibility_status: Optional[str] = None
    # Set actual_realized_next_speed_mps to None; declare its type as Optional[float].
    actual_realized_next_speed_mps: Optional[float] = None
    # Set actual_realized_acceleration_mps2 to None; declare its type as Optional[float].
    actual_realized_acceleration_mps2: Optional[float] = None
    # Set sumo_max_deceleration_enforcement_active to None; declare its type as Optional[bool].
    sumo_max_deceleration_enforcement_active: Optional[bool] = None
    # Set sumo_safe_speed_enforcement_active to None; declare its type as Optional[bool].
    sumo_safe_speed_enforcement_active: Optional[bool] = None
    # Set sumo_max_acceleration_enforcement_active to None; declare its type as Optional[bool].
    sumo_max_acceleration_enforcement_active: Optional[bool] = None
    # Set sumo_junction_priority_enforcement_active to None; declare its type as Optional[bool].
    sumo_junction_priority_enforcement_active: Optional[bool] = None
    # Set runtime_authority to None; declare its type as Optional[str].
    runtime_authority: Optional[str] = None
    # Set precommand_python_feasibility_rejection to None; declare its type as Optional[bool].
    precommand_python_feasibility_rejection: Optional[bool] = None
    # Set speed_mode to None; declare its type as Optional[int].
    speed_mode: Optional[int] = None

    # Post init using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    def __post_init__(self):
        # Call object.__setattr__ with the supplied arguments.
        object.__setattr__(self, "provenance", _freeze(self.provenance))


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define NegotiationTrafficCausalTrace to group the state and operations declared below.
# Declared fields: trace_id, scenario_id, protocol_branch, source_snapshot_id, original_precedence_graph,
# effective_precedence_graph, execution_plan_ids, vehicle_permission_transitions, speed_constraint_records,....
# Construction and attribute behavior follow the declared decorators and base classes.
class NegotiationTrafficCausalTrace:
    # Declare trace_id as tuple for this data structure.
    trace_id: tuple
    # Declare scenario_id as tuple for this data structure.
    scenario_id: tuple
    # Declare protocol_branch as str for this data structure.
    protocol_branch: str
    # Declare source_snapshot_id as tuple for this data structure.
    source_snapshot_id: tuple
    # Declare original_precedence_graph as Tuple[tuple, ...] for this data structure.
    original_precedence_graph: Tuple[tuple, ...]
    # Declare effective_precedence_graph as Tuple[tuple, ...] for this data structure.
    effective_precedence_graph: Tuple[tuple, ...]
    # Declare execution_plan_ids as Tuple[tuple, ...] for this data structure.
    execution_plan_ids: Tuple[tuple, ...]
    # Declare vehicle_permission_transitions as Tuple[tuple, ...] for this data structure.
    vehicle_permission_transitions: Tuple[tuple, ...]
    # Declare speed_constraint_records as Tuple[SpeedConstraintRecord, ...] for this data structure.
    speed_constraint_records: Tuple[SpeedConstraintRecord, ...]
    # Declare conflict_zone_entry_events as Tuple[tuple, ...] for this data structure.
    conflict_zone_entry_events: Tuple[tuple, ...]
    # Declare conflict_zone_clear_events as Tuple[tuple, ...] for this data structure.
    conflict_zone_clear_events: Tuple[tuple, ...]
    # Declare episode_team_travel_time_seconds as Optional[float] for this data structure.
    episode_team_travel_time_seconds: Optional[float]
    # Declare episode_raw_team_reward as Optional[float] for this data structure.
    episode_raw_team_reward: Optional[float]
    # Declare causal_status as str for this data structure.
    causal_status: str
    # Declare action_source as str for this data structure.
    action_source: str
    # Declare provenance as Mapping[str, str] for this data structure.
    provenance: Mapping[str, str]

    # Post init using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    def __post_init__(self):
        # Call object.__setattr__ with the supplied arguments.
        object.__setattr__(self, "provenance", _freeze(self.provenance))
