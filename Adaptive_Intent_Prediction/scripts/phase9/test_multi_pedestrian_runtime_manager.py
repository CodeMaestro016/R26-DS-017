from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

from utils.annotation_loader import AnnotationLoader
from utils.image_loader import ImageLoader
from utils.multi_pedestrian_runtime_manager import (
    MultiPedestrianRuntimeManager,
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
    "outputs/phase9"
)

DEFAULT_SEQUENCE_INDEX = 28
DEFAULT_DATASET_SET = "set01"


def parse_args() -> argparse.Namespace:
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


def parse_frames(
    value: Any,
) -> list[int]:
    if isinstance(value, str):
        normalized = (
            value
            .replace(",", "|")
            .replace(" ", "|")
        )
        return [
            int(item)
            for item
            in normalized.split("|")
            if item
        ]

    raise TypeError(
        f"Unsupported frames value: {value!r}"
    )


def main() -> None:
    args = parse_args()

    print("=" * 100)
    print("PHASE 9.3 - PER-TRACK ROLLING RUNTIME MANAGER TEST")
    print("=" * 100)

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
    ).reset_index(drop=True)

    sequence_index = int(
        args.sequence_index
    )

    if not 0 <= sequence_index < len(
        metadata
    ):
        raise IndexError(
            f"sequence-index must be between 0 and "
            f"{len(metadata) - 1}"
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
            f"Expected 30 frames, got {len(frames)}"
        )

    image_loader = ImageLoader(
        str(FRAME_ROOT)
    )

    annotation_loader = AnnotationLoader(
        str(ANNOTATION_PATH)
    )

    manager = MultiPedestrianRuntimeManager(
        explanation_steps=int(
            args.explanation_steps
        )
    )

    print(
        "Sequence index :",
        sequence_index,
    )
    print(
        "Sequence ID    :",
        row.get(
            "sequence_id",
            "unknown",
        ),
    )
    print(
        "Video          :",
        video,
    )
    print(
        "Track ID       :",
        pedestrian_id,
    )
    print(
        "Frames         :",
        frames[0],
        "->",
        frames[-1],
    )

    final_update = None
    history = []

    print()
    print("-" * 100)
    print("ROLLING TRACK BUFFER")
    print("-" * 100)

    for step, frame_number in enumerate(
        frames,
        start=1,
    ):
        frame = image_loader.load_frame(
            video=video,
            frame_number=frame_number,
            dataset_set=args.dataset_set,
        )

        annotation = (
            annotation_loader.get_annotation(
                video=video,
                frame=frame_number,
                pedestrian_id=pedestrian_id,
            )
        )

        if annotation is None:
            raise RuntimeError(
                f"Missing annotation for "
                f"{video} frame={frame_number} "
                f"pedestrian={pedestrian_id}"
            )

        update = manager.update_track(
            frame=frame,
            bbox=(
                annotation["x1"],
                annotation["y1"],
                annotation["x2"],
                annotation["y2"],
            ),
            track_id=pedestrian_id,
            occlusion=annotation[
                "occlusion"
            ],
        )

        history.append(
            update.to_dict()
        )

        print(
            f"Frame {step:02d}/30 | "
            f"source={frame_number} | "
            f"buffer={update.buffered_frames:02d}/30 | "
            f"status={update.status:10s} | "
            f"current_occ={update.normalized_occlusion:6s} | "
            f"max_occ={update.maximum_buffer_occlusion:6s}"
        )

        if step < 30 and update.ready:
            raise RuntimeError(
                "Track became READY before 30 observations."
            )

        if step == 30:
            final_update = update

    if final_update is None:
        raise RuntimeError(
            "No final track update was produced."
        )

    if not final_update.ready:
        raise RuntimeError(
            "Track did not become READY at observation 30."
        )

    if manager.get_track_buffer_size(
        pedestrian_id
    ) != 30:
        raise RuntimeError(
            "Final rolling buffer size is not 30."
        )

    result = (
        final_update.final_result
    )

    print()
    print("-" * 100)
    print("TRACK READY -> FINAL SYSTEM OUTPUT")
    print("-" * 100)

    print(
        "Intent prediction  :",
        result["intent_prediction"],
    )
    print(
        "P(crossing)        :",
        f"{result['p_crossing']:.6f}",
    )
    print(
        "Confidence         :",
        f"{result['confidence']:.6f}",
    )
    print(
        "Agent action       :",
        result["agent_action_name"],
    )
    print(
        "Agent probability  :",
        f"{result['agent_action_probability']:.6f}",
    )
    print(
        "Committed intent   :",
        result["committed_intent"],
    )
    print(
        "AV interface signal:",
        result["av_interface_signal"],
    )
    print(
        "Explanation group  :",
        result[
            "dominant_explanation_group"
        ],
    )
    print(
        "Explanation        :",
        result["explanation"],
    )

    print()
    print("-" * 100)
    print("TRACK LIFECYCLE TEST")
    print("-" * 100)

    print(
        "Active tracks before cleanup:",
        manager.active_track_ids(),
    )

    removed = manager.remove_missing_tracks(
        active_track_ids=[]
    )

    print(
        "Removed stale tracks        :",
        removed,
    )
    print(
        "Active tracks after cleanup :",
        manager.active_track_ids(),
    )
    print(
        "Buffer after cleanup        :",
        manager.get_track_buffer_size(
            pedestrian_id
        ),
    )

    if pedestrian_id not in removed:
        raise RuntimeError(
            "Expected test track was not removed."
        )

    if manager.get_track_buffer_size(
        pedestrian_id
    ) != 0:
        raise RuntimeError(
            "Track buffer was not cleared."
        )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        OUTPUT_DIR
        / (
            f"multi_track_manager_"
            f"sequence_{sequence_index}.json"
        )
    )

    payload = {
        "phase": "9.3",
        "sequence_index": (
            sequence_index
        ),
        "sequence_id": row.get(
            "sequence_id",
            "unknown",
        ),
        "video": video,
        "pedestrian_id": (
            pedestrian_id
        ),
        "warmup_history": (
            history
        ),
        "final_result": result,
        "track_cleanup_passed": True,
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
        "The manager is detector/tracker agnostic. "
        "At deployment, an upstream tracker only needs to provide "
        "stable track_id + bbox + occlusion evidence for each pedestrian."
    )
    print("Status: PASSED")
    print("=" * 100)


if __name__ == "__main__":
    main()
