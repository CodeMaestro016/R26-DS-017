"""Step 5J.3C.1 two-replication closed-loop learning probe."""

import hashlib
import json
from pathlib import Path
from time import perf_counter

from experimentation import ScenarioRole, build_design
from negotiation_execution.replay import _specification

from .adam_contract import build_mechanical_adam_optimization_contract
from .architecture_contract import (
    build_mechanical_pilot_architecture_contract,
    deterministic_initialization_seed)
from .behavior_rollout import serializable
from .environment import CoupledNegotiationTrainingEnvironment
from .mappo_provider import (
    MAPPOBehaviorActionProvider, build_mechanical_mappo_behavior_policy_bundle)
from .pilot_analysis import (
    paired_difference_summary, two_replication_sample_statistics)
from .ppo_trainer import MechanicalMAPPOTrainer
from .rollout import MAPPOBehaviorRolloutIdentity, parameter_hash


EVIDENCE_PATH = Path("results/mappo_closed_loop_pilot_evidence.json")
PROGRESS_PATH = Path("results/mappo_closed_loop_pilot_progress.json")


def _identity(design, architecture, optimization, manifest, replication, label):
    fields = (design["freeze"].freeze_id, architecture.contract_id,
              optimization.contract_id, manifest.manifest_id,
              replication, label)
    return (label, hashlib.sha256(repr(fields).encode()).hexdigest())


def _current_hashes(bundle):
    return {"gnn": parameter_hash(bundle.gnn),
            "proposer": parameter_hash(bundle.proposer_actor),
            "responder": parameter_hash(bundle.responder_actor),
            "critic": parameter_hash(bundle.centralized_critic)}


def _pass_rollout_payload(design, architecture, optimization, manifest,
                          pass_identity, bundle, provider):
    factors = provider.final_factors
    critics = provider.final_critics
    hashes = _current_hashes(bundle)
    return {
        "checkpoint": "STEP_5J_3B_3",
        "status": "REAL_MAPPO_BEHAVIOR_ROLLOUT_VALIDATED",
        "step_5j_3b_4_readiness": "READY_FOR_FIRST_MECHANICAL_PPO_UPDATE",
        "behavior_rollout_identity": {
            "rollout_id": serializable(pass_identity)},
        "frozen_design_id": serializable(design["freeze"].freeze_id),
        "architecture_contract_id": serializable(architecture.contract_id),
        "optimization_contract_id": serializable(optimization.contract_id),
        "training_manifest_id": serializable(manifest.manifest_id),
        "initial_parameter_hashes": hashes,
        "policy_factors": serializable(factors),
        "critic_samples": serializable(critics),
        "total_ppo_sample_count": len(factors),
        "critic_sample_count": len(critics),
        "profiling_ppo_samples_reused": 0,
    }


def collect_controlled_training_pass(*, design, architecture, optimization,
                                     manifest, specifications, bundle,
                                     replication_identity, pass_label,
                                     progress_context):
    pass_identity = _identity(
        design, architecture, optimization, manifest,
        replication_identity, pass_label)
    sampling_seed = deterministic_initialization_seed(
        architecture.contract_id,
        (replication_identity, pass_label, "POLICY_ACTION_SAMPLING"))
    provider = MAPPOBehaviorActionProvider(bundle, sampling_seed=sampling_seed)
    initial_hashes = _current_hashes(bundle)
    started = perf_counter()
    episodes = []
    for index, specification in enumerate(specifications, 1):
        print(f"{replication_identity[-1]} {pass_label} scenario "
              f"{index}/{len(specifications)}")
        episodes.append(CoupledNegotiationTrainingEnvironment(provider).run_episode(
            specification, manifest.manifest_id))
        PROGRESS_PATH.write_text(json.dumps({
            **progress_context, "active_pass": pass_label,
            "active_pass_scenarios_completed": index,
            "active_pass_team_travel_time_seconds": sum(
                item.team_travel_time_seconds for item in episodes)}, indent=2),
            encoding="utf-8")
    final_hashes = _current_hashes(bundle)
    if final_hashes != initial_hashes:
        raise RuntimeError("POLICY_PARAMETER_CHANGED_DURING_COLLECTION")
    if any(item.collision_count for item in episodes):
        raise RuntimeError("CONTROLLED_PILOT_COLLISION_OBSERVED")
    if any(item.blocked_zone_entry_violation_count for item in episodes):
        raise RuntimeError("CONTROLLED_PILOT_BLOCKED_ZONE_VIOLATION")
    factors = tuple(provider.final_factors)
    metadata = tuple(provider.batch_metadata)
    action_names = ("KEEP_CLAIM", "RELINQUISH_CLAIM",
                    "ACCEPT_RELINQUISHMENT", "REJECT_RELINQUISHMENT")
    action_counts = {name: sum(item.selected_semantic_action == name
                               for item in factors) for name in action_names}
    scenario_metrics = []
    for episode in episodes:
        episode_factors = tuple(item for item in factors
                                if item.episode_id == episode.episode_id)
        episode_metadata = tuple(item for item in metadata
                                 if item["episode_id"] == episode.episode_id)
        scenario_metrics.append({
            "scenario_id": serializable(episode.scenario_id),
            "team_travel_time_seconds": episode.team_travel_time_seconds,
            "raw_reward": episode.raw_shared_team_reward,
            "proposer_count": sum(x.decision_role == "PROPOSER"
                                  for x in episode_factors),
            "responder_count": sum(x.decision_role == "RESPONDER"
                                   for x in episode_factors),
            "action_counts": {name: sum(x.selected_semantic_action == name
                                         for x in episode_factors)
                              for name in action_names},
            "coordination_cycle_count": sum(
                x["coordination_cycle_detected"] for x in episode_metadata),
            "physical_cycle_count": sum(
                x["physical_execution_cycle_detected"] for x in episode_metadata),
            "physical_executable_outcome_count": sum(
                x["graph_executable"] for x in episode_metadata),
            "completed_vehicle_count": episode.completed_vehicle_count,
            "collision_count": episode.collision_count,
            "blocked_zone_violation_count":
                episode.blocked_zone_entry_violation_count,
            "native_safety_intervention_count":
                episode.native_sumo_safety_intervention_count,
            "policy_factor_count": len(episode_factors),
            "sumo_step_count": episode.sumo_step_count,
            "wall_clock_runtime_seconds": episode.wall_clock_runtime_seconds})
    metrics = {
        "pass_identity": serializable(pass_identity),
        "sampling_seed_identity": serializable((
            replication_identity, pass_label, "POLICY_ACTION_SAMPLING")),
        "derived_sampling_seed": sampling_seed,
        "policy_parameter_identity": serializable(
            provider.policy_parameter_identity),
        "critic_identity": final_hashes["critic"],
        "scenario_count": len(episodes),
        "scenario_metrics": scenario_metrics,
        "team_travel_time_seconds": sum(
            item.team_travel_time_seconds for item in episodes),
        "raw_reward": sum(item.raw_shared_team_reward for item in episodes),
        "proposer_count": sum(x.decision_role == "PROPOSER" for x in factors),
        "responder_count": sum(x.decision_role == "RESPONDER" for x in factors),
        "policy_factor_count": len(factors),
        "action_counts": action_counts,
        "coordination_cycle_count": sum(
            item["coordination_cycle_detected"] for item in metadata),
        "physical_cycle_count": sum(
            item["physical_execution_cycle_detected"] for item in metadata),
        "physical_executable_outcome_count": sum(
            item["graph_executable"] for item in metadata),
        "completed_vehicle_count": sum(
            item.completed_vehicle_count for item in episodes),
        "collision_count": 0, "blocked_zone_violation_count": 0,
        "native_safety_intervention_count": sum(
            item.native_sumo_safety_intervention_count for item in episodes),
        "sumo_step_count": sum(item.sumo_step_count for item in episodes),
        "wall_clock_runtime_seconds": perf_counter() - started,
        "parameter_hashes_before_and_after_collection": {
            "before": initial_hashes, "after": final_hashes},
        "hard_validity_passed": all(all(
            item.hard_validity_gate_results.values()) for item in episodes),
        "route_truth_actor_fields": 0,
    }
    payload = _pass_rollout_payload(
        design, architecture, optimization, manifest, pass_identity,
        bundle, provider)
    return metrics, payload


class ControlledMAPPOPilotRunner:
    def run(self):
        started = perf_counter()
        design = build_design()
        architecture = build_mechanical_pilot_architecture_contract()
        optimization = build_mechanical_adam_optimization_contract()
        manifest = design["manifests"][ScenarioRole.TRAINING]
        specifications = tuple(_specification(design["payload"], scenario_id)
                               for scenario_id in manifest.scenario_ids)
        replications = []
        for replication_index in range(2):
            replication_identity = (
                "CONTROLLED_MAPPO_PILOT_REPLICATION_V1",
                design["freeze"].freeze_id, replication_index)
            behavior_identity = MAPPOBehaviorRolloutIdentity(
                _identity(design, architecture, optimization, manifest,
                          replication_identity, "INITIAL_MODEL_STATE"),
                design["freeze"].freeze_id, architecture.contract_id,
                optimization.contract_id, manifest.manifest_id)
            bundle = build_mechanical_mappo_behavior_policy_bundle(
                component_seed_identity=(replication_identity,
                                         "MODEL_INITIALIZATION"),
                behavior_rollout_identity=behavior_identity)
            initial_hashes = _current_hashes(bundle)
            rep_started = perf_counter()
            pass0, rollout0 = collect_controlled_training_pass(
                design=design, architecture=architecture,
                optimization=optimization, manifest=manifest,
                specifications=specifications, bundle=bundle,
                replication_identity=replication_identity,
                pass_label="TRAINING_PASS_0_PRE_UPDATE",
                progress_context={"replication_index": replication_index})
            update_started = perf_counter()
            update = MechanicalMAPPOTrainer(
                rollout_payload=rollout0, bundle=bundle,
                output_path=None).run()
            update_runtime = perf_counter() - update_started
            after_update = _current_hashes(bundle)
            pass1, _ = collect_controlled_training_pass(
                design=design, architecture=architecture,
                optimization=optimization, manifest=manifest,
                specifications=specifications, bundle=bundle,
                replication_identity=replication_identity,
                pass_label="TRAINING_PASS_1_POST_UPDATE",
                progress_context={"replication_index": replication_index})
            after_pass1 = _current_hashes(bundle)
            if after_pass1 != after_update:
                raise RuntimeError("POLICY_PARAMETER_CHANGED_DURING_COLLECTION")
            if not (initial_hashes["gnn"] == after_update["gnn"] ==
                    after_pass1["gnn"]):
                raise RuntimeError("FROZEN_GNN_PARAMETER_CHANGED")
            differences = tuple(
                post["team_travel_time_seconds"] - pre["team_travel_time_seconds"]
                for pre, post in zip(pass0["scenario_metrics"],
                                     pass1["scenario_metrics"]))
            replication = {
                "replication_index": replication_index,
                "replication_identity": serializable(replication_identity),
                "seed_selected_by_performance": False,
                "initial_policy_identity": serializable(
                    bundle.policy_parameter_identity),
                "pass0": pass0,
                "update_identity": serializable((
                    "CONTROLLED_PILOT_UPDATE_V1", replication_identity,
                    update["post_update_policy_identity"])),
                "update_diagnostics": update,
                "update_runtime_seconds": update_runtime,
                "post_update_policy_identity":
                    update["post_update_policy_identity"],
                "pass1": pass1,
                "delta_team_travel_time_seconds":
                    pass1["team_travel_time_seconds"] -
                    pass0["team_travel_time_seconds"],
                "paired_scenario_differences": differences,
                "paired_difference_summary":
                    paired_difference_summary(differences),
                "parameter_hashes": {
                    "initial": initial_hashes,
                    "after_update": after_update,
                    "after_pass1": after_pass1},
                "hard_validity_results": {
                    "pass0": pass0["hard_validity_passed"],
                    "pass1": pass1["hard_validity_passed"],
                    "gnn_unchanged": True,
                    "collisions": 0, "blocked_zone_violations": 0},
                "wall_clock_measurements": {
                    "pass0_seconds": pass0["wall_clock_runtime_seconds"],
                    "update_seconds": update_runtime,
                    "pass1_seconds": pass1["wall_clock_runtime_seconds"],
                    "total_replication_seconds": perf_counter() - rep_started},
                "provenance": {"performance_selected_seed": False,
                               "mechanical_weights_reused": False,
                               "pass0_data_used_for_update_cycles": 1,
                               "pass1_update_cycles": 0}}
            replications.append(replication)
            PROGRESS_PATH.write_text(json.dumps({
                "completed_replications": replication_index + 1,
                "replications": replications}, indent=2), encoding="utf-8")
        pre = [item["pass0"]["team_travel_time_seconds"]
               for item in replications]
        post = [item["pass1"]["team_travel_time_seconds"]
                for item in replications]
        delta = [item["delta_team_travel_time_seconds"]
                 for item in replications]
        result = {
            "checkpoint": "STEP_5J_3C_1",
            "status": "CLOSED_LOOP_PROGRESS_AND_VARIANCE_PROBE_COMPLETE",
            "training_budget_status":
                "FIRST_CLOSED_LOOP_PROGRESS_EVIDENCE_MEASURED",
            "replication_status": "FIRST_VARIANCE_PROBE_MEASURED",
            "final_training_budget_selected": False,
            "final_replication_count_selected": False,
            "final_replication_count_status":
                "REQUIRES_POST_PILOT_DETERMINATION",
            "frozen_design_id": serializable(design["freeze"].freeze_id),
            "provisional_configuration_id": serializable(
                design["provisional"].configuration_id),
            "architecture_contract_id": serializable(architecture.contract_id),
            "optimization_contract_id": serializable(optimization.contract_id),
            "physical_execution_mapping_identity":
                "COORDINATION_TO_PHYSICAL_EXECUTION_MAPPING_STEP_5J_3B_3A",
            "replication_probe_reason": "MINIMUM_SAMPLE_VARIANCE_PROBE",
            "replication_count": 2,
            "replications": replications,
            "variance_evidence": {
                "pre_update": two_replication_sample_statistics(pre),
                "post_update": two_replication_sample_statistics(post),
                "delta": two_replication_sample_statistics(delta)},
            "paired_scenario_change_count": 72,
            "improvement_threshold_used": False,
            "convergence_claimed": False,
            "total_training_scenario_executions": 144,
            "total_training_manifest_collections": 4,
            "total_ppo_update_cycles": 2,
            "total_sumo_steps": sum(
                item[label]["sumo_step_count"] for item in replications
                for label in ("pass0", "pass1")),
            "total_policy_factors": sum(
                item[label]["policy_factor_count"] for item in replications
                for label in ("pass0", "pass1")),
            "total_wall_clock_runtime_seconds": perf_counter() - started,
            "total_update_runtime_seconds": sum(
                item["update_runtime_seconds"] for item in replications),
            "collisions": 0, "blocked_zone_violations": 0,
            "validation_runs": 0, "held_out_runs": 0,
            "new_reward_terms": 0, "new_candidate_values": 0,
            "selected_hyperparameters": 0,
            "two_replications_are_final_design": False,
            "research_statement": (
                "The two-replication pilot is the mathematical minimum required "
                "to obtain a first sample-variance estimate. It is not the final "
                "replication design.")}
        EVIDENCE_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
        return result
