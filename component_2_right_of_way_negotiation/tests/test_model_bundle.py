"""Optional end-to-end model contract test."""

import importlib.util
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from predictor import IntentionPredictor
from tests.test_feature_builder import make_straight_history


@unittest.skipUnless(
    importlib.util.find_spec("onnxruntime") is not None,
    "onnxruntime is not installed",
)
class ModelBundleTests(unittest.TestCase):
    def test_both_models_return_valid_probabilities(self):
        predictor = IntentionPredictor()
        for model_key in ("primary", "secondary"):
            prediction = predictor.predict_stage(
                make_straight_history(), model_key
            )
            probabilities = prediction["probabilities"]
            self.assertEqual(
                set(probabilities),
                {"LEFT", "RIGHT", "STRAIGHT"},
            )
            self.assertAlmostEqual(
                sum(probabilities.values()),
                1.0,
                places=5,
            )


if __name__ == "__main__":
    unittest.main()
