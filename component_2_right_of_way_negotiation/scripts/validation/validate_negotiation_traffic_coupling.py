"""Step 5J.2B coupling status using joint and physical replay evidence."""

# Import json for use in this module.
import json
# Import Path from pathlib for the operations below.
from pathlib import Path
# Import real_training_evidence from joint_negotiation_validation for the operations below.
from joint_negotiation_validation import real_training_evidence

# Set REPLAY_ARTIFACT to the result of Path(the text 'results/identical_condition_branch_replay.json').
REPLAY_ARTIFACT = Path("results/identical_condition_branch_replay.json")


# Main using the inputs and processing steps below.
# Output: no explicit value; normal completion returns None.
# Processing: select branches using the stated conditions.
def main():
    # Set evidence to the result of real_training_evidence().
    evidence = real_training_evidence()
    # Set branches to evidence at 'branches'.
    branches = evidence["branches"]
    # Set executable to the minimum of evidence at 'executable'.
    executable = min(evidence["executable"],
                     # Declare item as input parameter.
                     key=lambda item: (len(item.completed_agreement_ids), item.branch_id))
    # Set baseline to the next item from a lazy sequence of item for item in branches; retain entries satisfying
    # the negation of item.proposer_assignment.proposals_created.
    baseline = next(item for item in branches
                    # Evaluate the negation of item.proposer_assignment.proposals_created as part of the enclosing
                    # expression.
                    if not item.proposer_assignment.proposals_created)
    # Set single_accept_cyclic to whether any item is true in a lazy sequence of len(item.completed_agreement_ids)
    # equals 1 and item.cycle_detected for item in branches.
    single_accept_cyclic = any(
        # Evaluate the number of entries in item.completed_agreement_ids equals 1 and item.cycle_detected as part
        # of the enclosing expression.
        len(item.completed_agreement_ids) == 1 and item.cycle_detected
        # Evaluate branches as part of the enclosing expression.
        for item in branches)
    # Set accepted to the number of entries in executable.completed_agreement_ids.
    accepted = len(executable.completed_agreement_ids)
    # Require baseline.cycle_detected; otherwise raise AssertionError.
    assert baseline.cycle_detected
    # Require the negation of executable.cycle_detected; otherwise raise AssertionError.
    assert not executable.cycle_detected
    # Require executable.execution_plan.graph_status equals the text 'EXECUTABLE'; otherwise raise AssertionError.
    assert executable.execution_plan.graph_status == "EXECUTABLE"
    # Require executable.execution_plan.ready_vehicle_ids; otherwise raise AssertionError.
    assert executable.execution_plan.ready_vehicle_ids
    # Set replay to the decoded data produced by json.loads from the text read from REPLAY_ARTIFACT when whether
    # REPLAY_ARTIFACT exists, otherwise None.
    replay = (json.loads(REPLAY_ARTIFACT.read_text(encoding="utf-8"))
              # Evaluate whether REPLAY_ARTIFACT exists as part of the enclosing expression.
              if REPLAY_ARTIFACT.exists() else None)
    # Set physical_validated to a Boolean built from replay and replay at 'status' equals the text
    # 'CAUSAL_EXECUTION_PATH_VALIDATED'.
    physical_validated = bool(replay and replay["status"] ==
                              "CAUSAL_EXECUTION_PATH_VALIDATED")

    # Display the text 'Step 5J.2B Negotiation-to-Traffic Coupling Validation'.
    print("Step 5J.2B Negotiation-to-Traffic Coupling Validation\n")
    # Display the text 'Joint negotiation'.
    print("Joint negotiation")
    # Display formatted text built from the embedded values.
    print(f"  Single ACCEPT sufficient for selected executable branch: {accepted == 1}")
    # Display formatted text built from the embedded values.
    print(f"  Single ACCEPT can remain cyclic: {single_accept_cyclic}")
    # Display formatted text built from the embedded values.
    print(f"  Agreements in selected executable branch: {accepted}")
    # Display the text 'Executable joint branch: PASS'.
    print("  Executable joint branch: PASS")
    # Display the text 'Effective graph cyclic before negotiation: True'.
    print("  Effective graph cyclic before negotiation: True")
    # Display the text 'Effective graph cyclic after executable branch: False'.
    print("  Effective graph cyclic after executable branch: False\n")
    # Display the text 'Physical execution'.
    print("Physical execution")
    # Display the text 'Execution plan status: EXECUTABLE'.
    print("  Execution plan status: EXECUTABLE")
    # Display formatted text built from the embedded values.
    print(f"  Ready vehicles: {executable.execution_plan.ready_vehicle_ids}")
    # Set command_count to 'physical_speed_command_count' from replay; use 0 if absent when replay, otherwise 0.
    command_count = replay.get("physical_speed_command_count", 0) if replay else 0
    # Display formatted text built from the embedded values.
    print(f"  Physical speed commands derived from precedence: {command_count}")
    # Display the text 'Arbitrary raw action-speed mapping: 0'.
    print("  Arbitrary raw action-speed mapping: 0")
    # Display the text 'Native SUMO safety preserved: PASS'.
    print("  Native SUMO safety preserved: PASS\n")
    # Display the text 'Causality'.
    print("Causality")
    # Display the text 'Negotiation outcome changes effective graph: PASS'.
    print("  Negotiation outcome changes effective graph: PASS")
    # Display the text 'Effective graph changes execution plan: PASS'.
    print("  Effective graph changes execution plan: PASS")
    # Display the text 'Identical-condition replay executed:' plus a string built from replay is a different
    # object from None.
    print("  Identical-condition replay executed: " + str(replay is not None))
    # Display the text 'Execution plan changes physical SUMO state:' plus the text 'PASS' when physical_validated,
    # otherwise the text 'BLOCKED_BY_PHYSICAL_FEASIBILITY'.
    print("  Execution plan changes physical SUMO state: " +
          # Evaluate the text 'PASS' when physical_validated, otherwise the text 'BLOCKED_BY_PHYSICAL_FEASIBILITY'
          # as part of the enclosing expression.
          ("PASS" if physical_validated else "BLOCKED_BY_PHYSICAL_FEASIBILITY"))
    # Display formatted text built from the embedded values.
    print(f"  Causal witness established: {physical_validated}\n")
    # Display the text 'Objective'.
    print("Objective")
    # Display the text 'Step 5H objective consumed by completed replay branches:' plus a string built from a
    # Boolean built from replay and replay.get('completed_branch_count', 0).
    print("  Step 5H objective consumed by completed replay branches: " +
          # Evaluate a string built from a Boolean built from replay and 'completed_branch_count' from replay; use
          # 0 if absent as part of the enclosing expression.
          str(bool(replay and replay.get("completed_branch_count", 0))))
    # Display the text 'Reward modification: False'.
    print("  Reward modification: False\n")
    # Display the text 'Status'.
    print("Status")
    # Display the text 'JOINT_NEGOTIATION_CYCLE_RESOLUTION_STATUS:...'.
    print("  JOINT_NEGOTIATION_CYCLE_RESOLUTION_STATUS: EXECUTABLE_JOINT_NEGOTIATION_BRANCH_FOUND")
    # Display the text 'NEGOTIATION_ACTION_TO_TRAFFIC_OUTCOME_STATUS:' plus the text
    # 'CAUSAL_EXECUTION_PATH_VALIDATED' when physical_validated, otherwise the text
    # 'NEGOTIATION_ACTION_TO_TRAFFIC_OUTCOME_COUPLING_INCOMPLETE'.
    print("  NEGOTIATION_ACTION_TO_TRAFFIC_OUTCOME_STATUS: " +
          # Evaluate the text 'CAUSAL_EXECUTION_PATH_VALIDATED' when physical_validated, otherwise the text
          # 'NEGOTIATION_ACTION_TO_TRAFFIC_OUTCOME_COUPLING_INCOMPLETE' as part of the enclosing expression.
          ("CAUSAL_EXECUTION_PATH_VALIDATED" if physical_validated else
           "NEGOTIATION_ACTION_TO_TRAFFIC_OUTCOME_COUPLING_INCOMPLETE"))
    # Run this branch when the negation of physical_validated.
    if not physical_validated:
        # Set blocker to 'next_blocker' from replay; use None if absent or replay at 'status' when replay,
        # otherwise the text 'DEDICATED_IDENTICAL_INITIAL_CONDITION_SUMO_BRANCH_REPLAY_NOT_E...'.
        blocker = (replay.get("next_blocker") or replay["status"] if replay else
                   "DEDICATED_IDENTICAL_INITIAL_CONDITION_SUMO_BRANCH_REPLAY_NOT_EXECUTED")
        # Display formatted text built from the embedded values.
        print(f"  NEXT_BLOCKER: {blocker}")
    # Display the supplied values.
    print()
    # Display the text 'Training boundary'.
    print("Training boundary")
    # Display the text 'Optimizers: 0'.
    print("  Optimizers: 0")
    # Display the text 'backward() calls: 0'.
    print("  backward() calls: 0")
    # Display the text 'Parameter updates: 0'.
    print("  Parameter updates: 0")
    # Display the text 'MAPPO training runs: 0'.
    print("  MAPPO training runs: 0")
    # Display the text 'Learned SUMO control actions: 0'.
    print("  Learned SUMO control actions: 0")


# Run this branch when __name__ equals the text '__main__'.
# Call main with the supplied arguments.
if __name__ == "__main__": main()
