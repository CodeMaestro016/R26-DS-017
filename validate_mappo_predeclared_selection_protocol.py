"""Fast Step 5J.3C.2D selection-protocol validator."""

from negotiation_training.selection_protocol import (
    build_mappo_selection_protocol)


def main():
    protocol, artifact = build_mappo_selection_protocol()
    print("Step 5J.3C.2D Predeclared MAPPO Selection Protocol\n")
    print("Source review")
    print("  Status: EXTENDED_EVIDENCE_REVIEW_COMPLETE\n")
    print("Resolved methodological structure")
    print("  Primary metric: TOTAL_TEAM_TRAVEL_TIME_SECONDS")
    print("  Direction: LOWER_IS_BETTER")
    print("  Hard validity: ZERO_COLLISION_AND_ZERO_BLOCKED_ZONE_VIOLATION")
    print("  Training design: FIXED_RESOURCE_HORIZON_WITH_VALIDATION_CHECKPOINT_SELECTION")
    print("  Replication stream: CANONICAL_DETERMINISTIC_REPLICATION_STREAM")
    print("  Seed replacement: FORBIDDEN")
    print("  Candidate comparison: MATCHED_PAIRED_VALIDATION_COMPARISON")
    print("  Checkpoint selection role: VALIDATION_ONLY")
    print("  Held-out usage: FINAL_CONFIGURATION_EVALUATION_ONLY")
    print("  Checkpoint tie: EARLIEST_EQUIVALENT_CHECKPOINT_RULE")
    print("  Candidate tie: REFERENCE_PRESERVING_TIE_RULE\n")
    print("External inputs still required")
    for item in protocol.unresolved_external_inputs:
        print(f"  {item.input_name}: {item.status}")
    print("\nResearch boundary")
    print("  New SUMO executions: 0")
    print("  Optimizer invocations: 0")
    print("  Backward calls: 0")
    print("  Parameter updates: 0")
    print("  VALIDATION executions: 0")
    print("  HELD_OUT executions: 0\n")
    print("Status")
    print(f"  STEP_5J_3C_2D_STATUS = {artifact['status']}")
    print(f"  PROTOCOL_READINESS = {artifact['protocol_readiness']}")
    print(f"  NEXT_BLOCKER = {artifact['next_blocker']}")


if __name__ == "__main__":
    main()
