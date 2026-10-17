"""
Compatibility test for RuntimeFeatureExtractor.

It reconstructs a saved test sequence from original PIE frames and annotations,
then compares the newly generated (30, 525) runtime sequence against the
previously saved reliability-enriched test features.

Run:
    python -m scripts.demo.test_runtime_feature_extractor

Optional explicit Bayesian model:
    python -m scripts.demo.test_runtime_feature_extractor \
        --bayesian-model outputs/phase4/<final-model>.pkl
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from utils.annotation_loader import AnnotationLoader
from utils.image_loader import ImageLoader
from utils.runtime_feature_extractor import RuntimeFeatureExtractor


FRAME_ROOT = Path("datasets/processed/frames")
ANNOTATION_PATH = Path("datasets/processed/metadata/annotations.csv")
TEST_METADATA_PATH = Path("datasets/processed/metadata/test.csv")
TEST_FEATURE_PATH = Path(
    "datasets/processed/features/test_reliability_enriched_features.npz"
)

DEFAULT_SEQUENCE_INDEX = 28
DEFAULT_DATASET_SET = "set01"


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
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
    return parser.parse_args()


def get_first_available(row: pd.Series, names: list[str]) -> Any:
    for name in names:
        if name in row.index:
            return row[name]
    raise KeyError(f"None of these columns were found: {names}")


def parse_frames(value: Any) -> list[int]:
    if isinstance(value, str):
        normalized = value.replace(",", "|").replace(" ", "|")
        return [int(item) for item in normalized.split("|") if item != ""]

    if isinstance(value, (list, tuple, np.ndarray)):
        return [int(item) for item in value]

    raise TypeError(f"Unsupported frames value: {value!r}")


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
            raise FileNotFoundError(f"Required path not found: {path}")

    test_metadata = pd.read_csv(TEST_METADATA_PATH).reset_index(drop=True)

    with np.load(TEST_FEATURE_PATH, allow_pickle=True) as data:
        saved_features = data["X"].astype(np.float32, copy=False)
        saved_labels = data["y"].astype(np.int64, copy=False)

    sequence_index = int(args.sequence_index)
    if not 0 <= sequence_index < len(test_metadata):
        raise IndexError(
            f"sequence-index must be between 0 and {len(test_metadata) - 1}."
        )

    if len(test_metadata) != len(saved_features):
        raise ValueError(
            "test.csv and saved test feature counts do not match: "
            f"{len(test_metadata)} vs {len(saved_features)}"
        )

    row = test_metadata.iloc[sequence_index]
    video = str(get_first_available(row, ["video", "video_id"]))
    pedestrian_id = str(
        get_first_available(row, ["pedestrian_id", "id", "pedestrian"])
    )
    frames = parse_frames(
        get_first_available(row, ["frames", "frame_numbers", "sequence_frames"])
    )

    if len(frames) != 30:
        raise ValueError(f"Expected 30 frames, found {len(frames)}.")

    image_loader = ImageLoader(str(FRAME_ROOT))
    annotation_loader = AnnotationLoader(str(ANNOTATION_PATH))
    runtime_extractor = RuntimeFeatureExtractor(
        bayesian_model_path=args.bayesian_model,
        normalize_to_training_resolution=True,
    )

    runtime_extractor.reset_track(pedestrian_id)
    extracted_vectors = []

    print("=" * 78)
    print("RUNTIME FEATURE EXTRACTOR COMPATIBILITY TEST")
    print("=" * 78)
    print("Sequence index       :", sequence_index)
    print("Video                :", video)
    print("Pedestrian           :", pedestrian_id)
    print("Frame count          :", len(frames))
    print("Bayesian model       :", runtime_extractor.bayesian_model_path)

    for time_step, frame_number in enumerate(frames):
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
                f"Missing annotation for {video}, frame {frame_number}, "
                f"pedestrian {pedestrian_id}."
            )

        bbox = (
            annotation["x1"],
            annotation["y1"],
            annotation["x2"],
            annotation["y2"],
        )

        result = runtime_extractor.extract_frame(
            frame=image,
            bbox=bbox,
            occlusion=annotation["occlusion"],
            track_id=pedestrian_id,
        )

        extracted_vectors.append(result["feature_vector"])

        print(
            f"Frame {time_step + 1:02d}/30 | source={frame_number} | "
            f"occlusion={result['occlusion_level']} | "
            f"motion={result['semantic_states']['motion']}"
        )

    runtime_sequence = np.stack(extracted_vectors).astype(np.float32)
    expected_sequence = saved_features[sequence_index]

    if runtime_sequence.shape != (30, 525):
        raise ValueError(f"Unexpected runtime shape: {runtime_sequence.shape}")

    absolute_error = np.abs(runtime_sequence - expected_sequence)
    raw_error = absolute_error[:, :522]
    reliability_error = absolute_error[:, 522:525]

    max_absolute_error = float(absolute_error.max())
    mean_absolute_error = float(absolute_error.mean())
    raw_max_error = float(raw_error.max())
    reliability_max_error = float(reliability_error.max())

    # ResNet/GPU implementations can introduce tiny floating-point differences.
    is_compatible = bool(
        np.allclose(
            runtime_sequence,
            expected_sequence,
            rtol=1e-4,
            atol=1e-4,
        )
    )

    print()
    print("=" * 78)
    print("COMPATIBILITY RESULTS")
    print("=" * 78)
    print("Runtime shape        :", runtime_sequence.shape)
    print("Saved shape          :", expected_sequence.shape)
    print("Ground-truth label   :", int(saved_labels[sequence_index]))
    print("Mean absolute error  :", f"{mean_absolute_error:.10f}")
    print("Maximum abs. error   :", f"{max_absolute_error:.10f}")
    print("Raw 522 max error    :", f"{raw_max_error:.10f}")
    print("Reliability max error:", f"{reliability_max_error:.10f}")

    if is_compatible:
        print("Status               : PASSED")
        print("Runtime features match the trained-model feature format.")
    else:
        print("Status               : FAILED")
        print(
            "The output dimension is correct, but values differ from the "
            "saved training pipeline. Inspect the raw and reliability error "
            "values before moving to new videos."
        )

    print("=" * 78)


if __name__ == "__main__":
    main()
