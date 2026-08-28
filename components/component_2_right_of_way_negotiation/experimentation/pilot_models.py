"""Immutable controlled-pilot design records for resumed Step 5J.2."""

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping, Optional, Tuple


def _freeze(value):
    return MappingProxyType(dict(value))


@dataclass(frozen=True)
class NegotiationScenarioCatalogueManifest:
    catalogue_id: tuple
    network_identity: str
    intersection_geometry_identity: tuple
    scenario_specification_ids: Tuple[tuple, ...]
    calibration_record_ids: Tuple[tuple, ...]
    regulatory_profile: str
    perception_configuration_identity: str
    intention_model_identity: str
    scenario_generator_version: str
    scenario_count: int
    catalogue_generation_provenance: Mapping[str, str]
    frozen_status: str

    def __post_init__(self):
        object.__setattr__(self, "catalogue_generation_provenance",
                           _freeze(self.catalogue_generation_provenance))


@dataclass(frozen=True)
class ScenarioCoverageSignature:
    scenario_id: tuple
    scenario_family: str
    participant_count: int
    movement_path_ids: Tuple[str, ...]
    approach_ids: Tuple[str, ...]
    manoeuvre_labels: Tuple[str, ...]
    regulatory_scc_structure: Tuple[Tuple[str, ...], ...]
    cyclic_participant_count: int
    scheduled_spawn_step_pattern: Tuple[int, ...]
    potential_claim_factors: int
    proposer_capable: bool
    responder_capable: bool
    multi_action_proposer_capable: bool
    multi_action_responder_capable: bool
    multi_factor_capable: bool
    equivalence_group_id: tuple


@dataclass(frozen=True)
class CandidateEvidenceRecord:
    evidence_id: tuple
    choice_id: str
    candidate_value: Any
    candidate_source: str
    primary_source_reference: str
    source_context: str
    project_relevance: str
    limitations: str
    candidate_only: bool
    selected: bool
    provenance: Mapping[str, str]

    def __post_init__(self):
        object.__setattr__(self, "provenance", _freeze(self.provenance))
        if isinstance(self.candidate_value, (int, float)) and not self.primary_source_reference:
            raise ValueError("NUMERIC_CANDIDATE_WITHOUT_PROVENANCE")
        if not self.candidate_only or self.selected:
            raise ValueError("CANDIDATE_MUST_REMAIN_UNSELECTED")


@dataclass(frozen=True)
class ProvisionalPilotAssignment:
    choice_id: str
    candidate_value_or_method: Any
    candidate_evidence_id: tuple
    status: str = "PROVISIONAL_PILOT_REFERENCE_ONLY"
    project_selected: bool = False


@dataclass(frozen=True)
class ProvisionalPilotReferenceConfiguration:
    configuration_id: tuple
    assignments: Tuple[ProvisionalPilotAssignment, ...]
    status: str = "PROVISIONAL_PILOT_REFERENCE_ONLY"


@dataclass(frozen=True)
class PilotExperimentPlan:
    pilot_plan_id: tuple
    experiment_family: str
    research_question: str
    choice_ids_under_test: Tuple[str, ...]
    candidate_set_ids: Tuple[tuple, ...]
    provisional_reference_configuration_id: tuple
    training_manifest_id: tuple
    validation_manifest_id: tuple
    held_out_manifest_id: tuple
    seed_manifest_id: tuple
    replication_design_status: str
    training_budget_status: str
    primary_metric_id: str
    secondary_diagnostic_ids: Tuple[str, ...]
    hard_validity_gate_ids: Tuple[str, ...]
    comparison_method: str
    selection_rule_id: tuple
    manifest_freeze_status: str
    execution_status: str
    environment_readiness_status: str
    provenance: Mapping[str, str]

    def __post_init__(self):
        object.__setattr__(self, "provenance", _freeze(self.provenance))


@dataclass(frozen=True)
class ExperimentalDesignFreezeRecord:
    freeze_id: tuple
    scenario_catalogue_id: tuple
    training_manifest_id: tuple
    validation_manifest_id: tuple
    held_out_manifest_id: tuple
    candidate_set_ids: Tuple[tuple, ...]
    pilot_plan_ids: Tuple[tuple, ...]
    metric_manifest_id: tuple
    validity_gate_manifest_id: tuple
    selection_rule_id: tuple
    replication_protocol_id: tuple
    code_revision: str
    freeze_status: str
    provenance: Mapping[str, str]

    def __post_init__(self):
        object.__setattr__(self, "provenance", _freeze(self.provenance))

