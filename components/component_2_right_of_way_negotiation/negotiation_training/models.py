"""Immutable post-freeze coupled-environment research records."""

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping, Optional, Tuple


def _freeze(value): return MappingProxyType(dict(value))


@dataclass(frozen=True)
class CoupledEnvironmentReadinessEvidence:
    evidence_id: tuple
    frozen_design_id: tuple
    training_manifest_id: tuple
    coupling_status: str
    physical_causal_witness: bool
    completed_branch_count: int
    hard_validity_gates_passed: bool
    readiness_status: str
    provenance: Mapping

    def __post_init__(self): object.__setattr__(self, "provenance", _freeze(self.provenance))


@dataclass(frozen=True)
class CoupledPolicyFactorRecord:
    decision_event_id: tuple
    joint_batch_id: tuple
    ego_id: str
    role: str
    claim_identity: tuple
    proposal_id: Optional[tuple]
    action_names: Tuple[str, ...]
    hard_action_mask: Tuple[bool, ...]
    selected_action: str
    behavior_policy_source: str
    ppo_update_eligible: bool
    actor_observation_shape: tuple
    claim_representation_shape: tuple
    protocol_representation_shape: Optional[tuple]
    return_record_id: Optional[tuple]
    advantage_record_id: Optional[tuple]
    provenance: Mapping

    def __post_init__(self): object.__setattr__(self, "provenance", _freeze(self.provenance))


@dataclass(frozen=True)
class CoupledNegotiationDecisionBatch:
    joint_batch_id: tuple
    episode_id: tuple
    scenario_id: tuple
    decision_timestamp: float
    source_joint_snapshot_id: tuple
    proposer_context_ids: Tuple[tuple, ...]
    proposer_decision_ids: Tuple[tuple, ...]
    proposal_ids: Tuple[tuple, ...]
    responder_context_ids: Tuple[tuple, ...]
    responder_decision_ids: Tuple[tuple, ...]
    protocol_snapshot_id: tuple
    effective_graph_id: tuple
    execution_plan_id: tuple
    physical_interval_start: float
    physical_interval_end: float
    next_decision_batch_id: Optional[tuple]
    continuation_status: str
    interval_team_reward: float
    policy_factors: Tuple[CoupledPolicyFactorRecord, ...]
    encoded_graph_shapes: Tuple[tuple, ...]
    critic_centralized_input_shape: tuple
    provenance: Mapping

    def __post_init__(self): object.__setattr__(self, "provenance", _freeze(self.provenance))


@dataclass(frozen=True)
class CoupledNegotiationEpisodeRecord:
    episode_id: tuple
    scenario_id: tuple
    scenario_manifest_id: tuple
    joint_decision_batches: Tuple[CoupledNegotiationDecisionBatch, ...]
    policy_factor_count: int
    proposer_factor_count: int
    responder_factor_count: int
    multi_factor_batch_count: int
    sumo_step_count: int
    simulation_duration_seconds: float
    wall_clock_runtime_seconds: float
    scheduled_vehicle_count: int
    completed_vehicle_count: int
    physical_speed_command_count: int
    conflict_zone_execution_plan_count: int
    native_sumo_safety_intervention_count: int
    team_travel_time_seconds: float
    raw_shared_team_reward: float
    interval_reward_sum: float
    collision_count: int
    blocked_zone_entry_violation_count: int
    episode_completion_status: str
    hard_validity_gate_results: Mapping
    provenance: Mapping

    def __post_init__(self):
        object.__setattr__(self, "hard_validity_gate_results", _freeze(self.hard_validity_gate_results))
        object.__setattr__(self, "provenance", _freeze(self.provenance))
