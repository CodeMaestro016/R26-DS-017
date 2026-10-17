"""
Test MC Dropout uncertainty estimation using
actual validation feature sequences.

The test uses:
1. One not-crossing sequence
2. One crossing sequence

No uncertainty category thresholds are used yet.
"""

from pathlib import Path

import numpy as np

from utils.uncertainty_estimator import (
    MCDropoutUncertaintyEstimator
)


VALIDATION_PATH = Path(
    "datasets/processed/features/"
    "val_reliability_enriched_features.npz"
)

CHECKPOINT_PATH = Path(
    "outputs/phase5/"
    "reliability_only_transformer_best.pt"
)

NUMBER_OF_MC_SAMPLES = 30


def load_validation_data():

    if not VALIDATION_PATH.exists():

        raise FileNotFoundError(
            f"Validation file not found: "
            f"{VALIDATION_PATH}"
        )

    with np.load(
        VALIDATION_PATH,
        allow_pickle=True
    ) as data:

        X = data["X"].astype(
            np.float32,
            copy=False
        )

        y = data["y"].astype(
            np.int64,
            copy=False
        )

    if X.shape != (
        845,
        30,
        525
    ):

        raise ValueError(
            "Unexpected validation feature shape: "
            f"{X.shape}"
        )

    return X, y


def validate_result(result):

    mean_probabilities = result[
        "mean_probabilities"
    ]

    if mean_probabilities.shape != (2,):

        raise ValueError(
            "Mean probability shape must be (2,)."
        )

    if not np.isclose(
        mean_probabilities.sum(),
        1.0,
        atol=1e-5
    ):

        raise ValueError(
            "Mean probabilities do not sum to 1."
        )

    if not (
        0.0
        <= result["confidence"]
        <= 1.0
    ):

        raise ValueError(
            "Confidence must be between 0 and 1."
        )

    if not (
        0.0
        <= result[
            "normalized_predictive_entropy"
        ]
        <= 1.0 + 1e-5
    ):

        raise ValueError(
            "Normalized entropy must be "
            "between 0 and 1."
        )

    if (
        result[
            "crossing_probability_variance"
        ]
        < 0
    ):

        raise ValueError(
            "Variance cannot be negative."
        )

    if result["mutual_information"] < 0:

        raise ValueError(
            "Mutual information cannot be negative."
        )

    sample_probabilities = result[
        "probability_samples"
    ]

    if sample_probabilities.shape != (
        NUMBER_OF_MC_SAMPLES,
        2
    ):

        raise ValueError(
            "Incorrect MC probability sample shape: "
            f"{sample_probabilities.shape}"
        )


def print_result(
    title,
    sequence_index,
    true_label,
    result
):

    print()
    print("=" * 78)
    print(title)
    print("=" * 78)

    print(
        f"Sequence index                 : "
        f"{sequence_index}"
    )

    print(
        f"Ground-truth class             : "
        f"{true_label}"
    )

    print(
        f"Predicted class                : "
        f"{result['predicted_class_name']}"
    )

    print(
        f"MC samples                     : "
        f"{result['number_of_samples']}"
    )

    print(
        f"Activated stochastic modules   : "
        f"{result['activated_stochastic_modules']}"
    )

    print()
    print(
        "Deterministic probabilities    :",
        result[
            "deterministic_probabilities"
        ]
    )

    print(
        "MC mean probabilities          :",
        result[
            "mean_probabilities"
        ]
    )

    print(
        f"Crossing probability mean      : "
        f"{result['crossing_probability_mean']:.6f}"
    )

    print(
        f"Crossing probability std       : "
        f"{result['crossing_probability_std']:.6f}"
    )

    print(
        f"Crossing probability variance  : "
        f"{result['crossing_probability_variance']:.6f}"
    )

    print(
        f"Crossing probability range     : "
        f"{result['crossing_probability_min']:.6f}"
        f" - "
        f"{result['crossing_probability_max']:.6f}"
    )

    print()
    print(
        f"Confidence                     : "
        f"{result['confidence']:.6f}"
    )

    print(
        f"Predictive entropy             : "
        f"{result['predictive_entropy']:.6f}"
    )

    print(
        f"Normalized predictive entropy  : "
        f"{result['normalized_predictive_entropy']:.6f}"
    )

    print(
        f"Expected entropy               : "
        f"{result['expected_entropy']:.6f}"
    )

    print(
        f"Mutual information             : "
        f"{result['mutual_information']:.6f}"
    )

    print(
        f"Variation ratio                : "
        f"{result['variation_ratio']:.6f}"
    )

    print()
    print(
        "First five MC crossing "
        "probabilities:"
    )

    print(
        result[
            "probability_samples"
        ][
            :5,
            1
        ]
    )


def main():

    print("=" * 78)
    print("PHASE 6.1 - MC DROPOUT UNCERTAINTY TEST")
    print("=" * 78)

    X, y = load_validation_data()

    not_crossing_indices = np.flatnonzero(
        y == 0
    )

    crossing_indices = np.flatnonzero(
        y == 1
    )

    if len(not_crossing_indices) == 0:
        raise ValueError(
            "No not-crossing validation sample."
        )

    if len(crossing_indices) == 0:
        raise ValueError(
            "No crossing validation sample."
        )

    selected_samples = [
        (
            "NOT-CROSSING SAMPLE",
            int(not_crossing_indices[0]),
            "not-crossing"
        ),
        (
            "CROSSING SAMPLE",
            int(crossing_indices[0]),
            "crossing"
        )
    ]

    estimator = (
        MCDropoutUncertaintyEstimator(
            checkpoint_path=
                CHECKPOINT_PATH,

            number_of_samples=
                NUMBER_OF_MC_SAMPLES,

            random_seed=42
        )
    )

    print("Device           :", estimator.device)
    print(
        "Input dimension  :",
        estimator.input_dimension
    )
    print(
        "Sequence length  :",
        estimator.sequence_length
    )

    for (
        title,
        sequence_index,
        true_label
    ) in selected_samples:

        result = estimator.estimate_single(
            feature_sequence=
                X[sequence_index],

            number_of_samples=
                NUMBER_OF_MC_SAMPLES,

            return_samples=True
        )

        validate_result(
            result
        )

        print_result(
            title=title,
            sequence_index=sequence_index,
            true_label=true_label,
            result=result
        )

    print()
    print("=" * 78)
    print("MC DROPOUT UNCERTAINTY TEST PASSED")
    print("=" * 78)

    print()
    print(
        "No low/medium/high uncertainty "
        "boundaries have been hardcoded."
    )

    print(
        "Those boundaries will be derived "
        "from validation uncertainty "
        "distributions in the next step."
    )


if __name__ == "__main__":
    main()