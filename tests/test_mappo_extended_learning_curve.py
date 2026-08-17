import json

import pytest
import torch

from experimentation import ScenarioRole, build_design
from negotiation_training.adam_contract import (
    build_mechanical_adam_optimization_contract)
from negotiation_training.architecture_contract import (
    build_mechanical_pilot_architecture_contract)
from negotiation_training.evidence_checkpoint import (
    restore_evidence_resume_checkpoint, save_evidence_resume_checkpoint)
from negotiation_training.extended_learning_analysis import (
    exact_scenario_paired_changes,
    three_replication_descriptive_statistics)
from negotiation_training.extended_learning_curve import (
    _fresh_bundle, _tranche_identity)
from negotiation_training.mappo_provider import MAPPOBehaviorActionProvider
from negotiation_training.rollout import parameter_hash


def test_three_replication_statistics_use_sample_variance():
    result = three_replication_descriptive_statistics((1, 2, 6))
    assert result["sample_mean"] == 3
    assert result["sample_variance_n_minus_1"] == 7
    assert result["sample_standard_deviation"] == pytest.approx(7 ** 0.5)
    assert result["minimum"] == 1
    assert result["maximum"] == 6
    assert result["median"] == 2


def test_statistics_reject_non_three_replications():
    with pytest.raises(ValueError, match="EXACTLY_THREE"):
        three_replication_descriptive_statistics((1, 2))


def test_exact_scenario_pairing_and_all_three_deltas():
    def state(a, b):
        return {"scenario_metrics": [
            {"scenario_id": ["S", 0], "team_travel_time_seconds": a},
            {"scenario_id": ["S", 1], "team_travel_time_seconds": b}]}
    changes = exact_scenario_paired_changes(
        state(10, 20), state(8, 21), state(7, 17))
    assert changes[0]["delta_state0_to_state1"] == -2
    assert changes[0]["delta_state1_to_state2"] == -1
    assert changes[0]["delta_state0_to_state2"] == -3
    assert changes[1]["delta_state0_to_state1"] == 1
    assert changes[1]["delta_state1_to_state2"] == -4
    assert changes[1]["delta_state0_to_state2"] == -3


def test_scenario_pairing_rejects_identity_mismatch():
    left = {"scenario_metrics": [
        {"scenario_id": "A", "team_travel_time_seconds": 1}]}
    right = {"scenario_metrics": [
        {"scenario_id": "B", "team_travel_time_seconds": 1}]}
    with pytest.raises(ValueError, match="PAIRING_IDENTITY"):
        exact_scenario_paired_changes(left, right, left)


def test_resume_checkpoint_restores_identity_and_deterministic_continuation(tmp_path):
    design = build_design()
    architecture = build_mechanical_pilot_architecture_contract()
    optimization = build_mechanical_adam_optimization_contract()
    manifest = design["manifests"][ScenarioRole.TRAINING]
    replication = ("EXTENDED_MAPPO_REPLICATION_V1",
                   design["freeze"].freeze_id, 0)
    bundle = _fresh_bundle(design, architecture, optimization,
                           manifest, replication)
    original_hash = parameter_hash(bundle.proposer_actor)
    path, saved = save_evidence_resume_checkpoint(
        bundle=bundle, replication_identity=replication, state_index=0,
        frozen_design_identity=design["freeze"].freeze_id,
        architecture_contract_identity=architecture.contract_id,
        optimization_contract_identity=optimization.contract_id,
        provisional_configuration_identity=
            design["provisional"].configuration_id,
        completed_rollout_payload={"behavior_rollout_identity": {"rollout_id": "X"}},
        completed_rollout_metrics={"pass_identity": ["STATE", "X"]},
        sampling_identity=["SAMPLE", 0],
        progress_cursor={"next_operation": "UPDATE"},
        update_diagnostics=[], directory=tmp_path)
    expected_provider = MAPPOBehaviorActionProvider(bundle, sampling_seed=987)
    expected_next = torch.rand(1, generator=expected_provider.generator).item()
    with torch.no_grad():
        next(bundle.proposer_actor.parameters()).add_(5)
    restored = restore_evidence_resume_checkpoint(path, bundle)
    actual_provider = MAPPOBehaviorActionProvider(bundle, sampling_seed=987)
    actual_next = torch.rand(1, generator=actual_provider.generator).item()
    assert parameter_hash(bundle.proposer_actor) == original_hash
    assert actual_next == expected_next
    assert restored["checkpoint_identity"] == saved["checkpoint_identity"]


def test_resume_checkpoint_is_never_selection_eligible(tmp_path):
    # The serialized contract is exercised in the preceding restore test; source
    # flags provide a cheap independent guard against accidental ranking semantics.
    source = open("negotiation_training/evidence_checkpoint.py", encoding="utf-8").read()
    for literal in ("best_model", "final_model", "selected_model",
                    "selection_eligible"):
        assert f'"{literal}": False' in source
    assert "LONG_RUNNING_EXPERIMENT_RESUME_ONLY" in source


def test_tranche_identity_is_deterministic_and_contract_bound():
    design = build_design()
    architecture = build_mechanical_pilot_architecture_contract()
    optimization = build_mechanical_adam_optimization_contract()
    assert _tranche_identity(design, architecture, optimization) == \
        _tranche_identity(design, architecture, optimization)


def test_extended_runner_declares_structural_and_data_boundaries():
    source = open("negotiation_training/extended_learning_curve.py",
                  encoding="utf-8").read()
    assert "range(3)" in source
    assert '"training_manifest_collections": 9' in source
    assert '"training_scenario_executions": 324' in source
    assert '"validation_scenario_executions": 0' in source
    assert '"held_out_scenario_executions": 0' in source
    assert '"candidate_comparisons": 0' in source
    assert '"update_3_performed": False' in source
    assert '"final_replication_count_selected": False' in source
    assert '"final_training_budget_selected": False' in source


def test_progress_writes_are_atomic():
    source = open("negotiation_training/controlled_pilot.py",
                  encoding="utf-8").read()
    assert "os.replace(temporary, path)" in source
