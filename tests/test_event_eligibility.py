import sys
import unittest
from collections import deque
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from config import (APPROACH_ZONE_RADIUS, EVENT_ARMING_ETA_SECONDS,
                    MAX_APPROACH_SPEED, MODEL_OBSERVATION_WINDOW_SECONDS,
                    OBSERVATION_SAFETY_MARGIN, PRIMARY_PREDICTION_LEAD_TIME_SECONDS,
                    SENSOR_RANGE)
from conflict_entry_monitor import ConflictEntryMonitor
from predictor import IntentionPredictor


def history(count=50, interval=0.04):
    return deque(({"timestamp": i * interval, "position": (i * interval * 8.0, 0.0)}
                  for i in range(count)), maxlen=50)


def track(eta, count=50, observed=True):
    speed = 10.0
    return {"id": "target", "road_id": "w_in", "lane_position": 100.0 - eta * speed,
            "lane_length": 100.0, "speed": speed, "is_observed": observed,
            "last_observed_time": 0.0, "position_history": history(count),
            "position": (0.0, 0.0),
            "velocity_vector": (1.0, 0.0), "intention_prediction": None}


class FakePredictor:
    def __init__(self):
        self.calls = []

    def predict_stage(self, samples, stage):
        self.calls.append(stage)
        return {"predicted_class": "LEFT", "label": "LEFT", "confidence": 0.9,
                "threshold": 0.5, "accepted": True,
                "probabilities": {"LEFT": 0.9, "RIGHT": 0.05, "STRAIGHT": 0.05},
                "feature_diagnostics": {"maximum_absolute_z_score": 1.0,
                    "raw_feature_means": {name: 0.0 for name in ("speed", "acceleration_magnitude", "longitudinal_velocity", "lateral_velocity", "longitudinal_acceleration", "lateral_acceleration")},
                    "maximum_absolute_z_score_by_feature": {name: 1.0 for name in ("speed", "acceleration_magnitude", "longitudinal_velocity", "lateral_velocity", "longitudinal_acceleration", "lateral_acceleration")}}}

    fuse_stage_results = staticmethod(IntentionPredictor.fuse_stage_results)


class FakeLDM:
    ego_id = "ego"

    def __init__(self, target_track):
        self.tracks = {"ego": {"road_id": "s_in", "position": (0.0, 0.0)},
                       "target": target_track}

    def get_conflict_relevant_vehicles(self):
        return {"target": self.tracks["target"]}


class EligibilityTests(unittest.TestCase):
    def test_ranges_follow_contract(self):
        context = MODEL_OBSERVATION_WINDOW_SECONDS + PRIMARY_PREDICTION_LEAD_TIME_SECONDS
        self.assertAlmostEqual(APPROACH_ZONE_RADIUS, MAX_APPROACH_SPEED * context + OBSERVATION_SAFETY_MARGIN)
        self.assertAlmostEqual(SENSOR_RANGE, 2 * MAX_APPROACH_SPEED * context + OBSERVATION_SAFETY_MARGIN)
        self.assertEqual(EVENT_ARMING_ETA_SECONDS, 3.0)

    def test_event_not_created_before_arming_horizon(self):
        monitor = ConflictEntryMonitor()
        monitor.update_ldm(FakeLDM(track(3.01)), 0.0, FakePredictor())
        self.assertFalse(monitor.events)

    def test_event_arms_at_valid_context(self):
        monitor = ConflictEntryMonitor()
        monitor.update_ldm(FakeLDM(track(3.0)), 0.0, FakePredictor())
        self.assertEqual(len(monitor.events), 1)

    def test_first_observation_near_primary_runs(self):
        monitor, predictor = ConflictEntryMonitor(), FakePredictor()
        monitor.update_ldm(FakeLDM(track(0.98)), 0.0, predictor)
        event = next(iter(monitor.events.values()))
        self.assertTrue(event["primary_model_executed"])
        self.assertEqual(predictor.calls, ["primary"])

    def test_first_observation_far_below_primary_is_late(self):
        monitor = ConflictEntryMonitor()
        monitor.update_ldm(FakeLDM(track(0.7)), 0.0, FakePredictor())
        event = next(iter(monitor.events.values()))
        self.assertEqual(event["primary_stage_status"], "MISSED_LATE_FIRST_OBSERVATION")

    def test_unobserved_and_49_samples_do_not_execute(self):
        for item in (track(0.98, observed=False), track(0.98, count=49)):
            monitor, predictor = ConflictEntryMonitor(), FakePredictor()
            # Arm while observed, then directly exercise the reached-stage contract.
            item["is_observed"] = True
            event = monitor._new_event("ego", "target", item, 0.0)
            item["is_observed"] = False if len(item["position_history"]) == 50 else True
            monitor._record_stage(event, "primary", item, 0.0, 0.98, 9.8, predictor)
            self.assertFalse(event["primary_model_executed"])
            self.assertEqual(predictor.calls, [])

    def test_each_stage_executes_at_most_once(self):
        monitor, predictor = ConflictEntryMonitor(), FakePredictor()
        ldm = FakeLDM(track(0.98))
        monitor.update_ldm(ldm, 0.0, predictor)
        monitor.update_ldm(ldm, 0.04, predictor)
        self.assertEqual(predictor.calls.count("primary"), 1)

    def test_track_lost_before_primary_is_cancelled(self):
        monitor, predictor = ConflictEntryMonitor(), FakePredictor()
        ldm = FakeLDM(track(3.0))
        monitor.update_ldm(ldm, 0.0, predictor)
        del ldm.tracks["target"]
        completed = monitor.update_ldm(ldm, 0.04, predictor)
        self.assertEqual(completed[0]["event_category"], "CANCELLED_BEFORE_PRIMARY")
        self.assertIsNone(completed[0]["primary_history_count_at_trigger"])

    def test_route_truth_does_not_change_timing_or_features(self):
        left, right = track(3.0), track(3.0)
        self.assertEqual(ConflictEntryMonitor.distance_to_conflict_entry(left),
                         ConflictEntryMonitor.distance_to_conflict_entry(right))
        self.assertEqual(IntentionPredictor.build_causal_features(left["position_history"]).tolist(),
                         IntentionPredictor.build_causal_features(right["position_history"]).tolist())

    def test_route_truth_is_supplied_only_through_evaluation_channel(self):
        monitor = ConflictEntryMonitor()
        ldm = FakeLDM(track(3.0))
        monitor.update_ldm(
            ldm, 0.0, FakePredictor(),
            evaluation_route_truth={"target": "route_w_left"},
        )
        event = next(iter(monitor.events.values()))
        self.assertEqual(event["ground_truth_route_id"], "route_w_left")
        self.assertNotIn("route_id", ldm.tracks["target"])
        self.assertNotIn("ground_truth_route_id", ldm.tracks["target"])

    def test_both_missing_fusion_status(self):
        self.assertEqual(IntentionPredictor.fuse_stage_results(None, None),
                         ("UNKNOWN", "BOTH_STAGES_MISSING"))


if __name__ == "__main__":
    unittest.main()
