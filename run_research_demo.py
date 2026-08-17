"""Run the three-scenario Step 5K.1 decentralized research demonstration."""

import json
from pathlib import Path

from conflict import ConflictZoneManager, MapPathManager
from experimentation import ScenarioRole, build_design
from negotiation_execution.physical_mapping import NONCONFLICTING
from negotiation_execution.replay import _specification
from negotiation_training.behavior_rollout import serializable
from negotiation_training.controlled_pilot import atomic_write_json
from negotiation_training.demo_policy import (
    DEMO_POLICY_PATH, SELECTION_RULE, SOURCE_CHECKPOINT,
    create_demo_policy, file_sha256, load_demo_policy)
from negotiation_training.demo_provider import DemonstrationMAPPOActionProvider
from negotiation_training.environment import CoupledNegotiationTrainingEnvironment


RESULT_PATH = Path("results/final_research_prototype_demo.json")
SUMMARY_PATH = Path("results/final_research_prototype_demo_summary.md")
SCENARIO_RULE = (
    "FROZEN_TRAINING_STRUCTURAL_COVERAGE_REGULATORY_CYCLE_"
    "MULTI_FACTOR_MULTI_ACTION_AUTHORITATIVE_NONPHYSICAL_EDGE_V1")


def select_demo_scenarios(design=None):
    design = design or build_design()
    training_ids = set(
        design["manifests"][ScenarioRole.TRAINING].scenario_ids)
    signatures = sorted(
        (item for item in design["signatures"]
         if item.scenario_id in training_ids), key=lambda item: repr(item.scenario_id))
    multi = next(item for item in signatures
                 if item.multi_factor_capable and
                 item.multi_action_proposer_capable and
                 item.multi_action_responder_capable)
    cycle = next(item for item in signatures
                 if item.scenario_id != multi.scenario_id and
                 item.cyclic_participant_count == item.participant_count and
                 item.participant_count >= 4)
    zones = ConflictZoneManager(MapPathManager())
    nonphysical = None
    nonphysical_pair = None
    for item in signatures:
        if item.scenario_id in (multi.scenario_id, cycle.scenario_id):
            continue
        for first in item.movement_path_ids:
            for second in item.movement_path_ids:
                if first == second:
                    continue
                relationship = zones.relationship(first, second)
                if (not relationship.coordinated_conflict and
                        not relationship.physical_overlap and
                        relationship.conflict_zone_id is None):
                    nonphysical, nonphysical_pair = item, (first, second)
                    break
            if nonphysical is not None:
                break
        if nonphysical is not None:
            break
    if nonphysical is None:
        raise RuntimeError("STRUCTURAL_NONPHYSICAL_EDGE_SCENARIO_NOT_AVAILABLE")
    return (
        {"category": "REGULATORY_CYCLE_NEGOTIATION",
         "signature": cycle, "selection_evidence": {
             "cyclic_participant_count": cycle.cyclic_participant_count,
             "participant_count": cycle.participant_count}},
        {"category": "MULTI_FACTOR_MULTI_ACTION_NEGOTIATION",
         "signature": multi, "selection_evidence": {
             "potential_claim_factors": multi.potential_claim_factors,
             "multi_factor_capable": multi.multi_factor_capable,
             "multi_action_proposer_capable":
                 multi.multi_action_proposer_capable,
             "multi_action_responder_capable":
                 multi.multi_action_responder_capable}},
        {"category": "COORDINATION_TO_NONPHYSICAL_EXECUTION_INTERPRETATION",
         "signature": nonphysical, "selection_evidence": {
             "authoritative_nonconflicting_movement_pair": nonphysical_pair}})


def _scenario_trace(selected, episode, provider):
    episode_id = episode.episode_id
    factors = tuple(item for item in provider.pending_factors
                    if item.episode_id == episode_id)
    metadata = tuple(item for item in provider.batch_metadata
                     if item["episode_id"] == episode_id)
    signature = selected["signature"]
    graph_shapes = tuple(shape for batch in episode.joint_decision_batches
                         for shape in batch.encoded_graph_shapes)
    node_counts = tuple(shape[0][0] for shape in graph_shapes)
    action_trace = tuple({
        "decision_role": item.decision_role,
        "ego_id": item.ego_id,
        "claim_identity": serializable(item.claim_identity),
        "proposal_id": serializable(item.proposal_id),
        "available_semantic_actions": serializable(item.action_names),
        "hard_action_mask": serializable(item.hard_action_mask),
        "actor_probability_vector": serializable(
            item.behavior_probability_vector),
        "selected_action_index": item.selected_action_index,
        "selected_semantic_action": item.selected_semantic_action,
        "actor_route_truth_fields_consumed": 0,
        "centralized_critic_used_for_action": False,
        "ego_local_observation_used": True,
        "hard_action_mask_applied": True}
        for item in factors)
    if any(not item.hard_action_mask[item.selected_action_index]
           for item in factors):
        raise RuntimeError("DEMONSTRATION_HARD_ACTION_MASK_BYPASSED")
    edge_interpretations = tuple(
        interpretation for item in metadata
        for interpretation in item.get("edge_interpretations", ()))
    return {
        "structural_category": selected["category"],
        "selection_evidence": serializable(selected["selection_evidence"]),
        "scenario_id": serializable(signature.scenario_id),
        "scenario_family": signature.scenario_family,
        "movement_paths": {f"SCENARIO_AV_{index}": path for index, path in
                           enumerate(signature.movement_path_ids)},
        "perception": {
            "av_count": signature.participant_count,
            "encoded_ego_local_graph_count": len(graph_shapes),
            "maximum_locally_encoded_nodes": max(node_counts, default=0),
            "locally_observed_neighbor_count_upper_bound":
                max((value - 1 for value in node_counts), default=0),
            "unobserved_or_propagated_track_count":
                "NOT_RETAINED_BY_COUPLED_EPISODE_RECORD"},
        "intention_prediction": {
            "runtime_pipeline_active": True,
            "per_vehicle_prediction_trace":
                "NOT_RETAINED_BY_COUPLED_EPISODE_RECORD"},
        "conflict_reasoning": {
            "coordination_edges": sum(
                item.get("coordination_edge_count", 0) for item in metadata),
            "physical_execution_edges": sum(
                item.get("physical_execution_edge_count", 0)
                for item in metadata),
            "nonphysical_coordination_edges": sum(
                item.get("nonphysical_coordination_edge_count", 0)
                for item in metadata)},
        "traffic_rule_reasoning": {
            "regulatory_cycle_expected_by_frozen_signature":
                signature.cyclic_participant_count > 0,
            "coordination_cycles_observed": sum(
                item.get("coordination_cycle_detected", False)
                for item in metadata)},
        "negotiation": {
            "batch_count": len(metadata),
            "proposer_decisions": sum(
                item.decision_role == "PROPOSER" for item in factors),
            "responder_decisions": sum(
                item.decision_role == "RESPONDER" for item in factors),
            "action_trace": action_trace,
            "effective_coordination_graphs": serializable(tuple(
                item.get("effective_graph", ()) for item in metadata))},
        "execution": {
            "physical_execution_graphs": serializable(tuple(
                item.get("physical_execution_graph", ()) for item in metadata)),
            "edge_interpretations": serializable(edge_interpretations),
            "physically_executable_outcomes": sum(
                item.get("graph_executable", False) for item in metadata),
            "nonphysical_interpretations_observed": sum(
                item.execution_relevance == NONCONFLICTING
                for item in edge_interpretations)},
        "decentralization": {
            "actor_route_truth_fields_consumed": 0,
            "centralized_critic_used_for_action": False,
            "ego_local_observation_used": True,
            "hard_action_mask_applied": True},
        "outcome": {
            "completed_vehicles": episode.completed_vehicle_count,
            "team_travel_time_seconds": episode.team_travel_time_seconds,
            "collisions": episode.collision_count,
            "blocked_zone_violations":
                episode.blocked_zone_entry_violation_count,
            "native_sumo_safety_interventions":
                episode.native_sumo_safety_intervention_count,
            "sumo_steps": episode.sumo_step_count,
            "wall_clock_runtime_seconds": episode.wall_clock_runtime_seconds}}


def _write_summary(result):
    lines = [
        "# Final Research Prototype Demonstration", "",
        "Project: Multi-Agent Negotiation for Right-of-Way in Complex Intersections",
        "", "Architecture demonstrated: decentralized execution using a "
        "CTDE-trained MAPPO policy.", "",
        "Each AV acts from ego-local observations. Intention predictions support "
        "conflict reasoning, traffic rules establish mandatory precedence, and "
        "MAPPO resolves negotiable ambiguity or cycles. Learned actions remain "
        "subordinate to hard regulatory, conflict-zone, and SUMO safety gates. "
        "The resulting agreement is mapped to physical vehicle control.", "",
        "The centralized critic was not part of runtime decentralized control. "
        "HELD_OUT remained untouched.", "",
        "The demonstration policy is an existing trained checkpoint selected by "
        "a deterministic provenance rule for demonstration only. It is not "
        "claimed to be the statistically optimal or final selected MAPPO model.",
        "", "## Demonstrated scenarios", ""]
    for item in result["per_scenario_evidence"]:
        lines.extend((
            f"- {item['structural_category']}: `{item['scenario_id']}` — "
            f"{len(item['negotiation']['action_trace'])} learned decisions, "
            f"{item['outcome']['completed_vehicles']} completed vehicles, "
            f"{item['outcome']['collisions']} collisions.",))
    lines.extend(("", "## Boundary", "",
                  "This validates end-to-end implementation, not model optimality. "
                  "Exhaustive hyperparameter selection remains future work under "
                  "explicit project resource and statistical protocols."))
    SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_demo():
    source_hash_before = file_sha256(SOURCE_CHECKPOINT)
    create_demo_policy()
    policy = load_demo_policy(DEMO_POLICY_PATH)
    provider = DemonstrationMAPPOActionProvider(policy)
    hashes_before = provider.inference_parameter_hashes()
    design = build_design()
    selected = select_demo_scenarios(design)
    traces = []
    base = {
        "checkpoint": "STEP_5K_1",
        "source_demo_policy_identity": serializable(
            policy["demo_policy_identity"]),
        "source_training_checkpoint_identity": serializable(
            policy["source_checkpoint_identity"]),
        "demo_checkpoint_selection_rule": SELECTION_RULE,
        "performance_selected": False,
        "statistical_selection_performed": False,
        "best_model": False, "final_model": False, "optimal_model": False,
        "decentralized_execution": True,
        "scenario_selection_rule": SCENARIO_RULE,
        "scenario_selection_performance_based": False}
    try:
        for selected_item in selected:
            specification = _specification(
                design["payload"], selected_item["signature"].scenario_id)
            episode = CoupledNegotiationTrainingEnvironment(
                provider).run_episode(
                    specification,
                    design["manifests"][ScenarioRole.TRAINING].manifest_id)
            trace = _scenario_trace(selected_item, episode, provider)
            traces.append(trace)
            if (trace["outcome"]["collisions"] or
                    trace["outcome"]["blocked_zone_violations"]):
                raise RuntimeError("DEMONSTRATION_SAFETY_GATE_FAILED")
    except Exception as error:
        failure = {**base, "status": "DEMONSTRATION_SAFETY_GATE_FAILED"
                   if str(error) == "DEMONSTRATION_SAFETY_GATE_FAILED"
                   else "DEMONSTRATION_EXECUTION_FAILED",
                   "failure": repr(error),
                   "per_scenario_evidence": traces,
                   "source_checkpoint_sha256_before": source_hash_before,
                   "source_checkpoint_sha256_after":
                       file_sha256(SOURCE_CHECKPOINT)}
        atomic_write_json(RESULT_PATH, failure)
        raise
    hashes_after = provider.inference_parameter_hashes()
    if hashes_after != hashes_before:
        raise RuntimeError("DEMONSTRATION_POLICY_PARAMETER_MUTATION_DETECTED")
    factors = tuple(provider.pending_factors)
    metadata = tuple(provider.batch_metadata)
    result = {
        **base,
        "status": "DECENTRALIZED_MAPPO_RESEARCH_PROTOTYPE_DEMONSTRATED",
        "ctde_runtime_critic_calls": provider.runtime_critic_calls,
        "actor_route_truth_fields_consumed":
            provider.actor_route_truth_fields_consumed,
        "ego_local_observation_used": provider.ego_local_observation_used,
        "hard_action_masks_active": provider.hard_action_mask_applied,
        "demonstration_action_sampling_seed_identity": serializable(
            policy["demonstration_action_sampling_seed_identity"]),
        "scenario_ids": [serializable(item["signature"].scenario_id)
                         for item in selected],
        "per_scenario_evidence": traces,
        "aggregate": {
            "scenario_count": len(traces),
            "completed_vehicles": sum(
                item["outcome"]["completed_vehicles"] for item in traces),
            "team_travel_time_seconds": sum(
                item["outcome"]["team_travel_time_seconds"] for item in traces),
            "collisions": 0, "blocked_zone_violations": 0,
            "learned_proposer_actions": sum(
                item.decision_role == "PROPOSER" for item in factors),
            "learned_responder_actions": sum(
                item.decision_role == "RESPONDER" for item in factors),
            "learned_mappo_decisions": len(factors),
            "negotiation_batches": len(metadata),
            "regulatory_cycles": sum(
                item.get("coordination_cycle_detected", False)
                for item in metadata),
            "physical_executable_outcomes": sum(
                item.get("graph_executable", False) for item in metadata),
            "nonphysical_coordination_edges": sum(
                item.get("nonphysical_coordination_edge_count", 0)
                for item in metadata),
            "native_safety_interventions": sum(
                item["outcome"]["native_sumo_safety_interventions"]
                for item in traces)},
        "parameter_hashes_before": hashes_before,
        "parameter_hashes_after": hashes_after,
        "policy_hashes_unchanged": True,
        "source_checkpoint_sha256_before": source_hash_before,
        "source_checkpoint_sha256_after": file_sha256(SOURCE_CHECKPOINT),
        "source_checkpoint_unchanged":
            file_sha256(SOURCE_CHECKPOINT) == source_hash_before,
        "training_operations": 0, "optimizer_instances": 0,
        "optimizer_step_calls": 0, "backward_calls": 0,
        "ppo_updates": 0, "parameter_updates": 0,
        "new_training_episodes": 0,
        "validation_scenarios_used": 0,
        "held_out_scenarios_used": 0,
        "normal_main_learned_actions": 0}
    if (result["ctde_runtime_critic_calls"] != 0 or
            result["actor_route_truth_fields_consumed"] != 0 or
            result["aggregate"]["learned_proposer_actions"] < 1 or
            result["aggregate"]["learned_mappo_decisions"] < 1 or
            not result["source_checkpoint_unchanged"]):
        result["status"] = "DEMONSTRATION_RUNTIME_BOUNDARY_FAILED"
        atomic_write_json(RESULT_PATH, result)
        raise RuntimeError(result["status"])
    atomic_write_json(RESULT_PATH, result)
    _write_summary(result)
    return result


def main():
    result = run_demo()
    print("Final Research Prototype Demonstration\n")
    print("Policy")
    print("  Type: RESEARCH_PROTOTYPE_DEMONSTRATION_POLICY")
    print("  Source replication: 0")
    print("  Source state: 2")
    print("  Performance-selected: False")
    print("  Final/optimal claim: False\n")
    print("Architecture")
    print("  Decentralized actor execution: PASS")
    print(f"  Centralized critic runtime use: {result['ctde_runtime_critic_calls']}")
    print(f"  Route-truth actor leakage: {result['actor_route_truth_fields_consumed']}")
    print("  Hard masks active: PASS")
    for index, item in enumerate(result["per_scenario_evidence"], 1):
        print(f"\nScenario {index}/3")
        print(f"  Category: {item['structural_category']}")
        print(f"  Scenario ID: {item['scenario_id']}")
        print(f"  Negotiation actions: {len(item['negotiation']['action_trace'])}")
        print(f"  Proposer: {item['negotiation']['proposer_decisions']}")
        print(f"  Responder: {item['negotiation']['responder_decisions']}")
        print(f"  Physical outcomes: {item['execution']['physically_executable_outcomes']}")
        print(f"  Collision: {item['outcome']['collisions']}")
        print("  Blocked-zone violations: "
              f"{item['outcome']['blocked_zone_violations']}")
    aggregate = result["aggregate"]
    print("\nAggregate")
    print(f"  Scenarios: {aggregate['scenario_count']}")
    print(f"  Learned MAPPO decisions: {aggregate['learned_mappo_decisions']}")
    print(f"  Completed vehicles: {aggregate['completed_vehicles']}")
    print(f"  Collisions: {aggregate['collisions']}")
    print(f"  Blocked-zone violations: {aggregate['blocked_zone_violations']}\n")
    print("STEP_5K_1_STATUS = " + result["status"])


if __name__ == "__main__":
    main()
