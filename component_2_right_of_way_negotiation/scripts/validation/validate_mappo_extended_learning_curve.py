"""Execute or resume the Step 5J.3C.2B evidence tranche."""

# Import ExtendedMAPLearningCurveRunner from negotiation_training.extended_learning_curve for the operations
# below.
from negotiation_training.extended_learning_curve import (
    ExtendedMAPLearningCurveRunner)


# Main using the inputs and processing steps below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def main():
    # Set result to the result of ExtendedMAPLearningCurveRunner().run().
    result = ExtendedMAPLearningCurveRunner().run()
    # Display the text 'Step 5J.3C.2B Extended Multi-Update MAPPO Learning Curve'.
    print("\nStep 5J.3C.2B Extended Multi-Update MAPPO Learning Curve\n")
    # Display the text 'Structure'.
    print("Structure")
    # Display formatted text built from the embedded values.
    print(f"  Replications observed: {result['replications_observed']}")
    # Display formatted text built from the embedded values.
    print("  Update intervals per replication: "
          # Evaluate {result['update_intervals_observed_per_replication']} as part of the enclosing expression.
          f"{result['update_intervals_observed_per_replication']}")
    # Display formatted text built from the embedded values.
    print(f"  Policy states per replication: {result['policy_states_per_replication']}")
    # Display formatted text built from the embedded values.
    print(f"  TRAINING manifest collections: {result['training_manifest_collections']}")
    # Display formatted text built from the embedded values.
    print(f"  TRAINING scenario executions: {result['training_scenario_executions']}")
    # Iterate over result at 'replications', binding each item to replication.
    for replication in result["replications"]:
        # Set index to replication at 'replication_index'.
        index = replication["replication_index"]
        # Set costs to a list of state at 'team_travel_time_seconds' for state in replication at 'policy_states'.
        costs = [state["team_travel_time_seconds"]
                 # Evaluate replication at 'policy_states' as part of the enclosing expression.
                 for state in replication["policy_states"]]
        # Set delta to replication at 'learning_curve_deltas'.
        delta = replication["learning_curve_deltas"]
        # Display formatted text built from the embedded values.
        print(f"\nReplication {index}")
        # Display formatted text built from the embedded values.
        print(f"  C0 / C1 / C2: {costs[0]} / {costs[1]} / {costs[2]}")
        # Display formatted text built from the embedded values.
        print(f"  Delta 0->1: {delta['delta_0_to_1']}")
        # Display formatted text built from the embedded values.
        print(f"  Delta 1->2: {delta['delta_1_to_2']}")
        # Display formatted text built from the embedded values.
        print(f"  Delta 0->2: {delta['delta_0_to_2']}")
        # Display formatted text built from the embedded values.
        print(f"  GNN unchanged: {replication['gnn_unchanged']}")
    # Display the text 'Cross-replication descriptive statistics'.
    print("\nCross-replication descriptive statistics")
    # Iterate over key/value pairs from result['cross_replication_descriptive_statistics'], binding each item to
    # (name, statistics).
    for name, statistics in result["cross_replication_descriptive_statistics"].items():
        # Display formatted text built from the embedded values.
        print(f"  {name}: mean={statistics['sample_mean']}, "
              # Evaluate {statistics['sample_variance_n_minus_1']} as part of the enclosing expression.
              f"variance={statistics['sample_variance_n_minus_1']}, "
              # Evaluate {statistics['sample_standard_deviation']} as part of the enclosing expression.
              f"stdev={statistics['sample_standard_deviation']}")
    # Display the text 'Safety'.
    print("\nSafety")
    # Display formatted text built from the embedded values.
    print(f"  Collisions: {result['safety_evidence']['collisions']}")
    # Display formatted text built from the embedded values.
    print("  Blocked-zone violations: "
          # Evaluate {result['safety_evidence']['blocked_zone_violations']} as part of the enclosing expression.
          f"{result['safety_evidence']['blocked_zone_violations']}")
    # Display the text 'Data boundary'.
    print("\nData boundary")
    # Display the text 'VALIDATION scenario executions: 0'.
    print("  VALIDATION scenario executions: 0")
    # Display the text 'HELD_OUT scenario executions: 0'.
    print("  HELD_OUT scenario executions: 0")
    # Display the text 'Candidate comparisons: 0'.
    print("  Candidate comparisons: 0")
    # Display the text 'Status'.
    print("\nStatus")
    # Display formatted text built from the embedded values.
    print(f"  STEP_5J_3C_2B_STATUS = {result['status']}")
    # Display the text 'FINAL_REPLICATION_COUNT_SELECTED = False'.
    print("  FINAL_REPLICATION_COUNT_SELECTED = False")
    # Display the text 'FINAL_TRAINING_BUDGET_SELECTED = False'.
    print("  FINAL_TRAINING_BUDGET_SELECTED = False")
    # Display formatted text built from the embedded values.
    print(f"  NEXT_READINESS = {result['next_readiness']}")


# Run this branch when __name__ equals the text '__main__'.
if __name__ == "__main__":
    # Call main with the supplied arguments.
    main()
