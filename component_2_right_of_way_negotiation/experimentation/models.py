"""Immutable experimental-selection contracts for Step 5J.1."""

# Import dataclass from dataclasses for the operations below.
from dataclasses import dataclass
# Import Enum from enum for the operations below.
from enum import Enum
# Import MappingProxyType from types for the operations below.
from types import MappingProxyType
# Import Any, Mapping, Optional, Tuple from typing for the operations below.
from typing import Any, Mapping, Optional, Tuple


# Set EXPERIMENTAL_SELECTION_FRAMEWORK_STATUS to the text 'IMPLEMENTED_STEP_5J_1'.
EXPERIMENTAL_SELECTION_FRAMEWORK_STATUS = "IMPLEMENTED_STEP_5J_1"
# Set EMPIRICAL_VALUES_SELECTED to False.
EMPIRICAL_VALUES_SELECTED = False
# Set ARCHITECTURE_SELECTION_STATUS to the text 'NOT_SELECTED'.
ARCHITECTURE_SELECTION_STATUS = "NOT_SELECTED"
# Set PPO_CLIP_SELECTION_STATUS to the text 'REQUIRES_EXPERIMENTAL_SELECTION'.
PPO_CLIP_SELECTION_STATUS = "REQUIRES_EXPERIMENTAL_SELECTION"
# Set LEARNING_RATE_SELECTION_STATUS to the text 'REQUIRES_EXPERIMENTAL_SELECTION'.
LEARNING_RATE_SELECTION_STATUS = "REQUIRES_EXPERIMENTAL_SELECTION"
# Set OPTIMIZER_SELECTION_STATUS to the text 'REQUIRES_EXPERIMENTAL_SELECTION'.
OPTIMIZER_SELECTION_STATUS = "REQUIRES_EXPERIMENTAL_SELECTION"
# Set NETWORK_CAPACITY_SELECTION_STATUS to the text 'REQUIRES_EXPERIMENTAL_SELECTION'.
NETWORK_CAPACITY_SELECTION_STATUS = "REQUIRES_EXPERIMENTAL_SELECTION"
# Set MULTI_FACTOR_AGGREGATION_SELECTION_STATUS to the text 'METHOD_REVIEW_REQUIRED'.
MULTI_FACTOR_AGGREGATION_SELECTION_STATUS = "METHOD_REVIEW_REQUIRED"
# Set SEED_SELECTION_STATUS to the text 'NOT_SELECTED'.
SEED_SELECTION_STATUS = "NOT_SELECTED"
# Set REPLICATION_COUNT_STATUS to the text 'NOT_SELECTED'.
REPLICATION_COUNT_STATUS = "NOT_SELECTED"
# Set STATISTICAL_COMPARISON_STATUS to the text 'NOT_SELECTED'.
STATISTICAL_COMPARISON_STATUS = "NOT_SELECTED"
# Set TRAINING_BUDGET_STATUS to the text 'NOT_SELECTED'.
TRAINING_BUDGET_STATUS = "NOT_SELECTED"
# Set EARLY_STOPPING_STATUS to the text 'REQUIRES_EXPERIMENTAL_DESIGN_SELECTION'.
EARLY_STOPPING_STATUS = "REQUIRES_EXPERIMENTAL_DESIGN_SELECTION"
# Set CHECKPOINT_SELECTION_STATUS to the text 'REQUIRES_EXPERIMENTAL_DESIGN_SELECTION'.
CHECKPOINT_SELECTION_STATUS = "REQUIRES_EXPERIMENTAL_DESIGN_SELECTION"
# Set TRAINING_STATUS to the text 'NOT_STARTED'.
TRAINING_STATUS = "NOT_STARTED"
# Set SAFETY_SHIELD_STATUS to the text 'NOT_IMPLEMENTED'.
SAFETY_SHIELD_STATUS = "NOT_IMPLEMENTED"


# Define ChoiceClassification to group the state and operations declared below.
# Base classes: str, Enum.
# Instances expose the attributes and methods implemented in this class.
class ChoiceClassification(str, Enum):
    # Set MATHEMATICALLY_FIXED to the text 'MATHEMATICALLY_FIXED'.
    MATHEMATICALLY_FIXED = "MATHEMATICALLY_FIXED"
    # Set PHYSICALLY_DERIVED to the text 'PHYSICALLY_DERIVED'.
    PHYSICALLY_DERIVED = "PHYSICALLY_DERIVED"
    # Set REGULATORY_FIXED to the text 'REGULATORY_FIXED'.
    REGULATORY_FIXED = "REGULATORY_FIXED"
    # Set SCHEMA_DERIVED to the text 'SCHEMA_DERIVED'.
    SCHEMA_DERIVED = "SCHEMA_DERIVED"
    # Set PROJECT_SEMANTIC_REQUIREMENT to the text 'PROJECT_SEMANTIC_REQUIREMENT'.
    PROJECT_SEMANTIC_REQUIREMENT = "PROJECT_SEMANTIC_REQUIREMENT"
    # Set RESEARCH_SUPPORTED_METHOD to the text 'RESEARCH_SUPPORTED_METHOD'.
    RESEARCH_SUPPORTED_METHOD = "RESEARCH_SUPPORTED_METHOD"
    # Set ARCHITECTURE_CHOICE_REQUIRES_ABLATION to the text 'ARCHITECTURE_CHOICE_REQUIRES_ABLATION'.
    ARCHITECTURE_CHOICE_REQUIRES_ABLATION = "ARCHITECTURE_CHOICE_REQUIRES_ABLATION"
    # Set REQUIRES_EXPERIMENTAL_SELECTION to the text 'REQUIRES_EXPERIMENTAL_SELECTION'.
    REQUIRES_EXPERIMENTAL_SELECTION = "REQUIRES_EXPERIMENTAL_SELECTION"
    # Set OPTIONAL_FUTURE_ABLATION to the text 'OPTIONAL_FUTURE_ABLATION'.
    OPTIONAL_FUTURE_ABLATION = "OPTIONAL_FUTURE_ABLATION"
    # Set NOT_APPLICABLE_TO_BASELINE to the text 'NOT_APPLICABLE_TO_BASELINE'.
    NOT_APPLICABLE_TO_BASELINE = "NOT_APPLICABLE_TO_BASELINE"


# Define ScenarioRole to group the state and operations declared below.
# Base classes: str, Enum.
# Instances expose the attributes and methods implemented in this class.
class ScenarioRole(str, Enum):
    # Set TRAINING to the text 'TRAINING'.
    TRAINING = "TRAINING"
    # Set VALIDATION to the text 'VALIDATION'.
    VALIDATION = "VALIDATION"
    # Set HELD_OUT_TEST to the text 'HELD_OUT_TEST'.
    HELD_OUT_TEST = "HELD_OUT_TEST"


# Define MetricDirection to group the state and operations declared below.
# Base classes: str, Enum.
# Instances expose the attributes and methods implemented in this class.
class MetricDirection(str, Enum):
    # Set LOWER_IS_BETTER to the text 'LOWER_IS_BETTER'.
    LOWER_IS_BETTER = "LOWER_IS_BETTER"
    # Set HIGHER_IS_BETTER to the text 'HIGHER_IS_BETTER'.
    HIGHER_IS_BETTER = "HIGHER_IS_BETTER"
    # Set DIAGNOSTIC_ONLY to the text 'DIAGNOSTIC_ONLY'.
    DIAGNOSTIC_ONLY = "DIAGNOSTIC_ONLY"


# Define CandidateSource to group the state and operations declared below.
# Base classes: str, Enum.
# Instances expose the attributes and methods implemented in this class.
class CandidateSource(str, Enum):
    # Set THEORETICAL_BOUND to the text 'THEORETICAL_BOUND'.
    THEORETICAL_BOUND = "THEORETICAL_BOUND"
    # Set ARCHITECTURAL_DISCRETE_ALTERNATIVE to the text 'ARCHITECTURAL_DISCRETE_ALTERNATIVE'.
    ARCHITECTURAL_DISCRETE_ALTERNATIVE = "ARCHITECTURAL_DISCRETE_ALTERNATIVE"
    # Set LITERATURE_INFORMED_SEARCH_REGION to the text 'LITERATURE_INFORMED_SEARCH_REGION'.
    LITERATURE_INFORMED_SEARCH_REGION = "LITERATURE_INFORMED_SEARCH_REGION"
    # Set PILOT_EXPERIMENT_DERIVED to the text 'PILOT_EXPERIMENT_DERIVED'.
    PILOT_EXPERIMENT_DERIVED = "PILOT_EXPERIMENT_DERIVED"
    # Set COMPUTE_CONSTRAINT_DERIVED to the text 'COMPUTE_CONSTRAINT_DERIVED'.
    COMPUTE_CONSTRAINT_DERIVED = "COMPUTE_CONSTRAINT_DERIVED"
    # Set PROJECT_SCHEMA_DERIVED to the text 'PROJECT_SCHEMA_DERIVED'.
    PROJECT_SCHEMA_DERIVED = "PROJECT_SCHEMA_DERIVED"


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define ExperimentalChoice to group the state and operations declared below.
# Declared fields: choice_id, human_readable_name, component, classification, current_status,
# mathematical_or_research_basis, candidate_generation_status, selection_method_status, selected_value,
# selected_value_status,....
# Construction and attribute behavior follow the declared decorators and base classes.
class ExperimentalChoice:
    # Declare choice_id as str for this data structure.
    choice_id: str
    # Declare human_readable_name as str for this data structure.
    human_readable_name: str
    # Declare component as str for this data structure.
    component: str
    # Declare classification as ChoiceClassification for this data structure.
    classification: ChoiceClassification
    # Declare current_status as str for this data structure.
    current_status: str
    # Declare mathematical_or_research_basis as str for this data structure.
    mathematical_or_research_basis: str
    # Declare candidate_generation_status as str for this data structure.
    candidate_generation_status: str
    # Declare selection_method_status as str for this data structure.
    selection_method_status: str
    # Declare selected_value as Optional[Any] for this data structure.
    selected_value: Optional[Any]
    # Declare selected_value_status as str for this data structure.
    selected_value_status: str
    # Declare evidence_record_ids as Tuple[str, ...] for this data structure.
    evidence_record_ids: Tuple[str, ...]
    # Declare dependencies as Tuple[str, ...] for this data structure.
    dependencies: Tuple[str, ...]
    # Declare provenance as Mapping[str, str] for this data structure.
    provenance: Mapping[str, str]

    # Post init using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    def __post_init__(self):
        # Call object.__setattr__ with the supplied arguments.
        object.__setattr__(self, "provenance", MappingProxyType(dict(self.provenance)))


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define CandidateSetDefinition to group the state and operations declared below.
# Declared fields: choice_id, candidate_values, candidate_source, candidate_justification,
# candidate_generation_method, status.
# Construction and attribute behavior follow the declared decorators and base classes.
class CandidateSetDefinition:
    # Declare choice_id as str for this data structure.
    choice_id: str
    # Declare candidate_values as Tuple[Any, ...] for this data structure.
    candidate_values: Tuple[Any, ...]
    # Declare candidate_source as Optional[CandidateSource] for this data structure.
    candidate_source: Optional[CandidateSource]
    # Declare candidate_justification as str for this data structure.
    candidate_justification: str
    # Declare candidate_generation_method as str for this data structure.
    candidate_generation_method: str
    # Set status to the text 'CANDIDATE_VALUES_NOT_YET_SELECTED'; declare its type as str.
    status: str = "CANDIDATE_VALUES_NOT_YET_SELECTED"


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define ScenarioManifest to group the state and operations declared below.
# Declared fields: manifest_id, purpose, scenario_ids, scenario_generation_source, demand_schedule_identity,
# intersection_network_identity, vehicle_type_identity, regulatory_profile, perception_configuration_identity,....
# Construction and attribute behavior follow the declared decorators and base classes.
class ScenarioManifest:
    # Declare manifest_id as tuple for this data structure.
    manifest_id: tuple
    # Declare purpose as ScenarioRole for this data structure.
    purpose: ScenarioRole
    # Declare scenario_ids as Tuple[tuple, ...] for this data structure.
    scenario_ids: Tuple[tuple, ...]
    # Declare scenario_generation_source as str for this data structure.
    scenario_generation_source: str
    # Declare demand_schedule_identity as tuple for this data structure.
    demand_schedule_identity: tuple
    # Declare intersection_network_identity as str for this data structure.
    intersection_network_identity: str
    # Declare vehicle_type_identity as str for this data structure.
    vehicle_type_identity: str
    # Declare regulatory_profile as str for this data structure.
    regulatory_profile: str
    # Declare perception_configuration_identity as str for this data structure.
    perception_configuration_identity: str
    # Declare intention_model_identity as str for this data structure.
    intention_model_identity: str
    # Declare randomization_provenance as Mapping[str, str] for this data structure.
    randomization_provenance: Mapping[str, str]
    # Declare frozen_status as str for this data structure.
    frozen_status: str
    # Declare used_for_parameter_selection as bool for this data structure.
    used_for_parameter_selection: bool

    # Post init using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    def __post_init__(self):
        # Call object.__setattr__ with the supplied arguments.
        object.__setattr__(self, "scenario_ids", tuple(sorted(self.scenario_ids, key=repr)))
        # Call object.__setattr__ with the supplied arguments.
        object.__setattr__(self, "randomization_provenance",
                           # Supply the result of MappingProxyType(a dictionary built from
                           # self.randomization_provenance) to object.__setattr__.
                           MappingProxyType(dict(self.randomization_provenance)))


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define SeedManifest to group the state and operations declared below.
# Declared fields: manifest_id, seed_source, seed_values, purpose, frozen_status, provenance.
# Construction and attribute behavior follow the declared decorators and base classes.
class SeedManifest:
    # Declare manifest_id as tuple for this data structure.
    manifest_id: tuple
    # Declare seed_source as str for this data structure.
    seed_source: str
    # Declare seed_values as Tuple[int, ...] for this data structure.
    seed_values: Tuple[int, ...]
    # Declare purpose as str for this data structure.
    purpose: str
    # Declare frozen_status as str for this data structure.
    frozen_status: str
    # Declare provenance as Mapping[str, str] for this data structure.
    provenance: Mapping[str, str]

    # Post init using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    def __post_init__(self):
        # Call object.__setattr__ with the supplied arguments.
        object.__setattr__(self, "provenance", MappingProxyType(dict(self.provenance)))


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define ExperimentalConfiguration to group the state and operations declared below.
# Declared fields: configuration_id, choice_assignments, unresolved_choices, fixed_choices, architecture_identity,
# training_method_identity, objective_definition_identity, return_definition_identity, regulatory_profile,....
# Construction and attribute behavior follow the declared decorators and base classes.
class ExperimentalConfiguration:
    # Declare configuration_id as tuple for this data structure.
    configuration_id: tuple
    # Declare choice_assignments as Mapping[str, Any] for this data structure.
    choice_assignments: Mapping[str, Any]
    # Declare unresolved_choices as Tuple[str, ...] for this data structure.
    unresolved_choices: Tuple[str, ...]
    # Declare fixed_choices as Tuple[str, ...] for this data structure.
    fixed_choices: Tuple[str, ...]
    # Declare architecture_identity as str for this data structure.
    architecture_identity: str
    # Declare training_method_identity as str for this data structure.
    training_method_identity: str
    # Declare objective_definition_identity as str for this data structure.
    objective_definition_identity: str
    # Declare return_definition_identity as str for this data structure.
    return_definition_identity: str
    # Declare regulatory_profile as str for this data structure.
    regulatory_profile: str
    # Declare semantic_schema_versions as Tuple[str, ...] for this data structure.
    semantic_schema_versions: Tuple[str, ...]
    # Declare provenance as Mapping[str, str] for this data structure.
    provenance: Mapping[str, str]

    # Post init using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    def __post_init__(self):
        # Call object.__setattr__ with the supplied arguments.
        object.__setattr__(self, "choice_assignments",
                           # Supply the result of MappingProxyType(a dictionary built from
                           # self.choice_assignments) to object.__setattr__.
                           MappingProxyType(dict(self.choice_assignments)))
        # Call object.__setattr__ with the supplied arguments.
        object.__setattr__(self, "provenance", MappingProxyType(dict(self.provenance)))


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define ExperimentMetricManifest to group the state and operations declared below.
# Declared fields: manifest_id, primary_selection_metric, primary_direction, equivalent_reward_metric,
# secondary_diagnostics, hard_validity_gates, weighted_composite_score.
# Construction and attribute behavior follow the declared decorators and base classes.
class ExperimentMetricManifest:
    # Declare manifest_id as tuple for this data structure.
    manifest_id: tuple
    # Declare primary_selection_metric as str for this data structure.
    primary_selection_metric: str
    # Declare primary_direction as MetricDirection for this data structure.
    primary_direction: MetricDirection
    # Declare equivalent_reward_metric as str for this data structure.
    equivalent_reward_metric: str
    # Declare secondary_diagnostics as Tuple[str, ...] for this data structure.
    secondary_diagnostics: Tuple[str, ...]
    # Declare hard_validity_gates as Tuple[str, ...] for this data structure.
    hard_validity_gates: Tuple[str, ...]
    # Declare weighted_composite_score as bool for this data structure.
    weighted_composite_score: bool


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define ExperimentManifest to group the state and operations declared below.
# Declared fields: experiment_id, experiment_family, research_question, hypothesis, choices_under_test,
# fixed_baseline_choices, training_scenario_manifest_id, validation_scenario_manifest_id,
# held_out_test_manifest_id,....
# Construction and attribute behavior follow the declared decorators and base classes.
class ExperimentManifest:
    # Declare experiment_id as tuple for this data structure.
    experiment_id: tuple
    # Declare experiment_family as str for this data structure.
    experiment_family: str
    # Declare research_question as str for this data structure.
    research_question: str
    # Declare hypothesis as str for this data structure.
    hypothesis: str
    # Declare choices_under_test as Tuple[str, ...] for this data structure.
    choices_under_test: Tuple[str, ...]
    # Declare fixed_baseline_choices as Tuple[str, ...] for this data structure.
    fixed_baseline_choices: Tuple[str, ...]
    # Declare training_scenario_manifest_id as tuple for this data structure.
    training_scenario_manifest_id: tuple
    # Declare validation_scenario_manifest_id as tuple for this data structure.
    validation_scenario_manifest_id: tuple
    # Declare held_out_test_manifest_id as tuple for this data structure.
    held_out_test_manifest_id: tuple
    # Declare replication_manifest_id as tuple for this data structure.
    replication_manifest_id: tuple
    # Declare metrics_manifest_id as tuple for this data structure.
    metrics_manifest_id: tuple
    # Declare hard_validity_gate_manifest_id as tuple for this data structure.
    hard_validity_gate_manifest_id: tuple
    # Declare selection_rule_manifest_id as tuple for this data structure.
    selection_rule_manifest_id: tuple
    # Declare software_version as str for this data structure.
    software_version: str
    # Declare code_revision_metadata as Mapping[str, str] for this data structure.
    code_revision_metadata: Mapping[str, str]
    # Declare environment_metadata as Mapping[str, str] for this data structure.
    environment_metadata: Mapping[str, str]
    # Declare provenance as Mapping[str, str] for this data structure.
    provenance: Mapping[str, str]

    # Post init using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    # Processing: iterate over the relevant records.
    def __post_init__(self):
        # Iterate over a tuple containing the text 'code_revision_metadata', the text 'environment_metadata', the
        # text 'provenance', binding each item to field.
        for field in ("code_revision_metadata", "environment_metadata", "provenance"):
            # Call object.__setattr__ with the supplied arguments.
            object.__setattr__(self, field, MappingProxyType(dict(getattr(self, field))))


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define ValidityGateResult to group the state and operations declared below.
# Declared fields: gate_id, passed, evidence, source, provenance.
# Construction and attribute behavior follow the declared decorators and base classes.
class ValidityGateResult:
    # Declare gate_id as str for this data structure.
    gate_id: str
    # Declare passed as bool for this data structure.
    passed: bool
    # Declare evidence as Tuple[str, ...] for this data structure.
    evidence: Tuple[str, ...]
    # Declare source as str for this data structure.
    source: str
    # Declare provenance as Mapping[str, str] for this data structure.
    provenance: Mapping[str, str]

    # Post init using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    def __post_init__(self):
        # Call object.__setattr__ with the supplied arguments.
        object.__setattr__(self, "provenance", MappingProxyType(dict(self.provenance)))


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define ExperimentRunRecord to group the state and operations declared below.
# Declared fields: run_id, experiment_id, configuration_id, scenario_manifest_id, seed_manifest_entry, run_role,
# training_status, validation_status, start_metadata, completion_metadata, metric_results,
# validity_gate_results,....
# Construction and attribute behavior follow the declared decorators and base classes.
class ExperimentRunRecord:
    # Declare run_id as tuple for this data structure.
    run_id: tuple
    # Declare experiment_id as tuple for this data structure.
    experiment_id: tuple
    # Declare configuration_id as tuple for this data structure.
    configuration_id: tuple
    # Declare scenario_manifest_id as tuple for this data structure.
    scenario_manifest_id: tuple
    # Declare seed_manifest_entry as Optional[tuple] for this data structure.
    seed_manifest_entry: Optional[tuple]
    # Declare run_role as ScenarioRole for this data structure.
    run_role: ScenarioRole
    # Declare training_status as str for this data structure.
    training_status: str
    # Declare validation_status as str for this data structure.
    validation_status: str
    # Declare start_metadata as Mapping[str, str] for this data structure.
    start_metadata: Mapping[str, str]
    # Declare completion_metadata as Mapping[str, str] for this data structure.
    completion_metadata: Mapping[str, str]
    # Declare metric_results as Tuple[tuple, ...] for this data structure.
    metric_results: Tuple[tuple, ...]
    # Declare validity_gate_results as Tuple[ValidityGateResult, ...] for this data structure.
    validity_gate_results: Tuple[ValidityGateResult, ...]
    # Declare artifact_ids as Tuple[str, ...] for this data structure.
    artifact_ids: Tuple[str, ...]
    # Declare checkpoint_id as Optional[str] for this data structure.
    checkpoint_id: Optional[str]
    # Declare code_revision as str for this data structure.
    code_revision: str
    # Declare provenance as Mapping[str, str] for this data structure.
    provenance: Mapping[str, str]

    # Post init using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    # Processing: iterate over the relevant records.
    def __post_init__(self):
        # Iterate over a tuple containing the text 'start_metadata', the text 'completion_metadata', the text
        # 'provenance', binding each item to field.
        for field in ("start_metadata", "completion_metadata", "provenance"):
            # Call object.__setattr__ with the supplied arguments.
            object.__setattr__(self, field, MappingProxyType(dict(getattr(self, field))))


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define SelectionMetricRecord to group the state and operations declared below.
# Declared fields: run_id, metric_id, raw_value, units, direction, aggregation_scope, scenario_manifest_id,
# provenance.
# Construction and attribute behavior follow the declared decorators and base classes.
class SelectionMetricRecord:
    # Declare run_id as tuple for this data structure.
    run_id: tuple
    # Declare metric_id as str for this data structure.
    metric_id: str
    # Declare raw_value as float for this data structure.
    raw_value: float
    # Declare units as str for this data structure.
    units: str
    # Declare direction as MetricDirection for this data structure.
    direction: MetricDirection
    # Declare aggregation_scope as str for this data structure.
    aggregation_scope: str
    # Declare scenario_manifest_id as tuple for this data structure.
    scenario_manifest_id: tuple
    # Declare provenance as Mapping[str, str] for this data structure.
    provenance: Mapping[str, str]

    # Post init using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    def __post_init__(self):
        # Call object.__setattr__ with the supplied arguments.
        object.__setattr__(self, "provenance", MappingProxyType(dict(self.provenance)))


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define SelectionDecisionRecord to group the state and operations declared below.
# Declared fields: selection_id, experiment_id, choice_id, candidate_configuration_ids,
# eligible_configuration_ids, rejected_configuration_ids, primary_metric_id, comparison_method,
# selected_configuration_id, selected_value,....
# Construction and attribute behavior follow the declared decorators and base classes.
class SelectionDecisionRecord:
    # Declare selection_id as tuple for this data structure.
    selection_id: tuple
    # Declare experiment_id as tuple for this data structure.
    experiment_id: tuple
    # Declare choice_id as str for this data structure.
    choice_id: str
    # Declare candidate_configuration_ids as Tuple[tuple, ...] for this data structure.
    candidate_configuration_ids: Tuple[tuple, ...]
    # Declare eligible_configuration_ids as Tuple[tuple, ...] for this data structure.
    eligible_configuration_ids: Tuple[tuple, ...]
    # Declare rejected_configuration_ids as Tuple[tuple, ...] for this data structure.
    rejected_configuration_ids: Tuple[tuple, ...]
    # Declare primary_metric_id as str for this data structure.
    primary_metric_id: str
    # Declare comparison_method as str for this data structure.
    comparison_method: str
    # Declare selected_configuration_id as Optional[tuple] for this data structure.
    selected_configuration_id: Optional[tuple]
    # Declare selected_value as Optional[Any] for this data structure.
    selected_value: Optional[Any]
    # Declare evidence_run_ids as Tuple[tuple, ...] for this data structure.
    evidence_run_ids: Tuple[tuple, ...]
    # Declare validation_manifest_id as tuple for this data structure.
    validation_manifest_id: tuple
    # Declare held_out_test_used as bool for this data structure.
    held_out_test_used: bool
    # Declare decision_status as str for this data structure.
    decision_status: str
    # Declare provenance as Mapping[str, str] for this data structure.
    provenance: Mapping[str, str]

    # Post init using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    def __post_init__(self):
        # Call object.__setattr__ with the supplied arguments.
        object.__setattr__(self, "provenance", MappingProxyType(dict(self.provenance)))

