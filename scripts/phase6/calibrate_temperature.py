"""
Phase 6.3 - Temperature Scaling Calibration.

Uses the validation split only to learn one positive
temperature value.

The frozen Transformer weights are not changed.

Outputs:
    outputs/phase6/temperature_calibration.json
"""

from pathlib import Path
import json
import math

import numpy as np
import torch
import torch.nn as nn

from sklearn.metrics import (
    brier_score_loss,
    log_loss,
    precision_recall_curve
)

from models.transformer_intent_model import (
    TransformerIntentModel
)


FEATURE_PATH = Path(
    "datasets/processed/features/"
    "val_reliability_enriched_features.npz"
)

CHECKPOINT_PATH = Path(
    "outputs/phase5/"
    "reliability_only_transformer_best.pt"
)

OUTPUT_PATH = Path(
    "outputs/phase6/"
    "temperature_calibration.json"
)

EXPECTED_SHAPE = (845, 30, 525)

BATCH_SIZE = 128
ECE_BINS = 15


def load_validation_data():

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

    if X.shape != EXPECTED_SHAPE:
        raise ValueError(
            f"Expected {EXPECTED_SHAPE}, got {X.shape}"
        )

    if len(X) != len(y):
        raise ValueError(
            "Feature and label counts do not match."
        )

    if not np.isfinite(X).all():
        raise ValueError(
            "NaN or infinite values found."
        )

    return X, y


def load_checkpoint(device):

    if not CHECKPOINT_PATH.exists():
        raise FileNotFoundError(
            f"Checkpoint not found: {CHECKPOINT_PATH}"
        )

    try:
        checkpoint = torch.load(
            CHECKPOINT_PATH,
            map_location=device,
            weights_only=False
        )

    except TypeError:
        checkpoint = torch.load(
            CHECKPOINT_PATH,
            map_location=device
        )

    return checkpoint


def create_model(checkpoint, device):

    configuration = checkpoint[
        "model_configuration"
    ]

    model = TransformerIntentModel(
        input_dim=int(
            checkpoint["input_dimension"]
        ),
        sequence_length=int(
            checkpoint["sequence_length"]
        ),
        num_classes=int(
            checkpoint["num_classes"]
        ),
        d_model=int(
            configuration["d_model"]
        ),
        num_heads=int(
            configuration["num_heads"]
        ),
        num_layers=int(
            configuration["num_layers"]
        ),
        dim_feedforward=int(
            configuration["dim_feedforward"]
        ),
        dropout=float(
            configuration["dropout"]
        )
    )

    model.load_state_dict(
        checkpoint["model_state_dict"]
    )

    model.to(device)
    model.eval()

    return model


def checkpoint_array(value):

    if isinstance(value, torch.Tensor):

        value = (
            value
            .detach()
            .cpu()
            .numpy()
        )

    return np.asarray(
        value,
        dtype=np.float32
    ).reshape(-1)


def collect_validation_logits(
    model,
    features,
    feature_mean,
    feature_std,
    device
):

    all_logits = []

    with torch.no_grad():

        for start_index in range(
            0,
            len(features),
            BATCH_SIZE
        ):

            end_index = min(
                start_index + BATCH_SIZE,
                len(features)
            )

            batch = features[
                start_index:end_index
            ]

            batch = (
                batch
                - feature_mean.reshape(
                    1,
                    1,
                    -1
                )
            ) / feature_std.reshape(
                1,
                1,
                -1
            )

            batch_tensor = torch.from_numpy(
                np.ascontiguousarray(
                    batch,
                    dtype=np.float32
                )
            ).to(device)

            logits = model(
                batch_tensor
            )

            all_logits.append(
                logits.detach()
            )

    return torch.cat(
        all_logits,
        dim=0
    )


def calculate_ece(
    labels,
    crossing_probabilities,
    number_of_bins=15
):

    bin_edges = np.linspace(
        0.0,
        1.0,
        number_of_bins + 1
    )

    bin_ids = np.digitize(
        crossing_probabilities,
        bin_edges[1:-1],
        right=True
    )

    total_samples = len(labels)
    ece = 0.0

    for bin_index in range(
        number_of_bins
    ):

        mask = (
            bin_ids == bin_index
        )

        sample_count = int(
            np.sum(mask)
        )

        if sample_count == 0:
            continue

        mean_probability = float(
            np.mean(
                crossing_probabilities[mask]
            )
        )

        observed_frequency = float(
            np.mean(
                labels[mask]
            )
        )

        ece += (
            sample_count
            / total_samples
        ) * abs(
            mean_probability
            - observed_frequency
        )

    return float(ece)


def select_f1_threshold(
    labels,
    probabilities
):

    precision, recall, thresholds = (
        precision_recall_curve(
            labels,
            probabilities
        )
    )

    if len(thresholds) == 0:
        return 0.5

    precision = precision[:-1]
    recall = recall[:-1]

    f1_values = (
        2.0
        * precision
        * recall
        / (
            precision
            + recall
            + 1e-12
        )
    )

    best_f1 = np.max(
        f1_values
    )

    candidates = np.flatnonzero(
        np.isclose(
            f1_values,
            best_f1
        )
    )

    selected_index = candidates[
        np.argmin(
            np.abs(
                thresholds[candidates]
                - 0.5
            )
        )
    ]

    return float(
        thresholds[selected_index]
    )


def probability_metrics(
    labels,
    logits
):

    probabilities = torch.softmax(
        logits,
        dim=1
    ).detach().cpu().numpy()

    crossing_probabilities = (
        probabilities[:, 1]
    )

    clipped = np.clip(
        crossing_probabilities,
        1e-7,
        1.0 - 1e-7
    )

    two_class_probabilities = (
        np.column_stack(
            [
                1.0 - clipped,
                clipped
            ]
        )
    )

    return {
        "brier_score": float(
            brier_score_loss(
                labels,
                clipped
            )
        ),

        "negative_log_likelihood": float(
            log_loss(
                labels,
                two_class_probabilities,
                labels=[0, 1]
            )
        ),

        "expected_calibration_error": float(
            calculate_ece(
                labels,
                clipped,
                number_of_bins=ECE_BINS
            )
        ),

        "f1_optimal_threshold": float(
            select_f1_threshold(
                labels,
                clipped
            )
        )
    }


def learn_temperature(
    logits,
    labels,
    device
):

    label_tensor = torch.tensor(
        labels,
        dtype=torch.long,
        device=device
    )

    # Optimize log-temperature so temperature
    # always remains positive.
    log_temperature = nn.Parameter(
        torch.zeros(
            1,
            device=device
        )
    )

    loss_function = nn.CrossEntropyLoss()

    optimizer = torch.optim.LBFGS(
        [log_temperature],
        lr=0.1,
        max_iter=100,
        tolerance_grad=1e-7,
        tolerance_change=1e-9,
        line_search_fn="strong_wolfe"
    )

    def closure():

        optimizer.zero_grad()

        temperature = torch.exp(
            log_temperature
        )

        calibrated_logits = (
            logits / temperature
        )

        loss = loss_function(
            calibrated_logits,
            label_tensor
        )

        loss.backward()

        return loss

    optimizer.step(
        closure
    )

    temperature = float(
        torch.exp(
            log_temperature
        ).detach().cpu().item()
    )

    if not math.isfinite(
        temperature
    ):

        raise ValueError(
            "Learned temperature is not finite."
        )

    if temperature <= 0:
        raise ValueError(
            "Temperature must be positive."
        )

    return temperature


def main():

    print("=" * 78)
    print("PHASE 6.3 - TEMPERATURE CALIBRATION")
    print("=" * 78)

    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    print("Device:", device)

    X, y = load_validation_data()

    checkpoint = load_checkpoint(
        device
    )

    model = create_model(
        checkpoint,
        device
    )

    feature_mean = checkpoint_array(
        checkpoint["feature_mean"]
    )

    feature_std = checkpoint_array(
        checkpoint[
            "feature_standard_deviation"
        ]
    )

    print(
        "Collecting validation logits..."
    )

    logits = collect_validation_logits(
        model=model,
        features=X,
        feature_mean=feature_mean,
        feature_std=feature_std,
        device=device
    )

    before_metrics = probability_metrics(
        labels=y,
        logits=logits
    )

    temperature = learn_temperature(
        logits=logits,
        labels=y,
        device=device
    )

    calibrated_logits = (
        logits / temperature
    )

    after_metrics = probability_metrics(
        labels=y,
        logits=calibrated_logits
    )

    result = {
        "checkpoint": str(
            CHECKPOINT_PATH
        ),

        "calibration_split":
            "validation",

        "validation_samples": int(
            len(y)
        ),

        "temperature": float(
            temperature
        ),

        "before_calibration":
            before_metrics,

        "after_calibration":
            after_metrics,

        "model_weights_modified":
            False,

        "test_split_used":
            False
    }

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        OUTPUT_PATH,
        "w",
        encoding="utf-8"
    ) as output_file:

        json.dump(
            result,
            output_file,
            indent=4
        )

    print()
    print("=" * 78)
    print("CALIBRATION RESULTS")
    print("=" * 78)

    print(
        f"Temperature: {temperature:.6f}"
    )

    print()
    print("Before calibration:")

    for name, value in (
        before_metrics.items()
    ):

        print(
            f"  {name:30}: "
            f"{value:.6f}"
        )

    print()
    print("After calibration:")

    for name, value in (
        after_metrics.items()
    ):

        print(
            f"  {name:30}: "
            f"{value:.6f}"
        )

    print()
    print(
        "Saved:",
        OUTPUT_PATH
    )

    print()
    print(
        "The test split has not been used."
    )


if __name__ == "__main__":
    main()