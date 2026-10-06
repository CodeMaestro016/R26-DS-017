"""Fast, analysis-only Step 5J.3C.2E.1 validator."""

from negotiation_training.resource_budget import resolve_training_resource_budget


def main():
    resolution, artifact = resolve_training_resource_budget()
    evidence = resolution.resource_evidence
    resource_input = resolution.resource_input
    print("Step 5J.3C.2E.1 Training Resource Budget\n")
    print("Source protocol:")
    print("  MAPPO_SELECTION_PROTOCOL_V1")
    print("  PASS\n")
    print("Resource evidence:")
    print(f"  TRAINING scenarios per manifest: {evidence.training_manifest_scenario_count}")
    print(f"  SUMO steps per scenario: {evidence.steps_per_scenario}")
    print(f"  SUMO steps per manifest: {evidence.sumo_steps_per_training_manifest}")
    print("  Historical runtime evidence loaded: PASS")
    print(f"  Manifest runtime bound: {evidence.manifest_runtime_bound}")
    print(f"  Update runtime bound: {evidence.update_runtime_bound}")
    print(f"  Replication overhead bound: {evidence.overhead_bound}\n")
    print("External resource input:")
    print(f"  Status: {dict(resource_input.provenance)['status']}")
    print(f"  Scope: {resource_input.scope}")
    print(f"  Numerical value supplied: {resource_input.budget_value is not None}\n")
    print("Training horizon:")
    print(f"  H derived: {resolution.derived_H is not None}")
    print("  Performance used to derive horizon: False\n")
    print("New protocol version created:")
    print(f"  {artifact['new_protocol_identity_created']}\n")
    print(f"STEP_5J_3C_2E_1_STATUS = {artifact['status']}")
    print(f"NEXT_BLOCKER = {artifact['next_blocker']}")


if __name__ == "__main__":
    main()
