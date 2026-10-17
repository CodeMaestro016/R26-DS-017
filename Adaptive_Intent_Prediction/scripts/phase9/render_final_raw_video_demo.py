from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import pandas as pd
import torch

from utils.full_automatic_intent_runtime import FullAutomaticIntentRuntime


TEST_METADATA = Path("datasets/processed/metadata/test.csv")
RAW_VIDEO_ROOT = Path("datasets/raw/videos")
OUTPUT_DIR = Path("outputs/phase9/final_raw_video_demo")

PANEL_WIDTH = 620

# UI-only visualization colors (BGR).
COLOR_CROSSING = (50, 50, 235)
COLOR_NOT_CROSSING = (70, 200, 90)
COLOR_OBSERVE = (0, 210, 255)
COLOR_WARMING = (180, 180, 180)
COLOR_OBSERVED = (255, 200, 70)
COLOR_PREDICTED = (180, 100, 255)
COLOR_TEXT = (235, 235, 235)
COLOR_DIM = (170, 170, 170)
COLOR_PANEL_BG = (24, 24, 24)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Render the final raw-video demo dashboard for the full automatic "
            "occluded-pedestrian intent pipeline."
        )
    )
    parser.add_argument("--sequence-index", type=int, default=28)
    parser.add_argument("--context", type=int, default=120)
    parser.add_argument("--max-frames", type=int, default=0)
    parser.add_argument("--device", type=str, default=None)
    parser.add_argument("--output-fps", type=float, default=0.0)
    parser.add_argument("--hold-seconds", type=float, default=2.0)
    return parser.parse_args()


def dataset_set_from_pedestrian_id(pedestrian_id: str) -> str:
    prefix = str(pedestrian_id).split("_", 1)[0]
    return f"set{int(prefix):02d}"


def action_color(action_name: str | None) -> tuple[int, int, int]:
    if action_name == "COMMIT_CROSSING":
        return COLOR_CROSSING
    if action_name == "COMMIT_NOT_CROSSING":
        return COLOR_NOT_CROSSING
    if action_name == "OBSERVE_MORE":
        return COLOR_OBSERVE
    return COLOR_WARMING


def clip_bbox(
    bbox: tuple[float, float, float, float],
    width: int,
    height: int,
) -> tuple[int, int, int, int]:
    x1, y1, x2, y2 = bbox
    x1 = int(np.clip(round(x1), 0, width - 1))
    y1 = int(np.clip(round(y1), 0, height - 1))
    x2 = int(np.clip(round(x2), x1 + 1, width))
    y2 = int(np.clip(round(y2), y1 + 1, height))
    return x1, y1, x2, y2


def put_text(
    image: np.ndarray,
    text: str,
    x: int,
    y: int,
    *,
    scale: float = 0.55,
    color: tuple[int, int, int] = COLOR_TEXT,
    thickness: int = 1,
) -> int:
    cv2.putText(
        image,
        str(text),
        (int(x), int(y)),
        cv2.FONT_HERSHEY_SIMPLEX,
        float(scale),
        color,
        int(thickness),
        cv2.LINE_AA,
    )
    return y + int(24 * max(scale / 0.55, 0.85))


def wrap_text(
    text: str,
    max_chars: int,
) -> list[str]:
    words = str(text).split()
    if not words:
        return []

    lines = []
    current = words[0]

    for word in words[1:]:
        candidate = current + " " + word
        if len(candidate) <= max_chars:
            current = candidate
        else:
            lines.append(current)
            current = word

    lines.append(current)
    return lines


def draw_track_box(
    canvas: np.ndarray,
    track: dict[str, Any],
) -> None:
    height, width = canvas.shape[:2]
    x1, y1, x2, y2 = clip_bbox(
        tuple(track["bbox"]),
        width,
        height,
    )

    runtime_result = track.get("runtime_result")

    if runtime_result is None:
        color = COLOR_WARMING
        decision_label = "WARMING_UP"
    else:
        decision_label = str(runtime_result["agent_action_name"])
        color = action_color(decision_label)

    # Predicted continuation gets a thinner/different visual cue while
    # preserving decision color on the text label.
    source = str(track["track_source"])
    box_color = (
        color
        if source == "OBSERVED"
        else COLOR_PREDICTED
    )

    cv2.rectangle(
        canvas,
        (x1, y1),
        (x2, y2),
        box_color,
        2,
    )

    label = (
        f"ID {track['track_id']} | "
        f"{source} | "
        f"occ={track['automatic_occlusion']} | "
        f"{track['buffer_size']}/30"
    )

    label_y = max(22, y1 - 8)

    cv2.putText(
        canvas,
        label,
        (x1, label_y),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.48,
        box_color,
        1,
        cv2.LINE_AA,
    )

    if runtime_result is not None:
        result_text = (
            f"{runtime_result['intent_prediction']} | "
            f"Pcross={runtime_result['p_crossing']:.2f} | "
            f"{decision_label}"
        )
        cv2.putText(
            canvas,
            result_text,
            (x1, min(height - 8, y2 + 20)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.48,
            color,
            1,
            cv2.LINE_AA,
        )


def select_primary_track(
    tracks: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if not tracks:
        return None

    def key(track: dict[str, Any]):
        ready = int(track["runtime_result"] is not None)
        observed = int(track["track_source"] == "OBSERVED")
        buffer_size = int(track["buffer_size"])
        confidence = track["detector_confidence"]
        confidence = (
            -1.0
            if confidence is None
            else float(confidence)
        )
        return (
            ready,
            buffer_size,
            observed,
            confidence,
        )

    return max(tracks, key=key)


def draw_panel(
    frame: np.ndarray,
    tracks: list[dict[str, Any]],
    frame_index: int,
    start_frame: int,
    end_frame: int,
    ready_total: int,
    last_ready_result: dict[str, Any] | None,
) -> np.ndarray:
    height, width = frame.shape[:2]
    panel = np.full(
        (height, PANEL_WIDTH, 3),
        COLOR_PANEL_BG,
        dtype=np.uint8,
    )

    y = 34
    y = put_text(
        panel,
        "ADAPTIVE INTENT PREDICTION",
        18,
        y,
        scale=0.72,
        thickness=2,
    )
    y = put_text(
        panel,
        "Full Automatic Raw-Video Runtime",
        18,
        y + 4,
        scale=0.52,
        color=COLOR_DIM,
    )

    cv2.line(
        panel,
        (16, y + 6),
        (PANEL_WIDTH - 16, y + 6),
        (80, 80, 80),
        1,
    )
    y += 35

    y = put_text(
        panel,
        f"Frame: {frame_index}  ({frame_index-start_frame+1}/{end_frame-start_frame+1})",
        18,
        y,
    )
    y = put_text(
        panel,
        f"Active automatic tracks: {len(tracks)}",
        18,
        y,
    )
    y = put_text(
        panel,
        f"Intent decisions emitted: {ready_total}",
        18,
        y,
    )

    primary = select_primary_track(tracks)

    if primary is None:
        y += 20
        y = put_text(
            panel,
            "No active pedestrian track",
            18,
            y,
            color=COLOR_WARMING,
            scale=0.62,
            thickness=2,
        )

        if last_ready_result is not None:
            y += 25
            y = put_text(
                panel,
                "Last emitted decision",
                18,
                y,
                scale=0.60,
                thickness=2,
            )
            rr = last_ready_result
            y = put_text(
                panel,
                f"Intent: {rr['intent_prediction']}",
                18,
                y,
            )
            y = put_text(
                panel,
                f"Agent: {rr['agent_action_name']}",
                18,
                y,
                color=action_color(rr["agent_action_name"]),
            )

        return np.concatenate(
            [frame, panel],
            axis=1,
        )

    y += 22
    y = put_text(
        panel,
        f"PRIMARY TRACK #{primary['track_id']}",
        18,
        y,
        scale=0.64,
        thickness=2,
    )
    y = put_text(
        panel,
        f"Track source: {primary['track_source']}",
        18,
        y,
        color=(
            COLOR_OBSERVED
            if primary["track_source"] == "OBSERVED"
            else COLOR_PREDICTED
        ),
    )
    y = put_text(
        panel,
        f"Buffer: {primary['buffer_size']}/30",
        18,
        y,
    )
    y = put_text(
        panel,
        f"Automatic occlusion: {primary['automatic_occlusion']}",
        18,
        y,
    )

    op = primary["occlusion_probabilities"]
    y = put_text(
        panel,
        (
            "Pocc "
            f"N={op['none']:.2f} "
            f"P={op['part']:.2f} "
            f"F={op['full']:.2f}"
        ),
        18,
        y,
        scale=0.49,
        color=COLOR_DIM,
    )

    rp = primary["reliability_probabilities"]
    y = put_text(
        panel,
        (
            "Reliability "
            f"L={rp['low']:.2f} "
            f"M={rp['medium']:.2f} "
            f"H={rp['high']:.2f}"
        ),
        18,
        y,
        scale=0.49,
        color=COLOR_DIM,
    )

    runtime_result = primary["runtime_result"]

    y += 22
    cv2.line(
        panel,
        (16, y),
        (PANEL_WIDTH - 16, y),
        (80, 80, 80),
        1,
    )
    y += 30

    if runtime_result is None:
        y = put_text(
            panel,
            "STATUS: WARMING UP",
            18,
            y,
            scale=0.68,
            color=COLOR_WARMING,
            thickness=2,
        )
        y = put_text(
            panel,
            "Waiting for 30-frame evidence window",
            18,
            y,
            color=COLOR_DIM,
        )
        return np.concatenate(
            [frame, panel],
            axis=1,
        )

    rr = runtime_result
    color = action_color(
        rr["agent_action_name"]
    )

    y = put_text(
        panel,
        f"INTENT: {rr['intent_prediction']}",
        18,
        y,
        scale=0.72,
        color=color,
        thickness=2,
    )
    y = put_text(
        panel,
        f"P(Crossing): {rr['p_crossing']:.3f}",
        18,
        y,
        scale=0.62,
    )
    y = put_text(
        panel,
        f"Confidence: {rr['confidence']:.3f}",
        18,
        y,
    )
    y = put_text(
        panel,
        (
            "Predictive entropy: "
            f"{rr['normalized_predictive_entropy']:.3f}"
        ),
        18,
        y,
    )
    y = put_text(
        panel,
        (
            "Mutual information: "
            f"{rr['mutual_information']:.4f}"
        ),
        18,
        y,
    )

    y += 18
    y = put_text(
        panel,
        f"AGENT: {rr['agent_action_name']}",
        18,
        y,
        scale=0.66,
        color=color,
        thickness=2,
    )
    y = put_text(
        panel,
        (
            "Agent probability: "
            f"{rr['agent_action_probability']:.3f}"
        ),
        18,
        y,
    )
    y = put_text(
        panel,
        f"AV signal: {rr['av_interface_signal']}",
        18,
        y,
        scale=0.50,
        color=color,
    )

    y += 18
    y = put_text(
        panel,
        (
            "Explanation group: "
            f"{rr['dominant_explanation_group']}"
        ),
        18,
        y,
        scale=0.55,
        thickness=2,
    )

    for line in wrap_text(
        rr["explanation"],
        max_chars=58,
    )[:5]:
        y = put_text(
            panel,
            line,
            18,
            y,
            scale=0.46,
            color=COLOR_DIM,
        )

    return np.concatenate(
        [frame, panel],
        axis=1,
    )


def main() -> None:
    args = parse_args()

    print("=" * 112)
    print("PHASE 9.8 - FINAL AUTOMATIC RAW-VIDEO DEMO DASHBOARD")
    print("=" * 112)

    metadata = pd.read_csv(
        TEST_METADATA
    ).reset_index(drop=True)

    row = metadata.iloc[
        int(args.sequence_index)
    ]

    dataset_set = dataset_set_from_pedestrian_id(
        str(row["pedestrian_id"])
    )
    video_name = str(row["video"])

    video_path = (
        RAW_VIDEO_ROOT
        / dataset_set
        / f"{video_name}.mp4"
    )

    if not video_path.exists():
        raise FileNotFoundError(
            f"Raw video not found: {video_path}"
        )

    start_frame = max(
        0,
        int(row["start_frame"])
        - int(args.context),
    )
    end_frame = (
        int(row["end_frame"])
        + int(args.context)
    )

    if int(args.max_frames) > 0:
        end_frame = min(
            end_frame,
            start_frame
            + int(args.max_frames)
            - 1,
        )

    if args.device is None:
        device = (
            "cuda:0"
            if torch.cuda.is_available()
            else "cpu"
        )
    else:
        device = str(args.device)

    runtime = FullAutomaticIntentRuntime(
        device=device
    )
    runtime.reset()

    capture = cv2.VideoCapture(
        str(video_path)
    )
    if not capture.isOpened():
        raise RuntimeError(
            f"Could not open video: {video_path}"
        )

    source_fps = float(
        capture.get(
            cv2.CAP_PROP_FPS
        )
    )
    if (
        not np.isfinite(source_fps)
        or source_fps <= 0
    ):
        source_fps = 30.0

    output_fps = (
        float(args.output_fps)
        if float(args.output_fps) > 0
        else source_fps
    )

    width = int(
        capture.get(
            cv2.CAP_PROP_FRAME_WIDTH
        )
    )
    height = int(
        capture.get(
            cv2.CAP_PROP_FRAME_HEIGHT
        )
    )

    capture.set(
        cv2.CAP_PROP_POS_FRAMES,
        float(start_frame),
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    video_out = (
        OUTPUT_DIR
        / (
            f"final_raw_video_demo_"
            f"sequence_{int(args.sequence_index)}.mp4"
        )
    )

    summary_out = (
        OUTPUT_DIR
        / (
            f"final_raw_video_demo_"
            f"sequence_{int(args.sequence_index)}_summary.json"
        )
    )

    writer = cv2.VideoWriter(
        str(video_out),
        cv2.VideoWriter_fourcc(*"mp4v"),
        output_fps,
        (
            width + PANEL_WIDTH,
            height,
        ),
    )

    if not writer.isOpened():
        raise RuntimeError(
            f"Could not create output video: {video_out}"
        )

    processed = 0
    decisions = 0
    unique_tracks = set()
    last_dashboard_frame = None
    last_ready_result = None
    last_ready_track = None

    print("Input video :", video_path)
    print("Output video:", video_out)
    print("Frame range :", start_frame, "->", end_frame)
    print("FPS         :", output_fps)
    print("Device      :", device)
    print()

    current_frame = int(start_frame)

    while current_frame <= end_frame:
        ok, frame = capture.read()
        if not ok:
            break

        result = runtime.process_frame(
            frame=frame,
            frame_index=current_frame,
        )

        tracks = result["tracks"]

        for track in tracks:
            unique_tracks.add(
                int(track["track_id"])
            )

            if track["runtime_result"] is not None:
                decisions += 1
                last_ready_result = track["runtime_result"]
                last_ready_track = int(
                    track["track_id"]
                )

        visual = frame.copy()

        for track in tracks:
            draw_track_box(
                visual,
                track,
            )

        dashboard = draw_panel(
            frame=visual,
            tracks=tracks,
            frame_index=current_frame,
            start_frame=start_frame,
            end_frame=end_frame,
            ready_total=decisions,
            last_ready_result=last_ready_result,
        )

        writer.write(dashboard)
        last_dashboard_frame = dashboard

        processed += 1

        if (
            processed % 10 == 0
            or tracks
        ):
            print(
                f"Frame {current_frame} | "
                f"tracks={len(tracks)} | "
                f"decisions={decisions}"
            )

        current_frame += 1

    capture.release()

    if (
        last_dashboard_frame is not None
        and float(args.hold_seconds) > 0
    ):
        hold_frames = int(
            round(
                output_fps
                * float(args.hold_seconds)
            )
        )

        for _ in range(hold_frames):
            writer.write(
                last_dashboard_frame
            )

    writer.release()

    summary = {
        "phase": "9.8",
        "input_video": str(video_path),
        "output_video": str(video_out),
        "processed_frames": int(processed),
        "automatic_track_count": int(
            len(unique_tracks)
        ),
        "intent_decision_frames": int(
            decisions
        ),
        "at_least_one_intent_decision": bool(
            decisions > 0
        ),
        "last_ready_track_id": last_ready_track,
        "runtime_annotation_inputs": {
            "bbox": False,
            "pedestrian_id": False,
            "occlusion": False,
            "crossing_label": False,
        },
        "display_note": (
            "Bounding-box/action colors are visualization only and are not "
            "a safety-risk scoring mechanism."
        ),
    }

    summary_out.write_text(
        json.dumps(
            summary,
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print("-" * 112)
    print("FINAL RAW-VIDEO DEMO SUMMARY")
    print("-" * 112)
    print("Frames processed           :", processed)
    print("Automatic track IDs        :", len(unique_tracks))
    print("Intent decision frames     :", decisions)
    print("At least one intent result :", decisions > 0)
    print("PIE bbox runtime input      :", False)
    print("PIE ID runtime input        :", False)
    print("PIE occlusion runtime input :", False)
    print("PIE crossing runtime input  :", False)
    print()
    print("Final MP4 :", video_out)
    print("Summary   :", summary_out)
    print("Status: PASSED")
    print("=" * 112)


if __name__ == "__main__":
    main()
