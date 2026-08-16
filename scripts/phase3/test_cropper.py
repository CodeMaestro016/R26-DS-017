"""
Phase 3 - Test Pedestrian Cropper

Loads one pedestrian from the dataset,
draws the bounding box,
extracts a context-aware crop,
and saves the results.
"""

import cv2

from utils.image_loader import ImageLoader
from utils.annotation_loader import AnnotationLoader
from utils.cropper import PedestrianCropper


# -------------------------------------------------
# Configuration
# -------------------------------------------------

FRAME_ROOT = "datasets/processed/frames"
ANNOTATIONS = "datasets/processed/metadata/annotations.csv"

VIDEO = "video_0001"
FRAME = 1458
PEDESTRIAN_ID = "1_1_3"
DATASET_SET = "set01"


# -------------------------------------------------
# Initialize Modules
# -------------------------------------------------

image_loader = ImageLoader(FRAME_ROOT)

annotation_loader = AnnotationLoader(
    ANNOTATIONS
)

cropper = PedestrianCropper(
    output_size=(224,224),
    context_scale=2.0,
    min_crop_size=128
)

# -------------------------------------------------
# Load Image
# -------------------------------------------------

image = image_loader.load_frame(
    video=VIDEO,
    frame_number=FRAME,
    dataset_set=DATASET_SET
)

annotation = annotation_loader.get_annotation(
    video=VIDEO,
    frame=FRAME,
    pedestrian_id=PEDESTRIAN_ID
)

if annotation is None:
    raise RuntimeError("Pedestrian annotation not found.")


bbox = (
    annotation["x1"],
    annotation["y1"],
    annotation["x2"],
    annotation["y2"]
)


# -------------------------------------------------
# Draw Bounding Box
# -------------------------------------------------

visualization = image.copy()

cv2.rectangle(
    visualization,
    (bbox[0], bbox[1]),
    (bbox[2], bbox[3]),
    (0, 255, 0),
    2
)

label = (
    f'{PEDESTRIAN_ID} | '
    f'{annotation["cross"]} | '
    f'{annotation["occlusion"]}'
)

cv2.putText(
    visualization,
    label,
    (bbox[0], max(20, bbox[1] - 5)),
    cv2.FONT_HERSHEY_SIMPLEX,
    0.5,
    (0, 255, 0),
    1
)


# -------------------------------------------------
# Extract Crop
# -------------------------------------------------

crop = cropper.crop(
    image=image,
    bbox=bbox
)


# -------------------------------------------------
# Save Results
# -------------------------------------------------

cv2.imwrite(
    "outputs/frame_with_bbox.jpg",
    visualization
)

cv2.imwrite(
    "outputs/pedestrian_crop.jpg",
    crop
)


# -------------------------------------------------
# Print Information
# -------------------------------------------------

print("=" * 50)
print("Pedestrian Crop Test")
print("=" * 50)

print(f"Video         : {VIDEO}")
print(f"Frame         : {FRAME}")
print(f"Pedestrian ID : {PEDESTRIAN_ID}")

print()

print("Bounding Box")

print(f"x1 = {bbox[0]}")
print(f"y1 = {bbox[1]}")
print(f"x2 = {bbox[2]}")
print(f"y2 = {bbox[3]}")

print()

print("Crop Shape")

print(crop.shape)

print()

print("Saved Files")

print("outputs/frame_with_bbox.jpg")
print("outputs/pedestrian_crop.jpg")