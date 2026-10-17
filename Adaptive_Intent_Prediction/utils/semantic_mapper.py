"""
Semantic Mapper

Combines motion, position and occlusion
into semantic states for the Bayesian Network.
"""

import joblib
import numpy as np

from utils.position_mapper import PositionMapper


class SemanticMapper:

    def __init__(
        self,
        motion_model_path="outputs/phase4/motion_kmeans.pkl"
    ):
        self.motion_model = joblib.load(motion_model_path)
        self.position_mapper = PositionMapper()

        # Sort motion clusters using their centroid values.
        centers = self.motion_model.cluster_centers_.flatten()
        order = centers.argsort()

        self.cluster_map = {
            int(order[0]): "static",
            int(order[1]): "walking",
            int(order[2]): "fast"
        }

    def map_motion(self, speed):

        model_dtype = self.motion_model.cluster_centers_.dtype

        speed_input = np.asarray(
            [[speed]],
            dtype=model_dtype
        )

        cluster = self.motion_model.predict(speed_input)[0]

        return self.cluster_map[int(cluster)]

    def map_position(
        self,
        center_x,
        center_y,
        image_width,
        image_height
    ):
        return self.position_mapper.map(
            center_x,
            center_y,
            image_width,
            image_height
        )

    def map_occlusion(self, occlusion):

        valid_levels = [
            "low",
            "medium",
            "high"
        ]

        if not isinstance(occlusion, str):
            raise TypeError(
                "Occlusion level must be a string."
            )

        occlusion = occlusion.strip().lower()

        if occlusion not in valid_levels:
            raise ValueError(
                f"Invalid occlusion level: {occlusion}. "
                f"Expected one of {valid_levels}."
            )

        return occlusion

    def map(
        self,
        speed,
        center_x,
        center_y,
        image_width,
        image_height,
        occlusion
    ):

        motion = self.map_motion(speed)

        position = self.map_position(
            center_x=center_x,
            center_y=center_y,
            image_width=image_width,
            image_height=image_height
        )

        occlusion_level = self.map_occlusion(occlusion)

        return {
            "motion": motion,
            "horizontal": position["horizontal"],
            "vertical": position["vertical"],
            "occlusion": occlusion_level
        }