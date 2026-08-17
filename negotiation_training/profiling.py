"""Exhaustive frozen TRAINING-manifest coupled-environment profiling."""

import hashlib
import json
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from pathlib import Path
from statistics import fmean

from experimentation import ScenarioRole, build_design
from negotiation_execution.replay import _specification

from .environment import CoupledNegotiationTrainingEnvironment
from .providers import DeterministicEnvironmentProfilingActionProvider
from .readiness import (assess_step_5j_3a_environment_readiness,
                        assess_step_5j_3b_pilot_readiness,
                        load_coupling_evidence)

PROFILE_PATH = Path("results/coupled_environment_profile.json")


def deterministic_seed_from_design(frozen_design_id, replication_index):
    if type(replication_index) is not int or replication_index < 0:
        raise ValueError("NONNEGATIVE_REPLICATION_INDEX_REQUIRED")
    digest = hashlib.sha256(
        repr((frozen_design_id, replication_index)).encode()).digest()
    return int.from_bytes(digest[:8], "big")


def _json(value):
    if is_dataclass(value):
        return {field.name: _json(getattr(value, field.name))
                for field in fields(value)}
    if isinstance(value, Mapping):
        return {str(key): _json(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)): return [_json(item) for item in value]
    return value


def profile_complete_training_manifest(output_path=PROFILE_PATH):
    design = build_design()
    coupling = load_coupling_evidence()
    readiness = assess_step_5j_3a_environment_readiness(design, coupling)
    manifest = design["manifests"][ScenarioRole.TRAINING]
    specifications = tuple(
        _specification(design["payload"], scenario_id)
        for scenario_id in manifest.scenario_ids)
    episodes = []
    provider = DeterministicEnvironmentProfilingActionProvider()
    for index, specification in enumerate(specifications, 1):
        print(f"Profiling TRAINING scenario {index}/{len(specifications)}")
        episodes.append(CoupledNegotiationTrainingEnvironment(provider).run_episode(
            specification, manifest.manifest_id))
        Path("results/coupled_environment_profile_progress.json").write_text(
            json.dumps({"completed": index,
                        "episodes": [_json(item) for item in episodes]}, indent=2),
            encoding="utf-8")
    visited = tuple(item.scenario_id for item in episodes)
    if tuple(sorted(visited, key=repr)) != manifest.scenario_ids:
        raise RuntimeError("TRAINING_MANIFEST_NOT_VISITED_EXACTLY_ONCE")
    hard_pass = all(all(item.hard_validity_gate_results.values())
                    for item in episodes)
    fields = ("wall_clock_runtime_seconds", "sumo_step_count",
              "simulation_duration_seconds", "policy_factor_count",
              "proposer_factor_count", "responder_factor_count",
              "multi_factor_batch_count")
    aggregate = {}
    for field in fields:
        values = [getattr(item, field) for item in episodes]
        aggregate[field] = {"total": sum(values), "minimum": min(values),
                            "maximum": max(values), "mean": fmean(values)}
    aggregate["joint_decision_batch_count"] = sum(
        len(item.joint_decision_batches) for item in episodes)
    aggregate["physical_speed_command_count"] = sum(
        item.physical_speed_command_count for item in episodes)
    aggregate["conflict_zone_execution_plan_count"] = sum(
        item.conflict_zone_execution_plan_count for item in episodes)
    aggregate["native_sumo_safety_intervention_count"] = sum(
        item.native_sumo_safety_intervention_count for item in episodes)
    aggregate["team_travel_time_seconds"] = sum(
        item.team_travel_time_seconds for item in episodes)
    aggregate["raw_shared_team_reward"] = sum(
        item.raw_shared_team_reward for item in episodes)
    profile = {
        "checkpoint": "STEP_5J_3A",
        "status": "COUPLED_ENVIRONMENT_PROFILE_COMPLETE",
        "environment_identity": "EVENT_DRIVEN_COUPLED_NEGOTIATION_SUMO_V1",
        "frozen_design_id": repr(design["freeze"].freeze_id),
        "readiness_evidence": _json(readiness),
        "coupling_status": coupling["status"],
        "physical_causal_witness": coupling["physical_causal_witness"],
        "training_manifest_id": repr(manifest.manifest_id),
        "training_scenarios_expected": len(manifest.scenario_ids),
        "training_scenarios_attempted": len(episodes),
        "training_scenarios_completed": sum(
            item.episode_completion_status == "COMPLETE" for item in episodes),
        "training_manifest_scenario_ids": [repr(item) for item in manifest.scenario_ids],
        "visited_scenario_ids": [repr(item) for item in visited],
        "validation_performance_executions": 0,
        "held_out_performance_executions": 0,
        "episodes": [_json(item) for item in episodes],
        "aggregate": aggregate,
        "hard_validity_gates_passed": hard_pass,
        "interval_rewards_reconcile": all(
            item.interval_reward_sum == item.raw_shared_team_reward
            for item in episodes),
        "profiling_action_selection": provider.selection_rule,
        "profiling_selection_uses_outcome_data": provider.outcome_data_used,
        "profiling_samples_ppo_eligible": any(
            factor.ppo_update_eligible for episode in episodes
            for batch in episode.joint_decision_batches
            for factor in batch.policy_factors),
        "natural_units": {
            "ONE_SUMO_STEP": "EXISTING_SIMULATOR_STEP",
            "ONE_SEMANTIC_DECISION_BATCH": "ONE_EVENT_DRIVEN_JOINT_DECISION",
            "ONE_POLICY_FACTOR": "ONE_PROPOSER_OR_RESPONDER_ACTION_SAMPLE",
            "ONE_SCENARIO_EPISODE": "ONE_FROZEN_SCENARIO_EXECUTION",
            "ONE_TRAINING_MANIFEST_PASS": len(manifest.scenario_ids)},
        "training_budget_status": "LEARNING_BUDGET_STILL_REQUIRES_PILOT_PROGRESS_EVIDENCE",
        "replication_count_status": "REQUIRES_PILOT_VARIANCE_ESTIMATE",
        "actual_rl_seeds_instantiated": 0,
        "new_candidate_values": 0,
        "selected_hyperparameter_values": 0,
        "optimizer_instances": 0,
        "backward_calls": 0,
        "parameter_updates": 0,
        "mappo_pilot_runs": 0,
        "model_checkpoints": 0,
        "learned_main_actions": 0,
        "reward_terms_added": 0,
        "provisional_configuration_id": repr(design["provisional"].configuration_id),
        "provisional_project_selected": False,
    }
    profile["step_5j_3b_readiness"] = assess_step_5j_3b_pilot_readiness(profile)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(profile, indent=2), encoding="utf-8")
    return profile
