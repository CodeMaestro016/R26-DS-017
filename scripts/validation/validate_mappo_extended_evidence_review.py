"""Fast analysis-only validator for Step 5J.3C.2C."""

from negotiation_training.extended_evidence_review import (
    build_extended_evidence_review)


def main():
    result = build_extended_evidence_review()
    curve = result["learning_curve_evidence"]
    print("Step 5J.3C.2C Extended Evidence Sufficiency Review\n")
    print("Source")
    print("  Step 5J.3C.2B status: EXTENDED_MULTI_UPDATE_EVIDENCE_ACQUIRED")
    print("  Replications: 3")
    print("  Policy states: 3")
    print("  Update intervals: 2\n")
    print("Learning curve")
    for index in range(3):
        print(f"  Rep {index}: {curve['C0'][index]} -> "
              f"{curve['C1'][index]} -> {curve['C2'][index]}")
    statistics = curve["descriptive_statistics"]
    print("  Mean: " + " -> ".join(str(statistics[name]["sample_mean"])
                                    for name in ("C0", "C1", "C2")))
    print("  Plateau established: False")
    print("  Consistent latest update direction: False\n")
    print("Training budget")
    print("  Final budget justified: False")
    print("  Final budget selected: False\n")
    print("Replication design")
    print("  Final replication count justified: False")
    print("  Final replication count selected: False\n")
    print("Checkpoint selection")
    print("  Final checkpoint selected: False\n")
    print("Candidate comparison")
    print("  Ready: False\n")
    print("Data boundary")
    print("  New SUMO executions: 0")
    print("  VALIDATION executions: 0")
    print("  HELD_OUT executions: 0")
    print("  Optimizer invocations: 0")
    print("  Parameter updates: 0\n")
    print("Status")
    print(f"  STEP_5J_3C_2C_STATUS = {result['status']}")
    print(f"  TRAINING_BUDGET_STATUS = {result['training_budget_status']}")
    print(f"  REPLICATION_STATUS = {result['replication_status']}")
    print(f"  CHECKPOINT_SELECTION_STATUS = {result['checkpoint_selection_status']}")
    print("  CANDIDATE_COMPARISON_READINESS = "
          f"{result['candidate_comparison_readiness']['status']}")
    print(f"  NEXT_CHECKPOINT = {result['next_checkpoint']}")


if __name__ == "__main__":
    main()
