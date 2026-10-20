"""Focused tests for spatial/temporal dashboard evidence."""

# Import inspect for use in this module.
import inspect
# Import json for use in this module.
import json
# Import SimpleNamespace from types for the operations below.
from types import SimpleNamespace

# Import GeometryCollection, LineString, MultiPolygon, Point, Polygon from shapely.geometry for the operations
# below.
from shapely.geometry import (
    GeometryCollection, LineString, MultiPolygon, Point, Polygon,
)

# Import build_conflict_evidence, geometry_mapping from debug_conflict_evidence for the operations below.
from debug_conflict_evidence import build_conflict_evidence, geometry_mapping


# Diagnostic using the inputs and processing steps below.
# Input probability: the supplied probability.
# Output: a dictionary containing ego_id, target_track_id, ego_manoeuvre, ego_path_id, target_prediction,...
def diagnostic(probability=None):
    # Return a dictionary containing ego_id, target_track_id, ego_manoeuvre, ego_path_id, target_prediction,... to
    # the caller.
    return {
        "ego_id": "AV_0", "target_track_id": "AV_1",
        "ego_manoeuvre": "STRAIGHT", "ego_path_id": "EGO_STRAIGHT",
        "target_prediction": "UNKNOWN", "prediction_status": "UNKNOWN",
        # Store a dictionary containing LEFT under 'target_candidate_paths'.
        # Store the text 'TARGET_LEFT' under 'LEFT'.
        "target_candidate_paths": {"LEFT": "TARGET_LEFT"},
        # Store a dictionary containing LEFT, STRAIGHT under 'spatially_conflicting_candidate_paths'.
        "spatially_conflicting_candidate_paths": {
            "LEFT": "TARGET_LEFT", "STRAIGHT": "TARGET_STRAIGHT"
        },
        # Store a list containing the text 'LEFT', the text 'STRAIGHT' under 'conflicting_manoeuvres'.
        "conflicting_manoeuvres": ["LEFT", "STRAIGHT"],
        # Store a list containing the text 'CZ_001' under 'shared_conflict_zone_ids'.
        "shared_conflict_zone_ids": ["CZ_001"],
        # Store a list containing the text 'CROSSING' under 'conflict_types'.
        "conflict_types": ["CROSSING"],
        # Store True under 'spatial_conflict_possible'.
        "spatial_conflict_possible": True,
        # Store probability under 'intention_weighted_conflict_probability'.
        "intention_weighted_conflict_probability": probability,
        # Store 0.04 under 'observation_age_seconds'.
        "observation_age_seconds": 0.04,
        "reason": "CONFLICTING_UNKNOWN_PATH_SET",
        "ground_truth_route_id": "must_not_leak",
    }


# Temporal using the inputs and processing steps below.
# Input status: the supplied status.
# Input possible: the supplied possible.
# Output: a dictionary containing ego_id, timestamp, edges.
def temporal(status="TEMPORAL_CONFLICT", possible=True):
    # Return a dictionary containing ego_id, timestamp, edges to the caller.
    return {"ego_id": "AV_0", "timestamp": 2.0, "edges": [{
        # Store the text 'AV_1' under 'target_id'.
        # Store status under 'status'.
        "target_id": "AV_1", "status": status,
        # Store possible under 'temporal_conflict_possible'.
        "temporal_conflict_possible": possible,
        # Store a list containing a dictionary containing target_path_id, status, ego_stopping_distance_m,
        # target_stopping_distance_m,... under 'evaluations'.
        "evaluations": [{
            # Store the text 'TARGET_LEFT' under 'target_path_id'.
            # Store status under 'status'.
            "target_path_id": "TARGET_LEFT", "status": status,
            # Store 4.2 under 'ego_stopping_distance_m'.
            "ego_stopping_distance_m": 4.2,
            # Store 5.1 under 'target_stopping_distance_m'.
            "target_stopping_distance_m": 5.1,
            # Store 9 under 'route_index'.
            "route_index": 9,
        }],
    }]}


# Define FakeLDM to group the state and operations declared below.
# Instances expose the attributes and methods implemented in this class.
class FakeLDM:
    # Set ego_id to the text 'AV_0'.
    ego_id = "AV_0"
    # Set in_approach_zone to True.
    in_approach_zone = True

    # Initialize the instance attributes and collaborators used by the operations below.
    # Input graph: the supplied graph.
    # Input assessment: the supplied assessment.
    # Output: no explicit value; normal completion returns None.
    def __init__(self, graph, assessment):
        # Set self.graph to graph.
        self.graph = graph
        # Set self.assessment to assessment.
        self.assessment = assessment
        # Set self.tracks to a dictionary containing AV_0, AV_1.
        self.tracks = {
            # Store a dictionary containing width under 'AV_0'.
            # Store 1.8 under 'width'.
            "AV_0": {"width": 1.8},
            # Store a dictionary containing width under 'AV_1'.
            # Store 2.1 under 'width'.
            "AV_1": {"width": 2.1},
        }

    # Get current conflict graph using the inputs and processing steps below.
    # Output: self.graph.
    def get_current_conflict_graph(self):
        # Return self.graph to the caller.
        return self.graph

    # Get current temporal assessment using the inputs and processing steps below.
    # Output: self.assessment.
    def get_current_temporal_assessment(self):
        # Return self.assessment to the caller.
        return self.assessment


# Define FakeZoneManager to group the state and operations declared below.
# Instances expose the attributes and methods implemented in this class.
class FakeZoneManager:
    # Zone record using the inputs and processing steps below.
    # Input _args: the supplied args.
    # Output: a dictionary containing zone_id, conflict_type, geometry_type, geometry,
    # first_path_distance_interval,...
    def zone_record(self, *_args):
        # Return a dictionary containing zone_id, conflict_type, geometry_type, geometry,
        # first_path_distance_interval,... to the caller.
        return {
            "zone_id": "CZ_001", "conflict_type": "CROSSING",
            "geometry_type": "Polygon",
            # Store the result of Polygon(a tuple containing a tuple containing 0, 0, a tuple containing 1, 0, a
            # tuple containing 1, 1, a...) under 'geometry'.
            "geometry": Polygon(((0, 0), (1, 0), (1, 1), (0, 1))),
            # Store a tuple containing 2.0, 3.0 under 'first_path_distance_interval'.
            "first_path_distance_interval": (2.0, 3.0),
            # Store a tuple containing 4.0, 5.0 under 'second_path_distance_interval'.
            "second_path_distance_interval": (4.0, 5.0),
        }


# Fixture using the inputs and processing steps below.
# Input probability: the supplied probability.
# Input temporal_status: the supplied temporal status.
# Input possible: the supplied possible.
# Output: a tuple containing manager, the result of SimpleNamespace(), the result of FakeZoneManager(), ldm.
def fixture(probability=None, temporal_status="TEMPORAL_CONFLICT",
            # Declare possible as input parameter.
            possible=True):
    # Set row to the result of diagnostic(probability).
    row = diagnostic(probability)
    # Set graph to a dictionary containing ego_id, nodes, edges, diagnostics, metrics.
    graph = {
        # Store the text 'AV_0' under 'ego_id'.
        # Store a list containing the text 'AV_0', the text 'AV_1' under 'nodes'.
        "ego_id": "AV_0", "nodes": ["AV_0", "AV_1"],
        # Store a list containing a dictionary built from row under 'edges'.
        # Store a list containing a dictionary built from row under 'diagnostics'.
        "edges": [dict(row)], "diagnostics": [dict(row)],
        # Store a dictionary containing locally_observed_targets, targets_evaluated_for_conflict,
        # spatial_conflict_edges,... under 'metrics'.
        "metrics": {
            # Store 1 under 'locally_observed_targets'.
            "locally_observed_targets": 1,
            # Store 1 under 'targets_evaluated_for_conflict'.
            "targets_evaluated_for_conflict": 1,
            # Store 1 under 'spatial_conflict_edges'.
            "spatial_conflict_edges": 1,
            # Store 0 under 'non_conflicting_targets_filtered'.
            "non_conflicting_targets_filtered": 0,
            # Store 1 under 'unknown_intention_conservative_edges'.
            "unknown_intention_conservative_edges": 1,
            # Store 0 under 'prediction_unavailable_conservative_edges'.
            "prediction_unavailable_conservative_edges": 0,
            # Store 1 under 'conflict_zones'.
            "conflict_zones": 1,
        },
    }
    # Set ldm to the result of FakeLDM(graph, the result of temporal(temporal_status, possible)).
    ldm = FakeLDM(graph, temporal(temporal_status, possible))
    # Set manager to the result of SimpleNamespace().
    manager = SimpleNamespace(ldms={"AV_0": ldm})
    # Set paths to a dictionary containing EGO_STRAIGHT, TARGET_LEFT, TARGET_STRAIGHT.
    paths = {
        # Store the result of SimpleNamespace() under 'EGO_STRAIGHT'.
        "EGO_STRAIGHT": SimpleNamespace(
            # Supply centerline_geometry as a tuple containing a tuple containing 0, 0, a tuple containing 2, 2.
            centerline_geometry=((0, 0), (2, 2))),
        # Store the result of SimpleNamespace() under 'TARGET_LEFT'.
        "TARGET_LEFT": SimpleNamespace(
            # Supply centerline_geometry as a tuple containing a tuple containing 0, 2, a tuple containing 2, 0.
            centerline_geometry=((0, 2), (2, 0))),
        # Store the result of SimpleNamespace() under 'TARGET_STRAIGHT'.
        "TARGET_STRAIGHT": SimpleNamespace(
            # Supply centerline_geometry as a tuple containing a tuple containing 1, 2, a tuple containing 1, 0.
            centerline_geometry=((1, 2), (1, 0))),
    }
    # Return a tuple containing manager, the result of SimpleNamespace(), the result of FakeZoneManager(), ldm to
    # the caller.
    return manager, SimpleNamespace(paths=paths), FakeZoneManager(), ldm


# Check graph and temporal evidence are defensive and route truth clean using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def test_graph_and_temporal_evidence_are_defensive_and_route_truth_clean():
    # Set (manager, paths, zones, ldm) to the result of fixture().
    manager, paths, zones, ldm = fixture()
    # Set result to the result of build_conflict_evidence(manager, paths, zones).
    result = build_conflict_evidence(manager, paths, zones)
    # Set result['local_conflict_graphs']['AV_0']['metrics']['spatial_conflict_edges'] to 999.
    result["local_conflict_graphs"]["AV_0"]["metrics"][
        # Supply 999 to the enclosing expression.
        "spatial_conflict_edges"] = 999
    # Set result['temporal_conflict_assessments']['AV_0']['edges'][0]['status'] to the text 'CHANGED'.
    result["temporal_conflict_assessments"]["AV_0"]["edges"][0][
        # Supply the text 'CHANGED' to the enclosing expression.
        "status"] = "CHANGED"
    # Require ldm.graph['metrics'] at 'spatial_conflict_edges' equals 1; otherwise raise AssertionError.
    assert ldm.graph["metrics"]["spatial_conflict_edges"] == 1
    # Require ldm.assessment['edges'][0] at 'status' equals the text 'TEMPORAL_CONFLICT'; otherwise raise
    # AssertionError.
    assert ldm.assessment["edges"][0]["status"] == "TEMPORAL_CONFLICT"
    # Set encoded to the serialized data produced by json.dumps.
    encoded = json.dumps(result, allow_nan=False)
    # Iterate over a tuple containing the text 'route_id', the text 'route_index', the text
    # 'ground_truth_route_id', the text 'must_not_leak', binding each item to forbidden.
    for forbidden in ("route_id", "route_index", "ground_truth_route_id",
                      "must_not_leak"):
        # Require forbidden does not belong to encoded; otherwise raise AssertionError.
        assert forbidden not in encoded


# Check candidate and spatially conflicting paths remain distinct using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_candidate_and_spatially_conflicting_paths_remain_distinct():
    # Set (manager, paths, zones, _) to the result of fixture().
    manager, paths, zones, _ = fixture()
    # Set graph to build_conflict_evidence(manager, paths, zones)['local_conflict_graphs'] at 'AV_0'.
    graph = build_conflict_evidence(manager, paths, zones)[
        # Supply the text 'AV_0' to the enclosing expression.
        "local_conflict_graphs"]["AV_0"]
    # Set row to graph['diagnostics'] at 0.
    row = graph["diagnostics"][0]
    # Require row at 'target_candidate_paths' equals a dictionary containing LEFT; otherwise raise AssertionError.
    assert row["target_candidate_paths"] == {"LEFT": "TARGET_LEFT"}
    # Require a set built from row at 'spatially_conflicting_candidate_paths' equals a set containing the text
    # 'LEFT', the text 'STRAIGHT'; otherwise raise AssertionError.
    assert set(row["spatially_conflicting_candidate_paths"]) == {
        "LEFT", "STRAIGHT"
    }


# Check metrics and temporal classifications match authoritative records using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def test_metrics_and_temporal_classifications_match_authoritative_records():
    # Iterate over a tuple containing a tuple containing the text 'TEMPORAL_CONFLICT', True, the text
    # 'temporal_conflict_edges', a tuple..., binding each item to (status, possible, key).
    for status, possible, key in (
        # Include a tuple containing the text 'TEMPORAL_CONFLICT', True, the text 'temporal_conflict_edges' in
        # this tuple.
        ("TEMPORAL_CONFLICT", True, "temporal_conflict_edges"),
        # Include a tuple containing the text 'SPATIAL_ONLY', False, the text 'spatial_only_edges' in this tuple.
        ("SPATIAL_ONLY", False, "spatial_only_edges"),
        # Include a tuple containing the text 'UNRESOLVED_TIMING', None, the text 'unresolved_temporal_edges' in
        # this tuple.
        ("UNRESOLVED_TIMING", None, "unresolved_temporal_edges"),
    ):
        # Set (manager, paths, zones, ldm) to the result of fixture().
        manager, paths, zones, ldm = fixture(
            # Supply temporal_status as status.
            # Supply possible as possible.
            temporal_status=status, possible=possible
        )
        # Set result to the result of build_conflict_evidence(manager, paths, zones).
        result = build_conflict_evidence(manager, paths, zones)
        # Set kpis to result['conflict_kpis_by_ego'] at 'AV_0'.
        kpis = result["conflict_kpis_by_ego"]["AV_0"]
        # Require kpis at 'spatial_conflict_edges' equals ldm.graph['metrics'] at 'spatial_conflict_edges';
        # otherwise raise AssertionError.
        assert kpis["spatial_conflict_edges"] == ldm.graph["metrics"][
            "spatial_conflict_edges"]
        # Require kpis at key equals 1; otherwise raise AssertionError.
        assert kpis[key] == 1
        # Run this branch when the result of status.startswith(the text 'UNRESOLVED').
        if status.startswith("UNRESOLVED"):
            # Require possible is the same object as None; otherwise raise AssertionError.
            assert possible is None


# Check geometry supports polygon multipolygon and geometry collection using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_geometry_supports_polygon_multipolygon_and_geometry_collection():
    # Set first to the result of Polygon(a tuple containing a tuple containing 0, 0, a tuple containing 1, 0, a
    # tuple containing 1, 1, a...).
    first = Polygon(((0, 0), (1, 0), (1, 1), (0, 1)))
    # Set second to the result of Polygon(a tuple containing a tuple containing 2, 0, a tuple containing 3, 0, a
    # tuple containing 3, 1, a...).
    second = Polygon(((2, 0), (3, 0), (3, 1), (2, 1)))
    # Set geometries to a tuple containing first, the result of MultiPolygon(a tuple containing first, second),
    # the result of GeometryCollection(a...
    geometries = (
        # Include first in this tuple.
        first,
        # Include the result of MultiPolygon(a tuple containing first, second) in this tuple.
        MultiPolygon((first, second)),
        # Include the result of GeometryCollection(a tuple containing first, the result of LineString(a tuple
        # containing (0, 0), (2, 2)), the...) in this tuple.
        GeometryCollection((first, LineString(((0, 0), (2, 2))), Point(1, 1))),
    )
    # Require a list of geometry_mapping(item) at 'type' for item in geometries equals a list containing the text
    # 'Polygon', the text 'MultiPolygon', the text 'GeometryCollection'; otherwise raise AssertionError.
    assert [geometry_mapping(item)["type"] for item in geometries] == [
        "Polygon", "MultiPolygon", "GeometryCollection"
    ]
    # Call json.dumps with the supplied arguments.
    json.dumps([geometry_mapping(item) for item in geometries], allow_nan=False)


# Check geometry uses actual track widths and preserves zero probability using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_geometry_uses_actual_track_widths_and_preserves_zero_probability():
    # Set (manager, paths, zones, _) to the result of fixture().
    manager, paths, zones, _ = fixture(probability=0.0)
    # Set result to the result of build_conflict_evidence(manager, paths, zones).
    result = build_conflict_evidence(manager, paths, zones)
    # Set geometry to result['conflict_geometry_by_ego']['AV_0'] at 'AV_1'.
    geometry = result["conflict_geometry_by_ego"]["AV_0"]["AV_1"]
    # Require geometry at 'ego_width_m' equals 1.8; otherwise raise AssertionError.
    assert geometry["ego_width_m"] == 1.8
    # Require geometry at 'target_width_m' equals 2.1; otherwise raise AssertionError.
    assert geometry["target_width_m"] == 2.1
    # Set row to result['local_conflict_graphs']['AV_0']['diagnostics'] at 0.
    row = result["local_conflict_graphs"]["AV_0"]["diagnostics"][0]
    # Require row at 'intention_weighted_conflict_probability' equals 0.0; otherwise raise AssertionError.
    assert row["intention_weighted_conflict_probability"] == 0.0
    # Set (manager, paths, zones, _) to the result of fixture().
    manager, paths, zones, _ = fixture(probability=None)
    # Set result to the result of build_conflict_evidence(manager, paths, zones).
    result = build_conflict_evidence(manager, paths, zones)
    # Require result['local_conflict_graphs']['AV_0']['diagnostics'][0] at
    # 'intention_weighted_conflict_probability' is the same object as None; otherwise raise AssertionError.
    assert result["local_conflict_graphs"]["AV_0"]["diagnostics"][0][
        # Supply None to the enclosing expression.
        "intention_weighted_conflict_probability"] is None


# Check stopping diagnostics are copied not recalculated using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_stopping_diagnostics_are_copied_not_recalculated():
    # Set (manager, paths, zones, _) to the result of fixture().
    manager, paths, zones, _ = fixture()
    # Set evaluation to build_conflict_evidence(manager, paths,... at 0.
    evaluation = build_conflict_evidence(manager, paths, zones)[
        # Supply 0 to the enclosing expression.
        "temporal_conflict_assessments"]["AV_0"]["edges"][0]["evaluations"][0]
    # Require evaluation at 'ego_stopping_distance_m' equals 4.2; otherwise raise AssertionError.
    assert evaluation["ego_stopping_distance_m"] == 4.2
    # Require evaluation at 'target_stopping_distance_m' equals 5.1; otherwise raise AssertionError.
    assert evaluation["target_stopping_distance_m"] == 5.1


# Check main has one same step write after spatial and temporal calls using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_main_has_one_same_step_write_after_spatial_and_temporal_calls():
    # Import main for use in this module.
    import main
    # Set source to the result of inspect.getsource(main.main).
    source = inspect.getsource(main.main)
    # Set graph_index to the result of source.index(the text 'conflict_graph_manager.build_local_graph').
    graph_index = source.index("conflict_graph_manager.build_local_graph")
    # Set temporal_index to the result of source.index(the text 'occupancy_assessor.assess_ldm').
    temporal_index = source.index("occupancy_assessor.assess_ldm")
    # Set evidence_index to the result of source.index(the text 'evidence_snapshot = build_evidence_snapshot').
    evidence_index = source.index("evidence_snapshot = build_evidence_snapshot")
    # Set write_index to the result of source.index(the text 'evidence_writer.write(evidence_snapshot)').
    write_index = source.index("evidence_writer.write(evidence_snapshot)")
    # Require graph_index is less than temporal_index; is less than evidence_index; is less than write_index;
    # otherwise raise AssertionError.
    assert graph_index < temporal_index < evidence_index < write_index
    # Require the result of source.count(the text 'evidence_writer.write(evidence_snapshot)') equals 1; otherwise
    # raise AssertionError.
    assert source.count("evidence_writer.write(evidence_snapshot)") == 1
