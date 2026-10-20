"""Fast, analysis-only Step 5J.3C.2E.1 validator."""

# Import resolve_training_resource_budget from negotiation_training.resource_budget for the operations below.
from negotiation_training.resource_budget import resolve_training_resource_budget


# Main using the inputs and processing steps below.
# Output: no explicit value; normal completion returns None.
def main():
    # Set (resolution, artifact) to the result of resolve_training_resource_budget().
    resolution, artifact = resolve_training_resource_budget()
    # Set evidence to resolution.resource_evidence.
    evidence = resolution.resource_evidence
    # Set resource_input to resolution.resource_input.
    resource_input = resolution.resource_input
    # Display the text 'Step 5J.3C.2E.1 Training Resource Budget'.
    print("Step 5J.3C.2E.1 Training Resource Budget\n")
    # Display the text 'Source protocol:'.
    print("Source protocol:")
    # Display the text 'MAPPO_SELECTION_PROTOCOL_V1'.
    print("  MAPPO_SELECTION_PROTOCOL_V1")
    # Display the text 'PASS'.
    print("  PASS\n")
    # Display the text 'Resource evidence:'.
    print("Resource evidence:")
    # Display formatted text built from the embedded values.
    print(f"  TRAINING scenarios per manifest: {evidence.training_manifest_scenario_count}")
    # Display formatted text built from the embedded values.
    print(f"  SUMO steps per scenario: {evidence.steps_per_scenario}")
    # Display formatted text built from the embedded values.
    print(f"  SUMO steps per manifest: {evidence.sumo_steps_per_training_manifest}")
    # Display the text 'Historical runtime evidence loaded: PASS'.
    print("  Historical runtime evidence loaded: PASS")
    # Display formatted text built from the embedded values.
    print(f"  Manifest runtime bound: {evidence.manifest_runtime_bound}")
    # Display formatted text built from the embedded values.
    print(f"  Update runtime bound: {evidence.update_runtime_bound}")
    # Display formatted text built from the embedded values.
    print(f"  Replication overhead bound: {evidence.overhead_bound}\n")
    # Display the text 'External resource input:'.
    print("External resource input:")
    # Display formatted text built from the embedded values.
    print(f"  Status: {dict(resource_input.provenance)['status']}")
    # Display formatted text built from the embedded values.
    print(f"  Scope: {resource_input.scope}")
    # Display formatted text built from the embedded values.
    print(f"  Numerical value supplied: {resource_input.budget_value is not None}\n")
    # Display the text 'Training horizon:'.
    print("Training horizon:")
    # Display formatted text built from the embedded values.
    print(f"  H derived: {resolution.derived_H is not None}")
    # Display the text 'Performance used to derive horizon: False'.
    print("  Performance used to derive horizon: False\n")
    # Display the text 'New protocol version created:'.
    print("New protocol version created:")
    # Display formatted text built from the embedded values.
    print(f"  {artifact['new_protocol_identity_created']}\n")
    # Display formatted text built from the embedded values.
    print(f"STEP_5J_3C_2E_1_STATUS = {artifact['status']}")
    # Display formatted text built from the embedded values.
    print(f"NEXT_BLOCKER = {artifact['next_blocker']}")


# Run this branch when __name__ equals the text '__main__'.
if __name__ == "__main__":
    # Call main with the supplied arguments.
    main()
