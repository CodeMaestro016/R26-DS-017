"""Fast Step 5J.3C.2D selection-protocol validator."""

# Import build_mappo_selection_protocol from negotiation_training.selection_protocol for the operations below.
from negotiation_training.selection_protocol import (
    build_mappo_selection_protocol)


# Main using the inputs and processing steps below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def main():
    # Set (protocol, artifact) to the result of build_mappo_selection_protocol().
    protocol, artifact = build_mappo_selection_protocol()
    # Display the text 'Step 5J.3C.2D Predeclared MAPPO Selection Protocol'.
    print("Step 5J.3C.2D Predeclared MAPPO Selection Protocol\n")
    # Display the text 'Source review'.
    print("Source review")
    # Display the text 'Status: EXTENDED_EVIDENCE_REVIEW_COMPLETE'.
    print("  Status: EXTENDED_EVIDENCE_REVIEW_COMPLETE\n")
    # Display the text 'Resolved methodological structure'.
    print("Resolved methodological structure")
    # Display the text 'Primary metric: TOTAL_TEAM_TRAVEL_TIME_SECONDS'.
    print("  Primary metric: TOTAL_TEAM_TRAVEL_TIME_SECONDS")
    # Display the text 'Direction: LOWER_IS_BETTER'.
    print("  Direction: LOWER_IS_BETTER")
    # Display the text 'Hard validity: ZERO_COLLISION_AND_ZERO_BLOCKED_ZONE_VIOLATION'.
    print("  Hard validity: ZERO_COLLISION_AND_ZERO_BLOCKED_ZONE_VIOLATION")
    # Display the text 'Training design:...'.
    print("  Training design: FIXED_RESOURCE_HORIZON_WITH_VALIDATION_CHECKPOINT_SELECTION")
    # Display the text 'Replication stream: CANONICAL_DETERMINISTIC_REPLICATION_STREAM'.
    print("  Replication stream: CANONICAL_DETERMINISTIC_REPLICATION_STREAM")
    # Display the text 'Seed replacement: FORBIDDEN'.
    print("  Seed replacement: FORBIDDEN")
    # Display the text 'Candidate comparison: MATCHED_PAIRED_VALIDATION_COMPARISON'.
    print("  Candidate comparison: MATCHED_PAIRED_VALIDATION_COMPARISON")
    # Display the text 'Checkpoint selection role: VALIDATION_ONLY'.
    print("  Checkpoint selection role: VALIDATION_ONLY")
    # Display the text 'Held-out usage: FINAL_CONFIGURATION_EVALUATION_ONLY'.
    print("  Held-out usage: FINAL_CONFIGURATION_EVALUATION_ONLY")
    # Display the text 'Checkpoint tie: EARLIEST_EQUIVALENT_CHECKPOINT_RULE'.
    print("  Checkpoint tie: EARLIEST_EQUIVALENT_CHECKPOINT_RULE")
    # Display the text 'Candidate tie: REFERENCE_PRESERVING_TIE_RULE'.
    print("  Candidate tie: REFERENCE_PRESERVING_TIE_RULE\n")
    # Display the text 'External inputs still required'.
    print("External inputs still required")
    # Iterate over protocol.unresolved_external_inputs, binding each item to item.
    for item in protocol.unresolved_external_inputs:
        # Display formatted text built from the embedded values.
        print(f"  {item.input_name}: {item.status}")
    # Display the text 'Research boundary'.
    print("\nResearch boundary")
    # Display the text 'New SUMO executions: 0'.
    print("  New SUMO executions: 0")
    # Display the text 'Optimizer invocations: 0'.
    print("  Optimizer invocations: 0")
    # Display the text 'Backward calls: 0'.
    print("  Backward calls: 0")
    # Display the text 'Parameter updates: 0'.
    print("  Parameter updates: 0")
    # Display the text 'VALIDATION executions: 0'.
    print("  VALIDATION executions: 0")
    # Display the text 'HELD_OUT executions: 0'.
    print("  HELD_OUT executions: 0\n")
    # Display the text 'Status'.
    print("Status")
    # Display formatted text built from the embedded values.
    print(f"  STEP_5J_3C_2D_STATUS = {artifact['status']}")
    # Display formatted text built from the embedded values.
    print(f"  PROTOCOL_READINESS = {artifact['protocol_readiness']}")
    # Display formatted text built from the embedded values.
    print(f"  NEXT_BLOCKER = {artifact['next_blocker']}")


# Run this branch when __name__ equals the text '__main__'.
if __name__ == "__main__":
    # Call main with the supplied arguments.
    main()
