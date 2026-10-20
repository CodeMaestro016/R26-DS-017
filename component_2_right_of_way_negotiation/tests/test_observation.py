"""Checks for the corrected LDM timing and SUMO heading convention."""

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

# Import LocalDynamicMap from observation for the operations below.
from observation import LocalDynamicMap


# Define ObservationTests to group the state and operations declared below.
# Base classes: unittest.TestCase.
# Instances expose the attributes and methods implemented in this class.
class ObservationTests(unittest.TestCase):
    # Check sumo navigation heading is converted correctly using the setup, calls, and assertions below.
    # Output: no explicit value; normal completion returns None.
    def test_sumo_navigation_heading_is_converted_correctly(self):
        # Set north to the result of LocalDynamicMap._velocity_vector(10.0, 0.0).
        north = LocalDynamicMap._velocity_vector(10.0, 0.0)
        # Set east to the result of LocalDynamicMap._velocity_vector(10.0, np.pi divided by 2.0).
        east = LocalDynamicMap._velocity_vector(
            # Supply 10.0 to the enclosing expression.
            10.0,
            # Supply np.pi divided by 2.0 to LocalDynamicMap._velocity_vector.
            np.pi / 2.0,
        )
        # Call np.testing.assert_allclose with the supplied arguments.
        np.testing.assert_allclose(north, (0.0, 10.0), atol=1e-8)
        # Call np.testing.assert_allclose with the supplied arguments.
        np.testing.assert_allclose(east, (10.0, 0.0), atol=1e-8)

    # Check propagation does not fake an observation using the setup, calls, and assertions below.
    # Output: no explicit value; normal completion returns None.
    def test_propagation_does_not_fake_an_observation(self):
        # Set ldm to the result of LocalDynamicMap(the text 'AV_ego').
        ldm = LocalDynamicMap("AV_ego")
        # Call ldm.add_or_update_track with the supplied arguments.
        ldm.add_or_update_track(
            # Supply vehicle_id as the text 'AV_other'.
            vehicle_id="AV_other",
            # Supply position as a tuple containing 0.0, 0.0.
            position=(0.0, 0.0),
            # Supply speed as 10.0.
            speed=10.0,
            # Supply heading_radians as np.pi divided by 2.0.
            heading_radians=np.pi / 2.0,
            # Supply lane_id as the text 'w_in_0'.
            lane_id="w_in_0",
            # Supply lane_position as 0.0.
            lane_position=0.0,
            # Supply lane_length as 100.0.
            lane_length=100.0,
            # Supply road_id as the text 'w_in'.
            road_id="w_in",
            # Supply current_time as 1.0.
            current_time=1.0,
        )

        # Call ldm.propagate_track with the supplied arguments.
        ldm.propagate_track("AV_other", current_time=1.5)
        # Set track to ldm.tracks at 'AV_other'.
        track = ldm.tracks["AV_other"]

        # Call self.assertEqual with the supplied arguments.
        self.assertEqual(track["last_observed_time"], 1.0)
        # Call self.assertEqual with the supplied arguments.
        self.assertEqual(len(track["position_history"]), 1)
        # Call np.testing.assert_allclose with the supplied arguments.
        np.testing.assert_allclose(
            # Supply track at 'position' to np.testing.assert_allclose.
            track["position"],
            # Supply a tuple containing 5.0, 0.0 to np.testing.assert_allclose.
            (5.0, 0.0),
            # Supply atol as 1e-12.
            atol=1e-12,
        )


# Run this branch when __name__ equals the text '__main__'.
if __name__ == "__main__":
    # Call unittest.main with the supplied arguments.
    unittest.main()
