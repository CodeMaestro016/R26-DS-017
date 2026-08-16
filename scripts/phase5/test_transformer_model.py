"""
Test the Transformer Intent Model using the
actual baseline and Bayesian-enriched feature files.
"""

from pathlib import Path

import numpy as np
import torch

from models.transformer_intent_model import (
    TransformerIntentModel
)


BASELINE_PATH = Path(
    "datasets/processed/features/"
    "train_features.npz"
)

ENRICHED_PATH = Path(
    "datasets/processed/features/"
    "train_enriched_features.npz"
)

EXPECTED_SEQUENCE_LENGTH = 30

EXPECTED_BASELINE_DIMENSION = 522
EXPECTED_ENRICHED_DIMENSION = 527

NUM_CLASSES = 2
TEST_BATCH_SIZE = 4


def load_npz(path):

    if not path.exists():
        raise FileNotFoundError(
            f"Feature file not found: {path}"
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

        X = data["X"]
        y = data["y"]

    return X, y


def validate_array(
    name,
    X,
    y,
    expected_dimension
):

    if X.ndim != 3:
        raise ValueError(
            f"{name}: expected 3D feature array, "
            f"but received {X.shape}."
        )

    if X.shape[1] != EXPECTED_SEQUENCE_LENGTH:
        raise ValueError(
            f"{name}: expected sequence length "
            f"{EXPECTED_SEQUENCE_LENGTH}, "
            f"but received {X.shape[1]}."
        )

    if X.shape[2] != expected_dimension:
        raise ValueError(
            f"{name}: expected feature dimension "
            f"{expected_dimension}, "
            f"but received {X.shape[2]}."
        )

    if len(X) != len(y):
        raise ValueError(
            f"{name}: feature and label counts "
            "do not match."
        )

    if not np.isfinite(X).all():
        raise ValueError(
            f"{name}: NaN or infinite values "
            "were detected."
        )

    unique_labels = set(
        np.unique(y).tolist()
    )

    if not unique_labels.issubset(
        {0, 1}
    ):
        raise ValueError(
            f"{name}: unsupported labels found: "
            f"{unique_labels}"
        )


def test_model(
    name,
    X,
    expected_dimension
):

    model = TransformerIntentModel(
        input_dim=expected_dimension,
        sequence_length=EXPECTED_SEQUENCE_LENGTH,
        num_classes=NUM_CLASSES
    )

    model.eval()

    sample = torch.from_numpy(
        X[:TEST_BATCH_SIZE]
    ).float()

    with torch.no_grad():

        logits = model(
            sample
        )

        probabilities = torch.softmax(
            logits,
            dim=1
        )

    expected_output_shape = (
        TEST_BATCH_SIZE,
        NUM_CLASSES
    )

    if tuple(logits.shape) != expected_output_shape:

        raise ValueError(
            f"{name}: expected logits shape "
            f"{expected_output_shape}, "
            f"but received {tuple(logits.shape)}."
        )

    probability_sums = (
        probabilities.sum(dim=1)
    )

    if not torch.allclose(
        probability_sums,
        torch.ones_like(
            probability_sums
        ),
        atol=1e-5
    ):
        raise ValueError(
            f"{name}: output probabilities "
            "do not sum to one."
        )

    print()
    print("-" * 70)
    print(name)
    print("-" * 70)

    print(
        "Input shape       :",
        tuple(sample.shape)
    )

    print(
        "Logits shape      :",
        tuple(logits.shape)
    )

    print(
        "Probabilities     :"
    )

    print(
        probabilities.cpu().numpy()
    )

    print(
        "Trainable params  :",
        f"{model.count_trainable_parameters():,}"
    )


def main():

    print("=" * 70)
    print("TRANSFORMER INTENT MODEL TEST")
    print("=" * 70)

    baseline_X, baseline_y = load_npz(
        BASELINE_PATH
    )

    enriched_X, enriched_y = load_npz(
        ENRICHED_PATH
    )

    validate_array(
        name="Baseline features",
        X=baseline_X,
        y=baseline_y,
        expected_dimension=
            EXPECTED_BASELINE_DIMENSION
    )

    validate_array(
        name="Enriched features",
        X=enriched_X,
        y=enriched_y,
        expected_dimension=
            EXPECTED_ENRICHED_DIMENSION
    )

    if not np.array_equal(
        baseline_y,
        enriched_y
    ):
        raise ValueError(
            "Baseline and enriched labels "
            "are not aligned."
        )

    print()
    print(
        "Baseline dataset shape :",
        baseline_X.shape
    )

    print(
        "Enriched dataset shape :",
        enriched_X.shape
    )

    print(
        "Label shape            :",
        baseline_y.shape
    )

    print(
        "Label distribution     :",
        dict(
            zip(
                *np.unique(
                    baseline_y,
                    return_counts=True
                )
            )
        )
    )

    test_model(
        name="Baseline Transformer",
        X=baseline_X,
        expected_dimension=
            EXPECTED_BASELINE_DIMENSION
    )

    test_model(
        name="Bayesian-Enriched Transformer",
        X=enriched_X,
        expected_dimension=
            EXPECTED_ENRICHED_DIMENSION
    )

    print()
    print("=" * 70)
    print("TRANSFORMER MODEL TEST PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()