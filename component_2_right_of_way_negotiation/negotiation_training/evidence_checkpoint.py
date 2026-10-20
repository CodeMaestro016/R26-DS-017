"""Atomic, non-selective resume checkpoints for long MAPPO evidence runs."""

# Import hashlib for use in this module.
import hashlib
# Import os for use in this module.
import os
# Import Path from pathlib for the operations below.
from pathlib import Path

# Import torch for use in this module.
import torch

# Import _current_hashes from .controlled_pilot for the operations below.
from .controlled_pilot import _current_hashes


# Set CHECKPOINT_DIRECTORY to the result of Path(the text 'results/mappo_extended_resume').
CHECKPOINT_DIRECTORY = Path("results/mappo_extended_resume")


# Checkpoint id using the inputs and processing steps below.
# Input replication_identity: the supplied replication identity.
# Input state_index: the supplied state index.
# Input hashes: the supplied hashes.
# Output: a tuple containing value at 0, the hexadecimal digest from hashlib.sha256(repr(value).encode()).
def _checkpoint_id(replication_identity, state_index, hashes):
    # Set value to a tuple containing the text 'EXTENDED_EVIDENCE_RESUME_CHECKPOINT_V1', replication_identity,
    # state_index, a tuple built from...
    value = ("EXTENDED_EVIDENCE_RESUME_CHECKPOINT_V1",
             # Include a tuple built from the sorted values from key/value pairs from hashes in this tuple.
             replication_identity, state_index, tuple(sorted(hashes.items())))
    # Return a tuple containing value at 0, the hexadecimal digest from hashlib.sha256(repr(value).encode()) to
    # the caller.
    return (value[0], hashlib.sha256(repr(value).encode()).hexdigest())


# Save evidence resume checkpoint using the inputs and processing steps below.
# Input bundle: the supplied bundle.
# Input replication_identity: the supplied replication identity.
# Input state_index: the supplied state index.
# Input frozen_design_identity: the supplied frozen design identity.
# Input architecture_contract_identity: the supplied architecture contract identity.
# Input optimization_contract_identity: the supplied optimization contract identity.
# Input provisional_configuration_identity: the supplied provisional configuration identity.
# Input completed_rollout_payload: the supplied completed rollout payload.
# Input completed_rollout_metrics: the supplied completed rollout metrics.
# Input sampling_identity: the supplied sampling identity.
# Input progress_cursor: the supplied progress cursor.
# Input update_diagnostics: the supplied update diagnostics.
# Input directory: the supplied directory.
# Output: a tuple containing path, payload.
def save_evidence_resume_checkpoint(*, bundle, replication_identity,
                                    # Declare state_index, frozen_design_identity as input parameters.
                                    state_index, frozen_design_identity,
                                    # Declare architecture_contract_identity as input parameter.
                                    architecture_contract_identity,
                                    # Declare optimization_contract_identity as input parameter.
                                    optimization_contract_identity,
                                    # Declare provisional_configuration_identity as input parameter.
                                    provisional_configuration_identity,
                                    # Declare completed_rollout_payload as input parameter.
                                    completed_rollout_payload,
                                    # Declare completed_rollout_metrics as input parameter.
                                    completed_rollout_metrics,
                                    # Declare sampling_identity, progress_cursor as input parameters.
                                    sampling_identity, progress_cursor,
                                    # Declare update_diagnostics as input parameter.
                                    update_diagnostics,
                                    # Declare directory as input parameter.
                                    directory=CHECKPOINT_DIRECTORY):
    # Set hashes to the result of _current_hashes(bundle).
    hashes = _current_hashes(bundle)
    # Set checkpoint_id to the result of _checkpoint_id(replication_identity, state_index, hashes).
    checkpoint_id = _checkpoint_id(replication_identity, state_index, hashes)
    # Set payload to a dictionary containing checkpoint_identity, checkpoint_type, replication_identity,
    # policy_state_index,...
    payload = {
        # Store checkpoint_id under 'checkpoint_identity'.
        "checkpoint_identity": checkpoint_id,
        "checkpoint_type": "EVIDENCE_RESUME_CHECKPOINT_ONLY",
        # Store replication_identity under 'replication_identity'.
        "replication_identity": replication_identity,
        # Store state_index under 'policy_state_index'.
        "policy_state_index": state_index,
        # Store frozen_design_identity under 'frozen_design_identity'.
        "frozen_design_identity": frozen_design_identity,
        # Store architecture_contract_identity under 'architecture_contract_identity'.
        "architecture_contract_identity": architecture_contract_identity,
        # Store optimization_contract_identity under 'optimization_contract_identity'.
        "optimization_contract_identity": optimization_contract_identity,
        # Store provisional_configuration_identity under 'provisional_configuration_identity'.
        "provisional_configuration_identity": provisional_configuration_identity,
        # Store the result of bundle.proposer_actor.state_dict() under 'proposer_state_dict'.
        "proposer_state_dict": bundle.proposer_actor.state_dict(),
        # Store the result of bundle.responder_actor.state_dict() under 'responder_state_dict'.
        "responder_state_dict": bundle.responder_actor.state_dict(),
        # Store the result of bundle.centralized_critic.state_dict() under 'critic_state_dict'.
        "critic_state_dict": bundle.centralized_critic.state_dict(),
        # Store the result of bundle.gnn.state_dict() under 'gnn_state_dict'.
        "gnn_state_dict": bundle.gnn.state_dict(),
        # Store a dictionary containing proposer, responder under 'policy_hashes'.
        # Store hashes at 'proposer' under 'proposer'.
        "policy_hashes": {"proposer": hashes["proposer"],
                          # Store hashes at 'responder' under 'responder'.
                          "responder": hashes["responder"]},
        # Store hashes at 'critic' under 'critic_hash'.
        "critic_hash": hashes["critic"],
        # Store hashes at 'gnn' under 'gnn_hash'.
        "gnn_hash": hashes["gnn"],
        "completed_rollout_artifact_identity":
            # Evaluate completed_rollout_metrics at 'pass_identity' as part of the enclosing expression.
            completed_rollout_metrics["pass_identity"],
        # Store completed_rollout_payload under 'completed_rollout_payload'.
        "completed_rollout_payload": completed_rollout_payload,
        # Store completed_rollout_metrics under 'completed_rollout_metrics'.
        "completed_rollout_metrics": completed_rollout_metrics,
        # Store sampling_identity under 'sampling_identity'.
        "sampling_identity": sampling_identity,
        # Store progress_cursor under 'progress_cursor'.
        "progress_cursor": progress_cursor,
        # Store update_diagnostics under 'update_diagnostics'.
        "update_diagnostics": update_diagnostics,
        # Store False under 'best_model'.
        # Store False under 'final_model'.
        "best_model": False, "final_model": False,
        # Store False under 'selected_model'.
        # Store False under 'selection_eligible'.
        "selected_model": False, "selection_eligible": False,
        "purpose": "LONG_RUNNING_EXPERIMENT_RESUME_ONLY",
        # Store a dictionary containing checkpoint, ranking_performed, model_selection_performed under
        # 'provenance'.
        "provenance": {
            "checkpoint": "STEP_5J_3C_2B",
            # Store False under 'ranking_performed'.
            "ranking_performed": False,
            # Store False under 'model_selection_performed'.
            "model_selection_performed": False}}
    # Set directory to the result of Path(directory).
    directory = Path(directory)
    # Create the directory requested by directory.
    directory.mkdir(parents=True, exist_ok=True)
    # Set path to directory divided by formatted text built from the embedded values.
    path = directory / f"replication_{replication_identity[-1]}_state_{state_index}.pt"
    # Set temporary to the result of path.with_suffix(the text '.pt.tmp').
    temporary = path.with_suffix(".pt.tmp")
    # Call torch.save with the supplied arguments.
    torch.save(payload, temporary)
    # Call os.replace with the supplied arguments.
    os.replace(temporary, path)
    # Return a tuple containing path, payload to the caller.
    return path, payload


# Restore evidence resume checkpoint using the inputs and processing steps below.
# Input path: the path or path object supplied by the caller.
# Input bundle: the supplied bundle.
# Output: payload.
# Processing: select branches using the stated conditions.
def restore_evidence_resume_checkpoint(path, bundle):
    # Set payload to the decoded data produced by torch.load from path.
    payload = torch.load(path, map_location="cpu", weights_only=False)
    # Run this branch when 'checkpoint_type' from payload; use None if absent differs from the text
    # 'EVIDENCE_RESUME_CHECKPOINT_ONLY'.
    if payload.get("checkpoint_type") != "EVIDENCE_RESUME_CHECKPOINT_ONLY":
        # Raise ValueError with the text 'INVALID_EVIDENCE_RESUME_CHECKPOINT_TYPE' to stop this execution path.
        raise ValueError("INVALID_EVIDENCE_RESUME_CHECKPOINT_TYPE")
    # Run this branch when whether any item is true in a lazy sequence of field from payload; use None if absent
    # is a different object from False for field in a tuple containing the text 'best_model', the text
    # 'final_model', the text 'selected_model', the text 'selection_eligible'.
    if any(payload.get(field) is not False for field in
           # Evaluate a tuple containing the text 'best_model', the text 'final_model', the text 'selected_model',
           # the text 'selection_eligible' as part of the enclosing expression.
           ("best_model", "final_model", "selected_model",
            "selection_eligible")):
        # Raise ValueError with the text 'RESUME_CHECKPOINT_SELECTION_FLAG_FORBIDDEN' to stop this execution path.
        raise ValueError("RESUME_CHECKPOINT_SELECTION_FLAG_FORBIDDEN")
    # Run this branch when 'purpose' from payload; use None if absent differs from the text
    # 'LONG_RUNNING_EXPERIMENT_RESUME_ONLY'.
    if payload.get("purpose") != "LONG_RUNNING_EXPERIMENT_RESUME_ONLY":
        # Raise ValueError with the text 'INVALID_RESUME_CHECKPOINT_PURPOSE' to stop this execution path.
        raise ValueError("INVALID_RESUME_CHECKPOINT_PURPOSE")
    # Call bundle.gnn.load_state_dict with the supplied arguments.
    bundle.gnn.load_state_dict(payload["gnn_state_dict"])
    # Call bundle.proposer_actor.load_state_dict with the supplied arguments.
    bundle.proposer_actor.load_state_dict(payload["proposer_state_dict"])
    # Call bundle.responder_actor.load_state_dict with the supplied arguments.
    bundle.responder_actor.load_state_dict(payload["responder_state_dict"])
    # Call bundle.centralized_critic.load_state_dict with the supplied arguments.
    bundle.centralized_critic.load_state_dict(payload["critic_state_dict"])
    # Set actual to the result of _current_hashes(bundle).
    actual = _current_hashes(bundle)
    # Set expected to a dictionary containing gnn, proposer, responder, critic.
    expected = {"gnn": payload["gnn_hash"],
                # Store payload['policy_hashes'] at 'proposer' under 'proposer'.
                "proposer": payload["policy_hashes"]["proposer"],
                # Store payload['policy_hashes'] at 'responder' under 'responder'.
                "responder": payload["policy_hashes"]["responder"],
                # Store payload at 'critic_hash' under 'critic'.
                "critic": payload["critic_hash"]}
    # Run this branch when actual differs from expected.
    if actual != expected:
        # Raise ValueError with the text 'RESTORED_PARAMETER_IDENTITY_MISMATCH' to stop this execution path.
        raise ValueError("RESTORED_PARAMETER_IDENTITY_MISMATCH")
    # Return payload to the caller.
    return payload
