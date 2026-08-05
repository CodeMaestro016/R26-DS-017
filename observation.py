"""Per-AV Local Dynamic Maps and genuine position histories."""

from collections import deque

import numpy as np

from config import (
    APPROACH_ZONE_RADIUS,
    CONFIDENCE_DECAY_RATE_PER_SECOND,
    CONFIDENCE_OBSERVED_BOOST,
    INTERSECTION_CENTER,
    MAX_CONFIDENCE,
    MIN_CONFIDENCE,
    MODEL_HISTORY_LENGTH,
    SENSOR_RANGE,
    TRACK_TIMEOUT_SECONDS,
)
from perception_interface import PerceptionInterface


class LocalDynamicMap:
    """Dynamic object tracks owned by one autonomous vehicle."""

    def __init__(self, ego_vehicle_id):
        self.ego_id = ego_vehicle_id
        self.tracks = {}
        self.in_approach_zone = False
        self.last_update_time = 0.0

    @staticmethod
    def _velocity_vector(speed, heading_radians):
        # SUMO uses navigational angles: 0=north and 90=east.
        vx = speed * np.sin(heading_radians)
        vy = speed * np.cos(heading_radians)
        return np.asarray([vx, vy], dtype=float)

    @staticmethod
    def _distance_to_center(position):
        return float(
            np.linalg.norm(
                np.asarray(position, dtype=float)
                - np.asarray(INTERSECTION_CENTER, dtype=float)
            )
        )

    def add_or_update_track(
        self,
        vehicle_id,
        position,
        speed,
        heading_radians,
        lane_id,
        lane_position,
        lane_length,
        road_id,
        current_time,
    ):
        previous = self.tracks.get(vehicle_id)
        if previous is None:
            history = deque(maxlen=MODEL_HISTORY_LENGTH)
            confidence = MAX_CONFIDENCE
            intention_prediction = None
        else:
            history = previous["position_history"]
            confidence = min(
                MAX_CONFIDENCE,
                previous["confidence"]
                + CONFIDENCE_OBSERVED_BOOST,
            )
            intention_prediction = previous.get(
                "intention_prediction"
            )

        if (
            not history
            or current_time > history[-1]["timestamp"]
        ):
            history.append(
                {
                    "timestamp": float(current_time),
                    "position": tuple(
                        np.asarray(position, dtype=float)
                    ),
                }
            )

        self.tracks[vehicle_id] = {
            "id": vehicle_id,
            "position": tuple(position),
            "speed": float(speed),
            "heading_radians": float(heading_radians),
            "lane_id": lane_id,
            "lane_position": float(lane_position),
            "lane_length": float(lane_length),
            "road_id": road_id,
            "distance_to_conflict": self._distance_to_center(
                position
            ),
            "last_observed_time": float(current_time),
            "last_update_time": float(current_time),
            "is_observed": True,
            "confidence": float(confidence),
            "velocity_vector": self._velocity_vector(
                speed,
                heading_radians,
            ),
            # Only genuine observations are added to this history.
            "position_history": history,
            "intention_prediction": intention_prediction,
        }

    def propagate_track(self, vehicle_id, current_time):
        track = self.tracks.get(vehicle_id)
        if track is None:
            return

        dt = max(
            0.0,
            float(current_time) - track["last_update_time"],
        )
        position = np.asarray(track["position"], dtype=float)
        predicted_position = (
            position + track["velocity_vector"] * dt
        )

        track["position"] = tuple(predicted_position)
        track["distance_to_conflict"] = self._distance_to_center(
            predicted_position
        )
        track["last_update_time"] = float(current_time)
        if track["lane_length"] > 0.0:
            track["lane_position"] = min(
                track["lane_length"],
                track["lane_position"] + track["speed"] * dt,
            )
        track["is_observed"] = False
        track["confidence"] = max(
            MIN_CONFIDENCE,
            track["confidence"]
            - CONFIDENCE_DECAY_RATE_PER_SECOND * dt,
        )
        # last_observed_time and position_history intentionally remain
        # unchanged because propagation is not a genuine observation.

    def remove_stale_tracks(self, current_time):
        stale_ids = [
            vehicle_id
            for vehicle_id, track in self.tracks.items()
            if vehicle_id != self.ego_id
            and current_time - track["last_observed_time"]
            > TRACK_TIMEOUT_SECONDS
        ]
        for vehicle_id in stale_ids:
            del self.tracks[vehicle_id]
        return len(stale_ids)

    def get_conflict_relevant_vehicles(self):
        """Provisional centre-approach filter.

        The later conflict-manager stage must replace this with lane-path and
        conflict-zone reasoning.
        """
        ego_track = self.tracks.get(self.ego_id)
        if ego_track is None:
            return {}

        ego_position = np.asarray(
            ego_track["position"],
            dtype=float,
        )
        center = np.asarray(INTERSECTION_CENTER, dtype=float)
        relevant = {}

        for vehicle_id, track in self.tracks.items():
            if vehicle_id == self.ego_id:
                continue

            position = np.asarray(track["position"], dtype=float)
            toward_center = center - position
            moving_toward_center = (
                np.dot(toward_center, track["velocity_vector"]) > 0.0
            )
            distance_to_ego = float(
                np.linalg.norm(position - ego_position)
            )

            if (
                moving_toward_center
                and distance_to_ego <= SENSOR_RANGE
            ):
                relevant[vehicle_id] = track

        return relevant

    def prediction_snapshot(self):
        return {
            vehicle_id: track["intention_prediction"]
            for vehicle_id, track in self.tracks.items()
            if vehicle_id != self.ego_id
            and track.get("intention_prediction") is not None
        }


class ObservationManager:
    """Create and update a separate LDM for every active AV."""

    def __init__(self):
        self.ldms = {}
        self.current_time = 0.0
        self.perception_interface = PerceptionInterface()

    def get_or_create_ldm(self, vehicle_id):
        if vehicle_id not in self.ldms:
            self.ldms[vehicle_id] = LocalDynamicMap(vehicle_id)
        return self.ldms[vehicle_id]

    def get_ldm(self, vehicle_id):
        return self.ldms.get(vehicle_id)

    @staticmethod
    def is_in_approach_zone(position):
        return (
            np.linalg.norm(
                np.asarray(position, dtype=float)
                - np.asarray(INTERSECTION_CENTER, dtype=float)
            )
            <= APPROACH_ZONE_RADIUS
        )

    def update(self, global_observations, current_time):
        self.current_time = float(current_time)
        vehicle_data = {}

        for vehicle_id, state in global_observations.items():
            vehicle_data[vehicle_id] = {
                "position": state["position"],
                "speed": state["speed"],
                "heading_radians": state["heading_radians"],
                "length": state["length"],
                "width": state["width"],
                "lane_id": state.get("lane_id", ""),
                "lane_position": state.get("lane_position", 0.0),
                "lane_length": state.get("lane_length", 0.0),
                "road_id": state.get("road_id", ""),
            }

        active_ids = set(vehicle_data)
        for vehicle_id in active_ids:
            self.get_or_create_ldm(vehicle_id)

        departed_ldms = [
            vehicle_id
            for vehicle_id in self.ldms
            if vehicle_id not in active_ids
        ]
        for vehicle_id in departed_ldms:
            del self.ldms[vehicle_id]
            self.perception_interface.clear_ego_diagnostics(vehicle_id)

        for ego_id, ldm in list(self.ldms.items()):
            ego_data = vehicle_data[ego_id]
            ldm.in_approach_zone = self.is_in_approach_zone(
                ego_data["position"]
            )
            ldm.last_update_time = self.current_time

            if not ldm.in_approach_zone:
                # Keep the ego state current, but do not build intersection
                # histories before the reasoning zone is reached.
                ego_track = ldm.tracks.get(ego_id)
                ldm.tracks = (
                    {ego_id: ego_track}
                    if ego_track is not None
                    else {}
                )
                ldm.add_or_update_track(
                    ego_id,
                    ego_data["position"],
                    ego_data["speed"],
                    ego_data["heading_radians"],
                    ego_data["lane_id"],
                    ego_data["lane_position"],
                    ego_data["lane_length"],
                    ego_data["road_id"],
                    self.current_time,
                )
                continue

            for track_id, track in ldm.tracks.items():
                if track_id != ego_id:
                    track["is_observed"] = False

            local_observations = (
                self.perception_interface.generate_observations(
                    ego_id,
                    ego_data,
                    vehicle_data,
                    self.current_time,
                )
            )

            for observed_id, observation in (
                local_observations.items()
            ):
                ldm.add_or_update_track(
                    observed_id,
                    observation["position"],
                    observation["speed"],
                    observation["heading_radians"],
                    observation["lane_id"],
                    observation["lane_position"],
                    observation["lane_length"],
                    observation["road_id"],
                    self.current_time,
                )

            for track_id, track in list(ldm.tracks.items()):
                if (
                    track_id != ego_id
                    and not track["is_observed"]
                ):
                    ldm.propagate_track(
                        track_id,
                        self.current_time,
                    )

            ldm.remove_stale_tracks(self.current_time)

    def reset(self):
        self.ldms.clear()
        self.current_time = 0.0
        self.perception_interface.clear_diagnostics()


observation_manager = ObservationManager()
