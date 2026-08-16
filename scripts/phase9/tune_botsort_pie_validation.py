from __future__ import annotations

import argparse
import itertools
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import pandas as pd
from ultralytics import YOLO


ANNOTATIONS = Path("datasets/processed/metadata/annotations.csv")
FRAMES_ROOT = Path("datasets/processed/frames")
DETECTOR_SPLIT = Path("datasets/processed/yolo_pedestrian/video_split.json")

DEFAULT_MODEL = Path(
    "outputs/phase9/yolo_pedestrian/"
    "yolo11n_pie_occlusion_v1-2/weights/best.pt"
)

OUTPUT_ROOT = Path("outputs/phase9/tracker_tuning")
DEFAULT_IMG_SIZE = 960
DEFAULT_IOU_MATCH = 0.30

OFFICIAL_DEFAULTS = {
    "track_high_thresh": 0.25,
    "track_low_thresh": 0.10,
    "new_track_thresh": 0.25,
    "track_buffer": 30,
    "match_thresh": 0.80,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Data-driven BoT-SORT tuning on video-disjoint detector validation "
            "videos. Final tracker values are selected by validation metrics, "
            "not manually chosen."
        )
    )
    parser.add_argument(
        "--model",
        type=Path,
        default=DEFAULT_MODEL,
    )
    parser.add_argument(
        "--imgsz",
        type=int,
        default=DEFAULT_IMG_SIZE,
    )
    parser.add_argument(
        "--clips-per-video",
        type=int,
        default=2,
        help="Highest-partial-occlusion clips selected per detector validation video.",
    )
    parser.add_argument(
        "--clip-length",
        type=int,
        default=120,
    )
    parser.add_argument(
        "--iou-match",
        type=float,
        default=DEFAULT_IOU_MATCH,
    )
    parser.add_argument(
        "--max-configs",
        type=int,
        default=36,
        help="Maximum candidate configurations after data-driven derivation.",
    )
    return parser.parse_args()


def set_from_pedestrian_id(value: Any) -> str:
    token = str(value).split("_", 1)[0]
    if not token.isdigit():
        raise ValueError(f"Cannot derive PIE set from pedestrian ID {value!r}")
    return f"set{int(token):02d}"


def normalize_occ(value: Any) -> str:
    text = str(value).strip().lower()
    if text in {"none", "no", "not-occluded", "not_occluded"}:
        return "none"
    if text in {"part", "partial", "partially-occluded", "partially_occluded"}:
        return "part"
    if text in {"full", "fully-occluded", "fully_occluded"}:
        return "full"
    return text


def frame_path(dataset_set: str, video: str, frame_number: int) -> Path | None:
    base = FRAMES_ROOT / dataset_set / video
    for ext in ("jpg", "jpeg", "png"):
        path = base / f"frame_{frame_number:06d}.{ext}"
        if path.exists():
            return path
    return None


def bbox_iou(a: np.ndarray, b: np.ndarray) -> float:
    ax1, ay1, ax2, ay2 = map(float, a)
    bx1, by1, bx2, by2 = map(float, b)

    ix1 = max(ax1, bx1)
    iy1 = max(ay1, by1)
    ix2 = min(ax2, bx2)
    iy2 = min(ay2, by2)

    iw = max(0.0, ix2 - ix1)
    ih = max(0.0, iy2 - iy1)
    inter = iw * ih

    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union = area_a + area_b - inter

    return float(inter / union) if union > 0 else 0.0


def greedy_match(
    gt_items: list[tuple[str, np.ndarray]],
    pred_items: list[tuple[int, np.ndarray, float]],
    iou_threshold: float,
) -> list[tuple[int, int, float]]:
    candidates: list[tuple[float, int, int]] = []

    for gi, (_, gt_box) in enumerate(gt_items):
        for pi, (_, pred_box, _) in enumerate(pred_items):
            iou = bbox_iou(gt_box, pred_box)
            if iou >= iou_threshold:
                candidates.append((iou, gi, pi))

    candidates.sort(reverse=True)

    used_gt: set[int] = set()
    used_pred: set[int] = set()
    matches: list[tuple[int, int, float]] = []

    for iou, gi, pi in candidates:
        if gi in used_gt or pi in used_pred:
            continue
        used_gt.add(gi)
        used_pred.add(pi)
        matches.append((gi, pi, iou))

    return matches


def split_consecutive(frames: list[int]) -> list[list[int]]:
    if not frames:
        return []

    segments = [[frames[0]]]

    for frame in frames[1:]:
        if frame == segments[-1][-1] + 1:
            segments[-1].append(frame)
        else:
            segments.append([frame])

    return segments


def select_validation_clips(
    ann: pd.DataFrame,
    validation_videos: list[str],
    clips_per_video: int,
    clip_length: int,
) -> list[dict[str, Any]]:
    clips: list[dict[str, Any]] = []

    for video_key in validation_videos:
        dataset_set, video = video_key.split("/", 1)

        group = ann[
            (ann["dataset_set"] == dataset_set)
            & (ann["video"] == video)
        ]

        candidates: list[dict[str, Any]] = []

        for ped_id, ped_group in group.groupby("id"):
            frames = sorted(set(ped_group["frame"].astype(int)))
            for segment in split_consecutive(frames):
                if len(segment) < min(30, clip_length):
                    continue

                segment_start = segment[0]
                segment_end = segment[-1]

                # Slide a fixed-length window across the segment and score it by
                # number of PART annotations, then FULL annotations.
                starts = list(range(
                    segment_start,
                    max(segment_start + 1, segment_end - clip_length + 2),
                    max(1, clip_length // 3),
                ))

                if segment_end - segment_start + 1 <= clip_length:
                    starts = [segment_start]

                for start in starts:
                    end = min(start + clip_length - 1, segment_end)

                    window = group[
                        (group["frame"] >= start)
                        & (group["frame"] <= end)
                    ]

                    target_window = ped_group[
                        (ped_group["frame"] >= start)
                        & (ped_group["frame"] <= end)
                    ]

                    part_count = int(
                        (target_window["occlusion_norm"] == "part").sum()
                    )
                    full_count = int(
                        (target_window["occlusion_norm"] == "full").sum()
                    )

                    candidates.append({
                        "dataset_set": dataset_set,
                        "video": video,
                        "video_key": video_key,
                        "target_pedestrian": str(ped_id),
                        "start_frame": int(start),
                        "end_frame": int(end),
                        "part_count": part_count,
                        "full_count": full_count,
                        "annotation_rows": int(len(window)),
                    })

        candidates.sort(
            key=lambda row: (
                row["part_count"],
                row["full_count"],
                row["annotation_rows"],
            ),
            reverse=True,
        )

        chosen: list[dict[str, Any]] = []

        for candidate in candidates:
            overlaps_too_much = False

            for existing in chosen:
                overlap = max(
                    0,
                    min(candidate["end_frame"], existing["end_frame"])
                    - max(candidate["start_frame"], existing["start_frame"])
                    + 1,
                )
                candidate_len = (
                    candidate["end_frame"] - candidate["start_frame"] + 1
                )
                if overlap / max(1, candidate_len) > 0.50:
                    overlaps_too_much = True
                    break

            if not overlaps_too_much:
                chosen.append(candidate)

            if len(chosen) >= clips_per_video:
                break

        clips.extend(chosen)

    if not clips:
        raise RuntimeError(
            "No validation clips could be selected. "
            "Check annotations and detector validation video keys."
        )

    return clips


def load_frame_annotations(
    ann: pd.DataFrame,
    dataset_set: str,
    video: str,
    frame_number: int,
) -> pd.DataFrame:
    return ann[
        (ann["dataset_set"] == dataset_set)
        & (ann["video"] == video)
        & (ann["frame"] == frame_number)
    ]


def collect_true_positive_confidences(
    model: YOLO,
    ann: pd.DataFrame,
    clips: list[dict[str, Any]],
    imgsz: int,
    iou_match: float,
) -> list[float]:
    confidences: list[float] = []

    for clip_index, clip in enumerate(clips, start=1):
        print(
            f"[confidence profiling] clip {clip_index}/{len(clips)} "
            f"{clip['video_key']} frames "
            f"{clip['start_frame']}-{clip['end_frame']}"
        )

        for frame_number in range(
            clip["start_frame"],
            clip["end_frame"] + 1,
        ):
            path = frame_path(
                clip["dataset_set"],
                clip["video"],
                frame_number,
            )
            if path is None:
                continue

            frame = cv2.imread(str(path))
            if frame is None:
                continue

            gt_frame = load_frame_annotations(
                ann,
                clip["dataset_set"],
                clip["video"],
                frame_number,
            )

            # Direct visual matching only on NONE/PART ground truth.
            gt_frame = gt_frame[
                gt_frame["occlusion_norm"].isin({"none", "part"})
            ]

            gt_items = [
                (
                    str(row.id),
                    np.array(
                        [row.x1, row.y1, row.x2, row.y2],
                        dtype=np.float32,
                    ),
                )
                for row in gt_frame.itertuples(index=False)
            ]

            if not gt_items:
                continue

            result = model.predict(
                source=frame,
                classes=[0],
                conf=0.001,
                imgsz=imgsz,
                device=0,
                verbose=False,
            )[0]

            pred_items: list[tuple[int, np.ndarray, float]] = []

            if result.boxes is not None and len(result.boxes):
                boxes = result.boxes.xyxy.detach().cpu().numpy()
                scores = result.boxes.conf.detach().cpu().numpy()

                for idx, (box, score) in enumerate(zip(boxes, scores)):
                    pred_items.append(
                        (idx, box.astype(np.float32), float(score))
                    )

            for gi, pi, _ in greedy_match(gt_items, pred_items, iou_match):
                confidences.append(float(pred_items[pi][2]))

    return confidences


def full_occlusion_run_lengths(
    ann: pd.DataFrame,
    clips: list[dict[str, Any]],
) -> list[int]:
    runs: list[int] = []

    for clip in clips:
        group = ann[
            (ann["dataset_set"] == clip["dataset_set"])
            & (ann["video"] == clip["video"])
            & (ann["frame"] >= clip["start_frame"])
            & (ann["frame"] <= clip["end_frame"])
        ]

        for _, ped_group in group.groupby("id"):
            states = {
                int(row.frame): str(row.occlusion_norm)
                for row in ped_group.itertuples(index=False)
            }

            current = 0

            for frame_number in range(
                clip["start_frame"],
                clip["end_frame"] + 1,
            ):
                if states.get(frame_number) == "full":
                    current += 1
                else:
                    if current > 0:
                        runs.append(current)
                    current = 0

            if current > 0:
                runs.append(current)

    return runs


def unique_rounded(values: list[float], minimum: float = 0.001) -> list[float]:
    return sorted(
        set(
            round(max(minimum, min(0.95, float(value))), 3)
            for value in values
        )
    )


def derive_candidate_grid(
    confidences: list[float],
    full_runs: list[int],
    max_configs: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if len(confidences) < 10:
        raise RuntimeError(
            f"Only {len(confidences)} matched detector confidences were found. "
            "Need at least 10 for data-driven tracker-threshold derivation."
        )

    q05, q10, q25, q50 = np.quantile(
        np.array(confidences, dtype=np.float32),
        [0.05, 0.10, 0.25, 0.50],
    ).tolist()

    high_candidates = unique_rounded([
        OFFICIAL_DEFAULTS["track_high_thresh"],
        q25,
        q50,
    ])

    low_candidates = unique_rounded([
        OFFICIAL_DEFAULTS["track_low_thresh"],
        q05,
        q10,
    ])

    new_candidates = unique_rounded([
        OFFICIAL_DEFAULTS["new_track_thresh"],
        q25,
    ])

    if full_runs:
        p90_run = int(math.ceil(float(np.quantile(full_runs, 0.90))))
        max_run = int(max(full_runs))
    else:
        p90_run = OFFICIAL_DEFAULTS["track_buffer"]
        max_run = OFFICIAL_DEFAULTS["track_buffer"]

    buffer_candidates = sorted(set([
        OFFICIAL_DEFAULTS["track_buffer"],
        max(OFFICIAL_DEFAULTS["track_buffer"], p90_run),
        min(90, max(OFFICIAL_DEFAULTS["track_buffer"], max_run)),
    ]))

    configs: list[dict[str, Any]] = []

    for high, low, new, buffer_size in itertools.product(
        high_candidates,
        low_candidates,
        new_candidates,
        buffer_candidates,
    ):
        if low >= high:
            continue

        # A new track threshold below the low-stage threshold is not sensible.
        if new < low:
            continue

        configs.append({
            "track_high_thresh": float(high),
            "track_low_thresh": float(low),
            "new_track_thresh": float(new),
            "track_buffer": int(buffer_size),
            "match_thresh": float(OFFICIAL_DEFAULTS["match_thresh"]),
        })

    # Always include the untouched official default as baseline.
    configs.append(dict(OFFICIAL_DEFAULTS))

    # Remove exact duplicates.
    unique: list[dict[str, Any]] = []
    seen: set[tuple] = set()

    for config in configs:
        key = tuple(sorted(config.items()))
        if key not in seen:
            seen.add(key)
            unique.append(config)

    # Keep the search bounded and deterministic.
    unique.sort(
        key=lambda c: (
            c["track_high_thresh"],
            c["track_low_thresh"],
            c["new_track_thresh"],
            c["track_buffer"],
        )
    )

    if len(unique) > max_configs:
        # Evenly sample across the ordered candidate list while preserving
        # the official baseline.
        baseline = dict(OFFICIAL_DEFAULTS)
        baseline_key = tuple(sorted(baseline.items()))

        indices = np.linspace(
            0,
            len(unique) - 1,
            max_configs - 1,
        ).round().astype(int)

        sampled = [unique[i] for i in indices]
        sampled_keys = {tuple(sorted(c.items())) for c in sampled}

        if baseline_key not in sampled_keys:
            sampled.append(baseline)

        unique = sampled

    derivation = {
        "matched_confidence_count": len(confidences),
        "confidence_quantiles": {
            "q05": float(q05),
            "q10": float(q10),
            "q25": float(q25),
            "q50": float(q50),
        },
        "full_occlusion_run_count": len(full_runs),
        "full_occlusion_run_p90": p90_run,
        "full_occlusion_run_max": max_run,
        "official_defaults": OFFICIAL_DEFAULTS,
        "high_candidates": high_candidates,
        "low_candidates": low_candidates,
        "new_candidates": new_candidates,
        "buffer_candidates": buffer_candidates,
        "candidate_config_count": len(unique),
        "selection_rule": (
            "Lexicographic: highest IDF1, then highest visible/partial GT track recall, "
            "then highest dominant-ID consistency, then fewer ID switches."
        ),
    }

    return unique, derivation


def write_tracker_yaml(path: Path, config: dict[str, Any]) -> None:
    path.write_text(
        "\n".join([
            "tracker_type: botsort",
            f"track_high_thresh: {config['track_high_thresh']}",
            f"track_low_thresh: {config['track_low_thresh']}",
            f"new_track_thresh: {config['new_track_thresh']}",
            f"track_buffer: {config['track_buffer']}",
            f"match_thresh: {config['match_thresh']}",
            "fuse_score: True",
            "gmc_method: sparseOptFlow",
            "proximity_thresh: 0.5",
            "appearance_thresh: 0.8",
            "with_reid: False",
            "model: auto",
            "",
        ]),
        encoding="utf-8",
    )


def evaluate_config(
    model_path: Path,
    config_path: Path,
    ann: pd.DataFrame,
    clips: list[dict[str, Any]],
    imgsz: int,
    iou_match: float,
    inference_conf: float,
) -> dict[str, Any]:
    model = YOLO(str(model_path))

    gt_total = 0
    pred_total = 0
    matched_total = 0
    iou_sum = 0.0

    pair_counts: Counter[tuple[str, int]] = Counter()
    matched_ids_by_gt: dict[str, list[int]] = defaultdict(list)

    for clip_index, clip in enumerate(clips, start=1):
        # Fresh tracking state for every independent clip.
        if getattr(model, "predictor", None) is not None:
            model.predictor = None

        for frame_number in range(
            clip["start_frame"],
            clip["end_frame"] + 1,
        ):
            path = frame_path(
                clip["dataset_set"],
                clip["video"],
                frame_number,
            )
            if path is None:
                continue

            frame = cv2.imread(str(path))
            if frame is None:
                continue

            gt_frame = load_frame_annotations(
                ann,
                clip["dataset_set"],
                clip["video"],
                frame_number,
            )
            gt_frame = gt_frame[
                gt_frame["occlusion_norm"].isin({"none", "part"})
            ]

            gt_items = [
                (
                    f"{clip['video_key']}::{row.id}",
                    np.array(
                        [row.x1, row.y1, row.x2, row.y2],
                        dtype=np.float32,
                    ),
                )
                for row in gt_frame.itertuples(index=False)
            ]

            result = model.track(
                source=frame,
                persist=True,
                tracker=str(config_path),
                classes=[0],
                conf=float(inference_conf),
                imgsz=int(imgsz),
                device=0,
                verbose=False,
            )[0]

            pred_items: list[tuple[int, np.ndarray, float]] = []

            if result.boxes is not None and len(result.boxes):
                boxes = result.boxes.xyxy.detach().cpu().numpy()
                scores = result.boxes.conf.detach().cpu().numpy()

                if result.boxes.id is None:
                    ids = np.full(len(boxes), -1, dtype=np.int64)
                else:
                    ids = (
                        result.boxes.id.detach().cpu().numpy().astype(np.int64)
                    )

                for track_id, box, score in zip(ids, boxes, scores):
                    if int(track_id) < 0:
                        continue
                    pred_items.append(
                        (
                            int(track_id),
                            box.astype(np.float32),
                            float(score),
                        )
                    )

            gt_total += len(gt_items)
            pred_total += len(pred_items)

            matches = greedy_match(
                gt_items,
                pred_items,
                iou_match,
            )

            matched_total += len(matches)

            for gi, pi, iou in matches:
                gt_id = gt_items[gi][0]
                pred_id = pred_items[pi][0]

                pair_counts[(gt_id, pred_id)] += 1
                matched_ids_by_gt[gt_id].append(pred_id)
                iou_sum += float(iou)

    # Global dominant-ID assignment approximation for IDF1.
    # Each predicted track can be assigned to at most one GT identity and vice versa.
    pair_items = [
        (count, gt_id, pred_id)
        for (gt_id, pred_id), count in pair_counts.items()
    ]
    pair_items.sort(reverse=True)

    used_gt: set[str] = set()
    used_pred: set[int] = set()
    idtp = 0

    for count, gt_id, pred_id in pair_items:
        if gt_id in used_gt or pred_id in used_pred:
            continue
        used_gt.add(gt_id)
        used_pred.add(pred_id)
        idtp += int(count)

    idfn = max(0, gt_total - idtp)
    idfp = max(0, pred_total - idtp)

    denominator = (2 * idtp + idfp + idfn)
    idf1 = float(2 * idtp / denominator) if denominator else 0.0

    track_recall = float(matched_total / gt_total) if gt_total else 0.0
    mean_iou = float(iou_sum / matched_total) if matched_total else 0.0

    consistency_numerator = 0
    consistency_denominator = 0
    id_switches = 0

    for gt_id, track_ids in matched_ids_by_gt.items():
        if not track_ids:
            continue

        counts = Counter(track_ids)
        consistency_numerator += counts.most_common(1)[0][1]
        consistency_denominator += len(track_ids)

        previous = track_ids[0]
        for current in track_ids[1:]:
            if current != previous:
                id_switches += 1
            previous = current

    id_consistency = (
        float(consistency_numerator / consistency_denominator)
        if consistency_denominator else 0.0
    )

    return {
        "idf1": idf1,
        "track_recall": track_recall,
        "id_consistency": id_consistency,
        "id_switches": int(id_switches),
        "mean_matched_iou": mean_iou,
        "gt_visible_partial_instances": int(gt_total),
        "tracked_predictions": int(pred_total),
        "matched_instances": int(matched_total),
        "idtp": int(idtp),
        "idfp": int(idfp),
        "idfn": int(idfn),
    }


def main() -> None:
    args = parse_args()

    print("=" * 112)
    print("PHASE 9.5C - DATA-DRIVEN BoT-SORT VALIDATION / PARAMETER SELECTION")
    print("=" * 112)

    for path in (args.model, ANNOTATIONS, DETECTOR_SPLIT):
        if not path.exists():
            raise FileNotFoundError(f"Required file not found: {path}")

    split_data = json.loads(
        DETECTOR_SPLIT.read_text(encoding="utf-8")
    )
    validation_videos = list(split_data["val_videos"])

    print("Fine-tuned detector:", args.model)
    print("Detector validation videos:")
    for key in validation_videos:
        print("  ", key)

    ann = pd.read_csv(ANNOTATIONS)
    ann = ann.copy()
    ann["id"] = ann["id"].astype(str)
    ann["video"] = ann["video"].astype(str)
    ann["frame"] = pd.to_numeric(ann["frame"], errors="raise").astype(int)
    ann["dataset_set"] = ann["id"].map(set_from_pedestrian_id)
    ann["occlusion_norm"] = ann["occlusion"].map(normalize_occ)

    clips = select_validation_clips(
        ann=ann,
        validation_videos=validation_videos,
        clips_per_video=int(args.clips_per_video),
        clip_length=int(args.clip_length),
    )

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    temp_dir = OUTPUT_ROOT / "candidate_yamls"
    temp_dir.mkdir(parents=True, exist_ok=True)

    clips_path = OUTPUT_ROOT / "selected_validation_clips.csv"
    pd.DataFrame(clips).to_csv(clips_path, index=False)

    print()
    print("Selected validation clips:")
    print(
        pd.DataFrame(clips)[
            [
                "video_key",
                "target_pedestrian",
                "start_frame",
                "end_frame",
                "part_count",
                "full_count",
            ]
        ].to_string(index=False)
    )

    print()
    print("Profiling true-positive detector confidence distribution...")
    profile_model = YOLO(str(args.model))

    confidences = collect_true_positive_confidences(
        model=profile_model,
        ann=ann,
        clips=clips,
        imgsz=int(args.imgsz),
        iou_match=float(args.iou_match),
    )

    full_runs = full_occlusion_run_lengths(
        ann=ann,
        clips=clips,
    )

    configs, derivation = derive_candidate_grid(
        confidences=confidences,
        full_runs=full_runs,
        max_configs=int(args.max_configs),
    )

    derivation_path = OUTPUT_ROOT / "candidate_derivation.json"
    derivation_path.write_text(
        json.dumps(derivation, indent=2),
        encoding="utf-8",
    )

    print()
    print("Data-derived confidence quantiles:")
    for key, value in derivation["confidence_quantiles"].items():
        print(f"  {key}: {value:.6f}")

    print(
        "Observed FULL-occlusion runs: "
        f"count={derivation['full_occlusion_run_count']} "
        f"p90={derivation['full_occlusion_run_p90']} "
        f"max={derivation['full_occlusion_run_max']}"
    )

    print("Candidate configurations:", len(configs))

    min_low = min(
        config["track_low_thresh"]
        for config in configs
    )
    inference_conf = max(0.001, min_low * 0.50)

    print("Detector conf passed to tracker search:", inference_conf)
    print()

    results: list[dict[str, Any]] = []

    for index, config in enumerate(configs, start=1):
        config_path = temp_dir / f"candidate_{index:03d}.yaml"
        write_tracker_yaml(config_path, config)

        print(
            f"[{index:02d}/{len(configs):02d}] "
            f"high={config['track_high_thresh']:.3f} "
            f"low={config['track_low_thresh']:.3f} "
            f"new={config['new_track_thresh']:.3f} "
            f"buffer={config['track_buffer']}"
        )

        metrics = evaluate_config(
            model_path=args.model,
            config_path=config_path,
            ann=ann,
            clips=clips,
            imgsz=int(args.imgsz),
            iou_match=float(args.iou_match),
            inference_conf=float(inference_conf),
        )

        results.append({
            "candidate_index": index,
            **config,
            **metrics,
        })

        print(
            f"    IDF1={metrics['idf1']:.4f} "
            f"Recall={metrics['track_recall']:.4f} "
            f"Consistency={metrics['id_consistency']:.4f} "
            f"IDsw={metrics['id_switches']}"
        )

    results_df = pd.DataFrame(results)

    # No arbitrary weighted score:
    # lexicographic validation selection.
    results_df = results_df.sort_values(
        by=[
            "idf1",
            "track_recall",
            "id_consistency",
            "id_switches",
            "mean_matched_iou",
        ],
        ascending=[
            False,
            False,
            False,
            True,
            False,
        ],
    ).reset_index(drop=True)

    results_path = OUTPUT_ROOT / "tracker_candidate_results.csv"
    results_df.to_csv(results_path, index=False)

    best = results_df.iloc[0].to_dict()

    best_config = {
        "track_high_thresh": float(best["track_high_thresh"]),
        "track_low_thresh": float(best["track_low_thresh"]),
        "new_track_thresh": float(best["new_track_thresh"]),
        "track_buffer": int(best["track_buffer"]),
        "match_thresh": float(best["match_thresh"]),
    }

    best_yaml = OUTPUT_ROOT / "botsort_pie_selected.yaml"
    write_tracker_yaml(best_yaml, best_config)

    best_summary = {
        "selection_data": "detector validation videos only",
        "validation_videos": validation_videos,
        "selected_clips_csv": str(clips_path),
        "candidate_derivation": str(derivation_path),
        "selection_rule": derivation["selection_rule"],
        "selected_config": best_config,
        "selected_metrics": {
            "idf1": float(best["idf1"]),
            "track_recall": float(best["track_recall"]),
            "id_consistency": float(best["id_consistency"]),
            "id_switches": int(best["id_switches"]),
            "mean_matched_iou": float(best["mean_matched_iou"]),
        },
        "inference_conf_during_search": float(inference_conf),
        "iou_match_threshold_for_validation": float(args.iou_match),
        "important_note": (
            "The selected tracker parameters were derived and chosen on "
            "video-disjoint detector validation clips. They were not selected "
            "using sequence 28 or the final raw-video demo."
        ),
    }

    summary_path = OUTPUT_ROOT / "selected_tracker_summary.json"
    summary_path.write_text(
        json.dumps(best_summary, indent=2),
        encoding="utf-8",
    )

    print()
    print("-" * 112)
    print("SELECTED TRACKER")
    print("-" * 112)
    print("track_high_thresh :", best_config["track_high_thresh"])
    print("track_low_thresh  :", best_config["track_low_thresh"])
    print("new_track_thresh  :", best_config["new_track_thresh"])
    print("track_buffer      :", best_config["track_buffer"])
    print("match_thresh      :", best_config["match_thresh"])
    print()
    print("Validation IDF1           :", f"{best['idf1']:.6f}")
    print("Validation track recall   :", f"{best['track_recall']:.6f}")
    print("Validation ID consistency :", f"{best['id_consistency']:.6f}")
    print("Validation ID switches    :", int(best["id_switches"]))
    print("Validation matched IoU    :", f"{best['mean_matched_iou']:.6f}")
    print()
    print("Selected YAML :", best_yaml)
    print("Results CSV   :", results_path)
    print("Summary JSON  :", summary_path)
    print()
    print("Status: PASSED")
    print("=" * 112)


if __name__ == "__main__":
    main()
