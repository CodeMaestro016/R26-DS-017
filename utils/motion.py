"""
Motion Feature Extractor

Extracts motion features between two consecutive frames.
"""

import numpy as np


class MotionFeatureExtractor:

    def extract(
        self,
        previous_spatial,
        current_spatial
    ):

        prev_cx = previous_spatial[0]
        prev_cy = previous_spatial[1]

        curr_cx = current_spatial[0]
        curr_cy = current_spatial[1]

        dx = curr_cx - prev_cx
        dy = curr_cy - prev_cy

        speed = np.sqrt(
            dx**2 + dy**2
        )

        direction = np.arctan2(
            dy,
            dx
        )

        features = np.array([
            dx,
            dy,
            speed,
            direction
        ], dtype=np.float32)

        return features