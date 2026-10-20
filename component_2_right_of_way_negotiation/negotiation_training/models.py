"""Immutable post-freeze coupled-environment research records."""

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
# Define CoupledEnvironmentReadinessEvidence to group the state and operations declared below.
# Declared fields: evidence_id, frozen_design_id, training_manifest_id, coupling_status, physical_causal_witness,
# completed_branch_count, hard_validity_gates_passed, readiness_status, provenance.
# Construction and attribute behavior follow the declared decorators and base classes.
class CoupledEnvironmentReadinessEvidence:
    # Declare evidence_id as tuple for this data structure.
    evidence_id: tuple
    # Declare frozen_design_id as tuple for this data structure.
    frozen_design_id: tuple
    # Declare training_manifest_id as tuple for this data structure.
    training_manifest_id: tuple
    # Declare coupling_status as str for this data structure.
    coupling_status: str
    # Declare physical_causal_witness as bool for this data structure.
    physical_causal_witness: bool
    # Declare completed_branch_count as int for this data structure.
    completed_branch_count: int
    # Declare hard_validity_gates_passed as bool for this data structure.
    hard_validity_gates_passed: bool
    # Declare readiness_status as str for this data structure.
    readiness_status: str
    # Declare provenance as Mapping for this data structure.
    provenance: Mapping

    # Post init using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    # Call object.__setattr__ with the supplied arguments.
    def __post_init__(self): object.__setattr__(self, "provenance", _freeze(self.provenance))


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define CoupledPolicyFactorRecord to group the state and operations declared below.
# Declared fields: decision_event_id, joint_batch_id, ego_id, role, claim_identity, proposal_id, action_names,
# hard_action_mask, selected_action, behavior_policy_source, ppo_update_eligible, actor_observation_shape,....
# Construction and attribute behavior follow the declared decorators and base classes.
class CoupledPolicyFactorRecord:
    # Declare decision_event_id as tuple for this data structure.
    decision_event_id: tuple
    # Declare joint_batch_id as tuple for this data structure.
    joint_batch_id: tuple
    # Declare ego_id as str for this data structure.
    ego_id: str
    # Declare role as str for this data structure.
    role: str
    # Declare claim_identity as tuple for this data structure.
    claim_identity: tuple
    # Declare proposal_id as Optional[tuple] for this data structure.
    proposal_id: Optional[tuple]
    # Declare action_names as Tuple[str, ...] for this data structure.
    action_names: Tuple[str, ...]
    # Declare hard_action_mask as Tuple[bool, ...] for this data structure.
    hard_action_mask: Tuple[bool, ...]
    # Declare selected_action as str for this data structure.
    selected_action: str
    # Declare behavior_policy_source as str for this data structure.
    behavior_policy_source: str
    # Declare ppo_update_eligible as bool for this data structure.
    ppo_update_eligible: bool
    # Declare actor_observation_shape as tuple for this data structure.
    actor_observation_shape: tuple
    # Declare claim_representation_shape as tuple for this data structure.
    claim_representation_shape: tuple
    # Declare protocol_representation_shape as Optional[tuple] for this data structure.
    protocol_representation_shape: Optional[tuple]
    # Declare return_record_id as Optional[tuple] for this data structure.
    return_record_id: Optional[tuple]
    # Declare advantage_record_id as Optional[tuple] for this data structure.
    advantage_record_id: Optional[tuple]
    # Declare provenance as Mapping for this data structure.
    provenance: Mapping

    # Post init using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    # Call object.__setattr__ with the supplied arguments.
    def __post_init__(self): object.__setattr__(self, "provenance", _freeze(self.provenance))


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define CoupledNegotiationDecisionBatch to group the state and operations declared below.
# Declared fields: joint_batch_id, episode_id, scenario_id, decision_timestamp, source_joint_snapshot_id,
# proposer_context_ids, proposer_decision_ids, proposal_ids, responder_context_ids, responder_decision_ids,....
# Construction and attribute behavior follow the declared decorators and base classes.
class CoupledNegotiationDecisionBatch:
    # Declare joint_batch_id as tuple for this data structure.
    joint_batch_id: tuple
    # Declare episode_id as tuple for this data structure.
    episode_id: tuple
    # Declare scenario_id as tuple for this data structure.
    scenario_id: tuple
    # Declare decision_timestamp as float for this data structure.
    decision_timestamp: float
    # Declare source_joint_snapshot_id as tuple for this data structure.
    source_joint_snapshot_id: tuple
    # Declare proposer_context_ids as Tuple[tuple, ...] for this data structure.
    proposer_context_ids: Tuple[tuple, ...]
    # Declare proposer_decision_ids as Tuple[tuple, ...] for this data structure.
    proposer_decision_ids: Tuple[tuple, ...]
    # Declare proposal_ids as Tuple[tuple, ...] for this data structure.
    proposal_ids: Tuple[tuple, ...]
    # Declare responder_context_ids as Tuple[tuple, ...] for this data structure.
    responder_context_ids: Tuple[tuple, ...]
    # Declare responder_decision_ids as Tuple[tuple, ...] for this data structure.
    responder_decision_ids: Tuple[tuple, ...]
    # Declare protocol_snapshot_id as tuple for this data structure.
    protocol_snapshot_id: tuple
    # Declare effective_graph_id as tuple for this data structure.
    effective_graph_id: tuple
    # Declare execution_plan_id as tuple for this data structure.
    execution_plan_id: tuple
    # Declare physical_interval_start as float for this data structure.
    physical_interval_start: float
    # Declare physical_interval_end as float for this data structure.
    physical_interval_end: float
    # Declare next_decision_batch_id as Optional[tuple] for this data structure.
    next_decision_batch_id: Optional[tuple]
    # Declare continuation_status as str for this data structure.
    continuation_status: str
    # Declare interval_team_reward as float for this data structure.
    interval_team_reward: float
    # Declare policy_factors as Tuple[CoupledPolicyFactorRecord, ...] for this data structure.
    policy_factors: Tuple[CoupledPolicyFactorRecord, ...]
    # Declare encoded_graph_shapes as Tuple[tuple, ...] for this data structure.
    encoded_graph_shapes: Tuple[tuple, ...]
    # Declare critic_centralized_input_shape as tuple for this data structure.
    critic_centralized_input_shape: tuple
    # Declare provenance as Mapping for this data structure.
    provenance: Mapping

    # Post init using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    # Call object.__setattr__ with the supplied arguments.
    def __post_init__(self): object.__setattr__(self, "provenance", _freeze(self.provenance))


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define CoupledNegotiationEpisodeRecord to group the state and operations declared below.
# Declared fields: episode_id, scenario_id, scenario_manifest_id, joint_decision_batches, policy_factor_count,
# proposer_factor_count, responder_factor_count, multi_factor_batch_count, sumo_step_count,....
# Construction and attribute behavior follow the declared decorators and base classes.
class CoupledNegotiationEpisodeRecord:
    # Declare episode_id as tuple for this data structure.
    episode_id: tuple
    # Declare scenario_id as tuple for this data structure.
    scenario_id: tuple
    # Declare scenario_manifest_id as tuple for this data structure.
    scenario_manifest_id: tuple
    # Declare joint_decision_batches as Tuple[CoupledNegotiationDecisionBatch, ...] for this data structure.
    joint_decision_batches: Tuple[CoupledNegotiationDecisionBatch, ...]
    # Declare policy_factor_count as int for this data structure.
    policy_factor_count: int
    # Declare proposer_factor_count as int for this data structure.
    proposer_factor_count: int
    # Declare responder_factor_count as int for this data structure.
    responder_factor_count: int
    # Declare multi_factor_batch_count as int for this data structure.
    multi_factor_batch_count: int
    # Declare sumo_step_count as int for this data structure.
    sumo_step_count: int
    # Declare simulation_duration_seconds as float for this data structure.
    simulation_duration_seconds: float
    # Declare wall_clock_runtime_seconds as float for this data structure.
    wall_clock_runtime_seconds: float
    # Declare scheduled_vehicle_count as int for this data structure.
    scheduled_vehicle_count: int
    # Declare completed_vehicle_count as int for this data structure.
    completed_vehicle_count: int
    # Declare physical_speed_command_count as int for this data structure.
    physical_speed_command_count: int
    # Declare conflict_zone_execution_plan_count as int for this data structure.
    conflict_zone_execution_plan_count: int
    # Declare native_sumo_safety_intervention_count as int for this data structure.
    native_sumo_safety_intervention_count: int
    # Declare team_travel_time_seconds as float for this data structure.
    team_travel_time_seconds: float
    # Declare raw_shared_team_reward as float for this data structure.
    raw_shared_team_reward: float
    # Declare interval_reward_sum as float for this data structure.
    interval_reward_sum: float
    # Declare collision_count as int for this data structure.
    collision_count: int
    # Declare blocked_zone_entry_violation_count as int for this data structure.
    blocked_zone_entry_violation_count: int
    # Declare episode_completion_status as str for this data structure.
    episode_completion_status: str
    # Declare hard_validity_gate_results as Mapping for this data structure.
    hard_validity_gate_results: Mapping
    # Declare provenance as Mapping for this data structure.
    provenance: Mapping

    # Post init using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    def __post_init__(self):
        # Call object.__setattr__ with the supplied arguments.
        object.__setattr__(self, "hard_validity_gate_results", _freeze(self.hard_validity_gate_results))
        # Call object.__setattr__ with the supplied arguments.
        object.__setattr__(self, "provenance", _freeze(self.provenance))
