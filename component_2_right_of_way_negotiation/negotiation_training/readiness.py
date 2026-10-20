"""Evidence-aware readiness layered after the immutable Step 5J.2 freeze."""

# Import json for use in this module.
import json
# Import sha256 from hashlib for the operations below.
from hashlib import sha256
# Import Path from pathlib for the operations below.
from pathlib import Path

# Import ScenarioRole, assess_step_5j_2_design_completion from experimentation for the operations below.
from experimentation import ScenarioRole, assess_step_5j_2_design_completion
# Import CoupledEnvironmentReadinessEvidence from .models for the operations below.
from .models import CoupledEnvironmentReadinessEvidence

# Set READY to the text 'READY_TO_BUILD_COUPLED_MAPPO_ENVIRONMENT'.
READY = "READY_TO_BUILD_COUPLED_MAPPO_ENVIRONMENT"


# Load coupling evidence using the inputs and processing steps below.
# Input path: the path or path object supplied by the caller.
# Output: evidence.
# Processing: select branches using the stated conditions.
def load_coupling_evidence(path="results/identical_condition_branch_replay.json"):
    # Set evidence to the decoded data produced by json.loads from the text read from Path(path).
    evidence = json.loads(Path(path).read_text(encoding="utf-8"))
    # Set required to a tuple containing 'status' from evidence; use None if absent equals the text
    # 'CAUSAL_EXECUTION_PATH_VALIDATED',...
    required = (
        # Include 'status' from evidence; use None if absent equals the text 'CAUSAL_EXECUTION_PATH_VALIDATED' in
        # this tuple.
        evidence.get("status") == "CAUSAL_EXECUTION_PATH_VALIDATED",
        # Include 'physical_causal_witness' from evidence; use None if absent is the same object as True in this
        # tuple.
        evidence.get("physical_causal_witness") is True,
        # Include 'completed_branch_count' from evidence; use None if absent equals 2 in this tuple.
        evidence.get("completed_branch_count") == 2,
        # Include 'blocked_zone_entry_violation_count' from evidence; use None if absent equals 0 in this tuple.
        evidence.get("blocked_zone_entry_violation_count") == 0,
        # Include the negation of 'next_blocker' from evidence; use None if absent in this tuple.
        not evidence.get("next_blocker"),
    )
    # Run this branch when the negation of whether every item is true in required.
    if not all(required):
        # Raise ValueError with the text 'CAUSAL_COUPLING_EVIDENCE_NOT_VALIDATED' to stop this execution path.
        raise ValueError("CAUSAL_COUPLING_EVIDENCE_NOT_VALIDATED")
    # Return evidence to the caller.
    return evidence


# Assess step 5j 3a environment readiness using the inputs and processing steps below.
# Input frozen_design: the supplied frozen design.
# Input coupling_evidence: the supplied coupling evidence.
# Output: the result of CoupledEnvironmentReadinessEvidence(a tuple containing the text
# 'STEP_5J_3A_ENVIRONMENT_EVIDENCE_V1', the hexadecimal digest from...).
# Processing: select branches using the stated conditions.
def assess_step_5j_3a_environment_readiness(frozen_design, coupling_evidence):
    # Run this branch when the result of assess_step_5j_2_design_completion(frozen_design) differs from the text
    # 'CONTROLLED_PILOT_DESIGN_FROZEN'.
    if assess_step_5j_2_design_completion(frozen_design) != "CONTROLLED_PILOT_DESIGN_FROZEN":
        # Raise ValueError with the text 'STEP_5J_2_DESIGN_NOT_FROZEN' to stop this execution path.
        raise ValueError("STEP_5J_2_DESIGN_NOT_FROZEN")
    # Set manifests to frozen_design at 'manifests'.
    manifests = frozen_design["manifests"]
    # Run this branch when a set built from manifests differs from a set built from ScenarioRole or whether any
    # item is true in a lazy sequence of item.frozen_status differs from 'FROZEN_BEFORE_PILOT_EXECUTION' for item
    # in values from manifests.
    if set(manifests) != set(ScenarioRole) or any(
            # Evaluate item.frozen_status differs from the text 'FROZEN_BEFORE_PILOT_EXECUTION' as part of the
            # enclosing expression.
            item.frozen_status != "FROZEN_BEFORE_PILOT_EXECUTION"
            # Evaluate values from manifests as part of the enclosing expression.
            for item in manifests.values()):
        # Raise ValueError with the text 'SCENARIO_MANIFESTS_NOT_FROZEN' to stop this execution path.
        raise ValueError("SCENARIO_MANIFESTS_NOT_FROZEN")
    # Set load_checks to a tuple containing coupling_evidence at 'status' equals the text
    # 'CAUSAL_EXECUTION_PATH_VALIDATED', coupling_evidence at...
    load_checks = (
        # Include coupling_evidence at 'status' equals the text 'CAUSAL_EXECUTION_PATH_VALIDATED' in this tuple.
        coupling_evidence["status"] == "CAUSAL_EXECUTION_PATH_VALIDATED",
        # Include coupling_evidence at 'physical_causal_witness' is the same object as True in this tuple.
        coupling_evidence["physical_causal_witness"] is True,
        # Include coupling_evidence at 'completed_branch_count' equals 2 in this tuple.
        coupling_evidence["completed_branch_count"] == 2,
        # Include coupling_evidence at 'blocked_zone_entry_violation_count' equals 0 in this tuple.
        coupling_evidence["blocked_zone_entry_violation_count"] == 0,
    )
    # Run this branch when the negation of whether every item is true in load_checks.
    if not all(load_checks):
        # Raise ValueError with the text 'CAUSAL_COUPLING_EVIDENCE_NOT_VALIDATED' to stop this execution path.
        raise ValueError("CAUSAL_COUPLING_EVIDENCE_NOT_VALIDATED")
    # Set identity to a tuple containing frozen_design['freeze'].freeze_id,
    # manifests[ScenarioRole.TRAINING].manifest_id, coupling_evidence at...
    identity = (frozen_design["freeze"].freeze_id,
                # Include manifests[ScenarioRole.TRAINING].manifest_id in this tuple.
                manifests[ScenarioRole.TRAINING].manifest_id,
                # Include coupling_evidence at 'fingerprint_ids' in this tuple.
                coupling_evidence["fingerprint_ids"])
    # Return the result of CoupledEnvironmentReadinessEvidence(a tuple containing the text
    # 'STEP_5J_3A_ENVIRONMENT_EVIDENCE_V1', the hexadecimal digest from...) to the caller.
    return CoupledEnvironmentReadinessEvidence(
        # Supply a tuple containing the text 'STEP_5J_3A_ENVIRONMENT_EVIDENCE_V1', the hexadecimal digest from
        # sha256(repr(identity).encode()) to CoupledEnvironmentReadinessEvidence.
        ("STEP_5J_3A_ENVIRONMENT_EVIDENCE_V1",
         # Include the hexadecimal digest from sha256(repr(identity).encode()) in this tuple.
         sha256(repr(identity).encode()).hexdigest()),
        # Supply frozen_design['freeze'].freeze_id to CoupledEnvironmentReadinessEvidence.
        frozen_design["freeze"].freeze_id,
        # Supply manifests[ScenarioRole.TRAINING].manifest_id to CoupledEnvironmentReadinessEvidence.
        manifests[ScenarioRole.TRAINING].manifest_id,
        # Supply coupling_evidence at 'status' to CoupledEnvironmentReadinessEvidence.
        coupling_evidence["status"], True, 2, True, READY,
        # Store True under 'post_freeze_layer'.
        # Store False under 'frozen_design_mutated'.
        {"post_freeze_layer": True, "frozen_design_mutated": False,
         # Store 0 under 'route_truth_policy_leakage'.
         # Store False under 'reward_changed'.
         "route_truth_policy_leakage": 0, "reward_changed": False,
         # Store False under 'protocol_changed'.
         "protocol_changed": False,
         "physical_authority": "SUMO_PROCESS_TRACI_SPEED_CONTROL"})


# Assess step 5j 3b pilot readiness using the inputs and processing steps below.
# Input profile: the supplied profile.
# Output: return the value selected by the matching return branch below.
# Processing: select branches using the stated conditions.
def assess_step_5j_3b_pilot_readiness(profile):
    # Run this branch when 'status' from profile; use None if absent equals the text
    # 'COUPLED_ENVIRONMENT_PROFILE_COMPLETE' and 'hard_validity_gates_passed' from profile; use None if absent is
    # the same object as True and 'profiling_samples_ppo_eligible' from profile; use None if absent is the same
    # object as False and 'optimizer_instances' from profile; use None if absent equals 0.
    if (profile.get("status") == "COUPLED_ENVIRONMENT_PROFILE_COMPLETE" and
            # Evaluate 'hard_validity_gates_passed' from profile; use None if absent is the same object as True as
            # part of the enclosing expression.
            profile.get("hard_validity_gates_passed") is True and
            # Evaluate 'profiling_samples_ppo_eligible' from profile; use None if absent is the same object as
            # False as part of the enclosing expression.
            profile.get("profiling_samples_ppo_eligible") is False and
            # Evaluate 'optimizer_instances' from profile; use None if absent equals 0 as part of the enclosing
            # expression.
            profile.get("optimizer_instances") == 0):
        # Return the text 'READY_TO_IMPLEMENT_FIRST_CONTROLLED_MAPPO_PILOT' to the caller.
        return "READY_TO_IMPLEMENT_FIRST_CONTROLLED_MAPPO_PILOT"
    # Return the text 'STEP_5J_3A_PROFILE_INCOMPLETE' to the caller.
    return "STEP_5J_3A_PROFILE_INCOMPLETE"


# Gate real behavior-policy implementation on both complete contracts.
# Input profile_path: the supplied profile path.
# Output: the text 'READY_TO_IMPLEMENT_REAL_MAPPO_BEHAVIOR_POLICY' when ready, otherwise the text
# 'STEP_5J_3B_CONFIGURATION_INCOMPLETE'.
def assess_step_5j_3b_behavior_policy_readiness(
        # Declare profile_path as input parameter.
        profile_path="results/coupled_environment_profile.json"):
    """Gate real behavior-policy implementation on both complete contracts."""
    # Import build_mechanical_adam_optimization_contract from .adam_contract for the operations below.
    from .adam_contract import build_mechanical_adam_optimization_contract
    # Import build_mechanical_pilot_architecture_contract from .architecture_contract for the operations below.
    from .architecture_contract import build_mechanical_pilot_architecture_contract

    # Set profile to the decoded data produced by json.loads from the text read from Path(profile_path).
    profile = json.loads(Path(profile_path).read_text(encoding="utf-8"))
    # Set architecture to the result of build_mechanical_pilot_architecture_contract(profile_path).
    architecture = build_mechanical_pilot_architecture_contract(profile_path)
    # Set optimization to the result of build_mechanical_adam_optimization_contract(profile_path).
    optimization = build_mechanical_adam_optimization_contract(profile_path)
    # Set ready to the negation of architecture.unresolved_architecture_fields and the negation of
    # optimization.unresolved_optimizer_fields and optimization.critic_loss_reduction equals the text
    # 'PER_JOINT_DECISION_BATCH_EMPIRICAL_MEAN_SQUARED_ERROR' and architecture.frozen_design_id equals
    # optimization.frozen_design_id and the result of assess_step_5j_3b_pilot_readiness(profile) equals the text
    # 'READY_TO_IMPLEMENT_FIRST_CONTROLLED_MAPPO_PILOT'.
    ready = (
        # Evaluate the negation of architecture.unresolved_architecture_fields and the negation of
        # optimization.unresolved_optimizer_fields and optimization.critic_loss_reduction equals the text
        # 'PER_JOINT_DECISION_BATCH_EMPIRICAL_MEAN_SQUARED_ERROR' and architecture.frozen_design_id equals
        # optimization.frozen_design_id and the result of assess_step_5j_3b_pilot_readiness(profile) equals the
        # text 'READY_TO_IMPLEMENT_FIRST_CONTROLLED_MAPPO_PILOT' as part of the enclosing expression.
        not architecture.unresolved_architecture_fields
        # Evaluate the negation of optimization.unresolved_optimizer_fields as part of the enclosing expression.
        and not optimization.unresolved_optimizer_fields
        # Evaluate optimization.critic_loss_reduction equals the text
        # 'PER_JOINT_DECISION_BATCH_EMPIRICAL_MEAN_SQUARED_ERROR' as part of the enclosing expression.
        and optimization.critic_loss_reduction ==
        "PER_JOINT_DECISION_BATCH_EMPIRICAL_MEAN_SQUARED_ERROR"
        # Evaluate architecture.frozen_design_id equals optimization.frozen_design_id as part of the enclosing
        # expression.
        and architecture.frozen_design_id == optimization.frozen_design_id
        # Evaluate the result of assess_step_5j_3b_pilot_readiness(profile) equals the text
        # 'READY_TO_IMPLEMENT_FIRST_CONTROLLED_MAPPO_PILOT' as part of the enclosing expression.
        and assess_step_5j_3b_pilot_readiness(profile) ==
        "READY_TO_IMPLEMENT_FIRST_CONTROLLED_MAPPO_PILOT"
    )
    # Return the text 'READY_TO_IMPLEMENT_REAL_MAPPO_BEHAVIOR_POLICY' when ready, otherwise the text
    # 'STEP_5J_3B_CONFIGURATION_INCOMPLETE' to the caller.
    return ("READY_TO_IMPLEMENT_REAL_MAPPO_BEHAVIOR_POLICY" if ready else
            "STEP_5J_3B_CONFIGURATION_INCOMPLETE")
