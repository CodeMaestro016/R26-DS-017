"""One frozen TRAINING-manifest MAPPO behavior collection pass."""

import json
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from pathlib import Path

from experimentation import ScenarioRole, build_design
from negotiation_execution.replay import _specification

from .environment import CoupledNegotiationTrainingEnvironment
from .mappo_provider import (
    MAPPOBehaviorActionProvider,
    build_mechanical_mappo_behavior_policy_bundle)


ROLLOUT_PATH = Path("results/mappo_behavior_rollout.json")
PROGRESS_PATH = Path("results/mappo_behavior_rollout_progress.json")


def serializable(value):
    if is_dataclass(value):
        return {field.name: serializable(getattr(value, field.name))
                for field in fields(value)}
    if isinstance(value, Mapping):
        return {str(key): serializable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [serializable(item) for item in value]
    return value


def _episode_summary(episode, metadata):
    return {
        "episode_id": serializable(episode.episode_id),
        "scenario_id": serializable(episode.scenario_id),
        "completion_status": episode.episode_completion_status,
        "sumo_steps": episode.sumo_step_count,
        "simulation_duration_seconds": episode.simulation_duration_seconds,
        "completed_vehicle_count": episode.completed_vehicle_count,
        "team_travel_time_seconds": episode.team_travel_time_seconds,
        "raw_shared_team_reward": episode.raw_shared_team_reward,
        "collision_count": episode.collision_count,
        "blocked_zone_entry_violation_count":
            episode.blocked_zone_entry_violation_count,
        "physical_speed_command_count": episode.physical_speed_command_count,
        "execution_plan_count": episode.conflict_zone_execution_plan_count,
        "joint_batches": serializable(metadata),
    }


def collect_mappo_behavior_rollout(output_path=ROLLOUT_PATH):
    design = build_design()
    manifest = design["manifests"][ScenarioRole.TRAINING]
    specifications = tuple(_specification(design["payload"], scenario_id)
                           for scenario_id in manifest.scenario_ids)
    bundle = build_mechanical_mappo_behavior_policy_bundle()
    provider = MAPPOBehaviorActionProvider(bundle)
    episodes = []
    for index, specification in enumerate(specifications, 1):
        print(f"Collecting MAPPO TRAINING scenario {index}/{len(specifications)}")
        before = len(provider.batch_metadata)
        try:
            episode = CoupledNegotiationTrainingEnvironment(provider).run_episode(
                specification, manifest.manifest_id)
        except RuntimeError as error:
            evidence = error.args[0] if error.args else None
            if (isinstance(evidence, tuple) and evidence and
                    evidence[0] == "EXECUTION_GRAPH_PHYSICAL_CONFLICT_UNORDERED"):
                blocker = {
                    "checkpoint": "STEP_5J_3B_3",
                    "status": "MAPPO_BEHAVIOR_ROLLOUT_BLOCKED",
                    "next_blocker": evidence[0],
                    "failed_training_scenario_index": index,
                    "failed_scenario_id": serializable(specification.scenario_id),
                    "sampled_effective_graph": serializable(evidence[1]),
                    "movement_path_by_vehicle": serializable(evidence[2]),
                    "completed_training_scenarios_before_stop": len(episodes),
                    "policy_actions_resampled": 0,
                    "branch_replacements": 0,
                    "manual_graph_edits": 0,
                    "optimizer_instances": 0,
                    "backward_calls": 0,
                    "parameter_updates": 0,
                    "frozen_design_id": serializable(design["freeze"].freeze_id),
                    "architecture_contract_id": serializable(
                        bundle.architecture_contract_id),
                    "optimization_contract_id": serializable(
                        bundle.optimization_contract_id),
                    "behavior_rollout_identity": serializable(
                        bundle.behavior_rollout_identity),
                    "initial_parameter_hashes": dict(
                        bundle.initial_parameter_hashes),
                    "parameter_hashes_at_stop": provider.final_parameter_hashes(),
                }
                Path("results/mappo_behavior_rollout_blocker.json").write_text(
                    json.dumps(blocker, indent=2), encoding="utf-8")
            raise
        episodes.append(episode)
        metadata = provider.batch_metadata[before:]
        PROGRESS_PATH.write_text(json.dumps({
            "completed": index,
            "episode_summaries": [_episode_summary(item, tuple(
                record for record in provider.batch_metadata
                if tuple(record["episode_id"]) == tuple(item.episode_id)))
                for item in episodes]}, indent=2), encoding="utf-8")

    if tuple(sorted((item.scenario_id for item in episodes), key=repr)) != (
            manifest.scenario_ids):
        raise RuntimeError("TRAINING_MANIFEST_NOT_VISITED_EXACTLY_ONCE")
    if not any(item.decision_role == "RESPONDER"
               for item in provider.final_factors):
        raise RuntimeError("RESPONDER_BEHAVIOR_PATH_NOT_OBSERVED")
    replay = provider.replay_all()
    final_hashes = provider.final_parameter_hashes()
    if dict(bundle.initial_parameter_hashes) != final_hashes:
        raise RuntimeError("MAPPO_PARAMETER_CHANGED_DURING_COLLECTION")

    # Canonical first scenario reproducibility uses a fresh identical bundle and
    # sampling generator, never a performance-selected scenario or seed.
    replay_provider = MAPPOBehaviorActionProvider(
        build_mechanical_mappo_behavior_policy_bundle())
    replay_episode = CoupledNegotiationTrainingEnvironment(
        replay_provider).run_episode(specifications[0], manifest.manifest_id)
    canonical_original = tuple(record for record in provider.batch_metadata
                               if tuple(record["episode_id"]) ==
                               tuple(episodes[0].episode_id))
    canonical_replay = tuple(replay_provider.batch_metadata)
    trace_equal = canonical_original == canonical_replay
    physical_trace = lambda item: (
        item.completed_vehicle_count, item.physical_speed_command_count,
        item.conflict_zone_execution_plan_count,
        item.team_travel_time_seconds, item.raw_shared_team_reward)
    physical_equal = physical_trace(episodes[0]) == physical_trace(replay_episode)
    if not trace_equal or not physical_equal:
        raise RuntimeError("MAPPO_BEHAVIOR_REPRODUCIBILITY_MISMATCH")

    proposer = tuple(x for x in provider.final_factors
                     if x.decision_role == "PROPOSER")
    responder = tuple(x for x in provider.final_factors
                      if x.decision_role == "RESPONDER")
    actions = {name: sum(x.selected_semantic_action == name
                         for x in provider.final_factors) for name in (
        "KEEP_CLAIM", "RELINQUISH_CLAIM",
        "ACCEPT_RELINQUISHMENT", "REJECT_RELINQUISHMENT")}
    metadata = tuple(provider.batch_metadata)
    payload = {
        "checkpoint": "STEP_5J_3B_3",
        "status": "REAL_MAPPO_BEHAVIOR_ROLLOUT_VALIDATED",
        "step_5j_3b_4_readiness": "READY_FOR_FIRST_MECHANICAL_PPO_UPDATE",
        "behavior_rollout_identity": serializable(
            bundle.behavior_rollout_identity),
        "frozen_design_id": serializable(design["freeze"].freeze_id),
        "architecture_contract_id": serializable(
            bundle.architecture_contract_id),
        "optimization_contract_id": serializable(
            bundle.optimization_contract_id),
        "training_manifest_id": serializable(manifest.manifest_id),
        "seed_derivation_method":
            "SHA256_CONTRACT_AND_BEHAVIOR_IDENTITY_COMPONENT_DERIVATION",
        "derived_component_seeds": dict(bundle.component_seeds),
        "hard_coded_training_seed_values": 0,
        "seed_selected_by_performance": False,
        "initial_parameter_hashes": dict(bundle.initial_parameter_hashes),
        "final_parameter_hashes": final_hashes,
        "parameter_hashes_unchanged": True,
        "model_counts": {"frozen_gnn": 1, "proposer_actor": 1,
                         "responder_actor": 1, "centralized_critic": 1},
        "trainable_parameter_counts": {
            "gnn": sum(x.numel() for x in bundle.gnn.parameters()
                       if x.requires_grad),
            "proposer": sum(x.numel() for x in
                            bundle.proposer_actor.parameters()
                            if x.requires_grad),
            "responder": sum(x.numel() for x in
                             bundle.responder_actor.parameters()
                             if x.requires_grad),
            "critic": sum(x.numel() for x in
                          bundle.centralized_critic.parameters()
                          if x.requires_grad)},
        "training_manifest_passes": 1,
        "training_scenarios_attempted": len(episodes),
        "training_scenarios_completed": sum(
            x.episode_completion_status == "COMPLETE" for x in episodes),
        "validation_performance_runs": 0,
        "held_out_performance_runs": 0,
        "episode_summaries": [_episode_summary(
            item, tuple(record for record in metadata
                        if tuple(record["episode_id"]) == tuple(item.episode_id)))
            for item in episodes],
        "joint_decision_batch_count": len(metadata),
        "proposer_ppo_sample_count": len(proposer),
        "responder_ppo_sample_count": len(responder),
        "total_ppo_sample_count": len(provider.final_factors),
        "critic_sample_count": len(provider.final_critics),
        "multi_factor_decision_batch_count": sum(
            x["proposer_count"] + x["responder_count"] > 1 for x in metadata),
        "real_proposal_count": sum(x["proposal_count"] for x in metadata),
        "action_counts": actions,
        "cyclic_policy_outcome_count": sum(x["cycle_detected"] for x in metadata),
        "executable_policy_outcome_count": sum(x["graph_executable"] for x in metadata),
        "joint_protocol_evaluations": provider.joint_protocol_evaluations,
        "manual_graph_edits": provider.manual_graph_edits,
        "executable_branch_replacements": 0,
        "branch_enumerator_action_selections":
            provider.branch_enumerator_action_selections,
        "collisions": sum(x.collision_count for x in episodes),
        "blocked_zone_violations": sum(
            x.blocked_zone_entry_violation_count for x in episodes),
        "team_travel_time_seconds": sum(
            x.team_travel_time_seconds for x in episodes),
        "raw_shared_team_reward": sum(x.raw_shared_team_reward for x in episodes),
        "return_record_count": len(provider.final_critics),
        "advantage_record_count": len(provider.final_critics),
        "critic_samples_duplicated_per_policy_factor": False,
        "policy_factors": serializable(provider.final_factors),
        "critic_samples": serializable(provider.final_critics),
        "joint_batch_metadata": serializable(metadata),
        "policy_replay": {
            "samples_replayed": len(replay),
            "finite_log_probabilities": all(
                __import__("math").isfinite(x.behavior_policy_log_probability)
                for x in provider.final_factors),
            "hard_masks_exact": True,
            "old_current_log_probabilities_exact": True,
            "importance_ratios_exactly_one": all(x[3] == 1.0 for x in replay)},
        "canonical_first_scenario_reproducibility": {
            "semantic_action_and_logprob_trace_exact": trace_equal,
            "effective_graph_trace_exact": trace_equal,
            "physical_event_trace_exact": physical_equal},
        "profiling_ppo_samples_reused": 0,
        "route_truth_actor_fields": 0,
        "future_outcome_action_selection_fields": 0,
        "optimizer_instances": 0,
        "backward_calls": 0,
        "parameter_updates": 0,
        "ppo_optimization_epochs_executed": 0,
        "model_checkpoints": 0,
        "learned_main_actions": 0,
        "new_reward_terms": 0,
    }
    if payload["collisions"]:
        raise RuntimeError("MAPPO_BEHAVIOR_ROLLOUT_COLLISION_OBSERVED")
    if payload["blocked_zone_violations"]:
        raise RuntimeError("MAPPO_BEHAVIOR_BLOCKED_ZONE_VIOLATION")
    output_path = Path(output_path)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload
