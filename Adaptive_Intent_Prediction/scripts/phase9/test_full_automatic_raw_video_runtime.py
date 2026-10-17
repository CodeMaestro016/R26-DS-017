from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import pandas as pd
import torch

from utils.full_automatic_intent_runtime import (
    FullAutomaticIntentRuntime,
)


TEST_METADATA = Path(
    "datasets/processed/metadata/test.csv"
)
RAW_VIDEO_ROOT = Path(
    "datasets/raw/videos"
)
OUTPUT_DIR = Path(
    "outputs/phase9/full_automatic_runtime"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the complete automatic perception-to-intent "
            "runtime on a raw PIE video clip without using bbox, "
            "pedestrian ID, occlusion, or crossing annotations."
        )
    )

    parser.add_argument(
        "--sequence-index",
        type=int,
        default=28,
        help=(
            "Used only to select the raw PIE video and a temporal "
            "diagnostic window. Its bbox/ID/occlusion/label are NOT "
            "passed to the runtime."
        ),
    )

    parser.add_argument(
        "--context",
        type=int,
        default=120,
        help=(
            "Extra raw frames before and after the selected "
            "30-frame diagnostic sequence."
        ),
    )

    parser.add_argument(
        "--max-frames",
        type=int,
        default=0,
        help=(
            "Optional cap after context expansion. 0 means "
            "process the entire selected window."
        ),
    )

    parser.add_argument(
        "--device",
        type=str,
        default=None,
        help=(
            "cpu or cuda:0. Default selects CUDA when the "
            "current environment supports it."
        ),
    )

    return parser.parse_args()


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


def serialize_for_json(
    value,
):
    import dataclasses
    import numpy as np

    if dataclasses.is_dataclass(
        value
    ):
        return {
            key: serialize_for_json(
                item
            )
            for key, item
            in dataclasses.asdict(
                value
            ).items()
        }

    if isinstance(
        value,
        dict,
    ):
        return {
            str(key): serialize_for_json(
                item
            )
            for key, item
            in value.items()
        }

    if isinstance(
        value,
        (list, tuple),
    ):
        return [
            serialize_for_json(
                item
            )
            for item in value
        ]

    if isinstance(
        value,
        np.ndarray,
    ):
        return value.tolist()

    if isinstance(
        value,
        np.generic,
    ):
        return value.item()

    return value


def main() -> None:
    args = parse_args()

    print("=" * 112)
    print(
        "PHASE 9.7B - FULL AUTOMATIC RAW-VIDEO "
        "PERCEPTION -> INTENT RUNTIME"
    )
    print("=" * 112)

    if not TEST_METADATA.exists():
        raise FileNotFoundError(
            f"Missing test metadata: {TEST_METADATA}"
        )

    metadata = pd.read_csv(
        TEST_METADATA
    ).reset_index(
        drop=True
    )

    sequence_index = int(
        args.sequence_index
    )

    if not (
        0
        <= sequence_index
        < len(metadata)
    ):
        raise IndexError(
            f"sequence-index must be in "
            f"[0,{len(metadata)-1}]"
        )

    row = metadata.iloc[
        sequence_index
    ]

    # Metadata below is used only to select a raw video/time window.
    # No target bbox/track ID/occlusion/crossing label is provided to runtime.
    dataset_set = (
        dataset_set_from_pedestrian_id(
            str(
                row[
                    "pedestrian_id"
                ]
            )
        )
    )

    video_name = str(
        row[
            "video"
        ]
    )

    video_path = (
        RAW_VIDEO_ROOT
        / dataset_set
        / f"{video_name}.mp4"
    )

    if not video_path.exists():
        raise FileNotFoundError(
            f"Raw PIE video not found: {video_path}"
        )

    start_frame = max(
        0,
        int(
            row[
                "start_frame"
            ]
        )
        - int(
            args.context
        ),
    )

    end_frame = (
        int(
            row[
                "end_frame"
            ]
        )
        + int(
            args.context
        )
    )

    if int(
        args.max_frames
    ) > 0:
        end_frame = min(
            end_frame,
            start_frame
            + int(
                args.max_frames
            )
            - 1,
        )

    if args.device is None:
        device = (
            "cuda:0"
            if torch.cuda.is_available()
            else "cpu"
        )
    else:
        device = str(
            args.device
        )

    runtime = (
        FullAutomaticIntentRuntime(
            device=device
        )
    )

    runtime.reset()

    capture = cv2.VideoCapture(
        str(
            video_path
        )
    )

    if not capture.isOpened():
        raise RuntimeError(
            f"Could not open raw video: {video_path}"
        )

    capture.set(
        cv2.CAP_PROP_POS_FRAMES,
        float(
            start_frame
        ),
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    frame_csv_path = (
        OUTPUT_DIR
        / (
            f"sequence_{sequence_index}_"
            "automatic_tracks.csv"
        )
    )

    decisions_path = (
        OUTPUT_DIR
        / (
            f"sequence_{sequence_index}_"
            "automatic_decisions.jsonl"
        )
    )

    summary_path = (
        OUTPUT_DIR
        / (
            f"sequence_{sequence_index}_"
            "runtime_summary.json"
        )
    )

    frame_rows = []
    decision_records = []

    processed = 0
    ready_events = 0
    observed_track_frames = 0
    predicted_track_frames = 0
    unique_track_ids = set()

    print(
        "Raw video       :",
        video_path,
    )
    print(
        "Frame window    :",
        start_frame,
        "->",
        end_frame,
    )
    print(
        "Runtime device  :",
        device,
    )
    print(
        "Important       : no PIE bbox, target track ID, "
        "occlusion label, or crossing label is passed into runtime."
    )
    print()

    current_frame = int(
        start_frame
    )

    while (
        current_frame
        <= end_frame
    ):
        ok, frame = capture.read()

        if not ok:
            break

        result = runtime.process_frame(
            frame=frame,
            frame_index=current_frame,
        )

        processed += 1

        tracks = result[
            "tracks"
        ]

        for track in tracks:
            track_id = int(
                track[
                    "track_id"
                ]
            )

            unique_track_ids.add(
                track_id
            )

            if (
                track[
                    "track_source"
                ]
                == "OBSERVED"
            ):
                observed_track_frames += 1
            else:
                predicted_track_frames += 1

            runtime_result = track[
                "runtime_result"
            ]

            decision = None

            if runtime_result is not None:
                ready_events += 1

                decision = {
                    "frame_index": (
                        current_frame
                    ),
                    "track_id": (
                        track_id
                    ),
                    "track_source": (
                        track[
                            "track_source"
                        ]
                    ),
                    "automatic_occlusion": (
                        track[
                            "automatic_occlusion"
                        ]
                    ),
                    "runtime_result": (
                        runtime_result
                    ),
                }

                decision_records.append(
                    decision
                )

            frame_rows.append(
                {
                    "frame_index": (
                        current_frame
                    ),
                    "track_id": (
                        track_id
                    ),
                    "raw_track_id": (
                        track[
                            "raw_track_id"
                        ]
                    ),
                    "track_source": (
                        track[
                            "track_source"
                        ]
                    ),
                    "missing_frames": (
                        track[
                            "missing_frames"
                        ]
                    ),
                    "detector_confidence": (
                        track[
                            "detector_confidence"
                        ]
                    ),
                    "automatic_occlusion": (
                        track[
                            "automatic_occlusion"
                        ]
                    ),
                    "p_occ_none": (
                        track[
                            "occlusion_probabilities"
                        ][
                            "none"
                        ]
                    ),
                    "p_occ_part": (
                        track[
                            "occlusion_probabilities"
                        ][
                            "part"
                        ]
                    ),
                    "p_occ_full": (
                        track[
                            "occlusion_probabilities"
                        ][
                            "full"
                        ]
                    ),
                    "p_rel_low": (
                        track[
                            "reliability_probabilities"
                        ][
                            "low"
                        ]
                    ),
                    "p_rel_medium": (
                        track[
                            "reliability_probabilities"
                        ][
                            "medium"
                        ]
                    ),
                    "p_rel_high": (
                        track[
                            "reliability_probabilities"
                        ][
                            "high"
                        ]
                    ),
                    "buffer_size": (
                        track[
                            "buffer_size"
                        ]
                    ),
                    "status": (
                        track[
                            "status"
                        ]
                    ),
                    "intent_prediction": (
                        None
                        if runtime_result is None
                        else runtime_result[
                            "intent_prediction"
                        ]
                    ),
                    "p_crossing": (
                        None
                        if runtime_result is None
                        else runtime_result[
                            "p_crossing"
                        ]
                    ),
                    "confidence": (
                        None
                        if runtime_result is None
                        else runtime_result[
                            "confidence"
                        ]
                    ),
                    "agent_action": (
                        None
                        if runtime_result is None
                        else runtime_result[
                            "agent_action_name"
                        ]
                    ),
                    "agent_action_probability": (
                        None
                        if runtime_result is None
                        else runtime_result[
                            "agent_action_probability"
                        ]
                    ),
                    "av_interface_signal": (
                        None
                        if runtime_result is None
                        else runtime_result[
                            "av_interface_signal"
                        ]
                    ),
                }
            )

        if (
            processed % 10 == 0
            or tracks
        ):
            ready_count = sum(
                int(
                    track[
                        "runtime_result"
                    ]
                    is not None
                )
                for track in tracks
            )

            print(
                f"Frame {current_frame} | "
                f"raw_tracks={result['raw_tracker_count']} | "
                f"active={result['active_continued_track_count']} | "
                f"ready={ready_count}"
            )

        current_frame += 1

    capture.release()

    pd.DataFrame(
        frame_rows
    ).to_csv(
        frame_csv_path,
        index=False,
    )

    with decisions_path.open(
        "w",
        encoding="utf-8",
    ) as handle:
        for record in decision_records:
            handle.write(
                json.dumps(
                    serialize_for_json(
                        record
                    ),
                    ensure_ascii=False,
                )
                + "\n"
            )

    summary = {
        "phase": "9.7B",
        "raw_video": str(
            video_path
        ),
        "selection_sequence_index": (
            sequence_index
        ),
        "processed_frame_window": {
            "start": int(
                start_frame
            ),
            "end_requested": int(
                end_frame
            ),
            "frames_processed": int(
                processed
            ),
        },
        "device": device,
        "runtime_inputs": {
            "raw_rgb_video": True,
            "pie_bbox": False,
            "pie_target_track_id": False,
            "pie_occlusion_label": False,
            "pie_crossing_label": False,
        },
        "unique_automatic_track_ids": sorted(
            int(value)
            for value in unique_track_ids
        ),
        "unique_automatic_track_count": (
            len(
                unique_track_ids
            )
        ),
        "observed_track_frames": int(
            observed_track_frames
        ),
        "predicted_continuation_frames": int(
            predicted_track_frames
        ),
        "ready_intent_events": int(
            ready_events
        ),
        "at_least_one_full_automatic_intent_decision": bool(
            ready_events > 0
        ),
        "outputs": {
            "frame_tracks_csv": str(
                frame_csv_path
            ),
            "decisions_jsonl": str(
                decisions_path
            ),
        },
        "important_note": (
            "The chosen test.csv row is used only to select a raw "
            "video and temporal window. Its target bbox, pedestrian "
            "ID, occlusion label, and crossing label are not provided "
            "to the automatic runtime."
        ),
    }

    summary_path.write_text(
        json.dumps(
            summary,
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print("-" * 112)
    print(
        "FULL AUTOMATIC RUNTIME SUMMARY"
    )
    print("-" * 112)
    print(
        "Frames processed                       :",
        processed,
    )
    print(
        "Unique automatic track IDs             :",
        len(
            unique_track_ids
        ),
    )
    print(
        "Observed automatic track-frames        :",
        observed_track_frames,
    )
    print(
        "Predicted continuation track-frames    :",
        predicted_track_frames,
    )
    print(
        "Full 30-frame intent decisions emitted :",
        ready_events,
    )
    print(
        "At least one automatic intent decision :",
        ready_events > 0,
    )
    print(
        "PIE bbox used as runtime input          :",
        False,
    )
    print(
        "PIE occlusion used as runtime input     :",
        False,
    )
    print(
        "PIE crossing label used as runtime input:",
        False,
    )
    print()
    print(
        "Tracks CSV    :",
        frame_csv_path,
    )
    print(
        "Decisions JSONL:",
        decisions_path,
    )
    print(
        "Summary       :",
        summary_path,
    )

    if ready_events == 0:
        print()
        print(
            "NOTE: Integration completed, but no automatic "
            "track accumulated 30 runtime observations in this "
            "diagnostic window. Increase --context or choose a "
            "longer raw-video window before the final MP4 demo."
        )

    print(
        "Status: PASSED"
    )
    print("=" * 112)


if __name__ == "__main__":
    main()
