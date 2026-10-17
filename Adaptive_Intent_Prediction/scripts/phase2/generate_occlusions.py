"""
Phase 2 Verification Script

Randomly selects a training sample and applies
synthetic occlusion for visual verification.
"""

import random
from pathlib import Path

import cv2
import pandas as pd

from utils.image_loader import ImageLoader
from utils.annotation_loader import AnnotationLoader
from utils.occlusion import OcclusionGenerator


# -------------------------------------------------
# Configuration
# -------------------------------------------------

TRAIN_CSV = "datasets/processed/metadata/train.csv"
ANNOTATIONS = "datasets/processed/metadata/annotations.csv"

FRAME_ROOT = "datasets/processed/frames"

OUTPUT_DIR = Path("outputs/phase2")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# -------------------------------------------------
# Load Training Metadata
# -------------------------------------------------

train_df = pd.read_csv(TRAIN_CSV)

sample = train_df.sample(1).iloc[0]

video = sample["video"]
pedestrian = sample["pedestrian_id"]

frames = sample["frames"].split("|")

frame = int(random.choice(frames))

print("=" * 60)
print("Random Training Sample")
print("=" * 60)

print(f"Video       : {video}")
print(f"Pedestrian  : {pedestrian}")
print(f"Frame       : {frame}")
print(f"Label       : {sample['label']}")

# -------------------------------------------------
# Initialize Modules
# -------------------------------------------------

image_loader = ImageLoader(FRAME_ROOT)

annotation_loader = AnnotationLoader(
    ANNOTATIONS
)

generator = OcclusionGenerator()

# -------------------------------------------------
# Load Image
# -------------------------------------------------

image = image_loader.load_frame(
    video=video,
    frame_number=frame,
    dataset_set="set01"
)

annotation = annotation_loader.get_annotation(
    video=video,
    frame=frame,
    pedestrian_id=pedestrian
)

if annotation is None:
    raise RuntimeError(
        "Annotation not found."
    )

bbox = (
    annotation["x1"],
    annotation["y1"],
    annotation["x2"],
    annotation["y2"]
)

# -------------------------------------------------
# Random Occlusion Level
# -------------------------------------------------

level = random.choice(
    ["low", "medium", "high"]
)

occluded, metadata = generator.apply(
    image=image,
    bbox=bbox,
    level=level
)

# -------------------------------------------------
# Draw Bounding Box (Visualization Only)
# -------------------------------------------------

before = image.copy()
after = occluded.copy()

cv2.rectangle(
    before,
    (bbox[0], bbox[1]),
    (bbox[2], bbox[3]),
    (0, 255, 0),
    2
)

cv2.rectangle(
    after,
    (bbox[0], bbox[1]),
    (bbox[2], bbox[3]),
    (0, 255, 0),
    2
)

# -------------------------------------------------
# Save
# -------------------------------------------------

before_path = OUTPUT_DIR / "before.jpg"
after_path = OUTPUT_DIR / "after.jpg"

cv2.imwrite(str(before_path), before)
cv2.imwrite(str(after_path), after)

print("\nOcclusion Metadata")
print("-" * 30)

for key, value in metadata.items():
    print(f"{key:15}: {value}")

print("\nSaved Files")

print(before_path)
print(after_path)