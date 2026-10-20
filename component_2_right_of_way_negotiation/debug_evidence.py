"""Passive, JSON-safe perception/LDM evidence snapshots and JSONL output."""

# Import annotations from __future__ for the operations below.
from __future__ import annotations

# Import json for use in this module.
import json
# Import math for use in this module.
import math
# Import Path from pathlib for the operations below.
from pathlib import Path

# Import numpy as np for use in this module.
import numpy as np

# Import EVENT_ARMING_ETA_SECONDS, INCOMING_EDGE_IDS, MODEL_HISTORY_LENGTH, MODEL_SAMPLE_INTERVAL_SECONDS,
# PRIMARY_PREDICTION_LEAD_TIME_SECONDS,... from config for the operations below.
from config import (
    EVENT_ARMING_ETA_SECONDS, INCOMING_EDGE_IDS, MODEL_HISTORY_LENGTH,
    MODEL_SAMPLE_INTERVAL_SECONDS, PRIMARY_PREDICTION_LEAD_TIME_SECONDS,
    SECONDARY_PREDICTION_LEAD_TIME_SECONDS,
)
# Import FEATURE_DIAGNOSTIC_NAMES from predictor for the operations below.
from predictor import FEATURE_DIAGNOSTIC_NAMES


# Set LOCAL_FIELDS to a tuple containing the text 'object_id', the text 'observation_type', the text 'position',
# the text 'speed', the text...
LOCAL_FIELDS = (
    "object_id", "observation_type", "position", "speed",
    "heading_radians", "relative_position_ego", "relative_velocity_ego",
    "range", "bearing_radians", "fov_visible_fraction",
    "occlusion_visible_fraction", "visible_fraction",
    "measurement_timestamp", "available_timestamp", "detection_status",
)
# Set DIAGNOSTIC_FIELDS to a tuple containing the text 'target_id', the text 'range_m', the text
# 'bearing_radians', the text 'result', the text...
DIAGNOSTIC_FIELDS = (
    "target_id", "range_m", "bearing_radians", "result", "reason",
    "fov_visible_fraction", "occlusion_visible_fraction", "visible_fraction",
)
# Set STAGE_RESULT_FIELDS to a tuple containing the text 'probabilities', the text 'predicted_class', the text
# 'label', the text 'confidence', the text...
STAGE_RESULT_FIELDS = (
    "probabilities", "predicted_class", "label", "confidence", "threshold",
    "accepted", "stage", "lead_time_seconds", "feature_diagnostics",
)
# Set EVENT_FIELDS to a tuple containing the text 'event_id', the text 'ego_id', the text 'target_id', the text
# 'event_start_time', the text...
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


# Convert NumPy/container values to strict JSON primitives.
# Input value: the supplied value.
# Output: return the value selected by the matching return branch below.
# Processing: select branches using the stated conditions.
def json_safe(value):
    """Convert NumPy/container values to strict JSON primitives."""
    # Run this branch when whether value has type np.generic.
    if isinstance(value, np.generic):
        # Return the result of json_safe(the result of value.item()) to the caller.
        return json_safe(value.item())
    # Run this branch when whether value has type np.ndarray.
    if isinstance(value, np.ndarray):
        # Return a list of the result of json_safe(item) for item in the result of value.tolist() to the caller.
        return [json_safe(item) for item in value.tolist()]
    # Run this branch when whether value has type dict.
    if isinstance(value, dict):
        # Return a dictionary of a string built from key mapped to the result of json_safe(item) for (key, item)
        # in key/value pairs from value to the caller.
        return {str(key): json_safe(item) for key, item in value.items()}
    # Run this branch when whether value has type a tuple containing list, tuple.
    if isinstance(value, (list, tuple)):
        # Return a list of the result of json_safe(item) for item in value to the caller.
        return [json_safe(item) for item in value]
    # Run this branch when whether value has type a tuple containing str, bool or value is the same object as
    # None.
    if isinstance(value, (str, bool)) or value is None:
        # Return value to the caller.
        return value
    # Run this branch when whether value has type int.
    if isinstance(value, int):
        # Return value to the caller.
        return value
    # Run this branch when whether value has type float.
    if isinstance(value, float):
        # Return value when whether value contains finite numeric values, otherwise None to the caller.
        return value if math.isfinite(value) else None
    # Return a string built from value to the caller.
    return str(value)


# Ground truth using the inputs and processing steps below.
# Input observations: the supplied observations.
# Output: a dictionary containing active_vehicle_count, vehicles.
# Processing: iterate over the relevant records.
def _ground_truth(observations):
    # Set vehicles to an empty list.
    vehicles = []
    # Iterate over key/value pairs from observations, binding each item to (vehicle_id, state).
    for vehicle_id, state in observations.items():
        # Set position to 'position' from state; use 'pos' from state; use a tuple containing 0.0, 0.0 if absent
        # if absent.
        position = state.get("position", state.get("pos", (0.0, 0.0)))
        # Append a dictionary containing id, position, speed, heading_radians, lane_id, road_id to vehicles.
        vehicles.append({
            # Store vehicle_id under 'id'.
            "id": vehicle_id,
            # Store the result of json_safe(position) under 'position'.
            "position": json_safe(position),
            # Store a floating-point number built from 'speed' from state; use 'vel' from state; use 0.0 if absent
            # if absent under 'speed'.
            "speed": float(state.get("speed", state.get("vel", 0.0))),
            # Store a floating-point number built from 'heading_radians' from state; use 0.0 if absent under
            # 'heading_radians'.
            "heading_radians": float(state.get("heading_radians", 0.0)),
            # Store 'lane_id' from state; use the text '' if absent under 'lane_id'.
            "lane_id": state.get("lane_id", ""),
            # Store 'road_id' from state; use the text '' if absent under 'road_id'.
            "road_id": state.get("road_id", ""),
        })
    # Return a dictionary containing active_vehicle_count, vehicles to the caller.
    return {"active_vehicle_count": len(vehicles), "vehicles": vehicles}


# Local snapshot using the inputs and processing steps below.
# Input raw: the supplied raw.
# Output: a list of the result of json_safe(a dictionary of key mapped to observation at key for key in
# LOCAL_FIELDS; retain entries...) for observation in values from raw.
def _local_snapshot(raw):
    # Return a list of the result of json_safe(a dictionary of key mapped to observation at key for key in
    # LOCAL_FIELDS; retain entries...) for observation in values from raw to the caller.
    return [
        # Evaluate the result of json_safe(a dictionary of key mapped to observation at key for key in
        # LOCAL_FIELDS; retain entries...) as part of the enclosing expression.
        json_safe({key: observation[key] for key in LOCAL_FIELDS
                   # Evaluate key belongs to observation as part of the enclosing expression.
                   if key in observation})
        # Evaluate values from raw as part of the enclosing expression.
        for observation in raw.values()
    ]


# Ldm snapshot using the inputs and processing steps below.
# Input ldm: the supplied ldm.
# Output: tracks.
# Processing: iterate over the relevant records.
def _ldm_snapshot(ldm):
    # Set tracks to an empty list.
    tracks = []
    # Iterate over key/value pairs from ldm.tracks, binding each item to (track_id, track).
    for track_id, track in ldm.tracks.items():
        # Set item to a dictionary containing id, position, speed, heading_radians, lane_id, road_id,
        # distance_to_conflict,...
        item = {
            # Store track_id under 'id'.
            "id": track_id,
            # Store 'position' from track; use None if absent under 'position'.
            "position": track.get("position"),
            # Store 'speed' from track; use None if absent under 'speed'.
            "speed": track.get("speed"),
            # Store 'heading_radians' from track; use None if absent under 'heading_radians'.
            "heading_radians": track.get("heading_radians"),
            # Store 'lane_id' from track; use the text '' if absent under 'lane_id'.
            "lane_id": track.get("lane_id", ""),
            # Store 'road_id' from track; use the text '' if absent under 'road_id'.
            "road_id": track.get("road_id", ""),
            # Store 'distance_to_conflict' from track; use None if absent under 'distance_to_conflict'.
            "distance_to_conflict": track.get("distance_to_conflict"),
            # Store a Boolean built from 'is_observed' from track; use False if absent under 'is_observed'.
            "is_observed": bool(track.get("is_observed", False)),
            # Store 'confidence' from track; use None if absent under 'confidence'.
            "confidence": track.get("confidence"),
            # Store 'last_observed_time' from track; use None if absent under 'last_observed_time'.
            "last_observed_time": track.get("last_observed_time"),
            # Store 'last_update_time' from track; use None if absent under 'last_update_time'.
            "last_update_time": track.get("last_update_time"),
            # Store the number of entries in 'position_history' from track; use an empty tuple if absent under
            # 'history_length'.
            "history_length": len(track.get("position_history", ())),
            # Store the result of prediction_record_snapshot('intention_prediction' from track; use None if
            # absent) under 'intention_prediction'.
            "intention_prediction": prediction_record_snapshot(
                # Supply 'intention_prediction' from track; use None if absent to prediction_record_snapshot.
                track.get("intention_prediction")
            ),
        }
        # Append the result of json_safe(item) to tracks.
        tracks.append(json_safe(item))
    # Return tracks to the caller.
    return tracks


# Stage result using the inputs and processing steps below.
# Input result: the supplied result.
# Output: return the value selected by the matching return branch below.
# Processing: select branches using the stated conditions.
def _stage_result(result):
    # Run this branch when the negation of whether result has type dict.
    if not isinstance(result, dict):
        # Return None to the caller.
        return None
    # Return the result of json_safe(a dictionary of key mapped to result at key for key in STAGE_RESULT_FIELDS;
    # retain entries...) to the caller.
    return json_safe({key: result[key] for key in STAGE_RESULT_FIELDS
                      # Evaluate key belongs to result as part of the enclosing expression.
                      if key in result})


# Allow-list prediction evidence; evaluation route truth cannot leak.
# Input record: the supplied record.
# Output: return the value selected by the matching return branch below.
# Processing: select branches using the stated conditions.
def prediction_record_snapshot(record):
    """Allow-list prediction evidence; evaluation route truth cannot leak."""
    # Run this branch when the negation of whether record has type dict.
    if not isinstance(record, dict):
        # Return None to the caller.
        return None
    # Set result to a dictionary of key mapped to record at key for key in EVENT_FIELDS; retain entries satisfying
    # key belongs to record.
    result = {key: record[key] for key in EVENT_FIELDS if key in record}
    # Set result['primary'] to the result of _stage_result('primary' from record; use None if absent).
    result["primary"] = _stage_result(record.get("primary"))
    # Set result['secondary'] to the result of _stage_result('secondary' from record; use None if absent).
    result["secondary"] = _stage_result(record.get("secondary"))
    # Return the result of json_safe(result) to the caller.
    return json_safe(result)


# Prediction sections using the inputs and processing steps below.
# Input observation_manager: the supplied observation manager.
# Input prediction_monitor: the supplied prediction monitor.
# Input predictor: the supplied predictor.
# Output: a tuple containing events_by_ego, pipeline_by_ego, the result of json_safe(config).
# Processing: iterate over the relevant records, then select branches using the stated conditions, then handle the
# specified errors.
def _prediction_sections(observation_manager, prediction_monitor, predictor):
    # Set (events_by_ego, pipeline_by_ego) to a tuple containing an empty dictionary, an empty dictionary.
    events_by_ego, pipeline_by_ego = {}, {}
    # Set active to the result of prediction_monitor.get_active_event_snapshots() when prediction_monitor is a
    # different object from None, otherwise an empty dictionary.
    active = (prediction_monitor.get_active_event_snapshots()
              # Evaluate prediction_monitor is a different object from None as part of the enclosing expression.
              if prediction_monitor is not None else {})
    # Iterate over key/value pairs from observation_manager.ldms, binding each item to (ego_id, ldm).
    for ego_id, ldm in observation_manager.ldms.items():
        # Set ego_events to an empty dictionary.
        ego_events = {}
        # Set cards to an empty list.
        cards = []
        # Attempt the enclosed operations and route matching exceptions to the handlers below.
        try:
            # Set relevant_ids to a set built from the result of ldm.get_conflict_relevant_vehicles().
            relevant_ids = set(ldm.get_conflict_relevant_vehicles())
        # Handle (KeyError, TypeError, ValueError) using the recovery steps below.
        except (KeyError, TypeError, ValueError):
            # Set relevant_ids to an empty set.
            relevant_ids = set()
        # Iterate over key/value pairs from ldm.tracks, binding each item to (target_id, track).
        for target_id, track in ldm.tracks.items():
            # Run this branch when target_id equals ego_id.
            if target_id == ego_id:
                # Skip the rest of this loop iteration and process the next item.
                continue
            # Set raw_event to target_id from active.get(ego_id, {}); use None if absent.
            raw_event = active.get(ego_id, {}).get(target_id)
            # Set raw_prediction to 'intention_prediction' from track; use None if absent.
            raw_prediction = track.get("intention_prediction")
            # Set event to the result of prediction_record_snapshot(raw_event or raw_prediction) or an empty
            # dictionary.
            event = prediction_record_snapshot(raw_event or raw_prediction) or {}
            # Run this branch when event.
            if event:
                # Set ego_events[target_id] to event.
                ego_events[target_id] = event
            # Set history to 'position_history' from track; use an empty tuple if absent.
            history = track.get("position_history", ())
            # Set count to the number of entries in history.
            count = len(history)
            # Set timing_valid to False.
            timing_valid = False
            # Run this branch when prediction_monitor is a different object from None.
            if prediction_monitor is not None:
                # Set (timing_valid, _) to the result of prediction_monitor._history_timing_valid(history).
                timing_valid, _ = prediction_monitor._history_timing_valid(history)
                # Set distance to the result of prediction_monitor.distance_to_conflict_entry(track).
                distance = prediction_monitor.distance_to_conflict_entry(track)
                # Set eta to the result of prediction_monitor.estimate_time_to_entry(distance, 'speed' from track;
                # use 0.0 if absent).
                eta = prediction_monitor.estimate_time_to_entry(
                    # Supply 'speed' from track; use 0.0 if absent to prediction_monitor.estimate_time_to_entry.
                    distance, track.get("speed", 0.0)
                )
                # Run this branch when the negation of whether eta contains finite numeric values.
                if not math.isfinite(eta):
                    # Set eta to None.
                    eta = None
            # Run this alternative branch when the preceding branch does not apply.
            else:
                # Set (distance, eta) to a tuple containing None, None.
                distance, eta = None, None
            # Set active_event to raw_event is a different object from None.
            active_event = raw_event is not None
            # Set finalized to a Boolean built from 'finalization_time' from event; use None if absent is a
            # different object from None.
            finalized = bool(event.get("finalization_time") is not None)
            # Set event_state to the text 'ACTIVE' when active_event, otherwise the text 'FINALIZED' when
            # finalized, otherwise the text 'NOT_ARMED'.
            event_state = ("ACTIVE" if active_event else
                           # Evaluate the text 'FINALIZED' when finalized, otherwise the text 'NOT_ARMED' as part
                           # of the enclosing expression.
                           "FINALIZED" if finalized else "NOT_ARMED")
            # Set primary to 'primary' from event; use None if absent.
            primary = event.get("primary")
            # Set secondary to 'secondary' from event; use None if absent.
            secondary = event.get("secondary")
            # Set overall to 'status' from event; use None if absent or the text 'WAITING_FOR_FINALIZATION' when
            # active_event, otherwise the text 'WAITING'.
            overall = event.get("status") or (
                # Evaluate the text 'WAITING_FOR_FINALIZATION' when active_event, otherwise the text 'WAITING' as
                # part of the enclosing expression.
                "WAITING_FOR_FINALIZATION" if active_event else "WAITING"
            )
            # Set current_label to 'fused_label' from event; use None if absent.
            current_label = event.get("fused_label")
            # Run this branch when the negation of current_label.
            if not current_label:
                # Set current_label to 'label' from (secondary or primary or {}); use None if absent when
                # secondary or primary, otherwise the text 'WAITING'.
                current_label = ((secondary or primary or {}).get("label")
                                 # Evaluate secondary or primary as part of the enclosing expression.
                                 if (secondary or primary) else "WAITING")
            # Append the result of json_safe(a dictionary containing target_id, road_id, is_observed,
            # ldm_confidence, history_count,...) to cards.
            cards.append(json_safe({
                # Store target_id under 'target_id'.
                "target_id": target_id,
                # Store 'road_id' from track; use the text '' if absent under 'road_id'.
                "road_id": track.get("road_id", ""),
                # Store a Boolean built from 'is_observed' from track; use False if absent under 'is_observed'.
                "is_observed": bool(track.get("is_observed", False)),
                # Store 'confidence' from track; use None if absent under 'ldm_confidence'.
                "ldm_confidence": track.get("confidence"),
                # Store count under 'history_count'.
                "history_count": count,
                # Store MODEL_HISTORY_LENGTH under 'required_history_count'.
                "required_history_count": MODEL_HISTORY_LENGTH,
                # Store count equals MODEL_HISTORY_LENGTH under 'history_ready'.
                "history_ready": count == MODEL_HISTORY_LENGTH,
                # Store timing_valid under 'history_timing_valid'.
                "history_timing_valid": timing_valid,
                # Store distance under 'distance_to_entry_meters'.
                "distance_to_entry_meters": distance,
                # Store eta under 'estimated_time_to_entry_seconds'.
                "estimated_time_to_entry_seconds": eta,
                # Store 'road_id' from track; use None if absent belongs to INCOMING_EDGE_IDS under
                # 'incoming_road'.
                "incoming_road": track.get("road_id") in INCOMING_EDGE_IDS,
                # Store target_id belongs to relevant_ids under 'intersection_relevant'.
                "intersection_relevant": target_id in relevant_ids,
                # Store active_event or finalized under 'event_armed'.
                "event_armed": active_event or finalized,
                # Store event_state under 'event_state'.
                "event_state": event_state,
                # Store a Boolean built from 'primary_triggered' from event; use None if absent under
                # 'primary_trigger_reached'.
                "primary_trigger_reached": bool(event.get("primary_triggered")),
                # Store 'primary_stage_status' from event; use the text 'NOT_REACHED' if absent under
                # 'primary_stage_status'.
                "primary_stage_status": event.get("primary_stage_status", "NOT_REACHED"),
                # Store 'secondary_stage_status' from event; use the text 'NOT_REACHED' if absent under
                # 'secondary_stage_status'.
                "secondary_stage_status": event.get("secondary_stage_status", "NOT_REACHED"),
                # Store current_label under 'current_intention'.
                "current_intention": current_label,
                # Store overall under 'overall_prediction_status'.
                "overall_prediction_status": overall,
                # Store event under 'event'.
                "event": event,
            }))
        # Set events_by_ego[ego_id] to ego_events.
        events_by_ego[ego_id] = ego_events
        # Set pipeline_by_ego[ego_id] to cards.
        pipeline_by_ego[ego_id] = cards
    # Set config to a dictionary containing event_arming_eta_seconds, primary_lead_time_seconds,
    # secondary_lead_time_seconds,...
    config = {
        # Store EVENT_ARMING_ETA_SECONDS under 'event_arming_eta_seconds'.
        "event_arming_eta_seconds": EVENT_ARMING_ETA_SECONDS,
        # Store PRIMARY_PREDICTION_LEAD_TIME_SECONDS under 'primary_lead_time_seconds'.
        "primary_lead_time_seconds": PRIMARY_PREDICTION_LEAD_TIME_SECONDS,
        # Store SECONDARY_PREDICTION_LEAD_TIME_SECONDS under 'secondary_lead_time_seconds'.
        "secondary_lead_time_seconds": SECONDARY_PREDICTION_LEAD_TIME_SECONDS,
        # Store MODEL_HISTORY_LENGTH under 'required_history_count'.
        "required_history_count": MODEL_HISTORY_LENGTH,
        # Store MODEL_SAMPLE_INTERVAL_SECONDS under 'sample_interval_seconds'.
        "sample_interval_seconds": MODEL_SAMPLE_INTERVAL_SECONDS,
        # Store 1.0 divided by MODEL_SAMPLE_INTERVAL_SECONDS under 'sampling_frequency_hz'.
        "sampling_frequency_hz": 1.0 / MODEL_SAMPLE_INTERVAL_SECONDS,
        # Store MODEL_HISTORY_LENGTH multiplied by MODEL_SAMPLE_INTERVAL_SECONDS under
        # 'observation_window_seconds'.
        "observation_window_seconds": (
            # Evaluate MODEL_HISTORY_LENGTH multiplied by MODEL_SAMPLE_INTERVAL_SECONDS as part of the enclosing
            # expression.
            MODEL_HISTORY_LENGTH * MODEL_SAMPLE_INTERVAL_SECONDS
        ),
        # Store a list containing 48, 6 under 'model_sequence_shape'.
        "model_sequence_shape": [48, 6],
        # Store a list built from FEATURE_DIAGNOSTIC_NAMES under 'feature_names'.
        "feature_names": list(FEATURE_DIAGNOSTIC_NAMES),
        # Store False under 'ldm_confidence_is_gru_input'.
        "ldm_confidence_is_gru_input": False,
        # Store False under 'eta_is_gru_feature'.
        "eta_is_gru_feature": False,
        # Store the requested attribute of predictor under 'primary_threshold'.
        "primary_threshold": getattr(predictor, "primary_threshold", None),
        # Store the requested attribute of predictor under 'secondary_threshold'.
        "secondary_threshold": getattr(predictor, "secondary_threshold", None),
    }
    # Return a tuple containing events_by_ego, pipeline_by_ego, the result of json_safe(config) to the caller.
    return events_by_ego, pipeline_by_ego, json_safe(config)


# Build the shared read-only visualization/evidence layer.
# Input current_time: the supplied current time.
# Input observations: the supplied observations.
# Input observation_manager: the supplied observation manager.
# Input sensor_profile: the supplied sensor profile.
# Input sensor_range: the supplied sensor range.
# Input prediction_monitor: the supplied prediction monitor.
# Input predictor: the supplied predictor.
# Input path_manager: the supplied path manager.
# Input zone_manager: the supplied zone manager.
# Output: result.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def build_evidence_snapshot(current_time, observations, observation_manager,
                            # Declare sensor_profile, sensor_range as input parameters.
                            sensor_profile=None, sensor_range=None,
                            # Declare prediction_monitor, predictor as input parameters.
                            prediction_monitor=None, predictor=None,
                            # Declare path_manager, zone_manager as input parameters.
                            path_manager=None, zone_manager=None):
    """Build the shared read-only visualization/evidence layer."""
    # Set perception to an empty dictionary.
    perception = {}
    # Set local to an empty dictionary.
    local = {}
    # Set ldms to an empty dictionary.
    ldms = {}
    # Set approach to an empty dictionary.
    approach = {}
    # Set ego_ids to the sorted values from observation_manager.ldms.
    ego_ids = sorted(observation_manager.ldms)
    # Set retained to the result of observation_manager.get_last_local_observations().
    retained = observation_manager.get_last_local_observations()
    # Iterate over ego_ids, binding each item to ego_id.
    for ego_id in ego_ids:
        # Set ldm to the result of observation_manager.get_ldm(ego_id).
        ldm = observation_manager.get_ldm(ego_id)
        # Set diagnostics to the result of observation_manager.perception_interface.get_last_diagnostics(ego_id).
        diagnostics = observation_manager.perception_interface.get_last_diagnostics(
            # Supply ego_id to observation_manager.perception_interface.get_last_diagnostics.
            ego_id
        )
        # Set perception[ego_id] to a dictionary containing summary, diagnostics.
        perception[ego_id] = {
            # Store the result of json_safe(the result of
            # observation_manager.perception_interface.get_last_summary(ego_id)) under 'summary'.
            "summary": json_safe(
                # Supply the result of observation_manager.perception_interface.get_last_summary(ego_id) to
                # json_safe.
                observation_manager.perception_interface.get_last_summary(ego_id)
            ),
            # Store a list of the result of json_safe(a dictionary of key mapped to row at key for key in
            # DIAGNOSTIC_FIELDS; retain entries satisfying...) for row in diagnostics under 'diagnostics'.
            "diagnostics": [json_safe({key: row[key] for key in DIAGNOSTIC_FIELDS
                                       # Evaluate diagnostics as part of the enclosing expression.
                                       if key in row}) for row in diagnostics],
        }
        # Set local[ego_id] to the result of _local_snapshot(ego_id from retained; use an empty dictionary if
        # absent).
        local[ego_id] = _local_snapshot(retained.get(ego_id, {}))
        # Set ldms[ego_id] to the result of _ldm_snapshot(ldm).
        ldms[ego_id] = _ldm_snapshot(ldm)
        # Set approach[ego_id] to a Boolean built from ldm.in_approach_zone.
        approach[ego_id] = bool(ldm.in_approach_zone)
    # Set (prediction_events, prediction_pipeline, prediction_config) to the result of
    # _prediction_sections(observation_manager, prediction_monitor, predictor).
    prediction_events, prediction_pipeline, prediction_config = (
        # Evaluate the result of _prediction_sections(observation_manager, prediction_monitor, predictor) as part
        # of the enclosing expression.
        _prediction_sections(observation_manager, prediction_monitor, predictor)
    )
    # Set result to a dictionary containing time_seconds, ground_truth, perception_by_ego,
    # local_observations_by_ego, ldm_by_ego,...
    result = {
        # Store a floating-point number built from current_time under 'time_seconds'.
        "time_seconds": float(current_time),
        # Store the result of _ground_truth(observations) under 'ground_truth'.
        "ground_truth": _ground_truth(observations),
        # Store perception under 'perception_by_ego'.
        "perception_by_ego": perception,
        # Store local under 'local_observations_by_ego'.
        "local_observations_by_ego": local,
        # Store ldms under 'ldm_by_ego'.
        "ldm_by_ego": ldms,
        # Store approach under 'approach_zone_by_ego'.
        "approach_zone_by_ego": approach,
        # Store a dictionary containing profile, range_m under 'sensor'.
        # Store sensor_profile under 'profile'.
        # Store sensor_range under 'range_m'.
        "sensor": {"profile": sensor_profile, "range_m": sensor_range},
        # Store prediction_events under 'prediction_events_by_ego'.
        "prediction_events_by_ego": prediction_events,
        # Store prediction_pipeline under 'prediction_pipeline_by_ego'.
        "prediction_pipeline_by_ego": prediction_pipeline,
        # Store prediction_config under 'prediction_configuration'.
        "prediction_configuration": prediction_config,
    }
    # Run this branch when path_manager is a different object from None and zone_manager is a different object
    # from None.
    if path_manager is not None and zone_manager is not None:
        # Local import avoids coupling the base perception serializer to
        # Shapely unless conflict geometry is explicitly requested.
        # Import build_conflict_evidence from debug_conflict_evidence for the operations below.
        from debug_conflict_evidence import build_conflict_evidence
        # Update result with the supplied entries.
        result.update(build_conflict_evidence(
            # Supply observation_manager to build_conflict_evidence.
            observation_manager, path_manager, zone_manager
        ))
    # Return result to the caller.
    return result


# Incremental fresh-per-run JSONL writer, independent of the dashboard.
# Instances expose the attributes and methods implemented in this class.
class EvidenceJsonlWriter:
    """Incremental fresh-per-run JSONL writer, independent of the dashboard."""

    # Initialize the instance attributes and collaborators used by the operations below.
    # Input path: the path or path object supplied by the caller.
    # Input flush_every: the supplied flush every.
    # Output: no explicit value; normal completion returns None.
    def __init__(self, path, flush_every=1):
        # Set self.path to the result of Path(path).
        self.path = Path(path)
        # Create the directory requested by self.path.parent.
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # Set self._file to the result of self.path.open(the text 'w').
        self._file = self.path.open("w", encoding="utf-8", newline="\n")
        # Set self._flush_every to the maximum of 1, an integer built from flush_every.
        self._flush_every = max(1, int(flush_every))
        # Set self._writes to 0.
        self._writes = 0

    # Write using the inputs and processing steps below.
    # Input record: the supplied record.
    # Output: no explicit value; normal completion returns None.
    # Processing: select branches using the stated conditions.
    def write(self, record):
        # Call self._file.write with the supplied arguments.
        self._file.write(json.dumps(json_safe(record), separators=(",", ":"),
                                    # Supply allow_nan as False.
                                    allow_nan=False) + "\n")
        # Update self._writes to its current value plus 1.
        self._writes += 1
        # Run this branch when self._writes modulo self._flush_every equals 0.
        if self._writes % self._flush_every == 0:
            # Call self._file.flush with the supplied arguments.
            self._file.flush()

    # Close using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    # Processing: select branches using the stated conditions.
    def close(self):
        # Run this branch when the negation of self._file.closed.
        if not self._file.closed:
            # Call self._file.flush with the supplied arguments.
            self._file.flush()
            # Call self._file.close with the supplied arguments.
            self._file.close()

    # Enter using the inputs and processing steps below.
    # Output: self.
    def __enter__(self):
        # Return self to the caller.
        return self

    # Exit using the inputs and processing steps below.
    # Input _args: the supplied args.
    # Output: no explicit value; normal completion returns None.
    def __exit__(self, *_args):
        # Call self.close with the supplied arguments.
        self.close()
