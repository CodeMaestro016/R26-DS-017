"""Immutable scheduled-demand and SUMO lifecycle accounting contracts."""

# Import dataclass from dataclasses for the operations below.
from dataclasses import dataclass
# Import Enum from enum for the operations below.
from enum import Enum
# Import MappingProxyType from types for the operations below.
from types import MappingProxyType
# Import Mapping, Optional, Tuple from typing for the operations below.
from typing import Mapping, Optional, Tuple


# Set SCHEDULED_DEMAND_ACCOUNTING_STATUS to the text 'IMPLEMENTED_STEP_5H_0'.
SCHEDULED_DEMAND_ACCOUNTING_STATUS = "IMPLEMENTED_STEP_5H_0"
# Set OBJECTIVE_FORMULATION_STATUS to the text 'BLOCKER_RESOLVED_READY_FOR_STEP_5H'.
OBJECTIVE_FORMULATION_STATUS = "BLOCKER_RESOLVED_READY_FOR_STEP_5H"


# Define DemandScheduleSource to group the state and operations declared below.
# Base classes: str, Enum.
# Instances expose the attributes and methods implemented in this class.
class DemandScheduleSource(str, Enum):
    # Set INITIAL_SIMULATION_DEMAND to the text 'INITIAL_SIMULATION_DEMAND'.
    INITIAL_SIMULATION_DEMAND = "INITIAL_SIMULATION_DEMAND"
    # Set VALIDATION_SPAWN_SCHEDULE to the text 'VALIDATION_SPAWN_SCHEDULE'.
    VALIDATION_SPAWN_SCHEDULE = "VALIDATION_SPAWN_SCHEDULE"
    # Set PERIODIC_SPAWN_SCHEDULE to the text 'PERIODIC_SPAWN_SCHEDULE'.
    PERIODIC_SPAWN_SCHEDULE = "PERIODIC_SPAWN_SCHEDULE"


# Define VehicleDemandStatus to group the state and operations declared below.
# Base classes: str, Enum.
# Instances expose the attributes and methods implemented in this class.
class VehicleDemandStatus(str, Enum):
    # Set SCHEDULED_WAITING_FOR_DEPARTURE to the text 'SCHEDULED_WAITING_FOR_DEPARTURE'.
    SCHEDULED_WAITING_FOR_DEPARTURE = "SCHEDULED_WAITING_FOR_DEPARTURE"
    # Set ACTIVE_IN_NETWORK to the text 'ACTIVE_IN_NETWORK'.
    ACTIVE_IN_NETWORK = "ACTIVE_IN_NETWORK"
    # Set SERVICE_COMPLETED to the text 'SERVICE_COMPLETED'.
    SERVICE_COMPLETED = "SERVICE_COMPLETED"
    # Set SCHEDULED_NOT_DEPARTED_AT_EPISODE_END to the text 'SCHEDULED_NOT_DEPARTED_AT_EPISODE_END'.
    SCHEDULED_NOT_DEPARTED_AT_EPISODE_END = "SCHEDULED_NOT_DEPARTED_AT_EPISODE_END"
    # Set DEPARTED_NOT_COMPLETED_AT_EPISODE_END to the text 'DEPARTED_NOT_COMPLETED_AT_EPISODE_END'.
    DEPARTED_NOT_COMPLETED_AT_EPISODE_END = "DEPARTED_NOT_COMPLETED_AT_EPISODE_END"


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define VehicleDemandRecord to group the state and operations declared below.
# Declared fields: vehicle_id, scheduled_spawn_time, actual_departure_time, service_completion_time,
# route_or_movement_metadata, schedule_source, completion_status, provenance.
# Construction and attribute behavior follow the declared decorators and base classes.
class VehicleDemandRecord:
    # Declare vehicle_id as str for this data structure.
    vehicle_id: str
    # Declare scheduled_spawn_time as float for this data structure.
    scheduled_spawn_time: float
    # Declare actual_departure_time as Optional[float] for this data structure.
    actual_departure_time: Optional[float]
    # Declare service_completion_time as Optional[float] for this data structure.
    service_completion_time: Optional[float]
    # Declare route_or_movement_metadata as Mapping[str, str] for this data structure.
    route_or_movement_metadata: Mapping[str, str]
    # Declare schedule_source as DemandScheduleSource for this data structure.
    schedule_source: DemandScheduleSource
    # Declare completion_status as VehicleDemandStatus for this data structure.
    completion_status: VehicleDemandStatus
    # Declare provenance as Mapping[str, str] for this data structure.
    provenance: Mapping[str, str]

    # Post init using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    def __post_init__(self):
        # Call object.__setattr__ with the supplied arguments.
        object.__setattr__(self, "route_or_movement_metadata",
                           # Supply the result of MappingProxyType(a dictionary built from
                           # self.route_or_movement_metadata) to object.__setattr__.
                           MappingProxyType(dict(self.route_or_movement_metadata)))
        # Call object.__setattr__ with the supplied arguments.
        object.__setattr__(self, "provenance", MappingProxyType(dict(self.provenance)))


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define SimulationLifecycleEvents to group the state and operations declared below.
# Declared fields: timestamp, departed_vehicle_ids, arrived_vehicle_ids.
# Construction and attribute behavior follow the declared decorators and base classes.
class SimulationLifecycleEvents:
    # Declare timestamp as float for this data structure.
    timestamp: float
    # Declare departed_vehicle_ids as Tuple[str, ...] for this data structure.
    departed_vehicle_ids: Tuple[str, ...]
    # Declare arrived_vehicle_ids as Tuple[str, ...] for this data structure.
    arrived_vehicle_ids: Tuple[str, ...]

