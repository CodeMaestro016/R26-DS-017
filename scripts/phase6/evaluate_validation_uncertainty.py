"""
Phase 6.2 - Validation-wide uncertainty evaluation.

This script:

1. Loads the frozen reliability-only Transformer.
2. Runs MC Dropout on the complete validation set.
3. Selects the Phase 6 decision threshold using
   validation MC-mean probabilities only.
4. Measures:
   - Classification performance
   - Probability calibration
   - Correct-vs-incorrect uncertainty
   - Error-detection ROC-AUC and Average Precision
   - Risk-coverage behaviour
   - Uncertainty by occlusion subset

The test split is not used.
"""

from pathlib import Path
import json
import math

import numpy as np
import pandas as pd

from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    f1_score,
    log_loss,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score
)

from utils.uncertainty_estimator import (
    MCDropoutUncertaintyEstimator
)


# =====================================================================
# Configuration
# =====================================================================

FEATURE_PATH = Path(
    "datasets/processed/features/"
    "val_reliability_enriched_features.npz"
)

METADATA_PATH = Path(
    "datasets/processed/metadata/val.csv"
)

BAYESIAN_DATA_PATH = Path(
    "datasets/processed/bayesian/"
    "val_bayesian.csv"
)

CHECKPOINT_PATH = Path(
    "outputs/phase5/"
    "reliability_only_transformer_best.pt"
)

OUTPUT_DIR = Path(
    "outputs/phase6"
)

NUMBER_OF_MC_SAMPLES = 30
BATCH_SIZE = 64
RANDOM_SEED = 42

EXPECTED_SHAPE = (
    845,
    30,
    525
)

ECE_BINS = 15

RISK_COVERAGES = [
    1.00,
    0.90,
    0.80,
    0.70,
    0.50
]


# =====================================================================
# Loading
# =====================================================================

def load_validation_features():

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
            f"Expected validation shape "
            f"{EXPECTED_SHAPE}, received {X.shape}."
        )

    if len(X) != len(y):
        raise ValueError(
            "Feature and label counts do not match."
        )

    if not np.isfinite(X).all():
        raise ValueError(
            "NaN or infinite feature values detected."
        )

    unique_labels = set(
        np.unique(y).tolist()
    )

    if not unique_labels.issubset({0, 1}):
        raise ValueError(
            f"Unsupported labels: {unique_labels}"
        )

    return X, y


def load_validation_metadata(
    number_of_sequences
):

    if not METADATA_PATH.exists():
        raise FileNotFoundError(
            f"Metadata file not found: {METADATA_PATH}"
        )

    metadata = pd.read_csv(
        METADATA_PATH
    ).reset_index(drop=True)

    if len(metadata) != number_of_sequences:
        raise ValueError(
            "Validation metadata count does not match "
            "the validation feature count."
        )

    return metadata


# =====================================================================
# Decision threshold
# =====================================================================

def select_f1_threshold(
    labels,
    probabilities
):
    """
    Select the threshold that maximizes crossing F1.

    This uses validation data only.
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

    # In a tie, prefer the threshold closest to 0.5.
    selected_index = candidate_indices[
        np.argmin(
            np.abs(
                thresholds[candidate_indices]
                - 0.5
            )
        )
    ]

    return float(
        thresholds[selected_index]
    )


# =====================================================================
# Dataset-wide MC inference
# =====================================================================

def run_mc_inference(
    estimator,
    features
):

    outputs = {
        "deterministic_probabilities": [],
        "mean_probabilities": [],
        "confidence": [],
        "predictive_entropy": [],
        "normalized_predictive_entropy": [],
        "expected_entropy": [],
        "mutual_information": [],
        "variation_ratio": [],
        "crossing_probability_variance": [],
        "crossing_probability_std": [],
        "crossing_probability_min": [],
        "crossing_probability_max": []
    }

    number_of_batches = math.ceil(
        len(features) / BATCH_SIZE
    )

    for batch_number, start_index in enumerate(
        range(
            0,
            len(features),
            BATCH_SIZE
        ),
        start=1
    ):

        end_index = min(
            start_index + BATCH_SIZE,
            len(features)
        )

        print(
            f"MC batch {batch_number:02d}/"
            f"{number_of_batches:02d} | "
            f"Sequences {start_index}-"
            f"{end_index - 1}"
        )

        # Prevent every batch from resetting to
        # exactly the same random sequence.
        estimator.random_seed = (
            RANDOM_SEED
            + batch_number
        )

        result = estimator.estimate_batch(
            features=features[
                start_index:end_index
            ],
            number_of_samples=
                NUMBER_OF_MC_SAMPLES,
            return_samples=False
        )

        for key in outputs:
            outputs[key].append(
                result[key]
            )

    for key in outputs:
        outputs[key] = np.concatenate(
            outputs[key],
            axis=0
        )

    expected_rows = len(features)

    for key, values in outputs.items():

        if len(values) != expected_rows:
            raise ValueError(
                f"Incorrect output length for "
                f"'{key}': {len(values)}"
            )

    return outputs


# =====================================================================
# Classification and calibration
# =====================================================================

def calculate_classification_metrics(
    labels,
    crossing_probabilities,
    threshold
):

    predictions = (
        crossing_probabilities
        >= threshold
    ).astype(np.int64)

    return {
        "samples": int(len(labels)),

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

        "f1": float(
            f1_score(
                labels,
                predictions,
                pos_label=1,
                zero_division=0
            )
        ),

        "roc_auc": float(
            roc_auc_score(
                labels,
                crossing_probabilities
            )
        ),

        "average_precision": float(
            average_precision_score(
                labels,
                crossing_probabilities
            )
        )
    }


def calculate_binary_ece(
    labels,
    probabilities,
    number_of_bins=15
):
    """
    Binary Expected Calibration Error.

    For each probability bin, compare:
        mean predicted crossing probability
        vs
        observed crossing frequency.
    """

    probabilities = np.clip(
        probabilities,
        0.0,
        1.0
    )

    bin_edges = np.linspace(
        0.0,
        1.0,
        number_of_bins + 1
    )

    bin_ids = np.digitize(
        probabilities,
        bin_edges[1:-1],
        right=True
    )

    ece = 0.0
    bin_rows = []

    total_samples = len(labels)

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
                probabilities[mask]
            )
        )

        observed_frequency = float(
            np.mean(
                labels[mask]
            )
        )

        calibration_gap = abs(
            mean_probability
            - observed_frequency
        )

        ece += (
            sample_count
            / total_samples
        ) * calibration_gap

        bin_rows.append({
            "bin_index": bin_index,
            "lower_bound":
                float(bin_edges[bin_index]),
            "upper_bound":
                float(bin_edges[bin_index + 1]),
            "samples": sample_count,
            "mean_probability":
                mean_probability,
            "observed_crossing_frequency":
                observed_frequency,
            "absolute_gap":
                float(calibration_gap)
        })

    return float(ece), bin_rows


def calculate_calibration_metrics(
    labels,
    crossing_probabilities
):

    clipped_probabilities = np.clip(
        crossing_probabilities,
        1e-7,
        1.0 - 1e-7
    )

    two_class_probabilities = np.column_stack(
        [
            1.0 - clipped_probabilities,
            clipped_probabilities
        ]
    )

    ece, calibration_bins = (
        calculate_binary_ece(
            labels=labels,
            probabilities=
                clipped_probabilities,
            number_of_bins=ECE_BINS
        )
    )

    metrics = {
        "brier_score": float(
            brier_score_loss(
                labels,
                clipped_probabilities
            )
        ),

        "negative_log_likelihood": float(
            log_loss(
                labels,
                two_class_probabilities,
                labels=[0, 1]
            )
        ),

        "expected_calibration_error":
            float(ece),

        "ece_bins": int(ECE_BINS)
    }

    return metrics, calibration_bins


# =====================================================================
# Error-detection evaluation
# =====================================================================

def calculate_margin_uncertainty(
    crossing_probabilities,
    threshold
):
    """
    A value near the decision threshold receives
    high uncertainty.

    A value near 0 or 1 receives lower uncertainty.
    """

    below_threshold = (
        crossing_probabilities < threshold
    )

    normalized_distance = np.empty_like(
        crossing_probabilities,
        dtype=np.float32
    )

    normalized_distance[
        below_threshold
    ] = (
        threshold
        - crossing_probabilities[
            below_threshold
        ]
    ) / max(
        threshold,
        1e-8
    )

    normalized_distance[
        ~below_threshold
    ] = (
        crossing_probabilities[
            ~below_threshold
        ]
        - threshold
    ) / max(
        1.0 - threshold,
        1e-8
    )

    return (
        1.0
        - np.clip(
            normalized_distance,
            0.0,
            1.0
        )
    ).astype(np.float32)


def safe_error_detection_metrics(
    error_labels,
    uncertainty_scores
):

    unique_error_states = np.unique(
        error_labels
    )

    if len(unique_error_states) < 2:

        return {
            "roc_auc": float("nan"),
            "average_precision": float("nan")
        }

    return {
        "roc_auc": float(
            roc_auc_score(
                error_labels,
                uncertainty_scores
            )
        ),

        "average_precision": float(
            average_precision_score(
                error_labels,
                uncertainty_scores
            )
        )
    }


def summarize_correct_and_incorrect(
    values,
    correct_mask
):

    correct_values = values[
        correct_mask
    ]

    incorrect_values = values[
        ~correct_mask
    ]

    def describe(array):

        if len(array) == 0:
            return {
                "samples": 0,
                "mean": float("nan"),
                "median": float("nan"),
                "standard_deviation":
                    float("nan")
            }

        return {
            "samples": int(len(array)),
            "mean": float(
                np.mean(array)
            ),
            "median": float(
                np.median(array)
            ),
            "standard_deviation": float(
                np.std(array)
            )
        }

    return {
        "correct": describe(
            correct_values
        ),

        "incorrect": describe(
            incorrect_values
        )
    }


# =====================================================================
# Risk-coverage
# =====================================================================

def calculate_risk_coverage(
    labels,
    predictions,
    uncertainty_scores,
    metric_name
):
    """
    Retain the least uncertain samples first.

    Risk:
        fraction of retained predictions that
        are incorrect.
    """

    order = np.argsort(
        uncertainty_scores
    )

    rows = []

    total_samples = len(labels)

    for requested_coverage in RISK_COVERAGES:

        retained_count = max(
            1,
            int(
                np.ceil(
                    requested_coverage
                    * total_samples
                )
            )
        )

        retained_indices = order[
            :retained_count
        ]

        retained_labels = labels[
            retained_indices
        ]

        retained_predictions = predictions[
            retained_indices
        ]

        error_rate = float(
            np.mean(
                retained_predictions
                != retained_labels
            )
        )

        rows.append({
            "uncertainty_metric":
                metric_name,

            "requested_coverage":
                float(requested_coverage),

            "actual_coverage":
                float(
                    retained_count
                    / total_samples
                ),

            "retained_samples":
                int(retained_count),

            "risk":
                error_rate,

            "selective_accuracy":
                float(
                    1.0 - error_rate
                ),

            "precision": float(
                precision_score(
                    retained_labels,
                    retained_predictions,
                    pos_label=1,
                    zero_division=0
                )
            ),

            "recall": float(
                recall_score(
                    retained_labels,
                    retained_predictions,
                    pos_label=1,
                    zero_division=0
                )
            ),

            "f1": float(
                f1_score(
                    retained_labels,
                    retained_predictions,
                    pos_label=1,
                    zero_division=0
                )
            )
        })

    return rows


# =====================================================================
# Occlusion summaries
# =====================================================================

def build_occlusion_summary(
    number_of_sequences
):

    if not BAYESIAN_DATA_PATH.exists():
        raise FileNotFoundError(
            f"Bayesian validation data not found: "
            f"{BAYESIAN_DATA_PATH}"
        )

    data = pd.read_csv(
        BAYESIAN_DATA_PATH
    )

    required_columns = {
        "sequence_index",
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
            "Every validation sequence must have "
            "30 occlusion records."
        )

    summary = counts.copy()

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
    prediction_dataframe
):

    maximum_occlusion = (
        prediction_dataframe[
            "maximum_occlusion"
        ].to_numpy()
    )

    subset_masks = {
        "all_validation_sequences":
            np.ones(
                len(prediction_dataframe),
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

        subset = prediction_dataframe.loc[
            mask
        ]

        errors = subset[
            "is_error"
        ].to_numpy(
            dtype=np.int64
        )

        entropy = subset[
            "normalized_predictive_entropy"
        ].to_numpy()

        error_metrics = (
            safe_error_detection_metrics(
                error_labels=errors,
                uncertainty_scores=entropy
            )
        )

        rows.append({
            "subset": subset_name,

            "samples": int(
                len(subset)
            ),

            "errors": int(
                errors.sum()
            ),

            "error_rate": float(
                errors.mean()
            ),

            "mean_confidence": float(
                subset[
                    "confidence"
                ].mean()
            ),

            "mean_normalized_entropy": float(
                subset[
                    "normalized_predictive_entropy"
                ].mean()
            ),

            "mean_mutual_information": float(
                subset[
                    "mutual_information"
                ].mean()
            ),

            "mean_crossing_variance": float(
                subset[
                    "crossing_probability_variance"
                ].mean()
            ),

            "entropy_error_detection_roc_auc":
                error_metrics["roc_auc"],

            "entropy_error_detection_ap":
                error_metrics[
                    "average_precision"
                ]
        })

    return rows


# =====================================================================
# JSON conversion
# =====================================================================

def clean_for_json(value):

    if isinstance(value, dict):

        return {
            str(key): clean_for_json(item)
            for key, item in value.items()
        }

    if isinstance(value, list):

        return [
            clean_for_json(item)
            for item in value
        ]

    if isinstance(value, np.ndarray):

        return clean_for_json(
            value.tolist()
        )

    if isinstance(
        value,
        (
            np.integer,
            np.floating
        )
    ):

        value = value.item()

    if isinstance(value, float):

        if not math.isfinite(value):
            return None

    return value


# =====================================================================
# Main
# =====================================================================

def main():

    print("=" * 78)
    print(
        "PHASE 6.2 - VALIDATION UNCERTAINTY EVALUATION"
    )
    print("=" * 78)

    X, y = load_validation_features()

    metadata = load_validation_metadata(
        number_of_sequences=len(X)
    )

    estimator = (
        MCDropoutUncertaintyEstimator(
            checkpoint_path=
                CHECKPOINT_PATH,

            number_of_samples=
                NUMBER_OF_MC_SAMPLES,

            random_seed=
                RANDOM_SEED
        )
    )

    print("Device             :", estimator.device)
    print("Validation shape   :", X.shape)
    print("MC samples         :", NUMBER_OF_MC_SAMPLES)
    print("Batch size         :", BATCH_SIZE)

    print()
    print("=" * 78)
    print("RUNNING MC DROPOUT")
    print("=" * 78)

    outputs = run_mc_inference(
        estimator=estimator,
        features=X
    )

    deterministic_crossing_probability = (
        outputs[
            "deterministic_probabilities"
        ][
            :,
            1
        ]
    )

    mc_crossing_probability = (
        outputs[
            "mean_probabilities"
        ][
            :,
            1
        ]
    )

    deterministic_threshold = (
        select_f1_threshold(
            labels=y,
            probabilities=
                deterministic_crossing_probability
        )
    )

    mc_threshold = select_f1_threshold(
        labels=y,
        probabilities=
            mc_crossing_probability
    )

    predictions = (
        mc_crossing_probability
        >= mc_threshold
    ).astype(np.int64)

    correct_mask = (
        predictions == y
    )

    error_labels = (
        ~correct_mask
    ).astype(np.int64)

    margin_uncertainty = (
        calculate_margin_uncertainty(
            crossing_probabilities=
                mc_crossing_probability,
            threshold=mc_threshold
        )
    )

    uncertainty_scores = {
        "one_minus_confidence":
            1.0 - outputs["confidence"],

        "normalized_predictive_entropy":
            outputs[
                "normalized_predictive_entropy"
            ],

        "mutual_information":
            outputs[
                "mutual_information"
            ],

        "crossing_probability_variance":
            outputs[
                "crossing_probability_variance"
            ],

        "variation_ratio":
            outputs[
                "variation_ratio"
            ],

        "decision_margin_uncertainty":
            margin_uncertainty
    }

    classification_metrics = (
        calculate_classification_metrics(
            labels=y,
            crossing_probabilities=
                mc_crossing_probability,
            threshold=mc_threshold
        )
    )

    calibration_metrics, calibration_rows = (
        calculate_calibration_metrics(
            labels=y,
            crossing_probabilities=
                mc_crossing_probability
        )
    )

    error_detection_rows = []
    correct_incorrect_summary = {}
    risk_coverage_rows = []

    for metric_name, scores in (
        uncertainty_scores.items()
    ):

        detection_metrics = (
            safe_error_detection_metrics(
                error_labels=
                    error_labels,
                uncertainty_scores=
                    scores
            )
        )

        error_detection_rows.append({
            "uncertainty_metric":
                metric_name,

            "errors": int(
                error_labels.sum()
            ),

            "correct_predictions": int(
                correct_mask.sum()
            ),

            "error_prevalence": float(
                error_labels.mean()
            ),

            "error_detection_roc_auc":
                detection_metrics[
                    "roc_auc"
                ],

            "error_detection_average_precision":
                detection_metrics[
                    "average_precision"
                ]
        })

        correct_incorrect_summary[
            metric_name
        ] = summarize_correct_and_incorrect(
            values=scores,
            correct_mask=correct_mask
        )

        risk_coverage_rows.extend(
            calculate_risk_coverage(
                labels=y,
                predictions=predictions,
                uncertainty_scores=scores,
                metric_name=metric_name
            )
        )

    # --------------------------------------------------------------
    # Prediction-level output
    # --------------------------------------------------------------

    prediction_dataframe = metadata.copy()

    prediction_dataframe.insert(
        0,
        "sequence_index",
        np.arange(
            len(X)
        )
    )

    prediction_dataframe["label_id"] = y

    prediction_dataframe[
        "deterministic_crossing_probability"
    ] = deterministic_crossing_probability

    prediction_dataframe[
        "mc_crossing_probability"
    ] = mc_crossing_probability

    prediction_dataframe[
        "prediction_id"
    ] = predictions

    prediction_dataframe[
        "prediction_name"
    ] = np.where(
        predictions == 1,
        "crossing",
        "not-crossing"
    )

    prediction_dataframe[
        "is_correct"
    ] = correct_mask

    prediction_dataframe[
        "is_error"
    ] = error_labels

    prediction_dataframe[
        "confidence"
    ] = outputs["confidence"]

    prediction_dataframe[
        "predictive_entropy"
    ] = outputs[
        "predictive_entropy"
    ]

    prediction_dataframe[
        "normalized_predictive_entropy"
    ] = outputs[
        "normalized_predictive_entropy"
    ]

    prediction_dataframe[
        "expected_entropy"
    ] = outputs[
        "expected_entropy"
    ]

    prediction_dataframe[
        "mutual_information"
    ] = outputs[
        "mutual_information"
    ]

    prediction_dataframe[
        "variation_ratio"
    ] = outputs[
        "variation_ratio"
    ]

    prediction_dataframe[
        "crossing_probability_variance"
    ] = outputs[
        "crossing_probability_variance"
    ]

    prediction_dataframe[
        "crossing_probability_std"
    ] = outputs[
        "crossing_probability_std"
    ]

    prediction_dataframe[
        "crossing_probability_min"
    ] = outputs[
        "crossing_probability_min"
    ]

    prediction_dataframe[
        "crossing_probability_max"
    ] = outputs[
        "crossing_probability_max"
    ]

    prediction_dataframe[
        "decision_margin_uncertainty"
    ] = margin_uncertainty

    occlusion_summary = (
        build_occlusion_summary(
            number_of_sequences=len(X)
        )
    )

    prediction_dataframe = (
        prediction_dataframe.merge(
            occlusion_summary,
            on="sequence_index",
            how="left",
            validate="one_to_one"
        )
    )

    occlusion_rows = (
        evaluate_occlusion_subsets(
            prediction_dataframe
        )
    )

    # --------------------------------------------------------------
    # Save
    # --------------------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    predictions_path = (
        OUTPUT_DIR
        / (
            "validation_uncertainty_"
            "predictions.csv"
        )
    )

    error_detection_path = (
        OUTPUT_DIR
        / (
            "validation_uncertainty_"
            "error_detection.csv"
        )
    )

    risk_coverage_path = (
        OUTPUT_DIR
        / "validation_risk_coverage.csv"
    )

    calibration_path = (
        OUTPUT_DIR
        / "validation_calibration_bins.csv"
    )

    occlusion_path = (
        OUTPUT_DIR
        / (
            "validation_uncertainty_"
            "by_occlusion.csv"
        )
    )

    summary_path = (
        OUTPUT_DIR
        / (
            "validation_uncertainty_"
            "summary.json"
        )
    )

    prediction_dataframe.to_csv(
        predictions_path,
        index=False
    )

    pd.DataFrame(
        error_detection_rows
    ).to_csv(
        error_detection_path,
        index=False
    )

    pd.DataFrame(
        risk_coverage_rows
    ).to_csv(
        risk_coverage_path,
        index=False
    )

    pd.DataFrame(
        calibration_rows
    ).to_csv(
        calibration_path,
        index=False
    )

    pd.DataFrame(
        occlusion_rows
    ).to_csv(
        occlusion_path,
        index=False
    )

    summary = {
        "checkpoint":
            str(CHECKPOINT_PATH),

        "validation_samples":
            int(len(X)),

        "mc_samples":
            int(NUMBER_OF_MC_SAMPLES),

        "deterministic_validation_threshold":
            float(deterministic_threshold),

        "mc_mean_validation_threshold":
            float(mc_threshold),

        "classification_metrics":
            classification_metrics,

        "calibration_metrics":
            calibration_metrics,

        "error_detection_metrics":
            error_detection_rows,

        "correct_vs_incorrect_uncertainty":
            correct_incorrect_summary,

        "output_files": {
            "predictions":
                str(predictions_path),

            "error_detection":
                str(error_detection_path),

            "risk_coverage":
                str(risk_coverage_path),

            "calibration_bins":
                str(calibration_path),

            "occlusion_summary":
                str(occlusion_path)
        },

        "test_split_used": False
    }

    with open(
        summary_path,
        "w",
        encoding="utf-8"
    ) as output_file:

        json.dump(
            clean_for_json(summary),
            output_file,
            indent=4
        )

    # --------------------------------------------------------------
    # Console summary
    # --------------------------------------------------------------

    print()
    print("=" * 78)
    print("VALIDATION CLASSIFICATION")
    print("=" * 78)

    print(
        "Deterministic threshold :",
        f"{deterministic_threshold:.6f}"
    )

    print(
        "MC-mean threshold       :",
        f"{mc_threshold:.6f}"
    )

    for name, value in (
        classification_metrics.items()
    ):

        if isinstance(value, float):
            print(
                f"{name:24}: {value:.6f}"
            )

    print()
    print("=" * 78)
    print("CALIBRATION")
    print("=" * 78)

    for name, value in (
        calibration_metrics.items()
    ):

        if isinstance(value, float):
            print(
                f"{name:30}: {value:.6f}"
            )

    print()
    print("=" * 78)
    print("ERROR-DETECTION PERFORMANCE")
    print("=" * 78)

    print(
        pd.DataFrame(
            error_detection_rows
        ).to_string(
            index=False
        )
    )

    print()
    print("=" * 78)
    print(
        "VALIDATION UNCERTAINTY EVALUATION COMPLETE"
    )
    print("=" * 78)

    print("Predictions      :", predictions_path)
    print("Error detection  :", error_detection_path)
    print("Risk coverage    :", risk_coverage_path)
    print("Calibration bins :", calibration_path)
    print("By occlusion     :", occlusion_path)
    print("Summary          :", summary_path)

    print()
    print(
        "The test split has not been used."
    )


if __name__ == "__main__":
    main()