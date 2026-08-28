"""Deterministic tests for shadow conflict-zone temporal occupancy."""

import math
from dataclasses import replace

import pytest
from shapely.geometry import LineString

from conflict.models import MovementPath
from conflict.occupancy_assessor import ConflictZoneOccupancyAssessor
from conflict import ConflictGraphManager, ConflictZoneManager, MapPathManager


class FakePathManager:
    def __init__(self):
        self.paths = {
            "EGO": MovementPath(
                "EGO", "ego_in_0", "ego_out_0", "STRAIGHT",
                ((0.0, 0.0), (20.0, 0.0)),
            ),
            "T_OVER": MovementPath(
                "T_OVER", "target_in_0", "target_out_0", "LEFT",
                ((0.0, 0.0), (20.0, 0.0)),
            ),
            "T_SEP": MovementPath(
                "T_SEP", "target_in_0", "other_out_0", "STRAIGHT",
                ((0.0, 0.0), (20.0, 0.0)),
            ),
        }

    @staticmethod
    def resolve_front_bumper_path_progress(track, path):
        if "path_progress" in track:
            return track["path_progress"], "INTERNAL_PATH_GEOMETRY", None
        if track["lane_id"] == path.incoming_lane_id:
            return -(track["lane_length"] - track["lane_position"]), (
                "INCOMING_LANE"
            ), None
        return None, None, "INCOMPATIBLE_WITH_OBSERVED_LANE"


class FakeZoneManager:
    @staticmethod
    def zone_record(ego_path_id, ego_width, target_path_id, target_width):
        del ego_width, target_width
        if ego_path_id != "EGO":
            return None
        target_start = 11.0 if target_path_id == "T_OVER" else 14.0
        return {
            "zone_id": f"CZ_{target_path_id}",
            "conflict_type": "CROSSING",
            "first_path_distance_interval": (10.0, 10.0),
            "second_path_distance_interval": (target_start, target_start),
        }


class LDM:
    ego_id = "ego"

    def __init__(self, ego_speed=1.0, target_speed=1.0, truth=None):
        self.tracks = {
            "ego": {
                "lane_id": "ego_in_0", "lane_position": 100.0,
                "lane_length": 100.0, "length": 2.0, "width": 1.8,
                "speed": ego_speed,
                "max_acceleration_mps2": 2.0,
                "comfortable_deceleration_mps2": 4.5,
                "emergency_deceleration_mps2": 7.0,
                "max_speed_mps": 13.89,
            },
            "target": {
                "lane_id": "target_in_0", "lane_position": 100.0,
                "lane_length": 100.0, "length": 2.0, "width": 1.8,
                "speed": target_speed, "route_id": truth,
                "route_index": 99, "ground_truth_route_id": truth,
                "max_acceleration_mps2": 2.0,
                "comfortable_deceleration_mps2": 4.5,
                "emergency_deceleration_mps2": 7.0,
                "max_speed_mps": 13.89,
            },
        }
        self.current_conflict_graph = {
            "ego_id": "ego",
            "edges": ({
                "ego_path_id": "EGO", "target_track_id": "target",
                "target_candidate_paths": {
                    "LEFT": "T_OVER", "STRAIGHT": "T_SEP",
                },
                "prediction_status": "UNKNOWN",
                "observation_age_seconds": 0.25,
            },),
        }


@pytest.mark.parametrize(
    ("first", "second", "expected"),
    [
        ((10.0, 12.0), (11.0, 13.0), (True, 1.0, 0.0)),
        ((10.0, 12.0), (14.0, 16.0), (False, 0.0, 2.0)),
        ((10.0, 12.0), (12.0, 14.0), (True, 0.0, 0.0)),
    ],
)
def test_closed_interval_overlap_and_separation(first, second, expected):
    result = ConflictZoneOccupancyAssessor.interval_relationship(
        first[0], first[1], second[0], second[1]
    )
    assert result == pytest.approx(expected)


def test_front_bumper_distance_and_vehicle_length_clearance():
    incoming, error = ConflictZoneOccupancyAssessor._incoming_distance({
        "lane_id": "in_0", "lane_position": 70.0, "lane_length": 100.0,
    }, "in_0")
    assert error is None and incoming == pytest.approx(30.0)
    timing, error = ConflictZoneOccupancyAssessor._kinematics(
        incoming, (5.0, 9.0), length=4.0, speed=2.0, current_time=20.0
    )
    assert error is None
    assert timing["distance_to_zone_entry_m"] == pytest.approx(35.0)
    assert timing["distance_to_zone_clear_m"] == pytest.approx(43.0)
    assert timing["time_to_entry_s"] == pytest.approx(17.5)
    assert timing["time_to_clear_s"] == pytest.approx(21.5)
    assert timing["predicted_entry_time_s"] == pytest.approx(37.5)
    assert timing["predicted_clear_time_s"] == pytest.approx(41.5)


def test_actual_map_incoming_internal_and_outgoing_path_progress():
    paths = MapPathManager()
    path = paths.paths["N_IN_0_LEFT"]

    incoming = {
        "lane_id": path.incoming_lane_id, "lane_position": 272.8,
        "lane_length": 292.8,
    }
    progress, source, error = paths.resolve_front_bumper_path_progress(
        incoming, path
    )
    assert error is None and source == "INCOMING_LANE"
    assert progress == pytest.approx(-20.0)

    line = LineString(path.centerline_geometry)
    expected_internal_progress = 5.0
    point = line.interpolate(expected_internal_progress)
    internal = {
        "lane_id": path.internal_lane_ids[0],
        "position": (point.x, point.y),
    }
    progress, source, error = paths.resolve_front_bumper_path_progress(
        internal, path
    )
    assert error is None and source == "INTERNAL_PATH_GEOMETRY"
    assert progress == pytest.approx(expected_internal_progress)

    outgoing = {"lane_id": path.outgoing_lane_id, "lane_position": 7.0}
    progress, source, error = paths.resolve_front_bumper_path_progress(
        outgoing, path
    )
    assert error is None and source == "OUTGOING_LANE"
    assert progress == pytest.approx(line.length + 7.0)


def test_actual_multi_internal_lane_path_projects_in_one_coordinate():
    paths = MapPathManager()
    # right_before_left compilation currently emits one internal lane per
    # movement, so retain this coordinate-continuity regression with an
    # explicit two-segment path instead of depending on netconvert internals.
    path = replace(
        paths.paths["N_IN_0_LEFT"],
        internal_lane_ids=(":synthetic_first", ":synthetic_second"),
    )
    assert len(path.internal_lane_ids) == 2
    line = LineString(path.centerline_geometry)
    expected = line.length - 1.0
    point = line.interpolate(expected)
    progress, source, error = paths.resolve_front_bumper_path_progress({
        "lane_id": path.internal_lane_ids[-1],
        "position": (point.x, point.y),
    }, path)
    assert error is None and source == "INTERNAL_PATH_GEOMETRY"
    assert progress == pytest.approx(expected)


def test_currently_occupying_and_cleared_distance_states():
    current, state, error = ConflictZoneOccupancyAssessor._timing_from_progress(
        progress=11.0, path_interval=(10.0, 12.0), length=4.0,
        speed=2.0, current_time=5.0,
    )
    assert error is None and state == "CURRENTLY_OCCUPYING"
    assert current["distance_to_zone_entry_m"] == 0.0
    assert current["distance_to_zone_clear_m"] == pytest.approx(5.0)
    assert current["time_to_entry_s"] == 0.0

    cleared, state, error = ConflictZoneOccupancyAssessor._timing_from_progress(
        progress=16.0, path_interval=(10.0, 12.0), length=4.0,
        speed=2.0, current_time=5.0,
    )
    assert error is None and state == "CLEARED_ZONE"
    assert cleared["distance_to_zone_entry_m"] == 0.0
    assert cleared["distance_to_zone_clear_m"] == 0.0


def test_zero_speed_current_occupancy_remains_explicit():
    timing, state, error = ConflictZoneOccupancyAssessor._timing_from_progress(
        progress=11.0, path_interval=(10.0, 12.0), length=4.0,
        speed=0.0, current_time=5.0,
    )
    assert state == "CURRENTLY_OCCUPYING"
    assert timing["zone_occupancy_state"] == "CURRENTLY_OCCUPYING"
    assert timing["time_to_entry_s"] == 0.0
    assert timing.get("time_to_clear_s") is None
    assert error == "UNRESOLVED_SPEED"


def test_earliest_reachability_from_rest_is_finite():
    result = ConflictZoneOccupancyAssessor.earliest_reachable_time(
        distance=8.0, initial_speed=0.0,
        max_acceleration=2.0, max_speed=100.0,
    )
    assert result == pytest.approx(math.sqrt(32.0) / 2.0)


def test_earliest_reachability_before_max_speed():
    result = ConflictZoneOccupancyAssessor.earliest_reachable_time(
        distance=8.0, initial_speed=2.0,
        max_acceleration=2.0, max_speed=100.0,
    )
    assert result == pytest.approx(2.0)


def test_earliest_reachability_with_acceleration_and_speed_cap_phases():
    result = ConflictZoneOccupancyAssessor.earliest_reachable_time(
        distance=12.0, initial_speed=0.0,
        max_acceleration=2.0, max_speed=4.0,
    )
    assert result == pytest.approx(4.0)


def test_stopping_distance_and_exact_equality_feasibility():
    distance = ConflictZoneOccupancyAssessor.stopping_distance(
        speed=4.0, comfortable_deceleration=2.0
    )
    assert distance == pytest.approx(4.0)
    assert distance <= 4.0
    assert not distance <= 3.999


@pytest.mark.parametrize("speed", [0.0, -1.0, math.nan, math.inf, None])
def test_unusable_speed_is_unresolved_without_substitution(speed):
    timing, error = ConflictZoneOccupancyAssessor._kinematics(
        0.0, (10.0, 12.0), length=4.0, speed=speed, current_time=0.0
    )
    assert error in {"UNRESOLVED_SPEED", "UNRESOLVED_VEHICLE_STATE"}
    if timing is not None:
        assert "time_to_entry_s" not in timing


def test_unknown_candidate_set_is_aggregated_conservatively():
    assessor = ConflictZoneOccupancyAssessor(
        FakePathManager(), FakeZoneManager()
    )
    result = assessor.assess_ldm(LDM(), 0.0)
    edge = result["edges"][0]
    assert edge["temporal_conflict_possible"] is True
    assert edge["status"] == "TEMPORAL_CONFLICT"
    assert [item["status"] for item in edge["evaluations"]] == [
        "TEMPORAL_CONFLICT", "SPATIAL_ONLY"
    ]
    assert edge["evaluations"][0]["overlap_duration_s"] == pytest.approx(1.0)
    assert edge["evaluations"][1]["temporal_separation_s"] == pytest.approx(2.0)


def test_stopped_candidate_makes_aggregate_unresolved():
    assessor = ConflictZoneOccupancyAssessor(
        FakePathManager(), FakeZoneManager()
    )
    edge = assessor.assess_ldm(LDM(target_speed=0.0), 0.0)["edges"][0]
    assert edge["temporal_conflict_possible"] is None
    assert edge["status"] == "UNRESOLVED_TIMING"
    assert all(item["status"] == "UNRESOLVED_SPEED"
               for item in edge["evaluations"])
    assert all(item["target_earliest_reachable_entry_time_s"] is not None
               for item in edge["evaluations"])
    assert all(item["target_entry_time_upper_bound_status"] == (
        "UNBOUNDED_CAN_STOP"
    ) for item in edge["evaluations"])


def test_both_stopped_while_occupying_remain_current_conflict():
    assessor = ConflictZoneOccupancyAssessor(
        FakePathManager(), FakeZoneManager()
    )
    ldm = LDM(ego_speed=0.0, target_speed=0.0)
    ldm.tracks["ego"]["path_progress"] = 10.0
    ldm.tracks["target"]["path_progress"] = 11.0
    edge = assessor.assess_ldm(ldm, 5.0)["edges"][0]
    assert edge["temporal_conflict_possible"] is True
    assert edge["status"] == "TEMPORAL_CONFLICT"
    first = edge["evaluations"][0]
    assert first["ego_zone_occupancy_state"] == "CURRENTLY_OCCUPYING"
    assert first["target_zone_occupancy_state"] == "CURRENTLY_OCCUPYING"
    assert first["reachability_interpretation"] == "CURRENTLY_OCCUPYING"
    assert first["ego_nominal_constant_speed_clear_time_s"] is None


def test_target_route_truth_cannot_change_temporal_result():
    assessor = ConflictZoneOccupancyAssessor(
        FakePathManager(), FakeZoneManager()
    )
    first = assessor.assess_ldm(LDM(truth="route_target_left"), 0.0)
    assessor.reset()
    second = assessor.assess_ldm(LDM(truth="route_target_right"), 0.0)
    assert first == second


def test_only_graph_edges_are_evaluated_and_ego_results_are_independent():
    assessor = ConflictZoneOccupancyAssessor(
        FakePathManager(), FakeZoneManager()
    )
    first_ldm = LDM()
    first = assessor.assess_ldm(first_ldm, 0.0)
    second_ldm = LDM()
    second_ldm.ego_id = "other_ego"
    second_ldm.tracks["other_ego"] = second_ldm.tracks.pop("ego")
    second_ldm.current_conflict_graph = {"ego_id": "other_ego", "edges": ()}
    second = assessor.assess_ldm(second_ldm, 0.0)
    assert first["edges"] and second["edges"] == ()
    assert assessor.get_result("ego") == first
    assessor.reset("other_ego")
    assert assessor.get_result("ego") == first


def test_actual_map_graph_and_zone_records_integrate():
    paths = MapPathManager()
    zones = ConflictZoneManager(paths)
    graph_manager = ConflictGraphManager(paths, zones)
    assessor = ConflictZoneOccupancyAssessor(paths, zones)
    ldm = LDM()
    ldm.tracks = {
        "ego": {
            "lane_id": "w_in_0", "lane_position": 282.8,
            "lane_length": 292.8, "length": 5.0, "width": 1.8,
            "speed": 10.0, "self_planned_manoeuvre": "STRAIGHT",
        },
        "target": {
            "lane_id": "n_in_0", "lane_position": 282.8,
            "lane_length": 292.8, "length": 5.0, "width": 1.8,
            "speed": 10.0, "last_observed_time": 0.0,
            "intention_prediction": None,
        },
    }
    ldm.current_conflict_graph = graph_manager.build_local_graph(ldm, 0.0)
    result = assessor.assess_ldm(ldm, 0.0)
    assert result["edges"][0]["evaluations"]
    applicable = [item for item in result["edges"][0]["evaluations"]
                  if item["status"] != "NO_APPLICABLE_ZONE"]
    assert applicable
    assert all(item["conflict_zone_id"].startswith("CZ_")
               for item in applicable)
    assert result["edges"][0]["status"] == "TEMPORAL_CONFLICT"

    # Software fixture: move the target farther back to produce exact temporal
    # separation without introducing an operational threshold.
    ldm.tracks["target"]["lane_position"] = 200.0
    ldm.current_conflict_graph = graph_manager.build_local_graph(ldm, 0.0)
    separated = assessor.assess_ldm(ldm, 0.0)
    assert separated["edges"][0]["status"] == "SPATIAL_ONLY"


def test_all_map_derived_coordinated_zones_have_path_progress_intervals():
    paths = MapPathManager()
    zones = ConflictZoneManager(paths)
    records = tuple(zones.zone_geometries.values())
    assert records
    assert all(item["first_path_distance_interval"] is not None for item in records)
    assert all(item["second_path_distance_interval"] is not None for item in records)


def test_observed_internal_lane_rejects_incompatible_unknown_candidates():
    paths = MapPathManager()
    zones = ConflictZoneManager(paths)
    assessor = ConflictZoneOccupancyAssessor(paths, zones)
    target_path = paths.paths["N_IN_0_LEFT"]
    point = LineString(target_path.centerline_geometry).interpolate(5.0)
    ldm = LDM()
    ldm.tracks = {
        "ego": {
            "lane_id": "w_in_0", "lane_position": 282.8,
            "lane_length": 292.8, "position": (282.8, 298.4),
            "length": 5.0, "width": 1.8, "speed": 10.0,
        },
        "target": {
            "lane_id": target_path.internal_lane_ids[0],
            "lane_position": 0.0, "lane_length": 1.0,
            "position": (point.x, point.y), "length": 5.0,
            "width": 1.8, "speed": 10.0,
        },
    }
    ldm.current_conflict_graph = {"edges": ({
        "ego_path_id": "W_IN_0_STRAIGHT", "target_track_id": "target",
        "target_candidate_paths": {
            "LEFT": "N_IN_0_LEFT", "RIGHT": "N_IN_0_RIGHT",
            "STRAIGHT": "N_IN_0_STRAIGHT",
        },
        "prediction_status": "UNKNOWN", "observation_age_seconds": 0.0,
    },)}
    edge = assessor.assess_ldm(ldm, 0.0)["edges"][0]
    statuses = {item["target_manoeuvre"]: item["status"]
                for item in edge["evaluations"]}
    assert statuses["RIGHT"] == "INCOMPATIBLE_WITH_OBSERVED_LANE"
    assert statuses["STRAIGHT"] == "INCOMPATIBLE_WITH_OBSERVED_LANE"
    assert statuses["LEFT"] != "INCOMPATIBLE_WITH_OBSERVED_LANE"
    assert assessor.validation_summary()[
        "candidate_paths_rejected_by_observed_lane"
    ] == 2


def test_empty_applicable_evaluation_is_unresolved_not_spatial_only():
    class NoZoneManager:
        @staticmethod
        def zone_record(*args):
            return None

    assessor = ConflictZoneOccupancyAssessor(FakePathManager(), NoZoneManager())
    edge = assessor.assess_ldm(LDM(), 0.0)["edges"][0]
    assert edge["temporal_conflict_possible"] is None
    assert edge["status"] == "UNRESOLVED_NO_APPLICABLE_EVALUATION"
    assert all(item["status"] == "NO_APPLICABLE_ZONE"
               for item in edge["evaluations"])
