from dataclasses import replace
from types import SimpleNamespace

import pytest

from config import APPROACH_ZONE_RADIUS
from conflict import ConflictZoneManager, MapPathManager
from map_geometry import (IntersectionGeometryError, derive_intersection_geometry,
                          get_intersection_geometry,
                          is_position_in_approach_zone)
from negotiation import NegotiationManager
from observation import LocalDynamicMap, ObservationManager


def test_common_junction_and_center_are_derived_from_every_legal_path():
    paths = MapPathManager()
    geometry = derive_intersection_geometry(paths)
    assert geometry.movement_path_ids_used == tuple(sorted(paths.paths))
    for path in paths.paths.values():
        incoming = paths.network.getLane(path.incoming_lane_id).getEdge().getToNode()
        outgoing = paths.network.getLane(path.outgoing_lane_id).getEdge().getFromNode()
        assert incoming.getID() == outgoing.getID() == geometry.junction_id
    assert geometry.center_xy == tuple(
        float(x) for x in paths.network.getNode(geometry.junction_id).getCoord())


def test_location_metadata_is_audited_without_offset_application():
    geometry = get_intersection_geometry()
    assert geometry.coordinate_frame == "SUMO_COMPILED_NETWORK_XY_METERS"
    assert geometry.net_offset
    assert geometry.provenance["location_metadata_role"] == "PROVENANCE_ONLY"
    assert geometry.provenance["manual_offset_application"] == "False"


def test_shared_approach_predicate_preserves_closed_boundary():
    geometry = get_intersection_geometry()
    cx, cy = geometry.center_xy
    assert is_position_in_approach_zone((cx, cy), geometry)
    assert is_position_in_approach_zone((cx + APPROACH_ZONE_RADIUS, cy), geometry)
    assert not is_position_in_approach_zone(
        (cx + APPROACH_ZONE_RADIUS + 1.0, cy), geometry)
    assert ObservationManager.is_in_approach_zone((cx, cy))


def test_ldm_and_legacy_negotiator_share_authoritative_center():
    geometry = get_intersection_geometry()
    assert LocalDynamicMap._distance_to_center(geometry.center_xy) == 0.0
    manager = NegotiationManager()
    assert manager.intersection_geometry is geometry
    assert manager.calculate_urgency({"pos": geometry.center_xy}) == 1.0


class _Node:
    def __init__(self, identity): self.identity = identity
    def getID(self): return self.identity
    def getCoord(self): return (0.0, 0.0)


class _Edge:
    def __init__(self, source, target): self.source, self.target = source, target
    def getFromNode(self): return self.source
    def getToNode(self): return self.target


class _Lane:
    def __init__(self, edge): self.edge = edge
    def getEdge(self): return self.edge


def _fake_manager(path_specs):
    lanes, paths, nodes = {}, {}, {}
    for path_id, incoming_target, outgoing_source in path_specs:
        nodes.setdefault(incoming_target, _Node(incoming_target))
        nodes.setdefault(outgoing_source, _Node(outgoing_source))
        incoming, outgoing = f"{path_id}_in", f"{path_id}_out"
        lanes[incoming] = _Lane(_Edge(_Node("outside"), nodes[incoming_target]))
        lanes[outgoing] = _Lane(_Edge(nodes[outgoing_source], _Node("outside")))
        paths[path_id] = SimpleNamespace(
            incoming_lane_id=incoming, outgoing_lane_id=outgoing)
    network = SimpleNamespace(
        getLane=lanes.__getitem__, getNode=nodes.__getitem__,
        _location={"netOffset": "0,0", "convBoundary": "0,0,1,1",
                   "origBoundary": "0,0,1,1", "projParameter": "!"})
    return SimpleNamespace(paths=paths, network=network)


def test_inconsistent_path_junction_is_rejected():
    with pytest.raises(IntersectionGeometryError,
                       match="MOVEMENT_PATH_JUNCTION_INCONSISTENT"):
        derive_intersection_geometry(_fake_manager((("P", "A", "B"),)))


def test_ambiguous_common_junction_is_rejected():
    with pytest.raises(IntersectionGeometryError,
                       match="INTERSECTION_JUNCTION_IDENTITY_AMBIGUOUS"):
        derive_intersection_geometry(_fake_manager(
            (("P", "A", "A"), ("Q", "B", "B"))))
