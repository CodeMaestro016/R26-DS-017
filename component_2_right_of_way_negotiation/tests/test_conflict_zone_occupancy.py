"""Deterministic tests for shadow conflict-zone temporal occupancy."""

# Import math for use in this module.
import math
# Import replace from dataclasses for the operations below.
from dataclasses import replace

# Import pytest for use in this module.
import pytest
# Import LineString from shapely.geometry for the operations below.
from shapely.geometry import LineString

# Import MovementPath from conflict.models for the operations below.
from conflict.models import MovementPath
# Import ConflictZoneOccupancyAssessor from conflict.occupancy_assessor for the operations below.
from conflict.occupancy_assessor import ConflictZoneOccupancyAssessor
# Import ConflictGraphManager, ConflictZoneManager, MapPathManager from conflict for the operations below.
from conflict import ConflictGraphManager, ConflictZoneManager, MapPathManager


# Define FakePathManager to group the state and operations declared below.
# Instances expose the attributes and methods implemented in this class.
class FakePathManager:
    # Initialize the instance attributes and collaborators used by the operations below.
    # Output: no explicit value; normal completion returns None.
    def __init__(self):
        # Set self.paths to a dictionary containing EGO, T_OVER, T_SEP.
        self.paths = {
            # Store the result of MovementPath(the text 'EGO', the text 'ego_in_0', the text 'ego_out_0', the text
            # 'STRAIGHT', a tuple...) under 'EGO'.
            "EGO": MovementPath(
                "EGO", "ego_in_0", "ego_out_0", "STRAIGHT",
                # Supply a tuple containing a tuple containing 0.0, 0.0, a tuple containing 20.0, 0.0 to
                # MovementPath.
                ((0.0, 0.0), (20.0, 0.0)),
            ),
            # Store the result of MovementPath(the text 'T_OVER', the text 'target_in_0', the text 'target_out_0',
            # the text 'LEFT', a tuple...) under 'T_OVER'.
            "T_OVER": MovementPath(
                "T_OVER", "target_in_0", "target_out_0", "LEFT",
                # Supply a tuple containing a tuple containing 0.0, 0.0, a tuple containing 20.0, 0.0 to
                # MovementPath.
                ((0.0, 0.0), (20.0, 0.0)),
            ),
            # Store the result of MovementPath(the text 'T_SEP', the text 'target_in_0', the text 'other_out_0',
            # the text 'STRAIGHT', a tuple...) under 'T_SEP'.
            "T_SEP": MovementPath(
                "T_SEP", "target_in_0", "other_out_0", "STRAIGHT",
                # Supply a tuple containing a tuple containing 0.0, 0.0, a tuple containing 20.0, 0.0 to
                # MovementPath.
                ((0.0, 0.0), (20.0, 0.0)),
            ),
        }

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Resolve front bumper path progress using the inputs and processing steps below.
    # Input track: the supplied track.
    # Input path: the path or path object supplied by the caller.
    # Output: return the value selected by the matching return branch below.
    # Processing: select branches using the stated conditions.
    def resolve_front_bumper_path_progress(track, path):
        # Run this branch when the text 'path_progress' belongs to track.
        if "path_progress" in track:
            # Return a tuple containing track at 'path_progress', the text 'INTERNAL_PATH_GEOMETRY', None to the
            # caller.
            return track["path_progress"], "INTERNAL_PATH_GEOMETRY", None
        # Run this branch when track at 'lane_id' equals path.incoming_lane_id.
        if track["lane_id"] == path.incoming_lane_id:
            # Return a tuple containing the negative of track at 'lane_length' minus track at 'lane_position', the
            # text 'INCOMING_LANE', None to the caller.
            return -(track["lane_length"] - track["lane_position"]), (
                "INCOMING_LANE"
            # Supply None to the enclosing expression.
            ), None
        # Return a tuple containing None, None, the text 'INCOMPATIBLE_WITH_OBSERVED_LANE' to the caller.
        return None, None, "INCOMPATIBLE_WITH_OBSERVED_LANE"


# Define FakeZoneManager to group the state and operations declared below.
# Instances expose the attributes and methods implemented in this class.
class FakeZoneManager:
    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Zone record using the inputs and processing steps below.
    # Input ego_path_id: the supplied ego path id.
    # Input ego_width: the supplied ego width.
    # Input target_path_id: the supplied target path id.
    # Input target_width: the supplied target width.
    # Output: return the value selected by the matching return branch below.
    # Processing: select branches using the stated conditions.
    def zone_record(ego_path_id, ego_width, target_path_id, target_width):
        # Delete ego_width, target_width from its containing namespace or collection.
        del ego_width, target_width
        # Run this branch when ego_path_id differs from the text 'EGO'.
        if ego_path_id != "EGO":
            # Return None to the caller.
            return None
        # Set target_start to 11.0 when target_path_id equals the text 'T_OVER', otherwise 14.0.
        target_start = 11.0 if target_path_id == "T_OVER" else 14.0
        # Return a dictionary containing zone_id, conflict_type, first_path_distance_interval,
        # second_path_distance_interval to the caller.
        return {
            # Store formatted text built from the embedded values under 'zone_id'.
            "zone_id": f"CZ_{target_path_id}",
            "conflict_type": "CROSSING",
            # Store a tuple containing 10.0, 10.0 under 'first_path_distance_interval'.
            "first_path_distance_interval": (10.0, 10.0),
            # Store a tuple containing target_start, target_start under 'second_path_distance_interval'.
            "second_path_distance_interval": (target_start, target_start),
        }


# Define LDM to group the state and operations declared below.
# Instances expose the attributes and methods implemented in this class.
class LDM:
    # Set ego_id to the text 'ego'.
    ego_id = "ego"

    # Initialize the instance attributes and collaborators used by the operations below.
    # Input ego_speed: the supplied ego speed.
    # Input target_speed: the supplied target speed.
    # Input truth: the supplied truth.
    # Output: no explicit value; normal completion returns None.
    def __init__(self, ego_speed=1.0, target_speed=1.0, truth=None):
        # Set self.tracks to a dictionary containing ego, target.
        self.tracks = {
            # Store a dictionary containing lane_id, lane_position, lane_length, length, width, speed,
            # max_acceleration_mps2,... under 'ego'.
            "ego": {
                # Store the text 'ego_in_0' under 'lane_id'.
                # Store 100.0 under 'lane_position'.
                "lane_id": "ego_in_0", "lane_position": 100.0,
                # Store 100.0 under 'lane_length'.
                # Store 2.0 under 'length'.
                # Store 1.8 under 'width'.
                "lane_length": 100.0, "length": 2.0, "width": 1.8,
                # Store ego_speed under 'speed'.
                "speed": ego_speed,
                # Store 2.0 under 'max_acceleration_mps2'.
                "max_acceleration_mps2": 2.0,
                # Store 4.5 under 'comfortable_deceleration_mps2'.
                "comfortable_deceleration_mps2": 4.5,
                # Store 7.0 under 'emergency_deceleration_mps2'.
                "emergency_deceleration_mps2": 7.0,
                # Store 13.89 under 'max_speed_mps'.
                "max_speed_mps": 13.89,
            },
            # Store a dictionary containing lane_id, lane_position, lane_length, length, width, speed, route_id,
            # route_index,... under 'target'.
            "target": {
                # Store the text 'target_in_0' under 'lane_id'.
                # Store 100.0 under 'lane_position'.
                "lane_id": "target_in_0", "lane_position": 100.0,
                # Store 100.0 under 'lane_length'.
                # Store 2.0 under 'length'.
                # Store 1.8 under 'width'.
                "lane_length": 100.0, "length": 2.0, "width": 1.8,
                # Store target_speed under 'speed'.
                # Store truth under 'route_id'.
                "speed": target_speed, "route_id": truth,
                # Store 99 under 'route_index'.
                # Store truth under 'ground_truth_route_id'.
                "route_index": 99, "ground_truth_route_id": truth,
                # Store 2.0 under 'max_acceleration_mps2'.
                "max_acceleration_mps2": 2.0,
                # Store 4.5 under 'comfortable_deceleration_mps2'.
                "comfortable_deceleration_mps2": 4.5,
                # Store 7.0 under 'emergency_deceleration_mps2'.
                "emergency_deceleration_mps2": 7.0,
                # Store 13.89 under 'max_speed_mps'.
                "max_speed_mps": 13.89,
            },
        }
        # Set self.current_conflict_graph to a dictionary containing ego_id, edges.
        self.current_conflict_graph = {
            "ego_id": "ego",
            # Store a tuple containing a dictionary containing ego_path_id, target_track_id,
            # target_candidate_paths, prediction_status,... under 'edges'.
            "edges": ({
                "ego_path_id": "EGO", "target_track_id": "target",
                # Store a dictionary containing LEFT, STRAIGHT under 'target_candidate_paths'.
                "target_candidate_paths": {
                    "LEFT": "T_OVER", "STRAIGHT": "T_SEP",
                },
                "prediction_status": "UNKNOWN",
                # Store 0.25 under 'observation_age_seconds'.
                "observation_age_seconds": 0.25,
            },),
        }


# Apply pytest.mark.parametrize as a decorator to configure the following definition.
@pytest.mark.parametrize(
    # Supply a tuple containing the text 'first', the text 'second', the text 'expected' to
    # pytest.mark.parametrize.
    ("first", "second", "expected"),
    # Supply a list containing a tuple containing a tuple containing 10.0, 12.0, a tuple containing 11.0, 13.0, a
    # tuple containing True,... to pytest.mark.parametrize.
    [
        # Include a tuple containing a tuple containing 10.0, 12.0, a tuple containing 11.0, 13.0, a tuple
        # containing True, 1.0, 0.0 in this list.
        ((10.0, 12.0), (11.0, 13.0), (True, 1.0, 0.0)),
        # Include a tuple containing a tuple containing 10.0, 12.0, a tuple containing 14.0, 16.0, a tuple
        # containing False, 0.0, 2.0 in this list.
        ((10.0, 12.0), (14.0, 16.0), (False, 0.0, 2.0)),
        # Include a tuple containing a tuple containing 10.0, 12.0, a tuple containing 12.0, 14.0, a tuple
        # containing True, 0.0, 0.0 in this list.
        ((10.0, 12.0), (12.0, 14.0), (True, 0.0, 0.0)),
    ],
)
# Check closed interval overlap and separation using the setup, calls, and assertions below.
# Input first: the supplied first.
# Input second: the supplied second.
# Input expected: the supplied expected.
# Output: no explicit value; normal completion returns None.
def test_closed_interval_overlap_and_separation(first, second, expected):
    # Set result to the result of ConflictZoneOccupancyAssessor.interval_relationship(first at 0, first at 1,
    # second at 0, second at 1).
    result = ConflictZoneOccupancyAssessor.interval_relationship(
        # Supply second at 0 to ConflictZoneOccupancyAssessor.interval_relationship.
        first[0], first[1], second[0], second[1]
    )
    # Require result equals the result of pytest.approx(expected); otherwise raise AssertionError.
    assert result == pytest.approx(expected)


# Check front bumper distance and vehicle length clearance using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_front_bumper_distance_and_vehicle_length_clearance():
    # Set (incoming, error) to the result of ConflictZoneOccupancyAssessor._incoming_distance(a dictionary
    # containing lane_id, lane_position, lane_length, the text 'in_0').
    incoming, error = ConflictZoneOccupancyAssessor._incoming_distance({
        # Store the text 'in_0' under 'lane_id'.
        # Store 70.0 under 'lane_position'.
        # Store 100.0 under 'lane_length'.
        "lane_id": "in_0", "lane_position": 70.0, "lane_length": 100.0,
    }, "in_0")
    # Require error is the same object as None and incoming equals the result of pytest.approx(30.0); otherwise
    # raise AssertionError.
    assert error is None and incoming == pytest.approx(30.0)
    # Set (timing, error) to the result of ConflictZoneOccupancyAssessor._kinematics(incoming, a tuple containing
    # 5.0, 9.0).
    timing, error = ConflictZoneOccupancyAssessor._kinematics(
        # Supply length as 4.0.
        # Supply speed as 2.0.
        # Supply current_time as 20.0.
        incoming, (5.0, 9.0), length=4.0, speed=2.0, current_time=20.0
    )
    # Require error is the same object as None; otherwise raise AssertionError.
    assert error is None
    # Require timing at 'distance_to_zone_entry_m' equals the result of pytest.approx(35.0); otherwise raise
    # AssertionError.
    assert timing["distance_to_zone_entry_m"] == pytest.approx(35.0)
    # Require timing at 'distance_to_zone_clear_m' equals the result of pytest.approx(43.0); otherwise raise
    # AssertionError.
    assert timing["distance_to_zone_clear_m"] == pytest.approx(43.0)
    # Require timing at 'time_to_entry_s' equals the result of pytest.approx(17.5); otherwise raise
    # AssertionError.
    assert timing["time_to_entry_s"] == pytest.approx(17.5)
    # Require timing at 'time_to_clear_s' equals the result of pytest.approx(21.5); otherwise raise
    # AssertionError.
    assert timing["time_to_clear_s"] == pytest.approx(21.5)
    # Require timing at 'predicted_entry_time_s' equals the result of pytest.approx(37.5); otherwise raise
    # AssertionError.
    assert timing["predicted_entry_time_s"] == pytest.approx(37.5)
    # Require timing at 'predicted_clear_time_s' equals the result of pytest.approx(41.5); otherwise raise
    # AssertionError.
    assert timing["predicted_clear_time_s"] == pytest.approx(41.5)


# Check actual map incoming internal and outgoing path progress using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_actual_map_incoming_internal_and_outgoing_path_progress():
    # Set paths to the result of MapPathManager().
    paths = MapPathManager()
    # Set path to paths.paths at 'N_IN_0_LEFT'.
    path = paths.paths["N_IN_0_LEFT"]

    # Set incoming to a dictionary containing lane_id, lane_position, lane_length.
    incoming = {
        # Store path.incoming_lane_id under 'lane_id'.
        # Store 272.8 under 'lane_position'.
        "lane_id": path.incoming_lane_id, "lane_position": 272.8,
        # Store 292.8 under 'lane_length'.
        "lane_length": 292.8,
    }
    # Set (progress, source, error) to the result of paths.resolve_front_bumper_path_progress(incoming, path).
    progress, source, error = paths.resolve_front_bumper_path_progress(
        # Supply incoming to paths.resolve_front_bumper_path_progress.
        incoming, path
    )
    # Require error is the same object as None and source equals the text 'INCOMING_LANE'; otherwise raise
    # AssertionError.
    assert error is None and source == "INCOMING_LANE"
    # Require progress equals the result of pytest.approx(the negative of 20.0); otherwise raise AssertionError.
    assert progress == pytest.approx(-20.0)

    # Set line to the result of LineString(path.centerline_geometry).
    line = LineString(path.centerline_geometry)
    # Set expected_internal_progress to 5.0.
    expected_internal_progress = 5.0
    # Set point to the result of line.interpolate(expected_internal_progress).
    point = line.interpolate(expected_internal_progress)
    # Set internal to a dictionary containing lane_id, position.
    internal = {
        # Store path.internal_lane_ids at 0 under 'lane_id'.
        "lane_id": path.internal_lane_ids[0],
        # Store a tuple containing point.x, point.y under 'position'.
        "position": (point.x, point.y),
    }
    # Set (progress, source, error) to the result of paths.resolve_front_bumper_path_progress(internal, path).
    progress, source, error = paths.resolve_front_bumper_path_progress(
        # Supply internal to paths.resolve_front_bumper_path_progress.
        internal, path
    )
    # Require error is the same object as None and source equals the text 'INTERNAL_PATH_GEOMETRY'; otherwise
    # raise AssertionError.
    assert error is None and source == "INTERNAL_PATH_GEOMETRY"
    # Require progress equals the result of pytest.approx(expected_internal_progress); otherwise raise
    # AssertionError.
    assert progress == pytest.approx(expected_internal_progress)

    # Set outgoing to a dictionary containing lane_id, lane_position.
    outgoing = {"lane_id": path.outgoing_lane_id, "lane_position": 7.0}
    # Set (progress, source, error) to the result of paths.resolve_front_bumper_path_progress(outgoing, path).
    progress, source, error = paths.resolve_front_bumper_path_progress(
        # Supply outgoing to paths.resolve_front_bumper_path_progress.
        outgoing, path
    )
    # Require error is the same object as None and source equals the text 'OUTGOING_LANE'; otherwise raise
    # AssertionError.
    assert error is None and source == "OUTGOING_LANE"
    # Require progress equals the result of pytest.approx(line.length plus 7.0); otherwise raise AssertionError.
    assert progress == pytest.approx(line.length + 7.0)


# Check actual multi internal lane path projects in one coordinate using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_actual_multi_internal_lane_path_projects_in_one_coordinate():
    # Set paths to the result of MapPathManager().
    paths = MapPathManager()
    # right_before_left compilation currently emits one internal lane per
    # movement, so retain this coordinate-continuity regression with an
    # explicit two-segment path instead of depending on netconvert internals.
    # Set path to the result of replace(paths.paths at 'N_IN_0_LEFT').
    path = replace(
        # Supply paths.paths at 'N_IN_0_LEFT' to replace.
        paths.paths["N_IN_0_LEFT"],
        # Supply internal_lane_ids as a tuple containing the text ':synthetic_first', the text
        # ':synthetic_second'.
        internal_lane_ids=(":synthetic_first", ":synthetic_second"),
    )
    # Require the number of entries in path.internal_lane_ids equals 2; otherwise raise AssertionError.
    assert len(path.internal_lane_ids) == 2
    # Set line to the result of LineString(path.centerline_geometry).
    line = LineString(path.centerline_geometry)
    # Set expected to line.length minus 1.0.
    expected = line.length - 1.0
    # Set point to the result of line.interpolate(expected).
    point = line.interpolate(expected)
    # Set (progress, source, error) to the result of paths.resolve_front_bumper_path_progress(a dictionary
    # containing lane_id, position, path).
    progress, source, error = paths.resolve_front_bumper_path_progress({
        # Store path.internal_lane_ids at -1 under 'lane_id'.
        "lane_id": path.internal_lane_ids[-1],
        # Store a tuple containing point.x, point.y under 'position'.
        "position": (point.x, point.y),
    # Supply path to paths.resolve_front_bumper_path_progress.
    }, path)
    # Require error is the same object as None and source equals the text 'INTERNAL_PATH_GEOMETRY'; otherwise
    # raise AssertionError.
    assert error is None and source == "INTERNAL_PATH_GEOMETRY"
    # Require progress equals the result of pytest.approx(expected); otherwise raise AssertionError.
    assert progress == pytest.approx(expected)


# Check currently occupying and cleared distance states using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_currently_occupying_and_cleared_distance_states():
    # Set (current, state, error) to the result of ConflictZoneOccupancyAssessor._timing_from_progress().
    current, state, error = ConflictZoneOccupancyAssessor._timing_from_progress(
        # Supply progress as 11.0.
        # Supply path_interval as a tuple containing 10.0, 12.0.
        # Supply length as 4.0.
        progress=11.0, path_interval=(10.0, 12.0), length=4.0,
        # Supply speed as 2.0.
        # Supply current_time as 5.0.
        speed=2.0, current_time=5.0,
    )
    # Require error is the same object as None and state equals the text 'CURRENTLY_OCCUPYING'; otherwise raise
    # AssertionError.
    assert error is None and state == "CURRENTLY_OCCUPYING"
    # Require current at 'distance_to_zone_entry_m' equals 0.0; otherwise raise AssertionError.
    assert current["distance_to_zone_entry_m"] == 0.0
    # Require current at 'distance_to_zone_clear_m' equals the result of pytest.approx(5.0); otherwise raise
    # AssertionError.
    assert current["distance_to_zone_clear_m"] == pytest.approx(5.0)
    # Require current at 'time_to_entry_s' equals 0.0; otherwise raise AssertionError.
    assert current["time_to_entry_s"] == 0.0

    # Set (cleared, state, error) to the result of ConflictZoneOccupancyAssessor._timing_from_progress().
    cleared, state, error = ConflictZoneOccupancyAssessor._timing_from_progress(
        # Supply progress as 16.0.
        # Supply path_interval as a tuple containing 10.0, 12.0.
        # Supply length as 4.0.
        progress=16.0, path_interval=(10.0, 12.0), length=4.0,
        # Supply speed as 2.0.
        # Supply current_time as 5.0.
        speed=2.0, current_time=5.0,
    )
    # Require error is the same object as None and state equals the text 'CLEARED_ZONE'; otherwise raise
    # AssertionError.
    assert error is None and state == "CLEARED_ZONE"
    # Require cleared at 'distance_to_zone_entry_m' equals 0.0; otherwise raise AssertionError.
    assert cleared["distance_to_zone_entry_m"] == 0.0
    # Require cleared at 'distance_to_zone_clear_m' equals 0.0; otherwise raise AssertionError.
    assert cleared["distance_to_zone_clear_m"] == 0.0


# Check zero speed current occupancy remains explicit using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_zero_speed_current_occupancy_remains_explicit():
    # Set (timing, state, error) to the result of ConflictZoneOccupancyAssessor._timing_from_progress().
    timing, state, error = ConflictZoneOccupancyAssessor._timing_from_progress(
        # Supply progress as 11.0.
        # Supply path_interval as a tuple containing 10.0, 12.0.
        # Supply length as 4.0.
        progress=11.0, path_interval=(10.0, 12.0), length=4.0,
        # Supply speed as 0.0.
        # Supply current_time as 5.0.
        speed=0.0, current_time=5.0,
    )
    # Require state equals the text 'CURRENTLY_OCCUPYING'; otherwise raise AssertionError.
    assert state == "CURRENTLY_OCCUPYING"
    # Require timing at 'zone_occupancy_state' equals the text 'CURRENTLY_OCCUPYING'; otherwise raise
    # AssertionError.
    assert timing["zone_occupancy_state"] == "CURRENTLY_OCCUPYING"
    # Require timing at 'time_to_entry_s' equals 0.0; otherwise raise AssertionError.
    assert timing["time_to_entry_s"] == 0.0
    # Require 'time_to_clear_s' from timing; use None if absent is the same object as None; otherwise raise
    # AssertionError.
    assert timing.get("time_to_clear_s") is None
    # Require error equals the text 'UNRESOLVED_SPEED'; otherwise raise AssertionError.
    assert error == "UNRESOLVED_SPEED"


# Check earliest reachability from rest is finite using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_earliest_reachability_from_rest_is_finite():
    # Set result to the result of ConflictZoneOccupancyAssessor.earliest_reachable_time().
    result = ConflictZoneOccupancyAssessor.earliest_reachable_time(
        # Supply distance as 8.0.
        # Supply initial_speed as 0.0.
        distance=8.0, initial_speed=0.0,
        # Supply max_acceleration as 2.0.
        # Supply max_speed as 100.0.
        max_acceleration=2.0, max_speed=100.0,
    )
    # Require result equals the result of pytest.approx(the square root of 32.0 divided by 2.0); otherwise raise
    # AssertionError.
    assert result == pytest.approx(math.sqrt(32.0) / 2.0)


# Check earliest reachability before max speed using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_earliest_reachability_before_max_speed():
    # Set result to the result of ConflictZoneOccupancyAssessor.earliest_reachable_time().
    result = ConflictZoneOccupancyAssessor.earliest_reachable_time(
        # Supply distance as 8.0.
        # Supply initial_speed as 2.0.
        distance=8.0, initial_speed=2.0,
        # Supply max_acceleration as 2.0.
        # Supply max_speed as 100.0.
        max_acceleration=2.0, max_speed=100.0,
    )
    # Require result equals the result of pytest.approx(2.0); otherwise raise AssertionError.
    assert result == pytest.approx(2.0)


# Check earliest reachability with acceleration and speed cap phases using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_earliest_reachability_with_acceleration_and_speed_cap_phases():
    # Set result to the result of ConflictZoneOccupancyAssessor.earliest_reachable_time().
    result = ConflictZoneOccupancyAssessor.earliest_reachable_time(
        # Supply distance as 12.0.
        # Supply initial_speed as 0.0.
        distance=12.0, initial_speed=0.0,
        # Supply max_acceleration as 2.0.
        # Supply max_speed as 4.0.
        max_acceleration=2.0, max_speed=4.0,
    )
    # Require result equals the result of pytest.approx(4.0); otherwise raise AssertionError.
    assert result == pytest.approx(4.0)


# Check stopping distance and exact equality feasibility using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_stopping_distance_and_exact_equality_feasibility():
    # Set distance to the result of ConflictZoneOccupancyAssessor.stopping_distance().
    distance = ConflictZoneOccupancyAssessor.stopping_distance(
        # Supply speed as 4.0.
        # Supply comfortable_deceleration as 2.0.
        speed=4.0, comfortable_deceleration=2.0
    )
    # Require distance equals the result of pytest.approx(4.0); otherwise raise AssertionError.
    assert distance == pytest.approx(4.0)
    # Require distance is at most 4.0; otherwise raise AssertionError.
    assert distance <= 4.0
    # Require the negation of distance is at most 3.999; otherwise raise AssertionError.
    assert not distance <= 3.999


# Apply pytest.mark.parametrize('speed', [0.0, -1.0, math.nan, math.inf, None]) as a decorator to configure the
# following definition.
@pytest.mark.parametrize("speed", [0.0, -1.0, math.nan, math.inf, None])
# Check unusable speed is unresolved without substitution using the setup, calls, and assertions below.
# Input speed: the supplied speed.
# Output: no explicit value; normal completion returns None.
# Processing: select branches using the stated conditions.
def test_unusable_speed_is_unresolved_without_substitution(speed):
    # Set (timing, error) to the result of ConflictZoneOccupancyAssessor._kinematics(0.0, a tuple containing 10.0,
    # 12.0).
    timing, error = ConflictZoneOccupancyAssessor._kinematics(
        # Supply length as 4.0.
        # Supply speed as speed.
        # Supply current_time as 0.0.
        0.0, (10.0, 12.0), length=4.0, speed=speed, current_time=0.0
    )
    # Require error belongs to a set containing the text 'UNRESOLVED_SPEED', the text 'UNRESOLVED_VEHICLE_STATE';
    # otherwise raise AssertionError.
    assert error in {"UNRESOLVED_SPEED", "UNRESOLVED_VEHICLE_STATE"}
    # Run this branch when timing is a different object from None.
    if timing is not None:
        # Require the text 'time_to_entry_s' does not belong to timing; otherwise raise AssertionError.
        assert "time_to_entry_s" not in timing


# Check unknown candidate set is aggregated conservatively using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_unknown_candidate_set_is_aggregated_conservatively():
    # Set assessor to the result of ConflictZoneOccupancyAssessor(the result of FakePathManager(), the result of
    # FakeZoneManager()).
    assessor = ConflictZoneOccupancyAssessor(
        # Supply the result of FakePathManager() to ConflictZoneOccupancyAssessor.
        FakePathManager(), FakeZoneManager()
    )
    # Set result to the result of assessor.assess_ldm(the result of LDM(), 0.0).
    result = assessor.assess_ldm(LDM(), 0.0)
    # Set edge to result['edges'] at 0.
    edge = result["edges"][0]
    # Require edge at 'temporal_conflict_possible' is the same object as True; otherwise raise AssertionError.
    assert edge["temporal_conflict_possible"] is True
    # Require edge at 'status' equals the text 'TEMPORAL_CONFLICT'; otherwise raise AssertionError.
    assert edge["status"] == "TEMPORAL_CONFLICT"
    # Require a list of item at 'status' for item in edge at 'evaluations' equals a list containing the text
    # 'TEMPORAL_CONFLICT', the text 'SPATIAL_ONLY'; otherwise raise AssertionError.
    assert [item["status"] for item in edge["evaluations"]] == [
        "TEMPORAL_CONFLICT", "SPATIAL_ONLY"
    ]
    # Require edge['evaluations'][0] at 'overlap_duration_s' equals the result of pytest.approx(1.0); otherwise
    # raise AssertionError.
    assert edge["evaluations"][0]["overlap_duration_s"] == pytest.approx(1.0)
    # Require edge['evaluations'][1] at 'temporal_separation_s' equals the result of pytest.approx(2.0); otherwise
    # raise AssertionError.
    assert edge["evaluations"][1]["temporal_separation_s"] == pytest.approx(2.0)


# Check stopped candidate makes aggregate unresolved using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_stopped_candidate_makes_aggregate_unresolved():
    # Set assessor to the result of ConflictZoneOccupancyAssessor(the result of FakePathManager(), the result of
    # FakeZoneManager()).
    assessor = ConflictZoneOccupancyAssessor(
        # Supply the result of FakePathManager() to ConflictZoneOccupancyAssessor.
        FakePathManager(), FakeZoneManager()
    )
    # Set edge to assessor.assess_ldm(LDM(target_speed=0.0), 0.0)['edges'] at 0.
    edge = assessor.assess_ldm(LDM(target_speed=0.0), 0.0)["edges"][0]
    # Require edge at 'temporal_conflict_possible' is the same object as None; otherwise raise AssertionError.
    assert edge["temporal_conflict_possible"] is None
    # Require edge at 'status' equals the text 'UNRESOLVED_TIMING'; otherwise raise AssertionError.
    assert edge["status"] == "UNRESOLVED_TIMING"
    # Require whether every item is true in a lazy sequence of item at 'status' equals the text 'UNRESOLVED_SPEED'
    # for item in edge at 'evaluations'; otherwise raise AssertionError.
    assert all(item["status"] == "UNRESOLVED_SPEED"
               # Evaluate edge at 'evaluations' as part of the enclosing expression.
               for item in edge["evaluations"])
    # Require whether every item is true in a lazy sequence of item at 'target_earliest_reachable_entry_time_s' is
    # a different object from None for item in edge at 'evaluations'; otherwise raise AssertionError.
    assert all(item["target_earliest_reachable_entry_time_s"] is not None
               # Evaluate edge at 'evaluations' as part of the enclosing expression.
               for item in edge["evaluations"])
    # Require whether every item is true in a lazy sequence of item at 'target_entry_time_upper_bound_status'
    # equals the text 'UNBOUNDED_CAN_STOP' for item in edge at 'evaluations'; otherwise raise AssertionError.
    assert all(item["target_entry_time_upper_bound_status"] == (
        "UNBOUNDED_CAN_STOP"
    # Evaluate edge at 'evaluations' as part of the enclosing expression.
    ) for item in edge["evaluations"])


# Check both stopped while occupying remain current conflict using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_both_stopped_while_occupying_remain_current_conflict():
    # Set assessor to the result of ConflictZoneOccupancyAssessor(the result of FakePathManager(), the result of
    # FakeZoneManager()).
    assessor = ConflictZoneOccupancyAssessor(
        # Supply the result of FakePathManager() to ConflictZoneOccupancyAssessor.
        FakePathManager(), FakeZoneManager()
    )
    # Set ldm to the result of LDM().
    ldm = LDM(ego_speed=0.0, target_speed=0.0)
    # Set ldm.tracks['ego']['path_progress'] to 10.0.
    ldm.tracks["ego"]["path_progress"] = 10.0
    # Set ldm.tracks['target']['path_progress'] to 11.0.
    ldm.tracks["target"]["path_progress"] = 11.0
    # Set edge to assessor.assess_ldm(ldm, 5.0)['edges'] at 0.
    edge = assessor.assess_ldm(ldm, 5.0)["edges"][0]
    # Require edge at 'temporal_conflict_possible' is the same object as True; otherwise raise AssertionError.
    assert edge["temporal_conflict_possible"] is True
    # Require edge at 'status' equals the text 'TEMPORAL_CONFLICT'; otherwise raise AssertionError.
    assert edge["status"] == "TEMPORAL_CONFLICT"
    # Set first to edge['evaluations'] at 0.
    first = edge["evaluations"][0]
    # Require first at 'ego_zone_occupancy_state' equals the text 'CURRENTLY_OCCUPYING'; otherwise raise
    # AssertionError.
    assert first["ego_zone_occupancy_state"] == "CURRENTLY_OCCUPYING"
    # Require first at 'target_zone_occupancy_state' equals the text 'CURRENTLY_OCCUPYING'; otherwise raise
    # AssertionError.
    assert first["target_zone_occupancy_state"] == "CURRENTLY_OCCUPYING"
    # Require first at 'reachability_interpretation' equals the text 'CURRENTLY_OCCUPYING'; otherwise raise
    # AssertionError.
    assert first["reachability_interpretation"] == "CURRENTLY_OCCUPYING"
    # Require first at 'ego_nominal_constant_speed_clear_time_s' is the same object as None; otherwise raise
    # AssertionError.
    assert first["ego_nominal_constant_speed_clear_time_s"] is None


# Check target route truth cannot change temporal result using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_target_route_truth_cannot_change_temporal_result():
    # Set assessor to the result of ConflictZoneOccupancyAssessor(the result of FakePathManager(), the result of
    # FakeZoneManager()).
    assessor = ConflictZoneOccupancyAssessor(
        # Supply the result of FakePathManager() to ConflictZoneOccupancyAssessor.
        FakePathManager(), FakeZoneManager()
    )
    # Set first to the result of assessor.assess_ldm(the result of LDM(), 0.0).
    first = assessor.assess_ldm(LDM(truth="route_target_left"), 0.0)
    # Call assessor.reset with the supplied arguments.
    assessor.reset()
    # Set second to the result of assessor.assess_ldm(the result of LDM(), 0.0).
    second = assessor.assess_ldm(LDM(truth="route_target_right"), 0.0)
    # Require first equals second; otherwise raise AssertionError.
    assert first == second


# Check only graph edges are evaluated and ego results are independent using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_only_graph_edges_are_evaluated_and_ego_results_are_independent():
    # Set assessor to the result of ConflictZoneOccupancyAssessor(the result of FakePathManager(), the result of
    # FakeZoneManager()).
    assessor = ConflictZoneOccupancyAssessor(
        # Supply the result of FakePathManager() to ConflictZoneOccupancyAssessor.
        FakePathManager(), FakeZoneManager()
    )
    # Set first_ldm to the result of LDM().
    first_ldm = LDM()
    # Set first to the result of assessor.assess_ldm(first_ldm, 0.0).
    first = assessor.assess_ldm(first_ldm, 0.0)
    # Set second_ldm to the result of LDM().
    second_ldm = LDM()
    # Set second_ldm.ego_id to the text 'other_ego'.
    second_ldm.ego_id = "other_ego"
    # Set second_ldm.tracks['other_ego'] to the result of second_ldm.tracks.pop(the text 'ego').
    second_ldm.tracks["other_ego"] = second_ldm.tracks.pop("ego")
    # Set second_ldm.current_conflict_graph to a dictionary containing ego_id, edges.
    second_ldm.current_conflict_graph = {"ego_id": "other_ego", "edges": ()}
    # Set second to the result of assessor.assess_ldm(second_ldm, 0.0).
    second = assessor.assess_ldm(second_ldm, 0.0)
    # Require first at 'edges' and second at 'edges' equals an empty tuple; otherwise raise AssertionError.
    assert first["edges"] and second["edges"] == ()
    # Require the result of assessor.get_result(the text 'ego') equals first; otherwise raise AssertionError.
    assert assessor.get_result("ego") == first
    # Call assessor.reset with the supplied arguments.
    assessor.reset("other_ego")
    # Require the result of assessor.get_result(the text 'ego') equals first; otherwise raise AssertionError.
    assert assessor.get_result("ego") == first


# Check actual map graph and zone records integrate using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_actual_map_graph_and_zone_records_integrate():
    # Set paths to the result of MapPathManager().
    paths = MapPathManager()
    # Set zones to the result of ConflictZoneManager(paths).
    zones = ConflictZoneManager(paths)
    # Set graph_manager to the result of ConflictGraphManager(paths, zones).
    graph_manager = ConflictGraphManager(paths, zones)
    # Set assessor to the result of ConflictZoneOccupancyAssessor(paths, zones).
    assessor = ConflictZoneOccupancyAssessor(paths, zones)
    # Set ldm to the result of LDM().
    ldm = LDM()
    # Set ldm.tracks to a dictionary containing ego, target.
    ldm.tracks = {
        # Store a dictionary containing lane_id, lane_position, lane_length, length, width, speed,
        # self_planned_manoeuvre under 'ego'.
        "ego": {
            # Store the text 'w_in_0' under 'lane_id'.
            # Store 282.8 under 'lane_position'.
            "lane_id": "w_in_0", "lane_position": 282.8,
            # Store 292.8 under 'lane_length'.
            # Store 5.0 under 'length'.
            # Store 1.8 under 'width'.
            "lane_length": 292.8, "length": 5.0, "width": 1.8,
            # Store 10.0 under 'speed'.
            # Store the text 'STRAIGHT' under 'self_planned_manoeuvre'.
            "speed": 10.0, "self_planned_manoeuvre": "STRAIGHT",
        },
        # Store a dictionary containing lane_id, lane_position, lane_length, length, width, speed,
        # last_observed_time,... under 'target'.
        "target": {
            # Store the text 'n_in_0' under 'lane_id'.
            # Store 282.8 under 'lane_position'.
            "lane_id": "n_in_0", "lane_position": 282.8,
            # Store 292.8 under 'lane_length'.
            # Store 5.0 under 'length'.
            # Store 1.8 under 'width'.
            "lane_length": 292.8, "length": 5.0, "width": 1.8,
            # Store 10.0 under 'speed'.
            # Store 0.0 under 'last_observed_time'.
            "speed": 10.0, "last_observed_time": 0.0,
            # Store None under 'intention_prediction'.
            "intention_prediction": None,
        },
    }
    # Set ldm.current_conflict_graph to the result of graph_manager.build_local_graph(ldm, 0.0).
    ldm.current_conflict_graph = graph_manager.build_local_graph(ldm, 0.0)
    # Set result to the result of assessor.assess_ldm(ldm, 0.0).
    result = assessor.assess_ldm(ldm, 0.0)
    # Require result['edges'][0] at 'evaluations'; otherwise raise AssertionError.
    assert result["edges"][0]["evaluations"]
    # Set applicable to a list of item for item in result['edges'][0] at 'evaluations'; retain entries satisfying
    # item at 'status' differs from the text 'NO_APPLICABLE_ZONE'.
    applicable = [item for item in result["edges"][0]["evaluations"]
                  # Evaluate item at 'status' differs from the text 'NO_APPLICABLE_ZONE' as part of the enclosing
                  # expression.
                  if item["status"] != "NO_APPLICABLE_ZONE"]
    # Require applicable; otherwise raise AssertionError.
    assert applicable
    # Require whether every item is true in a lazy sequence of the result of
    # item['conflict_zone_id'].startswith(the text 'CZ_') for item in applicable; otherwise raise AssertionError.
    assert all(item["conflict_zone_id"].startswith("CZ_")
               # Evaluate applicable as part of the enclosing expression.
               for item in applicable)
    # Require result['edges'][0] at 'status' equals the text 'TEMPORAL_CONFLICT'; otherwise raise AssertionError.
    assert result["edges"][0]["status"] == "TEMPORAL_CONFLICT"

    # Software fixture: move the target farther back to produce exact temporal
    # separation without introducing an operational threshold.
    # Set ldm.tracks['target']['lane_position'] to 200.0.
    ldm.tracks["target"]["lane_position"] = 200.0
    # Set ldm.current_conflict_graph to the result of graph_manager.build_local_graph(ldm, 0.0).
    ldm.current_conflict_graph = graph_manager.build_local_graph(ldm, 0.0)
    # Set separated to the result of assessor.assess_ldm(ldm, 0.0).
    separated = assessor.assess_ldm(ldm, 0.0)
    # Require separated['edges'][0] at 'status' equals the text 'SPATIAL_ONLY'; otherwise raise AssertionError.
    assert separated["edges"][0]["status"] == "SPATIAL_ONLY"


# Check all map derived coordinated zones have path progress intervals using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_all_map_derived_coordinated_zones_have_path_progress_intervals():
    # Set paths to the result of MapPathManager().
    paths = MapPathManager()
    # Set zones to the result of ConflictZoneManager(paths).
    zones = ConflictZoneManager(paths)
    # Set records to a tuple built from values from zones.zone_geometries.
    records = tuple(zones.zone_geometries.values())
    # Require records; otherwise raise AssertionError.
    assert records
    # Require whether every item is true in a lazy sequence of item at 'first_path_distance_interval' is a
    # different object from None for item in records; otherwise raise AssertionError.
    assert all(item["first_path_distance_interval"] is not None for item in records)
    # Require whether every item is true in a lazy sequence of item at 'second_path_distance_interval' is a
    # different object from None for item in records; otherwise raise AssertionError.
    assert all(item["second_path_distance_interval"] is not None for item in records)


# Check observed internal lane rejects incompatible unknown candidates using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_observed_internal_lane_rejects_incompatible_unknown_candidates():
    # Set paths to the result of MapPathManager().
    paths = MapPathManager()
    # Set zones to the result of ConflictZoneManager(paths).
    zones = ConflictZoneManager(paths)
    # Set assessor to the result of ConflictZoneOccupancyAssessor(paths, zones).
    assessor = ConflictZoneOccupancyAssessor(paths, zones)
    # Set target_path to paths.paths at 'N_IN_0_LEFT'.
    target_path = paths.paths["N_IN_0_LEFT"]
    # Set point to the result of LineString(target_path.centerline_geometry).interpolate(5.0).
    point = LineString(target_path.centerline_geometry).interpolate(5.0)
    # Set ldm to the result of LDM().
    ldm = LDM()
    # Set ldm.tracks to a dictionary containing ego, target.
    ldm.tracks = {
        # Store a dictionary containing lane_id, lane_position, lane_length, position, length, width, speed under
        # 'ego'.
        "ego": {
            # Store the text 'w_in_0' under 'lane_id'.
            # Store 282.8 under 'lane_position'.
            "lane_id": "w_in_0", "lane_position": 282.8,
            # Store 292.8 under 'lane_length'.
            # Store a tuple containing 282.8, 298.4 under 'position'.
            "lane_length": 292.8, "position": (282.8, 298.4),
            # Store 5.0 under 'length'.
            # Store 1.8 under 'width'.
            # Store 10.0 under 'speed'.
            "length": 5.0, "width": 1.8, "speed": 10.0,
        },
        # Store a dictionary containing lane_id, lane_position, lane_length, position, length, width, speed under
        # 'target'.
        "target": {
            # Store target_path.internal_lane_ids at 0 under 'lane_id'.
            "lane_id": target_path.internal_lane_ids[0],
            # Store 0.0 under 'lane_position'.
            # Store 1.0 under 'lane_length'.
            "lane_position": 0.0, "lane_length": 1.0,
            # Store a tuple containing point.x, point.y under 'position'.
            # Store 5.0 under 'length'.
            "position": (point.x, point.y), "length": 5.0,
            # Store 1.8 under 'width'.
            # Store 10.0 under 'speed'.
            "width": 1.8, "speed": 10.0,
        },
    }
    # Set ldm.current_conflict_graph to a dictionary containing edges.
    ldm.current_conflict_graph = {"edges": ({
        "ego_path_id": "W_IN_0_STRAIGHT", "target_track_id": "target",
        # Store a dictionary containing LEFT, RIGHT, STRAIGHT under 'target_candidate_paths'.
        "target_candidate_paths": {
            "LEFT": "N_IN_0_LEFT", "RIGHT": "N_IN_0_RIGHT",
            "STRAIGHT": "N_IN_0_STRAIGHT",
        },
        # Store the text 'UNKNOWN' under 'prediction_status'.
        # Store 0.0 under 'observation_age_seconds'.
        "prediction_status": "UNKNOWN", "observation_age_seconds": 0.0,
    },)}
    # Set edge to assessor.assess_ldm(ldm, 0.0)['edges'] at 0.
    edge = assessor.assess_ldm(ldm, 0.0)["edges"][0]
    # Set statuses to a dictionary of item at 'target_manoeuvre' mapped to item at 'status' for item in edge at
    # 'evaluations'.
    statuses = {item["target_manoeuvre"]: item["status"]
                # Evaluate edge at 'evaluations' as part of the enclosing expression.
                for item in edge["evaluations"]}
    # Require statuses at 'RIGHT' equals the text 'INCOMPATIBLE_WITH_OBSERVED_LANE'; otherwise raise
    # AssertionError.
    assert statuses["RIGHT"] == "INCOMPATIBLE_WITH_OBSERVED_LANE"
    # Require statuses at 'STRAIGHT' equals the text 'INCOMPATIBLE_WITH_OBSERVED_LANE'; otherwise raise
    # AssertionError.
    assert statuses["STRAIGHT"] == "INCOMPATIBLE_WITH_OBSERVED_LANE"
    # Require statuses at 'LEFT' differs from the text 'INCOMPATIBLE_WITH_OBSERVED_LANE'; otherwise raise
    # AssertionError.
    assert statuses["LEFT"] != "INCOMPATIBLE_WITH_OBSERVED_LANE"
    # Require assessor.validation_summary() at 'candidate_paths_rejected_by_observed_lane' equals 2; otherwise
    # raise AssertionError.
    assert assessor.validation_summary()[
        "candidate_paths_rejected_by_observed_lane"
    # Supply 2 to the enclosing expression.
    ] == 2


# Check empty applicable evaluation is unresolved not spatial only using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_empty_applicable_evaluation_is_unresolved_not_spatial_only():
    # Define NoZoneManager to group the state and operations declared below.
    # Instances expose the attributes and methods implemented in this class.
    class NoZoneManager:
        # Apply staticmethod as a decorator to configure the following definition.
        @staticmethod
        # Zone record using the inputs and processing steps below.
        # Input args: the supplied args.
        # Output: None.
        def zone_record(*args):
            # Return None to the caller.
            return None

    # Set assessor to the result of ConflictZoneOccupancyAssessor(the result of FakePathManager(), the result of
    # NoZoneManager()).
    assessor = ConflictZoneOccupancyAssessor(FakePathManager(), NoZoneManager())
    # Set edge to assessor.assess_ldm(LDM(), 0.0)['edges'] at 0.
    edge = assessor.assess_ldm(LDM(), 0.0)["edges"][0]
    # Require edge at 'temporal_conflict_possible' is the same object as None; otherwise raise AssertionError.
    assert edge["temporal_conflict_possible"] is None
    # Require edge at 'status' equals the text 'UNRESOLVED_NO_APPLICABLE_EVALUATION'; otherwise raise
    # AssertionError.
    assert edge["status"] == "UNRESOLVED_NO_APPLICABLE_EVALUATION"
    # Require whether every item is true in a lazy sequence of item at 'status' equals the text
    # 'NO_APPLICABLE_ZONE' for item in edge at 'evaluations'; otherwise raise AssertionError.
    assert all(item["status"] == "NO_APPLICABLE_ZONE"
               # Evaluate edge at 'evaluations' as part of the enclosing expression.
               for item in edge["evaluations"])
