# Import replace from dataclasses for the operations below.
from dataclasses import replace
# Import SimpleNamespace from types for the operations below.
from types import SimpleNamespace

# Import pytest for use in this module.
import pytest

# Import APPROACH_ZONE_RADIUS from config for the operations below.
from config import APPROACH_ZONE_RADIUS
# Import ConflictZoneManager, MapPathManager from conflict for the operations below.
from conflict import ConflictZoneManager, MapPathManager
# Import IntersectionGeometryError, derive_intersection_geometry, get_intersection_geometry,
# is_position_in_approach_zone from map_geometry for the operations below.
from map_geometry import (IntersectionGeometryError, derive_intersection_geometry,
                          get_intersection_geometry,
                          is_position_in_approach_zone)
# Import NegotiationManager from negotiation for the operations below.
from negotiation import NegotiationManager
# Import LocalDynamicMap, ObservationManager from observation for the operations below.
from observation import LocalDynamicMap, ObservationManager


# Check common junction and center are derived from every legal path using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def test_common_junction_and_center_are_derived_from_every_legal_path():
    # Set paths to the result of MapPathManager().
    paths = MapPathManager()
    # Set geometry to the result of derive_intersection_geometry(paths).
    geometry = derive_intersection_geometry(paths)
    # Require geometry.movement_path_ids_used equals a tuple built from the sorted values from paths.paths;
    # otherwise raise AssertionError.
    assert geometry.movement_path_ids_used == tuple(sorted(paths.paths))
    # Iterate over values from paths.paths, binding each item to path.
    for path in paths.paths.values():
        # Set incoming to the result of paths.network.getLane(path.incoming_lane_id).getEdge().getToNode().
        incoming = paths.network.getLane(path.incoming_lane_id).getEdge().getToNode()
        # Set outgoing to the result of paths.network.getLane(path.outgoing_lane_id).getEdge().getFromNode().
        outgoing = paths.network.getLane(path.outgoing_lane_id).getEdge().getFromNode()
        # Require the result of incoming.getID() equals the result of outgoing.getID(); equals
        # geometry.junction_id; otherwise raise AssertionError.
        assert incoming.getID() == outgoing.getID() == geometry.junction_id
    # Require geometry.center_xy equals a tuple built from a lazy sequence of a floating-point number built from x
    # for x in the result of paths.network.getNode(geometry.junction_id).getCoord(); otherwise raise
    # AssertionError.
    assert geometry.center_xy == tuple(
        # Evaluate the result of paths.network.getNode(geometry.junction_id).getCoord() as part of the enclosing
        # expression.
        float(x) for x in paths.network.getNode(geometry.junction_id).getCoord())


# Check location metadata is audited without offset application using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_location_metadata_is_audited_without_offset_application():
    # Set geometry to the result of get_intersection_geometry().
    geometry = get_intersection_geometry()
    # Require geometry.coordinate_frame equals the text 'SUMO_COMPILED_NETWORK_XY_METERS'; otherwise raise
    # AssertionError.
    assert geometry.coordinate_frame == "SUMO_COMPILED_NETWORK_XY_METERS"
    # Require geometry.net_offset; otherwise raise AssertionError.
    assert geometry.net_offset
    # Require geometry.provenance at 'location_metadata_role' equals the text 'PROVENANCE_ONLY'; otherwise raise
    # AssertionError.
    assert geometry.provenance["location_metadata_role"] == "PROVENANCE_ONLY"
    # Require geometry.provenance at 'manual_offset_application' equals the text 'False'; otherwise raise
    # AssertionError.
    assert geometry.provenance["manual_offset_application"] == "False"


# Check shared approach predicate preserves closed boundary using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_shared_approach_predicate_preserves_closed_boundary():
    # Set geometry to the result of get_intersection_geometry().
    geometry = get_intersection_geometry()
    # Set (cx, cy) to geometry.center_xy.
    cx, cy = geometry.center_xy
    # Require the result of is_position_in_approach_zone(a tuple containing cx, cy, geometry); otherwise raise
    # AssertionError.
    assert is_position_in_approach_zone((cx, cy), geometry)
    # Require the result of is_position_in_approach_zone(a tuple containing cx plus APPROACH_ZONE_RADIUS, cy,
    # geometry); otherwise raise AssertionError.
    assert is_position_in_approach_zone((cx + APPROACH_ZONE_RADIUS, cy), geometry)
    # Require the negation of the result of is_position_in_approach_zone(a tuple containing cx +
    # APPROACH_ZONE_RADIUS plus 1.0, cy, geometry); otherwise raise AssertionError.
    assert not is_position_in_approach_zone(
        # Supply a tuple containing cx plus APPROACH_ZONE_RADIUS plus 1.0, cy to is_position_in_approach_zone.
        (cx + APPROACH_ZONE_RADIUS + 1.0, cy), geometry)
    # Require the result of ObservationManager.is_in_approach_zone(a tuple containing cx, cy); otherwise raise
    # AssertionError.
    assert ObservationManager.is_in_approach_zone((cx, cy))


# Check ldm and legacy negotiator share authoritative center using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_ldm_and_legacy_negotiator_share_authoritative_center():
    # Set geometry to the result of get_intersection_geometry().
    geometry = get_intersection_geometry()
    # Require the result of LocalDynamicMap._distance_to_center(geometry.center_xy) equals 0.0; otherwise raise
    # AssertionError.
    assert LocalDynamicMap._distance_to_center(geometry.center_xy) == 0.0
    # Set manager to the result of NegotiationManager().
    manager = NegotiationManager()
    # Require manager.intersection_geometry is the same object as geometry; otherwise raise AssertionError.
    assert manager.intersection_geometry is geometry
    # Require the result of manager.calculate_urgency(a dictionary containing pos) equals 1.0; otherwise raise
    # AssertionError.
    assert manager.calculate_urgency({"pos": geometry.center_xy}) == 1.0


# Define _Node to group the state and operations declared below.
# Instances expose the attributes and methods implemented in this class.
class _Node:
    # Initialize the instance attributes and collaborators used by the operations below.
    # Input identity: the supplied identity.
    # Output: no explicit value; normal completion returns None.
    # Set self.identity to identity.
    def __init__(self, identity): self.identity = identity
    # Get ID using the inputs and processing steps below.
    # Output: self.identity.
    # Return self.identity to the caller.
    def getID(self): return self.identity
    # Get Coord using the inputs and processing steps below.
    # Output: a tuple containing 0.0, 0.0.
    # Return a tuple containing 0.0, 0.0 to the caller.
    def getCoord(self): return (0.0, 0.0)


# Define _Edge to group the state and operations declared below.
# Instances expose the attributes and methods implemented in this class.
class _Edge:
    # Initialize the instance attributes and collaborators used by the operations below.
    # Input source: the supplied source.
    # Input target: the supplied target.
    # Output: no explicit value; normal completion returns None.
    # Set (self.source, self.target) to a tuple containing source, target.
    def __init__(self, source, target): self.source, self.target = source, target
    # Get From Node using the inputs and processing steps below.
    # Output: self.source.
    # Return self.source to the caller.
    def getFromNode(self): return self.source
    # Get To Node using the inputs and processing steps below.
    # Output: self.target.
    # Return self.target to the caller.
    def getToNode(self): return self.target


# Define _Lane to group the state and operations declared below.
# Instances expose the attributes and methods implemented in this class.
class _Lane:
    # Initialize the instance attributes and collaborators used by the operations below.
    # Input edge: the supplied edge.
    # Output: no explicit value; normal completion returns None.
    # Set self.edge to edge.
    def __init__(self, edge): self.edge = edge
    # Get Edge using the inputs and processing steps below.
    # Output: self.edge.
    # Return self.edge to the caller.
    def getEdge(self): return self.edge


# Fake manager using the inputs and processing steps below.
# Input path_specs: the supplied path specs.
# Output: the result of SimpleNamespace().
# Processing: iterate over the relevant records.
def _fake_manager(path_specs):
    # Set (lanes, paths, nodes) to a tuple containing an empty dictionary, an empty dictionary, an empty
    # dictionary.
    lanes, paths, nodes = {}, {}, {}
    # Iterate over path_specs, binding each item to (path_id, incoming_target, outgoing_source).
    for path_id, incoming_target, outgoing_source in path_specs:
        # Call nodes.setdefault with the supplied arguments.
        nodes.setdefault(incoming_target, _Node(incoming_target))
        # Call nodes.setdefault with the supplied arguments.
        nodes.setdefault(outgoing_source, _Node(outgoing_source))
        # Set (incoming, outgoing) to a tuple containing formatted text built from the embedded values, formatted
        # text built from the embedded values.
        incoming, outgoing = f"{path_id}_in", f"{path_id}_out"
        # Set lanes[incoming] to the result of _Lane(the result of _Edge(the result of _Node(the text 'outside'),
        # nodes at incoming_target)).
        lanes[incoming] = _Lane(_Edge(_Node("outside"), nodes[incoming_target]))
        # Set lanes[outgoing] to the result of _Lane(the result of _Edge(nodes at outgoing_source, the result of
        # _Node(the text 'outside'))).
        lanes[outgoing] = _Lane(_Edge(nodes[outgoing_source], _Node("outside")))
        # Set paths[path_id] to the result of SimpleNamespace().
        paths[path_id] = SimpleNamespace(
            # Supply incoming_lane_id as incoming.
            # Supply outgoing_lane_id as outgoing.
            incoming_lane_id=incoming, outgoing_lane_id=outgoing)
    # Set network to the result of SimpleNamespace().
    network = SimpleNamespace(
        # Supply getLane as lanes.__getitem__.
        # Supply getNode as nodes.__getitem__.
        getLane=lanes.__getitem__, getNode=nodes.__getitem__,
        # Store the text '0,0' under 'netOffset'.
        # Store the text '0,0,1,1' under 'convBoundary'.
        _location={"netOffset": "0,0", "convBoundary": "0,0,1,1",
                   "origBoundary": "0,0,1,1", "projParameter": "!"})
    # Return the result of SimpleNamespace() to the caller.
    return SimpleNamespace(paths=paths, network=network)


# Check inconsistent path junction is rejected using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_inconsistent_path_junction_is_rejected():
    # Enter the result of pytest.raises(IntersectionGeometryError) and run the enclosed operations within that
    # context.
    with pytest.raises(IntersectionGeometryError,
                       # Supply match as the text 'MOVEMENT_PATH_JUNCTION_INCONSISTENT'.
                       match="MOVEMENT_PATH_JUNCTION_INCONSISTENT"):
        # Call derive_intersection_geometry with the supplied arguments.
        derive_intersection_geometry(_fake_manager((("P", "A", "B"),)))


# Check ambiguous common junction is rejected using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_ambiguous_common_junction_is_rejected():
    # Enter the result of pytest.raises(IntersectionGeometryError) and run the enclosed operations within that
    # context.
    with pytest.raises(IntersectionGeometryError,
                       # Supply match as the text 'INTERSECTION_JUNCTION_IDENTITY_AMBIGUOUS'.
                       match="INTERSECTION_JUNCTION_IDENTITY_AMBIGUOUS"):
        # Call derive_intersection_geometry with the supplied arguments.
        derive_intersection_geometry(_fake_manager(
            # Supply a tuple containing a tuple containing the text 'P', the text 'A', the text 'A', a tuple
            # containing the text 'Q', the text... to _fake_manager.
            (("P", "A", "A"), ("Q", "B", "B"))))
