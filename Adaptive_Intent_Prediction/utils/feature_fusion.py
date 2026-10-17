"""
Feature Fusion

Combines appearance, spatial and motion features
into a single feature vector.
"""

import numpy as np


class FeatureFusion:

    def fuse(
        self,
        appearance,
        spatial,
        motion
    ):

        appearance = np.asarray(
            appearance,
            dtype=np.float32
        )

        spatial = np.asarray(
            spatial,
            dtype=np.float32
        )

        motion = np.asarray(
            motion,
            dtype=np.float32
        )

        fused = np.concatenate([
            appearance,
            spatial,
            motion
        ])

        return fused