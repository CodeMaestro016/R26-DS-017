"""Resumable Step 5J.3C.2B three-replication learning-curve runner."""

import hashlib
import json
from pathlib import Path
from time import perf_counter

from experimentation import ScenarioRole, build_design
from negotiation_execution.replay import _specification

from .adam_contract import build_mechanical_adam_optimization_contract
from .architecture_contract import build_mechanical_pilot_architecture_contract
from .behavior_rollout import serializable
from .controlled_pilot import (
    _current_hashes, _identity, atomic_write_json,
    collect_controlled_training_pass)
from .evidence_checkpoint import (
    restore_evidence_resume_checkpoint, save_evidence_resume_checkpoint)
from .extended_learning_analysis import (
    exact_scenario_paired_changes,
    three_replication_descriptive_statistics)
from .mappo_provider import build_mechanical_mappo_behavior_policy_bundle
from .ppo_trainer import MechanicalMAPPOTrainer
from .rollout import MAPPOBehaviorRolloutIdentity


PROGRESS_PATH = Path("results/mappo_extended_learning_progress.json")
EVIDENCE_PATH = Path("results/mappo_extended_learning_curve_evidence.json")
REVIEW_PATH = Path("results/mappo_pilot_evidence_review.json")
TRANCHE_NAME = "EXTENDED_EVIDENCE_TRANCHE_V1"


def _tranche_identity(design, architecture, optimization):
    value = (TRANCHE_NAME, design["freeze"].freeze_id,
             architecture.contract_id, optimization.contract_id,
             "THREE_CANONICAL_REPLICATIONS", "THREE_POLICY_STATES")
    return (TRANCHE_NAME, hashlib.sha256(repr(value).encode()).hexdigest())


def _load_review():
    review = json.loads(REVIEW_PATH.read_text(encoding="utf-8"))
    if review.get("status") != "PILOT_EVIDENCE_REVIEW_COMPLETE":
        raise ValueError("STEP_5J_3C_2_REVIEW_NOT_VALIDATED")
    if review.get("next_readiness") != \
            "READY_TO_DEFINE_EXTENDED_LEARNING_EVIDENCE_PROTOCOL":
        raise ValueError("EXTENDED_EVIDENCE_PROTOCOL_NOT_READY")
    return review


def _fresh_bundle(design, architecture, optimization, manifest,
                  replication_identity):
    identity = MAPPOBehaviorRolloutIdentity(
        _identity(design, architecture, optimization, manifest,
                  replication_identity, "EXTENDED_INITIAL_MODEL_STATE"),
        design["freeze"].freeze_id, architecture.contract_id,
        optimization.contract_id, manifest.manifest_id)
    return build_mechanical_mappo_behavior_policy_bundle(
        component_seed_identity=(replication_identity,
                                 "MODEL_INITIALIZATION"),
        behavior_rollout_identity=identity)


def _new_progress(tranche_identity, design):
    return {
        "checkpoint": "STEP_5J_3C_2B",
        "evidence_tranche_identity": serializable(tranche_identity),
        "frozen_design_identity": serializable(design["freeze"].freeze_id),
        "completed_replications": [],
        "active_replication_index": 0,
        "active_policy_state_index": 0,
        "completed_policy_states_in_active_replication": 0,
        "purpose": "ATOMIC_LONG_RUNNING_EVIDENCE_PROGRESS"}


class ExtendedMAPLearningCurveRunner:
    def __init__(self, progress_path=PROGRESS_PATH,
                 evidence_path=EVIDENCE_PATH, resume=True):
        self.progress_path = Path(progress_path)
        self.evidence_path = Path(evidence_path)
        self.resume = resume

    def run(self):
        started = perf_counter()
        review = _load_review()
        design = build_design()
        architecture = build_mechanical_pilot_architecture_contract()
        optimization = build_mechanical_adam_optimization_contract()
        manifest = design["manifests"][ScenarioRole.TRAINING]
        specifications = tuple(_specification(design["payload"], scenario_id)
                               for scenario_id in manifest.scenario_ids)
        tranche_identity = _tranche_identity(
            design, architecture, optimization)
        if self.resume and self.progress_path.exists():
            progress = json.loads(self.progress_path.read_text(encoding="utf-8"))
            if progress.get("evidence_tranche_identity") != \
                    serializable(tranche_identity):
                raise ValueError("RESUME_TRANCHE_IDENTITY_MISMATCH")
        else:
            progress = _new_progress(tranche_identity, design)
            atomic_write_json(self.progress_path, progress)
        complete_records = list(progress.get("completed_replications", ()))
        completed_by_index = {item["replication_index"]: item
                              for item in complete_records}
        replications = []
        for replication_index in range(3):
            if replication_index in completed_by_index:
                replications.append(completed_by_index[replication_index])
                continue
            replication_identity = (
                "EXTENDED_MAPPO_REPLICATION_V1",
                design["freeze"].freeze_id, replication_index)
            bundle = _fresh_bundle(design, architecture, optimization,
                                   manifest, replication_identity)
            initial_hashes = _current_hashes(bundle)
            partial = progress.get("active_replication")
            if partial and partial.get("replication_index") == replication_index:
                states = list(partial.get("states", ()))
                updates = list(partial.get("updates", ()))
                checkpoint_paths = list(partial.get("resume_checkpoints", ()))
                if states:
                    resumed = restore_evidence_resume_checkpoint(
                        checkpoint_paths[-1], bundle)
                    rollout_payload = resumed["completed_rollout_payload"]
                else:
                    rollout_payload = None
            else:
                states, updates, checkpoint_paths = [], [], []
                rollout_payload = None
            rep_started = perf_counter()
            gnn_hash = initial_hashes["gnn"]
            while len(states) < 3:
                state_index = len(states)
                if state_index:
                    update_index = state_index
                    before_update = _current_hashes(bundle)
                    update_started = perf_counter()
                    update = MechanicalMAPPOTrainer(
                        rollout_payload=rollout_payload, bundle=bundle,
                        output_path=None).run()
                    update_runtime = perf_counter() - update_started
                    after_update = _current_hashes(bundle)
                    if after_update["gnn"] != gnn_hash:
                        raise RuntimeError("FROZEN_GNN_PARAMETER_CHANGED")
                    updates.append({
                        "update_index": update_index,
                        "source_policy_state_index": state_index - 1,
                        "source_rollout_identity":
                            rollout_payload["behavior_rollout_identity"],
                        "source_rollout_reused_by_other_update": False,
                        "parameter_state_identity":
                            f"REPLICATION_{replication_index}_POST_UPDATE_{update_index}",
                        "parameter_hashes_before": before_update,
                        "parameter_hashes_after": after_update,
                        "wall_clock_runtime_seconds": update_runtime,
                        "diagnostics": update})
                state_label = f"REPLICATION_{replication_index}_STATE_{state_index}"
                base_progress = {
                    **_new_progress(tranche_identity, design),
                    "completed_replications": replications,
                    "active_replication_index": replication_index,
                    "active_policy_state_index": state_index,
                    "completed_policy_states_in_active_replication": len(states),
                    "active_replication": {
                        "replication_index": replication_index,
                        "states": states, "updates": updates,
                        "resume_checkpoints": checkpoint_paths}}
                metrics, rollout_payload = collect_controlled_training_pass(
                    design=design, architecture=architecture,
                    optimization=optimization, manifest=manifest,
                    specifications=specifications, bundle=bundle,
                    replication_identity=replication_identity,
                    pass_label=state_label,
                    progress_context=base_progress,
                    progress_path=self.progress_path)
                hashes = _current_hashes(bundle)
                if hashes["gnn"] != gnn_hash:
                    raise RuntimeError("FROZEN_GNN_PARAMETER_CHANGED")
                metrics["policy_state_index"] = state_index
                metrics["parameter_state_identity"] = state_label
                metrics["proposer_hash"] = hashes["proposer"]
                metrics["responder_hash"] = hashes["responder"]
                metrics["critic_hash"] = hashes["critic"]
                metrics["gnn_hash"] = hashes["gnn"]
                states.append(metrics)
                checkpoint_path, checkpoint = save_evidence_resume_checkpoint(
                    bundle=bundle, replication_identity=replication_identity,
                    state_index=state_index,
                    frozen_design_identity=design["freeze"].freeze_id,
                    architecture_contract_identity=architecture.contract_id,
                    optimization_contract_identity=optimization.contract_id,
                    provisional_configuration_identity=
                        design["provisional"].configuration_id,
                    completed_rollout_payload=rollout_payload,
                    completed_rollout_metrics=metrics,
                    sampling_identity=metrics["sampling_seed_identity"],
                    progress_cursor={
                        "replication_index": replication_index,
                        "completed_policy_state_index": state_index,
                        "next_operation": "UPDATE" if state_index < 2
                                          else "NEXT_REPLICATION"},
                    update_diagnostics=updates)
                checkpoint_paths.append(str(checkpoint_path))
                progress = {
                    **_new_progress(tranche_identity, design),
                    "completed_replications": replications,
                    "active_replication_index": replication_index,
                    "active_policy_state_index": state_index,
                    "completed_policy_states_in_active_replication": len(states),
                    "active_replication": {
                        "replication_index": replication_index,
                        "replication_identity": serializable(replication_identity),
                        "initial_parameter_hashes": initial_hashes,
                        "states": states, "updates": updates,
                        "resume_checkpoints": checkpoint_paths,
                        "last_checkpoint_identity": serializable(
                            checkpoint["checkpoint_identity"])}}
                atomic_write_json(self.progress_path, progress)
            c0, c1, c2 = (item["team_travel_time_seconds"]
                          for item in states)
            record = {
                "replication_index": replication_index,
                "replication_identity": serializable(replication_identity),
                "canonical_replication_retained": True,
                "performance_selected": False,
                "fresh_initialization": True,
                "historical_pilot_state_spliced": False,
                "initial_parameter_hashes": initial_hashes,
                "policy_states": states,
                "updates": updates,
                "resume_checkpoints": checkpoint_paths,
                "learning_curve_deltas": {
                    "delta_0_to_1": c1 - c0,
                    "delta_1_to_2": c2 - c1,
                    "delta_0_to_2": c2 - c0},
                "scenario_paired_changes": exact_scenario_paired_changes(
                    states[0], states[1], states[2]),
                "gnn_hash_at_all_boundaries": [
                    initial_hashes["gnn"],
                    updates[0]["parameter_hashes_after"]["gnn"],
                    states[1]["gnn_hash"],
                    updates[1]["parameter_hashes_after"]["gnn"],
                    states[2]["gnn_hash"]],
                "gnn_unchanged": True,
                "wall_clock_runtime_seconds": perf_counter() - rep_started}
            if len(set(record["gnn_hash_at_all_boundaries"])) != 1:
                raise RuntimeError("FROZEN_GNN_PARAMETER_CHANGED")
            replications.append(record)
            progress = {
                **_new_progress(tranche_identity, design),
                "completed_replications": replications,
                "active_replication_index": replication_index + 1,
                "active_policy_state_index": 0,
                "completed_policy_states_in_active_replication": 0}
            atomic_write_json(self.progress_path, progress)
        statistic_sources = {
            "C0": [r["policy_states"][0]["team_travel_time_seconds"]
                   for r in replications],
            "C1": [r["policy_states"][1]["team_travel_time_seconds"]
                   for r in replications],
            "C2": [r["policy_states"][2]["team_travel_time_seconds"]
                   for r in replications],
            "delta_0_to_1": [r["learning_curve_deltas"]["delta_0_to_1"]
                             for r in replications],
            "delta_1_to_2": [r["learning_curve_deltas"]["delta_1_to_2"]
                             for r in replications],
            "delta_0_to_2": [r["learning_curve_deltas"]["delta_0_to_2"]
                             for r in replications]}
        result = {
            "checkpoint": "STEP_5J_3C_2B",
            "status": "EXTENDED_MULTI_UPDATE_EVIDENCE_ACQUIRED",
            "evidence_tranche_identity": serializable(tranche_identity),
            "source_review_identity": review["source_pilot_identity"],
            "frozen_design_identity": serializable(design["freeze"].freeze_id),
            "provisional_configuration_identity": serializable(
                design["provisional"].configuration_id),
            "architecture_contract_identity": serializable(
                architecture.contract_id),
            "optimization_contract_identity": serializable(
                optimization.contract_id),
            "replications_observed": 3,
            "update_intervals_observed_per_replication": 2,
            "policy_states_per_replication": 3,
            "training_manifest_collections": 9,
            "training_scenario_executions": 324,
            "replications": replications,
            "cross_replication_descriptive_statistics": {
                name: three_replication_descriptive_statistics(values)
                for name, values in statistic_sources.items()},
            "compute_cost_evidence": {
                "total_sumo_steps": sum(
                    state["sumo_step_count"] for replication in replications
                    for state in replication["policy_states"]),
                "total_state_collection_wall_clock_seconds": sum(
                    state["wall_clock_runtime_seconds"]
                    for replication in replications
                    for state in replication["policy_states"]),
                "total_update_runtime_seconds": sum(
                    update["wall_clock_runtime_seconds"]
                    for replication in replications
                    for update in replication["updates"]),
                "total_runner_wall_clock_seconds": perf_counter() - started},
            "safety_evidence": {
                "collisions": sum(state["collision_count"]
                                  for replication in replications
                                  for state in replication["policy_states"]),
                "blocked_zone_violations": sum(
                    state["blocked_zone_violation_count"]
                    for replication in replications
                    for state in replication["policy_states"])},
            "data_boundary_evidence": {
                "training_scenario_executions": 324,
                "validation_scenario_executions": 0,
                "held_out_scenario_executions": 0,
                "candidate_comparisons": 0},
            "improvement_threshold_used": False,
            "outliers_declared": 0,
            "replications_discarded": 0,
            "update_3_performed": False,
            "final_replication_count_selected": False,
            "final_training_budget_selected": False,
            "next_readiness":
                "READY_FOR_EXTENDED_EVIDENCE_SUFFICIENCY_REVIEW",
            "next_checkpoint": "STEP_5J_3C_2C"}
        if result["safety_evidence"] != {
                "collisions": 0, "blocked_zone_violations": 0}:
            atomic_write_json(self.evidence_path, result)
            raise RuntimeError("EXTENDED_EVIDENCE_SAFETY_GATE_FAILED")
        atomic_write_json(self.evidence_path, result)
        return result
