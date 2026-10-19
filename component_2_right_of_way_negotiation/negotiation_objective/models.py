"""Immutable physical-time objective records for Step 5H."""

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping, Optional, Tuple


OBJECTIVE_FORMULATION_STATUS = "IMPLEMENTED_STEP_5H"
BASELINE_REWARD_DEFINITION = "NEGATIVE_TEAM_TRAVEL_TIME_INCREMENT"
REWARD_DEFINITION_ID = "NEGATIVE_TEAM_TRAVEL_TIME_INCREMENT_V1"
REWARD_SCOPE_STATUS = "SHARED_TEAM_BASELINE"
LOCAL_VS_TEAM_REWARD_ABLATION = "OPTIONAL_FUTURE_EXPERIMENT"
MINIMIZATION_TO_MAXIMIZATION_SIGN = "MATHEMATICAL_EQUIVALENCE_NOT_HYPERPARAMETER"
REGULATORY_CONSTRAINT_ROLE = "HARD_FEASIBILITY_NOT_REWARD"
SAFETY_REWARD_STATUS = "NOT_USED_AS_SOFT_REWARD_BASELINE"
SAFETY_AUTHORITY_STATUS = "FUTURE_INDEPENDENT_SAFETY_SHIELD_REQUIRED"
FAIRNESS_REWARD_INTEGRATION_STATUS = "REQUIRES_EXPERIMENTAL_OR_FORMAL_SCALARIZATION"
ADDITIONAL_DELAY_OBJECTIVE_STATUS = "REQUIRES_MEASURED_BASELINE"
THROUGHPUT_REWARD_STATUS = "EVALUATION_DIAGNOSTIC_NOT_SEPARATE_REWARD_TERM"
DEADLOCK_REWARD_STATUS = "NOT_INCLUDED_UNTIL_NONARBITRARY_SEMANTICS_DEFINED"


@dataclass(frozen=True)
class VehicleTravelTimeMeasurement:
    vehicle_id: str
    scheduled_spawn_time: float
    actual_departure_time: Optional[float]
    service_end_time: float
    service_completion_time: Optional[float]
    observed_travel_time_seconds: float
    completion_status: str
    provenance: Mapping[str, str]

    def __post_init__(self):
        object.__setattr__(self, "provenance", MappingProxyType(dict(self.provenance)))


@dataclass(frozen=True)
class VehicleExposureRecord:
    vehicle_id: str
    interval_start_timestamp: float
    interval_end_timestamp: float
    exposure_seconds: float


@dataclass(frozen=True)
class JointNegotiationDecisionBatch:
    batch_id: tuple
    snapshot_id: tuple
    timestamp: float
    phase_identity: str
    decision_event_ids: Tuple[tuple, ...]
    participating_ego_ids: Tuple[str, ...]
    claim_or_proposal_subjects: Tuple[tuple, ...]


@dataclass(frozen=True)
class GlobalObjectiveInterval:
    objective_interval_id: tuple
    start_event_id: tuple
    end_event_id: tuple
    start_timestamp: float
    end_timestamp: float
    elapsed_seconds: float
    vehicle_exposure_records: Tuple[VehicleExposureRecord, ...]
    team_travel_time_increment_seconds: float
    raw_team_reward: float
    provenance: Mapping[str, str]

    def __post_init__(self):
        object.__setattr__(self, "provenance", MappingProxyType(dict(self.provenance)))


@dataclass(frozen=True)
class TeamObjectiveRecord:
    objective_interval_id: tuple
    source_batch_id: tuple
    successor_batch_id: tuple
    team_travel_time_increment_seconds: float
    team_reward: float
    reward_definition_id: str
    metric_units: str
    provenance: Mapping[str, str]

    def __post_init__(self):
        object.__setattr__(self, "provenance", MappingProxyType(dict(self.provenance)))


@dataclass(frozen=True)
class ObjectiveDiagnostics:
    vehicles_measured: int
    completed_services: int
    mean_travel_time_seconds: float
    minimum_travel_time_seconds: float
    maximum_travel_time_seconds: float
    travel_time_variance_seconds_squared: float

