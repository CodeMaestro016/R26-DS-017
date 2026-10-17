"""
Test reusable runtime prediction pipeline.

This test simulates real-time arrival of 30
per-frame feature vectors using the existing
untouched test feature file.
"""

from pathlib import Path

import numpy as np

from utils.runtime_intent_predictor import (
    RuntimeIntentPredictor
)

from utils.sequence_buffer import (
    FeatureSequenceBuffer
)


FEATURE_PATH = Path(
    "datasets/processed/features/"
    "test_reliability_enriched_features.npz"
)

TEST_SEQUENCE_INDICES = [
    28,
    463
]

CLASS_NAMES = {
    0: "not-crossing",
    1: "crossing"
}


def load_test_data():

    if not FEATURE_PATH.exists():
        raise FileNotFoundError(
            f"Test feature file not found: "
            f"{FEATURE_PATH}"
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

    if X.shape != (
        1152,
        30,
        525
    ):
        raise ValueError(
            f"Unexpected test shape: {X.shape}"
        )

    return X, y


def main():

    print("=" * 78)
    print("RUNTIME INTENT PIPELINE TEST")
    print("=" * 78)

    X, y = load_test_data()

    predictor = RuntimeIntentPredictor()

    buffer = FeatureSequenceBuffer(
        sequence_length=
            predictor.sequence_length,

        feature_dimension=
            predictor.input_dimension
    )

    print(
        "Device             :",
        predictor.estimator.device
    )

    print(
        "Expected input     :",
        (
            predictor.sequence_length,
            predictor.input_dimension
        )
    )

    print(
        "Temperature        :",
        predictor.temperature
    )

    print(
        "Decision threshold :",
        predictor.decision_threshold
    )

    print(
        "MC samples         :",
        predictor.mc_samples
    )

    passed = 0

    for sequence_index in (
        TEST_SEQUENCE_INDICES
    ):

        buffer.reset()

        for time_step in range(
            predictor.sequence_length
        ):

            buffer.add(
                feature_vector=
                    X[
                        sequence_index,
                        time_step
                    ],

                metadata={
                    "sequence_index":
                        sequence_index,

                    "time_step":
                        time_step
                }
            )

        if not buffer.is_ready:
            raise RuntimeError(
                "Buffer did not become ready."
            )

        runtime_sequence = (
            buffer.get_sequence()
        )

        result = predictor.predict(
            feature_sequence=
                runtime_sequence,

            random_seed=
                1000 + sequence_index
        )

        true_class_id = int(
            y[sequence_index]
        )

        is_correct = (
            result["predicted_class_id"]
            == true_class_id
        )

        if is_correct:
            passed += 1

        print()
        print("-" * 78)

        print(
            "Sequence index       :",
            sequence_index
        )

        print(
            "Buffered shape       :",
            runtime_sequence.shape
        )

        print(
            "Ground-truth intent  :",
            CLASS_NAMES[
                true_class_id
            ]
        )

        print(
            "Predicted intent     :",
            result[
                "predicted_intent"
            ]
        )

        print(
            "Crossing probability:",
            f"{result['crossing_probability']:.6f}"
        )

        print(
            "Confidence           :",
            f"{result['confidence']:.6f}"
        )

        print(
            "Normalized entropy   :",
            f"{result['normalized_entropy']:.6f}"
        )

        print(
            "Probability variance :",
            f"{result['crossing_probability_variance']:.6f}"
        )

        print(
            "Status               :",
            "CORRECT"
            if is_correct
            else "INCORRECT"
        )

    print()
    print("=" * 78)

    print(
        f"Correct runtime predictions: "
        f"{passed}/"
        f"{len(TEST_SEQUENCE_INDICES)}"
    )

    if passed == len(
        TEST_SEQUENCE_INDICES
    ):
        print(
            "RUNTIME INTENT PIPELINE TEST PASSED"
        )
    else:
        print(
            "Runtime pipeline executed, but one or "
            "more stochastic predictions differed."
        )

    print("=" * 78)


if __name__ == "__main__":
    main()