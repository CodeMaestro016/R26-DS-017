"""Passive, JSON-safe perception/LDM evidence snapshots and JSONL output."""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

from config import (
    EVENT_ARMING_ETA_SECONDS, INCOMING_EDGE_IDS, MODEL_HISTORY_LENGTH,
    MODEL_SAMPLE_INTERVAL_SECONDS, PRIMARY_PREDICTION_LEAD_TIME_SECONDS,
    SECONDARY_PREDICTION_LEAD_TIME_SECONDS,
)
from predictor import FEATURE_DIAGNOSTIC_NAMES


LOCAL_FIELDS = (
    "object_id", "observation_type", "position", "speed",
    "heading_radians", "relative_position_ego", "relative_velocity_ego",
    "range", "bearing_radians", "fov_visible_fraction",
    "occlusion_visible_fraction", "visible_fraction",
    "measurement_timestamp", "available_timestamp", "detection_status",
)
DIAGNOSTIC_FIELDS = (
    "target_id", "range_m", "bearing_radians", "result", "reason",
    "fov_visible_fraction", "occlusion_visible_fraction", "visible_fraction",
)
STAGE_RESULT_FIELDS = (
    "probabilities", "predicted_class", "label", "confidence", "threshold",
    "accepted", "stage", "lead_time_seconds", "feature_diagnostics",
)
EVENT_FIELDS = (
    "event_id", "ego_id", "target_id", "event_start_time",
    "latest_estimated_eta", "latest_observation_age", "latest_history_count",
    "maximum_history_count", "primary_triggered", "primary_trigger_time",
    "primary_trigger_eta_seconds", "primary_distance_to_entry_meters",
    "primary_stage_reached", "primary_observed_at_trigger",
    "primary_observation_age_seconds", "primary_history_count_at_trigger",
    "primary_history_complete", "primary_history_timing_valid",
    "primary_model_executed", "primary_stage_status", "primary_stage_error",
    "secondary_triggered", "secondary_trigger_time",
    "secondary_trigger_eta_seconds", "secondary_distance_to_entry_meters",
    "secondary_stage_reached", "secondary_observed_at_trigger",
    "secondary_observation_age_seconds", "secondary_history_count_at_trigger",
    "secondary_history_complete", "secondary_history_timing_valid",
    "secondary_model_executed", "secondary_stage_status",
    "secondary_stage_error", "finalization_time", "finalization_reason",
    "event_category", "fused_label", "status",
)


def json_safe(value):
    """Convert NumPy/container values to strict JSON primitives."""
    if isinstance(value, np.generic):
        return json_safe(value.item())
    if isinstance(value, np.ndarray):
        return [json_safe(item) for item in value.tolist()]
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    if isinstance(value, (str, bool)) or value is None:
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    return str(value)


def _ground_truth(observations):
    vehicles = []
    for vehicle_id, state in observations.items():
        position = state.get("position", state.get("pos", (0.0, 0.0)))
        vehicles.append({
            "id": vehicle_id,
            "position": json_safe(position),
            "speed": float(state.get("speed", state.get("vel", 0.0))),
            "heading_radians": float(state.get("heading_radians", 0.0)),
            "lane_id": state.get("lane_id", ""),
            "road_id": state.get("road_id", ""),
        })
    return {"active_vehicle_count": len(vehicles), "vehicles": vehicles}


def _local_snapshot(raw):
    return [
        json_safe({key: observation[key] for key in LOCAL_FIELDS
                   if key in observation})
        for observation in raw.values()
    ]


def _ldm_snapshot(ldm):
    tracks = []
    for track_id, track in ldm.tracks.items():
        item = {
            "id": track_id,
            "position": track.get("position"),
            "speed": track.get("speed"),
            "heading_radians": track.get("heading_radians"),
            "lane_id": track.get("lane_id", ""),
            "road_id": track.get("road_id", ""),
            "distance_to_conflict": track.get("distance_to_conflict"),
            "is_observed": bool(track.get("is_observed", False)),
            "confidence": track.get("confidence"),
            "last_observed_time": track.get("last_observed_time"),
            "last_update_time": track.get("last_update_time"),
            "history_length": len(track.get("position_history", ())),
            "intention_prediction": prediction_record_snapshot(
                track.get("intention_prediction")
            ),
        }
        tracks.append(json_safe(item))
    return tracks


def _stage_result(result):
    if not isinstance(result, dict):
        return None
    return json_safe({key: result[key] for key in STAGE_RESULT_FIELDS
                      if key in result})


def prediction_record_snapshot(record):
    """Allow-list prediction evidence; evaluation route truth cannot leak."""
    if not isinstance(record, dict):
        return None
    result = {key: record[key] for key in EVENT_FIELDS if key in record}
    result["primary"] = _stage_result(record.get("primary"))
    result["secondary"] = _stage_result(record.get("secondary"))
    return json_safe(result)


def _prediction_sections(observation_manager, prediction_monitor, predictor):
    events_by_ego, pipeline_by_ego = {}, {}
    active = (prediction_monitor.get_active_event_snapshots()
              if prediction_monitor is not None else {})
    for ego_id, ldm in observation_manager.ldms.items():
        ego_events = {}
        cards = []
        try:
            relevant_ids = set(ldm.get_conflict_relevant_vehicles())
        except (KeyError, TypeError, ValueError):
            relevant_ids = set()
        for target_id, track in ldm.tracks.items():
            if target_id == ego_id:
                continue
            raw_event = active.get(ego_id, {}).get(target_id)
            raw_prediction = track.get("intention_prediction")
            event = prediction_record_snapshot(raw_event or raw_prediction) or {}
            if event:
                ego_events[target_id] = event
            history = track.get("position_history", ())
            count = len(history)
            timing_valid = False
            if prediction_monitor is not None:
                timing_valid, _ = prediction_monitor._history_timing_valid(history)
                distance = prediction_monitor.distance_to_conflict_entry(track)
                eta = prediction_monitor.estimate_time_to_entry(
                    distance, track.get("speed", 0.0)
                )
                if not math.isfinite(eta):
                    eta = None
            else:
                distance, eta = None, None
            active_event = raw_event is not None
            finalized = bool(event.get("finalization_time") is not None)
            event_state = ("ACTIVE" if active_event else
                           "FINALIZED" if finalized else "NOT_ARMED")
            primary = event.get("primary")
            secondary = event.get("secondary")
            overall = event.get("status") or (
                "WAITING_FOR_FINALIZATION" if active_event else "WAITING"
            )
            current_label = event.get("fused_label")
            if not current_label:
                current_label = ((secondary or primary or {}).get("label")
                                 if (secondary or primary) else "WAITING")
            cards.append(json_safe({
                "target_id": target_id,
                "road_id": track.get("road_id", ""),
                "is_observed": bool(track.get("is_observed", False)),
                "ldm_confidence": track.get("confidence"),
                "history_count": count,
                "required_history_count": MODEL_HISTORY_LENGTH,
                "history_ready": count == MODEL_HISTORY_LENGTH,
                "history_timing_valid": timing_valid,
                "distance_to_entry_meters": distance,
                "estimated_time_to_entry_seconds": eta,
                "incoming_road": track.get("road_id") in INCOMING_EDGE_IDS,
                "intersection_relevant": target_id in relevant_ids,
                "event_armed": active_event or finalized,
                "event_state": event_state,
                "primary_trigger_reached": bool(event.get("primary_triggered")),
                "primary_stage_status": event.get("primary_stage_status", "NOT_REACHED"),
                "secondary_stage_status": event.get("secondary_stage_status", "NOT_REACHED"),
                "current_intention": current_label,
                "overall_prediction_status": overall,
                "event": event,
            }))
        events_by_ego[ego_id] = ego_events
        pipeline_by_ego[ego_id] = cards
    config = {
        "event_arming_eta_seconds": EVENT_ARMING_ETA_SECONDS,
        "primary_lead_time_seconds": PRIMARY_PREDICTION_LEAD_TIME_SECONDS,
        "secondary_lead_time_seconds": SECONDARY_PREDICTION_LEAD_TIME_SECONDS,
        "required_history_count": MODEL_HISTORY_LENGTH,
        "sample_interval_seconds": MODEL_SAMPLE_INTERVAL_SECONDS,
        "sampling_frequency_hz": 1.0 / MODEL_SAMPLE_INTERVAL_SECONDS,
        "observation_window_seconds": (
            MODEL_HISTORY_LENGTH * MODEL_SAMPLE_INTERVAL_SECONDS
        ),
        "model_sequence_shape": [48, 6],
        "feature_names": list(FEATURE_DIAGNOSTIC_NAMES),
        "ldm_confidence_is_gru_input": False,
        "eta_is_gru_feature": False,
        "primary_threshold": getattr(predictor, "primary_threshold", None),
        "secondary_threshold": getattr(predictor, "secondary_threshold", None),
    }
    return events_by_ego, pipeline_by_ego, json_safe(config)


def build_evidence_snapshot(current_time, observations, observation_manager,
                            sensor_profile=None, sensor_range=None,
                            prediction_monitor=None, predictor=None,
                            path_manager=None, zone_manager=None):
    """Build the shared read-only visualization/evidence layer."""
    perception = {}
    local = {}
    ldms = {}
    approach = {}
    ego_ids = sorted(observation_manager.ldms)
    retained = observation_manager.get_last_local_observations()
    for ego_id in ego_ids:
        ldm = observation_manager.get_ldm(ego_id)
        diagnostics = observation_manager.perception_interface.get_last_diagnostics(
            ego_id
        )
        perception[ego_id] = {
            "summary": json_safe(
                observation_manager.perception_interface.get_last_summary(ego_id)
            ),
            "diagnostics": [json_safe({key: row[key] for key in DIAGNOSTIC_FIELDS
                                       if key in row}) for row in diagnostics],
        }
        local[ego_id] = _local_snapshot(retained.get(ego_id, {}))
        ldms[ego_id] = _ldm_snapshot(ldm)
        approach[ego_id] = bool(ldm.in_approach_zone)
    prediction_events, prediction_pipeline, prediction_config = (
        _prediction_sections(observation_manager, prediction_monitor, predictor)
    )
    result = {
        "time_seconds": float(current_time),
        "ground_truth": _ground_truth(observations),
        "perception_by_ego": perception,
        "local_observations_by_ego": local,
        "ldm_by_ego": ldms,
        "approach_zone_by_ego": approach,
        "sensor": {"profile": sensor_profile, "range_m": sensor_range},
        "prediction_events_by_ego": prediction_events,
        "prediction_pipeline_by_ego": prediction_pipeline,
        "prediction_configuration": prediction_config,
    }
    if path_manager is not None and zone_manager is not None:
        # Local import avoids coupling the base perception serializer to
        # Shapely unless conflict geometry is explicitly requested.
        from debug_conflict_evidence import build_conflict_evidence
        result.update(build_conflict_evidence(
            observation_manager, path_manager, zone_manager
        ))
    return result


class EvidenceJsonlWriter:
    """Incremental fresh-per-run JSONL writer, independent of the dashboard."""

    def __init__(self, path, flush_every=1):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._file = self.path.open("w", encoding="utf-8", newline="\n")
        self._flush_every = max(1, int(flush_every))
        self._writes = 0

    def write(self, record):
        self._file.write(json.dumps(json_safe(record), separators=(",", ":"),
                                    allow_nan=False) + "\n")
        self._writes += 1
        if self._writes % self._flush_every == 0:
            self._file.flush()

    def close(self):
        if not self._file.closed:
            self._file.flush()
            self._file.close()

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()
