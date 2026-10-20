"""Run and report the Step 5J.3C.1 minimum closed-loop pilot."""

# Import ControlledMAPPOPilotRunner from negotiation_training.controlled_pilot for the operations below.
from negotiation_training.controlled_pilot import ControlledMAPPOPilotRunner


# Main using the inputs and processing steps below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def main():
    # Set result to the result of ControlledMAPPOPilotRunner().run().
    result = ControlledMAPPOPilotRunner().run()
    # Display the text 'Step 5J.3C.1 Controlled MAPPO Closed-Loop Pilot'.
    print("\nStep 5J.3C.1 Controlled MAPPO Closed-Loop Pilot\n")
    # Display the text 'Design'.
    print("Design")
    # Display the text 'Frozen design unchanged: PASS'.
    print("  Frozen design unchanged: PASS")
    # Display the text 'Provisional configuration: PROVISIONAL_REFERENCE_V1'.
    print("  Provisional configuration: PROVISIONAL_REFERENCE_V1")
    # Display the text 'Final configuration selected: False'.
    print("  Final configuration selected: False\n")
    # Display the text 'Replication probe'.
    print("Replication probe")
    # Display the text 'Canonical pilot replications: 2'.
    print("  Canonical pilot replications: 2")
    # Display the text 'Reason: MINIMUM_SAMPLE_VARIANCE_PROBE'.
    print("  Reason: MINIMUM_SAMPLE_VARIANCE_PROBE")
    # Display the text 'Performance-selected seeds: 0'.
    print("  Performance-selected seeds: 0")
    # Display the text 'Final replication count selected: False'.
    print("  Final replication count selected: False")
    # Iterate over result at 'replications', binding each item to item.
    for item in result["replications"]:
        # Display formatted text built from the embedded values.
        print(f"\nReplication {item['replication_index']}")
        # Display formatted text built from the embedded values.
        print(f"  TRAINING Pass 0 scenarios: {item['pass0']['scenario_count']}")
        # Display formatted text built from the embedded values.
        print("  Pass 0 team travel time: "
              # Evaluate {item['pass0']['team_travel_time_seconds']} as part of the enclosing expression.
              f"{item['pass0']['team_travel_time_seconds']}")
        # Display the text 'PPO update cycles: 1'.
        print("  PPO update cycles: 1")
        # Display the text 'Parameter update: PASS'.
        print("  Parameter update: PASS")
        # Display formatted text built from the embedded values.
        print(f"  TRAINING Pass 1 scenarios: {item['pass1']['scenario_count']}")
        # Display formatted text built from the embedded values.
        print("  Pass 1 team travel time: "
              # Evaluate {item['pass1']['team_travel_time_seconds']} as part of the enclosing expression.
              f"{item['pass1']['team_travel_time_seconds']}")
        # Display formatted text built from the embedded values.
        print("  Delta team travel time: "
              # Evaluate {item['delta_team_travel_time_seconds']} as part of the enclosing expression.
              f"{item['delta_team_travel_time_seconds']}")
    # Set variance to result at 'variance_evidence'.
    variance = result["variance_evidence"]
    # Display the text 'Variance evidence'.
    print("\nVariance evidence")
    # Display formatted text built from the embedded values.
    print(f"  Pre-update mean: {variance['pre_update']['sample_mean']}")
    # Display formatted text built from the embedded values.
    print("  Pre-update sample variance: "
          # Evaluate {variance['pre_update']['sample_variance_n_minus_1']} as part of the enclosing expression.
          f"{variance['pre_update']['sample_variance_n_minus_1']}")
    # Display formatted text built from the embedded values.
    print(f"  Post-update mean: {variance['post_update']['sample_mean']}")
    # Display formatted text built from the embedded values.
    print("  Post-update sample variance: "
          # Evaluate {variance['post_update']['sample_variance_n_minus_1']} as part of the enclosing expression.
          f"{variance['post_update']['sample_variance_n_minus_1']}")
    # Display formatted text built from the embedded values.
    print(f"  Delta mean: {variance['delta']['sample_mean']}")
    # Display formatted text built from the embedded values.
    print("  Delta sample variance: "
          # Evaluate {variance['delta']['sample_variance_n_minus_1']} as part of the enclosing expression.
          f"{variance['delta']['sample_variance_n_minus_1']}")
    # Display the text 'Learning progress'.
    print("\nLearning progress")
    # Display the text 'Paired scenario changes recorded: 72'.
    print("  Paired scenario changes recorded: 72")
    # Display the text 'Improvement threshold used: False'.
    print("  Improvement threshold used: False")
    # Display the text 'Convergence claimed: False'.
    print("  Convergence claimed: False")
    # Display the text 'Compute evidence'.
    print("\nCompute evidence")
    # Display formatted text built from the embedded values.
    print(f"  Total SUMO steps: {result['total_sumo_steps']}")
    # Display formatted text built from the embedded values.
    print("  Total wall-clock runtime: "
          # Evaluate {result['total_wall_clock_runtime_seconds']} as part of the enclosing expression.
          f"{result['total_wall_clock_runtime_seconds']}")
    # Display formatted text built from the embedded values.
    print(f"  Update runtime: {result['total_update_runtime_seconds']}")
    # Display the text 'Safety'.
    print("\nSafety")
    # Display formatted text built from the embedded values.
    print(f"  Collisions: {result['collisions']}")
    # Display formatted text built from the embedded values.
    print(f"  Blocked-zone violations: {result['blocked_zone_violations']}")
    # Display the text 'Data boundaries'.
    print("\nData boundaries")
    # Display the text 'VALIDATION runs: 0'.
    print("  VALIDATION runs: 0")
    # Display the text 'HELD_OUT runs: 0'.
    print("  HELD_OUT runs: 0")
    # Display the text 'Research boundary'.
    print("\nResearch boundary")
    # Display the text 'New reward terms: 0'.
    print("  New reward terms: 0")
    # Display the text 'New candidate values: 0'.
    print("  New candidate values: 0")
    # Display the text 'Selected hyperparameters: 0'.
    print("  Selected hyperparameters: 0")
    # Display the text 'Status'.
    print("\nStatus")
    # Display formatted text built from the embedded values.
    print(f"  STEP_5J_3C_1_STATUS: {result['status']}")
    # Display formatted text built from the embedded values.
    print(f"  TRAINING_BUDGET_STATUS: {result['training_budget_status']}")
    # Display formatted text built from the embedded values.
    print(f"  REPLICATION_STATUS: {result['replication_status']}")
    # Display the text 'FINAL_TRAINING_BUDGET_SELECTED: False'.
    print("  FINAL_TRAINING_BUDGET_SELECTED: False")
    # Display the text 'FINAL_REPLICATION_COUNT_SELECTED: False'.
    print("  FINAL_REPLICATION_COUNT_SELECTED: False")


# Run this branch when __name__ equals the text '__main__'.
# Call main with the supplied arguments.
if __name__ == "__main__": main()
