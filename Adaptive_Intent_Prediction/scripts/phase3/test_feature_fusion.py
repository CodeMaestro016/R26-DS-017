import numpy as np

from utils.feature_fusion import FeatureFusion

fusion = FeatureFusion()

appearance = np.random.rand(512)

spatial = np.array([
    0.48,
    0.76,
    0.02,
    0.08,
    0.0016,
    4.0
])

motion = np.array([
    0.006,
    -0.006,
    0.0084,
    -0.785
])

feature = fusion.fuse(
    appearance,
    spatial,
    motion
)

print("=" * 50)
print("Feature Fusion Test")
print("=" * 50)

print()

print("Feature Shape")

print(feature.shape)

print()

print("First 10 values")

print(feature[:10])

print()

print("Last 10 values")

print(feature[-10:])