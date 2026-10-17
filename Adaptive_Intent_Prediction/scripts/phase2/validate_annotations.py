from pathlib import Path
import random

import cv2
import pandas as pd

from utils.image_loader import ImageLoader

# ---------------------------------------------------
# Configuration
# ---------------------------------------------------

ANNOTATIONS = "datasets/processed/metadata/annotations.csv"
FRAME_ROOT = "datasets/processed/frames"

OUTPUT_DIR = Path("outputs/phase2/validation")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

NUM_SAMPLES = 50

# ---------------------------------------------------
# Load Data
# ---------------------------------------------------

df = pd.read_csv(ANNOTATIONS)

loader = ImageLoader(FRAME_ROOT)

samples = df.sample(NUM_SAMPLES, random_state=42)

invalid_boxes = 0
small_boxes = 0

report = []

# ---------------------------------------------------
# Validation Loop
# ---------------------------------------------------

for idx, row in samples.iterrows():

    video = row["video"]
    frame = int(row["frame"])

    # Infer dataset set from video name
    # (for now all your data is from set01)
    dataset_set = "set01"

    try:

        image = loader.load_frame(
            video=video,
            frame_number=frame,
            dataset_set=dataset_set
        )

    except FileNotFoundError:
        continue

    x1 = int(row["x1"])
    y1 = int(row["y1"])
    x2 = int(row["x2"])
    y2 = int(row["y2"])

    width = x2 - x1
    height = y2 - y1

    valid = True

    if width <= 0 or height <= 0:
        valid = False
        invalid_boxes += 1

    if width < 10 or height < 10:
        small_boxes += 1

    color = (0, 255, 0) if valid else (0, 0, 255)

    cv2.rectangle(
        image,
        (x1, y1),
        (x2, y2),
        color,
        2
    )

    text = f'{row["id"]} | {row["cross"]} | occ:{row["occlusion"]}'

    cv2.putText(
        image,
        text,
        (x1, max(20, y1 - 5)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        color,
        1
    )

    filename = OUTPUT_DIR / f"sample_{idx}.jpg"

    cv2.imwrite(
        str(filename),
        image
    )

# ---------------------------------------------------
# Report
# ---------------------------------------------------

report.append("===== DATASET VALIDATION =====\n")

report.append(f"Total Samples Checked : {NUM_SAMPLES}")
report.append(f"Invalid Boxes        : {invalid_boxes}")
report.append(f"Small Boxes          : {small_boxes}")

report_path = OUTPUT_DIR / "validation_report.txt"

with open(report_path, "w") as f:

    for line in report:
        f.write(line + "\n")

print("\nValidation Complete\n")

print(f"Samples Saved : {OUTPUT_DIR}")

print(f"Report Saved  : {report_path}")