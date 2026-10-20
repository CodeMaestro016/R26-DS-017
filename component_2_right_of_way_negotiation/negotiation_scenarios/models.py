"""Immutable Step 5J.2A scenario-coverage research records."""

# Import dataclass, field from dataclasses for the operations below.
from dataclasses import dataclass, field
# Import MappingProxyType from types for the operations below.
from types import MappingProxyType
# Import Mapping, Optional, Tuple from typing for the operations below.
from typing import Mapping, Optional, Tuple


# Set REAL_SUMO_SCENARIO_SNAPSHOT to the text 'REAL_SUMO_SCENARIO_SNAPSHOT'.
REAL_SUMO_SCENARIO_SNAPSHOT = "REAL_SUMO_SCENARIO_SNAPSHOT"
# Set DETERMINISTIC_COVERAGE_ENUMERATION to the text 'DETERMINISTIC_COVERAGE_ENUMERATION'.
DETERMINISTIC_COVERAGE_ENUMERATION = "DETERMINISTIC_COVERAGE_ENUMERATION"


# Mapping using the inputs and processing steps below.
# Input value: the supplied value.
# Output: the result of MappingProxyType(a dictionary built from value).
def _mapping(value):
    # Return the result of MappingProxyType(a dictionary built from value) to the caller.
    return MappingProxyType(dict(value))


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define ScenarioDiscoveryRecord to group the state and operations declared below.
# Declared fields: candidate_id, movement_path_ids, physical_conflict_relationships, regulatory_edges,
# strongly_connected_components, negotiation_status, discovery_result, rejection_reason, provenance.
# Construction and attribute behavior follow the declared decorators and base classes.
class ScenarioDiscoveryRecord:
    # Declare candidate_id as tuple for this data structure.
    candidate_id: tuple
    # Declare movement_path_ids as Tuple[str, ...] for this data structure.
    movement_path_ids: Tuple[str, ...]
    # Declare physical_conflict_relationships as Tuple[tuple, ...] for this data structure.
    physical_conflict_relationships: Tuple[tuple, ...]
    # Declare regulatory_edges as Tuple[tuple, ...] for this data structure.
    regulatory_edges: Tuple[tuple, ...]
    # Declare strongly_connected_components as Tuple[Tuple[str, ...], ...] for this data structure.
    strongly_connected_components: Tuple[Tuple[str, ...], ...]
    # Declare negotiation_status as str for this data structure.
    negotiation_status: str
    # Declare discovery_result as str for this data structure.
    discovery_result: str
    # Declare rejection_reason as Optional[str] for this data structure.
    rejection_reason: Optional[str]
    # Declare provenance as Mapping[str, str] for this data structure.
    provenance: Mapping[str, str]

    # Post init using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    def __post_init__(self):
        # Call object.__setattr__ with the supplied arguments.
        object.__setattr__(self, "provenance", _mapping(self.provenance))


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define MovementTimingCalibrationRecord to group the state and operations declared below.
# Declared fields: movement_path_id, route_environment_identity, simulation_step_seconds,
# scheduled_departure_step, actual_departure_step, synchronization_event_step, departure_to_event_steps,
# departure_to_event_seconds,....
# Construction and attribute behavior follow the declared decorators and base classes.
class MovementTimingCalibrationRecord:
    # Declare movement_path_id as str for this data structure.
    movement_path_id: str
    # Declare route_environment_identity as str for this data structure.
    route_environment_identity: str
    # Declare simulation_step_seconds as float for this data structure.
    simulation_step_seconds: float
    # Declare scheduled_departure_step as int for this data structure.
    scheduled_departure_step: int
    # Declare actual_departure_step as int for this data structure.
    actual_departure_step: int
    # Declare synchronization_event_step as int for this data structure.
    synchronization_event_step: int
    # Declare departure_to_event_steps as int for this data structure.
    departure_to_event_steps: int
    # Declare departure_to_event_seconds as float for this data structure.
    departure_to_event_seconds: float
    # Declare vehicle_configuration_identity as str for this data structure.
    vehicle_configuration_identity: str
    # Declare network_identity as str for this data structure.
    network_identity: str
    # Declare provenance as Mapping[str, str] for this data structure.
    provenance: Mapping[str, str]

    # Post init using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    def __post_init__(self):
        # Call object.__setattr__ with the supplied arguments.
        object.__setattr__(self, "provenance", _mapping(self.provenance))
        # Iterate over a tuple containing the text 'scheduled_departure_step', the text 'actual_departure_step',
        # the text..., binding each item to name.
        for name in ("scheduled_departure_step", "actual_departure_step",
                     "synchronization_event_step", "departure_to_event_steps"):
            # Run this branch when the result of type(the requested attribute of self) is a different object from
            # int.
            if type(getattr(self, name)) is not int:
                # Raise TypeError with formatted text built from the embedded values to stop this execution path.
                raise TypeError(f"{name} must be an integer simulator step")


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define NegotiationScenarioSpecification to group the state and operations declared below.
# Declared fields: scenario_id, scenario_family, movement_path_ids, approach_ids, vehicle_roles,
# expected_regulatory_topology, expected_negotiation_status, synchronization_method, scheduled_spawn_steps,
# scheduled_spawn_times,....
# Construction and attribute behavior follow the declared decorators and base classes.
class NegotiationScenarioSpecification:
    # Declare scenario_id as tuple for this data structure.
    scenario_id: tuple
    # Declare scenario_family as str for this data structure.
    scenario_family: str
    # Declare movement_path_ids as Tuple[str, ...] for this data structure.
    movement_path_ids: Tuple[str, ...]
    # Declare approach_ids as Tuple[str, ...] for this data structure.
    approach_ids: Tuple[str, ...]
    # Declare vehicle_roles as Tuple[str, ...] for this data structure.
    vehicle_roles: Tuple[str, ...]
    # Declare expected_regulatory_topology as Tuple[Tuple[str, ...], ...] for this data structure.
    expected_regulatory_topology: Tuple[Tuple[str, ...], ...]
    # Declare expected_negotiation_status as str for this data structure.
    expected_negotiation_status: str
    # Declare synchronization_method as str for this data structure.
    synchronization_method: str
    # Declare scheduled_spawn_steps as Tuple[int, ...] for this data structure.
    scheduled_spawn_steps: Tuple[int, ...]
    # Declare scheduled_spawn_times as Tuple[float, ...] for this data structure.
    scheduled_spawn_times: Tuple[float, ...]
    # Declare network_identity as str for this data structure.
    network_identity: str
    # Declare vehicle_type_identity as str for this data structure.
    vehicle_type_identity: str
    # Declare regulatory_profile as str for this data structure.
    regulatory_profile: str
    # Declare perception_configuration_identity as str for this data structure.
    perception_configuration_identity: str
    # Declare intention_model_identity as str for this data structure.
    intention_model_identity: str
    # Declare generation_basis as str for this data structure.
    generation_basis: str
    # Declare provenance as Mapping[str, str] for this data structure.
    provenance: Mapping[str, str]

    # Post init using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    def __post_init__(self):
        # Call object.__setattr__ with the supplied arguments.
        object.__setattr__(self, "provenance", _mapping(self.provenance))

    # Apply property as a decorator to configure the following definition.
    @property
    # Semantic fingerprint using the inputs and processing steps below.
    # Output: a tuple containing self.network_identity, self.scenario_family, a tuple built from the sorted values
    # from...
    def semantic_fingerprint(self):
        # Return a tuple containing self.network_identity, self.scenario_family, a tuple built from the sorted
        # values from... to the caller.
        return (self.network_identity, self.scenario_family,
                # Include a tuple built from the sorted values from self.movement_path_ids in this tuple.
                tuple(sorted(self.movement_path_ids)), self.synchronization_method,
                # Include self.vehicle_type_identity in this tuple.
                self.vehicle_type_identity, self.regulatory_profile)


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define LiveNegotiationCoverageRecord to group the state and operations declared below.
# Declared fields: scenario_id, snapshot_id, timestamp, negotiation_status, participant_ids,
# proposer_decision_event_ids, proposer_action_masks, responder_decision_event_ids, responder_action_masks,
# proposal_ids,....
# Construction and attribute behavior follow the declared decorators and base classes.
class LiveNegotiationCoverageRecord:
    # Declare scenario_id as tuple for this data structure.
    scenario_id: tuple
    # Declare snapshot_id as tuple for this data structure.
    snapshot_id: tuple
    # Declare timestamp as float for this data structure.
    timestamp: float
    # Declare negotiation_status as str for this data structure.
    negotiation_status: str
    # Declare participant_ids as Tuple[str, ...] for this data structure.
    participant_ids: Tuple[str, ...]
    # Declare proposer_decision_event_ids as Tuple[tuple, ...] for this data structure.
    proposer_decision_event_ids: Tuple[tuple, ...]
    # Declare proposer_action_masks as Tuple[Tuple[bool, ...], ...] for this data structure.
    proposer_action_masks: Tuple[Tuple[bool, ...], ...]
    # Declare responder_decision_event_ids as Tuple[tuple, ...] for this data structure.
    responder_decision_event_ids: Tuple[tuple, ...]
    # Declare responder_action_masks as Tuple[Tuple[bool, ...], ...] for this data structure.
    responder_action_masks: Tuple[Tuple[bool, ...], ...]
    # Declare proposal_ids as Tuple[tuple, ...] for this data structure.
    proposal_ids: Tuple[tuple, ...]
    # Declare protocol_outcomes as Tuple[str, ...] for this data structure.
    protocol_outcomes: Tuple[str, ...]
    # Set source to REAL_SUMO_SCENARIO_SNAPSHOT; declare its type as str.
    source: str = REAL_SUMO_SCENARIO_SNAPSHOT
    # Set provenance to the result of field(); declare its type as Mapping[str, str].
    provenance: Mapping[str, str] = field(default_factory=dict)

    # Post init using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    # Processing: select branches using the stated conditions.
    def __post_init__(self):
        # Call object.__setattr__ with the supplied arguments.
        object.__setattr__(self, "provenance", _mapping(self.provenance))
        # Run this branch when self.source differs from REAL_SUMO_SCENARIO_SNAPSHOT.
        if self.source != REAL_SUMO_SCENARIO_SNAPSHOT:
            # Raise ValueError with the text 'LIVE_COVERAGE_REQUIRES_REAL_SUMO_SOURCE' to stop this execution
            # path.
            raise ValueError("LIVE_COVERAGE_REQUIRES_REAL_SUMO_SOURCE")


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define NegotiationScenarioProtocolTrace to group the state and operations declared below.
# Declared fields: trace_id, scenario_id, source_snapshot_id, proposer_decision_event_id, proposer_action,
# proposal_id, responder_decision_event_id, responder_action, protocol_status, original_precedence_graph,....
# Construction and attribute behavior follow the declared decorators and base classes.
class NegotiationScenarioProtocolTrace:
    # Declare trace_id as tuple for this data structure.
    trace_id: tuple
    # Declare scenario_id as tuple for this data structure.
    scenario_id: tuple
    # Declare source_snapshot_id as tuple for this data structure.
    source_snapshot_id: tuple
    # Declare proposer_decision_event_id as tuple for this data structure.
    proposer_decision_event_id: tuple
    # Declare proposer_action as str for this data structure.
    proposer_action: str
    # Declare proposal_id as Optional[tuple] for this data structure.
    proposal_id: Optional[tuple]
    # Declare responder_decision_event_id as Optional[tuple] for this data structure.
    responder_decision_event_id: Optional[tuple]
    # Declare responder_action as Optional[str] for this data structure.
    responder_action: Optional[str]
    # Declare protocol_status as str for this data structure.
    protocol_status: str
    # Declare original_precedence_graph as Tuple[tuple, ...] for this data structure.
    original_precedence_graph: Tuple[tuple, ...]
    # Declare effective_precedence_graph as Tuple[tuple, ...] for this data structure.
    effective_precedence_graph: Tuple[tuple, ...]
    # Declare timestamps as Tuple[float, ...] for this data structure.
    timestamps: Tuple[float, ...]
    # Declare action_source as str for this data structure.
    action_source: str
    # Declare provenance as Mapping[str, str] for this data structure.
    provenance: Mapping[str, str]

    # Post init using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    # Processing: select branches using the stated conditions.
    def __post_init__(self):
        # Call object.__setattr__ with the supplied arguments.
        object.__setattr__(self, "provenance", _mapping(self.provenance))
        # Run this branch when self.action_source differs from DETERMINISTIC_COVERAGE_ENUMERATION.
        if self.action_source != DETERMINISTIC_COVERAGE_ENUMERATION:
            # Raise ValueError with the text 'COVERAGE_TRACE_ACTION_SOURCE_INVALID' to stop this execution path.
            raise ValueError("COVERAGE_TRACE_ACTION_SOURCE_INVALID")


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define ScenarioCataloguePartitionReadiness to group the state and operations declared below.
# Declared fields: distinct_scenario_ids, required_scenario_roles, identity_overlap_possible,
# proposer_capable_scenarios, responder_capable_scenarios, multi_action_proposer_scenarios,
# multi_action_responder_scenarios,....
# Construction and attribute behavior follow the declared decorators and base classes.
class ScenarioCataloguePartitionReadiness:
    # Declare distinct_scenario_ids as Tuple[tuple, ...] for this data structure.
    distinct_scenario_ids: Tuple[tuple, ...]
    # Declare required_scenario_roles as Tuple[str, ...] for this data structure.
    required_scenario_roles: Tuple[str, ...]
    # Declare identity_overlap_possible as bool for this data structure.
    identity_overlap_possible: bool
    # Declare proposer_capable_scenarios as Tuple[tuple, ...] for this data structure.
    proposer_capable_scenarios: Tuple[tuple, ...]
    # Declare responder_capable_scenarios as Tuple[tuple, ...] for this data structure.
    responder_capable_scenarios: Tuple[tuple, ...]
    # Declare multi_action_proposer_scenarios as Tuple[tuple, ...] for this data structure.
    multi_action_proposer_scenarios: Tuple[tuple, ...]
    # Declare multi_action_responder_scenarios as Tuple[tuple, ...] for this data structure.
    multi_action_responder_scenarios: Tuple[tuple, ...]
    # Declare partition_ready as bool for this data structure.
    partition_ready: bool
    # Declare blockers as Tuple[str, ...] for this data structure.
    blockers: Tuple[str, ...]
