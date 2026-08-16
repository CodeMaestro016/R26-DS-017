from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from utils.annotation_loader import AnnotationLoader
from utils.image_loader import ImageLoader
from utils.probabilistic_runtime_feature_extractor import (
    ProbabilisticRuntimeFeatureExtractor,
)
from utils.runtime_feature_extractor import (
    RuntimeFeatureExtractor,
)
from utils.runtime_occlusion_estimator import (
    RuntimeOcclusionEstimator,
)


FRAME_ROOT = Path(
    "datasets/processed/frames"
)
ANNOTATION_PATH = Path(
    "datasets/processed/metadata/annotations.csv"
)
TEST_METADATA_PATH = Path(
    "datasets/processed/metadata/test.csv"
)
OUTPUT_DIR = Path(
    "outputs/phase9/probabilistic_runtime_integration"
)

DEFAULT_SEQUENCE_INDEX = 28


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--sequence-index",
        type=int,
        default=DEFAULT_SEQUENCE_INDEX,
    )

    return parser.parse_args()


def parse_frames(
    value,
) -> list[int]:
    return [
        int(item)
        for item
        in str(value).split("|")
        if item
    ]


def dataset_set_from_pedestrian_id(
    pedestrian_id: str,
) -> str:
    prefix = str(
        pedestrian_id
    ).split(
        "_",
        1,
    )[0]

    return f"set{int(prefix):02d}"


def one_hot_for_label(
    label: str,
) -> dict[str, float]:
    text = str(
        label
    ).strip().lower()

    mapping = {
        "none": {
            "none": 1.0,
            "part": 0.0,
            "full": 0.0,
        },
        "part": {
            "none": 0.0,
            "part": 1.0,
            "full": 0.0,
        },
        "full": {
            "none": 0.0,
            "part": 0.0,
            "full": 1.0,
        },
    }

    return mapping[text]


def main() -> None:
    args = parse_args()

    print("=" * 108)
    print(
        "PHASE 9.7A - PROBABILISTIC OCCLUSION -> "
        "BAYESIAN RELIABILITY -> 525-D RUNTIME INTEGRATION"
    )
    print("=" * 108)

    for path in (
        FRAME_ROOT,
        ANNOTATION_PATH,
        TEST_METADATA_PATH,
    ):
        if not path.exists():
            raise FileNotFoundError(
                f"Required path not found: {path}"
            )

    metadata = pd.read_csv(
        TEST_METADATA_PATH
    ).reset_index(
        drop=True
    )

    sequence_index = int(
        args.sequence_index
    )

    row = metadata.iloc[
        sequence_index
    ]

    video = str(
        row["video"]
    )
    pedestrian_id = str(
        row["pedestrian_id"]
    )
    frames = parse_frames(
        row["frames"]
    )
    dataset_set = (
        dataset_set_from_pedestrian_id(
            pedestrian_id
        )
    )

    if len(frames) != 30:
        raise ValueError(
            f"Expected 30 frames, got {len(frames)}."
        )

    image_loader = ImageLoader(
        str(
            FRAME_ROOT
        )
    )

    annotation_loader = (
        AnnotationLoader(
            str(
                ANNOTATION_PATH
            )
        )
    )

    # Separate extractors are intentional so motion histories remain aligned
    # for each independent comparison path.
    legacy = RuntimeFeatureExtractor(
        normalize_to_training_resolution=True
    )

    one_hot_soft = (
        ProbabilisticRuntimeFeatureExtractor(
            normalize_to_training_resolution=True
        )
    )

    automatic_soft = (
        ProbabilisticRuntimeFeatureExtractor(
            normalize_to_training_resolution=True
        )
    )

    occlusion_estimator = (
        RuntimeOcclusionEstimator()
    )

    for extractor in (
        legacy,
        one_hot_soft,
        automatic_soft,
    ):
        extractor.reset_track(
            pedestrian_id
        )

    automatic_vectors = []
    compatibility_differences = []
    records = []

    print(
        "Sequence:",
        sequence_index,
        dataset_set,
        video,
        pedestrian_id,
    )
    print(
        "Purpose  : verify one-hot soft integration "
        "matches legacy hard-label Bayesian features, then "
        "build an annotation-free automatic-occlusion 525-D sequence."
    )
    print()

    for step, frame_number in enumerate(
        frames,
        start=1,
    ):
        image = image_loader.load_frame(
            video=video,
            frame_number=frame_number,
            dataset_set=dataset_set,
        )

        annotation = (
            annotation_loader
            .get_annotation(
                video=video,
                frame=frame_number,
                pedestrian_id=pedestrian_id,
            )
        )

        if annotation is None:
            raise RuntimeError(
                f"Missing annotation for "
                f"{dataset_set}/{video}, "
                f"frame={frame_number}, "
                f"pedestrian={pedestrian_id}."
            )

        bbox = (
            annotation["x1"],
            annotation["y1"],
            annotation["x2"],
            annotation["y2"],
        )

        # Compatibility branch: GT label is used ONLY to prove that the new
        # probabilistic formulation reduces to the legacy path for one-hot input.
        legacy_result = (
            legacy.extract_frame(
                frame=image,
                bbox=bbox,
                occlusion=annotation[
                    "occlusion"
                ],
                track_id=pedestrian_id,
            )
        )

        one_hot_result = (
            one_hot_soft
            .extract_frame_with_probabilities(
                frame=image,
                bbox=bbox,
                occlusion_probabilities=(
                    one_hot_for_label(
                        annotation[
                            "occlusion"
                        ]
                    )
                ),
                track_id=pedestrian_id,
            )
        )

        compatibility_error = float(
            np.max(
                np.abs(
                    legacy_result[
                        "feature_vector"
                    ]
                    - one_hot_result[
                        "feature_vector"
                    ]
                )
            )
        )

        compatibility_differences.append(
            compatibility_error
        )

        # Runtime branch: the occlusion annotation is NOT used.
        automatic_occ = (
            occlusion_estimator.predict(
                frame=image,
                bbox=bbox,
            )
        )

        automatic_result = (
            automatic_soft
            .extract_frame_with_probabilities(
                frame=image,
                bbox=bbox,
                occlusion_probabilities=(
                    automatic_occ[
                        "probabilities"
                    ]
                ),
                track_id=pedestrian_id,
            )
        )

        automatic_vectors.append(
            automatic_result[
                "feature_vector"
            ]
        )

        records.append(
            {
                "step": step,
                "frame": frame_number,
                "gt_occlusion_diagnostic_only": (
                    str(
                        annotation[
                            "occlusion"
                        ]
                    )
                ),
                "automatic_occlusion": (
                    automatic_occ[
                        "occlusion"
                    ]
                ),
                "p_none": float(
                    automatic_occ[
                        "probabilities"
                    ][
                        "none"
                    ]
                ),
                "p_part": float(
                    automatic_occ[
                        "probabilities"
                    ][
                        "part"
                    ]
                ),
                "p_full": float(
                    automatic_occ[
                        "probabilities"
                    ][
                        "full"
                    ]
                ),
                "p_reliability_low": float(
                    automatic_result[
                        "reliability_features"
                    ][0]
                ),
                "p_reliability_medium": float(
                    automatic_result[
                        "reliability_features"
                    ][1]
                ),
                "p_reliability_high": float(
                    automatic_result[
                        "reliability_features"
                    ][2]
                ),
                "one_hot_compatibility_max_error": (
                    compatibility_error
                ),
            }
        )

        probs = automatic_occ[
            "probabilities"
        ]

        reliability = automatic_result[
            "reliability_features"
        ]

        print(
            f"Frame {step:02d}/30 | "
            f"auto_occ={automatic_occ['occlusion']:5s} | "
            f"Pocc=({probs['none']:.3f},"
            f"{probs['part']:.3f},"
            f"{probs['full']:.3f}) | "
            f"Prel=({reliability[0]:.3f},"
            f"{reliability[1]:.3f},"
            f"{reliability[2]:.3f}) | "
            f"compat_err={compatibility_error:.8f}"
        )

    sequence = np.stack(
        automatic_vectors
    ).astype(
        np.float32
    )

    if sequence.shape != (
        30,
        525,
    ):
        raise ValueError(
            "Automatic runtime sequence has "
            f"shape {sequence.shape}, expected (30,525)."
        )

    max_compatibility_error = float(
        max(
            compatibility_differences
        )
    )

    is_compatible = bool(
        max_compatibility_error
        <= 1e-5
    )

    reliability_matrix = (
        sequence[
            :,
            522:525,
        ]
    )

    reliability_row_sums = (
        reliability_matrix.sum(
            axis=1
        )
    )

    probability_valid = bool(
        np.allclose(
            reliability_row_sums,
            1.0,
            atol=1e-5,
            rtol=1e-5,
        )
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    npz_path = (
        OUTPUT_DIR
        / (
            f"sequence_{sequence_index}_"
            "automatic_soft_features.npz"
        )
    )

    np.savez_compressed(
        npz_path,
        X=sequence,
    )

    csv_path = (
        OUTPUT_DIR
        / (
            f"sequence_{sequence_index}_"
            "automatic_soft_features.csv"
        )
    )

    pd.DataFrame(
        records
    ).to_csv(
        csv_path,
        index=False,
    )

    summary = {
        "phase": "9.7A",
        "sequence_index": sequence_index,
        "dataset_set": dataset_set,
        "video": video,
        "pedestrian_id": pedestrian_id,
        "automatic_sequence_shape": list(
            sequence.shape
        ),
        "one_hot_reduces_to_legacy_path": (
            is_compatible
        ),
        "one_hot_max_absolute_error": (
            max_compatibility_error
        ),
        "mixed_reliability_rows_sum_to_one": (
            probability_valid
        ),
        "runtime_annotation_dependency": (
            "none for automatic occlusion branch; "
            "ground-truth occlusion is used only for "
            "compatibility/diagnostic reporting"
        ),
        "important_note": (
            "The automatic occlusion estimator had validation "
            "accuracy 0.58 and macro-F1 about 0.578, so these "
            "soft probabilities preserve uncertainty instead of "
            "forcing a hard occlusion state."
        ),
        "outputs": {
            "npz": str(
                npz_path
            ),
            "csv": str(
                csv_path
            ),
        },
    }

    json_path = (
        OUTPUT_DIR
        / (
            f"sequence_{sequence_index}_"
            "integration_summary.json"
        )
    )

    json_path.write_text(
        json.dumps(
            summary,
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print("-" * 108)
    print("PROBABILISTIC RUNTIME INTEGRATION SUMMARY")
    print("-" * 108)
    print(
        "Automatic sequence shape              :",
        sequence.shape,
    )
    print(
        "One-hot soft path == legacy hard path :",
        is_compatible,
    )
    print(
        "Maximum one-hot compatibility error   :",
        f"{max_compatibility_error:.10f}",
    )
    print(
        "Reliability probabilities valid       :",
        probability_valid,
    )
    print(
        "Runtime automatic branch uses GT occ  :",
        False,
    )
    print(
        "NPZ:",
        npz_path,
    )
    print(
        "CSV:",
        csv_path,
    )
    print(
        "Summary:",
        json_path,
    )

    if not is_compatible:
        raise RuntimeError(
            "One-hot probabilistic integration does not "
            "reproduce the legacy feature path."
        )

    if not probability_valid:
        raise RuntimeError(
            "Mixed reliability probabilities are invalid."
        )

    print(
        "Status: PASSED"
    )
    print("=" * 108)


if __name__ == "__main__":
    main()
