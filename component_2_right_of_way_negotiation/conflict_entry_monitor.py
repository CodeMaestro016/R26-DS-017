"""Route-independent conflict-entry timing for shadow prediction events."""

# Import copy for use in this module.
import copy
# Import math for use in this module.
import math

# Import CONFLICT_TRIGGER_TOLERANCE_SECONDS, EVENT_ARMING_ETA_SECONDS, INCOMING_EDGE_IDS, MIN_ETA_SPEED_MPS,
# MODEL_HISTORY_LENGTH, PRIMARY_PREDICTION_LEAD_TIME_SECONDS,... from config for the operations below.
from config import (
    CONFLICT_TRIGGER_TOLERANCE_SECONDS,
    EVENT_ARMING_ETA_SECONDS,
    INCOMING_EDGE_IDS,
    MIN_ETA_SPEED_MPS,
    MODEL_HISTORY_LENGTH,
    PRIMARY_PREDICTION_LEAD_TIME_SECONDS,
    SECONDARY_PREDICTION_LEAD_TIME_SECONDS,
)
# Import IntentionPredictor, PredictionContractError, UNKNOWN_LABEL from predictor for the operations below.
from predictor import IntentionPredictor, PredictionContractError, UNKNOWN_LABEL


# Manage at most one primary and secondary call per ego-target approach.
# Instances expose the attributes and methods implemented in this class.
class ConflictEntryMonitor:
    """Manage at most one primary and secondary call per ego-target approach."""

    # Initialize the instance attributes and collaborators used by the operations below.
    # Output: no explicit value; normal completion returns None.
    def __init__(self):
        # Call self.reset with the supplied arguments.
        self.reset()

    # Reset using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    def reset(self):
        # Set self.events to an empty dictionary.
        self.events = {}
        # Set self.completed_pairs to an empty set.
        self.completed_pairs = set()
        # Set self.next_event_number to 1.
        self.next_event_number = 1

    # Return defensive operational snapshots with evaluation truth removed.
    # Input ego_id: the identifier of the ego vehicle.
    # Output: return the value selected by the matching return branch below.
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    def get_active_event_snapshots(self, ego_id=None):
        """Return defensive operational snapshots with evaluation truth removed."""
        # Set snapshots to an empty dictionary.
        snapshots = {}
        # Iterate over key/value pairs from self.events, binding each item to ((event_ego_id, target_id), event).
        for (event_ego_id, target_id), event in self.events.items():
            # Run this branch when ego_id is a different object from None and event_ego_id differs from ego_id.
            if ego_id is not None and event_ego_id != ego_id:
                # Skip the rest of this loop iteration and process the next item.
                continue
            # Set snapshot to a dictionary of key mapped to value for (key, value) in key/value pairs from event;
            # retain entries satisfying key does not belong to a set containing the text 'ground_truth_route_id',
            # the text...
            snapshot = {
                # Evaluate key/value pairs from event as part of the enclosing expression.
                key: value for key, value in event.items()
                # Evaluate key does not belong to a set containing the text 'ground_truth_route_id', the text
                # 'previous_eta_seconds' as part of the enclosing expression.
                if key not in {"ground_truth_route_id", "previous_eta_seconds"}
            }
            # Set snapshots.setdefault(event_ego_id, {})[target_id] to the result of copy.deepcopy(snapshot).
            snapshots.setdefault(event_ego_id, {})[target_id] = copy.deepcopy(
                # Supply snapshot to copy.deepcopy.
                snapshot
            )
        # Run this branch when ego_id is a different object from None.
        if ego_id is not None:
            # Return ego_id from snapshots; use an empty dictionary if absent to the caller.
            return snapshots.get(ego_id, {})
        # Return snapshots to the caller.
        return snapshots

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Distance to conflict entry using the inputs and processing steps below.
    # Input track: the supplied track.
    # Output: return the value selected by the matching return branch below.
    # Processing: select branches using the stated conditions.
    def distance_to_conflict_entry(track):
        # Run this branch when 'road_id' from track; use None if absent does not belong to INCOMING_EDGE_IDS.
        if track.get("road_id") not in INCOMING_EDGE_IDS:
            # Return None to the caller.
            return None
        # Set position to a floating-point number built from 'lane_position' from track; use 0.0 if absent.
        position = float(track.get("lane_position", 0.0))
        # Set length to a floating-point number built from 'lane_length' from track; use 0.0 if absent.
        length = float(track.get("lane_length", 0.0))
        # Run this branch when the negation of whether position contains finite numeric values or the negation of
        # whether length contains finite numeric values or length is at most 0.
        if not math.isfinite(position) or not math.isfinite(length) or length <= 0:
            # Return None to the caller.
            return None
        # Return the maximum of 0.0, length minus position to the caller.
        return max(0.0, length - position)

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Estimate time to entry using the inputs and processing steps below.
    # Input distance: the supplied distance.
    # Input speed: the supplied speed.
    # Output: return the value selected by the matching return branch below.
    # Processing: select branches using the stated conditions.
    def estimate_time_to_entry(distance, speed):
        # Set speed to a floating-point number built from speed.
        speed = float(speed)
        # Run this branch when distance is the same object as None or the negation of whether distance contains
        # finite numeric values or the negation of whether speed contains finite numeric values or speed is less
        # than MIN_ETA_SPEED_MPS.
        if distance is None or not math.isfinite(distance) or not math.isfinite(speed) or speed < MIN_ETA_SPEED_MPS:
            # Return math.inf to the caller.
            return math.inf
        # Return the maximum of 0.0, a floating-point number built from distance divided by speed to the caller.
        return max(0.0, float(distance) / speed)

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Lead time using the inputs and processing steps below.
    # Input stage: the supplied stage.
    # Output: PRIMARY_PREDICTION_LEAD_TIME_SECONDS when stage equals the text 'primary', otherwise
    # SECONDARY_PREDICTION_LEAD_TIME_SECONDS.
    def _lead_time(stage):
        # Return PRIMARY_PREDICTION_LEAD_TIME_SECONDS when stage equals the text 'primary', otherwise
        # SECONDARY_PREDICTION_LEAD_TIME_SECONDS to the caller.
        return (PRIMARY_PREDICTION_LEAD_TIME_SECONDS if stage == "primary"
                # Evaluate SECONDARY_PREDICTION_LEAD_TIME_SECONDS as part of the enclosing expression.
                else SECONDARY_PREDICTION_LEAD_TIME_SECONDS)

    # New event using the inputs and processing steps below.
    # Input ego_id: the identifier of the ego vehicle.
    # Input target_id: the supplied target id.
    # Input track: the supplied track.
    # Input current_time: the supplied current time.
    # Output: event.
    # Processing: iterate over the relevant records.
    def _new_event(self, ego_id, target_id, track, current_time):
        # Set event to a dictionary containing event_id, ego_id, target_id, event_start_time,
        # ground_truth_route_id,...
        event = {
            # Store formatted text built from the embedded values under 'event_id'.
            "event_id": f"event_{self.next_event_number:06d}_{ego_id}_{target_id}",
            # Store ego_id under 'ego_id'.
            "ego_id": ego_id,
            # Store target_id under 'target_id'.
            "target_id": target_id,
            # Store a floating-point number built from current_time under 'event_start_time'.
            "event_start_time": float(current_time),
            # Copied only for finalized evaluation/debug output.
            # Evaluation-only truth is held outside operational LDM tracks.
            "ground_truth_route_id": "",
            # Store None under 'previous_eta_seconds'.
            "previous_eta_seconds": None,
            # Store None under 'latest_estimated_eta'.
            "latest_estimated_eta": None,
            # Store None under 'latest_observation_age'.
            "latest_observation_age": None,
            # Store the number of entries in 'position_history' from track; use an empty tuple if absent under
            # 'latest_history_count'.
            "latest_history_count": len(track.get("position_history", ())),
            # Store the number of entries in 'position_history' from track; use an empty tuple if absent under
            # 'maximum_history_count'.
            "maximum_history_count": len(track.get("position_history", ())),
        }
        # Iterate over a tuple containing the text 'primary', the text 'secondary', binding each item to stage.
        for stage in ("primary", "secondary"):
            # Update event with the supplied entries.
            event.update({
                # Store False under f'{stage}_triggered'.
                f"{stage}_triggered": False,
                # Store None under f'{stage}_trigger_time'.
                f"{stage}_trigger_time": None,
                # Store None under f'{stage}_trigger_eta_seconds'.
                f"{stage}_trigger_eta_seconds": None,
                # Store None under f'{stage}_distance_to_entry_meters'.
                f"{stage}_distance_to_entry_meters": None,
                # Store False under f'{stage}_stage_reached'.
                f"{stage}_stage_reached": False,
                # Store None under f'{stage}_observed_at_trigger'.
                f"{stage}_observed_at_trigger": None,
                # Store None under f'{stage}_observation_age_seconds'.
                f"{stage}_observation_age_seconds": None,
                # Store None under f'{stage}_history_count_at_trigger'.
                f"{stage}_history_count_at_trigger": None,
                # Store None under f'{stage}_history_complete'.
                f"{stage}_history_complete": None,
                # Store None under f'{stage}_history_timing_valid'.
                f"{stage}_history_timing_valid": None,
                # Store False under f'{stage}_model_executed'.
                f"{stage}_model_executed": False,
                # Store the text 'NOT_REACHED' under f'{stage}_stage_status'.
                f"{stage}_stage_status": "NOT_REACHED",
                # Store the text '' under f'{stage}_stage_error'.
                f"{stage}_stage_error": "",
                # Store None under stage.
                stage: None,
            })
        # Update self.next_event_number to its current value plus 1.
        self.next_event_number += 1
        # Return event to the caller.
        return event

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # History timing valid using the inputs and processing steps below.
    # Input history: the supplied history.
    # Output: return the value selected by the matching return branch below.
    # Processing: select branches using the stated conditions, then handle the specified errors.
    def _history_timing_valid(history):
        # Run this branch when the number of entries in history differs from MODEL_HISTORY_LENGTH.
        if len(history) != MODEL_HISTORY_LENGTH:
            # Return a tuple containing False, the text '' to the caller.
            return False, ""
        # Attempt the enclosed operations and route matching exceptions to the handlers below.
        try:
            # Call IntentionPredictor._history_arrays with the supplied arguments.
            IntentionPredictor._history_arrays(history)
            # Return a tuple containing True, the text '' to the caller.
            return True, ""
        # Handle PredictionContractError as error using the recovery steps below.
        except PredictionContractError as error:
            # Return a tuple containing False, a string built from error to the caller.
            return False, str(error)

    # Record stage using the inputs and processing steps below.
    # Input event: the supplied event.
    # Input stage: the supplied stage.
    # Input track: the supplied track.
    # Input current_time: the supplied current time.
    # Input eta: the supplied eta.
    # Input distance: the supplied distance.
    # Input predictor: the supplied predictor.
    # Input status: the supplied status.
    # Output: no explicit value; normal completion returns None.
    # Processing: select branches using the stated conditions, then handle the specified errors.
    def _record_stage(self, event, stage, track, current_time, eta, distance,
                      # Declare predictor, status as input parameters.
                      predictor, status=None):
        # Set history to 'position_history' from track; use an empty tuple if absent.
        history = track.get("position_history", ())
        # Set count to the number of entries in history.
        count = len(history)
        # Set observed to a Boolean built from 'is_observed' from track; use False if absent.
        observed = bool(track.get("is_observed", False))
        # Set age to the maximum of 0.0, a floating-point number built from current_time minus a floating-point
        # number built from...
        age = max(0.0, float(current_time) - float(track.get("last_observed_time", current_time)))
        # Set complete to count equals MODEL_HISTORY_LENGTH.
        complete = count == MODEL_HISTORY_LENGTH
        # Set (timing_valid, timing_error) to the result of self._history_timing_valid(history).
        timing_valid, timing_error = self._history_timing_valid(history)
        # Update event with the supplied entries.
        event.update({
            # Store True under f'{stage}_triggered'.
            f"{stage}_triggered": True,
            # Store a floating-point number built from current_time under f'{stage}_trigger_time'.
            f"{stage}_trigger_time": float(current_time),
            # Store a floating-point number built from eta when whether eta contains finite numeric values,
            # otherwise None under f'{stage}_trigger_eta_seconds'.
            f"{stage}_trigger_eta_seconds": float(eta) if math.isfinite(eta) else None,
            # Store distance under f'{stage}_distance_to_entry_meters'.
            f"{stage}_distance_to_entry_meters": distance,
            # Store True under f'{stage}_stage_reached'.
            f"{stage}_stage_reached": True,
            # Store observed under f'{stage}_observed_at_trigger'.
            f"{stage}_observed_at_trigger": observed,
            # Store age under f'{stage}_observation_age_seconds'.
            f"{stage}_observation_age_seconds": age,
            # Store count under f'{stage}_history_count_at_trigger'.
            f"{stage}_history_count_at_trigger": count,
            # Store complete under f'{stage}_history_complete'.
            f"{stage}_history_complete": complete,
            # Store timing_valid under f'{stage}_history_timing_valid'.
            f"{stage}_history_timing_valid": timing_valid,
        })
        # Run this branch when status is a different object from None.
        if status is not None:
            # Set event[f'{stage}_stage_status'] to status.
            event[f"{stage}_stage_status"] = status
            # Return no value to the caller.
            return
        # Run this branch when the negation of observed.
        if not observed:
            # Set event[f'{stage}_stage_status'] to the text 'UNOBSERVED_AT_TRIGGER'.
            event[f"{stage}_stage_status"] = "UNOBSERVED_AT_TRIGGER"
            # Return no value to the caller.
            return
        # Run this branch when the negation of complete.
        if not complete:
            # Set event[f'{stage}_stage_status'] to the text 'INCOMPLETE_HISTORY'.
            event[f"{stage}_stage_status"] = "INCOMPLETE_HISTORY"
            # Return no value to the caller.
            return
        # Run this branch when the negation of timing_valid.
        if not timing_valid:
            # Set event[f'{stage}_stage_status'] to the text 'INVALID_HISTORY_TIMING'.
            event[f"{stage}_stage_status"] = "INVALID_HISTORY_TIMING"
            # Set event[f'{stage}_stage_error'] to timing_error.
            event[f"{stage}_stage_error"] = timing_error
            # Return no value to the caller.
            return
        # Attempt the enclosed operations and route matching exceptions to the handlers below.
        try:
            # Set event[stage] to the result of predictor.predict_stage(history, stage).
            event[stage] = predictor.predict_stage(history, stage)
        # Handle PredictionContractError as error using the recovery steps below.
        except PredictionContractError as error:
            # Set event[f'{stage}_stage_status'] to the text 'INVALID_HISTORY'.
            event[f"{stage}_stage_status"] = "INVALID_HISTORY"
            # Set event[f'{stage}_stage_error'] to a string built from error.
            event[f"{stage}_stage_error"] = str(error)
            # Return no value to the caller.
            return
        # Set event[f'{stage}_model_executed'] to True.
        event[f"{stage}_model_executed"] = True
        # Set event[f'{stage}_stage_status'] to the text 'PREDICTED'.
        event[f"{stage}_stage_status"] = "PREDICTED"

    # Process stage crossing using the inputs and processing steps below.
    # Input event: the supplied event.
    # Input stage: the supplied stage.
    # Input track: the supplied track.
    # Input current_time: the supplied current time.
    # Input eta: the supplied eta.
    # Input distance: the supplied distance.
    # Input predictor: the supplied predictor.
    # Output: no explicit value; normal completion returns None.
    # Processing: select branches using the stated conditions.
    def _process_stage_crossing(self, event, stage, track, current_time, eta,
                                # Declare distance, predictor as input parameters.
                                distance, predictor):
        # Run this branch when event at f'{stage}_triggered'.
        if event[f"{stage}_triggered"]:
            # Return no value to the caller.
            return
        # Set lead to the result of self._lead_time(stage).
        lead = self._lead_time(stage)
        # Set previous to event at 'previous_eta_seconds'.
        previous = event["previous_eta_seconds"]
        # Run this branch when previous is the same object as None.
        if previous is None:
            # Run this branch when the absolute value of eta minus lead is at most
            # CONFLICT_TRIGGER_TOLERANCE_SECONDS.
            if abs(eta - lead) <= CONFLICT_TRIGGER_TOLERANCE_SECONDS:
                # Call self._record_stage with the supplied arguments.
                self._record_stage(event, stage, track, current_time, eta, distance, predictor)
            # Run this branch when eta is less than lead minus CONFLICT_TRIGGER_TOLERANCE_SECONDS.
            elif eta < lead - CONFLICT_TRIGGER_TOLERANCE_SECONDS:
                # Call self._record_stage with the supplied arguments.
                self._record_stage(event, stage, track, current_time, eta, distance, predictor,
                                   "MISSED_LATE_FIRST_OBSERVATION")
            # Return no value to the caller.
            return
        # Run this branch when the negation of previous is greater than lead; is at least eta.
        if not (previous > lead >= eta):
            # Return no value to the caller.
            return
        # Run this branch when eta is less than lead minus CONFLICT_TRIGGER_TOLERANCE_SECONDS.
        if eta < lead - CONFLICT_TRIGGER_TOLERANCE_SECONDS:
            # Call self._record_stage with the supplied arguments.
            self._record_stage(event, stage, track, current_time, eta, distance, predictor,
                               "MISSED_ETA_JUMP")
        # Run this alternative branch when the preceding branch does not apply.
        else:
            # Call self._record_stage with the supplied arguments.
            self._record_stage(event, stage, track, current_time, eta, distance, predictor)

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Category using the inputs and processing steps below.
    # Input event: the supplied event.
    # Output: return the value selected by the matching return branch below.
    # Processing: select branches using the stated conditions.
    def _category(event):
        # Set primary_reached to event at 'primary_stage_reached'.
        primary_reached = event["primary_stage_reached"]
        # Set secondary_reached to event at 'secondary_stage_reached'.
        secondary_reached = event["secondary_stage_reached"]
        # Run this branch when the negation of primary_reached and the negation of secondary_reached.
        if not primary_reached and not secondary_reached:
            # Return the text 'CANCELLED_BEFORE_PRIMARY' to the caller.
            return "CANCELLED_BEFORE_PRIMARY"
        # Run this branch when event at 'primary_model_executed' or event at 'secondary_model_executed'.
        if event["primary_model_executed"] or event["secondary_model_executed"]:
            # Return the text 'MODEL_EVALUABLE' to the caller.
            return "MODEL_EVALUABLE"
        # Run this branch when primary_reached.
        if primary_reached:
            # Return the text 'PERCEPTION_INELIGIBLE' when event at 'primary_triggered', otherwise the text
            # 'INCOMPLETE_AFTER_PRIMARY' to the caller.
            return "PERCEPTION_INELIGIBLE" if event["primary_triggered"] else "INCOMPLETE_AFTER_PRIMARY"
        # Return the text 'INCOMPLETE_AFTER_PRIMARY' to the caller.
        return "INCOMPLETE_AFTER_PRIMARY"

    # Finalize event using the inputs and processing steps below.
    # Input pair: the supplied pair.
    # Input current_time: the supplied current time.
    # Input reason: the supplied reason.
    # Input predictor: the supplied predictor.
    # Output: result.
    def _finalize_event(self, pair, current_time, reason, predictor):
        # Set event to the result of self.events.pop(pair).
        event = self.events.pop(pair)
        # Add pair to self.completed_pairs.
        self.completed_pairs.add(pair)
        # Set (fused_label, fusion_status) to the result of predictor.fuse_stage_results(event at 'primary', event
        # at 'secondary').
        fused_label, fusion_status = predictor.fuse_stage_results(event["primary"], event["secondary"])
        # Set result to a dictionary of key mapped to value for (key, value) in key/value pairs from event; retain
        # entries satisfying key differs from the text 'previous_eta_seconds'.
        result = {key: value for key, value in event.items() if key != "previous_eta_seconds"}
        # Update result with the supplied entries.
        result.update({
            # Store a floating-point number built from current_time under 'finalization_time'.
            "finalization_time": float(current_time),
            # Store reason under 'finalization_reason'.
            "finalization_reason": reason,
            # Store the result of self._category(event) under 'event_category'.
            "event_category": self._category(event),
            # Store fused_label under 'fused_label'.
            "fused_label": fused_label,
            # Store fusion_status under 'status'.
            "status": fusion_status,
        })
        # Return result to the caller.
        return result

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Snapshot using the inputs and processing steps below.
    # Input event: the supplied event.
    # Output: a dictionary containing event_id, primary, secondary, fused_label, status.
    def _snapshot(event):
        # Return a dictionary containing event_id, primary, secondary, fused_label, status to the caller.
        return {"event_id": event["event_id"], "primary": event["primary"],
                # Store event at 'secondary' under 'secondary'.
                # Store UNKNOWN_LABEL under 'fused_label'.
                "secondary": event["secondary"], "fused_label": UNKNOWN_LABEL,
                "status": "WAITING_FOR_FINALIZATION"}

    # Update operational events with optional evaluation-only truth.
    # Input ldm: the supplied ldm.
    # Input current_time: the supplied current time.
    # Input predictor: the supplied predictor.
    # Input evaluation_route_truth: the supplied evaluation route truth.
    # Output: completed.
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    def update_ldm(self, ldm, current_time, predictor,
                   # Declare evaluation_route_truth as input parameter.
                   evaluation_route_truth=None):
        """Update operational events with optional evaluation-only truth.

        ``evaluation_route_truth`` is never written into an LDM track or sent
        to the predictor. It is copied only to finalized shadow-evaluation
        event records.
        """
        # Set evaluation_route_truth to evaluation_route_truth or an empty dictionary.
        evaluation_route_truth = evaluation_route_truth or {}
        # Set completed to an empty list.
        completed = []
        # Set present_ids to a set built from ldm.tracks.
        present_ids = set(ldm.tracks)
        # Finalize disappeared tracks before asking the LDM for currently
        # relevant objects; lightweight/test LDMs may not tolerate stale IDs.
        # Iterate over a list of pair for pair in self.events; retain entries satisfying pair at 0 equals
        # ldm.ego_id and pair at 1 does not belong to present_ids, binding each item to pair.
        for pair in [
            # Evaluate self.events as part of the enclosing expression.
            pair for pair in self.events
            # Evaluate pair at 0 equals ldm.ego_id and pair at 1 does not belong to present_ids as part of the
            # enclosing expression.
            if pair[0] == ldm.ego_id and pair[1] not in present_ids
        ]:
            # Append the result of self._finalize_event(pair, current_time, the text 'TRACK_LOST', predictor) to
            # completed.
            completed.append(
                # Supply the result of self._finalize_event(pair, current_time, the text 'TRACK_LOST', predictor)
                # to completed.append.
                self._finalize_event(
                    # Supply current_time to self._finalize_event.
                    pair, current_time, "TRACK_LOST", predictor
                )
            )
        # Set relevant_ids to a set built from the result of ldm.get_conflict_relevant_vehicles() when present_ids
        # minus a set containing ldm.ego_id, otherwise an empty set.
        relevant_ids = (
            # Evaluate a set built from the result of ldm.get_conflict_relevant_vehicles() when present_ids minus
            # a set containing ldm.ego_id, otherwise an empty set as part of the enclosing expression.
            set(ldm.get_conflict_relevant_vehicles())
            # Evaluate present_ids minus a set containing ldm.ego_id as part of the enclosing expression.
            if present_ids - {ldm.ego_id}
            # Evaluate an empty set as part of the enclosing expression.
            else set()
        )
        # Set ego to ldm.ego_id from ldm.tracks; use an empty dictionary if absent.
        ego = ldm.tracks.get(ldm.ego_id, {})
        # Set ego_incoming to 'road_id' from ego; use None if absent belongs to INCOMING_EDGE_IDS.
        ego_incoming = ego.get("road_id") in INCOMING_EDGE_IDS

        # Iterate over a list built from key/value pairs from ldm.tracks, binding each item to (target_id, track).
        for target_id, track in list(ldm.tracks.items()):
            # Run this branch when target_id equals ldm.ego_id.
            if target_id == ldm.ego_id:
                # Skip the rest of this loop iteration and process the next item.
                continue
            # Set pair to a tuple containing ldm.ego_id, target_id.
            pair = (ldm.ego_id, target_id)
            # Run this branch when pair belongs to self.completed_pairs.
            if pair in self.completed_pairs:
                # Skip the rest of this loop iteration and process the next item.
                continue
            # Set distance to the result of self.distance_to_conflict_entry(track).
            distance = self.distance_to_conflict_entry(track)
            # Run this branch when distance is the same object as None.
            if distance is None:
                # Run this branch when pair belongs to self.events.
                if pair in self.events:
                    # Append the result of self._finalize_event(pair, current_time, the text 'LEFT_INCOMING_EDGE',
                    # predictor) to completed.
                    completed.append(self._finalize_event(pair, current_time, "LEFT_INCOMING_EDGE", predictor))
                # Skip the rest of this loop iteration and process the next item.
                continue
            # Set eta to the result of self.estimate_time_to_entry(distance, 'speed' from track; use 0.0 if
            # absent).
            eta = self.estimate_time_to_entry(distance, track.get("speed", 0.0))
            # Set event to pair from self.events; use None if absent.
            event = self.events.get(pair)
            # Run this branch when event is the same object as None.
            if event is None:
                # Run this branch when the negation of ego_incoming and 'is_observed' from track; use False if
                # absent and target_id belongs to relevant_ids and eta is at most EVENT_ARMING_ETA_SECONDS.
                if not (ego_incoming and track.get("is_observed", False)
                        # Evaluate eta is at most EVENT_ARMING_ETA_SECONDS as part of the enclosing expression.
                        and target_id in relevant_ids and eta <= EVENT_ARMING_ETA_SECONDS):
                    # Skip the rest of this loop iteration and process the next item.
                    continue
                # Set event to the result of self._new_event(ldm.ego_id, target_id, track, current_time).
                event = self._new_event(ldm.ego_id, target_id, track, current_time)
                # Set event['ground_truth_route_id'] to target_id from evaluation_route_truth; use the text '' if
                # absent.
                event["ground_truth_route_id"] = evaluation_route_truth.get(
                    # Supply target_id to evaluation_route_truth.get.
                    target_id, ""
                )
                # Set self.events[pair] to event.
                self.events[pair] = event
            # Set count to the number of entries in 'position_history' from track; use an empty tuple if absent.
            count = len(track.get("position_history", ()))
            # Set event['latest_estimated_eta'] to eta when whether eta contains finite numeric values, otherwise
            # None.
            event["latest_estimated_eta"] = eta if math.isfinite(eta) else None
            # Set event['latest_observation_age'] to the maximum of 0.0, a floating-point number built from
            # current_time minus a floating-point number built from...
            event["latest_observation_age"] = max(0.0, float(current_time) - float(track.get("last_observed_time", current_time)))
            # Set event['latest_history_count'] to count.
            event["latest_history_count"] = count
            # Set event['maximum_history_count'] to the maximum of event at 'maximum_history_count', count.
            event["maximum_history_count"] = max(event["maximum_history_count"], count)
            # Call self._process_stage_crossing with the supplied arguments.
            self._process_stage_crossing(event, "primary", track, current_time, eta, distance, predictor)
            # Call self._process_stage_crossing with the supplied arguments.
            self._process_stage_crossing(event, "secondary", track, current_time, eta, distance, predictor)
            # Set track['intention_prediction'] to the result of self._snapshot(event).
            track["intention_prediction"] = self._snapshot(event)
            # Run this branch when event at 'secondary_triggered'.
            if event["secondary_triggered"]:
                # Set done to the result of self._finalize_event(pair, current_time, the text
                # 'SECONDARY_STAGE_REACHED', predictor).
                done = self._finalize_event(pair, current_time, "SECONDARY_STAGE_REACHED", predictor)
                # Set track['intention_prediction'] to done.
                track["intention_prediction"] = done
                # Append done to completed.
                completed.append(done)
            # Run this alternative branch when the preceding branch does not apply.
            else:
                # Set event['previous_eta_seconds'] to eta.
                event["previous_eta_seconds"] = eta

        # Return completed to the caller.
        return completed

    # Finalize all using the inputs and processing steps below.
    # Input current_time: the supplied current time.
    # Input predictor: the supplied predictor.
    # Input reason: the supplied reason.
    # Output: a list of the result of self._finalize_event(pair, current_time, reason, predictor) for pair in a
    # list built from self.events.
    def finalize_all(self, current_time, predictor, reason="SIMULATION_END"):
        # Return a list of the result of self._finalize_event(pair, current_time, reason, predictor) for pair in a
        # list built from self.events to the caller.
        return [self._finalize_event(pair, current_time, reason, predictor)
                # Evaluate a list built from self.events as part of the enclosing expression.
                for pair in list(self.events)]


# Set conflict_entry_monitor to the result of ConflictEntryMonitor().
conflict_entry_monitor = ConflictEntryMonitor()
