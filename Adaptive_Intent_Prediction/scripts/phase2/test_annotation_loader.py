from utils.annotation_loader import AnnotationLoader

loader = AnnotationLoader(
    "datasets/processed/metadata/annotations.csv"
)

annotation = loader.get_annotation(
    video="video_0001",
    frame=1013,
    pedestrian_id="1_1_1"
)

print(annotation)