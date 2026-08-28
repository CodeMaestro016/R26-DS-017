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
class ShadowEvaluationTests(unittest.TestCase):
    def test_route_suffix_becomes_debug_label(self):
        self.assertEqual(
            Evaluator._route_to_label("route_w_left"),
            "LEFT",
        )
        self.assertEqual(
            Evaluator._route_to_label("route_s_right"),
            "RIGHT",
        )
        self.assertEqual(
            Evaluator._route_to_label("route_n_straight"),
            "STRAIGHT",
        )

    def test_unknown_route_does_not_invent_a_label(self):
        self.assertEqual(
            Evaluator._route_to_label("unrecognized_route"),
            "",
        )


if __name__ == "__main__":
    unittest.main()
