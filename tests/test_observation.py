"""Checks for the corrected LDM timing and SUMO heading convention."""

import sys
import unittest
from pathlib import Path

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from observation import LocalDynamicMap


class ObservationTests(unittest.TestCase):
    def test_sumo_navigation_heading_is_converted_correctly(self):
        north = LocalDynamicMap._velocity_vector(10.0, 0.0)
        east = LocalDynamicMap._velocity_vector(
            10.0,
            np.pi / 2.0,
        )
        np.testing.assert_allclose(north, (0.0, 10.0), atol=1e-8)
        np.testing.assert_allclose(east, (10.0, 0.0), atol=1e-8)

    def test_propagation_does_not_fake_an_observation(self):
        ldm = LocalDynamicMap("AV_ego")
        ldm.add_or_update_track(
            vehicle_id="AV_other",
            position=(0.0, 0.0),
            speed=10.0,
            heading_radians=np.pi / 2.0,
            lane_id="w_in_0",
            lane_position=0.0,
            lane_length=100.0,
            road_id="w_in",
            ground_truth_route_id="route_w_straight",
            current_time=1.0,
        )

        ldm.propagate_track("AV_other", current_time=1.5)
        track = ldm.tracks["AV_other"]

        self.assertEqual(track["last_observed_time"], 1.0)
        self.assertEqual(len(track["position_history"]), 1)
        np.testing.assert_allclose(
            track["position"],
            (5.0, 0.0),
            atol=1e-12,
        )


if __name__ == "__main__":
    unittest.main()
