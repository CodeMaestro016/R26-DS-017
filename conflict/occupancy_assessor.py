"""Shadow-only map-aware conflict-zone temporal occupancy assessment.

Movement coordinate ``s=0`` is the end of the incoming lane. Front-bumper
progress is negative before the junction, projected onto the exact internal
movement centerline inside it, and continues as path length plus outgoing-lane
position. For zone interval [s_start, s_end] and vehicle length L:

    d_entry = max(0, s_start - s_vehicle)
    d_clear = max(0, s_end + L - s_vehicle)

Closed occupancy intervals overlap at boundary contact. No path-distance,
speed, temporal-safety threshold, or weighted score is used.
"""

import copy
import math


class ConflictZoneOccupancyAssessor:
    """Evaluate spatial graph edges using ego-local state and static geometry."""

    NON_APPLICABLE = frozenset({
        "INCOMPATIBLE_WITH_OBSERVED_LANE", "NO_APPLICABLE_ZONE"
    })

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
            "currently_occupied_zone_evaluations": 0,
            "cleared_zone_evaluations": 0,
            "unresolved_timing_evaluations": 0,
            "unresolved_path_progress": 0,
            "unresolved_speed": 0,
            "unresolved_vehicle_state": 0,
            "incompatible_with_observed_lane": 0,
            "no_applicable_zone": 0,
            "unresolved_no_applicable_evaluation": 0,
            "candidate_paths_rejected_by_observed_lane": 0,
            "nominal_timing_unavailable_due_to_zero_speed": 0,
            "earliest_reachability_calculations": 0,
            "stopped_vehicles_with_finite_earliest_arrival": 0,
            "vehicles_able_to_stop_before_zone": 0,
            "vehicles_unable_to_stop_before_zone": 0,
            "physical_state_or_dynamics_unresolved": 0,
            "non_conflicting_candidate_paths_excluded": 0,
        }

    @staticmethod
    def interval_relationship(first_entry, first_clear,
                              second_entry, second_clear):
        overlap_start = max(float(first_entry), float(second_entry))
        overlap_end = min(float(first_clear), float(second_clear))
        overlaps = overlap_start <= overlap_end
        if overlaps:
            return True, max(0.0, overlap_end - overlap_start), 0.0
        return False, 0.0, max(
            float(second_entry) - float(first_clear),
            float(first_entry) - float(second_clear),
        )

    @staticmethod
    def occupancy_state(path_progress, path_interval, length):
        start, end = map(float, path_interval)
        progress, length = float(path_progress), float(length)
        if not all(math.isfinite(value) for value in (start, end, progress, length)):
            return None, "UNRESOLVED_VEHICLE_STATE"
        if length <= 0.0 or end < start:
            return None, "UNRESOLVED_VEHICLE_STATE"
        if progress < start:
            return "BEFORE_ZONE", None
        if progress < end + length:
            return "CURRENTLY_OCCUPYING", None
        return "CLEARED_ZONE", None

    @staticmethod
    def _timing_from_progress(progress, path_interval, length, speed,
                              current_time):
        try:
            progress, length, speed = map(float, (progress, length, speed))
            start, end = map(float, path_interval)
        except (TypeError, ValueError):
            return None, None, "UNRESOLVED_VEHICLE_STATE"
        state, state_error = ConflictZoneOccupancyAssessor.occupancy_state(
            progress, (start, end), length
        )
        if state_error:
            return None, None, state_error
        distance_entry = max(0.0, start - progress)
        distance_clear = max(0.0, end + length - progress)
        timing = {
            "path_progress_m": progress,
            "distance_to_zone_entry_m": distance_entry,
            "distance_to_zone_clear_m": distance_clear,
            "vehicle_length_m": length,
            "speed_mps": speed,
            "zone_occupancy_state": state,
        }
        if state == "CLEARED_ZONE":
            timing.update({
                "time_to_entry_s": 0.0, "time_to_clear_s": 0.0,
                "predicted_entry_time_s": float(current_time),
                "predicted_clear_time_s": float(current_time),
            })
            return timing, state, None
        if not math.isfinite(speed) or speed <= 0.0:
            if state == "CURRENTLY_OCCUPYING":
                timing.update({
                    "time_to_entry_s": 0.0,
                    "predicted_entry_time_s": float(current_time),
                })
            return timing, state, "UNRESOLVED_SPEED"
        time_entry = distance_entry / speed
        time_clear = distance_clear / speed
        timing.update({
            "time_to_entry_s": time_entry,
            "time_to_clear_s": time_clear,
            "predicted_entry_time_s": float(current_time) + time_entry,
            "predicted_clear_time_s": float(current_time) + time_clear,
        })
        return timing, state, None

    @staticmethod
    def earliest_reachable_time(distance, initial_speed, max_acceleration,
                                max_speed):
        """Earliest time under maximum acceleration and a maximum-speed cap."""
        distance = float(distance)
        initial_speed = float(initial_speed)
        max_acceleration = float(max_acceleration)
        max_speed = float(max_speed)
        if not all(math.isfinite(value) for value in (
                distance, initial_speed, max_acceleration, max_speed)):
            raise ValueError("reachability inputs must be finite")
        if distance < 0.0 or initial_speed < 0.0:
            raise ValueError("distance and initial speed must be non-negative")
        if distance == 0.0:
            return 0.0
        if max_acceleration <= 0.0 or max_speed <= 0.0:
            raise ValueError("acceleration and maximum speed must be positive")
        if initial_speed >= max_speed:
            return distance / initial_speed
        acceleration_distance = (
            (max_speed ** 2 - initial_speed ** 2)
            / (2.0 * max_acceleration)
        )
        if distance <= acceleration_distance:
            return (
                -initial_speed + math.sqrt(
                    initial_speed ** 2
                    + 2.0 * max_acceleration * distance
                )
            ) / max_acceleration
        acceleration_time = (
            (max_speed - initial_speed) / max_acceleration
        )
        return (
            acceleration_time
            + (distance - acceleration_distance) / max_speed
        )

    @staticmethod
    def stopping_distance(speed, comfortable_deceleration):
        speed = float(speed)
        deceleration = float(comfortable_deceleration)
        if not math.isfinite(speed) or speed < 0.0:
            raise ValueError("speed must be finite and non-negative")
        if not math.isfinite(deceleration) or deceleration <= 0.0:
            raise ValueError("comfortable deceleration must be positive")
        return speed ** 2 / (2.0 * deceleration)

    def _add_reachability_fields(self, record, prefix, track, timing,
                                 current_time):
        dynamics = {
            "max_acceleration_mps2": track.get("max_acceleration_mps2"),
            "comfortable_deceleration_mps2": track.get(
                "comfortable_deceleration_mps2"
            ),
            "emergency_deceleration_mps2": track.get(
                "emergency_deceleration_mps2"
            ),
            "max_speed_mps": track.get("max_speed_mps"),
        }
        for name, value in dynamics.items():
            record[f"{prefix}_{name}"] = value
        if timing is None:
            record[f"{prefix}_reachability_status"] = "UNRESOLVED_DYNAMICS"
            return "UNRESOLVED_DYNAMICS"
        try:
            speed = float(track.get("speed"))
            acceleration = float(dynamics["max_acceleration_mps2"])
            deceleration = float(dynamics["comfortable_deceleration_mps2"])
            max_speed = float(dynamics["max_speed_mps"])
            earliest_entry = self.earliest_reachable_time(
                timing["distance_to_zone_entry_m"], speed,
                acceleration, max_speed,
            )
            earliest_clear = self.earliest_reachable_time(
                timing["distance_to_zone_clear_m"], speed,
                acceleration, max_speed,
            )
            stop_distance = self.stopping_distance(speed, deceleration)
        except (TypeError, ValueError):
            record[f"{prefix}_reachability_status"] = "UNRESOLVED_DYNAMICS"
            return "UNRESOLVED_DYNAMICS"
        can_stop = stop_distance <= timing["distance_to_zone_entry_m"]
        state = timing["zone_occupancy_state"]
        upper_status = (
            "CLEARED_ZONE" if state == "CLEARED_ZONE"
            else "CURRENTLY_OCCUPYING" if state == "CURRENTLY_OCCUPYING"
            else "UNBOUNDED_CAN_STOP" if can_stop
            else "CAN_NOT_STOP_BEFORE_ZONE"
        )
        record.update({
            f"{prefix}_earliest_reachable_entry_time_s": earliest_entry,
            f"{prefix}_earliest_reachable_clear_time_s": earliest_clear,
            f"{prefix}_earliest_predicted_entry_time_s": (
                float(current_time) + earliest_entry
            ),
            f"{prefix}_earliest_predicted_clear_time_s": (
                float(current_time) + earliest_clear
            ),
            f"{prefix}_stopping_distance_m": stop_distance,
            f"{prefix}_can_stop_before_zone": can_stop,
            f"{prefix}_entry_time_upper_bound_status": upper_status,
            f"{prefix}_reachability_status": "RESOLVED",
        })
        return "RESOLVED"

    # Compatibility helper retained for focused tests of the original
    # pre-junction formulation. General assessment uses path progress above.
    @staticmethod
    def _incoming_distance(track, expected_lane_id):
        if track.get("lane_id") != expected_lane_id:
            return None, "UNRESOLVED_PATH_PROGRESS"
        try:
            position, length = float(track["lane_position"]), float(track["lane_length"])
        except (KeyError, TypeError, ValueError):
            return None, "UNRESOLVED_PATH_PROGRESS"
        if not math.isfinite(position) or not math.isfinite(length):
            return None, "UNRESOLVED_PATH_PROGRESS"
        return max(0.0, length - position), None

    @staticmethod
    def _kinematics(incoming_distance, path_interval, length, speed, current_time):
        timing, _, error = ConflictZoneOccupancyAssessor._timing_from_progress(
            -float(incoming_distance), path_interval, length, speed, current_time
        )
        return timing, error

    @staticmethod
    def _candidate_path_ids(edge):
        candidates = edge.get("spatially_conflicting_candidate_paths")
        if candidates is None:
            candidates = edge.get("target_candidate_paths", {})
        for manoeuvre, value in candidates.items():
            for path_id in value if isinstance(value, (tuple, list)) else (value,):
                yield manoeuvre, path_id

    @staticmethod
    def _add_timing_fields(record, prefix, timing, source):
        timing = timing or {}
        record[f"{prefix}_path_progress_source"] = source
        for field in (
            "path_progress_m", "zone_occupancy_state", "vehicle_length_m",
            "distance_to_zone_entry_m", "distance_to_zone_clear_m", "speed_mps",
            "time_to_entry_s", "time_to_clear_s", "predicted_entry_time_s",
            "predicted_clear_time_s",
        ):
            record[f"{prefix}_{field}"] = timing.get(field)
        record[f"{prefix}_nominal_constant_speed_time_to_entry_s"] = timing.get(
            "time_to_entry_s"
        )
        record[f"{prefix}_nominal_constant_speed_time_to_clear_s"] = timing.get(
            "time_to_clear_s"
        )
        record[f"{prefix}_nominal_constant_speed_entry_time_s"] = timing.get(
            "predicted_entry_time_s"
        )
        record[f"{prefix}_nominal_constant_speed_clear_time_s"] = timing.get(
            "predicted_clear_time_s"
        )

    def _base_record(self, ldm, edge, target_id, manoeuvre, target_path_id,
                     current_time):
        return {
            "ego_id": ldm.ego_id, "target_id": target_id,
            "timestamp": float(current_time),
            "ego_path_id": edge["ego_path_id"],
            "target_path_id": target_path_id,
            "target_manoeuvre": manoeuvre,
            "target_prediction_status": edge.get("prediction_status"),
            "target_observation_age_seconds": edge.get("observation_age_seconds"),
            "ego_current_lane_id": ldm.tracks[ldm.ego_id].get("lane_id"),
            "target_current_lane_id": ldm.tracks[target_id].get("lane_id"),
        }

    def _evaluate_path(self, ldm, edge, target_id, manoeuvre, target_path_id,
                       current_time):
        ego, target = ldm.tracks[ldm.ego_id], ldm.tracks[target_id]
        ego_path_id = edge["ego_path_id"]
        record = self._base_record(
            ldm, edge, target_id, manoeuvre, target_path_id, current_time
        )
        ego_progress, ego_source, ego_error = (
            self.path_manager.resolve_front_bumper_path_progress(
                ego, self.path_manager.paths[ego_path_id]
            )
        )
        target_progress, target_source, target_error = (
            self.path_manager.resolve_front_bumper_path_progress(
                target, self.path_manager.paths[target_path_id]
            )
        )
        record.update({
            "ego_path_progress_m": ego_progress,
            "target_path_progress_m": target_progress,
            "ego_path_progress_source": ego_source,
            "target_path_progress_source": target_source,
        })
        if ego_error or target_error:
            record.update({
                "temporal_overlap": None, "overlap_duration_s": None,
                "temporal_separation_s": None,
                "status": ego_error or target_error,
            })
            return record
        zone = self.zone_manager.zone_record(
            ego_path_id, ego.get("width"), target_path_id, target.get("width")
        )
        if zone is None:
            record["status"] = "NO_APPLICABLE_ZONE"
            return record
        record.update({
            "conflict_zone_id": zone["zone_id"],
            "conflict_type": zone["conflict_type"],
            "ego_zone_path_interval_m": zone["first_path_distance_interval"],
            "target_zone_path_interval_m": zone["second_path_distance_interval"],
        })
        ego_timing, ego_state, ego_timing_error = self._timing_from_progress(
            ego_progress, zone["first_path_distance_interval"],
            ego.get("length"), ego.get("speed"), current_time,
        )
        target_timing, target_state, target_timing_error = self._timing_from_progress(
            target_progress, zone["second_path_distance_interval"],
            target.get("length"), target.get("speed"), current_time,
        )
        self._add_timing_fields(record, "ego", ego_timing, ego_source)
        self._add_timing_fields(record, "target", target_timing, target_source)
        ego_reachability = self._add_reachability_fields(
            record, "ego", ego, ego_timing, current_time
        )
        target_reachability = self._add_reachability_fields(
            record, "target", target, target_timing, current_time
        )
        if "CURRENTLY_OCCUPYING" in {ego_state, target_state}:
            reachability_interpretation = "CURRENTLY_OCCUPYING"
        elif "UNRESOLVED_DYNAMICS" in {
                ego_reachability, target_reachability}:
            reachability_interpretation = "UNRESOLVED_PHYSICAL_DYNAMICS"
        elif (record.get("ego_can_stop_before_zone")
              or record.get("target_can_stop_before_zone")):
            reachability_interpretation = "UNCOMMITTED_CAN_STOP"
        else:
            reachability_interpretation = "POTENTIAL_CONFLICT_REACHABLE"
        record["reachability_interpretation"] = reachability_interpretation

        if "CLEARED_ZONE" in {ego_state, target_state}:
            record.update({
                "temporal_overlap": False, "overlap_duration_s": 0.0,
                "temporal_separation_s": None, "status": "CLEARED_ZONE",
            })
            return record
        if ego_state == target_state == "CURRENTLY_OCCUPYING":
            clear_times = [
                item.get("predicted_clear_time_s") for item in
                (ego_timing or {}, target_timing or {})
            ]
            duration = (
                min(clear_times) - float(current_time)
                if all(value is not None for value in clear_times) else None
            )
            record.update({
                "temporal_overlap": True, "overlap_duration_s": duration,
                "temporal_separation_s": 0.0, "status": "TEMPORAL_CONFLICT",
            })
            return record
        if ego_timing_error or target_timing_error:
            record.update({
                "temporal_overlap": None, "overlap_duration_s": None,
                "temporal_separation_s": None,
                "status": ego_timing_error or target_timing_error,
            })
            return record
        overlap, duration, separation = self.interval_relationship(
            ego_timing["predicted_entry_time_s"],
            ego_timing["predicted_clear_time_s"],
            target_timing["predicted_entry_time_s"],
            target_timing["predicted_clear_time_s"],
        )
        record.update({
            "temporal_overlap": overlap, "overlap_duration_s": duration,
            "temporal_separation_s": separation,
            "status": "TEMPORAL_CONFLICT" if overlap else "SPATIAL_ONLY",
        })
        return record

    def _count_record(self, record):
        status = record["status"]
        if status == "INCOMPATIBLE_WITH_OBSERVED_LANE":
            self._totals["incompatible_with_observed_lane"] += 1
            self._totals["candidate_paths_rejected_by_observed_lane"] += 1
            return
        if status == "NO_APPLICABLE_ZONE":
            self._totals["no_applicable_zone"] += 1
            return
        self._totals["candidate_path_zone_evaluations"] += 1
        states = {
            record.get("ego_zone_occupancy_state"),
            record.get("target_zone_occupancy_state"),
        }
        if "CURRENTLY_OCCUPYING" in states:
            self._totals["currently_occupied_zone_evaluations"] += 1
        if "CLEARED_ZONE" in states:
            self._totals["cleared_zone_evaluations"] += 1
        for prefix in ("ego", "target"):
            if record.get(f"{prefix}_reachability_status") == "RESOLVED":
                self._totals["earliest_reachability_calculations"] += 1
                if (record.get(f"{prefix}_speed_mps") == 0.0
                        and record.get(
                            f"{prefix}_earliest_reachable_entry_time_s"
                        ) is not None):
                    self._totals[
                        "stopped_vehicles_with_finite_earliest_arrival"
                    ] += 1
                if record.get(f"{prefix}_can_stop_before_zone"):
                    self._totals["vehicles_able_to_stop_before_zone"] += 1
                else:
                    self._totals["vehicles_unable_to_stop_before_zone"] += 1
        if record.get("reachability_interpretation") == (
                "UNRESOLVED_PHYSICAL_DYNAMICS"):
            self._totals["physical_state_or_dynamics_unresolved"] += 1
        if status == "TEMPORAL_CONFLICT":
            self._totals["temporal_conflicts_observed"] += 1
        elif status in {"SPATIAL_ONLY", "CLEARED_ZONE"}:
            self._totals["spatial_only_temporal_separations"] += 1
        elif status.startswith("UNRESOLVED_"):
            self._totals["unresolved_timing_evaluations"] += 1
            key = {
                "UNRESOLVED_PATH_PROGRESS": "unresolved_path_progress",
                "UNRESOLVED_SPEED": "unresolved_speed",
                "UNRESOLVED_VEHICLE_STATE": "unresolved_vehicle_state",
            }.get(status)
            if key:
                self._totals[key] += 1
            if (status == "UNRESOLVED_SPEED"
                    and (record.get("ego_speed_mps") == 0.0
                         or record.get("target_speed_mps") == 0.0)):
                self._totals[
                    "nominal_timing_unavailable_due_to_zero_speed"
                ] += 1

    def assess_ldm(self, ldm, current_time):
        graph = ldm.current_conflict_graph or {}
        edge_results = []
        for edge in graph.get("edges", ()):
            self._totals["spatial_edges_evaluated"] += 1
            self._totals["non_conflicting_candidate_paths_excluded"] += int(
                edge.get("non_conflicting_candidate_path_count", 0)
            )
            target_id = edge["target_track_id"]
            records = []
            if target_id in ldm.tracks:
                for manoeuvre, path_id in self._candidate_path_ids(edge):
                    record = self._evaluate_path(
                        ldm, edge, target_id, manoeuvre, path_id, current_time
                    )
                    records.append(record)
                    self._count_record(record)
            applicable = [
                record for record in records
                if record["status"] not in self.NON_APPLICABLE
            ]
            statuses = {record["status"] for record in applicable}
            if "TEMPORAL_CONFLICT" in statuses:
                possible, status = True, "TEMPORAL_CONFLICT"
                self._conflicting_pairs.add((ldm.ego_id, target_id))
            elif any(value.startswith("UNRESOLVED_") for value in statuses):
                possible, status = None, "UNRESOLVED_TIMING"
            elif applicable:
                possible, status = False, "SPATIAL_ONLY"
            else:
                possible, status = None, "UNRESOLVED_NO_APPLICABLE_EVALUATION"
                self._totals["unresolved_no_applicable_evaluation"] += 1
            edge_results.append({
                "ego_id": ldm.ego_id, "target_id": target_id,
                "timestamp": float(current_time),
                "temporal_conflict_possible": possible,
                "status": status, "evaluations": tuple(records),
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
