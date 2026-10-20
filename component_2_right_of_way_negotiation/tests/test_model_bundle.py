"""Optional end-to-end model contract test."""

# Import importlib.util for use in this module.
import importlib.util
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

# Import IntentionPredictor from predictor for the operations below.
from predictor import IntentionPredictor
# Import make_straight_history from tests.test_feature_builder for the operations below.
from tests.test_feature_builder import make_straight_history


# Apply unittest.skipUnless as a decorator to configure the following definition.
@unittest.skipUnless(
    # Supply the result of importlib.util.find_spec(the text 'onnxruntime') is a different object from None to
    # unittest.skipUnless.
    importlib.util.find_spec("onnxruntime") is not None,
    "onnxruntime is not installed",
)
# Define ModelBundleTests to group the state and operations declared below.
# Base classes: unittest.TestCase.
# Instances expose the attributes and methods implemented in this class.
class ModelBundleTests(unittest.TestCase):
    # Check both models return valid probabilities using the setup, calls, and assertions below.
    # Output: no explicit value; normal completion returns None.
    # Processing: iterate over the relevant records.
    def test_both_models_return_valid_probabilities(self):
        # Set predictor to the result of IntentionPredictor().
        predictor = IntentionPredictor()
        # Iterate over a tuple containing the text 'primary', the text 'secondary', binding each item to
        # model_key.
        for model_key in ("primary", "secondary"):
            # Set prediction to the result of predictor.predict_stage(the result of make_straight_history(),
            # model_key).
            prediction = predictor.predict_stage(
                # Supply the result of make_straight_history() to predictor.predict_stage.
                make_straight_history(), model_key
            )
            # Set probabilities to prediction at 'probabilities'.
            probabilities = prediction["probabilities"]
            # Call self.assertEqual with the supplied arguments.
            self.assertEqual(
                # Supply a set built from probabilities to self.assertEqual.
                set(probabilities),
                # Supply a set containing the text 'LEFT', the text 'RIGHT', the text 'STRAIGHT' to
                # self.assertEqual.
                {"LEFT", "RIGHT", "STRAIGHT"},
            )
            # Call self.assertAlmostEqual with the supplied arguments.
            self.assertAlmostEqual(
                # Supply the sum of values from probabilities to self.assertAlmostEqual.
                sum(probabilities.values()),
                # Supply 1.0 to the enclosing expression.
                1.0,
                # Supply places as 5.
                places=5,
            )


# Run this branch when __name__ equals the text '__main__'.
if __name__ == "__main__":
    # Call unittest.main with the supplied arguments.
    unittest.main()
