# Import sys for use in this module.
import sys
# Import unittest for use in this module.
import unittest
# Import deque from collections for the operations below.
from collections import deque
# Import Path from pathlib for the operations below.
from pathlib import Path

# Set PROJECT_ROOT to Path(__file__).resolve().parents at 1.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
# Call sys.path.insert with the supplied arguments.
sys.path.insert(0, str(PROJECT_ROOT))

# Import APPROACH_ZONE_RADIUS, EVENT_ARMING_ETA_SECONDS, MAX_APPROACH_SPEED, MODEL_OBSERVATION_WINDOW_SECONDS,
# OBSERVATION_SAFETY_MARGIN, PRIMARY_PREDICTION_LEAD_TIME_SECONDS,... from config for the operations below.
from config import (APPROACH_ZONE_RADIUS, EVENT_ARMING_ETA_SECONDS,
                    MAX_APPROACH_SPEED, MODEL_OBSERVATION_WINDOW_SECONDS,
                    OBSERVATION_SAFETY_MARGIN, PRIMARY_PREDICTION_LEAD_TIME_SECONDS,
                    MIN_REQUIRED_OBSERVATION_RANGE_METERS, SENSOR_RANGE)
# Import ConflictEntryMonitor from conflict_entry_monitor for the operations below.
from conflict_entry_monitor import ConflictEntryMonitor
# Import IntentionPredictor from predictor for the operations below.
from predictor import IntentionPredictor


# History using the inputs and processing steps below.
# Input count: the supplied count.
# Input interval: the supplied interval.
# Output: the result of deque(a lazy sequence of a dictionary containing timestamp, position for i in the integer
# range...).
def history(count=50, interval=0.04):
    # Return the result of deque(a lazy sequence of a dictionary containing timestamp, position for i in the
    # integer range...) to the caller.
    return deque(({"timestamp": i * interval, "position": (i * interval * 8.0, 0.0)}
                  # Supply maxlen as 50.
                  for i in range(count)), maxlen=50)


# Track using the inputs and processing steps below.
# Input eta: the supplied eta.
# Input count: the supplied count.
# Input observed: the supplied observed.
# Output: a dictionary containing id, road_id, lane_position, lane_length, speed, is_observed,
# last_observed_time,...
def track(eta, count=50, observed=True):
    # Set speed to 10.0.
    speed = 10.0
    # Return a dictionary containing id, road_id, lane_position, lane_length, speed, is_observed,
    # last_observed_time,... to the caller.
    return {"id": "target", "road_id": "w_in", "lane_position": 100.0 - eta * speed,
            # Store 100.0 under 'lane_length'.
            # Store speed under 'speed'.
            # Store observed under 'is_observed'.
            "lane_length": 100.0, "speed": speed, "is_observed": observed,
            # Store 0.0 under 'last_observed_time'.
            # Store the result of history(count) under 'position_history'.
            "last_observed_time": 0.0, "position_history": history(count),
            # Store a tuple containing 0.0, 0.0 under 'position'.
            "position": (0.0, 0.0),
            # Store a tuple containing 1.0, 0.0 under 'velocity_vector'.
            # Store None under 'intention_prediction'.
            "velocity_vector": (1.0, 0.0), "intention_prediction": None}


# Define FakePredictor to group the state and operations declared below.
# Instances expose the attributes and methods implemented in this class.
class FakePredictor:
    # Initialize the instance attributes and collaborators used by the operations below.
    # Output: no explicit value; normal completion returns None.
    def __init__(self):
        # Set self.calls to an empty list.
        self.calls = []

    # Predict stage using the inputs and processing steps below.
    # Input samples: the supplied samples.
    # Input stage: the supplied stage.
    # Output: a dictionary containing predicted_class, label, confidence, threshold, accepted, probabilities,...
    def predict_stage(self, samples, stage):
        # Append stage to self.calls.
        self.calls.append(stage)
        # Return a dictionary containing predicted_class, label, confidence, threshold, accepted,
        # probabilities,... to the caller.
        return {"predicted_class": "LEFT", "label": "LEFT", "confidence": 0.9,
                # Store 0.5 under 'threshold'.
                # Store True under 'accepted'.
                "threshold": 0.5, "accepted": True,
                # Store a dictionary containing LEFT, RIGHT, STRAIGHT under 'probabilities'.
                # Store 0.9 under 'LEFT'.
                # Store 0.05 under 'RIGHT'.
                # Store 0.05 under 'STRAIGHT'.
                "probabilities": {"LEFT": 0.9, "RIGHT": 0.05, "STRAIGHT": 0.05},
                # Store a dictionary containing maximum_absolute_z_score, raw_feature_means,
                # maximum_absolute_z_score_by_feature under 'feature_diagnostics'.
                # Store 1.0 under 'maximum_absolute_z_score'.
                "feature_diagnostics": {"maximum_absolute_z_score": 1.0,
                    # Store a dictionary of name mapped to 0.0 for name in a tuple containing the text 'speed',
                    # the text 'acceleration_magnitude', the text 'longitudinal_velocity', the text... under
                    # 'raw_feature_means'.
                    "raw_feature_means": {name: 0.0 for name in ("speed", "acceleration_magnitude", "longitudinal_velocity", "lateral_velocity", "longitudinal_acceleration", "lateral_acceleration")},
                    # Store a dictionary of name mapped to 1.0 for name in a tuple containing the text 'speed',
                    # the text 'acceleration_magnitude', the text 'longitudinal_velocity', the text... under
                    # 'maximum_absolute_z_score_by_feature'.
                    "maximum_absolute_z_score_by_feature": {name: 1.0 for name in ("speed", "acceleration_magnitude", "longitudinal_velocity", "lateral_velocity", "longitudinal_acceleration", "lateral_acceleration")}}}

    # Set fuse_stage_results to the result of staticmethod(IntentionPredictor.fuse_stage_results).
    fuse_stage_results = staticmethod(IntentionPredictor.fuse_stage_results)


# Define FakeLDM to group the state and operations declared below.
# Instances expose the attributes and methods implemented in this class.
class FakeLDM:
    # Set ego_id to the text 'ego'.
    ego_id = "ego"

    # Initialize the instance attributes and collaborators used by the operations below.
    # Input target_track: the supplied target track.
    # Output: no explicit value; normal completion returns None.
    def __init__(self, target_track):
        # Set self.tracks to a dictionary containing ego, target.
        self.tracks = {"ego": {"road_id": "s_in", "position": (0.0, 0.0)},
                       # Store target_track under 'target'.
                       "target": target_track}

    # Get conflict relevant vehicles using the inputs and processing steps below.
    # Output: a dictionary containing target.
    def get_conflict_relevant_vehicles(self):
        # Return a dictionary containing target to the caller.
        return {"target": self.tracks["target"]}


# Define EligibilityTests to group the state and operations declared below.
# Base classes: unittest.TestCase.
# Instances expose the attributes and methods implemented in this class.
class EligibilityTests(unittest.TestCase):
    # Check ranges follow contract using the setup, calls, and assertions below.
    # Output: no explicit value; normal completion returns None.
    def test_ranges_follow_contract(self):
        # Set context to MODEL_OBSERVATION_WINDOW_SECONDS plus PRIMARY_PREDICTION_LEAD_TIME_SECONDS.
        context = MODEL_OBSERVATION_WINDOW_SECONDS + PRIMARY_PREDICTION_LEAD_TIME_SECONDS
        # Call self.assertAlmostEqual with the supplied arguments.
        self.assertAlmostEqual(APPROACH_ZONE_RADIUS, MAX_APPROACH_SPEED * context + OBSERVATION_SAFETY_MARGIN)
        # Call self.assertAlmostEqual with the supplied arguments.
        self.assertAlmostEqual(MIN_REQUIRED_OBSERVATION_RANGE_METERS, 2 * MAX_APPROACH_SPEED * context + OBSERVATION_SAFETY_MARGIN)
        # Call self.assertEqual with the supplied arguments.
        self.assertEqual(SENSOR_RANGE, 160.0)
        # Call self.assertEqual with the supplied arguments.
        self.assertEqual(EVENT_ARMING_ETA_SECONDS, 3.0)

    # Check event not created before arming horizon using the setup, calls, and assertions below.
    # Output: no explicit value; normal completion returns None.
    def test_event_not_created_before_arming_horizon(self):
        # Set monitor to the result of ConflictEntryMonitor().
        monitor = ConflictEntryMonitor()
        # Call monitor.update_ldm with the supplied arguments.
        monitor.update_ldm(FakeLDM(track(3.01)), 0.0, FakePredictor())
        # Call self.assertFalse with the supplied arguments.
        self.assertFalse(monitor.events)

    # Check event arms at valid context using the setup, calls, and assertions below.
    # Output: no explicit value; normal completion returns None.
    def test_event_arms_at_valid_context(self):
        # Set monitor to the result of ConflictEntryMonitor().
        monitor = ConflictEntryMonitor()
        # Call monitor.update_ldm with the supplied arguments.
        monitor.update_ldm(FakeLDM(track(3.0)), 0.0, FakePredictor())
        # Call self.assertEqual with the supplied arguments.
        self.assertEqual(len(monitor.events), 1)

    # Check first observation near primary runs using the setup, calls, and assertions below.
    # Output: no explicit value; normal completion returns None.
    def test_first_observation_near_primary_runs(self):
        # Set (monitor, predictor) to a tuple containing the result of ConflictEntryMonitor(), the result of
        # FakePredictor().
        monitor, predictor = ConflictEntryMonitor(), FakePredictor()
        # Call monitor.update_ldm with the supplied arguments.
        monitor.update_ldm(FakeLDM(track(0.98)), 0.0, predictor)
        # Set event to the next item from the result of iter(values from monitor.events).
        event = next(iter(monitor.events.values()))
        # Call self.assertTrue with the supplied arguments.
        self.assertTrue(event["primary_model_executed"])
        # Call self.assertEqual with the supplied arguments.
        self.assertEqual(predictor.calls, ["primary"])

    # Check first observation far below primary is late using the setup, calls, and assertions below.
    # Output: no explicit value; normal completion returns None.
    def test_first_observation_far_below_primary_is_late(self):
        # Set monitor to the result of ConflictEntryMonitor().
        monitor = ConflictEntryMonitor()
        # Call monitor.update_ldm with the supplied arguments.
        monitor.update_ldm(FakeLDM(track(0.7)), 0.0, FakePredictor())
        # Set event to the next item from the result of iter(values from monitor.events).
        event = next(iter(monitor.events.values()))
        # Call self.assertEqual with the supplied arguments.
        self.assertEqual(event["primary_stage_status"], "MISSED_LATE_FIRST_OBSERVATION")

    # Check unobserved and 49 samples do not execute using the setup, calls, and assertions below.
    # Output: no explicit value; normal completion returns None.
    # Processing: iterate over the relevant records.
    def test_unobserved_and_49_samples_do_not_execute(self):
        # Iterate over a tuple containing the result of track(0.98), the result of track(0.98), binding each item
        # to item.
        for item in (track(0.98, observed=False), track(0.98, count=49)):
            # Set (monitor, predictor) to a tuple containing the result of ConflictEntryMonitor(), the result of
            # FakePredictor().
            monitor, predictor = ConflictEntryMonitor(), FakePredictor()
            # Arm while observed, then directly exercise the reached-stage contract.
            # Set item['is_observed'] to True.
            item["is_observed"] = True
            # Set event to the result of monitor._new_event(the text 'ego', the text 'target', item, 0.0).
            event = monitor._new_event("ego", "target", item, 0.0)
            # Set item['is_observed'] to False when the number of entries in item at 'position_history' equals 50,
            # otherwise True.
            item["is_observed"] = False if len(item["position_history"]) == 50 else True
            # Call monitor._record_stage with the supplied arguments.
            monitor._record_stage(event, "primary", item, 0.0, 0.98, 9.8, predictor)
            # Call self.assertFalse with the supplied arguments.
            self.assertFalse(event["primary_model_executed"])
            # Call self.assertEqual with the supplied arguments.
            self.assertEqual(predictor.calls, [])

    # Check each stage executes at most once using the setup, calls, and assertions below.
    # Output: no explicit value; normal completion returns None.
    def test_each_stage_executes_at_most_once(self):
        # Set (monitor, predictor) to a tuple containing the result of ConflictEntryMonitor(), the result of
        # FakePredictor().
        monitor, predictor = ConflictEntryMonitor(), FakePredictor()
        # Set ldm to the result of FakeLDM(the result of track(0.98)).
        ldm = FakeLDM(track(0.98))
        # Call monitor.update_ldm with the supplied arguments.
        monitor.update_ldm(ldm, 0.0, predictor)
        # Call monitor.update_ldm with the supplied arguments.
        monitor.update_ldm(ldm, 0.04, predictor)
        # Call self.assertEqual with the supplied arguments.
        self.assertEqual(predictor.calls.count("primary"), 1)

    # Check track lost before primary is cancelled using the setup, calls, and assertions below.
    # Output: no explicit value; normal completion returns None.
    def test_track_lost_before_primary_is_cancelled(self):
        # Set (monitor, predictor) to a tuple containing the result of ConflictEntryMonitor(), the result of
        # FakePredictor().
        monitor, predictor = ConflictEntryMonitor(), FakePredictor()
        # Set ldm to the result of FakeLDM(the result of track(3.0)).
        ldm = FakeLDM(track(3.0))
        # Call monitor.update_ldm with the supplied arguments.
        monitor.update_ldm(ldm, 0.0, predictor)
        # Delete ldm.tracks['target'] from its containing namespace or collection.
        del ldm.tracks["target"]
        # Set completed to the result of monitor.update_ldm(ldm, 0.04, predictor).
        completed = monitor.update_ldm(ldm, 0.04, predictor)
        # Call self.assertEqual with the supplied arguments.
        self.assertEqual(completed[0]["event_category"], "CANCELLED_BEFORE_PRIMARY")
        # Call self.assertIsNone with the supplied arguments.
        self.assertIsNone(completed[0]["primary_history_count_at_trigger"])

    # Check route truth does not change timing or features using the setup, calls, and assertions below.
    # Output: no explicit value; normal completion returns None.
    def test_route_truth_does_not_change_timing_or_features(self):
        # Set (left, right) to a tuple containing the result of track(3.0), the result of track(3.0).
        left, right = track(3.0), track(3.0)
        # Call self.assertEqual with the supplied arguments.
        self.assertEqual(ConflictEntryMonitor.distance_to_conflict_entry(left),
                         # Supply the result of ConflictEntryMonitor.distance_to_conflict_entry(right) to
                         # self.assertEqual.
                         ConflictEntryMonitor.distance_to_conflict_entry(right))
        # Call self.assertEqual with the supplied arguments.
        self.assertEqual(IntentionPredictor.build_causal_features(left["position_history"]).tolist(),
                         # Supply the result of
                         # IntentionPredictor.build_causal_features(right['position_history']).tolist() to
                         # self.assertEqual.
                         IntentionPredictor.build_causal_features(right["position_history"]).tolist())

    # Check route truth is supplied only through evaluation channel using the setup, calls, and assertions below.
    # Output: no explicit value; normal completion returns None.
    def test_route_truth_is_supplied_only_through_evaluation_channel(self):
        # Set monitor to the result of ConflictEntryMonitor().
        monitor = ConflictEntryMonitor()
        # Set ldm to the result of FakeLDM(the result of track(3.0)).
        ldm = FakeLDM(track(3.0))
        # Call monitor.update_ldm with the supplied arguments.
        monitor.update_ldm(
            # Supply the result of FakePredictor() to monitor.update_ldm.
            ldm, 0.0, FakePredictor(),
            # Store the text 'route_w_left' under 'target'.
            evaluation_route_truth={"target": "route_w_left"},
        )
        # Set event to the next item from the result of iter(values from monitor.events).
        event = next(iter(monitor.events.values()))
        # Call self.assertEqual with the supplied arguments.
        self.assertEqual(event["ground_truth_route_id"], "route_w_left")
        # Call self.assertNotIn with the supplied arguments.
        self.assertNotIn("route_id", ldm.tracks["target"])
        # Call self.assertNotIn with the supplied arguments.
        self.assertNotIn("ground_truth_route_id", ldm.tracks["target"])

    # Check both missing fusion status using the setup, calls, and assertions below.
    # Output: no explicit value; normal completion returns None.
    def test_both_missing_fusion_status(self):
        # Call self.assertEqual with the supplied arguments.
        self.assertEqual(IntentionPredictor.fuse_stage_results(None, None),
                         # Supply a tuple containing the text 'UNKNOWN', the text 'BOTH_STAGES_MISSING' to
                         # self.assertEqual.
                         ("UNKNOWN", "BOTH_STAGES_MISSING"))


# Run this branch when __name__ equals the text '__main__'.
if __name__ == "__main__":
    # Call unittest.main with the supplied arguments.
    unittest.main()
