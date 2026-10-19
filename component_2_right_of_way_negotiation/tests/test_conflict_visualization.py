"""Focused tests for spatial/temporal dashboard evidence."""

import inspect
import json
from types import SimpleNamespace

from shapely.geometry import (
    GeometryCollection, LineString, MultiPolygon, Point, Polygon,
)

from debug_conflict_evidence import build_conflict_evidence, geometry_mapping


def diagnostic(probability=None):
    return {
        "ego_id": "AV_0", "target_track_id": "AV_1",
        "ego_manoeuvre": "STRAIGHT", "ego_path_id": "EGO_STRAIGHT",
        "target_prediction": "UNKNOWN", "prediction_status": "UNKNOWN",
        "target_candidate_paths": {"LEFT": "TARGET_LEFT"},
        "spatially_conflicting_candidate_paths": {
            "LEFT": "TARGET_LEFT", "STRAIGHT": "TARGET_STRAIGHT"
        },
        "conflicting_manoeuvres": ["LEFT", "STRAIGHT"],
        "shared_conflict_zone_ids": ["CZ_001"],
        "conflict_types": ["CROSSING"],
        "spatial_conflict_possible": True,
        "intention_weighted_conflict_probability": probability,
        "observation_age_seconds": 0.04,
        "reason": "CONFLICTING_UNKNOWN_PATH_SET",
        "ground_truth_route_id": "must_not_leak",
    }


def temporal(status="TEMPORAL_CONFLICT", possible=True):
    return {"ego_id": "AV_0", "timestamp": 2.0, "edges": [{
        "target_id": "AV_1", "status": status,
        "temporal_conflict_possible": possible,
        "evaluations": [{
            "target_path_id": "TARGET_LEFT", "status": status,
            "ego_stopping_distance_m": 4.2,
            "target_stopping_distance_m": 5.1,
            "route_index": 9,
        }],
    }]}


class FakeLDM:
    ego_id = "AV_0"
    in_approach_zone = True

    def __init__(self, graph, assessment):
        self.graph = graph
        self.assessment = assessment
        self.tracks = {
            "AV_0": {"width": 1.8},
            "AV_1": {"width": 2.1},
        }

    def get_current_conflict_graph(self):
        return self.graph

    def get_current_temporal_assessment(self):
        return self.assessment


class FakeZoneManager:
    def zone_record(self, *_args):
        return {
            "zone_id": "CZ_001", "conflict_type": "CROSSING",
            "geometry_type": "Polygon",
            "geometry": Polygon(((0, 0), (1, 0), (1, 1), (0, 1))),
            "first_path_distance_interval": (2.0, 3.0),
            "second_path_distance_interval": (4.0, 5.0),
        }


def fixture(probability=None, temporal_status="TEMPORAL_CONFLICT",
            possible=True):
    row = diagnostic(probability)
    graph = {
        "ego_id": "AV_0", "nodes": ["AV_0", "AV_1"],
        "edges": [dict(row)], "diagnostics": [dict(row)],
        "metrics": {
            "locally_observed_targets": 1,
            "targets_evaluated_for_conflict": 1,
            "spatial_conflict_edges": 1,
            "non_conflicting_targets_filtered": 0,
            "unknown_intention_conservative_edges": 1,
            "prediction_unavailable_conservative_edges": 0,
            "conflict_zones": 1,
        },
    }
    ldm = FakeLDM(graph, temporal(temporal_status, possible))
    manager = SimpleNamespace(ldms={"AV_0": ldm})
    paths = {
        "EGO_STRAIGHT": SimpleNamespace(
            centerline_geometry=((0, 0), (2, 2))),
        "TARGET_LEFT": SimpleNamespace(
            centerline_geometry=((0, 2), (2, 0))),
        "TARGET_STRAIGHT": SimpleNamespace(
            centerline_geometry=((1, 2), (1, 0))),
    }
    return manager, SimpleNamespace(paths=paths), FakeZoneManager(), ldm


def test_graph_and_temporal_evidence_are_defensive_and_route_truth_clean():
    manager, paths, zones, ldm = fixture()
    result = build_conflict_evidence(manager, paths, zones)
    result["local_conflict_graphs"]["AV_0"]["metrics"][
        "spatial_conflict_edges"] = 999
    result["temporal_conflict_assessments"]["AV_0"]["edges"][0][
        "status"] = "CHANGED"
    assert ldm.graph["metrics"]["spatial_conflict_edges"] == 1
    assert ldm.assessment["edges"][0]["status"] == "TEMPORAL_CONFLICT"
    encoded = json.dumps(result, allow_nan=False)
    for forbidden in ("route_id", "route_index", "ground_truth_route_id",
                      "must_not_leak"):
        assert forbidden not in encoded


def test_candidate_and_spatially_conflicting_paths_remain_distinct():
    manager, paths, zones, _ = fixture()
    graph = build_conflict_evidence(manager, paths, zones)[
        "local_conflict_graphs"]["AV_0"]
    row = graph["diagnostics"][0]
    assert row["target_candidate_paths"] == {"LEFT": "TARGET_LEFT"}
    assert set(row["spatially_conflicting_candidate_paths"]) == {
        "LEFT", "STRAIGHT"
    }


def test_metrics_and_temporal_classifications_match_authoritative_records():
    for status, possible, key in (
        ("TEMPORAL_CONFLICT", True, "temporal_conflict_edges"),
        ("SPATIAL_ONLY", False, "spatial_only_edges"),
        ("UNRESOLVED_TIMING", None, "unresolved_temporal_edges"),
    ):
        manager, paths, zones, ldm = fixture(
            temporal_status=status, possible=possible
        )
        result = build_conflict_evidence(manager, paths, zones)
        kpis = result["conflict_kpis_by_ego"]["AV_0"]
        assert kpis["spatial_conflict_edges"] == ldm.graph["metrics"][
            "spatial_conflict_edges"]
        assert kpis[key] == 1
        if status.startswith("UNRESOLVED"):
            assert possible is None


def test_geometry_supports_polygon_multipolygon_and_geometry_collection():
    first = Polygon(((0, 0), (1, 0), (1, 1), (0, 1)))
    second = Polygon(((2, 0), (3, 0), (3, 1), (2, 1)))
    geometries = (
        first,
        MultiPolygon((first, second)),
        GeometryCollection((first, LineString(((0, 0), (2, 2))), Point(1, 1))),
    )
    assert [geometry_mapping(item)["type"] for item in geometries] == [
        "Polygon", "MultiPolygon", "GeometryCollection"
    ]
    json.dumps([geometry_mapping(item) for item in geometries], allow_nan=False)


def test_geometry_uses_actual_track_widths_and_preserves_zero_probability():
    manager, paths, zones, _ = fixture(probability=0.0)
    result = build_conflict_evidence(manager, paths, zones)
    geometry = result["conflict_geometry_by_ego"]["AV_0"]["AV_1"]
    assert geometry["ego_width_m"] == 1.8
    assert geometry["target_width_m"] == 2.1
    row = result["local_conflict_graphs"]["AV_0"]["diagnostics"][0]
    assert row["intention_weighted_conflict_probability"] == 0.0
    manager, paths, zones, _ = fixture(probability=None)
    result = build_conflict_evidence(manager, paths, zones)
    assert result["local_conflict_graphs"]["AV_0"]["diagnostics"][0][
        "intention_weighted_conflict_probability"] is None


def test_stopping_diagnostics_are_copied_not_recalculated():
    manager, paths, zones, _ = fixture()
    evaluation = build_conflict_evidence(manager, paths, zones)[
        "temporal_conflict_assessments"]["AV_0"]["edges"][0]["evaluations"][0]
    assert evaluation["ego_stopping_distance_m"] == 4.2
    assert evaluation["target_stopping_distance_m"] == 5.1


def test_main_has_one_same_step_write_after_spatial_and_temporal_calls():
    import main
    source = inspect.getsource(main.main)
    graph_index = source.index("conflict_graph_manager.build_local_graph")
    temporal_index = source.index("occupancy_assessor.assess_ldm")
    evidence_index = source.index("evidence_snapshot = build_evidence_snapshot")
    write_index = source.index("evidence_writer.write(evidence_snapshot)")
    assert graph_index < temporal_index < evidence_index < write_index
    assert source.count("evidence_writer.write(evidence_snapshot)") == 1
