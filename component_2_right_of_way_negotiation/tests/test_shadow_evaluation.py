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
# Define ShadowEvaluationTests to group the state and operations declared below.
# Base classes: unittest.TestCase.
# Instances expose the attributes and methods implemented in this class.
class ShadowEvaluationTests(unittest.TestCase):
    # Check route suffix becomes debug label using the setup, calls, and assertions below.
    # Output: no explicit value; normal completion returns None.
    def test_route_suffix_becomes_debug_label(self):
        # Call self.assertEqual with the supplied arguments.
        self.assertEqual(
            # Supply the result of Evaluator._route_to_label(the text 'route_w_left') to self.assertEqual.
            Evaluator._route_to_label("route_w_left"),
            "LEFT",
        )
        # Call self.assertEqual with the supplied arguments.
        self.assertEqual(
            # Supply the result of Evaluator._route_to_label(the text 'route_s_right') to self.assertEqual.
            Evaluator._route_to_label("route_s_right"),
            "RIGHT",
        )
        # Call self.assertEqual with the supplied arguments.
        self.assertEqual(
            # Supply the result of Evaluator._route_to_label(the text 'route_n_straight') to self.assertEqual.
            Evaluator._route_to_label("route_n_straight"),
            "STRAIGHT",
        )

    # Check unknown route does not invent a label using the setup, calls, and assertions below.
    # Output: no explicit value; normal completion returns None.
    def test_unknown_route_does_not_invent_a_label(self):
        # Call self.assertEqual with the supplied arguments.
        self.assertEqual(
            # Supply the result of Evaluator._route_to_label(the text 'unrecognized_route') to self.assertEqual.
            Evaluator._route_to_label("unrecognized_route"),
            "",
        )


# Run this branch when __name__ equals the text '__main__'.
if __name__ == "__main__":
    # Call unittest.main with the supplied arguments.
    unittest.main()
