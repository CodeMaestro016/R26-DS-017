from __future__ import annotations

from pathlib import Path
from typing import Sequence

import numpy as np
import torch

from models.occlusion_estimator import (
    LearnedOcclusionEstimator,
)
from utils.visual_occlusion_feature_extractor import (
    VisualOcclusionFeatureExtractor,
)


class RuntimeOcclusionEstimator:
    """
    Predict PIE-style occlusion state directly from frame + bbox.

    Runtime output:
        none / part / full
        class probabilities

    No fixed confidence/visibility thresholds are used.
    """

    DEFAULT_CHECKPOINT = Path(
        "outputs/phase9/occlusion_estimator/"
        "learned_occlusion_estimator_best.pt"
    )

    def __init__(
        self,
        checkpoint_path: str | Path = DEFAULT_CHECKPOINT,
        device: str | None = None,
    ) -> None:
        checkpoint_path = Path(
            checkpoint_path
        )

        if not checkpoint_path.exists():
            raise FileNotFoundError(
                f"Occlusion checkpoint not found: "
                f"{checkpoint_path}"
            )

        if device is None:
            device = (
                "cuda"
                if torch.cuda.is_available()
                else "cpu"
            )

        self.device = torch.device(
            device
        )

        checkpoint = torch.load(
            checkpoint_path,
            map_location=self.device,
            weights_only=False,
        )

        self.class_names = list(
            checkpoint[
                "class_names"
            ]
        )

        self.mean = np.asarray(
            checkpoint[
                "feature_mean"
            ],
            dtype=np.float32,
        )

        self.std = np.asarray(
            checkpoint[
                "feature_std"
            ],
            dtype=np.float32,
        )

        self.model = (
            LearnedOcclusionEstimator(
                input_dim=int(
                    checkpoint[
                        "input_dim"
                    ]
                )
            )
            .to(self.device)
        )

        self.model.load_state_dict(
            checkpoint[
                "model_state_dict"
            ]
        )

        self.model.eval()

        self.extractor = (
            VisualOcclusionFeatureExtractor(
                normalize_to_training_resolution=True
            )
        )

    @torch.no_grad()
    def predict(
        self,
        frame: np.ndarray,
        bbox: Sequence[float],
    ) -> dict:
        extracted = self.extractor.extract(
            frame,
            bbox,
        )

        raw = extracted[
            "feature_vector"
        ]

        normalized = (
            raw
            - self.mean
        ) / self.std

        tensor = torch.from_numpy(
            normalized.astype(
                np.float32,
                copy=False,
            )
        ).unsqueeze(0).to(
            self.device
        )

        logits = self.model(
            tensor
        )

        probabilities = (
            torch.softmax(
                logits,
                dim=1,
            )[0]
            .detach()
            .cpu()
            .numpy()
            .astype(
                np.float32
            )
        )

        class_index = int(
            np.argmax(
                probabilities
            )
        )

        return {
            "occlusion": (
                self.class_names[
                    class_index
                ]
            ),
            "class_index": (
                class_index
            ),
            "probabilities": {
                name: float(
                    probabilities[
                        index
                    ]
                )
                for index, name
                in enumerate(
                    self.class_names
                )
            },
            "feature_vector": raw,
            "prepared_bbox": extracted[
                "prepared_bbox"
            ],
        }
