"""Step 5J.2B.2 deterministic replay contracts and boundaries."""

# Import FrozenInstanceError from dataclasses for the operations below.
from dataclasses import FrozenInstanceError
# Import inspect for use in this module.
import inspect

# Import pytest for use in this module.
import pytest

# Import real_training_evidence from joint_negotiation_validation for the operations below.
from joint_negotiation_validation import real_training_evidence
# Import PAIR_SELECTION_METHOD, PhysicalBranchReplayRunner, build_replay_specifications, execution_semantics,
# select_causal_branch_pair from negotiation_execution.replay for the operations below.
from negotiation_execution.replay import (PAIR_SELECTION_METHOD,
    PhysicalBranchReplayRunner, build_replay_specifications,
    execution_semantics, select_causal_branch_pair)
# Import PreBranchPhysicalStateFingerprint from negotiation_execution.replay_models for the operations below.
from negotiation_execution.replay_models import PreBranchPhysicalStateFingerprint


# Apply pytest.fixture(scope='module') as a decorator to configure the following definition.
@pytest.fixture(scope="module")
# Setup using the inputs and processing steps below.
# Output: a tuple containing evidence, pair, scenario, specifications.
def setup():
    # Set evidence to the result of real_training_evidence().
    evidence = real_training_evidence()
    # Set pair to the result of select_causal_branch_pair(evidence at 'branches').
    pair = select_causal_branch_pair(evidence["branches"])
    # Set (scenario, specifications) to the result of build_replay_specifications(evidence, pair).
    scenario, specifications = build_replay_specifications(evidence, pair)
    # Return a tuple containing evidence, pair, scenario, specifications to the caller.
    return evidence, pair, scenario, specifications


# Check pair selection is deterministic executable and semantically distinct using the setup, calls, and
# assertions below.
# Input setup: the supplied setup.
# Output: no explicit value; normal completion returns None.
def test_pair_selection_is_deterministic_executable_and_semantically_distinct(setup):
    # Set (evidence, pair, _, _) to setup.
    evidence, pair, _, _ = setup
    # Require pair equals the result of select_causal_branch_pair(a tuple built from the reverse traversal of
    # evidence['branches']); otherwise raise AssertionError.
    assert pair == select_causal_branch_pair(tuple(reversed(evidence["branches"])))
    # Require whether every item is true in a lazy sequence of item.graph_executable for item in pair; otherwise
    # raise AssertionError.
    assert all(item.graph_executable for item in pair)
    # Require pair[0].effective_precedence_graph differs from pair[1].effective_precedence_graph; otherwise raise
    # AssertionError.
    assert pair[0].effective_precedence_graph != pair[1].effective_precedence_graph
    # Require the result of execution_semantics(pair at 0) differs from the result of execution_semantics(pair at
    # 1); otherwise raise AssertionError.
    assert execution_semantics(pair[0]) != execution_semantics(pair[1])
    # Require the result of PAIR_SELECTION_METHOD.startswith(the text 'FIRST_CANONICAL_EXECUTABLE_PAIR');
    # otherwise raise AssertionError.
    assert PAIR_SELECTION_METHOD.startswith("FIRST_CANONICAL_EXECUTABLE_PAIR")


# Check pair selection source has no outcome metric access using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_pair_selection_source_has_no_outcome_metric_access():
    # Set source to the result of inspect.getsource(select_causal_branch_pair).lower().
    source = inspect.getsource(select_causal_branch_pair).lower()
    # Set forbidden to a tuple containing the text 'reward', the text 'travel_time', the text 'throughput', the
    # text 'collision', the text...
    forbidden = ("reward", "travel_time", "throughput", "collision", "crossing_time")
    # Require the negation of whether any item is true in a lazy sequence of item belongs to source for item in
    # forbidden; otherwise raise AssertionError.
    assert not any(item in source for item in forbidden)


# Check replay specification is frozen and preserves frozen inputs using the setup, calls, and assertions below.
# Input setup: the supplied setup.
# Output: no explicit value; normal completion returns None.
def test_replay_specification_is_frozen_and_preserves_frozen_inputs(setup):
    # Set (evidence, pair, scenario, specifications) to setup.
    evidence, pair, scenario, specifications = setup
    # Set first to specifications at 0.
    first = specifications[0]
    # Enter the result of pytest.raises(FrozenInstanceError) and run the enclosed operations within that context.
    with pytest.raises(FrozenInstanceError):
        # Set first.episode_end_time to 1.0.
        first.episode_end_time = 1.0
    # Require first.branch_id equals pair[0].branch_id; otherwise raise AssertionError.
    assert first.branch_id == pair[0].branch_id
    # Require first.scheduled_spawn_steps equals scenario.scheduled_spawn_steps; otherwise raise AssertionError.
    assert first.scheduled_spawn_steps == scenario.scheduled_spawn_steps
    # Require first.scheduled_spawn_times equals scenario.scheduled_spawn_times; otherwise raise AssertionError.
    assert first.scheduled_spawn_times == scenario.scheduled_spawn_times
    # Require first.scenario_manifest_id equals
    # evidence['design']['manifests'][__import__('experimentation').ScenarioRole.TRAINING].manifest_id; otherwise
    # raise AssertionError.
    assert first.scenario_manifest_id == evidence["design"]["manifests"][
        # Evaluate __import__('experimentation').ScenarioRole.TRAINING as part of the enclosing expression.
        __import__("experimentation").ScenarioRole.TRAINING].manifest_id
    # Require first.provenance at 'new_replay_seed' is the same object as False; otherwise raise AssertionError.
    assert first.provenance["new_replay_seed"] is False
    # Require first.provenance at 'validation_role_executions' equals 0; otherwise raise AssertionError.
    assert first.provenance["validation_role_executions"] == 0
    # Require first.provenance at 'held_out_role_executions' equals 0; otherwise raise AssertionError.
    assert first.provenance["held_out_role_executions"] == 0


# Fingerprint using the inputs and processing steps below.
# Input speed: the supplied speed.
# Output: the result of PreBranchPhysicalStateFingerprint(a tuple containing the text 'scenario', 1.0, 25, a tuple
# containing the text 'AV', a tuple...).
def fingerprint(speed=1.0):
    # Return the result of PreBranchPhysicalStateFingerprint(a tuple containing the text 'scenario', 1.0, 25, a
    # tuple containing the text 'AV', a tuple...) to the caller.
    return PreBranchPhysicalStateFingerprint(
        # Supply a tuple containing the text 'scenario' to PreBranchPhysicalStateFingerprint.
        ("scenario",), 1.0, 25, ("AV",),
        # Supply a tuple containing a tuple containing the text 'AV', 1.0, 2.0, speed, 0.0, the text 'lane', 3.0,
        # the text 'road', 5.0, 1.8,... to PreBranchPhysicalStateFingerprint.
        (("AV", 1.0, 2.0, speed, 0.0, "lane", 3.0, "road", 5.0,
          # Supply a tuple containing a tuple containing the text 'AV', the text 'B' to
          # PreBranchPhysicalStateFingerprint.
          1.8, 2.0, 4.5, 7.0, 13.89),), (("AV", "B"),),
        # Supply a tuple containing a tuple containing the text 'scenario', 1.0, the text 'JOINT' to
        # PreBranchPhysicalStateFingerprint.
        (("scenario",), 1.0, "JOINT"), (("AV", "B"),),
        # Supply a tuple containing a tuple containing a tuple containing the text 'AV', the text 'B', a tuple
        # containing True, True to PreBranchPhysicalStateFingerprint.
        ((('AV', 'B'), (True, True)),), "PROFILE", "NETWORK")


# Check fingerprint is complete immutable and exact using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_fingerprint_is_complete_immutable_and_exact():
    # Set (first, same, changed) to a tuple containing the result of fingerprint(), the result of fingerprint(),
    # the result of fingerprint(1.0000000000000002).
    first, same, changed = fingerprint(), fingerprint(), fingerprint(1.0000000000000002)
    # Require first equals same and first.fingerprint_id equals same.fingerprint_id; otherwise raise
    # AssertionError.
    assert first == same and first.fingerprint_id == same.fingerprint_id
    # Require first differs from changed and first.fingerprint_id differs from changed.fingerprint_id; otherwise
    # raise AssertionError.
    assert first != changed and first.fingerprint_id != changed.fingerprint_id
    # Enter the result of pytest.raises(FrozenInstanceError) and run the enclosed operations within that context.
    # Set first.simulation_timestamp to 2.0.
    with pytest.raises(FrozenInstanceError): first.simulation_timestamp = 2.0
    # Require the number of entries in first.vehicle_states at 0 equals 14; otherwise raise AssertionError.
    assert len(first.vehicle_states[0]) == 14


# Check replay command has no random or seed and preserves safety using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_replay_command_has_no_random_or_seed_and_preserves_safety():
    # Set command to PhysicalBranchReplayRunner.COMMAND_ARGUMENTS.
    command = PhysicalBranchReplayRunner.COMMAND_ARGUMENTS
    # Require the text '--random' does not belong to command; otherwise raise AssertionError.
    assert "--random" not in command
    # Require the text '--seed' does not belong to command; otherwise raise AssertionError.
    assert "--seed" not in command
    # Set source to the result of inspect.getsource(PhysicalBranchReplayRunner).
    source = inspect.getsource(PhysicalBranchReplayRunner)
    # Require the text 'setSpeedMode(vehicle_id, SAFE_SUMO_SPEED_MODE)' belongs to source; otherwise raise
    # AssertionError.
    assert "setSpeedMode(vehicle_id, SAFE_SUMO_SPEED_MODE)" in source
    # Require the text 'setSpeed(vehicle_id, -1.0)' belongs to source; otherwise raise AssertionError.
    assert "setSpeed(vehicle_id, -1.0)" in source
    # Require the text 'build_sumo_native_speed_constraint' belongs to source; otherwise raise AssertionError.
    assert "build_sumo_native_speed_constraint" in source
    # Require the text 'distance_to_entry' belongs to source; otherwise raise AssertionError.
    assert "distance_to_entry" in source


# Check runner uses fresh runtime objects and existing objective using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def test_runner_uses_fresh_runtime_objects_and_existing_objective():
    # Set source to the result of inspect.getsource(PhysicalBranchReplayRunner.run).
    source = inspect.getsource(PhysicalBranchReplayRunner.run)
    # Iterate over a tuple containing the text 'ObservationManager()', the text 'ConflictEntryMonitor()', the text
    # 'VehicleDemandLedger()', the..., binding each item to constructor.
    for constructor in ("ObservationManager()", "ConflictEntryMonitor()",
                        "VehicleDemandLedger()", "V2VPrecedenceClaimBus()"):
        # Require constructor belongs to source; otherwise raise AssertionError.
        assert constructor in source
    # Require the text 'measure_vehicle_travel_times' belongs to source; otherwise raise AssertionError.
    assert "measure_vehicle_travel_times" in source
    # Require the text 'total_team_travel_time_seconds' belongs to source; otherwise raise AssertionError.
    assert "total_team_travel_time_seconds" in source
    # Require the text 'raw_team_reward' belongs to source; otherwise raise AssertionError.
    assert "raw_team_reward" in source
    # Require the text 'torch.optim' does not belong to source; otherwise raise AssertionError.
    assert "torch.optim" not in source
    # Require the text 'backward(' does not belong to source; otherwise raise AssertionError.
    assert "backward(" not in source


# Check planner and protocol are not cycle breakers using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_planner_and_protocol_are_not_cycle_breakers():
    # Set planner to the result of inspect.getsource(__import__('negotiation_execution.planner',...).
    planner = inspect.getsource(__import__(
        # Supply fromlist as a list containing the text 'ConflictZoneExecutionPlanner'.
        "negotiation_execution.planner", fromlist=["ConflictZoneExecutionPlanner"]
    ).ConflictZoneExecutionPlanner)
    # Set replay to the result of inspect.getsource(PhysicalBranchReplayRunner).
    replay = inspect.getsource(PhysicalBranchReplayRunner)
    # Require the text 'remove_edge' does not belong to planner plus replay; otherwise raise AssertionError.
    assert "remove_edge" not in planner + replay
    # Require the text 'winner' does not belong to planner plus replay; otherwise raise AssertionError.
    assert "winner" not in planner + replay
    # Require the text 'evaluate_all_claims' does not belong to replay; otherwise raise AssertionError.
    assert "evaluate_all_claims" not in replay  # delegated to authoritative enumerator
