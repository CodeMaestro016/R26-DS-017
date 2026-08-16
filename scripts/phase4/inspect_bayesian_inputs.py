"""
Inspect the files required for Bayesian dataset generation.

Checks:
1. Keys and shapes inside train_features.npz
2. Columns inside metadata CSV files
3. Availability of intent labels
4. Availability of occlusion ratio / visibility metadata
"""

from pathlib import Path

import numpy as np
import pandas as pd


PROCESSED_ROOT = Path("datasets/processed")

FEATURE_PATH = (
    PROCESSED_ROOT
    / "features"
    / "train_features.npz"
)

METADATA_DIR = (
    PROCESSED_ROOT
    / "metadata"
)


SEARCH_TERMS = [
    "label",
    "intent",
    "cross",
    "occlusion",
    "ratio",
    "visibility",
    "visible"
]


def print_separator(title):
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


def inspect_npz(npz_path):

    print_separator("TRAIN FEATURE FILE")

    print(f"Path   : {npz_path}")
    print(f"Exists : {npz_path.exists()}")

    if not npz_path.exists():
        raise FileNotFoundError(
            f"Feature file not found: {npz_path}"
        )

    with np.load(npz_path, allow_pickle=True) as data:

        print(f"Keys   : {data.files}")

        for key in data.files:

            array = data[key]

            print()
            print(f"Key    : {key}")
            print(f"Shape  : {array.shape}")
            print(f"Dtype  : {array.dtype}")

            if array.size > 0:

                sample = array.reshape(-1)[:5]

                print(f"Sample : {sample}")


def inspect_csv(csv_path):

    print_separator(f"CSV FILE: {csv_path.name}")

    print(f"Path   : {csv_path}")
    print(f"Exists : {csv_path.exists()}")

    if not csv_path.exists():
        return

    preview = pd.read_csv(
        csv_path,
        nrows=5
    )

    print(f"Columns: {preview.columns.tolist()}")

    print()
    print("First rows:")
    print(preview.to_string(index=False))

    relevant_columns = [
        column
        for column in preview.columns
        if any(
            term in column.lower()
            for term in SEARCH_TERMS
        )
    ]

    print()
    print(
        "Relevant columns:",
        relevant_columns
    )

    if not relevant_columns:
        return

    relevant_data = pd.read_csv(
        csv_path,
        usecols=relevant_columns
    )

    for column in relevant_columns:

        print()
        print(f"[{column}]")

        series = relevant_data[column]

        if pd.api.types.is_numeric_dtype(series):

            print(series.describe().to_string())

        else:

            print(
                series.value_counts(
                    dropna=False
                ).head(15).to_string()
            )


def find_occlusion_files(root):

    print_separator(
        "POSSIBLE OCCLUSION / VISIBILITY FILES"
    )

    matched_files = []

    for path in root.rglob("*"):

        if not path.is_file():
            continue

        filename = path.name.lower()

        if any(
            term in filename
            for term in [
                "occlusion",
                "visibility",
                "visible",
                "ratio"
            ]
        ):
            matched_files.append(path)

    if not matched_files:

        print(
            "No filename containing occlusion or "
            "visibility terms was found."
        )

        return

    for path in matched_files:

        print(path)


def main():

    print_separator(
        "BAYESIAN INPUT INSPECTION"
    )

    inspect_npz(FEATURE_PATH)

    if not METADATA_DIR.exists():

        raise FileNotFoundError(
            f"Metadata directory not found: "
            f"{METADATA_DIR}"
        )

    csv_files = sorted(
        METADATA_DIR.glob("*.csv")
    )

    print_separator("METADATA CSV LIST")

    for csv_path in csv_files:
        print(csv_path)

    for csv_path in csv_files:
        inspect_csv(csv_path)

    find_occlusion_files(
        PROCESSED_ROOT
    )

    print_separator(
        "INSPECTION COMPLETE"
    )


if __name__ == "__main__":
    main()