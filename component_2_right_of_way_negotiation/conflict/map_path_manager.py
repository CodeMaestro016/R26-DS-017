"""Discover legal intersection movement paths from a compiled SUMO network."""

# Import math for use in this module.
import math

# Import LineString, Point from shapely.geometry for the operations below.
from shapely.geometry import LineString, Point

# Attempt the enclosed operations and route matching exceptions to the handlers below.
try:
    # Import sumolib for use in this module.
    import sumolib
# Handle ImportError as error using the recovery steps below.
except ImportError as error:  # pragma: no cover - installation failure path
    # Raise ImportError with the text "Conflict-map loading requires SUMO's official sumolib Python..." to stop
    # this execution path.
    raise ImportError(
        "Conflict-map loading requires SUMO's official sumolib Python package."
    # Evaluate error as part of the enclosing expression.
    ) from error

# Import SUMO_NETWORK_FILE from config for the operations below.
from config import SUMO_NETWORK_FILE
# Import MovementPath from .models for the operations below.
from .models import MovementPath


# Build a stable catalogue from lane connections and internal shapes.
# Instances expose the attributes and methods implemented in this class.
class MapPathManager:
    """Build a stable catalogue from lane connections and internal shapes."""

    # Set DIRECTION_TO_MANOEUVRE to a dictionary containing l, r, s.
    DIRECTION_TO_MANOEUVRE = {"l": "LEFT", "r": "RIGHT", "s": "STRAIGHT"}

    # Initialize the instance attributes and collaborators used by the operations below.
    # Input network_file: the supplied network file.
    # Output: no explicit value; normal completion returns None.
    # Processing: iterate over the relevant records.
    def __init__(self, network_file=SUMO_NETWORK_FILE):
        # Set self.network_file to a string built from network_file.
        self.network_file = str(network_file)
        # Set self.network to the result of sumolib.net.readNet(self.network_file).
        self.network = sumolib.net.readNet(self.network_file, withInternal=True)
        # Set self.paths to the result of self._build_paths().
        self.paths = self._build_paths()
        # Set self.paths_by_lane to an empty dictionary.
        self.paths_by_lane = {}
        # Iterate over values from self.paths, binding each item to path.
        for path in self.paths.values():
            # Append path to self.paths_by_lane.setdefault(path.incoming_lane_id, {}).setdefault(path.manoeuvre,
            # []).
            self.paths_by_lane.setdefault(path.incoming_lane_id, {}).setdefault(
                # Supply path.manoeuvre to self.paths_by_lane.setdefault(path.incoming_lane_id, {}).setdefault.
                path.manoeuvre, []
            # Supply path to self.paths_by_lane.setdefault(path.incoming_lane_id, {}).setdefault(path.manoeuvre,
            # []).append.
            ).append(path)
        # Iterate over values from self.paths_by_lane, binding each item to manoeuvres.
        for manoeuvres in self.paths_by_lane.values():
            # Iterate over key/value pairs from manoeuvres, binding each item to (manoeuvre, paths).
            for manoeuvre, paths in manoeuvres.items():
                # Set manoeuvres[manoeuvre] to a tuple built from the sorted values from paths.
                manoeuvres[manoeuvre] = tuple(
                    # Declare item as input parameter.
                    sorted(paths, key=lambda item: item.path_id)
                )

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Stable path id using the inputs and processing steps below.
    # Input incoming_lane_id: the supplied incoming lane id.
    # Input manoeuvre: the supplied manoeuvre.
    # Output: formatted text built from the embedded values.
    def _stable_path_id(incoming_lane_id, manoeuvre):
        # Return formatted text built from the embedded values to the caller.
        return f"{incoming_lane_id.upper()}_{manoeuvre}"

    # Connection geometry using the inputs and processing steps below.
    # Input connection: the supplied connection.
    # Output: a tuple containing a tuple built from a lazy sequence of a tuple containing float(x), float(y) for
    # (x, y) in points, a tuple...
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    def _connection_geometry(self, connection):
        # Set lane_id to the result of connection.getViaLaneID().
        lane_id = connection.getViaLaneID()
        # Set points to an empty list.
        points = []
        # Set internal_lane_ids to an empty list.
        internal_lane_ids = []
        # Set visited to an empty set.
        visited = set()
        # Repeat the following steps while lane_id and lane_id does not belong to visited.
        while lane_id and lane_id not in visited:
            # Add lane_id to visited.
            visited.add(lane_id)
            # Append lane_id to internal_lane_ids.
            internal_lane_ids.append(lane_id)
            # Set lane to the result of self.network.getLane(lane_id).
            lane = self.network.getLane(lane_id)
            # Set shape to the result of lane.getShape().
            shape = lane.getShape()
            # Extend points with shape when the negation of points, otherwise shape sliced by 1:.
            points.extend(shape if not points else shape[1:])
            # Set outgoing to the result of lane.getOutgoing().
            outgoing = lane.getOutgoing()
            # Run this branch when the negation of outgoing.
            if not outgoing:
                # Leave the nearest enclosing loop immediately.
                break
            # Set next_connection to outgoing at 0.
            next_connection = outgoing[0]
            # Run this branch when the result of next_connection.getViaLaneID().
            if next_connection.getViaLaneID():
                # Set lane_id to the result of next_connection.getViaLaneID().
                lane_id = next_connection.getViaLaneID()
            # Run this alternative branch when the preceding branch does not apply.
            else:
                # Leave the nearest enclosing loop immediately.
                break
        # Return a tuple containing a tuple built from a lazy sequence of a tuple containing float(x), float(y)
        # for (x, y) in points, a tuple... to the caller.
        return (
            # Include a tuple built from a lazy sequence of a tuple containing a floating-point number built from
            # x, a floating-point number built from y for (x, y) in points in this tuple.
            tuple((float(x), float(y)) for x, y in points),
            # Include a tuple built from internal_lane_ids in this tuple.
            tuple(internal_lane_ids),
        )

    # Build paths using the inputs and processing steps below.
    # Output: a dictionary built from the sorted values from key/value pairs from discovered.
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    def _build_paths(self):
        # Set discovered to an empty dictionary.
        discovered = {}
        # Iterate over the sorted values from the result of self.network.getEdges(), binding each item to edge.
        for edge in sorted(self.network.getEdges(), key=lambda item: item.getID()):
            # Run this branch when the result of edge.isSpecial() or the negation of the result of
            # edge.getToNode().getIncoming().
            if edge.isSpecial() or not edge.getToNode().getIncoming():
                # Skip the rest of this loop iteration and process the next item.
                continue
            # Iterate over the result of edge.getLanes(), binding each item to lane.
            for lane in edge.getLanes():
                # Iterate over the result of lane.getOutgoing(), binding each item to connection.
                for connection in lane.getOutgoing():
                    # Set manoeuvre to connection.getDirection() from self.DIRECTION_TO_MANOEUVRE; use None if
                    # absent.
                    manoeuvre = self.DIRECTION_TO_MANOEUVRE.get(
                        # Supply the result of connection.getDirection() to self.DIRECTION_TO_MANOEUVRE.get.
                        connection.getDirection()
                    )
                    # Run this branch when manoeuvre is the same object as None or the negation of the result of
                    # connection.getViaLaneID().
                    if manoeuvre is None or not connection.getViaLaneID():
                        # Skip the rest of this loop iteration and process the next item.
                        continue
                    # Set (geometry, internal_lane_ids) to the result of self._connection_geometry(connection).
                    geometry, internal_lane_ids = self._connection_geometry(
                        # Supply connection to self._connection_geometry.
                        connection
                    )
                    # Run this branch when the number of entries in geometry is less than 2 or the negation of
                    # whether every item is true in a lazy sequence of math.isfinite(value) for point in geometry.
                    if len(geometry) < 2 or not all(
                        # Evaluate whether value contains finite numeric values as part of the enclosing
                        # expression.
                        math.isfinite(value) for point in geometry for value in point
                    ):
                        # Raise ValueError with formatted text built from the embedded values to stop this
                        # execution path.
                        raise ValueError(f"Invalid geometry for lane {lane.getID()}")
                    # Set path_id to the result of self._stable_path_id(the result of lane.getID(), manoeuvre).
                    path_id = self._stable_path_id(lane.getID(), manoeuvre)
                    # Set path to the result of MovementPath(path_id, the result of lane.getID(), the result of
                    # connection.getToLane().getID(), manoeuvre,...).
                    path = MovementPath(
                        # Supply the result of connection.getToLane().getID() to MovementPath.
                        path_id, lane.getID(), connection.getToLane().getID(),
                        # Supply internal_lane_ids to MovementPath.
                        manoeuvre, geometry, internal_lane_ids,
                    )
                    # Call self._register_path with the supplied arguments.
                    self._register_path(discovered, path)
        # Return a dictionary built from the sorted values from key/value pairs from discovered to the caller.
        return dict(sorted(discovered.items()))

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Register path using the inputs and processing steps below.
    # Input discovered: the supplied discovered.
    # Input path: the path or path object supplied by the caller.
    # Output: no explicit value; normal completion returns None.
    # Processing: select branches using the stated conditions.
    def _register_path(discovered, path):
        # Run this branch when path.path_id belongs to discovered.
        if path.path_id in discovered:
            # Set existing to discovered at path.path_id.
            existing = discovered[path.path_id]
            # Raise ValueError with formatted text built from the embedded values to stop this execution path.
            raise ValueError(
                # Supply formatted text built from the embedded values to ValueError.
                f"Duplicate movement path ID {path.path_id!r} for "
                # Evaluate {existing.incoming_lane_id!r} as part of the enclosing expression.
                f"{existing.incoming_lane_id!r} and {path.incoming_lane_id!r}."
            )
        # Set discovered[path.path_id] to path.
        discovered[path.path_id] = path

    # Return a network-derived, human-readable movement catalogue.
    # Output: a tuple built from a lazy sequence of a dictionary containing path_id, incoming_lane, outgoing_lane,
    # manoeuvre, geometry_point_count for path in values from self.paths.
    def catalogue_rows(self):
        """Return a network-derived, human-readable movement catalogue."""
        # Return a tuple built from a lazy sequence of a dictionary containing path_id, incoming_lane,
        # outgoing_lane, manoeuvre, geometry_point_count for path in values from self.paths to the caller.
        return tuple({
            # Store path.path_id under 'path_id'.
            "path_id": path.path_id,
            # Store path.incoming_lane_id under 'incoming_lane'.
            "incoming_lane": path.incoming_lane_id,
            # Store path.outgoing_lane_id under 'outgoing_lane'.
            "outgoing_lane": path.outgoing_lane_id,
            # Store path.manoeuvre under 'manoeuvre'.
            "manoeuvre": path.manoeuvre,
            # Store the number of entries in path.centerline_geometry under 'geometry_point_count'.
            "geometry_point_count": len(path.centerline_geometry),
        # Evaluate values from self.paths as part of the enclosing expression.
        } for path in self.paths.values())

    # Apply property as a decorator to configure the following definition.
    @property
    # Incoming lane ids using the inputs and processing steps below.
    # Output: an immutable set built from self.paths_by_lane.
    def incoming_lane_ids(self):
        # Return an immutable set built from self.paths_by_lane to the caller.
        return frozenset(self.paths_by_lane)

    # Feasible paths using the inputs and processing steps below.
    # Input lane_id: the supplied lane id.
    # Output: a dictionary built from lane_id from self.paths_by_lane; use an empty dictionary if absent.
    def feasible_paths(self, lane_id):
        # Return a dictionary built from lane_id from self.paths_by_lane; use an empty dictionary if absent to the
        # caller.
        return dict(self.paths_by_lane.get(lane_id, {}))

    # Resolve path using the inputs and processing steps below.
    # Input lane_id: the supplied lane id.
    # Input manoeuvre: the supplied manoeuvre.
    # Output: paths at 0 when the number of entries in paths equals 1, otherwise None.
    def resolve_path(self, lane_id, manoeuvre):
        # Set paths to manoeuvre from self.paths_by_lane.get(lane_id, {}); use an empty tuple if absent.
        paths = self.paths_by_lane.get(lane_id, {}).get(manoeuvre, ())
        # Return paths at 0 when the number of entries in paths equals 1, otherwise None to the caller.
        return paths[0] if len(paths) == 1 else None

    # Classify source approaches from exact static incoming geometry.
    # Input ego_path_id: the supplied ego path id.
    # Input target_path_id: the supplied target path id.
    # Output: return the value selected by the matching return branch below.
    # Processing: select branches using the stated conditions.
    def approach_relation(self, ego_path_id, target_path_id):
        """Classify source approaches from exact static incoming geometry.

        Incoming direction vectors point toward their common junction. For
        this validated four-leg topology, parallel vectors mean the same
        approach, antiparallel vectors mean oncoming, and the sign of their
        2-D cross product distinguishes right from left. No angular threshold
        or live vehicle position participates in the classification.
        """
        # Set ego to ego_path_id from self.paths; use None if absent.
        ego = self.paths.get(ego_path_id)
        # Set target to target_path_id from self.paths; use None if absent.
        target = self.paths.get(target_path_id)
        # Run this branch when ego is the same object as None or target is the same object as None.
        if ego is None or target is None:
            # Return None to the caller.
            return None
        # Run this branch when ego.incoming_lane_id equals target.incoming_lane_id.
        if ego.incoming_lane_id == target.incoming_lane_id:
            # Return the text 'SAME_APPROACH' to the caller.
            return "SAME_APPROACH"

        # Set ego_vector to the result of self._incoming_direction(ego.incoming_lane_id).
        ego_vector = self._incoming_direction(ego.incoming_lane_id)
        # Set target_vector to the result of self._incoming_direction(target.incoming_lane_id).
        target_vector = self._incoming_direction(target.incoming_lane_id)
        # Set cross to ego_vector at 0 multiplied by target_vector at 1 minus ego_vector at 1 multiplied by
        # target_vector at 0.
        cross = ego_vector[0] * target_vector[1] - ego_vector[1] * target_vector[0]
        # Set dot to ego_vector at 0 multiplied by target_vector at 0 plus ego_vector at 1 multiplied by
        # target_vector at 1.
        dot = ego_vector[0] * target_vector[0] + ego_vector[1] * target_vector[1]
        # Set tolerance to the result of math.ulp(the maximum of 1.0, the unpacked values from (abs(value) for
        # value in (*ego_vector, *target_vector))) multiplied by 16.
        tolerance = math.ulp(max(1.0, *(abs(value) for value in (*ego_vector, *target_vector)))) * 16
        # Run this branch when the absolute value of cross is at most tolerance.
        if abs(cross) <= tolerance:
            # Return the text 'SAME_APPROACH' when dot is greater than 0.0, otherwise the text 'ONCOMING' to the
            # caller.
            return "SAME_APPROACH" if dot > 0.0 else "ONCOMING"
        # Return the text 'RIGHT' when cross is greater than 0.0, otherwise the text 'LEFT' to the caller.
        return "RIGHT" if cross > 0.0 else "LEFT"

    # Incoming direction using the inputs and processing steps below.
    # Input lane_id: the supplied lane id.
    # Output: a tuple containing vector at 0 divided by magnitude, vector at 1 divided by magnitude.
    # Processing: select branches using the stated conditions.
    def _incoming_direction(self, lane_id):
        # Set shape to the result of self.network.getLane(lane_id).getShape().
        shape = self.network.getLane(lane_id).getShape()
        # Run this branch when the number of entries in shape is less than 2.
        if len(shape) < 2:
            # Raise ValueError with formatted text built from the embedded values to stop this execution path.
            raise ValueError(f"Incoming lane {lane_id!r} lacks direction geometry")
        # Set (start, end) to a tuple containing shape at 0, shape at -1.
        start, end = shape[0], shape[-1]
        # Set vector to a tuple containing a floating-point number built from end at 0 minus start at 0, a
        # floating-point number built from end at 1...
        vector = (float(end[0] - start[0]), float(end[1] - start[1]))
        # Set magnitude to the result of math.hypot(the unpacked values from vector).
        magnitude = math.hypot(*vector)
        # Run this branch when magnitude equals 0.0.
        if magnitude == 0.0:
            # Raise ValueError with formatted text built from the embedded values to stop this execution path.
            raise ValueError(f"Incoming lane {lane_id!r} has zero-length direction")
        # Return a tuple containing vector at 0 divided by magnitude, vector at 1 divided by magnitude to the
        # caller.
        return vector[0] / magnitude, vector[1] / magnitude

    # Group paths supported by current lane membership, without routes.
    # Input lane_id: the supplied lane id.
    # Output: a dictionary of manoeuvre mapped to a tuple built from the sorted values from paths for (manoeuvre,
    # paths) in key/value pairs from compatible.
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    def paths_compatible_with_observed_lane(self, lane_id):
        """Group paths supported by current lane membership, without routes."""
        # Set compatible to an empty dictionary.
        compatible = {}
        # Iterate over values from self.paths, binding each item to path.
        for path in self.paths.values():
            # Run this branch when lane_id equals path.incoming_lane_id or lane_id belongs to
            # path.internal_lane_ids or lane_id equals path.outgoing_lane_id.
            if (lane_id == path.incoming_lane_id
                    # Evaluate lane_id belongs to path.internal_lane_ids as part of the enclosing expression.
                    or lane_id in path.internal_lane_ids
                    # Evaluate lane_id equals path.outgoing_lane_id as part of the enclosing expression.
                    or lane_id == path.outgoing_lane_id):
                # Append path to compatible.setdefault(path.manoeuvre, []).
                compatible.setdefault(path.manoeuvre, []).append(path)
        # Return a dictionary of manoeuvre mapped to a tuple built from the sorted values from paths for
        # (manoeuvre, paths) in key/value pairs from compatible to the caller.
        return {
            # Declare item as input parameter.
            manoeuvre: tuple(sorted(paths, key=lambda item: item.path_id))
            # Evaluate key/value pairs from compatible as part of the enclosing expression.
            for manoeuvre, paths in compatible.items()
        }

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Lane belongs to path using the inputs and processing steps below.
    # Input lane_id: the supplied lane id.
    # Input path: the path or path object supplied by the caller.
    # Output: lane_id equals path.incoming_lane_id or lane_id belongs to path.internal_lane_ids or lane_id equals
    # path.outgoing_lane_id.
    def lane_belongs_to_path(lane_id, path):
        # Return lane_id equals path.incoming_lane_id or lane_id belongs to path.internal_lane_ids or lane_id
        # equals path.outgoing_lane_id to the caller.
        return (lane_id == path.incoming_lane_id
                # Evaluate lane_id belongs to path.internal_lane_ids as part of the enclosing expression.
                or lane_id in path.internal_lane_ids
                # Evaluate lane_id equals path.outgoing_lane_id as part of the enclosing expression.
                or lane_id == path.outgoing_lane_id)

    # Resolve observed front-bumper progress in a movement coordinate.
    # Input track: the supplied track.
    # Input path: the path or path object supplied by the caller.
    # Output: return the value selected by the matching return branch below.
    # Processing: select branches using the stated conditions, then handle the specified errors.
    def resolve_front_bumper_path_progress(self, track, path):
        """Resolve observed front-bumper progress in a movement coordinate.

        ``s=0`` is the incoming-lane end and the first point of the internal
        movement centerline. Incoming progress is negative. Internal progress
        is projection onto that exact centerline. Outgoing progress continues
        from centerline length using SUMO's front-bumper lane position.
        """
        # Run this branch when whether path has type str.
        if isinstance(path, str):
            # Set path to self.paths at path.
            path = self.paths[path]
        # Set lane_id to 'lane_id' from track; use None if absent.
        lane_id = track.get("lane_id")
        # Run this branch when lane_id equals path.incoming_lane_id.
        if lane_id == path.incoming_lane_id:
            # Attempt the enclosed operations and route matching exceptions to the handlers below.
            try:
                # Set lane_position to a floating-point number built from track at 'lane_position'.
                lane_position = float(track["lane_position"])
                # Set lane_length to a floating-point number built from track at 'lane_length'.
                lane_length = float(track["lane_length"])
            # Handle (KeyError, TypeError, ValueError) using the recovery steps below.
            except (KeyError, TypeError, ValueError):
                # Return a tuple containing None, None, the text 'UNRESOLVED_PATH_PROGRESS' to the caller.
                return None, None, "UNRESOLVED_PATH_PROGRESS"
            # Run this branch when the negation of whether lane_position contains finite numeric values or the
            # negation of whether lane_length contains finite numeric values.
            if not math.isfinite(lane_position) or not math.isfinite(lane_length):
                # Return a tuple containing None, None, the text 'UNRESOLVED_PATH_PROGRESS' to the caller.
                return None, None, "UNRESOLVED_PATH_PROGRESS"
            # Set remaining to the maximum of 0.0, lane_length minus lane_position.
            remaining = max(0.0, lane_length - lane_position)
            # Return a tuple containing the negative of remaining, the text 'INCOMING_LANE', None to the caller.
            return -remaining, "INCOMING_LANE", None
        # Run this branch when lane_id belongs to path.internal_lane_ids.
        if lane_id in path.internal_lane_ids:
            # Attempt the enclosed operations and route matching exceptions to the handlers below.
            try:
                # Set (x, y) to the result of map(float, track at 'position').
                x, y = map(float, track["position"])
            # Handle (KeyError, TypeError, ValueError) using the recovery steps below.
            except (KeyError, TypeError, ValueError):
                # Return a tuple containing None, None, the text 'UNRESOLVED_PATH_PROGRESS' to the caller.
                return None, None, "UNRESOLVED_PATH_PROGRESS"
            # Run this branch when the negation of whether x contains finite numeric values or the negation of
            # whether y contains finite numeric values.
            if not math.isfinite(x) or not math.isfinite(y):
                # Return a tuple containing None, None, the text 'UNRESOLVED_PATH_PROGRESS' to the caller.
                return None, None, "UNRESOLVED_PATH_PROGRESS"
            # Set progress to the result of LineString(path.centerline_geometry).project(the result of Point(x,
            # y)).
            progress = LineString(path.centerline_geometry).project(Point(x, y))
            # Return a tuple containing a floating-point number built from progress, the text
            # 'INTERNAL_PATH_GEOMETRY', None to the caller.
            return float(progress), "INTERNAL_PATH_GEOMETRY", None
        # Run this branch when lane_id equals path.outgoing_lane_id.
        if lane_id == path.outgoing_lane_id:
            # Attempt the enclosed operations and route matching exceptions to the handlers below.
            try:
                # Set lane_position to a floating-point number built from track at 'lane_position'.
                lane_position = float(track["lane_position"])
            # Handle (KeyError, TypeError, ValueError) using the recovery steps below.
            except (KeyError, TypeError, ValueError):
                # Return a tuple containing None, None, the text 'UNRESOLVED_PATH_PROGRESS' to the caller.
                return None, None, "UNRESOLVED_PATH_PROGRESS"
            # Run this branch when the negation of whether lane_position contains finite numeric values.
            if not math.isfinite(lane_position):
                # Return a tuple containing None, None, the text 'UNRESOLVED_PATH_PROGRESS' to the caller.
                return None, None, "UNRESOLVED_PATH_PROGRESS"
            # Set path_length to LineString(path.centerline_geometry).length.
            path_length = LineString(path.centerline_geometry).length
            # Return a tuple containing path_length plus the maximum of 0.0, lane_position, the text
            # 'OUTGOING_LANE', None to the caller.
            return path_length + max(0.0, lane_position), "OUTGOING_LANE", None

        # Set known_internal to a set of member for candidate in values from self.paths.
        known_internal = {
            # Evaluate values from self.paths as part of the enclosing expression.
            member for candidate in self.paths.values()
            # Evaluate candidate.internal_lane_ids as part of the enclosing expression.
            for member in candidate.internal_lane_ids
        }
        # Set known_outgoing to a set of candidate.outgoing_lane_id for candidate in values from self.paths.
        known_outgoing = {
            # Evaluate candidate.outgoing_lane_id as part of the enclosing expression.
            candidate.outgoing_lane_id for candidate in self.paths.values()
        }
        # Run this branch when lane_id belongs to known_internal or lane_id belongs to known_outgoing.
        if lane_id in known_internal or lane_id in known_outgoing:
            # Return a tuple containing None, None, the text 'INCOMPATIBLE_WITH_OBSERVED_LANE' to the caller.
            return None, None, "INCOMPATIBLE_WITH_OBSERVED_LANE"
        # Return a tuple containing None, None, the text 'UNRESOLVED_PATH_PROGRESS' to the caller.
        return None, None, "UNRESOLVED_PATH_PROGRESS"
