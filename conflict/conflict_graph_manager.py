"""Construct ego-specific intention-aware conflict graphs from one LDM.

This project-specific integration combines local/partial perception with the
conflict-zone and graph principles cited in :mod:`conflict_zone_manager`.
Target paths are inferred from current lane and learned intention, never from
target SUMO route truth. ConflictEntryMonitor remains responsible only for
prediction timing and eligibility; this manager performs spatial path conflict
detection and makes no risk, right-of-way, or negotiation decision.

If M_C contains the mutually exclusive target manoeuvres conflicting with the
ego path, P(C) = sum(P(m) for m in M_C). No additional weight or threshold is
introduced.
"""

import copy
import math
from dataclasses import replace

from .models import LocalConflictGraph


MANOEUVRES = frozenset({"LEFT", "RIGHT", "STRAIGHT"})


def extract_operational_intention(track):
    """Adapt the ConflictEntryMonitor snapshot/final result without re-fusion."""
    prediction = track.get("intention_prediction")
    if prediction is None:
        return "UNKNOWN", "NOT_AVAILABLE", None
    if not isinstance(prediction, dict):
        return "UNKNOWN", "INVALID", None
    label = prediction.get("fused_label", "UNKNOWN")
    status = prediction.get("status", "UNKNOWN")
    if label not in MANOEUVRES and label != "UNKNOWN":
        return "UNKNOWN", "INVALID", None
    if label == "UNKNOWN":
        return label, "UNKNOWN", None

    # The fused label is authoritative. Use probabilities from the stage that
    # operational fusion accepted; agreement uses the later secondary result.
    primary, secondary = prediction.get("primary"), prediction.get("secondary")
    stage = secondary if status in {
        "CONFIRMED_AGREEMENT", "SECONDARY_RECOVERY"
    } else None
    probabilities = stage.get("probabilities") if isinstance(stage, dict) else None
    if probabilities is not None:
        try:
            normalized = {name: float(probabilities[name]) for name in MANOEUVRES}
            total = sum(normalized.values())
            if (not all(math.isfinite(value) and value >= 0.0
                        for value in normalized.values())
                    or not math.isclose(total, 1.0, rel_tol=1e-6, abs_tol=1e-6)):
                probabilities = None
            else:
                probabilities = normalized
        except (KeyError, TypeError, ValueError):
            probabilities = None
    return label, "PREDICTED", probabilities


class ConflictGraphManager:
    """Own independent dynamic graph snapshots for each ego LDM."""

    def __init__(self, path_manager, zone_manager):
        self.path_manager = path_manager
        self.zone_manager = zone_manager
        self._graphs = {}
        self._change_events = {}
        self._totals = self._empty_totals()

    @staticmethod
    def _empty_totals():
        return {
            "graphs_built": 0, "spatial_conflict_edges_observed": 0,
            "unknown_intention_conservative_edges": 0,
            "prediction_unavailable_conservative_edges": 0,
            "non_conflicting_targets_filtered": 0,
        }

    def reset(self, ego_id=None):
        if ego_id is None:
            self._graphs.clear()
            self._change_events.clear()
            self._totals = self._empty_totals()
        else:
            self._graphs.pop(ego_id, None)
            self._change_events.pop(ego_id, None)

    def get_graph(self, ego_id):
        graph = self._graphs.get(ego_id)
        return copy.deepcopy(graph.to_dict()) if graph is not None else None

    def build_local_graph(self, ldm, current_time):
        ego_id = ldm.ego_id
        ego = ldm.tracks.get(ego_id)
        nodes = tuple(sorted(ldm.tracks))
        if ego is None:
            return self._store(LocalConflictGraph(
                ego_id, float(current_time), None, nodes, (), ({
                    "ego_id": ego_id, "reason": "MISSING_EGO_PLAN"
                },), self._metrics(len(nodes) - 1, (), ()),
            ))
        ego_manoeuvre = ego.get("self_planned_manoeuvre")
        ego_path = self.path_manager.resolve_path(
            ego.get("lane_id", ""), ego_manoeuvre
        )
        if ego_path is None:
            ego_options = self.path_manager.feasible_paths(
                ego.get("lane_id", "")
            ).get(ego_manoeuvre, ())
            reason = (
                "MISSING_EGO_PLAN" if ego_manoeuvre not in MANOEUVRES
                else "NOT_ON_INTERSECTION_APPROACH" if ego.get("lane_id") not in
                self.path_manager.incoming_lane_ids
                else "AMBIGUOUS_EGO_PATH" if len(ego_options) > 1
                else "MISSING_MAP_CONNECTION"
            )
            diagnostics = tuple({
                "ego_id": ego_id, "target_track_id": target_id,
                "ego_lane": ego.get("lane_id", ""),
                "ego_manoeuvre": ego_manoeuvre, "ego_path_id": None,
                "reason": reason,
            } for target_id in sorted(set(ldm.tracks) - {ego_id}))
            return self._store(LocalConflictGraph(
                ego_id, float(current_time), None, nodes, (), diagnostics,
                self._metrics(len(nodes) - 1, (), diagnostics),
            ))

        edges, diagnostics = [], []
        for target_id in sorted(set(ldm.tracks) - {ego_id}):
            target = ldm.tracks[target_id]
            label, prediction_status, probabilities = extract_operational_intention(target)
            feasible = self.path_manager.feasible_paths(target.get("lane_id", ""))
            reason = None
            if not feasible:
                candidate_paths = {}
                reason = "NOT_ON_INTERSECTION_APPROACH"
            elif prediction_status == "INVALID":
                candidate_paths = feasible
                reason = "INVALID_INTENTION_RESULT"
            elif prediction_status == "PREDICTED" and label in feasible:
                candidate_paths = {label: feasible[label]}
            elif prediction_status == "PREDICTED":
                candidate_paths = feasible
                prediction_status = "INVALID"
                probabilities = None
                reason = "NO_FEASIBLE_PATH"
            else:
                candidate_paths = feasible

            conflicting, zones, types = [], set(), set()
            for manoeuvre, target_paths in candidate_paths.items():
                manoeuvre_conflicts = False
                for target_path in target_paths:
                    relationship, zone = self.zone_manager.coordinated_conflict(
                        ego_path.path_id, ego.get("width"),
                        target_path.path_id, target.get("width"),
                    )
                    if zone is not None:
                        manoeuvre_conflicts = True
                        zones.add(relationship.conflict_zone_id)
                        types.add(relationship.conflict_type)
                if manoeuvre_conflicts:
                    conflicting.append(manoeuvre)

            probability = None
            if probabilities is not None:
                probability_conflicts = set()
                for manoeuvre, target_paths in feasible.items():
                    if any(self.zone_manager.coordinated_conflict(
                        ego_path.path_id, ego.get("width"),
                        target_path.path_id, target.get("width"),
                    )[1] is not None for target_path in target_paths):
                        probability_conflicts.add(manoeuvre)
                probability = sum(
                    probabilities[name] for name in probability_conflicts
                )
                probability = min(1.0, max(0.0, probability))
            possible = bool(conflicting)
            if reason is None:
                if possible:
                    reason = ("CONFLICTING_PREDICTED_PATH"
                              if prediction_status == "PREDICTED"
                              else "CONFLICTING_UNKNOWN_PATH_SET")
                else:
                    reason = "NO_SHARED_CONFLICT_ZONE"
            diagnostic = {
                "ego_id": ego_id, "target_track_id": target_id,
                "ego_lane": ego.get("lane_id", ""),
                "ego_manoeuvre": ego_manoeuvre,
                "ego_path_id": ego_path.path_id,
                "target_lane": target.get("lane_id", ""),
                "target_prediction": label,
                "target_candidate_paths": {
                    name: (paths[0].path_id if len(paths) == 1 else tuple(
                        path.path_id for path in paths
                    )) for name, paths in sorted(candidate_paths.items())
                },
                "conflicting_manoeuvres": tuple(sorted(conflicting)),
                "shared_conflict_zone_ids": tuple(sorted(zones)),
                "conflict_types": tuple(sorted(types)),
                "spatial_conflict_possible": possible,
                "intention_weighted_conflict_probability": probability,
                "prediction_status": prediction_status,
                "observation_age_seconds": max(
                    0.0, float(current_time) -
                    float(target.get("last_observed_time", current_time))
                ),
                "timestamp": float(current_time), "reason": reason,
            }
            diagnostics.append(diagnostic)
            if possible:
                edges.append(dict(diagnostic))
        graph = LocalConflictGraph(
            ego_id, float(current_time), ego_path.path_id, nodes,
            tuple(edges), tuple(diagnostics),
            self._metrics(len(nodes) - 1, edges, diagnostics),
        )
        return self._store(graph)

    def _store(self, graph):
        previous = self._graphs.get(graph.ego_id)
        changes = self._detect_changes(previous, graph)
        graph = replace(graph, changes=tuple(changes))
        self._graphs[graph.ego_id] = graph
        self._change_events[graph.ego_id] = tuple(changes)
        self._totals["graphs_built"] += 1
        self._totals["spatial_conflict_edges_observed"] += len(graph.edges)
        for key in (
            "unknown_intention_conservative_edges",
            "prediction_unavailable_conservative_edges",
            "non_conflicting_targets_filtered",
        ):
            self._totals[key] += graph.metrics[key]
        return copy.deepcopy(graph.to_dict())

    @staticmethod
    def _detect_changes(previous, current):
        if previous is None:
            return tuple({
                "change_type": "EDGE_ADDED", "target_track_id": edge["target_track_id"]
            } for edge in current.edges)
        old = {item["target_track_id"]: item for item in previous.diagnostics}
        new = {item["target_track_id"]: item for item in current.diagnostics}
        changes = []
        old_edges = {item["target_track_id"] for item in previous.edges}
        new_edges = {item["target_track_id"] for item in current.edges}
        for target_id in sorted(new_edges - old_edges):
            changes.append({"change_type": "EDGE_ADDED", "target_track_id": target_id})
        for target_id in sorted(old_edges - new_edges):
            changes.append({"change_type": "EDGE_REMOVED", "target_track_id": target_id})
        for target_id in sorted(set(old) & set(new)):
            if old[target_id].get("prediction_status") != new[target_id].get("prediction_status"):
                changes.append({
                    "change_type": "PREDICTION_STATUS_CHANGED",
                    "target_track_id": target_id,
                    "from": old[target_id].get("prediction_status"),
                    "to": new[target_id].get("prediction_status"),
                })
            if old[target_id].get("target_candidate_paths") != new[target_id].get("target_candidate_paths"):
                changes.append({
                    "change_type": "CANDIDATE_PATHS_CHANGED",
                    "target_track_id": target_id,
                })
        return tuple(changes)

    def validation_summary(self):
        return dict(self._totals)

    @staticmethod
    def _metrics(observed_targets, edges, diagnostics):
        probabilities = [
            item["intention_weighted_conflict_probability"] for item in edges
            if item.get("intention_weighted_conflict_probability") is not None
        ]
        return {
            "locally_observed_targets": max(0, observed_targets),
            "targets_evaluated_for_conflict": len(diagnostics),
            "spatial_conflict_edges": len(edges),
            "non_conflicting_targets_filtered": sum(
                item.get("reason") == "NO_SHARED_CONFLICT_ZONE"
                for item in diagnostics
            ),
            "unknown_intention_conservative_edges": sum(
                bool(item.get("spatial_conflict_possible")) and
                item.get("prediction_status") == "UNKNOWN"
                for item in diagnostics
            ),
            "prediction_unavailable_conservative_edges": sum(
                bool(item.get("spatial_conflict_possible")) and
                item.get("prediction_status") == "NOT_AVAILABLE"
                for item in diagnostics
            ),
            "conflict_zones": len({zone for item in edges
                                   for zone in item["shared_conflict_zone_ids"]}),
            "mean_intention_weighted_spatial_conflict_probability": (
                sum(probabilities) / len(probabilities) if probabilities else None
            ),
        }
