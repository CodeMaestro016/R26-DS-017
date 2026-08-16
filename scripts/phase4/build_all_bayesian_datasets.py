"""
Build frame-level Bayesian datasets for train, validation and test splits.

Outputs:
    datasets/processed/bayesian/train_bayesian.csv
    datasets/processed/bayesian/val_bayesian.csv
    datasets/processed/bayesian/test_bayesian.csv
"""

from pathlib import Path

import numpy as np
import pandas as pd

from utils.semantic_mapper import SemanticMapper


FEATURE_DIR = Path("datasets/processed/features")
METADATA_DIR = Path("datasets/processed/metadata")
OUTPUT_DIR = Path("datasets/processed/bayesian")

ANNOTATION_PATH = METADATA_DIR / "annotations.csv"
MOTION_MODEL_PATH = Path(
    "outputs/phase4/motion_kmeans.pkl"
)

SPLITS = [
    "train",
    "val",
    "test"
]

CENTER_X_INDEX = 512
CENTER_Y_INDEX = 513
SPEED_INDEX = 520

IMAGE_WIDTH = 1920
IMAGE_HEIGHT = 1080

LABEL_ID_TO_NAME = {
    0: "not-crossing",
    1: "crossing"
}

PIE_OCCLUSION_TO_LEVEL = {
    "none": "low",
    "part": "medium",
    "full": "high"
}

PIE_OCCLUSION_TO_RELIABILITY = {
    "none": "high",
    "part": "medium",
    "full": "low"
}


def parse_frames(frame_string):

    return [
        int(frame)
        for frame in str(frame_string).split("|")
    ]


def load_annotation_lookup():

    annotations = pd.read_csv(
        ANNOTATION_PATH,
        dtype={
            "video": str,
            "id": str
        }
    )

    annotations["frame"] = (
        annotations["frame"].astype(int)
    )

    annotations["occlusion"] = (
        annotations["occlusion"]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    lookup = {}

    for row in annotations.itertuples(index=False):

        key = (
            str(row.video),
            str(row.id),
            int(row.frame)
        )

        lookup[key] = row.occlusion

    return lookup


def build_split(
    split_name,
    semantic_mapper,
    annotation_lookup
):

    feature_path = (
        FEATURE_DIR
        / f"{split_name}_features.npz"
    )

    metadata_path = (
        METADATA_DIR
        / f"{split_name}.csv"
    )

    output_path = (
        OUTPUT_DIR
        / f"{split_name}_bayesian.csv"
    )

    if not feature_path.exists():
        raise FileNotFoundError(
            f"Feature file not found: {feature_path}"
        )

    if not metadata_path.exists():
        raise FileNotFoundError(
            f"Metadata file not found: {metadata_path}"
        )

    feature_data = np.load(
        feature_path,
        allow_pickle=True
    )

    X = feature_data["X"]
    y = feature_data["y"]

    metadata = pd.read_csv(
        metadata_path,
        dtype={
            "video": str,
            "pedestrian_id": str
        }
    ).reset_index(drop=True)

    print()
    print("=" * 70)
    print(f"BUILDING {split_name.upper()} BAYESIAN DATASET")
    print("=" * 70)

    print(f"Feature shape : {X.shape}")
    print(f"Label shape   : {y.shape}")
    print(f"Metadata rows : {len(metadata)}")

    if X.ndim != 3:
        raise ValueError(
            f"{split_name}: expected 3D X, "
            f"received {X.shape}"
        )

    if X.shape[2] != 522:
        raise ValueError(
            f"{split_name}: expected 522 features, "
            f"received {X.shape[2]}"
        )

    if len(X) != len(metadata):
        raise ValueError(
            f"{split_name}: feature and metadata "
            "lengths do not match."
        )

    if len(y) != len(metadata):
        raise ValueError(
            f"{split_name}: label and metadata "
            "lengths do not match."
        )

    rows = []
    missing_annotations = []

    for sequence_index, metadata_row in (
        metadata.iterrows()
    ):

        video = str(metadata_row["video"])

        pedestrian_id = str(
            metadata_row["pedestrian_id"]
        )

        sequence_id = int(
            metadata_row["sequence_id"]
        )

        frame_numbers = parse_frames(
            metadata_row["frames"]
        )

        if len(frame_numbers) != X.shape[1]:

            raise ValueError(
                f"{split_name}, sequence "
                f"{sequence_id}: expected "
                f"{X.shape[1]} frames but found "
                f"{len(frame_numbers)}."
            )

        label_id = int(y[sequence_index])

        if label_id not in LABEL_ID_TO_NAME:

            raise ValueError(
                f"Unsupported label ID: {label_id}"
            )

        intention_tendency = (
            LABEL_ID_TO_NAME[label_id]
        )

        csv_label = (
            str(metadata_row["label"])
            .strip()
            .lower()
        )

        if csv_label != intention_tendency:

            raise ValueError(
                f"{split_name}, sequence "
                f"{sequence_id}: NPZ label "
                f"'{intention_tendency}' does not "
                f"match CSV label '{csv_label}'."
            )

        for time_step, frame_number in enumerate(
            frame_numbers
        ):

            frame_features = X[
                sequence_index,
                time_step
            ]

            center_x = float(
                frame_features[CENTER_X_INDEX]
            )

            center_y = float(
                frame_features[CENTER_Y_INDEX]
            )

            speed = float(
                frame_features[SPEED_INDEX]
            )

            motion = semantic_mapper.map_motion(
                speed
            )

            position = semantic_mapper.map_position(
                center_x=center_x,
                center_y=center_y,
                image_width=IMAGE_WIDTH,
                image_height=IMAGE_HEIGHT
            )

            annotation_key = (
                video,
                pedestrian_id,
                int(frame_number)
            )

            original_occlusion = (
                annotation_lookup.get(
                    annotation_key
                )
            )

            if original_occlusion is None:

                missing_annotations.append(
                    annotation_key
                )

                continue

            if (
                original_occlusion
                not in PIE_OCCLUSION_TO_LEVEL
            ):

                raise ValueError(
                    "Unsupported occlusion state "
                    f"'{original_occlusion}' for "
                    f"{annotation_key}."
                )

            rows.append({
                "sequence_index": sequence_index,
                "sequence_id": sequence_id,
                "time_step": time_step,
                "video": video,
                "pedestrian_id": pedestrian_id,
                "frame": int(frame_number),

                "motion": motion,

                "horizontal":
                    position["horizontal"],

                "vertical":
                    position["vertical"],

                "occlusion":
                    PIE_OCCLUSION_TO_LEVEL[
                        original_occlusion
                    ],

                "intention_tendency":
                    intention_tendency,

                "observation_reliability":
                    PIE_OCCLUSION_TO_RELIABILITY[
                        original_occlusion
                    ]
            })

        if (
            sequence_index + 1
        ) % 500 == 0:

            print(
                f"Processed "
                f"{sequence_index + 1}/"
                f"{len(metadata)} sequences"
            )

    if missing_annotations:

        print(
            f"Missing annotations: "
            f"{len(missing_annotations)}"
        )

        for key in missing_annotations[:10]:
            print(key)

        raise ValueError(
            f"{split_name}: unmatched annotations "
            "were detected."
        )

    bayesian_data = pd.DataFrame(rows)

    expected_rows = (
        X.shape[0] * X.shape[1]
    )

    if len(bayesian_data) != expected_rows:

        raise ValueError(
            f"{split_name}: expected "
            f"{expected_rows} rows but generated "
            f"{len(bayesian_data)}."
        )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    bayesian_data.to_csv(
        output_path,
        index=False
    )

    print()
    print(f"Saved : {output_path}")
    print(f"Shape : {bayesian_data.shape}")


def main():

    print("=" * 70)
    print("BUILD ALL BAYESIAN DATASETS")
    print("=" * 70)

    semantic_mapper = SemanticMapper(
        motion_model_path=str(
            MOTION_MODEL_PATH
        )
    )

    annotation_lookup = (
        load_annotation_lookup()
    )

    print(
        "Annotation lookup entries:",
        len(annotation_lookup)
    )

    for split_name in SPLITS:

        build_split(
            split_name=split_name,
            semantic_mapper=semantic_mapper,
            annotation_lookup=annotation_lookup
        )

    print()
    print("=" * 70)
    print("ALL BAYESIAN DATASETS COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()