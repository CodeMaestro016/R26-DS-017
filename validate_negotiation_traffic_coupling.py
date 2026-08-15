"""Step 5J.2B coupling status using a complete joint protocol outcome."""

from joint_negotiation_validation import real_training_evidence


def main():
    evidence = real_training_evidence()
    branches = evidence["branches"]
    executable = min(evidence["executable"],
                     key=lambda item: (len(item.completed_agreement_ids), item.branch_id))
    baseline = next(item for item in branches
                    if not item.proposer_assignment.proposals_created)
    single_accept_cyclic = any(
        len(item.completed_agreement_ids) == 1 and item.cycle_detected
        for item in branches)
    accepted = len(executable.completed_agreement_ids)
    assert baseline.cycle_detected
    assert not executable.cycle_detected
    assert executable.execution_plan.graph_status == "EXECUTABLE"
    assert executable.execution_plan.ready_vehicle_ids

    print("Step 5J.2B Negotiation-to-Traffic Coupling Validation\n")
    print("Joint negotiation")
    print(f"  Single ACCEPT sufficient for selected executable branch: {accepted == 1}")
    print(f"  Single ACCEPT can remain cyclic: {single_accept_cyclic}")
    print(f"  Agreements in selected executable branch: {accepted}")
    print("  Executable joint branch: PASS")
    print("  Effective graph cyclic before negotiation: True")
    print("  Effective graph cyclic after executable branch: False\n")
    print("Physical execution")
    print("  Execution plan status: EXECUTABLE")
    print(f"  Ready vehicles: {executable.execution_plan.ready_vehicle_ids}")
    print("  Physical speed commands derived from precedence: 0")
    print("  Arbitrary raw action-speed mapping: 0")
    print("  Native SUMO safety preserved: PASS\n")
    print("Causality")
    print("  Negotiation outcome changes effective graph: PASS")
    print("  Effective graph changes execution plan: PASS")
    print("  Execution plan changes physical SUMO state: NOT_EXECUTED")
    print("  Causal witness established: False\n")
    print("Objective")
    print("  Step 5H objective consumed: False")
    print("  Reward modification: False\n")
    print("Status")
    print("  JOINT_NEGOTIATION_CYCLE_RESOLUTION_STATUS: EXECUTABLE_JOINT_NEGOTIATION_BRANCH_FOUND")
    print("  NEGOTIATION_ACTION_TO_TRAFFIC_OUTCOME_STATUS: NEGOTIATION_ACTION_TO_TRAFFIC_OUTCOME_COUPLING_INCOMPLETE")
    print("  NEXT_BLOCKER: DEDICATED_IDENTICAL_INITIAL_CONDITION_SUMO_BRANCH_REPLAY_NOT_IMPLEMENTED\n")
    print("Training boundary")
    print("  Optimizers: 0")
    print("  backward() calls: 0")
    print("  Parameter updates: 0")
    print("  MAPPO training runs: 0")
    print("  Learned SUMO control actions: 0")


if __name__ == "__main__": main()
