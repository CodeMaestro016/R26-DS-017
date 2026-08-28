"""Tests that do not require SUMO or ONNX Runtime."""

import sys
import unittest
from pathlib import Path

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from predictor import IntentionPredictor, PredictionContractError


def make_straight_history(interval=0.04):
    return [
        {
            "timestamp": index * interval,
            "position": (index * interval * 8.0, 0.0),
        }
        for index in range(50)
    ]


class FeatureBuilderTests(unittest.TestCase):
    def test_straight_history_produces_expected_shape(self):
        features = IntentionPredictor.build_causal_features(
            make_straight_history()
        )
        self.assertEqual(features.shape, (48, 6))
        self.assertTrue(np.all(np.isfinite(features)))
        np.testing.assert_allclose(features[:, 0], 8.0, atol=1e-5)
        np.testing.assert_allclose(features[:, 2], 8.0, atol=1e-5)
        np.testing.assert_allclose(features[:, 3:], 0.0, atol=1e-5)

    def test_low_rate_history_is_rejected(self):
        with self.assertRaises(PredictionContractError):
            IntentionPredictor.build_causal_features(
                make_straight_history(interval=0.5)
            )

    def test_short_history_is_rejected(self):
        with self.assertRaises(PredictionContractError):
            IntentionPredictor.build_causal_features(
                make_straight_history()[:-1]
            )


if __name__ == "__main__":
    unittest.main()

