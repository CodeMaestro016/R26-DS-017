"""Deterministic, ASAM OSI-inspired object-level perception for SUMO.

The interface converts global simulator ground truth into an ego-specific
sensor view and then into current-frame local object detections. Positive ego
longitudinal is forward and positive lateral is left. SUMO navigation headings
are 0=north and 90 degrees=east.

SUMO ``position`` and ``lane_position`` use the center of the front bumper as
their vehicle reference. Geometric footprints derive the vehicle center from
that position and actual length. The virtual ego sensor origin remains the
project's SUMO reference point; no physical radar mounting offset is modelled.

``IDEAL_BASELINE`` applies only the 160 m reference limit (no FOV or
occlusion) to exact simulator values and is an unrealistic upper-performance
baseline. ``GEOMETRIC_SENSOR`` applies the fused 360-degree FOV and dynamic
vehicle-to-vehicle occlusion, retaining exact simulator values for visible
targets; it remains an object-level geometric abstraction. The provisional
``REALISTIC_OBJECT_SENSOR`` currently delegates to that same geometry: noise,
missed detections, and latency are not yet implemented.
Positive finite dimensions are mandatory for both geometric profiles.

Route and manoeuvre truth are deliberately excluded because they would leak
future information downstream. Static occluders may later be supplied to the
geometric layer; none are invented here.

``sensor_range`` is the selected reference sensor capability and
``sensor_fov_degrees`` is fused object-list coverage, not one radar's FOV. The
interface does not simulate separate radar returns; each reference radar has a
150-degree horizontal FOV. ASAM OSI inspires the ground-truth-to-sensor-view
structure but does not prescribe these numeric values.
"""

import copy
import math

import numpy as np

from config import (
    DEFAULT_PERCEPTION_PROFILE,
    GEOMETRIC_SENSOR_PROFILE,
    PERCEPTION_PROFILES,
    REALISTIC_OBJECT_SENSOR_PROFILE,
    SENSOR_CONFIGURATION_SUMMARY,
    SENSOR_FOV_DEGREES,
    SENSOR_RANGE,
)


class PerceptionInterface:
    """Produce an independent deterministic perception frame for one ego AV."""

    VALID_PROFILES = PERCEPTION_PROFILES
    GEOMETRIC_PROFILES = frozenset({
        GEOMETRIC_SENSOR_PROFILE,
        REALISTIC_OBJECT_SENSOR_PROFILE,
    })
    _EPSILON = 1e-12

    def __init__(self, profile=DEFAULT_PERCEPTION_PROFILE,
                 sensor_range=SENSOR_RANGE,
                 sensor_fov_degrees=SENSOR_FOV_DEGREES):
        if profile not in self.VALID_PROFILES:
            raise ValueError(f"Unsupported perception profile: {profile!r}")
        self.profile = profile
        self.sensor_range = self._finite_number(sensor_range, "sensor_range")
        self.sensor_fov_degrees = self._finite_number(
            sensor_fov_degrees, "sensor_fov_degrees"
        )
        if self.sensor_range < 0.0:
            raise ValueError("sensor_range must be non-negative")
        if not 0.0 < self.sensor_fov_degrees <= 360.0:
            raise ValueError("sensor_fov_degrees must be in (0, 360]")
        self.last_diagnostics_by_ego = {}
        self.last_summary_by_ego = {}
        # Deprecated compatibility alias for the most recently requested ego.
        self.last_diagnostics = []

    def generate_observations(self, ego_vehicle_id, ego_data,
                              all_vehicle_data, current_time):
        """Return ego localization plus current geometrically detected objects.

        ``all_vehicle_data[ego_vehicle_id]`` is the authoritative ego state.
        The separate ``ego_data`` parameter is retained temporarily for API
        compatibility and is validation-only; contradictory values raise
        ``ValueError``. Callers should plan to remove this redundant argument
        in a future breaking API revision.
        """
        timestamp = self._finite_number(current_time, "current_time")
        if timestamp < 0.0:
            raise ValueError("current_time must be non-negative")
        if ego_vehicle_id not in all_vehicle_data:
            raise ValueError(
                f"ego vehicle {ego_vehicle_id!r} is absent from all_vehicle_data"
            )

        applies_geometry = self._uses_geometric_visibility()
        require_dimensions = applies_geometry
        ego = self._validate_vehicle_state(
            ego_vehicle_id, ego_data, require_dimensions=require_dimensions
        )
        frame_ego = self._validate_vehicle_state(
            ego_vehicle_id,
            all_vehicle_data[ego_vehicle_id],
            require_dimensions=require_dimensions,
        )
        self._validate_consistent_ego_state(ego_vehicle_id, ego, frame_ego)
        ego = frame_ego
        observations = {
            ego_vehicle_id: self._make_ego_localization(
                ego_vehicle_id, ego, timestamp, self.profile
            )
        }
        diagnostics = []
        candidates = []

        for object_id, raw_state in all_vehicle_data.items():
            if object_id == ego_vehicle_id:
                continue
            diagnostic = self._diagnostic_template(
                timestamp, ego_vehicle_id, object_id
            )
            try:
                target = self._validate_vehicle_state(
                    object_id, raw_state, require_dimensions=require_dimensions
                )
            except (TypeError, ValueError) as error:
                diagnostic.update(
                    result="REJECTED", reason="INVALID_TARGET_STATE",
                    detail=str(error)
                )
                diagnostics.append(diagnostic)
                continue

            relative_position = self._world_to_ego(
                target["position"] - ego["position"], ego["heading_radians"]
            )
            range_m = float(np.hypot(*relative_position))
            bearing = math.atan2(relative_position[1], relative_position[0])
            diagnostic.update(range_m=range_m, bearing_radians=bearing)
            if range_m > self.sensor_range:
                diagnostic.update(result="REJECTED", reason="OUT_OF_RANGE")
                diagnostics.append(diagnostic)
                continue

            relative_velocity = self._world_to_ego(
                self._velocity_vector(target["speed"], target["heading_radians"])
                - self._velocity_vector(ego["speed"], ego["heading_radians"]),
                ego["heading_radians"],
            )
            intervals = None
            clipped_intervals = None
            fov_fraction = 1.0
            if require_dimensions:
                intervals = self._calculate_angular_interval(
                    self._calculate_bounding_box(target), ego
                )
                clipped_intervals = self._intersect_intervals(
                    intervals, self._fov_intervals()
                )
                fov_fraction = self._interval_fraction(
                    clipped_intervals, intervals
                )
                if fov_fraction <= self._EPSILON:
                    diagnostic.update(
                        result="REJECTED", reason="OUT_OF_FOV",
                        visible_fraction=0.0, fov_visible_fraction=0.0,
                        occlusion_visible_fraction=None,
                    )
                    diagnostics.append(diagnostic)
                    continue

            candidates.append({
                "object_id": object_id,
                "state": target,
                "relative_position": relative_position,
                "relative_velocity": relative_velocity,
                "range": range_m,
                "bearing": bearing,
                "intervals": intervals,
                "visible_intervals": clipped_intervals,
                "fov_visible_fraction": fov_fraction,
                "diagnostic": diagnostic,
                "profile": self.profile,
            })

        candidates.sort(key=lambda item: (item["range"], str(item["object_id"])))
        covered = []
        index = 0
        while index < len(candidates):
            group_end = index + 1
            while (group_end < len(candidates)
                   and abs(candidates[group_end]["range"]
                           - candidates[index]["range"]) <= self._EPSILON):
                group_end += 1
            group = candidates[index:group_end]
            group_intervals = []
            for candidate in group:
                occlusion_fraction = 1.0
                combined_fraction = 1.0
                if applies_geometry:
                    occlusion_fraction = self._calculate_visible_fraction(
                        candidate["visible_intervals"], covered
                    )
                    combined_fraction = self._clamp_fraction(
                        candidate["fov_visible_fraction"] * occlusion_fraction
                    )
                    group_intervals.extend(candidate["visible_intervals"])

                diagnostic = candidate["diagnostic"]
                diagnostic.update(
                    fov_visible_fraction=candidate["fov_visible_fraction"],
                    occlusion_visible_fraction=occlusion_fraction,
                    visible_fraction=combined_fraction,
                )
                if combined_fraction <= self._EPSILON:
                    diagnostic.update(result="REJECTED", reason="FULLY_OCCLUDED")
                else:
                    reason = (
                        "PARTIALLY_VISIBLE"
                        if combined_fraction < 1.0 - self._EPSILON
                        else "DETECTED"
                    )
                    diagnostic.update(result="DETECTED", reason=reason)
                    observations[candidate["object_id"]] = (
                        self._make_object_detection(
                            candidate, timestamp,
                            candidate["fov_visible_fraction"],
                            occlusion_fraction, combined_fraction,
                        )
                    )
                diagnostics.append(diagnostic)
            if applies_geometry:
                covered = self._merge_intervals(covered + group_intervals)
            index = group_end

        self._store_frame_metadata(
            ego_vehicle_id, timestamp, len(all_vehicle_data) - 1, diagnostics
        )
        return observations

    def _uses_geometric_visibility(self):
        """Whether this profile uses the shared deterministic geometry layer."""
        return self.profile in self.GEOMETRIC_PROFILES

    def get_last_diagnostics(self, ego_vehicle_id=None):
        """Return copies of the latest detailed diagnostics per requested ego."""
        if ego_vehicle_id is None:
            return copy.deepcopy(self.last_diagnostics_by_ego)
        return copy.deepcopy(self.last_diagnostics_by_ego.get(ego_vehicle_id, []))

    def get_last_summary(self, ego_vehicle_id=None):
        """Return copies of the latest frame summaries per requested ego."""
        if ego_vehicle_id is None:
            return copy.deepcopy(self.last_summary_by_ego)
        return copy.deepcopy(self.last_summary_by_ego.get(ego_vehicle_id))

    def clear_ego_diagnostics(self, ego_vehicle_id):
        """Discard retained latest-frame metadata for one departed ego."""
        self.last_diagnostics_by_ego.pop(ego_vehicle_id, None)
        self.last_summary_by_ego.pop(ego_vehicle_id, None)

    def clear_diagnostics(self):
        """Discard all retained frame metadata on simulation reset."""
        self.last_diagnostics_by_ego.clear()
        self.last_summary_by_ego.clear()
        self.last_diagnostics = []

    def _store_frame_metadata(self, ego_id, timestamp, candidate_count,
                              diagnostics):
        frame = copy.deepcopy(diagnostics)
        self.last_diagnostics_by_ego[ego_id] = frame
        self.last_diagnostics = copy.deepcopy(frame)
        counts = {reason: 0 for reason in (
            "INVALID_TARGET_STATE", "OUT_OF_RANGE", "OUT_OF_FOV",
            "FULLY_OCCLUDED", "PARTIALLY_VISIBLE"
        )}
        for item in diagnostics:
            if item["reason"] in counts:
                counts[item["reason"]] += 1
        self.last_summary_by_ego[ego_id] = {
            "time_seconds": timestamp,
            "ego_id": ego_id,
            "profile": self.profile,
            "candidate_targets": candidate_count,
            "detected_targets": sum(
                item["result"] == "DETECTED" for item in diagnostics
            ),
            "invalid_targets": counts["INVALID_TARGET_STATE"],
            "out_of_range_targets": counts["OUT_OF_RANGE"],
            "out_of_fov_targets": counts["OUT_OF_FOV"],
            "fully_occluded_targets": counts["FULLY_OCCLUDED"],
            "partially_visible_targets": counts["PARTIALLY_VISIBLE"],
            "sensor_configuration": copy.deepcopy(SENSOR_CONFIGURATION_SUMMARY),
        }

    def _diagnostic_template(self, timestamp, ego_id, target_id):
        return {
            "time_seconds": timestamp, "ego_id": ego_id,
            "target_id": target_id, "profile": self.profile,
            "result": None, "reason": None, "range_m": None,
            "bearing_radians": None, "fov_visible_fraction": None,
            "occlusion_visible_fraction": None, "visible_fraction": None,
        }

    @staticmethod
    def _finite_number(value, name):
        try:
            number = float(value)
        except (TypeError, ValueError) as error:
            raise ValueError(f"{name} must be a finite number") from error
        if not math.isfinite(number):
            raise ValueError(f"{name} must be a finite number")
        return number

    @classmethod
    def _validate_vehicle_state(cls, vehicle_id, state,
                                require_dimensions=True):
        if not isinstance(state, dict):
            raise TypeError(f"vehicle {vehicle_id!r} state must be a dictionary")
        for field in ("position", "speed", "heading_radians"):
            if field not in state:
                raise ValueError(
                    f"vehicle {vehicle_id!r} missing mandatory field {field!r}"
                )
        position = np.asarray(state["position"], dtype=float)
        speed = cls._finite_number(state["speed"], "speed")
        heading = cls._finite_number(state["heading_radians"], "heading_radians")
        if position.shape != (2,) or not np.all(np.isfinite(position)):
            raise ValueError(
                f"vehicle {vehicle_id!r} position must contain two finite numbers"
            )
        if speed < 0.0:
            raise ValueError(f"vehicle {vehicle_id!r} speed must be non-negative")

        dimensions = {}
        for field in ("length", "width"):
            if field not in state:
                if require_dimensions:
                    raise ValueError(
                        f"vehicle {vehicle_id!r} missing mandatory field {field!r}"
                    )
                dimensions[field] = None
                continue
            value = cls._finite_number(state[field], field)
            if value <= 0.0:
                raise ValueError(
                    f"vehicle {vehicle_id!r} {field} must be positive"
                )
            dimensions[field] = value

        validated = dict(state)
        validated.update(position=position.copy(), speed=speed,
                         heading_radians=heading, **dimensions)
        return validated

    @classmethod
    def _validate_consistent_ego_state(cls, vehicle_id, ego, frame_ego):
        """Reject contradictory duplicate ego inputs before geometry is used."""
        inconsistent = []
        if not np.array_equal(ego["position"], frame_ego["position"]):
            inconsistent.append("position")
        for field in ("speed", "heading_radians", "length", "width"):
            if ego.get(field) != frame_ego.get(field):
                inconsistent.append(field)
        if inconsistent:
            raise ValueError(
                f"ego vehicle {vehicle_id!r} state is inconsistent between "
                f"ego_data and all_vehicle_data for fields: "
                f"{', '.join(inconsistent)}"
            )

    @staticmethod
    def _velocity_vector(speed, heading_radians):
        return np.asarray([
            speed * math.sin(heading_radians),
            speed * math.cos(heading_radians),
        ], dtype=float)

    @staticmethod
    def _world_to_ego(vector, ego_heading_radians):
        forward = np.asarray([
            math.sin(ego_heading_radians), math.cos(ego_heading_radians)
        ])
        left = np.asarray([
            -math.cos(ego_heading_radians), math.sin(ego_heading_radians)
        ])
        return np.asarray([
            np.dot(vector, forward), np.dot(vector, left)
        ], dtype=float)

    @staticmethod
    def _calculate_bounding_box(state):
        """Return footprint corners from SUMO's front-bumper reference.

        If p_f is the front-bumper position, L the actual vehicle length, and
        u the heading unit vector, the geometric center is
        p_c = p_f - (L / 2) u. The footprint is then constructed around p_c.
        """
        heading = state["heading_radians"]
        forward = np.asarray([math.sin(heading), math.cos(heading)])
        left = np.asarray([-math.cos(heading), math.sin(heading)])
        longitudinal = 0.5 * state["length"] * forward
        lateral = 0.5 * state["width"] * left
        front_bumper_position = np.asarray(state["position"], dtype=float)
        geometric_center = front_bumper_position - longitudinal
        return np.asarray([
            geometric_center + longitudinal + lateral,
            geometric_center + longitudinal - lateral,
            geometric_center - longitudinal - lateral,
            geometric_center - longitudinal + lateral,
        ])

    @classmethod
    def _calculate_angular_interval(cls, world_corners, ego):
        local = np.asarray([
            cls._world_to_ego(
                corner - ego["position"], ego["heading_radians"]
            ) for corner in world_corners
        ])
        # If the sensor origin lies inside this convex box, it occupies every
        # bearing. Use the polygon edges rather than its axis-aligned bounds.
        cross_products = []
        for index, corner in enumerate(local):
            next_corner = local[(index + 1) % len(local)]
            edge = next_corner - corner
            to_origin = -corner
            cross_products.append(
                edge[0] * to_origin[1] - edge[1] * to_origin[0]
            )
        if (all(value >= -cls._EPSILON for value in cross_products)
                or all(value <= cls._EPSILON for value in cross_products)):
            return [(-math.pi, math.pi)]
        angles = np.mod(np.arctan2(local[:, 1], local[:, 0]), 2.0 * math.pi)
        angles.sort()
        circular = np.concatenate((angles, [angles[0] + 2.0 * math.pi]))
        gap_index = int(np.argmax(np.diff(circular)))
        start = circular[gap_index + 1]
        end = circular[gap_index] + 2.0 * math.pi
        start = ((start + math.pi) % (2.0 * math.pi)) - math.pi
        span = float(end - circular[gap_index + 1])
        finish = start + span
        if finish <= math.pi + cls._EPSILON:
            return [(float(start), min(float(finish), math.pi))]
        return [(float(start), math.pi),
                (-math.pi, float(finish - 2.0 * math.pi))]

    def _fov_intervals(self):
        if self.sensor_fov_degrees >= 360.0 - self._EPSILON:
            return [(-math.pi, math.pi)]
        half = math.radians(self.sensor_fov_degrees) / 2.0
        return [(-half, half)]

    def _is_inside_fov(self, bearing):
        """Compatibility helper for testing a point bearing, not a vehicle box."""
        return bool(self._intersect_intervals(
            [(math.atan2(math.sin(bearing), math.cos(bearing)),) * 2],
            self._fov_intervals(), include_points=True,
        ))

    @classmethod
    def _intersect_intervals(cls, first, second, include_points=False):
        intersections = []
        for first_start, first_end in first:
            for second_start, second_end in second:
                start = max(first_start, second_start)
                end = min(first_end, second_end)
                if end > start + cls._EPSILON or (
                    include_points and end >= start - cls._EPSILON
                ):
                    intersections.append((start, end))
        return cls._merge_intervals(intersections)

    @classmethod
    def _merge_intervals(cls, intervals):
        merged = []
        for start, end in sorted(intervals):
            if end < start:
                continue
            if not merged or start > merged[-1][1] + cls._EPSILON:
                merged.append([start, end])
            else:
                merged[-1][1] = max(merged[-1][1], end)
        return [(float(start), float(end)) for start, end in merged]

    @classmethod
    def _interval_length(cls, intervals):
        return sum(max(0.0, end - start) for start, end in
                   cls._merge_intervals(intervals))

    @classmethod
    def _interval_fraction(cls, visible, total):
        denominator = cls._interval_length(total)
        if denominator <= cls._EPSILON:
            return 1.0
        return cls._clamp_fraction(cls._interval_length(visible) / denominator)

    @classmethod
    def _calculate_visible_fraction(cls, intervals, covered):
        merged_intervals = cls._merge_intervals(intervals)
        merged_covered = cls._merge_intervals(covered)
        total = cls._interval_length(merged_intervals)
        if total <= cls._EPSILON:
            return 1.0
        hidden = cls._interval_length(
            cls._intersect_intervals(merged_intervals, merged_covered)
        )
        return cls._clamp_fraction((total - hidden) / total)

    @staticmethod
    def _clamp_fraction(value):
        return min(1.0, max(0.0, float(value)))

    @staticmethod
    def _context_fields(state):
        return {key: state[key] for key in (
            "lane_id", "lane_position", "lane_length", "road_id"
        ) if key in state}

    @classmethod
    def _make_ego_localization(cls, object_id, state, timestamp, profile):
        velocity = cls._velocity_vector(state["speed"], state["heading_radians"])
        result = {
            "object_id": object_id,
            "observation_type": "EGO_LOCALIZATION",
            "position": tuple(state["position"]),
            "measured_position_world": tuple(state["position"]),
            "speed": state["speed"],
            "heading_radians": state["heading_radians"],
            "velocity_world": tuple(velocity),
            "relative_position_ego": (0.0, 0.0),
            "relative_velocity_ego": (0.0, 0.0),
            "range": 0.0, "distance": 0.0, "bearing_radians": 0.0,
            "measurement_timestamp": timestamp,
            "available_timestamp": timestamp, "timestamp": timestamp,
            "detection_status": "SELF_LOCALIZATION",
            "perception_profile": profile,
            "localization_profile": "PERFECT_SUMO_LOCALIZATION",
        }
        for field in ("length", "width"):
            if state.get(field) is not None:
                result[field] = state[field]
        result.update(cls._context_fields(state))
        return result

    @classmethod
    def _make_object_detection(cls, candidate, timestamp, fov_fraction,
                               occlusion_fraction, visible_fraction):
        state = candidate["state"]
        velocity = cls._velocity_vector(state["speed"], state["heading_radians"])
        result = {
            "object_id": candidate["object_id"],
            "observation_type": "OBJECT_DETECTION",
            "position": tuple(state["position"]),
            "measured_position_world": tuple(state["position"]),
            "speed": state["speed"],
            "heading_radians": state["heading_radians"],
            "velocity_world": tuple(velocity),
            "relative_position_ego": tuple(candidate["relative_position"]),
            "relative_velocity_ego": tuple(candidate["relative_velocity"]),
            "range": candidate["range"], "distance": candidate["range"],
            "bearing_radians": candidate["bearing"],
            "fov_visible_fraction": cls._clamp_fraction(fov_fraction),
            "occlusion_visible_fraction": cls._clamp_fraction(
                occlusion_fraction
            ),
            "visible_fraction": cls._clamp_fraction(visible_fraction),
            "measurement_timestamp": timestamp,
            "available_timestamp": timestamp, "timestamp": timestamp,
            "detection_status": "DETECTED",
            "perception_profile": candidate["profile"],
        }
        for field in ("length", "width"):
            if state.get(field) is not None:
                result[field] = state[field]
        result.update(cls._context_fields(state))
        return result
