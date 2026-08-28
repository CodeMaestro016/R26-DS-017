"""Integration tests for SUMO state collection, perception, and the LDM."""

import math
import xml.etree.ElementTree as ET

import pytest

import environment
from config import PROJECT_ROOT
from environment import SUMOEnv
from observation import ObservationManager
from map_geometry import get_intersection_geometry


def sumo_state(position, route_id="route_w_left"):
    return {
        "position": position,
        "speed": 5.0,
        "heading_radians": 0.0,
        "length": 4.5,
        "width": 1.8,
        "pos": position,
        "vel": 5.0,
        "angle_degrees": 0.0,
        "lane_id": "w_in_0",
        "lane_position": 20.0,
        "lane_length": 100.0,
        "road_id": "w_in",
        "route_id": route_id,
        "route_index": 0,
        "max_acceleration_mps2": 2.0,
        "comfortable_deceleration_mps2": 4.5,
        "emergency_deceleration_mps2": 7.0,
        "max_speed_mps": 13.89,
    }


def test_geometric_sensor_dimensions_and_detections_reach_ldm():
    manager = ObservationManager()
    cx, cy = get_intersection_geometry().center_xy
    states = {
        "ego": sumo_state((cx, cy - 10.0)),
        "target": sumo_state((cx, cy + 10.0), "route_n_right"),
    }
    manager.update(states, 0.04)

    ego_ldm = manager.get_ldm("ego")
    assert set(ego_ldm.tracks) == {"ego", "target"}
    assert manager.perception_interface.profile == "GEOMETRIC_SENSOR"
    detection = manager.perception_interface.generate_observations(
        "ego",
        {key: states["ego"][key] for key in (
            "position", "speed", "heading_radians", "length", "width",
            "lane_id", "lane_position", "lane_length", "road_id",
        )},
        {
            vehicle_id: {key: state[key] for key in (
                "position", "speed", "heading_radians", "length", "width",
                "lane_id", "lane_position", "lane_length", "road_id",
            )}
            for vehicle_id, state in states.items()
        },
        0.04,
    )["target"]
    assert detection["length"] == 4.5
    assert detection["width"] == 1.8


def test_route_truth_does_not_enter_perception_or_ldm_tracks():
    manager = ObservationManager()
    cx, cy = get_intersection_geometry().center_xy
    states = {
        "ego": sumo_state((cx, cy - 10.0)),
        "target": sumo_state((cx, cy + 10.0), "route_n_right"),
    }
    manager.update(states, 0.04)
    forbidden = {"route_id", "ground_truth_route_id", "route_index"}
    for ldm in manager.ldms.values():
        assert not hasattr(ldm, "evaluation_route_truth")
        for track in ldm.tracks.values():
            assert forbidden.isdisjoint(track)


def test_departure_and_reset_clear_perception_diagnostics():
    manager = ObservationManager()
    cx, cy = get_intersection_geometry().center_xy
    states = {
        "ego": sumo_state((cx, cy - 10.0)),
        "target": sumo_state((cx, cy + 10.0)),
    }
    manager.update(states, 0.04)
    assert set(manager.perception_interface.get_last_diagnostics()) == {
        "ego", "target"
    }

    manager.update({"ego": states["ego"]}, 0.08)
    assert "target" not in manager.perception_interface.get_last_diagnostics()
    manager.reset()
    assert manager.perception_interface.get_last_diagnostics() == {}
    assert manager.perception_interface.get_last_summary() == {}


def test_environment_collects_canonical_perception_fields(monkeypatch):
    vehicle = environment.traci.vehicle
    lane = environment.traci.lane
    monkeypatch.setattr(vehicle, "getIDList", lambda: ("AV_1",))
    monkeypatch.setattr(vehicle, "getAngle", lambda _: 90.0)
    monkeypatch.setattr(vehicle, "getPosition", lambda _: (12.0, 34.0))
    monkeypatch.setattr(vehicle, "getSpeed", lambda _: 7.5)
    monkeypatch.setattr(vehicle, "getAcceleration", lambda _: 0.2)
    monkeypatch.setattr(vehicle, "getAccel", lambda _: 2.0)
    monkeypatch.setattr(vehicle, "getDecel", lambda _: 4.5)
    monkeypatch.setattr(vehicle, "getEmergencyDecel", lambda _: 7.0)
    monkeypatch.setattr(vehicle, "getMaxSpeed", lambda _: 13.89)
    monkeypatch.setattr(vehicle, "getLength", lambda _: 4.7)
    monkeypatch.setattr(vehicle, "getWidth", lambda _: 1.9)
    monkeypatch.setattr(vehicle, "getLaneID", lambda _: "w_in_0")
    monkeypatch.setattr(vehicle, "getLanePosition", lambda _: 10.0)
    monkeypatch.setattr(vehicle, "getRoadID", lambda _: "w_in")
    monkeypatch.setattr(vehicle, "getRouteID", lambda _: "route_w_left")
    monkeypatch.setattr(vehicle, "getRouteIndex", lambda _: 0)
    monkeypatch.setattr(vehicle, "getTypeID", lambda _: "AV")
    monkeypatch.setattr(lane, "getLength", lambda _: 100.0)

    state = SUMOEnv().get_vehicles()["AV_1"]
    assert state["position"] == (12.0, 34.0)
    assert state["speed"] == 7.5
    assert state["heading_radians"] == pytest.approx(math.pi / 2.0)
    assert state["length"] == 4.7
    assert state["width"] == 1.9
    assert state["max_acceleration_mps2"] == 2.0
    assert state["comfortable_deceleration_mps2"] == 4.5
    assert state["emergency_deceleration_mps2"] == 7.0
    assert state["max_speed_mps"] == 13.89


def test_actual_sumo_dynamics_reach_each_local_track():
    manager = ObservationManager()
    cx, cy = get_intersection_geometry().center_xy
    states = {
        "ego": sumo_state((cx, cy - 10.0)),
        "target": sumo_state((cx, cy + 10.0), "route_n_right"),
    }
    manager.update(states, 0.04)
    for track in manager.get_ldm("ego").tracks.values():
        assert track["max_acceleration_mps2"] == 2.0
        assert track["comfortable_deceleration_mps2"] == 4.5
        assert track["emergency_deceleration_mps2"] == 7.0
        assert track["max_speed_mps"] == 13.89


def test_propagated_dynamics_match_explicit_av_vtype():
    av_type = ET.parse(
        PROJECT_ROOT / "networks" / "intersection.rou.xml"
    ).getroot().find("vType[@id='AV']")
    assert av_type is not None
    assert float(av_type.attrib["accel"]) == 2.0
    assert float(av_type.attrib["decel"]) == 4.5
    assert float(av_type.attrib["emergencyDecel"]) == 7.0
    assert float(av_type.attrib["maxSpeed"]) == 13.89


def test_environment_start_and_first_observation_update_have_no_contract_error(
        monkeypatch):
    monkeypatch.setattr(environment.shutil, "which", lambda _: "sumo")
    monkeypatch.setattr(environment.traci, "start", lambda command: None)
    monkeypatch.setattr(
        environment.traci.simulation, "getTime", lambda: 0.0
    )
    env = SUMOEnv(use_gui=False)
    env.start()

    manager = ObservationManager()
    cx, cy = get_intersection_geometry().center_xy
    try:
        manager.update({"ego": sumo_state((cx, cy - 10.0))}, 0.0)
    except (KeyError, ValueError) as error:
        pytest.fail(f"canonical environment/perception contract failed: {error}")
