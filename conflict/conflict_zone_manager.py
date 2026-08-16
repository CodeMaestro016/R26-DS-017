"""Physical swept-envelope conflict zones for SUMO movement paths.

The conflict-zone representation follows Liu et al. (2018), DOI
10.1109/TIV.2017.2788209; graph encoding is conceptually supported by Chen et
al. (2022), DOI 10.1109/TITS.2022.3182403, and the AIM taxonomy of Zhong,
Nejad, and Lee (2020). The exact Shapely implementation is project-specific.

The corrected decision is Z_ij = P_i intersect P_j, where each P is the path
centreline buffered by exactly half the actual vehicle width. Centreline
intersection is not required. Flat end caps prevent extension beyond the map
path endpoints; round joins are the standard continuous offset around bends.
Neither choice adds a safety margin. Future covariance can expand envelopes
statistically; no guessed uncertainty distance is used here.

One path-pair zone may be Polygon, MultiPolygon, or GeometryCollection. It is
retained as one deterministic relationship without discarding components.
"""

from functools import lru_cache
from itertools import combinations_with_replacement

try:
    from shapely import BufferCapStyle, BufferJoinStyle
    from shapely.geometry import LineString, Point
except ImportError as error:  # pragma: no cover
    raise ImportError("Conflict geometry requires Shapely 2 or newer.") from error

from config import AV_WIDTH_METERS
from .models import ConflictRelationship


class ConflictZoneManager:
    """Separate lane topology from physical occupied-envelope intersection."""

    COORDINATED_TOPOLOGIES = frozenset({"POTENTIAL_CROSSING", "MERGING"})

    def __init__(self, path_manager, catalogue_vehicle_width=AV_WIDTH_METERS):
        self.path_manager = path_manager
        self.catalogue_vehicle_width = float(catalogue_vehicle_width)
        if self.catalogue_vehicle_width <= 0.0:
            raise ValueError("catalogue vehicle width must be positive")
        self.lines = {
            path_id: LineString(path.centerline_geometry)
            for path_id, path in path_manager.paths.items()
        }
        pairs = list(combinations_with_replacement(sorted(self.lines), 2))
        candidates = [pair for pair in pairs if self._topology(*pair) in
                      self.COORDINATED_TOPOLOGIES]
        self._candidate_zone_ids = {
            frozenset(pair): f"CZ_CANDIDATE_{index:03d}"
            for index, pair in enumerate(candidates, start=1)
        }
        provisional = {
            frozenset(pair): self.relationship_for_widths(
                pair[0], self.catalogue_vehicle_width,
                pair[1], self.catalogue_vehicle_width,
            ) for pair in pairs
        }
        coordinated_pairs = sorted(
            (tuple(sorted(key)) for key, value in provisional.items()
             if value.coordinated_conflict)
        )
        compact_ids = {
            frozenset(pair): f"CZ_{index:03d}"
            for index, pair in enumerate(coordinated_pairs, start=1)
        }
        for pair in candidates:
            key = frozenset(pair)
            compact_ids.setdefault(
                key, "CZ_PATHPAIR__" + "__".join(sorted(pair))
            )
        self._candidate_zone_ids = compact_ids
        self.relationships = {
            frozenset(pair): self.relationship_for_widths(
                pair[0], self.catalogue_vehicle_width,
                pair[1], self.catalogue_vehicle_width,
            ) for pair in pairs
        }
        self.zone_geometries = {
            relationship.conflict_zone_id: self.zone_record(
                relationship.first_path_id, self.catalogue_vehicle_width,
                relationship.second_path_id, self.catalogue_vehicle_width,
            )
            for relationship in self.relationships.values()
            if relationship.coordinated_conflict
        }

    def _topology(self, first_path_id, second_path_id):
        first = self.path_manager.paths[first_path_id]
        second = self.path_manager.paths[second_path_id]
        if first.path_id == second.path_id:
            return "SAME_PATH"
        if first.incoming_lane_id == second.incoming_lane_id:
            return "DIVERGING"
        if first.outgoing_lane_id == second.outgoing_lane_id:
            return "MERGING"
        return "POTENTIAL_CROSSING"

    @staticmethod
    def _validate_width(width):
        value = float(width)
        if value <= 0.0:
            raise ValueError("vehicle width must be positive")
        return value

    @lru_cache(maxsize=None)
    def physical_intersection(self, first_path_id, first_width,
                              second_path_id, second_width):
        first_width = self._validate_width(first_width)
        second_width = self._validate_width(second_width)
        first = self.lines[first_path_id].buffer(
            first_width / 2.0, cap_style=BufferCapStyle.flat,
            join_style=BufferJoinStyle.round,
        )
        second = self.lines[second_path_id].buffer(
            second_width / 2.0, cap_style=BufferCapStyle.flat,
            join_style=BufferJoinStyle.round,
        )
        return first.intersection(second)

    def relationship_for_widths(self, first_path_id, first_width,
                                second_path_id, second_width):
        topology = self._topology(first_path_id, second_path_id)
        overlap = self.physical_intersection(
            first_path_id, first_width, second_path_id, second_width
        )
        physical_overlap = not overlap.is_empty
        coordinated = topology in self.COORDINATED_TOPOLOGIES and physical_overlap
        conflict_type = (
            "CROSSING" if topology == "POTENTIAL_CROSSING" and coordinated
            else topology if topology in {"SAME_PATH", "DIVERGING", "MERGING"}
            else "NO_CONFLICT"
        )
        return ConflictRelationship(
            first_path_id, second_path_id,
            self._candidate_zone_ids.get(frozenset((first_path_id, second_path_id)))
            if coordinated else None,
            conflict_type, physical_overlap, coordinated,
            overlap.geom_type if physical_overlap else None,
        )

    def relationship(self, first_path_id, second_path_id):
        return self.relationships[frozenset((first_path_id, second_path_id))]

    def coordinated_conflict(self, first_path_id, first_width,
                             second_path_id, second_width):
        relationship = self.relationship_for_widths(
            first_path_id, first_width, second_path_id, second_width
        )
        if not relationship.coordinated_conflict:
            return relationship, None
        return relationship, self.physical_intersection(
            first_path_id, first_width, second_path_id, second_width
        )

    @staticmethod
    def _projected_interval(line, zone):
        occupied = line.intersection(zone)
        distances = []

        def collect(geometry):
            if geometry.geom_type in {"Point", "LineString", "LinearRing"}:
                distances.extend(
                    line.project(Point(x, y)) for x, y in geometry.coords
                )
            elif geometry.geom_type == "Polygon":
                collect(geometry.exterior)
                for ring in geometry.interiors:
                    collect(ring)
            elif hasattr(geometry, "geoms"):
                for component in geometry.geoms:
                    collect(component)

        # Swept envelopes can overlap between nearby centre lines without the
        # overlap polygon containing either centre line. In that valid case,
        # project the same authoritative overlap polygon onto the path. This
        # introduces neither a tolerance nor any additional geometry.
        collect(zone if occupied.is_empty else occupied)
        return (min(distances), max(distances)) if distances else None

    def zone_record(self, first_path_id, first_width,
                    second_path_id, second_width):
        relationship, zone = self.coordinated_conflict(
            first_path_id, first_width, second_path_id, second_width
        )
        if zone is None:
            return None
        first_line, second_line = self.lines[first_path_id], self.lines[second_path_id]
        return {
            "zone_id": relationship.conflict_zone_id,
            "first_path_id": first_path_id,
            "second_path_id": second_path_id,
            "conflict_type": relationship.conflict_type,
            "geometry": zone,
            "geometry_type": zone.geom_type,
            "first_path_distance_interval": self._projected_interval(first_line, zone),
            "second_path_distance_interval": self._projected_interval(second_line, zone),
        }

    def catalogue_rows(self):
        return tuple({
            "zone_id": item.conflict_zone_id or "",
            "first_path_id": item.first_path_id,
            "second_path_id": item.second_path_id,
            "topological_relationship": self._topology(
                item.first_path_id, item.second_path_id
            ),
            "conflict_type": item.conflict_type,
            "physical_overlap": item.physical_overlap,
            "coordinated_conflict": item.coordinated_conflict,
            "geometry_type": item.geometry_type or "",
        } for item in self.relationships.values())
