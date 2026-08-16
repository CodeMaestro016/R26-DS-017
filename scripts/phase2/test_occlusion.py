import cv2

from utils.image_loader import ImageLoader
from utils.annotation_loader import AnnotationLoader
from utils.occlusion import OcclusionGenerator

# ---------------------------------

image_loader = ImageLoader(
    "datasets/processed/frames"
)

annotation_loader = AnnotationLoader(
    "datasets/processed/metadata/annotations.csv"
)

generator = OcclusionGenerator()

# ---------------------------------

video = "video_0001"
frame = 1013
pedestrian = "1_1_1"

image = image_loader.load_frame(
    video,
    frame,
    "set01"
)

ann = annotation_loader.get_annotation(
    video,
    frame,
    pedestrian
)

bbox = (
    ann["x1"],
    ann["y1"],
    ann["x2"],
    ann["y2"]
)

occluded, metadata = generator.apply(
    image=image,
    bbox=bbox,
    level="medium"
)

print(metadata)

cv2.imwrite(
    "outputs/test_occlusion.jpg",
    occluded
)

print("\nSaved to outputs/test_occlusion.jpg")