"""Local authority, queue promotion, and real SUMO presentation acceptance."""

# Import fields, replace from dataclasses for the operations below.
from dataclasses import fields, replace
# Import sha256 from hashlib for the operations below.
from hashlib import sha256
# Import SimpleNamespace from types for the operations below.
from types import SimpleNamespace
# Import Path from pathlib for the operations below.
from pathlib import Path
# Import contextlib for use in this module.
import contextlib
# Import io for use in this module.
import io
# Import shutil for use in this module.
import shutil
# Import wraps from functools for the operations below.
from functools import wraps

# Import pytest for use in this module.
import pytest
# Import torch for use in this module.
import torch

# Import EgoExecutionContext, EgoCoordinationCommitment, ExecutionStateMessage,
# DecentralizedEgoExecutionController, ConflictZoneExecutionPlanner from negotiation_execution for the operations
# below.
from negotiation_execution import (EgoExecutionContext, EgoCoordinationCommitment,
    ExecutionStateMessage, DecentralizedEgoExecutionController,
    ConflictZoneExecutionPlanner)
# Import select_queue_heads, approach_queue_depth from runtime_simulation.queue_heads for the operations below.
from runtime_simulation.queue_heads import select_queue_heads, approach_queue_depth
# Import get_scenario from runtime_simulation.scenarios for the operations below.
from runtime_simulation.scenarios import get_scenario
# Import validate_presentation_schedule from runtime_simulation.schedule for the operations below.
from runtime_simulation.schedule import validate_presentation_schedule
# Import run_runtime_simulation, POLICY_PATH, _deliver_pair_commitments from runtime_simulation.runner for the
# operations below.
from runtime_simulation.runner import run_runtime_simulation, POLICY_PATH, _deliver_pair_commitments
# Import runner as panel_runner from runtime_simulation for the operations below.
from runtime_simulation import runner as panel_runner
# Import GraphTensorEncoder from negotiation_learning for the operations below.
from negotiation_learning import GraphTensorEncoder
# Import SAFE_SUMO_SPEED_MODE from config for the operations below.
from config import SAFE_SUMO_SPEED_MODE


# State using the inputs and processing steps below.
# Input progress: the supplied progress.
# Input lane: the supplied lane.
# Input lane_position: the supplied lane position.
# Output: a dictionary containing progress, width, length, lane_id, lane_position, speed,
# comfortable_deceleration_mps2.
def state(progress=-20.0, lane="n_in_0", lane_position=10.0):
    # Return a dictionary containing progress, width, length, lane_id, lane_position, speed,
    # comfortable_deceleration_mps2 to the caller.
    return {"progress": progress, "width": 1.8, "length": 5.0,
            # Store lane under 'lane_id'.
            # Store lane_position under 'lane_position'.
            "lane_id": lane, "lane_position": lane_position,
            # Store 4.0 under 'speed'.
            # Store 4.5 under 'comfortable_deceleration_mps2'.
            "speed": 4.0, "comfortable_deceleration_mps2": 4.5}


# Apply pytest.fixture as a decorator to configure the following definition.
@pytest.fixture
# Controller using the inputs and processing steps below.
# Output: the result of DecentralizedEgoExecutionController(paths, zones).
def controller():
    # Set paths to the result of SimpleNamespace().
    paths = SimpleNamespace(paths={p: SimpleNamespace(
        # Supply incoming_lane_id as the result of p.lower() plus the text '_in_0'.
        # Supply outgoing_lane_id as the result of p.lower() plus the text '_out_0'.
        incoming_lane_id=p.lower() + "_in_0", outgoing_lane_id=p.lower() + "_out_0",
        # Supply internal_lane_ids as a tuple containing the text ':' plus p.
        # Supply path_id as p.
        internal_lane_ids=(":" + p,), path_id=p) for p in "NESW"},
        # Declare s, p as input parameters.
        resolve_front_bumper_path_progress=lambda s, p: (s["progress"], None, None))
    # Set zones to the result of SimpleNamespace().
    zones = SimpleNamespace(zone_record=lambda *args: {
        # Store the text 'CZ' under 'zone_id'.
        # Store a tuple containing 0.0, 10.0 under 'first_path_distance_interval'.
        "zone_id": "CZ", "first_path_distance_interval": (0.0, 10.0),
        # Store a tuple containing 0.0, 10.0 under 'second_path_distance_interval'.
        "second_path_distance_interval": (0.0, 10.0)})
    # Return the result of DecentralizedEgoExecutionController(paths, zones) to the caller.
    return DecentralizedEgoExecutionController(paths, zones)


# Context using the inputs and processing steps below.
# Input ego: the ego vehicle used in this calculation.
# Input peer: the supplied peer.
# Input owed: the supplied owed.
# Output: the result of EgoExecutionContext(ego, the result of state(), the text 'N', 1.0, a tuple containing
# commitment, a tuple containing...).
def context(ego="arbitrary_ego", peer="arbitrary_peer", owed=True):
    # Set commitment to the result of EgoCoordinationCommitment(ego when owed, otherwise peer, peer when owed,
    # otherwise ego, a tuple containing the text...).
    commitment = EgoCoordinationCommitment(ego if owed else peer,
        # Supply peer when owed, otherwise ego to EgoCoordinationCommitment.
        peer if owed else ego, ("agreement",))
    # Return the result of EgoExecutionContext(ego, the result of state(), the text 'N', 1.0, a tuple containing
    # commitment, a tuple containing...) to the caller.
    return EgoExecutionContext(ego, state(), "N", 1.0, (commitment,),
        # Supply lane as the text 'e_in_0'.
        (ExecutionStateMessage(peer, "E", state(lane="e_in_0"), 1.0),), True, 1.0)


# Check context cannot accept global graph or unrelated commitments using the setup, calls, and assertions below.
# Input controller: the supplied controller.
# Output: no explicit value; normal completion returns None.
def test_context_cannot_accept_global_graph_or_unrelated_commitments(controller):
    # Set names to a set of f.name for f in the result of fields(EgoExecutionContext).
    names = {f.name for f in fields(EgoExecutionContext)}
    # Require the negation of names intersected with a set containing the text 'effective_graph', the text
    # 'ready_vehicle_ids', the text 'critic', the text 'actor_observations'; otherwise raise AssertionError.
    assert not names & {"effective_graph", "ready_vehicle_ids", "critic", "actor_observations"}
    # Enter the result of pytest.raises(ValueError) and run the enclosed operations within that context.
    with pytest.raises(ValueError, match="NONLOCAL_EXECUTION_COMMITMENT"):
        # Call replace with the supplied arguments.
        replace(context(), commitments=(EgoCoordinationCommitment("X", "Y", ()),))
    # Set inboxes to the result of _deliver_pair_commitments(a tuple containing a tuple containing the text 'A',
    # the text 'B', a tuple containing the text...).
    inboxes = _deliver_pair_commitments((("A", "B"), ("B", "C")), ("A", "B", "C"), ())
    # Require the number of entries in inboxes at 'A' equals 1; otherwise raise AssertionError.
    assert len(inboxes["A"]) == 1
    # Require whether every item is true in a lazy sequence of the text 'A' belongs to a tuple containing
    # c.yielding_vehicle_id, c.priority_vehicle_id for c in inboxes at 'A'; otherwise raise AssertionError.
    assert all("A" in (c.yielding_vehicle_id, c.priority_vehicle_id) for c in inboxes["A"])


# Check yielding ego derives own blocked zone and native stopping request using the setup, calls, and assertions
# below.
# Input controller: the supplied controller.
# Output: no explicit value; normal completion returns None.
def test_yielding_ego_derives_own_blocked_zone_and_native_stopping_request(controller):
    # Set own to the result of context().
    own = context()
    # Set decision to the result of controller.decide(own).
    decision = controller.decide(own)
    # Require decision.ego_id equals own.ego_id; otherwise raise AssertionError.
    assert decision.ego_id == own.ego_id
    # Require decision.permission equals the text 'BLOCKED_BY_PRECEDENCE'; otherwise raise AssertionError.
    assert decision.permission == "BLOCKED_BY_PRECEDENCE"
    # Require decision.blocked_zones equals a tuple containing a tuple containing the text 'CZ', 20.0, the text
    # 'arbitrary_peer'; otherwise raise AssertionError.
    assert decision.blocked_zones == (("CZ", 20.0, "arbitrary_peer"),)
    # Set api to the result of SimpleNamespace().
    api = SimpleNamespace(getSpeedMode=lambda ego: 31,
        # Declare ego as input parameter.
        getActionStepLength=lambda ego: .04,
        # Declare ego, speed, distance as input parameters.
        getStopSpeed=lambda ego, speed, distance: 2.0,
        # Declare ego as input parameter.
        getSpeedWithoutTraCI=lambda ego: 4.0)
    # Set constrained to the result of controller.constrain(own, decision, api, 0.04).
    constrained = controller.constrain(own, decision, api, .04)
    # Require constrained.requested_speed_mps equals 2.0; is less than own.ego_state at 'speed'; otherwise raise
    # AssertionError.
    assert constrained.requested_speed_mps == 2.0 < own.ego_state["speed"]
    # Require constrained.speed_constraints[0].vehicle_id equals own.ego_id; otherwise raise AssertionError.
    assert constrained.speed_constraints[0].vehicle_id == own.ego_id
    # Require constrained.speed_constraints[0].speed_mode equals SAFE_SUMO_SPEED_MODE; equals 31; otherwise raise
    # AssertionError.
    assert constrained.speed_constraints[0].speed_mode == SAFE_SUMO_SPEED_MODE == 31


# Check priority ego proceeds without consuming other decisions using the setup, calls, and assertions below.
# Input controller: the supplied controller.
# Output: no explicit value; normal completion returns None.
def test_priority_ego_proceeds_without_consuming_other_decisions(controller):
    # Set decision to the result of controller.decide(the result of context()).
    decision = controller.decide(context(owed=False))
    # Require decision.permission equals the text 'PERMITTED'; otherwise raise AssertionError.
    assert decision.permission == "PERMITTED"
    # Require the negation of decision.blocked_zones; otherwise raise AssertionError.
    assert not decision.blocked_zones
    # Require decision.decentralized_execution; otherwise raise AssertionError.
    assert decision.decentralized_execution
    # Require the negation of decision.centralized_execution_graph_used_for_control; otherwise raise
    # AssertionError.
    assert not decision.centralized_execution_graph_used_for_control


# Check follower advancement uses native stop without granting entry using the setup, calls, and assertions below.
# Input controller: the supplied controller.
# Output: no explicit value; normal completion returns None.
def test_follower_advancement_uses_native_stop_without_granting_entry(controller):
    # Set own to the result of replace(the result of context()).
    own=replace(context(),strict_admission=True,negotiation_eligible=False,
        # Supply ego_state as a dictionary built from the result of state().
        # Supply road_id as the text 'n_in'.
        # Supply lane_length as 100.0.
        ego_state=dict(state(),road_id='n_in',lane_length=100.))
    # Set held to the result of controller.decide(own).
    held=controller.decide(own)
    # Set calls to an empty list.
    calls=[]
    # Set api to the result of SimpleNamespace().
    api=SimpleNamespace(getSpeedMode=lambda _:31,getLaneIndex=lambda _:0,
        # Declare a, kw as input parameters.
        setStop=lambda *a,**kw:calls.append((a,kw)))
    # Set following to the result of controller.constrain(own, held, api, 0.04).
    following=controller.constrain(own,held,api,.04)
    # Require following.permission equals the text 'SAFE_HOLD'; otherwise raise AssertionError.
    assert following.permission=='SAFE_HOLD'
    # Require following.blocked_zones equals held.blocked_zones; otherwise raise AssertionError.
    assert following.blocked_zones==held.blocked_zones
    # Require following.requested_speed_mps is the same object as None and the negation of
    # following.speed_constraints; otherwise raise AssertionError.
    assert following.requested_speed_mps is None and not following.speed_constraints
    # Require the result of controller.native_hold.synchronize(own, following, controller.paths, api) equals the
    # text 'NATIVE_HOLD_INSTALLED'; otherwise raise AssertionError.
    assert controller.native_hold.synchronize(own,following,controller.paths,api)=='NATIVE_HOLD_INSTALLED'
    # Require calls[0][1] at 'pos' equals 99.999 and calls[0][1] at 'duration' is greater than 360; otherwise
    # raise AssertionError.
    assert calls[0][1]['pos']==99.999 and calls[0][1]['duration']>360
    # Physical intrusion is still a hard error even for an ineligible follower.
    # Enter the result of pytest.raises(RuntimeError) and run the enclosed operations within that context.
    with pytest.raises(RuntimeError,match='BLOCKED_VEHICLE_ENTERED_CONFLICT_ZONE'):
        # Call controller.decide with the supplied arguments.
        controller.decide(replace(own,ego_state=state(progress=1.,lane=':N')))


# Check promoted head without coordination retains speed constraint using the setup, calls, and assertions below.
# Input controller: the supplied controller.
# Output: no explicit value; normal completion returns None.
def test_promoted_head_without_coordination_retains_speed_constraint(controller):
    # Set own to the result of replace(the result of context()).
    own=replace(context(),strict_admission=True,negotiation_eligible=True,coordination_complete=False)
    # Set held to the result of controller.decide(own).
    held=controller.decide(own)
    # Set api to the result of SimpleNamespace().
    api=SimpleNamespace(getSpeedMode=lambda _:31,getActionStepLength=lambda _:.04,
        # Declare args, _ as input parameters.
        getStopSpeed=lambda *args:2.,getSpeedWithoutTraCI=lambda _:4.)
    # Set decision to the result of controller.constrain(own, held, api, 0.04).
    decision=controller.constrain(own,held,api,.04)
    # Require decision.permission equals the text 'SAFE_HOLD' and decision.requested_speed_mps equals 2.0;
    # otherwise raise AssertionError.
    assert decision.permission=='SAFE_HOLD' and decision.requested_speed_mps==2.
    # Require decision.speed_constraints; otherwise raise AssertionError.
    assert decision.speed_constraints


# Apply 'stale_coordination' as a decorator to configure the following definition.
@pytest.mark.parametrize("change", ["missing_coordination", "stale_coordination",
                                   "missing_clearance", "stale_clearance"])
# Check missing or stale local information safe holds using the setup, calls, and assertions below.
# Input controller: the supplied controller.
# Input change: the supplied change.
# Output: no explicit value; normal completion returns None.
def test_missing_or_stale_local_information_safe_holds(controller, change):
    # Set own to the result of context().
    own = context()
    # Set updates to a dictionary containing missing_coordination, stale_coordination, missing_clearance,
    # stale_clearance.
    updates = {"missing_coordination": {"coordination_complete": False},
               # Store a dictionary containing coordination_timestamp under 'stale_coordination'.
               # Store 0.96 under 'coordination_timestamp'.
               "stale_coordination": {"coordination_timestamp": .96},
               # Store a dictionary containing peer_messages under 'missing_clearance'.
               # Store an empty tuple under 'peer_messages'.
               "missing_clearance": {"peer_messages": ()},
               # Store a dictionary containing peer_messages under 'stale_clearance'.
               # Store a tuple containing the result of replace(own.peer_messages at 0) under 'peer_messages'.
               "stale_clearance": {"peer_messages": (
                   # Supply timestamp as 0.96.
                   replace(own.peer_messages[0], timestamp=.96),)}}
    # Set decision to the result of controller.decide(the result of replace(own)).
    decision = controller.decide(replace(own, **updates[change]))
    # Require decision.permission equals the text 'SAFE_HOLD'; otherwise raise AssertionError.
    assert decision.permission == "SAFE_HOLD"
    # Require decision.blocked_zones[0] at 1 equals 20.0; otherwise raise AssertionError.
    assert decision.blocked_zones[0][1] == 20.0


# Check observed priority clearance releases ego using the setup, calls, and assertions below.
# Input controller: the supplied controller.
# Output: no explicit value; normal completion returns None.
def test_observed_priority_clearance_releases_ego(controller):
    # Set own to the result of context().
    own = context()
    # Set cleared to the result of replace(own.peer_messages at 0).
    cleared = replace(own.peer_messages[0], state=state(progress=16.0))
    # Require controller.decide(replace(own, peer_messages=(cleared,))).permission equals the text 'PERMITTED';
    # otherwise raise AssertionError.
    assert controller.decide(replace(own, peer_messages=(cleared,))).permission == "PERMITTED"


# Check blocked entry is a hard safety failure using the setup, calls, and assertions below.
# Input controller: the supplied controller.
# Output: no explicit value; normal completion returns None.
def test_blocked_entry_is_a_hard_safety_failure(controller):
    # Set own to the result of context().
    own = context()
    # Require controller.decide(own).blocked_zones; otherwise raise AssertionError.
    assert controller.decide(own).blocked_zones
    # Enter the result of pytest.raises(RuntimeError) and run the enclosed operations within that context.
    with pytest.raises(RuntimeError, match="BLOCKED_VEHICLE_ENTERED_CONFLICT_ZONE"):
        # Call controller.decide with the supplied arguments.
        controller.decide(replace(own, ego_state=state(progress=1.0, lane=":N")))


# Check missing context junction hold cannot be crossed using the setup, calls, and assertions below.
# Input controller: the supplied controller.
# Output: no explicit value; normal completion returns None.
def test_missing_context_junction_hold_cannot_be_crossed(controller):
    # Set own to the result of replace(the result of context()).
    own = replace(context(), coordination_complete=False)
    # Require controller.decide(own).permission equals the text 'SAFE_HOLD'; otherwise raise AssertionError.
    assert controller.decide(own).permission == "SAFE_HOLD"
    # Enter the result of pytest.raises(RuntimeError) and run the enclosed operations within that context.
    with pytest.raises(RuntimeError, match="BLOCKED_VEHICLE_ENTERED_CONFLICT_ZONE"):
        # Call controller.decide with the supplied arguments.
        controller.decide(replace(own, ego_state=state(progress=1.0, lane=":N")))


# Check prior blocked entry is detected even if clearance message is lost using the setup, calls, and assertions
# below.
# Input controller: the supplied controller.
# Output: no explicit value; normal completion returns None.
def test_prior_blocked_entry_is_detected_even_if_clearance_message_is_lost(controller):
    # Set own to the result of context().
    own = context()
    # Call controller.decide with the supplied arguments.
    controller.decide(own)
    # Enter the result of pytest.raises(RuntimeError) and run the enclosed operations within that context.
    with pytest.raises(RuntimeError, match="BLOCKED_VEHICLE_ENTERED_CONFLICT_ZONE"):
        # Call controller.decide with the supplied arguments.
        controller.decide(replace(own, peer_messages=(),
            # Supply ego_state as the result of state().
            # Supply progress as 1.0.
            # Supply lane as the text ':N'.
            ego_state=state(progress=1.0, lane=":N")))


# Check controller instance cannot control a different ego using the setup, calls, and assertions below.
# Input controller: the supplied controller.
# Output: no explicit value; normal completion returns None.
def test_controller_instance_cannot_control_a_different_ego(controller):
    # Call controller.decide with the supplied arguments.
    controller.decide(context())
    # Enter the result of pytest.raises(ValueError) and run the enclosed operations within that context.
    with pytest.raises(ValueError, match="EXECUTION_CONTROLLER_EGO_MISMATCH"):
        # Call controller.decide with the supplied arguments.
        controller.decide(context(ego="other_ego"))


# Check native follower has no speed request using the setup, calls, and assertions below.
# Input controller: the supplied controller.
# Output: no explicit value; normal completion returns None.
def test_native_follower_has_no_speed_request(controller):
    # Set own to the result of replace(the result of context()).
    own = replace(context(), negotiation_eligible=False, coordination_complete=False)
    # Set decision to the result of controller.decide(own).
    decision = controller.decide(own)
    # Require decision.permission equals the text 'NATIVE_FOLLOWING'; otherwise raise AssertionError.
    assert decision.permission == "NATIVE_FOLLOWING"
    # Require decision.requested_speed_mps is the same object as None and the negation of decision.blocked_zones;
    # otherwise raise AssertionError.
    assert decision.requested_speed_mps is None and not decision.blocked_zones


# Check frontline selection uses physics and promotes after rear clears using the setup, calls, and assertions
# below.
# Input controller: the supplied controller.
# Output: no explicit value; normal completion returns None.
def test_frontline_selection_uses_physics_and_promotes_after_rear_clears(controller):
    # Set movements to a dictionary containing rear, front, east.
    movements = {"rear": "N", "front": "N", "east": "E"}
    # Set states to a dictionary containing rear, front, east.
    states = {"rear": state(lane_position=30), "front": state(lane_position=60),
              # Store the result of state() under 'east'.
              "east": state(lane="e_in_0", lane_position=40)}
    # Require the result of select_queue_heads(states, controller.paths, movements) equals a tuple containing the
    # text 'east', the text 'front'; otherwise raise AssertionError.
    assert select_queue_heads(states, controller.paths, movements) == ("east", "front")
    # Set states['front'] to the result of state().
    states["front"] = state(lane=":N", lane_position=2)
    # Require the text 'rear' does not belong to the result of select_queue_heads(states, controller.paths,
    # movements); otherwise raise AssertionError.
    assert "rear" not in select_queue_heads(states, controller.paths, movements)
    # Set states['front'] to the result of state().
    states["front"] = state(lane="n_out_0", lane_position=4)
    # Require the text 'rear' does not belong to the result of select_queue_heads(states, controller.paths,
    # movements); otherwise raise AssertionError.
    assert "rear" not in select_queue_heads(states, controller.paths, movements)
    # Set states['front'] to the result of state().
    states["front"] = state(lane="n_out_0", lane_position=6)
    # Require the result of select_queue_heads(states, controller.paths, movements) equals a tuple containing the
    # text 'east', the text 'rear'; otherwise raise AssertionError.
    assert select_queue_heads(states, controller.paths, movements) == ("east", "rear")


# Check dense schedule has 16 safe demand requests and all 12 movements using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_dense_schedule_has_16_safe_demand_requests_and_all_12_movements():
    # Set scenario to the result of get_scenario(the text 'congested_four_approach').
    scenario = get_scenario("congested_four_approach")
    # Set schedule to the result of validate_presentation_schedule(the result of scenario.schedule()).
    schedule = validate_presentation_schedule(scenario.schedule(), allow_repeated_movements=True)
    # Require scenario.vehicle_count equals 16; otherwise raise AssertionError.
    assert scenario.vehicle_count == 16
    # Require whether every item is true in a lazy sequence of the number of entries in schedule[a] equals 4 for a
    # in the text 'NESW'; otherwise raise AssertionError.
    assert all(len(schedule[a]) == 4 for a in "NESW")
    # Require the number of entries in a set of d.movement_path_id for rows in values from schedule equals 12;
    # otherwise raise AssertionError.
    assert len({d.movement_path_id for rows in schedule.values() for d in rows}) == 12
    # Require scenario.admission_mode equals the text 'INDEPENDENT_DEMAND'; otherwise raise AssertionError.
    assert scenario.admission_mode == "INDEPENDENT_DEMAND"
    # Require a list of d.scheduled_departure_seconds for d in schedule at 'N' equals a list containing 0, 1.5, 3,
    # 4.5; otherwise raise AssertionError.
    assert [d.scheduled_departure_seconds for d in schedule["N"]] == [0, 1.5, 3, 4.5]


# Check many live vehicles do not expand frontline using the setup, calls, and assertions below.
# Input controller: the supplied controller.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def test_many_live_vehicles_do_not_expand_frontline(controller):
    # Set (states, movements) to a tuple containing an empty dictionary, an empty dictionary.
    states, movements = {}, {}
    # Iterate over the text 'NESW', binding each item to approach.
    for approach in "NESW":
        # Iterate over the integer range defined by 4, binding each item to index.
        for index in range(4):
            # Set vehicle to formatted text built from the embedded values.
            vehicle = f"random_{approach}_{index}"
            # Set movements[vehicle] to approach.
            movements[vehicle] = approach
            # Set states[vehicle] to the result of state().
            states[vehicle] = state(lane=approach.lower() + "_in_0", lane_position=10 * index)
    # Require the number of entries in states equals 16; otherwise raise AssertionError.
    assert len(states) == 16
    # Require the number of entries in the result of select_queue_heads(states, controller.paths, movements)
    # equals 4; otherwise raise AssertionError.
    assert len(select_queue_heads(states, controller.paths, movements)) == 4
    # Require the result of approach_queue_depth(states, controller.paths, movements) equals the result of
    # dict.fromkeys(the text 'NESW', 4); otherwise raise AssertionError.
    assert approach_queue_depth(states, controller.paths, movements) == dict.fromkeys("NESW", 4)


# Fixture errors are not known liveness failures using the inputs and processing steps below.
# Input function: the supplied function.
# Output: checked.
def _fixture_errors_are_not_known_liveness_failures(function):
    # Apply wraps(function) as a decorator to configure the following definition.
    @wraps(function)
    # Checked using the inputs and processing steps below.
    # Input args: the supplied args.
    # Input kwargs: the supplied kwargs.
    # Output: the result of function(the unpacked values from args).
    # Processing: handle the specified errors.
    def checked(*args, **kwargs):
        # Attempt the enclosed operations and route matching exceptions to the handlers below.
        try:
            # Return the result of function(the unpacked values from args) to the caller.
            return function(*args, **kwargs)
        # Handle AssertionError as error using the recovery steps below.
        except AssertionError as error:
            # xfail(raises=AssertionError) must never consume safety, policy,
            # simulator or live-state contract failures in fixture setup.
            # Raise RuntimeError with the text 'DENSE_FIXTURE_CONTRACT_BREACH:' plus a string built from error to
            # stop this execution path.
            raise RuntimeError("DENSE_FIXTURE_CONTRACT_BREACH:" + str(error)) from error
    # Return checked to the caller.
    return checked


# Apply pytest.fixture(scope='module') as a decorator to configure the following definition.
@pytest.fixture(scope="module")
# Apply _fixture_errors_are_not_known_liveness_failures as a decorator to configure the following definition.
@_fixture_errors_are_not_known_liveness_failures
# Congested run using the inputs and processing steps below.
# Input tmp_path_factory: the supplied tmp path factory.
# Output: a tuple containing result, root.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def congested_run(tmp_path_factory):
    # Run this branch when the negation of the result of shutil.which(the text 'sumo').
    if not shutil.which("sumo"):
        # Call pytest.skip with the supplied arguments.
        pytest.skip("Real SUMO executable is required for presentation integration")
    # Set root to the result of tmp_path_factory.mktemp(the text 'congested_ego_execution').
    root = tmp_path_factory.mktemp("congested_ego_execution")
    # Set scenario to the result of get_scenario(the text 'congested_four_approach').
    scenario = get_scenario("congested_four_approach")
    # Set before to the hexadecimal digest from sha256(POLICY_PATH.read_bytes()).
    before = sha256(POLICY_PATH.read_bytes()).hexdigest()
    # Set forbidden_calls to an empty list.
    forbidden_calls = []
    # Forbidden using the inputs and processing steps below.
    # Input args: the supplied args.
    # Input kwargs: the supplied kwargs.
    # Output: no explicit value; normal completion returns None.
    def forbidden(*args, **kwargs):
        # Append True to forbidden_calls.
        forbidden_calls.append(True)
        # Raise AssertionError with the text 'Training, critic or global permission calculation invoked' to stop
        # this execution path.
        raise AssertionError("Training, critic or global permission calculation invoked")
    # Enter the result of pytest.MonkeyPatch.context() as patch and run the enclosed operations within that
    # context.
    with pytest.MonkeyPatch.context() as patch:
        # Set original_load to panel_runner._load_bundle.
        original_load = panel_runner._load_bundle
        # Set loaded_modules to an empty list.
        loaded_modules = []
        # Guarded load using the inputs and processing steps below.
        # Input path: the path or path object supplied by the caller.
        # Output: a tuple containing payload, bundle.
        # Processing: iterate over the relevant records.
        def guarded_load(path):
            # Set (payload, bundle) to the result of original_load(path).
            payload, bundle = original_load(path)
            # Call patch.setattr with the supplied arguments.
            patch.setattr(bundle.centralized_critic, "forward", forbidden)
            # Iterate over a tuple containing bundle.gnn, bundle.proposer_actor, bundle.responder_actor, binding
            # each item to module.
            for module in (bundle.gnn, bundle.proposer_actor, bundle.responder_actor):
                # Append a tuple containing module, a dictionary of key mapped to the result of value.clone() for
                # (key, value) in key/value pairs from... to loaded_modules.
                loaded_modules.append((module, {key: value.clone() for key, value in module.state_dict().items()}))
            # Return a tuple containing payload, bundle to the caller.
            return payload, bundle
        # Set original_encode to GraphTensorEncoder.encode.
        original_encode = GraphTensorEncoder.encode
        # Bounded encode using the inputs and processing steps below.
        # Input observation: the supplied observation.
        # Output: encoded.
        def bounded_encode(self, observation):
            # Set encoded to the result of original_encode(self, observation).
            encoded = original_encode(self, observation)
            # Require the number of entries in encoded.node_ids is at most 4; otherwise raise AssertionError.
            assert len(encoded.node_ids) <= 4
            # Return encoded to the caller.
            return encoded
        # Call patch.setattr with the supplied arguments.
        patch.setattr(panel_runner, "_load_bundle", guarded_load)
        # Call patch.setattr with the supplied arguments.
        patch.setattr(GraphTensorEncoder, "encode", bounded_encode)
        # Call patch.setattr with the supplied arguments.
        patch.setattr(torch.Tensor, "backward", forbidden)
        # Call patch.setattr with the supplied arguments.
        patch.setattr(torch.autograd, "backward", forbidden)
        # Call patch.setattr with the supplied arguments.
        patch.setattr(torch.optim.Adam, "step", forbidden)
        # Call patch.setattr with the supplied arguments.
        patch.setattr(ConflictZoneExecutionPlanner, "plan", forbidden)
        # Enter the result of contextlib.redirect_stdout(the result of io.StringIO()) and run the enclosed
        # operations within that context.
        with contextlib.redirect_stdout(io.StringIO()):
            # Set result to the result of run_runtime_simulation().
            result = run_runtime_simulation(duration_seconds=360,
                # Supply schedule as the result of scenario.schedule().
                # Supply admission_waves as scenario.admission_waves.
                schedule=scenario.schedule(), admission_waves=scenario.admission_waves,
                # Supply admission_mode as scenario.admission_mode.
                # Supply scenario_id as scenario.scenario_id.
                admission_mode=scenario.admission_mode, scenario_id=scenario.scenario_id,
                # Supply output_dir as root.
                # Supply web_live as True.
                # Supply browser_state_path as root joined with the path segment 'live_state.json'.
                output_dir=root, web_live=True, browser_state_path=root / "live_state.json")
        # Iterate over loaded_modules, binding each item to (module, original).
        for module, original in loaded_modules:
            # Require the negation of module.training; otherwise raise AssertionError.
            assert not module.training
            # Require whether every item is true in a lazy sequence of the result of torch.equal(original at key,
            # value) for (key, value) in key/value pairs from module.state_dict(); otherwise raise AssertionError.
            assert all(torch.equal(original[key], value) for key, value in module.state_dict().items())
    # Require the negation of forbidden_calls; otherwise raise AssertionError.
    assert not forbidden_calls
    # Require the hexadecimal digest from sha256(POLICY_PATH.read_bytes()) equals before; otherwise raise
    # AssertionError.
    assert sha256(POLICY_PATH.read_bytes()).hexdigest() == before
    # These checks are outside expected-failure test bodies: unsafe behavior,
    # execution/integrity regressions and corrupt live output must always fail.
    # Import json for use in this module.
    import json
    # Set live to the decoded data produced by json.loads from the text read from (root / 'live_state.json').
    live = json.loads((root / "live_state.json").read_text())
    # Set metrics to result at 'metrics'.
    metrics = result["metrics"]
    # Require metrics at 'collisions' equals metrics at 'blocked_zone_violations'; equals 0; otherwise raise
    # AssertionError.
    assert metrics["collisions"] == metrics["blocked_zone_violations"] == 0
    # Require metrics at 'maximum_negotiation_participants' is at most 4; otherwise raise AssertionError.
    assert metrics["maximum_negotiation_participants"] <= 4
    # Require metrics at 'centralized_critic_runtime_calls' equals 0; otherwise raise AssertionError.
    assert metrics["centralized_critic_runtime_calls"] == 0
    # Require result at 'policy_hash_unchanged' and result at 'decentralized_execution'; otherwise raise
    # AssertionError.
    assert result["policy_hash_unchanged"] and result["decentralized_execution"]
    # Require the negation of result at 'centralized_execution_graph_used_for_control'; otherwise raise
    # AssertionError.
    assert not result["centralized_execution_graph_used_for_control"]
    # Require whether every item is true in a lazy sequence of result at k equals 0 for k in a tuple containing
    # the text 'training_operations', the text 'backward_calls', the text 'optimizer_steps', the text...;
    # otherwise raise AssertionError.
    assert all(result[k] == 0 for k in ("training_operations", "backward_calls", "optimizer_steps", "parameter_updates"))
    # Require live at 'run_metrics' equals the decoded data produced by json.loads from the serialized data
    # produced by json.dumps; otherwise raise AssertionError.
    assert live["run_metrics"] == json.loads(json.dumps(metrics))
    # Require live at 'completed' equals metrics at 'total_vehicles_completed'; otherwise raise AssertionError.
    assert live["completed"] == metrics["total_vehicles_completed"]
    # Require metrics at 'total_vehicles_scheduled' equals metrics at 'total_vehicles_spawned'; equals 16;
    # otherwise raise AssertionError.
    assert metrics["total_vehicles_scheduled"] == metrics["total_vehicles_spawned"] == 16
    # Require metrics at 'maximum_simultaneous_active_vehicles' is at least 10; otherwise raise AssertionError.
    assert metrics["maximum_simultaneous_active_vehicles"] >= 10
    # Require metrics at 'maximum_simultaneously_moving_vehicles' is greater than 4; otherwise raise
    # AssertionError.
    assert metrics["maximum_simultaneously_moving_vehicles"] > 4
    # Require whether every item is true in a lazy sequence of metrics['maximum_per_approach_queue_depth'] at a is
    # greater than 1 for a in the text 'NESW'; otherwise raise AssertionError.
    assert all(metrics["maximum_per_approach_queue_depth"][a] > 1 for a in "NESW")
    # Require metrics at 'maximum_approaches_with_multiple_queued_vehicles' equals 4; otherwise raise
    # AssertionError.
    assert metrics["maximum_approaches_with_multiple_queued_vehicles"] == 4
    # Require the number of entries in result at 'actual_departure_seconds' equals 16; otherwise raise
    # AssertionError.
    assert len(result["actual_departure_seconds"]) == 16
    # Require the negation of result at 'pending_insertion_vehicle_ids'; otherwise raise AssertionError.
    assert not result["pending_insertion_vehicle_ids"]
    # Run this branch when result at 'run_status' differs from the text 'COMPLETED'.
    if result["run_status"] != "COMPLETED":
        # Require result at 'run_status' equals the text 'INCOMPLETE'; otherwise raise AssertionError.
        assert result["run_status"] == "INCOMPLETE"
        # Run this branch when 'movement_declaration_protocol' from result; use None if absent equals the text
        # 'CONDITIONAL_CLAIM_RECONCILIATION_V1'.
        if result.get("movement_declaration_protocol") == "CONDITIONAL_CLAIM_RECONCILIATION_V1":
            # Approved reconciliation fixes the old zero-discharge condition.
            # Keep partial progress distinct from the unchanged 16/16 test below.
            # Require 5 is at most metrics at 'total_vehicles_completed'; is less than 16; otherwise raise
            # AssertionError.
            assert 5 <= metrics["total_vehicles_completed"] < 16
            # Require metrics at 'current_active_vehicle_count' equals 16 minus metrics at
            # 'total_vehicles_completed'; otherwise raise AssertionError.
            assert metrics["current_active_vehicle_count"] == 16 - metrics["total_vehicles_completed"]
            # Require the number of entries in a set built from result at 'completed_vehicle_ids' equals metrics
            # at 'total_vehicles_completed'; otherwise raise AssertionError.
            assert len(set(result["completed_vehicle_ids"])) == metrics["total_vehicles_completed"]
            # Require metrics at 'mappo_decision_epochs' is greater than 0; otherwise raise AssertionError.
            assert metrics["mappo_decision_epochs"] > 0
            # Require whether any item is true in a lazy sequence of e at 'status' equals the text
            # 'NEGOTIATION_REQUIRED_REGULATORY_CYCLE' for e in result at 'events'; otherwise raise AssertionError.
            assert any(e["status"] == "NEGOTIATION_REQUIRED_REGULATORY_CYCLE" for e in result["events"])
        # Run this alternative branch when the preceding branch does not apply.
        else:
            # Require metrics at 'total_vehicles_completed' equals 0 and metrics at 'current_active_vehicle_count'
            # equals 16; otherwise raise AssertionError.
            assert metrics["total_vehicles_completed"] == 0 and metrics["current_active_vehicle_count"] == 16
            # Require result at 'events' and whether every item is true in a lazy sequence of e['status'] equals
            # 'COMMUNICATED_PRECEDENCE_DISAGREEMENT' for e in result at 'events'; otherwise raise AssertionError.
            assert result["events"] and all(e["status"] == "COMMUNICATED_PRECEDENCE_DISAGREEMENT" for e in result["events"])
    # Return a tuple containing result, root to the caller.
    return result, root


# Check real congested run has safe dense traffic and complete discharge using the setup, calls, and assertions
# below.
# Input congested_run: the supplied congested run.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def test_real_congested_run_has_safe_dense_traffic_and_complete_discharge(congested_run):
    # Set (result, _) to congested_run.
    result, _ = congested_run
    # Set metrics to result at 'metrics'.
    metrics = result["metrics"]
    # Require result at 'run_status' equals the text 'COMPLETED'; otherwise raise AssertionError.
    assert result["run_status"] == "COMPLETED"
    # Require metrics at 'total_vehicles_scheduled' equals metrics at 'total_vehicles_spawned'; equals 16;
    # otherwise raise AssertionError.
    assert metrics["total_vehicles_scheduled"] == metrics["total_vehicles_spawned"] == 16
    # Require metrics at 'total_vehicles_completed' equals 16; otherwise raise AssertionError.
    assert metrics["total_vehicles_completed"] == 16
    # Require metrics at 'maximum_simultaneous_active_vehicles' is at least 10; otherwise raise AssertionError.
    assert metrics["maximum_simultaneous_active_vehicles"] >= 10
    # Require metrics at 'maximum_simultaneously_moving_vehicles' is greater than 4; otherwise raise
    # AssertionError.
    assert metrics["maximum_simultaneously_moving_vehicles"] > 4
    # Require whether every item is true in a lazy sequence of metrics['maximum_per_approach_queue_depth'] at a is
    # greater than 1 for a in the text 'NESW'; otherwise raise AssertionError.
    assert all(metrics["maximum_per_approach_queue_depth"][a] > 1 for a in "NESW")
    # Require metrics at 'maximum_approaches_with_multiple_queued_vehicles' equals 4; otherwise raise
    # AssertionError.
    assert metrics["maximum_approaches_with_multiple_queued_vehicles"] == 4
    # Require metrics at 'maximum_negotiation_participants' is at most 4; otherwise raise AssertionError.
    assert metrics["maximum_negotiation_participants"] <= 4
    # Require metrics at 'collisions' equals metrics at 'blocked_zone_violations'; equals 0; otherwise raise
    # AssertionError.
    assert metrics["collisions"] == metrics["blocked_zone_violations"] == 0
    # Require metrics at 'centralized_critic_runtime_calls' equals 0; otherwise raise AssertionError.
    assert metrics["centralized_critic_runtime_calls"] == 0
    # Require result at 'policy_hash_unchanged'; otherwise raise AssertionError.
    assert result["policy_hash_unchanged"]
    # Require result at 'decentralized_execution'; otherwise raise AssertionError.
    assert result["decentralized_execution"]
    # Require the negation of result at 'centralized_execution_graph_used_for_control'; otherwise raise
    # AssertionError.
    assert not result["centralized_execution_graph_used_for_control"]
    # Require whether every item is true in a lazy sequence of result at k equals 0 for k in a tuple containing
    # the text 'training_operations', the text 'backward_calls', the text 'optimizer_steps', the text...;
    # otherwise raise AssertionError.
    assert all(result[k] == 0 for k in ("training_operations", "backward_calls",
        "optimizer_steps", "parameter_updates", "held_out_scenarios_consumed"))
    # Require the number of entries in result at 'actual_departure_seconds' equals 16; otherwise raise
    # AssertionError.
    assert len(result["actual_departure_seconds"]) == 16
    # Require the negation of result at 'pending_insertion_vehicle_ids'; otherwise raise AssertionError.
    assert not result["pending_insertion_vehicle_ids"]
    # Iterate over key/value pairs from result['actual_departure_seconds'], binding each item to (ego, departure).
    for ego, departure in result["actual_departure_seconds"].items():
        # Require departure is at least result['scheduled_departure_seconds'] at ego; otherwise raise
        # AssertionError.
        assert departure >= result["scheduled_departure_seconds"][ego]


# Check live state exports measured counts and execution flags using the setup, calls, and assertions below.
# Input congested_run: the supplied congested run.
# Output: no explicit value; normal completion returns None.
def test_live_state_exports_measured_counts_and_execution_flags(congested_run):
    # Import json for use in this module.
    import json
    # Set (result, root) to congested_run.
    result, root = congested_run
    # Set live to the decoded data produced by json.loads from the text read from (root / 'live_state.json').
    live = json.loads((root / "live_state.json").read_text())
    # Require live at 'run_metrics' equals the decoded data produced by json.loads from the serialized data
    # produced by json.dumps; otherwise raise AssertionError.
    assert live["run_metrics"] == json.loads(json.dumps(result["metrics"]))
    # Require live['run_metrics'] at 'decentralized_execution'; otherwise raise AssertionError.
    assert live["run_metrics"]["decentralized_execution"]
    # Require live['run_metrics'] at 'current_active_vehicle_count' equals 0; otherwise raise AssertionError.
    assert live["run_metrics"]["current_active_vehicle_count"] == 0
    # Require live at 'completed' equals 16; otherwise raise AssertionError.
    assert live["completed"] == 16
    # Require the negation of live at 'participants' and the negation of live at 'vehicles'; otherwise raise
    # AssertionError.
    assert not live["participants"] and not live["vehicles"]


# Check dense safety and decentralized integrity are not expected failures using the setup, calls, and assertions
# below.
# Input congested_run: the supplied congested run.
# Output: no explicit value; normal completion returns None.
def test_dense_safety_and_decentralized_integrity_are_not_expected_failures(congested_run):
    # Set (result, _) to congested_run.
    result, _ = congested_run
    # Set m to result at 'metrics'.
    m = result["metrics"]
    # Require m at 'collisions' equals m at 'blocked_zone_violations'; equals 0; otherwise raise AssertionError.
    assert m["collisions"] == m["blocked_zone_violations"] == 0
    # Require m at 'maximum_negotiation_participants' is at most 4; otherwise raise AssertionError.
    assert m["maximum_negotiation_participants"] <= 4
    # Require result at 'policy_hash_unchanged' and result at 'decentralized_execution'; otherwise raise
    # AssertionError.
    assert result["policy_hash_unchanged"] and result["decentralized_execution"]
    # Require the negation of result at 'centralized_execution_graph_used_for_control'; otherwise raise
    # AssertionError.
    assert not result["centralized_execution_graph_used_for_control"]
    # Require m at 'centralized_critic_runtime_calls' equals 0; otherwise raise AssertionError.
    assert m["centralized_critic_runtime_calls"] == 0


# Check dense live state preserves actual progress even when incomplete using the setup, calls, and assertions
# below.
# Input congested_run: the supplied congested run.
# Output: no explicit value; normal completion returns None.
def test_dense_live_state_preserves_actual_progress_even_when_incomplete(congested_run):
    # Import json for use in this module.
    import json
    # Set (result, root) to congested_run.
    result, root = congested_run
    # Set live to the decoded data produced by json.loads from the text read from (root / 'live_state.json').
    live = json.loads((root / "live_state.json").read_text())
    # Require live at 'run_metrics' equals the decoded data produced by json.loads from the serialized data
    # produced by json.dumps; otherwise raise AssertionError.
    assert live["run_metrics"] == json.loads(json.dumps(result["metrics"]))
    # Require live at 'completed' equals result['metrics'] at 'total_vehicles_completed'; otherwise raise
    # AssertionError.
    assert live["completed"] == result["metrics"]["total_vehicles_completed"]
    # Require live['run_metrics'] at 'current_active_vehicle_count' equals result['metrics'] at
    # 'current_active_vehicle_count'; otherwise raise AssertionError.
    assert live["run_metrics"]["current_active_vehicle_count"] == result["metrics"]["current_active_vehicle_count"]
