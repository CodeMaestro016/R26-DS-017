"""Immutable complete-episode MAPPO mathematics records for Step 5I."""

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping, Optional, Tuple


RETURN_SEMANTICS_STATUS = "EXACT_UNDISCOUNTED_EPISODIC_TEAM_RETURN"
DISCOUNT_FACTOR_STATUS = "NOT_REQUIRED_FOR_EXACT_STEP_5H_BASELINE_OBJECTIVE"
BOOTSTRAP_SEMANTICS_STATUS = "NO_BOOTSTRAP_FOR_COMPLETE_EPISODIC_BASELINE"
TRUNCATED_ROLLOUT_STATUS = "REQUIRES_BOOTSTRAP_RESEARCH_DECISION"
ADVANTAGE_DEFINITION_STATUS = "MONTE_CARLO_RETURN_MINUS_CENTRALIZED_VALUE"
GAE_STATUS = "NOT_USED_BASELINE_PARAMETER_REQUIRES_EXPERIMENTAL_SELECTION"
GAE_LAMBDA_STATUS = "NOT_SELECTED"
ADVANTAGE_NORMALIZATION_STATUS = "NOT_IMPLEMENTED_REQUIRES_EXPERIMENTAL_EVALUATION"
PPO_RATIO_STATUS = "MATHEMATICAL_INTERFACE_IMPLEMENTED"
PPO_CLIP_PARAMETER_STATUS = "REQUIRES_EXPERIMENTAL_SELECTION"
PPO_MULTI_FACTOR_AGGREGATION_STATUS = "REQUIRES_METHOD_SELECTION_BEFORE_OPTIMIZATION"
PPO_OPTIMIZATION_STATUS = "MATHEMATICAL_INTERFACE_ONLY_NO_PARAMETER_UPDATE"
RETURN_DEFINITION_ID = "EXACT_UNDISCOUNTED_TEAM_RETURN_V1"
RETURN_UNITS = "NEGATIVE_VEHICLE_SECONDS"


@dataclass(frozen=True)
class JointBatchReturnRecord:
    return_record_id: tuple
    batch_id: tuple
    terminal_batch_id: tuple
    objective_record_ids: Tuple[tuple, ...]
    undiscounted_team_return: float
    return_definition_id: str
    reward_definition_id: str
    metric_units: str
    episode_identity: str
    provenance: Mapping[str, str]

    def __post_init__(self):
        object.__setattr__(self, "provenance", MappingProxyType(dict(self.provenance)))


@dataclass(frozen=True)
class CentralizedBatchValueTarget:
    critic_target_id: tuple
    batch_id: tuple
    return_record_id: tuple
    target_return: float
    critic_value_at_collection: float
    critic_target: float
    value_error: float
    value_squared_error: float
    units: str
    provenance: Mapping[str, str]

    def __post_init__(self):
        object.__setattr__(self, "provenance", MappingProxyType(dict(self.provenance)))


@dataclass(frozen=True)
class JointBatchAdvantageRecord:
    advantage_record_id: tuple
    batch_id: tuple
    return_record_id: tuple
    critic_target_id: tuple
    undiscounted_return: float
    critic_value: float
    advantage: float
    advantage_definition_id: str
    metric_units: str
    provenance: Mapping[str, str]

    def __post_init__(self):
        object.__setattr__(self, "provenance", MappingProxyType(dict(self.provenance)))


@dataclass(frozen=True)
class PPOPolicyFactorSample:
    decision_event_id: tuple
    joint_batch_id: tuple
    ego_id: str
    decision_role: Any
    claim_identity: Tuple[str, str]
    proposal_id: Optional[tuple]
    actor_observation_snapshot: Any
    hard_action_mask: Tuple[bool, ...]
    selected_action_index: int
    selected_semantic_action: str
    behavior_policy_log_probability: float
    return_record_id: tuple
    advantage_record_id: tuple
    advantage: float
    policy_status: str
    provenance: Mapping[str, str]

    def __post_init__(self):
        object.__setattr__(self, "provenance", MappingProxyType(dict(self.provenance)))

