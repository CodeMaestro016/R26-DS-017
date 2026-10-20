"""One frozen TRAINING-manifest MAPPO behavior collection pass."""

# Import json for use in this module.
import json
# Import Mapping from collections.abc for the operations below.
from collections.abc import Mapping
# Import fields, is_dataclass from dataclasses for the operations below.
from dataclasses import fields, is_dataclass
# Import Path from pathlib for the operations below.
from pathlib import Path

# Import ScenarioRole, build_design from experimentation for the operations below.
from experimentation import ScenarioRole, build_design
# Import _specification from negotiation_execution.replay for the operations below.
from negotiation_execution.replay import _specification

# Import CoupledNegotiationTrainingEnvironment from .environment for the operations below.
from .environment import CoupledNegotiationTrainingEnvironment
# Import MAPPOBehaviorActionProvider, build_mechanical_mappo_behavior_policy_bundle from .mappo_provider for the
# operations below.
from .mappo_provider import (
    MAPPOBehaviorActionProvider,
    build_mechanical_mappo_behavior_policy_bundle)


# Set ROLLOUT_PATH to the result of Path(the text 'results/mappo_behavior_rollout.json').
ROLLOUT_PATH = Path("results/mappo_behavior_rollout.json")
# Set PROGRESS_PATH to the result of Path(the text 'results/mappo_behavior_rollout_progress.json').
PROGRESS_PATH = Path("results/mappo_behavior_rollout_progress.json")


# Serializable using the inputs and processing steps below.
# Input value: the supplied value.
# Output: return the value selected by the matching return branch below.
# Processing: select branches using the stated conditions.
def serializable(value):
    # Run this branch when the result of is_dataclass(value).
    if is_dataclass(value):
        # Return a dictionary of field.name mapped to the result of serializable(the requested attribute of value)
        # for field in the result of fields(value) to the caller.
        return {field.name: serializable(getattr(value, field.name))
                # Evaluate the result of fields(value) as part of the enclosing expression.
                for field in fields(value)}
    # Run this branch when whether value has type Mapping.
    if isinstance(value, Mapping):
        # Return a dictionary of a string built from key mapped to the result of serializable(item) for (key,
        # item) in key/value pairs from value to the caller.
        return {str(key): serializable(item) for key, item in value.items()}
    # Run this branch when whether value has type a tuple containing tuple, list.
    if isinstance(value, (tuple, list)):
        # Return a list of the result of serializable(item) for item in value to the caller.
        return [serializable(item) for item in value]
    # Return value to the caller.
    return value


# Episode summary using the inputs and processing steps below.
# Input episode: the supplied episode.
# Input metadata: the supplied metadata.
# Output: a dictionary containing episode_id, scenario_id, completion_status, sumo_steps,
# simulation_duration_seconds,...
def _episode_summary(episode, metadata):
    # Return a dictionary containing episode_id, scenario_id, completion_status, sumo_steps,
    # simulation_duration_seconds,... to the caller.
    return {
        # Store the result of serializable(episode.episode_id) under 'episode_id'.
        "episode_id": serializable(episode.episode_id),
        # Store the result of serializable(episode.scenario_id) under 'scenario_id'.
        "scenario_id": serializable(episode.scenario_id),
        # Store episode.episode_completion_status under 'completion_status'.
        "completion_status": episode.episode_completion_status,
        # Store episode.sumo_step_count under 'sumo_steps'.
        "sumo_steps": episode.sumo_step_count,
        # Store episode.simulation_duration_seconds under 'simulation_duration_seconds'.
        "simulation_duration_seconds": episode.simulation_duration_seconds,
        # Store episode.completed_vehicle_count under 'completed_vehicle_count'.
        "completed_vehicle_count": episode.completed_vehicle_count,
        # Store episode.team_travel_time_seconds under 'team_travel_time_seconds'.
        "team_travel_time_seconds": episode.team_travel_time_seconds,
        # Store episode.raw_shared_team_reward under 'raw_shared_team_reward'.
        "raw_shared_team_reward": episode.raw_shared_team_reward,
        # Store episode.collision_count under 'collision_count'.
        "collision_count": episode.collision_count,
        "blocked_zone_entry_violation_count":
            # Evaluate episode.blocked_zone_entry_violation_count as part of the enclosing expression.
            episode.blocked_zone_entry_violation_count,
        # Store episode.physical_speed_command_count under 'physical_speed_command_count'.
        "physical_speed_command_count": episode.physical_speed_command_count,
        # Store episode.conflict_zone_execution_plan_count under 'execution_plan_count'.
        "execution_plan_count": episode.conflict_zone_execution_plan_count,
        # Store the result of serializable(metadata) under 'joint_batches'.
        "joint_batches": serializable(metadata),
    }


# Collect mappo behavior rollout using the inputs and processing steps below.
# Input output_path: the supplied output path.
# Output: payload.
# Processing: iterate over the relevant records, then select branches using the stated conditions, then handle the
# specified errors.
def collect_mappo_behavior_rollout(output_path=ROLLOUT_PATH):
    # Set design to the result of build_design().
    design = build_design()
    # Set manifest to design['manifests'] at ScenarioRole.TRAINING.
    manifest = design["manifests"][ScenarioRole.TRAINING]
    # Set specifications to a tuple built from a lazy sequence of the result of _specification(design at
    # 'payload', scenario_id) for scenario_id in manifest.scenario_ids.
    specifications = tuple(_specification(design["payload"], scenario_id)
                           # Evaluate manifest.scenario_ids as part of the enclosing expression.
                           for scenario_id in manifest.scenario_ids)
    # Set bundle to the result of build_mechanical_mappo_behavior_policy_bundle().
    bundle = build_mechanical_mappo_behavior_policy_bundle()
    # Set provider to the result of MAPPOBehaviorActionProvider(bundle).
    provider = MAPPOBehaviorActionProvider(bundle)
    # Set episodes to an empty list.
    episodes = []
    # Iterate over index/value pairs from specifications, binding each item to (index, specification).
    for index, specification in enumerate(specifications, 1):
        # Display formatted text built from the embedded values.
        print(f"Collecting MAPPO TRAINING scenario {index}/{len(specifications)}")
        # Set before to the number of entries in provider.batch_metadata.
        before = len(provider.batch_metadata)
        # Attempt the enclosed operations and route matching exceptions to the handlers below.
        try:
            # Set episode to the result of
            # CoupledNegotiationTrainingEnvironment(provider).run_episode(specification, manifest.manifest_id).
            episode = CoupledNegotiationTrainingEnvironment(provider).run_episode(
                # Supply manifest.manifest_id to CoupledNegotiationTrainingEnvironment(provider).run_episode.
                specification, manifest.manifest_id)
        # Handle RuntimeError as error using the recovery steps below.
        except RuntimeError as error:
            # Set evidence to error.args at 0 when error.args, otherwise None.
            evidence = error.args[0] if error.args else None
            # Run this branch when whether evidence has type tuple and evidence and evidence at 0 equals the text
            # 'EXECUTION_GRAPH_PHYSICAL_CONFLICT_UNORDERED'.
            if (isinstance(evidence, tuple) and evidence and
                    # Evaluate evidence at 0 equals the text 'EXECUTION_GRAPH_PHYSICAL_CONFLICT_UNORDERED' as part
                    # of the enclosing expression.
                    evidence[0] == "EXECUTION_GRAPH_PHYSICAL_CONFLICT_UNORDERED"):
                # Set blocker to a dictionary containing checkpoint, status, next_blocker,
                # failed_training_scenario_index, failed_scenario_id,...
                blocker = {
                    "checkpoint": "STEP_5J_3B_3",
                    "status": "MAPPO_BEHAVIOR_ROLLOUT_BLOCKED",
                    # Store evidence at 0 under 'next_blocker'.
                    "next_blocker": evidence[0],
                    # Store index under 'failed_training_scenario_index'.
                    "failed_training_scenario_index": index,
                    # Store the result of serializable(specification.scenario_id) under 'failed_scenario_id'.
                    "failed_scenario_id": serializable(specification.scenario_id),
                    # Store the result of serializable(evidence at 1) under 'sampled_effective_graph'.
                    "sampled_effective_graph": serializable(evidence[1]),
                    # Store the result of serializable(evidence at 2) under 'movement_path_by_vehicle'.
                    "movement_path_by_vehicle": serializable(evidence[2]),
                    # Store the number of entries in episodes under 'completed_training_scenarios_before_stop'.
                    "completed_training_scenarios_before_stop": len(episodes),
                    # Store 0 under 'policy_actions_resampled'.
                    "policy_actions_resampled": 0,
                    # Store 0 under 'branch_replacements'.
                    "branch_replacements": 0,
                    # Store 0 under 'manual_graph_edits'.
                    "manual_graph_edits": 0,
                    # Store 0 under 'optimizer_instances'.
                    "optimizer_instances": 0,
                    # Store 0 under 'backward_calls'.
                    "backward_calls": 0,
                    # Store 0 under 'parameter_updates'.
                    "parameter_updates": 0,
                    # Store the result of serializable(design['freeze'].freeze_id) under 'frozen_design_id'.
                    "frozen_design_id": serializable(design["freeze"].freeze_id),
                    # Store the result of serializable(bundle.architecture_contract_id) under
                    # 'architecture_contract_id'.
                    "architecture_contract_id": serializable(
                        # Supply bundle.architecture_contract_id to serializable.
                        bundle.architecture_contract_id),
                    # Store the result of serializable(bundle.optimization_contract_id) under
                    # 'optimization_contract_id'.
                    "optimization_contract_id": serializable(
                        # Supply bundle.optimization_contract_id to serializable.
                        bundle.optimization_contract_id),
                    # Store the result of serializable(bundle.behavior_rollout_identity) under
                    # 'behavior_rollout_identity'.
                    "behavior_rollout_identity": serializable(
                        # Supply bundle.behavior_rollout_identity to serializable.
                        bundle.behavior_rollout_identity),
                    # Store a dictionary built from bundle.initial_parameter_hashes under
                    # 'initial_parameter_hashes'.
                    "initial_parameter_hashes": dict(
                        # Supply bundle.initial_parameter_hashes to dict.
                        bundle.initial_parameter_hashes),
                    # Store the result of provider.final_parameter_hashes() under 'parameter_hashes_at_stop'.
                    "parameter_hashes_at_stop": provider.final_parameter_hashes(),
                }
                # Write the supplied text to Path('results/mappo_behavior_rollout_blocker.json').
                Path("results/mappo_behavior_rollout_blocker.json").write_text(
                    # Supply encoding as the text 'utf-8'.
                    # Supply indent as 2.
                    json.dumps(blocker, indent=2), encoding="utf-8")
            # Re-raise the active exception.
            raise
        # Append episode to episodes.
        episodes.append(episode)
        # Set metadata to provider.batch_metadata sliced by before:.
        metadata = provider.batch_metadata[before:]
        # Write the supplied text to PROGRESS_PATH.
        PROGRESS_PATH.write_text(json.dumps({
            # Store index under 'completed'.
            "completed": index,
            # Store a list of the result of _episode_summary(item, a tuple built from a lazy sequence of record
            # for record in provider.batch_metadata; retain...) for item in episodes under 'episode_summaries'.
            "episode_summaries": [_episode_summary(item, tuple(
                # Evaluate provider.batch_metadata as part of the enclosing expression.
                record for record in provider.batch_metadata
                # Evaluate a tuple built from record at 'episode_id' equals a tuple built from item.episode_id as
                # part of the enclosing expression.
                if tuple(record["episode_id"]) == tuple(item.episode_id)))
                # Supply encoding as the text 'utf-8'.
                # Supply indent as 2.
                for item in episodes]}, indent=2), encoding="utf-8")

    # Run this branch when a tuple built from the sorted values from a lazy sequence of item.scenario_id for item
    # in episodes differs from manifest.scenario_ids.
    if tuple(sorted((item.scenario_id for item in episodes), key=repr)) != (
            # Evaluate manifest.scenario_ids as part of the enclosing expression.
            manifest.scenario_ids):
        # Raise RuntimeError with the text 'TRAINING_MANIFEST_NOT_VISITED_EXACTLY_ONCE' to stop this execution
        # path.
        raise RuntimeError("TRAINING_MANIFEST_NOT_VISITED_EXACTLY_ONCE")
    # Run this branch when the negation of whether any item is true in a lazy sequence of item.decision_role
    # equals 'RESPONDER' for item in provider.final_factors.
    if not any(item.decision_role == "RESPONDER"
               # Evaluate provider.final_factors as part of the enclosing expression.
               for item in provider.final_factors):
        # Raise RuntimeError with the text 'RESPONDER_BEHAVIOR_PATH_NOT_OBSERVED' to stop this execution path.
        raise RuntimeError("RESPONDER_BEHAVIOR_PATH_NOT_OBSERVED")
    # Set replay to the result of provider.replay_all().
    replay = provider.replay_all()
    # Set final_hashes to the result of provider.final_parameter_hashes().
    final_hashes = provider.final_parameter_hashes()
    # Run this branch when a dictionary built from bundle.initial_parameter_hashes differs from final_hashes.
    if dict(bundle.initial_parameter_hashes) != final_hashes:
        # Raise RuntimeError with the text 'MAPPO_PARAMETER_CHANGED_DURING_COLLECTION' to stop this execution
        # path.
        raise RuntimeError("MAPPO_PARAMETER_CHANGED_DURING_COLLECTION")

    # Canonical first scenario reproducibility uses a fresh identical bundle and
    # sampling generator, never a performance-selected scenario or seed.
    # Set replay_provider to the result of MAPPOBehaviorActionProvider(the result of
    # build_mechanical_mappo_behavior_policy_bundle()).
    replay_provider = MAPPOBehaviorActionProvider(
        # Supply the result of build_mechanical_mappo_behavior_policy_bundle() to MAPPOBehaviorActionProvider.
        build_mechanical_mappo_behavior_policy_bundle())
    # Set replay_episode to the result of
    # CoupledNegotiationTrainingEnvironment(replay_provider).run_episode(specifications at 0,
    # manifest.manifest_id).
    replay_episode = CoupledNegotiationTrainingEnvironment(
        # Supply manifest.manifest_id to CoupledNegotiationTrainingEnvironment(replay_provider).run_episode.
        replay_provider).run_episode(specifications[0], manifest.manifest_id)
    # Set canonical_original to a tuple built from a lazy sequence of record for record in
    # provider.batch_metadata; retain entries satisfying a tuple built from record['episode_id'] equals a tuple
    # built from episodes[0].episode_id.
    canonical_original = tuple(record for record in provider.batch_metadata
                               # Evaluate a tuple built from record at 'episode_id' equals a tuple built from
                               # episodes[0].episode_id as part of the enclosing expression.
                               if tuple(record["episode_id"]) ==
                               # Evaluate a tuple built from episodes[0].episode_id as part of the enclosing
                               # expression.
                               tuple(episodes[0].episode_id))
    # Set canonical_replay to a tuple built from replay_provider.batch_metadata.
    canonical_replay = tuple(replay_provider.batch_metadata)
    # Set trace_equal to canonical_original equals canonical_replay.
    trace_equal = canonical_original == canonical_replay
    # Set physical_trace to a callback that returns a tuple containing item.completed_vehicle_count,
    # item.physical_speed_command_count, item.conflict_zone_execution_plan_count,...
    physical_trace = lambda item: (
        # Include item.physical_speed_command_count in this tuple.
        item.completed_vehicle_count, item.physical_speed_command_count,
        # Include item.conflict_zone_execution_plan_count in this tuple.
        item.conflict_zone_execution_plan_count,
        # Include item.team_travel_time_seconds in this tuple.
        item.team_travel_time_seconds, item.raw_shared_team_reward)
    # Set physical_equal to the result of physical_trace(episodes at 0) equals the result of
    # physical_trace(replay_episode).
    physical_equal = physical_trace(episodes[0]) == physical_trace(replay_episode)
    # Run this branch when the negation of trace_equal or the negation of physical_equal.
    if not trace_equal or not physical_equal:
        # Raise RuntimeError with the text 'MAPPO_BEHAVIOR_REPRODUCIBILITY_MISMATCH' to stop this execution path.
        raise RuntimeError("MAPPO_BEHAVIOR_REPRODUCIBILITY_MISMATCH")

    # Set proposer to a tuple built from a lazy sequence of x for x in provider.final_factors; retain entries
    # satisfying x.decision_role equals the text 'PROPOSER'.
    proposer = tuple(x for x in provider.final_factors
                     # Evaluate x.decision_role equals the text 'PROPOSER' as part of the enclosing expression.
                     if x.decision_role == "PROPOSER")
    # Set responder to a tuple built from a lazy sequence of x for x in provider.final_factors; retain entries
    # satisfying x.decision_role equals the text 'RESPONDER'.
    responder = tuple(x for x in provider.final_factors
                      # Evaluate x.decision_role equals the text 'RESPONDER' as part of the enclosing expression.
                      if x.decision_role == "RESPONDER")
    # Set actions to a dictionary of name mapped to the sum of a lazy sequence of x.selected_semantic_action
    # equals name for x in provider.final_factors for name in a tuple containing the text 'KEEP_CLAIM', the text
    # 'RELINQUISH_CLAIM', the text 'ACCEPT_RELINQUISHMENT', the text...
    actions = {name: sum(x.selected_semantic_action == name
                         # Evaluate a tuple containing the text 'KEEP_CLAIM', the text 'RELINQUISH_CLAIM', the
                         # text 'ACCEPT_RELINQUISHMENT', the text... as part of the enclosing expression.
                         for x in provider.final_factors) for name in (
        "KEEP_CLAIM", "RELINQUISH_CLAIM",
        "ACCEPT_RELINQUISHMENT", "REJECT_RELINQUISHMENT")}
    # Set metadata to a tuple built from provider.batch_metadata.
    metadata = tuple(provider.batch_metadata)
    # Set payload to a dictionary containing checkpoint, status, step_5j_3b_4_readiness,
    # behavior_rollout_identity,...
    payload = {
        "checkpoint": "STEP_5J_3B_3",
        "status": "REAL_MAPPO_BEHAVIOR_ROLLOUT_VALIDATED",
        "step_5j_3b_4_readiness": "READY_FOR_FIRST_MECHANICAL_PPO_UPDATE",
        # Store the result of serializable(bundle.behavior_rollout_identity) under 'behavior_rollout_identity'.
        "behavior_rollout_identity": serializable(
            # Supply bundle.behavior_rollout_identity to serializable.
            bundle.behavior_rollout_identity),
        # Store the result of serializable(design['freeze'].freeze_id) under 'frozen_design_id'.
        "frozen_design_id": serializable(design["freeze"].freeze_id),
        # Store the result of serializable(bundle.architecture_contract_id) under 'architecture_contract_id'.
        "architecture_contract_id": serializable(
            # Supply bundle.architecture_contract_id to serializable.
            bundle.architecture_contract_id),
        # Store the result of serializable(bundle.optimization_contract_id) under 'optimization_contract_id'.
        "optimization_contract_id": serializable(
            # Supply bundle.optimization_contract_id to serializable.
            bundle.optimization_contract_id),
        # Store the result of serializable(manifest.manifest_id) under 'training_manifest_id'.
        "training_manifest_id": serializable(manifest.manifest_id),
        "seed_derivation_method":
            "SHA256_CONTRACT_AND_BEHAVIOR_IDENTITY_COMPONENT_DERIVATION",
        # Store a dictionary built from bundle.component_seeds under 'derived_component_seeds'.
        "derived_component_seeds": dict(bundle.component_seeds),
        # Store 0 under 'hard_coded_training_seed_values'.
        "hard_coded_training_seed_values": 0,
        # Store False under 'seed_selected_by_performance'.
        "seed_selected_by_performance": False,
        # Store a dictionary built from bundle.initial_parameter_hashes under 'initial_parameter_hashes'.
        "initial_parameter_hashes": dict(bundle.initial_parameter_hashes),
        # Store final_hashes under 'final_parameter_hashes'.
        "final_parameter_hashes": final_hashes,
        # Store True under 'parameter_hashes_unchanged'.
        "parameter_hashes_unchanged": True,
        # Store a dictionary containing frozen_gnn, proposer_actor, responder_actor, centralized_critic under
        # 'model_counts'.
        # Store 1 under 'frozen_gnn'.
        # Store 1 under 'proposer_actor'.
        "model_counts": {"frozen_gnn": 1, "proposer_actor": 1,
                         # Store 1 under 'responder_actor'.
                         # Store 1 under 'centralized_critic'.
                         "responder_actor": 1, "centralized_critic": 1},
        # Store a dictionary containing gnn, proposer, responder, critic under 'trainable_parameter_counts'.
        "trainable_parameter_counts": {
            # Store the sum of a lazy sequence of the result of x.numel() for x in the result of
            # bundle.gnn.parameters(); retain entries satisfying x.requires_grad under 'gnn'.
            "gnn": sum(x.numel() for x in bundle.gnn.parameters()
                       # Evaluate x.requires_grad as part of the enclosing expression.
                       if x.requires_grad),
            # Store the sum of a lazy sequence of the result of x.numel() for x in the result of
            # bundle.proposer_actor.parameters(); retain entries satisfying x.requires_grad under 'proposer'.
            "proposer": sum(x.numel() for x in
                            # Evaluate the result of bundle.proposer_actor.parameters() as part of the enclosing
                            # expression.
                            bundle.proposer_actor.parameters()
                            # Evaluate x.requires_grad as part of the enclosing expression.
                            if x.requires_grad),
            # Store the sum of a lazy sequence of the result of x.numel() for x in the result of
            # bundle.responder_actor.parameters(); retain entries satisfying x.requires_grad under 'responder'.
            "responder": sum(x.numel() for x in
                             # Evaluate the result of bundle.responder_actor.parameters() as part of the enclosing
                             # expression.
                             bundle.responder_actor.parameters()
                             # Evaluate x.requires_grad as part of the enclosing expression.
                             if x.requires_grad),
            # Store the sum of a lazy sequence of the result of x.numel() for x in the result of
            # bundle.centralized_critic.parameters(); retain entries satisfying x.requires_grad under 'critic'.
            "critic": sum(x.numel() for x in
                          # Evaluate the result of bundle.centralized_critic.parameters() as part of the enclosing
                          # expression.
                          bundle.centralized_critic.parameters()
                          # Evaluate x.requires_grad as part of the enclosing expression.
                          if x.requires_grad)},
        # Store 1 under 'training_manifest_passes'.
        "training_manifest_passes": 1,
        # Store the number of entries in episodes under 'training_scenarios_attempted'.
        "training_scenarios_attempted": len(episodes),
        # Store the sum of a lazy sequence of x.episode_completion_status equals the text 'COMPLETE' for x in
        # episodes under 'training_scenarios_completed'.
        "training_scenarios_completed": sum(
            # Evaluate x.episode_completion_status equals the text 'COMPLETE' as part of the enclosing expression.
            x.episode_completion_status == "COMPLETE" for x in episodes),
        # Store 0 under 'validation_performance_runs'.
        "validation_performance_runs": 0,
        # Store 0 under 'held_out_performance_runs'.
        "held_out_performance_runs": 0,
        # Store a list of the result of _episode_summary(item, a tuple built from a lazy sequence of record for
        # record in metadata; retain entries...) for item in episodes under 'episode_summaries'.
        "episode_summaries": [_episode_summary(
            # Supply a tuple built from a lazy sequence of record for record in metadata; retain entries
            # satisfying a tuple built from record['episode_id'] equals a tuple built from item.episode_id to
            # _episode_summary.
            item, tuple(record for record in metadata
                        # Evaluate a tuple built from record at 'episode_id' equals a tuple built from
                        # item.episode_id as part of the enclosing expression.
                        if tuple(record["episode_id"]) == tuple(item.episode_id)))
            # Evaluate episodes as part of the enclosing expression.
            for item in episodes],
        # Store the number of entries in metadata under 'joint_decision_batch_count'.
        "joint_decision_batch_count": len(metadata),
        # Store the number of entries in proposer under 'proposer_ppo_sample_count'.
        "proposer_ppo_sample_count": len(proposer),
        # Store the number of entries in responder under 'responder_ppo_sample_count'.
        "responder_ppo_sample_count": len(responder),
        # Store the number of entries in provider.final_factors under 'total_ppo_sample_count'.
        "total_ppo_sample_count": len(provider.final_factors),
        # Store the number of entries in provider.final_critics under 'critic_sample_count'.
        "critic_sample_count": len(provider.final_critics),
        # Store the sum of a lazy sequence of x['proposer_count'] plus x['responder_count'] is greater than 1 for
        # x in metadata under 'multi_factor_decision_batch_count'.
        "multi_factor_decision_batch_count": sum(
            # Evaluate x at 'proposer_count' plus x at 'responder_count' is greater than 1 as part of the
            # enclosing expression.
            x["proposer_count"] + x["responder_count"] > 1 for x in metadata),
        # Store the sum of a lazy sequence of x at 'proposal_count' for x in metadata under 'real_proposal_count'.
        "real_proposal_count": sum(x["proposal_count"] for x in metadata),
        # Store actions under 'action_counts'.
        "action_counts": actions,
        # Store the sum of a lazy sequence of x at 'cycle_detected' for x in metadata under
        # 'cyclic_policy_outcome_count'.
        "cyclic_policy_outcome_count": sum(x["cycle_detected"] for x in metadata),
        # Store the sum of a lazy sequence of x at 'coordination_edge_count' for x in metadata under
        # 'coordination_edge_count'.
        "coordination_edge_count": sum(
            # Evaluate x at 'coordination_edge_count' as part of the enclosing expression.
            x["coordination_edge_count"] for x in metadata),
        # Store the sum of a lazy sequence of x at 'physical_execution_edge_count' for x in metadata under
        # 'physical_execution_edge_count'.
        "physical_execution_edge_count": sum(
            # Evaluate x at 'physical_execution_edge_count' as part of the enclosing expression.
            x["physical_execution_edge_count"] for x in metadata),
        # Store the sum of a lazy sequence of x at 'nonphysical_coordination_edge_count' for x in metadata under
        # 'nonphysical_coordination_edge_count'.
        "nonphysical_coordination_edge_count": sum(
            # Evaluate x at 'nonphysical_coordination_edge_count' as part of the enclosing expression.
            x["nonphysical_coordination_edge_count"] for x in metadata),
        # Store the sum of a lazy sequence of x at 'coordination_cycle_detected' for x in metadata under
        # 'coordination_cycle_count'.
        "coordination_cycle_count": sum(
            # Evaluate x at 'coordination_cycle_detected' as part of the enclosing expression.
            x["coordination_cycle_detected"] for x in metadata),
        # Store the sum of a lazy sequence of x at 'physical_execution_cycle_detected' for x in metadata under
        # 'physical_execution_cycle_count'.
        "physical_execution_cycle_count": sum(
            # Evaluate x at 'physical_execution_cycle_detected' as part of the enclosing expression.
            x["physical_execution_cycle_detected"] for x in metadata),
        # Store the sum of a lazy sequence of x at 'graph_executable' for x in metadata under
        # 'executable_policy_outcome_count'.
        "executable_policy_outcome_count": sum(x["graph_executable"] for x in metadata),
        # Store provider.joint_protocol_evaluations under 'joint_protocol_evaluations'.
        "joint_protocol_evaluations": provider.joint_protocol_evaluations,
        # Store provider.manual_graph_edits under 'manual_graph_edits'.
        "manual_graph_edits": provider.manual_graph_edits,
        # Store 0 under 'executable_branch_replacements'.
        "executable_branch_replacements": 0,
        "branch_enumerator_action_selections":
            # Evaluate provider.branch_enumerator_action_selections as part of the enclosing expression.
            provider.branch_enumerator_action_selections,
        # Store the sum of a lazy sequence of x.collision_count for x in episodes under 'collisions'.
        "collisions": sum(x.collision_count for x in episodes),
        # Store the sum of a lazy sequence of x.blocked_zone_entry_violation_count for x in episodes under
        # 'blocked_zone_violations'.
        "blocked_zone_violations": sum(
            # Evaluate x.blocked_zone_entry_violation_count as part of the enclosing expression.
            x.blocked_zone_entry_violation_count for x in episodes),
        # Store the sum of a lazy sequence of x.team_travel_time_seconds for x in episodes under
        # 'team_travel_time_seconds'.
        "team_travel_time_seconds": sum(
            # Evaluate x.team_travel_time_seconds as part of the enclosing expression.
            x.team_travel_time_seconds for x in episodes),
        # Store the sum of a lazy sequence of x.raw_shared_team_reward for x in episodes under
        # 'raw_shared_team_reward'.
        "raw_shared_team_reward": sum(x.raw_shared_team_reward for x in episodes),
        # Store the number of entries in provider.final_critics under 'return_record_count'.
        "return_record_count": len(provider.final_critics),
        # Store the number of entries in provider.final_critics under 'advantage_record_count'.
        "advantage_record_count": len(provider.final_critics),
        # Store False under 'critic_samples_duplicated_per_policy_factor'.
        "critic_samples_duplicated_per_policy_factor": False,
        # Store the result of serializable(provider.final_factors) under 'policy_factors'.
        "policy_factors": serializable(provider.final_factors),
        # Store the result of serializable(provider.final_critics) under 'critic_samples'.
        "critic_samples": serializable(provider.final_critics),
        # Store the result of serializable(metadata) under 'joint_batch_metadata'.
        "joint_batch_metadata": serializable(metadata),
        # Store a dictionary containing samples_replayed, finite_log_probabilities, hard_masks_exact,... under
        # 'policy_replay'.
        "policy_replay": {
            # Store the number of entries in replay under 'samples_replayed'.
            "samples_replayed": len(replay),
            # Store whether every item is true in a lazy sequence of whether x.behavior_policy_log_probability
            # contains finite numeric values for x in provider.final_factors under 'finite_log_probabilities'.
            "finite_log_probabilities": all(
                # Evaluate whether x.behavior_policy_log_probability contains finite numeric values as part of the
                # enclosing expression.
                __import__("math").isfinite(x.behavior_policy_log_probability)
                # Evaluate provider.final_factors as part of the enclosing expression.
                for x in provider.final_factors),
            # Store True under 'hard_masks_exact'.
            "hard_masks_exact": True,
            # Store True under 'old_current_log_probabilities_exact'.
            "old_current_log_probabilities_exact": True,
            # Store whether every item is true in a lazy sequence of x at 3 equals 1.0 for x in replay under
            # 'importance_ratios_exactly_one'.
            "importance_ratios_exactly_one": all(x[3] == 1.0 for x in replay)},
        # Store a dictionary containing semantic_action_and_logprob_trace_exact, effective_graph_trace_exact,...
        # under 'canonical_first_scenario_reproducibility'.
        "canonical_first_scenario_reproducibility": {
            # Store trace_equal under 'semantic_action_and_logprob_trace_exact'.
            "semantic_action_and_logprob_trace_exact": trace_equal,
            # Store trace_equal under 'effective_graph_trace_exact'.
            "effective_graph_trace_exact": trace_equal,
            # Store physical_equal under 'physical_event_trace_exact'.
            "physical_event_trace_exact": physical_equal},
        # Store 0 under 'profiling_ppo_samples_reused'.
        "profiling_ppo_samples_reused": 0,
        # Store 0 under 'route_truth_actor_fields'.
        "route_truth_actor_fields": 0,
        # Store 0 under 'future_outcome_action_selection_fields'.
        "future_outcome_action_selection_fields": 0,
        # Store 0 under 'optimizer_instances'.
        "optimizer_instances": 0,
        # Store 0 under 'backward_calls'.
        "backward_calls": 0,
        # Store 0 under 'parameter_updates'.
        "parameter_updates": 0,
        # Store 0 under 'ppo_optimization_epochs_executed'.
        "ppo_optimization_epochs_executed": 0,
        # Store 0 under 'model_checkpoints'.
        "model_checkpoints": 0,
        # Store 0 under 'learned_main_actions'.
        "learned_main_actions": 0,
        # Store 0 under 'new_reward_terms'.
        "new_reward_terms": 0,
    }
    # Run this branch when payload at 'collisions'.
    if payload["collisions"]:
        # Raise RuntimeError with the text 'MAPPO_BEHAVIOR_ROLLOUT_COLLISION_OBSERVED' to stop this execution
        # path.
        raise RuntimeError("MAPPO_BEHAVIOR_ROLLOUT_COLLISION_OBSERVED")
    # Run this branch when payload at 'blocked_zone_violations'.
    if payload["blocked_zone_violations"]:
        # Raise RuntimeError with the text 'MAPPO_BEHAVIOR_BLOCKED_ZONE_VIOLATION' to stop this execution path.
        raise RuntimeError("MAPPO_BEHAVIOR_BLOCKED_ZONE_VIOLATION")
    # Set output_path to the result of Path(output_path).
    output_path = Path(output_path)
    # Write the supplied text to output_path.
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    # Return payload to the caller.
    return payload
