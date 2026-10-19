"""Derive an inference-only demonstration policy from canonical evidence."""

from dataclasses import replace
import hashlib
import os
from pathlib import Path

import torch

from .mappo_provider import build_mechanical_mappo_behavior_policy_bundle
from .rollout import parameter_hash


SOURCE_CHECKPOINT = Path(
    "results/mappo_extended_resume/replication_0_state_2.pt")
DEMO_POLICY_PATH = Path("results/mappo_demo_policy.pt")
SELECTION_RULE = (
    "FIRST_CANONICAL_REPLICATION_TERMINAL_STATE_OF_COMPLETED_EVIDENCE_TRANCHE")
SAMPLING_IDENTITY = (
    "STEP_5K_1_DEMONSTRATION_ACTION_SAMPLING", 0, 2)


def file_sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def create_demo_policy(source_path=SOURCE_CHECKPOINT,
                       output_path=DEMO_POLICY_PATH):
    source_path, output_path = Path(source_path), Path(output_path)
    source_bytes_hash = file_sha256(source_path)
    source = torch.load(source_path, map_location="cpu", weights_only=False)
    if (source.get("checkpoint_type") != "EVIDENCE_RESUME_CHECKPOINT_ONLY" or
            source.get("policy_state_index") != 2 or
            source.get("replication_identity", (None, None, None))[-1] != 0 or
            source.get("best_model") is not False or
            source.get("final_model") is not False or
            source.get("selected_model") is not False or
            source.get("selection_eligible") is not False):
        raise ValueError("DEMONSTRATION_SOURCE_CHECKPOINT_INVALID")
    bundle = build_mechanical_mappo_behavior_policy_bundle(
        component_seed_identity=("STEP_5K_1_ARCHITECTURE_RECONSTRUCTION",))
    bundle.gnn.load_state_dict(source["gnn_state_dict"])
    bundle.proposer_actor.load_state_dict(source["proposer_state_dict"])
    bundle.responder_actor.load_state_dict(source["responder_state_dict"])
    hashes = {
        "gnn": parameter_hash(bundle.gnn),
        "proposer": parameter_hash(bundle.proposer_actor),
        "responder": parameter_hash(bundle.responder_actor)}
    expected = {"gnn": source["gnn_hash"],
                "proposer": source["policy_hashes"]["proposer"],
                "responder": source["policy_hashes"]["responder"]}
    if hashes != expected:
        raise ValueError("DEMONSTRATION_SOURCE_PARAMETER_HASH_MISMATCH")
    identity_fields = (
        "RESEARCH_PROTOTYPE_DEMONSTRATION_POLICY_V1",
        source["checkpoint_identity"], tuple(sorted(hashes.items())),
        SELECTION_RULE, SAMPLING_IDENTITY)
    demo_identity = (
        identity_fields[0],
        hashlib.sha256(repr(identity_fields).encode()).hexdigest())
    payload = {
        "checkpoint_type": "RESEARCH_PROTOTYPE_DEMONSTRATION_POLICY",
        "demo_policy_identity": demo_identity,
        "source_checkpoint": str(source_path).replace("\\", "/"),
        "source_checkpoint_sha256": source_bytes_hash,
        "source_replication": 0,
        "source_policy_state": 2,
        "source_checkpoint_identity": source["checkpoint_identity"],
        "demo_checkpoint_selection_rule": SELECTION_RULE,
        "performance_selected": False,
        "statistically_selected": False,
        "best_model": False, "final_model": False,
        "optimal_model": False, "held_out_selected": False,
        "purpose": "END_TO_END_RESEARCH_PROTOTYPE_DEMONSTRATION_ONLY",
        "decentralized_runtime_components": (
            "FROZEN_GNN", "PROPOSER_ACTOR", "RESPONDER_ACTOR"),
        "centralized_critic_included": False,
        "gnn_state_dict": source["gnn_state_dict"],
        "proposer_state_dict": source["proposer_state_dict"],
        "responder_state_dict": source["responder_state_dict"],
        "parameter_hashes": hashes,
        "demonstration_action_sampling_seed_identity": SAMPLING_IDENTITY,
        "provenance": {
            "checkpoint": "STEP_5K_1", "weights_copied_not_mutated": True,
            "statistical_model_selection_performed": False,
            "performance_used_to_select_demo_checkpoint": False}}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(".pt.tmp")
    torch.save(payload, temporary)
    os.replace(temporary, output_path)
    if file_sha256(source_path) != source_bytes_hash:
        raise RuntimeError("ORIGINAL_EVIDENCE_CHECKPOINT_MUTATED")
    return payload


def load_demo_policy(path=DEMO_POLICY_PATH):
    payload = torch.load(path, map_location="cpu", weights_only=False)
    if (payload.get("checkpoint_type") !=
            "RESEARCH_PROTOTYPE_DEMONSTRATION_POLICY" or
            payload.get("centralized_critic_included") is not False or
            any(payload.get(field) is not False for field in (
                "performance_selected", "statistically_selected",
                "best_model", "final_model", "optimal_model",
                "held_out_selected"))):
        raise ValueError("DEMONSTRATION_POLICY_METADATA_INVALID")
    return payload


def reconstruct_demo_bundle(payload):
    bundle = build_mechanical_mappo_behavior_policy_bundle(
        component_seed_identity=("STEP_5K_1_ARCHITECTURE_RECONSTRUCTION",))
    bundle.gnn.load_state_dict(payload["gnn_state_dict"])
    bundle.proposer_actor.load_state_dict(payload["proposer_state_dict"])
    bundle.responder_actor.load_state_dict(payload["responder_state_dict"])
    for module in (bundle.gnn, bundle.proposer_actor, bundle.responder_actor):
        module.eval()
        for parameter in module.parameters():
            parameter.requires_grad_(False)
    hashes = {"gnn": parameter_hash(bundle.gnn),
              "proposer": parameter_hash(bundle.proposer_actor),
              "responder": parameter_hash(bundle.responder_actor)}
    if hashes != payload["parameter_hashes"]:
        raise ValueError("DEMONSTRATION_POLICY_PARAMETER_HASH_MISMATCH")
    # The critic is deliberately unavailable to the runtime provider.
    return replace(bundle, centralized_critic=None), hashes
