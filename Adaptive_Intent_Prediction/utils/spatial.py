"""
Spatial Feature Extractor

Extracts geometric features from a pedestrian
bounding box.
"""

import numpy as np


class SpatialFeatureExtractor:

    def extract(self, bbox):

        x1, y1, x2, y2 = bbox

        width = x2 - x1
        height = y2 - y1

        cx = x1 + width / 2
        cy = y1 + height / 2

        area = width * height

        aspect_ratio = (
            height / width
            if width > 0
            else 0
        )

        features = np.array([
            cx,
            cy,
            width,
            height,
            area,
            aspect_ratio
        ], dtype=np.float32)

        return features