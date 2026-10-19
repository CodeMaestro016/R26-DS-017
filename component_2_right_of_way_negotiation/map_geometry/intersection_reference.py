"""Resolve the operational junction reference from compiled legal paths."""

from functools import lru_cache
from decimal import Decimal

from config import APPROACH_ZONE_RADIUS, SUMO_NETWORK_FILE
from conflict.map_path_manager import MapPathManager

from .models import IntersectionGeometryContext


INTERSECTION_GEOMETRY_STATUS = "DERIVED_FROM_COMPILED_SUMO_NETWORK"
MANUAL_INTERSECTION_CENTER_CONFIGURED = False
MANUAL_NET_OFFSET_APPLICATION = False


class IntersectionGeometryError(ValueError):
    pass


def _numbers(value, count):
    parts = tuple(float(item) for item in str(value).split(","))
    if len(parts) != count:
        raise IntersectionGeometryError("COMPILED_NETWORK_LOCATION_METADATA_INVALID")
    return parts


def derive_intersection_geometry(path_manager):
    """Require every discovered movement to traverse one common junction."""
    junction_ids = set()
    path_ids = tuple(sorted(path_manager.paths))
    if not path_ids:
        raise IntersectionGeometryError("INTERSECTION_JUNCTION_IDENTITY_UNRESOLVED")
    for path_id in path_ids:
        path = path_manager.paths[path_id]
        incoming_edge = path_manager.network.getLane(
            path.incoming_lane_id).getEdge()
        outgoing_edge = path_manager.network.getLane(
            path.outgoing_lane_id).getEdge()
        incoming_destination = incoming_edge.getToNode()
        outgoing_origin = outgoing_edge.getFromNode()
        if incoming_destination.getID() != outgoing_origin.getID():
            raise IntersectionGeometryError("MOVEMENT_PATH_JUNCTION_INCONSISTENT")
        junction_ids.add(incoming_destination.getID())
    if not junction_ids:
        raise IntersectionGeometryError("INTERSECTION_JUNCTION_IDENTITY_UNRESOLVED")
    if len(junction_ids) != 1:
        raise IntersectionGeometryError("INTERSECTION_JUNCTION_IDENTITY_AMBIGUOUS")
    junction_id = next(iter(junction_ids))
    center = tuple(float(value) for value in
                   path_manager.network.getNode(junction_id).getCoord())
    location = dict(path_manager.network._location)
    network_path = SUMO_NETWORK_FILE.resolve()
    return IntersectionGeometryContext(
        f"{network_path.name}:{network_path.stat().st_size}", junction_id,
        center, "SUMO_COMPILED_NETWORK_XY_METERS",
        _numbers(location["netOffset"], 2),
        _numbers(location["convBoundary"], 4),
        _numbers(location["origBoundary"], 4),
        location["projParameter"],
        "COMMON_JUNCTION_FROM_LEGAL_MOVEMENT_PATHS", path_ids,
        {"network_source": str(network_path),
         "coordinate_source": "sumolib.net.Node.getCoord",
         "location_metadata_role": "PROVENANCE_ONLY",
         "manual_offset_application": "False"},
    )


@lru_cache(maxsize=1)
def get_intersection_geometry():
    return derive_intersection_geometry(MapPathManager())


def is_position_in_approach_zone(position, intersection_geometry=None,
                                 approach_zone_radius=APPROACH_ZONE_RADIUS):
    geometry = intersection_geometry or get_intersection_geometry()
    # Decimal conversion from the public float representation preserves the
    # exact closed-boundary semantics of ``<=`` without adding a tolerance.
    # This matters for the test point ``cx + radius``, whose binary subtraction
    # can otherwise round one ULP outside the mathematically identical radius.
    deltas = tuple(Decimal(str(value)) - Decimal(str(center))
                   for value, center in zip(position, geometry.center_xy))
    radius = Decimal(str(approach_zone_radius))
    return sum(delta * delta for delta in deltas) <= radius * radius
