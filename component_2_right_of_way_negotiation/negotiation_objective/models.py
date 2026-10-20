"""Immutable physical-time objective records for Step 5H."""

# Import dataclass from dataclasses for the operations below.
from dataclasses import dataclass
# Import MappingProxyType from types for the operations below.
from types import MappingProxyType
# Import Mapping, Optional, Tuple from typing for the operations below.
from typing import Mapping, Optional, Tuple


# Set OBJECTIVE_FORMULATION_STATUS to the text 'IMPLEMENTED_STEP_5H'.
OBJECTIVE_FORMULATION_STATUS = "IMPLEMENTED_STEP_5H"
# Set BASELINE_REWARD_DEFINITION to the text 'NEGATIVE_TEAM_TRAVEL_TIME_INCREMENT'.
BASELINE_REWARD_DEFINITION = "NEGATIVE_TEAM_TRAVEL_TIME_INCREMENT"
# Set REWARD_DEFINITION_ID to the text 'NEGATIVE_TEAM_TRAVEL_TIME_INCREMENT_V1'.
REWARD_DEFINITION_ID = "NEGATIVE_TEAM_TRAVEL_TIME_INCREMENT_V1"
# Set REWARD_SCOPE_STATUS to the text 'SHARED_TEAM_BASELINE'.
REWARD_SCOPE_STATUS = "SHARED_TEAM_BASELINE"
# Set LOCAL_VS_TEAM_REWARD_ABLATION to the text 'OPTIONAL_FUTURE_EXPERIMENT'.
LOCAL_VS_TEAM_REWARD_ABLATION = "OPTIONAL_FUTURE_EXPERIMENT"
# Set MINIMIZATION_TO_MAXIMIZATION_SIGN to the text 'MATHEMATICAL_EQUIVALENCE_NOT_HYPERPARAMETER'.
MINIMIZATION_TO_MAXIMIZATION_SIGN = "MATHEMATICAL_EQUIVALENCE_NOT_HYPERPARAMETER"
# Set REGULATORY_CONSTRAINT_ROLE to the text 'HARD_FEASIBILITY_NOT_REWARD'.
REGULATORY_CONSTRAINT_ROLE = "HARD_FEASIBILITY_NOT_REWARD"
# Set SAFETY_REWARD_STATUS to the text 'NOT_USED_AS_SOFT_REWARD_BASELINE'.
SAFETY_REWARD_STATUS = "NOT_USED_AS_SOFT_REWARD_BASELINE"
# Set SAFETY_AUTHORITY_STATUS to the text 'FUTURE_INDEPENDENT_SAFETY_SHIELD_REQUIRED'.
SAFETY_AUTHORITY_STATUS = "FUTURE_INDEPENDENT_SAFETY_SHIELD_REQUIRED"
# Set FAIRNESS_REWARD_INTEGRATION_STATUS to the text 'REQUIRES_EXPERIMENTAL_OR_FORMAL_SCALARIZATION'.
FAIRNESS_REWARD_INTEGRATION_STATUS = "REQUIRES_EXPERIMENTAL_OR_FORMAL_SCALARIZATION"
# Set ADDITIONAL_DELAY_OBJECTIVE_STATUS to the text 'REQUIRES_MEASURED_BASELINE'.
ADDITIONAL_DELAY_OBJECTIVE_STATUS = "REQUIRES_MEASURED_BASELINE"
# Set THROUGHPUT_REWARD_STATUS to the text 'EVALUATION_DIAGNOSTIC_NOT_SEPARATE_REWARD_TERM'.
THROUGHPUT_REWARD_STATUS = "EVALUATION_DIAGNOSTIC_NOT_SEPARATE_REWARD_TERM"
# Set DEADLOCK_REWARD_STATUS to the text 'NOT_INCLUDED_UNTIL_NONARBITRARY_SEMANTICS_DEFINED'.
DEADLOCK_REWARD_STATUS = "NOT_INCLUDED_UNTIL_NONARBITRARY_SEMANTICS_DEFINED"


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define VehicleTravelTimeMeasurement to group the state and operations declared below.
# Declared fields: vehicle_id, scheduled_spawn_time, actual_departure_time, service_end_time,
# service_completion_time, observed_travel_time_seconds, completion_status, provenance.
# Construction and attribute behavior follow the declared decorators and base classes.
class VehicleTravelTimeMeasurement:
    # Declare vehicle_id as str for this data structure.
    vehicle_id: str
    # Declare scheduled_spawn_time as float for this data structure.
    scheduled_spawn_time: float
    # Declare actual_departure_time as Optional[float] for this data structure.
    actual_departure_time: Optional[float]
    # Declare service_end_time as float for this data structure.
    service_end_time: float
    # Declare service_completion_time as Optional[float] for this data structure.
    service_completion_time: Optional[float]
    # Declare observed_travel_time_seconds as float for this data structure.
    observed_travel_time_seconds: float
    # Declare completion_status as str for this data structure.
    completion_status: str
    # Declare provenance as Mapping[str, str] for this data structure.
    provenance: Mapping[str, str]

    # Post init using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    def __post_init__(self):
        # Call object.__setattr__ with the supplied arguments.
        object.__setattr__(self, "provenance", MappingProxyType(dict(self.provenance)))


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define VehicleExposureRecord to group the state and operations declared below.
# Declared fields: vehicle_id, interval_start_timestamp, interval_end_timestamp, exposure_seconds.
# Construction and attribute behavior follow the declared decorators and base classes.
class VehicleExposureRecord:
    # Declare vehicle_id as str for this data structure.
    vehicle_id: str
    # Declare interval_start_timestamp as float for this data structure.
    interval_start_timestamp: float
    # Declare interval_end_timestamp as float for this data structure.
    interval_end_timestamp: float
    # Declare exposure_seconds as float for this data structure.
    exposure_seconds: float


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define JointNegotiationDecisionBatch to group the state and operations declared below.
# Declared fields: batch_id, snapshot_id, timestamp, phase_identity, decision_event_ids, participating_ego_ids,
# claim_or_proposal_subjects.
# Construction and attribute behavior follow the declared decorators and base classes.
class JointNegotiationDecisionBatch:
    # Declare batch_id as tuple for this data structure.
    batch_id: tuple
    # Declare snapshot_id as tuple for this data structure.
    snapshot_id: tuple
    # Declare timestamp as float for this data structure.
    timestamp: float
    # Declare phase_identity as str for this data structure.
    phase_identity: str
    # Declare decision_event_ids as Tuple[tuple, ...] for this data structure.
    decision_event_ids: Tuple[tuple, ...]
    # Declare participating_ego_ids as Tuple[str, ...] for this data structure.
    participating_ego_ids: Tuple[str, ...]
    # Declare claim_or_proposal_subjects as Tuple[tuple, ...] for this data structure.
    claim_or_proposal_subjects: Tuple[tuple, ...]


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define GlobalObjectiveInterval to group the state and operations declared below.
# Declared fields: objective_interval_id, start_event_id, end_event_id, start_timestamp, end_timestamp,
# elapsed_seconds, vehicle_exposure_records, team_travel_time_increment_seconds, raw_team_reward, provenance.
# Construction and attribute behavior follow the declared decorators and base classes.
class GlobalObjectiveInterval:
    # Declare objective_interval_id as tuple for this data structure.
    objective_interval_id: tuple
    # Declare start_event_id as tuple for this data structure.
    start_event_id: tuple
    # Declare end_event_id as tuple for this data structure.
    end_event_id: tuple
    # Declare start_timestamp as float for this data structure.
    start_timestamp: float
    # Declare end_timestamp as float for this data structure.
    end_timestamp: float
    # Declare elapsed_seconds as float for this data structure.
    elapsed_seconds: float
    # Declare vehicle_exposure_records as Tuple[VehicleExposureRecord, ...] for this data structure.
    vehicle_exposure_records: Tuple[VehicleExposureRecord, ...]
    # Declare team_travel_time_increment_seconds as float for this data structure.
    team_travel_time_increment_seconds: float
    # Declare raw_team_reward as float for this data structure.
    raw_team_reward: float
    # Declare provenance as Mapping[str, str] for this data structure.
    provenance: Mapping[str, str]

    # Post init using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    def __post_init__(self):
        # Call object.__setattr__ with the supplied arguments.
        object.__setattr__(self, "provenance", MappingProxyType(dict(self.provenance)))


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define TeamObjectiveRecord to group the state and operations declared below.
# Declared fields: objective_interval_id, source_batch_id, successor_batch_id, team_travel_time_increment_seconds,
# team_reward, reward_definition_id, metric_units, provenance.
# Construction and attribute behavior follow the declared decorators and base classes.
class TeamObjectiveRecord:
    # Declare objective_interval_id as tuple for this data structure.
    objective_interval_id: tuple
    # Declare source_batch_id as tuple for this data structure.
    source_batch_id: tuple
    # Declare successor_batch_id as tuple for this data structure.
    successor_batch_id: tuple
    # Declare team_travel_time_increment_seconds as float for this data structure.
    team_travel_time_increment_seconds: float
    # Declare team_reward as float for this data structure.
    team_reward: float
    # Declare reward_definition_id as str for this data structure.
    reward_definition_id: str
    # Declare metric_units as str for this data structure.
    metric_units: str
    # Declare provenance as Mapping[str, str] for this data structure.
    provenance: Mapping[str, str]

    # Post init using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    def __post_init__(self):
        # Call object.__setattr__ with the supplied arguments.
        object.__setattr__(self, "provenance", MappingProxyType(dict(self.provenance)))


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define ObjectiveDiagnostics to group the state and operations declared below.
# Declared fields: vehicles_measured, completed_services, mean_travel_time_seconds, minimum_travel_time_seconds,
# maximum_travel_time_seconds, travel_time_variance_seconds_squared.
# Construction and attribute behavior follow the declared decorators and base classes.
class ObjectiveDiagnostics:
    # Declare vehicles_measured as int for this data structure.
    vehicles_measured: int
    # Declare completed_services as int for this data structure.
    completed_services: int
    # Declare mean_travel_time_seconds as float for this data structure.
    mean_travel_time_seconds: float
    # Declare minimum_travel_time_seconds as float for this data structure.
    minimum_travel_time_seconds: float
    # Declare maximum_travel_time_seconds as float for this data structure.
    maximum_travel_time_seconds: float
    # Declare travel_time_variance_seconds_squared as float for this data structure.
    travel_time_variance_seconds_squared: float

