"""Traffic metrics plus eligibility-aware shadow-model evaluation."""

# Import csv for use in this module.
import csv
# Import defaultdict from collections for the operations below.
from collections import defaultdict

# Import numpy as np for use in this module.
import numpy as np
# Import traci for use in this module.
import traci

# Import DEADLOCK_DURATION_SECONDS, OUTPUT_DIR, SIM_TIME_STEP, STOPPED_SPEED_THRESHOLD_MPS from config for the
# operations below.
from config import DEADLOCK_DURATION_SECONDS, OUTPUT_DIR, SIM_TIME_STEP, STOPPED_SPEED_THRESHOLD_MPS

# Set CLASS_LABELS to a tuple containing the text 'LEFT', the text 'RIGHT', the text 'STRAIGHT'.
CLASS_LABELS = ("LEFT", "RIGHT", "STRAIGHT")
# Set FEATURE_NAMES to a tuple containing the text 'speed', the text 'acceleration_magnitude', the text
# 'longitudinal_velocity', the text...
FEATURE_NAMES = ("speed", "acceleration_magnitude", "longitudinal_velocity",
                 "lateral_velocity", "longitudinal_acceleration", "lateral_acceleration")


# Define Evaluator to group the state and operations declared below.
# Instances expose the attributes and methods implemented in this class.
class Evaluator:
    # Initialize the instance attributes and collaborators used by the operations below.
    # Output: no explicit value; normal completion returns None.
    def __init__(self):
        # Create the directory requested by OUTPUT_DIR.
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        # Call self.reset with the supplied arguments.
        self.reset()

    # Reset using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    def reset(self):
        # Set self.collision_events to 0.
        self.collision_events = 0
        # Set self.total_travel_time to 0.0.
        self.total_travel_time = 0.0
        # Set self.successful_crossings to 0.
        self.successful_crossings = 0
        # Set self.step_count to 0.
        self.step_count = 0
        # Set self.av_speeds_history to an empty list.
        self.av_speeds_history = []
        # Set self.vehicle_departure_times to an empty dictionary.
        self.vehicle_departure_times = {}
        # Set self.stopped_duration to the result of defaultdict(float).
        self.stopped_duration = defaultdict(float)
        # Set self.deadlocked_vehicle_ids to an empty set.
        self.deadlocked_vehicle_ids = set()
        # Set self.prediction_rows to an empty list.
        self.prediction_rows = []
        # Set self.safety_score to 100.0.
        self.safety_score = 100.0
        # Set self.deadlock_rate and self.throughput and self.avg_av_speed to 0.0.
        self.deadlock_rate = self.throughput = self.avg_av_speed = 0.0
        # Set self.total_collisions and self.avg_travel_time to 0.0.
        self.total_collisions = self.avg_travel_time = 0.0

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Route to label using the inputs and processing steps below.
    # Input route_id: the supplied route id.
    # Output: return the value selected by the matching return branch below.
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    def _route_to_label(route_id):
        # Set lowered to the result of str(route_id).lower().
        lowered = str(route_id).lower()
        # Iterate over a tuple containing the text 'left', the text 'right', the text 'straight', binding each
        # item to label.
        for label in ("left", "right", "straight"):
            # Run this branch when the result of lowered.endswith(the text '_' plus label).
            if lowered.endswith("_" + label):
                # Return the result of label.upper() to the caller.
                return label.upper()
        # Return the text '' to the caller.
        return ""

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Stage columns using the inputs and processing steps below.
    # Input stage: the supplied stage.
    # Input result: the supplied result.
    # Output: return the value selected by the matching return branch below.
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    def _stage_columns(stage, result):
        # Set values to an empty dictionary.
        values = {}
        # Set scalar_names to a tuple containing the text 'predicted_class', the text 'label', the text
        # 'confidence', the text 'threshold', the text 'accepted'.
        scalar_names = ("predicted_class", "label", "confidence", "threshold", "accepted")
        # Run this branch when result is the same object as None.
        if result is None:
            # Iterate over scalar_names, binding each item to name.
            for name in scalar_names:
                # Set values[f'{stage}_{name}'] to False when name equals the text 'accepted', otherwise the text
                # ''.
                values[f"{stage}_{name}"] = False if name == "accepted" else ""
            # Iterate over CLASS_LABELS, binding each item to label.
            for label in CLASS_LABELS:
                # Set values[f'{stage}_probability_{label.lower()}'] to the text ''.
                values[f"{stage}_probability_{label.lower()}"] = ""
            # Set values[f'{stage}_maximum_absolute_z_score'] to the text ''.
            values[f"{stage}_maximum_absolute_z_score"] = ""
            # Iterate over FEATURE_NAMES, binding each item to name.
            for name in FEATURE_NAMES:
                # Set values[f'{stage}_mean_{name}'] to the text ''.
                values[f"{stage}_mean_{name}"] = ""
                # Set values[f'{stage}_max_abs_z_{name}'] to the text ''.
                values[f"{stage}_max_abs_z_{name}"] = ""
            # Return values to the caller.
            return values
        # Iterate over scalar_names, binding each item to name.
        for name in scalar_names:
            # Set values[f'{stage}_{name}'] to result at name.
            values[f"{stage}_{name}"] = result[name]
        # Iterate over CLASS_LABELS, binding each item to label.
        for label in CLASS_LABELS:
            # Set values[f'{stage}_probability_{label.lower()}'] to result['probabilities'] at label.
            values[f"{stage}_probability_{label.lower()}"] = result["probabilities"][label]
        # Set diagnostics to result at 'feature_diagnostics'.
        diagnostics = result["feature_diagnostics"]
        # Set values[f'{stage}_maximum_absolute_z_score'] to diagnostics at 'maximum_absolute_z_score'.
        values[f"{stage}_maximum_absolute_z_score"] = diagnostics["maximum_absolute_z_score"]
        # Iterate over FEATURE_NAMES, binding each item to name.
        for name in FEATURE_NAMES:
            # Set values[f'{stage}_mean_{name}'] to diagnostics['raw_feature_means'] at name.
            values[f"{stage}_mean_{name}"] = diagnostics["raw_feature_means"][name]
            # Set values[f'{stage}_max_abs_z_{name}'] to diagnostics['maximum_absolute_z_score_by_feature'] at
            # name.
            values[f"{stage}_max_abs_z_{name}"] = diagnostics["maximum_absolute_z_score_by_feature"][name]
        # Return values to the caller.
        return values

    # Record prediction events using the inputs and processing steps below.
    # Input events: the supplied events.
    # Output: no explicit value; normal completion returns None.
    # Processing: iterate over the relevant records.
    def record_prediction_events(self, events):
        # Iterate over events, binding each item to event.
        for event in events:
            # Set truth to the result of self._route_to_label('ground_truth_route_id' from event; use the text ''
            # if absent).
            truth = self._route_to_label(event.get("ground_truth_route_id", ""))
            # Set row to a dictionary containing event_id, event_start_time, finalization_time,
            # finalization_reason, event_category,...
            row = {
                # Store event at 'event_id' under 'event_id'.
                # Store event at 'event_start_time' under 'event_start_time'.
                "event_id": event["event_id"], "event_start_time": event["event_start_time"],
                # Store event at 'finalization_time' under 'finalization_time'.
                # Store event at 'finalization_reason' under 'finalization_reason'.
                "finalization_time": event["finalization_time"], "finalization_reason": event["finalization_reason"],
                # Store event at 'event_category' under 'event_category'.
                # Store event at 'ego_id' under 'ego_id'.
                # Store event at 'target_id' under 'target_id'.
                "event_category": event["event_category"], "ego_id": event["ego_id"], "target_id": event["target_id"],
                # Store 'ground_truth_route_id' from event; use the text '' if absent under
                # 'ground_truth_route_id_debug'.
                "ground_truth_route_id_debug": event.get("ground_truth_route_id", ""),
                # Store truth under 'ground_truth_label_debug'.
                "ground_truth_label_debug": truth,
                # Store 'latest_history_count' from event; use None if absent under 'latest_history_count'.
                "latest_history_count": event.get("latest_history_count"),
                # Store 'maximum_history_count' from event; use None if absent under 'maximum_history_count'.
                "maximum_history_count": event.get("maximum_history_count"),
                # Store 'latest_estimated_eta' from event; use None if absent under 'latest_estimated_eta'.
                "latest_estimated_eta": event.get("latest_estimated_eta"),
                # Store 'latest_observation_age' from event; use None if absent under 'latest_observation_age'.
                "latest_observation_age": event.get("latest_observation_age"),
            }
            # Iterate over a tuple containing the text 'primary', the text 'secondary', binding each item to
            # stage.
            for stage in ("primary", "secondary"):
                # Set result to stage from event; use None if absent.
                result = event.get(stage)
                # Iterate over a tuple containing the text 'trigger_time', the text 'trigger_eta_seconds', the
                # text 'distance_to_entry_meters', the text..., binding each item to name.
                for name in ("trigger_time", "trigger_eta_seconds", "distance_to_entry_meters",
                             "stage_reached", "observed_at_trigger", "observation_age_seconds",
                             "history_count_at_trigger", "history_complete", "history_timing_valid",
                             "model_executed", "stage_status", "stage_error"):
                    # Set row[f'{stage}_{name}'] to f'{stage}_{name}' from event; use None if absent.
                    row[f"{stage}_{name}"] = event.get(f"{stage}_{name}")
                # Set row[f'{stage}_correct_when_accepted'] to a Boolean built from result and result at
                # 'accepted' and truth and result at 'label' equals truth.
                row[f"{stage}_correct_when_accepted"] = bool(result and result["accepted"] and truth and result["label"] == truth)
                # Update row with the supplied entries.
                row.update(self._stage_columns(stage, result))
            # Set fused_executed to a Boolean built from row at 'primary_model_executed' and row at
            # 'secondary_model_executed'.
            fused_executed = bool(row["primary_model_executed"] and row["secondary_model_executed"])
            # Set fused_label to 'fused_label' from event; use the text 'UNKNOWN' if absent.
            fused_label = event.get("fused_label", "UNKNOWN")
            # Update row with the supplied entries.
            row.update({
                # Store a Boolean built from row at 'primary_stage_reached' and row at 'secondary_stage_reached'
                # under 'fused_stage_reached'.
                "fused_stage_reached": bool(row["primary_stage_reached"] and row["secondary_stage_reached"]),
                # Store fused_executed under 'fused_model_executed'.
                "fused_model_executed": fused_executed,
                # Store the text 'PREDICTED' when fused_executed, otherwise the text 'INCOMPLETE' under
                # 'fused_stage_status'.
                "fused_stage_status": "PREDICTED" if fused_executed else "INCOMPLETE",
                # Store fused_label under 'fused_label'.
                # Store event at 'status' under 'fusion_status'.
                "fused_label": fused_label, "fusion_status": event["status"],
                # Store fused_executed and fused_label differs from the text 'UNKNOWN' under 'fused_accepted'.
                "fused_accepted": fused_executed and fused_label != "UNKNOWN",
                # Store fused_executed and fused_label differs from the text 'UNKNOWN' and a Boolean built from
                # truth and fused_label equals truth under 'fused_correct_when_accepted'.
                "fused_correct_when_accepted": fused_executed and fused_label != "UNKNOWN" and bool(truth) and fused_label == truth,
            })
            # Append row to self.prediction_rows.
            self.prediction_rows.append(row)

    # Update collisions using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    # Processing: select branches using the stated conditions, then handle the specified errors.
    def _update_collisions(self):
        # Attempt the enclosed operations and route matching exceptions to the handlers below.
        try:
            # Update self.collision_events to its current value plus the number of entries in the result of
            # traci.simulation.getCollisions().
            self.collision_events += len(traci.simulation.getCollisions())
        # Handle (AttributeError, traci.TraCIException) using the recovery steps below.
        except (AttributeError, traci.TraCIException):
            # Run this branch when the result of traci.simulation.getCollidingVehiclesNumber() is greater than 0.
            if traci.simulation.getCollidingVehiclesNumber() > 0:
                # Update self.collision_events to its current value plus 1.
                self.collision_events += 1

    # Update using the inputs and processing steps below.
    # Input current_time: the supplied current time.
    # Input observations: the supplied observations.
    # Input lifecycle_events: the supplied lifecycle events.
    # Output: no explicit value; normal completion returns None.
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    def update(self, current_time, observations, lifecycle_events=None):
        # Update self.step_count to its current value plus 1.
        self.step_count += 1
        # Call self._update_collisions with the supplied arguments.
        self._update_collisions()
        # Set active to a set built from observations.
        active = set(observations)
        # Iterate over a list built from self.stopped_duration, binding each item to vehicle_id.
        for vehicle_id in list(self.stopped_duration):
            # Run this branch when vehicle_id does not belong to active.
            if vehicle_id not in active:
                # Delete self.stopped_duration[vehicle_id] from its containing namespace or collection.
                del self.stopped_duration[vehicle_id]
        # Iterate over key/value pairs from observations, binding each item to (vehicle_id, state).
        for vehicle_id, state in observations.items():
            # Run this branch when 'vel' from state; use 0.0 if absent is less than STOPPED_SPEED_THRESHOLD_MPS.
            if state.get("vel", 0.0) < STOPPED_SPEED_THRESHOLD_MPS:
                # Update self.stopped_duration[vehicle_id] to its current value plus SIM_TIME_STEP.
                self.stopped_duration[vehicle_id] += SIM_TIME_STEP
                # Run this branch when self.stopped_duration at vehicle_id is at least DEADLOCK_DURATION_SECONDS.
                if self.stopped_duration[vehicle_id] >= DEADLOCK_DURATION_SECONDS:
                    # Add vehicle_id to self.deadlocked_vehicle_ids.
                    self.deadlocked_vehicle_ids.add(vehicle_id)
            # Run this alternative branch when the preceding branch does not apply.
            else:
                # Set self.stopped_duration[vehicle_id] to 0.0.
                self.stopped_duration[vehicle_id] = 0.0
                # Discard vehicle_id from self.deadlocked_vehicle_ids if present.
                self.deadlocked_vehicle_ids.discard(vehicle_id)
        # Extend self.av_speeds_history with a lazy sequence of 'vel' from state; use 0.0 if absent for (vid,
        # state) in key/value pairs from observations; retain entries satisfying the result of vid.startswith(the
        # text 'AV_').
        self.av_speeds_history.extend(state.get("vel", 0.0) for vid, state in observations.items() if vid.startswith("AV_"))
        # Iterate over the identifiers reported by traci.vehicle.getIDList, binding each item to vid.
        for vid in traci.vehicle.getIDList():
            # Call self.vehicle_departure_times.setdefault with the supplied arguments.
            self.vehicle_departure_times.setdefault(vid, float(current_time))
        # Set arrived_ids to lifecycle_events.arrived_vehicle_ids when lifecycle_events is a different object from
        # None, otherwise the result of traci.simulation.getArrivedIDList().
        arrived_ids = (lifecycle_events.arrived_vehicle_ids
                       # Evaluate lifecycle_events is a different object from None as part of the enclosing
                       # expression.
                       if lifecycle_events is not None else
                       # Evaluate the result of traci.simulation.getArrivedIDList() as part of the enclosing
                       # expression.
                       traci.simulation.getArrivedIDList())
        # Iterate over arrived_ids, binding each item to vid.
        for vid in arrived_ids:
            # Set departure to the result of self.vehicle_departure_times.pop(vid, None).
            departure = self.vehicle_departure_times.pop(vid, None)
            # Run this branch when departure is a different object from None.
            if departure is not None:
                # Update self.total_travel_time to its current value plus a floating-point number built from
                # current_time minus departure.
                self.total_travel_time += float(current_time) - departure
                # Update self.successful_crossings to its current value plus 1.
                self.successful_crossings += 1
        # Set self.total_collisions to self.collision_events.
        self.total_collisions = self.collision_events
        # Set self.safety_score to the maximum of 0.0, 100.0 minus 15.0 multiplied by self.collision_events.
        self.safety_score = max(0.0, 100.0 - 15.0 * self.collision_events)
        # Set self.avg_av_speed to a floating-point number built from the result of
        # np.mean(self.av_speeds_history) when self.av_speeds_history, otherwise 0.0.
        self.avg_av_speed = float(np.mean(self.av_speeds_history)) if self.av_speeds_history else 0.0
        # Set self.deadlock_rate to the number of entries in self.deadlocked_vehicle_ids divided by the maximum of
        # 1, the number of entries in observations.
        self.deadlock_rate = len(self.deadlocked_vehicle_ids) / max(1, len(observations))
        # Set self.throughput to self.successful_crossings divided by the maximum of a floating-point number built
        # from current_time, SIM_TIME_STEP.
        self.throughput = self.successful_crossings / max(float(current_time), SIM_TIME_STEP)
        # Set self.avg_travel_time to self.total_travel_time divided by the maximum of 1,
        # self.successful_crossings.
        self.avg_travel_time = self.total_travel_time / max(1, self.successful_crossings)

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Ratio using the inputs and processing steps below.
    # Input numerator: the supplied numerator.
    # Input denominator: the supplied denominator.
    # Output: None when denominator equals 0, otherwise numerator divided by denominator.
    def _ratio(numerator, denominator):
        # Return None when denominator equals 0, otherwise numerator divided by denominator to the caller.
        return None if denominator == 0 else numerator / denominator

    # Classification metrics using the inputs and processing steps below.
    # Input stage: the supplied stage.
    # Output: a dictionary containing model_count, acceptance, accuracy, balanced, macro_f1.
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    def _classification_metrics(self, stage):
        # Set model_rows to a list of row for row in self.prediction_rows; retain entries satisfying row at
        # f'{stage}_model_executed' and row at 'ground_truth_label_debug'.
        model_rows = [row for row in self.prediction_rows if row[f"{stage}_model_executed"] and row["ground_truth_label_debug"]]
        # Set accepted to a list of row for row in model_rows; retain entries satisfying row at
        # f'{stage}_accepted'.
        accepted = [row for row in model_rows if row[f"{stage}_accepted"]]
        # Set correct to the sum of a lazy sequence of row at f'{stage}_label' equals row at
        # 'ground_truth_label_debug' for row in accepted.
        correct = sum(row[f"{stage}_label"] == row["ground_truth_label_debug"] for row in accepted)
        # Set (recalls, f1s) to a tuple containing an empty list, an empty list.
        recalls, f1s = [], []
        # Iterate over CLASS_LABELS, binding each item to label.
        for label in CLASS_LABELS:
            # Set tp to the sum of a lazy sequence of r['ground_truth_label_debug'] equals label and
            # r[f'{stage}_label'] equals label for r in model_rows.
            tp = sum(r["ground_truth_label_debug"] == label and r[f"{stage}_label"] == label for r in model_rows)
            # Set fp to the sum of a lazy sequence of r['ground_truth_label_debug'] differs from label and
            # r[f'{stage}_label'] equals label for r in model_rows.
            fp = sum(r["ground_truth_label_debug"] != label and r[f"{stage}_label"] == label for r in model_rows)
            # Set fn to the sum of a lazy sequence of r['ground_truth_label_debug'] equals label and
            # r[f'{stage}_label'] differs from label for r in model_rows.
            fn = sum(r["ground_truth_label_debug"] == label and r[f"{stage}_label"] != label for r in model_rows)
            # Set recall to the result of self._ratio(tp, tp plus fn).
            recall = self._ratio(tp, tp + fn)
            # Set precision to the result of self._ratio(tp, tp plus fp).
            precision = self._ratio(tp, tp + fp)
            # Run this branch when recall is a different object from None.
            if recall is not None:
                # Append recall to recalls.
                recalls.append(recall)
            # Append 0.0 when precision is the same object as None or recall is the same object as None or
            # precision plus recall equals 0, otherwise 2 multiplied by precision multiplied by recall divided by
            # precision plus recall to f1s.
            f1s.append(0.0 if precision is None or recall is None or precision + recall == 0 else 2 * precision * recall / (precision + recall))
        # Return a dictionary containing model_count, acceptance, accuracy, balanced, macro_f1 to the caller.
        return {"model_count": len(model_rows), "acceptance": self._ratio(len(accepted), len(model_rows)),
                # Store the result of self._ratio(correct, the number of entries in accepted) under 'accuracy'.
                "accuracy": self._ratio(correct, len(accepted)),
                # Store a floating-point number built from the result of np.mean(recalls) when model_rows and
                # recalls, otherwise None under 'balanced'.
                "balanced": float(np.mean(recalls)) if model_rows and recalls else None,
                # Store a floating-point number built from the result of np.mean(f1s) when model_rows, otherwise
                # None under 'macro_f1'.
                "macro_f1": float(np.mean(f1s)) if model_rows else None}

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Rounded using the inputs and processing steps below.
    # Input value: the supplied value.
    # Output: None when value is the same object as None, otherwise the rounded value of value.
    def _rounded(value):
        # Return None when value is the same object as None, otherwise the rounded value of value to the caller.
        return None if value is None else round(value, 4)

    # Compute metrics using the inputs and processing steps below.
    # Input simulation_time: the supplied simulation time.
    # Output: metrics.
    # Processing: iterate over the relevant records.
    def compute_metrics(self, simulation_time):
        # Set total to the number of entries in self.prediction_rows.
        total = len(self.prediction_rows)
        # Set metrics to a dictionary containing Safety_Score, Deadlock_Rate, Throughput_Vehicles_Per_Second,
        # Avg_AV_Speed,...
        metrics = {
            # Store the rounded value of self.safety_score under 'Safety_Score'.
            # Store the rounded value of self.deadlock_rate under 'Deadlock_Rate'.
            "Safety_Score": round(self.safety_score, 2), "Deadlock_Rate": round(self.deadlock_rate, 4),
            # Store the rounded value of self.successful_crossings divided by the maximum of simulation_time,
            # SIM_TIME_STEP under 'Throughput_Vehicles_Per_Second'.
            "Throughput_Vehicles_Per_Second": round(self.successful_crossings / max(simulation_time, SIM_TIME_STEP), 4),
            # Store the rounded value of self.avg_av_speed under 'Avg_AV_Speed'.
            # Store self.collision_events under 'Total_Collision_Events'.
            "Avg_AV_Speed": round(self.avg_av_speed, 2), "Total_Collision_Events": self.collision_events,
            # Store self.successful_crossings under 'Successful_Crossings'.
            # Store the rounded value of self.avg_travel_time under 'Avg_Travel_Time'.
            "Successful_Crossings": self.successful_crossings, "Avg_Travel_Time": round(self.avg_travel_time, 2),
            # Store total under 'Finalized_Candidate_Events'.
            "Finalized_Candidate_Events": total,
            # Store the sum of a lazy sequence of r at 'event_category' equals the text 'CANCELLED_BEFORE_PRIMARY'
            # for r in self.prediction_rows under 'Cancelled_Before_Primary'.
            "Cancelled_Before_Primary": sum(r["event_category"] == "CANCELLED_BEFORE_PRIMARY" for r in self.prediction_rows),
            # Store the sum of a lazy sequence of r at 'event_category' equals the text 'PERCEPTION_INELIGIBLE'
            # for r in self.prediction_rows under 'Perception_Ineligible_Events'.
            "Perception_Ineligible_Events": sum(r["event_category"] == "PERCEPTION_INELIGIBLE" for r in self.prediction_rows),
            # Store the sum of a lazy sequence of a Boolean built from r at 'primary_stage_reached' for r in
            # self.prediction_rows under 'Primary_Horizon_Reached'.
            "Primary_Horizon_Reached": sum(bool(r["primary_stage_reached"]) for r in self.prediction_rows),
            # Store the sum of a lazy sequence of r at 'primary_observed_at_trigger' is the same object as True
            # for r in self.prediction_rows under 'Primary_Observed_At_Trigger'.
            "Primary_Observed_At_Trigger": sum(r["primary_observed_at_trigger"] is True for r in self.prediction_rows),
            # Store the sum of a lazy sequence of r['primary_history_complete'] is the same object as True and
            # r['primary_history_timing_valid'] is the same object as True for r in self.prediction_rows under
            # 'Primary_Complete_History'.
            "Primary_Complete_History": sum(r["primary_history_complete"] is True and r["primary_history_timing_valid"] is True for r in self.prediction_rows),
            # Store the sum of a lazy sequence of a Boolean built from r at 'primary_model_executed' for r in
            # self.prediction_rows under 'Primary_Model_Eligible'.
            "Primary_Model_Eligible": sum(bool(r["primary_model_executed"]) for r in self.prediction_rows),
            # Store the sum of a lazy sequence of a Boolean built from r at 'secondary_stage_reached' for r in
            # self.prediction_rows under 'Secondary_Horizon_Reached'.
            "Secondary_Horizon_Reached": sum(bool(r["secondary_stage_reached"]) for r in self.prediction_rows),
            # Store the sum of a lazy sequence of r at 'secondary_observed_at_trigger' is the same object as True
            # for r in self.prediction_rows under 'Secondary_Observed_At_Trigger'.
            "Secondary_Observed_At_Trigger": sum(r["secondary_observed_at_trigger"] is True for r in self.prediction_rows),
            # Store the sum of a lazy sequence of r['secondary_history_complete'] is the same object as True and
            # r['secondary_history_timing_valid'] is the same object as True for r in self.prediction_rows under
            # 'Secondary_Complete_History'.
            "Secondary_Complete_History": sum(r["secondary_history_complete"] is True and r["secondary_history_timing_valid"] is True for r in self.prediction_rows),
            # Store the sum of a lazy sequence of a Boolean built from r at 'secondary_model_executed' for r in
            # self.prediction_rows under 'Secondary_Model_Eligible'.
            "Secondary_Model_Eligible": sum(bool(r["secondary_model_executed"]) for r in self.prediction_rows),
            # Store the sum of a lazy sequence of a Boolean built from r at 'fused_model_executed' for r in
            # self.prediction_rows under 'Fused_Model_Eligible'.
            "Fused_Model_Eligible": sum(bool(r["fused_model_executed"]) for r in self.prediction_rows),
            # Store the number of entries in a set of r at 'target_id' for r in self.prediction_rows; retain
            # entries satisfying r at 'primary_model_executed' or r at 'secondary_model_executed' under
            # 'Unique_Targets_Evaluated'.
            "Unique_Targets_Evaluated": len({r["target_id"] for r in self.prediction_rows if r["primary_model_executed"] or r["secondary_model_executed"]}),
        }
        # Iterate over a tuple containing the text 'primary', the text 'secondary', binding each item to stage.
        for stage in ("primary", "secondary"):
            # Set reached to the sum of a lazy sequence of a Boolean built from r at f'{stage}_stage_reached' for
            # r in self.prediction_rows.
            reached = sum(bool(r[f"{stage}_stage_reached"]) for r in self.prediction_rows)
            # Set observed to the sum of a lazy sequence of r at f'{stage}_observed_at_trigger' is the same object
            # as True for r in self.prediction_rows.
            observed = sum(r[f"{stage}_observed_at_trigger"] is True for r in self.prediction_rows)
            # Set history to the sum of a lazy sequence of r[f'{stage}_history_complete'] is the same object as
            # True and r[f'{stage}_history_timing_valid'] is the same object as True for r in
            # self.prediction_rows.
            history = sum(r[f"{stage}_history_complete"] is True and r[f"{stage}_history_timing_valid"] is True for r in self.prediction_rows)
            # Set classified to the result of self._classification_metrics(stage).
            classified = self._classification_metrics(stage)
            # Set prefix to the result of stage.capitalize().
            prefix = stage.capitalize()
            # Set metrics[f'{prefix}_Timing_Eligibility'] to the result of self._rounded(the result of
            # self._ratio(reached, total)).
            metrics[f"{prefix}_Timing_Eligibility"] = self._rounded(self._ratio(reached, total))
            # Set metrics[f'{prefix}_Observation_Eligibility'] to the result of self._rounded(the result of
            # self._ratio(observed, reached)).
            metrics[f"{prefix}_Observation_Eligibility"] = self._rounded(self._ratio(observed, reached))
            # Set metrics[f'{prefix}_History_Eligibility'] to the result of self._rounded(the result of
            # self._ratio(history, reached)).
            metrics[f"{prefix}_History_Eligibility"] = self._rounded(self._ratio(history, reached))
            # Set metrics[f'{prefix}_Model_Eligibility'] to the result of self._rounded(the result of
            # self._ratio(classified at 'model_count', total)).
            metrics[f"{prefix}_Model_Eligibility"] = self._rounded(self._ratio(classified["model_count"], total))
            # Set metrics[f'{prefix}_Acceptance_Coverage'] to the result of self._rounded(classified at
            # 'acceptance').
            metrics[f"{prefix}_Acceptance_Coverage"] = self._rounded(classified["acceptance"])
            # Set metrics[f'{prefix}_Accepted_Accuracy'] to the result of self._rounded(classified at 'accuracy').
            metrics[f"{prefix}_Accepted_Accuracy"] = self._rounded(classified["accuracy"])
            # Set metrics[f'{prefix}_Balanced_Accuracy'] to the result of self._rounded(classified at 'balanced').
            metrics[f"{prefix}_Balanced_Accuracy"] = self._rounded(classified["balanced"])
            # Set metrics[f'{prefix}_Macro_F1'] to the result of self._rounded(classified at 'macro_f1').
            metrics[f"{prefix}_Macro_F1"] = self._rounded(classified["macro_f1"])
        # Display the text 'Evaluation results'.
        print("\nEvaluation results")
        # Iterate over key/value pairs from metrics, binding each item to (key, value).
        for key, value in metrics.items():
            # Display formatted text built from the embedded values.
            print(f"  {key}: {value}")
        # Return metrics to the caller.
        return metrics

    # Prediction fieldnames using the inputs and processing steps below.
    # Output: return the value selected by the matching return branch below.
    # Processing: select branches using the stated conditions.
    def _prediction_fieldnames(self):
        # Run this branch when the negation of self.prediction_rows.
        if not self.prediction_rows:
            # Stable schema is derived from a representative empty event only when needed.
            # Return an empty tuple to the caller.
            return ()
        # Return a tuple built from self.prediction_rows at 0 to the caller.
        return tuple(self.prediction_rows[0])

    # Confusion matrix rows using the inputs and processing steps below.
    # Output: rows.
    # Processing: iterate over the relevant records.
    def _confusion_matrix_rows(self):
        # Set rows to an empty list.
        rows = []
        # Iterate over a tuple containing the text 'primary', the text 'secondary', the text 'fused', binding each
        # item to stage.
        for stage in ("primary", "secondary", "fused"):
            # Set eligible to a list of r for r in self.prediction_rows; retain entries satisfying r at
            # f'{stage}_model_executed' and r at 'ground_truth_label_debug'.
            eligible = [r for r in self.prediction_rows if r[f"{stage}_model_executed"] and r["ground_truth_label_debug"]]
            # Iterate over CLASS_LABELS, binding each item to truth.
            for truth in CLASS_LABELS:
                # Iterate over a tuple containing the unpacked values from CLASS_LABELS, the text 'UNKNOWN',
                # binding each item to predicted.
                for predicted in (*CLASS_LABELS, "UNKNOWN"):
                    # Append a dictionary containing stage, true_label, predicted_label, count to rows.
                    rows.append({"stage": stage.upper(), "true_label": truth, "predicted_label": predicted,
                                 # Store the sum of a lazy sequence of r['ground_truth_label_debug'] equals truth
                                 # and r[f'{stage}_label'] equals predicted for r in eligible under 'count'.
                                 "count": sum(r["ground_truth_label_debug"] == truth and r[f"{stage}_label"] == predicted for r in eligible)})
        # Return rows to the caller.
        return rows

    # Save prediction log using the inputs and processing steps below.
    # Output: output.
    # Processing: select branches using the stated conditions.
    def save_prediction_log(self):
        # Set output to OUTPUT_DIR joined with the path segment 'shadow_prediction_events.csv'.
        output = OUTPUT_DIR / "shadow_prediction_events.csv"
        # Set fields to the result of self._prediction_fieldnames().
        fields = self._prediction_fieldnames()
        # Enter the result of output.open(the text 'w') as handle and run the enclosed operations within that
        # context.
        with output.open("w", newline="", encoding="utf-8") as handle:
            # Run this branch when fields.
            if fields:
                # Set writer to the result of csv.DictWriter(handle).
                writer = csv.DictWriter(handle, fieldnames=fields)
                # Call writer.writeheader with the supplied arguments.
                # Call writer.writerows with the supplied arguments.
                writer.writeheader(); writer.writerows(self.prediction_rows)
        # Set confusion to OUTPUT_DIR joined with the path segment 'shadow_confusion_matrices.csv'.
        confusion = OUTPUT_DIR / "shadow_confusion_matrices.csv"
        # Enter the result of confusion.open(the text 'w') as handle and run the enclosed operations within that
        # context.
        with confusion.open("w", newline="", encoding="utf-8") as handle:
            # Set writer to the result of csv.DictWriter(handle).
            writer = csv.DictWriter(handle, fieldnames=("stage", "true_label", "predicted_label", "count"))
            # Call writer.writeheader with the supplied arguments.
            # Call writer.writerows with the supplied arguments.
            writer.writeheader(); writer.writerows(self._confusion_matrix_rows())
        # Display formatted text built from the embedded values.
        print(f"Saved prediction events to {output}")
        # Display formatted text built from the embedded values.
        print(f"Saved confusion matrices to {confusion}")
        # Return output to the caller.
        return output


# Set evaluator to the result of Evaluator().
evaluator = Evaluator()
