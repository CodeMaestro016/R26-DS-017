import cv2

from utils.feature_extractor import (
    AppearanceFeatureExtractor
)

image = cv2.imread(
    "outputs/pedestrian_crop.jpg"
)

extractor = AppearanceFeatureExtractor()

features = extractor.extract(
    image
)

print("="*50)

print("Feature Extraction Test")

print("="*50)

print()

print("Feature Shape")

print(features.shape)

print()

print("First 20 Values")

print(features[:20])