"""Immutable controlled-pilot design records for resumed Step 5J.2."""

# Import dataclass from dataclasses for the operations below.
from dataclasses import dataclass
# Import MappingProxyType from types for the operations below.
from types import MappingProxyType
# Import Any, Mapping, Optional, Tuple from typing for the operations below.
from typing import Any, Mapping, Optional, Tuple


# Freeze using the inputs and processing steps below.
# Input value: the supplied value.
# Output: the result of MappingProxyType(a dictionary built from value).
def _freeze(value):
    # Return the result of MappingProxyType(a dictionary built from value) to the caller.
    return MappingProxyType(dict(value))


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define NegotiationScenarioCatalogueManifest to group the state and operations declared below.
# Declared fields: catalogue_id, network_identity, intersection_geometry_identity, scenario_specification_ids,
# calibration_record_ids, regulatory_profile, perception_configuration_identity, intention_model_identity,....
# Construction and attribute behavior follow the declared decorators and base classes.
class NegotiationScenarioCatalogueManifest:
    # Declare catalogue_id as tuple for this data structure.
    catalogue_id: tuple
    # Declare network_identity as str for this data structure.
    network_identity: str
    # Declare intersection_geometry_identity as tuple for this data structure.
    intersection_geometry_identity: tuple
    # Declare scenario_specification_ids as Tuple[tuple, ...] for this data structure.
    scenario_specification_ids: Tuple[tuple, ...]
    # Declare calibration_record_ids as Tuple[tuple, ...] for this data structure.
    calibration_record_ids: Tuple[tuple, ...]
    # Declare regulatory_profile as str for this data structure.
    regulatory_profile: str
    # Declare perception_configuration_identity as str for this data structure.
    perception_configuration_identity: str
    # Declare intention_model_identity as str for this data structure.
    intention_model_identity: str
    # Declare scenario_generator_version as str for this data structure.
    scenario_generator_version: str
    # Declare scenario_count as int for this data structure.
    scenario_count: int
    # Declare catalogue_generation_provenance as Mapping[str, str] for this data structure.
    catalogue_generation_provenance: Mapping[str, str]
    # Declare frozen_status as str for this data structure.
    frozen_status: str

    # Post init using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    def __post_init__(self):
        # Call object.__setattr__ with the supplied arguments.
        object.__setattr__(self, "catalogue_generation_provenance",
                           # Supply the result of _freeze(self.catalogue_generation_provenance) to
                           # object.__setattr__.
                           _freeze(self.catalogue_generation_provenance))


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define ScenarioCoverageSignature to group the state and operations declared below.
# Declared fields: scenario_id, scenario_family, participant_count, movement_path_ids, approach_ids,
# manoeuvre_labels, regulatory_scc_structure, cyclic_participant_count, scheduled_spawn_step_pattern,
# potential_claim_factors,....
# Construction and attribute behavior follow the declared decorators and base classes.
class ScenarioCoverageSignature:
    # Declare scenario_id as tuple for this data structure.
    scenario_id: tuple
    # Declare scenario_family as str for this data structure.
    scenario_family: str
    # Declare participant_count as int for this data structure.
    participant_count: int
    # Declare movement_path_ids as Tuple[str, ...] for this data structure.
    movement_path_ids: Tuple[str, ...]
    # Declare approach_ids as Tuple[str, ...] for this data structure.
    approach_ids: Tuple[str, ...]
    # Declare manoeuvre_labels as Tuple[str, ...] for this data structure.
    manoeuvre_labels: Tuple[str, ...]
    # Declare regulatory_scc_structure as Tuple[Tuple[str, ...], ...] for this data structure.
    regulatory_scc_structure: Tuple[Tuple[str, ...], ...]
    # Declare cyclic_participant_count as int for this data structure.
    cyclic_participant_count: int
    # Declare scheduled_spawn_step_pattern as Tuple[int, ...] for this data structure.
    scheduled_spawn_step_pattern: Tuple[int, ...]
    # Declare potential_claim_factors as int for this data structure.
    potential_claim_factors: int
    # Declare proposer_capable as bool for this data structure.
    proposer_capable: bool
    # Declare responder_capable as bool for this data structure.
    responder_capable: bool
    # Declare multi_action_proposer_capable as bool for this data structure.
    multi_action_proposer_capable: bool
    # Declare multi_action_responder_capable as bool for this data structure.
    multi_action_responder_capable: bool
    # Declare multi_factor_capable as bool for this data structure.
    multi_factor_capable: bool
    # Declare equivalence_group_id as tuple for this data structure.
    equivalence_group_id: tuple


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define CandidateEvidenceRecord to group the state and operations declared below.
# Declared fields: evidence_id, choice_id, candidate_value, candidate_source, primary_source_reference,
# source_context, project_relevance, limitations, candidate_only, selected, provenance.
# Construction and attribute behavior follow the declared decorators and base classes.
class CandidateEvidenceRecord:
    # Declare evidence_id as tuple for this data structure.
    evidence_id: tuple
    # Declare choice_id as str for this data structure.
    choice_id: str
    # Declare candidate_value as Any for this data structure.
    candidate_value: Any
    # Declare candidate_source as str for this data structure.
    candidate_source: str
    # Declare primary_source_reference as str for this data structure.
    primary_source_reference: str
    # Declare source_context as str for this data structure.
    source_context: str
    # Declare project_relevance as str for this data structure.
    project_relevance: str
    # Declare limitations as str for this data structure.
    limitations: str
    # Declare candidate_only as bool for this data structure.
    candidate_only: bool
    # Declare selected as bool for this data structure.
    selected: bool
    # Declare provenance as Mapping[str, str] for this data structure.
    provenance: Mapping[str, str]

    # Post init using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    # Processing: select branches using the stated conditions.
    def __post_init__(self):
        # Call object.__setattr__ with the supplied arguments.
        object.__setattr__(self, "provenance", _freeze(self.provenance))
        # Run this branch when whether self.candidate_value has type a tuple containing int, float and the
        # negation of self.primary_source_reference.
        if isinstance(self.candidate_value, (int, float)) and not self.primary_source_reference:
            # Raise ValueError with the text 'NUMERIC_CANDIDATE_WITHOUT_PROVENANCE' to stop this execution path.
            raise ValueError("NUMERIC_CANDIDATE_WITHOUT_PROVENANCE")
        # Run this branch when the negation of self.candidate_only or self.selected.
        if not self.candidate_only or self.selected:
            # Raise ValueError with the text 'CANDIDATE_MUST_REMAIN_UNSELECTED' to stop this execution path.
            raise ValueError("CANDIDATE_MUST_REMAIN_UNSELECTED")


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define ProvisionalPilotAssignment to group the state and operations declared below.
# Declared fields: choice_id, candidate_value_or_method, candidate_evidence_id, status, project_selected.
# Construction and attribute behavior follow the declared decorators and base classes.
class ProvisionalPilotAssignment:
    # Declare choice_id as str for this data structure.
    choice_id: str
    # Declare candidate_value_or_method as Any for this data structure.
    candidate_value_or_method: Any
    # Declare candidate_evidence_id as tuple for this data structure.
    candidate_evidence_id: tuple
    # Set status to the text 'PROVISIONAL_PILOT_REFERENCE_ONLY'; declare its type as str.
    status: str = "PROVISIONAL_PILOT_REFERENCE_ONLY"
    # Set project_selected to False; declare its type as bool.
    project_selected: bool = False


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define ProvisionalPilotReferenceConfiguration to group the state and operations declared below.
# Declared fields: configuration_id, assignments, status.
# Construction and attribute behavior follow the declared decorators and base classes.
class ProvisionalPilotReferenceConfiguration:
    # Declare configuration_id as tuple for this data structure.
    configuration_id: tuple
    # Declare assignments as Tuple[ProvisionalPilotAssignment, ...] for this data structure.
    assignments: Tuple[ProvisionalPilotAssignment, ...]
    # Set status to the text 'PROVISIONAL_PILOT_REFERENCE_ONLY'; declare its type as str.
    status: str = "PROVISIONAL_PILOT_REFERENCE_ONLY"


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define PilotExperimentPlan to group the state and operations declared below.
# Declared fields: pilot_plan_id, experiment_family, research_question, choice_ids_under_test, candidate_set_ids,
# provisional_reference_configuration_id, training_manifest_id, validation_manifest_id, held_out_manifest_id,....
# Construction and attribute behavior follow the declared decorators and base classes.
class PilotExperimentPlan:
    # Declare pilot_plan_id as tuple for this data structure.
    pilot_plan_id: tuple
    # Declare experiment_family as str for this data structure.
    experiment_family: str
    # Declare research_question as str for this data structure.
    research_question: str
    # Declare choice_ids_under_test as Tuple[str, ...] for this data structure.
    choice_ids_under_test: Tuple[str, ...]
    # Declare candidate_set_ids as Tuple[tuple, ...] for this data structure.
    candidate_set_ids: Tuple[tuple, ...]
    # Declare provisional_reference_configuration_id as tuple for this data structure.
    provisional_reference_configuration_id: tuple
    # Declare training_manifest_id as tuple for this data structure.
    training_manifest_id: tuple
    # Declare validation_manifest_id as tuple for this data structure.
    validation_manifest_id: tuple
    # Declare held_out_manifest_id as tuple for this data structure.
    held_out_manifest_id: tuple
    # Declare seed_manifest_id as tuple for this data structure.
    seed_manifest_id: tuple
    # Declare replication_design_status as str for this data structure.
    replication_design_status: str
    # Declare training_budget_status as str for this data structure.
    training_budget_status: str
    # Declare primary_metric_id as str for this data structure.
    primary_metric_id: str
    # Declare secondary_diagnostic_ids as Tuple[str, ...] for this data structure.
    secondary_diagnostic_ids: Tuple[str, ...]
    # Declare hard_validity_gate_ids as Tuple[str, ...] for this data structure.
    hard_validity_gate_ids: Tuple[str, ...]
    # Declare comparison_method as str for this data structure.
    comparison_method: str
    # Declare selection_rule_id as tuple for this data structure.
    selection_rule_id: tuple
    # Declare manifest_freeze_status as str for this data structure.
    manifest_freeze_status: str
    # Declare execution_status as str for this data structure.
    execution_status: str
    # Declare environment_readiness_status as str for this data structure.
    environment_readiness_status: str
    # Declare provenance as Mapping[str, str] for this data structure.
    provenance: Mapping[str, str]

    # Post init using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    def __post_init__(self):
        # Call object.__setattr__ with the supplied arguments.
        object.__setattr__(self, "provenance", _freeze(self.provenance))


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define ExperimentalDesignFreezeRecord to group the state and operations declared below.
# Declared fields: freeze_id, scenario_catalogue_id, training_manifest_id, validation_manifest_id,
# held_out_manifest_id, candidate_set_ids, pilot_plan_ids, metric_manifest_id, validity_gate_manifest_id,
# selection_rule_id,....
# Construction and attribute behavior follow the declared decorators and base classes.
class ExperimentalDesignFreezeRecord:
    # Declare freeze_id as tuple for this data structure.
    freeze_id: tuple
    # Declare scenario_catalogue_id as tuple for this data structure.
    scenario_catalogue_id: tuple
    # Declare training_manifest_id as tuple for this data structure.
    training_manifest_id: tuple
    # Declare validation_manifest_id as tuple for this data structure.
    validation_manifest_id: tuple
    # Declare held_out_manifest_id as tuple for this data structure.
    held_out_manifest_id: tuple
    # Declare candidate_set_ids as Tuple[tuple, ...] for this data structure.
    candidate_set_ids: Tuple[tuple, ...]
    # Declare pilot_plan_ids as Tuple[tuple, ...] for this data structure.
    pilot_plan_ids: Tuple[tuple, ...]
    # Declare metric_manifest_id as tuple for this data structure.
    metric_manifest_id: tuple
    # Declare validity_gate_manifest_id as tuple for this data structure.
    validity_gate_manifest_id: tuple
    # Declare selection_rule_id as tuple for this data structure.
    selection_rule_id: tuple
    # Declare replication_protocol_id as tuple for this data structure.
    replication_protocol_id: tuple
    # Declare code_revision as str for this data structure.
    code_revision: str
    # Declare freeze_status as str for this data structure.
    freeze_status: str
    # Declare provenance as Mapping[str, str] for this data structure.
    provenance: Mapping[str, str]

    # Post init using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    def __post_init__(self):
        # Call object.__setattr__ with the supplied arguments.
        object.__setattr__(self, "provenance", _freeze(self.provenance))

