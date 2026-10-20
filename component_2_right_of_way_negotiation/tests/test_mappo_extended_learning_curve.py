# Import json for use in this module.
import json

# Import pytest for use in this module.
import pytest
# Import torch for use in this module.
import torch

# Import ScenarioRole, build_design from experimentation for the operations below.
from experimentation import ScenarioRole, build_design
# Import build_mechanical_adam_optimization_contract from negotiation_training.adam_contract for the operations
# below.
from negotiation_training.adam_contract import (
    build_mechanical_adam_optimization_contract)
# Import build_mechanical_pilot_architecture_contract from negotiation_training.architecture_contract for the
# operations below.
from negotiation_training.architecture_contract import (
    build_mechanical_pilot_architecture_contract)
# Import restore_evidence_resume_checkpoint, save_evidence_resume_checkpoint from
# negotiation_training.evidence_checkpoint for the operations below.
from negotiation_training.evidence_checkpoint import (
    restore_evidence_resume_checkpoint, save_evidence_resume_checkpoint)
# Import exact_scenario_paired_changes, three_replication_descriptive_statistics from
# negotiation_training.extended_learning_analysis for the operations below.
from negotiation_training.extended_learning_analysis import (
    exact_scenario_paired_changes,
    three_replication_descriptive_statistics)
# Import _fresh_bundle, _tranche_identity from negotiation_training.extended_learning_curve for the operations
# below.
from negotiation_training.extended_learning_curve import (
    _fresh_bundle, _tranche_identity)
# Import MAPPOBehaviorActionProvider from negotiation_training.mappo_provider for the operations below.
from negotiation_training.mappo_provider import MAPPOBehaviorActionProvider
# Import parameter_hash from negotiation_training.rollout for the operations below.
from negotiation_training.rollout import parameter_hash


# Check three replication statistics use sample variance using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_three_replication_statistics_use_sample_variance():
    # Set result to the result of three_replication_descriptive_statistics(a tuple containing 1, 2, 6).
    result = three_replication_descriptive_statistics((1, 2, 6))
    # Require result at 'sample_mean' equals 3; otherwise raise AssertionError.
    assert result["sample_mean"] == 3
    # Require result at 'sample_variance_n_minus_1' equals 7; otherwise raise AssertionError.
    assert result["sample_variance_n_minus_1"] == 7
    # Require result at 'sample_standard_deviation' equals the result of pytest.approx(7 raised to the power 0.5);
    # otherwise raise AssertionError.
    assert result["sample_standard_deviation"] == pytest.approx(7 ** 0.5)
    # Require result at 'minimum' equals 1; otherwise raise AssertionError.
    assert result["minimum"] == 1
    # Require result at 'maximum' equals 6; otherwise raise AssertionError.
    assert result["maximum"] == 6
    # Require result at 'median' equals 2; otherwise raise AssertionError.
    assert result["median"] == 2


# Check statistics reject non three replications using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_statistics_reject_non_three_replications():
    # Enter the result of pytest.raises(ValueError) and run the enclosed operations within that context.
    with pytest.raises(ValueError, match="EXACTLY_THREE"):
        # Call three_replication_descriptive_statistics with the supplied arguments.
        three_replication_descriptive_statistics((1, 2))


# Check exact scenario pairing and all three deltas using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_exact_scenario_pairing_and_all_three_deltas():
    # State using the inputs and processing steps below.
    # Input a: the supplied a.
    # Input b: the supplied b.
    # Output: a dictionary containing scenario_metrics.
    def state(a, b):
        # Return a dictionary containing scenario_metrics to the caller.
        return {"scenario_metrics": [
            # Store a list containing the text 'S', 0 under 'scenario_id'.
            # Store a under 'team_travel_time_seconds'.
            {"scenario_id": ["S", 0], "team_travel_time_seconds": a},
            # Store a list containing the text 'S', 1 under 'scenario_id'.
            # Store b under 'team_travel_time_seconds'.
            {"scenario_id": ["S", 1], "team_travel_time_seconds": b}]}
    # Set changes to the result of exact_scenario_paired_changes(the result of state(10, 20), the result of
    # state(8, 21), the result of state(7, 17)).
    changes = exact_scenario_paired_changes(
        # Supply the result of state(10, 20) to exact_scenario_paired_changes.
        state(10, 20), state(8, 21), state(7, 17))
    # Require changes[0] at 'delta_state0_to_state1' equals the negative of 2; otherwise raise AssertionError.
    assert changes[0]["delta_state0_to_state1"] == -2
    # Require changes[0] at 'delta_state1_to_state2' equals the negative of 1; otherwise raise AssertionError.
    assert changes[0]["delta_state1_to_state2"] == -1
    # Require changes[0] at 'delta_state0_to_state2' equals the negative of 3; otherwise raise AssertionError.
    assert changes[0]["delta_state0_to_state2"] == -3
    # Require changes[1] at 'delta_state0_to_state1' equals 1; otherwise raise AssertionError.
    assert changes[1]["delta_state0_to_state1"] == 1
    # Require changes[1] at 'delta_state1_to_state2' equals the negative of 4; otherwise raise AssertionError.
    assert changes[1]["delta_state1_to_state2"] == -4
    # Require changes[1] at 'delta_state0_to_state2' equals the negative of 3; otherwise raise AssertionError.
    assert changes[1]["delta_state0_to_state2"] == -3


# Check scenario pairing rejects identity mismatch using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_scenario_pairing_rejects_identity_mismatch():
    # Set left to a dictionary containing scenario_metrics.
    left = {"scenario_metrics": [
        # Store the text 'A' under 'scenario_id'.
        # Store 1 under 'team_travel_time_seconds'.
        {"scenario_id": "A", "team_travel_time_seconds": 1}]}
    # Set right to a dictionary containing scenario_metrics.
    right = {"scenario_metrics": [
        # Store the text 'B' under 'scenario_id'.
        # Store 1 under 'team_travel_time_seconds'.
        {"scenario_id": "B", "team_travel_time_seconds": 1}]}
    # Enter the result of pytest.raises(ValueError) and run the enclosed operations within that context.
    with pytest.raises(ValueError, match="PAIRING_IDENTITY"):
        # Call exact_scenario_paired_changes with the supplied arguments.
        exact_scenario_paired_changes(left, right, left)


# Check resume checkpoint restores identity and deterministic continuation using the setup, calls, and assertions
# below.
# Input tmp_path: the supplied tmp path.
# Output: no explicit value; normal completion returns None.
def test_resume_checkpoint_restores_identity_and_deterministic_continuation(tmp_path):
    # Set design to the result of build_design().
    design = build_design()
    # Set architecture to the result of build_mechanical_pilot_architecture_contract().
    architecture = build_mechanical_pilot_architecture_contract()
    # Set optimization to the result of build_mechanical_adam_optimization_contract().
    optimization = build_mechanical_adam_optimization_contract()
    # Set manifest to design['manifests'] at ScenarioRole.TRAINING.
    manifest = design["manifests"][ScenarioRole.TRAINING]
    # Set replication to a tuple containing the text 'EXTENDED_MAPPO_REPLICATION_V1', design['freeze'].freeze_id,
    # 0.
    replication = ("EXTENDED_MAPPO_REPLICATION_V1",
                   # Include design['freeze'].freeze_id in this tuple.
                   design["freeze"].freeze_id, 0)
    # Set bundle to the result of _fresh_bundle(design, architecture, optimization, manifest, replication).
    bundle = _fresh_bundle(design, architecture, optimization,
                           # Supply replication to _fresh_bundle.
                           manifest, replication)
    # Set original_hash to the result of parameter_hash(bundle.proposer_actor).
    original_hash = parameter_hash(bundle.proposer_actor)
    # Set (path, saved) to the result of save_evidence_resume_checkpoint().
    path, saved = save_evidence_resume_checkpoint(
        # Supply bundle as bundle.
        # Supply replication_identity as replication.
        # Supply state_index as 0.
        bundle=bundle, replication_identity=replication, state_index=0,
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
        # Store a dictionary containing rollout_id under 'behavior_rollout_identity'.
        # Store the text 'X' under 'rollout_id'.
        completed_rollout_payload={"behavior_rollout_identity": {"rollout_id": "X"}},
        # Store a list containing the text 'STATE', the text 'X' under 'pass_identity'.
        completed_rollout_metrics={"pass_identity": ["STATE", "X"]},
        # Supply sampling_identity as a list containing the text 'SAMPLE', 0.
        sampling_identity=["SAMPLE", 0],
        # Store the text 'UPDATE' under 'next_operation'.
        progress_cursor={"next_operation": "UPDATE"},
        # Supply update_diagnostics as an empty list.
        # Supply directory as tmp_path.
        update_diagnostics=[], directory=tmp_path)
    # Set expected_provider to the result of MAPPOBehaviorActionProvider(bundle).
    expected_provider = MAPPOBehaviorActionProvider(bundle, sampling_seed=987)
    # Set expected_next to the result of torch.rand(1, generator=expected_provider.generator).item().
    expected_next = torch.rand(1, generator=expected_provider.generator).item()
    # Enter the result of torch.no_grad() and run the enclosed operations within that context.
    with torch.no_grad():
        # Call next(bundle.proposer_actor.parameters()).add_ with the supplied arguments.
        next(bundle.proposer_actor.parameters()).add_(5)
    # Set restored to the result of restore_evidence_resume_checkpoint(path, bundle).
    restored = restore_evidence_resume_checkpoint(path, bundle)
    # Set actual_provider to the result of MAPPOBehaviorActionProvider(bundle).
    actual_provider = MAPPOBehaviorActionProvider(bundle, sampling_seed=987)
    # Set actual_next to the result of torch.rand(1, generator=actual_provider.generator).item().
    actual_next = torch.rand(1, generator=actual_provider.generator).item()
    # Require the result of parameter_hash(bundle.proposer_actor) equals original_hash; otherwise raise
    # AssertionError.
    assert parameter_hash(bundle.proposer_actor) == original_hash
    # Require actual_next equals expected_next; otherwise raise AssertionError.
    assert actual_next == expected_next
    # Require restored at 'checkpoint_identity' equals saved at 'checkpoint_identity'; otherwise raise
    # AssertionError.
    assert restored["checkpoint_identity"] == saved["checkpoint_identity"]


# Check resume checkpoint is never selection eligible using the setup, calls, and assertions below.
# Input tmp_path: the supplied tmp path.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def test_resume_checkpoint_is_never_selection_eligible(tmp_path):
    # The serialized contract is exercised in the preceding restore test; source
    # flags provide a cheap independent guard against accidental ranking semantics.
    # Set source to the result of open('negotiation_training/evidence_checkpoint.py', encoding='utf-8').read().
    source = open("negotiation_training/evidence_checkpoint.py", encoding="utf-8").read()
    # Iterate over a tuple containing the text 'best_model', the text 'final_model', the text 'selected_model',
    # the text 'selection_eligible', binding each item to literal.
    for literal in ("best_model", "final_model", "selected_model",
                    "selection_eligible"):
        # Require formatted text built from the embedded values belongs to source; otherwise raise AssertionError.
        assert f'"{literal}": False' in source
    # Require the text 'LONG_RUNNING_EXPERIMENT_RESUME_ONLY' belongs to source; otherwise raise AssertionError.
    assert "LONG_RUNNING_EXPERIMENT_RESUME_ONLY" in source


# Check tranche identity is deterministic and contract bound using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_tranche_identity_is_deterministic_and_contract_bound():
    # Set design to the result of build_design().
    design = build_design()
    # Set architecture to the result of build_mechanical_pilot_architecture_contract().
    architecture = build_mechanical_pilot_architecture_contract()
    # Set optimization to the result of build_mechanical_adam_optimization_contract().
    optimization = build_mechanical_adam_optimization_contract()
    # Require the result of _tranche_identity(design, architecture, optimization) equals the result of
    # _tranche_identity(design, architecture, optimization); otherwise raise AssertionError.
    assert _tranche_identity(design, architecture, optimization) == \
        _tranche_identity(design, architecture, optimization)


# Check extended runner declares structural and data boundaries using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_extended_runner_declares_structural_and_data_boundaries():
    # Set source to the result of open('negotiation_training/extended_learning_curve.py',
    # encoding='utf-8').read().
    source = open("negotiation_training/extended_learning_curve.py",
                  # Supply encoding as the text 'utf-8'.
                  encoding="utf-8").read()
    # Require the text 'range(3)' belongs to source; otherwise raise AssertionError.
    assert "range(3)" in source
    # Require the text '"training_manifest_collections": 9' belongs to source; otherwise raise AssertionError.
    assert '"training_manifest_collections": 9' in source
    # Require the text '"training_scenario_executions": 324' belongs to source; otherwise raise AssertionError.
    assert '"training_scenario_executions": 324' in source
    # Require the text '"validation_scenario_executions": 0' belongs to source; otherwise raise AssertionError.
    assert '"validation_scenario_executions": 0' in source
    # Require the text '"held_out_scenario_executions": 0' belongs to source; otherwise raise AssertionError.
    assert '"held_out_scenario_executions": 0' in source
    # Require the text '"candidate_comparisons": 0' belongs to source; otherwise raise AssertionError.
    assert '"candidate_comparisons": 0' in source
    # Require the text '"update_3_performed": False' belongs to source; otherwise raise AssertionError.
    assert '"update_3_performed": False' in source
    # Require the text '"final_replication_count_selected": False' belongs to source; otherwise raise
    # AssertionError.
    assert '"final_replication_count_selected": False' in source
    # Require the text '"final_training_budget_selected": False' belongs to source; otherwise raise
    # AssertionError.
    assert '"final_training_budget_selected": False' in source


# Check progress writes are atomic using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_progress_writes_are_atomic():
    # Set source to the result of open('negotiation_training/controlled_pilot.py', encoding='utf-8').read().
    source = open("negotiation_training/controlled_pilot.py",
                  # Supply encoding as the text 'utf-8'.
                  encoding="utf-8").read()
    # Require the text 'os.replace(temporary, path)' belongs to source; otherwise raise AssertionError.
    assert "os.replace(temporary, path)" in source
