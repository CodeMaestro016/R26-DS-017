"""
Demo 1: PIE held-out test-sequence visualization.

This script reconstructs a sequence directly from original PIE frames and
annotations, generates the exact runtime 525-D features, buffers 30 frames,
runs the frozen calibrated Transformer with MC Dropout, and saves an annotated
MP4.

Ground-truth intent is used only for evaluation/display. It is NOT given to
the predictor.

Default examples:
    28  -> known held-out not-crossing example
    463 -> known held-out crossing example

Run:
    python -m scripts.demo.generate_pie_heldout_demo

Run one sequence:
    python -m scripts.demo.generate_pie_heldout_demo --sequence-indices 463
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import pandas as pd

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

DEFAULT_SEQUENCE_INDICES = [28, 463]
DEFAULT_DATASET_SET = "set01"
DEFAULT_OUTPUT_DIR = Path("outputs/demo/pie_heldout")
OUTPUT_WIDTH = 1280
OUTPUT_HEIGHT = 720
OUTPUT_FPS = 10.0
RESULT_HOLD_SECONDS = 2.5

CLASS_NAMES = {
    0: "NOT-CROSSING",
    1: "CROSSING",
}


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--sequence-indices",
        type=int,
        nargs="+",
        default=DEFAULT_SEQUENCE_INDICES,
        help="One or more held-out test sequence indices.",
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
        "--display",
        action="store_true",
        help="Also show the demo while it is generated.",
    )

    return parser.parse_args()


def get_first_available(row: pd.Series, names: list[str]) -> Any:
    for name in names:
        if name in row.index:
            return row[name]

    raise KeyError(
        f"None of the required columns were found: {names}"
    )


def parse_frames(value: Any) -> list[int]:
    if isinstance(value, str):
        normalized = (
            value.replace(",", "|")
            .replace(" ", "|")
            .replace("[", "")
            .replace("]", "")
        )

        return [
            int(item)
            for item in normalized.split("|")
            if item.strip() != ""
        ]

    if isinstance(value, (list, tuple, np.ndarray)):
        return [int(item) for item in value]

    raise TypeError(f"Unsupported frames value: {value!r}")


def draw_text(
    image: np.ndarray,
    text: str,
    position: tuple[int, int],
    scale: float = 0.62,
    thickness: int = 2,
) -> None:
    x, y = position

    cv2.putText(
        image,
        text,
        (x + 2, y + 2),
        cv2.FONT_HERSHEY_SIMPLEX,
        scale,
        (0, 0, 0),
        thickness + 2,
        cv2.LINE_AA,
    )

    cv2.putText(
        image,
        text,
        (x, y),
        cv2.FONT_HERSHEY_SIMPLEX,
        scale,
        (255, 255, 255),
        thickness,
        cv2.LINE_AA,
    )


def resize_for_demo(
    frame: np.ndarray,
    bbox: tuple[int, int, int, int],
) -> tuple[np.ndarray, tuple[int, int, int, int]]:
    source_height, source_width = frame.shape[:2]

    resized = cv2.resize(
        frame,
        (OUTPUT_WIDTH, OUTPUT_HEIGHT),
        interpolation=cv2.INTER_AREA,
    )

    scale_x = OUTPUT_WIDTH / float(source_width)
    scale_y = OUTPUT_HEIGHT / float(source_height)

    x1, y1, x2, y2 = bbox

    resized_bbox = (
        int(round(x1 * scale_x)),
        int(round(y1 * scale_y)),
        int(round(x2 * scale_x)),
        int(round(y2 * scale_y)),
    )

    return resized, resized_bbox


def add_pedestrian_zoom(
    display_frame: np.ndarray,
    source_frame: np.ndarray,
    source_bbox: tuple[int, int, int, int],
) -> None:
    source_height, source_width = source_frame.shape[:2]
    x1, y1, x2, y2 = source_bbox

    bbox_width = max(x2 - x1, 1)
    bbox_height = max(y2 - y1, 1)

    margin_x = max(int(bbox_width * 1.5), 40)
    margin_y = max(int(bbox_height * 0.6), 35)

    crop_x1 = max(0, x1 - margin_x)
    crop_y1 = max(0, y1 - margin_y)
    crop_x2 = min(source_width, x2 + margin_x)
    crop_y2 = min(source_height, y2 + margin_y)

    crop = source_frame[
        crop_y1:crop_y2,
        crop_x1:crop_x2,
    ]

    if crop.size == 0:
        return

    panel_width = 260
    panel_height = 310

    zoom = cv2.resize(
        crop,
        (panel_width, panel_height),
        interpolation=cv2.INTER_CUBIC,
    )

    panel_x1 = OUTPUT_WIDTH - panel_width - 24
    panel_y1 = 90
    panel_x2 = panel_x1 + panel_width
    panel_y2 = panel_y1 + panel_height

    display_frame[
        panel_y1:panel_y2,
        panel_x1:panel_x2,
    ] = zoom

    cv2.rectangle(
        display_frame,
        (panel_x1 - 3, panel_y1 - 3),
        (panel_x2 + 3, panel_y2 + 3),
        (255, 255, 255),
        3,
    )

    draw_text(
        display_frame,
        "PEDESTRIAN EVIDENCE",
        (panel_x1, panel_y1 - 14),
        scale=0.52,
    )


def add_status_overlay(
    display_frame: np.ndarray,
    *,
    sequence_index: int,
    source_frame_number: int,
    time_step: int,
    true_label: int,
    annotation: dict,
    extraction_result: dict,
    prediction: dict | None,
) -> None:
    overlay = display_frame.copy()

    cv2.rectangle(
        overlay,
        (0, 0),
        (OUTPUT_WIDTH, 205),
        (0, 0, 0),
        -1,
    )

    cv2.addWeighted(
        overlay,
        0.64,
        display_frame,
        0.36,
        0,
        display_frame,
    )

    draw_text(
        display_frame,
        "ADAPTIVE PEDESTRIAN INTENT PREDICTION",
        (22, 34),
        scale=0.78,
    )

    draw_text(
        display_frame,
        (
            f"PIE held-out test | Sequence {sequence_index} | "
            f"Source frame {source_frame_number}"
        ),
        (22, 65),
        scale=0.56,
    )

    draw_text(
        display_frame,
        (
            f"Evidence buffer: {time_step + 1}/30 | "
            f"Occlusion: {extraction_result['occlusion_level'].upper()} | "
            f"Motion: {extraction_result['semantic_states']['motion'].upper()}"
        ),
        (22, 96),
        scale=0.56,
    )

    draw_text(
        display_frame,
        (
            f"Ground truth (display only): {CLASS_NAMES[true_label]} | "
            f"PIE action: {annotation['action']}"
        ),
        (22, 127),
        scale=0.56,
    )

    if prediction is None:
        draw_text(
            display_frame,
            "Model state: COLLECTING TEMPORAL EVIDENCE...",
            (22, 169),
            scale=0.68,
        )
    else:
        is_correct = (
            prediction["predicted_class_id"]
            == true_label
        )

        status = "CORRECT" if is_correct else "INCORRECT"

        draw_text(
            display_frame,
            (
                f"Prediction: {prediction['predicted_intent'].upper()} "
                f"[{status}]"
            ),
            (22, 163),
            scale=0.74,
        )

        draw_text(
            display_frame,
            (
                f"P(crossing)={prediction['crossing_probability']:.3f} | "
                f"Confidence={prediction['confidence']:.3f} | "
                f"Entropy={prediction['normalized_entropy']:.3f} | "
                f"Variance="
                f"{prediction['crossing_probability_variance']:.6f}"
            ),
            (22, 194),
            scale=0.52,
        )


def open_writer(path: Path) -> cv2.VideoWriter:
    path.parent.mkdir(parents=True, exist_ok=True)

    writer = cv2.VideoWriter(
        str(path),
        cv2.VideoWriter_fourcc(*"mp4v"),
        OUTPUT_FPS,
        (OUTPUT_WIDTH, OUTPUT_HEIGHT),
    )

    if not writer.isOpened():
        raise RuntimeError(
            f"Could not create output video: {path}"
        )

    return writer


def generate_demo(
    *,
    sequence_index: int,
    test_metadata: pd.DataFrame,
    test_labels: np.ndarray,
    image_loader: ImageLoader,
    annotation_loader: AnnotationLoader,
    predictor: RuntimeIntentPredictor,
    dataset_set: str,
    output_dir: Path,
    bayesian_model_path: str | None,
    display: bool,
) -> dict:
    if not 0 <= sequence_index < len(test_metadata):
        raise IndexError(
            f"Sequence index must be between 0 and "
            f"{len(test_metadata) - 1}; received {sequence_index}."
        )

    row = test_metadata.iloc[sequence_index]

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
            ["frames", "frame_numbers", "sequence_frames"],
        )
    )

    if len(frames) != predictor.sequence_length:
        raise ValueError(
            f"Expected {predictor.sequence_length} frames, "
            f"found {len(frames)}."
        )

    true_label = int(test_labels[sequence_index])

    runtime_extractor = RuntimeFeatureExtractor(
        bayesian_model_path=bayesian_model_path,
        normalize_to_training_resolution=True,
    )

    runtime_extractor.reset_track(pedestrian_id)

    sequence_buffer = FeatureSequenceBuffer(
        sequence_length=predictor.sequence_length,
        feature_dimension=predictor.input_dimension,
    )

    output_path = (
        output_dir
        / (
            f"pie_test_sequence_{sequence_index}_"
            f"{CLASS_NAMES[true_label].lower()}.mp4"
        )
    )

    writer = open_writer(output_path)

    final_prediction = None
    final_display_frame = None

    print()
    print("-" * 78)
    print("Sequence index :", sequence_index)
    print("Video          :", video)
    print("Pedestrian     :", pedestrian_id)
    print("Ground truth   :", CLASS_NAMES[true_label])
    print("Output         :", output_path)

    try:
        for time_step, frame_number in enumerate(frames):
            source_frame = image_loader.load_frame(
                video=video,
                frame_number=frame_number,
                dataset_set=dataset_set,
            )

            annotation = annotation_loader.get_annotation(
                video=video,
                frame=frame_number,
                pedestrian_id=pedestrian_id,
            )

            if annotation is None:
                raise RuntimeError(
                    f"Missing annotation for {video}, frame "
                    f"{frame_number}, pedestrian {pedestrian_id}."
                )

            bbox = (
                annotation["x1"],
                annotation["y1"],
                annotation["x2"],
                annotation["y2"],
            )

            extraction_result = runtime_extractor.extract_frame(
                frame=source_frame,
                bbox=bbox,
                occlusion=annotation["occlusion"],
                track_id=pedestrian_id,
            )

            sequence_buffer.add(
                extraction_result["feature_vector"],
                metadata={
                    "frame_number": frame_number,
                    "bbox": bbox,
                },
            )

            if sequence_buffer.is_ready:
                final_prediction = predictor.predict(
                    sequence_buffer.get_sequence(),
                    random_seed=1000 + sequence_index,
                )

            display_frame, display_bbox = resize_for_demo(
                source_frame,
                bbox,
            )

            x1, y1, x2, y2 = display_bbox

            cv2.rectangle(
                display_frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                3,
            )

            draw_text(
                display_frame,
                f"Pedestrian {pedestrian_id}",
                (x1, max(y1 - 10, 225)),
                scale=0.50,
            )

            add_pedestrian_zoom(
                display_frame,
                source_frame,
                bbox,
            )

            add_status_overlay(
                display_frame,
                sequence_index=sequence_index,
                source_frame_number=frame_number,
                time_step=time_step,
                true_label=true_label,
                annotation=annotation,
                extraction_result=extraction_result,
                prediction=final_prediction,
            )

            writer.write(display_frame)
            final_display_frame = display_frame.copy()

            if display:
                cv2.imshow(
                    "PIE held-out intent demo",
                    display_frame,
                )

                key = cv2.waitKey(
                    int(1000 / OUTPUT_FPS)
                ) & 0xFF

                if key in (27, ord("q")):
                    break

        if (
            final_prediction is not None
            and final_display_frame is not None
        ):
            hold_frames = int(
                round(
                    RESULT_HOLD_SECONDS
                    * OUTPUT_FPS
                )
            )

            for _ in range(hold_frames):
                writer.write(final_display_frame)

                if display:
                    cv2.imshow(
                        "PIE held-out intent demo",
                        final_display_frame,
                    )

                    key = cv2.waitKey(
                        int(1000 / OUTPUT_FPS)
                    ) & 0xFF

                    if key in (27, ord("q")):
                        break

    finally:
        writer.release()

        if display:
            cv2.destroyAllWindows()

    if final_prediction is None:
        raise RuntimeError(
            "The sequence ended before a prediction was produced."
        )

    is_correct = (
        final_prediction["predicted_class_id"]
        == true_label
    )

    print(
        "Prediction     :",
        final_prediction["predicted_intent"],
    )
    print(
        "P(crossing)    :",
        f"{final_prediction['crossing_probability']:.6f}",
    )
    print(
        "Confidence     :",
        f"{final_prediction['confidence']:.6f}",
    )
    print(
        "Entropy        :",
        f"{final_prediction['normalized_entropy']:.6f}",
    )
    print(
        "Variance       :",
        f"{final_prediction['crossing_probability_variance']:.6f}",
    )
    print(
        "Status         :",
        "CORRECT" if is_correct else "INCORRECT",
    )

    return {
        "sequence_index": sequence_index,
        "ground_truth": CLASS_NAMES[true_label],
        "prediction": final_prediction["predicted_intent"],
        "crossing_probability": final_prediction[
            "crossing_probability"
        ],
        "confidence": final_prediction["confidence"],
        "is_correct": is_correct,
        "output_path": str(output_path),
    }


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

    test_metadata = pd.read_csv(
        TEST_METADATA_PATH
    ).reset_index(drop=True)

    with np.load(
        TEST_FEATURE_PATH,
        allow_pickle=True,
    ) as data:
        test_labels = data["y"].astype(
            np.int64,
            copy=False,
        )

    if len(test_metadata) != len(test_labels):
        raise ValueError(
            "Test metadata and test labels have different lengths."
        )

    image_loader = ImageLoader(
        str(FRAME_ROOT)
    )

    annotation_loader = AnnotationLoader(
        str(ANNOTATION_PATH)
    )

    predictor = RuntimeIntentPredictor()

    output_dir = Path(args.output_dir)

    print("=" * 78)
    print("DEMO 1 - PIE HELD-OUT INTENT PREDICTION")
    print("=" * 78)
    print("Sequences       :", args.sequence_indices)
    print("Input source    : Original PIE real-world frames")
    print("Test split      : Held out from training")
    print("Model input     : Runtime-generated (30, 525)")
    print("Output directory:", output_dir)
    print()
    print(
        "Ground-truth labels are used only for display/evaluation, "
        "not as model input."
    )

    summaries = []

    for sequence_index in args.sequence_indices:
        summaries.append(
            generate_demo(
                sequence_index=int(sequence_index),
                test_metadata=test_metadata,
                test_labels=test_labels,
                image_loader=image_loader,
                annotation_loader=annotation_loader,
                predictor=predictor,
                dataset_set=args.dataset_set,
                output_dir=output_dir,
                bayesian_model_path=args.bayesian_model,
                display=args.display,
            )
        )

    print()
    print("=" * 78)
    print("DEMO GENERATION COMPLETE")
    print("=" * 78)

    for item in summaries:
        print(
            f"Sequence {item['sequence_index']} | "
            f"truth={item['ground_truth']} | "
            f"prediction={item['prediction']} | "
            f"confidence={item['confidence']:.4f} | "
            f"status={'CORRECT' if item['is_correct'] else 'INCORRECT'}"
        )
        print("  ", item["output_path"])

    print("=" * 78)


if __name__ == "__main__":
    main()
