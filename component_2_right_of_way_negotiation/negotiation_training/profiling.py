"""Exhaustive frozen TRAINING-manifest coupled-environment profiling."""

# Import hashlib for use in this module.
import hashlib
# Import json for use in this module.
import json
# Import Mapping from collections.abc for the operations below.
from collections.abc import Mapping
# Import fields, is_dataclass from dataclasses for the operations below.
from dataclasses import fields, is_dataclass
# Import Path from pathlib for the operations below.
from pathlib import Path
# Import fmean from statistics for the operations below.
from statistics import fmean

# Import ScenarioRole, build_design from experimentation for the operations below.
from experimentation import ScenarioRole, build_design
# Import _specification from negotiation_execution.replay for the operations below.
from negotiation_execution.replay import _specification

# Import CoupledNegotiationTrainingEnvironment from .environment for the operations below.
from .environment import CoupledNegotiationTrainingEnvironment
# Import DeterministicEnvironmentProfilingActionProvider from .providers for the operations below.
from .providers import DeterministicEnvironmentProfilingActionProvider
# Import assess_step_5j_3a_environment_readiness, assess_step_5j_3b_pilot_readiness, load_coupling_evidence from
# .readiness for the operations below.
from .readiness import (assess_step_5j_3a_environment_readiness,
                        assess_step_5j_3b_pilot_readiness,
                        load_coupling_evidence)

# Set PROFILE_PATH to the result of Path(the text 'results/coupled_environment_profile.json').
PROFILE_PATH = Path("results/coupled_environment_profile.json")


# Deterministic seed from design using the inputs and processing steps below.
# Input frozen_design_id: the supplied frozen design id.
# Input replication_index: the supplied replication index.
# Output: the result of int.from_bytes(digest sliced by :8, the text 'big').
# Processing: select branches using the stated conditions.
def deterministic_seed_from_design(frozen_design_id, replication_index):
    # Run this branch when the result of type(replication_index) is a different object from int or
    # replication_index is less than 0.
    if type(replication_index) is not int or replication_index < 0:
        # Raise ValueError with the text 'NONNEGATIVE_REPLICATION_INDEX_REQUIRED' to stop this execution path.
        raise ValueError("NONNEGATIVE_REPLICATION_INDEX_REQUIRED")
    # Set digest to the result of hashlib.sha256(repr((frozen_design_id, replication_index)).encode()).digest().
    digest = hashlib.sha256(
        # Supply the result of repr((frozen_design_id, replication_index)).encode() to hashlib.sha256.
        repr((frozen_design_id, replication_index)).encode()).digest()
    # Return the result of int.from_bytes(digest sliced by :8, the text 'big') to the caller.
    return int.from_bytes(digest[:8], "big")


# Json using the inputs and processing steps below.
# Input value: the supplied value.
# Output: return the value selected by the matching return branch below.
# Processing: select branches using the stated conditions.
def _json(value):
    # Run this branch when the result of is_dataclass(value).
    if is_dataclass(value):
        # Return a dictionary of field.name mapped to the result of _json(the requested attribute of value) for
        # field in the result of fields(value) to the caller.
        return {field.name: _json(getattr(value, field.name))
                # Evaluate the result of fields(value) as part of the enclosing expression.
                for field in fields(value)}
    # Run this branch when whether value has type Mapping.
    if isinstance(value, Mapping):
        # Return a dictionary of a string built from key mapped to the result of _json(item) for (key, item) in
        # key/value pairs from value to the caller.
        return {str(key): _json(item) for key, item in value.items()}
    # Run this branch when whether value has type a tuple containing tuple, list.
    # Return a list of the result of _json(item) for item in value to the caller.
    if isinstance(value, (tuple, list)): return [_json(item) for item in value]
    # Return value to the caller.
    return value


# Profile complete training manifest using the inputs and processing steps below.
# Input output_path: the supplied output path.
# Output: profile.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def profile_complete_training_manifest(output_path=PROFILE_PATH):
    # Set design to the result of build_design().
    design = build_design()
    # Set coupling to the result of load_coupling_evidence().
    coupling = load_coupling_evidence()
    # Set readiness to the result of assess_step_5j_3a_environment_readiness(design, coupling).
    readiness = assess_step_5j_3a_environment_readiness(design, coupling)
    # Set manifest to design['manifests'] at ScenarioRole.TRAINING.
    manifest = design["manifests"][ScenarioRole.TRAINING]
    # Set specifications to a tuple built from a lazy sequence of the result of _specification(design at
    # 'payload', scenario_id) for scenario_id in manifest.scenario_ids.
    specifications = tuple(
        # Evaluate the result of _specification(design at 'payload', scenario_id) as part of the enclosing
        # expression.
        _specification(design["payload"], scenario_id)
        # Evaluate manifest.scenario_ids as part of the enclosing expression.
        for scenario_id in manifest.scenario_ids)
    # Set episodes to an empty list.
    episodes = []
    # Set provider to the result of DeterministicEnvironmentProfilingActionProvider().
    provider = DeterministicEnvironmentProfilingActionProvider()
    # Iterate over index/value pairs from specifications, binding each item to (index, specification).
    for index, specification in enumerate(specifications, 1):
        # Display formatted text built from the embedded values.
        print(f"Profiling TRAINING scenario {index}/{len(specifications)}")
        # Append the result of CoupledNegotiationTrainingEnvironment(provider).run_episode(specification,
        # manifest.manifest_id) to episodes.
        episodes.append(CoupledNegotiationTrainingEnvironment(provider).run_episode(
            # Supply manifest.manifest_id to CoupledNegotiationTrainingEnvironment(provider).run_episode.
            specification, manifest.manifest_id))
        # Write the supplied text to Path('results/coupled_environment_profile_progress.json').
        Path("results/coupled_environment_profile_progress.json").write_text(
            # Store index under 'completed'.
            json.dumps({"completed": index,
                        # Store a list of the result of _json(item) for item in episodes under 'episodes'.
                        "episodes": [_json(item) for item in episodes]}, indent=2),
            # Supply encoding as the text 'utf-8'.
            encoding="utf-8")
    # Set visited to a tuple built from a lazy sequence of item.scenario_id for item in episodes.
    visited = tuple(item.scenario_id for item in episodes)
    # Run this branch when a tuple built from the sorted values from visited differs from manifest.scenario_ids.
    if tuple(sorted(visited, key=repr)) != manifest.scenario_ids:
        # Raise RuntimeError with the text 'TRAINING_MANIFEST_NOT_VISITED_EXACTLY_ONCE' to stop this execution
        # path.
        raise RuntimeError("TRAINING_MANIFEST_NOT_VISITED_EXACTLY_ONCE")
    # Set hard_pass to whether every item is true in a lazy sequence of whether every item is true in values from
    # item.hard_validity_gate_results for item in episodes.
    hard_pass = all(all(item.hard_validity_gate_results.values())
                    # Evaluate episodes as part of the enclosing expression.
                    for item in episodes)
    # Set fields to a tuple containing the text 'wall_clock_runtime_seconds', the text 'sumo_step_count', the text
    # 'simulation_duration_seconds',...
    fields = ("wall_clock_runtime_seconds", "sumo_step_count",
              "simulation_duration_seconds", "policy_factor_count",
              "proposer_factor_count", "responder_factor_count",
              "multi_factor_batch_count")
    # Set aggregate to an empty dictionary.
    aggregate = {}
    # Iterate over fields, binding each item to field.
    for field in fields:
        # Set values to a list of the requested attribute of item for item in episodes.
        values = [getattr(item, field) for item in episodes]
        # Set aggregate[field] to a dictionary containing total, minimum, maximum, mean.
        aggregate[field] = {"total": sum(values), "minimum": min(values),
                            # Store the maximum of values under 'maximum'.
                            # Store the result of fmean(values) under 'mean'.
                            "maximum": max(values), "mean": fmean(values)}
    # Set aggregate['joint_decision_batch_count'] to the sum of a lazy sequence of the number of entries in
    # item.joint_decision_batches for item in episodes.
    aggregate["joint_decision_batch_count"] = sum(
        # Evaluate the number of entries in item.joint_decision_batches as part of the enclosing expression.
        len(item.joint_decision_batches) for item in episodes)
    # Set aggregate['physical_speed_command_count'] to the sum of a lazy sequence of
    # item.physical_speed_command_count for item in episodes.
    aggregate["physical_speed_command_count"] = sum(
        # Evaluate item.physical_speed_command_count as part of the enclosing expression.
        item.physical_speed_command_count for item in episodes)
    # Set aggregate['conflict_zone_execution_plan_count'] to the sum of a lazy sequence of
    # item.conflict_zone_execution_plan_count for item in episodes.
    aggregate["conflict_zone_execution_plan_count"] = sum(
        # Evaluate item.conflict_zone_execution_plan_count as part of the enclosing expression.
        item.conflict_zone_execution_plan_count for item in episodes)
    # Set aggregate['native_sumo_safety_intervention_count'] to the sum of a lazy sequence of
    # item.native_sumo_safety_intervention_count for item in episodes.
    aggregate["native_sumo_safety_intervention_count"] = sum(
        # Evaluate item.native_sumo_safety_intervention_count as part of the enclosing expression.
        item.native_sumo_safety_intervention_count for item in episodes)
    # Set aggregate['team_travel_time_seconds'] to the sum of a lazy sequence of item.team_travel_time_seconds for
    # item in episodes.
    aggregate["team_travel_time_seconds"] = sum(
        # Evaluate item.team_travel_time_seconds as part of the enclosing expression.
        item.team_travel_time_seconds for item in episodes)
    # Set aggregate['raw_shared_team_reward'] to the sum of a lazy sequence of item.raw_shared_team_reward for
    # item in episodes.
    aggregate["raw_shared_team_reward"] = sum(
        # Evaluate item.raw_shared_team_reward as part of the enclosing expression.
        item.raw_shared_team_reward for item in episodes)
    # Set profile to a dictionary containing checkpoint, status, environment_identity, frozen_design_id,
    # readiness_evidence,...
    profile = {
        "checkpoint": "STEP_5J_3A",
        "status": "COUPLED_ENVIRONMENT_PROFILE_COMPLETE",
        "environment_identity": "EVENT_DRIVEN_COUPLED_NEGOTIATION_SUMO_V1",
        # Store the result of repr(design['freeze'].freeze_id) under 'frozen_design_id'.
        "frozen_design_id": repr(design["freeze"].freeze_id),
        # Store the result of _json(readiness) under 'readiness_evidence'.
        "readiness_evidence": _json(readiness),
        # Store coupling at 'status' under 'coupling_status'.
        "coupling_status": coupling["status"],
        # Store coupling at 'physical_causal_witness' under 'physical_causal_witness'.
        "physical_causal_witness": coupling["physical_causal_witness"],
        # Store the result of repr(manifest.manifest_id) under 'training_manifest_id'.
        "training_manifest_id": repr(manifest.manifest_id),
        # Store the number of entries in manifest.scenario_ids under 'training_scenarios_expected'.
        "training_scenarios_expected": len(manifest.scenario_ids),
        # Store the number of entries in episodes under 'training_scenarios_attempted'.
        "training_scenarios_attempted": len(episodes),
        # Store the sum of a lazy sequence of item.episode_completion_status equals the text 'COMPLETE' for item
        # in episodes under 'training_scenarios_completed'.
        "training_scenarios_completed": sum(
            # Evaluate item.episode_completion_status equals the text 'COMPLETE' as part of the enclosing
            # expression.
            item.episode_completion_status == "COMPLETE" for item in episodes),
        # Store a list of the result of repr(item) for item in manifest.scenario_ids under
        # 'training_manifest_scenario_ids'.
        "training_manifest_scenario_ids": [repr(item) for item in manifest.scenario_ids],
        # Store a list of the result of repr(item) for item in visited under 'visited_scenario_ids'.
        "visited_scenario_ids": [repr(item) for item in visited],
        # Store 0 under 'validation_performance_executions'.
        "validation_performance_executions": 0,
        # Store 0 under 'held_out_performance_executions'.
        "held_out_performance_executions": 0,
        # Store a list of the result of _json(item) for item in episodes under 'episodes'.
        "episodes": [_json(item) for item in episodes],
        # Store aggregate under 'aggregate'.
        "aggregate": aggregate,
        # Store hard_pass under 'hard_validity_gates_passed'.
        "hard_validity_gates_passed": hard_pass,
        # Store whether every item is true in a lazy sequence of item.interval_reward_sum equals
        # item.raw_shared_team_reward for item in episodes under 'interval_rewards_reconcile'.
        "interval_rewards_reconcile": all(
            # Evaluate item.interval_reward_sum equals item.raw_shared_team_reward as part of the enclosing
            # expression.
            item.interval_reward_sum == item.raw_shared_team_reward
            # Evaluate episodes as part of the enclosing expression.
            for item in episodes),
        # Store provider.selection_rule under 'profiling_action_selection'.
        "profiling_action_selection": provider.selection_rule,
        # Store provider.outcome_data_used under 'profiling_selection_uses_outcome_data'.
        "profiling_selection_uses_outcome_data": provider.outcome_data_used,
        # Store whether any item is true in a lazy sequence of factor.ppo_update_eligible for episode in episodes
        # under 'profiling_samples_ppo_eligible'.
        "profiling_samples_ppo_eligible": any(
            # Evaluate factor.ppo_update_eligible as part of the enclosing expression.
            factor.ppo_update_eligible for episode in episodes
            # Evaluate episode.joint_decision_batches as part of the enclosing expression.
            for batch in episode.joint_decision_batches
            # Evaluate batch.policy_factors as part of the enclosing expression.
            for factor in batch.policy_factors),
        # Store a dictionary containing ONE_SUMO_STEP, ONE_SEMANTIC_DECISION_BATCH, ONE_POLICY_FACTOR,
        # ONE_SCENARIO_EPISODE,... under 'natural_units'.
        "natural_units": {
            "ONE_SUMO_STEP": "EXISTING_SIMULATOR_STEP",
            "ONE_SEMANTIC_DECISION_BATCH": "ONE_EVENT_DRIVEN_JOINT_DECISION",
            "ONE_POLICY_FACTOR": "ONE_PROPOSER_OR_RESPONDER_ACTION_SAMPLE",
            "ONE_SCENARIO_EPISODE": "ONE_FROZEN_SCENARIO_EXECUTION",
            # Store the number of entries in manifest.scenario_ids under 'ONE_TRAINING_MANIFEST_PASS'.
            "ONE_TRAINING_MANIFEST_PASS": len(manifest.scenario_ids)},
        "training_budget_status": "LEARNING_BUDGET_STILL_REQUIRES_PILOT_PROGRESS_EVIDENCE",
        "replication_count_status": "REQUIRES_PILOT_VARIANCE_ESTIMATE",
        # Store 0 under 'actual_rl_seeds_instantiated'.
        "actual_rl_seeds_instantiated": 0,
        # Store 0 under 'new_candidate_values'.
        "new_candidate_values": 0,
        # Store 0 under 'selected_hyperparameter_values'.
        "selected_hyperparameter_values": 0,
        # Store 0 under 'optimizer_instances'.
        "optimizer_instances": 0,
        # Store 0 under 'backward_calls'.
        "backward_calls": 0,
        # Store 0 under 'parameter_updates'.
        "parameter_updates": 0,
        # Store 0 under 'mappo_pilot_runs'.
        "mappo_pilot_runs": 0,
        # Store 0 under 'model_checkpoints'.
        "model_checkpoints": 0,
        # Store 0 under 'learned_main_actions'.
        "learned_main_actions": 0,
        # Store 0 under 'reward_terms_added'.
        "reward_terms_added": 0,
        # Store the result of repr(design['provisional'].configuration_id) under 'provisional_configuration_id'.
        "provisional_configuration_id": repr(design["provisional"].configuration_id),
        # Store False under 'provisional_project_selected'.
        "provisional_project_selected": False,
    }
    # Set profile['step_5j_3b_readiness'] to the result of assess_step_5j_3b_pilot_readiness(profile).
    profile["step_5j_3b_readiness"] = assess_step_5j_3b_pilot_readiness(profile)
    # Set output_path to the result of Path(output_path).
    output_path = Path(output_path)
    # Create the directory requested by output_path.parent.
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # Write the supplied text to output_path.
    output_path.write_text(json.dumps(profile, indent=2), encoding="utf-8")
    # Return profile to the caller.
    return profile
