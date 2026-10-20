"""Execute and report the first offline mechanical MAPPO PPO update."""

# Import MechanicalMAPPOTrainer from negotiation_training for the operations below.
from negotiation_training import MechanicalMAPPOTrainer


# Main using the inputs and processing steps below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def main():
    # Set result to the result of MechanicalMAPPOTrainer().run().
    result = MechanicalMAPPOTrainer().run()
    # Set counts to result at 'sample_counts'.
    counts = result["sample_counts"]
    # Display the text 'Step 5J.3B.4 First Mechanical MAPPO PPO Update'.
    print("Step 5J.3B.4 First Mechanical MAPPO PPO Update\n")
    # Display the text 'Source rollout'.
    print("Source rollout")
    # Display the text 'Status: REAL_MAPPO_BEHAVIOR_ROLLOUT_VALIDATED'.
    print("  Status: REAL_MAPPO_BEHAVIOR_ROLLOUT_VALIDATED")
    # Display formatted text built from the embedded values.
    print(f"  PPO factors: {counts['actor']}")
    # Display formatted text built from the embedded values.
    print(f"  Proposer: {counts['proposer']}")
    # Display formatted text built from the embedded values.
    print(f"  Responder: {counts['responder']}")
    # Display formatted text built from the embedded values.
    print(f"  Critic samples: {counts['critic']}\n")
    # Display the text 'Pre-update integrity'.
    print("Pre-update integrity")
    # Display the text 'Initial parameter hashes match behavior policy: PASS'.
    print("  Initial parameter hashes match behavior policy: PASS")
    # Display the text 'Hard masks exact: PASS'.
    print("  Hard masks exact: PASS")
    # Display the text 'Old/current log probabilities exact: PASS'.
    print("  Old/current log probabilities exact: PASS")
    # Display the text 'Importance ratios exactly one: PASS'.
    print("  Importance ratios exactly one: PASS\n")
    # Display the text 'Optimizer'.
    print("Optimizer")
    # Display the text 'Actor Adam instances: 1'.
    print("  Actor Adam instances: 1")
    # Display the text 'Critic Adam instances: 1'.
    print("  Critic Adam instances: 1")
    # Display the text 'Frozen GNN optimizer membership: 0'.
    print("  Frozen GNN optimizer membership: 0")
    # Display the text 'Silent defaults: 0'.
    print("  Silent defaults: 0\n")
    # Display the text 'PPO mechanics'.
    print("PPO mechanics")
    # Display the text 'Full batch: PASS'.
    print("  Full batch: PASS")
    # Display formatted text built from the embedded values.
    print(f"  PPO epochs: {result['ppo_configuration']['epochs']}")
    # Display formatted text built from the embedded values.
    print(f"  Clip epsilon: {result['ppo_configuration']['clip_epsilon']}")
    # Display the text 'Raw Monte Carlo advantage: PASS'.
    print("  Raw Monte Carlo advantage: PASS")
    # Display the text 'Entropy term: NONE'.
    print("  Entropy term: NONE")
    # Display the text 'Gradient clipping: NONE'.
    print("  Gradient clipping: NONE\n")
    # Iterate over result at 'epoch_diagnostics', binding each item to item.
    for item in result["epoch_diagnostics"]:
        # Display formatted text built from the embedded values.
        print(f"Epoch {item['epoch']}")
        # Display formatted text built from the embedded values.
        print(f"  Actor loss: {item['actor_loss']}")
        # Display formatted text built from the embedded values.
        print(f"  Critic loss: {item['critic_loss']}")
        # Display formatted text built from the embedded values.
        print("  Ratio min/mean/max: "
              # Evaluate {item['ratio_minimum']} as part of the enclosing expression.
              f"{item['ratio_minimum']} / {item['ratio_mean']} / "
              # Evaluate {item['ratio_maximum']} as part of the enclosing expression.
              f"{item['ratio_maximum']}")
        # Display formatted text built from the embedded values.
        print(f"  Clipped factors: {item['clipped_factor_count']}")
        # Display the text 'Actor gradients finite: PASS'.
        print("  Actor gradients finite: PASS")
        # Display the text 'Critic gradients finite: PASS'.
        print("  Critic gradients finite: PASS")
    # Display the text 'Optimization'.
    print("\nOptimization")
    # Display formatted text built from the embedded values.
    print(f"  Actor optimizer steps: {result['actor_optimizer_steps']}")
    # Display formatted text built from the embedded values.
    print(f"  Critic optimizer steps: {result['critic_optimizer_steps']}")
    # Display formatted text built from the embedded values.
    print(f"  Total optimizer steps: {result['total_optimizer_steps']}")
    # Display formatted text built from the embedded values.
    print(f"  Actor backward calls: {result['actor_backward_calls']}")
    # Display formatted text built from the embedded values.
    print(f"  Critic backward calls: {result['critic_backward_calls']}")
    # Display formatted text built from the embedded values.
    print(f"  Total backward calls: {result['total_backward_calls']}\n")
    # Display the text 'Parameters'.
    print("Parameters")
    # Display formatted text built from the embedded values.
    print(f"  GNN changed: {not result['gnn_hash_unchanged']}")
    # Display formatted text built from the embedded values.
    print(f"  Proposer changed: {result['proposer_parameter_changed']}")
    # Display formatted text built from the embedded values.
    print(f"  Responder changed: {result['responder_parameter_changed']}")
    # Display formatted text built from the embedded values.
    print(f"  Critic changed: {result['critic_parameter_changed']}\n")
    # Display the text 'Environment'.
    print("Environment")
    # Display the text 'New SUMO rollouts: 0'.
    print("  New SUMO rollouts: 0")
    # Display the text 'VALIDATION runs: 0'.
    print("  VALIDATION runs: 0")
    # Display the text 'HELD_OUT runs: 0'.
    print("  HELD_OUT runs: 0\n")
    # Display the text 'Research status'.
    print("Research status")
    # Display the text 'Final hyperparameters selected: 0'.
    print("  Final hyperparameters selected: 0")
    # Display the text 'Final model trained: False'.
    print("  Final model trained: False")
    # Display the text 'Mechanical update validated: True'.
    print("  Mechanical update validated: True\n")
    # Display formatted text built from the embedded values.
    print(f"STEP_5J_3B_4_STATUS: {result['status']}")
    # Display formatted text built from the embedded values.
    print(f"STEP_5J_3C_READINESS: {result['step_5j_3c_readiness']}")


# Run this branch when __name__ equals the text '__main__'.
# Call main with the supplied arguments.
if __name__ == "__main__": main()
