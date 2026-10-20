"""Focused tests for the passive visualization and evidence layer."""

# Import json for use in this module.
import json
# Import math for use in this module.
import math

# Import numpy as np for use in this module.
import numpy as np
# Import pytest for use in this module.
import pytest

# Import EvidenceJsonlWriter, build_evidence_snapshot from debug_evidence for the operations below.
from debug_evidence import EvidenceJsonlWriter, build_evidence_snapshot
# Import LocalDynamicMap, ObservationManager from observation for the operations below.
from observation import LocalDynamicMap, ObservationManager
# Import sensor_circle_points from sumo_debug_overlay for the operations below.
from sumo_debug_overlay import sensor_circle_points


# State using the inputs and processing steps below.
# Input x: the supplied x.
# Input route: the supplied route.
# Output: a dictionary containing position, speed, heading_radians, length, width, lane_id, lane_position,
# lane_length,...
def state(x=0.0, route="secret_route"):
    # Return a dictionary containing position, speed, heading_radians, length, width, lane_id, lane_position,
    # lane_length,... to the caller.
    return {
        # Store a tuple containing x, 0.0 under 'position'.
        # Store 5.0 under 'speed'.
        # Store 0.0 under 'heading_radians'.
        "position": (x, 0.0), "speed": 5.0, "heading_radians": 0.0,
        # Store 4.5 under 'length'.
        # Store 1.8 under 'width'.
        # Store the text 'w_in_0' under 'lane_id'.
        "length": 4.5, "width": 1.8, "lane_id": "w_in_0",
        # Store 10.0 under 'lane_position'.
        # Store 100.0 under 'lane_length'.
        # Store the text 'w_in' under 'road_id'.
        "lane_position": 10.0, "lane_length": 100.0, "road_id": "w_in",
        # Store route under 'route_id'.
        # Store 7 under 'route_index'.
        "route_id": route, "route_index": 7,
    }


# Local using the inputs and processing steps below.
# Input object_id: the supplied object id.
# Input source: the supplied source.
# Output: item.
def local(object_id, source):
    # Set item to a dictionary built from source.
    item = dict(source)
    # Update item with the supplied entries.
    item.update({
        # Store object_id under 'object_id'.
        # Store the text 'OBJECT_DETECTION' under 'observation_type'.
        "object_id": object_id, "observation_type": "OBJECT_DETECTION",
        # Store 12.0 under 'range'.
        # Store 0.1 under 'bearing_radians'.
        "range": 12.0, "bearing_radians": 0.1,
        # Store a tuple containing 12.0, 0.0 under 'relative_position_ego'.
        "relative_position_ego": (12.0, 0.0),
        # Store a tuple containing 0.0, 0.0 under 'relative_velocity_ego'.
        "relative_velocity_ego": (0.0, 0.0),
        # Store 1.0 under 'measurement_timestamp'.
        # Store 1.0 under 'available_timestamp'.
        "measurement_timestamp": 1.0, "available_timestamp": 1.0,
        "detection_status": "DETECTED",
    })
    # Return item to the caller.
    return item


# Manager with fake perception using the inputs and processing steps below.
# Output: manager.
def manager_with_fake_perception():
    # Set manager to the result of ObservationManager().
    manager = ObservationManager()
    # Set manager.is_in_approach_zone to a callback that returns True.
    manager.is_in_approach_zone = lambda _position: True
    # Set manager.perception_interface.generate_observations to a callback that returns a dictionary of the
    # supplied entries.
    manager.perception_interface.generate_observations = (
        # Declare ego, _ego, all_data, _time as input parameters.
        lambda ego, _ego, all_data, _time: {
            # Store the result of local(ego, all_data at ego) under ego.
            ego: local(ego, all_data[ego])
        }
    )
    # Return manager to the caller.
    return manager


# Check latest local observations are independent and defensive using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_latest_local_observations_are_independent_and_defensive():
    # Set manager to the result of manager_with_fake_perception().
    manager = manager_with_fake_perception()
    # Update manager with the supplied entries.
    manager.update({"AV_0": state(0), "AV_1": state(1)}, 1.0)
    # Set first to the result of manager.get_last_local_observations(the text 'AV_0').
    first = manager.get_last_local_observations("AV_0")
    # Set second to the result of manager.get_last_local_observations(the text 'AV_1').
    second = manager.get_last_local_observations("AV_1")
    # Require a set built from first equals a set containing the text 'AV_0'; otherwise raise AssertionError.
    assert set(first) == {"AV_0"}
    # Require a set built from second equals a set containing the text 'AV_1'; otherwise raise AssertionError.
    assert set(second) == {"AV_1"}
    # Set first['AV_0']['position'] to a tuple containing 999, 999.
    first["AV_0"]["position"] = (999, 999)
    # Require manager.get_last_local_observations('AV_0')['AV_0'] at 'position' differs from a tuple containing
    # 999, 999; otherwise raise AssertionError.
    assert manager.get_last_local_observations("AV_0")["AV_0"]["position"] != (999, 999)


# Check departure outside zone and reset clear retained data using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_departure_outside_zone_and_reset_clear_retained_data():
    # Set manager to the result of manager_with_fake_perception().
    manager = manager_with_fake_perception()
    # Update manager with the supplied entries.
    manager.update({"AV_0": state()}, 1.0)
    # Update manager with the supplied entries.
    manager.update({}, 1.04)
    # Require the result of manager.get_last_local_observations() equals an empty dictionary; otherwise raise
    # AssertionError.
    assert manager.get_last_local_observations() == {}
    # Update manager with the supplied entries.
    manager.update({"AV_0": state()}, 1.08)
    # Set manager.is_in_approach_zone to a callback that returns False.
    manager.is_in_approach_zone = lambda _position: False
    # Update manager with the supplied entries.
    manager.update({"AV_0": state()}, 1.12)
    # Require the result of manager.get_last_local_observations(the text 'AV_0') equals an empty dictionary;
    # otherwise raise AssertionError.
    assert manager.get_last_local_observations("AV_0") == {}
    # Call manager.reset with the supplied arguments.
    manager.reset()
    # Require the result of manager.get_last_local_observations() equals an empty dictionary; otherwise raise
    # AssertionError.
    assert manager.get_last_local_observations() == {}


# Check snapshot is json serializable and route truth does not leak using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_snapshot_is_json_serializable_and_route_truth_does_not_leak():
    # Set manager to the result of manager_with_fake_perception().
    manager = manager_with_fake_perception()
    # Set observations to a dictionary containing AV_0.
    observations = {"AV_0": state()}
    # Update manager with the supplied entries.
    manager.update(observations, np.float64(1.0))
    # Set snapshot to the result of build_evidence_snapshot(1.0, observations, manager, the text 'profile', 160).
    snapshot = build_evidence_snapshot(1.0, observations, manager, "profile", 160)
    # Set encoded to the serialized data produced by json.dumps.
    encoded = json.dumps(snapshot, allow_nan=False)
    # Require the text 'secret_route' does not belong to encoded; otherwise raise AssertionError.
    assert "secret_route" not in encoded
    # Require the text 'route_id' does not belong to encoded; otherwise raise AssertionError.
    assert "route_id" not in encoded
    # Require the text 'route_index' does not belong to encoded; otherwise raise AssertionError.
    assert "route_index" not in encoded


# Check jsonl writer writes one valid object per line using the setup, calls, and assertions below.
# Input tmp_path: the supplied tmp path.
# Output: no explicit value; normal completion returns None.
def test_jsonl_writer_writes_one_valid_object_per_line(tmp_path):
    # Set path to tmp_path joined with the path segment 'evidence.jsonl'.
    path = tmp_path / "evidence.jsonl"
    # Enter the result of EvidenceJsonlWriter(path) as writer and run the enclosed operations within that context.
    with EvidenceJsonlWriter(path) as writer:
        # Call writer.write with the supplied arguments.
        writer.write({"step": 1, "value": np.float64(2.0)})
        # Call writer.write with the supplied arguments.
        writer.write({"step": 2})
    # Set lines to the result of path.read_text(encoding='utf-8').splitlines().
    lines = path.read_text(encoding="utf-8").splitlines()
    # Require a list of json.loads(line) at 'step' for line in lines equals a list containing 1, 2; otherwise
    # raise AssertionError.
    assert [json.loads(line)["step"] for line in lines] == [1, 2]


# Check propagated track is marked unobserved using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_propagated_track_is_marked_unobserved():
    # Set ldm to the result of LocalDynamicMap(the text 'AV_0').
    ldm = LocalDynamicMap("AV_0")
    # Call ldm.add_or_update_track with the supplied arguments.
    ldm.add_or_update_track("AV_1", (0, 0), 2, math.pi / 2, "lane", 0,
                            # Supply 100 to the enclosing expression.
                            100, "road", 1.0)
    # Call ldm.propagate_track with the supplied arguments.
    ldm.propagate_track("AV_1", 1.5)
    # Require ldm.tracks['AV_1'] at 'is_observed' is the same object as False; otherwise raise AssertionError.
    assert ldm.tracks["AV_1"]["is_observed"] is False


# Check sensor circle uses exact configured radius using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def test_sensor_circle_uses_exact_configured_radius():
    # Set (center, radius) to a tuple containing a tuple containing 3.0, the negative of 4.0, 137.5.
    center, radius = (3.0, -4.0), 137.5
    # Set points to the result of sensor_circle_points(center, radius, 32).
    points = sensor_circle_points(center, radius, 32)
    # Require points at 0 equals points at -1; otherwise raise AssertionError.
    assert points[0] == points[-1]
    # Iterate over points sliced by :-1, binding each item to point.
    for point in points[:-1]:
        # Require the result of math.dist(center, point) equals the result of pytest.approx(radius); otherwise
        # raise AssertionError.
        assert math.dist(center, point) == pytest.approx(radius)


# Check snapshot builder does not modify decision state using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_snapshot_builder_does_not_modify_decision_state():
    # Set manager to the result of manager_with_fake_perception().
    manager = manager_with_fake_perception()
    # Set observations to a dictionary containing AV_0.
    observations = {"AV_0": state()}
    # Update manager with the supplied entries.
    manager.update(observations, 1.0)
    # Set ldm to the result of manager.get_ldm(the text 'AV_0').
    ldm = manager.get_ldm("AV_0")
    # Set ldm.current_negotiation_problem to a dictionary containing decision.
    ldm.current_negotiation_problem = {"decision": "unchanged"}
    # Set before to the result of ldm.current_negotiation_problem.copy().
    before = ldm.current_negotiation_problem.copy()
    # Call build_evidence_snapshot with the supplied arguments.
    build_evidence_snapshot(1.0, observations, manager)
    # Require ldm.current_negotiation_problem equals before; otherwise raise AssertionError.
    assert ldm.current_negotiation_problem == before
