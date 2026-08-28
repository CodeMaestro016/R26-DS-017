"""Discover legal intersection movement paths from a compiled SUMO network."""

import math

from shapely.geometry import LineString, Point

try:
    import sumolib
except ImportError as error:  # pragma: no cover - installation failure path
    raise ImportError(
        "Conflict-map loading requires SUMO's official sumolib Python package."
    ) from error

from config import SUMO_NETWORK_FILE
from .models import MovementPath


class MapPathManager:
    """Build a stable catalogue from lane connections and internal shapes."""

    DIRECTION_TO_MANOEUVRE = {"l": "LEFT", "r": "RIGHT", "s": "STRAIGHT"}

    def __init__(self, network_file=SUMO_NETWORK_FILE):
        self.network_file = str(network_file)
        self.network = sumolib.net.readNet(self.network_file, withInternal=True)
        self.paths = self._build_paths()
        self.paths_by_lane = {}
        for path in self.paths.values():
            self.paths_by_lane.setdefault(path.incoming_lane_id, {}).setdefault(
                path.manoeuvre, []
            ).append(path)
        for manoeuvres in self.paths_by_lane.values():
            for manoeuvre, paths in manoeuvres.items():
                manoeuvres[manoeuvre] = tuple(
                    sorted(paths, key=lambda item: item.path_id)
                )

    @staticmethod
    def _stable_path_id(incoming_lane_id, manoeuvre):
        return f"{incoming_lane_id.upper()}_{manoeuvre}"

    def _connection_geometry(self, connection):
        lane_id = connection.getViaLaneID()
        points = []
        internal_lane_ids = []
        visited = set()
        while lane_id and lane_id not in visited:
            visited.add(lane_id)
            internal_lane_ids.append(lane_id)
            lane = self.network.getLane(lane_id)
            shape = lane.getShape()
            points.extend(shape if not points else shape[1:])
            outgoing = lane.getOutgoing()
            if not outgoing:
                break
            next_connection = outgoing[0]
            if next_connection.getViaLaneID():
                lane_id = next_connection.getViaLaneID()
            else:
                break
        return (
            tuple((float(x), float(y)) for x, y in points),
            tuple(internal_lane_ids),
        )

    def _build_paths(self):
        discovered = {}
        for edge in sorted(self.network.getEdges(), key=lambda item: item.getID()):
            if edge.isSpecial() or not edge.getToNode().getIncoming():
                continue
            for lane in edge.getLanes():
                for connection in lane.getOutgoing():
                    manoeuvre = self.DIRECTION_TO_MANOEUVRE.get(
                        connection.getDirection()
                    )
                    if manoeuvre is None or not connection.getViaLaneID():
                        continue
                    geometry, internal_lane_ids = self._connection_geometry(
                        connection
                    )
                    if len(geometry) < 2 or not all(
                        math.isfinite(value) for point in geometry for value in point
                    ):
                        raise ValueError(f"Invalid geometry for lane {lane.getID()}")
                    path_id = self._stable_path_id(lane.getID(), manoeuvre)
                    path = MovementPath(
                        path_id, lane.getID(), connection.getToLane().getID(),
                        manoeuvre, geometry, internal_lane_ids,
                    )
                    self._register_path(discovered, path)
        return dict(sorted(discovered.items()))

    @staticmethod
    def _register_path(discovered, path):
        if path.path_id in discovered:
            existing = discovered[path.path_id]
            raise ValueError(
                f"Duplicate movement path ID {path.path_id!r} for "
                f"{existing.incoming_lane_id!r} and {path.incoming_lane_id!r}."
            )
        discovered[path.path_id] = path

    def catalogue_rows(self):
        """Return a network-derived, human-readable movement catalogue."""
        return tuple({
            "path_id": path.path_id,
            "incoming_lane": path.incoming_lane_id,
            "outgoing_lane": path.outgoing_lane_id,
            "manoeuvre": path.manoeuvre,
            "geometry_point_count": len(path.centerline_geometry),
        } for path in self.paths.values())

    @property
    def incoming_lane_ids(self):
        return frozenset(self.paths_by_lane)

    def feasible_paths(self, lane_id):
        return dict(self.paths_by_lane.get(lane_id, {}))

    def resolve_path(self, lane_id, manoeuvre):
        paths = self.paths_by_lane.get(lane_id, {}).get(manoeuvre, ())
        return paths[0] if len(paths) == 1 else None

    def approach_relation(self, ego_path_id, target_path_id):
        """Classify source approaches from exact static incoming geometry.

        Incoming direction vectors point toward their common junction. For
        this validated four-leg topology, parallel vectors mean the same
        approach, antiparallel vectors mean oncoming, and the sign of their
        2-D cross product distinguishes right from left. No angular threshold
        or live vehicle position participates in the classification.
        """
        ego = self.paths.get(ego_path_id)
        target = self.paths.get(target_path_id)
        if ego is None or target is None:
            return None
        if ego.incoming_lane_id == target.incoming_lane_id:
            return "SAME_APPROACH"

        ego_vector = self._incoming_direction(ego.incoming_lane_id)
        target_vector = self._incoming_direction(target.incoming_lane_id)
        cross = ego_vector[0] * target_vector[1] - ego_vector[1] * target_vector[0]
        dot = ego_vector[0] * target_vector[0] + ego_vector[1] * target_vector[1]
        tolerance = math.ulp(max(1.0, *(abs(value) for value in (*ego_vector, *target_vector)))) * 16
        if abs(cross) <= tolerance:
            return "SAME_APPROACH" if dot > 0.0 else "ONCOMING"
        return "RIGHT" if cross > 0.0 else "LEFT"

    def _incoming_direction(self, lane_id):
        shape = self.network.getLane(lane_id).getShape()
        if len(shape) < 2:
            raise ValueError(f"Incoming lane {lane_id!r} lacks direction geometry")
        start, end = shape[0], shape[-1]
        vector = (float(end[0] - start[0]), float(end[1] - start[1]))
        magnitude = math.hypot(*vector)
        if magnitude == 0.0:
            raise ValueError(f"Incoming lane {lane_id!r} has zero-length direction")
        return vector[0] / magnitude, vector[1] / magnitude

    def paths_compatible_with_observed_lane(self, lane_id):
        """Group paths supported by current lane membership, without routes."""
        compatible = {}
        for path in self.paths.values():
            if (lane_id == path.incoming_lane_id
                    or lane_id in path.internal_lane_ids
                    or lane_id == path.outgoing_lane_id):
                compatible.setdefault(path.manoeuvre, []).append(path)
        return {
            manoeuvre: tuple(sorted(paths, key=lambda item: item.path_id))
            for manoeuvre, paths in compatible.items()
        }

    @staticmethod
    def lane_belongs_to_path(lane_id, path):
        return (lane_id == path.incoming_lane_id
                or lane_id in path.internal_lane_ids
                or lane_id == path.outgoing_lane_id)

    def resolve_front_bumper_path_progress(self, track, path):
        """Resolve observed front-bumper progress in a movement coordinate.

        ``s=0`` is the incoming-lane end and the first point of the internal
        movement centerline. Incoming progress is negative. Internal progress
        is projection onto that exact centerline. Outgoing progress continues
        from centerline length using SUMO's front-bumper lane position.
        """
        if isinstance(path, str):
            path = self.paths[path]
        lane_id = track.get("lane_id")
        if lane_id == path.incoming_lane_id:
            try:
                lane_position = float(track["lane_position"])
                lane_length = float(track["lane_length"])
            except (KeyError, TypeError, ValueError):
                return None, None, "UNRESOLVED_PATH_PROGRESS"
            if not math.isfinite(lane_position) or not math.isfinite(lane_length):
                return None, None, "UNRESOLVED_PATH_PROGRESS"
            remaining = max(0.0, lane_length - lane_position)
            return -remaining, "INCOMING_LANE", None
        if lane_id in path.internal_lane_ids:
            try:
                x, y = map(float, track["position"])
            except (KeyError, TypeError, ValueError):
                return None, None, "UNRESOLVED_PATH_PROGRESS"
            if not math.isfinite(x) or not math.isfinite(y):
                return None, None, "UNRESOLVED_PATH_PROGRESS"
            progress = LineString(path.centerline_geometry).project(Point(x, y))
            return float(progress), "INTERNAL_PATH_GEOMETRY", None
        if lane_id == path.outgoing_lane_id:
            try:
                lane_position = float(track["lane_position"])
            except (KeyError, TypeError, ValueError):
                return None, None, "UNRESOLVED_PATH_PROGRESS"
            if not math.isfinite(lane_position):
                return None, None, "UNRESOLVED_PATH_PROGRESS"
            path_length = LineString(path.centerline_geometry).length
            return path_length + max(0.0, lane_position), "OUTGOING_LANE", None

        known_internal = {
            member for candidate in self.paths.values()
            for member in candidate.internal_lane_ids
        }
        known_outgoing = {
            candidate.outgoing_lane_id for candidate in self.paths.values()
        }
        if lane_id in known_internal or lane_id in known_outgoing:
            return None, None, "INCOMPATIBLE_WITH_OBSERVED_LANE"
        return None, None, "UNRESOLVED_PATH_PROGRESS"
