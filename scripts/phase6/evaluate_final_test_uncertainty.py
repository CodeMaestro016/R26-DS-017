"""
Phase 6.4 - Final Test Uncertainty Evaluation.

Pipeline
--------
1. Load the frozen reliability-only Transformer.
2. Load validation-fitted temperature scaling.
3. Run 30 MC Dropout passes on validation data.
4. Apply temperature scaling to every stochastic prediction.
5. Select the final MC-mean decision threshold using validation only.
6. Run the frozen uncertainty system on the test split.
7. Evaluate:
   - Classification
   - Calibration before and after temperature scaling
   - Error detection
   - Risk-coverage
   - Occlusion-specific uncertainty
   - Validation-derived high-confidence errors

No model or calibration parameter is fitted using test data.
"""

from pathlib import Path
import json
import math

import numpy as np
import pandas as pd

from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score
)

from utils.uncertainty_estimator import (
    MCDropoutUncertaintyEstimator
)

from scripts.phase6.evaluate_validation_uncertainty import (
    calculate_calibration_metrics,
    calculate_classification_metrics,
    calculate_margin_uncertainty,
    calculate_risk_coverage,
    clean_for_json,
    safe_error_detection_metrics,
    select_f1_threshold
)


# =====================================================================
# Configuration
# =====================================================================

VALIDATION_FEATURE_PATH = Path(
    "datasets/processed/features/"
    "val_reliability_enriched_features.npz"
)

TEST_FEATURE_PATH = Path(
    "datasets/processed/features/"
    "test_reliability_enriched_features.npz"
)

TEST_METADATA_PATH = Path(
    "datasets/processed/metadata/test.csv"
)

TEST_BAYESIAN_PATH = Path(
    "datasets/processed/bayesian/"
    "test_bayesian.csv"
)

CHECKPOINT_PATH = Path(
    "outputs/phase5/"
    "reliability_only_transformer_best.pt"
)

CALIBRATION_PATH = Path(
    "outputs/phase6/"
    "temperature_calibration.json"
)

OUTPUT_DIR = Path(
    "outputs/phase6/final_test"
)

NUMBER_OF_MC_SAMPLES = 30
BATCH_SIZE = 64
RANDOM_SEED = 42

SEQUENCE_LENGTH = 30
INPUT_DIMENSION = 525
EPSILON = 1e-7


# =====================================================================
# Loading
# =====================================================================

def load_feature_split(
    path,
    split_name
):

    if not path.exists():

        raise FileNotFoundError(
            f"{split_name} feature file "
            f"not found: {path}"
        )

    with np.load(
        path,
        allow_pickle=True
    ) as data:

        if "X" not in data.files:
            raise KeyError(
                f"'X' key missing from {path}"
            )

        if "y" not in data.files:
            raise KeyError(
                f"'y' key missing from {path}"
            )

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
            f"{split_name}: expected a 3D feature "
            f"array, received {X.shape}."
        )

    if X.shape[1] != SEQUENCE_LENGTH:

        raise ValueError(
            f"{split_name}: expected sequence "
            f"length {SEQUENCE_LENGTH}, received "
            f"{X.shape[1]}."
        )

    if X.shape[2] != INPUT_DIMENSION:

        raise ValueError(
            f"{split_name}: expected feature "
            f"dimension {INPUT_DIMENSION}, received "
            f"{X.shape[2]}."
        )

    if len(X) != len(y):

        raise ValueError(
            f"{split_name}: feature and label "
            "counts do not match."
        )

    if not np.isfinite(X).all():

        raise ValueError(
            f"{split_name}: NaN or infinite "
            "values were detected."
        )

    unique_labels = set(
        np.unique(y).tolist()
    )

    if not unique_labels.issubset(
        {0, 1}
    ):

        raise ValueError(
            f"{split_name}: unsupported labels "
            f"were found: {unique_labels}"
        )

    return X, y


def load_temperature():

    if not CALIBRATION_PATH.exists():

        raise FileNotFoundError(
            "Temperature calibration file "
            f"not found: {CALIBRATION_PATH}"
        )

    with open(
        CALIBRATION_PATH,
        "r",
        encoding="utf-8"
    ) as input_file:

        calibration = json.load(
            input_file
        )

    if "temperature" not in calibration:

        raise KeyError(
            "'temperature' is missing from "
            f"{CALIBRATION_PATH}"
        )

    temperature = float(
        calibration["temperature"]
    )

    if (
        not math.isfinite(temperature)
        or temperature <= 0
    ):

        raise ValueError(
            f"Invalid temperature: {temperature}"
        )

    return temperature, calibration


# =====================================================================
# Temperature scaling
# =====================================================================

def stable_sigmoid(values):
    """
    Numerically stable sigmoid.
    """

    values = np.asarray(
        values,
        dtype=np.float64
    )

    result = np.empty_like(
        values
    )

    positive_mask = (
        values >= 0
    )

    result[positive_mask] = (
        1.0
        / (
            1.0
            + np.exp(
                -values[positive_mask]
            )
        )
    )

    negative_exponential = np.exp(
        values[~positive_mask]
    )

    result[~positive_mask] = (
        negative_exponential
        / (
            1.0
            + negative_exponential
        )
    )

    return result


def temperature_scale_probabilities(
    probabilities,
    temperature
):
    """
    Apply temperature scaling to binary softmax
    probabilities.

    For two classes:

        logit difference = log(p / (1 - p))

    Temperature-scaled probability:

        sigmoid(logit_difference / temperature)

    This is equivalent to dividing both original
    class logits by the temperature before softmax.
    """

    probabilities = np.asarray(
        probabilities,
        dtype=np.float64
    )

    if probabilities.shape[-1] != 2:

        raise ValueError(
            "Expected probabilities with final "
            "dimension 2."
        )

    crossing_probability = np.clip(
        probabilities[..., 1],
        EPSILON,
        1.0 - EPSILON
    )

    log_odds = (
        np.log(
            crossing_probability
        )
        - np.log1p(
            -crossing_probability
        )
    )

    calibrated_crossing_probability = (
        stable_sigmoid(
            log_odds / temperature
        )
    )

    calibrated = np.stack(
        [
            1.0
            - calibrated_crossing_probability,

            calibrated_crossing_probability
        ],
        axis=-1
    )

    return calibrated.astype(
        np.float32
    )


# =====================================================================
# Uncertainty calculation
# =====================================================================

def summarize_probability_samples(
    probability_samples
):
    """
    Parameters
    ----------
    probability_samples:
        Shape:
        (MC samples, batch, 2)
    """

    if probability_samples.ndim != 3:

        raise ValueError(
            "Probability samples must have shape "
            "(samples, batch, classes)."
        )

    mean_probabilities = np.mean(
        probability_samples,
        axis=0
    )

    confidence = np.max(
        mean_probabilities,
        axis=1
    )

    clipped_mean = np.clip(
        mean_probabilities,
        EPSILON,
        1.0
    )

    predictive_entropy = -np.sum(
        clipped_mean
        * np.log(
            clipped_mean
        ),
        axis=1
    )

    normalized_predictive_entropy = (
        predictive_entropy
        / np.log(2.0)
    )

    clipped_samples = np.clip(
        probability_samples,
        EPSILON,
        1.0
    )

    sample_entropies = -np.sum(
        clipped_samples
        * np.log(
            clipped_samples
        ),
        axis=2
    )

    expected_entropy = np.mean(
        sample_entropies,
        axis=0
    )

    mutual_information = (
        predictive_entropy
        - expected_entropy
    )

    mutual_information = np.clip(
        mutual_information,
        0.0,
        None
    )

    crossing_samples = (
        probability_samples[
            :,
            :,
            1
        ]
    )

    sample_class_predictions = np.argmax(
        probability_samples,
        axis=2
    )

    variation_ratios = []

    for batch_index in range(
        probability_samples.shape[1]
    ):

        class_counts = np.bincount(
            sample_class_predictions[
                :,
                batch_index
            ],
            minlength=2
        )

        modal_count = np.max(
            class_counts
        )

        variation_ratios.append(
            1.0
            - (
                modal_count
                / probability_samples.shape[0]
            )
        )

    return {
        "mean_probabilities":
            mean_probabilities.astype(
                np.float32
            ),

        "confidence":
            confidence.astype(
                np.float32
            ),

        "predictive_entropy":
            predictive_entropy.astype(
                np.float32
            ),

        "normalized_predictive_entropy":
            normalized_predictive_entropy.astype(
                np.float32
            ),

        "expected_entropy":
            expected_entropy.astype(
                np.float32
            ),

        "mutual_information":
            mutual_information.astype(
                np.float32
            ),

        "crossing_probability_variance":
            np.var(
                crossing_samples,
                axis=0
            ).astype(
                np.float32
            ),

        "crossing_probability_std":
            np.std(
                crossing_samples,
                axis=0
            ).astype(
                np.float32
            ),

        "crossing_probability_min":
            np.min(
                crossing_samples,
                axis=0
            ).astype(
                np.float32
            ),

        "crossing_probability_max":
            np.max(
                crossing_samples,
                axis=0
            ).astype(
                np.float32
            ),

        "variation_ratio":
            np.asarray(
                variation_ratios,
                dtype=np.float32
            )
    }


# =====================================================================
# MC inference
# =====================================================================

def run_calibrated_mc_inference(
    estimator,
    features,
    temperature,
    split_name,
    seed_offset
):

    outputs = {
        "uncalibrated_mean_probabilities": [],
        "calibrated_mean_probabilities": [],
        "deterministic_probabilities": [],
        "calibrated_deterministic_probabilities": [],
        "confidence": [],
        "predictive_entropy": [],
        "normalized_predictive_entropy": [],
        "expected_entropy": [],
        "mutual_information": [],
        "crossing_probability_variance": [],
        "crossing_probability_std": [],
        "crossing_probability_min": [],
        "crossing_probability_max": [],
        "variation_ratio": []
    }

    number_of_batches = int(
        np.ceil(
            len(features)
            / BATCH_SIZE
        )
    )

    activated_stochastic_modules = None

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
            f"{split_name} MC batch "
            f"{batch_number:02d}/"
            f"{number_of_batches:02d} | "
            f"Sequences {start_index}-"
            f"{end_index - 1}"
        )

        estimator.random_seed = (
            RANDOM_SEED
            + seed_offset
            + batch_number
        )

        result = estimator.estimate_batch(
            features=features[
                start_index:end_index
            ],
            number_of_samples=
                NUMBER_OF_MC_SAMPLES,
            return_samples=True
        )

        if activated_stochastic_modules is None:

            activated_stochastic_modules = int(
                result[
                    "activated_stochastic_modules"
                ]
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

        calibrated_summary = (
            summarize_probability_samples(
                calibrated_samples
            )
        )

        calibrated_deterministic = (
            temperature_scale_probabilities(
                probabilities=result[
                    "deterministic_probabilities"
                ],
                temperature=temperature
            )
        )

        outputs[
            "uncalibrated_mean_probabilities"
        ].append(
            result["mean_probabilities"]
        )

        outputs[
            "calibrated_mean_probabilities"
        ].append(
            calibrated_summary[
                "mean_probabilities"
            ]
        )

        outputs[
            "deterministic_probabilities"
        ].append(
            result[
                "deterministic_probabilities"
            ]
        )

        outputs[
            "calibrated_deterministic_probabilities"
        ].append(
            calibrated_deterministic
        )

        for key in [
            "confidence",
            "predictive_entropy",
            "normalized_predictive_entropy",
            "expected_entropy",
            "mutual_information",
            "crossing_probability_variance",
            "crossing_probability_std",
            "crossing_probability_min",
            "crossing_probability_max",
            "variation_ratio"
        ]:

            outputs[key].append(
                calibrated_summary[key]
            )

    for key in outputs:

        outputs[key] = np.concatenate(
            outputs[key],
            axis=0
        )

        if len(outputs[key]) != len(features):

            raise ValueError(
                f"{split_name}: incorrect output "
                f"length for '{key}'."
            )

    outputs[
        "activated_stochastic_modules"
    ] = activated_stochastic_modules

    return outputs


# =====================================================================
# Occlusion summary
# =====================================================================

def build_test_occlusion_summary(
    number_of_sequences
):

    if not TEST_BAYESIAN_PATH.exists():

        raise FileNotFoundError(
            "Test Bayesian file not found: "
            f"{TEST_BAYESIAN_PATH}"
        )

    data = pd.read_csv(
        TEST_BAYESIAN_PATH
    )

    required_columns = {
        "sequence_index",
        "occlusion"
    }

    if not required_columns.issubset(
        data.columns
    ):

        raise ValueError(
            "Required test occlusion columns "
            "are missing."
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
            "Invalid occlusion states: "
            f"{invalid_states}"
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
        total_frames.to_numpy()
        == SEQUENCE_LENGTH
    ):

        raise ValueError(
            "Every test sequence must contain "
            f"{SEQUENCE_LENGTH} occlusion records."
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
        summary[
            "medium_frame_count"
        ] > 0,
        "maximum_occlusion"
    ] = "medium"

    summary.loc[
        summary[
            "high_frame_count"
        ] > 0,
        "maximum_occlusion"
    ] = "high"

    return summary.reset_index()


# =====================================================================
# Subset evaluation
# =====================================================================

def calculate_safe_subset_metrics(
    labels,
    probabilities,
    threshold
):

    predictions = (
        probabilities >= threshold
    ).astype(np.int64)

    metrics = {
        "samples": int(len(labels)),

        "not_crossing_samples": int(
            np.sum(labels == 0)
        ),

        "crossing_samples": int(
            np.sum(labels == 1)
        ),

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
                zero_division=0
            )
        ),

        "recall": float(
            recall_score(
                labels,
                predictions,
                zero_division=0
            )
        ),

        "f1": float(
            f1_score(
                labels,
                predictions,
                zero_division=0
            )
        )
    }

    if len(np.unique(labels)) == 2:

        metrics["roc_auc"] = float(
            roc_auc_score(
                labels,
                probabilities
            )
        )

        metrics[
            "average_precision"
        ] = float(
            average_precision_score(
                labels,
                probabilities
            )
        )

    else:

        metrics["roc_auc"] = float("nan")

        metrics[
            "average_precision"
        ] = float("nan")

    return metrics


def evaluate_occlusion_subsets(
    prediction_dataframe,
    decision_threshold
):

    maximum_occlusion = (
        prediction_dataframe[
            "maximum_occlusion"
        ].to_numpy()
    )

    subset_masks = {
        "all_test_sequences":
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

        labels = subset[
            "label_id"
        ].to_numpy(
            dtype=np.int64
        )

        probabilities = subset[
            "calibrated_mc_crossing_probability"
        ].to_numpy()

        errors = subset[
            "is_error"
        ].to_numpy(
            dtype=np.int64
        )

        variance = subset[
            "crossing_probability_variance"
        ].to_numpy()

        entropy = subset[
            "normalized_predictive_entropy"
        ].to_numpy()

        classification = (
            calculate_safe_subset_metrics(
                labels=labels,
                probabilities=probabilities,
                threshold=decision_threshold
            )
        )

        variance_detection = (
            safe_error_detection_metrics(
                error_labels=errors,
                uncertainty_scores=variance
            )
        )

        entropy_detection = (
            safe_error_detection_metrics(
                error_labels=errors,
                uncertainty_scores=entropy
            )
        )

        rows.append({
            "subset": subset_name,

            **classification,

            "errors": int(
                errors.sum()
            ),

            "error_rate": float(
                errors.mean()
            ),

            "mean_confidence": float(
                subset["confidence"].mean()
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

            "variance_error_detection_roc_auc":
                variance_detection[
                    "roc_auc"
                ],

            "variance_error_detection_ap":
                variance_detection[
                    "average_precision"
                ],

            "entropy_error_detection_roc_auc":
                entropy_detection[
                    "roc_auc"
                ],

            "entropy_error_detection_ap":
                entropy_detection[
                    "average_precision"
                ]
        })

    return rows


# =====================================================================
# Main
# =====================================================================

def main():

    print("=" * 78)
    print(
        "PHASE 6.4 - FINAL TEST "
        "UNCERTAINTY EVALUATION"
    )
    print("=" * 78)

    validation_X, validation_y = (
        load_feature_split(
            VALIDATION_FEATURE_PATH,
            "Validation"
        )
    )

    test_X, test_y = load_feature_split(
        TEST_FEATURE_PATH,
        "Test"
    )

    if not TEST_METADATA_PATH.exists():

        raise FileNotFoundError(
            "Test metadata file not found: "
            f"{TEST_METADATA_PATH}"
        )

    test_metadata = pd.read_csv(
        TEST_METADATA_PATH
    ).reset_index(drop=True)

    if len(test_metadata) != len(test_X):

        raise ValueError(
            "Test metadata and feature counts "
            "do not match."
        )

    temperature, calibration_config = (
        load_temperature()
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
    print("Temperature        :", temperature)
    print("MC samples         :", NUMBER_OF_MC_SAMPLES)
    print("Validation shape   :", validation_X.shape)
    print("Test shape         :", test_X.shape)

    print()
    print("=" * 78)
    print(
        "CALIBRATED VALIDATION MC INFERENCE"
    )
    print("=" * 78)

    validation_outputs = (
        run_calibrated_mc_inference(
            estimator=estimator,
            features=validation_X,
            temperature=temperature,
            split_name="Validation",
            seed_offset=0
        )
    )

    validation_crossing_probability = (
        validation_outputs[
            "calibrated_mean_probabilities"
        ][
            :,
            1
        ]
    )

    final_decision_threshold = (
        select_f1_threshold(
            labels=validation_y,
            probabilities=
                validation_crossing_probability
        )
    )

    validation_confidence_cutoff = float(
        np.quantile(
            validation_outputs[
                "confidence"
            ],
            0.90
        )
    )

    print()
    print(
        "Validation-derived MC threshold:",
        f"{final_decision_threshold:.6f}"
    )

    print(
        "Validation top-decile confidence "
        "cutoff:",
        f"{validation_confidence_cutoff:.6f}"
    )

    print()
    print("=" * 78)
    print("FINAL TEST MC INFERENCE")
    print("=" * 78)

    test_outputs = (
        run_calibrated_mc_inference(
            estimator=estimator,
            features=test_X,
            temperature=temperature,
            split_name="Test",
            seed_offset=1000
        )
    )

    uncalibrated_test_crossing = (
        test_outputs[
            "uncalibrated_mean_probabilities"
        ][
            :,
            1
        ]
    )

    calibrated_test_crossing = (
        test_outputs[
            "calibrated_mean_probabilities"
        ][
            :,
            1
        ]
    )

    test_predictions = (
        calibrated_test_crossing
        >= final_decision_threshold
    ).astype(
        np.int64
    )

    correct_mask = (
        test_predictions == test_y
    )

    error_labels = (
        ~correct_mask
    ).astype(
        np.int64
    )

    margin_uncertainty = (
        calculate_margin_uncertainty(
            crossing_probabilities=
                calibrated_test_crossing,

            threshold=
                final_decision_threshold
        )
    )

    classification_metrics = (
        calculate_classification_metrics(
            labels=test_y,

            crossing_probabilities=
                calibrated_test_crossing,

            threshold=
                final_decision_threshold
        )
    )

    (
        before_calibration_metrics,
        before_calibration_bins
    ) = calculate_calibration_metrics(
        labels=test_y,
        crossing_probabilities=
            uncalibrated_test_crossing
    )

    (
        after_calibration_metrics,
        after_calibration_bins
    ) = calculate_calibration_metrics(
        labels=test_y,
        crossing_probabilities=
            calibrated_test_crossing
    )

    uncertainty_scores = {
        "one_minus_confidence":
            1.0
            - test_outputs[
                "confidence"
            ],

        "normalized_predictive_entropy":
            test_outputs[
                "normalized_predictive_entropy"
            ],

        "mutual_information":
            test_outputs[
                "mutual_information"
            ],

        "crossing_probability_variance":
            test_outputs[
                "crossing_probability_variance"
            ],

        "variation_ratio":
            test_outputs[
                "variation_ratio"
            ],

        "decision_margin_uncertainty":
            margin_uncertainty
    }

    error_detection_rows = []
    risk_coverage_rows = []

    for metric_name, scores in (
        uncertainty_scores.items()
    ):

        detection = (
            safe_error_detection_metrics(
                error_labels=error_labels,
                uncertainty_scores=scores
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
                detection[
                    "roc_auc"
                ],

            "error_detection_average_precision":
                detection[
                    "average_precision"
                ]
        })

        risk_coverage_rows.extend(
            calculate_risk_coverage(
                labels=test_y,
                predictions=test_predictions,
                uncertainty_scores=scores,
                metric_name=metric_name
            )
        )

    # --------------------------------------------------------------
    # Prediction-level output
    # --------------------------------------------------------------

    prediction_dataframe = (
        test_metadata.copy()
    )

    prediction_dataframe.insert(
        0,
        "sequence_index",
        np.arange(
            len(test_X)
        )
    )

    prediction_dataframe[
        "label_id"
    ] = test_y

    prediction_dataframe[
        "uncalibrated_mc_crossing_probability"
    ] = uncalibrated_test_crossing

    prediction_dataframe[
        "calibrated_mc_crossing_probability"
    ] = calibrated_test_crossing

    prediction_dataframe[
        "prediction_id"
    ] = test_predictions

    prediction_dataframe[
        "prediction_name"
    ] = np.where(
        test_predictions == 1,
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
    ] = test_outputs[
        "confidence"
    ]

    prediction_dataframe[
        "predictive_entropy"
    ] = test_outputs[
        "predictive_entropy"
    ]

    prediction_dataframe[
        "normalized_predictive_entropy"
    ] = test_outputs[
        "normalized_predictive_entropy"
    ]

    prediction_dataframe[
        "expected_entropy"
    ] = test_outputs[
        "expected_entropy"
    ]

    prediction_dataframe[
        "mutual_information"
    ] = test_outputs[
        "mutual_information"
    ]

    prediction_dataframe[
        "crossing_probability_variance"
    ] = test_outputs[
        "crossing_probability_variance"
    ]

    prediction_dataframe[
        "crossing_probability_std"
    ] = test_outputs[
        "crossing_probability_std"
    ]

    prediction_dataframe[
        "crossing_probability_min"
    ] = test_outputs[
        "crossing_probability_min"
    ]

    prediction_dataframe[
        "crossing_probability_max"
    ] = test_outputs[
        "crossing_probability_max"
    ]

    prediction_dataframe[
        "variation_ratio"
    ] = test_outputs[
        "variation_ratio"
    ]

    prediction_dataframe[
        "decision_margin_uncertainty"
    ] = margin_uncertainty

    prediction_dataframe[
        "high_confidence_by_validation_cutoff"
    ] = (
        prediction_dataframe[
            "confidence"
        ]
        >= validation_confidence_cutoff
    )

    prediction_dataframe[
        "high_confidence_error"
    ] = (
        prediction_dataframe[
            "high_confidence_by_validation_cutoff"
        ]
        & prediction_dataframe[
            "is_error"
        ].astype(bool)
    )

    occlusion_summary = (
        build_test_occlusion_summary(
            number_of_sequences=
                len(test_X)
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
            prediction_dataframe=
                prediction_dataframe,

            decision_threshold=
                final_decision_threshold
        )
    )

    high_confidence_error_count = int(
        prediction_dataframe[
            "high_confidence_error"
        ].sum()
    )

    total_error_count = int(
        error_labels.sum()
    )

    high_confidence_error_fraction = (
        high_confidence_error_count
        / total_error_count
        if total_error_count > 0
        else float("nan")
    )

    # --------------------------------------------------------------
    # Save outputs
    # --------------------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    predictions_path = (
        OUTPUT_DIR
        / "test_uncertainty_predictions.csv"
    )

    error_detection_path = (
        OUTPUT_DIR
        / "test_uncertainty_error_detection.csv"
    )

    risk_coverage_path = (
        OUTPUT_DIR
        / "test_risk_coverage.csv"
    )

    before_bins_path = (
        OUTPUT_DIR
        / "test_calibration_bins_before.csv"
    )

    after_bins_path = (
        OUTPUT_DIR
        / "test_calibration_bins_after.csv"
    )

    occlusion_path = (
        OUTPUT_DIR
        / "test_uncertainty_by_occlusion.csv"
    )

    deployment_config_path = (
        OUTPUT_DIR
        / "uncertainty_deployment_config.json"
    )

    summary_path = (
        OUTPUT_DIR
        / "final_uncertainty_summary.json"
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
        before_calibration_bins
    ).to_csv(
        before_bins_path,
        index=False
    )

    pd.DataFrame(
        after_calibration_bins
    ).to_csv(
        after_bins_path,
        index=False
    )

    pd.DataFrame(
        occlusion_rows
    ).to_csv(
        occlusion_path,
        index=False
    )

    deployment_config = {
        "checkpoint":
            str(CHECKPOINT_PATH),

        "input_dimension":
            INPUT_DIMENSION,

        "sequence_length":
            SEQUENCE_LENGTH,

        "temperature":
            float(temperature),

        "temperature_source":
            str(CALIBRATION_PATH),

        "mc_samples":
            NUMBER_OF_MC_SAMPLES,

        "decision_threshold":
            float(
                final_decision_threshold
            ),

        "decision_threshold_source":
            (
                "validation calibrated "
                "MC-mean F1 optimization"
            ),

        "primary_uncertainty_metric":
            (
                "crossing_probability_variance"
            ),

        "supporting_uncertainty_metrics": [
            "mutual_information",
            "normalized_predictive_entropy"
        ],

        "validation_high_confidence_cutoff":
            float(
                validation_confidence_cutoff
            ),

        "test_data_used_for_tuning":
            False
    }

    with open(
        deployment_config_path,
        "w",
        encoding="utf-8"
    ) as output_file:

        json.dump(
            deployment_config,
            output_file,
            indent=4
        )

    summary = {
        "checkpoint":
            str(CHECKPOINT_PATH),

        "test_samples":
            int(len(test_y)),

        "mc_samples":
            NUMBER_OF_MC_SAMPLES,

        "activated_stochastic_modules":
            test_outputs[
                "activated_stochastic_modules"
            ],

        "temperature":
            float(temperature),

        "validation_derived_threshold":
            float(
                final_decision_threshold
            ),

        "classification_metrics":
            classification_metrics,

        "calibration_before_temperature":
            before_calibration_metrics,

        "calibration_after_temperature":
            after_calibration_metrics,

        "error_detection_metrics":
            error_detection_rows,

        "high_confidence_analysis": {
            "validation_confidence_cutoff":
                float(
                    validation_confidence_cutoff
                ),

            "test_errors":
                total_error_count,

            "test_high_confidence_errors":
                high_confidence_error_count,

            "fraction_of_errors_high_confidence":
                float(
                    high_confidence_error_fraction
                )
        },

        "occlusion_results":
            occlusion_rows,

        "output_files": {
            "predictions":
                str(predictions_path),

            "error_detection":
                str(error_detection_path),

            "risk_coverage":
                str(risk_coverage_path),

            "calibration_before":
                str(before_bins_path),

            "calibration_after":
                str(after_bins_path),

            "occlusion":
                str(occlusion_path),

            "deployment_config":
                str(deployment_config_path)
        },

        "test_data_used_for_tuning":
            False
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
    print("FINAL TEST CLASSIFICATION")
    print("=" * 78)

    print(
        "Final validation-derived threshold:",
        f"{final_decision_threshold:.6f}"
    )

    for name, value in (
        classification_metrics.items()
    ):

        if isinstance(value, float):

            print(
                f"{name:24}: "
                f"{value:.6f}"
            )

    print()
    print("=" * 78)
    print("TEST CALIBRATION")
    print("=" * 78)

    print("Before temperature scaling:")

    for name, value in (
        before_calibration_metrics.items()
    ):

        if isinstance(value, float):

            print(
                f"  {name:30}: "
                f"{value:.6f}"
            )

    print()
    print("After temperature scaling:")

    for name, value in (
        after_calibration_metrics.items()
    ):

        if isinstance(value, float):

            print(
                f"  {name:30}: "
                f"{value:.6f}"
            )

    print()
    print("=" * 78)
    print("TEST ERROR-DETECTION PERFORMANCE")
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
    print("HIGH-CONFIDENCE ERROR ANALYSIS")
    print("=" * 78)

    print(
        "Validation confidence cutoff:",
        f"{validation_confidence_cutoff:.6f}"
    )

    print(
        "Total test errors:",
        total_error_count
    )

    print(
        "High-confidence test errors:",
        high_confidence_error_count
    )

    print(
        "Fraction of errors high-confidence:",
        f"{high_confidence_error_fraction:.6f}"
    )

    print()
    print("=" * 78)
    print(
        "FINAL TEST UNCERTAINTY "
        "EVALUATION COMPLETE"
    )
    print("=" * 78)

    print("Predictions      :", predictions_path)
    print("Error detection  :", error_detection_path)
    print("Risk coverage    :", risk_coverage_path)
    print("Calibration      :", after_bins_path)
    print("By occlusion     :", occlusion_path)
    print("Deployment config:", deployment_config_path)
    print("Summary          :", summary_path)

    print()
    print(
        "The frozen uncertainty system has now "
        "been evaluated on the test split."
    )

    print(
        "Do not tune the model, temperature, "
        "threshold, or uncertainty method using "
        "these test results."
    )


if __name__ == "__main__":
    main()