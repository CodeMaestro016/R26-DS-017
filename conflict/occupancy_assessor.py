"""Shadow-only map-aware conflict-zone temporal occupancy assessment.

For a front-bumper-referenced track, remaining incoming distance is
max(0, lane_length - lane_position). If a projected zone interval is
[s_start, s_end] and vehicle length is L, front-bumper travel distances are
d_entry = d_incoming + s_start and d_clear = d_incoming + s_end + L.

Strictly positive finite current speed is held constant. Closed occupancy
intervals overlap when max(entries) <= min(clears). For separated intervals,
``temporal_separation_s`` is the non-negative empty time between the earlier
clear time and later entry time. No safety threshold or weighted score is used.
"""

import copy
import math


class ConflictZoneOccupancyAssessor:
    """Evaluate only the spatial edges in one ego AV's current local graph."""

    def __init__(self, path_manager, zone_manager):
        self.path_manager = path_manager
        self.zone_manager = zone_manager
        self._results = {}
        self._totals = self._empty_totals()
        self._conflicting_pairs = set()

    @staticmethod
    def _empty_totals():
        return {
            "spatial_edges_evaluated": 0,
            "candidate_path_zone_evaluations": 0,
            "temporal_conflicts_observed": 0,
            "spatial_only_temporal_separations": 0,
            "unresolved_timing_evaluations": 0,
        }

    @staticmethod
    def interval_relationship(first_entry, first_clear,
                              second_entry, second_clear):
        """Return closed-interval overlap, duration, and unsigned separation."""
        overlap_start = max(float(first_entry), float(second_entry))
        overlap_end = min(float(first_clear), float(second_clear))
        overlaps = overlap_start <= overlap_end
        if overlaps:
            return True, max(0.0, overlap_end - overlap_start), 0.0
        separation = max(
            float(second_entry) - float(first_clear),
            float(first_entry) - float(second_clear),
        )
        return False, 0.0, separation

    @staticmethod
    def _incoming_distance(track, expected_lane_id):
        if track.get("lane_id") != expected_lane_id:
            return None, "UNRESOLVED_PATH_PROGRESS"
        try:
            lane_position = float(track["lane_position"])
            lane_length = float(track["lane_length"])
        except (KeyError, TypeError, ValueError):
            return None, "UNRESOLVED_PATH_PROGRESS"
        if not math.isfinite(lane_position) or not math.isfinite(lane_length):
            return None, "UNRESOLVED_PATH_PROGRESS"
        return max(0.0, lane_length - lane_position), None

    @staticmethod
    def _kinematics(incoming_distance, path_interval, length, speed,
                    current_time):
        try:
            length, speed = float(length), float(speed)
            start, end = map(float, path_interval)
        except (TypeError, ValueError):
            return None, "UNRESOLVED_VEHICLE_STATE"
        if (not math.isfinite(length) or length <= 0.0
                or not all(math.isfinite(value) for value in (start, end))
                or end < start):
            return None, "UNRESOLVED_VEHICLE_STATE"
        distance_entry = incoming_distance + start
        distance_clear = incoming_distance + end + length
        base = {
            "distance_to_zone_entry_m": distance_entry,
            "distance_to_zone_clear_m": distance_clear,
            "vehicle_length_m": length,
            "speed_mps": speed,
        }
        if not math.isfinite(speed) or speed <= 0.0:
            return base, "UNRESOLVED_SPEED"
        time_entry = distance_entry / speed
        time_clear = distance_clear / speed
        base.update({
            "time_to_entry_s": time_entry,
            "time_to_clear_s": time_clear,
            "predicted_entry_time_s": float(current_time) + time_entry,
            "predicted_clear_time_s": float(current_time) + time_clear,
        })
        return base, None

    @staticmethod
    def _candidate_path_ids(edge):
        for manoeuvre, value in edge.get("target_candidate_paths", {}).items():
            path_ids = value if isinstance(value, (tuple, list)) else (value,)
            for path_id in path_ids:
                yield manoeuvre, path_id

    def _evaluate_path(self, ldm, edge, target_id, target_manoeuvre,
                       target_path_id, current_time):
        ego, target = ldm.tracks[ldm.ego_id], ldm.tracks[target_id]
        ego_path_id = edge["ego_path_id"]
        zone = self.zone_manager.zone_record(
            ego_path_id, ego.get("width"),
            target_path_id, target.get("width"),
        )
        if zone is None:
            return None
        ego_path = self.path_manager.paths[ego_path_id]
        target_path = self.path_manager.paths[target_path_id]
        ego_incoming, ego_progress_error = self._incoming_distance(
            ego, ego_path.incoming_lane_id
        )
        target_incoming, target_progress_error = self._incoming_distance(
            target, target_path.incoming_lane_id
        )
        record = {
            "ego_id": ldm.ego_id, "target_id": target_id,
            "timestamp": float(current_time), "ego_path_id": ego_path_id,
            "target_path_id": target_path_id,
            "target_manoeuvre": target_manoeuvre,
            "conflict_zone_id": zone["zone_id"],
            "conflict_type": zone["conflict_type"],
            "ego_incoming_distance_m": ego_incoming,
            "target_incoming_distance_m": target_incoming,
            "ego_zone_path_interval_m": zone["first_path_distance_interval"],
            "target_zone_path_interval_m": zone["second_path_distance_interval"],
            "target_prediction_status": edge.get("prediction_status"),
            "target_observation_age_seconds": edge.get(
                "observation_age_seconds"
            ),
            "ego_vehicle_length_m": ego.get("length"),
            "target_vehicle_length_m": target.get("length"),
            "ego_speed_mps": ego.get("speed"),
            "target_speed_mps": target.get("speed"),
        }
        if ego_progress_error or target_progress_error:
            record.update({
                "temporal_overlap": None, "overlap_duration_s": None,
                "temporal_separation_s": None,
                "status": ego_progress_error or target_progress_error,
            })
            return record
        ego_timing, ego_error = self._kinematics(
            ego_incoming, zone["first_path_distance_interval"],
            ego.get("length"), ego.get("speed"), current_time,
        )
        target_timing, target_error = self._kinematics(
            target_incoming, zone["second_path_distance_interval"],
            target.get("length"), target.get("speed"), current_time,
        )
        self._add_timing_fields(record, "ego", ego_timing)
        self._add_timing_fields(record, "target", target_timing)
        if ego_error or target_error:
            record.update({
                "temporal_overlap": None, "overlap_duration_s": None,
                "temporal_separation_s": None,
                "status": ego_error or target_error,
            })
            return record
        overlap, duration, separation = self.interval_relationship(
            ego_timing["predicted_entry_time_s"],
            ego_timing["predicted_clear_time_s"],
            target_timing["predicted_entry_time_s"],
            target_timing["predicted_clear_time_s"],
        )
        record.update({
            "temporal_overlap": overlap,
            "overlap_duration_s": duration,
            "temporal_separation_s": separation,
            "status": "TEMPORAL_CONFLICT" if overlap else "SPATIAL_ONLY",
        })
        return record

    @staticmethod
    def _add_timing_fields(record, prefix, timing):
        timing = timing or {}
        for source, suffix in (
            ("vehicle_length_m", "vehicle_length_m"),
            ("distance_to_zone_entry_m", "distance_to_zone_entry_m"),
            ("distance_to_zone_clear_m", "distance_to_zone_clear_m"),
            ("speed_mps", "speed_mps"),
            ("time_to_entry_s", "time_to_entry_s"),
            ("time_to_clear_s", "time_to_clear_s"),
            ("predicted_entry_time_s", "predicted_entry_time_s"),
            ("predicted_clear_time_s", "predicted_clear_time_s"),
        ):
            record[f"{prefix}_{suffix}"] = timing.get(source)

    def assess_ldm(self, ldm, current_time):
        graph = ldm.current_conflict_graph or {}
        edge_results = []
        for edge in graph.get("edges", ()):
            self._totals["spatial_edges_evaluated"] += 1
            target_id = edge["target_track_id"]
            if target_id not in ldm.tracks:
                continue
            evaluations = []
            for manoeuvre, path_id in self._candidate_path_ids(edge):
                record = self._evaluate_path(
                    ldm, edge, target_id, manoeuvre, path_id, current_time
                )
                if record is not None:
                    evaluations.append(record)
                    self._totals["candidate_path_zone_evaluations"] += 1
                    if record["status"] == "TEMPORAL_CONFLICT":
                        self._totals["temporal_conflicts_observed"] += 1
                    elif record["status"] == "SPATIAL_ONLY":
                        self._totals["spatial_only_temporal_separations"] += 1
                    else:
                        self._totals["unresolved_timing_evaluations"] += 1
            statuses = {item["status"] for item in evaluations}
            if "TEMPORAL_CONFLICT" in statuses:
                possible, status = True, "TEMPORAL_CONFLICT"
                self._conflicting_pairs.add((ldm.ego_id, target_id))
            elif any(value.startswith("UNRESOLVED_") for value in statuses):
                possible, status = None, "UNRESOLVED_TIMING"
            else:
                possible, status = False, "SPATIAL_ONLY"
            edge_results.append({
                "ego_id": ldm.ego_id, "target_id": target_id,
                "timestamp": float(current_time),
                "temporal_conflict_possible": possible,
                "status": status,
                "evaluations": tuple(evaluations),
            })
        result = {
            "ego_id": ldm.ego_id, "timestamp": float(current_time),
            "edges": tuple(edge_results),
        }
        self._results[ldm.ego_id] = copy.deepcopy(result)
        return copy.deepcopy(result)

    def get_result(self, ego_id):
        return copy.deepcopy(self._results.get(ego_id))

    def validation_summary(self):
        result = dict(self._totals)
        result["unique_ego_target_pairs_with_temporal_conflict"] = len(
            self._conflicting_pairs
        )
        return result

    def reset(self, ego_id=None):
        if ego_id is None:
            self._results.clear()
            self._totals = self._empty_totals()
            self._conflicting_pairs.clear()
        else:
            self._results.pop(ego_id, None)
