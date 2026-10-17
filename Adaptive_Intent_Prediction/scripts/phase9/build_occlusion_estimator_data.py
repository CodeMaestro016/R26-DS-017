from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np
import pandas as pd

from utils.visual_occlusion_feature_extractor import (
    VisualOcclusionFeatureExtractor,
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
OUTPUT_DIR = Path(
    "datasets/processed/occlusion_estimator"
)

LABEL_MAP = {
    "none": 0,
    "part": 1,
    "full": 2,
}

SEED = 42


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--train-per-class",
        type=int,
        default=1200,
        help=(
            "Maximum sampled training observations "
            "per occlusion class."
        ),
    )
    parser.add_argument(
        "--val-per-class",
        type=int,
        default=300,
        help=(
            "Maximum sampled validation observations "
            "per occlusion class."
        ),
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
    )

    return parser.parse_args()


def normalize_occ(
    value,
) -> str:
    text = str(
        value
    ).strip().lower()

    if text in {
        "none",
        "no",
        "not-occluded",
        "not_occluded",
    }:
        return "none"

    if text in {
        "part",
        "partial",
        "partially-occluded",
        "partially_occluded",
    }:
        return "part"

    if text in {
        "full",
        "fully-occluded",
        "fully_occluded",
    }:
        return "full"

    raise ValueError(
        f"Unsupported occlusion label: {value}"
    )


def dataset_set_from_id(
    pedestrian_id: str,
) -> str:
    token = str(
        pedestrian_id
    ).split(
        "_",
        1,
    )[0]

    return f"set{int(token):02d}"


def sample_by_class(
    frame: pd.DataFrame,
    count_per_class: int,
) -> pd.DataFrame:
    parts = []

    for label_name in (
        "none",
        "part",
        "full",
    ):
        subset = frame[
            frame["occlusion_norm"]
            == label_name
        ]

        take = min(
            int(count_per_class),
            len(subset),
        )

        if take == 0:
            continue

        parts.append(
            subset.sample(
                n=take,
                random_state=(
                    SEED
                    + LABEL_MAP[
                        label_name
                    ]
                ),
            )
        )

    if not parts:
        raise RuntimeError(
            "No samples were selected."
        )

    sampled = pd.concat(
        parts,
        ignore_index=True,
    )

    return sampled.sample(
        frac=1.0,
        random_state=SEED,
    ).reset_index(
        drop=True
    )


def frame_path(
    dataset_set: str,
    video: str,
    frame_number: int,
) -> Path | None:
    base = (
        FRAMES_ROOT
        / dataset_set
        / video
    )

    for ext in (
        "jpg",
        "jpeg",
        "png",
    ):
        path = (
            base
            / (
                f"frame_"
                f"{frame_number:06d}."
                f"{ext}"
            )
        )

        if path.exists():
            return path

    return None


def export_split(
    name: str,
    rows: pd.DataFrame,
    extractor: VisualOcclusionFeatureExtractor,
) -> dict:
    features = []
    labels = []
    manifest_rows = []
    skipped = 0

    print()
    print(
        f"Extracting {name} visual "
        f"occlusion features..."
    )

    for index, row in enumerate(
        rows.itertuples(
            index=False
        ),
        start=1,
    ):
        dataset_set = str(
            row.dataset_set
        )
        video = str(
            row.video
        )
        frame_number = int(
            row.frame
        )

        path = frame_path(
            dataset_set,
            video,
            frame_number,
        )

        if path is None:
            skipped += 1
            continue

        frame = cv2.imread(
            str(path)
        )

        if frame is None:
            skipped += 1
            continue

        bbox = (
            float(row.x1),
            float(row.y1),
            float(row.x2),
            float(row.y2),
        )

        try:
            result = extractor.extract(
                frame,
                bbox,
            )
        except Exception as exc:
            skipped += 1

            print(
                "Skipped:",
                dataset_set,
                video,
                frame_number,
                row.id,
                type(exc).__name__,
                str(exc),
            )
            continue

        features.append(
            result[
                "feature_vector"
            ]
        )

        labels.append(
            LABEL_MAP[
                row.occlusion_norm
            ]
        )

        manifest_rows.append(
            {
                "dataset_set": dataset_set,
                "video": video,
                "frame": frame_number,
                "pedestrian_id": str(
                    row.id
                ),
                "occlusion": str(
                    row.occlusion_norm
                ),
            }
        )

        if (
            index % 250 == 0
            or index == len(rows)
        ):
            print(
                f"  {index}/{len(rows)}"
            )

    if not features:
        raise RuntimeError(
            f"{name} feature set is empty."
        )

    X = np.stack(
        features
    ).astype(
        np.float32
    )

    y = np.asarray(
        labels,
        dtype=np.int64,
    )

    npz_path = (
        OUTPUT_DIR
        / f"{name}_occlusion_features.npz"
    )

    np.savez_compressed(
        npz_path,
        X=X,
        y=y,
    )

    manifest = pd.DataFrame(
        manifest_rows
    )

    manifest_path = (
        OUTPUT_DIR
        / f"{name}_manifest.csv"
    )

    manifest.to_csv(
        manifest_path,
        index=False,
    )

    counts = (
        manifest[
            "occlusion"
        ]
        .value_counts()
        .to_dict()
    )

    return {
        "npz": str(npz_path),
        "manifest": str(
            manifest_path
        ),
        "shape": list(
            X.shape
        ),
        "counts": {
            key: int(value)
            for key, value
            in counts.items()
        },
        "skipped": int(skipped),
    }


def main() -> None:
    args = parse_args()

    print("=" * 106)
    print(
        "PHASE 9.6A - BUILD LEARNED "
        "OCCLUSION-ESTIMATOR DATA"
    )
    print("=" * 106)

    for path in (
        ANNOTATIONS,
        FRAMES_ROOT,
        VIDEO_SPLIT,
    ):
        if not path.exists():
            raise FileNotFoundError(
                f"Missing required path: {path}"
            )

    if OUTPUT_DIR.exists():
        if not args.overwrite:
            existing = list(
                OUTPUT_DIR.glob("*")
            )

            if existing:
                raise FileExistsError(
                    f"{OUTPUT_DIR} already contains "
                    "files. Use --overwrite to rebuild."
                )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    split_data = json.loads(
        VIDEO_SPLIT.read_text(
            encoding="utf-8"
        )
    )

    train_videos = set(
        split_data[
            "train_videos"
        ]
    )
    val_videos = set(
        split_data[
            "val_videos"
        ]
    )

    if train_videos & val_videos:
        raise RuntimeError(
            "Video overlap detected between "
            "occlusion train and validation."
        )

    ann = pd.read_csv(
        ANNOTATIONS
    )

    required = {
        "video",
        "frame",
        "id",
        "x1",
        "y1",
        "x2",
        "y2",
        "occlusion",
    }

    missing = required - set(
        ann.columns
    )

    if missing:
        raise KeyError(
            "Missing annotation columns: "
            f"{sorted(missing)}"
        )

    ann = ann.copy()

    ann["id"] = (
        ann["id"]
        .astype(str)
    )

    ann["video"] = (
        ann["video"]
        .astype(str)
    )

    ann["frame"] = pd.to_numeric(
        ann["frame"],
        errors="raise",
    ).astype(int)

    ann["dataset_set"] = (
        ann["id"]
        .map(
            dataset_set_from_id
        )
    )

    ann["video_key"] = (
        ann["dataset_set"]
        + "/"
        + ann["video"]
    )

    ann["occlusion_norm"] = (
        ann["occlusion"]
        .map(
            normalize_occ
        )
    )

    train_ann = ann[
        ann["video_key"].isin(
            train_videos
        )
    ].copy()

    val_ann = ann[
        ann["video_key"].isin(
            val_videos
        )
    ].copy()

    train_rows = sample_by_class(
        train_ann,
        int(
            args.train_per_class
        ),
    )

    val_rows = sample_by_class(
        val_ann,
        int(
            args.val_per_class
        ),
    )

    print(
        "Train videos:",
        sorted(train_videos),
    )
    print(
        "Val videos  :",
        sorted(val_videos),
    )
    print(
        "Video overlap:",
        sorted(
            train_videos
            & val_videos
        ),
    )

    print()
    print(
        "Sampled train labels:"
    )
    print(
        train_rows[
            "occlusion_norm"
        ]
        .value_counts()
        .to_string()
    )

    print()
    print(
        "Sampled val labels:"
    )
    print(
        val_rows[
            "occlusion_norm"
        ]
        .value_counts()
        .to_string()
    )

    extractor = (
        VisualOcclusionFeatureExtractor(
            normalize_to_training_resolution=True
        )
    )

    train_summary = export_split(
        "train",
        train_rows,
        extractor,
    )

    val_summary = export_split(
        "val",
        val_rows,
        extractor,
    )

    summary = {
        "feature_dimension": 518,
        "feature_definition": (
            "512-D appearance + 6-D spatial; "
            "no occlusion label is used as input"
        ),
        "label_map": LABEL_MAP,
        "split_unit": (
            "video-disjoint detector "
            "train/validation split"
        ),
        "train_videos": sorted(
            train_videos
        ),
        "val_videos": sorted(
            val_videos
        ),
        "video_overlap": sorted(
            train_videos
            & val_videos
        ),
        "train": train_summary,
        "val": val_summary,
    }

    summary_path = (
        OUTPUT_DIR
        / "dataset_summary.json"
    )

    summary_path.write_text(
        json.dumps(
            summary,
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print("-" * 106)
    print("DATASET SUMMARY")
    print("-" * 106)
    print(
        "Train shape:",
        train_summary["shape"],
    )
    print(
        "Val shape  :",
        val_summary["shape"],
    )
    print(
        "Summary    :",
        summary_path,
    )
    print(
        "Status     : PASSED"
    )
    print("=" * 106)


if __name__ == "__main__":
    main()
