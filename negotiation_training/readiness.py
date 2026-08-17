"""Evidence-aware readiness layered after the immutable Step 5J.2 freeze."""

import json
from hashlib import sha256
from pathlib import Path

from experimentation import ScenarioRole, assess_step_5j_2_design_completion
from .models import CoupledEnvironmentReadinessEvidence

READY = "READY_TO_BUILD_COUPLED_MAPPO_ENVIRONMENT"


def load_coupling_evidence(path="results/identical_condition_branch_replay.json"):
    evidence = json.loads(Path(path).read_text(encoding="utf-8"))
    required = (
        evidence.get("status") == "CAUSAL_EXECUTION_PATH_VALIDATED",
        evidence.get("physical_causal_witness") is True,
        evidence.get("completed_branch_count") == 2,
        evidence.get("blocked_zone_entry_violation_count") == 0,
        not evidence.get("next_blocker"),
    )
    if not all(required):
        raise ValueError("CAUSAL_COUPLING_EVIDENCE_NOT_VALIDATED")
    return evidence


def assess_step_5j_3a_environment_readiness(frozen_design, coupling_evidence):
    if assess_step_5j_2_design_completion(frozen_design) != "CONTROLLED_PILOT_DESIGN_FROZEN":
        raise ValueError("STEP_5J_2_DESIGN_NOT_FROZEN")
    manifests = frozen_design["manifests"]
    if set(manifests) != set(ScenarioRole) or any(
            item.frozen_status != "FROZEN_BEFORE_PILOT_EXECUTION"
            for item in manifests.values()):
        raise ValueError("SCENARIO_MANIFESTS_NOT_FROZEN")
    load_checks = (
        coupling_evidence["status"] == "CAUSAL_EXECUTION_PATH_VALIDATED",
        coupling_evidence["physical_causal_witness"] is True,
        coupling_evidence["completed_branch_count"] == 2,
        coupling_evidence["blocked_zone_entry_violation_count"] == 0,
    )
    if not all(load_checks):
        raise ValueError("CAUSAL_COUPLING_EVIDENCE_NOT_VALIDATED")
    identity = (frozen_design["freeze"].freeze_id,
                manifests[ScenarioRole.TRAINING].manifest_id,
                coupling_evidence["fingerprint_ids"])
    return CoupledEnvironmentReadinessEvidence(
        ("STEP_5J_3A_ENVIRONMENT_EVIDENCE_V1",
         sha256(repr(identity).encode()).hexdigest()),
        frozen_design["freeze"].freeze_id,
        manifests[ScenarioRole.TRAINING].manifest_id,
        coupling_evidence["status"], True, 2, True, READY,
        {"post_freeze_layer": True, "frozen_design_mutated": False,
         "route_truth_policy_leakage": 0, "reward_changed": False,
         "protocol_changed": False,
         "physical_authority": "SUMO_PROCESS_TRACI_SPEED_CONTROL"})


def assess_step_5j_3b_pilot_readiness(profile):
    if (profile.get("status") == "COUPLED_ENVIRONMENT_PROFILE_COMPLETE" and
            profile.get("hard_validity_gates_passed") is True and
            profile.get("profiling_samples_ppo_eligible") is False and
            profile.get("optimizer_instances") == 0):
        return "READY_TO_IMPLEMENT_FIRST_CONTROLLED_MAPPO_PILOT"
    return "STEP_5J_3A_PROFILE_INCOMPLETE"


def assess_step_5j_3b_behavior_policy_readiness(
        profile_path="results/coupled_environment_profile.json"):
    """Gate real behavior-policy implementation on both complete contracts."""
    from .adam_contract import build_mechanical_adam_optimization_contract
    from .architecture_contract import build_mechanical_pilot_architecture_contract

    profile = json.loads(Path(profile_path).read_text(encoding="utf-8"))
    architecture = build_mechanical_pilot_architecture_contract(profile_path)
    optimization = build_mechanical_adam_optimization_contract(profile_path)
    ready = (
        not architecture.unresolved_architecture_fields
        and not optimization.unresolved_optimizer_fields
        and optimization.critic_loss_reduction ==
        "PER_JOINT_DECISION_BATCH_EMPIRICAL_MEAN_SQUARED_ERROR"
        and architecture.frozen_design_id == optimization.frozen_design_id
        and assess_step_5j_3b_pilot_readiness(profile) ==
        "READY_TO_IMPLEMENT_FIRST_CONTROLLED_MAPPO_PILOT"
    )
    return ("READY_TO_IMPLEMENT_REAL_MAPPO_BEHAVIOR_POLICY" if ready else
            "STEP_5J_3B_CONFIGURATION_INCOMPLETE")
