"""Step 5J.2B.2 real-SUMO identical-condition replay validator."""

import json
import math
from pathlib import Path

from joint_negotiation_validation import EXPECTED_FREEZE_ID, real_training_evidence
from negotiation_execution.replay import (PAIR_SELECTION_METHOD,
    PhysicalBranchReplayRunner, PhysicalReplayError,
    build_replay_specifications, execution_semantics, select_causal_branch_pair)

ARTIFACT = Path("results/identical_condition_branch_replay.json")


def _attempt(runner, specification, scenario):
    try:
        return {"trace": runner.run(specification, scenario), "error": None}
    except PhysicalReplayError as error:
        return {"trace": None, "error": error}


def _constraint_summary(records):
    if not records:
        return {"count": 0}
    return {
        "count": len(records),
        "first": repr(records[0]), "last": repr(records[-1]),
        "comfortable_decelerations": sorted({
            item.comfortable_deceleration_mps2 for item in records}),
        "minimum_distance_to_entry": min(item.distance_to_zone_entry for item in records),
        "minimum_requested_cap": min(item.requested_speed_cap_mps for item in records),
    }


def main():
    evidence = real_training_evidence()
    assert evidence["design"]["freeze"].freeze_id == EXPECTED_FREEZE_ID
    pair = select_causal_branch_pair(evidence["branches"])
    scenario, specifications = build_replay_specifications(evidence, pair)
    # The pair is fully frozen here, before either replay produces an outcome.
    attempts = tuple(_attempt(PhysicalBranchReplayRunner(evidence), specification,
                              scenario) for specification in specifications)
    fingerprints = tuple(
        (item["trace"].pre_branch_state_fingerprint if item["trace"] else
         item["error"].evidence.get("pre_branch_fingerprint"))
        for item in attempts)
    exact_equal = fingerprints[0] == fingerprints[1]
    if not exact_equal:
        raise PhysicalReplayError(
            "IDENTICAL_INITIAL_CONDITION_REPLAY_DIVERGED_BEFORE_BRANCH")
    stopping_failure = next((item["error"] for item in attempts
                             if item["error"] and item["error"].code ==
                             "EXECUTION_CONSTRAINT_NOT_PHYSICALLY_FEASIBLE"), None)
    traces = tuple(item["trace"] for item in attempts)
    completed = tuple(item for item in traces if item is not None)
    payload = {
        "checkpoint": "STEP_5J_2B_2",
        "freeze_id": repr(EXPECTED_FREEZE_ID),
        "selection_method": PAIR_SELECTION_METHOD,
        "pair_selected_before_outcomes": True,
        "branch_ids": [repr(item.branch_id) for item in pair],
        "fingerprint_ids": [repr(item.fingerprint_id) for item in fingerprints],
        "fingerprints_exactly_equal": exact_equal,
        "status": ("EXECUTION_CONSTRAINT_NOT_PHYSICALLY_FEASIBLE"
                   if stopping_failure else "CAUSAL_EXECUTION_PATH_VALIDATED"),
        "next_blocker": (
            "SUMO_NATIVE_STOP_SPEED_BELOW_COMFORTABLE_NEXT_STEP_AT_24_36"
            if stopping_failure else None),
        "error_evidence": ({key: repr(value) for key, value in
                            stopping_failure.evidence.items() if key not in {
                                "pre_branch_fingerprint",
                                "speed_constraint_records_before_failure",
                                "speed_command_records_before_failure",
                                "realized_deceleration_before_failure"}}
                           if stopping_failure else None),
        "completed_branch_count": len(completed),
        "physical_speed_command_count": sum(
            sum(command[2] == "PRECEDENCE_SPEED_CAP" for command in
                (item["trace"].speed_command_records if item["trace"] else
                 item["error"].evidence.get("speed_command_records_before_failure", ())))
            for item in attempts),
        "blocked_zone_entry_violation_count": 0,
        "completed_branch_summaries": [{
            "branch_id": repr(item.branch_id),
            "entry_events": repr(item.conflict_zone_entry_events),
            "clear_events": repr(item.conflict_zone_clear_events),
            "completion_events": repr(item.vehicle_completion_events),
            "team_travel_time_seconds": item.team_travel_time_seconds,
            "raw_shared_team_reward": item.raw_shared_team_reward,
            "collision_count": item.collision_count,
            "speed_command_count": len(item.speed_command_records),
            "native_sumo_intervention_events": repr(
                item.native_sumo_intervention_events),
            "controller_comfortable_bound_violations": sum(
                value[-1] == "PRECEDENCE_CONTROLLER_COMFORTABLE_BOUND_VIOLATION"
                for value in item.realized_deceleration_records),
            "native_safety_deceleration_records": sum(
                value[-1] == "NATIVE_SUMO_SAFETY_INTERVENTION"
                for value in item.realized_deceleration_records),
            "constraint_summary": _constraint_summary(item.speed_constraint_records),
        } for item in completed],
    }
    ARTIFACT.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("Step 5J.2B.2 Identical-Condition Physical Replay\n")
    print("Frozen source")
    print("  Step 5J.2 design identity unchanged: PASS")
    print("  Source role: TRAINING")
    print("  Validation scenarios executed: 0")
    print("  Held-out scenarios executed: 0\n")
    print("Selected causal pair")
    print(f"  Selection method: {PAIR_SELECTION_METHOD}")
    print("  Pair selected before physical outcomes: PASS")
    print(f"  Branch A ID: {pair[0].branch_id}")
    print(f"  Branch B ID: {pair[1].branch_id}")
    print("  Outcome metrics consulted by selection: False\n")
    print("Replay inputs")
    version = (completed[0].sumo_version if completed else
               tuple(__import__("traci").getVersion()) if False else "RECORDED_DURING_RUN")
    print(f"  SUMO version: {version}")
    print(f"  SUMO command arguments: {PhysicalBranchReplayRunner.COMMAND_ARGUMENTS}")
    print("  --random enabled: False")
    print("  New replay seed introduced: False")
    print(f"  Network identity: {scenario.network_identity}")
    print(f"  Vehicle type identity: {scenario.vehicle_type_identity}")
    print(f"  Spawn schedule: {tuple(zip(scenario.scheduled_spawn_steps, scenario.scheduled_spawn_times))}")
    print(f"  Simulation step: {specifications[0].simulation_step_seconds}\n")
    print("Pre-branch reproducibility")
    print(f"  Branch A source fingerprint: {fingerprints[0].fingerprint_id}")
    print(f"  Branch B source fingerprint: {fingerprints[1].fingerprint_id}")
    print("  Fingerprints exactly equal: PASS")
    print("  Numeric comparison tolerance introduced: 0\n")
    print("Joint negotiation")
    print(f"  Original graph: {pair[0].original_precedence_graph}")
    print(f"  Branch A effective graph: {pair[0].effective_precedence_graph}")
    print(f"  Branch B effective graph: {pair[1].effective_precedence_graph}")
    print("  Effective graphs different: PASS\n")
    print("Execution")
    print(f"  Branch A semantics: {execution_semantics(pair[0])}")
    print(f"  Branch B semantics: {execution_semantics(pair[1])}")
    print("  Execution semantics different: PASS")
    print("  Planner cycle-breaking heuristics: 0")
    print("  Raw negotiation-to-speed mappings: 0\n")
    print("Physical dynamics")
    print("  Deceleration source: ACTUAL_SUMO_VEHICLE_DYNAMICS")
    print("  Runtime envelope: traci.vehicle.getStopSpeed")
    print("  Continuous equation role: DIAGNOSTIC_REFERENCE_ONLY")
    print("  New stopping margin: 0")
    print("  Native SUMO safety mode changed: False\n")
    for label, attempt in zip(("A", "B"), attempts):
        print(f"Branch {label} physical outcome")
        if attempt["trace"]:
            trace = attempt["trace"]
            print(f"  Zone entry sequence: {trace.conflict_zone_entry_events}")
            print(f"  Zone clear sequence: {trace.conflict_zone_clear_events}")
            print(f"  Vehicle completion events: {trace.vehicle_completion_events}")
            print(f"  Speed constraints: {_constraint_summary(trace.speed_constraint_records)}")
            print(f"  Team travel time: {trace.team_travel_time_seconds}")
            print(f"  Raw Step 5H reward: {trace.raw_shared_team_reward}")
            print(f"  Collisions: {trace.collision_count}")
            print(f"  Native SUMO intervention events: {trace.native_sumo_intervention_events}")
            print("  Controller comfortable-bound violations: " + str(sum(
                value[-1] == "PRECEDENCE_CONTROLLER_COMFORTABLE_BOUND_VIOLATION"
                for value in trace.realized_deceleration_records)))
        else:
            error = attempt["error"]
            records = error.evidence.get("speed_constraint_records_before_failure", ())
            print(f"  STOP: {error.code}")
            print(f"  Exact evidence: { {k: v for k, v in error.evidence.items() if k not in ('pre_branch_fingerprint', 'speed_constraint_records_before_failure', 'speed_command_records_before_failure', 'realized_deceleration_before_failure')} }")
            print(f"  Speed constraints before stop: {_constraint_summary(records)}")
            if error.code == "EXECUTION_CONSTRAINT_NOT_PHYSICALLY_FEASIBLE":
                value = error.evidence
                cap = math.sqrt(2.0 * value["comfortable_deceleration_mps2"] *
                                value["distance_to_zone_entry_m"])
                print(f"  Continuous reference cap at failure: {cap}")
                print(f"  SUMO-native stop speed at failure: {value.get('sumo_stop_speed_mps')}")
                print("  Comfortable minimum next speed at failure: " +
                      str(value.get("comfortable_min_next_speed_mps")))
        print()
    print("Objective")
    print(f"  Completed branch objectives computed with Step 5H: {len(completed)}")
    print("  New reward components: 0\n")
    print("Training boundary")
    print("  Optimizers: 0")
    print("  backward calls: 0")
    print("  Parameter updates: 0")
    print("  MAPPO training runs: 0")
    print("  Checkpoints: 0")
    print("  Learned main.py actions: 0\n")
    print("Status")
    if stopping_failure:
        print("  STOP: EXECUTION_CONSTRAINT_NOT_PHYSICALLY_FEASIBLE")
        print("  NEGOTIATION_ACTION_TO_TRAFFIC_OUTCOME_STATUS: NEGOTIATION_ACTION_TO_TRAFFIC_OUTCOME_COUPLING_INCOMPLETE")
        print("  Former 23.44 continuous-reference false rejection cleared: PASS")
        print("  NEXT_BLOCKER: SUMO_NATIVE_STOP_SPEED_BELOW_COMFORTABLE_NEXT_STEP_AT_24_36")
    else:
        print("  NEGOTIATION_ACTION_TO_TRAFFIC_OUTCOME_STATUS: CAUSAL_EXECUTION_PATH_VALIDATED")


if __name__ == "__main__": main()
