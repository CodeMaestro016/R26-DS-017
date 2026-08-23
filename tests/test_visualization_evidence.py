"""Focused tests for the passive visualization and evidence layer."""

import json
import math

import numpy as np
import pytest

from debug_evidence import EvidenceJsonlWriter, build_evidence_snapshot
from observation import LocalDynamicMap, ObservationManager
from sumo_debug_overlay import sensor_circle_points


def state(x=0.0, route="secret_route"):
    return {
        "position": (x, 0.0), "speed": 5.0, "heading_radians": 0.0,
        "length": 4.5, "width": 1.8, "lane_id": "w_in_0",
        "lane_position": 10.0, "lane_length": 100.0, "road_id": "w_in",
        "route_id": route, "route_index": 7,
    }


def local(object_id, source):
    item = dict(source)
    item.update({
        "object_id": object_id, "observation_type": "OBJECT_DETECTION",
        "range": 12.0, "bearing_radians": 0.1,
        "relative_position_ego": (12.0, 0.0),
        "relative_velocity_ego": (0.0, 0.0),
        "measurement_timestamp": 1.0, "available_timestamp": 1.0,
        "detection_status": "DETECTED",
    })
    return item


def manager_with_fake_perception():
    manager = ObservationManager()
    manager.is_in_approach_zone = lambda _position: True
    manager.perception_interface.generate_observations = (
        lambda ego, _ego, all_data, _time: {
            ego: local(ego, all_data[ego])
        }
    )
    return manager


def test_latest_local_observations_are_independent_and_defensive():
    manager = manager_with_fake_perception()
    manager.update({"AV_0": state(0), "AV_1": state(1)}, 1.0)
    first = manager.get_last_local_observations("AV_0")
    second = manager.get_last_local_observations("AV_1")
    assert set(first) == {"AV_0"}
    assert set(second) == {"AV_1"}
    first["AV_0"]["position"] = (999, 999)
    assert manager.get_last_local_observations("AV_0")["AV_0"]["position"] != (999, 999)


def test_departure_outside_zone_and_reset_clear_retained_data():
    manager = manager_with_fake_perception()
    manager.update({"AV_0": state()}, 1.0)
    manager.update({}, 1.04)
    assert manager.get_last_local_observations() == {}
    manager.update({"AV_0": state()}, 1.08)
    manager.is_in_approach_zone = lambda _position: False
    manager.update({"AV_0": state()}, 1.12)
    assert manager.get_last_local_observations("AV_0") == {}
    manager.reset()
    assert manager.get_last_local_observations() == {}


def test_snapshot_is_json_serializable_and_route_truth_does_not_leak():
    manager = manager_with_fake_perception()
    observations = {"AV_0": state()}
    manager.update(observations, np.float64(1.0))
    snapshot = build_evidence_snapshot(1.0, observations, manager, "profile", 160)
    encoded = json.dumps(snapshot, allow_nan=False)
    assert "secret_route" not in encoded
    assert "route_id" not in encoded
    assert "route_index" not in encoded


def test_jsonl_writer_writes_one_valid_object_per_line(tmp_path):
    path = tmp_path / "evidence.jsonl"
    with EvidenceJsonlWriter(path) as writer:
        writer.write({"step": 1, "value": np.float64(2.0)})
        writer.write({"step": 2})
    lines = path.read_text(encoding="utf-8").splitlines()
    assert [json.loads(line)["step"] for line in lines] == [1, 2]


def test_propagated_track_is_marked_unobserved():
    ldm = LocalDynamicMap("AV_0")
    ldm.add_or_update_track("AV_1", (0, 0), 2, math.pi / 2, "lane", 0,
                            100, "road", 1.0)
    ldm.propagate_track("AV_1", 1.5)
    assert ldm.tracks["AV_1"]["is_observed"] is False


def test_sensor_circle_uses_exact_configured_radius():
    center, radius = (3.0, -4.0), 137.5
    points = sensor_circle_points(center, radius, 32)
    assert points[0] == points[-1]
    for point in points[:-1]:
        assert math.dist(center, point) == pytest.approx(radius)


def test_snapshot_builder_does_not_modify_decision_state():
    manager = manager_with_fake_perception()
    observations = {"AV_0": state()}
    manager.update(observations, 1.0)
    ldm = manager.get_ldm("AV_0")
    ldm.current_negotiation_problem = {"decision": "unchanged"}
    before = ldm.current_negotiation_problem.copy()
    build_evidence_snapshot(1.0, observations, manager)
    assert ldm.current_negotiation_problem == before
