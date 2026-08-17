"""Execute or resume the Step 5J.3C.2B evidence tranche."""

from negotiation_training.extended_learning_curve import (
    ExtendedMAPLearningCurveRunner)


def main():
    result = ExtendedMAPLearningCurveRunner().run()
    print("\nStep 5J.3C.2B Extended Multi-Update MAPPO Learning Curve\n")
    print("Structure")
    print(f"  Replications observed: {result['replications_observed']}")
    print("  Update intervals per replication: "
          f"{result['update_intervals_observed_per_replication']}")
    print(f"  Policy states per replication: {result['policy_states_per_replication']}")
    print(f"  TRAINING manifest collections: {result['training_manifest_collections']}")
    print(f"  TRAINING scenario executions: {result['training_scenario_executions']}")
    for replication in result["replications"]:
        index = replication["replication_index"]
        costs = [state["team_travel_time_seconds"]
                 for state in replication["policy_states"]]
        delta = replication["learning_curve_deltas"]
        print(f"\nReplication {index}")
        print(f"  C0 / C1 / C2: {costs[0]} / {costs[1]} / {costs[2]}")
        print(f"  Delta 0->1: {delta['delta_0_to_1']}")
        print(f"  Delta 1->2: {delta['delta_1_to_2']}")
        print(f"  Delta 0->2: {delta['delta_0_to_2']}")
        print(f"  GNN unchanged: {replication['gnn_unchanged']}")
    print("\nCross-replication descriptive statistics")
    for name, statistics in result["cross_replication_descriptive_statistics"].items():
        print(f"  {name}: mean={statistics['sample_mean']}, "
              f"variance={statistics['sample_variance_n_minus_1']}, "
              f"stdev={statistics['sample_standard_deviation']}")
    print("\nSafety")
    print(f"  Collisions: {result['safety_evidence']['collisions']}")
    print("  Blocked-zone violations: "
          f"{result['safety_evidence']['blocked_zone_violations']}")
    print("\nData boundary")
    print("  VALIDATION scenario executions: 0")
    print("  HELD_OUT scenario executions: 0")
    print("  Candidate comparisons: 0")
    print("\nStatus")
    print(f"  STEP_5J_3C_2B_STATUS = {result['status']}")
    print("  FINAL_REPLICATION_COUNT_SELECTED = False")
    print("  FINAL_TRAINING_BUDGET_SELECTED = False")
    print(f"  NEXT_READINESS = {result['next_readiness']}")


if __name__ == "__main__":
    main()
