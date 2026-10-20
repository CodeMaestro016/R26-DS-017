"""Run the three-scenario Step 5K.1 decentralized research demonstration."""

# Import argparse for use in this module.
import argparse
# Import json for use in this module.
import json
# Import Path from pathlib for the operations below.
from pathlib import Path

# Import ConflictZoneManager, MapPathManager from conflict for the operations below.
from conflict import ConflictZoneManager, MapPathManager
# Import ScenarioRole, build_design from experimentation for the operations below.
from experimentation import ScenarioRole, build_design
# Import NONCONFLICTING from negotiation_execution.physical_mapping for the operations below.
from negotiation_execution.physical_mapping import NONCONFLICTING
# Import _specification from negotiation_execution.replay for the operations below.
from negotiation_execution.replay import _specification
# Import serializable from negotiation_training.behavior_rollout for the operations below.
from negotiation_training.behavior_rollout import serializable
# Import atomic_write_json from negotiation_training.controlled_pilot for the operations below.
from negotiation_training.controlled_pilot import atomic_write_json
# Import DEMO_POLICY_PATH, SELECTION_RULE, SOURCE_CHECKPOINT, create_demo_policy, file_sha256, load_demo_policy
# from negotiation_training.demo_policy for the operations below.
from negotiation_training.demo_policy import (
    DEMO_POLICY_PATH, SELECTION_RULE, SOURCE_CHECKPOINT,
    create_demo_policy, file_sha256, load_demo_policy)
# Import DemonstrationMAPPOActionProvider from negotiation_training.demo_provider for the operations below.
from negotiation_training.demo_provider import DemonstrationMAPPOActionProvider
# Import CoupledNegotiationTrainingEnvironment from negotiation_training.environment for the operations below.
from negotiation_training.environment import CoupledNegotiationTrainingEnvironment


# Set RESULT_PATH to the result of Path(the text 'results/final_research_prototype_demo.json').
RESULT_PATH = Path("results/final_research_prototype_demo.json")
# Set SUMMARY_PATH to the result of Path(the text 'results/final_research_prototype_demo_summary.md').
SUMMARY_PATH = Path("results/final_research_prototype_demo_summary.md")
# Set GUI_RESULT_PATH to the result of Path(the text 'results/final_research_prototype_demo_gui.json').
GUI_RESULT_PATH = Path("results/final_research_prototype_demo_gui.json")
# Set GUI_SUMMARY_PATH to the result of Path(the text 'results/final_research_prototype_demo_gui_summary.md').
GUI_SUMMARY_PATH = Path("results/final_research_prototype_demo_gui_summary.md")
# Set SCENARIO_RULE to the text 'FROZEN_TRAINING_STRUCTURAL_COVERAGE_REGULATORY_CYCLE_MULTI_FAC...'.
SCENARIO_RULE = (
    "FROZEN_TRAINING_STRUCTURAL_COVERAGE_REGULATORY_CYCLE_"
    "MULTI_FACTOR_MULTI_ACTION_AUTHORITATIVE_NONPHYSICAL_EDGE_V1")


# Select demo scenarios using the inputs and processing steps below.
# Input design: the supplied design.
# Output: a tuple containing a dictionary containing category, signature, selection_evidence, a dictionary
# containing category,...
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def select_demo_scenarios(design=None):
    # Set design to design or the result of build_design().
    design = design or build_design()
    # Set training_ids to a set built from design['manifests'][ScenarioRole.TRAINING].scenario_ids.
    training_ids = set(
        # Supply design['manifests'][ScenarioRole.TRAINING].scenario_ids to set.
        design["manifests"][ScenarioRole.TRAINING].scenario_ids)
    # Set signatures to the sorted values from a lazy sequence of item for item in design at 'signatures'; retain
    # entries satisfying item.scenario_id belongs to training_ids.
    signatures = sorted(
        # Supply a lazy sequence of item for item in design at 'signatures'; retain entries satisfying
        # item.scenario_id belongs to training_ids to sorted.
        (item for item in design["signatures"]
         # Declare item as input parameter.
         if item.scenario_id in training_ids), key=lambda item: repr(item.scenario_id))
    # Set multi to the next item from a lazy sequence of item for item in signatures; retain entries satisfying
    # item.multi_factor_capable and item.multi_action_proposer_capable and...
    multi = next(item for item in signatures
                 # Evaluate item.multi_factor_capable and item.multi_action_proposer_capable and
                 # item.multi_action_responder_capable as part of the enclosing expression.
                 if item.multi_factor_capable and
                 # Evaluate item.multi_action_proposer_capable as part of the enclosing expression.
                 item.multi_action_proposer_capable and
                 # Evaluate item.multi_action_responder_capable as part of the enclosing expression.
                 item.multi_action_responder_capable)
    # Set cycle to the next item from a lazy sequence of item for item in signatures; retain entries satisfying
    # item.scenario_id differs from multi.scenario_id and item.cyclic_participant_count...
    cycle = next(item for item in signatures
                 # Evaluate item.scenario_id differs from multi.scenario_id and item.cyclic_participant_count
                 # equals item.participant_count and item.participant_count is at least 4 as part of the enclosing
                 # expression.
                 if item.scenario_id != multi.scenario_id and
                 # Evaluate item.cyclic_participant_count equals item.participant_count as part of the enclosing
                 # expression.
                 item.cyclic_participant_count == item.participant_count and
                 # Evaluate item.participant_count is at least 4 as part of the enclosing expression.
                 item.participant_count >= 4)
    # Set zones to the result of ConflictZoneManager(the result of MapPathManager()).
    zones = ConflictZoneManager(MapPathManager())
    # Set nonphysical to None.
    nonphysical = None
    # Set nonphysical_pair to None.
    nonphysical_pair = None
    # Iterate over signatures, binding each item to item.
    for item in signatures:
        # Run this branch when item.scenario_id belongs to a tuple containing multi.scenario_id,
        # cycle.scenario_id.
        if item.scenario_id in (multi.scenario_id, cycle.scenario_id):
            # Skip the rest of this loop iteration and process the next item.
            continue
        # Iterate over item.movement_path_ids, binding each item to first.
        for first in item.movement_path_ids:
            # Iterate over item.movement_path_ids, binding each item to second.
            for second in item.movement_path_ids:
                # Run this branch when first equals second.
                if first == second:
                    # Skip the rest of this loop iteration and process the next item.
                    continue
                # Set relationship to the result of zones.relationship(first, second).
                relationship = zones.relationship(first, second)
                # Run this branch when the negation of relationship.coordinated_conflict and the negation of
                # relationship.physical_overlap and relationship.conflict_zone_id is the same object as None.
                if (not relationship.coordinated_conflict and
                        # Evaluate the negation of relationship.physical_overlap as part of the enclosing
                        # expression.
                        not relationship.physical_overlap and
                        # Evaluate relationship.conflict_zone_id is the same object as None as part of the
                        # enclosing expression.
                        relationship.conflict_zone_id is None):
                    # Set (nonphysical, nonphysical_pair) to a tuple containing item, a tuple containing first,
                    # second.
                    nonphysical, nonphysical_pair = item, (first, second)
                    # Leave the nearest enclosing loop immediately.
                    break
            # Run this branch when nonphysical is a different object from None.
            if nonphysical is not None:
                # Leave the nearest enclosing loop immediately.
                break
        # Run this branch when nonphysical is a different object from None.
        if nonphysical is not None:
            # Leave the nearest enclosing loop immediately.
            break
    # Run this branch when nonphysical is the same object as None.
    if nonphysical is None:
        # Raise RuntimeError with the text 'STRUCTURAL_NONPHYSICAL_EDGE_SCENARIO_NOT_AVAILABLE' to stop this
        # execution path.
        raise RuntimeError("STRUCTURAL_NONPHYSICAL_EDGE_SCENARIO_NOT_AVAILABLE")
    # Return a tuple containing a dictionary containing category, signature, selection_evidence, a dictionary
    # containing category,... to the caller.
    return (
        # Store the text 'REGULATORY_CYCLE_NEGOTIATION' under 'category'.
        {"category": "REGULATORY_CYCLE_NEGOTIATION",
         # Store cycle under 'signature'.
         # Store a dictionary containing cyclic_participant_count, participant_count under 'selection_evidence'.
         "signature": cycle, "selection_evidence": {
             # Store cycle.cyclic_participant_count under 'cyclic_participant_count'.
             "cyclic_participant_count": cycle.cyclic_participant_count,
             # Store cycle.participant_count under 'participant_count'.
             "participant_count": cycle.participant_count}},
        # Store the text 'MULTI_FACTOR_MULTI_ACTION_NEGOTIATION' under 'category'.
        {"category": "MULTI_FACTOR_MULTI_ACTION_NEGOTIATION",
         # Store multi under 'signature'.
         # Store a dictionary containing potential_claim_factors, multi_factor_capable,
         # multi_action_proposer_capable,... under 'selection_evidence'.
         "signature": multi, "selection_evidence": {
             # Store multi.potential_claim_factors under 'potential_claim_factors'.
             "potential_claim_factors": multi.potential_claim_factors,
             # Store multi.multi_factor_capable under 'multi_factor_capable'.
             "multi_factor_capable": multi.multi_factor_capable,
             "multi_action_proposer_capable":
                 # Evaluate multi.multi_action_proposer_capable as part of the enclosing expression.
                 multi.multi_action_proposer_capable,
             "multi_action_responder_capable":
                 # Evaluate multi.multi_action_responder_capable as part of the enclosing expression.
                 multi.multi_action_responder_capable}},
        # Store the text 'COORDINATION_TO_NONPHYSICAL_EXECUTION_INTERPRETATION' under 'category'.
        {"category": "COORDINATION_TO_NONPHYSICAL_EXECUTION_INTERPRETATION",
         # Store nonphysical under 'signature'.
         # Store a dictionary containing authoritative_nonconflicting_movement_pair under 'selection_evidence'.
         "signature": nonphysical, "selection_evidence": {
             # Store nonphysical_pair under 'authoritative_nonconflicting_movement_pair'.
             "authoritative_nonconflicting_movement_pair": nonphysical_pair}})


# Scenario trace using the inputs and processing steps below.
# Input selected: the supplied selected.
# Input episode: the supplied episode.
# Input provider: the supplied provider.
# Output: a dictionary containing structural_category, selection_evidence, scenario_id, scenario_family,
# movement_paths,...
# Processing: select branches using the stated conditions.
def _scenario_trace(selected, episode, provider):
    # Set episode_id to episode.episode_id.
    episode_id = episode.episode_id
    # Set factors to a tuple built from a lazy sequence of item for item in provider.pending_factors; retain
    # entries satisfying item.episode_id equals episode_id.
    factors = tuple(item for item in provider.pending_factors
                    # Evaluate item.episode_id equals episode_id as part of the enclosing expression.
                    if item.episode_id == episode_id)
    # Set metadata to a tuple built from a lazy sequence of item for item in provider.batch_metadata; retain
    # entries satisfying item at 'episode_id' equals episode_id.
    metadata = tuple(item for item in provider.batch_metadata
                     # Evaluate item at 'episode_id' equals episode_id as part of the enclosing expression.
                     if item["episode_id"] == episode_id)
    # Set signature to selected at 'signature'.
    signature = selected["signature"]
    # Set graph_shapes to a tuple built from a lazy sequence of shape for batch in episode.joint_decision_batches.
    graph_shapes = tuple(shape for batch in episode.joint_decision_batches
                         # Evaluate batch.encoded_graph_shapes as part of the enclosing expression.
                         for shape in batch.encoded_graph_shapes)
    # Set node_counts to a tuple built from a lazy sequence of shape[0] at 0 for shape in graph_shapes.
    node_counts = tuple(shape[0][0] for shape in graph_shapes)
    # Set action_trace to a tuple built from a lazy sequence of a dictionary containing decision_role, ego_id,
    # claim_identity, proposal_id, available_semantic_actions,... for item in factors.
    action_trace = tuple({
        # Store item.decision_role under 'decision_role'.
        "decision_role": item.decision_role,
        # Store item.ego_id under 'ego_id'.
        "ego_id": item.ego_id,
        # Store the result of serializable(item.claim_identity) under 'claim_identity'.
        "claim_identity": serializable(item.claim_identity),
        # Store the result of serializable(item.proposal_id) under 'proposal_id'.
        "proposal_id": serializable(item.proposal_id),
        # Store the result of serializable(item.action_names) under 'available_semantic_actions'.
        "available_semantic_actions": serializable(item.action_names),
        # Store the result of serializable(item.hard_action_mask) under 'hard_action_mask'.
        "hard_action_mask": serializable(item.hard_action_mask),
        # Store the result of serializable(item.behavior_probability_vector) under 'actor_probability_vector'.
        "actor_probability_vector": serializable(
            # Supply item.behavior_probability_vector to serializable.
            item.behavior_probability_vector),
        # Store item.selected_action_index under 'selected_action_index'.
        "selected_action_index": item.selected_action_index,
        # Store item.selected_semantic_action under 'selected_semantic_action'.
        "selected_semantic_action": item.selected_semantic_action,
        # Store 0 under 'actor_route_truth_fields_consumed'.
        "actor_route_truth_fields_consumed": 0,
        # Store False under 'centralized_critic_used_for_action'.
        "centralized_critic_used_for_action": False,
        # Store True under 'ego_local_observation_used'.
        "ego_local_observation_used": True,
        # Store True under 'hard_action_mask_applied'.
        "hard_action_mask_applied": True}
        # Evaluate factors as part of the enclosing expression.
        for item in factors)
    # Run this branch when whether any item is true in a lazy sequence of the negation of item.hard_action_mask at
    # item.selected_action_index for item in factors.
    if any(not item.hard_action_mask[item.selected_action_index]
           # Evaluate factors as part of the enclosing expression.
           for item in factors):
        # Raise RuntimeError with the text 'DEMONSTRATION_HARD_ACTION_MASK_BYPASSED' to stop this execution path.
        raise RuntimeError("DEMONSTRATION_HARD_ACTION_MASK_BYPASSED")
    # Set edge_interpretations to a tuple built from a lazy sequence of interpretation for item in metadata.
    edge_interpretations = tuple(
        # Evaluate interpretation as part of the enclosing expression.
        interpretation for item in metadata
        # Evaluate 'edge_interpretations' from item; use an empty tuple if absent as part of the enclosing
        # expression.
        for interpretation in item.get("edge_interpretations", ()))
    # Return a dictionary containing structural_category, selection_evidence, scenario_id, scenario_family,
    # movement_paths,... to the caller.
    return {
        # Store selected at 'category' under 'structural_category'.
        "structural_category": selected["category"],
        # Store the result of serializable(selected at 'selection_evidence') under 'selection_evidence'.
        "selection_evidence": serializable(selected["selection_evidence"]),
        # Store the result of serializable(signature.scenario_id) under 'scenario_id'.
        "scenario_id": serializable(signature.scenario_id),
        # Store signature.scenario_family under 'scenario_family'.
        "scenario_family": signature.scenario_family,
        # Store a dictionary of formatted text built from the embedded values mapped to path for (index, path) in
        # index/value pairs from signature.movement_path_ids under 'movement_paths'.
        "movement_paths": {f"SCENARIO_AV_{index}": path for index, path in
                           # Evaluate index/value pairs from signature.movement_path_ids as part of the enclosing
                           # expression.
                           enumerate(signature.movement_path_ids)},
        # Store a dictionary containing av_count, encoded_ego_local_graph_count, maximum_locally_encoded_nodes,...
        # under 'perception'.
        "perception": {
            # Store signature.participant_count under 'av_count'.
            "av_count": signature.participant_count,
            # Store the number of entries in graph_shapes under 'encoded_ego_local_graph_count'.
            "encoded_ego_local_graph_count": len(graph_shapes),
            # Store the maximum of node_counts under 'maximum_locally_encoded_nodes'.
            "maximum_locally_encoded_nodes": max(node_counts, default=0),
            "locally_observed_neighbor_count_upper_bound":
                # Supply default as 0.
                max((value - 1 for value in node_counts), default=0),
            "unobserved_or_propagated_track_count":
                "NOT_RETAINED_BY_COUPLED_EPISODE_RECORD"},
        # Store a dictionary containing runtime_pipeline_active, per_vehicle_prediction_trace under
        # 'intention_prediction'.
        "intention_prediction": {
            # Store True under 'runtime_pipeline_active'.
            "runtime_pipeline_active": True,
            "per_vehicle_prediction_trace":
                "NOT_RETAINED_BY_COUPLED_EPISODE_RECORD"},
        # Store a dictionary containing coordination_edges, physical_execution_edges,
        # nonphysical_coordination_edges under 'conflict_reasoning'.
        "conflict_reasoning": {
            # Store the sum of a lazy sequence of 'coordination_edge_count' from item; use 0 if absent for item in
            # metadata under 'coordination_edges'.
            "coordination_edges": sum(
                # Evaluate 'coordination_edge_count' from item; use 0 if absent as part of the enclosing
                # expression.
                item.get("coordination_edge_count", 0) for item in metadata),
            # Store the sum of a lazy sequence of 'physical_execution_edge_count' from item; use 0 if absent for
            # item in metadata under 'physical_execution_edges'.
            "physical_execution_edges": sum(
                # Evaluate 'physical_execution_edge_count' from item; use 0 if absent as part of the enclosing
                # expression.
                item.get("physical_execution_edge_count", 0)
                # Evaluate metadata as part of the enclosing expression.
                for item in metadata),
            # Store the sum of a lazy sequence of 'nonphysical_coordination_edge_count' from item; use 0 if absent
            # for item in metadata under 'nonphysical_coordination_edges'.
            "nonphysical_coordination_edges": sum(
                # Evaluate 'nonphysical_coordination_edge_count' from item; use 0 if absent as part of the
                # enclosing expression.
                item.get("nonphysical_coordination_edge_count", 0)
                # Evaluate metadata as part of the enclosing expression.
                for item in metadata)},
        # Store a dictionary containing regulatory_cycle_expected_by_frozen_signature,
        # coordination_cycles_observed under 'traffic_rule_reasoning'.
        "traffic_rule_reasoning": {
            "regulatory_cycle_expected_by_frozen_signature":
                # Evaluate signature.cyclic_participant_count is greater than 0 as part of the enclosing
                # expression.
                signature.cyclic_participant_count > 0,
            # Store the sum of a lazy sequence of 'coordination_cycle_detected' from item; use False if absent for
            # item in metadata under 'coordination_cycles_observed'.
            "coordination_cycles_observed": sum(
                # Evaluate 'coordination_cycle_detected' from item; use False if absent as part of the enclosing
                # expression.
                item.get("coordination_cycle_detected", False)
                # Evaluate metadata as part of the enclosing expression.
                for item in metadata)},
        # Store a dictionary containing batch_count, proposer_decisions, responder_decisions, action_trace,...
        # under 'negotiation'.
        "negotiation": {
            # Store the number of entries in metadata under 'batch_count'.
            "batch_count": len(metadata),
            # Store the sum of a lazy sequence of item.decision_role equals the text 'PROPOSER' for item in
            # factors under 'proposer_decisions'.
            "proposer_decisions": sum(
                # Evaluate item.decision_role equals the text 'PROPOSER' as part of the enclosing expression.
                item.decision_role == "PROPOSER" for item in factors),
            # Store the sum of a lazy sequence of item.decision_role equals the text 'RESPONDER' for item in
            # factors under 'responder_decisions'.
            "responder_decisions": sum(
                # Evaluate item.decision_role equals the text 'RESPONDER' as part of the enclosing expression.
                item.decision_role == "RESPONDER" for item in factors),
            # Store action_trace under 'action_trace'.
            "action_trace": action_trace,
            # Store the result of serializable(a tuple built from a lazy sequence of 'effective_graph' from item;
            # use () if absent for item in...) under 'effective_coordination_graphs'.
            "effective_coordination_graphs": serializable(tuple(
                # Evaluate 'effective_graph' from item; use an empty tuple if absent as part of the enclosing
                # expression.
                item.get("effective_graph", ()) for item in metadata))},
        # Store a dictionary containing physical_execution_graphs, edge_interpretations,
        # physically_executable_outcomes,... under 'execution'.
        "execution": {
            # Store the result of serializable(a tuple built from a lazy sequence of 'physical_execution_graph'
            # from item; use () if absent for...) under 'physical_execution_graphs'.
            "physical_execution_graphs": serializable(tuple(
                # Evaluate 'physical_execution_graph' from item; use an empty tuple if absent as part of the
                # enclosing expression.
                item.get("physical_execution_graph", ()) for item in metadata)),
            # Store the result of serializable(edge_interpretations) under 'edge_interpretations'.
            "edge_interpretations": serializable(edge_interpretations),
            # Store the sum of a lazy sequence of 'graph_executable' from item; use False if absent for item in
            # metadata under 'physically_executable_outcomes'.
            "physically_executable_outcomes": sum(
                # Evaluate 'graph_executable' from item; use False if absent as part of the enclosing expression.
                item.get("graph_executable", False) for item in metadata),
            # Store the sum of a lazy sequence of item.execution_relevance equals NONCONFLICTING for item in
            # edge_interpretations under 'nonphysical_interpretations_observed'.
            "nonphysical_interpretations_observed": sum(
                # Evaluate item.execution_relevance equals NONCONFLICTING as part of the enclosing expression.
                item.execution_relevance == NONCONFLICTING
                # Evaluate edge_interpretations as part of the enclosing expression.
                for item in edge_interpretations)},
        # Store a dictionary containing actor_route_truth_fields_consumed, centralized_critic_used_for_action,...
        # under 'decentralization'.
        "decentralization": {
            # Store 0 under 'actor_route_truth_fields_consumed'.
            "actor_route_truth_fields_consumed": 0,
            # Store False under 'centralized_critic_used_for_action'.
            "centralized_critic_used_for_action": False,
            # Store True under 'ego_local_observation_used'.
            "ego_local_observation_used": True,
            # Store True under 'hard_action_mask_applied'.
            "hard_action_mask_applied": True},
        # Store a dictionary containing completed_vehicles, team_travel_time_seconds, collisions,
        # blocked_zone_violations,... under 'outcome'.
        "outcome": {
            # Store episode.completed_vehicle_count under 'completed_vehicles'.
            "completed_vehicles": episode.completed_vehicle_count,
            # Store episode.team_travel_time_seconds under 'team_travel_time_seconds'.
            "team_travel_time_seconds": episode.team_travel_time_seconds,
            # Store episode.collision_count under 'collisions'.
            "collisions": episode.collision_count,
            "blocked_zone_violations":
                # Evaluate episode.blocked_zone_entry_violation_count as part of the enclosing expression.
                episode.blocked_zone_entry_violation_count,
            "native_sumo_safety_interventions":
                # Evaluate episode.native_sumo_safety_intervention_count as part of the enclosing expression.
                episode.native_sumo_safety_intervention_count,
            # Store episode.sumo_step_count under 'sumo_steps'.
            "sumo_steps": episode.sumo_step_count,
            # Store episode.wall_clock_runtime_seconds under 'wall_clock_runtime_seconds'.
            "wall_clock_runtime_seconds": episode.wall_clock_runtime_seconds}}


# Write summary using the inputs and processing steps below.
# Input result: the supplied result.
# Input summary_path: the supplied summary path.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def _write_summary(result, summary_path=SUMMARY_PATH):
    # Set lines to a list containing the text '# Final Research Prototype Demonstration', the text '', the text
    # 'Project: Multi-Agent...
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
    # Iterate over result at 'per_scenario_evidence', binding each item to item.
    for item in result["per_scenario_evidence"]:
        # Extend lines with a tuple containing formatted text built from the embedded values.
        lines.extend((
            # Include formatted text built from the embedded values in this tuple.
            f"- {item['structural_category']}: `{item['scenario_id']}` — "
            # Evaluate {len(item['negotiation']['action_trace'])} as part of the enclosing expression.
            f"{len(item['negotiation']['action_trace'])} learned decisions, "
            # Evaluate {item['outcome']['completed_vehicles']} as part of the enclosing expression.
            f"{item['outcome']['completed_vehicles']} completed vehicles, "
            # Evaluate {item['outcome']['collisions']} as part of the enclosing expression.
            f"{item['outcome']['collisions']} collisions.",))
    # Extend lines with a tuple containing the text '', the text '## Boundary', the text '', the text 'This
    # validates end-to-end implementation, not...
    lines.extend(("", "## Boundary", "",
                  "This validates end-to-end implementation, not model optimality. "
                  "Exhaustive hyperparameter selection remains future work under "
                  "explicit project resource and statistical protocols."))
    # Write the supplied text to summary_path.
    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# Run demo using the inputs and processing steps below.
# Input use_gui: the supplied use gui.
# Output: result.
# Processing: iterate over the relevant records, then select branches using the stated conditions, then handle the
# specified errors.
def run_demo(use_gui=False):
    # Set use_gui to a Boolean built from use_gui.
    use_gui = bool(use_gui)
    # Set result_path to GUI_RESULT_PATH when use_gui, otherwise RESULT_PATH.
    result_path = GUI_RESULT_PATH if use_gui else RESULT_PATH
    # Set summary_path to GUI_SUMMARY_PATH when use_gui, otherwise SUMMARY_PATH.
    summary_path = GUI_SUMMARY_PATH if use_gui else SUMMARY_PATH
    # Set source_hash_before to the result of file_sha256(SOURCE_CHECKPOINT).
    source_hash_before = file_sha256(SOURCE_CHECKPOINT)
    # Call create_demo_policy with the supplied arguments.
    create_demo_policy()
    # Set policy to the result of load_demo_policy(DEMO_POLICY_PATH).
    policy = load_demo_policy(DEMO_POLICY_PATH)
    # Set provider to the result of DemonstrationMAPPOActionProvider(policy).
    provider = DemonstrationMAPPOActionProvider(policy)
    # Set hashes_before to the result of provider.inference_parameter_hashes().
    hashes_before = provider.inference_parameter_hashes()
    # Set design to the result of build_design().
    design = build_design()
    # Set selected to the result of select_demo_scenarios(design).
    selected = select_demo_scenarios(design)
    # Set traces to an empty list.
    traces = []
    # Set base to a dictionary containing checkpoint, source_demo_policy_identity,
    # source_training_checkpoint_identity,...
    base = {
        "checkpoint": "STEP_5K_1",
        # Store the result of serializable(policy at 'demo_policy_identity') under 'source_demo_policy_identity'.
        "source_demo_policy_identity": serializable(
            # Supply policy at 'demo_policy_identity' to serializable.
            policy["demo_policy_identity"]),
        # Store the result of serializable(policy at 'source_checkpoint_identity') under
        # 'source_training_checkpoint_identity'.
        "source_training_checkpoint_identity": serializable(
            # Supply policy at 'source_checkpoint_identity' to serializable.
            policy["source_checkpoint_identity"]),
        # Store SELECTION_RULE under 'demo_checkpoint_selection_rule'.
        "demo_checkpoint_selection_rule": SELECTION_RULE,
        # Store False under 'performance_selected'.
        "performance_selected": False,
        # Store False under 'statistical_selection_performed'.
        "statistical_selection_performed": False,
        # Store False under 'best_model'.
        # Store False under 'final_model'.
        # Store False under 'optimal_model'.
        "best_model": False, "final_model": False, "optimal_model": False,
        # Store True under 'decentralized_execution'.
        "decentralized_execution": True,
        # Store SCENARIO_RULE under 'scenario_selection_rule'.
        "scenario_selection_rule": SCENARIO_RULE,
        # Store False under 'scenario_selection_performance_based'.
        "scenario_selection_performance_based": False}
    # Attempt the enclosed operations and route matching exceptions to the handlers below.
    try:
        # Iterate over selected, binding each item to selected_item.
        for selected_item in selected:
            # Set specification to the result of _specification(design at 'payload',
            # selected_item['signature'].scenario_id).
            specification = _specification(
                # Supply selected_item['signature'].scenario_id to _specification.
                design["payload"], selected_item["signature"].scenario_id)
            # Set episode to the result of CoupledNegotiationTrainingEnvironment(provider,
            # use_gui=use_gui).run_episode(specification, design['manifests'][ScenarioRole.TRAINING].manifest_id).
            episode = CoupledNegotiationTrainingEnvironment(
                # Supply use_gui as use_gui.
                provider, use_gui=use_gui).run_episode(
                    # Supply specification to CoupledNegotiationTrainingEnvironment(provider,
                    # use_gui=use_gui).run_episode.
                    specification,
                    # Supply design['manifests'][ScenarioRole.TRAINING].manifest_id to
                    # CoupledNegotiationTrainingEnvironment(provider, use_gui=use_gui).run_episode.
                    design["manifests"][ScenarioRole.TRAINING].manifest_id)
            # Set trace to the result of _scenario_trace(selected_item, episode, provider).
            trace = _scenario_trace(selected_item, episode, provider)
            # Append trace to traces.
            traces.append(trace)
            # Run this branch when trace['outcome'] at 'collisions' or trace['outcome'] at
            # 'blocked_zone_violations'.
            if (trace["outcome"]["collisions"] or
                    # Evaluate trace['outcome'] at 'blocked_zone_violations' as part of the enclosing expression.
                    trace["outcome"]["blocked_zone_violations"]):
                # Raise RuntimeError with the text 'DEMONSTRATION_SAFETY_GATE_FAILED' to stop this execution path.
                raise RuntimeError("DEMONSTRATION_SAFETY_GATE_FAILED")
    # Handle Exception as error using the recovery steps below.
    except Exception as error:
        # Set failure to a dictionary containing status, failure, per_scenario_evidence,
        # source_checkpoint_sha256_before,...
        failure = {**base, "status": "DEMONSTRATION_SAFETY_GATE_FAILED"
                   # Evaluate a string built from error equals the text 'DEMONSTRATION_SAFETY_GATE_FAILED' as part
                   # of the enclosing expression.
                   if str(error) == "DEMONSTRATION_SAFETY_GATE_FAILED"
                   # Supply the text 'DEMONSTRATION_EXECUTION_FAILED' to the enclosing expression.
                   else "DEMONSTRATION_EXECUTION_FAILED",
                   # Store the result of repr(error) under 'failure'.
                   "failure": repr(error),
                   # Store traces under 'per_scenario_evidence'.
                   "per_scenario_evidence": traces,
                   # Store source_hash_before under 'source_checkpoint_sha256_before'.
                   "source_checkpoint_sha256_before": source_hash_before,
                   "source_checkpoint_sha256_after":
                       # Evaluate the result of file_sha256(SOURCE_CHECKPOINT) as part of the enclosing
                       # expression.
                       file_sha256(SOURCE_CHECKPOINT)}
        # Run this branch when use_gui.
        if use_gui:
            # Call atomic_write_json with the supplied arguments.
            atomic_write_json(GUI_RESULT_PATH, failure)
        # Run this alternative branch when the preceding branch does not apply.
        else:
            # Call atomic_write_json with the supplied arguments.
            atomic_write_json(RESULT_PATH, failure)
        # Re-raise the active exception.
        raise
    # Set hashes_after to the result of provider.inference_parameter_hashes().
    hashes_after = provider.inference_parameter_hashes()
    # Run this branch when hashes_after differs from hashes_before.
    if hashes_after != hashes_before:
        # Raise RuntimeError with the text 'DEMONSTRATION_POLICY_PARAMETER_MUTATION_DETECTED' to stop this
        # execution path.
        raise RuntimeError("DEMONSTRATION_POLICY_PARAMETER_MUTATION_DETECTED")
    # Set factors to a tuple built from provider.pending_factors.
    factors = tuple(provider.pending_factors)
    # Set metadata to a tuple built from provider.batch_metadata.
    metadata = tuple(provider.batch_metadata)
    # Set result to a dictionary containing status, ctde_runtime_critic_calls,
    # actor_route_truth_fields_consumed,...
    result = {
        # Evaluate base as part of the enclosing expression.
        **base,
        "status": "DECENTRALIZED_MAPPO_RESEARCH_PROTOTYPE_DEMONSTRATED",
        # Store provider.runtime_critic_calls under 'ctde_runtime_critic_calls'.
        "ctde_runtime_critic_calls": provider.runtime_critic_calls,
        "actor_route_truth_fields_consumed":
            # Evaluate provider.actor_route_truth_fields_consumed as part of the enclosing expression.
            provider.actor_route_truth_fields_consumed,
        # Store provider.ego_local_observation_used under 'ego_local_observation_used'.
        "ego_local_observation_used": provider.ego_local_observation_used,
        # Store provider.hard_action_mask_applied under 'hard_action_masks_active'.
        "hard_action_masks_active": provider.hard_action_mask_applied,
        # Store the result of serializable(policy at 'demonstration_action_sampling_seed_identity') under
        # 'demonstration_action_sampling_seed_identity'.
        "demonstration_action_sampling_seed_identity": serializable(
            # Supply policy at 'demonstration_action_sampling_seed_identity' to serializable.
            policy["demonstration_action_sampling_seed_identity"]),
        # Store a list of the result of serializable(item['signature'].scenario_id) for item in selected under
        # 'scenario_ids'.
        "scenario_ids": [serializable(item["signature"].scenario_id)
                         # Evaluate selected as part of the enclosing expression.
                         for item in selected],
        # Store traces under 'per_scenario_evidence'.
        "per_scenario_evidence": traces,
        # Store a dictionary containing scenario_count, completed_vehicles, team_travel_time_seconds,
        # collisions,... under 'aggregate'.
        "aggregate": {
            # Store the number of entries in traces under 'scenario_count'.
            "scenario_count": len(traces),
            # Store the sum of a lazy sequence of item['outcome'] at 'completed_vehicles' for item in traces under
            # 'completed_vehicles'.
            "completed_vehicles": sum(
                # Evaluate item['outcome'] at 'completed_vehicles' as part of the enclosing expression.
                item["outcome"]["completed_vehicles"] for item in traces),
            # Store the sum of a lazy sequence of item['outcome'] at 'team_travel_time_seconds' for item in traces
            # under 'team_travel_time_seconds'.
            "team_travel_time_seconds": sum(
                # Evaluate item['outcome'] at 'team_travel_time_seconds' as part of the enclosing expression.
                item["outcome"]["team_travel_time_seconds"] for item in traces),
            # Store 0 under 'collisions'.
            # Store 0 under 'blocked_zone_violations'.
            "collisions": 0, "blocked_zone_violations": 0,
            # Store the sum of a lazy sequence of item.decision_role equals the text 'PROPOSER' for item in
            # factors under 'learned_proposer_actions'.
            "learned_proposer_actions": sum(
                # Evaluate item.decision_role equals the text 'PROPOSER' as part of the enclosing expression.
                item.decision_role == "PROPOSER" for item in factors),
            # Store the sum of a lazy sequence of item.decision_role equals the text 'RESPONDER' for item in
            # factors under 'learned_responder_actions'.
            "learned_responder_actions": sum(
                # Evaluate item.decision_role equals the text 'RESPONDER' as part of the enclosing expression.
                item.decision_role == "RESPONDER" for item in factors),
            # Store the number of entries in factors under 'learned_mappo_decisions'.
            "learned_mappo_decisions": len(factors),
            # Store the number of entries in metadata under 'negotiation_batches'.
            "negotiation_batches": len(metadata),
            # Store the sum of a lazy sequence of 'coordination_cycle_detected' from item; use False if absent for
            # item in metadata under 'regulatory_cycles'.
            "regulatory_cycles": sum(
                # Evaluate 'coordination_cycle_detected' from item; use False if absent as part of the enclosing
                # expression.
                item.get("coordination_cycle_detected", False)
                # Evaluate metadata as part of the enclosing expression.
                for item in metadata),
            # Store the sum of a lazy sequence of 'graph_executable' from item; use False if absent for item in
            # metadata under 'physical_executable_outcomes'.
            "physical_executable_outcomes": sum(
                # Evaluate 'graph_executable' from item; use False if absent as part of the enclosing expression.
                item.get("graph_executable", False) for item in metadata),
            # Store the sum of a lazy sequence of 'nonphysical_coordination_edge_count' from item; use 0 if absent
            # for item in metadata under 'nonphysical_coordination_edges'.
            "nonphysical_coordination_edges": sum(
                # Evaluate 'nonphysical_coordination_edge_count' from item; use 0 if absent as part of the
                # enclosing expression.
                item.get("nonphysical_coordination_edge_count", 0)
                # Evaluate metadata as part of the enclosing expression.
                for item in metadata),
            # Store the sum of a lazy sequence of item['outcome'] at 'native_sumo_safety_interventions' for item
            # in traces under 'native_safety_interventions'.
            "native_safety_interventions": sum(
                # Evaluate item['outcome'] at 'native_sumo_safety_interventions' as part of the enclosing
                # expression.
                item["outcome"]["native_sumo_safety_interventions"]
                # Evaluate traces as part of the enclosing expression.
                for item in traces)},
        # Store hashes_before under 'parameter_hashes_before'.
        "parameter_hashes_before": hashes_before,
        # Store hashes_after under 'parameter_hashes_after'.
        "parameter_hashes_after": hashes_after,
        # Store True under 'policy_hashes_unchanged'.
        "policy_hashes_unchanged": True,
        # Store source_hash_before under 'source_checkpoint_sha256_before'.
        "source_checkpoint_sha256_before": source_hash_before,
        # Store the result of file_sha256(SOURCE_CHECKPOINT) under 'source_checkpoint_sha256_after'.
        "source_checkpoint_sha256_after": file_sha256(SOURCE_CHECKPOINT),
        "source_checkpoint_unchanged":
            # Evaluate the result of file_sha256(SOURCE_CHECKPOINT) equals source_hash_before as part of the
            # enclosing expression.
            file_sha256(SOURCE_CHECKPOINT) == source_hash_before,
        # Store 0 under 'training_operations'.
        # Store 0 under 'optimizer_instances'.
        "training_operations": 0, "optimizer_instances": 0,
        # Store 0 under 'optimizer_step_calls'.
        # Store 0 under 'backward_calls'.
        "optimizer_step_calls": 0, "backward_calls": 0,
        # Store 0 under 'ppo_updates'.
        # Store 0 under 'parameter_updates'.
        "ppo_updates": 0, "parameter_updates": 0,
        # Store 0 under 'new_training_episodes'.
        "new_training_episodes": 0,
        # Store 0 under 'validation_scenarios_used'.
        "validation_scenarios_used": 0,
        # Store 0 under 'held_out_scenarios_used'.
        "held_out_scenarios_used": 0,
        # Store 0 under 'normal_main_learned_actions'.
        "normal_main_learned_actions": 0}
    # Run this branch when result at 'ctde_runtime_critic_calls' differs from 0 or result at
    # 'actor_route_truth_fields_consumed' differs from 0 or result['aggregate'] at 'learned_proposer_actions' is
    # less than 1 or result['aggregate'] at 'learned_mappo_decisions' is less than 1 or the negation of result at
    # 'source_checkpoint_unchanged'.
    if (result["ctde_runtime_critic_calls"] != 0 or
            # Evaluate result at 'actor_route_truth_fields_consumed' differs from 0 as part of the enclosing
            # expression.
            result["actor_route_truth_fields_consumed"] != 0 or
            # Evaluate result['aggregate'] at 'learned_proposer_actions' is less than 1 as part of the enclosing
            # expression.
            result["aggregate"]["learned_proposer_actions"] < 1 or
            # Evaluate result['aggregate'] at 'learned_mappo_decisions' is less than 1 as part of the enclosing
            # expression.
            result["aggregate"]["learned_mappo_decisions"] < 1 or
            # Evaluate the negation of result at 'source_checkpoint_unchanged' as part of the enclosing
            # expression.
            not result["source_checkpoint_unchanged"]):
        # Set result['status'] to the text 'DEMONSTRATION_RUNTIME_BOUNDARY_FAILED'.
        result["status"] = "DEMONSTRATION_RUNTIME_BOUNDARY_FAILED"
        # Call atomic_write_json with the supplied arguments.
        atomic_write_json(result_path, result)
        # Raise RuntimeError with result at 'status' to stop this execution path.
        raise RuntimeError(result["status"])
    # Call atomic_write_json with the supplied arguments.
    atomic_write_json(result_path, result)
    # Call _write_summary with the supplied arguments.
    _write_summary(result, summary_path)
    # Return result to the caller.
    return result


# Parse args using the inputs and processing steps below.
# Input argv: the supplied argv.
# Output: the result of parser.parse_args(argv).
def parse_args(argv=None):
    # Set parser to the result of argparse.ArgumentParser().
    parser = argparse.ArgumentParser(
        # Supply description as the text 'Run the frozen decentralized MAPPO research demo.'.
        description="Run the frozen decentralized MAPPO research demo.")
    # Call parser.add_argument with the supplied arguments.
    parser.add_argument(
        # Supply action as the text 'store_true'.
        "--gui", action="store_true",
        # Supply help as the text 'visualize the unchanged demonstration with SUMO-GUI'.
        help="visualize the unchanged demonstration with SUMO-GUI")
    # Return the result of parser.parse_args(argv) to the caller.
    return parser.parse_args(argv)


# Main using the inputs and processing steps below.
# Input argv: the supplied argv.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def main(argv=None):
    # Set args to the result of parse_args(argv).
    args = parse_args(argv)
    # Display the text 'Final MAPPO research demo mode:' plus the text 'SUMO-GUI' when args.gui, otherwise the
    # text 'headless SUMO'.
    print("Final MAPPO research demo mode: " +
          # Evaluate the text 'SUMO-GUI' when args.gui, otherwise the text 'headless SUMO' as part of the
          # enclosing expression.
          ("SUMO-GUI" if args.gui else "headless SUMO"))
    # Display the text 'Policy execution: decentralized'.
    print("Policy execution: decentralized")
    # Display the text 'Centralized critic at runtime: disabled'.
    print("Centralized critic at runtime: disabled")
    # Display the text 'Training/parameter updates: disabled'.
    print("Training/parameter updates: disabled\n")
    # Set result to the result of run_demo().
    result = run_demo(use_gui=args.gui)
    # Display the text 'Final Research Prototype Demonstration'.
    print("Final Research Prototype Demonstration\n")
    # Display the text 'Policy'.
    print("Policy")
    # Display the text 'Type: RESEARCH_PROTOTYPE_DEMONSTRATION_POLICY'.
    print("  Type: RESEARCH_PROTOTYPE_DEMONSTRATION_POLICY")
    # Display the text 'Source replication: 0'.
    print("  Source replication: 0")
    # Display the text 'Source state: 2'.
    print("  Source state: 2")
    # Display the text 'Performance-selected: False'.
    print("  Performance-selected: False")
    # Display the text 'Final/optimal claim: False'.
    print("  Final/optimal claim: False\n")
    # Display the text 'Architecture'.
    print("Architecture")
    # Display the text 'Decentralized actor execution: PASS'.
    print("  Decentralized actor execution: PASS")
    # Display formatted text built from the embedded values.
    print(f"  Centralized critic runtime use: {result['ctde_runtime_critic_calls']}")
    # Display formatted text built from the embedded values.
    print(f"  Route-truth actor leakage: {result['actor_route_truth_fields_consumed']}")
    # Display the text 'Hard masks active: PASS'.
    print("  Hard masks active: PASS")
    # Iterate over index/value pairs from result at 'per_scenario_evidence', binding each item to (index, item).
    for index, item in enumerate(result["per_scenario_evidence"], 1):
        # Display formatted text built from the embedded values.
        print(f"\nScenario {index}/3")
        # Display formatted text built from the embedded values.
        print(f"  Category: {item['structural_category']}")
        # Display formatted text built from the embedded values.
        print(f"  Scenario ID: {item['scenario_id']}")
        # Display formatted text built from the embedded values.
        print(f"  Negotiation actions: {len(item['negotiation']['action_trace'])}")
        # Display formatted text built from the embedded values.
        print(f"  Proposer: {item['negotiation']['proposer_decisions']}")
        # Display formatted text built from the embedded values.
        print(f"  Responder: {item['negotiation']['responder_decisions']}")
        # Display formatted text built from the embedded values.
        print(f"  Completed vehicles: {item['outcome']['completed_vehicles']}")
        # Display formatted text built from the embedded values.
        print(f"  Physical outcomes: {item['execution']['physically_executable_outcomes']}")
        # Display formatted text built from the embedded values.
        print(f"  Collision: {item['outcome']['collisions']}")
        # Display formatted text built from the embedded values.
        print("  Blocked-zone violations: "
              # Evaluate {item['outcome']['blocked_zone_violations']} as part of the enclosing expression.
              f"{item['outcome']['blocked_zone_violations']}")
    # Set aggregate to result at 'aggregate'.
    aggregate = result["aggregate"]
    # Display the text 'Aggregate'.
    print("\nAggregate")
    # Display formatted text built from the embedded values.
    print(f"  Scenarios: {aggregate['scenario_count']}")
    # Display formatted text built from the embedded values.
    print(f"  Learned MAPPO decisions: {aggregate['learned_mappo_decisions']}")
    # Display formatted text built from the embedded values.
    print(f"  Completed vehicles: {aggregate['completed_vehicles']}")
    # Display formatted text built from the embedded values.
    print(f"  Collisions: {aggregate['collisions']}")
    # Display formatted text built from the embedded values.
    print(f"  Blocked-zone violations: {aggregate['blocked_zone_violations']}\n")
    # Display the text 'STEP_5K_1_STATUS =' plus result at 'status'.
    print("STEP_5K_1_STATUS = " + result["status"])


# Run this branch when __name__ equals the text '__main__'.
if __name__ == "__main__":
    # Call main with the supplied arguments.
    main()
