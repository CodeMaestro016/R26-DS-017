"""Map geometry, leakage, intention, and decentralization contracts."""

import copy
import math

import pytest
from shapely.geometry import LineString

from config import SUMO_NETWORK_FILE
from conflict import ConflictGraphManager, ConflictZoneManager, MapPathManager
from conflict import write_conflict_catalogues
from conflict.conflict_graph_manager import extract_operational_intention
from conflict.models import MovementPath
from observation import ObservationManager


@pytest.fixture(scope="module")
def managers():
    paths = MapPathManager(SUMO_NETWORK_FILE)
    zones = ConflictZoneManager(paths)
    return paths, zones, ConflictGraphManager(paths, zones)


class LDM:
    def __init__(self, ego_id, tracks):
        self.ego_id, self.tracks = ego_id, tracks


def prediction(label=None, probabilities=None):
    if label is None:
        return None
    if label == "UNKNOWN":
        return {"fused_label": "UNKNOWN", "status": "BOTH_UNCERTAIN",
                "primary": None, "secondary": None}
    result = {"label": label, "accepted": True,
              "probabilities": probabilities or {
                  "LEFT": 1.0 if label == "LEFT" else 0.0,
                  "RIGHT": 1.0 if label == "RIGHT" else 0.0,
                  "STRAIGHT": 1.0 if label == "STRAIGHT" else 0.0,
              }}
    return {"fused_label": label, "status": "CONFIRMED_AGREEMENT",
            "primary": result, "secondary": result}


def track(lane, width=1.8, plan=None, intent=None, **extra):
    value = {"lane_id": lane, "width": width, "last_observed_time": 9.5,
             "intention_prediction": intent}
    if plan is not None:
        value["self_planned_manoeuvre"] = plan
    value.update(extra)
    return value


def graph(manager, ego_lane="w_in_0", ego_plan="STRAIGHT",
          target_lane="s_in_0", intent=None, target_extra=None):
    tracks = {
        "ego": track(ego_lane, plan=ego_plan),
        "target": track(target_lane, intent=intent, **(target_extra or {})),
    }
    return manager.build_local_graph(LDM("ego", tracks), 10.0)


def test_actual_map_loads_and_discovers_all_legal_movements(managers):
    paths, _, _ = managers
    assert paths.network_file == str(SUMO_NETWORK_FILE)
    assert paths.incoming_lane_ids == {
        "w_in_0", "e_in_0", "s_in_0", "n_in_0"
    }
    assert len(paths.paths) == 12
    for lane in paths.incoming_lane_ids:
        assert set(paths.feasible_paths(lane)) == {"LEFT", "RIGHT", "STRAIGHT"}
    assert paths.resolve_path("w_in_0", "UTURN") is None
    assert list(paths.paths) == sorted(paths.paths)
    assert len(paths.paths) == len(set(paths.paths))


def test_lane_safe_ids_and_duplicate_registration():
    assert MapPathManager._stable_path_id("w_in_0", "STRAIGHT") == (
        "W_IN_0_STRAIGHT"
    )
    assert MapPathManager._stable_path_id("w_in_1", "STRAIGHT") == (
        "W_IN_1_STRAIGHT"
    )
    first = MovementPath(
        "W_IN_0_STRAIGHT", "w_in_0", "e_out_0", "STRAIGHT",
        ((0.0, 0.0), (1.0, 0.0)),
    )
    duplicate = MovementPath(
        "W_IN_0_STRAIGHT", "w_in_1", "e_out_1", "STRAIGHT",
        ((0.0, 1.0), (1.0, 1.0)),
    )
    discovered = {}
    MapPathManager._register_path(discovered, first)
    with pytest.raises(ValueError, match="Duplicate movement path ID"):
        MapPathManager._register_path(discovered, duplicate)


def test_path_and_zone_ids_are_stable_across_reloads():
    first_paths, second_paths = MapPathManager(), MapPathManager()
    first_zones = ConflictZoneManager(first_paths)
    second_zones = ConflictZoneManager(second_paths)
    assert tuple(first_paths.paths) == tuple(second_paths.paths)
    assert [row["zone_id"] for row in first_zones.catalogue_rows()] == [
        row["zone_id"] for row in second_zones.catalogue_rows()
    ]


def test_validation_catalogues_are_network_derived(managers, tmp_path):
    paths, zones, _ = managers
    path_file, zone_file = write_conflict_catalogues(paths, zones, tmp_path)
    assert path_file.read_text().count("\n") == len(paths.paths) + 1
    assert "W_IN_0_STRAIGHT,w_in_0,e_out_0,STRAIGHT" in path_file.read_text()
    assert "topological_relationship" in zone_file.read_text().splitlines()[0]


def test_path_geometry_is_finite_valid_and_turning(managers):
    paths, _, _ = managers
    for path in paths.paths.values():
        line = LineString(path.centerline_geometry)
        assert line.is_valid and not line.is_empty and line.length > 0.0
        assert all(math.isfinite(value) for point in path.centerline_geometry
                   for value in point)
    assert len(paths.paths["N_IN_0_LEFT"].centerline_geometry) > 3


def test_known_crossing_nonconflict_and_types_use_geometry(managers):
    _, zones, _ = managers
    assert zones.relationship("W_IN_0_STRAIGHT", "S_IN_0_STRAIGHT").conflict_type == "CROSSING"
    assert zones.relationship("W_IN_0_RIGHT", "E_IN_0_RIGHT").conflict_type == "NO_CONFLICT"
    assert zones.relationship("W_IN_0_STRAIGHT", "N_IN_0_LEFT").conflict_type == "MERGING"
    assert zones.relationship("W_IN_0_LEFT", "W_IN_0_STRAIGHT").conflict_type == "DIVERGING"
    assert zones.relationship("W_IN_0_LEFT", "W_IN_0_LEFT").conflict_type == "SAME_PATH"
    assert zones.relationship("W_IN_0_STRAIGHT", "S_IN_0_STRAIGHT").conflict_zone_id
    assert zones.relationship("W_IN_0_LEFT", "W_IN_0_LEFT").conflict_zone_id is None


def test_no_intersection_center_threshold_in_new_package():
    from pathlib import Path
    package_text = "".join(path.read_text() for path in Path("conflict").glob("*.py"))
    assert "INTERSECTION_CENTER" not in package_text


class SyntheticPaths:
    def __init__(self, paths):
        self.paths = {path.path_id: path for path in paths}


def synthetic_path(path_id, incoming, outgoing, points):
    return MovementPath(path_id, incoming, outgoing, "STRAIGHT", tuple(points))


def test_physical_envelopes_detect_crossing_offset_and_separation():
    paths = SyntheticPaths([
        synthetic_path("A", "a_in_0", "a_out_0", ((0, 0), (10, 0))),
        synthetic_path("CROSS", "b_in_0", "b_out_0", ((5, -5), (5, 5))),
        synthetic_path("OFFSET", "c_in_0", "c_out_0", ((0, 1), (10, 1))),
        synthetic_path("FAR", "d_in_0", "d_out_0", ((0, 3), (10, 3))),
    ])
    zones = ConflictZoneManager(paths, catalogue_vehicle_width=1.2)
    assert zones.relationship("A", "CROSS").coordinated_conflict
    # The centrelines are parallel and disjoint, but 0.6 m half-widths overlap.
    assert not zones.lines["A"].intersects(zones.lines["OFFSET"])
    assert zones.relationship("A", "OFFSET").coordinated_conflict
    assert zones.relationship("A", "OFFSET").conflict_type == "CROSSING"
    assert not zones.relationship("A", "FAR").physical_overlap
    assert not zones.relationship("A", "FAR").coordinated_conflict


def test_same_diverging_and_merging_physical_semantics():
    paths = SyntheticPaths([
        synthetic_path("SAME", "x_in_0", "x_out_0", ((0, 0), (10, 0))),
        synthetic_path("DIVERGE", "x_in_0", "y_out_0", ((0, 0), (5, 3))),
        synthetic_path("MERGE", "z_in_0", "x_out_0", ((5, 3), (10, 0))),
    ])
    zones = ConflictZoneManager(paths, catalogue_vehicle_width=1.8)
    same = zones.relationship("SAME", "SAME")
    diverging = zones.relationship("SAME", "DIVERGE")
    merging = zones.relationship("SAME", "MERGE")
    assert same.physical_overlap and not same.coordinated_conflict
    assert same.conflict_zone_id is None
    assert diverging.physical_overlap and not diverging.coordinated_conflict
    assert diverging.conflict_zone_id is None
    assert merging.conflict_type == "MERGING"
    assert merging.physical_overlap and merging.coordinated_conflict
    record = zones.zone_record("SAME", 1.8, "MERGE", 1.8)
    assert record["geometry_type"] in {"Polygon", "MultiPolygon", "GeometryCollection"}
    assert record["first_path_distance_interval"] is not None
    assert record["second_path_distance_interval"] is not None


@pytest.mark.parametrize("label", ["LEFT", "RIGHT", "STRAIGHT"])
def test_accepted_prediction_selects_only_matching_legal_path(managers, label):
    _, _, manager = managers
    result = graph(manager, intent=prediction(label))
    candidates = result["diagnostics"][0]["target_candidate_paths"]
    assert candidates == {label: f"S_IN_0_{label}"}


def test_predicted_conflicting_and_nonconflicting_graph_results(managers):
    _, _, manager = managers
    conflicting = graph(
        manager, target_lane="n_in_0", intent=prediction("STRAIGHT")
    )
    assert len(conflicting["edges"]) == 1
    assert conflicting["diagnostics"][0]["reason"] == (
        "CONFLICTING_PREDICTED_PATH"
    )
    nonconflicting = graph(
        manager, target_lane="n_in_0", intent=prediction("RIGHT")
    )
    assert nonconflicting["edges"] == ()
    assert nonconflicting["diagnostics"][0]["reason"] == (
        "NO_SHARED_CONFLICT_ZONE"
    )


@pytest.mark.parametrize("intent,status", [(prediction("UNKNOWN"), "UNKNOWN"),
                                             (None, "NOT_AVAILABLE")])
def test_unknown_or_missing_prediction_keeps_all_feasible_paths(
        managers, intent, status):
    _, _, manager = managers
    result = graph(manager, intent=intent)
    diagnostic = result["diagnostics"][0]
    assert set(diagnostic["target_candidate_paths"]) == {
        "LEFT", "RIGHT", "STRAIGHT"
    }
    assert diagnostic["prediction_status"] == status
    assert diagnostic["intention_weighted_conflict_probability"] is None
    assert diagnostic["reason"] == "CONFLICTING_UNKNOWN_PATH_SET"


def test_impossible_prediction_falls_back_and_is_diagnostic(managers):
    paths, _, manager = managers
    original = paths.paths_by_lane["s_in_0"].pop("LEFT")
    try:
        result = graph(manager, intent=prediction("LEFT"))
        assert result["diagnostics"][0]["reason"] == "NO_FEASIBLE_PATH"
        assert set(result["diagnostics"][0]["target_candidate_paths"]) == {
            "RIGHT", "STRAIGHT"
        }
    finally:
        paths.paths_by_lane["s_in_0"]["LEFT"] = original


def test_probability_is_exact_conflicting_class_mass(managers):
    _, _, manager = managers
    probabilities = {"LEFT": 0.6, "STRAIGHT": 0.3, "RIGHT": 0.1}
    result = graph(
        manager, target_lane="n_in_0", intent=prediction("LEFT", probabilities)
    )
    # W_STRAIGHT conflicts with N_LEFT and N_STRAIGHT, but not N_RIGHT.
    assert result["diagnostics"][0][
        "intention_weighted_conflict_probability"
    ] == pytest.approx(0.9)


def test_probability_zero_and_one(managers):
    _, _, manager = managers
    zero = graph(manager, target_lane="e_in_0", intent=prediction(
        "RIGHT", {"LEFT": 0.0, "STRAIGHT": 0.0, "RIGHT": 1.0}
    ))
    assert zero["diagnostics"][0]["intention_weighted_conflict_probability"] == 0.0
    all_conflict = graph(manager, target_lane="s_in_0", intent=prediction(
        "LEFT", {"LEFT": 0.5, "STRAIGHT": 0.5, "RIGHT": 0.0}
    ))
    assert all_conflict["diagnostics"][0]["intention_weighted_conflict_probability"] == 1.0


def test_route_truth_fields_cannot_change_graph(managers):
    _, _, manager = managers
    first = graph(manager, intent=prediction("LEFT"), target_extra={
        "route_id": "route_s_right", "route_index": 9,
        "ground_truth_route_id": "route_s_straight",
        "intended_manoeuvre": "RIGHT",
    })
    second = graph(manager, intent=prediction("LEFT"), target_extra={
        "route_id": "route_s_left", "route_index": 0,
        "ground_truth_route_id": "route_s_left",
        "intended_manoeuvre": "STRAIGHT",
    })
    assert first == second


def test_ego_self_intention_changes_only_ego_path(managers):
    _, _, manager = managers
    left = graph(manager, ego_plan="LEFT", intent=prediction("RIGHT"))
    straight = graph(manager, ego_plan="STRAIGHT", intent=prediction("RIGHT"))
    assert left["ego_path_id"] == "W_IN_0_LEFT"
    assert straight["ego_path_id"] == "W_IN_0_STRAIGHT"
    assert left["diagnostics"][0]["target_candidate_paths"] == straight[
        "diagnostics"
    ][0]["target_candidate_paths"]


def test_missing_ego_plan_produces_zero_edge_metrics(managers):
    _, _, manager = managers
    result = graph(manager, ego_plan=None, intent=None)
    assert result["edges"] == ()
    assert result["diagnostics"][0]["reason"] == "MISSING_EGO_PLAN"
    assert result["metrics"]["unknown_intention_conservative_edges"] == 0
    assert result["metrics"]["prediction_unavailable_conservative_edges"] == 0


def test_self_navigation_adapter_exposes_only_requested_ego_intention():
    ego = {"route_id": "route_w_left"}
    target = {"route_id": "route_s_right"}
    assert ObservationManager.get_ego_planned_manoeuvre("ego", ego) == "LEFT"
    # Supplying ego state never requires or reads the surrounding state.
    assert "self_planned_manoeuvre" not in target


def test_per_ego_graphs_are_independent_and_reset_independently(managers):
    paths, zones, _ = managers
    manager = ConflictGraphManager(paths, zones)
    one = manager.build_local_graph(LDM("AV_1", {
        "AV_1": track("w_in_0", plan="STRAIGHT"),
        "target": track("s_in_0", intent=None),
    }), 1.0)
    two = manager.build_local_graph(LDM("AV_2", {
        "AV_2": track("e_in_0", plan="RIGHT"),
    }), 1.0)
    assert one != two
    modified = copy.deepcopy(one)
    modified["nodes"] = ()
    assert manager.get_graph("AV_1")["nodes"] != ()
    manager.reset("AV_1")
    assert manager.get_graph("AV_1") is None
    assert manager.get_graph("AV_2") is not None


def test_graph_changes_report_prediction_and_edge_transitions(managers):
    paths, zones, _ = managers
    manager = ConflictGraphManager(paths, zones)
    ldm = LDM("ego", {
        "ego": track("w_in_0", plan="STRAIGHT"),
        "target": track("n_in_0", intent=None),
    })
    first = manager.build_local_graph(ldm, 1.0)
    assert any(item["change_type"] == "EDGE_ADDED" for item in first["changes"])
    ldm.tracks["target"]["intention_prediction"] = prediction("RIGHT")
    second = manager.build_local_graph(ldm, 2.0)
    change_types = {item["change_type"] for item in second["changes"]}
    assert "EDGE_REMOVED" in change_types
    assert "PREDICTION_STATUS_CHANGED" in change_types
    assert "CANDIDATE_PATHS_CHANGED" in change_types


def test_graph_paths_persist_and_narrow_from_observed_internal_lanes(managers):
    paths, zones, _ = managers
    manager = ConflictGraphManager(paths, zones)
    ldm = LDM("ego", {
        "ego": track("w_in_0", plan="STRAIGHT"),
        "target": track("n_in_0", intent=None),
    })
    initial = manager.build_local_graph(ldm, 0.0)
    assert initial["ego_path_id"] == "W_IN_0_STRAIGHT"

    ego_path = paths.paths["W_IN_0_STRAIGHT"]
    target_path = paths.paths["N_IN_0_STRAIGHT"]
    ldm.tracks["ego"].update(
        lane_id=ego_path.internal_lane_ids[0], position=(300.0, 298.4)
    )
    ldm.tracks["target"].update(
        lane_id=target_path.internal_lane_ids[0], position=(298.4, 300.0)
    )
    current = manager.build_local_graph(ldm, 1.0)
    assert current["ego_path_id"] == "W_IN_0_STRAIGHT"
    candidates = current["diagnostics"][0]["target_candidate_paths"]
    assert candidates == {"STRAIGHT": "N_IN_0_STRAIGHT"}


def test_adapter_consumes_fused_contract_not_stage_reinterpretation():
    value = prediction("LEFT")
    value["primary"]["label"] = "RIGHT"
    assert extract_operational_intention({"intention_prediction": value})[0] == "LEFT"
