"""Bounded V2 MAPPO validation selection and matched baseline experiment."""

# Import dataclass, replace from dataclasses for the operations below.
from dataclasses import dataclass, replace
# Import datetime, timezone from datetime for the operations below.
from datetime import datetime, timezone
# Import csv for use in this module.
import csv
# Import hashlib for use in this module.
import hashlib
# Import json for use in this module.
import json
# Import math for use in this module.
import math
# Import os for use in this module.
import os
# Import Path from pathlib for the operations below.
from pathlib import Path
# Import shutil for use in this module.
import shutil
# Import random for use in this module.
import random
# Import mean, median, pstdev from statistics for the operations below.
from statistics import mean, median, pstdev
# Import perf_counter from time for the operations below.
from time import perf_counter

# Import torch for use in this module.
import torch

# Import ScenarioRole, build_design from experimentation for the operations below.
from experimentation import ScenarioRole, build_design
# Import PhysicalReplayError, _specification from negotiation_execution.replay for the operations below.
from negotiation_execution.replay import PhysicalReplayError, _specification
# Import select_demo_scenarios from run_research_demo for the operations below.
from run_research_demo import select_demo_scenarios

# Import build_mechanical_adam_optimization_contract from .adam_contract for the operations below.
from .adam_contract import build_mechanical_adam_optimization_contract
# Import build_mechanical_pilot_architecture_contract from .architecture_contract for the operations below.
from .architecture_contract import build_mechanical_pilot_architecture_contract
# Import serializable from .behavior_rollout for the operations below.
from .behavior_rollout import serializable
# Import _current_hashes, _identity, atomic_write_json, collect_controlled_training_pass from .controlled_pilot
# for the operations below.
from .controlled_pilot import (
    _current_hashes, _identity, atomic_write_json,
    collect_controlled_training_pass,
)
# Import CoupledNegotiationTrainingEnvironment from .environment for the operations below.
from .environment import CoupledNegotiationTrainingEnvironment
# Import MAPPOBehaviorActionProvider, build_mechanical_mappo_behavior_policy_bundle from .mappo_provider for the
# operations below.
from .mappo_provider import (
    MAPPOBehaviorActionProvider, build_mechanical_mappo_behavior_policy_bundle,
)
# Import build_mechanical_pilot_configuration_audit from .optimizer_contract for the operations below.
from .optimizer_contract import build_mechanical_pilot_configuration_audit
# Import MechanicalMAPPOTrainer from .ppo_trainer for the operations below.
from .ppo_trainer import MechanicalMAPPOTrainer
# Import MAPPOBehaviorRolloutIdentity, parameter_hash from .rollout for the operations below.
from .rollout import MAPPOBehaviorRolloutIdentity, parameter_hash


# Set OUTPUT_ROOT to the result of Path(the text 'results/final_mappo_selection_v2').
OUTPUT_ROOT = Path("results/final_mappo_selection_v2")
# Set PROTOCOL_ID to the text 'FINAL_MAPPO_SELECTION_PROTOCOL_V2'.
PROTOCOL_ID = "FINAL_MAPPO_SELECTION_PROTOCOL_V2"
# Set REPLICATION_COUNT to 3.
REPLICATION_COUNT = 3
# Set UPDATE_HORIZON to 2.
UPDATE_HORIZON = 2
# Set CANDIDATE_EPOCHS to a dictionary containing E5, E10, E15.
CANDIDATE_EPOCHS = {"E5": 5, "E10": 10, "E15": 15}
# Set REFERENCE_CANDIDATE to the text 'E5'.
REFERENCE_CANDIDATE = "E5"
# Set BOOTSTRAP_SEED to 260826.
BOOTSTRAP_SEED = 260826
# Set BOOTSTRAP_RESAMPLES to 2000.
BOOTSTRAP_RESAMPLES = 2000


# Hash using the inputs and processing steps below.
# Input value: the supplied value.
# Output: the result of hashlib.sha256(json.dumps(serializable(value), sort_keys=True, separators=(',',...().
def _hash(value):
    # Return the result of hashlib.sha256(json.dumps(serializable(value), sort_keys=True, separators=(',',...() to
    # the caller.
    return hashlib.sha256(json.dumps(
        # Supply sort_keys as True.
        # Supply separators as a tuple containing the text ',', the text ':'.
        serializable(value), sort_keys=True, separators=(",", ":")
    ).encode()).hexdigest()


# File sha256 using the inputs and processing steps below.
# Input path: the path or path object supplied by the caller.
# Output: the hexadecimal digest from hashlib.sha256(Path(path).read_bytes()).
def file_sha256(path):
    # Return the hexadecimal digest from hashlib.sha256(Path(path).read_bytes()) to the caller.
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# Atomic torch save using the inputs and processing steps below.
# Input payload: the supplied payload.
# Input path: the path or path object supplied by the caller.
# Output: no explicit value; normal completion returns None.
def atomic_torch_save(payload, path):
    # Set path to the result of Path(path).
    # Create the directory requested by path.parent.
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    # Set temporary to the result of path.with_suffix(path.suffix plus the text '.tmp').
    temporary = path.with_suffix(path.suffix + ".tmp")
    # Call torch.save with the supplied arguments.
    # Call os.replace with the supplied arguments.
    torch.save(payload, temporary); os.replace(temporary, path)


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define FinalMAPPOCandidateConfiguration to group the state and operations declared below.
# Declared fields: candidate_id, ppo_update_epochs, learning_rate, ppo_clip_epsilon, gnn_hidden_dimension,
# gnn_message_passing_layers, gnn_training_mode, parameter_sharing_strategy, factor_aggregation, optimizer_family.
# Construction and attribute behavior follow the declared decorators and base classes.
class FinalMAPPOCandidateConfiguration:
    # Declare candidate_id as str for this data structure.
    candidate_id: str
    # Declare ppo_update_epochs as int for this data structure.
    ppo_update_epochs: int
    # Declare learning_rate as float for this data structure.
    learning_rate: float
    # Declare ppo_clip_epsilon as float for this data structure.
    ppo_clip_epsilon: float
    # Declare gnn_hidden_dimension as int for this data structure.
    gnn_hidden_dimension: int
    # Declare gnn_message_passing_layers as int for this data structure.
    gnn_message_passing_layers: int
    # Declare gnn_training_mode as str for this data structure.
    gnn_training_mode: str
    # Declare parameter_sharing_strategy as str for this data structure.
    parameter_sharing_strategy: str
    # Declare factor_aggregation as str for this data structure.
    factor_aggregation: str
    # Set optimizer_family to the text 'ADAM'; declare its type as str.
    optimizer_family: str = "ADAM"

    # Apply property as a decorator to configure the following definition.
    @property
    # Configuration hash using the inputs and processing steps below.
    # Output: the result of _hash(self.__dict__).
    def configuration_hash(self):
        # Return the result of _hash(self.__dict__) to the caller.
        return _hash(self.__dict__)


# Candidate configurations using the inputs and processing steps below.
# Input design: the supplied design.
# Output: a tuple built from a lazy sequence of the result of FinalMAPPOCandidateConfiguration(candidate_id,
# epochs, optimization.learning_rate, assignments at 'ppo_clip_epsilon',...) for...
def candidate_configurations(design=None):
    # Set design to design or the result of build_design().
    design = design or build_design()
    # Set architecture to the result of build_mechanical_pilot_architecture_contract().
    architecture = build_mechanical_pilot_architecture_contract()
    # Set optimization to the result of build_mechanical_adam_optimization_contract().
    optimization = build_mechanical_adam_optimization_contract()
    # Set assignments to a dictionary of x.choice_id mapped to x.candidate_value_or_method for x in
    # design['provisional'].assignments.
    assignments = {x.choice_id: x.candidate_value_or_method
                   # Evaluate design['provisional'].assignments as part of the enclosing expression.
                   for x in design["provisional"].assignments}
    # Return a tuple built from a lazy sequence of the result of FinalMAPPOCandidateConfiguration(candidate_id,
    # epochs, optimization.learning_rate, assignments at 'ppo_clip_epsilon',...) for (candidate_id, epochs) in
    # key/value pairs from CANDIDATE_EPOCHS to the caller.
    return tuple(FinalMAPPOCandidateConfiguration(
        # Supply optimization.learning_rate to FinalMAPPOCandidateConfiguration.
        candidate_id, epochs, optimization.learning_rate,
        # Supply architecture.gnn_hidden_dimension to FinalMAPPOCandidateConfiguration.
        assignments["ppo_clip_epsilon"], architecture.gnn_hidden_dimension,
        # Supply architecture.gnn_message_passing_layers to FinalMAPPOCandidateConfiguration.
        architecture.gnn_message_passing_layers, architecture.gnn_training_mode,
        # Supply architecture.parameter_sharing_strategy to FinalMAPPOCandidateConfiguration.
        architecture.parameter_sharing_strategy,
        # Supply assignments at 'multi_policy_factor_aggregation' to FinalMAPPOCandidateConfiguration.
        assignments["multi_policy_factor_aggregation"],
        # Supply optimization.optimizer_family to FinalMAPPOCandidateConfiguration.
        optimization.optimizer_family,
    # Evaluate key/value pairs from CANDIDATE_EPOCHS as part of the enclosing expression.
    ) for candidate_id, epochs in CANDIDATE_EPOCHS.items())


# Copy the historical audit and override only PPO update epochs.
# Input candidate: the supplied candidate.
# Output: the result of replace(audit).
def candidate_runtime_audit(candidate):
    """Copy the historical audit and override only PPO update epochs."""
    # Set audit to the result of build_mechanical_pilot_configuration_audit().
    audit = build_mechanical_pilot_configuration_audit()
    # Set choices to a tuple built from a lazy sequence of the result of replace(item) when item.choice_id equals
    # 'ppo_update_epochs', otherwise item for item in audit.runtime_choices.
    choices = tuple(
        # Supply value as candidate.ppo_update_epochs.
        replace(item, value=candidate.ppo_update_epochs,
                # Supply classification as the text 'FINAL_SELECTION_V2_CONTROLLED_OVERRIDE'.
                classification="FINAL_SELECTION_V2_CONTROLLED_OVERRIDE",
                # Supply provenance as a dictionary containing protocol_id, only_controlled_override.
                provenance={**dict(item.provenance),
                            # Store PROTOCOL_ID under 'protocol_id'.
                            "protocol_id": PROTOCOL_ID,
                            # Store True under 'only_controlled_override'.
                            "only_controlled_override": True})
        # Evaluate item.choice_id equals the text 'ppo_update_epochs' as part of the enclosing expression.
        if item.choice_id == "ppo_update_epochs" else item
        # Evaluate audit.runtime_choices as part of the enclosing expression.
        for item in audit.runtime_choices
    )
    # Return the result of replace(audit) to the caller.
    return replace(audit, runtime_choices=choices,
                   # Supply audit_id as a tuple containing PROTOCOL_ID, candidate.candidate_id,
                   # candidate.configuration_hash.
                   audit_id=(PROTOCOL_ID, candidate.candidate_id,
                             # Include candidate.configuration_hash in this tuple.
                             candidate.configuration_hash))


# Manifest payload using the inputs and processing steps below.
# Input manifest: the supplied manifest.
# Output: a dictionary containing manifest_id, role, scenario_ids, scenario_count.
def _manifest_payload(manifest):
    # Return a dictionary containing manifest_id, role, scenario_ids, scenario_count to the caller.
    return {"manifest_id": serializable(manifest.manifest_id),
            # Store manifest.purpose.value under 'role'.
            "role": manifest.purpose.value,
            # Store the result of serializable(manifest.scenario_ids) under 'scenario_ids'.
            "scenario_ids": serializable(manifest.scenario_ids),
            # Store the number of entries in manifest.scenario_ids under 'scenario_count'.
            "scenario_count": len(manifest.scenario_ids)}


# Build protocol using the inputs and processing steps below.
# Output: protocol.
# Processing: select branches using the stated conditions.
def build_protocol():
    # Set design to the result of build_design().
    design = build_design()
    # Set manifests to design at 'manifests'.
    manifests = design["manifests"]
    # Set role_sets to a dictionary of role mapped to a set built from manifests[role].scenario_ids for role in
    # ScenarioRole.
    role_sets = {role: set(manifests[role].scenario_ids) for role in ScenarioRole}
    # Run this branch when whether any item is true in a lazy sequence of role_sets at a intersected with
    # role_sets at b for (i, a) in index/value pairs from ScenarioRole.
    if any(role_sets[a] & role_sets[b] for i, a in enumerate(ScenarioRole)
           # Evaluate tuple(ScenarioRole) sliced by i + 1: as part of the enclosing expression.
           for b in tuple(ScenarioRole)[i + 1:]):
        # Raise ValueError with the text 'SCENARIO_ROLE_IDENTITY_LEAKAGE' to stop this execution path.
        raise ValueError("SCENARIO_ROLE_IDENTITY_LEAKAGE")
    # Run this branch when whether any item is true in a lazy sequence of the number of entries in role_sets[role]
    # differs from 36 for role in ScenarioRole.
    if any(len(role_sets[role]) != 36 for role in ScenarioRole):
        # Raise ValueError with the text 'FINAL_SELECTION_REQUIRES_36_SCENARIOS_PER_ROLE' to stop this execution
        # path.
        raise ValueError("FINAL_SELECTION_REQUIRES_36_SCENARIOS_PER_ROLE")
    # Set candidates to the result of candidate_configurations(design).
    candidates = candidate_configurations(design)
    # Set fixed to a dictionary of key mapped to the requested attribute of candidates at 0 for key in a tuple
    # containing the text 'learning_rate', the text 'ppo_clip_epsilon', the text 'gnn_hidden_dimension', the
    # text...
    fixed = {key: getattr(candidates[0], key) for key in (
        "learning_rate", "ppo_clip_epsilon", "gnn_hidden_dimension",
        "gnn_message_passing_layers", "gnn_training_mode",
        "parameter_sharing_strategy", "factor_aggregation", "optimizer_family")}
    # Set protocol to a dictionary containing protocol_id, version, status, study_type, varied_factor,
    # candidate_ids,...
    protocol = {
        # Store PROTOCOL_ID under 'protocol_id'.
        # Store 2 under 'version'.
        "protocol_id": PROTOCOL_ID, "version": 2,
        "status": "FROZEN_BEFORE_FINAL_SELECTION_EXECUTION",
        "study_type": "CONTROLLED_ONE_FACTOR_ABLATION_MODEL_SELECTION",
        "varied_factor": "ppo_update_epochs",
        # Store a list built from CANDIDATE_EPOCHS under 'candidate_ids'.
        "candidate_ids": list(CANDIDATE_EPOCHS),
        # Store CANDIDATE_EPOCHS under 'candidate_values'.
        "candidate_values": CANDIDATE_EPOCHS,
        # Store fixed under 'fixed_configuration'.
        "fixed_configuration": fixed,
        # Store REPLICATION_COUNT under 'replication_count_n'.
        "replication_count_n": REPLICATION_COUNT,
        # Store UPDATE_HORIZON under 'update_horizon_h'.
        "update_horizon_h": UPDATE_HORIZON,
        # Store the text 'N=3 and H=2 are predeclared project-resource choices for this...' under
        # 'resource_statement'.
        "resource_statement": (
            "N=3 and H=2 are predeclared project-resource choices for this "
            "bounded model-selection experiment. They are not claimed as "
            "statistically optimal replication or training-budget values."),
        # Store a list of a list containing the text 'FINAL_MAPPO_CANONICAL_REPLICATION_V2', index for index in
        # the integer range defined by REPLICATION_COUNT under 'replication_identities'.
        "replication_identities": [
            # Evaluate a list containing the text 'FINAL_MAPPO_CANONICAL_REPLICATION_V2', index as part of the
            # enclosing expression.
            ["FINAL_MAPPO_CANONICAL_REPLICATION_V2", index]
            # Evaluate the integer range defined by REPLICATION_COUNT as part of the enclosing expression.
            for index in range(REPLICATION_COUNT)],
        # Store False under 'adaptive_early_stopping'.
        "adaptive_early_stopping": False,
        # Store False under 'bad_seed_replacement'.
        "bad_seed_replacement": False,
        # Store False under 'adaptive_horizon_extension'.
        "adaptive_horizon_extension": False,
        "primary_metric": "TOTAL_TEAM_TRAVEL_TIME_SECONDS",
        "metric_direction": "LOWER_IS_BETTER",
        # Store a list containing the text 'ZERO_COLLISIONS', the text 'ZERO_BLOCKED_ZONE_VIOLATIONS', the text...
        # under 'hard_validity_gates'.
        "hard_validity_gates": [
            "ZERO_COLLISIONS", "ZERO_BLOCKED_ZONE_VIOLATIONS",
            "HARD_ACTION_MASKS_RESPECTED", "REGULATORY_INVARIANT",
            "PROTOCOL_INVARIANT", "ROUTE_TRUTH_LEAKAGE_ABSENT",
            "FINITE_NETWORK_AND_TRAINING_QUANTITIES"],
        "selection_rule": "LOWEST_MEAN_VALIDATION_TTT_AMONG_ELIGIBLE",
        "exact_tie_rule": "RETAIN_E5_IF_E5_IN_EXACT_TIE",
        # Store False under 'globally_optimal_claim'.
        "globally_optimal_claim": False,
        # Store False under 'exhaustive_hyperparameter_search'.
        "exhaustive_hyperparameter_search": False,
        # Store True under 'selected_best_among_tested_candidates'.
        "selected_best_among_tested_candidates": True,
        "selection_data_role": "VALIDATION",
        # Store False under 'held_out_used_for_selection'.
        "held_out_used_for_selection": False,
        # Store a dictionary of role.value mapped to the result of _manifest_payload(manifests at role) for role
        # in ScenarioRole under 'manifests'.
        "manifests": {role.value: _manifest_payload(manifests[role])
                      # Evaluate ScenarioRole as part of the enclosing expression.
                      for role in ScenarioRole},
        # Store a dictionary containing seed, resamples, interpretation under 'bootstrap'.
        # Store BOOTSTRAP_SEED under 'seed'.
        "bootstrap": {"seed": BOOTSTRAP_SEED,
                      # Store BOOTSTRAP_RESAMPLES under 'resamples'.
                      "resamples": BOOTSTRAP_RESAMPLES,
                      "interpretation": "DESCRIPTIVE_PAIRED_UNCERTAINTY_ONLY"},
        # Store the result of serializable(design['freeze'].freeze_id) under 'frozen_design_identity'.
        "frozen_design_identity": serializable(design["freeze"].freeze_id),
        # Store False under 'historical_demo_checkpoint_selection_eligible'.
        "historical_demo_checkpoint_selection_eligible": False,
    }
    # Set protocol['protocol_hash'] to the result of _hash(protocol).
    protocol["protocol_hash"] = _hash(protocol)
    # Return protocol to the caller.
    return protocol


# Prepare using the inputs and processing steps below.
# Input root: the base directory used to resolve files.
# Output: protocol.
# Processing: select branches using the stated conditions.
def prepare(root=OUTPUT_ROOT):
    # Set root to the result of Path(root).
    # Create the directory requested by root.
    root = Path(root); root.mkdir(parents=True, exist_ok=True)
    # Set protocol to the result of build_protocol().
    protocol = build_protocol()
    # Call atomic_write_json with the supplied arguments.
    atomic_write_json(root / "protocol.json", protocol)
    # Set manifest to a dictionary containing protocol_id, candidates, historical_contracts_mutated,
    # historical_checkpoints_eligible.
    manifest = {"protocol_id": PROTOCOL_ID,
                # Store a list of the result of serializable(x.__dict__) combined with a dictionary containing
                # configuration_hash, only_difference for x in the result of candidate_configurations() under
                # 'candidates'.
                "candidates": [serializable(x.__dict__) | {
                    # Store x.configuration_hash under 'configuration_hash'.
                    "configuration_hash": x.configuration_hash,
                    "only_difference": "ppo_update_epochs"}
                    # Evaluate the result of candidate_configurations() as part of the enclosing expression.
                    for x in candidate_configurations()],
                # Store False under 'historical_contracts_mutated'.
                "historical_contracts_mutated": False,
                # Store False under 'historical_checkpoints_eligible'.
                "historical_checkpoints_eligible": False}
    # Call atomic_write_json with the supplied arguments.
    atomic_write_json(root / "candidate_manifest.json", manifest)
    # Set progress to root joined with the path segment 'progress.json'.
    progress = root / "progress.json"
    # Run this branch when the negation of whether progress exists.
    if not progress.exists():
        # Call atomic_write_json with the supplied arguments.
        atomic_write_json(progress, {"protocol_id": PROTOCOL_ID,
            # Store an empty list under 'completed_training'.
            # Store an empty list under 'completed_validation'.
            "completed_training": [], "completed_validation": [],
            # Store False under 'held_out_consumed'.
            # Store False under 'baseline_consumed'.
            "held_out_consumed": False, "baseline_consumed": False})
    # Return protocol to the caller.
    return protocol


# Smoke using the inputs and processing steps below.
# Input root: the base directory used to resolve files.
# Output: payload.
def smoke(root=OUTPUT_ROOT):
    # Set protocol to the result of prepare(root).
    protocol = prepare(root)
    # Set payload to a dictionary containing status, evidence_classification, held_out_scenarios_consumed,
    # candidate_contracts,...
    payload = {"status": "SMOKE_TEST_ONLY",
               # Store a list containing the text 'NOT_MODEL_SELECTION_EVIDENCE', the text
               # 'NOT_VALIDATION_EVIDENCE', the text 'NOT_HELD_OUT_EVIDENCE' under 'evidence_classification'.
               "evidence_classification": ["NOT_MODEL_SELECTION_EVIDENCE",
                    "NOT_VALIDATION_EVIDENCE", "NOT_HELD_OUT_EVIDENCE"],
               # Store 0 under 'held_out_scenarios_consumed'.
               "held_out_scenarios_consumed": 0,
               # Store a list of the result of serializable(x.__dict__) for x in the result of
               # candidate_configurations() under 'candidate_contracts'.
               "candidate_contracts": [serializable(x.__dict__)
                                       # Evaluate the result of candidate_configurations() as part of the
                                       # enclosing expression.
                                       for x in candidate_configurations()],
               # Store True under 'synthetic_workload_only'.
               "synthetic_workload_only": True,
               # Store protocol at 'protocol_hash' under 'protocol_hash'.
               "protocol_hash": protocol["protocol_hash"]}
    # Call atomic_write_json with the supplied arguments.
    atomic_write_json(Path(root) / "smoke" / "smoke_result.json", payload)
    # Return payload to the caller.
    return payload


# Fresh bundle using the inputs and processing steps below.
# Input design: the supplied design.
# Input candidate: the supplied candidate.
# Input replication_index: the supplied replication index.
# Input manifest: the supplied manifest.
# Output: the result of build_mechanical_mappo_behavior_policy_bundle().
def _fresh_bundle(design, candidate, replication_index, manifest):
    # Set replication to a tuple containing the text 'FINAL_MAPPO_CANONICAL_REPLICATION_V2', replication_index.
    replication = ("FINAL_MAPPO_CANONICAL_REPLICATION_V2", replication_index)
    # Set identity to the result of MAPPOBehaviorRolloutIdentity(the result of _identity(design, the result of
    # build_mechanical_pilot_architecture_contract(),...).
    identity = MAPPOBehaviorRolloutIdentity(
        # Supply the result of _identity(design, the result of build_mechanical_pilot_architecture_contract(), the
        # result of...) to MAPPOBehaviorRolloutIdentity.
        _identity(design, build_mechanical_pilot_architecture_contract(),
                  # Supply the result of build_mechanical_adam_optimization_contract() to _identity.
                  build_mechanical_adam_optimization_contract(), manifest,
                  # Supply replication to _identity.
                  replication, "FINAL_SELECTION_INITIAL_STATE"),
        # Supply design['freeze'].freeze_id to MAPPOBehaviorRolloutIdentity.
        design["freeze"].freeze_id,
        # Supply build_mechanical_pilot_architecture_contract().contract_id to MAPPOBehaviorRolloutIdentity.
        build_mechanical_pilot_architecture_contract().contract_id,
        # Supply build_mechanical_adam_optimization_contract().contract_id to MAPPOBehaviorRolloutIdentity.
        build_mechanical_adam_optimization_contract().contract_id,
        # Supply manifest.manifest_id to MAPPOBehaviorRolloutIdentity.
        manifest.manifest_id)
    # Candidate is deliberately absent from initialization seed: matched
    # replications differ only in PPO update epochs.
    # Return the result of build_mechanical_mappo_behavior_policy_bundle() to the caller.
    return build_mechanical_mappo_behavior_policy_bundle(
        # Supply component_seed_identity as a tuple containing replication, the text 'MODEL_INITIALIZATION'.
        component_seed_identity=(replication, "MODEL_INITIALIZATION"),
        # Supply behavior_rollout_identity as identity.
        behavior_rollout_identity=identity)


# Checkpoint payload using the inputs and processing steps below.
# Input bundle: the supplied bundle.
# Input candidate: the supplied candidate.
# Input replication_index: the supplied replication index.
# Input states: the supplied states.
# Input updates: the supplied updates.
# Input manifest: the supplied manifest.
# Input runtime: the supplied runtime.
# Output: a dictionary containing checkpoint_type, protocol_id, candidate_id, candidate_configuration,...
def _checkpoint_payload(bundle, candidate, replication_index, states, updates,
                        # Declare manifest, runtime as input parameters.
                        manifest, runtime):
    # Set hashes to the result of _current_hashes(bundle).
    hashes = _current_hashes(bundle)
    # Return a dictionary containing checkpoint_type, protocol_id, candidate_id, candidate_configuration,... to
    # the caller.
    return {
        "checkpoint_type": "FINAL_MAPPO_SELECTION_V2_CANDIDATE_CHECKPOINT",
        # Store PROTOCOL_ID under 'protocol_id'.
        # Store candidate.candidate_id under 'candidate_id'.
        "protocol_id": PROTOCOL_ID, "candidate_id": candidate.candidate_id,
        # Store the result of serializable(candidate.__dict__) under 'candidate_configuration'.
        "candidate_configuration": serializable(candidate.__dict__),
        # Store candidate.configuration_hash under 'candidate_configuration_hash'.
        "candidate_configuration_hash": candidate.configuration_hash,
        # Store replication_index under 'replication_index'.
        "replication_index": replication_index,
        # Store a list containing the text 'FINAL_MAPPO_CANONICAL_REPLICATION_V2', replication_index under
        # 'replication_identity'.
        "replication_identity": ["FINAL_MAPPO_CANONICAL_REPLICATION_V2",
                                 # Include replication_index in this list.
                                 replication_index],
        # Store UPDATE_HORIZON under 'policy_state_index'.
        # Store UPDATE_HORIZON under 'update_count'.
        "policy_state_index": UPDATE_HORIZON, "update_count": UPDATE_HORIZON,
        # Store the result of serializable(manifest.manifest_id) under 'training_manifest_identity'.
        "training_manifest_identity": serializable(manifest.manifest_id),
        # Store the result of serializable(build_mechanical_pilot_architecture_contract().contract_id) under
        # 'architecture_identity'.
        "architecture_identity": serializable(
            # Supply build_mechanical_pilot_architecture_contract().contract_id to serializable.
            build_mechanical_pilot_architecture_contract().contract_id),
        # Store the result of serializable(build_mechanical_adam_optimization_contract().contract_id) under
        # 'optimizer_identity'.
        "optimizer_identity": serializable(
            # Supply build_mechanical_adam_optimization_contract().contract_id to serializable.
            build_mechanical_adam_optimization_contract().contract_id),
        # Store hashes under 'parameter_hashes'.
        "parameter_hashes": hashes,
        # Store the result of bundle.gnn.state_dict() under 'gnn_state_dict'.
        "gnn_state_dict": bundle.gnn.state_dict(),
        # Store the result of bundle.proposer_actor.state_dict() under 'proposer_state_dict'.
        "proposer_state_dict": bundle.proposer_actor.state_dict(),
        # Store the result of bundle.responder_actor.state_dict() under 'responder_state_dict'.
        "responder_state_dict": bundle.responder_actor.state_dict(),
        # Store the result of bundle.centralized_critic.state_dict() under 'critic_state_dict'.
        "critic_state_dict": bundle.centralized_critic.state_dict(),
        # Store a list of x at 'team_travel_time_seconds' for x in states under 'objective_history'.
        "objective_history": [x["team_travel_time_seconds"] for x in states],
        # Store states under 'state_metrics'.
        # Store updates under 'update_diagnostics'.
        "state_metrics": states, "update_diagnostics": updates,
        # Store the sum of a lazy sequence of x at 'sumo_step_count' for x in states under 'sumo_step_count'.
        "sumo_step_count": sum(x["sumo_step_count"] for x in states),
        # Store the sum of a lazy sequence of x at 'collision_count' for x in states under 'collisions'.
        "collisions": sum(x["collision_count"] for x in states),
        # Store the sum of a lazy sequence of x at 'blocked_zone_violation_count' for x in states under
        # 'blocked_zone_violations'.
        "blocked_zone_violations": sum(
            # Evaluate x at 'blocked_zone_violation_count' as part of the enclosing expression.
            x["blocked_zone_violation_count"] for x in states),
        # Store 0 under 'hard_mask_violations'.
        # Store runtime under 'runtime_seconds'.
        "hard_mask_violations": 0, "runtime_seconds": runtime,
        # Store False under 'performance_selected'.
        # Store False under 'held_out_consumed'.
        "performance_selected": False, "held_out_consumed": False,
    }


# Train using the inputs and processing steps below.
# Input root: the base directory used to resolve files.
# Input resume: the supplied resume.
# Output: a dictionary containing completed_training.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def train(root=OUTPUT_ROOT, resume=False):
    # Call prepare with the supplied arguments.
    # Set root to the result of Path(root).
    # Set design to the result of build_design().
    prepare(root); root = Path(root); design = build_design()
    # Set manifest to design['manifests'] at ScenarioRole.TRAINING.
    manifest = design["manifests"][ScenarioRole.TRAINING]
    # Set specs to a tuple built from a lazy sequence of the result of _specification(design at 'payload', sid)
    # for sid in manifest.scenario_ids.
    specs = tuple(_specification(design["payload"], sid)
                  # Evaluate manifest.scenario_ids as part of the enclosing expression.
                  for sid in manifest.scenario_ids)
    # Set completed to an empty list.
    completed = []
    # Iterate over the result of candidate_configurations(design), binding each item to candidate.
    for candidate in candidate_configurations(design):
        # Iterate over the integer range defined by REPLICATION_COUNT, binding each item to replication_index.
        for replication_index in range(REPLICATION_COUNT):
            # Set checkpoint to root joined with the path segment 'training' divided by candidate.candidate_id divided by
            # formatted text built from the embedded values.
            checkpoint = root / "training" / candidate.candidate_id / (
                # Evaluate formatted text built from the embedded values as part of the enclosing expression.
                f"replication_{replication_index}_state_{UPDATE_HORIZON}.pt")
            # Run this branch when resume and whether checkpoint exists.
            if resume and checkpoint.exists():
                # Append a list containing candidate.candidate_id, replication_index to completed.
                completed.append([candidate.candidate_id, replication_index])
                # Skip the rest of this loop iteration and process the next item.
                continue
            # Set started to the result of perf_counter().
            started = perf_counter()
            # Set bundle to the result of _fresh_bundle(design, candidate, replication_index, manifest).
            bundle = _fresh_bundle(
                # Supply replication_index to _fresh_bundle.
                design, candidate, replication_index, manifest)
            # Set replication to a tuple containing the text 'FINAL_MAPPO_CANONICAL_REPLICATION_V2',
            # replication_index.
            replication = ("FINAL_MAPPO_CANONICAL_REPLICATION_V2",
                           # Include replication_index in this tuple.
                           replication_index)
            # Set (states, updates, rollout) to a tuple containing an empty list, an empty list, None.
            states, updates, rollout = [], [], None
            # Iterate over the integer range defined by UPDATE_HORIZON plus 1, binding each item to state_index.
            for state_index in range(UPDATE_HORIZON + 1):
                # Run this branch when state_index.
                if state_index:
                    # Append the result of MechanicalMAPPOTrainer(rollout_payload=rollout, bundle=bundle,
                    # output_path=None,...() to updates.
                    updates.append(MechanicalMAPPOTrainer(
                        # Supply rollout_payload as rollout.
                        # Supply bundle as bundle.
                        rollout_payload=rollout, bundle=bundle,
                        # Supply output_path as None.
                        output_path=None,
                        # Supply configuration as the result of candidate_runtime_audit(candidate).
                        configuration=candidate_runtime_audit(candidate)).run())
                # Set (metrics, rollout) to the result of collect_controlled_training_pass().
                metrics, rollout = collect_controlled_training_pass(
                    # Supply design as design.
                    design=design,
                    # Supply architecture as the result of build_mechanical_pilot_architecture_contract().
                    architecture=build_mechanical_pilot_architecture_contract(),
                    # Supply optimization as the result of build_mechanical_adam_optimization_contract().
                    optimization=build_mechanical_adam_optimization_contract(),
                    # Supply manifest as manifest.
                    # Supply specifications as specs.
                    # Supply bundle as bundle.
                    manifest=manifest, specifications=specs, bundle=bundle,
                    # Supply replication_identity as replication.
                    replication_identity=replication,
                    # Supply pass_label as formatted text built from the embedded values.
                    pass_label=f"{candidate.candidate_id}_STATE_{state_index}",
                    # Store PROTOCOL_ID under 'protocol_id'.
                    progress_context={"protocol_id": PROTOCOL_ID,
                        # Store candidate.candidate_id under 'candidate_id'.
                        "candidate_id": candidate.candidate_id,
                        # Store replication_index under 'replication_index'.
                        "replication_index": replication_index,
                        # Store state_index under 'state_index'.
                        "state_index": state_index},
                    # Supply progress_path as root joined with the path segment 'progress.json'.
                    progress_path=root / "progress.json")
                # Append metrics to states.
                states.append(metrics)
            # Set payload to the result of _checkpoint_payload(bundle, candidate, replication_index, states,
            # updates, manifest, the result of perf_counter()...).
            payload = _checkpoint_payload(
                # Supply replication_index to _checkpoint_payload.
                bundle, candidate, replication_index, states, updates,
                # Supply the result of perf_counter() minus started to _checkpoint_payload.
                manifest, perf_counter() - started)
            # Call atomic_torch_save with the supplied arguments.
            atomic_torch_save(payload, checkpoint)
            # Append a list containing candidate.candidate_id, replication_index to completed.
            completed.append([candidate.candidate_id, replication_index])
            # Call atomic_write_json with the supplied arguments.
            atomic_write_json(root / "progress.json", {
                # Store PROTOCOL_ID under 'protocol_id'.
                # Store completed under 'completed_training'.
                "protocol_id": PROTOCOL_ID, "completed_training": completed,
                # Store False under 'held_out_consumed'.
                "held_out_consumed": False})
    # Return a dictionary containing completed_training to the caller.
    return {"completed_training": completed}


# Define FinalSelectionInferenceProvider to group the state and operations declared below.
# Base classes: MAPPOBehaviorActionProvider.
# Instances expose the attributes and methods implemented in this class.
class FinalSelectionInferenceProvider(MAPPOBehaviorActionProvider):
    # Set selection_rule to the text 'FINAL_SELECTION_V2_INFERENCE_ONLY_MASKED_MAPPO'.
    selection_rule = "FINAL_SELECTION_V2_INFERENCE_ONLY_MASKED_MAPPO"
    # Set supports_event_driven_renegotiation to True.
    supports_event_driven_renegotiation = True

    # Initialize the instance attributes and collaborators used by the operations below.
    # Input bundle: the supplied bundle.
    # Input sampling_seed: the supplied sampling seed.
    # Output: no explicit value; normal completion returns None.
    def __init__(self, bundle, sampling_seed):
        # Call super().__init__ with the supplied arguments.
        super().__init__(replace(bundle, centralized_critic=None),
                         # Supply sampling_seed as sampling_seed.
                         sampling_seed=sampling_seed,
                         # Supply runtime_critic_enabled as False.
                         runtime_critic_enabled=False)
        # Set self.training_operations to 0.
        self.training_operations = 0

    # Finalize episode using the inputs and processing steps below.
    # Input episode_id: the supplied episode id.
    # Input reward: the supplied reward.
    # Output: None.
    def finalize_episode(self, episode_id, reward):
        # Return None to the caller.
        return None


# Define DeterministicNoNegotiationRegulatoryBaseline to group the state and operations declared below.
# Instances expose the attributes and methods implemented in this class.
class DeterministicNoNegotiationRegulatoryBaseline:
    # Set selection_rule to the text 'KEEP_REGULATORY_CLAIMS_NO_LEARNED_NEGOTIATION_V1'.
    selection_rule = "KEEP_REGULATORY_CLAIMS_NO_LEARNED_NEGOTIATION_V1"
    # Set uses_mappo_behavior_policy to False.
    uses_mappo_behavior_policy = False
    # Set neural_actor_calls to 0.
    neural_actor_calls = 0
    # Set reward_used_for_selection to False.
    reward_used_for_selection = False
    # Set future_outcome_used_for_selection to False.
    future_outcome_used_for_selection = False
    # Set vehicle_id_priority_rule to False.
    vehicle_id_priority_rule = False
    # Set allows_unresolved_coordination to True.
    allows_unresolved_coordination = True

    # Select joint actions using the inputs and processing steps below.
    # Input branches: the supplied branches.
    # Input factor_contexts: the supplied factor contexts.
    # Output: matches at 0 when matches, otherwise None.
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    def select_joint_actions(self, branches, factor_contexts):
        # Delete factor_contexts from its containing namespace or collection.
        del factor_contexts
        # Set matches to an empty list.
        matches = []
        # Iterate over branches, binding each item to branch.
        for branch in branches:
            # Set proposer to branch.proposer_assignment.claim_action_assignments.
            proposer = branch.proposer_assignment.claim_action_assignments
            # Set responder to branch.responder_assignment.response_action_assignments.
            responder = branch.responder_assignment.response_action_assignments
            # Run this branch when whether every item is true in a lazy sequence of action equals 'KEEP_CLAIM' for
            # (_, action) in proposer and whether every item is true in a lazy sequence of action equals
            # 'REJECT_RELINQUISHMENT' for (_, action) in responder and branch.graph_executable.
            if (all(action == "KEEP_CLAIM" for _, action in proposer)
                    # Evaluate whether every item is true in a lazy sequence of action equals the text
                    # 'REJECT_RELINQUISHMENT' for (_, action) in responder as part of the enclosing expression.
                    and all(action == "REJECT_RELINQUISHMENT"
                            # Evaluate a tuple containing _, action as part of the enclosing expression.
                            for _, action in responder)
                    # Evaluate branch.graph_executable as part of the enclosing expression.
                    and branch.graph_executable):
                # Append branch to matches.
                matches.append(branch)
        # Run this branch when the number of entries in matches is greater than 1.
        if len(matches) > 1:
            # Raise RuntimeError with the text 'BASELINE_NONUNIQUE_KEEP_REGULATORY_BRANCH' to stop this execution
            # path.
            raise RuntimeError("BASELINE_NONUNIQUE_KEEP_REGULATORY_BRANCH")
        # Return matches at 0 when matches, otherwise None to the caller.
        return matches[0] if matches else None


# Load bundle using the inputs and processing steps below.
# Input checkpoint_path: the supplied checkpoint path.
# Output: a tuple containing payload, bundle.
# Processing: select branches using the stated conditions.
def _load_bundle(checkpoint_path):
    # Set payload to the decoded data produced by torch.load from checkpoint_path.
    payload = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    # Set bundle to the result of build_mechanical_mappo_behavior_policy_bundle().
    bundle = build_mechanical_mappo_behavior_policy_bundle(
        # Supply component_seed_identity as a tuple containing the text 'FINAL_SELECTION_V2_RECONSTRUCTION'.
        component_seed_identity=("FINAL_SELECTION_V2_RECONSTRUCTION",))
    # Call bundle.gnn.load_state_dict with the supplied arguments.
    bundle.gnn.load_state_dict(payload["gnn_state_dict"])
    # Call bundle.proposer_actor.load_state_dict with the supplied arguments.
    bundle.proposer_actor.load_state_dict(payload["proposer_state_dict"])
    # Call bundle.responder_actor.load_state_dict with the supplied arguments.
    bundle.responder_actor.load_state_dict(payload["responder_state_dict"])
    # Call bundle.centralized_critic.load_state_dict with the supplied arguments.
    bundle.centralized_critic.load_state_dict(payload["critic_state_dict"])
    # Run this branch when the result of _current_hashes(bundle) differs from payload at 'parameter_hashes'.
    if _current_hashes(bundle) != payload["parameter_hashes"]:
        # Raise ValueError with the text 'FINAL_SELECTION_CHECKPOINT_HASH_MISMATCH' to stop this execution path.
        raise ValueError("FINAL_SELECTION_CHECKPOINT_HASH_MISMATCH")
    # Return a tuple containing payload, bundle to the caller.
    return payload, bundle


# Episode record using the inputs and processing steps below.
# Input episode: the supplied episode.
# Input provider_kind: the supplied provider kind.
# Output: a dictionary containing scenario_id, total_team_travel_time_seconds, scheduled_vehicles,
# completed_vehicles,...
def _episode_record(episode, provider_kind):
    # Return a dictionary containing scenario_id, total_team_travel_time_seconds, scheduled_vehicles,
    # completed_vehicles,... to the caller.
    return {"scenario_id": serializable(episode.scenario_id),
            # Store episode.team_travel_time_seconds under 'total_team_travel_time_seconds'.
            "total_team_travel_time_seconds": episode.team_travel_time_seconds,
            # Store episode.scheduled_vehicle_count under 'scheduled_vehicles'.
            "scheduled_vehicles": episode.scheduled_vehicle_count,
            # Store episode.completed_vehicle_count under 'completed_vehicles'.
            "completed_vehicles": episode.completed_vehicle_count,
            # Store episode.episode_completion_status equals the text 'UNRESOLVED_COORDINATION_BASELINE' under
            # 'unresolved_coordination_case'.
            "unresolved_coordination_case": (
                # Evaluate episode.episode_completion_status equals the text 'UNRESOLVED_COORDINATION_BASELINE' as
                # part of the enclosing expression.
                episode.episode_completion_status ==
                "UNRESOLVED_COORDINATION_BASELINE"),
            # Store episode.episode_completion_status under 'episode_completion_status'.
            "episode_completion_status": episode.episode_completion_status,
            # Store 'unresolved_coordination_reason' from episode.provenance; use None if absent under
            # 'unresolved_coordination_reason'.
            "unresolved_coordination_reason": episode.provenance.get(
                "unresolved_coordination_reason"),
            # Store episode.completed_vehicle_count divided by episode.simulation_duration_seconds when
            # episode.simulation_duration_seconds, otherwise 0.0 under 'throughput'.
            "throughput": (episode.completed_vehicle_count /
                           # Evaluate episode.simulation_duration_seconds as part of the enclosing expression.
                           episode.simulation_duration_seconds
                           # Evaluate episode.simulation_duration_seconds as part of the enclosing expression.
                           if episode.simulation_duration_seconds else 0.0),
            # Store episode.collision_count under 'collisions'.
            "collisions": episode.collision_count,
            "blocked_zone_violations":
                # Evaluate episode.blocked_zone_entry_violation_count as part of the enclosing expression.
                episode.blocked_zone_entry_violation_count,
            "native_sumo_safety_interventions":
                # Evaluate episode.native_sumo_safety_intervention_count as part of the enclosing expression.
                episode.native_sumo_safety_intervention_count,
            # Store the number of entries in episode.joint_decision_batches under 'negotiation_batches'.
            "negotiation_batches": len(episode.joint_decision_batches),
            # Store episode.proposer_factor_count when provider_kind equals the text 'MAPPO', otherwise 0 under
            # 'learned_proposer_actions'.
            "learned_proposer_actions": episode.proposer_factor_count
                # Evaluate provider_kind equals the text 'MAPPO' as part of the enclosing expression.
                if provider_kind == "MAPPO" else 0,
            # Store episode.responder_factor_count when provider_kind equals the text 'MAPPO', otherwise 0 under
            # 'learned_responder_actions'.
            "learned_responder_actions": episode.responder_factor_count
                # Evaluate provider_kind equals the text 'MAPPO' as part of the enclosing expression.
                if provider_kind == "MAPPO" else 0,
            # Store 'neural_actor_calls' from episode.provenance; use 0 if absent under 'neural_actor_calls'.
            "neural_actor_calls": episode.provenance.get(
                # Supply the text 'neural_actor_calls' to the enclosing expression.
                "neural_actor_calls", 0),
            # Store 'fabricated_negotiation_branches' from episode.provenance; use 0 if absent under
            # 'fabricated_negotiation_branches'.
            "fabricated_negotiation_branches": episode.provenance.get(
                # Supply the text 'fabricated_negotiation_branches' to the enclosing expression.
                "fabricated_negotiation_branches", 0),
            # Store 'vehicle_id_priority_decisions' from episode.provenance; use 0 if absent under
            # 'vehicle_id_priority_decisions'.
            "vehicle_id_priority_decisions": episode.provenance.get(
                # Supply the text 'vehicle_id_priority_decisions' to the enclosing expression.
                "vehicle_id_priority_decisions", 0),
            # Store a dictionary built from 'liveness_metrics' from episode.provenance; use an empty dictionary if
            # absent under 'liveness_metrics'.
            "liveness_metrics": dict(episode.provenance.get(
                # Supply an empty dictionary to episode.provenance.get.
                "liveness_metrics", {})),
            # Store the result of serializable('liveness_diagnostics' from episode.provenance; use an empty tuple
            # if absent) under 'liveness_diagnostics'.
            "liveness_diagnostics": serializable(episode.provenance.get(
                # Supply an empty tuple to episode.provenance.get.
                "liveness_diagnostics", ())),
            # Store a dictionary built from episode.hard_validity_gate_results under 'hard_validity_gate_results'.
            "hard_validity_gate_results": dict(
                # Supply episode.hard_validity_gate_results to dict.
                episode.hard_validity_gate_results),
            # Store 0 under 'hard_mask_violations'.
            "hard_mask_violations": 0,
            # Store 0 under 'regulatory_invariant_violations'.
            "regulatory_invariant_violations": 0,
            # Store 0 under 'protocol_invariant_failures'.
            "protocol_invariant_failures": 0,
            # Store 0 under 'route_truth_actor_fields_consumed'.
            "route_truth_actor_fields_consumed": 0,
            # Store episode.sumo_step_count under 'sumo_steps'.
            "sumo_steps": episode.sumo_step_count,
            # Store episode.wall_clock_runtime_seconds under 'runtime_seconds'.
            "runtime_seconds": episode.wall_clock_runtime_seconds}


# Evaluate manifest using the inputs and processing steps below.
# Input checkpoint: the supplied checkpoint.
# Input manifest: the supplied manifest.
# Input design: the supplied design.
# Input role: the supplied role.
# Input replication_index: the supplied replication index.
# Output: records.
# Processing: iterate over the relevant records.
def _evaluate_manifest(checkpoint, manifest, design, role, replication_index):
    # Set (_, bundle) to the result of _load_bundle(checkpoint).
    _, bundle = _load_bundle(checkpoint)
    # Set provider to the result of FinalSelectionInferenceProvider(bundle).
    provider = FinalSelectionInferenceProvider(
        # Supply sampling_seed as the result of int.from_bytes(hashlib.sha256(repr((PROTOCOL_ID, role.value,
        # replication_index)).encode()).digest() sliced by...) modulo 2 raised to the power 31.
        bundle, sampling_seed=int.from_bytes(hashlib.sha256(repr((
            # Include replication_index in this tuple.
            PROTOCOL_ID, role.value, replication_index)).encode()).digest()[:8],
            # Evaluate 2 raised to the power 31 as part of the enclosing expression.
            "big") % (2 ** 31))
    # Set records to an empty list.
    records = []
    # Iterate over manifest.scenario_ids, binding each item to sid.
    for sid in manifest.scenario_ids:
        # Set episode to the result of CoupledNegotiationTrainingEnvironment(provider).run_episode(the result of
        # _specification(design at 'payload', sid), manifest.manifest_id).
        episode = CoupledNegotiationTrainingEnvironment(provider).run_episode(
            # Supply the result of _specification(design at 'payload', sid) to
            # CoupledNegotiationTrainingEnvironment(provider).run_episode.
            _specification(design["payload"], sid), manifest.manifest_id)
        # Append the result of _episode_record(episode, the text 'MAPPO') to records.
        records.append(_episode_record(episode, "MAPPO"))
    # Return records to the caller.
    return records


# Summary using the inputs and processing steps below.
# Input records: the supplied records.
# Output: a dictionary containing scenario_execution_count, total, mean, median, standard_deviation, minimum,
# maximum,...
def _summary(records):
    # Set values to a list of x at 'total_team_travel_time_seconds' for x in records.
    values = [x["total_team_travel_time_seconds"] for x in records]
    # Return a dictionary containing scenario_execution_count, total, mean, median, standard_deviation, minimum,
    # maximum,... to the caller.
    return {"scenario_execution_count": len(records), "total": sum(values),
            # Store the result of mean(values) under 'mean'.
            # Store the result of median(values) under 'median'.
            "mean": mean(values), "median": median(values),
            # Store the result of pstdev(values) under 'standard_deviation'.
            # Store the minimum of values under 'minimum'.
            "standard_deviation": pstdev(values), "minimum": min(values),
            # Store the maximum of values under 'maximum'.
            "maximum": max(values),
            # Store the sum of a lazy sequence of x at 'completed_vehicles' for x in records under
            # 'completed_vehicles'.
            "completed_vehicles": sum(x["completed_vehicles"] for x in records),
            # Store the sum of a lazy sequence of x at 'collisions' for x in records under 'collisions'.
            "collisions": sum(x["collisions"] for x in records),
            # Store the sum of a lazy sequence of x at 'blocked_zone_violations' for x in records under
            # 'blocked_zone_violations'.
            "blocked_zone_violations": sum(
                # Evaluate x at 'blocked_zone_violations' as part of the enclosing expression.
                x["blocked_zone_violations"] for x in records),
            # Store the sum of a lazy sequence of x at 'native_sumo_safety_interventions' for x in records under
            # 'native_sumo_safety_interventions'.
            "native_sumo_safety_interventions": sum(
                # Evaluate x at 'native_sumo_safety_interventions' as part of the enclosing expression.
                x["native_sumo_safety_interventions"] for x in records),
            # Store the sum of a lazy sequence of x at 'learned_proposer_actions' for x in records under
            # 'learned_proposer_actions'.
            "learned_proposer_actions": sum(
                # Evaluate x at 'learned_proposer_actions' as part of the enclosing expression.
                x["learned_proposer_actions"] for x in records),
            # Store the sum of a lazy sequence of x at 'learned_responder_actions' for x in records under
            # 'learned_responder_actions'.
            "learned_responder_actions": sum(
                # Evaluate x at 'learned_responder_actions' as part of the enclosing expression.
                x["learned_responder_actions"] for x in records),
            # Store the sum of a lazy sequence of a Boolean built from x at 'unresolved_coordination_case' for x
            # in records under 'unresolved_coordination_cases'.
            "unresolved_coordination_cases": sum(
                # Evaluate a Boolean built from x at 'unresolved_coordination_case' as part of the enclosing
                # expression.
                bool(x["unresolved_coordination_case"]) for x in records),
            # Store the sum of a lazy sequence of x at 'runtime_seconds' for x in records under 'runtime_seconds'.
            "runtime_seconds": sum(x["runtime_seconds"] for x in records)}


# Hard safety failure record using the inputs and processing steps below.
# Input scenario_id: the supplied scenario id.
# Input error: the supplied error.
# Output: a dictionary containing scenario_id, status, hard_validity_eligible, safety_failure_type,...
# Processing: select branches using the stated conditions.
def _hard_safety_failure_record(scenario_id, error):
    # Run this branch when error.code does not belong to a set containing the text
    # 'BLOCKED_VEHICLE_ENTERED_CONFLICT_ZONE', the text 'PHYSICAL_CAUSAL_BRANCH_COLLISION_OBSERVED'.
    if error.code not in {
            "BLOCKED_VEHICLE_ENTERED_CONFLICT_ZONE",
            "PHYSICAL_CAUSAL_BRANCH_COLLISION_OBSERVED"}:
        # Raise error to stop this execution path.
        raise error
    # Set evidence to the result of serializable(error.evidence).
    evidence = serializable(error.evidence)
    # Set provenance to a dictionary containing exception_type, failure_message, raw_evidence.
    provenance = {"exception_type": type(error).__name__,
                  # Store a string built from error under 'failure_message'.
                  # Store evidence under 'raw_evidence'.
                  "failure_message": str(error), "raw_evidence": evidence}
    # Run this branch when error.code equals the text 'BLOCKED_VEHICLE_ENTERED_CONFLICT_ZONE' and evidence.
    if error.code == "BLOCKED_VEHICLE_ENTERED_CONFLICT_ZONE" and evidence:
        # Update provenance with the supplied entries.
        provenance.update({"vehicle_id": evidence[0],
                           # Store evidence at 1 under 'conflict_zone_id'.
                           "conflict_zone_id": evidence[1],
                           # Store evidence at 2 under 'simulation_time'.
                           "simulation_time": evidence[2]})
    # Run this branch when error.code equals the text 'PHYSICAL_CAUSAL_BRANCH_COLLISION_OBSERVED' and evidence.
    elif error.code == "PHYSICAL_CAUSAL_BRANCH_COLLISION_OBSERVED" and evidence:
        # Update provenance with the supplied entries.
        provenance.update({"simulation_time": evidence[0],
                           # Store evidence at 1 under 'vehicle_ids'.
                           "vehicle_ids": evidence[1]})
    # Return a dictionary containing scenario_id, status, hard_validity_eligible, safety_failure_type,... to the
    # caller.
    return {"scenario_id": serializable(scenario_id),
            "status": "HARD_SAFETY_FAILURE",
            # Store False under 'hard_validity_eligible'.
            "hard_validity_eligible": False,
            # Store error.code under 'safety_failure_type'.
            "safety_failure_type": error.code,
            # Store provenance under 'safety_failure_provenance'.
            "safety_failure_provenance": provenance,
            # Store None under 'total_team_travel_time_seconds'.
            "total_team_travel_time_seconds": None}


# Baseline summary using the inputs and processing steps below.
# Input records: the supplied records.
# Output: result.
def _baseline_summary(records):
    # Set completed to a list of x for x in records; retain entries satisfying 'status' from x; use None if absent
    # differs from the text 'HARD_SAFETY_FAILURE'.
    completed = [x for x in records if x.get("status") !=
                 "HARD_SAFETY_FAILURE"]
    # Set failures to a list of x for x in records; retain entries satisfying 'status' from x; use None if absent
    # equals the text 'HARD_SAFETY_FAILURE'.
    failures = [x for x in records if x.get("status") ==
                "HARD_SAFETY_FAILURE"]
    # Set result to the result of _summary(completed) when completed, otherwise a dictionary containing
    # scenario_execution_count, total, mean, median, standard_deviation, minimum, maximum,...
    result = (_summary(completed) if completed else {
        # Store 0 under 'scenario_execution_count'.
        # Store None under 'total'.
        # Store None under 'mean'.
        "scenario_execution_count": 0, "total": None, "mean": None,
        # Store None under 'median'.
        # Store None under 'standard_deviation'.
        # Store None under 'minimum'.
        "median": None, "standard_deviation": None, "minimum": None,
        # Store None under 'maximum'.
        # Store 0 under 'completed_vehicles'.
        # Store 0 under 'collisions'.
        "maximum": None, "completed_vehicles": 0, "collisions": 0,
        # Store 0 under 'blocked_zone_violations'.
        "blocked_zone_violations": 0,
        # Store 0 under 'native_sumo_safety_interventions'.
        "native_sumo_safety_interventions": 0,
        # Store 0 under 'learned_proposer_actions'.
        # Store 0 under 'learned_responder_actions'.
        "learned_proposer_actions": 0, "learned_responder_actions": 0,
        # Store 0 under 'unresolved_coordination_cases'.
        # Store 0 under 'runtime_seconds'.
        "unresolved_coordination_cases": 0, "runtime_seconds": 0})
    # Update result with the supplied entries.
    result.update({
        # Store the number of entries in records under 'scenario_count'.
        "scenario_count": len(records),
        # Store the number of entries in completed under 'completed_episode_count'.
        "completed_episode_count": len(completed),
        # Store the number of entries in failures under 'hard_safety_failure_count'.
        "hard_safety_failure_count": len(failures),
        # Store the sum of a lazy sequence of x at 'safety_failure_type' equals the text
        # 'BLOCKED_VEHICLE_ENTERED_CONFLICT_ZONE' for x in failures under 'blocked_zone_failure_count'.
        "blocked_zone_failure_count": sum(
            # Evaluate x at 'safety_failure_type' equals the text 'BLOCKED_VEHICLE_ENTERED_CONFLICT_ZONE' as part
            # of the enclosing expression.
            x["safety_failure_type"] ==
            # Evaluate failures as part of the enclosing expression.
            "BLOCKED_VEHICLE_ENTERED_CONFLICT_ZONE" for x in failures),
        # Store the sum of a lazy sequence of x at 'safety_failure_type' equals the text
        # 'PHYSICAL_CAUSAL_BRANCH_COLLISION_OBSERVED' for x in failures under 'collision_failure_count'.
        "collision_failure_count": sum(
            # Evaluate x at 'safety_failure_type' equals the text 'PHYSICAL_CAUSAL_BRANCH_COLLISION_OBSERVED' as
            # part of the enclosing expression.
            x["safety_failure_type"] ==
            # Evaluate failures as part of the enclosing expression.
            "PHYSICAL_CAUSAL_BRANCH_COLLISION_OBSERVED" for x in failures),
        # Store the sum of a lazy sequence of a Boolean built from 'unresolved_coordination_case' from x; use None
        # if absent for x in completed under 'unresolved_coordination_case_count'.
        "unresolved_coordination_case_count": sum(
            # Evaluate a Boolean built from 'unresolved_coordination_case' from x; use None if absent as part of
            # the enclosing expression.
            bool(x.get("unresolved_coordination_case")) for x in completed),
        # Store the negation of failures under 'safety_eligible'.
        "safety_eligible": not failures,
        # Store a list of x at 'scenario_id' for x in failures under 'hard_safety_failure_scenario_ids'.
        "hard_safety_failure_scenario_ids": [
            # Evaluate x at 'scenario_id' as part of the enclosing expression.
            x["scenario_id"] for x in failures],
        # Store the text 'COMPLETED_BASELINE_EPISODES_ONLY' when failures, otherwise the text
        # 'ALL_BASELINE_EPISODES' under 'travel_time_scope'.
        "travel_time_scope": (
            # Evaluate the text 'COMPLETED_BASELINE_EPISODES_ONLY' when failures, otherwise the text
            # 'ALL_BASELINE_EPISODES' as part of the enclosing expression.
            "COMPLETED_BASELINE_EPISODES_ONLY" if failures else
            "ALL_BASELINE_EPISODES")})
    # Return result to the caller.
    return result


# Eligible using the inputs and processing steps below.
# Input records: the supplied records.
# Output: whether every item is true in a lazy sequence of x['collisions'] equals 0 and
# x['blocked_zone_violations'] equals 0 and x['hard_mask_violations'] equals 0 and...
def _eligible(records):
    # Return whether every item is true in a lazy sequence of x['collisions'] equals 0 and
    # x['blocked_zone_violations'] equals 0 and x['hard_mask_violations'] equals 0 and
    # x['regulatory_invariant_violations'] equals 0 and x['protocol_invariant_failures'] equals 0 and
    # x['route_truth_actor_fields_consumed'] equals 0 and whether every item is true in
    # x['hard_validity_gate_results'].values() and whether x['total_team_travel_time_seconds'] contains finite
    # numeric values for x in records to the caller.
    return (all(x["collisions"] == 0 and x["blocked_zone_violations"] == 0
                # Evaluate x at 'hard_mask_violations' equals 0 as part of the enclosing expression.
                and x["hard_mask_violations"] == 0
                # Evaluate x at 'regulatory_invariant_violations' equals 0 as part of the enclosing expression.
                and x["regulatory_invariant_violations"] == 0
                # Evaluate x at 'protocol_invariant_failures' equals 0 as part of the enclosing expression.
                and x["protocol_invariant_failures"] == 0
                # Evaluate x at 'route_truth_actor_fields_consumed' equals 0 as part of the enclosing expression.
                and x["route_truth_actor_fields_consumed"] == 0
                # Evaluate whether every item is true in values from x['hard_validity_gate_results'] as part of
                # the enclosing expression.
                and all(x["hard_validity_gate_results"].values())
                # Evaluate whether x at 'total_team_travel_time_seconds' contains finite numeric values as part of
                # the enclosing expression.
                and math.isfinite(x["total_team_travel_time_seconds"])
                # Evaluate records as part of the enclosing expression.
                for x in records))


# Validate using the inputs and processing steps below.
# Input root: the base directory used to resolve files.
# Input resume: the supplied resume.
# Output: payload.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def validate(root=OUTPUT_ROOT, resume=False):
    # Call prepare with the supplied arguments.
    # Set root to the result of Path(root).
    # Set design to the result of build_design().
    prepare(root); root = Path(root); design = build_design()
    # Set manifest to design['manifests'] at ScenarioRole.VALIDATION.
    manifest = design["manifests"][ScenarioRole.VALIDATION]
    # Set candidates to an empty dictionary.
    candidates = {}
    # Iterate over the result of candidate_configurations(design), binding each item to candidate.
    for candidate in candidate_configurations(design):
        # Set replications to an empty list.
        replications = []
        # Iterate over the integer range defined by REPLICATION_COUNT, binding each item to replication_index.
        for replication_index in range(REPLICATION_COUNT):
            # Set checkpoint to root joined with the path segment 'training' divided by candidate.candidate_id divided by
            # formatted text built from the embedded values.
            checkpoint = root / "training" / candidate.candidate_id / (
                # Evaluate formatted text built from the embedded values as part of the enclosing expression.
                f"replication_{replication_index}_state_{UPDATE_HORIZON}.pt")
            # Run this branch when the negation of whether checkpoint exists.
            if not checkpoint.exists():
                # Raise FileNotFoundError with formatted text built from the embedded values to stop this
                # execution path.
                raise FileNotFoundError(f"Missing training checkpoint: {checkpoint}")
            # Set output to root joined with the path segment 'validation' divided by candidate.candidate_id divided by
            # formatted text built from the embedded values.
            output = root / "validation" / candidate.candidate_id / (
                # Evaluate formatted text built from the embedded values as part of the enclosing expression.
                f"replication_{replication_index}.json")
            # Run this branch when resume and whether output exists.
            if resume and output.exists():
                # Set record to the decoded data produced by json.loads from the text read from output.
                record = json.loads(output.read_text(encoding="utf-8"))
            # Run this alternative branch when the preceding branch does not apply.
            else:
                # Set scenarios to the result of _evaluate_manifest(checkpoint, manifest, design,
                # ScenarioRole.VALIDATION, replication_index).
                scenarios = _evaluate_manifest(
                    # Supply ScenarioRole.VALIDATION to _evaluate_manifest.
                    checkpoint, manifest, design, ScenarioRole.VALIDATION,
                    # Supply replication_index to _evaluate_manifest.
                    replication_index)
                # Set record to a dictionary containing candidate_id, replication_index, data_role,
                # training_operations, scenario_results, summary.
                record = {"candidate_id": candidate.candidate_id,
                    # Store replication_index under 'replication_index'.
                    "replication_index": replication_index,
                    # Store the text 'VALIDATION' under 'data_role'.
                    # Store 0 under 'training_operations'.
                    "data_role": "VALIDATION", "training_operations": 0,
                    # Store scenarios under 'scenario_results'.
                    # Store the result of _summary(scenarios) under 'summary'.
                    "scenario_results": scenarios, "summary": _summary(scenarios)}
                # Call atomic_write_json with the supplied arguments.
                atomic_write_json(output, record)
            # Append record to replications.
            replications.append(record)
        # Set all_records to a list of x for rep in replications.
        all_records = [x for rep in replications for x in rep["scenario_results"]]
        # Set replication_totals to a list of item['summary'] at 'total' for item in replications.
        replication_totals = [
            # Evaluate item['summary'] at 'total' as part of the enclosing expression.
            item["summary"]["total"] for item in replications
        ]
        # Set candidate_summary to the result of _summary(all_records).
        candidate_summary = _summary(all_records)
        # Update candidate_summary with the supplied entries.
        candidate_summary.update({
            # Store replication_totals under 'replication_total_team_travel_time_seconds'.
            "replication_total_team_travel_time_seconds": replication_totals,
            # Store the result of mean(replication_totals) under
            # 'mean_replication_total_team_travel_time_seconds'.
            "mean_replication_total_team_travel_time_seconds": mean(
                # Supply replication_totals to mean.
                replication_totals),
            # Store the result of median(replication_totals) under
            # 'median_replication_total_team_travel_time_seconds'.
            "median_replication_total_team_travel_time_seconds": median(
                # Supply replication_totals to median.
                replication_totals),
            # Store the result of pstdev(replication_totals) under 'replication_total_standard_deviation'.
            "replication_total_standard_deviation": pstdev(replication_totals),
            # Store the minimum of replication_totals under 'replication_total_minimum'.
            "replication_total_minimum": min(replication_totals),
            # Store the maximum of replication_totals under 'replication_total_maximum'.
            "replication_total_maximum": max(replication_totals),
        })
        # Set candidates[candidate.candidate_id] to a dictionary containing candidate_id, configuration_hash,
        # replications, summary, eligible, hard_gate_result.
        candidates[candidate.candidate_id] = {
            # Store candidate.candidate_id under 'candidate_id'.
            "candidate_id": candidate.candidate_id,
            # Store candidate.configuration_hash under 'configuration_hash'.
            "configuration_hash": candidate.configuration_hash,
            # Store replications under 'replications'.
            # Store candidate_summary under 'summary'.
            "replications": replications, "summary": candidate_summary,
            # Store the result of _eligible(all_records) under 'eligible'.
            "eligible": _eligible(all_records),
            # Store the text 'ELIGIBLE' when the result of _eligible(all_records), otherwise the text 'INELIGIBLE'
            # under 'hard_gate_result'.
            "hard_gate_result": "ELIGIBLE" if _eligible(all_records)
                                # Supply the text 'INELIGIBLE' to the enclosing expression.
                                else "INELIGIBLE"}
    # Set payload to a dictionary containing protocol_id, data_role, held_out_consumed, candidates,
    # paired_descriptive_uncertainty.
    payload = {"protocol_id": PROTOCOL_ID, "data_role": "VALIDATION",
               # Store False under 'held_out_consumed'.
               # Store candidates under 'candidates'.
               "held_out_consumed": False, "candidates": candidates,
               "paired_descriptive_uncertainty":
                   # Evaluate the result of _paired_uncertainty(candidates) as part of the enclosing expression.
                   _paired_uncertainty(candidates)}
    # Call atomic_write_json with the supplied arguments.
    atomic_write_json(root / "comparison" /
                      # Supply payload to atomic_write_json.
                      "candidate_validation_summary.json", payload)
    # Call _write_candidate_csv with the supplied arguments.
    _write_candidate_csv(root, candidates)
    # Return payload to the caller.
    return payload


# Write candidate csv using the inputs and processing steps below.
# Input root: the base directory used to resolve files.
# Input candidates: the supplied candidates.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def _write_candidate_csv(root, candidates):
    # Set path to the result of Path(root) joined with the path segment 'comparison' joined with the path segment
    # 'candidate_validation_summary.csv'.
    path = Path(root) / "comparison" / "candidate_validation_summary.csv"
    # Create the directory requested by path.parent.
    path.parent.mkdir(parents=True, exist_ok=True)
    # Set temporary to the result of path.with_suffix(the text '.csv.tmp').
    temporary = path.with_suffix(".csv.tmp")
    # Enter the result of temporary.open(the text 'w') as handle and run the enclosed operations within that
    # context.
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        # Set writer to the result of csv.writer(handle).
        # Call writer.writerow with the supplied arguments.
        writer = csv.writer(handle); writer.writerow([
            "candidate", "mean_validation_ttt", "median", "sd", "collisions",
            "blocked_zone_violations", "eligible"])
        # Iterate over key/value pairs from candidates, binding each item to (key, item).
        for key, item in candidates.items():
            # Set s to item at 'summary'.
            # Call writer.writerow with the supplied arguments.
            s = item["summary"]; writer.writerow([key,
                # Include s at 'mean_replication_total_team_travel_time_seconds' in this list.
                s["mean_replication_total_team_travel_time_seconds"],
                # Include s at 'median_replication_total_team_travel_time_seconds' in this list.
                s["median_replication_total_team_travel_time_seconds"],
                # Include s at 'replication_total_standard_deviation' in this list.
                s["replication_total_standard_deviation"], s["collisions"],
                # Include s at 'blocked_zone_violations' in this list.
                s["blocked_zone_violations"], item["eligible"]])
    # Call os.replace with the supplied arguments.
    os.replace(temporary, path)


# Deterministic paired bootstrap over matched replication totals.
# Input candidates: the supplied candidates.
# Output: result.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def _paired_uncertainty(candidates):
    """Deterministic paired bootstrap over matched replication totals."""
    # Set reference to candidates[REFERENCE_CANDIDATE]['summary'] at 'replication_total_team_travel_time_seconds'.
    reference = candidates[REFERENCE_CANDIDATE]["summary"][
        "replication_total_team_travel_time_seconds"]
    # Set result to an empty dictionary.
    result = {}
    # Iterate over key/value pairs from candidates, binding each item to (candidate_id, item).
    for candidate_id, item in candidates.items():
        # Run this branch when candidate_id equals REFERENCE_CANDIDATE.
        if candidate_id == REFERENCE_CANDIDATE:
            # Skip the rest of this loop iteration and process the next item.
            continue
        # Set values to item['summary'] at 'replication_total_team_travel_time_seconds'.
        values = item["summary"][
            "replication_total_team_travel_time_seconds"]
        # Set differences to a list of a minus b for (a, b) in corresponding items paired from values, reference.
        differences = [a - b for a, b in zip(values, reference)]
        # Set generator to the result of random.Random(BOOTSTRAP_SEED multiplied by 1000 plus CANDIDATE_EPOCHS at
        # candidate_id).
        generator = random.Random((BOOTSTRAP_SEED * 1000) +
                                  # Evaluate CANDIDATE_EPOCHS at candidate_id as part of the enclosing expression.
                                  CANDIDATE_EPOCHS[candidate_id])
        # Set boot to the sorted values from a lazy sequence of the result of mean(a list of
        # differences[generator.randrange(len(differences))] for _ in differences) for _ in the integer range
        # defined by BOOTSTRAP_RESAMPLES.
        boot = sorted(mean([differences[generator.randrange(len(differences))]
                            # Evaluate differences as part of the enclosing expression.
                            for _ in differences])
                      # Evaluate the integer range defined by BOOTSTRAP_RESAMPLES as part of the enclosing
                      # expression.
                      for _ in range(BOOTSTRAP_RESAMPLES))
        # Set lower to boot at int(0.025 * (len(boot) - 1)).
        lower = boot[int(0.025 * (len(boot) - 1))]
        # Set upper to boot at int(0.975 * (len(boot) - 1)).
        upper = boot[int(0.975 * (len(boot) - 1))]
        # Set result[f'{candidate_id}_minus_{REFERENCE_CANDIDATE}'] to a dictionary containing
        # matched_replication_differences_seconds, paired_mean_difference_seconds,...
        result[f"{candidate_id}_minus_{REFERENCE_CANDIDATE}"] = {
            # Store differences under 'matched_replication_differences_seconds'.
            "matched_replication_differences_seconds": differences,
            # Store the result of mean(differences) under 'paired_mean_difference_seconds'.
            "paired_mean_difference_seconds": mean(differences),
            # Store the result of median(differences) under 'paired_median_difference_seconds'.
            "paired_median_difference_seconds": median(differences),
            # Store a list containing lower, upper under 'descriptive_bootstrap_95_percent_interval'.
            "descriptive_bootstrap_95_percent_interval": [lower, upper],
            # Store BOOTSTRAP_SEED under 'bootstrap_seed'.
            "bootstrap_seed": BOOTSTRAP_SEED,
            # Store BOOTSTRAP_RESAMPLES under 'bootstrap_resamples'.
            "bootstrap_resamples": BOOTSTRAP_RESAMPLES,
            # Store False under 'statistical_significance_claim'.
            "statistical_significance_claim": False,
        }
    # Return result to the caller.
    return result


# Select using the inputs and processing steps below.
# Input root: the base directory used to resolve files.
# Output: return the value selected by the matching return branch below.
# Processing: select branches using the stated conditions.
def select(root=OUTPUT_ROOT):
    # Set root to the result of Path(root).
    root = Path(root)
    # Set frozen_path to root joined with the path segment 'selected_configuration.json'.
    frozen_path = root / "selected_configuration.json"
    # Run this branch when whether frozen_path exists.
    if frozen_path.exists():
        # Set frozen to the decoded data produced by json.loads from the text read from frozen_path.
        frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
        # Run this branch when 'status' from frozen; use None if absent differs from the text 'SELECTION_FROZEN'.
        if frozen.get("status") != "SELECTION_FROZEN":
            # Raise ValueError with the text 'INVALID_EXISTING_SELECTION_ARTIFACT' to stop this execution path.
            raise ValueError("INVALID_EXISTING_SELECTION_ARTIFACT")
        # Return frozen to the caller.
        return frozen
    # Set source to root joined with the path segment 'comparison' joined with the path segment 'candidate_validation_summary.json'.
    source = root / "comparison" / "candidate_validation_summary.json"
    # Run this branch when the negation of whether source exists.
    if not source.exists():
        # Raise FileNotFoundError with the text 'Validation must finish before selection' to stop this execution
        # path.
        raise FileNotFoundError("Validation must finish before selection")
    # Set validation to the decoded data produced by json.loads from the text read from source.
    validation = json.loads(source.read_text(encoding="utf-8"))
    # Run this branch when 'data_role' from validation; use None if absent differs from the text 'VALIDATION' or
    # 'held_out_consumed' from validation; use None if absent is a different object from False.
    if validation.get("data_role") != "VALIDATION" or validation.get(
            # Supply False to the enclosing expression.
            "held_out_consumed") is not False:
        # Raise ValueError with the text 'SELECTION_DATA_BOUNDARY_VIOLATION' to stop this execution path.
        raise ValueError("SELECTION_DATA_BOUNDARY_VIOLATION")
    # Set eligible to a dictionary of key mapped to value for (key, value) in key/value pairs from
    # validation['candidates']; retain entries satisfying value at 'eligible'.
    eligible = {key: value for key, value in validation["candidates"].items()
                # Evaluate value at 'eligible' as part of the enclosing expression.
                if value["eligible"]}
    # Run this branch when the negation of eligible.
    if not eligible:
        # Raise RuntimeError with the text 'NO_ELIGIBLE_FINAL_MAPPO_CANDIDATE' to stop this execution path.
        raise RuntimeError("NO_ELIGIBLE_FINAL_MAPPO_CANDIDATE")
    # Selection mean using the inputs and processing steps below.
    # Input item: the supplied item.
    # Output: 'mean_replication_total_team_travel_time_seconds' from item['summary']; use item['summary'] at
    # 'mean' if absent.
    def selection_mean(item):
        # Return 'mean_replication_total_team_travel_time_seconds' from item['summary']; use item['summary'] at
        # 'mean' if absent to the caller.
        return item["summary"].get(
            "mean_replication_total_team_travel_time_seconds",
            # Supply item['summary'] at 'mean' to item['summary'].get.
            item["summary"]["mean"])
    # Set best_mean to the minimum of a lazy sequence of the result of selection_mean(x) for x in values from
    # eligible.
    best_mean = min(selection_mean(x) for x in eligible.values())
    # Set tied to the sorted values from a lazy sequence of key for (key, x) in key/value pairs from eligible;
    # retain entries satisfying the result of selection_mean(x) equals best_mean.
    tied = sorted(key for key, x in eligible.items()
                  # Evaluate the result of selection_mean(x) equals best_mean as part of the enclosing expression.
                  if selection_mean(x) == best_mean)
    # Set selected to REFERENCE_CANDIDATE when REFERENCE_CANDIDATE belongs to tied, otherwise tied at 0.
    selected = REFERENCE_CANDIDATE if REFERENCE_CANDIDATE in tied else tied[0]
    # Set candidate to the next item from a lazy sequence of x for x in the result of candidate_configurations();
    # retain entries satisfying x.candidate_id equals selected.
    candidate = next(x for x in candidate_configurations()
                     # Evaluate x.candidate_id equals selected as part of the enclosing expression.
                     if x.candidate_id == selected)
    # Set checkpoint to root joined with the path segment 'training' divided by selected joined with the path segment
    # 'replication_0_state_2.pt'.
    checkpoint = root / "training" / selected / "replication_0_state_2.pt"
    # Set selected_policy to root joined with the path segment 'selected_policy.pt'.
    selected_policy = root / "selected_policy.pt"
    # Set temporary to the result of selected_policy.with_suffix(the text '.pt.tmp').
    temporary = selected_policy.with_suffix(".pt.tmp")
    # Call shutil.copyfile with the supplied arguments.
    # Call os.replace with the supplied arguments.
    shutil.copyfile(checkpoint, temporary); os.replace(temporary, selected_policy)
    # Set payload to a dictionary containing protocol_id, status, selected_candidate_id, selection_reason,
    # selection_timestamp_utc,...
    payload = {"protocol_id": PROTOCOL_ID, "status": "SELECTION_FROZEN",
        # Store selected under 'selected_candidate_id'.
        "selected_candidate_id": selected,
        "selection_reason": "LOWEST_MEAN_VALIDATION_TTT_AMONG_ELIGIBLE",
        # Store the result of datetime.now(timezone.utc).isoformat() under 'selection_timestamp_utc'.
        "selection_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        # Store the result of serializable(candidate.__dict__) under 'candidate_configuration'.
        "candidate_configuration": serializable(candidate.__dict__),
        # Store candidate.configuration_hash under 'candidate_configuration_hash'.
        "candidate_configuration_hash": candidate.configuration_hash,
        # Store a dictionary of a string built from i mapped to the result of file_sha256(root / 'training'
        # divided by selected divided by formatted text built from the embedded values) for i in the integer range
        # defined by REPLICATION_COUNT under 'training_checkpoint_hashes'.
        "training_checkpoint_hashes": {
            # Evaluate the result of file_sha256(root joined with the path segment 'training' divided by selected divided by
            # formatted text built from the embedded...) as part of the enclosing expression.
            str(i): file_sha256(root / "training" / selected /
                # Evaluate formatted text built from the embedded values as part of the enclosing expression.
                f"replication_{i}_state_2.pt") for i in range(REPLICATION_COUNT)},
        # Store True under 'configuration_selected_by_validation'.
        "configuration_selected_by_validation": True,
        "selection_data_role": "VALIDATION",
        # Store False under 'held_out_used_for_selection'.
        "held_out_used_for_selection": False,
        # Store False under 'globally_optimal_claim'.
        "globally_optimal_claim": False,
        # Store False under 'exhaustive_hyperparameter_search'.
        "exhaustive_hyperparameter_search": False,
        # Store True under 'selected_best_among_tested_candidates'.
        "selected_best_among_tested_candidates": True,
        # Store False under 'demo_replication_selected_by_performance'.
        "demo_replication_selected_by_performance": False,
        "demo_replication_rule": "CANONICAL_REPLICATION_0",
        # Store the result of str(checkpoint).replace(the text '\\', the text '/') under 'selected_policy_source'.
        "selected_policy_source": str(checkpoint).replace("\\", "/"),
        # Store the result of file_sha256(selected_policy) under 'selected_policy_sha256'.
        "selected_policy_sha256": file_sha256(selected_policy),
        # Store the result of file_sha256(checkpoint) under 'source_checkpoint_sha256'.
        "source_checkpoint_sha256": file_sha256(checkpoint)}
    # Call atomic_write_json with the supplied arguments.
    atomic_write_json(frozen_path, payload)
    # Return payload to the caller.
    return payload


# Heldout using the inputs and processing steps below.
# Input root: the base directory used to resolve files.
# Input resume: the supplied resume.
# Output: return the value selected by the matching return branch below.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def heldout(root=OUTPUT_ROOT, resume=False):
    # Set root to the result of Path(root).
    # Set selected_path to root joined with the path segment 'selected_configuration.json'.
    root = Path(root); selected_path = root / "selected_configuration.json"
    # Run this branch when the negation of whether selected_path exists.
    if not selected_path.exists():
        # Raise RuntimeError with the text 'HELD_OUT_LOCKED_SELECTION_NOT_FROZEN' to stop this execution path.
        raise RuntimeError("HELD_OUT_LOCKED_SELECTION_NOT_FROZEN")
    # Set selected to the decoded data produced by json.loads from the text read from selected_path.
    selected = json.loads(selected_path.read_text(encoding="utf-8"))
    # Run this branch when 'status' from selected; use None if absent differs from the text 'SELECTION_FROZEN'.
    if selected.get("status") != "SELECTION_FROZEN":
        # Raise RuntimeError with the text 'HELD_OUT_LOCKED_SELECTION_NOT_FROZEN' to stop this execution path.
        raise RuntimeError("HELD_OUT_LOCKED_SELECTION_NOT_FROZEN")
    # Set output_path to root joined with the path segment 'held_out' joined with the path segment 'selected_mappo_results.json'.
    output_path = root / "held_out" / "selected_mappo_results.json"
    # Run this branch when resume and whether output_path exists.
    if resume and output_path.exists():
        # Return the decoded data produced by json.loads from the text read from output_path to the caller.
        return json.loads(output_path.read_text(encoding="utf-8"))
    # Set design to the result of build_design().
    # Set manifest to design['manifests'] at ScenarioRole.HELD_OUT_TEST.
    design = build_design(); manifest = design["manifests"][ScenarioRole.HELD_OUT_TEST]
    # Set replications to an empty list.
    replications = []
    # Iterate over the integer range defined by REPLICATION_COUNT, binding each item to index.
    for index in range(REPLICATION_COUNT):
        # Set checkpoint to root joined with the path segment 'training' divided by selected at 'selected_candidate_id'
        # divided by formatted text built from the embedded values.
        checkpoint = root / "training" / selected["selected_candidate_id"] / (
            # Evaluate formatted text built from the embedded values as part of the enclosing expression.
            f"replication_{index}_state_2.pt")
        # Set scenarios to the result of _evaluate_manifest(checkpoint, manifest, design,
        # ScenarioRole.HELD_OUT_TEST, index).
        scenarios = _evaluate_manifest(
            # Supply ScenarioRole.HELD_OUT_TEST to _evaluate_manifest.
            checkpoint, manifest, design, ScenarioRole.HELD_OUT_TEST, index)
        # Append a dictionary containing replication_index, scenario_results, summary to replications.
        replications.append({"replication_index": index,
                             # Store scenarios under 'scenario_results'.
                             "scenario_results": scenarios,
                             # Store the result of _summary(scenarios) under 'summary'.
                             "summary": _summary(scenarios)})
    # Set all_records to a list of x for rep in replications.
    all_records = [x for rep in replications for x in rep["scenario_results"]]
    # Set payload to a dictionary containing protocol_id, status, selected_candidate_id, replications, summary,...
    payload = {"protocol_id": PROTOCOL_ID, "status": "HELD_OUT_COMPLETE",
        # Store selected at 'selected_candidate_id' under 'selected_candidate_id'.
        "selected_candidate_id": selected["selected_candidate_id"],
        # Store replications under 'replications'.
        # Store the result of _summary(all_records) under 'summary'.
        "replications": replications, "summary": _summary(all_records),
        # Store False under 'held_out_used_for_training'.
        "held_out_used_for_training": False,
        # Store False under 'held_out_used_for_validation_selection'.
        "held_out_used_for_validation_selection": False,
        # Store False under 'held_out_used_for_candidate_selection'.
        "held_out_used_for_candidate_selection": False,
        # Store False under 'held_out_used_for_tie_breaking'.
        "held_out_used_for_tie_breaking": False,
        # Store 0 under 'training_operations'.
        "training_operations": 0}
    # Call atomic_write_json with the supplied arguments.
    atomic_write_json(output_path, payload)
    # Return payload to the caller.
    return payload


# Baseline using the inputs and processing steps below.
# Input root: the base directory used to resolve files.
# Input resume: the supplied resume.
# Output: return the value selected by the matching return branch below.
# Processing: iterate over the relevant records, then select branches using the stated conditions, then handle the
# specified errors.
def baseline(root=OUTPUT_ROOT, resume=False):
    # Set root to the result of Path(root).
    root = Path(root)
    # Run this branch when the negation of whether (root / 'selected_configuration.json') exists.
    if not (root / "selected_configuration.json").exists():
        # Raise RuntimeError with the text 'BASELINE_REQUIRES_FROZEN_SELECTION' to stop this execution path.
        raise RuntimeError("BASELINE_REQUIRES_FROZEN_SELECTION")
    # Set output_path to root joined with the path segment 'held_out' joined with the path segment 'baseline_results.json'.
    output_path = root / "held_out" / "baseline_results.json"
    # Set design to the result of build_design().
    # Set manifest to design['manifests'] at ScenarioRole.HELD_OUT_TEST.
    design = build_design(); manifest = design["manifests"][ScenarioRole.HELD_OUT_TEST]
    # Run this branch when resume and whether output_path exists.
    if resume and output_path.exists():
        # Set stored to the decoded data produced by json.loads from the text read from output_path.
        stored = json.loads(output_path.read_text(encoding="utf-8"))
        # Set expected to a list of the result of serializable(x) for x in manifest.scenario_ids.
        expected = [serializable(x) for x in manifest.scenario_ids]
        # Set actual to a list of 'scenario_id' from x; use None if absent for x in 'scenario_results' from
        # stored; use an empty list if absent.
        actual = [x.get("scenario_id") for x in
                  # Evaluate 'scenario_results' from stored; use an empty list if absent as part of the enclosing
                  # expression.
                  stored.get("scenario_results", [])]
        # Run this branch when actual differs from expected.
        if actual != expected:
            # Raise RuntimeError with the text 'BASELINE_RESUME_MANIFEST_ACCOUNTING_MISMATCH' to stop this
            # execution path.
            raise RuntimeError("BASELINE_RESUME_MANIFEST_ACCOUNTING_MISMATCH")
        # Return stored to the caller.
        return stored
    # Set provider to the result of DeterministicNoNegotiationRegulatoryBaseline().
    provider = DeterministicNoNegotiationRegulatoryBaseline()
    # Set progress to root joined with the path segment 'held_out' joined with the path segment 'baseline_scenario_records'.
    progress = root / "held_out" / "baseline_scenario_records"
    # Create the directory requested by progress.
    progress.mkdir(parents=True, exist_ok=True)
    # Set records to an empty list.
    records = []
    # Iterate over index/value pairs from manifest.scenario_ids, binding each item to (index, sid).
    for index, sid in enumerate(manifest.scenario_ids):
        # Set scenario_path to progress divided by formatted text built from the embedded values.
        scenario_path = progress / f"scenario_{index:03d}.json"
        # Run this branch when resume and whether scenario_path exists.
        if resume and scenario_path.exists():
            # Set stored to the decoded data produced by json.loads from the text read from scenario_path.
            stored = json.loads(scenario_path.read_text(encoding="utf-8"))
            # Run this branch when 'scenario_id' from stored; use None if absent differs from the result of
            # serializable(sid).
            if stored.get("scenario_id") != serializable(sid):
                # Raise RuntimeError with the text 'BASELINE_RESUME_SCENARIO_IDENTITY_MISMATCH' to stop this
                # execution path.
                raise RuntimeError("BASELINE_RESUME_SCENARIO_IDENTITY_MISMATCH")
            # Append stored to records.
            records.append(stored)
            # Skip the rest of this loop iteration and process the next item.
            continue
        # Attempt the enclosed operations and route matching exceptions to the handlers below.
        try:
            # Set episode to the result of CoupledNegotiationTrainingEnvironment(provider).run_episode(the result
            # of _specification(design at 'payload', sid), manifest.manifest_id).
            episode = CoupledNegotiationTrainingEnvironment(provider).run_episode(
                # Supply the result of _specification(design at 'payload', sid) to
                # CoupledNegotiationTrainingEnvironment(provider).run_episode.
                _specification(design["payload"], sid), manifest.manifest_id)
            # Set record to the result of _episode_record(episode, the text 'BASELINE').
            record = _episode_record(episode, "BASELINE")
        # Handle PhysicalReplayError as error using the recovery steps below.
        except PhysicalReplayError as error:
            # Set record to the result of _hard_safety_failure_record(sid, error).
            record = _hard_safety_failure_record(sid, error)
        # Call atomic_write_json with the supplied arguments.
        atomic_write_json(scenario_path, record)
        # Append record to records.
        records.append(record)
    # Set payload to a dictionary containing protocol_id, baseline_id, same_physical_environment,
    # scenario_manifest_identity,...
    payload = {"protocol_id": PROTOCOL_ID,
        # Store provider.selection_rule under 'baseline_id'.
        "baseline_id": provider.selection_rule,
        # Store True under 'same_physical_environment'.
        "same_physical_environment": True,
        # Store the result of serializable(manifest.manifest_id) under 'scenario_manifest_identity'.
        "scenario_manifest_identity": serializable(manifest.manifest_id),
        # Store 0 under 'neural_actor_calls'.
        # Store False under 'reward_used_for_action_selection'.
        "neural_actor_calls": 0, "reward_used_for_action_selection": False,
        # Store False under 'future_outcome_used_for_action_selection'.
        "future_outcome_used_for_action_selection": False,
        # Store False under 'vehicle_id_priority_rule'.
        # Store records under 'scenario_results'.
        "vehicle_id_priority_rule": False, "scenario_results": records,
        # Store the result of _baseline_summary(records) under 'summary'.
        "summary": _baseline_summary(records)}
    # Call atomic_write_json with the supplied arguments.
    atomic_write_json(output_path, payload)
    # Return payload to the caller.
    return payload


# Report using the inputs and processing steps below.
# Input root: the base directory used to resolve files.
# Output: a dictionary containing selected, held_out_comparison_complete.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def report(root=OUTPUT_ROOT):
    # Set root to the result of Path(root).
    # Set validation_path to root joined with the path segment 'comparison' joined with the path segment
    # 'candidate_validation_summary.json'.
    root = Path(root); validation_path = root / "comparison" / "candidate_validation_summary.json"
    # Set selection_path to root joined with the path segment 'selected_configuration.json'.
    selection_path = root / "selected_configuration.json"
    # Run this branch when the negation of whether validation_path exists or the negation of whether
    # selection_path exists.
    if not validation_path.exists() or not selection_path.exists():
        # Raise RuntimeError with the text 'REPORT_REQUIRES_VALIDATION_AND_FROZEN_SELECTION' to stop this
        # execution path.
        raise RuntimeError("REPORT_REQUIRES_VALIDATION_AND_FROZEN_SELECTION")
    # Set validation to the decoded data produced by json.loads from the text read from validation_path.
    validation = json.loads(validation_path.read_text(encoding="utf-8"))
    # Set selection to the decoded data produced by json.loads from the text read from selection_path.
    selection = json.loads(selection_path.read_text(encoding="utf-8"))
    # Set (mappo_path, baseline_path) to a tuple containing root joined with the path segment 'held_out' divided by the
    # text 'selected_mappo_results.json', root divided by the...
    mappo_path, baseline_path = (root / "held_out" / "selected_mappo_results.json",
                                 # Include root joined with the path segment 'held_out' joined with the path segment
                                 # 'baseline_results.json' in this tuple.
                                 root / "held_out" / "baseline_results.json")
    # Set heldout_ready to whether mappo_path exists and whether baseline_path exists.
    heldout_ready = mappo_path.exists() and baseline_path.exists()
    # Set comparison to None.
    comparison = None
    # Run this branch when heldout_ready.
    if heldout_ready:
        # Set mappo to the decoded data produced by json.loads from the text read from mappo_path.
        mappo = json.loads(mappo_path.read_text(encoding="utf-8"))
        # Set base to the decoded data produced by json.loads from the text read from baseline_path.
        base = json.loads(baseline_path.read_text(encoding="utf-8"))
        # Set scenario_results to an empty dictionary.
        scenario_results = {}
        # Iterate over mappo at 'replications', binding each item to rep.
        for rep in mappo["replications"]:
            # Iterate over rep at 'scenario_results', binding each item to row.
            for row in rep["scenario_results"]:
                # Append row to scenario_results.setdefault(json.dumps(row['scenario_id']), []).
                scenario_results.setdefault(
                    # Supply the serialized data produced by json.dumps to scenario_results.setdefault.
                    json.dumps(row["scenario_id"]), []).append(row)
        # Set rows to an empty list.
        rows = []
        # Iterate over base at 'scenario_results', binding each item to row.
        for row in base["scenario_results"]:
            # Set key to the serialized data produced by json.dumps.
            key = json.dumps(row["scenario_id"])
            # Set learned_rows to scenario_results at key.
            learned_rows = scenario_results[key]
            # Set learned to the result of mean(a lazy sequence of x at 'total_team_travel_time_seconds' for x in
            # learned_rows).
            learned = mean(x["total_team_travel_time_seconds"]
                           # Evaluate learned_rows as part of the enclosing expression.
                           for x in learned_rows)
            # Set failed to 'status' from row; use None if absent equals the text 'HARD_SAFETY_FAILURE'.
            failed = row.get("status") == "HARD_SAFETY_FAILURE"
            # Set baseline_time to 'total_team_travel_time_seconds' from row; use None if absent.
            baseline_time = row.get("total_team_travel_time_seconds")
            # Append a dictionary containing scenario_id, baseline_status, baseline_hard_validity_eligible,... to
            # rows.
            rows.append({"scenario_id": row["scenario_id"],
                # Store 'status' from row; use the text 'COMPLETE' if absent under 'baseline_status'.
                "baseline_status": row.get("status", "COMPLETE"),
                # Store the negation of failed under 'baseline_hard_validity_eligible'.
                "baseline_hard_validity_eligible": not failed,
                # Store 'safety_failure_type' from row; use None if absent under 'baseline_safety_failure_type'.
                "baseline_safety_failure_type": row.get(
                    "safety_failure_type"),
                # Store learned under 'mappo_travel_time'.
                "mappo_travel_time": learned,
                # Store baseline_time under 'baseline_travel_time'.
                "baseline_travel_time": baseline_time,
                # Store learned minus baseline_time when baseline_time is a different object from None, otherwise
                # None under 'difference_mappo_minus_baseline'.
                "difference_mappo_minus_baseline": (
                    # Evaluate learned minus baseline_time when baseline_time is a different object from None,
                    # otherwise None as part of the enclosing expression.
                    learned - baseline_time if baseline_time is not None
                    # Supply None to the enclosing expression.
                    else None),
                # Store the result of mean(a lazy sequence of x at 'completed_vehicles' for x in learned_rows)
                # under 'mappo_mean_completion'.
                "mappo_mean_completion": mean(
                    # Evaluate x at 'completed_vehicles' as part of the enclosing expression.
                    x["completed_vehicles"] for x in learned_rows),
                # Store 'completed_vehicles' from row; use None if absent under 'baseline_completion'.
                "baseline_completion": row.get("completed_vehicles"),
                # Store the sum of a lazy sequence of x at 'collisions' for x in learned_rows under
                # 'mappo_collisions'.
                "mappo_collisions": sum(x["collisions"]
                                        # Evaluate learned_rows as part of the enclosing expression.
                                        for x in learned_rows),
                # Store 'collisions' from row; use None if absent under 'baseline_collisions'.
                "baseline_collisions": row.get("collisions"),
                # Store the sum of a lazy sequence of x at 'blocked_zone_violations' for x in learned_rows under
                # 'mappo_blocked_zone_violations'.
                "mappo_blocked_zone_violations": sum(
                    # Evaluate x at 'blocked_zone_violations' as part of the enclosing expression.
                    x["blocked_zone_violations"] for x in learned_rows),
                # Store 'blocked_zone_violations' from row; use None if absent under
                # 'baseline_blocked_zone_violations'.
                "baseline_blocked_zone_violations": row.get(
                    "blocked_zone_violations"),
                # Store the sum of a lazy sequence of x at 'native_sumo_safety_interventions' for x in
                # learned_rows under 'mappo_native_sumo_safety_interventions'.
                "mappo_native_sumo_safety_interventions": sum(
                    # Evaluate x at 'native_sumo_safety_interventions' as part of the enclosing expression.
                    x["native_sumo_safety_interventions"]
                    # Evaluate learned_rows as part of the enclosing expression.
                    for x in learned_rows),
                # Store 'native_sumo_safety_interventions' from row; use None if absent under
                # 'baseline_native_sumo_safety_interventions'.
                "baseline_native_sumo_safety_interventions": row.get(
                    "native_sumo_safety_interventions"),
                # Store 'unresolved_coordination_case' from row; use False if absent under
                # 'baseline_unresolved_coordination_case'.
                "baseline_unresolved_coordination_case": row.get(
                    # Supply the text 'unresolved_coordination_case' to the enclosing expression.
                    "unresolved_coordination_case", False)})
        # Set matched to a list of x for x in rows; retain entries satisfying x at
        # 'difference_mappo_minus_baseline' is a different object from None.
        matched = [x for x in rows if
                   # Evaluate x at 'difference_mappo_minus_baseline' is a different object from None as part of
                   # the enclosing expression.
                   x["difference_mappo_minus_baseline"] is not None]
        # Set difference to the result of mean(a lazy sequence of x at 'difference_mappo_minus_baseline' for x in
        # matched) when matched, otherwise None.
        difference = (mean(x["difference_mappo_minus_baseline"]
                           # Evaluate matched as part of the enclosing expression.
                           for x in matched) if matched else None)
        # Set failure_count to base['summary'] at 'hard_safety_failure_count'.
        failure_count = base["summary"]["hard_safety_failure_count"]
        # Set mappo_safe to whether every item is true in a lazy sequence of x['collisions'] equals 0 and
        # x['blocked_zone_violations'] equals 0 for rep in mappo at 'replications'.
        mappo_safe = all(
            # Evaluate x at 'collisions' equals 0 and x at 'blocked_zone_violations' equals 0 as part of the
            # enclosing expression.
            x["collisions"] == 0 and x["blocked_zone_violations"] == 0
            # Evaluate mappo at 'replications' as part of the enclosing expression.
            for rep in mappo["replications"]
            # Evaluate rep at 'scenario_results' as part of the enclosing expression.
            for x in rep["scenario_results"])
        # Run this branch when failure_count.
        if failure_count:
            # Set wording to formatted text built from the embedded values plus the text 'The selected MAPPO
            # configuration remained eligible under the...' when mappo_safe, otherwise the text 'The selected
            # MAPPO configuration also did not satisfy all...'.
            wording = (
                "The deterministic no-negotiation baseline failed the "
                # Evaluate {failure_count} as part of the enclosing expression.
                f"predefined hard safety-validity gate in {failure_count} "
                "held-out scenario(s). Therefore a full safety-valid overall "
                "efficiency comparison is not available. " +
                # Evaluate the text 'The selected MAPPO configuration remained eligible under the...' when
                # mappo_safe, otherwise the text 'The selected MAPPO configuration also did not satisfy all...' as
                # part of the enclosing expression.
                ("The selected MAPPO configuration remained eligible under "
                 # Evaluate mappo_safe as part of the enclosing expression.
                 "the recorded held-out hard safety gates." if mappo_safe else
                 "The selected MAPPO configuration also did not satisfy all "
                 "recorded held-out hard safety gates."))
        # Run this alternative branch when the preceding branch does not apply.
        else:
            # Set wording to the text 'The selected MAPPO configuration reduced total team travel...' when
            # difference is a different object from None and difference is less than 0, otherwise the text 'No
            # clear operational improvement over the baseline was...' when difference equals 0, otherwise the text
            # 'The selected MAPPO configuration did not outperform the...'.
            wording = ("The selected MAPPO configuration reduced total team travel "
            "time relative to the deterministic no-negotiation baseline under "
            "the tested held-out scenarios while preserving the recorded hard "
            # Evaluate difference is a different object from None and difference is less than 0 as part of the
            # enclosing expression.
            "safety gates." if difference is not None and difference < 0 else
            "No clear operational improvement over the baseline was established "
            # Evaluate difference equals 0 as part of the enclosing expression.
            "under the tested held-out scenarios." if difference == 0 else
            "The selected MAPPO configuration did not outperform the baseline "
            "under the tested held-out scenarios.")
        # Set comparison to a dictionary containing scenario_rows, baseline_safety_eligible,
        # baseline_hard_safety_failure_count,...
        comparison = {"scenario_rows": rows,
            # Store base['summary'] at 'safety_eligible' under 'baseline_safety_eligible'.
            "baseline_safety_eligible": base["summary"]["safety_eligible"],
            # Store failure_count under 'baseline_hard_safety_failure_count'.
            "baseline_hard_safety_failure_count": failure_count,
            # Store base['summary'] at 'hard_safety_failure_scenario_ids' under
            # 'baseline_hard_safety_failure_scenario_ids'.
            "baseline_hard_safety_failure_scenario_ids": base["summary"][
                "hard_safety_failure_scenario_ids"],
            # Store the text 'DESCRIPTIVE_MATCHED_COMPLETED_SCENARIO_SUBSET_ONLY' when failure_count, otherwise
            # the text 'ALL_MATCHED_HELD_OUT_SCENARIOS' under 'efficiency_comparison_scope'.
            "efficiency_comparison_scope": (
                "DESCRIPTIVE_MATCHED_COMPLETED_SCENARIO_SUBSET_ONLY"
                # Evaluate failure_count as part of the enclosing expression.
                if failure_count else "ALL_MATCHED_HELD_OUT_SCENARIOS"),
            # Store the number of entries in matched under 'matched_completed_scenario_count'.
            "matched_completed_scenario_count": len(matched),
            # Store difference under 'matched_completed_subset_mean_difference'.
            "matched_completed_subset_mean_difference": difference,
            # Store None when failure_count, otherwise difference under 'overall_mean_difference'.
            "overall_mean_difference": None if failure_count else difference,
            # Store wording under 'truthful_conclusion'.
            "truthful_conclusion": wording}
        # Call atomic_write_json with the supplied arguments.
        atomic_write_json(root / "comparison" /
                          # Supply comparison to atomic_write_json.
                          "held_out_mappo_vs_baseline.json", comparison)
        # Call _write_comparison_csv with the supplied arguments.
        _write_comparison_csv(root, rows)
    # Set lines to a list containing the text '# Final MAPPO Selection Report', the text '', the text '## Research
    # question', the text '', the...
    lines = ["# Final MAPPO Selection Report", "", "## Research question", "",
        "Which eligible configuration among predefined E5/E10/E15 gives the "
        "lowest mean validation total team travel time?", "",
        "## Controlled design", "", "Only PPO update epochs varied. Learning "
        "rate, clip, architecture, GNN mode, masks, environment, manifests and "
        "H=2 remained fixed.", "", "## Validation results", ""]
    # Iterate over key/value pairs from validation['candidates'], binding each item to (key, item).
    for key, item in validation["candidates"].items():
        # Set selected_mean to 'mean_replication_total_team_travel_time_seconds' from item['summary']; use
        # item['summary'] at 'mean' if absent.
        selected_mean = item['summary'].get(
            'mean_replication_total_team_travel_time_seconds',
            # Supply item['summary'] at 'mean' to item['summary'].get.
            item['summary']['mean'])
        # Append formatted text built from the embedded values to lines.
        lines.append(f"- {key}: mean replication-total TTT {selected_mean}; "
                     # Evaluate {item['hard_gate_result']} as part of the enclosing expression.
                     f"{item['hard_gate_result']}")
    # Update lines to its current value plus a list containing the text '', the text '## Selected configuration',
    # the text '', formatted text built from the embedded...
    lines += ["", "## Selected configuration", "",
              # Include formatted text built from the embedded values in this list.
              f"{selection['selected_candidate_id']} — validation-selected "
              "among the predefined tested candidates.", "",
              "## Held-out and baseline", "",
              # Include comparison at 'truthful_conclusion' when comparison, otherwise the text 'Held-out MAPPO
              # and matched baseline experiments are not both...' in this list.
              comparison["truthful_conclusion"] if comparison else
              "Held-out MAPPO and matched baseline experiments are not both complete.",
              "", "## Limitations", "",
              "N=3 and H=2 are bounded project-resource choices. This is not an "
              "exhaustive search and does not establish global optimality."]
    # Write the supplied text to (root / 'FINAL_MAPPO_SELECTION_REPORT.md').
    (root / "FINAL_MAPPO_SELECTION_REPORT.md").write_text(
        # Supply encoding as the text 'utf-8'.
        "\n".join(lines) + "\n", encoding="utf-8")
    # Set summary to a list containing the text 'MAPPO MODEL-SELECTION SUMMARY', the text '', the text 'Search
    # Detail: type: Controlled one-factor...
    summary = ["MAPPO MODEL-SELECTION SUMMARY", "",
        "Search type: Controlled one-factor ablation",
        "Hyperparameter varied: PPO update epochs",
        "Candidates: 5 / 10 / 15", "Replications: 3 canonical replications",
        "Training horizon: 2 PPO update cycles", "Selection data: Validation only",
        "Primary metric: Total team travel time — lower is better",
        # Include formatted text built from the embedded values in this list.
        f"Selected: {selection['selected_candidate_id']}",
        "Claim: Best-performing eligible configuration among predefined tested candidates.",
        "Not claimed: Global MAPPO optimality."]
    # Write the supplied text to (root / 'PANEL_SUMMARY.txt').
    (root / "PANEL_SUMMARY.txt").write_text(
        # Supply encoding as the text 'utf-8'.
        "\n".join(summary) + "\n", encoding="utf-8")
    # Return a dictionary containing selected, held_out_comparison_complete to the caller.
    return {"selected": selection["selected_candidate_id"],
            # Store heldout_ready under 'held_out_comparison_complete'.
            "held_out_comparison_complete": heldout_ready}


# Write comparison csv using the inputs and processing steps below.
# Input root: the base directory used to resolve files.
# Input rows: the supplied rows.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def _write_comparison_csv(root, rows):
    # Set path to the result of Path(root) joined with the path segment 'comparison' joined with the path segment
    # 'held_out_mappo_vs_baseline.csv'.
    path = Path(root) / "comparison" / "held_out_mappo_vs_baseline.csv"
    # Set temporary to the result of path.with_suffix(the text '.csv.tmp').
    temporary = path.with_suffix(".csv.tmp")
    # Enter the result of temporary.open(the text 'w') as handle and run the enclosed operations within that
    # context.
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        # Set writer to the result of csv.DictWriter(handle).
        # Call writer.writeheader with the supplied arguments.
        writer = csv.DictWriter(handle, fieldnames=rows[0]); writer.writeheader()
        # Iterate over rows, binding each item to row.
        # Call writer.writerow with the supplied arguments.
        for row in rows: writer.writerow({**row,
            # Store the serialized data produced by json.dumps under 'scenario_id'.
            "scenario_id": json.dumps(row["scenario_id"])})
    # Call os.replace with the supplied arguments.
    os.replace(temporary, path)


# Run selected demo using the inputs and processing steps below.
# Input root: the base directory used to resolve files.
# Input use_gui: the supplied use gui.
# Output: a dictionary containing selected_candidate_id, demo_replication_rule, training_operations,...
# Processing: iterate over the relevant records.
def run_selected_demo(root=OUTPUT_ROOT, use_gui=False):
    # Set root to the result of Path(root).
    # Set selected to the decoded data produced by json.loads from the text read from (root /
    # 'selected_configuration.json').
    root = Path(root); selected = json.loads(
        # Supply encoding as the text 'utf-8'.
        (root / "selected_configuration.json").read_text(encoding="utf-8"))
    # Set (_, bundle) to the result of _load_bundle(root joined with the path segment 'selected_policy.pt').
    _, bundle = _load_bundle(root / "selected_policy.pt")
    # Set provider to the result of FinalSelectionInferenceProvider(bundle).
    provider = FinalSelectionInferenceProvider(bundle, sampling_seed=0)
    # Set design to the result of build_design().
    # Set records to an empty list.
    design = build_design(); records = []
    # Iterate over the result of select_demo_scenarios(design), binding each item to item.
    for item in select_demo_scenarios(design):
        # Set signature to item at 'signature'.
        signature = item["signature"]
        # Set episode to the result of CoupledNegotiationTrainingEnvironment(provider,
        # use_gui=use_gui).run_episode(the result of _specification(design at 'payload',
        # signature.scenario_id),...).
        episode = CoupledNegotiationTrainingEnvironment(
            # Supply use_gui as use_gui.
            provider, use_gui=use_gui).run_episode(
            # Supply the result of _specification(design at 'payload', signature.scenario_id) to
            # CoupledNegotiationTrainingEnvironment(provider, use_gui=use_gui).run_episode.
            _specification(design["payload"], signature.scenario_id),
            # Supply design['manifests'][ScenarioRole.TRAINING].manifest_id to
            # CoupledNegotiationTrainingEnvironment(provider, use_gui=use_gui).run_episode.
            design["manifests"][ScenarioRole.TRAINING].manifest_id)
        # Append the result of _episode_record(episode, the text 'MAPPO') to records.
        records.append(_episode_record(episode, "MAPPO"))
    # Return a dictionary containing selected_candidate_id, demo_replication_rule, training_operations,... to the
    # caller.
    return {"selected_candidate_id": selected["selected_candidate_id"],
            "demo_replication_rule": "CANONICAL_REPLICATION_0",
            # Store 0 under 'training_operations'.
            # Store 0 under 'held_out_scenarios_used'.
            "training_operations": 0, "held_out_scenarios_used": 0,
            # Store records under 'scenario_results'.
            "scenario_results": records}
