# Import sys for use in this module.
import sys
# Import unittest for use in this module.
import unittest
# Import Path from pathlib for the operations below.
from pathlib import Path

# Set PROJECT_ROOT to Path(__file__).resolve().parents at 1.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
# Call sys.path.insert with the supplied arguments.
sys.path.insert(0, str(PROJECT_ROOT))

# Attempt the enclosed operations and route matching exceptions to the handlers below.
try:
    # Import Evaluator from evaluation for the operations below.
    from evaluation import Evaluator
# Handle ModuleNotFoundError using the recovery steps below.
except ModuleNotFoundError:
    # Set Evaluator to None.
    Evaluator = None


# Apply unittest.skipIf(Evaluator is None, 'traci is not installed') as a decorator to configure the following
# definition.
@unittest.skipIf(Evaluator is None, "traci is not installed")
# Define EvaluationEligibilityTests to group the state and operations declared below.
# Base classes: unittest.TestCase.
# Instances expose the attributes and methods implemented in this class.
class EvaluationEligibilityTests(unittest.TestCase):
    # Check cancelled candidates have no model accuracy using the setup, calls, and assertions below.
    # Output: no explicit value; normal completion returns None.
    def test_cancelled_candidates_have_no_model_accuracy(self):
        # Set evaluator to the result of Evaluator().
        evaluator = Evaluator()
        # Set evaluator.prediction_rows to a list containing a dictionary containing event_category, target_id,
        # ground_truth_label_debug, primary_stage_reached,...
        evaluator.prediction_rows = [{
            "event_category": "CANCELLED_BEFORE_PRIMARY", "target_id": "t",
            "ground_truth_label_debug": "LEFT",
            # Store False under 'primary_stage_reached'.
            # Store None under 'primary_observed_at_trigger'.
            "primary_stage_reached": False, "primary_observed_at_trigger": None,
            # Store None under 'primary_history_complete'.
            # Store None under 'primary_history_timing_valid'.
            "primary_history_complete": None, "primary_history_timing_valid": None,
            # Store False under 'primary_model_executed'.
            # Store False under 'primary_accepted'.
            # Store the text '' under 'primary_label'.
            "primary_model_executed": False, "primary_accepted": False, "primary_label": "",
            # Store False under 'secondary_stage_reached'.
            # Store None under 'secondary_observed_at_trigger'.
            "secondary_stage_reached": False, "secondary_observed_at_trigger": None,
            # Store None under 'secondary_history_complete'.
            # Store None under 'secondary_history_timing_valid'.
            "secondary_history_complete": None, "secondary_history_timing_valid": None,
            # Store False under 'secondary_model_executed'.
            # Store False under 'secondary_accepted'.
            # Store the text '' under 'secondary_label'.
            "secondary_model_executed": False, "secondary_accepted": False, "secondary_label": "",
            # Store False under 'fused_model_executed'.
            # Store the text 'UNKNOWN' under 'fused_label'.
            "fused_model_executed": False, "fused_label": "UNKNOWN",
        }]
        # Set metrics to the result of evaluator.compute_metrics(1.0).
        metrics = evaluator.compute_metrics(1.0)
        # Call self.assertEqual with the supplied arguments.
        self.assertEqual(metrics["Cancelled_Before_Primary"], 1)
        # Call self.assertIsNone with the supplied arguments.
        self.assertIsNone(metrics["Primary_Accepted_Accuracy"])
        # Call self.assertIsNone with the supplied arguments.
        self.assertIsNone(metrics["Primary_Balanced_Accuracy"])

    # Check confusion total equals executed with truth using the setup, calls, and assertions below.
    # Output: no explicit value; normal completion returns None.
    def test_confusion_total_equals_executed_with_truth(self):
        # Set evaluator to the result of Evaluator().
        evaluator = Evaluator()
        # Set base to a dictionary containing event_category, target_id, ground_truth_label_debug,
        # primary_model_executed,...
        base = {"event_category": "MODEL_EVALUABLE", "target_id": "t",
                # Store the text 'LEFT' under 'ground_truth_label_debug'.
                # Store True under 'primary_model_executed'.
                "ground_truth_label_debug": "LEFT", "primary_model_executed": True,
                # Store the text 'UNKNOWN' under 'primary_label'.
                # Store False under 'secondary_model_executed'.
                "primary_label": "UNKNOWN", "secondary_model_executed": False,
                # Store the text '' under 'secondary_label'.
                # Store False under 'fused_model_executed'.
                # Store the text 'UNKNOWN' under 'fused_label'.
                "secondary_label": "", "fused_model_executed": False, "fused_label": "UNKNOWN"}
        # Set evaluator.prediction_rows to a list containing base.
        evaluator.prediction_rows = [base]
        # Set primary_total to the sum of a lazy sequence of row at 'count' for row in the result of
        # evaluator._confusion_matrix_rows(); retain entries satisfying row at 'stage' equals the text 'PRIMARY'.
        primary_total = sum(row["count"] for row in evaluator._confusion_matrix_rows()
                            # Evaluate row at 'stage' equals the text 'PRIMARY' as part of the enclosing
                            # expression.
                            if row["stage"] == "PRIMARY")
        # Call self.assertEqual with the supplied arguments.
        self.assertEqual(primary_total, 1)


# Run this branch when __name__ equals the text '__main__'.
if __name__ == "__main__":
    # Call unittest.main with the supplied arguments.
    unittest.main()
