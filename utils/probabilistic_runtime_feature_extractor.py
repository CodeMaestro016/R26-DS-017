from __future__ import annotations

from typing import Dict, Hashable, Mapping, Sequence, Any

import numpy as np

from utils.runtime_feature_extractor import RuntimeFeatureExtractor


class ProbabilisticRuntimeFeatureExtractor(RuntimeFeatureExtractor):
    """
    RuntimeFeatureExtractor variant that accepts learned occlusion probabilities.

    The original final intent model expects:
        512 appearance
        + 6 spatial
        + 4 motion
        + 3 Bayesian observation-reliability probabilities
        = 525 features.

    Instead of collapsing automatic occlusion estimation to one hard label,
    this class marginalizes the existing Bayesian reliability output over:
        P(none), P(part), P(full).

    Mapping to the original Bayesian semantic states:
        none -> low occlusion
        part -> medium occlusion
        full -> high occlusion

    Important:
    - The intent model is NOT retrained.
    - The Bayesian network is NOT retrained.
    - No manual runtime threshold is introduced.
    - A one-hot occlusion distribution reproduces the legacy hard-label path.
    """

    OCCLUSION_TO_LEVEL = {
        "none": "low",
        "part": "medium",
        "full": "high",
    }

    @staticmethod
    def _normalize_probabilities(
        probabilities: Mapping[str, float],
    ) -> Dict[str, float]:
        required = ("none", "part", "full")

        missing = [
            name
            for name in required
            if name not in probabilities
        ]

        if missing:
            raise KeyError(
                "Occlusion probabilities are missing keys: "
                f"{missing}"
            )

        values = np.asarray(
            [
                float(probabilities[name])
                for name in required
            ],
            dtype=np.float64,
        )

        if not np.isfinite(values).all():
            raise ValueError(
                "Occlusion probabilities contain NaN or infinity."
            )

        if np.any(values < 0.0):
            raise ValueError(
                "Occlusion probabilities must be non-negative."
            )

        total = float(values.sum())

        if total <= 0.0:
            raise ValueError(
                "Occlusion probabilities must sum to a positive value."
            )

        values /= total

        return {
            name: float(values[index])
            for index, name in enumerate(required)
        }

    def _bayesian_for_occlusion_level(
        self,
        *,
        motion: np.ndarray,
        spatial: np.ndarray,
        prepared_width: int,
        prepared_height: int,
        occlusion_level: str,
    ) -> Dict[str, Any]:
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

        feature_vector = np.asarray(
            bayesian_result["feature_vector"],
            dtype=np.float32,
        ).reshape(-1)

        if feature_vector.shape != (5,):
            raise ValueError(
                "Bayesian feature vector must have shape (5,), "
                f"got {feature_vector.shape}."
            )

        return {
            "semantic_states": semantic_states,
            "bayesian_result": bayesian_result,
            "feature_vector": feature_vector,
        }

    def extract_frame_with_probabilities(
        self,
        frame: np.ndarray,
        bbox: Sequence[float],
        occlusion_probabilities: Mapping[str, float],
        track_id: Hashable = "default",
    ) -> Dict[str, Any]:
        """
        Produce one 525-D runtime vector using soft occlusion evidence.
        """
        probabilities = self._normalize_probabilities(
            occlusion_probabilities
        )

        prepared_frame, prepared_bbox, transform_metadata = (
            self._prepare_frame_and_bbox(
                frame,
                bbox,
            )
        )

        crop = self.cropper.crop(
            prepared_frame,
            prepared_bbox,
        )

        appearance = self.appearance.extract(
            crop
        )

        spatial = self.spatial.extract(
            prepared_bbox
        )

        previous_spatial = self._previous_spatial.get(
            track_id
        )

        if previous_spatial is None:
            motion = np.zeros(
                4,
                dtype=np.float32,
            )
        else:
            motion = self.motion.extract(
                previous_spatial,
                spatial,
            )

        self._previous_spatial[
            track_id
        ] = spatial.copy()

        raw_feature_vector = self.fusion.fuse(
            appearance,
            spatial,
            motion,
        ).astype(
            np.float32,
            copy=False,
        )

        if raw_feature_vector.shape != (
            self.RAW_FEATURE_DIMENSION,
        ):
            raise ValueError(
                "Raw runtime feature vector has incorrect shape: "
                f"{raw_feature_vector.shape}"
            )

        prepared_height, prepared_width = (
            prepared_frame.shape[:2]
        )

        per_state = {}

        for occlusion_name, occlusion_level in (
            ("none", "low"),
            ("part", "medium"),
            ("full", "high"),
        ):
            per_state[
                occlusion_name
            ] = self._bayesian_for_occlusion_level(
                motion=motion,
                spatial=spatial,
                prepared_width=prepared_width,
                prepared_height=prepared_height,
                occlusion_level=occlusion_level,
            )

        mixed_bayesian = np.zeros(
            5,
            dtype=np.float32,
        )

        for occlusion_name in (
            "none",
            "part",
            "full",
        ):
            mixed_bayesian += (
                float(
                    probabilities[
                        occlusion_name
                    ]
                )
                * per_state[
                    occlusion_name
                ][
                    "feature_vector"
                ]
            )

        # Final intent model uses only Bayesian reliability entries 2:5.
        reliability_features = mixed_bayesian[
            2:5
        ].astype(
            np.float32,
            copy=False,
        )

        reliability_sum = float(
            reliability_features.sum()
        )

        # The Bayesian reliability vector should remain a valid probability
        # distribution after marginalization. Normalize only for numerical drift.
        if reliability_sum <= 0.0:
            raise ValueError(
                "Mixed reliability probabilities have non-positive sum."
            )

        reliability_features = (
            reliability_features
            / reliability_sum
        ).astype(
            np.float32,
            copy=False,
        )

        final_feature_vector = np.concatenate(
            [
                raw_feature_vector,
                reliability_features,
            ]
        ).astype(
            np.float32,
            copy=False,
        )

        if final_feature_vector.shape != (
            self.FINAL_FEATURE_DIMENSION,
        ):
            raise ValueError(
                "Final runtime feature vector has incorrect shape: "
                f"{final_feature_vector.shape}"
            )

        if not np.isfinite(
            final_feature_vector
        ).all():
            raise ValueError(
                "Final runtime feature vector contains invalid values."
            )

        dominant_occlusion = max(
            probabilities,
            key=probabilities.get,
        )

        return {
            "feature_vector": final_feature_vector,
            "raw_feature_vector": raw_feature_vector,
            "appearance_features": np.asarray(
                appearance,
                dtype=np.float32,
            ),
            "spatial_features": np.asarray(
                spatial,
                dtype=np.float32,
            ),
            "motion_features": np.asarray(
                motion,
                dtype=np.float32,
            ),
            "reliability_features": reliability_features,
            "mixed_bayesian_feature_vector": mixed_bayesian,
            "occlusion_probabilities": probabilities,
            "dominant_occlusion": dominant_occlusion,
            "dominant_occlusion_level": (
                self.OCCLUSION_TO_LEVEL[
                    dominant_occlusion
                ]
            ),
            "per_occlusion_bayesian": {
                name: {
                    "feature_vector": (
                        per_state[name][
                            "feature_vector"
                        ]
                    ),
                    "semantic_states": (
                        per_state[name][
                            "semantic_states"
                        ]
                    ),
                }
                for name in (
                    "none",
                    "part",
                    "full",
                )
            },
            "prepared_bbox": prepared_bbox,
            "transform_metadata": transform_metadata,
        }
