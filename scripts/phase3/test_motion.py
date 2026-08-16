from utils.motion import MotionFeatureExtractor

extractor = MotionFeatureExtractor()

# Example:
# previous frame
prev = [
    0.480,
    0.760,
    0.020,
    0.080,
    0.0016,
    4.0
]

# current frame
curr = [
    0.486,
    0.754,
    0.021,
    0.081,
    0.0017,
    3.9
]

features = extractor.extract(
    prev,
    curr
)

names = [
    "dx",
    "dy",
    "speed",
    "direction"
]

print("=" * 50)
print("Motion Feature Test")
print("=" * 50)

for n, v in zip(names, features):
    print(f"{n:12}: {v}")