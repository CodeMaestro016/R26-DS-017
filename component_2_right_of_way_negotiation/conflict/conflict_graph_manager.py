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

# Import copy for use in this module.
import copy
# Import math for use in this module.
import math
# Import replace from dataclasses for the operations below.
from dataclasses import replace

# Import LocalConflictGraph from .models for the operations below.
from .models import LocalConflictGraph


# Set MANOEUVRES to an immutable set built from a set containing the text 'LEFT', the text 'RIGHT', the text
# 'STRAIGHT'.
MANOEUVRES = frozenset({"LEFT", "RIGHT", "STRAIGHT"})


# Adapt the ConflictEntryMonitor snapshot/final result without re-fusion.
# Input track: the supplied track.
# Output: return the value selected by the matching return branch below.
# Processing: select branches using the stated conditions, then handle the specified errors.
def extract_operational_intention(track):
    """Adapt the ConflictEntryMonitor snapshot/final result without re-fusion."""
    # Set prediction to 'intention_prediction' from track; use None if absent.
    prediction = track.get("intention_prediction")
    # Run this branch when prediction is the same object as None.
    if prediction is None:
        # Return a tuple containing the text 'UNKNOWN', the text 'NOT_AVAILABLE', None to the caller.
        return "UNKNOWN", "NOT_AVAILABLE", None
    # Run this branch when the negation of whether prediction has type dict.
    if not isinstance(prediction, dict):
        # Return a tuple containing the text 'UNKNOWN', the text 'INVALID', None to the caller.
        return "UNKNOWN", "INVALID", None
    # Set label to 'fused_label' from prediction; use the text 'UNKNOWN' if absent.
    label = prediction.get("fused_label", "UNKNOWN")
    # Set status to 'status' from prediction; use the text 'UNKNOWN' if absent.
    status = prediction.get("status", "UNKNOWN")
    # Run this branch when label does not belong to MANOEUVRES and label differs from the text 'UNKNOWN'.
    if label not in MANOEUVRES and label != "UNKNOWN":
        # Return a tuple containing the text 'UNKNOWN', the text 'INVALID', None to the caller.
        return "UNKNOWN", "INVALID", None
    # Run this branch when label equals the text 'UNKNOWN'.
    if label == "UNKNOWN":
        # Return a tuple containing label, the text 'UNKNOWN', None to the caller.
        return label, "UNKNOWN", None

    # The fused label is authoritative. Use probabilities from the stage that
    # operational fusion accepted; agreement uses the later secondary result.
    # Set (primary, secondary) to a tuple containing 'primary' from prediction; use None if absent, 'secondary'
    # from prediction; use None if absent.
    primary, secondary = prediction.get("primary"), prediction.get("secondary")
    # Set stage to secondary when status belongs to a set containing the text 'CONFIRMED_AGREEMENT', the text
    # 'SECONDARY_RECOVERY', otherwise None.
    stage = secondary if status in {
        "CONFIRMED_AGREEMENT", "SECONDARY_RECOVERY"
    # Supply None to the enclosing expression.
    } else None
    # Set probabilities to 'probabilities' from stage; use None if absent when whether stage has type dict,
    # otherwise None.
    probabilities = stage.get("probabilities") if isinstance(stage, dict) else None
    # Run this branch when probabilities is a different object from None.
    if probabilities is not None:
        # Attempt the enclosed operations and route matching exceptions to the handlers below.
        try:
            # Set normalized to a dictionary of name mapped to a floating-point number built from probabilities at
            # name for name in MANOEUVRES.
            normalized = {name: float(probabilities[name]) for name in MANOEUVRES}
            # Set total to the sum of values from normalized.
            total = sum(normalized.values())
            # Run this branch when the negation of whether every item is true in a lazy sequence of
            # math.isfinite(value) and value >= 0.0 for value in normalized.values() or the negation of the result
            # of math.isclose(total, 1.0).
            if (not all(math.isfinite(value) and value >= 0.0
                        # Evaluate values from normalized as part of the enclosing expression.
                        for value in normalized.values())
                    # Supply rel_tol as 1e-06.
                    # Supply abs_tol as 1e-06.
                    or not math.isclose(total, 1.0, rel_tol=1e-6, abs_tol=1e-6)):
                # Set probabilities to None.
                probabilities = None
            # Run this alternative branch when the preceding branch does not apply.
            else:
                # Set probabilities to normalized.
                probabilities = normalized
        # Handle (KeyError, TypeError, ValueError) using the recovery steps below.
        except (KeyError, TypeError, ValueError):
            # Set probabilities to None.
            probabilities = None
    # Return a tuple containing label, the text 'PREDICTED', probabilities to the caller.
    return label, "PREDICTED", probabilities


# Own independent dynamic graph snapshots for each ego LDM.
# Instances expose the attributes and methods implemented in this class.
class ConflictGraphManager:
    """Own independent dynamic graph snapshots for each ego LDM."""

    # Initialize the instance attributes and collaborators used by the operations below.
    # Input path_manager: the supplied path manager.
    # Input zone_manager: the supplied zone manager.
    # Output: no explicit value; normal completion returns None.
    def __init__(self, path_manager, zone_manager):
        # Set self.path_manager to path_manager.
        self.path_manager = path_manager
        # Set self.zone_manager to zone_manager.
        self.zone_manager = zone_manager
        # Set self._graphs to an empty dictionary.
        self._graphs = {}
        # Set self._change_events to an empty dictionary.
        self._change_events = {}
        # Set self._totals to the result of self._empty_totals().
        self._totals = self._empty_totals()

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Empty totals using the inputs and processing steps below.
    # Output: a dictionary containing graphs_built, spatial_conflict_edges_observed,
    # unknown_intention_conservative_edges,...
    def _empty_totals():
        # Return a dictionary containing graphs_built, spatial_conflict_edges_observed,
        # unknown_intention_conservative_edges,... to the caller.
        return {
            # Store 0 under 'graphs_built'.
            # Store 0 under 'spatial_conflict_edges_observed'.
            "graphs_built": 0, "spatial_conflict_edges_observed": 0,
            # Store 0 under 'unknown_intention_conservative_edges'.
            "unknown_intention_conservative_edges": 0,
            # Store 0 under 'prediction_unavailable_conservative_edges'.
            "prediction_unavailable_conservative_edges": 0,
            # Store 0 under 'non_conflicting_targets_filtered'.
            "non_conflicting_targets_filtered": 0,
        }

    # Reset using the inputs and processing steps below.
    # Input ego_id: the identifier of the ego vehicle.
    # Output: no explicit value; normal completion returns None.
    # Processing: select branches using the stated conditions.
    def reset(self, ego_id=None):
        # Run this branch when ego_id is the same object as None.
        if ego_id is None:
            # Clear the stored entries in self._graphs.
            self._graphs.clear()
            # Clear the stored entries in self._change_events.
            self._change_events.clear()
            # Set self._totals to the result of self._empty_totals().
            self._totals = self._empty_totals()
        # Run this alternative branch when the preceding branch does not apply.
        else:
            # Remove the requested entry from self._graphs.
            self._graphs.pop(ego_id, None)
            # Remove the requested entry from self._change_events.
            self._change_events.pop(ego_id, None)

    # Get graph using the inputs and processing steps below.
    # Input ego_id: the identifier of the ego vehicle.
    # Output: the result of copy.deepcopy(the result of graph.to_dict()) when graph is a different object from
    # None, otherwise None.
    def get_graph(self, ego_id):
        # Set graph to ego_id from self._graphs; use None if absent.
        graph = self._graphs.get(ego_id)
        # Return the result of copy.deepcopy(the result of graph.to_dict()) when graph is a different object from
        # None, otherwise None to the caller.
        return copy.deepcopy(graph.to_dict()) if graph is not None else None

    # Build local graph using the inputs and processing steps below.
    # Input ldm: the supplied ldm.
    # Input current_time: the supplied current time.
    # Output: return the value selected by the matching return branch below.
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    def build_local_graph(self, ldm, current_time):
        # Set ego_id to ldm.ego_id.
        ego_id = ldm.ego_id
        # Set ego to ego_id from ldm.tracks; use None if absent.
        ego = ldm.tracks.get(ego_id)
        # Set nodes to a tuple built from the sorted values from ldm.tracks.
        nodes = tuple(sorted(ldm.tracks))
        # Run this branch when ego is the same object as None.
        if ego is None:
            # Return the result of self._store(the result of LocalConflictGraph(ego_id, a floating-point number
            # built from current_time, None,...) to the caller.
            return self._store(LocalConflictGraph(
                # Supply a tuple containing a dictionary containing ego_id, reason to LocalConflictGraph.
                ego_id, float(current_time), None, nodes, (), ({
                    # Store ego_id under 'ego_id'.
                    # Store the text 'MISSING_EGO_PLAN' under 'reason'.
                    "ego_id": ego_id, "reason": "MISSING_EGO_PLAN"
                # Supply the result of self._metrics(the number of entries in nodes minus 1, an empty tuple, an
                # empty tuple) to LocalConflictGraph.
                },), self._metrics(len(nodes) - 1, (), ()),
            ))
        # Set ego_manoeuvre to 'self_planned_manoeuvre' from ego; use None if absent.
        ego_manoeuvre = ego.get("self_planned_manoeuvre")
        # Set ego_path to the result of self.path_manager.resolve_path('lane_id' from ego; use the text '' if
        # absent, ego_manoeuvre).
        ego_path = self.path_manager.resolve_path(
            # Supply 'lane_id' from ego; use the text '' if absent to self.path_manager.resolve_path.
            ego.get("lane_id", ""), ego_manoeuvre
        )
        # Run this branch when ego_path is the same object as None.
        if ego_path is None:
            # Set previous to ego_id from self._graphs; use None if absent.
            previous = self._graphs.get(ego_id)
            # Set previous_path to previous.ego_path_id from self.path_manager.paths; use None if absent when
            # previous is a different object from None and previous.ego_path_id, otherwise None.
            previous_path = (
                # Evaluate previous.ego_path_id from self.path_manager.paths; use None if absent when previous is
                # a different object from None and previous.ego_path_id, otherwise None as part of the enclosing
                # expression.
                self.path_manager.paths.get(previous.ego_path_id)
                # Evaluate previous is a different object from None and previous.ego_path_id as part of the
                # enclosing expression.
                if previous is not None and previous.ego_path_id else None
            )
            # Run this branch when previous_path is a different object from None and previous_path.manoeuvre
            # equals ego_manoeuvre and the result of self.path_manager.lane_belongs_to_path('lane_id' from ego;
            # use the text '' if absent, previous_path).
            if (previous_path is not None
                    # Evaluate previous_path.manoeuvre equals ego_manoeuvre as part of the enclosing expression.
                    and previous_path.manoeuvre == ego_manoeuvre
                    # Evaluate the result of self.path_manager.lane_belongs_to_path('lane_id' from ego; use the
                    # text '' if absent, previous_path) as part of the enclosing expression.
                    and self.path_manager.lane_belongs_to_path(
                        # Supply 'lane_id' from ego; use the text '' if absent to
                        # self.path_manager.lane_belongs_to_path.
                        ego.get("lane_id", ""), previous_path
                    )):
                # Set ego_path to previous_path.
                ego_path = previous_path
        # Run this branch when ego_path is the same object as None.
        if ego_path is None:
            # Set ego_options to ego_manoeuvre from self.path_manager.feasible_paths(ego.get('lane_id', '')); use
            # an empty tuple if absent.
            ego_options = self.path_manager.feasible_paths(
                # Supply 'lane_id' from ego; use the text '' if absent to self.path_manager.feasible_paths.
                ego.get("lane_id", "")
            # Supply ego_manoeuvre to self.path_manager.feasible_paths(ego.get('lane_id', '')).get.
            ).get(ego_manoeuvre, ())
            # Set reason to the text 'MISSING_EGO_PLAN' when ego_manoeuvre does not belong to MANOEUVRES,
            # otherwise the text 'NOT_ON_INTERSECTION_APPROACH' when 'lane_id' from ego; use None if absent does
            # not belong to self.path_manager.incoming_lane_ids, otherwise the text 'AMBIGUOUS_EGO_PATH' when
            # len(ego_options) is greater than 1, otherwise the text 'MISSING_MAP_CONNECTION'.
            reason = (
                # Evaluate the text 'MISSING_EGO_PLAN' when ego_manoeuvre does not belong to MANOEUVRES, otherwise
                # the text 'NOT_ON_INTERSECTION_APPROACH' when 'lane_id' from ego; use None if absent does not
                # belong to self.path_manager.incoming_lane_ids, otherwise the text 'AMBIGUOUS_EGO_PATH' when
                # len(ego_options) is greater than 1, otherwise the text 'MISSING_MAP_CONNECTION' as part of the
                # enclosing expression.
                "MISSING_EGO_PLAN" if ego_manoeuvre not in MANOEUVRES
                # Evaluate the text 'NOT_ON_INTERSECTION_APPROACH' when 'lane_id' from ego; use None if absent
                # does not belong to self.path_manager.incoming_lane_ids, otherwise the text 'AMBIGUOUS_EGO_PATH'
                # when the number of entries in ego_options is greater than 1, otherwise the text
                # 'MISSING_MAP_CONNECTION' as part of the enclosing expression.
                else "NOT_ON_INTERSECTION_APPROACH" if ego.get("lane_id") not in
                # Evaluate self.path_manager.incoming_lane_ids as part of the enclosing expression.
                self.path_manager.incoming_lane_ids
                # Evaluate the text 'AMBIGUOUS_EGO_PATH' when the number of entries in ego_options is greater than
                # 1, otherwise the text 'MISSING_MAP_CONNECTION' as part of the enclosing expression.
                else "AMBIGUOUS_EGO_PATH" if len(ego_options) > 1
                # Supply the text 'MISSING_MAP_CONNECTION' to the enclosing expression.
                else "MISSING_MAP_CONNECTION"
            )
            # Set diagnostics to a tuple built from a lazy sequence of a dictionary containing ego_id,
            # target_track_id, ego_lane, ego_manoeuvre, ego_path_id, reason for target_id in the sorted values
            # from set(ldm.tracks) minus {ego_id}.
            diagnostics = tuple({
                # Store ego_id under 'ego_id'.
                # Store target_id under 'target_track_id'.
                "ego_id": ego_id, "target_track_id": target_id,
                # Store 'lane_id' from ego; use the text '' if absent under 'ego_lane'.
                "ego_lane": ego.get("lane_id", ""),
                # Store ego_manoeuvre under 'ego_manoeuvre'.
                # Store None under 'ego_path_id'.
                "ego_manoeuvre": ego_manoeuvre, "ego_path_id": None,
                # Store reason under 'reason'.
                "reason": reason,
            # Evaluate the sorted values from a set built from ldm.tracks minus a set containing ego_id as part of
            # the enclosing expression.
            } for target_id in sorted(set(ldm.tracks) - {ego_id}))
            # Return the result of self._store(the result of LocalConflictGraph(ego_id, a floating-point number
            # built from current_time, None,...) to the caller.
            return self._store(LocalConflictGraph(
                # Supply a floating-point number built from current_time to LocalConflictGraph.
                ego_id, float(current_time), None, nodes, (), diagnostics,
                # Supply the result of self._metrics(the number of entries in nodes minus 1, an empty tuple,
                # diagnostics) to LocalConflictGraph.
                self._metrics(len(nodes) - 1, (), diagnostics),
            ))

        # Set (edges, diagnostics) to a tuple containing an empty list, an empty list.
        edges, diagnostics = [], []
        # Iterate over the sorted values from a set built from ldm.tracks minus a set containing ego_id, binding
        # each item to target_id.
        for target_id in sorted(set(ldm.tracks) - {ego_id}):
            # Set target to ldm.tracks at target_id.
            target = ldm.tracks[target_id]
            # Set (label, prediction_status, probabilities) to the result of
            # extract_operational_intention(target).
            label, prediction_status, probabilities = extract_operational_intention(target)
            # Set feasible to the result of self.path_manager.feasible_paths('lane_id' from target; use the text
            # '' if absent).
            feasible = self.path_manager.feasible_paths(target.get("lane_id", ""))
            # Run this branch when the negation of feasible.
            if not feasible:
                # Set feasible to the result of self.path_manager.paths_compatible_with_observed_lane('lane_id'
                # from target; use the text '' if absent).
                feasible = self.path_manager.paths_compatible_with_observed_lane(
                    # Supply 'lane_id' from target; use the text '' if absent to
                    # self.path_manager.paths_compatible_with_observed_lane.
                    target.get("lane_id", "")
                )
            # Set reason to None.
            reason = None
            # Run this branch when the negation of feasible.
            if not feasible:
                # Set candidate_paths to an empty dictionary.
                candidate_paths = {}
                # Set reason to the text 'NOT_ON_INTERSECTION_APPROACH'.
                reason = "NOT_ON_INTERSECTION_APPROACH"
            # Run this branch when prediction_status equals the text 'INVALID'.
            elif prediction_status == "INVALID":
                # Set candidate_paths to feasible.
                candidate_paths = feasible
                # Set reason to the text 'INVALID_INTENTION_RESULT'.
                reason = "INVALID_INTENTION_RESULT"
            # Run this branch when prediction_status equals the text 'PREDICTED' and label belongs to feasible.
            elif prediction_status == "PREDICTED" and label in feasible:
                # Set candidate_paths to a dictionary of the supplied entries.
                candidate_paths = {label: feasible[label]}
            # Run this branch when prediction_status equals the text 'PREDICTED'.
            elif prediction_status == "PREDICTED":
                # Set candidate_paths to feasible.
                candidate_paths = feasible
                # Set prediction_status to the text 'INVALID'.
                prediction_status = "INVALID"
                # Set probabilities to None.
                probabilities = None
                # Set reason to the text 'NO_FEASIBLE_PATH'.
                reason = "NO_FEASIBLE_PATH"
            # Run this alternative branch when the preceding branch does not apply.
            else:
                # Set candidate_paths to feasible.
                candidate_paths = feasible

            # Set (conflicting, zones, types) to a tuple containing an empty list, an empty set, an empty set.
            conflicting, zones, types = [], set(), set()
            # Set spatially_conflicting_paths to an empty dictionary.
            spatially_conflicting_paths = {}
            # Iterate over key/value pairs from feasible, binding each item to (manoeuvre, target_paths).
            for manoeuvre, target_paths in feasible.items():
                # Set path_matches to an empty list.
                path_matches = []
                # Iterate over target_paths, binding each item to target_path.
                for target_path in target_paths:
                    # Set (relationship, zone) to the result of
                    # self.zone_manager.coordinated_conflict(ego_path.path_id, 'width' from ego; use None if
                    # absent, target_path.path_id, 'width' from...).
                    relationship, zone = self.zone_manager.coordinated_conflict(
                        # Supply ego_path.path_id to self.zone_manager.coordinated_conflict.
                        ego_path.path_id, ego.get("width"),
                        # Supply target_path.path_id to self.zone_manager.coordinated_conflict.
                        target_path.path_id, target.get("width"),
                    )
                    # Run this branch when zone is a different object from None.
                    if zone is not None:
                        # Append target_path to path_matches.
                        path_matches.append(target_path)
                        # Add relationship.conflict_zone_id to zones.
                        zones.add(relationship.conflict_zone_id)
                        # Add relationship.conflict_type to types.
                        types.add(relationship.conflict_type)
                # Run this branch when path_matches.
                if path_matches:
                    # Append manoeuvre to conflicting.
                    conflicting.append(manoeuvre)
                    # Set spatially_conflicting_paths[manoeuvre] to a tuple built from path_matches.
                    spatially_conflicting_paths[manoeuvre] = tuple(path_matches)

            # Set probability to None.
            probability = None
            # Run this branch when probabilities is a different object from None.
            if probabilities is not None:
                # Set probability_conflicts to an empty set.
                probability_conflicts = set()
                # Iterate over key/value pairs from feasible, binding each item to (manoeuvre, target_paths).
                for manoeuvre, target_paths in feasible.items():
                    # Run this branch when whether any item is true in a lazy sequence of
                    # self.zone_manager.coordinated_conflict(ego_path.path_id, ego.get('width'),
                    # target_path.path_id,... at 1 is a different object from None for target_path in
                    # target_paths.
                    if any(self.zone_manager.coordinated_conflict(
                        # Supply ego_path.path_id to self.zone_manager.coordinated_conflict.
                        ego_path.path_id, ego.get("width"),
                        # Supply target_path.path_id to self.zone_manager.coordinated_conflict.
                        target_path.path_id, target.get("width"),
                    # Evaluate target_paths as part of the enclosing expression.
                    )[1] is not None for target_path in target_paths):
                        # Add manoeuvre to probability_conflicts.
                        probability_conflicts.add(manoeuvre)
                # Set probability to the sum of a lazy sequence of probabilities at name for name in
                # probability_conflicts.
                probability = sum(
                    # Evaluate probability_conflicts as part of the enclosing expression.
                    probabilities[name] for name in probability_conflicts
                )
                # Set probability to the minimum of 1.0, the maximum of 0.0, probability.
                probability = min(1.0, max(0.0, probability))
            # Set possible to a Boolean built from conflicting.
            possible = bool(conflicting)
            # Run this branch when reason is the same object as None.
            if reason is None:
                # Run this branch when possible.
                if possible:
                    # Set selected_conflicts to whether any item is true in a lazy sequence of name belongs to
                    # spatially_conflicting_paths for name in candidate_paths.
                    selected_conflicts = any(
                        # Evaluate name belongs to spatially_conflicting_paths as part of the enclosing
                        # expression.
                        name in spatially_conflicting_paths
                        # Evaluate candidate_paths as part of the enclosing expression.
                        for name in candidate_paths
                    )
                    # Set reason to the text 'CONFLICTING_PREDICTED_PATH' when prediction_status equals the text
                    # 'PREDICTED' and selected_conflicts, otherwise the text 'CONFLICTING_FEASIBLE_PATH_SET' when
                    # prediction_status equals the text 'PREDICTED', otherwise the text
                    # 'CONFLICTING_UNKNOWN_PATH_SET'.
                    reason = (
                        "CONFLICTING_PREDICTED_PATH"
                        # Evaluate prediction_status equals the text 'PREDICTED' and selected_conflicts as part of
                        # the enclosing expression.
                        if prediction_status == "PREDICTED" and selected_conflicts
                        # Evaluate the text 'CONFLICTING_FEASIBLE_PATH_SET' when prediction_status equals the text
                        # 'PREDICTED', otherwise the text 'CONFLICTING_UNKNOWN_PATH_SET' as part of the enclosing
                        # expression.
                        else "CONFLICTING_FEASIBLE_PATH_SET"
                        # Evaluate prediction_status equals the text 'PREDICTED' as part of the enclosing
                        # expression.
                        if prediction_status == "PREDICTED"
                        # Supply the text 'CONFLICTING_UNKNOWN_PATH_SET' to the enclosing expression.
                        else "CONFLICTING_UNKNOWN_PATH_SET"
                    )
                # Run this alternative branch when the preceding branch does not apply.
                else:
                    # Set reason to the text 'NO_SHARED_CONFLICT_ZONE'.
                    reason = "NO_SHARED_CONFLICT_ZONE"
            # Set diagnostic to a dictionary containing ego_id, target_track_id, ego_lane, ego_manoeuvre,
            # ego_path_id, target_lane,...
            diagnostic = {
                # Store ego_id under 'ego_id'.
                # Store target_id under 'target_track_id'.
                "ego_id": ego_id, "target_track_id": target_id,
                # Store 'lane_id' from ego; use the text '' if absent under 'ego_lane'.
                "ego_lane": ego.get("lane_id", ""),
                # Store ego_manoeuvre under 'ego_manoeuvre'.
                "ego_manoeuvre": ego_manoeuvre,
                # Store ego_path.path_id under 'ego_path_id'.
                "ego_path_id": ego_path.path_id,
                # Store 'lane_id' from target; use the text '' if absent under 'target_lane'.
                "target_lane": target.get("lane_id", ""),
                # Store label under 'target_prediction'.
                "target_prediction": label,
                # Store a dictionary of name mapped to paths[0].path_id when the number of entries in paths equals
                # 1, otherwise a tuple built from a lazy sequence of path.path_id for path in paths for (name,
                # paths) in the sorted values from key/value pairs from candidate_paths under
                # 'target_candidate_paths'.
                "target_candidate_paths": {
                    # Evaluate paths[0].path_id when the number of entries in paths equals 1, otherwise a tuple
                    # built from a lazy sequence of path.path_id for path in paths as part of the enclosing
                    # expression.
                    name: (paths[0].path_id if len(paths) == 1 else tuple(
                        # Evaluate path.path_id as part of the enclosing expression.
                        path.path_id for path in paths
                    # Evaluate the sorted values from key/value pairs from candidate_paths as part of the
                    # enclosing expression.
                    )) for name, paths in sorted(candidate_paths.items())
                },
                # Store a dictionary of name mapped to paths[0].path_id when the number of entries in paths equals
                # 1, otherwise a tuple built from a lazy sequence of path.path_id for path in paths for (name,
                # paths) in the sorted values from key/value pairs from spatially_conflicting_paths under
                # 'spatially_conflicting_candidate_paths'.
                "spatially_conflicting_candidate_paths": {
                    # Evaluate paths[0].path_id when the number of entries in paths equals 1, otherwise a tuple
                    # built from a lazy sequence of path.path_id for path in paths as part of the enclosing
                    # expression.
                    name: (paths[0].path_id if len(paths) == 1 else tuple(
                        # Evaluate path.path_id as part of the enclosing expression.
                        path.path_id for path in paths
                    # Evaluate the sorted values from key/value pairs from spatially_conflicting_paths as part of
                    # the enclosing expression.
                    )) for name, paths in sorted(
                        # Supply key/value pairs from spatially_conflicting_paths to sorted.
                        spatially_conflicting_paths.items()
                    )
                },
                # Store the sum of a lazy sequence of the number of entries in paths for paths in values from
                # feasible minus the sum of a lazy sequence of the number of entries in paths for paths in values
                # from spatially_conflicting_paths under 'non_conflicting_candidate_path_count'.
                "non_conflicting_candidate_path_count": (
                    # Evaluate the sum of a lazy sequence of the number of entries in paths for paths in values
                    # from feasible minus the sum of a lazy sequence of the number of entries in paths for paths
                    # in values from spatially_conflicting_paths as part of the enclosing expression.
                    sum(len(paths) for paths in feasible.values())
                    # Evaluate the sum of a lazy sequence of the number of entries in paths for paths in values
                    # from spatially_conflicting_paths as part of the enclosing expression.
                    - sum(len(paths) for paths in spatially_conflicting_paths.values())
                ),
                # Store a tuple built from the sorted values from conflicting under 'conflicting_manoeuvres'.
                "conflicting_manoeuvres": tuple(sorted(conflicting)),
                # Store a tuple built from the sorted values from zones under 'shared_conflict_zone_ids'.
                "shared_conflict_zone_ids": tuple(sorted(zones)),
                # Store a tuple built from the sorted values from types under 'conflict_types'.
                "conflict_types": tuple(sorted(types)),
                # Store possible under 'spatial_conflict_possible'.
                "spatial_conflict_possible": possible,
                # Store probability under 'intention_weighted_conflict_probability'.
                "intention_weighted_conflict_probability": probability,
                # Store prediction_status under 'prediction_status'.
                "prediction_status": prediction_status,
                # Store the maximum of 0.0, a floating-point number built from current_time minus a floating-point
                # number built from... under 'observation_age_seconds'.
                "observation_age_seconds": max(
                    # Supply a floating-point number built from current_time minus a floating-point number built
                    # from 'last_observed_time' from target; use current_time if absent to max.
                    0.0, float(current_time) -
                    # Evaluate a floating-point number built from 'last_observed_time' from target; use
                    # current_time if absent as part of the enclosing expression.
                    float(target.get("last_observed_time", current_time))
                ),
                # Store a floating-point number built from current_time under 'timestamp'.
                # Store reason under 'reason'.
                "timestamp": float(current_time), "reason": reason,
            }
            # Append diagnostic to diagnostics.
            diagnostics.append(diagnostic)
            # Run this branch when possible.
            if possible:
                # Append a dictionary built from diagnostic to edges.
                edges.append(dict(diagnostic))
        # Set graph to the result of LocalConflictGraph(ego_id, a floating-point number built from current_time,
        # ego_path.path_id, nodes, a tuple built...).
        graph = LocalConflictGraph(
            # Supply a floating-point number built from current_time to LocalConflictGraph.
            ego_id, float(current_time), ego_path.path_id, nodes,
            # Supply a tuple built from diagnostics to LocalConflictGraph.
            tuple(edges), tuple(diagnostics),
            # Supply the result of self._metrics(the number of entries in nodes minus 1, edges, diagnostics) to
            # LocalConflictGraph.
            self._metrics(len(nodes) - 1, edges, diagnostics),
        )
        # Return the result of self._store(graph) to the caller.
        return self._store(graph)

    # Store using the inputs and processing steps below.
    # Input graph: the supplied graph.
    # Output: the result of copy.deepcopy(the result of graph.to_dict()).
    # Processing: iterate over the relevant records.
    def _store(self, graph):
        # Set previous to graph.ego_id from self._graphs; use None if absent.
        previous = self._graphs.get(graph.ego_id)
        # Set changes to the result of self._detect_changes(previous, graph).
        changes = self._detect_changes(previous, graph)
        # Set graph to the result of replace(graph).
        graph = replace(graph, changes=tuple(changes))
        # Set self._graphs[graph.ego_id] to graph.
        self._graphs[graph.ego_id] = graph
        # Set self._change_events[graph.ego_id] to a tuple built from changes.
        self._change_events[graph.ego_id] = tuple(changes)
        # Update self._totals['graphs_built'] to its current value plus 1.
        self._totals["graphs_built"] += 1
        # Update self._totals['spatial_conflict_edges_observed'] to its current value plus the number of entries
        # in graph.edges.
        self._totals["spatial_conflict_edges_observed"] += len(graph.edges)
        # Iterate over a tuple containing the text 'unknown_intention_conservative_edges', the text
        # 'prediction_unavailable_conservative_edges', the..., binding each item to key.
        for key in (
            "unknown_intention_conservative_edges",
            "prediction_unavailable_conservative_edges",
            "non_conflicting_targets_filtered",
        ):
            # Update self._totals[key] to its current value plus graph.metrics at key.
            self._totals[key] += graph.metrics[key]
        # Return the result of copy.deepcopy(the result of graph.to_dict()) to the caller.
        return copy.deepcopy(graph.to_dict())

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Detect changes using the inputs and processing steps below.
    # Input previous: the supplied previous.
    # Input current: the supplied current.
    # Output: return the value selected by the matching return branch below.
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    def _detect_changes(previous, current):
        # Run this branch when previous is the same object as None.
        if previous is None:
            # Return a tuple built from a lazy sequence of a dictionary containing change_type, target_track_id
            # for edge in current.edges to the caller.
            return tuple({
                # Store the text 'EDGE_ADDED' under 'change_type'.
                # Store edge at 'target_track_id' under 'target_track_id'.
                "change_type": "EDGE_ADDED", "target_track_id": edge["target_track_id"]
            # Evaluate current.edges as part of the enclosing expression.
            } for edge in current.edges)
        # Set old to a dictionary of item at 'target_track_id' mapped to item for item in previous.diagnostics.
        old = {item["target_track_id"]: item for item in previous.diagnostics}
        # Set new to a dictionary of item at 'target_track_id' mapped to item for item in current.diagnostics.
        new = {item["target_track_id"]: item for item in current.diagnostics}
        # Set changes to an empty list.
        changes = []
        # Set old_edges to a set of item at 'target_track_id' for item in previous.edges.
        old_edges = {item["target_track_id"] for item in previous.edges}
        # Set new_edges to a set of item at 'target_track_id' for item in current.edges.
        new_edges = {item["target_track_id"] for item in current.edges}
        # Iterate over the sorted values from new_edges minus old_edges, binding each item to target_id.
        for target_id in sorted(new_edges - old_edges):
            # Append a dictionary containing change_type, target_track_id to changes.
            changes.append({"change_type": "EDGE_ADDED", "target_track_id": target_id})
        # Iterate over the sorted values from old_edges minus new_edges, binding each item to target_id.
        for target_id in sorted(old_edges - new_edges):
            # Append a dictionary containing change_type, target_track_id to changes.
            changes.append({"change_type": "EDGE_REMOVED", "target_track_id": target_id})
        # Iterate over the sorted values from a set built from old intersected with a set built from new, binding
        # each item to target_id.
        for target_id in sorted(set(old) & set(new)):
            # Run this branch when 'prediction_status' from old[target_id]; use None if absent differs from
            # 'prediction_status' from new[target_id]; use None if absent.
            if old[target_id].get("prediction_status") != new[target_id].get("prediction_status"):
                # Append a dictionary containing change_type, target_track_id, from, to to changes.
                changes.append({
                    "change_type": "PREDICTION_STATUS_CHANGED",
                    # Store target_id under 'target_track_id'.
                    "target_track_id": target_id,
                    # Store 'prediction_status' from old[target_id]; use None if absent under 'from'.
                    "from": old[target_id].get("prediction_status"),
                    # Store 'prediction_status' from new[target_id]; use None if absent under 'to'.
                    "to": new[target_id].get("prediction_status"),
                })
            # Run this branch when 'target_candidate_paths' from old[target_id]; use None if absent differs from
            # 'target_candidate_paths' from new[target_id]; use None if absent.
            if old[target_id].get("target_candidate_paths") != new[target_id].get("target_candidate_paths"):
                # Append a dictionary containing change_type, target_track_id to changes.
                changes.append({
                    "change_type": "CANDIDATE_PATHS_CHANGED",
                    # Store target_id under 'target_track_id'.
                    "target_track_id": target_id,
                })
        # Return a tuple built from changes to the caller.
        return tuple(changes)

    # Validation summary using the inputs and processing steps below.
    # Output: a dictionary built from self._totals.
    def validation_summary(self):
        # Return a dictionary built from self._totals to the caller.
        return dict(self._totals)

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Metrics using the inputs and processing steps below.
    # Input observed_targets: the supplied observed targets.
    # Input edges: the supplied edges.
    # Input diagnostics: the supplied diagnostics.
    # Output: a dictionary containing locally_observed_targets, targets_evaluated_for_conflict,
    # spatial_conflict_edges,...
    def _metrics(observed_targets, edges, diagnostics):
        # Set probabilities to a list of item at 'intention_weighted_conflict_probability' for item in edges;
        # retain entries satisfying 'intention_weighted_conflict_probability' from item; use None if absent is a
        # different...
        probabilities = [
            # Evaluate item at 'intention_weighted_conflict_probability' as part of the enclosing expression.
            item["intention_weighted_conflict_probability"] for item in edges
            # Evaluate 'intention_weighted_conflict_probability' from item; use None if absent is a different
            # object from None as part of the enclosing expression.
            if item.get("intention_weighted_conflict_probability") is not None
        ]
        # Return a dictionary containing locally_observed_targets, targets_evaluated_for_conflict,
        # spatial_conflict_edges,... to the caller.
        return {
            # Store the maximum of 0, observed_targets under 'locally_observed_targets'.
            "locally_observed_targets": max(0, observed_targets),
            # Store the number of entries in diagnostics under 'targets_evaluated_for_conflict'.
            "targets_evaluated_for_conflict": len(diagnostics),
            # Store the number of entries in edges under 'spatial_conflict_edges'.
            "spatial_conflict_edges": len(edges),
            # Store the sum of a lazy sequence of 'reason' from item; use None if absent equals the text
            # 'NO_SHARED_CONFLICT_ZONE' for item in diagnostics under 'non_conflicting_targets_filtered'.
            "non_conflicting_targets_filtered": sum(
                # Evaluate 'reason' from item; use None if absent equals the text 'NO_SHARED_CONFLICT_ZONE' as
                # part of the enclosing expression.
                item.get("reason") == "NO_SHARED_CONFLICT_ZONE"
                # Evaluate diagnostics as part of the enclosing expression.
                for item in diagnostics
            ),
            # Store the sum of a lazy sequence of a Boolean built from item.get('spatial_conflict_possible') and
            # item.get('prediction_status') equals 'UNKNOWN' for item in diagnostics under
            # 'unknown_intention_conservative_edges'.
            "unknown_intention_conservative_edges": sum(
                # Evaluate a Boolean built from 'spatial_conflict_possible' from item; use None if absent and
                # 'prediction_status' from item; use None if absent equals the text 'UNKNOWN' as part of the
                # enclosing expression.
                bool(item.get("spatial_conflict_possible")) and
                # Evaluate 'prediction_status' from item; use None if absent equals the text 'UNKNOWN' as part of
                # the enclosing expression.
                item.get("prediction_status") == "UNKNOWN"
                # Evaluate diagnostics as part of the enclosing expression.
                for item in diagnostics
            ),
            # Store the sum of a lazy sequence of a Boolean built from item.get('spatial_conflict_possible') and
            # item.get('prediction_status') equals 'NOT_AVAILABLE' for item in diagnostics under
            # 'prediction_unavailable_conservative_edges'.
            "prediction_unavailable_conservative_edges": sum(
                # Evaluate a Boolean built from 'spatial_conflict_possible' from item; use None if absent and
                # 'prediction_status' from item; use None if absent equals the text 'NOT_AVAILABLE' as part of the
                # enclosing expression.
                bool(item.get("spatial_conflict_possible")) and
                # Evaluate 'prediction_status' from item; use None if absent equals the text 'NOT_AVAILABLE' as
                # part of the enclosing expression.
                item.get("prediction_status") == "NOT_AVAILABLE"
                # Evaluate diagnostics as part of the enclosing expression.
                for item in diagnostics
            ),
            # Store the number of entries in a set of zone for item in edges under 'conflict_zones'.
            "conflict_zones": len({zone for item in edges
                                   # Evaluate item at 'shared_conflict_zone_ids' as part of the enclosing
                                   # expression.
                                   for zone in item["shared_conflict_zone_ids"]}),
            # Store the sum of probabilities divided by the number of entries in probabilities when probabilities,
            # otherwise None under 'mean_intention_weighted_spatial_conflict_probability'.
            "mean_intention_weighted_spatial_conflict_probability": (
                # Evaluate the sum of probabilities divided by the number of entries in probabilities when
                # probabilities, otherwise None as part of the enclosing expression.
                sum(probabilities) / len(probabilities) if probabilities else None
            ),
        }
