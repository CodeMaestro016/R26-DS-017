"""
Demo 1B: PIE held-out batch runtime validation.

This script:
1. Selects a fixed, balanced subset from the untouched PIE test split.
2. Selection uses only ground-truth class and occlusion category, never model
   correctness, confidence, or probability.
3. Reconstructs every selected (30, 525) sequence from original PIE frames.
4. Compares runtime-generated features with the saved test features.
5. Runs the frozen calibrated Transformer with MC Dropout.
6. Saves per-sequence, classification, compatibility, and occlusion summaries.

Default:
    10 crossing + 10 not-crossing sequences.

Quick check:
    python -m scripts.demo.validate_pie_runtime_batch --per-class 3

Full default:
    python -m scripts.demo.validate_pie_runtime_batch
"""

from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from utils.annotation_loader import AnnotationLoader
from utils.image_loader import ImageLoader
from utils.runtime_feature_extractor import RuntimeFeatureExtractor
from utils.runtime_intent_predictor import RuntimeIntentPredictor
from utils.sequence_buffer import FeatureSequenceBuffer


FRAME_ROOT = Path("datasets/processed/frames")
ANNOTATION_PATH = Path("datasets/processed/metadata/annotations.csv")
TEST_METADATA_PATH = Path("datasets/processed/metadata/test.csv")
TEST_FEATURE_PATH = Path(
    "datasets/processed/features/test_reliability_enriched_features.npz"
)
FINAL_PREDICTION_PATH = Path(
    "outputs/phase6/final_test/test_uncertainty_predictions.csv"
)

DEFAULT_OUTPUT_DIR = Path("outputs/demo/pie_batch")
DEFAULT_DATASET_SET = "set01"

SEQUENCE_LENGTH = 30
FEATURE_DIMENSION = 525

CLASS_NAMES = {
    0: "not-crossing",
    1: "crossing",
}

OCCLUSION_ORDER = {
    "low": 0,
    "medium": 1,
    "high": 2,
}


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--per-class",
        type=int,
        default=10,
        help="Number of sequences selected for each class. Default: 10.",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Fixed sequence-selection seed.",
    )

    parser.add_argument(
        "--dataset-set",
        type=str,
        default=DEFAULT_DATASET_SET,
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(DEFAULT_OUTPUT_DIR),
    )

    parser.add_argument(
        "--bayesian-model",
        type=str,
        default=None,
    )

    parser.add_argument(
        "--sequence-indices",
        type=int,
        nargs="+",
        default=None,
        help=(
            "Optional explicit sequence indices. When supplied, automatic "
            "balanced selection is skipped."
        ),
    )

    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Continue processing if a selected sequence fails.",
    )

    return parser.parse_args()


def get_first_available(row: pd.Series, names: list[str]) -> Any:
    for name in names:
        if name in row.index:
            return row[name]

    raise KeyError(
        f"None of the expected columns were found: {names}"
    )


def parse_frames(value: Any) -> list[int]:
    if isinstance(value, str):
        normalized = (
            value.replace(",", "|")
            .replace(" ", "|")
            .replace("[", "")
            .replace("]", "")
            .replace("'", "")
            .replace('"', "")
        )

        return [
            int(item)
            for item in normalized.split("|")
            if item.strip() != ""
        ]

    if isinstance(value, (list, tuple, np.ndarray)):
        return [int(item) for item in value]

    raise TypeError(f"Unsupported frames value: {value!r}")


def normalize_occlusion(value: Any) -> str:
    return RuntimeFeatureExtractor.normalize_occlusion_label(value)


def maximum_occlusion(states: list[str]) -> str:
    if not states:
        raise ValueError("Cannot determine maximum occlusion from an empty list.")

    return max(
        states,
        key=lambda state: OCCLUSION_ORDER[state],
    )


def build_test_index(
    test_metadata: pd.DataFrame,
    test_labels: np.ndarray,
    annotation_loader: AnnotationLoader,
) -> pd.DataFrame:
    """
    Build one row per test sequence.

    Preferred source for maximum_occlusion is the already generated final-test
    prediction CSV. Only sequence index and occlusion metadata are read from it.
    Model correctness/confidence is not used for selection.

    If that file is unavailable, maximum occlusion is reconstructed from PIE
    annotations.
    """
    index_frame = pd.DataFrame(
        {
            "sequence_index": np.arange(
                len(test_metadata),
                dtype=np.int64,
            ),
            "label_id": test_labels.astype(
                np.int64,
                copy=False,
            ),
        }
    )

    if FINAL_PREDICTION_PATH.exists():
        prior = pd.read_csv(FINAL_PREDICTION_PATH)

        required = {
            "sequence_index",
            "maximum_occlusion",
        }

        if required.issubset(prior.columns):
            occlusion_frame = prior[
                [
                    "sequence_index",
                    "maximum_occlusion",
                ]
            ].copy()

            occlusion_frame["sequence_index"] = (
                occlusion_frame["sequence_index"]
                .astype(np.int64)
            )

            occlusion_frame["maximum_occlusion"] = (
                occlusion_frame["maximum_occlusion"]
                .astype(str)
                .str.strip()
                .str.lower()
            )

            merged = index_frame.merge(
                occlusion_frame,
                on="sequence_index",
                how="left",
                validate="one_to_one",
            )

            valid_states = set(
                merged["maximum_occlusion"]
                .dropna()
                .unique()
            )

            if (
                not merged["maximum_occlusion"].isna().any()
                and valid_states.issubset(
                    set(OCCLUSION_ORDER)
                )
            ):
                return merged

    print(
        "Occlusion index not available from final-test CSV; "
        "reconstructing it from original annotations..."
    )

    occlusion_rows = []

    for sequence_index, row in test_metadata.iterrows():
        video = str(
            get_first_available(
                row,
                ["video", "video_id"],
            )
        )

        pedestrian_id = str(
            get_first_available(
                row,
                ["pedestrian_id", "id", "pedestrian"],
            )
        )

        frames = parse_frames(
            get_first_available(
                row,
                [
                    "frames",
                    "frame_numbers",
                    "sequence_frames",
                ],
            )
        )

        states = []

        for frame_number in frames:
            annotation = annotation_loader.get_annotation(
                video=video,
                frame=int(frame_number),
                pedestrian_id=pedestrian_id,
            )

            if annotation is None:
                raise RuntimeError(
                    "Missing annotation while building the test index: "
                    f"{video}, frame {frame_number}, pedestrian "
                    f"{pedestrian_id}."
                )

            states.append(
                normalize_occlusion(
                    annotation["occlusion"]
                )
            )

        occlusion_rows.append(
            {
                "sequence_index": int(sequence_index),
                "maximum_occlusion": maximum_occlusion(states),
            }
        )

    return index_frame.merge(
        pd.DataFrame(occlusion_rows),
        on="sequence_index",
        how="left",
        validate="one_to_one",
    )


def allocate_occlusion_targets(
    total: int,
) -> dict[str, int]:
    """
    Approximate 40% low, 20% medium, 40% high.

    For total=10:
        low=4, medium=2, high=4
    """
    if total <= 0:
        raise ValueError("total must be positive.")

    medium = max(
        1,
        int(round(total * 0.20)),
    )

    remaining = total - medium
    low = remaining // 2
    high = remaining - low

    return {
        "low": low,
        "medium": medium,
        "high": high,
    }


def select_balanced_sequences(
    test_index: pd.DataFrame,
    per_class: int,
    seed: int,
) -> pd.DataFrame:
    if per_class <= 0:
        raise ValueError("--per-class must be positive.")

    rng = np.random.default_rng(seed)
    selected_parts = []

    targets = allocate_occlusion_targets(
        per_class
    )

    for label_id in (0, 1):
        class_rows = test_index[
            test_index["label_id"] == label_id
        ].copy()

        if len(class_rows) < per_class:
            raise ValueError(
                f"Class {label_id} contains only "
                f"{len(class_rows)} sequences; requested {per_class}."
            )

        selected_indices: list[int] = []

        for occlusion_state in (
            "low",
            "medium",
            "high",
        ):
            candidates = class_rows[
                class_rows["maximum_occlusion"]
                == occlusion_state
            ]["sequence_index"].to_numpy(
                dtype=np.int64
            )

            requested = targets[
                occlusion_state
            ]

            take = min(
                requested,
                len(candidates),
            )

            if take > 0:
                sampled = rng.choice(
                    candidates,
                    size=take,
                    replace=False,
                )

                selected_indices.extend(
                    int(value)
                    for value in sampled
                )

        remaining_needed = (
            per_class - len(selected_indices)
        )

        if remaining_needed > 0:
            remaining_candidates = class_rows[
                ~class_rows["sequence_index"].isin(
                    selected_indices
                )
            ]["sequence_index"].to_numpy(
                dtype=np.int64
            )

            if len(remaining_candidates) < remaining_needed:
                raise RuntimeError(
                    "Not enough remaining candidates to complete "
                    f"class {label_id} selection."
                )

            sampled = rng.choice(
                remaining_candidates,
                size=remaining_needed,
                replace=False,
            )

            selected_indices.extend(
                int(value)
                for value in sampled
            )

        selected_class = test_index[
            test_index["sequence_index"].isin(
                selected_indices
            )
        ].copy()

        selected_parts.append(
            selected_class
        )

    selected = pd.concat(
        selected_parts,
        ignore_index=True,
    )

    # Fixed random order so the two classes are not processed in blocks.
    order = rng.permutation(
        len(selected)
    )

    selected = (
        selected.iloc[order]
        .reset_index(drop=True)
    )

    selected.insert(
        0,
        "selection_order",
        np.arange(
            1,
            len(selected) + 1,
            dtype=np.int64,
        ),
    )

    return selected


def select_explicit_sequences(
    test_index: pd.DataFrame,
    sequence_indices: list[int],
) -> pd.DataFrame:
    unique_indices = list(
        dict.fromkeys(
            int(value)
            for value in sequence_indices
        )
    )

    invalid = [
        value
        for value in unique_indices
        if value not in set(
            test_index["sequence_index"]
        )
    ]

    if invalid:
        raise IndexError(
            f"Invalid sequence indices: {invalid}"
        )

    selected = test_index[
        test_index["sequence_index"].isin(
            unique_indices
        )
    ].copy()

    order_map = {
        value: order
        for order, value in enumerate(
            unique_indices,
            start=1,
        )
    }

    selected["selection_order"] = (
        selected["sequence_index"]
        .map(order_map)
        .astype(np.int64)
    )

    return selected.sort_values(
        "selection_order"
    ).reset_index(drop=True)


def reconstruct_sequence(
    *,
    sequence_index: int,
    metadata_row: pd.Series,
    image_loader: ImageLoader,
    annotation_loader: AnnotationLoader,
    runtime_extractor: RuntimeFeatureExtractor,
    dataset_set: str,
) -> tuple[np.ndarray, dict[str, Any]]:
    video = str(
        get_first_available(
            metadata_row,
            ["video", "video_id"],
        )
    )

    pedestrian_id = str(
        get_first_available(
            metadata_row,
            ["pedestrian_id", "id", "pedestrian"],
        )
    )

    frames = parse_frames(
        get_first_available(
            metadata_row,
            [
                "frames",
                "frame_numbers",
                "sequence_frames",
            ],
        )
    )

    if len(frames) != SEQUENCE_LENGTH:
        raise ValueError(
            f"Sequence {sequence_index}: expected "
            f"{SEQUENCE_LENGTH} frames, found {len(frames)}."
        )

    runtime_extractor.reset_track(
        pedestrian_id
    )

    vectors = []
    occlusion_states = []
    motion_states = []

    for frame_number in frames:
        image = image_loader.load_frame(
            video=video,
            frame_number=int(frame_number),
            dataset_set=dataset_set,
        )

        annotation = annotation_loader.get_annotation(
            video=video,
            frame=int(frame_number),
            pedestrian_id=pedestrian_id,
        )

        if annotation is None:
            raise RuntimeError(
                f"Sequence {sequence_index}: missing annotation for "
                f"{video}, frame {frame_number}, pedestrian "
                f"{pedestrian_id}."
            )

        bbox = (
            annotation["x1"],
            annotation["y1"],
            annotation["x2"],
            annotation["y2"],
        )

        extraction = runtime_extractor.extract_frame(
            frame=image,
            bbox=bbox,
            occlusion=annotation["occlusion"],
            track_id=pedestrian_id,
        )

        vectors.append(
            extraction["feature_vector"]
        )

        occlusion_states.append(
            extraction["occlusion_level"]
        )

        motion_states.append(
            extraction["semantic_states"]["motion"]
        )

    sequence = np.stack(
        vectors,
        axis=0,
    ).astype(
        np.float32,
        copy=False,
    )

    if sequence.shape != (
        SEQUENCE_LENGTH,
        FEATURE_DIMENSION,
    ):
        raise ValueError(
            f"Sequence {sequence_index}: unexpected runtime "
            f"shape {sequence.shape}."
        )

    return sequence, {
        "video": video,
        "pedestrian_id": pedestrian_id,
        "first_frame": int(frames[0]),
        "last_frame": int(frames[-1]),
        "maximum_occlusion": maximum_occlusion(
            occlusion_states
        ),
        "low_frames": int(
            sum(
                state == "low"
                for state in occlusion_states
            )
        ),
        "medium_frames": int(
            sum(
                state == "medium"
                for state in occlusion_states
            )
        ),
        "high_frames": int(
            sum(
                state == "high"
                for state in occlusion_states
            )
        ),
        "dominant_motion": pd.Series(
            motion_states
        ).mode().iloc[0],
    }


def safe_binary_metrics(
    labels: np.ndarray,
    predictions: np.ndarray,
    probabilities: np.ndarray,
) -> dict[str, float | int]:
    result: dict[str, float | int] = {
        "samples": int(len(labels)),
        "accuracy": float(
            accuracy_score(
                labels,
                predictions,
            )
        ),
        "precision": float(
            precision_score(
                labels,
                predictions,
                zero_division=0,
            )
        ),
        "recall": float(
            recall_score(
                labels,
                predictions,
                zero_division=0,
            )
        ),
        "f1": float(
            f1_score(
                labels,
                predictions,
                zero_division=0,
            )
        ),
    }

    if len(np.unique(labels)) == 2:
        result["roc_auc"] = float(
            roc_auc_score(
                labels,
                probabilities,
            )
        )

        result["average_precision"] = float(
            average_precision_score(
                labels,
                probabilities,
            )
        )
    else:
        result["roc_auc"] = float("nan")
        result["average_precision"] = float("nan")

    matrix = confusion_matrix(
        labels,
        predictions,
        labels=[0, 1],
    )

    tn, fp, fn, tp = matrix.ravel()

    result.update(
        {
            "true_negative": int(tn),
            "false_positive": int(fp),
            "false_negative": int(fn),
            "true_positive": int(tp),
        }
    )

    return result


def clean_for_json(value: Any) -> Any:
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

    if isinstance(value, tuple):
        return [
            clean_for_json(item)
            for item in value
        ]

    if isinstance(value, np.generic):
        return value.item()

    if isinstance(value, float):
        if not math.isfinite(value):
            return None

    return value


def main() -> None:
    args = parse_arguments()

    required_paths = [
        FRAME_ROOT,
        ANNOTATION_PATH,
        TEST_METADATA_PATH,
        TEST_FEATURE_PATH,
    ]

    for path in required_paths:
        if not path.exists():
            raise FileNotFoundError(
                f"Required path not found: {path}"
            )

    output_dir = Path(
        args.output_dir
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    test_metadata = pd.read_csv(
        TEST_METADATA_PATH
    ).reset_index(drop=True)

    with np.load(
        TEST_FEATURE_PATH,
        allow_pickle=True,
    ) as data:
        saved_features = data["X"].astype(
            np.float32,
            copy=False,
        )

        test_labels = data["y"].astype(
            np.int64,
            copy=False,
        )

    if len(test_metadata) != len(saved_features):
        raise ValueError(
            "Test metadata and feature counts do not match: "
            f"{len(test_metadata)} vs {len(saved_features)}."
        )

    image_loader = ImageLoader(
        str(FRAME_ROOT)
    )

    annotation_loader = AnnotationLoader(
        str(ANNOTATION_PATH)
    )

    print("=" * 78)
    print("DEMO 1B - PIE HELD-OUT BATCH RUNTIME VALIDATION")
    print("=" * 78)
    print("Test sequences        :", len(test_metadata))
    print("Selection seed        :", args.seed)
    print("Per-class target      :", args.per_class)
    print("Selection rule        : class + occlusion only")
    print("Prediction-based pick : NO")

    test_index = build_test_index(
        test_metadata=test_metadata,
        test_labels=test_labels,
        annotation_loader=annotation_loader,
    )

    if args.sequence_indices:
        selected = select_explicit_sequences(
            test_index,
            args.sequence_indices,
        )
    else:
        selected = select_balanced_sequences(
            test_index=test_index,
            per_class=args.per_class,
            seed=args.seed,
        )

    selected_path = (
        output_dir
        / "selected_sequences.csv"
    )

    selected.to_csv(
        selected_path,
        index=False,
    )

    print("Selected sequences    :", len(selected))
    print()
    print(
        selected.groupby(
            [
                "label_id",
                "maximum_occlusion",
            ]
        ).size().rename(
            "count"
        ).reset_index().to_string(
            index=False
        )
    )

    runtime_extractor = RuntimeFeatureExtractor(
        bayesian_model_path=args.bayesian_model,
        normalize_to_training_resolution=True,
    )

    predictor = RuntimeIntentPredictor()

    sequence_buffer = FeatureSequenceBuffer(
        sequence_length=predictor.sequence_length,
        feature_dimension=predictor.input_dimension,
    )

    prediction_rows = []
    failure_rows = []

    total_start = time.perf_counter()

    for processed_number, selected_row in selected.iterrows():
        sequence_index = int(
            selected_row["sequence_index"]
        )

        true_label = int(
            test_labels[sequence_index]
        )

        print()
        print("-" * 78)
        print(
            f"[{processed_number + 1:02d}/{len(selected):02d}] "
            f"Sequence {sequence_index} | "
            f"truth={CLASS_NAMES[true_label]} | "
            f"selected occlusion="
            f"{selected_row['maximum_occlusion']}"
        )

        sequence_start = time.perf_counter()

        try:
            runtime_sequence, metadata = reconstruct_sequence(
                sequence_index=sequence_index,
                metadata_row=test_metadata.iloc[
                    sequence_index
                ],
                image_loader=image_loader,
                annotation_loader=annotation_loader,
                runtime_extractor=runtime_extractor,
                dataset_set=args.dataset_set,
            )

            expected_sequence = saved_features[
                sequence_index
            ]

            absolute_error = np.abs(
                runtime_sequence
                - expected_sequence
            )

            mean_absolute_error = float(
                absolute_error.mean()
            )

            max_absolute_error = float(
                absolute_error.max()
            )

            raw_max_error = float(
                absolute_error[:, :522].max()
            )

            reliability_max_error = float(
                absolute_error[:, 522:525].max()
            )

            feature_compatible = bool(
                np.allclose(
                    runtime_sequence,
                    expected_sequence,
                    rtol=1e-4,
                    atol=1e-4,
                )
            )

            sequence_buffer.reset()

            for time_step in range(
                SEQUENCE_LENGTH
            ):
                sequence_buffer.add(
                    runtime_sequence[
                        time_step
                    ],
                    metadata={
                        "sequence_index": sequence_index,
                        "time_step": time_step,
                    },
                )

            prediction = predictor.predict(
                sequence_buffer.get_sequence(),
                random_seed=10000 + sequence_index,
            )

            predicted_label = int(
                prediction["predicted_class_id"]
            )

            is_correct = bool(
                predicted_label == true_label
            )

            elapsed_seconds = float(
                time.perf_counter()
                - sequence_start
            )

            prediction_rows.append(
                {
                    "sequence_index": sequence_index,
                    "video": metadata["video"],
                    "pedestrian_id": metadata[
                        "pedestrian_id"
                    ],
                    "first_frame": metadata[
                        "first_frame"
                    ],
                    "last_frame": metadata[
                        "last_frame"
                    ],
                    "label_id": true_label,
                    "ground_truth": CLASS_NAMES[
                        true_label
                    ],
                    "predicted_label_id": predicted_label,
                    "predicted_intent": prediction[
                        "predicted_intent"
                    ],
                    "is_correct": is_correct,
                    "crossing_probability": prediction[
                        "crossing_probability"
                    ],
                    "confidence": prediction[
                        "confidence"
                    ],
                    "normalized_entropy": prediction[
                        "normalized_entropy"
                    ],
                    "mutual_information": prediction[
                        "mutual_information"
                    ],
                    "crossing_probability_variance": (
                        prediction[
                            "crossing_probability_variance"
                        ]
                    ),
                    "maximum_occlusion": metadata[
                        "maximum_occlusion"
                    ],
                    "low_frames": metadata[
                        "low_frames"
                    ],
                    "medium_frames": metadata[
                        "medium_frames"
                    ],
                    "high_frames": metadata[
                        "high_frames"
                    ],
                    "dominant_motion": metadata[
                        "dominant_motion"
                    ],
                    "runtime_feature_compatible": (
                        feature_compatible
                    ),
                    "feature_mean_absolute_error": (
                        mean_absolute_error
                    ),
                    "feature_max_absolute_error": (
                        max_absolute_error
                    ),
                    "raw_522_max_error": raw_max_error,
                    "reliability_3_max_error": (
                        reliability_max_error
                    ),
                    "elapsed_seconds": elapsed_seconds,
                }
            )

            print(
                "Runtime feature match :",
                "PASSED"
                if feature_compatible
                else "FAILED",
            )

            print(
                "Prediction            :",
                prediction["predicted_intent"],
            )

            print(
                "P(crossing)           :",
                f"{prediction['crossing_probability']:.6f}",
            )

            print(
                "Confidence            :",
                f"{prediction['confidence']:.6f}",
            )

            print(
                "Status                :",
                "CORRECT"
                if is_correct
                else "INCORRECT",
            )

        except Exception as error:
            failure_rows.append(
                {
                    "sequence_index": sequence_index,
                    "error_type": type(error).__name__,
                    "error_message": str(error),
                }
            )

            print(
                "Sequence status        : FAILED"
            )

            print(
                "Reason                 :",
                f"{type(error).__name__}: {error}",
            )

            if not args.continue_on_error:
                raise

    predictions = pd.DataFrame(
        prediction_rows
    )

    failures = pd.DataFrame(
        failure_rows
    )

    predictions_path = (
        output_dir
        / "runtime_batch_predictions.csv"
    )

    failures_path = (
        output_dir
        / "runtime_batch_failures.csv"
    )

    by_occlusion_path = (
        output_dir
        / "runtime_batch_by_occlusion.csv"
    )

    summary_path = (
        output_dir
        / "runtime_batch_summary.json"
    )

    predictions.to_csv(
        predictions_path,
        index=False,
    )

    failures.to_csv(
        failures_path,
        index=False,
    )

    if predictions.empty:
        raise RuntimeError(
            "No sequences were evaluated successfully."
        )

    labels = predictions[
        "label_id"
    ].to_numpy(
        dtype=np.int64
    )

    predicted_labels = predictions[
        "predicted_label_id"
    ].to_numpy(
        dtype=np.int64
    )

    probabilities = predictions[
        "crossing_probability"
    ].to_numpy(
        dtype=np.float64
    )

    overall_metrics = safe_binary_metrics(
        labels=labels,
        predictions=predicted_labels,
        probabilities=probabilities,
    )

    occlusion_rows = []

    for occlusion_state in (
        "low",
        "medium",
        "high",
    ):
        subset = predictions[
            predictions["maximum_occlusion"]
            == occlusion_state
        ]

        if subset.empty:
            continue

        subset_metrics = safe_binary_metrics(
            labels=subset["label_id"].to_numpy(
                dtype=np.int64
            ),
            predictions=subset[
                "predicted_label_id"
            ].to_numpy(
                dtype=np.int64
            ),
            probabilities=subset[
                "crossing_probability"
            ].to_numpy(
                dtype=np.float64
            ),
        )

        occlusion_rows.append(
            {
                "maximum_occlusion": occlusion_state,
                **subset_metrics,
                "mean_confidence": float(
                    subset["confidence"].mean()
                ),
                "mean_normalized_entropy": float(
                    subset[
                        "normalized_entropy"
                    ].mean()
                ),
                "mean_probability_variance": float(
                    subset[
                        "crossing_probability_variance"
                    ].mean()
                ),
                "feature_compatibility_rate": float(
                    subset[
                        "runtime_feature_compatible"
                    ].mean()
                ),
            }
        )

    by_occlusion = pd.DataFrame(
        occlusion_rows
    )

    by_occlusion.to_csv(
        by_occlusion_path,
        index=False,
    )

    total_elapsed_seconds = float(
        time.perf_counter()
        - total_start
    )

    feature_compatibility_rate = float(
        predictions[
            "runtime_feature_compatible"
        ].mean()
    )

    summary = {
        "evaluation_type": (
            "PIE held-out balanced runtime batch diagnostic"
        ),
        "selection": {
            "selection_uses_model_outputs": False,
            "seed": int(args.seed),
            "requested_per_class": int(
                args.per_class
            ),
            "explicit_sequence_indices": (
                [
                    int(value)
                    for value in args.sequence_indices
                ]
                if args.sequence_indices
                else None
            ),
            "selected_sequences": int(
                len(selected)
            ),
        },
        "runtime": {
            "successful_sequences": int(
                len(predictions)
            ),
            "failed_sequences": int(
                len(failures)
            ),
            "total_elapsed_seconds": (
                total_elapsed_seconds
            ),
            "mean_seconds_per_successful_sequence": float(
                predictions[
                    "elapsed_seconds"
                ].mean()
            ),
        },
        "feature_compatibility": {
            "compatible_sequences": int(
                predictions[
                    "runtime_feature_compatible"
                ].sum()
            ),
            "compatibility_rate": (
                feature_compatibility_rate
            ),
            "maximum_absolute_error": float(
                predictions[
                    "feature_max_absolute_error"
                ].max()
            ),
            "mean_of_sequence_mae": float(
                predictions[
                    "feature_mean_absolute_error"
                ].mean()
            ),
        },
        "classification": overall_metrics,
        "by_occlusion": occlusion_rows,
        "important_note": (
            "This balanced subset is a runtime diagnostic and viva demo. "
            "It does not replace the previously reported full 1152-sequence "
            "test evaluation."
        ),
        "test_data_used_for_tuning": False,
        "output_files": {
            "selected_sequences": str(
                selected_path
            ),
            "predictions": str(
                predictions_path
            ),
            "failures": str(
                failures_path
            ),
            "by_occlusion": str(
                by_occlusion_path
            ),
            "summary": str(
                summary_path
            ),
        },
    }

    with open(
        summary_path,
        "w",
        encoding="utf-8",
    ) as output_file:
        json.dump(
            clean_for_json(summary),
            output_file,
            indent=4,
        )

    print()
    print("=" * 78)
    print("BATCH RUNTIME VALIDATION SUMMARY")
    print("=" * 78)
    print("Selected sequences       :", len(selected))
    print("Successful sequences     :", len(predictions))
    print("Failed sequences         :", len(failures))
    print(
        "Feature compatibility   :",
        f"{feature_compatibility_rate:.4f}",
    )
    print(
        "Maximum feature error   :",
        f"{predictions['feature_max_absolute_error'].max():.10f}",
    )
    print(
        "Accuracy                :",
        f"{overall_metrics['accuracy']:.6f}",
    )
    print(
        "Precision               :",
        f"{overall_metrics['precision']:.6f}",
    )
    print(
        "Recall                  :",
        f"{overall_metrics['recall']:.6f}",
    )
    print(
        "F1                      :",
        f"{overall_metrics['f1']:.6f}",
    )
    print(
        "ROC-AUC                 :",
        (
            f"{overall_metrics['roc_auc']:.6f}"
            if overall_metrics["roc_auc"] is not None
            else "N/A"
        ),
    )
    print(
        "Average precision       :",
        (
            f"{overall_metrics['average_precision']:.6f}"
            if overall_metrics[
                "average_precision"
            ] is not None
            else "N/A"
        ),
    )
    print(
        "Confusion matrix        :",
        (
            f"TN={overall_metrics['true_negative']} "
            f"FP={overall_metrics['false_positive']} "
            f"FN={overall_metrics['false_negative']} "
            f"TP={overall_metrics['true_positive']}"
        ),
    )

    print()
    print("By occlusion:")
    print(
        by_occlusion.to_string(
            index=False
        )
    )

    print()
    print("Outputs:")
    print("  Selected     :", selected_path)
    print("  Predictions  :", predictions_path)
    print("  Failures     :", failures_path)
    print("  By occlusion :", by_occlusion_path)
    print("  Summary      :", summary_path)
    print()
    print(
        "This balanced subset is a runtime diagnostic. "
        "Keep the full 1152-sequence test results as the official "
        "model-performance result."
    )
    print("=" * 78)


if __name__ == "__main__":
    main()
