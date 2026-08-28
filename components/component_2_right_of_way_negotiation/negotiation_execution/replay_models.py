"""Immutable records for deterministic physical branch replay."""

from dataclasses import dataclass
from hashlib import sha256
from types import MappingProxyType
from typing import Mapping, Tuple


ACTION_SOURCE = "DETERMINISTIC_PHYSICAL_COUPLING_VALIDATION"


def _mapping(value): return MappingProxyType(dict(value))


@dataclass(frozen=True)
class PhysicalBranchReplaySpecification:
    replay_id: tuple
    scenario_id: tuple
    scenario_manifest_id: tuple
    scenario_specification_id: tuple
    branch_id: tuple
    source_snapshot_id: tuple
    source_decision_timestamp: float
    movement_path_ids: Tuple[str, ...]
    scheduled_spawn_steps: Tuple[int, ...]
    scheduled_spawn_times: Tuple[float, ...]
    network_identity: str
    vehicle_type_identity: str
    regulatory_profile: str
    perception_configuration_identity: str
    intention_model_identity: str
    simulation_step_seconds: float
    episode_end_time: float
    action_source: str
    provenance: Mapping

    def __post_init__(self):
        if self.action_source != ACTION_SOURCE:
            raise ValueError("PHYSICAL_REPLAY_ACTION_SOURCE_INVALID")
        object.__setattr__(self, "provenance", _mapping(self.provenance))


@dataclass(frozen=True)
class PreBranchPhysicalStateFingerprint:
    scenario_id: tuple
    simulation_timestamp: float
    simulation_step_index: int
    active_vehicle_ids: Tuple[str, ...]
    vehicle_states: Tuple[tuple, ...]
    original_precedence_graph: Tuple[tuple, ...]
    source_snapshot_id: tuple
    policy_factor_ids: Tuple[tuple, ...]
    hard_action_masks: Tuple[tuple, ...]
    regulatory_profile: str
    network_identity: str

    @property
    def fingerprint_id(self):
        return ("PRE_BRANCH_PHYSICAL_STATE_V1",
                sha256(repr(self).encode("utf-8")).hexdigest())


@dataclass(frozen=True)
class PhysicalNegotiationBranchReplayTrace:
    replay_id: tuple
    scenario_id: tuple
    branch_id: tuple
    source_snapshot_id: tuple
    pre_branch_state_fingerprint: PreBranchPhysicalStateFingerprint
    effective_precedence_graph: Tuple[tuple, ...]
    initial_execution_plan_id: tuple
    initial_ready_vehicle_ids: Tuple[str, ...]
    initial_permissions: Tuple[tuple, ...]
    execution_plan_history: Tuple[tuple, ...]
    speed_constraint_records: tuple
    speed_command_records: Tuple[tuple, ...]
    realized_deceleration_records: Tuple[tuple, ...]
    ready_vehicle_transitions: Tuple[tuple, ...]
    blocked_vehicle_transitions: Tuple[tuple, ...]
    conflict_zone_entry_events: Tuple[tuple, ...]
    conflict_zone_clear_events: Tuple[tuple, ...]
    vehicle_completion_events: Tuple[tuple, ...]
    scheduled_spawn_records: Tuple[tuple, ...]
    actual_departure_records: Tuple[tuple, ...]
    episode_end_time: float
    team_travel_time_seconds: float
    raw_shared_team_reward: float
    collision_count: int
    blocked_zone_entry_violation_count: int
    native_sumo_intervention_events: Tuple[tuple, ...]
    native_sumo_intervention_status: str
    causal_status: str
    sumo_version: tuple
    sumo_command_arguments: Tuple[str, ...]
    action_source: str
    provenance: Mapping

    def __post_init__(self):
        object.__setattr__(self, "provenance", _mapping(self.provenance))
