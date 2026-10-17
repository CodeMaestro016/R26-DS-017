import pandas as pd
from pathlib import Path
import cv2

train = pd.read_csv(
    "processed_data/metadata/train.csv"
)

sample = train.iloc[0]

video = sample["video"]
frame = sample["start_frame"]

image_path = Path(
    "processed_data/frames/set01"
) / video / f"frame_{frame:06d}.jpg"

print(image_path)

image = cv2.imread(str(image_path))

if image is None:
    print("Frame NOT FOUND")
else:
    print("Frame Loaded Successfully")
    print(image.shape)