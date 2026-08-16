from utils.spatial import SpatialFeatureExtractor

bbox = (
    916,
    793,
    929,
    847
)

extractor = SpatialFeatureExtractor()

features = extractor.extract(
    bbox
)

print("=" * 50)
print("Spatial Feature Test")
print("=" * 50)

names = [
    "Center X",
    "Center Y",
    "Width",
    "Height",
    "Area",
    "Aspect Ratio"
]

for n, v in zip(names, features):
    print(f"{n:15}: {v}")