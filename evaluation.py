"""Traffic metrics plus eligibility-aware shadow-model evaluation."""

import csv
from collections import defaultdict

import numpy as np
import traci

from config import DEADLOCK_DURATION_SECONDS, OUTPUT_DIR, SIM_TIME_STEP, STOPPED_SPEED_THRESHOLD_MPS

CLASS_LABELS = ("LEFT", "RIGHT", "STRAIGHT")
FEATURE_NAMES = ("speed", "acceleration_magnitude", "longitudinal_velocity",
                 "lateral_velocity", "longitudinal_acceleration", "lateral_acceleration")


class Evaluator:
    def __init__(self):
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        self.reset()

    def reset(self):
        self.collision_events = 0
        self.total_travel_time = 0.0
        self.successful_crossings = 0
        self.step_count = 0
        self.av_speeds_history = []
        self.vehicle_departure_times = {}
        self.stopped_duration = defaultdict(float)
        self.deadlocked_vehicle_ids = set()
        self.prediction_rows = []
        self.safety_score = 100.0
        self.deadlock_rate = self.throughput = self.avg_av_speed = 0.0
        self.total_collisions = self.avg_travel_time = 0.0

    @staticmethod
    def _route_to_label(route_id):
        lowered = str(route_id).lower()
        for label in ("left", "right", "straight"):
            if lowered.endswith("_" + label):
                return label.upper()
        return ""

    @staticmethod
    def _stage_columns(stage, result):
        values = {}
        scalar_names = ("predicted_class", "label", "confidence", "threshold", "accepted")
        if result is None:
            for name in scalar_names:
                values[f"{stage}_{name}"] = False if name == "accepted" else ""
            for label in CLASS_LABELS:
                values[f"{stage}_probability_{label.lower()}"] = ""
            values[f"{stage}_maximum_absolute_z_score"] = ""
            for name in FEATURE_NAMES:
                values[f"{stage}_mean_{name}"] = ""
                values[f"{stage}_max_abs_z_{name}"] = ""
            return values
        for name in scalar_names:
            values[f"{stage}_{name}"] = result[name]
        for label in CLASS_LABELS:
            values[f"{stage}_probability_{label.lower()}"] = result["probabilities"][label]
        diagnostics = result["feature_diagnostics"]
        values[f"{stage}_maximum_absolute_z_score"] = diagnostics["maximum_absolute_z_score"]
        for name in FEATURE_NAMES:
            values[f"{stage}_mean_{name}"] = diagnostics["raw_feature_means"][name]
            values[f"{stage}_max_abs_z_{name}"] = diagnostics["maximum_absolute_z_score_by_feature"][name]
        return values

    def record_prediction_events(self, events):
        for event in events:
            truth = self._route_to_label(event.get("ground_truth_route_id", ""))
            row = {
                "event_id": event["event_id"], "event_start_time": event["event_start_time"],
                "finalization_time": event["finalization_time"], "finalization_reason": event["finalization_reason"],
                "event_category": event["event_category"], "ego_id": event["ego_id"], "target_id": event["target_id"],
                "ground_truth_route_id_debug": event.get("ground_truth_route_id", ""),
                "ground_truth_label_debug": truth,
                "latest_history_count": event.get("latest_history_count"),
                "maximum_history_count": event.get("maximum_history_count"),
                "latest_estimated_eta": event.get("latest_estimated_eta"),
                "latest_observation_age": event.get("latest_observation_age"),
            }
            for stage in ("primary", "secondary"):
                result = event.get(stage)
                for name in ("trigger_time", "trigger_eta_seconds", "distance_to_entry_meters",
                             "stage_reached", "observed_at_trigger", "observation_age_seconds",
                             "history_count_at_trigger", "history_complete", "history_timing_valid",
                             "model_executed", "stage_status", "stage_error"):
                    row[f"{stage}_{name}"] = event.get(f"{stage}_{name}")
                row[f"{stage}_correct_when_accepted"] = bool(result and result["accepted"] and truth and result["label"] == truth)
                row.update(self._stage_columns(stage, result))
            fused_executed = bool(row["primary_model_executed"] and row["secondary_model_executed"])
            fused_label = event.get("fused_label", "UNKNOWN")
            row.update({
                "fused_stage_reached": bool(row["primary_stage_reached"] and row["secondary_stage_reached"]),
                "fused_model_executed": fused_executed,
                "fused_stage_status": "PREDICTED" if fused_executed else "INCOMPLETE",
                "fused_label": fused_label, "fusion_status": event["status"],
                "fused_accepted": fused_executed and fused_label != "UNKNOWN",
                "fused_correct_when_accepted": fused_executed and fused_label != "UNKNOWN" and bool(truth) and fused_label == truth,
            })
            self.prediction_rows.append(row)

    def _update_collisions(self):
        try:
            self.collision_events += len(traci.simulation.getCollisions())
        except (AttributeError, traci.TraCIException):
            if traci.simulation.getCollidingVehiclesNumber() > 0:
                self.collision_events += 1

    def update(self, current_time, observations):
        self.step_count += 1
        self._update_collisions()
        active = set(observations)
        for vehicle_id in list(self.stopped_duration):
            if vehicle_id not in active:
                del self.stopped_duration[vehicle_id]
        for vehicle_id, state in observations.items():
            if state.get("vel", 0.0) < STOPPED_SPEED_THRESHOLD_MPS:
                self.stopped_duration[vehicle_id] += SIM_TIME_STEP
                if self.stopped_duration[vehicle_id] >= DEADLOCK_DURATION_SECONDS:
                    self.deadlocked_vehicle_ids.add(vehicle_id)
            else:
                self.stopped_duration[vehicle_id] = 0.0
                self.deadlocked_vehicle_ids.discard(vehicle_id)
        self.av_speeds_history.extend(state.get("vel", 0.0) for vid, state in observations.items() if vid.startswith("AV_"))
        for vid in traci.vehicle.getIDList():
            self.vehicle_departure_times.setdefault(vid, float(current_time))
        for vid in traci.simulation.getArrivedIDList():
            departure = self.vehicle_departure_times.pop(vid, None)
            if departure is not None:
                self.total_travel_time += float(current_time) - departure
                self.successful_crossings += 1
        self.total_collisions = self.collision_events
        self.safety_score = max(0.0, 100.0 - 15.0 * self.collision_events)
        self.avg_av_speed = float(np.mean(self.av_speeds_history)) if self.av_speeds_history else 0.0
        self.deadlock_rate = len(self.deadlocked_vehicle_ids) / max(1, len(observations))
        self.throughput = self.successful_crossings / max(float(current_time), SIM_TIME_STEP)
        self.avg_travel_time = self.total_travel_time / max(1, self.successful_crossings)

    @staticmethod
    def _ratio(numerator, denominator):
        return None if denominator == 0 else numerator / denominator

    def _classification_metrics(self, stage):
        model_rows = [row for row in self.prediction_rows if row[f"{stage}_model_executed"] and row["ground_truth_label_debug"]]
        accepted = [row for row in model_rows if row[f"{stage}_accepted"]]
        correct = sum(row[f"{stage}_label"] == row["ground_truth_label_debug"] for row in accepted)
        recalls, f1s = [], []
        for label in CLASS_LABELS:
            tp = sum(r["ground_truth_label_debug"] == label and r[f"{stage}_label"] == label for r in model_rows)
            fp = sum(r["ground_truth_label_debug"] != label and r[f"{stage}_label"] == label for r in model_rows)
            fn = sum(r["ground_truth_label_debug"] == label and r[f"{stage}_label"] != label for r in model_rows)
            recall = self._ratio(tp, tp + fn)
            precision = self._ratio(tp, tp + fp)
            if recall is not None:
                recalls.append(recall)
            f1s.append(0.0 if precision is None or recall is None or precision + recall == 0 else 2 * precision * recall / (precision + recall))
        return {"model_count": len(model_rows), "acceptance": self._ratio(len(accepted), len(model_rows)),
                "accuracy": self._ratio(correct, len(accepted)),
                "balanced": float(np.mean(recalls)) if model_rows and recalls else None,
                "macro_f1": float(np.mean(f1s)) if model_rows else None}

    @staticmethod
    def _rounded(value):
        return None if value is None else round(value, 4)

    def compute_metrics(self, simulation_time):
        total = len(self.prediction_rows)
        metrics = {
            "Safety_Score": round(self.safety_score, 2), "Deadlock_Rate": round(self.deadlock_rate, 4),
            "Throughput_Vehicles_Per_Second": round(self.successful_crossings / max(simulation_time, SIM_TIME_STEP), 4),
            "Avg_AV_Speed": round(self.avg_av_speed, 2), "Total_Collision_Events": self.collision_events,
            "Successful_Crossings": self.successful_crossings, "Avg_Travel_Time": round(self.avg_travel_time, 2),
            "Finalized_Candidate_Events": total,
            "Cancelled_Before_Primary": sum(r["event_category"] == "CANCELLED_BEFORE_PRIMARY" for r in self.prediction_rows),
            "Perception_Ineligible_Events": sum(r["event_category"] == "PERCEPTION_INELIGIBLE" for r in self.prediction_rows),
            "Primary_Horizon_Reached": sum(bool(r["primary_stage_reached"]) for r in self.prediction_rows),
            "Primary_Observed_At_Trigger": sum(r["primary_observed_at_trigger"] is True for r in self.prediction_rows),
            "Primary_Complete_History": sum(r["primary_history_complete"] is True and r["primary_history_timing_valid"] is True for r in self.prediction_rows),
            "Primary_Model_Eligible": sum(bool(r["primary_model_executed"]) for r in self.prediction_rows),
            "Secondary_Horizon_Reached": sum(bool(r["secondary_stage_reached"]) for r in self.prediction_rows),
            "Secondary_Observed_At_Trigger": sum(r["secondary_observed_at_trigger"] is True for r in self.prediction_rows),
            "Secondary_Complete_History": sum(r["secondary_history_complete"] is True and r["secondary_history_timing_valid"] is True for r in self.prediction_rows),
            "Secondary_Model_Eligible": sum(bool(r["secondary_model_executed"]) for r in self.prediction_rows),
            "Fused_Model_Eligible": sum(bool(r["fused_model_executed"]) for r in self.prediction_rows),
            "Unique_Targets_Evaluated": len({r["target_id"] for r in self.prediction_rows if r["primary_model_executed"] or r["secondary_model_executed"]}),
        }
        for stage in ("primary", "secondary"):
            reached = sum(bool(r[f"{stage}_stage_reached"]) for r in self.prediction_rows)
            observed = sum(r[f"{stage}_observed_at_trigger"] is True for r in self.prediction_rows)
            history = sum(r[f"{stage}_history_complete"] is True and r[f"{stage}_history_timing_valid"] is True for r in self.prediction_rows)
            classified = self._classification_metrics(stage)
            prefix = stage.capitalize()
            metrics[f"{prefix}_Timing_Eligibility"] = self._rounded(self._ratio(reached, total))
            metrics[f"{prefix}_Observation_Eligibility"] = self._rounded(self._ratio(observed, reached))
            metrics[f"{prefix}_History_Eligibility"] = self._rounded(self._ratio(history, reached))
            metrics[f"{prefix}_Model_Eligibility"] = self._rounded(self._ratio(classified["model_count"], total))
            metrics[f"{prefix}_Acceptance_Coverage"] = self._rounded(classified["acceptance"])
            metrics[f"{prefix}_Accepted_Accuracy"] = self._rounded(classified["accuracy"])
            metrics[f"{prefix}_Balanced_Accuracy"] = self._rounded(classified["balanced"])
            metrics[f"{prefix}_Macro_F1"] = self._rounded(classified["macro_f1"])
        print("\nEvaluation results")
        for key, value in metrics.items():
            print(f"  {key}: {value}")
        return metrics

    def _prediction_fieldnames(self):
        if not self.prediction_rows:
            # Stable schema is derived from a representative empty event only when needed.
            return ()
        return tuple(self.prediction_rows[0])

    def _confusion_matrix_rows(self):
        rows = []
        for stage in ("primary", "secondary", "fused"):
            eligible = [r for r in self.prediction_rows if r[f"{stage}_model_executed"] and r["ground_truth_label_debug"]]
            for truth in CLASS_LABELS:
                for predicted in (*CLASS_LABELS, "UNKNOWN"):
                    rows.append({"stage": stage.upper(), "true_label": truth, "predicted_label": predicted,
                                 "count": sum(r["ground_truth_label_debug"] == truth and r[f"{stage}_label"] == predicted for r in eligible)})
        return rows

    def save_prediction_log(self):
        output = OUTPUT_DIR / "shadow_prediction_events.csv"
        fields = self._prediction_fieldnames()
        with output.open("w", newline="", encoding="utf-8") as handle:
            if fields:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader(); writer.writerows(self.prediction_rows)
        confusion = OUTPUT_DIR / "shadow_confusion_matrices.csv"
        with confusion.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=("stage", "true_label", "predicted_label", "count"))
            writer.writeheader(); writer.writerows(self._confusion_matrix_rows())
        print(f"Saved prediction events to {output}")
        print(f"Saved confusion matrices to {confusion}")
        return output


evaluator = Evaluator()
