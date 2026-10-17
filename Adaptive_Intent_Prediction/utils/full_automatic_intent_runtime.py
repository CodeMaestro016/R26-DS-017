from __future__ import annotations

import dataclasses
from collections import defaultdict, deque
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import torch

from utils.automatic_pedestrian_tracker import AutomaticPedestrianTracker
from utils.occlusion_aware_track_continuation import OcclusionAwareTrackContinuation
from utils.probabilistic_runtime_feature_extractor import (
    ProbabilisticRuntimeFeatureExtractor,
)
from utils.runtime_occlusion_estimator import RuntimeOcclusionEstimator
from utils.unified_runtime_pipeline import UnifiedRuntimePipeline


class FullAutomaticIntentRuntime:
    """
    Raw frame -> automatic pedestrian track -> automatic occlusion probabilities
    -> probabilistic 525-D representation -> frozen intent/uncertainty/agent/explanation.

    No PIE bbox, pedestrian ID, occlusion label, or crossing label is required
    by this runtime class.
    """

    SEQUENCE_LENGTH = 30

    OCCLUSION_ORDER = {
        "none": 0,
        "part": 1,
        "full": 2,
    }

    def __init__(
        self,
        detector_checkpoint: str | Path = (
            "outputs/phase9/yolo_pedestrian/"
            "yolo11n_pie_occlusion_v2/weights/best.pt"
        ),
        tracker_config: str | Path = (
            "outputs/phase9/tracker_tuning/botsort_pie_selected.yaml"
        ),
        tracker_summary: str | Path = (
            "outputs/phase9/tracker_tuning/selected_tracker_summary.json"
        ),
        continuation_derivation: str | Path = (
            "outputs/phase9/tracker_tuning/candidate_derivation.json"
        ),
        imgsz: int = 960,
        device: str | None = None,
        unified_pipeline: UnifiedRuntimePipeline | None = None,
    ) -> None:
        detector_checkpoint = Path(detector_checkpoint)
        tracker_config = Path(tracker_config)
        tracker_summary = Path(tracker_summary)
        continuation_derivation = Path(continuation_derivation)

        for path in (
            detector_checkpoint,
            tracker_config,
            tracker_summary,
            continuation_derivation,
        ):
            if not path.exists():
                raise FileNotFoundError(
                    f"Required runtime artifact not found: {path}"
                )

        if device is None:
            device = (
                "cuda:0"
                if torch.cuda.is_available()
                else "cpu"
            )

        self.device = str(device)
        self.imgsz = int(imgsz)

        import json

        summary = json.loads(
            tracker_summary.read_text(
                encoding="utf-8"
            )
        )

        self.detector_conf = float(
            summary[
                "inference_conf_during_search"
            ]
        )

        self.detector_tracker = AutomaticPedestrianTracker(
            model_path=detector_checkpoint,
            tracker_config=str(tracker_config),
            conf=self.detector_conf,
            imgsz=self.imgsz,
            device=self.device,
        )

        self.continuation = (
            OcclusionAwareTrackContinuation
            .from_validation_artifacts(
                continuation_derivation
            )
        )

        # RuntimeOcclusionEstimator selects CUDA automatically when available.
        self.occlusion_estimator = RuntimeOcclusionEstimator(
            device=(
                "cuda"
                if self.device.startswith("cuda")
                else "cpu"
            )
        )

        self.feature_extractor = (
            ProbabilisticRuntimeFeatureExtractor(
                normalize_to_training_resolution=True
            )
        )

        self.unified_pipeline = (
            unified_pipeline
            or UnifiedRuntimePipeline()
        )

        self.feature_buffers: dict[
            int,
            deque[np.ndarray],
        ] = defaultdict(
            lambda: deque(
                maxlen=self.SEQUENCE_LENGTH
            )
        )

        self.occlusion_buffers: dict[
            int,
            deque[str],
        ] = defaultdict(
            lambda: deque(
                maxlen=self.SEQUENCE_LENGTH
            )
        )

        self.track_sources: dict[
            int,
            deque[str],
        ] = defaultdict(
            lambda: deque(
                maxlen=self.SEQUENCE_LENGTH
            )
        )

        self._known_tracks: set[int] = set()

    @staticmethod
    def _to_dict(
        value: Any,
    ) -> dict[str, Any]:
        if dataclasses.is_dataclass(value):
            return dataclasses.asdict(value)

        if isinstance(value, Mapping):
            return dict(value)

        if hasattr(value, "_asdict"):
            return dict(value._asdict())

        if hasattr(value, "__dict__"):
            return {
                key: item
                for key, item in vars(value).items()
                if not key.startswith("_")
            }

        raise TypeError(
            f"Unsupported runtime result type: {type(value).__name__}"
        )

    def reset(self) -> None:
        self.detector_tracker.reset()
        self.continuation.reset()

        for track_id in list(
            self._known_tracks
        ):
            self.feature_extractor.reset_track(
                track_id
            )

        self.feature_buffers.clear()
        self.occlusion_buffers.clear()
        self.track_sources.clear()
        self._known_tracks.clear()

    def _cleanup_expired(
        self,
        active_track_ids: set[int],
    ) -> list[int]:
        # The continuation layer returns a track throughout its complete
        # validation-derived continuation horizon. If a previously known ID is
        # absent from the returned active set, that continuation has expired.
        expired = sorted(
            self._known_tracks
            - active_track_ids
        )

        for track_id in expired:
            self.feature_buffers.pop(
                track_id,
                None,
            )
            self.occlusion_buffers.pop(
                track_id,
                None,
            )
            self.track_sources.pop(
                track_id,
                None,
            )

            self.feature_extractor.reset_track(
                track_id
            )

            self._known_tracks.discard(
                track_id
            )

        return expired

    def _maximum_occlusion(
        self,
        values: deque[str],
    ) -> str | None:
        if not values:
            return None

        return max(
            values,
            key=lambda name: (
                self.OCCLUSION_ORDER[
                    str(name)
                ]
            ),
        )

    def process_frame(
        self,
        frame: np.ndarray,
        frame_index: int,
    ) -> dict[str, Any]:
        raw_tracks = (
            self.detector_tracker
            .track_frame(
                frame
            )
        )

        valid_raw_tracks = [
            track
            for track in raw_tracks
            if int(
                track.track_id
            ) >= 0
        ]

        active_tracks = (
            self.continuation.update(
                observed_tracks=valid_raw_tracks,
                frame_index=int(
                    frame_index
                ),
                frame_shape=frame.shape,
            )
        )

        active_ids = {
            int(
                track.stable_track_id
            )
            for track in active_tracks
        }

        expired_ids = self._cleanup_expired(
            active_ids
        )

        frame_results = []

        for track in active_tracks:
            track_id = int(
                track.stable_track_id
            )

            self._known_tracks.add(
                track_id
            )

            bbox = tuple(
                float(value)
                for value in track.bbox
            )

            # This is still automatic even for a temporarily predicted bbox:
            # the estimator receives the current RGB frame and the temporally
            # continued track hypothesis. No annotation enters this branch.
            occlusion = (
                self.occlusion_estimator
                .predict(
                    frame=frame,
                    bbox=bbox,
                )
            )

            feature_result = (
                self.feature_extractor
                .extract_frame_with_probabilities(
                    frame=frame,
                    bbox=bbox,
                    occlusion_probabilities=(
                        occlusion[
                            "probabilities"
                        ]
                    ),
                    track_id=track_id,
                )
            )

            feature = np.asarray(
                feature_result[
                    "feature_vector"
                ],
                dtype=np.float32,
            )

            if feature.shape != (525,):
                raise ValueError(
                    f"Track {track_id} produced "
                    f"feature shape {feature.shape}, "
                    "expected (525,)."
                )

            self.feature_buffers[
                track_id
            ].append(
                feature
            )

            self.occlusion_buffers[
                track_id
            ].append(
                str(
                    occlusion[
                        "occlusion"
                    ]
                )
            )

            self.track_sources[
                track_id
            ].append(
                str(
                    track.source
                )
            )

            buffer_size = len(
                self.feature_buffers[
                    track_id
                ]
            )

            output: dict[str, Any] = {
                "track_id": track_id,
                "raw_track_id": int(
                    track.raw_track_id
                ),
                "bbox": bbox,
                "track_source": str(
                    track.source
                ),
                "missing_frames": int(
                    track.missing_frames
                ),
                "detector_confidence": (
                    None
                    if track.detector_confidence is None
                    else float(
                        track.detector_confidence
                    )
                ),
                "automatic_occlusion": str(
                    occlusion[
                        "occlusion"
                    ]
                ),
                "occlusion_probabilities": dict(
                    occlusion[
                        "probabilities"
                    ]
                ),
                "reliability_probabilities": {
                    "low": float(
                        feature_result[
                            "reliability_features"
                        ][0]
                    ),
                    "medium": float(
                        feature_result[
                            "reliability_features"
                        ][1]
                    ),
                    "high": float(
                        feature_result[
                            "reliability_features"
                        ][2]
                    ),
                },
                "buffer_size": buffer_size,
                "sequence_length": (
                    self.SEQUENCE_LENGTH
                ),
                "status": (
                    "READY"
                    if buffer_size
                    >= self.SEQUENCE_LENGTH
                    else "WARMING_UP"
                ),
                "runtime_result": None,
            }

            if (
                buffer_size
                >= self.SEQUENCE_LENGTH
            ):
                sequence = np.stack(
                    list(
                        self.feature_buffers[
                            track_id
                        ]
                    )
                ).astype(
                    np.float32
                )

                maximum_occlusion = (
                    self._maximum_occlusion(
                        self.occlusion_buffers[
                            track_id
                        ]
                    )
                )

                unified_result = (
                    self.unified_pipeline
                    .predict(
                        sequence,
                        maximum_occlusion=(
                            maximum_occlusion
                        ),
                    )
                )

                output[
                    "runtime_result"
                ] = self._to_dict(
                    unified_result
                )

            frame_results.append(
                output
            )

        return {
            "frame_index": int(
                frame_index
            ),
            "raw_tracker_count": len(
                valid_raw_tracks
            ),
            "active_continued_track_count": len(
                active_tracks
            ),
            "expired_track_ids": (
                expired_ids
            ),
            "tracks": frame_results,
        }
