"""Per-AV Local Dynamic Maps and genuine position histories."""

# Import deque from collections for the operations below.
from collections import deque
# Import copy for use in this module.
import copy

# Import numpy as np for use in this module.
import numpy as np

# Import APPROACH_ZONE_RADIUS, CONFIDENCE_DECAY_RATE_PER_SECOND, CONFIDENCE_OBSERVED_BOOST, MAX_CONFIDENCE,
# MIN_CONFIDENCE, MODEL_HISTORY_LENGTH, SENSOR_RANGE,... from config for the operations below.
from config import (
    APPROACH_ZONE_RADIUS,
    CONFIDENCE_DECAY_RATE_PER_SECOND,
    CONFIDENCE_OBSERVED_BOOST,
    MAX_CONFIDENCE,
    MIN_CONFIDENCE,
    MODEL_HISTORY_LENGTH,
    SENSOR_RANGE,
    TRACK_TIMEOUT_SECONDS,
)
# Import PerceptionInterface from perception_interface for the operations below.
from perception_interface import PerceptionInterface
# Import get_intersection_geometry, is_position_in_approach_zone from map_geometry for the operations below.
from map_geometry import (
    get_intersection_geometry, is_position_in_approach_zone,
)


# Set INTERSECTION_GEOMETRY to the result of get_intersection_geometry().
INTERSECTION_GEOMETRY = get_intersection_geometry()


# Dynamic object tracks owned by one autonomous vehicle.
# Instances expose the attributes and methods implemented in this class.
class LocalDynamicMap:
    """Dynamic object tracks owned by one autonomous vehicle."""

    # Initialize the instance attributes and collaborators used by the operations below.
    # Input ego_vehicle_id: the supplied ego vehicle id.
    # Output: no explicit value; normal completion returns None.
    def __init__(self, ego_vehicle_id):
        # Set self.ego_id to ego_vehicle_id.
        self.ego_id = ego_vehicle_id
        # Set self.tracks to an empty dictionary.
        self.tracks = {}
        # Set self.in_approach_zone to False.
        self.in_approach_zone = False
        # Set self.last_update_time to 0.0.
        self.last_update_time = 0.0
        # Set self.current_conflict_graph to None.
        self.current_conflict_graph = None
        # Set self.current_temporal_assessment to None.
        self.current_temporal_assessment = None
        # Set self.current_regulatory_assessment to None.
        self.current_regulatory_assessment = None
        # Set self.current_negotiation_problem to None.
        self.current_negotiation_problem = None
        # Set self.current_encoded_graph_observation to None.
        self.current_encoded_graph_observation = None
        # Set self.current_negotiation_protocol_state to None.
        self.current_negotiation_protocol_state = None
        # Set self.current_negotiated_precedence_overlay to None.
        self.current_negotiated_precedence_overlay = None

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Velocity vector using the inputs and processing steps below.
    # Input speed: the supplied speed.
    # Input heading_radians: the supplied heading radians.
    # Output: the result of np.asarray(a list containing vx, vy).
    def _velocity_vector(speed, heading_radians):
        # SUMO uses navigational angles: 0=north and 90=east.
        # Set vx to speed multiplied by the result of np.sin(heading_radians).
        vx = speed * np.sin(heading_radians)
        # Set vy to speed multiplied by the result of np.cos(heading_radians).
        vy = speed * np.cos(heading_radians)
        # Return the result of np.asarray(a list containing vx, vy) to the caller.
        return np.asarray([vx, vy], dtype=float)

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Distance to center using the inputs and processing steps below.
    # Input position: the supplied position.
    # Output: a floating-point number built from the result of np.linalg.norm(the result of np.asarray(position)
    # minus the result of np.asarray(INTERSECTION_GEOMETRY.center_xy)).
    def _distance_to_center(position):
        # Return a floating-point number built from the result of np.linalg.norm(the result of
        # np.asarray(position) minus the result of np.asarray(INTERSECTION_GEOMETRY.center_xy)) to the caller.
        return float(
            # Supply the result of np.linalg.norm(the result of np.asarray(position) minus the result of
            # np.asarray(INTERSECTION_GEOMETRY.center_xy)) to float.
            np.linalg.norm(
                # Supply dtype as float.
                np.asarray(position, dtype=float)
                # Supply dtype as float.
                - np.asarray(INTERSECTION_GEOMETRY.center_xy, dtype=float)
            )
        )

    # Add or update track using the inputs and processing steps below.
    # Input vehicle_id: the identifier of the vehicle being processed.
    # Input position: the supplied position.
    # Input speed: the supplied speed.
    # Input heading_radians: the supplied heading radians.
    # Input lane_id: the supplied lane id.
    # Input lane_position: the supplied lane position.
    # Input lane_length: the supplied lane length.
    # Input road_id: the supplied road id.
    # Input current_time: the supplied current time.
    # Input length: the supplied length.
    # Input width: the supplied width.
    # Input self_planned_manoeuvre: the supplied self planned manoeuvre.
    # Input max_acceleration_mps2: the supplied max acceleration mps2.
    # Input comfortable_deceleration_mps2: the supplied comfortable deceleration mps2.
    # Input emergency_deceleration_mps2: the supplied emergency deceleration mps2.
    # Input max_speed_mps: the supplied max speed mps.
    # Output: no explicit value; normal completion returns None.
    # Processing: select branches using the stated conditions.
    def add_or_update_track(
        # Declare self as input parameter.
        self,
        # Declare vehicle_id as input parameter.
        vehicle_id,
        # Declare position as input parameter.
        position,
        # Declare speed as input parameter.
        speed,
        # Declare heading_radians as input parameter.
        heading_radians,
        # Declare lane_id as input parameter.
        lane_id,
        # Declare lane_position as input parameter.
        lane_position,
        # Declare lane_length as input parameter.
        lane_length,
        # Declare road_id as input parameter.
        road_id,
        # Declare current_time as input parameter.
        current_time,
        # Declare length as input parameter.
        length=None,
        # Declare width as input parameter.
        width=None,
        # Declare self_planned_manoeuvre as input parameter.
        self_planned_manoeuvre=None,
        # Declare max_acceleration_mps2 as input parameter.
        max_acceleration_mps2=None,
        # Declare comfortable_deceleration_mps2 as input parameter.
        comfortable_deceleration_mps2=None,
        # Declare emergency_deceleration_mps2 as input parameter.
        emergency_deceleration_mps2=None,
        # Declare max_speed_mps as input parameter.
        max_speed_mps=None,
    ):
        # Set previous to vehicle_id from self.tracks; use None if absent.
        previous = self.tracks.get(vehicle_id)
        # Run this branch when previous is the same object as None.
        if previous is None:
            # Set history to the result of deque().
            history = deque(maxlen=MODEL_HISTORY_LENGTH)
            # Set confidence to MAX_CONFIDENCE.
            confidence = MAX_CONFIDENCE
            # Set intention_prediction to None.
            intention_prediction = None
        # Run this alternative branch when the preceding branch does not apply.
        else:
            # Set history to previous at 'position_history'.
            history = previous["position_history"]
            # Set confidence to the minimum of MAX_CONFIDENCE, previous at 'confidence' plus
            # CONFIDENCE_OBSERVED_BOOST.
            confidence = min(
                # Supply MAX_CONFIDENCE to min.
                MAX_CONFIDENCE,
                # Supply previous at 'confidence' plus CONFIDENCE_OBSERVED_BOOST to min.
                previous["confidence"]
                # Evaluate CONFIDENCE_OBSERVED_BOOST as part of the enclosing expression.
                + CONFIDENCE_OBSERVED_BOOST,
            )
            # Set intention_prediction to 'intention_prediction' from previous; use None if absent.
            intention_prediction = previous.get(
                "intention_prediction"
            )

        # Run this branch when the negation of history or current_time is greater than history[-1] at 'timestamp'.
        if (
            # Evaluate the negation of history or current_time is greater than history[-1] at 'timestamp' as part
            # of the enclosing expression.
            not history
            # Evaluate current_time is greater than history[-1] at 'timestamp' as part of the enclosing
            # expression.
            or current_time > history[-1]["timestamp"]
        ):
            # Append a dictionary containing timestamp, position to history.
            history.append(
                # Supply a dictionary containing timestamp, position to history.append.
                {
                    # Store a floating-point number built from current_time under 'timestamp'.
                    "timestamp": float(current_time),
                    # Store a tuple built from the result of np.asarray(position) under 'position'.
                    "position": tuple(
                        # Supply dtype as float.
                        np.asarray(position, dtype=float)
                    ),
                }
            )

        # Set self.tracks[vehicle_id] to a dictionary containing id, position, speed, heading_radians, lane_id,
        # lane_position, lane_length, road_id,...
        self.tracks[vehicle_id] = {
            # Store vehicle_id under 'id'.
            "id": vehicle_id,
            # Store a tuple built from position under 'position'.
            "position": tuple(position),
            # Store a floating-point number built from speed under 'speed'.
            "speed": float(speed),
            # Store a floating-point number built from heading_radians under 'heading_radians'.
            "heading_radians": float(heading_radians),
            # Store lane_id under 'lane_id'.
            "lane_id": lane_id,
            # Store a floating-point number built from lane_position under 'lane_position'.
            "lane_position": float(lane_position),
            # Store a floating-point number built from lane_length under 'lane_length'.
            "lane_length": float(lane_length),
            # Store road_id under 'road_id'.
            "road_id": road_id,
            # Store a floating-point number built from length when length is a different object from None,
            # otherwise 'length' from previous; use None if absent when previous, otherwise None under 'length'.
            "length": float(length) if length is not None else (
                # Evaluate 'length' from previous; use None if absent when previous, otherwise None as part of the
                # enclosing expression.
                previous.get("length") if previous else None
            ),
            # Store a floating-point number built from width when width is a different object from None, otherwise
            # 'width' from previous; use None if absent when previous, otherwise None under 'width'.
            "width": float(width) if width is not None else (
                # Evaluate 'width' from previous; use None if absent when previous, otherwise None as part of the
                # enclosing expression.
                previous.get("width") if previous else None
            ),
            # Store the result of self._distance_to_center(position) under 'distance_to_conflict'.
            "distance_to_conflict": self._distance_to_center(
                # Supply position to self._distance_to_center.
                position
            ),
            # Store a floating-point number built from current_time under 'last_observed_time'.
            "last_observed_time": float(current_time),
            # Store a floating-point number built from current_time under 'last_update_time'.
            "last_update_time": float(current_time),
            # Store True under 'is_observed'.
            "is_observed": True,
            # Store a floating-point number built from confidence under 'confidence'.
            "confidence": float(confidence),
            # Store the result of self._velocity_vector(speed, heading_radians) under 'velocity_vector'.
            "velocity_vector": self._velocity_vector(
                # Supply speed to self._velocity_vector.
                speed,
                # Supply heading_radians to self._velocity_vector.
                heading_radians,
            ),
            # Only genuine front-bumper observations are added to this
            # history. Do not convert these model inputs to geometric centers
            # until the original training-pipeline reference is verified.
            # Store history under 'position_history'.
            "position_history": history,
            # Store intention_prediction under 'intention_prediction'.
            "intention_prediction": intention_prediction,
            # Store max_acceleration_mps2 when max_acceleration_mps2 is a different object from None, otherwise
            # 'max_acceleration_mps2' from previous; use None if absent when previous, otherwise None under
            # 'max_acceleration_mps2'.
            "max_acceleration_mps2": (
                # Evaluate max_acceleration_mps2 when max_acceleration_mps2 is a different object from None,
                # otherwise 'max_acceleration_mps2' from previous; use None if absent when previous, otherwise
                # None as part of the enclosing expression.
                max_acceleration_mps2 if max_acceleration_mps2 is not None
                # Evaluate 'max_acceleration_mps2' from previous; use None if absent when previous, otherwise None
                # as part of the enclosing expression.
                else previous.get("max_acceleration_mps2") if previous else None
            ),
            # Store comfortable_deceleration_mps2 when comfortable_deceleration_mps2 is a different object from
            # None, otherwise 'comfortable_deceleration_mps2' from previous; use None if absent when previous,
            # otherwise None under 'comfortable_deceleration_mps2'.
            "comfortable_deceleration_mps2": (
                # Evaluate comfortable_deceleration_mps2 when comfortable_deceleration_mps2 is a different object
                # from None, otherwise 'comfortable_deceleration_mps2' from previous; use None if absent when
                # previous, otherwise None as part of the enclosing expression.
                comfortable_deceleration_mps2
                # Evaluate comfortable_deceleration_mps2 is a different object from None as part of the enclosing
                # expression.
                if comfortable_deceleration_mps2 is not None
                # Evaluate 'comfortable_deceleration_mps2' from previous; use None if absent when previous,
                # otherwise None as part of the enclosing expression.
                else previous.get("comfortable_deceleration_mps2")
                # Evaluate previous as part of the enclosing expression.
                if previous else None
            ),
            # Store emergency_deceleration_mps2 when emergency_deceleration_mps2 is a different object from None,
            # otherwise 'emergency_deceleration_mps2' from previous; use None if absent when previous, otherwise
            # None under 'emergency_deceleration_mps2'.
            "emergency_deceleration_mps2": (
                # Evaluate emergency_deceleration_mps2 when emergency_deceleration_mps2 is a different object from
                # None, otherwise 'emergency_deceleration_mps2' from previous; use None if absent when previous,
                # otherwise None as part of the enclosing expression.
                emergency_deceleration_mps2
                # Evaluate emergency_deceleration_mps2 is a different object from None as part of the enclosing
                # expression.
                if emergency_deceleration_mps2 is not None
                # Evaluate 'emergency_deceleration_mps2' from previous; use None if absent when previous,
                # otherwise None as part of the enclosing expression.
                else previous.get("emergency_deceleration_mps2")
                # Evaluate previous as part of the enclosing expression.
                if previous else None
            ),
            # Store max_speed_mps when max_speed_mps is a different object from None, otherwise 'max_speed_mps'
            # from previous; use None if absent when previous, otherwise None under 'max_speed_mps'.
            "max_speed_mps": (
                # Evaluate max_speed_mps when max_speed_mps is a different object from None, otherwise
                # 'max_speed_mps' from previous; use None if absent when previous, otherwise None as part of the
                # enclosing expression.
                max_speed_mps if max_speed_mps is not None
                # Evaluate 'max_speed_mps' from previous; use None if absent when previous, otherwise None as part
                # of the enclosing expression.
                else previous.get("max_speed_mps") if previous else None
            ),
        }
        # Run this branch when vehicle_id equals self.ego_id and self_planned_manoeuvre is a different object from
        # None.
        if vehicle_id == self.ego_id and self_planned_manoeuvre is not None:
            # Set self.tracks[vehicle_id]['self_planned_manoeuvre'] to self_planned_manoeuvre.
            self.tracks[vehicle_id]["self_planned_manoeuvre"] = (
                # Evaluate self_planned_manoeuvre as part of the enclosing expression.
                self_planned_manoeuvre
            )

    # Propagate track using the inputs and processing steps below.
    # Input vehicle_id: the identifier of the vehicle being processed.
    # Input current_time: the supplied current time.
    # Output: no explicit value; normal completion returns None.
    # Processing: select branches using the stated conditions.
    def propagate_track(self, vehicle_id, current_time):
        # Set track to vehicle_id from self.tracks; use None if absent.
        track = self.tracks.get(vehicle_id)
        # Run this branch when track is the same object as None.
        if track is None:
            # Return no value to the caller.
            return

        # Set dt to the maximum of 0.0, a floating-point number built from current_time minus track at
        # 'last_update_time'.
        dt = max(
            # Supply 0.0 to the enclosing expression.
            0.0,
            # Supply a floating-point number built from current_time minus track at 'last_update_time' to max.
            float(current_time) - track["last_update_time"],
        )
        # Set position to the result of np.asarray(track at 'position').
        position = np.asarray(track["position"], dtype=float)
        # Set predicted_position to position plus track at 'velocity_vector' multiplied by dt.
        predicted_position = (
            # Evaluate position plus track at 'velocity_vector' multiplied by dt as part of the enclosing
            # expression.
            position + track["velocity_vector"] * dt
        )

        # Set track['position'] to a tuple built from predicted_position.
        track["position"] = tuple(predicted_position)
        # Set track['distance_to_conflict'] to the result of self._distance_to_center(predicted_position).
        track["distance_to_conflict"] = self._distance_to_center(
            # Supply predicted_position to self._distance_to_center.
            predicted_position
        )
        # Set track['last_update_time'] to a floating-point number built from current_time.
        track["last_update_time"] = float(current_time)
        # Run this branch when track at 'lane_length' is greater than 0.0.
        if track["lane_length"] > 0.0:
            # Set track['lane_position'] to the minimum of track at 'lane_length', track at 'lane_position' plus
            # track at 'speed' multiplied by dt.
            track["lane_position"] = min(
                # Supply track at 'lane_length' to min.
                track["lane_length"],
                # Supply track at 'lane_position' plus track at 'speed' multiplied by dt to min.
                track["lane_position"] + track["speed"] * dt,
            )
        # Set track['is_observed'] to False.
        track["is_observed"] = False
        # Set track['confidence'] to the maximum of MIN_CONFIDENCE, track at 'confidence' minus
        # CONFIDENCE_DECAY_RATE_PER_SECOND multiplied by dt.
        track["confidence"] = max(
            # Supply MIN_CONFIDENCE to max.
            MIN_CONFIDENCE,
            # Supply track at 'confidence' minus CONFIDENCE_DECAY_RATE_PER_SECOND multiplied by dt to max.
            track["confidence"]
            # Evaluate CONFIDENCE_DECAY_RATE_PER_SECOND multiplied by dt as part of the enclosing expression.
            - CONFIDENCE_DECAY_RATE_PER_SECOND * dt,
        )
        # last_observed_time and position_history intentionally remain
        # unchanged because propagation is not a genuine observation.

    # Remove stale tracks using the inputs and processing steps below.
    # Input current_time: the supplied current time.
    # Output: the number of entries in stale_ids.
    # Processing: iterate over the relevant records.
    def remove_stale_tracks(self, current_time):
        # Set stale_ids to a list of vehicle_id for (vehicle_id, track) in key/value pairs from self.tracks;
        # retain entries satisfying vehicle_id differs from self.ego_id and current_time minus
        # track['last_observed_time']...
        stale_ids = [
            # Evaluate vehicle_id as part of the enclosing expression.
            vehicle_id
            # Evaluate key/value pairs from self.tracks as part of the enclosing expression.
            for vehicle_id, track in self.tracks.items()
            # Evaluate vehicle_id differs from self.ego_id and current_time minus track at 'last_observed_time' is
            # greater than TRACK_TIMEOUT_SECONDS as part of the enclosing expression.
            if vehicle_id != self.ego_id
            # Evaluate current_time minus track at 'last_observed_time' is greater than TRACK_TIMEOUT_SECONDS as
            # part of the enclosing expression.
            and current_time - track["last_observed_time"]
            # Evaluate TRACK_TIMEOUT_SECONDS as part of the enclosing expression.
            > TRACK_TIMEOUT_SECONDS
        ]
        # Iterate over stale_ids, binding each item to vehicle_id.
        for vehicle_id in stale_ids:
            # Delete self.tracks[vehicle_id] from its containing namespace or collection.
            del self.tracks[vehicle_id]
        # Return the number of entries in stale_ids to the caller.
        return len(stale_ids)

    # Legacy centre-approach filter retained for baseline compatibility.
    # Output: return the value selected by the matching return branch below.
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    def get_legacy_center_conflict_relevant_vehicles(self):
        """Legacy centre-approach filter retained for baseline compatibility."""
        # Set ego_track to self.ego_id from self.tracks; use None if absent.
        ego_track = self.tracks.get(self.ego_id)
        # Run this branch when ego_track is the same object as None.
        if ego_track is None:
            # Return an empty dictionary to the caller.
            return {}

        # Set ego_position to the result of np.asarray(ego_track at 'position').
        ego_position = np.asarray(
            # Supply ego_track at 'position' to np.asarray.
            ego_track["position"],
            # Supply dtype as float.
            dtype=float,
        )
        # Set center to the result of np.asarray(INTERSECTION_GEOMETRY.center_xy).
        center = np.asarray(INTERSECTION_GEOMETRY.center_xy, dtype=float)
        # Set relevant to an empty dictionary.
        relevant = {}

        # Iterate over key/value pairs from self.tracks, binding each item to (vehicle_id, track).
        for vehicle_id, track in self.tracks.items():
            # Run this branch when vehicle_id equals self.ego_id.
            if vehicle_id == self.ego_id:
                # Skip the rest of this loop iteration and process the next item.
                continue

            # Set position to the result of np.asarray(track at 'position').
            position = np.asarray(track["position"], dtype=float)
            # Set toward_center to center minus position.
            toward_center = center - position
            # Set moving_toward_center to the result of np.dot(toward_center, track at 'velocity_vector') is
            # greater than 0.0.
            moving_toward_center = (
                # Evaluate the result of np.dot(toward_center, track at 'velocity_vector') is greater than 0.0 as
                # part of the enclosing expression.
                np.dot(toward_center, track["velocity_vector"]) > 0.0
            )
            # Set distance_to_ego to a floating-point number built from the result of np.linalg.norm(position
            # minus ego_position).
            distance_to_ego = float(
                # Supply the result of np.linalg.norm(position minus ego_position) to float.
                np.linalg.norm(position - ego_position)
            )

            # Run this branch when moving_toward_center and distance_to_ego is at most SENSOR_RANGE.
            if (
                # Evaluate moving_toward_center and distance_to_ego is at most SENSOR_RANGE as part of the
                # enclosing expression.
                moving_toward_center
                # Evaluate distance_to_ego is at most SENSOR_RANGE as part of the enclosing expression.
                and distance_to_ego <= SENSOR_RANGE
            ):
                # Set relevant[vehicle_id] to track.
                relevant[vehicle_id] = track

        # Return relevant to the caller.
        return relevant

    # Compatibility alias used only by prediction timing/legacy modules.
    # Output: the result of self.get_legacy_center_conflict_relevant_vehicles().
    def get_conflict_relevant_vehicles(self):
        """Compatibility alias used only by prediction timing/legacy modules.

        New spatial-conflict consumers must use ``get_current_conflict_graph``.
        """
        # Return the result of self.get_legacy_center_conflict_relevant_vehicles() to the caller.
        return self.get_legacy_center_conflict_relevant_vehicles()

    # Preferred map-aware graph snapshot; legacy filters remain separate.
    # Output: self.current_conflict_graph.
    def get_current_conflict_graph(self):
        """Preferred map-aware graph snapshot; legacy filters remain separate."""
        # Return self.current_conflict_graph to the caller.
        return self.current_conflict_graph

    # Return shadow conflict-zone occupancy evidence for this ego.
    # Output: self.current_temporal_assessment.
    def get_current_temporal_assessment(self):
        """Return shadow conflict-zone occupancy evidence for this ego."""
        # Return self.current_temporal_assessment to the caller.
        return self.current_temporal_assessment

    # Return the current shadow German-StVO assessment for this ego.
    # Output: self.current_regulatory_assessment.
    def get_current_regulatory_assessment(self):
        """Return the current shadow German-StVO assessment for this ego."""
        # Return self.current_regulatory_assessment to the caller.
        return self.current_regulatory_assessment

    # Return the current shadow-only local MARL problem snapshot.
    # Output: self.current_negotiation_problem.
    def get_current_negotiation_problem(self):
        """Return the current shadow-only local MARL problem snapshot."""
        # Return self.current_negotiation_problem to the caller.
        return self.current_negotiation_problem

    # Return the read-only NumPy GNN input built in shadow mode.
    # Output: self.current_encoded_graph_observation.
    def get_current_encoded_graph_observation(self):
        """Return the read-only NumPy GNN input built in shadow mode."""
        # Return self.current_encoded_graph_observation to the caller.
        return self.current_encoded_graph_observation

    # Return shadow protocol readiness/evidence for the current snapshot.
    # Output: self.current_negotiation_protocol_state.
    def get_current_negotiation_protocol_state(self):
        """Return shadow protocol readiness/evidence for the current snapshot."""
        # Return self.current_negotiation_protocol_state to the caller.
        return self.current_negotiation_protocol_state

    # Return a claim-specific overlay; never a mutated regulatory graph.
    # Output: self.current_negotiated_precedence_overlay.
    def get_current_negotiated_precedence_overlay(self):
        """Return a claim-specific overlay; never a mutated regulatory graph."""
        # Return self.current_negotiated_precedence_overlay to the caller.
        return self.current_negotiated_precedence_overlay

    # Prediction snapshot using the inputs and processing steps below.
    # Output: a dictionary of vehicle_id mapped to track at 'intention_prediction' for (vehicle_id, track) in
    # key/value pairs from self.tracks; retain entries satisfying vehicle_id differs from...
    def prediction_snapshot(self):
        # Return a dictionary of vehicle_id mapped to track at 'intention_prediction' for (vehicle_id, track) in
        # key/value pairs from self.tracks; retain entries satisfying vehicle_id differs from self.ego_id and
        # 'intention_prediction' from track; use None if... to the caller.
        return {
            # Evaluate track at 'intention_prediction' as part of the enclosing expression.
            vehicle_id: track["intention_prediction"]
            # Evaluate key/value pairs from self.tracks as part of the enclosing expression.
            for vehicle_id, track in self.tracks.items()
            # Evaluate vehicle_id differs from self.ego_id and 'intention_prediction' from track; use None if
            # absent is a different object from None as part of the enclosing expression.
            if vehicle_id != self.ego_id
            # Evaluate 'intention_prediction' from track; use None if absent is a different object from None as
            # part of the enclosing expression.
            and track.get("intention_prediction") is not None
        }


# Create and update a separate LDM for every active AV.
# Instances expose the attributes and methods implemented in this class.
class ObservationManager:
    """Create and update a separate LDM for every active AV."""

    # Initialize the instance attributes and collaborators used by the operations below.
    # Output: no explicit value; normal completion returns None.
    def __init__(self):
        # Set self.ldms to an empty dictionary.
        self.ldms = {}
        # Set self.current_time to 0.0.
        self.current_time = 0.0
        # Set self.perception_interface to the result of PerceptionInterface().
        self.perception_interface = PerceptionInterface()
        # Presentation-only copy of the exact latest perception output.  No
        # operational consumer reads this structure.
        # Set self.last_local_observations_by_ego to an empty dictionary.
        self.last_local_observations_by_ego = {}

    # Get or create ldm using the inputs and processing steps below.
    # Input vehicle_id: the identifier of the vehicle being processed.
    # Output: self.ldms at vehicle_id.
    # Processing: select branches using the stated conditions.
    def get_or_create_ldm(self, vehicle_id):
        # Run this branch when vehicle_id does not belong to self.ldms.
        if vehicle_id not in self.ldms:
            # Set self.ldms[vehicle_id] to the result of LocalDynamicMap(vehicle_id).
            self.ldms[vehicle_id] = LocalDynamicMap(vehicle_id)
        # Return self.ldms at vehicle_id to the caller.
        return self.ldms[vehicle_id]

    # Get ldm using the inputs and processing steps below.
    # Input vehicle_id: the identifier of the vehicle being processed.
    # Output: vehicle_id from self.ldms; use None if absent.
    def get_ldm(self, vehicle_id):
        # Return vehicle_id from self.ldms; use None if absent to the caller.
        return self.ldms.get(vehicle_id)

    # Return defensive copies of retained visualization evidence.
    # Input ego_id: the identifier of the ego vehicle.
    # Output: return the value selected by the matching return branch below.
    # Processing: select branches using the stated conditions.
    def get_last_local_observations(self, ego_id=None):
        """Return defensive copies of retained visualization evidence."""
        # Run this branch when ego_id is the same object as None.
        if ego_id is None:
            # Return the result of copy.deepcopy(self.last_local_observations_by_ego) to the caller.
            return copy.deepcopy(self.last_local_observations_by_ego)
        # Return the result of copy.deepcopy(ego_id from self.last_local_observations_by_ego; use an empty
        # dictionary if absent) to the caller.
        return copy.deepcopy(
            # Supply ego_id from self.last_local_observations_by_ego; use an empty dictionary if absent to
            # copy.deepcopy.
            self.last_local_observations_by_ego.get(ego_id, {})
        )

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Expose only an ego's own navigation intent, never target route truth.
    # Input ego_id: the identifier of the ego vehicle.
    # Input ego_state: the supplied ego state.
    # Output: suffix when suffix belongs to a set containing the text 'LEFT', the text 'RIGHT', the text
    # 'STRAIGHT', otherwise None.
    def get_ego_planned_manoeuvre(ego_id, ego_state):
        """Expose only an ego's own navigation intent, never target route truth."""
        # Delete ego_id from its containing namespace or collection.
        del ego_id
        # Set route_id to 'route_id' from ego_state; use the text '' if absent.
        route_id = ego_state.get("route_id", "")
        # Set suffix to the result of route_id.rsplit('_', 1)[-1].upper().
        suffix = route_id.rsplit("_", 1)[-1].upper()
        # Return suffix when suffix belongs to a set containing the text 'LEFT', the text 'RIGHT', the text
        # 'STRAIGHT', otherwise None to the caller.
        return suffix if suffix in {"LEFT", "RIGHT", "STRAIGHT"} else None

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Is in approach zone using the inputs and processing steps below.
    # Input position: the supplied position.
    # Output: the result of is_position_in_approach_zone(position, INTERSECTION_GEOMETRY, APPROACH_ZONE_RADIUS).
    def is_in_approach_zone(position):
        # Return the result of is_position_in_approach_zone(position, INTERSECTION_GEOMETRY, APPROACH_ZONE_RADIUS)
        # to the caller.
        return is_position_in_approach_zone(
            # Supply INTERSECTION_GEOMETRY to is_position_in_approach_zone.
            position, INTERSECTION_GEOMETRY, APPROACH_ZONE_RADIUS)

    # Update using the inputs and processing steps below.
    # Input global_observations: the supplied global observations.
    # Input current_time: the supplied current time.
    # Output: no explicit value; normal completion returns None.
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    def update(self, global_observations, current_time):
        # Set self.current_time to a floating-point number built from current_time.
        self.current_time = float(current_time)
        # Set vehicle_data to an empty dictionary.
        vehicle_data = {}

        # Iterate over key/value pairs from global_observations, binding each item to (vehicle_id, state).
        for vehicle_id, state in global_observations.items():
            # Set vehicle_data[vehicle_id] to a dictionary containing position, speed, heading_radians, length,
            # width, lane_id, lane_position, lane_length,...
            vehicle_data[vehicle_id] = {
                # Store state at 'position' under 'position'.
                "position": state["position"],
                # Store state at 'speed' under 'speed'.
                "speed": state["speed"],
                # Store state at 'heading_radians' under 'heading_radians'.
                "heading_radians": state["heading_radians"],
                # Store state at 'length' under 'length'.
                "length": state["length"],
                # Store state at 'width' under 'width'.
                "width": state["width"],
                # Store 'lane_id' from state; use the text '' if absent under 'lane_id'.
                "lane_id": state.get("lane_id", ""),
                # Store 'lane_position' from state; use 0.0 if absent under 'lane_position'.
                "lane_position": state.get("lane_position", 0.0),
                # Store 'lane_length' from state; use 0.0 if absent under 'lane_length'.
                "lane_length": state.get("lane_length", 0.0),
                # Store 'road_id' from state; use the text '' if absent under 'road_id'.
                "road_id": state.get("road_id", ""),
                # Store 'max_acceleration_mps2' from state; use None if absent under 'max_acceleration_mps2'.
                "max_acceleration_mps2": state.get("max_acceleration_mps2"),
                # Store 'comfortable_deceleration_mps2' from state; use None if absent under
                # 'comfortable_deceleration_mps2'.
                "comfortable_deceleration_mps2": state.get(
                    "comfortable_deceleration_mps2"
                ),
                # Store 'emergency_deceleration_mps2' from state; use None if absent under
                # 'emergency_deceleration_mps2'.
                "emergency_deceleration_mps2": state.get(
                    "emergency_deceleration_mps2"
                ),
                # Store 'max_speed_mps' from state; use None if absent under 'max_speed_mps'.
                "max_speed_mps": state.get("max_speed_mps"),
            }

        # Set active_ids to a set built from vehicle_data.
        active_ids = set(vehicle_data)
        # Iterate over active_ids, binding each item to vehicle_id.
        for vehicle_id in active_ids:
            # Call self.get_or_create_ldm with the supplied arguments.
            self.get_or_create_ldm(vehicle_id)

        # Set departed_ldms to a list of vehicle_id for vehicle_id in self.ldms; retain entries satisfying
        # vehicle_id does not belong to active_ids.
        departed_ldms = [
            # Evaluate vehicle_id as part of the enclosing expression.
            vehicle_id
            # Evaluate vehicle_id as part of the enclosing expression.
            for vehicle_id in self.ldms
            # Evaluate vehicle_id does not belong to active_ids as part of the enclosing expression.
            if vehicle_id not in active_ids
        ]
        # Iterate over departed_ldms, binding each item to vehicle_id.
        for vehicle_id in departed_ldms:
            # Delete self.ldms[vehicle_id] from its containing namespace or collection.
            del self.ldms[vehicle_id]
            # Remove the requested entry from self.last_local_observations_by_ego.
            self.last_local_observations_by_ego.pop(vehicle_id, None)
            # Call self.perception_interface.clear_ego_diagnostics with the supplied arguments.
            self.perception_interface.clear_ego_diagnostics(vehicle_id)

        # Iterate over a list built from key/value pairs from self.ldms, binding each item to (ego_id, ldm).
        for ego_id, ldm in list(self.ldms.items()):
            # Set ego_data to vehicle_data at ego_id.
            ego_data = vehicle_data[ego_id]
            # Set ldm.in_approach_zone to the result of self.is_in_approach_zone(ego_data at 'position').
            ldm.in_approach_zone = self.is_in_approach_zone(
                # Supply ego_data at 'position' to self.is_in_approach_zone.
                ego_data["position"]
            )
            # Set ldm.last_update_time to self.current_time.
            ldm.last_update_time = self.current_time

            # Run this branch when the negation of ldm.in_approach_zone.
            if not ldm.in_approach_zone:
                # Remove the requested entry from self.last_local_observations_by_ego.
                self.last_local_observations_by_ego.pop(ego_id, None)
                # Call self.perception_interface.clear_ego_diagnostics with the supplied arguments.
                self.perception_interface.clear_ego_diagnostics(ego_id)
                # Keep the ego state current, but do not build intersection
                # histories before the reasoning zone is reached.
                # Set ego_track to ego_id from ldm.tracks; use None if absent.
                ego_track = ldm.tracks.get(ego_id)
                # Set ldm.tracks to a dictionary of the supplied entries when ego_track is a different object from
                # None, otherwise an empty dictionary.
                ldm.tracks = (
                    # Store ego_track under ego_id.
                    {ego_id: ego_track}
                    # Evaluate ego_track is a different object from None as part of the enclosing expression.
                    if ego_track is not None
                    # Evaluate an empty dictionary as part of the enclosing expression.
                    else {}
                )
                # Set ldm.current_regulatory_assessment to None.
                ldm.current_regulatory_assessment = None
                # Set ldm.current_negotiation_problem to None.
                ldm.current_negotiation_problem = None
                # Set ldm.current_encoded_graph_observation to None.
                ldm.current_encoded_graph_observation = None
                # Set ldm.current_negotiation_protocol_state to None.
                ldm.current_negotiation_protocol_state = None
                # Set ldm.current_negotiated_precedence_overlay to None.
                ldm.current_negotiated_precedence_overlay = None
                # Call ldm.add_or_update_track with the supplied arguments.
                ldm.add_or_update_track(
                    # Supply ego_id to ldm.add_or_update_track.
                    ego_id,
                    # Supply ego_data at 'position' to ldm.add_or_update_track.
                    ego_data["position"],
                    # Supply ego_data at 'speed' to ldm.add_or_update_track.
                    ego_data["speed"],
                    # Supply ego_data at 'heading_radians' to ldm.add_or_update_track.
                    ego_data["heading_radians"],
                    # Supply ego_data at 'lane_id' to ldm.add_or_update_track.
                    ego_data["lane_id"],
                    # Supply ego_data at 'lane_position' to ldm.add_or_update_track.
                    ego_data["lane_position"],
                    # Supply ego_data at 'lane_length' to ldm.add_or_update_track.
                    ego_data["lane_length"],
                    # Supply ego_data at 'road_id' to ldm.add_or_update_track.
                    ego_data["road_id"],
                    # Supply self.current_time to ldm.add_or_update_track.
                    self.current_time,
                    # Supply length as ego_data at 'length'.
                    length=ego_data["length"],
                    # Supply width as ego_data at 'width'.
                    width=ego_data["width"],
                    # Supply self_planned_manoeuvre as the result of self.get_ego_planned_manoeuvre(ego_id,
                    # global_observations at ego_id).
                    self_planned_manoeuvre=self.get_ego_planned_manoeuvre(
                        # Supply global_observations at ego_id to self.get_ego_planned_manoeuvre.
                        ego_id, global_observations[ego_id]
                    ),
                    # Supply max_acceleration_mps2 as ego_data at 'max_acceleration_mps2'.
                    max_acceleration_mps2=ego_data["max_acceleration_mps2"],
                    # Supply comfortable_deceleration_mps2 as ego_data at 'comfortable_deceleration_mps2'.
                    comfortable_deceleration_mps2=ego_data[
                        "comfortable_deceleration_mps2"
                    ],
                    # Supply emergency_deceleration_mps2 as ego_data at 'emergency_deceleration_mps2'.
                    emergency_deceleration_mps2=ego_data[
                        "emergency_deceleration_mps2"
                    ],
                    # Supply max_speed_mps as ego_data at 'max_speed_mps'.
                    max_speed_mps=ego_data["max_speed_mps"],
                )
                # Skip the rest of this loop iteration and process the next item.
                continue

            # Iterate over key/value pairs from ldm.tracks, binding each item to (track_id, track).
            for track_id, track in ldm.tracks.items():
                # Run this branch when track_id differs from ego_id.
                if track_id != ego_id:
                    # Set track['is_observed'] to False.
                    track["is_observed"] = False

            # Set local_observations to the result of self.perception_interface.generate_observations(ego_id,
            # ego_data, vehicle_data, self.current_time).
            local_observations = (
                # Evaluate the result of self.perception_interface.generate_observations(ego_id, ego_data,
                # vehicle_data, self.current_time) as part of the enclosing expression.
                self.perception_interface.generate_observations(
                    # Supply ego_id to self.perception_interface.generate_observations.
                    ego_id,
                    # Supply ego_data to self.perception_interface.generate_observations.
                    ego_data,
                    # Supply vehicle_data to self.perception_interface.generate_observations.
                    vehicle_data,
                    # Supply self.current_time to self.perception_interface.generate_observations.
                    self.current_time,
                )
            )
            # Set self.last_local_observations_by_ego[ego_id] to the result of copy.deepcopy(local_observations).
            self.last_local_observations_by_ego[ego_id] = copy.deepcopy(
                # Supply local_observations to copy.deepcopy.
                local_observations
            )

            # Iterate over key/value pairs from local_observations, binding each item to (observed_id,
            # observation).
            for observed_id, observation in (
                # Evaluate key/value pairs from local_observations as part of the enclosing expression.
                local_observations.items()
            ):
                # Call ldm.add_or_update_track with the supplied arguments.
                ldm.add_or_update_track(
                    # Supply observed_id to ldm.add_or_update_track.
                    observed_id,
                    # Supply observation at 'position' to ldm.add_or_update_track.
                    observation["position"],
                    # Supply observation at 'speed' to ldm.add_or_update_track.
                    observation["speed"],
                    # Supply observation at 'heading_radians' to ldm.add_or_update_track.
                    observation["heading_radians"],
                    # Supply observation at 'lane_id' to ldm.add_or_update_track.
                    observation["lane_id"],
                    # Supply observation at 'lane_position' to ldm.add_or_update_track.
                    observation["lane_position"],
                    # Supply observation at 'lane_length' to ldm.add_or_update_track.
                    observation["lane_length"],
                    # Supply observation at 'road_id' to ldm.add_or_update_track.
                    observation["road_id"],
                    # Supply self.current_time to ldm.add_or_update_track.
                    self.current_time,
                    # Supply length as 'length' from observation; use None if absent.
                    length=observation.get("length"),
                    # Supply width as 'width' from observation; use None if absent.
                    width=observation.get("width"),
                    # Supply self_planned_manoeuvre as the result of self.get_ego_planned_manoeuvre(ego_id,
                    # global_observations at ego_id) when observed_id equals ego_id, otherwise None.
                    self_planned_manoeuvre=(
                        # Evaluate the result of self.get_ego_planned_manoeuvre(ego_id, global_observations at
                        # ego_id) when observed_id equals ego_id, otherwise None as part of the enclosing
                        # expression.
                        self.get_ego_planned_manoeuvre(
                            # Supply global_observations at ego_id to self.get_ego_planned_manoeuvre.
                            ego_id, global_observations[ego_id]
                        # Evaluate observed_id equals ego_id as part of the enclosing expression.
                        ) if observed_id == ego_id else None
                    ),
                    # Supply max_acceleration_mps2 as 'max_acceleration_mps2' from observation; use None if
                    # absent.
                    max_acceleration_mps2=observation.get(
                        "max_acceleration_mps2"
                    ),
                    # Supply comfortable_deceleration_mps2 as 'comfortable_deceleration_mps2' from observation;
                    # use None if absent.
                    comfortable_deceleration_mps2=observation.get(
                        "comfortable_deceleration_mps2"
                    ),
                    # Supply emergency_deceleration_mps2 as 'emergency_deceleration_mps2' from observation; use
                    # None if absent.
                    emergency_deceleration_mps2=observation.get(
                        "emergency_deceleration_mps2"
                    ),
                    # Supply max_speed_mps as 'max_speed_mps' from observation; use None if absent.
                    max_speed_mps=observation.get("max_speed_mps"),
                )

            # Iterate over a list built from key/value pairs from ldm.tracks, binding each item to (track_id,
            # track).
            for track_id, track in list(ldm.tracks.items()):
                # Run this branch when track_id differs from ego_id and the negation of track at 'is_observed'.
                if (
                    # Evaluate track_id differs from ego_id and the negation of track at 'is_observed' as part of
                    # the enclosing expression.
                    track_id != ego_id
                    # Evaluate the negation of track at 'is_observed' as part of the enclosing expression.
                    and not track["is_observed"]
                ):
                    # Call ldm.propagate_track with the supplied arguments.
                    ldm.propagate_track(
                        # Supply track_id to ldm.propagate_track.
                        track_id,
                        # Supply self.current_time to ldm.propagate_track.
                        self.current_time,
                    )

            # Call ldm.remove_stale_tracks with the supplied arguments.
            ldm.remove_stale_tracks(self.current_time)

    # Reset using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    def reset(self):
        # Clear the stored entries in self.ldms.
        self.ldms.clear()
        # Clear the stored entries in self.last_local_observations_by_ego.
        self.last_local_observations_by_ego.clear()
        # Set self.current_time to 0.0.
        self.current_time = 0.0
        # Call self.perception_interface.clear_diagnostics with the supplied arguments.
        self.perception_interface.clear_diagnostics()


# Set observation_manager to the result of ObservationManager().
observation_manager = ObservationManager()
