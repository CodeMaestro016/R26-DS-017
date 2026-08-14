"""Immutable experimental-selection contracts for Step 5J.1."""

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping, Optional, Tuple


EXPERIMENTAL_SELECTION_FRAMEWORK_STATUS = "IMPLEMENTED_STEP_5J_1"
EMPIRICAL_VALUES_SELECTED = False
ARCHITECTURE_SELECTION_STATUS = "NOT_SELECTED"
PPO_CLIP_SELECTION_STATUS = "REQUIRES_EXPERIMENTAL_SELECTION"
LEARNING_RATE_SELECTION_STATUS = "REQUIRES_EXPERIMENTAL_SELECTION"
OPTIMIZER_SELECTION_STATUS = "REQUIRES_EXPERIMENTAL_SELECTION"
NETWORK_CAPACITY_SELECTION_STATUS = "REQUIRES_EXPERIMENTAL_SELECTION"
MULTI_FACTOR_AGGREGATION_SELECTION_STATUS = "METHOD_REVIEW_REQUIRED"
SEED_SELECTION_STATUS = "NOT_SELECTED"
REPLICATION_COUNT_STATUS = "NOT_SELECTED"
STATISTICAL_COMPARISON_STATUS = "NOT_SELECTED"
TRAINING_BUDGET_STATUS = "NOT_SELECTED"
EARLY_STOPPING_STATUS = "REQUIRES_EXPERIMENTAL_DESIGN_SELECTION"
CHECKPOINT_SELECTION_STATUS = "REQUIRES_EXPERIMENTAL_DESIGN_SELECTION"
TRAINING_STATUS = "NOT_STARTED"
SAFETY_SHIELD_STATUS = "NOT_IMPLEMENTED"


class ChoiceClassification(str, Enum):
    MATHEMATICALLY_FIXED = "MATHEMATICALLY_FIXED"
    PHYSICALLY_DERIVED = "PHYSICALLY_DERIVED"
    REGULATORY_FIXED = "REGULATORY_FIXED"
    SCHEMA_DERIVED = "SCHEMA_DERIVED"
    PROJECT_SEMANTIC_REQUIREMENT = "PROJECT_SEMANTIC_REQUIREMENT"
    RESEARCH_SUPPORTED_METHOD = "RESEARCH_SUPPORTED_METHOD"
    ARCHITECTURE_CHOICE_REQUIRES_ABLATION = "ARCHITECTURE_CHOICE_REQUIRES_ABLATION"
    REQUIRES_EXPERIMENTAL_SELECTION = "REQUIRES_EXPERIMENTAL_SELECTION"
    OPTIONAL_FUTURE_ABLATION = "OPTIONAL_FUTURE_ABLATION"
    NOT_APPLICABLE_TO_BASELINE = "NOT_APPLICABLE_TO_BASELINE"


class ScenarioRole(str, Enum):
    TRAINING = "TRAINING"
    VALIDATION = "VALIDATION"
    HELD_OUT_TEST = "HELD_OUT_TEST"


class MetricDirection(str, Enum):
    LOWER_IS_BETTER = "LOWER_IS_BETTER"
    HIGHER_IS_BETTER = "HIGHER_IS_BETTER"
    DIAGNOSTIC_ONLY = "DIAGNOSTIC_ONLY"


class CandidateSource(str, Enum):
    THEORETICAL_BOUND = "THEORETICAL_BOUND"
    ARCHITECTURAL_DISCRETE_ALTERNATIVE = "ARCHITECTURAL_DISCRETE_ALTERNATIVE"
    LITERATURE_INFORMED_SEARCH_REGION = "LITERATURE_INFORMED_SEARCH_REGION"
    PILOT_EXPERIMENT_DERIVED = "PILOT_EXPERIMENT_DERIVED"
    COMPUTE_CONSTRAINT_DERIVED = "COMPUTE_CONSTRAINT_DERIVED"
    PROJECT_SCHEMA_DERIVED = "PROJECT_SCHEMA_DERIVED"


@dataclass(frozen=True)
class ExperimentalChoice:
    choice_id: str
    human_readable_name: str
    component: str
    classification: ChoiceClassification
    current_status: str
    mathematical_or_research_basis: str
    candidate_generation_status: str
    selection_method_status: str
    selected_value: Optional[Any]
    selected_value_status: str
    evidence_record_ids: Tuple[str, ...]
    dependencies: Tuple[str, ...]
    provenance: Mapping[str, str]

    def __post_init__(self):
        object.__setattr__(self, "provenance", MappingProxyType(dict(self.provenance)))


@dataclass(frozen=True)
class CandidateSetDefinition:
    choice_id: str
    candidate_values: Tuple[Any, ...]
    candidate_source: Optional[CandidateSource]
    candidate_justification: str
    candidate_generation_method: str
    status: str = "CANDIDATE_VALUES_NOT_YET_SELECTED"


@dataclass(frozen=True)
class ScenarioManifest:
    manifest_id: tuple
    purpose: ScenarioRole
    scenario_ids: Tuple[tuple, ...]
    scenario_generation_source: str
    demand_schedule_identity: tuple
    intersection_network_identity: str
    vehicle_type_identity: str
    regulatory_profile: str
    perception_configuration_identity: str
    intention_model_identity: str
    randomization_provenance: Mapping[str, str]
    frozen_status: str
    used_for_parameter_selection: bool

    def __post_init__(self):
        object.__setattr__(self, "scenario_ids", tuple(sorted(self.scenario_ids, key=repr)))
        object.__setattr__(self, "randomization_provenance",
                           MappingProxyType(dict(self.randomization_provenance)))


@dataclass(frozen=True)
class SeedManifest:
    manifest_id: tuple
    seed_source: str
    seed_values: Tuple[int, ...]
    purpose: str
    frozen_status: str
    provenance: Mapping[str, str]

    def __post_init__(self):
        object.__setattr__(self, "provenance", MappingProxyType(dict(self.provenance)))


@dataclass(frozen=True)
class ExperimentalConfiguration:
    configuration_id: tuple
    choice_assignments: Mapping[str, Any]
    unresolved_choices: Tuple[str, ...]
    fixed_choices: Tuple[str, ...]
    architecture_identity: str
    training_method_identity: str
    objective_definition_identity: str
    return_definition_identity: str
    regulatory_profile: str
    semantic_schema_versions: Tuple[str, ...]
    provenance: Mapping[str, str]

    def __post_init__(self):
        object.__setattr__(self, "choice_assignments",
                           MappingProxyType(dict(self.choice_assignments)))
        object.__setattr__(self, "provenance", MappingProxyType(dict(self.provenance)))


@dataclass(frozen=True)
class ExperimentMetricManifest:
    manifest_id: tuple
    primary_selection_metric: str
    primary_direction: MetricDirection
    equivalent_reward_metric: str
    secondary_diagnostics: Tuple[str, ...]
    hard_validity_gates: Tuple[str, ...]
    weighted_composite_score: bool


@dataclass(frozen=True)
class ExperimentManifest:
    experiment_id: tuple
    experiment_family: str
    research_question: str
    hypothesis: str
    choices_under_test: Tuple[str, ...]
    fixed_baseline_choices: Tuple[str, ...]
    training_scenario_manifest_id: tuple
    validation_scenario_manifest_id: tuple
    held_out_test_manifest_id: tuple
    replication_manifest_id: tuple
    metrics_manifest_id: tuple
    hard_validity_gate_manifest_id: tuple
    selection_rule_manifest_id: tuple
    software_version: str
    code_revision_metadata: Mapping[str, str]
    environment_metadata: Mapping[str, str]
    provenance: Mapping[str, str]

    def __post_init__(self):
        for field in ("code_revision_metadata", "environment_metadata", "provenance"):
            object.__setattr__(self, field, MappingProxyType(dict(getattr(self, field))))


@dataclass(frozen=True)
class ValidityGateResult:
    gate_id: str
    passed: bool
    evidence: Tuple[str, ...]
    source: str
    provenance: Mapping[str, str]

    def __post_init__(self):
        object.__setattr__(self, "provenance", MappingProxyType(dict(self.provenance)))


@dataclass(frozen=True)
class ExperimentRunRecord:
    run_id: tuple
    experiment_id: tuple
    configuration_id: tuple
    scenario_manifest_id: tuple
    seed_manifest_entry: Optional[tuple]
    run_role: ScenarioRole
    training_status: str
    validation_status: str
    start_metadata: Mapping[str, str]
    completion_metadata: Mapping[str, str]
    metric_results: Tuple[tuple, ...]
    validity_gate_results: Tuple[ValidityGateResult, ...]
    artifact_ids: Tuple[str, ...]
    checkpoint_id: Optional[str]
    code_revision: str
    provenance: Mapping[str, str]

    def __post_init__(self):
        for field in ("start_metadata", "completion_metadata", "provenance"):
            object.__setattr__(self, field, MappingProxyType(dict(getattr(self, field))))


@dataclass(frozen=True)
class SelectionMetricRecord:
    run_id: tuple
    metric_id: str
    raw_value: float
    units: str
    direction: MetricDirection
    aggregation_scope: str
    scenario_manifest_id: tuple
    provenance: Mapping[str, str]

    def __post_init__(self):
        object.__setattr__(self, "provenance", MappingProxyType(dict(self.provenance)))


@dataclass(frozen=True)
class SelectionDecisionRecord:
    selection_id: tuple
    experiment_id: tuple
    choice_id: str
    candidate_configuration_ids: Tuple[tuple, ...]
    eligible_configuration_ids: Tuple[tuple, ...]
    rejected_configuration_ids: Tuple[tuple, ...]
    primary_metric_id: str
    comparison_method: str
    selected_configuration_id: Optional[tuple]
    selected_value: Optional[Any]
    evidence_run_ids: Tuple[tuple, ...]
    validation_manifest_id: tuple
    held_out_test_used: bool
    decision_status: str
    provenance: Mapping[str, str]

    def __post_init__(self):
        object.__setattr__(self, "provenance", MappingProxyType(dict(self.provenance)))

