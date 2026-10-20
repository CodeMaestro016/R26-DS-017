"""Resumable Step 5J.3C.2B three-replication learning-curve runner."""

# Import hashlib for use in this module.
import hashlib
# Import json for use in this module.
import json
# Import Path from pathlib for the operations below.
from pathlib import Path
# Import perf_counter from time for the operations below.
from time import perf_counter

# Import ScenarioRole, build_design from experimentation for the operations below.
from experimentation import ScenarioRole, build_design
# Import _specification from negotiation_execution.replay for the operations below.
from negotiation_execution.replay import _specification

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
    collect_controlled_training_pass)
# Import restore_evidence_resume_checkpoint, save_evidence_resume_checkpoint from .evidence_checkpoint for the
# operations below.
from .evidence_checkpoint import (
    restore_evidence_resume_checkpoint, save_evidence_resume_checkpoint)
# Import exact_scenario_paired_changes, three_replication_descriptive_statistics from .extended_learning_analysis
# for the operations below.
from .extended_learning_analysis import (
    exact_scenario_paired_changes,
    three_replication_descriptive_statistics)
# Import build_mechanical_mappo_behavior_policy_bundle from .mappo_provider for the operations below.
from .mappo_provider import build_mechanical_mappo_behavior_policy_bundle
# Import MechanicalMAPPOTrainer from .ppo_trainer for the operations below.
from .ppo_trainer import MechanicalMAPPOTrainer
# Import MAPPOBehaviorRolloutIdentity from .rollout for the operations below.
from .rollout import MAPPOBehaviorRolloutIdentity


# Set PROGRESS_PATH to the result of Path(the text 'results/mappo_extended_learning_progress.json').
PROGRESS_PATH = Path("results/mappo_extended_learning_progress.json")
# Set EVIDENCE_PATH to the result of Path(the text 'results/mappo_extended_learning_curve_evidence.json').
EVIDENCE_PATH = Path("results/mappo_extended_learning_curve_evidence.json")
# Set REVIEW_PATH to the result of Path(the text 'results/mappo_pilot_evidence_review.json').
REVIEW_PATH = Path("results/mappo_pilot_evidence_review.json")
# Set TRANCHE_NAME to the text 'EXTENDED_EVIDENCE_TRANCHE_V1'.
TRANCHE_NAME = "EXTENDED_EVIDENCE_TRANCHE_V1"


# Tranche identity using the inputs and processing steps below.
# Input design: the supplied design.
# Input architecture: the supplied architecture.
# Input optimization: the supplied optimization.
# Output: a tuple containing TRANCHE_NAME, the hexadecimal digest from hashlib.sha256(repr(value).encode()).
def _tranche_identity(design, architecture, optimization):
    # Set value to a tuple containing TRANCHE_NAME, design['freeze'].freeze_id, architecture.contract_id,
    # optimization.contract_id, the text...
    value = (TRANCHE_NAME, design["freeze"].freeze_id,
             # Include architecture.contract_id in this tuple.
             architecture.contract_id, optimization.contract_id,
             "THREE_CANONICAL_REPLICATIONS", "THREE_POLICY_STATES")
    # Return a tuple containing TRANCHE_NAME, the hexadecimal digest from hashlib.sha256(repr(value).encode()) to
    # the caller.
    return (TRANCHE_NAME, hashlib.sha256(repr(value).encode()).hexdigest())


# Load review using the inputs and processing steps below.
# Output: review.
# Processing: select branches using the stated conditions.
def _load_review():
    # Set review to the decoded data produced by json.loads from the text read from REVIEW_PATH.
    review = json.loads(REVIEW_PATH.read_text(encoding="utf-8"))
    # Run this branch when 'status' from review; use None if absent differs from the text
    # 'PILOT_EVIDENCE_REVIEW_COMPLETE'.
    if review.get("status") != "PILOT_EVIDENCE_REVIEW_COMPLETE":
        # Raise ValueError with the text 'STEP_5J_3C_2_REVIEW_NOT_VALIDATED' to stop this execution path.
        raise ValueError("STEP_5J_3C_2_REVIEW_NOT_VALIDATED")
    # Run this branch when 'next_readiness' from review; use None if absent differs from the text
    # 'READY_TO_DEFINE_EXTENDED_LEARNING_EVIDENCE_PROTOCOL'.
    if review.get("next_readiness") != \
            "READY_TO_DEFINE_EXTENDED_LEARNING_EVIDENCE_PROTOCOL":
        # Raise ValueError with the text 'EXTENDED_EVIDENCE_PROTOCOL_NOT_READY' to stop this execution path.
        raise ValueError("EXTENDED_EVIDENCE_PROTOCOL_NOT_READY")
    # Return review to the caller.
    return review


# Fresh bundle using the inputs and processing steps below.
# Input design: the supplied design.
# Input architecture: the supplied architecture.
# Input optimization: the supplied optimization.
# Input manifest: the supplied manifest.
# Input replication_identity: the supplied replication identity.
# Output: the result of build_mechanical_mappo_behavior_policy_bundle().
def _fresh_bundle(design, architecture, optimization, manifest,
                  # Declare replication_identity as input parameter.
                  replication_identity):
    # Set identity to the result of MAPPOBehaviorRolloutIdentity(the result of _identity(design, architecture,
    # optimization, manifest, replication_identity, the...).
    identity = MAPPOBehaviorRolloutIdentity(
        # Supply the result of _identity(design, architecture, optimization, manifest, replication_identity, the
        # text...) to MAPPOBehaviorRolloutIdentity.
        _identity(design, architecture, optimization, manifest,
                  # Supply replication_identity to _identity.
                  replication_identity, "EXTENDED_INITIAL_MODEL_STATE"),
        # Supply design['freeze'].freeze_id to MAPPOBehaviorRolloutIdentity.
        design["freeze"].freeze_id, architecture.contract_id,
        # Supply optimization.contract_id to MAPPOBehaviorRolloutIdentity.
        optimization.contract_id, manifest.manifest_id)
    # Return the result of build_mechanical_mappo_behavior_policy_bundle() to the caller.
    return build_mechanical_mappo_behavior_policy_bundle(
        # Supply component_seed_identity as a tuple containing replication_identity, the text
        # 'MODEL_INITIALIZATION'.
        component_seed_identity=(replication_identity,
                                 "MODEL_INITIALIZATION"),
        # Supply behavior_rollout_identity as identity.
        behavior_rollout_identity=identity)


# New progress using the inputs and processing steps below.
# Input tranche_identity: the supplied tranche identity.
# Input design: the supplied design.
# Output: a dictionary containing checkpoint, evidence_tranche_identity, frozen_design_identity,
# completed_replications,...
def _new_progress(tranche_identity, design):
    # Return a dictionary containing checkpoint, evidence_tranche_identity, frozen_design_identity,
    # completed_replications,... to the caller.
    return {
        "checkpoint": "STEP_5J_3C_2B",
        # Store the result of serializable(tranche_identity) under 'evidence_tranche_identity'.
        "evidence_tranche_identity": serializable(tranche_identity),
        # Store the result of serializable(design['freeze'].freeze_id) under 'frozen_design_identity'.
        "frozen_design_identity": serializable(design["freeze"].freeze_id),
        # Store an empty list under 'completed_replications'.
        "completed_replications": [],
        # Store 0 under 'active_replication_index'.
        "active_replication_index": 0,
        # Store 0 under 'active_policy_state_index'.
        "active_policy_state_index": 0,
        # Store 0 under 'completed_policy_states_in_active_replication'.
        "completed_policy_states_in_active_replication": 0,
        "purpose": "ATOMIC_LONG_RUNNING_EVIDENCE_PROGRESS"}


# Define ExtendedMAPLearningCurveRunner to group the state and operations declared below.
# Instances expose the attributes and methods implemented in this class.
class ExtendedMAPLearningCurveRunner:
    # Initialize the instance attributes and collaborators used by the operations below.
    # Input progress_path: the supplied progress path.
    # Input evidence_path: the supplied evidence path.
    # Input resume: the supplied resume.
    # Output: no explicit value; normal completion returns None.
    def __init__(self, progress_path=PROGRESS_PATH,
                 # Declare evidence_path, resume as input parameters.
                 evidence_path=EVIDENCE_PATH, resume=True):
        # Set self.progress_path to the result of Path(progress_path).
        self.progress_path = Path(progress_path)
        # Set self.evidence_path to the result of Path(evidence_path).
        self.evidence_path = Path(evidence_path)
        # Set self.resume to resume.
        self.resume = resume

    # Run using the inputs and processing steps below.
    # Output: result.
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    def run(self):
        # Set started to the result of perf_counter().
        started = perf_counter()
        # Set review to the result of _load_review().
        review = _load_review()
        # Set design to the result of build_design().
        design = build_design()
        # Set architecture to the result of build_mechanical_pilot_architecture_contract().
        architecture = build_mechanical_pilot_architecture_contract()
        # Set optimization to the result of build_mechanical_adam_optimization_contract().
        optimization = build_mechanical_adam_optimization_contract()
        # Set manifest to design['manifests'] at ScenarioRole.TRAINING.
        manifest = design["manifests"][ScenarioRole.TRAINING]
        # Set specifications to a tuple built from a lazy sequence of the result of _specification(design at
        # 'payload', scenario_id) for scenario_id in manifest.scenario_ids.
        specifications = tuple(_specification(design["payload"], scenario_id)
                               # Evaluate manifest.scenario_ids as part of the enclosing expression.
                               for scenario_id in manifest.scenario_ids)
        # Set tranche_identity to the result of _tranche_identity(design, architecture, optimization).
        tranche_identity = _tranche_identity(
            # Supply architecture to _tranche_identity.
            design, architecture, optimization)
        # Run this branch when self.resume and whether self.progress_path exists.
        if self.resume and self.progress_path.exists():
            # Set progress to the decoded data produced by json.loads from the text read from self.progress_path.
            progress = json.loads(self.progress_path.read_text(encoding="utf-8"))
            # Run this branch when 'evidence_tranche_identity' from progress; use None if absent differs from the
            # result of serializable(tranche_identity).
            if progress.get("evidence_tranche_identity") != \
                    serializable(tranche_identity):
                # Raise ValueError with the text 'RESUME_TRANCHE_IDENTITY_MISMATCH' to stop this execution path.
                raise ValueError("RESUME_TRANCHE_IDENTITY_MISMATCH")
        # Run this alternative branch when the preceding branch does not apply.
        else:
            # Set progress to the result of _new_progress(tranche_identity, design).
            progress = _new_progress(tranche_identity, design)
            # Call atomic_write_json with the supplied arguments.
            atomic_write_json(self.progress_path, progress)
        # Set complete_records to a list built from 'completed_replications' from progress; use an empty tuple if
        # absent.
        complete_records = list(progress.get("completed_replications", ()))
        # Set completed_by_index to a dictionary of item at 'replication_index' mapped to item for item in
        # complete_records.
        completed_by_index = {item["replication_index"]: item
                              # Evaluate complete_records as part of the enclosing expression.
                              for item in complete_records}
        # Set replications to an empty list.
        replications = []
        # Iterate over the integer range defined by 3, binding each item to replication_index.
        for replication_index in range(3):
            # Run this branch when replication_index belongs to completed_by_index.
            if replication_index in completed_by_index:
                # Append completed_by_index at replication_index to replications.
                replications.append(completed_by_index[replication_index])
                # Skip the rest of this loop iteration and process the next item.
                continue
            # Set replication_identity to a tuple containing the text 'EXTENDED_MAPPO_REPLICATION_V1',
            # design['freeze'].freeze_id, replication_index.
            replication_identity = (
                "EXTENDED_MAPPO_REPLICATION_V1",
                # Include design['freeze'].freeze_id in this tuple.
                design["freeze"].freeze_id, replication_index)
            # Set bundle to the result of _fresh_bundle(design, architecture, optimization, manifest,
            # replication_identity).
            bundle = _fresh_bundle(design, architecture, optimization,
                                   # Supply replication_identity to _fresh_bundle.
                                   manifest, replication_identity)
            # Set initial_hashes to the result of _current_hashes(bundle).
            initial_hashes = _current_hashes(bundle)
            # Set partial to 'active_replication' from progress; use None if absent.
            partial = progress.get("active_replication")
            # Run this branch when partial and 'replication_index' from partial; use None if absent equals
            # replication_index.
            if partial and partial.get("replication_index") == replication_index:
                # Set states to a list built from 'states' from partial; use an empty tuple if absent.
                states = list(partial.get("states", ()))
                # Set updates to a list built from 'updates' from partial; use an empty tuple if absent.
                updates = list(partial.get("updates", ()))
                # Set checkpoint_paths to a list built from 'resume_checkpoints' from partial; use an empty tuple
                # if absent.
                checkpoint_paths = list(partial.get("resume_checkpoints", ()))
                # Run this branch when states.
                if states:
                    # Set resumed to the result of restore_evidence_resume_checkpoint(checkpoint_paths at -1,
                    # bundle).
                    resumed = restore_evidence_resume_checkpoint(
                        # Supply checkpoint_paths at -1 to restore_evidence_resume_checkpoint.
                        checkpoint_paths[-1], bundle)
                    # Set rollout_payload to resumed at 'completed_rollout_payload'.
                    rollout_payload = resumed["completed_rollout_payload"]
                # Run this alternative branch when the preceding branch does not apply.
                else:
                    # Set rollout_payload to None.
                    rollout_payload = None
            # Run this alternative branch when the preceding branch does not apply.
            else:
                # Set (states, updates, checkpoint_paths) to a tuple containing an empty list, an empty list, an
                # empty list.
                states, updates, checkpoint_paths = [], [], []
                # Set rollout_payload to None.
                rollout_payload = None
            # Set rep_started to the result of perf_counter().
            rep_started = perf_counter()
            # Set gnn_hash to initial_hashes at 'gnn'.
            gnn_hash = initial_hashes["gnn"]
            # Repeat the following steps while the number of entries in states is less than 3.
            while len(states) < 3:
                # Set state_index to the number of entries in states.
                state_index = len(states)
                # Run this branch when state_index.
                if state_index:
                    # Set update_index to state_index.
                    update_index = state_index
                    # Set before_update to the result of _current_hashes(bundle).
                    before_update = _current_hashes(bundle)
                    # Set update_started to the result of perf_counter().
                    update_started = perf_counter()
                    # Set update to the result of MechanicalMAPPOTrainer(rollout_payload=rollout_payload,
                    # bundle=bundle, output_path=None).run().
                    update = MechanicalMAPPOTrainer(
                        # Supply rollout_payload as rollout_payload.
                        # Supply bundle as bundle.
                        rollout_payload=rollout_payload, bundle=bundle,
                        # Supply output_path as None.
                        output_path=None).run()
                    # Set update_runtime to the result of perf_counter() minus update_started.
                    update_runtime = perf_counter() - update_started
                    # Set after_update to the result of _current_hashes(bundle).
                    after_update = _current_hashes(bundle)
                    # Run this branch when after_update at 'gnn' differs from gnn_hash.
                    if after_update["gnn"] != gnn_hash:
                        # Raise RuntimeError with the text 'FROZEN_GNN_PARAMETER_CHANGED' to stop this execution
                        # path.
                        raise RuntimeError("FROZEN_GNN_PARAMETER_CHANGED")
                    # Append a dictionary containing update_index, source_policy_state_index,
                    # source_rollout_identity,... to updates.
                    updates.append({
                        # Store update_index under 'update_index'.
                        "update_index": update_index,
                        # Store state_index minus 1 under 'source_policy_state_index'.
                        "source_policy_state_index": state_index - 1,
                        "source_rollout_identity":
                            # Evaluate rollout_payload at 'behavior_rollout_identity' as part of the enclosing
                            # expression.
                            rollout_payload["behavior_rollout_identity"],
                        # Store False under 'source_rollout_reused_by_other_update'.
                        "source_rollout_reused_by_other_update": False,
                        "parameter_state_identity":
                            # Evaluate formatted text built from the embedded values as part of the enclosing
                            # expression.
                            f"REPLICATION_{replication_index}_POST_UPDATE_{update_index}",
                        # Store before_update under 'parameter_hashes_before'.
                        "parameter_hashes_before": before_update,
                        # Store after_update under 'parameter_hashes_after'.
                        "parameter_hashes_after": after_update,
                        # Store update_runtime under 'wall_clock_runtime_seconds'.
                        "wall_clock_runtime_seconds": update_runtime,
                        # Store update under 'diagnostics'.
                        "diagnostics": update})
                # Set state_label to formatted text built from the embedded values.
                state_label = f"REPLICATION_{replication_index}_STATE_{state_index}"
                # Set base_progress to a dictionary containing completed_replications, active_replication_index,
                # active_policy_state_index,...
                base_progress = {
                    # Evaluate the result of _new_progress(tranche_identity, design) as part of the enclosing
                    # expression.
                    **_new_progress(tranche_identity, design),
                    # Store replications under 'completed_replications'.
                    "completed_replications": replications,
                    # Store replication_index under 'active_replication_index'.
                    "active_replication_index": replication_index,
                    # Store state_index under 'active_policy_state_index'.
                    "active_policy_state_index": state_index,
                    # Store the number of entries in states under 'completed_policy_states_in_active_replication'.
                    "completed_policy_states_in_active_replication": len(states),
                    # Store a dictionary containing replication_index, states, updates, resume_checkpoints under
                    # 'active_replication'.
                    "active_replication": {
                        # Store replication_index under 'replication_index'.
                        "replication_index": replication_index,
                        # Store states under 'states'.
                        # Store updates under 'updates'.
                        "states": states, "updates": updates,
                        # Store checkpoint_paths under 'resume_checkpoints'.
                        "resume_checkpoints": checkpoint_paths}}
                # Set (metrics, rollout_payload) to the result of collect_controlled_training_pass().
                metrics, rollout_payload = collect_controlled_training_pass(
                    # Supply design as design.
                    # Supply architecture as architecture.
                    design=design, architecture=architecture,
                    # Supply optimization as optimization.
                    # Supply manifest as manifest.
                    optimization=optimization, manifest=manifest,
                    # Supply specifications as specifications.
                    # Supply bundle as bundle.
                    specifications=specifications, bundle=bundle,
                    # Supply replication_identity as replication_identity.
                    replication_identity=replication_identity,
                    # Supply pass_label as state_label.
                    pass_label=state_label,
                    # Supply progress_context as base_progress.
                    progress_context=base_progress,
                    # Supply progress_path as self.progress_path.
                    progress_path=self.progress_path)
                # Set hashes to the result of _current_hashes(bundle).
                hashes = _current_hashes(bundle)
                # Run this branch when hashes at 'gnn' differs from gnn_hash.
                if hashes["gnn"] != gnn_hash:
                    # Raise RuntimeError with the text 'FROZEN_GNN_PARAMETER_CHANGED' to stop this execution path.
                    raise RuntimeError("FROZEN_GNN_PARAMETER_CHANGED")
                # Set metrics['policy_state_index'] to state_index.
                metrics["policy_state_index"] = state_index
                # Set metrics['parameter_state_identity'] to state_label.
                metrics["parameter_state_identity"] = state_label
                # Set metrics['proposer_hash'] to hashes at 'proposer'.
                metrics["proposer_hash"] = hashes["proposer"]
                # Set metrics['responder_hash'] to hashes at 'responder'.
                metrics["responder_hash"] = hashes["responder"]
                # Set metrics['critic_hash'] to hashes at 'critic'.
                metrics["critic_hash"] = hashes["critic"]
                # Set metrics['gnn_hash'] to hashes at 'gnn'.
                metrics["gnn_hash"] = hashes["gnn"]
                # Append metrics to states.
                states.append(metrics)
                # Set (checkpoint_path, checkpoint) to the result of save_evidence_resume_checkpoint().
                checkpoint_path, checkpoint = save_evidence_resume_checkpoint(
                    # Supply bundle as bundle.
                    # Supply replication_identity as replication_identity.
                    bundle=bundle, replication_identity=replication_identity,
                    # Supply state_index as state_index.
                    state_index=state_index,
                    # Supply frozen_design_identity as design['freeze'].freeze_id.
                    frozen_design_identity=design["freeze"].freeze_id,
                    # Supply architecture_contract_identity as architecture.contract_id.
                    architecture_contract_identity=architecture.contract_id,
                    # Supply optimization_contract_identity as optimization.contract_id.
                    optimization_contract_identity=optimization.contract_id,
                    # Supply provisional_configuration_identity as design['provisional'].configuration_id.
                    provisional_configuration_identity=
                        # Evaluate design['provisional'].configuration_id as part of the enclosing expression.
                        design["provisional"].configuration_id,
                    # Supply completed_rollout_payload as rollout_payload.
                    completed_rollout_payload=rollout_payload,
                    # Supply completed_rollout_metrics as metrics.
                    completed_rollout_metrics=metrics,
                    # Supply sampling_identity as metrics at 'sampling_seed_identity'.
                    sampling_identity=metrics["sampling_seed_identity"],
                    # Supply progress_cursor as a dictionary containing replication_index,
                    # completed_policy_state_index, next_operation.
                    progress_cursor={
                        # Store replication_index under 'replication_index'.
                        "replication_index": replication_index,
                        # Store state_index under 'completed_policy_state_index'.
                        "completed_policy_state_index": state_index,
                        # Store the text 'UPDATE' when state_index is less than 2, otherwise the text
                        # 'NEXT_REPLICATION' under 'next_operation'.
                        "next_operation": "UPDATE" if state_index < 2
                                          # Supply the text 'NEXT_REPLICATION' to the enclosing expression.
                                          else "NEXT_REPLICATION"},
                    # Supply update_diagnostics as updates.
                    update_diagnostics=updates)
                # Append a string built from checkpoint_path to checkpoint_paths.
                checkpoint_paths.append(str(checkpoint_path))
                # Set progress to a dictionary containing completed_replications, active_replication_index,
                # active_policy_state_index,...
                progress = {
                    # Evaluate the result of _new_progress(tranche_identity, design) as part of the enclosing
                    # expression.
                    **_new_progress(tranche_identity, design),
                    # Store replications under 'completed_replications'.
                    "completed_replications": replications,
                    # Store replication_index under 'active_replication_index'.
                    "active_replication_index": replication_index,
                    # Store state_index under 'active_policy_state_index'.
                    "active_policy_state_index": state_index,
                    # Store the number of entries in states under 'completed_policy_states_in_active_replication'.
                    "completed_policy_states_in_active_replication": len(states),
                    # Store a dictionary containing replication_index, replication_identity,
                    # initial_parameter_hashes, states, updates,... under 'active_replication'.
                    "active_replication": {
                        # Store replication_index under 'replication_index'.
                        "replication_index": replication_index,
                        # Store the result of serializable(replication_identity) under 'replication_identity'.
                        "replication_identity": serializable(replication_identity),
                        # Store initial_hashes under 'initial_parameter_hashes'.
                        "initial_parameter_hashes": initial_hashes,
                        # Store states under 'states'.
                        # Store updates under 'updates'.
                        "states": states, "updates": updates,
                        # Store checkpoint_paths under 'resume_checkpoints'.
                        "resume_checkpoints": checkpoint_paths,
                        # Store the result of serializable(checkpoint at 'checkpoint_identity') under
                        # 'last_checkpoint_identity'.
                        "last_checkpoint_identity": serializable(
                            # Supply checkpoint at 'checkpoint_identity' to serializable.
                            checkpoint["checkpoint_identity"])}}
                # Call atomic_write_json with the supplied arguments.
                atomic_write_json(self.progress_path, progress)
            # Set (c0, c1, c2) to a lazy sequence of item at 'team_travel_time_seconds' for item in states.
            c0, c1, c2 = (item["team_travel_time_seconds"]
                          # Evaluate states as part of the enclosing expression.
                          for item in states)
            # Set record to a dictionary containing replication_index, replication_identity,
            # canonical_replication_retained,...
            record = {
                # Store replication_index under 'replication_index'.
                "replication_index": replication_index,
                # Store the result of serializable(replication_identity) under 'replication_identity'.
                "replication_identity": serializable(replication_identity),
                # Store True under 'canonical_replication_retained'.
                "canonical_replication_retained": True,
                # Store False under 'performance_selected'.
                "performance_selected": False,
                # Store True under 'fresh_initialization'.
                "fresh_initialization": True,
                # Store False under 'historical_pilot_state_spliced'.
                "historical_pilot_state_spliced": False,
                # Store initial_hashes under 'initial_parameter_hashes'.
                "initial_parameter_hashes": initial_hashes,
                # Store states under 'policy_states'.
                "policy_states": states,
                # Store updates under 'updates'.
                "updates": updates,
                # Store checkpoint_paths under 'resume_checkpoints'.
                "resume_checkpoints": checkpoint_paths,
                # Store a dictionary containing delta_0_to_1, delta_1_to_2, delta_0_to_2 under
                # 'learning_curve_deltas'.
                "learning_curve_deltas": {
                    # Store c1 minus c0 under 'delta_0_to_1'.
                    "delta_0_to_1": c1 - c0,
                    # Store c2 minus c1 under 'delta_1_to_2'.
                    "delta_1_to_2": c2 - c1,
                    # Store c2 minus c0 under 'delta_0_to_2'.
                    "delta_0_to_2": c2 - c0},
                # Store the result of exact_scenario_paired_changes(states at 0, states at 1, states at 2) under
                # 'scenario_paired_changes'.
                "scenario_paired_changes": exact_scenario_paired_changes(
                    # Supply states at 0 to exact_scenario_paired_changes.
                    states[0], states[1], states[2]),
                # Store a list containing initial_hashes at 'gnn', updates[0]['parameter_hashes_after'] at 'gnn',
                # states[1] at 'gnn_hash',... under 'gnn_hash_at_all_boundaries'.
                "gnn_hash_at_all_boundaries": [
                    # Include initial_hashes at 'gnn' in this list.
                    initial_hashes["gnn"],
                    # Include updates[0]['parameter_hashes_after'] at 'gnn' in this list.
                    updates[0]["parameter_hashes_after"]["gnn"],
                    # Include states[1] at 'gnn_hash' in this list.
                    states[1]["gnn_hash"],
                    # Include updates[1]['parameter_hashes_after'] at 'gnn' in this list.
                    updates[1]["parameter_hashes_after"]["gnn"],
                    # Include states[2] at 'gnn_hash' in this list.
                    states[2]["gnn_hash"]],
                # Store True under 'gnn_unchanged'.
                "gnn_unchanged": True,
                # Store the result of perf_counter() minus rep_started under 'wall_clock_runtime_seconds'.
                "wall_clock_runtime_seconds": perf_counter() - rep_started}
            # Run this branch when the number of entries in a set built from record at
            # 'gnn_hash_at_all_boundaries' differs from 1.
            if len(set(record["gnn_hash_at_all_boundaries"])) != 1:
                # Raise RuntimeError with the text 'FROZEN_GNN_PARAMETER_CHANGED' to stop this execution path.
                raise RuntimeError("FROZEN_GNN_PARAMETER_CHANGED")
            # Append record to replications.
            replications.append(record)
            # Set progress to a dictionary containing completed_replications, active_replication_index,
            # active_policy_state_index,...
            progress = {
                # Evaluate the result of _new_progress(tranche_identity, design) as part of the enclosing
                # expression.
                **_new_progress(tranche_identity, design),
                # Store replications under 'completed_replications'.
                "completed_replications": replications,
                # Store replication_index plus 1 under 'active_replication_index'.
                "active_replication_index": replication_index + 1,
                # Store 0 under 'active_policy_state_index'.
                "active_policy_state_index": 0,
                # Store 0 under 'completed_policy_states_in_active_replication'.
                "completed_policy_states_in_active_replication": 0}
            # Call atomic_write_json with the supplied arguments.
            atomic_write_json(self.progress_path, progress)
        # Set statistic_sources to a dictionary containing C0, C1, C2, delta_0_to_1, delta_1_to_2, delta_0_to_2.
        statistic_sources = {
            # Store a list of r['policy_states'][0] at 'team_travel_time_seconds' for r in replications under
            # 'C0'.
            "C0": [r["policy_states"][0]["team_travel_time_seconds"]
                   # Evaluate replications as part of the enclosing expression.
                   for r in replications],
            # Store a list of r['policy_states'][1] at 'team_travel_time_seconds' for r in replications under
            # 'C1'.
            "C1": [r["policy_states"][1]["team_travel_time_seconds"]
                   # Evaluate replications as part of the enclosing expression.
                   for r in replications],
            # Store a list of r['policy_states'][2] at 'team_travel_time_seconds' for r in replications under
            # 'C2'.
            "C2": [r["policy_states"][2]["team_travel_time_seconds"]
                   # Evaluate replications as part of the enclosing expression.
                   for r in replications],
            # Store a list of r['learning_curve_deltas'] at 'delta_0_to_1' for r in replications under
            # 'delta_0_to_1'.
            "delta_0_to_1": [r["learning_curve_deltas"]["delta_0_to_1"]
                             # Evaluate replications as part of the enclosing expression.
                             for r in replications],
            # Store a list of r['learning_curve_deltas'] at 'delta_1_to_2' for r in replications under
            # 'delta_1_to_2'.
            "delta_1_to_2": [r["learning_curve_deltas"]["delta_1_to_2"]
                             # Evaluate replications as part of the enclosing expression.
                             for r in replications],
            # Store a list of r['learning_curve_deltas'] at 'delta_0_to_2' for r in replications under
            # 'delta_0_to_2'.
            "delta_0_to_2": [r["learning_curve_deltas"]["delta_0_to_2"]
                             # Evaluate replications as part of the enclosing expression.
                             for r in replications]}
        # Set result to a dictionary containing checkpoint, status, evidence_tranche_identity,
        # source_review_identity,...
        result = {
            "checkpoint": "STEP_5J_3C_2B",
            "status": "EXTENDED_MULTI_UPDATE_EVIDENCE_ACQUIRED",
            # Store the result of serializable(tranche_identity) under 'evidence_tranche_identity'.
            "evidence_tranche_identity": serializable(tranche_identity),
            # Store review at 'source_pilot_identity' under 'source_review_identity'.
            "source_review_identity": review["source_pilot_identity"],
            # Store the result of serializable(design['freeze'].freeze_id) under 'frozen_design_identity'.
            "frozen_design_identity": serializable(design["freeze"].freeze_id),
            # Store the result of serializable(design['provisional'].configuration_id) under
            # 'provisional_configuration_identity'.
            "provisional_configuration_identity": serializable(
                # Supply design['provisional'].configuration_id to serializable.
                design["provisional"].configuration_id),
            # Store the result of serializable(architecture.contract_id) under 'architecture_contract_identity'.
            "architecture_contract_identity": serializable(
                # Supply architecture.contract_id to serializable.
                architecture.contract_id),
            # Store the result of serializable(optimization.contract_id) under 'optimization_contract_identity'.
            "optimization_contract_identity": serializable(
                # Supply optimization.contract_id to serializable.
                optimization.contract_id),
            # Store 3 under 'replications_observed'.
            "replications_observed": 3,
            # Store 2 under 'update_intervals_observed_per_replication'.
            "update_intervals_observed_per_replication": 2,
            # Store 3 under 'policy_states_per_replication'.
            "policy_states_per_replication": 3,
            # Store 9 under 'training_manifest_collections'.
            "training_manifest_collections": 9,
            # Store 324 under 'training_scenario_executions'.
            "training_scenario_executions": 324,
            # Store replications under 'replications'.
            "replications": replications,
            # Store a dictionary of name mapped to the result of three_replication_descriptive_statistics(values)
            # for (name, values) in key/value pairs from statistic_sources under
            # 'cross_replication_descriptive_statistics'.
            "cross_replication_descriptive_statistics": {
                # Evaluate the result of three_replication_descriptive_statistics(values) as part of the enclosing
                # expression.
                name: three_replication_descriptive_statistics(values)
                # Evaluate key/value pairs from statistic_sources as part of the enclosing expression.
                for name, values in statistic_sources.items()},
            # Store a dictionary containing total_sumo_steps, total_state_collection_wall_clock_seconds,... under
            # 'compute_cost_evidence'.
            "compute_cost_evidence": {
                # Store the sum of a lazy sequence of state at 'sumo_step_count' for replication in replications
                # under 'total_sumo_steps'.
                "total_sumo_steps": sum(
                    # Evaluate state at 'sumo_step_count' as part of the enclosing expression.
                    state["sumo_step_count"] for replication in replications
                    # Evaluate replication at 'policy_states' as part of the enclosing expression.
                    for state in replication["policy_states"]),
                # Store the sum of a lazy sequence of state at 'wall_clock_runtime_seconds' for replication in
                # replications under 'total_state_collection_wall_clock_seconds'.
                "total_state_collection_wall_clock_seconds": sum(
                    # Evaluate state at 'wall_clock_runtime_seconds' as part of the enclosing expression.
                    state["wall_clock_runtime_seconds"]
                    # Evaluate replications as part of the enclosing expression.
                    for replication in replications
                    # Evaluate replication at 'policy_states' as part of the enclosing expression.
                    for state in replication["policy_states"]),
                # Store the sum of a lazy sequence of update at 'wall_clock_runtime_seconds' for replication in
                # replications under 'total_update_runtime_seconds'.
                "total_update_runtime_seconds": sum(
                    # Evaluate update at 'wall_clock_runtime_seconds' as part of the enclosing expression.
                    update["wall_clock_runtime_seconds"]
                    # Evaluate replications as part of the enclosing expression.
                    for replication in replications
                    # Evaluate replication at 'updates' as part of the enclosing expression.
                    for update in replication["updates"]),
                # Store the result of perf_counter() minus started under 'total_runner_wall_clock_seconds'.
                "total_runner_wall_clock_seconds": perf_counter() - started},
            # Store a dictionary containing collisions, blocked_zone_violations under 'safety_evidence'.
            "safety_evidence": {
                # Store the sum of a lazy sequence of state at 'collision_count' for replication in replications
                # under 'collisions'.
                "collisions": sum(state["collision_count"]
                                  # Evaluate replications as part of the enclosing expression.
                                  for replication in replications
                                  # Evaluate replication at 'policy_states' as part of the enclosing expression.
                                  for state in replication["policy_states"]),
                # Store the sum of a lazy sequence of state at 'blocked_zone_violation_count' for replication in
                # replications under 'blocked_zone_violations'.
                "blocked_zone_violations": sum(
                    # Evaluate state at 'blocked_zone_violation_count' as part of the enclosing expression.
                    state["blocked_zone_violation_count"]
                    # Evaluate replications as part of the enclosing expression.
                    for replication in replications
                    # Evaluate replication at 'policy_states' as part of the enclosing expression.
                    for state in replication["policy_states"])},
            # Store a dictionary containing training_scenario_executions, validation_scenario_executions,... under
            # 'data_boundary_evidence'.
            "data_boundary_evidence": {
                # Store 324 under 'training_scenario_executions'.
                "training_scenario_executions": 324,
                # Store 0 under 'validation_scenario_executions'.
                "validation_scenario_executions": 0,
                # Store 0 under 'held_out_scenario_executions'.
                "held_out_scenario_executions": 0,
                # Store 0 under 'candidate_comparisons'.
                "candidate_comparisons": 0},
            # Store False under 'improvement_threshold_used'.
            "improvement_threshold_used": False,
            # Store 0 under 'outliers_declared'.
            "outliers_declared": 0,
            # Store 0 under 'replications_discarded'.
            "replications_discarded": 0,
            # Store False under 'update_3_performed'.
            "update_3_performed": False,
            # Store False under 'final_replication_count_selected'.
            "final_replication_count_selected": False,
            # Store False under 'final_training_budget_selected'.
            "final_training_budget_selected": False,
            "next_readiness":
                "READY_FOR_EXTENDED_EVIDENCE_SUFFICIENCY_REVIEW",
            "next_checkpoint": "STEP_5J_3C_2C"}
        # Run this branch when result at 'safety_evidence' differs from a dictionary containing collisions,
        # blocked_zone_violations.
        if result["safety_evidence"] != {
                # Store 0 under 'collisions'.
                # Store 0 under 'blocked_zone_violations'.
                "collisions": 0, "blocked_zone_violations": 0}:
            # Call atomic_write_json with the supplied arguments.
            atomic_write_json(self.evidence_path, result)
            # Raise RuntimeError with the text 'EXTENDED_EVIDENCE_SAFETY_GATE_FAILED' to stop this execution path.
            raise RuntimeError("EXTENDED_EVIDENCE_SAFETY_GATE_FAILED")
        # Call atomic_write_json with the supplied arguments.
        atomic_write_json(self.evidence_path, result)
        # Return result to the caller.
        return result
