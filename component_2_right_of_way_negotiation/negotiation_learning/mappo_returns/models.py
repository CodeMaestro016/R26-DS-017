"""Immutable complete-episode MAPPO mathematics records for Step 5I."""

# Import dataclass from dataclasses for the operations below.
from dataclasses import dataclass
# Import MappingProxyType from types for the operations below.
from types import MappingProxyType
# Import Any, Mapping, Optional, Tuple from typing for the operations below.
from typing import Any, Mapping, Optional, Tuple


# Set RETURN_SEMANTICS_STATUS to the text 'EXACT_UNDISCOUNTED_EPISODIC_TEAM_RETURN'.
RETURN_SEMANTICS_STATUS = "EXACT_UNDISCOUNTED_EPISODIC_TEAM_RETURN"
# Set DISCOUNT_FACTOR_STATUS to the text 'NOT_REQUIRED_FOR_EXACT_STEP_5H_BASELINE_OBJECTIVE'.
DISCOUNT_FACTOR_STATUS = "NOT_REQUIRED_FOR_EXACT_STEP_5H_BASELINE_OBJECTIVE"
# Set BOOTSTRAP_SEMANTICS_STATUS to the text 'NO_BOOTSTRAP_FOR_COMPLETE_EPISODIC_BASELINE'.
BOOTSTRAP_SEMANTICS_STATUS = "NO_BOOTSTRAP_FOR_COMPLETE_EPISODIC_BASELINE"
# Set TRUNCATED_ROLLOUT_STATUS to the text 'REQUIRES_BOOTSTRAP_RESEARCH_DECISION'.
TRUNCATED_ROLLOUT_STATUS = "REQUIRES_BOOTSTRAP_RESEARCH_DECISION"
# Set ADVANTAGE_DEFINITION_STATUS to the text 'MONTE_CARLO_RETURN_MINUS_CENTRALIZED_VALUE'.
ADVANTAGE_DEFINITION_STATUS = "MONTE_CARLO_RETURN_MINUS_CENTRALIZED_VALUE"
# Set GAE_STATUS to the text 'NOT_USED_BASELINE_PARAMETER_REQUIRES_EXPERIMENTAL_SELECTION'.
GAE_STATUS = "NOT_USED_BASELINE_PARAMETER_REQUIRES_EXPERIMENTAL_SELECTION"
# Set GAE_LAMBDA_STATUS to the text 'NOT_SELECTED'.
GAE_LAMBDA_STATUS = "NOT_SELECTED"
# Set ADVANTAGE_NORMALIZATION_STATUS to the text 'NOT_IMPLEMENTED_REQUIRES_EXPERIMENTAL_EVALUATION'.
ADVANTAGE_NORMALIZATION_STATUS = "NOT_IMPLEMENTED_REQUIRES_EXPERIMENTAL_EVALUATION"
# Set PPO_RATIO_STATUS to the text 'MATHEMATICAL_INTERFACE_IMPLEMENTED'.
PPO_RATIO_STATUS = "MATHEMATICAL_INTERFACE_IMPLEMENTED"
# Set PPO_CLIP_PARAMETER_STATUS to the text 'REQUIRES_EXPERIMENTAL_SELECTION'.
PPO_CLIP_PARAMETER_STATUS = "REQUIRES_EXPERIMENTAL_SELECTION"
# Set PPO_MULTI_FACTOR_AGGREGATION_STATUS to the text 'REQUIRES_METHOD_SELECTION_BEFORE_OPTIMIZATION'.
PPO_MULTI_FACTOR_AGGREGATION_STATUS = "REQUIRES_METHOD_SELECTION_BEFORE_OPTIMIZATION"
# Set PPO_OPTIMIZATION_STATUS to the text 'MATHEMATICAL_INTERFACE_ONLY_NO_PARAMETER_UPDATE'.
PPO_OPTIMIZATION_STATUS = "MATHEMATICAL_INTERFACE_ONLY_NO_PARAMETER_UPDATE"
# Set RETURN_DEFINITION_ID to the text 'EXACT_UNDISCOUNTED_TEAM_RETURN_V1'.
RETURN_DEFINITION_ID = "EXACT_UNDISCOUNTED_TEAM_RETURN_V1"
# Set RETURN_UNITS to the text 'NEGATIVE_VEHICLE_SECONDS'.
RETURN_UNITS = "NEGATIVE_VEHICLE_SECONDS"


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define JointBatchReturnRecord to group the state and operations declared below.
# Declared fields: return_record_id, batch_id, terminal_batch_id, objective_record_ids, undiscounted_team_return,
# return_definition_id, reward_definition_id, metric_units, episode_identity, provenance.
# Construction and attribute behavior follow the declared decorators and base classes.
class JointBatchReturnRecord:
    # Declare return_record_id as tuple for this data structure.
    return_record_id: tuple
    # Declare batch_id as tuple for this data structure.
    batch_id: tuple
    # Declare terminal_batch_id as tuple for this data structure.
    terminal_batch_id: tuple
    # Declare objective_record_ids as Tuple[tuple, ...] for this data structure.
    objective_record_ids: Tuple[tuple, ...]
    # Declare undiscounted_team_return as float for this data structure.
    undiscounted_team_return: float
    # Declare return_definition_id as str for this data structure.
    return_definition_id: str
    # Declare reward_definition_id as str for this data structure.
    reward_definition_id: str
    # Declare metric_units as str for this data structure.
    metric_units: str
    # Declare episode_identity as str for this data structure.
    episode_identity: str
    # Declare provenance as Mapping[str, str] for this data structure.
    provenance: Mapping[str, str]

    # Post init using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    def __post_init__(self):
        # Call object.__setattr__ with the supplied arguments.
        object.__setattr__(self, "provenance", MappingProxyType(dict(self.provenance)))


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define CentralizedBatchValueTarget to group the state and operations declared below.
# Declared fields: critic_target_id, batch_id, return_record_id, target_return, critic_value_at_collection,
# critic_target, value_error, value_squared_error, units, provenance.
# Construction and attribute behavior follow the declared decorators and base classes.
class CentralizedBatchValueTarget:
    # Declare critic_target_id as tuple for this data structure.
    critic_target_id: tuple
    # Declare batch_id as tuple for this data structure.
    batch_id: tuple
    # Declare return_record_id as tuple for this data structure.
    return_record_id: tuple
    # Declare target_return as float for this data structure.
    target_return: float
    # Declare critic_value_at_collection as float for this data structure.
    critic_value_at_collection: float
    # Declare critic_target as float for this data structure.
    critic_target: float
    # Declare value_error as float for this data structure.
    value_error: float
    # Declare value_squared_error as float for this data structure.
    value_squared_error: float
    # Declare units as str for this data structure.
    units: str
    # Declare provenance as Mapping[str, str] for this data structure.
    provenance: Mapping[str, str]

    # Post init using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    def __post_init__(self):
        # Call object.__setattr__ with the supplied arguments.
        object.__setattr__(self, "provenance", MappingProxyType(dict(self.provenance)))


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define JointBatchAdvantageRecord to group the state and operations declared below.
# Declared fields: advantage_record_id, batch_id, return_record_id, critic_target_id, undiscounted_return,
# critic_value, advantage, advantage_definition_id, metric_units, provenance.
# Construction and attribute behavior follow the declared decorators and base classes.
class JointBatchAdvantageRecord:
    # Declare advantage_record_id as tuple for this data structure.
    advantage_record_id: tuple
    # Declare batch_id as tuple for this data structure.
    batch_id: tuple
    # Declare return_record_id as tuple for this data structure.
    return_record_id: tuple
    # Declare critic_target_id as tuple for this data structure.
    critic_target_id: tuple
    # Declare undiscounted_return as float for this data structure.
    undiscounted_return: float
    # Declare critic_value as float for this data structure.
    critic_value: float
    # Declare advantage as float for this data structure.
    advantage: float
    # Declare advantage_definition_id as str for this data structure.
    advantage_definition_id: str
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
# Define PPOPolicyFactorSample to group the state and operations declared below.
# Declared fields: decision_event_id, joint_batch_id, ego_id, decision_role, claim_identity, proposal_id,
# actor_observation_snapshot, hard_action_mask, selected_action_index, selected_semantic_action,....
# Construction and attribute behavior follow the declared decorators and base classes.
class PPOPolicyFactorSample:
    # Declare decision_event_id as tuple for this data structure.
    decision_event_id: tuple
    # Declare joint_batch_id as tuple for this data structure.
    joint_batch_id: tuple
    # Declare ego_id as str for this data structure.
    ego_id: str
    # Declare decision_role as Any for this data structure.
    decision_role: Any
    # Declare claim_identity as Tuple[str, str] for this data structure.
    claim_identity: Tuple[str, str]
    # Declare proposal_id as Optional[tuple] for this data structure.
    proposal_id: Optional[tuple]
    # Declare actor_observation_snapshot as Any for this data structure.
    actor_observation_snapshot: Any
    # Declare hard_action_mask as Tuple[bool, ...] for this data structure.
    hard_action_mask: Tuple[bool, ...]
    # Declare selected_action_index as int for this data structure.
    selected_action_index: int
    # Declare selected_semantic_action as str for this data structure.
    selected_semantic_action: str
    # Declare behavior_policy_log_probability as float for this data structure.
    behavior_policy_log_probability: float
    # Declare return_record_id as tuple for this data structure.
    return_record_id: tuple
    # Declare advantage_record_id as tuple for this data structure.
    advantage_record_id: tuple
    # Declare advantage as float for this data structure.
    advantage: float
    # Declare policy_status as str for this data structure.
    policy_status: str
    # Declare provenance as Mapping[str, str] for this data structure.
    provenance: Mapping[str, str]

    # Post init using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    def __post_init__(self):
        # Call object.__setattr__ with the supplied arguments.
        object.__setattr__(self, "provenance", MappingProxyType(dict(self.provenance)))

