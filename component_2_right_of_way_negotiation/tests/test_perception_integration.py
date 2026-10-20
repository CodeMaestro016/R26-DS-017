"""Integration tests for SUMO state collection, perception, and the LDM."""

# Import math for use in this module.
import math
# Import xml.etree.ElementTree as ET for use in this module.
import xml.etree.ElementTree as ET

# Import pytest for use in this module.
import pytest

# Import environment for use in this module.
import environment
# Import PROJECT_ROOT from config for the operations below.
from config import PROJECT_ROOT
# Import SUMOEnv from environment for the operations below.
from environment import SUMOEnv
# Import ObservationManager from observation for the operations below.
from observation import ObservationManager
# Import get_intersection_geometry from map_geometry for the operations below.
from map_geometry import get_intersection_geometry


# Sumo state using the inputs and processing steps below.
# Input position: the supplied position.
# Input route_id: the supplied route id.
# Output: a dictionary containing position, speed, heading_radians, length, width, pos, vel, angle_degrees,
# lane_id,...
def sumo_state(position, route_id="route_w_left"):
    # Return a dictionary containing position, speed, heading_radians, length, width, pos, vel, angle_degrees,
    # lane_id,... to the caller.
    return {
        # Store position under 'position'.
        "position": position,
        # Store 5.0 under 'speed'.
        "speed": 5.0,
        # Store 0.0 under 'heading_radians'.
        "heading_radians": 0.0,
        # Store 4.5 under 'length'.
        "length": 4.5,
        # Store 1.8 under 'width'.
        "width": 1.8,
        # Store position under 'pos'.
        "pos": position,
        # Store 5.0 under 'vel'.
        "vel": 5.0,
        # Store 0.0 under 'angle_degrees'.
        "angle_degrees": 0.0,
        "lane_id": "w_in_0",
        # Store 20.0 under 'lane_position'.
        "lane_position": 20.0,
        # Store 100.0 under 'lane_length'.
        "lane_length": 100.0,
        "road_id": "w_in",
        # Store route_id under 'route_id'.
        "route_id": route_id,
        # Store 0 under 'route_index'.
        "route_index": 0,
        # Store 2.0 under 'max_acceleration_mps2'.
        "max_acceleration_mps2": 2.0,
        # Store 4.5 under 'comfortable_deceleration_mps2'.
        "comfortable_deceleration_mps2": 4.5,
        # Store 7.0 under 'emergency_deceleration_mps2'.
        "emergency_deceleration_mps2": 7.0,
        # Store 13.89 under 'max_speed_mps'.
        "max_speed_mps": 13.89,
    }


# Check geometric sensor dimensions and detections reach ldm using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_geometric_sensor_dimensions_and_detections_reach_ldm():
    # Set manager to the result of ObservationManager().
    manager = ObservationManager()
    # Set (cx, cy) to get_intersection_geometry().center_xy.
    cx, cy = get_intersection_geometry().center_xy
    # Set states to a dictionary containing ego, target.
    states = {
        # Store the result of sumo_state(a tuple containing cx, cy minus 10.0) under 'ego'.
        "ego": sumo_state((cx, cy - 10.0)),
        # Store the result of sumo_state(a tuple containing cx, cy plus 10.0, the text 'route_n_right') under
        # 'target'.
        "target": sumo_state((cx, cy + 10.0), "route_n_right"),
    }
    # Update manager with the supplied entries.
    manager.update(states, 0.04)

    # Set ego_ldm to the result of manager.get_ldm(the text 'ego').
    ego_ldm = manager.get_ldm("ego")
    # Require a set built from ego_ldm.tracks equals a set containing the text 'ego', the text 'target'; otherwise
    # raise AssertionError.
    assert set(ego_ldm.tracks) == {"ego", "target"}
    # Require manager.perception_interface.profile equals the text 'GEOMETRIC_SENSOR'; otherwise raise
    # AssertionError.
    assert manager.perception_interface.profile == "GEOMETRIC_SENSOR"
    # Set detection to manager.perception_interface.generate_observations('ego', {key: states['ego'][key] for key
    # in... at 'target'.
    detection = manager.perception_interface.generate_observations(
        "ego",
        # Supply a dictionary of key mapped to states['ego'] at key for key in a tuple containing the text
        # 'position', the text 'speed', the text 'heading_radians', the text 'length', the text 'width',... to
        # manager.perception_interface.generate_observations.
        {key: states["ego"][key] for key in (
            "position", "speed", "heading_radians", "length", "width",
            "lane_id", "lane_position", "lane_length", "road_id",
        )},
        # Supply a dictionary of vehicle_id mapped to a dictionary of key mapped to state at key for key in a
        # tuple containing the text 'position', the text 'speed', the text 'heading_radians', the text 'length',
        # the text 'width',... for (vehicle_id, state) in key/value pairs from states to
        # manager.perception_interface.generate_observations.
        {
            # Evaluate a dictionary of key mapped to state at key for key in a tuple containing the text
            # 'position', the text 'speed', the text 'heading_radians', the text 'length', the text 'width',... as
            # part of the enclosing expression.
            vehicle_id: {key: state[key] for key in (
                "position", "speed", "heading_radians", "length", "width",
                "lane_id", "lane_position", "lane_length", "road_id",
            )}
            # Evaluate a tuple containing vehicle_id, state as part of the enclosing expression.
            for vehicle_id, state in states.items()
        },
        # Supply 0.04 to the enclosing expression.
        0.04,
    # Supply the text 'target' to the enclosing expression.
    )["target"]
    # Require detection at 'length' equals 4.5; otherwise raise AssertionError.
    assert detection["length"] == 4.5
    # Require detection at 'width' equals 1.8; otherwise raise AssertionError.
    assert detection["width"] == 1.8


# Check route truth does not enter perception or ldm tracks using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def test_route_truth_does_not_enter_perception_or_ldm_tracks():
    # Set manager to the result of ObservationManager().
    manager = ObservationManager()
    # Set (cx, cy) to get_intersection_geometry().center_xy.
    cx, cy = get_intersection_geometry().center_xy
    # Set states to a dictionary containing ego, target.
    states = {
        # Store the result of sumo_state(a tuple containing cx, cy minus 10.0) under 'ego'.
        "ego": sumo_state((cx, cy - 10.0)),
        # Store the result of sumo_state(a tuple containing cx, cy plus 10.0, the text 'route_n_right') under
        # 'target'.
        "target": sumo_state((cx, cy + 10.0), "route_n_right"),
    }
    # Update manager with the supplied entries.
    manager.update(states, 0.04)
    # Set forbidden to a set containing the text 'route_id', the text 'ground_truth_route_id', the text
    # 'route_index'.
    forbidden = {"route_id", "ground_truth_route_id", "route_index"}
    # Iterate over values from manager.ldms, binding each item to ldm.
    for ldm in manager.ldms.values():
        # Require the negation of whether ldm exposes the requested attribute; otherwise raise AssertionError.
        assert not hasattr(ldm, "evaluation_route_truth")
        # Iterate over values from ldm.tracks, binding each item to track.
        for track in ldm.tracks.values():
            # Require the result of forbidden.isdisjoint(track); otherwise raise AssertionError.
            assert forbidden.isdisjoint(track)


# Check departure and reset clear perception diagnostics using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_departure_and_reset_clear_perception_diagnostics():
    # Set manager to the result of ObservationManager().
    manager = ObservationManager()
    # Set (cx, cy) to get_intersection_geometry().center_xy.
    cx, cy = get_intersection_geometry().center_xy
    # Set states to a dictionary containing ego, target.
    states = {
        # Store the result of sumo_state(a tuple containing cx, cy minus 10.0) under 'ego'.
        "ego": sumo_state((cx, cy - 10.0)),
        # Store the result of sumo_state(a tuple containing cx, cy plus 10.0) under 'target'.
        "target": sumo_state((cx, cy + 10.0)),
    }
    # Update manager with the supplied entries.
    manager.update(states, 0.04)
    # Require a set built from the result of manager.perception_interface.get_last_diagnostics() equals a set
    # containing the text 'ego', the text 'target'; otherwise raise AssertionError.
    assert set(manager.perception_interface.get_last_diagnostics()) == {
        "ego", "target"
    }

    # Update manager with the supplied entries.
    manager.update({"ego": states["ego"]}, 0.08)
    # Require the text 'target' does not belong to the result of
    # manager.perception_interface.get_last_diagnostics(); otherwise raise AssertionError.
    assert "target" not in manager.perception_interface.get_last_diagnostics()
    # Call manager.reset with the supplied arguments.
    manager.reset()
    # Require the result of manager.perception_interface.get_last_diagnostics() equals an empty dictionary;
    # otherwise raise AssertionError.
    assert manager.perception_interface.get_last_diagnostics() == {}
    # Require the result of manager.perception_interface.get_last_summary() equals an empty dictionary; otherwise
    # raise AssertionError.
    assert manager.perception_interface.get_last_summary() == {}


# Check environment collects canonical perception fields using the setup, calls, and assertions below.
# Input monkeypatch: the supplied monkeypatch.
# Output: no explicit value; normal completion returns None.
def test_environment_collects_canonical_perception_fields(monkeypatch):
    # Set vehicle to environment.traci.vehicle.
    vehicle = environment.traci.vehicle
    # Set lane to environment.traci.lane.
    lane = environment.traci.lane
    # Call monkeypatch.setattr with the supplied arguments.
    monkeypatch.setattr(vehicle, "getIDList", lambda: ("AV_1",))
    # Call monkeypatch.setattr with the supplied arguments.
    monkeypatch.setattr(vehicle, "getAngle", lambda _: 90.0)
    # Call monkeypatch.setattr with the supplied arguments.
    monkeypatch.setattr(vehicle, "getPosition", lambda _: (12.0, 34.0))
    # Call monkeypatch.setattr with the supplied arguments.
    monkeypatch.setattr(vehicle, "getSpeed", lambda _: 7.5)
    # Call monkeypatch.setattr with the supplied arguments.
    monkeypatch.setattr(vehicle, "getAcceleration", lambda _: 0.2)
    # Call monkeypatch.setattr with the supplied arguments.
    monkeypatch.setattr(vehicle, "getAccel", lambda _: 2.0)
    # Call monkeypatch.setattr with the supplied arguments.
    monkeypatch.setattr(vehicle, "getDecel", lambda _: 4.5)
    # Call monkeypatch.setattr with the supplied arguments.
    monkeypatch.setattr(vehicle, "getEmergencyDecel", lambda _: 7.0)
    # Call monkeypatch.setattr with the supplied arguments.
    monkeypatch.setattr(vehicle, "getMaxSpeed", lambda _: 13.89)
    # Call monkeypatch.setattr with the supplied arguments.
    monkeypatch.setattr(vehicle, "getLength", lambda _: 4.7)
    # Call monkeypatch.setattr with the supplied arguments.
    monkeypatch.setattr(vehicle, "getWidth", lambda _: 1.9)
    # Call monkeypatch.setattr with the supplied arguments.
    monkeypatch.setattr(vehicle, "getLaneID", lambda _: "w_in_0")
    # Call monkeypatch.setattr with the supplied arguments.
    monkeypatch.setattr(vehicle, "getLanePosition", lambda _: 10.0)
    # Call monkeypatch.setattr with the supplied arguments.
    monkeypatch.setattr(vehicle, "getRoadID", lambda _: "w_in")
    # Call monkeypatch.setattr with the supplied arguments.
    monkeypatch.setattr(vehicle, "getRouteID", lambda _: "route_w_left")
    # Call monkeypatch.setattr with the supplied arguments.
    monkeypatch.setattr(vehicle, "getRouteIndex", lambda _: 0)
    # Call monkeypatch.setattr with the supplied arguments.
    monkeypatch.setattr(vehicle, "getTypeID", lambda _: "AV")
    # Call monkeypatch.setattr with the supplied arguments.
    monkeypatch.setattr(lane, "getLength", lambda _: 100.0)

    # Set state to SUMOEnv().get_vehicles() at 'AV_1'.
    state = SUMOEnv().get_vehicles()["AV_1"]
    # Require state at 'position' equals a tuple containing 12.0, 34.0; otherwise raise AssertionError.
    assert state["position"] == (12.0, 34.0)
    # Require state at 'speed' equals 7.5; otherwise raise AssertionError.
    assert state["speed"] == 7.5
    # Require state at 'heading_radians' equals the result of pytest.approx(math.pi divided by 2.0); otherwise
    # raise AssertionError.
    assert state["heading_radians"] == pytest.approx(math.pi / 2.0)
    # Require state at 'length' equals 4.7; otherwise raise AssertionError.
    assert state["length"] == 4.7
    # Require state at 'width' equals 1.9; otherwise raise AssertionError.
    assert state["width"] == 1.9
    # Require state at 'max_acceleration_mps2' equals 2.0; otherwise raise AssertionError.
    assert state["max_acceleration_mps2"] == 2.0
    # Require state at 'comfortable_deceleration_mps2' equals 4.5; otherwise raise AssertionError.
    assert state["comfortable_deceleration_mps2"] == 4.5
    # Require state at 'emergency_deceleration_mps2' equals 7.0; otherwise raise AssertionError.
    assert state["emergency_deceleration_mps2"] == 7.0
    # Require state at 'max_speed_mps' equals 13.89; otherwise raise AssertionError.
    assert state["max_speed_mps"] == 13.89


# Check actual sumo dynamics reach each local track using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def test_actual_sumo_dynamics_reach_each_local_track():
    # Set manager to the result of ObservationManager().
    manager = ObservationManager()
    # Set (cx, cy) to get_intersection_geometry().center_xy.
    cx, cy = get_intersection_geometry().center_xy
    # Set states to a dictionary containing ego, target.
    states = {
        # Store the result of sumo_state(a tuple containing cx, cy minus 10.0) under 'ego'.
        "ego": sumo_state((cx, cy - 10.0)),
        # Store the result of sumo_state(a tuple containing cx, cy plus 10.0, the text 'route_n_right') under
        # 'target'.
        "target": sumo_state((cx, cy + 10.0), "route_n_right"),
    }
    # Update manager with the supplied entries.
    manager.update(states, 0.04)
    # Iterate over values from manager.get_ldm('ego').tracks, binding each item to track.
    for track in manager.get_ldm("ego").tracks.values():
        # Require track at 'max_acceleration_mps2' equals 2.0; otherwise raise AssertionError.
        assert track["max_acceleration_mps2"] == 2.0
        # Require track at 'comfortable_deceleration_mps2' equals 4.5; otherwise raise AssertionError.
        assert track["comfortable_deceleration_mps2"] == 4.5
        # Require track at 'emergency_deceleration_mps2' equals 7.0; otherwise raise AssertionError.
        assert track["emergency_deceleration_mps2"] == 7.0
        # Require track at 'max_speed_mps' equals 13.89; otherwise raise AssertionError.
        assert track["max_speed_mps"] == 13.89


# Check propagated dynamics match explicit av vtype using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_propagated_dynamics_match_explicit_av_vtype():
    # Set av_type to the result of ET.parse(PROJECT_ROOT / 'networks' / 'intersection.rou.xml').getroot().find(the
    # text "vType[@id='AV']").
    av_type = ET.parse(
        # Supply PROJECT_ROOT joined with the path segment 'networks' joined with the path segment 'intersection.rou.xml' to
        # ET.parse.
        PROJECT_ROOT / "networks" / "intersection.rou.xml"
    # Supply the text "vType[@id='AV']" to the enclosing expression.
    ).getroot().find("vType[@id='AV']")
    # Require av_type is a different object from None; otherwise raise AssertionError.
    assert av_type is not None
    # Require a floating-point number built from av_type.attrib at 'accel' equals 2.0; otherwise raise
    # AssertionError.
    assert float(av_type.attrib["accel"]) == 2.0
    # Require a floating-point number built from av_type.attrib at 'decel' equals 4.5; otherwise raise
    # AssertionError.
    assert float(av_type.attrib["decel"]) == 4.5
    # Require a floating-point number built from av_type.attrib at 'emergencyDecel' equals 7.0; otherwise raise
    # AssertionError.
    assert float(av_type.attrib["emergencyDecel"]) == 7.0
    # Require a floating-point number built from av_type.attrib at 'maxSpeed' equals 13.89; otherwise raise
    # AssertionError.
    assert float(av_type.attrib["maxSpeed"]) == 13.89


# Check environment start and first observation update have no contract error using the setup, calls, and
# assertions below.
# Input monkeypatch: the supplied monkeypatch.
# Output: no explicit value; normal completion returns None.
# Processing: handle the specified errors.
def test_environment_start_and_first_observation_update_have_no_contract_error(
        # Declare monkeypatch as input parameter.
        monkeypatch):
    # Call monkeypatch.setattr with the supplied arguments.
    monkeypatch.setattr(environment.shutil, "which", lambda _: "sumo")
    # Call monkeypatch.setattr with the supplied arguments.
    monkeypatch.setattr(environment.traci, "start", lambda command: None)
    # Call monkeypatch.setattr with the supplied arguments.
    monkeypatch.setattr(
        # Supply environment.traci.simulation to monkeypatch.setattr.
        environment.traci.simulation, "getTime", lambda: 0.0
    )
    # Set env to the result of SUMOEnv().
    env = SUMOEnv(use_gui=False)
    # Call env.start with the supplied arguments.
    env.start()

    # Set manager to the result of ObservationManager().
    manager = ObservationManager()
    # Set (cx, cy) to get_intersection_geometry().center_xy.
    cx, cy = get_intersection_geometry().center_xy
    # Attempt the enclosed operations and route matching exceptions to the handlers below.
    try:
        # Update manager with the supplied entries.
        manager.update({"ego": sumo_state((cx, cy - 10.0))}, 0.0)
    # Handle (KeyError, ValueError) as error using the recovery steps below.
    except (KeyError, ValueError) as error:
        # Call pytest.fail with the supplied arguments.
        pytest.fail(f"canonical environment/perception contract failed: {error}")
