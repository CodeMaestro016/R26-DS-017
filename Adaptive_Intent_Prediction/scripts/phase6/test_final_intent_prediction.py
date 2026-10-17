"""
End-to-end test of the final trained intent prediction system.

Loads:
- Final Reliability-only Transformer
- Validation-derived temperature
- Validation-derived MC decision threshold

Tests:
- One high-confidence not-crossing sequence
- One high-confidence crossing sequence
"""

from pathlib import Path
import json

import numpy as np
import pandas as pd

from utils.uncertainty_estimator import (
    MCDropoutUncertaintyEstimator
)

from scripts.phase6.evaluate_final_test_uncertainty import (
    temperature_scale_probabilities
)


FEATURE_PATH = Path(
    "datasets/processed/features/"
    "test_reliability_enriched_features.npz"
)

PREDICTION_PATH = Path(
    "outputs/phase6/final_test/"
    "test_uncertainty_predictions.csv"
)

DEPLOYMENT_CONFIG_PATH = Path(
    "outputs/phase6/final_test/"
    "uncertainty_deployment_config.json"
)


CLASS_NAMES = {
    0: "not-crossing",
    1: "crossing"
}


def load_test_features():

    if not FEATURE_PATH.exists():
        raise FileNotFoundError(
            f"Feature file not found: {FEATURE_PATH}"
        )

    with np.load(
        FEATURE_PATH,
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

    if X.shape != (1152, 30, 525):
        raise ValueError(
            f"Unexpected feature shape: {X.shape}"
        )

    return X, y


def load_deployment_config():

    if not DEPLOYMENT_CONFIG_PATH.exists():
        raise FileNotFoundError(
            "Deployment configuration not found: "
            f"{DEPLOYMENT_CONFIG_PATH}"
        )

    with open(
        DEPLOYMENT_CONFIG_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        config = json.load(file)

    required_keys = [
        "checkpoint",
        "temperature",
        "mc_samples",
        "decision_threshold"
    ]

    missing = [
        key
        for key in required_keys
        if key not in config
    ]

    if missing:
        raise KeyError(
            f"Missing deployment settings: {missing}"
        )

    return config


def select_high_confidence_examples():

    if not PREDICTION_PATH.exists():
        raise FileNotFoundError(
            f"Prediction file not found: "
            f"{PREDICTION_PATH}"
        )

    predictions = pd.read_csv(
        PREDICTION_PATH
    )

    correct_predictions = predictions[
        predictions["is_correct"].astype(bool)
    ].copy()

    selected_indices = []

    for label_id in [0, 1]:

        class_rows = correct_predictions[
            correct_predictions["label_id"]
            == label_id
        ].copy()

        if class_rows.empty:
            raise ValueError(
                f"No correct test prediction "
                f"available for class {label_id}."
            )

        class_rows = class_rows.sort_values(
            "confidence",
            ascending=False
        )

        sequence_index = int(
            class_rows.iloc[0][
                "sequence_index"
            ]
        )

        selected_indices.append(
            sequence_index
        )

    return selected_indices


def normalized_binary_entropy(
    crossing_probability
):

    epsilon = 1e-8

    p = np.clip(
        crossing_probability,
        epsilon,
        1.0 - epsilon
    )

    entropy = -(
        p * np.log(p)
        + (1.0 - p) * np.log(
            1.0 - p
        )
    )

    return float(
        entropy / np.log(2.0)
    )


def predict_sequence(
    estimator,
    feature_sequence,
    temperature,
    decision_threshold,
    mc_samples,
    random_seed
):

    estimator.random_seed = random_seed

    result = estimator.estimate_single(
        feature_sequence=feature_sequence,
        number_of_samples=mc_samples,
        return_samples=True
    )

    uncalibrated_samples = result[
        "probability_samples"
    ]

    calibrated_samples = (
        temperature_scale_probabilities(
            probabilities=
                uncalibrated_samples,
            temperature=temperature
        )
    )

    mean_probabilities = np.mean(
        calibrated_samples,
        axis=0
    )

    crossing_probability = float(
        mean_probabilities[1]
    )

    predicted_class_id = int(
        crossing_probability
        >= decision_threshold
    )

    confidence = float(
        mean_probabilities[
            predicted_class_id
        ]
    )

    crossing_variance = float(
        np.var(
            calibrated_samples[:, 1]
        )
    )

    normalized_entropy = (
        normalized_binary_entropy(
            crossing_probability
        )
    )

    return {
        "predicted_class_id":
            predicted_class_id,

        "predicted_class_name":
            CLASS_NAMES[
                predicted_class_id
            ],

        "not_crossing_probability":
            float(mean_probabilities[0]),

        "crossing_probability":
            crossing_probability,

        "confidence":
            confidence,

        "normalized_entropy":
            normalized_entropy,

        "crossing_probability_variance":
            crossing_variance
    }


def main():

    print("=" * 78)
    print("FINAL TRAINED INTENT PREDICTION TEST")
    print("=" * 78)

    X, y = load_test_features()

    deployment_config = (
        load_deployment_config()
    )

    temperature = float(
        deployment_config["temperature"]
    )

    decision_threshold = float(
        deployment_config[
            "decision_threshold"
        ]
    )

    mc_samples = int(
        deployment_config["mc_samples"]
    )

    checkpoint_path = (
        deployment_config["checkpoint"]
    )

    estimator = (
        MCDropoutUncertaintyEstimator(
            checkpoint_path=
                checkpoint_path,

            number_of_samples=
                mc_samples,

            random_seed=42
        )
    )

    selected_indices = (
        select_high_confidence_examples()
    )

    print(
        "Checkpoint         :",
        checkpoint_path
    )

    print(
        "Input dimension    :",
        estimator.input_dimension
    )

    print(
        "Temperature        :",
        temperature
    )

    print(
        "Decision threshold :",
        decision_threshold
    )

    print(
        "MC samples         :",
        mc_samples
    )

    passed_predictions = 0

    for sequence_index in selected_indices:

        true_class_id = int(
            y[sequence_index]
        )

        result = predict_sequence(
            estimator=estimator,
            feature_sequence=
                X[sequence_index],
            temperature=temperature,
            decision_threshold=
                decision_threshold,
            mc_samples=mc_samples,
            random_seed=
                1000 + sequence_index
        )

        is_correct = (
            result["predicted_class_id"]
            == true_class_id
        )

        if is_correct:
            passed_predictions += 1

        print()
        print("-" * 78)

        print(
            "Sequence index        :",
            sequence_index
        )

        print(
            "Ground-truth intent   :",
            CLASS_NAMES[
                true_class_id
            ]
        )

        print(
            "Predicted intent      :",
            result[
                "predicted_class_name"
            ]
        )

        print(
            "Not-crossing prob.    :",
            f"{result['not_crossing_probability']:.6f}"
        )

        print(
            "Crossing probability :",
            f"{result['crossing_probability']:.6f}"
        )

        print(
            "Confidence            :",
            f"{result['confidence']:.6f}"
        )

        print(
            "Normalized entropy    :",
            f"{result['normalized_entropy']:.6f}"
        )

        print(
            "Probability variance  :",
            f"{result['crossing_probability_variance']:.6f}"
        )

        print(
            "Prediction status     :",
            "CORRECT" if is_correct else "INCORRECT"
        )

    print()
    print("=" * 78)

    print(
        f"Correct sample predictions: "
        f"{passed_predictions}/"
        f"{len(selected_indices)}"
    )

    if passed_predictions == len(
        selected_indices
    ):

        print(
            "FINAL INTENT PREDICTION TEST PASSED"
        )

    else:

        print(
            "Some stochastic predictions changed. "
            "Inspect the printed probabilities."
        )

    print("=" * 78)


if __name__ == "__main__":
    main()