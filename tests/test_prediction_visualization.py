"""Tests for read-only intention-prediction evidence and presentation data."""

import json
import inspect
from types import SimpleNamespace

import pytest

from conflict_entry_monitor import ConflictEntryMonitor
from debug_dashboard import HTML
from debug_evidence import prediction_record_snapshot, _prediction_sections
from predictor import FEATURE_DIAGNOSTIC_NAMES, IntentionPredictor
from tests.test_event_eligibility import FakeLDM, FakePredictor, track


class Manager:
    def __init__(self, ldm):
        self.ldms = {ldm.ego_id: ldm}


def test_active_event_snapshots_are_defensive_and_hide_route_truth():
    monitor = ConflictEntryMonitor()
    ldm = FakeLDM(track(3.0))
    monitor.update_ldm(ldm, 0.0, FakePredictor(),
                       evaluation_route_truth={"target": "route_w_left"})
    snapshot = monitor.get_active_event_snapshots("ego")
    assert "ground_truth_route_id" not in json.dumps(snapshot)
    snapshot["target"]["latest_history_count"] = -1
    assert next(iter(monitor.events.values()))["latest_history_count"] == 50


def test_stage_probabilities_threshold_acceptance_and_fusion_are_preserved():
    primary = {"probabilities": {"LEFT": .72, "RIGHT": .18, "STRAIGHT": .10},
               "predicted_class": "LEFT", "confidence": .72,
               "threshold": .436763, "accepted": True, "label": "LEFT"}
    secondary = {"probabilities": {"LEFT": .8, "RIGHT": .1, "STRAIGHT": .1},
                 "predicted_class": "LEFT", "confidence": .8,
                 "threshold": .387270, "accepted": True, "label": "LEFT"}
    label, status = IntentionPredictor.fuse_stage_results(primary, secondary)
    record = prediction_record_snapshot({
        "primary": primary, "secondary": secondary,
        "fused_label": label, "status": status,
        "ground_truth_route_id": "secret",
    })
    assert record["primary"] == primary
    assert record["secondary"] == secondary
    assert (record["fused_label"], record["status"]) == (
        "LEFT", "CONFIRMED_AGREEMENT")
    assert "secret" not in json.dumps(record)


def test_pipeline_readiness_uses_50_samples_and_current_monitor_state():
    monitor, predictor = ConflictEntryMonitor(), FakePredictor()
    ldm = FakeLDM(track(0.98))
    monitor.update_ldm(ldm, 7.0, predictor)
    events, pipelines, config = _prediction_sections(
        Manager(ldm), monitor, SimpleNamespace(
            primary_threshold=.436, secondary_threshold=.387))
    card = pipelines["ego"][0]
    assert card["required_history_count"] == 50
    assert card["history_ready"] is True
    assert card["event"]["primary_model_executed"] is True
    assert card["event"]["primary"]["accepted"] is True
    assert events["ego"]["target"]["latest_estimated_eta"] == pytest.approx(.98)
    json.dumps({"events": events, "pipelines": pipelines, "config": config},
               allow_nan=False)


def test_incomplete_unobserved_and_departed_targets_are_represented_safely():
    monitor = ConflictEntryMonitor()
    incomplete = FakeLDM(track(4.2, count=32, observed=False))
    _, pipelines, _ = _prediction_sections(Manager(incomplete), monitor, None)
    card = pipelines["ego"][0]
    assert card["history_ready"] is False
    assert card["is_observed"] is False
    assert card["event_state"] == "NOT_ARMED"
    del incomplete.tracks["target"]
    _, pipelines, _ = _prediction_sections(Manager(incomplete), monitor, None)
    assert pipelines["ego"] == []


def test_feature_order_and_confidence_separation_match_runtime_contract():
    assert FEATURE_DIAGNOSTIC_NAMES == (
        "speed", "acceleration_magnitude", "longitudinal_velocity",
        "lateral_velocity", "longitudinal_acceleration",
        "lateral_acceleration",
    )
    _, _, config = _prediction_sections(
        Manager(FakeLDM(track(3.0))), ConflictEntryMonitor(), None)
    assert config["feature_names"] == list(FEATURE_DIAGNOSTIC_NAMES)
    assert config["ldm_confidence_is_gru_input"] is False
    assert "LDM confidence is NOT a GRU input" in HTML
    assert "ldm_confidence" not in IntentionPredictor.build_causal_features.__code__.co_names


def test_dashboard_supports_all_requested_prediction_states():
    for text in ('id="overview"', 'id="readiness"', 'id="timing"',
                 'id="model"', "Primary Prediction", "Secondary Prediction",
                 "Final Intention Fusion", "WAITING_FOR_FINALIZATION"):
        assert text in HTML


def test_main_writes_one_evidence_record_after_current_step_monitor_update():
    import main
    source = inspect.getsource(main.main)
    monitor_update = source.index("conflict_entry_monitor.update_ldm")
    evidence_build = source.index("evidence_snapshot = build_evidence_snapshot")
    evidence_write = source.index("evidence_writer.write(evidence_snapshot)")
    assert monitor_update < evidence_build < evidence_write
    assert source.count("evidence_writer.write(evidence_snapshot)") == 1
