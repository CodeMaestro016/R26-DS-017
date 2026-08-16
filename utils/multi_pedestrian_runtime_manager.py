from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Hashable

import numpy as np

from utils.runtime_feature_extractor import RuntimeFeatureExtractor
from utils.unified_runtime_pipeline import (
    UnifiedRuntimePipeline,
    UnifiedRuntimeResult,
)


OCCLUSION_RANK = {
    "low": 0,
    "medium": 1,
    "high": 2,
}


@dataclass
class TrackRuntimeUpdate:
    track_id: str
    status: str
    buffered_frames: int
    required_frames: int
    ready: bool
    normalized_occlusion: str
    maximum_buffer_occlusion: str
    final_result: dict[str, Any] | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class MultiPedestrianRuntimeManager:
    """
    Per-track runtime manager for the final pedestrian-intent system.

    Expected upstream input for every visible pedestrian:
        frame
        bbox = (x1, y1, x2, y2)
        track_id
        occlusion label

    The manager:
        1) extracts the exact frozen 525-D feature vector,
        2) maintains one 30-frame rolling sequence per track,
        3) preserves motion history independently per track,
        4) runs the unified intent/uncertainty/decision/explanation pipeline
           once the track has 30 observations,
        5) can remove stale tracks cleanly.

    Detector/tracker choice is intentionally decoupled from the research
    component. Any upstream detector/tracker can feed stable track IDs + bboxes.
    """

    def __init__(
        self,
        *,
        sequence_length: int = 30,
        bayesian_model_path: str | Path | None = None,
        explanation_steps: int = 32,
        normalize_to_training_resolution: bool = True,
    ) -> None:
        if sequence_length != 30:
            raise ValueError(
                "The frozen Transformer was trained with sequence_length=30. "
                "Do not change this at runtime."
            )

        self.sequence_length = int(sequence_length)

        self.feature_extractor = RuntimeFeatureExtractor(
            bayesian_model_path=bayesian_model_path,
            normalize_to_training_resolution=(
                normalize_to_training_resolution
            ),
        )

        self.pipeline = UnifiedRuntimePipeline(
            explanation_steps=explanation_steps,
        )

        self._feature_buffers: dict[str, deque[np.ndarray]] = {}
        self._occlusion_buffers: dict[str, deque[str]] = {}

    @staticmethod
    def _key(track_id: Hashable) -> str:
        return str(track_id)

    @staticmethod
    def _max_occlusion(levels: list[str]) -> str:
        if not levels:
            return "unknown"

        unsupported = [
            level
            for level in levels
            if level not in OCCLUSION_RANK
        ]

        if unsupported:
            raise ValueError(
                f"Unsupported normalized occlusion levels: {unsupported}"
            )

        return max(
            levels,
            key=lambda value: OCCLUSION_RANK[value],
        )

    def _ensure_track(self, track_id: str) -> None:
        if track_id not in self._feature_buffers:
            self._feature_buffers[track_id] = deque(
                maxlen=self.sequence_length
            )
            self._occlusion_buffers[track_id] = deque(
                maxlen=self.sequence_length
            )

    def update_track(
        self,
        *,
        frame: np.ndarray,
        bbox: tuple[float, float, float, float],
        track_id: Hashable,
        occlusion: Any,
    ) -> TrackRuntimeUpdate:
        key = self._key(track_id)
        self._ensure_track(key)

        extracted = self.feature_extractor.extract_frame(
            frame=frame,
            bbox=bbox,
            occlusion=occlusion,
            track_id=key,
        )

        vector = np.asarray(
            extracted["feature_vector"],
            dtype=np.float32,
        )

        if vector.shape != (525,):
            raise ValueError(
                f"Track {key} produced feature shape {vector.shape}; "
                "expected (525,)."
            )

        normalized_occlusion = str(
            extracted["occlusion_level"]
        )

        self._feature_buffers[key].append(
            vector
        )
        self._occlusion_buffers[key].append(
            normalized_occlusion
        )

        buffered = len(
            self._feature_buffers[key]
        )

        maximum_buffer_occlusion = (
            self._max_occlusion(
                list(
                    self._occlusion_buffers[key]
                )
            )
        )

        if buffered < self.sequence_length:
            return TrackRuntimeUpdate(
                track_id=key,
                status="WARMING_UP",
                buffered_frames=buffered,
                required_frames=self.sequence_length,
                ready=False,
                normalized_occlusion=normalized_occlusion,
                maximum_buffer_occlusion=maximum_buffer_occlusion,
                final_result=None,
            )

        sequence = np.stack(
            list(
                self._feature_buffers[key]
            ),
            axis=0,
        ).astype(
            np.float32,
            copy=False,
        )

        result: UnifiedRuntimeResult = (
            self.pipeline.predict(
                sequence,
                maximum_occlusion=(
                    maximum_buffer_occlusion
                ),
            )
        )

        return TrackRuntimeUpdate(
            track_id=key,
            status="READY",
            buffered_frames=buffered,
            required_frames=self.sequence_length,
            ready=True,
            normalized_occlusion=normalized_occlusion,
            maximum_buffer_occlusion=maximum_buffer_occlusion,
            final_result=result.to_dict(),
        )

    def process_frame(
        self,
        *,
        frame: np.ndarray,
        tracked_pedestrians: list[dict[str, Any]],
    ) -> list[TrackRuntimeUpdate]:
        """
        Process all tracked pedestrians visible in one video frame.

        Each item must contain:
            track_id
            bbox
            occlusion

        Example:
            {
                "track_id": 12,
                "bbox": (x1, y1, x2, y2),
                "occlusion": "part",
            }
        """
        updates = []

        for pedestrian in tracked_pedestrians:
            missing = [
                key
                for key in (
                    "track_id",
                    "bbox",
                    "occlusion",
                )
                if key not in pedestrian
            ]

            if missing:
                raise KeyError(
                    f"Tracked pedestrian is missing fields: {missing}"
                )

            updates.append(
                self.update_track(
                    frame=frame,
                    bbox=tuple(
                        pedestrian["bbox"]
                    ),
                    track_id=pedestrian[
                        "track_id"
                    ],
                    occlusion=pedestrian[
                        "occlusion"
                    ],
                )
            )

        return updates

    def reset_track(
        self,
        track_id: Hashable,
    ) -> None:
        key = self._key(track_id)

        self._feature_buffers.pop(
            key,
            None,
        )
        self._occlusion_buffers.pop(
            key,
            None,
        )

        # RuntimeFeatureExtractor keeps motion history per track.
        self.feature_extractor.reset_track(
            key
        )

    def remove_missing_tracks(
        self,
        active_track_ids: list[Hashable],
    ) -> list[str]:
        active = {
            self._key(track_id)
            for track_id in active_track_ids
        }

        existing = set(
            self._feature_buffers.keys()
        )

        removed = sorted(
            existing - active
        )

        for track_id in removed:
            self.reset_track(
                track_id
            )

        return removed

    def reset_all(self) -> None:
        for track_id in list(
            self._feature_buffers.keys()
        ):
            self.reset_track(
                track_id
            )

    def get_track_buffer_size(
        self,
        track_id: Hashable,
    ) -> int:
        key = self._key(track_id)

        if key not in self._feature_buffers:
            return 0

        return len(
            self._feature_buffers[key]
        )

    def active_track_ids(self) -> list[str]:
        return sorted(
            self._feature_buffers.keys()
        )
