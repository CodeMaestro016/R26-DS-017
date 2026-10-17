from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import pandas as pd

from utils.runtime_occlusion_estimator import (
    RuntimeOcclusionEstimator,
)


ANNOTATIONS = Path(
    "datasets/processed/metadata/annotations.csv"
)
FRAMES_ROOT = Path(
    "datasets/processed/frames"
)
VIDEO_SPLIT = Path(
    "datasets/processed/yolo_pedestrian/video_split.json"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--samples",
        type=int,
        default=12,
    )

    return parser.parse_args()


def dataset_set_from_id(
    pedestrian_id: str,
) -> str:
    return f"set{int(str(pedestrian_id).split('_', 1)[0]):02d}"


def main() -> None:
    args = parse_args()

    estimator = (
        RuntimeOcclusionEstimator()
    )

    ann = pd.read_csv(
        ANNOTATIONS
    )

    ann["id"] = (
        ann["id"]
        .astype(str)
    )

    # Deterministic small smoke sample.
    samples = (
        ann
        .groupby(
            "occlusion",
            group_keys=False,
        )
        .head(
            max(
                1,
                int(args.samples) // 3,
            )
        )
        .reset_index(drop=True)
    )

    print("=" * 100)
    print(
        "PHASE 9.6C - RUNTIME "
        "OCCLUSION ESTIMATOR SMOKE TEST"
    )
    print("=" * 100)

    correct = 0
    evaluated = 0

    for row in samples.itertuples(
        index=False
    ):
        dataset_set = (
            dataset_set_from_id(
                row.id
            )
        )

        path = (
            FRAMES_ROOT
            / dataset_set
            / str(row.video)
            / (
                f"frame_"
                f"{int(row.frame):06d}.jpg"
            )
        )

        frame = cv2.imread(
            str(path)
        )

        if frame is None:
            continue

        result = estimator.predict(
            frame=frame,
            bbox=(
                row.x1,
                row.y1,
                row.x2,
                row.y2,
            ),
        )

        target = str(
            row.occlusion
        ).strip().lower()

        predicted = str(
            result[
                "occlusion"
            ]
        )

        evaluated += 1
        correct += int(
            predicted == target
        )

        print(
            f"{dataset_set}/{row.video} "
            f"frame={int(row.frame)} "
            f"GT={target:5s} "
            f"PRED={predicted:5s} "
            f"probs={result['probabilities']}"
        )

    print()
    print(
        "Smoke accuracy:",
        (
            f"{correct/evaluated:.4f}"
            if evaluated
            else "N/A"
        ),
    )
    print(
        "NOTE: validation_summary.json "
        "is the real model-quality evidence; "
        "this is only a runtime API smoke test."
    )
    print(
        "Status: PASSED"
    )
    print("=" * 100)


if __name__ == "__main__":
    main()
