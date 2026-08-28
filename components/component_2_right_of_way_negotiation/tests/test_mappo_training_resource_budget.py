import hashlib
import json
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from negotiation_training.resource_budget import (
    EXPECTED_V1_ID, TrainingResourceBudgetInput,
    derive_horizon, derive_resource_evidence, load_and_validate_v1,
    resolve_training_resource_budget, validate_resource_input)


def approved(kind, value, unit=None):
    units = {
        "PPO_UPDATE_CYCLES_PER_REPLICATION": "PPO-update-cycles",
        "TRAINING_MANIFEST_COLLECTIONS_PER_REPLICATION":
            "TRAINING-manifest-collections",
        "SUMO_STEPS_PER_REPLICATION": "SUMO-steps",
        "WALL_CLOCK_SECONDS_PER_REPLICATION": "seconds"}
    return TrainingResourceBudgetInput(
        input_id=("TEST", kind, value), scope="PER_REPLICATION",
        budget_type=kind, budget_value=value, unit=unit or units[kind],
        justification_source="SUPERVISOR_TEST_FIXTURE_APPROVAL",
        approval_status="SUPERVISOR_APPROVED",
        provenance=(("status", "RESOLVED"), ("source_path", "TEST")))


def test_source_v1_identity_is_exact():
    source = load_and_validate_v1()
    assert tuple(source["protocol"]["protocol_id"]) == EXPECTED_V1_ID
    assert source["next_blocker"] == \
        "MAXIMUM_ACCEPTABLE_TRAINING_RESOURCE_BUDGET"


def test_structural_manifest_steps_are_derived_and_verified():
    evidence = derive_resource_evidence()
    assert evidence.training_manifest_scenario_count == 36
    assert evidence.steps_per_scenario == 5000
    assert evidence.sumo_steps_per_training_manifest == 180000
    assert len(evidence.observed_manifest_runtime_values) == 9
    assert len(evidence.observed_update_runtime_values) == 6
    assert len(evidence.observed_replication_overhead_values) == 3
    assert evidence.manifest_runtime_bound == max(
        evidence.observed_manifest_runtime_values)
    assert evidence.performance_values_used is False


def test_update_cycle_budget_maps_exactly_to_h():
    evidence = derive_resource_evidence()
    assert derive_horizon(approved(
        "PPO_UPDATE_CYCLES_PER_REPLICATION", 4), evidence)[0] == 4


def test_manifest_collection_budget_maps_to_h_minus_one():
    evidence = derive_resource_evidence()
    assert derive_horizon(approved(
        "TRAINING_MANIFEST_COLLECTIONS_PER_REPLICATION", 5), evidence)[0] == 4


def test_sumo_step_budget_uses_floor_and_preserves_unused_capacity():
    evidence = derive_resource_evidence()
    h, unused, _ = derive_horizon(approved(
        "SUMO_STEPS_PER_REPLICATION", 750000), evidence)
    assert h == 3
    assert unused == 30000
    assert (h + 1) * evidence.sumo_steps_per_training_manifest <= 750000


@pytest.mark.parametrize("resource", [
    approved("PPO_UPDATE_CYCLES_PER_REPLICATION", 0),
    approved("TRAINING_MANIFEST_COLLECTIONS_PER_REPLICATION", 1),
    approved("SUMO_STEPS_PER_REPLICATION", 359999),
])
def test_budget_too_small_for_one_update(resource):
    evidence = derive_resource_evidence()
    with pytest.raises(ValueError, match="TOO_SMALL"):
        derive_horizon(resource, evidence)


def test_wall_clock_mapping_uses_max_component_bounds_not_averages():
    evidence = derive_resource_evidence()
    required_for_h2 = (3 * evidence.manifest_runtime_bound +
                       2 * evidence.update_runtime_bound +
                       evidence.overhead_bound)
    h, unused, bound = derive_horizon(approved(
        "WALL_CLOCK_SECONDS_PER_REPLICATION", required_for_h2,
        "seconds"), evidence)
    assert h == 2
    assert bound == pytest.approx(required_for_h2)
    assert unused == pytest.approx(0.0)
    assert evidence.wall_clock_mapping_status == \
        "CONSERVATIVE_HISTORICAL_MAX_COMPONENT_MAPPING_AVAILABLE"


def test_production_external_input_remains_unresolved(tmp_path):
    resolution, artifact = resolve_training_resource_budget(
        resolution_path=tmp_path / "resolution.json",
        v2_path=tmp_path / "v2.json")
    assert resolution.resource_budget_resolved is False
    assert resolution.resource_input.scope == "PER_REPLICATION"
    assert resolution.resource_input.budget_value is None
    assert resolution.derived_H is None
    assert artifact["status"] == \
        "TRAINING_RESOURCE_BUDGET_EXTERNAL_INPUT_REQUIRED"
    assert artifact["new_protocol_identity_created"] is False
    assert not (tmp_path / "v2.json").exists()


def test_present_but_unapproved_value_does_not_resolve():
    value = replace(approved("PPO_UPDATE_CYCLES_PER_REPLICATION", 2),
                    justification_source=None,
                    approval_status="NOT_SUPPLIED")
    assert validate_resource_input(value) == \
        "RESOURCE_BUDGET_VALUE_PRESENT_BUT_NOT_JUSTIFIED"


def test_forbidden_performance_approval_is_rejected():
    value = replace(approved("PPO_UPDATE_CYCLES_PER_REPLICATION", 2),
                    approval_status="PERFORMANCE_SELECTED")
    with pytest.raises(ValueError, match="PROVENANCE_FORBIDDEN"):
        validate_resource_input(value)


def test_total_project_scope_is_rejected():
    value = replace(approved("PPO_UPDATE_CYCLES_PER_REPLICATION", 2),
                    scope="TOTAL_EXPERIMENT")
    with pytest.raises(ValueError, match="PER_REPLICATION"):
        validate_resource_input(value)


def test_resolved_fixture_creates_new_deterministic_v2_without_mutating_v1(tmp_path):
    original = Path("results/mappo_predeclared_selection_protocol.json").read_bytes()
    input_path = tmp_path / "input.json"
    input_path.write_text(json.dumps({
        "MAXIMUM_ACCEPTABLE_TRAINING_RESOURCE_BUDGET": {
            "status": "RESOLVED", "scope": "PER_REPLICATION",
            "budget_type": "PPO_UPDATE_CYCLES_PER_REPLICATION",
            "budget_value": 4, "unit": "PPO-update-cycles",
            "justification_source": "SUPERVISOR_TEST_FIXTURE_APPROVAL",
            "approval_status": "SUPERVISOR_APPROVED"}}), encoding="utf-8")
    first, artifact1 = resolve_training_resource_budget(
        external_input_path=input_path,
        resolution_path=tmp_path / "r1.json", v2_path=tmp_path / "v21.json")
    second, artifact2 = resolve_training_resource_budget(
        external_input_path=input_path,
        resolution_path=tmp_path / "r2.json", v2_path=tmp_path / "v22.json")
    assert first.derived_H == 4
    assert first.derived_policy_state_count == 5
    assert first.derived_sumo_steps_per_replication == 900000
    assert artifact1["new_v2_protocol_identity"] == \
        artifact2["new_v2_protocol_identity"]
    assert artifact1["new_v2_protocol_identity"] != EXPECTED_V1_ID
    assert Path("results/mappo_predeclared_selection_protocol.json").read_bytes() == original


def test_changing_approved_budget_changes_v2_identity(tmp_path):
    identities = []
    for value in (3, 4):
        path = tmp_path / f"input{value}.json"
        path.write_text(json.dumps({
            "MAXIMUM_ACCEPTABLE_TRAINING_RESOURCE_BUDGET": {
                "status": "RESOLVED", "scope": "PER_REPLICATION",
                "budget_type": "PPO_UPDATE_CYCLES_PER_REPLICATION",
                "budget_value": value, "unit": "PPO-update-cycles",
                "justification_source": "PROJECT_TEST_FIXTURE_APPROVAL",
                "approval_status": "PROJECT_APPROVED"}}), encoding="utf-8")
        _, artifact = resolve_training_resource_budget(
            external_input_path=path,
            resolution_path=tmp_path / f"r{value}.json",
            v2_path=tmp_path / f"v2{value}.json")
        identities.append(artifact["new_v2_protocol_identity"])
    assert identities[0] != identities[1]


def test_horizon_derivation_is_performance_independent():
    evidence = derive_resource_evidence()
    resource = approved("SUMO_STEPS_PER_REPLICATION", 900000)
    before = derive_horizon(resource, evidence)
    # Resource evidence intentionally has no C0/C1/C2 fields to alter.
    assert not hasattr(evidence, "C0")
    assert derive_horizon(resource, evidence) == before


def test_records_are_immutable():
    evidence = derive_resource_evidence()
    with pytest.raises(FrozenInstanceError):
        evidence.steps_per_scenario = 1


def test_no_execution_side_effects_in_production_resolution(tmp_path):
    resolution, artifact = resolve_training_resource_budget(
        resolution_path=tmp_path / "resolution.json",
        v2_path=tmp_path / "v2.json")
    assert resolution.performance_used_to_choose_budget is False
    assert resolution.performance_used_to_derive_H is False
    for name in ("new_sumo_executions", "training_episodes",
                 "optimizer_invocations", "backward_calls",
                 "parameter_updates", "validation_executions",
                 "held_out_executions"):
        assert artifact[name] == 0


def test_module_has_no_sumo_training_or_optimizer_execution_imports():
    source = Path("negotiation_training/resource_budget.py").read_text(
        encoding="utf-8").lower()
    assert "traci" not in source
    assert "mechanicalmappotrainer" not in source
    assert "extendedmappolearningcurverunner" not in source
    assert "optimizer.step" not in source
    assert ".backward(" not in source
