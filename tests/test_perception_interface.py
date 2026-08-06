"""Deterministic contract tests for the geometric perception interface."""

import copy
import math
import sys
from pathlib import Path

import numpy as np
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from config import (
    APPROACH_ZONE_RADIUS,
    DEFAULT_PERCEPTION_PROFILE,
    PERCEPTION_PROFILES,
    SENSOR_RANGE,
)
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


def diagnostic_by_target(interface, ego_id="ego"):
    return {
        item["target_id"]: item
        for item in interface.get_last_diagnostics(ego_id)
    }


def test_bbox_edge_inside_fov_when_center_is_outside():
    target = vehicle((-4.25, 20.0), width=4.0)
    interface = PerceptionInterface(sensor_fov_degrees=20.0)
    result = interface.generate_observations(
        "ego", vehicle((0.0, 0.0)),
        {"ego": vehicle((0.0, 0.0)), "target": target}, 0.0
    )
    assert "target" in result
    assert 0.0 < result["target"]["fov_visible_fraction"] < 1.0


def test_center_inside_fov_with_bbox_edge_outside_is_partial():
    target = vehicle((-2.8, 20.0), width=5.0)
    result = observe(target, sensor_fov_degrees=20.0)
    assert "target" in result
    assert 0.0 < result["target"]["fov_visible_fraction"] < 1.0
    assert 0.0 < result["target"]["visible_fraction"] < 1.0


def test_wrapped_object_interval_intersects_360_fov():
    result = observe(
        vehicle((0.0, -15.0), width=4.0), sensor_fov_degrees=360.0
    )
    assert result["target"]["fov_visible_fraction"] == pytest.approx(1.0)


def test_ideal_profile_skips_geometry_and_accepts_missing_dimensions(monkeypatch):
    ego = vehicle((0.0, 0.0))
    target = {"position": (0.0, 10.0), "speed": 1.0,
              "heading_radians": 0.0}
    interface = PerceptionInterface(profile="IDEAL_BASELINE",
                                    sensor_fov_degrees=1.0)
    monkeypatch.setattr(
        interface, "_calculate_bounding_box",
        lambda *_: pytest.fail("ideal baseline calculated bounding-box geometry")
    )
    result = interface.generate_observations(
        "ego", ego, {"ego": ego, "target": target}, 0.0
    )
    assert "target" in result
    assert "length" not in result["target"]
    assert "width" not in result["target"]
    assert result["target"]["visible_fraction"] == 1.0


def test_geometric_profile_requires_dimensions_and_logs_invalid_target():
    ego = vehicle((0.0, 0.0))
    target = {"position": (0.0, 10.0), "speed": 1.0,
              "heading_radians": 0.0}
    interface = PerceptionInterface()
    result = interface.generate_observations(
        "ego", ego, {"ego": ego, "target": target}, 0.0
    )
    assert "target" not in result
    item = diagnostic_by_target(interface)["target"]
    assert item["result"] == "REJECTED"
    assert item["reason"] == "INVALID_TARGET_STATE"


def test_diagnostics_cover_range_fov_detection_occlusion_and_partial():
    ego = vehicle((0.0, 0.0))
    states = {
        "ego": ego,
        "visible": vehicle((-10.0, 30.0)),
        "out_range": vehicle((0.0, SENSOR_RANGE + 1.0)),
        "out_fov": vehicle((30.0, 0.0)),
        "near": vehicle((0.0, 10.0), width=3.0),
        "hidden": vehicle((0.0, 25.0), width=2.0),
        "partial": vehicle((-2.5, 25.0), width=4.0),
        "bad": vehicle((1.0, 1.0), width=-1.0),
    }
    interface = PerceptionInterface(sensor_fov_degrees=60.0)
    result = interface.generate_observations("ego", ego, states, 3.0)
    details = diagnostic_by_target(interface)
    repeated = interface.generate_observations("ego", ego, states, 3.0)
    assert repeated == result
    assert len(interface.get_last_diagnostics("ego")) == len(states) - 1
    assert set(details) == set(states) - {"ego"}
    assert details["visible"]["reason"] == "DETECTED"
    assert details["out_range"]["reason"] == "OUT_OF_RANGE"
    assert details["out_fov"]["reason"] == "OUT_OF_FOV"
    assert details["hidden"]["reason"] == "FULLY_OCCLUDED"
    assert details["partial"]["reason"] == "PARTIALLY_VISIBLE"
    assert details["partial"]["result"] == "DETECTED"
    assert details["bad"]["reason"] == "INVALID_TARGET_STATE"
    assert "hidden" not in result and "partial" in result
    assert all("route_id" not in detection for detection in result.values())

    summary = interface.get_last_summary("ego")
    assert summary["candidate_targets"] == len(states) - 1
    assert summary["detected_targets"] == sum(
        item["result"] == "DETECTED" for item in details.values()
    )
    for key, reason in {
        "invalid_targets": "INVALID_TARGET_STATE",
        "out_of_range_targets": "OUT_OF_RANGE",
        "out_of_fov_targets": "OUT_OF_FOV",
        "fully_occluded_targets": "FULLY_OCCLUDED",
        "partially_visible_targets": "PARTIALLY_VISIBLE",
    }.items():
        assert summary[key] == sum(
            item["reason"] == reason for item in details.values()
        )


def test_per_ego_diagnostics_are_independent_and_accessors_return_copies():
    states = {
        "a": vehicle((0.0, 0.0)),
        "b": vehicle((0.0, 20.0)),
        "c": vehicle((0.0, 200.0)),
    }
    interface = PerceptionInterface(profile="IDEAL_BASELINE")
    interface.generate_observations("a", states["a"], states, 1.0)
    a_before = interface.get_last_diagnostics("a")
    interface.generate_observations("b", states["b"], states, 2.0)
    assert interface.get_last_diagnostics("a") == a_before
    assert interface.get_last_diagnostics("b") != a_before

    returned = interface.get_last_diagnostics()
    returned["a"][0]["reason"] = "MUTATED"
    assert interface.get_last_diagnostics("a")[0]["reason"] != "MUTATED"
    summary = interface.get_last_summary("a")
    summary["detected_targets"] = 999
    assert interface.get_last_summary("a")["detected_targets"] != 999


def test_multiple_overlapping_occluders_do_not_double_count():
    intervals = [(-0.2, 0.2)]
    covered = [(-0.2, 0.05), (-0.05, 0.1)]
    fraction = PerceptionInterface._calculate_visible_fraction(
        intervals, covered
    )
    assert fraction == pytest.approx(0.25)


def test_equal_range_objects_do_not_occlude_each_other_and_are_deterministic():
    ego = vehicle((0.0, 0.0))
    states = {
        "ego": ego,
        "a": vehicle((0.0, 20.0), width=3.0),
        "b": vehicle((0.0, 20.0), width=3.0),
    }
    interface = PerceptionInterface()
    first = interface.generate_observations("ego", ego, states, 0.0)
    second = interface.generate_observations("ego", ego, states, 0.0)
    assert set(first) == {"ego", "a", "b"}
    assert first["a"]["visible_fraction"] == 1.0
    assert first["b"]["visible_fraction"] == 1.0
    assert first == second


def test_all_geometric_visibility_fractions_are_clamped():
    ego = vehicle((0.0, 0.0))
    states = {
        "ego": ego,
        "near": vehicle((0.0, 10.0)),
        "partial": vehicle((-2.0, 20.0), width=4.0),
        "clear": vehicle((-10.0, 20.0)),
    }
    result = PerceptionInterface(sensor_fov_degrees=90.0).generate_observations(
        "ego", ego, states, 0.0
    )
    for detection in result.values():
        if detection["observation_type"] == "OBJECT_DETECTION":
            for key in ("fov_visible_fraction",
                        "occlusion_visible_fraction", "visible_fraction"):
                assert 0.0 <= detection[key] <= 1.0


def test_recursive_output_contains_no_route_or_manoeuvre_truth():
    forbidden = {"route_id", "ground_truth_route_id", "future_edge_sequence",
                 "future_trajectory", "intended_manoeuvre", "manoeuvre"}
    target = vehicle(
        (0.0, 10.0), route_id="route_n_left",
        ground_truth_route_id="route_n_left", intended_manoeuvre="LEFT",
        nested={"future_trajectory": [(0.0, 1.0)]},
    )
    result = observe(target)

    def keys(value):
        if isinstance(value, dict):
            for key, nested in value.items():
                yield key
                yield from keys(nested)
        elif isinstance(value, (list, tuple)):
            for nested in value:
                yield from keys(nested)

    assert forbidden.isdisjoint(set(keys(result)))


def test_default_profile_is_geometric_sensor():
    assert DEFAULT_PERCEPTION_PROFILE == "GEOMETRIC_SENSOR"
    assert PerceptionInterface().profile == "GEOMETRIC_SENSOR"


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("speed", -0.01, "speed must be non-negative"),
        ("heading_radians", math.nan, "heading_radians must be a finite number"),
        ("length", 0.0, "length must be positive"),
        ("width", math.inf, "width must be a finite number"),
    ],
)
def test_invalid_geometric_ego_values_raise(field, value, message):
    ego = vehicle((0.0, 0.0))
    ego[field] = value
    with pytest.raises(ValueError, match=message):
        PerceptionInterface().generate_observations(
            "ego", ego, {"ego": ego}, 0.0
        )


@pytest.mark.parametrize("field", ["length", "width"])
def test_geometric_ego_missing_dimension_raises(field):
    ego = vehicle((0.0, 0.0))
    del ego[field]
    with pytest.raises(ValueError, match=f"missing mandatory field '{field}'"):
        PerceptionInterface().generate_observations(
            "ego", ego, {"ego": ego}, 0.0
        )


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("position", (1.0, 0.0)),
        ("speed", 2.0),
        ("heading_radians", 0.1),
        ("length", 5.0),
        ("width", 2.5),
    ],
)
def test_inconsistent_duplicate_ego_state_raises(field, replacement):
    ego = vehicle((0.0, 0.0), speed=1.0)
    frame_ego = copy.deepcopy(ego)
    frame_ego[field] = replacement
    with pytest.raises(ValueError, match=f"inconsistent.*{field}"):
        PerceptionInterface().generate_observations(
            "ego", ego, {"ego": frame_ego}, 0.0
        )


def test_consistent_duplicate_ego_state_succeeds_without_mutation():
    ego = vehicle((2.0, 3.0), heading=0.25, speed=1.5)
    target = vehicle((2.0, 13.0))
    states = {"ego": copy.deepcopy(ego), "target": target}
    original_ego = copy.deepcopy(ego)
    original_states = copy.deepcopy(states)

    result = PerceptionInterface().generate_observations(
        "ego", ego, states, 4.0
    )

    assert result["ego"]["position"] == pytest.approx((2.0, 3.0))
    assert ego == original_ego
    assert states == original_states


def test_missing_ego_id_fails_clearly():
    ego = vehicle((0.0, 0.0))
    with pytest.raises(ValueError, match="ego.*absent from all_vehicle_data"):
        PerceptionInterface().generate_observations(
            "ego", ego, {"different_vehicle": ego}, 0.0
        )


def test_config_declares_all_three_perception_profiles():
    assert PERCEPTION_PROFILES == {
        "IDEAL_BASELINE",
        "GEOMETRIC_SENSOR",
        "REALISTIC_OBJECT_SENSOR",
    }


def test_invalid_profile_name_fails_clearly():
    with pytest.raises(ValueError, match="Unsupported perception profile"):
        PerceptionInterface(profile="UNKNOWN_SENSOR")


def test_realistic_profile_currently_matches_geometric_visibility():
    ego = vehicle((0.0, 0.0))
    states = {
        "ego": ego,
        "near": vehicle((0.0, 10.0), width=2.0),
        "partial": vehicle((-1.5, 20.0), width=4.0),
        "hidden": vehicle((0.0, 25.0), width=1.0),
        "outside_fov": vehicle((20.0, 0.0)),
    }

    def run(profile):
        interface = PerceptionInterface(
            profile=profile, sensor_fov_degrees=90.0
        )
        detections = interface.generate_observations(
            "ego", ego, states, 1.0
        )
        diagnostics = interface.get_last_diagnostics("ego")
        summary = interface.get_last_summary("ego")
        return detections, diagnostics, summary

    geometric, geometric_diagnostics, geometric_summary = run(
        "GEOMETRIC_SENSOR"
    )
    realistic, realistic_diagnostics, realistic_summary = run(
        "REALISTIC_OBJECT_SENSOR"
    )

    assert set(realistic) == set(geometric)
    for object_id in geometric:
        assert realistic[object_id]["perception_profile"] == (
            "REALISTIC_OBJECT_SENSOR"
        )
        assert geometric[object_id]["perception_profile"] == (
            "GEOMETRIC_SENSOR"
        )
        for field in geometric[object_id]:
            if field != "perception_profile":
                assert realistic[object_id][field] == pytest.approx(
                    geometric[object_id][field]
                ) if isinstance(geometric[object_id][field], float) else (
                    realistic[object_id][field] == geometric[object_id][field]
                )

    def without_profile(items):
        return [
            {key: value for key, value in item.items() if key != "profile"}
            for item in items
        ]

    assert without_profile(realistic_diagnostics) == without_profile(
        geometric_diagnostics
    )
    assert {
        key: value for key, value in realistic_summary.items()
        if key != "profile"
    } == {
        key: value for key, value in geometric_summary.items()
        if key != "profile"
    }
    assert realistic_summary["profile"] == "REALISTIC_OBJECT_SENSOR"


def test_realistic_profile_requires_vehicle_dimensions():
    ego = vehicle((0.0, 0.0))
    target = {
        "position": (0.0, 10.0),
        "speed": 1.0,
        "heading_radians": 0.0,
    }
    interface = PerceptionInterface(profile="REALISTIC_OBJECT_SENSOR")
    result = interface.generate_observations(
        "ego", ego, {"ego": ego, "target": target}, 0.0
    )
    assert "target" not in result
    assert interface.get_last_diagnostics("ego")[0]["reason"] == (
        "INVALID_TARGET_STATE"
    )
