"""Provisional approach-timing risk used by the legacy baseline.

This is no longer called TTC because it does not yet use map-defined path
conflict zones. The next project stage should replace this module with a true
map-aware conflict manager.
"""

import math

from config import (
    CONFIDENCE_RISK_WEIGHT,
    MAX_CONFIDENCE,
    TIMING_RISK_DECAY_SECONDS,
    TIMING_RISK_WEIGHT,
)


class RiskAssessment:
    def __init__(self):
        self.risk_data = {}

    @staticmethod
    def _eta_to_center(track):
        speed = float(track.get("speed", 0.0))
        if speed <= 0.1:
            return math.inf
        return float(track["distance_to_conflict"]) / speed

    def assess_risk(self, ego_vehicle_id, ldm, current_time):
        ego_track = ldm.tracks.get(ego_vehicle_id)
        if ego_track is None:
            self.risk_data[ego_vehicle_id] = {}
            return {}

        ego_eta = self._eta_to_center(ego_track)
        risk_metrics = {}

        for other_id, other_track in (
            ldm.get_conflict_relevant_vehicles().items()
        ):
            other_eta = self._eta_to_center(other_track)
            if math.isinf(ego_eta) or math.isinf(other_eta):
                arrival_time_gap = math.inf
                timing_risk = 0.0
            else:
                arrival_time_gap = abs(ego_eta - other_eta)
                timing_risk = math.exp(
                    -arrival_time_gap
                    / TIMING_RISK_DECAY_SECONDS
                )

            confidence = float(
                other_track.get("confidence", MAX_CONFIDENCE)
            )
            combined_risk = (
                TIMING_RISK_WEIGHT * timing_risk
                + CONFIDENCE_RISK_WEIGHT * (1.0 - confidence)
            )

            risk_metrics[other_id] = {
                "ego_eta_to_center": ego_eta,
                "other_eta_to_center": other_eta,
                "arrival_time_gap": arrival_time_gap,
                "confidence": confidence,
                "timing_risk": timing_risk,
                "combined_risk": max(
                    0.0,
                    min(1.0, combined_risk),
                ),
                "timestamp": float(current_time),
                "provisional_center_based_metric": True,
            }

        self.risk_data[ego_vehicle_id] = risk_metrics
        return risk_metrics

    def get_risk_data(self, ego_vehicle_id):
        return self.risk_data.get(ego_vehicle_id, {})

    def reset(self):
        self.risk_data.clear()


risk_assessor = RiskAssessment()
