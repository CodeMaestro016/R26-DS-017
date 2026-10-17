"""
Occlusion Generator

This module generates synthetic pedestrian occlusions
inside a bounding box.

Author: Avishka
Project: Adaptive Intent Prediction in Occluded Urban Scenarios
"""

import random
from typing import Dict, Tuple

import cv2
import numpy as np

from configs.occlusion import (
    OCCLUSION_LEVELS,
    OCCLUSION_COLOR,
    MIN_RECT_SIZE,
    RANDOM_SEED,
)

# Reproducibility
random.seed(RANDOM_SEED)


class OcclusionGenerator:
    """
    Generates synthetic occlusions inside pedestrian
    bounding boxes.
    """

    def __init__(self):

        self.levels = OCCLUSION_LEVELS
        self.color = OCCLUSION_COLOR
        self.min_size = MIN_RECT_SIZE

    def apply(
        self,
        image: np.ndarray,
        bbox: Tuple[int, int, int, int],
        level: str = "medium",
    ) -> Tuple[np.ndarray, Dict]:
        """
        Apply occlusion to a pedestrian bounding box.

        Parameters
        ----------
        image : np.ndarray
            Input image.

        bbox : tuple
            (x1, y1, x2, y2)

        level : str
            low / medium / high

        Returns
        -------
        occluded_image
        metadata
        """

        if level not in self.levels:
            raise ValueError(
                f"Unknown occlusion level: {level}"
            )

        x1, y1, x2, y2 = bbox

        image_copy = image.copy()

        bbox_width = x2 - x1
        bbox_height = y2 - y1

        ratio = self.levels[level]

        occ_width = max(
            self.min_size,
            int(bbox_width * ratio)
        )

        occ_height = max(
            self.min_size,
            int(bbox_height * ratio)
        )

        max_x = max(x1, x2 - occ_width)
        max_y = max(y1, y2 - occ_height)

        occ_x = random.randint(x1, max_x)
        occ_y = random.randint(y1, max_y)

        cv2.rectangle(
            image_copy,
            (occ_x, occ_y),
            (occ_x + occ_width, occ_y + occ_height),
            self.color,
            thickness=-1
        )

        metadata = {

            "level": level,

            "ratio": ratio,

            "bbox_x1": x1,
            "bbox_y1": y1,
            "bbox_x2": x2,
            "bbox_y2": y2,

            "occ_x": occ_x,
            "occ_y": occ_y,
            "occ_width": occ_width,
            "occ_height": occ_height,

            "bbox_width": bbox_width,
            "bbox_height": bbox_height

        }

        return image_copy, metadata

    def available_levels(self):
        """
        Returns available occlusion levels.
        """

        return list(self.levels.keys())
    