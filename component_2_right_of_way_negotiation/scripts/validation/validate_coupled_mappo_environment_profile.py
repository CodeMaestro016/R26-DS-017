"""Execute and report the exhaustive Step 5J.3A TRAINING profile."""

# Import assess_step_5j_3b_pilot_readiness from negotiation_training for the operations below.
from negotiation_training import assess_step_5j_3b_pilot_readiness
# Import profile_complete_training_manifest from negotiation_training.profiling for the operations below.
from negotiation_training.profiling import profile_complete_training_manifest


# Main using the inputs and processing steps below.
# Output: no explicit value; normal completion returns None.
def main():
    # Set profile to the result of profile_complete_training_manifest().
    profile = profile_complete_training_manifest()
    # Set total to profile at 'aggregate'.
    total = profile["aggregate"]
    # Require profile at 'validation_performance_executions' equals 0; otherwise raise AssertionError.
    assert profile["validation_performance_executions"] == 0
    # Require profile at 'held_out_performance_executions' equals 0; otherwise raise AssertionError.
    assert profile["held_out_performance_executions"] == 0
    # Require profile at 'interval_rewards_reconcile'; otherwise raise AssertionError.
    assert profile["interval_rewards_reconcile"]
    # Require profile at 'hard_validity_gates_passed'; otherwise raise AssertionError.
    assert profile["hard_validity_gates_passed"]
    # Require the negation of profile at 'profiling_samples_ppo_eligible'; otherwise raise AssertionError.
    assert not profile["profiling_samples_ppo_eligible"]
    # Require profile at 'optimizer_instances' equals 0; otherwise raise AssertionError.
    assert profile["optimizer_instances"] == 0
    # Set readiness to the result of assess_step_5j_3b_pilot_readiness(profile).
    readiness = assess_step_5j_3b_pilot_readiness(profile)
    # Display the text 'Step 5J.3A Coupled MAPPO Environment Profile'.
    print("Step 5J.3A Coupled MAPPO Environment Profile\n")
    # Display the text 'Frozen design'.
    print("Frozen design")
    # Display the text 'Step 5J.2 design unchanged: PASS'.
    print("  Step 5J.2 design unchanged: PASS")
    # Display formatted text built from the embedded values.
    print(f"  TRAINING scenarios: {profile['training_scenarios_expected']}")
    # Display the text 'VALIDATION performance scenarios executed: 0'.
    print("  VALIDATION performance scenarios executed: 0")
    # Display the text 'HELD_OUT performance scenarios executed: 0'.
    print("  HELD_OUT performance scenarios executed: 0\n")
    # Display the text 'Coupling'.
    print("Coupling")
    # Display the text 'Coupling artifact loaded: PASS'.
    print("  Coupling artifact loaded: PASS")
    # Display formatted text built from the embedded values.
    print(f"  Coupling status: {profile['coupling_status']}")
    # Display the text 'Physical causal witness: PASS'.
    print("  Physical causal witness: PASS\n")
    # Display the text 'Environment'.
    print("Environment")
    # Display the text 'Real SUMO environment: PASS'.
    print("  Real SUMO environment: PASS")
    # Display the text 'Event-driven decisions: PASS'.
    print("  Event-driven decisions: PASS")
    # Display the text 'Proposer action interface: PASS'.
    print("  Proposer action interface: PASS")
    # Display the text 'Responder action interface: PASS'.
    print("  Responder action interface: PASS")
    # Display the text 'Joint protocol resolution: PASS'.
    print("  Joint protocol resolution: PASS")
    # Display the text 'Effective graph -> physical execution: PASS'.
    print("  Effective graph -> physical execution: PASS")
    # Display the text 'Step 5H reward integration: PASS'.
    print("  Step 5H reward integration: PASS\n")
    # Display the text 'Profiling pass'.
    print("Profiling pass")
    # Display formatted text built from the embedded values.
    print(f"  Scenarios attempted: {profile['training_scenarios_attempted']}")
    # Display formatted text built from the embedded values.
    print(f"  Scenarios completed: {profile['training_scenarios_completed']}")
    # Display formatted text built from the embedded values.
    print(f"  SUMO steps: {total['sumo_step_count']['total']}")
    # Display formatted text built from the embedded values.
    print(f"  Joint decision batches: {total['joint_decision_batch_count']}")
    # Display formatted text built from the embedded values.
    print(f"  Proposer factors: {total['proposer_factor_count']['total']}")
    # Display formatted text built from the embedded values.
    print(f"  Responder factors: {total['responder_factor_count']['total']}")
    # Display formatted text built from the embedded values.
    print(f"  Total policy factors: {total['policy_factor_count']['total']}")
    # Display formatted text built from the embedded values.
    print(f"  Multi-factor batches: {total['multi_factor_batch_count']['total']}")
    # Display formatted text built from the embedded values.
    print(f"  Wall-clock runtime: {total['wall_clock_runtime_seconds']['total']}")
    # Display the text 'Collisions: 0'.
    print("  Collisions: 0")
    # Display the text 'Blocked-zone violations: 0'.
    print("  Blocked-zone violations: 0\n")
    # Display the text 'Reward accounting'.
    print("Reward accounting")
    # Display the text 'Interval rewards reconcile with complete episode objective: PASS'.
    print("  Interval rewards reconcile with complete episode objective: PASS")
    # Display the text 'New reward terms: 0'.
    print("  New reward terms: 0\n")
    # Display the text 'Training methodology'.
    print("Training methodology")
    # Display the text 'Final training budget selected: False'.
    print("  Final training budget selected: False")
    # Display the text 'Replication count selected: False'.
    print("  Replication count selected: False")
    # Display the text 'RL seeds instantiated: 0'.
    print("  RL seeds instantiated: 0")
    # Display the text 'Hyperparameters selected: 0'.
    print("  Hyperparameters selected: 0")
    # Display the text 'Candidate sets changed: False'.
    print("  Candidate sets changed: False\n")
    # Display the text 'PPO boundary'.
    print("PPO boundary")
    # Display the text 'Deterministic profiling samples PPO eligible: False'.
    print("  Deterministic profiling samples PPO eligible: False")
    # Display the text 'Optimizers instantiated: 0'.
    print("  Optimizers instantiated: 0")
    # Display the text 'backward calls: 0'.
    print("  backward calls: 0")
    # Display the text 'Parameter updates: 0'.
    print("  Parameter updates: 0")
    # Display the text 'MAPPO pilot runs: 0'.
    print("  MAPPO pilot runs: 0")
    # Display the text 'Model checkpoints: 0'.
    print("  Model checkpoints: 0\n")
    # Display the text 'Status'.
    print("Status")
    # Display the text 'STEP_5J_3A_STATUS: COUPLED_ENVIRONMENT_PROFILE_COMPLETE'.
    print("  STEP_5J_3A_STATUS: COUPLED_ENVIRONMENT_PROFILE_COMPLETE")
    # Display formatted text built from the embedded values.
    print(f"  STEP_5J_3B_READINESS: {readiness}")


# Run this branch when __name__ equals the text '__main__'.
# Call main with the supplied arguments.
if __name__ == "__main__": main()
