"""Deterministic contract tests for the geometric perception interface."""

# Import copy for use in this module.
import copy
# Import math for use in this module.
import math
# Import sys for use in this module.
import sys
# Import Path from pathlib for the operations below.
from pathlib import Path

# Import numpy as np for use in this module.
import numpy as np
# Import pytest for use in this module.
import pytest

# Set PROJECT_ROOT to Path(__file__).resolve().parents at 1.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
# Call sys.path.insert with the supplied arguments.
sys.path.insert(0, str(PROJECT_ROOT))

# Import APPROACH_ZONE_RADIUS, DEFAULT_PERCEPTION_PROFILE, FUSED_SURROUND_FOV_DEGREES, MAX_CLOSING_SPEED_MPS,
# MIN_REQUIRED_OBSERVATION_RANGE_METERS, OBSERVATION_SAFETY_MARGIN,... from config for the operations below.
from config import (
    APPROACH_ZONE_RADIUS,
    DEFAULT_PERCEPTION_PROFILE,
    FUSED_SURROUND_FOV_DEGREES,
    MAX_CLOSING_SPEED_MPS,
    MIN_REQUIRED_OBSERVATION_RANGE_METERS,
    OBSERVATION_SAFETY_MARGIN,
    PERCEPTION_PROFILES,
    REFERENCE_CORNER_RADAR_COUNT,
    REFERENCE_CORNER_RADAR_HORIZONTAL_FOV_DEGREES,
    REFERENCE_CORNER_RADAR_RANGE_METERS,
    REQUIRED_CONTEXT_SECONDS,
    SENSOR_FOV_DEGREES,
    SENSOR_RANGE,
    validate_sensor_range,
)
# Import PerceptionInterface from perception_interface for the operations below.
from perception_interface import PerceptionInterface


# Vehicle using the inputs and processing steps below.
# Input position: the supplied position.
# Input heading: the supplied heading.
# Input speed: the supplied speed.
# Input length: the supplied length.
# Input width: the supplied width.
# Input extra: the supplied extra.
# Output: state.
def vehicle(position, heading=0.0, speed=0.0, length=4.0, width=2.0, **extra):
    # Set state to a dictionary containing position, heading_radians, speed, length, width, lane_id,
    # lane_position, lane_length,...
    state = {
        # Store position under 'position'.
        # Store heading under 'heading_radians'.
        # Store speed under 'speed'.
        "position": position, "heading_radians": heading, "speed": speed,
        # Store length under 'length'.
        # Store width under 'width'.
        # Store the text 'lane' under 'lane_id'.
        # Store 1.0 under 'lane_position'.
        "length": length, "width": width, "lane_id": "lane", "lane_position": 1.0,
        # Store 100.0 under 'lane_length'.
        # Store the text 'road' under 'road_id'.
        "lane_length": 100.0, "road_id": "road",
    }
    # Update state with the supplied entries.
    state.update(extra)
    # Return state to the caller.
    return state


# Observe using the inputs and processing steps below.
# Input target: the supplied target.
# Input ego: the ego vehicle used in this calculation.
# Input interface_options: the supplied interface options.
# Output: the result of PerceptionInterface(**interface_options).generate_observations(the text 'ego', ego,
# states, 1.25).
def observe(target, ego=None, **interface_options):
    # Set ego to ego or the result of vehicle(a tuple containing 0.0, 0.0).
    ego = ego or vehicle((0.0, 0.0))
    # Set states to a dictionary containing ego, target.
    states = {"ego": ego, "target": target}
    # Return the result of PerceptionInterface(**interface_options).generate_observations(the text 'ego', ego,
    # states, 1.25) to the caller.
    return PerceptionInterface(**interface_options).generate_observations(
        # Supply states to PerceptionInterface(**interface_options).generate_observations.
        "ego", ego, states, 1.25
    )


# Apply pytest.mark.parametrize as a decorator to configure the following definition.
@pytest.mark.parametrize(
    # Supply a tuple containing the text 'heading', the text 'target_position', the text 'expected' to
    # pytest.mark.parametrize.
    ("heading", "target_position", "expected"),
    # Supply a list containing a tuple containing 0.0, a tuple containing 2.0, 10.0, a tuple containing 10.0, the
    # negative of 2.0, a... to pytest.mark.parametrize.
    [
        # Include a tuple containing 0.0, a tuple containing 2.0, 10.0, a tuple containing 10.0, the negative of
        # 2.0 in this list.
        (0.0, (2.0, 10.0), (10.0, -2.0)),
        # Include a tuple containing math.pi divided by 2, a tuple containing 10.0, 2.0, a tuple containing 10.0,
        # 2.0 in this list.
        (math.pi / 2, (10.0, 2.0), (10.0, 2.0)),
        # Include a tuple containing math.pi, a tuple containing the negative of 2.0, the negative of 10.0, a
        # tuple containing 10.0, the... in this list.
        (math.pi, (-2.0, -10.0), (10.0, -2.0)),
        # Include a tuple containing 3 multiplied by math.pi divided by 2, a tuple containing the negative of
        # 10.0, the negative of 2.0, a... in this list.
        (3 * math.pi / 2, (-10.0, -2.0), (10.0, 2.0)),
    ],
)
# Check cardinal coordinate transformations using the setup, calls, and assertions below.
# Input heading: the supplied heading.
# Input target_position: the supplied target position.
# Input expected: the supplied expected.
# Output: no explicit value; normal completion returns None.
def test_cardinal_coordinate_transformations(heading, target_position, expected):
    # Set result to the result of observe(the result of vehicle(target_position)).
    result = observe(vehicle(target_position), ego=vehicle((0.0, 0.0), heading=heading))
    # Require result['target'] at 'relative_position_ego' equals the result of pytest.approx(expected); otherwise
    # raise AssertionError.
    assert result["target"]["relative_position_ego"] == pytest.approx(expected)


# Check positive lateral is left using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_positive_lateral_is_left():
    # Set result to the result of observe(the result of vehicle(a tuple containing the negative of 3.0, 10.0)).
    result = observe(vehicle((-3.0, 10.0)))
    # Require result['target']['relative_position_ego'] at 1 is greater than 0.0; otherwise raise AssertionError.
    assert result["target"]["relative_position_ego"][1] > 0.0


# Check relative velocity uses ego coordinates using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_relative_velocity_uses_ego_coordinates():
    # Set result to the result of observe(the result of vehicle(a tuple containing 0.0, 10.0)).
    result = observe(vehicle((0.0, 10.0), heading=math.pi / 2, speed=8.0),
                     # Supply ego as the result of vehicle(a tuple containing 0.0, 0.0).
                     # Supply speed as 3.0.
                     ego=vehicle((0.0, 0.0), speed=3.0))
    # Require result['target'] at 'relative_velocity_ego' equals the result of pytest.approx(a tuple containing
    # the negative of 3.0, the negative of 8.0); otherwise raise AssertionError.
    assert result["target"]["relative_velocity_ego"] == pytest.approx((-3.0, -8.0))


# Check inside outside and exact range boundary using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_inside_outside_and_exact_range_boundary():
    # Require the text 'target' belongs to the result of observe(the result of vehicle(a tuple containing 0.0,
    # SENSOR_RANGE - 0.01)); otherwise raise AssertionError.
    assert "target" in observe(vehicle((0.0, SENSOR_RANGE - 0.01)))
    # Require the text 'target' belongs to the result of observe(the result of vehicle(a tuple containing 0.0,
    # SENSOR_RANGE)); otherwise raise AssertionError.
    assert "target" in observe(vehicle((0.0, SENSOR_RANGE)))
    # Require the text 'target' does not belong to the result of observe(the result of vehicle(a tuple containing
    # 0.0, SENSOR_RANGE + 0.01)); otherwise raise AssertionError.
    assert "target" not in observe(vehicle((0.0, SENSOR_RANGE + 0.01)))


# Check 360 degree fov includes object behind using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_360_degree_fov_includes_object_behind():
    # Require the text 'target' belongs to the result of observe(the result of vehicle(a tuple containing 0.0,
    # -10.0)); otherwise raise AssertionError.
    assert "target" in observe(vehicle((0.0, -10.0)), sensor_fov_degrees=360.0)


# Check narrow fov inside and outside using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_narrow_fov_inside_and_outside():
    # Require the text 'target' belongs to the result of observe(the result of vehicle(a tuple containing 1.0,
    # 10.0)); otherwise raise AssertionError.
    assert "target" in observe(vehicle((1.0, 10.0)), sensor_fov_degrees=30.0)
    # Require the text 'target' does not belong to the result of observe(the result of vehicle(a tuple containing
    # 10.0, 1.0)); otherwise raise AssertionError.
    assert "target" not in observe(vehicle((10.0, 1.0)), sensor_fov_degrees=30.0)


# Check angle wrapping near minus pi and plus pi using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_angle_wrapping_near_minus_pi_and_plus_pi():
    # Set interface to the result of PerceptionInterface().
    interface = PerceptionInterface(sensor_fov_degrees=20.0)
    # Require the result of interface._is_inside_fov(math.pi minus 0.01) is the same object as False; otherwise
    # raise AssertionError.
    assert interface._is_inside_fov(math.pi - 0.01) is False
    # Require the result of interface._is_inside_fov(the negative of math.pi plus 0.01) is the same object as
    # False; otherwise raise AssertionError.
    assert interface._is_inside_fov(-math.pi + 0.01) is False
    # Set behind to the result of observe(the result of vehicle(a tuple containing the negative of 0.01, the
    # negative of 10.0)).
    behind = observe(vehicle((-0.01, -10.0)), sensor_fov_degrees=360.0)
    # Require the text 'target' belongs to behind; otherwise raise AssertionError.
    assert "target" in behind


# Check no occlusion at different bearings using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_no_occlusion_at_different_bearings():
    # Set ego to the result of vehicle(a tuple containing 0.0, 0.0).
    ego = vehicle((0.0, 0.0))
    # Set states to a dictionary containing ego, a, b.
    states = {"ego": ego, "a": vehicle((-8.0, 15.0)), "b": vehicle((8.0, 30.0))}
    # Set result to the result of PerceptionInterface().generate_observations(the text 'ego', ego, states, 0.0).
    result = PerceptionInterface().generate_observations("ego", ego, states, 0.0)
    # Require a set built from result equals a set containing the text 'ego', the text 'a', the text 'b';
    # otherwise raise AssertionError.
    assert set(result) == {"ego", "a", "b"}
    # Require result['b'] at 'visible_fraction' equals the result of pytest.approx(1.0); otherwise raise
    # AssertionError.
    assert result["b"]["visible_fraction"] == pytest.approx(1.0)


# Check full occlusion directly behind using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_full_occlusion_directly_behind():
    # Set ego to the result of vehicle(a tuple containing 0.0, 0.0).
    ego = vehicle((0.0, 0.0))
    # Set states to a dictionary containing ego, near, far.
    states = {"ego": ego, "near": vehicle((0.0, 10.0), width=3.0),
              # Store the result of vehicle(a tuple containing 0.0, 20.0) under 'far'.
              "far": vehicle((0.0, 20.0), width=2.0)}
    # Set result to the result of PerceptionInterface().generate_observations(the text 'ego', ego, states, 0.0).
    result = PerceptionInterface().generate_observations("ego", ego, states, 0.0)
    # Require the text 'near' belongs to result and the text 'far' does not belong to result; otherwise raise
    # AssertionError.
    assert "near" in result and "far" not in result


# Check partial occlusion is retained using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_partial_occlusion_is_retained():
    # Set ego to the result of vehicle(a tuple containing 0.0, 0.0).
    ego = vehicle((0.0, 0.0))
    # Set states to a dictionary containing ego, near, far.
    states = {"ego": ego, "near": vehicle((0.0, 10.0), width=2.0),
              # Store the result of vehicle(a tuple containing the negative of 1.5, 20.0) under 'far'.
              "far": vehicle((-1.5, 20.0), width=4.0)}
    # Set result to the result of PerceptionInterface().generate_observations(the text 'ego', ego, states, 0.0).
    result = PerceptionInterface().generate_observations("ego", ego, states, 0.0)
    # Require 0.0 is less than result['far'] at 'visible_fraction'; is less than 1.0; otherwise raise
    # AssertionError.
    assert 0.0 < result["far"]["visible_fraction"] < 1.0


# Check vehicle dimensions affect occlusion using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_vehicle_dimensions_affect_occlusion():
    # Set ego to the result of vehicle(a tuple containing 0.0, 0.0).
    ego = vehicle((0.0, 0.0))
    # Frame using the inputs and processing steps below.
    # Input near_width: the supplied near width.
    # Output: the result of PerceptionInterface().generate_observations(the text 'ego', ego, states, 0.0).
    def frame(near_width):
        # Set states to a dictionary containing ego, near, far.
        states = {"ego": ego, "near": vehicle((0.0, 10.0), width=near_width),
                  # Store the result of vehicle(a tuple containing the negative of 1.5, 20.0) under 'far'.
                  "far": vehicle((-1.5, 20.0), width=2.0)}
        # Return the result of PerceptionInterface().generate_observations(the text 'ego', ego, states, 0.0) to
        # the caller.
        return PerceptionInterface().generate_observations("ego", ego, states, 0.0)
    # Require the text 'far' belongs to the result of frame(1.0); otherwise raise AssertionError.
    assert "far" in frame(1.0)
    # Require the text 'far' does not belong to the result of frame(6.0); otherwise raise AssertionError.
    assert "far" not in frame(6.0)


# Apply pytest.mark.parametrize as a decorator to configure the following definition.
@pytest.mark.parametrize(
    # Supply a tuple containing the text 'front_bumper', the text 'heading', the text 'expected_center', the text
    # 'longitudinal_axis', the... to pytest.mark.parametrize.
    ("front_bumper", "heading", "expected_center", "longitudinal_axis",
     "expected_longitudinal_limits", "lateral_axis", "expected_lateral_limits"),
    # Supply a list containing a tuple containing a tuple containing 0.0, 10.0, 0.0, a tuple containing 0.0, 8.0,
    # 1, a tuple containing... to pytest.mark.parametrize.
    [
        # Include a tuple containing a tuple containing 0.0, 10.0, 0.0, a tuple containing 0.0, 8.0, 1, a tuple
        # containing 6.0, 10.0, 0, a... in this list.
        ((0.0, 10.0), 0.0, (0.0, 8.0), 1, (6.0, 10.0), 0, (-1.0, 1.0)),
        # Include a tuple containing a tuple containing 10.0, 0.0, math.pi divided by 2.0, a tuple containing 8.0,
        # 0.0, 0, a tuple containing... in this list.
        ((10.0, 0.0), math.pi / 2.0, (8.0, 0.0), 0, (6.0, 10.0), 1, (-1.0, 1.0)),
    ],
)
# Check bounding box uses sumo front bumper reference using the setup, calls, and assertions below.
# Input front_bumper: the supplied front bumper.
# Input heading: the supplied heading.
# Input expected_center: the supplied expected center.
# Input longitudinal_axis: the supplied longitudinal axis.
# Input expected_longitudinal_limits: the supplied expected longitudinal limits.
# Input lateral_axis: the supplied lateral axis.
# Input expected_lateral_limits: the supplied expected lateral limits.
# Output: no explicit value; normal completion returns None.
def test_bounding_box_uses_sumo_front_bumper_reference(
        # Declare front_bumper, heading, expected_center, longitudinal_axis as input parameters.
        front_bumper, heading, expected_center, longitudinal_axis,
        # Declare expected_longitudinal_limits, lateral_axis, expected_lateral_limits as input parameters.
        expected_longitudinal_limits, lateral_axis, expected_lateral_limits):
    # Set state to the result of vehicle(front_bumper).
    state = vehicle(front_bumper, heading=heading, length=4.0, width=2.0)
    # Set original to the result of copy.deepcopy(state).
    original = copy.deepcopy(state)
    # Set corners to the result of PerceptionInterface._calculate_bounding_box(state).
    corners = PerceptionInterface._calculate_bounding_box(state)

    # Require the result of corners.mean() equals the result of pytest.approx(expected_center); otherwise raise
    # AssertionError.
    assert corners.mean(axis=0) == pytest.approx(expected_center)
    # Require a tuple containing the result of corners[:, longitudinal_axis].min(), the result of corners[:,
    # longitudinal_axis].max() equals the result of pytest.approx(expected_longitudinal_limits); otherwise raise
    # AssertionError.
    assert (corners[:, longitudinal_axis].min(),
            # Evaluate the result of pytest.approx(expected_longitudinal_limits) as part of the enclosing
            # expression.
            corners[:, longitudinal_axis].max()) == pytest.approx(
                # Supply expected_longitudinal_limits to pytest.approx.
                expected_longitudinal_limits
            )
    # Require a tuple containing the result of corners[:, lateral_axis].min(), the result of corners[:,
    # lateral_axis].max() equals the result of pytest.approx(expected_lateral_limits); otherwise raise
    # AssertionError.
    assert (corners[:, lateral_axis].min(),
            # Evaluate the result of pytest.approx(expected_lateral_limits) as part of the enclosing expression.
            corners[:, lateral_axis].max()) == pytest.approx(
                # Supply expected_lateral_limits to pytest.approx.
                expected_lateral_limits
            )
    # The supplied SUMO reference lies on the forward face of the box.
    # Set forward_face to the result of corners[:2].mean().
    forward_face = corners[:2].mean(axis=0)
    # Require forward_face equals the result of pytest.approx(front_bumper); otherwise raise AssertionError.
    assert forward_face == pytest.approx(front_bumper)
    # Require state equals original; otherwise raise AssertionError.
    assert state == original


# Check each ego receives a different local set using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_each_ego_receives_a_different_local_set():
    # Set states to a dictionary containing a, b, c.
    states = {"a": vehicle((0.0, 0.0)), "b": vehicle((0.0, 100.0)),
              # Store the result of vehicle(a tuple containing 0.0, 150.0) under 'c'.
              "c": vehicle((0.0, 150.0))}
    # Set interface to the result of PerceptionInterface().
    interface = PerceptionInterface(sensor_range=60.0, profile="IDEAL_BASELINE")
    # Set view_a to the result of interface.generate_observations(the text 'a', states at 'a', states, 0.0).
    view_a = interface.generate_observations("a", states["a"], states, 0.0)
    # Set view_b to the result of interface.generate_observations(the text 'b', states at 'b', states, 0.0).
    view_b = interface.generate_observations("b", states["b"], states, 0.0)
    # Require a set built from view_a equals a set containing the text 'a'; otherwise raise AssertionError.
    assert set(view_a) == {"a"}
    # Require a set built from view_b equals a set containing the text 'b', the text 'c'; otherwise raise
    # AssertionError.
    assert set(view_b) == {"b", "c"}


# Check ego label schema and no route leakage using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_ego_label_schema_and_no_route_leakage():
    # Set target to the result of vehicle(a tuple containing 0.0, 10.0).
    target = vehicle((0.0, 10.0), route_id="route_n_left",
                     # Supply ground_truth_route_id as the text 'route_n_left'.
                     # Supply intended_manoeuvre as the text 'LEFT'.
                     ground_truth_route_id="route_n_left", intended_manoeuvre="LEFT")
    # Set result to the result of observe(target).
    result = observe(target)
    # Require result['ego'] at 'observation_type' equals the text 'EGO_LOCALIZATION'; otherwise raise
    # AssertionError.
    assert result["ego"]["observation_type"] == "EGO_LOCALIZATION"
    # Require result['ego'] at 'detection_status' equals the text 'SELF_LOCALIZATION'; otherwise raise
    # AssertionError.
    assert result["ego"]["detection_status"] == "SELF_LOCALIZATION"
    # Set forbidden to a set containing the text 'route_id', the text 'ground_truth_route_id', the text
    # 'intended_manoeuvre'.
    forbidden = {"route_id", "ground_truth_route_id", "intended_manoeuvre"}
    # Require the result of forbidden.isdisjoint(result at 'target'); otherwise raise AssertionError.
    assert forbidden.isdisjoint(result["target"])


# Check invalid ego raises and invalid target is diagnostic using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_invalid_ego_raises_and_invalid_target_is_diagnostic():
    # Set invalid_ego to the result of vehicle(a tuple containing math.nan, 0.0).
    invalid_ego = vehicle((math.nan, 0.0))
    # Enter the result of pytest.raises(ValueError) and run the enclosed operations within that context.
    with pytest.raises(ValueError, match="position"):
        # Call PerceptionInterface().generate_observations with the supplied arguments.
        PerceptionInterface().generate_observations(
            # Store invalid_ego under 'ego'.
            "ego", invalid_ego, {"ego": invalid_ego}, 0.0
        )
    # Set ego to the result of vehicle(a tuple containing 0.0, 0.0).
    ego = vehicle((0.0, 0.0))
    # Set interface to the result of PerceptionInterface().
    interface = PerceptionInterface()
    # Set result to the result of interface.generate_observations(the text 'ego', ego, a dictionary containing
    # ego, bad, 0.0).
    result = interface.generate_observations(
        # Store ego under 'ego'.
        # Store the result of vehicle(a tuple containing 1.0, 1.0) under 'bad'.
        "ego", ego, {"ego": ego, "bad": vehicle((1.0, 1.0), width=-1.0)}, 0.0
    )
    # Require a set built from result equals a set containing the text 'ego'; otherwise raise AssertionError.
    assert set(result) == {"ego"}
    # Require interface.last_diagnostics[0] at 'reason' equals the text 'INVALID_TARGET_STATE'; otherwise raise
    # AssertionError.
    assert interface.last_diagnostics[0]["reason"] == "INVALID_TARGET_STATE"


# Check inputs are not mutated and results are deterministic using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_inputs_are_not_mutated_and_results_are_deterministic():
    # Set (ego, target) to a tuple containing the result of vehicle(a tuple containing 0.0, 0.0), the result of
    # vehicle(a tuple containing 2.0, 20.0).
    ego, target = vehicle((0.0, 0.0)), vehicle((2.0, 20.0))
    # Set states to a dictionary containing ego, target.
    states = {"ego": ego, "target": target}
    # Set original to the result of copy.deepcopy(states).
    original = copy.deepcopy(states)
    # Set interface to the result of PerceptionInterface().
    interface = PerceptionInterface()
    # Set first to the result of interface.generate_observations(the text 'ego', ego, states, 2.0).
    first = interface.generate_observations("ego", ego, states, 2.0)
    # Set second to the result of interface.generate_observations(the text 'ego', ego, states, 2.0).
    second = interface.generate_observations("ego", ego, states, 2.0)
    # Require states equals original; otherwise raise AssertionError.
    assert states == original
    # Require first equals second; otherwise raise AssertionError.
    assert first == second


# Check profiles differ when occlusion exists using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_profiles_differ_when_occlusion_exists():
    # Set ego to the result of vehicle(a tuple containing 0.0, 0.0).
    ego = vehicle((0.0, 0.0))
    # Set states to a dictionary containing ego, near, far.
    states = {"ego": ego, "near": vehicle((0.0, 10.0), width=3.0),
              # Store the result of vehicle(a tuple containing 0.0, 20.0) under 'far'.
              "far": vehicle((0.0, 20.0), width=2.0)}
    # Set geometric to the result of PerceptionInterface().generate_observations(the text 'ego', ego, states,
    # 0.0).
    geometric = PerceptionInterface().generate_observations("ego", ego, states, 0.0)
    # Set ideal to the result of PerceptionInterface(profile='IDEAL_BASELINE').generate_observations(the text
    # 'ego', ego, states, 0.0).
    ideal = PerceptionInterface(profile="IDEAL_BASELINE").generate_observations(
        # Supply states to PerceptionInterface(profile='IDEAL_BASELINE').generate_observations.
        "ego", ego, states, 0.0
    )
    # Require the text 'far' does not belong to geometric and the text 'far' belongs to ideal; otherwise raise
    # AssertionError.
    assert "far" not in geometric and "far" in ideal
    # Require ideal['far'] at 'perception_profile' equals the text 'IDEAL_BASELINE'; otherwise raise
    # AssertionError.
    assert ideal["far"]["perception_profile"] == "IDEAL_BASELINE"


# Check configured radii derivations using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_configured_radii_derivations():
    # Require APPROACH_ZONE_RADIUS equals the result of pytest.approx(76.67); otherwise raise AssertionError.
    assert APPROACH_ZONE_RADIUS == pytest.approx(76.67)
    # Require REFERENCE_CORNER_RADAR_RANGE_METERS equals the result of pytest.approx(160.0); otherwise raise
    # AssertionError.
    assert REFERENCE_CORNER_RADAR_RANGE_METERS == pytest.approx(160.0)
    # Require REFERENCE_CORNER_RADAR_HORIZONTAL_FOV_DEGREES equals the result of pytest.approx(150.0); otherwise
    # raise AssertionError.
    assert REFERENCE_CORNER_RADAR_HORIZONTAL_FOV_DEGREES == pytest.approx(150.0)
    # Require REFERENCE_CORNER_RADAR_COUNT equals 4; otherwise raise AssertionError.
    assert REFERENCE_CORNER_RADAR_COUNT == 4
    # Require FUSED_SURROUND_FOV_DEGREES equals the result of pytest.approx(360.0); otherwise raise
    # AssertionError.
    assert FUSED_SURROUND_FOV_DEGREES == pytest.approx(360.0)
    # Require SENSOR_FOV_DEGREES equals the result of pytest.approx(360.0); otherwise raise AssertionError.
    assert SENSOR_FOV_DEGREES == pytest.approx(360.0)
    # Require SENSOR_RANGE equals the result of pytest.approx(160.0); otherwise raise AssertionError.
    assert SENSOR_RANGE == pytest.approx(160.0)
    # Require MIN_REQUIRED_OBSERVATION_RANGE_METERS equals the result of pytest.approx(MAX_CLOSING_SPEED_MPS
    # multiplied by REQUIRED_CONTEXT_SECONDS plus OBSERVATION_SAFETY_MARGIN); otherwise raise AssertionError.
    assert MIN_REQUIRED_OBSERVATION_RANGE_METERS == pytest.approx(
        # Supply MAX_CLOSING_SPEED_MPS multiplied by REQUIRED_CONTEXT_SECONDS plus OBSERVATION_SAFETY_MARGIN to
        # pytest.approx.
        MAX_CLOSING_SPEED_MPS * REQUIRED_CONTEXT_SECONDS
        # Evaluate OBSERVATION_SAFETY_MARGIN as part of the enclosing expression.
        + OBSERVATION_SAFETY_MARGIN
    )
    # Require MIN_REQUIRED_OBSERVATION_RANGE_METERS equals the result of pytest.approx(118.34); otherwise raise
    # AssertionError.
    assert MIN_REQUIRED_OBSERVATION_RANGE_METERS == pytest.approx(118.34)
    # Require SENSOR_RANGE is at least MIN_REQUIRED_OBSERVATION_RANGE_METERS; otherwise raise AssertionError.
    assert SENSOR_RANGE >= MIN_REQUIRED_OBSERVATION_RANGE_METERS


# Check short reference range fails startup validation using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_short_reference_range_fails_startup_validation():
    # Enter the result of pytest.raises(ValueError) and run the enclosed operations within that context.
    with pytest.raises(ValueError, match=r"100\.00 m.*118\.34 m"):
        # Call validate_sensor_range with the supplied arguments.
        validate_sensor_range(100.0)


# Check sensor configuration is summary metadata not an observation using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_sensor_configuration_is_summary_metadata_not_an_observation():
    # Set interface to the result of PerceptionInterface().
    interface = PerceptionInterface()
    # Set result to the result of interface.generate_observations(the text 'ego', the result of vehicle(a tuple
    # containing 0.0, 0.0), a dictionary containing ego,...).
    result = interface.generate_observations(
        # Supply the result of vehicle(a tuple containing 0.0, 0.0) to interface.generate_observations.
        "ego", vehicle((0.0, 0.0)),
        # Store the result of vehicle(a tuple containing 0.0, 0.0) under 'ego'.
        # Store the result of vehicle(a tuple containing 0.0, 10.0) under 'target'.
        {"ego": vehicle((0.0, 0.0)), "target": vehicle((0.0, 10.0))}, 0.0
    )
    # Set metadata to interface.get_last_summary('ego') at 'sensor_configuration'.
    metadata = interface.get_last_summary("ego")["sensor_configuration"]
    # Require metadata equals a dictionary containing reference_sensor_name, individual_radar_range_meters,...;
    # otherwise raise AssertionError.
    assert metadata == {
        "reference_sensor_name": "Bosch corner radar reference profile",
        # Store 160.0 under 'individual_radar_range_meters'.
        "individual_radar_range_meters": 160.0,
        # Store 150.0 under 'individual_radar_horizontal_fov_degrees'.
        "individual_radar_horizontal_fov_degrees": 150.0,
        # Store 4 under 'sensor_count'.
        "sensor_count": 4,
        # Store 360.0 under 'fused_fov_degrees'.
        "fused_fov_degrees": 360.0,
        # Store the result of pytest.approx(118.34) under 'minimum_required_observation_range_meters'.
        "minimum_required_observation_range_meters": pytest.approx(118.34),
        # Store 160.0 under 'selected_operational_sensor_range_meters'.
        "selected_operational_sensor_range_meters": 160.0,
        # Store True under 'range_requirement_satisfied'.
        "range_requirement_satisfied": True,
    }
    # Require whether every item is true in a lazy sequence of the text 'sensor_configuration' does not belong to
    # observation for observation in values from result; otherwise raise AssertionError.
    assert all("sensor_configuration" not in observation
               # Evaluate values from result as part of the enclosing expression.
               for observation in result.values())


# Check ideal detects beyond old limit and geometry stops at 160m using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_ideal_detects_beyond_old_limit_and_geometry_stops_at_160m():
    # Set target to the result of vehicle(a tuple containing 0.0, MIN_REQUIRED_OBSERVATION_RANGE_METERS plus
    # 10.0).
    target = vehicle((0.0, MIN_REQUIRED_OBSERVATION_RANGE_METERS + 10.0))
    # Require the text 'target' belongs to the result of observe(target); otherwise raise AssertionError.
    assert "target" in observe(target, profile="IDEAL_BASELINE")
    # Require the text 'target' does not belong to the result of observe(the result of vehicle(a tuple containing
    # 0.0, SENSOR_RANGE + 0.01)); otherwise raise AssertionError.
    assert "target" not in observe(
        # Supply profile as the text 'GEOMETRIC_SENSOR'.
        vehicle((0.0, SENSOR_RANGE + 0.01)), profile="GEOMETRIC_SENSOR"
    )


# Diagnostic by target using the inputs and processing steps below.
# Input interface: the supplied interface.
# Input ego_id: the identifier of the ego vehicle.
# Output: a dictionary of item at 'target_id' mapped to item for item in the result of
# interface.get_last_diagnostics(ego_id).
def diagnostic_by_target(interface, ego_id="ego"):
    # Return a dictionary of item at 'target_id' mapped to item for item in the result of
    # interface.get_last_diagnostics(ego_id) to the caller.
    return {
        # Evaluate item at 'target_id' as part of the enclosing expression.
        item["target_id"]: item
        # Evaluate the result of interface.get_last_diagnostics(ego_id) as part of the enclosing expression.
        for item in interface.get_last_diagnostics(ego_id)
    }


# Check bbox edge inside fov when center is outside using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_bbox_edge_inside_fov_when_center_is_outside():
    # Set target to the result of vehicle(a tuple containing the negative of 4.25, 20.0).
    target = vehicle((-4.25, 20.0), width=4.0)
    # Set interface to the result of PerceptionInterface().
    interface = PerceptionInterface(sensor_fov_degrees=20.0)
    # Set result to the result of interface.generate_observations(the text 'ego', the result of vehicle(a tuple
    # containing 0.0, 0.0), a dictionary containing ego,...).
    result = interface.generate_observations(
        # Supply the result of vehicle(a tuple containing 0.0, 0.0) to interface.generate_observations.
        "ego", vehicle((0.0, 0.0)),
        # Store the result of vehicle(a tuple containing 0.0, 0.0) under 'ego'.
        # Store target under 'target'.
        {"ego": vehicle((0.0, 0.0)), "target": target}, 0.0
    )
    # Require the text 'target' belongs to result; otherwise raise AssertionError.
    assert "target" in result
    # Require 0.0 is less than result['target'] at 'fov_visible_fraction'; is less than 1.0; otherwise raise
    # AssertionError.
    assert 0.0 < result["target"]["fov_visible_fraction"] < 1.0


# Check center inside fov with bbox edge outside is partial using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_center_inside_fov_with_bbox_edge_outside_is_partial():
    # Set target to the result of vehicle(a tuple containing the negative of 2.8, 20.0).
    target = vehicle((-2.8, 20.0), width=5.0)
    # Set result to the result of observe(target).
    result = observe(target, sensor_fov_degrees=20.0)
    # Require the text 'target' belongs to result; otherwise raise AssertionError.
    assert "target" in result
    # Require 0.0 is less than result['target'] at 'fov_visible_fraction'; is less than 1.0; otherwise raise
    # AssertionError.
    assert 0.0 < result["target"]["fov_visible_fraction"] < 1.0
    # Require 0.0 is less than result['target'] at 'visible_fraction'; is less than 1.0; otherwise raise
    # AssertionError.
    assert 0.0 < result["target"]["visible_fraction"] < 1.0


# Check wrapped object interval intersects 360 fov using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_wrapped_object_interval_intersects_360_fov():
    # Set result to the result of observe(the result of vehicle(a tuple containing 0.0, the negative of 15.0)).
    result = observe(
        # Supply sensor_fov_degrees as 360.0.
        # Supply width as 4.0.
        vehicle((0.0, -15.0), width=4.0), sensor_fov_degrees=360.0
    )
    # Require result['target'] at 'fov_visible_fraction' equals the result of pytest.approx(1.0); otherwise raise
    # AssertionError.
    assert result["target"]["fov_visible_fraction"] == pytest.approx(1.0)


# Check ideal profile skips geometry and accepts missing dimensions using the setup, calls, and assertions below.
# Input monkeypatch: the supplied monkeypatch.
# Output: no explicit value; normal completion returns None.
def test_ideal_profile_skips_geometry_and_accepts_missing_dimensions(monkeypatch):
    # Set ego to the result of vehicle(a tuple containing 0.0, 0.0).
    ego = vehicle((0.0, 0.0))
    # Set target to a dictionary containing position, speed, heading_radians.
    target = {"position": (0.0, 10.0), "speed": 1.0,
              # Store 0.0 under 'heading_radians'.
              "heading_radians": 0.0}
    # Set interface to the result of PerceptionInterface().
    interface = PerceptionInterface(profile="IDEAL_BASELINE",
                                    # Supply sensor_fov_degrees as 1.0.
                                    sensor_fov_degrees=1.0)
    # Call monkeypatch.setattr with the supplied arguments.
    monkeypatch.setattr(
        # Supply interface to monkeypatch.setattr.
        interface, "_calculate_bounding_box",
        # Declare _ as input parameter.
        lambda *_: pytest.fail("ideal baseline calculated bounding-box geometry")
    )
    # Set result to the result of interface.generate_observations(the text 'ego', ego, a dictionary containing
    # ego, target, 0.0).
    result = interface.generate_observations(
        # Store ego under 'ego'.
        # Store target under 'target'.
        "ego", ego, {"ego": ego, "target": target}, 0.0
    )
    # Require the text 'target' belongs to result; otherwise raise AssertionError.
    assert "target" in result
    # Require the text 'length' does not belong to result at 'target'; otherwise raise AssertionError.
    assert "length" not in result["target"]
    # Require the text 'width' does not belong to result at 'target'; otherwise raise AssertionError.
    assert "width" not in result["target"]
    # Require result['target'] at 'visible_fraction' equals 1.0; otherwise raise AssertionError.
    assert result["target"]["visible_fraction"] == 1.0


# Check geometric profile requires dimensions and logs invalid target using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_geometric_profile_requires_dimensions_and_logs_invalid_target():
    # Set ego to the result of vehicle(a tuple containing 0.0, 0.0).
    ego = vehicle((0.0, 0.0))
    # Set target to a dictionary containing position, speed, heading_radians.
    target = {"position": (0.0, 10.0), "speed": 1.0,
              # Store 0.0 under 'heading_radians'.
              "heading_radians": 0.0}
    # Set interface to the result of PerceptionInterface().
    interface = PerceptionInterface()
    # Set result to the result of interface.generate_observations(the text 'ego', ego, a dictionary containing
    # ego, target, 0.0).
    result = interface.generate_observations(
        # Store ego under 'ego'.
        # Store target under 'target'.
        "ego", ego, {"ego": ego, "target": target}, 0.0
    )
    # Require the text 'target' does not belong to result; otherwise raise AssertionError.
    assert "target" not in result
    # Set item to diagnostic_by_target(interface) at 'target'.
    item = diagnostic_by_target(interface)["target"]
    # Require item at 'result' equals the text 'REJECTED'; otherwise raise AssertionError.
    assert item["result"] == "REJECTED"
    # Require item at 'reason' equals the text 'INVALID_TARGET_STATE'; otherwise raise AssertionError.
    assert item["reason"] == "INVALID_TARGET_STATE"


# Check diagnostics cover range fov detection occlusion and partial using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def test_diagnostics_cover_range_fov_detection_occlusion_and_partial():
    # Set ego to the result of vehicle(a tuple containing 0.0, 0.0).
    ego = vehicle((0.0, 0.0))
    # Set states to a dictionary containing ego, visible, out_range, out_fov, near, hidden, partial, bad.
    states = {
        # Store ego under 'ego'.
        "ego": ego,
        # Store the result of vehicle(a tuple containing the negative of 10.0, 30.0) under 'visible'.
        "visible": vehicle((-10.0, 30.0)),
        # Store the result of vehicle(a tuple containing 0.0, SENSOR_RANGE plus 1.0) under 'out_range'.
        "out_range": vehicle((0.0, SENSOR_RANGE + 1.0)),
        # Store the result of vehicle(a tuple containing 30.0, 0.0) under 'out_fov'.
        "out_fov": vehicle((30.0, 0.0)),
        # Store the result of vehicle(a tuple containing 0.0, 10.0) under 'near'.
        "near": vehicle((0.0, 10.0), width=3.0),
        # Store the result of vehicle(a tuple containing 0.0, 25.0) under 'hidden'.
        "hidden": vehicle((0.0, 25.0), width=2.0),
        # Store the result of vehicle(a tuple containing the negative of 3.5, 25.0) under 'partial'.
        "partial": vehicle((-3.5, 25.0), width=4.0),
        # Store the result of vehicle(a tuple containing 1.0, 1.0) under 'bad'.
        "bad": vehicle((1.0, 1.0), width=-1.0),
    }
    # Set interface to the result of PerceptionInterface().
    interface = PerceptionInterface(sensor_fov_degrees=60.0)
    # Set result to the result of interface.generate_observations(the text 'ego', ego, states, 3.0).
    result = interface.generate_observations("ego", ego, states, 3.0)
    # Set details to the result of diagnostic_by_target(interface).
    details = diagnostic_by_target(interface)
    # Set repeated to the result of interface.generate_observations(the text 'ego', ego, states, 3.0).
    repeated = interface.generate_observations("ego", ego, states, 3.0)
    # Require repeated equals result; otherwise raise AssertionError.
    assert repeated == result
    # Require the number of entries in the result of interface.get_last_diagnostics(the text 'ego') equals the
    # number of entries in states minus 1; otherwise raise AssertionError.
    assert len(interface.get_last_diagnostics("ego")) == len(states) - 1
    # Require a set built from details equals a set built from states minus a set containing the text 'ego';
    # otherwise raise AssertionError.
    assert set(details) == set(states) - {"ego"}
    # Require details['visible'] at 'reason' equals the text 'DETECTED'; otherwise raise AssertionError.
    assert details["visible"]["reason"] == "DETECTED"
    # Require details['out_range'] at 'reason' equals the text 'OUT_OF_RANGE'; otherwise raise AssertionError.
    assert details["out_range"]["reason"] == "OUT_OF_RANGE"
    # Require details['out_fov'] at 'reason' equals the text 'OUT_OF_FOV'; otherwise raise AssertionError.
    assert details["out_fov"]["reason"] == "OUT_OF_FOV"
    # Require details['hidden'] at 'reason' equals the text 'FULLY_OCCLUDED'; otherwise raise AssertionError.
    assert details["hidden"]["reason"] == "FULLY_OCCLUDED"
    # Require details['partial'] at 'reason' equals the text 'PARTIALLY_VISIBLE'; otherwise raise AssertionError.
    assert details["partial"]["reason"] == "PARTIALLY_VISIBLE"
    # Require details['partial'] at 'result' equals the text 'DETECTED'; otherwise raise AssertionError.
    assert details["partial"]["result"] == "DETECTED"
    # Require details['bad'] at 'reason' equals the text 'INVALID_TARGET_STATE'; otherwise raise AssertionError.
    assert details["bad"]["reason"] == "INVALID_TARGET_STATE"
    # Require the text 'hidden' does not belong to result and the text 'partial' belongs to result; otherwise
    # raise AssertionError.
    assert "hidden" not in result and "partial" in result
    # Require whether every item is true in a lazy sequence of the text 'route_id' does not belong to detection
    # for detection in values from result; otherwise raise AssertionError.
    assert all("route_id" not in detection for detection in result.values())

    # Set summary to the result of interface.get_last_summary(the text 'ego').
    summary = interface.get_last_summary("ego")
    # Require summary at 'candidate_targets' equals the number of entries in states minus 1; otherwise raise
    # AssertionError.
    assert summary["candidate_targets"] == len(states) - 1
    # Require summary at 'detected_targets' equals the sum of a lazy sequence of item['result'] equals 'DETECTED'
    # for item in values from details; otherwise raise AssertionError.
    assert summary["detected_targets"] == sum(
        # Evaluate item at 'result' equals the text 'DETECTED' as part of the enclosing expression.
        item["result"] == "DETECTED" for item in details.values()
    )
    # Iterate over the result of {'invalid_targets': 'INVALID_TARGET_STATE', 'out_of_range_targets':
    # 'OUT_OF_RANGE',...(), binding each item to (key, reason).
    for key, reason in {
        "invalid_targets": "INVALID_TARGET_STATE",
        "out_of_range_targets": "OUT_OF_RANGE",
        "out_of_fov_targets": "OUT_OF_FOV",
        "fully_occluded_targets": "FULLY_OCCLUDED",
        "partially_visible_targets": "PARTIALLY_VISIBLE",
    }.items():
        # Require summary at key equals the sum of a lazy sequence of item['reason'] equals reason for item in
        # values from details; otherwise raise AssertionError.
        assert summary[key] == sum(
            # Evaluate item at 'reason' equals reason as part of the enclosing expression.
            item["reason"] == reason for item in details.values()
        )


# Check per ego diagnostics are independent and accessors return copies using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_per_ego_diagnostics_are_independent_and_accessors_return_copies():
    # Set states to a dictionary containing a, b, c.
    states = {
        # Store the result of vehicle(a tuple containing 0.0, 0.0) under 'a'.
        "a": vehicle((0.0, 0.0)),
        # Store the result of vehicle(a tuple containing 0.0, 20.0) under 'b'.
        "b": vehicle((0.0, 20.0)),
        # Store the result of vehicle(a tuple containing 0.0, 200.0) under 'c'.
        "c": vehicle((0.0, 200.0)),
    }
    # Set interface to the result of PerceptionInterface().
    interface = PerceptionInterface(profile="IDEAL_BASELINE")
    # Call interface.generate_observations with the supplied arguments.
    interface.generate_observations("a", states["a"], states, 1.0)
    # Set a_before to the result of interface.get_last_diagnostics(the text 'a').
    a_before = interface.get_last_diagnostics("a")
    # Call interface.generate_observations with the supplied arguments.
    interface.generate_observations("b", states["b"], states, 2.0)
    # Require the result of interface.get_last_diagnostics(the text 'a') equals a_before; otherwise raise
    # AssertionError.
    assert interface.get_last_diagnostics("a") == a_before
    # Require the result of interface.get_last_diagnostics(the text 'b') differs from a_before; otherwise raise
    # AssertionError.
    assert interface.get_last_diagnostics("b") != a_before

    # Set returned to the result of interface.get_last_diagnostics().
    returned = interface.get_last_diagnostics()
    # Set returned['a'][0]['reason'] to the text 'MUTATED'.
    returned["a"][0]["reason"] = "MUTATED"
    # Require interface.get_last_diagnostics('a')[0] at 'reason' differs from the text 'MUTATED'; otherwise raise
    # AssertionError.
    assert interface.get_last_diagnostics("a")[0]["reason"] != "MUTATED"
    # Set summary to the result of interface.get_last_summary(the text 'a').
    summary = interface.get_last_summary("a")
    # Set summary['detected_targets'] to 999.
    summary["detected_targets"] = 999
    # Require interface.get_last_summary('a') at 'detected_targets' differs from 999; otherwise raise
    # AssertionError.
    assert interface.get_last_summary("a")["detected_targets"] != 999


# Check multiple overlapping occluders do not double count using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_multiple_overlapping_occluders_do_not_double_count():
    # Set intervals to a list containing a tuple containing the negative of 0.2, 0.2.
    intervals = [(-0.2, 0.2)]
    # Set covered to a list containing a tuple containing the negative of 0.2, 0.05, a tuple containing the
    # negative of 0.05, 0.1.
    covered = [(-0.2, 0.05), (-0.05, 0.1)]
    # Set fraction to the result of PerceptionInterface._calculate_visible_fraction(intervals, covered).
    fraction = PerceptionInterface._calculate_visible_fraction(
        # Supply intervals to PerceptionInterface._calculate_visible_fraction.
        intervals, covered
    )
    # Require fraction equals the result of pytest.approx(0.25); otherwise raise AssertionError.
    assert fraction == pytest.approx(0.25)


# Check equal range objects do not occlude each other and are deterministic using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_equal_range_objects_do_not_occlude_each_other_and_are_deterministic():
    # Set ego to the result of vehicle(a tuple containing 0.0, 0.0).
    ego = vehicle((0.0, 0.0))
    # Set states to a dictionary containing ego, a, b.
    states = {
        # Store ego under 'ego'.
        "ego": ego,
        # Store the result of vehicle(a tuple containing 0.0, 20.0) under 'a'.
        "a": vehicle((0.0, 20.0), width=3.0),
        # Store the result of vehicle(a tuple containing 0.0, 20.0) under 'b'.
        "b": vehicle((0.0, 20.0), width=3.0),
    }
    # Set interface to the result of PerceptionInterface().
    interface = PerceptionInterface()
    # Set first to the result of interface.generate_observations(the text 'ego', ego, states, 0.0).
    first = interface.generate_observations("ego", ego, states, 0.0)
    # Set second to the result of interface.generate_observations(the text 'ego', ego, states, 0.0).
    second = interface.generate_observations("ego", ego, states, 0.0)
    # Require a set built from first equals a set containing the text 'ego', the text 'a', the text 'b'; otherwise
    # raise AssertionError.
    assert set(first) == {"ego", "a", "b"}
    # Require first['a'] at 'visible_fraction' equals 1.0; otherwise raise AssertionError.
    assert first["a"]["visible_fraction"] == 1.0
    # Require first['b'] at 'visible_fraction' equals 1.0; otherwise raise AssertionError.
    assert first["b"]["visible_fraction"] == 1.0
    # Require first equals second; otherwise raise AssertionError.
    assert first == second


# Check all geometric visibility fractions are clamped using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def test_all_geometric_visibility_fractions_are_clamped():
    # Set ego to the result of vehicle(a tuple containing 0.0, 0.0).
    ego = vehicle((0.0, 0.0))
    # Set states to a dictionary containing ego, near, partial, clear.
    states = {
        # Store ego under 'ego'.
        "ego": ego,
        # Store the result of vehicle(a tuple containing 0.0, 10.0) under 'near'.
        "near": vehicle((0.0, 10.0)),
        # Store the result of vehicle(a tuple containing the negative of 2.0, 20.0) under 'partial'.
        "partial": vehicle((-2.0, 20.0), width=4.0),
        # Store the result of vehicle(a tuple containing the negative of 10.0, 20.0) under 'clear'.
        "clear": vehicle((-10.0, 20.0)),
    }
    # Set result to the result of PerceptionInterface(sensor_fov_degrees=90.0).generate_observations(the text
    # 'ego', ego, states, 0.0).
    result = PerceptionInterface(sensor_fov_degrees=90.0).generate_observations(
        # Supply states to PerceptionInterface(sensor_fov_degrees=90.0).generate_observations.
        "ego", ego, states, 0.0
    )
    # Iterate over values from result, binding each item to detection.
    for detection in result.values():
        # Run this branch when detection at 'observation_type' equals the text 'OBJECT_DETECTION'.
        if detection["observation_type"] == "OBJECT_DETECTION":
            # Iterate over a tuple containing the text 'fov_visible_fraction', the text
            # 'occlusion_visible_fraction', the text 'visible_fraction', binding each item to key.
            for key in ("fov_visible_fraction",
                        "occlusion_visible_fraction", "visible_fraction"):
                # Require 0.0 is at most detection at key; is at most 1.0; otherwise raise AssertionError.
                assert 0.0 <= detection[key] <= 1.0


# Check recursive output contains no route or manoeuvre truth using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_recursive_output_contains_no_route_or_manoeuvre_truth():
    # Set forbidden to a set containing the text 'route_id', the text 'ground_truth_route_id', the text
    # 'future_edge_sequence', the text...
    forbidden = {"route_id", "ground_truth_route_id", "future_edge_sequence",
                 "future_trajectory", "intended_manoeuvre", "manoeuvre"}
    # Set target to the result of vehicle(a tuple containing 0.0, 10.0).
    target = vehicle(
        # Supply route_id as the text 'route_n_left'.
        (0.0, 10.0), route_id="route_n_left",
        # Supply ground_truth_route_id as the text 'route_n_left'.
        # Supply intended_manoeuvre as the text 'LEFT'.
        ground_truth_route_id="route_n_left", intended_manoeuvre="LEFT",
        # Store a list containing a tuple containing 0.0, 1.0 under 'future_trajectory'.
        nested={"future_trajectory": [(0.0, 1.0)]},
    )
    # Set result to the result of observe(target).
    result = observe(target)

    # Keys using the inputs and processing steps below.
    # Input value: the supplied value.
    # Output: yield the values produced by the yield statements below.
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    def keys(value):
        # Run this branch when whether value has type dict.
        if isinstance(value, dict):
            # Iterate over key/value pairs from value, binding each item to (key, nested).
            for key, nested in value.items():
                # Yield key to the iterator consumer.
                yield key
                # Yield keys from keys to the iterator consumer.
                yield from keys(nested)
        # Run this branch when whether value has type a tuple containing list, tuple.
        elif isinstance(value, (list, tuple)):
            # Iterate over value, binding each item to nested.
            for nested in value:
                # Yield keys from keys to the iterator consumer.
                yield from keys(nested)

    # Require the result of forbidden.isdisjoint(a set built from keys from keys); otherwise raise AssertionError.
    assert forbidden.isdisjoint(set(keys(result)))


# Check default profile is geometric sensor using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_default_profile_is_geometric_sensor():
    # Require DEFAULT_PERCEPTION_PROFILE equals the text 'GEOMETRIC_SENSOR'; otherwise raise AssertionError.
    assert DEFAULT_PERCEPTION_PROFILE == "GEOMETRIC_SENSOR"
    # Require PerceptionInterface().profile equals the text 'GEOMETRIC_SENSOR'; otherwise raise AssertionError.
    assert PerceptionInterface().profile == "GEOMETRIC_SENSOR"


# Apply pytest.mark.parametrize as a decorator to configure the following definition.
@pytest.mark.parametrize(
    # Supply a tuple containing the text 'field', the text 'value', the text 'message' to pytest.mark.parametrize.
    ("field", "value", "message"),
    # Supply a list containing a tuple containing the text 'speed', the negative of 0.01, the text 'speed must be
    # non-negative', a tuple... to pytest.mark.parametrize.
    [
        # Include a tuple containing the text 'speed', the negative of 0.01, the text 'speed must be non-negative'
        # in this list.
        ("speed", -0.01, "speed must be non-negative"),
        # Include a tuple containing the text 'heading_radians', math.nan, the text 'heading_radians must be a
        # finite number' in this list.
        ("heading_radians", math.nan, "heading_radians must be a finite number"),
        # Include a tuple containing the text 'length', 0.0, the text 'length must be positive' in this list.
        ("length", 0.0, "length must be positive"),
        # Include a tuple containing the text 'width', math.inf, the text 'width must be a finite number' in this
        # list.
        ("width", math.inf, "width must be a finite number"),
    ],
)
# Check invalid geometric ego values raise using the setup, calls, and assertions below.
# Input field: the supplied field.
# Input value: the supplied value.
# Input message: the supplied message.
# Output: no explicit value; normal completion returns None.
def test_invalid_geometric_ego_values_raise(field, value, message):
    # Set ego to the result of vehicle(a tuple containing 0.0, 0.0).
    ego = vehicle((0.0, 0.0))
    # Set ego[field] to value.
    ego[field] = value
    # Enter the result of pytest.raises(ValueError) and run the enclosed operations within that context.
    with pytest.raises(ValueError, match=message):
        # Call PerceptionInterface().generate_observations with the supplied arguments.
        PerceptionInterface().generate_observations(
            # Store ego under 'ego'.
            "ego", ego, {"ego": ego}, 0.0
        )


# Apply pytest.mark.parametrize('field', ['length', 'width']) as a decorator to configure the following
# definition.
@pytest.mark.parametrize("field", ["length", "width"])
# Check geometric ego missing dimension raises using the setup, calls, and assertions below.
# Input field: the supplied field.
# Output: no explicit value; normal completion returns None.
def test_geometric_ego_missing_dimension_raises(field):
    # Set ego to the result of vehicle(a tuple containing 0.0, 0.0).
    ego = vehicle((0.0, 0.0))
    # Delete ego[field] from its containing namespace or collection.
    del ego[field]
    # Enter the result of pytest.raises(ValueError) and run the enclosed operations within that context.
    with pytest.raises(ValueError, match=f"missing mandatory field '{field}'"):
        # Call PerceptionInterface().generate_observations with the supplied arguments.
        PerceptionInterface().generate_observations(
            # Store ego under 'ego'.
            "ego", ego, {"ego": ego}, 0.0
        )


# Apply pytest.mark.parametrize as a decorator to configure the following definition.
@pytest.mark.parametrize(
    # Supply a tuple containing the text 'field', the text 'replacement' to pytest.mark.parametrize.
    ("field", "replacement"),
    # Supply a list containing a tuple containing the text 'position', a tuple containing 1.0, 0.0, a tuple
    # containing the text 'speed',... to pytest.mark.parametrize.
    [
        # Include a tuple containing the text 'position', a tuple containing 1.0, 0.0 in this list.
        ("position", (1.0, 0.0)),
        # Include a tuple containing the text 'speed', 2.0 in this list.
        ("speed", 2.0),
        # Include a tuple containing the text 'heading_radians', 0.1 in this list.
        ("heading_radians", 0.1),
        # Include a tuple containing the text 'length', 5.0 in this list.
        ("length", 5.0),
        # Include a tuple containing the text 'width', 2.5 in this list.
        ("width", 2.5),
    ],
)
# Check inconsistent duplicate ego state raises using the setup, calls, and assertions below.
# Input field: the supplied field.
# Input replacement: the supplied replacement.
# Output: no explicit value; normal completion returns None.
def test_inconsistent_duplicate_ego_state_raises(field, replacement):
    # Set ego to the result of vehicle(a tuple containing 0.0, 0.0).
    ego = vehicle((0.0, 0.0), speed=1.0)
    # Set frame_ego to the result of copy.deepcopy(ego).
    frame_ego = copy.deepcopy(ego)
    # Set frame_ego[field] to replacement.
    frame_ego[field] = replacement
    # Enter the result of pytest.raises(ValueError) and run the enclosed operations within that context.
    with pytest.raises(ValueError, match=f"inconsistent.*{field}"):
        # Call PerceptionInterface().generate_observations with the supplied arguments.
        PerceptionInterface().generate_observations(
            # Store frame_ego under 'ego'.
            "ego", ego, {"ego": frame_ego}, 0.0
        )


# Check consistent duplicate ego state succeeds without mutation using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_consistent_duplicate_ego_state_succeeds_without_mutation():
    # Set ego to the result of vehicle(a tuple containing 2.0, 3.0).
    ego = vehicle((2.0, 3.0), heading=0.25, speed=1.5)
    # Set target to the result of vehicle(a tuple containing 2.0, 13.0).
    target = vehicle((2.0, 13.0))
    # Set states to a dictionary containing ego, target.
    states = {"ego": copy.deepcopy(ego), "target": target}
    # Set original_ego to the result of copy.deepcopy(ego).
    original_ego = copy.deepcopy(ego)
    # Set original_states to the result of copy.deepcopy(states).
    original_states = copy.deepcopy(states)

    # Set result to the result of PerceptionInterface().generate_observations(the text 'ego', ego, states, 4.0).
    result = PerceptionInterface().generate_observations(
        # Supply states to PerceptionInterface().generate_observations.
        "ego", ego, states, 4.0
    )

    # Require result['ego'] at 'position' equals the result of pytest.approx(a tuple containing 2.0, 3.0);
    # otherwise raise AssertionError.
    assert result["ego"]["position"] == pytest.approx((2.0, 3.0))
    # Require ego equals original_ego; otherwise raise AssertionError.
    assert ego == original_ego
    # Require states equals original_states; otherwise raise AssertionError.
    assert states == original_states


# Check missing ego id fails clearly using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_missing_ego_id_fails_clearly():
    # Set ego to the result of vehicle(a tuple containing 0.0, 0.0).
    ego = vehicle((0.0, 0.0))
    # Enter the result of pytest.raises(ValueError) and run the enclosed operations within that context.
    with pytest.raises(ValueError, match="ego.*absent from all_vehicle_data"):
        # Call PerceptionInterface().generate_observations with the supplied arguments.
        PerceptionInterface().generate_observations(
            # Store ego under 'different_vehicle'.
            "ego", ego, {"different_vehicle": ego}, 0.0
        )


# Check config declares all three perception profiles using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_config_declares_all_three_perception_profiles():
    # Require PERCEPTION_PROFILES equals a set containing the text 'IDEAL_BASELINE', the text 'GEOMETRIC_SENSOR',
    # the text 'REALISTIC_OBJECT_SENSOR'; otherwise raise AssertionError.
    assert PERCEPTION_PROFILES == {
        "IDEAL_BASELINE",
        "GEOMETRIC_SENSOR",
        "REALISTIC_OBJECT_SENSOR",
    }


# Check invalid profile name fails clearly using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_invalid_profile_name_fails_clearly():
    # Enter the result of pytest.raises(ValueError) and run the enclosed operations within that context.
    with pytest.raises(ValueError, match="Unsupported perception profile"):
        # Call PerceptionInterface with the supplied arguments.
        PerceptionInterface(profile="UNKNOWN_SENSOR")


# Check realistic profile currently matches geometric visibility using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def test_realistic_profile_currently_matches_geometric_visibility():
    # Set ego to the result of vehicle(a tuple containing 0.0, 0.0).
    ego = vehicle((0.0, 0.0))
    # Set states to a dictionary containing ego, near, partial, hidden, outside_fov.
    states = {
        # Store ego under 'ego'.
        "ego": ego,
        # Store the result of vehicle(a tuple containing 0.0, 10.0) under 'near'.
        "near": vehicle((0.0, 10.0), width=2.0),
        # Store the result of vehicle(a tuple containing the negative of 1.5, 20.0) under 'partial'.
        "partial": vehicle((-1.5, 20.0), width=4.0),
        # Store the result of vehicle(a tuple containing 0.0, 25.0) under 'hidden'.
        "hidden": vehicle((0.0, 25.0), width=1.0),
        # Store the result of vehicle(a tuple containing 20.0, 0.0) under 'outside_fov'.
        "outside_fov": vehicle((20.0, 0.0)),
    }

    # Run using the inputs and processing steps below.
    # Input profile: the supplied profile.
    # Output: a tuple containing detections, diagnostics, summary.
    def run(profile):
        # Set interface to the result of PerceptionInterface().
        interface = PerceptionInterface(
            # Supply profile as profile.
            # Supply sensor_fov_degrees as 90.0.
            profile=profile, sensor_fov_degrees=90.0
        )
        # Set detections to the result of interface.generate_observations(the text 'ego', ego, states, 1.0).
        detections = interface.generate_observations(
            # Supply states to interface.generate_observations.
            "ego", ego, states, 1.0
        )
        # Set diagnostics to the result of interface.get_last_diagnostics(the text 'ego').
        diagnostics = interface.get_last_diagnostics("ego")
        # Set summary to the result of interface.get_last_summary(the text 'ego').
        summary = interface.get_last_summary("ego")
        # Return a tuple containing detections, diagnostics, summary to the caller.
        return detections, diagnostics, summary

    # Set (geometric, geometric_diagnostics, geometric_summary) to the result of run(the text 'GEOMETRIC_SENSOR').
    geometric, geometric_diagnostics, geometric_summary = run(
        "GEOMETRIC_SENSOR"
    )
    # Set (realistic, realistic_diagnostics, realistic_summary) to the result of run(the text
    # 'REALISTIC_OBJECT_SENSOR').
    realistic, realistic_diagnostics, realistic_summary = run(
        "REALISTIC_OBJECT_SENSOR"
    )

    # Require a set built from realistic equals a set built from geometric; otherwise raise AssertionError.
    assert set(realistic) == set(geometric)
    # Iterate over geometric, binding each item to object_id.
    for object_id in geometric:
        # Require realistic[object_id] at 'perception_profile' equals the text 'REALISTIC_OBJECT_SENSOR';
        # otherwise raise AssertionError.
        assert realistic[object_id]["perception_profile"] == (
            "REALISTIC_OBJECT_SENSOR"
        )
        # Require geometric[object_id] at 'perception_profile' equals the text 'GEOMETRIC_SENSOR'; otherwise raise
        # AssertionError.
        assert geometric[object_id]["perception_profile"] == (
            "GEOMETRIC_SENSOR"
        )
        # Iterate over geometric at object_id, binding each item to field.
        for field in geometric[object_id]:
            # Run this branch when field differs from the text 'perception_profile'.
            if field != "perception_profile":
                # Require realistic[object_id] at field equals the result of pytest.approx(geometric[object_id] at
                # field) when whether geometric[object_id] at field has type float, otherwise realistic[object_id]
                # at field equals geometric[object_id] at field; otherwise raise AssertionError.
                assert realistic[object_id][field] == pytest.approx(
                    # Supply geometric[object_id] at field to pytest.approx.
                    geometric[object_id][field]
                # Evaluate whether geometric[object_id] at field has type float as part of the enclosing
                # expression.
                ) if isinstance(geometric[object_id][field], float) else (
                    # Evaluate realistic[object_id] at field equals geometric[object_id] at field as part of the
                    # enclosing expression.
                    realistic[object_id][field] == geometric[object_id][field]
                )

    # Without profile using the inputs and processing steps below.
    # Input items: the supplied items.
    # Output: a list of a dictionary of key mapped to value for (key, value) in key/value pairs from item; retain
    # entries satisfying key differs from the text 'profile' for item in items.
    def without_profile(items):
        # Return a list of a dictionary of key mapped to value for (key, value) in key/value pairs from item;
        # retain entries satisfying key differs from the text 'profile' for item in items to the caller.
        return [
            # Evaluate a dictionary of key mapped to value for (key, value) in key/value pairs from item; retain
            # entries satisfying key differs from the text 'profile' as part of the enclosing expression.
            {key: value for key, value in item.items() if key != "profile"}
            # Evaluate items as part of the enclosing expression.
            for item in items
        ]

    # Require the result of without_profile(realistic_diagnostics) equals the result of
    # without_profile(geometric_diagnostics); otherwise raise AssertionError.
    assert without_profile(realistic_diagnostics) == without_profile(
        # Supply geometric_diagnostics to without_profile.
        geometric_diagnostics
    )
    # Require a dictionary of key mapped to value for (key, value) in key/value pairs from realistic_summary;
    # retain entries satisfying key differs from the text 'profile' equals a dictionary of key mapped to value for
    # (key, value) in key/value pairs from geometric_summary; retain entries satisfying key differs from the text
    # 'profile'; otherwise raise AssertionError.
    assert {
        # Evaluate key/value pairs from realistic_summary as part of the enclosing expression.
        key: value for key, value in realistic_summary.items()
        # Evaluate key differs from the text 'profile' as part of the enclosing expression.
        if key != "profile"
    # Evaluate a dictionary of key mapped to value for (key, value) in key/value pairs from geometric_summary;
    # retain entries satisfying key differs from the text 'profile' as part of the enclosing expression.
    } == {
        # Evaluate key/value pairs from geometric_summary as part of the enclosing expression.
        key: value for key, value in geometric_summary.items()
        # Evaluate key differs from the text 'profile' as part of the enclosing expression.
        if key != "profile"
    }
    # Require realistic_summary at 'profile' equals the text 'REALISTIC_OBJECT_SENSOR'; otherwise raise
    # AssertionError.
    assert realistic_summary["profile"] == "REALISTIC_OBJECT_SENSOR"


# Check realistic profile requires vehicle dimensions using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_realistic_profile_requires_vehicle_dimensions():
    # Set ego to the result of vehicle(a tuple containing 0.0, 0.0).
    ego = vehicle((0.0, 0.0))
    # Set target to a dictionary containing position, speed, heading_radians.
    target = {
        # Store a tuple containing 0.0, 10.0 under 'position'.
        "position": (0.0, 10.0),
        # Store 1.0 under 'speed'.
        "speed": 1.0,
        # Store 0.0 under 'heading_radians'.
        "heading_radians": 0.0,
    }
    # Set interface to the result of PerceptionInterface().
    interface = PerceptionInterface(profile="REALISTIC_OBJECT_SENSOR")
    # Set result to the result of interface.generate_observations(the text 'ego', ego, a dictionary containing
    # ego, target, 0.0).
    result = interface.generate_observations(
        # Store ego under 'ego'.
        # Store target under 'target'.
        "ego", ego, {"ego": ego, "target": target}, 0.0
    )
    # Require the text 'target' does not belong to result; otherwise raise AssertionError.
    assert "target" not in result
    # Require interface.get_last_diagnostics('ego')[0] at 'reason' equals the text 'INVALID_TARGET_STATE';
    # otherwise raise AssertionError.
    assert interface.get_last_diagnostics("ego")[0]["reason"] == (
        "INVALID_TARGET_STATE"
    )
