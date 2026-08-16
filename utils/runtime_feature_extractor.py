"""
Runtime per-frame feature extraction for the final intent model.

This module reproduces the training feature order exactly:

    512 appearance features
    + 6 spatial features
    + 4 motion features
    + 3 Bayesian observation-reliability probabilities
    = 525 features per frame

The final three values are ordered as:
    P(reliability=low), P(reliability=medium), P(reliability=high)

For new videos, frames and bounding boxes are optionally rescaled to the
PIE training resolution (1920 x 1080) before feature extraction. This is
important because the trained spatial and motion features use raw pixels.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Hashable, Optional, Sequence, Tuple

import cv2
import numpy as np

from utils.bayesian_network import BayesianSemanticNetwork
from utils.cropper import PedestrianCropper
from utils.feature_extractor import AppearanceFeatureExtractor
from utils.feature_fusion import FeatureFusion
from utils.motion import MotionFeatureExtractor
from utils.semantic_mapper import SemanticMapper
from utils.spatial import SpatialFeatureExtractor


BBox = Tuple[float, float, float, float]


class RuntimeFeatureExtractor:
    """Create one 525-dimensional feature vector per pedestrian per frame."""

    RAW_FEATURE_DIMENSION = 522
    RELIABILITY_FEATURE_DIMENSION = 3
    FINAL_FEATURE_DIMENSION = 525

    TRAINING_WIDTH = 1920
    TRAINING_HEIGHT = 1080

    def __init__(
        self,
        bayesian_model_path: Optional[str] = None,
        motion_model_path: str = "outputs/phase4/motion_kmeans.pkl",
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
            raise ValueError("training_resolution must contain positive values.")

        self.cropper = PedestrianCropper()
        self.appearance = AppearanceFeatureExtractor()
        self.spatial = SpatialFeatureExtractor()
        self.motion = MotionFeatureExtractor()
        self.fusion = FeatureFusion()

        self.semantic_mapper = SemanticMapper(
            motion_model_path=motion_model_path
        )

        resolved_bayesian_path = self._resolve_bayesian_model_path(
            bayesian_model_path
        )
        self.bayesian_model_path = resolved_bayesian_path
        self.bayesian_network = BayesianSemanticNetwork.load(
            resolved_bayesian_path
        )

        # Separate motion history for each tracked pedestrian.
        self._previous_spatial: Dict[Hashable, np.ndarray] = {}

    @staticmethod
    def _resolve_bayesian_model_path(
        supplied_path: Optional[str],
    ) -> Path:
        if supplied_path is not None:
            path = Path(supplied_path)
            if not path.exists():
                raise FileNotFoundError(
                    f"Bayesian model not found: {path}"
                )
            return path

        preferred_candidates = [
            Path("outputs/phase4/bayesian_network.pkl"),
            Path("outputs/phase4/bayesian_semantic_network.pkl"),
            Path("outputs/phase4/final_bayesian_network.pkl"),
            Path("outputs/phase4/bayesian_model.pkl"),
            Path("outputs/phase4/bayesian_network.joblib"),
            Path("outputs/phase4/bayesian_semantic_network.joblib"),
        ]

        for candidate in preferred_candidates:
            if candidate.exists():
                return candidate

        phase4_directory = Path("outputs/phase4")
        discovered = []

        if phase4_directory.exists():
            for pattern in ("*bayesian*.pkl", "*bayesian*.joblib"):
                discovered.extend(phase4_directory.rglob(pattern))

        # Avoid accidentally loading temporary fold/OOF models.
        discovered = sorted(
            {
                path
                for path in discovered
                if not any(
                    token in path.name.lower()
                    for token in ("fold", "oof", "temporary", "temp")
                )
            }
        )

        if len(discovered) == 1:
            return discovered[0]

        if len(discovered) > 1:
            formatted = "\n".join(f"  - {path}" for path in discovered)
            raise RuntimeError(
                "Multiple Bayesian model files were found. Pass the final "
                "model explicitly with bayesian_model_path. Candidates:\n"
                f"{formatted}"
            )

        raise FileNotFoundError(
            "Could not locate the final Bayesian model under outputs/phase4. "
            "Pass its path using bayesian_model_path."
        )

    @staticmethod
    def normalize_occlusion_label(value: Any) -> str:
        """Map PIE/manual occlusion labels to low, medium, or high."""
        text = str(value).strip().lower()

        mapping = {
            "none": "low",
            "no": "low",
            "not occluded": "low",
            "not-occluded": "low",
            "0": "low",
            "low": "low",
            "part": "medium",
            "partial": "medium",
            "partially occluded": "medium",
            "partially-occluded": "medium",
            "1": "medium",
            "medium": "medium",
            "full": "high",
            "fully occluded": "high",
            "fully-occluded": "high",
            "2": "high",
            "high": "high",
        }

        if text not in mapping:
            raise ValueError(
                f"Unsupported occlusion label '{value}'. Expected PIE labels "
                "none/part/full or runtime labels low/medium/high."
            )

        return mapping[text]

    @staticmethod
    def _validate_bbox(bbox: Sequence[float]) -> BBox:
        if len(bbox) != 4:
            raise ValueError("bbox must contain x1, y1, x2, y2.")

        x1, y1, x2, y2 = (float(value) for value in bbox)

        if not np.isfinite([x1, y1, x2, y2]).all():
            raise ValueError("bbox contains NaN or infinite values.")

        if x2 <= x1 or y2 <= y1:
            raise ValueError(f"Invalid bbox coordinates: {bbox}")

        return x1, y1, x2, y2

    def _prepare_frame_and_bbox(
        self,
        frame: np.ndarray,
        bbox: Sequence[float],
    ) -> Tuple[np.ndarray, Tuple[int, int, int, int], Dict[str, float]]:
        if not isinstance(frame, np.ndarray):
            raise TypeError("frame must be a NumPy array.")

        if frame.ndim != 3 or frame.shape[2] != 3:
            raise ValueError(
                f"Expected a BGR image with shape (H, W, 3), got {frame.shape}."
            )

        if frame.size == 0:
            raise ValueError("frame is empty.")

        x1, y1, x2, y2 = self._validate_bbox(bbox)
        source_height, source_width = frame.shape[:2]

        # Clip before scaling so detector boxes cannot leave the image.
        x1 = float(np.clip(x1, 0, source_width - 1))
        y1 = float(np.clip(y1, 0, source_height - 1))
        x2 = float(np.clip(x2, x1 + 1, source_width))
        y2 = float(np.clip(y2, y1 + 1, source_height))

        if self.normalize_to_training_resolution:
            scale_x = self.training_width / float(source_width)
            scale_y = self.training_height / float(source_height)

            prepared_frame = cv2.resize(
                frame,
                (self.training_width, self.training_height),
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

        prepared_height, prepared_width = prepared_frame.shape[:2]
        px1, py1, px2, py2 = prepared_bbox
        px1 = int(np.clip(px1, 0, prepared_width - 1))
        py1 = int(np.clip(py1, 0, prepared_height - 1))
        px2 = int(np.clip(px2, px1 + 1, prepared_width))
        py2 = int(np.clip(py2, py1 + 1, prepared_height))
        prepared_bbox = (px1, py1, px2, py2)

        transform_metadata = {
            "source_width": float(source_width),
            "source_height": float(source_height),
            "prepared_width": float(prepared_width),
            "prepared_height": float(prepared_height),
            "scale_x": float(scale_x),
            "scale_y": float(scale_y),
        }

        return prepared_frame, prepared_bbox, transform_metadata

    def reset_track(self, track_id: Optional[Hashable] = None) -> None:
        """Reset motion history for one track, or all tracks when omitted."""
        if track_id is None:
            self._previous_spatial.clear()
        else:
            self._previous_spatial.pop(track_id, None)

    def extract_frame(
        self,
        frame: np.ndarray,
        bbox: Sequence[float],
        occlusion: Any,
        track_id: Hashable = "default",
    ) -> Dict[str, Any]:
        """Extract one runtime feature vector and supporting metadata."""
        prepared_frame, prepared_bbox, transform_metadata = (
            self._prepare_frame_and_bbox(frame, bbox)
        )

        crop = self.cropper.crop(prepared_frame, prepared_bbox)
        appearance = self.appearance.extract(crop)
        spatial = self.spatial.extract(prepared_bbox)

        previous_spatial = self._previous_spatial.get(track_id)
        if previous_spatial is None:
            motion = np.zeros(4, dtype=np.float32)
        else:
            motion = self.motion.extract(previous_spatial, spatial)

        self._previous_spatial[track_id] = spatial.copy()

        raw_feature_vector = self.fusion.fuse(
            appearance,
            spatial,
            motion,
        ).astype(np.float32, copy=False)

        if raw_feature_vector.shape != (self.RAW_FEATURE_DIMENSION,):
            raise ValueError(
                "Raw runtime feature vector has incorrect shape: "
                f"{raw_feature_vector.shape}"
            )

        occlusion_level = self.normalize_occlusion_label(occlusion)
        prepared_height, prepared_width = prepared_frame.shape[:2]

        semantic_states = self.semantic_mapper.map(
            speed=float(motion[2]),
            center_x=float(spatial[0]),
            center_y=float(spatial[1]),
            image_width=int(prepared_width),
            image_height=int(prepared_height),
            occlusion=occlusion_level,
        )

        bayesian_result = self.bayesian_network.predict(
            motion=semantic_states["motion"],
            horizontal=semantic_states["horizontal"],
            vertical=semantic_states["vertical"],
            occlusion=semantic_states["occlusion"],
        )

        full_bayesian_vector = np.asarray(
            bayesian_result["feature_vector"],
            dtype=np.float32,
        ).reshape(-1)

        if full_bayesian_vector.shape != (5,):
            raise ValueError(
                "Bayesian feature vector must contain five probabilities, "
                f"got {full_bayesian_vector.shape}."
            )

        # Final model is reliability-only: append Bayesian entries 2:5.
        reliability_features = full_bayesian_vector[2:5]
        final_feature_vector = np.concatenate(
            [raw_feature_vector, reliability_features]
        ).astype(np.float32, copy=False)

        if final_feature_vector.shape != (self.FINAL_FEATURE_DIMENSION,):
            raise ValueError(
                "Final runtime feature vector has incorrect shape: "
                f"{final_feature_vector.shape}"
            )

        if not np.isfinite(final_feature_vector).all():
            raise ValueError("Final runtime feature vector contains invalid values.")

        return {
            "feature_vector": final_feature_vector,
            "raw_feature_vector": raw_feature_vector,
            "appearance_features": appearance.astype(np.float32, copy=False),
            "spatial_features": spatial,
            "motion_features": motion,
            "reliability_features": reliability_features,
            "bayesian_feature_vector": full_bayesian_vector,
            "semantic_states": semantic_states,
            "observation_reliability": bayesian_result[
                "observation_reliability"
            ],
            "intention_tendency": bayesian_result["intention_tendency"],
            "occlusion_level": occlusion_level,
            "prepared_bbox": prepared_bbox,
            "transform_metadata": transform_metadata,
        }
