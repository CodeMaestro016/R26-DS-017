from utils.image_loader import ImageLoader

loader = ImageLoader(
    "datasets/processed/frames"
)

image = loader.load_frame(
    video="video_0001",
    frame_number=1013,
    dataset_set="set01"
)

print(image.shape)