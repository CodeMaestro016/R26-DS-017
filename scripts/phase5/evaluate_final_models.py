"""
Final evaluation of the frozen Transformer architectures.

Models
------
1. Baseline Transformer:
       522 original features

2. Final proposed Transformer:
       522 original + 3 Bayesian reliability probabilities
       = 525 features

Important
---------
- Model selection was performed using validation data.
- Decision thresholds are selected using validation data only.
- Test data is used only for final evaluation.
- Occlusion-specific test results are also generated.
"""

from pathlib import Path
import json

import numpy as np
import pandas as pd
import torch

from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score
)

from models.transformer_intent_model import (
    TransformerIntentModel
)


FEATURE_DIR = Path(
    "datasets/processed/features"
)

METADATA_DIR = Path(
    "datasets/processed/metadata"
)

BAYESIAN_DIR = Path(
    "datasets/processed/bayesian"
)

OUTPUT_DIR = Path(
    "outputs/phase5/final_evaluation"
)

BATCH_SIZE = 128


MODEL_SPECIFICATIONS = {
    "baseline": {
        "checkpoint": Path(
            "outputs/phase5/"
            "baseline_transformer_best.pt"
        ),
        "validation_features": (
            FEATURE_DIR / "val_features.npz"
        ),
        "test_features": (
            FEATURE_DIR / "test_features.npz"
        ),
        "expected_dimension": 522
    },

    "reliability_only": {
        "checkpoint": Path(
            "outputs/phase5/"
            "reliability_only_transformer_best.pt"
        ),
        "validation_features": (
            FEATURE_DIR
            / "val_reliability_enriched_features.npz"
        ),
        "test_features": (
            FEATURE_DIR
            / "test_reliability_enriched_features.npz"
        ),
        "expected_dimension": 525
    }
}


def load_npz(path, expected_dimension):

    if not path.exists():
        raise FileNotFoundError(
            f"Feature file not found: {path}"
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

    if X.ndim != 3:
        raise ValueError(
            f"Expected 3D feature array, got {X.shape}"
        )

    if X.shape[1] != 30:
        raise ValueError(
            f"Expected sequence length 30, got {X.shape[1]}"
        )

    if X.shape[2] != expected_dimension:
        raise ValueError(
            f"Expected feature dimension "
            f"{expected_dimension}, got {X.shape[2]}"
        )

    if len(X) != len(y):
        raise ValueError(
            "Feature and label counts do not match."
        )

    if not np.isfinite(X).all():
        raise ValueError(
            f"NaN or infinite values found in {path}"
        )

    return X, y


def load_checkpoint(path, device):

    if not path.exists():
        raise FileNotFoundError(
            f"Checkpoint not found: {path}"
        )

    try:
        checkpoint = torch.load(
            path,
            map_location=device,
            weights_only=False
        )

    except TypeError:
        checkpoint = torch.load(
            path,
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


def get_normalization_arrays(checkpoint):

    feature_mean = (
        checkpoint["feature_mean"]
        .detach()
        .cpu()
        .numpy()
        .astype(np.float32)
    )

    feature_standard_deviation = (
        checkpoint[
            "feature_standard_deviation"
        ]
        .detach()
        .cpu()
        .numpy()
        .astype(np.float32)
    )

    return (
        feature_mean,
        feature_standard_deviation
    )


def predict_probabilities(
    model,
    features,
    feature_mean,
    feature_standard_deviation,
    device
):

    positive_probabilities = []

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
                - feature_mean.reshape(1, 1, -1)
            ) / feature_standard_deviation.reshape(
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

            probabilities = torch.softmax(
                logits,
                dim=1
            )[:, 1]

            positive_probabilities.append(
                probabilities
                .cpu()
                .numpy()
            )

    return np.concatenate(
        positive_probabilities
    )


def select_validation_threshold(
    labels,
    probabilities
):
    """
    Select the threshold that maximizes crossing F1
    using validation data only.
    """

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

    candidate_indices = np.flatnonzero(
        np.isclose(
            f1_values,
            best_f1
        )
    )

    # If several thresholds give the same F1,
    # select the one closest to the standard 0.5.
    best_index = candidate_indices[
        np.argmin(
            np.abs(
                thresholds[
                    candidate_indices
                ]
                - 0.5
            )
        )
    ]

    return float(
        thresholds[best_index]
    )


def calculate_metrics(
    labels,
    probabilities,
    threshold
):

    predictions = (
        probabilities >= threshold
    ).astype(np.int64)

    tn, fp, fn, tp = confusion_matrix(
        labels,
        predictions,
        labels=[0, 1]
    ).ravel()

    specificity_denominator = (
        tn + fp
    )

    specificity = (
        tn / specificity_denominator
        if specificity_denominator > 0
        else float("nan")
    )

    unique_labels = np.unique(
        labels
    )

    if len(unique_labels) == 2:

        roc_auc = roc_auc_score(
            labels,
            probabilities
        )

        average_precision = (
            average_precision_score(
                labels,
                probabilities
            )
        )

    else:

        roc_auc = float("nan")
        average_precision = float("nan")

    return {
        "samples": int(len(labels)),

        "not_crossing_samples": int(
            np.sum(labels == 0)
        ),

        "crossing_samples": int(
            np.sum(labels == 1)
        ),

        "threshold": float(threshold),

        "accuracy": float(
            accuracy_score(
                labels,
                predictions
            )
        ),

        "precision": float(
            precision_score(
                labels,
                predictions,
                pos_label=1,
                zero_division=0
            )
        ),

        "recall": float(
            recall_score(
                labels,
                predictions,
                pos_label=1,
                zero_division=0
            )
        ),

        "specificity": float(
            specificity
        ),

        "f1": float(
            f1_score(
                labels,
                predictions,
                pos_label=1,
                zero_division=0
            )
        ),

        "roc_auc": float(
            roc_auc
        ),

        "average_precision": float(
            average_precision
        ),

        "true_negative": int(tn),
        "false_positive": int(fp),
        "false_negative": int(fn),
        "true_positive": int(tp)
    }


def build_occlusion_summary(
    number_of_sequences
):

    path = (
        BAYESIAN_DIR
        / "test_bayesian.csv"
    )

    if not path.exists():
        raise FileNotFoundError(
            f"Test Bayesian dataset not found: {path}"
        )

    data = pd.read_csv(
        path
    )

    required_columns = {
        "sequence_index",
        "time_step",
        "occlusion"
    }

    if not required_columns.issubset(
        data.columns
    ):
        raise ValueError(
            "Required occlusion columns are missing."
        )

    data["occlusion"] = (
        data["occlusion"]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    invalid_states = set(
        data["occlusion"].unique()
    ) - {
        "low",
        "medium",
        "high"
    }

    if invalid_states:
        raise ValueError(
            f"Invalid occlusion states: {invalid_states}"
        )

    counts = pd.crosstab(
        data["sequence_index"],
        data["occlusion"]
    )

    counts = counts.reindex(
        index=range(number_of_sequences),
        columns=[
            "low",
            "medium",
            "high"
        ],
        fill_value=0
    )

    counts.columns = [
        "low_frame_count",
        "medium_frame_count",
        "high_frame_count"
    ]

    total_frames = counts.sum(
        axis=1
    )

    if not np.all(
        total_frames.to_numpy() == 30
    ):
        raise ValueError(
            "Each sequence must contain exactly "
            "30 occlusion records."
        )

    summary = counts.copy()

    summary["low_fraction"] = (
        summary["low_frame_count"]
        / total_frames
    )

    summary["medium_fraction"] = (
        summary["medium_frame_count"]
        / total_frames
    )

    summary["high_fraction"] = (
        summary["high_frame_count"]
        / total_frames
    )

    summary["maximum_occlusion"] = "low"

    summary.loc[
        summary["medium_frame_count"] > 0,
        "maximum_occlusion"
    ] = "medium"

    summary.loc[
        summary["high_frame_count"] > 0,
        "maximum_occlusion"
    ] = "high"

    summary = summary.reset_index()

    return summary


def evaluate_occlusion_subsets(
    model_name,
    labels,
    probabilities,
    threshold,
    occlusion_summary
):

    maximum_occlusion = (
        occlusion_summary[
            "maximum_occlusion"
        ].to_numpy()
    )

    subset_masks = {
        "all_test_sequences":
            np.ones(
                len(labels),
                dtype=bool
            ),

        "low_only":
            maximum_occlusion == "low",

        "any_occluded":
            maximum_occlusion != "low",

        "maximum_medium":
            maximum_occlusion == "medium",

        "contains_high":
            maximum_occlusion == "high"
    }

    rows = []

    for subset_name, mask in (
        subset_masks.items()
    ):

        if not np.any(mask):
            continue

        metrics = calculate_metrics(
            labels=labels[mask],
            probabilities=probabilities[mask],
            threshold=threshold
        )

        rows.append({
            "model": model_name,
            "subset": subset_name,
            **metrics
        })

    return rows


def main():

    print("=" * 78)
    print("PHASE 5.4 - FINAL TEST EVALUATION")
    print("=" * 78)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    print("Device:", device)

    model_outputs = {}
    test_labels_reference = None

    overall_rows = []

    for model_name, specification in (
        MODEL_SPECIFICATIONS.items()
    ):

        print()
        print("=" * 78)
        print(
            f"EVALUATING {model_name.upper()}"
        )
        print("=" * 78)

        validation_X, validation_y = load_npz(
            specification[
                "validation_features"
            ],
            specification[
                "expected_dimension"
            ]
        )

        test_X, test_y = load_npz(
            specification[
                "test_features"
            ],
            specification[
                "expected_dimension"
            ]
        )

        if test_labels_reference is None:
            test_labels_reference = test_y.copy()

        elif not np.array_equal(
            test_labels_reference,
            test_y
        ):
            raise ValueError(
                "Test labels are not aligned "
                "between models."
            )

        checkpoint = load_checkpoint(
            specification["checkpoint"],
            device
        )

        model = create_model(
            checkpoint,
            device
        )

        feature_mean, feature_std = (
            get_normalization_arrays(
                checkpoint
            )
        )

        validation_probabilities = (
            predict_probabilities(
                model=model,
                features=validation_X,
                feature_mean=feature_mean,
                feature_standard_deviation=
                    feature_std,
                device=device
            )
        )

        selected_threshold = (
            select_validation_threshold(
                labels=validation_y,
                probabilities=
                    validation_probabilities
            )
        )

        test_probabilities = (
            predict_probabilities(
                model=model,
                features=test_X,
                feature_mean=feature_mean,
                feature_standard_deviation=
                    feature_std,
                device=device
            )
        )

        default_metrics = calculate_metrics(
            labels=test_y,
            probabilities=test_probabilities,
            threshold=0.5
        )

        validation_threshold_metrics = (
            calculate_metrics(
                labels=test_y,
                probabilities=test_probabilities,
                threshold=selected_threshold
            )
        )

        overall_rows.append({
            "model": model_name,
            "threshold_mode": "default_0.5",
            **default_metrics
        })

        overall_rows.append({
            "model": model_name,
            "threshold_mode":
                "validation_f1_optimal",
            **validation_threshold_metrics
        })

        model_outputs[model_name] = {
            "probabilities":
                test_probabilities,

            "selected_threshold":
                selected_threshold,

            "metrics":
                validation_threshold_metrics
        }

        print(
            "Validation-selected threshold:",
            f"{selected_threshold:.6f}"
        )

        print(
            "Test accuracy:",
            f"{validation_threshold_metrics['accuracy']:.6f}"
        )

        print(
            "Test precision:",
            f"{validation_threshold_metrics['precision']:.6f}"
        )

        print(
            "Test recall:",
            f"{validation_threshold_metrics['recall']:.6f}"
        )

        print(
            "Test F1:",
            f"{validation_threshold_metrics['f1']:.6f}"
        )

        print(
            "Test ROC-AUC:",
            f"{validation_threshold_metrics['roc_auc']:.6f}"
        )

        print(
            "Test Average Precision:",
            f"{validation_threshold_metrics['average_precision']:.6f}"
        )

        del model

        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    number_of_test_sequences = len(
        test_labels_reference
    )

    occlusion_summary = (
        build_occlusion_summary(
            number_of_sequences=
                number_of_test_sequences
        )
    )

    subset_rows = []

    for model_name, output in (
        model_outputs.items()
    ):

        subset_rows.extend(
            evaluate_occlusion_subsets(
                model_name=model_name,
                labels=test_labels_reference,
                probabilities=
                    output["probabilities"],
                threshold=
                    output["selected_threshold"],
                occlusion_summary=
                    occlusion_summary
            )
        )

    overall_dataframe = pd.DataFrame(
        overall_rows
    )

    subset_dataframe = pd.DataFrame(
        subset_rows
    )

    test_metadata = pd.read_csv(
        METADATA_DIR / "test.csv"
    ).reset_index(drop=True)

    if len(test_metadata) != (
        number_of_test_sequences
    ):
        raise ValueError(
            "Test metadata count does not match "
            "test prediction count."
        )

    predictions = test_metadata.copy()

    predictions.insert(
        0,
        "sequence_index",
        np.arange(
            number_of_test_sequences
        )
    )

    predictions["label_id"] = (
        test_labels_reference
    )

    predictions = predictions.merge(
        occlusion_summary,
        on="sequence_index",
        how="left",
        validate="one_to_one"
    )

    for model_name, output in (
        model_outputs.items()
    ):

        threshold = output[
            "selected_threshold"
        ]

        probabilities = output[
            "probabilities"
        ]

        predictions[
            f"{model_name}_crossing_probability"
        ] = probabilities

        predictions[
            f"{model_name}_prediction"
        ] = (
            probabilities >= threshold
        ).astype(np.int64)

        predictions[
            f"{model_name}_threshold"
        ] = threshold

    overall_path = (
        OUTPUT_DIR
        / "final_test_comparison.csv"
    )

    subset_path = (
        OUTPUT_DIR
        / "occlusion_subset_comparison.csv"
    )

    predictions_path = (
        OUTPUT_DIR
        / "final_test_predictions.csv"
    )

    summary_path = (
        OUTPUT_DIR
        / "final_test_summary.json"
    )

    overall_dataframe.to_csv(
        overall_path,
        index=False
    )

    subset_dataframe.to_csv(
        subset_path,
        index=False
    )

    predictions.to_csv(
        predictions_path,
        index=False
    )

    summary = {
        model_name: {
            "validation_selected_threshold":
                float(
                    output[
                        "selected_threshold"
                    ]
                ),

            "test_metrics":
                output["metrics"]
        }
        for model_name, output
        in model_outputs.items()
    }

    with open(
        summary_path,
        "w",
        encoding="utf-8"
    ) as output_file:

        json.dump(
            summary,
            output_file,
            indent=4
        )

    print()
    print("=" * 78)
    print("FINAL TEST EVALUATION COMPLETE")
    print("=" * 78)

    print("Overall comparison:", overall_path)
    print("Occlusion comparison:", subset_path)
    print("Predictions:", predictions_path)
    print("Summary:", summary_path)

    print()
    print(
        "The test set evaluation is now complete. "
        "Do not tune the models using these results."
    )


if __name__ == "__main__":
    main()