"""
Build Bayesian feature-ablation datasets.

Outputs per split
-----------------
1. Intention-only enriched features:
       522 original + 2 intention probabilities = 524

2. Reliability-only enriched features:
       522 original + 3 reliability probabilities = 525

Existing full enriched features:
       522 original + 5 Bayesian probabilities = 527
"""

from pathlib import Path

import numpy as np


FEATURE_DIR = Path(
    "datasets/processed/features"
)

SPLITS = [
    "train",
    "val",
    "test"
]

RAW_DIMENSION = 522
BAYESIAN_DIMENSION = 5

INTENTION_DIMENSION = 2
RELIABILITY_DIMENSION = 3


def load_npz(path):

    if not path.exists():
        raise FileNotFoundError(
            f"File not found: {path}"
        )

    with np.load(
        path,
        allow_pickle=True
    ) as data:

        if "X" not in data.files:
            raise KeyError(
                f"'X' key not found in {path}"
            )

        if "y" not in data.files:
            raise KeyError(
                f"'y' key not found in {path}"
            )

        X = data["X"].astype(
            np.float32,
            copy=False
        )

        y = data["y"].astype(
            np.int64,
            copy=False
        )

    return X, y


def build_split(split_name):

    print()
    print("=" * 70)
    print(
        f"BUILD {split_name.upper()} "
        "ABLATION FEATURES"
    )
    print("=" * 70)

    raw_path = (
        FEATURE_DIR
        / f"{split_name}_features.npz"
    )

    bayesian_path = (
        FEATURE_DIR
        / f"{split_name}_bayesian_features.npz"
    )

    full_enriched_path = (
        FEATURE_DIR
        / f"{split_name}_enriched_features.npz"
    )

    raw_X, raw_y = load_npz(
        raw_path
    )

    bayesian_X, bayesian_y = load_npz(
        bayesian_path
    )

    if raw_X.ndim != 3:
        raise ValueError(
            f"Expected raw 3D array, got "
            f"{raw_X.shape}"
        )

    if bayesian_X.ndim != 3:
        raise ValueError(
            f"Expected Bayesian 3D array, got "
            f"{bayesian_X.shape}"
        )

    if raw_X.shape[2] != RAW_DIMENSION:
        raise ValueError(
            f"Expected {RAW_DIMENSION} raw "
            f"features, got {raw_X.shape[2]}"
        )

    if (
        bayesian_X.shape[2]
        != BAYESIAN_DIMENSION
    ):
        raise ValueError(
            f"Expected {BAYESIAN_DIMENSION} "
            f"Bayesian features, got "
            f"{bayesian_X.shape[2]}"
        )

    if (
        raw_X.shape[:2]
        != bayesian_X.shape[:2]
    ):
        raise ValueError(
            "Raw and Bayesian arrays are "
            "not temporally aligned."
        )

    if not np.array_equal(
        raw_y,
        bayesian_y
    ):
        raise ValueError(
            "Raw and Bayesian labels "
            "are not aligned."
        )

    intention_probabilities = (
        bayesian_X[
            :,
            :,
            :INTENTION_DIMENSION
        ]
    )

    reliability_probabilities = (
        bayesian_X[
            :,
            :,
            INTENTION_DIMENSION:
        ]
    )

    if (
        reliability_probabilities.shape[2]
        != RELIABILITY_DIMENSION
    ):
        raise ValueError(
            "Incorrect reliability feature "
            "dimension."
        )

    intention_enriched_X = np.concatenate(
        [
            raw_X,
            intention_probabilities
        ],
        axis=2
    ).astype(
        np.float32,
        copy=False
    )

    reliability_enriched_X = np.concatenate(
        [
            raw_X,
            reliability_probabilities
        ],
        axis=2
    ).astype(
        np.float32,
        copy=False
    )

    intention_output_path = (
        FEATURE_DIR
        / (
            f"{split_name}_"
            "intention_enriched_features.npz"
        )
    )

    reliability_output_path = (
        FEATURE_DIR
        / (
            f"{split_name}_"
            "reliability_enriched_features.npz"
        )
    )

    np.savez_compressed(
        intention_output_path,
        X=intention_enriched_X,
        y=raw_y
    )

    np.savez_compressed(
        reliability_output_path,
        X=reliability_enriched_X,
        y=raw_y
    )

    # Confirm the existing 527-dimensional file
    # matches raw + all Bayesian features.
    if full_enriched_path.exists():

        full_X, full_y = load_npz(
            full_enriched_path
        )

        expected_full_X = np.concatenate(
            [
                raw_X,
                bayesian_X
            ],
            axis=2
        )

        if not np.array_equal(
            raw_y,
            full_y
        ):
            raise ValueError(
                "Full enriched labels "
                "are not aligned."
            )

        if not np.allclose(
            expected_full_X,
            full_X,
            atol=1e-6
        ):
            raise ValueError(
                "Existing full enriched file "
                "does not match raw + Bayesian "
                "features."
            )

        print(
            "Full enriched consistency: PASSED"
        )

    print(
        "Raw shape             :",
        raw_X.shape
    )

    print(
        "Bayesian shape        :",
        bayesian_X.shape
    )

    print(
        "Intention-only shape  :",
        intention_enriched_X.shape
    )

    print(
        "Reliability-only shape:",
        reliability_enriched_X.shape
    )

    print(
        "Saved:",
        intention_output_path
    )

    print(
        "Saved:",
        reliability_output_path
    )


def main():

    print("=" * 70)
    print("BUILD BAYESIAN ABLATION FEATURES")
    print("=" * 70)

    for split_name in SPLITS:

        build_split(
            split_name
        )

    print()
    print("=" * 70)
    print("ABLATION FEATURE GENERATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()