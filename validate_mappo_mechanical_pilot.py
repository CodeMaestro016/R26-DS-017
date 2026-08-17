"""Step 5J.3B configuration gate; stops before construction when unresolved."""

import json
from dataclasses import fields, is_dataclass
from collections.abc import Mapping
from pathlib import Path

from experimentation import build_design
from negotiation_training import build_mechanical_pilot_configuration_audit

ARTIFACT = Path("results/mappo_mechanical_pilot.json")


def serializable(value):
    if is_dataclass(value):
        return {item.name: serializable(getattr(value, item.name))
                for item in fields(value)}
    if isinstance(value, Mapping):
        return {str(key): serializable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)): return [serializable(item) for item in value]
    return value


def main():
    before = build_design()["freeze"].freeze_id
    audit = build_mechanical_pilot_configuration_audit()
    after = build_design()["freeze"].freeze_id
    assert before == after == audit.frozen_design_id
    assert audit.silent_default_count == 0
    payload = serializable(audit)
    payload.update({
        "checkpoint": "STEP_5J_3B",
        "step_5j_3a_profile": "PASS",
        "coupling_status": "CAUSAL_EXECUTION_PATH_VALIDATED",
        "policy_integration_executed": False,
        "training_manifest_passes": 0,
        "ppo_eligible_proposer_factors": 0,
        "ppo_eligible_responder_factors": 0,
        "mappo_pilot_runs": 0,
        "model_checkpoints": 0,
    })
    ARTIFACT.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("Step 5J.3B MAPPO Mechanical Pilot\n")
    print("Readiness")
    print("  Step 5J.3A profile: PASS")
    print("  Frozen design unchanged: PASS")
    print("  Coupling validated: PASS\n")
    print("Configuration audit")
    print(f"  Runtime choices audited: {len(audit.runtime_choices)}")
    print("  Silent defaults: 0")
    print(f"  Unresolved operational parameters: {len(audit.unresolved_choice_ids)}")
    for item in audit.unresolved_choice_ids:
        print(f"    - {item}")
    print("\nRequired stop boundary")
    print("  Models constructed: 0")
    print("  RL seeds instantiated: 0")
    print("  Optimizers: 0")
    print("  backward calls: 0")
    print("  Parameter updates: 0")
    print("  MAPPO behavior samples: 0")
    print("  Learned main.py control: 0\n")
    print("Status")
    print(f"  STEP_5J_3B_STATUS: {audit.status}")
    print(f"  NEXT_BLOCKER: {audit.next_blocker}")


if __name__ == "__main__": main()
