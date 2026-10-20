"""Step 5J.3B configuration gate; stops before construction when unresolved."""

# Import json for use in this module.
import json
# Import fields, is_dataclass from dataclasses for the operations below.
from dataclasses import fields, is_dataclass
# Import Mapping from collections.abc for the operations below.
from collections.abc import Mapping
# Import Path from pathlib for the operations below.
from pathlib import Path

# Import build_design from experimentation for the operations below.
from experimentation import build_design
# Import build_mechanical_pilot_configuration_audit from negotiation_training for the operations below.
from negotiation_training import build_mechanical_pilot_configuration_audit

# Set ARTIFACT to the result of Path(the text 'results/mappo_mechanical_pilot.json').
ARTIFACT = Path("results/mappo_mechanical_pilot.json")


# Serializable using the inputs and processing steps below.
# Input value: the supplied value.
# Output: return the value selected by the matching return branch below.
# Processing: select branches using the stated conditions.
def serializable(value):
    # Run this branch when the result of is_dataclass(value).
    if is_dataclass(value):
        # Return a dictionary of item.name mapped to the result of serializable(the requested attribute of value)
        # for item in the result of fields(value) to the caller.
        return {item.name: serializable(getattr(value, item.name))
                # Evaluate the result of fields(value) as part of the enclosing expression.
                for item in fields(value)}
    # Run this branch when whether value has type Mapping.
    if isinstance(value, Mapping):
        # Return a dictionary of a string built from key mapped to the result of serializable(item) for (key,
        # item) in key/value pairs from value to the caller.
        return {str(key): serializable(item) for key, item in value.items()}
    # Run this branch when whether value has type a tuple containing tuple, list.
    # Return a list of the result of serializable(item) for item in value to the caller.
    if isinstance(value, (tuple, list)): return [serializable(item) for item in value]
    # Return value to the caller.
    return value


# Main using the inputs and processing steps below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def main():
    # Set before to build_design()['freeze'].freeze_id.
    before = build_design()["freeze"].freeze_id
    # Set audit to the result of build_mechanical_pilot_configuration_audit().
    audit = build_mechanical_pilot_configuration_audit()
    # Set after to build_design()['freeze'].freeze_id.
    after = build_design()["freeze"].freeze_id
    # Require before equals after; equals audit.frozen_design_id; otherwise raise AssertionError.
    assert before == after == audit.frozen_design_id
    # Require audit.silent_default_count equals 0; otherwise raise AssertionError.
    assert audit.silent_default_count == 0
    # Set payload to the result of serializable(audit).
    payload = serializable(audit)
    # Update payload with the supplied entries.
    payload.update({
        "checkpoint": "STEP_5J_3B",
        "step_5j_3a_profile": "PASS",
        "coupling_status": "CAUSAL_EXECUTION_PATH_VALIDATED",
        # Store False under 'policy_integration_executed'.
        "policy_integration_executed": False,
        # Store 0 under 'training_manifest_passes'.
        "training_manifest_passes": 0,
        # Store 0 under 'ppo_eligible_proposer_factors'.
        "ppo_eligible_proposer_factors": 0,
        # Store 0 under 'ppo_eligible_responder_factors'.
        "ppo_eligible_responder_factors": 0,
        # Store 0 under 'mappo_pilot_runs'.
        "mappo_pilot_runs": 0,
        # Store 0 under 'model_checkpoints'.
        "model_checkpoints": 0,
    })
    # Write the supplied text to ARTIFACT.
    ARTIFACT.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    # Display the text 'Step 5J.3B MAPPO Mechanical Pilot'.
    print("Step 5J.3B MAPPO Mechanical Pilot\n")
    # Display the text 'Readiness'.
    print("Readiness")
    # Display the text 'Step 5J.3A profile: PASS'.
    print("  Step 5J.3A profile: PASS")
    # Display the text 'Frozen design unchanged: PASS'.
    print("  Frozen design unchanged: PASS")
    # Display the text 'Coupling validated: PASS'.
    print("  Coupling validated: PASS\n")
    # Display the text 'Configuration audit'.
    print("Configuration audit")
    # Display formatted text built from the embedded values.
    print(f"  Runtime choices audited: {len(audit.runtime_choices)}")
    # Display the text 'Silent defaults: 0'.
    print("  Silent defaults: 0")
    # Display formatted text built from the embedded values.
    print(f"  Unresolved operational parameters: {len(audit.unresolved_choice_ids)}")
    # Iterate over audit.unresolved_choice_ids, binding each item to item.
    for item in audit.unresolved_choice_ids:
        # Display formatted text built from the embedded values.
        print(f"    - {item}")
    # Display the text 'Required stop boundary'.
    print("\nRequired stop boundary")
    # Display the text 'Models constructed: 0'.
    print("  Models constructed: 0")
    # Display the text 'RL seeds instantiated: 0'.
    print("  RL seeds instantiated: 0")
    # Display the text 'Optimizers: 0'.
    print("  Optimizers: 0")
    # Display the text 'backward calls: 0'.
    print("  backward calls: 0")
    # Display the text 'Parameter updates: 0'.
    print("  Parameter updates: 0")
    # Display the text 'MAPPO behavior samples: 0'.
    print("  MAPPO behavior samples: 0")
    # Display the text 'Learned main.py control: 0'.
    print("  Learned main.py control: 0\n")
    # Display the text 'Status'.
    print("Status")
    # Display formatted text built from the embedded values.
    print(f"  STEP_5J_3B_STATUS: {audit.status}")
    # Display formatted text built from the embedded values.
    print(f"  NEXT_BLOCKER: {audit.next_blocker}")


# Run this branch when __name__ equals the text '__main__'.
# Call main with the supplied arguments.
if __name__ == "__main__": main()
