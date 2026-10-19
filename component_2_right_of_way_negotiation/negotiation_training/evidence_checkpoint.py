"""Atomic, non-selective resume checkpoints for long MAPPO evidence runs."""

import hashlib
import os
from pathlib import Path

import torch

from .controlled_pilot import _current_hashes


CHECKPOINT_DIRECTORY = Path("results/mappo_extended_resume")


def _checkpoint_id(replication_identity, state_index, hashes):
    value = ("EXTENDED_EVIDENCE_RESUME_CHECKPOINT_V1",
             replication_identity, state_index, tuple(sorted(hashes.items())))
    return (value[0], hashlib.sha256(repr(value).encode()).hexdigest())


def save_evidence_resume_checkpoint(*, bundle, replication_identity,
                                    state_index, frozen_design_identity,
                                    architecture_contract_identity,
                                    optimization_contract_identity,
                                    provisional_configuration_identity,
                                    completed_rollout_payload,
                                    completed_rollout_metrics,
                                    sampling_identity, progress_cursor,
                                    update_diagnostics,
                                    directory=CHECKPOINT_DIRECTORY):
    hashes = _current_hashes(bundle)
    checkpoint_id = _checkpoint_id(replication_identity, state_index, hashes)
    payload = {
        "checkpoint_identity": checkpoint_id,
        "checkpoint_type": "EVIDENCE_RESUME_CHECKPOINT_ONLY",
        "replication_identity": replication_identity,
        "policy_state_index": state_index,
        "frozen_design_identity": frozen_design_identity,
        "architecture_contract_identity": architecture_contract_identity,
        "optimization_contract_identity": optimization_contract_identity,
        "provisional_configuration_identity": provisional_configuration_identity,
        "proposer_state_dict": bundle.proposer_actor.state_dict(),
        "responder_state_dict": bundle.responder_actor.state_dict(),
        "critic_state_dict": bundle.centralized_critic.state_dict(),
        "gnn_state_dict": bundle.gnn.state_dict(),
        "policy_hashes": {"proposer": hashes["proposer"],
                          "responder": hashes["responder"]},
        "critic_hash": hashes["critic"],
        "gnn_hash": hashes["gnn"],
        "completed_rollout_artifact_identity":
            completed_rollout_metrics["pass_identity"],
        "completed_rollout_payload": completed_rollout_payload,
        "completed_rollout_metrics": completed_rollout_metrics,
        "sampling_identity": sampling_identity,
        "progress_cursor": progress_cursor,
        "update_diagnostics": update_diagnostics,
        "best_model": False, "final_model": False,
        "selected_model": False, "selection_eligible": False,
        "purpose": "LONG_RUNNING_EXPERIMENT_RESUME_ONLY",
        "provenance": {
            "checkpoint": "STEP_5J_3C_2B",
            "ranking_performed": False,
            "model_selection_performed": False}}
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"replication_{replication_identity[-1]}_state_{state_index}.pt"
    temporary = path.with_suffix(".pt.tmp")
    torch.save(payload, temporary)
    os.replace(temporary, path)
    return path, payload


def restore_evidence_resume_checkpoint(path, bundle):
    payload = torch.load(path, map_location="cpu", weights_only=False)
    if payload.get("checkpoint_type") != "EVIDENCE_RESUME_CHECKPOINT_ONLY":
        raise ValueError("INVALID_EVIDENCE_RESUME_CHECKPOINT_TYPE")
    if any(payload.get(field) is not False for field in
           ("best_model", "final_model", "selected_model",
            "selection_eligible")):
        raise ValueError("RESUME_CHECKPOINT_SELECTION_FLAG_FORBIDDEN")
    if payload.get("purpose") != "LONG_RUNNING_EXPERIMENT_RESUME_ONLY":
        raise ValueError("INVALID_RESUME_CHECKPOINT_PURPOSE")
    bundle.gnn.load_state_dict(payload["gnn_state_dict"])
    bundle.proposer_actor.load_state_dict(payload["proposer_state_dict"])
    bundle.responder_actor.load_state_dict(payload["responder_state_dict"])
    bundle.centralized_critic.load_state_dict(payload["critic_state_dict"])
    actual = _current_hashes(bundle)
    expected = {"gnn": payload["gnn_hash"],
                "proposer": payload["policy_hashes"]["proposer"],
                "responder": payload["policy_hashes"]["responder"],
                "critic": payload["critic_hash"]}
    if actual != expected:
        raise ValueError("RESTORED_PARAMETER_IDENTITY_MISMATCH")
    return payload
