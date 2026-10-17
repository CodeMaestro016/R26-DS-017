from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


META = Path("datasets/processed/metadata")
TRAIN = META / "train.csv"
VAL = META / "val.csv"
TEST = META / "test.csv"
ANNOTATIONS = META / "annotations.csv"

OUT = Path("outputs/phase9/detector_split_audit")


def first_col(df: pd.DataFrame, names: list[str]) -> str:
    lookup = {str(c).lower(): str(c) for c in df.columns}

    for name in names:
        found = lookup.get(name.lower())
        if found is not None:
            return found

    raise KeyError(
        f"Missing one of {names}. Available columns: {list(df.columns)}"
    )


def normalize_occlusion(value) -> str:
    text = str(value).strip().lower()

    mapping = {
        "none": "none",
        "no": "none",
        "not-occluded": "none",
        "not_occluded": "none",
        "part": "part",
        "partial": "part",
        "partially-occluded": "part",
        "partially_occluded": "part",
        "full": "full",
        "fully-occluded": "full",
        "fully_occluded": "full",
    }

    return mapping.get(text, text)


def videos_from_split(path: Path) -> set[str]:
    df = pd.read_csv(path)
    video_col = first_col(df, ["video", "video_id"])
    return set(df[video_col].astype(str))


def main() -> None:
    print("=" * 100)
    print("PHASE 9.4B - DETECTOR VIDEO-SPLIT / OCCLUSION AUDIT")
    print("=" * 100)

    for path in (TRAIN, VAL, TEST, ANNOTATIONS):
        if not path.exists():
            raise FileNotFoundError(f"Required file not found: {path}")

    train_videos = videos_from_split(TRAIN)
    val_videos = videos_from_split(VAL)
    test_videos = videos_from_split(TEST)

    all_split_videos = train_videos | val_videos | test_videos

    unseen_to_intent_train = (
        (val_videos | test_videos) - train_videos
    )

    train_val_overlap = train_videos & val_videos
    train_test_overlap = train_videos & test_videos
    val_test_overlap = val_videos & test_videos

    ann = pd.read_csv(ANNOTATIONS)

    video_col = first_col(
        ann,
        ["video", "video_id"],
    )
    frame_col = first_col(
        ann,
        ["frame", "frame_id"],
    )
    ped_col = first_col(
        ann,
        ["id", "pedestrian_id", "pedestrian"],
    )
    occ_col = first_col(
        ann,
        ["occlusion", "occlusion_level"],
    )

    ann = ann.copy()
    ann["__video"] = ann[video_col].astype(str)
    ann["__frame"] = pd.to_numeric(
        ann[frame_col],
        errors="raise",
    ).astype(int)
    ann["__pedestrian"] = ann[ped_col].astype(str)
    ann["__occlusion"] = ann[occ_col].map(
        normalize_occlusion
    )

    rows = []

    for video, group in ann.groupby("__video"):
        occ_counts = (
            group["__occlusion"]
            .value_counts()
            .to_dict()
        )

        none_count = int(occ_counts.get("none", 0))
        part_count = int(occ_counts.get("part", 0))
        full_count = int(occ_counts.get("full", 0))

        visible_trainable = none_count + part_count
        total = int(len(group))

        rows.append(
            {
                "video": str(video),
                "annotation_rows": total,
                "unique_annotated_frames": int(
                    group["__frame"].nunique()
                ),
                "unique_pedestrians": int(
                    group["__pedestrian"].nunique()
                ),
                "occlusion_none_rows": none_count,
                "occlusion_part_rows": part_count,
                "occlusion_full_rows": full_count,
                "visible_or_partial_rows": visible_trainable,
                "partial_fraction_of_visible_or_partial": (
                    float(part_count / visible_trainable)
                    if visible_trainable > 0
                    else 0.0
                ),
                "in_intent_train": video in train_videos,
                "in_intent_val": video in val_videos,
                "in_intent_test": video in test_videos,
                "unseen_to_intent_train": (
                    video in unseen_to_intent_train
                ),
            }
        )

    summary_df = pd.DataFrame(rows)

    # Rank potential demonstration/evaluation videos:
    # unseen to the intent-training split + many partially occluded examples.
    candidates = (
        summary_df[
            summary_df["unseen_to_intent_train"]
        ]
        .sort_values(
            by=[
                "occlusion_part_rows",
                "unique_pedestrians",
                "visible_or_partial_rows",
            ],
            ascending=False,
        )
        .reset_index(drop=True)
    )

    OUT.mkdir(
        parents=True,
        exist_ok=True,
    )

    all_path = OUT / "video_occlusion_summary.csv"
    candidates_path = OUT / "unseen_video_candidates.csv"
    json_path = OUT / "detector_split_audit.json"

    summary_df.to_csv(
        all_path,
        index=False,
    )
    candidates.to_csv(
        candidates_path,
        index=False,
    )

    payload = {
        "intent_train_videos": sorted(train_videos),
        "intent_val_videos": sorted(val_videos),
        "intent_test_videos": sorted(test_videos),
        "all_split_videos": sorted(all_split_videos),
        "unseen_to_intent_train": sorted(
            unseen_to_intent_train
        ),
        "overlap": {
            "train_val": sorted(train_val_overlap),
            "train_test": sorted(train_test_overlap),
            "val_test": sorted(val_test_overlap),
        },
        "detector_methodology_note": (
            "For direct RGB detection training, use NONE and PART annotations "
            "as positive pedestrian boxes. FULL occlusion should not be treated "
            "as a directly visible detection target when the pedestrian has no "
            "observable pixels; continuity through full occlusion belongs to "
            "the tracking stage."
        ),
        "outputs": {
            "video_occlusion_summary": str(all_path),
            "unseen_video_candidates": str(candidates_path),
        },
    }

    json_path.write_text(
        json.dumps(
            payload,
            indent=2,
        ),
        encoding="utf-8",
    )

    print("Intent train videos :", len(train_videos))
    print("Intent val videos   :", len(val_videos))
    print("Intent test videos  :", len(test_videos))
    print()

    print("Video overlap:")
    print(
        "  train ∩ val  :",
        len(train_val_overlap),
        sorted(train_val_overlap),
    )
    print(
        "  train ∩ test :",
        len(train_test_overlap),
        sorted(train_test_overlap),
    )
    print(
        "  val ∩ test   :",
        len(val_test_overlap),
        sorted(val_test_overlap),
    )

    print()
    print(
        "Videos unseen to INTENT TRAIN:",
        len(unseen_to_intent_train),
    )
    print(
        sorted(unseen_to_intent_train)
    )

    print()
    print("-" * 100)
    print("TOP UNSEEN VIDEO CANDIDATES FOR FINAL OCCLUSION DEMO / DETECTOR EVALUATION")
    print("-" * 100)

    if candidates.empty:
        print(
            "No videos are completely unseen to the intent-training split."
        )
        print(
            "In that case, detector evaluation must use a NEW video-level holdout, "
            "but it cannot be called fully unseen to the frozen intent model."
        )
    else:
        columns = [
            "video",
            "occlusion_none_rows",
            "occlusion_part_rows",
            "occlusion_full_rows",
            "unique_pedestrians",
            "unique_annotated_frames",
            "in_intent_val",
            "in_intent_test",
        ]

        print(
            candidates[
                columns
            ]
            .head(15)
            .to_string(
                index=False
            )
        )

    print()
    print("-" * 100)
    print("DETECTOR TRAINING RULE")
    print("-" * 100)
    print(
        "Positive detection labels: occlusion = NONE or PART."
    )
    print(
        "Do NOT train a single-RGB detector to directly detect a never-visible "
        "FULL-occluded pedestrian. Full-occlusion continuity belongs to tracking."
    )

    print()
    print("Outputs:")
    print(all_path)
    print(candidates_path)
    print(json_path)
    print()
    print("Status: PASSED")
    print("=" * 100)


if __name__ == "__main__":
    main()
