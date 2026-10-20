"""Tests for read-only intention-prediction evidence and presentation data."""

# Import json for use in this module.
import json
# Import inspect for use in this module.
import inspect
# Import SimpleNamespace from types for the operations below.
from types import SimpleNamespace

# Import pytest for use in this module.
import pytest

# Import ConflictEntryMonitor from conflict_entry_monitor for the operations below.
from conflict_entry_monitor import ConflictEntryMonitor
# Import HTML from debug_dashboard for the operations below.
from debug_dashboard import HTML
# Import prediction_record_snapshot, _prediction_sections from debug_evidence for the operations below.
from debug_evidence import prediction_record_snapshot, _prediction_sections
# Import FEATURE_DIAGNOSTIC_NAMES, IntentionPredictor from predictor for the operations below.
from predictor import FEATURE_DIAGNOSTIC_NAMES, IntentionPredictor
# Import FakeLDM, FakePredictor, track from tests.test_event_eligibility for the operations below.
from tests.test_event_eligibility import FakeLDM, FakePredictor, track


# Define Manager to group the state and operations declared below.
# Instances expose the attributes and methods implemented in this class.
class Manager:
    # Initialize the instance attributes and collaborators used by the operations below.
    # Input ldm: the supplied ldm.
    # Output: no explicit value; normal completion returns None.
    def __init__(self, ldm):
        # Set self.ldms to a dictionary of the supplied entries.
        self.ldms = {ldm.ego_id: ldm}


# Check active event snapshots are defensive and hide route truth using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_active_event_snapshots_are_defensive_and_hide_route_truth():
    # Set monitor to the result of ConflictEntryMonitor().
    monitor = ConflictEntryMonitor()
    # Set ldm to the result of FakeLDM(the result of track(3.0)).
    ldm = FakeLDM(track(3.0))
    # Call monitor.update_ldm with the supplied arguments.
    monitor.update_ldm(ldm, 0.0, FakePredictor(),
                       # Store the text 'route_w_left' under 'target'.
                       evaluation_route_truth={"target": "route_w_left"})
    # Set snapshot to the result of monitor.get_active_event_snapshots(the text 'ego').
    snapshot = monitor.get_active_event_snapshots("ego")
    # Require the text 'ground_truth_route_id' does not belong to the serialized data produced by json.dumps;
    # otherwise raise AssertionError.
    assert "ground_truth_route_id" not in json.dumps(snapshot)
    # Set snapshot['target']['latest_history_count'] to the negative of 1.
    snapshot["target"]["latest_history_count"] = -1
    # Require next(iter(monitor.events.values())) at 'latest_history_count' equals 50; otherwise raise
    # AssertionError.
    assert next(iter(monitor.events.values()))["latest_history_count"] == 50


# Check stage probabilities threshold acceptance and fusion are preserved using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_stage_probabilities_threshold_acceptance_and_fusion_are_preserved():
    # Set primary to a dictionary containing probabilities, predicted_class, confidence, threshold, accepted,
    # label.
    primary = {"probabilities": {"LEFT": .72, "RIGHT": .18, "STRAIGHT": .10},
               # Store the text 'LEFT' under 'predicted_class'.
               # Store 0.72 under 'confidence'.
               "predicted_class": "LEFT", "confidence": .72,
               # Store 0.436763 under 'threshold'.
               # Store True under 'accepted'.
               # Store the text 'LEFT' under 'label'.
               "threshold": .436763, "accepted": True, "label": "LEFT"}
    # Set secondary to a dictionary containing probabilities, predicted_class, confidence, threshold, accepted,
    # label.
    secondary = {"probabilities": {"LEFT": .8, "RIGHT": .1, "STRAIGHT": .1},
                 # Store the text 'LEFT' under 'predicted_class'.
                 # Store 0.8 under 'confidence'.
                 "predicted_class": "LEFT", "confidence": .8,
                 # Store 0.38727 under 'threshold'.
                 # Store True under 'accepted'.
                 # Store the text 'LEFT' under 'label'.
                 "threshold": .387270, "accepted": True, "label": "LEFT"}
    # Set (label, status) to the result of IntentionPredictor.fuse_stage_results(primary, secondary).
    label, status = IntentionPredictor.fuse_stage_results(primary, secondary)
    # Set record to the result of prediction_record_snapshot(a dictionary containing primary, secondary,
    # fused_label, status, ground_truth_route_id).
    record = prediction_record_snapshot({
        # Store primary under 'primary'.
        # Store secondary under 'secondary'.
        "primary": primary, "secondary": secondary,
        # Store label under 'fused_label'.
        # Store status under 'status'.
        "fused_label": label, "status": status,
        "ground_truth_route_id": "secret",
    })
    # Require record at 'primary' equals primary; otherwise raise AssertionError.
    assert record["primary"] == primary
    # Require record at 'secondary' equals secondary; otherwise raise AssertionError.
    assert record["secondary"] == secondary
    # Require a tuple containing record at 'fused_label', record at 'status' equals a tuple containing the text
    # 'LEFT', the text 'CONFIRMED_AGREEMENT'; otherwise raise AssertionError.
    assert (record["fused_label"], record["status"]) == (
        "LEFT", "CONFIRMED_AGREEMENT")
    # Require the text 'secret' does not belong to the serialized data produced by json.dumps; otherwise raise
    # AssertionError.
    assert "secret" not in json.dumps(record)


# Check pipeline readiness uses 50 samples and current monitor state using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_pipeline_readiness_uses_50_samples_and_current_monitor_state():
    # Set (monitor, predictor) to a tuple containing the result of ConflictEntryMonitor(), the result of
    # FakePredictor().
    monitor, predictor = ConflictEntryMonitor(), FakePredictor()
    # Set ldm to the result of FakeLDM(the result of track(0.98)).
    ldm = FakeLDM(track(0.98))
    # Call monitor.update_ldm with the supplied arguments.
    monitor.update_ldm(ldm, 7.0, predictor)
    # Set (events, pipelines, config) to the result of _prediction_sections(the result of Manager(ldm), monitor,
    # the result of SimpleNamespace()).
    events, pipelines, config = _prediction_sections(
        # Supply the result of SimpleNamespace() to _prediction_sections.
        Manager(ldm), monitor, SimpleNamespace(
            # Supply primary_threshold as 0.436.
            # Supply secondary_threshold as 0.387.
            primary_threshold=.436, secondary_threshold=.387))
    # Set card to pipelines['ego'] at 0.
    card = pipelines["ego"][0]
    # Require card at 'required_history_count' equals 50; otherwise raise AssertionError.
    assert card["required_history_count"] == 50
    # Require card at 'history_ready' is the same object as True; otherwise raise AssertionError.
    assert card["history_ready"] is True
    # Require card['event'] at 'primary_model_executed' is the same object as True; otherwise raise
    # AssertionError.
    assert card["event"]["primary_model_executed"] is True
    # Require card['event']['primary'] at 'accepted' is the same object as True; otherwise raise AssertionError.
    assert card["event"]["primary"]["accepted"] is True
    # Require events['ego']['target'] at 'latest_estimated_eta' equals the result of pytest.approx(0.98);
    # otherwise raise AssertionError.
    assert events["ego"]["target"]["latest_estimated_eta"] == pytest.approx(.98)
    # Call json.dumps with the supplied arguments.
    json.dumps({"events": events, "pipelines": pipelines, "config": config},
               # Supply allow_nan as False.
               allow_nan=False)


# Check incomplete unobserved and departed targets are represented safely using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_incomplete_unobserved_and_departed_targets_are_represented_safely():
    # Set monitor to the result of ConflictEntryMonitor().
    monitor = ConflictEntryMonitor()
    # Set incomplete to the result of FakeLDM(the result of track(4.2)).
    incomplete = FakeLDM(track(4.2, count=32, observed=False))
    # Set (_, pipelines, _) to the result of _prediction_sections(the result of Manager(incomplete), monitor,
    # None).
    _, pipelines, _ = _prediction_sections(Manager(incomplete), monitor, None)
    # Set card to pipelines['ego'] at 0.
    card = pipelines["ego"][0]
    # Require card at 'history_ready' is the same object as False; otherwise raise AssertionError.
    assert card["history_ready"] is False
    # Require card at 'is_observed' is the same object as False; otherwise raise AssertionError.
    assert card["is_observed"] is False
    # Require card at 'event_state' equals the text 'NOT_ARMED'; otherwise raise AssertionError.
    assert card["event_state"] == "NOT_ARMED"
    # Delete incomplete.tracks['target'] from its containing namespace or collection.
    del incomplete.tracks["target"]
    # Set (_, pipelines, _) to the result of _prediction_sections(the result of Manager(incomplete), monitor,
    # None).
    _, pipelines, _ = _prediction_sections(Manager(incomplete), monitor, None)
    # Require pipelines at 'ego' equals an empty list; otherwise raise AssertionError.
    assert pipelines["ego"] == []


# Check feature order and confidence separation match runtime contract using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_feature_order_and_confidence_separation_match_runtime_contract():
    # Require FEATURE_DIAGNOSTIC_NAMES equals a tuple containing the text 'speed', the text
    # 'acceleration_magnitude', the text 'longitudinal_velocity', the text...; otherwise raise AssertionError.
    assert FEATURE_DIAGNOSTIC_NAMES == (
        "speed", "acceleration_magnitude", "longitudinal_velocity",
        "lateral_velocity", "longitudinal_acceleration",
        "lateral_acceleration",
    )
    # Set (_, _, config) to the result of _prediction_sections(the result of Manager(the result of FakeLDM(the
    # result of track(3.0))), the result of...).
    _, _, config = _prediction_sections(
        # Supply the result of Manager(the result of FakeLDM(the result of track(3.0))) to _prediction_sections.
        Manager(FakeLDM(track(3.0))), ConflictEntryMonitor(), None)
    # Require config at 'feature_names' equals a list built from FEATURE_DIAGNOSTIC_NAMES; otherwise raise
    # AssertionError.
    assert config["feature_names"] == list(FEATURE_DIAGNOSTIC_NAMES)
    # Require config at 'ldm_confidence_is_gru_input' is the same object as False; otherwise raise AssertionError.
    assert config["ldm_confidence_is_gru_input"] is False
    # Require the text 'LDM confidence is NOT a GRU input' belongs to HTML; otherwise raise AssertionError.
    assert "LDM confidence is NOT a GRU input" in HTML
    # Require the text 'ldm_confidence' does not belong to
    # IntentionPredictor.build_causal_features.__code__.co_names; otherwise raise AssertionError.
    assert "ldm_confidence" not in IntentionPredictor.build_causal_features.__code__.co_names


# Check dashboard supports all requested prediction states using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def test_dashboard_supports_all_requested_prediction_states():
    # Iterate over a tuple containing the text 'id="predictionOverview"', the text 'id="readiness"', the text
    # 'id="predictionTiming"', the text..., binding each item to text.
    for text in ('id="predictionOverview"', 'id="readiness"',
                 'id="predictionTiming"', 'id="modelInput"',
                 "Primary Prediction", "Secondary Prediction",
                 "Final Intention Fusion", "WAITING_FOR_FINALIZATION"):
        # Require text belongs to HTML; otherwise raise AssertionError.
        assert text in HTML


# Check main writes one evidence record after current step monitor update using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_main_writes_one_evidence_record_after_current_step_monitor_update():
    # Import main for use in this module.
    import main
    # Set source to the result of inspect.getsource(main.main).
    source = inspect.getsource(main.main)
    # Set monitor_update to the result of source.index(the text 'conflict_entry_monitor.update_ldm').
    monitor_update = source.index("conflict_entry_monitor.update_ldm")
    # Set evidence_build to the result of source.index(the text 'evidence_snapshot = build_evidence_snapshot').
    evidence_build = source.index("evidence_snapshot = build_evidence_snapshot")
    # Set evidence_write to the result of source.index(the text 'evidence_writer.write(evidence_snapshot)').
    evidence_write = source.index("evidence_writer.write(evidence_snapshot)")
    # Require monitor_update is less than evidence_build; is less than evidence_write; otherwise raise
    # AssertionError.
    assert monitor_update < evidence_build < evidence_write
    # Require the result of source.count(the text 'evidence_writer.write(evidence_snapshot)') equals 1; otherwise
    # raise AssertionError.
    assert source.count("evidence_writer.write(evidence_snapshot)") == 1
