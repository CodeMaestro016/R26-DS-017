"""Bounded V2 MAPPO validation selection and matched baseline experiment."""

from dataclasses import dataclass, replace
from datetime import datetime, timezone
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import random
from statistics import mean, median, pstdev
from time import perf_counter

import torch

from experimentation import ScenarioRole, build_design
from negotiation_execution.replay import PhysicalReplayError, _specification
from run_research_demo import select_demo_scenarios

from .adam_contract import build_mechanical_adam_optimization_contract
from .architecture_contract import build_mechanical_pilot_architecture_contract
from .behavior_rollout import serializable
from .controlled_pilot import (
    _current_hashes, _identity, atomic_write_json,
    collect_controlled_training_pass,
)
from .environment import CoupledNegotiationTrainingEnvironment
from .mappo_provider import (
    MAPPOBehaviorActionProvider, build_mechanical_mappo_behavior_policy_bundle,
)
from .optimizer_contract import build_mechanical_pilot_configuration_audit
from .ppo_trainer import MechanicalMAPPOTrainer
from .rollout import MAPPOBehaviorRolloutIdentity, parameter_hash


OUTPUT_ROOT = Path("results/final_mappo_selection_v2")
PROTOCOL_ID = "FINAL_MAPPO_SELECTION_PROTOCOL_V2"
REPLICATION_COUNT = 3
UPDATE_HORIZON = 2
CANDIDATE_EPOCHS = {"E5": 5, "E10": 10, "E15": 15}
REFERENCE_CANDIDATE = "E5"
BOOTSTRAP_SEED = 260826
BOOTSTRAP_RESAMPLES = 2000


def _hash(value):
    return hashlib.sha256(json.dumps(
        serializable(value), sort_keys=True, separators=(",", ":")
    ).encode()).hexdigest()


def file_sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def atomic_torch_save(payload, path):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    torch.save(payload, temporary); os.replace(temporary, path)


@dataclass(frozen=True)
class FinalMAPPOCandidateConfiguration:
    candidate_id: str
    ppo_update_epochs: int
    learning_rate: float
    ppo_clip_epsilon: float
    gnn_hidden_dimension: int
    gnn_message_passing_layers: int
    gnn_training_mode: str
    parameter_sharing_strategy: str
    factor_aggregation: str
    optimizer_family: str = "ADAM"

    @property
    def configuration_hash(self):
        return _hash(self.__dict__)


def candidate_configurations(design=None):
    design = design or build_design()
    architecture = build_mechanical_pilot_architecture_contract()
    optimization = build_mechanical_adam_optimization_contract()
    assignments = {x.choice_id: x.candidate_value_or_method
                   for x in design["provisional"].assignments}
    return tuple(FinalMAPPOCandidateConfiguration(
        candidate_id, epochs, optimization.learning_rate,
        assignments["ppo_clip_epsilon"], architecture.gnn_hidden_dimension,
        architecture.gnn_message_passing_layers, architecture.gnn_training_mode,
        architecture.parameter_sharing_strategy,
        assignments["multi_policy_factor_aggregation"],
        optimization.optimizer_family,
    ) for candidate_id, epochs in CANDIDATE_EPOCHS.items())


def candidate_runtime_audit(candidate):
    """Copy the historical audit and override only PPO update epochs."""
    audit = build_mechanical_pilot_configuration_audit()
    choices = tuple(
        replace(item, value=candidate.ppo_update_epochs,
                classification="FINAL_SELECTION_V2_CONTROLLED_OVERRIDE",
                provenance={**dict(item.provenance),
                            "protocol_id": PROTOCOL_ID,
                            "only_controlled_override": True})
        if item.choice_id == "ppo_update_epochs" else item
        for item in audit.runtime_choices
    )
    return replace(audit, runtime_choices=choices,
                   audit_id=(PROTOCOL_ID, candidate.candidate_id,
                             candidate.configuration_hash))


def _manifest_payload(manifest):
    return {"manifest_id": serializable(manifest.manifest_id),
            "role": manifest.purpose.value,
            "scenario_ids": serializable(manifest.scenario_ids),
            "scenario_count": len(manifest.scenario_ids)}


def build_protocol():
    design = build_design()
    manifests = design["manifests"]
    role_sets = {role: set(manifests[role].scenario_ids) for role in ScenarioRole}
    if any(role_sets[a] & role_sets[b] for i, a in enumerate(ScenarioRole)
           for b in tuple(ScenarioRole)[i + 1:]):
        raise ValueError("SCENARIO_ROLE_IDENTITY_LEAKAGE")
    if any(len(role_sets[role]) != 36 for role in ScenarioRole):
        raise ValueError("FINAL_SELECTION_REQUIRES_36_SCENARIOS_PER_ROLE")
    candidates = candidate_configurations(design)
    fixed = {key: getattr(candidates[0], key) for key in (
        "learning_rate", "ppo_clip_epsilon", "gnn_hidden_dimension",
        "gnn_message_passing_layers", "gnn_training_mode",
        "parameter_sharing_strategy", "factor_aggregation", "optimizer_family")}
    protocol = {
        "protocol_id": PROTOCOL_ID, "version": 2,
        "status": "FROZEN_BEFORE_FINAL_SELECTION_EXECUTION",
        "study_type": "CONTROLLED_ONE_FACTOR_ABLATION_MODEL_SELECTION",
        "varied_factor": "ppo_update_epochs",
        "candidate_ids": list(CANDIDATE_EPOCHS),
        "candidate_values": CANDIDATE_EPOCHS,
        "fixed_configuration": fixed,
        "replication_count_n": REPLICATION_COUNT,
        "update_horizon_h": UPDATE_HORIZON,
        "resource_statement": (
            "N=3 and H=2 are predeclared project-resource choices for this "
            "bounded model-selection experiment. They are not claimed as "
            "statistically optimal replication or training-budget values."),
        "replication_identities": [
            ["FINAL_MAPPO_CANONICAL_REPLICATION_V2", index]
            for index in range(REPLICATION_COUNT)],
        "adaptive_early_stopping": False,
        "bad_seed_replacement": False,
        "adaptive_horizon_extension": False,
        "primary_metric": "TOTAL_TEAM_TRAVEL_TIME_SECONDS",
        "metric_direction": "LOWER_IS_BETTER",
        "hard_validity_gates": [
            "ZERO_COLLISIONS", "ZERO_BLOCKED_ZONE_VIOLATIONS",
            "HARD_ACTION_MASKS_RESPECTED", "REGULATORY_INVARIANT",
            "PROTOCOL_INVARIANT", "ROUTE_TRUTH_LEAKAGE_ABSENT",
            "FINITE_NETWORK_AND_TRAINING_QUANTITIES"],
        "selection_rule": "LOWEST_MEAN_VALIDATION_TTT_AMONG_ELIGIBLE",
        "exact_tie_rule": "RETAIN_E5_IF_E5_IN_EXACT_TIE",
        "globally_optimal_claim": False,
        "exhaustive_hyperparameter_search": False,
        "selected_best_among_tested_candidates": True,
        "selection_data_role": "VALIDATION",
        "held_out_used_for_selection": False,
        "manifests": {role.value: _manifest_payload(manifests[role])
                      for role in ScenarioRole},
        "bootstrap": {"seed": BOOTSTRAP_SEED,
                      "resamples": BOOTSTRAP_RESAMPLES,
                      "interpretation": "DESCRIPTIVE_PAIRED_UNCERTAINTY_ONLY"},
        "frozen_design_identity": serializable(design["freeze"].freeze_id),
        "historical_demo_checkpoint_selection_eligible": False,
    }
    protocol["protocol_hash"] = _hash(protocol)
    return protocol


def prepare(root=OUTPUT_ROOT):
    root = Path(root); root.mkdir(parents=True, exist_ok=True)
    protocol = build_protocol()
    atomic_write_json(root / "protocol.json", protocol)
    manifest = {"protocol_id": PROTOCOL_ID,
                "candidates": [serializable(x.__dict__) | {
                    "configuration_hash": x.configuration_hash,
                    "only_difference": "ppo_update_epochs"}
                    for x in candidate_configurations()],
                "historical_contracts_mutated": False,
                "historical_checkpoints_eligible": False}
    atomic_write_json(root / "candidate_manifest.json", manifest)
    progress = root / "progress.json"
    if not progress.exists():
        atomic_write_json(progress, {"protocol_id": PROTOCOL_ID,
            "completed_training": [], "completed_validation": [],
            "held_out_consumed": False, "baseline_consumed": False})
    return protocol


def smoke(root=OUTPUT_ROOT):
    protocol = prepare(root)
    payload = {"status": "SMOKE_TEST_ONLY",
               "evidence_classification": ["NOT_MODEL_SELECTION_EVIDENCE",
                    "NOT_VALIDATION_EVIDENCE", "NOT_HELD_OUT_EVIDENCE"],
               "held_out_scenarios_consumed": 0,
               "candidate_contracts": [serializable(x.__dict__)
                                       for x in candidate_configurations()],
               "synthetic_workload_only": True,
               "protocol_hash": protocol["protocol_hash"]}
    atomic_write_json(Path(root) / "smoke" / "smoke_result.json", payload)
    return payload


def _fresh_bundle(design, candidate, replication_index, manifest):
    replication = ("FINAL_MAPPO_CANONICAL_REPLICATION_V2", replication_index)
    identity = MAPPOBehaviorRolloutIdentity(
        _identity(design, build_mechanical_pilot_architecture_contract(),
                  build_mechanical_adam_optimization_contract(), manifest,
                  replication, "FINAL_SELECTION_INITIAL_STATE"),
        design["freeze"].freeze_id,
        build_mechanical_pilot_architecture_contract().contract_id,
        build_mechanical_adam_optimization_contract().contract_id,
        manifest.manifest_id)
    # Candidate is deliberately absent from initialization seed: matched
    # replications differ only in PPO update epochs.
    return build_mechanical_mappo_behavior_policy_bundle(
        component_seed_identity=(replication, "MODEL_INITIALIZATION"),
        behavior_rollout_identity=identity)


def _checkpoint_payload(bundle, candidate, replication_index, states, updates,
                        manifest, runtime):
    hashes = _current_hashes(bundle)
    return {
        "checkpoint_type": "FINAL_MAPPO_SELECTION_V2_CANDIDATE_CHECKPOINT",
        "protocol_id": PROTOCOL_ID, "candidate_id": candidate.candidate_id,
        "candidate_configuration": serializable(candidate.__dict__),
        "candidate_configuration_hash": candidate.configuration_hash,
        "replication_index": replication_index,
        "replication_identity": ["FINAL_MAPPO_CANONICAL_REPLICATION_V2",
                                 replication_index],
        "policy_state_index": UPDATE_HORIZON, "update_count": UPDATE_HORIZON,
        "training_manifest_identity": serializable(manifest.manifest_id),
        "architecture_identity": serializable(
            build_mechanical_pilot_architecture_contract().contract_id),
        "optimizer_identity": serializable(
            build_mechanical_adam_optimization_contract().contract_id),
        "parameter_hashes": hashes,
        "gnn_state_dict": bundle.gnn.state_dict(),
        "proposer_state_dict": bundle.proposer_actor.state_dict(),
        "responder_state_dict": bundle.responder_actor.state_dict(),
        "critic_state_dict": bundle.centralized_critic.state_dict(),
        "objective_history": [x["team_travel_time_seconds"] for x in states],
        "state_metrics": states, "update_diagnostics": updates,
        "sumo_step_count": sum(x["sumo_step_count"] for x in states),
        "collisions": sum(x["collision_count"] for x in states),
        "blocked_zone_violations": sum(
            x["blocked_zone_violation_count"] for x in states),
        "hard_mask_violations": 0, "runtime_seconds": runtime,
        "performance_selected": False, "held_out_consumed": False,
    }


def train(root=OUTPUT_ROOT, resume=False):
    prepare(root); root = Path(root); design = build_design()
    manifest = design["manifests"][ScenarioRole.TRAINING]
    specs = tuple(_specification(design["payload"], sid)
                  for sid in manifest.scenario_ids)
    completed = []
    for candidate in candidate_configurations(design):
        for replication_index in range(REPLICATION_COUNT):
            checkpoint = root / "training" / candidate.candidate_id / (
                f"replication_{replication_index}_state_{UPDATE_HORIZON}.pt")
            if resume and checkpoint.exists():
                completed.append([candidate.candidate_id, replication_index])
                continue
            started = perf_counter()
            bundle = _fresh_bundle(
                design, candidate, replication_index, manifest)
            replication = ("FINAL_MAPPO_CANONICAL_REPLICATION_V2",
                           replication_index)
            states, updates, rollout = [], [], None
            for state_index in range(UPDATE_HORIZON + 1):
                if state_index:
                    updates.append(MechanicalMAPPOTrainer(
                        rollout_payload=rollout, bundle=bundle,
                        output_path=None,
                        configuration=candidate_runtime_audit(candidate)).run())
                metrics, rollout = collect_controlled_training_pass(
                    design=design,
                    architecture=build_mechanical_pilot_architecture_contract(),
                    optimization=build_mechanical_adam_optimization_contract(),
                    manifest=manifest, specifications=specs, bundle=bundle,
                    replication_identity=replication,
                    pass_label=f"{candidate.candidate_id}_STATE_{state_index}",
                    progress_context={"protocol_id": PROTOCOL_ID,
                        "candidate_id": candidate.candidate_id,
                        "replication_index": replication_index,
                        "state_index": state_index},
                    progress_path=root / "progress.json")
                states.append(metrics)
            payload = _checkpoint_payload(
                bundle, candidate, replication_index, states, updates,
                manifest, perf_counter() - started)
            atomic_torch_save(payload, checkpoint)
            completed.append([candidate.candidate_id, replication_index])
            atomic_write_json(root / "progress.json", {
                "protocol_id": PROTOCOL_ID, "completed_training": completed,
                "held_out_consumed": False})
    return {"completed_training": completed}


class FinalSelectionInferenceProvider(MAPPOBehaviorActionProvider):
    selection_rule = "FINAL_SELECTION_V2_INFERENCE_ONLY_MASKED_MAPPO"
    supports_event_driven_renegotiation = True

    def __init__(self, bundle, sampling_seed):
        super().__init__(replace(bundle, centralized_critic=None),
                         sampling_seed=sampling_seed,
                         runtime_critic_enabled=False)
        self.training_operations = 0

    def finalize_episode(self, episode_id, reward):
        return None


class DeterministicNoNegotiationRegulatoryBaseline:
    selection_rule = "KEEP_REGULATORY_CLAIMS_NO_LEARNED_NEGOTIATION_V1"
    uses_mappo_behavior_policy = False
    neural_actor_calls = 0
    reward_used_for_selection = False
    future_outcome_used_for_selection = False
    vehicle_id_priority_rule = False
    allows_unresolved_coordination = True

    def select_joint_actions(self, branches, factor_contexts):
        del factor_contexts
        matches = []
        for branch in branches:
            proposer = branch.proposer_assignment.claim_action_assignments
            responder = branch.responder_assignment.response_action_assignments
            if (all(action == "KEEP_CLAIM" for _, action in proposer)
                    and all(action == "REJECT_RELINQUISHMENT"
                            for _, action in responder)
                    and branch.graph_executable):
                matches.append(branch)
        if len(matches) > 1:
            raise RuntimeError("BASELINE_NONUNIQUE_KEEP_REGULATORY_BRANCH")
        return matches[0] if matches else None


def _load_bundle(checkpoint_path):
    payload = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    bundle = build_mechanical_mappo_behavior_policy_bundle(
        component_seed_identity=("FINAL_SELECTION_V2_RECONSTRUCTION",))
    bundle.gnn.load_state_dict(payload["gnn_state_dict"])
    bundle.proposer_actor.load_state_dict(payload["proposer_state_dict"])
    bundle.responder_actor.load_state_dict(payload["responder_state_dict"])
    bundle.centralized_critic.load_state_dict(payload["critic_state_dict"])
    if _current_hashes(bundle) != payload["parameter_hashes"]:
        raise ValueError("FINAL_SELECTION_CHECKPOINT_HASH_MISMATCH")
    return payload, bundle


def _episode_record(episode, provider_kind):
    return {"scenario_id": serializable(episode.scenario_id),
            "total_team_travel_time_seconds": episode.team_travel_time_seconds,
            "scheduled_vehicles": episode.scheduled_vehicle_count,
            "completed_vehicles": episode.completed_vehicle_count,
            "unresolved_coordination_case": (
                episode.episode_completion_status ==
                "UNRESOLVED_COORDINATION_BASELINE"),
            "episode_completion_status": episode.episode_completion_status,
            "unresolved_coordination_reason": episode.provenance.get(
                "unresolved_coordination_reason"),
            "throughput": (episode.completed_vehicle_count /
                           episode.simulation_duration_seconds
                           if episode.simulation_duration_seconds else 0.0),
            "collisions": episode.collision_count,
            "blocked_zone_violations":
                episode.blocked_zone_entry_violation_count,
            "native_sumo_safety_interventions":
                episode.native_sumo_safety_intervention_count,
            "negotiation_batches": len(episode.joint_decision_batches),
            "learned_proposer_actions": episode.proposer_factor_count
                if provider_kind == "MAPPO" else 0,
            "learned_responder_actions": episode.responder_factor_count
                if provider_kind == "MAPPO" else 0,
            "neural_actor_calls": episode.provenance.get(
                "neural_actor_calls", 0),
            "fabricated_negotiation_branches": episode.provenance.get(
                "fabricated_negotiation_branches", 0),
            "vehicle_id_priority_decisions": episode.provenance.get(
                "vehicle_id_priority_decisions", 0),
            "liveness_metrics": dict(episode.provenance.get(
                "liveness_metrics", {})),
            "liveness_diagnostics": serializable(episode.provenance.get(
                "liveness_diagnostics", ())),
            "hard_validity_gate_results": dict(
                episode.hard_validity_gate_results),
            "hard_mask_violations": 0,
            "regulatory_invariant_violations": 0,
            "protocol_invariant_failures": 0,
            "route_truth_actor_fields_consumed": 0,
            "sumo_steps": episode.sumo_step_count,
            "runtime_seconds": episode.wall_clock_runtime_seconds}


def _evaluate_manifest(checkpoint, manifest, design, role, replication_index):
    _, bundle = _load_bundle(checkpoint)
    provider = FinalSelectionInferenceProvider(
        bundle, sampling_seed=int.from_bytes(hashlib.sha256(repr((
            PROTOCOL_ID, role.value, replication_index)).encode()).digest()[:8],
            "big") % (2 ** 31))
    records = []
    for sid in manifest.scenario_ids:
        episode = CoupledNegotiationTrainingEnvironment(provider).run_episode(
            _specification(design["payload"], sid), manifest.manifest_id)
        records.append(_episode_record(episode, "MAPPO"))
    return records


def _summary(records):
    values = [x["total_team_travel_time_seconds"] for x in records]
    return {"scenario_execution_count": len(records), "total": sum(values),
            "mean": mean(values), "median": median(values),
            "standard_deviation": pstdev(values), "minimum": min(values),
            "maximum": max(values),
            "completed_vehicles": sum(x["completed_vehicles"] for x in records),
            "collisions": sum(x["collisions"] for x in records),
            "blocked_zone_violations": sum(
                x["blocked_zone_violations"] for x in records),
            "native_sumo_safety_interventions": sum(
                x["native_sumo_safety_interventions"] for x in records),
            "learned_proposer_actions": sum(
                x["learned_proposer_actions"] for x in records),
            "learned_responder_actions": sum(
                x["learned_responder_actions"] for x in records),
            "unresolved_coordination_cases": sum(
                bool(x["unresolved_coordination_case"]) for x in records),
            "runtime_seconds": sum(x["runtime_seconds"] for x in records)}


def _hard_safety_failure_record(scenario_id, error):
    if error.code not in {
            "BLOCKED_VEHICLE_ENTERED_CONFLICT_ZONE",
            "PHYSICAL_CAUSAL_BRANCH_COLLISION_OBSERVED"}:
        raise error
    evidence = serializable(error.evidence)
    provenance = {"exception_type": type(error).__name__,
                  "failure_message": str(error), "raw_evidence": evidence}
    if error.code == "BLOCKED_VEHICLE_ENTERED_CONFLICT_ZONE" and evidence:
        provenance.update({"vehicle_id": evidence[0],
                           "conflict_zone_id": evidence[1],
                           "simulation_time": evidence[2]})
    elif error.code == "PHYSICAL_CAUSAL_BRANCH_COLLISION_OBSERVED" and evidence:
        provenance.update({"simulation_time": evidence[0],
                           "vehicle_ids": evidence[1]})
    return {"scenario_id": serializable(scenario_id),
            "status": "HARD_SAFETY_FAILURE",
            "hard_validity_eligible": False,
            "safety_failure_type": error.code,
            "safety_failure_provenance": provenance,
            "total_team_travel_time_seconds": None}


def _baseline_summary(records):
    completed = [x for x in records if x.get("status") !=
                 "HARD_SAFETY_FAILURE"]
    failures = [x for x in records if x.get("status") ==
                "HARD_SAFETY_FAILURE"]
    result = (_summary(completed) if completed else {
        "scenario_execution_count": 0, "total": None, "mean": None,
        "median": None, "standard_deviation": None, "minimum": None,
        "maximum": None, "completed_vehicles": 0, "collisions": 0,
        "blocked_zone_violations": 0,
        "native_sumo_safety_interventions": 0,
        "learned_proposer_actions": 0, "learned_responder_actions": 0,
        "unresolved_coordination_cases": 0, "runtime_seconds": 0})
    result.update({
        "scenario_count": len(records),
        "completed_episode_count": len(completed),
        "hard_safety_failure_count": len(failures),
        "blocked_zone_failure_count": sum(
            x["safety_failure_type"] ==
            "BLOCKED_VEHICLE_ENTERED_CONFLICT_ZONE" for x in failures),
        "collision_failure_count": sum(
            x["safety_failure_type"] ==
            "PHYSICAL_CAUSAL_BRANCH_COLLISION_OBSERVED" for x in failures),
        "unresolved_coordination_case_count": sum(
            bool(x.get("unresolved_coordination_case")) for x in completed),
        "safety_eligible": not failures,
        "hard_safety_failure_scenario_ids": [
            x["scenario_id"] for x in failures],
        "travel_time_scope": (
            "COMPLETED_BASELINE_EPISODES_ONLY" if failures else
            "ALL_BASELINE_EPISODES")})
    return result


def _eligible(records):
    return (all(x["collisions"] == 0 and x["blocked_zone_violations"] == 0
                and x["hard_mask_violations"] == 0
                and x["regulatory_invariant_violations"] == 0
                and x["protocol_invariant_failures"] == 0
                and x["route_truth_actor_fields_consumed"] == 0
                and all(x["hard_validity_gate_results"].values())
                and math.isfinite(x["total_team_travel_time_seconds"])
                for x in records))


def validate(root=OUTPUT_ROOT, resume=False):
    prepare(root); root = Path(root); design = build_design()
    manifest = design["manifests"][ScenarioRole.VALIDATION]
    candidates = {}
    for candidate in candidate_configurations(design):
        replications = []
        for replication_index in range(REPLICATION_COUNT):
            checkpoint = root / "training" / candidate.candidate_id / (
                f"replication_{replication_index}_state_{UPDATE_HORIZON}.pt")
            if not checkpoint.exists():
                raise FileNotFoundError(f"Missing training checkpoint: {checkpoint}")
            output = root / "validation" / candidate.candidate_id / (
                f"replication_{replication_index}.json")
            if resume and output.exists():
                record = json.loads(output.read_text(encoding="utf-8"))
            else:
                scenarios = _evaluate_manifest(
                    checkpoint, manifest, design, ScenarioRole.VALIDATION,
                    replication_index)
                record = {"candidate_id": candidate.candidate_id,
                    "replication_index": replication_index,
                    "data_role": "VALIDATION", "training_operations": 0,
                    "scenario_results": scenarios, "summary": _summary(scenarios)}
                atomic_write_json(output, record)
            replications.append(record)
        all_records = [x for rep in replications for x in rep["scenario_results"]]
        replication_totals = [
            item["summary"]["total"] for item in replications
        ]
        candidate_summary = _summary(all_records)
        candidate_summary.update({
            "replication_total_team_travel_time_seconds": replication_totals,
            "mean_replication_total_team_travel_time_seconds": mean(
                replication_totals),
            "median_replication_total_team_travel_time_seconds": median(
                replication_totals),
            "replication_total_standard_deviation": pstdev(replication_totals),
            "replication_total_minimum": min(replication_totals),
            "replication_total_maximum": max(replication_totals),
        })
        candidates[candidate.candidate_id] = {
            "candidate_id": candidate.candidate_id,
            "configuration_hash": candidate.configuration_hash,
            "replications": replications, "summary": candidate_summary,
            "eligible": _eligible(all_records),
            "hard_gate_result": "ELIGIBLE" if _eligible(all_records)
                                else "INELIGIBLE"}
    payload = {"protocol_id": PROTOCOL_ID, "data_role": "VALIDATION",
               "held_out_consumed": False, "candidates": candidates,
               "paired_descriptive_uncertainty":
                   _paired_uncertainty(candidates)}
    atomic_write_json(root / "comparison" /
                      "candidate_validation_summary.json", payload)
    _write_candidate_csv(root, candidates)
    return payload


def _write_candidate_csv(root, candidates):
    path = Path(root) / "comparison" / "candidate_validation_summary.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".csv.tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle); writer.writerow([
            "candidate", "mean_validation_ttt", "median", "sd", "collisions",
            "blocked_zone_violations", "eligible"])
        for key, item in candidates.items():
            s = item["summary"]; writer.writerow([key,
                s["mean_replication_total_team_travel_time_seconds"],
                s["median_replication_total_team_travel_time_seconds"],
                s["replication_total_standard_deviation"], s["collisions"],
                s["blocked_zone_violations"], item["eligible"]])
    os.replace(temporary, path)


def _paired_uncertainty(candidates):
    """Deterministic paired bootstrap over matched replication totals."""
    reference = candidates[REFERENCE_CANDIDATE]["summary"][
        "replication_total_team_travel_time_seconds"]
    result = {}
    for candidate_id, item in candidates.items():
        if candidate_id == REFERENCE_CANDIDATE:
            continue
        values = item["summary"][
            "replication_total_team_travel_time_seconds"]
        differences = [a - b for a, b in zip(values, reference)]
        generator = random.Random((BOOTSTRAP_SEED * 1000) +
                                  CANDIDATE_EPOCHS[candidate_id])
        boot = sorted(mean([differences[generator.randrange(len(differences))]
                            for _ in differences])
                      for _ in range(BOOTSTRAP_RESAMPLES))
        lower = boot[int(0.025 * (len(boot) - 1))]
        upper = boot[int(0.975 * (len(boot) - 1))]
        result[f"{candidate_id}_minus_{REFERENCE_CANDIDATE}"] = {
            "matched_replication_differences_seconds": differences,
            "paired_mean_difference_seconds": mean(differences),
            "paired_median_difference_seconds": median(differences),
            "descriptive_bootstrap_95_percent_interval": [lower, upper],
            "bootstrap_seed": BOOTSTRAP_SEED,
            "bootstrap_resamples": BOOTSTRAP_RESAMPLES,
            "statistical_significance_claim": False,
        }
    return result


def select(root=OUTPUT_ROOT):
    root = Path(root)
    frozen_path = root / "selected_configuration.json"
    if frozen_path.exists():
        frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
        if frozen.get("status") != "SELECTION_FROZEN":
            raise ValueError("INVALID_EXISTING_SELECTION_ARTIFACT")
        return frozen
    source = root / "comparison" / "candidate_validation_summary.json"
    if not source.exists():
        raise FileNotFoundError("Validation must finish before selection")
    validation = json.loads(source.read_text(encoding="utf-8"))
    if validation.get("data_role") != "VALIDATION" or validation.get(
            "held_out_consumed") is not False:
        raise ValueError("SELECTION_DATA_BOUNDARY_VIOLATION")
    eligible = {key: value for key, value in validation["candidates"].items()
                if value["eligible"]}
    if not eligible:
        raise RuntimeError("NO_ELIGIBLE_FINAL_MAPPO_CANDIDATE")
    def selection_mean(item):
        return item["summary"].get(
            "mean_replication_total_team_travel_time_seconds",
            item["summary"]["mean"])
    best_mean = min(selection_mean(x) for x in eligible.values())
    tied = sorted(key for key, x in eligible.items()
                  if selection_mean(x) == best_mean)
    selected = REFERENCE_CANDIDATE if REFERENCE_CANDIDATE in tied else tied[0]
    candidate = next(x for x in candidate_configurations()
                     if x.candidate_id == selected)
    checkpoint = root / "training" / selected / "replication_0_state_2.pt"
    selected_policy = root / "selected_policy.pt"
    temporary = selected_policy.with_suffix(".pt.tmp")
    shutil.copyfile(checkpoint, temporary); os.replace(temporary, selected_policy)
    payload = {"protocol_id": PROTOCOL_ID, "status": "SELECTION_FROZEN",
        "selected_candidate_id": selected,
        "selection_reason": "LOWEST_MEAN_VALIDATION_TTT_AMONG_ELIGIBLE",
        "selection_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "candidate_configuration": serializable(candidate.__dict__),
        "candidate_configuration_hash": candidate.configuration_hash,
        "training_checkpoint_hashes": {
            str(i): file_sha256(root / "training" / selected /
                f"replication_{i}_state_2.pt") for i in range(REPLICATION_COUNT)},
        "configuration_selected_by_validation": True,
        "selection_data_role": "VALIDATION",
        "held_out_used_for_selection": False,
        "globally_optimal_claim": False,
        "exhaustive_hyperparameter_search": False,
        "selected_best_among_tested_candidates": True,
        "demo_replication_selected_by_performance": False,
        "demo_replication_rule": "CANONICAL_REPLICATION_0",
        "selected_policy_source": str(checkpoint).replace("\\", "/"),
        "selected_policy_sha256": file_sha256(selected_policy),
        "source_checkpoint_sha256": file_sha256(checkpoint)}
    atomic_write_json(frozen_path, payload)
    return payload


def heldout(root=OUTPUT_ROOT, resume=False):
    root = Path(root); selected_path = root / "selected_configuration.json"
    if not selected_path.exists():
        raise RuntimeError("HELD_OUT_LOCKED_SELECTION_NOT_FROZEN")
    selected = json.loads(selected_path.read_text(encoding="utf-8"))
    if selected.get("status") != "SELECTION_FROZEN":
        raise RuntimeError("HELD_OUT_LOCKED_SELECTION_NOT_FROZEN")
    output_path = root / "held_out" / "selected_mappo_results.json"
    if resume and output_path.exists():
        return json.loads(output_path.read_text(encoding="utf-8"))
    design = build_design(); manifest = design["manifests"][ScenarioRole.HELD_OUT_TEST]
    replications = []
    for index in range(REPLICATION_COUNT):
        checkpoint = root / "training" / selected["selected_candidate_id"] / (
            f"replication_{index}_state_2.pt")
        scenarios = _evaluate_manifest(
            checkpoint, manifest, design, ScenarioRole.HELD_OUT_TEST, index)
        replications.append({"replication_index": index,
                             "scenario_results": scenarios,
                             "summary": _summary(scenarios)})
    all_records = [x for rep in replications for x in rep["scenario_results"]]
    payload = {"protocol_id": PROTOCOL_ID, "status": "HELD_OUT_COMPLETE",
        "selected_candidate_id": selected["selected_candidate_id"],
        "replications": replications, "summary": _summary(all_records),
        "held_out_used_for_training": False,
        "held_out_used_for_validation_selection": False,
        "held_out_used_for_candidate_selection": False,
        "held_out_used_for_tie_breaking": False,
        "training_operations": 0}
    atomic_write_json(output_path, payload)
    return payload


def baseline(root=OUTPUT_ROOT, resume=False):
    root = Path(root)
    if not (root / "selected_configuration.json").exists():
        raise RuntimeError("BASELINE_REQUIRES_FROZEN_SELECTION")
    output_path = root / "held_out" / "baseline_results.json"
    design = build_design(); manifest = design["manifests"][ScenarioRole.HELD_OUT_TEST]
    if resume and output_path.exists():
        stored = json.loads(output_path.read_text(encoding="utf-8"))
        expected = [serializable(x) for x in manifest.scenario_ids]
        actual = [x.get("scenario_id") for x in
                  stored.get("scenario_results", [])]
        if actual != expected:
            raise RuntimeError("BASELINE_RESUME_MANIFEST_ACCOUNTING_MISMATCH")
        return stored
    provider = DeterministicNoNegotiationRegulatoryBaseline()
    progress = root / "held_out" / "baseline_scenario_records"
    progress.mkdir(parents=True, exist_ok=True)
    records = []
    for index, sid in enumerate(manifest.scenario_ids):
        scenario_path = progress / f"scenario_{index:03d}.json"
        if resume and scenario_path.exists():
            stored = json.loads(scenario_path.read_text(encoding="utf-8"))
            if stored.get("scenario_id") != serializable(sid):
                raise RuntimeError("BASELINE_RESUME_SCENARIO_IDENTITY_MISMATCH")
            records.append(stored)
            continue
        try:
            episode = CoupledNegotiationTrainingEnvironment(provider).run_episode(
                _specification(design["payload"], sid), manifest.manifest_id)
            record = _episode_record(episode, "BASELINE")
        except PhysicalReplayError as error:
            record = _hard_safety_failure_record(sid, error)
        atomic_write_json(scenario_path, record)
        records.append(record)
    payload = {"protocol_id": PROTOCOL_ID,
        "baseline_id": provider.selection_rule,
        "same_physical_environment": True,
        "scenario_manifest_identity": serializable(manifest.manifest_id),
        "neural_actor_calls": 0, "reward_used_for_action_selection": False,
        "future_outcome_used_for_action_selection": False,
        "vehicle_id_priority_rule": False, "scenario_results": records,
        "summary": _baseline_summary(records)}
    atomic_write_json(output_path, payload)
    return payload


def report(root=OUTPUT_ROOT):
    root = Path(root); validation_path = root / "comparison" / "candidate_validation_summary.json"
    selection_path = root / "selected_configuration.json"
    if not validation_path.exists() or not selection_path.exists():
        raise RuntimeError("REPORT_REQUIRES_VALIDATION_AND_FROZEN_SELECTION")
    validation = json.loads(validation_path.read_text(encoding="utf-8"))
    selection = json.loads(selection_path.read_text(encoding="utf-8"))
    mappo_path, baseline_path = (root / "held_out" / "selected_mappo_results.json",
                                 root / "held_out" / "baseline_results.json")
    heldout_ready = mappo_path.exists() and baseline_path.exists()
    comparison = None
    if heldout_ready:
        mappo = json.loads(mappo_path.read_text(encoding="utf-8"))
        base = json.loads(baseline_path.read_text(encoding="utf-8"))
        scenario_results = {}
        for rep in mappo["replications"]:
            for row in rep["scenario_results"]:
                scenario_results.setdefault(
                    json.dumps(row["scenario_id"]), []).append(row)
        rows = []
        for row in base["scenario_results"]:
            key = json.dumps(row["scenario_id"])
            learned_rows = scenario_results[key]
            learned = mean(x["total_team_travel_time_seconds"]
                           for x in learned_rows)
            failed = row.get("status") == "HARD_SAFETY_FAILURE"
            baseline_time = row.get("total_team_travel_time_seconds")
            rows.append({"scenario_id": row["scenario_id"],
                "baseline_status": row.get("status", "COMPLETE"),
                "baseline_hard_validity_eligible": not failed,
                "baseline_safety_failure_type": row.get(
                    "safety_failure_type"),
                "mappo_travel_time": learned,
                "baseline_travel_time": baseline_time,
                "difference_mappo_minus_baseline": (
                    learned - baseline_time if baseline_time is not None
                    else None),
                "mappo_mean_completion": mean(
                    x["completed_vehicles"] for x in learned_rows),
                "baseline_completion": row.get("completed_vehicles"),
                "mappo_collisions": sum(x["collisions"]
                                        for x in learned_rows),
                "baseline_collisions": row.get("collisions"),
                "mappo_blocked_zone_violations": sum(
                    x["blocked_zone_violations"] for x in learned_rows),
                "baseline_blocked_zone_violations": row.get(
                    "blocked_zone_violations"),
                "mappo_native_sumo_safety_interventions": sum(
                    x["native_sumo_safety_interventions"]
                    for x in learned_rows),
                "baseline_native_sumo_safety_interventions": row.get(
                    "native_sumo_safety_interventions"),
                "baseline_unresolved_coordination_case": row.get(
                    "unresolved_coordination_case", False)})
        matched = [x for x in rows if
                   x["difference_mappo_minus_baseline"] is not None]
        difference = (mean(x["difference_mappo_minus_baseline"]
                           for x in matched) if matched else None)
        failure_count = base["summary"]["hard_safety_failure_count"]
        mappo_safe = all(
            x["collisions"] == 0 and x["blocked_zone_violations"] == 0
            for rep in mappo["replications"]
            for x in rep["scenario_results"])
        if failure_count:
            wording = (
                "The deterministic no-negotiation baseline failed the "
                f"predefined hard safety-validity gate in {failure_count} "
                "held-out scenario(s). Therefore a full safety-valid overall "
                "efficiency comparison is not available. " +
                ("The selected MAPPO configuration remained eligible under "
                 "the recorded held-out hard safety gates." if mappo_safe else
                 "The selected MAPPO configuration also did not satisfy all "
                 "recorded held-out hard safety gates."))
        else:
            wording = ("The selected MAPPO configuration reduced total team travel "
            "time relative to the deterministic no-negotiation baseline under "
            "the tested held-out scenarios while preserving the recorded hard "
            "safety gates." if difference is not None and difference < 0 else
            "No clear operational improvement over the baseline was established "
            "under the tested held-out scenarios." if difference == 0 else
            "The selected MAPPO configuration did not outperform the baseline "
            "under the tested held-out scenarios.")
        comparison = {"scenario_rows": rows,
            "baseline_safety_eligible": base["summary"]["safety_eligible"],
            "baseline_hard_safety_failure_count": failure_count,
            "baseline_hard_safety_failure_scenario_ids": base["summary"][
                "hard_safety_failure_scenario_ids"],
            "efficiency_comparison_scope": (
                "DESCRIPTIVE_MATCHED_COMPLETED_SCENARIO_SUBSET_ONLY"
                if failure_count else "ALL_MATCHED_HELD_OUT_SCENARIOS"),
            "matched_completed_scenario_count": len(matched),
            "matched_completed_subset_mean_difference": difference,
            "overall_mean_difference": None if failure_count else difference,
            "truthful_conclusion": wording}
        atomic_write_json(root / "comparison" /
                          "held_out_mappo_vs_baseline.json", comparison)
        _write_comparison_csv(root, rows)
    lines = ["# Final MAPPO Selection Report", "", "## Research question", "",
        "Which eligible configuration among predefined E5/E10/E15 gives the "
        "lowest mean validation total team travel time?", "",
        "## Controlled design", "", "Only PPO update epochs varied. Learning "
        "rate, clip, architecture, GNN mode, masks, environment, manifests and "
        "H=2 remained fixed.", "", "## Validation results", ""]
    for key, item in validation["candidates"].items():
        selected_mean = item['summary'].get(
            'mean_replication_total_team_travel_time_seconds',
            item['summary']['mean'])
        lines.append(f"- {key}: mean replication-total TTT {selected_mean}; "
                     f"{item['hard_gate_result']}")
    lines += ["", "## Selected configuration", "",
              f"{selection['selected_candidate_id']} — validation-selected "
              "among the predefined tested candidates.", "",
              "## Held-out and baseline", "",
              comparison["truthful_conclusion"] if comparison else
              "Held-out MAPPO and matched baseline experiments are not both complete.",
              "", "## Limitations", "",
              "N=3 and H=2 are bounded project-resource choices. This is not an "
              "exhaustive search and does not establish global optimality."]
    (root / "FINAL_MAPPO_SELECTION_REPORT.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8")
    summary = ["MAPPO MODEL-SELECTION SUMMARY", "",
        "Search type: Controlled one-factor ablation",
        "Hyperparameter varied: PPO update epochs",
        "Candidates: 5 / 10 / 15", "Replications: 3 canonical replications",
        "Training horizon: 2 PPO update cycles", "Selection data: Validation only",
        "Primary metric: Total team travel time — lower is better",
        f"Selected: {selection['selected_candidate_id']}",
        "Claim: Best-performing eligible configuration among predefined tested candidates.",
        "Not claimed: Global MAPPO optimality."]
    (root / "PANEL_SUMMARY.txt").write_text(
        "\n".join(summary) + "\n", encoding="utf-8")
    return {"selected": selection["selected_candidate_id"],
            "held_out_comparison_complete": heldout_ready}


def _write_comparison_csv(root, rows):
    path = Path(root) / "comparison" / "held_out_mappo_vs_baseline.csv"
    temporary = path.with_suffix(".csv.tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0]); writer.writeheader()
        for row in rows: writer.writerow({**row,
            "scenario_id": json.dumps(row["scenario_id"])})
    os.replace(temporary, path)


def run_selected_demo(root=OUTPUT_ROOT, use_gui=False):
    root = Path(root); selected = json.loads(
        (root / "selected_configuration.json").read_text(encoding="utf-8"))
    _, bundle = _load_bundle(root / "selected_policy.pt")
    provider = FinalSelectionInferenceProvider(bundle, sampling_seed=0)
    design = build_design(); records = []
    for item in select_demo_scenarios(design):
        signature = item["signature"]
        episode = CoupledNegotiationTrainingEnvironment(
            provider, use_gui=use_gui).run_episode(
            _specification(design["payload"], signature.scenario_id),
            design["manifests"][ScenarioRole.TRAINING].manifest_id)
        records.append(_episode_record(episode, "MAPPO"))
    return {"selected_candidate_id": selected["selected_candidate_id"],
            "demo_replication_rule": "CANONICAL_REPLICATION_0",
            "training_operations": 0, "held_out_scenarios_used": 0,
            "scenario_results": records}
