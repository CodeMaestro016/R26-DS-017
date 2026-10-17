from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from utils.annotation_loader import AnnotationLoader
from utils.image_loader import ImageLoader
from utils.runtime_feature_extractor import RuntimeFeatureExtractor
from utils.unified_runtime_pipeline import UnifiedRuntimePipeline


FRAME_ROOT = Path("datasets/processed/frames")
ANNOTATION_PATH = Path("datasets/processed/metadata/annotations.csv")
TEST_METADATA_PATH = Path("datasets/processed/metadata/test.csv")
TEST_FEATURE_PATH = Path(
    "datasets/processed/features/test_reliability_enriched_features.npz"
)

DEFAULT_SEQUENCE_INDEX = 28
DEFAULT_DATASET_SET = "set01"

OCCLUSION_RANK = {
    "low": 0,
    "medium": 1,
    "high": 2,
}


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Reconstruct one held-out PIE sequence from original frames and "
            "annotations, then run the complete trained runtime pipeline."
        )
    )
    parser.add_argument(
        "--sequence-index",
        type=int,
        default=DEFAULT_SEQUENCE_INDEX,
    )
    parser.add_argument(
        "--dataset-set",
        type=str,
        default=DEFAULT_DATASET_SET,
    )
    parser.add_argument(
        "--bayesian-model",
        type=str,
        default=None,
    )
    parser.add_argument(
        "--explanation-steps",
        type=int,
        default=32,
    )
    return parser.parse_args()


def first_available(
    row: pd.Series,
    names: list[str],
) -> Any:
    for name in names:
        if name in row.index:
            return row[name]

    raise KeyError(
        f"None of these columns were found: {names}"
    )


def parse_frames(value: Any) -> list[int]:
    if isinstance(value, str):
        normalized = (
            value
            .replace(",", "|")
            .replace(" ", "|")
        )
        return [
            int(item)
            for item in normalized.split("|")
            if item != ""
        ]

    if isinstance(
        value,
        (list, tuple, np.ndarray),
    ):
        return [int(item) for item in value]

    raise TypeError(
        f"Unsupported frames value: {value!r}"
    )


def maximum_occlusion(
    levels: list[str],
) -> str:
    if not levels:
        raise ValueError(
            "Cannot calculate maximum occlusion from an empty list."
        )

    unknown = [
        level
        for level in levels
        if level not in OCCLUSION_RANK
    ]

    if unknown:
        raise ValueError(
            f"Unsupported normalized occlusion levels: {unknown}"
        )

    return max(
        levels,
        key=lambda value: OCCLUSION_RANK[value],
    )


def main() -> None:
    args = parse_arguments()

    print("=" * 100)
    print("PHASE 9.2 - PIE REAL-FRAME -> FINAL AGENT DECISION PIPELINE")
    print("=" * 100)

    for path in (
        FRAME_ROOT,
        ANNOTATION_PATH,
        TEST_METADATA_PATH,
        TEST_FEATURE_PATH,
    ):
        if not path.exists():
            raise FileNotFoundError(
                f"Required path not found: {path}"
            )

    metadata = pd.read_csv(
        TEST_METADATA_PATH
    ).reset_index(drop=True)

    with np.load(
        TEST_FEATURE_PATH,
        allow_pickle=True,
    ) as payload:
        saved_features = payload["X"].astype(
            np.float32,
            copy=False,
        )
        saved_labels = payload["y"].astype(
            np.int64,
            copy=False,
        )

    sequence_index = int(
        args.sequence_index
    )

    if not 0 <= sequence_index < len(metadata):
        raise IndexError(
            f"sequence-index must be between 0 and "
            f"{len(metadata) - 1}."
        )

    if len(metadata) != len(saved_features):
        raise ValueError(
            "test.csv and saved test feature counts differ: "
            f"{len(metadata)} vs {len(saved_features)}"
        )

    row = metadata.iloc[
        sequence_index
    ]

    video = str(
        first_available(
            row,
            ["video", "video_id"],
        )
    )

    pedestrian_id = str(
        first_available(
            row,
            [
                "pedestrian_id",
                "id",
                "pedestrian",
            ],
        )
    )

    frames = parse_frames(
        first_available(
            row,
            [
                "frames",
                "frame_numbers",
                "sequence_frames",
            ],
        )
    )

    if len(frames) != 30:
        raise ValueError(
            f"Expected 30 frames, found {len(frames)}."
        )

    image_loader = ImageLoader(
        str(FRAME_ROOT)
    )

    annotation_loader = AnnotationLoader(
        str(ANNOTATION_PATH)
    )

    feature_extractor = RuntimeFeatureExtractor(
        bayesian_model_path=args.bayesian_model,
        normalize_to_training_resolution=True,
    )

    unified_pipeline = UnifiedRuntimePipeline(
        explanation_steps=int(
            args.explanation_steps
        )
    )

    feature_extractor.reset_track(
        pedestrian_id
    )

    vectors: list[np.ndarray] = []
    normalized_occlusions: list[str] = []
    frame_diagnostics: list[dict[str, Any]] = []

    print(
        "Sequence index     :",
        sequence_index,
    )
    print(
        "Sequence ID        :",
        row.get(
            "sequence_id",
            "unknown",
        ),
    )
    print("Video              :", video)
    print("Pedestrian         :", pedestrian_id)
    print("Frame count        :", len(frames))
    print(
        "Ground truth       :",
        (
            "CROSSING"
            if int(saved_labels[sequence_index]) == 1
            else "NOT_CROSSING"
        ),
        "(diagnostic only)",
    )
    print(
        "Bayesian model     :",
        feature_extractor.bayesian_model_path,
    )

    print()
    print("-" * 100)
    print("RUNTIME FEATURE EXTRACTION FROM ORIGINAL PIE FRAMES")
    print("-" * 100)

    for time_step, frame_number in enumerate(
        frames,
        start=1,
    ):
        image = image_loader.load_frame(
            video=video,
            frame_number=frame_number,
            dataset_set=args.dataset_set,
        )

        annotation = annotation_loader.get_annotation(
            video=video,
            frame=frame_number,
            pedestrian_id=pedestrian_id,
        )

        if annotation is None:
            raise RuntimeError(
                f"Missing annotation for {video}, "
                f"frame {frame_number}, "
                f"pedestrian {pedestrian_id}."
            )

        bbox = (
            annotation["x1"],
            annotation["y1"],
            annotation["x2"],
            annotation["y2"],
        )

        extracted = feature_extractor.extract_frame(
            frame=image,
            bbox=bbox,
            occlusion=annotation["occlusion"],
            track_id=pedestrian_id,
        )

        vector = np.asarray(
            extracted["feature_vector"],
            dtype=np.float32,
        )

        if vector.shape != (525,):
            raise ValueError(
                f"Frame {frame_number} returned "
                f"feature shape {vector.shape}"
            )

        occ_level = str(
            extracted["occlusion_level"]
        )

        vectors.append(vector)
        normalized_occlusions.append(
            occ_level
        )

        semantic_states = extracted.get(
            "semantic_states",
            {},
        )

        diagnostic = {
            "time_step": int(time_step),
            "source_frame": int(frame_number),
            "source_occlusion": str(
                annotation["occlusion"]
            ),
            "normalized_occlusion": occ_level,
            "motion_state": str(
                semantic_states.get(
                    "motion",
                    "unknown",
                )
            ),
            "horizontal_state": str(
                semantic_states.get(
                    "horizontal",
                    "unknown",
                )
            ),
            "vertical_state": str(
                semantic_states.get(
                    "vertical",
                    "unknown",
                )
            ),
        }

        frame_diagnostics.append(
            diagnostic
        )

        print(
            f"Frame {time_step:02d}/30 | "
            f"source={frame_number} | "
            f"occlusion={occ_level:6s} | "
            f"motion={diagnostic['motion_state']}"
        )

    runtime_sequence = np.stack(
        vectors,
        axis=0,
    ).astype(
        np.float32,
        copy=False,
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

    is_compatible = bool(
        np.allclose(
            runtime_sequence,
            expected_sequence,
            rtol=1e-4,
            atol=1e-4,
        )
    )

    max_occ = maximum_occlusion(
        normalized_occlusions
    )

    print()
    print("-" * 100)
    print("FRAME -> FEATURE COMPATIBILITY")
    print("-" * 100)
    print(
        "Runtime shape          :",
        runtime_sequence.shape,
    )
    print(
        "Saved shape            :",
        expected_sequence.shape,
    )
    print(
        "Maximum occlusion      :",
        max_occ,
    )
    print(
        "Mean absolute error    :",
        f"{mean_absolute_error:.10f}",
    )
    print(
        "Maximum absolute error :",
        f"{max_absolute_error:.10f}",
    )
    print(
        "Raw 522 max error      :",
        f"{raw_max_error:.10f}",
    )
    print(
        "Reliability max error  :",
        f"{reliability_max_error:.10f}",
    )
    print(
        "Training compatibility :",
        "PASSED"
        if is_compatible
        else "FAILED",
    )

    if not is_compatible:
        raise RuntimeError(
            "Runtime features no longer match the frozen "
            "training/test feature representation. "
            "Stop before interpreting downstream model output."
        )

    result = unified_pipeline.predict(
        runtime_sequence,
        maximum_occlusion=max_occ,
    )

    print()
    print("-" * 100)
    print("FINAL END-TO-END RESULT")
    print("-" * 100)
    print(
        "Frozen intent          :",
        result.intent_prediction,
    )
    print(
        "P(crossing)            :",
        f"{result.p_crossing:.6f}",
    )
    print(
        "Confidence             :",
        f"{result.confidence:.6f}",
    )
    print(
        "Normalized entropy     :",
        f"{result.normalized_predictive_entropy:.6f}",
    )
    print(
        "Mutual information     :",
        f"{result.mutual_information:.6f}",
    )

    print()
    print(
        "Learned agent action   :",
        result.agent_action_name,
    )
    print(
        "Agent action prob.     :",
        f"{result.agent_action_probability:.6f}",
    )
    print(
        "Committed intent       :",
        result.committed_intent,
    )
    print(
        "AV interface signal    :",
        result.av_interface_signal,
    )

    print()
    print(
        "Explanation group      :",
        result.dominant_explanation_group,
    )
    print(
        "Situation explanation :",
        result.explanation,
    )

    output_dir = Path(
        "outputs/phase9"
    )
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        output_dir
        / (
            f"pie_frame_to_decision_"
            f"sequence_{sequence_index}.json"
        )
    )

    payload = {
        "phase": "9.2",
        "sequence_index": sequence_index,
        "sequence_id": (
            row.get(
                "sequence_id",
                "unknown",
            )
        ),
        "video": video,
        "pedestrian_id": pedestrian_id,
        "source_frames": frames,
        "ground_truth_diagnostic_only": int(
            saved_labels[sequence_index]
        ),
        "maximum_occlusion": max_occ,
        "feature_compatibility": {
            "runtime_shape": list(
                runtime_sequence.shape
            ),
            "saved_shape": list(
                expected_sequence.shape
            ),
            "mean_absolute_error": (
                mean_absolute_error
            ),
            "maximum_absolute_error": (
                max_absolute_error
            ),
            "raw_522_max_error": (
                raw_max_error
            ),
            "reliability_max_error": (
                reliability_max_error
            ),
            "passed": is_compatible,
        },
        "frame_diagnostics": (
            frame_diagnostics
        ),
        "final_runtime_result": (
            result.to_dict()
        ),
    }

    output_path.write_text(
        json.dumps(
            payload,
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )

    print()
    print("-" * 100)
    print("OUTPUT")
    print("-" * 100)
    print(output_path)
    print()
    print(
        "This run started from original PIE image frames and "
        "pedestrian annotations; saved 525-D features were used "
        "only as a compatibility reference, not as model input."
    )
    print("Status: PASSED")
    print("=" * 100)


if __name__ == "__main__":
    main()
