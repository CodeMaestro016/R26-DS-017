"""Step 5J.3C.1 two-replication closed-loop learning probe."""

# Import hashlib for use in this module.
import hashlib
# Import json for use in this module.
import json
# Import os for use in this module.
import os
# Import Path from pathlib for the operations below.
from pathlib import Path
# Import perf_counter from time for the operations below.
from time import perf_counter

# Import ScenarioRole, build_design from experimentation for the operations below.
from experimentation import ScenarioRole, build_design
# Import _specification from negotiation_execution.replay for the operations below.
from negotiation_execution.replay import _specification

# Import build_mechanical_adam_optimization_contract from .adam_contract for the operations below.
from .adam_contract import build_mechanical_adam_optimization_contract
# Import build_mechanical_pilot_architecture_contract, deterministic_initialization_seed from
# .architecture_contract for the operations below.
from .architecture_contract import (
    build_mechanical_pilot_architecture_contract,
    deterministic_initialization_seed)
# Import serializable from .behavior_rollout for the operations below.
from .behavior_rollout import serializable
# Import CoupledNegotiationTrainingEnvironment from .environment for the operations below.
from .environment import CoupledNegotiationTrainingEnvironment
# Import MAPPOBehaviorActionProvider, build_mechanical_mappo_behavior_policy_bundle from .mappo_provider for the
# operations below.
from .mappo_provider import (
    MAPPOBehaviorActionProvider, build_mechanical_mappo_behavior_policy_bundle)
# Import paired_difference_summary, two_replication_sample_statistics from .pilot_analysis for the operations
# below.
from .pilot_analysis import (
    paired_difference_summary, two_replication_sample_statistics)
# Import MechanicalMAPPOTrainer from .ppo_trainer for the operations below.
from .ppo_trainer import MechanicalMAPPOTrainer
# Import MAPPOBehaviorRolloutIdentity, parameter_hash from .rollout for the operations below.
from .rollout import MAPPOBehaviorRolloutIdentity, parameter_hash


# Set EVIDENCE_PATH to the result of Path(the text 'results/mappo_closed_loop_pilot_evidence.json').
EVIDENCE_PATH = Path("results/mappo_closed_loop_pilot_evidence.json")
# Set PROGRESS_PATH to the result of Path(the text 'results/mappo_closed_loop_pilot_progress.json').
PROGRESS_PATH = Path("results/mappo_closed_loop_pilot_progress.json")


# Replace a JSON record only after its complete successor is durable.
# Input path: the path or path object supplied by the caller.
# Input payload: the supplied payload.
# Output: no explicit value; normal completion returns None.
def atomic_write_json(path, payload):
    """Replace a JSON record only after its complete successor is durable."""
    # Set path to the result of Path(path).
    path = Path(path)
    # Create the directory requested by path.parent.
    path.parent.mkdir(parents=True, exist_ok=True)
    # Set temporary to the result of path.with_suffix(path.suffix plus the text '.tmp').
    temporary = path.with_suffix(path.suffix + ".tmp")
    # Write the supplied text to temporary.
    temporary.write_text(json.dumps(serializable(payload), indent=2),
                         # Supply encoding as the text 'utf-8'.
                         encoding="utf-8")
    # Call os.replace with the supplied arguments.
    os.replace(temporary, path)


# Identity using the inputs and processing steps below.
# Input design: the supplied design.
# Input architecture: the supplied architecture.
# Input optimization: the supplied optimization.
# Input manifest: the supplied manifest.
# Input replication: the supplied replication.
# Input label: the supplied label.
# Output: a tuple containing label, the hexadecimal digest from hashlib.sha256(repr(fields).encode()).
def _identity(design, architecture, optimization, manifest, replication, label):
    # Set fields to a tuple containing design['freeze'].freeze_id, architecture.contract_id,
    # optimization.contract_id, manifest.manifest_id,...
    fields = (design["freeze"].freeze_id, architecture.contract_id,
              # Include optimization.contract_id in this tuple.
              optimization.contract_id, manifest.manifest_id,
              # Include replication in this tuple.
              replication, label)
    # Return a tuple containing label, the hexadecimal digest from hashlib.sha256(repr(fields).encode()) to the
    # caller.
    return (label, hashlib.sha256(repr(fields).encode()).hexdigest())


# Current hashes using the inputs and processing steps below.
# Input bundle: the supplied bundle.
# Output: a dictionary containing gnn, proposer, responder, critic.
def _current_hashes(bundle):
    # Return a dictionary containing gnn, proposer, responder, critic to the caller.
    return {"gnn": parameter_hash(bundle.gnn),
            # Store the result of parameter_hash(bundle.proposer_actor) under 'proposer'.
            "proposer": parameter_hash(bundle.proposer_actor),
            # Store the result of parameter_hash(bundle.responder_actor) under 'responder'.
            "responder": parameter_hash(bundle.responder_actor),
            # Store the result of parameter_hash(bundle.centralized_critic) under 'critic'.
            "critic": parameter_hash(bundle.centralized_critic)}


# Pass rollout payload using the inputs and processing steps below.
# Input design: the supplied design.
# Input architecture: the supplied architecture.
# Input optimization: the supplied optimization.
# Input manifest: the supplied manifest.
# Input pass_identity: the supplied pass identity.
# Input bundle: the supplied bundle.
# Input provider: the supplied provider.
# Output: a dictionary containing checkpoint, status, step_5j_3b_4_readiness, behavior_rollout_identity,...
def _pass_rollout_payload(design, architecture, optimization, manifest,
                          # Declare pass_identity, bundle, provider as input parameters.
                          pass_identity, bundle, provider):
    # Set factors to provider.final_factors.
    factors = provider.final_factors
    # Set critics to provider.final_critics.
    critics = provider.final_critics
    # Set hashes to the result of _current_hashes(bundle).
    hashes = _current_hashes(bundle)
    # Return a dictionary containing checkpoint, status, step_5j_3b_4_readiness, behavior_rollout_identity,... to
    # the caller.
    return {
        "checkpoint": "STEP_5J_3B_3",
        "status": "REAL_MAPPO_BEHAVIOR_ROLLOUT_VALIDATED",
        "step_5j_3b_4_readiness": "READY_FOR_FIRST_MECHANICAL_PPO_UPDATE",
        # Store a dictionary containing rollout_id under 'behavior_rollout_identity'.
        "behavior_rollout_identity": {
            # Store the result of serializable(pass_identity) under 'rollout_id'.
            "rollout_id": serializable(pass_identity)},
        # Store the result of serializable(design['freeze'].freeze_id) under 'frozen_design_id'.
        "frozen_design_id": serializable(design["freeze"].freeze_id),
        # Store the result of serializable(architecture.contract_id) under 'architecture_contract_id'.
        "architecture_contract_id": serializable(architecture.contract_id),
        # Store the result of serializable(optimization.contract_id) under 'optimization_contract_id'.
        "optimization_contract_id": serializable(optimization.contract_id),
        # Store the result of serializable(manifest.manifest_id) under 'training_manifest_id'.
        "training_manifest_id": serializable(manifest.manifest_id),
        # Store hashes under 'initial_parameter_hashes'.
        "initial_parameter_hashes": hashes,
        # Store the result of serializable(factors) under 'policy_factors'.
        "policy_factors": serializable(factors),
        # Store the result of serializable(critics) under 'critic_samples'.
        "critic_samples": serializable(critics),
        # Store the number of entries in factors under 'total_ppo_sample_count'.
        "total_ppo_sample_count": len(factors),
        # Store the number of entries in critics under 'critic_sample_count'.
        "critic_sample_count": len(critics),
        # Store 0 under 'profiling_ppo_samples_reused'.
        "profiling_ppo_samples_reused": 0,
    }


# Collect controlled training pass using the inputs and processing steps below.
# Input design: the supplied design.
# Input architecture: the supplied architecture.
# Input optimization: the supplied optimization.
# Input manifest: the supplied manifest.
# Input specifications: the supplied specifications.
# Input bundle: the supplied bundle.
# Input replication_identity: the supplied replication identity.
# Input pass_label: the supplied pass label.
# Input progress_context: the supplied progress context.
# Input progress_path: the supplied progress path.
# Output: a tuple containing metrics, payload.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def collect_controlled_training_pass(*, design, architecture, optimization,
                                     # Declare manifest, specifications, bundle as input parameters.
                                     manifest, specifications, bundle,
                                     # Declare replication_identity, pass_label as input parameters.
                                     replication_identity, pass_label,
                                     # Declare progress_context as input parameter.
                                     progress_context,
                                     # Declare progress_path as input parameter.
                                     progress_path=PROGRESS_PATH):
    # Set pass_identity to the result of _identity(design, architecture, optimization, manifest,
    # replication_identity, pass_label).
    pass_identity = _identity(
        # Supply architecture to _identity.
        design, architecture, optimization, manifest,
        # Supply replication_identity to _identity.
        replication_identity, pass_label)
    # Set sampling_seed to the result of deterministic_initialization_seed(architecture.contract_id, a tuple
    # containing replication_identity, pass_label, the text...).
    sampling_seed = deterministic_initialization_seed(
        # Supply architecture.contract_id to deterministic_initialization_seed.
        architecture.contract_id,
        # Supply a tuple containing replication_identity, pass_label, the text 'POLICY_ACTION_SAMPLING' to
        # deterministic_initialization_seed.
        (replication_identity, pass_label, "POLICY_ACTION_SAMPLING"))
    # Set provider to the result of MAPPOBehaviorActionProvider(bundle).
    provider = MAPPOBehaviorActionProvider(bundle, sampling_seed=sampling_seed)
    # Set initial_hashes to the result of _current_hashes(bundle).
    initial_hashes = _current_hashes(bundle)
    # Set started to the result of perf_counter().
    started = perf_counter()
    # Set episodes to an empty list.
    episodes = []
    # Iterate over index/value pairs from specifications, binding each item to (index, specification).
    for index, specification in enumerate(specifications, 1):
        # Display formatted text built from the embedded values.
        print(f"{replication_identity[-1]} {pass_label} scenario "
              # Evaluate {len(specifications)} as part of the enclosing expression.
              f"{index}/{len(specifications)}")
        # Append the result of CoupledNegotiationTrainingEnvironment(provider).run_episode(specification,
        # manifest.manifest_id) to episodes.
        episodes.append(CoupledNegotiationTrainingEnvironment(provider).run_episode(
            # Supply manifest.manifest_id to CoupledNegotiationTrainingEnvironment(provider).run_episode.
            specification, manifest.manifest_id))
        # Call atomic_write_json with the supplied arguments.
        atomic_write_json(progress_path, {
            # Store pass_label under 'active_pass'.
            **progress_context, "active_pass": pass_label,
            # Store index under 'active_pass_scenarios_completed'.
            "active_pass_scenarios_completed": index,
            # Store the sum of a lazy sequence of item.team_travel_time_seconds for item in episodes under
            # 'active_pass_team_travel_time_seconds'.
            "active_pass_team_travel_time_seconds": sum(
                # Evaluate item.team_travel_time_seconds as part of the enclosing expression.
                item.team_travel_time_seconds for item in episodes)})
    # Set final_hashes to the result of _current_hashes(bundle).
    final_hashes = _current_hashes(bundle)
    # Run this branch when final_hashes differs from initial_hashes.
    if final_hashes != initial_hashes:
        # Raise RuntimeError with the text 'POLICY_PARAMETER_CHANGED_DURING_COLLECTION' to stop this execution
        # path.
        raise RuntimeError("POLICY_PARAMETER_CHANGED_DURING_COLLECTION")
    # Run this branch when whether any item is true in a lazy sequence of item.collision_count for item in
    # episodes.
    if any(item.collision_count for item in episodes):
        # Raise RuntimeError with the text 'CONTROLLED_PILOT_COLLISION_OBSERVED' to stop this execution path.
        raise RuntimeError("CONTROLLED_PILOT_COLLISION_OBSERVED")
    # Run this branch when whether any item is true in a lazy sequence of item.blocked_zone_entry_violation_count
    # for item in episodes.
    if any(item.blocked_zone_entry_violation_count for item in episodes):
        # Raise RuntimeError with the text 'CONTROLLED_PILOT_BLOCKED_ZONE_VIOLATION' to stop this execution path.
        raise RuntimeError("CONTROLLED_PILOT_BLOCKED_ZONE_VIOLATION")
    # Set factors to a tuple built from provider.final_factors.
    factors = tuple(provider.final_factors)
    # Set metadata to a tuple built from provider.batch_metadata.
    metadata = tuple(provider.batch_metadata)
    # Set action_names to a tuple containing the text 'KEEP_CLAIM', the text 'RELINQUISH_CLAIM', the text
    # 'ACCEPT_RELINQUISHMENT', the text...
    action_names = ("KEEP_CLAIM", "RELINQUISH_CLAIM",
                    "ACCEPT_RELINQUISHMENT", "REJECT_RELINQUISHMENT")
    # Set action_counts to a dictionary of name mapped to the sum of a lazy sequence of
    # item.selected_semantic_action equals name for item in factors for name in action_names.
    action_counts = {name: sum(item.selected_semantic_action == name
                               # Evaluate action_names as part of the enclosing expression.
                               for item in factors) for name in action_names}
    # Set scenario_metrics to an empty list.
    scenario_metrics = []
    # Iterate over episodes, binding each item to episode.
    for episode in episodes:
        # Set episode_factors to a tuple built from a lazy sequence of item for item in factors; retain entries
        # satisfying item.episode_id equals episode.episode_id.
        episode_factors = tuple(item for item in factors
                                # Evaluate item.episode_id equals episode.episode_id as part of the enclosing
                                # expression.
                                if item.episode_id == episode.episode_id)
        # Set episode_metadata to a tuple built from a lazy sequence of item for item in metadata; retain entries
        # satisfying item at 'episode_id' equals episode.episode_id.
        episode_metadata = tuple(item for item in metadata
                                 # Evaluate item at 'episode_id' equals episode.episode_id as part of the
                                 # enclosing expression.
                                 if item["episode_id"] == episode.episode_id)
        # Append a dictionary containing scenario_id, team_travel_time_seconds, raw_reward, proposer_count,
        # responder_count,... to scenario_metrics.
        scenario_metrics.append({
            # Store the result of serializable(episode.scenario_id) under 'scenario_id'.
            "scenario_id": serializable(episode.scenario_id),
            # Store episode.team_travel_time_seconds under 'team_travel_time_seconds'.
            "team_travel_time_seconds": episode.team_travel_time_seconds,
            # Store episode.raw_shared_team_reward under 'raw_reward'.
            "raw_reward": episode.raw_shared_team_reward,
            # Store the sum of a lazy sequence of x.decision_role equals the text 'PROPOSER' for x in
            # episode_factors under 'proposer_count'.
            "proposer_count": sum(x.decision_role == "PROPOSER"
                                  # Evaluate episode_factors as part of the enclosing expression.
                                  for x in episode_factors),
            # Store the sum of a lazy sequence of x.decision_role equals the text 'RESPONDER' for x in
            # episode_factors under 'responder_count'.
            "responder_count": sum(x.decision_role == "RESPONDER"
                                   # Evaluate episode_factors as part of the enclosing expression.
                                   for x in episode_factors),
            # Store a dictionary of name mapped to the sum of a lazy sequence of x.selected_semantic_action equals
            # name for x in episode_factors for name in action_names under 'action_counts'.
            "action_counts": {name: sum(x.selected_semantic_action == name
                                         # Evaluate episode_factors as part of the enclosing expression.
                                         for x in episode_factors)
                              # Evaluate action_names as part of the enclosing expression.
                              for name in action_names},
            # Store the sum of a lazy sequence of x at 'coordination_cycle_detected' for x in episode_metadata
            # under 'coordination_cycle_count'.
            "coordination_cycle_count": sum(
                # Evaluate x at 'coordination_cycle_detected' as part of the enclosing expression.
                x["coordination_cycle_detected"] for x in episode_metadata),
            # Store the sum of a lazy sequence of x at 'physical_execution_cycle_detected' for x in
            # episode_metadata under 'physical_cycle_count'.
            "physical_cycle_count": sum(
                # Evaluate x at 'physical_execution_cycle_detected' as part of the enclosing expression.
                x["physical_execution_cycle_detected"] for x in episode_metadata),
            # Store the sum of a lazy sequence of x at 'graph_executable' for x in episode_metadata under
            # 'physical_executable_outcome_count'.
            "physical_executable_outcome_count": sum(
                # Evaluate x at 'graph_executable' as part of the enclosing expression.
                x["graph_executable"] for x in episode_metadata),
            # Store episode.completed_vehicle_count under 'completed_vehicle_count'.
            "completed_vehicle_count": episode.completed_vehicle_count,
            # Store episode.collision_count under 'collision_count'.
            "collision_count": episode.collision_count,
            "blocked_zone_violation_count":
                # Evaluate episode.blocked_zone_entry_violation_count as part of the enclosing expression.
                episode.blocked_zone_entry_violation_count,
            "native_safety_intervention_count":
                # Evaluate episode.native_sumo_safety_intervention_count as part of the enclosing expression.
                episode.native_sumo_safety_intervention_count,
            # Store the number of entries in episode_factors under 'policy_factor_count'.
            "policy_factor_count": len(episode_factors),
            # Store episode.sumo_step_count under 'sumo_step_count'.
            "sumo_step_count": episode.sumo_step_count,
            # Store episode.wall_clock_runtime_seconds under 'wall_clock_runtime_seconds'.
            "wall_clock_runtime_seconds": episode.wall_clock_runtime_seconds})
    # Set metrics to a dictionary containing pass_identity, sampling_seed_identity, derived_sampling_seed,...
    metrics = {
        # Store the result of serializable(pass_identity) under 'pass_identity'.
        "pass_identity": serializable(pass_identity),
        # Store the result of serializable(a tuple containing replication_identity, pass_label, the text
        # 'POLICY_ACTION_SAMPLING') under 'sampling_seed_identity'.
        "sampling_seed_identity": serializable((
            # Include replication_identity in this tuple.
            replication_identity, pass_label, "POLICY_ACTION_SAMPLING")),
        # Store sampling_seed under 'derived_sampling_seed'.
        "derived_sampling_seed": sampling_seed,
        # Store the result of serializable(provider.policy_parameter_identity) under 'policy_parameter_identity'.
        "policy_parameter_identity": serializable(
            # Supply provider.policy_parameter_identity to serializable.
            provider.policy_parameter_identity),
        # Store final_hashes at 'critic' under 'critic_identity'.
        "critic_identity": final_hashes["critic"],
        # Store the number of entries in episodes under 'scenario_count'.
        "scenario_count": len(episodes),
        # Store scenario_metrics under 'scenario_metrics'.
        "scenario_metrics": scenario_metrics,
        # Store the sum of a lazy sequence of item.team_travel_time_seconds for item in episodes under
        # 'team_travel_time_seconds'.
        "team_travel_time_seconds": sum(
            # Evaluate item.team_travel_time_seconds as part of the enclosing expression.
            item.team_travel_time_seconds for item in episodes),
        # Store the sum of a lazy sequence of item.raw_shared_team_reward for item in episodes under 'raw_reward'.
        "raw_reward": sum(item.raw_shared_team_reward for item in episodes),
        # Store the sum of a lazy sequence of x.decision_role equals the text 'PROPOSER' for x in factors under
        # 'proposer_count'.
        "proposer_count": sum(x.decision_role == "PROPOSER" for x in factors),
        # Store the sum of a lazy sequence of x.decision_role equals the text 'RESPONDER' for x in factors under
        # 'responder_count'.
        "responder_count": sum(x.decision_role == "RESPONDER" for x in factors),
        # Store the number of entries in factors under 'policy_factor_count'.
        "policy_factor_count": len(factors),
        # Store action_counts under 'action_counts'.
        "action_counts": action_counts,
        # Store the sum of a lazy sequence of item at 'coordination_cycle_detected' for item in metadata under
        # 'coordination_cycle_count'.
        "coordination_cycle_count": sum(
            # Evaluate item at 'coordination_cycle_detected' as part of the enclosing expression.
            item["coordination_cycle_detected"] for item in metadata),
        # Store the sum of a lazy sequence of item at 'physical_execution_cycle_detected' for item in metadata
        # under 'physical_cycle_count'.
        "physical_cycle_count": sum(
            # Evaluate item at 'physical_execution_cycle_detected' as part of the enclosing expression.
            item["physical_execution_cycle_detected"] for item in metadata),
        # Store the sum of a lazy sequence of item at 'graph_executable' for item in metadata under
        # 'physical_executable_outcome_count'.
        "physical_executable_outcome_count": sum(
            # Evaluate item at 'graph_executable' as part of the enclosing expression.
            item["graph_executable"] for item in metadata),
        # Store the sum of a lazy sequence of item.completed_vehicle_count for item in episodes under
        # 'completed_vehicle_count'.
        "completed_vehicle_count": sum(
            # Evaluate item.completed_vehicle_count as part of the enclosing expression.
            item.completed_vehicle_count for item in episodes),
        # Store 0 under 'collision_count'.
        # Store 0 under 'blocked_zone_violation_count'.
        "collision_count": 0, "blocked_zone_violation_count": 0,
        # Store the sum of a lazy sequence of item.native_sumo_safety_intervention_count for item in episodes
        # under 'native_safety_intervention_count'.
        "native_safety_intervention_count": sum(
            # Evaluate item.native_sumo_safety_intervention_count as part of the enclosing expression.
            item.native_sumo_safety_intervention_count for item in episodes),
        # Store the sum of a lazy sequence of item.sumo_step_count for item in episodes under 'sumo_step_count'.
        "sumo_step_count": sum(item.sumo_step_count for item in episodes),
        # Store the result of perf_counter() minus started under 'wall_clock_runtime_seconds'.
        "wall_clock_runtime_seconds": perf_counter() - started,
        # Store a dictionary containing before, after under 'parameter_hashes_before_and_after_collection'.
        "parameter_hashes_before_and_after_collection": {
            # Store initial_hashes under 'before'.
            # Store final_hashes under 'after'.
            "before": initial_hashes, "after": final_hashes},
        # Store whether every item is true in a lazy sequence of whether every item is true in values from
        # item.hard_validity_gate_results for item in episodes under 'hard_validity_passed'.
        "hard_validity_passed": all(all(
            # Supply values from item.hard_validity_gate_results to all.
            item.hard_validity_gate_results.values()) for item in episodes),
        # Store 0 under 'route_truth_actor_fields'.
        "route_truth_actor_fields": 0,
    }
    # Set payload to the result of _pass_rollout_payload(design, architecture, optimization, manifest,
    # pass_identity, bundle, provider).
    payload = _pass_rollout_payload(
        # Supply pass_identity to _pass_rollout_payload.
        design, architecture, optimization, manifest, pass_identity,
        # Supply provider to _pass_rollout_payload.
        bundle, provider)
    # Return a tuple containing metrics, payload to the caller.
    return metrics, payload


# Define ControlledMAPPOPilotRunner to group the state and operations declared below.
# Instances expose the attributes and methods implemented in this class.
class ControlledMAPPOPilotRunner:
    # Run using the inputs and processing steps below.
    # Output: result.
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    def run(self):
        # Set started to the result of perf_counter().
        started = perf_counter()
        # Set design to the result of build_design().
        design = build_design()
        # Set architecture to the result of build_mechanical_pilot_architecture_contract().
        architecture = build_mechanical_pilot_architecture_contract()
        # Set optimization to the result of build_mechanical_adam_optimization_contract().
        optimization = build_mechanical_adam_optimization_contract()
        # Set manifest to design['manifests'] at ScenarioRole.TRAINING.
        manifest = design["manifests"][ScenarioRole.TRAINING]
        # Set specifications to a tuple built from a lazy sequence of the result of _specification(design at
        # 'payload', scenario_id) for scenario_id in manifest.scenario_ids.
        specifications = tuple(_specification(design["payload"], scenario_id)
                               # Evaluate manifest.scenario_ids as part of the enclosing expression.
                               for scenario_id in manifest.scenario_ids)
        # Set replications to an empty list.
        replications = []
        # Iterate over the integer range defined by 2, binding each item to replication_index.
        for replication_index in range(2):
            # Set replication_identity to a tuple containing the text 'CONTROLLED_MAPPO_PILOT_REPLICATION_V1',
            # design['freeze'].freeze_id, replication_index.
            replication_identity = (
                "CONTROLLED_MAPPO_PILOT_REPLICATION_V1",
                # Include design['freeze'].freeze_id in this tuple.
                design["freeze"].freeze_id, replication_index)
            # Set behavior_identity to the result of MAPPOBehaviorRolloutIdentity(the result of _identity(design,
            # architecture, optimization, manifest, replication_identity, the...).
            behavior_identity = MAPPOBehaviorRolloutIdentity(
                # Supply the result of _identity(design, architecture, optimization, manifest,
                # replication_identity, the text 'INITIAL_MODEL_STATE') to MAPPOBehaviorRolloutIdentity.
                _identity(design, architecture, optimization, manifest,
                          # Supply replication_identity to _identity.
                          replication_identity, "INITIAL_MODEL_STATE"),
                # Supply design['freeze'].freeze_id to MAPPOBehaviorRolloutIdentity.
                design["freeze"].freeze_id, architecture.contract_id,
                # Supply optimization.contract_id to MAPPOBehaviorRolloutIdentity.
                optimization.contract_id, manifest.manifest_id)
            # Set bundle to the result of build_mechanical_mappo_behavior_policy_bundle().
            bundle = build_mechanical_mappo_behavior_policy_bundle(
                # Supply component_seed_identity as a tuple containing replication_identity, the text
                # 'MODEL_INITIALIZATION'.
                component_seed_identity=(replication_identity,
                                         "MODEL_INITIALIZATION"),
                # Supply behavior_rollout_identity as behavior_identity.
                behavior_rollout_identity=behavior_identity)
            # Set initial_hashes to the result of _current_hashes(bundle).
            initial_hashes = _current_hashes(bundle)
            # Set rep_started to the result of perf_counter().
            rep_started = perf_counter()
            # Set (pass0, rollout0) to the result of collect_controlled_training_pass().
            pass0, rollout0 = collect_controlled_training_pass(
                # Supply design as design.
                # Supply architecture as architecture.
                design=design, architecture=architecture,
                # Supply optimization as optimization.
                # Supply manifest as manifest.
                optimization=optimization, manifest=manifest,
                # Supply specifications as specifications.
                # Supply bundle as bundle.
                specifications=specifications, bundle=bundle,
                # Supply replication_identity as replication_identity.
                replication_identity=replication_identity,
                # Supply pass_label as the text 'TRAINING_PASS_0_PRE_UPDATE'.
                pass_label="TRAINING_PASS_0_PRE_UPDATE",
                # Store replication_index under 'replication_index'.
                progress_context={"replication_index": replication_index})
            # Set update_started to the result of perf_counter().
            update_started = perf_counter()
            # Set update to the result of MechanicalMAPPOTrainer(rollout_payload=rollout0, bundle=bundle,
            # output_path=None).run().
            update = MechanicalMAPPOTrainer(
                # Supply rollout_payload as rollout0.
                # Supply bundle as bundle.
                rollout_payload=rollout0, bundle=bundle,
                # Supply output_path as None.
                output_path=None).run()
            # Set update_runtime to the result of perf_counter() minus update_started.
            update_runtime = perf_counter() - update_started
            # Set after_update to the result of _current_hashes(bundle).
            after_update = _current_hashes(bundle)
            # Set (pass1, _) to the result of collect_controlled_training_pass().
            pass1, _ = collect_controlled_training_pass(
                # Supply design as design.
                # Supply architecture as architecture.
                design=design, architecture=architecture,
                # Supply optimization as optimization.
                # Supply manifest as manifest.
                optimization=optimization, manifest=manifest,
                # Supply specifications as specifications.
                # Supply bundle as bundle.
                specifications=specifications, bundle=bundle,
                # Supply replication_identity as replication_identity.
                replication_identity=replication_identity,
                # Supply pass_label as the text 'TRAINING_PASS_1_POST_UPDATE'.
                pass_label="TRAINING_PASS_1_POST_UPDATE",
                # Store replication_index under 'replication_index'.
                progress_context={"replication_index": replication_index})
            # Set after_pass1 to the result of _current_hashes(bundle).
            after_pass1 = _current_hashes(bundle)
            # Run this branch when after_pass1 differs from after_update.
            if after_pass1 != after_update:
                # Raise RuntimeError with the text 'POLICY_PARAMETER_CHANGED_DURING_COLLECTION' to stop this
                # execution path.
                raise RuntimeError("POLICY_PARAMETER_CHANGED_DURING_COLLECTION")
            # Run this branch when the negation of initial_hashes at 'gnn' equals after_update at 'gnn'; equals
            # after_pass1 at 'gnn'.
            if not (initial_hashes["gnn"] == after_update["gnn"] ==
                    # Evaluate after_pass1 at 'gnn' as part of the enclosing expression.
                    after_pass1["gnn"]):
                # Raise RuntimeError with the text 'FROZEN_GNN_PARAMETER_CHANGED' to stop this execution path.
                raise RuntimeError("FROZEN_GNN_PARAMETER_CHANGED")
            # Set differences to a tuple built from a lazy sequence of post at 'team_travel_time_seconds' minus
            # pre at 'team_travel_time_seconds' for (pre, post) in corresponding items paired from pass0 at
            # 'scenario_metrics', pass1 at 'scenario_metrics'.
            differences = tuple(
                # Evaluate post at 'team_travel_time_seconds' minus pre at 'team_travel_time_seconds' as part of
                # the enclosing expression.
                post["team_travel_time_seconds"] - pre["team_travel_time_seconds"]
                # Evaluate corresponding items paired from pass0 at 'scenario_metrics', pass1 at
                # 'scenario_metrics' as part of the enclosing expression.
                for pre, post in zip(pass0["scenario_metrics"],
                                     # Supply pass1 at 'scenario_metrics' to zip.
                                     pass1["scenario_metrics"]))
            # Set replication to a dictionary containing replication_index, replication_identity,
            # seed_selected_by_performance,...
            replication = {
                # Store replication_index under 'replication_index'.
                "replication_index": replication_index,
                # Store the result of serializable(replication_identity) under 'replication_identity'.
                "replication_identity": serializable(replication_identity),
                # Store False under 'seed_selected_by_performance'.
                "seed_selected_by_performance": False,
                # Store the result of serializable(bundle.policy_parameter_identity) under
                # 'initial_policy_identity'.
                "initial_policy_identity": serializable(
                    # Supply bundle.policy_parameter_identity to serializable.
                    bundle.policy_parameter_identity),
                # Store pass0 under 'pass0'.
                "pass0": pass0,
                # Store the result of serializable(a tuple containing the text 'CONTROLLED_PILOT_UPDATE_V1',
                # replication_identity, update at...) under 'update_identity'.
                "update_identity": serializable((
                    # Include replication_identity in this tuple.
                    "CONTROLLED_PILOT_UPDATE_V1", replication_identity,
                    # Include update at 'post_update_policy_identity' in this tuple.
                    update["post_update_policy_identity"])),
                # Store update under 'update_diagnostics'.
                "update_diagnostics": update,
                # Store update_runtime under 'update_runtime_seconds'.
                "update_runtime_seconds": update_runtime,
                "post_update_policy_identity":
                    # Evaluate update at 'post_update_policy_identity' as part of the enclosing expression.
                    update["post_update_policy_identity"],
                # Store pass1 under 'pass1'.
                "pass1": pass1,
                "delta_team_travel_time_seconds":
                    # Evaluate pass1 at 'team_travel_time_seconds' minus pass0 at 'team_travel_time_seconds' as
                    # part of the enclosing expression.
                    pass1["team_travel_time_seconds"] -
                    # Evaluate pass0 at 'team_travel_time_seconds' as part of the enclosing expression.
                    pass0["team_travel_time_seconds"],
                # Store differences under 'paired_scenario_differences'.
                "paired_scenario_differences": differences,
                "paired_difference_summary":
                    # Evaluate the result of paired_difference_summary(differences) as part of the enclosing
                    # expression.
                    paired_difference_summary(differences),
                # Store a dictionary containing initial, after_update, after_pass1 under 'parameter_hashes'.
                "parameter_hashes": {
                    # Store initial_hashes under 'initial'.
                    "initial": initial_hashes,
                    # Store after_update under 'after_update'.
                    "after_update": after_update,
                    # Store after_pass1 under 'after_pass1'.
                    "after_pass1": after_pass1},
                # Store a dictionary containing pass0, pass1, gnn_unchanged, collisions, blocked_zone_violations
                # under 'hard_validity_results'.
                "hard_validity_results": {
                    # Store pass0 at 'hard_validity_passed' under 'pass0'.
                    "pass0": pass0["hard_validity_passed"],
                    # Store pass1 at 'hard_validity_passed' under 'pass1'.
                    "pass1": pass1["hard_validity_passed"],
                    # Store True under 'gnn_unchanged'.
                    "gnn_unchanged": True,
                    # Store 0 under 'collisions'.
                    # Store 0 under 'blocked_zone_violations'.
                    "collisions": 0, "blocked_zone_violations": 0},
                # Store a dictionary containing pass0_seconds, update_seconds, pass1_seconds,
                # total_replication_seconds under 'wall_clock_measurements'.
                "wall_clock_measurements": {
                    # Store pass0 at 'wall_clock_runtime_seconds' under 'pass0_seconds'.
                    "pass0_seconds": pass0["wall_clock_runtime_seconds"],
                    # Store update_runtime under 'update_seconds'.
                    "update_seconds": update_runtime,
                    # Store pass1 at 'wall_clock_runtime_seconds' under 'pass1_seconds'.
                    "pass1_seconds": pass1["wall_clock_runtime_seconds"],
                    # Store the result of perf_counter() minus rep_started under 'total_replication_seconds'.
                    "total_replication_seconds": perf_counter() - rep_started},
                # Store a dictionary containing performance_selected_seed, mechanical_weights_reused,... under
                # 'provenance'.
                # Store False under 'performance_selected_seed'.
                "provenance": {"performance_selected_seed": False,
                               # Store False under 'mechanical_weights_reused'.
                               "mechanical_weights_reused": False,
                               # Store 1 under 'pass0_data_used_for_update_cycles'.
                               "pass0_data_used_for_update_cycles": 1,
                               # Store 0 under 'pass1_update_cycles'.
                               "pass1_update_cycles": 0}}
            # Append replication to replications.
            replications.append(replication)
            # Call atomic_write_json with the supplied arguments.
            atomic_write_json(PROGRESS_PATH, {
                # Store replication_index plus 1 under 'completed_replications'.
                "completed_replications": replication_index + 1,
                # Store replications under 'replications'.
                "replications": replications})
        # Set pre to a list of item['pass0'] at 'team_travel_time_seconds' for item in replications.
        pre = [item["pass0"]["team_travel_time_seconds"]
               # Evaluate replications as part of the enclosing expression.
               for item in replications]
        # Set post to a list of item['pass1'] at 'team_travel_time_seconds' for item in replications.
        post = [item["pass1"]["team_travel_time_seconds"]
                # Evaluate replications as part of the enclosing expression.
                for item in replications]
        # Set delta to a list of item at 'delta_team_travel_time_seconds' for item in replications.
        delta = [item["delta_team_travel_time_seconds"]
                 # Evaluate replications as part of the enclosing expression.
                 for item in replications]
        # Set result to a dictionary containing checkpoint, status, training_budget_status, replication_status,...
        result = {
            "checkpoint": "STEP_5J_3C_1",
            "status": "CLOSED_LOOP_PROGRESS_AND_VARIANCE_PROBE_COMPLETE",
            "training_budget_status":
                "FIRST_CLOSED_LOOP_PROGRESS_EVIDENCE_MEASURED",
            "replication_status": "FIRST_VARIANCE_PROBE_MEASURED",
            # Store False under 'final_training_budget_selected'.
            "final_training_budget_selected": False,
            # Store False under 'final_replication_count_selected'.
            "final_replication_count_selected": False,
            "final_replication_count_status":
                "REQUIRES_POST_PILOT_DETERMINATION",
            # Store the result of serializable(design['freeze'].freeze_id) under 'frozen_design_id'.
            "frozen_design_id": serializable(design["freeze"].freeze_id),
            # Store the result of serializable(design['provisional'].configuration_id) under
            # 'provisional_configuration_id'.
            "provisional_configuration_id": serializable(
                # Supply design['provisional'].configuration_id to serializable.
                design["provisional"].configuration_id),
            # Store the result of serializable(architecture.contract_id) under 'architecture_contract_id'.
            "architecture_contract_id": serializable(architecture.contract_id),
            # Store the result of serializable(optimization.contract_id) under 'optimization_contract_id'.
            "optimization_contract_id": serializable(optimization.contract_id),
            "physical_execution_mapping_identity":
                "COORDINATION_TO_PHYSICAL_EXECUTION_MAPPING_STEP_5J_3B_3A",
            "replication_probe_reason": "MINIMUM_SAMPLE_VARIANCE_PROBE",
            # Store 2 under 'replication_count'.
            "replication_count": 2,
            # Store replications under 'replications'.
            "replications": replications,
            # Store a dictionary containing pre_update, post_update, delta under 'variance_evidence'.
            "variance_evidence": {
                # Store the result of two_replication_sample_statistics(pre) under 'pre_update'.
                "pre_update": two_replication_sample_statistics(pre),
                # Store the result of two_replication_sample_statistics(post) under 'post_update'.
                "post_update": two_replication_sample_statistics(post),
                # Store the result of two_replication_sample_statistics(delta) under 'delta'.
                "delta": two_replication_sample_statistics(delta)},
            # Store 72 under 'paired_scenario_change_count'.
            "paired_scenario_change_count": 72,
            # Store False under 'improvement_threshold_used'.
            "improvement_threshold_used": False,
            # Store False under 'convergence_claimed'.
            "convergence_claimed": False,
            # Store 144 under 'total_training_scenario_executions'.
            "total_training_scenario_executions": 144,
            # Store 4 under 'total_training_manifest_collections'.
            "total_training_manifest_collections": 4,
            # Store 2 under 'total_ppo_update_cycles'.
            "total_ppo_update_cycles": 2,
            # Store the sum of a lazy sequence of item[label] at 'sumo_step_count' for item in replications under
            # 'total_sumo_steps'.
            "total_sumo_steps": sum(
                # Evaluate item[label] at 'sumo_step_count' as part of the enclosing expression.
                item[label]["sumo_step_count"] for item in replications
                # Evaluate a tuple containing the text 'pass0', the text 'pass1' as part of the enclosing
                # expression.
                for label in ("pass0", "pass1")),
            # Store the sum of a lazy sequence of item[label] at 'policy_factor_count' for item in replications
            # under 'total_policy_factors'.
            "total_policy_factors": sum(
                # Evaluate item[label] at 'policy_factor_count' as part of the enclosing expression.
                item[label]["policy_factor_count"] for item in replications
                # Evaluate a tuple containing the text 'pass0', the text 'pass1' as part of the enclosing
                # expression.
                for label in ("pass0", "pass1")),
            # Store the result of perf_counter() minus started under 'total_wall_clock_runtime_seconds'.
            "total_wall_clock_runtime_seconds": perf_counter() - started,
            # Store the sum of a lazy sequence of item at 'update_runtime_seconds' for item in replications under
            # 'total_update_runtime_seconds'.
            "total_update_runtime_seconds": sum(
                # Evaluate item at 'update_runtime_seconds' as part of the enclosing expression.
                item["update_runtime_seconds"] for item in replications),
            # Store 0 under 'collisions'.
            # Store 0 under 'blocked_zone_violations'.
            "collisions": 0, "blocked_zone_violations": 0,
            # Store 0 under 'validation_runs'.
            # Store 0 under 'held_out_runs'.
            "validation_runs": 0, "held_out_runs": 0,
            # Store 0 under 'new_reward_terms'.
            # Store 0 under 'new_candidate_values'.
            "new_reward_terms": 0, "new_candidate_values": 0,
            # Store 0 under 'selected_hyperparameters'.
            "selected_hyperparameters": 0,
            # Store False under 'two_replications_are_final_design'.
            "two_replications_are_final_design": False,
            # Store the text 'The two-replication pilot is the mathematical minimum...' under
            # 'research_statement'.
            "research_statement": (
                "The two-replication pilot is the mathematical minimum required "
                "to obtain a first sample-variance estimate. It is not the final "
                "replication design.")}
        # Call atomic_write_json with the supplied arguments.
        atomic_write_json(EVIDENCE_PATH, result)
        # Return result to the caller.
        return result
