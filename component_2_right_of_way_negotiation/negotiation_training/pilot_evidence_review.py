"""Analysis-only Step 5J.3C.2 review of existing closed-loop evidence."""

from collections.abc import Mapping
from dataclasses import dataclass, fields
import hashlib
import json
from pathlib import Path
from types import MappingProxyType
from typing import Tuple

from experimentation import ScenarioRole, build_design


SOURCE_PATH = Path("results/mappo_closed_loop_pilot_evidence.json")
REVIEW_PATH = Path("results/mappo_pilot_evidence_review.json")


@dataclass(frozen=True)
class ExtendedMAPPOEvidenceAcquisitionDesign:
    design_id: Tuple[str, str]
    source_pilot_evidence_id: Tuple[str, str]
    frozen_experimental_design_id: tuple
    training_manifest_id: tuple
    validation_manifest_id: tuple
    held_out_manifest_id: tuple
    current_replication_evidence_status: str
    current_training_budget_evidence_status: str
    replication_extension_rule: dict
    training_curve_extension_rule: dict
    measurement_schedule: tuple
    selection_data_boundary: dict
    held_out_sealed: bool
    performance_seed_selection_forbidden: bool
    final_counts_selected: bool
    provenance: dict

    def __post_init__(self):
        for name in ("replication_extension_rule",
                     "training_curve_extension_rule",
                     "selection_data_boundary", "provenance"):
            object.__setattr__(self, name,
                               MappingProxyType(dict(getattr(self, name))))


def _jsonable(value):
    if isinstance(value, Mapping):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    return value


def _dataclass_payload(value):
    return {field.name: _jsonable(getattr(value, field.name))
            for field in fields(value)}


def _digest(value):
    encoded = json.dumps(_jsonable(value), sort_keys=True,
                         separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def load_and_validate_pilot_evidence(path=SOURCE_PATH):
    evidence = json.loads(Path(path).read_text(encoding="utf-8"))
    required = {
        "status": "CLOSED_LOOP_PROGRESS_AND_VARIANCE_PROBE_COMPLETE",
        "replication_count": 2,
        "validation_runs": 0,
        "held_out_runs": 0,
        "collisions": 0,
        "blocked_zone_violations": 0,
        "replication_probe_reason": "MINIMUM_SAMPLE_VARIANCE_PROBE",
        "final_training_budget_selected": False,
        "final_replication_count_selected": False,
    }
    for field, expected in required.items():
        if evidence.get(field) != expected:
            raise ValueError(f"INVALID_PILOT_EVIDENCE_{field.upper()}")
    if len(evidence.get("replications", ())) != 2:
        raise ValueError("EXACTLY_TWO_PILOT_REPLICATIONS_REQUIRED")
    if any(item.get("seed_selected_by_performance") is not False
           for item in evidence["replications"]):
        raise ValueError("PERFORMANCE_SELECTED_PILOT_SEED_FORBIDDEN")
    return evidence


def build_extended_evidence_acquisition_design(evidence, design):
    source_id = ("MAPPO_CLOSED_LOOP_PILOT_EVIDENCE_V1", _digest(evidence))
    manifests = design["manifests"]
    identity_fields = (
        source_id, design["freeze"].freeze_id,
        manifests[ScenarioRole.TRAINING].manifest_id,
        manifests[ScenarioRole.VALIDATION].manifest_id,
        manifests[ScenarioRole.HELD_OUT_TEST].manifest_id,
        "CANONICAL_CONTIGUOUS_REPLICATION_STREAM_FROM_INDEX_2",
        "SEQUENTIAL_CURRENT_POLICY_ON_POLICY_MANIFEST_UPDATES")
    return ExtendedMAPPOEvidenceAcquisitionDesign(
        design_id=("EXTENDED_MAPPO_EVIDENCE_ACQUISITION_DESIGN_V1",
                   _digest(identity_fields)),
        source_pilot_evidence_id=source_id,
        frozen_experimental_design_id=design["freeze"].freeze_id,
        training_manifest_id=manifests[ScenarioRole.TRAINING].manifest_id,
        validation_manifest_id=manifests[ScenarioRole.VALIDATION].manifest_id,
        held_out_manifest_id=manifests[ScenarioRole.HELD_OUT_TEST].manifest_id,
        current_replication_evidence_status=
            "INSUFFICIENT_MINIMUM_TWO_RUN_VARIANCE_PROBE",
        current_training_budget_evidence_status=
            "INSUFFICIENT_SINGLE_UPDATE_INTERVAL",
        replication_extension_rule={
            "stream": "CANONICAL_DETERMINISTIC_REPLICATION_STREAM",
            "next_index": 2,
            "order": "2,3,4,..._WITHOUT_SKIPPING",
            "termination_count": "NOT_YET_SELECTED",
            "performance_based_replacement": False},
        training_curve_extension_rule={
            "sequence": "STATE_K_COLLECTION_THEN_UPDATE_K_PLUS_1",
            "collection": "FULL_FROZEN_TRAINING_MANIFEST",
            "update_data": "IMMEDIATELY_PRECEDING_CURRENT_POLICY_ON_POLICY_DATA_ONLY",
            "stale_rollout_reuse": False,
            "final_update_count": "NOT_YET_SELECTED",
            "convergence_rule": "STATISTICAL_SELECTION_RULE_REQUIRES_PREDECLARATION"},
        measurement_schedule=(
            "policy_identity", "critic_identity", "training_team_travel_time",
            "per_scenario_travel_times", "physical_executable_outcomes",
            "coordination_cycles", "physical_cycles", "action_frequencies",
            "completed_vehicles", "collision_count",
            "blocked_zone_violations", "policy_factor_count", "sumo_steps",
            "wall_clock_runtime"),
        selection_data_boundary={
            "configuration_selection_roles": ("TRAINING", "VALIDATION"),
            "training_budget_probe_role": "TRAINING_ONLY",
            "held_out_role": "SEALED_FINAL_EVALUATION",
            "new_scenario_identities_added": False,
            "future_external_stress_test_classification":
                "POST_SELECTION_EXTERNAL_GENERALIZATION_EXPERIMENT"},
        held_out_sealed=True,
        performance_seed_selection_forbidden=True,
        final_counts_selected=False,
        provenance={
            "checkpoint": "STEP_5J_3C_2",
            "derivation": "EXISTING_STEP_5J_3C_1_EVIDENCE_ONLY",
            "sumo_runs": 0, "optimizer_invocations": 0,
            "backward_calls": 0, "parameter_updates": 0})


def build_pilot_evidence_review(source_path=SOURCE_PATH,
                                output_path=REVIEW_PATH):
    evidence = load_and_validate_pilot_evidence(source_path)
    design = build_design()
    replications = evidence["replications"]
    deltas = [item["delta_team_travel_time_seconds"]
              for item in replications]
    variance = evidence["variance_evidence"]["delta"]
    extended = build_extended_evidence_acquisition_design(evidence, design)
    training_manifest = design["manifests"][ScenarioRole.TRAINING]
    result = {
        "checkpoint": "STEP_5J_3C_2",
        "status": "PILOT_EVIDENCE_REVIEW_COMPLETE",
        "source_pilot_identity": list(extended.source_pilot_evidence_id),
        "source_pilot_path": str(source_path),
        "pilot_statistics": {
            "replications_observed": 2,
            "replication_indices_preserved": [item["replication_index"]
                                                for item in replications],
            "replications_discarded": 0,
            "ppo_update_intervals_per_replication": 1,
            "unique_training_scenarios": len(training_manifest.scenario_ids),
            "training_manifest_passes": evidence["total_training_manifest_collections"],
            "training_exposure_episodes": evidence["total_training_scenario_executions"],
            "delta_values": deltas,
            "delta_sample_mean": variance["sample_mean"],
            "delta_sample_variance_n_minus_1": variance["sample_variance_n_minus_1"],
            "delta_sample_standard_deviation": variance["sample_standard_deviation"],
            "validation_runs": 0, "held_out_runs": 0,
            "collisions": 0, "blocked_zone_violations": 0},
        "training_budget_sufficiency_assessment": {
            "status": "INSUFFICIENT_SINGLE_UPDATE_INTERVAL",
            "final_budget_justified": False,
            "final_training_budget_selected": False,
            "reason": "ONLY_ONE_UPDATE_INTERVAL_OBSERVED",
            "established": "PARAMETER_LEARNING_CAN_ALTER_PHYSICAL_TRAFFIC_OUTCOME",
            "not_established": ["LEARNING_CURVE_SHAPE", "PLATEAU",
                                "CONVERGENCE", "OVER_TRAINING_BEHAVIOR",
                                "LATER_DEGRADATION", "BEST_TRAINING_DURATION"]},
        "replication_sufficiency_assessment": {
            "status": "INSUFFICIENT_MINIMUM_TWO_RUN_VARIANCE_PROBE",
            "final_replication_count_justified": False,
            "final_replication_count_selected": False,
            "reason": "TWO_RUN_MINIMUM_VARIANCE_PROBE_ONLY",
            "observations_called_outliers": 0,
            "interpretation": "TWO_OBSERVATIONS_PERMIT_A_FIRST_SAMPLE_VARIANCE_CALCULATION_BUT_POORLY_CHARACTERIZE_THE_VARIANCE"},
        "scenario_design_assessment": {
            "new_unique_training_scenarios_required_now": False,
            "repeated_training_manifest_exposure_required": True,
            "partitions_modified": False,
            "terminology": {
                "UNIQUE_TRAINING_SCENARIOS": "NUMBER_OF_FROZEN_TRAINING_SCENARIO_IDENTITIES",
                "TRAINING_MANIFEST_PASS": "ONE_EXECUTION_OF_EVERY_FROZEN_TRAINING_SCENARIO",
                "PPO_UPDATE_CYCLE": "ONE_ON_POLICY_MANIFEST_COLLECTION_FOLLOWED_BY_CONFIGURED_PPO_OPTIMIZATION",
                "TRAINING_EXPOSURE": "SCENARIO_EPISODES_GENERATED_ACROSS_MANIFEST_PASSES_AND_REPLICATIONS"}},
        "compute_cost_evidence": {
            "total_wall_clock_seconds": evidence["total_wall_clock_runtime_seconds"],
            "wall_clock_seconds_per_training_manifest_collection":
                evidence["total_wall_clock_runtime_seconds"] /
                evidence["total_training_manifest_collections"],
            "complete_replication_wall_clock_seconds": [
                item["wall_clock_measurements"]["total_replication_seconds"]
                for item in replications],
            "total_ppo_update_runtime_seconds": evidence["total_update_runtime_seconds"],
            "ppo_update_runtime_seconds": [item["update_runtime_seconds"]
                                            for item in replications],
            "sumo_steps_per_training_manifest_collection":
                evidence["total_sumo_steps"] /
                evidence["total_training_manifest_collections"],
            "runtime_threshold_imposed": False},
        "extended_evidence_acquisition_design": _dataclass_payload(extended),
        "remaining_methodological_blockers": [
            "TRAINING_BUDGET_SELECTION_CRITERION_REQUIRES_PREDECLARATION",
            "REPLICATION_COUNT_ADEQUACY_CRITERION_REQUIRES_PREDECLARATION",
            "CANDIDATE_COMPARISON_STATISTIC_REQUIRES_PREDECLARATION",
            "TIE_RULE_REQUIRES_PREDECLARATION",
            "CHECKPOINT_MODEL_SELECTION_RULE_REQUIRES_PREDECLARATION",
            "STATISTICAL_SELECTION_RULE_REQUIRES_PREDECLARATION"],
        "candidate_experiments_started": False,
        "arbitrary_convergence_thresholds": 0,
        "final_counts_selected": False,
        "sumo_invocations": 0, "optimizer_invocations": 0,
        "backward_calls": 0, "model_parameter_updates": 0,
        "training_budget_evidence": "INSUFFICIENT_SINGLE_UPDATE_INTERVAL",
        "replication_evidence": "INSUFFICIENT_MINIMUM_TWO_RUN_VARIANCE_PROBE",
        "next_readiness": "READY_TO_DEFINE_EXTENDED_LEARNING_EVIDENCE_PROTOCOL",
        "next_checkpoint": "STEP_5J_3C_2B"}
    Path(output_path).write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result
