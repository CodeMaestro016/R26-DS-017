from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Any
import json

import numpy as np


@dataclass
class ContinuedTrack:
    stable_track_id: int
    raw_track_id: int
    bbox: tuple[float, float, float, float]
    source: str
    detector_confidence: float | None
    missing_frames: int


@dataclass
class _TrackState:
    stable_track_id: int
    raw_track_id: int
    last_bbox: np.ndarray
    velocity_xy: np.ndarray
    last_observed_frame: int
    detector_confidence: float | None
    missing_frames: int = 0


class OcclusionAwareTrackContinuation:
    def __init__(self, max_missing_frames: int) -> None:
        if max_missing_frames < 1:
            raise ValueError("max_missing_frames must be >= 1.")
        self.max_missing_frames = int(max_missing_frames)
        self._states: dict[int, _TrackState] = {}

    @classmethod
    def from_validation_artifacts(
        cls,
        derivation_json: str | Path = (
            "outputs/phase9/tracker_tuning/candidate_derivation.json"
        ),
    ) -> "OcclusionAwareTrackContinuation":
        path = Path(derivation_json)
        if not path.exists():
            raise FileNotFoundError(
                f"Tracker tuning derivation not found: {path}"
            )
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(max_missing_frames=int(data["full_occlusion_run_p90"]))

    def reset(self) -> None:
        self._states.clear()

    @staticmethod
    def _center(bbox: np.ndarray) -> np.ndarray:
        x1, y1, x2, y2 = bbox
        return np.array([(x1 + x2) / 2.0, (y1 + y2) / 2.0], dtype=np.float32)

    @staticmethod
    def _predict_bbox(
        state: _TrackState,
        current_frame_index: int,
        frame_shape,
    ) -> np.ndarray:
        height = int(frame_shape[0])
        width = int(frame_shape[1])
        dt = max(1, int(current_frame_index - state.last_observed_frame))

        x1, y1, x2, y2 = state.last_bbox.astype(np.float32)
        box_w = max(1.0, float(x2 - x1))
        box_h = max(1.0, float(y2 - y1))

        center = (
            OcclusionAwareTrackContinuation._center(state.last_bbox)
            + state.velocity_xy * float(dt)
        )

        px1 = float(center[0] - box_w / 2.0)
        py1 = float(center[1] - box_h / 2.0)
        px2 = float(center[0] + box_w / 2.0)
        py2 = float(center[1] + box_h / 2.0)

        px1 = max(0.0, min(float(width - 1), px1))
        py1 = max(0.0, min(float(height - 1), py1))
        px2 = max(0.0, min(float(width), px2))
        py2 = max(0.0, min(float(height), py2))

        if px2 <= px1:
            px2 = min(float(width), px1 + 1.0)
        if py2 <= py1:
            py2 = min(float(height), py1 + 1.0)

        return np.array([px1, py1, px2, py2], dtype=np.float32)

    def update(
        self,
        observed_tracks: Iterable[Any],
        frame_index: int,
        frame_shape,
    ) -> list[ContinuedTrack]:
        frame_index = int(frame_index)
        observed_ids: set[int] = set()

        for observed in observed_tracks:
            raw_track_id = int(observed.track_id)
            if raw_track_id < 0:
                continue

            observed_ids.add(raw_track_id)
            bbox = np.asarray(observed.bbox, dtype=np.float32)
            confidence = float(observed.confidence)

            state = self._states.get(raw_track_id)
            if state is None:
                self._states[raw_track_id] = _TrackState(
                    stable_track_id=raw_track_id,
                    raw_track_id=raw_track_id,
                    last_bbox=bbox,
                    velocity_xy=np.zeros(2, dtype=np.float32),
                    last_observed_frame=frame_index,
                    detector_confidence=confidence,
                    missing_frames=0,
                )
                continue

            dt = max(1, frame_index - state.last_observed_frame)
            state.velocity_xy = (
                self._center(bbox) - self._center(state.last_bbox)
            ) / float(dt)
            state.last_bbox = bbox
            state.last_observed_frame = frame_index
            state.detector_confidence = confidence
            state.missing_frames = 0

        outputs: list[ContinuedTrack] = []
        expired: list[int] = []

        for raw_track_id, state in self._states.items():
            if raw_track_id in observed_ids:
                outputs.append(
                    ContinuedTrack(
                        stable_track_id=state.stable_track_id,
                        raw_track_id=state.raw_track_id,
                        bbox=tuple(float(v) for v in state.last_bbox),
                        source="OBSERVED",
                        detector_confidence=state.detector_confidence,
                        missing_frames=0,
                    )
                )
                continue

            state.missing_frames = frame_index - state.last_observed_frame

            if state.missing_frames > self.max_missing_frames:
                expired.append(raw_track_id)
                continue

            predicted_bbox = self._predict_bbox(
                state,
                current_frame_index=frame_index,
                frame_shape=frame_shape,
            )

            outputs.append(
                ContinuedTrack(
                    stable_track_id=state.stable_track_id,
                    raw_track_id=state.raw_track_id,
                    bbox=tuple(float(v) for v in predicted_bbox),
                    source="PREDICTED_MISSING",
                    detector_confidence=None,
                    missing_frames=state.missing_frames,
                )
            )

        for raw_track_id in expired:
            self._states.pop(raw_track_id, None)

        return outputs
