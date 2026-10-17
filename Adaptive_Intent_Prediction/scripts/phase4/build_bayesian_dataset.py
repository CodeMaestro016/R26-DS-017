"""
Build the frame-level Bayesian Network training dataset.

DAG:

Motion ------------------------\
Horizontal Position ------------> Intention Tendency
Vertical Position --------------/

Occlusion ----------------------> Observation Reliability

Input:
    datasets/processed/features/train_features.npz
    datasets/processed/metadata/train.csv
    datasets/processed/metadata/annotations.csv
    outputs/phase4/motion_kmeans.pkl

Output:
    datasets/processed/bayesian/train_bayesian.csv
"""

from pathlib import Path

import numpy as np
import pandas as pd

from utils.semantic_mapper import SemanticMapper


# ---------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------

TRAIN_FEATURE_PATH = Path(
    "datasets/processed/features/train_features.npz"
)

TRAIN_METADATA_PATH = Path(
    "datasets/processed/metadata/train.csv"
)

ANNOTATION_PATH = Path(
    "datasets/processed/metadata/annotations.csv"
)

OUTPUT_PATH = Path(
    "datasets/processed/bayesian/train_bayesian.csv"
)

MOTION_MODEL_PATH = Path(
    "outputs/phase4/motion_kmeans.pkl"
)


# ---------------------------------------------------------------------
# Feature indices
# ---------------------------------------------------------------------

CENTER_X_INDEX = 512
CENTER_Y_INDEX = 513
SPEED_INDEX = 520

IMAGE_WIDTH = 1920
IMAGE_HEIGHT = 1080


# ---------------------------------------------------------------------
# State mappings
# ---------------------------------------------------------------------

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
    """
    Convert:
        '1013|1014|1015'

    into:
        [1013, 1014, 1015]
    """

    return [
        int(frame)
        for frame in str(frame_string).split("|")
    ]


def load_annotations():
    """
    Load annotations and build a lookup dictionary.

    Key:
        (video, pedestrian_id, frame)

    Value:
        original PIE occlusion state
    """

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


def validate_input_files():

    required_paths = [
        TRAIN_FEATURE_PATH,
        TRAIN_METADATA_PATH,
        ANNOTATION_PATH,
        MOTION_MODEL_PATH
    ]

    for path in required_paths:

        if not path.exists():

            raise FileNotFoundError(
                f"Required file not found: {path}"
            )


def main():

    print("=" * 70)
    print("BUILD BAYESIAN TRAINING DATASET")
    print("=" * 70)

    validate_input_files()

    # --------------------------------------------------------------
    # Load feature arrays
    # --------------------------------------------------------------

    feature_data = np.load(
        TRAIN_FEATURE_PATH,
        allow_pickle=True
    )

    X = feature_data["X"]
    y = feature_data["y"]

    print(f"Feature shape : {X.shape}")
    print(f"Label shape   : {y.shape}")

    if X.ndim != 3:

        raise ValueError(
            f"Expected X to have 3 dimensions, got {X.shape}"
        )

    if X.shape[2] != 522:

        raise ValueError(
            f"Expected 522 features, got {X.shape[2]}"
        )

    # --------------------------------------------------------------
    # Load sequence metadata
    # --------------------------------------------------------------

    sequences = pd.read_csv(
        TRAIN_METADATA_PATH,
        dtype={
            "video": str,
            "pedestrian_id": str
        }
    )

    print(f"Metadata rows : {len(sequences)}")

    if len(sequences) != len(X):

        raise ValueError(
            "Feature/metadata alignment mismatch: "
            f"{len(X)} feature sequences but "
            f"{len(sequences)} metadata rows."
        )

    if len(y) != len(sequences):

        raise ValueError(
            "Label/metadata alignment mismatch: "
            f"{len(y)} labels but "
            f"{len(sequences)} metadata rows."
        )

    # --------------------------------------------------------------
    # Load semantic models and annotation lookup
    # --------------------------------------------------------------

    semantic_mapper = SemanticMapper(
        motion_model_path=str(MOTION_MODEL_PATH)
    )

    annotation_lookup = load_annotations()

    print(
        f"Annotation lookup entries: "
        f"{len(annotation_lookup)}"
    )

    # --------------------------------------------------------------
    # Generate Bayesian rows
    # --------------------------------------------------------------

    bayesian_rows = []
    missing_annotations = []

    total_sequences = len(sequences)

    for sequence_index, row in sequences.iterrows():

        video = str(row["video"])
        pedestrian_id = str(row["pedestrian_id"])
        sequence_id = int(row["sequence_id"])

        frame_numbers = parse_frames(
            row["frames"]
        )

        if len(frame_numbers) != X.shape[1]:

            raise ValueError(
                f"Sequence {sequence_id} has "
                f"{len(frame_numbers)} frame IDs, but "
                f"feature array has {X.shape[1]} time steps."
            )

        numeric_label = int(y[sequence_index])

        if numeric_label not in LABEL_ID_TO_NAME:

            raise ValueError(
                f"Unknown numeric label: {numeric_label}"
            )

        intention_tendency = (
            LABEL_ID_TO_NAME[numeric_label]
        )

        csv_label = (
            str(row["label"])
            .strip()
            .lower()
        )

        if csv_label != intention_tendency:

            raise ValueError(
                f"Label mismatch at sequence {sequence_id}: "
                f"NPZ={intention_tendency}, "
                f"CSV={csv_label}"
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
                    "Unsupported PIE occlusion state "
                    f"'{original_occlusion}' for "
                    f"{annotation_key}"
                )

            occlusion_level = (
                PIE_OCCLUSION_TO_LEVEL[
                    original_occlusion
                ]
            )

            observation_reliability = (
                PIE_OCCLUSION_TO_RELIABILITY[
                    original_occlusion
                ]
            )

            bayesian_rows.append({
                "sequence_index": sequence_index,
                "sequence_id": sequence_id,
                "time_step": time_step,
                "video": video,
                "pedestrian_id": pedestrian_id,
                "frame": int(frame_number),

                "motion": motion,
                "horizontal": position["horizontal"],
                "vertical": position["vertical"],
                "occlusion": occlusion_level,

                "intention_tendency": intention_tendency,
                "observation_reliability":
                    observation_reliability
            })

        if (
            sequence_index + 1
        ) % 500 == 0:

            print(
                f"Processed "
                f"{sequence_index + 1}/"
                f"{total_sequences} sequences"
            )

    # --------------------------------------------------------------
    # Validate missing annotations
    # --------------------------------------------------------------

    if missing_annotations:

        print()
        print(
            f"Missing annotations: "
            f"{len(missing_annotations)}"
        )

        print("First missing keys:")

        for key in missing_annotations[:10]:
            print(key)

        raise ValueError(
            "Bayesian dataset creation stopped because "
            "some feature frames could not be matched "
            "with annotations."
        )

    # --------------------------------------------------------------
    # Save dataset
    # --------------------------------------------------------------

    bayesian_data = pd.DataFrame(
        bayesian_rows
    )

    expected_rows = (
        X.shape[0] * X.shape[1]
    )

    if len(bayesian_data) != expected_rows:

        raise ValueError(
            f"Expected {expected_rows} Bayesian rows, "
            f"but generated {len(bayesian_data)}."
        )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    bayesian_data.to_csv(
        OUTPUT_PATH,
        index=False
    )

    # --------------------------------------------------------------
    # Summary
    # --------------------------------------------------------------

    print()
    print("=" * 70)
    print("BAYESIAN DATASET COMPLETE")
    print("=" * 70)

    print(f"Output path : {OUTPUT_PATH}")
    print(f"Output shape: {bayesian_data.shape}")

    print()
    print("Motion distribution:")
    print(
        bayesian_data["motion"]
        .value_counts()
        .to_string()
    )

    print()
    print("Horizontal distribution:")
    print(
        bayesian_data["horizontal"]
        .value_counts()
        .to_string()
    )

    print()
    print("Vertical distribution:")
    print(
        bayesian_data["vertical"]
        .value_counts()
        .to_string()
    )

    print()
    print("Occlusion distribution:")
    print(
        bayesian_data["occlusion"]
        .value_counts()
        .to_string()
    )

    print()
    print("Intention tendency distribution:")
    print(
        bayesian_data["intention_tendency"]
        .value_counts()
        .to_string()
    )

    print()
    print("Observation reliability distribution:")
    print(
        bayesian_data[
            "observation_reliability"
        ]
        .value_counts()
        .to_string()
    )

    print()
    print("Sample rows:")
    print(
        bayesian_data.head().to_string(
            index=False
        )
    )


if __name__ == "__main__":
    main()