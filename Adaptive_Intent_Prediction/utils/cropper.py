"""
Pedestrian Cropper

Creates a square context crop around a pedestrian
bounding box while preserving aspect ratio.

Author: Avishka
Project: Adaptive Intent Prediction in Occluded Urban Scenarios
"""

from typing import Tuple

import cv2
import numpy as np


class PedestrianCropper:

    def __init__(
        self,
        output_size=(224, 224),
        context_scale=2.0,
        min_crop_size=128
    ):

        self.output_size = output_size
        self.context_scale = context_scale
        self.min_crop_size = min_crop_size

    def crop(
        self,
        image: np.ndarray,
        bbox: Tuple[int, int, int, int]
    ) -> np.ndarray:

        x1, y1, x2, y2 = bbox

        H, W = image.shape[:2]

        bbox_w = x2 - x1
        bbox_h = y2 - y1

        # ----------------------------------
        # Bounding box center
        # ----------------------------------

        cx = x1 + bbox_w / 2
        cy = y1 + bbox_h / 2

        # ----------------------------------
        # Square crop size
        # ----------------------------------

        side = max(bbox_w, bbox_h)

        side = int(side * self.context_scale)

        side = max(side, self.min_crop_size)

        half = side // 2

        crop_x1 = int(cx - half)
        crop_y1 = int(cy - half)

        crop_x2 = crop_x1 + side
        crop_y2 = crop_y1 + side

        # ----------------------------------
        # Shift crop back inside image
        # ----------------------------------

        if crop_x1 < 0:
            crop_x2 -= crop_x1
            crop_x1 = 0

        if crop_y1 < 0:
            crop_y2 -= crop_y1
            crop_y1 = 0

        if crop_x2 > W:
            diff = crop_x2 - W
            crop_x1 -= diff
            crop_x2 = W

        if crop_y2 > H:
            diff = crop_y2 - H
            crop_y1 -= diff
            crop_y2 = H

        crop_x1 = max(0, crop_x1)
        crop_y1 = max(0, crop_y1)

        crop = image[
            crop_y1:crop_y2,
            crop_x1:crop_x2
        ]

        if crop.size == 0:
            raise ValueError("Empty crop.")

        crop = cv2.resize(
            crop,
            self.output_size,
            interpolation=cv2.INTER_AREA
        )

        return crop

    def is_valid_bbox(
        self,
        bbox: Tuple[int, int, int, int],
        min_width=20,
        min_height=40
    ) -> bool:

        x1, y1, x2, y2 = bbox

        width = x2 - x1
        height = y2 - y1

        return (
            width >= min_width
            and
            height >= min_height
        )