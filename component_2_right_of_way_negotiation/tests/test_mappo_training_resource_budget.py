# Import hashlib for use in this module.
import hashlib
# Import json for use in this module.
import json
# Import FrozenInstanceError, replace from dataclasses for the operations below.
from dataclasses import FrozenInstanceError, replace
# Import Path from pathlib for the operations below.
from pathlib import Path

# Import pytest for use in this module.
import pytest

# Import EXPECTED_V1_ID, TrainingResourceBudgetInput, derive_horizon, derive_resource_evidence,
# load_and_validate_v1, resolve_training_resource_budget, validate_resource_input from
# negotiation_training.resource_budget for the operations below.
from negotiation_training.resource_budget import (
    EXPECTED_V1_ID, TrainingResourceBudgetInput,
    derive_horizon, derive_resource_evidence, load_and_validate_v1,
    resolve_training_resource_budget, validate_resource_input)


# Approved using the inputs and processing steps below.
# Input kind: the supplied kind.
# Input value: the supplied value.
# Input unit: the supplied unit.
# Output: the result of TrainingResourceBudgetInput().
def approved(kind, value, unit=None):
    # Set units to a dictionary containing PPO_UPDATE_CYCLES_PER_REPLICATION,
    # TRAINING_MANIFEST_COLLECTIONS_PER_REPLICATION,...
    units = {
        "PPO_UPDATE_CYCLES_PER_REPLICATION": "PPO-update-cycles",
        "TRAINING_MANIFEST_COLLECTIONS_PER_REPLICATION":
            "TRAINING-manifest-collections",
        "SUMO_STEPS_PER_REPLICATION": "SUMO-steps",
        "WALL_CLOCK_SECONDS_PER_REPLICATION": "seconds"}
    # Return the result of TrainingResourceBudgetInput() to the caller.
    return TrainingResourceBudgetInput(
        # Supply input_id as a tuple containing the text 'TEST', kind, value.
        # Supply scope as the text 'PER_REPLICATION'.
        input_id=("TEST", kind, value), scope="PER_REPLICATION",
        # Supply budget_type as kind.
        # Supply budget_value as value.
        # Supply unit as unit or units at kind.
        budget_type=kind, budget_value=value, unit=unit or units[kind],
        # Supply justification_source as the text 'SUPERVISOR_TEST_FIXTURE_APPROVAL'.
        justification_source="SUPERVISOR_TEST_FIXTURE_APPROVAL",
        # Supply approval_status as the text 'SUPERVISOR_APPROVED'.
        approval_status="SUPERVISOR_APPROVED",
        # Supply provenance as a tuple containing a tuple containing the text 'status', the text 'RESOLVED', a
        # tuple containing the text 'source_path', the...
        provenance=(("status", "RESOLVED"), ("source_path", "TEST")))


# Check source v1 identity is exact using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_source_v1_identity_is_exact():
    # Set source to the result of load_and_validate_v1().
    source = load_and_validate_v1()
    # Require a tuple built from source['protocol'] at 'protocol_id' equals EXPECTED_V1_ID; otherwise raise
    # AssertionError.
    assert tuple(source["protocol"]["protocol_id"]) == EXPECTED_V1_ID
    # Require source at 'next_blocker' equals the text 'MAXIMUM_ACCEPTABLE_TRAINING_RESOURCE_BUDGET'; otherwise
    # raise AssertionError.
    assert source["next_blocker"] == \
        "MAXIMUM_ACCEPTABLE_TRAINING_RESOURCE_BUDGET"


# Check structural manifest steps are derived and verified using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_structural_manifest_steps_are_derived_and_verified():
    # Set evidence to the result of derive_resource_evidence().
    evidence = derive_resource_evidence()
    # Require evidence.training_manifest_scenario_count equals 36; otherwise raise AssertionError.
    assert evidence.training_manifest_scenario_count == 36
    # Require evidence.steps_per_scenario equals 5000; otherwise raise AssertionError.
    assert evidence.steps_per_scenario == 5000
    # Require evidence.sumo_steps_per_training_manifest equals 180000; otherwise raise AssertionError.
    assert evidence.sumo_steps_per_training_manifest == 180000
    # Require the number of entries in evidence.observed_manifest_runtime_values equals 9; otherwise raise
    # AssertionError.
    assert len(evidence.observed_manifest_runtime_values) == 9
    # Require the number of entries in evidence.observed_update_runtime_values equals 6; otherwise raise
    # AssertionError.
    assert len(evidence.observed_update_runtime_values) == 6
    # Require the number of entries in evidence.observed_replication_overhead_values equals 3; otherwise raise
    # AssertionError.
    assert len(evidence.observed_replication_overhead_values) == 3
    # Require evidence.manifest_runtime_bound equals the maximum of evidence.observed_manifest_runtime_values;
    # otherwise raise AssertionError.
    assert evidence.manifest_runtime_bound == max(
        # Supply evidence.observed_manifest_runtime_values to max.
        evidence.observed_manifest_runtime_values)
    # Require evidence.performance_values_used is the same object as False; otherwise raise AssertionError.
    assert evidence.performance_values_used is False


# Check update cycle budget maps exactly to h using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_update_cycle_budget_maps_exactly_to_h():
    # Set evidence to the result of derive_resource_evidence().
    evidence = derive_resource_evidence()
    # Require derive_horizon(approved('PPO_UPDATE_CYCLES_PER_REPLICATION', 4), evidence) at 0 equals 4; otherwise
    # raise AssertionError.
    assert derive_horizon(approved(
        # Supply evidence to derive_horizon.
        "PPO_UPDATE_CYCLES_PER_REPLICATION", 4), evidence)[0] == 4


# Check manifest collection budget maps to h minus one using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_manifest_collection_budget_maps_to_h_minus_one():
    # Set evidence to the result of derive_resource_evidence().
    evidence = derive_resource_evidence()
    # Require derive_horizon(approved('TRAINING_MANIFEST_COLLECTIONS_PER_REPLICATION', 5), evidence) at 0 equals
    # 4; otherwise raise AssertionError.
    assert derive_horizon(approved(
        # Supply evidence to derive_horizon.
        "TRAINING_MANIFEST_COLLECTIONS_PER_REPLICATION", 5), evidence)[0] == 4


# Check sumo step budget uses floor and preserves unused capacity using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_sumo_step_budget_uses_floor_and_preserves_unused_capacity():
    # Set evidence to the result of derive_resource_evidence().
    evidence = derive_resource_evidence()
    # Set (h, unused, _) to the result of derive_horizon(the result of approved(the text
    # 'SUMO_STEPS_PER_REPLICATION', 750000), evidence).
    h, unused, _ = derive_horizon(approved(
        # Supply evidence to derive_horizon.
        "SUMO_STEPS_PER_REPLICATION", 750000), evidence)
    # Require h equals 3; otherwise raise AssertionError.
    assert h == 3
    # Require unused equals 30000; otherwise raise AssertionError.
    assert unused == 30000
    # Require h plus 1 multiplied by evidence.sumo_steps_per_training_manifest is at most 750000; otherwise raise
    # AssertionError.
    assert (h + 1) * evidence.sumo_steps_per_training_manifest <= 750000


# Apply 'resource' as a decorator to configure the following definition.
@pytest.mark.parametrize("resource", [
    # Include the result of approved(the text 'PPO_UPDATE_CYCLES_PER_REPLICATION', 0) in this list.
    approved("PPO_UPDATE_CYCLES_PER_REPLICATION", 0),
    # Include the result of approved(the text 'TRAINING_MANIFEST_COLLECTIONS_PER_REPLICATION', 1) in this list.
    approved("TRAINING_MANIFEST_COLLECTIONS_PER_REPLICATION", 1),
    # Include the result of approved(the text 'SUMO_STEPS_PER_REPLICATION', 359999) in this list.
    approved("SUMO_STEPS_PER_REPLICATION", 359999),
])
# Check budget too small for one update using the setup, calls, and assertions below.
# Input resource: the supplied resource.
# Output: no explicit value; normal completion returns None.
def test_budget_too_small_for_one_update(resource):
    # Set evidence to the result of derive_resource_evidence().
    evidence = derive_resource_evidence()
    # Enter the result of pytest.raises(ValueError) and run the enclosed operations within that context.
    with pytest.raises(ValueError, match="TOO_SMALL"):
        # Call derive_horizon with the supplied arguments.
        derive_horizon(resource, evidence)


# Check wall clock mapping uses max component bounds not averages using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_wall_clock_mapping_uses_max_component_bounds_not_averages():
    # Set evidence to the result of derive_resource_evidence().
    evidence = derive_resource_evidence()
    # Set required_for_h2 to 3 multiplied by evidence.manifest_runtime_bound plus 2 multiplied by
    # evidence.update_runtime_bound plus evidence.overhead_bound.
    required_for_h2 = (3 * evidence.manifest_runtime_bound +
                       # Evaluate 2 multiplied by evidence.update_runtime_bound as part of the enclosing
                       # expression.
                       2 * evidence.update_runtime_bound +
                       # Evaluate evidence.overhead_bound as part of the enclosing expression.
                       evidence.overhead_bound)
    # Set (h, unused, bound) to the result of derive_horizon(the result of approved(the text
    # 'WALL_CLOCK_SECONDS_PER_REPLICATION', required_for_h2, the text...).
    h, unused, bound = derive_horizon(approved(
        # Supply required_for_h2 to approved.
        "WALL_CLOCK_SECONDS_PER_REPLICATION", required_for_h2,
        # Supply evidence to derive_horizon.
        "seconds"), evidence)
    # Require h equals 2; otherwise raise AssertionError.
    assert h == 2
    # Require bound equals the result of pytest.approx(required_for_h2); otherwise raise AssertionError.
    assert bound == pytest.approx(required_for_h2)
    # Require unused equals the result of pytest.approx(0.0); otherwise raise AssertionError.
    assert unused == pytest.approx(0.0)
    # Require evidence.wall_clock_mapping_status equals the text
    # 'CONSERVATIVE_HISTORICAL_MAX_COMPONENT_MAPPING_AVAILABLE'; otherwise raise AssertionError.
    assert evidence.wall_clock_mapping_status == \
        "CONSERVATIVE_HISTORICAL_MAX_COMPONENT_MAPPING_AVAILABLE"


# Check production external input remains unresolved using the setup, calls, and assertions below.
# Input tmp_path: the supplied tmp path.
# Output: no explicit value; normal completion returns None.
def test_production_external_input_remains_unresolved(tmp_path):
    # Set (resolution, artifact) to the result of resolve_training_resource_budget().
    resolution, artifact = resolve_training_resource_budget(
        # Supply resolution_path as tmp_path joined with the path segment 'resolution.json'.
        resolution_path=tmp_path / "resolution.json",
        # Supply v2_path as tmp_path joined with the path segment 'v2.json'.
        v2_path=tmp_path / "v2.json")
    # Require resolution.resource_budget_resolved is the same object as False; otherwise raise AssertionError.
    assert resolution.resource_budget_resolved is False
    # Require resolution.resource_input.scope equals the text 'PER_REPLICATION'; otherwise raise AssertionError.
    assert resolution.resource_input.scope == "PER_REPLICATION"
    # Require resolution.resource_input.budget_value is the same object as None; otherwise raise AssertionError.
    assert resolution.resource_input.budget_value is None
    # Require resolution.derived_H is the same object as None; otherwise raise AssertionError.
    assert resolution.derived_H is None
    # Require artifact at 'status' equals the text 'TRAINING_RESOURCE_BUDGET_EXTERNAL_INPUT_REQUIRED'; otherwise
    # raise AssertionError.
    assert artifact["status"] == \
        "TRAINING_RESOURCE_BUDGET_EXTERNAL_INPUT_REQUIRED"
    # Require artifact at 'new_protocol_identity_created' is the same object as False; otherwise raise
    # AssertionError.
    assert artifact["new_protocol_identity_created"] is False
    # Require the negation of whether (tmp_path / 'v2.json') exists; otherwise raise AssertionError.
    assert not (tmp_path / "v2.json").exists()


# Check present but unapproved value does not resolve using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_present_but_unapproved_value_does_not_resolve():
    # Set value to the result of replace(the result of approved(the text 'PPO_UPDATE_CYCLES_PER_REPLICATION', 2)).
    value = replace(approved("PPO_UPDATE_CYCLES_PER_REPLICATION", 2),
                    # Supply justification_source as None.
                    justification_source=None,
                    # Supply approval_status as the text 'NOT_SUPPLIED'.
                    approval_status="NOT_SUPPLIED")
    # Require the result of validate_resource_input(value) equals the text
    # 'RESOURCE_BUDGET_VALUE_PRESENT_BUT_NOT_JUSTIFIED'; otherwise raise AssertionError.
    assert validate_resource_input(value) == \
        "RESOURCE_BUDGET_VALUE_PRESENT_BUT_NOT_JUSTIFIED"


# Check forbidden performance approval is rejected using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_forbidden_performance_approval_is_rejected():
    # Set value to the result of replace(the result of approved(the text 'PPO_UPDATE_CYCLES_PER_REPLICATION', 2)).
    value = replace(approved("PPO_UPDATE_CYCLES_PER_REPLICATION", 2),
                    # Supply approval_status as the text 'PERFORMANCE_SELECTED'.
                    approval_status="PERFORMANCE_SELECTED")
    # Enter the result of pytest.raises(ValueError) and run the enclosed operations within that context.
    with pytest.raises(ValueError, match="PROVENANCE_FORBIDDEN"):
        # Call validate_resource_input with the supplied arguments.
        validate_resource_input(value)


# Check total project scope is rejected using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_total_project_scope_is_rejected():
    # Set value to the result of replace(the result of approved(the text 'PPO_UPDATE_CYCLES_PER_REPLICATION', 2)).
    value = replace(approved("PPO_UPDATE_CYCLES_PER_REPLICATION", 2),
                    # Supply scope as the text 'TOTAL_EXPERIMENT'.
                    scope="TOTAL_EXPERIMENT")
    # Enter the result of pytest.raises(ValueError) and run the enclosed operations within that context.
    with pytest.raises(ValueError, match="PER_REPLICATION"):
        # Call validate_resource_input with the supplied arguments.
        validate_resource_input(value)


# Check resolved fixture creates new deterministic v2 without mutating v1 using the setup, calls, and assertions
# below.
# Input tmp_path: the supplied tmp path.
# Output: no explicit value; normal completion returns None.
def test_resolved_fixture_creates_new_deterministic_v2_without_mutating_v1(tmp_path):
    # Set original to the bytes read from Path('results/mappo_predeclared_selection_protocol.json').
    original = Path("results/mappo_predeclared_selection_protocol.json").read_bytes()
    # Set input_path to tmp_path joined with the path segment 'input.json'.
    input_path = tmp_path / "input.json"
    # Write the supplied text to input_path.
    input_path.write_text(json.dumps({
        # Store a dictionary containing status, scope, budget_type, budget_value, unit, justification_source,
        # approval_status under 'MAXIMUM_ACCEPTABLE_TRAINING_RESOURCE_BUDGET'.
        "MAXIMUM_ACCEPTABLE_TRAINING_RESOURCE_BUDGET": {
            "status": "RESOLVED", "scope": "PER_REPLICATION",
            "budget_type": "PPO_UPDATE_CYCLES_PER_REPLICATION",
            # Store 4 under 'budget_value'.
            # Store the text 'PPO-update-cycles' under 'unit'.
            "budget_value": 4, "unit": "PPO-update-cycles",
            "justification_source": "SUPERVISOR_TEST_FIXTURE_APPROVAL",
            # Store the text 'SUPERVISOR_APPROVED' under 'approval_status'.
            "approval_status": "SUPERVISOR_APPROVED"}}), encoding="utf-8")
    # Set (first, artifact1) to the result of resolve_training_resource_budget().
    first, artifact1 = resolve_training_resource_budget(
        # Supply external_input_path as input_path.
        external_input_path=input_path,
        # Supply resolution_path as tmp_path joined with the path segment 'r1.json'.
        # Supply v2_path as tmp_path joined with the path segment 'v21.json'.
        resolution_path=tmp_path / "r1.json", v2_path=tmp_path / "v21.json")
    # Set (second, artifact2) to the result of resolve_training_resource_budget().
    second, artifact2 = resolve_training_resource_budget(
        # Supply external_input_path as input_path.
        external_input_path=input_path,
        # Supply resolution_path as tmp_path joined with the path segment 'r2.json'.
        # Supply v2_path as tmp_path joined with the path segment 'v22.json'.
        resolution_path=tmp_path / "r2.json", v2_path=tmp_path / "v22.json")
    # Require first.derived_H equals 4; otherwise raise AssertionError.
    assert first.derived_H == 4
    # Require first.derived_policy_state_count equals 5; otherwise raise AssertionError.
    assert first.derived_policy_state_count == 5
    # Require first.derived_sumo_steps_per_replication equals 900000; otherwise raise AssertionError.
    assert first.derived_sumo_steps_per_replication == 900000
    # Require artifact1 at 'new_v2_protocol_identity' equals artifact2 at 'new_v2_protocol_identity'; otherwise
    # raise AssertionError.
    assert artifact1["new_v2_protocol_identity"] == \
        artifact2["new_v2_protocol_identity"]
    # Require artifact1 at 'new_v2_protocol_identity' differs from EXPECTED_V1_ID; otherwise raise AssertionError.
    assert artifact1["new_v2_protocol_identity"] != EXPECTED_V1_ID
    # Require the bytes read from Path('results/mappo_predeclared_selection_protocol.json') equals original;
    # otherwise raise AssertionError.
    assert Path("results/mappo_predeclared_selection_protocol.json").read_bytes() == original


# Check changing approved budget changes v2 identity using the setup, calls, and assertions below.
# Input tmp_path: the supplied tmp path.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def test_changing_approved_budget_changes_v2_identity(tmp_path):
    # Set identities to an empty list.
    identities = []
    # Iterate over a tuple containing 3, 4, binding each item to value.
    for value in (3, 4):
        # Set path to tmp_path divided by formatted text built from the embedded values.
        path = tmp_path / f"input{value}.json"
        # Write the supplied text to path.
        path.write_text(json.dumps({
            # Store a dictionary containing status, scope, budget_type, budget_value, unit, justification_source,
            # approval_status under 'MAXIMUM_ACCEPTABLE_TRAINING_RESOURCE_BUDGET'.
            "MAXIMUM_ACCEPTABLE_TRAINING_RESOURCE_BUDGET": {
                "status": "RESOLVED", "scope": "PER_REPLICATION",
                "budget_type": "PPO_UPDATE_CYCLES_PER_REPLICATION",
                # Store value under 'budget_value'.
                # Store the text 'PPO-update-cycles' under 'unit'.
                "budget_value": value, "unit": "PPO-update-cycles",
                "justification_source": "PROJECT_TEST_FIXTURE_APPROVAL",
                # Store the text 'PROJECT_APPROVED' under 'approval_status'.
                "approval_status": "PROJECT_APPROVED"}}), encoding="utf-8")
        # Set (_, artifact) to the result of resolve_training_resource_budget().
        _, artifact = resolve_training_resource_budget(
            # Supply external_input_path as path.
            external_input_path=path,
            # Supply resolution_path as tmp_path divided by formatted text built from the embedded values.
            resolution_path=tmp_path / f"r{value}.json",
            # Supply v2_path as tmp_path divided by formatted text built from the embedded values.
            v2_path=tmp_path / f"v2{value}.json")
        # Append artifact at 'new_v2_protocol_identity' to identities.
        identities.append(artifact["new_v2_protocol_identity"])
    # Require identities at 0 differs from identities at 1; otherwise raise AssertionError.
    assert identities[0] != identities[1]


# Check horizon derivation is performance independent using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_horizon_derivation_is_performance_independent():
    # Set evidence to the result of derive_resource_evidence().
    evidence = derive_resource_evidence()
    # Set resource to the result of approved(the text 'SUMO_STEPS_PER_REPLICATION', 900000).
    resource = approved("SUMO_STEPS_PER_REPLICATION", 900000)
    # Set before to the result of derive_horizon(resource, evidence).
    before = derive_horizon(resource, evidence)
    # Resource evidence intentionally has no C0/C1/C2 fields to alter.
    # Require the negation of whether evidence exposes the requested attribute; otherwise raise AssertionError.
    assert not hasattr(evidence, "C0")
    # Require the result of derive_horizon(resource, evidence) equals before; otherwise raise AssertionError.
    assert derive_horizon(resource, evidence) == before


# Check records are immutable using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_records_are_immutable():
    # Set evidence to the result of derive_resource_evidence().
    evidence = derive_resource_evidence()
    # Enter the result of pytest.raises(FrozenInstanceError) and run the enclosed operations within that context.
    with pytest.raises(FrozenInstanceError):
        # Set evidence.steps_per_scenario to 1.
        evidence.steps_per_scenario = 1


# Check no execution side effects in production resolution using the setup, calls, and assertions below.
# Input tmp_path: the supplied tmp path.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def test_no_execution_side_effects_in_production_resolution(tmp_path):
    # Set (resolution, artifact) to the result of resolve_training_resource_budget().
    resolution, artifact = resolve_training_resource_budget(
        # Supply resolution_path as tmp_path joined with the path segment 'resolution.json'.
        resolution_path=tmp_path / "resolution.json",
        # Supply v2_path as tmp_path joined with the path segment 'v2.json'.
        v2_path=tmp_path / "v2.json")
    # Require resolution.performance_used_to_choose_budget is the same object as False; otherwise raise
    # AssertionError.
    assert resolution.performance_used_to_choose_budget is False
    # Require resolution.performance_used_to_derive_H is the same object as False; otherwise raise AssertionError.
    assert resolution.performance_used_to_derive_H is False
    # Iterate over a tuple containing the text 'new_sumo_executions', the text 'training_episodes', the text
    # 'optimizer_invocations', the text..., binding each item to name.
    for name in ("new_sumo_executions", "training_episodes",
                 "optimizer_invocations", "backward_calls",
                 "parameter_updates", "validation_executions",
                 "held_out_executions"):
        # Require artifact at name equals 0; otherwise raise AssertionError.
        assert artifact[name] == 0


# Check module has no sumo training or optimizer execution imports using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_module_has_no_sumo_training_or_optimizer_execution_imports():
    # Set source to the result of
    # Path('negotiation_training/resource_budget.py').read_text(encoding='utf-8').lower().
    source = Path("negotiation_training/resource_budget.py").read_text(
        # Supply encoding as the text 'utf-8'.
        encoding="utf-8").lower()
    # Require the text 'traci' does not belong to source; otherwise raise AssertionError.
    assert "traci" not in source
    # Require the text 'mechanicalmappotrainer' does not belong to source; otherwise raise AssertionError.
    assert "mechanicalmappotrainer" not in source
    # Require the text 'extendedmappolearningcurverunner' does not belong to source; otherwise raise
    # AssertionError.
    assert "extendedmappolearningcurverunner" not in source
    # Require the text 'optimizer.step' does not belong to source; otherwise raise AssertionError.
    assert "optimizer.step" not in source
    # Require the text '.backward(' does not belong to source; otherwise raise AssertionError.
    assert ".backward(" not in source
