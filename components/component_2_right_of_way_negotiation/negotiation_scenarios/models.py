"""Immutable Step 5J.2A scenario-coverage research records."""

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping, Optional, Tuple


REAL_SUMO_SCENARIO_SNAPSHOT = "REAL_SUMO_SCENARIO_SNAPSHOT"
DETERMINISTIC_COVERAGE_ENUMERATION = "DETERMINISTIC_COVERAGE_ENUMERATION"


def _mapping(value):
    return MappingProxyType(dict(value))


@dataclass(frozen=True)
class ScenarioDiscoveryRecord:
    candidate_id: tuple
    movement_path_ids: Tuple[str, ...]
    physical_conflict_relationships: Tuple[tuple, ...]
    regulatory_edges: Tuple[tuple, ...]
    strongly_connected_components: Tuple[Tuple[str, ...], ...]
    negotiation_status: str
    discovery_result: str
    rejection_reason: Optional[str]
    provenance: Mapping[str, str]

    def __post_init__(self):
        object.__setattr__(self, "provenance", _mapping(self.provenance))


@dataclass(frozen=True)
class MovementTimingCalibrationRecord:
    movement_path_id: str
    route_environment_identity: str
    simulation_step_seconds: float
    scheduled_departure_step: int
    actual_departure_step: int
    synchronization_event_step: int
    departure_to_event_steps: int
    departure_to_event_seconds: float
    vehicle_configuration_identity: str
    network_identity: str
    provenance: Mapping[str, str]

    def __post_init__(self):
        object.__setattr__(self, "provenance", _mapping(self.provenance))
        for name in ("scheduled_departure_step", "actual_departure_step",
                     "synchronization_event_step", "departure_to_event_steps"):
            if type(getattr(self, name)) is not int:
                raise TypeError(f"{name} must be an integer simulator step")


@dataclass(frozen=True)
class NegotiationScenarioSpecification:
    scenario_id: tuple
    scenario_family: str
    movement_path_ids: Tuple[str, ...]
    approach_ids: Tuple[str, ...]
    vehicle_roles: Tuple[str, ...]
    expected_regulatory_topology: Tuple[Tuple[str, ...], ...]
    expected_negotiation_status: str
    synchronization_method: str
    scheduled_spawn_steps: Tuple[int, ...]
    scheduled_spawn_times: Tuple[float, ...]
    network_identity: str
    vehicle_type_identity: str
    regulatory_profile: str
    perception_configuration_identity: str
    intention_model_identity: str
    generation_basis: str
    provenance: Mapping[str, str]

    def __post_init__(self):
        object.__setattr__(self, "provenance", _mapping(self.provenance))

    @property
    def semantic_fingerprint(self):
        return (self.network_identity, self.scenario_family,
                tuple(sorted(self.movement_path_ids)), self.synchronization_method,
                self.vehicle_type_identity, self.regulatory_profile)


@dataclass(frozen=True)
class LiveNegotiationCoverageRecord:
    scenario_id: tuple
    snapshot_id: tuple
    timestamp: float
    negotiation_status: str
    participant_ids: Tuple[str, ...]
    proposer_decision_event_ids: Tuple[tuple, ...]
    proposer_action_masks: Tuple[Tuple[bool, ...], ...]
    responder_decision_event_ids: Tuple[tuple, ...]
    responder_action_masks: Tuple[Tuple[bool, ...], ...]
    proposal_ids: Tuple[tuple, ...]
    protocol_outcomes: Tuple[str, ...]
    source: str = REAL_SUMO_SCENARIO_SNAPSHOT
    provenance: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self):
        object.__setattr__(self, "provenance", _mapping(self.provenance))
        if self.source != REAL_SUMO_SCENARIO_SNAPSHOT:
            raise ValueError("LIVE_COVERAGE_REQUIRES_REAL_SUMO_SOURCE")


@dataclass(frozen=True)
class NegotiationScenarioProtocolTrace:
    trace_id: tuple
    scenario_id: tuple
    source_snapshot_id: tuple
    proposer_decision_event_id: tuple
    proposer_action: str
    proposal_id: Optional[tuple]
    responder_decision_event_id: Optional[tuple]
    responder_action: Optional[str]
    protocol_status: str
    original_precedence_graph: Tuple[tuple, ...]
    effective_precedence_graph: Tuple[tuple, ...]
    timestamps: Tuple[float, ...]
    action_source: str
    provenance: Mapping[str, str]

    def __post_init__(self):
        object.__setattr__(self, "provenance", _mapping(self.provenance))
        if self.action_source != DETERMINISTIC_COVERAGE_ENUMERATION:
            raise ValueError("COVERAGE_TRACE_ACTION_SOURCE_INVALID")


@dataclass(frozen=True)
class ScenarioCataloguePartitionReadiness:
    distinct_scenario_ids: Tuple[tuple, ...]
    required_scenario_roles: Tuple[str, ...]
    identity_overlap_possible: bool
    proposer_capable_scenarios: Tuple[tuple, ...]
    responder_capable_scenarios: Tuple[tuple, ...]
    multi_action_proposer_scenarios: Tuple[tuple, ...]
    multi_action_responder_scenarios: Tuple[tuple, ...]
    partition_ready: bool
    blockers: Tuple[str, ...]
