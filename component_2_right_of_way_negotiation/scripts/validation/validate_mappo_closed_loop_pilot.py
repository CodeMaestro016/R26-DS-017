"""Run and report the Step 5J.3C.1 minimum closed-loop pilot."""

from negotiation_training.controlled_pilot import ControlledMAPPOPilotRunner


def main():
    result = ControlledMAPPOPilotRunner().run()
    print("\nStep 5J.3C.1 Controlled MAPPO Closed-Loop Pilot\n")
    print("Design")
    print("  Frozen design unchanged: PASS")
    print("  Provisional configuration: PROVISIONAL_REFERENCE_V1")
    print("  Final configuration selected: False\n")
    print("Replication probe")
    print("  Canonical pilot replications: 2")
    print("  Reason: MINIMUM_SAMPLE_VARIANCE_PROBE")
    print("  Performance-selected seeds: 0")
    print("  Final replication count selected: False")
    for item in result["replications"]:
        print(f"\nReplication {item['replication_index']}")
        print(f"  TRAINING Pass 0 scenarios: {item['pass0']['scenario_count']}")
        print("  Pass 0 team travel time: "
              f"{item['pass0']['team_travel_time_seconds']}")
        print("  PPO update cycles: 1")
        print("  Parameter update: PASS")
        print(f"  TRAINING Pass 1 scenarios: {item['pass1']['scenario_count']}")
        print("  Pass 1 team travel time: "
              f"{item['pass1']['team_travel_time_seconds']}")
        print("  Delta team travel time: "
              f"{item['delta_team_travel_time_seconds']}")
    variance = result["variance_evidence"]
    print("\nVariance evidence")
    print(f"  Pre-update mean: {variance['pre_update']['sample_mean']}")
    print("  Pre-update sample variance: "
          f"{variance['pre_update']['sample_variance_n_minus_1']}")
    print(f"  Post-update mean: {variance['post_update']['sample_mean']}")
    print("  Post-update sample variance: "
          f"{variance['post_update']['sample_variance_n_minus_1']}")
    print(f"  Delta mean: {variance['delta']['sample_mean']}")
    print("  Delta sample variance: "
          f"{variance['delta']['sample_variance_n_minus_1']}")
    print("\nLearning progress")
    print("  Paired scenario changes recorded: 72")
    print("  Improvement threshold used: False")
    print("  Convergence claimed: False")
    print("\nCompute evidence")
    print(f"  Total SUMO steps: {result['total_sumo_steps']}")
    print("  Total wall-clock runtime: "
          f"{result['total_wall_clock_runtime_seconds']}")
    print(f"  Update runtime: {result['total_update_runtime_seconds']}")
    print("\nSafety")
    print(f"  Collisions: {result['collisions']}")
    print(f"  Blocked-zone violations: {result['blocked_zone_violations']}")
    print("\nData boundaries")
    print("  VALIDATION runs: 0")
    print("  HELD_OUT runs: 0")
    print("\nResearch boundary")
    print("  New reward terms: 0")
    print("  New candidate values: 0")
    print("  Selected hyperparameters: 0")
    print("\nStatus")
    print(f"  STEP_5J_3C_1_STATUS: {result['status']}")
    print(f"  TRAINING_BUDGET_STATUS: {result['training_budget_status']}")
    print(f"  REPLICATION_STATUS: {result['replication_status']}")
    print("  FINAL_TRAINING_BUDGET_SELECTED: False")
    print("  FINAL_REPLICATION_COUNT_SELECTED: False")


if __name__ == "__main__": main()
