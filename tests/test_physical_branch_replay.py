"""Step 5J.2B.2 deterministic replay contracts and boundaries."""

from dataclasses import FrozenInstanceError
import inspect

import pytest

from joint_negotiation_validation import real_training_evidence
from negotiation_execution.replay import (PAIR_SELECTION_METHOD,
    PhysicalBranchReplayRunner, build_replay_specifications,
    execution_semantics, select_causal_branch_pair)
from negotiation_execution.replay_models import PreBranchPhysicalStateFingerprint


@pytest.fixture(scope="module")
def setup():
    evidence = real_training_evidence()
    pair = select_causal_branch_pair(evidence["branches"])
    scenario, specifications = build_replay_specifications(evidence, pair)
    return evidence, pair, scenario, specifications


def test_pair_selection_is_deterministic_executable_and_semantically_distinct(setup):
    evidence, pair, _, _ = setup
    assert pair == select_causal_branch_pair(tuple(reversed(evidence["branches"])))
    assert all(item.graph_executable for item in pair)
    assert pair[0].effective_precedence_graph != pair[1].effective_precedence_graph
    assert execution_semantics(pair[0]) != execution_semantics(pair[1])
    assert PAIR_SELECTION_METHOD.startswith("FIRST_CANONICAL_EXECUTABLE_PAIR")


def test_pair_selection_source_has_no_outcome_metric_access():
    source = inspect.getsource(select_causal_branch_pair).lower()
    forbidden = ("reward", "travel_time", "throughput", "collision", "crossing_time")
    assert not any(item in source for item in forbidden)


def test_replay_specification_is_frozen_and_preserves_frozen_inputs(setup):
    evidence, pair, scenario, specifications = setup
    first = specifications[0]
    with pytest.raises(FrozenInstanceError):
        first.episode_end_time = 1.0
    assert first.branch_id == pair[0].branch_id
    assert first.scheduled_spawn_steps == scenario.scheduled_spawn_steps
    assert first.scheduled_spawn_times == scenario.scheduled_spawn_times
    assert first.scenario_manifest_id == evidence["design"]["manifests"][
        __import__("experimentation").ScenarioRole.TRAINING].manifest_id
    assert first.provenance["new_replay_seed"] is False
    assert first.provenance["validation_role_executions"] == 0
    assert first.provenance["held_out_role_executions"] == 0


def fingerprint(speed=1.0):
    return PreBranchPhysicalStateFingerprint(
        ("scenario",), 1.0, 25, ("AV",),
        (("AV", 1.0, 2.0, speed, 0.0, "lane", 3.0, "road", 5.0,
          1.8, 2.0, 4.5, 7.0, 13.89),), (("AV", "B"),),
        (("scenario",), 1.0, "JOINT"), (("AV", "B"),),
        ((('AV', 'B'), (True, True)),), "PROFILE", "NETWORK")


def test_fingerprint_is_complete_immutable_and_exact():
    first, same, changed = fingerprint(), fingerprint(), fingerprint(1.0000000000000002)
    assert first == same and first.fingerprint_id == same.fingerprint_id
    assert first != changed and first.fingerprint_id != changed.fingerprint_id
    with pytest.raises(FrozenInstanceError): first.simulation_timestamp = 2.0
    assert len(first.vehicle_states[0]) == 14


def test_replay_command_has_no_random_or_seed_and_preserves_safety():
    command = PhysicalBranchReplayRunner.COMMAND_ARGUMENTS
    assert "--random" not in command
    assert "--seed" not in command
    source = inspect.getsource(PhysicalBranchReplayRunner)
    assert "setSpeedMode(vehicle_id, SAFE_SUMO_SPEED_MODE)" in source
    assert "setSpeed(vehicle_id, -1.0)" in source
    assert "build_speed_constraint" in source
    assert "distance_to_entry" in source


def test_runner_uses_fresh_runtime_objects_and_existing_objective():
    source = inspect.getsource(PhysicalBranchReplayRunner.run)
    for constructor in ("ObservationManager()", "ConflictEntryMonitor()",
                        "VehicleDemandLedger()", "V2VPrecedenceClaimBus()"):
        assert constructor in source
    assert "measure_vehicle_travel_times" in source
    assert "total_team_travel_time_seconds" in source
    assert "raw_team_reward" in source
    assert "torch.optim" not in source
    assert "backward(" not in source


def test_planner_and_protocol_are_not_cycle_breakers():
    planner = inspect.getsource(__import__(
        "negotiation_execution.planner", fromlist=["ConflictZoneExecutionPlanner"]
    ).ConflictZoneExecutionPlanner)
    replay = inspect.getsource(PhysicalBranchReplayRunner)
    assert "remove_edge" not in planner + replay
    assert "winner" not in planner + replay
    assert "evaluate_all_claims" not in replay  # delegated to authoritative enumerator

