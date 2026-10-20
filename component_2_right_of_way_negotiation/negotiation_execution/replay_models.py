"""Immutable records for deterministic physical branch replay."""

# Import dataclass from dataclasses for the operations below.
from dataclasses import dataclass
# Import sha256 from hashlib for the operations below.
from hashlib import sha256
# Import MappingProxyType from types for the operations below.
from types import MappingProxyType
# Import Mapping, Tuple from typing for the operations below.
from typing import Mapping, Tuple


# Set ACTION_SOURCE to the text 'DETERMINISTIC_PHYSICAL_COUPLING_VALIDATION'.
ACTION_SOURCE = "DETERMINISTIC_PHYSICAL_COUPLING_VALIDATION"


# Mapping using the inputs and processing steps below.
# Input value: the supplied value.
# Output: the result of MappingProxyType(a dictionary built from value).
# Return the result of MappingProxyType(a dictionary built from value) to the caller.
def _mapping(value): return MappingProxyType(dict(value))


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define PhysicalBranchReplaySpecification to group the state and operations declared below.
# Declared fields: replay_id, scenario_id, scenario_manifest_id, scenario_specification_id, branch_id,
# source_snapshot_id, source_decision_timestamp, movement_path_ids, scheduled_spawn_steps,
# scheduled_spawn_times,....
# Construction and attribute behavior follow the declared decorators and base classes.
class PhysicalBranchReplaySpecification:
    # Declare replay_id as tuple for this data structure.
    replay_id: tuple
    # Declare scenario_id as tuple for this data structure.
    scenario_id: tuple
    # Declare scenario_manifest_id as tuple for this data structure.
    scenario_manifest_id: tuple
    # Declare scenario_specification_id as tuple for this data structure.
    scenario_specification_id: tuple
    # Declare branch_id as tuple for this data structure.
    branch_id: tuple
    # Declare source_snapshot_id as tuple for this data structure.
    source_snapshot_id: tuple
    # Declare source_decision_timestamp as float for this data structure.
    source_decision_timestamp: float
    # Declare movement_path_ids as Tuple[str, ...] for this data structure.
    movement_path_ids: Tuple[str, ...]
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
    # Declare simulation_step_seconds as float for this data structure.
    simulation_step_seconds: float
    # Declare episode_end_time as float for this data structure.
    episode_end_time: float
    # Declare action_source as str for this data structure.
    action_source: str
    # Declare provenance as Mapping for this data structure.
    provenance: Mapping

    # Post init using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    # Processing: select branches using the stated conditions.
    def __post_init__(self):
        # Run this branch when self.action_source differs from ACTION_SOURCE.
        if self.action_source != ACTION_SOURCE:
            # Raise ValueError with the text 'PHYSICAL_REPLAY_ACTION_SOURCE_INVALID' to stop this execution path.
            raise ValueError("PHYSICAL_REPLAY_ACTION_SOURCE_INVALID")
        # Call object.__setattr__ with the supplied arguments.
        object.__setattr__(self, "provenance", _mapping(self.provenance))


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define PreBranchPhysicalStateFingerprint to group the state and operations declared below.
# Declared fields: scenario_id, simulation_timestamp, simulation_step_index, active_vehicle_ids, vehicle_states,
# original_precedence_graph, source_snapshot_id, policy_factor_ids, hard_action_masks, regulatory_profile,....
# Construction and attribute behavior follow the declared decorators and base classes.
class PreBranchPhysicalStateFingerprint:
    # Declare scenario_id as tuple for this data structure.
    scenario_id: tuple
    # Declare simulation_timestamp as float for this data structure.
    simulation_timestamp: float
    # Declare simulation_step_index as int for this data structure.
    simulation_step_index: int
    # Declare active_vehicle_ids as Tuple[str, ...] for this data structure.
    active_vehicle_ids: Tuple[str, ...]
    # Declare vehicle_states as Tuple[tuple, ...] for this data structure.
    vehicle_states: Tuple[tuple, ...]
    # Declare original_precedence_graph as Tuple[tuple, ...] for this data structure.
    original_precedence_graph: Tuple[tuple, ...]
    # Declare source_snapshot_id as tuple for this data structure.
    source_snapshot_id: tuple
    # Declare policy_factor_ids as Tuple[tuple, ...] for this data structure.
    policy_factor_ids: Tuple[tuple, ...]
    # Declare hard_action_masks as Tuple[tuple, ...] for this data structure.
    hard_action_masks: Tuple[tuple, ...]
    # Declare regulatory_profile as str for this data structure.
    regulatory_profile: str
    # Declare network_identity as str for this data structure.
    network_identity: str

    # Apply property as a decorator to configure the following definition.
    @property
    # Fingerprint id using the inputs and processing steps below.
    # Output: a tuple containing the text 'PRE_BRANCH_PHYSICAL_STATE_V1', the hexadecimal digest from
    # sha256(repr(self).encode('utf-8')).
    def fingerprint_id(self):
        # Return a tuple containing the text 'PRE_BRANCH_PHYSICAL_STATE_V1', the hexadecimal digest from
        # sha256(repr(self).encode('utf-8')) to the caller.
        return ("PRE_BRANCH_PHYSICAL_STATE_V1",
                # Include the hexadecimal digest from sha256(repr(self).encode('utf-8')) in this tuple.
                sha256(repr(self).encode("utf-8")).hexdigest())


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define PhysicalNegotiationBranchReplayTrace to group the state and operations declared below.
# Declared fields: replay_id, scenario_id, branch_id, source_snapshot_id, pre_branch_state_fingerprint,
# effective_precedence_graph, initial_execution_plan_id, initial_ready_vehicle_ids, initial_permissions,....
# Construction and attribute behavior follow the declared decorators and base classes.
class PhysicalNegotiationBranchReplayTrace:
    # Declare replay_id as tuple for this data structure.
    replay_id: tuple
    # Declare scenario_id as tuple for this data structure.
    scenario_id: tuple
    # Declare branch_id as tuple for this data structure.
    branch_id: tuple
    # Declare source_snapshot_id as tuple for this data structure.
    source_snapshot_id: tuple
    # Declare pre_branch_state_fingerprint as PreBranchPhysicalStateFingerprint for this data structure.
    pre_branch_state_fingerprint: PreBranchPhysicalStateFingerprint
    # Declare effective_precedence_graph as Tuple[tuple, ...] for this data structure.
    effective_precedence_graph: Tuple[tuple, ...]
    # Declare initial_execution_plan_id as tuple for this data structure.
    initial_execution_plan_id: tuple
    # Declare initial_ready_vehicle_ids as Tuple[str, ...] for this data structure.
    initial_ready_vehicle_ids: Tuple[str, ...]
    # Declare initial_permissions as Tuple[tuple, ...] for this data structure.
    initial_permissions: Tuple[tuple, ...]
    # Declare execution_plan_history as Tuple[tuple, ...] for this data structure.
    execution_plan_history: Tuple[tuple, ...]
    # Declare speed_constraint_records as tuple for this data structure.
    speed_constraint_records: tuple
    # Declare speed_command_records as Tuple[tuple, ...] for this data structure.
    speed_command_records: Tuple[tuple, ...]
    # Declare realized_deceleration_records as Tuple[tuple, ...] for this data structure.
    realized_deceleration_records: Tuple[tuple, ...]
    # Declare ready_vehicle_transitions as Tuple[tuple, ...] for this data structure.
    ready_vehicle_transitions: Tuple[tuple, ...]
    # Declare blocked_vehicle_transitions as Tuple[tuple, ...] for this data structure.
    blocked_vehicle_transitions: Tuple[tuple, ...]
    # Declare conflict_zone_entry_events as Tuple[tuple, ...] for this data structure.
    conflict_zone_entry_events: Tuple[tuple, ...]
    # Declare conflict_zone_clear_events as Tuple[tuple, ...] for this data structure.
    conflict_zone_clear_events: Tuple[tuple, ...]
    # Declare vehicle_completion_events as Tuple[tuple, ...] for this data structure.
    vehicle_completion_events: Tuple[tuple, ...]
    # Declare scheduled_spawn_records as Tuple[tuple, ...] for this data structure.
    scheduled_spawn_records: Tuple[tuple, ...]
    # Declare actual_departure_records as Tuple[tuple, ...] for this data structure.
    actual_departure_records: Tuple[tuple, ...]
    # Declare episode_end_time as float for this data structure.
    episode_end_time: float
    # Declare team_travel_time_seconds as float for this data structure.
    team_travel_time_seconds: float
    # Declare raw_shared_team_reward as float for this data structure.
    raw_shared_team_reward: float
    # Declare collision_count as int for this data structure.
    collision_count: int
    # Declare blocked_zone_entry_violation_count as int for this data structure.
    blocked_zone_entry_violation_count: int
    # Declare native_sumo_intervention_events as Tuple[tuple, ...] for this data structure.
    native_sumo_intervention_events: Tuple[tuple, ...]
    # Declare native_sumo_intervention_status as str for this data structure.
    native_sumo_intervention_status: str
    # Declare causal_status as str for this data structure.
    causal_status: str
    # Declare sumo_version as tuple for this data structure.
    sumo_version: tuple
    # Declare sumo_command_arguments as Tuple[str, ...] for this data structure.
    sumo_command_arguments: Tuple[str, ...]
    # Declare action_source as str for this data structure.
    action_source: str
    # Declare provenance as Mapping for this data structure.
    provenance: Mapping

    # Post init using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    def __post_init__(self):
        # Call object.__setattr__ with the supplied arguments.
        object.__setattr__(self, "provenance", _mapping(self.provenance))
