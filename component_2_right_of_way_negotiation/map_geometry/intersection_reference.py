"""Resolve the operational junction reference from compiled legal paths."""

# Import lru_cache from functools for the operations below.
from functools import lru_cache
# Import Decimal from decimal for the operations below.
from decimal import Decimal

# Import APPROACH_ZONE_RADIUS, SUMO_NETWORK_FILE from config for the operations below.
from config import APPROACH_ZONE_RADIUS, SUMO_NETWORK_FILE
# Import MapPathManager from conflict.map_path_manager for the operations below.
from conflict.map_path_manager import MapPathManager

# Import IntersectionGeometryContext from .models for the operations below.
from .models import IntersectionGeometryContext


# Set INTERSECTION_GEOMETRY_STATUS to the text 'DERIVED_FROM_COMPILED_SUMO_NETWORK'.
INTERSECTION_GEOMETRY_STATUS = "DERIVED_FROM_COMPILED_SUMO_NETWORK"
# Set MANUAL_INTERSECTION_CENTER_CONFIGURED to False.
MANUAL_INTERSECTION_CENTER_CONFIGURED = False
# Set MANUAL_NET_OFFSET_APPLICATION to False.
MANUAL_NET_OFFSET_APPLICATION = False


# Define IntersectionGeometryError to group the state and operations declared below.
# Base classes: ValueError.
# Instances expose the attributes and methods implemented in this class.
class IntersectionGeometryError(ValueError):
    # Keep this block syntactically valid without performing an operation.
    pass


# Numbers using the inputs and processing steps below.
# Input value: the supplied value.
# Input count: the supplied count.
# Output: parts.
# Processing: select branches using the stated conditions.
def _numbers(value, count):
    # Set parts to a tuple built from a lazy sequence of a floating-point number built from item for item in the
    # result of str(value).split(the text ',').
    parts = tuple(float(item) for item in str(value).split(","))
    # Run this branch when the number of entries in parts differs from count.
    if len(parts) != count:
        # Raise IntersectionGeometryError with the text 'COMPILED_NETWORK_LOCATION_METADATA_INVALID' to stop this
        # execution path.
        raise IntersectionGeometryError("COMPILED_NETWORK_LOCATION_METADATA_INVALID")
    # Return parts to the caller.
    return parts


# Require every discovered movement to traverse one common junction.
# Input path_manager: the supplied path manager.
# Output: the result of IntersectionGeometryContext(formatted text built from the embedded values, junction_id,
# center, the text...).
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def derive_intersection_geometry(path_manager):
    """Require every discovered movement to traverse one common junction."""
    # Set junction_ids to an empty set.
    junction_ids = set()
    # Set path_ids to a tuple built from the sorted values from path_manager.paths.
    path_ids = tuple(sorted(path_manager.paths))
    # Run this branch when the negation of path_ids.
    if not path_ids:
        # Raise IntersectionGeometryError with the text 'INTERSECTION_JUNCTION_IDENTITY_UNRESOLVED' to stop this
        # execution path.
        raise IntersectionGeometryError("INTERSECTION_JUNCTION_IDENTITY_UNRESOLVED")
    # Iterate over path_ids, binding each item to path_id.
    for path_id in path_ids:
        # Set path to path_manager.paths at path_id.
        path = path_manager.paths[path_id]
        # Set incoming_edge to the result of path_manager.network.getLane(path.incoming_lane_id).getEdge().
        incoming_edge = path_manager.network.getLane(
            # Supply path.incoming_lane_id to path_manager.network.getLane.
            path.incoming_lane_id).getEdge()
        # Set outgoing_edge to the result of path_manager.network.getLane(path.outgoing_lane_id).getEdge().
        outgoing_edge = path_manager.network.getLane(
            # Supply path.outgoing_lane_id to path_manager.network.getLane.
            path.outgoing_lane_id).getEdge()
        # Set incoming_destination to the result of incoming_edge.getToNode().
        incoming_destination = incoming_edge.getToNode()
        # Set outgoing_origin to the result of outgoing_edge.getFromNode().
        outgoing_origin = outgoing_edge.getFromNode()
        # Run this branch when the result of incoming_destination.getID() differs from the result of
        # outgoing_origin.getID().
        if incoming_destination.getID() != outgoing_origin.getID():
            # Raise IntersectionGeometryError with the text 'MOVEMENT_PATH_JUNCTION_INCONSISTENT' to stop this
            # execution path.
            raise IntersectionGeometryError("MOVEMENT_PATH_JUNCTION_INCONSISTENT")
        # Add the result of incoming_destination.getID() to junction_ids.
        junction_ids.add(incoming_destination.getID())
    # Run this branch when the negation of junction_ids.
    if not junction_ids:
        # Raise IntersectionGeometryError with the text 'INTERSECTION_JUNCTION_IDENTITY_UNRESOLVED' to stop this
        # execution path.
        raise IntersectionGeometryError("INTERSECTION_JUNCTION_IDENTITY_UNRESOLVED")
    # Run this branch when the number of entries in junction_ids differs from 1.
    if len(junction_ids) != 1:
        # Raise IntersectionGeometryError with the text 'INTERSECTION_JUNCTION_IDENTITY_AMBIGUOUS' to stop this
        # execution path.
        raise IntersectionGeometryError("INTERSECTION_JUNCTION_IDENTITY_AMBIGUOUS")
    # Set junction_id to the next item from the result of iter(junction_ids).
    junction_id = next(iter(junction_ids))
    # Set center to a tuple built from a lazy sequence of a floating-point number built from value for value in
    # the result of path_manager.network.getNode(junction_id).getCoord().
    center = tuple(float(value) for value in
                   # Evaluate the result of path_manager.network.getNode(junction_id).getCoord() as part of the
                   # enclosing expression.
                   path_manager.network.getNode(junction_id).getCoord())
    # Set location to a dictionary built from path_manager.network._location.
    location = dict(path_manager.network._location)
    # Set network_path to the result of SUMO_NETWORK_FILE.resolve().
    network_path = SUMO_NETWORK_FILE.resolve()
    # Return the result of IntersectionGeometryContext(formatted text built from the embedded values, junction_id,
    # center, the text...) to the caller.
    return IntersectionGeometryContext(
        # Supply formatted text built from the embedded values to IntersectionGeometryContext.
        f"{network_path.name}:{network_path.stat().st_size}", junction_id,
        # Supply center to IntersectionGeometryContext.
        center, "SUMO_COMPILED_NETWORK_XY_METERS",
        # Supply the result of _numbers(location at 'netOffset', 2) to IntersectionGeometryContext.
        _numbers(location["netOffset"], 2),
        # Supply the result of _numbers(location at 'convBoundary', 4) to IntersectionGeometryContext.
        _numbers(location["convBoundary"], 4),
        # Supply the result of _numbers(location at 'origBoundary', 4) to IntersectionGeometryContext.
        _numbers(location["origBoundary"], 4),
        # Supply location at 'projParameter' to IntersectionGeometryContext.
        location["projParameter"],
        # Supply path_ids to IntersectionGeometryContext.
        "COMMON_JUNCTION_FROM_LEGAL_MOVEMENT_PATHS", path_ids,
        # Store a string built from network_path under 'network_source'.
        {"network_source": str(network_path),
         "coordinate_source": "sumolib.net.Node.getCoord",
         "location_metadata_role": "PROVENANCE_ONLY",
         "manual_offset_application": "False"},
    )


# Apply lru_cache(maxsize=1) as a decorator to configure the following definition.
@lru_cache(maxsize=1)
# Get intersection geometry using the inputs and processing steps below.
# Output: the result of derive_intersection_geometry(the result of MapPathManager()).
def get_intersection_geometry():
    # Return the result of derive_intersection_geometry(the result of MapPathManager()) to the caller.
    return derive_intersection_geometry(MapPathManager())


# Is position in approach zone using the inputs and processing steps below.
# Input position: the supplied position.
# Input intersection_geometry: the supplied intersection geometry.
# Input approach_zone_radius: the supplied approach zone radius.
# Output: the sum of a lazy sequence of delta multiplied by delta for delta in deltas is at most radius multiplied
# by radius.
def is_position_in_approach_zone(position, intersection_geometry=None,
                                 # Declare approach_zone_radius as input parameter.
                                 approach_zone_radius=APPROACH_ZONE_RADIUS):
    # Set geometry to intersection_geometry or the result of get_intersection_geometry().
    geometry = intersection_geometry or get_intersection_geometry()
    # Decimal conversion from the public float representation preserves the
    # exact closed-boundary semantics of ``<=`` without adding a tolerance.
    # This matters for the test point ``cx + radius``, whose binary subtraction
    # can otherwise round one ULP outside the mathematically identical radius.
    # Set deltas to a tuple built from a lazy sequence of the result of Decimal(str(value)) minus the result of
    # Decimal(str(center)) for (value, center) in corresponding items paired from position, geometry.center_xy.
    deltas = tuple(Decimal(str(value)) - Decimal(str(center))
                   # Evaluate corresponding items paired from position, geometry.center_xy as part of the
                   # enclosing expression.
                   for value, center in zip(position, geometry.center_xy))
    # Set radius to the result of Decimal(a string built from approach_zone_radius).
    radius = Decimal(str(approach_zone_radius))
    # Return the sum of a lazy sequence of delta multiplied by delta for delta in deltas is at most radius
    # multiplied by radius to the caller.
    return sum(delta * delta for delta in deltas) <= radius * radius
