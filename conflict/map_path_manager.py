"""Discover legal intersection movement paths from a compiled SUMO network."""

import math

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

    def _connection_shape(self, connection):
        lane_id = connection.getViaLaneID()
        points = []
        visited = set()
        while lane_id and lane_id not in visited:
            visited.add(lane_id)
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
        return tuple((float(x), float(y)) for x, y in points)

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
                    geometry = self._connection_shape(connection)
                    if len(geometry) < 2 or not all(
                        math.isfinite(value) for point in geometry for value in point
                    ):
                        raise ValueError(f"Invalid geometry for lane {lane.getID()}")
                    path_id = self._stable_path_id(lane.getID(), manoeuvre)
                    path = MovementPath(
                        path_id, lane.getID(), connection.getToLane().getID(),
                        manoeuvre, geometry,
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
