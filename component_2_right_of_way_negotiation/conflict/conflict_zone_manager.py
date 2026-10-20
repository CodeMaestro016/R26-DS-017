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

# Import lru_cache from functools for the operations below.
from functools import lru_cache
# Import combinations_with_replacement from itertools for the operations below.
from itertools import combinations_with_replacement

# Attempt the enclosed operations and route matching exceptions to the handlers below.
try:
    # Import BufferCapStyle, BufferJoinStyle from shapely for the operations below.
    from shapely import BufferCapStyle, BufferJoinStyle
    # Import LineString, Point from shapely.geometry for the operations below.
    from shapely.geometry import LineString, Point
# Handle ImportError as error using the recovery steps below.
except ImportError as error:  # pragma: no cover
    # Raise ImportError with the text 'Conflict geometry requires Shapely 2 or newer.' to stop this execution
    # path.
    raise ImportError("Conflict geometry requires Shapely 2 or newer.") from error

# Import AV_WIDTH_METERS from config for the operations below.
from config import AV_WIDTH_METERS
# Import ConflictRelationship from .models for the operations below.
from .models import ConflictRelationship


# Separate lane topology from physical occupied-envelope intersection.
# Instances expose the attributes and methods implemented in this class.
class ConflictZoneManager:
    """Separate lane topology from physical occupied-envelope intersection."""

    # Set COORDINATED_TOPOLOGIES to an immutable set built from a set containing the text 'POTENTIAL_CROSSING',
    # the text 'MERGING'.
    COORDINATED_TOPOLOGIES = frozenset({"POTENTIAL_CROSSING", "MERGING"})

    # Initialize the instance attributes and collaborators used by the operations below.
    # Input path_manager: the supplied path manager.
    # Input catalogue_vehicle_width: the supplied catalogue vehicle width.
    # Output: no explicit value; normal completion returns None.
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    def __init__(self, path_manager, catalogue_vehicle_width=AV_WIDTH_METERS):
        # Set self.path_manager to path_manager.
        self.path_manager = path_manager
        # Set self.catalogue_vehicle_width to a floating-point number built from catalogue_vehicle_width.
        self.catalogue_vehicle_width = float(catalogue_vehicle_width)
        # Run this branch when self.catalogue_vehicle_width is at most 0.0.
        if self.catalogue_vehicle_width <= 0.0:
            # Raise ValueError with the text 'catalogue vehicle width must be positive' to stop this execution
            # path.
            raise ValueError("catalogue vehicle width must be positive")
        # Set self.lines to a dictionary of path_id mapped to the result of LineString(path.centerline_geometry)
        # for (path_id, path) in key/value pairs from path_manager.paths.
        self.lines = {
            # Evaluate the result of LineString(path.centerline_geometry) as part of the enclosing expression.
            path_id: LineString(path.centerline_geometry)
            # Evaluate key/value pairs from path_manager.paths as part of the enclosing expression.
            for path_id, path in path_manager.paths.items()
        }
        # Set pairs to a list built from the result of combinations_with_replacement(the sorted values from
        # self.lines, 2).
        pairs = list(combinations_with_replacement(sorted(self.lines), 2))
        # Set candidates to a list of pair for pair in pairs; retain entries satisfying the result of
        # self._topology(the unpacked values from pair) belongs to...
        candidates = [pair for pair in pairs if self._topology(*pair) in
                      # Evaluate self.COORDINATED_TOPOLOGIES as part of the enclosing expression.
                      self.COORDINATED_TOPOLOGIES]
        # Set self._candidate_zone_ids to a dictionary of an immutable set built from pair mapped to formatted
        # text built from the embedded values for (index, pair) in index/value pairs from candidates.
        self._candidate_zone_ids = {
            # Evaluate formatted text built from the embedded values as part of the enclosing expression.
            frozenset(pair): f"CZ_CANDIDATE_{index:03d}"
            # Supply start as 1.
            for index, pair in enumerate(candidates, start=1)
        }
        # Set provisional to a dictionary of an immutable set built from pair mapped to the result of
        # self.relationship_for_widths(pair at 0, self.catalogue_vehicle_width, pair at 1,
        # self.catalogue_vehicle_width) for pair in pairs.
        provisional = {
            # Evaluate the result of self.relationship_for_widths(pair at 0, self.catalogue_vehicle_width, pair at
            # 1, self.catalogue_vehicle_width) as part of the enclosing expression.
            frozenset(pair): self.relationship_for_widths(
                # Supply self.catalogue_vehicle_width to self.relationship_for_widths.
                pair[0], self.catalogue_vehicle_width,
                # Supply self.catalogue_vehicle_width to self.relationship_for_widths.
                pair[1], self.catalogue_vehicle_width,
            # Evaluate pairs as part of the enclosing expression.
            ) for pair in pairs
        }
        # Set coordinated_pairs to the sorted values from a lazy sequence of a tuple built from the sorted values
        # from key for (key, value) in key/value pairs from provisional; retain entries satisfying
        # value.coordinated_conflict.
        coordinated_pairs = sorted(
            # Supply a lazy sequence of a tuple built from the sorted values from key for (key, value) in
            # key/value pairs from provisional; retain entries satisfying value.coordinated_conflict to sorted.
            (tuple(sorted(key)) for key, value in provisional.items()
             # Evaluate value.coordinated_conflict as part of the enclosing expression.
             if value.coordinated_conflict)
        )
        # Set compact_ids to a dictionary of an immutable set built from pair mapped to formatted text built from
        # the embedded values for (index, pair) in index/value pairs from coordinated_pairs.
        compact_ids = {
            # Evaluate formatted text built from the embedded values as part of the enclosing expression.
            frozenset(pair): f"CZ_{index:03d}"
            # Supply start as 1.
            for index, pair in enumerate(coordinated_pairs, start=1)
        }
        # Iterate over candidates, binding each item to pair.
        for pair in candidates:
            # Set key to an immutable set built from pair.
            key = frozenset(pair)
            # Call compact_ids.setdefault with the supplied arguments.
            compact_ids.setdefault(
                # Supply the text 'CZ_PATHPAIR__' plus the result of '__'.join(the sorted values from pair) to
                # compact_ids.setdefault.
                key, "CZ_PATHPAIR__" + "__".join(sorted(pair))
            )
        # Set self._candidate_zone_ids to compact_ids.
        self._candidate_zone_ids = compact_ids
        # Set self.relationships to a dictionary of an immutable set built from pair mapped to the result of
        # self.relationship_for_widths(pair at 0, self.catalogue_vehicle_width, pair at 1,
        # self.catalogue_vehicle_width) for pair in pairs.
        self.relationships = {
            # Evaluate the result of self.relationship_for_widths(pair at 0, self.catalogue_vehicle_width, pair at
            # 1, self.catalogue_vehicle_width) as part of the enclosing expression.
            frozenset(pair): self.relationship_for_widths(
                # Supply self.catalogue_vehicle_width to self.relationship_for_widths.
                pair[0], self.catalogue_vehicle_width,
                # Supply self.catalogue_vehicle_width to self.relationship_for_widths.
                pair[1], self.catalogue_vehicle_width,
            # Evaluate pairs as part of the enclosing expression.
            ) for pair in pairs
        }
        # Set self.zone_geometries to a dictionary of relationship.conflict_zone_id mapped to the result of
        # self.zone_record(relationship.first_path_id, self.catalogue_vehicle_width,
        # relationship.second_path_id,...) for relationship in values from self.relationships; retain entries
        # satisfying relationship.coordinated_conflict.
        self.zone_geometries = {
            # Evaluate the result of self.zone_record(relationship.first_path_id, self.catalogue_vehicle_width,
            # relationship.second_path_id,...) as part of the enclosing expression.
            relationship.conflict_zone_id: self.zone_record(
                # Supply self.catalogue_vehicle_width to self.zone_record.
                relationship.first_path_id, self.catalogue_vehicle_width,
                # Supply self.catalogue_vehicle_width to self.zone_record.
                relationship.second_path_id, self.catalogue_vehicle_width,
            )
            # Evaluate values from self.relationships as part of the enclosing expression.
            for relationship in self.relationships.values()
            # Evaluate relationship.coordinated_conflict as part of the enclosing expression.
            if relationship.coordinated_conflict
        }

    # Topology using the inputs and processing steps below.
    # Input first_path_id: the supplied first path id.
    # Input second_path_id: the supplied second path id.
    # Output: return the value selected by the matching return branch below.
    # Processing: select branches using the stated conditions.
    def _topology(self, first_path_id, second_path_id):
        # Set first to self.path_manager.paths at first_path_id.
        first = self.path_manager.paths[first_path_id]
        # Set second to self.path_manager.paths at second_path_id.
        second = self.path_manager.paths[second_path_id]
        # Run this branch when first.path_id equals second.path_id.
        if first.path_id == second.path_id:
            # Return the text 'SAME_PATH' to the caller.
            return "SAME_PATH"
        # Run this branch when first.incoming_lane_id equals second.incoming_lane_id.
        if first.incoming_lane_id == second.incoming_lane_id:
            # Return the text 'DIVERGING' to the caller.
            return "DIVERGING"
        # Run this branch when first.outgoing_lane_id equals second.outgoing_lane_id.
        if first.outgoing_lane_id == second.outgoing_lane_id:
            # Return the text 'MERGING' to the caller.
            return "MERGING"
        # Return the text 'POTENTIAL_CROSSING' to the caller.
        return "POTENTIAL_CROSSING"

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Validate width using the inputs and processing steps below.
    # Input width: the supplied width.
    # Output: value.
    # Processing: select branches using the stated conditions.
    def _validate_width(width):
        # Set value to a floating-point number built from width.
        value = float(width)
        # Run this branch when value is at most 0.0.
        if value <= 0.0:
            # Raise ValueError with the text 'vehicle width must be positive' to stop this execution path.
            raise ValueError("vehicle width must be positive")
        # Return value to the caller.
        return value

    # Apply lru_cache(maxsize=None) as a decorator to configure the following definition.
    @lru_cache(maxsize=None)
    # Physical intersection using the inputs and processing steps below.
    # Input first_path_id: the supplied first path id.
    # Input first_width: the supplied first width.
    # Input second_path_id: the supplied second path id.
    # Input second_width: the supplied second width.
    # Output: the result of first.intersection(second).
    def physical_intersection(self, first_path_id, first_width,
                              # Declare second_path_id, second_width as input parameters.
                              second_path_id, second_width):
        # Set first_width to the result of self._validate_width(first_width).
        first_width = self._validate_width(first_width)
        # Set second_width to the result of self._validate_width(second_width).
        second_width = self._validate_width(second_width)
        # Set first to the result of self.lines[first_path_id].buffer(first_width divided by 2.0).
        first = self.lines[first_path_id].buffer(
            # Supply cap_style as BufferCapStyle.flat.
            first_width / 2.0, cap_style=BufferCapStyle.flat,
            # Supply join_style as BufferJoinStyle.round.
            join_style=BufferJoinStyle.round,
        )
        # Set second to the result of self.lines[second_path_id].buffer(second_width divided by 2.0).
        second = self.lines[second_path_id].buffer(
            # Supply cap_style as BufferCapStyle.flat.
            second_width / 2.0, cap_style=BufferCapStyle.flat,
            # Supply join_style as BufferJoinStyle.round.
            join_style=BufferJoinStyle.round,
        )
        # Return the result of first.intersection(second) to the caller.
        return first.intersection(second)

    # Relationship for widths using the inputs and processing steps below.
    # Input first_path_id: the supplied first path id.
    # Input first_width: the supplied first width.
    # Input second_path_id: the supplied second path id.
    # Input second_width: the supplied second width.
    # Output: the result of ConflictRelationship(first_path_id, second_path_id, frozenset((first_path_id,
    # second_path_id)) from...).
    def relationship_for_widths(self, first_path_id, first_width,
                                # Declare second_path_id, second_width as input parameters.
                                second_path_id, second_width):
        # Set topology to the result of self._topology(first_path_id, second_path_id).
        topology = self._topology(first_path_id, second_path_id)
        # Set overlap to the result of self.physical_intersection(first_path_id, first_width, second_path_id,
        # second_width).
        overlap = self.physical_intersection(
            # Supply second_path_id to self.physical_intersection.
            first_path_id, first_width, second_path_id, second_width
        )
        # Set physical_overlap to the negation of overlap.is_empty.
        physical_overlap = not overlap.is_empty
        # Set coordinated to topology belongs to self.COORDINATED_TOPOLOGIES and physical_overlap.
        coordinated = topology in self.COORDINATED_TOPOLOGIES and physical_overlap
        # Set conflict_type to the text 'CROSSING' when topology equals the text 'POTENTIAL_CROSSING' and
        # coordinated, otherwise topology when topology belongs to a set containing 'SAME_PATH', 'DIVERGING',
        # 'MERGING', otherwise the text 'NO_CONFLICT'.
        conflict_type = (
            # Evaluate the text 'CROSSING' when topology equals the text 'POTENTIAL_CROSSING' and coordinated,
            # otherwise topology when topology belongs to a set containing 'SAME_PATH', 'DIVERGING', 'MERGING',
            # otherwise the text 'NO_CONFLICT' as part of the enclosing expression.
            "CROSSING" if topology == "POTENTIAL_CROSSING" and coordinated
            # Evaluate topology when topology belongs to a set containing the text 'SAME_PATH', the text
            # 'DIVERGING', the text 'MERGING', otherwise the text 'NO_CONFLICT' as part of the enclosing
            # expression.
            else topology if topology in {"SAME_PATH", "DIVERGING", "MERGING"}
            # Supply the text 'NO_CONFLICT' to the enclosing expression.
            else "NO_CONFLICT"
        )
        # Return the result of ConflictRelationship(first_path_id, second_path_id, frozenset((first_path_id,
        # second_path_id)) from...) to the caller.
        return ConflictRelationship(
            # Supply second_path_id to ConflictRelationship.
            first_path_id, second_path_id,
            # Supply frozenset((first_path_id, second_path_id)) from self._candidate_zone_ids; use None if absent
            # when coordinated, otherwise None to ConflictRelationship.
            self._candidate_zone_ids.get(frozenset((first_path_id, second_path_id)))
            # Evaluate coordinated as part of the enclosing expression.
            if coordinated else None,
            # Supply physical_overlap to ConflictRelationship.
            conflict_type, physical_overlap, coordinated,
            # Supply overlap.geom_type when physical_overlap, otherwise None to ConflictRelationship.
            overlap.geom_type if physical_overlap else None,
        )

    # Relationship using the inputs and processing steps below.
    # Input first_path_id: the supplied first path id.
    # Input second_path_id: the supplied second path id.
    # Output: self.relationships at frozenset((first_path_id, second_path_id)).
    def relationship(self, first_path_id, second_path_id):
        # Return self.relationships at frozenset((first_path_id, second_path_id)) to the caller.
        return self.relationships[frozenset((first_path_id, second_path_id))]

    # Coordinated conflict using the inputs and processing steps below.
    # Input first_path_id: the supplied first path id.
    # Input first_width: the supplied first width.
    # Input second_path_id: the supplied second path id.
    # Input second_width: the supplied second width.
    # Output: return the value selected by the matching return branch below.
    # Processing: select branches using the stated conditions.
    def coordinated_conflict(self, first_path_id, first_width,
                             # Declare second_path_id, second_width as input parameters.
                             second_path_id, second_width):
        # Set relationship to the result of self.relationship_for_widths(first_path_id, first_width,
        # second_path_id, second_width).
        relationship = self.relationship_for_widths(
            # Supply second_path_id to self.relationship_for_widths.
            first_path_id, first_width, second_path_id, second_width
        )
        # Run this branch when the negation of relationship.coordinated_conflict.
        if not relationship.coordinated_conflict:
            # Return a tuple containing relationship, None to the caller.
            return relationship, None
        # Return a tuple containing relationship, the result of self.physical_intersection(first_path_id,
        # first_width, second_path_id,... to the caller.
        return relationship, self.physical_intersection(
            # Supply second_path_id to self.physical_intersection.
            first_path_id, first_width, second_path_id, second_width
        )

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Projected interval using the inputs and processing steps below.
    # Input line: the supplied line.
    # Input zone: the supplied zone.
    # Output: a tuple containing the minimum of distances, the maximum of distances when distances, otherwise
    # None.
    def _projected_interval(line, zone):
        # Set occupied to the result of line.intersection(zone).
        occupied = line.intersection(zone)
        # Set distances to an empty list.
        distances = []

        # Collect using the inputs and processing steps below.
        # Input geometry: the supplied geometry.
        # Output: no explicit value; normal completion returns None.
        # Processing: iterate over the relevant records, then select branches using the stated conditions.
        def collect(geometry):
            # Run this branch when geometry.geom_type belongs to a set containing the text 'Point', the text
            # 'LineString', the text 'LinearRing'.
            if geometry.geom_type in {"Point", "LineString", "LinearRing"}:
                # Extend distances with a lazy sequence of the result of line.project(the result of Point(x, y))
                # for (x, y) in geometry.coords.
                distances.extend(
                    # Evaluate the result of line.project(the result of Point(x, y)) as part of the enclosing
                    # expression.
                    line.project(Point(x, y)) for x, y in geometry.coords
                )
            # Run this branch when geometry.geom_type equals the text 'Polygon'.
            elif geometry.geom_type == "Polygon":
                # Call collect with the supplied arguments.
                collect(geometry.exterior)
                # Iterate over geometry.interiors, binding each item to ring.
                for ring in geometry.interiors:
                    # Call collect with the supplied arguments.
                    collect(ring)
            # Run this branch when whether geometry exposes the requested attribute.
            elif hasattr(geometry, "geoms"):
                # Iterate over geometry.geoms, binding each item to component.
                for component in geometry.geoms:
                    # Call collect with the supplied arguments.
                    collect(component)

        # Swept envelopes can overlap between nearby centre lines without the
        # overlap polygon containing either centre line. In that valid case,
        # project the same authoritative overlap polygon onto the path. This
        # introduces neither a tolerance nor any additional geometry.
        # Call collect with the supplied arguments.
        collect(zone if occupied.is_empty else occupied)
        # Return a tuple containing the minimum of distances, the maximum of distances when distances, otherwise
        # None to the caller.
        return (min(distances), max(distances)) if distances else None

    # Zone record using the inputs and processing steps below.
    # Input first_path_id: the supplied first path id.
    # Input first_width: the supplied first width.
    # Input second_path_id: the supplied second path id.
    # Input second_width: the supplied second width.
    # Output: return the value selected by the matching return branch below.
    # Processing: select branches using the stated conditions.
    def zone_record(self, first_path_id, first_width,
                    # Declare second_path_id, second_width as input parameters.
                    second_path_id, second_width):
        # Set (relationship, zone) to the result of self.coordinated_conflict(first_path_id, first_width,
        # second_path_id, second_width).
        relationship, zone = self.coordinated_conflict(
            # Supply second_path_id to self.coordinated_conflict.
            first_path_id, first_width, second_path_id, second_width
        )
        # Run this branch when zone is the same object as None.
        if zone is None:
            # Return None to the caller.
            return None
        # Set (first_line, second_line) to a tuple containing self.lines at first_path_id, self.lines at
        # second_path_id.
        first_line, second_line = self.lines[first_path_id], self.lines[second_path_id]
        # Return a dictionary containing zone_id, first_path_id, second_path_id, conflict_type, geometry,
        # geometry_type,... to the caller.
        return {
            # Store relationship.conflict_zone_id under 'zone_id'.
            "zone_id": relationship.conflict_zone_id,
            # Store first_path_id under 'first_path_id'.
            "first_path_id": first_path_id,
            # Store second_path_id under 'second_path_id'.
            "second_path_id": second_path_id,
            # Store relationship.conflict_type under 'conflict_type'.
            "conflict_type": relationship.conflict_type,
            # Store zone under 'geometry'.
            "geometry": zone,
            # Store zone.geom_type under 'geometry_type'.
            "geometry_type": zone.geom_type,
            # Store the result of self._projected_interval(first_line, zone) under 'first_path_distance_interval'.
            "first_path_distance_interval": self._projected_interval(first_line, zone),
            # Store the result of self._projected_interval(second_line, zone) under
            # 'second_path_distance_interval'.
            "second_path_distance_interval": self._projected_interval(second_line, zone),
        }

    # Catalogue rows using the inputs and processing steps below.
    # Output: a tuple built from a lazy sequence of a dictionary containing zone_id, first_path_id,
    # second_path_id, topological_relationship, conflict_type,... for item in values from self.relationships.
    def catalogue_rows(self):
        # Return a tuple built from a lazy sequence of a dictionary containing zone_id, first_path_id,
        # second_path_id, topological_relationship, conflict_type,... for item in values from self.relationships
        # to the caller.
        return tuple({
            # Store item.conflict_zone_id or the text '' under 'zone_id'.
            "zone_id": item.conflict_zone_id or "",
            # Store item.first_path_id under 'first_path_id'.
            "first_path_id": item.first_path_id,
            # Store item.second_path_id under 'second_path_id'.
            "second_path_id": item.second_path_id,
            # Store the result of self._topology(item.first_path_id, item.second_path_id) under
            # 'topological_relationship'.
            "topological_relationship": self._topology(
                # Supply item.second_path_id to self._topology.
                item.first_path_id, item.second_path_id
            ),
            # Store item.conflict_type under 'conflict_type'.
            "conflict_type": item.conflict_type,
            # Store item.physical_overlap under 'physical_overlap'.
            "physical_overlap": item.physical_overlap,
            # Store item.coordinated_conflict under 'coordinated_conflict'.
            "coordinated_conflict": item.coordinated_conflict,
            # Store item.geometry_type or the text '' under 'geometry_type'.
            "geometry_type": item.geometry_type or "",
        # Evaluate values from self.relationships as part of the enclosing expression.
        } for item in self.relationships.values())
