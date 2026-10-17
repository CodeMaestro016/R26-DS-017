"""
Unseen real-world video intent inference pilot.

This is an initial controlled runtime test:
- The user manually selects one pedestrian in the first frame.
- OpenCV tracks that pedestrian.
- A constant/manual occlusion state is supplied from the command line.
- The existing RuntimeFeatureExtractor creates exact 525-D features.
- A 30-frame FeatureSequenceBuffer feeds the frozen intent model.
- Calibrated crossing probability and uncertainty are overlaid.
- The annotated result is saved as an MP4.

Example:
    python -m scripts.demo.test_unseen_video_inference \
        --video inputs/demo/pedestrian_demo.mp4 \
        --occlusion low

Controls:
    ROI window:
        Drag a box around the pedestrian, then press ENTER or SPACE.
    Playback window:
        q or ESC = stop
        1 = set runtime occlusion to low
        2 = set runtime occlusion to medium
        3 = set runtime occlusion to high
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Callable, Optional, Tuple

import cv2
import numpy as np

from utils.runtime_feature_extractor import RuntimeFeatureExtractor
from utils.runtime_intent_predictor import RuntimeIntentPredictor
from utils.sequence_buffer import FeatureSequenceBuffer


BBoxXYWH = Tuple[float, float, float, float]


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--video",
        type=str,
        required=True,
        help="Path to an unseen MP4/AVI video.",
    )

    parser.add_argument(
        "--output",
        type=str,
        default="outputs/demo/unseen_video_intent_output.mp4",
        help="Annotated output-video path.",
    )

    parser.add_argument(
        "--occlusion",
        type=str,
        choices=["low", "medium", "high"],
        default="low",
        help=(
            "Initial manual occlusion state. During playback, "
            "press 1/2/3 to change low/medium/high."
        ),
    )

    parser.add_argument(
        "--frame-step",
        type=int,
        default=1,
        help=(
            "Use every Nth source frame for feature extraction. "
            "Use 1 for approximately 25-30 FPS videos; use 2 for 50-60 FPS."
        ),
    )

    parser.add_argument(
        "--predict-every",
        type=int,
        default=5,
        help=(
            "After the 30-frame buffer is ready, run MC inference every N "
            "accepted frames. Lower values update more often but are slower."
        ),
    )

    parser.add_argument(
        "--track-id",
        type=str,
        default="pedestrian_1",
    )

    parser.add_argument(
        "--no-display",
        action="store_true",
        help="Process and save without showing the playback window.",
    )

    parser.add_argument(
        "--bayesian-model",
        type=str,
        default=None,
        help="Optional explicit final Bayesian model path.",
    )

    return parser.parse_args()


def create_tracker() -> object:
    candidates: list[Optional[Callable[[], object]]] = [
        getattr(cv2, "TrackerCSRT_create", None),
        getattr(getattr(cv2, "legacy", object()), "TrackerCSRT_create", None),
        getattr(cv2, "TrackerKCF_create", None),
        getattr(getattr(cv2, "legacy", object()), "TrackerKCF_create", None),
        getattr(cv2, "TrackerMIL_create", None),
    ]

    for creator in candidates:
        if callable(creator):
            return creator()

    raise RuntimeError(
        "No supported OpenCV tracker is available. Install an OpenCV build "
        "with tracking support, usually: pip install opencv-contrib-python"
    )


def xywh_to_xyxy(box: BBoxXYWH) -> Tuple[float, float, float, float]:
    x, y, width, height = (float(value) for value in box)

    if width <= 1 or height <= 1:
        raise ValueError(f"Tracker returned an invalid box: {box}")

    return x, y, x + width, y + height


def clipped_xyxy(
    box: Tuple[float, float, float, float],
    frame_width: int,
    frame_height: int,
) -> Tuple[int, int, int, int]:
    x1, y1, x2, y2 = box

    x1 = int(np.clip(round(x1), 0, frame_width - 1))
    y1 = int(np.clip(round(y1), 0, frame_height - 1))
    x2 = int(np.clip(round(x2), x1 + 1, frame_width))
    y2 = int(np.clip(round(y2), y1 + 1, frame_height))

    return x1, y1, x2, y2


def put_text(
    frame: np.ndarray,
    text: str,
    y: int,
    scale: float = 0.62,
) -> None:
    cv2.putText(
        frame,
        text,
        (18, y),
        cv2.FONT_HERSHEY_SIMPLEX,
        scale,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )
    cv2.putText(
        frame,
        text,
        (18, y),
        cv2.FONT_HERSHEY_SIMPLEX,
        scale,
        (0, 0, 0),
        1,
        cv2.LINE_AA,
    )


def open_video_writer(
    output_path: Path,
    source_fps: float,
    frame_width: int,
    frame_height: int,
) -> cv2.VideoWriter:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fps = source_fps if source_fps > 0 else 30.0
    writer = cv2.VideoWriter(
        str(output_path),
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (frame_width, frame_height),
    )

    if not writer.isOpened():
        raise RuntimeError(f"Could not create output video: {output_path}")

    return writer


def reliability_state(feature_result: dict) -> Tuple[str, float]:
    probabilities = np.asarray(
        feature_result["reliability_features"],
        dtype=np.float32,
    ).reshape(-1)

    if probabilities.shape != (3,):
        return "unknown", float("nan")

    labels = ("low", "medium", "high")
    index = int(np.argmax(probabilities))

    return labels[index], float(probabilities[index])


def main() -> None:
    args = parse_arguments()

    if args.frame_step <= 0:
        raise ValueError("--frame-step must be positive.")

    if args.predict_every <= 0:
        raise ValueError("--predict-every must be positive.")

    video_path = Path(args.video)
    output_path = Path(args.output)

    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    capture = cv2.VideoCapture(str(video_path))

    if not capture.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    ok, first_frame = capture.read()

    if not ok or first_frame is None:
        capture.release()
        raise RuntimeError("Could not read the first video frame.")

    frame_height, frame_width = first_frame.shape[:2]
    source_fps = float(capture.get(cv2.CAP_PROP_FPS))
    total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))

    print("=" * 78)
    print("UNSEEN REAL-WORLD VIDEO INTENT INFERENCE")
    print("=" * 78)
    print("Video              :", video_path)
    print("Resolution         :", (frame_width, frame_height))
    print("Source FPS         :", f"{source_fps:.3f}")
    print("Source frame count :", total_frames)
    print("Frame step         :", args.frame_step)
    print("Initial occlusion  :", args.occlusion)
    print()
    print("Select one pedestrian, then press ENTER or SPACE.")

    initial_roi = cv2.selectROI(
        "Select pedestrian",
        first_frame,
        showCrosshair=True,
        fromCenter=False,
    )
    cv2.destroyWindow("Select pedestrian")

    if initial_roi[2] <= 1 or initial_roi[3] <= 1:
        capture.release()
        raise RuntimeError("No valid pedestrian ROI was selected.")

    tracker = create_tracker()

    tracker_initialization = tracker.init(
        first_frame,
        tuple(initial_roi),
    )

    # Some OpenCV builds return None on successful initialization;
    # only an explicit False indicates failure.
    if tracker_initialization is False:
        capture.release()
        raise RuntimeError("OpenCV tracker initialization failed.")

    runtime_extractor = RuntimeFeatureExtractor(
        bayesian_model_path=args.bayesian_model,
        normalize_to_training_resolution=True,
    )

    predictor = RuntimeIntentPredictor()

    sequence_buffer = FeatureSequenceBuffer(
        sequence_length=predictor.sequence_length,
        feature_dimension=predictor.input_dimension,
    )

    runtime_extractor.reset_track(args.track_id)

    writer = open_video_writer(
        output_path=output_path,
        source_fps=source_fps,
        frame_width=frame_width,
        frame_height=frame_height,
    )

    current_occlusion = args.occlusion
    last_prediction: Optional[dict] = None
    last_feature_result: Optional[dict] = None

    source_frame_index = 0
    accepted_frame_count = 0
    prediction_count = 0
    tracker_failures = 0
    current_frame = first_frame

    try:
        while True:
            if source_frame_index == 0:
                tracking_ok = True
                tracked_xywh = initial_roi
            else:
                tracking_ok, tracked_xywh = tracker.update(current_frame)

            display_frame = current_frame.copy()

            if tracking_ok:
                bbox = xywh_to_xyxy(tracked_xywh)
                x1, y1, x2, y2 = clipped_xyxy(
                    bbox,
                    frame_width=frame_width,
                    frame_height=frame_height,
                )

                cv2.rectangle(
                    display_frame,
                    (x1, y1),
                    (x2, y2),
                    (0, 255, 0),
                    2,
                )

                should_extract = (
                    source_frame_index % args.frame_step == 0
                )

                if should_extract:
                    last_feature_result = runtime_extractor.extract_frame(
                        frame=current_frame,
                        bbox=(x1, y1, x2, y2),
                        occlusion=current_occlusion,
                        track_id=args.track_id,
                    )

                    sequence_buffer.add(
                        last_feature_result["feature_vector"],
                        metadata={
                            "source_frame_index": source_frame_index,
                            "bbox": (x1, y1, x2, y2),
                            "occlusion": current_occlusion,
                        },
                    )

                    accepted_frame_count += 1

                    if (
                        sequence_buffer.is_ready
                        and (
                            last_prediction is None
                            or accepted_frame_count % args.predict_every == 0
                        )
                    ):
                        last_prediction = predictor.predict(
                            sequence_buffer.get_sequence(),
                            random_seed=1000 + prediction_count,
                        )
                        prediction_count += 1

                put_text(
                    display_frame,
                    f"Track: OK | bbox=({x1},{y1},{x2},{y2})",
                    28,
                )
            else:
                tracker_failures += 1
                put_text(display_frame, "Track: FAILED", 28)

            progress = sequence_buffer.progress
            put_text(
                display_frame,
                (
                    f"Buffer: {progress['collected']}/"
                    f"{progress['required']} | "
                    f"Occlusion input: {current_occlusion}"
                ),
                55,
            )

            if last_feature_result is not None:
                state, state_probability = reliability_state(
                    last_feature_result
                )
                put_text(
                    display_frame,
                    (
                        f"Bayesian reliability: {state} "
                        f"({state_probability:.3f})"
                    ),
                    82,
                )

            if last_prediction is None:
                put_text(
                    display_frame,
                    "Intent: collecting 30-frame evidence...",
                    109,
                )
            else:
                put_text(
                    display_frame,
                    (
                        f"Intent: "
                        f"{last_prediction['predicted_intent'].upper()}"
                    ),
                    109,
                    scale=0.72,
                )
                put_text(
                    display_frame,
                    (
                        f"P(crossing): "
                        f"{last_prediction['crossing_probability']:.3f} | "
                        f"confidence: "
                        f"{last_prediction['confidence']:.3f}"
                    ),
                    138,
                )
                put_text(
                    display_frame,
                    (
                        f"entropy: "
                        f"{last_prediction['normalized_entropy']:.3f} | "
                        f"variance: "
                        f"{last_prediction['crossing_probability_variance']:.6f}"
                    ),
                    165,
                )

            put_text(
                display_frame,
                "Keys: 1=low  2=medium  3=high  q=quit",
                frame_height - 18,
                scale=0.52,
            )

            writer.write(display_frame)

            if not args.no_display:
                cv2.imshow("Runtime intent prediction", display_frame)
                key = cv2.waitKey(1) & 0xFF

                if key in (ord("q"), 27):
                    break
                if key == ord("1"):
                    current_occlusion = "low"
                elif key == ord("2"):
                    current_occlusion = "medium"
                elif key == ord("3"):
                    current_occlusion = "high"

            ok, next_frame = capture.read()
            if not ok or next_frame is None:
                break

            source_frame_index += 1
            current_frame = next_frame

    finally:
        capture.release()
        writer.release()
        cv2.destroyAllWindows()

    print()
    print("=" * 78)
    print("VIDEO INFERENCE COMPLETE")
    print("=" * 78)
    print("Accepted feature frames :", accepted_frame_count)
    print("Intent predictions      :", prediction_count)
    print("Tracker failures        :", tracker_failures)
    print("Output video            :", output_path)

    if last_prediction is not None:
        print("Final predicted intent  :", last_prediction["predicted_intent"])
        print(
            "Final crossing prob.    :",
            f"{last_prediction['crossing_probability']:.6f}",
        )
        print(
            "Final confidence        :",
            f"{last_prediction['confidence']:.6f}",
        )
        print(
            "Final entropy           :",
            f"{last_prediction['normalized_entropy']:.6f}",
        )
    else:
        print(
            "No intent prediction was produced. The tracked pedestrian must "
            "remain visible for at least 30 accepted frames."
        )

    print("=" * 78)


if __name__ == "__main__":
    main()
