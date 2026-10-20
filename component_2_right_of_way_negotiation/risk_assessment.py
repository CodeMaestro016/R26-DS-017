"""Provisional approach-timing risk used by the legacy baseline.

This is no longer called TTC because it does not use map-defined path conflict
zones. It remains the control-facing legacy baseline while the separate
ConflictZoneOccupancyAssessor runs in shadow mode.
"""

# Import math for use in this module.
import math

# Import CONFIDENCE_RISK_WEIGHT, MAX_CONFIDENCE, TIMING_RISK_DECAY_SECONDS, TIMING_RISK_WEIGHT from config for the
# operations below.
from config import (
    CONFIDENCE_RISK_WEIGHT,
    MAX_CONFIDENCE,
    TIMING_RISK_DECAY_SECONDS,
    TIMING_RISK_WEIGHT,
)


# Define RiskAssessment to group the state and operations declared below.
# Instances expose the attributes and methods implemented in this class.
class RiskAssessment:
    # Initialize the instance attributes and collaborators used by the operations below.
    # Output: no explicit value; normal completion returns None.
    def __init__(self):
        # Set self.risk_data to an empty dictionary.
        self.risk_data = {}

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Eta to center using the inputs and processing steps below.
    # Input track: the supplied track.
    # Output: return the value selected by the matching return branch below.
    # Processing: select branches using the stated conditions.
    def _eta_to_center(track):
        # Set speed to a floating-point number built from 'speed' from track; use 0.0 if absent.
        speed = float(track.get("speed", 0.0))
        # Run this branch when speed is at most 0.1.
        if speed <= 0.1:
            # Return math.inf to the caller.
            return math.inf
        # Return a floating-point number built from track at 'distance_to_conflict' divided by speed to the
        # caller.
        return float(track["distance_to_conflict"]) / speed

    # Assess risk using the inputs and processing steps below.
    # Input ego_vehicle_id: the supplied ego vehicle id.
    # Input ldm: the supplied ldm.
    # Input current_time: the supplied current time.
    # Output: return the value selected by the matching return branch below.
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    def assess_risk(self, ego_vehicle_id, ldm, current_time):
        # Set ego_track to ego_vehicle_id from ldm.tracks; use None if absent.
        ego_track = ldm.tracks.get(ego_vehicle_id)
        # Run this branch when ego_track is the same object as None.
        if ego_track is None:
            # Set self.risk_data[ego_vehicle_id] to an empty dictionary.
            self.risk_data[ego_vehicle_id] = {}
            # Return an empty dictionary to the caller.
            return {}

        # Set ego_eta to the result of self._eta_to_center(ego_track).
        ego_eta = self._eta_to_center(ego_track)
        # Set risk_metrics to an empty dictionary.
        risk_metrics = {}

        # Iterate over key/value pairs from ldm.get_conflict_relevant_vehicles(), binding each item to (other_id,
        # other_track).
        for other_id, other_track in (
            # Evaluate key/value pairs from ldm.get_conflict_relevant_vehicles() as part of the enclosing
            # expression.
            ldm.get_conflict_relevant_vehicles().items()
        ):
            # Set other_eta to the result of self._eta_to_center(other_track).
            other_eta = self._eta_to_center(other_track)
            # Run this branch when the result of math.isinf(ego_eta) or the result of math.isinf(other_eta).
            if math.isinf(ego_eta) or math.isinf(other_eta):
                # Set arrival_time_gap to math.inf.
                arrival_time_gap = math.inf
                # Set timing_risk to 0.0.
                timing_risk = 0.0
            # Run this alternative branch when the preceding branch does not apply.
            else:
                # Set arrival_time_gap to the absolute value of ego_eta minus other_eta.
                arrival_time_gap = abs(ego_eta - other_eta)
                # Set timing_risk to the exponential of the negative of arrival_time_gap divided by
                # TIMING_RISK_DECAY_SECONDS.
                timing_risk = math.exp(
                    # Supply the negative of arrival_time_gap divided by TIMING_RISK_DECAY_SECONDS to math.exp.
                    -arrival_time_gap
                    # Evaluate TIMING_RISK_DECAY_SECONDS as part of the enclosing expression.
                    / TIMING_RISK_DECAY_SECONDS
                )

            # Set confidence to a floating-point number built from 'confidence' from other_track; use
            # MAX_CONFIDENCE if absent.
            confidence = float(
                # Supply 'confidence' from other_track; use MAX_CONFIDENCE if absent to float.
                other_track.get("confidence", MAX_CONFIDENCE)
            )
            # Set combined_risk to TIMING_RISK_WEIGHT multiplied by timing_risk plus CONFIDENCE_RISK_WEIGHT
            # multiplied by 1.0 minus confidence.
            combined_risk = (
                # Evaluate TIMING_RISK_WEIGHT multiplied by timing_risk plus CONFIDENCE_RISK_WEIGHT multiplied by
                # 1.0 minus confidence as part of the enclosing expression.
                TIMING_RISK_WEIGHT * timing_risk
                # Evaluate CONFIDENCE_RISK_WEIGHT multiplied by 1.0 minus confidence as part of the enclosing
                # expression.
                + CONFIDENCE_RISK_WEIGHT * (1.0 - confidence)
            )

            # Set risk_metrics[other_id] to a dictionary containing ego_eta_to_center, other_eta_to_center,
            # arrival_time_gap, confidence, timing_risk,...
            risk_metrics[other_id] = {
                # Store ego_eta under 'ego_eta_to_center'.
                "ego_eta_to_center": ego_eta,
                # Store other_eta under 'other_eta_to_center'.
                "other_eta_to_center": other_eta,
                # Store arrival_time_gap under 'arrival_time_gap'.
                "arrival_time_gap": arrival_time_gap,
                # Store confidence under 'confidence'.
                "confidence": confidence,
                # Store timing_risk under 'timing_risk'.
                "timing_risk": timing_risk,
                # Store the maximum of 0.0, the minimum of 1.0, combined_risk under 'combined_risk'.
                "combined_risk": max(
                    # Supply 0.0 to the enclosing expression.
                    0.0,
                    # Supply the minimum of 1.0, combined_risk to max.
                    min(1.0, combined_risk),
                ),
                # Store a floating-point number built from current_time under 'timestamp'.
                "timestamp": float(current_time),
                # Store True under 'provisional_center_based_metric'.
                "provisional_center_based_metric": True,
            }

        # Set self.risk_data[ego_vehicle_id] to risk_metrics.
        self.risk_data[ego_vehicle_id] = risk_metrics
        # Return risk_metrics to the caller.
        return risk_metrics

    # Get risk data using the inputs and processing steps below.
    # Input ego_vehicle_id: the supplied ego vehicle id.
    # Output: ego_vehicle_id from self.risk_data; use an empty dictionary if absent.
    def get_risk_data(self, ego_vehicle_id):
        # Return ego_vehicle_id from self.risk_data; use an empty dictionary if absent to the caller.
        return self.risk_data.get(ego_vehicle_id, {})

    # Reset using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    def reset(self):
        # Clear the stored entries in self.risk_data.
        self.risk_data.clear()


# Set risk_assessor to the result of RiskAssessment().
risk_assessor = RiskAssessment()
