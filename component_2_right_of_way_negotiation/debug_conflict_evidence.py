"""Read-only, JSON-safe spatial and temporal conflict visualization evidence."""

# Import copy for use in this module.
import copy

# Import mapping from shapely.geometry for the operations below.
from shapely.geometry import mapping

# Import json_safe from debug_evidence for the operations below.
from debug_evidence import json_safe


# Set FORBIDDEN_TRUTH_FIELDS to an immutable set built from a set containing the text 'route_id', the text
# 'route_index', the text 'ground_truth_route_id', the text...
FORBIDDEN_TRUTH_FIELDS = frozenset({
    "route_id", "route_index", "ground_truth_route_id",
    "ground_truth_manoeuvre", "ground_truth_intention",
})


# Sanitized using the inputs and processing steps below.
# Input value: the supplied value.
# Output: return the value selected by the matching return branch below.
# Processing: select branches using the stated conditions.
def _sanitized(value):
    # Run this branch when whether value has type dict.
    if isinstance(value, dict):
        # Return a dictionary of a string built from key mapped to the result of _sanitized(item) for (key, item)
        # in key/value pairs from value; retain entries satisfying key does not belong to FORBIDDEN_TRUTH_FIELDS
        # to the caller.
        return {
            # Evaluate the result of _sanitized(item) as part of the enclosing expression.
            str(key): _sanitized(item) for key, item in value.items()
            # Evaluate key does not belong to FORBIDDEN_TRUTH_FIELDS as part of the enclosing expression.
            if key not in FORBIDDEN_TRUTH_FIELDS
        }
    # Run this branch when whether value has type a tuple containing list, tuple.
    if isinstance(value, (list, tuple)):
        # Return a list of the result of _sanitized(item) for item in value to the caller.
        return [_sanitized(item) for item in value]
    # Return the result of json_safe(value) to the caller.
    return json_safe(value)


# Serialize Polygon/MultiPolygon/GeometryCollection without mutation.
# Input geometry: the supplied geometry.
# Output: return the value selected by the matching return branch below.
# Processing: select branches using the stated conditions.
def geometry_mapping(geometry):
    """Serialize Polygon/MultiPolygon/GeometryCollection without mutation."""
    # Run this branch when geometry is the same object as None or geometry.is_empty.
    if geometry is None or geometry.is_empty:
        # Return None to the caller.
        return None
    # Return the result of json_safe(the result of mapping(geometry)) to the caller.
    return json_safe(mapping(geometry))


# Path ids using the inputs and processing steps below.
# Input value: the supplied value.
# Output: return the value selected by the matching return branch below.
# Processing: select branches using the stated conditions.
def _path_ids(value):
    # Run this branch when value is the same object as None.
    if value is None:
        # Return an empty tuple to the caller.
        return ()
    # Return a tuple built from value when whether value has type a tuple containing list, tuple, otherwise a
    # tuple containing value to the caller.
    return tuple(value) if isinstance(value, (list, tuple)) else (value,)


# Geometry for diagnostic using the inputs and processing steps below.
# Input diagnostic: the supplied diagnostic.
# Input ldm: the supplied ldm.
# Input path_manager: the supplied path manager.
# Input zone_manager: the supplied zone manager.
# Output: the result of json_safe(result).
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def _geometry_for_diagnostic(diagnostic, ldm, path_manager, zone_manager):
    # Set ego_id to ldm.ego_id.
    ego_id = ldm.ego_id
    # Set ego_track to ego_id from ldm.tracks; use an empty dictionary if absent.
    ego_track = ldm.tracks.get(ego_id, {})
    # Set target_id to 'target_track_id' from diagnostic; use None if absent.
    target_id = diagnostic.get("target_track_id")
    # Set target_track to target_id from ldm.tracks; use an empty dictionary if absent.
    target_track = ldm.tracks.get(target_id, {})
    # Set ego_path_id to 'ego_path_id' from diagnostic; use None if absent.
    ego_path_id = diagnostic.get("ego_path_id")
    # Set ego_path to ego_path_id from path_manager.paths; use None if absent.
    ego_path = path_manager.paths.get(ego_path_id)
    # Set result to a dictionary containing ego_path_id, ego_width_m, target_width_m, ego_centerline,
    # target_paths.
    result = {
        # Store ego_path_id under 'ego_path_id'.
        "ego_path_id": ego_path_id,
        # Store 'width' from ego_track; use None if absent under 'ego_width_m'.
        "ego_width_m": ego_track.get("width"),
        # Store 'width' from target_track; use None if absent under 'target_width_m'.
        "target_width_m": target_track.get("width"),
        # Store the result of json_safe(ego_path.centerline_geometry) when ego_path, otherwise None under
        # 'ego_centerline'.
        "ego_centerline": (
            # Evaluate the result of json_safe(ego_path.centerline_geometry) when ego_path, otherwise None as part
            # of the enclosing expression.
            json_safe(ego_path.centerline_geometry) if ego_path else None
        ),
        # Store an empty list under 'target_paths'.
        "target_paths": [],
    }
    # Set conflicting to 'spatially_conflicting_candidate_paths' from diagnostic; use an empty dictionary if
    # absent.
    conflicting = diagnostic.get("spatially_conflicting_candidate_paths", {})
    # Set candidates to 'target_candidate_paths' from diagnostic; use an empty dictionary if absent.
    candidates = diagnostic.get("target_candidate_paths", {})
    # Set all_paths to an empty dictionary.
    all_paths = {}
    # Iterate over a tuple containing candidates, conflicting, binding each item to source.
    for source in (candidates, conflicting):
        # Iterate over key/value pairs from source, binding each item to (manoeuvre, value).
        for manoeuvre, value in source.items():
            # Iterate over the result of _path_ids(value), binding each item to path_id.
            for path_id in _path_ids(value):
                # Set all_paths[manoeuvre, path_id] to path_id.
                all_paths[(manoeuvre, path_id)] = path_id
    # Iterate over the sorted values from all_paths, binding each item to (manoeuvre, path_id).
    for manoeuvre, path_id in sorted(all_paths):
        # Set path to path_id from path_manager.paths; use None if absent.
        path = path_manager.paths.get(path_id)
        # Set is_conflicting to path_id belongs to the result of _path_ids(manoeuvre from conflicting; use None if
        # absent).
        is_conflicting = path_id in _path_ids(conflicting.get(manoeuvre))
        # Set item to a dictionary containing manoeuvre, path_id, selected_candidate, spatially_conflicting,
        # centerline, conflict_zone.
        item = {
            # Store manoeuvre under 'manoeuvre'.
            "manoeuvre": manoeuvre,
            # Store path_id under 'path_id'.
            "path_id": path_id,
            # Store path_id belongs to the result of _path_ids(manoeuvre from candidates; use None if absent)
            # under 'selected_candidate'.
            "selected_candidate": path_id in _path_ids(candidates.get(manoeuvre)),
            # Store is_conflicting under 'spatially_conflicting'.
            "spatially_conflicting": is_conflicting,
            # Store the result of json_safe(path.centerline_geometry) when path, otherwise None under
            # 'centerline'.
            "centerline": json_safe(path.centerline_geometry) if path else None,
            # Store None under 'conflict_zone'.
            "conflict_zone": None,
        }
        # Run this branch when is_conflicting and ego_path_id and path is a different object from None.
        if is_conflicting and ego_path_id and path is not None:
            # Set zone to the result of zone_manager.zone_record(ego_path_id, 'width' from ego_track; use None if
            # absent, path_id, 'width' from target_track; use...).
            zone = zone_manager.zone_record(
                # Supply 'width' from ego_track; use None if absent to zone_manager.zone_record.
                ego_path_id, ego_track.get("width"),
                # Supply 'width' from target_track; use None if absent to zone_manager.zone_record.
                path_id, target_track.get("width"),
            )
            # Run this branch when zone is a different object from None.
            if zone is not None:
                # Set item['conflict_zone'] to a dictionary containing zone_id, conflict_type, geometry_type,
                # geometry, ego_path_interval_m,...
                item["conflict_zone"] = {
                    # Store zone at 'zone_id' under 'zone_id'.
                    "zone_id": zone["zone_id"],
                    # Store zone at 'conflict_type' under 'conflict_type'.
                    "conflict_type": zone["conflict_type"],
                    # Store zone at 'geometry_type' under 'geometry_type'.
                    "geometry_type": zone["geometry_type"],
                    # Store the result of geometry_mapping(zone at 'geometry') under 'geometry'.
                    "geometry": geometry_mapping(zone["geometry"]),
                    # Store the result of json_safe(zone at 'first_path_distance_interval') under
                    # 'ego_path_interval_m'.
                    "ego_path_interval_m": json_safe(
                        # Supply zone at 'first_path_distance_interval' to json_safe.
                        zone["first_path_distance_interval"]
                    ),
                    # Store the result of json_safe(zone at 'second_path_distance_interval') under
                    # 'target_path_interval_m'.
                    "target_path_interval_m": json_safe(
                        # Supply zone at 'second_path_distance_interval' to json_safe.
                        zone["second_path_distance_interval"]
                    ),
                }
        # Append item to result['target_paths'].
        result["target_paths"].append(item)
    # Return the result of json_safe(result) to the caller.
    return json_safe(result)


# Copy current authoritative graph/occupancy state for presentation.
# Input observation_manager: the supplied observation manager.
# Input path_manager: the supplied path manager.
# Input zone_manager: the supplied zone manager.
# Output: a dictionary containing local_conflict_graphs, temporal_conflict_assessments,
# conflict_geometry_by_ego,...
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def build_conflict_evidence(observation_manager, path_manager=None,
                            # Declare zone_manager as input parameter.
                            zone_manager=None):
    """Copy current authoritative graph/occupancy state for presentation."""
    # Set (graphs, temporal, geometry, kpis) to a tuple containing an empty dictionary, an empty dictionary, an
    # empty dictionary, an empty dictionary.
    graphs, temporal, geometry, kpis = {}, {}, {}, {}
    # Iterate over key/value pairs from observation_manager.ldms, binding each item to (ego_id, ldm).
    for ego_id, ldm in observation_manager.ldms.items():
        # Set graph to the result of _sanitized(the result of copy.deepcopy(the result of
        # ldm.get_current_conflict_graph())).
        graph = _sanitized(copy.deepcopy(ldm.get_current_conflict_graph()))
        # Set assessment to the result of _sanitized(the result of copy.deepcopy(the result of
        # ldm.get_current_temporal_assessment())).
        assessment = _sanitized(copy.deepcopy(
            # Supply the result of ldm.get_current_temporal_assessment() to copy.deepcopy.
            ldm.get_current_temporal_assessment()
        ))
        # Set graphs[ego_id] to graph.
        graphs[ego_id] = graph
        # Set temporal[ego_id] to assessment.
        temporal[ego_id] = assessment
        # Set geometry[ego_id] to an empty dictionary.
        geometry[ego_id] = {}
        # Set diagnostics to 'diagnostics' from (graph or {}); use an empty list if absent.
        diagnostics = (graph or {}).get("diagnostics", [])
        # Run this branch when path_manager is a different object from None and zone_manager is a different object
        # from None.
        if path_manager is not None and zone_manager is not None:
            # Iterate over diagnostics, binding each item to diagnostic.
            for diagnostic in diagnostics:
                # Set target_id to 'target_track_id' from diagnostic; use None if absent.
                target_id = diagnostic.get("target_track_id")
                # Run this branch when target_id belongs to ldm.tracks.
                if target_id in ldm.tracks:
                    # Set geometry[ego_id][target_id] to the result of _geometry_for_diagnostic(diagnostic, ldm,
                    # path_manager, zone_manager).
                    geometry[ego_id][target_id] = _geometry_for_diagnostic(
                        # Supply path_manager to _geometry_for_diagnostic.
                        diagnostic, ldm, path_manager, zone_manager
                    )
        # Set metrics to a dictionary built from 'metrics' from (graph or {}); use an empty dictionary if absent.
        metrics = dict((graph or {}).get("metrics", {}))
        # Set temporal_edges to 'edges' from (assessment or {}); use an empty list if absent.
        temporal_edges = (assessment or {}).get("edges", [])
        # Update metrics with the supplied entries.
        metrics.update({
            # Store the sum of a lazy sequence of 'status' from edge; use None if absent equals the text
            # 'TEMPORAL_CONFLICT' for edge in temporal_edges under 'temporal_conflict_edges'.
            "temporal_conflict_edges": sum(
                # Evaluate 'status' from edge; use None if absent equals the text 'TEMPORAL_CONFLICT' as part of
                # the enclosing expression.
                edge.get("status") == "TEMPORAL_CONFLICT"
                # Evaluate temporal_edges as part of the enclosing expression.
                for edge in temporal_edges
            ),
            # Store the sum of a lazy sequence of 'status' from edge; use None if absent equals the text
            # 'SPATIAL_ONLY' for edge in temporal_edges under 'spatial_only_edges'.
            "spatial_only_edges": sum(
                # Evaluate 'status' from edge; use None if absent equals the text 'SPATIAL_ONLY' as part of the
                # enclosing expression.
                edge.get("status") == "SPATIAL_ONLY"
                # Evaluate temporal_edges as part of the enclosing expression.
                for edge in temporal_edges
            ),
            # Store the sum of a lazy sequence of the result of str(edge.get('status', '')).startswith(the text
            # 'UNRESOLVED_') for edge in temporal_edges under 'unresolved_temporal_edges'.
            "unresolved_temporal_edges": sum(
                # Evaluate the result of str(edge.get('status', '')).startswith(the text 'UNRESOLVED_') as part of
                # the enclosing expression.
                str(edge.get("status", "")).startswith("UNRESOLVED_")
                # Evaluate temporal_edges as part of the enclosing expression.
                for edge in temporal_edges
            ),
        })
        # Set kpis[ego_id] to the result of json_safe(metrics).
        kpis[ego_id] = json_safe(metrics)
    # Return a dictionary containing local_conflict_graphs, temporal_conflict_assessments,
    # conflict_geometry_by_ego,... to the caller.
    return {
        # Store graphs under 'local_conflict_graphs'.
        "local_conflict_graphs": graphs,
        # Store temporal under 'temporal_conflict_assessments'.
        "temporal_conflict_assessments": temporal,
        # Store geometry under 'conflict_geometry_by_ego'.
        "conflict_geometry_by_ego": geometry,
        # Store kpis under 'conflict_kpis_by_ego'.
        "conflict_kpis_by_ego": kpis,
    }
