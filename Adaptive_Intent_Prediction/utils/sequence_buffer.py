"""
Runtime Feature Sequence Buffer.

Collects 30 consecutive per-frame feature vectors
before sending them to the trained intent predictor.
"""

from collections import deque

import numpy as np


class FeatureSequenceBuffer:

    def __init__(
        self,
        sequence_length=30,
        feature_dimension=525
    ):
        if sequence_length <= 0:
            raise ValueError(
                "sequence_length must be positive."
            )

        if feature_dimension <= 0:
            raise ValueError(
                "feature_dimension must be positive."
            )

        self.sequence_length = int(
            sequence_length
        )

        self.feature_dimension = int(
            feature_dimension
        )

        self._features = deque(
            maxlen=self.sequence_length
        )

        self._metadata = deque(
            maxlen=self.sequence_length
        )

    def add(
        self,
        feature_vector,
        metadata=None
    ):
        feature_vector = np.asarray(
            feature_vector,
            dtype=np.float32
        ).reshape(-1)

        if (
            feature_vector.shape[0]
            != self.feature_dimension
        ):
            raise ValueError(
                f"Expected feature dimension "
                f"{self.feature_dimension}, but received "
                f"{feature_vector.shape[0]}."
            )

        if not np.isfinite(
            feature_vector
        ).all():
            raise ValueError(
                "Feature vector contains NaN "
                "or infinite values."
            )

        self._features.append(
            feature_vector
        )

        self._metadata.append(
            metadata
        )

        return self.is_ready

    @property
    def is_ready(self):

        return (
            len(self._features)
            == self.sequence_length
        )

    @property
    def progress(self):

        return {
            "collected": len(self._features),
            "required": self.sequence_length,
            "ready": self.is_ready
        }

    def get_sequence(self):

        if not self.is_ready:
            raise RuntimeError(
                "Sequence buffer is not ready. "
                f"Collected {len(self._features)}/"
                f"{self.sequence_length} frames."
            )

        sequence = np.stack(
            list(self._features),
            axis=0
        ).astype(
            np.float32,
            copy=False
        )

        expected_shape = (
            self.sequence_length,
            self.feature_dimension
        )

        if sequence.shape != expected_shape:
            raise ValueError(
                f"Expected buffered sequence shape "
                f"{expected_shape}, received "
                f"{sequence.shape}."
            )

        return sequence

    def get_metadata(self):

        if not self.is_ready:
            raise RuntimeError(
                "Sequence buffer is not ready."
            )

        return list(
            self._metadata
        )

    def reset(self):

        self._features.clear()
        self._metadata.clear()

    def __len__(self):

        return len(
            self._features
        )