import os
import numpy as np
import pandas as pd

from tqdm import tqdm

from utils.sequence_feature_extractor import (
    SequenceFeatureExtractor
)


# ----------------------------------------------------
# Configuration
# ----------------------------------------------------

FRAME_ROOT = "datasets/processed/frames"

ANNOTATION_CSV = "datasets/processed/metadata/annotations.csv"

DATASET_SET = "set01"

CSV_FOLDER = "datasets/processed/metadata"

OUTPUT_FOLDER = "datasets/processed/features"

os.makedirs(
    OUTPUT_FOLDER,
    exist_ok=True
)


# ----------------------------------------------------
# Process One Split
# ----------------------------------------------------

def process_split(csv_file, output_name):

    print(f"\nLoading {csv_file}")

    df = pd.read_csv(csv_file)

    extractor = SequenceFeatureExtractor(
        frame_root=FRAME_ROOT,
        annotation_csv=ANNOTATION_CSV,
        dataset_set=DATASET_SET
    )

    X = []

    y = []

    skipped = 0

    for _, row in tqdm(
        df.iterrows(),
        total=len(df)
    ):

        features = extractor.extract(row)

        if features is None:

            skipped += 1
            continue

        if features.shape != (30, 522):

            skipped += 1
            continue

        X.append(features)

        label = (
            1
            if row["label"] == "crossing"
            else 0
        )

        y.append(label)

    X = np.asarray(
        X,
        dtype=np.float32
    )

    y = np.asarray(
        y,
        dtype=np.int64
    )

    output_path = os.path.join(
        OUTPUT_FOLDER,
        output_name
    )

    np.savez_compressed(
        output_path,
        X=X,
        y=y
    )

    print("\n------------------------------------")

    print(f"Saved : {output_name}")

    print(f"Samples : {len(X)}")

    print(f"Skipped : {skipped}")

    print(f"Feature Shape : {X.shape}")

    print("------------------------------------")


# ----------------------------------------------------
# Main
# ----------------------------------------------------

def main():

    process_split(
        os.path.join(CSV_FOLDER, "train.csv"),
        "train_features.npz"
    )

    process_split(
        os.path.join(CSV_FOLDER, "val.csv"),
        "val_features.npz"
    )

    process_split(
        os.path.join(CSV_FOLDER, "test.csv"),
        "test_features.npz"
    )

    print("\nFeature extraction completed.")


if __name__ == "__main__":
    main()