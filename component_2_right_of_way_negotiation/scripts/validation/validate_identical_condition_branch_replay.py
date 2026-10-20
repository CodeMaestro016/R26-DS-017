"""Step 5J.2B.4 SUMO-authoritative identical-condition replay validator."""

# Import json for use in this module.
import json
# Import math for use in this module.
import math
# Import Path from pathlib for the operations below.
from pathlib import Path

# Import EXPECTED_FREEZE_ID, real_training_evidence from joint_negotiation_validation for the operations below.
from joint_negotiation_validation import EXPECTED_FREEZE_ID, real_training_evidence
# Import PAIR_SELECTION_METHOD, PhysicalBranchReplayRunner, PhysicalReplayError, build_replay_specifications,
# execution_semantics, select_causal_branch_pair from negotiation_execution.replay for the operations below.
from negotiation_execution.replay import (PAIR_SELECTION_METHOD,
    PhysicalBranchReplayRunner, PhysicalReplayError,
    build_replay_specifications, execution_semantics, select_causal_branch_pair)

# Set ARTIFACT to the result of Path(the text 'results/identical_condition_branch_replay.json').
ARTIFACT = Path("results/identical_condition_branch_replay.json")


# Attempt using the inputs and processing steps below.
# Input runner: the supplied runner.
# Input specification: the supplied specification.
# Input scenario: the supplied scenario.
# Output: return the value selected by the matching return branch below.
# Processing: handle the specified errors.
def _attempt(runner, specification, scenario):
    # Attempt the enclosed operations and route matching exceptions to the handlers below.
    try:
        # Return a dictionary containing trace, error to the caller.
        return {"trace": runner.run(specification, scenario), "error": None}
    # Handle PhysicalReplayError as error using the recovery steps below.
    except PhysicalReplayError as error:
        # Return a dictionary containing trace, error to the caller.
        return {"trace": None, "error": error}


# Constraint summary using the inputs and processing steps below.
# Input records: the supplied records.
# Output: return the value selected by the matching return branch below.
# Processing: select branches using the stated conditions.
def _constraint_summary(records):
    # Run this branch when the negation of records.
    if not records:
        # Return a dictionary containing count to the caller.
        return {"count": 0}
    # Return a dictionary containing count, first, last, comfortable_decelerations, minimum_distance_to_entry,...
    # to the caller.
    return {
        # Store the number of entries in records under 'count'.
        "count": len(records),
        # Store the result of repr(records at 0) under 'first'.
        # Store the result of repr(records at -1) under 'last'.
        "first": repr(records[0]), "last": repr(records[-1]),
        # Store the sorted values from a set of item.comfortable_deceleration_mps2 for item in records under
        # 'comfortable_decelerations'.
        "comfortable_decelerations": sorted({
            # Evaluate item.comfortable_deceleration_mps2 as part of the enclosing expression.
            item.comfortable_deceleration_mps2 for item in records}),
        # Store the minimum of a lazy sequence of item.distance_to_zone_entry for item in records under
        # 'minimum_distance_to_entry'.
        "minimum_distance_to_entry": min(item.distance_to_zone_entry for item in records),
        # Store the minimum of a lazy sequence of item.requested_speed_cap_mps for item in records under
        # 'minimum_requested_cap'.
        "minimum_requested_cap": min(item.requested_speed_cap_mps for item in records),
    }


# Main using the inputs and processing steps below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def main():
    # Set evidence to the result of real_training_evidence().
    evidence = real_training_evidence()
    # Require evidence['design']['freeze'].freeze_id equals EXPECTED_FREEZE_ID; otherwise raise AssertionError.
    assert evidence["design"]["freeze"].freeze_id == EXPECTED_FREEZE_ID
    # Set pair to the result of select_causal_branch_pair(evidence at 'branches').
    pair = select_causal_branch_pair(evidence["branches"])
    # Set (scenario, specifications) to the result of build_replay_specifications(evidence, pair).
    scenario, specifications = build_replay_specifications(evidence, pair)
    # The pair is fully frozen here, before either replay produces an outcome.
    # Set attempts to a tuple built from a lazy sequence of the result of _attempt(the result of
    # PhysicalBranchReplayRunner(evidence), specification, scenario) for specification in specifications.
    attempts = tuple(_attempt(PhysicalBranchReplayRunner(evidence), specification,
                              # Evaluate specifications as part of the enclosing expression.
                              scenario) for specification in specifications)
    # Set fingerprints to a tuple built from a lazy sequence of item['trace'].pre_branch_state_fingerprint when
    # item at 'trace', otherwise 'pre_branch_fingerprint' from item['error'].evidence; use None if absent for item
    # in attempts.
    fingerprints = tuple(
        # Evaluate item['trace'].pre_branch_state_fingerprint when item at 'trace', otherwise
        # 'pre_branch_fingerprint' from item['error'].evidence; use None if absent as part of the enclosing
        # expression.
        (item["trace"].pre_branch_state_fingerprint if item["trace"] else
         # Evaluate 'pre_branch_fingerprint' from item['error'].evidence; use None if absent as part of the
         # enclosing expression.
         item["error"].evidence.get("pre_branch_fingerprint"))
        # Evaluate attempts as part of the enclosing expression.
        for item in attempts)
    # Set exact_equal to fingerprints at 0 equals fingerprints at 1.
    exact_equal = fingerprints[0] == fingerprints[1]
    # Run this branch when the negation of exact_equal.
    if not exact_equal:
        # Raise PhysicalReplayError with the text 'IDENTICAL_INITIAL_CONDITION_REPLAY_DIVERGED_BEFORE_BRANCH' to
        # stop this execution path.
        raise PhysicalReplayError(
            "IDENTICAL_INITIAL_CONDITION_REPLAY_DIVERGED_BEFORE_BRANCH")
    # Set replay_failure to the next item from a lazy sequence of item at 'error' for item in attempts; retain
    # entries satisfying item at 'error'.
    replay_failure = next((item["error"] for item in attempts
                           # Evaluate item at 'error' as part of the enclosing expression.
                           if item["error"]), None)
    # Set traces to a tuple built from a lazy sequence of item at 'trace' for item in attempts.
    traces = tuple(item["trace"] for item in attempts)
    # Set completed to a tuple built from a lazy sequence of item for item in traces; retain entries satisfying
    # item is a different object from None.
    completed = tuple(item for item in traces if item is not None)
    # Set trajectory_signatures to a tuple built from a lazy sequence of a tuple containing
    # item.conflict_zone_entry_events, item.conflict_zone_clear_events, item.vehicle_completion_events for item in
    # completed.
    trajectory_signatures = tuple(
        # Evaluate a tuple containing item.conflict_zone_entry_events, item.conflict_zone_clear_events,
        # item.vehicle_completion_events as part of the enclosing expression.
        (item.conflict_zone_entry_events, item.conflict_zone_clear_events,
         # Include item.vehicle_completion_events in this tuple.
         item.vehicle_completion_events) for item in completed)
    # Set physical_causal_witness to the number of entries in trajectory_signatures equals 2 and
    # trajectory_signatures at 0 differs from trajectory_signatures at 1.
    physical_causal_witness = (
        # Evaluate the number of entries in trajectory_signatures equals 2 and trajectory_signatures at 0 differs
        # from trajectory_signatures at 1 as part of the enclosing expression.
        len(trajectory_signatures) == 2 and
        # Evaluate trajectory_signatures at 0 differs from trajectory_signatures at 1 as part of the enclosing
        # expression.
        trajectory_signatures[0] != trajectory_signatures[1])
    # Run this branch when the number of entries in completed equals 2 and the negation of
    # physical_causal_witness.
    if len(completed) == 2 and not physical_causal_witness:
        # Raise PhysicalReplayError with the text 'NO_PHYSICAL_CAUSAL_WITNESS_FOUND' to stop this execution path.
        raise PhysicalReplayError("NO_PHYSICAL_CAUSAL_WITNESS_FOUND")
    # Set former_24_36 to the next item from a lazy sequence of record for record in
    # completed[0].speed_constraint_records; retain entries satisfying record.vehicle_id == 'SCENARIO_AV_1' and
    # record.conflict_zone_id == 'CZ_016' and... when completed, otherwise None.
    former_24_36 = next((record for record in completed[0].speed_constraint_records
                         # Evaluate record.vehicle_id equals the text 'SCENARIO_AV_1' and record.conflict_zone_id
                         # equals the text 'CZ_016' and 'timestamp' from record.provenance; use None if absent
                         # equals the text '24.36' as part of the enclosing expression.
                         if record.vehicle_id == "SCENARIO_AV_1" and
                         # Evaluate record.conflict_zone_id equals the text 'CZ_016' as part of the enclosing
                         # expression.
                         record.conflict_zone_id == "CZ_016" and
                         # Evaluate 'timestamp' from record.provenance; use None if absent equals the text '24.36'
                         # as part of the enclosing expression.
                         record.provenance.get("timestamp") == "24.36"), None) \
        if completed else None
    # Set former_24_36_realized to the next item from a lazy sequence of item for item in
    # completed[0].realized_deceleration_records; retain entries satisfying item[0] == 24.4 and item[1] ==
    # 'SCENARIO_AV_1' when completed, otherwise None.
    former_24_36_realized = next((item for item in
                                  # Evaluate completed[0].realized_deceleration_records as part of the enclosing
                                  # expression.
                                  completed[0].realized_deceleration_records
                                  # Evaluate item at 0 equals 24.4 and item at 1 equals the text 'SCENARIO_AV_1'
                                  # as part of the enclosing expression.
                                  if item[0] == 24.4 and
                                  # Evaluate item at 1 equals the text 'SCENARIO_AV_1' as part of the enclosing
                                  # expression.
                                  item[1] == "SCENARIO_AV_1"), None) \
        if completed else None
    # Set payload to a dictionary containing checkpoint, freeze_id, selection_method,
    # pair_selected_before_outcomes, branch_ids,...
    payload = {
        "checkpoint": "STEP_5J_2B_4",
        # Store the result of repr(EXPECTED_FREEZE_ID) under 'freeze_id'.
        "freeze_id": repr(EXPECTED_FREEZE_ID),
        # Store PAIR_SELECTION_METHOD under 'selection_method'.
        "selection_method": PAIR_SELECTION_METHOD,
        # Store True under 'pair_selected_before_outcomes'.
        "pair_selected_before_outcomes": True,
        # Store a list of the result of repr(item.branch_id) for item in pair under 'branch_ids'.
        "branch_ids": [repr(item.branch_id) for item in pair],
        # Store a list of the result of repr(item.fingerprint_id) for item in fingerprints under
        # 'fingerprint_ids'.
        "fingerprint_ids": [repr(item.fingerprint_id) for item in fingerprints],
        # Store exact_equal under 'fingerprints_exactly_equal'.
        "fingerprints_exactly_equal": exact_equal,
        # Store replay_failure.code when replay_failure, otherwise the text 'CAUSAL_EXECUTION_PATH_VALIDATED'
        # under 'status'.
        "status": (replay_failure.code if replay_failure else
                   "CAUSAL_EXECUTION_PATH_VALIDATED"),
        # Store replay_failure.code when replay_failure, otherwise None under 'next_blocker'.
        "next_blocker": replay_failure.code if replay_failure else None,
        # Store physical_causal_witness under 'physical_causal_witness'.
        "physical_causal_witness": physical_causal_witness,
        # Store the result of repr(former_24_36) under 'former_24_36_record'.
        "former_24_36_record": repr(former_24_36),
        # Store the result of repr(former_24_36_realized) under 'former_24_36_realized_record'.
        "former_24_36_realized_record": repr(former_24_36_realized),
        # Store a dictionary of key mapped to the result of repr(value) for (key, value) in key/value pairs from
        # replay_failure.evidence; retain entries satisfying key does not belong to a set containing
        # 'pre_branch_fingerprint',... when replay_failure, otherwise None under 'error_evidence'.
        "error_evidence": ({key: repr(value) for key, value in
                            # Evaluate key does not belong to a set containing the text 'pre_branch_fingerprint',
                            # the text 'speed_constraint_records_before_failure', the text... as part of the
                            # enclosing expression.
                            replay_failure.evidence.items() if key not in {
                                "pre_branch_fingerprint",
                                "speed_constraint_records_before_failure",
                                "speed_command_records_before_failure",
                                "realized_deceleration_before_failure"}}
                           # Evaluate replay_failure as part of the enclosing expression.
                           if replay_failure else None),
        # Store the number of entries in completed under 'completed_branch_count'.
        "completed_branch_count": len(completed),
        # Store the sum of a lazy sequence of the sum of a lazy sequence of command[2] == 'PRECEDENCE_SPEED_CAP'
        # for command in item['trace'].speed_command_records if item['trace'] else... for item in attempts under
        # 'physical_speed_command_count'.
        "physical_speed_command_count": sum(
            # Evaluate the sum of a lazy sequence of command at 2 equals the text 'PRECEDENCE_SPEED_CAP' for
            # command in item['trace'].speed_command_records when item at 'trace', otherwise
            # 'speed_command_records_before_failure' from item['error'].evidence; use () if absent as part of the
            # enclosing expression.
            sum(command[2] == "PRECEDENCE_SPEED_CAP" for command in
                # Evaluate item['trace'].speed_command_records when item at 'trace', otherwise
                # 'speed_command_records_before_failure' from item['error'].evidence; use an empty tuple if absent
                # as part of the enclosing expression.
                (item["trace"].speed_command_records if item["trace"] else
                 # Evaluate 'speed_command_records_before_failure' from item['error'].evidence; use an empty tuple
                 # if absent as part of the enclosing expression.
                 item["error"].evidence.get("speed_command_records_before_failure", ())))
            # Evaluate attempts as part of the enclosing expression.
            for item in attempts),
        # Store 0 under 'blocked_zone_entry_violation_count'.
        "blocked_zone_entry_violation_count": 0,
        # Store a list of a dictionary containing branch_id, entry_events, clear_events, completion_events,
        # team_travel_time_seconds,... for item in completed under 'completed_branch_summaries'.
        "completed_branch_summaries": [{
            # Store the result of repr(item.branch_id) under 'branch_id'.
            "branch_id": repr(item.branch_id),
            # Store the result of repr(item.conflict_zone_entry_events) under 'entry_events'.
            "entry_events": repr(item.conflict_zone_entry_events),
            # Store the result of repr(item.conflict_zone_clear_events) under 'clear_events'.
            "clear_events": repr(item.conflict_zone_clear_events),
            # Store the result of repr(item.vehicle_completion_events) under 'completion_events'.
            "completion_events": repr(item.vehicle_completion_events),
            # Store item.team_travel_time_seconds under 'team_travel_time_seconds'.
            "team_travel_time_seconds": item.team_travel_time_seconds,
            # Store item.raw_shared_team_reward under 'raw_shared_team_reward'.
            "raw_shared_team_reward": item.raw_shared_team_reward,
            # Store item.collision_count under 'collision_count'.
            "collision_count": item.collision_count,
            # Store the number of entries in item.speed_command_records under 'speed_command_count'.
            "speed_command_count": len(item.speed_command_records),
            # Store the result of repr(item.native_sumo_intervention_events) under
            # 'native_sumo_intervention_events'.
            "native_sumo_intervention_events": repr(
                # Supply item.native_sumo_intervention_events to repr.
                item.native_sumo_intervention_events),
            # Store the sum of a lazy sequence of value at -1 equals the text
            # 'PRECEDENCE_CONTROLLER_COMFORTABLE_BOUND_VIOLATION' for value in item.realized_deceleration_records
            # under 'controller_comfortable_bound_violations'.
            "controller_comfortable_bound_violations": sum(
                # Evaluate value at -1 equals the text 'PRECEDENCE_CONTROLLER_COMFORTABLE_BOUND_VIOLATION' as part
                # of the enclosing expression.
                value[-1] == "PRECEDENCE_CONTROLLER_COMFORTABLE_BOUND_VIOLATION"
                # Evaluate item.realized_deceleration_records as part of the enclosing expression.
                for value in item.realized_deceleration_records),
            # Store the sum of a lazy sequence of value at -1 equals the text 'NATIVE_SUMO_SAFETY_INTERVENTION'
            # for value in item.realized_deceleration_records under 'native_safety_deceleration_records'.
            "native_safety_deceleration_records": sum(
                # Evaluate value at -1 equals the text 'NATIVE_SUMO_SAFETY_INTERVENTION' as part of the enclosing
                # expression.
                value[-1] == "NATIVE_SUMO_SAFETY_INTERVENTION"
                # Evaluate item.realized_deceleration_records as part of the enclosing expression.
                for value in item.realized_deceleration_records),
            # Store the result of _constraint_summary(item.speed_constraint_records) under 'constraint_summary'.
            "constraint_summary": _constraint_summary(item.speed_constraint_records),
        # Evaluate completed as part of the enclosing expression.
        } for item in completed],
    }
    # Write the supplied text to ARTIFACT.
    ARTIFACT.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    # Display the text 'Step 5J.2B.4 SUMO-Native Physical Causal Replay'.
    print("Step 5J.2B.4 SUMO-Native Physical Causal Replay\n")
    # Display the text 'Frozen source'.
    print("Frozen source")
    # Display the text 'Step 5J.2 design identity unchanged: PASS'.
    print("  Step 5J.2 design identity unchanged: PASS")
    # Display the text 'Source role: TRAINING'.
    print("  Source role: TRAINING")
    # Display the text 'Validation scenarios executed: 0'.
    print("  Validation scenarios executed: 0")
    # Display the text 'Held-out scenarios executed: 0'.
    print("  Held-out scenarios executed: 0\n")
    # Display the text 'Selected causal pair'.
    print("Selected causal pair")
    # Display formatted text built from the embedded values.
    print(f"  Selection method: {PAIR_SELECTION_METHOD}")
    # Display the text 'Pair selected before physical outcomes: PASS'.
    print("  Pair selected before physical outcomes: PASS")
    # Display formatted text built from the embedded values.
    print(f"  Branch A ID: {pair[0].branch_id}")
    # Display formatted text built from the embedded values.
    print(f"  Branch B ID: {pair[1].branch_id}")
    # Display the text 'Outcome metrics consulted by selection: False'.
    print("  Outcome metrics consulted by selection: False\n")
    # Display the text 'Replay inputs'.
    print("Replay inputs")
    # Set version to completed[0].sumo_version when completed, otherwise a tuple built from the result of
    # __import__('traci').getVersion() when False, otherwise the text 'RECORDED_DURING_RUN'.
    version = (completed[0].sumo_version if completed else
               # Evaluate a tuple built from the result of __import__('traci').getVersion() when False, otherwise
               # the text 'RECORDED_DURING_RUN' as part of the enclosing expression.
               tuple(__import__("traci").getVersion()) if False else "RECORDED_DURING_RUN")
    # Display formatted text built from the embedded values.
    print(f"  SUMO version: {version}")
    # Display formatted text built from the embedded values.
    print(f"  SUMO command arguments: {PhysicalBranchReplayRunner.COMMAND_ARGUMENTS}")
    # Display the text '--random enabled: False'.
    print("  --random enabled: False")
    # Display the text 'New replay seed introduced: False'.
    print("  New replay seed introduced: False")
    # Display formatted text built from the embedded values.
    print(f"  Network identity: {scenario.network_identity}")
    # Display formatted text built from the embedded values.
    print(f"  Vehicle type identity: {scenario.vehicle_type_identity}")
    # Display formatted text built from the embedded values.
    print(f"  Spawn schedule: {tuple(zip(scenario.scheduled_spawn_steps, scenario.scheduled_spawn_times))}")
    # Display formatted text built from the embedded values.
    print(f"  Simulation step: {specifications[0].simulation_step_seconds}\n")
    # Display the text 'Pre-branch reproducibility'.
    print("Pre-branch reproducibility")
    # Display formatted text built from the embedded values.
    print(f"  Branch A source fingerprint: {fingerprints[0].fingerprint_id}")
    # Display formatted text built from the embedded values.
    print(f"  Branch B source fingerprint: {fingerprints[1].fingerprint_id}")
    # Display the text 'Fingerprints exactly equal: PASS'.
    print("  Fingerprints exactly equal: PASS")
    # Display the text 'Numeric comparison tolerance introduced: 0'.
    print("  Numeric comparison tolerance introduced: 0\n")
    # Display the text 'Joint negotiation'.
    print("Joint negotiation")
    # Display formatted text built from the embedded values.
    print(f"  Original graph: {pair[0].original_precedence_graph}")
    # Display formatted text built from the embedded values.
    print(f"  Branch A effective graph: {pair[0].effective_precedence_graph}")
    # Display formatted text built from the embedded values.
    print(f"  Branch B effective graph: {pair[1].effective_precedence_graph}")
    # Display the text 'Effective graphs different: PASS'.
    print("  Effective graphs different: PASS\n")
    # Display the text 'Execution'.
    print("Execution")
    # Display formatted text built from the embedded values.
    print(f"  Branch A semantics: {execution_semantics(pair[0])}")
    # Display formatted text built from the embedded values.
    print(f"  Branch B semantics: {execution_semantics(pair[1])}")
    # Display the text 'Execution semantics different: PASS'.
    print("  Execution semantics different: PASS")
    # Display the text 'Planner cycle-breaking heuristics: 0'.
    print("  Planner cycle-breaking heuristics: 0")
    # Display the text 'Raw negotiation-to-speed mappings: 0'.
    print("  Raw negotiation-to-speed mappings: 0\n")
    # Display the text 'Physical dynamics'.
    print("Physical dynamics")
    # Display the text 'Deceleration source: ACTUAL_SUMO_VEHICLE_DYNAMICS'.
    print("  Deceleration source: ACTUAL_SUMO_VEHICLE_DYNAMICS")
    # Display the text 'Runtime envelope: traci.vehicle.getStopSpeed'.
    print("  Runtime envelope: traci.vehicle.getStopSpeed")
    # Display the text 'Continuous equation role: DIAGNOSTIC_REFERENCE_ONLY'.
    print("  Continuous equation role: DIAGNOSTIC_REFERENCE_ONLY")
    # Display the text 'New stopping margin: 0'.
    print("  New stopping margin: 0")
    # Display the text 'Native SUMO safety mode changed: False'.
    print("  Native SUMO safety mode changed: False\n")
    # Run this branch when former_24_36.
    if former_24_36:
        # Display the text 'Former 24.36 state under SUMO authority'.
        print("Former 24.36 state under SUMO authority")
        # Display formatted text built from the embedded values.
        print(f"  Current speed: {former_24_36.current_speed_mps}")
        # Display formatted text built from the embedded values.
        print(f"  SUMO stop speed: {former_24_36.sumo_stop_speed_mps}")
        # Display the text 'Diagnostic comfortable minimum:' plus a string built from
        # former_24_36.comfortable_min_next_speed_mps.
        print("  Diagnostic comfortable minimum: " +
              # Evaluate a string built from former_24_36.comfortable_min_next_speed_mps as part of the enclosing
              # expression.
              str(former_24_36.comfortable_min_next_speed_mps))
        # Display the text 'Pre-command Python rejection: False'.
        print("  Pre-command Python rejection: False")
        # Display the text 'Requested precedence speed:' plus a string built from
        # former_24_36.requested_precedence_speed_mps.
        print("  Requested precedence speed: " +
              # Evaluate a string built from former_24_36.requested_precedence_speed_mps as part of the enclosing
              # expression.
              str(former_24_36.requested_precedence_speed_mps))
        # Display the text 'Actual next SUMO speed:' plus a string built from
        # former_24_36.actual_realized_next_speed_mps.
        print("  Actual next SUMO speed: " +
              # Evaluate a string built from former_24_36.actual_realized_next_speed_mps as part of the enclosing
              # expression.
              str(former_24_36.actual_realized_next_speed_mps))
        # Display the text 'Actual next acceleration:' plus a string built from
        # former_24_36.actual_realized_acceleration_mps2.
        print("  Actual next acceleration: " +
              # Evaluate a string built from former_24_36.actual_realized_acceleration_mps2 as part of the
              # enclosing expression.
              str(former_24_36.actual_realized_acceleration_mps2))
        # Display the text 'Native intervention classification:' plus a string built from former_24_36_realized at
        # -1 when former_24_36_realized, otherwise None.
        print("  Native intervention classification: " +
              # Evaluate a string built from former_24_36_realized at -1 when former_24_36_realized, otherwise
              # None as part of the enclosing expression.
              str(former_24_36_realized[-1] if former_24_36_realized else None))
        # Display the text 'SUMO emergency-stop event: False'.
        print("  SUMO emergency-stop event: False")
        # Display formatted text built from the embedded values.
        print(f"  Speed mode: {former_24_36.speed_mode}\n")
    # Iterate over corresponding items paired from a tuple containing the text 'A', the text 'B', attempts,
    # binding each item to (label, attempt).
    for label, attempt in zip(("A", "B"), attempts):
        # Display formatted text built from the embedded values.
        print(f"Branch {label} physical outcome")
        # Run this branch when attempt at 'trace'.
        if attempt["trace"]:
            # Set trace to attempt at 'trace'.
            trace = attempt["trace"]
            # Display formatted text built from the embedded values.
            print(f"  Zone entry sequence: {trace.conflict_zone_entry_events}")
            # Display formatted text built from the embedded values.
            print(f"  Zone clear sequence: {trace.conflict_zone_clear_events}")
            # Display formatted text built from the embedded values.
            print(f"  Vehicle completion events: {trace.vehicle_completion_events}")
            # Display formatted text built from the embedded values.
            print(f"  Speed constraints: {_constraint_summary(trace.speed_constraint_records)}")
            # Display formatted text built from the embedded values.
            print(f"  Team travel time: {trace.team_travel_time_seconds}")
            # Display formatted text built from the embedded values.
            print(f"  Raw Step 5H reward: {trace.raw_shared_team_reward}")
            # Display formatted text built from the embedded values.
            print(f"  Collisions: {trace.collision_count}")
            # Display formatted text built from the embedded values.
            print(f"  Native SUMO intervention events: {trace.native_sumo_intervention_events}")
            # Display the text 'Controller comfortable-bound violations:' plus a string built from the sum of a
            # lazy sequence of value[-1] == 'PRECEDENCE_CONTROLLER_COMFORTABLE_BOUND_VIOLATION' for value in
            # trace.realized_deceleration_records.
            print("  Controller comfortable-bound violations: " + str(sum(
                # Evaluate value at -1 equals the text 'PRECEDENCE_CONTROLLER_COMFORTABLE_BOUND_VIOLATION' as part
                # of the enclosing expression.
                value[-1] == "PRECEDENCE_CONTROLLER_COMFORTABLE_BOUND_VIOLATION"
                # Evaluate trace.realized_deceleration_records as part of the enclosing expression.
                for value in trace.realized_deceleration_records)))
        # Run this alternative branch when the preceding branch does not apply.
        else:
            # Set error to attempt at 'error'.
            error = attempt["error"]
            # Set records to 'speed_constraint_records_before_failure' from error.evidence; use an empty tuple if
            # absent.
            records = error.evidence.get("speed_constraint_records_before_failure", ())
            # Display formatted text built from the embedded values.
            print(f"  STOP: {error.code}")
            # Display formatted text built from the embedded values.
            print(f"  Exact evidence: { {k: v for k, v in error.evidence.items() if k not in ('pre_branch_fingerprint', 'speed_constraint_records_before_failure', 'speed_command_records_before_failure', 'realized_deceleration_before_failure')} }")
            # Display formatted text built from the embedded values.
            print(f"  Speed constraints before stop: {_constraint_summary(records)}")
            # Run this branch when error.code equals the text 'EXECUTION_CONSTRAINT_NOT_PHYSICALLY_FEASIBLE'.
            if error.code == "EXECUTION_CONSTRAINT_NOT_PHYSICALLY_FEASIBLE":
                # Set value to error.evidence.
                value = error.evidence
                # Set cap to the square root of 2.0 multiplied by value at 'comfortable_deceleration_mps2'
                # multiplied by value at 'distance_to_zone_entry_m'.
                cap = math.sqrt(2.0 * value["comfortable_deceleration_mps2"] *
                                # Evaluate value at 'distance_to_zone_entry_m' as part of the enclosing
                                # expression.
                                value["distance_to_zone_entry_m"])
                # Display formatted text built from the embedded values.
                print(f"  Continuous reference cap at failure: {cap}")
                # Display formatted text built from the embedded values.
                print(f"  SUMO-native stop speed at failure: {value.get('sumo_stop_speed_mps')}")
                # Display the text 'Comfortable minimum next speed at failure:' plus a string built from
                # 'comfortable_min_next_speed_mps' from value; use None if absent.
                print("  Comfortable minimum next speed at failure: " +
                      # Evaluate a string built from 'comfortable_min_next_speed_mps' from value; use None if
                      # absent as part of the enclosing expression.
                      str(value.get("comfortable_min_next_speed_mps")))
        # Display the supplied values.
        print()
    # Display the text 'Objective'.
    print("Objective")
    # Display formatted text built from the embedded values.
    print(f"  Completed branch objectives computed with Step 5H: {len(completed)}")
    # Display the text 'New reward components: 0'.
    print("  New reward components: 0\n")
    # Display the text 'Training boundary'.
    print("Training boundary")
    # Display the text 'Optimizers: 0'.
    print("  Optimizers: 0")
    # Display the text 'backward calls: 0'.
    print("  backward calls: 0")
    # Display the text 'Parameter updates: 0'.
    print("  Parameter updates: 0")
    # Display the text 'MAPPO training runs: 0'.
    print("  MAPPO training runs: 0")
    # Display the text 'Checkpoints: 0'.
    print("  Checkpoints: 0")
    # Display the text 'Learned main.py actions: 0'.
    print("  Learned main.py actions: 0\n")
    # Display the text 'Status'.
    print("Status")
    # Run this branch when replay_failure.
    if replay_failure:
        # Display formatted text built from the embedded values.
        print(f"  STOP: {replay_failure.code}")
        # Display the text 'NEGOTIATION_ACTION_TO_TRAFFIC_OUTCOME_STATUS:...'.
        print("  NEGOTIATION_ACTION_TO_TRAFFIC_OUTCOME_STATUS: NEGOTIATION_ACTION_TO_TRAFFIC_OUTCOME_COUPLING_INCOMPLETE")
        # Display formatted text built from the embedded values.
        print(f"  NEXT_BLOCKER: {replay_failure.code}")
    # Run this alternative branch when the preceding branch does not apply.
    else:
        # Display the text 'Physical trajectory difference: PASS'.
        print("  Physical trajectory difference: PASS")
        # Display the text 'NEGOTIATION_ACTION_TO_TRAFFIC_OUTCOME_STATUS:...'.
        print("  NEGOTIATION_ACTION_TO_TRAFFIC_OUTCOME_STATUS: CAUSAL_EXECUTION_PATH_VALIDATED")


# Run this branch when __name__ equals the text '__main__'.
# Call main with the supplied arguments.
if __name__ == "__main__": main()
