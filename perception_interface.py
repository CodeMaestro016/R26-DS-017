"""Deterministic, ASAM OSI-inspired object-level perception for SUMO.

The interface converts global simulator ground truth into an ego-specific
SensorView and then local object detections. It is not a tracker or a physical
sensor simulator: it adds no noise, latency, confidence, history, prediction,
or data association. Positive ego longitudinal is forward; positive lateral
is left. SUMO navigation headings are 0=north and 90 degrees=east.

IDEAL_BASELINE applies range only and is an unrealistic regression baseline.
GEOMETRIC_SENSOR additionally applies field of view and vehicle occlusion.
The source is still perfect SUMO truth. Route and manoeuvre truth are excluded
because future-route knowledge would leak privileged information downstream.
Static-occluder support can later be added alongside the vehicle boxes without
changing the output contract.
"""

import math

import numpy as np

from config import (
    DEFAULT_PERCEPTION_PROFILE,
    SENSOR_FOV_DEGREES,
    SENSOR_RANGE,
)


class PerceptionInterface:
    """Produce independent, current-frame local detections for one ego AV."""

    VALID_PROFILES = frozenset({"IDEAL_BASELINE", "GEOMETRIC_SENSOR"})
    _EPSILON = 1e-12

    def __init__(
        self,
        profile=DEFAULT_PERCEPTION_PROFILE,
        sensor_range=SENSOR_RANGE,
        sensor_fov_degrees=SENSOR_FOV_DEGREES,
    ):
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
        self.last_diagnostics = []

    def generate_observations(
        self, ego_vehicle_id, ego_data, all_vehicle_data, current_time
    ):
        """Return ego localization plus geometrically detected objects.

        Invalid ego/frame inputs raise ``ValueError``. Invalid targets are
        skipped and recorded in ``last_diagnostics`` as structured entries.
        Inputs are read only and are never mutated.
        """
        timestamp = self._finite_number(current_time, "current_time")
        if timestamp < 0.0:
            raise ValueError("current_time must be non-negative")
        if ego_vehicle_id not in all_vehicle_data:
            raise ValueError(f"ego vehicle {ego_vehicle_id!r} is absent from all_vehicle_data")
        ego = self._validate_vehicle_state(ego_vehicle_id, ego_data)
        self.last_diagnostics = []
        observations = {
            ego_vehicle_id: self._make_ego_localization(
                ego_vehicle_id, ego, timestamp
            )
        }

        candidates = []
        for object_id, raw_state in all_vehicle_data.items():
            if object_id == ego_vehicle_id:
                continue
            try:
                target = self._validate_vehicle_state(object_id, raw_state)
            except (KeyError, TypeError, ValueError) as error:
                self.last_diagnostics.append(
                    {"object_id": object_id, "reason": "INVALID_TARGET_STATE", "detail": str(error)}
                )
                continue
            relative_position = self._world_to_ego(
                target["position"] - ego["position"], ego["heading_radians"]
            )
            range_m = float(np.hypot(*relative_position))
            if range_m > self.sensor_range:
                continue
            bearing = math.atan2(relative_position[1], relative_position[0])
            if self.profile == "GEOMETRIC_SENSOR" and not self._is_inside_fov(bearing):
                continue
            relative_velocity = self._world_to_ego(
                self._velocity_vector(target["speed"], target["heading_radians"])
                - self._velocity_vector(ego["speed"], ego["heading_radians"]),
                ego["heading_radians"],
            )
            intervals = self._calculate_angular_interval(
                self._calculate_bounding_box(target), ego
            )
            candidates.append(
                {
                    "object_id": object_id,
                    "state": target,
                    "relative_position": relative_position,
                    "relative_velocity": relative_velocity,
                    "range": range_m,
                    "bearing": bearing,
                    "intervals": intervals,
                    "profile": self.profile,
                }
            )

        candidates.sort(key=lambda item: (item["range"], str(item["object_id"])))
        covered = []
        for candidate in candidates:
            visible_fraction = 1.0
            if self.profile == "GEOMETRIC_SENSOR":
                visible_fraction = self._calculate_visible_fraction(
                    candidate["intervals"], covered
                )
                covered = self._merge_intervals(covered + candidate["intervals"])
                if visible_fraction <= self._EPSILON:
                    continue
            observations[candidate["object_id"]] = self._make_object_detection(
                candidate, timestamp, visible_fraction
            )
        return observations

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
    def _validate_vehicle_state(cls, vehicle_id, state):
        if not isinstance(state, dict):
            raise TypeError(f"vehicle {vehicle_id!r} state must be a dictionary")
        try:
            position = np.asarray(state["position"], dtype=float)
            speed = cls._finite_number(state["speed"], "speed")
            heading = cls._finite_number(state["heading_radians"], "heading_radians")
            length = cls._finite_number(state["length"], "length")
            width = cls._finite_number(state["width"], "width")
        except KeyError as error:
            raise ValueError(f"vehicle {vehicle_id!r} missing mandatory field {error.args[0]!r}") from error
        if position.shape != (2,) or not np.all(np.isfinite(position)):
            raise ValueError(f"vehicle {vehicle_id!r} position must contain two finite numbers")
        if speed < 0.0:
            raise ValueError(f"vehicle {vehicle_id!r} speed must be non-negative")
        if length <= 0.0 or width <= 0.0:
            raise ValueError(f"vehicle {vehicle_id!r} length and width must be positive")
        validated = dict(state)
        validated.update(position=position.copy(), speed=speed,
                         heading_radians=heading, length=length, width=width)
        return validated

    @staticmethod
    def _velocity_vector(speed, heading_radians):
        return np.asarray(
            [speed * math.sin(heading_radians), speed * math.cos(heading_radians)],
            dtype=float,
        )

    @staticmethod
    def _world_to_ego(vector, ego_heading_radians):
        forward = np.asarray(
            [math.sin(ego_heading_radians), math.cos(ego_heading_radians)]
        )
        left = np.asarray(
            [-math.cos(ego_heading_radians), math.sin(ego_heading_radians)]
        )
        return np.asarray([np.dot(vector, forward), np.dot(vector, left)], dtype=float)

    @classmethod
    def _calculate_bounding_box(cls, state):
        heading = state["heading_radians"]
        forward = np.asarray([math.sin(heading), math.cos(heading)])
        left = np.asarray([-math.cos(heading), math.sin(heading)])
        longitudinal = 0.5 * state["length"] * forward
        lateral = 0.5 * state["width"] * left
        center = state["position"]
        return np.asarray(
            [center + longitudinal + lateral, center + longitudinal - lateral,
             center - longitudinal - lateral, center - longitudinal + lateral]
        )

    @classmethod
    def _calculate_angular_interval(cls, world_corners, ego):
        local = np.asarray(
            [cls._world_to_ego(corner - ego["position"], ego["heading_radians"])
             for corner in world_corners]
        )
        angles = np.sort(np.arctan2(local[:, 1], local[:, 0]))
        extended = np.concatenate((angles, [angles[0] + 2.0 * math.pi]))
        gap_index = int(np.argmax(np.diff(extended)))
        start = float(extended[gap_index + 1] if gap_index + 1 < len(angles) else angles[0])
        end = float(extended[gap_index] + (2.0 * math.pi if extended[gap_index] < start else 0.0))
        start = ((start + math.pi) % (2.0 * math.pi)) - math.pi
        span = (end - (extended[gap_index + 1] if gap_index + 1 < len(angles) else angles[0])) % (2.0 * math.pi)
        end_unwrapped = start + span
        if end_unwrapped <= math.pi:
            return [(start, end_unwrapped)]
        return [(start, math.pi), (-math.pi, end_unwrapped - 2.0 * math.pi)]

    def _is_inside_fov(self, bearing):
        if self.sensor_fov_degrees >= 360.0 - self._EPSILON:
            return True
        wrapped = math.atan2(math.sin(bearing), math.cos(bearing))
        return abs(wrapped) <= math.radians(self.sensor_fov_degrees) / 2.0 + self._EPSILON

    @classmethod
    def _merge_intervals(cls, intervals):
        merged = []
        for start, end in sorted(intervals):
            if not merged or start > merged[-1][1] + cls._EPSILON:
                merged.append([start, end])
            else:
                merged[-1][1] = max(merged[-1][1], end)
        return [(start, end) for start, end in merged]

    @classmethod
    def _calculate_visible_fraction(cls, intervals, covered):
        total = sum(max(0.0, end - start) for start, end in intervals)
        if total <= cls._EPSILON:
            return 1.0
        hidden = 0.0
        for start, end in intervals:
            for cover_start, cover_end in covered:
                hidden += max(0.0, min(end, cover_end) - max(start, cover_start))
        return min(1.0, max(0.0, (total - hidden) / total))

    @staticmethod
    def _context_fields(state):
        return {
            key: state[key]
            for key in ("lane_id", "lane_position", "lane_length", "road_id")
            if key in state
        }

    @classmethod
    def _make_ego_localization(cls, object_id, state, timestamp):
        velocity = cls._velocity_vector(state["speed"], state["heading_radians"])
        result = {
            "object_id": object_id, "observation_type": "EGO_LOCALIZATION",
            "position": tuple(state["position"]),
            "measured_position_world": tuple(state["position"]),
            "speed": state["speed"], "heading_radians": state["heading_radians"],
            "velocity_world": tuple(velocity), "relative_position_ego": (0.0, 0.0),
            "relative_velocity_ego": (0.0, 0.0), "range": 0.0, "distance": 0.0,
            "bearing_radians": 0.0, "length": state["length"], "width": state["width"],
            "visible_fraction": 1.0, "measurement_timestamp": timestamp,
            "available_timestamp": timestamp, "timestamp": timestamp,
            "detection_status": "SELF_LOCALIZATION", "perception_profile": "PERFECT_SUMO_LOCALIZATION",
        }
        result.update(cls._context_fields(state))
        return result

    @classmethod
    def _make_object_detection(cls, candidate, timestamp, visible_fraction):
        state = candidate["state"]
        velocity = cls._velocity_vector(state["speed"], state["heading_radians"])
        result = {
            "object_id": candidate["object_id"], "observation_type": "OBJECT_DETECTION",
            "position": tuple(state["position"]),
            "measured_position_world": tuple(state["position"]),
            "speed": state["speed"], "heading_radians": state["heading_radians"],
            "velocity_world": tuple(velocity),
            "relative_position_ego": tuple(candidate["relative_position"]),
            "relative_velocity_ego": tuple(candidate["relative_velocity"]),
            "range": candidate["range"], "distance": candidate["range"],
            "bearing_radians": candidate["bearing"], "length": state["length"],
            "width": state["width"], "visible_fraction": float(visible_fraction),
            "measurement_timestamp": timestamp, "available_timestamp": timestamp,
            "timestamp": timestamp, "detection_status": "DETECTED",
            "perception_profile": candidate["profile"],
        }
        result.update(cls._context_fields(state))
        return result
