from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np
import torch

from utils.full_automatic_intent_runtime import FullAutomaticIntentRuntime
from scripts.phase9.render_final_raw_video_demo import (
    PANEL_WIDTH,
    draw_panel,
    draw_track_box,
)


DEFAULT_OUTPUT_DIR = Path("outputs/phase9/external_video_demo")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the full automatic intent pipeline on any video file."
    )
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--start-frame", type=int, default=0)
    parser.add_argument(
        "--max-frames",
        type=int,
        default=0,
        help="0 means process until the video ends.",
    )
    parser.add_argument("--device", type=str, default=None)
    parser.add_argument("--output-fps", type=float, default=0.0)
    parser.add_argument("--hold-seconds", type=float, default=2.0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    video_path = args.video.resolve()

    if not video_path.exists():
        raise FileNotFoundError(f"Input video not found: {video_path}")

    if video_path.suffix.lower() not in {".mp4", ".avi", ".mov", ".mkv", ".m4v"}:
        raise ValueError(f"Unsupported video extension: {video_path.suffix}")

    if args.device is None:
        device = "cuda:0" if torch.cuda.is_available() else "cpu"
    else:
        device = str(args.device)

    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    source_fps = float(capture.get(cv2.CAP_PROP_FPS))
    if not np.isfinite(source_fps) or source_fps <= 0:
        source_fps = 30.0

    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))

    start_frame = max(0, int(args.start_frame))
    if total_frames > 0:
        start_frame = min(start_frame, total_frames - 1)

    if int(args.max_frames) > 0:
        end_frame = start_frame + int(args.max_frames) - 1
    elif total_frames > 0:
        end_frame = total_frames - 1
    else:
        end_frame = start_frame + 10_000_000

    if total_frames > 0:
        end_frame = min(end_frame, total_frames - 1)

    output_fps = float(args.output_fps) if float(args.output_fps) > 0 else source_fps

    DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = (
        args.output.resolve()
        if args.output is not None
        else (DEFAULT_OUTPUT_DIR / f"{video_path.stem}_intent_demo.mp4").resolve()
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path = output_path.with_name(output_path.stem + "_summary.json")

    writer = cv2.VideoWriter(
        str(output_path),
        cv2.VideoWriter_fourcc(*"mp4v"),
        output_fps,
        (width + PANEL_WIDTH, height),
    )
    if not writer.isOpened():
        capture.release()
        raise RuntimeError(f"Could not create output video: {output_path}")

    capture.set(cv2.CAP_PROP_POS_FRAMES, float(start_frame))

    runtime = FullAutomaticIntentRuntime(device=device)
    runtime.reset()

    print("=" * 112)
    print("PHASE 9.9 - EXTERNAL VIDEO FULL AUTOMATIC DEMO")
    print("=" * 112)
    print("Input video    :", video_path)
    print("Resolution     :", f"{width}x{height}")
    print("Source FPS     :", source_fps)
    print("Frame window   :", start_frame, "->", end_frame)
    print("Runtime device :", device)
    print("Runtime input  : RGB video only")
    print()

    current_frame = start_frame
    processed = 0
    decision_count = 0
    unique_tracks: set[int] = set()
    last_ready_result = None
    last_dashboard = None

    while current_frame <= end_frame:
        ok, frame = capture.read()
        if not ok:
            break

        result = runtime.process_frame(frame=frame, frame_index=current_frame)
        tracks = result["tracks"]

        for track in tracks:
            unique_tracks.add(int(track["track_id"]))
            if track["runtime_result"] is not None:
                decision_count += 1
                last_ready_result = track["runtime_result"]

        visual = frame.copy()
        for track in tracks:
            draw_track_box(visual, track)

        dashboard = draw_panel(
            frame=visual,
            tracks=tracks,
            frame_index=current_frame,
            start_frame=start_frame,
            end_frame=end_frame,
            ready_total=decision_count,
            last_ready_result=last_ready_result,
        )

        writer.write(dashboard)
        last_dashboard = dashboard
        processed += 1

        if processed % 30 == 0 or tracks:
            ready_now = sum(
                int(track["runtime_result"] is not None)
                for track in tracks
            )
            print(
                f"Frame {current_frame} | "
                f"tracks={len(tracks)} | "
                f"ready_now={ready_now} | "
                f"decisions_total={decision_count}"
            )

        current_frame += 1

    capture.release()

    if last_dashboard is not None and float(args.hold_seconds) > 0:
        hold_frames = int(round(output_fps * float(args.hold_seconds)))
        for _ in range(hold_frames):
            writer.write(last_dashboard)

    writer.release()

    summary = {
        "phase": "9.9",
        "input_video": str(video_path),
        "output_video": str(output_path),
        "processed_frames": int(processed),
        "automatic_track_count": int(len(unique_tracks)),
        "intent_decision_frames": int(decision_count),
        "at_least_one_intent_decision": bool(decision_count > 0),
        "runtime_inputs": {
            "rgb_video": True,
            "pie_bbox": False,
            "pie_pedestrian_id": False,
            "pie_occlusion": False,
            "pie_crossing_label": False,
        },
        "important_note": (
            "Without ground-truth annotations, an external video is a qualitative "
            "generalization demo rather than a new quantitative accuracy benchmark."
        ),
    }

    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print()
    print("-" * 112)
    print("EXTERNAL VIDEO DEMO SUMMARY")
    print("-" * 112)
    print("Frames processed           :", processed)
    print("Automatic track IDs        :", len(unique_tracks))
    print("Intent decision frames     :", decision_count)
    print("At least one intent result :", decision_count > 0)
    print("Annotation input used      :", False)
    print()
    print("Output MP4 :", output_path)
    print("Summary    :", summary_path)
    print("Status: PASSED")
    print("=" * 112)


if __name__ == "__main__":
    main()
