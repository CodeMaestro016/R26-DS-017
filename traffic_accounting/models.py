"""Immutable scheduled-demand and SUMO lifecycle accounting contracts."""

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Mapping, Optional, Tuple


SCHEDULED_DEMAND_ACCOUNTING_STATUS = "IMPLEMENTED_STEP_5H_0"
OBJECTIVE_FORMULATION_STATUS = "BLOCKER_RESOLVED_READY_FOR_STEP_5H"


class DemandScheduleSource(str, Enum):
    INITIAL_SIMULATION_DEMAND = "INITIAL_SIMULATION_DEMAND"
    VALIDATION_SPAWN_SCHEDULE = "VALIDATION_SPAWN_SCHEDULE"
    PERIODIC_SPAWN_SCHEDULE = "PERIODIC_SPAWN_SCHEDULE"


class VehicleDemandStatus(str, Enum):
    SCHEDULED_WAITING_FOR_DEPARTURE = "SCHEDULED_WAITING_FOR_DEPARTURE"
    ACTIVE_IN_NETWORK = "ACTIVE_IN_NETWORK"
    SERVICE_COMPLETED = "SERVICE_COMPLETED"
    SCHEDULED_NOT_DEPARTED_AT_EPISODE_END = "SCHEDULED_NOT_DEPARTED_AT_EPISODE_END"
    DEPARTED_NOT_COMPLETED_AT_EPISODE_END = "DEPARTED_NOT_COMPLETED_AT_EPISODE_END"


@dataclass(frozen=True)
class VehicleDemandRecord:
    vehicle_id: str
    scheduled_spawn_time: float
    actual_departure_time: Optional[float]
    service_completion_time: Optional[float]
    route_or_movement_metadata: Mapping[str, str]
    schedule_source: DemandScheduleSource
    completion_status: VehicleDemandStatus
    provenance: Mapping[str, str]

    def __post_init__(self):
        object.__setattr__(self, "route_or_movement_metadata",
                           MappingProxyType(dict(self.route_or_movement_metadata)))
        object.__setattr__(self, "provenance", MappingProxyType(dict(self.provenance)))


@dataclass(frozen=True)
class SimulationLifecycleEvents:
    timestamp: float
    departed_vehicle_ids: Tuple[str, ...]
    arrived_vehicle_ids: Tuple[str, ...]

