"""Route-independent conflict-entry timing for shadow prediction events."""

import math

from config import (
    CONFLICT_TRIGGER_TOLERANCE_SECONDS,
    EVENT_ARMING_ETA_SECONDS,
    INCOMING_EDGE_IDS,
    MIN_ETA_SPEED_MPS,
    MODEL_HISTORY_LENGTH,
    PRIMARY_PREDICTION_LEAD_TIME_SECONDS,
    SECONDARY_PREDICTION_LEAD_TIME_SECONDS,
)
from predictor import IntentionPredictor, PredictionContractError, UNKNOWN_LABEL


class ConflictEntryMonitor:
    """Manage at most one primary and secondary call per ego-target approach."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.events = {}
        self.completed_pairs = set()
        self.next_event_number = 1

    @staticmethod
    def distance_to_conflict_entry(track):
        if track.get("road_id") not in INCOMING_EDGE_IDS:
            return None
        position = float(track.get("lane_position", 0.0))
        length = float(track.get("lane_length", 0.0))
        if not math.isfinite(position) or not math.isfinite(length) or length <= 0:
            return None
        return max(0.0, length - position)

    @staticmethod
    def estimate_time_to_entry(distance, speed):
        speed = float(speed)
        if distance is None or not math.isfinite(distance) or not math.isfinite(speed) or speed < MIN_ETA_SPEED_MPS:
            return math.inf
        return max(0.0, float(distance) / speed)

    @staticmethod
    def _lead_time(stage):
        return (PRIMARY_PREDICTION_LEAD_TIME_SECONDS if stage == "primary"
                else SECONDARY_PREDICTION_LEAD_TIME_SECONDS)

    def _new_event(self, ego_id, target_id, track, current_time):
        event = {
            "event_id": f"event_{self.next_event_number:06d}_{ego_id}_{target_id}",
            "ego_id": ego_id,
            "target_id": target_id,
            "event_start_time": float(current_time),
            # Copied only for finalized evaluation/debug output.
            # Evaluation-only truth is held outside operational LDM tracks.
            "ground_truth_route_id": "",
            "previous_eta_seconds": None,
            "latest_estimated_eta": None,
            "latest_observation_age": None,
            "latest_history_count": len(track.get("position_history", ())),
            "maximum_history_count": len(track.get("position_history", ())),
        }
        for stage in ("primary", "secondary"):
            event.update({
                f"{stage}_triggered": False,
                f"{stage}_trigger_time": None,
                f"{stage}_trigger_eta_seconds": None,
                f"{stage}_distance_to_entry_meters": None,
                f"{stage}_stage_reached": False,
                f"{stage}_observed_at_trigger": None,
                f"{stage}_observation_age_seconds": None,
                f"{stage}_history_count_at_trigger": None,
                f"{stage}_history_complete": None,
                f"{stage}_history_timing_valid": None,
                f"{stage}_model_executed": False,
                f"{stage}_stage_status": "NOT_REACHED",
                f"{stage}_stage_error": "",
                stage: None,
            })
        self.next_event_number += 1
        return event

    @staticmethod
    def _history_timing_valid(history):
        if len(history) != MODEL_HISTORY_LENGTH:
            return False, ""
        try:
            IntentionPredictor._history_arrays(history)
            return True, ""
        except PredictionContractError as error:
            return False, str(error)

    def _record_stage(self, event, stage, track, current_time, eta, distance,
                      predictor, status=None):
        history = track.get("position_history", ())
        count = len(history)
        observed = bool(track.get("is_observed", False))
        age = max(0.0, float(current_time) - float(track.get("last_observed_time", current_time)))
        complete = count == MODEL_HISTORY_LENGTH
        timing_valid, timing_error = self._history_timing_valid(history)
        event.update({
            f"{stage}_triggered": True,
            f"{stage}_trigger_time": float(current_time),
            f"{stage}_trigger_eta_seconds": float(eta) if math.isfinite(eta) else None,
            f"{stage}_distance_to_entry_meters": distance,
            f"{stage}_stage_reached": True,
            f"{stage}_observed_at_trigger": observed,
            f"{stage}_observation_age_seconds": age,
            f"{stage}_history_count_at_trigger": count,
            f"{stage}_history_complete": complete,
            f"{stage}_history_timing_valid": timing_valid,
        })
        if status is not None:
            event[f"{stage}_stage_status"] = status
            return
        if not observed:
            event[f"{stage}_stage_status"] = "UNOBSERVED_AT_TRIGGER"
            return
        if not complete:
            event[f"{stage}_stage_status"] = "INCOMPLETE_HISTORY"
            return
        if not timing_valid:
            event[f"{stage}_stage_status"] = "INVALID_HISTORY_TIMING"
            event[f"{stage}_stage_error"] = timing_error
            return
        try:
            event[stage] = predictor.predict_stage(history, stage)
        except PredictionContractError as error:
            event[f"{stage}_stage_status"] = "INVALID_HISTORY"
            event[f"{stage}_stage_error"] = str(error)
            return
        event[f"{stage}_model_executed"] = True
        event[f"{stage}_stage_status"] = "PREDICTED"

    def _process_stage_crossing(self, event, stage, track, current_time, eta,
                                distance, predictor):
        if event[f"{stage}_triggered"]:
            return
        lead = self._lead_time(stage)
        previous = event["previous_eta_seconds"]
        if previous is None:
            if abs(eta - lead) <= CONFLICT_TRIGGER_TOLERANCE_SECONDS:
                self._record_stage(event, stage, track, current_time, eta, distance, predictor)
            elif eta < lead - CONFLICT_TRIGGER_TOLERANCE_SECONDS:
                self._record_stage(event, stage, track, current_time, eta, distance, predictor,
                                   "MISSED_LATE_FIRST_OBSERVATION")
            return
        if not (previous > lead >= eta):
            return
        if eta < lead - CONFLICT_TRIGGER_TOLERANCE_SECONDS:
            self._record_stage(event, stage, track, current_time, eta, distance, predictor,
                               "MISSED_ETA_JUMP")
        else:
            self._record_stage(event, stage, track, current_time, eta, distance, predictor)

    @staticmethod
    def _category(event):
        primary_reached = event["primary_stage_reached"]
        secondary_reached = event["secondary_stage_reached"]
        if not primary_reached and not secondary_reached:
            return "CANCELLED_BEFORE_PRIMARY"
        if event["primary_model_executed"] or event["secondary_model_executed"]:
            return "MODEL_EVALUABLE"
        if primary_reached:
            return "PERCEPTION_INELIGIBLE" if event["primary_triggered"] else "INCOMPLETE_AFTER_PRIMARY"
        return "INCOMPLETE_AFTER_PRIMARY"

    def _finalize_event(self, pair, current_time, reason, predictor):
        event = self.events.pop(pair)
        self.completed_pairs.add(pair)
        fused_label, fusion_status = predictor.fuse_stage_results(event["primary"], event["secondary"])
        result = {key: value for key, value in event.items() if key != "previous_eta_seconds"}
        result.update({
            "finalization_time": float(current_time),
            "finalization_reason": reason,
            "event_category": self._category(event),
            "fused_label": fused_label,
            "status": fusion_status,
        })
        return result

    @staticmethod
    def _snapshot(event):
        return {"event_id": event["event_id"], "primary": event["primary"],
                "secondary": event["secondary"], "fused_label": UNKNOWN_LABEL,
                "status": "WAITING_FOR_FINALIZATION"}

    def update_ldm(self, ldm, current_time, predictor):
        completed = []
        present_ids = set(ldm.tracks)
        # Finalize disappeared tracks before asking the LDM for currently
        # relevant objects; lightweight/test LDMs may not tolerate stale IDs.
        for pair in [
            pair for pair in self.events
            if pair[0] == ldm.ego_id and pair[1] not in present_ids
        ]:
            completed.append(
                self._finalize_event(
                    pair, current_time, "TRACK_LOST", predictor
                )
            )
        relevant_ids = (
            set(ldm.get_conflict_relevant_vehicles())
            if present_ids - {ldm.ego_id}
            else set()
        )
        ego = ldm.tracks.get(ldm.ego_id, {})
        ego_incoming = ego.get("road_id") in INCOMING_EDGE_IDS

        for target_id, track in list(ldm.tracks.items()):
            if target_id == ldm.ego_id:
                continue
            pair = (ldm.ego_id, target_id)
            if pair in self.completed_pairs:
                continue
            distance = self.distance_to_conflict_entry(track)
            if distance is None:
                if pair in self.events:
                    completed.append(self._finalize_event(pair, current_time, "LEFT_INCOMING_EDGE", predictor))
                continue
            eta = self.estimate_time_to_entry(distance, track.get("speed", 0.0))
            event = self.events.get(pair)
            if event is None:
                if not (ego_incoming and track.get("is_observed", False)
                        and target_id in relevant_ids and eta <= EVENT_ARMING_ETA_SECONDS):
                    continue
                event = self._new_event(ldm.ego_id, target_id, track, current_time)
                event["ground_truth_route_id"] = getattr(
                    ldm, "evaluation_route_truth", {}
                ).get(target_id, "")
                self.events[pair] = event
            count = len(track.get("position_history", ()))
            event["latest_estimated_eta"] = eta if math.isfinite(eta) else None
            event["latest_observation_age"] = max(0.0, float(current_time) - float(track.get("last_observed_time", current_time)))
            event["latest_history_count"] = count
            event["maximum_history_count"] = max(event["maximum_history_count"], count)
            self._process_stage_crossing(event, "primary", track, current_time, eta, distance, predictor)
            self._process_stage_crossing(event, "secondary", track, current_time, eta, distance, predictor)
            track["intention_prediction"] = self._snapshot(event)
            if event["secondary_triggered"]:
                done = self._finalize_event(pair, current_time, "SECONDARY_STAGE_REACHED", predictor)
                track["intention_prediction"] = done
                completed.append(done)
            else:
                event["previous_eta_seconds"] = eta

        return completed

    def finalize_all(self, current_time, predictor, reason="SIMULATION_END"):
        return [self._finalize_event(pair, current_time, reason, predictor)
                for pair in list(self.events)]


conflict_entry_monitor = ConflictEntryMonitor()
