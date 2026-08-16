from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import pandas as pd

from utils.automatic_pedestrian_tracker import AutomaticPedestrianTracker
from utils.occlusion_aware_track_continuation import (
    OcclusionAwareTrackContinuation,
)


TEST_CSV = Path("datasets/processed/metadata/test.csv")
ANNOTATIONS = Path("datasets/processed/metadata/annotations.csv")
FRAMES_ROOT = Path("datasets/processed/frames")

DEFAULT_MODEL = Path(
    "outputs/phase9/yolo_pedestrian/"
    "yolo11n_pie_occlusion_v2/weights/best.pt"
)
SELECTED_TRACKER = Path(
    "outputs/phase9/tracker_tuning/botsort_pie_selected.yaml"
)
TRACKER_SUMMARY = Path(
    "outputs/phase9/tracker_tuning/selected_tracker_summary.json"
)
DERIVATION = Path(
    "outputs/phase9/tracker_tuning/candidate_derivation.json"
)
OUTPUT_DIR = Path("outputs/phase9/track_continuation")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sequence-index", type=int, default=28)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--imgsz", type=int, default=960)
    return parser.parse_args()


def set_from_pedestrian_id(pedestrian_id: str) -> str:
    return f"set{int(str(pedestrian_id).split('_', 1)[0]):02d}"


def bbox_iou(a, b) -> float:
    ax1, ay1, ax2, ay2 = map(float, a)
    bx1, by1, bx2, by2 = map(float, b)

    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)

    iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
    inter = iw * ih

    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union = area_a + area_b - inter

    return float(inter / union) if union > 0 else 0.0


def longest_same_id_run(values) -> int:
    best = 0
    current = 0
    previous = None

    for value in values:
        if value is None:
            current = 0
            previous = None
        elif value == previous:
            current += 1
        else:
            current = 1
            previous = value

        best = max(best, current)

    return best


def main() -> None:
    args = parse_args()

    print("=" * 108)
    print("PHASE 9.5D - OCCLUSION-AWARE TRACK CONTINUATION SMOKE TEST")
    print("=" * 108)

    for path in (
        TEST_CSV,
        ANNOTATIONS,
        args.model,
        SELECTED_TRACKER,
        TRACKER_SUMMARY,
        DERIVATION,
    ):
        if not path.exists():
            raise FileNotFoundError(f"Required path not found: {path}")

    summary_data = json.loads(TRACKER_SUMMARY.read_text(encoding="utf-8"))
    inference_conf = float(summary_data["inference_conf_during_search"])

    continuation = OcclusionAwareTrackContinuation.from_validation_artifacts(
        DERIVATION
    )

    test = pd.read_csv(TEST_CSV).reset_index(drop=True)
    row = test.iloc[int(args.sequence_index)]

    video = str(row["video"])
    pedestrian_id = str(row["pedestrian_id"])
    dataset_set = set_from_pedestrian_id(pedestrian_id)
    frames = [int(v) for v in str(row["frames"]).split("|")]

    ann = pd.read_csv(ANNOTATIONS)
    ann["id"] = ann["id"].astype(str)
    ann["video"] = ann["video"].astype(str)
    ann["frame"] = pd.to_numeric(ann["frame"], errors="raise").astype(int)

    tracker = AutomaticPedestrianTracker(
    model_path=args.model,
    tracker_config=str(SELECTED_TRACKER),
    conf=inference_conf,
    imgsz=int(args.imgsz),
    device="cuda:0",
)
    tracker.reset()
    continuation.reset()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    raw_ids = []
    continued_ids = []
    records = []

    raw_matches = 0
    continued_matches = 0
    raw_iou_sum = 0.0
    continued_iou_sum = 0.0

    print("Detector              :", args.model)
    print("Tracker               :", SELECTED_TRACKER)
    print("Detector conf         :", inference_conf)
    print(
        "Continuation horizon  :",
        continuation.max_missing_frames,
        "frames (validation p90 FULL-occlusion duration)",
    )
    print("Sequence              :", args.sequence_index, dataset_set, video, pedestrian_id)
    print()

    for step, frame_number in enumerate(frames, start=1):
        path = (
            FRAMES_ROOT
            / dataset_set
            / video
            / f"frame_{frame_number:06d}.jpg"
        )
        frame = cv2.imread(str(path))
        if frame is None:
            raise FileNotFoundError(f"Could not load frame: {path}")

        gt_rows = ann[
            (ann["video"] == video)
            & (ann["frame"] == frame_number)
            & (ann["id"] == pedestrian_id)
        ]
        if gt_rows.empty:
            raise RuntimeError(
                f"Missing GT row for {video} frame {frame_number} ped {pedestrian_id}"
            )

        gt = gt_rows.iloc[0]
        gt_bbox = (
            float(gt["x1"]),
            float(gt["y1"]),
            float(gt["x2"]),
            float(gt["y2"]),
        )

        observed = [
            t
            for t in tracker.track_frame(frame)
            if int(t.track_id) >= 0
        ]

        active = continuation.update(
            observed_tracks=observed,
            frame_index=step,
            frame_shape=frame.shape,
        )

        raw_best_iou = 0.0
        raw_best_id = None
        for t in observed:
            iou = bbox_iou(gt_bbox, t.bbox)
            if iou > raw_best_iou:
                raw_best_iou = iou
                raw_best_id = int(t.track_id)

        cont_best_iou = 0.0
        cont_best_id = None
        cont_best_source = None
        cont_best_missing = None

        for t in active:
            iou = bbox_iou(gt_bbox, t.bbox)
            if iou > cont_best_iou:
                cont_best_iou = iou
                cont_best_id = int(t.stable_track_id)
                cont_best_source = t.source
                cont_best_missing = int(t.missing_frames)

        raw_ids.append(raw_best_id if raw_best_iou >= 0.10 else None)
        continued_ids.append(cont_best_id if cont_best_iou >= 0.10 else None)

        raw_matches += int(raw_best_iou >= 0.10)
        continued_matches += int(cont_best_iou >= 0.10)
        raw_iou_sum += raw_best_iou
        continued_iou_sum += cont_best_iou

        records.append({
            "step": step,
            "frame": frame_number,
            "source_occlusion_reference": str(gt["occlusion"]),
            "raw_valid_track_count": len(observed),
            "continued_active_track_count": len(active),
            "raw_best_iou": raw_best_iou,
            "raw_best_id": raw_best_id,
            "continued_best_iou": cont_best_iou,
            "continued_best_id": cont_best_id,
            "continued_best_source": cont_best_source,
            "continued_best_missing_frames": cont_best_missing,
        })

        print(
            f"Frame {step:02d}/30 | "
            f"occ={str(gt['occlusion']):5s} | "
            f"raw_tracks={len(observed):2d} | "
            f"active={len(active):2d} | "
            f"raw_IoU={raw_best_iou:.3f} | "
            f"cont_IoU={cont_best_iou:.3f} | "
            f"cont_ID={cont_best_id} | "
            f"source={cont_best_source}"
        )

    n = len(frames)
    raw_recall = raw_matches / n
    cont_recall = continued_matches / n
    raw_mean_iou = raw_iou_sum / n
    cont_mean_iou = continued_iou_sum / n
    raw_run = longest_same_id_run(raw_ids)
    cont_run = longest_same_id_run(continued_ids)

    csv_path = OUTPUT_DIR / f"sequence_{args.sequence_index}_track_continuation.csv"
    pd.DataFrame(records).to_csv(csv_path, index=False)

    result = {
        "sequence_index": int(args.sequence_index),
        "continuation_horizon_frames": continuation.max_missing_frames,
        "raw_tracker": {
            "recall_iou_0_10": raw_recall,
            "mean_best_iou": raw_mean_iou,
            "longest_same_id_run": raw_run,
        },
        "with_continuation": {
            "recall_iou_0_10": cont_recall,
            "mean_best_iou": cont_mean_iou,
            "longest_same_id_run": cont_run,
        },
        "annotation_used_as_runtime_input": False,
    }

    json_path = OUTPUT_DIR / f"sequence_{args.sequence_index}_track_continuation_summary.json"
    json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print()
    print("-" * 108)
    print("TRACK CONTINUATION SUMMARY")
    print("-" * 108)
    print("Raw tracker recall @ IoU>=0.10      :", f"{raw_recall:.4f}")
    print("Continuation recall @ IoU>=0.10     :", f"{cont_recall:.4f}")
    print("Raw mean best IoU                   :", f"{raw_mean_iou:.4f}")
    print("Continuation mean best IoU          :", f"{cont_mean_iou:.4f}")
    print("Raw longest same-ID run             :", f"{raw_run}/{n}")
    print("Continuation longest same-ID run    :", f"{cont_run}/{n}")
    print()
    print("CSV     :", csv_path)
    print("Summary :", json_path)
    print("Status: PASSED")
    print("=" * 108)


if __name__ == "__main__":
    main()
