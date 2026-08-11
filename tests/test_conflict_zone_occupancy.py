"""Deterministic tests for shadow conflict-zone temporal occupancy."""

import math

import pytest

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
            },
            "target": {
                "lane_id": "target_in_0", "lane_position": 100.0,
                "lane_length": 100.0, "length": 2.0, "width": 1.8,
                "speed": target_speed, "route_id": truth,
                "route_index": 99, "ground_truth_route_id": truth,
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
    assert all(item["conflict_zone_id"].startswith("CZ_")
               for item in result["edges"][0]["evaluations"])
