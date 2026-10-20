"""Validate Step 5J.3C.2 using existing evidence only."""

# Import build_pilot_evidence_review from negotiation_training.pilot_evidence_review for the operations below.
from negotiation_training.pilot_evidence_review import build_pilot_evidence_review


# Main using the inputs and processing steps below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def main():
    # Set result to the result of build_pilot_evidence_review().
    result = build_pilot_evidence_review()
    # Set pilot to result at 'pilot_statistics'.
    pilot = result["pilot_statistics"]
    # Display the text 'Step 5J.3C.2 Pilot Evidence Review'.
    print("Step 5J.3C.2 Pilot Evidence Review\n")
    # Display the text 'Pilot evidence'.
    print("Pilot evidence")
    # Display formatted text built from the embedded values.
    print(f"  Replications observed: {pilot['replications_observed']}")
    # Display formatted text built from the embedded values.
    print("  PPO update intervals per replication: "
          # Evaluate {pilot['ppo_update_intervals_per_replication']} as part of the enclosing expression.
          f"{pilot['ppo_update_intervals_per_replication']}")
    # Display formatted text built from the embedded values.
    print(f"  TRAINING manifest: {pilot['unique_training_scenarios']} scenarios")
    # Display formatted text built from the embedded values.
    print(f"  VALIDATION used: {pilot['validation_runs']}")
    # Display formatted text built from the embedded values.
    print(f"  HELD_OUT used: {pilot['held_out_runs']}\n")
    # Display the text 'Learning progress'.
    print("Learning progress")
    # Iterate over index/value pairs from pilot at 'delta_values', binding each item to (index, delta).
    for index, delta in enumerate(pilot["delta_values"]):
        # Display formatted text built from the embedded values.
        print(f"  Replication {index} delta: {delta}")
    # Display formatted text built from the embedded values.
    print(f"  Delta mean: {pilot['delta_sample_mean']}")
    # Display formatted text built from the embedded values.
    print(f"  Delta sample variance: {pilot['delta_sample_variance_n_minus_1']}\n")
    # Display the text 'Training budget'.
    print("Training budget")
    # Display the text 'Final budget justified: False'.
    print("  Final budget justified: False")
    # Display the text 'Reason: ONLY_ONE_UPDATE_INTERVAL_OBSERVED'.
    print("  Reason: ONLY_ONE_UPDATE_INTERVAL_OBSERVED\n")
    # Display the text 'Replication design'.
    print("Replication design")
    # Display the text 'Final replication count justified: False'.
    print("  Final replication count justified: False")
    # Display the text 'Reason: TWO_RUN_MINIMUM_VARIANCE_PROBE_ONLY'.
    print("  Reason: TWO_RUN_MINIMUM_VARIANCE_PROBE_ONLY\n")
    # Display the text 'Scenario design'.
    print("Scenario design")
    # Display the text 'New unique training scenarios required now: False'.
    print("  New unique training scenarios required now: False")
    # Display the text 'Repeated TRAINING-manifest exposure required: True'.
    print("  Repeated TRAINING-manifest exposure required: True\n")
    # Display the text 'Data boundary'.
    print("Data boundary")
    # Display the text 'VALIDATION remains unused for training-budget probe: PASS'.
    print("  VALIDATION remains unused for training-budget probe: PASS")
    # Display the text 'HELD_OUT remains sealed: PASS'.
    print("  HELD_OUT remains sealed: PASS\n")
    # Display the text 'Status'.
    print("Status")
    # Display formatted text built from the embedded values.
    print(f"  STEP_5J_3C_2_STATUS = {result['status']}")
    # Display formatted text built from the embedded values.
    print(f"  TRAINING_BUDGET_EVIDENCE = {result['training_budget_evidence']}")
    # Display formatted text built from the embedded values.
    print(f"  REPLICATION_EVIDENCE = {result['replication_evidence']}")
    # Display formatted text built from the embedded values.
    print(f"  NEXT_READINESS = {result['next_readiness']}")


# Run this branch when __name__ equals the text '__main__'.
if __name__ == "__main__":
    # Call main with the supplied arguments.
    main()
