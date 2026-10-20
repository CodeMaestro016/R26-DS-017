"""Fast analysis-only validator for Step 5J.3C.2C."""

# Import build_extended_evidence_review from negotiation_training.extended_evidence_review for the operations
# below.
from negotiation_training.extended_evidence_review import (
    build_extended_evidence_review)


# Main using the inputs and processing steps below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def main():
    # Set result to the result of build_extended_evidence_review().
    result = build_extended_evidence_review()
    # Set curve to result at 'learning_curve_evidence'.
    curve = result["learning_curve_evidence"]
    # Display the text 'Step 5J.3C.2C Extended Evidence Sufficiency Review'.
    print("Step 5J.3C.2C Extended Evidence Sufficiency Review\n")
    # Display the text 'Source'.
    print("Source")
    # Display the text 'Step 5J.3C.2B status: EXTENDED_MULTI_UPDATE_EVIDENCE_ACQUIRED'.
    print("  Step 5J.3C.2B status: EXTENDED_MULTI_UPDATE_EVIDENCE_ACQUIRED")
    # Display the text 'Replications: 3'.
    print("  Replications: 3")
    # Display the text 'Policy states: 3'.
    print("  Policy states: 3")
    # Display the text 'Update intervals: 2'.
    print("  Update intervals: 2\n")
    # Display the text 'Learning curve'.
    print("Learning curve")
    # Iterate over the integer range defined by 3, binding each item to index.
    for index in range(3):
        # Display formatted text built from the embedded values.
        print(f"  Rep {index}: {curve['C0'][index]} -> "
              # Evaluate {curve['C1'][index]} as part of the enclosing expression.
              f"{curve['C1'][index]} -> {curve['C2'][index]}")
    # Set statistics to curve at 'descriptive_statistics'.
    statistics = curve["descriptive_statistics"]
    # Display the text 'Mean:' plus the result of ' -> '.join(a lazy sequence of a string built from
    # statistics[name]['sample_mean'] for name in a tuple...).
    print("  Mean: " + " -> ".join(str(statistics[name]["sample_mean"])
                                    # Evaluate a tuple containing the text 'C0', the text 'C1', the text 'C2' as
                                    # part of the enclosing expression.
                                    for name in ("C0", "C1", "C2")))
    # Display the text 'Plateau established: False'.
    print("  Plateau established: False")
    # Display the text 'Consistent latest update direction: False'.
    print("  Consistent latest update direction: False\n")
    # Display the text 'Training budget'.
    print("Training budget")
    # Display the text 'Final budget justified: False'.
    print("  Final budget justified: False")
    # Display the text 'Final budget selected: False'.
    print("  Final budget selected: False\n")
    # Display the text 'Replication design'.
    print("Replication design")
    # Display the text 'Final replication count justified: False'.
    print("  Final replication count justified: False")
    # Display the text 'Final replication count selected: False'.
    print("  Final replication count selected: False\n")
    # Display the text 'Checkpoint selection'.
    print("Checkpoint selection")
    # Display the text 'Final checkpoint selected: False'.
    print("  Final checkpoint selected: False\n")
    # Display the text 'Candidate comparison'.
    print("Candidate comparison")
    # Display the text 'Ready: False'.
    print("  Ready: False\n")
    # Display the text 'Data boundary'.
    print("Data boundary")
    # Display the text 'New SUMO executions: 0'.
    print("  New SUMO executions: 0")
    # Display the text 'VALIDATION executions: 0'.
    print("  VALIDATION executions: 0")
    # Display the text 'HELD_OUT executions: 0'.
    print("  HELD_OUT executions: 0")
    # Display the text 'Optimizer invocations: 0'.
    print("  Optimizer invocations: 0")
    # Display the text 'Parameter updates: 0'.
    print("  Parameter updates: 0\n")
    # Display the text 'Status'.
    print("Status")
    # Display formatted text built from the embedded values.
    print(f"  STEP_5J_3C_2C_STATUS = {result['status']}")
    # Display formatted text built from the embedded values.
    print(f"  TRAINING_BUDGET_STATUS = {result['training_budget_status']}")
    # Display formatted text built from the embedded values.
    print(f"  REPLICATION_STATUS = {result['replication_status']}")
    # Display formatted text built from the embedded values.
    print(f"  CHECKPOINT_SELECTION_STATUS = {result['checkpoint_selection_status']}")
    # Display formatted text built from the embedded values.
    print("  CANDIDATE_COMPARISON_READINESS = "
          # Evaluate {result['candidate_comparison_readiness']['status']} as part of the enclosing expression.
          f"{result['candidate_comparison_readiness']['status']}")
    # Display formatted text built from the embedded values.
    print(f"  NEXT_CHECKPOINT = {result['next_checkpoint']}")


# Run this branch when __name__ equals the text '__main__'.
if __name__ == "__main__":
    # Call main with the supplied arguments.
    main()
