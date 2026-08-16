"""
Test the Gated Bayesian Fusion Transformer
using actual project feature files.
"""

from pathlib import Path

import numpy as np
import torch

from models.gated_fusion_intent_model import (
    GatedFusionIntentModel
)


FEATURE_DIR = Path(
    "datasets/processed/features"
)

VISUAL_PATH = (
    FEATURE_DIR
    / "train_features.npz"
)

BAYESIAN_PATH = (
    FEATURE_DIR
    / "train_bayesian_features.npz"
)

BATCH_SIZE = 4


def load_npz(path):

    if not path.exists():
        raise FileNotFoundError(
            f"File not found: {path}"
        )

    with np.load(
        path,
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

    return X, y


def main():

    print("=" * 70)
    print("GATED FUSION MODEL TEST")
    print("=" * 70)

    visual_X, visual_y = load_npz(
        VISUAL_PATH
    )

    bayesian_X, bayesian_y = load_npz(
        BAYESIAN_PATH
    )

    if (
        visual_X.shape[:2]
        != bayesian_X.shape[:2]
    ):
        raise ValueError(
            "Visual and Bayesian arrays "
            "are not aligned."
        )

    if not np.array_equal(
        visual_y,
        bayesian_y
    ):
        raise ValueError(
            "Visual and Bayesian labels "
            "are not aligned."
        )

    visual_batch = torch.from_numpy(
        visual_X[:BATCH_SIZE]
    ).float()

    bayesian_batch = torch.from_numpy(
        bayesian_X[:BATCH_SIZE]
    ).float()

    model = GatedFusionIntentModel(
        visual_input_dim=522,
        bayesian_input_dim=5,
        sequence_length=30,
        num_classes=2
    )

    model.eval()

    with torch.no_grad():

        result = model(
            visual_features=
                visual_batch,

            bayesian_features=
                bayesian_batch,

            return_diagnostics=True
        )

        logits = result["logits"]

        probabilities = torch.softmax(
            logits,
            dim=1
        )

        fusion_gate = (
            result["fusion_gate"]
        )

        attention_weights = (
            result[
                "bayesian_attention_weights"
            ]
        )

    if tuple(logits.shape) != (
        BATCH_SIZE,
        2
    ):
        raise ValueError(
            f"Incorrect logits shape: "
            f"{tuple(logits.shape)}"
        )

    if tuple(fusion_gate.shape) != (
        BATCH_SIZE,
        128
    ):
        raise ValueError(
            f"Incorrect gate shape: "
            f"{tuple(fusion_gate.shape)}"
        )

    if tuple(attention_weights.shape) != (
        BATCH_SIZE,
        30
    ):
        raise ValueError(
            "Incorrect Bayesian attention "
            f"shape: "
            f"{tuple(attention_weights.shape)}"
        )

    if not torch.allclose(
        probabilities.sum(dim=1),
        torch.ones(
            BATCH_SIZE
        ),
        atol=1e-5
    ):
        raise ValueError(
            "Probabilities do not sum to one."
        )

    if (
        fusion_gate.min() < 0
        or fusion_gate.max() > 1
    ):
        raise ValueError(
            "Fusion gate values must be "
            "between zero and one."
        )

    if not torch.allclose(
        attention_weights.sum(dim=1),
        torch.ones(
            BATCH_SIZE
        ),
        atol=1e-5
    ):
        raise ValueError(
            "Bayesian attention weights "
            "do not sum to one."
        )

    print()
    print(
        "Visual input shape    :",
        tuple(visual_batch.shape)
    )

    print(
        "Bayesian input shape  :",
        tuple(bayesian_batch.shape)
    )

    print(
        "Logits shape          :",
        tuple(logits.shape)
    )

    print(
        "Probability shape     :",
        tuple(probabilities.shape)
    )

    print(
        "Fusion gate shape     :",
        tuple(fusion_gate.shape)
    )

    print(
        "Attention shape       :",
        tuple(attention_weights.shape)
    )

    print(
        "Initial gate mean     :",
        float(fusion_gate.mean())
    )

    print(
        "Trainable parameters  :",
        f"{model.count_trainable_parameters():,}"
    )

    print()
    print("Probabilities:")
    print(
        probabilities.numpy()
    )

    print()
    print("=" * 70)
    print("GATED FUSION MODEL TEST PASSED")
    print("=" * 70)

    print()
    print(
        "The model is not trained yet. "
        "The displayed probabilities and "
        "gate values are initialization outputs."
    )


if __name__ == "__main__":
    main()