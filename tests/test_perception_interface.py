"""Deterministic contract tests for the geometric perception interface."""

import copy
import math
import sys
from pathlib import Path

import numpy as np
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from config import APPROACH_ZONE_RADIUS, SENSOR_RANGE
from perception_interface import PerceptionInterface


def vehicle(position, heading=0.0, speed=0.0, length=4.0, width=2.0, **extra):
    state = {
        "position": position, "heading_radians": heading, "speed": speed,
        "length": length, "width": width, "lane_id": "lane", "lane_position": 1.0,
        "lane_length": 100.0, "road_id": "road",
    }
    state.update(extra)
    return state


def observe(target, ego=None, **interface_options):
    ego = ego or vehicle((0.0, 0.0))
    states = {"ego": ego, "target": target}
    return PerceptionInterface(**interface_options).generate_observations(
        "ego", ego, states, 1.25
    )


@pytest.mark.parametrize(
    ("heading", "target_position", "expected"),
    [
        (0.0, (2.0, 10.0), (10.0, -2.0)),
        (math.pi / 2, (10.0, 2.0), (10.0, 2.0)),
        (math.pi, (-2.0, -10.0), (10.0, -2.0)),
        (3 * math.pi / 2, (-10.0, -2.0), (10.0, 2.0)),
    ],
)
def test_cardinal_coordinate_transformations(heading, target_position, expected):
    result = observe(vehicle(target_position), ego=vehicle((0.0, 0.0), heading=heading))
    assert result["target"]["relative_position_ego"] == pytest.approx(expected)


def test_positive_lateral_is_left():
    result = observe(vehicle((-3.0, 10.0)))
    assert result["target"]["relative_position_ego"][1] > 0.0


def test_relative_velocity_uses_ego_coordinates():
    result = observe(vehicle((0.0, 10.0), heading=math.pi / 2, speed=8.0),
                     ego=vehicle((0.0, 0.0), speed=3.0))
    assert result["target"]["relative_velocity_ego"] == pytest.approx((-3.0, -8.0))


def test_inside_outside_and_exact_range_boundary():
    assert "target" in observe(vehicle((0.0, SENSOR_RANGE - 0.01)))
    assert "target" in observe(vehicle((0.0, SENSOR_RANGE)))
    assert "target" not in observe(vehicle((0.0, SENSOR_RANGE + 0.01)))


def test_360_degree_fov_includes_object_behind():
    assert "target" in observe(vehicle((0.0, -10.0)), sensor_fov_degrees=360.0)


def test_narrow_fov_inside_and_outside():
    assert "target" in observe(vehicle((1.0, 10.0)), sensor_fov_degrees=30.0)
    assert "target" not in observe(vehicle((10.0, 1.0)), sensor_fov_degrees=30.0)


def test_angle_wrapping_near_minus_pi_and_plus_pi():
    interface = PerceptionInterface(sensor_fov_degrees=20.0)
    assert interface._is_inside_fov(math.pi - 0.01) is False
    assert interface._is_inside_fov(-math.pi + 0.01) is False
    behind = observe(vehicle((-0.01, -10.0)), sensor_fov_degrees=360.0)
    assert "target" in behind


def test_no_occlusion_at_different_bearings():
    ego = vehicle((0.0, 0.0))
    states = {"ego": ego, "a": vehicle((-8.0, 15.0)), "b": vehicle((8.0, 30.0))}
    result = PerceptionInterface().generate_observations("ego", ego, states, 0.0)
    assert set(result) == {"ego", "a", "b"}
    assert result["b"]["visible_fraction"] == pytest.approx(1.0)


def test_full_occlusion_directly_behind():
    ego = vehicle((0.0, 0.0))
    states = {"ego": ego, "near": vehicle((0.0, 10.0), width=3.0),
              "far": vehicle((0.0, 20.0), width=2.0)}
    result = PerceptionInterface().generate_observations("ego", ego, states, 0.0)
    assert "near" in result and "far" not in result


def test_partial_occlusion_is_retained():
    ego = vehicle((0.0, 0.0))
    states = {"ego": ego, "near": vehicle((0.0, 10.0), width=2.0),
              "far": vehicle((-1.5, 20.0), width=4.0)}
    result = PerceptionInterface().generate_observations("ego", ego, states, 0.0)
    assert 0.0 < result["far"]["visible_fraction"] < 1.0


def test_vehicle_dimensions_affect_occlusion():
    ego = vehicle((0.0, 0.0))
    def frame(near_width):
        states = {"ego": ego, "near": vehicle((0.0, 10.0), width=near_width),
                  "far": vehicle((-1.5, 20.0), width=2.0)}
        return PerceptionInterface().generate_observations("ego", ego, states, 0.0)
    assert "far" in frame(1.0)
    assert "far" not in frame(6.0)


def test_each_ego_receives_a_different_local_set():
    states = {"a": vehicle((0.0, 0.0)), "b": vehicle((0.0, 100.0)),
              "c": vehicle((0.0, 150.0))}
    interface = PerceptionInterface(sensor_range=60.0, profile="IDEAL_BASELINE")
    view_a = interface.generate_observations("a", states["a"], states, 0.0)
    view_b = interface.generate_observations("b", states["b"], states, 0.0)
    assert set(view_a) == {"a"}
    assert set(view_b) == {"b", "c"}


def test_ego_label_schema_and_no_route_leakage():
    target = vehicle((0.0, 10.0), route_id="route_n_left",
                     ground_truth_route_id="route_n_left", intended_manoeuvre="LEFT")
    result = observe(target)
    assert result["ego"]["observation_type"] == "EGO_LOCALIZATION"
    assert result["ego"]["detection_status"] == "SELF_LOCALIZATION"
    forbidden = {"route_id", "ground_truth_route_id", "intended_manoeuvre"}
    assert forbidden.isdisjoint(result["target"])


def test_invalid_ego_raises_and_invalid_target_is_diagnostic():
    invalid_ego = vehicle((math.nan, 0.0))
    with pytest.raises(ValueError, match="position"):
        PerceptionInterface().generate_observations(
            "ego", invalid_ego, {"ego": invalid_ego}, 0.0
        )
    ego = vehicle((0.0, 0.0))
    interface = PerceptionInterface()
    result = interface.generate_observations(
        "ego", ego, {"ego": ego, "bad": vehicle((1.0, 1.0), width=-1.0)}, 0.0
    )
    assert set(result) == {"ego"}
    assert interface.last_diagnostics[0]["reason"] == "INVALID_TARGET_STATE"


def test_inputs_are_not_mutated_and_results_are_deterministic():
    ego, target = vehicle((0.0, 0.0)), vehicle((2.0, 20.0))
    states = {"ego": ego, "target": target}
    original = copy.deepcopy(states)
    interface = PerceptionInterface()
    first = interface.generate_observations("ego", ego, states, 2.0)
    second = interface.generate_observations("ego", ego, states, 2.0)
    assert states == original
    assert first == second


def test_profiles_differ_when_occlusion_exists():
    ego = vehicle((0.0, 0.0))
    states = {"ego": ego, "near": vehicle((0.0, 10.0), width=3.0),
              "far": vehicle((0.0, 20.0), width=2.0)}
    geometric = PerceptionInterface().generate_observations("ego", ego, states, 0.0)
    ideal = PerceptionInterface(profile="IDEAL_BASELINE").generate_observations(
        "ego", ego, states, 0.0
    )
    assert "far" not in geometric and "far" in ideal
    assert ideal["far"]["perception_profile"] == "IDEAL_BASELINE"


def test_configured_radii_derivations():
    assert APPROACH_ZONE_RADIUS == pytest.approx(76.67)
    assert SENSOR_RANGE == pytest.approx(118.34)
