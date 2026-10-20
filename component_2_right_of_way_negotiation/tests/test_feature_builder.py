"""Tests that do not require SUMO or ONNX Runtime."""

# Import sys for use in this module.
import sys
# Import unittest for use in this module.
import unittest
# Import Path from pathlib for the operations below.
from pathlib import Path

# Import numpy as np for use in this module.
import numpy as np


# Set PROJECT_ROOT to Path(__file__).resolve().parents at 1.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
# Call sys.path.insert with the supplied arguments.
sys.path.insert(0, str(PROJECT_ROOT))

# Import IntentionPredictor, PredictionContractError from predictor for the operations below.
from predictor import IntentionPredictor, PredictionContractError


# Make straight history using the inputs and processing steps below.
# Input interval: the supplied interval.
# Output: a list of a dictionary containing timestamp, position for index in the integer range defined by 50.
def make_straight_history(interval=0.04):
    # Return a list of a dictionary containing timestamp, position for index in the integer range defined by 50 to
    # the caller.
    return [
        # Evaluate a dictionary containing timestamp, position as part of the enclosing expression.
        {
            # Store index multiplied by interval under 'timestamp'.
            "timestamp": index * interval,
            # Store a tuple containing index multiplied by interval multiplied by 8.0, 0.0 under 'position'.
            "position": (index * interval * 8.0, 0.0),
        }
        # Evaluate the integer range defined by 50 as part of the enclosing expression.
        for index in range(50)
    ]


# Define FeatureBuilderTests to group the state and operations declared below.
# Base classes: unittest.TestCase.
# Instances expose the attributes and methods implemented in this class.
class FeatureBuilderTests(unittest.TestCase):
    # Check straight history produces expected shape using the setup, calls, and assertions below.
    # Output: no explicit value; normal completion returns None.
    def test_straight_history_produces_expected_shape(self):
        # Set features to the result of IntentionPredictor.build_causal_features(the result of
        # make_straight_history()).
        features = IntentionPredictor.build_causal_features(
            # Supply the result of make_straight_history() to IntentionPredictor.build_causal_features.
            make_straight_history()
        )
        # Call self.assertEqual with the supplied arguments.
        self.assertEqual(features.shape, (48, 6))
        # Call self.assertTrue with the supplied arguments.
        self.assertTrue(np.all(np.isfinite(features)))
        # Call np.testing.assert_allclose with the supplied arguments.
        np.testing.assert_allclose(features[:, 0], 8.0, atol=1e-5)
        # Call np.testing.assert_allclose with the supplied arguments.
        np.testing.assert_allclose(features[:, 2], 8.0, atol=1e-5)
        # Call np.testing.assert_allclose with the supplied arguments.
        np.testing.assert_allclose(features[:, 3:], 0.0, atol=1e-5)

    # Check low rate history is rejected using the setup, calls, and assertions below.
    # Output: no explicit value; normal completion returns None.
    def test_low_rate_history_is_rejected(self):
        # Enter the result of self.assertRaises(PredictionContractError) and run the enclosed operations within
        # that context.
        with self.assertRaises(PredictionContractError):
            # Call IntentionPredictor.build_causal_features with the supplied arguments.
            IntentionPredictor.build_causal_features(
                # Supply interval as 0.5.
                make_straight_history(interval=0.5)
            )

    # Check short history is rejected using the setup, calls, and assertions below.
    # Output: no explicit value; normal completion returns None.
    def test_short_history_is_rejected(self):
        # Enter the result of self.assertRaises(PredictionContractError) and run the enclosed operations within
        # that context.
        with self.assertRaises(PredictionContractError):
            # Call IntentionPredictor.build_causal_features with the supplied arguments.
            IntentionPredictor.build_causal_features(
                # Supply make_straight_history() sliced by :-1 to IntentionPredictor.build_causal_features.
                make_straight_history()[:-1]
            )


# Run this branch when __name__ equals the text '__main__'.
if __name__ == "__main__":
    # Call unittest.main with the supplied arguments.
    unittest.main()

