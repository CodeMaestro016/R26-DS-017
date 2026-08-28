import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from evaluation import Evaluator
except ModuleNotFoundError:
    Evaluator = None


@unittest.skipIf(Evaluator is None, "traci is not installed")
class EvaluationEligibilityTests(unittest.TestCase):
    def test_cancelled_candidates_have_no_model_accuracy(self):
        evaluator = Evaluator()
        evaluator.prediction_rows = [{
            "event_category": "CANCELLED_BEFORE_PRIMARY", "target_id": "t",
            "ground_truth_label_debug": "LEFT",
            "primary_stage_reached": False, "primary_observed_at_trigger": None,
            "primary_history_complete": None, "primary_history_timing_valid": None,
            "primary_model_executed": False, "primary_accepted": False, "primary_label": "",
            "secondary_stage_reached": False, "secondary_observed_at_trigger": None,
            "secondary_history_complete": None, "secondary_history_timing_valid": None,
            "secondary_model_executed": False, "secondary_accepted": False, "secondary_label": "",
            "fused_model_executed": False, "fused_label": "UNKNOWN",
        }]
        metrics = evaluator.compute_metrics(1.0)
        self.assertEqual(metrics["Cancelled_Before_Primary"], 1)
        self.assertIsNone(metrics["Primary_Accepted_Accuracy"])
        self.assertIsNone(metrics["Primary_Balanced_Accuracy"])

    def test_confusion_total_equals_executed_with_truth(self):
        evaluator = Evaluator()
        base = {"event_category": "MODEL_EVALUABLE", "target_id": "t",
                "ground_truth_label_debug": "LEFT", "primary_model_executed": True,
                "primary_label": "UNKNOWN", "secondary_model_executed": False,
                "secondary_label": "", "fused_model_executed": False, "fused_label": "UNKNOWN"}
        evaluator.prediction_rows = [base]
        primary_total = sum(row["count"] for row in evaluator._confusion_matrix_rows()
                            if row["stage"] == "PRIMARY")
        self.assertEqual(primary_total, 1)


if __name__ == "__main__":
    unittest.main()
