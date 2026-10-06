"""Read-only, JSON-safe spatial and temporal conflict visualization evidence."""

import copy

from shapely.geometry import mapping

from debug_evidence import json_safe


FORBIDDEN_TRUTH_FIELDS = frozenset({
    "route_id", "route_index", "ground_truth_route_id",
    "ground_truth_manoeuvre", "ground_truth_intention",
})


def _sanitized(value):
    if isinstance(value, dict):
        return {
            str(key): _sanitized(item) for key, item in value.items()
            if key not in FORBIDDEN_TRUTH_FIELDS
        }
    if isinstance(value, (list, tuple)):
        return [_sanitized(item) for item in value]
    return json_safe(value)


def geometry_mapping(geometry):
    """Serialize Polygon/MultiPolygon/GeometryCollection without mutation."""
    if geometry is None or geometry.is_empty:
        return None
    return json_safe(mapping(geometry))


def _path_ids(value):
    if value is None:
        return ()
    return tuple(value) if isinstance(value, (list, tuple)) else (value,)


def _geometry_for_diagnostic(diagnostic, ldm, path_manager, zone_manager):
    ego_id = ldm.ego_id
    ego_track = ldm.tracks.get(ego_id, {})
    target_id = diagnostic.get("target_track_id")
    target_track = ldm.tracks.get(target_id, {})
    ego_path_id = diagnostic.get("ego_path_id")
    ego_path = path_manager.paths.get(ego_path_id)
    result = {
        "ego_path_id": ego_path_id,
        "ego_width_m": ego_track.get("width"),
        "target_width_m": target_track.get("width"),
        "ego_centerline": (
            json_safe(ego_path.centerline_geometry) if ego_path else None
        ),
        "target_paths": [],
    }
    conflicting = diagnostic.get("spatially_conflicting_candidate_paths", {})
    candidates = diagnostic.get("target_candidate_paths", {})
    all_paths = {}
    for source in (candidates, conflicting):
        for manoeuvre, value in source.items():
            for path_id in _path_ids(value):
                all_paths[(manoeuvre, path_id)] = path_id
    for manoeuvre, path_id in sorted(all_paths):
        path = path_manager.paths.get(path_id)
        is_conflicting = path_id in _path_ids(conflicting.get(manoeuvre))
        item = {
            "manoeuvre": manoeuvre,
            "path_id": path_id,
            "selected_candidate": path_id in _path_ids(candidates.get(manoeuvre)),
            "spatially_conflicting": is_conflicting,
            "centerline": json_safe(path.centerline_geometry) if path else None,
            "conflict_zone": None,
        }
        if is_conflicting and ego_path_id and path is not None:
            zone = zone_manager.zone_record(
                ego_path_id, ego_track.get("width"),
                path_id, target_track.get("width"),
            )
            if zone is not None:
                item["conflict_zone"] = {
                    "zone_id": zone["zone_id"],
                    "conflict_type": zone["conflict_type"],
                    "geometry_type": zone["geometry_type"],
                    "geometry": geometry_mapping(zone["geometry"]),
                    "ego_path_interval_m": json_safe(
                        zone["first_path_distance_interval"]
                    ),
                    "target_path_interval_m": json_safe(
                        zone["second_path_distance_interval"]
                    ),
                }
        result["target_paths"].append(item)
    return json_safe(result)


def build_conflict_evidence(observation_manager, path_manager=None,
                            zone_manager=None):
    """Copy current authoritative graph/occupancy state for presentation."""
    graphs, temporal, geometry, kpis = {}, {}, {}, {}
    for ego_id, ldm in observation_manager.ldms.items():
        graph = _sanitized(copy.deepcopy(ldm.get_current_conflict_graph()))
        assessment = _sanitized(copy.deepcopy(
            ldm.get_current_temporal_assessment()
        ))
        graphs[ego_id] = graph
        temporal[ego_id] = assessment
        geometry[ego_id] = {}
        diagnostics = (graph or {}).get("diagnostics", [])
        if path_manager is not None and zone_manager is not None:
            for diagnostic in diagnostics:
                target_id = diagnostic.get("target_track_id")
                if target_id in ldm.tracks:
                    geometry[ego_id][target_id] = _geometry_for_diagnostic(
                        diagnostic, ldm, path_manager, zone_manager
                    )
        metrics = dict((graph or {}).get("metrics", {}))
        temporal_edges = (assessment or {}).get("edges", [])
        metrics.update({
            "temporal_conflict_edges": sum(
                edge.get("status") == "TEMPORAL_CONFLICT"
                for edge in temporal_edges
            ),
            "spatial_only_edges": sum(
                edge.get("status") == "SPATIAL_ONLY"
                for edge in temporal_edges
            ),
            "unresolved_temporal_edges": sum(
                str(edge.get("status", "")).startswith("UNRESOLVED_")
                for edge in temporal_edges
            ),
        })
        kpis[ego_id] = json_safe(metrics)
    return {
        "local_conflict_graphs": graphs,
        "temporal_conflict_assessments": temporal,
        "conflict_geometry_by_ego": geometry,
        "conflict_kpis_by_ego": kpis,
    }
