from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


META = Path("datasets/processed/metadata")
FRAME_ROOT = Path("datasets/processed/frames")

TRAIN = META / "train.csv"
VAL = META / "val.csv"
TEST = META / "test.csv"
ANNOTATIONS = META / "annotations.csv"

OUT = Path("outputs/phase9/unused_pie_video_audit")


def first_col(df: pd.DataFrame, names: list[str]) -> str:
    lookup = {str(c).lower(): str(c) for c in df.columns}

    for name in names:
        found = lookup.get(name.lower())
        if found is not None:
            return found

    raise KeyError(
        f"Missing one of {names}. Available columns: {list(df.columns)}"
    )


def split_videos(path: Path) -> set[str]:
    df = pd.read_csv(path)
    video_col = first_col(df, ["video", "video_id"])
    return set(df[video_col].astype(str))


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


def scan_frame_directories() -> dict[str, list[str]]:
    found: dict[str, list[str]] = {}

    if not FRAME_ROOT.exists():
        return found

    for video_dir in FRAME_ROOT.rglob("video_*"):
        if not video_dir.is_dir():
            continue

        video = video_dir.name
        relative = str(
            video_dir.relative_to(FRAME_ROOT)
        )

        found.setdefault(
            video,
            [],
        ).append(relative)

    return found


def main() -> None:
    print("=" * 104)
    print("PHASE 9.4C - FIND PIE VIDEOS UNUSED BY THE FROZEN INTENT MODEL")
    print("=" * 104)

    for path in (TRAIN, VAL, TEST, ANNOTATIONS):
        if not path.exists():
            raise FileNotFoundError(
                f"Required file not found: {path}"
            )

    train_videos = split_videos(TRAIN)
    val_videos = split_videos(VAL)
    test_videos = split_videos(TEST)

    used_by_any_split = (
        train_videos
        | val_videos
        | test_videos
    )

    ann = pd.read_csv(ANNOTATIONS)

    video_col = first_col(
        ann,
        ["video", "video_id"],
    )
    occ_col = first_col(
        ann,
        ["occlusion", "occlusion_level"],
    )

    ann = ann.copy()
    ann["__video"] = ann[video_col].astype(str)
    ann["__occlusion"] = ann[occ_col].map(
        normalize_occlusion
    )

    annotation_videos = set(
        ann["__video"].unique()
    )

    frame_directories = scan_frame_directories()
    frame_videos = set(
        frame_directories.keys()
    )

    available_videos = (
        annotation_videos
        | frame_videos
    )

    completely_unused = (
        available_videos
        - used_by_any_split
    )

    unseen_to_intent_train = (
        available_videos
        - train_videos
    )

    rows = []

    for video in sorted(
        available_videos
    ):
        group = ann[
            ann["__video"] == video
        ]

        counts = (
            group["__occlusion"]
            .value_counts()
            .to_dict()
        )

        rows.append(
            {
                "video": video,
                "has_annotations": video in annotation_videos,
                "has_extracted_frames": video in frame_videos,
                "frame_directories": " | ".join(
                    frame_directories.get(
                        video,
                        [],
                    )
                ),
                "annotation_rows": int(
                    len(group)
                ),
                "occlusion_none_rows": int(
                    counts.get(
                        "none",
                        0,
                    )
                ),
                "occlusion_part_rows": int(
                    counts.get(
                        "part",
                        0,
                    )
                ),
                "occlusion_full_rows": int(
                    counts.get(
                        "full",
                        0,
                    )
                ),
                "in_intent_train": (
                    video in train_videos
                ),
                "in_intent_val": (
                    video in val_videos
                ),
                "in_intent_test": (
                    video in test_videos
                ),
                "unused_by_all_intent_splits": (
                    video in completely_unused
                ),
                "unseen_to_intent_train": (
                    video in unseen_to_intent_train
                ),
            }
        )

    summary_df = pd.DataFrame(rows)

    unused_df = (
        summary_df[
            summary_df[
                "unused_by_all_intent_splits"
            ]
        ]
        .sort_values(
            by=[
                "occlusion_part_rows",
                "annotation_rows",
            ],
            ascending=False,
        )
        .reset_index(drop=True)
    )

    OUT.mkdir(
        parents=True,
        exist_ok=True,
    )

    all_path = (
        OUT
        / "all_available_pie_videos.csv"
    )

    unused_path = (
        OUT
        / "completely_unused_pie_videos.csv"
    )

    json_path = (
        OUT
        / "unused_pie_video_audit.json"
    )

    summary_df.to_csv(
        all_path,
        index=False,
    )

    unused_df.to_csv(
        unused_path,
        index=False,
    )

    payload = {
        "intent_train_videos": sorted(
            train_videos
        ),
        "intent_val_videos": sorted(
            val_videos
        ),
        "intent_test_videos": sorted(
            test_videos
        ),
        "annotation_videos": sorted(
            annotation_videos
        ),
        "extracted_frame_videos": sorted(
            frame_videos
        ),
        "available_videos": sorted(
            available_videos
        ),
        "completely_unused_by_intent_splits": sorted(
            completely_unused
        ),
        "unseen_to_intent_train": sorted(
            unseen_to_intent_train
        ),
        "recommended_interpretation": (
            "A video can only be called completely unseen to the frozen "
            "intent system if it was not used in intent train, validation, "
            "or test during development. If no such local PIE video exists, "
            "a new PIE video/set or external real-world video must be added "
            "for a clean post-freeze generalization demonstration."
        ),
        "outputs": {
            "all_available_pie_videos": str(
                all_path
            ),
            "completely_unused_pie_videos": str(
                unused_path
            ),
        },
    }

    json_path.write_text(
        json.dumps(
            payload,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(
        "Intent train videos      :",
        len(train_videos),
        sorted(train_videos),
    )
    print(
        "Intent val videos        :",
        len(val_videos),
        sorted(val_videos),
    )
    print(
        "Intent test videos       :",
        len(test_videos),
        sorted(test_videos),
    )

    print()
    print(
        "Videos in annotations    :",
        len(annotation_videos),
        sorted(annotation_videos),
    )
    print(
        "Videos with frame folders:",
        len(frame_videos),
        sorted(frame_videos),
    )

    print()
    print(
        "Completely UNUSED by intent train/val/test:",
        len(completely_unused),
    )
    print(
        sorted(completely_unused)
    )

    print()
    print("-" * 104)
    print("COMPLETELY UNUSED PIE VIDEO CANDIDATES")
    print("-" * 104)

    if unused_df.empty:
        print(
            "NONE FOUND in the currently processed PIE files."
        )
        print()
        print(
            "Meaning: the local processed dataset does not currently contain "
            "a clean post-freeze unseen PIE video."
        )
        print(
            "Next scientific option: extract/add another PIE video/set that was "
            "never used during model development, or use an external real-world video."
        )
    else:
        columns = [
            "video",
            "has_annotations",
            "has_extracted_frames",
            "occlusion_none_rows",
            "occlusion_part_rows",
            "occlusion_full_rows",
            "frame_directories",
        ]

        print(
            unused_df[
                columns
            ].to_string(
                index=False
            )
        )

    print()
    print("Outputs:")
    print(all_path)
    print(unused_path)
    print(json_path)
    print()
    print("Status: PASSED")
    print("=" * 104)


if __name__ == "__main__":
    main()
