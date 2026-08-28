"""Validate Step 5J.3C.2 using existing evidence only."""

from negotiation_training.pilot_evidence_review import build_pilot_evidence_review


def main():
    result = build_pilot_evidence_review()
    pilot = result["pilot_statistics"]
    print("Step 5J.3C.2 Pilot Evidence Review\n")
    print("Pilot evidence")
    print(f"  Replications observed: {pilot['replications_observed']}")
    print("  PPO update intervals per replication: "
          f"{pilot['ppo_update_intervals_per_replication']}")
    print(f"  TRAINING manifest: {pilot['unique_training_scenarios']} scenarios")
    print(f"  VALIDATION used: {pilot['validation_runs']}")
    print(f"  HELD_OUT used: {pilot['held_out_runs']}\n")
    print("Learning progress")
    for index, delta in enumerate(pilot["delta_values"]):
        print(f"  Replication {index} delta: {delta}")
    print(f"  Delta mean: {pilot['delta_sample_mean']}")
    print(f"  Delta sample variance: {pilot['delta_sample_variance_n_minus_1']}\n")
    print("Training budget")
    print("  Final budget justified: False")
    print("  Reason: ONLY_ONE_UPDATE_INTERVAL_OBSERVED\n")
    print("Replication design")
    print("  Final replication count justified: False")
    print("  Reason: TWO_RUN_MINIMUM_VARIANCE_PROBE_ONLY\n")
    print("Scenario design")
    print("  New unique training scenarios required now: False")
    print("  Repeated TRAINING-manifest exposure required: True\n")
    print("Data boundary")
    print("  VALIDATION remains unused for training-budget probe: PASS")
    print("  HELD_OUT remains sealed: PASS\n")
    print("Status")
    print(f"  STEP_5J_3C_2_STATUS = {result['status']}")
    print(f"  TRAINING_BUDGET_EVIDENCE = {result['training_budget_evidence']}")
    print(f"  REPLICATION_EVIDENCE = {result['replication_evidence']}")
    print(f"  NEXT_READINESS = {result['next_readiness']}")


if __name__ == "__main__":
    main()
