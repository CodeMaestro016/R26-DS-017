"""Derive an inference-only demonstration policy from canonical evidence."""

# Import replace from dataclasses for the operations below.
from dataclasses import replace
# Import hashlib for use in this module.
import hashlib
# Import os for use in this module.
import os
# Import Path from pathlib for the operations below.
from pathlib import Path

# Import torch for use in this module.
import torch

# Import build_mechanical_mappo_behavior_policy_bundle from .mappo_provider for the operations below.
from .mappo_provider import build_mechanical_mappo_behavior_policy_bundle
# Import parameter_hash from .rollout for the operations below.
from .rollout import parameter_hash


# Set SOURCE_CHECKPOINT to the result of Path(the text 'results/mappo_extended_resume/replication_0_state_2.pt').
SOURCE_CHECKPOINT = Path(
    "results/mappo_extended_resume/replication_0_state_2.pt")
# Set DEMO_POLICY_PATH to the result of Path(the text 'results/mappo_demo_policy.pt').
DEMO_POLICY_PATH = Path("results/mappo_demo_policy.pt")
# Set SELECTION_RULE to the text 'FIRST_CANONICAL_REPLICATION_TERMINAL_STATE_OF_COMPLETED_EVIDEN...'.
SELECTION_RULE = (
    "FIRST_CANONICAL_REPLICATION_TERMINAL_STATE_OF_COMPLETED_EVIDENCE_TRANCHE")
# Set SAMPLING_IDENTITY to a tuple containing the text 'STEP_5K_1_DEMONSTRATION_ACTION_SAMPLING', 0, 2.
SAMPLING_IDENTITY = (
    # Supply the text 'STEP_5K_1_DEMONSTRATION_ACTION_SAMPLING' to the enclosing expression.
    "STEP_5K_1_DEMONSTRATION_ACTION_SAMPLING", 0, 2)


# File sha256 using the inputs and processing steps below.
# Input path: the path or path object supplied by the caller.
# Output: the hexadecimal digest from hashlib.sha256(Path(path).read_bytes()).
def file_sha256(path):
    # Return the hexadecimal digest from hashlib.sha256(Path(path).read_bytes()) to the caller.
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# Create demo policy using the inputs and processing steps below.
# Input source_path: the supplied source path.
# Input output_path: the supplied output path.
# Output: payload.
# Processing: select branches using the stated conditions.
def create_demo_policy(source_path=SOURCE_CHECKPOINT,
                       # Declare output_path as input parameter.
                       output_path=DEMO_POLICY_PATH):
    # Set (source_path, output_path) to a tuple containing the result of Path(source_path), the result of
    # Path(output_path).
    source_path, output_path = Path(source_path), Path(output_path)
    # Set source_bytes_hash to the result of file_sha256(source_path).
    source_bytes_hash = file_sha256(source_path)
    # Set source to the decoded data produced by torch.load from source_path.
    source = torch.load(source_path, map_location="cpu", weights_only=False)
    # Run this branch when 'checkpoint_type' from source; use None if absent differs from the text
    # 'EVIDENCE_RESUME_CHECKPOINT_ONLY' or 'policy_state_index' from source; use None if absent differs from 2 or
    # source.get('replication_identity', (None, None, None)) at -1 differs from 0 or 'best_model' from source; use
    # None if absent is a different object from False or 'final_model' from source; use None if absent is a
    # different object from False or 'selected_model' from source; use None if absent is a different object from
    # False or 'selection_eligible' from source; use None if absent is a different object from False.
    if (source.get("checkpoint_type") != "EVIDENCE_RESUME_CHECKPOINT_ONLY" or
            # Evaluate 'policy_state_index' from source; use None if absent differs from 2 as part of the
            # enclosing expression.
            source.get("policy_state_index") != 2 or
            # Evaluate source.get('replication_identity', (None, None, None)) at -1 differs from 0 as part of the
            # enclosing expression.
            source.get("replication_identity", (None, None, None))[-1] != 0 or
            # Evaluate 'best_model' from source; use None if absent is a different object from False as part of
            # the enclosing expression.
            source.get("best_model") is not False or
            # Evaluate 'final_model' from source; use None if absent is a different object from False as part of
            # the enclosing expression.
            source.get("final_model") is not False or
            # Evaluate 'selected_model' from source; use None if absent is a different object from False as part
            # of the enclosing expression.
            source.get("selected_model") is not False or
            # Evaluate 'selection_eligible' from source; use None if absent is a different object from False as
            # part of the enclosing expression.
            source.get("selection_eligible") is not False):
        # Raise ValueError with the text 'DEMONSTRATION_SOURCE_CHECKPOINT_INVALID' to stop this execution path.
        raise ValueError("DEMONSTRATION_SOURCE_CHECKPOINT_INVALID")
    # Set bundle to the result of build_mechanical_mappo_behavior_policy_bundle().
    bundle = build_mechanical_mappo_behavior_policy_bundle(
        # Supply component_seed_identity as a tuple containing the text 'STEP_5K_1_ARCHITECTURE_RECONSTRUCTION'.
        component_seed_identity=("STEP_5K_1_ARCHITECTURE_RECONSTRUCTION",))
    # Call bundle.gnn.load_state_dict with the supplied arguments.
    bundle.gnn.load_state_dict(source["gnn_state_dict"])
    # Call bundle.proposer_actor.load_state_dict with the supplied arguments.
    bundle.proposer_actor.load_state_dict(source["proposer_state_dict"])
    # Call bundle.responder_actor.load_state_dict with the supplied arguments.
    bundle.responder_actor.load_state_dict(source["responder_state_dict"])
    # Set hashes to a dictionary containing gnn, proposer, responder.
    hashes = {
        # Store the result of parameter_hash(bundle.gnn) under 'gnn'.
        "gnn": parameter_hash(bundle.gnn),
        # Store the result of parameter_hash(bundle.proposer_actor) under 'proposer'.
        "proposer": parameter_hash(bundle.proposer_actor),
        # Store the result of parameter_hash(bundle.responder_actor) under 'responder'.
        "responder": parameter_hash(bundle.responder_actor)}
    # Set expected to a dictionary containing gnn, proposer, responder.
    expected = {"gnn": source["gnn_hash"],
                # Store source['policy_hashes'] at 'proposer' under 'proposer'.
                "proposer": source["policy_hashes"]["proposer"],
                # Store source['policy_hashes'] at 'responder' under 'responder'.
                "responder": source["policy_hashes"]["responder"]}
    # Run this branch when hashes differs from expected.
    if hashes != expected:
        # Raise ValueError with the text 'DEMONSTRATION_SOURCE_PARAMETER_HASH_MISMATCH' to stop this execution
        # path.
        raise ValueError("DEMONSTRATION_SOURCE_PARAMETER_HASH_MISMATCH")
    # Set identity_fields to a tuple containing the text 'RESEARCH_PROTOTYPE_DEMONSTRATION_POLICY_V1', source at
    # 'checkpoint_identity', a tuple built from...
    identity_fields = (
        "RESEARCH_PROTOTYPE_DEMONSTRATION_POLICY_V1",
        # Include source at 'checkpoint_identity' in this tuple.
        source["checkpoint_identity"], tuple(sorted(hashes.items())),
        # Include SAMPLING_IDENTITY in this tuple.
        SELECTION_RULE, SAMPLING_IDENTITY)
    # Set demo_identity to a tuple containing identity_fields at 0, the hexadecimal digest from
    # hashlib.sha256(repr(identity_fields).encode()).
    demo_identity = (
        # Include identity_fields at 0 in this tuple.
        identity_fields[0],
        # Include the hexadecimal digest from hashlib.sha256(repr(identity_fields).encode()) in this tuple.
        hashlib.sha256(repr(identity_fields).encode()).hexdigest())
    # Set payload to a dictionary containing checkpoint_type, demo_policy_identity, source_checkpoint,
    # source_checkpoint_sha256,...
    payload = {
        "checkpoint_type": "RESEARCH_PROTOTYPE_DEMONSTRATION_POLICY",
        # Store demo_identity under 'demo_policy_identity'.
        "demo_policy_identity": demo_identity,
        # Store the result of str(source_path).replace(the text '\\', the text '/') under 'source_checkpoint'.
        "source_checkpoint": str(source_path).replace("\\", "/"),
        # Store source_bytes_hash under 'source_checkpoint_sha256'.
        "source_checkpoint_sha256": source_bytes_hash,
        # Store 0 under 'source_replication'.
        "source_replication": 0,
        # Store 2 under 'source_policy_state'.
        "source_policy_state": 2,
        # Store source at 'checkpoint_identity' under 'source_checkpoint_identity'.
        "source_checkpoint_identity": source["checkpoint_identity"],
        # Store SELECTION_RULE under 'demo_checkpoint_selection_rule'.
        "demo_checkpoint_selection_rule": SELECTION_RULE,
        # Store False under 'performance_selected'.
        "performance_selected": False,
        # Store False under 'statistically_selected'.
        "statistically_selected": False,
        # Store False under 'best_model'.
        # Store False under 'final_model'.
        "best_model": False, "final_model": False,
        # Store False under 'optimal_model'.
        # Store False under 'held_out_selected'.
        "optimal_model": False, "held_out_selected": False,
        "purpose": "END_TO_END_RESEARCH_PROTOTYPE_DEMONSTRATION_ONLY",
        # Store a tuple containing the text 'FROZEN_GNN', the text 'PROPOSER_ACTOR', the text 'RESPONDER_ACTOR'
        # under 'decentralized_runtime_components'.
        "decentralized_runtime_components": (
            "FROZEN_GNN", "PROPOSER_ACTOR", "RESPONDER_ACTOR"),
        # Store False under 'centralized_critic_included'.
        "centralized_critic_included": False,
        # Store source at 'gnn_state_dict' under 'gnn_state_dict'.
        "gnn_state_dict": source["gnn_state_dict"],
        # Store source at 'proposer_state_dict' under 'proposer_state_dict'.
        "proposer_state_dict": source["proposer_state_dict"],
        # Store source at 'responder_state_dict' under 'responder_state_dict'.
        "responder_state_dict": source["responder_state_dict"],
        # Store hashes under 'parameter_hashes'.
        "parameter_hashes": hashes,
        # Store SAMPLING_IDENTITY under 'demonstration_action_sampling_seed_identity'.
        "demonstration_action_sampling_seed_identity": SAMPLING_IDENTITY,
        # Store a dictionary containing checkpoint, weights_copied_not_mutated,
        # statistical_model_selection_performed,... under 'provenance'.
        "provenance": {
            # Store the text 'STEP_5K_1' under 'checkpoint'.
            # Store True under 'weights_copied_not_mutated'.
            "checkpoint": "STEP_5K_1", "weights_copied_not_mutated": True,
            # Store False under 'statistical_model_selection_performed'.
            "statistical_model_selection_performed": False,
            # Store False under 'performance_used_to_select_demo_checkpoint'.
            "performance_used_to_select_demo_checkpoint": False}}
    # Create the directory requested by output_path.parent.
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # Set temporary to the result of output_path.with_suffix(the text '.pt.tmp').
    temporary = output_path.with_suffix(".pt.tmp")
    # Call torch.save with the supplied arguments.
    torch.save(payload, temporary)
    # Call os.replace with the supplied arguments.
    os.replace(temporary, output_path)
    # Run this branch when the result of file_sha256(source_path) differs from source_bytes_hash.
    if file_sha256(source_path) != source_bytes_hash:
        # Raise RuntimeError with the text 'ORIGINAL_EVIDENCE_CHECKPOINT_MUTATED' to stop this execution path.
        raise RuntimeError("ORIGINAL_EVIDENCE_CHECKPOINT_MUTATED")
    # Return payload to the caller.
    return payload


# Load demo policy using the inputs and processing steps below.
# Input path: the path or path object supplied by the caller.
# Output: payload.
# Processing: select branches using the stated conditions.
def load_demo_policy(path=DEMO_POLICY_PATH):
    # Set payload to the decoded data produced by torch.load from path.
    payload = torch.load(path, map_location="cpu", weights_only=False)
    # Run this branch when 'checkpoint_type' from payload; use None if absent differs from the text
    # 'RESEARCH_PROTOTYPE_DEMONSTRATION_POLICY' or 'centralized_critic_included' from payload; use None if absent
    # is a different object from False or whether any item is true in a lazy sequence of payload.get(field) is a
    # different object from False for field in a tuple containing 'performance_selected',
    # 'statistically_selected', 'best_model', 'final_model', 'optimal_model',...
    if (payload.get("checkpoint_type") !=
            # Supply the text 'RESEARCH_PROTOTYPE_DEMONSTRATION_POLICY' to the enclosing expression.
            "RESEARCH_PROTOTYPE_DEMONSTRATION_POLICY" or
            # Evaluate 'centralized_critic_included' from payload; use None if absent is a different object from
            # False as part of the enclosing expression.
            payload.get("centralized_critic_included") is not False or
            # Evaluate whether any item is true in a lazy sequence of field from payload; use None if absent is a
            # different object from False for field in a tuple containing the text 'performance_selected', the
            # text 'statistically_selected', the text 'best_model', the text... as part of the enclosing
            # expression.
            any(payload.get(field) is not False for field in (
                "performance_selected", "statistically_selected",
                "best_model", "final_model", "optimal_model",
                "held_out_selected"))):
        # Raise ValueError with the text 'DEMONSTRATION_POLICY_METADATA_INVALID' to stop this execution path.
        raise ValueError("DEMONSTRATION_POLICY_METADATA_INVALID")
    # Return payload to the caller.
    return payload


# Reconstruct demo bundle using the inputs and processing steps below.
# Input payload: the supplied payload.
# Output: a tuple containing the result of replace(bundle), hashes.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def reconstruct_demo_bundle(payload):
    # Set bundle to the result of build_mechanical_mappo_behavior_policy_bundle().
    bundle = build_mechanical_mappo_behavior_policy_bundle(
        # Supply component_seed_identity as a tuple containing the text 'STEP_5K_1_ARCHITECTURE_RECONSTRUCTION'.
        component_seed_identity=("STEP_5K_1_ARCHITECTURE_RECONSTRUCTION",))
    # Call bundle.gnn.load_state_dict with the supplied arguments.
    bundle.gnn.load_state_dict(payload["gnn_state_dict"])
    # Call bundle.proposer_actor.load_state_dict with the supplied arguments.
    bundle.proposer_actor.load_state_dict(payload["proposer_state_dict"])
    # Call bundle.responder_actor.load_state_dict with the supplied arguments.
    bundle.responder_actor.load_state_dict(payload["responder_state_dict"])
    # Iterate over a tuple containing bundle.gnn, bundle.proposer_actor, bundle.responder_actor, binding each item
    # to module.
    for module in (bundle.gnn, bundle.proposer_actor, bundle.responder_actor):
        # Call module.eval with the supplied arguments.
        module.eval()
        # Iterate over the result of module.parameters(), binding each item to parameter.
        for parameter in module.parameters():
            # Call parameter.requires_grad_ with the supplied arguments.
            parameter.requires_grad_(False)
    # Set hashes to a dictionary containing gnn, proposer, responder.
    hashes = {"gnn": parameter_hash(bundle.gnn),
              # Store the result of parameter_hash(bundle.proposer_actor) under 'proposer'.
              "proposer": parameter_hash(bundle.proposer_actor),
              # Store the result of parameter_hash(bundle.responder_actor) under 'responder'.
              "responder": parameter_hash(bundle.responder_actor)}
    # Run this branch when hashes differs from payload at 'parameter_hashes'.
    if hashes != payload["parameter_hashes"]:
        # Raise ValueError with the text 'DEMONSTRATION_POLICY_PARAMETER_HASH_MISMATCH' to stop this execution
        # path.
        raise ValueError("DEMONSTRATION_POLICY_PARAMETER_HASH_MISMATCH")
    # The critic is deliberately unavailable to the runtime provider.
    # Return a tuple containing the result of replace(bundle), hashes to the caller.
    return replace(bundle, centralized_critic=None), hashes
