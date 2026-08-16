from __future__ import annotations

from typing import Dict, Sequence, Tuple

import cv2
import numpy as np

from utils.cropper import PedestrianCropper
from utils.feature_extractor import AppearanceFeatureExtractor
from utils.spatial import SpatialFeatureExtractor


class VisualOcclusionFeatureExtractor:
    """
    Extract occlusion-estimation features WITHOUT requiring an occlusion label.

    Feature order:
        512-D ResNet18 appearance
        + 6-D spatial geometry
        = 518-D

    Frame/bbox normalization mirrors RuntimeFeatureExtractor:
        source frame/bbox -> PIE training resolution 1920x1080 -> crop/features
    """

    FEATURE_DIMENSION = 518
    TRAINING_WIDTH = 1920
    TRAINING_HEIGHT = 1080

    def __init__(
        self,
        normalize_to_training_resolution: bool = True,
        training_resolution: Tuple[int, int] = (
            TRAINING_WIDTH,
            TRAINING_HEIGHT,
        ),
    ) -> None:
        self.normalize_to_training_resolution = bool(
            normalize_to_training_resolution
        )
        self.training_width = int(training_resolution[0])
        self.training_height = int(training_resolution[1])

        if self.training_width <= 0 or self.training_height <= 0:
            raise ValueError(
                "training_resolution must contain positive values."
            )

        self.cropper = PedestrianCropper()
        self.appearance = AppearanceFeatureExtractor()
        self.spatial = SpatialFeatureExtractor()

    @staticmethod
    def _validate_bbox(
        bbox: Sequence[float],
    ) -> tuple[float, float, float, float]:
        if len(bbox) != 4:
            raise ValueError(
                "bbox must contain x1, y1, x2, y2."
            )

        x1, y1, x2, y2 = (
            float(value)
            for value in bbox
        )

        if not np.isfinite(
            [x1, y1, x2, y2]
        ).all():
            raise ValueError(
                "bbox contains NaN or infinite values."
            )

        if x2 <= x1 or y2 <= y1:
            raise ValueError(
                f"Invalid bbox coordinates: {bbox}"
            )

        return x1, y1, x2, y2

    def _prepare_frame_and_bbox(
        self,
        frame: np.ndarray,
        bbox: Sequence[float],
    ) -> tuple[
        np.ndarray,
        tuple[int, int, int, int],
        Dict[str, float],
    ]:
        if not isinstance(frame, np.ndarray):
            raise TypeError(
                "frame must be a NumPy array."
            )

        if (
            frame.ndim != 3
            or frame.shape[2] != 3
        ):
            raise ValueError(
                "Expected BGR frame shape (H,W,3), "
                f"got {frame.shape}."
            )

        x1, y1, x2, y2 = self._validate_bbox(
            bbox
        )

        source_height, source_width = (
            frame.shape[:2]
        )

        x1 = float(
            np.clip(
                x1,
                0,
                source_width - 1,
            )
        )
        y1 = float(
            np.clip(
                y1,
                0,
                source_height - 1,
            )
        )
        x2 = float(
            np.clip(
                x2,
                x1 + 1,
                source_width,
            )
        )
        y2 = float(
            np.clip(
                y2,
                y1 + 1,
                source_height,
            )
        )

        if self.normalize_to_training_resolution:
            scale_x = (
                self.training_width
                / float(source_width)
            )
            scale_y = (
                self.training_height
                / float(source_height)
            )

            prepared_frame = cv2.resize(
                frame,
                (
                    self.training_width,
                    self.training_height,
                ),
                interpolation=cv2.INTER_LINEAR,
            )

            prepared_bbox = (
                int(round(x1 * scale_x)),
                int(round(y1 * scale_y)),
                int(round(x2 * scale_x)),
                int(round(y2 * scale_y)),
            )
        else:
            scale_x = 1.0
            scale_y = 1.0
            prepared_frame = frame
            prepared_bbox = (
                int(round(x1)),
                int(round(y1)),
                int(round(x2)),
                int(round(y2)),
            )

        prepared_height, prepared_width = (
            prepared_frame.shape[:2]
        )

        px1, py1, px2, py2 = prepared_bbox

        px1 = int(
            np.clip(
                px1,
                0,
                prepared_width - 1,
            )
        )
        py1 = int(
            np.clip(
                py1,
                0,
                prepared_height - 1,
            )
        )
        px2 = int(
            np.clip(
                px2,
                px1 + 1,
                prepared_width,
            )
        )
        py2 = int(
            np.clip(
                py2,
                py1 + 1,
                prepared_height,
            )
        )

        prepared_bbox = (
            px1,
            py1,
            px2,
            py2,
        )

        metadata = {
            "source_width": float(
                source_width
            ),
            "source_height": float(
                source_height
            ),
            "prepared_width": float(
                prepared_width
            ),
            "prepared_height": float(
                prepared_height
            ),
            "scale_x": float(scale_x),
            "scale_y": float(scale_y),
        }

        return (
            prepared_frame,
            prepared_bbox,
            metadata,
        )

    def extract(
        self,
        frame: np.ndarray,
        bbox: Sequence[float],
    ) -> Dict[str, np.ndarray]:
        (
            prepared_frame,
            prepared_bbox,
            metadata,
        ) = self._prepare_frame_and_bbox(
            frame,
            bbox,
        )

        crop = self.cropper.crop(
            prepared_frame,
            prepared_bbox,
        )

        appearance = (
            self.appearance.extract(crop)
            .astype(
                np.float32,
                copy=False,
            )
            .reshape(-1)
        )

        spatial = (
            self.spatial.extract(
                prepared_bbox
            )
            .astype(
                np.float32,
                copy=False,
            )
            .reshape(-1)
        )

        if appearance.shape != (512,):
            raise ValueError(
                "Expected 512 appearance features, "
                f"got {appearance.shape}."
            )

        if spatial.shape != (6,):
            raise ValueError(
                "Expected 6 spatial features, "
                f"got {spatial.shape}."
            )

        features = np.concatenate(
            [
                appearance,
                spatial,
            ]
        ).astype(
            np.float32,
            copy=False,
        )

        if features.shape != (
            self.FEATURE_DIMENSION,
        ):
            raise ValueError(
                "Occlusion feature vector shape "
                f"is {features.shape}, expected "
                f"({self.FEATURE_DIMENSION},)."
            )

        if not np.isfinite(features).all():
            raise ValueError(
                "Occlusion feature vector "
                "contains invalid values."
            )

        return {
            "feature_vector": features,
            "appearance_features": appearance,
            "spatial_features": spatial,
            "prepared_bbox": np.asarray(
                prepared_bbox,
                dtype=np.int32,
            ),
            "transform_metadata": metadata,
        }
