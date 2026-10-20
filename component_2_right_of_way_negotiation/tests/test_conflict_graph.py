"""Map geometry, leakage, intention, and decentralization contracts."""

# Import copy for use in this module.
import copy
# Import math for use in this module.
import math

# Import pytest for use in this module.
import pytest
# Import LineString from shapely.geometry for the operations below.
from shapely.geometry import LineString

# Import SUMO_NETWORK_FILE from config for the operations below.
from config import SUMO_NETWORK_FILE
# Import ConflictGraphManager, ConflictZoneManager, MapPathManager from conflict for the operations below.
from conflict import ConflictGraphManager, ConflictZoneManager, MapPathManager
# Import write_conflict_catalogues from conflict for the operations below.
from conflict import write_conflict_catalogues
# Import extract_operational_intention from conflict.conflict_graph_manager for the operations below.
from conflict.conflict_graph_manager import extract_operational_intention
# Import MovementPath from conflict.models for the operations below.
from conflict.models import MovementPath
# Import ObservationManager from observation for the operations below.
from observation import ObservationManager


# Apply pytest.fixture(scope='module') as a decorator to configure the following definition.
@pytest.fixture(scope="module")
# Managers using the inputs and processing steps below.
# Output: a tuple containing paths, zones, the result of ConflictGraphManager(paths, zones).
def managers():
    # Set paths to the result of MapPathManager(SUMO_NETWORK_FILE).
    paths = MapPathManager(SUMO_NETWORK_FILE)
    # Set zones to the result of ConflictZoneManager(paths).
    zones = ConflictZoneManager(paths)
    # Return a tuple containing paths, zones, the result of ConflictGraphManager(paths, zones) to the caller.
    return paths, zones, ConflictGraphManager(paths, zones)


# Define LDM to group the state and operations declared below.
# Instances expose the attributes and methods implemented in this class.
class LDM:
    # Initialize the instance attributes and collaborators used by the operations below.
    # Input ego_id: the identifier of the ego vehicle.
    # Input tracks: the supplied tracks.
    # Output: no explicit value; normal completion returns None.
    def __init__(self, ego_id, tracks):
        # Set (self.ego_id, self.tracks) to a tuple containing ego_id, tracks.
        self.ego_id, self.tracks = ego_id, tracks


# Prediction using the inputs and processing steps below.
# Input label: the supplied label.
# Input probabilities: the supplied probabilities.
# Output: return the value selected by the matching return branch below.
# Processing: select branches using the stated conditions.
def prediction(label=None, probabilities=None):
    # Run this branch when label is the same object as None.
    if label is None:
        # Return None to the caller.
        return None
    # Run this branch when label equals the text 'UNKNOWN'.
    if label == "UNKNOWN":
        # Return a dictionary containing fused_label, status, primary, secondary to the caller.
        return {"fused_label": "UNKNOWN", "status": "BOTH_UNCERTAIN",
                # Store None under 'primary'.
                # Store None under 'secondary'.
                "primary": None, "secondary": None}
    # Set result to a dictionary containing label, accepted, probabilities.
    result = {"label": label, "accepted": True,
              # Store probabilities or a dictionary containing LEFT, RIGHT, STRAIGHT under 'probabilities'.
              "probabilities": probabilities or {
                  # Store 1.0 when label equals the text 'LEFT', otherwise 0.0 under 'LEFT'.
                  "LEFT": 1.0 if label == "LEFT" else 0.0,
                  # Store 1.0 when label equals the text 'RIGHT', otherwise 0.0 under 'RIGHT'.
                  "RIGHT": 1.0 if label == "RIGHT" else 0.0,
                  # Store 1.0 when label equals the text 'STRAIGHT', otherwise 0.0 under 'STRAIGHT'.
                  "STRAIGHT": 1.0 if label == "STRAIGHT" else 0.0,
              }}
    # Return a dictionary containing fused_label, status, primary, secondary to the caller.
    return {"fused_label": label, "status": "CONFIRMED_AGREEMENT",
            # Store result under 'primary'.
            # Store result under 'secondary'.
            "primary": result, "secondary": result}


# Track using the inputs and processing steps below.
# Input lane: the supplied lane.
# Input width: the supplied width.
# Input plan: the supplied plan.
# Input intent: the supplied intent.
# Input extra: the supplied extra.
# Output: value.
# Processing: select branches using the stated conditions.
def track(lane, width=1.8, plan=None, intent=None, **extra):
    # Set value to a dictionary containing lane_id, width, last_observed_time, intention_prediction.
    value = {"lane_id": lane, "width": width, "last_observed_time": 9.5,
             # Store intent under 'intention_prediction'.
             "intention_prediction": intent}
    # Run this branch when plan is a different object from None.
    if plan is not None:
        # Set value['self_planned_manoeuvre'] to plan.
        value["self_planned_manoeuvre"] = plan
    # Update value with the supplied entries.
    value.update(extra)
    # Return value to the caller.
    return value


# Graph using the inputs and processing steps below.
# Input manager: the supplied manager.
# Input ego_lane: the supplied ego lane.
# Input ego_plan: the supplied ego plan.
# Input target_lane: the supplied target lane.
# Input intent: the supplied intent.
# Input target_extra: the supplied target extra.
# Output: the result of manager.build_local_graph(the result of LDM(the text 'ego', tracks), 10.0).
def graph(manager, ego_lane="w_in_0", ego_plan="STRAIGHT",
          # Declare target_lane, intent, target_extra as input parameters.
          target_lane="s_in_0", intent=None, target_extra=None):
    # Set tracks to a dictionary containing ego, target.
    tracks = {
        # Store the result of track(ego_lane) under 'ego'.
        "ego": track(ego_lane, plan=ego_plan),
        # Store the result of track(target_lane) under 'target'.
        "target": track(target_lane, intent=intent, **(target_extra or {})),
    }
    # Return the result of manager.build_local_graph(the result of LDM(the text 'ego', tracks), 10.0) to the
    # caller.
    return manager.build_local_graph(LDM("ego", tracks), 10.0)


# Check actual map loads and discovers all legal movements using the setup, calls, and assertions below.
# Input managers: the supplied managers.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def test_actual_map_loads_and_discovers_all_legal_movements(managers):
    # Set (paths, _, _) to managers.
    paths, _, _ = managers
    # Require paths.network_file equals a string built from SUMO_NETWORK_FILE; otherwise raise AssertionError.
    assert paths.network_file == str(SUMO_NETWORK_FILE)
    # Require paths.incoming_lane_ids equals a set containing the text 'w_in_0', the text 'e_in_0', the text
    # 's_in_0', the text 'n_in_0'; otherwise raise AssertionError.
    assert paths.incoming_lane_ids == {
        "w_in_0", "e_in_0", "s_in_0", "n_in_0"
    }
    # Require the number of entries in paths.paths equals 12; otherwise raise AssertionError.
    assert len(paths.paths) == 12
    # Iterate over paths.incoming_lane_ids, binding each item to lane.
    for lane in paths.incoming_lane_ids:
        # Require a set built from the result of paths.feasible_paths(lane) equals a set containing the text
        # 'LEFT', the text 'RIGHT', the text 'STRAIGHT'; otherwise raise AssertionError.
        assert set(paths.feasible_paths(lane)) == {"LEFT", "RIGHT", "STRAIGHT"}
    # Require the result of paths.resolve_path(the text 'w_in_0', the text 'UTURN') is the same object as None;
    # otherwise raise AssertionError.
    assert paths.resolve_path("w_in_0", "UTURN") is None
    # Require a list built from paths.paths equals the sorted values from paths.paths; otherwise raise
    # AssertionError.
    assert list(paths.paths) == sorted(paths.paths)
    # Require the number of entries in paths.paths equals the number of entries in a set built from paths.paths;
    # otherwise raise AssertionError.
    assert len(paths.paths) == len(set(paths.paths))


# Check lane safe ids and duplicate registration using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_lane_safe_ids_and_duplicate_registration():
    # Require the result of MapPathManager._stable_path_id(the text 'w_in_0', the text 'STRAIGHT') equals the text
    # 'W_IN_0_STRAIGHT'; otherwise raise AssertionError.
    assert MapPathManager._stable_path_id("w_in_0", "STRAIGHT") == (
        "W_IN_0_STRAIGHT"
    )
    # Require the result of MapPathManager._stable_path_id(the text 'w_in_1', the text 'STRAIGHT') equals the text
    # 'W_IN_1_STRAIGHT'; otherwise raise AssertionError.
    assert MapPathManager._stable_path_id("w_in_1", "STRAIGHT") == (
        "W_IN_1_STRAIGHT"
    )
    # Set first to the result of MovementPath(the text 'W_IN_0_STRAIGHT', the text 'w_in_0', the text 'e_out_0',
    # the text 'STRAIGHT', a tuple...).
    first = MovementPath(
        "W_IN_0_STRAIGHT", "w_in_0", "e_out_0", "STRAIGHT",
        # Supply a tuple containing a tuple containing 0.0, 0.0, a tuple containing 1.0, 0.0 to MovementPath.
        ((0.0, 0.0), (1.0, 0.0)),
    )
    # Set duplicate to the result of MovementPath(the text 'W_IN_0_STRAIGHT', the text 'w_in_1', the text
    # 'e_out_1', the text 'STRAIGHT', a tuple...).
    duplicate = MovementPath(
        "W_IN_0_STRAIGHT", "w_in_1", "e_out_1", "STRAIGHT",
        # Supply a tuple containing a tuple containing 0.0, 1.0, a tuple containing 1.0, 1.0 to MovementPath.
        ((0.0, 1.0), (1.0, 1.0)),
    )
    # Set discovered to an empty dictionary.
    discovered = {}
    # Call MapPathManager._register_path with the supplied arguments.
    MapPathManager._register_path(discovered, first)
    # Enter the result of pytest.raises(ValueError) and run the enclosed operations within that context.
    with pytest.raises(ValueError, match="Duplicate movement path ID"):
        # Call MapPathManager._register_path with the supplied arguments.
        MapPathManager._register_path(discovered, duplicate)


# Check path and zone ids are stable across reloads using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_path_and_zone_ids_are_stable_across_reloads():
    # Set (first_paths, second_paths) to a tuple containing the result of MapPathManager(), the result of
    # MapPathManager().
    first_paths, second_paths = MapPathManager(), MapPathManager()
    # Set first_zones to the result of ConflictZoneManager(first_paths).
    first_zones = ConflictZoneManager(first_paths)
    # Set second_zones to the result of ConflictZoneManager(second_paths).
    second_zones = ConflictZoneManager(second_paths)
    # Require a tuple built from first_paths.paths equals a tuple built from second_paths.paths; otherwise raise
    # AssertionError.
    assert tuple(first_paths.paths) == tuple(second_paths.paths)
    # Require a list of row at 'zone_id' for row in the result of first_zones.catalogue_rows() equals a list of
    # row at 'zone_id' for row in the result of second_zones.catalogue_rows(); otherwise raise AssertionError.
    assert [row["zone_id"] for row in first_zones.catalogue_rows()] == [
        # Evaluate the result of second_zones.catalogue_rows() as part of the enclosing expression.
        row["zone_id"] for row in second_zones.catalogue_rows()
    ]


# Check validation catalogues are network derived using the setup, calls, and assertions below.
# Input managers: the supplied managers.
# Input tmp_path: the supplied tmp path.
# Output: no explicit value; normal completion returns None.
def test_validation_catalogues_are_network_derived(managers, tmp_path):
    # Set (paths, zones, _) to managers.
    paths, zones, _ = managers
    # Set (path_file, zone_file) to the result of write_conflict_catalogues(paths, zones, tmp_path).
    path_file, zone_file = write_conflict_catalogues(paths, zones, tmp_path)
    # Require the result of path_file.read_text().count(the text '') equals the number of entries in paths.paths
    # plus 1; otherwise raise AssertionError.
    assert path_file.read_text().count("\n") == len(paths.paths) + 1
    # Require the text 'W_IN_0_STRAIGHT,w_in_0,e_out_0,STRAIGHT' belongs to the text read from path_file;
    # otherwise raise AssertionError.
    assert "W_IN_0_STRAIGHT,w_in_0,e_out_0,STRAIGHT" in path_file.read_text()
    # Require the text 'topological_relationship' belongs to zone_file.read_text().splitlines() at 0; otherwise
    # raise AssertionError.
    assert "topological_relationship" in zone_file.read_text().splitlines()[0]


# Check path geometry is finite valid and turning using the setup, calls, and assertions below.
# Input managers: the supplied managers.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def test_path_geometry_is_finite_valid_and_turning(managers):
    # Set (paths, _, _) to managers.
    paths, _, _ = managers
    # Iterate over values from paths.paths, binding each item to path.
    for path in paths.paths.values():
        # Set line to the result of LineString(path.centerline_geometry).
        line = LineString(path.centerline_geometry)
        # Require line.is_valid and the negation of line.is_empty and line.length is greater than 0.0; otherwise
        # raise AssertionError.
        assert line.is_valid and not line.is_empty and line.length > 0.0
        # Require whether every item is true in a lazy sequence of whether value contains finite numeric values
        # for point in path.centerline_geometry; otherwise raise AssertionError.
        assert all(math.isfinite(value) for point in path.centerline_geometry
                   # Evaluate value as part of the enclosing expression.
                   for value in point)
    # Require the number of entries in paths.paths['N_IN_0_LEFT'].centerline_geometry is greater than 3; otherwise
    # raise AssertionError.
    assert len(paths.paths["N_IN_0_LEFT"].centerline_geometry) > 3


# Check known crossing nonconflict and types use geometry using the setup, calls, and assertions below.
# Input managers: the supplied managers.
# Output: no explicit value; normal completion returns None.
def test_known_crossing_nonconflict_and_types_use_geometry(managers):
    # Set (_, zones, _) to managers.
    _, zones, _ = managers
    # Require zones.relationship('W_IN_0_STRAIGHT', 'S_IN_0_STRAIGHT').conflict_type equals the text 'CROSSING';
    # otherwise raise AssertionError.
    assert zones.relationship("W_IN_0_STRAIGHT", "S_IN_0_STRAIGHT").conflict_type == "CROSSING"
    # Require zones.relationship('W_IN_0_RIGHT', 'E_IN_0_RIGHT').conflict_type equals the text 'NO_CONFLICT';
    # otherwise raise AssertionError.
    assert zones.relationship("W_IN_0_RIGHT", "E_IN_0_RIGHT").conflict_type == "NO_CONFLICT"
    # Require zones.relationship('W_IN_0_STRAIGHT', 'N_IN_0_LEFT').conflict_type equals the text 'MERGING';
    # otherwise raise AssertionError.
    assert zones.relationship("W_IN_0_STRAIGHT", "N_IN_0_LEFT").conflict_type == "MERGING"
    # Require zones.relationship('W_IN_0_LEFT', 'W_IN_0_STRAIGHT').conflict_type equals the text 'DIVERGING';
    # otherwise raise AssertionError.
    assert zones.relationship("W_IN_0_LEFT", "W_IN_0_STRAIGHT").conflict_type == "DIVERGING"
    # Require zones.relationship('W_IN_0_LEFT', 'W_IN_0_LEFT').conflict_type equals the text 'SAME_PATH';
    # otherwise raise AssertionError.
    assert zones.relationship("W_IN_0_LEFT", "W_IN_0_LEFT").conflict_type == "SAME_PATH"
    # Require zones.relationship('W_IN_0_STRAIGHT', 'S_IN_0_STRAIGHT').conflict_zone_id; otherwise raise
    # AssertionError.
    assert zones.relationship("W_IN_0_STRAIGHT", "S_IN_0_STRAIGHT").conflict_zone_id
    # Require zones.relationship('W_IN_0_LEFT', 'W_IN_0_LEFT').conflict_zone_id is the same object as None;
    # otherwise raise AssertionError.
    assert zones.relationship("W_IN_0_LEFT", "W_IN_0_LEFT").conflict_zone_id is None


# Check no intersection center threshold in new package using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_no_intersection_center_threshold_in_new_package():
    # Import Path from pathlib for the operations below.
    from pathlib import Path
    # Set package_text to the result of ''.join(a lazy sequence of the text read from path for path in the result
    # of Path('conflict').glob(the...).
    package_text = "".join(path.read_text() for path in Path("conflict").glob("*.py"))
    # Require the text 'INTERSECTION_CENTER' does not belong to package_text; otherwise raise AssertionError.
    assert "INTERSECTION_CENTER" not in package_text


# Define SyntheticPaths to group the state and operations declared below.
# Instances expose the attributes and methods implemented in this class.
class SyntheticPaths:
    # Initialize the instance attributes and collaborators used by the operations below.
    # Input paths: the supplied paths.
    # Output: no explicit value; normal completion returns None.
    def __init__(self, paths):
        # Set self.paths to a dictionary of path.path_id mapped to path for path in paths.
        self.paths = {path.path_id: path for path in paths}


# Synthetic path using the inputs and processing steps below.
# Input path_id: the supplied path id.
# Input incoming: the supplied incoming.
# Input outgoing: the supplied outgoing.
# Input points: the supplied points.
# Output: the result of MovementPath(path_id, incoming, outgoing, the text 'STRAIGHT', a tuple built from points).
def synthetic_path(path_id, incoming, outgoing, points):
    # Return the result of MovementPath(path_id, incoming, outgoing, the text 'STRAIGHT', a tuple built from
    # points) to the caller.
    return MovementPath(path_id, incoming, outgoing, "STRAIGHT", tuple(points))


# Check physical envelopes detect crossing offset and separation using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_physical_envelopes_detect_crossing_offset_and_separation():
    # Set paths to the result of SyntheticPaths(a list containing the result of synthetic_path(the text 'A', the
    # text 'a_in_0', the text...).
    paths = SyntheticPaths([
        # Include the result of synthetic_path(the text 'A', the text 'a_in_0', the text 'a_out_0', a tuple
        # containing a tuple containing 0, 0,...) in this list.
        synthetic_path("A", "a_in_0", "a_out_0", ((0, 0), (10, 0))),
        # Include the result of synthetic_path(the text 'CROSS', the text 'b_in_0', the text 'b_out_0', a tuple
        # containing a tuple containing...) in this list.
        synthetic_path("CROSS", "b_in_0", "b_out_0", ((5, -5), (5, 5))),
        # Include the result of synthetic_path(the text 'OFFSET', the text 'c_in_0', the text 'c_out_0', a tuple
        # containing a tuple containing...) in this list.
        synthetic_path("OFFSET", "c_in_0", "c_out_0", ((0, 1), (10, 1))),
        # Include the result of synthetic_path(the text 'FAR', the text 'd_in_0', the text 'd_out_0', a tuple
        # containing a tuple containing 0,...) in this list.
        synthetic_path("FAR", "d_in_0", "d_out_0", ((0, 3), (10, 3))),
    ])
    # Set zones to the result of ConflictZoneManager(paths).
    zones = ConflictZoneManager(paths, catalogue_vehicle_width=1.2)
    # Require zones.relationship('A', 'CROSS').coordinated_conflict; otherwise raise AssertionError.
    assert zones.relationship("A", "CROSS").coordinated_conflict
    # The centrelines are parallel and disjoint, but 0.6 m half-widths overlap.
    # Require the negation of the result of zones.lines['A'].intersects(zones.lines at 'OFFSET'); otherwise raise
    # AssertionError.
    assert not zones.lines["A"].intersects(zones.lines["OFFSET"])
    # Require zones.relationship('A', 'OFFSET').coordinated_conflict; otherwise raise AssertionError.
    assert zones.relationship("A", "OFFSET").coordinated_conflict
    # Require zones.relationship('A', 'OFFSET').conflict_type equals the text 'CROSSING'; otherwise raise
    # AssertionError.
    assert zones.relationship("A", "OFFSET").conflict_type == "CROSSING"
    # Require the negation of zones.relationship('A', 'FAR').physical_overlap; otherwise raise AssertionError.
    assert not zones.relationship("A", "FAR").physical_overlap
    # Require the negation of zones.relationship('A', 'FAR').coordinated_conflict; otherwise raise AssertionError.
    assert not zones.relationship("A", "FAR").coordinated_conflict


# Check same diverging and merging physical semantics using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_same_diverging_and_merging_physical_semantics():
    # Set paths to the result of SyntheticPaths(a list containing the result of synthetic_path(the text 'SAME',
    # the text 'x_in_0', the text...).
    paths = SyntheticPaths([
        # Include the result of synthetic_path(the text 'SAME', the text 'x_in_0', the text 'x_out_0', a tuple
        # containing a tuple containing 0,...) in this list.
        synthetic_path("SAME", "x_in_0", "x_out_0", ((0, 0), (10, 0))),
        # Include the result of synthetic_path(the text 'DIVERGE', the text 'x_in_0', the text 'y_out_0', a tuple
        # containing a tuple containing...) in this list.
        synthetic_path("DIVERGE", "x_in_0", "y_out_0", ((0, 0), (5, 3))),
        # Include the result of synthetic_path(the text 'MERGE', the text 'z_in_0', the text 'x_out_0', a tuple
        # containing a tuple containing...) in this list.
        synthetic_path("MERGE", "z_in_0", "x_out_0", ((5, 3), (10, 0))),
    ])
    # Set zones to the result of ConflictZoneManager(paths).
    zones = ConflictZoneManager(paths, catalogue_vehicle_width=1.8)
    # Set same to the result of zones.relationship(the text 'SAME', the text 'SAME').
    same = zones.relationship("SAME", "SAME")
    # Set diverging to the result of zones.relationship(the text 'SAME', the text 'DIVERGE').
    diverging = zones.relationship("SAME", "DIVERGE")
    # Set merging to the result of zones.relationship(the text 'SAME', the text 'MERGE').
    merging = zones.relationship("SAME", "MERGE")
    # Require same.physical_overlap and the negation of same.coordinated_conflict; otherwise raise AssertionError.
    assert same.physical_overlap and not same.coordinated_conflict
    # Require same.conflict_zone_id is the same object as None; otherwise raise AssertionError.
    assert same.conflict_zone_id is None
    # Require diverging.physical_overlap and the negation of diverging.coordinated_conflict; otherwise raise
    # AssertionError.
    assert diverging.physical_overlap and not diverging.coordinated_conflict
    # Require diverging.conflict_zone_id is the same object as None; otherwise raise AssertionError.
    assert diverging.conflict_zone_id is None
    # Require merging.conflict_type equals the text 'MERGING'; otherwise raise AssertionError.
    assert merging.conflict_type == "MERGING"
    # Require merging.physical_overlap and merging.coordinated_conflict; otherwise raise AssertionError.
    assert merging.physical_overlap and merging.coordinated_conflict
    # Set record to the result of zones.zone_record(the text 'SAME', 1.8, the text 'MERGE', 1.8).
    record = zones.zone_record("SAME", 1.8, "MERGE", 1.8)
    # Require record at 'geometry_type' belongs to a set containing the text 'Polygon', the text 'MultiPolygon',
    # the text 'GeometryCollection'; otherwise raise AssertionError.
    assert record["geometry_type"] in {"Polygon", "MultiPolygon", "GeometryCollection"}
    # Require record at 'first_path_distance_interval' is a different object from None; otherwise raise
    # AssertionError.
    assert record["first_path_distance_interval"] is not None
    # Require record at 'second_path_distance_interval' is a different object from None; otherwise raise
    # AssertionError.
    assert record["second_path_distance_interval"] is not None


# Apply pytest.mark.parametrize('label', ['LEFT', 'RIGHT', 'STRAIGHT']) as a decorator to configure the following
# definition.
@pytest.mark.parametrize("label", ["LEFT", "RIGHT", "STRAIGHT"])
# Check accepted prediction selects only matching legal path using the setup, calls, and assertions below.
# Input managers: the supplied managers.
# Input label: the supplied label.
# Output: no explicit value; normal completion returns None.
def test_accepted_prediction_selects_only_matching_legal_path(managers, label):
    # Set (_, _, manager) to managers.
    _, _, manager = managers
    # Set result to the result of graph(manager).
    result = graph(manager, intent=prediction(label))
    # Set candidates to result['diagnostics'][0] at 'target_candidate_paths'.
    candidates = result["diagnostics"][0]["target_candidate_paths"]
    # Require candidates equals a dictionary of the supplied entries; otherwise raise AssertionError.
    assert candidates == {label: f"S_IN_0_{label}"}


# Check prediction does not remove feasible spatial conflicts using the setup, calls, and assertions below.
# Input managers: the supplied managers.
# Output: no explicit value; normal completion returns None.
def test_prediction_does_not_remove_feasible_spatial_conflicts(managers):
    # Set (_, _, manager) to managers.
    _, _, manager = managers
    # Set conflicting to the result of graph(manager).
    conflicting = graph(
        # Supply target_lane as the text 'n_in_0'.
        # Supply intent as the result of prediction(the text 'STRAIGHT').
        manager, target_lane="n_in_0", intent=prediction("STRAIGHT")
    )
    # Require the number of entries in conflicting at 'edges' equals 1; otherwise raise AssertionError.
    assert len(conflicting["edges"]) == 1
    # Require conflicting['diagnostics'][0] at 'reason' equals the text 'CONFLICTING_PREDICTED_PATH'; otherwise
    # raise AssertionError.
    assert conflicting["diagnostics"][0]["reason"] == (
        "CONFLICTING_PREDICTED_PATH"
    )
    # Set predicted_nonconflicting to the result of graph(manager).
    predicted_nonconflicting = graph(
        # Supply target_lane as the text 'n_in_0'.
        # Supply intent as the result of prediction(the text 'RIGHT').
        manager, target_lane="n_in_0", intent=prediction("RIGHT")
    )
    # Require the number of entries in predicted_nonconflicting at 'edges' equals 1; otherwise raise
    # AssertionError.
    assert len(predicted_nonconflicting["edges"]) == 1
    # Set diagnostic to predicted_nonconflicting['diagnostics'] at 0.
    diagnostic = predicted_nonconflicting["diagnostics"][0]
    # Require diagnostic at 'reason' equals the text 'CONFLICTING_FEASIBLE_PATH_SET'; otherwise raise
    # AssertionError.
    assert diagnostic["reason"] == "CONFLICTING_FEASIBLE_PATH_SET"
    # Require a set built from diagnostic at 'spatially_conflicting_candidate_paths' equals a set containing the
    # text 'LEFT', the text 'STRAIGHT'; otherwise raise AssertionError.
    assert set(diagnostic["spatially_conflicting_candidate_paths"]) == (
        # Evaluate a set containing the text 'LEFT', the text 'STRAIGHT' as part of the enclosing expression.
        {"LEFT", "STRAIGHT"}
    )


# Apply (prediction('UNKNOWN'), 'UNKNOWN') as a decorator to configure the following definition.
@pytest.mark.parametrize("intent,status", [(prediction("UNKNOWN"), "UNKNOWN"),
                                             # Include a tuple containing None, the text 'NOT_AVAILABLE' in this
                                             # list.
                                             (None, "NOT_AVAILABLE")])
# Check unknown or missing prediction keeps all feasible paths using the setup, calls, and assertions below.
# Input managers: the supplied managers.
# Input intent: the supplied intent.
# Input status: the supplied status.
# Output: no explicit value; normal completion returns None.
def test_unknown_or_missing_prediction_keeps_all_feasible_paths(
        # Declare managers, intent, status as input parameters.
        managers, intent, status):
    # Set (_, _, manager) to managers.
    _, _, manager = managers
    # Set result to the result of graph(manager).
    result = graph(manager, intent=intent)
    # Set diagnostic to result['diagnostics'] at 0.
    diagnostic = result["diagnostics"][0]
    # Require a set built from diagnostic at 'target_candidate_paths' equals a set containing the text 'LEFT', the
    # text 'RIGHT', the text 'STRAIGHT'; otherwise raise AssertionError.
    assert set(diagnostic["target_candidate_paths"]) == {
        "LEFT", "RIGHT", "STRAIGHT"
    }
    # Require diagnostic at 'prediction_status' equals status; otherwise raise AssertionError.
    assert diagnostic["prediction_status"] == status
    # Require diagnostic at 'intention_weighted_conflict_probability' is the same object as None; otherwise raise
    # AssertionError.
    assert diagnostic["intention_weighted_conflict_probability"] is None
    # Require diagnostic at 'reason' equals the text 'CONFLICTING_UNKNOWN_PATH_SET'; otherwise raise
    # AssertionError.
    assert diagnostic["reason"] == "CONFLICTING_UNKNOWN_PATH_SET"


# Check impossible prediction falls back and is diagnostic using the setup, calls, and assertions below.
# Input managers: the supplied managers.
# Output: no explicit value; normal completion returns None.
# Processing: handle the specified errors.
def test_impossible_prediction_falls_back_and_is_diagnostic(managers):
    # Set (paths, _, manager) to managers.
    paths, _, manager = managers
    # Set original to the result of paths.paths_by_lane['s_in_0'].pop(the text 'LEFT').
    original = paths.paths_by_lane["s_in_0"].pop("LEFT")
    # Attempt the enclosed operations and route matching exceptions to the handlers below.
    try:
        # Set result to the result of graph(manager).
        result = graph(manager, intent=prediction("LEFT"))
        # Require result['diagnostics'][0] at 'reason' equals the text 'NO_FEASIBLE_PATH'; otherwise raise
        # AssertionError.
        assert result["diagnostics"][0]["reason"] == "NO_FEASIBLE_PATH"
        # Require a set built from result['diagnostics'][0] at 'target_candidate_paths' equals a set containing
        # the text 'RIGHT', the text 'STRAIGHT'; otherwise raise AssertionError.
        assert set(result["diagnostics"][0]["target_candidate_paths"]) == {
            "RIGHT", "STRAIGHT"
        }
    # Run these cleanup steps whether the preceding operations succeed or raise an exception.
    finally:
        # Set paths.paths_by_lane['s_in_0']['LEFT'] to original.
        paths.paths_by_lane["s_in_0"]["LEFT"] = original


# Check probability is exact conflicting class mass using the setup, calls, and assertions below.
# Input managers: the supplied managers.
# Output: no explicit value; normal completion returns None.
def test_probability_is_exact_conflicting_class_mass(managers):
    # Set (_, _, manager) to managers.
    _, _, manager = managers
    # Set probabilities to a dictionary containing LEFT, STRAIGHT, RIGHT.
    probabilities = {"LEFT": 0.6, "STRAIGHT": 0.3, "RIGHT": 0.1}
    # Set result to the result of graph(manager).
    result = graph(
        # Supply target_lane as the text 'n_in_0'.
        # Supply intent as the result of prediction(the text 'LEFT', probabilities).
        manager, target_lane="n_in_0", intent=prediction("LEFT", probabilities)
    )
    # W_STRAIGHT conflicts with N_LEFT and N_STRAIGHT, but not N_RIGHT.
    # Require result['diagnostics'][0] at 'intention_weighted_conflict_probability' equals the result of
    # pytest.approx(0.9); otherwise raise AssertionError.
    assert result["diagnostics"][0][
        "intention_weighted_conflict_probability"
    # Evaluate the result of pytest.approx(0.9) as part of the enclosing expression.
    ] == pytest.approx(0.9)


# Check probability zero and one using the setup, calls, and assertions below.
# Input managers: the supplied managers.
# Output: no explicit value; normal completion returns None.
def test_probability_zero_and_one(managers):
    # Set (_, _, manager) to managers.
    _, _, manager = managers
    # Set zero to the result of graph(manager).
    zero = graph(manager, target_lane="e_in_0", intent=prediction(
        # Store 0.0 under 'LEFT'.
        # Store 0.0 under 'STRAIGHT'.
        # Store 1.0 under 'RIGHT'.
        "RIGHT", {"LEFT": 0.0, "STRAIGHT": 0.0, "RIGHT": 1.0}
    ))
    # Require zero['diagnostics'][0] at 'intention_weighted_conflict_probability' equals 0.0; otherwise raise
    # AssertionError.
    assert zero["diagnostics"][0]["intention_weighted_conflict_probability"] == 0.0
    # Set all_conflict to the result of graph(manager).
    all_conflict = graph(manager, target_lane="s_in_0", intent=prediction(
        # Store 0.5 under 'LEFT'.
        # Store 0.5 under 'STRAIGHT'.
        # Store 0.0 under 'RIGHT'.
        "LEFT", {"LEFT": 0.5, "STRAIGHT": 0.5, "RIGHT": 0.0}
    ))
    # Require all_conflict['diagnostics'][0] at 'intention_weighted_conflict_probability' equals 1.0; otherwise
    # raise AssertionError.
    assert all_conflict["diagnostics"][0]["intention_weighted_conflict_probability"] == 1.0


# Check route truth fields cannot change graph using the setup, calls, and assertions below.
# Input managers: the supplied managers.
# Output: no explicit value; normal completion returns None.
def test_route_truth_fields_cannot_change_graph(managers):
    # Set (_, _, manager) to managers.
    _, _, manager = managers
    # Set first to the result of graph(manager).
    first = graph(manager, intent=prediction("LEFT"), target_extra={
        # Store the text 'route_s_right' under 'route_id'.
        # Store 9 under 'route_index'.
        "route_id": "route_s_right", "route_index": 9,
        "ground_truth_route_id": "route_s_straight",
        "intended_manoeuvre": "RIGHT",
    })
    # Set second to the result of graph(manager).
    second = graph(manager, intent=prediction("LEFT"), target_extra={
        # Store the text 'route_s_left' under 'route_id'.
        # Store 0 under 'route_index'.
        "route_id": "route_s_left", "route_index": 0,
        "ground_truth_route_id": "route_s_left",
        "intended_manoeuvre": "STRAIGHT",
    })
    # Require first equals second; otherwise raise AssertionError.
    assert first == second


# Check ego self intention changes only ego path using the setup, calls, and assertions below.
# Input managers: the supplied managers.
# Output: no explicit value; normal completion returns None.
def test_ego_self_intention_changes_only_ego_path(managers):
    # Set (_, _, manager) to managers.
    _, _, manager = managers
    # Set left to the result of graph(manager).
    left = graph(manager, ego_plan="LEFT", intent=prediction("RIGHT"))
    # Set straight to the result of graph(manager).
    straight = graph(manager, ego_plan="STRAIGHT", intent=prediction("RIGHT"))
    # Require left at 'ego_path_id' equals the text 'W_IN_0_LEFT'; otherwise raise AssertionError.
    assert left["ego_path_id"] == "W_IN_0_LEFT"
    # Require straight at 'ego_path_id' equals the text 'W_IN_0_STRAIGHT'; otherwise raise AssertionError.
    assert straight["ego_path_id"] == "W_IN_0_STRAIGHT"
    # Require left['diagnostics'][0] at 'target_candidate_paths' equals straight['diagnostics'][0] at
    # 'target_candidate_paths'; otherwise raise AssertionError.
    assert left["diagnostics"][0]["target_candidate_paths"] == straight[
        "diagnostics"
    # Supply the text 'target_candidate_paths' to the enclosing expression.
    ][0]["target_candidate_paths"]


# Check missing ego plan produces zero edge metrics using the setup, calls, and assertions below.
# Input managers: the supplied managers.
# Output: no explicit value; normal completion returns None.
def test_missing_ego_plan_produces_zero_edge_metrics(managers):
    # Set (_, _, manager) to managers.
    _, _, manager = managers
    # Set result to the result of graph(manager).
    result = graph(manager, ego_plan=None, intent=None)
    # Require result at 'edges' equals an empty tuple; otherwise raise AssertionError.
    assert result["edges"] == ()
    # Require result['diagnostics'][0] at 'reason' equals the text 'MISSING_EGO_PLAN'; otherwise raise
    # AssertionError.
    assert result["diagnostics"][0]["reason"] == "MISSING_EGO_PLAN"
    # Require result['metrics'] at 'unknown_intention_conservative_edges' equals 0; otherwise raise
    # AssertionError.
    assert result["metrics"]["unknown_intention_conservative_edges"] == 0
    # Require result['metrics'] at 'prediction_unavailable_conservative_edges' equals 0; otherwise raise
    # AssertionError.
    assert result["metrics"]["prediction_unavailable_conservative_edges"] == 0


# Check self navigation adapter exposes only requested ego intention using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_self_navigation_adapter_exposes_only_requested_ego_intention():
    # Set ego to a dictionary containing route_id.
    ego = {"route_id": "route_w_left"}
    # Set target to a dictionary containing route_id.
    target = {"route_id": "route_s_right"}
    # Require the result of ObservationManager.get_ego_planned_manoeuvre(the text 'ego', ego) equals the text
    # 'LEFT'; otherwise raise AssertionError.
    assert ObservationManager.get_ego_planned_manoeuvre("ego", ego) == "LEFT"
    # Supplying ego state never requires or reads the surrounding state.
    # Require the text 'self_planned_manoeuvre' does not belong to target; otherwise raise AssertionError.
    assert "self_planned_manoeuvre" not in target


# Check per ego graphs are independent and reset independently using the setup, calls, and assertions below.
# Input managers: the supplied managers.
# Output: no explicit value; normal completion returns None.
def test_per_ego_graphs_are_independent_and_reset_independently(managers):
    # Set (paths, zones, _) to managers.
    paths, zones, _ = managers
    # Set manager to the result of ConflictGraphManager(paths, zones).
    manager = ConflictGraphManager(paths, zones)
    # Set one to the result of manager.build_local_graph(the result of LDM(the text 'AV_1', a dictionary
    # containing AV_1, target), 1.0).
    one = manager.build_local_graph(LDM("AV_1", {
        # Store the result of track(the text 'w_in_0') under 'AV_1'.
        "AV_1": track("w_in_0", plan="STRAIGHT"),
        # Store the result of track(the text 's_in_0') under 'target'.
        "target": track("s_in_0", intent=None),
    # Supply 1.0 to the enclosing expression.
    }), 1.0)
    # Set two to the result of manager.build_local_graph(the result of LDM(the text 'AV_2', a dictionary
    # containing AV_2), 1.0).
    two = manager.build_local_graph(LDM("AV_2", {
        # Store the result of track(the text 'e_in_0') under 'AV_2'.
        "AV_2": track("e_in_0", plan="RIGHT"),
    # Supply 1.0 to the enclosing expression.
    }), 1.0)
    # Require one differs from two; otherwise raise AssertionError.
    assert one != two
    # Set modified to the result of copy.deepcopy(one).
    modified = copy.deepcopy(one)
    # Set modified['nodes'] to an empty tuple.
    modified["nodes"] = ()
    # Require manager.get_graph('AV_1') at 'nodes' differs from an empty tuple; otherwise raise AssertionError.
    assert manager.get_graph("AV_1")["nodes"] != ()
    # Call manager.reset with the supplied arguments.
    manager.reset("AV_1")
    # Require the result of manager.get_graph(the text 'AV_1') is the same object as None; otherwise raise
    # AssertionError.
    assert manager.get_graph("AV_1") is None
    # Require the result of manager.get_graph(the text 'AV_2') is a different object from None; otherwise raise
    # AssertionError.
    assert manager.get_graph("AV_2") is not None


# Check graph changes report prediction and edge transitions using the setup, calls, and assertions below.
# Input managers: the supplied managers.
# Output: no explicit value; normal completion returns None.
def test_graph_changes_report_prediction_and_edge_transitions(managers):
    # Set (paths, zones, _) to managers.
    paths, zones, _ = managers
    # Set manager to the result of ConflictGraphManager(paths, zones).
    manager = ConflictGraphManager(paths, zones)
    # Set ldm to the result of LDM(the text 'ego', a dictionary containing ego, target).
    ldm = LDM("ego", {
        # Store the result of track(the text 'w_in_0') under 'ego'.
        "ego": track("w_in_0", plan="STRAIGHT"),
        # Store the result of track(the text 'n_in_0') under 'target'.
        "target": track("n_in_0", intent=None),
    })
    # Set first to the result of manager.build_local_graph(ldm, 1.0).
    first = manager.build_local_graph(ldm, 1.0)
    # Require whether any item is true in a lazy sequence of item at 'change_type' equals the text 'EDGE_ADDED'
    # for item in first at 'changes'; otherwise raise AssertionError.
    assert any(item["change_type"] == "EDGE_ADDED" for item in first["changes"])
    # Set ldm.tracks['target']['intention_prediction'] to the result of prediction(the text 'RIGHT').
    ldm.tracks["target"]["intention_prediction"] = prediction("RIGHT")
    # Set second to the result of manager.build_local_graph(ldm, 2.0).
    second = manager.build_local_graph(ldm, 2.0)
    # Set change_types to a set of item at 'change_type' for item in second at 'changes'.
    change_types = {item["change_type"] for item in second["changes"]}
    # Require the text 'EDGE_REMOVED' does not belong to change_types; otherwise raise AssertionError.
    assert "EDGE_REMOVED" not in change_types
    # Require the text 'PREDICTION_STATUS_CHANGED' belongs to change_types; otherwise raise AssertionError.
    assert "PREDICTION_STATUS_CHANGED" in change_types
    # Require the text 'CANDIDATE_PATHS_CHANGED' belongs to change_types; otherwise raise AssertionError.
    assert "CANDIDATE_PATHS_CHANGED" in change_types


# Check graph paths persist and narrow from observed internal lanes using the setup, calls, and assertions below.
# Input managers: the supplied managers.
# Output: no explicit value; normal completion returns None.
def test_graph_paths_persist_and_narrow_from_observed_internal_lanes(managers):
    # Set (paths, zones, _) to managers.
    paths, zones, _ = managers
    # Set manager to the result of ConflictGraphManager(paths, zones).
    manager = ConflictGraphManager(paths, zones)
    # Set ldm to the result of LDM(the text 'ego', a dictionary containing ego, target).
    ldm = LDM("ego", {
        # Store the result of track(the text 'w_in_0') under 'ego'.
        "ego": track("w_in_0", plan="STRAIGHT"),
        # Store the result of track(the text 'n_in_0') under 'target'.
        "target": track("n_in_0", intent=None),
    })
    # Set initial to the result of manager.build_local_graph(ldm, 0.0).
    initial = manager.build_local_graph(ldm, 0.0)
    # Require initial at 'ego_path_id' equals the text 'W_IN_0_STRAIGHT'; otherwise raise AssertionError.
    assert initial["ego_path_id"] == "W_IN_0_STRAIGHT"

    # Set ego_path to paths.paths at 'W_IN_0_STRAIGHT'.
    ego_path = paths.paths["W_IN_0_STRAIGHT"]
    # Set target_path to paths.paths at 'N_IN_0_STRAIGHT'.
    target_path = paths.paths["N_IN_0_STRAIGHT"]
    # Update ldm.tracks['ego'] with the supplied entries.
    ldm.tracks["ego"].update(
        # Supply lane_id as ego_path.internal_lane_ids at 0.
        # Supply position as a tuple containing 300.0, 298.4.
        lane_id=ego_path.internal_lane_ids[0], position=(300.0, 298.4)
    )
    # Update ldm.tracks['target'] with the supplied entries.
    ldm.tracks["target"].update(
        # Supply lane_id as target_path.internal_lane_ids at 0.
        # Supply position as a tuple containing 298.4, 300.0.
        lane_id=target_path.internal_lane_ids[0], position=(298.4, 300.0)
    )
    # Set current to the result of manager.build_local_graph(ldm, 1.0).
    current = manager.build_local_graph(ldm, 1.0)
    # Require current at 'ego_path_id' equals the text 'W_IN_0_STRAIGHT'; otherwise raise AssertionError.
    assert current["ego_path_id"] == "W_IN_0_STRAIGHT"
    # Set candidates to current['diagnostics'][0] at 'target_candidate_paths'.
    candidates = current["diagnostics"][0]["target_candidate_paths"]
    # Require candidates equals a dictionary containing STRAIGHT; otherwise raise AssertionError.
    assert candidates == {"STRAIGHT": "N_IN_0_STRAIGHT"}


# Check adapter consumes fused contract not stage reinterpretation using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_adapter_consumes_fused_contract_not_stage_reinterpretation():
    # Set value to the result of prediction(the text 'LEFT').
    value = prediction("LEFT")
    # Set value['primary']['label'] to the text 'RIGHT'.
    value["primary"]["label"] = "RIGHT"
    # Require extract_operational_intention({'intention_prediction': value}) at 0 equals the text 'LEFT';
    # otherwise raise AssertionError.
    assert extract_operational_intention({"intention_prediction": value})[0] == "LEFT"
